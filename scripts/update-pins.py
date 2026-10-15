#!/usr/bin/env python3
"""Bump the pinned downloads (PINNED in main.py) to the latest releases.

Usage: python3 scripts/update-pins.py [--dry-run] [TOOL ...]
  TOOL      keys of PINNED (kitty, starship, nvim, bat, lsd, hack-nerd-font,
            fzf); all of them if omitted.
  --dry-run only print the diff, don't write main.py.

For each tool it follows https://github.com/<owner>/<repo>/releases/latest
to the newest release tag, downloads every asset of the new version,
computes its SHA-256 and checks it against the checksum file the release
publishes (<asset>.sha256, shasum.txt, SHA-256.txt) and against the sha256
digest GitHub shows for the asset on the release page, when there are any.
fzf is a git clone, so it gets the tag's commit (git ls-remote) instead.
Then it rewrites the entries in main.py and prints the diff. Nothing is
committed: review the diff, run the installer, and commit it yourself.
Stdlib only (plus the git CLI for fzf); doesn't use the GitHub API.
"""
import argparse
import ast
import difflib
import hashlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MAIN = Path(__file__).resolve().parent.parent / "main.py"
UA = {"User-Agent": "auto-kitty-update-pins"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def latest_tag(repo_url):
    """Tag of the latest release, from the Location of the releases/latest redirect."""
    req = urllib.request.Request(repo_url + "/releases/latest", method="HEAD", headers=UA)
    try:
        urllib.request.build_opener(NoRedirect).open(req, timeout=30)
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            tag = e.headers["Location"].rstrip("/").rsplit("/tag/", 1)
            if len(tag) == 2:
                return urllib.parse.unquote(tag[1])
        raise
    sys.exit(f"ERROR: {repo_url}/releases/latest didn't redirect to a release tag.")


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def published_sha256(url):
    """(hash, source) from a checksum file published next to the asset, or (None, None)."""
    base, name = url.rsplit("/", 1)
    for cand in (url + ".sha256", url + ".sha256sum", base + "/shasum.txt", base + "/SHA-256.txt"):
        try:
            text = fetch(cand).decode("utf-8", "replace")
        except urllib.error.HTTPError:
            continue
        for line in text.splitlines():
            parts = line.split()
            if len(parts) == 1 and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
                return parts[0].lower(), cand
            if len(parts) >= 2 and parts[-1].lstrip("*") == name:
                return parts[0].lower(), cand
    return None, None


def github_digest(url):
    """(hash, source) from the "sha256:..." digest GitHub shows next to a
    release asset (the HTML of releases/expanded_assets/<tag>, no API), or
    (None, None) when the page or the digest isn't there (older releases)."""
    m = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)/releases/download/([^/]+)/([^/]+)", url)
    if not m:
        return None, None
    page = f"https://github.com/{m[1]}/releases/expanded_assets/{m[2]}"
    try:
        html = fetch(page).decode("utf-8", "replace")
    except OSError:   # HTTP errors and timeouts too: just no digest to compare
        return None, None
    href = f'href="/{m[1]}/releases/download/{m[2]}/{m[3]}"'
    start = html.find(href)
    if start < 0:
        return None, None
    # Only look up to the next asset, so another file's digest can't match.
    end = html.find("/releases/download/", start + len(href))
    d = re.search(r"sha256:([0-9a-f]{64})", html[start:end if end >= 0 else len(html)])
    return (d[1], page) if d else (None, None)


def repo_of(entry):
    if "repo" in entry:
        return entry["repo"]
    for asset in entry.values():
        if isinstance(asset, dict) and "url" in asset:
            m = re.match(r"(https://github\.com/[^/]+/[^/]+)/releases/download/", asset["url"])
            if m:
                return m.group(1)
    sys.exit(f"ERROR: can't tell the GitHub repo of {entry}")


def tag_commit(repo, tag):
    out = subprocess.run(["git", "ls-remote", repo + ".git", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"],
                         capture_output=True, text=True, check=True).stdout
    refs = dict(reversed(line.split("\t")) for line in out.splitlines() if "\t" in line)
    # Annotated tags: the peeled ^{} ref is the commit.
    commit = refs.get(f"refs/tags/{tag}^{{}}") or refs.get(f"refs/tags/{tag}")
    if not commit:
        sys.exit(f"ERROR: tag {tag} not found in {repo}")
    return commit


def entry_span(text, name):
    """(start, end) of the `"name": {...},` block inside PINNED in main.py's text."""
    start = text.index("\nPINNED = {")
    m = re.compile(rf'^    "{re.escape(name)}": \{{\n.*?^    \}},\n', re.M | re.S).search(text, start)
    if not m:
        sys.exit(f"ERROR: entry {name!r} not found in PINNED in {MAIN}")
    return m.start(), m.end()


def update(text, name, entry):
    old = entry["version"]
    repo = repo_of(entry)
    new = latest_tag(repo)
    if new == old:
        print(f"{name}: {old} is the latest release.")
        return text
    print(f"{name}: {old} -> {new}")
    start, end = entry_span(text, name)
    block = text[start:end].replace(f'"version": "{old}"', f'"version": "{new}"', 1)
    if "commit" in entry:
        block = block.replace(entry["commit"], tag_commit(repo, new))
    for arch, asset in entry.items():
        if not (isinstance(asset, dict) and "url" in asset):
            continue
        # Asset names carry the version with or without the "v" (kitty-0.49.2-x86_64.txz).
        url = asset["url"].replace(old.lstrip("v"), new.lstrip("v"))
        print(f"  {arch}: downloading {url}")
        digest = hashlib.sha256(fetch(url)).hexdigest()
        checks = [c for c in (published_sha256(url), github_digest(url)) if c[0]]
        for published, source in checks:
            if published != digest:
                sys.exit(f"ERROR: {url}: computed {digest}, but {source} says {published}")
        if not checks:
            print(f"  {arch}: sha256 {digest} (no published checksum or GitHub digest; check the release page)")
        else:
            print(f"  {arch}: sha256 {digest} (matches {' and '.join(src for _, src in checks)})")
        block = block.replace(asset["url"], url).replace(asset["sha256"], digest)
    return text[:start] + block + text[end:]


def main():
    p = argparse.ArgumentParser(description="Bump PINNED in main.py to the latest releases.")
    p.add_argument("tools", nargs="*", help="PINNED keys to update (default: all)")
    p.add_argument("--dry-run", action="store_true", help="print the diff without writing main.py")
    args = p.parse_args()

    text = MAIN.read_text()
    # Read the table without importing (= running) main.py.
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "PINNED" for t in n.targets))
    pinned = ast.literal_eval(node.value)
    unknown = set(args.tools) - pinned.keys()
    if unknown:
        p.error(f"unknown tool(s): {', '.join(sorted(unknown))}; choose from {', '.join(pinned)}")

    new_text = text
    for name in args.tools or pinned:
        new_text = update(new_text, name, pinned[name])

    if new_text == text:
        print("Nothing to update.")
        return
    sys.stdout.writelines(difflib.unified_diff(text.splitlines(True), new_text.splitlines(True),
                                               "a/main.py", "b/main.py"))
    if args.dry_run:
        print("\n(--dry-run: main.py not written)")
    else:
        MAIN.write_text(new_text)
        print("\nmain.py updated. Review the diff, test the installer and commit it yourself.")


if __name__ == "__main__":
    main()

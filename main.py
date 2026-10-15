import argparse
import hashlib
import os
import platform
import pwd
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from sys import stdout


REPO = Path(__file__).resolve().parent
HOME = Path.home()

THEMES_DIR = REPO / "tools" / "themes"
DESKTOP_DIR = REPO / "tools" / "desktop"
STATE_DIR = HOME / ".config" / "auto-kitty"

# Each theme lives in tools/themes/<key>/ (color.ini + starship.toml).
THEMES = {
    "classic": {
        "name": "Classic",
        "desc": "Catppuccin pastel + prompt arcoíris (el Auto-Kitty original)",
        "nvchad": "onedark",   # NvChad's default
        "bat": None,           # bat's default theme
    },
    "moonfly": {
        "name": "Moonfly",
        "desc": "Negro con acentos verdes: prompt gris, bordes y pestañas neutras",
        "nvchad": "yoru",      # closest NvChad theme to Moonfly
        "bat": "ansi",         # bat uses the terminal's (Moonfly) colors
    },
}

# Filled in by the menu / CLI flags before the install phases run.
CHOICE = {"theme": "classic", "desktop": False}

# The tools the installer downloads, pinned to an exact release and checked
# with SHA-256 before use (see download_verified). Not pinned: the NvChad
# starter config and, in the optional Moonfly desktop, the Colloid theme and
# papirus-folders, which come from their latest commit. Assets are keyed by
# machine ("any" = same file everywhere); preflight() only allows x86_64 for
# now, so supporting arm64 means adding "aarch64" entries. Bump them with
# scripts/update-pins.py, never by hand-editing a hash you didn't check.
ARCH = "x86_64"
PINNED = {
    "kitty": {
        "version": "v0.49.2",
        "x86_64": {"url": "https://github.com/kovidgoyal/kitty/releases/download/v0.49.2/kitty-0.49.2-x86_64.txz",
                   "sha256": "d573618b911e9c461bd421b96c13c74c7f1cb2f1ac9c327818d4ff84366cf5c6"},
    },
    "starship": {
        "version": "v1.26.0",
        "x86_64": {"url": "https://github.com/starship/starship/releases/download/v1.26.0/starship-x86_64-unknown-linux-musl.tar.gz",
                   "sha256": "b7c232b0e8249d8e55a40beb79c5c43a7d370f3f9408bd215deb0170daeaadf3"},
    },
    "nvim": {
        "version": "v0.12.6",
        "x86_64": {"url": "https://github.com/neovim/neovim/releases/download/v0.12.6/nvim-linux-x86_64.tar.gz",
                   "sha256": "474430d53e6264f6d6dd18db42d6dc9df3a1b56ca9e88a325bbf860e1a811d87"},
    },
    "bat": {
        "version": "v0.26.1",
        "x86_64": {"url": "https://github.com/sharkdp/bat/releases/download/v0.26.1/bat-v0.26.1-x86_64-unknown-linux-musl.tar.gz",
                   "sha256": "0dcd8ac79732c0d5b136f11f4ee00e581440e16a44eab5b3105b611bbf2cf191"},
    },
    "lsd": {
        "version": "v1.2.0",
        "x86_64": {"url": "https://github.com/lsd-rs/lsd/releases/download/v1.2.0/lsd-v1.2.0-x86_64-unknown-linux-musl.tar.gz",
                   "sha256": "77849da1210336534258551a581401ba19ae6b8d7b66a2a1feff148ad41e3814"},
    },
    "hack-nerd-font": {
        "version": "v3.5.1",
        "any": {"url": "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.5.1/Hack.zip",
                "sha256": "fa24da7de7cefe7766614d27762570b20453c852fc1d5b657111666df9a5e449"},
    },
    # Cloned, not downloaded: the tag's commit is checked after checkout.
    "fzf": {
        "version": "v0.74.5",
        "repo": "https://github.com/junegunn/fzf",
        "commit": "c0a193e031f01fb50bf6f7be4381990a3753f7cf",
    },
}


"""APP LOGO"""
BANNER = """
 █████╗ ██╗   ██╗████████╗ ██████╗       ██╗  ██╗██╗████████╗████████╗██╗   ██╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗      ██║ ██╔╝██║╚══██╔══╝╚══██╔══╝╚██╗ ██╔╝
███████║██║   ██║   ██║   ██║   ██║█████╗█████╔╝ ██║   ██║      ██║    ╚████╔╝
██╔══██║██║   ██║   ██║   ██║   ██║╚════╝██╔═██╗ ██║   ██║      ██║     ╚██╔╝
██║  ██║╚██████╔╝   ██║   ╚██████╔╝      ██║  ██╗██║   ██║      ██║      ██║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝       ╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝      ╚═╝
██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗███████╗██████╗  █████╗  ██████╗███████╗
██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝
██║ █╗ ██║██║   ██║██████╔╝█████╔╝ ███████╗██████╔╝███████║██║     █████╗
██║███╗██║██║   ██║██╔══██╗██╔═██╗ ╚════██║██╔═══╝ ██╔══██║██║     ██╔══╝
╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗███████║██║     ██║  ██║╚██████╗███████╗
 ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝
                                                             (by Juanfu224)
"""


"""COLORS"""
def red():
    stdout.write("\033[1;31m")


def green():
    stdout.write("\033[0;32m")


def blue():
    stdout.write("\033[1;34m")


def yellow():
    stdout.write("\033[1;33m")


def orange():
    stdout.write("\033[1;38;5;208m")


def white():
    stdout.write("\033[1;37m")


def purple():
    stdout.write("\033[1;35m")


def cyan():
    stdout.write("\033[1;36m")


def light_gray():
    stdout.write("\033[0;37m")


def dark_gray():
    stdout.write("\033[1;30m")


def light_blue():
    stdout.write("\033[1;94m")


"""HELPERS"""
def run(cmd, *, shell=False, check=True, cwd=None, env=None):
    """All shell calls go through here. check=True so failures abort."""
    display = cmd if isinstance(cmd, str) else " ".join(shlex.quote(c) for c in cmd)
    cyan(); print(f"  $ {display}"); white()
    if isinstance(cmd, str) and not shell:
        cmd = shlex.split(cmd)
    return subprocess.run(cmd, shell=shell, check=check, cwd=cwd, env=env)


# Fresh Mint installs often have mintupdate / unattended-upgrades holding the
# dpkg lock for a few minutes; wait for it instead of failing with
# "Could not get lock /var/lib/dpkg/lock-frontend".
APT = ["sudo", "apt-get", "-o", "DPkg::Lock::Timeout=600"]


def download(url, dest: Path):
    """Download to a .part file first so an interrupted run never leaves a
    truncated file that later runs would treat as already downloaded."""
    part = dest.with_name(dest.name + ".part")
    run(["curl", "-fL", "--retry", "3", "-o", str(part), url])
    part.replace(dest)


def sha256_of(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_verified(name):
    """Download PINNED[name]'s asset into the repo dir and check its SHA-256.
    A cached copy is reused only if its hash matches; a bad download is
    deleted and the installer stops instead of installing it."""
    entry = PINNED[name]
    asset = entry.get(ARCH) or entry["any"]
    url, want = asset["url"], asset["sha256"]
    dest = REPO / url.rsplit("/", 1)[1]
    # Versioned file names (bat-v0.26.1-...) leave older pins behind; drop them.
    ver = entry["version"].lstrip("v")
    if ver in dest.name:
        for stale in REPO.glob(dest.name.replace(ver, "*")):
            if stale != dest:
                stale.unlink()
    if dest.exists():
        if sha256_of(dest) == want:
            print(f"  {dest.name} already downloaded (SHA-256 OK).")
            return dest
        dest.unlink()   # an older version under the same name, or corrupted
    download(url, dest)
    got = sha256_of(dest)
    if got != want:
        dest.unlink()
        sys.exit(f"ERROR: SHA-256 mismatch for {url}\n"
                 f"       expected {want}\n"
                 f"       got      {got}\n"
                 f"       The file was deleted and nothing was installed from it. Try again later;\n"
                 f"       if it keeps happening, the download was altered or the pin in main.py is wrong.")
    green(); print(f"  {dest.name}: SHA-256 OK"); white()
    return dest


VERSION_RE = re.compile(r"v?(\d+(?:\.\d+)+)(?:[-+~].*)?")


def version_key(text):
    """(0, 49, 2) for "v0.49.2" / "0.49.2-dev+g1234", for comparing versions
    numerically; None if text isn't a version. Trailing zeros are dropped so
    that 1.2 == 1.2.0."""
    m = VERSION_RE.fullmatch(text)
    if not m:
        return None
    key = [int(n) for n in m.group(1).split(".")]
    while key and key[-1] == 0:
        key.pop()
    return tuple(key)


def has_version(binary, version, sudo=False):
    """The version `binary --version` reports on its first line if it is
    `version` or newer, else None. Newer counts so that a rerun never
    downgrades a tool the user updated in our install location."""
    try:
        res = subprocess.run((["sudo"] if sudo else []) + [str(binary), "--version"],
                             capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    first = (res.stdout.splitlines() or [""])[0]
    found = next((t for t in first.split() if version_key(t) is not None), None)
    return found if found and version_key(found) >= version_key(version) else None


def print_kept(name, found, version, where=""):
    """Message for a tool has_version() found at the pinned version or newer."""
    if version_key(found) == version_key(version):
        print(f"  {name} {version} already installed{where}, skipping.")
    else:
        print(f"  {name} {found} already installed{where} (newer than the pinned {version}), keeping it.")


def install_release_binary(name):
    """Install a pinned single-binary release tarball (bat, lsd, starship) to
    /usr/local/bin, with its man page and zsh completion when it ships them.
    /usr/local/bin comes before /usr/bin in PATH and sudo's secure_path, so an
    older apt/dpkg copy doesn't shadow it."""
    version = PINNED[name]["version"]
    dest = Path("/usr/local/bin") / name
    found = has_version(dest, version)
    if found:
        print_kept(name, found, version)
        return
    archive = download_verified(name)
    with tempfile.TemporaryDirectory(prefix=f"akw-{name}-") as tmp:
        run(["tar", "-xzf", str(archive), "-C", tmp, "--no-same-owner"])
        found = [p for p in Path(tmp).rglob(name) if p.is_file()]
        if not found:
            sys.exit(f"ERROR: {archive.name} has no '{name}' binary.")
        top = found[0].parent
        run(["sudo", "install", "-m", "755", str(found[0]), str(dest)])
        man = top / f"{name}.1"
        if man.is_file():
            run(["sudo", "install", "-D", "-m", "644", str(man), f"/usr/local/share/man/man1/{name}.1"])
        for comp in (top / "autocomplete" / f"_{name}", top / "autocomplete" / f"{name}.zsh"):
            if comp.is_file():
                run(["sudo", "install", "-D", "-m", "644", str(comp),
                     f"/usr/local/share/zsh/site-functions/_{name}"])
                break
    if not has_version(dest, version):
        sys.exit(f"ERROR: {dest} --version doesn't report {version} after installing it.")


def sudo_keepalive():
    """Refresh the sudo timestamp in the background so long phases (nvim,
    fonts...) don't stop halfway to ask for the password again."""
    def loop():
        while True:
            time.sleep(60)
            subprocess.run(["sudo", "-n", "-v"], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    threading.Thread(target=loop, daemon=True).start()


def gsettings_has(schema, key):
    """True if this desktop has that gsettings schema/key (Cinnamon-only keys)."""
    if shutil.which("gsettings") is None:
        return False
    res = subprocess.run(["gsettings", "list-keys", schema],
                         capture_output=True, text=True, check=False)
    return res.returncode == 0 and key in res.stdout.split()


def print_step(text):
    orange()
    print(text)
    white()


def backup_path(p: Path, sudo=False):
    """Move existing file/dir aside with a timestamped suffix; no-op if absent.
    lexists: a dangling symlink is moved aside too, instead of written through.
    sudo=True for paths only root can see (/root/...)."""
    def lexists(q):
        if not sudo:
            return os.path.lexists(q)
        return subprocess.run(["sudo", "test", "-e", str(q), "-o", "-L", str(q)], check=False).returncode == 0
    if not lexists(p):
        return None
    stamp = int(time.time())
    backup, n = p.with_name(f"{p.name}.backup.{stamp}"), 1
    # Two backups of the same path within one second must not collide:
    # moving a dir onto an existing backup dir would nest it inside.
    while lexists(backup):
        n += 1
        backup = p.with_name(f"{p.name}.backup.{stamp}-{n}")
    if sudo:
        run(["sudo", "mv", "-T", str(p), str(backup)])
    else:
        shutil.move(str(p), str(backup))
    yellow(); print(f"  Backed up {p} -> {backup}"); white()
    return backup


def same_bytes(a: Path, b: Path):
    """True if both are readable files with identical contents."""
    try:
        return a.is_file() and b.is_file() and a.read_bytes() == b.read_bytes()
    except OSError:
        return False


def install_file(src: Path, dest: Path):
    """Copy src to dest, backing up a different existing dest first. When dest
    already has the same bytes there's nothing to back up or copy, so reruns
    don't pile up identical .backup.<epoch> files."""
    if same_bytes(dest, src):
        print(f"  {dest} is already up to date, no backup needed.")
        return
    backup_path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest)


def dir_has_exactly(d: Path, files):
    """True if d is a real directory holding exactly `files` (name -> source
    path), each a regular file with the same bytes as its source. Replacing
    such a directory loses nothing, so it needs no backup."""
    try:
        if d.is_symlink() or not d.is_dir():
            return False
        entries = {e.name: e for e in d.iterdir()}
        return entries.keys() == files.keys() and all(
            not e.is_symlink() and same_bytes(e, files[name]) for name, e in entries.items())
    except OSError:
        return False


def theme_file(name, theme=None):
    """Path of a file inside tools/themes/<theme>/."""
    return THEMES_DIR / (theme or CHOICE["theme"]) / name


def is_cinnamon():
    env = " ".join(os.environ.get(k, "") for k in
                   ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION"))
    return "cinnamon" in env.lower()


NVCHAD_STARTER = "https://github.com/NvChad/starter"
NVCHAD_THEME_RE = re.compile(r'theme\s*=\s*"[^"]*"')


def set_nvchad_theme(nvchad_theme, regenerate=False):
    """Point NvChad's chadrc at the theme (user + root).

    On a fresh install NvChad builds its theme cache on first launch, so editing
    chadrc is enough. On an existing install the cache must be rebuilt
    (regenerate=True); never delete it, the starter config dofile()s it.
    """
    chadrc = HOME / ".config" / "nvim" / "lua" / "chadrc.lua"
    if chadrc.exists():
        chadrc.write_text(NVCHAD_THEME_RE.sub(f'theme = "{nvchad_theme}"', chadrc.read_text(), count=1))
    root_chadrc = "/root/.config/nvim/lua/chadrc.lua"
    run(["sudo", "sh", "-c",
         f'[ -f {root_chadrc} ] && sed -i \'0,/theme = "[^"]*"/s//theme = "{nvchad_theme}"/\' {root_chadrc} || true'],
        check=False)
    if regenerate and shutil.which("nvim") and chadrc.exists():
        run(["nvim", "--headless", "+lua require('base46').load_all_highlights()", "+qa"], check=False)


BAT_MARKER = "# Managed by Auto-Kitty"


def set_bat_theme(bat_theme):
    """Moonfly: make bat (aliased as cat) use the terminal colors. Classic: bat's default."""
    content = f'{BAT_MARKER} (theme setting)\n--theme="{bat_theme}"\n' if bat_theme else None
    user_cfg = HOME / ".config" / "bat" / "config"
    if content:
        if user_cfg.exists() and BAT_MARKER not in user_cfg.read_text():
            backup_path(user_cfg)
        user_cfg.parent.mkdir(parents=True, exist_ok=True)
        user_cfg.write_text(content)
        run(["sudo", "mkdir", "-p", "/root/.config/bat"])
        subprocess.run(["sudo", "tee", "/root/.config/bat/config"], input=content,
                       text=True, stdout=subprocess.DEVNULL, check=True)
    else:
        if user_cfg.exists() and BAT_MARKER in user_cfg.read_text():
            user_cfg.unlink()
        run(["sudo", "sh", "-c",
             f'grep -qs "{BAT_MARKER}" /root/.config/bat/config && rm -f /root/.config/bat/config || true'],
            check=False)


def save_state(theme):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "theme").write_text(theme + "\n")


"""INSTALL PHASES"""
def preflight():
    print_step("\n[+] Preflight checks...\n")
    if shutil.which("apt") is None:
        sys.exit("ERROR: this installer requires apt (Debian/Ubuntu/Mint).")
    if platform.machine() not in ("x86_64", "amd64"):
        sys.exit(f"ERROR: the pinned downloads (PINNED in main.py) are x86_64-only; detected {platform.machine()}.")
    if shutil.which("sudo") is None:
        sys.exit("ERROR: sudo is required.")
    # Warm up sudo so subsequent steps don't each prompt for a password.
    run(["sudo", "-v"])
    sudo_keepalive()


def apt_prereqs():
    print_step("\n[+] Installing apt prerequisites...\n")
    # One broken third-party repo (expired key: Spotify, Chrome, Docker...)
    # makes `apt-get update` exit 100 even though the Ubuntu/Mint lists were
    # refreshed fine. Warn and carry on; the install below still fails
    # loudly if something we need really can't be fetched.
    if run(APT + ["update"], check=False).returncode != 0:
        note = ("`apt-get update` dio errores en algún repositorio (mira las líneas 'E:' / 'W:' de arriba).\n"
                "    Suele ser un repo de terceros con la clave caducada; la instalación sigue igualmente.\n"
                "    Arréglalo con las instrucciones de ese programa o desactívalo en 'Fuentes de software'.")
        END_NOTES.append(note)
        yellow(); print(f"\n[!] {note}\n"); white()
    run(APT + [
        "install", "-y",
        "curl", "wget", "unzip", "git", "zsh",
        "xz-utils",          # kitty's release is a .txz
        "zsh-autosuggestions", "zsh-syntax-highlighting",
        "ncurses-bin",       # provides `tic`
        "fontconfig",        # fc-cache / fc-list for the Nerd Font check
        "build-essential",   # NvChad compiles treesitter parsers on first launch
        "ripgrep",           # NvChad's Telescope live grep
        "xclip",             # Neovim clipboard on X11 (Cinnamon)
        "wl-clipboard",      # same on Wayland (Cinnamon's Wayland session, Mint 23+)
    ])
    # apt ships fzf 0.44.x on Noble; that's older than 0.48.0 which added
    # `fzf --zsh`. The upstream install script in fzf() writes a `.fzf.zsh`
    # that calls `fzf --zsh`, so /usr/bin/fzf must be gone or it shadows
    # ~/.fzf/bin/fzf on PATH and the shell prints "unknown option: --zsh".
    run(APT + ["remove", "-y", "fzf"], check=False)


def kitty_install():
    print_step("\n[+] Installing Kitty...\n")
    # Official kitty binary release (apt version is too old), installed into
    # ~/.local/kitty.app the same way the official installer.sh does it:
    # extract to a new dir inside a temp dir, delete the old kitty.app, move
    # the new one in. That new dir is made with mkdir (0755 with the usual
    # umask), not mkdtemp, which would leave kitty.app private (0700).
    app = HOME / ".local" / "kitty.app"
    version = PINNED["kitty"]["version"]
    found = has_version(app / "bin" / "kitty", version)
    if found:
        print_kept("kitty", found, version)
    else:
        txz = download_verified("kitty")
        app.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix="kitty-install-", dir=app.parent))
        try:
            new = tmp / "kitty.app"
            new.mkdir()
            run(["tar", "-C", str(new), "-xJof", str(txz)])
            if app.is_symlink() or app.is_file():
                app.unlink()
            elif app.exists():
                shutil.rmtree(app)
            new.rename(app)
        finally:
            if tmp.exists():
                shutil.rmtree(tmp)
        if not has_version(app / "bin" / "kitty", version):
            sys.exit(f"ERROR: {app}/bin/kitty --version doesn't report {version} after installing it.")

    (HOME / ".local" / "bin").mkdir(parents=True, exist_ok=True)
    for binname in ("kitty", "kitten"):
        target = HOME / ".local" / "kitty.app" / "bin" / binname
        link = HOME / ".local" / "bin" / binname
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(target)

    # Desktop integration (menu entry + icon)
    apps_dir = HOME / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    src_apps = HOME / ".local" / "kitty.app" / "share" / "applications"
    shutil.copy(src_apps / "kitty.desktop", apps_dir / "kitty.desktop")
    if (src_apps / "kitty-open.desktop").exists():
        shutil.copy(src_apps / "kitty-open.desktop", apps_dir / "kitty-open.desktop")

    icon = HOME / ".local" / "kitty.app" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "kitty.png"
    exe = HOME / ".local" / "kitty.app" / "bin" / "kitty"
    for desktop in apps_dir.glob("kitty*.desktop"):
        text = desktop.read_text()
        text = text.replace("Icon=kitty", f"Icon={icon}")
        text = text.replace("Exec=kitty", f"Exec={exe}")
        desktop.write_text(text)

    # Back up any existing config, then install ours (no backup when the
    # directory already holds exactly our files, e.g. on a rerun).
    cfg_dir = HOME / ".config" / "kitty"
    files = {"kitty.conf": REPO / "tools" / "kitty" / "kitty.conf",
             "color.ini": theme_file("color.ini")}
    if dir_has_exactly(cfg_dir, files):
        print(f"  {cfg_dir} is already up to date, no backup needed.")
    else:
        backup_path(cfg_dir)
        cfg_dir.mkdir(parents=True, exist_ok=True)
        for name, src in files.items():
            shutil.copy(src, cfg_dir / name)


def kitty_terminfo():
    """Register xterm-kitty terminfo system-wide for tmux/less/ssh-to-self.

    kitty has shipped its terminfo at a few different subpaths inside the
    binary distribution; check the documented ones before giving up.
    """
    print_step("\n[+] Registering xterm-kitty terminfo...\n")
    base = HOME / ".local" / "kitty.app"

    src_candidates = [
        base / "share" / "terminfo" / "kitty.terminfo",
        base / "lib" / "kitty" / "terminfo" / "kitty.terminfo",
    ]
    for src in src_candidates:
        if src.exists():
            run(["sudo", "tic", "-xe", "xterm-kitty", str(src)])
            return

    compiled_candidates = [
        base / "share" / "terminfo" / "x" / "xterm-kitty",
        base / "lib" / "kitty" / "terminfo" / "x" / "xterm-kitty",
    ]
    for compiled in compiled_candidates:
        if compiled.exists():
            run(["sudo", "mkdir", "-p", "/usr/share/terminfo/x"])
            run(["sudo", "cp", str(compiled), "/usr/share/terminfo/x/xterm-kitty"])
            return

    # Last resort: dump kitty's bundled terminfo via infocmp and recompile
    # system-wide. This works regardless of where the file actually lives,
    # as long as one of the candidate TERMINFO dirs above contains it.
    for terminfo_dir in (base / "share" / "terminfo", base / "lib" / "kitty" / "terminfo"):
        if (terminfo_dir / "x" / "xterm-kitty").exists():
            run(
                f'TERMINFO="{terminfo_dir}" infocmp -x xterm-kitty '
                f'| sudo tic -x -o /usr/share/terminfo /dev/stdin',
                shell=True,
                check=False,
            )
            return

    yellow()
    print("WARN: kitty terminfo not found at expected paths; "
          "tmux/ssh may report 'unknown terminal type: xterm-kitty'.")
    print("      The TERMINFO_DIRS fallback in ~/.zshrc will keep "
          "interactive shells working.")
    white()


# Messages shown again at the very end, so they don't get lost in the log.
END_NOTES = []

ZPROFILE_LINE = "[[ -f ~/.profile ]] && emulate sh -c '. ~/.profile'"


def keep_zshrc_extras(old_rc: Path):
    """Keep what other installers (nvm, uv, bun, conda...) appended to an
    Auto-Kitty ~/.zshrc: move it to ~/.zshrc.local, which the new .zshrc
    sources and reinstalls never overwrite. Call before backing up old_rc."""
    if not old_rc.exists():
        return
    lines = old_rc.read_text(errors="replace").splitlines()
    ends = [i for i, line in enumerate(lines)
            if "starship init zsh" in line or line.startswith("zle-line-init() {")]
    if not ends or not any(line.startswith("# Manual aliases") for line in lines):
        END_NOTES.append("Tu ~/.zshrc anterior no era de Auto-Kitty: está guardado como ~/.zshrc.backup.*\n"
                         "    Si tenías PATH, exports o alias propios ahí, cópialos a ~/.zshrc.local")
        return
    extras = "\n".join(lines[ends[-1] + 1:]).strip()
    if not extras:
        return
    local = HOME / ".zshrc.local"
    current = local.read_text() if local.exists() else ""
    if extras in current:
        return
    sep = "\n" if current and not current.endswith("\n") else ""
    local.write_text(f"{current}{sep}\n# Moved here by Auto-Kitty from your previous ~/.zshrc\n{extras}\n")
    green(); print("  Lines added to ~/.zshrc by other installers kept in ~/.zshrc.local"); white()


def zprofile():
    """Login shells (TTY, SSH) read ~/.zprofile, never ~/.profile, so the PATH
    set there (~/bin, ~/.local/bin, cargo, Go...) would be missing. Source it,
    in sh emulation, so login zsh gets the same PATH as login bash."""
    zp = HOME / ".zprofile"
    text = zp.read_text() if zp.exists() else ""
    if ZPROFILE_LINE in text:
        return
    sep = "\n" if text and not text.endswith("\n") else ""
    zp.write_text(f"{text}{sep}# Added by Auto-Kitty: same login PATH as bash (~/.profile)\n{ZPROFILE_LINE}\n")


def warn_about_bashrc():
    """zsh doesn't read ~/.bashrc. Point out PATH/toolchain lines there that
    the new .zshrc doesn't already cover (nvm, ~/.local/bin, cargo and Go are)."""
    rc = HOME / ".bashrc"
    if not rc.exists():
        return
    pat = re.compile(r"PATH=|\b(conda|pyenv|rbenv|sdkman|bun|deno|pnpm|volta|asdf|mise|fnm|direnv)\b")
    local = HOME / ".zshrc.local"
    done = local.read_text() if local.exists() else ""
    hits = [line.strip() for line in rc.read_text(errors="replace").splitlines()
            if pat.search(line) and not line.lstrip().startswith("#")
            and "nvm" not in line.lower() and line.strip() not in done]
    if hits:
        END_NOTES.append("Tu ~/.bashrc configura cosas que zsh no lee. Si las usas, cópialas a ~/.zshrc.local\n"
                         "    (o vuelve a ejecutar su instalador, que ya detectará zsh):\n"
                         + "\n".join(f"        {h}" for h in hits[:15]))


def zsh():
    print_step("\n[+] Configuring ZSH...\n")
    # zsh + plugins were installed in apt_prereqs(). Just change the default shells.
    zsh_bin = shutil.which("zsh") or "/usr/bin/zsh"
    user = pwd.getpwuid(os.getuid()).pw_name
    run(["sudo", "usermod", "--shell", zsh_bin, user])
    run(["sudo", "usermod", "--shell", zsh_bin, "root"])

    # Backup + install .zshrc for user and root
    user_rc = HOME / ".zshrc"
    keep_zshrc_extras(user_rc)
    install_file(REPO / "tools" / "zsh" / ".zshrc", user_rc)
    run(["sudo", "cp", str(REPO / "tools" / "zsh" / ".zshrc"), "/root/.zshrc"])
    zprofile()
    warn_about_bashrc()

    # bat and lsd: pinned musl release binaries (static, so they run on any
    # distro version). Skipped when /usr/local/bin already has that version.
    for tool in ("bat", "lsd"):
        install_release_binary(tool)

    # ohmyzsh sudo plugin, vendored in tools/zsh/plugins/ (MIT, see the
    # .LICENSE file next to it). Also replaces the copy older versions
    # downloaded, which `sudo mv` left owned by the user (root's zsh sources it).
    sudo_plugin_src = REPO / "tools" / "zsh" / "plugins" / "sudo.plugin.zsh"
    sudo_plugin_path = Path("/usr/share/zsh-sudo") / "sudo.plugin.zsh"
    if not (same_bytes(sudo_plugin_path, sudo_plugin_src) and sudo_plugin_path.stat().st_uid == 0):
        run(["sudo", "install", "-D", "-m", "644", str(sudo_plugin_src), str(sudo_plugin_path)])


def hnf():
    print_step("\n[+] Installing Hack Nerd Fonts...\n")
    fonts_dir = HOME / ".local" / "share" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    if list(fonts_dir.glob("Hack*Nerd*.ttf")) or list(fonts_dir.glob("HackNerd*.ttf")):
        print("  Hack Nerd Font already installed, skipping.")
        return

    zip_path = download_verified("hack-nerd-font")

    extract_dir = REPO / "Hack-extracted"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir()
    run(["unzip", "-o", str(zip_path), "-d", str(extract_dir)])

    for f in extract_dir.iterdir():
        if f.name.startswith("Hack") and f.suffix.lower() in (".ttf", ".otf"):
            shutil.move(str(f), str(fonts_dir / f.name))
    run(["fc-cache", "-fv"])

    # Verify — silent box-glyph failures are exactly what we're trying to prevent.
    res = subprocess.run(["fc-list", ":family"], capture_output=True, text=True, check=True)
    if "Hack Nerd Font" not in res.stdout and "HackNerdFont" not in res.stdout:
        sys.exit("ERROR: Hack Nerd Font installation failed — prompt glyphs would render as boxes.")


def starship():
    print_step("\n[+] Installing Starship...\n")
    # Pinned release binary, in /usr/local/bin like the official install.sh.
    install_release_binary("starship")

    install_file(theme_file("starship.toml"), HOME / ".config" / "starship.toml")

    run(["sudo", "mkdir", "-p", "/root/.config"])
    run([
        "sudo", "cp",
        str(theme_file("starship.toml")),
        "/root/.config/starship.toml",
    ])


def fzf():
    print_step("\n[+] Configuring FZF...\n")
    # Clone the upstream repo at the pinned release tag; its install script
    # downloads the fzf binary of that same version and writes the
    # keybindings + completion, non-interactively.
    tag, commit = PINNED["fzf"]["version"], PINNED["fzf"]["commit"]
    for target_str, sudo in ((str(HOME / ".fzf"), False), ("/root/.fzf", True)):
        target = Path(target_str)
        prefix = ["sudo"] if sudo else []
        # Use `test` (via sudo for root paths) instead of Path.exists():
        # Python 3.12+ raises PermissionError on stat() of unreadable paths
        # like /root/* when running as a non-root user.
        exists = subprocess.run(
            prefix + ["test", "-e", str(target), "-o", "-L", str(target)], check=False
        ).returncode == 0
        git = prefix + ["git", "-c", "advice.detachedHead=false"]
        if exists and not is_clean_fzf_clone(target, prefix):
            # Not ours to update in place (own edits, not a clone...): keep it
            # as a backup and start over from a fresh clone.
            yellow()
            print(f"  [!] {target} no es un clon de fzf sin cambios: se guarda una copia y se clona de nuevo.")
            white()
            backup_path(target, sudo=sudo)
            exists = False
        # A clone already at the pinned version or newer is left as it is.
        found = has_version(target / "bin" / "fzf", tag, sudo=sudo) if exists else None
        if found:
            print_kept("fzf", found, tag, f" in {target}")
        elif exists:
            # Older installs cloned master; move them to the pinned tag.
            run(git + ["-C", str(target), "fetch", "--depth=1", "origin", "tag", tag])
            run(git + ["-C", str(target), "checkout", "-q", tag])
        else:
            run(git + [
                "clone", "--depth=1", "--branch", tag,
                PINNED["fzf"]["repo"] + ".git", str(target),
            ])
        head = subprocess.run(prefix + ["git", "-C", str(target), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        if not found and head != commit:
            sys.exit(f"ERROR: {target} is at {head}, but fzf {tag} is pinned to {commit}.")
        # HOME set explicitly: the install script writes $HOME/.fzf.zsh, and
        # not every sudo (e.g. sudo-rs) resets HOME the same way.
        run(prefix + [
            "env", f"HOME={target.parent}",
            str(target / "install"),
            "--key-bindings", "--completion",
            "--no-update-rc", "--no-bash", "--no-fish",
        ])


def is_clean_fzf_clone(d: Path, prefix):
    """True if d is the top of a git clone of fzf with no edits to tracked
    files, so checking out another tag in it loses nothing (untracked files
    stay where they are). prefix: ["sudo"] for /root/.fzf."""
    def git(*args):
        res = subprocess.run(prefix + ["git", "-C", str(d), *args],
                             capture_output=True, text=True, check=False)
        return res.stdout.rstrip("\n") if res.returncode == 0 else None
    repo = PINNED["fzf"]["repo"]
    # --show-prefix is "" only at the top of a work tree (not in a ~ dotfiles repo).
    return (git("rev-parse", "--show-prefix") == ""
            and git("remote", "get-url", "origin") in (repo, repo + ".git")
            and git("status", "--porcelain", "--untracked-files=no") == "")


def is_untouched_nvchad_starter(d: Path):
    """True if d is a clone of the NvChad starter whose only change is the
    theme line we set: every file is then in upstream git, so replacing it
    loses nothing. Anything else (own edits, untracked files such as the
    lazy-lock.json written on first launch, local commits, stashes) -> False."""
    def git(*args):
        res = subprocess.run(["git", "-C", str(d), *args],
                             capture_output=True, text=True, check=False)
        return res.stdout.rstrip("\n") if res.returncode == 0 else None
    if d.is_symlink() or not (d / ".git").is_dir() or shutil.which("git") is None:
        return False
    if git("rev-parse", "--show-toplevel") != str(d.resolve()):
        return False
    if git("remote", "get-url", "origin") not in (NVCHAD_STARTER, NVCHAD_STARTER + ".git"):
        return False
    status = git("status", "--porcelain", "--ignored", "--untracked-files=all")
    if status is None or status.splitlines() not in ([], [" M lua/chadrc.lua"]):
        return False
    if git("stash", "list") != "" or git("rev-list", "HEAD", "--branches", "--not", "--remotes") != "":
        return False
    # Files marked assume-unchanged/skip-worktree hide their edits from status.
    tracked = git("ls-files", "-v")
    if tracked is None or any(not line.startswith("H ") for line in tracked.splitlines()):
        return False
    if status:
        # The theme value must be one we set, not the user's own choice.
        head = git("show", "HEAD:lua/chadrc.lua")
        current = (d / "lua" / "chadrc.lua").read_text().rstrip("\n")
        m = NVCHAD_THEME_RE.search(current)
        ours = {f'theme = "{t["nvchad"]}"' for t in THEMES.values()}
        if head is None or not m or m.group(0) not in ours:
            return False
        if NVCHAD_THEME_RE.sub("", head, count=1) != NVCHAD_THEME_RE.sub("", current, count=1):
            return False
    return True


def nvim():
    print_step("\n[+] Installing Neovim (NvChad)...\n")
    # Clean prior installs so reruns are idempotent. The user's own config is
    # moved aside, never deleted; plugin data/cache can be rebuilt. An
    # untouched starter clone from a previous run needs no backup.
    nvim_cfg = HOME / ".config" / "nvim"
    if is_untouched_nvchad_starter(nvim_cfg):
        print(f"  {nvim_cfg} is an unmodified NvChad starter clone, replacing it without a backup.")
        shutil.rmtree(nvim_cfg)
    else:
        backup_path(nvim_cfg)
    for p in [HOME / ".local" / "share" / "nvim",
              HOME / ".cache" / "nvim"]:
        if p.exists():
            shutil.rmtree(p)
    for p in ["/root/.config/nvim", "/root/.local/share/nvim", "/root/.cache/nvim"]:
        run(["sudo", "rm", "-rf", p])

    # Official release tarball, pinned in PINNED (bump it with
    # scripts/update-pins.py), so random rebuilds can't slide in via "latest".
    # Clean the AppImage downloads older versions of this installer left.
    for stale in REPO.glob("nvim-*.appimage"):
        stale.unlink()
    if (REPO / "squashfs-root").exists():
        shutil.rmtree(REPO / "squashfs-root")

    # Install to /opt/nvim and symlink bin/nvim -> /usr/local/bin/nvim.
    # /opt/nvim may hold an extracted AppImage from an older version; the new
    # tree is extracted and checked first, then swapped in.
    # Old installer left a directory at /usr/bin/nvim — clean that up too, but
    # only if it is that directory (a real /usr/bin/nvim belongs to apt's neovim).
    version = PINNED["nvim"]["version"]
    found = has_version("/opt/nvim/bin/nvim", version)
    if found and os.path.realpath("/usr/local/bin/nvim") == "/opt/nvim/bin/nvim":
        print_kept("Neovim", found, version, " in /opt/nvim")
    else:
        tarball = download_verified("nvim")
        with tempfile.TemporaryDirectory(prefix="akw-nvim-") as tmp:
            new = Path(tmp) / "nvim"
            new.mkdir()
            run(["tar", "-xzf", str(tarball), "-C", str(new), "--no-same-owner", "--strip-components=1"])
            if not has_version(new / "bin" / "nvim", version):
                sys.exit(f"ERROR: the Neovim {version} release doesn't run here ({new}/bin/nvim --version failed).")
            run(["sudo", "rm", "-rf", "/opt/nvim", "/usr/local/bin/nvim"])
            run(["sudo", "sh", "-c", "[ -d /usr/bin/nvim ] && rm -rf /usr/bin/nvim || true"])
            run(["sudo", "mkdir", "-p", "/opt"])
            run(["sudo", "mv", str(new), "/opt/nvim"])
            run(["sudo", "chown", "-R", "root:root", "/opt/nvim"])
        run(["sudo", "ln", "-sf", "/opt/nvim/bin/nvim", "/usr/local/bin/nvim"])

    # NvChad starter config (for user and root)
    run(["git", "clone", NVCHAD_STARTER, str(nvim_cfg)])
    run([
        "sudo", "bash", "-c",
        f"git clone {NVCHAD_STARTER} /root/.config/nvim",
    ])
    set_nvchad_theme(THEMES[CHOICE["theme"]]["nvchad"])


def theme_extras():
    print_step(f"\n[+] Applying the {THEMES[CHOICE['theme']]['name']} theme extras...\n")
    set_bat_theme(THEMES[CHOICE["theme"]]["bat"])
    save_state(CHOICE["theme"])


def desktop():
    print_step("\n[+] Applying the Moonfly desktop theme (Cinnamon)...\n")
    run(["bash", str(DESKTOP_DIR / "apply-desktop.sh")])


def set_default_terminal():
    print_step("\n[+] Setting kitty as the system default terminal...\n")

    kitty_bin = HOME / ".local" / "kitty.app" / "bin" / "kitty"
    if not kitty_bin.exists():
        sys.exit(f"ERROR: {kitty_bin} not found; kitty was not installed.")

    # Cinnamon: panel keybind (Ctrl+Alt+T), nemo "Open Terminal Here", and
    # Mint's "Preferred Applications" GUI all read these two keys. The
    # exec-arg='--' matches X-TerminalArgExec in the kitty .desktop file —
    # kitty uses '--' as the separator before the command to run, not '-e'.
    # Absolute path: ~/.local/bin is only on the session PATH after the next
    # login if it didn't exist yet, and Ctrl+Alt+T should work right away.
    schema = "org.cinnamon.desktop.default-applications.terminal"
    if gsettings_has(schema, "exec"):
        run(["gsettings", "set", schema, "exec", str(kitty_bin)])
        run(["gsettings", "set", schema, "exec-arg", "--"])
    else:
        yellow(); print("  (no Cinnamon terminal setting here; skipping gsettings)"); white()

    # xdg-terminal-exec (used by newer desktops/apps to pick the terminal).
    terms = HOME / ".config" / "xdg-terminals.list"
    lines = terms.read_text().splitlines() if terms.exists() else []
    if not lines or lines[0].strip() != "kitty.desktop":
        terms.parent.mkdir(parents=True, exist_ok=True)
        others = [line for line in lines if line.strip() != "kitty.desktop"]
        terms.write_text("\n".join(["kitty.desktop"] + others) + "\n")

    # Debian-wide alternative — covers scripts/IDEs that hard-code
    # /usr/bin/x-terminal-emulator. Priority 50 beats gnome-terminal's 40;
    # --set pins the choice so apt installs can't silently steal it back.
    run(["sudo", "update-alternatives", "--install",
         "/usr/bin/x-terminal-emulator", "x-terminal-emulator",
         str(kitty_bin), "50"])
    run(["sudo", "update-alternatives", "--set",
         "x-terminal-emulator", str(kitty_bin)])

    green()
    print("\n[+] kitty is now the default terminal.")
    print("    Revertir: gsettings reset org.cinnamon.desktop.default-applications.terminal exec")
    print("              sudo update-alternatives --auto x-terminal-emulator")
    white()


KEYBINDINGS_SCRIPT = REPO / "tools" / "keybindings" / "apply_super_arrows.py"
# Must match SENTINEL in apply_super_arrows.py
KEYBINDINGS_SENTINEL = "# === auto-kitty: super+shift move_window ==="


def keybindings_enabled():
    conf = HOME / ".config" / "kitty" / "kitty.conf"
    return conf.exists() and KEYBINDINGS_SENTINEL in conf.read_text()


def offer_keybindings(flag):
    """Offer the opt-in Super+arrow split shortcuts (Cinnamon only).
    flag = --keybindings / --no-keybindings, or None to ask (Enter = yes)."""
    CHOICE["keybindings"] = False
    if flag is False or not is_cinnamon():
        return
    if keybindings_enabled():
        CHOICE["keybindings"] = True
        return
    if flag is None:
        blue()
        print("\nOptional: Super + arrow keys to move between kitty splits")
        white()
        print("  kitty can split one window into several terminals side by side")
        print("  (F5 / F6 create a split). These shortcuts make working with them fast:")
        print()
        print("    Super + arrows          jump to the split on the left / right / up / down")
        print("    Super + Shift + arrows  move the current split to that side (reorder them)")
        print()
        print("  Super is the Windows key. Cinnamon uses those same keys to snap windows to")
        print("  half the screen (Super + arrows) and to send them to another monitor")
        print("  (Super + Shift + arrows), so those Cinnamon shortcuts are turned off to let")
        print("  kitty receive the keys. Super + H/J/K/L keep working either way.")
        blue()
        if not ask_yes_no("\nEnable these shortcuts?"):
            white()
            return
        white()
    try:
        run([sys.executable, str(KEYBINDINGS_SCRIPT)])
        CHOICE["keybindings"] = True
    except subprocess.CalledProcessError as e:
        red()
        print(f"\n[!] Could not enable the Super + arrow shortcuts (exit {e.returncode}).")
        print("    Everything else is installed; you can retry later with the command below.")
        white()


def print_end_notes():
    yellow()
    for note in END_NOTES:
        print(f"\n[!] {note}")
    print("\n[!] IMPORTANTE: cierra sesión y vuelve a entrar para que zsh sea tu shell por defecto.")
    print("    Para probarlo inmediatamente en esta terminal: `exec zsh`")
    print("\n[!] Si aceptaste cambiar la terminal por defecto:")
    print("    -> Cinnamon usará kitty para Ctrl+Alt+T, el panel y nemo 'Abrir terminal aquí'.")
    print("    -> Cierra sesión para que todos los procesos hereden la nueva configuración.")
    if CHOICE.get("keybindings"):
        print("\n[!] Atajos Super+flechas activados: muévete entre splits con Super+flechas")
        print("    y reordénalos con Super+Shift+flechas (reabre kitty para usarlos).")
    elif is_cinnamon():
        print("\n[!] Opcional (solo Cinnamon): si quieres Super+flechas para moverte entre splits")
        print("    y Super+Shift+flechas para reordenarlos, ejecuta:")
        print(f"        python3 {shlex.quote(str(KEYBINDINGS_SCRIPT))}")
    print(f"\n[!] Tema instalado: {THEMES[CHOICE['theme']]['name']}. Para cambiarlo más tarde sin reinstalar:")
    print(f"        python3 {shlex.quote(str(REPO / 'main.py'))} --switch-theme classic     (o moonfly)")
    if CHOICE["desktop"]:
        print("\n[!] Escritorio Moonfly aplicado. Tamaño/estilo de los contadores de la barra:")
        print(f"        bash {shlex.quote(str(DESKTOP_DIR / 'set-badges.sh'))} 11 black"
              "     (tamaño 8-14, black o colored)")
        print("    Para deshacerlo, usa el comando 'To undo' que se mostró arriba.")
    white()


PHASES = [
    ("preflight",      preflight),
    ("apt-prereqs",    apt_prereqs),
    ("kitty",          kitty_install),
    ("kitty-terminfo", kitty_terminfo),
    ("zsh",            zsh),
    ("hack-nerd-fonts", hnf),
    ("starship",       starship),
    ("fzf",            fzf),
    ("nvim",           nvim),
    ("theme-extras",   theme_extras),
]


def install():
    completed = []
    phases = PHASES + ([("desktop", desktop)] if CHOICE["desktop"] else [])
    for name, fn in phases:
        try:
            fn()
            completed.append(name)
        except subprocess.CalledProcessError as e:
            red()
            print(f"\n[!!!] Phase '{name}' failed: command exited {e.returncode}")
            print(f"      Command: {e.cmd}")
            white()
            print(f"\nCompleted before failure: {', '.join(completed) or '(none)'}")
            sys.exit(1)
        except Exception as e:
            red()
            print(f"\n[!!!] Phase '{name}' failed: {type(e).__name__}: {e}")
            white()
            print(f"\nCompleted before failure: {', '.join(completed) or '(none)'}")
            sys.exit(1)


"""MENU AND THEME SWITCHING"""
def ask_yes_no(text, eof_answer=False):
    """Yes/no question shown as (Y/n): Enter means yes. Accepts y/yes/s/si/sí
    and n/no in any case, ignoring surrounding spaces.

    With no terminal attached (EOF, e.g. stdin from /dev/null) nobody can
    answer, so return eof_answer: False by default, because every question
    here changes system settings. Use the CLI flags (or --yes) to say yes."""
    while True:
        try:
            r = input(f"{text} (Y/n): ").strip().lower()
        except EOFError:
            # Same language as the question (the Spanish ones start with ¿).
            note = "(sin terminal)" if text.lstrip().startswith("¿") else "(no terminal)"
            print("y" if eof_answer else "n", note)
            return eof_answer
        if r in ("", "y", "yes", "s", "si", "sí"):
            return True
        if r in ("n", "no"):
            return False
        print("\nPlease answer y (yes) or n (no). Press Enter for yes.\n")


def choose_theme():
    keys = list(THEMES)
    blue(); print("\nElige el estilo del workspace:\n")
    for i, key in enumerate(keys, 1):
        white(); print(f"  [{i}] {THEMES[key]['name']:<8} {THEMES[key]['desc']}")
    blue()
    while True:
        try:
            r = input(f"\nOpción [1-{len(keys)}] (Enter = 1): ").strip().lower()
        except EOFError:          # no terminal attached: same as Enter
            print(f"\n[i] Sin terminal para responder: se usa {THEMES[keys[0]]['name']} (elige otro con --theme).")
            return keys[0]
        if r == "":
            return keys[0]
        if r.isdigit() and 1 <= int(r) <= len(keys):
            return keys[int(r) - 1]
        if r in THEMES:
            return r
        print(f"Responde un número del 1 al {len(keys)}.")


def decide_desktop(flag):
    """Moonfly only: also theme the Cinnamon desktop? flag = --desktop/--no-desktop or None."""
    if flag is False:
        return False
    if not is_cinnamon():
        yellow()
        print("\n[i] El tema de escritorio Moonfly es solo para Cinnamon; no se aplicará aquí.")
        white()
        return False
    if flag is True:
        return True
    blue()
    return ask_yes_no("\n¿Aplicar también el escritorio Moonfly (ventanas negras con verde, "
                      "panel negro, iconos Papirus)?")


LEGACY_KITTY_LINES = [re.compile(p) for p in (
    r"^#*\s*url_color\s+#61afef\s*$",               # classic colors that used to live in kitty.conf
    r"^#*\s*inactive_tab_background\s+#e06c75\s*$",
    r"^#*\s*inactive_tab_foreground\s+#000000\s*$",
    r"^#*\s*active_tab_background\s+#98c379\s*$",
    r"^#*\s*tab_bar_margin_color\s+\S+\s*$",       # now set by each theme's color.ini
    r"^inactive_text_alpha 0\.75$",                  # older Moonfly patch; now in moonfly/color.ini
    r"^# Dim the text in splits you're not typing in, so the active one is obvious$",
    r"^# even with 5-8 terminals open\. 1\.0 = no dimming\.$",
)]


def clean_kitty_conf(path):
    """Bring an older kitty.conf up to date without touching the user's own keybindings."""
    out, in_kitten_block = [], False
    for line in path.read_text().splitlines():
        if line.startswith("# BEGIN_KITTY_THEME"):   # left by `kitten themes`
            in_kitten_block = True
            continue
        if in_kitten_block:
            in_kitten_block = not line.startswith("# END_KITTY_THEME")
            continue
        if any(p.match(line) for p in LEGACY_KITTY_LINES):
            continue
        if re.match(r"^#\s*include color\.ini\s*$", line):
            line = "include color.ini"
        out.append(line)
    if "include color.ini" not in out:
        out.insert(0, "include color.ini")
    if not any(line.startswith("scrollback_lines") for line in out):
        out.append("scrollback_lines 10000")
    text = re.sub(r"\n{4,}", "\n\n\n", "\n".join(out) + "\n")
    path.write_text(text)


def switch_theme(theme, desktop_flag):
    """--switch-theme: re-theme an existing install (kitty, prompt, bat, NvChad) without reinstalling."""
    CHOICE["theme"] = theme
    kitty_dir = HOME / ".config" / "kitty"
    if not (kitty_dir / "kitty.conf").exists():
        sys.exit("ERROR: no encuentro ~/.config/kitty/kitty.conf. Ejecuta primero: python3 main.py")
    print_step(f"\n[+] Cambiando al tema {THEMES[theme]['name']}...\n")
    run(["sudo", "-v"])

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup, n = STATE_DIR / f"backup-{stamp}", 1
    while backup.exists():
        n += 1
        backup = STATE_DIR / f"backup-{stamp}-{n}"
    backup.mkdir(parents=True)
    for f in (kitty_dir / "kitty.conf", kitty_dir / "color.ini", HOME / ".config" / "starship.toml"):
        if f.exists():
            shutil.copy(f, backup / f.name)
    yellow(); print(f"  Backup de tu configuración actual: {backup}"); white()

    clean_kitty_conf(kitty_dir / "kitty.conf")
    shutil.copy(theme_file("color.ini"), kitty_dir / "color.ini")
    shutil.copy(theme_file("starship.toml"), HOME / ".config" / "starship.toml")
    run(["sudo", "mkdir", "-p", "/root/.config"])
    run(["sudo", "cp", str(theme_file("starship.toml")), "/root/.config/starship.toml"])
    set_bat_theme(THEMES[theme]["bat"])
    set_nvchad_theme(THEMES[theme]["nvchad"], regenerate=True)
    save_state(theme)

    if theme == "moonfly":
        CHOICE["desktop"] = decide_desktop(desktop_flag)
        if CHOICE["desktop"]:
            desktop()
    else:
        backups = sorted(HOME.glob("theme-backup-desktop-*/restore.sh"))
        if backups and desktop_flag is not False and is_cinnamon():
            blue()
            if desktop_flag or ask_yes_no("\n¿Restaurar también el escritorio original de Mint?"):
                run(["bash", str(backups[0])])
            white()

    green()
    print(f"\n[+] Tema {THEMES[theme]['name']} aplicado.")
    print("    -> En kitty pulsa Ctrl+Shift+F5 (o abre una ventana nueva) para ver los colores.")
    print("    -> El prompt se actualiza al pulsar Enter.")
    print(f"    -> Para deshacer: copia los archivos de {backup} a su sitio.")
    white()


def flag_or_yes(flag, yes):
    """Answer for a question with a --x/--no-x flag: an explicit flag always
    wins; otherwise --yes means yes; None means ask."""
    return True if flag is None and yes else flag


def parse_args():
    p = argparse.ArgumentParser(
        description="Auto-Kitty-Workspace installer",
        epilog="Explicit --x / --no-x flags always win over --yes "
               "(e.g. --yes --no-desktop answers yes to everything except the desktop).")
    p.add_argument("--theme", choices=list(THEMES),
                   help="install this theme without showing the menu")
    p.add_argument("--desktop", action=argparse.BooleanOptionalAction, default=None,
                   help="also apply (or skip) the matching Cinnamon desktop theme (moonfly only)")
    p.add_argument("--keybindings", action=argparse.BooleanOptionalAction, default=None,
                   help="also enable (or skip) the Super+arrow split shortcuts (Cinnamon only)")
    p.add_argument("--default-terminal", action=argparse.BooleanOptionalAction, default=None,
                   help="make kitty the system default terminal (or leave it), without asking")
    p.add_argument("-y", "--yes", action="store_true",
                   help="answer yes to every yes/no question not set by a flag above "
                        "(the theme menu still needs --theme to be skipped)")
    p.add_argument("--switch-theme", choices=list(THEMES), metavar="THEME",
                   help="only change the theme of an existing install (classic or moonfly)")
    return p.parse_args()


"""MAIN PROGRAM"""
if __name__ == '__main__':
    # Kept on purpose for older interpreters, even though ruff assumes 3.9+.
    if sys.version_info < (3, 9):  # noqa: UP036
        sys.exit("ERROR: Python 3.9 or newer is required.")
    if os.geteuid() == 0:
        sys.exit("ERROR: no lo ejecutes con sudo ni como root; usa: python3 main.py\n"
                 "       (te pedirá la contraseña cuando haga falta)")
    args = parse_args()
    purple()
    print(BANNER)

    if args.switch_theme:
        switch_theme(args.switch_theme, flag_or_yes(args.desktop, args.yes))
        sys.exit(0)

    CHOICE["theme"] = args.theme or choose_theme()
    if CHOICE["theme"] == "moonfly":
        CHOICE["desktop"] = decide_desktop(flag_or_yes(args.desktop, args.yes))
    elif args.desktop:
        yellow(); print("\n[i] --desktop solo aplica al tema moonfly; se ignora."); white()

    install()

    default_terminal = flag_or_yes(args.default_terminal, args.yes)
    if default_terminal is None:
        blue()
        default_terminal = ask_yes_no("\n¿Deseas cambiar la terminal por defecto?")
        white()
    if default_terminal:
        try:
            set_default_terminal()
        except subprocess.CalledProcessError as e:
            red()
            print(f"\n[!] No se pudo poner kitty como terminal por defecto (exit {e.returncode}): {e.cmd}")
            print("    El resto de la instalación está bien; puedes elegir kitty en Aplicaciones preferidas.")
            white()

    offer_keybindings(flag_or_yes(args.keybindings, args.yes))

    print_end_notes()
    green()
    print("\n[+] La instalación y la configuración de la terminal se ha realizado correctamente.")
    print("    Abre Kitty desde el menú de aplicaciones para comprobarlo.")
    print("Disfruta <3")
    white()

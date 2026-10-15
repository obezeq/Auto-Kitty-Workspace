#!/usr/bin/env bash
# Install test in a throwaway docker container.
#
# Usage: tests/container-test.sh [-i IMAGE] [-r REPO] [-u OLD_REPO] [-- INSTALLER_ARGS...]
#   -i IMAGE  docker image (default: linuxmintd/mint22.3-amd64; ubuntu:24.04 works too)
#   -r REPO   repo to test (default: this script's repo); tracked + untracked,
#             non-ignored files are copied in (not Hack.zip or other downloads)
#   -u OLD_REPO  upgrade test: first install OLD_REPO (e.g. a git worktree of an
#             older commit) as run 0, then swap its files for REPO's, keeping
#             what it downloaded, like a `git pull`. INSTALLER_ARGS must work
#             with both versions.
#   INSTALLER_ARGS  passed to main.py (default: --theme classic --no-desktop --no-keybindings)
#   KEEP_CONTAINER=1 leaves the container running afterwards for debugging.
#
# Runs main.py twice (after run 0 with -u) as a normal user with passwordless
# sudo and stdin from /dev/null, and prints a key=value summary after each run
# (runN.*) plus an idempotency check. Exits non-zero if a run fails or `zsh -i`
# errors.
# Example: tests/container-test.sh -i ubuntu:24.04 > /tmp/akw.log 2>&1
set -euo pipefail

image=linuxmintd/mint22.3-amd64
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
old_repo=
while getopts "i:r:u:h" opt; do
    case $opt in
        i) image=$OPTARG ;;
        r) repo=$(cd "$OPTARG" && pwd) ;;
        u) old_repo=$(cd "$OPTARG" && pwd) ;;
        h) sed -n '2,19s/^# \{0,1\}//p' "$0"; exit 0 ;;
        *) exit 2 ;;
    esac
done
shift $((OPTIND - 1))
args=("$@")
[ ${#args[@]} -gt 0 ] || args=(--theme classic --no-desktop --no-keybindings)

user=tester
home=/home/$user
dest=$home/Auto-Kitty-Workspace

cid=$(docker run -d "$image" sleep infinity)
# shellcheck disable=SC2329  # called by the trap below
cleanup() {
    if [ "${KEEP_CONTAINER:-}" = 1 ]; then echo "container kept: $cid"; else docker rm -f "$cid" >/dev/null; fi
}
trap cleanup EXIT
echo "image=$image container=${cid:0:12} repo=$repo${old_repo:+ upgrade_from=$old_repo} args=${args[*]}"

# Just what a desktop install already has and the README asks for.
docker exec -e DEBIAN_FRONTEND=noninteractive "$cid" bash -c "
    set -e
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends sudo python3 ca-certificates curl git >/dev/null
    useradd -m -s /bin/bash $user
    echo '$user ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/$user
    mkdir $dest"

# NUL-separated list of the files of repo $1 to copy in.
repo_files() {
    if git -C "$1" rev-parse --git-dir >/dev/null 2>&1; then
        git -C "$1" ls-files -z -co --exclude-standard
    else
        (cd "$1" && find . -type f -print0)
    fi
}

# Copy (not bind-mount): the installer writes downloads into the repo dir.
copy_repo() {
    repo_files "$1" | tar -C "$1" --null --ignore-failed-read -T - -cf - |
        docker exec -i "$cid" tar -C "$dest" -xf -
    docker exec "$cid" chown -R "$user:$user" "$dest"
}

# With -u: run 0 installs OLD_REPO; then its files are swapped for REPO's
# before run 1, leaving what run 0 downloaded into the dir (like `git pull`).
copy_repo "${old_repo:-$repo}"
upgrade_repo() {
    echo; echo "===== upgrade: replacing $old_repo with $repo ====="
    repo_files "$old_repo" | docker exec -i -w "$dest" "$cid" xargs -0 rm -f --
    copy_repo "$repo"
}

in_container() { docker exec -u "$user" -w "$dest" -e HOME="$home" -e USER="$user" "$@"; }

run_installer() {
    in_container "$cid" sh -c 'exec python3 main.py "$@" </dev/null' sh "${args[@]}"
}

# Prints runN.key=value lines; $1=run number, $2=exit code, $3=duration.
summary() {
    in_container -i -e TERM=xterm-kitty "$cid" bash -s -- "$@" <<'EOF'
p=run$1
export PATH="$HOME/.local/bin:$HOME/.fzf/bin:/usr/local/bin:$PATH"
echo "$p.exit=$2"
echo "$p.duration_s=$3"
ver() { local v; v=$("$@" 2>/dev/null | head -n1); echo "${v:-MISSING}"; }
bat=bat; command -v bat >/dev/null || bat=batcat
for t in kitty starship nvim "$bat" lsd fzf zsh; do echo "$p.version.$t=$(ver "$t" --version)"; done
echo "$p.login_shell=$(getent passwd "$(id -un)" | cut -d: -f7)"
echo "$p.hack_font_files=$(fc-list 2>/dev/null | grep -ci hack)"
for f in .zshrc .config/kitty/kitty.conf .config/starship.toml .config/nvim; do
    [ -e "$HOME/$f" ] && echo "$p.exists.~/$f=yes" || echo "$p.exists.~/$f=no"
done
# Under a pty like a real terminal: without one, fzf's key bindings print
# "can't change option: zle". Any output from `zsh -i -c exit` is an error.
err=$(set -o pipefail; script -qec "zsh -i -c exit" /dev/null </dev/null 2>&1 | tr -d '\r'); rc=$?
echo "$p.zsh_i.exit=$rc"
echo "$p.zsh_i.output_lines=$(printf '%s' "$err" | grep -c '')"
[ -z "$err" ] || printf '%s\n' "$err" | sed "s/^/$p.zsh_i.output: /"
# Hooks the .zshrc registers (zle-line-init sets the beam cursor).
for w in zle-line-init zle-keymap-select; do
    echo "$p.zle.$w=$(script -qec "zsh -i -c 'print -r -- \${widgets[$w]:-unset}'" /dev/null </dev/null 2>&1 | tr -d '\r')"
done
sp=/usr/share/zsh-sudo/sudo.plugin.zsh
[ -f "$sp" ] && echo "$p.sudo_plugin=$(stat -c '%U:%G %a' "$sp") $(sha256sum "$sp" | cut -c1-12)" || echo "$p.sudo_plugin=MISSING"
echo "$p.x_terminal_emulator=$(readlink -f /etc/alternatives/x-terminal-emulator 2>/dev/null || echo none)"
backups=$(find "$HOME" -maxdepth 3 -name '*.backup.*' | sort)
echo "$p.backup_count=$(printf '%s' "$backups" | grep -c '')"
[ -z "$backups" ] || printf '%s\n' "$backups" | sed "s/^/$p.backup=/"
echo "$p.state_dir=$(ls -A "$HOME/.config/auto-kitty" 2>/dev/null | tr '\n' ' ')"
EOF
}

get() { sed -n "s/^$1=//p" <<<"$2"; }

failed=0
declare -A out
for n in ${old_repo:+0} 1 2; do
    [ "$n" != 1 ] || [ -z "$old_repo" ] || upgrade_repo
    echo; echo "===== installer run $n ====="
    start=$SECONDS rc=0
    run_installer || rc=$?
    echo; echo "===== summary run $n ====="
    out[$n]=$(summary "$n" "$rc" $((SECONDS - start)))
    echo "${out[$n]}"
    [ "$rc" = 0 ] || failed=1
    [ "$(get "run$n.zsh_i.exit" "${out[$n]}")" = 0 ] || failed=1
    [ "$(get "run$n.zsh_i.output_lines" "${out[$n]}")" = 0 ] || failed=1
done

echo; echo "===== idempotency ====="
echo "idempotency.run2_exit=$(get run2.exit "${out[2]}")"
b1=$(get run1.backup_count "${out[1]}") b2=$(get run2.backup_count "${out[2]}")
echo "idempotency.new_backups_run2=$(( ${b2:-0} - ${b1:-0} ))"
if [ -n "$old_repo" ]; then
    b0=$(get run0.backup_count "${out[0]}")
    echo "upgrade.new_backups_run1=$(( ${b1:-0} - ${b0:-0} ))"
fi
echo "result=$([ "$failed" = 0 ] && echo PASS || echo FAIL)"
exit "$failed"

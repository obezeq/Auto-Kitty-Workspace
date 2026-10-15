#!/usr/bin/env bash
# Install test in a throwaway docker container.
#
# Usage: tests/container-test.sh [-i IMAGE] [-r REPO] [-- INSTALLER_ARGS...]
#   -i IMAGE  docker image (default: linuxmintd/mint22.3-amd64; ubuntu:24.04 works too)
#   -r REPO   repo to test (default: this script's repo); tracked + untracked,
#             non-ignored files are copied in (not Hack.zip, nvim-*.appimage...)
#   INSTALLER_ARGS  passed to main.py (default: --theme classic --no-desktop --no-keybindings)
#   KEEP_CONTAINER=1 leaves the container running afterwards for debugging.
#
# Runs main.py twice as a normal user with passwordless sudo and stdin from
# /dev/null, and prints a key=value summary after each run (runN.*) plus an
# idempotency check. Exits non-zero if a run fails or `zsh -i` errors.
# Example: tests/container-test.sh -i ubuntu:24.04 > /tmp/akw.log 2>&1
set -euo pipefail

image=linuxmintd/mint22.3-amd64
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
while getopts "i:r:h" opt; do
    case $opt in
        i) image=$OPTARG ;;
        r) repo=$(cd "$OPTARG" && pwd) ;;
        h) sed -n '2,14s/^# \{0,1\}//p' "$0"; exit 0 ;;
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
echo "image=$image container=${cid:0:12} repo=$repo args=${args[*]}"

# Just what a desktop install already has and the README asks for.
docker exec -e DEBIAN_FRONTEND=noninteractive "$cid" bash -c "
    set -e
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends sudo python3 ca-certificates curl git >/dev/null
    useradd -m -s /bin/bash $user
    echo '$user ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/$user
    mkdir $dest"

# Copy (not bind-mount): the installer writes downloads into the repo dir.
if git -C "$repo" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$repo" ls-files -z -co --exclude-standard |
        tar -C "$repo" --null --ignore-failed-read -T - -cf -
else
    tar -C "$repo" -cf - .
fi | docker exec -i "$cid" tar -C "$dest" -xf -
docker exec "$cid" chown -R "$user:$user" "$dest"

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
backups=$(find "$HOME" -maxdepth 3 -name '*.backup.*' | sort)
echo "$p.backup_count=$(printf '%s' "$backups" | grep -c '')"
[ -z "$backups" ] || printf '%s\n' "$backups" | sed "s/^/$p.backup=/"
echo "$p.state_dir=$(ls -A "$HOME/.config/auto-kitty" 2>/dev/null | tr '\n' ' ')"
EOF
}

get() { sed -n "s/^$1=//p" <<<"$2"; }

failed=0
declare -A out
for n in 1 2; do
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
echo "result=$([ "$failed" = 0 ] && echo PASS || echo FAIL)"
exit "$failed"

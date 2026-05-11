"""Opt-in: enable Super+arrows / Super+Shift+arrows for kitty split nav.

This script does two paired things that the base installer intentionally
leaves alone:

  1. Clears Cinnamon's Super+arrow window-tiling shortcuts (otherwise the
     desktop intercepts the keys and kitty never sees them).
  2. Appends `super+shift+arrow -> move_window` mappings to the user's
     installed `~/.config/kitty/kitty.conf` so the active split can be
     swapped with its neighbour.

Run it AFTER `python3 main.py` finishes:

    python3 tools/keybindings/apply_super_arrows.py

Cinnamon only. On GNOME/KDE clear the equivalent Super+arrow tiling
shortcuts manually before running anything similar.
"""

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


HOME = Path.home()
KITTY_CONF = HOME / ".config" / "kitty" / "kitty.conf"

SENTINEL = "# === auto-kitty: super+shift move_window ==="

BLOCK = f"""
{SENTINEL}
# Mover el split actual (Super+Shift+Arrows)
# Requiere haber liberado move-to-monitor en Cinnamon
map super+shift+left  move_window left
map super+shift+right move_window right
map super+shift+up    move_window up
map super+shift+down  move_window down
"""

CINNAMON_KEYS_TO_CLEAR = [
    "push-tile-left",
    "push-tile-right",
    "push-tile-up",
    "push-tile-down",
    "move-to-monitor-left",
    "move-to-monitor-right",
    "move-to-monitor-up",
    "move-to-monitor-down",
]


def run(cmd):
    """Same shape as main.py's helper: echo + check=True so failures abort."""
    display = " ".join(shlex.quote(c) for c in cmd)
    print(f"  $ {display}")
    return subprocess.run(cmd, check=True)


def require_cinnamon():
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    if "Cinnamon" not in desktop:
        sys.exit(
            "ERROR: this script only supports Cinnamon "
            f"(XDG_CURRENT_DESKTOP={desktop!r}).\n"
            "On GNOME/KDE/XFCE clear the equivalent Super+arrow tiling "
            "shortcuts manually before re-running."
        )
    if shutil.which("gsettings") is None:
        sys.exit("ERROR: gsettings not found; is Cinnamon actually installed?")


def clear_cinnamon_keys():
    print("\n[+] Clearing Cinnamon Super+arrow tiling shortcuts...")
    for key in CINNAMON_KEYS_TO_CLEAR:
        run(["gsettings", "set", "org.cinnamon.desktop.keybindings.wm", key, "[]"])
        print(f"  [ok] cleared {key}")


def append_kitty_bindings():
    print("\n[+] Adding Super+Shift+arrow mappings to kitty.conf...")
    if not KITTY_CONF.exists():
        sys.exit(
            f"ERROR: {KITTY_CONF} does not exist. "
            "Run `python3 main.py` first so the base config is installed."
        )

    current = KITTY_CONF.read_text()
    if SENTINEL in current:
        print(f"  [ok] sentinel already present in {KITTY_CONF}; skipping append.")
        return

    suffix = "" if current.endswith("\n") else "\n"
    KITTY_CONF.write_text(current + suffix + BLOCK)
    print(f"  [ok] appended block to {KITTY_CONF}")


def main():
    require_cinnamon()
    clear_cinnamon_keys()
    append_kitty_bindings()
    print(
        "\n[+] Done.\n"
        "    Reopen kitty (or run `kitty @ load-config` inside a kitty window)\n"
        "    so the new mappings take effect. Cinnamon picks up the dconf\n"
        "    change immediately."
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"\n[!!!] command failed (exit {e.returncode}): {e.cmd}")

import argparse
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
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


"""LOGOTIPO DE LA APLICACIÓN"""
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


"""COLORES"""
def red():  # Rojo
    stdout.write("\033[1;31m")


def green():  # Verde
    stdout.write("\033[0;32m")


def blue():  # Azul
    stdout.write("\033[1;34m")


def yellow():  # Amarillo
    stdout.write("\033[1;33m")


def orange():  # Naranja
    stdout.write("\033[1;38;5;208m")


def white():  # Blanco
    stdout.write("\033[1;37m")


def purple():  # Morado
    stdout.write("\033[1;35m")


def cyan():  # Cian
    stdout.write("\033[1;36m")


def light_gray():  # Gris claro
    stdout.write("\033[0;37m")


def dark_gray():  # Gris oscuro
    stdout.write("\033[1;30m")


def light_blue():  # Azul claro
    stdout.write("\033[1;94m")


"""HELPERS"""
def run(cmd, *, shell=False, check=True, cwd=None, env=None):
    """All shell calls go through here. check=True so failures abort."""
    display = cmd if isinstance(cmd, str) else " ".join(shlex.quote(c) for c in cmd)
    cyan(); print(f"  $ {display}"); white()
    if isinstance(cmd, str) and not shell:
        cmd = shlex.split(cmd)
    return subprocess.run(cmd, shell=shell, check=check, cwd=cwd, env=env)


def mostrar_progeso(texto):
    orange()
    print(texto)
    white()


def backup_path(p: Path):
    """Move existing file/dir aside with a timestamped suffix; no-op if absent."""
    if not p.exists():
        return None
    backup = p.with_name(f"{p.name}.backup.{int(time.time())}")
    shutil.move(str(p), str(backup))
    yellow(); print(f"  Backed up {p} -> {backup}"); white()
    return backup


def theme_file(name, theme=None):
    """Path of a file inside tools/themes/<theme>/."""
    return THEMES_DIR / (theme or CHOICE["theme"]) / name


def is_cinnamon():
    env = " ".join(os.environ.get(k, "") for k in
                   ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION"))
    return "cinnamon" in env.lower()


def set_nvchad_theme(nvchad_theme, regenerate=False):
    """Point NvChad's chadrc at the theme (user + root).

    On a fresh install NvChad builds its theme cache on first launch, so editing
    chadrc is enough. On an existing install the cache must be rebuilt
    (regenerate=True); never delete it, the starter config dofile()s it.
    """
    pattern = re.compile(r'theme\s*=\s*"[^"]*"')
    chadrc = HOME / ".config" / "nvim" / "lua" / "chadrc.lua"
    if chadrc.exists():
        chadrc.write_text(pattern.sub(f'theme = "{nvchad_theme}"', chadrc.read_text(), count=1))
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


"""FUNCIONES PRINCIPALES"""
def preflight():
    mostrar_progeso("\n[+] Preflight checks...\n")
    if shutil.which("apt") is None:
        sys.exit("ERROR: this installer requires apt (Debian/Ubuntu/Mint).")
    if platform.machine() not in ("x86_64", "amd64"):
        sys.exit(f"ERROR: bundled .deb packages are amd64-only; detected {platform.machine()}.")
    # Warm up sudo so subsequent steps don't each prompt for a password.
    run(["sudo", "-v"])


def apt_prereqs():
    mostrar_progeso("\n[+] Installing apt prerequisites...\n")
    run(["sudo", "apt", "update"])
    run([
        "sudo", "apt", "install", "-y",
        "curl", "wget", "unzip", "git", "zsh",
        "zsh-autosuggestions", "zsh-syntax-highlighting",
        "ncurses-bin",  # ncurses-bin provides `tic`
    ])
    # apt ships fzf 0.44.x on Noble; that's older than 0.48.0 which added
    # `fzf --zsh`. The upstream install script in fzf() writes a `.fzf.zsh`
    # that calls `fzf --zsh`, so /usr/bin/fzf must be gone or it shadows
    # ~/.fzf/bin/fzf on PATH and the shell prints "unknown option: --zsh".
    run(["sudo", "apt", "remove", "-y", "fzf"], check=False)


def kitty_install():
    mostrar_progeso("\n[+] Installing Kitty...\n")
    # Official kitty installer (apt version is too old)
    run("curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin", shell=True)

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
    for desktop in ("kitty.desktop", "kitty-open.desktop"):
        shutil.copy(src_apps / desktop, apps_dir / desktop)

    icon = HOME / ".local" / "kitty.app" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "kitty.png"
    exe = HOME / ".local" / "kitty.app" / "bin" / "kitty"
    for desktop in apps_dir.glob("kitty*.desktop"):
        text = desktop.read_text()
        text = text.replace("Icon=kitty", f"Icon={icon}")
        text = text.replace("Exec=kitty", f"Exec={exe}")
        desktop.write_text(text)

    # Back up any existing config, then install ours
    cfg_dir = HOME / ".config" / "kitty"
    backup_path(cfg_dir)
    cfg_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "tools" / "kitty" / "kitty.conf", cfg_dir / "kitty.conf")
    shutil.copy(theme_file("color.ini"), cfg_dir / "color.ini")


def kitty_terminfo():
    """Register xterm-kitty terminfo system-wide for tmux/less/ssh-to-self.

    kitty has shipped its terminfo at a few different subpaths inside the
    binary distribution; check the documented ones before giving up.
    """
    mostrar_progeso("\n[+] Registering xterm-kitty terminfo...\n")
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


def zsh():
    mostrar_progeso("\n[+] Configuring ZSH...\n")
    # zsh + plugins were installed in apt_prereqs(). Just change the default shells.
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    if user:
        run(["sudo", "usermod", "--shell", "/usr/bin/zsh", user])
    run(["sudo", "usermod", "--shell", "/usr/bin/zsh", "root"])

    # Backup + install .zshrc for user and root
    user_rc = HOME / ".zshrc"
    backup_path(user_rc)
    shutil.copy(REPO / "tools" / "zsh" / ".zshrc", user_rc)
    run(["sudo", "cp", str(REPO / "tools" / "zsh" / ".zshrc"), "/root/.zshrc"])

    # Bundled .deb plugins (bat, lsd) — apt install resolves deps, dpkg -i doesn't.
    debs = sorted(str(p) for p in (REPO / "tools" / "zsh" / "plugins").glob("*.deb"))
    if debs:
        run(["sudo", "apt", "install", "-y"] + debs)

    # ohmyzsh sudo plugin
    sudo_plugin_dir = Path("/usr/share/zsh-sudo")
    sudo_plugin_path = sudo_plugin_dir / "sudo.plugin.zsh"
    if not sudo_plugin_path.exists():
        tmp = REPO / "sudo.plugin.zsh"
        run([
            "wget", "-O", str(tmp),
            "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/plugins/sudo/sudo.plugin.zsh",
        ])
        run(["sudo", "mkdir", "-p", str(sudo_plugin_dir)])
        run(["sudo", "mv", str(tmp), str(sudo_plugin_path)])


def hnf():
    mostrar_progeso("\n[+] Installing Hack Nerd Fonts...\n")
    fonts_dir = HOME / ".local" / "share" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    if list(fonts_dir.glob("Hack*Nerd*.ttf")) or list(fonts_dir.glob("HackNerd*.ttf")):
        print("  Hack Nerd Font already installed, skipping.")
        return

    zip_path = REPO / "Hack.zip"
    if not zip_path.exists():
        run([
            "wget", "-O", str(zip_path),
            "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/Hack.zip",
        ])

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
    mostrar_progeso("\n[+] Installing Starship...\n")
    # Official installer; --yes makes it non-interactive.
    run("curl -sS https://starship.rs/install.sh | sh -s -- --yes", shell=True)

    user_cfg = HOME / ".config" / "starship.toml"
    backup_path(user_cfg)
    (HOME / ".config").mkdir(parents=True, exist_ok=True)
    shutil.copy(theme_file("starship.toml"), user_cfg)

    run(["sudo", "mkdir", "-p", "/root/.config"])
    run([
        "sudo", "cp",
        str(theme_file("starship.toml")),
        "/root/.config/starship.toml",
    ])


def fzf():
    mostrar_progeso("\n[+] Configuring FZF...\n")
    # fzf binary already installed in apt_prereqs(); clone upstream repo for
    # the install script (keybindings + completion) and run it non-interactively.
    for target_str, sudo in ((str(HOME / ".fzf"), False), ("/root/.fzf", True)):
        target = Path(target_str)
        prefix = ["sudo"] if sudo else []
        # Use `test -e` (via sudo for root paths) instead of Path.exists():
        # Python 3.12+ raises PermissionError on stat() of unreadable paths
        # like /root/* when running as a non-root user.
        exists = subprocess.run(
            prefix + ["test", "-e", str(target)], check=False
        ).returncode == 0
        if exists:
            run(prefix + ["git", "-C", str(target), "pull", "--ff-only"], check=False)
        else:
            run(prefix + [
                "git", "clone", "--depth=1",
                "https://github.com/junegunn/fzf.git", str(target),
            ])
        run(prefix + [
            str(target / "install"),
            "--key-bindings", "--completion",
            "--no-update-rc", "--no-bash", "--no-fish",
        ])


def nvim():
    mostrar_progeso("\n[+] Installing Neovim (NvChad)...\n")
    # Clean prior installs so reruns are idempotent.
    for p in [HOME / ".config" / "nvim",
              HOME / ".local" / "share" / "nvim",
              HOME / ".cache" / "nvim"]:
        if p.exists():
            shutil.rmtree(p)
    for p in ["/root/.config/nvim", "/root/.local/share/nvim", "/root/.cache/nvim"]:
        run(["sudo", "rm", "-rf", p])

    # Pin to current stable (April 2026). Bump deliberately — random
    # rebuilds shouldn't slide in via "latest".
    NVIM_VERSION = "v0.12.2"
    appimage = REPO / f"nvim-{NVIM_VERSION}-linux-x86_64.appimage"
    # Clean stale downloads from previous versions so disk doesn't grow.
    for stale in REPO.glob("nvim-*.appimage"):
        if stale != appimage:
            stale.unlink()
    if (REPO / "nvim-linux-x86_64.appimage").exists():
        (REPO / "nvim-linux-x86_64.appimage").unlink()
    if not appimage.exists():
        run([
            "curl", "-L", "-o", str(appimage),
            f"https://github.com/neovim/neovim/releases/download/{NVIM_VERSION}/nvim-linux-x86_64.appimage",
        ])
    run(["chmod", "u+x", str(appimage)])

    sq = REPO / "squashfs-root"
    if sq.exists():
        shutil.rmtree(sq)
    run([str(appimage), "--appimage-extract"], cwd=str(REPO))

    # Install to /opt/nvim and symlink AppRun -> /usr/local/bin/nvim.
    # Old installer left a directory at /usr/bin/nvim — clean that up too.
    run(["sudo", "rm", "-rf", "/opt/nvim", "/usr/local/bin/nvim", "/usr/bin/nvim"])
    run(["sudo", "mv", str(sq), "/opt/nvim"])
    run(["sudo", "ln", "-sf", "/opt/nvim/AppRun", "/usr/local/bin/nvim"])

    # NvChad starter config (for user and root)
    run(["git", "clone", "https://github.com/NvChad/starter", str(HOME / ".config" / "nvim")])
    run([
        "sudo", "bash", "-c",
        "git clone https://github.com/NvChad/starter /root/.config/nvim",
    ])
    set_nvchad_theme(THEMES[CHOICE["theme"]]["nvchad"])


def theme_extras():
    mostrar_progeso(f"\n[+] Applying the {THEMES[CHOICE['theme']]['name']} theme extras...\n")
    set_bat_theme(THEMES[CHOICE["theme"]]["bat"])
    save_state(CHOICE["theme"])


def desktop():
    mostrar_progeso("\n[+] Applying the Moonfly desktop theme (Cinnamon)...\n")
    run(["bash", str(DESKTOP_DIR / "apply-desktop.sh")])


def cambiar_terminal():
    mostrar_progeso("\n[+] Setting kitty as the system default terminal...\n")

    kitty_bin = HOME / ".local" / "kitty.app" / "bin" / "kitty"

    # Cinnamon: panel keybind (Ctrl+Alt+T), nemo "Open Terminal Here", and
    # Mint's "Preferred Applications" GUI all read these two keys. The
    # exec-arg='--' matches X-TerminalArgExec in the kitty .desktop file —
    # kitty uses '--' as the separator before the command to run, not '-e'.
    run(["gsettings", "set",
         "org.cinnamon.desktop.default-applications.terminal",
         "exec", "kitty"])
    run(["gsettings", "set",
         "org.cinnamon.desktop.default-applications.terminal",
         "exec-arg", "--"])

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


def aviso_final():
    yellow()
    print("\n[!] IMPORTANTE: cierra sesión y vuelve a entrar para que zsh sea tu shell por defecto.")
    print("    Para probarlo inmediatamente en esta terminal: `exec zsh`")
    print("\n[!] Si aceptaste cambiar la terminal por defecto:")
    print("    -> Cinnamon usará kitty para Ctrl+Alt+T, el panel y nemo 'Abrir terminal aquí'.")
    print("    -> Cierra sesión para que todos los procesos hereden la nueva configuración.")
    print("\n[!] Opcional (solo Cinnamon): si quieres Super+flechas para moverte entre splits")
    print("    y Super+Shift+flechas para reordenarlos, ejecuta:")
    print("        python3 tools/keybindings/apply_super_arrows.py")
    print(f"\n[!] Tema instalado: {THEMES[CHOICE['theme']]['name']}. Para cambiarlo más tarde sin reinstalar:")
    print("        python3 main.py --switch-theme classic     (o moonfly)")
    if CHOICE["desktop"]:
        print("\n[!] Escritorio Moonfly aplicado. Tamaño/estilo de los contadores de la barra:")
        print("        bash tools/desktop/set-badges.sh 11 black     (tamaño 8-14, black o colored)")
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


def instalar():
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


"""MENÚ Y CAMBIO DE TEMA"""
def preguntar_si_no(texto):
    while True:
        r = input(texto).strip().lower()
        if r in ("s", "si", "sí", "y", "yes"):
            return True
        if r in ("n", "no"):
            return False
        print("\nSolo puedes responder 's' o 'n'\n")


def elegir_tema():
    keys = list(THEMES)
    blue(); print("\nElige el estilo del workspace:\n")
    for i, key in enumerate(keys, 1):
        white(); print(f"  [{i}] {THEMES[key]['name']:<8} {THEMES[key]['desc']}")
    blue()
    while True:
        r = input(f"\nOpción [1-{len(keys)}] (Enter = 1): ").strip().lower()
        if r == "":
            return keys[0]
        if r.isdigit() and 1 <= int(r) <= len(keys):
            return keys[int(r) - 1]
        if r in THEMES:
            return r
        print(f"Responde un número del 1 al {len(keys)}.")


def decidir_escritorio(flag):
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
    return preguntar_si_no("\n¿Aplicar también el escritorio Moonfly (ventanas negras con verde, "
                           "panel negro, iconos Papirus)? (s/n): ")


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


def limpiar_kitty_conf(path):
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
    if not any(l.startswith("scrollback_lines") for l in out):
        out.append("scrollback_lines 10000")
    text = re.sub(r"\n{4,}", "\n\n\n", "\n".join(out) + "\n")
    path.write_text(text)


def cambiar_tema(theme, desktop_flag):
    """--switch-theme: re-theme an existing install (kitty, prompt, bat, NvChad) without reinstalling."""
    CHOICE["theme"] = theme
    kitty_dir = HOME / ".config" / "kitty"
    if not (kitty_dir / "kitty.conf").exists():
        sys.exit("ERROR: no encuentro ~/.config/kitty/kitty.conf. Ejecuta primero: python3 main.py")
    mostrar_progeso(f"\n[+] Cambiando al tema {THEMES[theme]['name']}...\n")
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

    limpiar_kitty_conf(kitty_dir / "kitty.conf")
    shutil.copy(theme_file("color.ini"), kitty_dir / "color.ini")
    shutil.copy(theme_file("starship.toml"), HOME / ".config" / "starship.toml")
    run(["sudo", "mkdir", "-p", "/root/.config"])
    run(["sudo", "cp", str(theme_file("starship.toml")), "/root/.config/starship.toml"])
    set_bat_theme(THEMES[theme]["bat"])
    set_nvchad_theme(THEMES[theme]["nvchad"], regenerate=True)
    save_state(theme)

    if theme == "moonfly":
        CHOICE["desktop"] = decidir_escritorio(desktop_flag)
        if CHOICE["desktop"]:
            desktop()
    else:
        backups = sorted(HOME.glob("theme-backup-desktop-*/restore.sh"))
        if backups and desktop_flag is not False and is_cinnamon():
            blue()
            if desktop_flag or preguntar_si_no("\n¿Restaurar también el escritorio original de Mint? (s/n): "):
                run(["bash", str(backups[0])])
            white()

    green()
    print(f"\n[+] Tema {THEMES[theme]['name']} aplicado.")
    print("    -> En kitty pulsa Ctrl+Shift+F5 (o abre una ventana nueva) para ver los colores.")
    print("    -> El prompt se actualiza al pulsar Enter.")
    print(f"    -> Para deshacer: copia los archivos de {backup} a su sitio.")
    white()


def parse_args():
    p = argparse.ArgumentParser(description="Auto-Kitty-Workspace installer")
    p.add_argument("--theme", choices=list(THEMES),
                   help="install this theme without showing the menu")
    p.add_argument("--desktop", action=argparse.BooleanOptionalAction, default=None,
                   help="also apply (or skip) the matching Cinnamon desktop theme (moonfly only)")
    p.add_argument("--switch-theme", choices=list(THEMES), metavar="THEME",
                   help="only change the theme of an existing install (classic or moonfly)")
    return p.parse_args()


"""PROGRAMA PRINCIPAL"""
if __name__ == '__main__':
    args = parse_args()
    purple()
    print(BANNER)

    if args.switch_theme:
        cambiar_tema(args.switch_theme, args.desktop)
        sys.exit(0)

    CHOICE["theme"] = args.theme or elegir_tema()
    if CHOICE["theme"] == "moonfly":
        CHOICE["desktop"] = decidir_escritorio(args.desktop)
    elif args.desktop:
        yellow(); print("\n[i] --desktop solo aplica al tema moonfly; se ignora."); white()

    instalar()

    blue()
    while True:
        cambiar = input("\n¿Deseas cambiar la terminal por defecto? (s/n): ").lower()
        if cambiar not in ["s", "n"]:
            print("\nSolo puedes responder 's' o 'n'\n")
            continue
        if cambiar == "s":
            cambiar_terminal()
        break

    aviso_final()
    green()
    print("\n[+] La instalación y la configuración de la terminal se ha realizado correctamente.")
    print("    Abre Kitty desde el menú de aplicaciones para comprobarlo.")
    print("Disfruta <3")
    white()

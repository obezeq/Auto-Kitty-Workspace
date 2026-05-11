import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from sys import stdout


REPO = Path(__file__).resolve().parent
HOME = Path.home()


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
    shutil.copy(REPO / "tools" / "kitty" / "color.ini", cfg_dir / "color.ini")


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
    shutil.copy(REPO / "tools" / "starship" / "starship.toml", user_cfg)

    run(["sudo", "mkdir", "-p", "/root/.config"])
    run([
        "sudo", "cp",
        str(REPO / "tools" / "starship" / "starship.toml"),
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


def cambiar_terminal():
    yellow()
    print("\n[!] Kitty se ha instalado como aplicacion de usuario (~/.local/kitty.app/)")
    print("[!] Para establecerla como terminal por defecto:")
    print("    -> Configuracion del sistema > Aplicaciones preferidas > Terminal")
    white()


def aviso_final():
    yellow()
    print("\n[!] IMPORTANTE: cierra sesión y vuelve a entrar para que zsh sea tu shell por defecto.")
    print("    Para probarlo inmediatamente en esta terminal: `exec zsh`")
    print("\n[!] Opcional (solo Cinnamon): si quieres Super+flechas para moverte entre splits")
    print("    y Super+Shift+flechas para reordenarlos, ejecuta:")
    print("        python3 tools/keybindings/apply_super_arrows.py")
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
]


def instalar():
    completed = []
    for name, fn in PHASES:
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


"""PROGRAMA PRINCIPAL"""
if __name__ == '__main__':
    purple()
    print(BANNER)
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

import os
import time
from sys import stdout


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
    RED = "\033[1;31m"
    stdout.write(RED)


def green():  # Verde
    GREEN = "\033[0;32m"
    stdout.write(GREEN)


def blue():  # Azul
    BLUE = "\033[1;34m"
    stdout.write(BLUE)


def yellow():  # Amarillo
    YELLOW = "\033[1;33m"
    stdout.write(YELLOW)


def orange():  # Naranja
    ORANGE = "\033[1;38;5;208m"
    stdout.write(ORANGE)


def white():  # Blanco
    WHITE = "\033[1;37m"
    stdout.write(WHITE)


def purple():  # Morado
    PURPLE = "\033[1;35m"
    stdout.write(PURPLE)


def cyan():  # Cian
    CYAN = "\033[1;36m"
    stdout.write(CYAN)


def light_gray():  # Gris claro
    LIGHT_GRAY = "\033[0;37m"
    stdout.write(LIGHT_GRAY)


def dark_gray():  # Gris oscuro
    DARK_GRAY = "\033[1;30m"
    stdout.write(DARK_GRAY)


def light_blue():  # Azul claro
    LIGHT_BLUE = "\033[1;94m"
    stdout.write(LIGHT_BLUE)


"""FUNCIONES PRINCIPALES"""
def starship():
    # Instalar Starship en user y root
    os.system("curl -sS https://starship.rs/install.sh | sh")
    os.system("sudo curl -sS https://starship.rs/install.sh | sh")

    # Aplicar tema catpuccino modificado
    os.system("cp ~/Auto-Kitty-Workspace/tools/starship/starship.toml ~/.config")
    os.system("sudo cp ~/Auto-Kitty-Workspace/tools/starship/starship.toml /root/.config")


def hnf():
    # Instalar Hack Nerd Fonts
    os.system("wget https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/Hack.zip")
    os.system("unzip -o Hack.zip")
    for file in os.listdir():
        if file.startswith("Hack"):
            os.system(f"sudo mv {file} /usr/share/fonts")


def kitty():
    # Configurar Kitty
    os.system("sudo apt install kitty -y")
    os.system("rm -rf ~/.config/kitty/*")  # borra config anterior
    os.system("mkdir -p ~/.config/kitty")
    os.system("cp -r ~/Auto-Kitty-Workspace/tools/kitty/kitty.conf ~/.config/kitty")
    os.system("cp -r ~/Auto-Kitty-Workspace/tools/kitty/color.ini ~/.config/kitty")


def zsh():
    # Configurar zsh por defecto
    os.system("sudo apt install zsh -y")
    os.system("sudo usermod --shell /usr/bin/zsh $USER")
    os.system("sudo usermod --shell /usr/bin/zsh root")

    # Aplicar config de .zshrc
    os.system("cp -r ~/Auto-Kitty-Workspace/tools/zsh/.zshrc ~/")
    os.system("sudo cp -r ~/Auto-Kitty-Workspace/tools/zsh/.zshrc /root")

    # Instalar plugins
    os.system("sudo wget https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/plugins/sudo/sudo.plugin.zsh")
    os.system("sudo apt install zsh-autosuggestions zsh-syntax-highlighting git -y")
    os.system("sudo dpkg -i ~/Auto-Kitty-Workspace/tools/zsh/plugins/*")
    os.system("sudo mkdir -p /usr/share/zsh-sudo")
    os.system("sudo mv sudo.plugin.zsh /usr/share/zsh-sudo")


def fzf():
    # Instalar FZF en el usuario y root
    os.system("sudo apt install fzf -y")
    os.system("git clone --depth=1 https://github.com/junegunn/fzf.git ~/.fzf")
    os.system("sudo git clone --depth=1 https://github.com/junegunn/fzf.git /root/.fzf")
    os.system("sudo ~/.fzf/install")
    os.system("sudo /root/.fzf/install")


def nvim():
    # Borrar antigua configuración de Nvim (mejor prevenir que curar)
    os.system("sudo rm -rf ~/.config/nvim")
    os.system("sudo rm -rf ~/.local/share/nvim")
    os.system("sudo rm -rf ~/.cache/nvim")
    os.system("sudo rm -rf /root/.config/nvim")
    os.system("sudo rm -rf /root/.local/share/nvim")
    os.system("sudo rm -rf /root/.config/nvim")

    # Instalar Nvim
    os.system("sudo apt install curl")
    os.system("curl -LO https://github.com/neovim/neovim/releases/download/v0.11.3/nvim-linux-x86_64.appimage")
    os.system("chmod u+x nvim-linux-x86_64.appimage")
    os.system("./nvim-linux-x86_64.appimage --appimage-extract")
    os.system("sudo mv squashfs-root nvim ")
    os.system("sudo mv nvim /usr/bin")

    # Configurar Nvim en usuario y root
    os.system("git clone https://github.com/NvChad/starter ~/.config/nvim")
    os.system("sudo git clone https://github.com/NvChad/starter /root/.config/nvim")


def cambiar_terminal():
    # Cambiar terminal
    os.system("sudo update-alternatives --config x-terminal-emulator")

def mostrar_progeso(texto):
    orange()
    print(texto)
    white()  

def instalar():
    # Instalar Kitty
    mostrar_progeso("\n[+] Instalando la Kitty....\n")
    kitty()

    # Instalar zsh
    mostrar_progeso("\n[+] Instalando ZSH....\n")
    time.sleep(3)
    zsh()

    # Instalar Hack Nerd Fonts
    mostrar_progeso("\n[+] Instalando las Hack Nerd Fonts....\n")
    time.sleep(3)
    hnf()

    # Aplicar config de starship
    mostrar_progeso("\n[+] Instalando Starship....\n")
    time.sleep(3)
    starship()

    # Instalar FZF
    mostrar_progeso("\n[+] Instalando FZF....\n")
    time.sleep(3)
    fzf()

    # Instalar Nvim
    mostrar_progeso("\n[+] Instalando Nvim....\n")
    time.sleep(3)
    nvim()


"""PROGRAMA PRINCIPAL"""
if __name__ == '__main__':
    # Imprimir banner del programa y instalar programa
    purple()
    print(BANNER)
    instalar()

 # Cambiar terminal por defecto
    time.sleep(2)
    blue()
    while True:
        cambiar = input("\n¿Deseas cambiar la terminal por defecto? (s/n): ").lower()
        if cambiar not in ["s", "n"]:
            print("\nSolo puedes responder 's' o 'n'\n")
            continue
        if cambiar == "s":
            cambiar_terminal()
        break

    # Mensaje final
    green()
    print("\n[+] La instalación y la configuración de la terminal se ha realizado correctamente. Abra la terminal Kitty para comprobarlo")
    print("Disfruta <3")

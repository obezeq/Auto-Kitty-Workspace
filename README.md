# Auto-Kitty-Workspace
It automates the installation and configuration of a workspace environment in the popular Kitty terminal, using the Catppuccin theme. Includes:
- **ZSH** with a pastel **Starship** theme.
- **FZF** for an improved terminal UI.
- **Neovim** with **NvChad**.
- **Personal shortcuts** for an easier life.

It is compatible with any Debian-based distribution. Tested on Linux Mint 22.1 (Xia) and Ubuntu 24.04 (Noble Numbat).

# Overview
![overview](https://raw.githubusercontent.com/Juanfu224/Auto-Linux-Workspace/master/tools/images/Vista.png)

# Installation
You must have Git installed!!
```
git clone https://github.com/Juanfu224/Auto-Kitty-Workspace.git ~/Auto-Kitty-Workspace
cd ~/Auto-Kitty-Workspace
python3 main.py
```

# Script Features
The script consists of several distinct functions:
- **Install and configure Kitty**: Terminal emulator for advanced users.

- **Install and configure Starship in ZSH**: ZSH theme that provides a fast and highly customizable prompt.

- **Configure Neovim with NvChad**: Neovim configuration for developers, providing a modern and modular text editing experience.

- **Install FZF**: General-purpose command-line fuzzy finder, useful for searching files, commands, and more.

- **Provide plugins**: Includes Zsh-autosuggestions, Zsh-syntax-highlighting, bat, lsd, among others.

# Important
- It is recommended to restart your system after completing the installation.

## Reinstall Neovim:
If you have an older version of Neovim already installed, it is highly recommended to uninstall it and remove any residual files left on the system with the following commands:
```
sudo rm -rf ~/.config/nvim
sudo rm -rf ~/.local/share/nvim
sudo rm -rf ~/.cache/nvim
sudo rm -rf /root/.config/nvim
sudo rm -rf /root/.local/share/nvim
sudo rm -rf /root/.config/nvim
```
Sometimes, errors may occur during the installation of Nvim, so you may need to rerun the script. This script already automatically removes all previous Nvim configurations.

# Descriptions:
- **Kitty**: Terminal emulator for advanced users.

- **Starship**: Minimal, fast, and highly customizable shell prompt written in Rust, designed to work with any shell.

- **zsh**: Powerful and developer-friendly shell, known for its robust configuration capabilities and plugins.

- **FZF**: General-purpose command-line fuzzy finder, useful for searching files, commands, and more.

- **NvChad**: Neovim configuration for developers, providing a modern and modular text editing experience.

- **Zsh-autosuggestions**: Zsh plugin that suggests commands as you type based on your history.

- **Zsh-syntax-highlighting**: Zsh plugin that highlights the syntax of the current command.

- **bat**: `cat` clone with syntax highlighting and integrated pagination, useful for viewing files in the terminal.

- **lsd**: Enhanced and modern `ls` offering colors, icons, and a better visual experience when listing files and directories in the terminal.

- **Neovim**: Modernized text editor based on Vim, focused on extensibility and usability.

# Shortcuts
<kbd>Ctrl</kbd> + <kbd>R</kbd> : View command history and search within it.

<kbd>Ctrl</kbd> + <kbd>←</kbd> : Switch to the neighboring window on the left.

<kbd>Ctrl</kbd> + <kbd>→</kbd> : Switch to the neighboring window on the right.

<kbd>Ctrl</kbd> + <kbd>↑</kbd> : Switch to the neighboring window above.

<kbd>Ctrl</kbd> + <kbd>↓</kbd> : Switch to the neighboring window below.

<kbd>F1</kbd> : Copy to buffer a.

<kbd>F2</kbd> : Paste from buffer a.

<kbd>F3</kbd> : Copy to buffer b.

<kbd>F4</kbd> : Paste from buffer b.

<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Z</kbd> : Switch to stacked window layout.

<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Enter</kbd> : Open a new window with the current directory.

<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>T</kbd> : Open a new tab with the current directory.

# Credits
- Script Author: Juanfu224 --> https://github.com/Juanfu224
- Powerlevel10k Author: romkatv --> https://github.com/romkatv
- bat Author: sharkdp --> https://github.com/sharkdp
- lsd Author: Peltoche --> https://github.com/Peltoche
- Hack Nerd Font Author: ryanoasis --> https://github.com/ryanoasis
- FZF Author: junegunn --> https://github.com/junegunn
- Neovim Author: Neovim --> https://github.com/neovim
- Kitty Author: kovidgoyal --> https://github.com/kovidgoyal
- Inspired by S4vitar and Yorkox0 ❤️

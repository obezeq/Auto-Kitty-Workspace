<h3 align="center">
	<img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/logos/exports/1544x1544_circle.png" width="100" alt="Logo"/><br/>
	<img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/misc/transparent.png" height="30" width="0px"/>
	Catppuccin for <a href="https://github.com/kovidgoyal/kitty">Kitty</a> & <a href="https://starship.rs">Starship</a>
	<img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/misc/transparent.png" height="30" width="0px"/>
</h3>

![overview](https://raw.githubusercontent.com/Juanfu224/Auto-Linux-Workspace/master/tools/images/Logo.png)

# Auto-Kitty-Workspace
<p>
	Automates the installation and configuration of a fully themed workspace environment in the <b>Kitty</b> terminal using the <b>Catppuccin</b> theme.<br/>
</p>


## Features

- 🐚 **ZSH** with a pastel **Starship** prompt.  
- 🔍 **FZF** for an improved terminal search experience.  
- 📝 **Neovim** with the **NvChad** configuration.  
- ⚡ **Custom shortcuts** for a faster workflow.  

> ✅ Compatible with any Debian-based distribution.  
> 🧪 Tested on **Linux Mint 22.1 (Xia)** and **Ubuntu 24.04 (Noble Numbat)**.



## Installation

> **Requirements:** Git and Python 3 must be installed.

```bash
git clone https://github.com/Juanfu224/Auto-Kitty-Workspace.git ~/Auto-Kitty-Workspace
cd ~/Auto-Kitty-Workspace
python3 main.py
````



## Script Overview

The installation script performs the following tasks:

* **🐈 Kitty installation & configuration** — Sets up the terminal with Catppuccin theme and keyboard shortcuts.
* **🌈 Starship + ZSH setup** — Installs a fast, customizable shell prompt with helpful plugins.
* **🧠 Neovim (NvChad)** — Sets up a modern, modular development environment.
* **🔎 FZF** — Adds fuzzy finding for commands, files, and history.
* **🔌 Plugins & utilities** — Installs `zsh-autosuggestions`, `zsh-syntax-highlighting`, `bat`, `lsd`, and more.



## Important Notes

* 🔁 It is **recommended to restart your system** after installation to apply all changes.
* 🧹 The script automatically removes old Neovim configurations before installing NvChad.

### 🧼 Reinstalling Neovim (Clean Setup)

If you have an older Neovim version, remove any previous configurations before running the script:

```bash
sudo rm -rf ~/.config/nvim
sudo rm -rf ~/.local/share/nvim
sudo rm -rf ~/.cache/nvim
sudo rm -rf /root/.config/nvim
sudo rm -rf /root/.local/share/nvim
sudo rm -rf /root/.cache/nvim
```

If an error occurs during installation, rerun the script — it will automatically clean up any leftover files.



## Descriptions

| Component                   | Description                                                     |
| --------------------------- | --------------------------------------------------------------- |
| **Kitty**                   | Fast, GPU-accelerated terminal emulator for advanced users.     |
| **Starship**                | Minimal, fast, and customizable shell prompt written in Rust.   |
| **ZSH**                     | Developer-friendly shell with extensive plugin support.         |
| **FZF**                     | Command-line fuzzy finder for files, history, and more.         |
| **NvChad**                  | Neovim configuration framework focused on speed and modularity. |
| **Zsh-autosuggestions**     | Suggests commands from history as you type.                     |
| **Zsh-syntax-highlighting** | Highlights shell commands in real time.                         |
| **bat**                     | Enhanced `cat` with syntax highlighting and pagination.         |
| **lsd**                     | Modern `ls` replacement with icons and colors.                  |
| **Neovim**                  | Modern text editor based on Vim, built for extensibility.       |



## Custom Keyboard Shortcuts — Kitty Terminal

These shortcuts are configured in `kitty.conf` and help optimize navigation and workflow.


### 🔁 Window Navigation

| Keys                           | Action                     | Description              |
| ------------------------------ | -------------------------- | ------------------------ |
| <kbd>Ctrl</kbd> + <kbd>←</kbd> | `neighboring_window left`  | Move to the left panel.  |
| <kbd>Ctrl</kbd> + <kbd>→</kbd> | `neighboring_window right` | Move to the right panel. |
| <kbd>Ctrl</kbd> + <kbd>↑</kbd> | `neighboring_window up`    | Move to the panel above. |
| <kbd>Ctrl</kbd> + <kbd>↓</kbd> | `neighboring_window down`  | Move to the panel below. |


### 📋 Copy & Paste Between Buffers

| Keys          | Action                | Description                     |
| ------------- | --------------------- | ------------------------------- |
| <kbd>F1</kbd> | `copy_to_buffer a`    | Copy selection to **Buffer A**. |
| <kbd>F2</kbd> | `paste_from_buffer a` | Paste from **Buffer A**.        |
| <kbd>F3</kbd> | `copy_to_buffer b`    | Copy selection to **Buffer B**. |
| <kbd>F4</kbd> | `paste_from_buffer b` | Paste from **Buffer B**.        |



### 🪟 Window & Tab Management

| Keys                                                  | Action                | Description                                     |
| ----------------------------------------------------- | --------------------- | ----------------------------------------------- |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Z</kbd>     | `toggle_layout stack` | Switch to **stacked window mode**.              |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Enter</kbd> | `new_window_with_cwd` | Open a new **window** in the current directory. |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>T</kbd>     | `new_tab_with_cwd`    | Open a new **tab** in the current directory.    |



### 🧠 Command History

| Keys                           | Description                          |
| ------------------------------ | ------------------------------------ |
| <kbd>Ctrl</kbd> + <kbd>R</kbd> | Search and navigate command history. |



## Credits

| Component          | Author     | Link                                    |
| ------------------ | ---------- | --------------------------------------- |
| **Script**         | Juanfu224  | [GitHub](https://github.com/Juanfu224)  |
| **Powerlevel10k**  | romkatv    | [GitHub](https://github.com/romkatv)    |
| **bat**            | sharkdp    | [GitHub](https://github.com/sharkdp)    |
| **lsd**            | Peltoche   | [GitHub](https://github.com/Peltoche)   |
| **Hack Nerd Font** | ryanoasis  | [GitHub](https://github.com/ryanoasis)  |
| **FZF**            | junegunn   | [GitHub](https://github.com/junegunn)   |
| **Neovim**         | Neovim     | [GitHub](https://github.com/neovim)     |
| **Kitty**          | kovidgoyal | [GitHub](https://github.com/kovidgoyal) |

> Inspired by **S4vitar** and **Yorkox0** ❤️



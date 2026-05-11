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

- **ZSH** with a pastel **Starship** prompt.  
- **FZF** for an improved terminal search experience.  
- **Neovim** with the **NvChad** configuration.  
- **Custom shortcuts** for a faster workflow.  

> Compatible with any Debian-based distribution.  
> Tested on **Linux Mint 22.3 (Zena)** and **Ubuntu 24.04 (Noble Numbat)**.



## Installation

> **Requirements:** Git and Python 3 must be installed.

```bash
git clone https://github.com/Juanfu224/Auto-Kitty-Workspace.git ~/Auto-Kitty-Workspace
cd ~/Auto-Kitty-Workspace
python3 main.py
````



## Script Overview

The installation script performs the following tasks:

* **Kitty installation & configuration** — Sets up the terminal with Catppuccin theme and keyboard shortcuts.
* **Starship + ZSH setup** — Installs a fast, customizable shell prompt with helpful plugins.
* **Neovim (NvChad)** — Sets up a modern, modular development environment.
* **FZF** — Adds fuzzy finding for commands, files, and history.
* **Plugins & utilities** — Installs `zsh-autosuggestions`, `zsh-syntax-highlighting`, `bat`, `lsd`, and more.



## Important Notes

* **Log out and log back in** after installation so the default-shell change to zsh takes effect. To preview it in the current terminal without a re-login, run `exec zsh`.
* The installer automatically backs up any existing `~/.zshrc`, `~/.config/kitty/`, and `~/.config/starship.toml` with a `.backup.<timestamp>` suffix.
* The installer registers kitty's `xterm-kitty` terminfo system-wide (via `tic`) so tmux, ssh-to-self, and `less` work without "unknown terminal type" errors. The `.zshrc` also exports `TERMINFO_DIRS` as a fallback.
* Hack Nerd Font is downloaded and installed automatically; the installer aborts if `fc-list` doesn't see it afterward (so you don't end up with prompt glyphs rendering as boxes).
* Any phase failure now aborts the installer immediately with a clear message naming the failed step (no more silent partial installs).
* Re-running the script is safe — it backs up configs, skips already-installed fonts, and reuses existing clones.
* If `nvim` shows deprecation warnings on first launch (e.g. `vim.lsp.get_active_clients` was removed in Neovim 0.12), run `:Lazy sync` inside Neovim once — NvChad's starter tracks upstream Neovim releases but the first run after a major version bump can occasionally lag a release behind.



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


### Window Navigation & Splits

| Keys                                                                  | Action                                            | Description                                     |
| --------------------------------------------------------------------- | ------------------------------------------------- | ----------------------------------------------- |
| <kbd>Super</kbd> + <kbd>H</kbd>/<kbd>J</kbd>/<kbd>K</kbd>/<kbd>L</kbd> | `neighboring_window left/down/up/right`           | Move focus between splits (Vim-style).          |
| <kbd>Super</kbd> + <kbd>←</kbd>/<kbd>↓</kbd>/<kbd>↑</kbd>/<kbd>→</kbd> | `neighboring_window …`                            | Move focus between splits (arrow alias).        |
| <kbd>F5</kbd>                                                         | `launch --location=hsplit`                        | Create a horizontal split in the current dir.   |
| <kbd>F6</kbd>                                                         | `launch --location=vsplit`                        | Create a vertical split in the current dir.     |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>←</kbd>/<kbd>→</kbd>/<kbd>↑</kbd>/<kbd>↓</kbd> | `resize_window narrower/wider/taller/shorter 3` | Resize the active split by 3 cells.        |
| <kbd>F7</kbd>                                                         | `start_resizing_window`                           | Enter interactive resize mode (Esc to exit).    |

> <kbd>Super</kbd> + <kbd>Shift</kbd> + arrows to **move** (swap) the active split with its neighbour is **opt-in** — run `python3 tools/keybindings/apply_super_arrows.py` once after the installer to free up Cinnamon's tiling shortcuts and append the matching kitty bindings. See the "Optional: Super+arrow split keybindings" section below.


### Copy & Paste Between Buffers

| Keys          | Action                | Description                     |
| ------------- | --------------------- | ------------------------------- |
| <kbd>F1</kbd> | `copy_to_buffer a`    | Copy selection to **Buffer A**. |
| <kbd>F2</kbd> | `paste_from_buffer a` | Paste from **Buffer A**.        |
| <kbd>F3</kbd> | `copy_to_buffer b`    | Copy selection to **Buffer B**. |
| <kbd>F4</kbd> | `paste_from_buffer b` | Paste from **Buffer B**.        |



### Window & Tab Management

| Keys                                                  | Action                | Description                                     |
| ----------------------------------------------------- | --------------------- | ----------------------------------------------- |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Z</kbd>     | `toggle_layout stack` | Switch to **stacked window mode**.              |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Enter</kbd> | `new_window_with_cwd` | Open a new **window** in the current directory. |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>T</kbd>     | `new_tab_with_cwd`    | Open a new **tab** in the current directory.    |



### Command History

| Keys                           | Description                          |
| ------------------------------ | ------------------------------------ |
| <kbd>Ctrl</kbd> + <kbd>R</kbd> | Search and navigate command history. |



## Optional: Super+arrow split keybindings (Cinnamon only)

The base installer ships a kitty config that already binds `Super+HJKL` for split navigation, which works on any desktop environment. If you also want **`Super+Arrows`** to move focus between splits and **`Super+Shift+Arrows`** to swap the active split with its neighbour, you need to free up those keys on the Cinnamon side first (by default Cinnamon binds them to window-tiling and move-to-monitor).

After running `python3 main.py`, run:

```bash
python3 tools/keybindings/apply_super_arrows.py
```

That script:

1. Clears the eight Cinnamon `push-tile-*` / `move-to-monitor-*` shortcuts via `gsettings` so kitty can receive the keys.
2. Appends the `super+shift+arrow → move_window` mappings to your installed `~/.config/kitty/kitty.conf` (idempotently — re-running won't duplicate the block).

It refuses to run on non-Cinnamon desktops (GNOME/KDE/XFCE), where you'd clear the equivalent shortcuts manually instead. Reopen kitty (or run `kitty @ load-config` inside a kitty window) afterward to pick up the new mappings.



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



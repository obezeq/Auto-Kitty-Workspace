# Fix the Java Problem
export _JAVA_AWT_WM_NONREPARENTING=1

# Make kitty's bundled terminfo discoverable for tmux/less/ssh-to-self.
# Fallback for systems where the installer hasn't (or couldn't) register
# xterm-kitty system-wide via `tic`.
if [[ -d "$HOME/.local/kitty.app/share/terminfo" ]]; then
  export TERMINFO_DIRS="$HOME/.local/kitty.app/share/terminfo:${TERMINFO_DIRS:-/usr/share/terminfo}"
fi


# Set up the prompt
autoload -Uz promptinit
promptinit
setopt histignorealldups sharehistory

# Use emacs keybindings even if our EDITOR is set to vi
bindkey -e

# Keep 1000 lines of history within the shell and save it to ~/.zsh_history:
HISTSIZE=1000
SAVEHIST=1000
HISTFILE=~/.zsh_history

# Use modern completion system
autoload -Uz compinit
compinit

zstyle ':completion:*' auto-description 'specify: %d'
zstyle ':completion:*' completer _expand _complete _correct _approximate
zstyle ':completion:*' format 'Completing %d'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' menu select=2
eval "$(dircolors -b)"
zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' list-prompt %SAt %p: Hit TAB for more, or the character to insert%s
zstyle ':completion:*' matcher-list '' 'm:{a-z}={A-Z}' 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=* l:|=*'
zstyle ':completion:*' menu select=long
zstyle ':completion:*' select-prompt %SScrolling active: current selection at %p%s
zstyle ':completion:*' use-compctl false
zstyle ':completion:*' verbose true

zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#)*=0=01;31'
zstyle ':completion:*:kill:*' command 'ps -u $USER -o pid,%cpu,tty,cputime,cmd'


# Manual configuration

# Prepend user-local bins; preserve the inherited PATH from the desktop
# session (/etc/environment, /etc/profile, ~/.profile: snap, /usr/local/sbin,
# etc.). typeset -U dedupes automatically so sourcing twice doesn't grow PATH.
# These are added even if they don't exist yet, so tools installed there
# later (pipx, uv, cargo...) work without touching this file.
typeset -U path PATH
path=(
  "$HOME/.local/bin"
  "$HOME/bin"
  "$HOME/.cargo/bin"
  "$HOME/.local/kitty.app/bin"
  $path
)
# Go's official install only documents ~/.profile; add it here too (only
# if installed — (N-/) drops the entry when the directory doesn't exist).
path+=( /usr/local/go/bin(N-/) "$HOME"/go/bin(N-/) )
export PATH

# nvm is usually set up in ~/.bashrc, which zsh never reads. Load it here so
# node/npm keep working after switching to zsh. (nvm's own installer sees
# "nvm.sh" in this file and won't add it twice.)
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

# Manual aliases — only when the tool exists, so a missing package never
# breaks basic commands like ls or cat.
if (( $+commands[lsd] )); then
  alias ll='lsd -lh --group-dirs=first'
  alias la='lsd -a --group-dirs=first'
  alias l='lsd --group-dirs=first'
  alias lla='lsd -lha --group-dirs=first'
  alias ls='lsd --group-dirs=first'
fi
# Debian/Ubuntu's own bat package names the binary `batcat`.
if (( $+commands[bat] )); then
  alias cat='bat'
elif (( $+commands[batcat] )); then
  alias cat='batcat'
fi
alias clear-histfile='rm $HISTFILE'
alias c='clear'
alias copy='kitten clipboard'
alias update='sudo apt update && sudo apt full-upgrade -y && { ! (( $+commands[flatpak] )) || sudo flatpak update -y; }'
alias autoremove='sudo apt autoclean && sudo apt autoremove'

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Plugins — guard each source so a missing package doesn't kill the shell.
# zsh-syntax-highlighting goes last, as its docs require.
[ -f /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ] \
  && source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
[ -f /usr/share/zsh-sudo/sudo.plugin.zsh ] \
  && source /usr/share/zsh-sudo/sudo.plugin.zsh
[ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ] \
  && source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# Functions

# Set 'man' colors
function man() {
    env \
    LESS_TERMCAP_mb=$'\e[01;31m' \
    LESS_TERMCAP_md=$'\e[01;31m' \
    LESS_TERMCAP_me=$'\e[0m' \
    LESS_TERMCAP_se=$'\e[0m' \
    LESS_TERMCAP_so=$'\e[01;44;33m' \
    LESS_TERMCAP_ue=$'\e[0m' \
    LESS_TERMCAP_us=$'\e[01;32m' \
    man "$@"
}


# Keyboard
bindkey "^[[H" beginning-of-line
bindkey "^[[F" end-of-line
bindkey "^[[3~" delete-char
bindkey "^[[1;3C" forward-word
bindkey "^[[1;3D" backward-word
bindkey -s "^[Ok" "+"
bindkey -s "^[Om" "-"
bindkey -s "^[OM" "^M"
bindkey -s "^[Oj" "*"
bindkey -s "^[Oo" "/"

# Change cursor shape for different vi modes.
function zle-keymap-select {
  if [[ $KEYMAP == vicmd ]] || [[ $1 = 'block' ]]; then
    echo -ne '\e[1 q'
  elif [[ $KEYMAP == main ]] || [[ $KEYMAP == viins ]] || [[ $KEYMAP = '' ]] || [[ $1 = 'beam' ]]; then
    echo -ne '\e[5 q'
  fi
}
zle -N zle-keymap-select
 
# Start with beam shape cursor on zsh startup and after every command.
zle-line-init() { zle-keymap-select 'beam'}

# Your own additions (PATH, exports, aliases...) go in ~/.zshrc.local:
# reinstalling or switching theme never overwrites that file.
[ -f ~/.zshrc.local ] && source ~/.zshrc.local

# Guard so zsh starts cleanly even if starship isn't on PATH yet
# (e.g. first zsh session before logout/relogin picks up the new PATH).
command -v starship >/dev/null && eval "$(starship init zsh)"
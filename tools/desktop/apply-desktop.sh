#!/usr/bin/env bash
# Moonfly-style desktop for Linux Mint Cinnamon
#   - Colloid theme, pure black, with Moonfly's exact green (#8cc85f) as the only accent
#   - Plain gray window buttons (no colored macOS dots)
#   - Solid black panel (same black as the Moonfly terminal)
#   - Taskbar badges in Moonfly green/red (change them anytime with set-badges.sh)
#   - Papirus-Dark icons with gray folders (no white tiles behind app icons)
# Saves your original look the first time; run the printed restore command to undo.
# Safe to run again: it keeps that first backup, so undo always returns to your original look.
set -e

GREEN="#8cc85f"
THEME="Colloid-Green-Dark"
ICONS="Papirus-Dark"
PANEL_BG="#080808"
BACKUP="$HOME/theme-backup-desktop-$(date +%Y%m%d-%H%M%S)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ "$(id -u)" -eq 0 ]; then
  echo "Run this as your normal user (not with sudo). It will ask for your password when needed."; exit 1
fi

EXISTING="$(ls -d "$HOME"/theme-backup-desktop-* 2>/dev/null | head -1)"
if [ -n "$EXISTING" ] && [ -f "$EXISTING/restore.sh" ]; then
  BACKUP="$EXISTING"
  echo "[1/5] Keeping your original backup at $BACKUP"
else
  echo "[1/5] Saving your current look to $BACKUP"
  mkdir -p "$BACKUP"
  [ -d "$HOME/.config/gtk-4.0" ] && cp -r "$HOME/.config/gtk-4.0" "$BACKUP/gtk-4.0"
  {
    echo "#!/usr/bin/env bash"
    echo "# Restores the desktop look you had before apply-desktop.sh"
    for key in "org.cinnamon.desktop.interface gtk-theme" \
               "org.cinnamon.desktop.wm.preferences theme" \
               "org.cinnamon.theme name" \
               "org.cinnamon.desktop.interface icon-theme"; do
      echo "gsettings set $key $(gsettings get $key)"
    done
    echo "rm -rf \"\$HOME/.config/gtk-4.0\""
    echo "[ -d \"$BACKUP/gtk-4.0\" ] && cp -r \"$BACKUP/gtk-4.0\" \"\$HOME/.config/gtk-4.0\""
    echo "echo 'Previous look restored.'"
  } > "$BACKUP/restore.sh"
  chmod +x "$BACKUP/restore.sh"
fi

echo "[2/5] Installing build tools (may ask for your password)"
sudo apt-get install -y git curl sassc gtk2-engines-murrine gnome-themes-extra papirus-icon-theme >/dev/null

echo "[3/5] Building the theme with Moonfly green ($GREEN)"
git clone -q --depth 1 https://github.com/vinceliuice/Colloid-gtk-theme.git "$WORK/theme"
sed -i "s/^\$green-light: .*/\$green-light: $GREEN;/; s/^\$green-dark: .*/\$green-dark: $GREEN;/" \
  "$WORK/theme/src/sass/_color-palette-default.scss"
grep -q "^\$green-light: $GREEN;" "$WORK/theme/src/sass/_color-palette-default.scss" \
  || { echo "Could not set the green color (theme source changed?). Nothing was applied."; exit 1; }
# -t green: accent | -c dark | black: pure black | normal: plain gray window buttons | -l: GTK4 apps too
(cd "$WORK/theme" && ./install.sh -t green -c dark --tweaks black normal -l >/dev/null)
# Solid panel instead of 75% see-through black
CSS="$HOME/.themes/$THEME/cinnamon/cinnamon.css"
sed -i '/^\.panel-top, \.panel-bottom, \.panel-left, \.panel-right {/,/}/ s/background-color: rgba(0, 0, 0, 0\.[0-9]*);/background-color: '"$PANEL_BG"';/' "$CSS"
grep -q "background-color: $PANEL_BG;" "$CSS" || echo "   (note: couldn't make the panel solid; it stays slightly see-through)"
# Taskbar badges (window count + notifications). Uses your saved choice from set-badges.sh if any.
BADGE_SIZE=11; BADGE_STYLE=black
CONF="$HOME/.config/moonfly-desktop/badges.conf"
if [ -f "$CONF" ]; then
  v=$(grep -E '^BADGE_SIZE=(8|9|10|11|12|13|14)$' "$CONF" | cut -d= -f2); [ -n "$v" ] && BADGE_SIZE=$v
  v=$(grep -E '^BADGE_STYLE=(black|colored)$' "$CONF" | cut -d= -f2); [ -n "$v" ] && BADGE_STYLE=$v
fi
if [ "$BADGE_STYLE" = colored ]; then CB="#8cc85f"; CT="#080808"; NB="#ff5d5d"; NT="#080808"
else CB="#080808"; CT="#8cc85f"; NB="#080808"; NT="#ff5d5d"; fi
cat >> "$CSS" << BADGES_EOF
/* Moonfly taskbar badges */
.grouped-window-list-badge { background-color: $CB; border-radius: 99px; }
.grouped-window-list-number-label { color: $CT; font-size: ${BADGE_SIZE}px; font-weight: bold; padding: 0 2px; }
.grouped-window-list-notifications-badge { background-color: $NB; color: $NT; border-radius: 99px; }
.grouped-window-list-notifications-badge-label { color: $NT; font-size: ${BADGE_SIZE}px; font-weight: bold; padding: 0 2px; }
/* end Moonfly taskbar badges */
BADGES_EOF

echo "[4/5] Setting up Papirus-Dark icons with gray folders"
curl -fsSL https://raw.githubusercontent.com/PapirusDevelopmentTeam/papirus-folders/master/papirus-folders -o "$WORK/papirus-folders"
sudo bash "$WORK/papirus-folders" -C grey --theme Papirus-Dark >/dev/null
sudo bash "$WORK/papirus-folders" -C grey --theme Papirus >/dev/null   # small sizes live here
rm -rf "$HOME/.local/share/icons/Colloid-Grey" "$HOME/.local/share/icons/Colloid-Grey-Dark" "$HOME/.local/share/icons/Colloid-Grey-Light"

echo "[5/5] Applying everything"
gsettings set org.cinnamon.desktop.interface gtk-theme "$THEME"
gsettings set org.cinnamon.desktop.wm.preferences theme "$THEME"
# switch away and back so Cinnamon reloads the panel style if the theme was already active
gsettings set org.cinnamon.theme name ""
sleep 1
gsettings set org.cinnamon.theme name "$THEME"
gsettings set org.cinnamon.desktop.interface icon-theme "$ICONS"
# Tell GTK4 / Flatpak apps to prefer dark mode (ignored if not supported)
gsettings set org.x.apps.portal color-scheme 'prefer-dark' 2>/dev/null || true
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true

echo
echo "Done! Your desktop now matches the terminal."
echo "Apps that were already open may need a restart to fully update."
echo "To undo:  bash $BACKUP/restore.sh"

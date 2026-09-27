#!/usr/bin/env bash
# Try taskbar badge looks live on your panel (window count + notifications).
#   bash set-badges.sh <size> <style>
#   size:  8 to 14 (text size in px; the circle grows with it)
#   style: black    -> black circle, green / red numbers
#          colored  -> green / red circle, black numbers
# Examples:
#   bash set-badges.sh 10 black
#   bash set-badges.sh 11 colored
# Your choice is remembered, so re-running apply-desktop.sh keeps it.
set -e

SIZE="${1:-11}"
STYLE="${2:-black}"
THEME="Colloid-Green-Dark"
CSS="$HOME/.themes/$THEME/cinnamon/cinnamon.css"

case "$SIZE" in 8|9|10|11|12|13|14) ;; *) echo "Size must be a number from 8 to 14."; exit 1 ;; esac
case "$STYLE" in black|colored) ;; *) echo "Style must be 'black' or 'colored'."; exit 1 ;; esac
[ -f "$CSS" ] || { echo "Theme not found. Run apply-desktop.sh first."; exit 1; }

if [ "$STYLE" = colored ]; then
  CB="#8cc85f"; CT="#080808"; NB="#ff5d5d"; NT="#080808"
else
  CB="#080808"; CT="#8cc85f"; NB="#080808"; NT="#ff5d5d"
fi

# Replace any previous badge block (also handles older versions without an end marker)
sed -i '/\/\* Moonfly taskbar badges \*\//,/\/\* end Moonfly taskbar badges \*\//d' "$CSS"
cat >> "$CSS" << EOF
/* Moonfly taskbar badges */
.grouped-window-list-badge { background-color: $CB; border-radius: 99px; }
.grouped-window-list-number-label { color: $CT; font-size: ${SIZE}px; font-weight: bold; padding: 0 2px; }
.grouped-window-list-notifications-badge { background-color: $NB; color: $NT; border-radius: 99px; }
.grouped-window-list-notifications-badge-label { color: $NT; font-size: ${SIZE}px; font-weight: bold; padding: 0 2px; }
/* end Moonfly taskbar badges */
EOF

mkdir -p "$HOME/.config/moonfly-desktop"
printf 'BADGE_SIZE=%s\nBADGE_STYLE=%s\n' "$SIZE" "$STYLE" > "$HOME/.config/moonfly-desktop/badges.conf"

# Make Cinnamon reload the panel style
gsettings set org.cinnamon.theme name ""
sleep 1
gsettings set org.cinnamon.theme name "$THEME"
echo "Badges set to ${SIZE}px, $STYLE."

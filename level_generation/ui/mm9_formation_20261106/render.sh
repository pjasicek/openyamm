#!/bin/bash
# Renders the study's images with headless Chrome: ./render.sh (from this folder); needs ../mm9_hirelings_20261106/images/R2_*.png
cd "$(dirname "$0")"; mkdir -p images
shot() { google-chrome --headless --no-sandbox --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --virtual-time-budget=2000 --window-size=$2 --screenshot="images/$1.png" "file://$PWD/index.html?$3" 2>/dev/null; }
shot formation_16x9 1920,1080 "aspect=16x9"
shot formation_4x3 1440,1080 "aspect=4x3"
shot formation_16x9_drag 1920,1080 "aspect=16x9&state=drag"

#!/bin/bash
# Renders the study's images with headless Chrome: ./render.sh (from this folder)
cd "$(dirname "$0")"; mkdir -p images
shot() { google-chrome --headless --no-sandbox --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --window-size=$2 --screenshot="images/$1.png" "file://$PWD/index.html?$3" 2>/dev/null; }
for v in A B C; do
  shot ${v}_16x9 1920,1080 "variant=$v&aspect=16x9&n=2"
  shot ${v}_4x3 1440,1080 "variant=$v&aspect=4x3&n=2"
done
shot A_16x9_one 1920,1080 "variant=A&aspect=16x9&n=1"
shot C_4x3_one 1440,1080 "variant=C&aspect=4x3&n=1"
# revision 1 (2026-11-06)
shot R_16x9 1920,1080 "variant=R&aspect=16x9&n=2"
shot R_4x3 1440,1080 "variant=R&aspect=4x3&n=2"
shot R_16x9_one 1920,1080 "variant=R&aspect=16x9&n=1"
# revision 2 (2026-11-06): three hirelings
shot R2_16x9 1920,1080 "variant=R2&aspect=16x9&n=3"
shot R2_4x3 1440,1080 "variant=R2&aspect=4x3&n=3"
shot R2_16x9_buttons 1920,1080 "variant=R2&aspect=16x9&n=3&buttons=1"
shot R2_4x3_two 1440,1080 "variant=R2&aspect=4x3&n=2"

#!/bin/bash
# Tier D head colour (project folder): finish_tex.py (raw -> final with the dark lining texel; head_seam.py is NOT run: this paint has
# no forehead seam and its blend joined the brows) -> mouth_fix2.py (closed-mouth master) -> eye_fix.py -> textures/pm2d_head_d_final.png
set -e
python3 scripts/finish_tex.py
python3 scripts/mouth_fix2.py textures/pm2d_head_d_final.png work/head_d_mouth.png | tail -1
python3 scripts/eye_fix.py work/head_d_mouth.png textures/pm2d_head_d_final.png 0.65 0.6

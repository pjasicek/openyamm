#!/bin/sh
# X3 L1 brief: generate, format, validate, draw (lane A5). Run from anywhere.
set -e
cd "$(dirname "$0")/../../.."
python3 level_generation/projects/xeen/x3/gen_l1.py
openyamm-studio/build-xeen/oymap fmt devdocs/xeen/briefs/x3/L1
openyamm-studio/build-xeen/oymap validate devdocs/xeen/briefs/x3/L1 --assets assets_dev
python3 level_generation/projects/xeen/x3/render.py

#!/bin/bash
# Rebuild this batch: textures, every model (Blender headless), review sheets, finish (LOD link, validation);
# --install also installs each output with tools/install_model.py --engine; run
# ../../mm8_3d/animated/scripts/check_winding.py work/mm7_deco_*.glb first (inverted closed parts: 0).
# Usage: ./build.sh [--install]   (fetch the Poly Haven sources once first: scripts/fetch_textures.py)
set -e
cd "$(dirname "$0")"
python3 scripts/make_textures.py
scripts/run.sh build_beacon.py stone_blue beacon_stone_blue outdoor 0 dec60a
scripts/run.sh build_beacon.py stone_orange beacon_stone_orange outdoor 0 dec62a
scripts/run.sh build_beacon.py stone_white beacon_stone_white outdoor 0 dec63a
scripts/run.sh build_beacon.py gold beacon_gold outdoor 0 dec61a
scripts/run.sh build_pedestal.py - pedestal outdoor 0 dec64a
scripts/run.sh build_buoy.py - buoy outdoor 0 7dec33a
scripts/run.sh build_lantern.py lantern lantern dungeon 0 torch02a
scripts/run.sh build_lantern.py lantern_free lantern_free dungeon 0 torch02a
scripts/run.sh build_burnedfire.py - burnedfire outdoor 0 7dec24x
scripts/run.sh build_burnedfire.py lit litfire outdoor 0 7dec24a
for prop in beacon_stone_blue beacon_stone_orange beacon_stone_white beacon_gold pedestal buoy lantern lantern_free \
        burnedfire litfire; do
    python3 scripts/finish.py "$prop" "$@"
done
blender --background --python scripts/review_variants.py -- pedestal_variants \
    $(for i in $(seq 64 75); do echo "work/mm7_deco_dec$i.glb"; done) > /dev/null 2>&1
python3 scripts/sheet_variants.py pedestal_variants $(for i in $(seq 64 75); do echo "dec${i}a:mm7_deco_dec$i"; done)

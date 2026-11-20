#!/bin/sh
# Rebuild the MM6 dungeon fire fixtures: textures, every model, review sheets, then
# finish (validation) and, with --install, install into assets_dev/worlds/mm6/models/.
# Usage: scripts/build.sh [--install] [prop ...]
set -e
cd "$(dirname "$0")/.."
BLENDER=${BLENDER:-/snap/bin/blender}
INSTALL=
if [ "$1" = "--install" ]; then INSTALL=--install; shift; fi
PROPS=${*:-"brazier brazier_unlit flambeaux sconce2 sconce2_free sconce1 sconce1_free cauldron candle"}
python3 scripts/make_textures.py > /dev/null
python3 scripts/make_pbr_textures.py > /dev/null
for prop in $PROPS; do
    case $prop in
        brazier*) script=build_brazier.py; sprite=$( [ "$prop" = brazier ] && echo brzier00 || echo brazir2f );;
        flambeaux) script=build_flambeaux.py; sprite=flamb00;;
        sconce2*) script=build_sconce.py; sprite=scon200;;
        sconce1*) script=build_sconce.py; sprite=scon100;;
        cauldron) script=build_cauldron.py; sprite=cauld00;;
        candle) script=build_candle.py; sprite=cndlab0;;
    esac
    "$BLENDER" --background --python "scripts/$script" -- "$prop" 2>&1 | grep -E 'LEVEL|EXPORTED|TINT|Error|Traceback'
    "$BLENDER" --background --python scripts/review.py -- "$prop" "work/${prop}_export.glb" 2>&1 \
        | grep -E 'REVIEW|Error|Traceback'
    python3 scripts/sheet.py "$prop" "$sprite"
    python3 scripts/finish.py "$prop" $INSTALL
done

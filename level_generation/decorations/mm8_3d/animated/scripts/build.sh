#!/bin/sh
# Rebuild the MM8 animated decorations: textures, every model, review renders and sheets, then finish
# (validation) and, with --install, tools/install_model.py --engine.
# Usage: scripts/build.sh [--install] [--textures] [prop ...]
set -e
cd "$(dirname "$0")/.."
BLENDER=${BLENDER:-/snap/bin/blender}
INSTALL=
if [ "$1" = "--install" ]; then INSTALL=--install; shift; fi
if [ "$1" = "--textures" ]; then python3 scripts/make_textures.py > /dev/null; shift; fi
PROPS=${*:-"orb seaweed coral lantern chandelier1 chandelier2 candlestick torch campfire buoy"}
for prop in $PROPS; do
    swing=
    case $prop in
        orb) script=build_orb.py; sprites=dec57; light=outdoor;;
        seaweed) script=build_weed.py; sprites="weed010 weed014"; light=outdoor;;
        coral) script=build_weed.py; sprites="weed020 weed024"; light=outdoor;;
        lantern) script=build_lantern.py; sprites=dec07a; light=indoor; swing=1.5;;
        chandelier1) script=build_chandelier.py; sprites=dec08a; light=indoor; swing=1.0;;
        chandelier2) script=build_chandelier.py; sprites=dec27a; light=indoor; swing=1.0;;
        candlestick) script=build_candlestick.py; sprites=dec02a; light=indoor;;
        torch) script=build_torch.py; sprites=dec06a; light=outdoor;;
        campfire) script=build_campfire.py; sprites="dec24a dec24x"; light=outdoor;;
        buoy) script=build_buoy.py; sprites="dec30a dec30f"; light=outdoor;;
    esac
    "$BLENDER" --background --python "scripts/$script" -- "$prop" 2>&1 | grep -E 'LEVEL|EXPORTED|TINT|Error|Traceback|line [0-9]'
    "$BLENDER" --background --python scripts/review.py -- "$prop" "work/${prop}_export.glb" $light $swing 2>&1 \
        | grep -E 'REVIEW|Error|Traceback|line [0-9]'
    python3 scripts/sheet.py "$prop" $sprites
    python3 scripts/finish.py "$prop" $INSTALL
done

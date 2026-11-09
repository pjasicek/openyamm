#!/bin/sh
# Rebuild the textured wall torches: textures, then for each model build, finish (validate; install with --install),
# review renders and sheet in torch_textures/review/<prop>/ with native-versus-model band means, and a close-up sheet
# of the clamp and head (closeup.png).
# Usage: run_all.sh [--install] [prop ...]   (props: torch torch_free torchnf torchnf_free irontorch irontorch_free
#        irontorch_unlit irontorch_unlit_free torch01 torch01_free; default all)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
D=$HERE/../..
BLENDER=/snap/bin/blender
INSTALL=
if [ "$1" = "--install" ]; then INSTALL=--install; shift; fi
PROPS=${*:-"torch torch_free torchnf torchnf_free irontorch irontorch_free irontorch_unlit irontorch_unlit_free torch01 torch01_free"}
python3 -I "$HERE/make_textures.py"
for PROP in $PROPS; do
    case $PROP in
        torch|torch_free) BUILD=$D/scripts/build_torch.py; FINISH=$D/scripts/finish.py; WORK=$D/work
            NATIVE=torch01; BANDS="0:25 26:41 43:57 59:72"; CLOSE="20 80" ;;
        torchnf|torchnf_free) BUILD=$D/scripts/build_torch.py; FINISH=$D/scripts/finish.py; WORK=$D/work
            NATIVE=torchnf; BANDS="0:25 26:41 43:57 59:74"; CLOSE="20 80" ;;
        irontorch|irontorch_free) BUILD=$D/torches/scripts/build_irontorch.py; FINISH=$D/torches/scripts/finish.py
            WORK=$D/torches/work; NATIVE=trchb00; BANDS="0:5 6:29 30:47 48:77 78:92"; CLOSE="25 95" ;;
        irontorch_unlit|irontorch_unlit_free) BUILD=$D/torches/scripts/build_irontorch.py
            FINISH=$D/torches/scripts/finish.py; WORK=$D/torches/work; NATIVE=nwtrchnf; BANDS="0:5 6:29 30:47 48:77 78:93"; CLOSE="25 95" ;;
        torch01|torch01_free) BUILD=$D/torches/scripts/build_torch01.py; FINISH=$D/torches/scripts/finish.py
            WORK=$D/torches/work; NATIVE=torch01a; BANDS="0:40 44:54 55:67 68:80"; CLOSE="40 90" ;;
        *) echo "unknown prop $PROP"; exit 2 ;;
    esac
    $BLENDER --background --python "$BUILD" -- "$PROP" 2>&1 | grep -E "^LEVEL|EXPORTED|Error|Traceback" || true
    python3 "$FINISH" "$PROP" $INSTALL
    $BLENDER --background --python "$HERE/review.py" -- "$PROP" "$WORK/${PROP}_export.glb" 2>&1 \
        | grep -E "^REVIEW|Error|Traceback" || true
    python3 "$HERE/sheet.py" "$PROP" "$NATIVE" $BANDS
    $BLENDER --background --python "$HERE/closeup.py" -- "$PROP" "$WORK/${PROP}_export.glb" $CLOSE 2>&1 \
        | grep -E "^CLOSEUP|Error|Traceback" || true
    python3 "$HERE/closeup_sheet.py" "$PROP" "$NATIVE" $CLOSE
done

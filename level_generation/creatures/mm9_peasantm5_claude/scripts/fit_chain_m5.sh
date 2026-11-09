#!/bin/bash
# PeasantM5 body fit to MM9 M5's silhouette (coordinator, 2026-11-02): five fit_body_m5.py passes from the pre-lining master.
set -e
cd "$(dirname "$0")/.."
W=$PWD/work; M=$W/mm9_dumps/m5.npz
export BAND=-0.20,0.30
# final settings (see-through tests r6-r16 in the README): forearms out of the fit, upper arms full, armpit folds protected
export FA_FADE=${FA_FADE:-100} UA_END=${UA_END:-1.0} ARMPIT=${ARMPIT:-1}
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python scripts/band_scale.py -- $W/lid_m5_v3.blend $W/band_m5.blend $M 2>&1 | grep -E "BAND_SCALE|Error|Trace" | cut -c1-120
B="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python scripts/fit_body_m5.py --"
$B $W/band_m5.blend $W/fitc_1.blend $M $W/fitc_1.json 2>&1 | grep -E "^FIT|Error|Trace"
$B $W/fitc_1.blend $W/fitc_2.blend $M $W/fitc_2.json 2>&1 | grep -E "^FIT|Error|Trace"
RAY=${RAY:-1} $B $W/fitc_2.blend $W/fitc_3.blend $M $W/fitc_3.json 2>&1 | grep -E "^FIT|Error|Trace"
RAY=${RAY:-1} WEB=${WEB:-1} $B $W/fitc_3.blend $W/fitc_4.blend $M $W/fitc_4.json 2>&1 | grep -E "^FIT|Error|Trace"
SIGMA=0.01 RAD=0.025 RAY=${RAY:-1} WEB=${WEB:-1} $B $W/fitc_4.blend $W/fit_m5_final.blend $M $W/fit_m5_final.json 2>&1 | grep -E "^FIT|Error|Trace"
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python scripts/move_despike.py -- $W/lid_m5_v3.blend $W/fit_m5_final.blend $W/fit_m5_ds.blend 2>&1 | grep -E "DESPIKE|Error|Trace"

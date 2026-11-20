#!/bin/bash
# v3 geometry chain: cdr1 import -> neck plane -> bisect cut -> head graft + loft -> mesh -> spine row -> UVs/uploads.
set -e
cd "$(dirname "$0")/../.."
B="blender -b --factory-startup"
q() { grep -E "$1" || true; }
step=${1:-import}
case $step in import)
  $B -P scripts/v3/import_cdr1.py 2>&1 | q "WELD|TRIS|Error"
  $B work/v3/src.blend -P scripts/v3/dump.py -- work/v3/src.npz 2>&1 | q "DUMPED|Error"
  ;& cut)
  read C N <<< "$(python3 scripts/v3/graft.py plane | awk '/PLANE/{print $2, $3}')"
  $B work/v3/src.blend -P scripts/v3/cut_cdr1.py -- $C $N work/v3/cut.blend 2>&1 | q "CUT|Error"
  $B work/v3/cut.blend -P scripts/v3/dump.py -- work/v3/cut.npz 2>&1 | q "DUMPED|Error"
  ;& graft)
  python3 scripts/v3/graft.py | cut -c1-400
  $B work/v3/cut.blend -P scripts/v3/build_mesh.py -- work/v3/graft.npz work/v3/graft_preview.blend --preview 2>&1 | q "BUILT|Error"
  ;& spines)
  $B work/v3/graft_preview.blend -P scripts/v3/add_spines.py -- work/v3/spines.blend 2>&1 | q "SPINES|Error" | cut -c1-120
  ;& uv)
  $B -P scripts/v3/uv_v3.py 2>&1 | q "FILLED|UV |Error" | cut -c1-300
  ;& meshy_uv)
  # the retextures were painted on the layout recorded in their returns: restore it exactly
  [ -f meshy/body_retexture_v3/model_urls_glb.glb ] && $B -P scripts/v3/meshy_uvs.py 2>&1 | q "MESHY_UV|Error"
  $B -P scripts/v3/sym_spines.py 2>&1 | q "SYM_SPINES|Error"
  python3 scripts/v3/reshape_neck.py | q "RESHAPE|APPLIED|Error"
  ;& bake)
  $B -P scripts/v3/bake_maps.py 2>&1 | q "BAKED|Error"
  ;;
esac

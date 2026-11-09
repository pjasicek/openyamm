#!/usr/bin/env bash
# Whole reduction from the rollback source: import + weld -> dumps -> regions/sets -> picked ladder (j, 0.83) ->
# export with LODs/variants -> checks -> viewer. Usage: TOKEN=<lease> scripts/reproduce.sh
set -euo pipefail
cd "$(dirname "$0")/.."; P=$PWD
REA_GLB=level_generation/creatures/mm7_m222_reduce_claude/work/mm7_m222_source_pre_reduce.glb REA_NODE=M222 scripts/blend.sh import_source.py | grep -E "WELD|SIZE|TRIS"
REA_PROTECT=B_Head scripts/blend.sh dump_mesh.py | grep DUMPED; scripts/blend.sh dump_groups.py | grep GROUPS
python3 scripts/extract_basecolor.py work/mm7_m222_source_pre_reduce.glb; REA_SMALL=80 python3 scripts/small_pieces.py | tail -1
python3 scripts/m222_regions.py; python3 scripts/trim_faces.py
M222_FACE_Y=-0.055 M222_BOOT_Z=0.52 M222_TORSO_Z=0.98 M222_KEEP_PAINT=1 python3 scripts/m222_sets.py j
REA_KEEP_FACES=work/keep_j.npy REA_GROUPS=work/groups_j.npy REA_GROUP_RATIOS=3:0.6,4:0.5,5:0.6,6:0.75,7:0.8,9:0.48,10:0.75,11:0.8 \
  scripts/run_ladder.sh j 0.83
scripts/build_export.sh j Cand_83
python3 scripts/compare_structure.py work/mm7_m222_source_pre_reduce.glb export/mm7_m222.glb | tail -1
python3 scripts/grip_check.py work/mm7_m222_source_pre_reduce.glb export/mm7_m222.glb M222
REA_NODE=M222 scripts/blend.sh lod_check.py "$P/export/mm7_m222.glb" red | grep -c LODCHECK
python3 scripts/viewer_variants.py work/mm7_m222_source_pre_reduce.glb r100; python3 scripts/viewer_variants.py export/mm7_m222.glb r83
for t in a b c; do for g in r100 r83; do python3 scripts/viewer_sword.py review/viewer/mm7_m222_${t}_$g.glb $t; done; done
python3 scripts/viewer_manifest.py "MM7 Chain Fighter (m222)" r83 9666 8020

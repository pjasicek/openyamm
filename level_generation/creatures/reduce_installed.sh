#!/usr/bin/env bash
# Texture-aware reduction of an installed creature, auto-pick, no retexture (RETOPOLOGY_PLAYBOOK.md default route,
# no-rebuild branch). Usage: reduce_installed.sh <name> <mesh node> "<title>"  (model assets_source/worlds/mm6/models/mm6_<name>.glb)
# -> mm6_<name>_reduce_claude/: ladder, export/mm6_<name>.glb (LODs + variants), review/viewer, review/close. No install.
set -euo pipefail
name=$1; node=$2; title=$3
C="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$C/../.." && pwd)"; P="$C/mm6_${name}_reduce_claude"
VENV="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/da4542c9-2ca5-4473-bf19-87d753441380/scratchpad/im_venv/bin/python -I"
R=0.70,0.55,0.45,0.40,0.35,0.30,0.25
mkdir -p "$P"/{scripts,work,export,review/viewer,review/feedback}
cp "$C"/mm6_wdm_reduce_claude/scripts/{dump_mesh,decimate_tex,reduce_ladder,compare_ladder,import_source,export_cand,swap_lod0,carry_variants,viewer_variants,close_views,viewer_manifest}.py "$P/scripts/"
cp "$C"/mm6_wdm_reduce_claude/review/viewer/{index.html,review.js} "$P/review/viewer/"
sed -i -e "s#<title>.*</title>#<title>$title reduction</title>#" -e "s#<header>.*</header>#<header><h1>$title: installed vs auto-picked reduction</h1><p>Same textures, variants and clips; only the geometry is reduced.</p></header>#" "$P/review/viewer/index.html"
sed -i -e "s/MM6 Flying Demon/$title/g" -e "s/mm6-wdm-reduce-claude/mm6-$name-reduce-claude/" -e "s/mm6:wdm/mm6:$name/" -e "s/mm6_wdm_reduce_frame_feedback/mm6_${name}_reduce_frame_feedback/" "$P/review/viewer/review.js"
echo '{"findings": []}' > "$P/review/feedback/user_feedback.json"
cd "$P"; T0=$(date +%s)
glb="assets_source/worlds/mm6/models/mm6_${name}.glb"
size=$(REA_GLB=$glb REA_NODE=$node blender -b -P scripts/import_source.py 2>&1 | tee work/import.log | grep -E "^SIZE" | sed 's/SIZE //')
height=$(python3 -c "print(max($size))"); grep -E "WELD|TRIS" work/import.log
blender -b -P scripts/dump_mesh.py > work/dump.log 2>&1
$VENV scripts/decimate_tex.py work $R > work/decimate.log
REA_METHOD=texture REA_RATIOS=$R blender -b -P scripts/reduce_ladder.py > work/ladder.log 2>&1
REA_HEIGHT_M=$height python3 scripts/compare_ladder.py > work/compare.log
pick=$(python3 -c "import json;print(json.load(open('work/selection.json'))['picked'] or '')")
python3 - <<PY
import json;d=json.load(open('work/selection.json'));print('height $height m, limits',d['thresholds_mm'],'source',d['source_tris'],'picked',d['picked'])
for t,c in d['ladder'].items(): print(' ',t,c['tris'],'p99',c['p99_mm'],'max',c['max_mm'],'IoU',c['iou_min'],'SSIM',c['ssim_mean'],'PASS' if c['pass'] else 'fail')
PY
[ -n "$pick" ] || { echo "NO PASSING STEP for $name"; exit 0; }
T1=$(date +%s)
REA_CAND=Cand_${pick#r} REA_NODE=$node blender -b -P scripts/export_cand.py > work/export_cand.log 2>&1
python3 scripts/swap_lod0.py "$ROOT/$glb" work/cand_export.glb export/mm6_${name}_lod0.glb "$node"
blender -b -P "$ROOT/tools/build_actor_lods.py" -- export/mm6_${name}_lod0.glb export/mm6_${name}.glb --mesh-node "$node" 2>&1 | grep "LOD tri"
python3 scripts/carry_variants.py export/mm6_${name}.glb
python3 scripts/viewer_variants.py "$ROOT/$glb" r100 > /dev/null; python3 scripts/viewer_variants.py export/mm6_${name}.glb $pick > /dev/null
src=$(python3 -c "import json;print(json.load(open('work/selection.json'))['source_tris'])")
ptris=$(python3 -c "import json;d=json.load(open('work/selection.json'));print(d['ladder'][d['picked']]['tris'])")
python3 scripts/viewer_manifest.py "$title" $pick $src $ptris
first=$(ls review/viewer | grep -m1 "_${pick}.glb" | sed "s/_${pick}.glb//")
mkdir -p review/close; for t in r100 $pick; do blender -b -P scripts/close_views.py -- review/viewer/${first}_$t.glb $t > work/close_$t.log 2>&1; done
python3 - <<PY
from PIL import Image
for spot in ['whole','head','hand']:
    s=Image.new('RGB',(1200,800))
    for i,v in enumerate(['front','q34','side']):
        for j,t in enumerate(['r100','$pick']): s.paste(Image.open(f'review/close/{t}_{spot}_{v}.png').convert('RGB').resize((400,400)),(i*400,j*400))
    s.save(f'review/close/sheet_{spot}.png')
PY
echo "TIMES ladder $((T1-T0))s build+viewer $(( $(date +%s)-T1 ))s"

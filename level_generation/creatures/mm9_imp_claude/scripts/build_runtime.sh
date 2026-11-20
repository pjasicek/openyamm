#!/usr/bin/env bash
# MM9 Imp runtime GLBs: master blend -> textured export -> MM9 clips + solved fist -> prepare -> LODs -> shadow fix ->
# A/B/C skins (region ramps) -> attachments split (trident; tier parts) -> floor pass -> mirror to true handedness ->
# winding check [-> install]. Usage (project folder): PYGLTF_PYTHON=<gltf venv python> TOKEN=<lease> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
n=imp; N=Imp; V="${PYGLTF_PYTHON:?set PYGLTF_PYTHON}"; : "${TOKEN:?set TOKEN}"
rel="level_generation/creatures/$(basename "$here")"
BLEND="${BLEND:-work/master.blend}"
HT="${HEADTEX:-imp}"
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|HEADFIX" "$log" | cut -c1-300 || true; }
B "$rel/scripts/build_export_imp.py" "$here/$BLEND" "$here/work/${n}_body_tex.glb" "$N" "$n" "$n" "$HT"
"$V" scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips.glb scripts/roles_imp.json work/clips.json 2>&1 | grep -v "Unexpected value"
if [[ -f scripts/hand_rest_imp.txt ]]; then
  cur=work/mm9_${n}_clips.glb; k=0
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    k=$((k + 1)); nxt=work/mm9_${n}_rest${k}.glb
    eval "python3 scripts/hand_rest.py $cur $nxt $line" | cut -c1-200
    cur=$nxt
  done < scripts/hand_rest_imp.txt
  cp "$cur" export/mm9_${n}_lod0.glb
else
  python3 scripts/trident_clear.py work/mm9_${n}_clips.glb export/mm9_${n}_lod0.glb AttackMelee Hit AttackRanged Fidget Death | cut -c1-160
fi
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N"
python3 ../claude_shared/region_variants.py export/mm9_${n}_lods_shadowfix.glb export/mm9_${n}_skins.glb textures/imp_ramps.json \
  --extra Imp openyamm_specular=0 --extra Imp pbr.metallicFactor=0
# attachments first: the floor pass must not see the trident's butt, which swings under the feet
python3 "$repo/tools/split_attachment.py" export/mm9_${n}_skins.glb --joint Yweaponbase --body work/split1.glb \
  --attachment export/mm9_${n}_trident_m.glb
python3 "$repo/tools/split_attachment.py" work/split1.glb --joint "Xwrap L" --body work/split2.glb --attachment export/mm9_${n}_wrapl_m.glb
python3 "$repo/tools/split_attachment.py" work/split2.glb --joint "Xwrap R" --body work/split3.glb --attachment export/mm9_${n}_wrapr_m.glb
python3 "$repo/tools/split_attachment.py" work/split3.glb --joint Xtongue --body work/split4.glb --attachment export/mm9_${n}_tongue_m.glb
python3 ../claude_shared/floor/floor_fix.py work/split4.glb work/floor1.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead
python3 ../claude_shared/floor/floor_fix.py work/floor1.glb work/floor.glb $(cat scripts/floor_ops_hit.txt)
# glow: eyes (the mask's luminance), on the head material of each tier
python3 ../claude_shared/emission.py work/floor.glb work/glow.glb --material ImpHead --mask work/imp_eye_mask.png \
  --color imp_a=0.05,0.9,0.1 --color imp_b=0.62,0.36,0.02 --color imp_c=0.6,0.13,0.01 --strength 0.42
python3 scripts/mirror_glb.py work/glow.glb export/mm9_${n}.glb
for p in trident wrapl wrapr tongue; do python3 scripts/mirror_glb.py export/mm9_${n}_${p}_m.glb export/mm9_${n}_${p}.glb; done
# the viewer shows everything in one GLB: the full model with the floored clips
"$V" ../claude_shared/graft_clips.py export/mm9_${n}_skins.glb work/floor.glb work/full_floor.glb --replace --clip Standing --clip Walking --clip Running --clip Fidget --clip Taunt --clip AttackMelee --clip AttackRanged --clip Hit --clip Death --clip Dead 2>&1 | grep -v "Unexpected value" | tail -1
python3 ../claude_shared/emission.py work/full_floor.glb work/full_glow.glb --material ImpHead --mask work/imp_eye_mask.png \
  --color imp_a=0.05,0.9,0.1 --color imp_b=0.62,0.36,0.02 --color imp_c=0.6,0.13,0.01 --strength 0.42
python3 scripts/mirror_glb.py work/full_glow.glb export/mm9_${n}_full.glb
python3 scripts/fix_winding.py export/mm9_${n}.glb work/wound.glb && mv work/wound.glb export/mm9_${n}.glb
python3 scripts/fix_winding.py export/mm9_${n}_full.glb work/wound.glb && mv work/wound.glb export/mm9_${n}_full.glb
rm -f export/mm9_${n}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  for f in mm9_${n} mm9_${n}_trident mm9_${n}_wrapl mm9_${n}_wrapr mm9_${n}_tongue; do
    python3 "$repo/tools/install_model.py" export/$f.glb --world mm9
  done
fi
ls -la export/mm9_${n}*.glb | cut -c25-

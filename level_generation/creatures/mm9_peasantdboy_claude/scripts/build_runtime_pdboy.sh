#!/usr/bin/env bash
# Runtime GLB for mm9_peasantdboy (the PeasantBoy chain on PEASANTDBOY1.abc's own 38-joint skeleton and clips): rigged
# master -> textured export -> MM9 clips (+ finger aliases) -> hand rest (scripts/hand_rest_pdboy.txt) -> prepare -> LODs ->
# shadow fix -> tiers (body: region mask + ramps; head: tier b image, a different boy) -> material extras -> floor fix ->
# true handedness (mirror_glb.py) -> winding check [-> install --world mm9]. Every Blender step memory-capped (12G, no swap).
# Usage (from the repo root): TOKEN=<lease> [BLEND=work/....blend] level_generation/creatures/mm9_peasantdboy_claude/scripts/build_runtime_pdboy.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
: "${TOKEN:?set TOKEN}"
V=../claude_shared/gltf_venv/bin/python
CAP=(systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0)
rel="level_generation/creatures/$(basename "$here")"
n=pdboy; N=PeasantDBoy
B() { local out log; out=$(cd "$repo" && "${CAP[@]}" tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|HEADFIX|LOD triangles" "$log" | cut -c1-200 || true; }
mkdir -p export work
[[ -n "${SKIP_EXPORT:-}" ]] || B "$rel/scripts/build_export_v2.py" "$here/${BLEND:-work/linings_v3.blend}" "$here/work/${n}_body_tex.glb" "$N" pdboy_tp pdboy pdboy_tp
PYTHONPATH=/usr/lib/python3/dist-packages "$V" scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips.glb scripts/roles_dboy.json work/clips_v1.json 2>/dev/null | cut -c1-240
# Fidget's hands hang against the flared tunic skirt and on the hips, Running's right hand brushes it: the upper arm turns
# the least that clears them (arm_clear.py, smoothed, capped)
PYTHONPATH=/usr/lib/python3/dist-packages "$V" -W ignore scripts/arm_clear.py work/mm9_${n}_clips.glb work/mm9_${n}_clear.glb --side L=' L ' --side R=' R ' \
  --clips ${ARMCLIPS:-Fidget,Running} --outer-only --max-deg ${ARMCAP:-20} 2>&1 | grep -E "ARMCLEAR|Traceback|Error" | cut -c1-200 || true
# second pass: the elbow takes the rest (two joints share the turn, each slower: jitter gate)
PYTHONPATH=/usr/lib/python3/dist-packages "$V" -W ignore scripts/arm_clear.py work/mm9_${n}_clear.glb work/mm9_${n}_clear2.glb --side L=' L ' --side R=' R ' \
  --clips ${ARMCLIPS2:-Fidget} --outer-only --max-deg ${ARMCAP2:-25} --upper Forearm 2>&1 | grep -E "ARMCLEAR|Traceback|Error" | cut -c1-200 || true
# per-key corrections jitter (jitter gate: shoulder skin 8-12 mm/f2): each corrected arm takes ONE rotation, the mean of
# its corrections, faded in and out (arm_bump.py, from mm9_banshee_claude)
cur=work/mm9_${n}_clips.glb; b=0
while IFS=: read -r bc bj be bd bt0 bt1 bf; do
  [[ -z "$bc" ]] && continue
  b=$((b + 1)); BUMP_T0=${bt0:-} BUMP_T1=${bt1:-} PYTHONPATH=/usr/lib/python3/dist-packages "$V" -W ignore scripts/arm_bump.py $cur work/mm9_${n}_${bf:-clear}.glb work/mm9_${n}_bump$b.glb "$bc" "$bj" "$be" $bd 2>&1 | tail -1 | cut -c1-160
  cur=work/mm9_${n}_bump$b.glb
done < scripts/arm_bumps_pdboy.txt
k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); nxt=work/mm9_${n}_rest${k}.glb
  eval "python3 scripts/hand_rest.py $cur $nxt $line" | grep HANDREST | cut -c1-240
  cur=$nxt
done < scripts/hand_rest_${n}.txt
cp "$cur" export/mm9_${n}_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
"${CAP[@]}" /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N"
PYTHONPATH=/usr/lib/python3/dist-packages "$V" ../claude_shared/region_variants.py export/mm9_${n}_lods_shadowfix.glb work/mm9_${n}_rv.glb textures/pdboy_ramps.json 2>/dev/null | tail -1 | cut -c1-200
PYTHONPATH=/usr/lib/python3/dist-packages "$V" scripts/tier_head.py work/mm9_${n}_rv.glb work/mm9_${n}_tiers.glb PeasantDBoyHead pdboy_b=pdboyb_tp 2>/dev/null
python3 scripts/set_material_extras.py work/mm9_${n}_tiers.glb export/mm9_${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0
python3 ../claude_shared/floor/floor_fix.py export/mm9_${n}_extras.glb work/mm9_${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -3
# true handedness: convert_abc_model.py keeps LithTech's left-handed numbers, so the unmirrored build is the actor in a mirror
PYTHONPATH=/usr/lib/python3/dist-packages $V scripts/mirror_glb.py work/mm9_${n}_floor.glb export/mm9_${n}.glb | tail -1
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_${n}.glb --world mm9 --name mm9_peasantdboy.glb
fi
ls -la export/mm9_${n}.glb

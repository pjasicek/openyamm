#!/usr/bin/env bash
# Runtime GLB of one PeasantDF design (one shared mesh, rig and clip set; the design's own body + head paints):
# master blend -> textured export -> MM9 clips (soft offsets) -> relaxed fingers -> hand rest -> prepare -> LODs ->
# shadow fix -> tiers (region masks + ramps, body and head) -> material extras -> floor fix -> true handedness (mirror)
# -> winding check [-> install --world mm9 --name mm9_peasantdf<N>.glb].
# Usage (repo root): TOKEN=<lease> [BLEND=work/master_v2.blend] level_generation/creatures/mm9_peasantdf_claude/scripts/build_runtime_pdf.sh <d1..d4> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
: "${TOKEN:?set TOKEN}"
d=$1; k=${d#d}; n=pdf$k; pre=pdf${k}_tp; N=PeasantDF
V=../claude_shared/gltf_venv/bin/python
CAP="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0"
rel="level_generation/creatures/$(basename "$here")"
B() { local out log; out=$(cd "$repo" && $CAP tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LOD triangles" "$log" | cut -c1-200 || true; }
mkdir -p export work
B "$rel/scripts/build_export_v2.py" "$here/${BLEND:-work/master_v2.blend}" "$here/work/${n}_body_tex.glb" "$N" $pre pdf $pre
$CAP $V scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips.glb scripts/roles_pdf.json work/clips_${n}.json 2>/dev/null | cut -c1-160
$CAP python3 scripts/finger_pose.py work/mm9_${n}_clips.glb work/mm9_${n}_fp.glb --mcp-extra 0 --pip-extra 0 --thumb-ip 6 --thumb-in 3 | grep -c FINGERPOSE >/dev/null
cur=work/mm9_${n}_fp.glb; i=0
if [[ -f scripts/hand_rest_pdf.txt ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    i=$((i + 1)); nxt=work/mm9_${n}_rest${i}.glb
    eval "$CAP python3 scripts/hand_rest.py $cur $nxt $line" | grep HANDREST | cut -c1-200
    cur=$nxt
  done < scripts/hand_rest_pdf.txt
fi
cp "$cur" export/mm9_${n}_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
$CAP /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
$CAP python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N" | tail -1 | cut -c1-160
$CAP $V ../claude_shared/region_variants.py export/mm9_${n}_lods_shadowfix.glb work/mm9_${n}_rv.glb textures/${d}_ramps.json 2>/dev/null | tail -1 | cut -c1-200
python3 scripts/set_material_extras.py work/mm9_${n}_rv.glb export/mm9_${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0
python3 ../claude_shared/floor/floor_fix.py export/mm9_${n}_extras.glb work/mm9_${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -3
$V scripts/mirror_glb.py work/mm9_${n}_floor.glb export/mm9_peasantdf${k}.glb | tail -1
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_peasantdf${k}.glb | tail -1
if [[ "${2:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_peasantdf${k}.glb --world mm9
fi
ls -la export/mm9_peasantdf${k}.glb

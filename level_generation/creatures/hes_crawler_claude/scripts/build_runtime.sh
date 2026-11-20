#!/usr/bin/env bash
# Acid Crawler runtime GLBs, NOT installed (the Hesper stage integrates them):
# export -> prepare -> LODs -> shadow fix -> A/B/C skins (region ramps) -> four rigid attachments split out
# (Pods for B, Sacs_F/M/R for C) -> winding check. Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/hes_crawler_lod0.glb export/hes_crawler_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/hes_crawler_runtime_lod0.glb" \
  "$here/export/hes_crawler_lods.glb" --mesh-node Crawler 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/hes_crawler_lods.glb export/hes_crawler_lods_shadowfix.glb
python3 scripts/tier_ramps.py > /dev/null
python3 ../claude_shared/region_variants.py export/hes_crawler_lods_shadowfix.glb export/hes_crawler_full.glb \
  textures/hcr_ramps.json --extra Crawler openyamm_specular=0 --extra Crawler pbr.metallicFactor=0
cp export/hes_crawler_full.glb export/hes_crawler.glb
for j in Pods Sacs_F Sacs_M Sacs_R; do
  lower=$(echo $j | tr 'A-Z' 'a-z')
  python3 "$repo/tools/split_attachment.py" export/hes_crawler.glb --joint $j --body export/hes_crawler.glb \
    --attachment export/hes_crawler_${lower}.glb
done
# Glowing acid (engine emission and creature bloom, 2026-10-22): the acid mask as the emissive texture, each tier's
# acid colour (tier_ramps.py, acid ramp top stop) as its emissive factor, a gentle pulse.
python3 ../claude_shared/emission.py export/hes_crawler.glb export/hes_crawler.glb --material Crawler_ \
  --mask textures/hcr_glow_mask.png --gamma 1.5 --strength 0.6 --pulse 0.2,2.5 \
  --color crawler_a=0.581,0.76,0.108 --color crawler_b=0.9,0.838,0.059 --color crawler_c=0.605,0.874,0.072
rm -f export/hes_crawler_lods.geometry.glb
for g in export/hes_crawler.glb export/hes_crawler_pods.glb export/hes_crawler_sacs_*.glb; do
  python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$g" | tail -1
done
ls -la export/hes_crawler*.glb

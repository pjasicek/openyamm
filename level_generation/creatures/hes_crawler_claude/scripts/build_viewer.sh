#!/usr/bin/env bash
# Review viewer GLBs: per tier the LOD0 export with the tier colours baked (work/tier_<v>.png from tier_ramps.py) and
# only that tier's attachments joined (B pods, C sacs), normal map converted; then the manifest.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
for v in a b c; do
  keep=","; [ $v = b ] && keep="Crawler_Pods,"; [ $v = c ] && keep="Crawler_Sacs,"
  scripts/step.sh export_glb.py work/viewer_$v.glb work/tier_crawler_$v.png "$keep"
  python3 "$repo/tools/prepare_actor_glb.py" work/viewer_$v.glb review/viewer/hes_crawler_$v.glb | tail -1
done
# The glowing acid, as in the runtime GLB (three.js shows emissive maps; the game adds bloom).
for t in a:0.581,0.76,0.108 b:0.9,0.838,0.059 c:0.605,0.874,0.072; do
  python3 ../claude_shared/emission.py review/viewer/hes_crawler_${t%%:*}.glb review/viewer/hes_crawler_${t%%:*}.glb \
    --material Crawler_A --mask textures/hcr_glow_mask.png --gamma 1.5 --strength 0.6 --color ${t#*:}
done
python3 scripts/viewer_manifest.py

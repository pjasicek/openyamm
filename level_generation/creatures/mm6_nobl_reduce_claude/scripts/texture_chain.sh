#!/usr/bin/env bash
# Swordsman texture/runtime chain after the Meshy jobs (README "Front detail set"): body (1K) and detail (2K) compose,
# collar de-streak in the head maps, runtime build from work/ladder_final.blend, final 3104 x 2080 atlases, viewer GLBs
# -> export/mm6_nobl.glb. Geometry/UV steps before the jobs (chest_repair, body_uv, buckle_uv, detail_faces, detail_uv)
# change what Meshy painted; rerunning them needs new Meshy jobs. detail_groups.py and atlas_layout.py only remap UVs.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/compose_body.py > /dev/null
REA_SET=detail python3 scripts/compose_body.py > /dev/null
python3 scripts/head_collar.py
scripts/build_pick.sh r62 final
python3 scripts/atlas_final.py export/mm6_nobl_finalr62.glb export/mm6_nobl_finalr62.glb
cp export/mm6_nobl_finalr62.glb export/mm6_nobl.glb
python3 scripts/viewer_variants.py export/mm6_nobl.glb finalr62 > /dev/null

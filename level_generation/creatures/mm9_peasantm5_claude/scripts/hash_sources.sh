#!/bin/bash
# sha256 of every file of the frozen source project (Markel) + its installed/runtime GLBs. Usage (repo root): hash_sources.sh <out.txt>
cd /home/pjasicek/github/OpenYAMM
{ find level_generation/creatures/mm9_markel_claude -type f ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum
  sha256sum assets_source/worlds/mm9/models/mm9_markel.glb assets_dev/worlds/mm9/models/mm9_markel.glb; } > "$1"
wc -l "$1"

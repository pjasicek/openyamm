#!/bin/bash
# sha256 of every file of the frozen source projects + their installed/runtime GLBs. Usage (repo root): hash_sources.sh <out.txt>
cd /home/pjasicek/github/OpenYAMM
{ find level_generation/creatures/mm9_peasantm8_claude level_generation/creatures/mm9_forad_claude -type f ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum
  sha256sum assets_source/worlds/mm9/models/mm9_peasantm8.glb assets_dev/worlds/mm9/models/mm9_peasantm8.glb \
    assets_source/worlds/mm9/models/mm9_forad.glb assets_dev/worlds/mm9/models/mm9_forad.glb; } > "$1"
wc -l "$1"

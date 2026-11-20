#!/bin/bash
# One codex exec per shot in parallel (at most 16 at once):  concepts/run.sh <map> <shot>...
# Input: the map's capture of the shot (review/<map>/capture/<shot>.png, New Sorpigal: review/town_original);
# output: concepts/<map>/<shot>_A.png (New Sorpigal: concepts/<shot>_A.png).
cd /home/pjasicek/github/OpenYAMM
D=level_generation/projects/mm6_sorpigal_geometry_pilot
MAP=$1; shift
NAME=$(python3 -c "import sys; sys.path.insert(0, '$D/source'); import maps; print(maps.NAMES['$MAP'])")
if [ "$MAP" = oute3 ]; then IN=$D/review/town_original; OUT=$D/concepts; else IN=$D/review/$MAP/capture; OUT=$D/concepts/$MAP; fi
mkdir -p "$OUT"
for s in "$@"; do
  while [ "$(jobs -rp | wc -l)" -ge 16 ]; do wait -n; done
  codex exec "Read and follow $D/concepts/COMMON_A.md exactly. Map: $NAME. Shot: $s. The attached image is the input. Output: $OUT/${s}_A.png. Use your built-in image generation tool. Do not write code or modify any other file." \
    -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
    -o "$OUT/${s}_last.md" -i "$IN/$s.png" < /dev/null > "$OUT/${s}_run.log" 2>&1 &
done
wait
echo done

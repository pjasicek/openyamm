#!/bin/bash
# Runs one codex exec image worker per view in parallel; waits for all.
cd /home/pjasicek/github/OpenYAMM
D=level_generation/geometry_study_20261111
pids=()
for v in "$@"; do
  img=$(ls $D/captures/*-$v.png)
  codex exec "Follow the brief in $D/briefs/$v.md exactly. The attached image is its input." \
    -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write \
    --add-dir ~/.codex/generated_images -o $D/concepts/${v}_last_message.md -i "$img" \
    < /dev/null > $D/concepts/${v}_run.log 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
echo done

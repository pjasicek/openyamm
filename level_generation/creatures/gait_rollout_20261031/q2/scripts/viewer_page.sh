#!/bin/sh
# Give a creature project's review viewer the page of ../../mm7_m382_reduce_claude/review/viewer (itself the
# mm9_bigfoot_claude page) when it has none, and a feedback file; then copy the GLBs to review into it.
#   viewer_page.sh <project dir> <creature id, e.g. mm7:m509> <title> <glb> [<glb> ...]
set -e
project=$1; creature=$2; title=$3; shift 3
here=$(dirname "$0")/../../..
viewer=$project/review/viewer
src=$here/mm7_m382_reduce_claude/review/viewer
mkdir -p "$viewer/feedback"
[ -f "$viewer/feedback/user_feedback.json" ] || echo '{"findings": []}' > "$viewer/feedback/user_feedback.json"
if [ ! -f "$viewer/index.html" ]; then
    sed "s|<h1>.*</h1><p>.*</p>|<h1>$title</h1><p>Gait rollout q2 (2026-10-31): installed clips and the new gaits.</p>|" \
        "$src/index.html" > "$viewer/index.html"
    name=$(basename "$project")
    sed "s|creature:'mm7:m382'|creature:'$creature'|; s|mm7_m382_reduce_claude_frame_feedback|${name}_frame_feedback|" \
        "$src/review.js" > "$viewer/review.js"
fi
for glb in "$@"; do cp "$glb" "$viewer/"; done

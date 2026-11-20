#!/usr/bin/env bash
# Register, bake and review-render every design whose paint sheet exists and has no export yet (or is newer than it).
# Usage (from the project folder): scripts/process_ready.sh
set -uo pipefail
for brief in codex_tex/*/CODEX_BRIEF_paint.md; do
    folder=$(dirname "$brief")
    design=$(basename "$folder")
    raw=$(ls -t "$folder"/paint_mask_raw_v*.png "$folder"/paint_raw_v*.png 2>/dev/null | head -1)
    export=work/codex_tex/${design}_export.glb
    [ -n "$raw" ] || continue
    [ -f "$export" ] && [ "$export" -nt "$raw" ] && continue
    python3 scripts/register_views.py "$design" 2>&1 | grep -E 'REGISTERED|FAILED'
    blender --background --python scripts/codex_texture.py -- bake "$design" 2>&1 | grep -E 'BAKED|Error|rror:'
    [ -f "$export" ] && [ "$export" -nt "$raw" ] && blender --background --python scripts/review_render.py -- \
        "$export" "review/final/$design" >/dev/null 2>&1 && echo "RENDERED $design"
done

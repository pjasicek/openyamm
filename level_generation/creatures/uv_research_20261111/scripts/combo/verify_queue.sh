#!/usr/bin/env bash
# Port verification queue (2026-11-12): CREATURE_3D_TOKEN=<lease> verify_queue.sh <blend> <name> [unwrap args ...]
# Runs verify_port.py through the lease-checked Blender wrapper (waits while the write lock is busy), then puts the
# placeholder material back and measures with texture_quality.py. Outputs in uv_research_20261111/verify/.
set -euo pipefail
cd /home/pjasicek/github/OpenYAMM
U=level_generation/creatures/uv_research_20261111
OUT=$U/verify
mkdir -p "$OUT"
BLEND="$1"; NAME="$2"; shift 2
for attempt in $(seq 1 60); do
    if out=$(tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$U/scripts/combo/verify_port.py" \
            "$BLEND" "$OUT" "$NAME" "$@" 2>&1); then
        cp "$(echo "$out" | sed -n 's/^Blender log: //p')" "$OUT/$NAME.log"
        break
    fi
    log="$(echo "$out" | sed -n 's/^Blender log: //p')"
    if grep -q "Another creature operation is running" "$log" 2>/dev/null; then sleep 10; continue; fi
    cp "$log" "$OUT/$NAME.log" 2>/dev/null; echo "FAILED $NAME"; tail -20 "$OUT/$NAME.log"; exit 1
done
P=$U/../claude_shared/sparrow_venv/py/bin/python
"$P" "$U/scripts/layout/glb_add_material.py" "$OUT/${NAME}_measure.glb" "$OUT/${NAME}_measure.glb"
python3 "$U/../claude_shared/texture_quality.py" "$OUT/${NAME}_measure.glb" --by-bone --heatmap "$OUT/${NAME}_heat" \
    --json "$OUT/${NAME}_quality.json" | tail -1
grep -E "^VERIFY |UV_ATLAS FALLBACK|UV_ATLAS weld" "$OUT/$NAME.log" | cut -c1-600

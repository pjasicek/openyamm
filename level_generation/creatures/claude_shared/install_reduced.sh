#!/usr/bin/env bash
# Install one user-approved MM9 reduction candidate (REDUCTION_BRIEF_20261104.md "Review and install").
# Usage (repo root): level_generation/creatures/claude_shared/install_reduced.sh <short> <glb stem> <candidate path> <creature project dir>
#   e.g. install_reduced.sh lich mm9_lich level_generation/creatures/mm9_lich_reduce_claude/export/mm9_lich.glb level_generation/creatures/mm9_lich_claude
# Checks that the installed source still equals the reduction's before/ copy, runs the winding check, installs, marks the
# ledger row installed (under the ledger flock) and appends the post-install note to the creature README.
# Run the binding regression afterwards (once per batch).
set -euo pipefail
short=$1; stem=$2; cand=$3; creature=$4
proj=level_generation/creatures/mm9_${short}_reduce_claude
src=assets_source/worlds/mm9/models/${stem}.glb
cmp -s "$src" "$proj/before/${stem}.glb" || { echo "ABORT: $src differs from $proj/before/${stem}.glb"; exit 1; }
uvj=$(mktemp --suffix=.json)
python3 level_generation/creatures/claude_shared/reduction_uv_audit.py "$cand" "$proj/before/${stem}.glb" --json "$uvj" > /dev/null 2>&1 || true
python3 - "$uvj" <<'EOF' || { rm -f "$uvj"; echo "ABORT: UV audit — LOD0 faces leave the painted charts (or no audit output); fix with the chart guard first"; exit 1; }
import sys, json
d = json.load(open(sys.argv[1]))
n = sum(p['escaping'] for lods in d['nodes'].values() for p in lods[0])   # LOD0 of every mesh node
print('UV audit: LOD0 faces leaving the painted charts:', n)
sys.exit(0 if n == 0 else 1)
EOF
rm -f "$uvj"
w=$(python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$cand" | tail -1)
echo "$w"; case "$w" in *": 0") ;; *) echo "ABORT: winding"; exit 1;; esac
python3 tools/install_model.py "$cand" --world mm9 --name "${stem}.glb" | tail -1
flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock python3 - "$stem.glb" <<'EOF'
import sys, os, re
f = sys.argv[1]; p = 'level_generation/creatures/REDUCTION_LEDGER.md'; s = open(p).read()
head, sep, tail = s.partition('## MM9 reduction (started 2026-11-04)'); out = []
for l in tail.split('\n'):
    if re.match(r'\| \d+ \| ', l):
        c = l.split('|')   # ['', ' #', ' prio', ' model', ' file', ' before', ' after', ' lods', ' status', ...]
        if c[4].strip().strip('`') == f and not c[8].strip().startswith('installed'):
            c[8] = ' installed ' + __import__('datetime').date.today().isoformat() + ' (orchestrator pre-screen: looks the same; user rule "if they look the same then it is fine") — ' + c[8].strip() + ' '
            l = '|'.join(c)
    out.append(l)
t = p + '.tmp'; open(t, 'w').write(head + sep + '\n'.join(out)); os.replace(t, p)
EOF
printf '\n\n**LOD0 reduced post-install on %s by `%s/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `%s/before/`.\n' "$(date +%F)" "$proj" "$proj" >> "$creature/README.md"
echo "installed $stem"

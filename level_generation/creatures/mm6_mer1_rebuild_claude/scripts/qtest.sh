#!/usr/bin/env bash
# Untextured motion test of work/pruned_v1.blend: clips, helpers [, robe keys with ROBE=1] -> motion audit summary. Usage: scripts/qtest.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; export TOKEN=$(cat work/token); G=../claude_shared/gltf_venv/bin/python
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning\|Warn" ; }
scripts/B.sh quick_export.py $here/work/pruned_v1.blend $here/work/q.glb > /dev/null
Q $G scripts/clips_mm9.py work/q.glb work/q1.glb scripts/roles_mer.json work/q_clips.json | tail -1 | cut -c1-200
Q $G scripts/half_keys.py work/q1.glb work/q2.glb | tail -1
if [[ -n "${ROBE:-}" ]]; then Q $G scripts/robe_keys.py work/q2.glb work/q3.glb work/rig_v1.blend.robe.json work/q_robe.json | tail -1; else cp work/q2.glb work/q3.glb; fi
rm -rf work/audit_q3; python3 ../claude_shared/motion_audit.py work/q3.glb --out work/audit_q3 >/dev/null 2>&1
python3 -c "
import json;d=json.load(open('work/audit_q3/q3.json'))
for c,v in d['clips'].items(): print(c, {k:x['bad_pct'] for k,x in v['deform'].items()})"

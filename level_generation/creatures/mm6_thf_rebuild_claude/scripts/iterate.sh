#!/usr/bin/env bash
# Weight passes after the paint -> textured export -> clips -> motion audit summary. Usage (project folder): scripts/iterate.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; export TOKEN=$(cat work/token); W=$here/work
scripts/B.sh smooth_band.py $W/final_v1.blend $W/final_s1.blend 14 0.2 0.50 0.74 8
scripts/B.sh smooth_band.py $W/final_s1.blend $W/final_v2.blend 1 0.2 0.52 0.64 4
scripts/B.sh export_thf.py $W/final_v2.blend $W/thf_body_tex.glb | grep -v LIFT
scripts/clips.sh work/thf_body_tex.glb work/thf_clips.glb > work/clips_log.txt
python3 ../claude_shared/motion_audit.py work/thf_clips.glb --out work/audit_it >/dev/null 2>&1
python3 -c "
import json;d=json.load(open('work/audit_it/thf_clips.json'))
for c,v in d['clips'].items(): print(c, {k:x['bad_pct'] for k,x in v['deform'].items() if k in ('hand','arm','head','spine','leg','cloth')})"

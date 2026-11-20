#!/usr/bin/env bash
# Set up an anim-fix project from a gait-rollout package (from the repository root):
#   setup_from_package.sh <world> <id> <package, e.g. h11> <job prefix, e.g. m170>
# Claims <world>:<id> (prints the token), backs up the installed GLB and actors.yml to work/before_anim/, copies the
# package's scripts (path depths fixed for a direct child of creatures/), its jobs for the prefix, the pre-gait GLB,
# chain files and library sources, then checks that the composer reproduces the installed GLB byte for byte.
set -euo pipefail
W=$1; ID=$2; PKG=$3; PFX=$4
S=${W}_$ID
P=level_generation/creatures/${S}_animfix_claude
H=level_generation/creatures/gait_rollout_20261031/$PKG
mkdir -p "$P/work/before_anim" "$P/review" "$P/scripts" "$P/jobs" "$P/work/sources" "$P/work/exp" "$P/export"
python3 tools/creature_workspace.py claim --project "$P" --identity "$W:$ID" --owner anim-anim \
    | python3 -c "import json,sys;print('TOKEN', json.load(sys.stdin)['token'])"
cp "assets_source/worlds/$W/models/$S.glb" "$P/work/before_anim/"
cp "assets_dev/worlds/$W/models/actors.yml" "$P/work/before_anim/actors_$W.yml"
cp "$H"/scripts/*.py "$P/scripts/"; cp "$H"/scripts/*.sh "$P/scripts/" 2>/dev/null || true
cp "$H"/jobs/${PFX}_*.json "$P/jobs/"
cp "$H/work/${S}_pre_gait.glb" "$P/work/"
for f in "$H"/work/${PFX}_*chains*.json "$H"/work/${PFX}_*.json; do [ -f "$f" ] && cp "$f" "$P/work/"; done
python3 - "$H" "$P" <<'EOF'
import json, re, shutil, sys
from pathlib import Path
H, P = Path(sys.argv[1]), Path(sys.argv[2])
for job in sorted((P / 'jobs').glob('*.json')):
    text = job.read_text()
    for rel in set(re.findall(r'"(work/[^"]+)"', text)):
        src = H / rel
        if src.exists() and not (P / rel).exists():
            (P / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, P / rel)
EOF
cd "$P"
sed -i 's/ROOT = HERE.parents\[4\]/ROOT = HERE.parents[3]/' scripts/gaitlib.py
sed -i 's/HERE.parents\[2\]/HERE.parents[1]/g' scripts/*.py
sed -i 's|"$here/../../../.."|"$here/../../.."|' scripts/*.sh 2>/dev/null || true
jobs=$(python3 -c "
import json,glob
order={'walk2':0,'walk3':1,'jog':2,'run2':3,'run':3,'jog2':4,'sprint':5}
fs=sorted(glob.glob('jobs/*.json'),key=lambda f:order.get(f.split('_',1)[1][:-5],9))
print(' '.join(fs))")
echo "JOBS $jobs"
python3 scripts/compose_gait.py "work/${S}_pre_gait.glb" work/repro.glb $jobs > work/repro.log 2>&1 || tail -5 work/repro.log
a=$(sha256sum work/repro.glb | cut -c1-16); b=$(sha256sum "work/before_anim/$S.glb" | cut -c1-16)
[ "$a" = "$b" ] && echo "REPRO identical $a" || echo "REPRO DIFFERS $a vs $b"

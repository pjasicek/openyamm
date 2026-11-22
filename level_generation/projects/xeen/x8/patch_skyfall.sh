#!/bin/bash
# Scratch root only: A3's Xeen.skyFall with {direct = true, keepHeight = not onWater} (the fix requested from A3).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
cd "$OYR"/output/studio_cal/x8
python3 - <<'PY'
p='root/worlds/xeen/events/common/xeen_common.lua'; s=open(p).read()
a='    evt.MoveToMap(x, y, z, yaw, 0, 0, 0, 0, map)\nend'
if a in s:
    s=s.replace(a,'    evt.MoveToMap(x, y, z, yaw, 0, 0, 0, 0, map, {direct = true, keepHeight = not onWater})\nend')
    open(p,'w').write(s); print('patched')
else:
    print('skyFall already passes options (or changed):', 'keepHeight' in s)
PY

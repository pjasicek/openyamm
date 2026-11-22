#!/bin/bash
# Pass 2: fmt, validate and build against the play root's assets (the generated textures live only there), install
# into this pass's private root (a hard-link copy of output/studio_play/xeen_root; install writes new files).
set -e
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd03/L4
X=$R/output/studio_cal/xd03/pass2
B=${1:-build}
cd $R
$O fmt $L >/dev/null
$O validate $L --assets output/studio_play/xeen_root
$O build $L --assets output/studio_play/xeen_root --out $X/$B > $X/$B.log 2>&1 || { cat $X/$B.log; exit 1; }
grep -v "is named" $X/$B.log | cut -c1-260 || true
$O install $L --build $X/$B --root $X/root >/dev/null
echo installed

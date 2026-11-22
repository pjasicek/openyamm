#!/bin/bash
# Pass 3: fmt, validate and build against the play root's assets (the generated textures live only there), install
# into this pass's private root (a hard-link copy of output/studio_play/xeen_root; install writes new files).
set -e
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd01/L4
X=$R/output/studio_cal/xd01/pass3
cd $R
$O fmt $L >/dev/null
$O validate $L --assets output/studio_play/xeen_root
$O build $L --assets output/studio_play/xeen_root --out $X/build 2>&1 | grep -v "is named" | cut -c1-220 || true
$O install $L --build $X/build --root $X/root >/dev/null
echo installed

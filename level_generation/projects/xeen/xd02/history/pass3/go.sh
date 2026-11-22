#!/bin/bash
# Pass 3: fmt, validate, build against the play root's assets, install into this pass's private root (a hard-link copy
# of output/studio_play/xeen_root; install writes new files by rename). Usage: go.sh [build dir name, default build]
set -e
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd02/L4
X=$R/output/studio_cal/xd02/pass3
B=$X/${1:-build}
cd $R
$O fmt $L >/dev/null
$O validate $L --assets output/studio_play/xeen_root
$O build $L --assets output/studio_play/xeen_root --out $B 2>&1 | grep -v "is named" | cut -c1-300 || true
$O install $L --build $B --root $X/root >/dev/null
echo installed $B

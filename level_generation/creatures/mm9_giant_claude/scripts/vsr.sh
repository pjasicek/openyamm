#!/bin/bash
# vs.sh with retries (the viewer can time out under load), one Chrome at a time. Args as vs.sh
for i in 1 2 3 4; do r=$(timeout 800 scripts/vs.sh "$@"); case "$r" in SHOTS*) echo "$r"; exit 0;; esac; done; echo FAILED "$r"

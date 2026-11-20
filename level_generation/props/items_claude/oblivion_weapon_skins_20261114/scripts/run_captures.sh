#!/bin/sh
# In-game captures for template:place pairs, PARALLEL (default 4) at a time. Usage: run_captures.sh <tag> <pair>...
cd "$(dirname "$0")/.." || exit 1
TAG=$1; shift
for j in "$@"; do echo "$j"; done | xargs -P "${PARALLEL:-4}" -I{} sh -c 'scripts/run_ingame.sh ${1%:*} ${1#*:} '"$TAG" _ {}

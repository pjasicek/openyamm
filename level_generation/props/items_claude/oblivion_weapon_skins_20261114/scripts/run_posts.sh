#!/bin/sh
# post.py skin for template:tier:job triples, PARALLEL (default 6) at a time.
cd "$(dirname "$0")/.." || exit 1
for j in "$@"; do echo "$j"; done | xargs -P "${PARALLEL:-6}" -I{} sh -c 'IFS=:; set -- $1; python3 scripts/post.py skin $1 $2 $3 > work/post_$1_t$2.log 2>&1; echo "$1 $2 $3 exit $?"; grep "^SKIN" work/post_$1_t$2.log | cut -c1-230' _ {}

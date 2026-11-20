#!/bin/bash
# Runs the MAW balance model for every difficulty/mode configuration and writes one CSV.
LUA=${LUA:-lua}
ROOT=${ROOT:-/home/pjasicek/github/Maw-Mod-MMMerge}
OUT=$1; BUFF=${2:-mapping}; ROUND=${3:-trunc}
echo "config,austerity,party_count,$($LUA harness.lua $ROOT 100 0 0 0 0 0 5 $BUFF $ROUND 1 | head -1)" > $OUT
# name bolster mode insanity madness trueNightmare austerity
CONFIGS="easy_normal:50:0:0:0:0:0 unreachable70:70:0:0:0:0:0 maw:100:0:0:0:0:0 hard:150:0:0:0:0:0 hell:200:0:0:0:0:0
nightmare:300:0:0:0:1:0 doom:600:2:0:0:0:0 insanity:600:2:1:0:0:0 madness:600:2:1:1:0:0
aust_easy_normal:50:8:0:0:0:1 aust_unreachable70:70:8:0:0:0:1 aust_maw:100:8:0:0:0:1 aust_hard:150:8:0:0:0:1
aust_hell:200:8:0:0:0:1 aust_nightmare:300:8:0:0:1:1"
for c in $CONFIGS; do
  IFS=: read name b m i md tn a <<< "$c"
  for p in 5 1; do
    $LUA harness.lua $ROOT $b $m $i $md $tn $a $p $BUFF $ROUND | tail -n +2 | sed "s/^/$name,$a,$p,/" >> $OUT
  done
done

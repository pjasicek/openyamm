#!/bin/bash
# each tier's neck: front, quarter, side, back
for t in a b c; do scripts/vs.sh zombie_$t review/neck ${t}_f:Standing:0:front:body:0.05,1.52,0.62:0,1.53,0.05 ${t}_q:Standing:0:front:body:-0.42,1.56,0.48:0,1.53,0.03 ${t}_s:Standing:0:front:body:-0.62,1.54,0.1:0,1.53,0.03 ${t}_b:Standing:0:front:body:0.05,1.58,-0.55:0,1.53,0.03; done

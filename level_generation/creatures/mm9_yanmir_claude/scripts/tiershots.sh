#!/bin/bash
# tier sheet shots with cameras for a 2.56 m body. Project folder.
for t in a b c; do scripts/vsr.sh bf_$t review/shots s${t}_front:Standing:0.5:front:body:0,1.25,5.6:0,1.25,0.25 s${t}_back:Standing:0.5:front:body:0,1.25,-5.2:0,1.25,0.25 s${t}_quarter:Standing:0.5:front:body:-3,1.4,4.8:0,1.25,0.25 s${t}_fh:Standing:0.5:front:body:0,2.1,1.9:0,2.1,0.3 s${t}_qh:Standing:0.5:front:body:-0.9,2.1,1.6:0,2.1,0.3; done

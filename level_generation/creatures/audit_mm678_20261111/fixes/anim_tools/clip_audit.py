#!/usr/bin/env python3
"""Region bad shares of chosen clips: clip_audit.py <glb> <clip> ...  (motion_audit thresholds)."""
import sys, numpy as np
sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared')
import motion_audit
a=motion_audit.Audit(sys.argv[1])
for c in sys.argv[2:]:
    r,_=a.clip(c,30)
    print(c, {k:v['bad_pct'] for k,v in r['deform'].items()}, 'hot',r['hotspot'], 'pop',r.get('loop_pop'), 'inside', r['hand_inside_pct'])

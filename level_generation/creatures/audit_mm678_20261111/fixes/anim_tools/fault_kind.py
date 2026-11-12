#!/usr/bin/env python3
"""Stretch / squash / fold shares of one region over a clip: fault_kind.py <glb> <clip> [region]."""
import sys
sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared')
import motion_audit, numpy as np
a=motion_audit.Audit(sys.argv[1]); clip=sys.argv[2]; reg=sys.argv[3] if len(sys.argv)>3 else 'cloth'
ri=motion_audit.REGIONS.index(reg)
tot=a.rest_area[(a.tri_region==ri)&a.valid].sum()
ts=a.model.clip_times(clip); 
for t in np.linspace(ts[0],ts[-1],9):
    posed,scale,pal,w=a.pose(clip,t)
    s1,s2,fold,live=a.deformation(posed,scale,pal)
    c=(a.tri_region==ri)&live
    print('%.2f stretch %.1f squash %.1f fold %.1f any %.1f'%(t, 100*a.rest_area[c&(s1>1.6)].sum()/tot, 100*a.rest_area[c&(s2<0.55)].sum()/tot, 100*a.rest_area[c&fold].sum()/tot, 100*a.rest_area[c&((s1>1.6)|(s2<0.55)|fold)].sum()/tot))

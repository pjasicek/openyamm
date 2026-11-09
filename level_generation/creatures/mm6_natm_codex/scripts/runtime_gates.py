"""Shared runtime runner, with a float32-endpoint correction and explicit distal-twist wrist measurement.
No shared files are changed. Raw hinge-relative wrist roll is retained alongside the actual distal-skin frame.
"""
import sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
def grid(start,end,hz):
 start,end=float(start),float(end);tol=max(1e-7,abs(end)*np.finfo(np.float32).eps*2)
 values=np.arange(start,end,1/hz,dtype=float);values=np.r_[values[values<end-tol],end]
 if hz==48 and start==0 and len(values)==2:values=np.array([start,(start+end)/2,end])
 return values
assert len(grid(0,np.float32(76/48),48))==77
assert np.diff(grid(0,np.float32(76/48),48)).min()>.0208
assert len(grid(0,np.float32(1/48),48))==3
G.sample_grid=grid
original=G.bone_gates
def bones(glb,pose,times,clip,config,report,props):
 original(glb,pose,times,clip,config,report,props)
 for side in 'LR':
  fn=glb.names[f'B_{side}_ForearmTwist'];hn=glb.names[f'B_{side}_Hand'];fingers=[glb.names[f'B_{side}_Finger{i}']for i in range(5)]
  fr=glb.rest[fn,:3,:3];hr=glb.rest[hn,:3,:3];fp=pose[:,fn,:3,:3];hp=pose[:,hn,:3,:3];neutral=fp@fr.T@hr
  rel=np.swapaxes(neutral,-1,-2)@hp;axis=hr.T@G.unit(np.mean(glb.rest[fingers,:3,3],axis=0)-glb.rest[hn,:3,3]);swing,roll=G.swing_twist(rel,axis)
  report.series('distal_wrist_roll_deg',abs(roll),times,45.,clip=clip,lod='rig',region=side,unit_name='deg',detail='Hand relative to the actual distal forearm deformation frame')
G.bone_gates=bones
sys.argv=['gates','--',str(P/'export/mm6_natm.glb'),'--config',str(P/'gates.json'),'--out',str(P/'review/runtime_gates')]
G.main()

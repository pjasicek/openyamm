import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
cfg=json.loads((P/'gates.json').read_text());g=G.Glb(P/'export/mm6_mfp.glb');data=json.loads((P/'review/round1/shared_gates_v5/gates.json').read_text());clips={n:a for n,a,s,e in g.clips()}
for clip in ['Attack','Hit']:
 row=next(r for r in data['gates']if r['clip']==clip and r['gate']=='angular_acceleration_deg_s2'and r['status']=='FAIL');t=row['time_s'];pose=g.pose(clips[clip],np.array([t-1/48,t,t+1/48]));print('ACC_CHAIN',clip,t)
 for name in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_L_Clavicle','B_L_UpperArm','B_L_Forearm']:
  if name not in g.names:continue
  r=pose[:,g.names[name],:3,:3];rv=G.rotation_vector(r[1:]@np.swapaxes(r[:-1],-1,-2));print(name,np.degrees(rv).tolist())
for m in G.load_meshes(g):
 if m.label!='PeasantF3/colour0':continue
 G.configure_mesh(m,cfg,G.Report(cfg))
 for clip in ['Hit','Death','Walking']:
  for row in [x for x in data['gates']if x['gate']=='cloth_penetration_mm'and x['clip']==clip and x['lod']==m.label and x['status']=='FAIL']:
   surface=next(x for x in m.cloth if x[0]==row['region']);ids=np.flatnonzero(surface[2]);vi=ids[row['detail']['sample_vertex']];print('CLOTH',clip,row['region'],row['worst'],m.rest[vi].tolist())

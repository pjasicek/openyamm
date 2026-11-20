"""Rigid plates follow one segment; flexible leg shells bend around measured knee centres."""
import bpy,sys,json
import numpy as np
from pathlib import Path
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src);body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
p=Path(__file__).resolve().parents[1];J=json.loads((p/'work/joints_final.json').read_text())['joints']
names=[g.name for g in body.vertex_groups]
def set_w(v,w):
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 total=sum(w.values());assert total>.99
 for n,a in w.items():
  if a>1e-6:body.vertex_groups[n].add([v.index],float(a/total),'REPLACE')
def blend(a,b,t):
 t=float(np.clip(t,0,1));t=t*t*(3-2*t);return {a:1-t,b:t}
rigid={1:'B_Head',8:'B_Head',11:'B_Head',13:'B_Head',19:'B_Head',24:'B_Head',25:'B_Head',29:'B_Head',30:'B_Head',3:'B_Spine2',26:'B_Spine2'}
for side,ids in [('L',[9,14,16,18,20,22,28,32]),('R',[10,12,15,17,21,23,27,31])]:
 for i in ids:rigid[i]=f'B_{side}_'+('ForearmTwist' if i in [9,10,31,32] else 'Calf' if i in [15,16,27,28] else 'UpperArm')
for v in body.data.vertices:
 piece=body.data.attributes['piece'].data[v.index].value;x,y,z=v.co
 if piece in rigid:set_w(v,{rigid[piece]:1})
 elif piece in [4,5]:set_w(v,{'B_L_Hand' if piece==4 else 'B_R_Hand':1})
 elif piece in [0,2]:
  side='L' if x>0 else 'R';pre='B_'+side+'_';knee=J[side+'_Calf'][2];hip=J[side+'_Thigh'][2];ankle=J[side+'_Foot'][2]
  if z>.94:w=blend('B_Pelvis','B_Spine',(z-.94)/.12)
  elif z>hip-.075:w=blend(pre+'Thigh','B_Pelvis',(z-(hip-.075))/.15)
  elif z>knee-.08:w=blend(pre+'Calf',pre+'Thigh',(z-(knee-.08))/.16)
  elif z>ankle-.015:w=blend(pre+'Foot',pre+'Calf',(z-(ankle-.015))/.09)
  else:w=blend(pre+'Foot',pre+'Toe0',(-y-.13)/.075)
  set_w(v,w)
for v in body.data.vertices:assert abs(sum(g.weight for g in v.groups)-1)<.001
bpy.ops.wm.save_as_mainfile(filepath=out)

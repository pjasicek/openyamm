"""Keep disconnected Merchant surfaces on their anatomical owners before finger weights."""
import bpy,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=str(P/(args[0] if args else 'work/pilot_raw.blend')));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
pv=np.array([a.value for a in me.attributes['piece'].data]);gn={g.index:g.name for g in body.vertex_groups}
def put(v,w):
 total=sum(w.values());assert total>0
 for e in v.groups[:]:body.vertex_groups[e.group].remove([v.index])
 for n,x in w.items():
  if x>1e-8:body.vertex_groups[n].add([v.index],float(x/total),'REPLACE')
for v in me.vertices:
 part=int(pv[v.index]);s='L' if v.co.x>0 else 'R';w={gn[g.group]:g.weight for g in v.groups}
 if part in (0,11,14,15):w={'B_Head':1}
 elif part in (10,12,13,16,17):w={'B_Pelvis':1}
 elif part in (3,4):
  wr=rig.data.bones[f'B_{s}_Hand'].head_local;el=rig.data.bones[f'B_{s}_Forearm'].head_local;d=(wr-el).normalized();t=float(np.clip(((v.co-wr).dot(d)+.012)/.025,0,1));w={f'B_{s}_Hand':t,f'B_{s}_Forearm':1-t}
 elif part in (6,7):
  t=float(np.clip((v.co.z-.15)/.12,0,1));w={f'B_{s}_Foot':1-t,f'B_{s}_Calf':t}
 elif part==2:
  h=float(np.clip((.88-v.co.z)/.5,0,.8));left=float(np.clip(.5+v.co.x/.48,0,1));w={'B_Pelvis':1-h,'B_L_Thigh':h*left,'B_R_Thigh':h*(1-left)}
 elif part==1:
  for n in list(w):
   if any(k in n for k in ('Thigh','Calf','Hand','Forearm','Head')):w['B_Spine2']=w.get('B_Spine2',0)+w.pop(n)
  for n in list(w):
   if 'UpperArm'in n or 'Clavicle'in n:
    keep=float(np.clip((abs(v.co.x)-.14)/.11,0,1)*np.clip((v.co.z-1.15)/.15,0,1));move=w[n]*(1-keep);w[n]-=move;w['B_Spine2']=w.get('B_Spine2',0)+move
 elif part in (8,9):
  for n in list(w):
   if any(k in n for k in ('Thigh','Calf','Foot','Head','Finger')) or (n.startswith('B_R_') if s=='L' else n.startswith('B_L_')):
    w[f'B_{s}_Forearm']=w.get(f'B_{s}_Forearm',0)+w.pop(n)
 put(v,w)
# Sleeve roots lie under the shoulder shell and must share its deformation across the overlap.
from mathutils.kdtree import KDTree
ids=np.where(pv==1)[0];kd=KDTree(len(ids))
for i in ids:kd.insert(me.vertices[int(i)].co,int(i))
kd.balance()
for v in me.vertices:
 if pv[v.index] not in (8,9):continue
 s='L' if v.co.x>0 else 'R';sh=rig.data.bones[f'B_{s}_UpperArm'].head_local;el=rig.data.bones[f'B_{s}_Forearm'].head_local;d=(el-sh).normalized();t=(v.co-sh).dot(d)
 blend=float(np.clip((.12-t)/.10,0,1))
 if blend>0:
  _,j,dist=kd.find(v.co);w={gn[e.group]:e.weight*(1-blend)for e in v.groups}
  for e in me.vertices[j].groups:w[gn[e.group]]=w.get(gn[e.group],0)+e.weight*blend
  put(v,w)
assert all(abs(sum(e.weight for e in v.groups)-1)<1e-5 for v in me.vertices)
bpy.ops.wm.save_as_mainfile(filepath=str(P/(args[1] if args else 'work/pilot_weights.blend')))

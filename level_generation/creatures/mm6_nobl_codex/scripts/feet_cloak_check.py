"""Measure the shipped boot soles and cloak overlap, including between-frame skinning."""
import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];out=p/'review/feet_cloak_20261011'
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v15.blend'));o=bpy.data.objects['Body']
pv=np.zeros(len(o.data.vertices),np.int32);o.data.attributes['piece'].data.foreach_get('value',pv)
co=np.array([v.co[:] for v in o.data.vertices]);kd=KDTree(len(co))
for i,c in enumerate(co):kd.insert(Vector(c),i)
kd.balance()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_nobl_lod0.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');o=next(o for o in bpy.data.objects if o.type=='MESH' and o.parent==r);sc=bpy.context.scene
mapping=np.array([kd.find(o.matrix_world@v.co)[1] for v in o.data.vertices]);rest=co[mapping];pieces=pv[mapping]
soles={s:np.flatnonzero((pieces==2)&(rest[:,2]<.001)&(rest[:,0]*(1 if s=='L' else -1)>0)) for s in 'LR'}
boot={s:np.flatnonzero((pieces==2)&(rest[:,2]<.13)&(rest[:,0]*(1 if s=='L' else -1)>0)) for s in 'LR'}
result={};failures=[]
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frames=[];prev=None;motion=[]
 for f in np.arange(a.frame_range[0],a.frame_range[1]+1e-5,sc.render.fps/240):
  sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
  X=np.array([tuple(o.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear()
  row={}
  for s in 'LR':
   P=X[soles[s]];center=P.mean(0);_,_,V=np.linalg.svd(P-center,full_matrices=False);normal=V[-1];normal*=np.sign(normal[2])
   D=np.linalg.norm(X[boot[s]][:,None]-X[boot[s]][None,:],axis=2)
   D0=np.linalg.norm(rest[boot[s]][:,None]-rest[boot[s]][None,:],axis=2)
   row[s]={'sole_height_min_mm':float(P[:,2].min()*1000),'sole_height_max_mm':float(P[:,2].max()*1000),'tilt_degrees':float(np.degrees(np.arccos(np.clip(normal[2],-1,1)))),'boot_shape_error_mm':float(abs(D-D0).max()*1000)}
  if prev is not None:motion.append(float(np.linalg.norm(X-prev,axis=1).max()*1000))
  prev=X;frames.append(row)
 summary={s:{k:max(row[s][k] for row in frames) for k in frames[0][s]} for s in 'LR'}
 summary['minimum_floor_mm']=min(row[s]['sole_height_min_mm'] for row in frames for s in 'LR')
 summary['maximum_frame_motion_mm_at_240fps']=max(motion)
 result[a.name]={'summary':summary,'frames':frames}
 print('BOOT_GATE',a.name,json.dumps(summary),flush=True)
 for s in 'LR':assert summary[s]['boot_shape_error_mm']<.1,(a.name,s,summary[s])
 if a.name in ['Standing','Fidget']:
  for s in 'LR':
   
   if summary[s]['tilt_degrees']>=.2:failures.append((a.name,s,'tilt',summary[s]))
   
   if summary[s]['sole_height_max_mm']>=2.0:failures.append((a.name,s,'height',summary[s]))
 if a.name not in ['Death','Dead'] and summary['minimum_floor_mm']<=-.8:failures.append((a.name,'floor',summary['minimum_floor_mm']))
(out/'boot_gate.json').write_text(json.dumps(result,indent=1))

assert not failures,failures

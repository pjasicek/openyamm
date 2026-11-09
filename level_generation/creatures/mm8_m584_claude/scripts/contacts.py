"""Closed-skin contacts and floor bounds at half frames; feather layers use body proximity."""
from pathlib import Path
import bpy,json,os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/os.environ.get('RAVEN_CONTACT_BLEND','rig_final.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['PolearmMesh'];me=body.data
names=[g.name for g in body.vertex_groups]
weights=np.zeros((len(me.vertices),len(names)))
for v in me.vertices:
 for e in v.groups:weights[v.index,e.group]=e.weight
rest=np.array([tuple(v.co) for v in me.vertices]);piece=np.array([a.value for a in me.attributes['piece'].data])
def weight(terms,side=''):
 return weights[:,[i for i,n in enumerate(names) if (not side or n.startswith(f'B_{side}_')) and any(t in n for t in terms)]].sum(1)
parts={}
for side in 'LR':
 exclude=weight(('Clavicle','UpperArm','Forearm','Hand','Finger'),side)>.15
 for label,terms in [('forearm',('Forearm',)),('hand',('Hand','Finger'))]:
  parts[side+'_'+label]=(np.where(weight(terms,side)>.5)[0],exclude)
parts['wings']=(np.where((piece>=1000)&(abs(rest[:,0])>.42))[0],np.zeros(len(rest),bool))
skin=[tuple(f.vertices) for f in me.polygons if piece[f.vertices[0]] in (0,1)]
face_sets={key:[f for f in skin if all(not exclude[i] for i in f)] for key,(_,exclude) in parts.items()}
directions=[Vector(v) for v in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))]
def inside(tree,p):
 hits=exits=0
 for d in directions:
  loc,n,_,_=tree.ray_cast(p+d*.0001,d,4)
  if loc is not None:hits+=1;exits+=int(n.dot(d)>0)
 return hits>=4 and hits==exits
def evaluated(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
 points=np.array([tuple(ob.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return points
report={}
for a in bpy.data.actions:
 if not a.use_fake_user or os.environ.get('RAVEN_CHECK_CLIP',a.name)!=a.name:continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst={};ground=[]
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)));points=evaluated(body)
  trees={k:BVHTree.FromPolygons(points.tolist(),faces) for k,faces in face_sets.items()}
  for key,(ids,_) in parts.items():
   tree=trees[key]
   for i in ids:
    p=Vector(points[i]);hit,normal,face,d=tree.find_nearest(p,.12)
    if hit is not None and d>.002 and (p-hit).dot(normal)<-.7*d and inside(tree,p):
     if d>worst.get(key,{}).get('depth_m',0):worst[key]={'frame':float(f),'depth_m':float(d),'vertex':int(i)}
  tree=trees['wings'];pp=evaluated(prop)
  for i,xyz in enumerate(pp):
   p=Vector(xyz);hit,normal,face,d=tree.find_nearest(p,.15)
   if hit is not None and d>.002 and (p-hit).dot(normal)<-.7*d and inside(tree,p):
    if d>worst.get('polearm',{}).get('depth_m',0):worst['polearm']={'frame':float(f),'depth_m':float(d),'vertex':i}
  ground.append({'frame':float(f),'body_min_z':float(points[piece<1000,2].min()),'wings_min_z':float(points[piece>=1000,2].min()),'prop_min_z':float(pp[:,2].min())})
 report[a.name]={'contacts':worst,'floor_end':ground[-1],'floor_min':{k:min(x[k] for x in ground) for k in ('body_min_z','wings_min_z','prop_min_z')}}
 print('CONTACT',a.name,report[a.name],flush=True)
Path(os.environ.get('RAVEN_CONTACT_REPORT',str(P/'work/contacts_final.json'))).write_text(json.dumps(report,indent=2)+'\n')

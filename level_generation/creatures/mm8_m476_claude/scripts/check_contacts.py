"""Half-frame surface penetration diagnostic for the assembled club and both arms."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_club.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];club=bpy.data.objects['SkullClub'];sc=bpy.context.scene
names=[g.name for g in body.vertex_groups];co=np.array([tuple(v.co) for v in body.data.vertices]);piece=np.array([v.value for v in body.data.attributes['piece'].data]);faces=[tuple(f.vertices) for f in body.data.polygons]
W=np.zeros((len(co),len(names)))
for v in body.data.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
part={}
for sd in 'LR':
 for label,keys in [('hand',['Hand','Finger']),('forearm',['Forearm'])]:
  part[f'{sd}_{label}']=W[:,[i for i,n in enumerate(names) if n.startswith(f'B_{sd}_') and any(k in n for k in keys)]].sum(1)>.5
trunkfaces=[f for f in faces if piece[f[0]] in (0,1)]
clubfaces=[f for f in faces if not any(part['L_hand'][v] for v in f)]
def posed(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([tuple(o.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return P
report={}
for an in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 a=bpy.data.actions[an];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst={}
 for fr in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(fr),subframe=float(fr-int(fr)));P=posed(body);C=posed(club)
  trunk=BVHTree.FromPolygons(P.tolist(),trunkfaces);full=BVHTree.FromPolygons(P.tolist(),clubfaces)
  for label,pts in [(n,P[m]) for n,m in part.items()]+[('club',C)]:
   tree=full if label=='club' else trunk
   for j,q in enumerate(pts):
    loc,nrm,idx,dist=tree.find_nearest(Vector(q),.12)
    if loc is not None and dist>.003 and (Vector(q)-loc).dot(nrm)<-.7*dist and dist>worst.get(label,{}).get('depth_m',0):
     worst[label]={'depth_m':float(dist),'frame':float(fr),'sample':j,'position':q.tolist()}
 report[an]=worst;print('CONTACTS',an,{k:(round(v['depth_m']*100,2),v['frame']) for k,v in worst.items()},flush=True)
(p/'work/contacts_v1.json').write_text(json.dumps(report,indent=2))

"""Half-frame surface contacts for the Mage's actual wand, arms and garment panels."""
from pathlib import Path
import bpy,sys,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilots_fitted.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];wand=bpy.data.objects['Wand'];me=body.data
pv=np.array([x.value for x in me.attributes['piece'].data]);faces=[tuple(f.vertices) for f in me.polygons]
names=[g.name for g in body.vertex_groups];weights=np.zeros((len(me.vertices),len(names)))
for v in me.vertices:
 for e in v.groups:weights[v.index,e.group]=e.weight
def mask(side,parts,threshold):
 ids=[i for i,n in enumerate(names) if n.startswith(f'B_{side}_') and any(t in n for t in parts)]
 return weights[:,ids].sum(1)>threshold
arm={s:mask(s,['Clavicle','UpperArm','Forearm','Hand','Finger'],.2) for s in 'LR'}
hands={s:mask(s,['Forearm','Hand','Finger'],.5) for s in 'LR'}
skin=np.isin(pv,[0,2,3,4])
skin_faces=[f for f in faces if all(skin[i] for i in f)]
cape=np.array([x.value for x in me.attributes['cape'].data])>0
loin=np.array([x.value for x in me.attributes['loin'].data])>0
def coordinates(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([tuple(obj.matrix_world@x.co) for x in m.vertices]);ev.to_mesh_clear();return v
def depth(tree,points):
 best=(0,None)
 for i,pt in enumerate(points):
  loc,n,face,d=tree.find_nearest(Vector(pt),.05)
  if loc is not None and d>best[0] and (Vector(pt)-loc).dot(n)<-.7*d:best=(d,pt.tolist())
 return best
report={'method':'Local signed closest-surface test on skin pieces only, excluding the sampled arm; open garments tested against skin, actual complete wand sampled. Near-boundary false positives require visual inspection.','clips':{}}
for name in ['Standing','Walking','Running','Attack']:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];worst={}
 for frame in np.arange(0,act.frame_range[1]+1e-6,.5):
  bpy.context.scene.frame_set(int(frame),subframe=float(frame-int(frame)));P=coordinates(body);Q=coordinates(wand)
  for side in 'LR':
   fl=[f for f in skin_faces if not any(arm[side][i] for i in f)];tree=BVHTree.FromPolygons(P.tolist(),fl)
   groups={side+'_arm':P[hands[side]]}
   if side=='R':groups['wand']=Q
   for key,points in groups.items():
    d,pt=depth(tree,points)
    if d>worst.get(key,{}).get('depth_m',0):worst[key]={'depth_m':d,'frame':float(frame),'point':pt}
  tree=BVHTree.FromPolygons(P.tolist(),skin_faces)
  for key,flag in [('cape',cape),('loin',loin)]:
   d,pt=depth(tree,P[flag])
   if d>worst.get(key,{}).get('depth_m',0):worst[key]={'depth_m':d,'frame':float(frame),'point':pt}
 report['clips'][name]=worst;print('MAGE_CONTACTS',name,worst,flush=True)
(p/'review/pilot_contacts.json').write_text(json.dumps(report,indent=2)+'\n')

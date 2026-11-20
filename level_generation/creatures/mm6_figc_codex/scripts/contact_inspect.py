import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups]
def posed(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[o.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return co
rows=[]
for name,f,part in [('Walking',12.5,'R'),('Death',33.125,'R'),('Death',36.875,'Axe'),('Death',71.25,'Shield')]:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(int(f),subframe=f%1);co=posed(body)
 if part=='R':
  own=[sum(e.weight for e in v.groups if names[e.group].startswith('B_R_') and any(k in names[e.group] for k in ['Clavicle','UpperArm','Forearm','Hand','Finger']))>.2 for v in me.vertices]
  ids=[v.index for v in me.vertices if sum(e.weight for e in v.groups if names[e.group].startswith('B_R_') and any(k in names[e.group] for k in ['Forearm','Hand','Finger']))>.5];pts=[co[i] for i in ids]
 else:
  side='R' if part=='Axe' else 'L';own=[sum(e.weight for e in v.groups if names[e.group].startswith('B_'+side+'_') and any(k in names[e.group] for k in ['Hand','Finger']))>.3 for v in me.vertices];pts=posed(bpy.data.objects[part]);ids=list(range(len(pts)))
 fs=[tuple(p.vertices) for p in me.polygons if not any(own[i] for i in p.vertices)];tree=BVHTree.FromPolygons(co,fs);hits=[]
 for i,p in zip(ids,pts):
  loc,n,fi,d=tree.find_nearest(p,.05)
  if loc is not None and (p-loc).dot(n)<-.707*d:hits.append((d,i,fi,tuple(p),tuple(loc),tuple(n),int(pv[fs[fi][0]])))
 hits.sort(reverse=True);rows.append([name,f,part,hits[:8]]);print('CONTACT',rows[-1],flush=True)
 sys.path.insert(0,str(P/'scripts'));import common
 common.workbench_clay(bpy.context.scene);lo,hi=common.world_bounds([body,bpy.data.objects['Axe'],bpy.data.objects['Shield']]);center=(lo+hi)*.5;common.render_views(str(P/f'review/contact_{name}_{part}'),center.z,2.2,views=['three_quarter','left'],resolution=(600,800),target=(center.x,center.y))
(P/'work/contact_details.json').write_text(json.dumps(rows,indent=2))

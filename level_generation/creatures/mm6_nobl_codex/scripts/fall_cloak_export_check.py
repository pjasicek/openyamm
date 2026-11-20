import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v12.blend'));o=bpy.data.objects['Body'];me=o.data
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv);co=np.array([v.co[:] for v in me.vertices])
kd=KDTree(len(co))
for i,c in enumerate(co):kd.insert(Vector(c),i)
kd.balance()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_nobl_runtime_lod0.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');o=next(o for o in bpy.data.objects if o.type=='MESH' and o.parent==r);sc=bpy.context.scene
idx=np.array([kd.find(o.matrix_world@v.co)[1] for v in o.data.vertices]);rest=co[idx];pieces=pv[idx]
faces=[tuple(f.vertices) for f in o.data.polygons if all(pieces[i]==0 for i in f.vertices) and np.mean(rest[list(f.vertices),2])<1.2]
boots=np.flatnonzero((pieces==2)&(rest[:,2]<.14));a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
report=[]
for t in np.arange(0,1.833334,1/120):
 f=t*sc.render.fps;sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();X=[o.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
 tree=BVHTree.FromPolygons(X,faces);worst=0
 for i in boots:
  v=X[int(i)];hit,n,k,d=tree.ray_cast(v+Vector((0,0,.7)),Vector((0,0,-1)),1.4)
  if hit is not None:worst=max(worst,v.z+.004-hit.z)
 report.append({'time':float(t),'clearance_deficit_mm':float(worst*1000)})
(p/'review/feet_cloak_20261011/fall_cloak_export_gate.json').write_text(json.dumps(report,indent=1))
print('EXPORTED_CLOAK_CLEARANCE',max(r['clearance_deficit_mm'] for r in report),'mm')
assert max(r['clearance_deficit_mm'] for r in report)<1

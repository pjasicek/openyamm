import json,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Quaternion,Vector
from mathutils.bvhtree import BVHTree
P=Path('level_generation/creatures/hes_bulwark_codex').resolve();bpy.ops.wm.open_mainfile(filepath=str(P/'work/bulwark_final_rig.blend'))
rig=bpy.data.objects['BulwarkRig'];body=bpy.data.objects['Bulwark'];cables=bpy.data.objects['Bulwark_Cables'];scene=bpy.context.scene
names={g.index:g.name for g in body.vertex_groups}
def owner(v):return names[max(v.groups,key=lambda g:g.weight).group]
owners=[owner(v) for v in body.data.vertices]
groups={'lower':[],'chassis':[],'head_clear':[],'barrels':[]}
for f in body.data.polygons:
 ns={owners[v] for v in f.vertices};vs=list(f.vertices)
 if all(n.startswith(('B_LF','B_RF','B_LH','B_RH')) for n in ns):groups['lower'].append(vs)
 if ns=={'B_Chassis'}:groups['chassis'].append(vs)
 if ns=={'B_Barrel'} and min(body.data.vertices[v].co.z for v in vs)>2.1:groups['head_clear'].append(vs)
 if all(n.startswith('B_Recoil') for n in ns) and f.center.y<-.7:groups['barrels'].append(vs)
cf=[list(f.vertices) for f in cables.data.polygons]
def hits():
 dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh();co=[v.co.copy() for v in me.vertices];trees={k:BVHTree.FromPolygons(co,v) for k,v in groups.items()};ev.to_mesh_clear()
 ev=cables.evaluated_get(dg);me=ev.to_mesh();c=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],cf);ev.to_mesh_clear()
 return {'cable_legs':len(c.overlap(trees['lower'])),'cable_chassis':len(c.overlap(trees['chassis'])),'head_above_bearing_chassis':len(trees['head_clear'].overlap(trees['chassis'])),'exposed_barrels_chassis':len(trees['barrels'].overlap(trees['chassis']))}
report={'head_bearing_exclusion':'head faces with any rest vertex at z <= 2.1 m','clips':{},'look':{}}
for a in bpy.data.actions:
 if not a.slots:continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst={k:0 for k in hits()}
 for frame in np.arange(0,round(a.frame_range[1])+.01,.5):
  scene.frame_set(int(frame),subframe=float(frame%1));h=hits();worst={k:max(v,h[k]) for k,v in worst.items()}
 report['clips'][a.name]=worst
rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis.identity()
pb=rig.pose.bones['B_Barrel'];pb.rotation_mode='QUATERNION';axis=pb.bone.matrix_local.to_3x3().inverted()@Vector((1,0,0))
for pitch in range(-15,13):
 pb.rotation_quaternion=Quaternion(axis.normalized(),math.radians(-pitch));bpy.context.view_layer.update();report['look'][str(pitch)]=hits()
(P/'review/geometry/final_contacts.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
assert not any(v for row in report['clips'].values() for v in row.values())
assert not any(v for row in report['look'].values() for v in row.values())

import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];prop=bpy.data.objects['BowAsset'];sc=bpy.context.scene;g=Matrix(json.loads((P/'work/round2_bow_binding.json').read_text())['hand_local']);names={x.index:x.name for x in b.vertex_groups}
keep=[sum(g.weight for g in v.groups if 'Hand'in names[g.group]or'Finger'in names[g.group])<=.5 for v in b.data.vertices];faces=[tuple(f.vertices)for f in b.data.polygons if all(keep[i]for i in f.vertices)]
prop_ids=[v.index for v in prop.data.vertices if any(prop.vertex_groups[g.group].name=='Bow'and g.weight>.9 for g in v.groups)]
def posed(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[x.co.copy()for x in m.vertices];ev.to_mesh_clear();return v
results=[]
for tilt in [0,9]:
 for angle in range(-180,181,15):
  z=Vector((math.sin(math.radians(tilt)),0,math.cos(math.radians(tilt))));y=Vector((-math.sin(math.radians(angle)),math.cos(math.radians(angle)),0));y=(y-z*y.dot(z)).normalized();x=y.cross(z);BR=Matrix((x,y,z)).transposed();R=BR@g.to_3x3().inverted();worst=0
  for clip in ['Standing','Walking']:
   a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
   for frame in ([0,30]if clip=='Standing'else range(0,25,4)):
    sc.frame_set(frame);H=r.pose.bones['B_L_Hand'];m=R.to_4x4();m.translation=H.head;H.matrix=m;bpy.context.view_layer.update();r.pose.bones['Bow'].matrix=H.matrix@g;bpy.context.view_layer.update();v=posed(b);q=posed(prop);tree=BVHTree.FromPolygons(v,faces)
    for i in prop_ids:
     hit,n,index,d=tree.find_nearest(q[i],.05)
     if hit is not None and (q[i]-hit).dot(n)<-.7*d:worst=max(worst,d)
  inward=r.pose.bones['B_L_Thigh'].head-r.pose.bones['Bow'].head;inward.z=0
  results.append({'tilt':tilt,'angle':angle,'penetration_mm':worst*1000,'inward_dot':y.dot(inward.normalized())});print('CARRY_SEARCH',results[-1],flush=True)
(P/'review/round2/carry_plane_search.json').write_text(json.dumps(results,indent=2))

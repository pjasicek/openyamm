import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Quaternion,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_native.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['Crossbow'];sc=bpy.context.scene
a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(37)
pose={b.name:b.matrix_basis.copy() for b in rig.pose.bones};rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=pose[b.name]
bpy.context.view_layer.update()
pv=np.array([x.value for x in body.data.attributes['piece'].data]);fing=np.array([x.value for x in body.data.attributes['finger'].data])
def co(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([tuple(o.matrix_world@x.co) for x in m.vertices]);ev.to_mesh_clear();return v
weapon=co(prop);adj=[set() for _ in weapon]
for e in prop.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
components=[];seen=set()
for i in range(len(weapon)):
 if i in seen:continue
 todo=[i];part=set()
 while todo:
  v=todo.pop()
  if v in part:continue
  part.add(v);todo.extend(adj[v]-part)
 seen|=part
 faces=[tuple(p.vertices) for p in prop.data.polygons if p.vertices[0] in part]
 pts=weapon[list(part)];components.append((BVHTree.FromPolygons(weapon.tolist(),faces),pts.min(0),pts.max(0)))
G=json.loads((P/'work/grip_pose_L.json').read_text());out={}
for amount in (.65,.8,1):
 for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion().slerp(Quaternion(q),amount)
 bpy.context.view_layer.update();pts=co(body);worst={}
 for s,piece in [('L',7),('R',8)]:
  for ci,(tree,lo,hi) in enumerate(components):
   ids=np.where((pv==piece)&np.all(pts>=lo,axis=1)&np.all(pts<=hi,axis=1))[0]
   for i in ids:
    loc,norm,face,d=tree.find_nearest(Vector(pts[i]))
    if (Vector(pts[i])-loc).dot(norm)<-1e-5 and d>worst.get(s,{}).get('depth_m',0):worst[s]={'component':ci,'depth_m':d,'vertex':int(i),'finger':int(fing[i]),'point':pts[i].tolist()}
 out[amount]=worst
 common.workbench_clay(sc)
 center=Vector(pts[pv==7].mean(0));H=rig.pose.bones['B_L_Hand'].matrix.to_3x3();axis=H@Vector(G['handle_axis_hand_local'])
 cam=common.ortho_camera('grip_camera',center+axis*2,(0,0,0),.28);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-axis).to_track_quat('-Z','Y');sc.camera=cam
 sc.render.resolution_x=sc.render.resolution_y=600;sc.render.filepath=str(P/f'review/grip_amount_{amount}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
print('PROP GRIP INTERIORS',out,flush=True);(P/'work/grip_interiors.json').write_text(json.dumps(out,indent=2))

"""Inspect the actual prop and both hands, rather than the grip solver's cylinder proxy."""
import os,bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/os.environ.get('M632_CHECK_BLEND','work/motion_native.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['Crossbow'];sc=bpy.context.scene
piece=np.array([x.value for x in body.data.attributes['piece'].data]);finger=np.array([x.value for x in body.data.attributes['finger'].data])
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[tuple(o.matrix_world@v.co) for v in m.vertices];ev.to_mesh_clear();return np.array(co)
report={};common.workbench_clay(sc)
for name,frame in [('Standing',0),('Attack',round(1.25*sc.render.fps)),('Attack',round(1.38*sc.render.fps))]:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(frame)
 pts=coords(body);weapon=coords(prop);tree=BVHTree.FromPolygons(weapon.tolist(),[tuple(p.vertices) for p in prop.data.polygons])
 for side,pid in [('R',8),('L',7)]:
  if side=='L' and name=='Standing':continue
  distances={}
  for f in range(1,6):
   ids=np.where((piece==pid)&(finger==f))[0]
   distances[f]=min(tree.find_nearest(Vector(pts[i]))[3] for i in ids)
  report[f'{name}:{frame}:{side}']=distances
  center=Vector(pts[piece==pid].mean(0))
  H=rig.pose.bones[f'B_{side}_Hand'].matrix.to_3x3()
  grip=json.loads((P/f'work/grip_pose_{side}.json').read_text())
  normal=H@Vector(grip['palm_normal_hand_local']);axis=H@Vector(grip['handle_axis_hand_local'])
  for label,d in [('palm',normal),('back',-normal),('axis',axis)]:
   cam=common.ortho_camera('hand_camera',center+d*2,(0,0,0),.30)
   cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam
   sc.render.resolution_x=sc.render.resolution_y=600
   sc.render.filepath=str(P/f'review/actual_{name}_{frame}_{side}_{label}.png');bpy.ops.render.render(write_still=True)
   bpy.data.objects.remove(cam,do_unlink=True)
(P/'work/grip_actual.json').write_text(json.dumps(report,indent=2));print('ACTUAL GRIP distance_m',report,flush=True)

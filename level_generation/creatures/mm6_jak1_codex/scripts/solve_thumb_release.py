"""Find a thumb opening arc that stays outside the held shaft."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/drop_unretimed.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Jackalman'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
G=json.loads((P/'work/grip_pose.json').read_text())['finger_local'];q0=Quaternion(G['B_R_Finger0']);pb=rig.pose.bones['B_R_Finger0'];names={g.index:g.name for g in ob.vertex_groups};ids=[v.index for v in ob.data.vertices if sum(g.weight for g in v.groups if names[g.group].startswith('B_R_Finger0'))>.6];inv=(rig.matrix_world@rig.pose.bones['Staff'].matrix).inverted();best=None
for xyz in [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(1,-1,0),(1,0,-1),(0,1,-1)]:
 for deg in [-90,-60,-30,30,60,90]:
  q1=Quaternion(Vector(xyz).normalized(),math.radians(deg))@q0;minimum=10;last=0
  for u in np.linspace(0,1,13):
   pb.rotation_quaternion=q0.slerp(q1,float(u));bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();points=[inv@ob.matrix_world@me.vertices[i].co for i in ids];ev.to_mesh_clear();radius=min((v.x*v.x+v.y*v.y)**.5 for v in points);minimum=min(minimum,radius);last=radius
   if minimum<.014:break
  if minimum>=.014 and last>.04 and (best is None or -abs(deg)-last>best['score']):best={'target_quaternion':list(q1),'axis':xyz,'angle_deg':deg,'min_radius_m':minimum,'final_min_radius_m':last,'score':-abs(deg)-last}
assert best and best['final_min_radius_m']>.035,best
(P/'work/thumb_release.json').write_text(json.dumps(best,indent=2));print('THUMB ARC',best,flush=True)

sys=__import__('sys');sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as shared
glb=shared.Glb(P/'export/mm6_jak1_runtime_lod0.glb')
for clip,animation,start,end in glb.clips():
 pose=glb.pose(animation,shared.sample_grid(start,end,48));out={}
 for side in 'LR':
  wrist=pose[:,glb.names[f'B_{side}_Hand'],:3,3];elbow=pose[:,glb.names[f'B_{side}_Forearm'],:3,3];knuckles=np.mean([pose[:,glb.names[f'B_{side}_Finger{i}'],:3,3]for i in range(1,5)],axis=0);angles=shared.angle(wrist-elbow,knuckles-wrist);out[side]=[float(angles.min()),float(angles.max())]
 print('PHYSICAL WRIST BEND',clip,out,flush=True)

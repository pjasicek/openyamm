import bpy,sys,json,numpy as np,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_sources.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig'];common.workbench_clay(scene)
g=json.loads((P/'work/grip_pose.json').read_text());axis=Vector(g['handle_axis_hand_local']);center=Vector(g['handle_centre_hand_local'])
bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.013,depth=1.88);staff=bpy.context.object;staff.name='StaffStandIn';staff.data.transform(Matrix.Translation((0,0,-.18)))
mat=bpy.data.materials.new('Staff');mat.diffuse_color=(.35,.18,.04,1);staff.data.materials.append(mat)
out=P/'review/round2/sources';out.mkdir(exist_ok=True);rows={}
for role in ['Cast1','Cast2','Cast3','Summon']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows[role]=[]
 for i,f in enumerate(np.linspace(*a.frame_range,7)):
  scene.frame_set(int(f),subframe=float(f-int(f)));H=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix;M=(H.to_3x3()@axis).to_track_quat('Z','Y').to_matrix().to_4x4();M.translation=H@center;staff.matrix_world=M
  for v in ['front','three_quarter']:
   path=common.render_views(str(out/f'{role}_{i}'),.9,3.6,views=(v,),resolution=(260,350))[0];rows[role].append({'view':v,'frame':float(f),'path':str(Path(path).relative_to(P))})
(out/'frames.json').write_text(json.dumps(rows,indent=2))

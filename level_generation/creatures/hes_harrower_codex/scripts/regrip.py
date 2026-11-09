"""Keep the approved blade plane while aligning the fist's grip centre forward of the wrist."""
from pathlib import Path
import json,bpy
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_final.blend'));rig=bpy.data.objects['Rig']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for sd,sgn in (('L',1),('R',-1)):
 g=json.loads((P/f'work/grip_pose_{sd}.json').read_text());z=Vector(g['handle_axis_hand_local']);x=Vector(g['blade_out_hand_local']);y=z.cross(x)
 old=Matrix((x,y,z)).transposed().to_4x4();old.translation=Vector(g['handle_centre_hand_local'])
 f=Vector(g['handle_centre_hand_local']);f=(f-z*f.dot(z)).normalized();local=Matrix((z,f,z.cross(f))).transposed()
 up=Vector((0,0,1));forward=Vector((0,-1,0));H=Matrix((up,forward,up.cross(forward))).transposed()@local.transposed()
 g['blade_out_hand_local']=list(H.transposed()@Vector((sgn,0,0)));g['blade_front_hand_local']=list(H.transposed()@forward)
 x=Vector(g['blade_out_hand_local']);new=Matrix((x,z.cross(x),z)).transposed().to_4x4();new.translation=Vector(g['handle_centre_hand_local'])
 hand=rig.data.bones[f'B_{sd}_Hand'].matrix_local;T=hand@new@old.inverted()@hand.inverted()
 for prefix in ('Family_','Vreth_'):
  for v in bpy.data.objects[prefix+'Blade_'+sd].data.vertices:v.co=T@v.co
 (P/f'work/grip_pose_{sd}.json').write_text(json.dumps(g,indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/grip_forward.blend'))

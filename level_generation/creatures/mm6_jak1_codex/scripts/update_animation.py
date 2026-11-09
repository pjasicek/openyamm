import bpy,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
for n in ['animate_staff.py','refine_deformation.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
from thumb_cmc import repair_thumbs
from hand_rest_roll import restore,apply as roll_palms
from shoulder_weights import repair_shoulders
from skirt_weights import repair_skirt
new_staff={n:bpy.data.objects['Rig'].data.bones[n].matrix_local.copy() for n in ['Staff','StaffTip']}
for name in ['textured_master','production_body']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{name}.blend'))
 rig=bpy.data.objects['Rig'];restore(bpy.data.objects['Body'],rig);repair_thumbs(bpy.data.objects['Body'],rig);roll_palms(bpy.data.objects['Body'],rig);repair_shoulders(bpy.data.objects['Body']);repair_skirt(bpy.data.objects['Body']);old=rig.data.bones['Staff'].matrix_local.copy();delta=new_staff['Staff']@old.inverted()
 if 'StaffMesh' in bpy.data.objects:bpy.data.objects['StaffMesh'].data.transform(delta)
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 for n,m in new_staff.items():rig.data.edit_bones[n].matrix=m
 bpy.ops.object.mode_set(mode='OBJECT')
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/animated_master.blend'))as(src,dst):dst.actions=src.actions
 for a in dst.actions:a.use_fake_user=True
 bpy.context.scene.render.fps=240
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{name}.blend'))
runpy.run_path(str(P/'scripts/fit_shoulder_weights.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/weapon_probe.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')

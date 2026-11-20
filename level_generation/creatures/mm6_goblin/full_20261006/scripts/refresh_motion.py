import bpy,json,hashlib
from pathlib import Path
O=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006')
bpy.ops.wm.open_mainfile(filepath=str(O/'work/native_textured_v1.blend'))
body=bpy.data.objects['Goblin_Body'];arm=bpy.data.objects['Goblin_Rig'];clips=['Standing','Walk','Attack','Hit','Death','Corpse','Fidget']
def identity():
 return hashlib.sha256(repr(([tuple(v.co) for v in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons],[tuple(v.uv) for v in body.data.uv_layers.active.data],[[tuple((g.group,g.weight)) for g in v.groups] for v in body.data.vertices])).encode()).hexdigest()
before=identity();arm.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(O/'work/native_full_v1.blend'),link=False) as (src,dst):
 assert all(c in src.actions for c in clips);dst.actions=clips
for a in dst.actions:a.use_fake_user=True
arm.animation_data_create();a=bpy.data.actions['Standing'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0]
bpy.context.scene.render.fps=48;bpy.context.scene.frame_set(1)
assert identity()==before,'UV/geometry/weights changed during action-only repair'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'work/native_textured_v2.blend'))
(O/'review/motion_only_refresh.json').write_text(json.dumps({'operation':'Replace seven native action datablocks only; repair Hit hand orientation interpolation','source_actions':'work/native_full_v1.blend','retained_texture_master':'work/native_textured_v1.blend','output':'work/native_textured_v2.blend','geometry_uv_weights_identity_before_and_after':before,'paid_static_upload_unchanged':True},indent=2)+'\n')

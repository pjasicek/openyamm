from pathlib import Path
import bpy
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
rig=bpy.data.objects['Turtle_Rig'];rig.animation_data_clear()
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
with bpy.data.libraries.load(str(P/'work/anim_v1.blend')) as (source,target):target.actions=list(source.actions)
assert len(bpy.data.actions)==7
for a in bpy.data.actions:a.use_fake_user=True
rig.animation_data_create();rig.animation_data.action=bpy.data.actions['SwimIdle'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))

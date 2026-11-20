import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['textured_master_full','textured_master']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{name}.blend'));rig=bpy.data.objects['Rig'];rig.animation_data_clear()
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/anim_v1.blend'),link=False) as (src,dst):dst.actions=src.actions
 for a in dst.actions:a.use_fake_user=True
 assert len(bpy.data.actions)==8
 rig.animation_data_create();rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.render.fps=60;bpy.context.scene.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{name}.blend'))

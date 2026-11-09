from pathlib import Path
import bpy
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5h.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(p/'work/rig_v5.blend'),link=False) as (src,dst):dst.actions=src.actions
for a in dst.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v5h.blend'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v6.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(p/'work/rig_v5.blend'),link=False) as (src,dst):dst.actions=src.actions
for a in dst.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v6.blend'))

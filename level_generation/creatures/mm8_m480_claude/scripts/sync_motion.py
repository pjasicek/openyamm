"""Apply selected actions without changing the textured mesh or fitted rest skeleton."""
from pathlib import Path
import bpy,numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/authored.blend'));rig=bpy.data.objects['Rig'];rest={b.name:np.array(b.matrix_local) for b in rig.data.bones}
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured.blend'));rig=bpy.data.objects['Rig']
assert set(rest)==set(b.name for b in rig.data.bones)
assert max(np.abs(rest[b.name]-np.array(b.matrix_local)).max() for b in rig.data.bones)<1e-6
rig.animation_data.action=None
for act in list(bpy.data.actions):bpy.data.actions.remove(act)
with bpy.data.libraries.load(str(p/'work/authored.blend'),link=False) as (src,dst):dst.actions=src.actions
assert len(bpy.data.actions)==8
for act in bpy.data.actions:act.use_fake_user=True
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.render.fps=60;bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/ready_final.blend'))

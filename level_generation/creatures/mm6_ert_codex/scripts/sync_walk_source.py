import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
bpy.data.actions.remove(bpy.data.actions['Walking'])
with bpy.data.libraries.load(str(P/'review/walk_posture_v2/candidate.blend'),link=False) as (src,dst):
 assert 'Walking' in src.actions;dst.actions=['Walking']
a=bpy.data.actions['Walking'];a.use_fake_user=True
assert bpy.context.scene.render.fps==60 and a.frame_range[1]==86
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))

import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for file in ['work/rig_equipped.blend','work/rig_textured.blend','work/reduction_soft/lod0_step1_finalmotion.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(P/file));print('ACTIONS',file,[(a.name,a.use_fake_user,a.users)for a in bpy.data.actions],flush=True)

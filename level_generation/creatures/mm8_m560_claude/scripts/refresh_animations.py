"""Replace authored actions in the existing UV master without touching geometry or materials."""
from pathlib import Path
import bpy
P=Path(__file__).resolve().parents[1]
names={'Fly','Attack','Hit','Death','Dead'}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
rig=bpy.data.objects['Wyvern_Rig']
assert len(rig.data.bones)==44
rig.animation_data.action=None
for name in names:
    bpy.data.actions.remove(bpy.data.actions[name])
with bpy.data.libraries.load(str(P/'work/anim_v1.blend'),link=False) as (source,target):
    assert names.issubset(source.actions)
    target.actions=sorted(names)
for action in target.actions:
    assert action.name in names and len(action.slots)==1
    action.use_fake_user=True
rig.animation_data.action=bpy.data.actions['Fly']
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/uv_master.blend'))

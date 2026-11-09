"""Replace the seven clips in an isolated export checkpoint after an animation-only correction."""
import bpy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'animations/manifest.json').read_text())
target=Path(bpy.data.filepath)
assert target.parent==ROOT/'export_work' and target.name in {'game_mesh_library.blend','baked_library.blend'}
assert len(bpy.data.scenes)==1,'Refresh only an isolated export checkpoint'
expected={v['action'] for v in manifest['clips'].values()}
# FULL_COPY can duplicate the active action; discard only this known copy form while replacing the clip set.
for action in bpy.data.actions:
    if action.name in expected:continue
    base,separator,suffix=action.name.rpartition('.')
    assert separator and suffix.isdecimal() and base in expected,'Unexpected action in isolated export checkpoint'
scene=bpy.data.scenes[0];bpy.context.window.scene=scene
rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear()
for action in list(bpy.data.actions):bpy.data.actions.remove(action,do_unlink=True)
with bpy.data.libraries.load(str(ROOT/'animations/animation_library.blend'),link=False) as (available,loaded):
    assert expected.issubset(available.actions)
    loaded.actions=sorted(expected)
for action in loaded.actions:action.use_fake_user=True
rig.animation_data_create();rig.animation_data.action=bpy.data.actions[manifest['clips']['Standing']['action']];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
scene.frame_set(1)
bpy.data.libraries.write(str(target),{scene,*loaded.actions},fake_user=True)
print('Refreshed seven clips in',target.name)

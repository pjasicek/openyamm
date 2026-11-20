"""Replace the clips of the textured master with the gated chain's (clip changes without redoing UVs and textures):
every fake-user action of <src> (work/rig_v5.blend) replaces the action of that name in <dst> (work/rig_v6.blend);
dst actions missing from src are removed. Both files share the rig (same bones), so actions carry over by bone name.
Optional action names replace only those clips, preserving all other destination actions.
Args: -- <src blend> <dst blend> [action ...]"""
import bpy, sys, os
args = sys.argv[sys.argv.index('--') + 1:]
src, dst = (os.path.abspath(p) for p in args[:2])
selected = args[2:]
bpy.ops.wm.open_mainfile(filepath=dst)
rig = bpy.data.objects['Rig']
with bpy.data.libraries.load(src, link=False) as (data_from, _):
    names = list(data_from.actions)
if selected:
    assert set(selected) <= set(names), 'Requested source action is missing'
    names = selected
for a in list(bpy.data.actions):
    if not selected or a.name in selected:
        bpy.data.actions.remove(a)
with bpy.data.libraries.load(src, link=False) as (_, data_to):
    data_to.actions = names
missing = set()
bones = {b.name for b in rig.data.bones}
for a in data_to.actions:
    a.use_fake_user = True
    for fc in getattr(a, 'fcurves', []) or []:
        if fc.data_path.startswith('pose.bones["'):
            n = fc.data_path.split('"')[1]
            if n not in bones:
                missing.add(n)
if missing:
    raise RuntimeError(f'actions animate bones missing from the master: {sorted(missing)}')
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.ops.wm.save_mainfile()
print('SYNC', {a.name: [int(x) for x in a.frame_range] for a in data_to.actions})

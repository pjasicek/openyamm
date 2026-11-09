"""Copies every action of a rig blend into the textured master (work/rig_v6.blend), replacing same-named actions, so
clip changes (clip_timing.py) do not regenerate the head UVs the head retexture was painted on. The two blends share
one armature (same bones). Args: -- <source blend> <target blend>"""
import bpy, sys, os
src, dst = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(dst))
with bpy.data.libraries.load(os.path.abspath(src)) as (data_from, data_to):
    names = [a for a in data_from.actions]
for n in names:
    if n in bpy.data.actions:
        bpy.data.actions[n].name = n + '_old'
with bpy.data.libraries.load(os.path.abspath(src)) as (data_from, data_to):
    data_to.actions = names
for a in data_to.actions:
    a.use_fake_user = True
for a in [a for a in bpy.data.actions if a.name.endswith('_old')]:
    bpy.data.actions.remove(a)
print('SYNC actions', sorted(a.name for a in bpy.data.actions))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(dst))

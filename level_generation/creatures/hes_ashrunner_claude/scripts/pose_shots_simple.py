"""Clay renders of chosen action frames (views). Args: -- <blend> <out png prefix> <views comma> Action:frame [...]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out, views = a[1], a[2].split(','); items = a[3:]
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; common.workbench_clay(sc)
for _n in [x for x in os.environ.get('HIDE', '').split(',') if x]:   # har: hide the other tiers' gear
    if _n in bpy.data.objects:
        bpy.data.objects[_n].hide_render = True
for it in items:
    an, f = it.split(':'); act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f = float(f); sc.frame_set(int(f), subframe=f - int(f))
    common.render_views(f'{out}_{an}_{f:g}', float(os.environ.get('CZ', '1.1')), float(os.environ.get('CH', '2.4')), views=tuple(views), resolution=(500, 560))

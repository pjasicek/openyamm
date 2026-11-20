"""One GLB, two clip sets: the rifle chain's blend (tiers B/C: Standing, Walking, ...) receives the pistol chain's clips
(tier A) renamed <prefix><name> (P_Standing, ...). Both chains start from the same weighted rig (work/rig_v2w.blend),
so the actions carry over by bone name; actions.yml maps tier A's roles onto the P_ clips. Args: -- <rifle blend>
<pistol blend> <out blend> <prefix> <clip> [...]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
rb, pb, out, pre, clips = a[0], a[1], a[2], a[3], a[4:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(rb))
for n in clips:
    old = bpy.data.actions.get(pre + n)
    if old:
        bpy.data.actions.remove(old)
before = set(bpy.data.actions)
with bpy.data.libraries.load(os.path.abspath(pb), link=False) as (src, dst):
    dst.actions = [n for n in clips if n in src.actions]
for act in dst.actions:
    base = act.name.split('.')[0] if act not in before else act.name
    act.name = pre + base; act.use_fake_user = True
    print('MERGE', base, '->', act.name, [int(x) for x in act.frame_range])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

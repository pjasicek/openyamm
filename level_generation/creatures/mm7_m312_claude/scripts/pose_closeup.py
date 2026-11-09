"""Clay close-ups of one bone's region in a posed frame: <action>:<frame> renders around the bone head (front, left,
back, right, ortho, HEIGHT m tall). Args: -- <blend> <bone> <out prefix> <action>:<frame> [...]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, bone, out, items = a[0], a[1], a[2], a[3:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene; common.workbench_clay(scene)
H = float(os.environ.get('HEIGHT', '0.3'))
for it in items:
    an, f = it.split(':'); act = bpy.data.actions[an]
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(float(f)))
    p = rig.matrix_world @ rig.pose.bones[bone].head
    common.render_views(f'{out}_{an}{f}', p.z, H, views=('front', 'left', 'back', 'right'), resolution=(400, 400),
                        target=(p.x, p.y))

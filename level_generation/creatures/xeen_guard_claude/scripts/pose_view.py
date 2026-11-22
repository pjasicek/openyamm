"""Large clay views of one clip frame (front, side, quarter). Args: -- clip frame out_prefix [blend]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, a[3] if len(a) > 3 else 'work/anim_v1.blend'))
rig = bpy.data.objects['Guard_Rig']
import colorize; colorize.colorize(bpy.data.objects['Guard'])
if a[0] != 'REST':
    act = bpy.data.actions[a[0]]; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(a[1]))
else:
    rig.data.pose_position = 'REST'
for v, cam in {'front': ((0, -5, 0.9), (0, 0, 0.9)), 'side': ((5, 0, 0.9), (0, 0, 0.9)),
               'quarter': ((3.4, -3.6, 1.6), (0, 0, 0.8))}.items():
    C.render(*cam, 2.3, os.path.join(HERE, f'{a[2]}_{v}.png'), res=(600, 600), bones=True, color='MATERIAL')

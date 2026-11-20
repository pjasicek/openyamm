"""Close-up clay renders of the right hand with the real sickle mesh on the Sword frame (sickle_geo.frame at BLADE_ROLL),
centred on the hand: front, right, three_quarter, rside60, back. Args: -- <blend> <out prefix> <action:frame> [...]"""
import bpy, sys, os, json
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, sickle_geo
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, picks = a[0], a[1], a[2:]
ROLL = float(os.environ.get('BLADE_ROLL', '90'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; common.workbench_clay(sc)
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
with bpy.data.libraries.load(os.path.join(common.WORK, 'props.blend'), link=False) as (src, dst):
    dst.objects = ['SickleMesh']
sk = dst.objects[0]; sc.collection.objects.link(sk)
c, ax, sx = sickle_geo.frame(rig, G, ROLL); sz = sx.cross(ax)
L = Matrix((sx, ax, sz)).transposed().to_4x4(); L.translation = c
for pk in picks:
    an, fr = pk.split(':'); act = bpy.data.actions[an]
    rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(float(fr)))
    H = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
    sk.matrix_world = H @ L
    p = H.translation
    common.render_views(f'{out}_{an}{fr}', p.z, 0.45, views=('front', 'right', 'three_quarter', 'rside60', 'back'),
                        resolution=(420, 420), target=(p.x, p.y))
print('SHOTS done')

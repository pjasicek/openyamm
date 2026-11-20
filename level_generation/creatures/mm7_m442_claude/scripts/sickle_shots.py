"""Clay renders of the rig with the real sickle mesh (work/props.blend 'SickleMesh') on the solved handle at given blade
rolls (sickle_geo.frame), for the roll choice and blade checks. Args: -- <blend> <out prefix> <rolls comma> <action:frame> [...]"""
import bpy, sys, os, json
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, sickle_geo
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, rolls, picks = a[0], a[1], [float(x) for x in a[2].split(',')], a[3:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; common.workbench_clay(sc)
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
with bpy.data.libraries.load(os.path.join(common.WORK, 'props.blend'), link=False) as (src, dst):
    dst.objects = ['SickleMesh']
sk = dst.objects[0]; sc.collection.objects.link(sk)
for roll in rolls:
    c, ax, sx = sickle_geo.frame(rig, G, roll); sz = sx.cross(ax)
    L = Matrix((sx, ax, sz)).transposed().to_4x4(); L.translation = c
    for pk in picks:
        an, fr = pk.split(':'); act = bpy.data.actions[an]
        rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
        sc.frame_set(int(float(fr)))
        sk.matrix_world = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix @ L
        common.render_views(f'{out}_r{int(roll)}_{an}{fr}', 0.9, 2.1, views=('front', 'right'), resolution=(300, 460))
print('SHOTS done')

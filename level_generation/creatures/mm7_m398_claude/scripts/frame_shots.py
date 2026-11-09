"""Renders listed action frames (front, right, three-quarter) with the sword stand-in on the solved handle
(work/grip_pose.json). Args: -- <blend> <out prefix> action:frame [...]"""
import bpy, bmesh, sys, os, json
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, picks = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
c, ax = Vector(G['handle_centre_hand_local']), Vector(G['handle_axis_hand_local']).normalized()
side = ax.orthogonal().normalized(); flat = ax.cross(side)
me = bpy.data.meshes.new('sword'); bm = bmesh.new()
for a0, a1, w, t in ((-0.10, 0.05, 0.012, 0.012), (0.05, 0.065, 0.07, 0.016), (0.065, 0.85, 0.022, 0.004)):
    vs = [bm.verts.new(c + ax * aa + side * (sx * w) + flat * (sy * t)) for aa in (a0, a1) for sx in (-1, 1) for sy in (-1, 1)]
    for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[i] for i in q])
bm.to_mesh(me); bm.free()
sw = bpy.data.objects.new('sword', me); bpy.context.scene.collection.objects.link(sw)
mat = bpy.data.materials.new('s'); mat.diffuse_color = (0.75, 0.45, 0.2, 1); me.materials.append(mat)
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
for pk in picks:
    an, fr = pk.split(':')
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(fr))
    sw.matrix_world = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
    # FS_FOCUS=x,y,z,size: close-up around a point (e.g. a reported contact) instead of the whole body
    fx = [float(v) for v in os.environ['FS_FOCUS'].split(',')] if os.environ.get('FS_FOCUS') else None
    if fx:
        common.render_views(f'{out}_{an}{fr}', fx[2], fx[3], views=('front', 'right', 'back', 'three_quarter'),
                            resolution=(360, 360), target=(fx[0], fx[1]))
    else:
        common.render_views(f'{out}_{an}{fr}', 0.95, 2.0, views=('front', 'right', 'three_quarter'), resolution=(360, 400))

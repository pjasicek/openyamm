"""Clip sheet with a spear stand-in on the solved handle (work/grip_pose.json) and a buckler disc on the left forearm.
Spear: 1.9 m, held 0.75 m from the butt, head (red) at +axis. Renders N evenly spaced frames per action, one view.
Args: -- <blend> <out_dir> <view> <frames per action> action [action ...]   (env FRAMES=a,b,c picks exact frames)"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, view, n = a[0], a[1], a[2], int(a[3]); acts = a[4:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene; common.workbench_clay(scene)
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
c = Vector(G['handle_centre_hand_local']); ax = Vector(G['handle_axis_hand_local']).normalized()
side = ax.orthogonal().normalized(); flat = ax.cross(side)


def box_mesh(name, segs, col):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for a0, a1, w0, w1, t in segs:
        vs = [bm.verts.new(c + ax * aa + side * (sx * (w0 if aa == a0 else w1)) + flat * (sy * t)) for aa in (a0, a1) for sx in (-1, 1) for sy in (-1, 1)]
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            bm.faces.new([vs[i] for i in q])
    bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new(name); m.diffuse_color = col; me.materials.append(m)
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); return o


shaft = box_mesh('shaft', [(-0.75, 0.93, 0.014, 0.014, 0.014)], (0.45, 0.3, 0.15, 1))
head = box_mesh('head', [(0.93, 1.15, 0.035, 0.003, 0.006)], (0.85, 0.1, 0.1, 1))
me = bpy.data.meshes.new('buckler'); bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=0.2); bm.to_mesh(me); bm.free()
m = bpy.data.materials.new('buck'); m.diffuse_color = (0.4, 0.6, 0.2, 1); me.materials.append(m)
buck = bpy.data.objects.new('buckler', me); scene.collection.objects.link(buck)
fl = os.environ.get('FRAMES')
rows = []
for name in acts:
    act = bpy.data.actions[name]
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    frames = [float(x) for x in fl.split(',')] if fl else [f0 + (f1 - f0) * i / max(n - 1, 1) for i in range(n)]
    row = []
    for i, f in enumerate(frames):
        scene.frame_set(int(f), subframe=f - int(f))
        H = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
        shaft.matrix_world = H; head.matrix_world = H
        fa = rig.matrix_world @ rig.pose.bones['B_L_Forearm'].matrix
        hd = rig.matrix_world @ rig.pose.bones['B_L_Hand'].matrix
        p0, p1 = fa.translation, hd.translation
        along = (p1 - p0).normalized()
        lat = hd.to_3x3() @ Vector((0, 0, 1)); lat = (lat - along * lat.dot(along)).normalized()
        cen = p0 + (p1 - p0) * 0.65 + lat * 0.06
        z = lat; x = along; y = z.cross(x)
        buck.matrix_world = Matrix.Translation(cen) @ Matrix((x, y, z)).transposed().to_4x4()
        p = common.render_views(os.path.join(out, f'{name}_{i}'), 1.0, 2.7, views=(view,), resolution=(300, 400), distance=9)[0]
        row.append([p, f'{name} {f:.1f}'])
    rows.append(row)
json.dump(rows, open(os.path.join(out, 'frames.json'), 'w'))
print('SHEET', len(rows))

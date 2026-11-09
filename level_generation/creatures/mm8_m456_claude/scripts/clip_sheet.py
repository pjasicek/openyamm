"""Render N evenly spaced frames per action of the Rig (one view) to <out_dir>/<action>_<i>.png + frames.json.
Args: -- <blend> <out_dir> <view> <frames per action> action [action ...]"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, view, n = a[0], a[1], a[2], int(a[3]); acts = a[4:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene; common.workbench_clay(scene)
import json as _json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_G = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'grip_pose.json')
sword = None
if os.path.exists(_G):
    import bmesh
    from mathutils import Vector
    G = _json.load(open(_G)); c = Vector(G['handle_centre_hand_local']); ax = Vector(G['handle_axis_hand_local']).normalized()
    side = ax.orthogonal().normalized(); flat = ax.cross(side)
    me = bpy.data.meshes.new('sw'); bm = bmesh.new()
    for a0, a1, w, t in ((-0.09, 0.045, 0.011, 0.011), (0.045, 0.06, 0.075, 0.014), (0.06, 1.11, 0.025, 0.004)):
        vs = [bm.verts.new(c + ax * aa + side * (sx * w) + flat * (sy * t)) for aa in (a0, a1) for sx in (-1, 1) for sy in (-1, 1)]
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            bm.faces.new([vs[i] for i in q])
    bm.to_mesh(me); bm.free()
    sword = bpy.data.objects.new('sw', me); scene.collection.objects.link(sword)
rows = []
for name in acts:
    act = bpy.data.actions[name]
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1)
        scene.frame_set(int(f), subframe=f - int(f))
        if sword is not None:
            sword.matrix_world = rig.matrix_world @ rig.pose.bones['B_L_Hand'].matrix
        p = common.render_views(os.path.join(out, f'{name}_{i}'), 0.9, 2.4, views=(view,), resolution=(260, 420))[0]
        row.append([p, f'{name} {f:.1f}'])
    rows.append(row)
json.dump(rows, open(os.path.join(out, 'frames.json'), 'w'))

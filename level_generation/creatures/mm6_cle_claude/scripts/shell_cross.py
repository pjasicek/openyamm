"""Cloak shell crossing audit: the cloak is a solid shell (outer and inner side from cloak_sides.py), and
where the inner surface passes through the outer one (or the outer through the inner) the other side's paint shows
as spots. Each inner vertex is tied at rest to its nearest outer-face point (face + barycentric) and its signed
offset along that face's normal (negative = inside); per frame the tracked point and normal are re-evaluated and an
inner vertex whose offset turns positive by more than TOL crosses. Rim vertices (|rest offset| < RIM) are skipped.
Args: blend [clips...]; prints SHELL <clip> {worst frame count, depth, where}."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, args[0]))
arm = bpy.data.objects['Cleric_Rig']; mesh = bpy.data.objects['Cleric']; me = mesh.data
REG = json.loads(bpy.context.scene['cle_uv_regions'])
ureg = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['uv_region'].data.foreach_get('value', ureg)
CLOAK = {'CloakB', 'CloakL', 'CloakR', 'Mantle', 'CloakBi', 'CloakLi', 'CloakRi', 'Mantlei'}
SIDE_IN = set(json.loads(open(os.path.join(common.WORK, 'cloak_sides.json')).read())['inner'])   # cloak_sides.py
TOL, RIM = 0.002, 0.004
me.calc_loop_triangles()
otris = [t for t in me.loop_triangles if REG[ureg[t.polygon_index]] in CLOAK and t.polygon_index not in SIDE_IN]
iverts = sorted({v for p in me.polygons if p.index in SIDE_IN for v in p.vertices})
ovset = {v for t in otris for v in t.vertices}
iverts = [v for v in iverts if v not in ovset]


def positions():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = [mesh.matrix_world @ v.co for v in m.vertices]
    ev.to_mesh_clear()
    return P


arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
R = positions()
tree = BVHTree.FromPolygons(R, [tuple(t.vertices) for t in otris])
ties = []
for v in iverts:
    loc, nrm, fi, dist = tree.find_nearest(R[v])
    if fi is None or dist > 0.05:
        continue
    a, b, c = (R[i] for i in otris[fi].vertices)
    off = (R[v] - loc).dot((b - a).cross(c - a).normalized())
    if off > -RIM:
        continue
    ties.append((v, fi, loc.copy(), off))
print('TIES', len(ties), 'of', len(iverts))
clips = args[1:] or [a.name for a in bpy.data.actions if not a.name.endswith('_src')]
for name in clips:
    act = bpy.data.actions.get(name)
    if act is None:
        continue
    arm.animation_data.action = act
    if act.slots:
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    worst = (0, 0, 0.0, None)
    frames = 0
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        P = positions()
        n = 0; depth = 0.0; where = []
        for v, fi, rest, off in ties:
            ta, tb, tc = (R[i] for i in otris[fi].vertices)
            a, b, c = (P[i] for i in otris[fi].vertices)
            q = barycentric_transform(rest, ta, tb, tc, a, b, c)
            d = (P[v] - q).dot((b - a).cross(c - a).normalized())
            if d > TOL:
                n += 1; depth = max(depth, d)
                where.append((REG[ureg[otris[fi].polygon_index]], round(R[v].z, 2)))
        frames += n > 0
        if n > worst[0]:
            worst = (n, f, depth, sorted(set(where))[:8])
    print('SHELL', name, json.dumps({'frames_with': frames, 'of': f1 - f0 + 1, 'worst': worst[0], 'frame': worst[1],
                                     'depth_mm': round(worst[2] * 1000, 1), 'where': worst[3]}))

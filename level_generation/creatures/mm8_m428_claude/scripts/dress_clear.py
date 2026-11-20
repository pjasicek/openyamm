"""Right fist and dagger vs the dress, every frame: the skirt (piece 0 below the belt) is a bell, so at each sample's
height the dress outline is the convex hull of the posed skirt vertices within +/-1.5 cm of that height; a sample is
inside when it lies within that outline (2D). Reports per clip the deepest inside depth (cm, positive = inside), the
minimum clearance outside, and frames with any hand vertex (piece 4) or dagger sample inside.
Args: -- <blend> [action ...]"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); acts = a[1:] or ['Standing', 'Walking', 'Running', 'Hit', 'Fidget']
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
rest = np.array([v.co[:] for v in me.vertices])
skirt_idx = np.flatnonzero((pv == 0) & (rest[:, 2] < 1.0) & ~((rest[:, 2] > 0.95) & (np.abs(rest[:, 0]) > 0.19)))
hand_idx = np.flatnonzero(pv == 4)


def hull(pts):
    pts = sorted(map(tuple, pts))
    if len(pts) < 3: return np.array(pts)
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return np.array(lo[:-1] + hi[:-1])


def depth(poly, q):
    """signed distance of q into the convex polygon (positive inside)"""
    d = []
    for i in range(len(poly)):
        p0, p1 = poly[i], poly[(i + 1) % len(poly)]; e = p1 - p0; n = np.array([e[1], -e[0]]); n /= np.linalg.norm(n) + 1e-12
        d.append((q - p0) @ n)
    return -max(d)


for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    worst_in, worst_f, clear, bad = -1e9, None, 1e9, []
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
        sk = co[skirt_idx]
        M = rig.matrix_world @ rig.pose.bones['Dagger'].matrix
        samples = list(co[hand_idx]) + [np.array((M @ Vector((0, y, 0)))[:]) for y in np.linspace(-0.06, 0.32, 20)]
        hit = False
        for q in samples:
            band = sk[np.abs(sk[:, 2] - q[2]) < 0.015]
            if len(band) < 6 or q[2] > 1.0: continue
            dd = depth(hull(band[:, :2]), q[:2])
            if dd > worst_in: worst_in, worst_f = dd, f
            if dd > 0.002: hit = True
            clear = min(clear, -dd)
        if hit: bad.append(f)
    print('DRESSCLEAR', name, 'deepest', round(worst_in * 100, 2), 'cm at frame', worst_f, '| frames inside', bad)

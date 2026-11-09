"""Clamp the reduced rollers inside the source rollers' rolling contour: blender -b -P roller_clamp.py -- <ladder.blend>
<Cand_xx>. The quadric placement put a few new roller vertices just outside the source contour (seen along the roll
axis, x), so the rolling rollers dipped 1.4 mm under the floor in Walking; the creature's contact audit keeps every
rolling subframe above it. Each candidate vertex rigid on a Roller bone that lies outside the convex hull of that
roller's source vertices (yz) moves onto the hull. Saves work/ladder.blend for export_cand.py."""
import os, sys, bpy, numpy as np
blend, cn = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=blend)
src = bpy.data.objects['Body']; c = bpy.data.objects[cn]
def hull_eq(pts):
    """2D convex hull facets as (nx, ny, offset), n.p + offset <= 0 inside (monotone chain; Blender has no scipy)"""
    pts = sorted(set(map(tuple, np.round(pts, 7).tolist())))
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    ring = np.array(lo[:-1] + up[:-1]); eq = []
    for a, b in zip(ring, np.roll(ring, -1, 0)):
        d = b - a; n = np.array([d[1], -d[0]]) / np.linalg.norm(d)  # counter-clockwise ring: outward normal
        eq.append([n[0], n[1], -n @ a])
    return np.array(eq)


def rigid(o, bone):
    g = o.vertex_groups[bone].index
    return np.array([any(x.group == g and x.weight > .999 for x in v.groups) for v in o.data.vertices])
moved = 0
for bone in [g.name for g in src.vertex_groups if g.name.startswith('Roller_')]:
    sv = np.array([v.co[:] for v in src.data.vertices])[rigid(src, bone)]
    eq = hull_eq(sv[:, 1:])
    assert (sv[:, 1:] @ eq[:, :2].T + eq[:, 2]).max() < 1e-6
    m = rigid(c, bone)
    for i in np.flatnonzero(m):
        co = np.array(c.data.vertices[i].co[:]); s = eq[:, :2] @ co[1:] + eq[:, 2]
        for _ in range(4):  # move along the worst facet normal until inside (corners need a second step)
            k = int(s.argmax())
            if s[k] <= 0:
                break
            co[1:] -= eq[k, :2] * (s[k] + 1e-6); s = eq[:, :2] @ co[1:] + eq[:, 2]; moved += 1
        c.data.vertices[i].co = co
    print('ROLLER', bone, 'source verts', len(sv), 'candidate verts', int(m.sum()))
print('CLAMPED moves', moved)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'ladder.blend'))

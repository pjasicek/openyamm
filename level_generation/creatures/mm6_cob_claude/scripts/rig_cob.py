"""Cobra rig on work/hd_reduced.blend (1 m tall rest pose: ground body along +Y, neck raised at the origin, head -Y).

Centreline from the mesh: slices across the ground body (by y) and the raised neck (by z), joined at the bend,
smoothed and resampled every SEG metres from the tail tip to the neck top; the head is one bone from the neck top to
the snout. Root = the segment at the bend; Tail_01.. run outward along the ground, Spine_01.. up the neck, then Head.
Weights: each vertex's arc position along the centreline (nearest point, smoothed over the mesh to avoid jumps
across the inner bend), blended linearly between neighbouring segment midpoints (a partition of unity: no heat-weight
failures on a long thin tube, the hood follows the neck segments it sits on).
Writes work/rig_v1.blend (Cobra + Cobra_Rig) and work/rig.json (joints, segment lengths, body radius per joint, root
index) for anim_cob.py."""
import bpy, json, os, math
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEG = 0.11
mesh = bpy.data.objects['Cobra']; me = mesh.data
co = np.array([tuple(v.co) for v in me.vertices])
ymax = co[:, 1].max()

# ---- raw centreline ----------------------------------------------------------------------------------------------
ground, raised = [], []
for y in np.arange(ymax - 0.03, 0.17, -0.04):
    s = co[(np.abs(co[:, 1] - y) < 0.02) & (co[:, 2] < 0.4)]
    if len(s) > 4:
        ground.append(((s[:, 0].min() + s[:, 0].max()) / 2, y, (s[:, 2].min() + s[:, 2].max()) / 2,
                       (s[:, 2].max() - s[:, 2].min()) / 2))
corner = co[(co[:, 1] < 0.17) & (co[:, 2] < 0.3)]
for z in np.arange(0.30, 0.81, 0.04):
    s = co[(np.abs(co[:, 2] - z) < 0.02) & (co[:, 1] < 0.17)]
    if len(s) > 4:
        raised.append(((s[:, 0].min() + s[:, 0].max()) / 2, (s[:, 1].min() + s[:, 1].max()) / 2, z,
                       (s[:, 1].max() - s[:, 1].min()) / 2))
tip = co[co[:, 1] > ymax - 0.01].mean(0)
raw = [(tip[0], ymax, tip[2], 0.005)] + ground + \
      [(0.0, (corner[:, 1].min() + 0.17) / 2 + 0.02, 0.15, 0.1)] + raised
raw = np.array(raw)
pts, rad = raw[:, :3], raw[:, 3]
for _ in range(3):                                   # Chaikin smoothing, endpoints kept
    p2, r2 = [pts[0]], [rad[0]]
    for a, b, ra, rb in zip(pts[:-1], pts[1:], rad[:-1], rad[1:]):
        p2 += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]; r2 += [0.75 * ra + 0.25 * rb, 0.25 * ra + 0.75 * rb]
    p2.append(pts[-1]); r2.append(rad[-1]); pts, rad = np.array(p2), np.array(r2)
pts[:, 0] = 0.0                                      # symmetric rig
arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
n = int(round(arc[-1] / SEG))
samp = np.linspace(0, arc[-1], n + 1)
J = np.stack([np.interp(samp, arc, pts[:, i]) for i in range(3)], 1)
R = np.interp(samp, arc, rad)
snout = co[co[:, 1] < co[:, 1].min() + 0.015].mean(0)
J = np.vstack([J, [0.0, snout[1] + 0.01, snout[2]]]); R = np.append(R, 0.04)
nseg = len(J) - 1                                    # last segment = head
root = int(np.argmin(np.linalg.norm(J[:-1] - np.array([0, 0.1, 0.12]), axis=1)))
print('CENTRELINE length %.3f segments %d root %d' % (arc[-1], nseg, root))


def name(i):
    if i == nseg - 1:
        return 'Head'
    if i == root:
        return 'Root'
    return f'Tail_{root - i:02d}' if i < root else f'Spine_{i - root:02d}'


# ---- armature ----------------------------------------------------------------------------------------------------
arm = bpy.data.armatures.new('Cobra_Rig'); rig = bpy.data.objects.new('Cobra_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for i in range(nseg):
    b = arm.edit_bones.new(name(i))
    a, c = Vector(J[i]), Vector(J[i + 1])
    b.head, b.tail = (c, a) if i < root else (a, c)   # tail bones point away from the root
    b.align_roll(Vector((1, 0, 0)) if abs((b.tail - b.head).normalized().x) < 0.9 else Vector((0, 0, 1)))
    eb[i] = b
for i in range(nseg):
    if i < root:
        eb[i].parent = eb[i + 1]
    elif i > root:
        eb[i].parent = eb[i - 1]
    eb[i].use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')

# ---- weights -----------------------------------------------------------------------------------------------------
segA, segB = J[:-1], J[1:]
seglen = np.linalg.norm(segB - segA, axis=1)
cum = np.concatenate([[0], np.cumsum(seglen)])
best_s = np.zeros(len(co)); best_d = np.full(len(co), 1e9)
for i in range(nseg):
    d = segB[i] - segA[i]
    t = np.clip(((co - segA[i]) @ d) / (d @ d), 0, 1)
    dist = np.linalg.norm(co - (segA[i] + t[:, None] * d), axis=1)
    m = dist < best_d
    best_d[m] = dist[m]; best_s[m] = cum[i] + t[m] * seglen[i]
adj = [[] for _ in range(len(co))]
for e in me.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)
s = best_s.copy()
for _ in range(4):
    s = np.array([0.5 * s[v] + 0.5 * np.mean(s[adj[v]]) if adj[v] else s[v] for v in range(len(co))])
mid = (cum[:-1] + cum[1:]) / 2
groups = [mesh.vertex_groups.new(name=name(i)) for i in range(nseg)]
for v in range(len(co)):
    x = s[v]
    if x <= mid[0]:
        groups[0].add([v], 1.0, 'REPLACE'); continue
    if x >= mid[-1]:
        groups[-1].add([v], 1.0, 'REPLACE'); continue
    i = int(np.searchsorted(mid, x) - 1)
    f = (x - mid[i]) / (mid[i + 1] - mid[i])
    groups[i].add([v], 1 - f, 'REPLACE'); groups[i + 1].add([v], f, 'REPLACE')
mesh.parent = rig
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
json.dump({'joints': J.round(5).tolist(), 'radius': R.round(4).tolist(), 'root': root,
           'names': [name(i) for i in range(nseg)]}, open(os.path.join(HERE, 'work', 'rig.json'), 'w'), indent=1)
print('RIG bones', nseg, 'unweighted', sum(1 for v in me.vertices if not v.groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))

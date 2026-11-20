"""Sea serpent rig on work/hd_reduced.blend (or hd_base): 1 m tall column from the waterline (z 0) arching forward to
the head at -Y.

Centreline by marching: from the base centre, step STEP along the current direction, take the mesh slab across it
(within SLAB of the plane, within REACH of the step point), re-centre on the slab's bounding-box centre and turn (at
most MAX_TURN per step), until the slab is empty past the snout. Smoothed and resampled every SEG metres. The last
HEAD_LEN of the centreline is one Head bone (head shell, mouth and claw ring move rigidly); Root..Spine_NN below it.
Weights: arc position along the centreline (nearest point, smoothed over the mesh), blended linearly between
neighbouring segment midpoints (as mm6_cob_claude).
Writes work/rig_v1.blend (Seas + Seas_Rig) and work/rig.json (joints, radius per joint, names)."""
import bpy, json, os, math
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP, SLAB, REACH, MAX_TURN = 0.035, 0.018, 0.2, math.radians(25)
SEG, HEAD_LEN = 0.075, 0.24
mesh = bpy.data.objects['Seas']; me = mesh.data
co = np.array([tuple(v.co) for v in me.vertices])

# ---- march the centreline ---------------------------------------------------------------------------------------
base = co[co[:, 2] < 0.03]
p = np.array([(base[:, 0].min() + base[:, 0].max()) / 2, (base[:, 1].min() + base[:, 1].max()) / 2, 0.0])
d = np.array([0.0, 0.0, 1.0])
pts, rad = [p.copy()], [float(np.linalg.norm(base[:, :2] - p[:2], axis=1).mean())]
for _ in range(200):
    q = p + STEP * d
    rel = co - q
    s = co[(np.abs(rel @ d) < SLAB) & (np.linalg.norm(rel, axis=1) < REACH)]
    if len(s) < 6:
        break
    c = (s.min(0) + s.max(0)) / 2
    c = c - ((c - q) @ d) * d                     # stay on the step plane
    nd = (c - p) / np.linalg.norm(c - p)
    ang = math.acos(max(-1.0, min(1.0, float(nd @ d))))
    if ang > MAX_TURN:                            # limit the turn
        axis = np.cross(d, nd); axis /= np.linalg.norm(axis)
        nd = d * math.cos(MAX_TURN) + np.cross(axis, d) * math.sin(MAX_TURN)
        c = p + STEP * nd
    pts.append(c.copy()); rad.append(float(np.median(np.linalg.norm(s - c, axis=1))))
    d, p = nd, c
pts, rad = np.array(pts), np.array(rad)
pts[:, 0] = 0.0                                    # symmetric rig
for _ in range(2):                                 # Chaikin smoothing, endpoints kept
    p2, r2 = [pts[0]], [rad[0]]
    for a, b, ra, rb in zip(pts[:-1], pts[1:], rad[:-1], rad[1:]):
        p2 += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]; r2 += [0.75 * ra + 0.25 * rb, 0.25 * ra + 0.75 * rb]
    p2.append(pts[-1]); r2.append(rad[-1]); pts, rad = np.array(p2), np.array(r2)
arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
head_start = arc[-1] - HEAD_LEN
n = max(2, int(round(head_start / SEG)))
samp = np.append(np.linspace(0, head_start, n + 1), arc[-1])
J = np.stack([np.interp(samp, arc, pts[:, i]) for i in range(3)], 1)
R = np.interp(samp, arc, rad)
nseg = len(J) - 1
print('CENTRELINE length %.3f segments %d head from %.3f' % (arc[-1], nseg, head_start))


def name(i):
    return 'Head' if i == nseg - 1 else ('Root' if i == 0 else f'Spine_{i:02d}')


arm = bpy.data.armatures.new('Seas_Rig'); rig = bpy.data.objects.new('Seas_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = []
for i in range(nseg):
    b = arm.edit_bones.new(name(i)); b.head, b.tail = Vector(J[i]), Vector(J[i + 1])
    b.align_roll(Vector((1, 0, 0)))
    if i:
        b.parent = eb[i - 1]
    b.use_connect = False
    eb.append(b)
bpy.ops.object.mode_set(mode='OBJECT')

segA, segB = J[:-1], J[1:]
seglen = np.linalg.norm(segB - segA, axis=1); cum = np.concatenate([[0], np.cumsum(seglen)])
best_s = np.zeros(len(co)); best_d = np.full(len(co), 1e9)
for i in range(nseg):
    dd = segB[i] - segA[i]
    t = np.clip(((co - segA[i]) @ dd) / (dd @ dd), 0, 1)
    dist = np.linalg.norm(co - (segA[i] + t[:, None] * dd), axis=1)
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
    i = int(np.searchsorted(mid, x) - 1); f = (x - mid[i]) / (mid[i + 1] - mid[i])
    groups[i].add([v], 1 - f, 'REPLACE'); groups[i + 1].add([v], f, 'REPLACE')
mesh.parent = rig
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
json.dump({'joints': J.round(5).tolist(), 'radius': R.round(4).tolist(), 'names': [name(i) for i in range(nseg)]},
          open(os.path.join(HERE, 'work', 'rig.json'), 'w'), indent=1)
print('RIG bones', nseg, 'unweighted', sum(1 for v in me.vertices if not v.groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))

"""Treant rig (non-humanoid playbook, own rig). Forward -Y, up +Z, character left +X. work/step2.blend -> work/rig_v1.blend.

The Smart Topology return is a soup of ~140 loose strands (bark ropes, root tendrils, limb pieces, twig tips) that
overlap and touch everywhere. Heat weights or per-piece rigid binding would tear touching strands apart, so every
weight is a CONTINUOUS FIELD OF POSITION: overlapping pieces at the same place get the same weights and stay together.

Bones:
  Root (0 -> 0.3 m: the root skirt stays planted), Trunk1 (0.3 -> 1.2, holds the mouth), Trunk2 (1.2 -> 1.9, eyes),
  Trunk3 (1.9 -> 2.4, where the limbs leave), Spire (2.4 -> 3.8, the pointed top);
  Limb<k>_1..3 for k = 0..5: six crown sectors at azimuths 0, 60, ..., 300 deg (0 = front, +60 = toward the
  character's left), each a three-bone chain from the trunk at z 2.2 out through the sector's limb mass (joints at the
  centroids of the sector's crown vertices at 0.5 and 1.0 m from the base, tail at the far 10 %);
  Jaw (lower lip + lower teeth), UpperLip (upper lip arc + upper teeth): translated to close/open the mouth;
  Socket_Mouth (non-deforming, ranged release).
Weights:
  trunk: smooth hat functions of height; root factor 1 below z 0.1 fading out by 0.6;
  crown: c = smoothstep of the distance outside the trunk radius r_t(z) and of z above 1.85; sector blend linear in
  azimuth between the two nearest sectors; along a chain by distance from the sector base (blend 0.15 m);
  mouth: lower lip piece 15 rises with Jaw by height (0 at z 0.3, 1 at 0.6) and less toward the corners; lower teeth
  0.85 Jaw; upper teeth 1.0 UpperLip; face bark just above the mouth opening follows UpperLip, fading out by z 1.25.
At most 4 influences, normalised. Writes work/joints.json and work/rig_v1.blend. Args: none"""
import bpy, os, math, json
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'step2.blend'))
body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
pa = np.zeros(nv, np.int32); me.attributes['part'].data.foreach_get('value', pa)


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- trunk
AX = [(0.0, (0, -0.15)), (1.2, (0, -0.15)), (1.9, (0, -0.10)), (2.4, (0, -0.03)), (3.8, (0, 0.0))]
TRUNK = {'Root': ((0, 0, 0), (0, -0.05, 0.3)), 'Trunk1': ((0, -0.05, 0.3), (0, -0.15, 1.2)),
         'Trunk2': ((0, -0.15, 1.2), (0, -0.10, 1.9)), 'Trunk3': ((0, -0.10, 1.9), (0, -0.03, 2.4)),
         'Spire': ((0, -0.03, 2.4), (0, 0, 3.8))}
RT = np.array([[0.0, 1.4], [0.4, 0.85], [0.8, 0.75], [1.2, 0.6], [1.6, 0.45], [2.0, 0.32], [2.4, 0.26], [3.8, 0.0]])
axy = np.stack([np.interp(co[:, 2], [a[0] for a in AX], [a[1][i] for a in AX]) for i in range(2)], 1)
d_ax = co[:, :2] - axy
r = np.linalg.norm(d_ax, axis=1); az = np.degrees(np.arctan2(co[:, 0], -co[:, 1]))
rt = np.interp(co[:, 2], RT[:, 0], RT[:, 1])
crown = ss((r - rt - 0.02) / 0.25) * ss((co[:, 2] - 1.85) / 0.25)
spire_piece = pv == 20
crown[spire_piece] = 0

names = ['Root', 'Trunk1', 'Trunk2', 'Trunk3', 'Spire']
z = co[:, 2]
hat = np.zeros((nv, 5))
rootf = 1 - ss((z - 0.1) / 0.5)
b12 = ss((z - 1.05) / 0.3); b23 = ss((z - 1.75) / 0.3); b3s = ss((z - 2.3) / 0.3)
hat[:, 0] = rootf
rest = 1 - rootf
hat[:, 1] = rest * (1 - b12)
hat[:, 2] = rest * b12 * (1 - b23)
hat[:, 3] = rest * b12 * b23 * (1 - b3s)
hat[:, 4] = rest * b12 * b23 * b3s
hat[spire_piece & (z > 2.45)] = [0, 0, 0, 0, 1]

# ---------------------------------------------------------------- crown sectors
NS = 6; SAZ = np.arange(NS) * 360.0 / NS; BASE_Z = 2.2
cm = crown > 0.3
chains = {}
for k in range(NS):
    a = math.radians(SAZ[k]); dirv = np.array([math.sin(a), -math.cos(a), 0])
    B = np.array([0, -0.06, BASE_Z]) + 0.25 * dirv
    dz = (az - SAZ[k] + 180) % 360 - 180
    sel = cm & (np.abs(dz) < 30)
    d = np.linalg.norm(co - B, axis=1)
    pts = [B]
    for lo, hi in ((0.35, 0.65), (0.85, 1.15)):
        m = sel & (d >= lo) & (d < hi)
        pts.append(co[m].mean(0) if m.sum() > 5 else pts[-1] + (pts[-1] - B if len(pts) > 1 else dirv * 0.5))
    far = sel & (d >= np.percentile(d[sel], 90))
    pts.append(co[far].mean(0))
    chains[k] = [list(map(float, p)) for p in pts]
    print('CHAIN', k, 'verts', int(sel.sum()), [np.round(p, 2).tolist() for p in pts])
for k in range(NS):
    names += [f'Limb{k}_{i}' for i in (1, 2, 3)]
names += ['Jaw', 'UpperLip']
gi = {n: i for i, n in enumerate(names)}
W = np.zeros((nv, len(names)))
W[:, :5] = hat * (1 - crown)[:, None]
# sector blend (linear in azimuth between the two nearest sectors)
step = 360.0 / NS
for k in range(NS):
    dz = np.abs((az - SAZ[k] + 180) % 360 - 180)
    ws = np.clip(1 - dz / step, 0, 1) * crown
    pts = np.array(chains[k]); B = pts[0]
    d = np.linalg.norm(co - B, axis=1)
    L1 = np.linalg.norm(pts[1] - pts[0]); L2 = L1 + np.linalg.norm(pts[2] - pts[1])
    t12 = ss((d - (L1 - 0.15)) / 0.3); t23 = ss((d - (L2 - 0.15)) / 0.3)
    W[:, gi[f'Limb{k}_1']] += ws * (1 - t12)
    W[:, gi[f'Limb{k}_2']] += ws * t12 * (1 - t23)
    W[:, gi[f'Limb{k}_3']] += ws * t12 * t23

# ---------------------------------------------------------------- mouth
x, y = co[:, 0], co[:, 1]
lip = pv == 15
wj = ss((z - 0.3) / 0.3) * (1 - 0.6 * ss((np.abs(x) - 0.25) / 0.3))
for m, w, bone in ((lip, wj, 'Jaw'), (pa == 2, np.full(nv, 0.85), 'Jaw'), (pa == 1, np.ones(nv), 'UpperLip')):
    W[m] *= (1 - w[m])[:, None]; W[m, gi[bone]] += w[m]
ul = (pv == 0) & (y < -0.45) & (np.abs(x) < 0.7) & (z > 0.85) & (z < 1.3)
wu = (1 - ss((z - 1.0) / 0.25)) * (1 - ss((np.abs(x) - 0.35) / 0.3)) * ul
W *= (1 - wu)[:, None]; W[:, gi['UpperLip']] += wu

# ---------------------------------------------------------------- limit and write
top = np.argsort(-W, 1)[:, :4]; W2 = np.zeros_like(W); rows = np.arange(nv)[:, None]
W2[rows, top] = W[rows, top]; W2 /= np.maximum(W2.sum(1, keepdims=True), 1e-9)
print('RIG unweighted', int((W.sum(1) < 1e-6).sum()), 'crown verts', int((crown > 0.5).sum()))
ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones
V = Vector
prev = None
for n in ('Root', 'Trunk1', 'Trunk2', 'Trunk3', 'Spire'):
    b = eb.new(n); b.head, b.tail = V(TRUNK[n][0]), V(TRUNK[n][1]); b.align_roll(V((0, -1, 0)))
    b.parent = prev; b.use_connect = prev is not None; prev = b
for k in range(NS):
    prev = eb['Trunk3']; pts = chains[k]
    for i in (1, 2, 3):
        b = eb.new(f'Limb{k}_{i}'); b.head, b.tail = V(pts[i - 1]), V(pts[i]); b.align_roll(V((0, 0, 1)))
        b.parent = prev; b.use_connect = i > 1; prev = b
for n, h in (('Jaw', (0, -0.45, 0.55)), ('UpperLip', (0, -0.45, 1.02))):
    b = eb.new(n); b.head = V(h); b.tail = V(h) + V((0, -0.4, 0)); b.align_roll(V((0, 0, 1))); b.parent = eb['Trunk1']
s = eb.new('Socket_Mouth'); s.head = V((0, -0.85, 0.8)); s.tail = V((0, -1.0, 0.8)); s.parent = eb['Trunk1']
s.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
body.vertex_groups.clear()
for n in names:
    body.vertex_groups.new(name=n)
for j, n in enumerate(names):
    g = body.vertex_groups[n]
    for i in np.nonzero(W2[:, j] > 1e-4)[0]:
        g.add([int(i)], float(W2[i, j]), 'REPLACE')
body.parent = rig
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
json.dump({'chains': chains, 'sector_azimuths': SAZ.tolist(), 'trunk': TRUNK}, open(os.path.join(HERE, 'work', 'joints.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
print('RIG saved bones', len(names) + 1)

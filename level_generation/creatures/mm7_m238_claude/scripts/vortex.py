"""The genie's vortex tail as a soft chain (she has no legs). Midline = per-height centroid of the vortex shell (P01)
from TOP (the hips, just below B_Pelvis) to the tip; N joints at equal height steps; bones Vortex_00..Vortex_<N-2>
(Vortex_00 parent B_Pelvis). Weights below TOP: the shell and the body's core cone go onto the chain by height (linear
hats between the joints, the last span on the last bone), blended over BLEND m into the Meshy hip weights above TOP.
Meshy's auto-rig put its legs inside the vortex: every leg weight (Thigh/Calf/Foot/Toe) anywhere moves to B_Pelvis
(above TOP) or the chain (below). The leg bones stay in the rig without weights (the clips never use them).
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
N = int(os.environ.get('VORTEX_JOINTS', '9'))
BLEND = float(os.environ.get('VORTEX_BLEND', '0.08'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
shell = pv == 1
TOP = rig.data.bones['B_Pelvis'].head_local.z - float(os.environ.get('TOP_BELOW_PELVIS', '0.04'))
zs = np.linspace(TOP, co[shell, 2].min(), N)
mid = []
for z in zs:
    m = shell & (np.abs(co[:, 2] - z) < 0.04)
    c = co[m].mean(0) if m.sum() > 5 else (mid[-1] if mid else np.array([0, 0, z]))
    mid.append(np.array([c[0], c[1], z]))
mid = np.array(mid); mid[-1] = co[shell][np.argmin(co[shell, 2])]
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
parent = eb['B_Pelvis']
names = []
for i in range(N - 1):
    b = eb.new(f'Vortex_{i:02d}'); b.head = Vector(mid[i]); b.tail = Vector(mid[i + 1]); b.parent = parent
    b.use_connect = i > 0; b.align_roll(Vector((0, -1, 0))); b.use_deform = True; parent = b; names.append(b.name)
bpy.ops.object.mode_set(mode='OBJECT')
gnames = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(gnames)}
W = np.zeros((nv, len(gnames)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
LEG = [gi[n] for n in gnames if any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe'))]
PEL = gi['B_Pelvis']
W[:, PEL] += W[:, LEG].sum(1); W[:, LEG] = 0
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
for n in names:
    body.vertex_groups.new(name=n); gnames.append(n)
W = np.hstack([W, np.zeros((nv, len(names)))]); gi = {n: i for i, n in enumerate(gnames)}
s = (TOP - co[:, 2]) / (TOP - zs[-1]) * (N - 1)                  # 0 at TOP, N-1 at the tip
chain = np.zeros((nv, len(names)))
for i in range(len(names)):
    chain[:, i] = np.clip(1 - np.abs(s - i), 0, 1)
chain[:, -1] += np.clip(s - (len(names) - 1), 0, 1)              # the last span (to the tip) on the last bone
chain /= np.maximum(chain.sum(1, keepdims=True), 1e-9)
ARMW = W[:, [gi[n] for n in gnames if any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]].sum(1)
below = (co[:, 2] < TOP + BLEND) & (((pv == 0) & (ARMW < 0.05)) | shell)   # the hands hang at hip height
a = np.clip((TOP + BLEND - co[:, 2]) / BLEND, 0, 1)             # 0 above TOP + BLEND, 1 at TOP and below
a[~below] = 0
a[shell & (co[:, 2] < TOP)] = 1
idx = [gi[n] for n in names]
W[:, idx] = chain * a[:, None]
W[:, :len(gnames) - len(names)] *= (1 - a)[:, None]
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for n in gnames:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(W[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(W[i, j]), 'REPLACE')
json.dump({'top': float(TOP), 'joints': mid.tolist(), 'bones': names}, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'vortex.json'), 'w'), indent=1)
print('VORTEX bones', len(names), 'top z', round(float(TOP), 3), 'tip z', round(float(mid[-1][2]), 3),
      'vertices on the chain', int((a > 0).sum()), 'leg weight moved (vertices)', 'all')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

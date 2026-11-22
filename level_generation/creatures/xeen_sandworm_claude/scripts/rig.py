"""Sand worm rig: work/clean_v2.blend + clean_v2.json -> work/rig_v1.blend + rig_v1.json.

Bones (forward -Y, up +Z, character left +X):
- Root (on the floor at the axis);
- Lobe0..Lobe5 (Root's children): six lobes of the sand mound around the axis (60 degrees apart, Lobe0 in front);
  the mound rises, falls and ripples by moving them (translation only, no scale: joints carry uniform scale only);
- Ring0 > Ring1 > Ring2 > Ring3 > Ring4 > Head: the body chain on the axis from the floor through the crease heights
  between the Meshy ring shells to the top of the head ring (which holds the maw);
- Lip0..Lip5 (Head's children): six points on the maw rim (the fang bases' circle), each pointing out along the maw
  normal; moving them out and tilting them opens the maw, the fangs flaring with them.
Weights:
- ring shells by piece (part/seg attributes), blended with the neighbouring shell where they touch (smoothstep over
  BL = 3.5 cm of distance to the other shell, 50/50 at contact), so a bend keeps the creases closed; spikes rigid on
  their ring;
- the head's maw region: a radial lip influence (0 deep in the gullet, 1 at the rim, back to 0 at 1.7 rims) shared
  among the lips by angle (cos^2 lobes); the fangs rigid on their nearest lip;
- the mound: a radial lobe influence (1 inside the worm's base radius, 0 at the rim, so the rim stays on the floor)
  shared among the lobes by angle; the rest on Root; each rock rigid with the mound weights under its centroid."""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector, Matrix, kdtree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work')
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, 'clean_v2.blend'))
J = json.load(open(os.path.join(W, 'clean_v2.json')))
mesh = bpy.data.objects['Worm']; me = mesh.data
co = np.array([v.co[:] for v in me.vertices]); nv = len(co)
vpart = np.full(nv, -1); vseg = np.full(nv, -9)
for p in me.polygons:
    for v in p.vertices:
        vpart[v] = me.attributes['part'].data[p.index].value
        vseg[v] = me.attributes['seg'].data[p.index].value
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lab = np.full(nv, -1); npc = 0
for v in bm.verts:
    if lab[v.index] >= 0: continue
    st = [v]; lab[v.index] = npc
    while st:
        x = st.pop()
        for e in x.link_edges:
            w = e.other_vert(x)
            if lab[w.index] < 0: lab[w.index] = npc; st.append(w)
    npc += 1
JZ = J['joints']; MAW = J['maw']; MD = J['mound']
mc = Vector(MAW['centre']); mn = Vector(MAW['normal']).normalized(); rim = MAW['rim']
e1 = Vector((1, 0, 0)) - mn * mn.x; e1.normalize(); e2 = mn.cross(e1).normalized()
R0, R1 = MD['R0'], MD['R1']
NL = 6
RINGS = ['Ring0', 'Ring1', 'Ring2', 'Ring3', 'Ring4', 'Head']

arm = bpy.data.armatures.new('Worm_Rig'); rig = bpy.data.objects.new('Worm_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, h, t, parent=None, connect=False, roll=Vector((0, -1, 0))):
    b = eb.new(name); b.head = Vector(h); b.tail = Vector(t); b.align_roll(Vector(roll))
    if parent:
        b.parent = eb[parent]; b.use_connect = connect
    return b


bone('Root', (0, 0, 0), (0, 0.2, 0), roll=(0, 0, 1))
LOBE_TH = [-math.pi / 2 + 2 * math.pi * k / NL for k in range(NL)]       # Lobe0 at -Y (front), then counter-clockwise
RL = (R0 + R1) / 2
for k, th in enumerate(LOBE_TH):
    p = Vector((RL * math.cos(th), RL * math.sin(th), 0.04))
    bone(f'Lobe{k}', p, p + Vector((0, 0, 0.08)), 'Root')
for i, name in enumerate(RINGS):
    bone(name, (0, 0, JZ[i]), (0, 0, JZ[i + 1]), 'Root' if i == 0 else RINGS[i - 1], i > 0)
LIP_PH = [2 * math.pi * k / NL for k in range(NL)]
LIPS = []
for k, ph in enumerate(LIP_PH):
    p = mc + (e1 * math.cos(ph) + e2 * math.sin(ph)) * rim
    radial = (p - mc).normalized()
    bone(f'Lip{k}', p, p + mn * 0.05, 'Head', roll=radial)
    LIPS.append(dict(name=f'Lip{k}', pos=list(p), radial=list(radial), phase=ph))
bpy.ops.object.mode_set(mode='OBJECT')


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


Wt = [dict() for _ in range(nv)]
# ---- rings: piece weights blended where shells touch -------------------------------------------------------------------
BL = 0.035
shell = (vpart == 0) | (vpart == 1)
trees = {}
for s in range(6):
    idx = np.where(shell & (vseg == s))[0]
    kd = kdtree.KDTree(len(idx))
    for j, v in enumerate(idx): kd.insert(co[v], j)
    kd.balance(); trees[s] = kd
for v in np.where(shell)[0]:
    s = int(vseg[v]); w = {RINGS[s]: 1.0}
    for nb in (s - 1, s + 1):
        if 0 <= nb < 6:
            _, _, d = trees[nb].find(co[v])
            if d < BL:
                a = 0.5 * float(ss(1 - d / BL))
                w[RINGS[s]] -= a; w[RINGS[nb]] = w.get(RINGS[nb], 0) + a
    Wt[v] = w
for v in np.where(vpart == 2)[0]:
    Wt[v] = {RINGS[int(vseg[v])]: 1.0}
# ---- maw: lips on the head region and the fangs ------------------------------------------------------------------------


def lip_angle(p):
    d = Vector(p) - mc; d = d - mn * d.dot(mn)
    return math.atan2(d.dot(e2), d.dot(e1)), d.length, (Vector(p) - mc).dot(mn)


def lip_share(ang):
    s = np.array([max(0.0, math.cos(ang - ph)) ** 2 for ph in LIP_PH]); return s / s.sum()


for v in np.where(vpart == 1)[0]:
    ang, rho, hn = lip_angle(co[v])
    if hn < -0.16 or rho > 1.7 * rim:
        continue
    if rho <= rim:
        f = float(ss((rho - 0.35 * rim) / (0.65 * rim)))
    else:
        f = float(ss(1 - (rho - rim) / (0.7 * rim)))
    f *= float(ss((hn + 0.16) / 0.06))
    if f < 1e-3:
        continue
    base = {k: x * (1 - f) for k, x in Wt[v].items()}
    for k, x in enumerate(lip_share(ang)):
        if x * f > 1e-3:
            base[f'Lip{k}'] = base.get(f'Lip{k}', 0) + x * f
    Wt[v] = base
fang_pieces = sorted(set(lab[vpart == 3]))
for pc in fang_pieces:
    idx = np.where(lab == pc)[0]
    ang, _, _ = lip_angle(co[idx].mean(0))
    k = int(np.argmax(lip_share(ang)))
    for v in idx:
        Wt[v] = {f'Lip{k}': 1.0}
# ---- mound and rocks ---------------------------------------------------------------------------------------------------


def lobe_share(th):
    s = np.array([max(0.0, math.cos(th - t)) ** 2 for t in LOBE_TH]); return s / s.sum()


def mound_w(p):
    r = math.hypot(p[0], p[1]); th = math.atan2(p[1], p[0])
    f = float(ss(1 - (r - R0) / (0.92 * R1 - R0))) if r > R0 else 1.0
    w = {'Root': 1 - f} if f < 1 else {}
    for k, x in enumerate(lobe_share(th)):
        if x * f > 1e-3:
            w[f'Lobe{k}'] = x * f
    return w


for v in np.where(vpart == 4)[0]:
    Wt[v] = mound_w(co[v]) if co[v][2] > 0.0005 else {'Root': 1.0}     # the bottom fan's centre stays on the floor
for pc in sorted(set(lab[vpart == 5])):
    idx = np.where(lab == pc)[0]
    w = mound_w(co[idx].mean(0))
    for v in idx:
        Wt[v] = dict(w)
groups = {}
for v, w in enumerate(Wt):
    tot = sum(w.values())
    for n, x in w.items():
        if x / tot > 1e-4:
            if n not in groups: groups[n] = mesh.vertex_groups.new(name=n)
            groups[n].add([v], float(x / tot), 'REPLACE')
empty = sum(1 for w in Wt if not w)
mesh.parent = rig
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
print('RIGGED bones', len(arm.bones), 'unweighted', empty, 'groups', len(groups), 'fang pieces', len(fang_pieces))
json.dump(dict(joints=JZ, maw=dict(centre=list(mc), normal=list(mn), e1=list(e1), e2=list(e2), rim=rim),
               lips=LIPS, lobes=[dict(name=f'Lobe{k}', theta=t) for k, t in enumerate(LOBE_TH)],
               mound=MD, rings=RINGS),
          open(os.path.join(W, 'rig_v1.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, 'rig_v1.blend'))

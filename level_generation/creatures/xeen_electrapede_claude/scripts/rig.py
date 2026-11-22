"""Electrapede rig (exoskeleton route of the quadruped playbook's segmented-creature section): reads
work/clean_v2.blend + clean_v2.json, writes work/rig_v1.blend and work/rig_v1.json (joint data for the clips).

Bones (forward -Y, up +Z, character left +X; every spine bone rolled so its Z axis is world up at rest):
- Root (ground, under the body centre) > Seg0 .. Seg14 (one per leg pair, head to tail, each from the plate boundary
  in front of its legs to the one behind) > Tail (the two leg-less tail plates and the cerci);
- Seg0 > Head > Jaw (the lower mouth parts) and Mandible_L/R (the front palps), Ant<k>_<side>[1,2] (antennae: two
  bones for the long ones, one for the short ones);
- Seg<j> > Femur<j>_<side> > Tibia<j>_<side> (every leg; Z axis = the leg plane's normal at rest).
Weights: plates and sockets by arc position along the spine (rigid inside a plate's span, smoothstep blend over 2.5 cm
either side of each plate boundary, so bending opens no gaps); head pieces and eyes rigid on Head, jaw/mandible/antenna
pieces rigid on their bones (antennae blended over their two bones by arc); each leg rigid on Femur up to its knee
ring, Tibia beyond, the knee ring half and half. Sockets for FX: Socket_Mouth (in front of the mouth, on Head) and
Socket_Antenna_L/R (the long antenna tips)."""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work')
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, 'clean_v2.blend'))
J = json.load(open(os.path.join(W, 'clean_v2.json')))
mesh = bpy.data.objects['Pede']; me = mesh.data
LEG_Y = J['leg_y']; N = len(LEG_Y)
co = np.array([v.co[:] for v in me.vertices])
nv = len(co)
vpart = np.full(nv, -1); vseg = np.full(nv, -9); vside = np.zeros(nv, int)
for p in me.polygons:
    for v in p.vertices:
        vpart[v] = me.attributes['part'].data[p.index].value
        vseg[v] = me.attributes['seg'].data[p.index].value
        vside[v] = me.attributes['side'].data[p.index].value
# connected pieces
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lab = np.full(nv, -1); npc = 0
for v in bm.verts:
    if lab[v.index] >= 0:
        continue
    st = [v]; lab[v.index] = npc
    while st:
        x = st.pop()
        for e in x.link_edges:
            w = e.other_vert(x)
            if lab[w.index] < 0:
                lab[w.index] = npc; st.append(w)
    npc += 1

# ---- spine joints -----------------------------------------------------------------------------------------------------
B = [LEG_Y[0] - (LEG_Y[1] - LEG_Y[0]) / 2] + [(LEG_Y[i - 1] + LEG_Y[i]) / 2 for i in range(1, N)] + \
    [LEG_Y[-1] + (LEG_Y[-1] - LEG_Y[-2]) / 2]
TAIL_END = float(co[:, 1].max())
plate = vpart == 0


def zmid(y, band=0.03):
    m = plate & (np.abs(co[:, 1] - y) < band)
    if m.sum() < 5:
        m = plate & (np.abs(co[:, 1] - y) < 0.08)
    return float((co[m, 2].min() + co[m, 2].max()) / 2)


JOINTS = [Vector((0, y, zmid(y))) for y in B] + [Vector((0, TAIL_END - 0.01, zmid(TAIL_END - 0.04, 0.05)))]
print('JOINTS', [(round(j.y, 3), round(j.z, 3)) for j in JOINTS])

# ---- head pieces ------------------------------------------------------------------------------------------------------
pieces = {}
for k in range(npc):
    idx = np.where(lab == k)[0]
    pieces[k] = dict(idx=idx, part=int(vpart[idx[0]]), c=co[idx].mean(0), mn=co[idx].min(0), mx=co[idx].max(0))
jaw = [k for k, p in pieces.items() if p['part'] == 1 and p['c'][1] < -1.06 and p['c'][2] < 0.15 and abs(p['c'][0]) < 0.08]
mand = [k for k, p in pieces.items() if p['part'] == 1 and p['c'][1] < -1.0 and p['c'][2] < 0.17 and abs(p['c'][0]) >= 0.08
        and p['mx'][0] - p['mn'][0] < 0.16]
ants = [k for k, p in pieces.items() if p['part'] == 3]
print('JAW', [(k, pieces[k]['c'].round(3).tolist()) for k in jaw])
print('MANDIBLES', [(k, pieces[k]['c'].round(3).tolist()) for k in mand])
HEAD_C = Vector((0, -1.02, 0.21))

arm = bpy.data.armatures.new('Pede_Rig'); rig = bpy.data.objects.new('Pede_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, h, t, parent=None, connect=False, roll=Vector((0, 0, 1))):
    b = eb.new(name); b.head = Vector(h); b.tail = Vector(t); b.align_roll(Vector(roll))
    if parent:
        b.parent = eb[parent]; b.use_connect = connect
    return b


bone('Root', (0, 0, 0), (0, 0.25, 0))
for i in range(N):
    bone(f'Seg{i}', JOINTS[i], JOINTS[i + 1], 'Root' if i == 0 else f'Seg{i - 1}', i > 0)
bone('Tail', JOINTS[N], JOINTS[N + 1], f'Seg{N - 1}', True)
bone('Head', JOINTS[0], Vector((0, -1.13, 0.20)), 'Seg0')
JAW_H = Vector((0, -1.06, 0.15))
if jaw:
    jc = np.mean([pieces[k]['c'] for k in jaw], 0)
    bone('Jaw', JAW_H, Vector((0, jc[1] - 0.03, jc[2] - 0.01)), 'Head')
MAND = {}
for k in mand:
    p = pieces[k]; sd = 1 if p['c'][0] > 0 else -1; s = 'L' if sd > 0 else 'R'
    pts = co[p['idx']]
    inner = pts[np.argmin(np.abs(pts[:, 0]))]; outer = pts[np.argmax(np.abs(pts[:, 0]))]
    bone(f'Mandible_{s}', inner, outer, 'Head'); MAND[k] = f'Mandible_{s}'
ANT = {}; ANT_TIPS = {}
for k in sorted(ants, key=lambda k: pieces[k]['c'][0]):
    p = pieces[k]; pts = co[p['idx']]
    base = pts[np.argmin(np.linalg.norm(pts - np.array(HEAD_C), axis=1))]
    tip = pts[np.argmax(np.linalg.norm(pts - base, axis=1))]
    L = float(np.linalg.norm(tip - base)); sd = 1 if p['c'][0] > 0 else -1; s = 'L' if sd > 0 else 'R'
    n = sum(1 for v in ANT.values() if v['side'] == s)
    name = f'Ant{n}_{s}'
    if L > 0.2:
        mid = base + (tip - base) * 0.45
        bone(name + '1', base, mid, 'Head', roll=(0, -1, 0)); bone(name + '2', mid, tip, name + '1', True, roll=(0, -1, 0))
        ANT[k] = dict(side=s, bones=[name + '1', name + '2'], base=base, tip=tip, L=L)
    else:
        bone(name + '1', base, tip, 'Head', roll=(0, -1, 0))
        ANT[k] = dict(side=s, bones=[name + '1'], base=base, tip=tip, L=L)
print('ANTENNAE', [(v['bones'], round(v['L'], 3)) for v in ANT.values()])
LEGB = {}
for leg in J['legs']:
    j, sd = leg['seg'], leg['side']; s = 'L' if sd > 0 else 'R'
    H, K, F = Vector(leg['hip']), Vector(leg['knee']), Vector(leg['foot'])
    nrm = (K - H).cross(F - K).normalized()
    if nrm.z < 0:
        nrm = -nrm
    bone(f'Femur{j}_{s}', H, K, f'Seg{j}', roll=nrm)
    bone(f'Tibia{j}_{s}', K, F, f'Femur{j}_{s}', True, roll=nrm)
    LEGB[(j, sd)] = (f'Femur{j}_{s}', f'Tibia{j}_{s}', H, K, F)
bpy.ops.object.mode_set(mode='OBJECT')

# ---- weights ----------------------------------------------------------------------------------------------------------
groups = {}


def g(name):
    if name not in groups:
        groups[name] = mesh.vertex_groups.new(name=name)
    return groups[name]


W8 = [dict() for _ in range(nv)]


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


BL = 0.025
spine_names = [f'Seg{i}' for i in range(N)] + ['Tail']
JY = [j.y for j in JOINTS]
for v in np.where((vpart == 0) | (vpart == 5) | (vpart == 6))[0]:
    y = co[v, 1]
    i = int(np.clip(np.searchsorted(JY, y) - 1, 0, N))       # span index (0..N)
    w = {spine_names[i]: 1.0}
    # blend toward the neighbour across the nearest boundary
    if i > 0 and y - JY[i] < BL:
        a = float(ss((y - JY[i] + BL) / (2 * BL)))
        w = {spine_names[i]: a, spine_names[i - 1]: 1 - a}
    elif i < N and JY[i + 1] - y < BL:
        a = float(ss((JY[i + 1] - y + BL) / (2 * BL)))
        w = {spine_names[i]: a, spine_names[i + 1]: 1 - a}
    if vpart[v] == 5:                                            # sockets: rigid with their own segment
        w = {f'Seg{vseg[v]}': 1.0}
    if vpart[v] == 6:
        w = {'Tail': 1.0}
    W8[v] = w
for v in np.where((vpart == 1) | (vpart == 2))[0]:
    W8[v] = {'Head': 1.0}
for k in jaw:
    for v in pieces[k]['idx']:
        W8[v] = {'Jaw': 1.0}
for k, name in MAND.items():
    for v in pieces[k]['idx']:
        W8[v] = {name: 1.0}
for k, a in ANT.items():
    for v in pieces[k]['idx']:
        if len(a['bones']) == 1:
            W8[v] = {a['bones'][0]: 1.0}
        else:
            t = np.linalg.norm(co[v] - a['base']) / a['L']
            u = float(ss((t - 0.35) / 0.2))
            W8[v] = {a['bones'][0]: 1 - u, a['bones'][1]: u}
for v in np.where(vpart == 4)[0]:
    fem, tib, H, K, F = LEGB[(int(vseg[v]), int(vside[v]))]
    p = Vector(co[v])
    d = (K - H); t = (p - H).dot(d) / d.length_squared
    # knee ring: distance to K small and along-femur parameter near 1
    dk = (p - K).length
    if dk < 0.02:
        W8[v] = {fem: 0.5, tib: 0.5}
    elif t < 1.0:
        W8[v] = {fem: 1.0}
    else:
        W8[v] = {tib: 1.0}
for v, w in enumerate(W8):
    for n, x in w.items():
        if x > 1e-4:
            g(n).add([v], float(x), 'REPLACE')
empty = sum(1 for w in W8 if not w)
mesh.parent = rig
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
print('RIGGED bones', len(arm.bones), 'unweighted', empty, 'groups', len(groups))

# ---- FX sockets ---------------------------------------------------------------------------------------------------------


def socket(name, bone_name, world):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.empty_display_size = 0.03
    e.parent = rig; e.parent_type = 'BONE'; e.parent_bone = bone_name
    bpy.context.view_layer.update()
    pb = rig.pose.bones[bone_name]
    # BONE parenting places the child relative to the bone's tail
    e.matrix_world = Matrix.Translation(world)
    return e


bpy.context.view_layer.update()
mouth = Vector((0, float(co[(vpart == 1)][:, 1].min()) - 0.03, 0.15))
socket('Socket_Mouth', 'Head', mouth)
for k, a in ANT.items():
    if len(a['bones']) == 2:
        socket(f'Socket_Antenna_{a["side"]}', a['bones'][1], Vector(a['tip']))
bpy.context.view_layer.update()
print('SOCKETS', [(o.name, [round(x, 3) for x in o.matrix_world.translation]) for o in bpy.data.objects if o.name.startswith('Socket')])
json.dump(dict(joints=[list(j) for j in JOINTS], legs=J['legs'], leg_y=LEG_Y,
               antennae={v['bones'][0]: dict(bones=v['bones'], base=list(map(float, v['base'])),
                                             tip=list(map(float, v['tip']))) for v in ANT.values()},
               jaw=bool(jaw), mandibles=list(MAND.values())),
          open(os.path.join(W, 'rig_v1.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, 'rig_v1.blend'))

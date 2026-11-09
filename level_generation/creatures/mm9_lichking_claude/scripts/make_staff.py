"""The Lich King's staff as new parts 'staff' (shaft, crook, bands, butt cap) and 'sskull' (the Lich's skull with its UVs on the Lich head set, small, hanging from the crook), built
in our bind along the grip axis (rig.json['grip']) with MM9's lengths (butt 0.62 m behind the fist, crook top 0.68 m ahead). MM9's staff keeps a
45 deg forward tilt in its bind: the crook bends to MM9's world-down side and the skull hangs along MM9's world down, carried into our bind by the
same rotation that carries MM9's staff axis onto ours. Blender frame. Args: <asm npz> <rig json> <skull npz> <out npz>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
IN, RIG, SK, OUT = sys.argv[sys.argv.index('--') + 1:]
D = np.load(IN); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
R = json.load(open(RIG)); GR = R['grip']
def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
def frame(x_, b_):
    x_ = unit(x_); z_ = unit(np.cross(x_, b_)); return np.c_[x_, np.cross(z_, x_), z_]
Dm = frame(GR['axis'], GR['finger_dir']) @ frame(GR['mm9_axis'], GR['mm9_dir']).T       # MM9 bind directions -> ours
a = unit(GR['axis']); G = np.array(GR['point'])
um = unit(GR['mm9_axis']); hm = np.array([0, 0, -1.0]) - np.array([0, 0, -1.0]) @ um * um; hm = unit(hm)
h = Dm @ hm; down = Dm @ np.array([0, 0, -1.0]); fwd = Dm @ np.array([0, -1.0, 0])
RS = 0.0165; SIDES = 10
def ring(c, t, r, b0):
    b1 = unit(np.cross(t, b0)); b0 = unit(np.cross(b1, t))
    return [c + r * (np.cos(k * 2 * np.pi / SIDES) * b0 + np.sin(k * 2 * np.pi / SIDES) * b1) for k in range(SIDES)]
# centre line: butt -> top of the shaft (r2: MM9's head sits ON the shaft, 0.45 m above the fist; the r1 crook with a hanging skull reached
# 23 cm higher than MM9's staff and read as a shepherd's crook)
L_BACK, L_TOP = 0.619, 0.45
pts = [G - a * L_BACK + a * t for t in np.linspace(0, L_BACK + L_TOP, 13)]
radii = [0.021, 0.021, 0.0165] + [RS] * 9 + [0.019]
pts = np.array(pts)
# bands: thicker rings near the fist and below the crook
band_at = {9: 0.0195, 11: 0.0205, 12: 0.022}
verts = []; faces = []; b0 = h
for i, p in enumerate(pts):
    t = unit(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
    verts += ring(p, t, band_at.get(i, radii[i]), b0)
for i in range(len(pts) - 1):
    for k in range(SIDES):
        a0, a1 = i * SIDES + k, i * SIDES + (k + 1) % SIDES
        faces.append([a0, a1, a1 + SIDES]); faces.append([a0, a1 + SIDES, a0 + SIDES])
# caps
for idx, p, out in ((0, pts[0], True), (len(pts) - 1, pts[-1], False)):
    ci = len(verts); verts.append(p)
    for k in range(SIDES):
        q0, q1 = idx * SIDES + k, idx * SIDES + (k + 1) % SIDES
        faces.append([ci, q1, q0] if out else [ci, q0, q1])
staff_v = np.array(verts); staff_t = np.array(faces)
# skull: the Lich's, merged at its UV seams, reduced, small, hanging from the crook tip along MM9's down
S = np.load(SK); sc, st = S['co'], S['tri']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('s'); me.from_pydata(sc.tolist(), [], st.tolist()); me.update()
o = bpy.data.objects.new('s', me); bpy.context.scene.collection.objects.link(o)
uvl = me.uv_layers.new(name='UVMap'); suv = S['uv']
for lp in me.loops: uvl.data[lp.index].uv = (suv[lp.vertex_index][0], suv[lp.vertex_index][1])
bpy.context.view_layer.objects.active = o; o.select_set(True)
m = o.modifiers.new('d', 'DECIMATE'); m.ratio = 440 / len(me.polygons); m.use_symmetry = True; m.symmetry_axis = 'X'; m.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='d')
me.calc_loop_triangles()
q = np.array([v.co[:] for v in me.vertices]); qt = np.array([lt.vertices[:] for lt in me.loop_triangles])
quv = np.zeros((len(q), 2)); uvd = me.uv_layers.active.data
for lt in me.loop_triangles:
    for vi, li in zip(lt.vertices, lt.loops): quv[vi] = uvd[li].uv[:]
SC = 0.6
q = (q - [0.5 * (q[:, 0].min() + q[:, 0].max()), 0.5 * (q[:, 1].min() + q[:, 1].max()), q[:, 2].max()]) * SC    # top centre at the origin
up = a.copy(); f_ = unit(fwd - up * (fwd @ up))                     # skull upright on the staff, face to MM9's forward
Rk = np.c_[np.cross(-f_, up), -f_, up]
tip = pts[-1]
q = q @ Rk.T                                                          # top centre at the origin
q = q + tip + up * (-(q @ up).min() - 0.005)                           # jaw on the shaft's collar
print('STAFF tris', len(staff_t), 'skull tris', len(qt), 'tip', tip.round(3), 'butt', pts[0].round(3), 'skull top', (q @ up).max().round(3))
# crown cap: the Meshy crown is an open ring; MM9's is closed over the head. A shallow dark dome on the ring's inner edge at z 1.541
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from meshlib import section
ct = tri[comp[tri[:, 0]] == names.index('crown')]
L = sorted([l for l in section(co, ct, np.array([0, 0, 1.541]), np.array([0, 0, 1.0])) if l['per'] > 0.3], key=lambda l: l['per'])[0]
c0 = L['c'].copy(); ang = np.arctan2(L['pts'][:, 1] - c0[1], L['pts'][:, 0] - c0[0]); P = L['pts'][np.argsort(ang)]
step = max(1, len(P) // 24); P = P[::step]; P = c0 + (P - c0) * (1 - 0.003 / np.maximum(np.linalg.norm(P - c0, axis=1, keepdims=True), 1e-6))
mid = c0 + (P - c0) * 0.6 + np.array([0, 0, 0.006]); cap_v = np.vstack([P, mid, c0 + [0, 0, 0.010]]); n_ = len(P); cap_t = []
for k in range(n_):
    a0, a1 = k, (k + 1) % n_; b0, b1 = n_ + k, n_ + (k + 1) % n_
    cap_t += [[a0, a1, b1], [a0, b1, b0], [b0, b1, 2 * n_]]
cap_t = np.array(cap_t)
fn = np.cross(cap_v[cap_t[:, 1]] - cap_v[cap_t[:, 0]], cap_v[cap_t[:, 2]] - cap_v[cap_t[:, 0]])
if fn[:, 2].mean() < 0: cap_t = cap_t[:, ::-1]
print('CAP', len(cap_t), 'tris, ring', len(P))
# tube caps (r5): the open rims of the upper-arm tubes, the trousers and the gauntlets' wrists, closed by a fan on the dark steel strip, so a rim
# that leaves its cover in a pose shows a dark end, not the hollow inside
tc_v = []; tc_t = []; tc_src = []
for pn in ('uarms', 'pants', 'hands'):
    t = tri[comp[tri[:, 0]] == names.index(pn)]
    e = np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]); es = np.sort(e, 1); u_, inv_, c_ = np.unique(es, axis=0, return_inverse=True, return_counts=True)
    bd = e[c_[inv_] == 1]                                                # boundary edges, oriented as in their face
    nxt = {int(a_): int(b_) for a_, b_ in bd}; seen = set()
    for st in list(nxt):
        if st in seen: continue
        loop = [st]; seen.add(st); x = nxt.get(st)
        while x is not None and x != st and x not in seen and len(loop) < 400: loop.append(x); seen.add(x); x = nxt.get(x)
        if x != st or len(loop) < 3: continue
        b0 = len(tc_v); c = co[loop].mean(0); tc_v += [co[i] for i in loop] + [c]; tc_src += loop + [loop[0]]
        k = len(loop)
        for j in range(k): tc_t.append([b0 + (j + 1) % k, b0 + j, b0 + k])          # reversed: the cap faces out of the hole
tc_v = np.array(tc_v); tc_t = np.array(tc_t)
print('TUBECAPS', len(tc_t), 'tris')
Co = [co, staff_v, q]; base = len(co)
Tr = [tri, staff_t + base, qt + base + len(staff_v)]
Pa = [comp, np.full(len(staff_v), len(names)), np.full(len(q), len(names) + 1)]
Co.append(cap_v); Tr.append(cap_t + base + len(staff_v) + len(q)); Pa.append(np.full(len(cap_v), len(names) + 2))
b3 = base + len(staff_v) + len(q) + len(cap_v); Co.append(tc_v); Tr.append(tc_t + b3); Pa.append(np.full(len(tc_v), len(names) + 3))
np.savez(OUT, co=np.vstack(Co), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names + ['staff', 'sskull', 'cap', 'tubecap']), tubecap_src=np.array(tc_src), sskull_uv=quv, staff_rings=np.array([len(pts), SIDES]))

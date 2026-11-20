"""Copies of the painted skull (head faces without the ember eyes, their head-set UVs kept): the HELD skull in the left hand
(work/held_skull.json from grip_sk.py) and the necklace PENDANT (pend_at from assemble_sk.py), each reduced with its UVs. Appended as parts
'heldskull' and 'pendant' to both the asm npz (positions, for the weights) and the UV mesh npz (positions + UVs, orig -> the new asm verts).
Args: <asm npz> <uv mesh npz> <out asm npz> <out uv npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
A_, U_, OA, OU = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
A = dict(np.load(A_)); U = dict(np.load(U_)); names = [str(x) for x in A['names']]
H = json.load(open(os.path.join(os.path.dirname(OA), 'held_skull.json')))
hk = names.index('head'); skk = float(A['skull_k']); eye = np.asarray(A['skull_eye'], float)
ut, uu, uo = U['tri'], U['uv'], U['orig']
fsel = (U['comp'][ut[:, 0]] == hk) & (A['head_label'][uo[ut[:, 0]]] != 3) & (U['mat'] == 1)
ft = ut[fsel]
bpy.ops.wm.read_factory_settings(use_empty=True)


def make(name, xform, target):
    used, inv = np.unique(uo[ft], return_inverse=True); vt = inv.reshape(-1, 3)
    P = A['co'][used]; loc = (P - eye) / skk
    me = bpy.data.meshes.new(name); me.from_pydata(xform(loc).tolist(), [], vt.tolist()); me.update()
    uvl = me.uv_layers.new(name='UVMap')
    for p_, f in zip(me.polygons, ft):
        for li, ci in zip(p_.loop_indices, f): uvl.data[li].uv = uu[ci]
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    for x in bpy.data.objects: x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
    md = o.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = target / len(ft); md.use_collapse_triangulate = True
    md.delimit = {'UV'}
    bpy.ops.object.modifier_apply(modifier='d'); me = o.data; me.calc_loop_triangles()
    co_ = np.array([v.co[:] for v in me.vertices]); uvd = me.uv_layers['UVMap'].data
    tris = [[(me.loops[l].vertex_index, tuple(uvd[l].uv)) for l in lt.loops] for lt in me.loop_triangles]
    print('COPY', name, len(ft), '->', len(tris)); return co_, tris


Rh = np.array(H['R']); ch = np.array(H['centre']); bm_ = np.array(H['box_mid'])
held = make('heldskull', lambda l: (l * H['scale'] - bm_) @ Rh.T + ch, int(E('B_HELD', '1100')))
pw = E('PEND_W', '0.045') / float(np.ptp(((A['co'][A['comp'] == hk] - eye) / skk)[:, 0]))
pa = np.asarray(A['pend_at'], float)
tilt = np.radians(E('PEND_TILT', '12')); Rx = np.array([[1, 0, 0], [0, np.cos(tilt), -np.sin(tilt)], [0, np.sin(tilt), np.cos(tilt)]])
pend = make('pendant', lambda l: (l * pw) @ Rx.T + pa, int(E('B_PEND', '320')))
# the held skull's empty eye sockets showed the background through the open skull (see-through gate, sleeve L 22 px): a small sphere
# behind each socket, every vertex on the darkest head-set texel of the skull's own paint (the socket's shadow)
img = bpy.data.images.load(os.path.abspath(os.path.join(os.path.dirname(OA), '..', 'textures', 'sk_head_raw.png')))
W_, H_ = img.size; px = np.array(img.pixels[:], np.float32).reshape(H_, W_, 4)[::-1]
tex = px[..., :3].mean(2) * 255
cv = np.unique(ut[fsel & (A['head_label'][uo[ut[:, 0]]] == 0)])
lum = tex[np.clip(((1 - uu[cv, 1]) * tex.shape[0]).astype(int), 0, tex.shape[0] - 1), np.clip((uu[cv, 0] * tex.shape[1]).astype(int), 0, tex.shape[1] - 1)]
duv = tuple(uu[cv[np.argmin(lum)]]); print('DARK texel', duv, lum.min())
eyes = A['co'][(A['comp'] == hk) & (A['head_label'] == 3)]; el = (eyes - eye) / skk
xf = lambda l: (l * H['scale'] - bm_) @ Rh.T + ch
c_h, t_h = held; n0 = len(c_h); extra_c = []; extra_t = []
for sgn in (1, -1):
    side = el[el[:, 0] * sgn > 0]; cen = side.mean(0); r = float(np.linalg.norm(side - cen, axis=1).max()) * 1.6
    for i in range(6):
        for j in range(8):
            th = np.pi * (i + 0.5) / 6; ph = 2 * np.pi * j / 8
            extra_c.append(xf(cen + r * np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])[None])[0])
    b0 = n0 + len(extra_c) - 48
    for i in range(5):
        for j in range(8):
            a_, b_ = b0 + i * 8 + j, b0 + i * 8 + (j + 1) % 8
            extra_t.append([(a_, duv), (b_ + 8, duv), (b_, duv)]); extra_t.append([(a_, duv), (a_ + 8, duv), (b_ + 8, duv)])
held = (np.vstack([c_h, np.array(extra_c)]), t_h + extra_t); print('SOCKET fill tris', len(extra_t))
for nm, (c_, tris) in (('heldskull', held), ('pendant', pend)):
    k = len(names); names.append(nm); a0 = len(A['co']); u0 = len(U['co'])
    A['co'] = np.vstack([A['co'], c_]); A['comp'] = np.r_[A['comp'], np.full(len(c_), k)]
    A['hand_piece'] = np.r_[A['hand_piece'], np.full(len(c_), -100000)]; A['head_label'] = np.r_[A['head_label'], np.full(len(c_), 4)]
    A['tri'] = np.vstack([A['tri'], np.array([[v for v, _ in t] for t in tris]) + a0])
    keys = {}; nco = []; nuv = []; nor = []; nt = []
    for t in tris:
        row = []
        for v, uvv in t:
            kk = (v, round(uvv[0], 6), round(uvv[1], 6))
            if kk not in keys: keys[kk] = len(nco); nco.append(c_[v]); nuv.append(uvv); nor.append(a0 + v)
            row.append(u0 + keys[kk])
        nt.append(row)
    U['co'] = np.vstack([U['co'], nco]); U['uv'] = np.vstack([U['uv'], nuv]); U['orig'] = np.r_[U['orig'], nor]
    U['tri'] = np.vstack([U['tri'], nt]); U['mat'] = np.r_[U['mat'], np.ones(len(nt), int)]; U['comp'] = np.r_[U['comp'], np.full(len(nco), k)]
    if 'inner' in U: U['inner'] = np.r_[U['inner'], np.zeros(len(nt), bool)]
    for key in ('hand_piece', 'head_label'):
        if key in U: U[key] = np.r_[U[key], A[key][np.array(nor)]]
A['names'] = np.array(names); U['names'] = np.array(names)
np.savez(OA, **A); np.savez(OU, **U); print('SAVED', len(A['co']), len(U['co']), len(U['tri']))

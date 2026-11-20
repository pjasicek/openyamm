"""Pass 7 step D: Fre's mesh npz (build_glb_pf.py format) with the new head. Body = r72's final positions/UVs (work/uv_tex2.npz, after
geo_chain_fre.sh) without F1's face shell ('head'), its hidden old hood ('scarf') and PeasantF2's hair cap (the 'hair2' faces outside the
braid tube). Kept from 'hair2': the braid tube (asm 'hair2_tube'), renamed component 'braid2' on material FreHair; its upper part is moved
into the new hair at the nape (BRAID_DY at the top, fading to 0 at BRAID_Z1). New component 'nhead' on material FreHead: work/nh/head_uv.npz
(split at UV seams, src -> work/nh/head_geo.npz vertex).
Weights: body and braid r72's (work/weights.npz); new head: face/skull/neck, hair and eyes rigid on Head, except the new neck's lowest
NECK_EASE m above the bridge, which eases from r72's neck weights at the cut ring (nearest ring vertex) to Head; r72's neck band keeps its
own weights (interpolated where the cut bisected it). Four influences, normalised.
Outputs: work/nh/asm_nh.npz, work/nh/weights_nh.npz. Textures: FreHead -> textures/nh_head_{base,normal,orm}.png."""
import os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(HERE)
E = os.environ.get
BRAID_DY, BRAID_Z1 = float(E('BRAID_DY', '-0.068')), float(E('BRAID_Z1', '0.45')); NECK_EASE = float(E('NECK_EASE', '0.02'))
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
R = np.load('work/uv_tex2.npz'); W = np.load('work/weights.npz'); A = np.load('work/asm_frozen.npz')
G = np.load('work/nh/head_geo.npz'); U = np.load('work/nh/head_uv.npz')
names = [str(x) for x in R['names']]; wnames = [str(x) for x in W['wnames']]; NB = len(wnames); HEAD = wnames.index('FHP Head')
co, tri, uv, orig, mat, comp, inner = R['co'], R['tri'], R['uv'], R['orig'], R['mat'], R['comp'], R['inner']
tube = (comp == names.index('hair2')) & A['hair2_tube'][orig]
drop = np.isin(comp, [names.index('head'), names.index('scarf')]) | ((comp == names.index('hair2')) & ~tube)
keepf = ~drop[tri].any(1)
used = np.unique(tri[keepf]); remap = -np.ones(len(co), int); remap[used] = np.arange(len(used))
bco, btri, buv, bmat, binner = co[used].copy(), remap[tri[keepf]], uv[used], mat[keepf], inner[keepf]
bcomp = comp[used].copy(); bwj, bww = W['wj'][orig[used]], W['ww'][orig[used]]
# no 'hair2' in the names: build_glb_pf.py's PeasantF2-hair normal steps stay off
names2 = [('hair2_old' if n == 'hair2' else n) for n in names] + ['nhead', 'braid2']; NH, BR = names2.index('nhead'), names2.index('braid2')
bt = tube[used]; bcomp[bt] = BR
z = bco[bt, 2]; zt = z.max(); f = ss(z, BRAID_Z1, zt)
bco[bt, 1] += BRAID_DY * f
print('BODY verts', len(bco), 'faces', len(btri), '| braid verts', int(bt.sum()), 'top z', round(float(zt), 4), 'moved', BRAID_DY)
# new head
hco, htri, huv, src = U['co'], U['tri'], U['uv'], U['src']
gpiece, old_dense = G['piece'], G['old_dense']; Z0, Y0, SL, GAP = float(G['z0']), float(G['y0']), float(G['slope']), float(G['gap'])
pn = np.array([0, -SL, 1.0]); pn /= np.linalg.norm(pn); gco = G['co']
h = (gco - np.array([0, Y0, Z0])) @ pn
dense = np.zeros((len(gco), NB)); dense[:, HEAD] = 1.0
old = gpiece == 3; dense[old] = old_dense[old]
ring_o = G['ring_old']
d2 = ((gco[:, None, :] - gco[ring_o][None]) ** 2).sum(2); near = ring_o[np.argmin(d2, 1)]
ease = (gpiece == 0) & (h < GAP + NECK_EASE)
t = ss(h[ease], GAP, GAP + NECK_EASE)[:, None]
dense[ease] = old_dense[near[ease]] * (1 - t) + dense[ease] * t
print('HEAD weights: r72 neck', int(old.sum()), 'eased neck', int(ease.sum()), 'rigid Head', int(((gpiece != 3) & ~ease).sum()))
o4 = np.argsort(-dense, 1)[:, :4]; w4 = np.take_along_axis(dense, o4, 1); w4 /= w4.sum(1, keepdims=True)
hwj, hww = o4[src], w4[src].astype(np.float32)
# round 2 (orchestrator on r76: the eyes read startled, white above the iris): calmer, slightly heavy upper lids. The upper lid (face piece,
# front of the eye) moves down by up to LID_D at the middle of the opening, cos^2 across the eye's width (0 at the corners), full on the
# lid rim rows and fading to 0 at the brow and toward the lower lid (smoothstep); vertices that would enter the eyeball (ellipsoid from
# its extents) are pushed back onto it + LID_GAP. UVs travel with the vertices, so the painted lash line and lid crease follow the rim.
# Symmetric (same field mirrored). Geometry after the paint: deliberate, the lid texels only stretch by up to LID_D.
LID_D, LID_GAP = float(E('LID_D', '0.0032')), float(E('LID_GAP', '0.0006'))
EC, ER = np.array([0.0288, -0.0969, 0.6839]), np.array([0.0134, 0.0122, 0.0131])
def lids(p, face):
    p = p.copy(); ax = np.abs(p[:, 0]); sg = np.sign(p[:, 0])
    u = np.clip((ax - 0.0305) / 0.0175, -1, 1); cu = np.cos(np.pi / 2 * u) ** 2
    v = p[:, 2] - 0.6927
    wv = ss(v, -0.0085, -0.0050) * (1 - ss(v, 0.0005, 0.0085))
    wy = 1 - ss(p[:, 1], -0.098, -0.090)
    w = cu * wv * wy * face * (ax > 0.010) * (ax < 0.050)
    c = np.c_[EC[0] * sg, np.full(len(p), EC[1]), np.full(len(p), EC[2])]
    d0 = np.linalg.norm((p - c) / ER, axis=1)
    p[:, 2] -= LID_D * w
    q = (p - c) / ER; d1 = np.linalg.norm(q, axis=1); lim = 1 + LID_GAP / ER.mean()
    push = (w > 0) & (d0 >= lim) & (d1 < lim)
    p[push] = c[push] + ER * q[push] / d1[push, None] * lim
    print('LIDS moved', int((w > 0.01).sum()), 'pushed onto the eyeball', int(push.sum()), 'max', round(float(LID_D * w.max()) * 1000, 2), 'mm')
    return p
gco_l = lids(gco, (gpiece == 0).astype(float))
hco = gco_l[src].copy()
# tiny closed hair bits left by the parting repair (two 18-triangle zero-volume flaps at the hairline, check_winding's inverted part): dropped
par = np.arange(len(gco))
def fnd(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t_ in G['tri']: r_ = fnd(t_[0]); par[fnd(t_[1])] = r_; par[fnd(t_[2])] = r_
groot = np.array([fnd(i) for i in range(len(gco))]); gsize = np.bincount(groot[G['tri'][:, 0]], minlength=len(gco))
tiny = (gsize[groot[src[htri[:, 0]]]] < 30) & (gpiece[src[htri[:, 0]]] == 1)
htri = htri[~tiny]; print('HEAD tiny hair bits dropped', int(tiny.sum()), 'faces')
# assemble
n0 = len(bco)
co2 = np.vstack([bco, hco]); tri2 = np.vstack([btri, htri + n0]); uv2 = np.vstack([buv, huv]); mat2 = np.r_[bmat, np.ones(len(htri), int)]
comp2 = np.r_[bcomp, np.full(len(hco), NH)]; inner2 = np.r_[binner, np.zeros(len(htri), bool)]
wj2 = np.vstack([bwj, hwj]); ww2 = np.vstack([bww, hww]).astype(np.float32)
tex = json.loads(str(R['textures'])); tex['FreHair'] = dict(tex['FreHair'], base='textures/nh_braid_base.png'); tex['FreHead'] = {'base': 'textures/nh_head_base.png', 'normal': 'textures/nh_head_normal.png', 'orm': 'textures/nh_head_orm.png'}
np.savez('work/nh/asm_nh.npz', co=co2, tri=tri2, uv=uv2, orig=np.arange(len(co2)), mat=mat2, comp=comp2, inner=inner2, names=np.array(names2),
         matnames=R['matnames'], textures=json.dumps(tex), head_src=np.r_[-np.ones(n0, int), src], head_piece=np.r_[-np.ones(n0, int), gpiece[src]])
np.savez('work/nh/weights_nh.npz', wj=wj2, ww=ww2, wnames=W['wnames'])
print('ASM verts', len(co2), 'faces', len(tri2), 'per material', np.bincount(mat2).tolist())

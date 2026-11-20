"""Final mesh for build_glb: vertices split by UV. Args: <joined npz> <weights npz> <uv npz> <out mesh npz> <out weights npz> [textures json file]. Strip faces take the head ring's UV."""
import sys, json, numpy as np
J_, W_, U_, OUT, OUTW = sys.argv[1:6]
TEX = sys.argv[6] if len(sys.argv) > 6 else None
J = np.load(J_); U = np.load(U_); W = np.load(W_)
co, tri, mat = J['co'], J['tri'], J['mat']; copies = J['ringcopy']; rh = J['ringhead']
Pg = np.load('work/pages.npz', allow_pickle=True)
ub, ob, uh, oh = Pg['ub2'], U['ob'], U['uh'], U['oh']; page = Pg['page']
# head ring vertex -> a UV
vuv = {}
for f, uvf in zip(oh, uh):
    for v, q in zip(f, uvf): vuv.setdefault(int(v), q)
cmap = {int(c): int(r) for c, r in zip(copies, rh)}
fh_all = tri[mat == 1]; strip = fh_all[np.isin(fh_all, copies).any(1)]
strip = strip
copyset = set(int(c) for c in copies)
# the strip is a few mm wide: each triangle takes one texel of its head-ring vertex (ring verts of different charts would span the atlas)
us = np.array([[vuv[next((int(q) for q in f if int(q) not in copyset), cmap[int(f[0])])]] * 3 for f in strip])
# run 2: the first corner's UV is an edge texel, sometimes a pale one (a 3 cm2 strip face at L .93 read as a pale streak on the figure's right
# neck). Each strip face takes instead the centroid texel of the head face round its ring vertex whose colour is nearest the ring's median.
from PIL import Image
_hi = np.asarray(Image.open('textures/head_final.png').convert('RGB'), np.float32) / 255; _S = _hi.shape[0]
def _tex(q): q = np.clip((np.asarray(q) * [1, -1] + [0, 1]) * _S, 0, _S - 1).astype(int); return _hi[q[..., 1], q[..., 0]]   # uh is Blender v-up
_inc = {}
for f, uvf in zip(oh, uh):
    for v in f: _inc.setdefault(int(v), []).append(uvf.mean(0))
_rv = [next((int(q) for q in f if int(q) not in copyset), cmap[int(f[0])]) for f in strip]
_med = np.median(np.vstack([_tex(np.array(_inc[r])) for r in set(_rv)]), 0)
for i, r in enumerate(_rv):
    cand = np.array(_inc[r]); us[i] = [cand[np.argmin(np.linalg.norm(_tex(cand) - _med, axis=1))]] * 3
# where all three corners map to head-ring UVs of one chart (within .03), the strip face spans those UVs instead, so the scales carry across
# (one texel stretched over a strip that opens to several cm with the head bent read as flat pale bands at the neck's sides)
_span = 0; _vall = {}
for f_, uvf in zip(oh, uh):
    for v, q in zip(f_, uvf): _vall.setdefault(int(v), []).append(q)
for i, f in enumerate(strip):
    cs = [np.array(_vall.get(cmap.get(int(v), int(v)), [vuv[cmap.get(int(v), int(v))]])) for v in f]; best = None
    for a in cs[0]:
        q = np.array([a] + [c[np.argmin(np.linalg.norm(c - a, axis=1))] for c in cs[1:]]); sp = np.abs(q[:, None] - q[None]).max()
        if best is None or sp < best[0]: best = (sp, q)
    if best[0] < .03: us[i] = best[1]; _span += 1
print('strip faces recoloured', len(_rv), 'ring median', np.round(_med, 2), 'spanning their ring UVs', _span)
# chin fans
ch = J['chin']; uch = np.array([[vuv[int(f[0])]] * 3 for f in ch])      # rim charts differ: each fan triangle takes one texel of its rim, never a span across the atlas
# run 2: one texel per fan triangle drew a radial star under the jaw (Death2 from below). Each fan disk (shared centre) takes one texel for all
# its triangles: of the head faces round its rim, the centroid texel nearest the median colour of that rim.
for cen in np.unique(ch[:, 2]):
    rows = np.where(ch[:, 2] == cen)[0]; cand = np.array([q for r_ in np.unique(ch[rows, :2]) for q in _inc.get(int(r_), [])])
    if len(cand):      # the brighter hide of the jaw's underside, not the darker rim median (it read as a hole)
        col = _tex(cand); L_ = col @ np.array([.2126, .7152, .0722]); uch[rows] = cand[np.argmin(np.abs(L_ - np.percentile(L_, 80)))]
print('chin fan disks', len(np.unique(ch[:, 2])))
# run 2, third request: strip and chin faces get their own UV cells in free head atlas space (throat_paint.py), painted by 3D position
import os; sys.path.insert(0, 'scripts')
if os.environ.get('THROAT_CELLS', '1') == '1':
    import throat_paint as TP
    _us, _uch, _cf = TP.cells(J); assert len(_us) == len(strip) and len(_uch) == len(ch); us, uch = _us, _uch; strip = _cf[:len(strip)]; print('throat cells', len(us) + len(uch), '(strip zipped)')
fo = np.vstack([ob, oh, strip, ch]); fu = np.vstack([ub, uh, us, uch]); fm = np.r_[page, np.full(len(oh) + len(strip) + len(ch), 2)]
k = np.c_[fo.ravel(), np.repeat(fm, 3), np.round(fu.reshape(-1, 2) * 2 ** 20).astype(np.int64)]
u_, idx, inv = np.unique(k, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
vm = fo.ravel()[idx]; nco = co[vm]; nuv = fu.reshape(-1, 2)[idx] * [1, -1] + [0, 1]; ntri = inv.reshape(-1, 3)
# run 2, third request: the head ring sits on its body copy (up to 7 mm apart), so the strip is closed in every pose
if os.environ.get('RINGWELD', '0') == '1':
    _rh = {int(h): int(c) for h, c in zip(J['ringhead'], copies)}; _k = np.array([v in _rh for v in vm])
    nco[_k] = co[[_rh[int(v)] for v in vm[_k]]]; print('ring welded', int(_k.sum()), 'vertices')
# hip plates stand 3.2 cm off the thigh, measured from the thigh's axis
pv = J['part'][vm]; pl = np.isin(pv, [14, 15])
for sg in (1, -1):
    m_ = pl & (nco[:, 0] * sg > 0); a_ = np.array([.127 * sg, .058, -.058]); b_ = np.array([.176 * sg, -.385, .017]); ab = b_ - a_
    t_ = np.clip((nco[m_] - a_) @ ab / (ab @ ab), 0, 1); r_ = nco[m_] - (a_ + t_[:, None] * ab); r_ /= np.maximum(np.linalg.norm(r_, axis=1, keepdims=True), 1e-9); nco[m_] += r_ * .032
# flap: a little forward and narrower, to pass between the thighs
fl = pv == 9; nco[fl, 2] += .022 * np.clip((.09 - nco[fl, 1]) / .1, 0, 1) + .006; nco[fl, 0] *= .8
# run 2, chest plate shell (part 11) clipped to its paint: its upper corners were a rectangle cut through the painted side plates. Vertices outside
# the outer edge of the side plates' rim (|x| > xr(y)) slide in to it along the shell's own surface, taking the position and UV of that surface point
# from the original triangles of the same chart and side, so the texture stays where it was and the outline follows the rim. Topology unchanged.
def _xr(y): return np.maximum(.036 + .643 * (.47 - y), .036)
sh = np.where(pv == 11)[0]; st = ntri[np.isin(ntri, sh).all(1)]; P0, U0 = nco.copy(), nuv.copy(); moved = 0
for v in sh[np.abs(nco[sh, 0]) > _xr(nco[sh, 1]) + 1e-4]:
    tgt = np.array([np.sign(P0[v, 0]) * _xr(P0[v, 1]), P0[v, 1]]); best = None
    for t in st[(np.abs(U0[st] - U0[v]).max(2).max(1) < .06)]:      # triangles of the same chart near it
        a, b, c = P0[t][:, :2]; m_ = np.c_[b - a, c - a]
        if abs(np.linalg.det(m_)) < 1e-10: continue
        l1, l2 = np.linalg.solve(m_, tgt - a); l0 = 1 - l1 - l2
        L_ = np.maximum([l0, l1, l2], 0); L_ /= L_.sum(); l0, l1, l2 = L_      # a target above the top edge takes the nearest point of the edge
        p2 = l0 * a + l1 * b + l2 * c; z = l0 * P0[t[0], 2] + l1 * P0[t[1], 2] + l2 * P0[t[2], 2]
        sc = np.linalg.norm(p2 - tgt) + .3 * abs(z - P0[v, 2])
        if best is None or sc < best[0]: best = (sc, t, (l0, l1, l2))
    if best is None: print('  no surface for', v, np.round(P0[v], 3)); continue
    _, t, l = best; nco[v] = sum(li * P0[ti] for li, ti in zip(l, t)); nuv[v] = sum(li * U0[ti] for li, ti in zip(l, t)); moved += 1
print('chest shell clipped', moved, 'of', len(sh), 'vertices')
# cutlass: third material, rigid on Bone07
Wp = np.load('work/weapon.npz'); nv = len(nco); wv, wf, wu = Wp['v'], Wp['f'], Wp['uv']
nco = np.vstack([nco, wv]); nuv = np.vstack([nuv, wu * [1, -1] + [0, 1]]); ntri2 = np.vstack([ntri, wf + nv]); fm2 = np.r_[fm, np.full(len(wf), 3)]
wn = [str(x) for x in W['wnames']]
if 'Bone07' not in wn: wn.append('Bone07')
j7 = wn.index('Bone07')
wjj = np.vstack([W['wj'][vm], np.tile([j7, 0, 0, 0], (len(wv), 1))]); www = np.vstack([W['ww'][vm], np.tile([1., 0, 0, 0], (len(wv), 1))])
out = dict(co=nco, tri=ntri2, uv=nuv, mat=fm2, matnames=np.array(['Liz', 'LizB', 'LizHead', 'LizWeapon']), part=np.r_[J['part'][vm], np.full(len(wv), 30)], vmap=np.r_[vm, np.full(len(wv), -1)], ringv=np.r_[np.isin(vm, J['ringall']), np.zeros(len(wv), bool)])
if TEX: out['textures'] = open(TEX).read()
np.savez(OUT, **out)
np.savez(OUTW, wj=wjj, ww=www.astype('f4'), wnames=np.array(wn))
print('FINAL', len(nco), len(ntri2), np.bincount(fm2))

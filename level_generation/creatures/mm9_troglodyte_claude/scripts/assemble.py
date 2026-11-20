"""Final mesh for build_glb: vertices split by UV. Args: <joined npz> <weights npz> <uv npz> <out mesh npz> <out weights npz> [textures json file]. Strip faces take the head ring's UV."""
import sys, json, numpy as np
J_, W_, U_, OUT, OUTW = sys.argv[1:6]
TEX = sys.argv[6] if len(sys.argv) > 6 else None
J = np.load(J_); U = np.load(U_); W = np.load(W_)
co, tri, mat = J['co'], J['tri'], J['mat']; copies = J['ringcopy']; rh = J['ringhead']
ub, ob, uh, oh = U['ub'], U['ob'], U['uh'], U['oh']
# head ring vertex -> a UV
vuv = {}
for f, uvf in zip(oh, uh):
    for v, q in zip(f, uvf): vuv.setdefault(int(v), q)
cmap = {int(c): int(r) for c, r in zip(copies, rh)}
fh_all = tri[mat == 1]; strip = fh_all[np.isin(fh_all, copies).any(1)]
copyset = set(int(c) for c in copies)
# the strip is a few mm wide: each triangle takes one texel of its head-ring vertex (ring verts of different charts would span the atlas)
us = np.array([[vuv[next((int(q) for q in f if int(q) not in copyset), cmap[int(f[0])])]] * 3 for f in strip])
fo = np.vstack([ob, oh, strip]); fu = np.vstack([ub, uh, us]); fm = np.r_[np.zeros(len(ob), int), np.ones(len(oh) + len(strip), int)]
k = np.c_[fo.ravel(), np.round(fu.reshape(-1, 2) * 2 ** 20).astype(np.int64)]
u_, idx, inv = np.unique(k, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
vm = fo.ravel()[idx]; nco = co[vm]; nuv = fu.reshape(-1, 2)[idx] * [1, -1] + [0, 1]; ntri = inv.reshape(-1, 3)
out = dict(co=nco, tri=ntri, uv=nuv, mat=fm, matnames=J['matnames'], part=J['part'][vm], vmap=vm, ringv=np.isin(vm, J['ringall']))
if TEX: out['textures'] = open(TEX).read()
np.savez(OUT, **out)
np.savez(OUTW, wj=W['wj'][vm], ww=W['ww'][vm], wnames=W['wnames'])
print('FINAL', len(nco), len(ntri), np.bincount(fm))

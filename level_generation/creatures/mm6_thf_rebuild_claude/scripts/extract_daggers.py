#!/usr/bin/env python3
"""The approved MM6 daggers (2026-10-14, 126 tris each, `mm6_thf_reduce_claude/scripts/dagger_mesh.py`) out of the installed GLB: LOD0 vertices weighted to
DaggerL / DaggerR in the bind pose (glTF axes converted to Blender: x, -z, y), triangles, UVs, and the painted dagger column of the body images
(base colour, normal, ORM) as PNGs. Each dagger's own frame: u = blade axis (hilt -> tip), a = across the flat (widest section), the grip centre
(the middle of the grip between guard and pommel, from the section profile). Args: <installed glb> <out npz> <out image dir>"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT, IMG = sys.argv[1:4]
g = Glb(Path(IN)); m = Model(g); d = g.json
names = [n.get('name') for n in d['nodes']]
jn = [names[j] for j in m.joints]
w0 = m.world({})
posed = m.skinned_positions(w0)
res = {}
for pi, pr in enumerate(m.primitives):
    J, W = pr['joints'], pr['weights']
    for side, bone in (('R', 'DaggerR'), ('L', 'DaggerL')):
        if bone not in jn: continue
        bi = jn.index(bone)
        dom = (J == bi) & (W > 0.5)
        vs = np.nonzero(dom.any(1))[0]
        if len(vs) == 0 or side in res: continue
        tri = pr['triangles']; keep = np.all(np.isin(tri, vs), 1)
        if keep.sum() < 20: continue
        mesh = next(mm for mm in d['meshes'] if any(p is not None for p in mm['primitives']))
        # find the glTF primitive for UVs/material
        prim = None
        node = d['nodes'][pr['node']]
        for p in d['meshes'][node['mesh']]['primitives']:
            if g.accessor(p['attributes']['POSITION']).shape[0] == len(pr['positions']): prim = p; break
        uv = g.accessor(prim['attributes']['TEXCOORD_0'])
        P = posed[pi][0]
        remap = {v: k for k, v in enumerate(vs)}
        T = np.array([[remap[v] for v in t] for t in tri[keep]])
        Pb = np.c_[P[vs, 0], -P[vs, 2], P[vs, 1]]                  # Blender axes
        res[side] = dict(P=Pb, T=T, UV=uv[vs], mat=prim.get('material'))
        print('DAGGER', side, 'verts', len(vs), 'tris', len(T), 'material', prim.get('material'))
out = {}
for side, r in res.items():
    P = r['P']; c = P.mean(0); U = np.linalg.svd(P - c)[2]
    u = U[0]; a = U[1]
    t = (P - c) @ u
    # blade tip = the thin end: section width near each end
    w_lo = np.ptp(((P - c) @ a)[t < t.min() + 0.03]); w_hi = np.ptp(((P - c) @ a)[t > t.max() - 0.03])
    if w_lo < w_hi: u = -u; t = -t                               # u points hilt -> tip
    # profile: section width along u, the guard is the widest station; the grip lies between the pommel end and the guard
    bins = np.linspace(t.min(), t.max(), 41); wid = []
    for b0, b1 in zip(bins[:-1], bins[1:]):
        s = (t >= b0) & (t < b1)
        wid.append(np.ptp(((P - c) @ a)[s]) if s.sum() > 2 else 0)
    wid = np.array(wid); mid = 0.5 * (bins[:-1] + bins[1:])
    guard = mid[np.argmax(np.where(mid < 0, wid, 0))]
    grip = 0.5 * (t.min() + guard) + 0.006
    out[side + '_P'] = P; out[side + '_T'] = r['T']; out[side + '_UV'] = r['UV']
    out[side + '_frame'] = np.array([c, u, a, np.cross(u, a)]); out[side + '_grip_t'] = np.array([grip])
    print('FRAME', side, 'length', round(float(np.ptp(t)), 3), 'guard t', round(float(guard), 3), 'grip t', round(float(grip), 3),
          'uv', r['UV'].min(0).round(3).tolist(), r['UV'].max(0).round(3).tolist())
np.savez(OUT, **out)
# images of the dagger material
mat = d['materials'][res['R']['mat']]
Path(IMG).mkdir(parents=True, exist_ok=True)
def img(ti, name):
    src = d['textures'][ti]['source']; im = d['images'][src]
    bv = d['bufferViews'][im['bufferView']]
    data = bytes(g.bin[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])
    Image.open(io.BytesIO(data)).save(Path(IMG) / name)
    print('IMAGE', name)
pbr = mat.get('pbrMetallicRoughness', {})
if 'baseColorTexture' in pbr: img(pbr['baseColorTexture']['index'], 'old_body_color.png')
if 'normalTexture' in mat: img(mat['normalTexture']['index'], 'old_body_normal.png')
if 'metallicRoughnessTexture' in pbr: img(pbr['metallicRoughnessTexture']['index'], 'old_body_orm.png')

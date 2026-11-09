"""Texture quality pass (claude_shared/TEXTURE_QUALITY_PASS.md, 2026-10-30): new wing UVs for Dfly_Wings.

v1 wing UVs were the top-view image points of a 1488x864 crop squeezed into the 1K square (13 % used, x squeezed
0.69, y stretched 1.19). Here every wing leaf is flattened isometrically on its own plane (PCA of its vertices; top and
bottom sheets share the coordinates), optionally cut across its long axis into PIECES pieces, all pieces at one texel
density, and packed by xatlas brute force (claude_shared/xatlas_charts.py) into the 1K square with a MARGIN px margin.
The mesh is unchanged. Per piece the report keeps the affine map new UV -> top-view image pixel (from the v1 UVs), so
compose_wing_v2.py re-projects the top view into the new layout, gutters included, without any seam.

Args: -- <in blend (uv_v1)> <out blend> <report json> [pieces=2] [margin=4] [size=1024]
"""
import bpy, bmesh, sys, os, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
opt = dict(a.split('=', 1) for a in argv[3:])
PIECES = int(opt.get('pieces', 2))
MARGIN = int(opt.get('margin', 4))
SIZE = int(opt.get('size', 1024))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prof = json.load(open(os.path.join(HERE, 'work', 'wing_profiles.json')))
x0, y0, x1, y1 = prof['crop']

bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Dfly_Wings']
rig = ob.parent
if rig and rig.animation_data:
    rig.animation_data.action = None
if rig:
    for b in rig.pose.bones:
        b.matrix_basis.identity()
me = ob.data
uvname = me.uv_layers[0].name
nf = len(me.polygons)
assert all(len(p.vertices) == 3 for p in me.polygons)
tri = np.array([p.vertices[:] for p in me.polygons])
pos = np.array([v.co[:] for v in me.vertices])
flat = np.zeros(len(me.loops) * 2)
me.uv_layers[uvname].data.foreach_get('uv', flat)
flat = flat.reshape(-1, 2)
old = np.array([flat[list(p.loop_indices)] for p in me.polygons])          # (nf, 3, 2)
img = np.stack([x0 + old[..., 0] * (x1 - x0), y0 + (1 - old[..., 1]) * (y1 - y0)], -1)

# wing components by shared vertices
parent = np.arange(len(pos))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


for t in tri:
    for k in (1, 2):
        a, b = find(t[0]), find(t[k])
        if a != b:
            parent[a] = b
comp = np.array([find(t[0]) for t in tri])
wings = list(np.unique(comp))
chart_uv = np.zeros_like(old)
piece = np.zeros(nf, int)
normal = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
top = np.zeros(nf, bool)
rep = {'pieces': PIECES, 'margin_px': MARGIN, 'size': SIZE, 'wings': []}
pid = 0
for w in wings:
    f = comp == w
    vid = np.unique(tri[f])
    c = pos[vid].mean(0)
    _, _, vt = np.linalg.svd(pos[vid] - c)
    a1, a2, n = vt
    p2 = np.stack([(pos - c) @ a1, (pos - c) @ a2], -1)              # isometric plane coordinates
    chart_uv[f] = p2[tri[f]]
    top[f] = normal[f] @ n > 0
    s = p2[vid, 0]
    edges = np.linspace(s.min(), s.max(), PIECES + 1)
    cen = chart_uv[f][:, :, 0].mean(1)
    k = np.clip(np.searchsorted(edges, cen) - 1, 0, PIECES - 1)
    piece[f] = pid + k
    rep['wings'].append({'faces': int(f.sum()), 'length_m': float(s.max() - s.min()),
                         'width_m': float(np.ptp(p2[vid, 1]))})
    pid += PIECES
# xatlas packs the top sheets (one island per piece); the bottom sheets take the same transform
sel = top
area3 = np.linalg.norm(normal, axis=1) / 2
packed = uv_atlas._xatlas('pack', {'uv': chart_uv[sel].astype(np.float32),
                                    'vert': tri[sel] + len(pos) * piece[sel][:, None]}, '--size', SIZE,
                          '--padding', MARGIN)['uv'].astype(np.float64)
new = np.zeros_like(old)
rep['affine_uv_to_image'] = {}
for p in range(pid):
    fs = sel & (piece == p)
    src = chart_uv[fs].reshape(-1, 2)
    dst = packed[piece[sel] == p].reshape(-1, 2)
    A = np.c_[src, np.ones(len(src))]
    M, res, *_ = np.linalg.lstsq(A, dst, rcond=None)                  # chart -> packed UV (similarity in practice)
    err = float(np.abs(A @ M - dst).max() * SIZE)
    fa = piece == p
    new[fa] = np.c_[chart_uv[fa].reshape(-1, 2), np.ones(fa.sum() * 3)].reshape(-1, 3, 3) @ M
    # packed UV -> top-view image pixel: least squares over the piece's corners (exact affine by construction)
    B = np.c_[new[fa].reshape(-1, 2), np.ones(fa.sum() * 3)]
    Q, *_ = np.linalg.lstsq(B, img[fa].reshape(-1, 2), rcond=None)
    ierr = float(np.abs(B @ Q - img[fa].reshape(-1, 2)).max())
    rep['affine_uv_to_image'][str(p)] = {'matrix': Q.tolist(), 'pack_fit_px': err, 'image_fit_px': ierr,
                                         'faces': int(fa.sum())}
assert all(v['pack_fit_px'] < 0.05 and v['image_fit_px'] < 0.5 for v in rep['affine_uv_to_image'].values()), rep
flat = np.zeros((len(me.loops), 2))
for p in me.polygons:
    flat[list(p.loop_indices)] = new[p.index]
me.uv_layers[uvname].data.foreach_set('uv', flat.ravel().astype(np.float32))
d1, d2 = new[:, 1] - new[:, 0], new[:, 2] - new[:, 0]
use = float(np.abs(d1[top, 0] * d2[top, 1] - d1[top, 1] * d2[top, 0]).sum() / 2)
rep['use'] = round(use, 4)
rep['texels_per_m'] = float(np.sqrt(np.abs(d1[top, 0] * d2[top, 1] - d1[top, 1] * d2[top, 0]).sum() / 2
                                    / area3[top].sum()) * SIZE)
# face -> piece id, for the texture composer (pieces rasterised in UV space)
np.savez(os.path.join(HERE, 'work', 'wing_uv_v2.npz'), uv=new.astype(np.float32), piece=piece, top=top)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('WING_UV_V2', json.dumps({k: v for k, v in rep.items() if k != 'affine_uv_to_image'}))

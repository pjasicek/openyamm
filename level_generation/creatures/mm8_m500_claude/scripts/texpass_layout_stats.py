"""Quick layout numbers of a texpass uv_layout npz, as texture_quality.py measures them (texel-centre union at
2048, density spread, fragments, stretch), split into body and head-set charts.
Usage: texpass_layout_stats.py <uv_layout.npz>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texpass_glb import BEFORE, lod0_arrays, np, read_glb  # noqa: E402
from transfer_textures import rasterize  # noqa: E402

layout = np.load(sys.argv[1])
uv = layout['corner_uv'].copy()
uv[..., 1] = 1 - uv[..., 1]
head = layout['head_face']
doc, binary = read_glb(BEFORE)
pos, _, faces = lod0_arrays(doc, binary)
p = pos[faces]
a3 = np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1) / 2
t = uv * 2048
a2 = np.abs((t[:, 1, 0] - t[:, 0, 0]) * (t[:, 2, 1] - t[:, 0, 1]) - (t[:, 2, 0] - t[:, 0, 0]) * (t[:, 1, 1] - t[:, 0, 1])) / 2
tri, x, y, _ = rasterize(uv, 2048)
cover = np.zeros((2048, 2048), bool)
cover[y, x] = True
d = np.sqrt(a2 / np.maximum(a3 * 1e4, 1e-12))  # px per cm
zero = int((a2 < 1e-6).sum())
for name, m in (('body', ~head), ('head', head)):
    w = a3[m]
    o = np.argsort(d[m])
    c = np.cumsum(w[o]) / w.sum()
    q = [d[m][o][np.searchsorted(c, f)] for f in (.1, .5, .9)]
    print(f'{name}: px/cm p10/p50/p90 {q[0]:.2f}/{q[1]:.2f}/{q[2]:.2f} spread {q[2] / q[0]:.2f}, atlas {a2[m].sum() / 2048 ** 2:.1%}')
print(f'atlas union {cover.mean():.1%}, zero-area UV triangles {zero}')

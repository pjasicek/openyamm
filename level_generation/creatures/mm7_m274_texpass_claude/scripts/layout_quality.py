"""texture_quality.py measures of a layout npz (corner UVs + positions) at 2048, before any GLB exists, with the
head-set faces reported apart. Usage: layout_quality.py <layout npz>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import texture_quality as TQ  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
lay = np.load(sys.argv[1])
uv, xyz = lay['uv'], lay['xyz']
head = np.load(HERE / 'work' / 'lod0_before.npz')['head_face']
extent = float(np.ptp(xyz.reshape(-1, 3), 0).max())
e1, e2 = xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]
a3 = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
px = uv * 2048
d1, d2 = px[:, 1] - px[:, 0], px[:, 2] - px[:, 0]
a2 = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
dens = np.sqrt(a2 / np.maximum(a3, 1e-12)) * extent
union = TQ.raster_union(uv)
isl = TQ.islands(uv, xyz)
_, inv, cnt = np.unique(isl, return_inverse=True, return_counts=True)
frag = cnt[inv] < 8
wp = lambda v, w, q: TQ.weighted_percentile(v, w, q)
print(f'atlas {100 * union.mean():.1f}% equivalent {2048 * np.sqrt(union.mean()):.0f}px islands {len(cnt)} '
      f'fragments {100 * a3[frag].sum() / a3.sum():.1f}% zero-area {(a2 < 1e-9).sum()}')
for name, sel in (('body', ~head), ('head', head), ('all', np.ones(len(uv), bool))):
    print(f'  {name}: density p10/p50/p90 {wp(dens[sel], a3[sel], 10):.0f}/{wp(dens[sel], a3[sel], 50):.0f}/'
          f'{wp(dens[sel], a3[sel], 90):.0f}')

"""Pack existing UV charts with xatlas (brute force) into one RESOLUTION square.
xatlas keeps each chart's shape (use_input_mesh_uvs) and sizes it by its 3D area, so the caller scales the positions
of denser charts (head, gun) about their centre beforehand. The texel density is searched so the atlas just fits.
Usage: <python with xatlas> xatlas_pack.py in.npz out.npz RESOLUTION PADDING
in.npz: pos (V,3), uv (V,2), idx (T,3). out.npz: idx (T,3) into uvx (W,2) in 0..1, utilization, size, tpu."""
import sys
import numpy as np
import xatlas
src, dst, res, pad = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
d = np.load(src)


def run(tpu):
    atlas = xatlas.Atlas()
    atlas.add_mesh(d['pos'].astype(np.float32), d['idx'].astype(np.uint32), uvs=d['uv'].astype(np.float32))
    co = xatlas.ChartOptions(); co.use_input_mesh_uvs = True; co.fix_winding = False
    po = xatlas.PackOptions(); po.padding = pad; po.bilinear = True; po.bruteForce = True
    po.rotate_charts = True; po.rotate_charts_to_axis = True; po.resolution = res
    if tpu:
        po.texels_per_unit = tpu
    atlas.generate(co, po)
    return atlas


# largest texel density whose charts fit one RESOLUTION page (bisection)
lo, hi = 300.0, 2000.0
best = None
for it in range(int(sys.argv[5]) if len(sys.argv) > 5 else 9):
    tpu = (lo + hi) / 2
    a = run(tpu)
    fits = a.atlas_count == 1
    print('TRY', it, round(tpu, 1), a.width, a.height, a.atlas_count, round(float(np.ravel(a.utilization)[0]), 3), flush=True)
    if fits:
        lo = tpu; best = (tpu, a)
    else:
        hi = tpu
tpu, a = best
vmap, idx, uv = a[0]
uvx = uv * np.array([a.width, a.height]) / res
np.savez(dst, idx=idx, uvx=uvx, utilization=np.array(a.utilization), size=np.array([a.width, a.height]), tpu=tpu)
print('XATLAS', a.width, a.height, float(np.ravel(a.utilization)[0]), a.chart_count, round(tpu, 2))

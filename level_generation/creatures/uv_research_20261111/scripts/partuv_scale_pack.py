"""PartUV study: PartUV charts (or any per-face chart layout) -> one texel density with the head denser -> xatlas pack.

The density and packing steps are those of claude_shared/uv_atlas.py (area-based scale per chart, head charts
`head_factor` times denser when at least half of the chart's surface is head; xatlas brute-force pack of
partuv_xatlas_charts.py, an unchanged copy of claude_shared/xatlas_charts.py, run in claude_shared/xatlas_venv), so
only the charts differ from the baseline.

  partuv_scale_pack.py <mesh.npz> <charts.npz> <out.npz> [head_factor=1.8] [size=2048] [margin=2] [steps=10] [fine=0]
                       [mode=xatlas|keep]
mode=keep writes the charts' UVs as they are (already packed, e.g. PartUV's own Blender packing) and only measures.
Mirrored charts (negative total UV area) are flipped in u first: the packer only rotates.
"""
import json
import os
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
XATLAS_PY = os.path.join(HERE, '..', '..', 'claude_shared', 'xatlas_venv', 'bin', 'python')
PACKER = os.path.join(HERE, 'partuv_xatlas_charts.py')

mesh_path, charts_path, out = sys.argv[1:4]
opts = dict(a.split('=', 1) for a in sys.argv[4:])
head_factor = float(opts.get('head_factor', 1.8))
size, margin = int(opts.get('size', 2048)), int(opts.get('margin', 2))
steps, fine = int(opts.get('steps', 10)), int(opts.get('fine', 0))
mesh, charts = np.load(mesh_path), np.load(charts_path)
pos, tri, head = mesh['pos'], mesh['tri'], mesh['head']
uv, label = charts['uv'].astype(np.float64).copy(), charts['chart']
p3 = pos[tri]
area3 = np.linalg.norm(np.cross(p3[:, 1] - p3[:, 0], p3[:, 2] - p3[:, 0]), axis=1) / 2


def signed(t):
    return ((t[:, 1, 0] - t[:, 0, 0]) * (t[:, 2, 1] - t[:, 0, 1])
            - (t[:, 2, 0] - t[:, 0, 0]) * (t[:, 1, 1] - t[:, 0, 1])) / 2


start = time.time()
info = {'charts': int(len(np.unique(label))), 'mirrored_charts': 0, 'flipped_triangles': 0}
if opts.get('mode', 'xatlas') == 'xatlas':
    for c in np.unique(label):
        faces = label == c
        s = signed(uv[faces])
        if s.sum() < 0:
            uv[faces, :, 0] *= -1
            info['mirrored_charts'] += 1
            s = -s
        info['flipped_triangles'] += int((s < 0).sum())
        a2, a3 = np.abs(s).sum(), area3[faces].sum()
        if a2 <= 0 or a3 <= 0:
            continue
        k = np.sqrt(a3 / a2)
        if head_factor != 1.0 and area3[faces & head].sum() >= 0.5 * a3:
            k *= head_factor
        centre = uv[faces].reshape(-1, 2).mean(0)
        uv[faces] = centre + (uv[faces] - centre) * k
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, 'in.npz'), os.path.join(tmp, 'out.npz')
        # packing vertices: one per (chart, mesh vertex), so islands are exactly the charts
        np.savez(src, uv=uv.astype(np.float32), vert=(label[:, None] * len(pos) + tri).astype(np.int64))
        run = subprocess.run([XATLAS_PY, '-I', PACKER, 'pack', src, dst, '--size', str(size), '--padding', str(margin),
                              '--steps', str(steps), '--fine', str(fine)], capture_output=True, text=True)
        print(run.stdout.strip())
        if run.returncode:
            raise RuntimeError(run.stderr)
        uv = np.load(dst)['uv'].astype(np.float64)
info['pack_seconds'] = round(time.time() - start, 1)
info['use'] = round(float(np.abs(signed(uv)).sum()), 4)
np.savez(out, uv=uv, chart=label)
json.dump(info, open(out.replace('.npz', '.json'), 'w'), indent=1)
print('PACKED', out, info)

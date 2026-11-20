"""Print measurements of chosen components of the oriented raw return (after parts.py's bucket shift is irrelevant:
these are body parts): vertex boxes near the front of the vent hoods, the nozzle mouth ring, the core drums."""
import os
import sys

import bmesh
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harvester_common as tc  # noqa: E402

obj = tc.import_raw()
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = tc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
np.set_printoptions(precision=3, suppress=True)
for c in (2, 44):
    p = co[labels == c]
    print('HOOD', c, 'lo', p.min(0), 'hi', p.max(0))
    for dy in (0.02, 0.08, 0.2, 0.4):
        f = p[p[:, 1] < p[:, 1].min() + dy]
        print('  front', dy, len(f), 'x', f[:, 0].min(), f[:, 0].max(), 'z', f[:, 2].min(), f[:, 2].max())
    # profile: for slices along y, x/z extents of the shell
    for y in np.linspace(p[:, 1].min() + 0.05, p[:, 1].max() - 0.05, 6):
        s = p[np.abs(p[:, 1] - y) < 0.06]
        if len(s):
            print('  slice y %.2f' % y, 'x', s[:, 0].min(), s[:, 0].max(), 'z', s[:, 2].min(), s[:, 2].max(), len(s))
p = co[labels == 4]
m = p[p[:, 1] > p[:, 1].max() - 0.06]
print('NOZZLE mouth', len(m), 'centre', m.mean(0), 'x', m[:, 0].min(), m[:, 0].max(), 'z', m[:, 2].min(), m[:, 2].max())
p40 = co[labels == 40]
print('NECK lo', p40.min(0), 'hi', p40.max(0))
low = p40[p40[:, 2] < p40[:, 2].min() + 0.08]
print('NECK base', low.mean(0), 'x', low[:, 0].min(), low[:, 0].max(), 'y', low[:, 1].min(), low[:, 1].max())
for c in (110, 15):
    p = co[labels == c]
    print('DRUM', c, 'lo', p.min(0), 'hi', p.max(0), 'mean', p.mean(0))

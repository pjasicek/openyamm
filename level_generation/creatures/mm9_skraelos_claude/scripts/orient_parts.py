#!/usr/bin/env python3
"""Generated parts' winding: the necklace (fangs and cord) was built inward-facing (back faces seen from the front), so its triangles are
reversed; the robe's inner cap faces down (seen from under the hem). Index order only: positions and UVs unchanged. Args: <in npz> <out npz>"""
import sys
import numpy as np
D = dict(np.load(sys.argv[1])); co, t, comp = D['co'], D['tri'].copy(), D['comp']; names = [str(x) for x in D['names']]
m = comp[t[:, 0]] == names.index('necklace'); t[m] = t[m][:, ::-1]
m = comp[t[:, 0]] == names.index('cap'); fn = np.cross(co[t[m, 1]] - co[t[m, 0]], co[t[m, 2]] - co[t[m, 0]])
if (fn[:, 2] > 0).mean() > 0.5: t[m] = t[m][:, ::-1]
D['tri'] = t; np.savez(sys.argv[2], **D); print('ORIENT', sys.argv[2])

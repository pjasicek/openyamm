#!/usr/bin/env python3
"""r5: the back of the skull (hidden by the helm) stood up to 1.1 cm through the helm's back plate at z 1.46-1.53 (seen from above on the
face-down corpse): the occiput (y > 0.04, Blender frame) is squashed to 0.72 of its depth. Face, eyes and jaw do not move. Args: <in npz> <out npz>"""
import sys, numpy as np
D = dict(np.load(sys.argv[1])); co = D['co'].copy(); names = [str(x) for x in D['names']]
v = np.where(D['comp'] == names.index('skull'))[0]; y = co[v, 1]; b = y > 0.04
co[v[b], 1] = 0.04 + (y[b] - 0.04) * 0.72
print('skull back y', round(float(y.max()), 3), '->', round(float(co[v, 1].max()), 3))
D['co'] = co; np.savez(sys.argv[2], **D)

#!/usr/bin/env python3
"""work/lod_check_<a>.json vs <b>.json (lod_check.py): per LOD triangles, rest top, faces stretched over 20x and the lowest
point per clip; and each LOD of <b> against its own LOD0. Usage: lod_compare.py <a> <b>"""
import json, sys
a, b = (json.load(open(f'work/lod_check_{t}.json')) for t in sys.argv[1:3])
for l in a:
    A, B = a[l], b[l]
    print('LOD', l, 'tris', A['tris'], '->', B['tris'], '| rest top', A['rest_max'][2], '->', B['rest_max'][2],
          '| stretched max', max(c['stretched_faces'] for c in A['clips'].values()), '->', max(c['stretched_faces'] for c in B['clips'].values()),
          '| Standing low', A['clips']['Standing']['min_z'], '->', B['clips']['Standing']['min_z'],
          '| worst low any clip', min(c['min_z'] for c in A['clips'].values()), '->', min(c['min_z'] for c in B['clips'].values()))
z0 = b['0']
for l in b:
    d = [b[l]['clips'][c]['min_z'] - z0['clips'][c]['min_z'] for c in z0['clips']]
    print(sys.argv[2], 'LOD', l, 'top vs LOD0 %+.4f' % (b[l]['rest_max'][2] - z0['rest_max'][2]), 'lowest point vs LOD0 per clip: min %+.4f max %+.4f' % (min(d), max(d)))

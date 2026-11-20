"""Compare node TRS of two converted MM9 GLBs. Usage: cmp_skel.py a.glb b.glb"""
import sys, json, struct
import numpy as np
def nodes(p):
    d = open(p, 'rb').read(); n = struct.unpack('<I', d[12:16])[0]; j = json.loads(d[20:20 + n])
    return {x.get('name'): (np.array(x.get('translation', [0, 0, 0])), np.array(x.get('rotation', [0, 0, 0, 1]))) for x in j['nodes']}
a, b = nodes(sys.argv[1]), nodes(sys.argv[2])
print('only a', sorted(set(a) - set(b))[:20]); print('only b', sorted(set(b) - set(a))[:20])
for k in a:
    if k in b:
        dt = np.abs(a[k][0] - b[k][0]).max(); q1, q2 = a[k][1], b[k][1]
        dq = min(np.abs(q1 - q2).max(), np.abs(q1 + q2).max())
        if dt > 1e-4 or dq > 1e-3:
            print(f'{k:30s} dt {dt*100:.2f} cm dq {dq:.3f}  a {np.round(q1,3)} b {np.round(q2,3)}')

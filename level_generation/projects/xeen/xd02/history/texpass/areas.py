# areas.py <export.json>: area share by texture for walls (upright), floors and ceilings, and of all faces.
import json, sys, collections
d = json.load(open(sys.argv[1]))['map']
V = d['vertices']
def area(f):
    p = [V[i] for i in f['vertices']]
    sx = sy = sz = 0.0
    for a, b in zip(p, p[1:] + p[:1]):
        sx += a[1] * b[2] - a[2] * b[1]; sy += a[2] * b[0] - a[0] * b[2]; sz += a[0] * b[1] - a[1] * b[0]
    return 0.5 * (sx * sx + sy * sy + sz * sz) ** 0.5
roles = collections.defaultdict(collections.Counter)
for f in d['faces']:
    if f['is_portal']:
        continue
    nz = f['plane_normal'][2] / 65536
    r = 'floor' if nz > 0.7 else 'ceil' if nz < -0.7 else 'wall'
    a = area(f)
    roles[r][f['texture'].lower()] += a
    roles['all'][f['texture'].lower()] += a
for r in ('wall', 'floor', 'ceil', 'all'):
    tot = sum(roles[r].values())
    print(r, f'{tot/1e6:.1f} M', ' '.join(f'{t}:{v/tot:.2f}' for t, v in roles[r].most_common(8)))

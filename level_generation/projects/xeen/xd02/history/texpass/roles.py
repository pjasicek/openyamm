# roles.py <export.json>: each texture's faces as floor / wall / ceiling (by normal), most faces first.
import json, sys, collections
d = json.load(open(sys.argv[1]))['map']
c = collections.defaultdict(collections.Counter)
for f in d['faces']:
    if f['is_portal']:
        continue
    nz = f['plane_normal'][2] / 65536
    role = 'floor' if nz > 0.7 else 'ceil' if nz < -0.7 else 'slope' if abs(nz) > 0.2 else 'wall'
    c[f['texture'].lower()][role] += 1
for t, r in sorted(c.items(), key=lambda kv: -sum(kv[1].values())):
    print(f'{t:12s} {sum(r.values()):5d}  ' + ' '.join(f'{k}:{v}' for k, v in r.most_common()))

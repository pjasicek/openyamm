import json, sys, collections
d = json.load(open(sys.argv[1])); m = d['map']; V = m['vertices']
def area(f):
    pts = [V[i] for i in f['vertices']]
    import math
    # polygon area via cross products
    ax=ay=az=0
    for i in range(len(pts)):
        a=pts[i]; b=pts[(i+1)%len(pts)]
        ax += a[1]*b[2]-a[2]*b[1]; ay += a[2]*b[0]-a[0]*b[2]; az += a[0]*b[1]-a[1]*b[0]
    return 0.5*math.sqrt(ax*ax+ay*ay+az*az)
roles = collections.defaultdict(lambda: collections.Counter())
for f in m['faces']:
    if f['is_portal']: continue
    nz = f['plane_normal'][2]/65536
    r = 'floor' if nz > 0.7 else 'ceil' if nz < -0.7 else 'wall'
    roles[f['texture'].lower()][r] += area(f)
tot = sum(sum(c.values()) for c in roles.values())
for t, c in sorted(roles.items(), key=lambda kv: -sum(kv[1].values())):
    s = sum(c.values())
    print(f"{t:12s} {100*s/tot:5.1f}%  " + "  ".join(f"{k} {100*v/s:.0f}%" for k, v in c.most_common()))

"""Print a BModel's faces: texture, normal, size, attributes, events."""
import sys, math
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/util')
import map_export as me
from pathlib import Path
pl = me.parse_odm_file(Path('/home/pjasicek/github/OpenYAMM/assets_dev/worlds/mm6/maps/oute3.odm'))['payload']
for idx in map(int, sys.argv[1:]):
    m = pl['bmodels'][idx]
    V = m['vertices']
    print(f"== {idx} {m['name']} faces={len(m['faces'])} verts={len(V)}")
    for f in m['faces']:
        P = [(V[i]['x'], V[i]['y'], V[i]['z']) for i in f['vertex_indices']]
        ax = [round(sum(p[k] for p in P) / len(P)) for k in range(3)]
        # Newell normal
        n = [0, 0, 0]
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n[0] += (a[1] - b[1]) * (a[2] + b[2]); n[1] += (a[2] - b[2]) * (a[0] + b[0]); n[2] += (a[0] - b[0]) * (a[1] + b[1])
        L = math.sqrt(sum(c * c for c in n)) or 1
        n = [round(c / L, 2) for c in n]
        ext = [max(p[k] for p in P) - min(p[k] for p in P) for k in range(3)]
        print(f"{f['index']:3d} {f['texture_name']:10s} n={n} c={ax} ext={ext} nv={len(P)} attr={f['attributes']:#x} ev={f['cog_triggered_number']} cog={f['cog_number']}")

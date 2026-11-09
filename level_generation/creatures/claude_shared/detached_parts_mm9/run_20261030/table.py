import json, glob
from pathlib import Path
for f in sorted(glob.glob('*.json')):
    r=json.load(open(f))[0]; n=Path(f).stem
    print(f"{n}: comps {r['components']} detached {len(r['parts'])} concealed {len(r['concealed'])} lift {len(r['root_lift'])}")
    for k,p in sorted(r['parts'].items(), key=lambda kv:-kv[1]['worst']['gap']):
        w=p['worst']
        print(f"   {k:>4} {p['joint'][:16]:16} {p['triangles']:>5}t ext {p['extent']*100:5.0f}cm bind {p['bind_gap']*1000:6.1f} worst {w['gap']*1000:7.1f}mm {w['kind']:8} off {w['against'][:14]:14} {w['clip']} {w['frame']} ({w['time']}) {p['detached_poses']}/{p['poses']} car {p['carried_poses']}")
    for k,p in sorted(r['root_lift'].items(), key=lambda kv:-kv[1]['root_lift']['gap'])[:3]:
        w=p['root_lift']; print(f"      lift {k} {p['joint'][:16]} {p['triangles']}t {w['gap']*1000:.1f}mm {w['clip']} {w['frame']}")

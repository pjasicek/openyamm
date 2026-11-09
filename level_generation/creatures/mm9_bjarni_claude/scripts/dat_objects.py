"""List every MM9 DAT object whose class or any property names Bjarni, with its script and model properties.
Usage: python3 dat_objects.py [regex] [keys...] [--full]"""
import glob, json, re, sys, collections
pat = re.compile(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else r"bjarni", re.I)
rows = []
def hit(cur):
    return any(pat.search(str(v)) for v in cur.values())
for path in sorted(glob.glob('assets_dev/worlds/mm9/maps/*.raw_objects.yml')):
    cur = None; prop = None
    with open(path) as f:
        for line in f:
            s = line.strip()
            if s.startswith('- object_index:'):
                if cur and hit(cur): rows.append(cur)
                cur = {'map': path.split('/')[-1].split('.')[0]}
            elif cur is not None and s.startswith('name:') and 'class' not in cur and line.startswith('    name'):
                cur['class'] = s.split(':', 1)[1].strip().strip('"')
            elif cur is not None and s.startswith('- name:'):
                prop = s.split(':', 1)[1].strip().strip('"')
            elif cur is not None and prop and s.startswith('value_json:'):
                v = s.split(':', 1)[1].strip()
                try: v = json.loads(json.loads(v))
                except Exception: pass
                cur[prop] = v; prop = None
    if cur and hit(cur): rows.append(cur)
if '--full' in sys.argv:
    for r in rows:
        print(json.dumps({k: v for k, v in r.items() if v not in ('', 0, None, [])}, default=str))
    sys.exit()
keys = [k for k in sys.argv[2:] if not k.startswith('--')] or ['Name', 'Filename', 'ScriptName', 'ScriptParams']
for r in rows:
    print(r['map'], r['class'], [str(r.get(k, ''))[:80] for k in keys])
print(len(rows), 'objects')

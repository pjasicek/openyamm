"""List every MM9 DAT object of the elf female townsfolk classes with its script and model properties."""
import glob, json, re, sys, collections
pat = re.compile(sys.argv[1] if len(sys.argv) > 1 else r"(Commoner|Prisoner)ElfFemale", re.I)
rows = []
for path in sorted(glob.glob('assets_dev/worlds/mm9/maps/*.raw_objects.yml')):
    cur = None; prop = None
    with open(path) as f:
        for line in f:
            s = line.strip()
            if s.startswith('- object_index:'):
                if cur and pat.search(cur.get('class', '')): rows.append(cur)
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
    if cur and pat.search(cur.get('class', '')): rows.append(cur)
if '--keys' in sys.argv:
    print(sorted(rows[0].keys())); sys.exit()
keys = [k for k in sys.argv[2:] if not k.startswith('--')] or ['ScriptName', 'ScriptParams']
c = collections.Counter()
for r in rows:
    c[(r['class'],) + tuple(str(r.get(k, '')) for k in keys)] += 1
for k, n in sorted(c.items()): print(n, k)
print(len(rows), 'objects')

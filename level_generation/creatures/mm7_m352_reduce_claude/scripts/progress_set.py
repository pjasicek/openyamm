"""Set keys in the canonical progress record: progress_set.py <project> key=<json> ... (dotted keys create nesting).
A key `hash:<section>=<file>[,<file>...]` stores the files' sha256 under <section> (paths relative to the project)."""
import hashlib, json, sys
from pathlib import Path
P = Path(sys.argv[1]); f = P / 'creature_3d_progress.json'
d = json.loads(f.read_text()) if f.exists() else {}
for arg in sys.argv[2:]:
    k, v = arg.split('=', 1)
    if k.startswith('hash:'):
        sec = d.setdefault(k[5:], {})
        for p in v.split(','):
            sec[Path(p).name if '/' not in p else p] = hashlib.sha256((P / p).read_bytes()).hexdigest()
        continue
    node = d; parts = k.split('.')
    for p in parts[:-1]:
        node = node.setdefault(p, {})
    node[parts[-1]] = json.loads(v)
f.write_text(json.dumps(d, indent=1) + '\n')

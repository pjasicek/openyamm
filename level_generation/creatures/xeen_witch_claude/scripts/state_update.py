"""Merge a JSON patch file into creature_3d_progress.json (top-level keys replaced). Args: <patch.json>"""
import json, sys, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(HERE, 'creature_3d_progress.json')
d = json.load(open(p))
patch = json.load(open(sys.argv[1]))
d.update(patch)
json.dump(d, open(p, 'w'), indent=2)
print('STATE keys', sorted(d.keys()))

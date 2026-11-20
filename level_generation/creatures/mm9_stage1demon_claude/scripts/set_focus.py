"""Viewer focus overrides for a shot batch (the wrapper only accepts six focus names): writes manifest.json "focuses".
Usage: set_focus.py name=x,y,z,dist [...]   (glTF coords: y up, +z forward, +x the creature's left); no args clears."""
import json, sys
p = 'review/viewer/manifest.json'; m = json.load(open(p))
m['focuses'] = {a.split('=')[0]: [float(v) for v in a.split('=')[1].split(',')] for a in sys.argv[1:]}
if not m['focuses']: m.pop('focuses')
json.dump(m, open(p, 'w'), indent=1)

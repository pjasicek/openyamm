# Writes a tour yml from a shot list module: python3 tour.py <list.py> <out yml> <output dir>
import sys, yaml, runpy
H = 'render hud off'
S = runpy.run_path(sys.argv[1])['S']
shots = []
for s in S:
    d = {'name': s[0], 'position': s[1], 'yaw': s[2], 'pitch': s[3], 'commands': [H] + s[4]}
    if len(s) > 5:
        d['settle_seconds'] = s[5]
    shots.append(d)
out = {'output_dir': sys.argv[3], 'exit': True, 'settle_seconds': 1.3, 'shots': shots}
open(sys.argv[2], 'w').write(yaml.safe_dump(out, sort_keys=False, default_flow_style=None, width=200))

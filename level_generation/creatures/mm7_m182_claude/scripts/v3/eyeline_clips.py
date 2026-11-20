#!/usr/bin/env python3
"""Eye-line record (system Python + Blender): side renders (camera from the dragon's right, motion-gate elevation) of
the tier-A preview blend at given clip frames, measured with scripts/v3/eyeline.py (eye = red iris centroid, snout =
foremost pixel of the upper jaw at the eye's height). Native side flight frames read the same way off gridded x2
crops (eye -> snout tip): sa2 23.4, wb2 20.7, wd2 20.2, wf2 21.8 deg, mean 21.5.
Usage: eyeline_clips.py <blend> <out.json> clip:frame ..."""
import json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parents[2]; blend, out, shots = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
R = P / 'work/v3b/renders/eyeline_clips'; R.mkdir(parents=True, exist_ok=True)
spec = {'out': str(R), 'engine': 'WORKBENCH', 'color': 'TEXTURE', 'transparent': True, 'res': [900, 900],
        'shots': [{'name': s.replace(':', '_'), 'clip': s.split(':')[0], 'frame': int(s.split(':')[1]), 'dir': [-1, 0, .0195], 'track': 'Head', 'offset': [0, -.1, 0], 'scale': .7} for s in shots]}
(R / 'spec.json').write_text(json.dumps(spec)); subprocess.run(['blender', '-b', '--factory-startup', '-P', str(P / 'scripts/v3/render.py'), '--', blend, str(R / 'spec.json')], check=True, capture_output=True)
res = {'native_deg': {'m182sa2': 23.4, 'm182wb2': 20.7, 'm182wd2': 20.2, 'm182wf2': 21.8, 'mean': 21.5}}
for s in shots:
    o = subprocess.run(['python3', str(P / 'scripts/v3/eyeline.py'), str(R / (s.replace(':', '_') + '.png'))], capture_output=True, text=True).stdout
    res[s] = float(o.split()[1]) if o.startswith('EYELINE') else None
out.write_text(json.dumps(res, indent=1)); print('EYELINES', res)

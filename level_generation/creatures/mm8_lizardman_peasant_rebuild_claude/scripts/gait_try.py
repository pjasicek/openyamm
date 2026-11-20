#!/usr/bin/env python3
"""Try gain/rate pairs for Run and Sprint: build clips with clips_mm9.py and print stride_audit's feet measurement
(stride, natural speed). Usage: gait_try.py Run:gain:rate ..."""
import json, subprocess, sys, os
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared/postprocess')); sys.path.insert(0, str(HERE.parent / 'claude_shared/floor'))
import stride_audit, glb_pose as gp
base = json.load(open(HERE / 'scripts/roles_lizp.json'))
env = dict(os.environ, PYTHONPATH=subprocess.check_output(['python3', '-c', 'import yaml,os;print(os.path.dirname(os.path.dirname(yaml.__file__)))'], text=True).strip())
for spec in sys.argv[1:]:
    role, gain, rate = spec.split(':')
    r = json.loads(json.dumps(base)); r['roles'] = {k: v for k, v in r['roles'].items() if k in ('Standing', role)}
    r['roles'][role]['gain'] = {'joints': ['Thigh', 'Calf', 'Foot'], 'amount': float(gain)}; r['roles'][role]['rate'] = float(rate)
    r.pop('dead_from', None)
    json.dump(r, open(HERE / 'work/gait_try.json', 'w'))
    subprocess.run([str(HERE.parent / 'claude_shared/gltf_venv/bin/python'), 'scripts/clips_mm9.py', 'work/body_uv.glb', 'work/gait_try.glb', 'work/gait_try.json'], cwd=HERE, env=env, capture_output=True, check=True)
    m = gp.Model(gp.Glb(HERE / 'work/gait_try.glb')); T = max(m.clip_times(role))
    feet = stride_audit.measure_feet(m, role)
    print(spec, 'T %.3f' % T, 'feet', feet, 'speed %.2f' % (feet / T) if feet else '')

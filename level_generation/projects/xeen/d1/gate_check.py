#!/usr/bin/env python3
"""A6 (2026-11-20): the built scene's decorations against D1's gate lanes (gen.py GATES, in_gate_lane): no tree or
prop in front of either gate, inside or out. Usage: gate_check.py <build dir>. Exit 1 on a finding."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import io
import contextlib
import os
import sys
import yaml

B = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_REPO_ROOT, 'output/studio_cal/d1', 'build')
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
_argv = sys.argv
sys.argv = [_argv[0]]                       # gen.py reads its briefs folder from argv; its module level only checks
with contextlib.redirect_stdout(io.StringIO()):
    import gen as G
sys.argv = _argv
scene = yaml.load(open(os.path.join(B, 'xeen_d1.scene.yml')), Loader=yaml.CSafeLoader)
bad = []
n = 0
for e in scene['entities']:
    name = e['name']
    if 'start' in name or name.lower().startswith('snd'):
        continue
    n += 1
    p = (e['position']['x'] / 512.0 + 64, 64 - e['position']['y'] / 512.0)
    g = G.in_gate_lane(p, G.prop_margin(name))
    if g:
        bad.append('%s at [%.2f, %.2f] stands in the lane of %s' % (name, p[0], p[1], g))
print('gate lanes: %d decorations checked, %d in a lane' % (n, len(bad)))
for b in bad:
    print('  ' + b)
sys.exit(1 if bad else 0)

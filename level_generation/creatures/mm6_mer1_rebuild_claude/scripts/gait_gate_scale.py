#!/usr/bin/env python3
"""claude_shared/postprocess/gait_gate.py with the rebuild's binding scale (and no z_offset) applied to the model's descriptors before
the gate runs (the installed binding still carries the old model's scale). Usage: gait_gate_scale.py <scale> <gait_gate args...>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/postprocess'))
import gait_gate  # noqa: E402
SCALE = float(sys.argv.pop(1))
_orig = gait_gate.bindings


def bindings(world, model):
    actors, mine = _orig(world, model)
    names = {a['descriptor'] for a in mine}
    for a in actors:
        if a['descriptor'] in names:
            a['scale'] = SCALE; a.pop('z_offset', None)
    return actors, [a for a in actors if a['descriptor'] in names]


gait_gate.bindings = bindings
sys.exit(gait_gate.main())

#!/usr/bin/env python3
"""gait_gate.py for a subset of a model's descriptors: the shared gate applies --set to every descriptor bound to the
model, but on a shared model (MM7 m382: Rat A-C and zrat a-c) a binding change may be for some tiers only.
Runs ../../claude_shared/postprocess/gait_gate.py unchanged, with its binding lookup limited to the descriptors given.

    gate_only.py --only "zrat a,zrat b,zrat c" <gait_gate.py arguments>
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "claude_shared" / "postprocess"))
import gait_gate  # noqa: E402

index = sys.argv.index("--only")
ONLY = {name.strip() for name in sys.argv[index + 1].split(",")}
del sys.argv[index:index + 2]
_bindings = gait_gate.bindings


def bindings(world, model):
    actors, mine = _bindings(world, model)
    return actors, [actor for actor in mine if actor["descriptor"] in ONLY]


gait_gate.bindings = bindings
sys.exit(gait_gate.main())

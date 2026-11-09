#!/usr/bin/env python3
"""tools/mm9_import_discovery/convert_abc_model.py with an animation of an MM9 animation library added to the model
first (the peasants' sitting, listening, writing and innkeeper poses live in PeasantSeated.abc / PeasantWork.abc, not
in PeasantMS2.abc / PeasantM2.abc). The library must have the model's nodes in the same order (checked).
Environment: LIBRARY_POSE=<library .abc path>|<animation name>. Arguments: as convert_abc_model.py.
Run with cwd tools/mm9_import_discovery (convert_all.py does)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
import convert_abc_model as tool  # noqa: E402

LIBRARY, ANIMATION = os.environ['LIBRARY_POSE'].split('|')
_read_abc = tool.read_abc
_done = set()


def read_abc(path):
    model = _read_abc(path)
    if Path(path).resolve() == Path(sys.argv[1]).resolve():
        library = _read_abc(Path(LIBRARY))
        if [n.name for n in library.nodes] != [n.name for n in model.nodes]:
            raise SystemExit(f'{LIBRARY}: its nodes differ from {path}')
        animation = next(a for a in library.animations if a.name.lower() == ANIMATION.lower())
        model.animations = [animation] + [a for a in model.animations if a.name.lower() != ANIMATION.lower()]
        binding = next((b for b in library.anim_bindings if b.name.lower() == ANIMATION.lower()), None)
        if binding is not None:
            model.anim_bindings = [binding] + [b for b in model.anim_bindings if b.name.lower() != ANIMATION.lower()]
    return model


tool.read_abc = read_abc
sys.exit(tool.main())

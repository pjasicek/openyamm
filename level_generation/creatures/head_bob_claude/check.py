#!/usr/bin/env python3
"""Checks every export against its installed source: the floor rules (floor_audit.py) and the measured strides
(stride_audit.py) of every binding of the model, before and after. Run from the repository root."""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import sys

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "level_generation/creatures/claude_shared/floor"))
sys.path.insert(0, str(ROOT / "level_generation/creatures/claude_shared/postprocess"))
import floor_audit  # noqa: E402
import stride_audit  # noqa: E402

def check(export):
    world, name = export.parent.name, export.name
    lines, failed = [], False
    # A model of another world (MM7 binds MM8's Earth Elemental) is judged by every world that binds it.
    for binding_world in ("mm6", "mm7", "mm8"):
        actors = [actor for actor in yaml.safe_load(
            (ROOT / f"assets_dev/worlds/{binding_world}/models/actors.yml").read_text())["actors"]
            if actor["model"] == f"worlds/{world}/models/{name}"]
        if not actors:
            continue
        candidate = [dict(actor, model=str(export)) for actor in actors]
        floor_before = {r["descriptor"]: r["problems"] for r in floor_audit.audit(binding_world, None, 2.5, 0.01, actors)}
        floor_after = {r["descriptor"]: r["problems"] for r in floor_audit.audit(binding_world, None, 2.5, 0.01,
                                                                                 candidate)}
        new = {descriptor: problems for descriptor, problems in floor_after.items()
               if problems and problems != floor_before[descriptor]}
        strides_before = {r["clip"]: r["measured"] for r in stride_audit.audit(binding_world, None, 0.1, actors)}
        strides_after = {r["clip"]: r["measured"] for r in stride_audit.audit(binding_world, None, 0.1, candidate)}
        changes = {clip: (strides_before[clip], value) for clip, value in strides_after.items()
                   if (value is None) != (strides_before.get(clip) is None)
                   or (value and abs(value / strides_before[clip] - 1) > 0.03)}
        status = "ok" if not new and not changes else "CHECK"
        failed |= status != "ok"
        lines.append(f"{binding_world} {name:18} floor {'new: ' + str(new) if new else 'unchanged'}; strides "
                     f"{changes if changes else 'within 3 %'}  {status}")
    return "\n".join(lines), failed


def main():
    exports = sorted((HERE / "export").glob("*/*.glb"))
    if len(sys.argv) > 1:
        exports = [export for export in exports if export.stem in sys.argv[1:]]
    failed = False
    with ProcessPoolExecutor(max_workers=12) as pool:
        for text, bad in pool.map(check, exports):
            print(text, flush=True)
            failed |= bad
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

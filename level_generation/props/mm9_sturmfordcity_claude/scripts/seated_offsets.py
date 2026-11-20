#!/usr/bin/env python3
"""The seated townsfolk's binding z_offset (M18, 2026-11-06; seats.py has the rule and the measurement): for each
decoration of SEATED, the mean seat-contact need over its placements in every MM9 map's props.json, added to its
binding's current z_offset, so the figures sit on their benches, pews, stools, chairs and stand steps without a map
conversion. Rerunning is idempotent (the need is measured with the current offset).

Writes work/seat_offsets.json (tables.py of this project and The Arena's emit its z_offset when they append a binding)
and, with --apply, the z_offset lines of the world bindings (worlds/mm9/models/indoor_decorations.yml), as a new file
renamed over the old one, then the same file into the review roots (REVIEW_ROOTS), the same way.
Not here: mm9_bjarnisitting (it sits right on Thronheim's chair and over Sturmford's throne step it floats: Sturmford's
placements.py lowers that placement instead) and the Thronheim council (on their chairs; seats.py measures them 4-12
units into the seats, not looked at in game: they are hidden at start).
Usage: seated_offsets.py [--apply]"""
import json
import os
import re
import sys
import tempfile
from collections import defaultdict

import numpy as np

import seats

HERE = seats.REPO / 'level_generation/props/mm9_sturmfordcity_claude'
WORLD_BINDINGS = seats.REPO / 'assets_dev/worlds/mm9/models/indoor_decorations.yml'
REVIEW_ROOTS = (seats.REPO / 'output/mm9_rework/assets_dev', seats.REPO / 'output/mm9_rework/isleofashes_blv_root')
OFFSETS = HERE / 'work/seat_offsets.json'
SEATED = {
    # Sturmford City (this project): the tavern's benches and the pew (MoveToFloor). Not the two MoveToFloor 0 men,
    # at MM9's own DAT height: Ludwig sits on his chair, the man on the bar stool rests his arms on the bar (+13 to
    # his measured stool top lifted them off it, 2026-11-06 review)
    'mm9_peasantms2bconv', 'mm9_peasantms2csitting', 'mm9_peasantms2dlisten', 'mm9_erccsitting',
    # The Arena (mm9_thearena_claude): the spectators on the stand's steps
    'mm9_peasantfs2bconv1', 'mm9_peasantms1alisten', 'mm9_peasantms1blisten', 'mm9_peasantms2alisten',
    'mm9_peasantms2blisten', 'mm9_peasantms2clisten',
}


def write(path, text):
    """A new file renamed over the old one (hard-linked mirrors keep the old file until they get the copy)."""
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
    with os.fdopen(handle, 'w') as f:
        f.write(text)
    os.chmod(temp, 0o644)
    os.replace(temp, path)


def set_offset(text, name, offset):
    """The binding block of name with its z_offset line set (after yaw), or removed for 0."""
    pattern = re.compile(rf'(  - name: {re.escape(name)}\n(?:    .*\n)*?)(?=  [-#]|\Z)')
    match = pattern.search(text)
    if match is None:
        sys.exit(f'{name}: no binding in {WORLD_BINDINGS}')
    block = re.sub(r'    z_offset: .*\n', '', match.group(1))
    if offset:
        block = re.sub(r'(    yaw: .*\n)', rf'\g<1>    z_offset: {offset}\n', block, count=1)
        if 'z_offset' not in block:
            block += f'    z_offset: {offset}\n'
    return text[:match.start()] + block + text[match.end():]


def main():
    table = seats.bindings()
    needs = defaultdict(list)
    for props_json in sorted((seats.REPO / 'level_generation/projects').glob('mm9r_*/props.json')):
        entries = json.loads(props_json.read_text())
        for entry in entries:
            if entry['decoration'].lower() not in SEATED:
                continue
            need, seat, top, plane, feet = seats.seat_contact(entries, entry, table)
            needs[entry['decoration'].lower()].append(need)
            print(f"{props_json.parent.name:20s} {entry['source_name']:20s} {entry['decoration']:24s} seat {seat} "
                  f"{top:.1f}, seat plane {plane:.1f}, feet {feet:.1f}: need {need:+.1f}")
    offsets = {}
    for name in sorted(SEATED):
        current = float(table[name].get('z_offset', 0.0) or 0.0)
        offsets[name] = round(current + float(np.mean(needs[name])), 1)
        spread = max(needs[name]) - min(needs[name])
        print(f'{name}: z_offset {current:+.1f} -> {offsets[name]:+.1f} ({len(needs[name])} placements'
              f"{f', spread {spread:.1f}' if len(needs[name]) > 1 else ''})")
    OFFSETS.write_text(json.dumps(offsets, indent=1, sort_keys=True) + '\n')
    if '--apply' not in sys.argv:
        print('dry run (work/seat_offsets.json written); --apply writes the bindings')
        return
    text = WORLD_BINDINGS.read_text()
    for name, offset in offsets.items():
        text = set_offset(text, name, offset)
    write(WORLD_BINDINGS, text)
    for root in REVIEW_ROOTS:
        target = root / WORLD_BINDINGS.relative_to(seats.REPO / 'assets_dev')
        if target.exists():
            write(target, text)
    print('WROTE', WORLD_BINDINGS, 'and', ', '.join(str(r) for r in REVIEW_ROOTS))


if __name__ == '__main__':
    main()

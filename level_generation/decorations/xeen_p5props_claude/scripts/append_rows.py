#!/usr/bin/env python3
"""Append the P5 shrine decorations (lane S, xeen-s7-p5) to the Xeen world's decoration table, sprite table and indoor
bindings. Append only: each file is re-read, nothing else changes, a row/sprite/binding already present is refused.

    append_rows.py <rows.json> [--apply]       (without --apply: print what would be appended)"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
W = ROOT / 'assets_dev/worlds/xeen'
TABLE = W / 'models/decoration_data.txt'
SPRITES = W / 'rendering/sprite_frame_data_world_decorations.yml'
BINDINGS = W / 'models/indoor_decorations.yml'
spec = json.load(open(sys.argv[1]))
apply = '--apply' in sys.argv
table, sprites, bindings = TABLE.read_text(), SPRITES.read_text(), BINDINGS.read_text()
rows, sp, bi = [], [], []
for d in spec['rows']:
    if f"\n{d['row']}\t" in table or f"\t{d['name']}\t" in table:
        sys.exit(f"row {d['row']} / {d['name']} already in the table")
    if f"sprite_id: {d['sprite']}\n" in sprites:
        sys.exit(f"sprite {d['sprite']} already taken")
    if f"- name: {d['name']}\n" in bindings:
        sys.exit(f"binding {d['name']} already present")
    rows.append('\t'.join(map(str, [d['row'], d['name'], d['hint'], 0, d['radius'], d['height'], 0, 0, 0, 0, 0,
                                     d.get('flags', 0), d['sprite'], '-'])) + '\n')
    sp.append(f'  - sprite_id: {d["sprite"]}\n    sprite_name: "{d["name"]}"\n    frames:\n'
              f'      - texture_name: "pending"\n        frame_length_raw: 0\n        flags: [First]\n'
              f'        scale: 1.0\n')
    lines = [f"  # {line}" for line in d['comment']]
    lines += [f"  - name: {d['name']}", f"    model: {d['model']}", f"    height: {d['binding_height']}",
              "    yaw: facing"]
    for k in ('yaw_offset', 'z_offset'):
        if k in d:
            lines.append(f"    {k}: {d[k]}")
    bi.append('\n'.join(lines) + '\n')
for name, text, add in ((TABLE, table, rows), (SPRITES, sprites, sp), (BINDINGS, bindings, bi)):
    new = text + ('' if text.endswith('\n') else '\n') + ''.join(add)
    print(f'== {name.relative_to(ROOT)}: +{len(add)}')
    print(''.join(add))
    if apply:
        name.write_text(new)
print('APPLIED' if apply else 'DRY RUN')

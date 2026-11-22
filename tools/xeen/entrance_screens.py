#!/usr/bin/env python3
"""Xeen's entrance lines on the outdoor maps' doors (F16, D-90 4; lane A6, 2026-11-22).

A3's `source/entrances.yml` names, per trans.txt row, the map things that enter its dungeon (`entered_by`, e.g.
"d1 door:thing:kalindra_gate (123), door:thing:kalindra_gate_restored (254)"; text after "No row:" is not a row's).
`screens(stem)` returns {sketch thing id: row id} for one map; `apply_sketch(sketch, stem)` sets `into.screen:
{text: <row>}` on every thing whose `into` enters a dungeon and has no `screen` of its own, so a map's generator never
hand-copies row numbers. `row_for(stem, event_name)` gives the row of a Lua-written move (a rope, a choice).

    python3 tools/xeen/entrance_screens.py xeen_d1        # the map's rows
"""
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(ROOT, 'assets_dev', 'worlds', 'xeen', 'source', 'entrances.yml')
MAP_WORD = re.compile(r'^(x\d|d\d|p\d|xd\d\d|dd\d\d[a-c]?|fd\d\d)\s+(.*)$')


def _rows():
    rows = {}
    for entry in yaml.safe_load(open(SOURCE))['entrances']:
        text = str(entry.get('text') or '').strip()
        if not text or text.startswith('(empty'):      # 5046 (the griffin): a note, not a line
            continue
        said = entry['entered_by'].split('No row:')[0]
        for segment in re.split(r';|\.\s+', said):
            match = MAP_WORD.match(segment.strip())
            if not match:
                continue
            short = match.group(1)
            for item in match.group(2).split(','):
                name = item.strip().split(' (')[0].strip()
                if name and re.match(r'^[\w:/]+$', name):
                    rows.setdefault('xeen_' + short, {})[name] = entry['id']
    return rows


def row_for(stem, event_name):
    """The row of an event name as the map's Lua heads it (`door:thing:x`, `part:thing:x/y`, `thing:x`)."""
    return _rows().get(stem, {}).get(event_name)


def screens(stem):
    """{sketch thing id: row}: `door:thing:x` and `thing:x` both name the sketch thing `thing:x`."""
    out = {}
    for name, row in _rows().get(stem, {}).items():
        if name.startswith('part:'):
            continue
        out[name[len('door:'):] if name.startswith('door:') else name] = row
    return out


def apply_sketch(sketch, stem):
    """Set `into.screen: {text: row}` where the map's thing has a row and no screen of its own; returns the count."""
    rows = screens(stem)
    count = 0
    for key in ('things', 'buildings', 'structures'):
        for thing in sketch.get(key) or []:
            into = thing.get('into') if isinstance(thing, dict) else None
            if not isinstance(into, dict) or 'screen' in into:
                continue
            if not str(into.get('map', '')).lower().endswith('.blv'):
                continue
            row = rows.get(thing.get('id'))
            if row:
                into['screen'] = {'text': row}
                count += 1
    return count


if __name__ == '__main__':
    for stem in sys.argv[1:] or sorted(_rows()):
        for name, row in sorted(_rows().get(stem, {}).items(), key=lambda kv: kv[1]):
            print(stem, row, name)

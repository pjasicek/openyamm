#!/usr/bin/env python3
"""Writes a copy of an oymap export whose entities carry their decoration's internal name (decoration_data row
decoration_list_id + 1) in place of the scene's id, so that A7's measure.py (which keys on the decoration name) sees
the map's props. Usage: named_export.py <export.json> <out.json>"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json, sys
R = _REPO_ROOT + '/assets_dev/engine/data_tables/decoration_data.txt'
DD = {}
for line in open(R, encoding='latin-1'):
    c = line.rstrip('\n').split('\t')
    if len(c) > 2 and c[0].isdigit():
        DD[int(c[0])] = c[1]
d = json.load(open(sys.argv[1]))
for e in d['map']['entities']:
    e['scene_id'] = e['name']
    e['name'] = DD.get(e['decoration_list_id'] + 1, e['name'])
json.dump(d, open(sys.argv[2], 'w'))

"""Dump a compact view of the isle's raw MM9 objects (class, properties) to work/raw_objects_compact.json."""
import json, sys
from collections import Counter
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parents[1]
raw = yaml.load((ROOT / 'assets_editor_dev/worlds/mm9/maps/isleofashes.raw_objects.yml').read_text(), Loader=yaml.CSafeLoader)
out = []
for obj in raw['objects']:
    props = {}
    for p in obj['properties']:
        try:
            props[p['name']] = json.loads(p['value_json']) if p.get('value_json') is not None else None
        except Exception:
            props[p['name']] = p.get('value_json')
    out.append({'index': obj['object_index'], 'class': obj['name'], 'props': props})
(HERE / 'work/raw_objects_compact.json').write_text(json.dumps(out, indent=1))
print(Counter(o['class'] for o in out).most_common())

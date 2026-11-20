#!/usr/bin/env python3
"""Lists the isle's placed objects that are not decorations here (chests, doors, destructible walls, world objects,
effects and gameplay helpers) with their remade-frame positions -> non_props.json, for the map conversion session."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import props_table  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
T = json.loads((props_table.REPO / 'level_generation/projects/mm9r_isleofashes/work/transform.json').read_text())
CLASSES = {'TreasureChest': 'chest (model Chest1.ABC; the old map bakes it as MM9_chest_<index>_*)',
           'RotatingDoor': 'door (rotating brush)', 'Door': 'door (sliding brush)',
           'DestructableBrush': 'destructible wall brush', 'WorldObject': 'world-object brush',
           'Fire': 'fire effect (on the log pile 766)', 'Shooter': 'trap shooter', 'HidingPlace': 'sea monster lair',
           'ScriptObject': 'script helper / explosion effect', 'Trigger': 'trigger', 'ExitTrigger': 'map exit',
           'StartPoint': 'party start', 'EarthQuake': 'earthquake effect', 'Light': 'light',
           'InvisibleBrush': 'invisible blocker', 'PerceptionBrush': 'AI perception brush'}
out = []
for o in props_table.objects():
    if o['class'] not in CLASSES:
        continue
    p = o['props']
    pos = p.get('Pos')
    entry = {'source_object': o['index'], 'class': o['class'], 'name': p.get('Name'), 'kind': CLASSES[o['class']]}
    if pos:
        entry['x'] = round(pos[0] * 2.56 - T['offset_x'], 1)
        entry['y'] = round(pos[2] * 2.56 - T['offset_y'], 1)
        entry['z'] = round((pos[1] - T['sea_level_lt']) * 2.56, 1)
    for key in ('Filename', 'Skin', 'Rotation'):
        if key in p:
            entry[key.lower()] = p[key]
    out.append(entry)
(HERE / 'non_props.json').write_text(json.dumps(out, indent=1) + '\n')
from collections import Counter
print(Counter(e['class'] for e in out))

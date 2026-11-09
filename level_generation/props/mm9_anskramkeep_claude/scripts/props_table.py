"""Anskram Keep's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them, and
the ABC placement binding origins. The isle's props (../../mm9_isleofashes_claude) are reused by name when a model
and skin match one of them; none of the keep's do (its furniture is other ABC files).

    python3 scripts/props_table.py            # work/raw_objects_compact.json, work/binding_origins.json, summary
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
ISLE = REPO / 'level_generation/props/mm9_isleofashes_claude'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/anskramkeep.raw_objects.yml'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
# The skin decides the prop when one mesh has several (weapons cabinet, chest).
MODELS = {
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/bed.abc', 'skins/props/bed.dtx'): 'bed',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/bookcase02ns.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ns',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair02.abc', 'skins/props/chair02.dtx'): 'chair02',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/desk01.abc', 'skins/props/desk01.dtx'): 'desk01',
    ('models/props/desk01ns.abc', 'skins/props/desk01.dtx'): 'desk01ns',
    ('models/props/dresserns.abc', 'skins/props/dresserplain.dtx'): 'dresserns',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/table_bench_broken.abc', 'skins/props/table_bench.dtx'): 'tablebench',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/weaponrack.abc', 'skins/props/weaponrack_used.dtx'): 'weaponrack',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet01.dtx'): 'weaponscabinet01',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet04.dtx'): 'weaponscabinet04',
    ('models/props/trashpile.abc', 'skins/props/trashpile.dtx'): 'trashpile',
    ('models/props/walltorch.abc', 'skins/props/walltorch.dtx'): 'walltorch',
    ('models/props/chest1.abc', 'skins/props/chest2.dtx'): 'chest',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    ('models/props/spikepit.abc', 'skins/props/spikepit.dtx'): 'spikepit',
}
# Classes whose objects are placed as decorations. PropDamager: the spike pits in the trap pits (the ones attached to
# the crushers move with them, which decorations cannot); the map project places them on the pit floors.
CLASSES = {'Prop', 'WallTorch', 'Barrel', 'BonePile', 'TreasureChest', 'PropDamager'}


def key(path):
    return (path or '').replace('\\', '/').lower()


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def placements():
    """(object index, prop id) of every decoration object."""
    out = []
    for o in objects():
        p = o['props']
        if o['class'] in CLASSES and p.get('Filename') and not p.get('AttachTo'):
            out.append((o['index'], MODELS[(key(p['Filename']), key(p.get('Skin')))]))
    return out


def source(prop):
    """(model path, skin path) under mm9/extracted for a prop id."""
    model, skin = next(k for k, v in MODELS.items() if v == prop)
    return (REPO / 'mm9/extracted/MODELS/MODELS' / model[len('models/'):],
            REPO / 'mm9/extracted/SKINS/SKINS' / skin[len('skins/'):])


def resolve(path):
    """The extracted file of a case-insensitive path."""
    current = path.parents[len(path.parts) - len((REPO / 'mm9/extracted').parts) - 1]
    for part in path.parts[len(current.parts):]:
        match = next((c for c in current.iterdir() if c.name.lower() == part.lower()), None)
        if match is None:
            raise FileNotFoundError(path)
        current = match
    return current


_origins = None


def binding_origin(prop):
    global _origins
    if _origins is None:
        _origins = json.loads((HERE / 'work/binding_origins.json').read_text())
    return _origins[prop]


def main():
    import yaml
    sys.path.insert(0, str(REPO / 'tools/mm9_import_discovery'))
    raw = yaml.load(RAW.read_text(), Loader=yaml.CSafeLoader)
    out = []
    for obj in raw['objects']:
        props = {}
        for p in obj['properties']:
            try:
                props[p['name']] = json.loads(p['value_json']) if p.get('value_json') is not None else None
            except ValueError:
                props[p['name']] = p.get('value_json')
        out.append({'index': obj['object_index'], 'class': obj['name'], 'props': props})
    (HERE / 'work/raw_objects_compact.json').write_text(json.dumps(out, indent=1))
    from convert_abc_model import read_abc
    from transcode_mm9_dat_to_odm import abc_static_model_placement_info
    origins = {}
    for prop in sorted(set(MODELS.values())):
        model, _ = source(prop)
        info = abc_static_model_placement_info(read_abc(resolve(model)))
        origins[prop] = list(info.binding_origin) if info else [0.0, 0.0, 0.0]
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    print(Counter(prop for _, prop in placements()).most_common())


if __name__ == '__main__':
    main()

"""Beethoven's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
the ABC placement binding origins, and which props reuse a decoration another project built (same ABC model, skin and
placement scale; its GLB, row and binding stay where they are). The module keeps the names the Anskram Keep scripts
read (HERE, REPO, ISLE, MODELS, source, resolve, ...), so they run on this table from sys.modules['props_table'].

    python3 scripts/props_table.py            # work/raw_objects_compact.json, work/binding_origins.json, summary
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
ISLE = REPO / 'level_generation/props/mm9_isleofashes_claude'
ANSKRAM = REPO / 'level_generation/props/mm9_anskramkeep_claude'
PROJECT = REPO / 'level_generation/projects/mm9r_beethoven'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/beethoven.raw_objects.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    ('models/pickupitems/quest/ludwig-manuscript.abc', 'skins/pickupitems/quest/ludwigmanuscript.dtx'): 'manuscript',
    ('models/props/urngargoyle.abc', 'skins/props/urngargoyle.dtx'): 'urngargoyle',
    ('models/props/jar01.abc', 'skins/props/pantry-items.dtx'): 'jar01',
    ('models/props/jar02.abc', 'skins/props/pantry-items.dtx'): 'jar02',
    ('models/props/jar03.abc', 'skins/props/pantry-items.dtx'): 'jar03',
    ('models/props/jar04.abc', 'skins/props/pantry-items02.dtx'): 'jar04',
    ('models/props/jar05.abc', 'skins/props/pantry-items02.dtx'): 'jar05',
    ('models/props/jar06.abc', 'skins/props/pantry-items02.dtx'): 'jar06',
    ('models/props/coffinfancy.abc', 'skins/props/coffinstone.dtx'): 'coffinfancy',
    ('models/props/coffinraised.abc', 'skins/props/coffinstone.dtx'): 'coffinraised',
    ('models/props/torch2.abc', 'skins/props/sconce1.dtx'): 'sconcetorch',
    ('models/props/hangingbrazierbowl.abc', 'skins/props/hangingbrazierbowl.dtx'): 'hangingbowl1',
    ('models/props/bonepile.abc', 'skins/props/bonepile.dtx'): 'bonepile',
    ('models/props/walltorch.abc', 'skins/props/walltorch.dtx'): 'walltorch',
    ('models/props/trashpile.abc', 'skins/props/trashpile.dtx'): 'trashpile',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    ('models/props/well.abc', 'skins/props/well.dtx'): 'well',
    ('models/props/winebottle01.abc', 'skins/props/winebottle01.dtx'): 'winebottle',
}
# A jar lying on its side (Jar1, Jar7: pitch 90 degrees) and the manuscript lying flat: one model each, the pitch baked
# in (decorations turn about z only).
TILTED = {'Jar1': 'jar01side', 'Jar7': 'jar04side'}
BOOK_TILT = {'jar01side': (1.5707964, 0.0), 'jar04side': (1.5707964, 0.0), 'manuscript': (1.5707964, 0.0)}
SOURCES = {'jar01side': 'jar01', 'jar04side': 'jar04'}
ISLE_WORK = ISLE
# Decorations another project built from the same ABC model and skin (prop -> owning project).
REUSED = {'walltorch': ANSKRAM, 'trashpile': ANSKRAM, 'chest1': ANSKRAM, 'well': ISLE}
CLASSES = {'Prop', 'WallTorch', 'CandleProp', 'TreasureChest', 'BonePile', 'DestructableProp', 'WellMMIX'}
SKIPPED = {'BottleNW', 'BottleNE', 'BottleSW', 'BottleSE'}      # the floating bottle: scripts/bottle.py, a scripted model
BOOK_PROPS = {}


def key(path):
    return (path or '').replace('\\', '/').lower().strip()


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def object_prop(o):
    p = o['props']
    return TILTED.get(p['Name']) or MODELS[(key(p['Filename']), key(p.get('Skin')))]


def placements():
    """(object index, prop id) of every decoration object."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')
            and o['props']['Name'] not in SKIPPED]


def source_prop(prop):
    return SOURCES.get(prop, prop)


def built_props():
    return sorted((set(MODELS.values()) | set(TILTED.values())) - set(REUSED))


def home(prop):
    """The props project whose work/ holds the prop's meta, raw and finished GLBs."""
    return REUSED.get(prop, HERE)


def source(prop):
    """(model path, skin path) under mm9/extracted for a prop id."""
    model, skin = next(k for k, v in MODELS.items() if v == source_prop(prop))
    roots = {'models': 'MODELS/MODELS', 'skins': 'SKINS/SKINS', 'textures': 'TEXTURES/TEXTURES'}

    def path(p):
        top, rest = p.split('/', 1)
        return EXTRACTED / roots[top] / rest
    return path(model), path(skin)


def resolve(path):
    """The extracted file of a case-insensitive path."""
    current = path.parents[len(path.parts) - len(EXTRACTED.parts) - 1]
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
    return _origins[source_prop(prop)]


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
    (HERE / 'work').mkdir(exist_ok=True)
    (HERE / 'work/raw_objects_compact.json').write_text(json.dumps(out, indent=1))
    from convert_abc_model import read_abc
    from transcode_mm9_dat_to_odm import abc_static_model_placement_info
    origins = {}
    for prop in sorted(set(MODELS.values()) | set(BOOK_PROPS.values())):
        model, _ = source(prop)
        info = abc_static_model_placement_info(read_abc(resolve(model)))
        origins[prop] = list(info.binding_origin) if info else [0.0, 0.0, 0.0]
    origins.update({prop: origins[base] for prop, base in SOURCES.items()})
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    counts = Counter(prop for _, prop in placements())
    print(len(counts), 'props,', sum(counts.values()), 'placements;',
          Counter(o['class'] for o in out if o['class'] in CLASSES))
    print('built:', [(p, counts[p]) for p in built_props()])
    print('reused:', [(p, counts[p]) for p in sorted(REUSED)])


if __name__ == '__main__':
    main()

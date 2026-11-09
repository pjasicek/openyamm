"""Training Hall's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
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
PROJECT = REPO / 'level_generation/projects/mm9r_traininghall'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/traininghall.raw_objects.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by the Anskram Keep, Temple of Honk, Lich Lab, Drangheim Prison and Beethoven projects
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/brazier.abc', 'skins/props/brazier.dtx'): 'brazier',
    ('models/props/walltorch.abc', 'skins/props/walltorch.dtx'): 'walltorch',
    ('models/props/hangingbrazierbowl.abc', 'skins/props/hangingbrazierbowl.dtx'): 'hangingbowl1',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
    ('models/props/debris/lumberstonedebris02.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'lumberstone02',
    # built here
    ('models/props/debris/lumberdebris02.abc', 'skins/props/debris/lumberdebris.dtx'): 'lumberdebris02',
    ('models/props/debris/lumberdebris03.abc', 'skins/props/debris/lumberdebris.dtx'): 'lumberdebris03',
    ('models/props/debris/lumberdebris05.abc', 'skins/props/debris/lumberdebris.dtx'): 'lumberdebris05',
    ('models/props/training_mount.abc', 'skins/props/training_mount.dtx'): 'trainingmount',
    ('models/props/training_spindummy1.abc', 'skins/props/training_spindummy1.dtx'): 'spindummy',
    ('models/props/training_strawdummy1.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy',
}
TILTED = {}
BOOK_TILT = {}
SOURCES = {}
ISLE_WORK = ISLE
LICHLAB = REPO / 'level_generation/props/mm9_lichlab_claude'
TEMPLE = REPO / 'level_generation/props/mm9_templeofhonk_claude'
DRANGHEIM = REPO / 'level_generation/props/mm9_drangheimprison_claude'
BEETHOVEN = REPO / 'level_generation/props/mm9_beethoven_claude'
# Decorations another project built from the same ABC model and skin (prop -> owning project).
REUSED = {'barrel03': ANSKRAM, 'brazier': TEMPLE, 'walltorch': ANSKRAM, 'hangingbowl1': BEETHOVEN, 'chest1': ANSKRAM,
          'blackchest': LICHLAB, 'lumberstone02': DRANGHEIM}
# MM9's Torch class here is the hanging brazier bowl (HangingBrazierBowl.abc); Fire objects have no model (the map
# project places the Anskram gate fire's flames at them).
CLASSES = {'Prop', 'WallTorch', 'Brazier', 'Torch', 'Barrel', 'TreasureChest'}
SKIPPED = set()
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

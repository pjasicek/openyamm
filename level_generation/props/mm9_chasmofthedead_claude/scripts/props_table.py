"""The Chasm of the Dead's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
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
PROJECT = REPO / 'level_generation/projects/mm9r_chasmofthedead'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/chasmofthedead.raw_objects.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # the Chasm's fires are blue (CandleProp Blue 1, lights 0/128/255): the Temple's brazier and hanging bowl and MM9's
    # sconce and torch with the shared flipbook recoloured blue, models of their own
    ('models/props/brazier.abc', 'skins/props/brazier.dtx'): 'bluebrazier',
    ('models/props/hangingbrazierbowl.abc', 'skins/props/hangingbrazierbowl3.dtx'): 'bluebowl',
    ('models/props/sconce2.abc', 'skins/props/sconce2.dtx'): 'bluesconce',
    ('models/props/torch2.abc', 'skins/props/sconce1.dtx'): 'bluetorch',
    ('models/pickupitems/quest/cronakiga.abc', 'skins/pickupitems/quest/cronakiga.dtx'): 'cronakiga',
    ('models/pickupitems/quest/lichinstructions.abc', 'skins/pickupitems/quest/lichinstructions.dtx'): 'lichinstructions',
    ('models/props/altar1.abc', 'skins/props/altar1.dtx'): 'altar1',
    ('models/props/box-ornamental.abc', 'skins/props/box-ornamental.dtx'): 'boxornamental',
    ('models/props/chair1.abc', 'skins/props/chair1.dtx'): 'chair1',
    ('models/props/cup1.abc', 'skins/props/cup1.dtx'): 'cup1',
    ('models/props/goblet_fancy01.abc', 'skins/props/goblet_fancy01.dtx'): 'goblet',
    ('models/props/jar01.abc', 'skins/props/pantry-items.dtx'): 'jar01',
    ('models/props/jar04.abc', 'skins/props/pantry-items02.dtx'): 'jar04',
    ('models/props/pillarstand.abc', 'skins/props/pillarstand.dtx'): 'pillarstand',
    ('models/props/sarcophagus2.abc', 'skins/props/sarcophagus2.dtx'): 'sarcophagus',
    ('models/props/sarcophagus2ns.abc', 'skins/props/sarcophagus2.dtx'): 'sarcophagusns',
    ('models/props/sarcophagus2ns.abc', 'skins/props/sarcophagus3.dtx'): 'sarcophagusns3',
    ('models/props/sarcophagus2vert.abc', 'skins/props/sarcophagus2.dtx'): 'sarcophagusvert',
    ('models/props/statue_guardian1.abc', 'skins/props/statue_guardian1.dtx'): 'statueguardian',
    ('models/props/statue_guardian1ew.abc', 'skins/props/statue_guardian1.dtx'): 'statueguardianew',
    ('models/props/treasurechute.abc', 'skins/props/treasurechute.dtx'): 'treasurechute',
    ('models/props/treasurepile.abc', 'skins/props/treasurepile.dtx'): 'treasurepile',
    ('models/props/tumbler1.abc', 'skins/props/tumbler1.dtx'): 'tumbler1',
    ('models/props/urn1.abc', 'skins/props/urn1.dtx'): 'urn1',
    ('models/props/urn2.abc', 'skins/props/urn2.dtx'): 'urn2',
    ('models/props/mummyew.abc', 'skins/props/mummy2.dtx'): 'mummyew',
    ('models/props/chest5.abc', 'skins/props/chest5.dtx'): 'chest5',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
}
LICHLAB = REPO / 'level_generation/props/mm9_lichlab_claude'
# Decorations another project built from the same ABC model and skin (prop -> owning project): their GLBs and rows stay
# where they are; a placement scale they do not have becomes a variant row here (tables.py).
BEETHOVEN = REPO / 'level_generation/props/mm9_beethoven_claude'
REUSED = {'blackchest': LICHLAB, 'jar01': BEETHOVEN, 'jar04': BEETHOVEN}
CLASSES = {'Prop', 'CandleProp', 'TreasureChest'}     # the PropDamager spikes: the map project (they move or lie in the pit)
# Toppled in MM9 (decorations turn about z only): their pitch baked in, a model each.
TILTED = {'Altar20': 'altar1flip', 'Stand3': 'pillarfallen', 'Urn5': 'urn2tip1', 'Urn8': 'urn2tip2'}
SOURCES = {'altar1flip': 'altar1', 'pillarfallen': 'pillarstand', 'urn2tip1': 'urn2', 'urn2tip2': 'urn2'}
BOOK_TILT = {'altar1flip': (3.1415927, 0.0), 'pillarfallen': (1.5707964, 0.0), 'urn2tip1': (2.0944, 0.0),
             'urn2tip2': (0.8727, 0.0)}
BOOK_PROPS = {}


def key(path):
    return (path or '').replace('\\', '/').lower().strip()


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def object_prop(o):
    p = o['props']
    return TILTED.get(p.get('Name')) or MODELS[(key(p['Filename']), key(p.get('Skin')))]


def placements():
    """(object index, prop id) of every decoration object."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')]


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
    for prop in sorted(set(MODELS.values()) | set(TILTED.values())):
        model, _ = source(prop)
        info = abc_static_model_placement_info(read_abc(resolve(model)))
        origins[prop] = list(info.binding_origin) if info else [0.0, 0.0, 0.0]
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    counts = Counter(prop for _, prop in placements())
    print(len(counts), 'props,', sum(counts.values()), 'placements;',
          Counter(o['class'] for o in out if o['class'] in CLASSES))
    print('built:', [(p, counts[p]) for p in built_props()])
    print('reused:', [(p, counts[p]) for p in sorted(REUSED)])


if __name__ == '__main__':
    main()

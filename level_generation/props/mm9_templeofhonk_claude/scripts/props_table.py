"""The Temple of Honk's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
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
PROJECT = REPO / 'level_generation/projects/mm9r_templeofhonk'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/templeofhonk.raw_objects.yml'
EXTRACTED = REPO / 'mm9/extracted'

TAPESTRY_SKINS = {
    'carpets/tapestry_flower': 'tapestry_flower', 'carpets/tapestry_olive': 'tapestry_olive',
    'carpets/tapestry_purple': 'tapestry_purple', 'carpets/tapestry_redblack': 'tapestry_redblack',
    'misc/bayeux2_2': 'tapestry_bayeux2_2', 'misc/bayeux2_end': 'tapestry_bayeux2_end',
    'misc/bayeux2_link': 'tapestry_bayeux2_link', 'misc/bayeux2_start': 'tapestry_bayeux2_start',
    'misc/bayeux_2': 'tapestry_bayeux_2', 'misc/bayeux_link': 'tapestry_bayeux_link',
    'misc/bayeux_start': 'tapestry_bayeux_start', 'misc/bayuex_end': 'tapestry_bayeux_end'}
# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    ('models/props/brazier.abc', 'skins/props/brazier.dtx'): 'brazier',
    ('models/props/hangingbrazierbowl.abc', 'skins/props/hangingbrazierbowl3.dtx'): 'hangingbowl',
    ('models/props/hangingbrazierbowl2.abc', 'skins/props/hangingbrazierbowl3.dtx'): 'hangingbowl2',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/bench04.abc', 'skins/props/bench04.dtx'): 'bench04',
    ('models/props/bench_stone01.abc', 'skins/props/bench_stone.dtx'): 'benchstone01',
    ('models/props/bench_stone02.abc', 'skins/props/bench_stone.dtx'): 'benchstone02',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'book',
    ('models/props/bookcase01ew.abc', 'skins/props/bookcase01.dtx'): 'bookcase01ew',
    ('models/props/bookcase01ns.abc', 'skins/props/bookcase01.dtx'): 'bookcase01ns',
    ('models/props/cabinet01ns.abc', 'skins/props/cabinet01.dtx'): 'cabinet01ns',
    ('models/props/cabinet04.abc', 'skins/props/cabinet04.dtx'): 'cabinet04',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair_fordesk01.abc', 'skins/props/chair_fordesk01.dtx'): 'chairdesk01',
    ('models/props/chair_fordesk03.abc', 'skins/props/chair_fordesk03.dtx'): 'chairdesk03',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/desk01ns.abc', 'skins/props/desk01.dtx'): 'desk01ns',
    ('models/props/desk03.abc', 'skins/props/desk03.dtx'): 'desk03',
    ('models/props/harp.abc', 'skins/props/harp.dtx'): 'harp',
    ('models/props/key2.abc', 'skins/props/key2.dtx'): 'key2',
    ('models/props/table02.abc', 'skins/props/table01.dtx'): 'table02',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/walltorch.abc', 'skins/props/walltorch.dtx'): 'walltorch',
    ('models/props/chest1.abc', 'skins/props/chest2.dtx'): 'chest',
    ('models/props/chest3.abc', 'skins/props/chest3.dtx'): 'chest3',
    ('models/pickupitems/quest/goldenhonk.abc', 'skins/pickupitems/quest/goldenhonk.dtx'): 'goldenhonk',
}
MODELS.update({('models/props/tapestry-old01.abc', f'textures/leveltextures/{skin}.dtx'): prop
               for skin, prop in TAPESTRY_SKINS.items()})
# The book placements differ by pitch (decorations turn about z only): Book0 lies flat, Book1 leans 14.6 degrees on
# the reading stand. One model each, the pitch baked in.
BOOK_PROPS = {0.0: 'bookflat', 0.255: 'booktilt15'}
BOOK_TILT = {'booktilt15': (0.2548180818557739, 0.0)}
# Decorations another project built from the same ABC model, skin and placement scale (prop -> owning project); their
# rows, bindings and GLBs are reused unchanged. (The isle's mm9_book has its lectern tilt baked in: not reused.)
REUSED = {'barrel': ANSKRAM, 'chair': ANSKRAM, 'crate': ANSKRAM, 'desk01ns': ANSKRAM, 'tableround': ANSKRAM,
          'walltorch': ANSKRAM, 'chest': ANSKRAM}
CLASSES = {'Prop', 'Brazier', 'WallTorch', 'TreasureChest', 'PickupItem'}     # not the six Fish


def key(path):
    return (path or '').replace('\\', '/').lower().strip()


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def object_prop(o):
    p = o['props']
    prop = MODELS[(key(p['Filename']), key(p.get('Skin')))]
    if prop == 'book':
        return BOOK_PROPS[round(float(p['Rotation'][0]), 3)]
    return prop


def placements():
    """(object index, prop id) of every decoration object."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')]


def source_prop(prop):
    return 'book' if prop in BOOK_PROPS.values() else prop


def built_props():
    return sorted((set(MODELS.values()) - set(REUSED) - {'book'}) | set(BOOK_PROPS.values()))


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
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    counts = Counter(prop for _, prop in placements())
    print(len(counts), 'props,', sum(counts.values()), 'placements;',
          Counter(o['class'] for o in out if o['class'] in CLASSES))
    print('built:', [(p, counts[p]) for p in built_props()])
    print('reused:', [(p, counts[p]) for p in sorted(REUSED)])


if __name__ == '__main__':
    main()

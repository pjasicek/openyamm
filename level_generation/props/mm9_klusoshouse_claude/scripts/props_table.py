"""Klusos House's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
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
PROJECT = REPO / 'level_generation/projects/mm9r_klusoshouse'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/klusoshouse.raw_objects.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by the Anskram Keep, Temple of Honk, Lich Lab, Drangheim Prison, isle and Ruined Temple projects
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/bed.abc', 'skins/props/bed.dtx'): 'bed',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/chair02.abc', 'skins/props/chair02.dtx'): 'chair02',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet04.dtx'): 'weaponscabinet04',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/cabinet01ns.abc', 'skins/props/cabinet01.dtx'): 'cabinet01ns',
    ('models/props/cabinet04.abc', 'skins/props/cabinet04.dtx'): 'cabinet04',
    ('models/props/table02.abc', 'skins/props/table01.dtx'): 'table02',
    ('models/props/chair03.abc', 'skins/props/chair03.dtx'): 'chair03',
    ('models/props/table01ns.abc', 'skins/props/table01.dtx'): 'table01ns',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
    ('models/props/cabinet04ns.abc', 'skins/props/cabinet04.dtx'): 'cabinet04ns',
    ('models/props/shelfitem06.abc', 'skins/props/shelfitem06.dtx'): 'shelfitem06',
    ('models/props/shelfitem07.abc', 'skins/props/shelfitem07.dtx'): 'shelfitem07',
    ('models/props/shelfitem08.abc', 'skins/props/shelfitem08.dtx'): 'shelfitem08',
    ('models/props/logsburning.abc', 'skins/props/logsburning.dtx'): 'logsburning',
    ('models/props/chandelier3.abc', 'skins/props/chandelier3.dtx'): 'chandelier3',
    # built here
    ('models/props/wallcandle.abc', 'skins/props/wallcandle.dtx'): 'wallcandle',
    ('models/props/basket_fruit.abc', 'skins/props/basket_fruit.dtx'): 'basketfruit',
    ('models/props/basket_veggies.abc', 'skins/props/basket_veggies.dtx'): 'basketveggies',
    ('models/props/bed02.abc', 'skins/props/bed02.dtx'): 'bed02',
    ('models/props/cabinet01.abc', 'skins/props/cabinet01.dtx'): 'cabinet01',
    ('models/props/cabinet02.abc', 'skins/props/cabinet02.dtx'): 'cabinet02',
    ('models/props/cabinet02ns.abc', 'skins/props/cabinet02.dtx'): 'cabinet02ns',
    ('models/props/cabinet03.abc', 'skins/props/cabinet03.dtx'): 'cabinet03',
    ('models/props/cabinet03ns.abc', 'skins/props/cabinet03.dtx'): 'cabinet03ns',
    ('models/props/cabinet05.abc', 'skins/props/cabinet05.dtx'): 'cabinet05',
    ('models/props/dresser.abc', 'skins/props/dresserfancy.dtx'): 'dresserfancy',
    ('models/props/dresserns.abc', 'skins/props/dresserfancy.dtx'): 'dresserfancyns',
    ('models/props/pew2ns.abc', 'skins/props/pew2.dtx'): 'pew2ns',
    ('models/props/pitcher01.abc', 'skins/props/pantry-items.dtx'): 'pitcher01',
    ('models/props/plate-stack1.abc', 'skins/props/plate2.dtx'): 'platestack1',
    ('models/props/plate-stack2.abc', 'skins/props/plate2.dtx'): 'platestack2',
    ('models/props/shield.abc', 'skins/props/shield3.dtx'): 'shield3',
    ('models/props/stovens.abc', 'skins/props/stove.dtx'): 'stovens',
    ('models/props/tableround4.abc', 'skins/props/tableround5.dtx'): 'tableround5',
    ('models/props/tabletrestle.abc', 'skins/props/tabletrestle2.dtx'): 'tabletrestle2',
    ('models/weapons/dirk.abc', 'skins/weapons/dirk.dtx'): 'dirk',          # the Blackheart (Blackheart.scr)
}
TILTED = {}
BOOK_TILT = {'shield3': (1.581268, 0.0)}      # Prop27 hangs on the wall: MM9's pitch baked in (decorations turn about z only)
SOURCES = {}
ISLE_WORK = ISLE
LICHLAB = REPO / 'level_generation/props/mm9_lichlab_claude'
TEMPLE = REPO / 'level_generation/props/mm9_templeofhonk_claude'
DRANGHEIM = REPO / 'level_generation/props/mm9_drangheimprison_claude'
RUINED = REPO / 'level_generation/props/mm9_ruinedtemple_claude'
# Decorations another project built from the same ABC model and skin (prop -> owning project).
REUSED = {'barrel': ANSKRAM, 'bed': ANSKRAM, 'bookcase02ew': ANSKRAM, 'chair02': ANSKRAM, 'scroll': ANSKRAM,
          'weaponscabinet04': ANSKRAM, 'tableround': ANSKRAM, 'cabinet01ns': TEMPLE, 'cabinet04': TEMPLE,
          'table02': TEMPLE, 'chair03': LICHLAB, 'table01ns': LICHLAB, 'blackchest': LICHLAB, 'cabinet04ns': DRANGHEIM,
          'shelfitem06': DRANGHEIM, 'shelfitem07': DRANGHEIM, 'shelfitem08': DRANGHEIM, 'logsburning': ISLE,
          'chandelier3': RUINED}
CLASSES = {'Prop', 'CandleProp', 'TreasureChest', 'BonePile', 'DestructableProp', 'Barrel'}
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

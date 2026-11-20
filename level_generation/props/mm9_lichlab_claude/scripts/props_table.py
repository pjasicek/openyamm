"""Lich Lab's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them, and the ABC
placement binding origins. Props whose model and skin match an installed isle or Anskram Keep decoration are reused
(REUSED: their decoration rows, bindings and GLBs stay where they are); the rest are built here.

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
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/lichlab.raw_objects.yml'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by the isle (book: its own tilt, not these) or Anskram props projects
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/cookpot.abc', 'skins/props/cookpot.dtx'): 'cookpot',
    # built here
    ('models/props/pew3ns.abc', 'skins/props/pew3.dtx'): 'pew3ns',
    ('models/props/throne.abc', 'skins/props/throne.dtx'): 'throne',
    ('models/props/chair_fordesk03.abc', 'skins/props/chair_fordesk03.dtx'): 'chairdesk03',
    ('models/props/desk03.abc', 'skins/props/desk03.dtx'): 'desk03',
    ('models/props/torturecage01.abc', 'skins/props/torturecage01.dtx'): 'torturecage01',
    ('models/pickupitems/jar_empty.abc', 'skins/pickupitems/jar_empty.dtx'): 'jar',
    ('models/pickupitems/jar_broken.abc', 'skins/pickupitems/jar_empty.dtx'): 'jarbroken',
    ('models/props/skeletonstatue.abc', 'skins/props/skeletonstatue.dtx;skins/props/skelstatuebase.dtx'):
        'skeletonstatue',
    ('models/props/torturerack01.abc', 'skins/props/torturerack01.dtx'): 'torturerack01',
    ('models/props/table02.abc', 'skins/props/table01.dtx'): 'table02',
    ('models/props/table01ns.abc', 'skins/props/table01.dtx'): 'table01ns',
    ('models/props/table01.abc', 'skins/props/table01.dtx'): 'table01',
    ('models/props/shelfitem01.abc', 'skins/props/shelfitem01.dtx'): 'shelfitem01',
    ('models/props/shelfitem02.abc', 'skins/props/shelfitem02.dtx'): 'shelfitem02',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shelfitem05.abc', 'skins/props/shelfitem05.dtx'): 'shelfitem05',
    ('models/props/pillory.abc', 'skins/props/pillory.dtx'): 'pillory',
    ('models/props/flayingbench.abc', 'skins/props/flayingbench.dtx'): 'flayingbench',
    ('models/props/torturecrusher01.abc', 'skins/props/torturecrusher.dtx'): 'torturecrusher01',
    ('models/props/torturecrusher02.abc', 'skins/props/torturecrusher.dtx'): 'torturecrusher02',
    ('models/props/torturewheel01.abc', 'skins/props/torturewheel01.dtx'): 'torturewheel01',
    ('models/props/torturewheel02.abc', 'skins/props/torturewheel01.dtx'): 'torturewheel02',
    ('models/props/skeletoncage.abc', 'skins/props/skeletoncage.dtx'): 'skeletoncage',
    ('models/props/bookstack01.abc', 'skins/props/bookstack01.dtx'): 'bookstack01',
    ('models/props/chair03.abc', 'skins/props/chair03.dtx'): 'chair03',
    ('models/props/burner.abc', 'skins/props/burner.dtx'): 'burner',
    ('models/props/scroll3.abc', 'skins/props/scroll3.dtx'): 'scroll3',
    ('models/props/scroll-double.abc', 'skins/props/scrolldouble.dtx'): 'scrolldouble',
    ('models/props/scroll2.abc', 'skins/props/scroll2.dtx'): 'scroll2',
    ('models/pickupitems/quest/bagherbs2.abc', 'skins/pickupitems/quest/bagherbs1.dtx;skins/pickupitems/quest/herbs.dtx'):
        'bagherbs',
    ('models/props/skeletonsitting.abc', 'skins/props/skeleton.dtx'): 'skeletonsitting',
    ('models/props/switch02.abc', 'skins/props/switch02.dtx'): 'switch02',
    ('models/props/headsmansblock.abc', 'skins/props/headsmansblock.dtx'): 'headsmansblock',
    ('models/props/lichengine.abc', 'skins/props/lichengine.dtx'): 'lichengine',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
    ('models/props/beaker01.abc', 'skins/props/beaker01.dtx'): 'beaker01',
    ('models/props/cauldron01.abc', 'skins/props/cauldron01.dtx'): 'cauldron01',
    ('models/props/podium01.abc', 'skins/props/podium01.dtx'): 'podium01',
    # the log pile without the isle's flame cards (no Fire object burns on it here)
    ('models/props/logsburning.abc', 'skins/props/logsburning.dtx'): 'logs',
    # the book with each placement's pitch baked in (decorations turn about z only)
    ('models/props/book.abc', 'skins/props/book.dtx'): 'book',
}
# Installed decorations reused by model (decoration GLB name -> the project that owns it).
REUSED = {'chair': 'anskram', 'crate': 'anskram', 'barrel': 'anskram', 'chest1': 'anskram', 'scroll': 'anskram',
          'cookpot': 'isle', 'bookflat': 'templeofhonk', 'chairdesk03': 'templeofhonk', 'desk03': 'templeofhonk',
          'table02': 'templeofhonk'}
TEMPLE = REPO / 'level_generation/props/mm9_templeofhonk_claude'
# The Temple of Honk props project built and installed these four first, from the same ABC and skin (identical
# meshes): their GLBs and rows are reused, never installed from here.
# Object-specific choices. BonePile1 names MM9's lever model with a missing skin (a data slip: a lever drawn with a
# skeleton skin where the other two bone piles are sitting skeletons); it becomes a sitting skeleton too.
OBJECT_PROP = {'BonePile1': 'skeletonsitting'}
# The book placements differ by pitch: Book0 lies flat, the three shooting books (firebook2-4) are tilted 27 degrees on
# their lecterns. One model each (the pitch baked in).
BOOK_PROPS = {0.0: 'bookflat', 0.471: 'booktilt'}
CLASSES = {'Prop', 'Barrel', 'BonePile', 'TreasureChest'}


def key(path):
    return (path or '').replace('\\', '/').lower().strip()


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def object_prop(o):
    p = o['props']
    if p.get('Name') in OBJECT_PROP:
        return OBJECT_PROP[p['Name']]
    prop = MODELS[(key(p['Filename']), key(p.get('Skin')))]
    if prop == 'book':
        pitch = round(float(p['Rotation'][0]), 3)
        return BOOK_PROPS[pitch]
    return prop


def placements():
    """(object index, prop id) of every decoration object."""
    out = []
    for o in objects():
        p = o['props']
        if o['class'] in CLASSES and p.get('Filename'):
            out.append((o['index'], object_prop(o)))
    return out


def built_props():
    """The props built in this project (not reused)."""
    names = set(MODELS.values()) - {'book'}
    return sorted((names | set(BOOK_PROPS.values())) - set(REUSED))


def source_prop(prop):
    """The MODELS id whose source a built prop converts (the book variants share the book)."""
    return 'book' if prop in BOOK_PROPS.values() else prop


def source(prop):
    """(model path, [skin paths]) under mm9/extracted for a prop id."""
    model, skins = next(k for k, v in MODELS.items() if v == source_prop(prop))
    return (REPO / 'mm9/extracted/MODELS/MODELS' / model[len('models/'):],
            [REPO / 'mm9/extracted/SKINS/SKINS' / s[len('skins/'):] for s in skins.split(';')])


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
    for prop in sorted(set(MODELS.values())):
        model, _ = source(prop)
        info = abc_static_model_placement_info(read_abc(resolve(model)))
        origins[prop] = list(info.binding_origin) if info else [0.0, 0.0, 0.0]
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    counts = Counter(prop for _, prop in placements())
    print(len(counts), 'props,', sum(counts.values()), 'placements')
    print('built:', [(p, counts[p]) for p in built_props()])
    print('reused:', [(p, counts[p]) for p in sorted(REUSED)])


if __name__ == '__main__':
    main()

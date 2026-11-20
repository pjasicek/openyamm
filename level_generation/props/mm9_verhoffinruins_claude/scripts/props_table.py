"""The Verhoffin Ruins' prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
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
PROJECT = REPO / 'level_generation/projects/mm9r_verhoffinruins'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/verhoffinruins.raw_objects.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/props/minelantern.abc', 'skins/props/minelantern.dtx'): 'minelantern',
    ('models/props/sconce1.abc', 'skins/props/sconce1.dtx'): 'sconce1',
    ('models/props/manacles.abc', 'skins/props/manacles.dtx'): 'manacles',
    ('models/props/key1.abc', 'skins/props/key1.dtx'): 'key1',
    ('models/props/debris/skeletondebris03.abc', 'skins/props/debris/skeletondebris.dtx'): 'skeletondebris03',
    ('models/pickupitems/quest/capstone.abc', 'skins/pickupitems/quest/capstone.dtx'): 'capstone',
    ('models/pickupitems/quest/greatbook.abc', 'skins/pickupitems/quest/greatbookfake.dtx'): 'greatbookfake',
    ('models/pickupitems/quest/writ.abc', 'skins/pickupitems/quest/writ.dtx'): 'writ',
    # reused: built by another MM9 props project (same ABC model and skin)
    ('models/props/bedmedium2.abc', 'skins/props/bedmedium2.dtx'): 'bedmedium2',
    ('models/props/bench01.abc', 'skins/props/bench01.dtx'): 'bench01',
    ('models/props/chair_fordesk03.abc', 'skins/props/chair_fordesk03.dtx'): 'chairdesk03',
    ('models/props/debris/skeletondebris02.abc', 'skins/props/debris/skeletondebris.dtx'): 'skeletondebris02',
    ('models/props/flayingbench.abc', 'skins/props/flayingbench.dtx'): 'flayingbench',
    ('models/props/pew3ns.abc', 'skins/props/pew3.dtx'): 'pew3ns',
    ('models/props/pillarstand.abc', 'skins/props/pillarstand.dtx'): 'pillarstand',
    ('models/props/pillory.abc', 'skins/props/pillory.dtx'): 'pillory',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/skeletoncage.abc', 'skins/props/skeletoncage.dtx'): 'skeletoncage',
    ('models/props/table02.abc', 'skins/props/table01.dtx'): 'table02',
    ('models/props/tableround2.abc', 'skins/props/tableround2.dtx'): 'tableround2',
    ('models/props/tableround3.abc', 'skins/props/tableround3.dtx'): 'tableround3',
    ('models/props/torturerack01.abc', 'skins/props/torturerack01.dtx'): 'torturerack01',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet01.dtx'): 'weaponscabinet01',
    ('models/props/weaponscabinet02.abc', 'skins/props/weaponscabinet02.dtx'): 'weaponscabinet02',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
}
PROPS_DIR = REPO / 'level_generation/props'
# Decorations another project built from the same ABC model and skin (prop -> owning project, the one whose finished
# GLB is the installed one): their GLBs and rows stay where they are; a placement scale they do not have becomes a
# variant row here (tables.py).
REUSED = {prop: PROPS_DIR / owner for prop, owner in {
    'bedmedium2': 'mm9_drangheimprison_claude', 'bench01': 'mm9_drangheimprison_claude',
    'chairdesk03': 'mm9_lichlab_claude', 'skeletondebris02': 'mm9_drangheimprison_claude',
    'flayingbench': 'mm9_lichlab_claude', 'pew3ns': 'mm9_lichlab_claude', 'pillarstand': 'mm9_chasmofthedead_claude',
    'pillory': 'mm9_lichlab_claude', 'scroll': 'mm9_anskramkeep_claude', 'skeletoncage': 'mm9_lichlab_claude',
    'table02': 'mm9_templeofhonk_claude', 'tableround2': 'mm9_drangheimprison_claude',
    'tableround3': 'mm9_drangheimprison_claude', 'torturerack01': 'mm9_lichlab_claude',
    'weaponscabinet01': 'mm9_anskramkeep_claude', 'weaponscabinet02': 'mm9_drangheimprison_claude',
    'chest1': 'mm9_anskramkeep_claude', 'blackchest': 'mm9_lichlab_claude'}.items()}
# The PropDamager spikes in the electrified pit: the map project places Anskram's spikepit (they lie in the pit).
CLASSES = {'Prop', 'Torch', 'TreasureChest'}
# Tipped over in MM9 (decorations turn about z only): their pitch and roll baked in, a model each (the Chasm's route).
TILTED = {'Chair0': 'chairdesk03p90', 'Chair1': 'chairdesk03p270', 'Chair2': 'chairdesk03p270',
          'Table2': 'tableround2p60', 'Table4': 'tableround2p60', 'Cabinet2': 'weaponscabinet02tip',
          'Prop3': 'scrollp268',
          # the beds lie on their side: PropAnim.scr "onside" loops the ABC's onside animation (a full export, posed)
          **{f'Bed{k}': 'bedmedium2onside' for k in range(7)}}
SOURCES = {'chairdesk03p90': 'chairdesk03', 'chairdesk03p270': 'chairdesk03', 'tableround2p60': 'tableround2',
           'weaponscabinet02tip': 'weaponscabinet02', 'scrollp268': 'scroll',
           'bedmedium2onside': 'bedmedium2'}
BOOK_TILT = {'chairdesk03p90': (1.5707964, 0.0), 'chairdesk03p270': (4.712389, 0.0),
             'tableround2p60': (1.0471976, 0.0), 'weaponscabinet02tip': (4.712389, 0.8726646),
             'scrollp268': (4.6862092, 0.0)}
BOOK_PROPS = {}
# Props built in an animation's pose (action, frame): the beds' PropAnim.scr "onside" (the pews' ABC has no onside).
POSES = {'bedmedium2onside': ('onside', 1)}
# Flame-only decorations (no ABC): the pentagram's fires, by colour (PentaFire1-5 in the puzzle's order).
PENTAFIRES = ['red', 'yellow', 'blue', 'green', 'orange']


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

"""Lindisfarne Monastery's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place
them, and the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9
props project are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they
are); the rest are built here (Dook's Castle's route, itself Drangheim Prison's and the Lich Lab's: one material per
MM9 skin, the isle's blib build and finish checks).

    python3 scripts/props_table.py            # work/raw_objects_compact.json, work/binding_origins.json, summary
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
PROPS_DIR = REPO / 'level_generation/props'
ISLE = PROPS_DIR / 'mm9_isleofashes_claude'
ANSKRAM = PROPS_DIR / 'mm9_anskramkeep_claude'
TEMPLE = PROPS_DIR / 'mm9_templeofhonk_claude'
LICHLAB = PROPS_DIR / 'mm9_lichlab_claude'
CHASM = PROPS_DIR / 'mm9_chasmofthedead_claude'
TASAR = PROPS_DIR / 'mm9_tasaracademy_claude'
PROJECT = REPO / 'level_generation/projects/mm9r_lindisfarnemonastery'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/lindisfarnemonastery.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/lindisfarnemonastery.odm'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/bench_stone02.abc', 'skins/props/bench_stone.dtx'): 'benchstone02',
    ('models/props/chair03.abc', 'skins/props/chair03.dtx'): 'chair03',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/pillarstand.abc', 'skins/props/pillarstand.dtx'): 'pillarstand',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',      # the isle's 'book' is tilted (lectern)
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/walltorch.abc', 'skins/props/walltorch.dtx'): 'walltorch',
    ('models/props/candle.abc', 'skins/props/candle.dtx'): 'candle',
    # built here
    ('models/props/bell.abc', 'skins/props/bell.dtx'): 'bell',
    ('models/props/pew2.abc', 'skins/props/pew2.dtx'): 'pew2',
    ('models/props/bench_large1ns.abc', 'skins/props/bench_large1.dtx'): 'benchlarge1ns',
    ('models/props/bookcase01ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase01ew2',   # the Temple's has bookcase01
    ('models/props/chair_fordesk03.abc', 'skins/props/chair_fordesk03b.dtx'): 'chairdesk03b',
    ('models/props/desk03.abc', 'skins/props/desk03b.dtx'): 'desk03b',
    ('models/props/washtub_table.abc', 'skins/props/washtub_table.dtx'): 'washtubtable',
    ('models/props/podium02.abc', 'skins/props/podium02.dtx'): 'podium02',
    ('models/props/reliquary.abc', 'skins/props/reliquary.dtx'): 'reliquary',
    ('models/props/plantsandtrees/tree04.abc',
     'skins/props/plantsandtrees/treebark2.dtx;skins/props/plantsandtrees/treebranch3.dtx'): 'tree04',
    ('models/weapons/thjorad.abc', 'skins/weapons/thjorad.dtx'): 'thjorad',     # the quest maul (Thjorad.scr)
}
REUSED = {'benchstone02': TEMPLE, 'chair03': LICHLAB, 'tableround': ANSKRAM, 'pillarstand': CHASM, 'bookflat': TEMPLE,
          'scroll': ANSKRAM, 'walltorch': ANSKRAM, 'candle': TASAR}
OBJECT_PROP = {}
TILTED = {}
TILTS = {}
BOOK_PROPS = {}
CLASSES = {'Prop', 'WallTorch', 'CandleProp'}
OWNERS = {}
# PropAnim.scr's animation (the raised coffins' and stone benches' "ns", a quarter turn from Static_Model) is posed by
# the map converter for every map (mm9r_common/dungeon/prop_pose.py, 2026-11-07); placements.py writes the placement
# as baked. This table stays empty.
POSE_TURN = {}
# Models built in an animation pose (full export, posed in Blender): the bell's rigid export is its bind pose, which
# hangs the bell 12 units higher than MM9's static_model pose (the pose MM9 shows between rings and the old map baked).
POSES = {'bell': ('static_model', 0)}


def key(path):
    return ';'.join(part.replace('\\', '/').lower().strip() for part in (path or '').split(';'))


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def object_prop(o):
    p = o['props']
    if p.get('Name') in OBJECT_PROP:
        return OBJECT_PROP[p['Name']]
    return MODELS[(key(p['Filename']), key(p.get('Skin')))]


def placements():
    """(object index, prop id) of every decoration object."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')]


def built_props():
    """The props built in this project (not reused)."""
    return sorted((set(MODELS.values()) | set(TILTED)) - set(REUSED))


def home(prop):
    return REUSED.get(prop, HERE)


def source_prop(prop):
    """The MODELS id whose source a built prop converts (the tilted variants share their upright model's)."""
    return TILTED[prop][0] if prop in TILTED else prop


def source(prop):
    """(model path, [skin paths]) under mm9/extracted for a prop id."""
    model, skins = next(k for k, v in MODELS.items() if v == source_prop(prop))
    roots = {'skins': 'SKINS/SKINS', 'textures': 'TEXTURES/TEXTURES'}

    def skin_path(s):
        top, rest = s.split('/', 1)
        return REPO / 'mm9/extracted' / roots[top] / rest
    return (REPO / 'mm9/extracted/MODELS/MODELS' / model[len('models/'):], [skin_path(s) for s in skins.split(';')])


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
    print(len(counts), 'props,', sum(counts.values()), 'placements;',
          Counter(o['class'] for o in out if o['class'] in CLASSES))
    print('built:', [(p, counts[p]) for p in built_props()])
    print('reused:', [(p, counts[p]) for p in sorted(REUSED)])


if __name__ == '__main__':
    main()

"""Yanmir's Fort's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them, and
the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9 props
project are reused (REUSED: prop -> owning project, the one whose work/mm9_deco_<prop>.glb is md5-identical to the
installed assets_source/engine/models/ GLB; their decoration rows, bindings and GLBs stay where they are); the rest are
built here (Lindisfarne Monastery's route: one material per MM9 skin, the isle's blib build and finish checks, with the
Anskram flame cards added for the claw lamps and torches).

Tilted objects (decorations turn about z only: pitch and roll are baked into a model of their own, the Verhoffin Ruins
route): every ClawLamp hangs upside down (pitch pi) and every ClawTorch is rolled half round (roll pi); five chairs and
a stool lie toppled (pitch 270 / 90 degrees). PropAnim.scr "onside" beds use Verhoffin's posed bedmedium2onside.

    python3 scripts/props_table.py            # work/raw_objects_compact.json, work/binding_origins.json, summary
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
PROPS_DIR = REPO / 'level_generation/props'
ISLE = PROPS_DIR / 'mm9_isleofashes_claude'
PROJECT = REPO / 'level_generation/projects/mm9r_yanmirsfort'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/yanmirsfort.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/yanmirsfort.odm'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id
# (the upright source; a tilted variant names it in SOURCES).
MODELS = {
    # built here (only through their tilted variants for the claws)
    ('models/props/clawlamp.abc', 'skins/props/clawlamp.dtx'): 'clawlamp',
    ('models/props/clawtorch.abc', 'skins/props/clawtorch.dtx'): 'clawtorch',
    ('models/props/chest-rusty01.abc', 'skins/props/chest1.dtx'): 'chestrusty01',
    ('models/props/crate.abc', 'textures/a6frosgaard/misc/yanmiricepillar.dtx'): 'crateice',   # the ice blocks
    ('models/props/stool02.abc', 'skins/props/stool02.dtx'): 'stool02',
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/table_bench.abc', 'skins/props/table_bench.dtx'): 'tablebench2',
    ('models/props/bed.abc', 'skins/props/bed.dtx'): 'bed',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/bedmedium2.abc', 'skins/props/bedmedium2.dtx'): 'bedmedium2',
    ('models/props/bed_ornate.abc', 'skins/props/bed_ornate.dtx'): 'bedornate',
    ('models/props/bonepile.abc', 'skins/props/bonepile.dtx'): 'bonepile',
    ('models/props/bucket01.abc', 'skins/props/bucket01.dtx'): 'bucket01',
    ('models/props/cabinet04ns.abc', 'skins/props/cabinet04.dtx'): 'cabinet04ns',
    ('models/props/cabinet05ns.abc', 'skins/props/cabinet05.dtx'): 'cabinet05ns',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair_fordesk03.abc', 'skins/props/chair_fordesk03.dtx'): 'chairdesk03',
    ('models/props/dresserns.abc', 'skins/props/dresserfancy.dtx'): 'dresserfancyns',
    ('models/props/pew3.abc', 'skins/props/pew3.dtx'): 'pew3',
    ('models/props/pew3ns.abc', 'skins/props/pew3.dtx'): 'pew3ns',
    ('models/props/stool01.abc', 'skins/props/stool01.dtx'): 'stool01',
    ('models/props/stove.abc', 'skins/props/stove.dtx'): 'stove',
    ('models/props/tableround.abc', 'skins/props/tableroundplain.dtx'): 'tableroundplain',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/tableround3.abc', 'skins/props/tableround3.dtx'): 'tableround3',
    ('models/props/throne.abc', 'skins/props/throne.dtx'): 'throne',
    ('models/props/trashpile.abc', 'skins/props/trashpile.dtx'): 'trashpile',
    ('models/props/weaponscabinet02.abc', 'skins/props/weaponscabinet02.dtx'): 'weaponscabinet02',
    ('models/props/woodbin.abc', 'skins/props/woodbin.dtx'): 'woodbin',
    ('models/props/key2.abc', 'skins/props/key2.dtx'): 'key2',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
}
REUSED = {prop: PROPS_DIR / owner for prop, owner in {
    'barrel': 'mm9_anskramkeep_claude', 'crate': 'mm9_anskramkeep_claude', 'bed': 'mm9_anskramkeep_claude',
    'bedmedium': 'mm9_anskramkeep_claude', 'chair': 'mm9_anskramkeep_claude', 'tableround': 'mm9_anskramkeep_claude',
    'trashpile': 'mm9_anskramkeep_claude', 'tablebench2': 'mm9_drangheimprison_claude',
    'bucket01': 'mm9_drangheimprison_claude', 'cabinet04ns': 'mm9_drangheimprison_claude',
    'cabinet05ns': 'mm9_drangheimprison_claude', 'stove': 'mm9_drangheimprison_claude',
    'tableround3': 'mm9_drangheimprison_claude', 'weaponscabinet02': 'mm9_drangheimprison_claude',
    'bedmedium2onside': 'mm9_verhoffinruins_claude', 'chairdesk03p270': 'mm9_verhoffinruins_claude',
    'bedornate': 'mm9_dookscastle_claude', 'bonepile': 'mm9_beethoven_claude',
    'chairdesk03': 'mm9_templeofhonk_claude', 'key2': 'mm9_templeofhonk_claude',
    'dresserfancyns': 'mm9_klusoshouse_claude', 'pew3': 'mm9_bathhouse_claude', 'pew3ns': 'mm9_lichlab_claude',
    'throne': 'mm9_lichlab_claude', 'blackchest': 'mm9_lichlab_claude', 'stool01': 'mm9_thjoradmine_claude',
    'tableroundplain': 'mm9_thjoradmine_claude', 'woodbin': 'mm9_thjoradmine_claude'}.items()}
# Tilted variants: prop -> its upright source prop, and its (pitch, roll) in radians (the transcoder's object pitch
# about x, then roll about y; baked into the model, the isle's tilt_matrix). The chairdesk03p270 values are
# Verhoffin's (its BOOK_TILT), which built that model.
SOURCES = {'clawlampp180': 'clawlamp', 'clawtorchr180': 'clawtorch', 'chairp270': 'chair', 'stool01p90': 'stool01',
           'chairdesk03p270': 'chairdesk03', 'bedmedium2onside': 'bedmedium2'}
TILTS = {'clawlampp180': (math.pi, 0.0), 'clawtorchr180': (0.0, math.pi), 'chairp270': (4.712389, 0.0),
         'stool01p90': (1.5707964, 0.0), 'chairdesk03p270': (4.712389, 0.0)}
# (source prop, pitch, roll) of a DAT object -> the tilted variant that shows it
TILT_OF = {('clawlamp', 180, 0): 'clawlampp180', ('clawtorch', 0, 180): 'clawtorchr180',
           ('chair', 270, 0): 'chairp270', ('stool01', 90, 0): 'stool01p90', ('chairdesk03', 270, 0): 'chairdesk03p270'}
# PropAnim.scr "onside" loops the ABC's onside animation: BedMedium2's (the beds lie on their side) is Verhoffin's
# posed bedmedium2onside. Posed props (placements.py): MM9 shows the animation pose and drops them to the floor; the old
# bake is the bind pose. KEY2.abc's Static_Model (the pose MM9 shows, and the one Blender's import evaluates: the
# Temple's mm9_key2) lays the key flat (LT extents 6.81 x 0.51 up x 2.67), its bind pose (both maps' old bakes: this
# map's key 44 x 36 x 21 at Scale 3) stands it on its edge.
ONSIDE = {'bedmedium2': 'bedmedium2onside'}
POSES = {'bedmedium2onside': ('onside', 1), 'key2': ('Static_Model', 0)}
POSE_TURN = {}
CLASSES = {'Prop', 'CandleProp', 'DestructableProp', 'TreasureChest'}


def key(path):
    return ';'.join(part.replace('\\', '/').lower().strip() for part in (path or '').split(';'))


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def tilt_degrees(p):
    r = p.get('Rotation') or [0, 0, 0]
    return int(round(math.degrees(float(r[0])))) % 360, int(round(math.degrees(float(r[2])))) % 360


def object_prop(o):
    p = o['props']
    prop = MODELS[(key(p['Filename']), key(p.get('Skin')))]
    pitch, roll = tilt_degrees(p)
    if (pitch, roll) != (0, 0):
        if (prop, pitch, roll) not in TILT_OF:
            raise SystemExit(f"{p['Name']}: {prop} tilted pitch {pitch} roll {roll} has no variant")
        return TILT_OF[(prop, pitch, roll)]
    if 'propanim' in (p.get('ScriptName') or '').lower() and (p.get('ScriptParams') or '').strip() == 'onside':
        if prop not in ONSIDE:
            raise SystemExit(f"{p['Name']}: {prop} PropAnim onside without a posed variant")
        return ONSIDE[prop]
    return prop


def placements():
    """(object index, prop id) of every decoration object."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')]


def source_prop(prop):
    return SOURCES.get(prop, prop)


def built_props():
    """The props built here: the placed ones (the claws only through their tilted variants) minus the reused."""
    try:
        placed = {prop for _, prop in placements()}
    except FileNotFoundError:
        placed = (set(MODELS.values()) | set(SOURCES)) - set(SOURCES.values())
    return sorted(placed - set(REUSED))


def home(prop):
    return REUSED.get(prop, HERE)


def source(prop):
    """(model path, [skin paths]) under mm9/extracted for a prop id."""
    model, skins = next(k for k, v in MODELS.items() if v == source_prop(prop))
    roots = {'models': 'MODELS/MODELS', 'skins': 'SKINS/SKINS', 'textures': 'TEXTURES/TEXTURES'}

    def path(s):
        top, rest = s.split('/', 1)
        return EXTRACTED / roots[top] / rest
    return path(model), [path(s) for s in skins.split(';')]


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
    for prop in sorted(set(MODELS.values())):
        model, _ = source(prop)
        info = abc_static_model_placement_info(read_abc(resolve(model)))
        origins[prop] = list(info.binding_origin) if info else [0.0, 0.0, 0.0]
    for prop, src in SOURCES.items():
        origins[prop] = origins[src]
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    counts = Counter(prop for _, prop in placements())
    print(len(counts), 'props,', sum(counts.values()), 'placements;',
          Counter(o['class'] for o in out if o['class'] in CLASSES and o['props'].get('Filename')))
    print('built:', [(p, counts[p]) for p in built_props()])
    print('reused:', [(p, counts[p]) for p in sorted(REUSED) if counts[p]])
    print('unused REUSED entries:', [p for p in sorted(REUSED) if not counts[p]])


if __name__ == '__main__':
    main()

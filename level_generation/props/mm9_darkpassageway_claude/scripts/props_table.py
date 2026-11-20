"""Dark Passageway's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
and the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9 props
project are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they are); the
rest are built here (Yanmir's Fort's route, itself Lindisfarne Monastery's with the Anskram flame cards: one material
per MM9 skin, the isle's blib build and finish checks).

The MM9 monster models placed as props (the bridge puzzle's small ice statuettes, Skin Icebolt at Scale 0.4, and the
canyon's four stone banshees, Skin Debris at Scale 2) are skinned ABCs: exported in full and posed in Blender
(POSES: the idle 'stand' at its first key; the first animation is a T-pose for two of them). One skin binds every ABC material (the
skeleton's dagger, the skeleton warrior's scimitar are material 1 and take the ice too).

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
PROJECT = REPO / 'level_generation/projects/mm9r_darkpassageway'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/darkpassageway.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/darkpassageway.odm'
EXTRACTED = REPO / 'mm9/extracted'

ICE = 'skins/spells/icebolt.dtx'
TREES = 'skins/props/plantsandtrees/'
# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/props/clawtorch.abc', 'skins/props/clawtorch.dtx'): 'clawtorch',     # upright (Yanmir's is rolled pi)
    ('models/props/crystal.abc', 'skins/props/crystal.dtx'): 'crystal',
    ('models/props/runestone.abc', 'skins/props/runestone.dtx'): 'runestone',
    ('models/props/plantsandtrees/bush03.abc', TREES + 'bush03.dtx'): 'bush03',
    ('models/props/plantsandtrees/bush05.abc', TREES + 'bush05.dtx'): 'bush05',
    ('models/props/plantsandtrees/tree01b.abc', f'{TREES}treebark1.dtx;{TREES}treebranch1.dtx'): 'tree01b',
    ('models/props/plantsandtrees/tree02.abc', f'{TREES}treebark2.dtx;{TREES}treebranch3.dtx'): 'tree02',
    ('models/props/plantsandtrees/tree05.abc', f'{TREES}treebark3.dtx;{TREES}treebranch4.dtx'): 'tree05',
    ('models/props/plantsandtrees/tree06.abc', f'{TREES}treebark3.dtx;{TREES}treebranch5.dtx'): 'tree06',
    ('models/skeleton.abc', ICE): 'iceskeleton',
    ('models/zombie.abc', ICE): 'icezombie',
    ('models/lich.abc', ICE): 'icelich',
    ('models/banshee.abc', ICE): 'icebanshee',
    ('models/terror.abc', ICE): 'iceterror',
    ('models/skeletonwarrior.abc', ICE): 'iceskeletonwarrior',
    ('models/banshee.abc', 'skins/spells/debris.dtx'): 'stonebanshee',
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/chest5.abc', 'skins/props/chest5.dtx'): 'chest5',
    ('models/props/logsburning.abc', 'skins/props/logsburning.dtx'): 'logsburning',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    # Dark Passageway's exit: MM9 skins this barrel (Prop36, at ExitPoint) with a water sprite frame (water125_0000), so
    # it reads as the portal it is; built here with that skin (2026-11-09; before, Anskram's barrel and its wood skin)
    ('models/props/barrel.abc', 'spritetextures/water/water125/water125_0000.dtx'): 'barrelwater',
    # the PropDamager spikes at the bottom of the spike trap pit (Spikes1; the map agent asked for it, 2026-10-31)
    ('models/props/spikepit.abc', 'skins/props/spikepit.dtx'): 'spikepit',
}
REUSED = {prop: PROPS_DIR / owner for prop, owner in {
    'chest5': 'mm9_chasmofthedead_claude', 'logsburning': 'mm9_isleofashes_claude', 'scroll': 'mm9_anskramkeep_claude',
    'spikepit': 'mm9_anskramkeep_claude'}.items()}
STATUES = {'iceskeleton', 'icezombie', 'icelich', 'icebanshee', 'iceterror', 'iceskeletonwarrior', 'stonebanshee'}
# MM9 draws a fire at a CandleProp (here all four claw torches: Blue 1, StartOn 1), not at a Prop: the lit claw torch
# is its own model with the orb flames (build.py ORB_FLAMES, 2026-10-31), so Dungeon of Secrets' 34 Prop claw torches
# keep reusing the flameless `clawtorch`, which stays built here (KEPT) though no object here places it.
SOURCES = {'clawtorchlit': 'clawtorch'}
LIT = {'clawtorch': 'clawtorchlit'}
KEPT = {'clawtorch'}
TILTS = {}
TILT_OF = {}
ONSIDE = {}
# Posed statues: (animation, frame) set in build (blib.import_raw) and placements (posed_points). The ABCs' first
# animation (static_model / static_model1 / bansetup: what Blender's import evaluates and the old map baked) is a T-pose
# for the skeleton and the zombie and a flat spread cape for the banshee (review/pose_study/sheet.png); the idle
# 'stand' ('standAir' for the banshee) at its first key stands every statue naturally: all seven use it.
POSES = {'iceskeleton': ('stand', 0), 'icezombie': ('stand', 0), 'icelich': ('stand', 0), 'iceterror': ('stand', 0),
         'iceskeletonwarrior': ('stand', 0), 'icebanshee': ('standAir', 0), 'stonebanshee': ('standAir', 0)}
POSE_TURN = {}
CLASSES = {'Prop', 'CandleProp', 'TreasureChest', 'PropDamager'}


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
    if o['class'] == 'CandleProp' and prop in LIT:
        return LIT[prop]
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
    """The props built here: the placed ones minus the reused."""
    try:
        placed = {prop for _, prop in placements()}
    except FileNotFoundError:
        placed = (set(MODELS.values()) | set(SOURCES)) - set(SOURCES.values())
    return sorted((placed | KEPT) - set(REUSED))


def home(prop):
    return REUSED.get(prop, HERE)


def source(prop):
    """(model path, [skin paths]) under mm9/extracted for a prop id."""
    model, skins = next(k for k, v in MODELS.items() if v == source_prop(prop))
    roots = {'models': 'MODELS/MODELS', 'skins': 'SKINS/SKINS', 'textures': 'TEXTURES/TEXTURES',
             'spritetextures': 'SPRITETEXTURES/SPRITETEXTURES'}

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

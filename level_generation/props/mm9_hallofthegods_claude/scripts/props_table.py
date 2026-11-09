r"""Hall of the Gods' prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
and the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9 props
project are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they are); the
rest are built here (Dark Passageway's route, itself Yanmir's Fort's and Lindisfarne Monastery's with the Anskram
flame cards: one material per MM9 skin, POSES, the isle's blib build and finish checks).

The six god statues (PropAnim.scr "statue": MM9 loops each model's `statue` animation) are the gods' own creature
ABCs with their *sculpt skins, exported in full and posed in Blender in `statue` at its first key (POSES; the bind
pose, which the old import baked, is a T-pose). Krohn carries three skins, one per ABC material (body, sword piece,
spear piece) in the DAT's order.

Not shipped by MM9 (MODELS.REZ has no such file; work/missing_models.txt): models\DragonAzure.abc (the two
DragonAzure objects), models\props\DragonThrone.abc and models\DragonPharoah.abc + skins\DragonPharoah.dtx: MM9
itself shows nothing there, and they get no decoration (SKIPPED). The only DragonPharoah MM9 ships,
models\props\DragonPharoah.abc with its DragonPharoahStatue skin (the 1000 Terrors' `dragonpharoah`, a dragon seated
on its own throne), was tried as a stand-in (ALIASES, PLACE_POSES, row mm9_dragonpharoah_x150): at the DAT spot it
stands inside Krohn's statue (32 LT apart; the stand-in is 659 units tall, Krohn's skirt hangs 103 units over the dais)
and overlaps the throne in front, so it is not placed (README).

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
PROJECT = REPO / 'level_generation/projects/mm9r_hallofthegods'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/hallofthegods.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/hallofthegods.odm'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/props/lionstatue.abc', 'skins/props/lionstatue.dtx'): 'lionstatue',
    ('models/props/dragonbrazier2.abc', 'skins/props/dragonbrazier.dtx'): 'dragonbrazier2',     # flame cards
    # the Ruined Temple's torchmetal is this model and skin with blue flames; these burn orange (FireColor 220/180/0)
    ('models/props/torch2.abc', 'skins/props/torch_metal.dtx'): 'torchmetalorange',
    ('models/krohn.abc', 'skins/krohnsculpt.dtx;skins/krohnspearsculpt.dtx;skins/krohnswordsculpt.dtx'): 'krohnstatue',
    ('models/skraelos.abc', 'skins/skraelossculpt.dtx'): 'skraelosstatue',
    ('models/njam.abc', 'skins/njamsculpt.dtx'): 'njamstatue',
    ('models/fre.abc', 'skins/fresculpt.dtx'): 'frestatue',
    ('models/wyrd_old.abc', 'skins/wyrdoldsculpt.dtx'): 'wyrdoldstatue',
    ('models/wyrd_mature.abc', 'skins/wyrdmaturesculpt.dtx'): 'wyrdmaturestatue',
    ('models/wyrd_young.abc', 'skins/wyrdyoungsculpt.dtx'): 'wyrdyoungstatue',
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/bench_stone02.abc', 'skins/props/bench_stone.dtx'): 'benchstone02',
    ('models/props/throne.abc', 'skins/props/throne.dtx'): 'throne',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/dragonpharoah.abc', 'skins/props/dragonpharoahstatue.dtx'): 'dragonpharoah',
}
# DAT model/skin pairs MM9 does not ship, shown with a shipped pair (the object keeps its DAT names in props.json).
ALIASES = {('models/dragonpharoah.abc', 'skins/dragonpharoah.dtx'):
           ('models/props/dragonpharoah.abc', 'skins/props/dragonpharoahstatue.dtx')}
REUSED = {prop: PROPS_DIR / owner for prop, owner in {
    'benchstone02': 'mm9_templeofhonk_claude', 'throne': 'mm9_lichlab_claude', 'scroll': 'mm9_anskramkeep_claude',
    'dragonpharoah': 'mm9_1000terrors_claude'}.items()}
STATUES = {'krohnstatue', 'skraelosstatue', 'njamstatue', 'frestatue', 'wyrdoldstatue', 'wyrdmaturestatue',
           'wyrdyoungstatue'}
SOURCES = {}
TILTS = {}
# Posed models: (animation, frame) set in build (blib.import_raw) and placements (posed_points). PropAnim.scr "statue"
# loops the `statue` animation (two keys, 0 and 1 ms: one pose); the first animation (krsetup, static, Njam, Fre,
# wyrds_*: what the old map baked) is a T-pose.
POSES = {name: ('statue', 0) for name in STATUES}
# Reused models placed by an animation pose of their ABC (no bake to check against): the 1000 Terrors built
# DragonPharoah with its Static_Model root (its BUILT_TURN), so its placed points are that pose's.
PLACE_POSES = {'dragonpharoah': ('Static_Model', 0)}
# Models whose first animation's root is turned from the bind pose the old map baked: TORCH2's static_object root is a
# quarter round from its bind root, and the built model (Blender's import evaluates the first animation) has MM9's
# static_object facing, its back plate on the wall (work/wall_probe.py); the old bake lies along the wall. They are
# placed as the others (bake-centred) and also checked against that pose's own points (fit_pose_units).
CHECK_POSES = {'torchmetalorange': ('static_object', 0)}
POSE_TURN = {}
# Skin k binds ABC material k. Krohn's DAT lists Krohnsculpt;KrohnSpearsculpt;KROHNSwordsculpt, but material 1 is the
# sword piece and material 2 the spear (MM9's own Krohn monster row: Krohn.dtx, KrohnSword.dtx, KrohnSpear.dtx). The
# spear sculpt's layout fits the sword's UVs worse (0.91 of the sword's UV samples land on drawn texels against 1.00
# for the sword sculpt; the spear 0.99 on its own layout against 0.84 on the sword's), so each weapon takes its own
# sculpt skin: DAT skins in the order 0, 2, 1.
SKIN_ORDER = {'krohnstatue': [0, 2, 1]}
CLASSES = {'Prop', 'Brazier', 'WallTorch'}
# Objects of those classes (and the other model-carrying objects of the DAT) that get no decoration: name -> reason.
SKIPPED = {
    'DragonPharoah': 'models\\DragonPharoah.abc and skins\\DragonPharoah.dtx are not in MM9 (MODELS.REZ, SKINS.REZ); '
                     'the props DragonPharoah stand-in would stand inside Krohn\'s statue (README)',
    'DragonThrone': 'models\\props\\DragonThrone.abc is not in MM9 (MODELS.REZ)',
    'DragonAzure0': 'models\\DragonAzure.abc is not in MM9 (MODELS.REZ): nothing to build or pose',
    'DragonAzure1': 'models\\DragonAzure.abc is not in MM9 (MODELS.REZ): nothing to build or pose',
}


def key(path):
    return ';'.join(part.replace('\\', '/').lower().strip() for part in (path or '').split(';'))


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def tilt_degrees(p):
    r = p.get('Rotation') or [0, 0, 0]
    return int(round(math.degrees(float(r[0])))) % 360, int(round(math.degrees(float(r[2])))) % 360


def object_prop(o):
    p = o['props']
    pair = (key(p['Filename']), key(p.get('Skin')))
    prop = MODELS[ALIASES.get(pair, pair)]
    pitch, roll = tilt_degrees(p)
    if (pitch, roll) != (0, 0):
        raise SystemExit(f"{p['Name']}: {prop} tilted pitch {pitch} roll {roll} has no variant")
    script = (p.get('ScriptName') or '').lower()
    if 'propanim' in script and (p.get('ScriptParams') or '').strip().lower() != 'statue':
        raise SystemExit(f"{p['Name']}: {prop} PropAnim {p.get('ScriptParams')} has no posed variant")
    return prop


def placements():
    """(object index, prop id) of every decoration object (not the SKIPPED ones)."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')
            and o['props'].get('Name') not in SKIPPED]


def source_prop(prop):
    return SOURCES.get(prop, prop)


def built_props():
    """The props built here: the placed ones minus the reused."""
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
    roots = {'models': 'MODELS/MODELS', 'skins': 'SKINS/SKINS', 'textures': 'TEXTURES/TEXTURES',
             'spritetextures': 'SPRITETEXTURES/SPRITETEXTURES'}

    def path(s):
        top, rest = s.split('/', 1)
        return EXTRACTED / roots[top] / rest
    skins = skins.split(';')
    skins = [skins[k] for k in SKIN_ORDER.get(source_prop(prop), range(len(skins)))]
    return path(model), [path(s) for s in skins]


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
    # every model-carrying object of the DAT: placed, or skipped with its reason; the DAT models MM9 does not ship
    missing = []
    for o in out:
        f = o['props'].get('Filename')
        if not f or not isinstance(f, str) or not f.lower().endswith('.abc'):
            continue
        parts = key(f).split('/')
        try:
            resolve(EXTRACTED / 'MODELS/MODELS' / '/'.join(parts[1:]))
        except FileNotFoundError:
            missing.append(f"{o['index']} {o['class']} {o['props'].get('Name')}: {f} not in mm9/extracted (MODELS.REZ)")
        if o['class'] not in CLASSES and o['props'].get('Name') not in SKIPPED:
            print('NOT A DECORATION CLASS (not placed):', o['index'], o['class'], o['props'].get('Name'), f)
    (HERE / 'work/missing_models.txt').write_text('\n'.join(missing) + '\n')
    print('DAT models not shipped:', *missing, sep='\n  ')
    print('skipped:', SKIPPED)


if __name__ == '__main__':
    main()

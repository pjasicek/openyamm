"""Dungeon of Secrets' prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
and the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9 props
project are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they are); the
rest are built here (Dark Passageway's scripts, Yanmir's Fort's route: one material per MM9 skin, the isle's blib build
and finish checks, the Anskram flame cards in `card` mode).

The map has three kinds of prop: 34 upright claw torches (Prop, ClawTorch, Scale 1: Dark Passageway's `clawtorch`),
one hanging claw lamp (Prop46: ClawLamp.ABC with pitch pi, Yanmir's Fort's `clawlampp180`; MM9 skins it with
ClawTorch.dtx, the same layout as ClawLamp.dtx: the lamp's UVs never reach the torch skin's wood patch) and 20 wall
sconces (class Torch, SCONCE2 / Sconce2.dtx, Scale 1.5, Fire 1 with orange FireColor: built here as `sconce2`, the
orange counterpart of Chasm of the Dead's blue `bluesconce`).

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
PROJECT = REPO / 'level_generation/projects/mm9r_dungeonofsecrets'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/dungeonofsecrets.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/dungeonofsecrets.odm'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id
# (the upright source; a tilted variant names it in SOURCES).
MODELS = {
    # built here: the 20 Torch-class wall sconces (orange fire)
    ('models/props/sconce2.abc', 'skins/props/sconce2.dtx'): 'sconce2',
    # reused: built by other MM9 props projects (same ABC model; the lamp's skin below)
    ('models/props/clawtorch.abc', 'skins/props/clawtorch.dtx'): 'clawtorch',
    # MM9 skins this lamp with ClawTorch.dtx; Yanmir's Fort's lamp has ClawLamp.dtx (same layout, README)
    ('models/props/clawlamp.abc', 'skins/props/clawtorch.dtx'): 'clawlamp',
}
REUSED = {prop: PROPS_DIR / owner for prop, owner in {
    'clawtorch': 'mm9_darkpassageway_claude', 'clawlampp180': 'mm9_yanmirsfort_claude'}.items()}
STATUES = set()
# Prop46 hangs with pitch pi (claw above, orb below): Yanmir's Fort's variant with the pitch baked in.
SOURCES = {'clawlampp180': 'clawlamp'}
TILTS = {'clawlampp180': (math.pi, 0.0)}
TILT_OF = {('clawlamp', 180, 0): 'clawlampp180'}
ONSIDE = {}
POSES = {}
POSE_TURN = {}
CLASSES = {'Prop', 'Torch'}


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

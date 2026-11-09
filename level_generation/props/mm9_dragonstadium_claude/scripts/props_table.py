"""Dragon Stadium's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them, and
the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9 props project
are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they are); the rest
are built here (the Drangheim Prison / Lich Lab route: one material per MM9 skin, tilts baked in).

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
KLUSOS = PROPS_DIR / 'mm9_klusoshouse_claude'
CHASM = PROPS_DIR / 'mm9_chasmofthedead_claude'
VERHOFFIN = PROPS_DIR / 'mm9_verhoffinruins_claude'
PROJECT = REPO / 'level_generation/projects/mm9r_dragonstadium'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/dragonstadium.raw_objects.yml'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
# Both of the stadium's props are reused (same ABC model and skin as an installed decoration): nothing is built here.
MODELS = {
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
    ('models/props/skeletonlaying.abc', 'skins/props/skeleton.dtx'): 'skeletonlayingprop',
}
CONNECTING = PROPS_DIR / 'mm9_connectingtunnels_claude'
REUSED = {'blackchest': LICHLAB, 'skeletonlayingprop': CONNECTING}
TILTED = {}
OBJECT_PROP = {}
TILTS = {}
BOOK_PROPS = {}
CLASSES = {'Prop', 'Barrel', 'TreasureChest', 'BonePile', 'CandleProp'}
OWNERS = {}


def key(path):
    return ';'.join(part.replace('\\', '/').lower().strip() for part in (path or '').split(';'))


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def _tilts():
    path = HERE / 'work/raw_objects_compact.json'
    if not path.exists():
        return
    by_name = {o['props'].get('Name'): o['props'] for o in json.loads(path.read_text())}
    for variant, (_, names) in TILTED.items():
        rotations = {(by_name[n]['Rotation'][0], by_name[n]['Rotation'][2]) for n in names}
        if len(rotations) != 1:
            raise SystemExit(f'{variant}: its objects differ in pitch/roll {rotations}')
        TILTS[variant] = rotations.pop()


_tilts()


def object_prop(o):
    p = o['props']
    if p.get('Name') in OBJECT_PROP:
        return OBJECT_PROP[p['Name']]
    return MODELS[(key(p['Filename']), key(p.get('Skin')))]


EXTRA_PLACEMENTS = []


def placements():
    """(object index, prop id) of every decoration object, then the extra placements."""
    out = [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')]
    for name, prop, _ in EXTRA_PLACEMENTS:
        out.append((next(o['index'] for o in objects() if o['props'].get('Name') == name), prop))
    return out


def anchor(index, prop, name):
    """The props.json anchor of a placement: the DAT name, or an extra placement's own anchor."""
    return next((a for n, p, a in EXTRA_PLACEMENTS if n == name and p == prop), name)


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

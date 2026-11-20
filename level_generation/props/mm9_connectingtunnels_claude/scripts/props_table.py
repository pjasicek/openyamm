"""Connecting Tunnels' prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them, and
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
PROJECT = REPO / 'level_generation/projects/mm9r_connectingtunnels'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/connectingtunnels.raw_objects.yml'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/chest3.abc', 'skins/props/chest3.dtx'): 'chest3',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
    ('models/props/candle.abc', 'skins/props/candle.dtx'): 'candle',
    ('models/props/debris/lumberstonedebris03.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'lumberstone03',
    ('models/props/debris/stonedebris02.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'stonedebris02',
    ('models/props/sack03.abc', 'skins/props/sack01.dtx'): 'sack03',
    # built here (another skin than the installed model of the same ABC, or not installed yet)
    ('models/props/minelantern02.abc', 'skins/props/minelantern.dtx'): 'minelantern02plain',
    ('models/props/skeletonlaying.abc', 'skins/props/skeleton.dtx'): 'skeletonlayingprop',
    ('models/props/debris/stonedebris01.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'stonedebris01ls',
    ('models/props/debris/stonedebris04.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'stonedebris04ls',
    ('models/props/debris/stonedebris05.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'stonedebris05ls',
    ('models/props/sack01.abc', 'skins/props/sack01.dtx'): 'sack01',
    ('models/props/sack02.abc', 'skins/props/sack01.dtx'): 'sack02',
}
TASAR = PROPS_DIR / 'mm9_tasaracademy_claude'
DRANGHEIM = PROPS_DIR / 'mm9_drangheimprison_claude'
REUSED = {'barrel03': ANSKRAM, 'barrel': ANSKRAM, 'crate': ANSKRAM, 'chest3': TEMPLE, 'blackchest': LICHLAB,
          'candle': TASAR, 'lumberstone03': DRANGHEIM, 'stonedebris02': ISLE, 'sack03': DRANGHEIM}
# The tunnels' props on slopes (the ramp's debris, the crates, a barrel and a sack on a sloping floor): MM9 pitches or
# rolls them by a few degrees, which a decoration cannot do (yaw only), so each tilt is its own model with the DAT's
# pitch and roll baked in (Dook's Castle's TILTS route); the old bake fits them to 0.5 units instead of 6-8.
# variant -> (source prop of MODELS, DAT objects); TILTS: variant -> (pitch, roll) radians (the DAT Rotation x and z).
TILTED = {
    'stonedebris04lsp7': ('stonedebris04ls', ['Prop3']),
    'stonedebris04lsp350': ('stonedebris04ls', ['Prop6']),
    'lumberstone03p10': ('lumberstone03', ['Prop4']),
    'stonedebris01lsp350': ('stonedebris01ls', ['Prop5']),
    'stonedebris05lsp350': ('stonedebris05ls', ['Prop7']),
    'stonedebris02p350': ('stonedebris02', ['Prop8']),
    'cratep356': ('crate', ['Prop9', 'Prop10', 'Prop12']),
    'crater355': ('crate', ['Prop14']),
    'barrelp356': ('barrel', ['Prop13']),
    'sack01p350r356': ('sack01', ['Prop17']),
}
OBJECT_PROP = {name: variant for variant, (_, names) in TILTED.items() for name in names}
TILTS = {}          # filled from the DAT in _tilts() (the objects of one variant share their rotation exactly)
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

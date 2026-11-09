"""Dook's Castle's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them, and
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
PROJECT = REPO / 'level_generation/projects/mm9r_dookscastle'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/dookscastle.raw_objects.yml'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/brazier.abc', 'skins/props/brazier.dtx'): 'brazier',
    ('models/props/hangingbrazierbowl.abc', 'skins/props/hangingbrazierbowl3.dtx'): 'hangingbowl',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/box-ornamental.abc', 'skins/props/box-ornamental.dtx'): 'boxornamental',
    ('models/props/cabinet02.abc', 'skins/props/cabinet02.dtx'): 'cabinet02',
    ('models/props/cabinet05.abc', 'skins/props/cabinet05.dtx'): 'cabinet05',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair_fordesk01.abc', 'skins/props/chair_fordesk01.dtx'): 'chairdesk01',
    ('models/props/desk01.abc', 'skins/props/desk01.dtx'): 'desk01',
    ('models/props/dresserns.abc', 'skins/props/dresserfancy.dtx'): 'dresserfancyns',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/shield.abc', 'skins/props/shield3.dtx'): 'shield3',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/throne.abc', 'skins/props/throne.dtx'): 'throne',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet04.dtx'): 'weaponscabinet04',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
    ('models/props/chest1.abc', 'skins/props/chest2.dtx'): 'chest',
    ('models/props/sconce1.abc', 'skins/props/sconce1.dtx'): 'sconce1',
    # built here
    ('models/props/bed_ornate.abc', 'skins/props/bed_ornate.dtx'): 'bedornate',
    ('models/props/cards.abc', 'skins/props/cards.dtx'): 'cards',
    ('models/props/suitofarmor02.abc', 'skins/props/amoredsuitgold.dtx;skins/props/amoredsuithalberd.dtx'):
        'suitofarmor02',
    ('models/props/shield.abc', 'skins/props/shield.dtx'): 'shield1',
    ('models/props/shield.abc', 'skins/props/shield2.dtx'): 'shield2',
    ('models/props/shield.abc', 'skins/props/shield4.dtx'): 'shield4',
    ('models/props/weaponrackns.abc', 'skins/props/weaponrack_new.dtx'): 'weaponracknew',
    ('models/props/tapestry-old01.abc', 'textures/leveltextures/misc/banner4.dtx'): 'tapestry_banner4',
}
REUSED = {'barrel03': ANSKRAM, 'brazier': TEMPLE, 'hangingbowl': TEMPLE, 'bedmedium': ANSKRAM,
          'bookcase02ew': ANSKRAM, 'boxornamental': CHASM, 'cabinet02': KLUSOS, 'cabinet05': KLUSOS, 'chair': ANSKRAM,
          'chairdesk01': TEMPLE, 'desk01': ANSKRAM, 'dresserfancyns': KLUSOS, 'scroll': ANSKRAM, 'shield3': KLUSOS,
          'tableround': ANSKRAM, 'throne': LICHLAB, 'weaponscabinet04': ANSKRAM, 'blackchest': LICHLAB, 'chest': ANSKRAM,
          'sconce1': VERHOFFIN}
# The shields hang on the walls (LithTech pitch 1.571; decorations turn about z only): the tilt is baked in. MM9 gives
# the two on the north wall roll 0 and the two on the south wall roll pi; through the transcoder's tilt (pitch, then
# roll) roll 0 hangs a heater shield point up (Klusos House's shield3, review v04 l09), which a shield on a wall is not:
# all four are baked with roll pi, point down (the models are double-sided, so the facing does not matter).
# Sheild2 (shield3 skin) is a variant of Klusos House's shield3.
OBJECT_PROP = {'Sheild2': 'shield3r'}
TILTED = {'shield3r': ('shield3', (1.5707964, 3.1415927))}
TILTS = {'shield1': (1.5707964, 3.1415927), 'shield2': (1.5707964, 3.1415927), 'shield4': (1.5707964, 3.1415927),
         'shield3r': (1.5707964, 3.1415927)}
BOOK_PROPS = {}
CLASSES = {'Prop', 'Barrel', 'TreasureChest', 'Brazier', 'WallTorch'}
OWNERS = {'shield3r': KLUSOS}       # a tilted variant converts its owner's source model (MODELS key) itself


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

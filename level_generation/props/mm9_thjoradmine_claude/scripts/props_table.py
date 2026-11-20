"""Thjorad Mine's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them, and
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
PROJECT = REPO / 'level_generation/projects/mm9r_thjoradmine'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/thjoradmine.raw_objects.yml'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/trashpile.abc', 'skins/props/trashpile.dtx'): 'trashpile',
    ('models/props/anvil.abc', 'skins/props/anvil.dtx'): 'anvil',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/bench01.abc', 'skins/props/bench01.dtx'): 'bench01',
    ('models/props/bucket01.abc', 'skins/props/bucket01.dtx'): 'bucket01',
    ('models/props/chair_fordesk03.abc', 'skins/props/chair_fordesk03.dtx'): 'chairdesk03',
    ('models/props/coalbin.abc', 'skins/props/coalbin.dtx'): 'coalbin',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/table_bench.abc', 'skins/props/table_bench.dtx'): 'tablebench2',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet01.dtx'): 'weaponscabinet01',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    # built here
    ('models/props/oillamp.abc', 'skins/props/oillamp.dtx'): 'oillamp',
    ('models/props/minecart.abc', 'skins/props/minecart.dtx;skins/props/thjorad.dtx'): 'minecart',
    ('models/props/stool01.abc', 'skins/props/stool01.dtx'): 'stool01',
    ('models/pickupitems/quest/machine-part_broken.abc', 'skins/pickupitems/quest/machinepart_broken.dtx'):
        'machinepartbroken',
    # not placed in the DAT: SlagExtractor.scr's OnShow swaps the slag prop to it (SetModelFilenames) when the party
    # installs the replacement; the map places it hidden at slag's position (props.json anchor slag_whole)
    ('models/pickupitems/quest/machine-part_whole.abc', 'skins/pickupitems/quest/machinepart_whole.dtx'):
        'machinepartwhole',
    ('models/props/boiler.abc', 'skins/props/boiler.dtx'): 'boiler',
    ('models/props/box02.abc', 'skins/props/pantry-items02.dtx'): 'box02pantry',
    ('models/props/bucket02.abc', 'skins/props/bucket02.dtx'): 'bucket02',
    ('models/props/debris/stonedebris05.abc', 'skins/props/thjorad.dtx'): 'stonedebris05thjorad',
    ('models/props/minelantern02.abc', 'skins/props/minelantern-bright.dtx'): 'minelantern02',
    ('models/props/tableround.abc', 'skins/props/tableroundplain.dtx'): 'tableroundplain',
    ('models/props/thjorad-bin.abc', 'skins/props/thjorad-bin.dtx;skins/props/thjorad.dtx'): 'thjoradbin',
    ('models/props/woodbin.abc', 'skins/props/woodbin.dtx'): 'woodbin',
    # posed variants of other projects (PropAnim.scr "onside": the ABC's onside pose baked in by their owners)
    ('models/modelprops/dwarfaxe.abc', 'skins/modelprops/dwarfaxe.dtx'): 'dwarfaxeonside',
    ('models/props/bedmedium2.abc', 'skins/props/bedmedium2.dtx'): 'bedmedium2onside',
}
TASAR = PROPS_DIR / 'mm9_tasaracademy_claude'
DRANGHEIM = PROPS_DIR / 'mm9_drangheimprison_claude'
REUSED = {'barrel03': ANSKRAM, 'barrel': ANSKRAM, 'crate': ANSKRAM, 'trashpile': ANSKRAM, 'anvil': DRANGHEIM,
          'bedmedium': ANSKRAM, 'bench01': DRANGHEIM, 'bucket01': DRANGHEIM, 'chairdesk03': TEMPLE,
          'coalbin': DRANGHEIM, 'scroll': ANSKRAM, 'tablebench2': DRANGHEIM, 'weaponscabinet01': ANSKRAM,
          'chest1': ANSKRAM, 'dwarfaxeonside': TASAR, 'bedmedium2onside': VERHOFFIN}
OBJECT_PROP = {}
TILTED = {}
TILTS = {}
BOOK_PROPS = {}
CLASSES = {'Prop', 'Barrel', 'TreasureChest', 'DestructableProp', 'BonePile', 'CandleProp'}
OWNERS = {}


def key(path):
    return ';'.join(part.replace('\\', '/').lower().strip() for part in (path or '').split(';'))


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def object_prop(o):
    p = o['props']
    if p.get('Name') in OBJECT_PROP:
        return OBJECT_PROP[p['Name']]
    return MODELS[(key(p['Filename']), key(p.get('Skin')))]


# Extra placements of a model at another object's place: (object name, prop, anchor). The whole slag extractor
# stands where the broken one is (SlagExtractor.scr OnShow), hidden until the quest is done (the map script).
EXTRA_PLACEMENTS = [('slag', 'machinepartwhole', 'slag_whole')]


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

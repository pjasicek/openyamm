"""Drangheim Prison's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them, and the ABC
placement binding origins. Props whose model and skin match an installed isle or Anskram Keep decoration are reused
(REUSED: their decoration rows, bindings and GLBs stay where they are); the rest are built here.

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
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/drangheimprison.raw_objects.yml'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by the Anskram, Temple of Honk or Lich Lab projects
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/bed.abc', 'skins/props/bed.dtx'): 'bed',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair_fordesk01.abc', 'skins/props/chair_fordesk01.dtx'): 'chairdesk01',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    ('models/props/desk01ns.abc', 'skins/props/desk01.dtx'): 'desk01ns',
    ('models/props/hangingbrazierbowl2.abc', 'skins/props/hangingbrazierbowl3.dtx'): 'hangingbowl2',
    ('models/props/table01.abc', 'skins/props/table01.dtx'): 'table01',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/trashpile.abc', 'skins/props/trashpile.dtx'): 'trashpile',
    ('models/props/walltorch.abc', 'skins/props/walltorch.dtx'): 'walltorch',
    ('models/props/weaponrack.abc', 'skins/props/weaponrack_used.dtx'): 'weaponrack',
    ('models/props/bed_cot.abc', 'skins/props/bed_cot.dtx'): 'cot',
    # built here
    ('models/props/anvil.abc', 'skins/props/anvil.dtx'): 'anvil',
    ('models/props/axe-rusty.abc', 'skins/props/axe-rusty.dtx'): 'axerusty',
    ('models/props/bed_wall.abc', 'skins/props/bed_wall.dtx'): 'bedwall',
    ('models/props/bedmedium2.abc', 'skins/props/bedmedium2.dtx'): 'bedmedium2',
    ('models/props/bench01.abc', 'skins/props/bench01.dtx'): 'bench01',
    ('models/props/bonepile.abc', 'skins/props/bonepile.dtx'): 'bonepile',
    ('models/props/bucket01.abc', 'skins/props/bucket01.dtx'): 'bucket01',
    ('models/props/cabinet04ns.abc', 'skins/props/cabinet04.dtx'): 'cabinet04ns',
    ('models/props/cabinet05ns.abc', 'skins/props/cabinet05.dtx'): 'cabinet05ns',
    ('models/props/canvassack.abc', 'skins/props/canvassack.dtx'): 'canvassack',
    ('models/props/chair_fordesk02.abc', 'skins/props/chair_fordesk02.dtx'): 'chairdesk02',
    ('models/props/coalbin.abc', 'skins/props/coalbin.dtx'): 'coalbin',
    ('models/props/debris/lumberstonedebris02.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'lumberstone02',
    ('models/props/debris/lumberstonedebris03.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'lumberstone03',
    ('models/props/debris/skeletondebris01.abc', 'skins/props/debris/skeletondebris.dtx'): 'skeletondebris01',
    ('models/props/debris/skeletondebris02.abc', 'skins/props/debris/skeletondebris.dtx'): 'skeletondebris02',
    ('models/props/iron-ingots.abc', 'skins/props/iron-ingots.dtx'): 'ironingots',
    ('models/props/ropecoil.abc', 'skins/props/ropecoil.dtx'): 'ropecoil',
    ('models/props/sack03.abc', 'skins/props/sack01.dtx'): 'sack03',
    ('models/props/shelfitem06.abc', 'skins/props/shelfitem06.dtx'): 'shelfitem06',
    ('models/props/shelfitem07.abc', 'skins/props/shelfitem07.dtx'): 'shelfitem07',
    ('models/props/shelfitem08.abc', 'skins/props/shelfitem08.dtx'): 'shelfitem08',
    ('models/props/shield-broken02.abc', 'skins/props/shield-broken02.dtx'): 'shieldbroken02',
    ('models/props/stove.abc', 'skins/props/stove.dtx'): 'stove',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitaged.dtx'): 'suitofarmor01',
    ('models/props/sword-broken.abc', 'skins/props/sword-broken.dtx'): 'swordbroken',
    ('models/props/table_bench.abc', 'skins/props/table_bench.dtx'): 'tablebench2',
    ('models/props/tableround2.abc', 'skins/props/tableround2.dtx'): 'tableround2',
    ('models/props/tableround3.abc', 'skins/props/tableround3.dtx'): 'tableround3',
    ('models/props/tapestry-old01.abc', 'skins/props/tapestry-old01.dtx'): 'tapestryold01',
    ('models/props/tapestry-old02.abc', 'skins/props/tapestry-old02.dtx'): 'tapestryold02',
    ('models/props/weaponrackns.abc', 'skins/props/weaponrack_used.dtx'): 'weaponrackns',
    ('models/props/weaponscabinet02.abc', 'skins/props/weaponscabinet02.dtx'): 'weaponscabinet02',
}
# Installed decorations reused by model (decoration GLB name -> the project that owns it).
REUSED = {'barrel': 'anskram', 'barrel03': 'anskram', 'bed': 'anskram', 'blackchest': 'lichlab', 'chair': 'anskram',
          'chairdesk01': 'templeofhonk', 'chest1': 'anskram', 'cot': 'isle', 'desk01ns': 'templeofhonk',
          'hangingbowl2': 'templeofhonk', 'table01': 'lichlab', 'tableround': 'templeofhonk', 'trashpile': 'anskram',
          'walltorch': 'templeofhonk', 'weaponrack': 'anskram'}
TEMPLE = REPO / 'level_generation/props/mm9_templeofhonk_claude'
LICHLAB = REPO / 'level_generation/props/mm9_lichlab_claude'
# Placements MM9 tips over (decorations turn about z only): a model with the object's pitch or roll baked in.
OBJECT_PROP = {'Barrel15': 'barrellying', 'Barrel16': 'barrellying', 'Cot4': 'bedmedium2r90', 'Cot5': 'bedmedium2r270'}
TILTED = {'barrellying': ('barrel', (1.5707964, 0.0)), 'bedmedium2r90': ('bedmedium2', (0.0, 1.5707964)),
          'bedmedium2r270': ('bedmedium2', (0.0, 4.712389))}
BOOK_PROPS = {}
CLASSES = {'Prop', 'Barrel', 'BonePile', 'TreasureChest', 'Brazier', 'DestructableProp'}


def key(path):
    return (path or '').replace('\\', '/').lower().strip()


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def object_prop(o):
    p = o['props']
    if p.get('Name') in OBJECT_PROP:
        return OBJECT_PROP[p['Name']]
    prop = MODELS[(key(p['Filename']), key(p.get('Skin')))]
    return prop


def placements():
    """(object index, prop id) of every decoration object."""
    out = []
    for o in objects():
        p = o['props']
        if o['class'] in CLASSES and p.get('Filename'):
            out.append((o['index'], object_prop(o)))
    return out


def built_props():
    """The props built in this project (not reused)."""
    return sorted((set(MODELS.values()) | set(TILTED)) - set(REUSED))


def source_prop(prop):
    """The MODELS id whose source a built prop converts (the tipped variants share their upright model's)."""
    return TILTED[prop][0] if prop in TILTED else prop


def source(prop):
    """(model path, [skin paths]) under mm9/extracted for a prop id."""
    model, skins = next(k for k, v in MODELS.items() if v == source_prop(prop))
    return (REPO / 'mm9/extracted/MODELS/MODELS' / model[len('models/'):],
            [REPO / 'mm9/extracted/SKINS/SKINS' / s[len('skins/'):] for s in skins.split(';')])


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
    print(len(counts), 'props,', sum(counts.values()), 'placements')
    print('built:', [(p, counts[p]) for p in built_props()])
    print('reused:', [(p, counts[p]) for p in sorted(REUSED)])


if __name__ == '__main__':
    main()

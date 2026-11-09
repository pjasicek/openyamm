"""Inventa Storca's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them, and the ABC
placement binding origins. Props whose model and skin match an installed MM9 decoration are reused (REUSED: their
decoration rows, bindings and GLBs stay where they are, with their owning project's build records); the rest are built
here: the Orb of Linking, the bench and the treasure bag.

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
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/inventastorca.raw_objects.yml'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by other MM9 props projects (REUSED names the project that holds the build records)
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/bonepile.abc', 'skins/props/bonepile.dtx'): 'bonepile',
    ('models/props/hangingbrazierbowl2.abc', 'skins/props/hangingbrazierbowl3.dtx'): 'hangingbowl2',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/table_bench.abc', 'skins/props/table_bench.dtx'): 'tablebench2',
    ('models/props/bench04.abc', 'skins/props/bench04.dtx'): 'bench04',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/walltorch.abc', 'skins/props/walltorch.dtx'): 'walltorch',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
    ('models/props/chest1.abc', 'skins/props/chest2.dtx'): 'chest',
    # built here
    ('models/pickupitems/quest/orb_linking.abc', 'skins/pickupitems/quest/orb_linking.dtx'): 'orblinking',
    ('models/props/bench03.abc', 'skins/props/bench03.dtx'): 'bench03',
    ('models/pickupitems/treasurebag.abc', 'skins/pickupitems/bag1.dtx'): 'treasurebag',
}
OWNERS = {name: REPO / f'level_generation/props/mm9_{name}_claude' for name in
          ('anskramkeep', 'templeofhonk', 'lichlab', 'beethoven', 'drangheimprison', 'chasmofthedead', 'isleofashes')}
# Installed decorations reused by model (decoration GLB name -> the props project holding its build records).
REUSED = {'barrel03': 'anskramkeep', 'bonepile': 'beethoven', 'hangingbowl2': 'templeofhonk', 'chair': 'anskramkeep',
          'tableround': 'anskramkeep', 'tablebench2': 'drangheimprison', 'bench04': 'templeofhonk',
          'scroll': 'anskramkeep', 'walltorch': 'anskramkeep', 'blackchest': 'lichlab', 'chest': 'anskramkeep'}
TEMPLE = OWNERS['templeofhonk']
LICHLAB = OWNERS['lichlab']
OBJECT_PROP = {}
TILTED = {}
BOOK_PROPS = {}
CLASSES = {'Prop', 'Barrel', 'BonePile', 'TreasureChest', 'TreasureBag', 'Brazier', 'WallTorch'}


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

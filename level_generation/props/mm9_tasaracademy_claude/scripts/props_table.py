"""The Tasar Academy's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
the ABC placement binding origins, and which props reuse a decoration another project built (same ABC model, skin and
placement scale; its GLB, row and binding stay where they are). The module keeps the names the Anskram Keep scripts
read (HERE, REPO, ISLE, MODELS, source, resolve, ...), so they run on this table from sys.modules['props_table'].
The route is the Verhoffin Ruins props project's (../mm9_verhoffinruins_claude/).

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
PROJECT = REPO / 'level_generation/projects/mm9r_tasaracademy'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/tasaracademy.raw_objects.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin file) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/props/candle.abc', 'skins/props/candle.dtx'): 'candle',
    ('models/props/chandelier.abc', 'skins/props/chandelier.dtx'): 'chandelier',
    ('models/props/scroll1.abc', 'skins/props/scroll1.dtx'): 'scroll1',
    ('models/pickupitems/scroll.abc', 'skins/props/scrolldouble.dtx'): 'scrollpickup',
    ('models/props/smithhammer.abc', 'skins/props/smithhammer.dtx'): 'smithhammer',
    ('models/props/pew.abc', 'skins/props/pew.dtx'): 'pew',
    ('models/props/weaponrack.abc', 'skins/props/weaponrack_new.dtx'): 'weaponrack_new',
    ('models/modelprops/dwarfaxe.abc', 'skins/modelprops/dwarfaxe.dtx'): 'dwarfaxe',
    ('models/props/forge.abc', 'skins/props/forge.dtx'): 'forge',
    ('models/props/grindingwheel.abc', 'skins/props/grindingwheel.dtx'): 'grindingwheel',
    ('models/props/goblet_fancy02.abc', 'skins/props/goblet_fancy02.dtx'): 'gobletfancy02',
    ('models/pickupitems/quest/book-rules.abc', 'skins/pickupitems/quest/bookrules.dtx'): 'bookrules',
    ('models/props/bag-herbs1.abc', 'skins/pickupitems/quest/bagherbs1.dtx'): 'bagherbs1',
    # reused: built by another MM9 props project (same ABC model and skin)
    ('models/props/brazier.abc', 'skins/props/brazier.dtx'): 'brazier',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/dresserns.abc', 'skins/props/dresserplain.dtx'): 'dresserns',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',
    ('models/props/chair_fordesk03.abc', 'skins/props/chair_fordesk03.dtx'): 'chairdesk03',
    ('models/props/desk03.abc', 'skins/props/desk03.dtx'): 'desk03',
    ('models/props/table_bench.abc', 'skins/props/table_bench.dtx'): 'tablebench2',
    ('models/props/table01.abc', 'skins/props/table01.dtx'): 'table01',
    ('models/props/pillarstand.abc', 'skins/props/pillarstand.dtx'): 'pillarstand',
    ('models/props/suitofarmor02.abc', 'skins/props/amoredsuitgold.dtx;skins/props/amoredsuithalberd.dtx'):
        'suitofarmor02',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/bookcase02ns.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ns',
    ('models/props/table01ns.abc', 'skins/props/table01.dtx'): 'table01ns',
    ('models/props/bookstack01.abc', 'skins/props/bookstack01.dtx'): 'bookstack01',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shelfitem05.abc', 'skins/props/shelfitem05.dtx'): 'shelfitem05',
    ('models/props/bucket01.abc', 'skins/props/bucket01.dtx'): 'bucket01',
    ('models/props/podium03.abc', 'skins/props/podium03.dtx'): 'podium',
    ('models/props/podium01.abc', 'skins/props/podium01.dtx'): 'podium01',
    ('models/props/chest3.abc', 'skins/props/chest3.dtx'): 'chest3',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    ('models/props/anvil.abc', 'skins/props/anvil.dtx'): 'anvil',
    ('models/props/iron-ingots.abc', 'skins/props/iron-ingots.dtx'): 'ironingots',
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/ropecoil.abc', 'skins/props/ropecoil.dtx'): 'ropecoil',
    ('models/props/jar01.abc', 'skins/props/pantry-items.dtx'): 'jar01',
    ('models/props/jar02.abc', 'skins/props/pantry-items.dtx'): 'jar02',
    ('models/props/jar03.abc', 'skins/props/pantry-items.dtx'): 'jar03',
    ('models/props/jar04.abc', 'skins/props/pantry-items02.dtx'): 'jar04',
    ('models/props/jar05.abc', 'skins/props/pantry-items02.dtx'): 'jar05',
    ('models/props/jar06.abc', 'skins/props/pantry-items02.dtx'): 'jar06',
    ('models/props/goblet_fancy01.abc', 'skins/props/goblet_fancy01.dtx'): 'goblet',
    ('models/props/spikepit.abc', 'skins/props/spikepit.dtx'): 'spikepit',
    ('models/props/coalbin.abc', 'skins/props/coalbin.dtx'): 'coalbin',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/skeletonstatue.abc', 'skins/props/skeletonstatue.dtx;skins/props/skelstatuebase.dtx'):
        'skeletonstatue',
    # MM9 ships no Skillbook.abc (nor its skin SkillBook_Normal.dtx): the six SkillBook.scr books (Prop5, Prop88-91,
    # Prop94) had no mesh in the old bake either. They stand in as the Temple of Honk's flat book (MM9's book model),
    # lying on the surface under their DAT position, so the map's click events have something to click.
    ('models/pickupitems/skillbook.abc', 'skins/pickupitems/skillbook_normal.dtx'): 'bookflat',
}
PROPS_DIR = REPO / 'level_generation/props'
# Decorations another project built from the same ABC model and skin (prop -> owning project, the one whose finished
# GLB is the installed one: md5-checked against assets_source/engine/models/): their GLBs and rows stay where they are;
# a placement scale they do not have becomes a variant row here (tables.py).
REUSED = {prop: PROPS_DIR / owner for prop, owner in {
    'brazier': 'mm9_templeofhonk_claude', 'bedmedium': 'mm9_anskramkeep_claude', 'dresserns': 'mm9_anskramkeep_claude',
    'bookflat': 'mm9_templeofhonk_claude', 'book': 'mm9_isleofashes_claude', 'chairdesk03': 'mm9_lichlab_claude',
    'desk03': 'mm9_templeofhonk_claude', 'tablebench2': 'mm9_drangheimprison_claude', 'table01': 'mm9_lichlab_claude',
    'pillarstand': 'mm9_chasmofthedead_claude', 'suitofarmor02': 'mm9_dookscastle_claude',
    'bookcase02ew': 'mm9_anskramkeep_claude', 'bookcase02ns': 'mm9_anskramkeep_claude',
    'table01ns': 'mm9_lichlab_claude', 'bookstack01': 'mm9_lichlab_claude', 'shelfitem03': 'mm9_lichlab_claude',
    'shelfitem05': 'mm9_lichlab_claude', 'bucket01': 'mm9_drangheimprison_claude', 'podium': 'mm9_isleofashes_claude',
    'podium01': 'mm9_lichlab_claude', 'chest3': 'mm9_templeofhonk_claude', 'chest1': 'mm9_anskramkeep_claude',
    'anvil': 'mm9_drangheimprison_claude', 'ironingots': 'mm9_drangheimprison_claude',
    'barrel03': 'mm9_anskramkeep_claude', 'ropecoil': 'mm9_drangheimprison_claude',
    'jar01': 'mm9_beethoven_claude', 'jar02': 'mm9_beethoven_claude', 'jar03': 'mm9_beethoven_claude',
    'jar04': 'mm9_beethoven_claude', 'jar05': 'mm9_beethoven_claude', 'jar06': 'mm9_beethoven_claude',
    'goblet': 'mm9_chasmofthedead_claude', 'spikepit': 'mm9_anskramkeep_claude', 'coalbin': 'mm9_drangheimprison_claude',
    'crate': 'mm9_anskramkeep_claude', 'skeletonstatue': 'mm9_lichlab_claude'}.items()}
# Every prop-like DAT class; the PropDamager spikes (Spikes1) are placed here too (Anskram's spikepit), Barrel and
# DestructableProp as plain props.
CLASSES = {'Prop', 'Brazier', 'CandleProp', 'TreasureChest', 'Barrel', 'DestructableProp', 'PropDamager'}
# Tipped over in MM9 (decorations turn about z only): their pitch and roll baked in, a model each (the Chasm's route),
# or an existing variant with the same pose. Prop160 (the letter on the lectern Prop159) has exactly the isle's lectern
# book pose (pitch 2.5062928, roll pi): the isle's mm9_book. BookRules (on the lectern Prop162) lies the same way.
TILTED = {'Prop160': 'book', 'BookRules': 'bookrulestilt',
          # PropAnim.scr "onside" loops the ABC's onside animation (the pickaxes lie on their side): a full export,
          # posed in Blender (Verhoffin's bedmedium2onside route)
          **{f'Pickaxe{k}': 'dwarfaxeonside' for k in (3, 4, 5)}}
SOURCES = {'bookrulestilt': 'bookrules', 'dwarfaxeonside': 'dwarfaxe', 'book': 'bookflat'}
BOOK_TILT = {'bookrulestilt': (2.504547357559204, 3.152064800262451),
             'book': (2.5062928199768066, 3.1415927410125732)}   # the isle's (its meta 'tilt'); built there
BOOK_PROPS = {}
# Props built in an animation's pose (action, frame).
POSES = {'dwarfaxeonside': ('onside', 1)}
PENTAFIRES = []


def key(path):
    return (path or '').replace('\\', '/').lower().strip()


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def object_prop(o):
    p = o['props']
    return TILTED.get(p.get('Name')) or MODELS[(key(p['Filename']), key(p.get('Skin')))]


def placements():
    """(object index, prop id) of every decoration object."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')]


def source_prop(prop):
    return SOURCES.get(prop, prop)


def built_props():
    """Props built here: those placed (only through a tipped or posed variant for the book of rules and the
    pickaxes, whose upright forms MM9 never shows here), minus the reused ones."""
    try:
        placed = {prop for _, prop in placements()}
    except FileNotFoundError:
        placed = set(MODELS.values()) | set(TILTED.values())
    return sorted(placed - set(REUSED))


def home(prop):
    """The props project whose work/ holds the prop's meta, raw and finished GLBs."""
    return REUSED.get(prop, HERE)


def source(prop):
    """(model path, skin path) under mm9/extracted for a prop id."""
    model, skin = next(k for k, v in MODELS.items() if v == source_prop(prop))
    roots = {'models': 'MODELS/MODELS', 'skins': 'SKINS/SKINS', 'textures': 'TEXTURES/TEXTURES'}

    def path(p):
        top, rest = p.split('/', 1)
        return EXTRACTED / roots[top] / rest
    return path(model), path(skin.split(';')[0])


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
    for prop in sorted(set(MODELS.values()) | set(TILTED.values())):
        try:
            model, _ = source(prop)
            info = abc_static_model_placement_info(read_abc(resolve(model)))
        except (FileNotFoundError, StopIteration):
            print('no model file for', prop, '(origin 0)')
            info = None
        origins[prop] = list(info.binding_origin) if info else [0.0, 0.0, 0.0]
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    counts = Counter(prop for _, prop in placements())
    print(len(counts), 'props,', sum(counts.values()), 'placements;',
          Counter(o['class'] for o in out if o['class'] in CLASSES))
    print('built:', [(p, counts[p]) for p in built_props()])
    print('reused:', [(p, counts[p]) for p in sorted(REUSED)])


if __name__ == '__main__':
    main()

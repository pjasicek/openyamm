r"""Drangheim City's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
and the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9 props
project are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they are); the
rest are built here. The route is Hall of the Gods' (Dark Passageway's, Yanmir's Fort's, Lindisfarne Monastery's,
Drangheim Prison's: one material per MM9 skin, POSES, the isle's blib build and finish checks) with the Anskram flame
cards (`card` billboard, the pipeline as fixed on 2026-10-30), seated on the ABCs' Flame socket markers.

Classes placed: Prop, CandleProp (all lit: StartOn 1, Blue 0), WallTorch, Brazier, TreasureBag (loot: kind chest) and
RUDEProp (the named townsfolk with dialogue scripts: static decorations in their script's pose; README).

  - RUDEProps and other creature ABCs are exported in full and posed in Blender (POSES: animation, first key): the
    seated peasants (PeasantMS2: its only animation MP_2s; the scripts' sitting/listen/conv1/Ludwig_writting
    animations are not in the model, so MM9 plays that one), the barkeeper (PeasantM2: MP_2a), Bjarni (Bjarni.scr
    `loopanim Sit`), Ercc (the drunk at the inn: erccspeech.scr `LoopAnim sitting`) and the cat (PropAnim `standdown`).
    Their `ngon`/`ngon_s` piece (one 300-vertex polygon, MM9's shadow n-gon) is stripped (HIDDEN).
  - HidePiece: an object's HidePiece0-4 pieces are stripped from its variant's raw GLBs (HIDDEN; Bathhouse's
    strip_pieces route): the two weapon racks (Group2, Group3), two shelves of ShelfItem09 and one of ShelfItem03.
  - Tipped: Shield/Shield0 (Shield_Rusty, pitch pi/2: the ABC lies flat, MM9 stands it on the wall) and Shield1/Shield2
    (Shield.ABC, pitch pi/2: the ABC stands, MM9 lays it flat; the old bake is flat, 10 units high, and fits pitch pi/2
    roll 0 at 0.41 against 39.7 for Dook's Castle's hanging shield1/shield2) get it baked in (TILTS); Prop4 (scroll-open,
    pitch 268.5 degrees) is Verhoffin Ruins' scrollp268 (the same pitch).
  - Not shipped by MM9 (MODELS.REZ has no such file; work/missing_models.txt): models\Props\Painting_Rectangle.ABC
    (Painting, Painting0): no decoration (SKIPPED). candelabra's second skin (candel.dtx) is not shipped either and
    binds no material (the ABC has material 0 only): ALIASES.

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
PROJECT = REPO / 'level_generation/projects/mm9r_drangheimcity'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/drangheimcity.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/drangheimcity.odm'
SCENE = REPO / 'assets_dev/worlds/mm9/maps/drangheimcity.scene.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/props/barstool2.abc', 'skins/props/barstool1.dtx'): 'barstool2',
    ('models/props/box01.abc', 'skins/props/pantry-items.dtx'): 'box01',
    ('models/props/box02.abc', 'skins/props/pantry-items.dtx'): 'box02',       # Thjorad's box02pantry: pantry-items02
    ('models/props/cart01.abc', 'skins/props/cart01.dtx'): 'cart01',
    ('models/props/cart02.abc', 'skins/props/cart02.dtx'): 'cart02',
    ('models/props/clover.abc', 'skins/props/plantsandtrees/clover.dtx'): 'clover',
    ('models/props/coatrack2.abc', 'skins/props/coatrack2.dtx'): 'coatrack2',
    ('models/props/hitchingpost.abc', 'skins/props/hitchingpost.dtx'): 'hitchingpost',
    ('models/props/jug1.abc', 'skins/props/jug1.dtx'): 'jug1',
    ('models/props/plate-stack1.abc', 'skins/props/plate-set1.dtx'): 'platestack1set1',   # Klusos': plate2 skin
    ('models/props/plate-stack2.abc', 'skins/props/plate-set1.dtx'): 'platestack2set1',
    ('models/props/stein_fancy01.abc', 'skins/props/stein_fancy01.dtx'): 'steinfancy01',
    ('models/props/tapestry-old01.abc', 'textures/leveltextures/misc/banner2.dtx'): 'tapestry_banner2',
    ('models/props/winebottle02.abc', 'skins/props/winebottle02.dtx'): 'winebottle02',
    ('models/props/winebottle03.abc', 'skins/props/winebottle03.dtx'): 'winebottle03',
    ('models/props/winebottle05.abc', 'skins/props/pantry-items02.dtx'): 'winebottle05',
    ('models/props/shelfitem09.abc', 'skins/props/shelfitem09.dtx'): 'shelfitem09',   # Sturmford built only variants
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/anvil.abc', 'skins/props/anvil.dtx'): 'anvil',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/basket_fruit.abc', 'skins/props/basket_fruit.dtx'): 'basketfruit',
    ('models/props/basket_veggies.abc', 'skins/props/basket_veggies.dtx'): 'basketveggies',
    ('models/props/bed.abc', 'skins/props/bed.dtx'): 'bed',
    ('models/props/bed_ornate.abc', 'skins/props/bed_ornate.dtx'): 'bedornate',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/bench_stone02.abc', 'skins/props/bench_stone.dtx'): 'benchstone02',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',
    ('models/props/bookcase02ns.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ns',
    ('models/props/cabinet01.abc', 'skins/props/cabinet01.dtx'): 'cabinet01',
    ('models/props/candelabra.abc', 'skins/props/candelabra.dtx'): 'candelabra',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair03.abc', 'skins/props/chair03.dtx'): 'chair03',
    ('models/props/chandelier2.abc', 'skins/props/chandelier2.dtx'): 'chandelier2',
    ('models/props/chandelier3.abc', 'skins/props/chandelier3.dtx'): 'chandelier3',
    ('models/props/coatrack1.abc', 'skins/props/coatrack1.dtx'): 'coatrack',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/dresser.abc', 'skins/props/dresserfancy.dtx'): 'dresserfancy',
    ('models/props/dresser.abc', 'skins/props/dresserplain.dtx'): 'dresser',
    ('models/props/dresserns.abc', 'skins/props/dresserfancy.dtx'): 'dresserfancyns',
    ('models/props/keg_beer.abc', 'skins/props/keg_beer.dtx'): 'kegbeer',
    ('models/props/logsburning.abc', 'skins/props/logsburning.dtx'): 'logsburning',
    ('models/props/pew2.abc', 'skins/props/pew2.dtx'): 'pew2',
    ('models/props/pillarstand.abc', 'skins/props/pillarstand.dtx'): 'pillarstand',
    ('models/props/pitcher01.abc', 'skins/props/pantry-items.dtx'): 'pitcher01',
    ('models/props/podium01.abc', 'skins/props/podium01.dtx'): 'podium01',
    ('models/props/portal-whole.abc', 'skins/props/portaldirty.dtx'): 'portalwhole',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shelfitem05.abc', 'skins/props/shelfitem05.dtx'): 'shelfitem05',
    ('models/props/shield.abc', 'skins/props/shield3.dtx'): 'shield3',
    ('models/props/shield.abc', 'skins/props/shield4.dtx'): 'shield4',
    ('models/props/smithhammer.abc', 'skins/props/smithhammer.dtx'): 'smithhammer',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitaged.dtx'): 'suitofarmor01',
    ('models/props/suitofarmor02.abc', 'skins/props/amoredsuitgold.dtx;skins/props/amoredsuithalberd.dtx'):
        'suitofarmor02',
    ('models/props/table01ns.abc', 'skins/props/table01.dtx'): 'table01ns',
    ('models/props/table_bench.abc', 'skins/props/table_bench.dtx'): 'tablebench2',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/throne.abc', 'skins/props/throne.dtx'): 'throne',
    ('models/props/training_archery1.abc', 'skins/props/training_archery.dtx'): 'trainingarchery1',
    ('models/props/training_spindummy1.abc', 'skins/props/training_spindummy1.dtx'): 'spindummy',
    ('models/props/training_strawdummy2_c.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2c',
    ('models/props/training_strawdummy2_l.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2l',
    ('models/props/training_strawdummy2_r.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2r',
    ('models/props/wallcandle.abc', 'skins/props/wallcandle.dtx'): 'wallcandle',
    ('models/props/weaponrack.abc', 'skins/props/weaponrack_used.dtx'): 'weaponrack',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet04.dtx'): 'weaponscabinet04',
    ('models/props/well.abc', 'skins/props/well.dtx'): 'well',
    ('models/props/winebottle01.abc', 'skins/props/winebottle01.dtx'): 'winebottle',
    ('models/props/winebottle04.abc', 'skins/props/pantry-items.dtx'): 'winebottle04',
    ('models/props/woodbin.abc', 'skins/props/woodbin.dtx'): 'woodbin',
}
ALIASES = {}
_OWNERS = {
    'anvil': 'drangheimprison', 'barrel': 'anskramkeep', 'barrel03': 'anskramkeep', 'basketfruit': 'klusoshouse',
    'basketveggies': 'klusoshouse', 'bed': 'anskramkeep', 'bedornate': 'dookscastle', 'bedmedium': 'anskramkeep',
    'benchstone02': 'templeofhonk', 'bookflat': 'templeofhonk', 'bookcase02ns': 'anskramkeep',
    'cabinet01': 'klusoshouse', 'candelabra': 'sturmfordcity', 'chair': 'anskramkeep', 'chair03': 'lichlab',
    'chandelier2': 'sturmfordcity', 'chandelier3': 'ruinedtemple', 'coatrack': 'isleofashes', 'crate': 'anskramkeep',
    'dresserfancy': 'klusoshouse', 'dresser': 'isleofashes', 'dresserfancyns': 'klusoshouse',
    'kegbeer': 'sturmfordcity', 'logs': 'lichlab', 'logsburning': 'isleofashes', 'pew2': 'lindisfarnemonastery',
    'pillarstand': 'chasmofthedead', 'pitcher01': 'klusoshouse', 'podium01': 'lichlab',
    'portalwhole': 'sturmfordcity', 'scroll': 'anskramkeep', 'shelfitem03': 'lichlab', 'shelfitem05': 'lichlab',
    'shield3': 'klusoshouse', 'shield4': 'dookscastle', 'smithhammer': 'tasaracademy',
    'suitofarmor01': 'drangheimprison', 'suitofarmor02': 'dookscastle', 'table01ns': 'lichlab',
    'tablebench2': 'drangheimprison', 'tableround': 'anskramkeep', 'throne': 'lichlab',
    'trainingarchery1': 'sturmfordcity', 'spindummy': 'traininghall', 'strawdummy2c': 'sturmfordcity',
    'strawdummy2l': 'sturmfordcity', 'strawdummy2r': 'sturmfordcity', 'wallcandle': 'klusoshouse',
    'weaponrack': 'anskramkeep', 'weaponscabinet04': 'anskramkeep', 'well': 'isleofashes',
    'winebottle': 'beethoven', 'winebottle04': 'sturmfordcity', 'woodbin': 'thjoradmine',
    'coatrack2': 'thronheimcity', 'steinfancy01': 'thronheimcity',
    'shelfitem03f': 'sturmfordcity', 'shelfitem09sg': 'sturmfordcity', 'shelfitem09d': 'sturmfordcity'}
REUSED = {prop: PROPS_DIR / f'mm9_{owner}_claude' for prop, owner in _OWNERS.items()}
# Objects whose decoration is another prop than their (model, skin)'s: the burning logs are the isle's logsburning
# (flame cards) where MM9's Fire stands on them, else the Lich Lab's unlit logs (FIRE_ON_LOGS, filled by
# object_prop from the DAT's Fire objects); the HidePiece variants (HIDDEN).
OBJECT_PROP = {}
# Variants built here from another prop's source (MODELS id).
SOURCES = {'cart02nohay': 'cart02', 'shelfitem09g': 'shelfitem09', 'shelfitem03hc': 'shelfitem03',
           'weaponrackg1': 'weaponrack', 'weaponrackg2': 'weaponrack',
           'shelfitem03f': 'shelfitem03', 'shelfitem09sg': 'shelfitem09', 'shelfitem09d': 'shelfitem09'}
# Variants of a reused prop's source model: converted here from the extracted ABC (their MODELS key)
OWN_SOURCE = {'shelfitem03hc', 'weaponrackg1', 'weaponrackg2', 'shelfitem09', 'shelfitem09g'}
# The two shields (pitch 90): Shield.ABC's first animation lays it down and MM9's pitch stands it up again: they hang on
# the wall as Dook's Castle's shield3r/shield4 (Thjorgard City's route; prop_audit.py, 2026-11-07). Until then they
# took Thronheim City's shieldNflat, read against the old bake (which lies flat): they stuck out of the wall like shelves.
TILT_OF = {('shield3', 90, 0): 'shield3r', ('shield4', 90, 0): 'shield4'}
TILTS = {v: (1.5707964, 3.1415927) for v in ('shield3r', 'shield4')}
SOURCES['shield3r'] = 'shield3'
REUSED.update({v: PROPS_DIR / 'mm9_dookscastle_claude' for v in ('shield3r', 'shield4')})
# HidePiece0-4 of the objects: their pieces stripped from the variant's raw GLBs (convert_all.strip).
HIDDEN = {'cart02nohay': ['Hay'], 'shelfitem09g': ['Gloves'], 'shelfitem03hc': ['Hourglass1', 'Crystals1'],
          'weaponrackg1': ['Group1'], 'weaponrackg2': ['Group2'],
          'shelfitem03f': ['Crystals1', 'Wands1', 'Hourglass1'], 'shelfitem09sg': ['SkullCaps', 'Gloves'],
          'shelfitem09d': ['Daggers']}
# HidePiece sets -> variant, per prop (object_prop picks by the object's HidePiece list)
HIDE_VARIANTS = {('cart02', ('hay',)): 'cart02nohay', ('shelfitem09', ('gloves',)): 'shelfitem09g',
                 ('shelfitem09', ('gloves', 'skullcaps')): 'shelfitem09sg', ('shelfitem09', ('daggers',)): 'shelfitem09d',
                 ('shelfitem03', ('crystals1', 'hourglass1')): 'shelfitem03hc',
                 ('shelfitem03', ('crystals1', 'hourglass1', 'wands1')): 'shelfitem03f',
                 # ShelfItem05.abc has no Wands1 or Crystals1 piece (five jars): Shelfitems' HidePiece hides nothing
                 ('shelfitem05', ('crystals1', 'wands1')): 'shelfitem05',
                 ('weaponrack', ('group1',)): 'weaponrackg1', ('weaponrack', ('group2',)): 'weaponrackg2'}
LIBRARY = {}
POSES = {}
PLACE_POSES = {}
CHECK_POSES = {}
POSE_TURN = {}
SKIN_ORDER = {}
CLASSES = {'Prop', 'CandleProp', 'WallTorch', 'Brazier', 'TreasureBag', 'RUDEProp', 'Barrel', 'Clover', 'WellMMIX'}
# Objects of those classes (and the other model-carrying objects of the DAT) that get no decoration: name -> reason.
SKIPPED = {}
# MM9 Fire objects stand on burning logs: a logsburning object within FIRE_RADIUS_LT of a Fire (plan distance) is lit
FIRE_RADIUS_LT = 48.0


def key(path):
    return ';'.join(part.replace('\\', '/').lower().strip() for part in (path or '').split(';'))


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def tilt_degrees(p):
    r = p.get('Rotation') or [0, 0, 0]
    return int(round(math.degrees(float(r[0])))) % 360, int(round(math.degrees(float(r[2])))) % 360


_fires = None


def fire_points():
    global _fires
    if _fires is None:
        _fires = [o['props']['Pos'] for o in objects() if o['class'] == 'Fire']
    return _fires


def object_prop(o):
    p = o['props']
    pair = (key(p['Filename']), key(p.get('Skin')))
    prop = OBJECT_PROP.get(p.get('Name')) or MODELS[ALIASES.get(pair, pair)]
    if prop == 'logsburning':
        x, z = p['Pos'][0], p['Pos'][2]
        if not any(math.hypot(f[0] - x, f[2] - z) <= FIRE_RADIUS_LT for f in fire_points()):
            prop = 'logs'
    hidden_set = tuple(sorted(p[f'HidePiece{k}'].lower() for k in range(5) if p.get(f'HidePiece{k}')))
    if hidden_set:
        prop = HIDE_VARIANTS.get((prop, hidden_set), prop)
    if source_prop(prop) not in MODELS.values() and prop not in REUSED and prop not in SOURCES:
        raise SystemExit(f"{p['Name']}: {prop} has no source")
    tilt = tilt_degrees(p)
    if tilt != (0, 0):
        if (prop, *tilt) not in TILT_OF:
            raise SystemExit(f"{p['Name']}: {prop} tilted pitch {tilt[0]} roll {tilt[1]} has no variant")
        prop = TILT_OF[(prop, *tilt)]
    if tilt == (0, 0) and prop in TILTS:
        raise SystemExit(f"{p['Name']}: {prop} is a tilted model, the object is upright")
    hidden = sorted(p[f'HidePiece{k}'].lower() for k in range(5) if p.get(f'HidePiece{k}'))
    if hidden and prop != 'shelfitem05' and hidden != sorted(x.lower() for x in HIDDEN.get(prop, [])):
        raise SystemExit(f"{p['Name']}: {prop} hides {hidden}, its model {HIDDEN.get(prop)}")
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
    print('built:', len(built_props()), [(p, counts[p]) for p in built_props()])
    print('reused:', len([p for p in REUSED if counts[p]]), [(p, counts[p]) for p in sorted(REUSED) if counts[p]])
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

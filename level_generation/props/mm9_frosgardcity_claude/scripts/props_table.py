r"""Thjorgard City's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
and the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9 props
project are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they are); the
rest are built here. The route is Sturmford City's (level_generation/props/mm9_sturmfordcity_claude/: one material per
MM9 skin, specs.json turns, POSES, HidePiece variants, the isle's blib build and finish checks, the Anskram flame cards
on the ABCs' Flame socket markers).

Classes placed: Prop, CandleProp (lit: StartOn 1; Clawlamp0 is Blue 1), Torch (MM9's torch2 sconce, The Arena's
torchrust), DestructableProp (the two beakers), Clover (models\Props\clover.ABC), WellMMIX (the drinkable well, the
isle's well). No RUDEProp, TreasureBag or TreasureChest in this DAT.

  - PropAnim.scr poses: Pickaxe0-2 (Dwarfaxe.ABC `onside`) are Tasar Academy's posed dwarfaxeonside; Bed3, Bed18-20
    (BedMedium.ABC `EW`: the Scene Root a quarter turn about the vertical, the same turn as MM9's `ns` models) are
    built posed (bedmediumew, POSES); Bed4/Bed5 (Bed.ABC `ew`) keep the plain bed: Bed.ABC has no `ew` animation
    (only `Bed`), so LoopAnim finds nothing and MM9 shows its default pose.
  - HidePiece: an object's HidePiece0-4 pieces are stripped from its variant's raw GLBs (HIDDEN; HIDE_OF picks the
    variant by the hidden set). Hidden names the model does not have are ignored (NO_SUCH_PIECE: ShelfItem05 has no
    Wands1 or Crystals1, its four shelves are the plain shelfitem05).
  - Tipped: Shield0-9 (Shield.ABC, pitch pi/2) hang on the walls: Dook's Castle's hung shield1/shield2/shield4/shield3r
    (TILT_OF, TILTS), as Thjorgard City's. Until 2026-11-07 they took Sturmford's and Thronheim's shieldNflat, which
    lie flat (the old bake's reading of the pitch): they stuck out of the walls like shelves (prop_audit.py).
  - Clawlamp0 is a CandleProp with Blue 1: the upright claw lamp with its ice orb glowing blue (Yanmir's Fort's orb
    route), clawlampupblue; Clawlamp2 (a plain Prop) is Sturmford's clawlampup.

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
PROJECT = REPO / 'level_generation/projects/mm9r_frosgardcity'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/frosgardcity.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/frosgardcity.odm'
SCENE = REPO / 'assets_dev/worlds/mm9/maps/frosgardcity.scene.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/dog.abc', 'skins/dog.dtx'): 'dog',                                               # posed: dogsitting
    ('models/props/maypole_old.abc', 'skins/props/maypole_old.dtx'): 'maypoleold',
    ('models/props/maypole.abc', 'skins/props/maypole.dtx'): 'maypole',                       # ChangeModel.scr, key 268
    ('models/props/plate-set2.abc', 'skins/props/plate-set1.dtx'): 'plateset2p1',
    ('models/props/tapestry-old01.abc', 'textures/leveltextures/misc/banner1.dtx'): 'tapestry_banner1',
    ('models/props/weaponscabinet03.abc', 'skins/props/weaponscabinet03.dtx'): 'weaponscabinet03s3',
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/anvil.abc', 'skins/props/anvil.dtx'): 'anvil',
    ('models/props/bag-herbs1.abc', 'skins/pickupitems/quest/bagherbs1.dtx'): 'bagherbs1',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/barstool1.abc', 'skins/props/barstool1.dtx'): 'barstool1',
    ('models/props/bed_cot.abc', 'skins/props/bed_cot.dtx'): 'cot',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/bookstack01.abc', 'skins/props/bookstack01.dtx'): 'bookstack01',
    ('models/props/brazier.abc', 'skins/props/brazier.dtx'): 'brazier',
    ('models/props/burner.abc', 'skins/props/burner.dtx'): 'burner',
    ('models/props/chair_fordesk02.abc', 'skins/props/chair_fordesk02.dtx'): 'chairdesk02',
    ('models/props/chandelier2.abc', 'skins/props/chandelier2.dtx'): 'chandelier2',
    ('models/props/chandelier3.abc', 'skins/props/chandelier3.dtx'): 'chandelier3',
    ('models/props/clawlamp.abc', 'skins/props/clawlamp.dtx'): 'clawlampup',
    ('models/props/clover.abc', 'skins/props/plantsandtrees/clover.dtx'): 'clover',
    ('models/props/coalbin.abc', 'skins/props/coalbin.dtx'): 'coalbin',
    ('models/props/coatrack2.abc', 'skins/props/coatrack2.dtx'): 'coatrack2',
    ('models/props/dresserns.abc', 'skins/props/dresserplain.dtx'): 'dresserns',
    ('models/props/forge.abc', 'skins/props/forge.dtx'): 'forge',
    ('models/props/hangingbrazierbowl.abc', 'skins/props/hangingbrazierbowl3.dtx'): 'hangingbowl',
    ('models/props/herb-rack1.abc', 'skins/props/herb-rack1.dtx'): 'herbrack1',
    ('models/props/herb-rack2.abc', 'skins/props/herb-rack1.dtx'): 'herbrack2',
    ('models/props/iron-ingots.abc', 'skins/props/iron-ingots.dtx'): 'ironingots',
    ('models/props/keg_beer.abc', 'skins/props/keg_beer.dtx'): 'kegbeer',
    ('models/props/logsburning.abc', 'skins/props/logsburning.dtx'): 'logs',
    ('models/props/mug1.abc', 'skins/props/mug1.dtx'): 'mug1',
    ('models/props/oillamp.abc', 'skins/props/oillamp.dtx'): 'oillamp',
    ('models/props/pew3.abc', 'skins/props/pew3.dtx'): 'pew3',
    ('models/props/pitcher01.abc', 'skins/props/pantry-items.dtx'): 'pitcher01',
    ('models/props/podium01.abc', 'skins/props/podium01.dtx'): 'podium01',
    ('models/props/portal-whole.abc', 'skins/props/portaldirty.dtx'): 'portalwhole',
    ('models/props/runestone.abc', 'skins/props/runestone.dtx'): 'runestone',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/shelfitem01.abc', 'skins/props/shelfitem01.dtx'): 'shelfitem01',
    ('models/props/shelfitem02.abc', 'skins/props/shelfitem02.dtx'): 'shelfitem02',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shelfitem05.abc', 'skins/props/shelfitem05.dtx'): 'shelfitem05',
    ('models/props/shield.abc', 'skins/props/shield.dtx'): 'shield1',
    ('models/props/shield.abc', 'skins/props/shield2.dtx'): 'shield2',
    ('models/props/shield.abc', 'skins/props/shield3.dtx'): 'shield3',
    ('models/props/shield.abc', 'skins/props/shield4.dtx'): 'shield4',
    ('models/props/smithhammer.abc', 'skins/props/smithhammer.dtx'): 'smithhammer',
    ('models/props/spikepit.abc', 'skins/props/spikepit.dtx'): 'spikepit',
    ('models/props/stove.abc', 'skins/props/stove.dtx'): 'stove',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitplain.dtx'): 'suitofarmor01plain',
    ('models/props/table_bench.abc', 'skins/props/table_bench.dtx'): 'tablebench2',
    ('models/props/tableround2.abc', 'skins/props/tableround2.dtx'): 'tableround2',
    ('models/props/throne.abc', 'skins/props/throne.dtx'): 'throne',
    ('models/props/training_archery1.abc', 'skins/props/training_archery.dtx'): 'trainingarchery1',
    ('models/props/training_mount.abc', 'skins/props/training_mount.dtx'): 'trainingmount',
    ('models/props/training_spindummy1.abc', 'skins/props/training_spindummy1.dtx'): 'spindummy',
    ('models/props/training_strawdummy2_c.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2c',
    ('models/props/training_strawdummy2_l.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2l',
    ('models/props/training_strawdummy2_r.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2r',
    ('models/props/vikingship.abc', 'skins/props/vikingship.dtx'): 'vikingship',
    ('models/props/wallcandle.abc', 'skins/props/wallcandle.dtx'): 'wallcandle',
    ('models/props/weaponrack.abc', 'skins/props/weaponrack_used.dtx'): 'weaponrack',
    ('models/props/weaponrackns.abc', 'skins/props/weaponrack_used.dtx'): 'weaponrackns',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet01.dtx'): 'weaponscabinet01',
    ('models/props/well.abc', 'skins/props/well.dtx'): 'well',
    ('models/props/winebottle01.abc', 'skins/props/winebottle01.dtx'): 'winebottle',
}
ALIASES = {}
_OWNERS = {
    'anvil': 'drangheimprison', 'bagherbs1': 'tasaracademy', 'barrel': 'anskramkeep', 'barstool1': 'sturmfordcity',
    'cot': 'isleofashes', 'bedmedium': 'anskramkeep', 'bedmediumew': 'thjorgardcity', 'bookflat': 'templeofhonk',
    'bookcase02ew': 'anskramkeep', 'bookstack01': 'lichlab', 'brazier': 'templeofhonk', 'burner': 'lichlab',
    'chairdesk02': 'drangheimprison', 'chandelier2': 'sturmfordcity', 'chandelier3': 'ruinedtemple',
    'clawlampup': 'sturmfordcity', 'clover': 'drangheimcity', 'coalbin': 'drangheimprison',
    'coatrack2': 'thronheimcity', 'dresserns': 'anskramkeep', 'forge': 'tasaracademy', 'hangingbowl': 'templeofhonk',
    'herbrack1': 'thronheimcity', 'herbrack2': 'thjorgardcity', 'ironingots': 'drangheimprison',
    'kegbeer': 'sturmfordcity', 'logs': 'lichlab', 'mug1': 'sturmfordcity', 'oillamp': 'thjoradmine',
    'pew3': 'bathhouse', 'pitcher01': 'klusoshouse', 'podium01': 'lichlab', 'portalwhole': 'sturmfordcity',
    'runestone': 'darkpassageway', 'scroll': 'anskramkeep', 'shelfitem01': 'lichlab', 'shelfitem02': 'lichlab',
    'shelfitem03': 'lichlab', 'shelfitem05': 'lichlab', 'shelfitem02mp': 'thronheimcity',
    'shelfitem03f': 'sturmfordcity', 'shield1': 'dookscastle', 'shield2': 'dookscastle', 'shield3': 'klusoshouse',
    'shield4': 'dookscastle', 'shield3r': 'dookscastle', 'smithhammer': 'tasaracademy',
    'spikepit': 'anskramkeep', 'stove': 'drangheimprison', 'suitofarmor01plain': 'thronheimcity',
    'tablebench2': 'drangheimprison', 'tableround2': 'drangheimprison', 'throne': 'lichlab',
    'trainingarchery1': 'sturmfordcity', 'trainingmount': 'traininghall', 'spindummy': 'traininghall',
    'strawdummy2c': 'sturmfordcity', 'strawdummy2l': 'sturmfordcity', 'strawdummy2r': 'sturmfordcity',
    'vikingship': 'isleofashes', 'wallcandle': 'klusoshouse', 'weaponrack': 'anskramkeep',
    'weaponrackns': 'drangheimprison', 'weaponscabinet01': 'anskramkeep', 'well': 'isleofashes',
    'winebottle': 'beethoven', 'logsburning': 'isleofashes'}
REUSED = {prop: PROPS_DIR / f'mm9_{owner}_claude' for prop, owner in _OWNERS.items()}
# Objects whose decoration is another prop than their (model, skin)'s: the dogs (PropAnim.scr "sitting"), filled in
# from the DAT (the BedMedium beds in MM9's EW pose, PropAnim.scr "ew": Thjorgard City's bedmediumew).
OBJECT_PROP = {'Dog1': 'dogsitting', 'Dog2': 'dogsitting',
               # the hall's fire pit: Logs0-2 lie under MM9's Fire0-2 (Scale 2.5): the isle's logsburning (flame cards)
               'Logs0': 'logsburning', 'Logs1': 'logsburning', 'Logs2': 'logsburning',
               **{f'Bed{k}': 'bedmediumew' for k in (2, 3, 4, 5)}}
# Variants built here from another prop's source (MODELS id).
SOURCES = {'dogsitting': 'dog', 'logsburning': 'logs', 'weaponracknsusedg2': 'weaponrackns', 'weaponracknsusedg3': 'weaponrackns',
           # reused variants, for the placements' raw sources
           'bedmediumew': 'bedmedium', 'shield3r': 'shield3', 'shelfitem02mp': 'shelfitem02', 'shelfitem03f': 'shelfitem03'}
# Pitch, roll baked in (decorations turn about z only); placements.py tilts the raw points the same way to check them.
TILTS = {'shield1': (1.5707964, 3.1415927), 'shield2': (1.5707964, 3.1415927), 'shield3r': (1.5707964, 3.1415927),
         'shield4': (1.5707964, 3.1415927)}
# (prop, pitch, roll in whole degrees) of a tilted object -> its tilted variant (Yanmir's Fort's route).
TILT_OF = {('shield1', 90, 0): 'shield1', ('shield2', 90, 0): 'shield2', ('shield3', 90, 0): 'shield3r',
           ('shield4', 90, 0): 'shield4'}
# HidePiece0-4 of the objects: their pieces stripped from the variant's raw GLBs (convert_all.strip). Built here: the
# used-skin NS weapon racks without Group2 / Group3 (Thronheim's weaponracknsnewg<n> scheme); reused: Thronheim's
# shelfitem02mp, Sturmford's shelfitem03f.
HIDDEN = {'shelfitem02mp': ['Amulets1', 'SkelBones1', 'Skull1'], 'shelfitem03f': ['Crystals1', 'Wands1', 'Hourglass1'],
          'weaponracknsusedg2': ['Group2'], 'weaponracknsusedg3': ['Group3']}
# (prop, hidden pieces lower case, sorted) -> its HidePiece variant
HIDE_OF = {(SOURCES[v], tuple(sorted(x.lower() for x in pieces))): v for v, pieces in HIDDEN.items()}
# HidePiece names that are not pieces of the model (ignored, as MM9 does): ShelfItem05 has Jar01-05 only.
NO_SUCH_PIECE = {'shelfitem05': {'wands1', 'crystals1'}}
# Posed models: (animation, frame) set in build (blib.import_raw) and placements (posed_points).
LIBRARY = {}
POSES = {'dogsitting': ('sitting', 0)}
# Reused posed models (built posed by their owners): placed and checked on MM9's pose as POSES are.
PLACE_POSES = {'bedmediumew': ('EW', 0)}
CHECK_POSES = {}
POSE_TURN = {}
SKIN_ORDER = {}
CLASSES = {'Prop', 'CandleProp', 'Brazier', 'DestructableProp', 'Clover', 'WellMMIX', 'PropDamager'}
# Objects of those classes (and the other model-carrying objects of the DAT) that get no decoration: name -> reason.
SKIPPED = {}


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
    prop = OBJECT_PROP.get(p.get('Name')) or MODELS[ALIASES.get(pair, pair)]
    if source_prop(prop) not in MODELS.values() and prop not in REUSED:
        raise SystemExit(f"{p['Name']}: {prop} has no source")
    tilt = tilt_degrees(p)
    if tilt != (0, 0):
        if (prop, *tilt) not in TILT_OF:
            raise SystemExit(f"{p['Name']}: {prop} tilted pitch {tilt[0]} roll {tilt[1]} has no variant")
        prop = TILT_OF[(prop, *tilt)]
    if tilt == (0, 0) and prop in TILTS:
        raise SystemExit(f"{p['Name']}: {prop} is a tilted model, the object is upright")
    hidden = sorted(p[f'HidePiece{k}'].lower() for k in range(5) if p.get(f'HidePiece{k}'))
    hidden = [h for h in hidden if h not in NO_SUCH_PIECE.get(prop, set())]
    if hidden and (prop, tuple(hidden)) in HIDE_OF:
        prop = HIDE_OF[(prop, tuple(hidden))]
    if hidden and hidden != sorted(x.lower() for x in HIDDEN.get(prop, [])):
        raise SystemExit(f"{p['Name']}: {prop} hides {hidden}, its model {HIDDEN.get(prop)}")
    return prop


def placements():
    """(object index, prop id) of every decoration object (not the SKIPPED ones)."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')
            and o['props'].get('Name') not in SKIPPED]


def source_prop(prop):
    return SOURCES.get(prop, prop)


# Models a script swaps in (ChangeModel.scr): built here, placed beside their object (placements.py), shown by a cog.
CHANGED = {'Prop0': 'maypole'}


def built_props():
    """The props built here: the placed ones minus the reused, and the ChangeModel targets."""
    try:
        placed = {prop for _, prop in placements()} | set(CHANGED.values())
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
    # a reused prop needs its owner's raw GLB, build meta and binding origin (placements.py) and its installed model
    for prop in sorted(p for p in REUSED if counts[p]):
        owner = REUSED[prop]
        need = [owner / f'work/raw/{prop}/{prop}.glb', owner / f'work/{prop}_meta.json',
                REPO / f'assets_source/worlds/mm9/models/mm9_deco_{prop}.glb']
        missing = [str(n.relative_to(REPO)) for n in need if not n.exists()]
        origins_path = owner / 'work/binding_origins.json'
        if not origins_path.exists() or prop not in json.loads(origins_path.read_text()) and \
                source_prop(prop) not in json.loads(origins_path.read_text()):
            missing.append(f'{origins_path.relative_to(REPO)}[{prop}]')
        if missing:
            print('REUSED WITHOUT ITS FILES:', prop, missing)
    index = {o['index']: o for o in out}
    for idx, prop in placements():
        p = index[idx]['props']
        if 'propanim' in str(p.get('ScriptName')).lower():
            print('PropAnim', p['Name'], p['Filename'], repr(p.get('ScriptParams')), '->', prop)
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

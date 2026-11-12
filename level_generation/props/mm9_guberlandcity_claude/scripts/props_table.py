r"""Guberland City's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
and the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9 props
project are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they are;
the reuse check is work/registry.py over every MM9 props project); the rest are built here. The route is Thronheim
City's (itself Sturmford City's: one material per MM9 skin, POSES, the isle's blib build and finish checks).

Classes placed: Prop, CandleProp (all lit: chandelier2, chandelier3, wallcandle; reused with their owners' flames),
WellMMIX (Well0, the isle's well) and SeaMonster (SeaMonster0, the tiny sea monster in the apothecary's fish tank:
SEAMONSTER.abc with Sea Monster A's skin SeaCreatureF.dtx, posed at its idle `standwater`'s first key, non-solid).
This DAT has no TreasureChest, TreasureBag, DestructableProp, Barrel or RUDEProp.

  - Cabinet7 (PropAnim.scr `ns`): WeaponsCabinet02.abc has an `NS` animation that turns its Scene Root a quarter:
    weaponscabinet02ns is built posed (POSES, as Thjorgard's bedmediumew) and checked against MM9's pose.
  - HidePiece: an object's hidden set picks its variant (HIDE_OF), all built by other projects: shelfitem02mp
    (Thronheim), shelfitem03f, shelfitem09d, weaponracknewg2/g3 (Sturmford), shelfitem03hwc (Thjorgard).
    ShelfItem05's hidden Wands1, Crystals1 are not pieces of ShelfItem05.abc: plain shelfitem05 (IGNORED_HIDES).
  - Tipped: Shield2/Shield3 (Shield.ABC, pitch pi/2) lie flat: Thronheim's shield3flat / shield4flat.
  - Scroll objects (models\PickUpItems\Scroll.abc) name skins\PickUpItems\scroll.dtx, which MM9 does not ship:
    Tasar Academy's scrollpickup (scrolldouble skin) stands in, as Arslegard City's (ALIASES).
  - Clover (the two four-leaf clover patches, Drangheim City's `clover`): placed since 2026-11-12, so that the map's
    bonus events have something to click (they were left out at first, "not a decoration class").

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
PROJECT = REPO / 'level_generation/projects/mm9r_guberlandcity'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/guberlandcity.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/guberlandcity.odm'
SCENE = REPO / 'assets_dev/worlds/mm9/maps/guberlandcity.scene.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/pickupitems/quest/prize.abc', 'skins/pickupitems/quest/prize.dtx'): 'prize',
    ('models/props/suitofarmor02.abc', 'skins/props/amoredsuitaged.dtx;skins/props/amoredsuithalberd.dtx'):
        'suitofarmor02aged',
    ('models/props/tapestry-old01.abc', 'textures/leveltextures/misc/banner7.dtx'): 'tapestry_banner7',
    # the fish tank's sea monster (SeaMonster class: no Skin property; MONSTERS.txt row 177 Sea Monster A's skin)
    ('models/seamonster.abc', 'skins/seacreaturef.dtx'): 'seamonster',
    # the clover patches (Clover class); built by Drangheim City
    ('models/props/clover.abc', 'skins/props/plantsandtrees/clover.dtx'): 'clover',
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/modelprops/clansoldierhelmet.abc', 'skins/clansoldier1.dtx'): 'clansoldierhelmet',
    ('models/modelprops/dookmilitiahelmet.abc', 'skins/dookmilitia1.dtx'): 'dookmilitiahelmet',
    # Scroll objects name skins\PickUpItems\scroll.dtx, which MM9 does not ship: Tasar Academy's scrolldouble skin on
    # the same ABC (its scrollpickup) stands in, as Arslegard City's
    ('models/pickupitems/scroll.abc', 'skins/props/scrolldouble.dtx'): 'scrollpickup',
    ('models/props/anvil.abc', 'skins/props/anvil.dtx'): 'anvil',
    ('models/props/bag-herbs1.abc', 'skins/pickupitems/quest/bagherbs1.dtx'): 'bagherbs1',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/barstool1.abc', 'skins/props/barstool1.dtx'): 'barstool1',
    ('models/props/basket_fruit.abc', 'skins/props/basket_fruit.dtx'): 'basketfruit',
    ('models/props/basket_veggies.abc', 'skins/props/basket_veggies.dtx'): 'basketveggies',
    ('models/props/bed.abc', 'skins/props/bed.dtx'): 'bed',
    ('models/props/bed_ornate.abc', 'skins/props/bed_ornate.dtx'): 'bedornate',
    ('models/props/bed_wall.abc', 'skins/props/bed_wall.dtx'): 'bedwall',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/bench_stone02.abc', 'skins/props/bench_stone.dtx'): 'benchstone02',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/bookcase02ns.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ns',
    ('models/props/bookstack01.abc', 'skins/props/bookstack01.dtx'): 'bookstack01',
    ('models/props/bucket01.abc', 'skins/props/bucket01.dtx'): 'bucket01',
    ('models/props/burner.abc', 'skins/props/burner.dtx'): 'burner',
    ('models/props/cabinet01.abc', 'skins/props/cabinet01.dtx'): 'cabinet01',
    ('models/props/cabinet02ns.abc', 'skins/props/cabinet02.dtx'): 'cabinet02ns',
    ('models/props/chair02.abc', 'skins/props/chair02.dtx'): 'chair02',
    ('models/props/chair03.abc', 'skins/props/chair03.dtx'): 'chair03',
    ('models/props/chair_fordesk02.abc', 'skins/props/chair_fordesk02.dtx'): 'chairdesk02',
    ('models/props/chandelier2.abc', 'skins/props/chandelier2.dtx'): 'chandelier2',
    ('models/props/chandelier3.abc', 'skins/props/chandelier3.dtx'): 'chandelier3',
    ('models/props/clawlamp.abc', 'skins/props/clawlamp.dtx'): 'clawlampup',
    ('models/props/coalbin.abc', 'skins/props/coalbin.dtx'): 'coalbin',
    ('models/props/coatrack2.abc', 'skins/props/coatrack2.dtx'): 'coatrack2',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/desk01ns.abc', 'skins/props/desk01.dtx'): 'desk01ns',
    ('models/props/dresser.abc', 'skins/props/dresserfancy.dtx'): 'dresserfancy',
    ('models/props/dresser.abc', 'skins/props/dresserplain.dtx'): 'dresser',
    ('models/props/dresserns.abc', 'skins/props/dresserplain.dtx'): 'dresserns',
    ('models/props/forge.abc', 'skins/props/forge.dtx'): 'forge',
    ('models/props/herb-rack1.abc', 'skins/props/herb-rack1.dtx'): 'herbrack1',
    ('models/props/iron-ingots.abc', 'skins/props/iron-ingots.dtx'): 'ironingots',
    ('models/props/keg_beer.abc', 'skins/props/keg_beer.dtx'): 'kegbeer',
    ('models/props/mug1.abc', 'skins/props/mug1.dtx'): 'mug1',
    ('models/props/pew2ns.abc', 'skins/props/pew2.dtx'): 'pew2ns',
    ('models/props/pitcher01.abc', 'skins/props/pantry-items.dtx'): 'pitcher01',
    ('models/props/plantsandtrees/tree04.abc',
     'skins/props/plantsandtrees/treebark2.dtx;skins/props/plantsandtrees/treebranch3.dtx'): 'tree04',
    ('models/props/plate-set2.abc', 'skins/props/plate-set1.dtx'): 'plateset2p1',
    ('models/props/plate-stack2.abc', 'skins/props/plate-set1.dtx'): 'platestack2set1',
    ('models/props/podium02.abc', 'skins/props/podium02.dtx'): 'podium02',
    ('models/props/portal-whole.abc', 'skins/props/portaldirty.dtx'): 'portalwhole',
    ('models/props/pottedplant1.abc', 'skins/props/pottedplant1.dtx'): 'pottedplant1',
    ('models/props/pottedplant2.abc', 'skins/props/pottedplant2.dtx'): 'pottedplant2',
    ('models/props/pottedplant3.abc', 'skins/props/pottedplant3.dtx'): 'pottedplant3',
    ('models/props/sack03.abc', 'skins/props/sack01.dtx'): 'sack03',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/shelfitem01.abc', 'skins/props/shelfitem01.dtx'): 'shelfitem01',
    ('models/props/shelfitem02.abc', 'skins/props/shelfitem02.dtx'): 'shelfitem02',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shelfitem05.abc', 'skins/props/shelfitem05.dtx'): 'shelfitem05',
    ('models/props/shelfitem06.abc', 'skins/props/shelfitem06.dtx'): 'shelfitem06',
    ('models/props/shelfitem07.abc', 'skins/props/shelfitem07.dtx'): 'shelfitem07',
    ('models/props/shelfitem08.abc', 'skins/props/shelfitem08.dtx'): 'shelfitem08',
    ('models/props/shelfitem09.abc', 'skins/props/shelfitem09.dtx'): 'shelfitem09',
    ('models/props/shield.abc', 'skins/props/shield3.dtx'): 'shield3',
    ('models/props/shield.abc', 'skins/props/shield4.dtx'): 'shield4',
    ('models/props/smithhammer.abc', 'skins/props/smithhammer.dtx'): 'smithhammer',
    ('models/props/stove.abc', 'skins/props/stove.dtx'): 'stove',
    ('models/props/stovens.abc', 'skins/props/stove.dtx'): 'stovens',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitplain.dtx'): 'suitofarmor01plain',
    ('models/props/table01.abc', 'skins/props/table01.dtx'): 'table01',
    ('models/props/table_bench.abc', 'skins/props/table_bench.dtx'): 'tablebench2',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/tableround2.abc', 'skins/props/tableround2.dtx'): 'tableround2',
    ('models/props/throne.abc', 'skins/props/throne.dtx'): 'throne',
    ('models/props/training_archery1.abc', 'skins/props/training_archery.dtx'): 'trainingarchery1',
    ('models/props/training_mount.abc', 'skins/props/training_mount.dtx'): 'trainingmount',
    ('models/props/training_spindummy1.abc', 'skins/props/training_spindummy1.dtx'): 'spindummy',
    ('models/props/training_strawdummy2_c.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2c',
    ('models/props/training_strawdummy2_l.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2l',
    ('models/props/training_strawdummy2_r.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2r',
    ('models/props/wallcandle.abc', 'skins/props/wallcandle.dtx'): 'wallcandle',
    ('models/props/weaponrack.abc', 'skins/props/weaponrack_new.dtx'): 'weaponrack_new',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet04.dtx'): 'weaponscabinet04',
    ('models/props/weaponscabinet02.abc', 'skins/props/weaponscabinet02.dtx'): 'weaponscabinet02',
    ('models/props/weaponscabinet03.abc', 'skins/props/weaponscabinet03.dtx'): 'weaponscabinet03s3',
    ('models/props/weaponscabinet03.abc', 'skins/props/weaponscabinet06.dtx'): 'weaponscabinet03',
    ('models/props/well.abc', 'skins/props/well.dtx'): 'well',
}
# DAT (model, skin) pairs written otherwise than their MODELS key: the scroll skin MM9 does not ship, the sea monster
# without a Skin property.
ALIASES = {('models/pickupitems/scroll.abc', 'skins/pickupitems/scroll.dtx'):
           ('models/pickupitems/scroll.abc', 'skins/props/scrolldouble.dtx'),
           ('models/seamonster.abc', ''): ('models/seamonster.abc', 'skins/seacreaturef.dtx')}
_OWNERS = {
    'clansoldierhelmet': 'arslegardcity', 'dookmilitiahelmet': 'arslegardcity', 'scrollpickup': 'tasaracademy',
    'anvil': 'drangheimprison', 'bagherbs1': 'tasaracademy', 'barrel': 'anskramkeep', 'barstool1': 'sturmfordcity',
    'basketfruit': 'klusoshouse', 'basketveggies': 'klusoshouse', 'bed': 'anskramkeep', 'bedornate': 'dookscastle',
    'bedwall': 'drangheimprison', 'bedmedium': 'anskramkeep', 'benchstone02': 'templeofhonk',
    'bookflat': 'templeofhonk', 'bookcase02ew': 'anskramkeep', 'bookcase02ns': 'anskramkeep',
    'bookstack01': 'lichlab', 'bucket01': 'drangheimprison', 'burner': 'lichlab', 'cabinet01': 'klusoshouse',
    'cabinet02ns': 'klusoshouse', 'chair02': 'anskramkeep', 'chair03': 'lichlab', 'chairdesk02': 'drangheimprison',
    'chandelier2': 'sturmfordcity', 'chandelier3': 'ruinedtemple', 'clawlampup': 'sturmfordcity',
    'coalbin': 'drangheimprison', 'coatrack2': 'thronheimcity', 'crate': 'anskramkeep', 'desk01ns': 'anskramkeep',
    'dresserfancy': 'klusoshouse', 'dresser': 'isleofashes', 'dresserns': 'anskramkeep', 'forge': 'tasaracademy',
    'herbrack1': 'thronheimcity', 'ironingots': 'drangheimprison', 'kegbeer': 'sturmfordcity',
    'mug1': 'sturmfordcity', 'pew2ns': 'klusoshouse', 'pitcher01': 'klusoshouse', 'tree04': 'lindisfarnemonastery',
    'plateset2p1': 'frosgardcity', 'platestack2set1': 'drangheimcity', 'podium02': 'lindisfarnemonastery',
    'portalwhole': 'sturmfordcity', 'pottedplant1': 'thronheimcity', 'pottedplant2': 'thronheimcity',
    'pottedplant3': 'thronheimcity', 'sack03': 'drangheimprison', 'scroll': 'anskramkeep',
    'shelfitem01': 'lichlab', 'shelfitem02': 'lichlab', 'shelfitem03': 'lichlab', 'shelfitem05': 'lichlab',
    'shelfitem06': 'drangheimprison', 'shelfitem07': 'drangheimprison', 'shelfitem08': 'drangheimprison',
    'shelfitem02mp': 'thronheimcity', 'shelfitem03f': 'sturmfordcity', 'shelfitem03hwc': 'thjorgardcity',
    'shelfitem09d': 'sturmfordcity', 'shield3flat': 'thronheimcity', 'shield4flat': 'thronheimcity',
    'smithhammer': 'tasaracademy', 'stove': 'drangheimprison', 'stovens': 'klusoshouse',
    'suitofarmor01plain': 'thronheimcity', 'table01': 'lichlab', 'tablebench2': 'drangheimprison',
    'tableround': 'anskramkeep', 'tableround2': 'drangheimprison', 'throne': 'lichlab',
    'trainingarchery1': 'sturmfordcity', 'trainingmount': 'traininghall', 'spindummy': 'traininghall',
    'strawdummy2c': 'sturmfordcity', 'strawdummy2l': 'sturmfordcity', 'strawdummy2r': 'sturmfordcity',
    'wallcandle': 'klusoshouse', 'weaponracknewg2': 'sturmfordcity', 'weaponracknewg3': 'sturmfordcity',
    'weaponscabinet04': 'anskramkeep', 'weaponscabinet02': 'drangheimprison', 'weaponscabinet03s3': 'frosgardcity',
    'weaponscabinet03': 'thjorgardcity', 'well': 'isleofashes', 'clover': 'drangheimcity'}
REUSED = {prop: PROPS_DIR / f'mm9_{owner}_claude' for prop, owner in _OWNERS.items()}
# Objects whose decoration is another prop than their (model, skin)'s: the quarter-turned weapons cabinet (PropAnim
# `ns`, built posed), the HidePiece variants (HIDE_OF picks them by the hidden set).
OBJECT_PROP = {'Cabinet7': 'weaponscabinet02ns'}
# (prop, hidden pieces lower case sorted) -> its HidePiece variant
HIDE_OF = {('shelfitem02', ('amulets1', 'skelbones1', 'skull1')): 'shelfitem02mp',
           ('shelfitem03', ('crystals1', 'hourglass1', 'wands1')): 'shelfitem03f',
           ('shelfitem03', ('crystals1', 'wands1')): 'shelfitem03hwc',
           ('shelfitem09', ('daggers',)): 'shelfitem09d',
           ('weaponrack_new', ('group2',)): 'weaponracknewg2',
           ('weaponrack_new', ('group3',)): 'weaponracknewg3'}
# Objects tilted by their script's pose, not by their Rotation (checked against that pose in placements.py).
POSE_TILT = {}
# Variants built here from another prop's source (MODELS id); the reused variants' sources for the checks.
SOURCES = {'weaponscabinet02ns': 'weaponscabinet02', 'shield3flat': 'shield3', 'shield4flat': 'shield4',
           'shelfitem02mp': 'shelfitem02', 'shelfitem03f': 'shelfitem03', 'shelfitem03hwc': 'shelfitem03',
           'shelfitem09d': 'shelfitem09', 'weaponracknewg2': 'weaponrack_new', 'weaponracknewg3': 'weaponrack_new'}
# Pitch, roll baked in (decorations turn about z only); placements.py tilts the raw points the same way to check them.
TILTS = {'shield3flat': (1.5707964, 0.0), 'shield4flat': (1.5707964, 0.0)}
# (prop, pitch, roll in whole degrees) of a tilted object -> its tilted variant.
# 2026-11-07 (prop_audit.py): MM9's pitch pi/2 stands up the shield its first animation lays down: the shields hang
# on the walls as Dook's Castle's shield1/shield2/shield4/shield3r (Thjorgard City's route); the shieldNflat variants
# lie flat and stuck out of the walls like shelves.
TILT_OF = {('shield3', 90, 0): 'shield3r', ('shield4', 90, 0): 'shield4'}
TILTS.update({v: (1.5707964, 3.1415927) for v in ('shield1', 'shield2', 'shield3r', 'shield4')})
SOURCES['shield3r'] = 'shield3'
REUSED.update({v: PROPS_DIR / 'mm9_dookscastle_claude' for v in ('shield1', 'shield2', 'shield3r', 'shield4')})
# HidePiece0-4 of the objects: their pieces stripped from the variant's raw GLBs (the reused ones by their owners).
HIDDEN = {'shelfitem02mp': ['Amulets1', 'SkelBones1', 'Skull1'], 'shelfitem03f': ['Crystals1', 'Wands1', 'Hourglass1'],
          'shelfitem03hwc': ['Wands1', 'Crystals1'], 'shelfitem09d': ['Daggers'], 'weaponracknewg2': ['Group2'],
          'weaponracknewg3': ['Group3']}
# HidePieces that name no piece of the object's model (ShelfItem05.abc is five jars): nothing to hide.
IGNORED_HIDES = {'shelfitem05': {'wands1', 'crystals1'}}
LIBRARY = {}
# Posed models: (animation, frame) set in build (blib.import_raw) and placements (posed_points). Cabinet7's PropAnim
# `ns` plays WeaponsCabinet02's NS (its Scene Root turned a quarter: the cabinet MM9 shows); the sea monster in the
# apothecary's tank at its idle `standwater`'s first key.
POSES = {'weaponscabinet02ns': ('NS', 0), 'seamonster': ('standwater', 0)}
PLACE_POSES = {}
CHECK_POSES = {}
POSE_TURN = {}
SKIN_ORDER = {}
CLASSES = {'Prop', 'CandleProp', 'DestructableProp', 'WallTorch', 'Brazier', 'Barrel', 'WellMMIX', 'TreasureChest',
           'TreasureBag', 'RUDEProp', 'SeaMonster', 'Clover'}
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
    if tilt == (0, 0) and prop in TILTS and p.get('Name') not in POSE_TILT:
        raise SystemExit(f"{p['Name']}: {prop} is a tilted model, the object is upright")
    hidden = sorted(p[f'HidePiece{k}'].lower() for k in range(5) if p.get(f'HidePiece{k}')
                    and p[f'HidePiece{k}'].lower() not in IGNORED_HIDES.get(prop, ()))
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

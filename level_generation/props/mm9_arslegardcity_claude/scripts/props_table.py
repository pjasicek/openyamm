r"""Arslegard City's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
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
  - Tipped: Shield0-3 (Shield.ABC, pitch pi/2, yaw pi/2) lie flat as Sturmford's shield1flat/shield2flat and Thronheim
    City's shield3flat/shield4flat (TILT_OF, TILTS).
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
PROJECT = REPO / 'level_generation/projects/mm9r_arslegardcity'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/arslegardcity.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/arslegardcity.odm'
SCENE = REPO / 'assets_dev/worlds/mm9/maps/arslegardcity.scene.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
T = 'skins/props/plantsandtrees/'
MODELS = {
    # built here
    ('models/modelprops/clansoldierhelmet.abc', 'skins/clansoldier1.dtx'): 'clansoldierhelmet',
    ('models/modelprops/dookmilitiahelmet.abc', 'skins/dookmilitia1.dtx'): 'dookmilitiahelmet',
    ('models/props/horsestatue.abc', 'skins/props/horsestatue3.dtx'): 'horsestatue3',
    ('models/props/lamppost1.abc', 'skins/props/lamppost1.dtx'): 'lamppost1',                 # flame card
    ('models/props/plate1.abc', 'skins/props/plate2.dtx'): 'plate1',
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/modelprops/dwarfaxe.abc', 'skins/modelprops/dwarfaxe.dtx'): 'dwarfaxeonside',
    # Scroll1/Scroll2 name skins\PickUpItems\scroll.dtx, which MM9 does not ship: the same ABC with Tasar Academy's
    # scrolldouble skin (its scrollpickup) stands in
    ('models/pickupitems/scroll.abc', 'skins/pickupitems/scroll.dtx'): 'scrollpickup',
    ('models/pickupitems/quest/orb_linking.abc', 'skins/pickupitems/quest/orb_linking.dtx'): 'orblinking',
    ('models/props/bag-herbs1.abc', 'skins/pickupitems/quest/bagherbs1.dtx'): 'bagherbs1',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/barstool2.abc', 'skins/props/barstool1.dtx'): 'barstool2',
    ('models/props/basket_fruit.abc', 'skins/props/basket_fruit.dtx'): 'basketfruit',
    ('models/props/basket_veggies.abc', 'skins/props/basket_veggies.dtx'): 'basketveggies',
    ('models/props/beaker01.abc', 'skins/props/beaker01.dtx'): 'beaker01',
    ('models/props/bench_large1.abc', 'skins/props/bench_large1.dtx'): 'benchlarge1',
    ('models/props/bench_large1ns.abc', 'skins/props/bench_large1.dtx'): 'benchlarge1ns',
    ('models/props/bench_stone02.abc', 'skins/props/bench_stone.dtx'): 'benchstone02',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/bookcase02ns.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ns',
    ('models/props/bookstack01.abc', 'skins/props/bookstack01.dtx'): 'bookstack01',
    ('models/props/bucket01.abc', 'skins/props/bucket01.dtx'): 'bucket01',
    ('models/props/burner.abc', 'skins/props/burner.dtx'): 'burner',
    ('models/props/cabinet02ns.abc', 'skins/props/cabinet02.dtx'): 'cabinet02ns',
    ('models/props/cart02.abc', 'skins/props/cart02.dtx'): 'cart02',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair02.abc', 'skins/props/chair02.dtx'): 'chair02',
    ('models/props/chair03.abc', 'skins/props/chair03.dtx'): 'chair03',
    ('models/props/chandelier2.abc', 'skins/props/chandelier2.dtx'): 'chandelier2',
    ('models/props/chandelier3.abc', 'skins/props/chandelier3.dtx'): 'chandelier3',
    ('models/props/clawlamp.abc', 'skins/props/clawlamp.dtx'): 'clawlampup',
    ('models/props/coatrack1.abc', 'skins/props/coatrack1.dtx'): 'coatrack',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/debris/stonedebris01.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'stonedebris01ls',
    ('models/props/jug1.abc', 'skins/props/jug1.dtx'): 'jug1',
    ('models/props/keg_beer.abc', 'skins/props/keg_beer.dtx'): 'kegbeer',
    ('models/props/logsburning.abc', 'skins/props/logsburning.dtx'): 'logs',
    ('models/props/pew2ns.abc', 'skins/props/pew2.dtx'): 'pew2ns',
    ('models/props/plantsandtrees/tree05.abc', f'{T}treebark3.dtx;{T}treebranch4.dtx'): 'tree05',
    ('models/props/plantsandtrees/tree06.abc', f'{T}treebark3.dtx;{T}treebranch5.dtx'): 'tree06',
    ('models/props/plate-stack1.abc', 'skins/props/plate2.dtx'): 'platestack1',
    ('models/props/plate-stack2.abc', 'skins/props/plate2.dtx'): 'platestack2',
    ('models/props/podium01.abc', 'skins/props/podium01.dtx'): 'podium01',
    ('models/props/ropecoil.abc', 'skins/props/ropecoil.dtx'): 'ropecoil',
    ('models/props/sack01.abc', 'skins/props/sack01.dtx'): 'sack01',
    ('models/props/sack02.abc', 'skins/props/sack01.dtx'): 'sack02',
    ('models/props/sack03.abc', 'skins/props/sack01.dtx'): 'sack03',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/scroll1.abc', 'skins/props/scroll1.dtx'): 'scroll1',
    ('models/props/shelfitem01.abc', 'skins/props/shelfitem01.dtx'): 'shelfitem01',
    ('models/props/shelfitem02.abc', 'skins/props/shelfitem02.dtx'): 'shelfitem02',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shelfitem05.abc', 'skins/props/shelfitem05.dtx'): 'shelfitem05',
    ('models/props/shelfitem09.abc', 'skins/props/shelfitem09.dtx'): 'shelfitem09',
    ('models/props/shield.abc', 'skins/props/shield.dtx'): 'shield1',
    ('models/props/shield.abc', 'skins/props/shield2.dtx'): 'shield2',
    ('models/props/shield.abc', 'skins/props/shield3.dtx'): 'shield3',
    ('models/props/shield.abc', 'skins/props/shield4.dtx'): 'shield4',
    ('models/props/smithhammer.abc', 'skins/props/smithhammer.dtx'): 'smithhammer',
    ('models/props/stein_fancy01.abc', 'skins/props/stein_fancy01.dtx'): 'steinfancy01',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitplain.dtx'): 'suitofarmor01plain',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitgold.dtx'): 'suitofarmor01gold',
    ('models/props/table01ns.abc', 'skins/props/table01.dtx'): 'table01ns',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/tableround4.abc', 'skins/props/tableround5.dtx'): 'tableround5',
    ('models/props/tabletrestle.abc', 'skins/props/tabletrestle2.dtx'): 'tabletrestle2',
    ('models/props/training_archery1.abc', 'skins/props/training_archery.dtx'): 'trainingarchery1',
    ('models/props/training_spindummy1.abc', 'skins/props/training_spindummy1.dtx'): 'spindummy',
    ('models/props/training_strawdummy2_c.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2c',
    ('models/props/training_strawdummy2_l.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2l',
    ('models/props/training_strawdummy2_r.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2r',
    ('models/props/vials.abc', 'skins/props/vials.dtx'): 'vials',
    ('models/props/wallcandle.abc', 'skins/props/wallcandle.dtx'): 'wallcandle',
    ('models/props/weaponrack.abc', 'skins/props/weaponrack_new.dtx'): 'weaponrack_new',
    ('models/props/weaponrackns.abc', 'skins/props/weaponrack_new.dtx'): 'weaponracknew',
    ('models/props/winebottle01.abc', 'skins/props/winebottle01.dtx'): 'winebottle',
    ('models/props/winebottle02.abc', 'skins/props/winebottle02.dtx'): 'winebottle02',
    ('models/props/winebottle03.abc', 'skins/props/winebottle03.dtx'): 'winebottle03',
    ('models/props/winebottle04.abc', 'skins/props/pantry-items.dtx'): 'winebottle04',
    ('models/props/winebottle05.abc', 'skins/props/pantry-items02.dtx'): 'winebottle05',
    ('models/props/woodbin.abc', 'skins/props/woodbin.dtx'): 'woodbin',
}
ALIASES = {}
_OWNERS = {
    'dwarfaxeonside': 'tasaracademy', 'scrollpickup': 'tasaracademy', 'orblinking': 'inventastorca', 'bagherbs1': 'tasaracademy',
    'barrel': 'anskramkeep', 'barstool2': 'drangheimcity', 'basketfruit': 'klusoshouse',
    'basketveggies': 'klusoshouse', 'beaker01': 'lichlab', 'benchlarge1': 'thronheimcity',
    'benchlarge1ns': 'lindisfarnemonastery', 'benchstone02': 'templeofhonk', 'bookflat': 'templeofhonk',
    'bookcase02ew': 'anskramkeep', 'bookcase02ns': 'anskramkeep', 'bookstack01': 'lichlab',
    'bucket01': 'drangheimprison', 'burner': 'lichlab', 'cabinet02ns': 'klusoshouse', 'cart02': 'drangheimcity',
    'chair': 'anskramkeep', 'chair02': 'anskramkeep', 'chair03': 'lichlab', 'chandelier2': 'sturmfordcity',
    'chandelier3': 'ruinedtemple', 'clawlampup': 'sturmfordcity', 'coatrack': 'isleofashes', 'crate': 'anskramkeep',
    'stonedebris01ls': 'connectingtunnels', 'jug1': 'drangheimcity', 'kegbeer': 'sturmfordcity', 'logs': 'lichlab',
    'logsburning': 'isleofashes', 'pew2ns': 'klusoshouse', 'tree05': 'darkpassageway', 'tree06': 'darkpassageway',
    'platestack1': 'klusoshouse', 'platestack2': 'klusoshouse', 'podium01': 'lichlab', 'ropecoil': 'drangheimprison',
    'sack01': 'connectingtunnels', 'sack02': 'connectingtunnels', 'sack03': 'drangheimprison', 'scroll': 'anskramkeep',
    'scroll1': 'tasaracademy', 'shelfitem01': 'lichlab', 'shelfitem02': 'lichlab', 'shelfitem03': 'lichlab',
    'shelfitem05': 'lichlab', 'shelfitem09': 'drangheimcity', 'shield1': 'dookscastle', 'shield2': 'dookscastle',
    'shield3': 'klusoshouse', 'shield4': 'dookscastle', 'smithhammer': 'tasaracademy',
    'steinfancy01': 'thronheimcity', 'suitofarmor01plain': 'thronheimcity', 'suitofarmor01gold': 'thjorgardcity',
    'table01ns': 'lichlab', 'tableround': 'anskramkeep', 'tableround5': 'klusoshouse',
    'tabletrestle2': 'klusoshouse', 'trainingarchery1': 'sturmfordcity', 'spindummy': 'traininghall',
    'strawdummy2c': 'sturmfordcity', 'strawdummy2l': 'sturmfordcity', 'strawdummy2r': 'sturmfordcity',
    'vials': 'sturmfordcity', 'wallcandle': 'klusoshouse', 'weaponrack_new': 'tasaracademy',
    'weaponracknew': 'dookscastle', 'winebottle': 'beethoven', 'winebottle02': 'drangheimcity',
    'winebottle03': 'drangheimcity', 'winebottle04': 'sturmfordcity', 'winebottle05': 'drangheimcity',
    'woodbin': 'thjoradmine',
    # the variants of other projects (HidePiece, tilted)
    'shield1flat': 'sturmfordcity', 'shield2flat': 'sturmfordcity', 'shield3flat': 'thronheimcity',
    'shield4flat': 'thronheimcity', 'shelfitem03f': 'sturmfordcity', 'shelfitem03hc': 'drangheimcity',
    'shelfitem09g': 'drangheimcity', 'shelfitem09sg': 'sturmfordcity', 'shelfitem09d': 'sturmfordcity', 'weaponracknewg3': 'sturmfordcity',
    'weaponrackg1': 'drangheimcity', 'weaponracknsnewg1': 'thronheimcity', 'weaponracknsnewg2': 'thjorgardcity',
    'weaponracknsnewg3': 'thronheimcity'}
REUSED = {prop: PROPS_DIR / f'mm9_{owner}_claude' for prop, owner in _OWNERS.items()}
# Objects whose decoration is another prop than their (model, skin)'s: the logs under MM9's two Fire objects burn
# (the isle's logsburning, its flame cards; convert.py's check: work/fires.txt).
OBJECT_PROP = {'Prop51': 'logsburning', 'Logs0': 'logsburning'}
# Variants built here or by others from another prop's source (MODELS id).
SOURCES = {'plate1p80': 'plate1', 'logsburning': 'logs',
           'shield1flat': 'shield1', 'shield2flat': 'shield2', 'shield3flat': 'shield3', 'shield4flat': 'shield4',
           'shelfitem03f': 'shelfitem03', 'shelfitem03hc': 'shelfitem03', 'shelfitem09g': 'shelfitem09',
           'shelfitem09sg': 'shelfitem09', 'shelfitem09d': 'shelfitem09', 'weaponracknewg3': 'weaponrack_new', 'weaponrackg1': 'weaponrack_new',
           'weaponracknsnewg1': 'weaponracknew', 'weaponracknsnewg2': 'weaponracknew',
           'weaponracknsnewg3': 'weaponracknew'}
# Pitch, roll baked in (decorations turn about z only); placements.py tilts the raw points the same way to check them.
TILTS = {'shield1flat': (1.5707964, 0.0), 'shield2flat': (1.5707964, 0.0), 'shield3flat': (1.5707964, 0.0),
         'shield4flat': (1.5707964, 0.0), 'plate1p80': (1.4035, 0.0)}   # 80.4 degrees: MM9's 79.9 and 80.9 (one variant, 0.7 units apart at the rim)
# (prop, pitch, roll in whole degrees) of a tilted object -> its tilted variant (Yanmir's Fort's route).
# 2026-11-07 (prop_audit.py): MM9's pitch pi/2 stands up the shield its first animation lays down: the shields hang
# on the walls as Dook's Castle's shield1/shield2/shield4/shield3r (Thjorgard City's route); the shieldNflat variants
# lie flat and stuck out of the walls like shelves.
TILT_OF = {('shield1', 90, 0): 'shield1', ('shield2', 90, 0): 'shield2', ('shield3', 90, 0): 'shield3r',
           ('shield4', 90, 0): 'shield4', ('plate1', 80, 0): 'plate1p80', ('plate1', 81, 0): 'plate1p80'}
TILTS.update({v: (1.5707964, 3.1415927) for v in ('shield1', 'shield2', 'shield3r', 'shield4')})
SOURCES['shield3r'] = 'shield3'
REUSED.update({v: PROPS_DIR / 'mm9_dookscastle_claude' for v in ('shield1', 'shield2', 'shield3r', 'shield4')})
# HidePiece0-4 of the objects: their pieces stripped from the variant's raw GLBs. All reused (their owners' names).
HIDDEN = {'shelfitem09g': ['Gloves'], 'shelfitem09sg': ['SkullCaps', 'Gloves'], 'shelfitem09d': ['Daggers'],
          'shelfitem03f': ['Crystals1', 'Wands1', 'Hourglass1'], 'shelfitem03hc': ['Hourglass1', 'Crystals1'],
          'weaponracknewg3': ['Group3'], 'weaponrackg1': ['Group1'],
          'weaponracknsnewg1': ['Group1'], 'weaponracknsnewg2': ['Group2'], 'weaponracknsnewg3': ['Group3']}
# (prop, hidden pieces lower case, sorted) -> its HidePiece variant
HIDE_OF = {(SOURCES[v], tuple(sorted(x.lower() for x in pieces))): v for v, pieces in HIDDEN.items()}
# HidePiece names that are not pieces of the model (ignored, as MM9 does): ShelfItem05 has Jar01-05 only.
NO_SUCH_PIECE = {'shelfitem05': {'wands1', 'crystals1'}}
# Posed models: (animation, frame) set in build (blib.import_raw) and placements (posed_points).
LIBRARY = {}
POSES = {}
# Reused posed models (built posed by their owners): placed and checked on MM9's pose as POSES are.
PLACE_POSES = {'dwarfaxeonside': ('onside', 1)}
CHECK_POSES = {}
POSE_TURN = {}
SKIN_ORDER = {}
CLASSES = {'Prop', 'CandleProp'}
# Objects of those classes (and the other model-carrying objects of the DAT) that get no decoration: name -> reason.
# The five models the old import found no source for (baked_model_missing_source 5): MM9 ships neither file in
# MODELS.REZ, so MM9 shows nothing there.
SKIPPED = {**{name: 'models\\Props\\GoblinStatue1.abc is not shipped by MM9 (MODELS.REZ): MM9 shows nothing'
              for name in ('Prop57', 'Prop188', 'Prop189')},
           'Prop36': 'models\\PickupItems\\spellbook3.abc is not shipped by MM9 (MODELS.REZ): MM9 shows nothing',
           'Prop6': 'models\\PickupItems\\spellbook1.abc is not shipped by MM9 (MODELS.REZ): MM9 shows nothing'}


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

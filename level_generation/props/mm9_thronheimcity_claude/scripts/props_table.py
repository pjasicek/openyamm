r"""Thronheim City's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
and the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9 props
project are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they are;
the reuse check is work/registry.py over every MM9 props project); the rest are built here. The route is Sturmford
City's (itself Drangheim Prison's and Hall of the Gods': one material per MM9 skin, POSES, the isle's blib build and
finish checks, the Anskram flame cards on the ABCs' Flame socket markers). The `ns` models (FlowerBoxNS, WeaponRackns)
carry MM9's quarter turn (specs.json `turn: 90`, as Dook's Castle's weaponracknew).

Classes placed: Prop, CandleProp (all lit: StartOn 1, Blue 0), DestructableProp (the flower boxes, a bookcase: static
decorations), Barrel, WellMMIX, TreasureChest (loot container 0: kind chest) and RUDEProp (the council's six, posed
by PropAnim.scr `Sit`: static decorations in that pose, hidden until ARG_Unhide.scr shows them; README).

  - The council (RUDEProps) and the Argument cinema's Sven are posed in Blender at their animation's first key
    (POSES): Sven_ARG's `sitting` (its only seated animation; PropAnim's `Sit` is not in the model, so it plays its
    first animation, `sitting`; Sven sits on the ABC's own chair piece, skin 1 ChairPlain), Tryggva, Markel, Forad
    and Sigmund `sit`; Bjarni is Sturmford's bjarnisitting (the same ABC, skin and `sit` pose). MarkeProp0 (Markel
    dead, PropAnim `static_die2`, which NPC239.scr shows) is markeldie2. Their one-triangle `ngon` shadow piece
    (Sigmund's `Sigmond01`) is stripped (HIDDEN).
  - Scroll pose: Prop9 (arguetreaty.scr: LoopAnim Down) and TreatyProp (PropAnim `Down`) lie flat; scroll-open's
    `down` animation is exactly pitch pi/2 of its static model (checked: 0.0 LT), so they are 1000 Terrors' scrollp90
    (POSE_TILT: tilted by their script, not by their Rotation).
  - HidePiece: an object's HidePiece0-4 pieces are stripped from its variant's raw GLBs (HIDDEN): ShelfItem02 without
    Amulets1, SkelBones1, Skull1 (shelfitem02mp: the mortar and the pouches), the two WeaponRackns without Group1 /
    Group3; ShelfItem03 without Crystals1, Wands1, Hourglass1 and ShelfItem09 without SkullCaps+Gloves / Daggers are
    Sturmford's shelfitem03f / shelfitem09sg / shelfitem09d. ShelfItem05's hidden Wands1, Crystals1 are not pieces of
    ShelfItem05.abc (five jars): plain shelfitem05 (IGNORED_HIDES).
  - Tipped: Shield5/2/3 (Shield.ABC, pitch pi/2: the old bake is flat, 10 units high, as Sturmford's shields):
    shield2flat (Sturmford's), shield3flat, shield4flat built here.
  - Burning logs: all three LogsBurning props lie under a Fire (Prop22 under Fire4, Prop5 under Fire2 + Fire3, Prop10
    on the cinema stage under Fire5): the isle's logsburning (its flame cards), as Sturmford's Logs4.
  - Clover (the two four-leaf clover patches, Drangheim City's `clover`): placed since 2026-11-12, so that the map's
    bonus events have something to click (they were left out at first, "not a decoration class").
  - Not placed: the Argument cinema stage under the city (STAGE_Y), whose geometry the native map drops.

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
PROJECT = REPO / 'level_generation/projects/mm9r_thronheimcity'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/thronheimcity.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/thronheimcity.odm'
SCENE = REPO / 'assets_dev/worlds/mm9/maps/thronheimcity.scene.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/pickupitems/quest/kirashield.abc', 'skins/pickupitems/quest/kirashield.dtx'): 'kirashield',
    ('models/props/bench_large1.abc', 'skins/props/bench_large1.dtx'): 'benchlarge1',
    ('models/props/clover.abc', 'skins/props/plantsandtrees/clover.dtx'): 'clover',        # Clover class; Drangheim City's
    ('models/props/coatrack2.abc', 'skins/props/coatrack2.dtx'): 'coatrack2',
    ('models/props/flowerboxew.abc', 'skins/props/flowerboxns.dtx'): 'flowerboxew',
    ('models/props/flowerboxns.abc', 'skins/props/flowerboxns.dtx'): 'flowerboxns',
    ('models/props/herb-rack1.abc', 'skins/props/herb-rack1.dtx'): 'herbrack1',
    ('models/props/lamppost3.abc', 'skins/props/lamppost3.dtx'): 'lamppost3',                 # flame cards
    ('models/props/plate-set2.abc', 'skins/props/plate2.dtx'): 'plateset2',
    ('models/props/pottedplant1.abc', 'skins/props/pottedplant1.dtx'): 'pottedplant1',
    ('models/props/pottedplant2.abc', 'skins/props/pottedplant2.dtx'): 'pottedplant2',
    ('models/props/pottedplant3.abc', 'skins/props/pottedplant3.dtx'): 'pottedplant3',
    ('models/props/shelfitem02.abc', 'skins/props/shelfitem02.dtx'): 'shelfitem02',
    ('models/props/shield.abc', 'skins/props/shield3.dtx'): 'shield3',
    ('models/props/shield.abc', 'skins/props/shield4.dtx'): 'shield4',
    ('models/props/stein_fancy01.abc', 'skins/props/stein_fancy01.dtx'): 'steinfancy01',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitplain.dtx'): 'suitofarmor01plain',
    ('models/props/tapestry-old01.abc', 'textures/leveltextures/misc/banner8.dtx'): 'tapestry_banner8',
    ('models/props/weaponrackns.abc', 'skins/props/weaponrack_new.dtx'): 'weaponracknsnew',     # HidePiece variants
    # creature ABCs, posed (POSES)
    ('models/sven_arg.abc', 'skins/sven.dtx;skins/props/chairplain.dtx'): 'svensitting',
    ('models/tryggva.abc', 'skins/tryggva.dtx'): 'tryggvasit',
    ('models/markel.abc', 'skins/markel.dtx'): 'markelsit',
    ('models/foraddarre.abc', 'skins/foraddarre.dtx'): 'foradsit',
    ('models/sigmund.abc', 'skins/sigmund.dtx'): 'sigmundsit',
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/bjarni.abc', 'skins/bjarni.dtx'): 'bjarnisitting',
    ('models/props/anvil.abc', 'skins/props/anvil.dtx'): 'anvil',
    ('models/props/bag-herbs1.abc', 'skins/pickupitems/quest/bagherbs1.dtx'): 'bagherbs1',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/barstool1.abc', 'skins/props/barstool1.dtx'): 'barstool1',
    ('models/props/bench_large1ns.abc', 'skins/props/bench_large1.dtx'): 'benchlarge1ns',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/bookcase02ns.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ns',
    ('models/props/cabinet02.abc', 'skins/props/cabinet02.dtx'): 'cabinet02',
    ('models/props/cabinet04ns.abc', 'skins/props/cabinet04.dtx'): 'cabinet04ns',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair02.abc', 'skins/props/chair02.dtx'): 'chair02',
    ('models/props/chair03.abc', 'skins/props/chair03.dtx'): 'chair03',
    ('models/props/chandelier2.abc', 'skins/props/chandelier2.dtx'): 'chandelier2',
    ('models/props/chandelier3.abc', 'skins/props/chandelier3.dtx'): 'chandelier3',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    ('models/props/chest5.abc', 'skins/props/chest5.dtx'): 'chest5',
    ('models/props/clawlamp.abc', 'skins/props/clawlamp.dtx'): 'clawlampup',
    ('models/props/coalbin.abc', 'skins/props/coalbin.dtx'): 'coalbin',
    ('models/props/coatrack1.abc', 'skins/props/coatrack1.dtx'): 'coatrack',
    ('models/props/forge.abc', 'skins/props/forge.dtx'): 'forge',
    ('models/props/iron-ingots.abc', 'skins/props/iron-ingots.dtx'): 'ironingots',
    ('models/props/jar01.abc', 'skins/props/pantry-items.dtx'): 'jar01',
    ('models/props/jar02.abc', 'skins/props/pantry-items.dtx'): 'jar02',
    ('models/props/jar03.abc', 'skins/props/pantry-items.dtx'): 'jar03',
    ('models/props/jar04.abc', 'skins/props/pantry-items02.dtx'): 'jar04',
    ('models/props/jar05.abc', 'skins/props/pantry-items02.dtx'): 'jar05',
    ('models/props/jar06.abc', 'skins/props/pantry-items02.dtx'): 'jar06',
    ('models/props/keg_beer.abc', 'skins/props/keg_beer.dtx'): 'kegbeer',
    ('models/props/logsburning.abc', 'skins/props/logsburning.dtx'): 'logsburning',
    ('models/props/pew2.abc', 'skins/props/pew2.dtx'): 'pew2',
    ('models/props/pew2ns.abc', 'skins/props/pew2.dtx'): 'pew2ns',
    ('models/props/pitcher01.abc', 'skins/props/pantry-items.dtx'): 'pitcher01',
    ('models/props/podium01.abc', 'skins/props/podium01.dtx'): 'podium01',
    ('models/props/portal-whole.abc', 'skins/props/portaldirty.dtx'): 'portalwhole',
    ('models/props/sack03.abc', 'skins/props/sack01.dtx'): 'sack03',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/shelfitem01.abc', 'skins/props/shelfitem01.dtx'): 'shelfitem01',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shelfitem05.abc', 'skins/props/shelfitem05.dtx'): 'shelfitem05',
    ('models/props/shelfitem09.abc', 'skins/props/shelfitem09.dtx'): 'shelfitem09',
    ('models/props/shield.abc', 'skins/props/shield2.dtx'): 'shield2',
    ('models/props/smithhammer.abc', 'skins/props/smithhammer.dtx'): 'smithhammer',
    ('models/props/suitofarmor02.abc', 'skins/props/amoredsuitgold.dtx;skins/props/amoredsuithalberd.dtx'):
        'suitofarmor02',
    ('models/props/table01.abc', 'skins/props/table01.dtx'): 'table01',
    ('models/props/table01ns.abc', 'skins/props/table01.dtx'): 'table01ns',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/tableround4.abc', 'skins/props/tableround5.dtx'): 'tableround5',
    ('models/props/tabletrestle.abc', 'skins/props/tabletrestle2.dtx'): 'tabletrestle2',
    ('models/props/training_archery1.abc', 'skins/props/training_archery.dtx'): 'trainingarchery1',
    ('models/props/training_mount.abc', 'skins/props/training_mount.dtx'): 'trainingmount',
    ('models/props/training_spindummy1.abc', 'skins/props/training_spindummy1.dtx'): 'spindummy',
    ('models/props/training_strawdummy2_c.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2c',
    ('models/props/training_strawdummy2_l.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2l',
    ('models/props/training_strawdummy2_r.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2r',
    ('models/props/wallcandle.abc', 'skins/props/wallcandle.dtx'): 'wallcandle',
    ('models/props/well.abc', 'skins/props/well.dtx'): 'well',
}
# The DAT writes Sven's two skins with a space after the ';' (key() strips it).
ALIASES = {}
_OWNERS = {
    'bjarnisitting': 'sturmfordcity', 'anvil': 'drangheimprison', 'bagherbs1': 'tasaracademy',
    'barrel': 'anskramkeep', 'barrel03': 'anskramkeep', 'barstool1': 'sturmfordcity',
    'benchlarge1ns': 'lindisfarnemonastery', 'bookflat': 'templeofhonk', 'bookcase02ew': 'anskramkeep',
    'bookcase02ns': 'anskramkeep', 'cabinet02': 'klusoshouse', 'cabinet04ns': 'drangheimprison',
    'chair': 'anskramkeep', 'chair02': 'anskramkeep', 'chair03': 'lichlab', 'chandelier2': 'sturmfordcity',
    'chandelier3': 'ruinedtemple', 'chest1': 'anskramkeep', 'chest5': 'chasmofthedead', 'clawlampup': 'sturmfordcity',
    'coalbin': 'drangheimprison', 'coatrack': 'isleofashes', 'forge': 'tasaracademy', 'ironingots': 'drangheimprison',
    'jar01': 'beethoven', 'jar02': 'beethoven', 'jar03': 'beethoven', 'jar04': 'beethoven', 'jar05': 'beethoven',
    'jar06': 'beethoven', 'kegbeer': 'sturmfordcity', 'logsburning': 'isleofashes', 'pew2': 'lindisfarnemonastery',
    'pew2ns': 'klusoshouse', 'pitcher01': 'klusoshouse', 'podium01': 'lichlab', 'portalwhole': 'sturmfordcity',
    'sack03': 'drangheimprison', 'scroll': 'anskramkeep', 'scrollp90': '1000terrors', 'shelfitem01': 'lichlab',
    'shelfitem02': 'lichlab', 'shelfitem03': 'lichlab', 'shelfitem05': 'lichlab', 'shelfitem03f': 'sturmfordcity',
    'shelfitem09sg': 'sturmfordcity', 'shelfitem09d': 'sturmfordcity', 'shield2flat': 'sturmfordcity',
    'smithhammer': 'tasaracademy', 'suitofarmor02': 'dookscastle', 'table01': 'lichlab', 'table01ns': 'lichlab',
    'tableround': 'anskramkeep', 'tableround5': 'klusoshouse', 'tabletrestle2': 'klusoshouse',
    'trainingarchery1': 'sturmfordcity', 'trainingmount': 'traininghall', 'spindummy': 'traininghall',
    'strawdummy2c': 'sturmfordcity', 'strawdummy2l': 'sturmfordcity', 'strawdummy2r': 'sturmfordcity',
    'wallcandle': 'klusoshouse', 'well': 'isleofashes', 'clover': 'drangheimcity'}
REUSED = {prop: PROPS_DIR / f'mm9_{owner}_claude' for prop, owner in _OWNERS.items()}
# Objects whose decoration is another prop than their (model, skin)'s: Markel dead (PropAnim static_die2), the two
# scrolls lying flat by their script (POSE_TILT), the HidePiece variants (HIDDEN).
OBJECT_PROP = {'MarkeProp0': 'markeldie2', 'Prop9': 'scrollp90', 'TreatyProp': 'scrollp90',
               'Shelfitems9': 'shelfitem02mp', 'Shelfitems10': 'shelfitem02mp',
               'Weaponrack2': 'weaponracknsnewg1', 'Weaponrack1': 'weaponracknsnewg3',
               'Shelfitems11': 'shelfitem03f', 'Shelfitems24': 'shelfitem03f', 'Shelfitems30': 'shelfitem03f',
               'Shelfitems14': 'shelfitem09sg', 'Shelfitems15': 'shelfitem09d'}
# Objects tilted by their script's pose, not by their Rotation (checked against that pose in placements.py).
POSE_TILT = {'Prop9': 'down', 'TreatyProp': 'down'}
# Variants built here from another prop's source (MODELS id); the reused variants' sources for the checks.
SOURCES = {'markeldie2': 'markelsit', 'shelfitem02mp': 'shelfitem02', 'weaponracknsnewg1': 'weaponracknsnew',
           'weaponracknsnewg3': 'weaponracknsnew', 'shield3flat': 'shield3', 'shield4flat': 'shield4',
           'shield2flat': 'shield2', 'scrollp90': 'scroll', 'shelfitem03f': 'shelfitem03',
           'shelfitem09sg': 'shelfitem09', 'shelfitem09d': 'shelfitem09'}
# Pitch, roll baked in (decorations turn about z only); placements.py tilts the raw points the same way to check them.
TILTS = {'shield2flat': (1.5707964, 0.0), 'shield3flat': (1.5707964, 0.0), 'shield4flat': (1.5707964, 0.0),
         'scrollp90': (1.5707964, 0.0)}
# (prop, pitch, roll in whole degrees) of a tilted object -> its tilted variant.
# 2026-11-07 (prop_audit.py): MM9's pitch pi/2 stands up the shield its first animation lays down: the shields hang
# on the walls as Dook's Castle's shield1/shield2/shield4/shield3r (Thjorgard City's route); the shieldNflat variants
# lie flat and stuck out of the walls like shelves.
TILT_OF = {('shield2', 90, 0): 'shield2', ('shield3', 90, 0): 'shield3r', ('shield4', 90, 0): 'shield4'}
TILTS.update({v: (1.5707964, 3.1415927) for v in ('shield1', 'shield2', 'shield3r', 'shield4')})
SOURCES['shield3r'] = 'shield3'
REUSED.update({v: PROPS_DIR / 'mm9_dookscastle_claude' for v in ('shield1', 'shield2', 'shield3r', 'shield4')})
# HidePiece0-4 of the objects: their pieces stripped from the variant's raw GLBs. The creature ABCs lose their
# one-triangle shadow n-gon.
HIDDEN = {'shelfitem02mp': ['Amulets1', 'SkelBones1', 'Skull1'], 'weaponracknsnewg1': ['Group1'],
          'weaponracknsnewg3': ['Group3'], 'shelfitem03f': ['Crystals1', 'Wands1', 'Hourglass1'],
          'shelfitem09sg': ['SkullCaps', 'Gloves'], 'shelfitem09d': ['Daggers'],
          'svensitting': ['ngon'], 'tryggvasit': ['ngon'], 'markelsit': ['ngon'], 'markeldie2': ['ngon'],
          'foradsit': ['ngon'], 'sigmundsit': ['Sigmond01'], 'bjarnisitting': ['ngon']}
# HidePieces that name no piece of the object's model (ShelfItem05.abc is five jars): nothing to hide.
IGNORED_HIDES = {'shelfitem05': {'wands1', 'crystals1'}}
LIBRARY = {}
# Posed models: (animation, frame) set in build (blib.import_raw) and placements (posed_points).
POSES = {'svensitting': ('sitting', 0), 'tryggvasit': ('sit', 0), 'markelsit': ('sit', 0),
         'markeldie2': ('static_die2', 0), 'foradsit': ('sit', 0), 'sigmundsit': ('sit', 0),
         'bjarnisitting': ('sit', 0)}
PLACE_POSES = {}
CHECK_POSES = {}
POSE_TURN = {}
SKIN_ORDER = {}
CLASSES = {'Prop', 'CandleProp', 'DestructableProp', 'WallTorch', 'Brazier', 'Barrel', 'WellMMIX', 'TreasureChest',
           'RUDEProp', 'Clover'}
# Objects of those classes (and the other model-carrying objects of the DAT) that get no decoration: name -> reason.
SKIPPED = {}
# The Argument cinema stage under the city (DAT y < 900, about the origin: chairs, scroll, book, Sven, the burning logs
# under Fire5, four chandeliers) is not built in the native map (the map agent's decision, 2026-10-31): not placed.
STAGE_Y = 900.0


def on_stage(o):
    return float(o['props']['Pos'][1]) < STAGE_Y


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
    if hidden and hidden != sorted(x.lower() for x in HIDDEN.get(prop, [])):
        raise SystemExit(f"{p['Name']}: {prop} hides {hidden}, its model {HIDDEN.get(prop)}")
    return prop


def placements():
    """(object index, prop id) of every decoration object (not the SKIPPED ones)."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')
            and o['props'].get('Name') not in SKIPPED and not on_stage(o)]


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
    print('not placed, the cinema stage:', [(o['index'], o['props']['Name']) for o in out if o['class'] in CLASSES
                                             and o['props'].get('Filename') and on_stage(o)])


if __name__ == '__main__':
    main()

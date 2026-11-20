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
  - Tipped: Shield0-3 (Shield.ABC, pitch pi/2, yaw pi/2) hang on the armoury wall (their centres 5 units off it, half
    a shield's thickness): Dook's Castle's hung shield1/shield2/shield4/shield3r, point down (TILT_OF, TILTS). Until
    2026-11-02 they took Sturmford's shield1flat/shield2flat and Thronheim's shield3flat/shield4flat, which lie flat:
    Sturmford read the pitch against the old bake, which the old import had baked flat (Dook's Castle README).
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
PROJECT = REPO / 'level_generation/projects/mm9r_thjorgardcity'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/thjorgardcity.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/thjorgardcity.odm'
SCENE = REPO / 'assets_dev/worlds/mm9/maps/thjorgardcity.scene.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/props/basket01.abc', 'skins/props/basket01.dtx'): 'basket01',
    ('models/pickupitems/quest/bookkey.abc', 'skins/pickupitems/quest/greatbookreal.dtx'): 'bookkey',
    ('models/props/desk02ns.abc', 'skins/props/desk02.dtx'): 'desk02ns',
    ('models/props/herb-rack2.abc', 'skins/props/herb-rack1.dtx'): 'herbrack2',
    ('models/props/lamppost2.abc', 'skins/props/lamppost1.dtx'): 'lamppost2',                 # flame card
    ('models/props/lantern2.abc', 'skins/props/lantern1.dtx'): 'lantern2',                    # flame card
    ('models/props/plate-set1.abc', 'skins/props/plate2.dtx'): 'plateset1',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitgold.dtx'): 'suitofarmor01gold',
    ('models/props/weaponscabinet03.abc', 'skins/props/weaponscabinet06.dtx'): 'weaponscabinet03',
    # reused: built by other MM9 props projects (same ABC model and skin); Thronheim City and Drangheim City built
    # these the same afternoon
    ('models/props/barstool2.abc', 'skins/props/barstool1.dtx'): 'barstool2',
    ('models/props/clover.abc', 'skins/props/plantsandtrees/clover.dtx'): 'clover',
    ('models/props/jug1.abc', 'skins/props/jug1.dtx'): 'jug1',
    ('models/props/shelfitem09.abc', 'skins/props/shelfitem09.dtx'): 'shelfitem09',
    ('models/props/winebottle02.abc', 'skins/props/winebottle02.dtx'): 'winebottle02',
    ('models/props/winebottle03.abc', 'skins/props/winebottle03.dtx'): 'winebottle03',
    ('models/props/winebottle05.abc', 'skins/props/pantry-items02.dtx'): 'winebottle05',
    ('models/props/coatrack2.abc', 'skins/props/coatrack2.dtx'): 'coatrack2',
    ('models/props/herb-rack1.abc', 'skins/props/herb-rack1.dtx'): 'herbrack1',
    ('models/props/plate-set2.abc', 'skins/props/plate2.dtx'): 'plateset2',
    ('models/props/stein_fancy01.abc', 'skins/props/stein_fancy01.dtx'): 'steinfancy01',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitplain.dtx'): 'suitofarmor01plain',
    ('models/modelprops/dwarfaxe.abc', 'skins/modelprops/dwarfaxe.dtx'): 'dwarfaxeonside',
    ('models/pickupitems/scroll.abc', 'skins/props/scrolldouble.dtx'): 'scrollpickup',
    ('models/props/anvil.abc', 'skins/props/anvil.dtx'): 'anvil',
    ('models/props/bag-herbs1.abc', 'skins/pickupitems/quest/bagherbs1.dtx'): 'bagherbs1',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/basket_fruit.abc', 'skins/props/basket_fruit.dtx'): 'basketfruit',
    ('models/props/basket_veggies.abc', 'skins/props/basket_veggies.dtx'): 'basketveggies',
    ('models/props/beaker01.abc', 'skins/props/beaker01.dtx'): 'beaker01',
    ('models/props/bed.abc', 'skins/props/bed.dtx'): 'bed',
    ('models/props/bed_ornate.abc', 'skins/props/bed_ornate.dtx'): 'bedornate',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/bookcase02ns.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ns',
    ('models/props/bookstack01.abc', 'skins/props/bookstack01.dtx'): 'bookstack01',
    ('models/props/bucket01.abc', 'skins/props/bucket01.dtx'): 'bucket01',
    ('models/props/burner.abc', 'skins/props/burner.dtx'): 'burner',
    ('models/props/cabinet01.abc', 'skins/props/cabinet01.dtx'): 'cabinet01',
    ('models/props/cabinet01ns.abc', 'skins/props/cabinet01.dtx'): 'cabinet01ns',
    ('models/props/cabinet02.abc', 'skins/props/cabinet02.dtx'): 'cabinet02',
    ('models/props/cabinet02ns.abc', 'skins/props/cabinet02.dtx'): 'cabinet02ns',
    ('models/props/cabinet03.abc', 'skins/props/cabinet03.dtx'): 'cabinet03',
    ('models/props/cabinet04.abc', 'skins/props/cabinet04.dtx'): 'cabinet04',
    ('models/props/cabinet04ns.abc', 'skins/props/cabinet04.dtx'): 'cabinet04ns',
    ('models/props/cabinet05.abc', 'skins/props/cabinet05.dtx'): 'cabinet05',
    ('models/props/cabinet05ns.abc', 'skins/props/cabinet05.dtx'): 'cabinet05ns',
    ('models/props/candelabra.abc', 'skins/props/candelabra.dtx'): 'candelabra',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair02.abc', 'skins/props/chair02.dtx'): 'chair02',
    ('models/props/chair03.abc', 'skins/props/chair03.dtx'): 'chair03',
    ('models/props/chair_fordesk02.abc', 'skins/props/chair_fordesk02.dtx'): 'chairdesk02',
    ('models/props/chandelier2.abc', 'skins/props/chandelier2.dtx'): 'chandelier2',
    ('models/props/chandelier3.abc', 'skins/props/chandelier3.dtx'): 'chandelier3',
    ('models/props/clawlamp.abc', 'skins/props/clawlamp.dtx'): 'clawlampup',
    ('models/props/coalbin.abc', 'skins/props/coalbin.dtx'): 'coalbin',
    ('models/props/coatrack1.abc', 'skins/props/coatrack1.dtx'): 'coatrack',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/desk01.abc', 'skins/props/desk01.dtx'): 'desk01',
    ('models/props/desk01ns.abc', 'skins/props/desk01.dtx'): 'desk01ns',
    ('models/props/dresser.abc', 'skins/props/dresserfancy.dtx'): 'dresserfancy',
    ('models/props/dresserns.abc', 'skins/props/dresserfancy.dtx'): 'dresserfancyns',
    ('models/props/forge.abc', 'skins/props/forge.dtx'): 'forge',
    ('models/props/iron-ingots.abc', 'skins/props/iron-ingots.dtx'): 'ironingots',
    ('models/props/keg_beer.abc', 'skins/props/keg_beer.dtx'): 'kegbeer',
    ('models/props/logsburning.abc', 'skins/props/logsburning.dtx'): 'logs',
    ('models/props/oillamp.abc', 'skins/props/oillamp.dtx'): 'oillamp',
    ('models/props/pew2.abc', 'skins/props/pew2.dtx'): 'pew2',
    ('models/props/pew2ns.abc', 'skins/props/pew2.dtx'): 'pew2ns',
    ('models/props/pitcher01.abc', 'skins/props/pantry-items.dtx'): 'pitcher01',
    ('models/props/plate-stack1.abc', 'skins/props/plate2.dtx'): 'platestack1',
    ('models/props/plate-stack2.abc', 'skins/props/plate2.dtx'): 'platestack2',
    ('models/props/podium01.abc', 'skins/props/podium01.dtx'): 'podium01',
    ('models/props/portal-whole.abc', 'skins/props/portaldirty.dtx'): 'portalwhole',
    ('models/props/ropecoil.abc', 'skins/props/ropecoil.dtx'): 'ropecoil',
    ('models/props/sack01.abc', 'skins/props/sack01.dtx'): 'sack01',
    ('models/props/sack02.abc', 'skins/props/sack01.dtx'): 'sack02',
    ('models/props/sack03.abc', 'skins/props/sack01.dtx'): 'sack03',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/shelfitem01.abc', 'skins/props/shelfitem01.dtx'): 'shelfitem01',
    ('models/props/shelfitem02.abc', 'skins/props/shelfitem02.dtx'): 'shelfitem02',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shelfitem05.abc', 'skins/props/shelfitem05.dtx'): 'shelfitem05',
    ('models/props/shelfitem06.abc', 'skins/props/shelfitem06.dtx'): 'shelfitem06',
    ('models/props/shelfitem07.abc', 'skins/props/shelfitem07.dtx'): 'shelfitem07',
    ('models/props/shelfitem08.abc', 'skins/props/shelfitem08.dtx'): 'shelfitem08',
    ('models/props/shield.abc', 'skins/props/shield.dtx'): 'shield1',
    ('models/props/shield.abc', 'skins/props/shield2.dtx'): 'shield2',
    ('models/props/shield.abc', 'skins/props/shield3.dtx'): 'shield3',
    ('models/props/shield.abc', 'skins/props/shield4.dtx'): 'shield4',
    ('models/props/smithhammer.abc', 'skins/props/smithhammer.dtx'): 'smithhammer',
    ('models/props/stove.abc', 'skins/props/stove.dtx'): 'stove',
    ('models/props/stovens.abc', 'skins/props/stove.dtx'): 'stovens',
    ('models/props/suitofarmor02.abc', 'skins/props/amoredsuitgold.dtx;skins/props/amoredsuithalberd.dtx'):
        'suitofarmor02',
    ('models/props/table01.abc', 'skins/props/table01.dtx'): 'table01',
    ('models/props/table01ns.abc', 'skins/props/table01.dtx'): 'table01ns',
    ('models/props/table02.abc', 'skins/props/table01.dtx'): 'table02',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/tapestry-old01.abc', 'textures/leveltextures/misc/banner6.dtx'): 'tapestry_banner6',
    ('models/props/throne.abc', 'skins/props/throne.dtx'): 'throne',
    ('models/props/torch2.abc', 'textures/leveltextures/misc/refinerysolidrusta.dtx'): 'torchrust',
    ('models/props/training_archery1.abc', 'skins/props/training_archery.dtx'): 'trainingarchery1',
    ('models/props/training_mount.abc', 'skins/props/training_mount.dtx'): 'trainingmount',
    ('models/props/training_spindummy1.abc', 'skins/props/training_spindummy1.dtx'): 'spindummy',
    ('models/props/training_strawdummy2_c.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2c',
    ('models/props/training_strawdummy2_l.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2l',
    ('models/props/training_strawdummy2_r.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2r',
    ('models/props/wallcandle.abc', 'skins/props/wallcandle.dtx'): 'wallcandle',
    ('models/props/washtub_table.abc', 'skins/props/washtub_table.dtx'): 'washtubtable',
    ('models/props/weaponrackns.abc', 'skins/props/weaponrack_new.dtx'): 'weaponracknew',
    ('models/props/weaponscabinet01.abc', 'skins/props/weaponscabinet04.dtx'): 'weaponscabinet04',
    ('models/props/well.abc', 'skins/props/well.dtx'): 'well',
    ('models/props/winebottle01.abc', 'skins/props/winebottle01.dtx'): 'winebottle',
    ('models/props/winebottle04.abc', 'skins/props/pantry-items.dtx'): 'winebottle04',
    ('models/props/winerack.abc', 'skins/props/winerack.dtx'): 'winerack',
    ('models/props/woodbin.abc', 'skins/props/woodbin.dtx'): 'woodbin',
}
ALIASES = {}
_OWNERS = {
    'dwarfaxeonside': 'tasaracademy', 'scrollpickup': 'tasaracademy', 'anvil': 'drangheimprison',
    'bagherbs1': 'tasaracademy', 'barrel': 'anskramkeep', 'basketfruit': 'klusoshouse', 'basketveggies': 'klusoshouse',
    'beaker01': 'lichlab', 'bed': 'anskramkeep', 'bedornate': 'dookscastle', 'bedmedium': 'anskramkeep',
    'bookflat': 'templeofhonk', 'bookcase02ew': 'anskramkeep', 'bookcase02ns': 'anskramkeep',
    'bookstack01': 'lichlab', 'bucket01': 'drangheimprison', 'burner': 'lichlab', 'cabinet01': 'klusoshouse',
    'cabinet01ns': 'templeofhonk', 'cabinet02': 'klusoshouse', 'cabinet02ns': 'klusoshouse', 'cabinet03': 'klusoshouse',
    'cabinet04': 'templeofhonk', 'cabinet04ns': 'drangheimprison', 'cabinet05': 'klusoshouse',
    'cabinet05ns': 'drangheimprison', 'candelabra': 'sturmfordcity', 'chair': 'anskramkeep', 'chair02': 'anskramkeep',
    'chair03': 'lichlab', 'chairdesk02': 'drangheimprison', 'chandelier2': 'sturmfordcity',
    'chandelier3': 'ruinedtemple', 'clawlampup': 'sturmfordcity', 'coalbin': 'drangheimprison',
    'coatrack': 'isleofashes', 'crate': 'anskramkeep', 'desk01': 'anskramkeep', 'desk01ns': 'anskramkeep',
    'dresserfancy': 'klusoshouse', 'dresserfancyns': 'klusoshouse', 'forge': 'tasaracademy',
    'ironingots': 'drangheimprison', 'kegbeer': 'sturmfordcity', 'logs': 'lichlab', 'oillamp': 'thjoradmine',
    'pew2': 'lindisfarnemonastery', 'pew2ns': 'klusoshouse', 'pitcher01': 'klusoshouse', 'platestack1': 'klusoshouse',
    'platestack2': 'klusoshouse', 'podium01': 'lichlab', 'portalwhole': 'sturmfordcity', 'ropecoil': 'drangheimprison',
    'sack01': 'connectingtunnels', 'sack02': 'connectingtunnels', 'sack03': 'drangheimprison', 'scroll': 'anskramkeep',
    'scrollp90': '1000terrors',
    'shelfitem01': 'lichlab', 'shelfitem02': 'lichlab', 'shelfitem03': 'lichlab', 'shelfitem05': 'lichlab',
    'shelfitem06': 'drangheimprison', 'shelfitem07': 'drangheimprison', 'shelfitem08': 'drangheimprison',
    'shelfitem03f': 'sturmfordcity', 'shelfitem09d': 'sturmfordcity', 'shelfitem09sg': 'sturmfordcity',
    'shield1': 'dookscastle', 'shield2': 'dookscastle', 'shield3': 'klusoshouse', 'shield4': 'dookscastle',
    'shield3r': 'dookscastle', 'smithhammer': 'tasaracademy',
    'stove': 'drangheimprison', 'stovens': 'klusoshouse', 'suitofarmor02': 'dookscastle', 'table01': 'lichlab',
    'table01ns': 'lichlab', 'table02': 'templeofhonk', 'tableround': 'anskramkeep', 'tapestry_banner6': 'thearena',
    'throne': 'lichlab', 'torchrust': 'thearena', 'trainingarchery1': 'sturmfordcity', 'trainingmount': 'traininghall',
    'spindummy': 'traininghall', 'strawdummy2c': 'sturmfordcity', 'strawdummy2l': 'sturmfordcity',
    'strawdummy2r': 'sturmfordcity', 'wallcandle': 'klusoshouse', 'washtubtable': 'lindisfarnemonastery',
    'weaponracknew': 'dookscastle', 'weaponscabinet04': 'anskramkeep', 'well': 'isleofashes',
    'winebottle': 'beethoven', 'winebottle04': 'sturmfordcity', 'winerack': 'sturmfordcity', 'woodbin': 'thjoradmine',
    # Thronheim City's (installed 18:24-18:29, while this project was building the same models: theirs are kept)
    'coatrack2': 'thronheimcity', 'herbrack1': 'thronheimcity', 'plateset2': 'thronheimcity',
    'steinfancy01': 'thronheimcity', 'suitofarmor01plain': 'thronheimcity',
    'shelfitem02mp': 'thronheimcity', 'weaponracknsnewg1': 'thronheimcity',
    'weaponracknsnewg3': 'thronheimcity',
    # Drangheim City's (installed 18:34)
    'barstool2': 'drangheimcity', 'clover': 'drangheimcity', 'jug1': 'drangheimcity', 'shelfitem09': 'drangheimcity',
    'shelfitem09g': 'drangheimcity', 'shelfitem03hc': 'drangheimcity', 'winebottle02': 'drangheimcity',
    'winebottle03': 'drangheimcity', 'winebottle05': 'drangheimcity'}
REUSED = {prop: PROPS_DIR / f'mm9_{owner}_claude' for prop, owner in _OWNERS.items()}
# Objects whose decoration is another prop than their (model, skin)'s: the BedMedium beds in MM9's EW pose
# (PropAnim.scr "ew"), the blue claw lamp.
OBJECT_PROP = {**{name: 'bedmediumew' for name in ('Bed3', 'Bed18', 'Bed19', 'Bed20')},
               'Clawlamp0': 'clawlampupblue'}
# Variants built here from another prop's source (MODELS id).
SOURCES = {'chandelier3orange': 'chandelier3', 'bedmediumew': 'bedmedium', 'clawlampupblue': 'clawlampup',
           'shield3r': 'shield3', 'scrollp90': 'scroll', 'shelfitem09g': 'shelfitem09', 'shelfitem03hc': 'shelfitem03',
           'weaponracknsnewg1': 'weaponracknew', 'weaponracknsnewg2': 'weaponracknew',
           'weaponracknsnewg3': 'weaponracknew', 'shelfitem02mp': 'shelfitem02', 'shelfitem03hwc': 'shelfitem03',
           'shelfitem07hfruit': 'shelfitem07', 'shelfitem07hpie': 'shelfitem07', 'shelfitem07hbread': 'shelfitem07',
           'shelfitem08hbasket': 'shelfitem08', 'shelfitem08hbottle': 'shelfitem08', 'shelfitem08hsack': 'shelfitem08',
           'shelfitem08honions': 'shelfitem08',
           # Sturmford's variants (reused), for the placements' raw sources
           'shelfitem09sg': 'shelfitem09',
           'shelfitem09d': 'shelfitem09', 'shelfitem03f': 'shelfitem03'}
# Pitch, roll baked in (decorations turn about z only); placements.py tilts the raw points the same way to check them.
TILTS = {'shield1': (1.5707964, 3.1415927), 'shield2': (1.5707964, 3.1415927), 'shield3r': (1.5707964, 3.1415927),
         'shield4': (1.5707964, 3.1415927), 'scrollp90': (1.5707964, 0.0)}
# An upright model that MoveToFloor sets down on a table or a floor, away from a wall -> the same model lying flat
# (2026-11-02, the play-test: a letter stood upright on a counter). Scroll-open stands (Anskram Keep hangs it on walls)
# and MM9 lays it down only by PropAnim's `down` (Thronheim's TreatyProp); a BookLetter letter on a counter keeps
# standing in MM9, which reads as a placard. One pinned at a wall stays upright (placements.WALL_HUNG_REACH).
LAID_FLAT = {'scroll': 'scrollp90'}
# (prop, pitch, roll in whole degrees) of a tilted object -> its tilted variant (Yanmir's Fort's route).
TILT_OF = {('shield1', 90, 0): 'shield1', ('shield2', 90, 0): 'shield2', ('shield3', 90, 0): 'shield3r',
           ('shield4', 90, 0): 'shield4'}
# HidePiece0-4 of the objects: their pieces stripped from the variant's raw GLBs (convert_all.strip). The variants built
# here are named h<hidden>: the pieces they hide; the reused keep their owners' names (Sturmford's shelfitem09sg,
# shelfitem09d, shelfitem03f; Thronheim's shelfitem02mp and weaponracknsnewg1/g3, whose scheme weaponracknsnewg2 follows;
# Drangheim City's shelfitem09g, shelfitem03hc).
HIDDEN = {'shelfitem09g': ['Gloves'], 'shelfitem09sg': ['SkullCaps', 'Gloves'], 'shelfitem09d': ['Daggers'],
          'shelfitem03f': ['Crystals1', 'Wands1', 'Hourglass1'], 'shelfitem03hwc': ['Wands1', 'Crystals1'],
          'shelfitem03hc': ['Hourglass1', 'Crystals1'], 'shelfitem02mp': ['Amulets1', 'SkelBones1', 'Skull1'],
          'shelfitem07hfruit': ['Fruit1'], 'shelfitem07hpie': ['Pie1'], 'shelfitem07hbread': ['Bread1'],
          'shelfitem08hbasket': ['Basket'], 'shelfitem08hbottle': ['Bottle'], 'shelfitem08hsack': ['Sack'],
          'shelfitem08honions': ['Onions'],
          'weaponracknsnewg1': ['Group1'], 'weaponracknsnewg2': ['Group2'], 'weaponracknsnewg3': ['Group3']}
# (prop, hidden pieces lower case, sorted) -> its HidePiece variant
HIDE_OF = {(SOURCES[v], tuple(sorted(x.lower() for x in pieces))): v for v, pieces in HIDDEN.items()}
# HidePiece names that are not pieces of the model (ignored, as MM9 does): ShelfItem05 has Jar01-05 only.
NO_SUCH_PIECE = {'shelfitem05': {'wands1', 'crystals1'}}
# Posed models: (animation, frame) set in build (blib.import_raw) and placements (posed_points).
LIBRARY = {}
POSES = {'bedmediumew': ('EW', 0)}
# Reused posed models (built posed by their owners): placed and checked on MM9's pose as POSES are.
PLACE_POSES = {'dwarfaxeonside': ('onside', 1)}
CHECK_POSES = {}
POSE_TURN = {}
SKIN_ORDER = {}
CLASSES = {'Prop', 'CandleProp', 'Torch', 'DestructableProp', 'Clover', 'WellMMIX'}
# Objects of those classes (and the other model-carrying objects of the DAT) that get no decoration: name -> reason.
SKIPPED = {}


def key(path):
    return ';'.join(part.replace('\\', '/').lower().strip() for part in (path or '').split(';'))


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


_AT_WALL = {}


def at_wall(p):
    """Whether a MoveToFloor object's DAT position is pinned at a wall, well over its floor (placements' wall rule)."""
    if p['Name'] not in _AT_WALL:
        import importlib.util
        import numpy as np
        # this project's placements.py by path (another project's scripts folder may come first on sys.path)
        spec = importlib.util.spec_from_file_location('thjorgard_placements', Path(__file__).with_name('placements.py'))
        placements = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(placements)
        bmodels = _AT_WALL.setdefault(None, placements.load_map())
        point = np.array([p['Pos'][0], p['Pos'][2], p['Pos'][1]]) * 2.56
        floor = placements.floor_below(bmodels, point + np.array([0, 0, 4]))
        _AT_WALL[p['Name']] = floor is not None and point[2] - floor >= placements.WALL_HUNG_HEIGHT \
            and placements.wall_distance(bmodels, point, placements.WALL_HUNG_REACH) is not None
    return _AT_WALL[p['Name']]


def tilt_degrees(p):
    r = p.get('Rotation') or [0, 0, 0]
    return int(round(math.degrees(float(r[0])))) % 360, int(round(math.degrees(float(r[2])))) % 360


def object_prop(o):
    p = o['props']
    pair = (key(p['Filename']), key(p.get('Skin')))
    prop = OBJECT_PROP.get(p.get('Name')) or MODELS[ALIASES.get(pair, pair)]
    # The Ruined Temple's chandelier3 (reused) burns blue, as all its CandleProps are Blue 1; a city's CandleProp
    # without Blue takes the same model with the orange flame (2026-11-01: work/mm9_deco_chandelier3orange.glb, the
    # Ruined Temple GLB with this project's flame02 image; raw files and binding origin copied from its owner).
    if prop == 'chandelier3' and o['class'] == 'CandleProp' and not p.get('Blue'):
        prop = 'chandelier3orange'
    if source_prop(prop) not in MODELS.values() and prop not in REUSED:
        raise SystemExit(f"{p['Name']}: {prop} has no source")
    tilt = tilt_degrees(p)
    if prop in LAID_FLAT and tilt == (0, 0) and p.get('MoveToFloor') and not at_wall(p):
        return LAID_FLAT[prop]
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

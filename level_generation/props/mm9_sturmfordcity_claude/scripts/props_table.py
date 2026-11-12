r"""Sturmford City's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
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
PROJECT = REPO / 'level_generation/projects/mm9r_sturmfordcity'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/sturmfordcity.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/sturmfordcity.odm'
SCENE = REPO / 'assets_dev/worlds/mm9/maps/sturmfordcity.scene.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # the clover patches (Clover class, placed since 2026-11-12: the map's bonus events need something to click);
    # built by Drangheim City
    ('models/props/clover.abc', 'skins/props/plantsandtrees/clover.dtx'): 'clover',
    # built here
    ('models/props/barrel-beet.abc', 'skins/props/barrel.dtx'): 'barrelbeet',
    ('models/props/barstool1.abc', 'skins/props/barstool1.dtx'): 'barstool1',
    ('models/props/bedmedium.abc', 'skins/props/bedplain.dtx'): 'bedmediumplain',
    ('models/props/beet-rack.abc', 'skins/props/beet-rack.dtx'): 'beetrack',
    ('models/props/bowl04.abc', 'skins/props/pantry-items02.dtx'): 'bowl04',
    ('models/props/broom.abc', 'skins/props/broom.dtx'): 'broom',
    ('models/props/candelabra.abc', 'skins/props/candelabra.dtx'): 'candelabra',              # flame cards x3
    ('models/props/chair.abc', 'skins/props/chair1.dtx'): 'chairskin1',     # the Chasm's chair1 is CHAIR1.ABC
    ('models/props/chandelier2.abc', 'skins/props/chandelier2.dtx'): 'chandelier2',           # flame cards x8
    ('models/props/clawlamp.abc', 'skins/props/clawlamp.dtx'): 'clawlampup',     # Yanmir's clawlampp180 upright
    ('models/props/cup02.abc', 'skins/props/pantry-items.dtx'): 'cup02',
    ('models/props/dragontrophy.abc', 'skins/props/dragontrophy.dtx'): 'dragontrophy',
    ('models/props/jacobsladder.abc', 'skins/props/jacobsladder.dtx'): 'jacobsladder',
    ('models/props/keg_beer.abc', 'skins/props/keg_beer.dtx'): 'kegbeer',
    ('models/props/lamppost4.abc', 'skins/props/lamppost3.dtx'): 'lamppost4',                 # flame cards
    ('models/props/lantern_wall1.abc', 'skins/props/lantern_wall1.dtx'): 'lanternwall1',      # flame cards
    ('models/props/mug1.abc', 'skins/props/mug1.dtx'): 'mug1',
    ('models/props/pewns.abc', 'skins/props/pew.dtx'): 'pewns',
    ('models/props/portal-whole.abc', 'skins/props/portaldirty.dtx'): 'portalwhole',
    # TownPortal.scr's cleansed altar (SetModelFilenames Portal-Whole.ABC PortalClean.dtx): no DAT object places it;
    # the city scripts swap mm9_portalwhole to it with evt.SetSprite (EXTRA_BUILT)
    ('models/props/portal-whole.abc', 'skins/props/portalclean.dtx'): 'portalclean',
    ('models/props/sack01.abc', 'skins/props/sack-beet.dtx'): 'sack01beet',
    ('models/props/shelfitem09.abc', 'skins/props/shelfitem09.dtx'): 'shelfitem09',
    ('models/props/shield_rusty.abc', 'skins/props/shield-rusty.dtx'): 'shieldrusty',
    ('models/props/training_archery1.abc', 'skins/props/training_archery.dtx'): 'trainingarchery1',
    ('models/props/training_strawdummy2_c.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2c',
    ('models/props/training_strawdummy2_l.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2l',
    ('models/props/training_strawdummy2_r.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy2r',
    ('models/props/vials.abc', 'skins/props/vials.dtx'): 'vials',
    ('models/props/winebottle04.abc', 'skins/props/pantry-items.dtx'): 'winebottle04',
    ('models/props/winerack.abc', 'skins/props/winerack.dtx'): 'winerack',
    # creature ABCs, posed (POSES)
    ('models/peasantm2.abc', 'skins/peasantm2c.dtx'): 'peasantm2c',
    ('models/peasantms2.abc', 'skins/peasantm2b.dtx'): 'peasantms2b',
    ('models/peasantms2.abc', 'skins/peasantm2c.dtx'): 'peasantms2c',
    ('models/peasantms2.abc', 'skins/peasantm2d.dtx'): 'peasantms2d',
    ('models/bjarni.abc', 'skins/bjarni.dtx'): 'bjarnisitting',
    ('models/props/ercc.abc', 'skins/peasantm2a.dtx;skins/props/cup1.dtx'): 'erccsitting',
    ('models/cat.abc', 'skins/cat.dtx'): 'catstanddown',
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/pickupitems/scroll.abc', 'skins/props/scrolldouble.dtx'): 'scrollpickup',
    ('models/pickupitems/treasurebag.abc', 'skins/pickupitems/bag1.dtx'): 'treasurebag',
    ('models/props/anvil.abc', 'skins/props/anvil.dtx'): 'anvil',
    ('models/props/barrel.abc', 'skins/props/barrel.dtx'): 'barrel',
    ('models/props/basket_fruit.abc', 'skins/props/basket_fruit.dtx'): 'basketfruit',
    ('models/props/basket_veggies.abc', 'skins/props/basket_veggies.dtx'): 'basketveggies',
    ('models/props/beaker01.abc', 'skins/props/beaker01.dtx'): 'beaker01',
    ('models/props/bed.abc', 'skins/props/bed.dtx'): 'bed',
    ('models/props/bed_ornate.abc', 'skins/props/bed_ornate.dtx'): 'bedornate',
    ('models/props/bed_wall.abc', 'skins/props/bed_wall.dtx'): 'bedwall',
    ('models/props/bedmedium.abc', 'skins/props/bedmedium.dtx'): 'bedmedium',
    ('models/props/bench_stone01.abc', 'skins/props/bench_stone.dtx'): 'benchstone01',
    ('models/props/bench_stone02.abc', 'skins/props/bench_stone.dtx'): 'benchstone02',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',
    ('models/props/bookcase01ew.abc', 'skins/props/bookcase01.dtx'): 'bookcase01ew',
    ('models/props/bookcase01ns.abc', 'skins/props/bookcase01.dtx'): 'bookcase01ns',
    ('models/props/bookcase02ew.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ew',
    ('models/props/bookcase02ns.abc', 'skins/props/bookcase02.dtx'): 'bookcase02ns',
    ('models/props/brazier.abc', 'skins/props/brazier.dtx'): 'brazier',
    ('models/props/bucket01.abc', 'skins/props/bucket01.dtx'): 'bucket01',
    ('models/props/bucket02.abc', 'skins/props/bucket02.dtx'): 'bucket02',
    ('models/props/burner.abc', 'skins/props/burner.dtx'): 'burner',
    ('models/props/cabinet02.abc', 'skins/props/cabinet02.dtx'): 'cabinet02',
    ('models/props/cabinet02ns.abc', 'skins/props/cabinet02.dtx'): 'cabinet02ns',
    ('models/props/cabinet04ns.abc', 'skins/props/cabinet04.dtx'): 'cabinet04ns',
    ('models/props/cabinet05.abc', 'skins/props/cabinet05.dtx'): 'cabinet05',
    ('models/props/cabinet05ns.abc', 'skins/props/cabinet05.dtx'): 'cabinet05ns',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair02.abc', 'skins/props/chair02.dtx'): 'chair02',
    ('models/props/chair03.abc', 'skins/props/chair03.dtx'): 'chair03',
    ('models/props/chair_fordesk01.abc', 'skins/props/chair_fordesk01.dtx'): 'chairdesk01',
    ('models/props/chair_fordesk03.abc', 'skins/props/chair_fordesk03.dtx'): 'chairdesk03',
    ('models/props/chandelier.abc', 'skins/props/chandelier.dtx'): 'chandelier',
    ('models/props/chandelier3.abc', 'skins/props/chandelier3.dtx'): 'chandelier3',
    ('models/props/chest1.abc', 'skins/props/chest1.dtx'): 'chest1',
    ('models/props/coalbin.abc', 'skins/props/coalbin.dtx'): 'coalbin',
    ('models/props/coatrack1.abc', 'skins/props/coatrack1.dtx'): 'coatrack',
    ('models/props/crate.abc', 'skins/props/crate.dtx'): 'crate',
    ('models/props/desk01.abc', 'skins/props/desk01.dtx'): 'desk01',
    ('models/props/desk01ns.abc', 'skins/props/desk01.dtx'): 'desk01ns',
    ('models/props/desk03.abc', 'skins/props/desk03.dtx'): 'desk03',
    ('models/props/dresser.abc', 'skins/props/dresserplain.dtx'): 'dresser',
    ('models/props/dresserns.abc', 'skins/props/dresserplain.dtx'): 'dresserns',
    ('models/props/forge.abc', 'skins/props/forge.dtx'): 'forge',
    ('models/props/hangingbrazierbowl.abc', 'skins/props/hangingbrazierbowl.dtx'): 'hangingbowl1',
    ('models/props/iron-ingots.abc', 'skins/props/iron-ingots.dtx'): 'ironingots',
    ('models/props/logsburning.abc', 'skins/props/logsburning.dtx'): 'logs',
    ('models/props/oillamp.abc', 'skins/props/oillamp.dtx'): 'oillamp',
    ('models/props/pew2ns.abc', 'skins/props/pew2.dtx'): 'pew2ns',
    ('models/props/pillarstand.abc', 'skins/props/pillarstand.dtx'): 'pillarstand',
    ('models/props/pitcher01.abc', 'skins/props/pantry-items.dtx'): 'pitcher01',
    ('models/props/plantsandtrees/bush03.abc', 'skins/props/plantsandtrees/bush03.dtx'): 'bush03',
    ('models/props/podium01.abc', 'skins/props/podium01.dtx'): 'podium01',
    ('models/props/sack02.abc', 'skins/props/sack01.dtx'): 'sack02',
    ('models/props/sack03.abc', 'skins/props/sack01.dtx'): 'sack03',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/shelfitem01.abc', 'skins/props/shelfitem01.dtx'): 'shelfitem01',
    ('models/props/shelfitem02.abc', 'skins/props/shelfitem02.dtx'): 'shelfitem02',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shield.abc', 'skins/props/shield.dtx'): 'shield1',
    ('models/props/shield.abc', 'skins/props/shield2.dtx'): 'shield2',
    ('models/props/smithhammer.abc', 'skins/props/smithhammer.dtx'): 'smithhammer',
    ('models/props/stove.abc', 'skins/props/stove.dtx'): 'stove',
    ('models/props/suitofarmor01.abc', 'skins/props/amoredsuitaged.dtx'): 'suitofarmor01',
    ('models/props/table01ns.abc', 'skins/props/table01.dtx'): 'table01ns',
    ('models/props/table02.abc', 'skins/props/table01.dtx'): 'table02',
    ('models/props/table_bench.abc', 'skins/props/table_bench.dtx'): 'tablebench2',
    ('models/props/tableround.abc', 'skins/props/tableround.dtx'): 'tableround',
    ('models/props/tableround2.abc', 'skins/props/tableround2.dtx'): 'tableround2',
    ('models/props/throne.abc', 'skins/props/throne.dtx'): 'throne',
    ('models/props/training_mount.abc', 'skins/props/training_mount.dtx'): 'trainingmount',
    ('models/props/training_spindummy1.abc', 'skins/props/training_spindummy1.dtx'): 'spindummy',
    ('models/props/training_strawdummy1.abc', 'skins/props/training_strawdummy1.dtx'): 'strawdummy',
    ('models/props/plantsandtrees/tree04.abc',
     'skins/props/plantsandtrees/treebark2.dtx;skins/props/plantsandtrees/treebranch3.dtx'): 'tree04',
    ('models/props/wallcandle.abc', 'skins/props/wallcandle.dtx'): 'wallcandle',
    ('models/props/walltorch.abc', 'skins/props/walltorch.dtx'): 'walltorch',
    ('models/props/weaponrack.abc', 'skins/props/weaponrack_new.dtx'): 'weaponrack_new',
    ('models/props/woodbin.abc', 'skins/props/woodbin.dtx'): 'woodbin',
}
# DAT model/skin pairs shown with another pair of the table: candelabra's second skin is not shipped and binds no
# material; tree04's third skin (the leaf pile) binds none (the ABC has materials 0 and 1, Lindisfarne's tree04).
ALIASES = {('models/props/candelabra.abc', 'skins/props/candelabra.dtx;skins/props/candel.dtx'):
           ('models/props/candelabra.abc', 'skins/props/candelabra.dtx'),
           ('models/props/plantsandtrees/tree04.abc', 'skins/props/plantsandtrees/treebark2.dtx;'
            'skins/props/plantsandtrees/treebranch3.dtx;skins/props/plantsandtrees/leafpile01.dtx'):
           ('models/props/plantsandtrees/tree04.abc',
            'skins/props/plantsandtrees/treebark2.dtx;skins/props/plantsandtrees/treebranch3.dtx')}
_OWNERS = {
    'scrollpickup': 'tasaracademy', 'treasurebag': 'inventastorca', 'anvil': 'drangheimprison',
    'barrel': 'anskramkeep', 'basketfruit': 'klusoshouse', 'basketveggies': 'klusoshouse', 'beaker01': 'lichlab',
    'bed': 'anskramkeep', 'bedornate': 'dookscastle', 'bedwall': 'drangheimprison', 'bedmedium': 'anskramkeep',
    'benchstone01': 'templeofhonk', 'benchstone02': 'templeofhonk', 'bookflat': 'templeofhonk',
    'bookcase01ew': 'templeofhonk', 'bookcase01ns': 'templeofhonk', 'bookcase02ew': 'anskramkeep',
    'bookcase02ns': 'anskramkeep', 'brazier': 'templeofhonk', 'bucket01': 'drangheimprison',
    'bucket02': 'thjoradmine', 'burner': 'lichlab', 'cabinet02': 'klusoshouse', 'cabinet02ns': 'klusoshouse',
    'cabinet04ns': 'drangheimprison', 'cabinet05': 'klusoshouse', 'cabinet05ns': 'drangheimprison',
    'chair': 'anskramkeep', 'chair02': 'anskramkeep', 'chair03': 'lichlab', 'chairdesk01': 'templeofhonk',
    'chairdesk03': 'templeofhonk', 'chandelier': 'tasaracademy', 'chandelier3': 'ruinedtemple',
    'chest1': 'anskramkeep', 'coalbin': 'drangheimprison', 'coatrack': 'isleofashes', 'crate': 'anskramkeep',
    'desk01': 'anskramkeep', 'desk01ns': 'anskramkeep', 'desk03': 'templeofhonk', 'dresser': 'isleofashes',
    'dresserns': 'anskramkeep', 'forge': 'tasaracademy', 'hangingbowl1': 'beethoven',
    'ironingots': 'drangheimprison', 'logs': 'lichlab', 'logsburning': 'isleofashes', 'oillamp': 'thjoradmine',
    'pew2ns': 'klusoshouse', 'pillarstand': 'chasmofthedead', 'pitcher01': 'klusoshouse', 'bush03': 'darkpassageway',
    'podium01': 'lichlab', 'sack02': 'connectingtunnels', 'sack03': 'drangheimprison', 'scroll': 'anskramkeep',
    'scrollp268': 'verhoffinruins', 'shelfitem01': 'lichlab', 'shelfitem02': 'lichlab', 'shelfitem03': 'lichlab',
    'shield1': 'dookscastle', 'shield2': 'dookscastle', 'smithhammer': 'tasaracademy',
    'stove': 'drangheimprison', 'suitofarmor01': 'drangheimprison', 'table01ns': 'lichlab',
    'table02': 'templeofhonk', 'tablebench2': 'drangheimprison', 'tableround': 'anskramkeep',
    'tableround2': 'drangheimprison', 'throne': 'lichlab', 'trainingmount': 'traininghall',
    'spindummy': 'traininghall', 'strawdummy': 'traininghall', 'tree04': 'lindisfarnemonastery',
    'wallcandle': 'klusoshouse', 'walltorch': 'anskramkeep', 'weaponrack_new': 'tasaracademy',
    'woodbin': 'thjoradmine', 'clover': 'drangheimcity'}
REUSED = {prop: PROPS_DIR / f'mm9_{owner}_claude' for prop, owner in _OWNERS.items()}
# Objects whose decoration is another prop than their (model, skin)'s: the burning logs under MM9's Fire3 (FireScale
# 4) are the isle's logsburning (its flame cards); the four others have no Fire and are the Lich Lab's unlit logs.
# The tipped scroll and shields (above); the HidePiece variants (HIDDEN).
OBJECT_PROP = {'Logs4': 'logsburning',
               'Bartender': 'peasantm2innkeeper', 'Ludwig': 'peasantms2bwriting', 'RUDEProp0': 'peasantms2bconv',
               'CommonerHumanMaleA5': 'peasantms2csitting', 'CommonerElfFemaleA1': 'peasantms2csitting',
               'Halfdan': 'peasantms2dlisten', 'CommonerHumanMaleA6': 'peasantms2dsitting2',
               'Weaponrack0': 'weaponracknewg2', 'Weaponrack1': 'weaponracknewg3',
               'Shelfitems15': 'shelfitem09sg', 'Shelfitems14': 'shelfitem09d', 'Shelfitems24': 'shelfitem03f'}
# Variants built here from another prop's source (MODELS id).
SOURCES = {'peasantm2innkeeper': 'peasantm2c', 'peasantms2bwriting': 'peasantms2b', 'peasantms2bconv': 'peasantms2b',
           'peasantms2csitting': 'peasantms2c', 'peasantms2dlisten': 'peasantms2d', 'peasantms2dsitting2': 'peasantms2d',
           'shieldrustyp90': 'shieldrusty', 'shield1flat': 'shield1', 'shield2flat': 'shield2', 'weaponracknewg2': 'weaponrack_new', 'weaponracknewg3': 'weaponrack_new',
           'shelfitem09sg': 'shelfitem09', 'shelfitem09d': 'shelfitem09', 'shelfitem03f': 'shelfitem03'}
# Pitch, roll baked in (decorations turn about z only); placements.py tilts the raw points the same way to check them.
# scrollp268 is Verhoffin Ruins' with this tilt baked in.
TILTS = {'shieldrustyp90': (1.5707964, 0.0), 'shield1flat': (1.5707964, 0.0), 'shield2flat': (1.5707964, 0.0),
         'scrollp268': (4.6862092, 0.0)}
# (prop, pitch, roll in whole degrees) of a tilted object -> its tilted variant (Yanmir's Fort's route).
# 2026-11-07 (prop_audit.py): MM9's pitch pi/2 stands up the shield its first animation lays down: the shields hang
# on the walls as Dook's Castle's shield1/shield2/shield4/shield3r (Thjorgard City's route); the shieldNflat variants
# lie flat and stuck out of the walls like shelves.
TILT_OF = {('shield1', 90, 0): 'shield1', ('shield2', 90, 0): 'shield2', ('shieldrusty', 90, 0): 'shieldrustyp90',
           ('scroll', 269, 0): 'scrollp268'}
TILTS.update({v: (1.5707964, 3.1415927) for v in ('shield1', 'shield2', 'shield3r', 'shield4')})
SOURCES['shield3r'] = 'shield3'
REUSED.update({v: PROPS_DIR / 'mm9_dookscastle_claude' for v in ('shield1', 'shield2', 'shield3r', 'shield4')})
# HidePiece0-4 of the objects: their pieces stripped from the variant's raw GLBs (scripts/strip_pieces.py). The
# creature ABCs lose their shadow n-gon (one polygon of ~330 vertices).
HIDDEN = {'weaponracknewg2': ['Group2'], 'weaponracknewg3': ['Group3'], 'shelfitem09sg': ['SkullCaps', 'Gloves'],
          'shelfitem09d': ['Daggers'], 'shelfitem03f': ['Crystals1', 'Wands1', 'Hourglass1'],
          'peasantm2innkeeper': ['ngon'], 'peasantms2bwriting': ['ngon_s'], 'peasantms2bconv': ['ngon_s'],
          'peasantms2csitting': ['ngon_s'], 'peasantms2dlisten': ['ngon_s'], 'peasantms2dsitting2': ['ngon_s'],
          'bjarnisitting': ['ngon'], 'erccsitting': ['ngon_s'],
          # VIALS.abc also holds a 3ds Max biped (the Bip01* pieces, a 30 LT mannequin 230 LT off the vials)
          'vials': ['Bip01*']}
# The peasants' animations are not in their models (PeasantMS2 has only MP_2s, PeasantM2 only MP_2a: their first
# keys are T-poses with the arms out): MM9 takes them from its animation libraries, PeasantSeated.abc (the seated
# men: sitting, sitting2, listen, conv, Ludwig_writting; the same 43 nodes in the same order as PeasantMS2) and
# PeasantWork.abc (innkeeper2; the same 45 nodes as PeasantM2). scripts/convert_library_pose.py exports the model with
# the library animation added (LIBRARY: prop -> (library ABC under MODELS, animation)). Tryggva's conv1
# (tryggvaspeech.scr) is not in PeasantSeated; its `conv` stands in (PeasantHoFS1's conv1 is a female library).
LIBRARY = {'peasantm2innkeeper': ('PEASANTWORK.abc', 'innkeeper2'),
           'peasantms2bwriting': ('PEASANTSEATED.abc', 'Ludwig_writting'),
           'peasantms2bconv': ('PEASANTSEATED.abc', 'conv'),
           'peasantms2csitting': ('PEASANTSEATED.abc', 'sitting'),
           'peasantms2dlisten': ('PEASANTSEATED.abc', 'listen'),
           'peasantms2dsitting2': ('PEASANTSEATED.abc', 'sitting2')}
# Posed models: (animation, frame) set in build (blib.import_raw) and placements (posed_points).
POSES = {**{prop: (animation, 0) for prop, (_, animation) in LIBRARY.items()},
         'bjarnisitting': ('sit', 0), 'erccsitting': ('sitting', 0), 'catstanddown': ('standdown', 0)}
PLACE_POSES = {}
CHECK_POSES = {}
POSE_TURN = {}
SKIN_ORDER = {}
# Built though no DAT object places them: the town portal altar's cleansed skin, the model a script swaps in.
EXTRA_BUILT = {'portalclean'}
CLASSES = {'Prop', 'CandleProp', 'WallTorch', 'Brazier', 'TreasureBag', 'RUDEProp', 'Clover'}
# Objects of those classes (and the other model-carrying objects of the DAT) that get no decoration: name -> reason.
SKIPPED = {
    'Painting': 'models\\Props\\Painting_Rectangle.ABC is not in MM9 (MODELS.REZ): MM9 shows nothing there',
    'Painting0': 'models\\Props\\Painting_Rectangle.ABC is not in MM9 (MODELS.REZ): MM9 shows nothing there',
}


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
    """The props built here: the placed ones minus the reused, and EXTRA_BUILT."""
    try:
        placed = {prop for _, prop in placements()}
    except FileNotFoundError:
        placed = (set(MODELS.values()) | set(SOURCES)) - set(SOURCES.values())
    return sorted((placed | EXTRA_BUILT) - set(REUSED))


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

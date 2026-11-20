# MM9 outdoor regions' props (2026-11-04)

The props of MM9's eleven outdoor regions (Sturmford, Thjorgard, Thronheim, Drangheim, Guberland, Frosgard,
Lindisfarne, Yorwick, Mountain Pass, Boot Camp, Afterworld), rebuilt as BLVs open to the sky
(devdocs/mm9_rework/OUTDOOR_BLV_ALL.md), as decorations: step 3 of devdocs/mm9_rework/DECORATIONS_AND_GRASS.md. The Isle of
Ashes keeps its pilot's props.json.

## What is placed

- **Props another map already built** (746 placements of 94 props): the model the props project of another MM9 map
  installed for the same (model, skin), at the DAT position, fitted to the old import's baked copy of the same object
  (median of medians 0.5-0.65 units per region), MoveToFloor ones then standing on the remade ground.
- **Vegetation** (about 450): MM9's trees, bushes and flowers as MM6-MM8 3D models at MM9's own sizes
  (`scripts/vegetation.py`, review/tree_candidates.png, review/mm9_vegetation_skins.png):

  | MM9 | ours |
  | --- | --- |
  | tree02, tree04 (pine, irregular crown) | MM6 6tree18 (2/3), MM7 tree60 hemlock (1/3) |
  | tree05 (conical spruce) | MM8 pines tree29, tree30 |
  | tree06 (tall narrow spruce) | MM7 tree60, MM8 tree30 |
  | snowtree1/2 | MM7 tree36 snow spruce (1/2), MM6 snotre01, snotre05 |
  | deadtree3/4 | MM8 tree28, MM6 6tree27 |
  | bush01 (fern), bush02 (broad leaves) | MM7 bush03, MM7 bush02 |
  | flowers01/03 (roses, daisies) | MM7 flower03, flower04, flower10 |

  MM9's trees are much taller than ours (tree02 1708 units at scale 1, our MM8 pines 976-1000): each is an MM9 world
  row `mm9v_<ours>_<height>` binding our model at MM9's height x the object's Scale (25-unit steps).
- **Props built here** (`scripts/props_table.py`, Thjorgard City's route): stones (and the five coloured ones of
  Thjorgard and Guberland), arrows, swords, the pickaxe, hay bales, the lantern (lantern2's half-size flame cards seated on its candle top), toy
  boats, the beam-less bell, two awnings, sheds, the windmill sails, the plough, doll, great book, hair brush, the
  penance rune stone and the broken portal. Tilted ones (arrows and swords stuck in the ground, the leaning windmill,
  Afterworld's rusty axes) are baked variants `<prop>p<pitch>[r<roll>]` (TILTS): a decoration turns only about the
  vertical; the old import's bakes fit their tilt (0.5-0.7 units; the other pitch sign 8.8). Their skins are redrawn by
  ../mm9_skins_x4/skins.py like every MM9 prop's.

## Added 2026-11-05 (the props audit, devdocs/mm9_rework/checks/props_audit_20261105.md)

- **Every prop class** (inventory.py CLASSES): besides Prop and CandleProp, the braziers and torches, the chests
  (kind chest: 19 region chests had loot and click events but no decoration, so they could not be opened), stat
  barrels (Barrel), bone piles, cauldrons, cook pots, clover, wells and the stat stones.
- **Stat stones**: StatStone.ABC in five skins. The red one is the Isle of Ashes' `statstone` (its orb on a scrolling,
  pulsing material); `scripts/statstones.py` makes `statstoneplain` (cyan orb), `statstonegreen`, `statstonepurple`
  and `statstoneyellow` from it (the skin and the orb tile swapped, the glow tinted). Their use is the shared region
  script's (outdoor_blv.py `stat_stones`, event 390 + k): MM9's StatStone class gives +BonusAmt to one stat for
  BonusSeconds (MM9 stat ids: might, magic, endurance, accuracy, speed, luck; magic is intellect and personality),
  once while it lasts. Boot Camp's museum stone has no bonus. MM9's PropAnim "Rotate" spin is not carried.
- **Battle witch axes** stuck in the ground (Yorwick, Afterworld): `battlewitchp89`, `battlewitchp136`.
- **Boot Camp's rune stone** (`runestonegm`) and **Frosgard's Green Man's tree** (`greenmanstree`: a unique landmark,
  MM9's own 40 m mesh with its bark and leaf cut-out skins redrawn, not swapped for an MM6-MM8 tree).
- **The whack-a-honky geese** (Thjorgard, Guberland: `goosefigure`, our goose model standing) at rest in their holes
  under the board, where MM9 keeps them until the game pops one up; the game itself is not carried (it needs a prop
  moved from Lua).
- **Posed figures** (user, 2026-11-05: our new 3D models posed as MM9 poses them): `scripts/pose_bake.py` skins each
  creature model's LODs at one frame of one clip in its MM9 tier (KHR_materials_variants; the colour-region masks
  and ramps kept, which the decoration renderer applies as the actors' do) into a static decoration: Afterworld's
  fallen clan soldiers (DeadStatic, Dead2; Clanshield1 clan_b, BeldShield1 clan_a), Kira, Bjarni, Sigmund and
  Tryggva dead (StaticDie, Dead, DeadStatic), the three seated heroes (Sit), and Boot Camp's nine museum creatures
  (Standing, their MM9 skins' tiers). placements.py `posed_bake` places them at their DAT position on the floor.
  The skeleton's dagger reads as 2 inverted closed parts in the Standing pose only (a thin blade the pose folds; the
  rest pose and the actor are the same mesh): accepted.

## Left out (listed by placements.py)

- **Yorwick's battlefield** (70 objects: the guard, Kira, Sven and the fallen, swords and arrows): SvenShowTake.inc's
  RemoveAll hides them except during Svenspeech.scr's cutscene (key 95, not 97), which the map does not carry (it
  gives the cutscene's reward on load). Afterworld's copies are placed: nothing there hides them.
- MM9's two invisible `candle` CandleProps and Thjorgard's Barrel02 (MM9 does not ship the model).

## Route

```sh
cd level_generation/props/mm9_outdoor_regions_claude
python3 scripts/inventory.py                      # region Props/CandleProps matched to installed models
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install               # never beside a game build or a map conversion
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
python3 scripts/inventory.py                      # again: the new models now count as installed
python3 scripts/placements.py                     # props.json per region + new rows (scripts/rows.py)
python3 ../../projects/mm9r_common/review_root.py # then convert the regions (mm9r_<region>_blv/convert.py)
```

Rows (scripts/rows.py) go into assets_dev's MM9 world tables and indoor manifest; the outdoor BLVs' review root
rebuilds its own copy of the manifest from assets_dev on every conversion (outdoor_blv.py `bind_indoor_decorations`).

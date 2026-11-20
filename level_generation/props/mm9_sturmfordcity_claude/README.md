# MM9 Sturmford City props as 3D decorations (2026-10-31)

The props, lamps, candles, chandeliers, braziers, wall torches, treasure bags and the named townsfolk (RUDEProps) of
MM9's Sturmford City (`STURMFORDCITY.dat`), converted from their LithTech ABC models into OpenYAMM 3D decorations for
the native BLV ([map project](../../projects/mm9r_sturmfordcity/)). The route is Drangheim Prison's
([`../mm9_drangheimprison_claude/`](../mm9_drangheimprison_claude/README.md), itself the Lich Lab's) in its latest form,
Hall of the Gods' scripts (one material per MM9 skin, `specs.json` turns, `POSES` for posed creature ABCs, the isle's
`blib` build and `finish` checks) with the Anskram flame cards (`card` billboard, the pipeline as fixed on 2026-10-30).
No paid services, no Meshy, no Codex, no Real-ESRGAN: every model is MM9's own mesh with its skin x4 by plain Lanczos
(the isle's `textures.upscale`).

## Outputs

- **44 models built** and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked copies in `assets_dev/engine/models/`), all through `check_winding.py` (0 inverted closed parts each, in
  `finish.py` and rerun on the installed sources: `work/check_winding_installed.log`).
- **77 models reused** (same ABC and skin; their GLBs stay with their owners, `props_table.REUSED`): Anskram Keep
  (`barrel`, `bed`, `bedmedium`, `bookcase02ew/ns`, `chair`, `chair02`, `chest1`, `crate`, `desk01`, `desk01ns`,
  `dresserns`, `scroll`, `tableround`, `walltorch`), Temple of Honk (`benchstone01/02`, `bookcase01ew/ns`, `bookflat`,
  `brazier`, `chairdesk01`, `chairdesk03`, `desk03`, `table02`), Lich Lab (`beaker01`, `burner`, `chair03`, `logs`,
  `podium01`, `shelfitem01-03`, `table01ns`, `throne`), Drangheim Prison (`anvil`, `bedwall`, `bucket01`,
  `cabinet04ns/05ns`, `coalbin`, `ironingots`, `sack03`, `stove`, `suitofarmor01`, `tablebench2`, `tableround2`),
  Klusos House (`basketfruit`, `basketveggies`, `cabinet02/02ns/05`, `pew2ns`, `pitcher01`, `wallcandle`), Tasar Academy
  (`chandelier`, `forge`, `scrollpickup`, `smithhammer`), the isle (`coatrack`, `dresser`, `logsburning`), Training Hall
  (`trainingmount`, `spindummy`, `strawdummy`), Thjorad Mine (`bucket02`, `oillamp`, `woodbin`), Dook's Castle
  (`bedornate`), Beethoven (`hangingbowl1`), Ruined Temple (`chandelier3`), Chasm of the Dead (`pillarstand`), Dark
  Passageway (`bush03`), Connecting Tunnels (`sack02`), Inventa Storca (`treasurebag`), Lindisfarne (`tree04`),
  Verhoffin Ruins (`scrollp268`).
- Rows **2454-2515** (62 rows: the 44 new models and 18 new-scale variants of reused ones) in
  `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites **26255-26316**, 64 bindings in
  `worlds/mm9/models/indoor_decorations.yml` (the 62 plus indoor bindings of the isle's `mm9_coatrack` and
  `mm9_dresser`, which had only outdoor ones), appended in one run under
  `mm9r_common/locks/mm9_decorations.lock` (`work/tables_apply.log`). A rerun of `tables.py` reports 0 rows to add.
  No row carries a light.
- `../../projects/mm9r_sturmfordcity/props.json`: **439 placements** (329 `prop`, 99 `torch`, 9 `npc`, 2 `chest`),
  every Prop, CandleProp, WallTorch, Brazier, TreasureBag and RUDEProp of the DAT except the two paintings (below).
  **427** are checked against the old map's baked BModel of the same object: **median of medians 0.52 units, worst
  1.14** (Crate_1019; next chair02 0.83, crate 0.78); per model 0.26-0.83. The 12 not checked have no bake: the 9
  posed townsfolk and the posed cat (checked against MM9's own pose instead, `fit_pose_units` 0.01-1.11) and the two
  treasure bags (on the floor under their DAT position, MoveToFloor).
- **`portalclean`** (added 2026-11-06): TownPortal.scr's cleansed altar, PORTAL-WHOLE.abc with PORTALCLEAN.dtx
  (`props_table.EXTRA_BUILT`: no DAT object places it), built, finished and installed like `portalwhole` (identical
  positions, UVs, normals and vertex occlusion; 44 triangles; 0 inverted closed parts). Row 2813 `mm9_portalclean`
  (`tables.EXTRA`, `portalwhole`'s size and collision), sprite 26614, bound next to `mm9_portalwhole`. The cities'
  converters place it at the altar's spot as its hidden twin (`../../projects/mm9r_common/dungeon/town_portal.py`).
  `review/portalwhole_vs_portalclean.png`: the two side by side; `review/portalclean_ingame_sturmford.png`: Sturmford
  City before and after the click (engine capture).
- `review/props_sheet.png`: contact sheet of the 44 built models (LOD0 front, three-quarter, side, behind-above, below;
  LODs), looked at; `review/<prop>/` the renders.

| Model | Triangles | Placements | Fit | Notes |
|---|---|---|---|---|
| `barrelbeet` | 132 | 4 | 0.48 | BARREL-BEET (barrel skin), x1.5 |
| `barstool1` | 110 | 3 | 0.58 | |
| `bedmediumplain` | 92 | 4 | 0.33 | BEDMEDIUM with BEDPLAIN (Anskram's `bedmedium` has the BEDMEDIUM skin) |
| `beetrack` | 268 | 14 | 0.55 | cut-out skin; no LODs (the native LOD2 kept only a rope) |
| `bowl04`, `cup02`, `mug1`, `winebottle04`, `vials` | 88-214 | 1-4 | 0.50-0.65 | table things, no collision; VIALS.ABC also holds a 3ds Max biped 230 LT off (stripped, `HIDDEN`) |
| `broom`, `jacobsladder`, `kegbeer`, `portalwhole`, `sack01beet`, `winerack`, `trainingarchery1` | 44-1292 | 1-4 | 0.40-0.58 | `portalwhole` is the town portal (`townportal.scr`) |
| `chairskin1` | 104 | 2 | 0.47 | CHAIR with CHAIR1 (the Chasm's `chair1` is CHAIR1.ABC) |
| `candelabra` | 393 / 201 / 107 + 3 flames | 1 | 0.47 | flame cards on its three Flame sockets |
| `chandelier2` | 616 / 320 / 178 + 8 flames | 5 | 0.45 | flame cards on its eight Flame sockets |
| `lamppost4` | 281 + 1 flame | 25 | 0.52 | the street lamps; flame in the lantern (cut-out panes); no LODs (LOD2 lost the arm) |
| `lanternwall1` | 287 / 181 / 73 + 1 flame | 16 | 0.44 | wall lanterns; flame on the burner, cut-out panes |
| `clawlampup` | 396 / 172 / 99 | 1 | 0.44 | CLAWLAMP upright (Yanmir's `clawlampp180` hangs); a plain Prop here: no glow |
| `dragontrophy` | 397 / 197 / 99 | 1 | 0.52 | x4, wall-hung |
| `pewns` | 140 | 10 | 0.47 | MM9's `ns` quarter turn baked in (`specs.json` `turn: 90`; 107 unturned) |
| `shield1flat`, `shield2flat` | 104 | 1 + 1 | 0.39 | SHIELD with shield / shield2 skins lying flat (below) |
| `shieldrustyp90` | 140 | 2 | 0.48 | SHIELD_RUSTY, pitch pi/2 baked in: on the wall, x2 |
| `shelfitem09sg`, `shelfitem09d`, `shelfitem03f` | 177-348 | 1 each | 0.51-0.59 | HidePiece variants (below) |
| `weaponracknewg2`, `weaponracknewg3` | 936 / 1001 | 1 each | 0.66 / 0.69 | Tasar's `weaponrack_new` source without MM9's hidden Group2 / Group3 |
| `strawdummy2c/l/r` | 362-418 | 2 each | 0.55-0.59 | the hanging training dummies |
| `peasantm2innkeeper`, `peasantms2bwriting`, `peasantms2bconv`, `peasantms2csitting`, `peasantms2dlisten`, `peasantms2dsitting2` | 678-694 / ~335 / ~170 | 1-2 | pose 0.01-1.11 | the townsfolk, posed (below) |
| `bjarnisitting`, `erccsitting`, `catstanddown` | 274-780 | 1 each | pose 0.01-0.02 | Bjarni (`Sit`), Ercc (`sitting`, two skins: body and cup), the cat (`standdown`) |

New-scale rows of reused models: `mm9_barrel_x100`-style reuse where a row existed; new ones `mm9_beaker01_x75/_x50`,
`mm9_bed_x150`, `mm9_bedornate_x100`, `mm9_bookcase01ew_x125`, `mm9_bookcase01ns_x125/_x150`, `mm9_bush03_x100`,
`mm9_forge_x100`, `mm9_hangingbowl1_x200`, `mm9_logs_x150`, `mm9_pew2ns_x100`, `mm9_pitcher01_x75`, `mm9_podium01_x85`,
`mm9_sack03_x200`, `mm9_scrollpickup_x100`, `mm9_tableround_x75`, `mm9_tree04_x100` (Lindisfarne's trunk blocker
scaled: radius 40, height 269). The burning logs use the existing unlit `mm9_logsburning_x150` (row 2251).

## RUDEProps and other named entities (entity name = `source_name` in props.json)

No MM9 props project had placed RUDEProps (The Arena left its spectators out: no peasant 3D models). Here each is a
static decoration in its script's pose, `kind: npc`, with `script`, `script_params` and `rude_npc_id` (the DAT's
RUDENPCId, a float stored as its bits, decoded) so the map's `convert.py` can wire their dialogue to the entity:

| Entity | Decoration | Script (params) | rude_npc_id | Placement |
|---|---|---|---|---|
| `Bartender` | `mm9_peasantm2innkeeper` | Sturmgaardinn.scr (Innkeeper2) | 57 | behind the inn's bar, on the floor |
| `Ludwig` | `mm9_peasantms2bwriting` | LudwigVan.scr | 47 | on his chair at the round table, writing |
| `RUDEProp0` (Tryggva) | `mm9_peasantms2bconv` | tryggvaspeech.scr | 63 | at the tavern bench table; Trigger1 sends it `blabber` |
| `Halfdan` | `mm9_peasantms2dlisten` | PropAnim.scr (listen) | 76 | at the same table |
| `CommonerHumanMaleA5` | `mm9_peasantms2csitting` | PropAnim.scr (sitting) | 428 | tavern bench table |
| `CommonerHumanMaleA6` | `mm9_peasantms2dsitting2` | PropAnim.scr (Sitting2) | 428 | on the bar stool (MoveToFloor 0) |
| `CommonerElfFemaleA1` | `mm9_peasantms2csitting` | akeretainer.scr (Fidget1) | 86 | on the pew Pew5 (the retainer) |
| `Bjarni` | `mm9_bjarnisitting` | Bjarni.scr | 45 | by the Throne (9 LT off), base on the floor |
| `RUDEProp1` (Ercc, a Prop) | `mm9_erccsitting` | erccspeech.scr | - | the drunk at the tavern table; Trigger2 sends it `blabber` |
| `Cat2` | `mm9_catstanddown` | PropAnim.scr (standdown) | - | `kind: prop` |
| `Prop0`, `Prop1`, `Prop3`, `Prop4`, `Prop7` | `mm9_scroll` (`Prop4`: `mm9_scrollp268`) | BookLetter.scr (449 letter 1, 450 Letter, 452 Letter 1, 453 Letter, 451 Letter 1) | - | `kind: prop` |
| `Books`, `Books0`, `Books1` | `mm9_bookflat` | book.scr | - | `kind: prop` |
| `TownPortal0` | `mm9_portalwhole` | TownPortal.scr (Sturmford) | - | `kind: prop` |

53 unscripted DAT names repeat (Chair, Table, Barrel, ...) and `Bucket` is a decoration's name: they get
`_<object index>` (`dat_name` keeps the DAT's). No scripted name repeats.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_sturmfordcity_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_sturmfordcity_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose            # --preview writes work/props_preview.json instead
python3 ../../projects/mm9r_common/review_root.py
```

`tables.py` does not take the lock itself (run it under `flock` as above). `convert_all.py` runs
`scripts/convert_library_pose.py` for the `LIBRARY` props and strips `HIDDEN` pieces (keeping `<prop>_full.glb`, the
unstripped export placements.py fits against the old bake). `work/registry.py` maps every (ABC, skin) of the other MM9
props projects to its prop and owner (`work/registry.json`): the reuse check.

## Notes

- **Townsfolk poses.** PeasantMS2.abc and PeasantM2.abc carry only `MP_2s` / `MP_2a`, whose first keys are T-poses;
  MM9 takes the scripts' animations from its libraries, which have the same nodes in the same order: PeasantSeated.abc
  (`sitting`, `sitting2`, `listen`, `conv`, `Ludwig_writting`) and PeasantWork.abc (`innkeeper2`).
  `convert_library_pose.py` adds the library animation to the export and `build.py` poses it at its first key
  (`props_table.LIBRARY`, `POSES`). Tryggva's `conv1` is not in PeasantSeated; its `conv` stands in (PeasantHoFS1's
  `conv1` is a female library). Their `ngon`/`ngon_s` piece (a one-polygon shadow n-gon) is stripped. They are static:
  no idle animation, no turning to the party.
- **Seat heights.** MoveToFloor townsfolk stand with their feet on the floor under them (the transcoder's floor rule;
  Ercc lands exactly on his old bake, delta 0.0); the two without MoveToFloor (Ludwig, the man on the bar stool) are at
  their DAT position with the model origin at Pos (with the binding origin added they would sink 15 LT), Ludwig lifted
  10 units so his feet do not go through the floor. Bjarni sits by the Throne with his feet on the floor; whether he
  clears its seat was not looked at in game.
- **Shields.** Shield_Rusty's ABC lies flat and MM9's pitch pi/2 stands it on the wall (`shieldrustyp90`); Shield.ABC
  stands and the same pitch lays it flat: the old bake is flat (10 units high) and fits pitch pi/2, roll 0 at 0.41
  (Dook's Castle's hanging `shield1`/`shield2` measured 39.7). So `shield1flat`/`shield2flat`. Blender's import of the
  raw Shield GLB is already flat (glbio's node transforms see it standing), so their `specs.json` tilt is 0 while
  `props_table.TILTS` (pitch pi/2) is the one placements.py applies to the raw points; the finished models fit 0.39.
  **Corrected 2026-11-02 (Thjorgard City's play-test): MM9 hangs these shields.** The old bake this was measured
  against is the old import's, which baked every pitched Shield.ABC flat (Dook's Castle README: its four hang at pitch
  1.571); the shields stand 5 units off a wall, half a shield's thickness. Use Dook's hung `shield1`/`shield2`/
  `shield4`/`shield3r` (TILTS pitch pi/2, roll pi) at the rollout, as `mm9_thjorgardcity_claude` does.
- **HidePiece**: Weaponrack0/1 hide Group2/Group3, Shelfitems15 hides SkullCaps and Gloves (daggers stay:
  `shelfitem09sg`), Shelfitems14 hides Daggers (`shelfitem09d`), Shelfitems24 hides Crystals1, Wands1, Hourglass1
  (`shelfitem03f`): stripped from the raw exports (Bathhouse's `strip_pieces` route).
- **Flames** use the pipeline as fixed on 2026-10-30: the isle's `finish.py` gives the `Fire` material
  `openyamm_billboard: card`; the cards (Klusos House's / Tasar's candle cards) stand on the ABCs' Flame socket markers
  (one-triangle pieces at each wick or burner, dropped from the mesh). Reused lit models keep their owners' flames
  (`walltorch`, `brazier`, `chandelier`, `chandelier3`, `wallcandle`, `oillamp`: `card`; `hangingbowl1` and the isle's
  `logsburning`: plain billboard on the axis). Logs4 lies under MM9's Fire3 (FireScale 4) and is the isle's
  `logsburning`; Logs0-3 have no Fire and are the Lich Lab's unlit `logs`.
- **Lights**: no row carries a light. Each of the 99 torches names the nearest DAT `Light` (10-131 units off, 99
  distinct) in `light`; the map project's `work/lights.json` did not exist yet.
- **Not placed**: `Painting`, `Painting0` (`models\Props\Painting_Rectangle.ABC` is not shipped by MM9: MM9 shows
  nothing there). The 2 `Clover` objects (`models\Props\clover.ABC`, baked by the old map as static props) were
  left out at first as "not a decoration class";
  the two `Clover` objects are placed since 2026-11-12 (Drangheim City's `mm9_clover`, the existing row; appended to `props.json` from `placements.py --preview`, the other entries left as installed): the map's clover events had nothing to click. Not decoration classes, left to the map: the townsfolk/shopkeeper/guard creature classes (`CommonerElfFemaleA`, ...: 24 of
  them reference models MM9 does not ship; `work/missing_models.txt`).
- Chests: the DAT has no TreasureChest; the four `Chest1.ABC` objects are Props (no loot in MM9; the old map baked them as
  `MM9_chest_*`) and are `kind: prop`. The two TreasureBags (loot containers 0 and 1) are `kind: chest`.
- Not looked at in game: the flames from the side, the townsfolk on their seats, the lamp posts' cut-out panes.

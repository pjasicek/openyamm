# MM9 rework: Hall of the Gods (`hallofthegods.blv`)

MM9's Hall of the Gods (the gods' open temple above the clouds: reached from Arslegard City's ExitTriggerHall, from
the Thousand Terrors' ExitTrigger1 after Njam, and from the Afterworld; home of Krohn, Skraelos, Fre and the Great
Honk, and the stage of the end of the game) converted from its DAT world into a native indoor map (BLV) on the shared
dungeon converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the
isolated review root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and
the prop models ([props project](../../props/mm9_hallofthegods_claude/README.md)). No x4 textures yet.

Status 2026-10-31 (overnight run): geometry with MM9's own Arslegaard sky box on the six sky faces, 1 room, 34 lights, 41 decorations (statues in
MM9's `statue` pose), the four gods with their RUDE dialogues and quest ends, the end-game cinema's outcome, the bill of
sale, baked lighting matched to MM9's DAT lightmaps. No package change, no engine change.

Update 2026-10-31 (floor holes: the shared converter's `dungeon/floors.py`,
[`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md), Thousand Terrors section): one 2.56-unit
crack (`FloorMarbleBorder`, 1 178 long at (5012, 1353, 676), over a 1 987 drop) is welded. 2 165 compiled faces. Rebuilt
and rebaked (`bake_slot.sh`); the four scenarios pass; the walkability audit is unchanged.

## Does it fit the dungeon route? Yes

The brief asked to decide first. The map is real enclosed geometry: a PhysicsBSP of 2 784 polygons (a porch with the
gate to Arslegard, the colonnaded west hall with its pool, the great stair, the throne hall with the god statues),
closed by MM9's six `skymarker` faces round the whole temple, through which MM9 draws its Arslegaard sky box (the
`Snow` DemoSkyWorldModel: blue sky, the sun overhead, a sea of clouds below). It is a story map (no monsters, the gods'
dialogues, the end-game cinema), not a cutscene stage: the party arrives on `StartPoint0`, walks, talks and leaves by
the gate. The open sky is the Chasm of the Dead's and Lindisfarne's situation (sky faces inside the BLV), so the map
converts on the shared route. The end-game cinema is the in-engine cinematic `gods_epilogue` (Cinematics, below).

## Build and review

```sh
python3 level_generation/projects/mm9r_hallofthegods/convert.py --plan     # rooms only: work/rooms*.png
python3 level_generation/projects/mm9r_hallofthegods/convert.py            # build, compile, install
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_hallofthegods
python3 level_generation/projects/mm9r_hallofthegods/make_scenarios.py
for s in doors_exits scripted quests immobile; do ./build/game/openyamm \
    --asset-root "$PWD/output/mm9_rework/assets_dev" --headless-run-scenario \
    level_generation/projects/mm9r_hallofthegods/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_hallofthegods
python3 level_generation/projects/mm9r_hallofthegods/make_tour.py v02 [--original]     # also lighting<n>
level_generation/projects/mm9r_hallofthegods/work/run_tour.sh v02 [original] [--set video.lightmaps=false]
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_hallofthegods
```

`work/run_tour.sh` wraps `./tools/run_game.sh --isolated` (minimized, `SDL_AUDIODRIVER=dummy`, the original with
`--set video.view_distance=unlimited`).

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame). The porch and the west hall on 0 LT, the
  great stair's landing at 256, the throne hall at 264-268, Krohn's dais at 332; the sky box from LT y -512 (the clouds
  below) to 2 304, x -3 616..3 872, z -928..3 328.
- 2 906 source polygons -> 1 921 merged -> **1 905 native polygons** (57 triangulated), **2 165 compiled faces** (one crack welded, 2026-10-31), 4 201
  vertices; 16 faces with no air in front dropped (`work/dropped_faces.json`: the column bases' undersides and tops
  against the floor and roof, the fence boxes' bottoms, one underside of the platform; no thin partition, `thin_walls` on).
- **1 room** (+ sector 0) and **0 portal faces**: the whole temple stands in one air volume with the sky box round it
  (the colonnades open on every side), so no cut can close a room (playbook: loops cannot be cut). Floor check 0 LT²;
  `mixed_faces.json` empty.
- **0 movers**, **0 chests** (MM9 has none here), **0 pads**.
- **34 BLV lights** of MM9's 46 `Light`s (+12 bake-only fills over the four-per-point cap), the 31 `DirLight`s in the
  bake; light coverage at most 4 per floor point.
- **41 decorations** ([props project](../../props/mm9_hallofthegods_claude/README.md): 19 props, 18 braziers, 4 wall
  torches), **10 actors** (4 NPCs shown, the cinema's 6 hidden).
- **15 translucent faces** (the stained glass).

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP` (2 784 polygons), `StainedGlassWindows`, `WorldObject0` (the stained glass and its stucco), `WorldObject2` (the spiked fence round the porch, its invisible collision), `WorldObject6` (the gate's `Water115.spr` shimmer), `WorldObject42` (the pool's surface) | static world; invisible collision; non-solid surfaces untouchable. `VisBSP`: no UserPortals |
| six `skymarker` faces (the box round the temple) | the six textures of MM9's Arslegaard sky box (`Snow`, a DemoSkyWorldModel): each face takes the texture and texel axes of the sky box's inner face with the same normal, scaled to the box (`convert.py edit_polygons`); shown at texture brightness by the bake (emitter `display` 1.0) |
| `windowlead1` (leaded stained glass, translucent and fully bright in MM9) | 15 translucent faces (`glass` in overrides.yml: opacity 1 x the texture's alpha 33-255, two-sided); the sky shows through them |
| `Prop` (benches, lions, throne, the bill of sale, seven god statues), `Brazier` (18), `WallTorch` (4) | 41 3D decorations (props project): the statues in MM9's `statue` pose (PropAnim.scr), flame cards on braziers and torches |
| `DragonAzure0/1`, `DragonPharoah`, `DragonThrone` | not built: MM9 does not ship their models (`DragonAzure.abc`, `DragonThrone.abc`, `models\DragonPharoah.abc`: absent from its archives), so MM9 draws nothing there either (props README) |
| `Krohn0` (NPC335), `Skraelos` (NPC336, Hall), `Fre` (NPC337), `TheGreatHonk0` (NPC377) | four friendly NPCs with their RUDE dialogues (335, 336, 337, 377): the old importer's MM9 NPC picture rows (Krohn 565 KnightPlate A, Skraelos 568 BLich A, Fre 352, the Great Honk MM9 row 9262), MM9's bodies (ABC extents x Scale x 2.56: Krohn.abc 20 x 54 at 1.25, Lich.abc 10 x 35 at 1.6, goose.abc 10 x 16 at 1.5), immobile but the Honk (BaseWander.inc) |
| `Hanndl`, `Krohn`, `Skraelos0`, `WyrdeoftheKnowing0`, `WyrdeoftheKnown0/1` (the cinema's cast: WG_NPC334/335/336.scr hide them at start) | six hidden actors (group 1) shown only for the end-game cinema (Lua) |
| `StartPoint0`, `ExitTriggerHall`, `ExitTrigger0` | start 0 in the porch facing east into the hall; MM9 positioned exit to Arslegard City (HallOfTheGodsExit) in the gate; ExitTrigger0 (to the Afterworld) stays a row in the air beyond the hall's east end, out of reach as in MM9, and Skraelos' script moves the party to its arrival |
| `Light` (46), `ObjectLight` (6), `DirLight` (31) | 34 BLV point lights, 12 bake-only (over the four-per-point cap); the ObjectLights light only MM9's models (not built); the DirLights in the bake (`dirlights: true`) |
| `ScriptObject` `WinMan` (WinMan.scr Part2) | the map Lua (the end of the game, below) |
| `Camera` (11), `Marker` (2), `AmbientSound` (23), `OutsideDef0`, `FastApproxArea0`, `WorldProperties0` | not built: the cinema's cameras (no scripted camera in the engine), HanndlMarker (Hanndl's place, used by the Lua), the camera pan target, ambient sound (a later pass), sky and visibility helpers |

## Scripted objects (`worlds/mm9/events/maps/hallofthegods.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **Krohn** `NPC335.scr` :OnRude :StopNjam | dialogue end (event 50124): key 108 (Tamur spoken to) without 191: Njam's Key (item 576) into the packs, key 191, 218 000 experience, the quest sound |
| **Skraelos** `NPC336.scr` (ScriptParams `Hall`) :OnRude | dialogue end (50125): :Teleport (key 101 without 102: key 379 and the party goes to the Afterworld, ExitTrigger0's arrival); :sixfires (key 103 without 189: key 189, 52 000 experience, the quest sound); :Failure (key 392: keys 379-392 taken, back to the Afterworld) |
| **Fre** `NPC337.scr` :OnRude :GoldenHonk | dialogue end (50126): key 346 without 347: 10 000 gold, 80 000 experience, the quest sound, the Golden Honk (369) taken, key 347 |
| **The Great Honk** `NPC377.scr` :OnUse (DoRude 377) | a click opens RUDE 377 |
| **The bill of sale** `BookLetter.scr` "480 Letter 1" (Prop3, the scroll on the bench) | a click (event 76) shows MM9's letter 480 (`evt.SimpleMessage`) |
| **The end of the game** `WinMan.scr` Part2 (:Init, :OnKrohn, :StartPart2, :End, :Release), `WG_NPC334/335/336.scr` (:Loop, :OnStart, :OnAction) | map load: the cinema's cast hidden, Krohn0 shown. With key 109 (Njam beaten, given on the Thousand Terrors) and without the Writ of Fate (394): the cast appears (Hanndl, Krohn, Skraelos and the three Wyrdes), Krohn0 leaves the throne (hidden), Hanndl stands at HanndlMarker (his WalkTo, `evt.SetMapActorPosition`); after 90 s (MM9's chain of waits and the 13 lines of 76 s) :End gives the Writ of Fate (394) and :Release hides the cast and puts Krohn0 back. Once the Writ is held (or the map variable `CinemaDone` set) it does not run again |

**Unmatched** (not carried, with reasons): subtitles for the 13 voice lines (their text is not in the MM9 data);
`DoHighScore` (MM9's end-of-game score screen): the
engine's win screen (`WinGameScreen`, house 600) carries MM8's Jadame ending text and movie, wrong for MM9: an MM9 ending
is world work, written down here instead of shown wrong. WinMan.scr :OnUse, :OnSwitch, :DestroyMonsters, the Njam and
WG_Shot cameras: the Thousand Terrors' copy of the script (Part1), not reached here (this WinMan stands outside the walls).
NPC336.scr's six fires scenes (:Guilt, :Confession, :Suffering, :Retribution, :Absolution, :Rebirth, keys 380-391) work
on the Afterworld's objects (its fires, Camera9, the spawn markers, the dead heroes) and belong to the Afterworld's
conversion. Krohn's and Fre's greeting voices and Fre's OnUse voice line (`voices\NPC\NPC_335/337.wav`). PropAnim.scr on
the statues: baked into their pose (props project).

## Cinematics

`gods_epilogue` (105.6 s; `cinematics_hall.py`, installed by convert.py's map_script as `hallofthegods.cinematics.yml`
with its Lua block): WinMan.scr Part2 on load (the map-load event, key 109, no Writ of Fate, `CinemaDone` 0) starts it
instead of the old 90 s timer. Timeline from the scripts: :OnKrohn's 1 s, WG_Scene7Cam1's Wait 1 and MoveToPos
Scene7MK1 at 150, Cam2 3.5 s, Hanndl's WalkTo HanndlMarker at 50 LT/s (MONSTERS.txt row 260; it stops 75 LT short, where Cam5, Cam8 and Cam9 frame him), Krohn's Wait 1, then the
talk by the actors' waits and Hanndl05's length; the voices start on the .abc Voice keys (all at 0) and are MM9's wavs
(`voices\cinema\wingame\*.wav`); the cast plays the GLB clips Hanndl01-06, Krohn01-05, SC7_22_Krohn. Shots: party
view, Scene7Cam1's pan, then Cam2, 3, 4, 3, 5, 6, 5, 7, 5, 9, 6, 8, 7, 11, 5, 6, 10, 11, party view. Steps: 36001 gather
(the cast shown, Krohn0 hidden), 36002 the Writ of Fate (394) at :End (101.6 s), 36003 :Release (`CinemaDone`, the cast
hidden, Krohn0 back) at 104.6 s; done 36000. Cues: fades, Hanndl's place/walk/faces, Krohn's face, clips, 13 voices.

Test without a conversion: `python3 level_generation/projects/mm9r_hallofthegods/cinematics_pilot.py`, then in
`output/mm9_rework/cinematics_pilot_run` the headless `cinematic_gods_epilogue_{play,skip}.yml` and the regenerated
`scenario_scripted.yml` (PASS 2026-11-06). Captures: `output/mm9_rework/cinematics_pilot_run/captures_gods_epilogue3/`.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_hallofthegods.yml`: **direct 0.55,
ambient 1.5, bounce 1 (x1.0), sky_scale 0.2**, 128 samples, `dirlights: true` (MM9's 31 DirLights), `max_lighting: 1`
(MM9 clips at x1), 12 bake-only lights, the six sky box textures an emitter (0.85, 0.9, 1.0) shown at `display` 1.0 (MM9
draws them fully bright). Sector minimum light **31** (`map.ambient`): no frame ambient is subtracted from the decorations'
light; the bake keeps its own floor with `ambient_scale`. The stained glass is translucent, which the bake never makes
an emitter (`bake_indoor.py`): it shows the bright sky through its leading. `stale_bakes.py --check` does not list the map.

## Brightness

**Lightmap-matched** (no real MM9 screenshot of this map exists; `devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`: walls are
texture x lightmap x1). The scales are a least-squares fit of the three bake passes (direct, ambient, sky; each
recomposed alone, `work/zone_passes.txt`) to MM9's DAT lightmap luminance per zone (`hue_zones.py`). Ours / MM9 per zone
(`work/zone_ratio_final.txt`): porch 0.465 / 0.580 **x0.80**, west hall x1.00, stair x1.01, throne hall 0.432 / 0.351
**x1.23**, Krohn's dais x1.07. Hue: MM9's lightmaps are neutral (B/R 0.96-1.02), ours 1.00-1.07. Two zones are off by
more than 10 %: the porch (lit in MM9 by DirLights our cones reach less) and the throne hall (open on all sides, it takes
more of the sky and the shared ambient). The map is one room (no cut can close the open colonnades), so the sector
ambient cannot differ per zone; the fit is the best compromise (a closer porch makes the throne hall brighter still).
The real MM9 adds its torches' and braziers' dynamic light on top (RE), so on screen it reads brighter near them.

Screen means (centre crop, `work/brightness_lighting01.txt`): old-import capture 85.9, native unbaked 60.2, **native
baked 76.2** (x0.89 of the capture, information only: the capture draws the sky navy and walls brighter than MM9's
lightmaps). Per view the baked views are 58.6-94.0 (no dark view; MM9's PlayerLightOn has nothing to stand in for).
Views off the capture by more than 10 %: the west hall views x0.69-0.75, the stair foot x0.69, back from the throne
x0.71, the west corner x0.80 (the capture's walls), back to the gate x1.39, the throne x1.20, the throne hall entry
x1.12 (our sky in place of the capture's navy void).

**Decorations under the bake**: with sector minimum light 31 the statues, lions, benches and braziers read as bright as
the walls or brighter (`review/lighting01`), as MM9 lights its models. `model_lighting: true` was tried
(`review/model_lighting_compare.jpg`): the lions turned black and the statues and gods far darker than the walls and
MM9 (12 of the map's fills are bake-only and never reach that path), so it stays off.

Sheets (looked at): `review/v02_compare.jpg` (25 views, MM9 original | native baked), `review/lighting01_compare.jpg`
(original | unbaked | baked, 12 views), `review/model_lighting_compare.jpg`, `review/v01_compare.jpg` (the first unbaked
build without props), `review/o01_original_sheet.jpg`, the props' `../../props/mm9_hallofthegods_claude/review/props_sheet.png`.
Flames: looked at from the side in game by the props project (`game01`, `game02` there).

## Checks

- Scenarios (all on the final build, `work/scen_*.log`): `scenario_doors_exits.yml` **PASS** (from inside the gate along
  the west hall to the stair, up the stair to its landing; the gate's shimmer raises ExitTriggerHall to Arslegard City),
  `scenario_scripted.yml` **PASS** (the bill of sale by a real click; without key 109 the cinema's six are hidden and
  Krohn is on his throne; with key 109 they appear, Krohn0 is hidden, Hanndl stands at his mark; after 95 s the Writ of
  Fate is in the packs, the six are hidden again and Krohn is back; with the Writ held the cinema does not rearm),
  `scenario_quests.yml` **PASS** (every god friendly; the Great Honk's and Fre's RUDE by real clicks; Krohn's and
  Skraelos' by `interact_actor` (below); Krohn's end gives Njam's Key and key 191 only with key 108; Fre takes the Golden
  Honk for key 347; Skraelos gives key 189 for key 103, and with key 101 key 379 and the move to the Afterworld),
  `scenario_immobile.yml` **PASS** (the four gods hold their places for 30 s).
- **Model actors take no headless click**: Krohn (row 565) and Skraelos (568) draw the MM6 world's 3D models; every
  press_interact pose missed them headless (`work/dbg_krohn.yml`), so their talks run through `interact_actor`, the
  click's activation path. The sprite actors take real clicks.
- **The gods' rows were hostile**: 565, 568 and 555 are monster families the relation table sets against the party, so
  Krohn and Skraelos read `hostile_to_party` with the aggressor bit clear and their talk was refused. Every god
  borrows the peasant family's relations (`ally` 118, row 352's type; `GameplayActorService::relationMonsterId`); the
  quests scenario asserts all ten friendly.
- **Desktop checks** (isolated runs, dummy audio): the party walks up the stair into the throne hall
  (`work/walkdbg/collision_trace.txt`: from the landing at z 635 to 676 and on to x 3 003; headless movement stopped at the
  landing's last 8 LT riser until 2026-11-07 and now walks on into the throne hall as well, scenario_doors_exits; the audit reads the throne hall as cut off for the same reason: false,
  no monster lives here); Skraelos' dialogue end with key 101 opens the travel question to the Afterworld
  (`work/teleport/after_teleport.png`; MM9's ExitTrigger0 has AskPlayer 1 too).
- Walkability (`work/walkability.json`, `work/audit.log`): 27 steps, 6 flights, 3 unreachable regions. Steps: the
  porch fence's posts (61-82, its invisible boxes), the lion plinths and the two long statue platforms (16 LT, 41), the
  stair landing's sides, Krohn's dais (16 LT); flights: the fence posts. Unreachable: the two lion plinths (0.43 M units²
  each, 41 high: the party steps up, the audit's monster rule does not) and the throne hall (above: walkable on the
  desktop). No actor is a monster; the Great Honk's row is Stationary.
- Floor check 0 LT²; mixed faces 0; no hole seen in the 25 + 12 views.
- Starts: StartPoint0 on the porch floor facing east into the hall (first view of every tour); the arrivals from
  Arslegard City, the Thousand Terrors and the Afterworld land on it (rows' arrival z 1).
- Compiler unit tests `build/tools/openyamm_indoor_source_tests`: 21/21 pass (205 assertions).
- The shared transitions row `mm9:transition/1000terrors/444` (the Thousand Terrors into this map) checked after the
  final convert: source `1000terrors.blv` (that map's half), destination `hallofthegods.blv` with this map's arrival.
  For about five minutes at 02:36 this map's rebuild had put the row's source back to the old ODM and every game load
  failed; it was fixed by hand under the review tables lock and the shared writer now merges from the current row.
  Since that writer keeps a row once its map file is converted, ExitTriggerHall's box (reaching down to the porch floor,
  48 deep along x: MM9's 4 LT box is tested against its player's box, ours against the party's centre) is written by a
  map-local wrapper of `tables.transitions_text` in `convert.py`.
- Old-map `_authored` files: none exist for this map.

## Deviations from MM9 and why

- **The pool** (`WorldObject42`, Water115) draws with the liquid shader (2026-10-31, `water115_mm9`, `depth: shallow`,
  [shared helper](../mm9r_common/liquids.py)); the gate's vertical shimmer (`WorldObject6`) keeps its Water115 bitmap (a sheet,
  not a surface). Sheet: `review/liquid/before_after_p1.jpg`.
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): the pool stays opaque: its brush (`WorldObject42`) has no Translucent bit, so
  MM9 draws it opaque. Sheet `review/liquid/see_through.jpg` (unchanged).

- **The end-game cinema** is the cinematic `gods_epilogue` (Cinematics); MM9's score screen is the world's completion
  certificate, which appears when key 109 is given (at the Thousand Terrors' change of level), before the epilogue.
  :OnKrohn3 turns Cam4 off instead of Cam5, so MM9 has Cam5 and Cam7 on together for Krohn's third line: Cam7 (the shot
  of the speaker) is used.
- **Sky box at the box walls**: MM9 draws its sky box at infinity; here its six textures lie on the skymarker box a few
  thousand LT away, one tile per face (a little parallax when walking, the front and back faces stretched 1.8:1).
- **The gods' pictures** are the old importer's NPC replacement rows (a plate knight for Krohn, the MM6 lich for
  Skraelos, a red-dressed lady for Fre, a goose for the Honk, peasant women for the Wyrdes) until MM9 models land, and
  they borrow the peasants' relations.
- **The Great Honk does not wander** (its row is Stationary); MM9's BaseWander lets it walk about.
- **No dragons**: MM9 ships no models for DragonAzure, DragonPharoah and DragonThrone.

## Open items

- MM9 models for Krohn, Skraelos, Fre, Hanndl, the Wyrdes and the Great Honk (another session builds models).
- The completion certificate before the epilogue (above); ambient sound (23 AmbientSounds); the NPC voice lines.
- The six fires' scenes (keys 380-391) in the Afterworld's conversion.
- x4 textures last.

## Not checked

- Arrival by walking the Thousand Terrors' ExitTrigger1 or Arslegard's ExitTriggerHall (the rows' arrival is the start).
- Taking the Arslegard exit on the desktop (headless raises its transition).
- A desktop playthrough with real input, save/load after the Writ, Android.
- LOD switching of the statues at distance; the party against the statues' collision.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:00:57 (convert.py from the current shared converter, end 15:01:39): 30 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 2135 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_doors_exits.yml` pass, `scenario_immobile.yml` pass, `scenario_quests.yml` pass, `scenario_scripted.yml` pass.

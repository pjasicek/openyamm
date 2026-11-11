# MM9 rework: Lindisfarne Monastery (`lindisfarnemonastery.blv`)

MM9's Lindisfarne Monastery (reached from Lindisfarne's ExitTrigger0; home of the Thjorad hammer, the bell puzzle, the
organ, the Saint's relic and the paladin promotion) converted from its DAT world into a native indoor map (BLV: sectors,
portals, rotating and linear movers, ladders, lights, an exit volume) on the shared dungeon converter
([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_lindisfarnemonastery_claude/README.md)). No x4 textures yet.

Status 2026-10-31 (overnight run): geometry with the courtyard and the hillside outside the front door, 8 sectors, 40
movers, 7 ladders, 106 lights, the exit, 125 decorations, 27 monks and NPCs with their RUDE dialogues, the monks'
hostility, the bell puzzle, Thjorad, the organ, the NPCs' quest ends, the letters, baked lighting. The shared converter
is unchanged; one small engine fix (below, "Engine change").

Update 2026-10-31 (floor holes: the shared converter's `dungeon/floors.py`,
[`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md), Thousand Terrors section): 38 one-LT
(2.56-unit) cracks between same-height floor slabs are welded (`keepstonefloor128a` at 983 and 2294, the `AmazingTrim1b`
trims at 287 and 369, `Boards2a` at 896); each was a slit over a 983-unit drop in the installed BLV, wide enough for a
monster's path planner (2-unit floor samples) to fall through. 13 804 faces, 21 602 vertices. Rebuilt and rebaked
(`bake_slot.sh`); the four scenarios pass; the walkability audit is unchanged.

Update 2026-11-10 (the monks' chores): every monk stood and fidgeted, and the monk's `Fidget2` is its "who's there?"
voice, so it sounded across the monastery. MM9's scripts loop a clip whenever a monk stands, and a looped script clip
never fidgets ([ambient animation](../../../devdocs/mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md) section 4, item
8). `convert.py` now gives each monk its scene `mm9_ai.idle_clip` (`MONK_IDLE_CLIPS`): `MonkGuardBasic.scr` type 0
`standing`, 1 `hoe`, 2 `sweep`, 3 `hammer`, 4 `wash`, and `ThjoradMonk.scr` its first parameter (`pray`, `hammer`).
After the bells, Brother Kennet prays too (`evt.PlayActorClip` in `praying()`), and hostility clears the prayers.
Only the ten chatting monks (type -1) and the named NPCs still fidget. The scene and Lua were rebuilt with `--scratch`
(BLV unchanged), checked to differ only by these lines, and copied into `assets_dev` and the review root. Later the
same day: the working monks hold MM9's tools (`MONK_TOOLS`, scene `held_items`: hoe, broom, wash cloth; the
[held items project](../../props/mm9_held_items_claude/README.md)), and the organ player (NPC420.scr) turns to the organ
and plays it (`play`) for the hymn's 24 s (`T_ORGAN`), not talking meanwhile (`OrganPlaying`, which nothing set before).
The Thjorad monks carry no hammer, as in MM9 (ThjoradMonk.scr attaches one only to a monk without an NPC id).

## Build and review

```sh
python3 level_generation/projects/mm9r_lindisfarnemonastery/convert.py --plan     # rooms only: work/rooms*.png
python3 level_generation/projects/mm9r_lindisfarnemonastery/convert.py            # build, compile, install
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_lindisfarnemonastery
python3 level_generation/projects/mm9r_lindisfarnemonastery/make_scenarios.py
for s in doors_exits scripted quests immobile; do ./build/game/openyamm \
    --asset-root "$PWD/output/mm9_rework/assets_dev" --headless-run-scenario \
    level_generation/projects/mm9r_lindisfarnemonastery/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_lindisfarnemonastery
python3 level_generation/projects/mm9r_lindisfarnemonastery/make_tour.py v03 [--original]   # also lighting<n>
level_generation/projects/mm9r_lindisfarnemonastery/work/run_tour.sh v03 [original] [--set video.lightmaps=false]
level_generation/projects/mm9r_lindisfarnemonastery/work/zone_ratio.sh     # recompose + ours/MM9 lightmaps per zone
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_lindisfarnemonastery
```

`work/run_tour.sh` wraps `./tools/run_game.sh --isolated` (minimized, `SDL_AUDIODRIVER=dummy`, the original with
`--set video.view_distance=unlimited`).

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame). Ground floor 0 LT (the courtyard's grass
  -16), galleries, library and scriptorium 384, tower lofts 632, attic and organ loft 896, bell floor 1264.
- 14 383 source polygons -> 13 440 merged -> **13 804 native faces**, 21 602 vertices (38 cracks welded, 2026-10-31); 400 faces with no air in front
  dropped (`work/dropped_faces.json`: undersides of the pillar bases and trims, faces between brushes; no thin
  partition among them; `thin_walls` is on).
- **7 rooms** (+ sector 0): the porch and the hillside, the narthex, the two towers, the nave, the courtyard with the
  cloister and the east wing, the transepts, choir, galleries, attic, organ loft and bell tower. One air component, no
  leak; the courtyard and the hillside are open to MM9's sky box (`skymarker` faces).
- **13 portal faces**: 8 MM9 UserPortals (the nave doors, the tower doors, the monks' door) and 5 of the `front_wall` cut
  (the narthex's front wall: two door arches, two high windows, the west low window). `front_wall_4` (the east low
  window) has the porch's air on both sides and is not used. Floor check 442 LT² (door sills).
- **40 movers**: 10 `rotate` leaves (2 double nave doors, 6 single doors, MM9's swing and auto-close), 25 organ keys and
  5 bell ropes (`dat`, MM9's MoveDir, MoveDist and Speed).
- **7 ladders** (scene `ladders`): the two towers (144 -> 632), library and scriptorium (384 -> the attic 896), the
  crossing attic to the bell floor (896 -> 1264), the two transept ladders (0 -> 384, through holes in the gallery floor).
- **106 BLV lights** of MM9's 126 (+20 over the four-per-point cap light the bake only) and its 264 `DirLight`s in the
  bake. Light coverage: at most 4 per floor point.
- **125 decorations** (props.json: 101 props, 22 wall torches, the candle, Thjorad), **0 chests** (MM9 has none here),
  **27 actors** (18 Initiates, 7 Monks, 2 Reverend Monks), 0 pads.
- Outline budget: the hillside's 1 507 up-facing faces are compiled invisible (`TRIGGER_detail_*`, outside the 7 000
  outline bitset) and drawn again by `face_attribute_overrides` at load (the Chasm of the Dead's route).

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP`, `WorldObject0-7, 9, 42`, `Carpet0-22`, `InvisibleBrush0-7`, `Terrain0` | static world; carpets and the ladders' rung meshes static; invisible collision; the hillside built (seen through the front door; InvisibleBrush5 and the exit keep the party in) |
| `skymarker` | `sky04` stretched (0.2 texel/LT), the bake's sky emitter (display 1.1) |
| `soundonly.dtx` (the fountain garden's solid sound-only box) | invisible collision, as MM9's PhysicsBSP has it solid |
| `RotatingDoor` `anavedoor1/2`, `bnavedoor1/2`, `RotatingDoor0-5` | `rotate` movers, one per leaf, MM9 pivot, angle, speed, open-away; doorway portals at the UserPortals |
| `Door` `A1` ... `E3` (25 organ keys) | `dat` movers 2 LT down, each a click plays its note (`OpenStartSound` Sounds\Music\<note>.wav) |
| `Door` `Rope1-5` | `dat` movers 32 LT down: a pull rings its bell (OpenTrigger0 `use`) |
| `Ladder0-5`, `Ladder10` | scene `ladders` (`overrides.yml`) |
| `Prop`, `WallTorch`, `CandleProp` | 3D decorations (props project); the bells, the scrolls, Thjorad and the book are their own entities |
| `Initiate`, `Monk`, `ReverendMonk` | 27 actors, monster rows 583/584/585 (the replacement table's Novice/Initiate/Master Monk), MM9's bodies (monk.abc 11 x 36 LT, PeasantMale.abc 12 x 34 LT, x 2.56), friendly, each with its RUDE id |
| `StartPoint0`, `ExitTrigger0` | start 0 in the narthex facing north; MM9 positioned exit to Lindisfarne (LindisfarneExit) in the porch |
| `ScriptObject` `BellControl`, `MONK_HOSTILITY` | the map Lua (bell order, the hostility map variable) |
| `Fog0/1`, `WeatherMan0` | no fog: neither starts on and `WorldProperties` has no `EnableFog` (MM9 switches them only by WeatherMan) |
| `AIRail` (131), `Marker` (8), `AmbientSound` (7), `OutsideDef0`, `SkyPointer0`, `TOD_Sky0`, `SkyBox0`, `DemoSkyWorldModel` | not built (AI helpers, sky; the markers' positions are used by the Lua) |

## Scripted objects (`worlds/mm9/events/maps/lindisfarnemonastery.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **Monks' hostility** `MonkHostility.inc` (every monk, NPC282/283/420, ThjoradMonk), `MONK_HOSTILITY` | the monks are friends until the party hurts or kills one (damage/killed hooks): `alarmbell.wav`, map variable `MonksHostile`, both monk groups hostile, talk blocked (BlockRude), Thjorad on. Robert Aefgil (no MonkHostility) stays out of it |
| **Bells** `LindisfarneBell.scr` (Bell1-5, p2 the note), the ropes' OpenTrigger0, `LindisfarneBellController.scr` | a rope pull or a click on a bell rings it (`churchbellring*.wav`); Bell1 starts the order, each next bell must follow (else Reset); Bell5 after Bell4: 2000 experience (once), key 9507, the peal (Bell1-5 half a second apart), the Thjorad monks go to pray at Thjorad0-3, Thjorad on. The order is Rope1, Rope5, Rope2, Rope4, Rope3 |
| **Thjorad** `Thjorad.scr` | on (key 9507 or the monks hostile): with key 2 and without 31, key 31; else without 162, key 162; item 197, 1000 experience, gone (also on later loads) |
| **Thjorad monks** `ThjoradMonk.scr` (p1 marker, p2 rude) | their dialogue (434, 423, 422, 421) until they go to pray (AtPrayer) |
| **Organ** (the 25 key Doors), **organist** `NPC420.scr` | each key plays its note and rises a second later; the organist's dialogue end with key 9506 plays the hymn (`HeroesPipe441.wav`) and takes the key |
| **Grehgknak** `NPC282.scr` | dialogue end: `:giveletter` (key 228 without 229: key 229, item 419), `:paladins` (key 236 without 237: 63 000 experience, quest sound, `:PromotePaladin` for each character holding key 421-424 (key taken), 5 000 gold, key 237) |
| **Abbot Leffery** `NPC283.scr` | dialogue end: `:MissingRelic` (key 341 without 342: item 368 taken, 3 000 gold, 80 000 experience, key 342); `@M 5 : 00 Givekey`: the first 5:00 after the abbot agreed (key 253) gives key 254 |
| **Robert Aefgil** `NPC284.scr` | hidden (invisible, not solid) without key 254, gone with 255; appears with 254 (checked every 3 s) |
| **Letters** `BookLetter.scr` "470"..."473 Letter" (Prop5-8) | `evt.SimpleMessage` with MM9's text (Prayer to Igdra, Letter to mother, Letter to Abbot Leffery, Thjorad) |
| Monks `MonkGuardBasic.scr` (p0 type, p1 rude) | their RUDE dialogues; types -1 (chat), 3 (hammer), 4 (wash) stand (`immobile`), 0-2 (pray, hoe, broom) wander |

The dialogues are MM9's own RUDE rows (`GameplayDialogController::activateMm9ActorDialogue`); the use events (53000 +
object index) block talk while the monks are hostile, and the exit events (50000 + object index) run each NPC's
`OnRudeExit`. `mm9_scr_to_lua.py` rejects these scripts (wait, trigger, object handles), so their callbacks are written
here, each citing its routine.

**Unmatched** (not carried, with reasons): the monks' work and prayer animations, their wandering to MarkerHoe0-2 and the
prayer walk (MM9 walks the Thjorad monks; here they are set at their markers); `StartPrayer`/`StopPrayer` on
`gotopray` (nothing sends it in this map); the hammer, hoe, broom and cloth props they hold (AttachProp); the bells'
swing (`PlayAnim Ring`: decorations do not animate) and the 3 s re-ring guard (Counter); `book.scr` (Book0 only
animates its pages: no text, nothing to carry); `PropAnim.scr` on the stone benches (its "NS" quarter turn is baked
into their yaw by the props project); the NPCs' voice lines (`voices\NPC\NPC_282.wav` ...); `AmbientSound` (chanting,
fountain, birds, the organ's 45-180 s hymn loop: a later pass); `WeatherMan` fog switching.

## Engine change (built 2026-10-31 00:45 by the orchestrator)

`evt.SetMapActorPosition` did nothing indoors: `IndoorWorldRuntime` did not implement `setMapActorPosition` (only the
outdoor runtime did), so the Thjorad monks could not go to pray (and Drangheim Prison's gate guards never stepped aside,
Inventa Storca's and the Training Hall's moves were no-ops). `IndoorWorldRuntime::setMapActorPosition` finds the point's
sector, stands the actor there with `placeMapActorAt` and makes it the actor's home. Unit test: "evt.SetMapActorPosition
indoors stands a walker at the point and makes it its home" in `tests/IndoorActorFlyingRuntimeTests.cpp` (hive.blv). No
MM6-MM8 script calls it (grep of `assets_dev/engine` and the MM6-MM8 worlds). The test is in `openyamm_runtime_tests`
(passes, 16 assertions); `openyamm_unit_tests` 2396/2396 pass.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_lindisfarnemonastery.yml`:
**direct 0.42, bounce 6, ambient 0.5, sky_scale 0.03**, 128 samples, `dirlights: true` (MM9's 264 DirLights), `max_lighting: 1`
(MM9 clips at x1), 20 bake-only lights, the sky faces (`sky04`) an emitter (1.0, 0.97, 0.9) shown at 1.1. Sector minimum
light **31** (`map.ambient`): no frame ambient is subtracted from the decorations' light (the Inventa Storca workaround);
the bake keeps its own floor with `ambient_scale`. `stale_bakes.py --check` does not list the map.

## Brightness

**Lightmap-matched** (no real MM9 screenshot of this map exists; `devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`: MM9 draws
walls as texture x lightmap x1). Lightmap texel luminance, ours / MM9's DAT lightmaps per zone (`hue_zones.py`,
`work/zone_ratio_final.txt`; measured with the sky faces at a neutral 0.3, since MM9's skymarker faces carry no lightmap
and our sky emitter's own faces at 1.1 would count as wall): narthex 0.40/0.36 **x1.12**, west tower x1.09, east tower
**x1.29**, nave x0.96, transepts x0.94, library and scriptorium x1.10, choir x1.06, attic and organ loft x0.95, bell
tower **x1.31**, courtyard x1.04, east wing x0.84, hillside x1.13. Two zones are over 10 % +20 %: the east tower and the
bell tower, small rooms each lit by one large MM9 fill light (Light15, Light93, radius 700 LT) that our bake carries at
full strength. MM9's lightmaps here are almost neutral (B/R 0.95-0.99) and fairly even (0.30-0.42 everywhere): its 264
white DirLights (BrightScale 0.9) light the monastery; ours are a little warmer (B/R 0.86-0.92) where the orange wall
torches add up. The real MM9 also adds the torches' dynamic light on top (RE), so on screen MM9 should read warmer and
brighter than its lightmaps near them; not checked against a real shot.

Screen means (centre crop, 35 views, `work/brightness_v03.txt`): old-import capture 92.0, native unbaked 62.0, **native
baked 51.6** (x0.56 of the capture, as the other lightmap-matched maps: the capture is not a brightness reference).
Courtyard views 63-74 (the capture 80-88), the nave 46-51, the attic and organ loft 22-24 (MM9's lightmaps make the
attic the darkest zone, x0.95 there).

**Decorations under the bake** (`work/prop_gap.py`, `work/prop_gap_v03.txt`): with sector minimum light 31 the props read
as bright as or brighter than the walls: the crossing's pew 0.96 of its wall, the choir's pews 1.73, the scriptorium's
desk 2.80 (its white paper and pale wood; the capture 0.72). No black furniture; MM9 itself lights props brighter than
the walls (ModelAdd 30 and full-colour lights, RE).

Sheets (looked at): `review/v03_compare.jpg` (35 views, MM9 original | native baked), `review/lighting_v03_compare.jpg`
(original | unbaked | baked), `review/v02_compare.jpg` (the 16-sample draft), `review/o01_original/` (first look at
the old map), the props' `../../props/mm9_lindisfarnemonastery_claude/review/props_sheet.png`. Flames: `f01_torch_side`
and `f02_torch_front` in `review/v03`: the nave torch's flame card stands on its head from the side and the front.

## Checks

- Scenarios (real clicks for the doors, the organ key, the first rope, the letters, Thjorad and every NPC's dialogue):
  `scenario_doors_exits.yml` **PASS** (the porch raises ExitTrigger0 through the east arch; NaveDoor1 shut stops a walk
  from the narthex, opens on a click and is walked through; the other 7 door groups open on a click; all 7 ladders are
  climbed from their foot onto their upper floor), `scenario_quests.yml` **PASS** (a hoeing monk opens RUDE 296; the
  abbot takes the relic for key 342; Grehgknak's letter (key 229, item 419) and paladin end (key 237); the organist's
  hymn takes key 9506; Robert is hidden, and after key 253 a day's advance gives key 254 and shows him),
  `scenario_immobile.yml` **PASS** (the 18 immobile NPCs and working monks hold their places for 30 s),
  `scenario_scripted.yml` **PASS** (on the build of 2026-10-31 00:45 with the engine change; the four letters; the organ's C2 key goes down and rises; Rope1 lowers;
  a wrong bell order gives no key; Thjorad gives nothing before the bells; MM9's order gives key 9507; the Thjorad
  monks at their prayer markers; Thjorad by a real click gives item 197 and key 162; hurting a monk turns the others
  hostile).
- Walkability (`work/walkability.json`, `work/audit.log`): 190 steps, 2 flights, 19 mover notes, 1 actor note, 1
  unreachable region. The steps are the 16 LT (41) edges of the choir and altar platforms, the stairs of the east wing
  (24 LT risers, 246-369 at its west stair) (144 LT landing); the flights are that stair's top. The
  unreachable region is the fountain's basin inside its solid sound-only box (0.03 M units², 100 above the grass:
  MM9's PhysicsBSP keeps the party out too). Mover notes: the organ keys sit in their keyboard's recess; the east tower's two doors' tops lie under the loft floor.
  Actor note: the organist sits against the organ (MM9 places him there). **No actor is cut off from the party
  start**: every monk stands in a region the audit joins to it, so no reach probes were needed.
- Floor check: 442 LT² of floor under another room's air (door sills of the narthex and transepts).
- Faces: `work/mixed_faces.json` (329, 209 with a minority over 20 %) are the long walls and the courtyard grass along
  the room borders; no hole seen in the 35 review views.
- All four scenarios rerun on the final build: PASS. The Thjorad click, the letters, the organ key and the rope are
  real interact hits (events 75-79, 142, 91 in `work/scen_scripted.log`).
- Compiler unit tests not rerun (the compiler is unchanged).

## Deviations from MM9 and why

- **No AI scripting**: monks stand or wander at their DAT places; MM9's work and prayer animations, paths and attached
  tools are not carried (PLAN.md: no native patrols).
- **Thjorad monks** are set at their prayer markers instead of walking there.
- **The bells** swing (2026-11-10: the bell part and clapper play Ring, then Stop; cogs 311-315, timers 271-275) and
  ring their note on the clips' BellBing/BellBong keys (0.4, 1.2, 2.366, 3.233 s from BELL.abc); each reports to the
  controller 5 s after its use, as MM9's StopDone. The note is not positional (MM9: radius 200-1000 LT at the bell), a
  bell is not rung by damage (OnDamage OnUse), and Ring starts from its first frame (17 degrees) without MM9's blend.
- **The hillside** is built only to be seen through the front door; its faces are invisible to the outline pass
  (minimap), drawn at load.
- **The courtyard trees** have a trunk collision (radius 30); MM9 lets the party walk through its trees.
- **Sky**: `sky04` instead of MM9's SnowMtns sky box.
- **Robert Aefgil** appears on a 3-second check of key 254 instead of MM9's `@M 6 : 00`.

## Open items

- MM9 models for the monks (Initiate, Monk, Reverend Monk) draw the BMonk sprite rows (another session builds models).
- Ambient sounds (chanting, the fountain, birds, the organ loop); the NPC voice lines.
- A density and pack pass (PLAN.md: later); x4 textures last.

## Not checked

- Monster behaviour once hostile beyond the scenario's hostility bit (combat, the immobile NPCs fighting in place);
  Robert Aefgil walking; monks wandering into each other.
- The bells' and organ's sounds heard in a running game (all runs use the dummy audio driver); the hymn's length.
- Arrival from Lindisfarne by walking its ExitTrigger0 (the transition row's arrival is the start's floor).
- A desktop playthrough with real input; save/load after the bells and after Thjorad; Android.
- A thin dark line along the cloister's south window reveal in `g13_cloister_south` (baked view; one face edge), not
  traced.
- The blotchy light on the tower floors (`g16`, `g17`): the bake's DirLight cones at 128 samples; not traced.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:18:54 (convert.py from the current shared converter, end 15:20:48): 23 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 13790 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_doors_exits.yml` pass, `scenario_immobile.yml` pass, `scenario_quests.yml` pass, `scenario_scripted.yml` pass.
Stair probes (`scenario_stair_probes.yml`, `../mm9r_common/stair_probes.py`): 6 walks up the ramps over dropped bottoms, before / after (xy, z native): [86.0, 0.0] / [86.0, 0.0]; [58.0, 0.0] / [58.0, 0.0]; [86.0, 0.0] / [86.0, 0.0]; [58.0, 0.0] / [58.0, 0.0]; [85.339, 0.0] / [85.339, 0.0]; [213.339, 0.0] / [213.339, 0.0]; 0 walk farther after the rebuild.
Blocker probes: 8 walks into helper brushes resting on the floor stop short of them, 8 identical before and after (their sides still block).
Its 11 faces with `Misc\Firethrough.dtx` (7 MM9 polygons of InvisibleBrush6 with flags 0x109, no invisible bit; the magenta "FIRE THROUGH" marker filling a pointed window) are now invisible like every other map's (`source.HELPER_TEXTURES`): the scene export shows 0 visible Firethrough faces (11 before), and five views of the window (`review/firethrough_check/sheet.jpg`, looked at) show no magenta.

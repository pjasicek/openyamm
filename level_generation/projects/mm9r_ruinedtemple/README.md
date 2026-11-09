# MM9 rework: Ruined Temple (`ruinedtemple.blv`)

MM9's Ruined Temple (off Frosgard, monsters L16-79: skeletons and Dagrells) converted from its DAT world into a native
indoor map (BLV: sectors, portals, linear movers, a ladder, lights, exit volume) on the shared dungeon converter
([`../mm9r_common/dungeon`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_ruinedtemple_claude/README.md)). Status 2026-10-30 (overnight run): geometry, rooms,
doors, every scripted object, lights, exit, 68 decorations, 3 chests, 15 actors (the genie hidden until called), baked
lighting calibrated per zone on MM9's DAT lightmaps. No converter or engine change.

The temple: the party arrives on the upper floor of the entrance hall, beside the exit to Frosgard. A glass skylight box
stands over a hole in that floor; coming near it breaks the glass and its frame, and the way in is down through the
hole into the hall below. North, up a stair and through the altar door, lies the main temple (a sunken floor with the
genie's lamp, a gallery with the locked LeftDoor); east, room 3 and the hidden door to the spiral room and the chest
room; north, the diagonal corridor to the pew hall, the elevator room and its symbol-button puzzle; below, the prison
corridor, the crypt hall with the Tree of Life's cell, the counterbalance and the crypt, the shaft of dirt plugs, the
shaft bottom and the spiral ramps up to the tunnel behind the cell.

## Build and review

```sh
python3 level_generation/projects/mm9r_ruinedtemple/analyse.py           # DAT survey: work/analysis.json, dat_objects.json
python3 level_generation/projects/mm9r_ruinedtemple/convert.py --plan    # rooms only (7 s)
python3 level_generation/projects/mm9r_ruinedtemple/convert.py           # build, compile, install (10 s)
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_ruinedtemple                          # bake (about 2 min)
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_ruinedtemple   # hue
python3 level_generation/projects/mm9r_ruinedtemple/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_ruinedtemple/scenario_$s.yml --scenario-no-color; done
for s in reach_ramps reach_monsters; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_ruinedtemple/work/$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_ruinedtemple
python3 level_generation/projects/mm9r_ruinedtemple/make_tour.py v08 [--original]       # 34 eye-level views
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated ruinedtemple_v08 --world mm9 --map ruinedtemple.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position 0 -858 -1719 --yaw-radians -1.5708 --pitch-degrees 0 --warmup 3 --seconds 150 \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_ruinedtemple/review_tour_v08.yml
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated ruinedtemple_v02orig --world mm9 --map ruinedtemple.odm --assets "$PWD/output/mm9_rework/assets_original" \
    ... --set video.view_distance=unlimited --set debug.screenshot_tour_path=.../review_tour_v02_original.yml
cd level_generation/projects/mm9r_common && python3 -m dungeon.sheet ../mm9r_ruinedtemple/review/v08 ../mm9r_ruinedtemple/review/v02_original
python3 level_generation/projects/mm9r_ruinedtemple/tools/views.py review/v02_original review/v08   # per-view brightness
```

Review: [`review/v08_compare.jpg`](review/v08_compare.jpg) (34 views, MM9's bmodel_world map left, native BLV baked
right), [`review/v01_compare.jpg`](review/v01_compare.jpg) (the same views before the bake), lighting
[`review/lighting_compare.jpg`](review/lighting_compare.jpg) (MM9 | unbaked | baked). The tour folders v03-v07 and props_* are the
calibration steps (below).

## Files

- `overrides.yml`: every DAT world model's rule, the sky marker texture, `seed_exclude`, the ladder; `convert.py`: the
  population, the perception hints, the light colours, the genie, every script (a `dungeon.Hooks` subclass);
  `analyse.py`, `make_scenarios.py`, `make_tour.py`, `hue_zones.py`, `tools/` (`leak.py`: seeds of air components
  touching the border; `probe.py`: polygons in an LT box; `views.py`: per-view brightness; `lightmap_ratio.py`; `prop_crops.py`), `scenario_*.yml`,
  `review_tour_*.yml`, `review/`.
- `props.json`: 68 placements from the props project; `work/`: `build_report.json`, `doors.json`, `lights.json`,
  `content.json`, `walkability.json`, `rooms_<level>.png`, `runtime/`, `reach_ramps.yml`, `reach_monsters.yml`,
  `hue.txt`, `lightmap_ratio.txt`, `brightness_v08.txt`, `teal_check.txt`, `model_lighting_props.txt`, `decoration_vs_wall.txt`, scenario logs.

## Numbers

| | |
| --- | --- |
| Frame | `native = (LT.x, LT.z, LT.y) x 2.56`, no offset (the old map's frame) |
| Geometry | 2 683 source polygons -> 2 586 merged -> **3 724 native faces**, 5 826 vertices; 105 faces with no air in front dropped |
| Air | sealed (`leaked_to_border` 0) once the three relay triggers parked above the roof (`DBEffectsTrigger0-2`) and the genie's sealed closet are out of the seeds; 1 seeded component |
| Rooms | **9 + sector 0**; median 378 faces, largest 1 148 (the main temple with the pew hall and the diagonal corridor); no archway cuts needed |
| Portals | **10 faces**: 5 UserPortals (HiddenDoorPortal, HiddenDoorPortal2, LeftDoorPortal, PrisonPortal, PrisonPortal2), 5 from door leaves (AltarDoor, UpDoor, HiddenDoor3, PrisonDoor, DoorCryptEscape0); every portal joins two rooms |
| Movers | **43 DAT models in 33 groups, 54 mechanisms** (11 invisible collision parts): 10 doors, 17 buttons, the lift, the cell's door and bars, 9 destroyed glass and planks, the counterbalance, 4 cave-in rocks. The 6 dirt plugs, the crypt lid and the 4 rails and ceiling pieces are scene destructibles (`motion: break`, 2026-11-06) |
| Lights | 67 `Light` -> **65 BLV lights** (colour x BrightScale, fitted to MM9's lightmaps: Baked lighting); props and actors use MM9's model lighting (Prop lighting); `Light20`, `Light21` over the four-per-point cap light the bake only; at most 4 per floor point |
| Decorations | **68**: 22 wall torches and 8 chandeliers (blue flames), 6 banners, 6 pews, 5 bone piles, 5 barrels, a crate, 3 chests, 4 debris heaps, 2 urns, the podium, 2 scrolls, the lamp, the Tree of Life, the skeleton in the crypt |
| Actors | **15**: Skeleton Warrior 4, Skeleton 3, Skeleton Master 3, Dagrell 2, Spectre Dagrell 2 at MM9's body size (below), and the Colloidal Warrior genie, hidden |
| Translucent faces | 211: 108 webs (0.7), 43 glass, chain and ladder faces (texture alpha, two-sided), 60 perception hints (0.35) |
| Exit | `ExitTrigger0` (object 324) to Frosgard, just north of the start; arrival facing south (270) |

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP` | static world; `VisBSP` only for its 5 UserPortals |
| `AltarDoorLeft/Right`, `UpDoor`, `PrisonEntrance`, `PrisonEntrance2` | doors, MM9's linear motion and speed, a click each. MM9's auto-close after 5-6 s is not carried (linear doors toggle) |
| `LeftDoor` | the same, MM9 `Locked` until HiddenDoor2 has opened (its OpenTrigger) |
| `HiddenDoor`, `HiddenDoor2`, `HiddenDoor3` | secret doors, MM9's 88 LT up (HiddenDoor3 down) at 100, shut again after 10 s (CloseWaitTime) |
| `SunButton`-`SunButton4` | the buttons ride their door (MM9 `AttachTo`): each slides with it; their own 7.5 LT press is not shown |
| `MoonButton1/2`, `DiamondButton1/2`, `StarButton1/2`, `SecondButton`, `HiddenButton(2)`, `PrisonButton2/3` | MM9 Door motion (3-4 LT in), click events |
| `MainElevator` (`Lift`), `MainButton` | a linear mover 216 LT down at 60 LT/s; the button rides it |
| `PrisonBars`, `PrisonDoor`, `DoorCryptEscape0` | the cell's bars and door (88 / 80 LT up at 20) and the escape slab (120 LT at 25), no click (MM9: not PushOpen) |
| `DestructableBrush6`, `glass1-8` | the skylight box's frame and glass over the hole: dropped out of sight when MM9 destroys them |
| `DB_Crypt0`, `DestructableBrush0-5`, `DB_RailLeft/Right`, `DB_CeilingLeft/Right` | the crypt lid (500 hp), the shaft's dirt plugs (20 hp), the cave-ins' rails and ceiling (500 hp): scene destructibles 345, 339-344, 363/362, 380/379 (cogs 20000 + index); weapons break them as in MM9, the scripts below destroy them, a click breaks a plug (events 38339-38344; the others take no click) |
| `WO_CounterBalance`, `CaveInLeft/Right(B)` | MM9's `MoveToPos` as a slide to the script's marker at its speed (300 / 220 LT/s) |
| `DBFloor`, `DBFloor0-2` | not built: coplanar copies of the floor under them (MM9 shatters them into the same ruinfloor), they would z-fight |
| `RopeWheel` (`RotatingBrush`) | static: the portcullis winch |
| `Transparent Bars`, `WorldObject*` chains and webs, `InvisibleBrush0/1`, `WorldObject9` | static; the webs non-solid; invisible collision |
| `AIBarrier0/1` | not built: they stop only MM9's AI (monsters off the skylight); built, they would wall the party out |
| `Ladder` | a real ladder from the crypt floor through the hole in the chest room's floor |
| `PerceptionBrush0-10` | untouchable translucent faces at 0.35 with a cog each, shown to a party with Perception 8 (MM9's PerceptionValue) unless MM9's wiring switched the brush off |
| `Light`, `StaticSunLight0`, sky markers | BLV lights; the 7 sky faces over the skylight draw MM9's Clouds1 sky (`CLOUVKSJD0`) and are bake emitters, with the skylight's glass |
| `Prop`, `CandleProp`, `Barrel`, `BonePile`, `DestructableProp`, `TreasureChest` | 3D decorations; every `CandleProp` is `Blue 1`: blue flames |
| `Fire` (`DustObject0-6`), `EarthQuake` (6) | script only: `evt.CameraShake` and an `mm9:smoke` puff where they fire (Camera shake); DustObject3-6 (the floor slabs under the fallen rocks) and QuakeObject1 (no sender) are not built |
| `AITrk`, `AIRail`, `Marker`, `AmbientSound` (5), sky objects | not built |

## Scripted objects (`worlds/mm9/events/maps/ruinedtemple.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **The skylight**: `Trigger0`, `Trigger1` (each triggers the other) | the party near the box (Trigger1's box widened by 100: the frame's low lattice stops the native party short of it) drops the frame and the nine glass panes; the party goes down the hole |
| **Hidden doors** (door wiring): `SunButton`-`SunButton4`, `HiddenDoor(2,3)`, `HiddenButton(2)`, `LeftDoor`, `PerceptionBrush0`, `PerceptionBrush10` | SunButton opens HiddenDoor and SunButton4 HiddenDoor2 (the hint goes off while open); SunButton2/3, on the doors' far sides, are their DoubleDoorName pairs and open them from there (fixed 2026-11-08: as decoys they shut the party in below); each door shuts after 10 s; HiddenDoor2 unlocks LeftDoor; HiddenButton or HiddenButton2 opens HiddenDoor3 |
| **The elevator**: `SunTempleButtons.scr`, the six symbol buttons, `MainButton`, `SecondButton`, `PerceptionBrush1/2` | each symbol button toggles in and out and toggles its symbol; the main button sends the lift when Star1 and Diamond2 are set and the rest are not (the two hinted buttons); SecondButton at the shaft's foot calls it; each sends it to the other end |
| **The crypt**: `RT_CounterBalance.scr`, `PrisonButton2`, `DB_Crypt0`, `DestructableBrush0-5`, `PerceptionBrush3-9`, `PrisonButton3`, `DoorCryptEscape0`, `PrisonDoor`, `PrisonBars` | PrisonButton2 drops the counterbalance onto the crypt lid, `evt.DestroyDestructible(345)` (its destroyed event 244, also on a weapon break: TriggerHostile0, `CryptOpen`); weapons or a click break each dirt plug (destroyed events 230-235: `Broken<plug>`, its hint off) and the party drops to the next; PrisonButton3 in the tunnel raises the escape slab, which then opens the cell |
| **The Tree of Life**: `TreeofLife.scr` | a world item (`dungeon/pickups.py`, item 241), hidden with key 256; its pickup gives key 256 and arms TriggerCaveIn1 |
| **Cave-ins**: `RT_CaveIn.scr` on `CaveInLeft/Right(B)`, `TriggerCaveIn0` (on at start), `TriggerCaveIn1` (armed by the Tree) | the rails or the ceiling break and the rocks drop onto MM9's markers, half a second (left) and a second (right) after the trigger |
| **The genie**: `GenieCrystal.scr` (the lamp), `ColloidalGenie.scr` (`Genie`, dialogue 435) | a click on the lamp calls the genie once: 2 s later it stands in the smoke over the lamp; a click opens dialogue 435, whose rows set keys 5022-5025; closing it grants 5000 gold, 5000 experience, a random item 234-238 or Might +10 (the active member), and the genie vanishes 3 s later |
| **Scrolls**: `BookLetter.scr` on `Prop7` (502), `Prop8` (503) | a click shows MM9's text ("Excerpt from Book", "Diary Entry") |
| `PropAnim.scr` on the six pews (`onside`) | nothing to do: `pew3NS.abc` has no `onside` animation, MM9 shows them upright too |
| `TriggerHostile0`, `DBEffectsTrigger0-2` | relays of the dust and quakes (Camera shake); TriggerHostile0 also sets a map variable |

All of MM9's Trigger volumes are boxes polled four times a second (any part of the party: the box grows by the party's
37-unit radius), each once. Map variables keep the state; one-shot timers are armed by a variable (playbook).

## Camera shake (2026-11-06)

MM9's EarthQuake and dust objects as `evt.CameraShake` and an `mm9:smoke` puff in the handlers of what sets them off
(`convert.py` `effects_lua`, the rule of devdocs/mm9_rework/MM9_CUTSCENES.md section 5: intensity
min(ShakeAmount, 12) / 12, seconds QuakeDuration + min(ShakeAmount, 12) / DecayRate, felt within OuterRadius of the
object; InnerDamage is 0 everywhere). No cinematic: the temple has no camera.

| Sender | What fires | Shake |
| --- | --- | --- |
| `TriggerCaveIn0` / `TriggerCaveIn1` (volumes) | QuakeObject0 / QuakeObject2 at once, with the cave-in's fall | 1 for 6 s, radius 1792 |
| DB_RailLeft/Right (0.5 s, 1 s after TriggerCaveIn0), DB_CeilingLeft/Right (after TriggerCaveIn1): destroyed by the timers or by weapons | their destroyed events 245-248, DBEffectsTrigger1 / 2: DustObject1 / 2 and DBQuakeObject1 / 2, once per brush | 1 for 6.7 s, radius 1792 |
| `TriggerHostile0` (DB_Crypt0's death or the party at the shaft's foot, whichever first, once) | DBEffectsTrigger0: DustObject0, DBQuakeObject0 | 1 for 7 s, radius 1024 |

The DBEffectsTriggers are relays MM9 parks above the roof (never touched). Without a conversion, `shakes_pilot.py`
writes the installed Lua with these changes into the scratch root `output/mm9_rework/cinematics_pilot_root`;
`scenario_shakes.yml` (run from `output/mm9_rework/cinematics_pilot_run`) checks each handler runs through its shake
(the crypt, both cave-ins); captures in `output/mm9_rework/cinematics_pilot_run/captures_ruinedtemple_shakes/`
(`sheet.jpg`; the stills show the dust puffs, not the tremor).

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` bakes `ruinedtemple.lighting` / `.bake.json` from the 65 BLV lights and the 2 over the
cap (profile `tools/lighting/baked_indoors/profiles/mm9_ruinedtemple.yml`: 64 samples, 3 bounces, **direct 5.0, bounce 3,
ambient 0.55, sky 1.2**, `max_lighting` 1; emitters: the sky faces and the skylight's outward glass). One 4096 x 538
page, 2 543 charts, about 2 minutes of Cycles. `stale_bakes.py --check` does not list the map.

**Reference: MM9's DAT lightmaps (the user's decision, 2026-10-30), for brightness and hue, dark rooms staying dark.**
MM9 draws walls as texture x lightmap x1 (`devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`). The old-import capture is not a
brightness reference (on Verhoffin Ruins it measured 94 where real MM9 shows 62); no real MM9 shot of this map exists.
Per zone (`hue_zones.py`, `../mm9r_common/hue_vs_lightmaps.py` -> `work/hue.txt`, `tools/lightmap_ratio.py` ->
`work/lightmap_ratio.txt`): texel luminance ours / MM9, and B/R, G/R MM9 / ours:

| Zone | Luma ours / MM9 | B/R MM9 / ours | G/R MM9 / ours |
| --- | --- | --- | --- |
| entrance hall | 1.08 | 1.76 / 1.74 | 1.20 / 1.20 |
| south ruins | 0.86 | 2.34 / 1.86 | 1.45 / 1.23 |
| main temple | 1.00 | 1.61 / 1.45 | 1.13 / 1.10 |
| east rooms | 1.00 | 1.96 / 2.08 | 1.27 / 1.27 |
| north corridor | 0.91 | 2.10 / 1.82 | 1.35 / 1.22 |
| pew hall | 1.04 | 2.24 / 2.09 | 1.42 / 1.29 |
| elevator room | 1.22 | 1.82 / 2.58 | 1.20 / 1.53 |
| crypt level | 0.93 | 1.52 / 1.59 | 1.19 / 1.12 |
| shaft and ramps | 0.88 | 1.78 / 1.76 | 1.27 / 1.19 |

Eight zones within 0.86-1.08; the elevator room (the smallest zone, 0.46 M LT² of texels) stays 1.22 and too blue: the
torches beside it (Light7, Light10) light its walls at close range. MM9's lightmaps in every zone are a dark neutral floor
(R 0.19-0.24) with the blue torch light on top; the bake matches that with a low ambient and a strong direct term.

**Light colours** (`convert.py` `blv_colour`, fitted to the lightmaps, map-specific): MM9 weights each Light by its
`BrightScale`, which the shared converter does not carry: the BLV lights are colour x BrightScale. The blue torches
(0 / 128 / 255, BrightScale 0.6) carry **0.3 of their green**: over each zone's floor they add +0.04 green to +0.16 blue in
MM9's lightmaps (G/B 0.26, not 0.5). At 0.5 the zone means matched but the pools round each torch, where the bake's blue
clips at x1 and its green keeps rising, read teal (2026-10-31: top 5 % G/B 0.83 against MM9's 0.57 in the south ruins).
The white fills (BrightScale 0.2-0.6, over the main temple, the pew hall, the crypt level) carry **a quarter**: in MM9's
lightmaps they add only 0.02-0.04 red over the floor; at colour x BrightScale they gave 0.12-0.14. The two bake-only
lights get the same fit (`work/lights.json` `colour`, the authored one in `colour_authored`).

**Teal check** (`work/teal_check.txt`, G/B of the lightmap texels, MM9 / ours): mean 0.62-0.78 / 0.59-0.76 in every zone,
the brightest 5 % 0.57-0.84 / 0.54-0.84 except the crypt level and the shaft (MM9 1.56 / 1.19, ours 0.61 / 0.73: MM9's own
pools there are green, from the shaft's green lights). The views the orchestrator flagged (e04, e05, e07, t02) read blue
now (e05 RGB 23 / 38 / 75; v07 was 24 / 49 / 77).

Calibration history (screen mean of the 34 views, centre crop; the capture's 36.0 only for orientation):

| Step | Profile, lights | Screen mean |
| --- | --- | --- |
| v02 | colours as authored, direct 0.9, ambient 1.6 | 60.9 (unbaked 55.1) |
| v04 | colour x BrightScale, direct 2.6, ambient 0.6 | 38.4 |
| v06 | the torches' green halved, direct 2.8, bounce 3, sky 1.2 | 34.3 |
| v07 | lightmap-matched: white fills x 0.25, direct 5.0, ambient 0.55 | 32.2 |
| **v08** | **the torches' green at 0.3 (teal pools), model lighting for props** | **28.4 luma** |

**No pitch-black views** (`work/brightness_v08.txt`, Rec. 709 luma of the centre crop): the darkest are the cell 16.6,
the ramps 17.6, the gallery by LeftDoor 19.7, the lift's foot 20.0; none under 10-12, so no player-light stand-in floor
was needed (MM9's `PlayerLightOn` is not carried). The skylight hall stays darker than the capture (e03 luma 29 against
52): MM9's lightmaps do not show the hall brighter than the other zones (entrance hall luma 0.253, the map's median).

## Prop lighting

Under the bake the old path drew decorations far darker than the walls (v07: banners 0.17-0.20 of the capture's prop
luma, the crate 0.14, the chests 0.27; `work/decoration_vs_wall.txt`). The map has capped lights (Light20, Light21), so
both paths were compared on the same props (`tools/prop_crops.py`, Thjorad Mine's method; `work/model_lighting_props.txt`,
prop crop luma as a ratio of the old-import capture, which draws props nearly unlit and so overstates them):

| Prop | old path (v07) | old path, sector light 31 | model lighting x1.67 | **model lighting x4 (v08)** |
| --- | --- | --- | --- | --- |
| banners (lower hall) | 0.17-0.20 | 0.39-0.43 | 0.39 | **0.40-0.41** |
| banner (crypt hall) | 0.20 | 0.39 | 0.38 | **0.40** |
| genie lamp | 0.86 | 1.02 | 0.89 | **0.95** |
| chests | 0.27 | 0.48 | 0.57 | **0.58** |
| crate / barrel | 0.14 / 0.25 | 0.40 / 0.47 | 0.36 / 0.44 | **0.39 / 0.46** |
| pews | 0.39-0.45 | 0.53-0.59 | 0.51-0.53 | **0.46-0.47** |
| podium box | 0.58 | 0.79 | 0.55 | **0.57** |
| sarcophagus (crypt lid, a mover face) | 0.88 | **0.59** | 0.88 | **0.86** |

Kept: **`map: {model_lighting: {light_scale: 4.0}}`** (devdocs/INDOOR_MODEL_LIGHTING.md; scene only, the BLV and bake are
unchanged by it): world ambient 50 / 50 / 70 (the DAT's `AmbientLight`) + ModelAdd 30 + the BLV lights. Sector minimum
light 31 lifts the props as much but darkens the vertex-lit movers (the crypt lid 0.88 -> 0.59), so the old path stays
off. `light_scale` 4: MM9 lights models at full colour without BrightScale, while the BLV colours carry BrightScale and
the lightmap fit (torches 0.6 x green 0.3, fills 0.2-0.6 x 0.25); 1 / 0.6 = 1.67 leaves the white-lit rooms' props under
their MM9 light, 4 brings the fills to about their BrightScale and clamps the torches' blue at 1. The props read
0.4-0.95 of the capture; against the wall beside them (`work/decoration_vs_wall.txt`, decoration / wall, unbaked -> v07
-> v08) the banners 1.29 -> 0.35 -> **1.08** and 0.88 -> 0.25 -> **0.82**, the crate 1.32 -> 0.35 -> **1.04**, the chests
0.84 -> 0.65 -> 0.67, the pews (dark wood against a lit wall) 0.34 throughout: back to their unbaked relation, warmer
than the walls (the banners pink-white, the pews brown).

## Checks
## Checks
## Checks

- `scenario_doors_exits.yml` passes (47 steps): the exit raises `mm9_exit_trigger:324`; walking at the skylight breaks
  it (`FloorFallen`, frame and glass open) and the party drops through the hole to the hall floor; AltarDoor stops the
  party shut, opens on a **click** and the party walks through; LeftDoor stays shut on a click, SunButton4 (click) opens
  HiddenDoor2 and unlocks it, a click opens it; the ladder climbs from the crypt floor onto the floor above.
- `scenario_chests.yml` passes: the 3 chests open by interact from in front of their models.
- `scenario_scripted.yml` passes (205 steps): perception hints at Perception 1 and 8; SunButton2 opens HiddenDoor from the
  elevator room's side, SunButton opens it with both buttons, it shuts after 10 s; HiddenButton opens HiddenDoor3; the elevator does nothing
  with no symbol and with MoonButton2, goes down with StarButton1 + DiamondButton2 (party on it), SecondButton sends it
  back; PrisonButton2, counterbalance and crypt lid; the first dirt plug standing after 19 damage (console), the six broken by **clicks** from the party standing on
  each (2026-11-06); PrisonButton3, escape slab, cell; the Tree of Life by interact (item 241 in the packs, key 256); TriggerCaveIn1
  (party set down in its box: the spiral stair's foot has no straight level approach) and TriggerCaveIn0 (walked into);
  both scrolls; the lamp, the genie appearing, its dialogue by click, the gold wish, the genie gone. Every button, door,
  chest and object above is a real click (`press_interact`) unless noted.
- Party reach (`work/reach_ramps.yml`, passes): from the shaft bottom up the corner stair (41-unit risers) onto the
  landing and up the spiral ramps into the tunnel behind the cell.
- Monster reach (`work/reach_monsters.yml`, passes): Dagrell1 (radius 64) in the spiral room and Skeleton2 in the pew
  hall close on a party in their room; SpectreDagrell0 on the west ramp closes on a party up the ramp in front of it
  (placed behind it, out of its sight, it stays: sight, not geometry).
- Walkability (`work/walkability.json`): 176 steps, 46 flights (the spiral stair and wedge steps), 20 mover notes,
  1 unreachable, 2 pits, 1 actor note, each checked: the unreachable 0.24 M at -2724 is the closed crypt lid's top
  (gone once it breaks); both pits (the shaft bottom, 0.82 M; the tunnel behind the shut escape slab, 1.49 M) hold no
  monster and the party climbs out (reach_ramps; the audit's grid falls between the corner stair's narrow wedge steps);
  the Spectre Dagrell "under a ceiling 1 above it" stands on the west ramp, whose sloped ceiling is 128 LT over it
  (false: the audit takes the ceiling's low end), and it walks (reach_monsters). No "cut off" actor region.
- Thin walls: `work/dropped_faces.json` has no dropped partition with air on both sides (the invisible brushes' dropped
  faces face solid rock, the black faces are the genie's sealed closet); `thin_walls` not needed.
- Floor check: 1 080 LT² of floor under another room's air: HiddenDoor3's sill (863, rooms 6/5) and the ladder hole's
  rim (217, rooms 8/6).
- Mixed faces: 24 with a minority over 20 %. Every review view inspected: no holes. The skylight's glass draws
  two-sided, like MM9's.
- Flames in game (`review/flames/`, `review_tour_flames*.yml`): a wall torch from the front and both sides and a
  chandelier from two sides: the blue cards sit on the torch head and on each candle (`card` billboard).
- Starts: the start stands on the upper floor facing south into the hall (view e01); `stale_bakes.py --check` does not
  list the map. Compiler unit tests not run: no compiler change.

## Bodies

MM9's bodies (the ABC's AnimBinding half extents x MONSTERS.txt Scale 1 x 2.56; `convert.py` `BODY_LT`): Skeleton
38 / 179, Skeleton Warrior and Master 38 / 189, Dagrell and Spectre Dagrell 64 / 148 (radius / height). The shared
rows carry 60-70 / 170-220. The genie keeps its row (it never moves).

## Deviations from MM9 and why

- **The plank floor and its glass drop out of sight** instead of breaking into debris; the other destroyed brushes are
  scene destructibles (stone dust, no debris models). The dirt plugs also break on a click (a killing blow), besides
  MM9's 20 points of damage. The counterbalance does not fall when struck (`OnDamage`).
- **Trigger1** is widened by 100 units: the skylight frame's lattice, 56 LT over the floor, stops the native party (a
  37-unit cylinder) before MM9's party box would reach it.
- **The genie** talks on a click; MM9 opens its dialogue by itself 3 s after it appears. Might +10 goes to the active
  member (MM9's `GiveAttribute 0, 10, TRUE, 0`).
- **The elevator** goes to the other end on each press; MM9's lift is Sticky (stays down) and is left by the ladder.
  `MoonButton1` toggles Star1, as MM9 wires it.
- **The sun buttons** ride their doors but do not show their own press.
- **Doors** do not close themselves after 5-6 s (linear doors toggle); the hidden doors do (script).
- **Dust and quakes**: the quakes follow the DATs' ShakeAmount, not MM9's shipped 0.5 units (the ShakeAmt bug); the dust
  is one `mm9:smoke` puff, not MM9's three-second smoke; the floor slabs' dust (DustObject3-6) is not built.
- **Light colours**: x BrightScale, the torches' green at 0.3 and the white fills at a quarter (Baked lighting), fitted to
  MM9's lightmaps. Props and actors: MM9's model lighting at `light_scale` 4 (Prop lighting).

- **Fixed 2026-11-08 (the MM9 promotion playthrough, block C): the inner sun buttons.** SunButton2 (the elevator
  room's side of HiddenDoor) and SunButton3 (the spiral top's side of HiddenDoor2) were converted as decoys that do
  nothing, so a party that rode the lift down or took the Tree of Life up the spiral was shut in for good (the lift
  and the ladder lead only back to those two doors). In the DAT each is its door button's `DoubleDoorName` pair, and a
  double door's press moves both, as the converter does for every other pair: each now opens its door as its pair
  does (SunButton3 also unlocks LeftDoor). Regression: `tests/scenarios/mm9/ruinedtemple_inner_sun_buttons.yml`.

## Open items

- MM9 art for the Skeleton, Skeleton Warrior/Master, Dagrell and Colloidal Warrior (3 actors draw as placeholders).
- 5 `AmbientSound`s (interior ambience).
- Props under model lighting read 0.4-0.6 of the old capture; no real MM9 screenshot of this map to check them against.
- MM6-MM8 density (PLAN.md: later). No x4 textures (the project's last step).

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:03:56 (convert.py from the current shared converter, end 15:04:16): 9 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 3715 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
Stair probes (`scenario_stair_probes.yml`, `../mm9r_common/stair_probes.py`): 2 walks up the ramps over dropped bottoms, before / after (xy, z native): [1787.297, 0.0] / [1787.297, 0.0]; [0.0, 0.0] / [114.251, 37.247]; 1 walk farther after the rebuild.
Blocker probes: 8 walks into helper brushes resting on the floor stop short of them, 8 identical before and after (their sides still block).

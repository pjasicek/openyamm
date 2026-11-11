# MM9 rework: Dook's Castle (`dookscastle.blv`)

MM9's Dook's Castle (Baron Dook's keep in Guberland, its half-orc militia, the secret door behind the shield and the
caverns under the castle with the rope-bridge lake) converted from its DAT world into a native indoor map (BLV:
sectors, portals, rotating and linear movers, lights, an exit volume, a ladder) on the shared dungeon converter
([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_dookscastle_claude/README.md)). No x4 textures yet.

Status 2026-10-30 (overnight run): geometry, 11 rooms, 7 rotating double doors, the secret sliding door and its button,
156 BLV lights (+18 bake-only, 7 DirLights in the bake), the gate exit, Ladder0, the lake as a wading surface, 96
decorations, 7 chests, 47 actors, the castle's scripted objects and baked lighting. In the review root no actor draws
(Open items).

## Build and review

```sh
python3 level_generation/projects/mm9r_dookscastle/convert.py --plan   # rooms only: work/rooms_<storey>.png
python3 level_generation/projects/mm9r_dookscastle/convert.py          # build, compile, install
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_dookscastle --samples 128
python3 level_generation/projects/mm9r_dookscastle/calib_lightmaps.py <direct> <ambient>   # recompose + zone ratios
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_dookscastle
python3 level_generation/projects/mm9r_dookscastle/make_scenarios.py
for s in doors_exits chests scripted alarm; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_dookscastle/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_dookscastle
python3 level_generation/projects/mm9r_dookscastle/work/reach/make_probes.py      # then run work/reach/probe_*.yml
python3 level_generation/projects/mm9r_dookscastle/make_tour.py v03 [--original]  # lighting<n>: the 15-view subset
bash level_generation/projects/mm9r_dookscastle/work/run_tours.sh v03 [--set video.lightmaps=false]
bash level_generation/projects/mm9r_dookscastle/work/run_tour_original.sh v03     # view_distance=unlimited
python3 level_generation/projects/mm9r_common/dungeon/sheet.py <project>/review/v03 <project>/review/v03_original
```

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame). The castle storey at 160 LT (the gate
  hall rises from 0 by two flights to 176); the caves from -30 down to -1400, the lake's bed at -1920 and its surface
  at -1504 (ClearWater0), the rope bridges -1406 to -1148.
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): unchanged: the lake (`ClearWater0`, SurfaceAlpha 0.9 x Ocean4, no alpha) is a
  wading face with no bed built under it, so it stays opaque.
- DAT: 4368 source polygons (PhysicsBSP and the world objects), 4208 merged; 125 faces dropped as having no air in
  front: the outside of the castle and the caves (56), the tops of the bridges' iron rods in the cavern roof (59,
  WorldObject5), the invisible collision boxes' undersides (9) and one lake tile at the rim.
- BLV: **4588 faces**, 6203 vertices, **12 sectors** (11 rooms), **12 portal faces**, **16 movers** (14 door leaves,
  the secret door, the button's invisible box), **156 lights**, faces per sector max 1313 (the lake cavern) / median 226.
- Content: 96 decorations (26 in the busiest room), 7 chests (6 placed, TreasureChest6 on the lake bed reached by its
  dive pad), 47 actors (17 Half Orc Captains, 4 Half Orc Soldiers, Baron Dook, 11 Trellborgs, 6 winged mutants,
  6 basilisks and 2 King Basilisks), 1 pad (the dive), 3 polled trigger boxes.
- Lights: 174 MM9 `Light` objects, 156 in the BLV, 18 over the four-per-point cap bake-only; 7 `DirLight`s (the throne
  room's six orange window beams and its back light) in the bake (`dirlights: true`); no LIGHTDEFS textures, no fog.

## What each DAT object became

| DAT | Native |
| --- | --- |
| `PhysicsBSP` | the static world; `VisBSP`'s 8 UserPortals are the door portals and the secret door's |
| 14 `RotatingDoor` leaves (7 double doors) | one `rotate` mover per leaf (MM9's 90° swing, 75 LT/s, open-away, close after 3 s, reopen on contact); a click swings the pair; each closes its UserPortal |
| `doorslide` (`Door`) | `dat` mover (MoveDir -x, 176 LT at 45 LT/s), doorway portal `secret doorportal`, no click (no PushOpen; Sticky: it stays open) |
| `Tempbutton` (`RotatingDoor`, all Invisible.dtx) | a `rotate` mover (`Tempbutton_INV`) behind `Sheild0`; the shield's click is its event (Scripted objects) |
| `WorldObject0-4` (carpets on invisible boxes), `WorldObject32-36` (copper chain links) | static faces; `thin_walls: true` keeps the thin chain links |
| `WorldObject5` (the bridges' iron rods) | static faces |
| `ClearWater0` (ShowSurface, `Ocean4.spr`, alpha 0.9) | since the shared water rule (2026-11-06) a scene water volume (fog 1280-5120 black) swum to its bed at -1920 LT, its top non-solid; before: its top as a solid wading face at -1504 LT, cut to the cavern on a 64 LT grid (33 faces), Ocean4's frames animated, the engine's water shader (`ocean_mm9_dookscastle`, colour 70/120/170, review root's `liquids.yml`) and a bake display emitter, so it reads as MM9's blue surface; the bed under it is not built (Deviations) |
| `Ladder0` | a scene ladder from under the lake's surface (160 native, `SWIM_LADDER_DEPTH`; the wading surface without swimming) up to the bridge platform (facing +x, exit at (3610, -1212, 1150) LT) |
| 174 `Light`, 7 `DirLight` | BLV point lights (radius x 2.56, colours as authored) or bake-only; the DirLights bake-only spots |
| 57 `Prop`, 18 `WallTorch`, 12 `Brazier`, 3 `Barrel`, 7 `TreasureChest` | 3D decorations (props project); the chests open containers 0-6 (events 41-47) |
| `HalfOrcCaptain` x17, `HalfOrcSoldier` x4, `Baron`, the cave monsters | actors at their DAT positions, facing 90 − ry, MM9 bodies (ABC extents x Scale x 2.56: dookmilitia 38 x 195, trellborg at 0.9 46 x 198, wingedmutant 46 x 133, basilisk at 0.3 35 x 32, at 0.75 86 x 81, Nobleman 38 x 184); the winged ones (Fly Y) keep their DAT height |
| `StartPoint0` | start 0 (the gate, facing north into the hall); the arrival from Guberland's `ExitTrigger0` |
| `ExitTrigger0` | MM9 positioned transition volume (the gate) to Guberland (`DooksCastleExit`) |
| `Trigger` x3 (`SleepTrigger`, `ScurryTrigger0/1`) | boxes polled four times a second by the map script (they fire on any part of the party, as MM9's; ScurryTrigger0 stands on a slope no pad fits) |
| `ScriptObject DOOK_HOSTILITY` | the map variable `Hostile` (Scripted objects) |
| `AIRail` x58, `Marker` x9, `AmbientSound` x25, `ObjectLight` x6, `OutsideDef0`, `WorldProperties0`, `AITrk*` | not built (AI helpers, ambient sound later) |

## Scripted objects (`worlds/mm9/events/maps/dookscastle.lua`, written by `convert.py`)

| MM9 script | Objects | Native |
| --- | --- | --- |
| `DookHostility.inc` (in `DookGuardBasic.scr`, `DC_sargent.scr`, `DookSleepGaurd.scr`) | the 21 militia | friendly (no hostile/aggressor bit, the row's engagement type kept) until DOOK_HOSTILITY goes: the secret door opens (`doorslide` OpenTrigger `remove`), or the party hurts or kills a guard (`TurnHostilityOn`: the alarm bell, monster damage and killed hooks 96/97). Then groups 1 and 3 turn hostile (`evt.SetMonGroupBit`), the sleepers wake; the load handler reapplies it (`OnPostMiniSaveLoad`) |
| `Tempbutton` OpenTriggers (`doorslide open`, `Tempbutton lock`) | `Sheild0`, `Tempbutton` | event 70 on a click on the shield: the button turns, the secret door slides open (boulderroll, doorlatch02), once (`SecretOpen`) |
| `DC_sargent.scr` (`StartUp`, `WakeGuards`) | `SleepCaptain`, `SleepTrigger` | the box fires event 73 once; timer 200 wakes `HallwaySleeper0-3` one every 3 s (MM9: the sargent walks to each in turn) |
| `DookSleepGaurd.scr` (`LoopAnim Sleep`, `WakeUp`) | `HallwaySleeper0-3` | `dormant` actors in group 3; woken by the sargent, the alarm or a hit |
| `ScurryCreature.scr` (`Hide`) | `ScurryBasilisk0-5`, `ScurryTrigger0/1` | friendly small basilisks; each box (events 74/75) once: `dragonredhop.wav`, `MM9.removeActor` on its three (MM9: they run to HideMarker at six times their speed and vanish) |
| `NPC415.scr` (`:OnUse DoRude 415`) | `dook` (Baron Dook) | `mm9_rude_id` 415, immobile, friendly: a click opens MM9's dialogue 415 (Markel's errand, keys 64/65/138 by the RUDE rows) |
| `BookLetter.scr` (`492 Letter`, `493 Letter 1`) | `Prop5` (the shield room's table), `Prop6` (the throne room) | events 71/72: MM9's letters 492 "Attention all Guards" and 493 "Letter to the Dook" (`BOOK AND SCROLL TEXT.csv`), bookopen.wav |
| (the lake) | `TreasureChest6` on the bed | an ordinary chest on the built bed, opened under water (swimming); pad 76 on the wading surface only with `map: {swim: false}` |

Unmatched: the militia's wandering (`BaseWanderInit`/`Startup`: no native wander paths; they stand, as other maps' guards),
the sargent's walk to each sleeper and the sleepers' cower/fidget animations (`DookSleepGaurd.scr` `WakeUp`,
`GoCower`, `DoFidget2/3`), the basilisks' run to their HideMarkers (they vanish where they stand), `DookHostility.inc`'s
`BlockRude` (no militia dialogue exists to block). NPC415's `OnRude` quest sections are empty in MM9.

## Baked lighting


Profile `tools/lighting/baked_indoors/profiles/mm9_dookscastle.yml`: 128 samples, 3 bounces, `direct_scale` 0.5,
`bounce_scale` 4, `ambient_scale` 0.25, `max_lighting` 1, `dirlights: true` (the throne room's six orange window beams,
233/88/1, and its back light); emitters: the throne room's window panes (`DOOKWZCQ7S`, outward, warm) and the lake's
surface (`OCEABYM7AI`, display 0.75 of a pale blue, strength 0.1: MM9 draws its water surfaces unlit); 18 bake-only
lights. Sector ambient per room (`convert.py` `CAVE_AMBIENT`): the castle 20, the tunnels and north caves 27, the lake
cavern 29. Bake about 6 min through `bake_slot.sh`; `stale_bakes.py --assets output/mm9_rework/assets_dev --check`
does not list the map.

Calibration (AGENT_BRIEF, Brightness: against MM9's own DAT lightmaps, `calib_lightmaps.py`, which recomposes and runs
`../mm9r_common/hue_vs_lightmaps.py` over `hue_zones.py`; `work/calib_lightmaps_final.txt`). Lightmap luminance ours /
MM9's per zone: gate hall 1.06, corridors 0.99, throne room 0.96, west rooms 0.95, east rooms 0.92, upper tunnels 1.62,
north caves 1.29, lake cavern 10.1 (MM9's lake cavern averages 0.017 of full over its bed and walls, which are under
our surface or unbuilt; our zone is the bridges, rim and the water's display, so the ratio says little). Hue (B/R,
G/R MM9 / ours): gate 0.73/0.61 0.96/0.86, corridors 0.62/0.56 0.94/0.85, throne 0.28/0.37 0.67/0.70, west 0.64/0.61
0.98/0.91, east 0.67/0.62 1.00/0.91, tunnels 1.15/1.10 1.08/1.05, caves 1.17/1.10 1.09/1.05: the castle's torchlight a
little warmer than MM9's, the caves' blue a little weaker. The first draft (direct 0.7, ambient 0.6, one ambient level)
measured 1.5-1.7 in the castle and 2-3 in the caves: MM9's caverns are much darker than its castle, hence the per-room
ambient.

## Checks

1. Every DAT world model has a rule (the build stops otherwise); skipped classes listed above.
2. Sealed air: `leaked_to_border` false, one seeded air component. `TreasureChest6` is excluded as a seed (it lies under
   the wading surface). Dropped faces: the castle's and caves' outside, the rods' tops, the invisible boxes' undersides.
3. Portals: 12, each joins two rooms (`portals_without_two_rooms` 0): the 7 double doors, the secret door, and four
   archway cuts (`castle_neck` between the gate hall and the corridor, `cave_west_arm` at the tunnel fork,
   `lake_north` and `lake_west` at the lake cavern's two tunnels).
4. No holes: every view of v01-v03 looked at (v01's c04 and c16 stood on a lintel and in a wall: view picks, moved in v02). Floor check: 1236 LT² of floor under another room's air, the strips
   along the `lake_north` cut (Chasm's note: harmless). Mixed faces: 81 with a minority over 20 %, cave walls along the
   cuts' planes and door jambs.
5. Review sheets: `review/v03_compare.jpg` (37 views, MM9 capture | native baked), `review/lighting01_compare.jpg`
   (15 views, capture | native unbaked | native baked), `review/flames01/flames_sheet.jpg` (a wall sconce from the side
   and the front, a floor brazier from the side, a hanging bowl from below: each flame on its seat),
   `review/v01_compare.jpg` (the first, unbaked pass), `../../props/mm9_dookscastle_claude/review/props_sheet.png`. All
   looked at. Screen means (information only: the capture is the old import in our outdoor renderer, not MM9;
   `work/brightness_v03.txt`): capture 31.3, native baked 28.0 (x0.89); no view under x0.6. Views off by more than
   10 %: c01 0.88, c04 0.85, c05 0.76, c06 0.79, c07 0.76, c11 0.68, c12 0.80, c13 0.87, c14 0.73, c15 0.77, c16 0.87,
   c17 1.15, c18 1.19, c19 0.82, k01 0.82, k02 0.78, k03 0.85, k06 0.80, k08 1.50, k09 1.20, k12 1.15, k15 1.41,
   k16 1.21, k18 0.63 (the dark lake views are a few grey levels either way; k18 looks down at the island's rock, the
   capture's brighter rock face).
6. Walkability (`work/walkability.json`): 0 unreachable, 0 pits (one before the rim ramps: the lake cavern). 36 steps:
   12 of 33-40 in the gate hall (the flights' baluster edges, under the party's 50 step) and 24 at the lake's rim (the
   rock steps under the invisible ramps, which the audit does not follow, and the ramps' own edges); 20 flights in the
   north caves (a 45° bump in the slope from (3960, -1310, 3420) LT, walked through by the probe below).
   9 actor notes: the four sleepers stand at the corridor's pillar plinths (MM9's placements); four "ceiling 1-2 above"
   notes on Trellborg0, KinTrellborg3, Trellborg2 and KingBasilisk1 are false: MM9's polygons give them 192 LT
   (491 native) of headroom over their floors (-236/-44, -962/-770, -1338/-1146, -839/-647 LT).
7. Scenarios: `scenario_doors_exits.yml` **pass** (the gate exit raises its transition; the shut door03 stops a walk,
   opens on a real click, the party walks through, it shuts after MM9's 3 s; all 7 double doors open on real clicks;
   Ladder0 climbs 735 from the wading surface to the bridge), `scenario_chests.yml` **pass** (six chests by interact,
   the seventh by the dive pad), `scenario_scripted.yml` **pass** (a guard 400 off ignores the party; both letters and
   Baron Dook's dialogue 415 by real clicks; SleepTrigger wakes the four sleepers in turn; both scurry boxes remove
   their basilisks; the shield's click opens the secret door, sets Hostile; the guard then closes from 1000 to within
   500 of the party), `scenario_alarm.yml` **pass** (damaging a guard sets Hostile and another guard turns hostile).
8. Starts: StartPoint0 on the gate hall's floor facing north into the castle (first view of the tours).
9. Compiler unit tests: not rerun (no engine or compiler change).
10. Lights: no floor point under more than 4; bake current (`stale_bakes.py --check` does not list the map).

## Can the party and the monsters reach each other

The audit finds no unreachable region and no cut-off actor, so no "cut off" finding needed an in-game test. The lake
cavern was a pit: its rim is MM9 rock steps of 40-48 LT (102-123 native) that MM9's player climbs and the party's 50
step does not (reach probes: from the bridge to the north landing 0 climbed, the landing's upper step 0, the west sill
1). Three invisible ramps (`convert.py` `RAMPS`) lie over them; with them the probes (`work/reach/probe_*.yml`) climb
from the bridge to the north landing (236 up), the landing's upper step (81) and from the west planks into the tunnel
(284). The north caves' steep bump was walked over (654 along, 42 up). The lake's monsters fly (Fly Y), the
basilisks and Trellborgs stand on the cave floors the audit reaches.

## Deviations from MM9 and why

- **The lake is a wading floor.** No swimming yet (PLAN.md Water and diving): ClearWater0's surface is a solid face the
  party walks on, Ocean4's frames with the water shader; the bed (-1920) and the lake's walls under the surface are not
  built. TreasureChest6, on the bed, opens from a pad on the surface over it. Reversible: `convert.py` `LAKE_*`,
  `DIVE_CHEST`, and `seed_exclude` in overrides.yml. A party that falls off a bridge lands on the water (MM9: in it).
- **Invisible ramps at the lake's rim** (above): MM9's player climbs the rock steps; ours needs a ramp.
- The militia stand (no wander paths); the sargent wakes the sleepers on a timer instead of walking to them; the
  scurrying basilisks vanish in place.
- The shield does not turn with its button (decorations do not move); its click opens the door as MM9's button does.
- The lake's per-room light: the caves' and the lake's sector ambient is darker than the castle's (levels 27 and 29
  against 20), so the bake keeps MM9's dark caverns dark.

## Shared converter changes

None. Everything is in this map's `convert.py` (the lake surface, the ramps, the polled boxes, the per-room ambient
through a wrapper of the package writer, the DOORS keys with underscores for MM9's "double door left 01" names).

## Open items

- **Actors draw nothing in the review root** (2026-10-30): the borrowed MM6-MM8 sprite atlases fail there ("requires
  cooked schema 2") and only the winged mutants have MM9 3D models; actors are present (headless reports, scenarios).
- A guard that closes to about 400 of a party in plain view holds there with its targeting flag off (seen in the
  scripted scenario; Drangheim Prison's note); engine AI, not changed here.
- Not checked: a desktop playthrough with real input (the hostility fight, the bridges, the ladder), save/load after the
  secret door, the arrival in Guberland (not rebuilt), the Baron's quest rows with Markel's keys, Android.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:01:44 (convert.py from the current shared converter, end 15:02:26): 0 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV is byte-identical to before (no face of this map met the rule) and its baked lighting stays installed (not stale); it has 4588 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_alarm.yml` pass, `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.

## The sergeant's round (2026-11-11)

`DC_sargent.scr` is now walked, not timed: SleepTrigger sends the sergeant (SleepCaptain, actor 42) to SMkr0, then to
each of HallwaySleeper0-3 in the script's order (100 in front of each, `evt.MoveActorTo` with arrival events 210-212);
at each he turns to the sleeper, wakes it (`WakeUp`: it cowers, then stands watch), waits 3 s and goes on; last he walks
to SMkr1 and stays. Map var `SleepWoken`: 1-4 the sleeper he is on, 5 walking to SMkr1, 6 done. The alarm or his death
ends the round; a load during it (walks are not saved), or a leg not done in 20 s, finishes it where it was going.
**Deviation:** MM9's `PlayAnim aware` at each sleeper is not carried (his body, like MM9's DookMilitia.abc, has no such
clip). `scenario_scripted.yml` (make_scenarios.py) checks `SleepWoken` 6 and the sergeant near SMkr1. Checked: the four
scenarios pass; a headless trace (round done in about 26 s, ending at SMkr1); desktop captures
`output/held_items_check/b3_dook/close2.png` (he stops facing the first sleeper, it wakes, he walks on).

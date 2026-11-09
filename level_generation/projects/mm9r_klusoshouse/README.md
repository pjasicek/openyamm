# MM9 rework: Klusos House (`klusoshouse.blv`)

MM9's Klusos House (Lord Kluso's mansion in Drangheim City, entered by its front door or the west window; the heist of
the Blackheart) converted from its DAT world into a native indoor map (BLV: sectors, portals, rotating movers, lights,
exit volumes) on the shared dungeon converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)).
Built into the isolated review root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's
decoration rows and the prop models ([props project](../../props/mm9_klusoshouse_claude/README.md)). No x4 textures yet.

Status 2026-10-30 (overnight run): geometry, 10 rooms, 13 rotating double doors (26 leaves), 36 BLV lights (+5
bake-only), both exits, 112 decorations, the chest, 20 actors, the house's scripted objects and baked lighting. The
Guard Captains and Count Kluso have no MM9 3D models yet, and in the review root no actor draws at all (Open items).

## Build and review

```sh
python3 level_generation/projects/mm9r_klusoshouse/convert.py --plan   # rooms only: work/rooms_<storey>.png
python3 level_generation/projects/mm9r_klusoshouse/convert.py          # build, compile, install
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_klusoshouse
python3 level_generation/projects/mm9r_klusoshouse/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_klusoshouse/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_klusoshouse
python3 level_generation/projects/mm9r_klusoshouse/make_tour.py v04 [--original]      # lighting<n>: the 12-view subset
bash level_generation/projects/mm9r_klusoshouse/work/run_tours.sh v04 [--set video.lightmaps=false]
bash level_generation/projects/mm9r_klusoshouse/work/run_tour_original.sh v04      # view_distance=unlimited
python3 level_generation/projects/mm9r_common/dungeon/sheet.py <project>/review/v04 <project>/review/v04_original
python3 level_generation/projects/mm9r_klusoshouse/calib.py v04 v04_original       # brightness per view
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_klusoshouse
```

`sheet.py` takes the native folder first and the original second (the labels follow that order).

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame). Storeys: ground floor 0 LT (front hall
  0-16, the hearths 4), upper floor 176 LT, ceilings 144 / 320 LT; one two-flight stair (8 LT risers) in the north-east.
- DAT: 1358 source polygons (PhysicsBSP 1299 and the world objects), 1239 merged; 165 faces dropped as having no air
  in front (the outside of the house, the roof, the sky box, the balcony outside the window, and the pieces of the
  ceilings and walls over or behind the partitions).
- BLV: **1716 faces**, 2977 vertices, **11 sectors** (10 rooms), **13 portal faces**, **26 movers**, **36 lights**,
  faces per sector max 846 / median 84.
- Content: 112 decorations (37 in the busiest room), 1 chest (container 0, treasure level 6, trap 18), 20 actors
  (19 Guard Captains, row 9113, and Count Kluso, row 9155), no pads.
- Lights: 41 MM9 `Light` objects, 36 in the BLV, 5 over the four-per-point cap (`Light16`, `Light17`, `Light19`,
  `Light132`, `Light151`) bake-only; no floor point under more than 4 lights. No `DirLight`s, no LIGHTDEFS textures, no fog.

## What each DAT object became

| DAT | Native |
| --- | --- |
| `PhysicsBSP` | the static world; `VisBSP`'s 11 UserPortals are the door portals |
| 26 `RotatingDoor` (13 double doors) | one `rotate` mover per leaf (MM9's 90° swing, 50 LT/s, open-away, close after 10 s, reopen on contact); a click swings the pair. 12 pairs close a doorway portal (11 UserPortals and RDoor4/5 from its leaves); RDoor2/6 closes none (the great hall below) and gets the map's own click event 120 |
| `Transparent Window Grate13` | its invisible collision box, and its leaded pane (`window_03`) turned to face the room (convert.py `edit_polygons`): MM9's pane faces out, toward the hillside, where no air is |
| `WorldObject14-16` (chain links), `Carpet29-32`, `InvisibleBrush0-2` | static faces (the brushes invisible collision) |
| `Terrain0` (the hillside outside the window), `TOD_Sky0`, `SkyBox0`, the 7 `skymarker` faces | not built: no air reaches them; the window is opaque (below) |
| `AIBarrier0/1` | not built: AI-only blockers (Invisible.dtx) that keep MM9's monsters off the stair landing; the party walks through them in MM9 |
| 41 `Light`, 3 `Fire` | BLV point lights (radius x 2.56, colours as authored); the `Fire` objects' flames are the reused log pile's flame cards |
| 89 `Prop`, 22 `CandleProp`, `TreasureChest1` | 3D decorations (props project); the chest opens container 0 (event 41) |
| `GuardCaptain` x19, `Count` x1 | actors at their DAT positions, facing 90 − ry; MM9 bodies (guard.abc extents 15 x 36 LT: radius 38, height 184; Count's DAT model PeasantM2.abc 12 x 34: radius 31, height 174) |
| `StartPoint0`, `WindowStartPoint` | starts 0 (front door, facing west into the hall) and 1 (the window room, facing 40°); arrivals from Drangheim City `ExitTrigger2`/`ExitTrigger1` |
| `ExitTrigger1`, `ExitTrigger0` | MM9 positioned transition volumes (front door, west window) to Drangheim City |
| `GuardTrigger` | not built: a relay outside the walls (Scripted objects); also excluded as an air seed (`seed_exclude`) |
| `AIRail` x112, `Marker` x49, `AmbientSound` x5, `ObjectLight0`, `OutsideDef0`, `SkyPointer0`, `WorldProperties0` | not built (AI helpers, sky, ambient sound later) |

## Scripted objects (`worlds/mm9/events/maps/klusoshouse.lua`, written by `convert.py`)

| MM9 script | Objects | Native |
| --- | --- | --- |
| `Blackheart.scr` (:OnUse, :Init) | `Blackheart` (the dirk on the dining-room mantel) | event 75 on a click: item 29, the Elite Dagger (`MM9.ItemIds`, 10029), into the packs (MM9's Black's Heart, item 180, is TreasureChest1's fixed slot 1), key 223 (QBit 90223), the dagger hidden (cog 300), the alarm bell (`events/alarmbell.wav`); map load hides it once key 223 is held |
| `KlusosHidden.scr` (:OnObjectLinkBroken) | `LowerTimed0-6` | hidden (invisible bit, group 1) until the Blackheart is taken: `evt.SetMonGroupBit(1, Invisible, false)`; they fight with the native AI (baseMelee) |
| `KlusosSleeper.scr` (LoopAnim sleep, :OnObjectLinkBroken, OnDamage) | `UpperSleep0-7` | `dormant` actors; `evt.WakeActor` on each when the Blackheart is taken; a hit wakes the one hit (the engine's rule; group 0, so only that one, as MM9's OnDamage) |
| `BookLetter.scr` ("456 Letter") | `Prop46`, the scroll on the kitchen table | event 76: MM9's letter 456 "Post to the Kitchen" (`BOOK AND SCROLL TEXT.csv`) in a message box |
| `KlusosPatrol.scr` | `LowerPatrol0-3` | **unmatched in part**: placed hostile in group 2 at their DAT positions. MM9 walks them round the ground floor (`KlusosPatrol25-48` markers, pairs started by `OnTraverseDone` at index 38); there are no native patrol paths (playbook: MM9 AI scripting has no native equivalent). Their `AlertOthers` (`GuardTrigger` sends `charge` to all patrols, plays `aware2.wav`) is not built: the native AI pursues on sight, and `aware2.wav` is not in our audio |
| `PropAnim.scr` ("ns") | `Cabinet1-6`, `Table2` | **unmatched, nothing to carry**: a looping idle animation named `ns` on static furniture (no Use trigger with an "OnUse" parameter) |

Count Kluso (`Kluso0`) has no script: MONSTERS.txt's default (basemelee.scr) makes him a plain hostile monster, as
placed. The `GuardTrigger` relay names `UpperPatrol0/1`, which the DAT does not contain.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

**Installed: matched to the user's four real MM9 screenshots of Klusos House** (2026-10-30 night; real screenshots
outrank the lightmap math). Profile `tools/lighting/baked_indoors/profiles/mm9_klusoshouse.yml`: 128 samples, 3 bounces,
**`direct_scale` 0.75, `ambient_scale` 1.188, `max_lighting` 1.4**, sector minimum light **31** (`map.ambient` in
overrides.yml, below), the window pane (`WIND41JATM`) an outward emitter; 5 bake-only lights. Bake 30 s through
`bake_slot.sh`; `tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev --check` does not list the map.

### Against the real screenshots

The four shots (`devdocs/mm9_rework/overnight/real_mm9/klusoshouse_real_1..4_*.png`) found by compass (MM9's N is +z
LT, confirmed by shot 2's aligned doors) and furniture, as `make_real_tour.py` views shot at unlimited view distance;
`real_compare.py` measures the central crop (x 18-82 %, y 15-90 %), luma (Rec. 709) and RGB, and writes the sheet:

| Shot | Spot (LT, facing) | Real MM9 luma (RGB) b/r | Ours luma (RGB) b/r | ratio |
| --- | --- | --- | --- | --- |
| 1 corridor guard | west bedroom (room 4), (-670, 20) NE: north door, Cabinet40, WallTorch68 | 64.7 (74, 64, 41) 0.55 | 65.7 (76, 65, 41) 0.54 | 1.02 |
| 2 doorway | west bedroom, (-560, 150) S through doorportal9 to the window room's door | 47.6 (53, 47, 34) 0.64 | 48.0 (53, 48, 32) 0.59 | 1.01 |
| 3 dark room props | master bedroom (upper SE), (60, -140) SE: Cabinet31, chair, table, Cabinet32 | 37.0 (42, 37, 28) 0.67 | 35.4 (41, 35, 26) 0.64 | 0.96 |
| 4 Count's room | great hall, (-390, 970) SE: south door, Cabinet34, east door | 92.4 (106, 92, 52) 0.50 | 82.2 (92, 83, 50) 0.54 | 0.89 |

Shot 4's gap is mostly the Count: MM9 has him large and gold in the middle of the crop; ours draws no actor in the
review root (Open items). Shot 2's door is open in MM9, shut in ours. Sheet `review/real_vs_real09.jpg` (real | ours),
looked at: same rooms, same brightness, the dark room stays dark. The sweep: `real_vs_real02_real03_real04.jpg`,
`real_vs_real03_real05_real06.jpg` (lightmap-matched 0.35/0.72 was x0.74/0.79/0.97/0.61; 0.7/0.6 x0.93/0.96/0.91/0.83;
0.75/0.62 cap 1.4 the best).

Lightmap texel luminance ours / MM9's DAT lightmaps per zone (`work/lightmap_ratio.txt`): ground floor rooms 1.19,
front hall 1.26, great hall 1.21, upper corridors 1.23, upper bedrooms 1.28, upper south rooms 1.37; B/R 0.66-0.79
against MM9's 0.80-0.94 (ours warmer, as the real shots are: their b/r 0.50-0.67 on screen).

**Props against walls (shot 3).** MM9 lights props brightly where walls are dark. In shot 3 MM9's low cabinet reads
46.1 against its back wall's 41.7 (x1.11), ours 42.4 against 24.9 (x1.70): our walls are the darker part there, the
cabinet is x0.92 of MM9's (and less orange: b/r 0.47 against 0.30). The engine issue (a decoration's light subtracts
the frame ambient, Inventa Storca README "Black tables") shows instead in the central room: its chairs read 31.6 against
the back wall's 85.1 (x0.37, `work/prop_gap.py`). The **sector-minimum-light workaround** (level 31: no frame ambient
subtracted; the bake's ambient floor kept by `ambient_scale` x 0.345/0.18) lifts them to 41.5 (x0.49) and leaves the
walls and the four real views as they were. The engine fix itself is not made here.

**Reused `cabinet04ns` turned a further quarter** (props `placements.py` `YAW_FIX`): shots 1 and 3 show its carved
front where ours showed its narrow end (Drangheim Prison's model; the old bake shares the error, so its fit could not
tell).

**Documented alternatives:**
- lightmap-matched (`direct` 0.35, `ambient` 0.72 at sector ambient 20, cap 1): lightmap ratios 0.91-1.23, hue within
  0.03-0.05 of the DAT lightmaps, but x0.61-0.79 of the real shots in the lit rooms (review `lighting08_baked`).
- capture-matched (`work/profile_capture_matched.yml`: 0.72 / 2.1 at sector ambient 20, cap 1.5): mean 93.5 against the
  old-import capture's 93.4 (review `lighting07_baked`, `v04`); too bright and grey against the real shots.
Switch by editing the profile (and `map.ambient`, then convert.py and a full bake) and running
`bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_klusoshouse --recompose`.

## Brightness

The "MM9 original" capture (the old import in our outdoor renderer) is not a valid brightness reference: it draws the
textures nearly unlit. Centre-crop means of the 12 lighting views
(`calib.py lighting10_baked lighting02_original`): capture 93.4, native unbaked 77.1, **installed bake 49.2**: front door
41, front hall 48, central room 59, dining room 39, kitchen 61, great hall 66, upper E-W corridor 28, N-S corridor 64,
gallery 43, bedrooms 45-50. Sheet `review/lighting10_compare.jpg` (capture | lightmap-matched | installed), looked at:
candle pools on the walls, fireplaces and chandeliers the brightest spots, the long corridor between candles dark, no
view black. The 28-view compare `review/v04_compare.jpg` was taken with the earlier capture-matched bake.

## Checks

1. Every DAT world model has a rule (the build stops otherwise); skipped classes listed above.
2. Sealed air: `leaked_to_border` false, one seeded air component (`GuardTrigger` excluded: it stands outside the walls).
   Dropped faces are the house's outside, the roof and the sky box; `thin_walls: true` restores the undersides of the
   door lintels (264 and 88 LT), the gallery's handrail posts and the chain links (24 faces it would otherwise drop).
3. Portals: 13, each joins two rooms (`portals_without_two_rooms` 0). One archway cut (`central_hall_arch`: the central
   room's open side onto the front hall). The great hall is open above its walls to the upper gallery on two sides (a
   handrail over balusters): it stays one room with the front hall and stair, so RDoor2/6 is a plain mover (a cut would
   need one portal per baluster gap; playbook: loops cannot be cut once).
4. No holes: every view of v04 looked at. Mixed faces: the shared converter splits a face only where a second room holds
   15 % of its samples, so the one 320 LT ceiling over the eight bedrooms and corridors stayed in the corridor room and
   drew black inside the bedrooms (v02, `u02_window`). `convert.py` `split_at_walls` cuts each large ceiling at the
   partitions whose tops meet it and each long wall at the partitions whose ends meet it (301 extra pieces; the pieces
   over or behind partitions are dropped): every bedroom's ceiling is now its own room's (checked in the compiled BLV
   and in v03/v04). 74 faces remain mixed with a minority over 20 %: door jambs in the doorway planes, wall-top strips
   over solid walls, a ceiling strip along the central arch. Floor check: 0 LT² of floor under another room's air.
5. Review sheets: `review/real_vs_real09.jpg` (the four real MM9 screenshots | ours, installed bake),
   `review/lighting10_compare.jpg` (12 views, capture | lightmap-matched | installed), `review/v04_compare.jpg` (28 views,
   capture | native, capture-matched bake), `review/lighting08_compare.jpg`, `review/lighting07_compare.jpg`
   (12 views, MM9 original | native unbaked | native baked), flames from the side `review/flames01/`.
6. Walkability (`work/walkability.json`): 0 unreachable, 0 flights, 0 pits; 3 step edges (102/82/41) at x 312 LT,
   z 969-1000: the side of the upper stair flight over the lower one (the two flights run side by side), not a step on
   the way; the stair itself climbs in 8 LT risers. 8 actor notes: guards placed by MM9 against walls or door edges.
7. Scenarios: `scenario_doors_exits.yml` **pass** (both exits raise their transitions; every one of the 13 door groups
   opens on a real click from in front of it; the shut dining-room door stops a walk, opens on a click, the party walks
   through, it shuts again after MM9's 10 s), `scenario_chests.yml` **pass** (the chest opens by interact),
   `scenario_scripted.yml` **pass** (the letter by a click; before the theft the hidden guards are hidden and a sleeper in
   plain view does not target the party; the Blackheart by a click gives item 10029 and QBit 90223, the hidden guards
   appear, the same sleeper now targets the party; a second click gives nothing).
8. Starts: both on the floor facing into the house (first views of the tours; the window start looks along room 1).
9. Compiler unit tests: not rerun (no engine or compiler change).
10. Lights: no floor point under more than 4; bake current.

## Can the monsters reach the party

The audit finds no unreachable region and no cut-off actor, so there was no "cut off" finding to test. Bodies carry MM9's
sizes (above). The headless scripted scenario shows a woken sleeper on the upper floor turning to the party and
targeting it within 2 s.

## Deviations from MM9 and why

- The guards do not patrol (no native patrol paths) and the patrols' alarm relay is not built (Scripted objects).
- The west window's pane is opaque and lit as an emitter; MM9 draws it translucent over the hillside outside, which is
  not built (no air outside: a translucent pane would show the void, as the Temple of Honk's skylights did).
- Brightness follows the user's real MM9 screenshots (Baked lighting): lit rooms about half the old-import capture's
  screen brightness, the master bedroom dark; the lightmap texels come out 1.2-1.4 of MM9's and warmer.
- Sector minimum light 31 instead of 20 (the decorations' light workaround; the bake's floor is unchanged).
- AI barriers on the stair landing are not built: they only steer MM9's monsters.
- MM9's OnDamage wake of a sleeper is the engine's "a hit wakes a resting actor" (each sleeper in group 0, so a hit wakes
  only the one hit).

## Shared converter changes

None in the end. An opt-in `mixed_split_fraction` was tried under `locks/converter_edit.d` (it split only the window room
off the ceiling) and reverted; the Lich Lab `--plan --scratch` outputs before and after are byte-identical
(`work/lichlab_before`, `work/lichlab_after`). The ceiling and wall splitting lives in this map's `convert.py`.

## Open items

- **Actors draw nothing in the review root** (2026-10-30): the Guard Captain and Nobleman rows use borrowed MM6 sprites
  (`gucstaa`, `noblsta`), whose atlases fail to load there (`[SpriteAtlas] ... engine/sprites_new/mm6_nobl/manifest.json
  (requires cooked schema 2)`), and no MM9 3D model exists yet. The actors are present (headless reports, scenarios); the
  creature session's models will make them visible.
- MM9 patrol paths for the four `LowerPatrol` guards (an actor behaviour with `moveTo` waypoints could carry them).
- The chandeliers' candle flames are the Ruined Temple's `chandelier3` (small, faint from below).
- Not checked: a desktop playthrough with real input (doors, the theft, the fight), save/load after the theft (the load
  handler hides the dagger), the exits' arrivals in Drangheim City (not rebuilt), Android.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 14:57:59 (convert.py from the current shared converter, end 14:58:22): 4 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 1712 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.

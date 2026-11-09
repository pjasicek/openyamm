# MM9 rework: Ta'Sar Academy (`tasaracademy.blv`)

MM9's Ta'Sar Academy (the military academy in Lindisfarne; Ludwig's errand for the Book of Rules) converted from its
DAT world into a native indoor map (BLV: sectors, portals, linear and rotating movers, ladders, lights, an exit volume)
on the shared dungeon converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into
the isolated review root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration
rows and the prop models ([props project](../../props/mm9_tasaracademy_claude/README.md)). No x4 textures yet.

Status 2026-10-30 (overnight run): geometry, 29 rooms, 45 movers, 2 ladders, 116 lights, the exit, 304 decorations,
4 chests, 26 actors, the library puzzle, the Book of Rules, the trap doors and the spike pit, the bookcase, the secret
doors, the cracked wall, the chalices, the skill books, the letters, the crate's Dagrell, the sparring, the perception
hints, baked lighting. The shared converter is unchanged: every map-specific choice is in `overrides.yml` and
`convert.py`.

## Build and review

```sh
python3 level_generation/projects/mm9r_tasaracademy/convert.py --plan     # rooms only: work/rooms*.png
python3 level_generation/projects/mm9r_tasaracademy/convert.py            # build, compile, install
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_tasaracademy
level_generation/projects/mm9r_tasaracademy/work/ratios.sh               # lightmap texels ours / MM9's DAT per zone
python3 level_generation/projects/mm9r_tasaracademy/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_tasaracademy/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_tasaracademy
python3 level_generation/projects/mm9r_tasaracademy/reach/make_probes.py && level_generation/projects/mm9r_tasaracademy/reach/run_probes.sh
python3 level_generation/projects/mm9r_tasaracademy/make_tour.py v03 [--original]   # also v03_unbaked, features02
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated ta --world mm9 --map tasaracademy.blv \
    --assets "$PWD/output/mm9_rework/assets_dev" --position 2621 614 1 --yaw-radians -1.5708 --pitch-degrees 0 \
    --warmup 3 --seconds 300 --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_tasaracademy/review_tour_v03.yml
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated taorig --world mm9 --map tasaracademy.odm \
    --assets "$PWD/output/mm9_rework/assets_original" ... --set video.view_distance=unlimited \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_tasaracademy/review_tour_v03_original.yml
python3 level_generation/projects/mm9r_tasaracademy/work/pages.py review/v03_pages review/v03_original \
    review/v03_unbaked review/v03                                                # compare pages, 6 views each
```

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame, int16). Storeys (LT): the halls 0 (the
  arena's floor 16-32), the south wing 128-136, the library's tower floors 208 and 416, the spike pit -256 and its
  tunnel rising to 0.
- 6 550 source polygons -> 6 191 merged -> **6 918 native faces**, 10 810 vertices (183 polygons triangulated); 317
  faces with no air in front dropped (between brushes, the undersides of the invisible brushes).
- **29 rooms** (+ sector 0), 6 sealed air components (the academy and the barn's five pens behind barred gates; the
  second pen holds no animal and is seeded in overrides.yml), no leak. Largest room 1 107 faces (the library), median 191.
- **34 portal faces**: 15 MM9 UserPortals, 7 from door leaves (the linear doors without a UserPortal and the cracked
  wall), 6 archway cuts (the arena's four mouths, the two stairs), 6 `rect_portals` (the pit's mouth under the trap
  doors, the five pen gates). Every portal joins two rooms; floor check 1 474 LT² (SecretDoor1's sill).
- **44 movers**: 38 `dat` (MM9's linear double doors, the two secret doors, the bookcase's two book buttons), 6 `rotate`
  (LibraryDoor, RotatingBookcase1, the two trap doors, the two wall switches); the cracked wall is two scene
  destructibles (`break`, 2026-11-06; before, a `sink` mover).
- **2 ladders** (Ladder0 floor to 208, Ladder1 208 to 416, inside the library's central tower).
- **116 lights** of MM9's 121 class `Light` objects (colour x BrightScale); 5 white fills over the four-per-point cap
  light the bake only; MM9's 4 `DirLight`s in the bake. No floor point under more than four.
- **304 decorations** (props.json: 233 props, 65 flames, 4 chests, the spike pit, the Book of Rules), **4 chests** (loot
  from the shared MM9 item sources), **26 actors**, 0 pads (MM9's touch triggers are polled boxes in the Lua).

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP`, `WorldObject0-4`, `Rails`, `Rails0`, `Transparent Bars`, `Transparent Bars0`, `InvisibleBrush0-2` | static world (the ladders' rungs, the library's galleries and rails, the west wing's barred windows), invisible collision (`InvisibleBrush2`'s `soundonly.dtx` faces too) |
| `Door` pairs `Door0`-`Door33`, `DoubleDoorL/R11` | `dat` movers with MM9's MoveDir, MoveDist 44, Speed 40; a click toggles the pair; doorway portals (UserPortal or the leaves' rectangle) |
| `SecretDoor0/1` (Door) + `Switch1`/`Switch` | `dat` secret doors (95 LT up) and `rotate` wall switches (60 degrees) |
| `LibraryDoor` (RotatingDoor, Locked) | `rotate` (90 degrees, MM9 pivot); opened by the library puzzle |
| `RotatingBookcase1` + `BookButtonFront1/Back1` | `rotate` (180 degrees) and two 3 LT `dat` book buttons |
| `PitDoorLeft1/Right1` + `PitDoorTrigger1`, `Spikes1` (PropDamager) | `rotate` trap doors (`bodies: push`, `carry`, owned by the tower above), a rect portal over the pit; the spike pit decoration on the pit floor, 40 damage once on landing |
| `door crack`, `door crack 2` (DestructableBrush) | scene destructibles 599 (25 hp) and 600 (TriggerDestroyOnly), cogs 20599/20600 (`motion: break`, 2026-11-06), keeping the doorway portal between the pit's tunnel and the library |
| `Ladder0`, `Ladder1` | scene `ladders` (the tops step off onto the tower's floors beside the holes) |
| `Light` (121), `DirLight` (4) | BLV point lights; bake-only lights; profile `dirlights: true` |
| `Prop`, `Brazier`, `CandleProp`, `Barrel`, `TreasureChest`, `DestructableProp0` | 3D decorations ([props project](../../props/mm9_tasaracademy_claude/README.md)); the pickaxes in MM9's `onside` pose |
| `skymarker` (the arena's open roof, the library's lantern) | `sky04` stretched (0.2 texel/LT), the bake's sky emitter |
| `Guard` (16, students among them), `GuardCaptain0`, `HalfOrcCaptain` (2), `Dagrell0`, `Cow0`, `Pig0/1`, `Goat0/1` | 26 placed actors (with the crate's Dagrell), MM9's bodies (ABC extents x Scale x 2.56: guards 38/184, Dook's captains 38/195, Dagrell 64/148 and 48/111 at Scale 0.75, cow 64/133, pigs 26/36, goats 44/87); the animals on their MM9 rows (9267 Cow, 9268 Goat, 9271 Pig), wandering, not immobile |
| `StartPoint0`, `ExitTrigger0` | start 0 in the entrance hall (facing 270, into the academy); MM9 positioned exit to Lindisfarne (`TaSarExit`) |
| `PerceptionBrush0-4` | untouchable translucent faces (Perception.spr, Alpha 0.5, two-sided), cogs 450-454, shown at Perception 10 |
| `AIRail` (252), `Marker` (35), `AmbientSound` (9), `OutsideDef0`, `SkyPointer0`, `SkyBox0`, `TOD_Sky0`, `WorldProperties0` | not built |

## Scripted objects (`worlds/mm9/events/maps/tasaracademy.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **Library puzzle** `TaSarBook.scr` (20 books "<item> <Location>"), `TaSarTable.scr` (Prop163-168: Offense, Strategy, Defense x2, Intelligence, Start) | the four textbooks (items 435-438) lie on the Start table; a book is taken (to the packs) only when the key for the book before it stands (436 needs 9517, 437 9518, 438 9519) and its own table's key does not, and only before key 9516; a table given its own book gives its two keys (9501+9517, 9502+9518, 9503+9519, 9504+9520) and takes every textbook the party carries, showing each on itself; with 9501-9504 key 9516 and LibraryDoor opens (unlock, use, lock: it stays open). Prop168 (behind LibraryDoor) is a second Defense table, as in MM9 |
| **Book of Rules** `BookOfRules.scr` (BookRules) | a world item (`dungeon/pickups.py`, item 391), hidden with key 59 or 166; its pickup gives 5 000 experience, the quest sound and key 59 on Ludwig's errand (key 57), else key 166. The podium's `PropTrigger.scr` "BookRules Use" is not wired: the party picks up the book itself |
| **Bookcase** `BookButtonFront1` OpenTriggers, `RotatingBookcase1` Open/CloseTriggers | either book button presses in and swings the bookcase 180 degrees; released 5.5 s later |
| **Secret doors** `Switch`, `Switch1` Open/CloseTriggers | a click swings the switch and opens its secret door (it shuts after 7 s, CloseWaitTime); the hint is gone |
| **Trap doors** `PitDoorTrigger1` (PitDoorRight1 toggle, PerceptionBrush2 off), `Spikes1` | stepping on the doors drops them (polled box, re-armed); 40 on landing on the spikes; the way out is the tunnel to the cracked wall |
| **Cracked wall** `door crack` (DamageTrigger destroys `door crack 2`, DeathTrigger PerceptionBrush3 off) | weapons break it as in MM9; its damage (event 205) destroys `door crack 2`, its death (event 204) sets `CrackBroken` and its hint goes; a click on either (or on its hint) still breaks it (event 38599, a killing blow) |
| **Chalices** `TaSarChalice.scr` (Prop145-152; "Right" on Prop151) | the right one: +10 Might for the active character (`MightBonus`, temporary) and key 9500, once per character; the others do nothing (MM9: ";damage player" commented out) |
| **Skill books** `SkillBook.scr` (Prop5 "Blade", Prop88 "Random", Prop89-91, Prop94 "") | world items (`dungeon/pickups.py`): item 285 for Prop5, for the others a skill book drawn per session from 285-306, so the party sees which before taking it |
| **Letters and books** `BookLetter.scr` (Prop2 432, Prop4 433, Prop160 434 and its podium Prop159 by `PropTrigger.scr` "Prop160 Use", Brazier48 434, Prop96 439, Prop179 440, Prop174 441, Prop178 442, Prop175 443, Prop177 444) | `evt.SimpleMessage` with MM9's text (BOOK AND SCROLL TEXT.csv) |
| **Crate** `Trigger4` (DestructableProp0 Destroy; SpawnObject "Dagrell Scale 0.75") | entering the store room's box smashes the crate (gone, `crate_smash.wav`) and a hidden Dagrell at Scale 0.75 appears, hostile |
| **Sparring** `Trigger0-3` (GuardCaptain0 Fight), `TaSarTeacher.scr` :OnSpawn (Hate to Student0-3, DooksGuardCaptain0/1), `TaSarStudent.scr` :OnHate (AddEnemy) | the Guard rows (9111, 9113) and the Half Orc Captain row (9104) become enemies (`SetMonsterRelation`, again on later loads); nobody turns on the party |
| **PerceptionBrushes** | shown at Perception 10 (`evt.CheckSkill`), checked on load and every 3 s; the secret doors' go once found, the crack's once broken; the hint faces round the crack and the book button take their clicks |

**Unmatched** (not carried, with reasons): `TaSarGuardDuty.scr` on Guard7/8/11/12 (they walk to their beds at 20:00
and back at 06:00 along `BedMarker`/`Start` markers: no marker paths for native actors, they stand at their posts);
`TaSarTeacher.scr`'s attack animation before the sparring; `BookLetter.scr` "434" on three `AIRail` objects (AITrk2,
AITrk191, AITrk207: invisible AI helpers, nothing to click); `AmbientSound` (9, a later pass). Everything else is a
native event citing its .scr.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_tasaracademy.yml`: 64 samples,
**direct 0.9, bounce 1.0, ambient 0.9, sky_scale 0.05**, `dirlights: true` (MM9's 4 DirLights over the arena and the
library), `max_lighting: 1` (MM9 clips at x1), 5 bake-only lights (white fills over the four-per-point cap), the two
skylights (`sky04`) a sky emitter coloured (1.0, 0.97, 0.88). Sector minimum light **31** (`map.ambient`, the AGENT_BRIEF's decoration workaround: no frame ambient subtracted from the
decorations' light), with `ambient_scale` raised x1.92 (0.9 -> 1.725, Klusos House's 0.345/0.18) so the bake is unchanged:
the lightmap ratios below are the same at sector light 20 and 31. The BLV lights
carry colour x BrightScale (`scale_lights` in convert.py, the Ruined Temple's lesson): the braziers' orange 0.7 over 50 LT,
the white fills 0.2-0.5 over 300-450 LT. `tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev --check`
does not list the map.

**Calibrated to MM9's own DAT lightmaps** (AGENT_BRIEF "How MM9 draws light": walls are texture x lightmap x1, no
multiplier), per zone (`hue_zones.py`,
`../mm9r_common/hue_vs_lightmaps.py`, `work/ratios.sh`), lightmap texel luminance ours / MM9's:

| Zone | MM9 | ours | ratio | B/R ours (MM9) |
| --- | --- | --- | --- | --- |
| entry halls | 0.432 | 0.421 | 0.97 | 0.95 (1.00) |
| arena | 0.377 | 0.456 | 1.21 | 0.97 (1.00) |
| west wing | 0.398 | 0.457 | 1.15 | 0.95 (1.00) |
| east wing | 0.426 | 0.451 | 1.06 | 0.95 (1.00) |
| store room | 0.401 | 0.398 | 0.99 | 0.96 (0.99) |
| library | 0.335 | 0.345 | 1.03 | 0.98 (0.99) |
| pit tower | 0.332 | 0.361 | 1.09 | 0.97 (0.98) |
| south halls (olive hall, corridors) | 0.363 | 0.390 | 1.07 | 0.97 (1.00) |
| south hall | 0.396 | 0.385 | 0.97 | 0.97 (0.99) |
| Book of Rules' room | 0.616 | 0.599 | 0.97 | 0.92 (1.00) |
| east octagon | 0.542 | 0.481 | 0.89 | 0.94 (0.99) |
| barn | 0.376 | 0.365 | 0.97 | 0.98 (0.99) |

MM9's lightmaps here are **neutral white** everywhere (B/R 0.98-1.00, saturation 0.00-0.03): the academy is lit by
large white fills (`Light` 255/255/255 at BrightScale 0.2-0.5) and white DirLights; the braziers' orange lights reach
only 50 LT. The first draft (direct 0.7, bounce 6, ambient 0.6, sky 0.4, Verhoffin's profile) came out warm (B/R
0.73-0.91: the bounce off the warm plaster and wood) and the arena x2 (the skylight); bounce 1 and sky 0.05 bring every
zone within 0.89-1.21 of MM9 and its hue within 0.08. The first profile is `work/profile_v1.yml`; a sweep is
`work/recompose.sh key=value ...` (edits the profile, recomposes in seconds, prints the ratios). No real MM9 screenshot
of this map exists in `devdocs/mm9_rework/overnight/real_mm9/`. MM9 adds its flickering candle and brazier lights on
top at run time (the brief: real shots come out 1.1-1.37x the lightmaps in rooms with them); ours carry them in the
bake and as BLV lights.

## Brightness

The reference is MM9's DAT lightmaps (table above), not the old-import capture, which draws the textures nearly unlit
(AGENT_BRIEF). For information, screen means of the 76 tour views (centre crop, Rec. 709, `work/brightness.py`,
`review/brightness_v03.txt`): **capture 64.3, native unbaked 51.2, native baked 54.5 (x0.85 of the capture)**. The views
furthest under the capture are the library's central column (a22 x0.42, a19 x0.51, a18 x0.64: the capture shows the
plaster column bright, MM9's own lightmap texels on it are 0.288, ours 0.334, x1.16), the west corridor and dormitory
(x0.66-0.67: MM9's lightmaps there are 0.40, ours 0.46) and the east octagon (x0.67, ours x0.89 of its lightmaps).
The arena, the dormitories and the chalice room read x1.0-1.12. The library column's MM9 lightmap comes out darker
than its walls; ours follows it.

Sheets (looked at): `review/v03_pages_p01-p13.jpg` (MM9 original | native unbaked | native baked, 76 views),
`review/v03_compare.jpg` and `review/lighting_v03_compare.jpg` (the same as single sheets), `review/features02/` (a
brazier's flame card from the side, the barn's pens through their gates, the arena's skylight and the library's lantern
with `sky04`, the trap doors and the podium). The v03 tours show the actors (stand-ins and MM9 models) since the review
root's actors.yml loads again; the teacher stands in front of the camera in `a05_arena_north`.

## Checks

- Scenarios (all pass on the final build, real clicks for doors, the switch, the book button, the cracked wall, the
  chests, the chalices, the skill book, the textbooks and tables, the letter and the Book of Rules):
  `scenario_doors_exits.yml` (ExitTrigger0 raises its transition; Door0/1 stops the party, opens on a click and is walked
  through into the dormitory; LibraryDoor stays locked; Switch1 opens SecretDoor0; BookButtonFront1 swings the bookcase
  open; the cracked wall breaks and the party walks through into the pit's tunnel; Ladder0 and Ladder1 climb to the
  tower's floors at 208 and 416 LT), `scenario_chests.yml` (the 4 chests, behind the two secret doors),
  `scenario_scripted.yml` (the perception hints off at Perception 1 and on at 10; the trap doors drop the party onto the
  spikes; Trigger0 starts the sparring; Trigger4 smashes the crate; a wrong chalice does nothing, the right one gives key
  9500; Prop5 gives the Blade skill book; textbook 436 cannot be taken first; the four books on their tables in order
  give 9501-9504 and 9516 and LibraryDoor opens; a letter; the Book of Rules on Ludwig's errand gives item 391 and key
  59, not 166).
- Walkability (`work/walkability.json`, `audit.py`): 12 steps (41-64: the arena's raised sides 61, the stage's 49, door
  sills 41), 2 flights (the arena's side steps, 41 within one path step), 47 mover notes (the linear doors' lips and
  recesses, the switches), 2 actor notes (Pig0 against its pen's wall, Dagrell0 by the store room's crate shelf). Its 36
  unreachable entries hold no actor: the dormitories' bunk platforms (72 above the floor, 0.03 M units² each), the south
  hall's two daises and the stage (112 and 48 above, 0.04-0.20 M) and a dormitory's raised dais (49).
- Faces: the views (below) show no holes; `work/mixed_faces.json` (158 faces over two rooms without a portal: the edge
  samples along thin walls) caused no visible fault. `work/dropped_faces.json` has no partition a body could walk
  through (`thin_walls: true`).
- Lights: 116 BLV lights, no floor point under more than four (`content.json` `light_coverage`).
- Compiler unit tests (`build/tools/openyamm_indoor_source_tests`): 21 test cases, 205 assertions pass.

## Can the monsters reach the party

The audit reports no cut-off region with an actor in it (the unreachable entries above are bunks and daises). The store
room's two Dagrells behind SecretDoor0 were probed for reach (`reach/make_probes.py`,
`reach/run_probes.sh`, `report_state` every 2 s):

| Probe | Result |
| --- | --- |
| `dagrell_seen` (party in the store room, 300 LT away) | Dagrell0 comes to about 400 of the party and attacks from there (the "stops short in sight" pattern) |
| `dagrell_hidden` (Switch1 opened, party seen, then out in the east corridor) | Dagrell0 follows out through the store room's corridor to SecretDoor0's doorway (x 5 236 native) and targets the party in the corridor |
| `dagrell_door_shut` (control: SecretDoor0 shut) | Dagrell0 follows to the shut door (x 5 348) and stops: the door holds it, as MM9's |

The academy's own people (16 guards and students, the teacher, Dook's two captains) are hostile to the party, as in MM9
(2026-11-08, checked by the user against a video of the original): probe with the party among the four duty guards in
the dormitory corridor (1741, -60): all four target and attack it within 5 s; a wandering guard (Guard 3) comes from the
corridor and attacks.

## Deviations from MM9 and why

- **Guards stand at their posts.** `TaSarGuardDuty.scr` walks Guard7/8/11/12 to their beds at 20:00 and back at 06:00
  along markers; native actors have no marker paths.
- **The sparring** turns the Guard rows against the Half Orc Captain row (`SetMonsterRelation`), so any guard nearby
  joins in; MM9 sends Hate only to Student0-3 and the two captains. The teacher's attack animation is not played.
- **The switches do not lock.** MM9's Switch1 locks itself after its second swing (OpenTrigger "lock"); here each
  switch keeps working, so a party inside the store room is never shut in once SecretDoor0 closes (7 s). The secret
  doors also open on a click (MM9: they are Doors and answer Use).
- **The cracked wall also breaks on a click** (a killing blow): MM9 breaks it by 25 hit points of weapon damage only, which
  works too since it became a scene destructible (2026-11-06).
- **The chalice gives +10 Might once per character** as a temporary bonus until rest (MM9's GiveAttribute for 288 000
  game seconds, repeatable).
- **The hints of the secret doors stay gone once found** (MM9 shows them again when the door shuts); the trap doors'
  hint stays (MM9 hides it while the doors are open).
- **Skill books** are `bookflat` stand-ins (MM9 ships no `Skillbook.abc`); three of them lie on the floor beside their
  tables where MM9's gravity drops them (props README).
- **The bookcase's buttons** come back 5.5 s after a press (MM9: when the bookcase's swing ends).
- **Brightness** follows MM9's lightmaps at x1 (above); MM9's dynamic flicker of the candles and braziers is not added.

## Map-local converter changes (`convert.py`, the shared package unchanged)

- `edit_polygons`: the skylights' `skymarker` faces drawn with `sky04` at 0.2 texel/LT (walls along their horizontal
  tangent and down).
- `scale_lights`: BLV light colour x BrightScale.
- `place_perception_hints`, the polled trigger boxes and the scene's translucent hint faces follow Verhoffin Ruins.
- `actors`: the animals' MM9 rows written here (the shared replacement table has none), the crate's Dagrell as a hidden
  actor at the crate.
- overrides.yml: `soundonly.dtx` aliased to the invisible texture (InvisibleBrush2), the cracked wall `break` (its
  model names are no Lua identifiers: no DOORS keys), `rect_portals` for the pit and the pens, a `seeds` entry in the empty second pen, `skip_user_portals: [PitDoorPortal1]`
  (its side samples fall in no air; the trap doors are owned by the tower above, as Anskram Keep's), ladder tops beside
  the holes so a forward step does not walk back into them.

## Open items

- MM9 models for the Guard family, the Half Orc Captain and the Dagrell draw stand-ins or nothing in the review root
  (borrowed MM6-MM8 sprites need cooked schema 2; another session builds the MM9 models).
- Guard duty walks (marker paths), ambient sounds, the candles' and braziers' flicker.
- A density and pack pass (PLAN.md: later); x4 textures last.

## Not checked

- The trap doors' drop and the bookcase's swing seen in a running game (the scenarios prove the states, the fall onto
  the spikes and the damage; no desktop capture mid-motion).
- Arrival from Lindisfarne by walking its ExitTrigger1 (the transition row's arrival is the start's floor).
- The perception hints at Perception 10 in a desktop capture (the tour party shows them; the scenario checks the map
  variable at Perception 1 and 10).
- The sparring fight itself (only that the relation is set and the trigger fires) and combat AI beyond the reach probes.
- Real MM9 screenshots of this map (none exist in `devdocs/mm9_rework/overnight/real_mm9/`).
- The stray 2 cm ball mesh the props agent found in reused models (`mm9_deco_bookflat`, `mm9_deco_book`, props README).

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 14:52:25 (convert.py from the current shared converter, end 14:53:41): 15 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 6903 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
Blocker probes: 8 walks into helper brushes resting on the floor stop short of them, 8 identical before and after (their sides still block).

# A player's pins, 2026-11-22 evening (Xeen v3.1, Vertigo and XD-02)

A player sent 20 in-game pins (`pin <text>` in the console): 19 on X1 Vertigo, one in XD-02. Each pin has the pose and
the game's own picture.

- Pins are filed in the map projects: `devdocs/xeen/briefs/x1/L4/review/pins.yml` (pin:p1–p19) and
  `devdocs/xeen/briefs/xd02/L4/review/pins.yml` (pin:p1). Use `oymap pins list|claim|tour|resolve` on them
  (openyamm-studio/README.md, "Pins from the game").
- Pictures: `output/xeen_fb/p2_20261123/original/<stamp>-<map>.png` (with the pin YAMLs), and
  `<project>/.oymap/pins/pictures/`.

**The rule (the user's, 2026-11-21, applies here too):** every family is fixed at its source (generator, shared kit,
engine, common Lua, data), then on **every** site of its kind in the Xeen world, with a check that keeps it fixed. The
pinned spot is only the example. See [briefs/FEEDBACK_FIX_RULES.md](../briefs/FEEDBACK_FIX_RULES.md).

## The pins, grouped into families

Poses are `position [x, y, z]`, `yaw` radians, `pitch` degrees, from the pin files.

| F | Family | Pin(s), map, pose, what the picture shows | Agent |
| --- | --- | --- | --- |
| F24 | **NPCs stuck** | X1 p1 "npc stuck" [-6150.2, 7579.5, 628.4] yaw 4.691 p -10.9: a guard on Vertigo Bridge against its rail. X1 p15 "npc stuck" [-5887.0, 10816.8, 709.1] yaw 1.508 p -8.5: a peasant in a dark hollow under a stone retaining wall | town |
| F25 | **River culverts through the town wall**: open faces | X1 p3 "here is something missing" [-1183.8, 4455.6, 438.7] yaw 2.089 p -50.7: arch through the wall, black void above, flat untextured blue strip for water. X1 p18 "missing textures on both side" [-908.2, 5627.4, 577.0] yaw 3.125 p -25.3 ("Outfall"): wall face with cut, open sides over the river | town |
| F26 | **Gaps where walls meet houses** | X1 p5 "there is something missing" [-8743.7, 11252.6, 641.6] yaw 3.017 p 3.6: retaining wall ends open beside a half-timbered house, underside visible. X1 p6 "gap" [-7369.9, 11622.5, 999.5] yaw 3.126 p -12.8: gap between a wall top and a house | town |
| F27 | **House buried in a slope** | X1 p14 "the house is buried" [-6817.4, 15020.1, 911.8] yaw 2.067 p -14.4: ground rises over the house's foot and door | town |
| F28 | **Road misses the gate** | X1 p19 "the path has to be more to the right" [-9684.9, 10439.6, 641.0] yaw 3.523 p -5.1: the cobbled road runs into the tower beside the gate arch | town |
| F29 | **Terrain holes and too-steep banks** | X1 p7 "You can fall in it" [20326.9, 1049.4, 577.0] yaw 1.496 p -38.4: a dark gap between ground and a rock face. X1 p12 "a bit to steep" [21240.7, 12728.0, 1.0] yaw 4.385 p 3.0: a sheer earth bank at the east shore | wild |
| F30 | **Single-sided ruin walls** | X1 p11 "textures missing" [16654.2, 12286.7, 1089.1] yaw 1.099 p -11.1 ("Ruined watchtower"): paper-thin walls, backs not drawn | wild |
| F31 | **Z-fighting** | X1 p8 "texture are z fighting" [-20796.0, 1214.8, 621.3] yaw 3.041 p -7.8 ("Hunters' tent"): the plank roof flickers | wild |
| F32 | **Empty shrine pavilion** (suggestion) | X1 p16 "maybe put an altar under the hut" [-19804.7, -8633.3, 668.6] yaw 5.298 p -10.3: a roof on four posts, nothing under it | wild |
| F33 | **Lootable camps** (suggestion) | X1 p9 "maybe allow looting it with some gold and an item" [-17506.8, 17713.2, 1664.4] yaw 1.118 p -20.1 ("Orc campfire") | wild |
| F34 | **Water reflection vanishes as you move** | X1 p2 "if you move further the reflection disappears" [-6303.7, 7281.4, 591.2] yaw 3.762 p -8.3: the river mirrors the houses at this pose, not a little further on | engine |
| F35 | **Guild dues do nothing** | X1 p4 "it is not working" [-7941.8, 4276.3, 641.0] yaw 4.706 p -8.1: Vern's House, Vern the Guildman, topic "Dues" ("I'll put anyone on the guild roll for free. Dues will cost 25 gold, though.") | engine |
| F36 | **Shop greeting drawn over the shelves** | X1 p13 "The back for more Steel is overlapping" [-10655.9, 10364.5, 641.0] yaw 2.061 p -9.5: Norman's Ironworks, "Back for more steel?" over the lowest plank | engine |
| F37 | **Doom bug sounds strange** | X1 p10 [6300.3, 9475.8, 650.8] yaw 0.154 p 2.1 | engine |
| F38 | **Skeleton Lords hit hard** (level-6 party, 94 HP) | X1 p17 [-5847.8, -17794.7, 796.0] yaw 2.485 p -6.6 | engine |
| F39 | **Open containers with no inside** | XD-02 p1 "the inside texture are missing" [7636.6, 7217.9, -352.0] yaw 4.811 p -31.0 ("Empty Cauldron"): the cauldron's inner wall is not drawn | engine |

Agents: **town** (F24–F28: Vertigo's town, walls, river crossings, houses, roads, wanderers), **wild** (F29–F33:
terrain, ruins, props, camps and shrines outside the towns), **engine** (F34–F39: rendering, house/shop screens,
sounds, monster data, models; this run's only builder).

## Results

(appended per family)

### F29–F33: the wild land (agent `xeen-fb2-wild`, 2026-11-23 ~10:20–11:30; for A5, A6, A3)

Before captures at every pin's pose from assets_dev: `output/xeen_fb/p2_wild/before/` (`01-p7` … `06-p16`; tour
`tour_before.yml`); each matches the player's picture. Deciders (read-only) answered F29's rim, F32 and F33; their rows
are under DECIDE in the agent's report (not written to DECISIONS.md by this agent).

**F29, terrain holes and too-steep banks.** *Cause:* every Xeen outdoor map ends on one or two sides in the world rim:
a one-cell cliff (576–2,400 high) over a sea at 0 that stands for the stars (`water:sky` / `water:rim_sea`). The design's
edge-fall trigger (WORLD_DESIGN §4, PRODUCTION/ROADMAP E5) was never built, so a party that walked off the rim (p12) or
fell into the hole the studio's `waterfall` word cuts beside Pitchfork Falls (p7: the land under the sheet is lowered to
0 a cell wider than the crags cover) stood in the sea, "drowning", under a cliff steeper than the party climbs.
*Fix at the source (data, no engine work):* `level_generation/projects/xeen/common/wild.py` `rim_fall()` gives every map
with a rim sea a timer event (every second) calling `Xeen.rimFall(seas, points)` (new, `xeen_common.lua`): a party not
flying, below 320 and in the rim sea or within 1,024 of it (the rim's foot, the falls' hole) is put back over the nearest
return point on the rim top and falls `Xeen.SkyFallHeight` (the engine's fall damage, Feather Fall spares), status line
"You fall from the edge of the world... and wake on the rim." Return points (10–24 a map) are found on the installed
map's land: three cells in from the sea, level, walkable from the map's start, two cells from any structure. All 13
outdoor generators call `WILD.apply(sketch, '<key>')` before writing the sketch. *Sites:* 13 rim maps (X1–X7, D1–D6),
the X1 falls hole; the old `rules: rim: {fall: death}` notes in d5/d6/x6/x7 project.yml are now wrong (orchestrator's).
*Check:* `tools/xeen/check_wild.py` (`rim.event`, `rim.point` against the built terrain, `rim.pit`: land 1,024–4,096 from
the rim sea below 320 that the rescue misses: none today); scenarios `tests/scenarios/xeen/rim_fall.yml` (p12's beach,
the campfire, the altar) and `rim_fall_pit.yml` (p7's hole), both pass on a private root with X1 rebuilt
(`output/xeen_fb/p2_wild/root`). Known gap: in a headless run only the first rescue of a map visit fires (a second
`set_pose` into the sea stays; see REQUESTS); the pit stays visible until the studio covers it (REQUESTS).

**F30, single-sided ruin walls.** *Cause:* the studio's `ruin` (`OutdoorBuildings.cpp` `raiseRuinWall`) gives each wall
an inner face and end faces only where a stretch *within the wall* is lower; at the outline's corners it never closes the
wall where the next wall is lower or gone, and on a many-sided (round) part the inner faces stop `thickness` short of
each corner, leaving wedge gaps. So every ruin shows paper-thin wall ends at its corners (p11's round watchtower: 104
open edges). Not fixable in the sketch: studio spec under REQUESTS. *Check:* `tools/xeen/check_faces.py`
`shell.open_edge` (a ruin's faces over the land must close: every edge along another face). *Sites (27 ruins, 12 maps):*
X1 watchtower, ruined shrine, ruined cottage, burned farmstead; X2 watchtower, shore ruin; X3 watchtower, Newcastle ruin,
wreck; X4 mill ruin, rim lookout; X5 Edge Watch; X6 caravanserai, Gargoyle watch; X7 east lookout, pony shed, watch
barracks; D1 burnt mill, shipwreck, trebuchet; D3 rim watch, Vespar ruin; D4 isle tower crown; D5 broken pyramid, hill
shrine; D6 broken pyramid, ridge tower. All left for the studio fix, then a rebuild of the 12 maps.

**F31, z-fighting.** *Cause:* the game draws every outdoor BModel face and every indoor face from both sides (no
back-face culling in `OutdoorRenderer.cpp` / `IndoorRenderer.cpp`), and the studio's tent (`OutdoorThings.cpp`
`raiseTent`, "both ways") lays its canvas twice on the same points, outward and inward, each with its own lightmap: the
two flicker (p8, dark streaks on the Hunters' tent's planks). The studio's coplanar warning looks only at faces facing
the same way. *Check:* `tools/xeen/check_faces.py` `faces.back_to_back` (opposite faces in one plane that overlap, when
one side is open space: two solids touching hide theirs) and `faces.coplanar`. *Sites outdoors (51 models, 155 pairs):*
tents and hides 33 (X1 hunters', travellers'; X2 two camps; X3 Ebenezer's, rangers' x2; X4 barbarians' x3, knights' x2,
the lists' pavilions x2; X5 archer, camp x2, Freeda, hunt, ogre, outpost x2; X6 Arie, prospector; X7 the outpost's three
hides; D1 Justine, Sardaj x2; D5 dwarf, robbers), wagons/carts 5 (X4 Joe's, X6 two, X7 two: the same canvas), X5's
palisade, X2 Nystor's ship, D1 castaway camp, gatehouse, Kalindra's ghost house and gate, wall NE, cv_weapons; D2
sprite houses; D3 south gatehouse x2; D5 broken pyramid; X1 Witch Tower door frame, the culvert outfall (town's F25).
Same-facing (55 pairs, 12 models): the waterfalls of D2, D3 x2, D4, X4 (their sheets over the top water), X4 village
wall (32), X4 eyrie and rim lookout, X2 Nystor's ship, X5 XD-10 north door, D1 jetty deck and square paving. *Indoors:*
526 pairs on 45 BLVs (`output/xeen_fb/p2_wild/all_faces_before.json`, `.txt`): not yet looked at one by one (the rays
that tell open from enclosed are rougher in rooms); for A7/A8 after the outdoor fix. Tents need the studio
(REQUESTS); the others go to each map's lane with the list.

**F32, empty shrine pavilion (suggestion, taken).** Decider: MM6's prefab shrines put the click on an altar block only
(OUTE1 event 261 on `shrineE`'s altar faces), MM7 pairs "Shrine" (hint) with "Altar" (the click). *Fix:*
`wild.shrine_altars()`: a building part on posts titled a shrine whose click gives something gets a `platform` altar
192 x 128, 128 high, in the part's wall texture, under its roof, and the click (condition, effects, else) moves onto it;
the pavilion keeps its title. Bell frames and lean-tos keep their own click. *Sites (9):* X1 Shrine of Poison, X2 Shrine
of Electricity, X3 wayside (garlic) shrine, X4 Shrine of Fire, X5 Shrine of Cold, D1 wayside shrine of Mok and the
prayer shrine, D3 wayside shrine of the desert sun (X6's and X7's shrines are houses: no change). *Check:*
`check_wild.py` `wild.altar`. The decider's dressing of empty stalls and sheds is not done (NEXT).

**F33, lootable camps (suggestion, taken as MM does it).** Decider: no MM6–MM8 campfire gives gold; MM8's Global
285/286 "Camp Fire" give 1–4 food once (`evt.ChangeEvent(0)`), MM7's (here 1162/1163) food and, with Perception, a
small ring. *Fix:* `wild.campfires()`: every campfire decoration (`cmpfyr00`, `ckfyr00`, `dec24`, `dec25`, `dec04`,
`7dec02`) without an event of its own feeds the party 1–3 food once, and a character with Perception finds a ring on
the cursor (D-93), with a status line; Graalg's parley fire and D6's smoking vent are left. Hostile camps keep their
chests/crates (X1's outposts already have a crate beside the fire). *Sites:* 29 fires on 11 maps (X1 10, X2 3, X3 2, X4
2, X5 6, X6 1, X7 2, D1 2, D4 1, D5 1, D6 2; the dungeons' fires are not done: NEXT). *Check:* `check_wild.py`
`wild.campfire`.

**State.** Generators: X1–X7, D1–D6 call `WILD.apply`; X1's L4 regenerated and recorded with it (entry 3); X1 built,
installed into `output/xeen_fb/p2_wild/root`, audit 0 errors, door_check 0, walk (428 steps) and hostility pass,
`rim_fall` and `rim_fall_pit` pass. **Not installed into assets_dev:** a rebuild at 11:03 picked up the town agent's
unfinished change to `tools/xeen/kit_pieces.py` (two X1 walls invalid), so X1 waits for the town agent's X1 install,
which carries this change (or rerun `output/xeen_fb/p2_wild/x1_cycle.sh` with `INSTALL=1` under the X1 lock). The other
12 maps need a rebuild with bake each (their lanes'). After captures: none yet (nothing installed). `check_wild.py`
today: every map `rim.event` (until rebuilt), X2–D5 `wild.altar`/`wild.campfire` until rebuilt.

### F34–F39: rendering, house and shop screens, sounds, monster data, models (agent `xeen-fb2-engine`, 2026-11-23, for A1, A2, A3, A4, A5, AU, S)

Scratch and captures: `output/xeen_fb/p2_engine/` (`f34/`, `f36/`, `f37_f38/`, `f39/`). Binaries: `build-xeen/game/openyamm`
and `build/game/openyamm` (see the A1 Log of this date). All six pins are resolved with these notes.

**F34, the river's reflection vanishes as you move (X1 p2). Engine fault, every world.**
- Cause: the water renderer gives at most two planar captures a frame, nearest surface first. BModel water faces of
  one height were one surface with **one bounding box** over all of them: Vertigo's three wells (z 712, from
  (-16619, 10671) to (-6575, 3461)) and its two fountains (z 688) made boxes over half the map with the camera inside,
  so their "distance" was the camera's height above them (55-79), nearer than the river below the bank (191). Both
  captures went to wells and fountains hidden behind houses (the occlusion answer said so, but it only skipped
  refreshing their capture); the river took the plain sky fill. At the pin the square's fountain and the river won;
  300 units on, the south well's box took the river's capture. Measured with a temporary log (removed):
  `output/xeen_fb/p2_engine/f34/instrumentation.diff`.
- Fix (A1, shared): `game/render/WaterGeometry.h` `addWaterFacePatch`: each connected piece of a level keeps its own
  box (faces that touch merge); `WaterRenderer::prepare`: a surface the last occlusion answer found hidden takes no
  capture.
- Sites: outdoor maps with BModel water of one height in pieces more than 2,000 apart (wells, fountains, falls):
  Xeen X1 (3 levels), X2, X4, D3; also MM6 outb1, outb2, outc1 (3), outd1, outd2 (2), oute3 (2), MM7 7out01, 7out03,
  7out05, 7out06, MM8 out03. All fixed by the engine change. Indoor batches are per sector, so indoor maps change
  little.
- Check: unit test "water faces of one level far apart keep separate bounds for the nearest-capture choice"
  (`tests/WaterRenderingTests.cpp`); the water tests pass (100 cases).
- Captures (pin pose, then 300/600/1000 forward, 500-3000 west, 500-2000 east): before
  `output/xeen_fb/p2_engine/f34/before/` (sheet `f34/sheet_before.jpg`: no reflection away from the bridge), after
  `f34/after/` (`f34/sheet_after.jpg`: reflection at every pose).
- MM6–MM9: the listed MM6–MM8 maps gain the river/lake reflection where a well or fountain stole it; a hidden pool no
  longer costs a capture (less work, no visual loss).

**F35, guild dues do nothing (X1 p4). Data and text; decided by a decider (DECIDE 1 below).**
- Cause: Xeen's guilds are open to everyone (the engine gates guilds of MM6 and MM7 only, `magicGuildMembershipType`;
  TOWNS_FORMAT §3). Vern's "Dues" topic and several guild people's lines still sold or demanded membership, and the
  town files carried a `services: [{guild_membership: ...}]` key nothing reads.
- Fix (A4, A3 text): no membership in Xeen. Every line that sold, priced or demanded it now says the guild is open, in
  the speaker's voice: Vern (greeting and Dues topic), Calder (Fire Guild), Hesper (Body Guild), Vatawna, Aldous,
  Brother Cael (`source/towns/x1.yml`, `x2.yml`), Casper's greeting and "The rolls" topic (`towns/x5.yml`,
  `npcs/flavour/x5.yml`, the wink kept as a true joke); `source/npcs/x1.yml` Dues. The dead `guild_membership` key is
  gone. Sarah Slither, Brunhilde ("free") and Mordant ("used to cost") were true and stay. Tables regenerated
  (`npc_greet.txt`, `npc_topic_text.txt`, `xeen_quests.lua`); `build_world.py --check` 0 differ.
- Sites: 8 NPCs, 12 lines and 4 dead keys found; all fixed. No test asserted the old text.
- Check: `tools/xeen/towns.py` `membership_text_errors`: a guild person (owner or resident of a guild house, or titled
  for a guild) whose greeting or talk topic pairs membership/roll/dues with gold, pay, cost, bribe, "members only" or
  an invitation, and any `guild_membership` key, is an ERROR. On the sources before the fix: 12 errors; after: 0.
- Captures: before, the player's p4; after `output/xeen_fb/p2_engine/f36/after/vern_menu.png`, `vern_dues.png`.
- Translations: `languages/zh-cn/text/xeen.po` still has the old lines until the next `l10n.py update`.

**F36, a shop greeting drawn over the shelves (X1 p13). Engine fault, every world.**
- Cause: since merge point 40 a talking proprietor (F1) opens his menu with his greeting as the dialogue body. When a
  service opened the shelves (or the party inventory for Display Equipment, Sell, Identify, Repair), the body text was
  still drawn on top, at the bottom of the shop picture over the lowest plank. MM6–MM8 proprietors never talk, so
  their buy screens had no body lines.
- Fix (A1): `GameplayUiController::houseShopCoversDialogueBody`; `GameplayDialogueRenderer` draws neither the body
  frame nor its text while a shop's shelves, stock list or party inventory fill the picture. The shop's prompts stay
  on the hint line above the party bar.
- Sites: 38 Xeen shops and guilds with a talking proprietor (9 weapon, 4 armour, 3 magic, 4 alchemists, 18 guilds,
  from F1's list `output/xeen_fb/F1_F7/f1_sites.txt`); all fixed by the engine change. Every shop type checked in the
  capture tour (weapon buy, display/sell bag, armour, magic, alchemist, guild).
- Check: unit test "a shop's shelves and its party inventory hide the house dialogue's body text"
  (`tests/GameplayUiRuntimeTests.cpp`).
- Captures: before `output/xeen_fb/p2_engine/f36/before/norman_buy.png` (sheet `f36/sheet_before.jpg`), after
  `f36/after/norman_buy.png` (sheet `f36/sheet_after.jpg`). Tours `f36/tour_shops_{before,after}.yml`.
- MM6–MM9: no visible change in MM6–MM8 (their buy screens have no body lines); MM9 vendor houses with a talking
  proprietor lose the same overlap.

**F37, the Doom Bug sounds strange (X1 p10). AU data.**
- Cause: the ElevenLabs swarm sounds came out as white hiss (centroid 7.6–10.8 kHz, 1–3 % of the energy under
  2.5 kHz, flatness 0.20–0.30; MM6–MM8 insects buzz at 100–600 Hz), and the Doom Bug, one cricket, played the same
  hiss pitched three semitones down (62034–62037). Length, loudness, clipping and DC were normal.
- Fix (AU): `level_generation/sounds/xeen_20261120/jobs.yml` re-prompted the swarms as a 140 Hz wing hum and gave the
  Doom Bug its own giant-cricket set; picks by measurement (`picks.yml` `listening`); `install.py` wrote 18 WAVs.
  Sound ids unchanged, so no monster row changed. AUDIO.md and AU's Log updated.
- Sites: 18 sounds in 4 families had the hiss: swarms 4 (also rows 11341, 11342), Doom Bug 4, sprites 6 (rows
  11530–11538), snake men 4 (with the Snake Lord's). All re-done.
- Check: `tools/xeen/check_monster_sounds.py` measures every Xeen row's sounds against the 645 MM6–MM8 monster sounds:
  missing, clipping, hiss, loudness and length outliers, cut-off ends, DC. Before (HEAD WAVs): 18 faults, exit 1;
  after: 0 (`f37_f38/check_before.txt`, `check_after.txt`).
- Credits: 45 requests, 621 charged, 2,220 committed (ledger 38,412 charged, 135,170 committed of 140,000).
- Open: picked by measurement; nobody has listened yet. MM6–MM9: none.

**F38, Skeleton Lords hit hard (X1 p17). A2 data; decided by a decider (DECIDE 2 below).**
- The row is in line: Xeen Skeleton Lord 11242, level 16, 74 HP, 2d8+6, recovery 90, Curse: 16.7 a round, like
  MM6–MM8's Skeleton Lord (level 14, 16.9).
- Cause: X1's skeleton spawn slot ran at Dif 1 (D-1.3's 90/8/2), and Dif 1's 2 % C tier is that lord: level 16 on a
  map whose band is 2–12 (MAPS §0); 1.5× X1's next-strongest monster per round. D-85/D-87 do not apply (melee Curse,
  `d85.py xeen_x1` clean). The reporter plays a Death Knight, so MAW: MAW rescales the lord to about level 7.
- Fix: X1's skeletons at Dif 0 (`source/map_rows.yml`; `level_generation/projects/xeen/x1/gen.py` `SLOT['skeletons']`
  at tier 0 in the world even when FULLER, so a rebuild keeps it; no rebuild needed: map_stats carries the tier).
  `build_world.py --only gen_maps`: only X1's map_stats row changed.
- Sites: X1 (fixed: `balance.py` X1 2-16 → 2-11, kill XP 1.14 → 1.09, Act I 1.15 → 1.13). Act I sweep: XD-01 2-4,
  XD-03 6-18 (Clan King boss), XD-04 4-20 (Head Witch boss), XD-05 5-12 (Drum-Master) are inside their bands with their
  bosses; **XD-02 reads 3-12 against a band of 3–10** (left for A2: a level-12 row placed in the mines, 2 over).
- Check: `tools/xeen/balance.py` prints each map's level range (X1 now 2-11, inside MAPS §0's band; no automatic
  band rule yet, NEXT for A2);
  `tools/maw/xeen_balance.py --check` passes (82 maps).
- MM6–MM9: none. MX: confirm MAW's Nightmare/Doom Dif raise on X1 does not lift the slot back to the C tier.

**F39, open containers with no inside (XD-02 p1). S models, engine decorations.**
- Cause: the cauldron XD-02 places (`cauld00`, `engine/models/mm6_deco_cauldron_pot.glb`) had its brew disc facing
  down, so the engine (which honours `doubleSided` and culls single-sided back faces) dropped it from above. The build
  scripts' lathe points a surface's front where the profile runs bottom to top, and flat discs were profiled from the
  axis outward. `check_winding.py` counts closed parts only, so it passed.
- Fix (S): the build scripts in `level_generation/decorations/mm6_dungeons_3d/fire/scripts/` (`build_cauldron.py`,
  `build_brazier.py`, `build_flambeaux.py`, `build_sconce.py`, `build_candle.py`, `fire_lib.py` links),
  `mm6_new_sorpigal_3d/props/scripts/` (`fire_parts.py` ember bed, `build_fountain.py` panels, `build_cauldron.py`
  links) and `mm8_3d/animated/scripts/build_candlestick.py` (cup floors under the candles). Rebuilt in Blender, every
  model `check_winding` 0, installed with `tools/install_model.py --engine`: `mm6_deco_cauldron_pot`, `brazier`,
  `brazier_unlit`, `flambeaux`, `sconce1`, `sconce1_free`, `sconce2`, `sconce2_free`, `candle`, `cauldron`, `campfire`,
  `logfire`, `fountain`, `mm8_deco_candlestick`.
- Sites: 58 container and fire models Xeen places checked: 14 fixed (above; placed on 60+ Xeen maps, e.g. the
  cauldron pot on DD-06/07/09/20 and XD-01–05/09/11/13/27, campfires on X1–X7); the rest fine (open barrels and their
  liquids, bucket, food bowl, MM7 cauldron, fruit bowl, goblet, metal bowls, MM8 campfire, every `xeen_deco_*`
  container). Left: `mm7_deco_7dec21` cask (closed, not an open interior); the lit brazier's LOD1/2 (3.9 % from one
  diagonal, far detail only); 57 non-container models (trees, corpses, torch wraps, crystals, cages) show the same
  back-face class at LOD0: a separate fault class for S.
- Check: `tools/xeen/check_open_interiors.py` renders every model Xeen places (bindings, overlays, `xeen_deco_*`) from
  above and eight 30°/60° directions and fails when ≥ 1 % (and ≥ 12 px) of what shows is single-sided back faces.
  Before: 15 faulty (the cauldron pot 47 % from above), exit 1; after: 58 checked, 0 faults
  (`f39/check_before.txt`, `check_after.txt`).
- Captures: before `output/xeen_fb/p2_engine/f39/cauldron_before.png`, after `cauldron_after.png`.
- `stale_bakes.py --check` 0. Open for S: after use the decoration reads "Empty Cauldron" but the shared model still
  shows the brew (one model for both states).
- MM6–MM9: a visual improvement on the MM6–MM8 maps that place these models (campfire: MM6 outc2, oute2, MM7 7d18,
  7d35, 7out01, 7out03, 7out04, out11, out14, t02, MM8 out02, out03, out05, out08; the ckfyr00 cauldron: 14 MM6 maps;
  the cauldron pot: MM6 6d17, 6d19, 6t1, 6t7, cd2; flambeaux, logfire, fountain, braziers, candles, sconces on MM6
  dungeons and towns; candlestick: MM8 d06). MM9: none.

**DECIDE (read-only deciders; for the orchestrator to number)**
1. Guild membership and dues (Vern's "Dues" does nothing) | Guilds stay open to all; every Xeen line that sells,
   prices or demands membership becomes a true line in the speaker's voice (Casper's wink kept as a true joke; Sarah,
   Brunhilde and Mordant unchanged); the unused `guild_membership` field is dropped; `towns.py` fails on
   membership-for-gold or members-only text and on the field | A4 (text, field, check), A3 (confirm tests). Option A
   (real membership gating guild purchases, MM4/MM6/MM7-faithful) was rejected as against "simple but fun" and the
   tested open guilds.
2. Skeleton Lords (level 16) on X1, above its 2–12 band | X1's skeleton slot to Dif 0 (A tier only; orcs and toads
   keep 90/8/2), a one-slot override of D-1.3; band check on the other Act I slots | A2, A5 (gen.py constant), MX.
   The decider marked the override of D-1.3 as its own reading, not a user ruling.

### F24-F28: Vertigo's town (agent `xeen-fb2-town`, 2026-11-23 ~10:20-11:40)

**The check (new): `tools/xeen/town_fit_check.py`** (`[<stem>...]`, or `--odm <build> --sketch <L4 sketch>` on a build;
`--list`). On every built outdoor map, on the ground as the game draws it: `walls.hollow` (a body finds neither land
nor face looking in under a wall's face: its foot stands over the land), `walls.buried` (the land rises over a wall's
top just behind it), `houses.buried_door` (the land 32-160 before a door stands over 48 above its sill),
`gates.road_off` (the road tiles through a wall's `gates` entry or a town_walls.yml seal are centred over 128 off the
passage's middle), `culverts.ground_inside` / `dry_water` / `open_side` (land climbing into a culvert's tunnel; its
water on dry land; its tunnel open at the side), `actors.over_water` (a walking actor placed over a water tile, on a
bridge or a shore). `towns.py --strict` runs it (an ERROR; the sites still waiting for their map's rebuild are listed
in `tools/xeen/town_fit_pending.yml` and are warnings there; a listed site that is fixed becomes an error, so the list
only shrinks). Before: 52 errors on 7 maps (`output/xeen_fb/p2_town/fit_before.txt`); after: X1 0, 32 pending.

**F24 NPCs stuck.** Cause: p1, Vertigo Bridge's guard pair was placed on the bridge over the creek and beside it; a
guard (Medium wander 2,560) walks back to its home, steps off the bridge's side over water and sticks against the rail
(the engine's water rule lets a body whose disc still touches the deck stand over a water tile: REQUESTS). p15, the
peasant was in the hollow under the terrace wall (F26's cause). Fix (X1 `gen.py`): the bridge pair on land at the
bridge's north head (52.0/53.0, 49.3); the gate pairs re-centred on the moved gates; Orothin (4047, Long wander) from
a shore tile at (63.6, 64.6) to land at (62.35, 62.85) (D-85 kept: 6,698 from the nearest hostile spawn). Check
`actors.over_water`; the hollow is `walls.hollow`. Sites: X1 2 actors over water (fixed); no other map has one.

**F25 culverts.** Cause: the D-95 sunken entrance's mouth was a `culvert`: its 128-deep tunnel ran back under the bank,
whose nodes keep the creek's level (a `heights.nodes` cut there is refused), so the land climbed 48-64 into the arch as
grass under the black face (p3), and its water face lay on the dry ditch floor, drawn as a flat blue strip; the
outfall's block (a 16-thick headwall, the cap 36 behind it) left its tunnel open at both sides over the creek (p18);
the revetments' feet hung 50-100 over the ditch floor. Fix at the source, `tools/xeen/kit_pieces.py`
`SunkenEntrance`: the mouth is a dark arched door in the end face (`doorway`: frame = the end face, 112 deep, sill on
the floor; no tunnel, no water; the cap from the frame's back), the revetments' feet go down to the floor (`raise`),
the outfall gets cheeks over its tunnel's sides, and `structures(..., quay=True)` runs the quay on to the outfall with
two wings beside it (X1 uses it: one stone quay from the arch to the creek). The kit also takes `under` (rows behind
the face cut too) for a site whose bank is not water. Sites: X1 culvert grate and outfall (fixed); X4 Asp's undercroft
stair (`xd25_stair`, the same kit: land 56 into its tunnel) fixed in the kit, takes effect at X4's next rebuild
(pending); D1 `dd01_outfall` (land 188 inside its tunnel, water on dry land, an open side: D1's own culvert, not the
kit; pending, needs a look and a D1 generator change).

**F26 walls against houses and slopes.** Cause: a studio wall's foot is its centre line's lowest land less 64 and its
top the highest plus `height`. Vertigo's terrace wall stood on the middle of its one-cell step (row 41.5, land 896):
a 512-thick slab from 832 to 944 across the slope, 192 over the street under its face (the hollow of p15, the open
underside at its ends, p5), the terrace's grass rising 208 over its top behind it (p6's gap). Fix (X1 `town.py`
`retaining_walls`): `raise` takes the foot 64 into the street and the top 48 over the terrace (the slab is the step);
the town hall's gap exactly the steps' and its tower's width (48.375-49.125), `joints_ok` for the two ends flanking
the steps beside the hall's tower (`town_walls.yml`). Sites: X1 terrace walls 1-5 and the culvert's revetments
(fixed); X2 Rivercity `north_wall_1`-`4`, `south_wall_1`-`5` (the same slab-on-a-slope: hollows 128, land 74-144 over
their tops; pending, X2's generator wants the same `raise`/`height` rule); D3 `gorge_face_e1`-`e3`, `gorge_face_head_w`,
`_e` (hollows 45-88, land 56-58 over the tops of the gorge's cut faces; pending, to be looked at: cut faces may be
meant to stop under the rim).

**F27 house buried.** Cause: the studio levels only the nodes under a plot; the fringe home at (49, 33.5) faced east
into the hillside, the land before its door 56 over the sill (p14); its neighbour at (56.5, 34.5) faced north uphill,
132 over. Fix (X1 `town.py` `_FRINGE_AT`): the first faces south (downhill), the second east (off the slope).
Sites: X1 2 (fixed); X2 `farmsteads#2` (88 over; pending); X7 `xd05_gate` (two leaves, 70 over: the dungeon gate's
door set below its approach; pending, to be looked at).

**F28 road misses the gate.** Cause: a road on the line x lays its tiles on the cell x..x+1 (its middle x.5); Vertigo's
gatehouses and bridge stood on the lines, half a cell off their roads, the cobbles running into the tower (p19).
Fix (X1 `town.py` `GATE_HOUSE`, `gen.py` bridge): the north, east and west gatehouses and the bridge on their roads'
middles (52.5, 38), (62.5, 46.5), (41.5, 44.5), bridge x 52.5; roads unchanged; walk and seals moved with them.
Sites: X1 3 gates and the bridge (fixed); D1 Castleview's north gate (253 off) and Queen's gate (`wall_ne`, 469 off),
D6 the Necropolis gate (`np_gate_wall`, 249 off) (pending).

**X1 rebuilt and installed with its bake** (11:28, under the X1 lock; an 11:17 install still had the kit's `under`
row given under the creek's bank, which the studio refuses, so the quay stood 207 too high: fixed and reinstalled, through `tools/heavy.sh`; it carries the wild
agent's F29-F33 work too): audit 0 errors, wall_check 0, town_fit 0, door_check 0, check_exits 0, D-85 0, empty
zones and props pass, house signs 0, key_npcs written, actor heights 0, `check_wild.py` X1 clean, `stale_bakes
--check` 0, `towns.py --strict` 0 errors (32 pending warnings), `build_world.py --check` 0 differ; X1 walk and
hostility playtests, `rim_fall`, `rim_fall_pit`, `x1_start_nothing_in_reach` pass. Scripts:
`output/xeen_fb/p2_town/tools/` (`patch_x1*.py`, `x1_build.sh`, `x1_install.sh`), logs `run_x1/`.

**Captures.** Player pictures `output/xeen_fb/p2_town/before_player/`; before from assets_dev
`output/xeen_fb/p2_town/before/` and context `ctx/` (sheets `before_sheet.jpg`, `ctx_sheet.jpg`); after `after/`,
`ctx_after/` (`after_sheet.jpg`, `ctx_after_sheet.jpg`); wild pins after `wild_after/` (`wild_sheet.jpg`, before |
after). p6's pose now stands inside the wall: its after pictures are the terrace and street views. All eight pins
resolved with after pictures; the wild pins p7, p9, p12, p16 too (p8, p11 wait for the studio fixes).

**Relayed studio and engine requests (built by `xeen-fb2-engine`'s sub-agents, 2026-11-23)**
- Studio binary `openyamm-studio/build-xeen/oymap` (built 11:40; `oymap_tests` 516/516). No map rebuilt.
  - F31 tents and wagons (`core/OutdoorThings.cpp` `raiseTent`): one drawn canvas; the inner face kept invisible for
    collision when its texture is the canvas's, else 2 units inward (the game draws outdoor faces both sides,
    `OutdoorRenderer.cpp`, but collides one side). New warning `faces.back_to_back` (`core/Coplanar.*`, audit) with
    check_faces.py's open-space filter. Barriers ~4024/~5992 unchanged (both faces hidden).
  - F30 ruins (`core/OutdoorBuildings.cpp` `raiseRuinWall`, helpers `ruinPieces`, `ruinTops`, `ruinStandsAt`,
    `ruinMitre`): mitred inner corners, end faces up to the higher wall, pieces split at bay edges, inner foundation
    and sill where the wall is gone. Test "F30: a ruin is a closed shell" (box, 8- and 12-sided).
  - F29 waterfall cut (`core/OutdoorFalls.cpp` `shapeOutdoorFallLand`): with rock sides only the nodes under the sheet
    (+32) are lowered; X1 nodes (104,59), (104,61) stay at 576 (the p7 pit). Check X4's falls after its rebuild.
  - Town requests: audit warning `houses.buried_door` (`core/TextureAudit.cpp`, town_fit_check.py's rule) fires on X2
    `farmsteads#2`, X7 `xd05_gate`; build warning `gates.road_off` (`core/OutdoorBuild.*`) fires on D1 `wall_ne`, D6
    `np_gate_wall`, bridges D1 `east_bridge`, D2 `footbridge`, X2 `ogre_bridge`, X4 `kings_bridge`, X5
    `golem_bridge` (it does not read `town_walls.yml`, so the Python check's D1 Castleview gate is not seen).
  - check_faces.py on scratch builds: X1 back_to_back 11 → 5 (culvert, Witch Tower door), open_edge 4 → 0; X4
    back_to_back 25 → 0, coplanar 41 → 40; D3's remaining pairs are its south gatehouse.
  - Maps that change when rebuilt: all 13 outdoor maps (ruins); tents/wagons d1 d5 x1–x7; falls d1 d2 d3 d4 x1 x4.
- Engine question F29 (in-map MoveToMap stops map timers): no fault. X1's opening message (timer 102, `m1.opening`)
  pauses the world in game and headless; `tests/scenarios/xeen/rim_fall.yml` now closes it and asserts the landing
  and the timer firing again.
- Town requests to the engine (F24, F25), a sub-agent of `xeen-fb2-engine`; scratch `output/xeen_fb/p2_engine/engine2/`:
  - F24 guards stuck on Vertigo Bridge (p1): the suspected disc overlap was **not** the cause (25,000 logged steps, no
    walker over water off a deck). Cause: the water rule took a deck as support only while the actor's own support
    state said so; a guard on the humped deck by the kerb sank 0.2–3 under the surface, its state flipped to
    terrain/airborne, and every step after counted "over water" (blocked 9,210 steps in a row). Fix:
    `OutdoorMovementController::hasNonFluidBModelFloorUnder` (map faces, not the actor's state; replaces
    `hasNonFluidBModelActorSupport`), `outdoorWalkerHasDeckUnder` / `outdoorWalkerStandsOverWater` in
    `OutdoorWorldRuntime.cpp`: a step's centre within 8 of a deck, a deck 32 under to 32 over the feet. Test hook
    `IGameplayWorldRuntime::actorStandsOverWater`, scenario key `actor_visible: {over_water: bool}`; unit test "a
    walker's deck over water is the model floor under its centre near its feet"; scenario
    `tests/scenarios/xeen/x1_bridge_walkers.yml` (five wandering guards, 120 s). MM6–MM9: walkers near docks and
    bridges no longer freeze on a deck; a step whose centre leaves the deck over water is refused; a deck more than 32
    above the feet no longer counts; a walker may step from land onto a deck within 32. The old X1 guard placed inside
    the deck slab was data (already fixed by the town agent). Captures: `engine2/cap/x1_head_before/04-p1_bridge.png`,
    `engine2/cap/x1_now_after/01-p1_bridge.png`.
  - F25 model water flat (p3): the same in MM7 (Steadwick's well). Model water has no seabed and from above almost no
    reflection, and nothing shaded the body colour. Fix `game/shaders/fs_water.sc`: on model water and any water
    without a capture, the waves shade the body ±35 % and the sky fill ±20 % (not tar, lava, falls). All worlds: wells,
    fountains, canals, culverts and uncaptured terrain water show waves. Captures `engine2/cap/x1_head_{before,after}/`,
    `engine2/cap/mm7_{before,after}/`.

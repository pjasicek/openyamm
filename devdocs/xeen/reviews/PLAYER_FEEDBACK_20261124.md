# A player's pins, 2026-11-23 midday to 2026-11-24 01:12 (Xeen v3.1/3.2, X1–X3 and eight dungeons)

The same player as [PLAYER_FEEDBACK_20261123.md](PLAYER_FEEDBACK_20261123.md) sent a second archive
(`pins_inbox_yamm.7z`, 75 pins). Its first 20 pins are that file's F24–F39. The **55 new** ones are filed here:
X1 8, X2 10, X3 9, XD-02 4, XD-03 2, XD-04 4, XD-05 9, XD-08 1, XD-21 2, XD-24 4, XD-27 2. Most were made on v3.1;
3.2 went out at 2026-11-23 22:47, so pins from before then can show faults 3.2 already fixed (listed below).

- Pins are filed in the map projects: `devdocs/xeen/briefs/<map>/L4/review/pins.yml` (ids below). Use
  `oymap pins list|claim|tour|resolve` (openyamm-studio/README.md, "Pins from the game").
- Pictures: `output/xeen_fb/p3_20261124/original/<stamp>-<map>.png` (with the pin YAMLs), and
  `<project>/.oymap/pins/pictures/`.

**The rule (the user's, 2026-11-21):** every family is fixed at its source (generator, shared kit, engine, common Lua,
data), then on **every** site of its kind in the Xeen world, with a check that keeps it fixed. The pinned spot is only
the example. See [briefs/FEEDBACK_FIX_RULES.md](../briefs/FEEDBACK_FIX_RULES.md).

## Probably fixed by 3.2 already (confirm with a capture at the pin's pose)

| Pin | Text | Fixed by |
| --- | --- | --- |
| X1 p20 [-7963.2, 4266.2, 641.0] yaw 4.841 | "not working" (Vern's Dues) | F35: no guild membership in Xeen |
| X1 p24 [13559.2, 11625.9, 809.3] yaw 2.182 | "z fighting" (Travellers' tent) | F31: tents. `check_faces.py` X1–X3: no tent finding |
| X2 p1 [12409.1, 20531.4, 1153.0] yaw 2.791 | "z-fighting" (Rangers' tent) | F31 |
| X3 p6 [-17842.5, 15356.8, 1376.6] yaw 2.010 | "z-fighting" (Evil Ranger camp tent) | F31 |
| X3 p2 [11549.3, 11762.9, 1025.0] yaw 5.053 | "z-fighting and the barrel is clipping" (Ebenezer's Tent) | F31 for the planks; the barrel through the tent wall is **F40** |
| X3 p4 [8847.8, 14751.2, 1761.0] yaw 5.372, p5 [9343.1, 14583.9, 1761.0] yaw 5.919 | "textures missing" (Ruins of Newcastle: paper-thin walls) | F30: ruin walls closed. `check_faces.py` X3 clean |
| XD-05 p1 [-90.7, 205.2, 0] yaw 1.401 | "is this intended, that you can't go back?" (the double door at the start) | 3.2: hidden cave-mouth exits on six dungeons, XD-05's among them (a Discord report) |
| X1 p25 (picture only) | Norman's greeting drawn over the shelves | F36 (the pin itself is about the stock: F52) |

The classic-kit rebuild running on 2026-11-24 (U-14/U-15) left new `check_faces.py` findings on X1 (culvert grate and
cap, Witch tower door, culvert outfall) and X2 (Nystor ship): for that work's owner, not this file's families.

## The new pins, grouped into families

Poses are `position [x, y, z]`, `yaw` radians, from the pin files. "Agent" is the run that takes the family.

| F | Family | Pin(s), map, pose, what the picture shows | Agent |
| --- | --- | --- | --- |
| F40 | **Props inside props or walls; items hidden in them** | XD-05 p6 "z-fighting" [2477.8, 7919.6, -384] yaw 1.028: a trash heap, a crate and a barrel inside one another. XD-02 p2 "there is an item but i cannot pick it up, the trash heap is hiding it" [12895.6, 6658.3, -192] yaw 2.501. XD-27 p1 "clipping" [1361.6, 3421.7, 0] yaw 1.016: a bucket half inside the cave wall. X3 p2 (the barrel through Ebenezer's tent wall) | dungeon (indoor), outdoor (X3) |
| F41 | **Monsters that hold back or get stuck** | XD-05 p7 "they don't want attack me" [2218.1, 12589.4, 320] yaw 1.487 and p8 "they attack when i am near" [2180.8, 12513.9, 298.3]: two orcs by a dark doorway, hostile, standing still until the party comes close. XD-04 p1 "he is not coming to me" [-1401.7, -1264.7, 0] yaw 3.350: a goblin behind a table. XD-03 p2 "monster gets stuck between crystal an stalagmite" [1532.1, 1626.9, -604.6] yaw 3.045: a cave spider. XD-03 p1 "i guess this is intended" [3144.3, 3423.6, -512] yaw 1.492: two Mad Dwarves standing at double doors | engine (AI), dungeon (props on paths) |
| F42 | **Invisible walls in openings monsters attack through** | XD-05 p5 "here seems to be an invisible wall" [2225.3, 7731.6, 192] yaw 1.858: an Orc Archer in a window-like opening. XD-04 p3 "she cast a spell but there is an invisible wall" [3139.4, 742.1, 700] yaw 1.331: the Schoolmistress behind the classroom's open front | dungeon |
| F43 | **Places the party cannot leave** | XD-02 p4 "if you fall down, you can't go out" [11456.9, 4645.0, -1792] yaw 2.678: the foot of a scaffold shaft. XD-02 p5 "you get stuck here" [9273.1, 4543.4, -384] yaw 5.567: wedged under sloping planks | dungeon |
| F44 | **Doors drawn wrong** | XD-24 p2 "the texture on the door should be flipped" [-2173.4, 658.5, 0] yaw 5.772, p3 [-614.5, -3459.8, -640] yaw 2.552, p4 [-2142.4, -3377.2, -640] yaw 2.553: the skull knocker is on the hinge side. XD-05 p3 "from this angle the door disappers" [657.2, 1996.2, 192] yaw 3.162. XD-08 p1 "z-fighting" [1836.8, 7104.5, -640] yaw 2.236: magenta specks flicker on the wall behind a portcullis | dungeon (engine if a renderer fault) |
| F45 | **Arrivals in the thick of it** | XD-24 p1 "the spawnpoint is too far in to the dungeon." [0, 704, 0] yaw 1.555: Gnome Vampires on the party at once. X3 p1 "maybe set the spawnpoint further away" [17664, -5120, 1009] yaw 2.648: back out of XD-24 facing a wall. XD-02 p3 (second half) "if you leave the dungeon, the monsters will kill you" | dungeon, outdoor (X3) |
| F46 | **A destructible wall opens onto the void** | XD-27 p2 "after i destroed the layer, you can look through here" [-2421.8, 3450.4, 32] yaw 5.555 | dungeon |
| F47 | **Hard to use, or a dialogue for a simple thing** | XD-02 p3 "this was hard to activate" [3137.5, 5192.5, 256] yaw 2.711: a small winch. XD-05 p9 "i know you could decide in vanilla xeen, but do we really need this here?" [-2623.4, 7153.4, -192] yaw 2.970: the Spirit drum's choice (as F13). X3 p9 [11900.4, 11021.4, 1025] yaw 1.454: Ebenezer's tent is clicked from deep inside; "put the trigger point more to the beginning or put a door in front of it", and check the other tents | dungeon, outdoor (X3) |
| F48 | **Bridge and causeway ends: a step the party cannot climb** | X2 p4 "maybe fill the gap" [110.7, 2791.5, 1025] yaw 1.626: The Great Bridge. X3 p7 "i cannot enter the bridge" [274.2, 4303.5, 890.9] yaw 4.723: The causeway | outdoor |
| F49 | **Town buildings jammed together, walls off the ground** | X1 p21 "there a many like this" [-1497.2, 4853.3, 609] yaw 4.649: two houses' walls overlap and a plinth sticks out. X2 p2 "this does not look good" [4714.2, 3689.6, 878] yaw 0.015: two houses squeezed between each other and the town wall. X2 p5 [-5677.5, 3619.6, 647.3] yaw 0.104: a wall hangs over the ground beside a house. X2 p6 [1874.9, 8282.0, 1030.6] yaw 1.845: a barrel against market stalls and a cut path strip. X2 p10 "clean it up a bit" [-8390.5, 2295.5, 733.7] yaw 4.343: a pier's pointed deck sticks out of a mound | outdoor (with the classic-kit work) |
| F50 | **Ruins on uneven ground, untextured entrances** | X3 p3 "moce it to a more even ground" [9225.8, 13035.6, 1453.2] yaw 2.228: Newcastle's ring arch and tower on a slope. X3 p8 "missing texture" [-15342.1, -9325.6, 1121.9] yaw 4.674: the Tomb of a Thousand Terrors entrance is plain brown. X2 p9 "missing texture" [-15976.7, -6928.4, 872.3] yaw 0.656: a thin strip and a black slot in a ruin wall | outdoor |
| F51 | **Pick-ups nobody can reach** | X1 p23 "is this intended, that these barrels are not reachable?" [-23106.0, 8745.8, 956.9] yaw 2.520: a Green Barrel on a hilltop | outdoor |
| F52 | **Shops and services** | X1 p25 "if roll for a new stock ... always the same" [-10665.4, 10257.2, 641] yaw 1.696: Norman's New stock (1000 gold) brings back the same items. X1 p27 "schedule is not working, like in the other world" [766.5, 8978.0, 641] yaw 5.169: Vertigo Stables, "Sorry, come back another day". X2 p3 "not working" [5094.6, 1754.0, 1025] yaw 2.015: Lindon's Work offers 100 gold for a week, then refuses | engine, data |
| F53 | **Status text vanishes too fast** | XD-21 p1 "the duration of the text here is too short, i have to say, they are everywhere too short" [412.6, 4767.2, 0] yaw 3.980 | engine |
| F54 | **Sprites: no loot, and tiresome** | X2 p7 "Sprites are giving no loot. Even the bosses." [-7744.6, -310.9, 957.4] yaw 3.425 (P.S. Queen, Medusa Sprites). X2 p8 "Sprites are annoying." [-8688.3, -2868.2, 1044.3] yaw 4.896; the player on Discord, 2026-11-24: "With p8 i mean the sprites are always in the air" (they hover out of melee reach; see "X1 p26 and X2 p8, as the player meant them") | engine, data |
| F55 | **Balance** | XD-05 p2 "a bit too much" [63.1, 1312.2, 0] yaw 1.395: nine orcs in the first room. XD-05 p4 "you can pull the mobs to easily" [1846.6, 2471.6, 192] yaw 4.124. X1 p26 "maybe you have a maximum here" [6481.2, -10500.9, 538.8] yaw 2.530: the toad swamp; the player on Discord, 2026-11-24: "you can only have one root, but if you throw it on the floor, you can have as many as you want. I got 60 potions with that" (the Phirna root exploit, not the toads; see "X1 p26 and X2 p8, as the player meant them"). XD-04 p4 "xp from them are, i think, small" [-2666.1, 2435.2, 1280] yaw 3.236. XD-04 p2 "you only get a scroll, in exchange for a gem, that has more value" [1952.9, 529.6, 640] yaw 0.099: the skull shelf | engine (decider) |
| F56 | **MAW: no boss in XD-21** | XD-21 p2 "in MAW there is no Boss here in this Dungeon" [3021.6, 3960.7, 256] yaw 0.005 | engine (MX lane) |
| F57 | **The Giant Toad looks strange** | X1 p22 "this looks strange" [-4934.5, -1925.0, 609] yaw 5.977 | engine (creature check) |

Agents: **dungeon** (F40 indoors, F42–F44, F45 indoors, F46, F47 indoors), **engine** (F41, F52–F57; this run's only
builder), **outdoor** (F40 X3, F45 X3, F47 X3, F48–F51; after the classic-kit install queue of 2026-11-24 and agreed
with its owner, since both change the outdoor generators of X1–X3).

## Results

(appended per family)

### F40, F42–F47 indoors: the dungeons (agent `xeen-fb3-dungeon`, 2026-11-24 ~12:30–14:00; for A7, A8, A1)

Before captures at every pin's pose from that morning's assets_dev: `output/xeen_fb/p3_dungeon/before/<map>/` (tours
`before/<map>.tour.yml`, `mktours.py`/`runtours.sh` beside them). Each fault is still there, except the ones that need
a state a tour cannot set (an open door, a broken lair). Checks written: `tools/xeen/check_prop_overlap.py`,
`check_arrivals.py`, `check_door_leaves.py`, `check_wiring_rules.py`, `texture_alpha_bleed.py`, and a rule in
`check_drops.py`. Rebuilt, installed and baked: XD-27, XD-05, XD-02 (playtests pass, audit 0 errors).

**F40, props inside props or walls; items hidden in them.** *Cause:* the game collides with a decoration as the
cylinder of its table radius, and every generator and hand L4 spaces props by that radius, but the 3D models are drawn
2–4 times wider (`7dec10` trash heap drawn 116–146 against 52, `sklplrev` skull pile 120 against 30, `dec05` skeleton
100 against 16). No check looked at props overlapping or entering walls. XD-05's heap is the `mm6_deco_trasheap.glb`
model itself (its crate and barrel are parts of the model): a model fix in `level_generation/decorations/
mm6_dungeons_3d/containers/`. *Check:* `tools/xeen/check_prop_overlap.py` (drawn outlines from the bound GLBs as
`DecorationModelSet::placementFor` places them): `prop.overlap`, `prop.wall`, `item.hidden` errors, `prop.squeeze`
warnings; it finds XD-02's item under the heap, XD-27's bucket and bowl in the wall, XD-03's crystal/stalagmite squeeze.
*Sites:* 65 errors on 38 maps (19 overlaps, 44 in walls, 2 hidden items: XD-02 `spawn:ore_heap_item`, XD-03
`spawn:item_spoil`), 143 warnings; the list with each site's source line is `output/xeen_fb/p3_dungeon/f40/all.txt`.
**Not fixed yet:** moving them is one edit per site in 38 sources and a rebuild and bake of each; the studio audit
should own the rule (REQUESTS). Left for the next dungeon pass.

**F42, invisible walls in openings.** Not reproduced: both openings are open in the built maps (XD-05 p5 is the drum
hall's doorway at the foot of the bat chimney, x 1856, z -384..128; XD-04 p3 the schoolroom's swinging double door).
The fault needs a monster fight at the pose, which a tour cannot stage. Spec for the engine agent under REQUESTS (a
headless `fire_actor_projectile` / `cast_spell` repro at both poses). Likely related: the open-away leaves of F44.

**F43, places the party cannot leave.** *Cause:* `check_drops.py` did find XD-02's chasm (z -1792) and the trestle's
deck slivers, and XD-02's NOTES kept them "by design: reached only by stepping off the moving car"; the player fell
off the car. *Fix:* XD-02 gets `ladder:chasm_north` (L4 objects.yml) from the chasm floor up the north wall to the foot
drift's gap; `check_drops.py` now says a mover never excuses a pocket. XD-02 rebuilt: 0 pockets (was 5), audit 0
errors. p5 (wedged under sloping planks at the east line's turntable stop): the east cart's gate (door 5) and deck are
sliding movers with the default `bodies: ignore`, so they close through a party standing in the gateway; studio spec
under REQUESTS (sliding doors and gates reopen on bodies, as hinged leaves already do). World-wide `check_drops`: run
after each rebuild as before.

**F44, doors drawn wrong.** (1) *XD-24's knocker on the hinge side:* the studio lays a hinged leaf's back face with the
front picture unmirrored, so a handed picture (cndl's knocker) shows its hinge edge at the free edge from the back.
`check_door_leaves.py leaf.back_unmirrored`: 91 of 225 hinged leaves on 22 maps (dd02, dd04, dd05, dd10a–c, dd11b,
dd12, dd13, dd24, fd02–fd04, xd02, xd03, xd13, xd14, xd20, xd22, xd24, xd26, xd27). Studio fix under REQUESTS (no
vocabulary mirrors a single hinged leaf). (2) *XD-05's door that disappears:* an open-away leaf swings through its
doorway into the other room but its faces are listed only in the room it closes from, so it is not drawn while only
the other room is seen (the gate leaves seen through the firing step's window). `leaf.swing_room`: 74 leaves on the
maps in `output/xeen_fb/p3_dungeon/door_leaves_before.txt`. Studio fix under REQUESTS. (3) *XD-08's magenta specks:* the
six Xeen cutout textures (`xkportc`, `xngrille`, `xopoles`, `xwward`, `xwcage`, `xufield`) keep a rim of opaque magenta
halo texels and dark magenta under their holes, which the cook's box-filtered mips mix into the bars;
`tools/xeen/texture_alpha_bleed.py` finds them (and `--write` clears the halo and bleeds the bars' colour under the
holes). Applied and recooked, it did **not** remove the specks at the pin (they changed pattern: a renderer fault with
cutout door faces, spec under REQUESTS), and the six textures are dependencies of 23 lighting bakes, outdoor maps among
them, so it was reverted (sources, x2 and cooked files as committed; XD-02 and XD-05 rebaked; `stale_bakes.py --check`
0). Apply it with the next round of bakes of those maps. Before/after of the trial: `before/xeen_xd08/`,
`after/xeen_xd08/`.

**F45, arrivals in the thick of it.** `tools/xeen/check_arrivals.py` (every party start and every MoveToMap landing;
hostile placed actors within the indoor detect range 5,120 with a clear line, the engine's two rays): 33 `arrival.hot`
on 24 maps (XD-24's start among them: Gnome Vampires a18/a19 see the party at 1,328 and 1,600), plus deep/near
warnings; the table is `output/xeen_fb/p3_dungeon/f45/all.txt`. XD-24's better arrival is (0, 1600, 224) facing south
on the coffin stair (no monster sees it, the exit 380 away), but the landing that matters is written by X3's `into`
(`x3/gen.py:591`), an outdoor map: for the outdoor agent with XD-24's `start` (`xd24/gen.py:447`). XD-02's exit lands
at X1 (-10240, 15872, 1184) with three orc spawn markers (6–9 orcs with archers) 3,508–4,735 away: X1's D-85 check
(outdoor agent). Not fixed: each site moves a start in a dungeon generator and the matching `into` in its outdoor
neighbour; open-air maps (D7, P1–P4, X8) need a ruling first (DECIDE).

**F46, a destructible wall opens onto the void.** *Cause:* XD-27's lair event hides `panel:sail`, a wall panel: the
panel is the wall itself, so the hole goes to the void. The studio already has covering panels (`cover: true`, DD-13's
hides: the wall built whole behind). *Fix:* `xd27/gen.py` makes the sail a covering panel; rebuilt. *Check:*
`check_wiring_rules.py hide.panel_wall` (no other site in the 69 projects).

**F47, hard to use, or a dialogue for a simple thing.** (1) *Destroy questions:* XD-05's three drums and XD-27's lair
now burn or break at the click (wiring `question` removed; the playtests, `11_orc_caves`, `15_ogre_lair`,
`x1-tam_oslos_son`, `q-c23_ogre_boulders` and the two maps' playtests no longer answer). `check_wiring_rules.py
ask.goal` lists the rest: open (to do on their next rebuild) X8's three nests, DD-23's ten roost rocks, XD-19's six
generators and machines, XD-25's transformer; for the decider (D-25 approved them as real choices, or a cost may hang
on them) DD-13's two fort pits, XD-23's fire pit, XD-16's two skulls, FD-04's five shrines. (2) *XD-02's winch:* the
clicked drum is 80 high and its iron head and bars answer nothing (`click.covered`; also XD-01's five tanks, warnings);
studio vocabulary spec under REQUESTS.

*Runs (14:00):* XD-27 playtests 4 of 4 (fall, hostility, in, main), XD-05 4 of 4, XD-02 3 of 3 (main 218 steps), audit 0
errors on all three, `check_exits` 0 errors, `check_drops` XD-27 0 and XD-02 0 pockets (XD-05: the prisoner pit, kept
with its ladder as before), `xeen_pack_reserve` and `xeen_balance.py --check` clean, `stale_bakes.py --check` 0. Story
segment 11 (XD-05) passes; 15 (XD-27) fails in 3 s on a stale checkpoint (X4 rebuilt by the classic-kit work since; the
runner prints STALE), while side quest `q-c23_ogre_boulders` (XD-27's lair from a new game) and `x1-tam_oslos_son` (the
drums) pass. Rerun 15 from a fresh chain after the outdoor installs.

### F41, F52–F57: monsters, shops, status text, sprites, balance, MAW, the toad (agent `xeen-fb3-engine`, 2026-11-24 ~12:50–14:30; for A1, A2, A3, A4, A7, MX, S)

Scratch and captures: `output/xeen_fb/p3_engine/`. Binary `build/game/openyamm` (built 13:1x with the changes below);
unit tests 3,186 of 3,186 pass, the 16 release scenarios pass, the two new runtime tests pass. (The full
`openyamm_runtime_tests` run segfaults at "quick Heal goes to the member most in danger" when run after the other
cases, with or without this run's tests; the case passes alone. Not from this run; for A1.)

**F41, monsters that hold back (XD-05 p7/p8, XD-04 p1, XD-03 p1). Map data, not the AI.**
- Cause: the five actors are placed `immobile: true` in their map projects (XD-05's gate guards `guard_e`/`guard_w`, Orc
  Guard 11032; XD-04's `warden`, Gremlin Guard 11012; XD-03's `gate_guard_1/2`, Mad Dwarf 11050), and the rows have no
  missile and no spell: they fight only what walks up to them and can be shot from anywhere. The shared AI does what it
  should with an immobile monster; no AI change (MM6–MM9 untouched).
- Check: `tools/xeen/check_immobile.py` (+ `check_immobile.yml`, the placements held on purpose with the reason: the
  skyroad and heights golems D-1.2 on D7/X8/X9, XD-19's throne guards freed by script D-98, XD-13's lagoon ambush D-4).
  Every objects.yml monster that is immobile (or whose row moves `stand`), hostile, unleashed and melee-only is a
  finding. 142 such placements; **6 findings**, exit 1: the five pinned actors and XD-05's **Drum-Master** (boss on his
  scaffold). Fix for the dungeon lane (REQUESTS): `immobile: true` → `leash: <radius>` (about 600; the guard keeps its
  post and fights within the circle), rebuild XD-03/04/05; the check then exits 0 (`f41_immobile_findings.txt`).
- XD-03 p2 (a Cave Spider wedged between a crystal and a stalagmite): prop spacing, for the dungeon lane (two
  colliding props closer than a monster's width on a walk line; the prop overlap audit of request 5 could carry it).

**F52, shops and services. Engine (schedule), data (Lindon), no change (stock).**
- Schedule (X1 p27): Hob in Vertigo Stables talks (F1's talking proprietor), so the house opens on his talk: the
  dialogue's source is the NPC and the stable only its host house. The Schedule popup checked "a house dialogue whose
  source is the house" and closed itself in the frame it opened. Fix (A1, shared):
  `GameplayTransportSchedule::dialogueIsInHouse` (the house's own screen, or a talk whose host house it is), used by the
  popup. Sites: every Xeen stable and boat with a talking proprietor (16 stables and boats, e.g. Kramer, Lucio, Idris,
  Hob, Garrick, Nystor, Ned, Oskar, Gorm); MM6–MM8 proprietors do not talk and MM9 docks use their own path, so no change
  there. Test: "a stable's Schedule shows over its own screen and over its talking proprietor's talk"
  (`tests/GameplayUiRuntimeTests.cpp`, runtime tests).
- New stock (X1 p25): measured, not broken. MAW's paid reroll of Norman's Ironworks (4001) and an MM7 weapon shop gives
  five different shelves in five stockings (test "MAW's paid new stock gives a weapon shop new shelves",
  `tests/MawMm9ShopRuntimeTests.cpp`). The stock is keyed by the save's seed and the stocking's number
  (devdocs/maw/RANDOMS.md 7.1), so **a reloaded save rerolls the same "new" stock again**, which is what "like the trash
  heap, always the same" describes; MAW's own reroll is unseeded. DECIDE 1.
- Lindon's Work (X2 p3): the offer never worked. Decider (after D-107, Vern's Dues): honest text. `source/npcs/x2.yml`
  4136 topic 16: "I used to pay 100 gold for a week of work. Then the robbers under the bridge took every job in town and
  paid themselves. There's nothing left for honest hands." `build_world.py`: only `npc_topic_text.txt` 47565 and
  `xeen_quests.lua` changed. zh-cn until the next `l10n.py update`.

**F53, status text vanishes too fast "everywhere" (XD-21 p1). Engine, every world.**
- Cause: MM6–MM8 (and OpenYAMM) hold every status line 2 s (OpenEnroth `StatusBar::EVENT_DURATION`); Xeen's event texts
  run to 90–150 characters (their scripts give 4–7 s), which is 15–25 characters a second.
- Fix (A1, shared): `GameplayUiController::setStatusBarEvent` keeps a line at least its reading time,
  `statusTextReadingSeconds` = characters / 12 (a CJK character counts 2.5), at most 12 s; a script's longer time stays;
  0 s still shows nothing. Lines up to about 24 characters keep the original 2 s, so MM6–MM8's short lines are
  unchanged; XD-21's sluice line (89 characters) stays 7.4 s instead of 6.
- Test: "a long status line stays up long enough to read; a short one keeps the original 2 seconds"
  (`tests/SpellbookUiLayoutTests.cpp`); the older status tests pass unchanged. No capture (a timing change).

**F54, Sprites drop no loot; Sprites are annoying (X2 p7, p8). A2 data and generator.**
- Cause: the Sprites (and the Darkside sprites, Sharla) borrow the Will o' Wisp's descriptor, whose SpriteDead is
  `null`: no corpse, and the game then drops none of the table loot (MM6–MM8's rule for wisps and elementals). Nine rows.
- Fix: `tools/xeen/gen_monsters.py`: a row whose borrowed descriptor has no dead sprite must say `corpse: dying` (a body;
  the dying sprite stands for the dead one, the model ends in its death pose) or `corpse: none` (vanishes as in MM6–MM8),
  else the build stops; `hit_material` overrides the struck material. `monsters.yml`: sprites and dark sprites
  `corpse: dying`, `hit_material: Flesh`; robots, fire and air elementals `corpse: none` (MM's convention; their table
  loot stays lost, noted). Only `monster_descriptors.txt` changed (9 rows).
- Annoying (the touch change stands; the player meant something else, the sprites hovering out of reach: fixed in
  "X1 p26 and X2 p8, as the player meant them"): decider: the Medusa Sprite's touch (A 11530, D 11537, level 10) `Stone` → `Weak`: a level-10 touch petrifies
  10 % of hits (level × attack level), which ends a solo run; nothing in MM6–MM8 petrifies below level 27. Count and
  speed stay (X2 1.08, inside the gate). Only `monster_data.txt` rows 11530/11537 changed. The Gorgon Sprite (11534,
  level 16, Stone, D2) has the same problem: DECIDE 2.
- Check: the generator refusal; scenario `tests/scenarios/xeen/sprites_leave_loot.yml` (a Sprite Queen and a Medusa
  Sprite killed in X2 leave gold): fails on the old table (`f54_scenario_before.txt`, "the Sprite Queen left no gold"),
  passes now.

**F55, balance (XD-05 p2, p4; X1 p26; XD-04 p2, p4). Decider on `balance.py` numbers (`balance_before.md`).**
- XD-05 first room (nine orcs: three 2-3 spawn points on the entry fight): move `spawn:gate` to `room:palisade_yard`
  `at: [0, 3300]` (dungeon lane, REQUESTS); count and XP unchanged.
- XD-04 skulls (a 200–3,000 gold gem for a 40-gold scroll): one gem buys **three** scrolls of the skull's spell
  (wiring `evt:skull_1..3`, texts "three scrolls", playtest; dungeon lane, REQUESTS).
- Kept: pulling (the shared MM6–MM8 AI), X1's toad swamp (X1 176 of 175, ratio 1.09; four toad markers near the pin; if
  more reports come, drop marker 19 or 21), XD-04's witch XP (L×(L+10), Act I already at 1.15). (X1 p26 was not about
  the toads: the player meant the Phirna root exploit; fixed in "X1 p26 and X2 p8, as the player meant them".)

**F56, MAW: no boss in XD-21 (XD-21 p2). No change; decider (a).**
- MAW names bosses only on maps with more than 30 monsters (`ceil((n - 30) / 150)`, C-tier rows,
  `MawMonsterRules.cpp`, MAW's MMMerge rule); small MM6–MM8 dungeons get none either, and Xeen's authored boss rows (the
  Robber Boss) are families of their own (XEEN_SUPPORT §3) and never become MAW bosses. The Robber Boss is there (in
  the picture, at the table). Reply for the player: "MAW names bosses only on maps with more than 30 monsters; the
  Robbers' Den's boss is the Robber Boss." DECIDE 3 if more players ask (option b: Xeen's unscripted authored bosses
  become MAW bosses, MX lane only).

**F57, the Giant Toad looks strange (X1 p22). S; no rebuild started.**
- Captures: `output/xeen_fb/p3_engine/f57/sheet.jpg` (a friendly toad from five sides at the pin), `shots/`; the
  project's clay sheets `level_generation/creatures/xeen_toad_claude/review/clips_front.png`.
- What is wrong: (1) the player's picture is the Attack clip seen from the front at eye level: the lips part at the
  corners onto **black slits** (no mouth interior), and the reared head fills the view so the toad reads as a head
  floating over its feet; (2) in the clay sheets the Walking and Running hops fold the **thighs up above the back**
  (frames 4–6), and the Death/Dead pose shows a **peg sticking out of the belly** (the tongue root or a throat piece
  through the skin on its back). At rest from the side (`shots/03-side.png`) it reads well. A fix (a closed mouth
  cavity, the thighs' hop, the belly peg) is a model job for S: USER 1.

### F48–F51, F40/F45/F47 outdoors (agent `xeen-fb3-outdoor`, 2026-11-24 ~12:50–13:45; stopped at the token budget)

Captures: player pictures `output/xeen_fb/p3_outdoor/player/`; before (assets_dev after the classic-kit install)
`output/xeen_fb/p3_outdoor/before/<map>/` and `<map>_sheet.jpg`; after `after/xeen_x3/`, `after/xeen_x3_sheet.jpg`.
Scripts `output/xeen_fb/p3_outdoor/tools/` (`cycle.sh <key>`: regen, validate, build, checks; `install_check.sh <key>
<build>`: A5's baked install under the bake lock, then the checks; pass the playtests as absolute paths).

**New checks.** `tools/xeen/town_fit_check.py` (run by `towns.py --strict`) gains `bridges.step` (F48: a bridge's deck
ends more than 32 over or under what is beyond it, the end over water or `ends_in_air` skipped), `houses.jammed` (F49:
a house under 128 from another building, or 33–95 from a wall over its floor, or running into either; flush backing
within 32 allowed; pieces of a town-wall circuit and `hidden`/`staged` alternates skipped) and `props.in_wall` (F40:
a decoration's disc through a model's face). New `tools/xeen/check_reach.py` (F51): every chest, crate, well,
fountain, sketch item, clicked or container decoration must have walked-on land within 320, the land found as the
game walks it (the engine's four-corner steep-tile rule, water, decks of bridges/piers/platforms/stairs, and the
map's bounds ±23,143: Xeen has no `map_navigation` rows, so the default bounds hold the party in, and anything past
them is out of reach).

**F48 bridge ends.** Cause: a level bridge (`height`) is built at that height whatever the land at its ends; where the
deck ended between node lines or the land fell away to a water's edge the party met a 56–87 step (The Great Bridge,
the causeway, the piers), or the deck ran 102 into its bank (Medin's jetty, X2 p10). Fix at the source,
`level_generation/projects/xeen/common/wild.py` `bridge_ends()` (every outdoor generator runs it through
`WILD.apply`): an end with a step is carried on to the first dry node line (the studio levels land under water, so a
pad under the deck in the water stays low), a buried end is pulled back to where its bank meets the deck, and only
then, if a step remains, a `heights.terraces` pad at the deck less 8 runs back over two cells. X3's causeway now rests
on the land at both ends (no `height`: the shore is at 864 and the islet at 1,000) and ends on the islet's node line
67. Sites (9 ends): X3 causeway ×2 **fixed and installed**; X2 great_bridge ×2, nystor_pier, medin_jetty (p10),
island_jetty and D4 ferry_jetty, isle_jetty: **source fixed, maps not rebuilt** (dry run of `bridge_ends` lists them).
Left: D1 `jetty_pier` (ends in the air by design, D-5.3: give it `ends_in_air: true`), D2 `rope_walk_1`/`_3` (tree
walks: their platforms need a look), D4 `snow_bridge` (33/43 at its kerb side, humped deck).

**F49 jammed houses.** X1 Joe's shop stood against the warehouse's front and the culvert revetment (p21): `x1/town.py`
moves it to (58.5, 55.5), door north; **installed**. Left for the town generators (listed by `houses.jammed`): X1
terrace-backed shops (bank, core_houses#2 at 64 from terrace_wall_5, magic_shop 61, core_houses#3 100 from
wall_tower_1); X2 quay_houses#1, #3–#6 against the terrace walls (p2, p5; also F26's pending hollows of X2's
north/south walls); X5 Winterkill tavern/temple 80, houses #2/#3 104, #7/#8 72; D1 cv_weapons/cv_jail 88; D3
sc_guild_light/sc_houses#1 56; X4 asp_guild_body into the xd25 revetment (X4 is not rebuilt this run). X2 p6 (barrel
against stalls, the cut path strip) and X2's tavern patrons through its wall (`props.in_wall`) not done.

**F50.** Tomb of a Thousand Terrors (p8): a free-standing `cave_mouth` with the ground's own dirt as shell reads as a
plain brown wedge on flat land. `wild.free_mouths()`: a `free: true` mouth with a ground shell (or none) gets stone
(`cwb1`); X3's tomb takes the tower kit's dark blocks (`xvtwall`). **Installed** (after picture 08). The same rule
reaches X5's Troll Warren and X6's werewolf den at their next rebuild. Newcastle (p3): the rise's terrace runs a cell
further south beside the gate ramp; the mirror's foot is level but the pin's view (from the ramp below) looks much the
same: **partly done**, see NEXT. X2 p9 (thin strip and black slot in a ruin wall): not done.

**F51 unreachable things.** `check_reach.py` found 15 on 6 maps. X1: the west and north road orc camps (fire, barrel,
keg; p23's barrels) and the Shepherd's spring stood past the bounds — moved beside their roads inside them; Orothin's
two statue isles (Q-C20) were levelled into the delta pond by the studio (a `heights.points` inside a water body is
lost) — the pond now leaves a two-cell spit from the south shore to each isle. **Installed**, X1 0 errors. Left: X2
`island_chest`, D4 `skerry_strongbox` and `genie_lamp_skerry`, D6 `lamp_islet` (islands: Water Walk or Fly as the
intended means? DECIDE), X2 `river_boulder_3` (a text-only sign in the river), D2 `fairy_ring` (past the bounds).

**F40 / F47 / F45 on X3.** Ebenezer's rain barrels moved off the tent's wall (p2). `wild.house_tents()`: a tent that is a
house gets a closed front with a door (`xvdoor`), so its click is on the door only (p9); Ebenezer's Tent is the only
house tent on the 13 maps (the other clickable tents are camps burnt by a click on the whole tent). Both installed.
F45 p1: X3's `into` for XD-24 is now (0, 1600, 224) facing south (the dungeon agent's landing); the return point onto
X3 is written by XD-24's generator (`xd24/gen.py` `X3_ARRIVAL`, the dungeon agent's): proposed (17664, -5888, 992)
facing 1536, 0.75 cell south of the coffin's foot and its plinth. X1: the two orc markers nearest XD-02's exit
(44, 33) moved to (52, 20) and (34, 25) (3,500/4,500 → 6,500/7,800); installed.

**Installed with bakes:** X3 13:24 (town_fit 0, check_reach 0, door 0, D-85 0, stale_bakes 0, walk and hostility
pass after `x3/gen_walk.py` was taught the new XD-24 landing), X1 13:26 (check_reach 0, door 0, D-85 0, stale_bakes 0;
its playtests were rerun with absolute paths, see the agent's report). The classic-kit audit errors on X3
(`textures.feature_repeated` xvtwin on the Tower of High Magic) are c7's kit's, not this run's.

**Probably fixed by 3.2 (captures `before/`):** X1 p24, X2 p1, X3 p6 tents: no streaks; X3 p4/p5 ruin walls closed:
fixed. X3 p2's planks fixed; its barrel is F40 (done). X1 p20 (Vern's Dues) is not a picture question: not checked.

**The dungeon agent's requests to the builder (same agent, after F41–F57).**
- 1 done (studio, `openyamm-studio/core/IndoorLowering.cpp` `readDoorDrawing` and the single-leaf door node): a single
  hinged leaf whose back has no picture of its own, or a `back_surface` of the front's texture, shows its front
  mirrored (the row read from the other end, each picture mirrored; a hinged pair's back stays its front, its wings
  being mirror images). `build-xeen/oymap` rebuilt. Scratch builds: XD-24 5 → 0, DD-05 10 → 0, XD-14 9 → 0, DD-13 3 → 0
  `leaf.back_unmirrored` (`tools/xeen/check_door_leaves.py` on `output/xeen_fb/p3_engine/doors_root`). No studio audit
  rule added: the Python check stays the gate. Maps to rebuild: the 22 with findings (DD-02, DD-04, DD-05, DD-10A–C,
  DD-11B, DD-12, DD-13, DD-24, FD-02, FD-03, FD-04, XD-02, XD-03, XD-13, XD-14, XD-20, XD-22, XD-24, XD-26, XD-27).
- 3 done (studio, `IndoorBuild.cpp`): every sliding door or gate leaf of a studio map gets `mover: {bodies: reverse}`
  (closing onto the party or a monster it opens again; opening it holds), lifts and movers unchanged. XD-02 scratch:
  doors 2–16 now carry it (17–34, the lifts and movers, do not). Every studio BLV with sliding doors changes on its next
  rebuild; the gateway scenario is left for after XD-02's rebuild (NEXT). MM6–MM9 maps are not studio-built: no change.
- 2, 4, 5, 6, 7 not started (budget).

### F48–F51, F40 outdoors, second pass (agent `xeen-fb3-outdoor2`, 2026-11-24 ~13:30–14:40)

Scratch and tools `output/xeen_fb/p3_outdoor2/` (`tools/cycle.sh`, `tools/install_check.sh`: now picks A5's or A6's
install script by map and calls `check_faces.py`/`check_wild.py` with `--maps`). Before pictures are the first
pass's `output/xeen_fb/p3_outdoor/before/`; after pictures `after/xeen_x1/`, `after/xeen_x2/`, `after/sheet.jpg`.

**X1's walk (regression, fixed).** Joe's shop now stands on the culvert lane's old waypoint (59.3, 56.2):
`x1/gen_walk.py` goes up between the shop and the dec at (60.6, 57.15) by (60.25, 56.3). Walk 426/426 and hostility pass
on the installed X1.

**F48 bridge ends, made stable.** `common/wild.py bridge_ends()` read the installed map, so a pad left out once its land
had come up to the deck was gone again at the next build, and a buried end pulled back to the old deck's cut met a
bank 64 over it at the next build (Medin's jetty). Now: every land end gets its pad (deck less 8) unless the land is
already at the deck's own height (±4); a buried end keeps its end and its pad cuts the bank down (no pull-back); the
node-line search looks at every node across the deck's width (Island jetty's centre ran between a dry and a wet node
row: +36/+48), and the end goes 16 past the node line (the Great Bridge's end faces lay in the quay walls' faces);
a hull afloat (`piers: 0`: D4's ferry and skiff, D2's walks, D6's crust) is skipped (the ferry had been drawn up the
shore). X2: Great Bridge ×2, Nystor's pier, Medin's jetty (p10: the pointed deck now lies on its cut bank), Island
jetty **fixed and installed**; D4 ferry and isle jetties **fixed** (see the install line). Kept: D1 `jetty_pier`
(D-5.3, in the air on purpose) in the new `tools/xeen/town_fit_kept.yml` (the studio has no `ends_in_air` word).
Left: D4 `snow_bridge` +33/+43 (a humped `rise` bridge, no `height`: the rule does not reach it), D2's tree walks.

**F49 jammed houses.** The check (`houses.jammed`) was made truer: a house is a `building:` or a thing with `house:`
(gatehouses, towers and ghost gates with doors are not), a doorless building at most half a cell each way is a
fitting (D1's barred jail window), a wall face looking away from the house is not a slot (a terrace wall's end behind
a shop's corner: X1 weapon shop, armoury, tavern), a hull-only "runs into" along the house's own wall is flush
(X1 town hall: its tower in the steps' gap), and a work that is not a house counts as a wall (D1's gatehouse).
Fixes at the source: X1's terrace wall comes 48 forward to the shops' backs (`town.py RETAIN_FILL`: magic shop, bank,
core_houses#2), core_houses#3 half a cell off the west gate tower; X2's quay walls come 36 forward
(`x2/gen.py retaining(... toward=)`: quay_houses #1, #3–#6, pins p2, p5); D1's jail half a cell east of the smithy
(its window and POI with it; the two casks in the slot now stand in a lane). X1, X2 **installed**, D1 see below.
Left: X5 Winterkill (tavern/temple 80–102, houses #2/#3 104, #7/#8 72) and D3 (light guild / sc_houses#1 56): their
maps are not rebuilt this run (NEXT).

**F40 props.** X2's tavern patrons at 42.6 (they stood through its front at 42.45); X2 p6's cask pair off stall 5's
corner (67.7, 47.75); prop 3 off Nystor's pier's lengthened foot. D4's Blackfang beacons on the wall walk are kept
(`town_fit_kept.yml`, on purpose). Left: D1 `prop_4`-style sites elsewhere: D2's charred stumps by the palisades (8),
D3 barrel_1_pair, X5 outpost bones, X6 wagon barrels (X6 is c7's this run).

**F50 X2 p9.** `wild.ruin_windows()`: a ruin's walls carry no windows (the glazed window was a black slot in a broken
32-thick wall) and its trim is its wall's stone (the low broken course was a strip of the kit's timber trim2_32a).
Every ruin: X2 shore ruin installed; X1 ruined cottage and burned farm, X3 Newcastle, X6 caravanserai and D3 Vespar's
ruin take it at their next rebuild. The "cut path strip" of p6 was not traced (no road, ground area or deck there in
the sketch): NEXT.

**F51.** X2 `river_boulder_3`, out in mid-stream, is a plain boulder (its three neighbours keep the click). Open for the
user (unchanged): X2 `island_chest`, D4 `skerry_strongbox` and `genie_lamp_skerry`, D6 `lamp_islet`.

**F31 faces at the source.** The culvert's cap now reaches 4 into its end face's block, 2 under its top and 4 inside
its sides (`tools/xeen/kit_pieces.py SunkenEntrance.backing(sink=)`): X1's grate/cap pair is gone (and the build's two
cap/quay coplanar warnings with it); X4's `xd25_stair` cap is the same kit and follows at its next rebuild. Left for the
studio (REQUESTS): the culvert outfall's grating bars stand on the water's plane (`raiseCulvertGrating` starts the
uprights at `waterLevel`), and a doorway's hood is built back to back on its frame's front (X1 Witch Tower door).
Nystor's ship is MM7's model taken whole: kept with its reason in the new `tools/xeen/check_faces.yml` (format `kept:`).

### The dungeon agent's requests 2, 4, 5, 6, 7 and the runtime-test crash (agent `xeen-fb3-engine2`, 2026-11-24 ~14:30–16:30; for A1)

Scratch: `output/xeen_fb/p3_engine2/` (scratch builds under `scratch/`, captures `f44/`, repro scenarios `f42/`).
Binaries rebuilt: `build/game/openyamm`, its unit and runtime tests, `openyamm-studio/build-xeen/oymap` (with
`oymap_tests` 522 of 522). No map rebuilt or installed: every studio change below reaches a map on its next build.

**Request 2, hinged leaves not drawn from the far room (F44, XD-05 p3). Studio.** `IndoorLowering.cpp` (door
mechanisms): a hinged leaf that is not a trapdoor becomes a `kind: rotating` mechanism with `extra_rooms` = its
opening's `to` room, the compiler's existing form for MM9's converted doors (`IndoorSourceGeometryCompiler.cpp`): its
faces are listed in both rooms (room behind = the other room) and take facet type 0 (kind by normal, as MM9's rotating
faces). The renderer, collision and picking already take a face in either of its rooms; no engine change, MM6–MM9 maps
untouched. Scratch builds: `leaf.swing_room` XD-05 2 → 0, XD-02 5 → 0, DD-12 14 → 0; XD-05's audit identical to the
installed map's (reach 25 of 25 sectors, same findings). Test "a door slides sideways ..." (oymap_tests) now checks every
hinged leaf's faces in both rooms. **Maps that change on rebuild:** every studio BLV with hinged leaves (41: dd02 dd04
dd05 dd08 dd09 dd10a dd10b dd10c dd11b dd12 dd13 dd14 dd15 dd17 dd19 dd20 dd21 dd24 dd25 dd26 fd02 fd03 fd04 p1 xd01
xd02 xd03 xd05 xd07 xd09 xd12 xd13 xd14 xd15 xd18 xd19 xd20 xd22 xd24 xd26 xd27); the 74 leaves with a visible fault
are on dd02 dd05 dd10b dd10c dd12 dd24 fd03 fd04 p1 xd01 xd02 xd03 xd05 xd09 xd20 xd27.

**Request 4, one click for the parts of one object (F47, XD-02's winch). Studio vocabulary.** rooms.yml
`part_of: <platform id>` on a platform without an `id`, or on a beam: the part runs the platform's click (every face) and
changes with it (`hide`, `show`, `texture`: the same face number). Refused on a pillar or a platform with its own `id`;
an unknown platform is a reference issue. Schema `rooms.schema.json` (platforms and beams), README ("Parts of a clicked
platform"), test "the parts of a clicked platform (part_of) run its click and change with it". XD-02 scratch with
`part_of: platform:winch` on the iron head and both capstan bars: the winch event's faces 9 → 31. `check_wiring_rules.py`
`click.covered` skips a part with `part_of`. **For the dungeon rebuild:** XD-02 rooms.yml lines 390 (iron head) and the
two "Capstan bar" beams get `part_of: platform:winch` (then drop `('xd02', 'click.covered')` from OPEN); XD-01's five
tanks likewise (warnings).

**Request 5, the prop overlap audit (F40). Studio audit.** `core/Audit.cpp` `auditPropOverlap` (+ `readPropModelShape`,
`PropOverlapData` in `Audit.h`), run by `oymap audit` on every Xeen indoor map (others with `--dressing`): the four rules
of `tools/xeen/check_prop_overlap.py` with its numbers and classes (`prop.overlap`, `prop.wall`, `item.hidden`,
`prop.squeeze`; prop/wall slots, the script's optional `--wall-squeeze`, are left out). Footprints are each bound
model's plan hull per height band (read from the GLB with cgltf, scaled, jittered and turned as
`DecorationModelSet::placementFor`), else the collision circle; chests their faces' box. On the installed XD-02, XD-03 and
XD-27 it gives exactly the script's findings (same rules, severities and counts: 4, 4 and 6 errors). Test "F40 prop
overlap: ..." (`openyamm-studio/tests/OutdoorTests.cpp`). **Consequence:** the audit now has these errors on the 38 maps
of `f40/all.txt` (65 errors) until their props move: "audit 0 errors" gates of indoor rebuilds fail on them (DECIDE 1).

**Request 6, purple specks behind XD-08 door 8's portcullis (F44). Renderer, shared.** Cause: the indoor face shader
discarded only texels of alpha ≤ 0.001 (`fs_indoor_textured_lit.sc`); BC7 stores the hole texels beside the bars with
alpha a few steps over 0 and arbitrary colour, so they were drawn opaque as specks (not the mips' box filter alone,
not depth order or coplanar leaves: the two leaf faces are 16 apart, the specks lie on the back face). Fix: the cut at
0.1, the outdoor BModels' (`outdoor_bmodel_lightmap.sh`). Pin pose before/after: `f44/before.png`, `f44/after_cut01.png`,
sheet `f44/xd08_portcullis_before_after.jpg` (purple pixels 5,826 → 1,097: a one-pixel rim left on the holes' edges,
which is the textures' dark-purple colour under the holes mixed in by bilinear filtering: `tools/xeen/
texture_alpha_bleed.py --write` removes it, with the next bakes of those textures' maps). MM6–MM8: none of their indoor
face textures has a cut-out (x4 masters scanned: no alpha holes, no magenta key; MM6's `trekscon` alpha 234–250), so no
change. MM9: Beethoven's grill and web before/after (`f44/cmp_*.jpg`): 69 of 1.44 M pixels differ on the grill's edges,
the web (translucent) none.

**Request 7, F42 repro (headless; `f42/*.yml`, logs beside them).**
- XD-04 p3: with the mistress's doors 11/12 open (they slide and fold in the built map), a missile from the
  Schoolmistress's place (a Wicked Witch's Mind missile, an Orc Archer's arrow) flies to the party and ends at it
  (sampled every 0.01 s: last 65 from the party's middle), and the party's Fire Bolt hits the actor. With the doors shut
  the AI does not shoot. Not reproduced: no invisible face.
- XD-05 p5: the party at the pin stands 140 back from the lip of its 576-high ledge (z 192, the lip at y 7872); the line
  from the drum hall's archer to the party's eye crosses that lip at z 192.4, so the arrow (radius 16) strikes the lip,
  and the party's Fire Bolt aimed at the archer strikes the ledge floor 15 from the lip. Both ways the shot dies at the
  lip, an "invisible wall" to the player (an arrow leaves no mark). The monster's line of sight is a thin ray that clears
  the lip; its shot is not. Real, but shared AI (MM6–MM9 monsters on ledges): DECIDE 2. No change.

**The runtime-test crash.** Not order-dependent: "quick cast attacks instead when the quick spell lacks mana or a target"
(the case after "quick Heal ...", which doctest named) crashed alone too, as did "a quick Lifedrain ...":
`GameplayScreenRuntime::soloHud()` read the settings through a null pointer in a session without settings (the spell
service tests make one). Fix: `soloHud()` takes no preview without settings (`m_pSettings` checked, as the runtime's
other settings readers do). `GameplaySpellServiceTests.cpp` 13 of 13 pass.

*Runs (16:30):* unit tests 3,188 of 3,188; the 16 release scenarios pass; `oymap_tests` 522 of 522. The full
`openyamm_runtime_tests` now runs to the end: 116 of 120. The four failures were hidden behind the crash and are not
this run's: "HUD text colour codes take no room ..." (`GameplayUiRuntimeTests.cpp:371`, 3 quads for 2), "New Sorpigal
temple braziers toggle ..." (`IndoorDecorationInteractionTests.cpp:44`, a frame's texture and palette not among the
billboards'), "party creation offers all starting characters with continent-specific caster classes"
(`NewGameScreenTests.cpp:45/63`, Chedian's classes) fail alone too; "party creation race card groups alike attributes
and skill rules" fails only in the full run (order-dependent). For A1 (NEXT).

**REQUESTS (dungeon rebuild round).** Rebuild with this oymap: (1) the 41 maps with hinged leaves (request 2, listed
above; 16 with visible faults) — `check_door_leaves.py` `leaf.swing_room` 0 after; (2) XD-02 with `part_of:
platform:winch` on the iron head and the two capstan bars, XD-01's tanks' parts likewise (`click.covered` 0); (3) the 38
maps of `f40/all.txt`: move the props until `oymap audit` has no `prop.*`/`item.hidden` error; (4) with the next bakes of
the six Xeen cut-out textures' maps, `texture_alpha_bleed.py --write` (the purple rim on XD-08's portcullis holes).

**DECIDE.** (1) The prop overlap audit's errors: keep them errors (the 38 maps' audits fail until their props move, as
the user's rule wants a check that keeps it fixed), or warnings until the dungeon round has moved them (cheaper to
reverse: a one-word change in `auditPropOverlap`). Kept as errors. (2) F42 XD-05: a monster shoots when its thin line
of sight clears a lip its arrow (radius 16) does not. Options: (a) nothing (a player stepping to the lip shoots
freely); (b) the map: a parapet or lower lip at XD-05's ledge (dungeon lane); (c) shared AI: a ranged monster tests its
shot with the projectile's radius before shooting (all worlds; needs an MM6–MM8 check). Took (a) meanwhile.

**Installed with bakes (all four: town_fit 0 apart from kept and the open items, door 0, walk and hostility pass;
no stale bake of these maps).** X1 13:46 (walk 426, hostility 64); X2 14:09 (walk 449, hostility 45; check_reach 1:
`island_chest`, open); D4 14:13 (walk 426, hostility 87; left `snow_bridge` ×2, the two skerry pick-ups, open;
check_faces: the isle tower crown's open edge, old); D1 14:16 (walk 908, hostility 50; check_faces 28, the F31 lane
list: gatehouse, Kalindra's ghost houses, wall NE). D-85: X2 (entrance:xd06_yak, two Killer Sprites at 873/1,273)
and D1 (NPCs 4951, 4953, 4956 at 5,527–5,803) fail exactly as in HEAD's scenes: not from this run. Stale bakes: 24
indoor maps after another session's `textures_x4` changes, none of these. Story: 01–19 pass on `build/game/openyamm`
(13 and 15 after their stables poses moved to the classic kit's office doors: X1 (368, 9212), X4 (772, 4386));
D1's and D4's segments (39–73) not run: NEXT.

**Requests (studio, for the builder).** (1) `OutdoorThings.cpp raiseCulvertGrating`: start the upright bars 2 under
the water (`foot = waterLevel - 2`, the bar's foot hidden in the tunnel's floor when the water is 0) so their feet do
not lie on the water's plane (X1 outfall, 3 pairs). (2) The doorway's `hood` (`OutdoorThings.cpp` ~4325): build the
hood's roof and cheeks without their back faces, which lie on the frame's front face (X1 Witch Tower door; every hooded
doorway). (3) `kind: model`: a word to drop a taken model's overlapping faces (Nystor's ship, kept until then).
(4) A rise (humped) bridge's ends: meet the land within 32 (D4 snow bridge).

### Dungeon rebuild round, Cloudside (agent `xeen-fb3-rebuild-cloud`, 2026-11-24 ~14:10–15:00; for A7, A8, A3)

Scratch, logs and the two drivers: `output/xeen_fb/p3_rebuild_cloud/` (`sb.sh <key>`: regen, fmt, build into
`output/studio_cal/<key>/b_<time>`, `oymap audit --mount` of the stage; `iq.sh <key>`: install that stage, bake under
`bake.lock`, audit, `check_exits/drops/open_sky/identity/door_leaves/arrivals`, `xeen_pack_reserve`, every playtest;
`iq2.sh` skips the bake of the unbaked open-air maps; per-map results `q/<key>.iq.log`). Every map under its lock, built
once with the current oymap (mirrored door backs, leaves in both rooms, sliding doors that stop for bodies, `part_of`,
the prop overlap audit), installed and baked straight after.

**Rebuilt, installed and baked (24):** XD-01 to XD-10, XD-12 to XD-16, XD-18, XD-19, XD-20, XD-22 to XD-27; X8 and P1
rebuilt and installed (open-air, no bake profile). **Baked only:** XD-11 (the cut-out textures). Every one: `oymap
audit` 0 errors (the F40 prop rules included), `check_exits` 0, `check_open_sky` 0, `check_identity` 0,
`check_door_leaves` 0 (whole world: clean, 69 maps), `xeen_pack_reserve` clean, `xeen_balance.py --check` clean,
playtests all pass (X8's and XD-26's: see below). `check_immobile.py` exit 0; `check_wiring_rules.py` 0 errors, OPEN
emptied (the 10 `decide` sites wait for the ruling); `stale_bakes.py --check` 0 at the end.

- **F44/F43 doors (every hinged-leaf map of the share):** XD-01 02 03 05 07 09 12 13 14 15 18 19 20 22 24 26 27, P1
  rebuilt: `leaf.back_unmirrored` and `leaf.swing_room` 0; sliding leaves carry `bodies: reverse`.
- **F40 props (L4 or generator):** XD-01 `hall_sacks_4`, `pen_3_bowl` moved, `shaft_nest` and `outfall_junk` (heaps of
  radius 115–147 in a 1-cell shaft and on the outfall's walking line) dropped. XD-02 `spawn:ore_heap_item` (item.hidden)
  to (12830, 6800), `spider_galleries_102` off the chest, `west_line_76` off the wall, `west_line_upper_78` dropped (a
  234-wide heap in a 320-wide incline). XD-03 `spawn:item_spoil` (item.hidden) to (4640, 1640), `prospector`,
  `geode_cluster_2`, `warren_rock_2` moved. XD-05 `cache_cask`/`cache_barrel`, `hall_skulls_w`, `mouth_skulls_e/w`
  (clear of the skull-torch poles) moved; the pinned trash heap `chimney_guano` to the bat chimney's south-east corner
  (3040, 7710), clear of the spawn and the bones. **Model fault (S):** `mm6_deco_trasheap.glb` carries a crate and a
  barrel inside its heap (`level_generation/decorations/mm6_dungeons_3d/containers/`): wherever it stands it shows
  three things inside one another; the model wants the crate and barrel taken out or set on the heap. XD-06 chapel
  statues, XD-08 stocks skeletons (now at the foot of each pair: in the board they went through the timber), XD-10
  `guard_post` stalagmite, XD-12 `scrap_2`, XD-14 `study_fire`, XD-16 `rubble_03/04`, XD-23 `guard_skulls`, XD-25
  `basin_trash`, XD-26 `roost_skulls`, `low_nests_skulls`, `mouth_rock`, XD-27 `mouth_skulls_w`, `chief_skulls_1`
  (to the den's south wall), `den_bones_3`, `feast_cask`, `kennel_bowl`, `kennel_bucket`: moved in their generators.
- **F41:** `immobile: true` → `leash: 600` on XD-05 `guard_e`, `guard_w`, `drum_master`, XD-04 `warden`, XD-03
  `gate_guard_1/2`. XD-03 p2: `stalagmite_3` to (1190, 1760) (its gap to `geode_glow_2` 45 → 116; no squeeze left
  there), `geode_cluster_2` off the wall.
- **F55:** XD-05 `spawn:gate` → `room:palisade_yard` (0, 3300). XD-04 skulls: one gem buys three scrolls (wiring
  `evt:skull_1..3`, three `GiveItem`, the texts "Three scrolls of ..."; playtest checks +3 scrolls of Heal).
- **F47:** XD-02 `part_of: platform:winch` (iron head, both capstan bars); XD-01 tanks 1, 2, 3, 5, 6: their four
  posts and lid frame `part_of` the tank (25 parts; `click.covered` 0). Destroy questions removed: X8's three nests
  (`gen_objects.py`), XD-19's four generators and two guard machines (`gen.py`), XD-25's transformer (`gen.py`); tests
  updated: X8 `gen_playtests.py`, XD-19 `gen_tests.py`, XD-25 playtest, story `83_castle_xeen`, side quests
  `x8-sky_cloudreach`, `q-c5_q-c11_asp_and_crystals`. The 10 `decide` sites (DD-13, XD-23, XD-16, FD-04) untouched.
- **F45:** XD-24 start → (0, 1600) on the coffin stair facing south (`xd24/gen.py`; no monster sees it, the exit 380
  away), `X3_ARRIVAL` → (17664, -5888, 992) facing 1536; XD-24's playtests follow. `check_arrivals` on the share: XD-24
  clean; **left** (hot, need a per-map design move of the entry guards or a bend, not done this round): XD-05 X7 gate
  (the two gate guards 274 away, now leashed: DECIDE), XD-10 ×2 (Flying Feet in the entry halls), XD-13 (Wood Golems
  1,336+), XD-15 (Sand Golems 1,211+; and the drop cell, a fight on purpose), XD-16 (Demons 1,414+), XD-19 (Devils
  1,824+), XD-22 (Ninjas 563, in the porch), XD-23 (Trolls 416, in the mouth). Open-air, for the ruling: X8 ×2
  (landing, High Magic arrival), P1–P4 starts.
- **Textures (F44 rim):** `texture_alpha_bleed.py --write` on the six cut-out textures at 14:15 (repeated until
  `--check` is clean: xopoles and xwward needed five passes, the halo cleared one ring at a time), recooked
  (`cook_surface_textures.py --world xeen --only xeen/<stem>`). Their Cloudside bakes are all redone (XD-02 04 05 07 08
  11 13 14 18 25); Darkside's are the sibling's. No outdoor bake was stale.
- **Also:** `xd15/gen.py` chest:vault takes the committed L4's (384, 6104) (a hand edit that regen would have lost).
  `check_drops` pockets left as they were in HEAD (same check on the committed maps): XD-05 prisoner pit (kept, ladder),
  XD-10 the pool at (2048, 2944) (a 64 step), XD-12 the outer ground at the four edge exits, XD-15 the drop cell
  (D-39 Q5), X8 (open air).
- **Playtests:** X8 `playtest` failed at the explorer statue: it expected a window, but since F13 the statue answers
  on the status line (old fault): `x8/gen_playtests.py` `click_status`, regenerated (`regen.py --build x8`): passes.
  **XD-26 `playtest` fails (twice, reproducible) at step 62**: back out of the fence's cache towards the hoist the
  walker sticks at (3237, 1619, 1024) and times out; the same playtest **passes on HEAD's XD-26** (map, scene, Lua and
  bake from git in `output/xeen_fb/p3_rebuild_cloud/headmount/`, run with `--extra-mount`). The only change on that
  path is the studio's: `door:fence` (hinged, `open_away`, pivot (3136, 1440)) is now listed in sectors [4, 1]
  (request 2) where HEAD had [4]; the F40 moves on XD-26 are far from it. REQUEST to A1 below; XD-26 stays installed
  (every check clean) unless the orchestrator restores HEAD's six files from that folder.
- **Story and side runs (`build/game/openyamm`):** story 03 05 07 09 11 13 15 21 23 25 27 29 31 33 35 37 79 81 83 87
  96 pass (83 with the generators answered by a click); STALE (checkpoints older than rebuilt maps, the game reset
  them): 21, 79, 81, 87, 96. Side quests q-c10, q-c12, q-c15, q-c23, q-c25, q-c26, q-c3, q-c4, q-c5/q-c11, q-c7,
  q-c8/q-c9, x1-tam_oslos_son, x8-sky pass (q-c7 after its XD-24 arrival assert moved to (0, 1600)). Promotions 05 11
  21 25 27 61 67 68 pass (61 likewise updated; STALE 05, 11, 21, 61). `balance.py`: every act within 15 %.

**REQUEST (A1, studio).** XD-26's fence door: with the hinged leaf as a `kind: rotating` mechanism listed in both
rooms, the party (the scenario walker) cannot walk from the fence's cache (sector 4) back to the east ledge after the
door was opened from the ledge; HEAD's build (the leaf in sector 4 only) passes. Repro: `build/game/openyamm
--asset-root assets_dev --world xeen --headless-run-scenario devdocs/xeen/briefs/xd26/L4/playtest.yml` (step 62);
the same with `--extra-mount output/xeen_fb/p3_rebuild_cloud/headmount` and that folder's `playtest.yml` passes.
Check whether an open rotating leaf's faces collide at their closed place in the extra room, and whether other
41 maps' hinged doors walked back through after opening behave (no other playtest of the 26 maps failed).

### Dungeon rebuild round, Darkside (agent `xeen-fb3-rebuild-dark`, 2026-11-24 ~14:10–15:20; for A7, A8, A3)

Scratch `output/xeen_fb/p3_rebuild_dark/` (`dark.sh <key>`: regen, build, stage into a private root, audit, door,
arrival, drop and exit checks; `MODE=full`: install, bake under `bake.lock`, open-sky, identity, pack reserve, MAW
balance, every playtest; `hide.py <stem>`: for each hot arrival, the nearest same-room spot out of each monster's sight
and the nearest arrival spot no monster sees, on the arrivals check's own geometry). Every generator reproduced its L4
first (`regen.py --check`; DD-12's two hand-moved chests carried into `dd12/gen.py`, so DD-12 now reproduces).

**Rebuilt with the current oymap, installed, baked (30 maps):** DD-01, 02, 04–10C, 11A–C, 12, 13, 14, 15, 17, 19, 20,
21, 23, 24, 25, 26, FD-02, 03, 04, plus a bake of DD-03 (only stale from the six textures' `texture_alpha_bleed.py
--write`, done by the Cloudside agent). `stale_bakes.py --check` 0. Every rebuilt map: audit 0 errors, every playtest
passes, `check_door_leaves.py` clean on all 34 Darkside dungeons, `check_exits` 0, `check_open_sky` 0,
`check_identity` passes, pack reserve and `xeen_balance.py --check` clean, `check_wiring_rules.py` 0 errors.
`check_drops`: 0 pockets everywhere but DD-21's lower sewer (the known pocket in its NOTES, unchanged).

- **Hinged leaves (F44):** the 23 Darkside maps with hinged leaves picked up the mirrored backs and both-room leaves.
  FD-03 still failed `leaf.back_unmirrored` (doors 5/6, 9/10): its pairs used `crsmdr1` unmirrored on both wings.
  `fd03/gen.py` `WING_R` is now the left wing mirrored (as DD-24's `PAIR`).
- **F40 props (27 errors on 14 maps, all fixed at the source):** DD-01 rubble; DD-04 cellar casks, sappers' tunnel
  dirt (a boulder now: no 117-wide heap fits the 320 tunnel beside its walking line); DD-06 counting and mess casks,
  bunks' heap; DD-07, DD-08 cask pairs; DD-10A skeleton, cobweb skull; DD-10B the God's two crystals; DD-10C miner
  off the chest, collapse rocks, nest ash; DD-11A midden skulls; DD-11B skeleton 3; DD-11C gate skulls; DD-12 store
  barrels, two maze rubble heaps (dead-end offsets); DD-13 four barrel/cask pairs; DD-23 roost skulls. Warnings left
  as they were.
- **F47:** DD-23's ten roost rocks and feet no longer ask "Destroy (Yes/No)?". A click calls `q-d15.roost`. The
  playtest, side quest `q-d15_calebs_glass` (passes) and `check_wiring_rules.py` OPEN (`dd23` dropped) follow. DD-13's
  fort pits and FD-04's shrines are kept as questions (the decider's).
- **F45 arrivals:** every Darkside dungeon arrival is out of sight now except the three below. The monsters moved to
  the nearest spot in their own room that does not see the landing (they still guard it, around the corner): DD-05,
  the front door's Heretic Lord and three golems now behind the mirror hall's door; DD-06, two Rogues, the Thief and
  the Sabertooth; DD-07, an Adept; DD-09, a Shaman; DD-15, the atrium's three; DD-17, a Gamma Gazer (from D7's
  landing); DD-20, two Witches and four Stalkers (start and D4's shaft landing); DD-21, two Greater Liches; DD-23,
  three Gargoyles and the Sentinel. DD-11A/B's tunnel trolls have no hiding place in their tunnel, so the starts moved
  176/182 into the pit's corner ((80, -208), (144, -208)). Their playtests follow (the hostility test walks back to the
  old spot for its sight check). **D2's troll-hole landings still write (96, -32)** until D2 is rebuilt (REQUESTS).
  `arrival.hot_within` warnings stay on DD-15 and DD-17 (teleports inside the map). D7 (open-air) is unchanged and
  waits for the ruling: hot at its start (from D1), the P1, P2 and P4 returns.
- **DD-12's exit test and story 57, side quest Q-D25:** D4's isle landing is now at z 1185 / 1149 a step on (the
  outdoor pass's D4 jetty pads), under the tests' `z_min: 1200`. The window is now 1100 (tests only, no map change).

**Runs (15:20).** Side quests crossing these maps: 29 of 30 pass. `q-d11_forts_graalgs_ogres` fails at step 10, the
press on Kramer's bounty at D1 (3844, 5376) (D1's jail moved in the outdoor pass; not these maps). Story: 41–69 pass
(STALE notes for D1/D2 checkpoints); 77, 97, 98 pass. **73 (step 36) and 85 (step 78) fail at DD-15's lift top**:
stuck at (241, -3316, 2304) at `door:lift_gate` (slide_up, opened by the lift's climb), which now carries the studio's
new `mover: {bodies: reverse}`. Likely the same door-change regression family as XD-26's (relayed to the builder). The
map is kept installed, since every other check passes and its own playtests (lift ridden down only) pass. Promotions:
35, 37, 55, 57, 63–66, 69, 81, 83, 85, 89, 95 pass. 47 fails at the same D1 Kramer press as Q-D11.
`balance.py`: DD-10/DD-11 row 0.75 "off" (no monster count changed this round: earlier state).

### Predetermined loot, a player's report 2026-11-24 (agent `xeen-fb3-random`, 2026-11-24 ~14:50–16:00; for A1, A3)

Report: "No matter which fire, the order is fixed. And so is everything, where you can loot something, even the ore
trader." With X1 p25 (F52: Norman's paid New stock "always the same").

**Causes.** (1) *Event rolls* (`evt.RandomJump`/`PickRandomOption`, `RandomBetween`, a random `evt.GiveItem` such as
the campfire ring, MM6–MM8 trash heaps and the MMerge ore smiths' Make Weapon/Armor/Item, `SummonRandomItem`): one LCG
per map visit (`EventRuntime.cpp` `nextEventRandom`), seeded on the first roll from that event's id and the hour, the
same in every game, and its low bits alternate (`% 2` strictly took turns). Measured: a new game on X1 rolling
`RandomBetween(1, 6)` 16 times gave `1,2,1,2,1,4,1,2,1,6,3,4,5,2,5,4` in two games with the old binary; now
`1,5,4,1,6,5,…` and `1,6,2,3,2,3,…` (`output/xeen_fb/p3_random/scn/`). (2) *Decoration contents*: cauldrons, large bags,
buckets and MMerge's contest pedestals took their first state from their position (`InteractiveDecorationRules.cpp`),
the same spot holding the same thing in every game; barrels already rolled. (3) *Paid New stock*: keyed by the
playthrough's seed and the stocking's number, so a reload before it rerolled the same shelf (F52's note).
Not causes: chests, loot containers, searchable props (heaps), MM9 barrels and treasure roll from the map's
`sessionChestSeed` (`random_device` and the clock on a map's first visit, then saved), corpse loot from `random_device`,
Lua's `math.random` (the fire's food) is seeded from the clock by Lua 5.4.

**Fix (A1, every world).** Event rolls: a SplitMix64 stream seeded from `std::random_device` on the first roll of a map
visit, never saved (`EventRuntimeState::eventRandomState`, now 64-bit; a test sets it nonzero for a fixed sequence).
Decorations: the cauldron/bag/bucket/pedestal states come from the map's fresh roll as barrels'. Shops: a paid New stock
mixes a fresh `random_device` value into its stock seed; the timed restock stays keyed by the playthrough's seed. Stored
results do not change: a chest, a shelf or a decoration once rolled is saved as before. `devdocs/maw/RANDOMS.md` 7.1
notes both.

**Tests.** Unit: "lua random jump advances between repeated event activations" (rewritten: a fixed seed repeats, every
target comes, a two-way jump does not take turns, two unseeded runs differ), "fresh map cauldron, bag and bucket contents
follow the map's roll, not their spot" (new); full unit suite 3189/3189. Runtime: "MAW's paid new stock gives a weapon
shop new shelves" extended with a reload (the saved shop state restored before the same paid stocking gives a different
shelf). Scenarios with `build/` (logs `output/xeen_fb/p3_random/logs_*`): release list 16/16; npcs, Xeen and Xeen side
quests 110/120; MM6–MM8, worlds, journal, top-level and the loot/shop ruleset ones 99/114. None of the failures is from
this change: Q-D2 (Castleview Jail), Q-D11 (both, Kramer's press), `maw_seers_and_bounties` (Town Hall), `maw_density`,
`x2_fall_damage`, the MM6 probes and `goblins_mixed_close_in` fail the same with the 23 November binary
(`build-xeen`); the `.arena.yml` files and `mm6/main_story_draft` are not plain scenarios. Q-C4 (stuck in XD-22 at
(304, -1320)) and Q-C8 (XD-14, (-1381, -6)) pass with `build-xeen` and fail with `build/` every time, but neither dungeon
rolls anything (no random event, no rolled decoration): the indoor movement/door changes since (the door-change family
above), not this one.

**Behaviour change, every world.** Trash heaps, campfires, ore smiths, random `GiveItem` rewards and every scripted
`RandomJump` or `RandomBetween` now differ between games and reloads, as in the
original games (their `rand()` is seeded at start). A scenario or playthrough that needs one outcome must not rely on a
roll; none found that did.

### Door regressions after the rebuild round: XD-26's fence door, DD-15's lift gate, Q-C4, Q-C8 (agent `xeen-fb3-doorfix`, 2026-11-24 ~14:50–16:00; for A1, A3, A7)

Scratch: `output/xeen_fb/p3_doorfix/` (repro scenarios `sc/`, playtest logs `maps/`, scenario logs `scen/`).
No map rebuilt or installed, no engine or studio change: the fix is in the scenario walker.

- **XD-26 `playtest` step 62: the walker, not the door.** With `door:fence` listed in rooms [4, 1] (request 2) its open
  leaf, swung into the fence's cache (along y 1440 from x 3136 to 3328), now blocks in the cache as a leaf must; in
  HEAD's build it was listed in the near room only and the party walked through its half in the cache. Collision is
  right (scratch `sc/xd26_fence_diag*.yml`: the doorway south of the open leaf passes, the closed pose blocks nothing,
  walking south at the leaf stops at its face), and the planner's route rounds the leaf's free end at x 3365 (its
  waypoints dumped). The scenario walker steered at a point up to 96 ahead on the route and so aimed past the corner:
  it slid along the leaf into the cache's north-west corner and stuck. MM9's two-room doors are the same form; nothing
  in the game changes. **Fix** (`game/scenario/ScenarioRuntimeDriver.cpp`, walk_to): on a planned indoor route the
  walker looks past a waypoint only at one the path map says it can walk to straight (`canReachDirectly`, the party's
  body; a waypoint within 24 is passed regardless); stuck, it aims further as before. Helpers
  `scenarioPartyPathObject` and `scenarioIndoorPathMap` (shared with `planWalkRoute`). Test
  `tests/scenarios/xeen/xd26_open_leaf_far_room.yml` (the open leaf stops a walk into it in the cache; a planned walk
  from the corner rounds it; fails with the old walker).
- **Exposure:** every map whose scene has `open_away` leaves (41: the request-2 list). All their L4 playtests with the
  fixed binary: **167 of 167 pass** (dd02 dd04 dd05 dd08 dd09 dd10a–c dd11b dd12–dd15 dd17 dd19–dd21 dd24–dd26
  fd02–fd04 p1 xd01–xd03 xd05 xd07 xd09 xd12–xd15 xd18–xd20 xd22 xd24 xd26 xd27; `maps/summary.txt`). A first version
  that also limited the stuck lookahead failed P1 `playtest` step 19 (a body the path map does not hold); the stuck
  lookahead is now as before.
- **DD-15, story 73 step 36 and 85 step 78: stale checkpoints, not the gate.** `door:lift_gate` is `open` at the top
  (logged every 0.5 s); six hostiles stand in the antechamber because the checkpoints (71 of 2026-11-23, 83 holding
  DD-15 from 73) predate DD-15's rebuild, so the game reset the map and its monsters live again (the logs' "changed
  since the save"); the step at the foot clears 3000 only. With hostiles cleared at the top the walk passes.
  `bodies: reverse` holds an opening door only for a face moving into a body; a rising gate moves away. Chain rerun
  with `build/game/openyamm`: **69, 71, 73, 75, 77, 79, 81, 83, 85 pass** (checkpoints refreshed; STALE left: 79 x1 x2
  xd12, 81 x3 x4 xd07, 85 x5, from segments before 69).
- **Q-C4 (XD-22, (304, -1320)): a Ninja, not a door.** The doors there (2, 3, 6, 9, 11, 12, sliding) are open; actor 27,
  a Ninja from the lower floor (dishonoured, hostile), stands in the walk's way and the step had no `clear_hostiles`.
  `q-c4_ninja_pagoda.yml` line 138 gets `clear_hostiles: 480` (as the next step): passes.
- **Q-C8 (XD-14, (-1381, -6)): not a door; left open (A3, A7).** The walk from the east foot (2368, 0) to the great
  hall (1200, 0) has no way but the kennels' door (door 10, event 20), which the scenario never opens; a shut leaf
  blocks alike in both builds. The planner then returns a node-limited partial route round the keep, different from
  run to run (old binary: 23 s of 30 with a jump at (-1381, -6); now it ends on the keep's upper floor above the
  target). Opening door 10 does not help yet: walking through it, and in at the west arch, the party stops at
  x ±1381 inside the hall with no face, decoration or actor there and passes only by jumping; the planner found no route into
  the hall from either side. For A7: what stops a body at x ±1381, y 0 / 832 in XD-14's great hall; for
  A3: open door 10 on the way back (the scenario is unchanged).
- Other checks with the fixed binary: unit tests 3189 of 3189; 80 scenarios (`scen_list.txt`: every
  `tests/scenarios/xeen/*.yml`, A1's regression set, the release scenarios, MM6–MM9 scenarios with walks) 77 pass;
  `maw_density`, `maw_seers_and_bounties`, `x2_fall_damage` fail the same on the 23 November binary (no walks).
  MM9 side quests (`tests/scenarios/mm9/side_quests/run.py`, MM9's walks through its converted two-room doors): 16 of
  16 pass.

### X1 p26 and X2 p8, as the player meant them (agent `xeen-fb3-p8p26`, 2026-11-24 evening; for A2, A3)

The player explained both pins on Discord (2026-11-24). The earlier rulings on them (F55 "no change" for p26; F54's
Weak touch as the answer to p8) answered other complaints; the touch change stays.

**X1 p26, the Phirna root: "you can only have one root, but if you throw it on the floor, you can have as many as you
want. I got 60 potions with that."**
- Cause: Q-C21's `phirna_plant` hook (four Phirna plants in Toad Meadow, X1 events 255-258) gave a root whenever the
  party carried none (`requires: {not: {item: phirna_root}}`, the original's rule); thrown away, the root came again,
  and Myra paid five Cure Poison potions for each. No other Xeen find is limited by the packs: every other item- or
  gold-giving map event and hook is `once` (a qbit), a numbered map variable (the campfires, beds, bones, veins) or a
  per-member bit (scanned: 117 map events, every quest and NPC file's hooks).
- MM6–MM8's rule: a reagent find is a map variable (MM6's `znwc` "You found something!" counts MapVar 3 to 16, MM8's
  palm trees a qbit), and a map's refill clears its map variables (`GameApplication`: a timed respawn starts the map's
  event state fresh). A plant gives what it gives, then regrows with the map.
- Fix (common Lua and the quest generator; no map rebuild):
  - `engine/scripts/common/event_support.lua`: `CurrentEventId()`, the map or global event that is running (set where
    each registered event begins). No other world calls it; MM6/MM7/MM8 map lifecycles and the save round trips pass.
  - `worlds/xeen/events/common/xeen_common.lua` `XeenQuests.hook`: a hook with `harvest = n` runs n times at each
    calling event (a named map variable `xeen.harvest.<hook>.<event>`), then shows its else line until the map refills.
  - `tools/xeen/gen_quests.py`: `harvest: <n>` emitted and listed in `quest_hooks.yml`; **refusals**: a hook that
    `gives:` items with neither `once` nor `harvest`, and a `requires` that asks the party to lack an item the hook
    gives. `QUESTS_FORMAT.md` §7 "A find is once or a harvest".
  - `source/quests/q-c21.yml`: `harvest: 1`, the carry rule gone; the refusal line became the else line "This Phirna
    plant has been dug up already. It will grow back in time." (same text id 43555). Four roots per X1 refill (672
    days), 20 potions. Generated: `xeen_quests.lua` (the hook), `npc_topic_text.txt` (43555), `quest_hooks.yml`.
  - The guide site (`tools/xeen_site/story/side_cloudside.yml`) and the A3 stub run (`quest_stub.py` learnt
    `event: <id>`; `act1.yml` digs at two plants and finds the first dug) follow.
- Sites: 1 found (Q-C21's four plants), 1 fixed; 0 left.
- Checks: `tests/scenarios/xeen/harvest_once.yml` (dig at plant 255, throw the root away, dig again: nothing and the
  dug-up line; plant 256 gives its root while the party carries one; a save and load keeps both dug; 673 days later
  plant 255 has grown back) passes; `side_quests/q-c21_phirna_root.yml` updated and passes; quest stub 19/19;
  `quests.py` clean; `quests_smoke`, `campfire_once` pass. Translations: 43555's new English is untranslated until the
  next `l10n.py extract`/update round.

**X2 p8, the Sprites: "With p8 i mean the sprites are always in the air."**
- Cause: the Sprites were MM6–MM8 ranged flyers. The Medusa Sprite took the borrowed Will o' Wisp row's Light
  missile (`gen_monsters` falls back to the stand-in's Missile column) and the Killer Sprite, both Sprite Queens,
  Sharla and the Gorgon Sprites carried `missile: Air`. A flying row with a missile hovers its radius + 512 above the
  party outdoors and circles it at range (OE `AI_Pursue1-3` WantedZ, reproduced in `OutdoorWorldRuntime`'s flying
  ranged pursuit height); a melee flyer comes down to the party. A probe at the pin (four sprites spawned 600 away,
  `output/xeen_fb/p3_p8p26/p8/probe.txt`, `probe2.txt`): `attack_ranged` and `orbit` only, a Medusa Sprite 838 away
  and 361 above the party after 2.5 s. The source's sprites (Medusa Sprite D53, Killer Sprite X22, Sharla D90) fly
  but have no ranged attack (XEEN_SYSTEMS flags `F`, not `R`), and MM6–MM8's small winged monsters (harpies,
  gargoyles, bats, wyverns) are melee flyers. The AI follows MM6–MM8 (no engine change).
- Fix (A2 data and generator): `monsters.yml` sprites and dark_sprites `missile: 0` (the Medusa Sprite's attack
  `type: Phys`, the source's 3d3 physical); the Queens keep Sparks and Sharla Lightning Bolt (spells, as MM's Harpy
  Witch). `gen_monsters.py` **refuses** a flying row with a missile unless it says `ranged_flyer: "<why>"` (family or
  tier). Only `monster_data.txt` rows 11530-11538 changed (missile 0; Medusa Sprite Light → Phys).
- Sites (every Xeen flyer with a missile, 49 rows): the sprites (9 rows) became melee flyers; kept as ranged flyers
  with their reason: floating mages (source R), the Beholder Bat (A), octopods (A), eyes (MM's beholders), the
  Guardian, robots (Annihilator R), fire and air elementals (A), the living dragons (R, A) and the undead dragons.
  DECIDE (not changed): the Guardian (the Tower of High Magic) and the Autobot have no ranged attack in the source
  (`F` only) either; they are constructs with energy bolts, as MM's ranged flyers of their kind. If players find them
  as tiresome, the same `missile: 0` makes them melee. D-88's "ranged disablers" at the Temple of Yak are melee
  sprites now (their placement is unchanged).
- Checks: `tests/scenarios/xeen/sprites_come_down.yml` (at the pin, a Medusa Sprite, a Killer Sprite and a Sprite
  Queen spawned 700 off and 400 up close in to within 400 of the party, about 75 above its feet, strike it in melee,
  and a Knight's sword hurts them) passes; `sprites_leave_loot.yml` passes; `check_actor_heights.py` 0 findings;
  `xeen_balance.py --check` passes; `build_world.py --check` 0 differ.

### Orchestrator's list for the final outdoor round (2026-11-24 afternoon)

Maps: X1, X2, X3, X5, D1, D2, D3, D4 (one rebuild each, after the Map Studio round and the door fix). Not X4, X6,
D5, D6 (c7's, clean). Besides each agent's NEXT lists above:
- **Spawns and actors past the map bounds** (|x| or |y| > 23,106; `scene.yml` spawns type 3 and
  `initial_state.actors`), found by openyamm-c7: X1 13 spawns, 4 at the old west-road camp (cells ~3-11, 43-49:
  (-27264, 10912), (-28896, 7808), (-31328, 10752)) and 9 at the old north-road camp (cells ~65-73, 3-18:
  (3936, 27008), (1280, 30528), (7104, 23264)): gen.py's `pop:hill_orcs` and the north camp's pop still point at the
  camps' old spots ((8, 49), (3, 43) ...); one placed Orc (11030, group 74) at (-8704, 24064). X2 4 spawns past the
  north bound: (-10944, 23200), (10720, 23488), (6240, 23712), (-19616, 23392). D2 4 spawns: (-24768, 13056),
  (24608, -8064), (25056, -8608), (27584, -16224). Fix at the source, and add a `reach.spawn` rule to
  `tools/xeen/check_reach.py` (spawns and actors inside the bounds, on walked-on land).
- D2: rebuild for DD-11A/B's moved starts (troll-hole landings (80, -208) and (144, -208), `gen_walk.py` too).
- D1: Kramer's bounty interact pose (3844, 5376) for side quest Q-D11 and promotion 47 after the jail moved.
- `tests/scenarios/xeen/campfire_once.yml` (c7's) needs the rebuilt X1.
- X1 p26 and X2 p8 (agent `xeen-fb3-p8p26`) need no rebuild: the Phirna plants' limit is in the common Lua and the
  quest file, the sprites' in the monster table. After the X1 rebuild, run `tests/scenarios/xeen/harvest_once.yml` and
  `side_quests/q-c21_phirna_root.yml` (they click X1 events 255 and 256, `evt:thing:phirna_1`/`_2`, from poses beside
  the plants at (6144, -10296) and (13568, -7224)); gen.py must keep each plant its own event (the spot is the event).
- D-120 (island finds): `check_reach.py` follows clicked things' teleports (Medin's boat → X2 `island_chest`);
  `reach: water walk or fly` on D4's skerry strongbox and genie lamp, `reach: fly` on D6's `lamp_islet`; D2's fairy
  ring and its nine caps moved inside the bounds (at least cell 20); one Water Walk scenario to D4's skerry.

### Orchestrator's list for the dungeon follow-up round (after the studio round)

D-119 (Gorgon Sprite 11534 Stone → Weak, `gen_monsters.py` refuses Stone/Dead/Errad below level 27), D-121 (XD-23
fire pit, XD-16 skulls, FD-04 lesser shrines and the Lord Xeen Machine become clicks; DD-13's fort pits and FD-04's
Ultimate shrine stay questions; `ask.goal` keep list), D-122 (open-air arrival rule in `check_arrivals.py`, then D7,
P1–P4, X8 markers), D-123 (XD-05 ledge parapet + Xeen ledge-shot check), D-124 (XD-05's X7 gate guards into the
tunnel), and the XD-02 p5 gateway scenario (closing gate 5 at (9273, 4543, -384)).

### Map Studio round before the final outdoor rebuilds (agent `xeen-fb3-studio3`, 2026-11-24 ~15:40–16:50; for A1, A7, A3)

Scratch `output/xeen_fb/p3_studio3/` (scratch builds `build_<key>`, their mounts `mount_<key>`, audits `audit_*.txt`,
the indoor sweep `sweep/`, run logs `pt/`, `rel/`). Binaries rebuilt: `openyamm-studio/build-xeen/oymap` and
`oymap_tests` (526 of 526), `build/tests/openyamm_unit_tests` (3189 of 3189; `build/game/openyamm` had nothing to
relink). The 16 release scenarios pass. Note for anyone checking a scratch build: `oymap audit <path>` reads a map by
its **name** from the asset root, so a scratch build is audited through a mount (`oymap install <L4> --mount <dir>
--assets assets_dev --build <build>`, then `oymap audit <dir>/worlds/xeen/maps/<stem>.odm ... --mount <dir>`);
`oymap export <path>` reads the file itself.

**Outdoor studio requests (round 2's REQUESTS 1–4).** All in `openyamm-studio/core/OutdoorThings.cpp`, each with a test
in `openyamm-studio/tests/OutdoorTests.cpp`, the README's lines and (3) the schema.
1. Culvert grating (`raiseCulvertGrating`): the upright bars start 2 under the water, so their feet no longer lie back
   to back with the water's face. This was also X1's culvert outfall `back_to_back` ×3 (7wtrtyl/7t1butts): the same
   cause. Test: the S8d grating case has no back-to-back pair and its bars' feet are 2 under the dark face's foot.
2. Doorway hood: the roof's and cheeks' backs (on the frame's front) are left out (`OutdoorModelBuilder::addPrism`
   takes a side to leave out). X1's Witch Tower door finding is gone. Test: the hooded den has no back-to-back or
   coplanar pair.
3. `kind: model` gets `drop_overlaps: true`: of each two faces taken that lie on each other (the same way, or back to
   back where that is seen) the smaller is dropped (the later of two the same size). Nystor's ship loses 5 trim faces
   (TRIM2_32a 59 → 54; the hull boards stay) and has no finding. `x2/gen.py` writes it on the ship (a regen of X2 differs
   from the L4 by this one line only), and the ship's two kept entries are **removed** from `tools/xeen/check_faces.yml`
   (`kept: []`): until X2 is rebuilt, `check_faces.py --check` shows the installed X2's 4 ship findings. Test: a sail
   laid both ways with a patch keeps one face.
4. Bridge ends: an end on land stands `raise` (16) over the lowest land across its end and 32 beyond it (the middle, a
   quarter and two fifths of the width each side, open water left out), or halfway between the lowest and highest
   where the land falls more than 32 across it. Every bridge without `height` gets this, humped or not (where the land
   is level nothing changes). D4's `snow_bridge` +33/+43 → ends at 1213/1206 against land 1201–1226: town_fit 0. Test:
   a humped bridge over land falling about 48 a cell across it is within 32 everywhere.

Scratch builds of the current L4s with this oymap (X2 with the ship word added): `check_faces.py --file` X1 clean
(4 → 0), X2 clean (4 kept → 0), D4 1 (the isle tower crown's open edge, old, not this round's); `town_fit_check.py` X1
0, X2 0, D4 0 (was 2); `oymap audit --reach --solve` through mounts: X1 the outfall's 3 back-to-back warnings gone,
X2 the ship's 2 back-to-back and 3 coplanar warnings gone, D4 the same as installed; the texture errors
(`feature_repeated`, `trim_tiled`, `feature_cut`) are the classic kit's and the same as installed. Left in X1's audit:
`water_end_1/2` back-to-back warnings (the studio's audit sees them, `check_faces.py` does not: old). Not installed.

**XD-14's invisible blocker (the door-fix agent's request to A7).** Not the engine, a mover or a portal: the great
hall's two long tables (`platform:table_w`/`_e`, 64 high, x ±1184 to ±1344, y −128 to 896) ran across all three side
doors (the west arch at y 0, the scriptorium's and the kennels' doors at y 832), 64 off the wall. Through a door the
party stood in that 64 between wall and table; its middle stopped at x ±1381 (the table's wall-side face at ±1344 plus
its radius 37), and the table, over the engine's step of 50, passed only by a jump. The face is drawn but hidden behind
the table from the door: an "invisible wall" to the player. **Fix at the source:** `xd14/gen.py` `HALL_TABLES`: the
west table y 224–656 (between the arch and the scriptorium door), the east −128–656 (clear of the kennels door); the
plates and goblet on them moved on. Rebuilt, installed and baked under the locks (16:08 build): audit as before but
for the three new errors' absence (the MAW reserve unchanged, `xeen_balance --check` ok, check_exits 0, check_drops 0
pockets, check_open_sky 0, check_identity clean, `check_door_leaves` clean, stale bakes 0); playtests 3 of 3 pass
(`playtest`, `playtest_exit`, `playtest_hostility`). The rebuild also carries a pending `gen.py` edit of another session
(the study fire at (502, 1606)).
**The check:** studio audit rule `face.in_doorway` (`core/Audit.cpp` `auditDoorwayFaces`, run by every `oymap audit`;
an error on Xeen's maps, a warning elsewhere): walking straight out of a portal one walks through, along every line
across it, the party's middle must get its radius past the jambs; faces it cannot step over count (over 50 from foot to
top, top over 50 over the sill, foot under the head and under 160 over the sill), not door leaves, a face over the
opening itself or a clicked panel across it (XD-13's breach plug, XD-04's cupboard panel, XD-19's secret walls), nor
a drawn face as high as the opening (a closet's back). Test "P3: audit names a table across a doorway's way out".
**Sweep, every installed Xeen indoor map (69):** XD-14 3 (fixed) and **XD-13 1**: the woodpile (`platform:woodpile`
at (−896, 2880), 384 by 256, 72 high, 64 off the west wall) across the great hall's door to the pantry
(`open:hall_pantry`, y 2736–2896): the same fault, for A7 (`xd13/gen.py`: shorten or move the woodpile off y 2700–2940).
Not caught by the rule but seen in the sweep: FD-02's dais of `egywla` blocks 108 past portal 769 (sectors 7/9), its
first step 64 high (over the step of 50) across the corridor with 16 each side: look whether that corridor is meant to
be walked. MM6–MM8 shipped maps: 32 warnings on 120 (steep cave floors, secret ways), left as warnings.

**Q-C8** (`tests/scenarios/xeen/side_quests/q-c8_q-c9_scroll_and_sphinx.yml`): on the way back the walk goes from the
kennels to (1700, 832), opens door 10 (event 20) and walks into the hall at (1200, 832); the east foot→hall step that
had no way is gone. Passes (348 steps) on `build/game/openyamm` against the rebuilt XD-14.

**REQUESTS (final outdoor round: what changes on rebuild).** X1: the culvert outfall's bars (feet 2 under the water;
3 back-to-back gone), the Witch Tower door's and the warehouse door's hoods (no backs), `town_bridge`'s ends (to the
land across them). X2: Nystor's ship with `drop_overlaps` (regen: the one sketch line), `den_door`'s hood,
`ogre_bridge`'s ends. X3: `causeway`, `fen_bridge` ends. X5: `xd09_door` hood, `golem_bridge` ends. D1: `dd10a_adit`
hood, `east_bridge`/`rope_bridge` ends. D2: `dd10b_adit` hood, `footbridge`/`log_bridge` ends. D3: `wrath_bridge` ends.
D4: `snow_bridge` ends (town_fit's 2 errors go). Run `check_faces.py --check` after X2's rebuild (the ship's kept rows
are gone). Not in the round but changed on their next rebuild: X4 (`kings_bridge`, `xd02_adit`), X7 (`black_bridge`,
`fd04_gate`, `xd05_gate`), D5 (`giants_hall_doors`, `bosco_door`). Indoor: XD-13's woodpile (A7).

### F57, the Giant Toad (D-118) (agent `xeen-toad-repair`, 2026-11-24 ~15:00–16:45; for S)

**Repaired without Meshy and installed; for the user's look.** Before/after: `output/xeen_fb/p3_toad/before_after.jpg`
(Blender close-ups of the attack, the hop takeoffs and the dead pose, and the player's picture against the new attack
from the pin). Project log: `level_generation/creatures/xeen_toad_claude/README.md` "Log".
- **Mouth.** The black slits were the painted lip crease, opening because the upper lip followed Head and the lower
  lip Chest while the head reared. The crease faces now carry their own material `Mouth` (a dark-to-red-brown
  gradient, one colour for every tier), and the lower lip rides on a new `Jaw` bone (Head's child), so the mouth stays
  shut when the head moves and opens (up to 9 degrees) only around the tongue strike, onto a red-brown cavity.
  Deviation from the ruling's "fixed to Head and Throat": the Throat bone's puff scale would push the lower lip about
  by up to 12 cm, so the lower lip is on Jaw. Attack rears less (pitch 3-4, head 4-5 degrees, were 6-8 and 10-12) with
  a smaller throat puff, so the head no longer fills the view.
- **Thighs.** The heat weights gave each fused thigh/shin lobe mostly to Foot and Toes, so the 55-degree heel lift
  threw the lobe over the back. New hind-leg weights (Toes and the sole only at the front, the lobe Thigh/Shin), a
  stable IK pole in the leg's rest plane, an 18-degree heel lift and earlier toe-off. Gate (body frame, the highest
  leg vertex against the back over the hips): Walking +11.3 -> -8.5 cm, Running -1.4 -> -9.2 cm; the largest leg edge
  stretch 27 -> 4 cm (Walking), 45 -> 5 cm (Running).
- **Belly peg.** It was the tongue, extended to 35 % in Death and standing out of the upturned throat; Death and Dead
  keep it in (25.7 -> 4.0 cm outside the body, the resting tongue's own depth in the lip crease) and the throat
  unpuffed.
- Checks: all eight clips pass `scripts/repair_gates.py` (floor, legs over the back, leg stretch, tongue;
  `review/repair_gates.json`, the old clips fail all eight); floor audit (A) ok; winding 0; far LODs rebuilt with
  `lod_repair_claude` (r25_12 accepted, `verify_far_only` OK, tiers A/B/C on the far copies); viewer check (8 clips, no
  errors). In game on X1 at the pin's pose (`output/xeen_fb/p3_toad/ingame/`, isolated run): the attack opens onto the
  mouth with the tongue strike, no slits; the death flips it onto its back with no peg. The hop was not caught in
  game (a hostile toad attacks from where it stands; the friendly one hopped out of view): see the viewer shots
  `level_generation/creatures/xeen_toad_claude/review/shots/` and the clay sheets `review/clips_*.png`.
- **USER**: look at `before_after.jpg`; in game, X1 around [-4934, -1925, 609] (the toad meadow), or the viewer
  `level_generation/creatures/xeen_toad_claude/review/viewer/` (serve with
  `python3 level_generation/creatures/claude_shared/serve_review.py 8912`).

### F57, the Giant Toad: the tongue (D-126) (agent `xeen-toad-tongue`, 2026-11-24 ~17:20–18:10; for S)

**Repainted without Meshy and installed; for the user's look.** Before/after:
`output/xeen_fb/p3_toad/tongue_before_after.jpg` (the native `013.att` frames, the old and new maps, viewer close-ups
of the strike head-on, three-quarter and side, and the game at the pin). Project log:
`level_generation/creatures/xeen_toad_claude/README.md` "2026-11-24, D-126 the tongue".
- **Cause.** Not only the paint: the old map was a 256 px two-colour gradient, and its cylinder unwrap gave the tip's
  end cap (what the player sees head-on) one texel row with a single u at the tip, so the strike drew a flat disc; one
  face per ring also ran backwards across the whole map at the u seam.
- **Fix.** New tongue UVs (`scripts/tongue_uv.py`): the tube on its own seam column, the end cap as a disc around the
  tip at an even 700 px/m, so the cap's texels reach the tip. New paint (`scripts/paint_tongue.py`, procedural, so it
  reproduces): the native tongue's own 16-step turquoise ramp, mid turquoise with darker teal mottling and veins, pale
  lengthwise wet streaks on the top and flanks, a pale crescent on the cap's upper rim, a darker, more saturated tip.
  Material class 7 (mouth interior; `textures/toad_tongue_material_classes.png`), roughness 0.35, specular 0.5. One
  tongue for Giant, Bog and Swamp Toad, outside the hide's region mask, like `Mouth`. Mesh, weights and clips
  unchanged.
- Checks: body maps byte-identical after the rebuild; far LODs rerun with `lod_repair_claude` (r25_12 accepted, the
  same scores, `verify_far_only` OK; the tongue has no far LODs); winding 0; installed with `tools/install_model.py
  --world xeen`; Android textures cooked and verified (this also cooked D-118's new maps, which had none). Viewer:
  `level_generation/creatures/xeen_toad_claude/review/shots/ta_*.png`. In game at X1 p22 (isolated run, pitch -28 so
  the toad clears the basebar; `output/xeen_fb/p3_toad/tongue/ingame/`): the strike shows the mottled, veined, glinting
  cap and tube; a friendly toad's hop caught from behind (`g_hop_00`-`07`), legs tucked, nothing over the back.
- Left as is: the tongue is a ten-sided 240-triangle tube, so up close its cap stays faceted and fills the view at the
  moment of the hit (the strike reaches the party). A rounder, smaller tip would be a model change (not in D-126).
- **USER**: look at `tongue_before_after.jpg`; in game, X1 around [-4934, -1925, 609].

(Orchestrator note kept from the queue entry this replaces: D-129 goes into the next release notes.)

### Dungeon follow-up round: D-119, D-121 to D-124, D-127, D-130, XD-13's woodpile, XD-02 p5 (agent `xeen-fb3-dungeon-followup`, 2026-11-24 ~16:00–18:00; for A2, A3, A7, A8, A1)

Scratch `output/xeen_fb/p3_followup/` (`sb.sh <key>`: regen, build into `output/studio_cal/<key>/b_<time>`, audit of
the stage; `iq.sh <key>`: install, bake under `bake.lock` where a profile exists, audit and every check, playtests;
`mkroot.sh <dir> <keys>`: a private root of hard links with scratch stages over assets_dev, for checks before install;
`hide2.py` = the Darkside `hide.py` with `--any-room`; `try_spots.py`: does an actor see a landing from given spots;
`tests_queue.sh`: the story, side-quest, promotion and focused runs, logs in `tests/`).

**D-119.** `monsters.yml` Gorgon Sprite 11534 `bonus: Stone` → `Weak`. `tools/xeen/gen_monsters.py` refuses a Stone,
Dead or Errad bonus below level 27 (`LETHAL_BONUSES`, `LETHAL_BONUS_MIN_LEVEL`); no other row is under it.
**D-127** (batched): the Guardian 11601 `missile: 0` (written out: left out, the stand-in's missile came back),
`ranged_flyer` gone, Energy touch and DrainSP kept; the robots' `ranged_flyer` reason rewritten without "DECIDE".
`build_world.py --only gen_monsters`: `monster_data.txt` rows 11534 and 11601 only (`--check` 0 before and after),
`xeen_balance.py --check` ok, X8 `check_arrivals` 0 errors.

**D-121.** Clicks, the hook's answer on the status line (the XD-05/XD-27 pattern): XD-23's fire pit (`xd23/gen.py`),
XD-16's two skulls (`xd16/gen.py`), FD-04's Minor, Lesser and Great shrines and the Lord Xeen Machine (`fd04/gen.py`;
`q-f2.machine` now `status: true`, its `window:` gone). Kept questions: DD-13's two fort pits and FD-04's Ultimate
shrine. `check_wiring_rules.py`: DECIDE replaced by `KEEP` ((map, event) → reason); `ask.goal` now 0 errors, the three
kept sites reported as `kept`. Tests that answered: XD-16 `gen_tests.py` (playtest), FD-04 `gen_tests.py` (gongs,
shrine), XD-23 `L4/playtest.yml`, side quests `q-c15_troll_problem`, `q-c26_shangri_la`, `q-f2_dungeon_of_death`, and
`tests/scenarios/xeen/hooks_fd04.yml`. The `where:` texts of q-c15/q-c26/q-f2 say "a click" (`quest_hooks.yml`).

**D-122.** `check_arrivals.py` open-air mode for D7, P1–P4, X8 (`OPEN_AIR`): `arrival.open_hot` (error: an aggressive
monster that is not `immobile` or has a missile or spell, within 2,000 2D with a clear line), `arrival.disabler`
(error: D-87's ranged disablers, d85.py's kinds, within 5,888 2D, line or not; a spawn marker counts by any row its
slot can roll), `arrival.open_seen` (warning: what the indoor rule would have said). Before: 1 error on the six maps,
D7's DD-17/FD-01 landing (-18688, 8448) with the Megadragon 1,086 away on the hatch; no ranged disabler anywhere
(the sprites are melee now). Fix: `d7_design.py` `BOSS` at (-19584, 10496) by the crag's east foot (2,235 from the
landing; its leash circle still 6,019 from every other walkable place, D-54's 5,888 kept; sleep sound moves with it).
D7 rebuilt (no bake profile): 0 errors. Also: `check_arrivals.py --spawns` counts the BLV's own spawn markers (the
scene has none; XD-05's archers are BLV markers): off by default, see NEXT.

**D-123.** XD-05's top landing in the bat chimney gets a 64-high, 16-thick rock parapet on its lip (y 7856–7872,
x 1856–2304; `L4/rooms.yml`, base on the landing). Test `tests/scenarios/xeen/xd05_ledge_parapet.yml` (AI arenas
`xd05_ledge_parapet_back/_lip.arena.yml`, an Orc Archer in the drum hall's doorway as the F42 repro): on the old map
the archer decides `attack_ranged` 5 times in 12 s from 140 back (every arrow dies on the lip); with the parapet 0
times. At the parapet it sees the party and shoots, but its arrows strike the parapet, and so does the party's Fire
Bolt: the doorway is almost straight below, so a shot aimed at the party's middle crosses the lip ~38 over it while the
eye line from 140 back crosses ~51 over: no height in 64–96 lets both through (DECIDE 1). The test pins what is built.
New Xeen-only check `tools/xeen/check_ledge_shots.py` (`ledge.thin_shot`, warnings): lips of walkable floors over a
drop of 128+, party spots 60/140/220 back, shooter spots on every lower floor 256–3,000 beyond the lip (monsters move)
where a ranged hostile (placed, BLV marker or scene spawn) stands within 5,120; flags where the clear sight line passes
within 16 of the lip's edge. World sweep (before the parapet): 381 lips on 23 maps, `ledge_world.txt`: P3 74, P2 71,
XD-12 48, P4 35, P1 19, XD-22 18, DD-07 17, DD-17 16, XD-04 14, XD-05 12 (now 11: the drum hall's terraces, a ledge
window; the pinned lip is gone), D7 11, X8 9, XD-11 6, DD-14 6, XD-16 4, FD-01 4, DD-22 4, FD-04 3, DD-19 3, XD-03 2,
DD-21 2, DD-16 2, XD-25 1. For each map's next rebuild (the planes and skyroads: island rims over flyers; most need
a look before a parapet).

**D-124.** XD-05's gate guards `guard_e`/`guard_w` into `room:back_tunnel`'s long climb east ((1664, 11672),
(1440, 11666), facing east, `leash: 600`), out of sight of X7's landing; `check_arrivals` XD-05 0 errors, 0 warnings.
`playtest_back.yml` clears hostiles on the tunnel walk.

**D-130** (by the Darkside method, `hide.py`, checked on the scratch stages through `mkroot.sh` before install;
`check_arrivals` 0 errors on all six after). XD-10: the north and south mouths have no hidden spot, their Flying Feet
pairs wait at the near end of the icicle hall and the frost cavern (`dress.py` PLACED, a third item names the room
they stand in, ids unchanged); icicle hall ×4, mirage hall FF ×3 and Guardian (-384, 4448: hidden from the south
landing, 5,230 from the north one), frost cavern FF ×2 and Guardian moved. XD-13: hall golems 1–3 and 6 (golem 1 north
of the moved woodpile). XD-16: the ash gallery's first Demon in the gallery, the other two in the vault ante-room's
mouth; the fire lake's three Devils to its far shores. XD-19: the nave's five (same nave). XD-22: the porch has no
spot: its two Ninjas in the kitchen's and the shrine's mouths. XD-23: the mouth has none: its trolls in the larder's
mouth and the bone hall's west side; two bone-hall trolls moved; the mouth's south-east corner kept square
(`CAVES 'keep'`: the cave shaper had cut it once no troll stood there, and the bone hall's opening no longer fit).
No landing moved (all are written by outdoor maps). XD-15's drop cell kept (D-39).

**XD-13's woodpile** (`face.in_doorway`): `xd13/gen.py` to (-896, 2240), south of the pantry door; XD-13's audit has no
`face.in_doorway`. **FD-02's "dais" at portal 769** is the Stair of the Name's flight (32 risers of 32, 352 wide in a
384 room): not a block (the sweep read two risers as one), no change.

**XD-02 p5.** `tests/scenarios/xeen/xd02_gate_reopens_on_party.yml`: the points east, the party set at the pin
(9273, 4543, -384) in the gateway, the Turntable lever pulled: gate 5 (`slide_down`, scene `mover: {bodies:
reverse}`) closes fully through the party in 1.75 s (`closing` … `closed`). **Fails: an engine fault** (REQUEST 1).

### Final outdoor round, Cloudside: X1, X2, X3, X5 (agent `xeen-fb3-final-cloud`, 2026-11-24 ~16:15–17:30; for A5, A6, A1, A3)

Scratch, tools and captures `output/xeen_fb/p3_final_cloud/` (`tools/cycle.sh`, `install_check.sh`, `checks_only.sh`,
`sq.py` (the side-quest runner on `build/game/openyamm`), `focused.sh`, `ascii.py` (walked-on land per half cell));
before `before/xeen_<map>/`, after `after/xeen_<map>/` (the player's pin poses; X5 at the jammed sites; X2 adds
`11-p6_top`/`12-p6_high`; X3's Newcastle from the ramp in `after/xeen_x3_newcastle/`). The L4s before the round:
`briefs_before/`.

**New and extended checks.**
- `tools/xeen/check_reach.py` `reach.spawn`: every `scene.yml` spawn point and placed actor inside the bounds
  (|x|, |y| ≤ 23,106) and within 384 of walked-on land. D-120's teleport rule: a reached clicked thing whose
  `effects`/`else_effects` teleport within its map joins the land at the destination (Medin's boat → X2's island and
  `island_chest`, no exemption needed). Exemptions cannot stand in a sketch (`oymap validate` refuses unknown words), so
  they live in the new **`tools/xeen/check_reach.yml`** `kept:` (`{map, thing: <glob>, reason}` for a thing,
  `{map, group: <actor group>, reason}` for the land rule of a placed group, never the bounds); an entry that keeps
  nothing is an error. Kept: X2 group 80 (D-54's three Water Dragons over the lake), D6 groups 2–4 (fire elementals
  over the lava); the dark round added D4's and D6's D-120 entries. World: **0 errors**.
- `tools/xeen/town_fit_check.py` `platforms.through` (X2 p6): the land more than 4 over a platform's top inside it.
  `things.overhang` (X3 p3): the land more than 24 under a free-standing portal's (a mirror's dais), fountain's or
  well's lowest point. Sites on maps outside this round are in `town_fit_pending.yml` (D5 munchies ×2, D6 pinnacle,
  X4 sky_crack_ledge and olympian_fountain, X6 oasis_fountain); D1's square, D3's square and D4's well were cleared by
  the dark round's rebuilds. `towns.py --strict`: 0 town_fit errors.

**X1** (installed 16:34, one rebuild). `reach.spawn` 14 → 0: `pop:hill_orcs` (12, 43), (8, 49), (3, 43) →
(25, 41), (27, 34), (22, 38) round the west road camp's new fire (22.5, 42.6); `pop:road_orcs` (72, 10), (67, 13),
(77, 19), (66, 5), (73, 3), (65, 17) → (76, 21), (64, 20), (81, 20), (59, 20), (85, 21), (90, 21) round the north
road camp (72.8, 21.5); the orc scout (group 74) (47, 17) → (47, 21). Arrivals ≥ 2,000, doors ≥ 4,500 (gen.py's own
checks), D-85 0. The studio round's changes came in (outfall bars, Witch Tower/warehouse hoods, `town_bridge` ends:
`check_faces` clean), and the ruin rule (ruined cottage, burned farm: no windows, wall-stone trim). `houses.jammed` 0
(nothing left). Phirna plants still one event each (255–258). Checks: town_fit 0, reach 0, faces clean, wild 0,
door 0, D-85 0, audit errors only the classic kit's `textures.*`; walk 426/426, hostility pass; `campfire_once`,
`harvest_once`, Q-C1, Q-C20, Q-C21, Q-C22, X1-TAM pass. Left: **villagers** X1 villager 13 starts 453 from Joe's
shop door (since the shop moved, 13:26): `villagers.py --place X1` rewrote `source/towns/villagers_spots.yml`'s X1
block; it reaches the map at X1's next rebuild (c7's `fit_maps` rebuild).

**X2** (installed 16:39, one rebuild). `reach.spawn` 4 → 0: rangers (44, 19) r 1.5, (85, 19), (76, 18) → (44, 21)
r 1, (85, 21), (76, 21); ogres (27, 19) r 1.5 → (28, 21) r 1. Nystor's ship `drop_overlaps` built: `check_faces` X2
clean (its kept rows gone). `den_door`, `ogre_bridge` from the studio round. **p6, the cut path strip, traced:** the
three market stalls on Bridge Square had `floor: PLATEAU + 16` (the court's top, 1,040); the studio's land, in steps of
32, rose to 1,056 under them, through the court, leaving the court's paving as a thin strip beyond the risen ground at
its east edge. `x2/gen.py`: the stalls' floor `PLATEAU` (the court's top covers it by 16); after: the stalls stand on
the paving (`after/xeen_x2/06`, `11-p6_top`). Check `platforms.through`. D-120: `check_reach` follows Medin's boat.
Checks: town_fit 0, reach 0, faces clean, wild 0, door 0, D-85 0; walk 449, hostility pass; Q-C2, Q-C3, Q-C12, Q-C13,
Q-C17, Q-C18, Q-C19, Q-C23, `sprites_come_down`, `sprites_leave_loot` pass.

**X3** (installed 16:55, **three builds**: the first two installs left audit errors and the p3 view unchanged).
Newcastle (p3): the cause was not the terrace's outline but the gate stair's road bed: `NEWCASTLE_STAIR` ran on to
(82.5, 37.5) inside the gate, and the studio eases a road's land over five cells, cutting a ramp 96–256 deep into the
terrace between the mirror and the west gate tower (nodes (82–83, 37–39) at 1,664/1,600/1,504 against 1,760): the
mirror's dais hung over it and the tower's plinth showed. Now the stair ends at the terrace edge (82.5, 39.5), the
ramp notch of the terrace polygon is filled; the terrace is level to row 38, the mirror and towers stand on it
(`after/xeen_x3_newcastle/03-gate_high.png`; the pin's own pose is now inside the bank). Check `things.overhang`.
Ebenezer's Tent (left from the first outdoor round): the door 128 wide (`common/wild.py TENT_DOOR`, was 192: audit
`doors.tiled`), the keg west of the rain barrel (audit `dressing.door`). `causeway`/`fen_bridge` ends, ruin rule
(wreck, watchtower), `classic_kit.yml fit_maps` += x3 (orchestrator's request). Checks: audit 0 non-texture errors,
town_fit 0, reach 0, faces clean, wild 0, door 0, D-85 0; `x3/gen_walk.py` (676 steps, the ramp's z) pass, hostility
pass; Q-C7, Q-C12, obelisks pass.

**X5** (installed 16:48, one rebuild, A6's script). Winterkill's jammed houses (plots keep the half-cell grid):
house #12 and the tavern half a cell west (tavern/temple 80/102 → over 128), #3 half a cell south (from #2), #8 half a
cell east (from #7); the tavern's barrel pair with it; the outpost's first bones off the tent wall (`props.in_wall`).
`fit_maps` += x5. `xd09_door`, `golem_bridge`, the Troll Warren's stone shell (`wild.free_mouths`) came in. Checks:
town_fit 0, reach 0, wild 0, door 0, wall_check 0, house_signs 0; walk 754, hostility pass; Q-C1, Q-C4, Q-C6, Q-C14,
Q-C15, Q-C16, Q-C18 pass. `check_faces` X5: 9 (as installed before): `palisade_1` ×8 back to back (rail end caps
meeting where the fence's rail pieces join on the slope) and `xd10_north` ×1 coplanar (7snow): studio (REQUESTS).
D-85: `common/d85.py` lists FAIL 6/WARN 2 on X5 (Winterkill's start beside the haunted town's skeletons, arrivals by
troll markers); no marker or actor of X5 moved in this round, so they predate it: for A6.

*Rebuilt, installed and baked once each* (bake where a profile exists; D7 has none): XD-05, XD-10, XD-13, XD-16, XD-19,
XD-22, XD-23, FD-04, D7. FD-02 not rebuilt (no change). Every one: `oymap audit` 0 errors, `check_exits` 0,
`check_open_sky` 0, `check_identity` ok, `check_door_leaves` ok, `check_arrivals` 0 errors, `xeen_pack_reserve` ok;
`check_drops`: XD-05's prisoner pit and XD-10's pool (2048, 2944), both known; D7 open air. Playtests: all pass on
XD-05 (4), XD-10, XD-13, XD-16, XD-19, XD-22, XD-23, FD-04 (9); D7 13 of 14: `playtest_fall_cd12` fails after the
fall onto D5 (Brokk *gains* 4–5 HP in the 20 s the test expects no change; D5 was rebuilt by c7 at 16:41; REQUEST 2).
After the runs: `q-f2.machine` also `else_status: true` (the broken machine's line on the status line, not a window).
*Global:* `stale_bakes.py --check` 0; `xeen_balance.py --check` ok; `balance.py` every act within 15 % (rows already
off before this round: XD-19 1.46, DD-04 0.37, DD-10/11 0.75; no count changed); `check_immobile.py` 0;
`check_actor_heights.py` 0; `check_wiring_rules.py` 0 errors (3 kept); `quest_stub.py` all pass. `build_world.py
--check` shows `trainer_places.txt` differing: another session's source change, not run here.
*Story* (`build/game/openyamm`): 11, 33, 73, 75, 81, 83, 87, 89, 91, 93, 95 pass (STALE notes from the outdoor
rebuilds on 11, 33, 73, 81, 87, 95). *Side quests:* x1-tam_oslos_son, q-c4, q-c15, q-c26, q-f1, q-f2, q-d26, q-d27 (D7),
q-d28 pass (q-d26 after its Megadragon post and clear radius moved with D-122). *Promotions:* 21, 25, 27 pass.
*Focused:* `hooks_fd04.yml` and `xd05_ledge_parapet.yml` pass; `xd02_gate_reopens_on_party.yml` fails (REQUEST 1).

**REQUESTS.** (1) A1, engine: a sliding gate with `mover: {bodies: reverse}` closes through a party standing in its
gateway: XD-02 door 5 (`slide_down`, direction +z, 320) from the pin, `closing` to `closed` in 1.75 s with the party at
(9273, 4543, -384) on the leaf's plane (`IndoorSceneRuntime::applyMoverBodyRules` / `indoorMoverFaceBlocksBody`: for a
leaf moving down through the body's axis both faces are seen as "behind" or not approaching, or the party is never
tested). Repro `tests/scenarios/xeen/xd02_gate_reopens_on_party.yml`; it should pass after the fix (MM9's sliding
ReopenOnContact doors take the same path). (2) c7 (D5): D7 `playtest_fall_cd12` lands on D5's `entrance:d7_fall`;
since D5's 16:41 rebuild a member's HP rises by 4–5 in 20 s there (a regeneration source by the landing?). (3) The
outdoor owners: no landing was moved (D-130's monster moves sufficed).

**DECIDE.** (1) D-123's "from the parapet both shots land" cannot hold at XD-05's landing for any parapet of 64–96:
the shooter's doorway is almost straight below (the shot at the party's middle crosses the lip ~38 over it, the eye
line from 140 back ~51). Built: 64 (no shots from back; at the parapet the shots strike it, visible cover). Options:
keep (cover); or remove it and leave the thin-line fault (the fallback); or the shared AI's thick-ray test (D-123 said
no). (2) `check_arrivals.py --spawns`: count the BLV's own spawn markers (XD-05's archers and most dungeons' slot
monsters are BLV markers the check never saw). Off by default until its new findings are looked at.

**NEXT.** Run `check_arrivals.py --all --spawns` and look at what the markers add. The 23 maps of the ledge list on
their next rebuild. Refresh the stale story checkpoints after the outdoor round. XD-02's gate test after A1's fix.

### Queued (orchestrator): the spawn-marker and ledge-check batch (D-132, D-133)

Starts when a heavy-agent slot frees up, after the gate fix: tighten `check_ledge_shots.py` per D-132; make
`--spawns` the default in `check_arrivals.py` per D-133 and fix its 5 errors by `hide.py` in the same batch (XD-02,
XD-04, XD-05, XD-08, XD-26: one rebuild each, with their tests); rerun the XD-02 gate scenario after the engine fix.
Also in that batch: the outdoor D-85/D-87 arrival checkers (`level_generation/projects/xeen/common/d85.py`, per-map
`check_d85.py`) count scene spawns too, per D-133. Found through D7's `playtest_fall_cd12`: a Xeen Roc spawn 1,312 from
D5's `entrance:d7_fall` (1024, -4608) reaches the party in the quiet window. c7 moves that pop on D5 (2026-11-24);
rerun D7's playtest after.

**Tests (after the four installs, `build/game/openyamm`).** Main story chain from 01 (fresh checkpoints, after the
dark round's D1–D4 installs and the dungeon follow-up's segments): **52/52** (17:05–17:15). Promotions `--start`
**41/41** (the last six rerun: A1 relinked the binary mid-run). Side quests crossing X1/X2/X3/X5 (24 scenarios, above)
pass; focused `campfire_once`, `harvest_once`, `sprites_come_down`, `sprites_leave_loot` pass. Every map's walk and
hostility playtests pass. `stale_bakes --check` 0. `check_reach` world 0. `towns.py --strict`: only the villager
errors (X1 above; D1's is the dark round's).

**REQUESTS (A1, studio; none built).**
1. Fence rails (`openyamm-studio/core/OutdoorThings.cpp`, the `fence` kind): where two rail pieces of one fence meet
   end to end with no post between (on a slope), their end caps lie back to back (X5 `palisade_1`, 8 findings of
   `check_faces.py`). Leave the caps out where two pieces of one rail meet. Test: a fence over a slope has no
   back-to-back pair. Xeen only uses this kit; MM6–MM9 maps are not studio-built.
2. Cave mouth `xd10_north` (X5, shell `7snow`, 576 by 1536, floor 1,400): two of its shell faces lie on one plane
   facing the same way (`faces.coplanar`, 2,834 sq units at (16352, 10986, 1484)). Look at `cave_mouth`'s shell where
   its side meets the land at a node line.
3. A building's `floor` off the land's 32 step (X2's stalls at 1,040) rounds the land under it up, through a platform
   it stands on. Either keep the land under a building at or under its floor, or refuse such a floor in `validate`
   when the building stands on a platform. Checked now by `town_fit_check platforms.through`.
4. Optional: a road bed (`gradeRoads`, eased over five cells) may lower land under a portal or a building's footprint
   (X3's stair into Newcastle's terrace). An audit warning when it does would catch the next one; `things.overhang`
   catches the result for portals, fountains and wells.

**DECIDE.** None new. (X3's gate ramp now starts at the terrace edge with a steeper last cell (448 in one cell, under
the game's 512 step): the walk passes; a gentler ramp would need the terrace's south edge or the stair moved.)

**NEXT.** c7's `fit_maps` rebuild of X1 and X2 (not in `fit_maps`; both installed this round before the request):
X1's then carries the new villager spots (villager 13). A6: X5's `common/d85.py` FAILs (Winterkill's start by the
haunted town's skeletons, arrivals by troll markers), predating this round. `town_fit_pending.yml`'s D5, D6, X4, X6
entries at those maps' next rebuilds.

### Sliding gate closing through the party: XD-02 p5, the follow-up round's REQUEST 1 (agent `xeen-fb3-gatefix`, 2026-11-24 ~17:00–18:00; for A1)

Scratch: `output/xeen_fb/p3_gatefix/` (scenario logs `scen/`, `sumA.txt`/`sumB.txt`; playtests `maps/`; story
`story_73_85.log`). No map rebuilt or installed.

- **Cause: the side test, for a body between a thin leaf's two faces.** XD-02's door 5 is a studio leaf of two faces
  (3310, 3311) 16 apart and no top face; `slide_down` stores it sunk in its floor slot (open at distance 0, +z 320 to
  close), so closing raises it. The pin's party stands on the leaf's line, 11 behind one face and 5 behind the other.
  `indoorMoverFaceBlocksBody` lets a face stop a mover only when the body's axis is in front of it (so a trailing face
  of a solid moving away stops nothing); here the axis is behind both faces, so the rising leaf never counted and
  went up through the party. `reverse` itself was wired for slides (the hold-and-reopen code is shared); nothing
  reached it. The same holds for any 2-face leaf falling from the ceiling (DD-15's door 18) onto a body on its line.
- **Fix** (`game/indoor/IndoorMovers.cpp`/`.h`, `game/scene/IndoorSceneRuntime.cpp`): `indoorMoverFaceBlocksBody` takes
  the sliding mover's direction (zero for a rotating or spinning one, which keep today's rule exactly). A face sliding
  within 60° of its own plane leads with its edge: once it approaches within the body's radius (and was not the floor
  beneath the feet) it stops the mover on either side. A face sliding along its normal keeps the side test. MM6–MM8 have
  no `bodies` movers, so they are untouched; MM9's sliding `hold`/`reverse` doors take the same path (their side faces
  now also count from behind; a door opening or a gate rising away still moves away from the body and stops nothing).
  Rules doc: `devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md`, "Bodies in the swing".
- **Tests.** `tests/scenarios/xeen/xd02_gate_reopens_on_party.yml` passes (gate `closing` -> `open` at 1 s and after;
  the party walks out and back); it failed on the 15:41 binary (`closed`). Unit test "mover bodies: a thin sliding leaf
  stops on a body standing on its line, between its faces" (`tests/IndoorMoversTests.cpp`); unit 3190/3190.
  Scenarios 44/44: 14 MM9 door/mover scenarios (`mm9r_*/scenario_doors_exits.yml` of the maps with sliding `bodies`
  doors, `anskramkeep/scenario_rotating.yml`, `bootcamp_blv/scenario_doors.yml`), 4 MM9 door scenarios
  (`tests/scenarios/mm9/`: vent grate, trial with traps, open hatch, cell step), the 16 release scenarios, 10 Xeen door
  scenarios (xd02 gate, dd15 lift reload, dd12 plate, xd26 open leaf, fd04 rotating door, hooks fd02/fd03/fd04/dd26/xd18).
  L4 playtests of four sliding-gate maps, 14/14: XD-02 (3), DD-15 (4), XD-04 (3), DD-06 (4). Story 73 and 85 pass
  (DD-15's lift gate; STALE notes for D5 from the outdoor rebuilds).

### Final outdoor round, Darkside: D1, D2, D3, D4 (agent `xeen-fb3-final-dark`, 2026-11-24 ~16:20–17:40; for A5, A6, A3)

Scratch `output/xeen_fb/p3_final_dark/` (tools `cycle.sh`, `install_check.sh`, `queue.sh`, `sq.sh` (scenarios with
`build/game/openyamm`), `sites.py` (site tours), `doorpos.py` (a door's middle and its pose)). Before captures from the
installed maps `before/xeen_<map>/` and `_sheet.jpg`; after `after/xeen_<map>/`, `after/xeen_d2b`, `d2c` (the fairy
ring, the rope walks), `after/xeen_d3b` (the Guild of Light and Astra's House from above). Every map regenerated by its
generator with the classic kit and `fit_maps` (D1–D4 added to `classic_kit.yml` on the orchestrator's word), built with
the studio round's oymap, `gen_walk.py` rerun on the build, installed with its bake (A6's script for D1, D2, D4; A5's
under `bake.lock` for D3), terrain weights.

**Per map.**
- **D1:** Kramer's bounty pose: Kramer's Caravans is the classic stables office now, door (4144, 5904): the pose is
  (3844, 5904) in Q-D11 (both), Q-D2, story 43, promotions 47 and 49, `class_table.py` and two prep notes. The jail's
  door pose (2176, 8724) in Q-D2 (moved by the earlier pass). `dd10a_adit` hood, `east_bridge`/`rope_bridge` ends,
  the stables and `fit_maps` by regen. `houses.jammed`: none left (weapon shop and jail clear). New sites found on the
  way: the square's paving had the DD-01 hatch's raised land 79 through its corner (`platforms.through`): `DD01_AT`
  a cell east, (67.5, 57.5) (DD-01's arrival unchanged; hatch pose (1300, 3328) in story 45 and Q-D5); villager 47
  stood 493 from a house door (`villagers.py --place D1`). D-85: NPCs 4951, 4953, 4956 at 5,527–5,803: **still there**
  (unchanged by this run).
- **D2:** the four spawns past the bounds were three wolf markers: (16, 38) → (22, 36), (112, 80) → (106, 78),
  (118, 95) → (107.5, 86); `reach.spawn` 0. DD-11A/B landings `HOLE_INSIDE` (80, -208), (144, -208), `gen_walk.py` too;
  Q-D13 and promotion 63 assert the new landing. D-120: the fairy ring and its nine caps at (21.5, 96.5), the
  village's empty south-west corner (caps east of cell 20.4). Rope walks: the guild's deck (720) and house 1's (680)
  left walk ends 34–40 under their decks: all four decks at 700, `bridges.step` 0 (captures `after/xeen_d2b`). Stumps
  in walls: the eight charred stumps stand on the palisade's line and are shown only by the event that hides the
  palisade: `town_fit_check.py props.in_wall` skips a decoration shown by an event that hides the model (they are never
  seen together). `dd10b_adit`, `footbridge`, `log_bridge` by regen.
- **D3:** the Guild of Light [2, 2.5] instead of [2.5, 2.5] (`gen_l1.py`; plots keep to half cells between the Guild of
  Spirit and Astra's House, the quarter wall behind it): 56 → 312 apart; Nasir's pose (-13824, 20548, 1504) in Q-D18,
  story 65, promotion 45, `class_table.py`. The barrel pair stood inside Saffron House: against its south wall now.
  The square's paving starts at y 27.75 (`platforms.through`: the quarter terrace's foot rose 54 through its corner).
  Stables (Sandcaster Caravans, office door (-11984, 12048)), Vespar's ruin (no windows, wall-stone trim),
  `wrath_bridge` by regen.
- **D4:** `snow_bridge`: town_fit's 2 errors gone. D-120 marks in `tools/xeen/check_reach.yml` (the sibling's format:
  the sketch refuses unknown words): skerry strongbox and genie lamp `water walk or fly`, D6 `lamp_islet` `fly` (D6 not
  rebuilt), and D-36's five swimming octopods (groups 3–7) for `reach.spawn`'s land rule. A Lakeside villager stood
  on the graveyard isle (`reach.spawn`): `villagers.yml` Lakeside `avoid` the isle, spots re-placed. The warding well
  hung 43 over the brow's slope (`things.overhang`): at (84.75, 95.5) by Well Fork. Scenario
  `tests/scenarios/xeen/d4_skerry_water_walk.yml`: Water Walk from the west shore over the lake to the strongbox, the
  party unhurt, the chest opens; without the spell the same walk hurts the party (checked).

**Checks (installed).** town_fit 0 on all four (kept: D1 `jetty_pier`, D4 beacons), check_reach 0 (kept as above),
door 0, wall 0, check_wild 0, house signs 0, villagers 0 errors on D1–D4 (X1 Vertigo villager 13 left: X1's),
`stale_bakes --check` 0, key_npcs and actor heights rerun. check_faces: D1 28 (the F31 list, unchanged), D2 0, D3 5
(south gate, spring fall, unchanged), D4 1 (isle crown, old). Audit: D2 0 errors; D1 `doors.tiled`
(`kalindra_gate_restored`, xvsdoor 2 across) and one `textures.feature_repeated` (xvswin), D3 8 and D4 1
`feature_repeated` (xvwin/xvswin on classic-kit houses: lucio jetty, alchemist, training, armour, sc_houses #10, #11,
#14, #23): the classic kit's, for c7. D-85: D2, D3, D4 0; D1 3 (above).

**Tests (`build/game/openyamm`).** Playtests: D1 walk 908, hostility 50; D2 391, 67; D3 706, 44; D4 426, 87: pass.
Story 39–99 (the chain from 39, checkpoints refreshed): all pass, no STALE after 39. Promotions `--start`: 41 of 41
(47 included). Side quests crossing D1–D4: 32 of 32 (Q-D11 both, Q-D13 after its landing assert, Q-D18 and Q-D2 after
their poses), plus `d4_skerry_water_walk`.

**REQUESTS.** (c7) the classic kit's audit errors above with `fit_maps` on: `feature_repeated` xvwin/xvswin on 2-storey
kit walls (3 across, 2 down) on D1 (1), D3 (8), D4 (1); D1 `kalindra_gate_restored`'s door picture 2 across.
**NEXT.** D1's D-85 NPCs (4951, 4953, 4956) for A6 (they predate this run). The fairy ring's caps are small
mushroom decorations hidden in the grass at a cell (`after/xeen_d2c`): a look for A6 if "tall glowing caps" is meant.

### For the next decider batch (orchestrator)

- The toad's tongue tip is a ten-sided tube of 240 triangles: in game the cap is still faceted and fills the view at
  the hit. A rounder, smaller tip is a model change (no Meshy needed?). Do it, or leave it?

### Map Studio round 4: the final outdoor round's studio requests, D1's D-85, D2's fairy caps (agent `xeen-fb3-studio4`, 2026-11-24 ~17:40–18:20; for A1, A6, S)

Scratch `output/xeen_fb/p3_studio4/` (`build_check.sh` builds an L4 and runs town_fit, check_faces `--file` and the
audit through a mount; `model_diff.py` lists the models and land nodes a build changes against the installed map;
builds `b2_<map>/`; proofs `b2_x2_1040/` (X2's stalls back at 1,040), `b2_x3_oldstair/` (X3's old stair), `d1_moved/`,
`d2_caps/`; capture `shots/d2_caps_after.png`). `oymap` relinked 18:01 (after the round's last change; c7's relink
for X4 carries these too), `oymap_tests` 527/527. No map installed.

1. **X5 `palisade_1` "back to back" ×8: not the studio.** The pairs were the two sides of one 8-thick rail. Integer
   corners tilt one side 0.03° from the other, and `check_faces.py` compared the planes' constants (`d`): 17,000 out,
   that cannot tell 8 apart. The fence has no end caps. **Fix in `tools/xeen/check_faces.py`**: one plane = every corner
   of each face within 1 of the other's plane (the studio's `Coplanar` already measured so); the bucket key coarser.
   World run: X5's 8 and D7's 1 (a cloud face 5.9 from a floor) go, nothing else changes (82 maps).
   `check_faces.py --self-test` holds the rail's real faces (the old test fails it).
2. **X5 `xd10_north` coplanar: the cave-mouth shell, every mouth.** Rim 64 + mouth 448 fill the 576 footprint, so the
   mound from each jamb to the side lies in the side's plane. Roughness shook a point outward, the clamp put it back on
   the side, but its shake along the side stayed: two points 31 apart swapped and the quad folded onto itself. Also
   found by a sweep (4 shapes × 4 roughness × 60 seeds): the corner column (front foot = footprint corner) shaken into
   the rim's recess, and two cuts 1 apart making slivers. Fix in `core/OutdoorWaysIn.cpp` (README "Xeen pins round
   P4"); test 960 builds, 0 pairs (49 before). X5 scratch: `check_faces` 0 (was 9), the audit's coplanar warning gone.
3. **A floor off the 32 step on a platform.** `levelPlots` rounded a said floor to the nearest step: X2's stalls at
   1,040 stood at 1,056, the land with them, through the court. Now a building whose plot overlaps a drawn platform
   stands at its said floor, the land under it at the step at or below (covered by the platform). Off a platform: as
   before (D1's town floor 1,150 on land at 1,152 would otherwise sink every plot 32). X2 scratch with the stalls at
   1,040 again: `platforms.through` 0. D1's DD-01 hatch (the wedge's own mound) and D3's square (the terrace's eased
   foot) were other causes; their generator moves stand and `platforms.through` keeps catching those.
4. **Road beds by things:** a build warning (README). X3's old stair (`b2_x3_oldstair`): "lowers the land 142 within a
   cell of thing:newcastle_mirror" (and 96 by the ruin); the current X3: none. Current L4s warn on X1 (north_street by
   gatehouse_north 202, orchard_road by pyramid 144), X2 (chapel_path by tito_chapel 111), X4 (lava_track by
   rim_lookout 73, falls_path by olympian_fountain 84), D3 (gate_street by both south gate towers 72, guild_row by
   wq_houses#1 187, high_path by crag_5 340), D4 (camp_lane by camp_tent_2 80), D6 (alamar_road by both gatehouses
   69): for the map owners to look at (town_fit and check_faces pass on all of them).
5. **D1's D-85 "FAIL"s were the checker.** `common/d85.py` counted every placed actor, so Castleview's villagers
   (group 47 peasants and monks) were "hostiles" 775–2,485 from givers 4951, 4956 and 16 town arrivals. Now it counts
   the actors `check_arrivals.hostiles` counts (aggressors or rows not friendly to the party). What is left near the
   three givers (5,527–5,803: Arachnoid marker 17, Electrapedes 11/12, a Gremlin Saboteur; Yog's marker 35) is
   D-85's warning band with no disabler, kept by D-87 (its line naming "D1's Joe, Justine, Luna and Yog"): no move.
   **D-133's first fight:** Electrapede actor 12 (group 3) 1,734 from `entrance:d7_rope`. `d1/gen.py`: the pack at
   `ELECTRAPEDES[0]` (49.8, 32.6) → (50.4, 31.6), the nearest flat grove place where every member is 2,000 or more
   from the landing, the step in from it and the rope's foot (4.8 cells from the trunk). Regenerated into scratch: the
   pack, and about 20 dark-grove trees that keep a clearing round it, move; nothing else. Build: d85 FF 0 (nearest
   2,328), check_reach 0, town_fit 0, faces as installed (28), gen.py's own D-85 guard passes.
6. **D2's fairy caps: the design is plain, no decider.** The approved L1 plan: "A ring of tall glowing mushrooms";
   gen.py's own line: "tall glowing caps". The caps were 64-high sprites. New Xeen decoration row 4069 `xeen_fairycap`
   (sprite 27069 stub, `worlds/xeen/models/decorations.yml`: MM6's cap model at 200 ±15 %, light radius 384 pale
   green), `d2/gen.py` places it for the nine caps. Scratch D2: only the nine caps differ; town_fit 0, faces 0; the
   ring reads clearly from 1.8 cells (`shots/d2_caps_after.png`).

**What changes on each map's next rebuild** (scratch builds of the current L4s against the installed maps):
- X1: `mine_portal`, `orc_cave_mouth` shells; road warnings ×2.
- X2: `ogre_lair` shell; warning ×1. (Stalls unchanged: their floor is 1,024 now.)
- X3: `tomb` shell. X4: `xd26_eyrie` shell, check_faces 34 (installed 40); warnings ×2.
- X5: `xd10_north`, `xd10_south`, `warren` shells (one land node under xd10_south's shell +96); `acme_machine` on its
  platform at its said 1,016 (was 1,024). X6: `werewolf_den`. X7: `miner_adit`, `orc_den`, `sablewing_cave`,
  `xd16_mouth`, `xd17_cleft`, `xd18_mouth`.
- D1: Lyle's bench on the square's paving at 1,158 (was 1,152, 6 under the paving's top); **with the gen.py change**
  the electrapede pack and ~20 dark-grove trees. D2: the fairy caps (gen.py). D3: nothing; warnings ×4. D4:
  `dd23_lair` shell, `square_bench_1/2` and `stocks` (on the paving at their said floor); warning ×1. D5: nothing.
  D6: `dd10c_adit` shell, `np_book_1–3` (on a platform at their said floor); warnings ×2.
Every scratch build: town_fit 0; check_faces equal to or below the installed; audits equal but X5's coplanar line.

**REQUESTS.** Orchestrator: D1 (`d1/gen.py` ready) and D2 (`d2/gen.py` + the new decoration row) need one rebuild
each with bake. S: the new row 4069 `xeen_fairycap` in `worlds/xeen/models/` (a glow on the cap's texture would read
by day; today only its light). Map owners: the road-bed warnings above.
- D2's new fairy caps (row 4069) glow only through their light, so the ring reads at night but not by day. A glowing
  (emissive) cap texture so it reads by day too: do it, or leave it?

### D1 and D2 rebuilt with the studio round 4 changes (agent `xeen-fb3-d1d2`, 2026-11-24 ~18:15–18:45; for A6, A3)

Scratch `output/xeen_fb/p3_d1d2/` (`tools/cycle.sh` regen + validate + build after a brief `cpp_build.lock`,
`tools/install_check.sh` gen_walk + A6's `a6_install_baked.sh` + checks + gen_daily + playtests, `tools/sites.py`
tours, `tools/sq.sh`). oymap of 18:12:58 (whole: the lock was free). Each map once: `regen.py` (classic kit,
`fit_maps`), build, `gen_walk.py` on the build, installed with its bake under the map's lock, terrain weights (same
bytes: no land change).
- **D1:** the regen changed only the Electrapede pack (group 3, (49.8, 32.6) → (50.4, 31.6)) and the dark grove's
  tree circles round it. D-85 (`common/d85.py`): **FF 0** (`entrance:d7_rope` nearest 2,328; was 1,734), DIS 0;
  `x2/check_d85.py` lists only the three D-87 kept givers 4951/4953/4956 (5,527–5,803). The D-85 band lines (no
  disabler) unchanged. Capture from the rope landing: `xeen_d1/01-rope_landing_to_pack.png` (the pack in its clearing,
  far through the trees).
- **D2:** the regen changed only the nine caps to `xeen_fairycap` (row 4069). Captures by day (12:00) and night
  (23:30): `xeen_d2/01–04-fairy_ring_*.png`: the caps stand tall and read from 1.8 cells; by night the pale green
  light lights the ring's grass; the caps themselves do not glow (studio round 4's S request stands).
  `common/d85.py` on D2: FF 18, **the same 18 on HEAD's scene** (not from this run): Q-D11's ogre camps (groups 1, 2)
  972–1,691 from `entrance:dd13_west`/`dd13_east` (the fort gates' exits) and spawn markers 23 and 30 at 1,717/1,824
  from `dd11a_hole`/`dd11c_hole`. For A6 / the decider: the camps stand at the forts by design (Q-D11); kept, moved,
  or the arrivals set further out?

**Checks (installed).** D1 / D2: town_fit 0 / 0, check_reach 0 / 0, door 0 / 0, wall 0 / 0, check_wild 0 / 0,
check_faces 28 (the F31 list, unchanged) / 0, audit errors 1 (`feature_repeated` xvswin, the classic kit's, c7's
request) / 0, actor heights 0, key_npcs rewritten, `stale_bakes --check` 0.
**Tests (`build/game/openyamm`).** D1 playtest, hostility, daily (`gen_daily.py d1 d2` rerun: no change): pass. D2
playtest, hostility, daily, graalg_parley: pass. Side quests: Q-D11 (forts, peace), Q-D2, Q-D13 (both), Q-D5: 6 of 6.
Promotions 47, 49, 63: pass (STALE from checkpoints older than the rebuild: c7's chain rerun from 01 refreshes them).
Story chain not run (c7's).
- D2's 18 first-fight findings under D-133 (the same on HEAD's D2, so older than this run): Q-D11's ogre camps
  (groups 1, 2) 927–1,691 from the DD-13 fort gates' exits (`entrance:dd13_west`, `dd13_east`), and spawn markers 23
  and 30, 1,717 and 1,824 from the DD-11A and DD-11C holes. The camps stand at the forts by design: keep, move, or set
  the arrivals further out? Not blocking 3.3.

### The spawn-marker and ledge-check batch: D-132, D-133 (agent `xeen-fb3-checks`, 2026-11-24 ~17:20–17:50; for A7, A6, A5, tools)

Scratch `output/xeen_fb/p3_checks/` (`hide3.py`: the Darkside `hide.py` counting BLV markers, a 96 margin round the new
spot; `ledge_try.py`: the nearest post of a shooter in its room with no thin shot; `sb.sh`/`iq.sh`/`mkroot.sh` as the
follow-up round's; logs `q/`, sweeps `arrivals_*.txt`, `ledge_*.txt`, `d85*.txt`).

**D-132, `tools/xeen/check_ledge_shots.py`.** Open-air maps (`check_arrivals.OPEN_AIR`: D7, P1–P4, X8) skipped. Shooters
are the ranged hostiles (placed, BLV markers, scene spawns), each from its own post and from the spots it can move to:
walkable faces within its `leash_radius` (else 1,024 of its post, 2D) in its post's walk component (floor faces joined
by overlapping edges with a rise of at most 56, the engine's 50 step), still 64 below the lip and 256–3,000 beyond it.
`ledge.thin_shot` (error, exit 1): from a post; `ledge.thin_shot_move` (warning): only from a spot it can move to.
World, after this batch's installs (`ledge_after.txt`): **16 errors on 6 maps**, 51 warnings on 12 (was 381 warnings on
23 maps). Errors, for each map's next rebuild (move the shooter first, a 64 parapet, else KEPT):
- DD-07 (8 lips, the tower's three galleries at z 720/1360/1920–2000 over the shaft): Floating Adepts actor 27
  (-256, -192, 0), 28 (0, 256, 0), 29 (0, -256, 0) under the gallery lips (flyers in a shaft; a KEPT candidate).
- DD-19 (2): Wizard actor 0 (-4608, 1920, -512) at the lip x -4096; Enchantress actor 14 (1536, 1664, 0) at y 1840.
- DD-21 (1): Greater Lich actor 6 (-1152, -4064, -896) under the lip y -3968, z -512.
- FD-04 (1): Autobots actors 29, 30 (±800, 11300, -2560) under the lip y 11968, z -1888.
- XD-12 (2): marker 15 (slot 6) at (-2496, 0, 1536) under the lip x -2624, z 1952–1984.
- XD-22 (2): Ninja actor 13 (-1200, -500, 0) under the lips x -656/-674, z 512.
XD-05's (spawn `hall_w`) and XD-11's (library Sorceress) errors were fixed in their rebuilds below.

**D-133, `tools/xeen/check_arrivals.py`.** `--spawns` removed: the BLV's markers and the scene's spawns always count, by
any row their slot can roll, with the widest notice range of those rows (`marker_range`). World before: **7 errors**,
the five named plus **XD-11** (two foyer markers seen from the party start) and **XD-15** (the paw hall's three Sand
Golems seen from the party start, placed actors, left since the Cloudside round). Fixed by the Darkside method (in their
room, out of sight with a 96 margin), one rebuild each through the generator (hand L4 for XD-02/04/05), checked on a
scratch root first, installed, baked:
- XD-02 (L4 `objects.yml`): `spawn:deep_station` (4300, 4700) → (4620, 3932), `deep_station_bay` (4150, 3550) →
  (4534, 3678), `ledge_sse` (6575, 1993) → (6447, 1929) (all three saw the XD-03 arrival; now `arrival.near`, a warning).
- XD-04 (L4): `spawn:steam` (550, 550) → (678, 550).
- XD-05 (L4): `spawn:step_e` (760, 2048) → (888, 1984); `spawn:hall_w` (-1000, 9344) → (-936, 9088) (D-132 error).
- XD-08 (`gen.py`): spawn `welcome` (256, 1664) → (512, 1472).
- XD-11 (`dress.py`): foyer spawns (-1600, -512) → (-1920, -704), (-640, 512) → (-576, 320); library Sorceress
  (-384, 832) → (-512, 832) (D-132 error).
- XD-15 (`gen.py` `PLACED`): Sand Golems (-256, 1440), (256, 1440), (0, 1824) → the aisles outside the columns
  (-960, 1440) facing east, (960, 1440) west, (-960, 1888) east (clear of the braziers at ±640).
- XD-26 (`gen.py`): `spawn:shaft_e` (1500, 300) → (1756, 172).
All seven: audit 0 errors, `check_exits` 0, `check_open_sky` 0, `check_identity` ok, `check_door_leaves` ok,
`check_arrivals` 0 errors, `xeen_pack_reserve` ok; `check_drops` only the known XD-05 prisoner pit and XD-15 drop cell.
Playtests: XD-02 3/3, XD-04 3/3, XD-05 4/4, XD-08 3/3, XD-11 5/5, XD-15 4/4, XD-26 4/4. World: **`check_arrivals --all`
0 errors** (56 warnings); `stale_bakes --check` 0; `xeen_balance.py --check` ok; `key_npcs --write`;
`check_actor_heights` 0; `balance.py` as before (XD-19 1.46, DD-04 0.37, DD-10/11 0.75 off; no count changed).
`xd02_gate_reopens_on_party.yml` **passes** on `build/game/openyamm` of 17:17 (after the XD-02 install). Story, side
quests, promotions: not run here (c7's full chain; the orchestrator runs the two focused scenarios).

**Outdoor arrival checkers.** Both already counted scene spawns for D-85/D-87 (5,120/5,888, disablers); what was
missing was D-15's 2,000 first-fight buffer, which nothing measured with spawns (the D5 Roc 1,312 from `d7_fall`).
New `first_fight()` in `check_arrivals.py` (placed hostiles and scene spawns that move or shoot within 2,000 2D, less
the marker's radius; no line test); `x2/check_d85.py` makes each an ERROR (exit 1; `--kept-group` keeps a group),
`common/d85.py` lists them as `FF`. Findings on the 13 outdoor maps (`x2/check_d85.py`, which also reads Lua landings):
- X1, X3, D5: none (D5's Roc already moved by c7).
- X2 (7): north start/`entrance:north_road` spawn 31 (slot 2) at 1,997; `entrance:xd27_lair` and its Lua landing:
  Ogre Brutes 36–38 (group 62) 475–1,367.
- X4 (1): XD-26's Lua landing (-7424, 14592): spawn 4 (slot 3) at 1,888.
- X5 (10): Winterkill's start/mirror/portal: the Spirit Bones of group 40 (Q-C6's first wave, D-13) 597–1,988.
- X6 (2): `entrance:xd14_gate` and its landing: spawn 20 (slot 2) 1,921–1,946.
- X7 (1): `entrance:xd18_mouth`: spawn 14 (slot 2) at 1,843.
- D1 (1): `entrance:d7_rope`: Electrapede actor 12 (group 3) at 1,734.
- D2 (18): DD-13's fort gates: the ogre camps (groups 1, 2) 927–1,691; DD-11A/DD-11C holes: spawns 23, 30 at 1,717, 1,824.
- D3 (1): `entrance:dd07_door`: spawn 18 (slot 1) at 898.
- D4 (1): `entrance:dd20_guild`: Druid actor 30 (group 47) at 1,227.
- D6 (2): `entrance:dd17_gate`/`fd01_stair`: Patrols 40 (group 18) and 43 (group 19) at 1,894, 1,903.
Fixes for the owners: move each spawn past 2,000 (most are 100–300 short), or the camp/guard groups back from the
landing, or keep the group with `--kept-group` and a decision (X2 62, X5 40, D2 1/2, D6 18/19). The checker is the
build gate of X1, X3, X4, X6, X7, D3 (`vw.sh`/`rb.sh`): X4, X6, X7, D3 now fail it until moved.
**X5's six `common/d85.py` FAILs** are not new: the same on HEAD's (3.2) X5 scene. Mayor Randon 456 from the Spirit
Bones (D-13, kept by a decider, NOTES), Winterkill's start 544 from them (Q-C6's wave on purpose), and four arrivals
within 5,120 of melee-only markers (east road 4,663, north road 2,159, XD-09 door 2,355, XD-10 north 3,931): D-87.4
makes melee kinds information only; common/d85.py prints them FAIL.

**DECIDE.** (1) Dungeon-mouth and fort-gate arrivals with a guard group in the 2,000 (X2's XD-27 ogres, D2's DD-13
camps, D6's patrols, D4's druid, X5's Winterkill wave): D-15 names edge arrivals and a new game's start; D-133 holds
every arrival by analogy. Built: every arrival an error (the stricter; `--kept-group` undoes it per map). (2) DD-07's
Floating Adepts under the tower galleries: flyers in a shaft, as the open-air maps; KEPT or moved?

**NEXT.** The six maps' ledge errors at their next rebuilds; the outdoor first-fight list at each outdoor map's next
rebuild (X4, X6, X7, D3 before their next `vw.sh` passes); c7's story chain, promotions and side quests over XD-02,
XD-04 (09, x8-sky), XD-05 (11, x1-tam), XD-08 (27), XD-11 (35), XD-15 (q-c8/q-c9), XD-26 (promotion 11, q-c10).

### After 3.3 (orchestrator): open work from D-134 to D-138

- S: the toad's tongue tip (D-134).
- tools: `check_ledge_shots.py` flying shooters → warnings (D-137); `--kept-group` records for D2 groups 1, 2 and X5
  group 40 (D-136).
- A5 (next rebuilds): X4 spawn 4 (recheck), X6 spawn 20, X7 spawn 14, D3 spawn 18 (D-138). A6: D2 spawns 23, 30, D6
  groups 18, 19, D4 Druid 30 (D-136, D-138); a ranged member of D2's fort camps moves.
- A7: the D-132 ledge errors (DD-19, DD-21, FD-04, XD-12, XD-22) at their next rebuilds; DD-07's gallery capture (D-137).

### Hull collision rebuild, Cloudside and Darkside: X1, X2, X3, X5, D1, D2, D3, D4 (agent `xeen-fb3-hull`, 2026-11-24 ~19:50–20:50; for A5, A6, tools)

Scratch `output/xeen_fb/p3_hull/` (`tools/cycle.sh` regen + validate + build, `install_check.sh` gen_walk + install
with bake + checks + playtests, `queue.sh`, `spot.py` (terrain sight lines and spots past 2,000), the pinned
`bin/oymap_1944` and `tools/a5_install_pinned.sh`/`a6_install_pinned.sh`: the lanes' install scripts with only that
binary and the repository path changed). Every map once: `regen.py` (classic kit, `fit_maps`; all eight reproduced
before the edits), built **with the orchestrator's pinned 19:44 oymap** (`oymap_1944`, the hull's `collision: model`,
without the 19:54 uncommitted proxy edits), `gen_walk.py` rerun on the build, installed with its bake (A6's script for
X5, D1, D2, D4; A5's under `bake.lock` for X1-X3, D3), terrain weights. Installed: X5 20:18:34, D2 20:16:49, D3
20:31:23, X1 20:35:04, D4 20:37:30, X2 20:39:16, D1 20:42:06, X3 20:43:08.

**Decisions applied.**
- D-138, D2: `pop:trolls` 1 (58, 79) → (56, 80.5), 4 (63, 96) → (61.5, 95.5), 3 (72, 89) → (72, 89.5) (its circle's
  edge was 1,989 from DD-11B's spot). Built spawn 23 3,524 from DD-11A's return spot, spawn 30 3,334 from DD-11C's.
  `d2/gen.py` refuses any marker circle within 2,000 of a hole's return spot (D-25's 512, trolls only, before). No
  line-of-sight cover is possible there: the troll plain is flat (900-1,000), nothing short of the trolls' 5,120 notice
  range is hidden by land, so they stand at the nearest spots past 2,000 still facing the holes.
- D-138, D3: `d3/gen.py clear_arrivals()`: a marker within 2,000 of a door arrival (`DOOR_ARRIVALS`: DD-07's door,
  the D7 fall) moves to the nearest free candidate past it that the land hides from the arrival (64 of cover, the
  circle's middle and edges); the others keep their places. Wrath hills marker 8 (spawn 18) (93, 45) → (90, 41): built
  at (13184, 12096), 3,610 from the door, hidden by the built land (51).
- D-136, D2: groups 1, 2 kept (no member shoots or casts: Ogre, Ogre Brute, Ogre Chief; nothing moved); `d2/v.sh`
  runs `check_d85.py --kept-group 1 --kept-group 2`, NOTES line. X5: group 40 kept; `x5/v.sh` runs `check_d85.py
  ... 5120 --kept-group 40` and fails on every ERROR but Randon's D-87.1 giver line; NOTES line.
- D-136, D4 "Druid 30": **not moved**. It is a Lakeside villager (D-96, row 517, group 47): the map's load event
  makes rows 349/364/517/598 friendly and clears group 47's hostile bit, so it neither fights nor casts. The finding
  was the checker reading only the world's relations: `tools/xeen/check_arrivals.py` `World.map_friendly()` leaves out
  placed actors whose row the map's own onLoad Lua makes friendly (`check_arrivals --all` still 0 errors, 56 warnings).

**Checks (installed, all eight).** town_fit 0, check_reach 0, door 0, wall 0, check_wild 0, key_npcs rewritten, actor
heights 0, `stale_bakes --check` 0. check_faces: X1, X2, X3, X5, D2 0; D1 28 (the F31 list), D3 5, D4 1 (as before).
D-85 (`x2/check_d85.py`): 0 errors on X1, X2 (`--kept-group 63`), X3, D1 (5,120), D2 (16 KEPT lines of groups 1, 2),
D3, D4; X5 1 (Randon, D-87.1; 10 KEPT lines of group 40). `common/d85.py` FF: 0 apart from the kept groups. Audit:
besides the classic kit's `textures.feature_repeated` (c7's request: X1 6, X2 17, X3 6, X5 3, D1 1, D3 8, D4 1), only
**`void.occupied` on every hull piece's `collision:thing:hull_*` copy** (the audit's void rule does not know the new
proxies; the orchestrator asked c7 to fix the rule; no map change). `towns.py --strict`: no error on these maps (X1's
villager 13 gone with the rebuild).

**Tests (`build/game/openyamm` of 20:05).** Every playtest of the eight maps passes: X1 walk, hostility; X2 walk,
hostility, danulf_ring, lake_dragons, lake_dragons_leash; X3 walk, hostility; X5 walk, hostility, randon; D1 walk,
hostility, daily; D2 walk, hostility, daily, graalg_parley; D3 walk, hostility, d7_fall; D4 walk, hostility, daily
(`gen_daily.py` rerun on D1, D2, D4). Hull edges, new: `tests/scenarios/xeen/
x1_hull_edge.yml` (east rim, the party stops at x 20,784, the land ends at 20,992) and `d1_hull_edge.yml` (west rim,
stops at -20,784): pass. Story chain, side quests and promotions not run (after all 13 maps).

**DECIDE.** D4's Druid 30: kept as a peaceful villager with the checker fixed (above), against D-136's "moved". If the
decider wants no shooting row of any kind near a door arrival even when friendly, `villagers.yml` Lakeside gets an
`avoid` round the guild's arrival and `villagers.py --place D4` at D4's next rebuild.
**NEXT.** c7's audit rule for `collision:` proxies; the classic kit's `feature_repeated` on the eight maps.

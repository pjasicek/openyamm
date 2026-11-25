# A player's pins, 2026-11-24 12:43 to 2026-11-25 00:42 (Xeen v3.2/3.3, X1, X2, X4, X5, X6, X8 and eight dungeons)

The same player as [PLAYER_FEEDBACK_20261124.md](PLAYER_FEEDBACK_20261124.md) sent a third archive
(`pins_inbox_yamm_2.7z`, 65 pins, all new): X1 4, X2 2, X4 12, X5 13, X6 13, X8 9, XD-04 1, XD-07 1, XD-10 1,
XD-13 1, XD-14 5, XD-23 1, XD-25 1, XD-26 1. 3.3 was tagged at 2026-11-24 21:56, so pins up to X1 p31 (20:52) and
X8 p9 (21:18) were made on 3.2 and can show what 3.3 already fixed. The pins from 22:20 on (XD-13, X5, XD-10, XD-23,
X4 p12) may be on either version: the pin files do not record it.

- Pins are filed in the map projects: `devdocs/xeen/briefs/<map>/L4/review/pins.yml` (ids below; X1 p28–p31, X2
  p11–p12, X4 p1–p12, X5 p1–p13, X6 p1–p13, X8 p1–p9, XD-04 p5, XD-07 p1, XD-10 p1, XD-13 p1, XD-14 p1–p5, XD-23
  p1, XD-25 p1, XD-26 p1). Use `oymap pins list|claim|tour|resolve` (openyamm-studio/README.md, "Pins from the game").
- Pictures: `output/xeen_fb/p4_20261125/original/<stamp>-<map>.png` (with the pin YAMLs), and
  `<project>/.oymap/pins/pictures/`.

**The rule (the user's, 2026-11-21):** every family is fixed at its source (generator, shared kit, engine, common Lua,
data), then on **every** site of its kind in the Xeen world, with a check that keeps it fixed. The pinned spot is only
the example. See [briefs/FEEDBACK_FIX_RULES.md](../briefs/FEEDBACK_FIX_RULES.md).

## Probably fixed by 3.3 already (confirm with a capture at the pin's pose)

| Pin | Text | Fixed by |
| --- | --- | --- |
| X4 p9 [-20161.4, 4635.5, 1345.0] yaw 4.249 | "campfire gives you rings and food" | 3.3 (commit ab4bb65858): the campfire event is `once: true`; `check_wild.py` flags one without it. Confirm the fire gives them once only |
| X1 p31 [-10370.0, 4333.9, 641.0] yaw 4.564 | "Vertigo has always the same Spell books" (the Guild of Vertigo's shelf) | Maybe D-129 (3.3: a paid New stock rolls a new shelf each time). If the guild's shelf never rerolls by design (a guild sells its fixed spells), say so in a reply; else F52's fix has not reached guilds |

## The new pins, grouped into families

Poses are `position [x, y, z]`, `yaw` radians, from the pin files. "Agent" is the run that takes the family. "TB" means
the picture shows the turn-based combat bar (Attack, Pass).

| F | Family | Pin(s), map, pose, what the picture shows | Agent |
| --- | --- | --- | --- |
| F58 | **Flicker at ruin and wall footings, the hull's top** | X2 p11 "z-fighting" [18723.9, 14646.3, 1089.0] yaw 4.313: a flagstone strip in the inside corner of the Ruined watchtower's walls. X4 p2 "z-fighting" [20578.8, 16490.3, 2177.0] yaw 1.954, X6 p2 "z-fighting" [7257.8, -6858.6, 1505.0] yaw 4.826 (the ruined caravanserai), X6 p12 "z-fighting" [20480.0, 12703.2, 1537.0] yaw 0.293, X5 p5 "z-fighting" [-19435.6, 11854.9, 1023.7] yaw 3.981: the same grey or brown strip on the ground where two ruin walls meet, seen from above. X1 p29 "z-fighting" [20717.3, -20708.3, 1025.0] yaw 5.464: the world's hull from its top, slabs meeting at a stepped corner with a grille (3.2's hull; the hull was rebuilt for 3.3). XD-13 p1 "z-fighting" [1081.5, 3336.1, 288.1] yaw 4.723: a flat white face beside a stone pillar (more like a missing or untextured face than flicker; see F60) | outdoor (a shared ruin kit), dungeon (XD-13) |
| F59 | **Things on slopes: floating, half-buried, uneven** | X1 p28 "stone flying" [-421.2, 18429.4, 1708.0] yaw 1.291: a boulder hanging off a slope over its shadow. X4 p5 "the fountain needs a even ground" [6647.7, 8168.0, 655.1] yaw 3.077: the Olympian Fountain's base in the air on the downhill side. X6 p6 "move the fountain to a more even ground" [-9942.4, 1089.1, 993.0] yaw 0.653: the oasis fountain, the same. X4 p7 "pile needs a more even ground" [-9580.7, 11191.9, 1797.7] yaw 2.354: a skull pile on a steep slope. X6 p11 "one part needs mor ground" [13865.7, 16295.5, 1755.1] yaw 0.456: a half-buried wagon, one end in the air. X5 p6 "maybe put the tree to a more even ground" [3760.3, -3253.0, 769.0] yaw 0.054: the face tree. X5 p3 "Freedas tent can fly" [9454.7, 9666.6, 1644.5] yaw 0.845: Freeda's tent off a hillside. X5 p8 "both tents need a even ground" [-11448.6, -15929.1, 2256.1] yaw 0.623, p9 "or make this even" [-10906.0, -15082.7, 2258.3] yaw 5.899: the troll camp's tents and fence on a slope | outdoor |
| F60 | **Missing walls, untextured and see-through faces** | XD-14 p3 "wall is missing" [2779.0, 1974.0, 1280.0] yaw 1.395, p4 "missing wall" [2341.0, 810.3, 1280.0] yaw 4.542: a blue void slot between two walls (Castle Basenji, upper floor). X5 p10 "missing texture" [783.8, -13735.7, 1164.1] yaw 4.604: a cave-mouth mound in plain brown (as F50's Tomb entrance; 3.3's "cave mouth shells" may have fixed it). X5 p4 "there is something missing" [23062.3, -18857.2, 986.0] yaw 5.059: a snow ridge runs up to the hull and the gap beside it is open. X4 p6 "z-fighting i guess?" [3115.6, 3235.9, 1297.3] yaw 2.981: Burlock's village wall with a black wedge-shaped hole in it. X4 p8 "you can see through" [-8199.8, 13563.8, 3070.5] yaw 0.992: high on a hill looking at a low wall; what is see-through needs a capture. XD-13 p1 (F58) | dungeon (XD-13, XD-14), outdoor |
| F61 | **The Sphinxes: the party walks into them, doors stick out** | X6 p7 "you can clip through" [8813.4, 9993.5, 1409.0] yaw 1.605, p8 "here the same" [9599.2, 10142.5, 1409.0] yaw 1.539, p10 "here too" [9033.3, 16493.4, 1409.0] yaw 4.737: the party stands inside The Sphinx's model (paws, sides). p9 "the entrance is clipping through both side" [8908.2, 9757.1, 1409.0] yaw 1.478: the door panel cuts through the model's sides. p13 "sorry to say this, the door sticks out" [-11687.3, -10275.1, 1574.5] yaw 3.129: The Southern Sphinx's door stands proud of the body. This is a player asking for a solid model, which D-140 (only the hull is solid in 3.3) said no report did | outdoor; decider (D-140) |
| F62 | **X8 Cloudreach: bridges, towers, a stuck spot** | p1 [11431.0, -7168.4, 0] yaw 3.245, p4 [5113.4, -663.2, 128] yaw 3.063, p5 [-9786.2, -4457.0, 0] yaw 4.801, p7 [-7246.6, 1189.8, 256] yaw 3.501, p9 [12879.5, 11394.7, 834.0] yaw 0.642, all "bridge is clipping": plank bridges sink through the cloud floor, and their ends cut into the islands. p3 "is it intended that you can't go back to the tower?" [11500.1, -7048.0, 0] yaw 4.723, p6 "cannot go to this tower" [-10743.9, -4703.1, 0] yaw 4.741: a path ends short of an island with a tower. p8 "you get stuck here" [-10564.7, 10078.2, 768.0] yaw 1.210: wedged against a sloping cloud face. p2 "2 things, remove the input and make i clickable, and also remove the skulls" [11144.8, -10435.3, -128.0] yaw 3.173: a gold ball and a skull on the cloud before a statue on a plinth; the player wants the typed answer gone (a click instead) and the skulls removed (see xeen-no-riddles: an answer the game gives plainly, or no typing) | dungeon (X8 is a BLV) |
| F63 | **Monsters that stand, hide or get stuck** | X5 p11 "Polter-Fool are not attacking." [-14392.3, 10504.3, 1009.0] yaw 1.295 (TB) and p12 "Ghost-Rider are also not moving" same spot, yaw 1.266 (TB): undead standing in a town square among NPCs. X5 p13 "monster is stuck" [-12844.0, 12438.8, 1009.0] yaw 1.012: one inside "A strange machine" (a box prop). X5 p7 "the trolls are stuck in their tents" [-11515.4, -13113.5, 2349.4] yaw 4.672: a Cyclops against a tent. X6 p4 "the monsters are trapped" [-18068.3, -15224.2, 1488.0] yaw 1.640: at the hull's edge (3.2's hull). XD-14 p1 "monsters can get stuck here" [2475.3, 996.9, 0] yaw 1.121: straw beds with skulls. XD-07 p1 "the fire dragon gets stuck there" [2857.8, -4508.2, -1152.0] yaw 1.376: a narrow brick alcove (XD-07 keeps the Fire Dragon in its pit by design, D-32: check whether this alcove is that pit). XD-04 p5 "i think he is bugged" [-2773.3, -1624.0, 0] yaw 4.266: an orc-bodied figure named "peasant" standing still (map cleared 69/69) | engine (AI, TB), outdoor and dungeon (props on paths) |
| F64 | **Monsters too near the roads** | X6 p1 "i make the pin here for every map. Is it possible to move the monsters more far away from the streets? You load in and get immediately attacked." [21803.3, 2246.8, 1198.3] yaw 4.560 (TB): Great Worms on a road at a map's edge. The player means every outdoor map, not only arrivals (D-138 kept spawns 2,000 from arrivals) | decider, then outdoor |
| F65 | **Hard to click** | XD-26 p1 "make the nest more clickable, first i thought there is a bug" [1285.9, 2873.7, 2048.0] yaw 1.582: a small blue scarab in the middle of a wide platform, the Great nest. XD-25 p1 "it is a bit hard to click on them and get the crystal" [423.5, -1743.3, -640.0] yaw 1.689: Crystals on a chest. XD-23 p1 "i had problem to click on this" [1980.1, -5854.2, -1024.0] yaw 0.111: a low hexagonal stone dais. X4 p10 "let it burn when you click on it" [-19559.5, 4924.8, 1345.0] yaw 2.009 (a minute after X4 p9, by a Barbarian tent): probably the campfire, which should keep burning after its click. X8 p2 (F62) | engine (picking), dungeon |
| F66 | **Props in props, the party under ramps, tall tables** | X6 p3 "barrels are clipping" [11732.9, -14336.1, 1505.0] yaw 4.773: two barrels (Purple Barrel +2 Speed) through a tent's plank wall (as F40). X4 p11 "i crawl under the ramp" [-1306.7, 6511.7, 1313.0] yaw 5.282: the party under a stone ramp's open underside. XD-14 p5 "maybe make these table shorter, i know you can jump" [-529.1, 390.9, 0] yaw 3.122: long low wooden tables block the way | outdoor, dungeon |
| F67 | **Town and shore layout** | X4 p12 "move the house to the street" [-9115.4, -10815.3, 1057.0] yaw 5.112: The Potter's stands off the road. X4 p1 "maybe move the bridge a bit more left" [11302.0, -6720.1, 840.1] yaw 2.895: the bridge's end lands beside the road. X2 p12 "make the pier a little deeper" [8831.3, 4699.1, 577.0] yaw 2.887: Captain Nystor's pier stands over the beach, not the water. X4 p3 "i guess it has to be like this, but it looks strange" [11599.5, 11106.3, 1154.4] yaw 2.526, p4 "the complete thing looks strange" [9051.3, 9124.4, 641.0] yaw 1.704: a weir across the river: plain dark blue slabs, two rock spurs, a waterfall strip | outdoor |
| F68 | **Services, music, alchemy, travel** | X5 p1 "blessing is not working" [3194.1, 17397.0, 1889.0] yaw 0.505: Brother Lin, Hall of Stillness, "Donate 30 gold". X5 p2 "music in winterkill is the old one" [2780.4, 14478.9, 1889.0] yaw 5.474. XD-14 p2 "the other black potion are not in the category grandmaster" [-2437.3, 769.5, 0] yaw 2.039: the recipe list puts Pure Elemental Resistance, Divine Blessing, Darkness, Twilight, Dawn and others above the GRANDMASTER heading, only Pure Self Resistance and Divine Resistance below it. X1 p30 "if you can take the boat to Vertigo, why couldn't you take the boat back?" [-7625.3, 4842.2, 611.7] yaw 0.135: Vertigo's quay. X1 p31 (above) | engine, data |
| F69 | **Balance** | XD-10 p1 "3 gems for +3 is not a good exchange" [851.9, 6440.9, -640.0] yaw 1.879: the skull pile between two skulls on plinths (as F55's skull shelf). X6 p5 "maybe remove the question" [-18465.7, 4463.6, 1432.0] yaw 1.572: a glowing orb on a pedestal under a canopy, a Greater Werewolf beyond (TB); the choice dialogue for a simple thing, as F47 | decider, then dungeon (XD-10), outdoor (X6) |

Agents: **dungeon** (F58 XD-13, F60 XD-13/XD-14, F62 X8, F63 XD-04/XD-07/XD-14 props, F65 indoors, F66 XD-14, F69
XD-10), **engine** (F63 AI and turn-based, F65 picking, F68), **outdoor** (F58, F59, F60 outdoors, F61, F63 outdoor
props, F64 after the decider, F66 X4/X6, F67, F69 X6; with c7's classic-kit and hull work, since both change the
outdoor generators). **Decider** first: F61 against D-140, F64 (how far from roads, every map), F69, F62 p2.

## Results

### Round summary (orchestrator, 2026-11-25 ~12:00)

All 65 pins resolved (`oymap pins list <project>`). Decisions D-141–D-164 (D-163 amended by the user: MM9's child bodies, new
skins allowed). Built and installed this round: X1, X2, X3, X4, X5, X6, X7, D1, D2, D3, D5, D6, X8, X9, D7, P1–P5,
XD-02, XD-04, XD-07, XD-10, XD-11, XD-12, XD-13, XD-14, XD-17, XD-19, XD-22, XD-23, XD-25, XD-26, DD-05, DD-07, DD-13,
DD-23, FD-01. Engine: indoor round-collider slide (`IndoorCollisionPrimitives.cpp`), picks through eventless
decorations and hover names within click reach (D-153). Studio: ruin course, actors on structures, clicked tops,
outward ramp faces (also changes mm6_outd3, mm7_7out03, mm6_oute3, mm8_out02, mm8_out06 at their next build). End
checks 0: build_world, quests, quest_stub 19/19, sky falls, stale bakes, wiring, towns --strict, xeen_balance.

Open after the round: bridge/jetty end faces on the land (`BRIDGE_SINK = 32`, then X2, D2, D3), 18 other on-land
faces, D7's coplanar warning, ledge shots on DD-19, DD-21, FD-04, XD-22, the boy's sulk (a head texture), the new
player text for translation (X8's stair refusals, the sundial line, the boy's topic, Nystor's landings), the
playthrough chain's stale checkpoints (a rerun before release), `x2_lake_dragon_leash.yml` in tests/scenarios (refresh
from the L4 copy).

### F62 X8, F60 indoors (part), D-145, D-146 (agent `xeen-fb4-dungeon`, 2026-11-25; for A6, A7; stopped at the token budget)

Before captures at every pin of the dungeon share: `output/xeen_fb/p4_dungeon/before/<map>/` (tours and `mktours.py`,
`runtours.sh`, `pt.sh` beside them); after: `after/xeen_x8/`. New checks: `tools/xeen/check_floor_cross.py`,
`tools/xeen/check_parapet_gaps.py`.

**F62, X8 Cloudreach (done, installed; X8 has no bake).**
- *Bridges cut into the islands (p1, p4, p5, p7, p9).* Cause: `x8/gen.py` laid each deck from 160 inside one island
  (8 over its cloud) to 160 inside the other in one straight slope, plus a 160 sag on long bridges. Wherever the far
  island is higher, the near one lower, or the deck sags, the deck dropped under the cloud top before the rim and came
  out over the void: cloud drawn over the planks, the deck's end apparently cut into the island. Fix: each link is now
  a level landing on each island out to where the island ends under the deck's whole width (`landing_end`, the rim is
  crooked), and slopes or sags only over the void. Sites: all 13 links (11 crossings found, every one of the five pins
  among them); 0 after. Check: `check_floor_cross.py` `floor.cross` (two floors of normal z 0.9+ whose heights cross
  where they overlap).
- *Stuck at a cloud lump (p8).* Cause: X8's blocks all hang from the room's floor at -6,000, so the studio draws their
  undersides; each set piece's underside lay exactly on the cloud top, a ceiling at the party's feet at the block's
  foot. Fix: every block on an island or on another block is sunk 8 into it (`SINK`). Sites: 27 (cloud lumps, spires,
  eyrie rocks, nests, plinths, tiers, the observatory's porch, telescope and domes); 0 after. Check:
  `check_floor_cross.py` `floor.lid` (a face looking down within 2 of a floor, under a block the party can step or
  climb onto).
- *No way back to the tower (p3, p6).* The arrival stairs ran down into the sky; the only way off was the fall. Now the
  stair of cloud the party came up (`xwcloudst`, XD-04's picture) stands at each stair's foot, clicked: back to the
  Witch Tower's roof (XD-04, (-6784, 448, 2560) facing east) or the Tower of High Magic's roof (XD-11, (1536, 1152,
  2560) facing south), the exit window's OK/Close; it also stops a walk off the last step. A step trigger on the last
  step was tried first and never fired on this open-air map (no event from the pressure plate; not chased further).
  `playtest_down.yml`, `playtest_down_west.yml` (new) pass. Open: `check_arrivals.py` gives `arrival.hot` for the XD-11
  roof landing (XD-11's roof spawn marker `spawn:roof_1` at (0, -512) sees it; the stairway below sees the library's
  Sorceresses): move that marker out of sight at XD-11's next rebuild. DECIDE (cheaper to reverse taken): X8's notes
  and XD-04's neighbour said "one way up, no way back down but falling".
- *D-145 (p2).* `evt:nest_{k}` also hides `deco:n{k}_bones` and `deco:n{k}_skull` (both inside the nest's 384 square);
  the main playtest asserts them hidden (`sprite_hidden`). Replied on p2.
- Runs: `oymap audit` 0 errors; playtests 7 of 7 (main 145 steps, three falls, hostility, the two stairs down) from a
  private root, then installed; `key_npcs.py --write` unchanged, `check_actor_heights.py` clean.
- **Other open-air maps (not rebuilt, NEXT):** `check_floor_cross.py --all`: crossings D7 22, P1 25, P2 28, P3 6, P4
  1, P5 11, X9 27 (bridge or ramp decks through clouds: D7 12, P2 4, P5 1, X9 17; the rest cloud tops crossing cloud
  tops); lids D7 397, P1 16, P2 30, P3 12, P4 11, P5 24, X9 38; and lids under walkable blocks on 22 dungeons (stacked
  blocks such as beds on daises; most need a look, not all are stuck spots). X9, D7 and P5 share X8's slab code: the
  same `landing_end`/`SINK` change applies there. Lists: `output/xeen_fb/p4_dungeon/floor_cross_before.txt`.

**F60 XD-14 p3/p4 (source fixed, not rebuilt).** Cause: `xd14/gen.py` `sky_side` ran each sky walk's parapet 32 in
from the sky wall and stopped it 32 short of the side walls, so a slot 32 wide showed the sky from the floor up at
both ends (the battlements, the roof walk, the moon tower). Fix: the parapet runs from side wall to side wall. Same
pattern in `xd19/gen.py` (the four wall walks): fixed the same way. Check: `check_parapet_gaps.py --all`: XD-14 6 gaps,
XD-19 8, XD-22 7 (XD-22's are the railing's turned corner and the rope's slot at the south walk's east end, meant;
the check is naive at corners). **Not rebuilt:** XD-14 and XD-19 need regen, build, install, bake, MAW reserve,
playtests (NEXT). XD-13 p1, F63 (XD-14 p1, XD-07 p1, XD-04 p5), F65 and D-143 (XD-10) not started.

**D-146 (XD-14 p5).** Capture at the pin from today's build: the hall table stands against the back wall, clear of the
door (3.3's shortened tables): fixed; replied on p5. `face.in_doorway` world run not done (NEXT).

**F63 XD-14 p1 (looked at, not fixed).** The pin is the kennels' sunken feeding pit (64 deep, banks of normal z 0.83,
two bone piles on its straw). A headless trial with two Werewolves spawned in the pit and on the floor beside it could
not tell them apart (the party took no damage in either), so the cause is not confirmed.

### F63 (AI), F65 (picking), F68, the 3.3 checks; F58's oymap (agent `xeen-fb4-engine`, 2026-11-25 ~08:00–09:00; for A1, A5, A6, A4, A7, decider)

Scratch and logs: `output/xeen_fb/p4_engine/`. The only builder this round. Released: `openyamm-studio/build-xeen/oymap`
08:35:41 (system clock; F58's ruin course and F63's actor placement), oymap_tests 535/535. Game `build-xeen/game/openyamm`
rebuilt from the tree (no game source changed by this run: a temporary movement trace was added and removed).

**F63, X5 p11/p12 (Polter-Fools and Ghost Riders stand still and never attack). Map Studio, every studio ODM.**
- Cause: the studio set every outdoor actor and spawn point on the land (`groundHeightAt`). Winterkill's square is a
  platform 16 over the land (`thing:square_court`), so 48 ghosts and the townsfolk stood inside it at 992 under its top
  at 1008. Walkers (the Spirit Bones) step up out of it; flyers do not step, and a flyer inside a floor cannot move. A
  movement trace showed `pursue` every frame with the resolved velocity 0 and the position unchanged; the AI, turn-based
  mode, the leash and the relations were not involved (a Polter-Fool spawned in the open, or 100 over the square, came
  and fought). Turn-based play only showed the same standstill.
- Fix (`openyamm-studio/core/OutdoorBuild.cpp`): actors and spawn points stand on a structure's top where one covers the
  land, through `standingPlaceOnModels` as arrivals already did (drawn models only, not decoration collision boxes).
  Sites: X5 35 actors lifted 992 -> 1008 (waves 1-3 and the townsfolk); D4 1 actor (+8); every other Xeen ODM unchanged.
  MM6–MM9 untouched (studio only). Takes effect with each map's next studio build (X5: the outdoor round).
- Check: a build warning "an actor of <monster> (group N) at [x, y] stands inside <model>, which cuts through its body"
  (`modelThroughBody`); regression `tests/scenarios/xeen/x5_winterkill_ghosts_move.yml` (waves 2 and 3 revealed, three
  Polter-Fools and three Ghost Riders must leave their places): fails on the installed X5 (step 23, Polter-Fool 78
  never moves; `f63_regr_assets_dev.log`), passes on a scratch root with the lifted scene (`f63_regr_root.log`).
- The new warning over all 13 Xeen ODMs (scratch builds, `oymap/all_*.log`), placement for the outdoor lane:
  X5 3 Cyclops (group 30) inside `thing:outpost_tent`/`outpost_tent2` (**X5 p7**, "trolls stuck in their tents"),
  X5 1 Ghost Rider (group 42, [-12544, 13005]) inside `thing:acme_machine` (**X5 p13**: x5/gen.py spot (39.2, 38.8),
  wave 3's +0.3/-0.2 shift), X3 1 Elite Ranger (group 61) inside `thing:ranger_tent_2`, X4 1 Barbarian (group 61)
  inside `thing:barbarian_tent_3`. X6 p4 (3.2's hull edge): not this cause; outdoor lane.
- Compared with the 24 Nov F41 result: F41 was data (`immobile: true` guards); this one is placement height, also data
  at the build, so again no AI change.

**F65, hard to click (XD-26 p1, XD-25 p1, XD-23 p1). Probed at each pin pose with `press_interact` (`f65_*.log`).**
- At the pin poses all three use: XD-26's crosshair hits the platform's top face, event 9 "Great nest" (250 away), and
  gives the scarab; XD-23's hits "Fire pit" event 7 (227 away). What misleads: the name of a face or decoration shows
  in the status line up to 1,024 away (`NearHoverStatusDistance`), but a Use reaches only 512 (`mouseInteractionDepth`,
  MM's 0x200); between the two the name shows and the click does nothing (with the smart click, it attacks instead).
- XD-25: the crosshair hits the decoration `deco:crystals` ("Crystals", no event) standing in front of the housing that
  has `evt:crystals`. The keyboard fallback (`pickKeyboardUseTarget`) finds the housing, but the Use (E or the left
  click) takes only the crosshair's hit and never falls back, so clicking the crystals does nothing. MM's click ignores
  decorations without an event (OpenEnroth `vis_decoration_noevent_filter` on the left click); OpenYAMM's pick does not.
- Not changed this round (agreed scope: the dungeon agent did not reach F65). Spec for the next builder (REQUESTS):
  `GameplayWorldPickRequest` gets `ignoreDecorationsWithoutEvent` (beside `ignoreActors`), honoured by
  `IndoorRenderer::inspectAtCursor` and `OutdoorInteractionController`'s pick, set by the Use path
  (`GameplayInteractionController` ~2920) and the smart click's choice; hover keeps naming them. Test: XD-25 at the pin
  pose, the Use through the input path gives the crystals. MM6–MM9: decorations without an event stop blocking clicks,
  as in the originals. Data meanwhile (dungeon lane): `deco:crystals` carries `evt:crystals` too.
- X4 p10 "let it burn when you click on it" is at a Barbarian tent, not the campfire: a content suggestion (DECIDE 4).

**F68.** X5 p1 (temple blessing): MAW reads reputation as Neutral (DEVIATIONS 202), and a Neutral donation blesses no
one, as in MM7: D-148, replied. X5 p2 (music): the map's MM6 track 47 by design: D-149, replied. XD-14 p2 (alchemy):
the Workbench files recipes by the mastery the game requires, and MAW's own table gives 252–261 Master: D-147, replied.
X1 p31 (Vertigo's spell books): no fault: as in MM6–MM8 a guild's shelf holds every spell of its rank (Vertigo's guilds
teach four spells each, `guild: {spells: 4}`, and the shelf has room for all four, `generateGuildSpellbookStock`); the
paid New stock (D-129) rerolls shops only. Resolved. X1 p30 (no boat back from Vertigo): true; Nystor's boat (X2 house
4063) sails to `vertigo_creek` (route 403) and to `x4_river_landing` (407), and neither landing has a boat back
(Olympus' dock, routes 424-426, has its mirror). A return boat at each landing is town data and a map door (A4, A5):
REQUEST. Replied on the pin, left claimed.

**3.3 checks.** X4 p9 (campfire rings and food): at the pin the first click gives 2 food and a ring, the second
nothing; the fire stays drawn and named (`x4_campfire.log`; `tests/scenarios/xeen/campfire_once.yml` covers reloads).
Resolved.

**F58's oymap (the outdoor agent's spec).** `openyamm-studio/core/OutdoorBuildings.cpp` `ruinPieces`: a gone bay of a ruin's lowest row
over a foundation stands one 8-unit course (`RuinCourse`), so its cap no longer lies on the levelled land. X2 scratch
build: `check_faces.py` on_land 16 -> 6, 0 ruin lines (were 10), `shell.open_edge` 0. Note: `check_faces.py` caches each
map's export by name; give `--cache` per build when comparing two builds of one map.

### F58/F60 XD-13, F60 XD-14/XD-19, F63 dungeons, F65 data side, D-143, D-146, D-151 (agent `xeen-fb4-dungeon2`, 2026-11-25; for A7, A8, A6's X8, A3)

Scratch `output/xeen_fb/p4_dungeon2/` (`cyc.sh <key>`: regen, build, stage, audit, `check_parapet_gaps`, drops, every
playtest from assets_dev + the stage; `post.sh <key>`: install, bake under `bake.lock`, MAW reserve, open-sky,
arrivals, ledge shots, exits). After captures: `after/xeen_xd13/`, `after/xeen_xd14/` (before:
`output/xeen_fb/p4_dungeon/before/`). **Rebuilt, installed and baked once each:** XD-10, XD-11, XD-13, XD-14, XD-19;
X8 installed (no bake). Every map: audit 0 errors, playtests pass (XD-13 3/3, XD-14 3/3, XD-19 4/4, XD-10 6/6,
XD-11 5/5, X8 7/7), MAW reserves rerun, `xeen_balance.py --check` 0, `stale_bakes.py --check` 0, `key_npcs.py
--write`, `check_actor_heights.py` clean.

**F58/F60 XD-13 p1 "z-fighting" (fixed).** Not flicker: the breach (`room:breach`, the fallen north-east corner,
"seen, never walked", reached by a jump from the rubble) had its walls drawn as sky from the floor up. From the heap
the sky below the eye showed as the `swamp` preset's flat below-horizon fog, a white face beside the pillar. Fix
(`xd13/gen.py`): the breach's walls are ruin stone (ch1b1) to 832 (`BREACH_WALL`, over the heap's top 480 and the
stage-2 plug's 752), with sky only above them and overhead (its ceiling raised to 1,024). **Check:**
`tools/xeen/check_parapet_gaps.py` rule `sky.low` (a sky wall with no parapet, coming down to within 64 of a floor
that runs up to it; skipped on maps whose preset draws sky below the horizon and on `open_ground` horizon rooms). World
sweep (`sky_low_before.txt`): XD-13 3 faces (fixed, 0 now) and **XD-12 16 spots** on the four roof terraces and the sky
stair, where raised floors (3,136-3,184) meet sky faces from 3,200 (left: A8's map, not rebuilt, NEXT; not captured).

**F60 XD-14 p3/p4 (fixed, resolved).** The predecessor's `sky_side` and `xd19/gen.py` parapet fix built. After
captures at both pins show the parapet running wall to wall. `check_parapet_gaps.py`: XD-14 0, XD-19 0 (XD-22's 7
are the railing's corner and the rope slot, meant).

**F63.**
- *XD-14 p1, the kennels' pit (not fixed, engine).* The pit's flat floor is 512 by 256, with banks of normal z 0.83
  (walkable; the uphill limit is 0.71). A headless test (`dbg_pit2.yml`: three hostile monsters spawned, two in the
  pit, positions after 1 s and 21 s via `report_state`) gives the following. One pit monster walks out. The other
  moves 96 to (2496, 1300, -64), then stands there for good: animation 0, not targeting the party, 400 away. The
  same happens with the big bone pile (7dec18, radius 52, solid) moved out of the pit floor to its north corners
  (`xd14/gen.py`, done anyway: the floor is clear). So the decoration is not the cause → REQUEST to the engine.
  Pin claimed, replied.
- *XD-07 p1, the Fire Dragon (by design).* The pin pose (2858, -4508, -1152) is inside `room:dragon_pit`, at its
  north wall, looking into the mouth of the pit stair (160 wide, 288 high). That stair is exactly D-32's barrier
  ("XD-07's pit stair (288 high) holds the 487-tall Fire Dragon"). The dragon chased the party to it and stopped.
  Replied. DECIDE: a `leash` (about 768) so it goes back to its hoard instead of waiting at the stair. Costs an XD-07
  rebuild and bake.
- *XD-04 p5, "peasant" (by design, poorly signalled).* `monster:child_1` (Goblin peasant 439, friendly, `immobile`,
  group 11) is the half-turned boy of M4. After the warden's ring hoists cage 1, he waits (`boy_waiting`) until the
  cage is clicked again with the Alacorn (`m4.cage_1`, `child_rescued_1`). His only cue is one status line. His
  hover says "peasant" and clicking him does nothing. Replied with the way to cure him. NEXT/REQUEST: a placed name
  (A2's `source/monsters.yml` names, 401+, e.g. "Goblin-eared boy", plus `name:` on `monster:child_1` in XD-04's
  objects.yml), and his words on a click.

**F65 (data side; the engine side is xeen-fb4-engine/engine2's: reach 512 against the name's 1,024, and picks
skipping eventless decorations).** Survey `f65_survey.py` → `f65_survey.txt` covers every Xeen BLV.
- 0 eventless decorations overlap an event decoration.
- 43 eventless decorations stand within reach in front of an event wall face. DD-13 has most of them: torches 12 in
  front of door faces, bags, barrels and bones before its storeroom and bunk event faces. Also XD-03's hoard goblets
  and urn before the coin piles, DD-23's skull pile, XD-03's stalagmite.
- 36 decorations stand on an event floor or top: X8 and X9 nest bones and skulls, the planes' daises, DD-13's fires
  and table plates, XD-03's hoard bowl.
- 155 event faces are smaller than 96 on their long side: mostly buttons and levers of 16-64, MM-style.
- XD-25's crystals (on top of the housing) slip past the survey. They are D-153's site; XD-25 was not rebuilt, so
  `deco:crystals` does not have `evt:crystals` yet (NEXT, at XD-25's next rebuild). The engine's skip makes all of
  these clickable; no data change made.

**D-143, XD-10 (done, resolved p1).** `xd10/dress.py`: `SKULL_DEALS` 1 gem each (was 3/3/5/5); `GREAT_PRICE` 1 for the
great skull's +5 offer (was 10); the key stays 10. The texts ("One gem for +2 Luck?", "clacks shut on one gem") and the
notice board ("ONE A HEAD FOR THEIR GIFTS") are changed. `source/quests/m12.yml` `skull_upper`/`skull_deep`/
`skull_grotto` `where` and texts are changed, and `build_world.py --only gen_quests` was rerun (3 files).
`playtest.yml` covers one granted gem for Luck, 4 left after the key, 3 after the great skull's offer (6/6). Note:
`build_world.py --check` shows `trainer_places.txt` differing; that is not this agent's change (left).

**D-146 (done).** `oymap audit` of all 69 Xeen BLVs: `face.in_doorway` 0, `thing.in_doorway` 0 (`audit_all/`). XD-14
p5 resolved with the after capture. Only audit errors in the world were X8's 4 `textures.feature_cut` (the
predecessor's stair-of-cloud panels' 48-wide ends): fixed (`end_surface`), 0 now.

**D-151, X8 (done).** `evt:down_stair_landing` needs 111240 or 111260, and `evt:down_witch_landing` needs 110046.
Otherwise the decider's lines show on the status line (`gen_objects.py`). Each down playtest first tries without the
qbit (`gen_playtests.py`). Notes of X8, XD-04 and XD-11 changed. **XD-11 `roof_1`:** the open roof has no spot hidden
from the X8 landing (`hide.py`, `hide2.py --any-room`: none). The marker moved to the Stairway to Heaven's foot
(`spawn:stairway_1` (-1728, 1664, 1920), hidden with its 128 spread). `check_arrivals.py` on XD-11: 0 errors (was
arrival.hot).

**Not done (NEXT):** the X8 bridge/lid fix on X9, D7, P5, and on P1-P4, plus the lid triage (item 8); XD-12's
`sky.low` spots; XD-25's crystals event; XD-04's boy name; XD-07's leash (DECIDE).

### F65 (picking, hover reach, D-153), the X8 step trigger (agent `xeen-fb4-engine2`, 2026-11-25 ~08:40–09:20; for A1, A7, decider)

Scratch and logs: `output/xeen_fb/p4_engine2/`. Game `build-xeen/game/openyamm` rebuilt (heavy.sh, -j16); unit 3199/3199,
the new runtime doctests 4/4; oymap released `openyamm-studio/build-xeen/oymap` 09:05:01 (private link first,
`oymap/build_oymap.sh`), oymap_tests 535/535.

**F65, the Use looks through decorations without an event (D-153, every world).**
- Game: `GameplayWorldPickRequest::ignoreDecorationsWithoutEvent`; `IndoorRenderer::inspectAtCursor` skips, when it is
  set, a decoration (billboard, model or the entity box) that has no event, light toggle or interactive state
  (`entityHasInteraction`, shared with the hover's filter). `GameplayInteractionController` sets it for the Use key,
  the smart click's choice, Trigger's first pick and the context popup (`usePickRequest`); the hover and the attack pick
  are unchanged, so a torch or bones keep their name. Outdoors the interaction picks skipped such decorations already
  (`DecorationPickMode::Interaction`). MM6–MM9 indoor: as the originals' click (MM7 `vis_decoration_noevent_filter`).
- Test `tests/scenarios/xeen/x9_use_through_nest_bones.yml` (X9's first Roc Nest, the crosshair on its bones, a Use
  through the input path asks "Destroy?"): passes; with the flag forced off in the same build it fails (`x9_noflag.log`).
  Headless note: indoor decoration models are posed only once something has picked or hovered, so the old binary
  without a hover first passes it too (`x9_bones_before.log`); the scenario hovers first (`hover()`).
- Sites: the dungeon lane's survey (`output/xeen_fb/p4_dungeon2/f65_survey.txt`, 233 eventless decorations on or in
  front of an event face in 14 maps: DD-13 87, XD-03 52, XD-23 23, P5 23, X9 10, ...) are all covered by the engine rule.

**D-153, a name only within a click's reach.** `resolveHoverStatusText` takes the interaction depth (the crosshair's
`keyboardInteractionDepth`, the cursor's `mouseInteractionDepth`, clamped 32–4096; `HoverStateInput::interactionDepth`)
for faces, mechanisms and decorations with an event (indoor Entity, outdoor Decoration targets); a decoration without
an event keeps its name at any distance; `NearHoverStatusDistance` (1,024) is gone; no "Too far away" line.
Doctests `tests/HoverReachTests.cpp` (400 named, 600 not, for Surface, Entity, Decoration, Mechanism; eventless 3,000
named). Scenario Lua gained `hover()` (README).

**XD-26 p1, the Great nest: a studio fault.** The nest (a platform 24 high, clicked, `evt:nest`) stands in
`room:roost`, whose floor runs `evt:roost_seen` (step). `featureFloorPart` gave every low block's top the room's step
event, so the nest's top was a pressure plate and only its 24-high rim was clickable. Fix
(`openyamm-studio/core/IndoorLowering.cpp`): a clicked block keeps its click on its top. Test
`tests/scenarios/xeen/xd26_nest_name_within_reach.yml` (from about 700 no name and no scarab; at about 400 "Great
nest" and the Use gives the scarab): passes on a scratch root with XD-26 rebuilt (`xd26_scratch.log`), fails on the
installed XD-26 (`xd26_installed.log`) until it is rebuilt. Sites (a clicked block under 50 high in a room with a step
event; their tops change at the next build): DD-05 `bed_humble`, `bed_pious`; DD-13 `pit_e`, `pit_w`; DD-23 `nest`,
`heap_high`, `heap_north`, `heap_west`, `heap_east`, `heap_south`; XD-14 `bed_k1`-`bed_k3`; XD-22 `cushion`; XD-26
`great_nest` (16 in 7 maps; DD-10B's god crystal stands higher and is unchanged). Each room's step event is a "seen"
text except DD-05's `humble_ask`, which the room's floor still runs.

**XD-25 p1, the crystals: data, not the pick.** `deco:crystals` is `crclstr`, MMerge's gem crystal: an interactive
decoration whose first click gives a random Gem and hides it. At the pin the first Use takes that gem, only the second
reaches the housing's `evt:crystals` (`f65_xd25_probe2.log`). The engine change does not touch this. Dungeon lane: give
`deco:crystals` the housing's event (or a decoration that is not a gem crystal); the check
`output/xeen_fb/p4_engine2/xd25_use_gives_crystals.yml` (machine dead, one Use at the pin gives 12313) fails today and
belongs in XD-25's playtest once fixed.

**X8, a step trigger on a platform top.** No engine fault. On a scratch X8 with `platform:witch_landing_down` as a
flat step (top -256) and `trigger: step`: walking on from the stair (press_action, a movement_segment, or the whole
walk from the island) runs the event every time (`x8_step/probe*.log`). With the `exit:` effect the move needs the
leave window, which a scenario queues and opens only with `advance_runtime: {present_dialogs: true}`; with it, OK takes
the party to XD-04 (`probe4.log`). xeen-fb4-dungeon's attempt asserted without presenting the window.

Captures: `shots/xd26_before/` (engine tour at the far and pin poses; a tour runs in cursor mode, so the status line
shows no hover and the scenarios are the evidence). Pins: replied on XD-26 p1, XD-25 p1, XD-23 p1 ("A name now shows
only when a click can use the thing."), left claimed by xeen-fb4-dungeon.

**Not done:** X5 p11/p12 (X5 not installed with the new oymap yet); F63 XD-14 p1 (the kennel pit's frozen monster,
`output/xeen_fb/p4_dungeon2/dbg_pit2.yml`): not started, token budget.

### F58, F59, F60, F61, F63, F64, F66, F67, F69 outdoors (agent `xeen-fb4-outdoor`, 2026-11-25 ~07:40–10:30; for A5, A6, A1, A3, tools)

Scratch `output/xeen_fb/p4_outdoor/` (`tools/cycle.sh`, `tools/install_check.sh` with the current oymap and
`build-xeen/game/openyamm`; `tour.sh`, `near.py`, `sheet.py`); before pictures at every pin pose `before/<map>/`,
after pictures `after/<map>/`; sub-agents' work `sub_a/` (X4, X2), `sub_b/` (X5, X6), `sub_c/` (D-142), `sub_d/`
(D-144, D-141). Pins claimed by `agent:xeen-fb4-outdoor`.

**F58, the ruins' flicker.** Cause: where a ruin's wall is gone the studio drew the foundation's sill as a cap at the
part's floor, and the plot's land is levelled to that floor: the cap lay on the land (X2 p11, X4 p2, X5 p5, X6 p2,
p12; every ruin of the 13 maps). Fix at the source (A1/engine, oymap 08:29 and later, `OutdoorBuildings.cpp`
`ruinPieces`): a gone stretch keeps a stone course 8 over the floor. Check: `tools/xeen/check_faces.py`
`faces.on_land` (an upward face within 2 of the land over 512 sq units; water faces skipped). Sites: ruins X1 4, X2 2,
X4 2, X5 1, X6 2 (rebuilt now); X3 newcastle_ruin, watchtower, wreck; X7 east_lookout, watch_barracks, pony_shed;
D3 rim_watch, vespar_ruin; D5 hill_shrine; D6 broken_pyramid, ridge_tower (their next rebuild). Other on_land kinds
the rule found and left (NEXT): the bridge decks whose end pads round back up to the deck (X2 great_bridge,
medin/island jetties, X4 kings_bridge (fixed by the bridge's move) and nystor_jetty, D2/D3/D4 bridges: a 4-unit deck
lift broke the ends' fit and is off, `wild.py DECK_LIFT`), the lane steps' lowest treads (X1), cave-mouth floors
(t2bs), X1's culvert pieces, X5's hot spring and pools, D1's trebuchet. X1 p29 (the hull's top, 3.2's hull): 3.3's
hull shows no flicker at the pose (`check29/`), no face pair there: fixed by 3.3.

**F59, things on slopes.** `level_generation/projects/xeen/common/level_pads.py` `auto()` (run by `wild.apply` on every
outdoor map): a set piece with a foot of its own (tents, fountains, wells, crates, stone rings, titled or clicked
decorations, piles) on land uneven by more than 32 under its footprint gets a level pad (touching pads merge at the
lower height); the choice is kept in `common/level_pads.yml` (a padded thing's land is level at the next run). A plain
rock, stump or bone heap (decoration_data's description) sinks to its rim's lowest land (`raise`). Footprints of model
decorations from their GLB at their bound height: new `tools/xeen/deco_footprint.py`. Checks: `town_fit_check.py`
`things.overhang` now also tents, platforms, obelisks, crates, stone rings, models (raised caps and spans over water
skipped) and new `decorations.slope`. Pins: X1 p28 (rock12 sunk 32), X4 p7 (eyrie skull pile padded), X5 p3 (Freeda's
tent, 277 over the slope before), p8/p9 (the Cyclops' outpost tents), X6 p11 (the half-buried wagon), X4 p5 / X6 p6
(fountains: padded in 3.3 already). X4 p8 "see through": the sky-crack ledge (a platform) over Gargoyle Peak, padded in
3.3 (the pin's pose is now inside the hill). X5 p6 (the face tree): a scattered tree on walkable ground, not changed.
Sites on maps not rebuilt: `tools/xeen/town_fit_pending.yml` (X3 2 tents, X7 wagon, D1 Sardaj tent, D3's crags ×7, D6
cinder vent and a barrel).

**F60.** X5 p10: the Troll Warren's free-standing mound was `cwb1` (F50's stone), a dark brown rubble reading as dirt
on the snow; now Winterkill's grey stone `cnb` (`x5/gen.py`). X5 p4: X5's own fen fell 600 under `hull_049` at the
south-east corner: a terrace at 928 under rows 100-104 (`x5/gen.py`); a rim proposal for c7 (hull pieces over land
varying more than 128: four `xeen_hull1` or the lowest edge height; survey `sub_b/hull_steps.py`). X4 p6: 3.2's wall
faces across the east gate; fixed by 3.3 (`wall_check` 0). X4 p8: F59 above.

**F61, the Sphinxes (D-141).** LOD3 lay 17-40 inside LOD0 at paws, door frame and haunches, so LOD2 proxies
(`level_generation/decorations/xeen_sphinx_claude/scripts/collision_proxy.py`, installed with `install_model.py`) are
the `collision_model` of `xeen_sphinx_north/south` (`worlds/xeen/models/decorations.yml`, `collision: model`); the
barrier rings are gone; door carriers ±208/±176, tops 528/464, front 8 inside the reveal (`x6/places.py`). New
`tests/scenarios/xeen/x6_sphinx_solid.yml` (p7, p8, p10: the party stops 22-79 outside the model). X7's idols: the
camera never entered them; not changed.

**F63 placement.** The engine agent's oymap stands actors on structure tops (X5 p11/p12) and warns when an actor
stands inside a model. X5 p7: the outpost's eight Cyclopes at fixed spots inside its fence (`OUTPOST_CYCLOPES`); X5
p13: wave spot (39.2, 38.8) → (39.6, 39.4) out of the Acme machine; X6 p4: X6's markers 2.5 cells from the cove, rims
and bounds (`HULL_CELLS`), X5's bounds guard; X4's barbarians off tent 3; X3's rangers (generator only). New check
`tools/xeen/check_spawn_clear.py` (`spawn.in_model`, `spawn.at_hull`); other maps' sites in `sub_b/spawn_clear_all_before.txt`.

**F64 (D-142).** `check_arrivals.py` `arrival_kind()`, floors 4,096 / 5,888 (shooters) at edges and the start,
dungeon exits on the rebuilt maps (`D142_EXITS`: X1, X2, X5, X6), road setback 1,024 (warning); `x2/check_d85.py` and
`common/d85.py` report them; new `common/d142.py` `enforce()` for the samplers. X1 W 2,889 → 6,332, N 2,561 → 6,886;
X2 W 2,243 → 5,894, N 2,902 → 6,435, E 4,881 → 6,146; X5 N 2,127 → 4,417; X6 E 2,869 → 4,283 (and every dungeon exit
of these four ≥ 4,252). **X4 not done** (its encounters are polygons: needs circle markers); X3, X7, D1, D3, D5 fail
the new floors on their installed maps (`sub_c/others_<key>.txt`). MAPS.md and ROADMAP's D-15 band text updated.

**F66.** X6 p3: the barrels stood 90 from the coach's wall by their table radius but drew wider: moved 220 off it
(`x6/places.py`); `props.in_wall` measures barrels, casks, crates and sacks by their model's width too (found D6's
`np_prop_2`). X4 p11: the castle ramp's geometry is closed (cheeks to the land less 64, land flat under it); the party
got inside through a collision gap, probably XD-07's gate arrival (-1024, 6912, 1808) 7 over the ramp's top: REQUEST.
The 13 maps have two ramps (X4, D1), both closed.

**F67.** X4 p12: The Potter's door faces north onto the road (`x4/gen_l1.py` `ASP_HOUSES` 4183). X4 p1: the King's
Bridge's line on y 76.5, where the road's tiles lie. X4 p3/p4: the falls lean 448 as a sheet over the lip into the
pool (`x4/places.py`, `x4/land.py` POOL from row 41), not an upright dark slab. X2 p12: Nystor's pier 0.25 cell deeper
only (52.45): deeper, `bridge_ends` and `bridges.step` take its head for a land end (NEXT). Other houses off any street
(X4 13, X2 16) and bridge ends that miss their road (X2 ogre_bridge, maybe X1/X5/D1/D2) are listed in `sub_a/`.

**F69 / D-144, D-152.** Clicks instead of free questions: X6's Shrine of Energy, the Reflectors of X1, X5, X6, the burns
of X4's barbarian camp (after-text "Scorched planks. The barbarians will not camp here again.", its bones hidden) and
X5's outpost; X3's rangers' camp (generator only). D1's Sardaj camp keeps its question (Q-D12's war or peace). Hooks
`status: true` / `else_status`. New `check_wiring_rules.py` `ask.free` (outdoor Lua). Tests: the four `gen_walk.py`,
`85_reflectors.yml` (X7 still asks), `q-c16_cyclops_outpost.yml`.

### F65 dungeons (XD-26, XD-25, XD-23, the clicked-top sites), D-154 XD-07, XD-12 `sky.low`, F62 on X9 (agent `xeen-fb4-dungeon3`, 2026-11-25 ~09:00–09:45; for A7, A8, A6's X9, A1)

Scratch `output/xeen_fb/p4_dungeon3/` (`cyc.sh`/`post.sh` as dungeon2's, plus `EXTRA=<scenario>`). Every rebuilt map:
audit 0 errors, `check_parapet_gaps` and `check_drops` clean, all its playtests pass from the stage, then installed and
baked once (09:05 oymap), MAW reserve rerun; at the end `xeen_balance.py --check` 0, `stale_bakes.py --check` 0,
`key_npcs.py --write`, `check_actor_heights.py` clean, `indoor_bake_brightness.py --check` on each.
**Installed and baked:** XD-26, XD-25, XD-07, DD-07, XD-09, DD-05, DD-23, XD-14, XD-22. **Built, not installed:**
XD-23, DD-13 (wait for the studio fix below).

**XD-26 p1 (done, resolved).** Rebuilt with the 09:05 oymap: the Great nest's top keeps its click.
`tests/scenarios/xeen/xd26_nest_name_within_reach.yml` passes from the stage and from assets_dev after the install.

**XD-25 p1 (done, resolved).** `xd25/gen.py`: a second event `evt:crystals_cluster` on `deco:crystals` (crclstr), the
housing's hook; both events, once `q-c5.done` is set, also hide the crystals (else the hook's fail text). New L4 playtest
`playtest_crystals_use.yml` (from engine2's check: one live Use at the pin gives 12313 and no Diamond 2056, the
decoration hidden after, a second Use gives nothing more): fails on the old map, passes on the new.
- **Sweep and check: `tools/xeen/check_self_acting_decos.py`** (all Xeen BLVs, 4 s). It mirrors the game's
  `InteractiveDecorationRules.cpp` (gem crystals, barrels, cauldrons, trash heaps, camp fires, casks, sacks, bags,
  buckets, MM8's dec40–75, the light toggles). Error `self_acting.on_event`: an eventless self-acting decoration on the
  top of a clicked face or overlapping an event decoration (it reads as part of that thing). Warning
  `self_acting.beside_event`: one standing in front of an upright clicked face (a sack by a bed; the thing stays
  clickable from its top). Note: decorations carry the studio's event in `event_id_secondary`, and clicked faces are
  those with attribute 0x02000000 and `cog_triggered` (`cog_number` is the face's cog, not its event): the F65
  survey of dungeon2 read `cog_number`, so its counts are not reliable.
- Sites: errors 4 → 0: XD-25 crystals; DD-07 `deco:vat` (cauld00 on the vat bench: now `evt:vat_pot`, the vat's text,
  D-39 no stat); XD-09 `deco:forge_fire` (ckfyr00, gave food and went out) and `deco:forge_pot` (cauld00): now
  `evt:forge_fire`/`evt:forge_pot` with the hearths' texts. Warnings 7, left (meant: separate things beside a
  clickable one): DD-07 two sacks by `evt:bed_1`, DD-14 two barrels beside the cellar trapdoor, XD-21 a sack by
  `evt:bunk_1`, XD-22 two sacks by `evt:chest_cellar` and `evt:shinobu`.

**XD-23 p1 (cause found, studio REQUEST; not resolved).** At the pin the live Use and `hover()` find nothing at any
pitch (-35 to -15); engine's `press_interact` probe used the scenario's fallback pick, which found the rim. The fire
pit's top (face 978) has event 0 and no click: the pit has `set_texture ... face: top`, so the studio builds the top as
a node of its own (`TRIGGER_top_fire_pit`, cog only) without the block's click; only the 24-high rim clicks. A rebuild
with the 09:05 oymap does not change it. Same on XD-02's two drinking pools (water floor part on top) and DD-13's two
pits (`xochar` tops). REQUEST to A1 (IndoorLowering.cpp: the lid node of a clicked block takes the click unless its
floor part has an event of its own). Test `tests/scenarios/xeen/xd23_fire_pit_use_at_pin.yml` (hover "Fire pit" at
the pin, one Use burns the lair): fails today. Replied on the pin, left claimed.

**Clicked low blocks (the 09:05 studio fix and the above): `tools/xeen/check_clicked_tops.py`** (a block under 64
high whose clicked sides' top inside the same outline has another event or none). Before: 17 on 7 maps. Rebuilt with
the 09:05 oymap and installed: DD-05 beds (2), DD-23 nest and heaps (6), XD-14 kennel beds (3), XD-22 cushion (1),
XD-26 (1). Left 5: XD-23 fire pit, XD-02 two pools, DD-13 two pits (rebuild after the studio request; DD-13's rebuild
today moved its tops from the step event to none, so it was not installed).

**D-154 XD-07 p1 (done, resolved).** `xd07/gen.py` `leash: 768` on `monster:fire_dragon`. `playtest_dragon.yml` gains
the party in the pit at the pin's place (wakes it), then at the stair's foot for 20 s: the dragon stays 300+ from the
mouth (it stops at about (3438, -4350), 770 from its post); without the leash it waited at (2944, -4156), 60 from the
mouth (the step fails on the old map). D-32's check (portcullis up 40 s, the dragon still in the pit) passes. **Not
as D-154 said:** it does not walk home when the party leaves: out of the party's sight an indoor actor is a background
actor (`selectIndoorActiveActors`, MM's rule) and holds still, so the playtest asserts it stays within its leash (864)
and away from the mouth instead. Ledge shots 0, MAW reserve run (spawn points only).

**XD-12 `sky.low` (looked at; check refined; 2 left for A8).** Captures `xd12_before/` (roof corners, sky stair): no
white face. 14 of the 16 were the roof parapets' corners: a 32-thick parapet top with the sky standing on its end, as
on every parapet run. `check_parapet_gaps.py` `sky.low` now counts a floor at the sky face's foot only when it is at
least 64 deep and wide (`DEPTH`). Left: faces 2056/2057 (room 39, the sky stair's east wall top at 3,184, 112 over the
roof, sky down to it at both ends): seen only after a jump onto the wall; A8 (draw those two ends as stone, or the
band 128 higher). XD-12 not rebuilt.

**F62 on X9 (decks level over the clouds).** `x9/gen.py`: `landing_end` (X8's) and `level_spans`: the neck, road,
causeway and rope-bridge decks lie level at each cloud's height until they are past that cloud across their whole
width, and slope (or sag) only between; a level span is a plain block (`base`/`rise`, no `top_heights`/`thickness`).
`check_floor_cross.py` on the scratch build: `floor.cross` 27 → 1 (left: (-504, 10926), a cloud and the 7tws1f
flags; not looked at). X9 regenerated with `regen.py --build`, installed (no bake profile), MAW reserve rerun; audit
0 errors; playtests 5 of 8 pass (main, castle_gone, dragon_clouds, hostility, tonic) and
`x9_use_through_nest_bones.yml` passes. The three fall playtests (`fall_chain`, `fall_south`, `fall_xeendom`) fail at
step 10, "member Brokk has 178 health, expected 181" after the fall to X2. They fail the same way on the X9 installed
before this change, so the fall's damage has changed elsewhere (the 09:19 game binary?) and not here (A6/A1, NEXT).
`check_drops` gives X9's void floor (-6,000, exit 15) as a pocket, as before. `SINK` (lids, 38 on X9) is not ported.
Not started: D7, P5, P1–P4 and the 22-dungeon lid triage.

### F63 XD-14 p1 (kennel pit), X5 p11/p12 confirmed (agent `xeen-fb4-engine3`, 2026-11-25 ~09:10–09:50; for A1, A7, A5)

Scratch and logs: `output/xeen_fb/p4_engine3/`. Game `build-xeen/game/openyamm` rebuilt (heavy.sh, -j16) with the fix
below and no diagnostics; unit 3201/3201 (two new doctests).

**F63, XD-14 p1 (cause found, fixed in the engine, every world).**
- The predecessor's "frozen" Wizard (`p4_dungeon2/dbg_pit2.yml`) was not frozen: it stood 285 from the party's edge,
  inside MM's melee reach (307.2, `ActorMeleeRange`), so as in the originals a ranged monster there stands and shoots
  (`StandForRangedBlock`, trace `wait_no_shot` / `attack_ranged` every 2 s; a werewolf at the same spot hits the party,
  `pitw_dmg.log`). `report_state`'s `targeting_party` is only true while pursuing or attacking, hence the confusion.
- The real fault: with the party 1,000 away (`pitfar.yml`, nine werewolves over the pit floor), one werewolf climbed
  the east bank, turned back and met the corner bone pile (`kennel_bones_2`, dec29) on the bank, then stood at
  (2828, 1437, -56) for good, pursuing. A per-substep trace showed the swept move hitting the pile at distance 0,
  sliding along it, and hitting it again at distance 0 for all eight sweep iterations. Cause:
  `sweepIndoorSphereAgainstCylinderWithNormalizedDirection` (`game/indoor/IndoorCollisionPrimitives.cpp`): a body
  touching a cylinder was stopped by any move with `B < 0`; the slide projected from the contact normal is tangent,
  and its float residue pointed inward on about one contact angle in seven (the new doctest: 101 of 720 slides blocked).
- Fix: touching, a move counts as into the cylinder only past a tolerance of `CollisionEpsilon * combinedRadius`
  (well over the rounding, well under one degree inward). Shared by every indoor body (actors, the party) against
  decorations, sprite objects and actor bodies in MM6–MM9 and Xeen; outdoors uses its own overlap handling (unchanged).
- Sites: every round indoor collider in every world (decorations with collision, actors, sprite objects); the XD-14
  bone pile is the reported one. No map change needed; XD-14 was not rebuilt.
- Checks: doctests "swept indoor sphere slides along a touched cylinder" (fails before: 101 blocked) and "... touching
  a cylinder still stops a move into it" (`tests/IndoorCollisionPrimitivesTests.cpp`); scenario
  `tests/scenarios/xeen/xd14_kennel_pit_monsters_leave.yml` (nine werewolves must reach the party, feet out of the
  pit): passes now, fails on the 09:13 `build/game/openyamm` (step 18, the werewolf at the bones, `xd14_before.log`).
- Regression: 53 scenarios (MM6/MM7/MM8 indoor monsters and party movement, MAW indoor, arenas, MM9 AI walkers,
  XD-02/XD-26 doors, `regr_list.txt`): 50 pass; the three `scene_overlays/` ones need their folder's `run.sh` (test
  mount, save order) and fail alike on the old binary. Pin resolved with a capture at its pose
  (`shots/xd14_pin/01-p1_pin.png`: a werewolf has come up to the party).

**X5 p11/p12 (Winterkill's ghosts).** X5 installed 09:20 from the 08:35 oymap: `tests/scenarios/xeen/x5_winterkill_ghosts_move.yml`
passes (`x5_ghosts.log`). Capture at the pin pose `shots/x5_pin/01-p11_pin.png` (wave 1 on the paving; the ghost waves
appear later). Both pins resolved (claims taken over from xeen-fb4-engine).

**Installed with bakes** (installer sub-agent, `tools/install_check.sh`): X6 09:11:10, X4 09:18:15 (no D-142),
X5 09:20:49, X1 09:25:38, X2 09:28:48; `stale_bakes --check` 0, `check_wiring_rules` 0 (X1/X4/X5/X6 lines out of
`OUTDOOR_OPEN`), `balance.py` ok. Walks pass (X6 358, X5 735, X4 418, X1 422, X2 449 steps), hostility, daily, randon,
danulf_ring pass; `x6_sphinx_solid`, `x5_winterkill_ghosts_move` (X5 p11/p12, the engine agent's fix), `x1_hull_edge`,
side quest q-c16 pass. **Fail:** X2 `playtest_lake_dragons` / `_leash` (D-142 moved the north-west dragon's home to
(20.5, 51.5); `x2/gen_lake_dragons.py` must be rerun and its `SHORE` looked at: both pass when regenerated in
`output/xeen_fb/p4_outdoor/x2/dragon_tests/`). Left on the installed maps: X1 way_in_dress_18/_20 `decorations.slope`
(new, beside the merged campfire pad), X2 lair_dress_7 (new), old slope lines (X5 haybales, outpost_tent2 45, X2
yak_dress_4, X4 eyrie_bones_3 57, X1 way_in_dress_36), X5 `check_wild rim.point` (21504, -18944) on 928 land, X4
`gen_daily.py` KeyError 'x4', `towns.py --strict`: X4 Asp villager 31 375 from a house door (the Potter's turn?), D5's
Doom barrier. After pictures `after/<map>/`, sheets `sheets/`. Pins resolved: 32; left claimed: X4 p11 (ramp), X5 p6
(a scattered tree, not changed), p8/p9 (the left tent still on its slope edge), plus X1 p30/p31, X4 p9/p10, X5
p1/p2/p11/p12 (other agents').

### D-150, D-155 (agent xeen-fb4-town, 2026-11-25 09:30–09:58; for A2, A3, A4, A7)

Scratch `output/xeen_fb/p4_town/`. Captures `cap/` (real game, the user's pin pose).

**D-155, XD-04 p5 (the goblin-eared boy reads "peasant" and does nothing on a click).** The cause was that
`monster:child_1` had no name and no NPC. The fix touches four sources. A2: `placed_names` 416 Goblin-eared boy.
A4: NPC 4053 in `x1.yml`, "Goblin-eared boy, Toad Meadow Child" (D-21 capitalises the decision's "child"), house
none, with the decision's greetings and portrait `npc14053` (batch 16). A3: `m4.yml` topic 40204 "Ears", whose
states mirror `cage_1` and check `child_rescued_1` first:
- caged: the warden's ring in his strongbox;
- waiting: the Alacorn "on a pedestal on the plank bridge over the cauldron shaft, three floors up";
- with the Alacorn: cured, `child_rescued_1`, 200 once, group 11 hidden.

`cage_1`'s two lines now name the same place. XD-04: `name:` and `npc: 4053` on `monster:child_1`; rebuilt,
installed, baked 09:54. MAW: no reserve (spawn points); `xeen_balance.py --check` ok.

- Checks, all passing: `playtest_m4.yml` 119/119 (new first section: the three states, the cure's single award,
  the empty cage afterwards), `playtest.yml` 196/196 (the cage route), `playtest_hostility.yml` 36/36;
  `key_npcs.py --write` adds the boy to Witch Tower; `check_actor_heights`, `stale_bakes` 0.
- Captures: `cap/boy_hoisted_hover.png` (hover "Goblin-eared boy") and `cap/boy_talk.png` (his talk, portrait,
  "Ears").
- Not asserted headless: the headless pick reads "Locked cage" there, because it still meets the hoisted cage's
  bars at their rest place. The real game picks the boy.
- Sites: the other friendly placed children are cages 2–4. They vanish on rescue and need no talk.
- Pin resolved.

**D-150, X1 p30 (no boat back from Vertigo).** The data side is done. The map side was given to
xeen-fb4-outdoor2 by the orchestrator.
- X1: `x1.yml` house **4042** Nystor's Landing (boats, door `thing:nystor_post`: the mooring post on a short jetty at
  `vertigo_creek`). Owner **4054 Rudd**, Nystor's Mate. Route **433** to `rivercity_dock` [mon, wed, fri, sun], 1 day.
- X4: `x4.yml` house **4187** Nystor's Landing (door `thing:nystor_post`, replacing event 129), `opens: q-c23.done`
  with the post's closed line. Owner **4346 Marla**, River Pilot. Route **434** [tue, sat], 2 days,
  `qbit: q-c23.done`.
- Tables written by `gen_towns`: npc, greet, house_data, house_animations, transport rows. Portraits `npc14054` and
  `npc14346`.
- Test: new `tests/scenarios/xeen/nystor_boats_back.yml` 46/46, both round trips by `evt.EnterHouse`.
- `towns.py --strict` lists the two door-less houses until X1 and X4 are rebuilt with the posts. Pin replied, left
  claimed for outdoor2.
- Sites of the kind ("a landing with no boat back"): X1 `vertigo_creek` and X4 `x4_river_landing`, both fixed in
  data. D4's Isle had its ferry already (D-36). No other one-way boat routes: Olympus' dock has its mirror,
  routes 424–426.

**trainer_places.txt.** Regenerated at 09:3x. The change from HEAD is positions only: XD-17's eight teachers at the
X7 entrance x 4904 → 4921, D3's 4610 door x -13696 → -13824. `--check` 0 differ at 09:56. It goes stale again if
outdoor2's X1/X4 rebuilds move a teacher's door: rerun `build_world.py --only gen_towns` after them.

### X2 dragons and pier (F67 p12), X1 D-150 jetty and slope lines, D-157/D-158 checks, the hull steps rule (agent `xeen-fb4-outdoor2`, 2026-11-25 ~09:40–10:30; for A5, A6, A3, A4)

Scratch `output/xeen_fb/p4_outdoor2/` (`tools/cycle.sh`, `install_check.sh`, `post_install.sh`, `tour.sh`, `hmap.py`
land heights per node); after pictures `after/<map>/`. Sub-agents: X4 (`x4/`), X5 and X3 (`x5/`, `x3/`), below.

**X2** (installed with its bake 09:52:53). `x2/gen_lake_dragons.py` `SHORE` (23, 42.5) → (20.5, 46): 2,816 from the
north-west dragon's D-142 home (20.5, 51.5) again (it was 4,780, outside the dragon's sight: the leash test tested
nothing); both lake-dragon playtests pass. F67 p12: Nystor's pier head to y 52.0 over the river (was 52.45) with
`head: 'last'` (common/wild.py); `town_fit_check.py bridges.step` now skips an end over the sketch's water body or
river band (`sketch_wet`; a shore tile under a river's edge is not a water tile), the same 27 errors on every
installed map with and without it. lair_dress_7 (63 over its rim): the sink was read before a merged pad changed
its land; the next regen read the padded land (+0). Checks: town_fit 1 (yak_dress_4, below), reach 0, wild 0, faces
the same 5 `on_land` (great bridge, jetties, lair mouth: NEXT), check_d85 0 (10 kept, group 63), audit's classic-kit
`feature_repeated` only; walk, hostility, danulf_ring, lake_dragons, lake_dragons_leash pass. `quest_stub.py`
`act5_x9_xd17` step 40 expected 1618: stale since `xeen_common.lua` SkyFalls.x9 took X2's ground 736 (768 before);
the expectation is now 1586 (`tools/xeen/quest_stub/act5_x9_xd17.yml`), quest_stub 19/19.
Left: yak_dress_4 (Temple of Yak's east skull pile, 24 over its rim): its level pad loses to the temple's plot (1,088)
and the dip before its door (864); move it at X2's next rebuild.

**X1** (installed with its bake 09:59:30). D-150: `thing:nystor_jetty` (deck 616, x 49.3, y 54.4 → 52.3 over Pitchfork
Creek, `head: last`) and `thing:nystor_post` on it, the door of house 4042 Nystor's Landing (id read from
`source/towns/x1.yml` by door, as D4's isle ferry); `evt.EnterHouse(4042)` in the map Lua; `towns.py --strict` no
longer lists X1's door; `tests/scenarios/xeen/nystor_boats_back.yml` passes. The deck stands at 616 because an end pad
at a deck on a 32 step (608 less 8) rounds back up to the deck and lies on it (`faces.on_land` on the first build).
way_in_dress_20 (the orc mouth's east skull pile, 34): onto the mouth's terrace (82.75, 31.75; its level pad lost to
the 1,344 terrace); way_in_dress_18 (a flag) and _36 (a stump): `town_fit_check decorations.slope` now measures a
decoration by its drawn footprint (`deco_footprint`: the model's extent, the table's radius without a model; the
collision radius overstated stump5a 96 against 49 drawn) and skips flat pieces on a pole (drawn < 16 thick), as
`common/level_pads.py` sinks and pads by; on every installed map only these lines changed. `common/level_pads.py`
also pads a set decoration whose middle stands more than 20 over its rim (the check's own measure; X2's Yak pile had
26 relief, under PAD_RELIEF). ruined_shrine's 2 `on_land` faces: the shrine a quarter cell south (29.5, 96.75), its
north wall on the level node row 97, not on the land rising to the cliff's foot. Checks: fit 0, reach 0, wild 0, faces
10 (lane steps, culvert pieces, mine and shaft mouths: the known kinds), check_d85 0, common/d85 0, audit 7 (the same
classic-kit textures and a barrel's `support.edge`); walk, hostility, `x1_hull_edge` pass. Captures
`after/x1/01-p30.png` (the jetty at Vertigo's quay), `03-jetty_side.png`, `04-orc_mouth_skulls.png`,
`05-ruined_shrine.png`; `after/x2/01-p12.png`, `02-p12_side.png`, `03-lair_dress_7.png`.

**D-157, D-158 (checks).** `check_arrivals.py`, `x2/check_d85.py`, `common/d85.py`: the road setback texts say "road,
lane or path" (the rule already took every `roads` entry). `x2/check_d85.py` no longer warns of the band's upper end
for a start that shares its point with a town arrival (X1's Vertigo square); X1 NOTES, MAPS line 14, ROADMAP §5.1
item 4 carry the clause.

**The hull steps (F60 X5 p4).** `common/rim.py`: a long hull piece over installed land that varies more than
`HULL_STEP` (128) along its span is built as four short pieces, each on its own land (on X1's present sketch: 52 short
and 39 long pieces). `check_wild.py` `rim.hull_step` warns until each map is rebuilt
(today X1 15, X2 2; `output/xeen_fb/p4_outdoor/sub_b/hull_steps.py` lists 162 pieces over 160 on the 13 maps). X1
and X2 were built before the rule: theirs change at their next rebuild; X4, X5, X3 take it in this round.

**X5** (sub-agent; installed with its bake 10:01:07). p8/p9: the giants' east crags were raised after the level pads
and climbed through the outpost's pad and its east fence: the crags start at x 49.5 (`x5/gen.py`), the two tent pads
merge and the stockade is level at 2,304 out to its fence; the lone Giant (group 34) to the crag's north foot (46.0,
88.5; its top is now cut off, check_reach). Haybales: `hay` is a set word in `common/level_pads.py` (pads on every
map's next rebuild). `rim.point` (21504, -18944): the return point was read from the land before F60's terrace;
regenerated from the scratch build's land (`XEEN_WILD_MAPS`), 928. Checks: town_fit, wild, reach, spawn_clear,
door, wall 0; check_d85 1 (Randon's D-87.1 line, as before), faces the same 4, audit the classic kit's 3, no
`rim.hull_step`; walk, hostility, randon, `x5_winterkill_ghosts_move` pass. Pins p8, p9 resolved. Captures
`x5/before/`, `x5/after/`.

**X3** (sub-agent; installed with its bake 10:07:15). D-142/D-157: the polygon areas' markers are fixed circles
(`POLY_SPOTS`) moved by `d142_enforce()` (10: 4 off roads, 3 off XD-08/XD-13 exits, 1 north edge 3,455 before, 2 off
the X8 landing); `xeen_x3` in `D142_EXITS`. D-159: a sundial click turns it one step, "You turn the sundial. It is set
to {N}."; q-c7.dials_set as before; `x3/gen_walk.py` and `side_quests/q-c7_count_of_nightshadow.yml` click. F58: the
watchtower on a level terrace at 2,688 (its plot did not level the hill inside its north rim); `faces.on_land` 0 on
newcastle_ruin, wreck, watchtower (68 before; nightshadow_temple and the causeway keep 2). `rune stone` is a natural
word (sinks to its rim). F63: Ebenezer's third workman out of the stage-2 keep; three markers a cell in from the
bounds. Checks: check_d85 0 (no FF, no ROAD), check_wiring_rules 0 (X3's `OUTDOOR_OPEN` lines removed), town_fit,
reach, wild, spawn_clear, door, wall 0, towns.py no X3 line, audit the classic kit's 6; walk, hostility, q-c7 pass.
X3's line is out of `town_fit_pending.yml`.

### F65 clicked tops (studio), XD-23 p1, X9 falls, F62 sky maps (D7, P5, X9), D-159 X9 nests, D-89 X8 (agent `xeen-fb4-dungeon4`, 2026-11-25 ~09:30–10:15; for A1, A7, A8, A3, A6)

Scratch `output/xeen_fb/p4_dungeon4/` (`cyc.sh <key>` as dungeon3's, `NOGEN=1` builds a project with no generator;
`post.sh <key>`). Every rebuilt map: audit 0 errors, every playtest passes from the stage, installed, baked once where
it has a profile, MAW reserve rerun. End: `xeen_balance.py --check` 0, `stale_bakes.py --check` 0, `key_npcs.py --write`,
`check_actor_heights.py` clean, `quests.py` 0 errors, `check_wiring_rules.py` 0, `check_clicked_tops.py` 0 on 69 BLVs.

**F65, a clicked block's top built apart (studio, done).** `openyamm-studio/core/IndoorLowering.cpp`: a clicked block
whose top is a node of its own (a `set_texture ... face: top` effect, or a water/lava floor part on it) records the
lid in `m_clickedLids`; the metadata gives that lid the block's click (a floor-part lid without a step event of its own
gets the click trigger beside its water/lava flag; a texture-only lid gets a surface). A platform with a step event is
untouched (one object, one event). MM6–MM9 maps are not built by this path. Test: doctest "F65: a clicked block's top
built apart ... keeps the click" (`tests/CoreTests.cpp`); oymap_tests 536/536. oymap released 09:38
(`openyamm-studio/build-xeen/oymap`, linked privately first). Sites: the 5 left by dungeon3 — XD-23 fire pit, XD-02's
two drinking pools (blue, green; the gold and red have no water floor), DD-13's two pits: all rebuilt, installed and
baked; `check_clicked_tops.py` 5 → 0. `tests/scenarios/xeen/xd23_fire_pit_use_at_pin.yml` passes (failed before).
XD-23 p1 resolved with a capture at its pose (`shots/xd23_pin/01-p1.png`).

**X9's fall playtests, "Brokk 178, expected 181" (cause: data, fixed).** Not the engine: 3.3's X2 has 736 at
entrance:x9_fall (the ground dips toward Darzog's door; 3.2 had a level 768 there), while `Xeen.SkyFalls.x9` still
said 768, so the fall was 882, not 850 (damage = distance × maxHP/10 / 256: 92 instead of 89). Fix:
`xeen_common.lua` `SkyFalls.x9` ground 736. New check `tools/xeen/check_sky_falls.py` (each landing of the table
against its map's ground or floor, error over 16): all 9 landings 0 (D4's is 8 off, within). All 8 X9 playtests pass.
REQUEST (outdoor, X2): the island's crown is meant level ("level under the tower", `x2/gen.py`) but dips 704–752 in
front of the door; if X2 is levelled again, rerun `check_sky_falls.py` and put the table back.

**F62 ported (X8's `landing_end`, level spans, sunk blocks).**
- *X9* (installed, no bake): `SINK` in `block()`, nests and the plaza (not the awning or the keep's frieze, whose sides
  run on the plane of the sides under them: `sink=0`); the gate causeway now lies level on the castle cloud
  (`landing_end`); `level_spans` lies level on the higher cloud where the clouds overlap (`partial`). `floor.cross`
  1 → 0, `floor.lid` 38 → 6 (left: the four booth awnings on their 16-wide back walls at 896, and two booth
  counters' bottoms inside the plaza at 456 over the buried road landings: none reachable).
- *D7* (installed, no bake): `link_spans` (roads, spurs, causeways: level landings, slope between, level on the higher
  where the islands overlap; bridges: landings and the sag between them), `height_at` follows them (boards, huts,
  toll booths stand on the deck), the paved band follows each piece (24 deep; its joints 16 past the slab's), blocks
  whose foot is the walkable top under their middle are sunk 4 (8 met the hatches' foot). `floor.cross` 22 → 0,
  `floor.lid` 397 → 317: left are stacked parts (gilt capitals and courses on Olympus' columns and facades, 2,600+
  high; hut walls on hut floors; roofs). 1 audit warning left: `geometry.coplanar` w2's slab end and its band's start
  8 apart at (-27912, -11295) (internal; NEXT).
- *P5* (installed, no bake): `link_spans` with a level stretch across each board's lobe (the lobes were level discs
  through the sloping road), landings run back across a lobe at the ends, flags over a bend left out, flags 24 deep,
  blocks and the shrine's paving and disc sunk 4. `floor.cross` 11 → 0, `floor.lid` 24 → 16 (left: walls on the
  raised hut floors (9), tent roof on its walls (3), the observatory's slate (3), the gong (1)).
- *P1–P4*: not started (their crossings are rock paths through glass/lava sheets, own generators; NEXT).
- Playtests: X9 8/8 + `x9_use_through_nest_bones`, D7 11/11, P5 10/10, X8 7/7.

**D-159, X9's Roc Nests (done).** `x9/gen_objects.py`: a click burns the nest (no "Destroy?"), hides the nest, its bones
and its skull, A3's `x9.nest_*` (2,000 XP once, the "Sticks the size of spars…" line); each `nest_*_gone` load hides them
too. The skull as well as the bones (X8's D-145 did both; cheap to reverse). `gen_playtests.py` asserts the bit and
`sprite_hidden` per nest. `x9_use_through_nest_bones.yml`: a Use on the bones burns the nest (2,000 XP to the one-member
party, bit 116222, bones and skull hidden, nothing nest-named under the crosshair after); fails on the old map.
`check_wiring_rules.py` `ask.free` reads the open-air BLVs (X8, X9, D7, P1–P5): X9 5 errors → 0, the others had none.
`source/npcs/x9.yml` hook text updated (`build_world.py --only gen_quests`).

**D-89 on X8's `down_stair_landing` (done).** New sealed hook `m13.cloud_stair_down` (`source/quests/m13.yml`: entrance
XD-11, `sealed:` D-151, requires `m12.key_bought` or `done`, D-151's refusal as fail_text; added at the end of M13's
hooks, so no text id moved; on `quests.py` SEALED). X8's condition is `XeenQuests.can("m13.cloud_stair_down")`.
`build_world.py --only gen_quests` (only this change). X8 rebuilt and installed: 7/7 playtests (both down stairs refuse
first, then take the party down); `quests.py` 0 errors. The new line (40653) needs its zh-cn translation.

Not done: the 22-dungeon lid triage, XD-12's two `sky.low` ends, DD-07's 8 ledge-shot errors.

**X4** (sub-agent; installed with its bake 10:05:20, again 10:10:36 for four `check_spawn_clear` lines found after the
first). D-142/D-157: the polygon encounter areas are circle markers (`x4/gen_l1.py MARKERS`) moved by
`x4/gen.py d142_enforce()` (15 moves, the plan's own rules kept); the barbarian camp (tents, fire, chest, dress,
actors, its flat ground in `land.py`) 4 cells east and 2 north, 4,096 from the west arrival; the ogres and their chest,
the renegade knights moved; `xeen_x4` in `D142_EXITS`: check_d85 0 errors and no road-setback warning (7 and 7
before), common/d85 0. `gen_daily.py`'s KeyError: X4's own `x4/gen_daily.py <L4> <build>` is its quintain playtest's
writer (the s22 tool covers D1, D2, D4, D6; `tools/install_check.sh` picks the map's own). Villager 31: villagers
re-placed (`villagers.py --place X4`). eyrie_bones_3: the skull pile to (43.7, 41.0). D-150: `thing:nystor_post` opens
house 4187 (from `source/towns/x4.yml` by door), the closed text before Q-C23 kept; `gen_walk.py` checks both. Checks:
door, wall, wild, fit, reach, spawn_clear, wiring 0; towns.py no X4 line; audit the classic kit's 6; walk, hostility,
daily pass. Pin p10 resolved. Left: Nystor's jetty `faces.on_land` (its end pad 728 rounds up to the 736 deck: the
same fault X1's jetty showed; a pad at a deck on a 32 step should go to the step below, `common/wild.py` NEXT).
**D-160 (X4 p11)**: new `tools/xeen/ramp_test.py` writes `tests/scenarios/xeen/x4_castle_ramp.yml` (table-driven; D1's
ramp is one more row). (a) XD-07's gate exit lands within 300 of (-1024, 6912) at 1,760-1,860 after 0.5 s and 3 s,
party and solo: pass. (b) the walk down and up keeps the feet within 32 of the ramp: pass. (c) **fails** in both modes:
pushing east at y 6,350 walks through the west cheek 802 units to the east cheek's inside, feet on the land at 1,313
under the 1,628 top; the east cheek and the foot at 70°/110° the same. Cause: the ramp's four side faces (bmodel 39)
are wound inward, so the one-sided collision lets the party in from outside: REQUEST to A1 (Map Studio `stairs` with
`ramp: true`). p11 stays claimed with the reproduction.

**Bridge end pads (`common/wild.py bridge_ends`, after X4's report).** A level deck on one of the land's 32 steps
takes its end pad 32 below (deck less 8 rounded back up to the deck and lay on it: X1's and X4's Nystor jetties, the
`faces.on_land` bridge kind of the last round); 32 is a step `bridges.step` allows. Every map takes it at its next
rebuild (X7, D1 in this round); X4's jetty at its next.

**X7** (sub-agent; installed with its bake 10:20:44). `x7/gen.py`: one `spot_ok()` for the marker rules and
`d142_enforce()` (29 moves, dungeon exits held to the floors), `HULL_CELLS` 2.7 (F63 spawns 20, 25 off the hull);
`x7/places.py`: the Fire Reflector a click on A3's hook (D-144), the orc outpost burns on one click of its fire, its
hides, fire and bones hidden and charred stakes and embers shown (D-152, `OUTPOST_CHAR`, `evt:outpost_state` on load),
Sablewing off his shelter's face; `gen_walk.py` and `tests/playthrough/xeen/85_reflectors.yml` click (the playthrough
not run). `xeen_x7` in `D142_EXITS`; `check_wiring_rules.py` `OUTDOOR_OPEN` empty. The broken wagon and hoard_bones_2
padded (X7's line out of `town_fit_pending.yml`). Checks: check_d85 0, common/d85 0, spawn_clear 0, audit 0, door,
wall, wild (no hull step), fit, reach 0; `faces.on_land` 4 (XD-18's cave-mouth floor, XD-05's gate sill; the ruins'
gone); walk, hostility, `x7_edges`, `hooks_fd04` pass. Captures `after/x7/`.

**D1** (sub-agent; installed with its bake 10:27:59). `d1/gen.py`: `d142_enforce()` (11 moves: three siege markers off
the north arrival, one off the east, seven off roads, lanes or paths); F63: the centipede marker off the bounds, Luna
in the middle of her stone ring (she stood in a stone), the barbarians south of their moved tent; F59: sardaj_tent_1
onto the camp's shelf (87.0, 23.9; it hung 578 over the gorge's lip), mill_beam sunk 26. D1's line out of
`town_fit_pending.yml`. Checks: check_d85 (5120) 0 with no road warning, common/d85 0 (26 exit warnings), spawn_clear,
wiring, fit, reach, wild, door, wall 0, audit and faces as before; walk, hostility, daily, `d1_hull_edge` pass; the
Sardaj camp keeps its question (Q-D12). D1 is **not** in `D142_EXITS`: DECIDE (its grove exits). Captures `after/d1/`.

Before stopping: `build_world.py --check` 0 differ, `stale_bakes --check` 0, `quest_stub.py` 19/19,
`check_sky_falls.py` 0 errors.

### F62 on P1–P4, the dungeon lid triage, D-163 (agent `xeen-fb4-dungeon5`, 2026-11-25 ~10:05–11:05; for A6, A7, A8, A2, S)

Scratch `output/xeen_fb/p4_dungeon5/` (`cyc.sh`/`post.sh` as dungeon4's, `REGEN_BUILD=1` for `regen.py --build`;
`quick.sh <key>` regen + stage + `check_floor_cross` + audit; `where.py <key> <check output> [--lids]` names the L4
platforms at each finding; `lidprobe.py`/`runprobes.sh` the lid probes; `topview.py` a height-coloured top view of a BLV).
Every rebuilt map: audit 0 errors, its playtests from the stage (exceptions below), installed, baked where profiled, MAW
reserve rerun. End: `xeen_balance.py --check` 0, `stale_bakes.py --check` 0, `build_world.py --check` 0 differ,
`key_npcs.py --write` (75 figures), `check_actor_heights.py` clean, `quests.py` 0 errors, `check_wiring_rules.py` 0,
`check_sky_falls.py` 0 errors.

**F62 on the planes (P1–P4, installed; no bake profiles).** New shared `level_generation/projects/xeen/common/planes/spans.py`
(X8's `landing_end`; `link_spans` level across each shelf, isle, terrace or sheet and sloping between, `ramp_spans`,
`span_top`, `deck_top`). `floor.cross` 25/28/6/1 → **0/0/0/0**; `floor.lid` 16/30/12/11 → 3/0/0/6.
- *P1* (rock causeways and ramps through the glass and crust shelves): causeways and the obsidian bridge in level
  landings (`_a`/`_b`) and a slope; every ramp level over its shelf (`_rampN_a`) before it runs down to the lava. Three
  ramps lay on a deck's line and crossed it: statue 330 → 270 (causeway_s at 335), arena 160 → 135 (the bridge at 168),
  330 → 298 (causeway_ne at 325). Causeway aprons follow the deck's heights; vents and the test plate sunk 4 and stand
  4 over a landing they lie on (vent 7 and the plate were coplanar with a landing). Left: the gate's lintel/gables'
  bottoms at 1,088 (stacked, out of reach) and the sunk test plate's bottom on a 254 glass face under it (NEXT: find
  that face; the plate is 4 high, the party steps on it). 9/9 playtests.
- *P2* (cloud-stone bridges; cloud skirts and wisps): bridges as P1; a skirt or wisp whose tilted top would meet an
  overlapping one, the island slab's underside or its first tier's ledge within 8 goes under it (`clear_band`); plates,
  the eye, the dais and the updraft sunk 4, plates over a bridge landing stand on it. `playtest_test` fails at step 49
  (actor 26, a roaming 11624, stands in the aerie stair): **the same on the installed map before this change**
  (NEXT, A6). 8 of 9 otherwise.
- *P3* (rock bridges of slabs): `span()` breaks its slabs at the landings' ends; plates, the dais, the dust shaft sunk 4,
  plates over a landing stand on it. 7/7.
- *P4* (colonnade walks): the walks in landings and slopes (`walk_z`/`slab_z` follow them: columns, flights); the test
  plate, the dais, the coral shelf, the ship's log sunk 4, wave plates over a walk's landing stand on it. Left lids: four
  column caps (700+ up), a sea stack's top (601), the hold's water (untouchable, its own top 2 over its bottom). 8/8.
- `tools/xeen/check_drops.py` now skips untouchable faces (FaceAttribute::Untouchable, cloud skirts the party falls
  through): P2's three "pockets" on skirts are gone; its void floor (-6,000, exit 7) is listed with its exit as X9's is.
  P4's three pockets (sea bed, terrace feet under water) are as before. Note: `oymap export` of a *staged* map reads
  the door records of the *installed* one, so face-indexed checks on a stage (`check_drops`, `check_floor_cross`) can
  mistake a face for a door leaf; P1's apparent lava pocket was that (gone once installed).

**The dungeon lid triage (task 2).** `check_floor_cross --all` lists 77 lids on 17 dungeons (before this round's
rebuilds). Each lid's floor was tested for reach on foot from the start (`check_drops`' reach) and, where reached, a
headless probe (`lidprobe.py`: the party put down on that floor beside the block, 0.6 s into it, then `walk_to` back
to where it started; fresh user data per probe, 25 probes):
- **Real stuck spot, fixed at the source (1 + 1 by the same shape):** XD-17's travel pyramid (its bottom on the terrace
  floor at 256): walking into its foot from the east the party slid 250 inside it and could not walk out. `xd17/gen.py`
  sinks it 8 (base -8, rise 712); the probe now walks back out. FD-01's dead pyramid on its plinth is the same shape
  (no free floor beside it for a probe): `fd01/geo.py` sinks it 8 into the plinth. Both rebuilt, installed (FD-01
  baked; XD-17's terrain-material files installed too: `install_stage.py` now takes `terrain_materials/<stem>_blv*`).
  XD-17 4/4 playtests; FD-01 7 of 8, `playtest_in` fails at step 17 (ends on D6) **the same on the installed map before**
  (NEXT, A8). Note for A1: the party still walks about 190 into a pyramid's steep foot (normal z ~0.5) before stopping.
- **Probed, not stuck (kept):** DD-04 2 (stair pieces), XD-02 2 (the turntable's rim), XD-03 4 (the gong, the throne
  room's daises), XD-04 3 (bedsheets on the beds), XD-05 2 (deck pieces), XD-16 5 (the dais's pieces), XD-21 2 (the
  catwalk's rail). Probed, the party walked off the edge instead (no wedge): XD-04 2 (the bridge at 1,920: its 24-high
  rail is stepped over and the party falls to the floor; check_drops finds no pocket, USER/A7 may want a real rail),
  XD-12 5 (posts on the lake balcony and well overlook; the party steps past them down 100).
- **Floor not reached on foot (kept: tops of furniture or roofs):** DD-08 2 books, DD-11C 3, DD-22 the couch on its
  dais, XD-01 the desk's top, XD-09 2 anvils' tops, XD-12 the journal, XD-13 the well's cap, XD-17 19 roofs (the
  houses' and the guild's stacked roofs, 320–1,600 up).
- **No free floor beside them for a probe (kept, small things on small tops):** DD-08 5 books on 96-high shelves, DD-19
  the Xenoc's chair on his dais, XD-02 the trestle deck's underside on its ramp, XD-03 2 span bottoms on rock.
- Open-air maps' lids (D7 317, P5 16, X9 6) are dungeon4's lists (stacked parts out of reach), not re-triaged.

**D-163, XD-04's children (done, as amended by the user).** New friendly rows (A2, `source/monsters.yml`
`characters`): 11930 "Goblin-eared boy" (stand-in PeasantM1 A, 133/26) and 11931 "Goblin-eared girl" (PeasantF1 A,
130/21); `build_world.py` (only these rows). Bindings (S, `models/actors.yml`): Xeen copies of MM9's children
installed with `tools/install_model.py --world xeen` from `assets_source/worlds/mm9/models` (D-44; the boy's cook
sidecar copied): `xeen_peasantboy.glb` skin `pboy_e` with `xeen_peasantboy_elfears.glb` on `Bip01 ElfEars` (MM9 73),
`xeen_peasantgirl1e.glb` skin `pg_g1e` (MM9 74), MM9's clips and script clips. XD-04 L4: child 1 (name, NPC 4053,
group 11 kept) and child 3 on 11930, Rosebud (2) and child 4 on 11931; `playtest_hostility` asserts the new ids.
Rebuilt, installed, baked; MAW reserve (spawn points only); audit 0 errors (26 warnings as before); playtest,
playtest_m4, playtest_hostility pass. Captures (real game, the pin's pose): `xd04_cap/p5_pose.png` (caged),
`p5_cage_hoisted.png` (the boy under his hoisted cage, elf-eared), `boy_talk_low.png` (his talk: portrait, "Don't stare
at my ears!", Ears). Replied on XD-04 p5. The first try on MM6 peasants at 0.65 (the decider's version) was superseded
before install. **Not done:** new skins (the user's later note: ginger hair and freckles for the boy, each child
different): the boy's head colour is MM9 boy e's (brown hair), NEXT.

**Not done (budget):** XD-12's two `sky.low` ends, DD-07's 8 ledge-shot errors, D7's coplanar warning at (-27912,
-11295): as dungeon4 left them.

### D-160 (X4 p11), D-161, D-162, X1 p30, the hull steps, the last town_fit sites (agent `xeen-fb4-outdoor3`, 2026-11-25 ~10:35–11:45; for A1, A5, A6, A3)

Scratch `output/xeen_fb/p4_outdoor3/` (`tools/cycle.sh`, `install_check.sh` (passes the kept groups to both D-85
checkers), `tour.sh`, `tools/ramp_normals.py` (each face's normal against its model's middle)); captures `after/`;
the sub-agent's D2, D3, D5, D6 work `sub_d/`.

**D-160, the studio ramp (X4 p11).** Cause: Map Studio's `stairs` with `ramp: true` (`OutdoorThings.cpp`
`raiseStairs`) wound its two cheeks and two ends inward (the installed X4 bmodel 39 and D1 bmodel 138: `+----`), so the
one-sided collision let a party walking at a cheek in under the top. Fix at the source: the sides run round the top's
outline as a prism's; the doctest "forms: a ramp is one sloping slab ..." checks every face looks out. oymap released
10:39:18 (private link `oymap/oymap_1039` first; oymap_tests 536/536). Sites: the 2 Xeen ramps (X4 castle lane, D1
Kalindra's ramp), both rebuilt (`+++++`); the building stair's ramp and the cave ledge were built with explicit facings
and were right. Outside Xeen (change at their next build, not rebuilt): mm6_outd3 4, mm7_7out03 2, mm6_oute3,
mm8_out02, mm8_out06 1 each; no MM9 or Hesper map uses one. `tools/xeen/ramp_test.py` works in each ramp's own frame
(D1's row; `tests/scenarios/xeen/d1_ramp.yml`, no cheek pushes there: its cheeks stand under a step over the land), its
slant walks into the foot are short and assert the top inside the footprint (a long slant walk steps off the side onto
the land, which the old assertion took for "under"), and it clears hostiles before the walks (in solo mode a monster
closed in during the stations). `x4_castle_ramp.yml` and `d1_ramp.yml` pass in party and solo mode, Blink included
(the cheek pushes failed before). p11 resolved (`after/x4/01-01-p11.png`: a camera at the pin's pose is now inside
the solid ramp; `03-03-ramp_foot.png`).

**X4, X2, X1, X6 rebuilt** (A5's installer, bakes 10:42:27, 11:03:51, 11:09:42, 11:15:19): the hull steps
(`rim.hull_step` none on any, X6 had 17), the jetty end pads one step down (X4 `faces.on_land` 0; X2's jetties
smaller but still there), X2's Temple of Yak skull piles on its level plot ((60.3, 99.3), (63.7, 99.3); yak_dress_4
stood in the dip before the door), X6's strongbox (95.0, 30.6) off the swallowed wagon's foot (its own pad at 1,792
cut 42 under the wagon). Door, wall, wild, fit, reach, check_d85, common/d85 0 on each; every playtest passes, and
`x1_hull_edge`, `nystor_boats_back`, `x6_sphinx_solid`. **X1 p30** resolved with the post on its jetty and Rudd's boat
window (`after/x1/01-p30_post.png`, `02-p30_boat_window.png`: "1 day to Rivercity and Lake Darzog for 16 gold").

**D-161, D1** (bake 10:50:25): `xeen_d1` in `D142_EXITS`; the grove's markers 3-7 are five placed packs (12
Arachnoids, 3 Queens, groups 6-10) in its clearings, 2,000+ from the rope and 4,096+ from the adit, DD-05 and the
pyramid; markers 14, 15, 21 and 6 moved by `d142_enforce` (the grove's two remaining markers end up at (77, 26) and
(59, 71): nothing nearer clears 5,888 from the rope, DD-05 and the adit); the saboteurs at the cut bridge's east end
(4,966 from the outfall, was 3,033). Kept for the rope only: groups 3-5 (Electrapedes) and 6-10, NOTES line.
`common/d85.py` takes `--kept-group`. Checks 0 (12 KEPT lines at the rope), walk, hostility, daily, gate lanes pass.

**D-162, D2, D3, D5, D6** (sub-agent; bakes D2 10:45:30, D3 11:00:20, D5, D6 after): D2 (11 moves, ogre groups 3/4
past 4,096 from DD-13, kept groups 1, 2), D3 (32 moves, the crags sunk and grown, `faces.on_land` 10 → 3), D5
(`POLY_SPOTS`, 9 moves, `on_land` 10 → 2) in `D142_EXITS`; D6 rebuilt with 6 moves and its two town_fit sites, but
not in `D142_EXITS` (DECIDE: Alamar's gate robots and the lake's fire elementals). `common/d142.py` `hull_reason()`
for every map. `town_fit_pending.yml` now holds no map. All their playtests pass.

**Wording (A3), playthrough.** `source/npcs/x7.yml` `orc_outpost.where` and `source/quests/m37.yml`
`reflector_fire.where` say a click (D-144/D-152); `build_world.py --only gen_quests` changed only those two
`quest_hooks.yml` lines. `tests/playthrough/xeen/85_reflectors.yml` passes (run.py notes its checkpoint predates the
D1, D5, D6, X1, X4, X5 rebuilds; the game reset them on entry: a chain rerun from the segment that last left them would
refresh it).

**End checks.** `build_world.py --check` 0 differ; `quests.py` 0 errors; `quest_stub.py` 19/19; `check_sky_falls.py`
0; `stale_bakes --check` 0; `check_wiring_rules.py` 0; `towns.py --strict` 1 error: D5's Doom barrier `walls.open`
(a 32-wide slot at the curtain's east end, (98.05, 23.86), the same on HEAD). Left: `check_spawn_clear` X1 3, X2 9
(hull clearance, an actor in X1's temple, X2's great bridge and Danulf's ring: outdoor's before-list); the known
`on_land` kinds (X1 10, X2 5, D2 1, D3 3, D5 2).

### D-163 skins, XD-04's bridge rail, XD-12 `sky.low`, DD-07 and XD-12 ledge shots, P1's lid, P2 and FD-01 tests (agent xeen-fb4-dungeon6, 2026-11-25 ~11:10–12:30; for A2, S, A7, A8, A6)

Scratch `output/xeen_fb/p4_dungeon6/` (`cyc.sh`/`post.sh` as dungeon5's). Every rebuilt map: audit 0 errors, its
playtests from the stage, installed, baked where profiled, MAW reserve rerun. End: `xeen_balance.py --check` 0,
`stale_bakes.py --check` 0, `build_world.py --check` 0 differ, `key_npcs.py --write` (75 figures),
`check_actor_heights.py` clean, `quests.py` 0 errors, `check_wiring_rules.py` 0, `check_sky_falls.py` 0 errors.

**D-163 skins (S, A2; done).** Ramps only, no new paint: `level_generation/creatures/xeen_children_claude/`
(`skins.py` masks and ramps, `add_variants.py` appends variants to the MM9 sources, `fix_variant_maps.py` far maps,
`install_model.py --world xeen`). The goblin-eared boy (`xboy_ginger`) matches npc 4053's portrait: boy e's freckled
head with its hair ramped bright copper-ginger by a new hair mask, the ears attachment tinged goblin green, a grey-brown
homespun vest over undyed linen. Each child differs: child 3 `xboy_dark` (boy b's dark hair, moss-green vest), Rosebud
`xgirl_rose` (madder rose), child 4 `xgirl_flax` (flaxen hair by a head mask, woad blue). One descriptor carries one
skin, so child 3 and 4 have rows of their own: 11932 Goblin-eared boy, 11933 Goblin-eared girl (`source/monsters.yml`
characters, `picture: Xeen Goblin-eared boy 2 / girl 2`; `build_world.py --only gen_monsters`, which also wrote the
missing `relations.yml` factions of 11930/11931). XD-04 rebuilt (with the rails below), baked; playtest, playtest_m4,
playtest_hostility (asserts 11930–11933) pass. Captures: `xd04_cap/boy_talk_before_after.png` (his talk, portrait
beside him), `xd04_cap/after2/` (each child in its cage; the boy at the p5 pose with cage 1 hoisted). Replied on XD-04
pin:p5. Not done: the portrait's sulky mouth (the head paint smiles; a texture change, not a ramp).

**XD-04's Alacorn bridge (A7; done).** The plank bridge at 1,920 had two 24 kerbs: stepped over (step-up 50), the
party fell 1,920. Now 96 rails, as the balconies' sills (the map's own rail height), plus a 96 rail on the landing's
seven open edges over the cauldron (it had none). dungeon5's probes 345/351 stop on the bridge now (z drift 0).

**XD-12 `sky.low` (A8; done).** Faces 2056/2057 were the east battlement's reveals in the keep wall's 256 thickness,
drawn as sky down to the 256-deep sill (3,184). `xd12/shell.py`: `open:battlement_e` 288 high over its sill with stone
reveals and a sky lintel; the first try (full-height stone reveals) stood up as two bare posts 1,000 into the sky
(`xd12/sheet.png` vs `sheet2.png`). 2 -> 0.

**Ledge shots, D-132 (A8; done on DD-07 and XD-12).** DD-07's 8 errors: the well foot's three Floating Adepts; every
post in the well's foot 48 or more off its middle grazes a railed window, and the middle is in the arrival's sight
(`arrival.hot`, tried on an edited scene without rebuilds: `dd07/try.py`). They keep the ring1 gallery now (`dd07/gen.py`
PLACED, ids kept): 8 -> 0, arrivals 0. XD-12 had 2 errors on HEAD's map as well (marker 15, the library stair hall,
over the flight's edge): `xd12/dress.py` `spawn:library_stair` 512 south: 2 -> 0. World sweep now: **6 errors on
DD-19, DD-21, FD-04, XD-22** (not touched; D-132: each at its next rebuild).

**P1's 254 glass face (A6; done).** It was the test plate's own bottom: the plate straddles the Crucible's halves (east
top 256, west 258) and was sunk 4 under the west half only, so its bottom lay 2 under the east half's top. `p1/gen.py`:
sunk under the lower half. `floor.lid` 3 -> 2 (the gate's lintel and gables, out of reach); 9/9 playtests; installed.

**P2 `playtest_test` step 49 (A6; the test).** Not the map: a Lesser Air Elemental of group 5 (actor 26, posted at
(720, 1114), outside the test's 3,000 clear) roams since the 3.3 AI and stood on the Stair of Wind after the reload.
`p2/gen_playtests.py` clears the field before each walk through the curtain (the test is the curtain's, not a fight).
Passes on the installed map.

**FD-01 `playtest_in` step 17 (A8; the test).** Not the map: D6's stair hatch shows F16's entrance window (screen text
5062) before the move, as D6's own walk test expects; FD-01's test still assumed D-72's "no window" and closed it as a
stray dialog, so the party stayed on D6. `fd01/tests.py`: asserts the window, OK, then the move. Passes.

**Not done:** D7's coplanar warning at (-27912, -11295) (no D7 rebuild this round; not cheap without one).

### D-164 (D6), D5's Doom barrier, X1/X2 spawn clearance, the `on_land` list (agent `xeen-fb4-outdoor4`, 2026-11-25 ~11:20–12:00; for A6, A5, A1, tools)

Scratch `output/xeen_fb/p4_outdoor4/` (`tools/cycle.sh`, `tools/install_check.sh` from outdoor3's; `spawn_try/try.py`
moves actors in a scratch copy of an installed scene and runs `check_spawn_clear` on it; D6's fight runs `d6/fight/`).
Built with oymap 10:39 (no oymap rebuild), game 09:24.

**D-164, D6** (installed with its bake 11:41). `d6/gen.py`: robot groups 14-19 on the north half of Alamar's mesa
(east flank (58.6, 44), north rim (54.8, 39) for the Annihilators, (47.4, 39), (49.3, 37.9), west flank (41.6, 44),
(43.2, 42.6)); 11, 12 stay; 13 back on the top at (57.9, 42.4) (at (58, 40) one robot stood in the moat at 1,536 and one
on the cliff at 2,089). 16 Patrols + 2 Annihilators, all on the top (2,264-2,299), every spot a cell inside the edge.
`ROBOT_CLEAR` 5,888 / `ROBOT_AIM` 6,400 from the gate and the pyramid (drawn point and built cell) in gen.py; the
`clear` entry stays 2,400 for markers. Nearest robot 6,586 from DD-17's gate / FD-01's stair (was 3,118), 9,291 from
the pyramid (was 2,731). `HATCH_CLEAR` replaced by `LAVA_CLEAR`: each lava dweller's home 6,144 + spread × 512 from the
hatch, pyramid and gate; group 1 in the moat's east arm (63, 46), group 2 in the west arm (36.5, 46) spread 0.8 and its
Elemental (37, 43.5), groups 3, 4 on the lake's north shore (67.9, 57.8), (66.8, 58.5) spread 0.5 and their Elementals
(69.5, 57.6), (68.8, 57.3) (the decider's (68, 58) and (66.5, 58.6) fail by 48 and 15 from the hatch and the drawn
pyramid point: the band is x 67.6-68.2 at y 57.8). 14 kept, leash 1,024. Nearest 6,275 from the hatch, 6,598 from the
pyramid. `xeen_d6` in `check_arrivals.D142_EXITS`; the local `CA.D142_EXITS.add` gone; no kept groups.
`check_reach.yml` keeps groups 1, 2, 4 (group 3 stands on the shore). `gen_hostility_d6.py` read a stale
`output/studio_cal/d6/build` (yesterday's) and kept the old homes: it now takes a scene (argv 1, else the installed map's).
Checks: door, wall, faces, wild, fit, reach 0, `check_d85` 0, `common/d85` 0 FF and 0 FFW lines; walk, daily,
hostility pass. **First fight** (headless, an immortal level-30 party set down at each arrival, every placed hostile
logged 60 s; `d6/fight/gate.log`, `pyramid.log`, `analyse.py`): at the gate the nearest robot stays at 6,586 and none
targets the party in the minute (inside D-15's 4,096-8,192; no ambush, so no mesa leash); at the pyramid the nearest
lava dweller stays at 6,597. Captures `output/xeen_fb/p4_outdoor4/d6/tour/` (`02-mesa_from_nw_high.png`: the garrison
on the rim and the west flank; `04-lake_north_shore.png`: the elementals on the shore).

**D5, the Doom barrier** (installed with its bake 11:42). Cause: the end frames stand on the hull's line (y 24.2) and a
walkable ledge (y 23.84-24.3) runs between the hull and the rim's cliff; from a hull gap (x 85-89) it ran past the east
end frame (the 32-wide slot at (98.05, 23.86)). `d5/gen.py`: `thing:barrier_block`'s line runs on north to y 23.2 at
both ends, into the cliff. `wall_check` 0; `towns.py --strict` **0 errors** (2 known villager warnings). Walk and
hostility pass. D5's `check_faces` keeps 4 errors that were there before (broken pyramid `faces.back_to_back` 1,
`shell.open_edge` 1; the basin's 2 `on_land`).

**X1, X2 spawn clearance** (installed with bakes 11:53, 11:56): `check_spawn_clear` **12 → 0** (whole world 0).
Cause of the four marker errors: X1's and X2's `d142_enforce()` never passed `also=d142.hull_reason()` (the other maps
do), so circles at the bounds were never moved. Now: X1 (hull 3.0) hill orcs 9 (52, 20) → (32, 27), road orcs 11 → (100,
23), the dead 4 → (23, 101); X2 rangers 1-4 and ogres 5 a few cells in. Shared fix in `common/d142.py standard_ok()`:
the districts' plot houses count as buildings (it read only `structures`; X2's moved rangers 5 landed on farmstead 1).
Placed actors: X1's Plague Cult member 4052 out of the temple's nave to (60.4, 46.4); X2's four Great Bridge guards
0.15 in from the parapets, Danulf to (56.5, 81.8) north-east of his altar (5,999 from the sprites' circle, D-85), the
west lake dragon a cell east (20.5, 58), the ogre wanderer to (30, 20.5). `gen_lake_dragons.py` rewrote both dragon
tests. Every check 0 on both; X1 walk, hostility, `x1_hull_edge`, `x1_start_nothing_in_reach`, `nystor_boats_back`; X2
walk, hostility, `danulf_ring`, `lake_dragons`, `lake_dragons_leash` pass. `tests/scenarios/xeen/x2_lake_dragon_leash.yml`
(A1's repro) fails: its dragon homes and shore pose are from before outdoor2 moved the north-west dragon (stale, not
this round's change; the generated L4 copy of the test passes).

**Faces lying on the land** (no fix; no oymap rebuild). The bridge and jetty ends: X2 `great_bridge`, `medin_jetty`,
`island_jetty`; D2 `log_bridge`; D3 `wrath_bridge`. Cause: `common/wild.py bridge_ends` pads the land at a deck's end to
the deck less `BRIDGE_SINK` (8), but the studio's land comes in steps of 32, so on a deck at a multiple of 32 the pad
rounds back up to the deck and the end lies on it. `DECK_LIFT` (lifting the deck) broke the ends' fit on X2; the
candidate shared fix is `BRIDGE_SINK = 32` (one land step under the deck, X4's jetty pad, which took X4 to 0), with
`town_fit_check bridges.step` run on every map that has a bridge, then rebuilding X2, D2, D3 and any map whose pads move.
Not bridge kinds (each its own piece): X1 lane steps 2 (smith, bank), culvert grate/revetment/cap 4, mine portal 2,
shaft head 2; X2 ogre lair mouth 2; D3 `sc_guild_light` and `vespar_ruin`; D5 the basin 2.

**End checks.** `build_world.py --check` 0 differ; `quests.py` 0 errors; `quest_stub.py` 19/19; `check_sky_falls.py`
0; `stale_bakes --check` 0 (an XD-12 bake was stale at 11:43 during the dungeon agent's work; 0 at 11:58);
`towns.py --strict` 0 errors; `check_spawn_clear` 0.

### D-175 (agent xeen-fb4-tests, 2026-11-25 ~12:05–12:20; for A1, tests)

The stale `tests/scenarios/xeen/x2_lake_dragon_leash.yml` (the north-west dragon's old home) is deleted.
`tools/xeen/regressions.sh` now runs `devdocs/xeen/briefs/x2/L4/playtest_lake_dragons_leash.yml`, which
`level_generation/projects/xeen/x2/gen_lake_dragons.py` writes from `gen.LAKE_DRAGONS` on every X2 rebuild. A1's
keepStepOnLeash note moved into the generator's header for that file (and its stale `output/studio_cal` path fixed);
rerun: only the header changed, `playtest_lake_dragons.yml` byte-identical. STATUS.md merge point 24 points at the
L4 file. Other mentions (A1.md, A5.md, this file's earlier notes) are historical log lines, left as they are. Run on
`build-xeen` (headless, absolute path; a relative path fails to load): `xeen.x2.l4.lake_dragons_leash` passed.
No X2 map file touched.

### D-170 studio rules (agent xeen-fb4-studio5, 2026-11-25 ~12:15–12:50; for A1, A5, A6, decider)

Scratch `output/xeen_fb/p5_studio/` (`oymap/build_oymap.sh`: heavy.sh 24, `cpp_build.lock`, private link
`oymap/oymap_work`; `tools/cmp_maps.sh`: each outdoor map's L4 project built under its lock with the released 10:39
oymap and with `oymap_work`, `tools/model_diff.py` on the two exports, `check_faces.py` on the new build with a private
cache; `tools/others.sh`: the non-Xeen studio projects, from Hesper's `projects.sh`). **oymap not released**: one
oymap_tests case fails in the shared tree, in openyamm-81's new GLB import (`tests/GlbModelTests.cpp:186`, "slivers and
tiny faces are refused"; files 12:31–12:35, untracked); 547/548 pass, every other case and the 4 new ones included.
openyamm-81 told; the release waits for that case (or its OK). Release = `oymap_work` relinked from the tree, then
`openyamm-studio/build-xeen/oymap`.

**The rule** (`core/OutdoorLowering`): `LoweredOutdoorMap::groundRangeUnder(polygon)` (the game's triangles, exact:
corners, crossings of cell lines and diagonals, nodes inside) and `outdoorClearOfLand(lowered, outline, top,
highest)`: a level face stays at `top` when the land under it is all ≥ 4 under or ≥ 8 over it; else 4 over its highest
land (up to `highest`), else 8 under its lowest. Nothing is deleted.
- Buildings (`OutdoorBuildings.cpp`, `raiseOutdoorBuilding(..., pLand)`): a porch's slab (`floor`) and a ruin's gone
  course (`RuinCourse`) stand 4 over the land beyond the levelled plot. The "xvbeam sills" were all porch slabs (X3
  temple, D3 Guild of Light, D4 house 7) and D3's roadside ruin course.
- Stairs (`OutdoorThings.cpp raiseStairs`): each tread the hillside reaches stands 4 over it, at most 4 under the
  next tread; else 8 under the land (X1's two lane steps were the top tread, X5's monastery stair three treads).
- Gate leaves (`raiseWall`, `wallEndCovered`): a `kind: wall`'s free end makes no end face where an upright face
  covers it: another wall's gate cheek (the leaf no thicker or higher than that wall), another wall's free end met head
  on (as thick and as high or more), or a building part's wall square to it reaching from the foot to the top.
- Tests (`tests/OutdoorTests.cpp`, "D-170:" ×4): the range and the rule; a porch over rising land; treads up a
  hill; a double gate's leaves in a gate (0 end faces) beside a free wall (2).

**Sites** (scratch builds vs the installed export): fixed by these rules X1 lane steps 2; X3 temple porch 1; X5
monastery stair 3; D3 `sc_guild_light` 1, `vespar_ruin` 1; D4 `lk_houses#7` 1; D3 gate leaves 3 of 3; D1 gate leaves 6
of 13. Also changed (same rules, no finding before): X1 watchtower, X5 edge_watch, X7 pony_shed, D1 mill_burnt (ruin
courses/porches); X6 yard gate leaves ×4, D1 wall_ne/wall_nw, D3 city walls ×3 and south_gatehouse, D6 np walls (end
faces covered by a gate cheek or a wall met head on). Left: **D1's other 7 gatehouse pairs** (the `arch` part's ends on
the towers ×5, `north_gate_lintel` on the towers ×2: building parts abutting, no rule this round; cheapest fix in D1's
generator: the arch part and the lintel 16 longer at each end, into the towers); **cave mouths** (X1 mine_portal, X2
ogre_lair, X5 xd10_north, X7 xd18_mouth; D4 dd23_lair gone in the current L4): the shell's flat crest (inner points
capped at `crest`) is crossed by a hill kept over the crest at the back edge; no ≥4/≥8 rule fits a face that the land
crosses (DECIDE below); bridges, jetties, X3 causeway, the X1 culvert, shaft head, X7 XD-05 gate (outdoor's). D2's L4
did not build at 12:44 (`roads[2].link: link:log_bridge`, outdoor5's edit in progress): not compared.

**Outside Xeen** at their next build: only `mm6_outd3` (calib_ironfist.odm; its stairs/gated walls). mm6_oute3,
mm7_7out02, mm7_7out03, mm8_out02, mm8_out06 and the examples build byte-identical; Hesper's cinder and the
`glb_gate`/`odm_v2_vale` examples do not build on the 10:39 base (not compared); no MM9 studio map.

DECIDE (caves): (a) cap the shell's inner points a step under the crest so only the back edge reaches it (no level
crest face; a hill crossing the crest becomes a sloped crossing line, which `faces.on_land` does not count), or (b) a
buried mouth raises the land over its whole crest (crest + 32 from the tunnel's end back), or (c) keep, listed in
`check_faces.yml`. Cheapest to reverse: (c) now, (a) next studio round.

### D-170 rebuilds (agent xeen-fb4-outdoor5, 2026-11-25 ~12:20–13:30; for A5, A6, A1, tools, openyamm-1a)

Scratch `output/xeen_fb/p5_outdoor/` (`tools/cycle.sh` build, `tools/install_check.sh` gated install with bake and
checks, `tools/run_map.sh` the whole per-map run ending in a second `regen.py --check`; each map's `run.out`;
`tools/upfaces.py`, `hits.py`, `probe_bridges.py` read a model's level faces and its on-land samples). Built with oymap
12:48 (studio5's D-170 rules), game 09:24.

**`common/wild.py bridge_ends` (D-170).** Level decks: the end pad at the highest 32 step ≥ 4 (`BRIDGE_UNDER`) under
the deck, the deck's width + ½ cell a side; an end meeting a terrace at the deck's own height takes no pad and stops 16
short of the terrace on the water side (the Great Bridge, both ends). Every deck: each node of a cell the deck covers
that stands at or over the step under the deck there is cut to it, one slope-0 pad per node (stable from build to
build; the decider's "pad under every over-land stretch" taken as "no land within 4 of the deck": filling the Great
Bridge's 640 banks to 992 was not meant). Land-following decks: the dry nodes of the end's own cells levelled at their
lowest step, no slope, nothing further (a 1.5-cell sloped pad dented Vertigo's square 32 under X1's town bridge and the
start stood beside the dimensional pedestal's foot: `x1_start_nothing_in_reach` failed; fixed and passing); `pad_beyond:
1.5` on a bridge runs it 1.5 cells on up the bank where a road graded after the terraces lifts an end-cell pad
(D2's log bridge, D3's Wrath Bridge). Water nodes come from the sketch with the studio's two-cell river width
(`_wet_node`); land-following ends read only the sketch's water (an end read once as over water flipped X3's causeway).
Height points were tried to pin pads against road grading and dropped: a river that follows the land follows them.

**`tools/xeen/check_faces.py faces.on_land`.** Compares each face's plane height at each sample (the mean of a
sloping deck lay on the land: X3's causeway, D3's Wrath Bridge were false) and, by D-176, skips land of slope ≥ 0.35
(a seam, not a flicker: the cave crests, X1's culvert and shaft head, X7's XD-05 gate); self-test cases for 0.44
(not counted) and 0.125 (counted). `check_faces.yml` holds 7 reasoned lines for findings on the installed maps before
this round, outside D-170 (D1 Kalindra's ghost stages, its gate shimmer, wall_ne/jetty bastion, the burnt mill's open
shell, cv_weapons' porch beam ends; D3 spring_fall's lip; D4's isle tower crown).

**Singletons and sites** (generators): X1 culvert `KIT.SunkenEntrance(bank=576)` with revetments to 55.15 and the
guild lane ending at 58.5, shaft head `height: 256` (sub-agent); D5 Last Water on a level pad at the pool, the broken
pyramid's apex standing on the 1600 shelf (back-to-back and open edge gone); X7 XD-05 gate depth 416 (sub-agent);
D1 gatehouse arch and both lintels 16 into the towers, wall_nw 16 into the west tower, Lucio's pier from the deck's
edge (48.4); D2 log bridge's east end out of the Glimmerbrook's band to (53.5, 46.06), `raise: 24`, `pad_beyond`;
D3 Wrath Bridge `raise: 24`, `pad_beyond`; D4 Snow River bridge `rise: 64` (the river's own water nodes fall 64 a
cell under it; no terrace reaches them); X2 lake path's last stretch on y 62 (graded along y 61 it lifted Medin's
jetty pad to 704), the D-167 nest's dead branches at r 0.8 (at 0.74 they stood in the rim's stones, props.in_wall).

**Installed** (gate: `check_faces --check` 0 on the build, town_fit with `bridges.step` 0; then door, wall, faces,
wild, fit, reach, check_d85, common/d85 0, every playtest passes; second regen identical): **X1** (all six extra
scenarios pass: q-c20, q-c17, hull_edge, start_nothing_in_reach, nystor_boats_back, bridge_walkers), **X2** (q-c17
passes). openyamm-1a's roots `output/xeen_d167/root_x1_b`, `root_x2_e` deleted. **X3** and **X6** installed, checks and
playtests pass, second regen differs: X3 from the causeway end flip (fixed in wild.py, X3 queued again), X6 from
`level_pads.py` (a tent pad reads the installed land at its centre: 2688 → 2656; REQUEST). **D2** first installed on
the old binary (passes), its new-binary run stopped at the gate (log bridge end on the road's grade) and is queued
again with `pad_beyond`. D1, D3, D4 stopped at the gate before their fixes above and are queued again; X5, X7, D5, D6
were running at the time of writing: each map's result is its `output/xeen_fb/p5_outdoor/<map>/run.out`.

**World on-land count** (installed, the fixed checker): 36 at the start → 14 before these installs (checker fixes and
D2) → X1, X2, X3 at 0.

Addendum (13:25): **X5** and **D6** installed with their bakes; second regen identical on both. Two checks are not 0,
and whether either was already failing before this round is not checked:
- X5 `check_d85` 1 error: NPC 4502 (actor 120) has monsters within 5,120.
- D6 `wall_check` 2 errors: the gap between np_wall_w and np_wall_e at (91, 90), `walls.loose_end` and `walls.slit`.
Both are open for the next outdoor session. D4 stopped at the gate again because the run started before its kept line
was added; it is queued again.

### D-170 rebuilds, finish (agent xeen-fb4-outdoor6, 2026-11-25 ~13:20–14:10)

Took over outdoor5's lanes (`output/xeen_fb/p5_outdoor/tools/run_map.sh`, same gate) and its scratch; mine under
`o6/`. oymap 12:48, game 09:24.

**Every map installed with its bake and its gate passed** (check_faces --check 0 not kept, town_fit with
`bridges.step` 0, door, wall, wild, fit, reach, check_d85, common/d85 0, every playtest and extra scenario passes,
second regen identical; installed .odm times): X1 13:05, X2 13:08 (outdoor5), X3 13:49, X5 13:17, X6 13:14, X7 13:22,
D1 13:44 (+ d1_ramp), D2 13:40, D3 13:34, D4 13:26, D5 13:28, D6 13:20. Each map's record: `output/xeen_fb/p5_outdoor/<map>/run.out`.

- **D2 log bridge** (stopped at the gate twice: the deck's east end on the land at 1,302–1,311). Cause: the slanted
  deck (49.2, 49.4)→(53.5, 46.06) ran its east end beside the Glimmerbrook upstream, whose water falls 64 a cell north
  to south (1,312 at y 46): wherever the end was put, its last flat stretch lay on that water and on the caravan road's
  bed, which the studio grades after the end's pad. Height points pinning the end's nodes were tried and moved the
  brook (outdoor5's finding again). Fix in `d2/gen.py`: `LOG_BRIDGE = [[48.5, 48], [53, 48]]`, square across the
  brook, the caravan road through both ends; the east end on the node line x 53 (the road lifts (54, 47) to 1,344),
  `raise: 24` (at 16 its north corner lay on the road's grade); no `pad_beyond`. Gate clean, playtests pass.
- **X5 check_d85**: Mayor Randon (NPC 4502) among Q-C6's waves is D-87.1 (unkillable by `evt:randon_load`); the same
  line errs on HEAD's install. `x2/check_d85.py --kept-giver N` reports such a giver as KEPT (a ranged disabler within
  5,888 still errs); `x5/v.sh` and the lane's install check pass `--kept-giver 4502`. X5 0 errors.
- **D6 and D1 wall_check** (2 + 2 errors, new this round, 0 on HEAD's installs): false findings after the studio's
  D-170 end-face rule. D6: np_wall_e meets np_wall_w head on at (91, 90); the studio dropped np_wall_e's end face, so
  wall_w's face no longer met a back face (`loose_end`) and wall_e's merlon end faced wall_w's 32-higher end across a
  crenel (`slit`). D1: wall_nw's end at the jetty bastion kept only a merlon end over the bastion's top (`loose_end`),
  and its end 16 into the gatehouse's west tower (outdoor5's back-to-back fix) sits in the tower's lower storey, a part
  under the upper storey's floor, where `contains` finds no solid (`step`). `tools/xeen/wall_check.py`: a sample is
  covered by the solid 10 past it; an end with only merlon or set-back faces is covered when the piece's solid stands
  past it; a sample shut in on all sides by a building (`enclosed`) is covered. World wall_check 0.
- **Build-twice drift** (task 2). `common/level_pads.py` read each pad's height from the installed land at the
  thing's centre; X6's prospector's tent pad is cut by its lane's road bed (graded after the terraces), so the next
  read was 2,656 for 2,688. Now each pad's height is read once and kept in `common/level_pad_heights.yml` (map →
  thing → `at`, height) while the thing stays at its `at` (moving it, or deleting its line, reads the land again);
  stale lines are pruned; writes go under `output/xeen_locks/level_pads.lock` (the lanes regenerate several maps at
  once; `level_pads.yml` now written the same way). The same drift showed on D3 (second regen differed after its
  install): the Wrath Bridge's land-following end pad read the deck's own node cuts under its end (1,024 → 992) and a
  cut node the road bed had lowered dropped out. `common/wild.py bridge_ends`: land-following end pad heights
  (`<bridge>#<end>`) and the under-deck cut nodes (`<bridge>#cut`, kept while the line stays) in
  `common/bridge_end_heights.yml`. Both files seeded from the installed L4s (`o6/seed_*.py`), so no installed map
  changed: X6 needs no rebuild (its installed L4 has 2,688) and D3 none. Second regen identical on X1, X2, X5, X6, D3,
  D4 with the new code; every later lane run identical too.
- **outdoor5's DECIDE** (task 3): "a pad under every stretch of deck over land" read as "no land within 4 under the
  deck", per-node cuts, not filling the banks to a pad (the literal reading raised the Great Bridge's banks 640 → 992).
  Kept: cheaper, and the on-land check is clean on every bridge with it.

**End checks** (14:00): `stale_bakes --check` 0; `build_world.py --check` 0 differ (no trainer_places regen needed);
`quests.py` exit 0 (17 OPEN, as before); `quest_stub.py` 19 passed; `check_sky_falls` 0; `towns.py --strict` 0 (XD-17
villagers WARN, pending its lane); `check_wiring_rules` 0 over 82; `xeen_balance --check` 0 (82 maps).
**World on-land count: 36 at D-170's start → 0** (`check_faces.py --quiet`, every Xeen map; no `faces.on_land` on any
map). What `check_faces.yml` still keeps on the outdoor maps is outside D-170 (outdoor5's 7 lines: D1 Kalindra ghost
stages ×8, its gate shimmer, cv_weapons' porch beams, the burnt mill's open shell; D3 spring_fall's lip ×2; D4's isle
tower crown). D1's 13 gatehouse gate-leaf back-to-backs: 0.

### D-174 playthroughs and regressions (agent xeen-fb4-tests2, 2026-11-25 ~14:05–14:40; for A1, A3, A5, A6, tests)

Cut short by the coordinator at 14:38: promotions, `regressions.sh` and further side-quest fixes went to xeen-fb4-promo,
xeen-fb4-regress and xeen-fb4-side. Scratch and probe logs `output/xeen_fb/p5_tests/`.

**Binary.** `build-xeen` rebuilt 14:09 (openyamm) / 14:14 (unit tests) under `cpp_build.lock`, heavy.sh 24: built clean
with the shared tree's uncommitted game/engine/core edits (about 120 files of other sessions: Implants skill, Web of
Worlds, terrain materials, sky/weather, coop, scenario runner, indoor collision ...). `openyamm_unit_tests`
3213/3213 pass (`unit.log`). Every run below is on this binary.

**Main chain** (normal, checkpoints refreshed 14:14–14:36): 52 segments, **50 pass as written, 2 fail on map faults**
(15, 93); both pass to the end in a probe copy that steps around the fault, and those probe runs wrote the 15 and 93
checkpoints so that the chain continues (`15_probe.log`, `93_probe.log`). Two stale tests fixed (17, 39).
- **15 Ogre Lair, real fault (X2, A5; F59 `common/level_pads.py`).** The party leaves XD-27 to (-20992, 17155, 1248)
  and lands at z 1,137.9 (assert z 1,150–1,350). X2's land there fell from 1,248 to 1,137: the F59 auto pads of the
  lair's campfire and two skull pillars (`lair_dress_1/5/6`) merged into one terrace `[[21, 29], [26, 32]]` at 960
  (`common/level_pad_heights.yml`), cutting the bluff either side of the cave mouth from 1,632–1,888 to 960 (nodes
  (21–22, 29–32)) and the forecourt to 1,056. 960 is 256 under the mouth's `LAIR_FLOOR` 1216; the pad heights were
  seeded, not read at the things (the land there is about 1,250). Same fault fails side quest `q-c23_ogre_boulders`
  (probe passes: `q-c23_probe.log`). Fix in X2's pads (drop the merged lair pad or seed it at about 1,216), then
  rebuild X2; the tests need no change.
- **93 Water Sleeper, real fault (P4, A6; F62 plate `SINK`).** From (-2462, 1560) the party walks onto the test's
  plate (256 × 256 at (-2880, 1664), now sunk 4 into the floor) and stands at (-2855, 1658) without "Accept the test
  of Water?" (3 of 3 runs). Started at (-2512, 1649) (the P4 playtest's start; probe with radius 24 on the step
  before) it asks at (-2766, 1659) and the segment passes. A step plate that fires only on some approaches; A6 with
  A1 (the step trigger after the indoor slide fix) to look. `devdocs/xeen/briefs/p4/L4/playtest_test.yml` passes.
- 17 (stale, fixed): D-142 moved the north-west lake dragon (23, 48) → (20.5, 51.5); the poses now (-21680, 6400) and
  (-21680, 3072). Same fix in `q-c13_lake_beasts.yml`.
- 39 (stale, fixed): D1's rebuild inserted 15 actors before the NPCs: Yog 29 → 44, Justine 31 → 46 (also NPC 4956
  30 → 45, Luna 32 → 47). Fixed in 39, promotions 85 and 87, side quests q-d12 ×2, q-d20, q-d2_q-c24.

**Side quests** (normal, before the fixes): 64/71 pass. After the test fixes: q-c13, q-d12 ×2, q-d20, q-d2_q-c24
pass; q-d3 passes three of three (`--repeat 3`); **q-c23 fails on the X2 fault above**. So 70/71, the one being
the map fault. Reports `side_report_run1.md`, `side2.log`.
- q-d3 (stale, fixed): Sister Ada's 2,000 XP read 2,084 for member 0 in about half the runs. Not a learning bonus:
  the `clear_hostiles: 3000` before Ada killed an Arachnoid (D1 spawn 14, moved this round from (-12000, 17568) to
  (-2688, -3168), south of Castleview) that had come to about 2,950 from her cell targeting the party; its XP went
  into the lesson's count. The XP is now remembered after the clear (`q-d3_probe_b.log` lists the actors). For A6:
  that spawn now aggroes on the Drawkcab cells' row; check it is meant.

**Promotions** (`--start`): 22 pass (01–57), stopped at 61 (stale: D-159 made each sundial click turn the dial one step
with "You turn the sundial. It is set to {N}." on the status line). `promotions/61_nightshadow_count.yml` rewritten
for that (6, 3 and 9 clicks, each reading checked); not rerun (handed to xeen-fb4-promo, from 61 on).
**`regressions.sh`**: not run (xeen-fb4-regress).

Not checked: other standalone Xeen scenarios with D1/D6/X5/DD-01 actor indices that moved this round
(`hooks_d5_d6.yml` actors 34/43, `x5_winterkill_ghosts_move.yml` 75/77/88/90/103, `q-d5_rooka.yml` DD-01 37/47 → 38/48
if they are the same monsters); the list came from comparing HEAD's and the installed scenes' actors.

### D-174 promotions (agent xeen-fb4-promo, 2026-11-25 ~14:40–14:45)

Normal run (no `--reload`) on `build-xeen` of 14:09 (not rebuilt), each segment under `tools/heavy.sh 6` with
`SDL_AUDIODRIVER=dummy`, two lanes. Picked up from 61 as xeen-fb4-tests2 left it: its `--start` at 14:36 (starts
copied from the main chain's checkpoints of 14:15–14:29) passed 01–57, 22 of 22. Blocks R, F, H and I run from those
start copies (`output/xeen_fb/p5_promo/drive.py`: the promotions runner with logs and reports in
`output/xeen_fb/p5_promo/<block>/`; checkpoints in the usual `output/playthrough/xeen/promotions/checkpoints/`).

- **R (61–69): 9 of 9 pass**, 61 with tests2's rewrite for D-159's one-step sundial (6, 3 and 9 clicks, each reading
  checked). **F (81–99): 6 of 6 pass**, 85 and 87 with tests2's D1 actor indices (Luna 47). **H (91, 93): 2 of 2.**
  **I (95, 97): 2 of 2.**
- **Whole set: 41 of 41 pass** on today's rebuilt maps. STALE none (no map reset on entry), D-75 ISSUE none (both
  prerequisite lines proven), PARTY: nobody down; lesser conditions only (Weak in 67–68 and 81–89, Disease in 61),
  logged as before.
- No new failures, so no real fault to hand on; no test changed in this pass. `--reload` stays for the release check
  (D-174).

### D-174 side quests (agent xeen-fb4-side, 2026-11-25 ~14:40–14:55; for A3, tests)

Scope cut by the coordinator: no second full set (xeen-fb4-tests2's 70/71 stands; q-c23 is the X2 lair pad, being
fixed by another agent). Binary `build-xeen` 14:09, no map installed after 14:00. Scratch `output/xeen_fb/p5_side/`.

**Actor indices moved this round** (`actors_diff.py`: HEAD's scene actors against the installed ones, by monster,
NPC and group in order). Only three maps shifted: **D1** (15 new arachnoid actors at 18–32: old 18–28 → 33–43,
Yog/NPC 4956/Justine/Luna 29–32 → 44–47, the street group 33–62 → 48–77), **DD-01** (Felix 4958 inserted at 12:
every old index ≥ 12 is +1; Rooka 36 → 37, the 2475 actor 46 → 47), **XD-04** (actors 0–3 the D-163 child bodies,
same indices). D2, D3, D4, D5, D6, D7, X1–X7, X9, DD-07 keep their order (positions moved, indices not).

Every hard-coded actor index in `tests/scenarios/xeen/`, `tests/playthrough/xeen/` and `devdocs/xeen/briefs/*/L4/
playtest*.yml` on those maps checked: all already on the new numbers (tests2's fixes; D1 and DD-01 and XD-04 L4
playtests regenerated with their maps) except one generator: `tests/playthrough/xeen/promotions/class_table.py`
LUNA still said actor 32 (D1) while its output `87_luna_table.yml` had been hand-fixed to 47; fixed in the
generator. Regenerated in a scratch copy: every segment it writes is byte-identical to the tree.

**Runs** (normal, heavy.sh 6, two lanes): `q-d3_drawkcab_way` PASS (Ada's lesson stable after tests2's fix),
`q-d5_rooka` PASS (37/47 are right; not 38/48), `hooks_d5_d6.yml` PASS (D6 actors 26, 34, 43–45 unchanged),
`x5_winterkill_ghosts_move.yml` PASS (X5 actors unchanged). No real fault beyond tests2's q-c23 (X2, A5).

### D-174 regressions (agent xeen-fb4-regress, 2026-11-25 ~14:40–14:50; for A1, A5, tests)

`tools/xeen/regressions.sh` (with D-175's `playtest_lake_dragons_leash.yml`) on `build-xeen` 14:09 as it is (unit tests
14:14; `openyamm_runtime_tests` is the 08:56 build, not rebuilt). Each game run in its own `heavy.sh 6` scope (a wrapper
passed as the game binary), `SDL_AUDIODRIVER=dummy`, the script's two lanes. Logs
`output/xeen_fb/p5_regress/xeen_regressions.bkj4NO/` (summary `run1.out`).

**Result:** unit tests pass, runtime tests (dimensional travel, town portal) pass, **43 of 44 scenarios pass as
written** (MM7/MM8/MM9 round trips, MM6/MM7/MM8 lifecycles, release, turn-based, every Xeen one incl. the L4 leash,
`d6_ambrose_flight` and `key_npcs_unkillable` with their actor indices unchanged), model dependencies, `quests.py`,
`key_npcs.py`, `check_actor_heights.py` pass. Nothing from D-153 picking or the round-collider slide fails here.
- `tests/scenarios/xeen/x2_fall_damage.yml` (stale, fixed): the party landed at z 737, the test asserted 760–776 (ground
  768). X2's landing node (34, 58) is 736 on the installed map, the dip in front of Darzog's door that dungeon4 already
  reported (REQUEST to outdoor, open) and that `SkyFalls.x9` and `check_sky_falls.py` take as 736. The test's falls now
  start 850 and 858 over 736 (1586, 1594) and land at 728–744; the damage expectations are unchanged (they follow the
  fall's height). Passes (`output/xeen_fb/p5_regress/fall1.log`). Not generated (hand-written, A1).

For A5 (observation, X2, not a test failure): the island's crown east of the door is now a trench, not only a dip:
nodes (33–35, 60–61) 640, (34, 59) 672, (34, 58) 736, while the crown terrace `[[28, 55], [35, 61]]` is 768.
`bridge_end_heights.yml` `x2 thing:island_jetty#cut` runs the jetty's line from 33.969 (the generator's is 36.0) and
keeps those five nodes cut; `ISLAND_LANDING` (35, 60.5) still drops the party at 768 (a 128 fall into it). If the
crown is levelled again, the x9 table, `check_sky_falls.py` and `x2_fall_damage.yml` go back to 768 together.

### D-174 fixes: X2 lair pad, P4 plate (agent xeen-fb4-fix7, 2026-11-25 ~14:40–15:10)

Scratch `output/xeen_fb/p5_fix7/` (`tools/install_check.sh` is outdoor5's with its own scratch).

**X2 Ogre Lair (segment 15, Q-C23): fixed at the source.** Cause: F59's auto pads of the lair campfire and the two
skull pillars were merged at the lower one's height (960, read on the bank's lip), cutting the bluff either side of
the cave mouth by up to 928. Rule (`common/level_pads.py`, D-174): a pad chosen by `auto` may move no node more than
`CUT_LIMIT` 256 (cut: the node's own land or its outline's land carried across, so a map already built with the pad
reads the same; fill: the node's own land; water nodes and nodes a later layer holds are skipped). A pad, or a merged
pad, over the limit is left out and its decorations sink to their rim as rocks do. PADS's hand-listed pads are laid as
before but listed. Check: `python3 level_generation/projects/xeen/common/level_pads.py --check [maps]` (exit 1 on any
auto pad over the limit). X2: the three lair pads left out (928/704/384), the pillars and campfire sunk 64/59/32; the
lair land is back to HEAD's (bluff 1,632–1,888, forecourt 1,216–1,280).
- **Sites the check lists on the installed maps** (each drops its pad, or sinks, at that map's next regen; maps that
  need a rebuild): X1 Orc supplies (30, 28) 265, Travellers' camp (93, 42) 345, Shepherd's spring (65, 20) 275;
  X4 eyrie_bones_3 304; X5 Freeda's tent + campfire 710, the ogres' camp 448, the Cyclops' outpost 472; X6 the
  prospector's tent 670, Gorm's coach 784; X7 the miner's cache 420 (all cuts into bluffs). D6's basalt pinnacle 408
  is a PADS (hand) pad: listed, kept. Also over the limit by fill on HEAD's land but not seen on the built maps:
  X1's well (60–62, 39–42) filled 512 at a bank (true by HEAD), D3's mages' cart 336. **Rebuild: X1, X4, X5, X6, X7
  (and D3 to check).** Not done here (lanes' maps; their regen prints `level pad ... left out`).

**X2 island crown (xeen-fb4-regress's report): fixed.** Cause: `common/wild.py bridge_ends` took a node as water
when its installed land stood at the lake's level, so the land the island jetty's own deck cut had lowered read as
water; the end crept inland (36.0 -> 33.97 since 3.3) and the cut followed (`bridge_end_heights.yml` kept it).
Now a node is water only where the sketch has water too. An end that butts into a generator terrace standing more than
BRIDGE_STEP over the deck (the crown, 768) takes no pad and cuts nothing beyond: it stands where the land rising to the
terrace passes 16 under the deck (middle and quarter-width lines, as `town_fit bridges.step` reads). The studio holds
node 35,61 at the lake's 576, so the jetty moved to y 60.0 (`x2/gen.py`; its boat sign 38.6, 60.5) and
`ISLAND_LANDING` to (34.9, 60.15) (land 742; 186 from the old point, inside the tests' 200 radius). The crown is level
768 at (33–35, 57–60) and (31–34, 61) (35,61 the studio's lake); the `#cut` entry is now `[35.969, 60.0]`, no nodes. Other `#cut` entries: none
crept the same way except possibly D4's `isle_jetty` (73.3 -> 71.97, one wet loop; recheck at D4's next regen).
`Xeen.SkyFalls.x9` 768, `x2_fall_damage.yml` 1618/1626 and 760–776, quest_stub `act5_x9_xd17` 1618: back.

**X2 rebuilt** (built three times identical, the third from the installed land), installed with its bake: gate
(faces, town_fit 0), door, wall, faces, wild, fit, reach, check_d85, common/d85, heights 0, stale_bakes 0; five
playtests pass; `check_sky_falls.py` 0, `quest_stub` act5_x9_xd17 passes, `x2_fall_damage.yml` passes;
**playthrough segment 15 passes** (`run.py 15`, new checkpoint) and **`q-c23_ogre_boulders` passes**.

**P4 test plate (segment 93): not fixed; cause found, engine-side.** The installed plate is a block 124–132 (top
face 2385, event 11, PressurePlate) standing in the arena floor at 128, which runs on under it. The indoor movement's
"walkable floor above the chosen one within a step" rule (`IndoorMovementController.cpp` ~2690) deliberately does not
stand the party on trigger faces (MM9's invisible plates refired), so a party whose floor sample picked the arena floor
likely walks on inside the 4-high plate at 128 and never stands on face 2385; an approach whose wall hit steps it up
(head-on from the east, y ≈ 1,650) fires. Not confirmed by a probe run (budget). Spec in REQUESTS of this agent's report (A1). Not rebuilt.

### D-174: P4 trigger plate (agent xeen-fb4-engine8, 2026-11-25 ~15:00–15:55)

Scratch `output/xeen_fb/p5_engine8/` (probe scripts, logs, `probe*/compare.txt`).

**Cause, proved.** The floor sample takes the floor nearest the feet, so a party at 128 keeps the arena floor 343
running on under the sunk plate block (124–132). The indoor rule that lifts a body onto a walkable floor within a step
above (`IndoorMovementController.cpp`, the overlapping-floor rule) skipped every trigger face (kept for MM9's invisible
plates), so the party walked on inside the 4-high block. It touched face 2385 only when the leading-probe step-up
briefly put it on top (one step, then back to 343). That brief touch fired the plate on some approaches and not on
others. A per-step trace of segment 93 with the old rule shows the party on 343 from (-2694, 1618) to the plate's
middle and never on 2385 (FAIL at step 49). With the fix it stands on 2385 from (-2756, 1633) on.

**Fix (shared indoor movement).** A trigger face is skipped by that rule only when it is a bare sheet. A trigger face
that tops a solid (a wall of its room shares one of its edges and runs down from it) is stood on like any floor.
`indoorFaceRunsDownFromFloorEdge` (`IndoorGeometryUtils`), `IndoorMovementController::floorFaceTopsSolid` (lazy and
remembered per face until the runtime cache is invalidated; no per-frame cost off plates). No save change.

**Sites (offline inventory, `sunk_plates.py`: up-facing trigger faces over a floor of their room within 50).**
Xeen 118, all with side faces (P1–P4 10 each, D7 8, X9 1, XD-12 11, XD-02 10, and others; P5 and X8 none). MM9:
68 invisible sheets, none with a side face, so they are unchanged by construction; 44 visible plate blocks with sides
(Chasm of the Dead 23, Anskram Keep 21, shooter, crusher and gate pads) are now stood on. MM6–MM8: 7 raised plates with
sides (6 oracle 448; 7 7d23 168/756; 8 d20 129, d29 461, d40 730/943).

**Four-direction probe** (pose 96 off each side on the floor under, hold forward, per-step support trace; old rule
compared on the same binary). P1–P4, D7, X9 (49 plates, 196 probes): fix 178/178 reachable sides stand on the plate.
With the old rule, 50 stood, 126 only touched it for 1–2 steps (the fault) and 2 never touched it (P1 2533 N, P2 3876 W).
The 18 misses are the same under both rules: the approach is blocked or falls (X9 2682 is a doorway threshold walled
W/E/N; D7 corner plates' outer sides are the void; others start in a wall or behind a statue). MM6–MM8 (28 probes): the
same as before, except d40 943 W, where the old rule wedged the party at the dais's east edge and it now walks across.

**Tests.** Doctest "a trigger plate sunk into the floor is stood on from every side; a bare trigger sheet is not"
(`tests/IndoorMovementRecoveryTests.cpp`, 10 directions; fails on every direction with the old rule). Scenario
`tests/scenarios/xeen/p4_water_plate_approach.yml` (from (-2462, 1560); passes, the party stands at z 132).
**Main segment 93 passes** (`run.py 93`, checkpoint rewritten). Unit tests 3224/3224. Regressions pass: MM9
`chasm_hidden_shooter_hits_party`, `dungeon_of_secrets_trial_with_traps`, MM9 playthrough 09 (Anskram gate pads) and
15 (Chasm) from their checkpoints in scratch copies; MM6 shadow guild ×3, `party_stops_on_stair_tread`,
`abandoned_temple_cage_trap` (failed once while two games ran, then passed 2/2, and passes on the 14:09 binary: a
timing flake); MM7 `heart_of_the_wood_trapped_chest`; MM8 `castle_of_air_exit_stairs`; Xeen `dd12_plate_after_load`,
P4 `playtest_test.yml`.
**`openyamm_runtime_tests`** rebuilt (15:40) and run: 122/126. The 4 failures are outside movement and come from other
sessions' uncommitted edits: HUD text colour codes, New Sorpigal brazier billboard palettes
(`IndoorDecorationInteractionTests.cpp:82`), party creation class lists and race card (`NewGameScreenTests.cpp:45/63`,
continent chedian). `build-xeen` openyamm/unit/runtime built 15:39–15:40 with the final code.

### D-174: deep pad rebuilds (agent xeen-fb4-outdoor9, 2026-11-25 ~15:05–16:20)

Scratch, logs and captures `output/xeen_fb/p5_outdoor9/` (`<map>/run.out` per map, `shots/<map>_before|after/`).
Every site of fix7's list was first built without its pad (`tools/dry.sh`: the L4 minus the over-limit pads) and
measured on that land (`tools/evalsite.py`): most were set pieces that would hang or bury, not rocks that sink.

**Rule (`common/level_pads.py apply`, set pieces).** A tent, well, crate or other set piece does not sink as a rock
does, so leaving its pad out left it on the slope. Now: (1) a set piece's pad over CUT_LIMIT tries the cells its
footprint touches (no MARGIN); if that is within the limit it is laid and kept as `margin: 0` with its height in
`level_pad_heights.yml` (on land built with it, the wider pad would read level and come back); (2) a merged pad over
the limit leaves its decorations out (they sink, as on X2) and keeps each set piece on its own pad, unmerged;
(3) `auto` no longer lays a thing PADS lists by hand; `--check` recognises hand pads by the thing's title.
Freeda's tent (X5) and the prospector's tent (X6) have no pad within the limit (the land under each tent's own cells
differs 864 / 672; without a pad each tent hangs 180–300 and is buried 320–420 at its back): **listed by hand in PADS**
(their pads as installed: cuts into the mound / notch behind the tent, no path or landing there). X5's gen calls
`LP.apply` for it. Two of the seeded heights (ogres' tent 1472 → 1664 read on the land without the pad; miner's cache)
were re-read from the pad-less build (regen with `XEEN_WILD_MAPS` on that build, then on its own build until two
builds are identical).

**Sites (11 auto + 2 bank fills):**
- X1 Orc supplies (30.8, 29.4): footprint pad (margin 0) at 1632. Travellers' camp: tent alone at 704, the campfire
  left out and sunk 24. Shepherd's spring: footprint pad at 1984. All stand level (captures 01–06).
- X4 eyrie_bones_3: left out, sunk 35 (a skull pillar half in the slope, as rocks).
- X5 Freeda's tent: hand pad (unchanged look); her campfire has its own small pad at 1568 (within the limit on the
  built land). Ogres' camp: tent alone at 1664 (its seeded merged 1472 would cut 320), fire left out (no sink needed).
  Cyclops' outpost: both tents one pad at 2304, now within the limit.
- X6 prospector's tent: hand pad (unchanged). Gorm's coach: its north end and the yard barrels stood on the rise
  from the coach yard's level floor to the cliff (row 91); the coach moved 0.6 cells south (87.2, 93.6) and the
  barrels to y 92.1 (`x6/places.py`), all on the yard's floor, no pad. A margin-0 pad there alternated between builds
  (`_moved` reads a generator-levelled terrace as "built"): see NEXT.
- X7 miner's cache: left out; the 64 crate stands at its lowest corner on the slope below the adit (fine; capture).
- X1's well (60–62, 39–42) fill 512: the well stands in a walled yard on the town's 1152 terrace, the wall holds the
  edge (captures `shots/x1_well`); kept. D3's mages' cart fill 336: a 64 crate on a grassy knoll under a tree by the
  tower, no visible plinth (`shots/d3_cart`); kept, D3 not rebuilt.

**Bridge ends (fix7's wild.py water rule, found on the rebuilds).** With water only where the sketch has water, X4's
Nystor jetty end went from 83.03 back to 82.03 (+39 at the lake's corner node 82,102) and D4's isle jetty from 71.97
to 72.97 (+67: row 73 are shore nodes the studio holds at the lake's 1056); both gates failed (town_fit
`bridges.step`). Fixed in the generators: `x4/places.py` jetty end 83.0, `d4/gen.py` `ISLE_JETTY` end 72.0 (the
installed, passing ends). The rule still stops an end on such shore nodes elsewhere: NEXT.

**Rebuilt and installed with bakes: X1, X4, X5, X6, X7, D4.** Each: two consecutive builds identical, gate (faces
--check, town_fit) 0, door, wall, faces --check, wild, fit, reach, check_d85, common/d85 exit 0, heights 0, every L4
playtest (walk, hostility, daily, Randon) passes, `level_pads.py --check <map>` 0, regen --check from the installed
map identical. Extra: X1 q-c20, q-c17, hull_edge, start_nothing_in_reach, nystor_boats_back, bridge_walkers; X4
hull_edge; X5 winterkill_ghosts_move; X6 warzone_entrance; X7 edges; then q-c16_cyclops_outpost, q-c10_scarab,
nystor_boats_back (after X4): all pass. The 15:40 session interruption killed the X1 lane after its playtests: its
last extra, level_pads and regen --check were rerun (pass, identical).
**End:** `level_pads.py --check` exit 0 (D6 pinnacle, X5 Freeda, X6 prospector hand-listed); stale_bakes 0;
build_world --check 0 differ; quest_stub 19 passed; check_sky_falls 0; towns.py --strict exit 0.
**Main chain** (`run.py`, normal, 16:10–16:35, checkpoints refreshed; segment 15 first read STALE on X4's checkpoint):
52 of 52 pass (`output/xeen_fb/p5_outdoor9/tests/chain.log`).

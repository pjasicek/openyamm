# DD-10A Gemstone Mines, west pocket (L4): notes

Lane A8 (agent `agent:xeen-a8-dd10a`), phase 3, 2026-11-20. Built from the MU-6 graph
(`devdocs/xeen/mockups/act3_graphs/dd10a.graph.yml`) with decider D-27 (`mockups/act3_a8_decisions_b.md`), which wins
where they differ. All four levels are written by `output/studio_cal/dd10a/tools/gen.py`, which imports the mine's
shared pieces from `output/studio_cal/dd10a/tools/mine.py` (below: DD-10B and DD-10C use the same module). The
playtests and this file are written by hand. `output/studio_cal/dd10a/cycle.sh` generates, formats, validates,
builds, installs into the scratch root `output/studio_cal/dd10a/root`, audits and records (`LEVELS="L1 L2 L3 L4"`).

## What was built

Map 9159, `xeen_dd10a.blv`, class S, on D1 Castleview Vale, under the hill above the gemsmiths' row; Q-D7 The
Gemsmiths (repeatable). Party 23-27, band 16-28, 20 monsters, treasure 3, music 18.

Seven rooms, all floors at 0 (the sump's pool sunk 32), in the plan frame x east, y north, the adit's mouth at y 0:

| Room | Size | Texture | Monsters | What |
| --- | --- | --- | --- | --- |
| West adit | 384 × 896, 352 high | timbered | — | arrival and exit; two timber sets, cart rails, the plank door north |
| Timbered gallery | an L 512 wide, 1,408 north then 1,536 east, 416 high | timbered | 3 Beholder Bats | five timber sets, lagged roof, an old ore cart |
| Ruby stope | about 1,800 × 1,500, 576-832 high, rough | rock | 3 Arachnoid Hunters, 2 Electrapedes | five ruby veins, a rock pillar, two stalactites |
| Cobweb drift | about 1,400 × 1,200, 448-576, rough | rock, webbed roof slopes | 4 Arachnoid Queens, 3 Hunters | the queens' den; two web-wrapped bundles |
| Sump | about 1,100 × 960, 384-448, rough | rock, 7wtrtyl pool | — | standing water, the strongbox (T3) |
| Emerald gallery | about 1,500 × 1,000, 512-640, rough | rock | 3 Beholder Bats, 2 Electrapedes | five emerald veins, a stalactite |
| Bone pocket | about 1,300 × 1,300, 384-448, rough | rock | — | three bone heaps (one explodes), a skeleton, the miners' chest (T3) |

Links as the graph: adit -door- gallery -open- ruby -open- cobweb -door- sump -door- emerald -open- bones -open-
gallery. Critical path adit, gallery, ruby, cobweb, sump, emerald; return emerald, bones, gallery, adit; one loop.

**Measured** (`oymap metrics`, `metrics.json`): 7 sectors (≤ 15), **9.48 M units²** (≤ 20), 20 monsters (15-30), 2
chests (0-3), 3 doors (3-8), 1 exit, 19 lights (9 room lights and a coloured glint before each vein), 3 placed sounds,
17 decorations. Largest room the ruby stope (2.37 M); ceilings 352-832 (median 480).

## Monsters and kill experience

All placed, hostile by their rows, no map relations (D-27): Arachnoid Hunter 18 (11331) ×6, Arachnoid Queen 24 (11332)
×4, Beholder Bat 20 (11312) ×6, Electrapede 20 (11361) ×4. Groups 1 gallery, 2 ruby stope, 3 cobweb drift, 4 emerald
gallery. Kill XP L(L+10): 6 × 504 + 4 × 816 + 6 × 600 + 4 × 600 = **12,288, 3.07k per member** (the graph's 3.07k).

Map card slots (encounter chance 0, the card only): Xeen Arachnoid tier 5, 2-3, weight 40; Xeen Night Bat tier 5,
2-3, weight 35; Xeen Crawler tier 4, 1-2, weight 25. Environment cave, lock 4, trap 3, perception 2, refill 672 days.

## Mechanisms and hooks

- **Veins** (D-27): five ruby veins on the ruby stope's walls and five emerald veins in the emerald gallery, each a
  wall panel of A6's vein picture (`xdvruby`, `xdvemrld`, 256 × 384, drawn once) with a small coloured light 96 in
  front so it glints across the cave. Hover "Ruby vein" / "Emerald vein" (dark/aaze0039:1-4). A click with the vein's
  map variable clear sets it, gives one rock (ruby 12357, emerald 12358: the hooks' `map_gives`), runs A3's hook
  (`q-d7.ruby_veins` / `emerald_veins`: sets `q-d7.dug` 113144) and says "You work a ruby rock out of the vein.";
  spent: "You've got all this vein has to offer." (aaze0039:10). A rock given while the hand is empty lands in the
  hand, as any GiveItem.
- **Refill** (`evt:refill`, a load event): when `q-d7.refill_a` (113141) is set, every vein's variable goes back to 0,
  the bit is cleared and the status says "The veins glitter again: the God of Minerals has been at work." refill_b and
  refill_c are the other pockets' and are left alone. Played: picked, re-entered unpaid (still spent), paid,
  re-entered (full, refill_a clear, refill_b/c still set), picked again (dug set again), re-entered (no second refill).
- **The exploding bone heap** (D-27): one of the bone pocket's three heaps (`deco:bones_heap_c`): "The bones
  explode!" (aaze0039:13) and **16 fire to every member**, once (map variable `bones_blown`); then, like the other two
  heaps, "The bones crumble to dust in your hands." (aaze0039:14). A level-25 party has 165 / 82 / 108 / 72 hit points
  (Knight, Cleric, Archer, Sorcerer): 16 is 10-22 %, 15 % of the average member. The heap does not come back with a
  refill.
- **Exit** (`evt:exit`, the `exit` preset, D-24): the adit's mouth (a plank face, 160 × 320, in the adit's south
  wall), the game's own "Do you wish to leave Gemstone Mines?" window; "Exit the Gemstone Mines?" (aaze0039:0) is its
  meaning. Live onto D1.
- `evt:arrive`: a one-shot window on the first arrival (`arrived_once` 117160): "THE GEMSTONE MINES. Old timber, cart
  rails and the smell of wet stone. ..." `evt:enter`: a status line on every entry.
- Flavour: the ore cart, the skeleton, the two web bundles ("Cobwebs", the graph's line), three plank doors, two chests.

## Qbits, variables, items

| Name | Number | Use |
| --- | --- | --- |
| `arrived_once` | **117160** | map qbit (provisional block 117160-117199): the arrival window, once per game |
| `q-d7.refill_a` | 113141 | A3's: read and cleared by this pocket's entry |
| `q-d7.dug` | 113144 | A3's: set by every vein through the hooks |

No player bits. Map variables: `ruby_1`-`ruby_5`, `emerald_1`-`emerald_5`, `bones_blown` (+ the studio's
`once.arrive`). Items: ruby rock 12357, emerald rock 12358 (one per vein).

## Exit and arrival

`exit:d1` → `exit:d1_adit`, **live** onto D1 at A6's return point for D1 event 187, **(-9728, 20480, 1600) facing
1536** (south, studio direction 270), 990 south of the adit's face (thing:dd10a_adit at y 21470). Measured with
`playtest_exit.yml`: (-9728, 20480, **1601**), D1 as installed at 18:08 (odm) with its 18:05 bake (loads cleanly; the
root's D1 files are the same inodes as assets_dev's at the end of the session).

**D1's door into this map (A6, D1 event 187 still says the mines are not open):** the start point **(0, 192, 0),
facing north (90°, game 512)**, just inside the adit's mouth.

## Textures (22 distinct, cap 30; 0 new of 4)

MM7 Nighon Tunnels 7d35 (D-27, `dungeon_families.yml` mines): `cwb1` walls and roofs, `cfb1` floors, `trim9_32`
posts, jambs and plank doors, `trim9_32a` caps and lagging, `7wtrtyl` the sump's water; the world's `xncartsd` and
`xnrustirn` (XD-02's ore cart, the rails) and `xnweb` (webbed roof slopes and bundles in the cobweb drift); A6's
`xdvruby` and `xdvemrld` on the veins (installed and registered; nothing waits on A6). Chest pictures make the rest.
`python3 tools/xeen/texture_budget.py --root output/studio_cal/dd10a/root --map DD-10A`: S 22/30, 0/4 new.

## Original lines (dark/aaze0039)

"Exit the Gemstone Mines?" (:0, the leave window's meaning); "Ruby vein" / "Emerald vein" (:1-4, the hovers); "You've
got all this vein has to offer." (:10); "The bones explode!" (:13); "The bones crumble to dust in your hands." (:14).

## Presentation

Music 18. Placed sounds: air at the adit's mouth (`whistling wind`), seepage in the stope (`drip02`), the sump
(`drip01`). Lanterns (`torch02`) on solid wall only (none in a doorway: the lead's lamp rule of 2026-11-20 applied;
three were moved off openings). Ambient 12-18: timber lit, caves darker, the web drift coldest. **No bake in the
scratch root** (the lane lead bakes after install).

## Dressing

`oymap audit --world xeen --dressing`: 0 errors, 0 warnings. No containers but the two chests (by walls, far from the
doors and openings); the bone heaps and skeleton in the bone pocket's south-west, off the walking line between its two
openings; the cart against the gallery's north wall; the timber set beside the bone pocket's opening moved east so no
post stands in it. **Dressing exceptions:** none.

## Checks (scratch root, `--world xeen`)

- `oymap validate` L1-L4 no issues; `oymap build` 0 warnings; `fmt --check` clean on L1-L4.
- `oymap audit --reach --solve` (`output/studio_cal/dd10a/audit.txt`): no error, no warning, 0 faces in one plane;
  solve reaches 7 of 7 sectors in two steps (the three doors), the exit to D1 listed.
- Playtests (`output/studio_cal/dd10a/four.sh`, logs `run/four_185142/`, summary `four1.out`): **all three 4 of 4**:
  `playtest.yml` 80 asserts (the loop, every vein, spent lines, the bones and the trap's damage, both chests, the
  pick-pay-re-enter-full refill), `playtest_hostility.yml` 25, `playtest_exit.yml` 23.
- The playtest plays the God of Minerals' payment by an event script with the hook's own do-list (10,000 gold, the three
  refill bits, dug cleared): the scenario's event Lua has no `XeenQuests`. The God's refusal while nothing is dug is
  DD-10B's to test, at the God.

## Pictures looked at

`output/studio_cal/dd10a/shots/look1_1..4.jpg` (31 shots: every room, each door closed and open, every vein wall,
the bones, the chests, the cart, the openings) and `look2_1..4.jpg` (after the fixes). Fixed after look1: the ruby veins
were nearly invisible (red cracks on red-brown rock): now larger panels with a red glint light each (emerald green);
grey web rectangles on the cobweb drift's walls read as panels of grey cloth: removed, the web now on the roof's slopes
and two low web-wrapped bundles; a timber post stood in the bone pocket's opening: the set moved; three lanterns hung in
openings: moved onto wall. PNG folders deleted; `tools/tour.py <name>` and `shoot.sh <name>` remake them.
Still plain: the cobweb drift reads mostly as rock (the web shows on the roof's slopes only); the plank doors are one
stretched plank picture; the lighting is flat until the bake.

## For DD-10B and DD-10C: the shared generator

`output/studio_cal/dd10a/tools/mine.py` holds what makes the three pockets one mine: the 7d35 themes (`theme:rock`,
`theme:timbered`) and surfaces, `timber_set`, `rails`, `cart`, `vein_panel` / `vein_light` / `wall_point` /
`vein_events` (one rock, the hook, the variable, the spent line), `refill_event(bit, gems)`, `false_vein_event(gem,
panel, amount)` ("A gem exploded!", fire, once), `exit_event`, `arrival_event`, the plan helpers and `write_levels`.
Copy recipe: copy `output/studio_cal/dd10a/{cycle.sh,four.sh,shoot.sh,tools/gen.py,tools/tour.py,tools/sheet.py}` to
the pocket's folder, `sed s/dd10a/dd10b/`, keep `sys.path.insert(0, '.../dd10a/tools'); from mine import *` in
gen.py (do not copy mine.py, so one change reaches all three), and replace gen.py's rooms, monsters, veins and
numbers. B: `refill_event('refill_b', ['sapphire'])`, `vein_events('sapphire')`, a sixth panel with
`false_vein_event('sapphire', 'panel:false_vein', 16)`, the throne and the God's hook. C (geometry only now): the same
with `diamond`, `refill_c`, and the lava seam (`LAVA`, `LAVA_ROCK`).

## Words needed

None new. (As DD-01/DD-04: no indoor talking monster; B's God is a clicked presence per the hook.)

## DECIDE

- None. (Trap damage 16 fire is a judgment inside D-27's "about a tenth to a fifth"; a lower number is one constant,
  `BONE_DAMAGE` in gen.py.)

## What the user should look at

- The veins: do the glinting red and green panels read as veins worth clicking?
- The cobweb drift: the queens' den shows little web (roof slopes, two bundles).
- The bone heaps: one explodes once; afterwards it crumbles like the rest.
- Pay the God (DD-10B) and come back: the veins are full again.

## State and next steps

L4 complete in the scratch root; nothing waits on another lane except A2's map row 9159 (the root carries a test row
copied from 9153's form with this map's name, stem, music 18, treasure 3 and the slots above) and A6's D1 event 187
(door into this map). The lane lead installs into assets_dev and bakes.

## Installed (lane lead, A8 session 5, 2026-11-20)

- Rebuilt on the merge point 13 oymap (byte for byte the agent's build), installed into assets_dev by temp file and
  rename (`output/studio_cal/a8_s5/rebuild.sh dd10a`), baked (`a8_s5/bake.sh dd10a <scratch root>`, profile
  `tools/lighting/baked_indoors/profiles/xeen_dd10a.yml`, XD-08's values; `stale_bakes.py` 0).
- A2's map row landed; **playtests from assets_dev 4 of 4** under D-32's levelRadiusLimit 60
  (`output/studio_cal/a8_s5/assets_dev_dd09_10a.out`, `run/four_1902*`).

## Session 7 batch (texture fit, mine bed, refill on entry, one size per texture; A8 session 7, 2026-11-20)

Changes in the shared `output/studio_cal/dd10a/tools/mine.py` reach DD-10B and DD-10C too (copies before:
`mine_before_s7.py`, `mine_before_s7_visit.py`, `gen_before_s7.py`).
- **Cart side** (merge point 16, 2 `feature_repeated` on `xncartsd`): a platform's side takes no `fit`, and a
  declared size does not change the texels a unit spans: `CART_SIDE` is the picture at its own size (128 x 64) at
  scale 1.5, once over the 200 x 88 side.
- **Bed**: AU's `xeen_amb_mine` (62801) from the gallery (512, 2432) and the ruby stope (3200, 2304), radius 2800,
  inner 800, volume 0.4.
- **Refill on a fresh entry only** (A3's bug: event 20 refilled the veins on every load, so a reload right after
  paying the God refilled them in the same visit): `refill_event` runs only while the map variable `in_visit` is clear
  and sets it either way; `visit_end_event` (leave) clears it (DD-09's pattern). The playtest pays, saves and reloads
  (nothing refilled, refill_a still set), leaves by the adit onto D1 and comes back (refilled).
- **One size per texture** (merge point 17's build warning): `LAGGING` and `DOOR_PLANKS` are `trim9_32a`/`trim9_32`
  at their own size with scale 2, the exit's planks at scale 5 (were sizes [128, 64], [64, 128], [160, 320]).
- Audit 2 / 0 → 0 / 0; build warnings 0. Recorded, installed, baked; tests from assets_dev 4 of 4 (92, 25, 23 steps;
  `s7_post2.out`). Pictures `output/studio_cal/dd10a/shots/s7/` (looked at: the riveted cart side once, the gallery).

## Session 21 (A8): AU's sounds

The room-filling beds `sound:bed_gallery`, `bed_ruby` take `pan: false` (D-48); the point sounds keep panning. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 22 (A8): "an emerald"

The emerald veins (events 13-17) say "You work an emerald rock out of the vein." (`tools/mine.py` picks the article; was
"a emerald", A3-side's Q-D7 note). The playtest asserts each vein's line. Rebuilt under oymap 12:43:03, installed
14:26 (only `wiring.yml`'s five lines changed; no warnings), bake not stale, tests 4 of 4 from assets_dev, audit 0 / 0;
Q-D7's two scenarios pass normal and `--reload`.

## Session 26 (A8): mine door pictures (F12)

- The three plank doors (events 10-12: `door:adit`, `door:sump`, `door:emerald`) showed the timber strip `trim9_32`
  tiled across their leaves. The shared `tools/mine.py` `door()` (DD-10A/B/C) now gives each leaf MM6's rough plank
  door `d2smldor` (iron handle) once, `fit` over the 224 x 320 leaf (`MINE_DOOR`); edges and tops stay timber, and the
  themes' default door keeps `trim9_32` (no opening uses it). Before: `output/studio_cal/a8_s26/before/dd10a/mine.py`.
- Installed 00:54, baked, tests 12 of 12 from assets_dev (`output/studio_cal/a8_s26/run/dd10a/c005441`); audit 0 / 0;
  check_exits 0, check_drops 0.

## Session 28 (A8): D-89 identity (vein crystals, rails, slopes)

The design review (`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2, DD-10A/B/C severity 3: "a timbered adit with rails, then
rock boxes with flat vein panels") asked for timber sets along the galleries, rails and the cart deeper, irregular
stopes with slopes and rock pillars, each vein framed by shipped gcrys clusters. Generators reproduced the installed L4
first (snapshots `output/studio_cal/a8_s28/before/<key>/`).
- Shared (`dd10a/tools/mine.py` `vein_crystals()`): every vein panel, the false vein too, gets a cluster of three
  tapering crystal shards at both ends (out 56-108 from the wall line, clear of `rough`), in the gem's MM8 d37
  crystal: ruby `gcryswal`, emerald `gcrysc1` (trim_u 16 x 32, enlarged 5 times so one repeat covers a shard),
  sapphire and diamond `gcrysc3` (at each map's existing size). Shards stand square to the map (a turned tapering
  block's faces are not flat on whole units) and may stand on a sloping floor. `write_levels(..., identity)` writes
  `identity:` into L4's project.yml.
- DD-10A: the rails run on along the timbered gallery (north leg and east leg to the ruby stope; bats moved off them);
  uneven floors in the ruby stope, emerald gallery, cobweb drift, sump (the pool's rim kept level by `floor_lines`)
  and bone pocket; a centipede and the emerald spoil moved off the new crystals. `identity: {shape: mine, family:
  7d35}`. Audit 0 errors / 0 warnings (the cave-shape check passes: 30 %+ uneven), check_exits 0, check_drops 0.
- Installed 01:48 (second pass with the stopes' slopes), baked, tests 12 of 12 from assets_dev
  (`output/studio_cal/a8_s26/run/dd10a/c014814`).
- Pictures: before `output/studio_cal/a8_s28/dd10a_before_sheet.jpg`, after (baked)
  `output/studio_cal/a8_s28/shots/dd10a_after.jpg` (tour `shots/s28_before.yml`, `tools/tour.py`).

# DD-10B Gemstone Mines, east pocket (L4): notes

Lane A8 (agent `agent:xeen-a8-dd10b`), phase 3, 2026-11-20. Built from the MU-6 graph
(`devdocs/xeen/mockups/act3_graphs/dd10b.graph.yml`) with decider D-27 (`mockups/act3_a8_decisions_b.md`), which wins
where they differ. All four levels are written by `output/studio_cal/dd10b/tools/gen.py`, which imports the mine's
shared pieces from DD-10A's `output/studio_cal/dd10a/tools/mine.py` (not copied: one change reaches all three pockets).
The playtests and this file are written by hand. `output/studio_cal/dd10b/cycle.sh` generates, formats, validates,
builds, installs into the scratch root `output/studio_cal/dd10b/root`, audits and records (`LEVELS="L1 L2 L3 L4"`).

## What was built

Map 9160, `xeen_dd10b.blv`, class S, on D2 Sprite Forest, in the Gemstone foothills (D2 zone mine_mouth); Q-D7 The
Gemsmiths (repeatable). Party 23-27, band 16-28, 20 monsters, treasure 3, music 18.

Nine rooms on two levels, in the plan frame x east, y north, the adit's mouth at y 0. The upper level at 0, the deep
level at -480; no room lies over another.

| Room | Size | Floor | Texture | Monsters | What |
| --- | --- | --- | --- | --- | --- |
| East adit | 384 × 896, 352 high | 0 | timbered | — | arrival and exit; two timber sets, rails, the plank door north |
| Upper drift | an L 448 wide, 1,280 north then 1,792 east, 416 high | 0 | timbered | 3 Electrapedes, 3 Beholder Bats | four timber sets; the side cut north, the ramp south |
| Side cut | 512 × 480, 352 | 0 | timbered | — | an ore cart of spoil, the miners' chest (T3) |
| Sapphire hall | about 1,900 × 1,650, 576-832, rough | 0 | rock | 3 Electrapedes, 2 Stone Golems | five sapphire veins, the false vein, a rock pillar, two stalactites, raw crystal |
| Gem maker's throne | octagon 1,024 × 1,024, 512, hipped roof to 704 | 0 | rock | 2 Lava Roaches, 2 Stone Golems | the throne of dressed stone with a crystal in its back, on its dais (east), the stair down in the south wall |
| Throne stair | 384 × 704, twelve steps of 40 | 0 → -480 | rock, timber risers | — | down to the God |
| Spiral ramp | a tunnel 320 wide, four legs (south, west, south, east) round the rock core, 2,600 long | 0 → -480 | rock | 3 Beholder Bats | the plank door at its foot |
| Flooded drift | about 1,400 × 1,100, 448-576, rough | -480 | rock, 7wtrtyl pool (sunk 48) | 2 Lava Roaches | knee-deep water along its north side, a chest on the dry south side |
| The God of Minerals | about 1,280 × 1,216, 576-768, rough | -480 | gold-veined rock | — | the God: a great crystal grown out of the east wall, lesser crystals round it |

Links as the graph (plus the side cut and the stair as rooms): adit -door- drift -open- sapphire -door- throne -open-
stair -open- God -open- flooded -door- ramp -open- drift; drift -open- side cut. Critical path adit, drift, sapphire,
throne, stair, God; return God, flooded, ramp, drift, adit; one loop ("down by the ramp, up by the throne's stair").

**Measured** (`oymap metrics`, `output/studio_cal/dd10b/metrics.json`): 9 sectors (≤ 15), **10.67 M units²** (≤ 20),
20 monsters (15-30), 2 chests (0-3), 3 doors (3-8), 1 exit, 21 lights (10 room lights, the throne's and the God's glow,
a glint before each of the six veins, three on the ramp), 4 placed sounds, 18 decorations. Largest room the sapphire
hall (2.76 M); ceilings 352-824 (median 704).

## Monsters and kill experience

All placed, hostile by their rows, no map relations (D-27): Electrapede 20 (11361) ×6, Lava Roach 26 (11362) ×4,
Beholder Bat 20 (11312) ×6, **Stone Golem 26 (11581) ×4** (D-27, for the graph's Sand Golem 22). Groups 1 upper drift,
2 sapphire hall, 3 throne hall, 4 ramp, 5 flooded drift. Kill XP L(L+10): 6 × 600 + 4 × 936 + 6 × 600 + 4 × 936 =
**14,688, 3.67k per member** (the graph's about 3.7k; DD-10A 3.07k).

They wander: in the playtests a golem of the sapphire hall followed the party onto the ramp, and the throne hall's
monsters down the stair. The D-32 radius (golems move at 60) lets them through every opening; nothing is meant to keep
them in.

Map card slots (encounter chance 0, the card only): Xeen Crawler tier 5, 2-3, weight 35; Xeen Night Bat tier 5, 2-3,
weight 35; Xeen Golem tier 4, 1-2, weight 30. Environment cave, lock 4, trap 3, perception 2, refill 672 days.

## Mechanisms and hooks

- **Veins** (D-27, the shared `mine.py`): five sapphire veins in the sapphire hall's walls (edges 0, 1, 4, 5, 6), each a
  wall panel of A6's `xdvsaph` with a blue glint light 96 in front. Hover "Sapphire vein" (dark/aaze0039:1-4). A click
  with the vein's map variable clear sets it, gives one sapphire rock (12359, the hook's `map_gives`), runs A3's
  `q-d7.sapphire_veins` (sets `q-d7.dug` 113144) and says "You work a sapphire rock out of the vein."; spent: "You've got
  all this vein has to offer." (aaze0039:10).
- **The false vein** (D-27): a sixth panel of the same picture on edge 7 with its own glint, hover "Sapphire vein":
  "A gem exploded!" (aaze0039:11) and **16 fire to every member**, once (map variable `false_vein`); then the spent
  line. 16 is DD-10A's bones' number (same band: a level-25 party's 72-165 hit points, 10-22 %). It does not come back
  with a refill.
- **Refill** (`evt:refill`, a load event): when `q-d7.refill_b` (113142) is set, the five veins' variables go back to 0,
  the bit is cleared and the status says "The veins glitter again: the God of Minerals has been at work."
- **The God of Minerals** (`evt:god`, A3's `q-d7.god_of_minerals`, D-27): the great crystal in his hall's east wall
  (`platform:god`), hover "God of Minerals". The hook refuses while `dug` is clear ("The mountains are full. Empty them
  first."), names his price to a party short of 10,000 gold, else takes 10,000 gold, sets `refill_a`/`refill_b`/
  `refill_c` (113141-113143) and clears `dug`. No question window: the hook pays on the click (as A3 wrote it). A
  payment refills nothing at once, here or elsewhere: each pocket refills on its next entry. **Played through the real
  hook** (the map's own event, run as a click runs it): refusal with nothing dug (no gold taken, no bits), payment
  after digging (exactly 10,000 taken, three bits set, dug cleared), the price line when short of gold.
- **The God's line** (`evt:god_speaks`, a step event on his hall's floor, once): "A voice like grinding stone: 'I am
  the god of these mountains. If you give me 10,000 of your gold pieces, I will use them to replenish the gems inside
  the mountains.'" (aaze0039:16, the price rescaled as A3's).
- **Gem maker's throne** (D-27, flavour): seat, arms, back and dais of 7d35's dressed stone `cwb`, a great sapphire-blue
  crystal (`gcrysc3`, see Textures) set in its back, hover "Gem maker's
  throne" (aaze0039:8), click "The throne hums. It was not made for you." (a status line; seat, back and dais).
- **Exit** (`evt:exit`, the `exit` preset, D-24): the adit's boarded mouth in the adit's south wall, the game's own
  "Do you wish to leave Gemstone Mines?" window; "Exit the Gemstone Mines?" (aaze0039:0) is its meaning. Live onto D2.
- `evt:arrive`: a one-shot window on the first arrival (`arrived_once` 117200): "THE GEMSTONE MINES, EAST POCKET.
  ..." `evt:enter`: a status line on every entry.
- Flavour: the ore cart in the side cut; three plank doors (single leaves, 224 wide: no double door in this map); two
  chests.

## Qbits, variables, items

| Name | Number | Use |
| --- | --- | --- |
| `arrived_once` | **117200** | map qbit (provisional block 117200-117239): the arrival window, once per game |
| `q-d7.refill_b` | 113142 | A3's: read and cleared by this pocket's entry; set (with refill_a, refill_c) by the God's hook |
| `q-d7.dug` | 113144 | A3's: set by every vein through the hook, read and cleared by the God's hook |

No player bits. Map variables: `sapphire_1`-`sapphire_5`, `false_vein` (+ the studio's `once.arrive`,
`once.god_speaks`). Items: sapphire rock 12359 (one per vein).

## Exit and arrival

`exit:d2` → `exit:d2_adit`, **live** onto D2 at A6's return point for D2 event 44, **(-15360, 16384, 1696) facing
1536** (south, studio direction 270), about 900 south of the adit's face (thing:dd10b_adit, D2 cell [34, 30.2], floor
1700). Measured with `playtest_exit.yml`: (-15360, 16384, **1697**), against D2 as installed at 18:54 and again (4 of 4)
after A6's 19:10 reinstall (the root's D2 files re-linked to assets_dev's at 19:11).

**D2's door into this map (A6, D2 event 44 still says "The adit is shored shut ... CLOSED."):** the start point
**(0, 192, 0), facing north (90°, game 512)**, just inside the adit's mouth.

## Textures (23 distinct, cap 30; 0 new of 4)

MM7 Nighon Tunnels 7d35 (D-27, `dungeon_families.yml` mines): `cwb1` walls and roofs, `cfb1` floors and stair treads,
`trim9_32` posts, jambs and plank doors, `trim9_32a` caps, lagging and stair risers, `7wtrtyl` the flooded drift's
water, **`cwb1gold`** (7d35's gold-veined rock, the family's own) on the God's hall's walls; the world's `xncartsd` and
`xnrustirn` (the ore cart, the rails); A6's `xdvsaph` on the six veins (installed and registered: nothing waits on A6);
`cwb` (7d35's dressed stone) for the throne's body; **MM8 Prison of the Lord of Fire d37's `gcrysc3`** crystal for the
God's crystals and the throne's inlay, laid at its native 64 × 128 at scale 4 (one picture over a crystal's height, no
visible repeat) and drawn see-through (`translucent`: opacity 0.8, tint 0.38/0.52/0.85, a deep sapphire blue) so it
reads as crystal in the dark rock, not as a saturated cyan block (the lane lead's baked pictures, 19:20) (XD-09's diamond level uses it:
one texture of another shipped family, as a set piece's material). Chest pictures make the rest.
`python3 tools/xeen/texture_budget.py --root output/studio_cal/dd10b/root --map DD-10B`: S 23/30, 0/4 new.

Texture fit (the user's rule, 2026-11-20): each vein panel shows its picture once, whole (`fit`, as DD-10A's); the
crystal is a seamless tile, one picture tall on each prism; nothing one-off is tiled. (`cwb` on the inlay's 12-wide
ends is marked `uneven`: the audit's `texture.squashed` info names those two slivers.)

## Original lines (dark/aaze0039)

"Exit the Gemstone Mines?" (:0, the leave window's meaning); "Sapphire vein" (:1-4, the hovers); "Gem maker's throne"
(:8); "You've got all this vein has to offer." (:10); "A gem exploded!" (:11); "I am the god of these mountains. If you
give me ... of your gold pieces, I will use them to replenish the gems inside the mountains." (:16, the price 10,000).

## Presentation

Music 18. Placed sounds: air at the adit's mouth (`whistling wind`), seepage in the sapphire hall (`drip02`), water in
the flooded drift (`water lapping loop`), the God's `humming`. Lanterns (`torch02`) on solid wall only, none in a
doorway or on a door leaf; room lights are plain lights in open air, none inside geometry (the lamp rule). A1's
light audit (`oymap` 19:17, `devdocs/xeen/formats/LIGHTS.md`): 0 errors, 0 warnings, after three lights in the deep
level and on the ramp were given heights over their floor (they had absolute heights, so they sat in the rock) and the
sapphire hall's west torch was moved off the drift's opening onto solid wall. Ambient
12-18: timber lit, caves darker, the flooded drift darkest; blue light in the sapphire hall, a cold glow at the throne
and the God, warm gold light in his hall. **No bake in the scratch root** (the lane lead bakes after install).

## Dressing

`oymap audit --world xeen --dressing`: 0 errors, 0 warnings. No containers but the two chests (by walls, away from
doors and openings); the cart and spoil in the side cut's back half, off the walking line; the throne against the hall's
east wall, beside (not in front of) the stair; the God's crystals against his east wall. **Dressing exceptions:** none.

## Checks (scratch root, `--world xeen`)

- `oymap validate` L1-L4 no issues; `oymap build` 0 warnings; `fmt --check` clean on L1-L4.
- `oymap audit --reach --solve` (`output/studio_cal/dd10b/audit.txt`): no error, no warning, 0 faces in one plane;
  9 of 9 sectors on foot with the doors out of the way (the three plank doors).
- Playtests (`output/studio_cal/dd10b/four.sh`, summary `four1.out`, logs `run/four_191032/`): **all three 4 of 4**:
  `playtest.yml` 108 asserts, `playtest_hostility.yml` 25, `playtest_exit.yml` 23; the exit test again 4 of 4 after
  D2's 19:10 reinstall (`run/four_191159/`). After the crystal, throne and light fix: all three again 4 of 4 (`run/four_192008/`,
  summary `four2.out`). `playtest.yml` (the loop, every vein, the spent line, the false vein's damage once, both chests, the throne,
  the God's refusal, his payment through the real hook, re-entry full, the price line when short, no second refill),
  `playtest_hostility.yml`, `playtest_exit.yml`.

## Pictures looked at

`output/studio_cal/dd10b/shots/look1_1..4.jpg` (35 shots: every room, each door closed and open, every vein wall, the
false vein, the throne, the God, the stair from both ends, the ramp's four legs, the chests, the cart) and
`look2_1..2.jpg` (after the fixes). Fixed after look1: the God was a flat tiled crystal panel in the wall, reading as a
cyan rectangle: now a great crystal prism and four lesser ones grown out of the east wall; the throne stair's treads
did not read from below: timber risers; the crystal texture is used at its true size (fewer repeats). PNG folders
deleted; `tools/tour.py <name> [filters]` and `shoot.sh <name>` remake them.
After the lane lead's baked pictures (`shots/baked_a.jpg`: flat saturated cyan blocks with a tiled pattern): the
crystal re-laid and tinted, the throne rebuilt in dressed stone with a crystal inlay (`look3_1.jpg`, `look4_1.jpg`).
Still plain: the ramp is plain rock; the lighting is flat until the bake.

## Words needed

None new. (No indoor talking monster: the God is a clicked crystal per the hook.)

## DECIDE

- **The God's picture.** The graph says "a face in the rock"; no shipped 7d35 picture shows one, and the brief gives B
  one new texture (the sapphire vein). Built as a great crystal of MM8's `gcrysc3` (cheapest to reverse: one platform
  id). If the user wants a face, A6 could paint one (B has 3 of its 4 new-texture slots free) and it goes on a panel in
  front of the crystal.
- Gem damage 16 fire (as DD-10A's bones; `GEM_DAMAGE` in gen.py).

## What the user should look at

- The God of Minerals: does the crystal in the gold-veined hall read as a god? Pay him once something is dug, come back:
  the veins are full.
- The God's crystal and the throne's inlay after the rebake: a deep, see-through sapphire blue.
- The spiral ramp: four plain legs round the rock core (no visible shaft).

## State and next steps

L4 complete in the scratch root; nothing waits on another lane except A2's map row 9160 (the root carries a test row
copied from DD-10A's 9159 test row with this map's stem and the slots above) and A6's D2 event 44 (door into this map).
The lane lead installs into assets_dev and bakes.

## Installed (lane lead, A8 session 5, 2026-11-20)

- First install and bake showed the God's crystal and the throne as flat tiled cyan blocks (`shots/baked_a.jpg`);
  fixed by the agent (translucent tinted `gcrysc3` at scale 4, a `cwb` stone throne with a crystal inlay; light audit
  0/0). Rebuilt on the merge point 14 oymap (byte for byte), reinstalled into assets_dev by temp file and rename,
  re-baked (profile `tools/lighting/baked_indoors/profiles/xeen_dd10b.yml`, XD-08's values; `stale_bakes.py` 0).
  Baked retake `output/studio_cal/dd10b/shots/baked2_a.jpg`, looked at: the crystal reads as faceted blue crystal,
  the throne as dressed stone with a crystal slab, the drifts and the stair read right.
- **Waits on A2's row 9160** for the tests from assets_dev (`ASSETS=$PWD/assets_dev output/studio_cal/dd10b/four.sh`).

## Session 7 batch (the God's face, texture fit, mine bed, refill on entry, one size per texture; A8 session 7)

`tools/gen.py` (copy before: `gen_before_s7.py`) and the shared `dd10a/tools/mine.py` (see DD-10A's NOTES).
- **D-37 (4) the God's face**: A6's `xdgodface` once (`fit: true`, its own 256 x 256) on the east wall behind the
  crystal, `panel:god_face`, 448 x 448 from 96 up; hover "God of Minerals" (`evt:god_face` runs the same hook as the
  crystal). The great crystal is cut down to 205–260 and the two lesser crystals at the wall to 120–180, so the
  crystal stands at his chin and his brow and sapphire eyes show over it; the crystal's glow `light:god_face` moved out
  of the crystal to (4800, 352) at 320. Pictures `output/studio_cal/dd10b/shots/s7/01-03` (looked at: a bearded face
  in gold-veined rock, blue eyes, the crystal at his chin; it reads as carved rock, not a poster;
  `first_take/` has the face hidden by the tall crystal).
- **Cart side**, **bed** (`xeen_amb_mine` from the upper drift (512, 2304), the sapphire hall (2880, 2432), the flooded
  drift (3200, 320)), **refill on a fresh entry only** (A3's bug: event 13 refilled on every load; `in_visit`,
  `evt:visit_end`), **one size per texture** (merge point 17): as DD-10A. The playtest pays the God, saves and reloads
  (nothing refilled, refill_b still set), leaves by the adit onto D2 and comes back (refilled): 120 steps (was 108).
- Audit 2 / 0 → 0 / 0; build warnings 0. Recorded, installed, baked; tests from assets_dev 4 of 4 (120, 25, 23 steps;
  `s7_post17.out`).

## Session 21 (A8): AU's sounds

The room-filling beds `sound:bed_flooded`, `bed_sapphire`, `bed_upper` take `pan: false` (D-48); the point sounds keep panning. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 26 (A8): mine door pictures (F12)

- The three plank doors (events 5-7: `door:adit`, `door:throne`, `door:ramp`) showed the timber strip `trim9_32` tiled
  across their leaves; DD-10A's shared `tools/mine.py` `door()` now lays MM6's rough plank door `d2smldor` once, `fit`,
  over each leaf (224 x 320; the ramp's 224 x 288). Edges and tops stay timber.
- Installed 00:56, baked, tests 12 of 12 from assets_dev (`output/studio_cal/a8_s26/run/dd10b/c005552`); audit 0 / 0;
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
- DD-10B: the rails run on along the timbered drift's north leg to its bend (the east leg stays clear: centipedes
  there are wide; three centipedes and a bat moved off the rails); the sapphire hall's and the flooded drift's floors
  slope (the pool's rim kept level by `floor_lines`); the side cut's walls rough. `identity: {shape: mine, family:
  7d35}`. Audit 0 errors / 2 warnings, both the cave-shape check: 30 % of the floor uneven (on its line) and 17 % of
  the wall area rough against 18 % (the throne hall stays cut square by design). check_exits 0, check_drops 0.
- Installed 01:46, baked, tests 12 of 12 from assets_dev (`output/studio_cal/a8_s26/run/dd10b/c014622`).
- Pictures: before `output/studio_cal/a8_s28/dd10b_before_sheet.jpg`, after `output/studio_cal/a8_s28/shots/dd10b_after.jpg`.
- Merge point 42 (oymap's props rules): `support.overhang` error on `deco:saph_crystal` (crclstr), which the vein's
  new crystals lifted 154 off the floor: moved to (3376, 2896). Reinstalled 02:07, baked, audit 0 / 2 (cave shape),
  tests 12 of 12 (`output/studio_cal/a8_s26/run/dd10b/c020658`).

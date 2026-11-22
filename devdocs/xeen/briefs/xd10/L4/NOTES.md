# XD-10 Cave of Illusion, L4: notes

A new M dungeon (no original), story step **M12** (the Enchanted Key from the great skull), built with the Map Studio
from its graph (`devdocs/xeen/mockups/act2_graphs/xd10.graph.yml`) and decider D-4
(`devdocs/xeen/mockups/act2_dungeon_decisions.md`, which wins) by lane A8's sub-agent `agent:xeen-a8-xd10`,
2026-11-20. Key `xd10`, project `xeen_xd10`, stem `xeen_xd10.blv`, map_stats 9126, world `xeen`.

**State (end of session 3).** L1-L4 `oymap validate` no issues, `fmt --check` clean. Installed in the Xeen world
(`assets_dev/worlds/xeen/maps/xeen_xd10.{blv,scene.yml,studio.yml}`, `events/maps/xeen_xd10.lua`). `oymap audit
xeen_xd10.blv --world xeen --assets assets_dev --reach --solve` on the installed map (`audit.txt`, `solve.txt`): 0
errors, **0 faces in one plane**, 23 of 23 rooms reached (13 with the doors as they start), solve 23 of 23 in two steps
(the mirages, then the plug), both exits to X5, no dressing finding. `tools/xeen/quests.py` reports nothing for XD-10.
**Playtests: all six 4 of 4, exit 0** on the build with D-22.2 (A1's binary dumped core after the last step of every
scenario from 15:52 to about 16:28; it no longer does). `oymap solve` notes that the great skull's gems come from
elsewhere (the Lua's gem list; the echo cave's 15 are in a chest), information only.

**Scratch** `output/studio_cal/xd10/`: `tools/gen.py` (plan, project, diagram; `python3 gen.py L1 L2 L3 L4`),
`tools/geo.py` (rooms, openings), `tools/dress.py` (objects, wiring), `tools/tour.py` (`tour.py water|rooms <name>`
writes `shots/<name>.yml`); `go.sh` (generate L4, fmt, validate, build, install into assets_dev, record; `INSTALL=0`
builds only), `four.sh` (the six playtests N times, one game at a time, exact PIDs; `TESTS=`, `N=`), `shoot.sh <tour>`
(one desktop tour run, exact PID; it fails while the 15:52 binary dumps core in run_game.sh's own preparation),
`shoot_direct.sh <tour>` (the same tour with the binary run directly, minimized, from a copied wrapper settings file and
start save in the scratchpad's `tourrun/`); `audit.txt`, `solve.txt`, `scale_bands.txt`, `dress_check.txt`, `xexport.json`,
`plan3.png`, `iso3.png`; `shots/water3_sheet.jpg` (the moving-water check); `run/` (logs).
**Every project file of L1-L4 except the playtests and these notes is written by the generator**; each run recorded
with `oymap record --author agent:xeen-a8-xd10`.

## The cave

Three levels in one frame (x east, y north, heights from the arrival floor):

| Level | Rooms | What |
|---|---|---|
| Upper caves (0) | north mouth (arrival, snow, icicles; exit to X5), behind the mirage (cache), phantom safe, icicle hall, Hall of Mirages (roof to 1,024, a rock column), frost cavern, skull alcoves, sluice (bricks, the plug in its pool, a railed window over the reservoir), south mouth (exit to X5) | 15 Flying Feet, 7 Guardians |
| Drowned galleries (-640) | ledge over the water (railed, the notice), mirror maze (four ice-faced rock islands), deep skull alcoves, Guardian post, echo cave, drowned gallery (two pools) | 6 Flying Feet, 5 Guardians, 3 Water Golems |
| Reservoir bed (-1280) | reservoir (a cavern 3,200 by 5,376 from -1280 to a roof at +448 to +704), sunken boat (the hull, casks), sump (the hole), grotto of the great skull, phantom vault | 9 Flying Feet, 5 Water Golems |

Three tunnels join the levels: the **ice stair** (from the hall's north-east corner, round a bend, down 640 to the
ledge), the **reservoir steps** (ledge to the bed, behind a sluice gate) and the **gallery stair** (drowned gallery to
the wreck, behind a sluice gate). Caves are chamfered outlines with `rough` walls, roofs by `ceiling_points`,
stalactites (ice at the mouths and in the icicle hall).

**Measured:** 24 sectors (23 rooms; M 20-45), **54.8 M units² of floor** (M 30-90), 8 doors (four mirages, three
sluice gates, the sluice's door) and two movers (11 door records), 5 chests, 50 placed monsters, 21 lights, 9 placed
sounds. Scale bands (`scale_bands.txt`): upper-quarter room 2.06 M (shipped median 1.64 M, percentile 65), typical
ceiling 576 (median 521), upper-quarter height 832 (median 570), doorways 384 (median 256).

## Monsters (all placed, Xeen rows of A2)

| Who | Row | Level | Where | Count |
|---|---|---|---|---|
| Flying Feet | 11600 | 18 | north mouth 2, icicle hall 4, phantom safe 2, Hall of Mirages 3, frost cavern 2, south mouth 2, mirror maze 4, echo cave 2, sump 1, wreck 2, reservoir 4 (hidden), vault 2 | 30 |
| Guardian | 11601 | 24 | Hall of Mirages 2, frost cavern 2, sluice 3, mirror maze 1, post 4 | 12 |
| Water Golem | 11591 | 28 | drowned gallery 3, sump 2, reservoir 2 (hidden), vault 1 | 8 |

**50 at load** (groups of 2-5 by room; `playtest_hostility.yml` asserts 30, 12, 8, 50). **Kill XP** L(L+10): 30 x 504
+ 12 x 816 + 8 x 1,064 = 33,424 for the party, **8.36k per member** (MAPS 8.1k, +3 %; A2 counted 1.03).

**The reservoir's six (D-18 (c)).** 2 Water Golems and 4 Flying Feet placed `hidden` in their own group 10 on the bed
under the water, about 1,200 from the two ways onto the bed (the steps' foot at (2816, 2496) and the wreck's opening at
(2816, 1792)): (4032, 2496), (3904, 1152), (4032, 1600), (4096, 2944), (3840, 3392), (4160, 2112).
`evt:bed_walked` is a step event on the reservoir's own floor (so any way onto the bed runs it: the steps' gate, the
gallery stair's gate through the wreck), condition `{qbit: plug_pulled, not: {map_var: bed_revealed}}`, effects
`show_actors: 10`, `bed_revealed` = 1 and the line "Shapes stir in the silt of the drained bed." The guard is the map
variable `bed_revealed` (a refill resets it with the actors), not the studio's `once` (which is a map variable too,
`once.*` in ids.lock.yml, but the brief asked for an explicit one). Played: before the step `actor remaining` lists the
six as hidden, standing on the water's top as it sinks and on the bed after it (z -1300 before the water's end was
raised to 2 under the bed; now on the bed); after the first step none is hidden, none is peaceful (`actor_count`
hostile false max 0), they walk at the party; after `save_game`/`load_game` none is hidden and `bed_revealed` is still
1.

## Mechanisms (two states each)

- **Mirages** (D-4 item 1). Four doors (`door:mirage_safe`, `_cache`, `_maze`, `_vault`), each a leaf of the cave rock
  `t68a02b` with the **fluid bit** (`liquid: liquid`; drawn at its size), `slide_down` at speed 4000 (gone at once).
  A click runs `evt:mirage_<k>` (door preset: open, "The mirage dissipates with your touch.", aaze0042:24, sets the
  map variable `mirage_<k>`); a **touch** is a floor plate before the wall (`plate:mirage_<k>`, the studio has no
  touch trigger) with a step event that opens it once. A pulsing pale light stands before each mirage. None is on the
  critical path. Played: the cache mirage touched from the north mouth, the safe's mirage clicked, the maze and grotto
  mirages touched.
- **The phantom safe**: `platform:safe`, a block of A6's riveted iron (`xwiron`) with the fluid bit, hover name
  "Safe"; clicked: "Your hand passes through the safe as though it were not there." (aaze0042:72). Not a chest.
- **The Potion of Might** (D-22.2): the cache's chest holds no Might Boost; `evt:chest_cache` gives one on the cache's
  first opening, `evt.SetHeldItem(240, {bonus = 10})` (power 10: +30 Might, so any member reaches the plug's 30) with
  "A flask of red draught lies on top.", once per game behind map qbit `cache_potion` **110642**. Played: the potion in
  the hand at the first opening, `cache_potion` set, a second opening gives nothing, Might 15 -> 45 after drinking.
- **The plug** (D-4 item 3): `mover:plug`, a bronze block (`xngong`) in the sluice's pool with its iron chain (a part)
  into the roof; clicked (`evt:plug`, switch preset): condition `{not: {qbit: plug_pulled}, stat: {name: ActualMight,
  at_least: 30}}`. **Played: Might 15 refused ("You aren't strong enough to pull the plug.", aaze0042:23), the
  Potion of Might from the cache drunk by the same member (Might 45: the temporary bonus counts), then pulled.** Pulled:
  the plug rises, the water sinks, the three gates open, `plug_pulled` 110640 is set, a window ("... The water roars
  away down the sump; somewhere below, stone gates grind open."); a later click: "The plug hangs free on its chain.
  Below the window the reservoir lies empty." `evt:drained_load` (a load event) reopens all five after a refill.
- **Draining** (D-4 item 2): `mover:water`, one block in the reservoir's outline (inset 32) from the bed to -660 with
  the flowing water `wtrtyl` on its sides and top, `travel: [0, 0, -638]`, speed 107 (6 s), its top ending 2 under the bed (at first 20 under: the hidden monsters
  standing on it stood 20 in the floor).
  The three stone sluice gates (`door:gate_drowned`, `_steps`, `_wreck`; d33's bricks, the wreck's in two leaves) are
  shut until the plug; clicked before: "The stone sluice gate is shut fast. Water presses against it from the other
  side."
- **Skulls** (D-4 item 4): MM7's skull `7dec20` on rock shelves, hover names "Skull (Luck)", "Skull (Personality)",
  "Skull (Intellect)", "Skull (Speed)", "Great skull". Each is a `script` event in Lua: the member's bit set ->
  `XeenQuests.hook("m12.skull_sold")`; too few gems -> `m12.skull_poor`; else the offer hook (`m12.skull_upper` /
  `m12.skull_deep`) and `AskChoiceWithAnswerSteps` Yes/No; Yes -> `Xeen.payGems(n)`, `AddValue(Base<Stat>, n)`,
  `SetPlayerBit`, a window "+n <Stat> (permanent)". Played: Luck (3 gems, Luck 10 -> 12, a second click "You've had
  yours"), the deep Intellect skull with no gems ("says nothing at all"), then with gems (Intellect 10 -> 13).
- **The great skull**: before the key `XeenQuests.hook("m12.skull")` (A3's: 10 gems, the Enchanted Key 12306, qbit
  111240, 1,500 XP, its own fail and else texts); after it, in D-18 (b)'s order: `m12.skull_sold` if bit 11240 is set,
  `m12.skull_poor` under 10 gems, else `m12.skull_grotto` and **one question with three buttons** (Might, Endurance,
  Accuracy; `AskChoiceWithAnswerSteps` as `Xeen.useMirror` uses it; closing it is no), +5 Base stat for 10 gems, bit 11240 once per
  character across the three. Played: the key with the echo cave's last 10 gems (0 left), then +5 Endurance (10 -> 15)
  with granted gems, then "You've had yours".
- **Gems before the great skull** (D-1.6): the echo cave's chest holds 15 fixed gems (177-186, 177-181), on the way
  ledge -> maze -> post -> echo before the steps; the ledge's notice (`panel:notice`, a plank board, a window):
  "THE SKULLS TAKE GEMS, NOT GOLD. THE GREAT ONE AT THE BOTTOM WANTS TEN FOR HIS KEY - KEEP TEN. THE ECHO CAVE PAST THE
  GUARDIANS' POST KEEPS SOME. THE PLUG IN THE SLUICE LETS THE WATER OUT, IF YOU ARE STRONG."

## Moving water (A1's open question, answered here)

**The moving fluid face draws right indoors.** Checked on the installed map with a tour from the ledge's rail
(`shots/water3/`, sheet `shots/water3_sheet.jpg`; the water mover opened by the console `lua
evt.SetDoorState(10, DoorAction.Open)`): at the start the reservoir is a sheet of rippling water (`wtrtyl`, the
stalactites reflected) about 20 under the ledge; 1 s and 3 s after, the surface stands lower with more wall showing
above it and still draws as water; at the end the bed (`t68a03a`) is dry. Collision: the main playtest walks the party
down the steps onto the drained bed and asserts it stands on it (z -1300 to -1240 at (3300, 2496)), then crosses it to
the grotto and back to the wreck. **D-4's fallback (a face swap behind a fade) was not needed.** Not checked: a party
on the water's top while it sinks (the ledge's sill of 128 keeps it off).

A1's answer (A1.md "Answered for A8", merge point 8) is the same route: a door mover, no engine change, solid. A1
advises making only the top face the mover, because side faces coplanar with the walls flicker. **I kept the whole
block:** its outline is the reservoir's inset by 32, so its sides stand 32 inside the walls (the audit finds 0 faces in
one plane) and they show water while it sinks. No bake profile (no `shadowless_faces` needed).

Mirage ripple: in two pictures 0.5 s apart from 300 before the phantom safe's mirage (`shots/fix1/06`, `07`) the
leaf changes about twice as much as the plain rock beside it (mean difference 33 against 17; the pulsing light before
it changes both), so the fluid bit does move the picture on a wall. It is subtle: in a still the mirage reads as a
slab of rock with a frame. **Not replaced with a Codex shimmer texture**; look in play (below).

## Exits (linked to X5) and arrival

- `exit:north` (the north mouth's north wall, MM8 `snow` as daylight) -> `exit:x5_north`: `xeen_x5.odm` at (16640,
  9987, 1408) facing south (1536). `exit:south` (the south mouth's south wall) -> `exit:x5_south`: (6915, -9472, 1216)
  facing west (1024). Both "Leave the Cave of Illusion" (aaze0042:49; the game's own question). solve lists both.
- X5's doors (events 91 and 110) enter at this map's start: the north mouth, (0, 9664, 0) facing south.
- `evt:arrive`: a one-shot timer window on the first arrival only (`arrived_once` 110641): "THE CAVE OF ILLUSION. Warm,
  wet breath blows out of the ice into your faces. Artemus was plain about it: somewhere deep in this cave a talking
  skull sells the key to the Tower of High Magic, and skulls take gems, not gold. Mind the walls here: not all of them
  are there." Played (and qbit asserted).

## Original lines

"The mirage dissipates with your touch." (aaze0042:24); "Your hand passes through the safe as though it were not
there." (aaze0042:72); "You aren't strong enough to pull the plug." (aaze0042:23); "Leave the Cave of Illusion?"
(aaze0042:49); the key lines are A3's hook (aaze0045:48, :54).

## Ids

- Map qbits: `plug_pulled` **110640**, `arrived_once` **110641**, `cache_potion` **110642** (of 110640-110679; A3 to
  register 110642). Quest bit:
  `key_bought` 111240 (A3's hook).
- Player bits (registered in m12.yml): 11236 Luck, 11237 Personality, 11238 Intellect, 11239 Speed, 11240 the great
  skull (one of Might, Endurance, Accuracy).
- Map variables: `mirage_safe`, `mirage_cache`, `mirage_maze`, `mirage_vault`.
- Items: Enchanted Key 12306 (hook), Might Boost 240 (given by evt:chest_cache at power 10), gems 177-186 (echo cave).

## Textures (one family)

**21 distinct of 45, 0 new** (`tools/xeen/texture_budget.py`). **MM8 Passage Under Regna (`d33.blv`)** everywhere: rock
`t68a02b` (walls, roofs, the mirages with the fluid bit), granite `t68a03b` (upper) and `t68a03a` (lower), bricks
`t09a01` (sluice walls, sluice gates), flags `t09a02b`, trim `t09b11b`, the sluice door `t09a03c`, timber/planks
`t09a05b` (the boat). Where d33 has none: MM6 Icewind Keep's ice `orair32` (the maze's islands, at scale 4), MM8
`snow` (the mouths' floors, their daylight, the icicles), MM8 flowing water `wtrtyl`, the world's `xngong` (plug),
`xnrustirn` (chain), `xwiron` (the safe). For A6: XD-10's family is d33 + orair32/snow.

## Dressing (D-7)

`oymap audit --world xeen` (build-xeen's, with A1's recalibrated dressing checks) on the installed map: **0 dressing
findings** (it found one error in the first L4: a rock 53 from the drowned gallery's walking line; moved). A7's
`check_dressing.py` on the export: 23 floor props (2 containers), **0 findings** (it found the wreck's cask 286 from a
portal; both casks moved to the wreck's south-west corner as a pair). Props: skull piles by the skulls, stalagmites
against walls, rocks in the drowned gallery and the sump, casks by the wreck; the reservoir's bed has **no props**
(the studio refuses a decoration under the water mover: it would stand in the block at the start).
**Dressing exceptions:** none.

Build warnings kept, each explained: the liquid `t68a02b`/`xnrustirn` lies on faces without the fluid bit (the
mirages and the safe ripple by design, the rest of the rock does not); `evt:plug` "a click does nothing the player
sees" (its `else_effects` Lua shows one of two lines; played); the arrival warning (the timer has a condition).

## Playtests

`output/studio_cal/xd10/four.sh` from assets_dev, `--world xeen --map xeen_xd10.blv` (the way-in tests
`--map xeen_x5.odm`); A2's row 9126 is in the world's tables, no test mount. Logs `run/four_*`.

| Test | Steps | Runs, every step passed | Exit |
|---|---|---|---|
| `playtest.yml` | 161 | 4 of 4 (`four_163147`, after D-22.2) | 0 |
| `playtest_hostility.yml` | 20 | 4 of 4 (`four_162916`, after D-22.2) | 0 |
| `playtest_exit_north.yml` | 13 | 4 of 4 (`four_162916`) | 0 |
| `playtest_exit_south.yml` | 15 | 4 of 4 (`four_162916`) | 0 |
| `playtest_in_north.yml` | 25 | 4 of 4 (`four_162916`) | 0 |
| `playtest_in_south.yml` | 25 | 4 of 4 (`four_162916`) | 0 |

Earlier runs (before D-22.2, `four_160126`, `four_160558`) passed every step 4 of 4 with exit 139 after the last step
(A1's binary of 15:52). In `four_162916` the walk failed twice at the echo cave ("16 gems"): a random roll of the
cache or the post chest was a gem. The walk now drops the party's gems (a `lua_event`) before the Luck skull and
before the echo cave, so its gem counts are the map's own.

- `playtest.yml` (level-18 party, Might 15, immortal): the route is in its header; it asserts the arrival window and
  `arrived_once`, every mirage open (clicked: the line; touched: the door and its map variable), the potion in the
  cache, the safe's line, Luck 10 -> 12 and the second click's "had yours", the plug refused at Might 15 and pulled
  at 33 (the five doors and movers open, `plug_pulled`, "hangs free"), the notice, the deep skull without gems and
  Intellect 10 -> 13 with them, 15 gems from the echo cave, the reveal (above), the key (12306, 111240, 0 gems left),
  Endurance 10 -> 15 and "had yours", the hoard, the wreck, the gallery stair and the drowned gallery's gate.
- `playtest_hostility.yml`: 30, 12, 8 at load (50), none peaceful; a Flying Feet, a Guardian and a Water Golem side by
  side in the frost cavern do not target each other, the last targets the party.
- `playtest_exit_north/south.yml`: the exit event, the game's question, OK, `xeen_x5.odm` within 128 of (16640, 9987)
  / (6915, -9472).
- `playtest_in_north/south.yml`: a new game on X5, 280 before the mouth's face, `press_interact` (X5's events 91 /
  110), XD-10's start, the window once, out by the north mouth, in again, no window.

## Pictures (looked at)

Contact sheets in `output/studio_cal/xd10/shots/` (PNG folders deleted for the disk except `water3/` and `fix1/`; `tour.py` remakes them): `water1..3` (the moving-water check),
`rooms1_s_1..4.jpg` (40 poses: every room, the mirages, the safe, the skulls, the plug, the window, the stairs; shots
31-40 after the console opened every door and the water), `fix1_sheet.jpg` (12 poses after the fixes).
What I changed after looking: the icicles and the mouths' roofs of `orair32` read as blue bathroom tiles (icicles now
MM8 `snow`, roofs rock); A6's `xnnotice` shows "Joe the Exterminator" (the notice is now a plank board, the text in its
window); the phantom safe of `xnrustirn` read as a brown crate (now A6's riveted iron `xwiron`, smaller: it reads as a
safe); a large brown stalagmite model stood in the ice stair's mouth (removed; the other `stlmite2` are `stlmite3`).
Still weak: the mirror maze's ice islands (`orair32` at scale 4) read as glass panes, which suits "mirrors" but looks
built; the reservoir is a plain box with a bare bed; the icicles are stepped blocks; the wreck's hull is a plank block;
the Flying Feet and Guardians show the S lane's stand-in bodies. A tour pose inside the steps tunnel drew black beyond
the camera (`rooms1` 33; a tour pose in a sloped tunnel, as XD-11's defect 1); in play the walk goes down the steps
and the pictures from the ledge and the bed draw right.

## Words needed

1. **A touch trigger** on a door face (D-4's mirages): a floor plate before the wall stands in for it.
2. **Props under a moving liquid**: decorations on a floor that a water mover covers at the start (weed and shells on
   the drained bed); the studio refuses them.

## Tool defects

1. `status()` in `play_lua` sees only the lines of its own step: a line shown during `walk_to` (a step plate's text)
   cannot be asserted; the touches assert the door and the map variable instead.
2. `item_count(12306)` returned other than 1 while `has_item(12306)` was true (a quest item?).
3. `scale_bands.py` gives the largest room as 33.8 M (the reservoir is 17.2 M; its water mover's top counted?).

## Blocked, and requests

- None blocking. X1's stale bake (15:44-15:48, A5) and X5's (16:03-16:05, A6) each stopped Xeen new games for a few
  minutes; both re-baked.
- **A1**: the moving-water answer above (it works); a touch trigger (Words needed 1).
- **A2**: row 9126 as written fits (lock 5, trap 3, perception 5, music 2, CAVE, slots Xeen Construct tier 0 [2, 3]
  75 %, Xeen Elemental Golem tier 1 [2, 3] 25 %); every monster is placed, so the slots only serve the map card.
- **A3**: register map qbit `cache_potion` 110642 in m12.yml (110640 and 110641 are registered).
- **A2**: record XD-10's fixed potion as given by event (Might Boost 240, power 10, once per game), not a chest item.
- **A6**: no new textures; XD-10's family is d33 (+ orair32, snow).

## Next steps, in order (as of the end of session 3)

1. Nothing needed for done.
2. Optional look in play: the mirages' ripple, the maze's ice.

## What the user should look at when playing

- The north mouth: the arrival window, the shimmering west wall (walk into it), the cache's Potion of Might (in the hand, once per game).
- The phantom safe (click it), its shimmering north wall.
- The plug in the sluice: refused at Might under 30, pulled after the potion; watch the water sink from the window.
- The ledge over the water and its notice; the drained bed seen from the rail.
- The skulls: buy once per character, then try again; the great skull's key and its three-answer stat question.
- Whether the mirages read as illusions and whether the bare drained bed and the plain reservoir walls look right.

## Merge point 13 (lane A8 session 5, 2026-11-20): mirages by touch, first bake

- The studio's `touch: true` (merge point 13) on the four mirage door events: walking into a mirage runs its event
  ("The mirage dissipates with your touch.") and opens it; the four plates before the walls and their step events are
  gone (`tools/dress.py`, copy before `dress_before_touch.py`; `gen.py`'s texts). The scene has
  `party_movement: {touch_faces: run}`. `playtest.yml` walks into the cache's mirage (`walk_to` into the cache) and
  into the maze's and the grotto's (`movement_segment` forward from the wall), 163 steps.
- Rebuilt on the 18:33 oymap (`b_184234`), installed by temp file and rename; **first lighting bake** (profile
  `tools/lighting/baked_indoors/profiles/xeen_xd10.yml`, XD-08's values; `stale_bakes.py` 0).
- **Six tests 4 of 4** from assets_dev on the 18:28 game (`four_touch.out`, `run/four_184420/`): playtest 163,
  hostility 20, exit north 13, exit south 15, in north 25, in south 25.

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/xd10/tools/dress.py`, copy before the
change `dress_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- No light finding. **Named arrival for A6:** `arrivals` gains `entrance:x5_south` in `room:south_mouth`, just inside
  the south mouth at **(64, 1408, 0) facing north (512)**, into the cave; `xeen_xd10.studio.yml` lists it. X5's south
  door can name it: `arrival: entrance:x5_south` (today it lands at the north start). The map's files other than the
  studio file are byte for byte as before, so no re-bake.

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/xd10/audit_lights.txt`): lights
  errors/warnings before **0/0 (clean)**, after **0/0**; no dressing finding. **Light exceptions:** none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh xd10` (build `output/studio_cal/xd10/b_192658`), not
  re-baked (the .blv and .scene.yml are byte for byte the merge point 13 build's; `stale_bakes.py --check` lists none).
  **Playtests from assets_dev, each 4 of 4** (four.sh; record `output/studio_cal/xd10/lights_post.out`): playtest 4/4
  (163 steps); playtest_hostility 4/4 (20 steps); playtest_exit_north 4/4 (13 steps); playtest_exit_south 4/4 (15
  steps); playtest_in_north 4/4 (25 steps); playtest_in_south 4/4 (25 steps). (`playtest_in_south` still enters by X5's
  door as it is today, at the north start; once A6 points the door at the arrival, it should assert the south mouth.)
- **Pictures** none (no light changed).

## Session 7 batch (texture fit, drain sound, A8 session 7, 2026-11-20)

- **Plug (merge point 16, 6 `feature_repeated` on `xngong`)**: the gong picture was tiled 1.8 times over the plug's
  224 x 224 top and 224 x 144 sides. Now (`tools/geo.py` `PLUG_TOP`, `PLUG_SIDE`; `tools/dress.py`; copies before:
  `*_before_s7.py`): the top shows `xngong` once, whole (scale 1.75, offset [46, -46] to the plug's corner: a mover's top
  takes no `fit`; the two axes' offsets have opposite signs, measured with `--textures-measure`: whole 0.99 x 0.99);
  the sides take the gong's ringed edge slab `xngong6` at scale 2 (a tile). Audit 6 / 0 → 0 / 0.
- **Sound**: AU's `xeen_reservoir_drain` (62508) plays at the plug (2048, 2944, 0) when it is pulled (`evt:plug`).
- **Way in from X5's south mouth**: A6's door now names `entrance:x5_south`; `playtest_in_south.yml` asserted the old
  start (0, 9664) and now asserts (64, 1408).
- Recorded, installed, baked; tests from assets_dev 4 of 4 (163, 20, 13, 15, 25, 25 steps; `s7_post.out` and
  `s7_in_south.out`). Pictures `output/studio_cal/xd10/shots/s7/` (looked at: a bronze plug in its pool, the runed
  gong face once on top, ringed bronze sides).

## Session 26 (A8, 2026-11-22)

- The bronze plug's refusal adds A3's hint: "You aren't strong enough to pull the plug. A stronger arm, or a potion of
  Might, might shift it." (status line, 6 s). Lua and studio file only (no bake).
- F16 on X5 (rebuilt 00:02 with MP40): both way-in tests answer the standard entrance window (OK) before the move.
- Drop pockets (`check_drops`, by hand): the skull shelves' tops (rise 96, out of reach) and the plug's own 64-deep
  pool (the plug fills it): no change.
- Tests 24/24 from assets_dev; audit 0 / 0.

## Session 28 (A8): D-89 identity (darker deep rock, uneven floors)

The design review (`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2, severity 3: "boxy caves in one grey rock with flat
floors; the illusory walls are blue glass grids") asked for irregular outlines and slopes across d33's rocks, illusory
walls in their neighbours' rock, weed and silt on the drained floor, ice only at the two mouths. In `tools/geo.py`'s
"D-89 identity" block (+ `dress.py`, `identity:` in `gen.py`); the generator reproduced the installed L4 first
(snapshot `output/studio_cal/a8_s28/before/xd10/`).
- The drowned galleries, the reservoir bed, the wreck, the sump and the grotto (`theme:deep`) in d33's darker rock
  `t68a02a` (walls and roofs); the upper caves keep `t68a02b`. d33 itself has only these two rocks and its granites.
- The four mirages already wear the cave rock with the fluid bit (since session 7); the two in deep rooms (mirror
  maze, grotto) now wear `t68a02a` like the rock round them. The mirror maze's glass panels are its mirrors (by design),
  not mirages.
- Uneven floors (`floor_points`, up to 40 over or 24 under) in the icicle hall, the Hall of Mirages, the frost
  cavern, the Guardian post, the echo cave, the cache and the phantom vault.
- Weed on the reservoir bed could not be placed: the bed lies inside the water mover at the map's start, and the build
  refuses objects there; its dark granite stands for the silt. Ice was already only at the two mouths.
- `identity: {shape: cave, family: d33}`. Audit 0 errors / 1 warning (cave shape: 13 % of the wall area rough against
  18 %: the sluice's brick and the stair tunnels). check_exits 0; check_drops 1 pocket, the plug's 64-deep pool (by
  design, see above).
- Installed 01:55, then again on oymap merge point 42 (the style chest), baked; tests from assets_dev 24 of 24
  (`output/studio_cal/a8_s26/run/xd10/c015512`; on merge point 42 24 of 24 again, `c021106`).
- Pictures: before `output/studio_cal/a8_s28/shots/xd10_before.jpg`, after (baked)
  `output/studio_cal/a8_s28/shots/xd10_after.jpg` (tour `tools/tour.py rooms`).

## Session 29 (A8, 2026-11-22): identity family

- `tools/xeen/check_identity.py` (A7) measured 44 % of the map in d33's textures: the 28th session's "d33's darker rock
  t68a02a" is MM8 d17's rock, not d33's. The deep theme's walls are now d33's own dark granite t68a03a (128), the deep
  ceilings d33's wet rock t68a02b; the deep mirages wear t68a03a too. Family share 79 %. The rough-wall share (13 %)
  stays below the cave-shape number, accepted by the orchestrator (session 28 DECIDE).
- Installed, baked, audit 0 / 1 (cave shape), drops 1 (as before), tests 24/24 from assets_dev
  (`output/studio_cal/a8_s26/run/xd10/c024129`).

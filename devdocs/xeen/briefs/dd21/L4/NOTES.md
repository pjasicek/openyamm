# DD-21 Necropolis Sewer, L4: notes

New S dungeon under D6's Necropolis (dark maze0036 and Sandro's lines from maze0035), side quest Q-D23 Sandro's Heart
(Promo Lich / Priest of Dark), built with the Map Studio from `devdocs/xeen/mockups/act5_graphs/dd21.graph.yml` and
decider D-62 (`mockups/act5_a8_decisions_b.md`, which wins) by `agent:xeen-a8-dd21` (lane A8 session 13), 2026-11-21.
Key `dd21`, project `xeen_dd21`, stem `xeen_dd21.blv`, map_stats 9174, world `xeen`, music 11.

## State and next steps

**Built in the scratch root only** (`output/studio_cal/dd21/root`: `cp -al assets_dev`, `worlds/xeen/data_tables/` a
real copy taken after A2's and A3's D-62 rows landed; `xeen_quests.lua` re-linked after A3's rewrite). Validate: no
issues; build 0 warnings (no "two sizes for one texture"); audit of the installed map (`--reach --solve`,
`output/studio_cal/dd21/audit.txt`) and of the project (`audit_project.txt`): **0 errors, 0 warnings** (fit, doors,
lights, dressing), two `click.silent` infos on the bier (impossible qbit states). Solve: 13 of 14 sectors at once, the
reliquary after released (and the heart culvert after sluice_open); the exit to D6 listed. Texture budget 28/30, 1 new.

**Next (the lane lead):** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd21`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd21` (bake from xd08's profile
template, then `four.sh` from assets_dev). Baked pictures: `ASSETS=$PWD/assets_dev output/studio_cal/dd21/shoot.sh
things1`. A6 then unseals D6's `door:dd21` (arrival `entrance:d6_stair`).

**Resume:** `RECORD=1 LABEL="..." output/studio_cal/dd21/cycle.sh` (gen.py, fmt, validate, build, install into the root,
audit, record; `LEVELS="L1 L2 L3 L4"` for all). Diff the L4 against `.oymap/last` first if anyone edited it by hand.
`output/studio_cal/dd21/refresh.sh` prints the commands that refresh stale world files in the root.

**Scratch** `output/studio_cal/dd21/`: `tools/gen.py` (plan, project, diagram), `tools/geo.py` (rooms, openings,
themes, furniture), `tools/dress.py` (objects, wiring), `tools/tour.py rooms|things <name>` + `tools/sheet.py`,
`tools/texsheet.py`, `cycle.sh`, `four.sh` (`ASSETS=`, `N=`, `TESTS=`, `LOCK=`; every game through
`a8_s13/game.lock` and `a8_s9/slot.sh`), `shoot.sh <tour>`, `explore/` (probes), `run/` (logs), `shots/` (sheets).
**Every project file of L1-L4 except the playtests and these notes is written by the generator.**

## What was built

Three floors in one frame (x east, y north, z up):

- **The crypts (0), MM6 Tomb of Ethric (6d14):** the crypt stair (the arrival at its foot (0, 0, 0); fourteen steps
  north up to a head at 448 and the grille pair, two exit faces `gkp103a`/`gkp103b`), the Hall of Biers (1,024 x
  1,792: burial niches `d2niche1`/`d2niche4` at the floor, three stone biers between them, candles; Sandro's seal
  `xdsandro` once over the double doors; the railed stair's head in the west wall), Sandro's crypt (four carved posts
  `d2wlbpos`, the dais and his bier, skull piles and candlesticks; the reliquary's grille in the east wall), the
  reliquary (the chest, the statuette on its plinth).
- **The sewer (-512), MM6 Free Haven Sewer:** the stair landing (two storeys: its head at 0 off the hall, sixteen
  railed steps down along its north wall), the main channel's west and east arms (sewage `swprrf3` along the north
  wall, the walkway south of it, drains `d1lggrt` in the south wall), the mummy's vault (mossy `d1medbw`, behind the
  iron door `crsmdr1`), the dead-food cellar (six barrels in pairs by the walls; iron door `d8dora`), the west and east
  culverts (L-shaped: south, then in to the outfall; sewage along the outer walls; the sluice room's door and the Box's
  niche in the inner walls), the sluice room (the wheel), the outfall (a round basin; the culvert gate in its south
  wall).
- **The lowest culvert (-896):** the heart culvert (two storeys: the gate's head at -512 and twelve steps down; the
  cistern; the jar on its ledge with a green light).

## Measurements

`oymap metrics` (`output/studio_cal/dd21/metrics.json`): **14 sectors** (S at most 15), **17.67 M units² of floor**
(S at most 20; the graph's "about 11" counted the rooms smaller), 1 loop (the sewer ring), **6 doors** (7 leaves: the
crypt's pair, the grille, the vault's and two iron doors, the culvert gate) + the grille pair's two exit faces (the
graph's 8), the wheel, **3 chests** (T5), 16 placed monsters + the risen Sandro (not counted). Textures
(`tools/xeen/texture_budget.py --root output/studio_cal/dd21/root --map DD-21`): **28 of 30, 1 new** (`xdsandro`).

| Who | Row | Level | XP | Where | Count |
|---|---|---|---|---|---|
| Cinder Roach | 11363 | 40 | 2,000 | west arm 3, east arm 2, east culvert 2, heart culvert 1, the Dead Food barrel 2 (hidden) | 10 |
| Greater Lich | 11281 | 50 | 3,000 | Hall of Biers 2, heart culvert 1 | 3 |
| Ghost Mummy | 11273 | 62 | 4,464 | the vault | 2 |
| Sandro | 11283 | 65 | 4,875 | his crypt (group 5) | 1 |
| Sandro (risen) | 11926 | 65 | - | by his bier, hidden until his fall (group 30), peaceful, immobile, no damage | 1 (not counted) |

**Kill XP** 42,803 for the party, **10.70k per member** (D-62). Groups 2-3; the stair, the landing, the sluice room, the
outfall and the reliquary are quiet. Rest encounters (= A2's row 9174): `{monster: Xeen Mummy, tier: 0, per_marker:
[1, 2], weight: 100}`, encounter 10.

## Mechanisms

- `evt:arrive` (timer, once): dd21_arrived_once 117720 and a status line (map-local, for A3).
- **Sandro's fall** (`evt:sandro_fell`, a timer on the kill of `monster:sandro`): sandro_fell 117727,
  `q-d23.sandro`, the risen Sandro's group shown, the fallen body's hidden, the risen made unkillable at once.
  **Load events:** `evt:risen_show` (117727 set, released clear: show 30, hide 5), `evt:risen_gone` (released: hide
  both), `evt:risen_figure` (`SetMm9ActorCanReceiveDamage(ActorIndex("monster:sandro_risen"), false)`).
- **First entry** (`evt:first_entry`, a step on the crypt's floor): `q-d23.first_entry` (sandro_met 117722, once).
- **Talk** (`evt:dais`, the dais's step; `evt:bier`, the bier's click): from 117727 while released is clear,
  `q-d23.sandro` (its beaten or heart text); with the heart its text stands over Yes/No (see DECIDE 1); Yes: "Ask
  Sandro for his ritual first?" when somebody can learn it (`XeenQuests.can("q-d23.ritual")`, taught clear), Yes runs
  `q-d23.ritual`; then `q-d23.release`; on success the grave-dust puff (`mm9:smoke`) and the risen Sandro hidden. The
  bier before his fall "Sandro's bier.", after the release "Sandro's bier, empty. Grave dust lies over it."
- **The grille** (`evt:grille`): `q-d23.grille` before the release (aaze0035:29); `evt:grille_opens` (timer) lifts it
  once released 113462 is set (again after a refill).
- **The sluice** (`evt:wheel`): `q-d23.sluice_wheel` (sluice_open 117721, once) and the culvert gate lifts; a second
  turn shows its else line. `evt:gate`: `q-d23.culvert_gate` while shut. `evt:gate_up` (timer) lifts it again after a
  refill.
- **The heart** (`evt:jar`, the ledge): `q-d23.heart`.
- **The Dead Food** (`evt:dead_food`, the barrel): `q-d23.dead_food` (Might 30 for the clicking member; the first pry
  sets dead_food_pried 117723 and feeds; later pries feed whoever has not eaten, player bit 11378).
  `evt:barrel_roaches` (timer): once 117723 is set, shows the barrel's two roaches once (map variable `roaches_out`;
  no load event, D-18). The other barrels: `q-d23.barrel_sign`.
- **Drains:** three finds once (drain_1 117724 900 gold, drain_2 117725 a level-5 ring, drain_3 117726 1,200 gold),
  then "Nothing here."; three "Nothing here." (aaze0036:3, :1). The outfall's alcove "Nothing here." (aaze0036:0).
- **Exits:** the grille pair's two wings (`exit:wing_left`, `exit:wing_right`, the exit preset, title "Climb up to the
  Necropolis", A3's `q-d23.stair_exit`) to D6's `entrance:dd21_stair`.

## Arrivals and exits

| Inside arrival | At (x, y, z), facing | Measured headless | From |
|---|---|---|---|
| `entrance:d6_stair` (= start) | (0, 0, 0), south (1536) | (0, 0, 0) facing 1536 | D6's `door:dd21` (A6, still sealed): `evt.MoveToMap(0, 0, 0, 1536, 0, 0, 0, 0, "xeen_dd21.blv")` |

| This map's way out | To | Measured | Facing |
|---|---|---|---|
| the grille pair (either wing) | D6 `entrance:dd21_stair` (17408, -11776, 1664) | **(17408, -11776, 1665)** | 512 |

## Ids

- Map qbits (A3's names): dd21_arrived_once 117720, sluice_open 117721, sandro_met 117722, dead_food_pried 117723,
  drain_1 117724, drain_2 117725, drain_3 117726, sandro_fell 117727 (117728 unused). Read: beaten 113460,
  heart_found 113461, released 113462, taught 113463. Player bit: 11378 (A3's Dead Food).
- Map variables: grille_open, gate_up, roaches_out (+ `once.arrive`).
- Groups: 1 liches, 2 roaches, 3 mummies, 5 Sandro, 20 the barrel's roaches (hidden), 30 the risen Sandro (hidden).
  Actor indices: 0-1 the barrel's roaches, 15 Sandro, 16 the risen Sandro.

## Playtests

`output/studio_cal/dd21/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map xeen_dd21.blv`.
**All five 4 of 4** (`output/studio_cal/dd21/run/four_053432`, summary `four_s13b.txt`; playtest 175 checks,
heart_first 71, reload 57, deadfood 64, hostility 51). The strike tests use a party of fighters: a Cleric left active
after the fight made 3 weapon attacks of 40 (two failures in `run/four_053131`, `four_053306`).

| Test | What |
|---|---|
| `playtest.yml` | from D6: the arrival (position and facing); the crypt's doors; first entry; the fall (117727, beaten, risen shown and peaceful, fallen hidden); the grille's line; the dais without the heart; the railed stair; a drain's find; the gate refuses; the wheel lifts it (and its second turn); the steps, the jar (the heart, then "An empty jar."); the ring back; the dais with the heart: Yes, the ritual No, the release (key, heart taken, Sandro hidden, the grille lifts), the bier empty; the reliquary chest; out by the left wing to D6 (17408, -11776) facing 512 |
| `playtest_heart_first.yml` | the wheel, the heart before the fight; the fall with the heart (its heart text, 117727 set, beaten clear); the dais: Yes, the ritual Yes (taught), the release |
| `playtest_reload.yml` | after the fall a save and a load (risen shown, peaceful; member 0 healed to 500 HP and selected, struck 40 times, hp 618 unchanged); the release; a save and a load (hidden, the grille open). Session 19: the heal before `select_member` (the cure clears conditions, not HP; a member at 0 HP cannot be selected: the 2-of-4 flake, A1) makes it 4 of 4 from assets_dev (`output/studio_cal/dd21/run/four_084724`, 59 checks each) |
| `playtest_deadfood.yml` | a signed barrel; the weak member refused (aaze0036:7), the strong one pries: +2 Endurance each, the two roaches shown; a save and a load (still shown); a second pry, nobody eats twice; killed, a save and a load (still dead) |
| `playtest_hostility.yml` | 10/3/2/1 hostile at load (the barrel's two counted), none peaceful, the risen hidden; after 117727 and a load the risen shown peaceful; the kinds spawned side by side do not fight; the risen struck 40 times, unhurt |

## Texture fit exceptions

None (audit: 0 texture findings).

## Dressing exceptions

None (audit: 0 dressing findings).

## Waiting on / stand-ins

- No test rows: A2's 11363, 11926 and map row 9174 are used as they landed. 11926 reads party friendly, move stand,
  as D-62 Q41 asks.
- The jar is S's `xeen_heartjar` (row 4047, MM7's vase recast in glowing green glass; A8 session 17, for `dec97`) on
  its ledge, the green light kept; the statuette is MM7's small statue `7dec54` on a plinth (a dwarf; S may supply
  Sandro's statuette).
- `xdsandro` is the lead's real texture (hard-linked from assets_dev).

## Lines for A3 (map-local, written inline)

- Arrival status line: "Sandro's crypts under the Necropolis. Below them runs the sewer, where his heart is said to lie."
- The bier: "Sandro's bier." / "Sandro's bier, empty. Grave dust lies over it."
- The seal: "A heart pierced by a bone, carved in the dark stone over the doors."
- The gate once open: "The culvert gate stands open."
- The drains' finds: "Wedged in the drain's bars, a purse. (+900 gold)", "Something glints in the muck behind the
  bars: a ring.", "Caught in the drain's bars, a dead man's purse. (+1200 gold)".

## Sounds for AU

`xeen_amb_sewer` beds at the landing and the outfall (`pan: false`); `water lapping loop` at the basin and the cistern;
`drip03` in the Hall of Biers; the wheel plays `xeen_winch`; the release's dust is the effect `mm9:smoke` (no sound).
A slow heartbeat loop at the jar is AU's (none placed).

## DECIDE

1. **The dais's question text.** With the heart, `q-d23.sandro`'s heart text ("... Give it to me, and I will be free of
   this life.") stands over the Yes/No buttons: the engine drops a choice's own text ("Give Sandro his heart?") when the
   event has already shown a message. Kept (the hook's line asks the same). Else A3 appends the question to the heart
   text, or the map skips the hook when the heart is carried.
2. **The ritual question only when someone can learn it** (and not yet taught); otherwise Yes releases him at once
   (no "There is nobody here I could teach." before the release).
3. **The sewage cannot be waded** (the walker routes round it): the arms' channels run along their north walls, the
   culverts' along their outer walls, so the doorways and the culvert mouths stay on dry walkways; the sluice room sits
   on the west culvert's inner side and the Box's niche on the east culvert's.
4. **Floor 17.7 M units²** against the graph's "about 11" (S's cap is 20): the two-storey stair rooms and 512-wide arms.
5. **The cistern is the sewer's own sewage** (`swprrf3`), not a black water texture, to stay within 30 textures; the bake
   should darken it.
6. **The first pry also feeds** (A3's hook does both at once).
7. **Arrival line**: a status line (the build asks every new dungeon for one); the stair's foot stays quiet otherwise.

## Pictures (looked at, scratch root, no bake)

`output/studio_cal/dd21/shots/things1_1..3.jpg` (every interactive thing), `rooms1_1..4.jpg` (every room from two
corners and the fixes), `fix1_1.jpg` (a statue tried). Changed after looking: the posts and chests in `cedsqrdk` read
bright red (posts now `d2wlbpos`, chests MM7's `7gt002`); the alcove and one niche texture dropped for the budget. The
tours' `SetMonGroupBit` does not show hidden groups in pictures (the playtests check them).

## Session 21 (A8): AU's sounds

`sound:heart` (AU's `xeen_heartbeat_loop`, radius 900, inner 250, 0.6) beats in the jar; `evt:jar` stops it once `heart_found` (113461) is set, and `evt:heart_quiet` (load) keeps it off after. Checked in the game (`a8_s21/sndcheck/logs/dd21_game.log`): it starts at the jar, stops at the click, does not start after a reload. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 24 (A8): merge point 35 tests

`playtest.yml`: the culvert walk east to (-640, -2560) clears (1,500): a guard no longer killed earlier (merge point
33's storey-bound clears) stood in it. No map change. 4 of 4 from assets_dev on merge point 35 (143).

## Session 26 (A8): status-line finds

No map change (the generator reproduces the L4; the check build matches assets_dev). The jar's find (`q-d23.heart`) is
a status line since D-90: `playtest.yml` (step 92) and `playtest_heart_first.yml` (step 21) read it from `status()`.
Tests 20 of 20 from assets_dev (`output/studio_cal/a8_s26/run/dd21/t003336`); audit 0 / 0; check_exits 0.

### Drop pockets

- `check_drops` reports the sewer's lower half (-992..-464: the culverts, the sluice room, the heart culvert and the
  cistern; doors 16, 18, 19, lever 39) as one pocket. Not a trap: the stair rooms' flights (steps of 32, e.g. the heart
  culvert's from -512 down to -896) stand over their rooms' continuous floors, so their treads share no edge with them
  and the check misses them. The playtest walks down to the jar (-896) and back up to 0.

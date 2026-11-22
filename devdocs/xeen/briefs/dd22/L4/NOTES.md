# DD-22 Sheltem's Pod, L4: notes

New S dungeon in D6's Ancient field (the source's Escape Pod 2, dark maze0088, aaze0088), optional lore for Act VI,
built with the Map Studio from `devdocs/xeen/mockups/act5_graphs/dd22.graph.yml` and deciders D-62
(`mockups/act5_a8_decisions_b.md`, which wins) and D-65 (`mockups/act6_a8_decisions.md`: B1's hook rule) by
`agent:xeen-a8-dd22` (lane A8 session 14), 2026-11-21. Key `dd22`, project `xeen_dd22`, stem `xeen_dd22.blv`,
map_stats 9175, world `xeen`, music 46.

## State and next steps

**Built in the scratch root only** (`output/studio_cal/dd22/root`: `cp -al assets_dev`, `worlds/xeen/data_tables/` a
real copy taken again at 06:24 after A2's/A3's latest rows; `xeen_quests.lua` re-linked after A3's rewrite). Validate:
no issues; build 0 warnings (no "two sizes for one texture"); audit of the installed map (`--reach --solve`,
`output/studio_cal/dd22/audit.txt`) and of the project (`audit_project.txt`): **0 errors, 0 warnings** (fit, doors,
lights, dressing), three infos (the ladder picture `bemv` squashed as DD-17's; `click.silent` on the blast door for an
impossible qbit state; `AmbientSound1` set and not read). Solve (`solve.txt`): all 12 sectors, the exit to D6 listed.
Texture budget 19/30, 0 new. `oymap fmt --check` clean; L4 recorded.

**Next (the lane lead):** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd22`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd22` (bake from xd08's profile
template, then `four.sh` from assets_dev). Baked pictures: `ASSETS=$PWD/assets_dev output/studio_cal/dd22/shoot.sh
baked1`. A6 then names `entrance:d6_hatch` on D6's `door:dd22` and drops `listed_only` (D-62 RELAYS); after that a
`playtest_in.yml` (from D6 with `m33.done`, the hatch, `entrance:d6_hatch`) can be added.

**Resume:** `RECORD=1 LABEL="..." output/studio_cal/dd22/cycle.sh` (gen.py, fmt, validate, build, install into the root,
audit, record; `LEVELS="L1 L2 L3 L4"` for all). Diff the L4 against `.oymap/last` first if anyone edited it by hand.
`output/studio_cal/dd22/refresh.sh` prints the commands that refresh stale world files in the root.

**Scratch** `output/studio_cal/dd22/`: `tools/gen.py` (plan, project, diagram, atmosphere), `tools/geo.py` (rooms,
openings, holes, furniture, the dome), `tools/dress.py` (objects, wiring), `tools/tour.py rooms|things <name>` +
`tools/sheet.py`, `tools/texsheet.py`, `cycle.sh`, `four.sh` (`ASSETS=`, `N=`, `TESTS=`, `LOCK=`; every game through
`a8_s14/game.lock`), `shoot.sh <tour>`, `run/` (logs), `shots/` (sheets). **Every project file of L1-L4 except the
playtests and these notes is written by the generator.**

## What was built

Escape Pod 2 upright in its crater: three decks 448 apart round a lift spine (x east, y north, z up; z 0 the hatch
sill = D6's 1,952), MM6 Control Center (`sci-fi.blv`) in its red accents.

- **Deck 1 (0, ceilings 320):** the airlock (the arrival; the hatch's inner face `swdoora` in its south wall at y
  -1024, the exit), the lower ring (an L round the shaft's foot, its outer corner cut; the maintenance hatch
  `swtrpnl` in its east arm), the shaft's foot (lift A's red pad, its button), the stores (west; locker, barrels and
  kegs in pairs in the corners), the drive room (north; red floor grilles `swrdk2` a step of 24 down with a pulsing red
  glow, the two dormant devices `swaled`, the cold stasis generator `swor2` and its tool rack), the maintenance ladder
  (in the hull's thickness, up through the gun deck's floor hatch).
- **Deck 2 (448, ceilings 768, teal `swankdk`):** the middle ring (lift A's well, lift B's pad, both buttons on the
  north wall), the gun deck (east; Phaser and Photon Control against the hull; the ladder's hatch), the brig (west; two
  dark stasis cells `swrdk2` in the west wall, the guards' locker), the security post (north of the brig, red floor,
  charging alcoves `swared`, the console, a pulsing red alarm light).
- **Deck 3 (896):** the bridge landing (lift B's well and button; the blast door, two leaves of one `swdoora` parting in
  the middle, DD-17's pattern) and the bridge (the set piece): a dome of dark red-pilot panels (`swll5dk`) leaning in to
  an oculus open to the Darkside's sky (`atmosphere.yml` `xeen_darkside_fading`), two dark steel rings under it,
  Sheltem's empty command couch on its dais facing the nose, the main and scanning consoles against the north wall with
  flickering red lights, the log computer (a `trekscrn` screen in a riveted frame) on the east wall; red light.

## Measurements

`oymap metrics` (`output/studio_cal/dd22/metrics.json`): **12 sectors** (S 6-15; the audit counts 13 with sector 0),
**8.34 M units² of floor** (S at most 20; the graph's "about 10"), 1 loop (lift A up, the ladder down), **7 doors**
(8 leaves: the airlock's, the stores', the maintenance hatch, the gun deck's, the brig's, the security post's, the
blast door pair) + the hatch's exit face = the graph's 8; 2 lifts, 4 buttons, 1 ladder; **3 chests** (T6) + the rack's
find; 20 placed monsters; 18 lights. Every door 256 high or more (the blast door 320; D-32).

| Who | Row | Level | XP | Where | Count |
|---|---|---|---|---|---|
| Patrol | 11610 | 50 | 3,000 | lower ring 2, drive 2, stores 2, gun deck 2, brig 2, security 1, landing 2, bridge 1 | 14 |
| Annihilator | 11611 | 62 | 4,464 | drive 1, gun deck 1, brig 1, security 2, bridge 1 | 6 |

By deck 7 / 9 / 4. **Kill XP** 68,784 for the party, **17.20k per member** (D-62). One group (1). Quiet: the airlock,
the shaft's foot, the middle ring, the ladder. Rest encounters (= A2's row 9175): `{monster: Xeen Robot, tier: 0,
per_marker: [1, 2], weight: 100}`, encounter 10 (Patrol only at Dif 0).

## Mechanisms

- `evt:arrive` (timer, once): dd22_arrived_once 117760 and a status line (map-local, for A3).
- **The lockdown:** `evt:blast` (the blast door's click while the lockdown holds) calls A3's `dd22.blast_door` (its fail
  text); `evt:security_console` asks "Security lockdown: bridge sealed. Release?" with **no message before it** (D-65
  B1: the prompt keeps its text; the playtest asserts it); Yes calls `dd22.security_console` (117761, once), opens both
  leaves for good (D-43) and stops the alarm (`AmbientSound1` 2); later clicks show the hook's else text.
  `evt:lockdown_load` keeps the door open and the alarm off on every load.
- **The lifts:** `lift:a` (shaft's foot 0 to the middle ring 448) and `lift:b` (middle ring 448 to the landing 896), 16
  thick, each rising through a hole in the deck above; each button toggles its lift (call or ride) with `xeen_lift`.
- **The log computer** (`evt:log`, D-47 Q19's pattern): each click shows A3's next page `dd22.log_page_1..6` with a
  chirp (`tone2`), wrapping round after the sixth (map variable `log_page`); page 6's hook adds autonote 4139.
- **Weapons** (`evt:phaser`, `evt:photon`): the message aaze0088:2/:3 ends on "Fire anyway?" (B1), prompt "Fire
  (Yes/No)?"; Yes calls `dd22.weapons` ("Nothing happens.").
- **The drive rack** (`evt:drive_rack`): the first search gives one random T6 item (`GiveItem(6, 0)`) and calls
  `dd22.drive_rack` (117762); then "Nothing here.".
- Text: the devices (aaze0088:0), the main and scanning consoles (:5, :6), the couch, the cells, the generator.
- **Exit:** `exit:hatch`, the `exit` preset "Exit Escape Pod 2" (aaze0088:1's meaning, as DD-16) to D6's
  `entrance:dd22_hatch`.

## Arrivals and exits

| Inside arrival | At (x, y, z), facing | Measured headless | From |
|---|---|---|---|
| `entrance:d6_hatch` (= start) | (0, -832, 0), north (512) | (0, -832, 0) facing 512 | D6's `door:dd22` (A6, not yet moving here): `evt.MoveToMap(0, -832, 0, 512, 0, 0, 0, 0, "xeen_dd22.blv")` |

| This map's way out | To | Measured | Facing |
|---|---|---|---|
| the hatch (exit preset, OK) | D6 `entrance:dd22_hatch` (7168, 12288, 1952) | **(7168, 12288, 1953)** | 1536 |

## Ids

- Map qbits (A3's names): dd22_arrived_once 117760, lockdown_released 117761, drive_find 117762 (block 117760-117799).
  No player bits. Autonote 4139 (A3's hook).
- Map variables: `log_page` (+ `once.arrive`). Placed sound 1 = the alarm (`AmbientSound1`).
- Events (ids.lock.yml): blast 2, security console 30, log 25, phaser 27, photon 28, rack 17, hatch 19, lifts 20-23,
  chests 5 (brig), 6 (couch), 7 (stores). Doors: lifts 1-2, airlock 3, blast 4/5, brig 6, gun 7, maint 8, security 9,
  stores 10.

## Playtests

`output/studio_cal/dd22/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_dd22.blv`: **all three 4 of 4** (`run/four_062542`, summary `four_s14b.txt`; playtest 178 checks, exit 21,
hostility 17).

| Test | What |
|---|---|
| `playtest.yml` | from D6 by `MoveToMap`: the arrival (position, facing 512, 117760, its line); lift A up, lift B up; the blast door refused (fail text); lift B down; the brig's locker; the security console's own prompt text, Yes (117761, the alarm off, both leaves open), its else text; lift B up; the log six times (Entry 1-6 of 6, autonote 4139 absent before and present after the sixth), the seventh wraps to Entry 1; the main console; Sheltem's locker; a save and load (the door open, the bit, the alarm off); lift B down; the gun deck: Phaser, Yes, "Nothing happens."; down the ladder (`climb ... down`) to deck 1; the maintenance hatch; the stores' locker; the drive: a dormant device, the rack (its line, 117762, an item), then "Nothing here." |
| `playtest_exit.yml` | from the airlock: the hatch's leave window, OK; D6 at (7168, 12288, 1953) facing 1536 |
| `playtest_hostility.yml` | 14 Patrols and 6 Annihilators hostile at load, none peaceful; both kinds spawned side by side do not fight each other and go for the party |

A new game started in this map does not take the start's facing (playtest_exit asserts the position only; the walk's
`MoveToMap` arrival asserts 512).

## Texture fit exceptions

None (audit: 0 texture findings).

## Dressing exceptions

None (audit: 0 dressing findings).

## Waiting on / stand-ins

- No test rows: A2's 11610, 11611 and map row 9175 and A3's dd22 hooks are used as they landed.
- D6's `door:dd22` (A6) still runs only `d6.sheltem_hatch`: no `playtest_in.yml` until it moves into this map.

## Lines for A3 (map-local, written inline)

- Arrival status line: "Escape Pod 2. Cold air, red light, and somewhere above, machines still on guard."
- The open blast door: "The blast door stands open."
- The couch: "Sheltem's command couch, empty. The harness hangs open."
- The cells: "An empty stasis cell. Its field is dark."
- The generator: "The stasis generator that carried Sheltem through the crash. It is cold."
- Source lines: aaze0088:0 (devices), :2, :3 (the weapons' message), :5, :6 (consoles); "Nothing here." (the rack after).

## Sounds for AU

Beds `humming` on each deck (`pan: false`, volume 0.2); the alarm `buzzer01` (a shipped buzzer with a wait of 1-2 s,
stopped by the release); the log's chirp `tone2` per page; the lifts `xeen_lift`. All shipped; AU may swap the alarm
and the chirp for better takes.

## DECIDE

1. **Two lifts make the spine** (A deck 1 to 2, B deck 2 to 3, side by side): a studio lift has two stops. The middle
   ring and the bridge landing are the lifts' landings, so there is one shaft room (12 rooms, 12 sectors). While a
   lift stands down, its well is an open hole in the deck above (a 448 drop), as DD-17's lift core; no gates.
2. **The dome's oculus is open to the Darkside's sky** (a sky face, `xeen_darkside_fading` as DD-03), the "viewport";
   the dome's sides are dark panels with two dark steel rings (raking ribs drew squashed undersides). Cheap to reverse:
   drop `sky` and `atmosphere.yml`.
3. **The blast door is one `swdoora` over two leaves parting in the middle** (DD-17's Command Central, which the doors
   audit passes) rather than a `swdoora`/`swdoorb` pair.
4. **Floor 8.34 M units²** against the graph's "about 10" (inside S's band).
5. **The lockers are riveted metal boxes** (`swgirder` chests), not the wooden default.

## Pictures (looked at, scratch root, no bake)

`output/studio_cal/dd22/shots/things3_1..3.jpg` (every interactive thing and the set piece), `rooms1_1..3.jpg` (every
room from two corners), earlier `things1`, `things2` (before the fixes). Changed after looking: the dome's raking ribs
became rings, light `swgirder` rings became dark panels, the dome's sides dark and its top a sky oculus; the consoles'
blue strip ends became riveted plate; the couch's blue top plate; the lockers metal. Tours placed at z 160 on deck 1
put the eye over the 320 ceiling (black above the walls in the drive): tours now stand at the floor.

## D-67 follow-up (session 14, after the lead's 06:27 install)

Decider D-67 (`mockups/act6_a8_followups_d67.md`) accepted all five DECIDE items and asked for four changes, made in
the generators (backups `tools/*_before_d67.py`), 0 new textures:

1. **Oculus sky** `xeen_darkside_day` (the pod opens after M33, when the sun is whole again).
2. **Red accents:** `swll5dk` is the main wall of every room but the airlock (theme `theme:airlock` keeps `swll4dk`);
   deck 2's and the landing's ceilings `swceilf`; every reveal (door jambs, the lift wells', the ladder hatch's lining)
   `swll5dk`. `swared` panels once each, whole (`fit`), on the rings' long south walls (two each).
3. **Yes/No buttons** (`AskChoiceWithAnswerSteps`, as DD-08/DD-15): the security console asks its own text with no
   message before it (B1; the playtest asserts the text and presses Yes); Phaser/Photon show the source's message
   ending on "Fire anyway?" (`evt.SetMessage`) over the buttons "Fire anyway?" (B1 drops it). The console's Yes opens
   both blast-door leaves by their numbers in ids.lock.yml (4, 5) and stops the alarm.
4. **Couch arms:** two 32-wide blocks on the dais beside the seat, 56 above it; the back widened to 264 across them;
   still facing the nose, the locker behind the back.

Checks (root, tables recopied 06:35, `xeen_quests.lua` re-linked): validate clean, build 0 warnings, audit 0 errors 0
warnings (infos: `bemv`, two `click.silent` the audit cannot read through the button script, `AmbientSound1`), solve
12 of 12; **12/12 playtests** (`run/four_063908`, `four_d67.txt`; playtest now 184 checks). Unbaked pictures
`shots/rooms_d67_1..3.jpg`, `shots/things_d67_1..3.jpg` (26-27: the couch with arms). The lead rebakes and reshoots
`baked1`.

`playtest_in.yml` (new): D6 with m33.done (111662), D6's hatch event 44, then `entrance:d6_hatch` (0, -832, 0) facing
512. **It fails today** (run `four_063855`): D6's door still only shows `d6.sheltem_hatch`'s opening line and does not
move; it is not in `four.sh`'s default list. Run `TESTS=playtest_in output/studio_cal/dd22/four.sh` after A6's D6.

## Session 21 (A8): AU's sounds

`sound:alarm` is AU's `xeen_pod_alarm`, a loop with no wait (was `buzzer01` with a wait), still stopped by the release; the log plays `xeen_log_chirp` (was `tone2`). Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 26 (A8): merge point 40 rebuild

- No source change (the generator reproduces the L4); oymap 40 builds the .blv slightly differently. Installed 00:53,
  baked, tests 16 of 16 from assets_dev (`output/studio_cal/a8_s26/run/dd22/c005256`); audit 0 / 0; check_exits 0.

### Drop pockets

- The stasis generator's top (`platform:generator`, `swgirder`, z 224, 144 x 256): the check reaches it only through
  the deck above (z 448) whose edge lines up with it from above. Not a trap: from the top the party steps down onto the
  room's floor (0), which it walks back from; nothing up there to fetch.

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:27): the generator reproduced the L4 unchanged and the build equals
the installed map (its three chests are already the 7gt002 kind; the fitted tops stand on the floor), nothing to
install; audit 0/0, check_exits 0, check_drops 0. Chest pictures: output/studio_cal/a8_s29/shots/dd22_chests.jpg and
dd22_couch.jpg (all on the floor or the couch's dais).

# DD-07 Eastern Tower: L4 notes

Lane A7 phase 4, ninth session (agent `agent:xeen-a7-dd07`), 2026-11-20. Map 9156, `xeen_dd07.blv`, class M,
`world: xeen`, on D3 (Sandcaster and the Aging Forest, the knoll by the east rim), Act IV, party 36-40. Built from the
MU-6 graph `devdocs/xeen/mockups/act4_graphs/dd07.graph.yml` with decider D-39 (`mockups/act4_a7_decisions.md`, DD-07
rows 1-7 and the approval changes), which wins where they differ, and A3's `source/quests/q-d18.yml` and `q-d20.yml`.

Generator: `output/studio_cal/dd07/tools/gen.py` writes L1-L4. Never hand-edit the written files. The playtests are
written by `tools/gen_tests.py` from the built `ids.lock.yml`. The cycle (generate, fmt, validate, build, install into
the scratch root, audit) is `output/studio_cal/dd07/cycle.sh`; the pictures are `shots.sh` with `shots.yml`. The scratch
root is `output/studio_cal/dd07/root` (hard links; real copies of `worlds/xeen/maps`, `events/maps` and every data
table). Its `map_stats.txt` and `bolster_maps.txt` carry a test row 9156 (copied from 9141, renamed, slots and music
set, continent 7) until A2 writes the real one.

## What was built

- **The levitation well.** An octagon (apothem 448) open from the ground floor to a slate cone: 2,944 at its walls, a
  point at 3,584. Its walls are the tower's ashlar with a marble band (`gstntileh`) at each floor's slab. The galleries
  open on it through arches on the ground floor and railed windows (sill 80) above. A pale light falls from the cone.
- **The floating disc.** A lift in the well against its east wall: black stone 352 square, 16 thick. It rests at the
  top floor at load, level with the gallery's opening in its east rail (the disc's landing). Its lever on the rail
  post beside the opening sends it down the well with whoever stands on it (1,920 at 240 a second, about 8 s), or
  calls it back up. The foot's lever, beside the east arch, answers only once the disc has been sent from the top:
  "The disc does not answer from below." AU's `xeen_lift` plays on each ride.
- **Four floors, 640 apart**, each 512 high (the top floor 640):
  - **L1 (0):** the door hall (the arrival, quiet; the D3 door in its west wall; the first stair's foot beside the
    door; the well through an arch), the east gallery round the well, the mages' commons (the long table, lore books),
    the store room (a storeroom: barrels, sacks and the chest).
  - **L2 (640):** the second landing, the second gallery, the cabinet of curiosities (cabinets of labelled oddities,
    the Golden Griffin in the last), the dormitory (four beds, the mages' chest), the mirror room (the dead mirror).
  - **L3 (1,280):** the third landing, the third gallery with the vault's door of light in its east wall, the conjury
    (the west ward pylon), the scrying room (the east ward pylon, three crystal balls, a black scrying pool with stars
    in it), the vault behind the door (the Jewel of Ages' stand of black glass), the disk alcoves (the experiment).
  - **L4 (1,920):** the top landing, the gallery under the cone (the disc's landing), the laboratory and the study in
    MM7's School of Sorcery (D-39 Q6). The laboratory holds benches, the Bubbling Vat, the Fountain of Minimal
    Abilities, the Fountain of Life and floor braziers. The study holds the desk with Ellinger's letter, two lecterns,
    shelves and the master's chest.
- **The stair.** Three two-storey stair halls west of the landings, alternating south, north, south, the third over
  the first. Each has a flight of 20 steps of 32 along its length to a gallery at the next floor. The climb winds round
  the tower's west side; it is built as a dog-leg (the studio has no winding stair; DD-06's halls are the model).
- **The door of light** (D-39 Q4). The vault's door is XD-04's ward (`xwward`, translucent, a folding leaf that sinks
  into the floor). Clicked while it stands: "A wall of light hums in the doorway. Two beams feed it, from the west and
  from the east." The two ward pylons are crystals (`crystl0`, destructibles of glass, 40 hp) on black pillars, a cool
  blue beam light at each. A click on the pillar strikes the crystal and breaks it; a blow or missile breaks it too.
  A timer then counts it (map variable `pylons`), puts out its beam and says "The west pylon shatters. Its beam goes
  out.". When both are broken the door fades ("In the vault's doorway the wall of light flickers and fades.") and
  stays open, on every later load too.
- **Counts.** 23 rooms (23 sectors), 30.5 M units² of floor. 10 doors, the disc lift and its two levers. 3 chests at
  treasure 4 (store, dormitory, study). 5 loops: round L1's well; L2's gallery, cabinet, dormitory and mirror room;
  L3's pylon rooms; L4's gallery, laboratory, study and landing; and the stair up with the disc down.
- **Monsters.** 30 (D-9.3, D-39 Q2), all placed and hostile in groups 10-22 by room:
  - 15 Floating Adepts 11203 (28);
  - 9 Floating Magi 11204 (38);
  - 4 Mystic Mages 11200 (45): one in the vault, one in the laboratory, two in the study;
  - 2 Floating Eyes 11570 (40): the third gallery, the study.

  Kill XP is 11.57k per member, as the graph has it. Rest encounters are 10 % from the map's own hostile rows (D-39):
  slot 1 Xeen Floating Mage tier 0 (the Mystic Mage; the Adept and Magus tiers are placed only), slot 2 Xeen Eye
  tier 0 (the Floating Eye). Music 43.
- **Textures:** the Towers of Mok family (MM8 d27: `gston1wl`, `gstntilev`, `gstntileh`, `gston1fl`, `gstn1cl`,
  `gcstflor`, `gcstdoor`, `gstyl`) and MM7 7d14 in the laboratory and the study (`twb2`, `7tfb1`, `tfb2`,
  `trim5_32`, `7t1books`, `7t1books1`, `7t1cabs`, `deskside`, `desktop`). Specials: XD-04's `xwward`, D-37's
  `xkmirror`, `wtrtyl` (the fountains, `liquid: water`), `sgstars` (the scrying pool), `7trimd` and `t2bedsht` (beds,
  table). 36 distinct of the 45 cap, the chests' pictures included; 0 new.
- **Sound:** one placed `xeen_amb_tower` bed in the well (volume 0.35, radius 5,120), heard on every floor. The graph
  asks for two; one source keeps them from stacking (DD-02's precedent). AU's `xeen_spring_drink` plays at the Fountain
  of Minimal Abilities, `xeen_lift` on each ride of the disc.

## Quest hooks (A3's, wired)

- `q-d18.jewel`: the vault's stand (title 'Jewel', dark/aaze0067:0).
- `q-d18.l3_disks`: the alcoves' experiment (title 'Disc', dark/aaze0067:1). The hook's `map_gives` means the map
  hands over the 2 Energy Disks 12334; it does that once, until `tower_disks` 113362 is set. Then it calls the hook (the
  bit and the line), and afterwards the hook's "Loose wires where the disks were.".
- `q-d18.letter`: the study's desk.
- `q-d18.fantastic_book`, `q-d18.great_power_book`: the study's two lecterns (the hooks decide).
- `q-d18.minimal_fountain`: the laboratory's fountain (the hook decides).
- `q-d20.griffin`: the cabinet of curiosities' last cabinet.

The map's own: the Fountain of Life heals the drinking member (`AddValue(CurrentHealth, 1000)`, clamped by the game).
The Bubbling Vat is dressing with its name and a line.

## Original lines (dark/aaze)

- "Exit the Great Eastern Tower?" (aaze0065:0): the meaning of the west door's exit preset (D-24).
- "The mirror does not respond." (aaze0066:1): the dead mirror (D-39 Q5, flavour only).
- "Jewel" / "Disc" / "Nothing here." (aaze0067:0-2): the vault's stand, the alcoves' experiment, the dormitory's beds.
- "Bubbling Vat", "Fountain of Minimal Abilities", "Fountain of Life" (aaze0068:0, :1, :4): the laboratory. The hooks
  say "Your statistics have increased!", "The water is cool and refreshing." and "Your intellect is already
  fantastic!" (aaze0068:2-3, :6).

## Measurements

- **Named arrival** `entrance:d3_door`: (-2496, 0, 0) facing east (0°), in the door hall 256 inside the west door, at
  the first stair's foot. It is the map's start too.
- **Way out:** `exit:d3_door` (the west door, the exit preset) to D3 by its named arrival `entrance:dd07_door`
  ((15360, 9216, 1888) facing west, D3's `xeen_d3.studio.yml`). Measured landing (`playtest_exit.yml`, after 2 s):
  **(15360, 9216, 1889)**.
- **The disc:** at load the party steps on at (256, 0, 1920) from the top gallery. After the lever and 12 s it stands at
  the foot, z 0 to 40 (`playtest.yml`).
- **Across the well:** with the party at the third landing's window (-640, 0, 1280), a Floating Adept spawned in the
  third gallery's east arm (736, 0, 1280), 1,376 away over the well, orbits there and attacks the party with Fire Bolt
  and its missile again and again (the trial's AI trace: attack_spell / attack_ranged against the party every
  2-3 s).

## Checks (2026-11-20, from `output/studio_cal/dd07/root`)

- `oymap validate` reports no issues on L1-L4, and `fmt --check` is clean. The build has 0 warnings
  (`output/studio_cal/dd07/build.log`).
- `oymap audit --reach --solve` (`output/studio_cal/dd07/audit.txt`; Xeen maps get `--dressing` by default) reports 0
  errors and 0 warnings: 0 `lights.*`, 0 `doors.*`, 0 `textures.*` and 0 dressing findings. On foot from the start,
  15 of 23 sectors are reached with the doors as they start and 23 with every door out of the way.
- Playtests, 4 of 4 each (`output/studio_cal/dd07/four_walk.out` for `playtest.yml`,
  `four_hostility_exit.out` for the other two; logs in `output/studio_cal/dd07/a7_xrun/`):
  - `playtest.yml`: the critical path. The stair to L3; the door of light shut, then both pylons broken by a click each
    and the door gone; the jewel and the disks (each twice); the third stair; the study (the letter, both books, the
    chest) and the laboratory (both fountains, the vat); onto the disc and down the well, the foot's lever calling it
    back; a save and load (the door of light stays gone). Then D-39's check: a Floating Adept across the well targets
    the party and attacks it (`ai_trace`, `combat_log`).
  - `playtest_hostility.yml`: all four rows hostile at load and after a reload; an adept, a magus and an eye side by
    side do not fight each other and go for the party.
  - `playtest_exit.yml`: out to D3, the landing measured.
- Pictures: `output/studio_cal/dd07/sheet1.jpg` to `sheet3.jpg` (18 shots of `shots.yml`; the full-size PNGs were
  deleted for disk space). The map is unbaked, so the rooms are evenly bright; the lane lead bakes it. Looked at: the
  well, the stair, the door of light, the pylons, the scrying pool, the study and the laboratory read as meant. Fixed
  after the pictures: the stone doors showed the door picture one and a half times across their 192-wide leaves
  (folded, tiled); they are now plain sliding leaves with the picture stretched once.

- **From `assets_dev` with A2's row 9156 (2026-11-20, tenth session, binaries of merge point 18):** `playtest.yml`
  (151), `playtest_hostility.yml` (28), `playtest_exit.yml` (14) 4 of 4 each, `--world xeen`
  (`output/studio_cal/a7/s10_rows_dd07.out`); the scratch root `output/studio_cal/dd07/root` is deleted.

## Texture fit exceptions

None.

## Dressing exceptions

None. Containers stand by walls in pairs; the store room is a storeroom (`store: true`) with its clumps; the vat,
the braziers and the fountains stand against the laboratory's north wall or off the line between its doors.

## Words needed

- **A winding stair.** The graph's spiral stair round the wall is built as three two-storey halls with straight
  flights, as DD-06's.
- **A destructible's `on_destroyed` event is reported `event.unbound`** by the audit (a `trigger: call` handler bound
  to no face). Workaround: a one-shot timer with `condition: {destroyed: ...}` counts each broken pylon.
- **No light beam geometry** from a pylon to the door: each beam is a light at its pylon, put out with it.

## Decided

- **D-45 (3), 2026-11-20:** the three two-storey stair halls with straight flights stay (a winding stair is a
  low-priority studio word, A1); the disc landing stays an opening in the top gallery's east rail (the graph marks
  `room:disc_top` built into `room:ring4`), and the commons opens only on the gallery (the graph's
  `link:commons_hall` is not built; the first-floor loop is door hall, well and gallery).

## What the user should look at

- The well: from the door hall's arch looking up to the cone, and from each landing's window across to the galleries.
- The ride on the floating disc from the top gallery to the foot.
- The door of light (`xwward`) on the third gallery, and the two crystal pylons.
- The scrying pool (`sgstars`) and the laboratory's two fountains (`wtrtyl` water tops).
- The map is unbaked; the lane lead bakes it.

## Tower bed centred (2026-11-21, fifteenth session, lane A7 sub-agent)

- D-48 (AUDIO.md "Indoor beds"): `sound:tower_bed` takes `pan: false` (`tools/gen.py`): the one bed up the well is
  heard centred on every floor (the scene's ambient sound 1, `pan: false`).
- `xcycle.sh`: build warnings 0, audit 0 errors, 0 warnings. Installed with bake (02:00:21), stale bakes 0. From
  `assets_dev`, 4 of 4 each: `playtest` 151, `playtest_hostility` 28, `playtest_exit` 14
  (`output/studio_cal/a7/s15_dd07_four.out`).

## D-58 roof stair (2026-11-21, seventeenth session, lane A7 sub-agent)

Decider D-58 (`briefs/d7/L1/D58_DECISION.md`, D-4 and Q2): a roof stair from the top floor up through a trapdoor, one
way up to D7's named arrival `entrance:dd07_roof`, open after `m30.done`. Generator `tools/gen.py`, playtests
`tools/gen_tests.py` (before: `output/studio_cal/dd07/s17/gen_before_s17.py`, `gen_tests_before_s17.py`, L4 before
`s17/L4_before/`; both unchanged generators reproduced that L4 and its playtests exactly first). `cycle.sh` now writes
L4 only (`gen.py L4`): L1-L3 stay as approved, without the roof stair.

- **Where:** `room:roof_stair` "Roof stair", (-256, -1472)-(1536, -1088), floor 1,920 (the top floor), south of the
  gallery under the cone. `open:ring4_roof` (256 wide, at x 0) through the gallery's south outer wall. One flight of 16
  steps of 32 rising east from (256, -1280) to the head `platform:roof_head` (1088..1536, -1472..-1088) at **2,432**;
  the hall's ceiling 2,720. Over the head the hatch: four black beams (`hwm2rf`, 32 wide, 40 deep) framing (1216,
  -1376)-(1408, -1184), and inside them the closed leaf `platform:roof_hatch` (plank `7trimd`, 16 thick, 2,704 to
  2,720), centred **(1312, -1280)**. Two `scon100` sconces (the foot's west wall, the head's north wall), a lamp over the
  foot (2,340) and one over the head (2,632). Stair theme (ashlar, cobbles). No monsters, no props.
- **Wiring (sealed; opened in the eighteenth session):** `evt:roof_trapdoor` (event 44, "Roof trapdoor", a script on the leaf): condition
  `all: [{lua: XeenQuests.hook("d7.roof_dd07")}, {map_var: d7_open}]`, effect `{exit: exit:d7_roof}` (the game's leave
  window). The hook runs first: before `m30.done` (111600) its "The trapdoor is shut fast." and nothing else; with it
  the else line "Wind whistles round the trapdoor's edges, but it will not lift. (Not open yet.)" (only while
  `XeenQuests.can`). Map variable `d7_open` (2) is never set. project.yml neighbour `exit:d7_roof` to `xeen_d7.odm`,
  kind `roof`, `one_way`, `arrival: entrance:dd07_roof`.
- **Opening it when D7 installs (the lead; done in the eighteenth session, see the last section):** drop `{map_var: d7_open}` from the condition in `gen.py` (and the
  variable), rebuild against a root with D7 installed (the build then knows the arrival).
- **Checks** (root `output/studio_cal/dd07/root`: a new hard-link root of `assets_dev` with real copies of the map's
  own files and the tables, its stale bake removed; binaries of merge point 25):
  - validate clean; build 1 warning (`exit:d7_roof.arrival`: D7 not installed).
  - `audit --reach --solve` (`output/studio_cal/dd07/audit.txt`): **0 errors**, 1 warning, `state.never_set` map_var 2
    (the seal, by design until D7); one info `click.silent` (an impossible path). 24 rooms (25 sectors), all reached
    with the doors open; no `lights.*`, `doors.*`, `textures.*` or `dressing.*` finding.
  - Playtests 4 of 4 each from the root (`output/studio_cal/a7/s17_dd07_roof_four.out`, logs
    `output/studio_cal/dd07/a7_xrun/`): `playtest` 151, `playtest_hostility` 28, `playtest_exit` 14 (unchanged by the
    new ids), and the new `playtest_roof.yml` 26 (put in the gallery's south arm, walks up the flight to the head, clicks
    the trapdoor: "The trapdoor is shut fast." and no sealed line; `set_qbit 111600`; again: "(Not open yet.)"; still on
    DD-07, on the head).
  - Pictures: `output/studio_cal/dd07/s17/roof_sheet.jpg` (shots `s17/shots/`, tour `s17/tour_roof.yml`), looked at:
    the doorway in the gallery's south wall, the flight up to the hatch, the framed plank trapdoor from the head.
    Unbaked (flat light).
- **For D7 (A6):** the trapdoor is at (1312, -1280), south-east of the well (the well's octagon is centred on (0, 0)),
  its leaf at 2,704 to 2,720 over the head at 2,432; the tower's top is the well's slate cone, 2,944 at its walls and
  3,584 at the point. D7's `entrance:dd07_roof` (L4: (27136, -6144) facing west) should stand on the roof beside its
  hatch; where on the roof is D7's choice.
- Decorations renumbered by the lock (sorted by id: `deco:roof_sconce_head` is 38); no event, door or chest number
  changed. Not installed, not baked (the lead does both).

### D-58 roof stair installed (2026-11-21, lane A7 lead, seventeenth session)

- Installed with its bake 04:50:50 (`install_baked.sh` from `output/studio_cal/dd07/root`), stale bakes 0. Audit from
  `assets_dev` 0 errors, 1 warning (the sealed roof's map variable) (`output/studio_cal/dd07/audit_assets_dev_s17.txt`). **16/16 from `assets_dev`** (playtest
  151, hostility 28, exit 14, roof 26; `output/studio_cal/a7/s17_dd07_four.out`). Open when D7 installs: drop `{map_var: d7_open}` in gen.py.

## Eighteenth session (2026-11-21, lane A7 lead)

- The roof trapdoor is open (D7 installed): condition A3's `d7.roof_dd07` only, `{exit: exit:d7_roof}` to `xeen_d7.blv` `entrance:dd07_roof`, at once (indoor neighbour); `d7_open` gone. `playtest_roof`: shut before m30.done, then lands on D7 at (27136, -6144) z 950-1100. Build warning (kept): as DD-06's.
- Installed with its bake 05:21:20 (`output/studio_cal/a7/s18/install_queue.sh`), stale bakes 0; audit from `assets_dev` 0 errors, 0 warnings (`output/studio_cal/a7/s18/audit/dd07.txt`); **16/16 from `assets_dev`** (playtest 151, hostility 28, exit 14, roof 28; `output/studio_cal/a7/s18_four.out`, merge point 25/26 binaries).

## Twentieth session (2026-11-21, lane A7 lead)

- D-66: the roof trapdoor checks A3's `d7.roof_dd07` first, then asks the map's own Yes/No "Climb up through the trapdoor?" (DD-08's pattern); Yes runs the hook and moves at once to D7's `entrance:dd07_roof` (27136, -6144, 1024) facing 1024, No stays. `playtest_roof` (gen_tests.py) answers No then Yes. The build warning about the hook condition is gone.
- Built into `output/studio_cal/a7/s20/dd07/` with the oymap of merge point 27: BLV and scene byte for byte the installed ones (no rebake; stale bakes 0); the Lua differs by the trapdoor only. Lua and studio file installed 06:51:18. Audit from `assets_dev` 0 errors, 0 warnings (`output/studio_cal/a7/s20/audit/dd07.txt`). **16/16 from `assets_dev`** (playtest 151, exit 14, hostility 28, roof 39; `output/studio_cal/a7/s20/four_dd07.out`).

## jewel_found dropped (2026-11-22, lane A7 twenty-seventh session)

`project.yml` no longer names `jewel_found` (113361), nor does the plan's goal give it (A3 35th: nothing sets or
reads it since the Jewel of Ages became a ground item, D-90). Only the studio file changed (installed); tests 16/16.

# D-195 to D-199: the pin round's leftovers (decider, 2026-11-26)

Context: [DECIDER_BRIEF_20261126b.md](DECIDER_BRIEF_20261126b.md),
[PLAYER_FEEDBACK_20261126.md](PLAYER_FEEDBACK_20261126.md) (Round summary, "Open after the round", the dungeon2,
outdoor2 and outdoor3 Results), [D185_D188_DECISION.md](D185_D188_DECISION.md) (D-186, D-189, D-190),
[D180_D184_DECISION.md](D180_D184_DECISION.md) (D-180), [DECISIONS.md](../DECISIONS.md), [AGENT_GUIDE.md](../AGENT_GUIDE.md)
§4 and §6. The decider edited nothing but this file. Checks ran read-only on the installed maps (`assets_dev`),
through `tools/heavy.sh 4` or as small scripts on `oymap export` copies in the session scratchpad; the pictures were
read at full size.

## D-195: XD-05's three campfires, its two faults, and `campfires.py --check`

### Premises checked

- **Neither fault is in XD-05's map. Both are in a check or a test.**
- **The `check_drops` pocket is a false finding.** The "pocket" at (-2398, 5374), z -480, is the prisoner pit. It has
  a rope ladder (`scene.yml ladders: pit`, bottom (-2400, 5672, -480), `top_exit` (-2400, 5856, -224)), and
  `playtest.yml` climbs out by it and passes (`climb: {ladder: pit}`, then the party at z -232..-216).
  `check_drops.py` joins a ladder's foot and top with `face_at(x, y, z, tol=8)`. That function takes a floor's height
  as the **mean of its vertices**. The floor under the top exit is a sloping rock triangle, face 2687, with vertices
  at z -176, -224, -224: its mean is -208, but its plane at (-2400, 5856) is exactly -224. Because -208 > -224 + 8, the
  ladder's top finds no floor, the ladder is never joined, and the pit reads as a trap.
  - With `face_at` reading the plane's height at the point (scratch copy of the tool), XD-05 shows **0 pockets**.
  - I ran both versions on all **69** installed Xeen BLVs. **Only XD-05's result changes** (1 to 0). Nothing else
    moves, so no real pocket is hidden.
- **The playtest fault is a stale z window.** `playtest.yml:161` and `playtest_mouth.yml:68` assert X1's arrival
  `z_min: 1300, z_max: 1450`, written when X1's land in front of the orc cave was 1376. The X1 rebuild in commit
  81bd30afa2 (3.4, 2026-11-25) lowered it to about 1280. X1's own generated test followed (`gen_walk.py round_trip`
  asserts ground ± 80: HEAD `z_min 1200, z_max 1360`; before that commit `1296..1456`). The party now lands at
  (9216, 16384, **1281**), on the ground, facing 1536, which is correct. XD-05's hand-written tests were not updated.
  That is why the installed map fails too.
- `campfires.py --check` today: 1 error, `xd05 campfire.not_installed` (0 of 3), 21 fires listed on 11 maps.
  `regressions.sh`'s gate loop runs only `tools/xeen/<script>`, and `campfires.py` lives in
  `level_generation/projects/xeen/common/`.
- The L4 already carries the three events (`git diff`: `wiring.yml` +21, `ids.lock.yml` +6). The stage's audit had 0
  errors, `check_monster_fit` 0, and `playtest_back` and `playtest_hostility` passed
  (`output/xeen_fb/p5_dungeon2/cf_xd05.log`).

### DECISION

**Fix the two faults first (both are small and lie outside the map), then install the campfires.** Do not drop the
campfires, and do not install with a recorded fault.

1. **`tools/xeen/check_drops.py`, `face_at`:** a floor's height at (x, y) is its plane's height there, from three of
   its vertices (fall back to the mean only for a degenerate face). Leave the tolerance as it is. Add one docstring
   line: "a sloping floor is measured at the point (XD-05's pit ladder, D-195)". Rerun on every Xeen BLV: only XD-05
   may change.
2. **XD-05's tests (the L4 is their source):**
   - In `playtest.yml` line 161 and `playtest_mouth.yml` line 68, set the X1 arrival window to `z_min: 1200,
     z_max: 1360`, the same window as X1's own generated round trip (X1's ground 1280 ± 80). Add a comment that this
     follows X1's ground at `entrance:xd05_mouth`.
   - In `project.yml`, change `arrival_hint`'s "(9216, 16384, 1376)" to "(9216, 16384, 1280)".
3. **Then XD-05's normal map cycle.** Use the dungeon2 stage (`output/xeen_fb/p5_dungeon2/runmap.sh`) under
   `flock output/xeen_locks/xeen_xd05.lock`:
   - build, audit 0, `check_drops` 0, `check_monster_fit` 0, 4 of 4 playtests;
   - install, bake under `bake.lock`, `xeen_pack_reserve.py xeen_xd05`, `xeen_balance.py --check`;
   - `key_npcs.py --write`, `check_actor_heights.py`, `stale_bakes.py --check` 0;
   - `campfires.py --check` 0. Add one line to XD-05's NOTES.md and A7's Log.
4. **`campfires.py --check` joins `tools/xeen/regressions.sh`** once step 3 makes it 0. Add its own block after the
   gate loop: `python3 "$root/level_generation/projects/xeen/common/campfires.py" --check` with PASS/FAIL lines like
   the gates. The comment cites D-104 and D-195.

### WHY

- Installing with "faults recorded" would record two faults that do not exist, and would leave XD-05's playtests red,
  so every later round would trip on them.
- Dropping the campfires would leave XD-05 the only map of the 11 surveyed fire maps where a player's open fire does
  nothing (D-104, F74).
- The tool fix is the root fix, not an exception for one site. A floor's height must be read where the ladder stands,
  and any sloped rock floor at a ladder end on a future map would hit the same false pocket. The all-BLV comparison
  shows it hides nothing.
- The test window follows the precedent X1 already set (its generator asserts ground ± 80). A hard-coded 1376-era
  window is exactly the stale state AGENTS.md says to fix at its source.

### WHO ACTS

- **A7:** `check_drops.py` (a few lines plus the all-map rerun), XD-05's two tests and `project.yml`, and XD-05's
  stage, install and bake. About an hour plus the bake.
- **Orchestrator:** the `regressions.sh` block (5 lines) after A7 reports `campfires.py --check` 0.

### REVERSIBLE

Yes: a measurement in a tool, two test bounds and one map install. Confidence **90 %**.

**SUMMARY ROW**

`| D-195 | 2026-11-26 | XD-05's three campfires: install with faults, fix first, or drop (decider) | Fix first; neither fault is in the map. check_drops' pocket is false: face_at takes a floor's mean z, and the pit ladder's top_exit (-2400, 5856, -224) sits on a sloping triangle (mean -208, plane -224), so the ladder is never joined; read the plane's z at the point (on all 69 Xeen BLVs only XD-05 changes, 1 → 0). The playtests' X1 window (1300–1450) predates X1's 3.4 ground at the cave (1280): set 1200–1360 as X1's own round trip, and arrival_hint z 1280. Then XD-05's stage, install, bake. campfires.py --check joins regressions.sh as its own block once 0. 90 % | A7; orchestrator (regressions.sh) |`

---

## D-196: Darkside's 192-wide tower doors tile MM7 door pictures

### Premises checked

- **The four sites.** All four towers wear the tower kit's dark blocks.

  | Tower | Picture | Leaf |
  | --- | --- | --- |
  | D1 Ellinger's Tower | `hkm1d` | 192 × 320 |
  | D1 Western Tower | `hkm3dr` | 160 × 320 |
  | D2 Southern Tower | `hkm1d` | 192 × 384 |
  | D3 Eastern Tower | `hkm1d` | 192 × 320 |

  The classic kit keeps the MM7 pictures only because outdoor3 added them to `common/classic_kit.yml keep_doors`.
- **What the pictures are.** Sheet of `hkm1d`, `hkm3dr` and `hkm1dl` made from the x2 PNGs:
  - `hkm1d` is one whole door, framed: its stone jambs on both sides and its own fanlight on top.
  - `hkm3dr` is one whole framed door (skulls, a blue gem, its own columns).
  - Both are 128 × 256. On a 192 leaf they show **1.5 doors**, a full one and a narrow half (`after/d2/crop_door.png`,
    `after/d1b/01-ellinger.png`, `after/d3/01-e_tower.png`). On a 160 leaf they show 1.25.
- **Why the audit passes them.** Both are classed `door: tile` (tiles across). The class comes from
  `tools/xeen/texture_classes.py`'s seam measure. `TextureAudit.cpp` exempts `door: tile` from `doors.tiled`, so the
  1.5 repeat passes. But the shipped maps use both pictures once (`used: [1.0, 1.0]`), and the class only feeds the
  audit, not the build (`grep` of `openyamm-studio/core`).
- **The kit's own door.** The tower kit's door is `xvtdoor` (128 × 256, `door: single`: a plank door with an iron
  ring in a stone surround). The studio lays a part's picture once per bay with `textures.<role>: {texture, fit:
  true, size}` (README "Building parts lay a picture once per bay"). D2's Graalg gates already use it.
  - At 192 × 320 the picture is stretched 1.5 × 1.25, which is 1.2× wider than its own shape. I looked at a 1.2×
    stretch of `xvtdoor` and it reads as the same door.
  - At 192 × 384 and 160 × 320 it keeps its own 1:2.
- **Fronts.** Ellinger's facet is 2 × 440 × sin 15° ≈ 228 wide, so a 256 door (two 128 leaves) does not fit it.

### DECISION

**Each of these doors shows the kit's own single door picture once over its leaf, stretched to fit. The classic kit
does this for any single-leaf door bay wider than its picture.**

1. **`common/classic_kit.yml`:** `keep_doors: [xkportc]` (remove `hkm1d` and `hkm3dr`), and update the comment.
2. **`common/classic_kit.py`:** where the kit writes a part's `door` role, check the part's door bay in its `walls`
   list.
   - If the bay is wider than 128 and the door is a single leaf (not `leaves: 2`, which keeps F74's wings), write
     `{'texture': <kit door>, 'fit': True, 'size': [128, 256]}` instead of the bare name.
   - The rule covers every kit: house `xvdoor`, stone `xvsdoor`, tower `xvtdoor`.
   - The four towers then show `xvtdoor` once: Ellinger and Eastern 192 × 320, Southern 192 × 384, Western 160 × 320.
   - The leaf sizes stay as D-180 (a) and D-190 set them.
3. **Generators:** D1 `gen.py` (Ellinger 1291, Western 1571), D2 `gen.py` 1278–1285 and D3 `places.py` 683 keep a
   `door` entry. Their comments change from "MM7's iron-bound planks hkm1d, a door that tiles across" to "the kit's
   door laid once over the leaf (D-196)". Writing `xvtdoor` there is optional, because the kit replaces it.
4. **The audit gap:** in `tools/xeen/texture_classes_overrides.yml`, set `hkm1d: {class: feature, door: single}` and
   `hkm3dr: {class: feature, door: single}`, with a comment saying each is one framed door with its own fanlight and
   jambs. Regenerate `texture_classes.yml` with its tool. `doors.tiled` then fails a 1.5 repeat of either picture
   anywhere.
   - Look at `hkm2d` (X5's Ninja Pagoda, 160 wide; XD-22) the same way: if it is also one framed door, override it
     too.
   - Then run `oymap audit` on every Xeen map. Any new `doors.tiled` is fixed by the fit rule above, never by a kept
     line.
5. **Rebuild D1, D2 and D3** with their bakes. Checks: `door_check.py` 0, the audit's `doors.*` 0,
   `town_fit_check` 0, and the maps' playtests. Take one capture of each door front at the poses of
   `output/xeen_fb/p5_outdoor3/look/d{1,2,3}_after.yml`.

### WHY

- A door with half a second door beside it is the same fault the player pinned as X6 p16 ("the doors are clipping",
  two whole doors side by side). The audit missed it only because of a class that the pictures' own use (once per
  leaf on every shipped map) contradicts.
- U-15 puts the classic kits on Xeen's dark places, and the four towers already wear the tower kit's walls. An MM7
  Harmondale door on them is the stand-in U-15 removed. The kit's own door matches Darzog's Tower, Darkstone and the
  X3 tomb.
- DOORS.md: "a single-leaf door picture on a leaf up to about 192 wide", laid once. One stretch keeps the frame and
  the ring whole.

Options rejected:
- A wing pair (`xvtdoorw` or `hkm1dl`/`hkm1dr`) of 96-wide leaves: under 192 together is `doors.narrow_pair`, and each
  wing would be squashed to 0.6 of its shape.
- 256-wide doors (two whole 128 pictures): Ellinger's 228 facet cannot hold one.
- Keeping MM7's pictures stretched once: possible, but a stand-in on the kit's wall.
- New art: not needed.

### WHO ACTS

- **A6** (Darkside; D1, D2, D3 rebuilds with bakes): kit code and yml, the three generators' comments, captures.
  About half a day with the bakes.
- **A1/A6:** the two overrides and the class regeneration, then one audit pass over the Xeen maps (A6 reviews
  overrides, per the overrides file's header).

### REVERSIBLE

Yes: a kit rule, two class overrides and three rebuilds. Confidence **75 %** (192 × 320's 1.2 stretch is taste. If
it reads wide on the captures, Ellinger and Eastern may take `door_height: 384`, which D-180 (a)'s +64 allows, where
their storeys hold it).

**SUMMARY ROW**

`| D-196 | 2026-11-26 | Darkside's 192-wide tower doors tile MM7 door pictures (decider) | hkm1d/hkm3dr are whole framed doors (own jambs and fanlight, used once on shipped maps), so 192 shows 1.5 doors; the audit misses it only because they are classed door: tile. The kit's own door is laid once: keep_doors back to [xkportc]; classic_kit.py writes {texture: <kit door>, fit: true, size: [128, 256]} on any single-leaf door bay wider than 128 (all kits; leaves: 2 keep wings). Ellinger 192 × 320, Western 160 × 320, Southern 192 × 384, Eastern 192 × 320 show xvtdoor once. Overrides hkm1d, hkm3dr → door: single (hkm2d looked at); D1–D3 rebuilt with bakes, door captures. 75 % | A6; A1/A6 (class overrides) |`

---

## D-197: X7's `xd05_gate`, "a picture 416 deep"

### Premises checked

- **What the warning measures.** `door_check.py`'s `doors.deep_leaf` reads the sketch's `depth` and reports it as
  the leaf's distance behind the frame. The built model says otherwise. In `oymap export` of the installed
  `xeen_x7.odm`, `thing:xd05_gate` has:
  - the doorway block, `cwb1`, from x 12256 to 12672: **416 deep into the hill**;
  - the hood, 12192 to 12256 (64);
  - both `chb1dl` leaves at **x 12254**.

  So the door stands **62 behind the frame's face**, 2 in front of the block's face.
- **The same holds on every doorway measured.** The leaf stands at the hood less 2, whatever the depth:

  | Doorway | depth | hood | leaf behind the frame |
  | --- | --- | --- | --- |
  | X7 `fd04_gate` | 96 | 48 | 46 |
  | X1 warehouse | 128 | 96 | 94 |
  | X1 witch tower | 128 | 128 | 126 |
  | X7 `xd05_gate` | 416 | 64 | 62 |

  `depth` is how far the block reaches into the hill. D-170 set 416 so that its top ends 8 over the rising hillside
  (448 had laid its back on the land and it flickered).
- A capture of the gate front (`output/xeen_rimmap_b/x7/cap_extra/06-gate_front.png`, before D-170) shows the
  arched double door near the face of its rock frame, not at the end of a tunnel.

### DECISION

**D-189's rule applies to every built door, old or new. It means the leaf's setback from the frame's face (what the
player sees), not the block's `depth`. The X7 gate already meets it (62 ≤ 128), so nothing on the gate changes.**
- `depth` 416 stays (D-170).
- `door_check.py` `doors.deep_leaf` measures the leaf from the built model: the distance of the doorway's
  door-picture faces behind the frontmost face of the same facing in that model, or `hood` as a fallback. It no
  longer reads `depth`. With that, `xd05_gate` drops out of `--list`, and no kept line or NOTES exception is needed.
- Fix the docstring the same way: "leaf at most LEAF_DEPTH behind the frame's face (in the studio it stands at the
  hood's back)".
- D-189's earlier "shorten `depth` 384 → 128" edits (X1 warehouse and witch tower, X2 den door, X5 Golem slab) only
  shortened the blocks. Their leaves were already at the hood's back. They stay as built; nothing is redone.

### WHY

The player's complaint behind D-189 was a door that reads as missing, deep in a hole. That is about where the leaf
stands, and the measurement shows it stands at the hood on every doorway. Shortening this block to 128 would bring
back D-170's fault (its top below the hillside, the land through it) for no visible gain. A check that measures the
wrong number would keep asking for that change.

### WHO ACTS

**A5** (`door_check.py`, which A5 owns per D-189): about 20 lines and a rerun over X1–X7 and D1–D6, `--list` showing
no `doors.deep_leaf` for any doorway whose hood is 128 or less. No map rebuild.

### REVERSIBLE

Yes: a check's measurement. Confidence **85 %**.

**SUMMARY ROW**

`| D-197 | 2026-11-26 | X7's xd05_gate "picture 416 deep": does D-189's 128 apply to older doors? (decider) | Yes, to every built door, but D-189's 128 is the leaf's setback behind the frame's face, and the studio sets the leaf at the hood's back (hood − 2), not at depth. Measured on the installed X7: the leaves stand 62 behind the frame (hood 64); depth 416 is the block's reach into the hill (D-170: its top 8 over the hillside). The gate is unchanged. door_check.py doors.deep_leaf measures the leaf on the built model (hood as fallback), not the sketch's depth; xd05_gate drops out; D-189's earlier depth cuts stay, no redo. 85 % | A5 (door_check.py) |`

---

## D-198: D-186's pair placed differently from the decision

### Premises checked

- D-186's "free south-west quarter" was wrong in its premise. The nest (`fd04/gen.py`: x -1536..704, y -1536..960)
  has the egg bowl (x -800..-32, y -672..96, 96 down) in its middle, and its south-west quarter already holds groups
  21 and 23's (-1150, -1150), (-416, -1150) and (-1150, -288). Two more 476-wide bodies there would stand about 530
  from their neighbours, or over the bowl.
- **Where dungeon2 put group 25:**
  - **Positions:** Fire Dragon (-506, 256) leash 480, north of the bowl; Frost Dragon (100, -450) leash 512, east of
    the bowl.
  - **Spacing:** each 687+ from every other dragon (my pairwise list: 687, 687, 737). The closest pairs elsewhere in
    the nest are 734–784. The eggs are 541–551 away.
  - **Counts:** kept (8 in the nest, 2 in the hatchery; the plan table says so).
  - **Checks:** 9 of 9 playtests; `check_monster_fit.py --maps xeen_fd04 --squeeze` today: 0 stuck, 0 squeeze.
- **Captures.**
  - `fd04/rest_01_crop.jpg` (before the move): a Frost Dragon's wing through the Fire Dragon's head in the hatchery.
    D-186's trigger was met.
  - `after/01-hatchery_nest_door`: one pair, clear.
  - `after/04`, `06`, `07`: the nest's eight standing apart round the bowl, none in it, no body through another at
    rest.

### DECISION

**Accept the placement as built.** Group 25 stays at (-506, 256) and (100, -450) with leashes 480 and 512. D-186's
row is read with this correction: the fallback is "the nest, spaced 687+ from every other dragon, off the bowl", not
its south-west quarter. No rebuild.

### WHY

The fallback's purpose was bodies that do not run through each other and counts that are kept, and the captures and
the fit check show both. The quarter that D-186 named was not free (a premise error of that decider). Putting the
pair there would crowd five dragons into one quarter or onto the eggs. The agent's spots give the even spacing the
rest of the nest has.

### WHO ACTS

**Orchestrator:** record D-198 beside D-186 in DECISIONS.md. Nothing for A7.

### REVERSIBLE

Yes: two posts in one generator table. Confidence **85 %**.

**SUMMARY ROW**

`| D-198 | 2026-11-26 | D-186's pair placed N and E of FD-04's egg bowl, not in the nest's south-west quarter (decider) | Accept as built: the quarter D-186 called free already holds three of the nest's six (premise error). Group 25 at (-506, 256) leash 480 and (100, -450) leash 512 stands 687+ from every other dragon (the nest's own spacing 734–784), off the bowl, 541–551 from the eggs. Counts kept; 9/9 playtests; check_monster_fit 0 stuck, 0 squeeze; captures show no bodies through each other at rest. D-186's fallback reads "the nest, spaced, off the bowl". 85 % | orchestrator (record only) |`

---

## D-199: X7's Dragon Tower plinth, 215 over its slope

### Premises checked

- **What the check samples.** `town_fit_check.py check_plinths` samples the plot rectangle's corners, edge midpoints
  and middle. `thing:dragon_tower` has a 3 × 4-cell plot at (27.5, 27.6), but the building is one round part: radius
  512, centre (29.0, 30.59) in cells. The installed model's bounds are x -18415..-17425, y 16611..17600: cells
  28.0–30.0 by 29.6–31.6, with the walls' foot at z 2464.
- **Where the 215 comes from.** The lowest sample is the plot's north-west corner (27.5, 27.6), ground 2384. It lies
  about 1.3 cells outside the tower, on the crag's skirt. The crag's mesa top (`x7/land.py TOWER_CRAG` (29.0, 30.0),
  radius 2.7) holds the whole tower: its farthest wall is 1.6 cells from the crag's centre.
- **The ground under the walls**, on the installed `xeen_x7.odm` terrain (the game's triangles), 48 points per ring:
  - under the walls (r 495): **2592 everywhere**;
  - 64 out: 2592–2595;
  - 128 out: 2592–2599.

  The floor is 2600. Nothing hangs over a bank: this is a false finding of the check, not a building on a plinth.

### DECISION

**Accept the building as built. Change the check, not the tower.**
- `check_plinths` samples each part's own footprint: for a round part, its centre and points on its ring at the
  radius; for an outline or rectangle part, its corners, edge midpoints and middle. It uses the plot rectangle only
  for a building without parts.
- Delete the X7 `houses.plinth` line from `tools/xeen/town_fit_kept.yml`.
- Rerun `town_fit_check.py --list` on every map. D6's Alamar NE tower should still be reported (its walls run down
  the cliff) and keeps its kept line and reason. If it no longer trips, delete that line too.

### WHY

The rule (D1 p3, "the mill is in the air") is about walls standing over a falling bank. Measured where the walls
stand, the Dragon Tower is level to within 7. Moving it "a quarter cell south" would change FD-04's door, its arrival
and the D-85/D-142 distances for no visible gain. A kept line for a false finding hides the same mistake on the next
round building with a large plot.

### WHO ACTS

**A5** (owner of `town_fit_check.py`, outdoor tools): about 20 lines, a run over X1–X7 and D1–D6, and the kept line
deleted. No map rebuild.

### REVERSIBLE

Yes: a check's sampling and one kept line. Confidence **90 %**.

**SUMMARY ROW**

`| D-199 | 2026-11-26 | X7's Dragon Tower plinth 215 over its slope (decider) | Accept the building; the 215 is false. check_plinths samples the 3 × 4-cell plot rectangle, whose NW corner (2384) is 1.3 cells off the round keep (r 512) on the crag's skirt. Under the walls the installed land is 2592 all round (2592–2599 128 out), floor 2600, the whole tower on the crag's mesa top. check_plinths samples each part's own footprint (round: ring and centre); the X7 line leaves town_fit_kept.yml; D6's Alamar NE tower keeps its line if it still trips. 90 % | A5 (town_fit_check.py) |`

---

## Summary rows (for DECISIONS.md)

| D-195 | 2026-11-26 | XD-05's three campfires: install with faults, fix first, or drop (decider) | Fix first; neither fault is in the map. check_drops' pocket is false: face_at takes a floor's mean z, and the pit ladder's top_exit (-2400, 5856, -224) sits on a sloping triangle (mean -208, plane -224), so the ladder is never joined; read the plane's z at the point (on all 69 Xeen BLVs only XD-05 changes, 1 → 0). The playtests' X1 window (1300–1450) predates X1's 3.4 ground at the cave (1280): set 1200–1360 as X1's own round trip, and arrival_hint z 1280. Then XD-05's stage, install, bake. campfires.py --check joins regressions.sh as its own block once 0. 90 % | A7; orchestrator (regressions.sh) |
| D-196 | 2026-11-26 | Darkside's 192-wide tower doors tile MM7 door pictures (decider) | hkm1d/hkm3dr are whole framed doors (own jambs and fanlight, used once on shipped maps), so 192 shows 1.5 doors; the audit misses it only because they are classed door: tile. The kit's own door is laid once: keep_doors back to [xkportc]; classic_kit.py writes {texture: <kit door>, fit: true, size: [128, 256]} on any single-leaf door bay wider than 128 (all kits; leaves: 2 keep wings). Ellinger 192 × 320, Western 160 × 320, Southern 192 × 384, Eastern 192 × 320 show xvtdoor once. Overrides hkm1d, hkm3dr → door: single (hkm2d looked at); D1–D3 rebuilt with bakes, door captures. 75 % | A6; A1/A6 (class overrides) |
| D-197 | 2026-11-26 | X7's xd05_gate "picture 416 deep": does D-189's 128 apply to older doors? (decider) | Yes, to every built door, but D-189's 128 is the leaf's setback behind the frame's face, and the studio sets the leaf at the hood's back (hood − 2), not at depth. Measured on the installed X7: the leaves stand 62 behind the frame (hood 64); depth 416 is the block's reach into the hill (D-170: its top 8 over the hillside). The gate is unchanged. door_check.py doors.deep_leaf measures the leaf on the built model (hood as fallback), not the sketch's depth; xd05_gate drops out; D-189's earlier depth cuts stay, no redo. 85 % | A5 (door_check.py) |
| D-198 | 2026-11-26 | D-186's pair placed N and E of FD-04's egg bowl, not in the nest's south-west quarter (decider) | Accept as built: the quarter D-186 called free already holds three of the nest's six (premise error). Group 25 at (-506, 256) leash 480 and (100, -450) leash 512 stands 687+ from every other dragon (the nest's own spacing 734–784), off the bowl, 541–551 from the eggs. Counts kept; 9/9 playtests; check_monster_fit 0 stuck, 0 squeeze; captures show no bodies through each other at rest. D-186's fallback reads "the nest, spaced, off the bowl". 85 % | orchestrator (record only) |
| D-199 | 2026-11-26 | X7's Dragon Tower plinth 215 over its slope (decider) | Accept the building; the 215 is false. check_plinths samples the 3 × 4-cell plot rectangle, whose NW corner (2384) is 1.3 cells off the round keep (r 512) on the crag's skirt. Under the walls the installed land is 2592 all round (2592–2599 128 out), floor 2600, the whole tower on the crag's mesa top. check_plinths samples each part's own footprint (round: ring and centre); the X7 line leaves town_fit_kept.yml; D6's Alamar NE tower keeps its line if it still trips. 90 % | A5 (town_fit_check.py) |

Least certain: D-196's 1.2 stretch on the 192 × 320 doors (taste; the fallback is in its REVERSIBLE). The other four
rest on measurements.

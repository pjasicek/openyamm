# DD-06 Southern Tower, L4: notes

Lane A7, sub-agent `agent:xeen-a7-dd06`, 2026-11-20 (phase 3). The generator is `output/studio_cal/dd06/tools/gen.py`.
It writes L1–L4, and the written files are not edited by hand. The cycle (fmt, validate, build, install into the
scratch root, audit) is `output/studio_cal/dd06/cycle.sh`. The playtests are run by `play.sh` and `four.sh`, the
pictures by `shots.sh`.

Inputs: the MU-6 graph `devdocs/xeen/mockups/act3_graphs/dd06.graph.yml` and `notes_d2.md` (DD-06). Decider D-25
(`mockups/act3_a7_decisions.md`) wins where they differ.

## What was built

The source's four-storey tower is one BLV. It is a square tower 4,096 across inside, with four floors stacked 640
apart. Rooms are 544 high and the slabs 96. The counting room is 640 high under the cone's beams. Walls between rooms
are 128 thick. The geometry follows XD-11's stacked tower.

| Floor | z | Rooms |
| --- | --: | --- |
| The front | 0 | Entrance hall (start; a straw heap where the chute lets out), lookouts' room, first gong (the memo), tapestry hall (button, false wall), the stash behind it, kennel |
| The den | 640 | Den landing, mess hall, fence's room (lockbox), treasury (the Ali Baba chest on a dais), second gong, bunkroom |
| The practice floor | 1280 | Practice landing, practice hall (dummies, targets, practice locks), trap walk (two disarmed plates), strongroom (iron door), third gong |
| The inner circle | 1920 | Top landing, thieves' library (two lecterns), counting room (desk, high chair, the Master Thief and four guards), bedchamber (the hoard), getaway hatch |

- **The stairs.** Each stair up is a two-storey hall along the outer wall, behind a gong door. A flight of 20 steps of
  32 runs up to a gallery. The stairs alternate west (0–640), east (640–1280) and west (1280–1920). The first and third
  stair halls stand one above the other.
- **The getaway chute.** The trapdoor in the getaway room is an in-map teleport. It drops the party onto the entrance
  hall's straw heap at (1760, 1780, 32) with one line, and does no fall damage.

**Measured** (`oymap metrics`, `metrics.json`):

| Measure | Value | Band (M) |
| --- | --- | --- |
| Sectors | 25 | 20–45 |
| Floor area | 44.1 M units² | 30–90 |
| Doors | 13 (14 door records with the button) | 6–16 |
| Chests | 5 | 3–7 |
| Monsters | 46 placed (45 and the boss) | 45–75 |
| Distinct textures | 41 (20 named in the project, the rest the chests' kinds) | cap 45; 0 new |
| Loops | 4 | |

The four loops are the front, the den, the practice floor, and up by the gongs and down by the chute.

## Monsters (A2's rows, all placed)

| Room | Group | Monsters |
| --- | --: | --- |
| Lookouts' room | 10 | Rogue 11110 ×2, Thief 11111 ×2 |
| First gong | 11 | Rogue ×2 |
| Tapestry hall | 12 | Rogue ×2, Thief ×1 |
| Kennel | 13 | Dark Wolf 11410 ×2, Sabertooth 11411 ×2 |
| Mess hall | 14 | Thief ×5 |
| Bunkroom | 15 | Thief ×4 |
| Fence's room | 16 | Thief ×2, Master Thief 11112 ×1 |
| Second gong | 17 | Thief ×3 |
| Practice hall | 18 | Thief ×3, Master Thief ×2 |
| Trap walk | 19 | Thief ×3 |
| Third gong | 20 | Thief ×2, Master Thief ×1 |
| Library | 21 | Thief ×1, Master Thief ×1 |
| Counting room | 30 | Inner Circle Guard 11115 ×4, immobile |
| Counting room | 31 | The Master Thief 11114 (level 32), immobile |

- **Totals:** Rogue 6, Thief 26, Master Thief 5, the four guards replacing four of the graph's nine Master Thieves
  (D-25), Dark Wolf 2, Sabertooth 2.
- **Hostility:**
  - Groups 10–21 are `hostile: true`.
  - The guards and the Master Thief leave `hostile` out. Their faction `inner_circle` is friendly to the party by A2's
    relations, so they stay friendly until attacked, when the game alerts their kin.
  - The rows are D-25's (levels 12–32), with treasure level 3 and the hoard at 4.
- **Map card** (no spawn markers; encounter chance 0): slot 1 `Xeen Outlaw` tier 1, [2, 3], weight 85; slot 2
  `Xeen Wolf` tier 1, [1, 2], weight 15.

## Mechanisms

- **Gongs 1–3.** Each gong is a wall panel (`panel:gong1..3`, XD-03's `xngong` picture) south of its stair door.
  - A click asks "Ring gong how many times?" (aaze0062:2). The answer 3 or three runs A3's `q-d19.gongs`, whose window
    reads "The gong booms three times …", and opens that floor's stair door (`door:gong1..3`, which stays open).
  - Any other answer shows "The gong booms, and the echo dies away." (D-25 Q13). The door stays shut, and the next
    click asks again.
  - The stair doors refuse until their gong is answered: "The stone door will not move. A bronze gong hangs on the
    wall beside it."
  - The answers are kept in the map variables `gong1..3`.
- **The guild memo.** `panel:memo` (MM6 `scroll`) beside the first gong calls `q-d19.guild_memo`, which gives both
  answers.
- **The Ali Baba chest.** The chest event asks "What's the password?", with the message window "Ali Baba Chest. What's
  the password?" (aaze0063:6).
  - "open sesame" or "opensesame" sets the map variable `sesame`, runs `q-d19.ali_baba` (the Eastern Tower key 12340,
    chest_opened 113383) and opens the chest.
  - A wrong word does nothing.
  - Once the word is given, the chest opens like any other.
- **The tapestry and the button.**
  - The tapestry is two panels (MM7 `tap4`, `tap3`), and clicking it gives "Tapestry. …" (aaze0061:4).
  - `switch:button` at its north end says "Click. The wall beside the tapestry is gone. An illusion!" (aaze0061:5,
    :7). It drops `door:illusion` at once: a secret door of the hall's own ashlar.
  - The false wall clicked before the button says "Cold stone."
- **The strongroom's iron door** opens with A2's Strongroom Key 12262, a fixed item in the fence's lockbox (sixth
  session, "Strongroom unblocked" below); behind it the chest's 2 Energy Disks (`q-d19.l3_disks`).
- **The ledger.** The big desk (`platform:desk`, hover name "Ledger") runs `q-d19.ledger` (ledger_read 113381 and the
  autonote).
- **The Master Thief.**
  - He stands immobile behind his high chair and is NPC 5109 (`monsters[].npc`, merge point 22): clicked while he is
    at peace, he talks: "You got past the gongs and the chest. Impressive. ..." and A3's "Inner circle" topic with the
    Dark promotion. The source has no Master Thief, so nothing greets the party unasked; the high chair is furniture
    with no click. Attacked, he and his guards fight and the promotion is lost (no other route needs him).
  - His death runs a kill timer that calls `q-d19.master_thief` (master_slain 113384). On every load with
    master_slain set, his group (31) is hidden.
- **The Manual of Master Thievery** (D-25 Q11). The lectern `platform:manual` pays a member without player bit 11295
  1,500 experience once (`q-d19.thievery_manual`) and sets 11295. After that it says "You learn nothing new"
  (`q-d19.thievery_manual_again`).
- **The Prince Book.** The lectern `platform:prince_book` calls A3's `q-d19.prince_book` alone, for every member.
  - The lane lead decided on 2026-11-20 that the hook decides by q-c9's throne bit 11302, owns the read-once bit, gives
    the +2 Luck, and falls back to "For the eyes of the prince only!".
  - The map reads and sets no player bit for the book. Until A3's change lands the hook shows its prince text to
    everyone (Open issues).
- **Beds.** The four bunks and the bedchamber's bed say "Nothing here." (aaze0064:7–8).
- **Other lines.** The card table ("five aces"), the practice locks, the trap walk's two pressure plates (step lines),
  the straw heap, and the arrival line (a one-shot timer).

**Map qbits 110950–110959:** none used. The map uses map variables `gong1`, `gong2`, `gong3`, `illusion`, `sesame`,
plus the build's `once.*` variables. It names A3's Q-D19 bits 113381–113385.

## Exit (sealed) and the start

- **The start (D2's `into` for door:dd06):** room:door_hall at **(640, 1700, 0)**, facing **south** (direction 270),
  just inside the front door. The door is in the hall's north wall at x 640, and D2's door faces north.
- **The front door** is `panel:front_door` (`gcstdoor`). D2 is not installed, so it is sealed with "The iron-bound door
  will not open: something heavy lies against it outside. There is no way out here for now." It follows XD-05's
  "Sealed exits".
- **Unsealing:**
  1. Give project.yml a neighbour to `xeen_d2.odm` at A6's arrival in front of `door:dd06`.
  2. Make the panel an `exits` entry on the hall's north wall.
  3. Make `evt:front_door` the `exit` preset (D-24: no question).
  4. Add the plan entrance's `neighbour` and kind `both`.
  5. Add a `playtest_exit.yml`.

## Original lines (with aaze references)

- "Tapestry" / "Button" / "An illusion!": aaze0061:4–5, :7.
- "Ring gong how many times?": aaze0062:2 (answers :3–4).
- "Ali Baba Chest" / "What's the password?": aaze0063:6 (answers :7–8).
- The ledger (A3's text): aaze0062:1.
- "Energy Disc", in A3's `q-d19.l3_disks` text, reached only once the strongroom opens: aaze0063:0.
- "You learn nothing new": aaze0064:1.
- "Prince Book" / "For the eyes of the prince only!": aaze0064:3–4.
- "Bed" / "Nothing here.": aaze0064:7–8.
- "Three's the charm", in the memo: aaze0064:9.

The source's "Exit the Great Southern Tower?" (aaze0061:0) is not used (D-24).

## Textures (one family per area; none new)

- **The tower:** the Towers of Mok family from A6's towers kit (MM8 Castle of Air d27). That is `gston1wl` walls over a
  `gstntilev` skirting, `gston1fl` flags, `gstn1cl` ceilings, `gcstflor` cobbles in the stair halls, and `gcstdoor`
  stone doors.
- **The thieves' fittings:** MM7 `7trimd` boards (the den, the top floor, plank doors), `hwm2rf` black beams (the
  cone), `trim11_32` posts, `7t1books`, `7t1books1` and `7t1cabs` furniture, `t2bedsht`, MM6 `straw` (kennel, heap,
  dummies), MM6 `scroll` (the memo), and MM7 `tap4` and `tap3` (the tapestry).
- **Reused world textures:** XD-03's `xngong`, XD-04's `xwiron` (the treasury and strongroom doors) and `xngrille`
  (the kennel gate and pens).
- **Count:** 41 distinct with the chests' kinds, against a cap of 45.

## Dressing

`oymap audit --world xeen` reports 0 dressing errors and 0 dressing warnings. The first build's two sacks in front of
the fence's north opening were moved to the room's south-west corner. Containers stand against walls in pairs, and
tables stand off the walking lines. The mess's stew pot (`cauld00`) is in a corner.

**Dressing exceptions:** none.

## Checks (scratch root `output/studio_cal/dd06/root`, `--world xeen`)

- **Build:**
  - `validate`: no issues in L1–L4.
  - `build`: 0 warnings.
  - `fmt --check`: clean.
- **`audit --reach --solve`** (`output/studio_cal/dd06/audit.txt`): no errors.
  - All 25 sectors open up from the start in 4 solve steps. The solver does not model the strongroom's `lua: false`
    lock.
  - Five warnings, all `question.answer`: the gongs' "three" and the chest's words come from A3's memo hook, which the
    audit cannot read.
- **Playtests, 4 of 4 each** (`four.sh`; logs `output/studio_cal/dd06/run/playtest_1..4.log` and
  `playtest_hostility_1..4.log`, summary `four_a.out` and `four_b.out`):
  - `playtest.yml` (180 steps) covers the critical path: memo, three gongs including a wrong answer, the lockbox, the
    Ali Baba chest with a wrong word and then the right one, the strongroom refusal, the Manual's 1,500 experience, the
    Master Thief's talk with the guards still friendly, the ledger, the hoard, and the chute down. It ends with every
    window closed and a reload ("RELOAD ok at step 171").
  - `playtest_hostility.yml` (33 steps): the thieves and hounds are hostile, the guards and the Master Thief are
    friendly before and after a reload, and spawned kinds do not fight each other.
- **`tools/xeen/quests.py`:** no error from DD-06.
- **Pictures:** 29 tour poses (`shots.yml`), sheets `output/studio_cal/dd06/sheet1.jpg` and `sheet2.jpg`, looked at.
  - Fixed after looking: the front door picture was tiled; the upper bunks floated (posts added); the bed was bare
    (bedposts added); the hatch did not read (dark beams).
  - Rooms are flat-lit because there is no bake yet.

## Strongroom unblocked (2026-11-20, lane A7 sixth session)

- A2's Strongroom Key is item **12262**: `gen.py`'s `STRONGROOM_KEY` now defaults to it. The fence's lockbox holds the
  key, `evt:strongroom` needs `{item: strongroom_key}` ("The iron door is locked. The keyhole is cut for a heavy key."
  without it), plan and project carry it.
- `playtest.yml` (187 steps): the lockbox gives the key; the iron door opens with it; the strongroom's chest
  (`loot_chest(15)`) gives 2 × item 12334 and sets tower_disks 113382 (A3's `q-d19.l3_disks`).

## Words needed

1. **A sealed exit** (XD-11's word 1): the front door is a text panel until D2 exists.
2. A panel laid over an opening on the same wall built without a warning. The first gongs overlapped their stair doors,
   which the pictures showed.

## What the user should look at

- The gong rooms: the wrong answer's echo, and the stone door grinding open.
- The tapestry: its button, and the wall that vanishes.
- The stair halls: one long flight along the outer wall to a gallery.
- The counting room: click the Master Thief behind his desk for his greeting; his guards stand still.
- The chute from the top floor into the straw.
- Whether the green-grey Mok stone reads as a lived-in thieves' tower.

## Front door live to D2 (2026-11-20, lane lead A7)

D2 is installed (A6): the five unsealing steps are done in `output/studio_cal/dd06/tools/gen.py` (the sealed version
kept as `gen.py.pre_d2`): `exit:front_door` on the entrance hall's north wall at x 640 (`gcstdoor`, the `exit` preset,
"You step out into the tower's clearing.") to `exit:d2_door`, A6's point (15872, -7680, 1056) facing north (D2's event
20); the plan entrance `kind: both`. `playtest_exit.yml` (13 steps: the leave window, OK, on D2) measures the landing
at Z 1,057. A2's row 9155 is live: installed, re-baked from `assets_dev`, every playtest 4 of 4 from `assets_dev`
(`output/studio_cal/a7/s5_dd06_four.out`).

## Sixth session (2026-11-20, lane A7)

- **Strongroom** opened with A2's key 12262 ("Strongroom unblocked" above).
- **Lamp rule:** the 17 `torch01` wall torches stood on the floor about 50 off their walls (A1's audit: 15 warnings,
  lampcheck errors): each is now on its room's nearest wall (12 in) at height 176 (`gen.py` `on_wall`). Clean.

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- The kennel's pens and gate: `xwcage` (cage band; the pens at `scale: 1.25`, one picture up 320; the folding gate 1:1, 1.25 up) in place of the once-only grille `xngrille` (8 times along the pens).
- The Ali Baba chest 80 high (the 7gt002 kind's own height; at 112 its 16-wide end posts showed the `7gt002b` band 1.5 times up).
- The three gongs strike AU's `xeen_gong` at the gong (`evt.PlaySoundName("xeen_gong", x, y, z)`) on the right answer and in `wrong_effects`.

### Texture fit exceptions

- `textures.tile_seams` `xwiron`: the treasury's and the strongroom's folding iron doors (a folding leaf takes pictures at one texel a unit); the plate edges read as the doors' bands.

## Fifteenth session (2026-11-21, lane A7 sub-agent)

- **The Master Thief talks himself** (merge point 22, `monsters[].npc`): `monster:master_thief` carries `npc: 5109`
  (scene actor 29, `npc_id` 5109). Dropped from `gen.py`: `plate:before_desk` and its once-only `evt:master_approach`
  (the source has no greeting to keep), and the chair's `evt:master_chair` (it spoke only for him; its post-death line
  went with it). Event and map variable numbers are kept by `ids.lock.yml` (28, 29 and `once.master_approach` 6 unused).
- `playtest.yml` (186 steps) clicks him (`interact_actor` 29) for the greeting, and again after the ledger.
- `xcycle.sh`: build warnings 0, audit 0 errors, 9 warnings (the 4 `xwiron` seams and 5 `question.answer` above).
  Installed with bake (01:51:54), stale bakes 0. From `assets_dev`, 4 of 4 each: `playtest` 186, `playtest_hostility`
  33, `playtest_exit` 13 (`output/studio_cal/a7/s15_dd06_four.out`).

## D-58 roof stair (2026-11-21, seventeenth session, lane A7 sub-agent)

Decider D-58 (`briefs/d7/L1/D58_DECISION.md`, D-4 and Q2): a roof stair from the top floor up through a trapdoor, one
way up to D7's named arrival `entrance:dd06_roof`, open after `m30.done`. Generator `tools/gen.py` (the version before
it: `output/studio_cal/dd06/s17/gen_before_s17.py`, L4 before: `s17/L4_before/`; the unchanged generator reproduced
that L4 exactly first).

- **A new way, not the getaway hatch.** The getaway hatch is a trapdoor in the floor down the chute to the entrance
  hall: the source's way out and the map's fourth loop. A roof needs a climb of over 500 up, which the small getaway
  room (640 by 896, 544 high) cannot hold beside its floor trapdoor. So the roof stair is a hall of its own that opens off
  the getaway room's north wall: the thieves' room of ways out now has one down and one up.
- **Where:** `room:roof_stair` "Roof stair", (1024, 768)-(1536, 2048), floor 1,920 (the top floor), over the second
  stair hall. `open:getaway_roof` (256 wide, at x 1,168) from the getaway room. One flight of 16 steps of 32 up the east
  wall, rising north from (1376, 896) to the head `platform:roof_head` (1024..1536, 1664..2048) at **2,432**; the hall's
  ceiling 2,720. Over the head the hatch: four black beams (`hwm2rf`, 32 wide, 40 deep) framing (1184, 1760)-(1376,
  1952), and inside them the closed leaf `platform:roof_hatch` (plank `7trimd`, 16 thick, 2,704 to 2,720), centred
  **(1280, 1856)**. A wall torch on the west wall at the foot (1036, 1180, 2096), a lamp over the foot (2,380) and one
  over the head (2,632). No monsters, no props.
- **Wiring (sealed; opened in the eighteenth session):** `evt:roof_trapdoor` (event 46, "Roof trapdoor", a script on the leaf): condition
  `all: [{lua: XeenQuests.hook("d7.roof_dd06")}, {map_var: d7_open}]`, effect `{exit: exit:d7_roof}` (the game's leave
  window, as the exit preset; exits stand on walls, so the ceiling leaf is a platform with the `exit` effect). The hook
  runs first: before `m30.done` (111600) its "The trapdoor is shut fast." and nothing else; with it, the else line
  "Wind whistles round the trapdoor's edges, but it will not lift. (Not open yet.)" (shown only while
  `XeenQuests.can`). Map variable `d7_open` (8) is never set. project.yml neighbour `exit:d7_roof` to `xeen_d7.odm`,
  kind `roof`, `one_way`, `arrival: entrance:dd06_roof`.
- **Opening it when D7 installs (the lead; done in the eighteenth session, see the last section):** drop `{map_var: d7_open}` from the condition in `gen.py` (and the
  variable), rebuild against a root with D7 installed (the build then knows the arrival). The else line then never shows.
- **Checks** (root `output/studio_cal/dd06/root`, resynced from `assets_dev`, binaries of merge point 25):
  - fmt clean; validate clean; build 1 warning (`exit:d7_roof.arrival`: D7 not installed, as FD-03's P5 hatch).
  - `audit --reach --solve` (`output/studio_cal/dd06/audit.txt`): **0 errors**, 10 warnings: the 9 known (4 `xwiron`
    seams, 5 `question.answer`) and `state.never_set` map_var 8 (the seal, by design until D7); one info
    `click.silent` (an impossible path). 26 sectors, all reached with the doors open; no `lights.*`, `doors.*`,
    `dressing.*` finding.
  - Playtests 4 of 4 each from the root (`output/studio_cal/a7/s17_dd06_roof_four_b.out`, logs
    `output/studio_cal/dd06/a7_xrun/`): `playtest` 186, `playtest_hostility` 33, `playtest_exit` 13, and the new
    `playtest_roof.yml` 26 (put in the getaway room, walks up the flight to the head, clicks the trapdoor: "The trapdoor
    is shut fast." and no sealed line; `set_qbit 111600`; clicks again: "(Not open yet.)"; still on DD-06, on the head).
  - Pictures: `output/studio_cal/dd06/s17/roof_sheet.jpg` (shots in `s17/shots/`, tour `s17/tour_roof.yml`), looked
    at: the doorway off the getaway room, the flight with the hatch at its head, the framed plank trapdoor from the head.
    Unbaked (flat light).
- **For D7 (A6):** the trapdoor is at (1280, 1856) in the tower's north-east quarter (the tower is 4,096 square,
  -2048..2048; the hatch 768 in from the east wall and 192 from the north wall), its leaf at 2,704 to 2,720 over the
  head at 2,432; the highest point inside the tower is the roof stair's ceiling, 2,720 (the counting room's beams
  2,560). D7's `entrance:dd06_roof` (L4: (5632, -14848, 704) facing south) should stand on the roof beside its hatch;
  where on the roof is D7's choice.
- Not installed, not baked (the lead does both).

### D-58 roof stair installed (2026-11-21, lane A7 lead, seventeenth session)

- Installed with its bake 04:49:43 (`install_baked.sh` from `output/studio_cal/dd06/root`), stale bakes 0. Audit from
  `assets_dev` 0 errors, 10 warnings (the 9 kept ones and the sealed roof's map variable) (`output/studio_cal/dd06/audit_assets_dev_s17.txt`). **16/16 from `assets_dev`** (playtest
  186, hostility 33, exit 13, roof 26; `output/studio_cal/a7/s17_dd06_four.out`). Open when D7 installs: drop `{map_var: d7_open}` in gen.py.

## Eighteenth session (2026-11-21, lane A7 lead)

- The roof trapdoor is open (D7 installed by A6, 04:53): condition A3's `d7.roof_dd06` only, effect `{exit: exit:d7_roof}` to `xeen_d7.blv` `entrance:dd06_roof`; D7 is an indoor map, so the move is at once (no leave window); `d7_open` and the sealed line gone. `playtest_roof`: shut before m30.done, then lands on D7 at (5632, -14848) z 640-800. Build warning (kept): the studio does not see that the hook's fail text answers a failed condition.
- Installed with its bake 05:20:15 (`output/studio_cal/a7/s18/install_queue.sh`), stale bakes 0; audit from `assets_dev` 0 errors, 9 warnings (the 9 kept ones; the sealed roof's variable gone) (`output/studio_cal/a7/s18/audit/dd06.txt`); **16/16 from `assets_dev`** (playtest 186, hostility 33, exit 13, roof 28; `output/studio_cal/a7/s18_four.out`, merge point 25/26 binaries).

## Twentieth session (2026-11-21, lane A7 lead)

- D-66: the roof trapdoor checks A3's `d7.roof_dd06` first (before m30.done its "The trapdoor is shut fast."), then asks the map's own Yes/No "Climb up through the trapdoor?" (DD-08's pattern, no hook text before it, D-65); Yes runs the hook and moves at once (`{direct = true}`) to D7's `entrance:dd06_roof` (5632, -14848, 710) facing 1536, No stays. `playtest_roof.yml` answers No (stays) then Yes (lands, measured). The build warning about the hook condition is gone.
- Built into `output/studio_cal/a7/s20/dd06/` with the oymap of merge point 27: BLV and scene byte for byte the installed ones (no rebake; stale bakes 0); the Lua differs by the trapdoor only. Lua and studio file installed 06:51:18. Audit from `assets_dev` 0 errors, the 9 kept warnings (`output/studio_cal/a7/s20/audit/dd06.txt`). **16/16 from `assets_dev`** (playtest 186, exit 13, hostility 33, roof 39; `output/studio_cal/a7/s20/four_dd06.out`).

## Door pictures (2026-11-22, lane A7 twenty-seventh session)

F12(b), the orchestrator's decision (plank-strip leaves titled Door show a door picture of the family): the six plank doors (7trimd strips) are two leaves each showing MM8's plank door pair gkp103a/b (one wing a leaf, 128 by 256 at its own size); their doorways 256 high (were 320). gen.py. Installed with the bake; build warnings and audit as before; tests 4 of 4.

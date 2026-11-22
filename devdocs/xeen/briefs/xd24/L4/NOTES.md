# XD-24 Nightshadow Crypt: L4 notes

Lane A7, agent `agent:xeen-a7-xd24`, 2026-11-20. Map `xeen_xd24.blv`, map_stats 9147, music 3, class S, under
Nightshadow's square on X3, Act III, party 25-29, monsters 32-40 and Count Draco 45, treasure level 3 (the vault's
hoard 4). Design: the MU-6 graph `devdocs/xeen/mockups/act3_graphs/xd24.graph.yml` and its section of
`notes_cloudside.md`, with decider D-25 (`mockups/act3_a7_decisions.md`) winning where they differ; A3's
`source/quests/q-c7.yml`.

Every file of L1-L4 except the playtests and this file is written by `output/studio_cal/xd24/tools/gen.py`
(`--levels` for L1-L3; `--standin` builds with the shipped stand-ins for the two new textures); rebuild with
`output/studio_cal/xd24/cycle.sh` (fmt, validate, build, install into `output/studio_cal/xd24/root`, audit). Never
hand-edit the written files. Not installed into `assets_dev` (the lane lead installs and bakes).

## What was built

Fourteen rooms, fourteen sectors, 19.85 M units² of floor (`oymap metrics`; S: at most 15 and 20), three loops,
3 chests, 7 doors, 24 events, 22 monsters. Frame: x east, y north; the town's crypt at z 0, the Count's catacombs at
-640, his vault at -1280.

| Room | Size | What |
| --- | --- | --- |
| Coffin stair foot | 896 × 1,024, 512 high | The arrival from X3's open coffin (start 0, 704 facing south); candle stubs, bones; no monsters (D-11.3). The Count's stair comes out in its east wall once he is dead |
| Coffin stair | 384 × 768, 12 steps up | Up to the underside of Draco's coffin: the exit to X3 (the `exit` preset, D-24) |
| Town ossuary | 1,280 × 1,280 | North and south walls of stacked bones (`xobones`), two bone shelves, skull piles; gnome vampires 2 + 2 (D-25) |
| Gnome niches | corridor 2,432 × 512 | Five niches in the south wall, each with a small stone coffin, its wooden lid aside: "The coffin is empty." (three clickable); gnome vampires 2 + 3 (D-25) |
| Night chapel | 1,216 × 1,792, roof to a point at 1,088 | The black altar (`7tfb11`) under the painted moon window (new `xmoonwin`), carved skulls either side (`d2skulas`); 3 gnome vampires; the ossuary's door, the niches, the sexton's door, the stair down |
| Sexton's room | 640 × 640 | Dead end: his cot and his lockbox (chest, T3) |
| Chapel stair | 384 × 1,152, 20 steps down | To the catacombs |
| West catacomb | 640 × 2,304 | Loculi in both long walls (MM8's `d2niche1-4` on `cwb`, rough `cwb1` vault); 2 gnome vampires |
| Draco's gallery (set piece) | 2,048 × 896, 640 high, low hipped roof | Five portraits of the Count, the same face in every frame (new `xdracoport`); one Vampire of his household |
| East catacomb | 640 × 1,280 | Older loculi, a collapsed one (rubble); 2 gnome vampires |
| The Count's feast hall | 1,280 × 1,280 | The long table laid with plates, goblets and a candle, the Count's portrait at its foot, the silver plate chest (T3) at its head; 2 Vampires. Both doors on the north side, the table off the walking line |
| Vault stair | 1,152 × 384, 20 steps down | The iron door (`t5d1`, gilt symbols) at its foot, the inscription over it; no monsters (rest here until 21:00) |
| Draco's resting vault (set piece, goal) | 1,920 × 1,920 at -1280, hipped ribbed vault to 1,280 high | The dais (a step of 32), the great sarcophagus with the rhyme on its foot, two ribs crossing under the vault, the Count's portrait; Count Draco and two Vampires; his hoard (chest, T4) by the north wall |
| The Count's stair | path, 320 wide, climbs 1,280 | A ramp from behind the dais up to the stair foot (level 256, 1,664 north climbing 896, a turn west climbing 384); a wall slab at each end sinks when he dies |

Texture family (one per area, ROADMAP §5.2): MM7's grey castle stone `cnb` from Castle Navan's dungeon (7d15) with its
flags `t3s2fl` and oak-and-arch doors `cndl` on the crypt floor; the catacombs in the browner `cwb`/`cwb1` with MM8's
loculi; the Count's rooms the same `cnb` on dark slabs `7tfb11`, dressed with portraits, plate and candles (no second
family). 24 distinct textures (cap 30), 2 new (cap 4).

## Monsters (A2's rows, all placed, hostile)

| Where | Rows | Group |
| --- | --- | --- |
| Ossuary | 4 Gnome Vampire 11290 (32) | 1 (2), 2 (2) |
| Niches | 5 Gnome Vampire | 3 (2), 4 (3) |
| Chapel | 3 Gnome Vampire | 5 |
| West catacomb | 2 Gnome Vampire | 6 |
| Gallery | 1 Vampire 11291 (40) | 7 |
| East catacomb | 2 Gnome Vampire | 8 |
| Feast hall | 2 Vampire | 9 |
| Vault | 2 Vampire; Count Draco 11293 (45, blink on hit) | 10; 11 |

22 monsters (16 + 5 + Draco), groups of 2-3 (the gallery's lone Vampire as the graph), kill XP about 8.5k per member
(D-25 Q2). No spawn points; `encounter_chance` 0 (the vault stair is the resting place, D-25). Map card slots (the card
only): `Xeen Vampire` tier 0 (2-3, 75), tier 1 (1-2, 25).

## Mechanisms, hooks and qbits

- **Iron door** (`evt:iron_door`, event 18, `door:iron` 5): its condition is `qbit vault_open or Xeen.isNight()`
  (`Xeen.isNight` exists in `worlds/xeen/events/common/xeen_common.lua`: hour ≥ 21 or < 6). By night it opens, sets
  `vault_open` and says "The symbol on the iron door flares once and goes dark. The door swings inward."; by day a
  message window: "The door refuses to budge. A symbol etched on its surface flashes pale blue whenever you try to
  move it." (D-25 Q1). `evt:vault_state` (load) keeps it open once opened: Draco then fights at any hour.
- **Draco's death** (`evt:draco_dead`, event 16): a 2-second timer, `once`, on `kills: monster:draco` (XD-05's drum
  method) runs `XeenQuests.hook("q-c7.draco")` (A3: sets q-c7.done 112141, 10,000 experience, its text) and sinks both
  slabs of the Count's stair (`door:count_base` 1, `door:count_top` 2), with a window "Behind the dais a slab of the
  wall sinks into the floor ...". `evt:count_state` (load, on 112141) keeps the stair open.
- **Map qbits** (block 110940-110949): **110940 `vault_open`** (the iron door was opened once). No other map qbit; the
  once-flags are map variables (`once.arrive` 0, `once.count_stair_seen` 1, `once.draco_dead` 2).
- **A3's bits read:** 112141 q-c7.done (`draco_done`).
- **Arrival line** (`evt:arrive`, one-shot timer, until Draco is dead): "Draco's coffin was a door: the stair under it
  ends in the old crypt of Nightshadow. Somewhere below, the Count sleeps by day. The town's signs said the rest: only
  at night can you put up a fight."

## Original lines

| Line | Ref | Where |
| --- | --- | --- |
| "The coffin is empty." | aaze0029:3 | the niches' coffins 1, 3, 5 (events 7-9) |
| "Only at night can you put up a fight." | aaze0029:6 | the inscription over the iron door (event 22, a window) |
| "The door refuses to budge. A symbol etched on its surface flashes pale blue whenever you try to move it." | aaze0029:24, paraphrase (lid → door, D-25) | the iron door by day |
| "Open his coffin and bid him farewell; only then can you use the magic of the well." | aaze0029:8 | the sarcophagus's foot (event 21, a window) |

## Into the world

- **X3's `into`** (A5, `thing:coffin_open`): this map's start **(0, 704, 0) facing south (270°, 1536)**, at the foot
  of the coffin stair.
- **The exit** (`exit:coffin`, event 17, the `exit` preset) is live to `xeen_x3.odm` at (17664, -5120, 992) facing
  south (1536). **Measured** (playtest_exit.yml, 2026-11-20, this root): the party stands at **z 1009** there (the
  square's ground is 17 above the named 992; the game lifts the party onto it, no fall).
- Map row: A2's `map_rows.yml` row for XD-24 does not exist yet; the scratch root carries a test row 9147 (copied from
  9149's, `sync_test_rows.py`).

## Measurements

- `oymap metrics`: 14 sectors, 16 links, 3 loops, 19.85 M units² of floor, 24 textures.
- `scale_bands.py`: upper-quarter room area 1.84 M (shipped median 1.64 M, percentile 57); largest room 4.0 M
  (percentile 29); typical ceiling 832 (percentile 92); upper-quarter height 1,088 (percentile 85); doorway width 320.
- Audit (`--reach --solve`): no error, no warning; every sector on foot from the start with the doors out of the way
  (12 of 14 with the doors as they start: the vault and the Count's stair).

## Textures made (Codex, `output/studio_cal/xd24/tex`, `xtex.py --project`)

| Name | Size (art) | Kind | Refs | Where |
| --- | --- | --- | --- | --- |
| `xdracoport` | 128 × 256 (art 128 × 192) | picture | mm7 cnbport-2, cnb, cnbport-1 | the gallery (5), the feast hall, the vault: the same Count in every frame |
| `xmoonwin` | 128 × 256 (art 128 × 192) | picture | mm7 cnbw, cnb, cnbport-2 | the chapel's painted moon window over the altar |

Installed in the scratch root only (`worlds/xeen/textures_x4`, `textures_x2`); for A6's registry
(`source/textures.yml`) and the lane lead's install. Faces show them `fit` on 256 × 384 panels (their art's 2:3).

## Dressing exceptions

None: the audit lists no dressing warning. Containers: none (no barrels in a crypt); candles, skull piles and bones
stand by the walls or on the furniture.

## Words needed / workarounds

- A secret door that is found by an event and not by Perception: the Count's slabs are plain doors drawn as the wall
  (`tile: true`, no `secret` flag), so they do not pulse red for a perceptive party before the Count is dead.
- The headless runner opens no window from a timer: the playtest asserts the arrival and kill timers by their map
  variables.

## Playtests (from `output/studio_cal/xd24/root`, `--world xeen`, merge point 11 binaries)

- `playtest.yml` (90 steps): the critical path with the day refusal and the night opening, the kill timer, the Count's
  stair, a reload, the exit.
- `playtest_hostility.yml`: all three kinds hostile at load, none fights another.
- `playtest_exit.yml`: the exit to X3 and the landing height.

## What the user should look at

- The gallery: five copies of one portrait, as the source says; the feast hall and the vault have it too.
- The iron door at the foot of the vault stair: the bottom tread before it is narrow (a stepped stair ends at the door).
- Draco's vault: the dais step, the plain stone sarcophagus, the ribs under the hipped vault.
- Vampires wear the stand-in Vampire family's look (A2/S).
- Lighting is unbaked in the pictures (the lane lead bakes).

## Sixth session (2026-11-20, lane A7)

- **Lamp rule (A1's lights audit, merge point 14):** `catae_torch` along the north wall 0.5 → 0.2, out of the opening; the Count's stair note says two-way after his
  death (D-33 (1)). Clean under the audit.

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- No error. Warning kept:

### Texture fit exceptions

- `textures.tile_seams` `cnb1s`: the vault's three stone ribs (48-square beams under the great crypt's ceiling); the stone's course lines read as the blocks' joints along each rib.

# XD-16 Volcano Cave: L4 notes

Lane A7 phase 5 (agent `agent:xeen-a7-xd16`), 2026-11-21. Map 9142, `xeen_xd16.blv`, class M, `world: xeen`, on X7
Mount Firestone (the cave mouth at its west foot between the demon and devil idols), Act V, party 48-52. Built from
the MU-6 graph `devdocs/xeen/mockups/act5_graphs/xd16.graph.yml` with decider D-47 (`mockups/act5_a7_decisions.md`),
which wins where they differ, and A3's `source/quests/q-c26.yml`.

Generator: `output/studio_cal/xd16/tools/gen.py` writes L1-L4. Never hand-edit the written files. The playtests are
written by `tools/gen_tests.py` from the built `ids.lock.yml`. The cycle (generate, fmt, validate L1-L4, build, install
into the scratch root, audit) is `output/studio_cal/xd16/cycle.sh`; the pictures are `shots.sh` with `shots.yml`. The
scratch root is `output/studio_cal/xd16/root` (hard-link copy of `assets_dev`, real copies of `worlds/xeen/maps`,
`events/maps` and every `data_tables` file).

## What was built

- **Floor 0, the burning halls (z 0 = X7's sill).** The cave mouth (the arrival, quiet; daylight in the west wall is
  the way out). The ash gallery (3 Demons). South of it the smoking passage (2 Devils, a real T5 chest) and, behind an
  iron door, the vault of chests (quiet). The fire lake, a tall cavern (1,152) round a lake of lava 128 below the shore
  (`floors: lava`), banked on its four outer sides; the island in the middle carries the devil skull's black altar and
  three Devils, reached by a causeway of crust 256 wide (2 Demons and a Devil on the shores). North, the fissure (glowing
  seams, 2 Demons) to the demon shrine's iron door: worked stone, four floor braziers, four wall torches, the demon
  skull's black altar on a dais, 3 Demons. From the shrine's south-east corner the cinder run (2 Demons) runs back south
  along the lake's east side to the stair head on the south shore.
- **Floor -1, the gate stones (z -640)**, down twenty rough steps: the stair foot; the lever hall with the black pillar
  and its four lever stones (2 Demons, a Devil); the steam vents (2 Demons, a Devil, a real chest) closing the loop to
  the lever hall; the magma caves (2 Demons, a Devil) with the lava river (two banked reaches) and the stepping crust
  between them, to the slag pocket (a real chest by an old pick). The gate run opens south off the lever hall in sight
  of the pillar: five short rooms between four slabs of black rock (2 Devils and a Screamer beyond the third and
  fourth).
- **Floor -2, the heart of the mountain (z -1,280)**, down the deep stair: the obsidian landing; the ember pocket (a
  Devil, a Screamer, a real chest); the glass caves (2 Demons, a Devil) and the ash pits (a Devil, a Screamer), each an
  L reaching from the landing down to a ledge of the magma heart; the heart (1,280 high), an octagonal pool of lava
  banked on every side with a ring ledge (3 Screamers); the last cave and its rock; the cool passage beyond.
- **Counts.** 28 rooms (29 sectors with the outside), 48.9 M units² of floor (`oymap metrics`; 50.1 before the rough
  walls). 7 doors (the vault and shrine iron doors,
  the four slabs, the way's rock) and four levers. 5 real T5 chests (the smoking passage, the vault's real chest, the
  steam vents, the slag pocket, the ember pocket) and 5 trap chests. 3 loops (round the lake, the vents, round the
  heart). 40 monsters, all placed and hostile in groups 10-33 by room: Demon 11630 (42) x 20, Devil 11631 (50) x 14,
  Screamer 11632 (58) x 6; floor 0 18 (12/6/0), floor -1 12 (6/5/1), floor -2 10 (2/3/5). Kill XP 27.34k per member.
  Music 7. No boss.
- **Textures:** MM7 Thunderfist 7d07 (D-45): `c2b`, `c2bb`, `cfb1`, `dirt`, `7dirttyl`, `lava`, `cwb`, `cwb1`,
  `ch1b1`, `t5d1`, and Xeen's `xodaylt` in the mouth (as XD-26); with the chests' own pictures 19 distinct (`oymap
  metrics`) of the 45 cap, **0 new** (`xvskull` not made: the altars are blocks of the seamed black rock with a skull on
  each). By area `c2b` 62 %, as 7d07's own 60 %.

## Mechanisms (D-47)

- **The skulls (Q-C26).** Each altar (a platform) asks the source's question (aaze0046:0 demon, :1 devil; a real
  choice, "yes"/"y"). Yes calls A3's `q-c26.demon_skull` / `q-c26.devil_skull` (the second sets `q-c26.done` 112522),
  breaks the skull (a destructible of the skull decoration, `trigger_only`, not hurt by blows) and plays
  `xeen_fire_ignite`. A broken altar clicked again gives the hook's "splinters" line; on every later load the broken
  skull stays broken.
- **The way (Q4).** The rock across the last cave's end is a door (`door:way`, slide_left, bare `c2b` rock). Before
  `done` its click calls `q-c26.way` (the fail line "Bare rock, hot to the touch. Two skulls ..."). A one-second timer
  sees `done` without `rock_drawn` and grinds it open with a stone-door sound in the same visit as the second skull
  (map qbit `rock_drawn` 118054); a load event opens it on every later load. The first step into the cool passage calls
  `q-c26.way` (its text). The passage's end (`exit:way_end`, fallen stones, cwb1) is the `exit` preset ("The way to
  Shangri-La") to XD-17's named arrival `entrance:xd16_way` (-1280, -4736, 4) facing north (fifteenth session; an
  indoor map, so no leave window).
- **The lever stones (Q3).** Four levers on the pillar's north, east, south and west sides, titled "First slab" ...
  "Fourth slab". Each pull: map qbit `slab_N` (118050-118053), A3's `q-c26.lever`, and its slab (slide_down) grinds into
  the floor. One-way (D-43): a second click calls `q-c26.lever_down` ("The lever is down."). A slab clicked: "A slab of
  black rock fills the passage. It does not move for you." Lowered slabs stay down on every load.
- **The vault of chests (Q2).** Six `ch1` chests in a row on the dais, all titled "Chest". West to east: trap, trap,
  **real**, trap, trap, trap. Each trap chest stands on a dark hearth stone with embers glowing in its cracks (`c2bb`
  laid small, 8 high on the dais) and has a faint pulsing ember light at its foot; the real chest stands on the bare ash
  of the dais and has neither. (MM6's burning rock `Brnrock0` was tried first: indoors it is a big rock in flames that
  hides the chests, not a faint tell.) A trap's first opening: map qbit `trap_N` (118055-118059), the
  `explosion` sound, Fire 50 on each member, "The chest explodes!" (aaze0046:6); after that "The chest is empty."
  (aaze0046:2). The real chest holds T5 loot (4 rolls, 4,000 gold).
- **Lava (Q5).** The lake (one C-shaped level round the island and causeway), the river's two reaches and the heart's
  pool are sunken levels 128 deep, `floors: lava`, `lava` texture, crust (`c2b`) edges. Every basin has banks the party
  walks out by: the lake on its four outer sides (192), the river reaches on both long sides (160), the heart all round
  (192). The causeway, the island, the stepping crust and the ledges are plain floor.
- **Stairs** are walked (20 steps of 32 each, twice); no stair asks or shows a sign (D-47).
- **Arrival line:** a one-shot status line six seconds in: "Heat on your face and a red glow far ahead. Behind you,
  daylight between a demon and a devil of black stone."

## Measurements

- **Arrival** `entrance:x7_mouth`: (256, 0, 0) facing east, in the cave mouth about 256 inside. It is the map's start.
- **Way out:** `exit:mouth` (the exit preset, 448 x 384 of daylight in the mouth's west wall) to X7's named arrival
  `entrance:xd16_mouth` (512, 9728, 2240) facing west. Measured landing (`playtest_exit.yml`, 4 of 4): **(512, 9728,
  2241)** after 2 s.
- **XD-17's arrival** `entrance:xd17_way`: (4864, -18176, -1280) facing north, in the cool passage about 256 inside its
  far end, facing back toward the last cave.

## Checks

2026-11-21, from `output/studio_cal/xd16/root`, binaries of merge point 20:

- `oymap validate` reports no issues on L1-L4, `fmt --check` is clean, the build has 0 warnings.
- `oymap audit --world xeen --reach --solve` (`output/studio_cal/xd16/audit.txt`): **0 errors, 0 warnings** (no
  `lights.*`, `doors.*`, `textures.*` or `dressing.*` finding); one info, `texture.squashed` on the exit's daylight
  face. On foot from the start 15 of 28 sectors with the doors as they start, 28 with every door out of the way; no dead
  handler.
- Playtests, 4 of 4 each (`output/studio_cal/xd16/four.out`, logs `output/studio_cal/xd16/a7_xrun/`):
  - `playtest.yml` (118 steps): the arrival line, the way out's window cancelled; the devil skull (Yes); the rock still
    shut after one skull and its click's fail line; the splinters line; the demon skull (Yes: done) and the rock open
    within six seconds in the same visit (rock_drawn set); the cinder run and the rough steps; the four lever stones
    (each slab down, each second click "The lever is down."); the gate run, the deep stair, the glass caves, the heart's
    west ledge, the last cave; the cool passage's line; up to its end; a save and load (`RELOAD ok`): the rock and the four slabs stay open.
  - `playtest_traps.yml` (32): every member at 100 HP, the westmost trap chest: "The chest explodes!", each member then
    40-60 (Fire 50), trap_1 set; again: "The chest is empty.", no damage; the real chest's loot (4,000 gold and more).
  - `playtest_lava.yml` (133): into the lake's north reach, the lake under the causeway, both river reaches and the
    heart: each burns (every member under 100 a second in) and each is walked out of by its bank to the floor, with no
    burn after.
  - `playtest_exit.yml` (14): out to X7, the landing above.
  - `playtest_hostility.yml` (23): 20 Demons, 14 Devils, 6 Screamers hostile, after a reload too; a Demon, a Devil and
    a Screamer side by side do not fight each other and go for the party.
- Pictures (unbaked, so the rooms are evenly lit): `output/studio_cal/xd16/shots/` (22, tour `shots.yml`), sheets
  `sheet1.jpg`-`sheet4.jpg` and `sheet_final.jpg`; `shots/11-vault-3m.png` is the trap tell from about 3.8 m.

## Map qbits used (block 118050-118059)

| Name | Number | What |
| --- | --- | --- |
| slab_1 .. slab_4 | 118050-118053 | the four lever stones pulled (one-way) |
| rock_drawn | 118054 | the way's rock drawn open |
| trap_1 .. trap_5 | 118055-118059 | the five trap chests burst |

A3's bits read or set through the hooks: `demon_skull` 112520, `devil_skull` 112521, `done` 112522.

## Test rows

None. A2's map row 9142 had landed in `assets_dev` before the root was made (CAVE, Xeen Demon Dif 5 [1, 2],
encounter 10, music 7); the root's tables are plain copies. The project's `map_stats` gives lock 15, trap 8,
perception 15, treasure 5 (A2's values).

## Count exceptions

- 40 monsters under M's floor of 45: MAPS §0's own count for XD-16 (D-47 Q1).

## Original lines

- aaze0046:0 "The skull of a demon grins wickedly at you, and you have a sudden desire to smash it.  Destroy?" (the
  demon altar's question).
- aaze0046:1 "The skull of a devil stares at you as though daring you to damage it.  Destroy?" (the devil altar's).
- aaze0046:6 "The chest explodes!" and aaze0046:2 "The chest is empty." (the trap chests; map-local, for A3's
  ORIGINAL_LINES).
- aaze0046:5 "Leave the Volcano Cave?" is the exit preset's meaning (D-24); aaze0047/48:0-1 are ledger only (D-47).
- Map-local lines (A3 to record): the slab's "A slab of black rock fills the passage. It does not move for you.", the
  arrival line (the sealed end's line is gone with the exit).

## Audit exceptions

None: the audit has no warnings (one `texture.squashed` info on the daylight face of the exit, as XD-26's).

## Texture fit exceptions

None.

## Dressing exceptions

None.

## Optional polish (D-51)

- **Smoke indoors: optional polish (D-51).** The `smoke` decoration (EmitSmoke) emits only outdoors
  (`OutdoorSpatialFxRuntime`); indoors it draws nothing. D-51 (2) accepts the tell as built (the ember-cracked stones
  and their faint pulsing light under the five trap chests, the real chest on bare ash); smoke is not a condition of
  done. **Done in the eighteenth session** (merge point 25: `smoke` smokes indoors): `deco:smoke_trap_1..5`, the
  engine's `smoke` 88 north of each trap chest on the dais (just off the hearth stone's edge), the real chest none;
  always on (a burst chest smokes as well). Audit 0/0.
- Baked re-capture (2026-11-21, fourteenth session, from `assets_dev` with its bake):
  `output/studio_cal/xd16/s14_baked/01-vault-3m.png` (and `02-vault-trap-close.png`, `03-cool-passage-end.png`):
  from about 3 m the five dark ember plinths and the one bare chest still stand apart at a glance.
- The cool passage's end: `exit:way_end` on the far (south) wall at y -18432 to XD-17's `entrance:xd16_way`;
  `entrance:xd17_way` stands at (4864, -18176, -1280), 256 inside that end, facing north back down the passage (D-50).

## Blocked on

- Nothing. XD-17 (A5, installed 01:45): the cool passage's end opened (fifteenth session), XD-17's way back arrives
  at `entrance:xd17_way`; the arrival line (`evt:arrive`) now speaks only in the mouth (`evt.GetPartyPosition` inside
  room:mouth), not to a party back from Shangri-La. `playtest_way.yml` walks both ways and checks it.
- **X7's door:xd16 (A5):** X7's door is sealed until this map is installed; it then names `entrance:x7_mouth`.

## What the user should look at

- The fire lake from the north shore (the island, the causeway, the lava light), and walking into the lava and out.
- The vault of chests: five chests on dark ember-cracked stones, the real one on the bare ash (`shots/11-vault-3m.png`).
- The lever hall: each lever lowers its slab down the gate run.
- The magma heart and the rock that grinds open when the second skull breaks.
- The mouth's daylight is XD-26's `xodaylt` (a green valley): X7's own slope would read better there; a picture for
  A6 if wanted.
- The map is unbaked; the lane lead bakes it.
- Fifteenth session (2026-11-21, merge point 22): the cool passage's end to XD-17 (exit preset, project neighbour
  `exit:xd17_way`), the arrival line only in the mouth, `playtest_way.yml` (to XD-17 and back); first installed with
  its bake 01:58:55 (24/24, `output/studio_cal/a7/s15_xd16_four.out`), then again with the mouth-only line
  (`output/studio_cal/a7/s15_xd16_four_b.out`).

## Eighteenth session (2026-11-21, lane A7 lead)

- Smoke wisps over the five trap chests (see Optional polish); baked shots `output/studio_cal/xd16/s18/shots/` (faint wisps over the five, none over the real chest).
- Installed with its bake 05:22:05 (`output/studio_cal/a7/s18/install_queue.sh`), stale bakes 0; audit from `assets_dev` 0 errors, 0 warnings (`output/studio_cal/a7/s18/audit/xd16.txt`); **24/24 from `assets_dev`** (playtest 114, exit 14, hostility 23, lava 133, traps 32, way 23; `output/studio_cal/a7/s18_four.out`, merge point 25/26 binaries).

## D-89 cave shape, identity and name test (2026-11-22, lane A7 28th-29th sessions)

Shared pass `tools/xeen/cave_shape.py` (corners cut where no other room, object or numbered wall is near, `rough` walls,
floor points that rise and fall with everything standing pinned level, vaulted roofs), called from this map's generator
after L4 is written; `identity:` in project.yml. Metrics are `oymap metrics`' cave_shape (floor uneven share, ceiling
spread, rough wall share; the audit's numbers 0.30 / 80 / 0.18). `tools/xeen/check_identity.py <key>` checks the family
share and the shape of the installed map.

- Metrics before -> after (floor / ceiling spread / rough): 0.23 / 17 / 0.41 -> 0.41 / 97 / 0.45; family 7d07 87 %.
- `playtest_way.yml` (gen_tests.py): XD-17's way back (its event 20) is now a BLV-to-BLV move with the leave window
  (picture 1, A5's rebuild on oymap MP40+): the test answers it. 4/4 (`s29/xd16/t022248`).
- Name test (arrival, first fight room, signature room), engine captures from `assets_dev` in
  `output/studio_cal/a7/s29/names/xd16/shots/`  (01-1_arrival.png, 02-2_fire_lake.png, 03-3_demon_shrine.png,
  04-4_magma_heart.png); all eight maps on one sheet `output/studio_cal/a7/s29/names/names_sheet.jpg`. Reads as named:
  the mouth's red rock, the fire lake with its causeway and the skull on its island, the demon skull's shrine with
  candles. The magma-heart shot is blocked by a demon at the landing (the room itself was seen in s28).

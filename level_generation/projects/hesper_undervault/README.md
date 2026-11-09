# Hesper: the Undervault (`hes_undervault.blv`)

The hub town, built to its [build document](../../../design/kreegan_world/zone1/dungeons/UNDERVAULT.md) the way MM7's
Stone City is: every house is a door in the walls of one great hall. Rooms, links, markers and lights are the `lh`
plan of `design/kreegan_world/zone1/dungeons/make_dungeon_plans.py`; the Stone City study it follows is
[`../hesper_lowhold_study`](../hesper_lowhold_study/).

## Build

```sh
(cd level_generation/projects/hesper_undervault && blender --background --factory-startup --python author_undervault_blender.py)
python3 level_generation/projects/hesper_undervault/build_undervault.py      # compile, scene, Lua -> runtime/worlds/hesper
python3 level_generation/projects/hesper_stage/stage.py                # install into the shared Hesper stage (id 9102)
```

- `author_undervault_blender.py` writes `source/`. Since the redesign (2026-10-21: the shops, the inn and the
  bounty board moved up to Landfall) it follows the plan's layout constants (`HALL_W`, `HALL_COLS`, `FACADE_X`,
  `LIFT_X`, `DEEP_X` and the rest in `make_dungeon_plans.py`):
  - the 6 400 × 4 800 hall in nine sectors under its barrel vault;
  - the Clinic's bay (its front one fitted picture cut round a recessed door, the sign plaque above);
  - the four end-wall façades with double doors;
  - the galleries with their parapets, pillars and 16-step stairs, and eight home doors;
  - the Chapel Steps and the Chapel;
  - the Kept Refuge, the Water Works and the Deep Stair to the D15 bulkhead;
  - the fountain, the four great pillars, two stalls, cloth banners, 89 decorations (the light fixtures among them).
- `build_undervault.py` compiles the BLV and writes the scene and Lua (handlers in `source/hes_undervault.handlers.lua`;
  the lift's destination is Starport Reach's `lift_arrival` from `out1_build.json`).
- Textures: the D0 Colonial set, the Hesperian interior set and the round-3 house fronts and doors
  (design/kreegan_world/art/textures_interiors, `hfr*`, `hfdoor*`, `hfrail`, `hcpillar`), and K3's root-lock
  bulkhead `htbulk` / `htbulkon` (design/kreegan_world/art/textures_k3_transit, CR-P3-03; the stage cooks these two
  keys of K3, `SURFACE_KEYS` in `hesper_stage/stage.py`).
- Links to maps not built yet: `build_undervault.py` fills the handlers' tokens from the other builds' records
  (out1's `lift_arrival`, D2's `water_works`, D15's `deep_stair` in `hesper_d15/source/hes_d15.semantic.json`, the
  Scour's `tunnel_arrival` in `hesper_out2/out2_build.json`) and writes a status text for a map whose record does not
  exist yet ("the way is not yet open"), as `hesper_out1`'s dungeon entries do. Rebuild the Undervault after D15 or
  the Scour is built.

## Look and test

```sh
./tools/run_game.sh --isolated undervault --world hesper --map hes_undervault.blv \
    --assets "$PWD/output/hesper_stage/assets_editor_dev" \
    --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_undervault/review_tour_01.yml" --seconds 0
```

`review/rebuild01/sheet.jpg` is the tour of the redesign (`review_tour_07.yml`); `review/build01/` and later
folders are the first build's. `lift_round_trip.yml` (run from `output/hesper_stage/scenario_run`) checks Warder
Halm at the Lift Gate (his The Guardian gives M3, 100203) and takes the lift up to Landfall's Lift Head (passes). The way down stays barred by the guards until D1, as designed, so reach the
Undervault with `--map`. `bulkhead_and_tunnel.yml` checks the bulkhead shut for a party without Grandmaster Hacking
and the Water Works door (barred before S2; after it the two ways, the tunnel's status text and the Pumping Station);
`bulkhead_open.yml` opens the bulkhead with a Grandmaster Hacker (map variable 1). Both pass (2026-10-23), with
`lift_round_trip.yml`, D2's `drain_and_water_works.yml` and the other Hesper scenarios of `rebuild_all.sh`.
`review_tour_bulkhead.yml` captures the bulkhead shut and open (the third shot opens it through the console:
`skill set Hacking 10 G`, `event 17`, then `reload map`); `review/bulkhead01/`. `review/settexture_20261023/` holds
the engine fix's before/after sheets (the bulkhead, D0's breakers, D1's board and breakers, MM7's Haunted Mansion).

## Status (2026-10-21)

Built: the whole plan, every house door bound to its event (the houses and their people since 2026-10-23, below), the
lift up, the Water Works door to D2 (open once S2 is done, QBit 100102 (event 16); `build_undervault.py` reads D2's `water_works`
arrival from `hesper_d02/source/hes_d02.semantic.json`; `hesper_stage/rebuild_all.sh` authors every map before
building any). The houses now use [Hesper backdrops](../../ui/hesper_house_backdrops/README.md) (2026-10-24; native
desktop capture pending). Not yet: the market's sound, the Sim
Hall's arena.

## The bulkhead and the tunnel (2026-10-23)

- **The Deep Stair bulkhead** (event 17, CR-P3-03 and CR-P3-14): its face is `htbulk` (cog 9017, `BULKHEAD_COG` in
  the author script, the semantic record's `cogs`). Without a Grandmaster Hacker (the party's best hacker,
  `evt.CheckSkill`): "An Ancient root lock. Nothing you know opens it." With one it opens: map variable 1 set, the face
  swapped to `htbulkon` (`evt.SetTexture`), which the load event (1) re-applies, so it stays open; then the move to
  D15's `deep_stair`, a status text until `hes_d15` is built.
  Since the engine fix of 2026-10-23 the swap shows at once when event 17 runs, and the engine loads `htbulkon` when
  the swap needs it (no face uses it), so the hidden `htbulkon` face that stood 8 behind the door face is gone (the
  map rebuilt and re-staged: 2 244 faces). D0's `hcmachon` and D1's `hcboardon` swaps work the same way. D15's way back is the new arrival
  **`deep_stair_bulkhead`** (492, −2 048, −1 024), a pace in front of the bulkhead facing east up the stair, in
  `source/hes_undervault.semantic.json` for D15's event 50.
- **The Water Works door after S2** (event 16, CR-P1-5): MM's travel question as a dialogue, NPC 9040 "The Water
  Works" (no portrait, `hesper_stage/npcs.yml`) with two topics, **Pumping Station** (9040: D2's `water_works`) and
  **Service tunnel** (9041: the Scour's `tunnel_arrival`, a status text until the Scour is built; the first use sets
  100420 and autonote 10102); leaving the dialogue is staying. The topics are this map's own events (`map_event` in
  `npcs.yml`: no global event; `build_undervault.py` registers them from there). Before S2 the door stays barred.
- **House ids** (the registry's 9450–9485): the Clinic 9452 to the Refuge 9457 are house rows
  (`hesper_stage/npcs_undervault.yml`), the Sim Hall 9204 (`hesper_stage/skills.yml`); the gallery homes (registry
  9472–9479, events 18–25) are not houses: their doors speak to their residents.

## The opening's people and doors (2026-10-23)

P4's CR-P4-14 and the integrator's follow-ups 18-19 (`design/kreegan_world/WORK_PACKAGES/requests/P4.md`):

- **Warder Halm** (NPC 9550, `hesper_stage/npcs.yml`), a Guard Sergeant (Hesper row 10068) posted at the Lift Gate
  beside the arrival (actor 0, `build_undervault.py`): The Guardian (M3 given for a party that skipped D1's relay)
  and The old town.
- **The Council's doors** (events 6 and 9-12: the Clinic, the Sim Hall, the Workshop, the Council, the Archive):
  before M3 (100003) the notice "Closed. A notice on the door: 'By the Council's custom, strangers are received after
  the Guardian has spoken for them.'"; from M3 the Sim Hall enters its house (9204, `hesper_stage/skills.yml`), the
  others name their house until the Undervault's house tables exist.
- **The Chapel** (event 13): Aster's talk (NPC 9500: her greeting, The shard, Who are you, The lander's parts, The
  Voice, The Hum) until her house (9456) exists. **The Kept Refuge** (event 14): closed until M6 (100006).
- The handlers of the moved shops (events 3, 4, 5, 7, 8) are gone: no face is bound to them.

## The houses and their people (2026-10-23)

The integrator's follow-ups 42, 43 and 36 (`design/kreegan_world/WORK_PACKAGES/requests/P4.md`), P4's texts
(`design/kreegan_world/quests/dialogue/UNDERVAULT.md`, `NPCS.md`, the news in `LANDFALL.md`, Pell's lines in
`READABLES.md`). The people, their topics and the house rows are `hesper_stage/npcs_undervault.yml`, written by
[`gen_npcs_undervault.py`](gen_npcs_undervault.py) (edit the script, then run it and the stage).

| Event | House | People (npc.txt 2D location, or moved in by the door) | Hours |
|---|---|---|---|
| 6 | The Clinic 9452 | Neve 9512 (9734, 9735); Doctor Ilse 9503 from M6 (9680, 9681 S4) | 8–20 |
| 9 | The Sim Hall 9204 | Brannoc 9504 (9685, 9686 S8 given) | always |
| 10 | The Workshop 9453 | Orrin 9511 (9731) | 8–20 |
| 11 | The Council Hall 9454 | Elder Maren 9501 (9660, 9661 M5, 9662 M6) | 8–20 |
| 12 | The Archive 9455 | Pell 9505 (9690, 9691 M14b, 9692, 9694 S9, 9695 after 100301) | 8–20 |
| 13 | The Guardian's Chapel 9456, a temple (MM's Donate lowers the reputation) | Aster 9500 (`npcs.yml`), Iver 9223 (Grandmaster Hacking from two shards, `skills.yml`) | always |
| 14 | The Kept Refuge 9457, from M6 | Tamsin 9502 (9670–9673), Hob 9574, Dree 9575; Cale, Senna, Rook, Tibb (9576–9579) from camps 1–4 (100115–100118) | always |

- The Council's doors keep the notice before M3 (CR-P4-14); the Chapel is open from the first visit.
- **Odo** (9506, row 10073, actor 1, group 1) stands by the Water Works arch, invisible until M2: the load event
  (handler 1) clears group 1's Invisible bit once 100002 is set. His Pressure (9700) gives and closes S2.
- **The gallery homes:** event 18 Pim (9551), 19 Sabra (9552), each after its home's status line; 20–25 Kobb, Lissa,
  Mott, Nara, Oswin, Rhosa (9568–9573). **The hall's street people** 9553–9567 are wandering villager actors 2–16
  (`STREET_SPOTS` in `build_undervault.py`), faces `hes_townsfolk_1`–`8` and NPCS' street pool. Each street person and
  resident carries two News topics (`npcs.yml` 9771–9790): the opening item in turn and the later item in turn. They
  have one short greeting each from P4 (UNDERVAULT, "Street people and home residents: greetings";
  `STREET_GREETINGS` in `gen_npcs_undervault.py`).
- Hand-ins: Maren's M5 and M6, Ilse's S4, Pell's S9 and Odo's S2 lower the reputation by 1 (REPUTATION.md,
  `AddValue(ReputationInCurrentLocation, -1)`). Ilse counts the Glassback Hearts with `PlayerItemCount` (an
  `IsAtLeast` on an inventory item only checks presence).
- **Not staged, so commented out in their topics:** Tamsin's Combat Reflex II (11211), Ilse's Ablative Lattice II
  (11205) and Pell's Last Light of Hesper (11428) (the implants wait for an implant slot); tablets IV–XII are not
  placed yet. The freed Kept are not hirelings yet (npc.txt's join column; P4 asks for the inn's hireling rules).
- **Left:** the Sim Hall's arena (S8: the three ranks' waves, 100121–100123, their prizes, 100108): it needs an arena
  room or map (MM7's arena is its own map with summoning topics) and the Scour's and the Crown's monsters, none staged.
  Brannoc's The Ranks gives S8 (100228, autonote 10416) and answers by the rank bits.

Check: [`houses_and_people.yml`](houses_and_people.yml) (headless: the party faces each door and interacts).


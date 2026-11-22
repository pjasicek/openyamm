# Xeen: orchestrator handoff

> **2026-11-21:** a newer handoff exists — start from [HANDOFF_ORCHESTRATOR4.md](HANDOFF_ORCHESTRATOR4.md). This file's §1, §2 and §5 still hold; §3–§4 are superseded.

Written 2026-11-20 by the first orchestrator session (`openyamm-c3`); rewritten at 23:10 the same day by the second
(`openyamm-66`) for the third. Read this file
first, then [ROADMAP.md](ROADMAP.md), [STATUS.md](STATUS.md), [DECISIONS.md](DECISIONS.md),
[lanes/README.md](lanes/README.md) and every lane file in [lanes/](lanes/). Every lane was stopped at a clean
checkpoint for this handover; each lane file's State says exactly where it stands and what comes next.

## 1. What the program is

The user asked (2026-11-20) for the whole World of Xeen as an OpenYAMM world at MM6/MM7 quality: 82 maps, its own
monsters, items, towns, NPCs, teachers, quests, travel, Town Portal, presentation. ROADMAP.md is the plan; this
session ran it as the orchestrator with eight lanes and a 3D lane:

| Lane | Owns |
| --- | --- |
| A1 platform | engine, game, Map Studio, the `build-xeen/` trees, regressions |
| A2 data | monsters, items, treasure, the generator `tools/xeen/build_world.py`, `balance.py` |
| A3 story | quests, quest and story topics, world Lua, the playthrough chain |
| A4 towns | houses, residents, teachers, vendors, transport, Town Portal, portraits, flavour topics |
| A5 outdoor 1 | X1–X4, D3, X6, X7 (built); next X9, XD-17, P5; unseals its maps' dungeon doors |
| A6 outdoor 2 + art | art direction, kits, texture registry (`source/textures.yml`), skies, terrain materials; X5, X8, D1, D2, D4 (built); next D5–D7, P1–P4 |
| A7 dungeons 1 | XD-01–05, -07, -08, -13–15, -20, -22–26, DD-06, -07, -11A–C, -13, -23 (built); phase 5 XD-16, -19, DD-16, -24 |
| A8 dungeons 2 | XD-06, -09–12, -21, -27, DD-01–04, -09, -10A/B, -18 (built); DD-05, -12, -14, -19, -20 (now); later DD-08, -10C, -15, -17, -21, -25 … |
| S 3D | new creatures, colour tiers, quest-item and decoration models |
| AU audio | ElevenLabs sounds (added 2026-11-20 by the second orchestrator at the user's word): monster, event and ambient sounds, optional voice lines; `devdocs/xeen/AUDIO.md`, `level_generation/sounds/xeen_20261120/` |

The world package is `assets_dev/worlds/xeen/` (git-ignored; its model sources sit in `assets_source/worlds/xeen/`,
kept out of the submodule's git status by its local `.git/info/exclude`). Briefs are in `devdocs/xeen/briefs/`
(tracked), work files in `output/studio_cal/<map>/`.

## 2. How to run it

- **Lanes are background agents** (Agent tool, general-purpose, run_in_background). A lane session lasts roughly
  300–600k tokens; when its report says the context is long, start a fresh session for that lane. Its brief: "You are
  the Xeen lane <X>, <n>th session … read lanes/README.md, lanes/<X>.md, DECISIONS.md, ROADMAP §…, STATUS.md … then
  the work, in order: … Report in the README's DONE/STATE/REQUESTS/DECIDE/USER/NEXT shape." The briefs this session
  used are good models; the lane file holds everything else.
- **Relaying.** Lanes never talk to each other; every REQUEST in a report goes to its owner with SendMessage (a
  running agent receives it at its next step; a stopped one is resumed by the message). Keep STATUS.md current
  (you own it, `world.yml`, `source/maps.yml`, ROADMAP, DECISIONS).
- **Design questions never go to the user** (the user's instruction of 2026-11-20). Each `DECIDE:` item, and every
  mock-up approval before geometry, goes to a **new Opus decider agent** (`model: opus`), read-only, with a
  self-contained brief: the question and evidence, the documents to read, the constraints, what each option costs,
  and the answer shape (DECISION, WHY, WHO ACTS, REVERSIBLE). Record each answer in DECISIONS.md (D-n) and relay it.
  See D-15 to D-46 as examples. Gates that go to a decider, never the user: each outdoor map's L1 mock-ups (MU-2/3,
  e.g. D-31, D-36, D-40), each dungeon's MU-6 graph (D-25–D-27, D-39, D-42), every lane DECIDE item, and engine-scope
  questions (D-41, D-44). A decider gets the lane's NOTES/graph page, the relevant D-n precedents and the rules files; it
  may look at images; it edits nothing.
- **What still goes to the user:** results to play at the gates; commits (never stage or commit); any new kind of
  spending. Density changes are not held for the user (the user, 2026-11-20: "don't we have the decider logic in
  place?"): a decider settles them, the count and clustering table goes on the gate's review page, and the install
  goes ahead. More generally, nothing a decider has settled waits on the user.
- **Only A1 builds**, at merge points, into `build-xeen/` and `openyamm-studio/build-xeen/`. Lanes run
  `build-xeen/game/openyamm` (or set `OPENYAMM_GAME_BINARY` for the run wrappers).
- **The generator** `tools/xeen/build_world.py` has a write lock and `--only <module>`; lanes write their own module;
  a full write only when `--check` is clean everywhere.

## 3. Where it stands (2026-11-20 23:10, second handover)

**Maps in the world (installed with bakes, tested from `assets_dev`):** 50 of 82, plus XD-20 installed (tested only
in a scratch root until A2's row 9121 lands).
- Outdoor: X1–X8, D1–D4 (every outdoor map of phases 0–4; X7 is phase 5 but installed).
- Cloudside dungeons: XD-01 to XD-15, XD-21 to XD-27 (all but XD-16–XD-20).
- Darkside dungeons: DD-01, DD-02, DD-03, DD-04, DD-06, DD-07, DD-09, DD-10A, DD-10B, DD-11A–C, DD-13, DD-18, DD-23.
- Not yet built: X9, D5, D6, D7, P1–P5, XD-16 to XD-19, DD-05, DD-08, DD-10C (geometry in A8's scratch, phase 5 with
  D6), DD-12, DD-14, DD-15, DD-16, DD-17, DD-19, DD-20, DD-21, DD-22, DD-24, DD-25, DD-26, FD-01 to FD-04.
- In progress at the handover: **DD-05, DD-20** (built, not installed), **DD-12, DD-14, DD-19** (A8's phase 4, D-42; rows 9154/9173/9165/9167/9172 already written by A2, qbit blocks
  registered by A3, textures registered by A6), phase-5 MU-6 graphs (A7: XD-19, DD-16, DD-24 drawn; XD-16 and the
  collecting page still to do).
- Every installed map: audit 0 errors (dressing D-7/D-14, lights MP14, doors MP15, texture fit MP16 with D-41's storey
  rule), playtests 4/4 (dungeons) or walk/hostility 2/2 (outdoor), `stale_bakes.py` 0 at the handover (DD-02/DD-03 re-baked on
  `xkmirror` v2; their tours and 4/4 rerun are queued in `output/studio_cal/a8_s8/queue_polish1.sh`).

**Engine:** game binary merge point 18 (22:38:19), studio `oymap` merge point 19 (23:02:35), merge point 20 parked
unbuilt in the source tree (E9, rim glow fix; §4 item 1); STATUS.md's Engine
section lists every merge point. Still to come from A1: E9 outdoor ambient emitters (AU's six outdoor beds and X6's
sand-fall loop wait on it), the rim glow drawn over the horizon cloud bank (then A6 sets `below_deg` 1–2, D-36).

**Story:** the playthrough chain passes a new game to segment 55 (Q-D7 gem mines, Q-D19, M19 stage 2), normally and
with `--reload` (25–55); 11 quest stubs; `quests.py` 0 errors except bits waiting on unbuilt maps. Next: segment 57
(Act IV main line as DD-12 and DD-14 land).

**Balance (A2, STATUS.md Balance section):** Act I 1.15 (X7's south trimmed), Act II 1.08, Act III 1.02, Act IV
installed 1.03 and projected 1.04 over every Act IV map, X7 Act V 0.99.

**Content:** 294 monster descriptors on 72 models (D-44: Xeen depends on engine, mm6, mm7, mm8 — never mm9); 424 NPC
portraits; 141 of 450 new textures; 227 ElevenLabs sounds (AU: 19.9k credits charged, 67.7k committed of the 100k
budget) including D-38's nine voiced sounds; Meshy lane total about 265 credits (≤30 per creature, approved per creature).

**Decisions:** D-1 to D-46 in DECISIONS.md. The next decider is **D-47**. Long answers are kept beside the row:
`mockups/act3_a7_decisions.md` (D-25), `act3_a8_decisions_a.md`/`_b.md` (D-26/27), `act4_a7_decisions.md` (D-39),
`act4_a8_decisions.md` (D-42), `briefs/x7/L1/D40_DECISION.md` (D-40). Pattern: save the decider's whole answer to such a
file (the agent's final text), append a one-row summary to DECISIONS.md, edit MAPS/ROADMAP rows it names, then relay.

## 4. Restarting the lanes

The agent ids of this session cannot be resumed from a new session: start every lane **fresh** from its lane file
(each lane was asked to stop at a clean checkpoint and write its State; if a lane file's State predates 23:00, check the
lane's last report in this file's §4.2 and in STATUS.md). Start them in this order, at most about eight agents at once
(memory: §5):

1. **A1** (17th session): A1 parked **merge point 20** unbuilt (session end): E9 outdoor ambient sounds (game
   `ambient_sounds` in outdoor scenes, `OutdoorWorldRuntime::ambientSounds()`; studio sketch `sounds` list) and the rim
   glow lighting the horizon cloud banks (`fs_sky.sc`) are in the source tree. Finish per A1.md State
   (`output/xeen_a1/mp19/build.sh`, the in-game E9 check `output/xeen_a1/arena/e9.yml`, full studio tests, regression
   set, release), then tell A6 (`below_deg` 1–2 and captures), AU (outdoor beds), A5 (X6's sand-fall loop). Then the D4
   frame cost at view_distance 1.0 vs 1.6 on a quiet machine, then DD-13's studio words.
2. **A8** (9th): per A8.md State: run `output/studio_cal/a8_s8/queue_polish1.sh` (tours and 4/4 for DD-02, DD-03,
   XD-27 after their re-bakes); resume **DD-05** (built, audit 0, not installed; `playtest.yml` fails at step 68: a
   cell's question fires mid-walk) and **DD-20** (built, audit 0, no playtests yet) from their NOTES "State and next
   steps", install each with its bake, 4/4; then DD-12, DD-14, DD-19 (briefs in `output/studio_cal/a8_s8/`), two
   sub-agents at a time; reinstall the maps that use the lift trap word; polish (DD-09, XD-10, XD-12's dark roof).
3. **A7** (12th): XD-20 is built and installed with its bake (12/12 in the scratch root `output/studio_cal/a7/root_s6`
   with a test row; from assets_dev after A2's row 9121 and A5's X6 door). Next per A7.md: XD-01 back to ≤ 46 textures;
   XD-16's graph and the page `mockups/act5_dungeon_graphs_a7.md` from the three notes files in
   `mockups/act5_graphs/` (XD-19, DD-16, DD-24 drawn; 20 DECIDE items listed there) → a decider (D-47); XD-20 4/4 from
   assets_dev, then drop `root_s6`'s test row.
4. **A5** (13th): X7's crag is basalt now (installed 23:13 with bake, walk/hostility 2/2; not yet looked at in game).
   Next per A5.md: shoot the crag (`output/studio_cal/a6/x7mat/run.sh s12 assets_dev`, shots 01–02), X1/X4 walk asserts
   for the X7 edge points (no reinstall), D3's signature with the rim glow; place XD-16's idols on X7 (§4.1); unseal
   doors as dungeons install (X6: XD-20, FD-02; D3: DD-19; X7: XD-16/17/18, FD-04); then phase 5 (X9, XD-17).
5. **A6** (12th): rim glow `below_deg` after A1; D4 rebuild when DD-12/14/20 install (doors go live by name); then
   phase 5 outdoor (D5, D6) mock-ups (L1) → decider.
6. **S** (7th): sand worm, XD-16's idols (decorations 4008/4009) and D-44's mummy move are done (Meshy lane total 290).
   Resume the **armadillo** from its README's "Resume here" (`level_generation/creatures/xeen_armadillo_claude/`: UV
   quality check, 4K retexture 10 cr, clips, tiers, LODs, install, bind `Xeen Sand Worm B`), then the octopod (origin at
   the water surface, D-36), `xeen_guard` (D-19), the Northern Sphinx (+ buried Southern) for X6.
7. **A2, A3, A4, AU** are stopped with nothing urgent: start them when relays arrive (A2: rows for each new map and
   recounts; A3: segment 57, `m33.sundial_nine` 111663 has no setter yet; A4: each installed town map's loop; AU: the
   outdoor beds and the desert/Darkside revisit once E9 lands, Sheltem's set if he gets a monster row).

### 4.1 Pending relays at the handover

- A2: XD-20 map row 9121 (encounter 0, no slots, STONEROOM, music 45) — XD-20 is installed and cannot load from
  assets_dev without it; phase-5 rows wait on the decider (XD-19 elemental tiers 11624–11626, Slayer Sword undroppable;
  DD-16/24 peaceful Corak, "People" giants, giant height ~300; Act V recount).
- A5: open X6's `door:xd20` to `entrance:x6_yard` (256, 0) facing east, after A2's row 9121.
- A6/A3/A1/S/AU: A7's phase-5 requests (arrivals `entrance:d6_hatch`, `entrance:d5_hold`; textures; hook texts; a
  damage hook for Lord Xeen's Slayer-Sword immunity; `xeen_guard`, elemental tiers, Corak's look; optional sounds) wait
  on the phase-5 decider's answer: relay them with it.

- A6: D1's `door:dd05_rope` → `arrival: entrance:d1_rope` (1376, 1472, 1920, facing south) and `door:dd05_front` →
  `entrance:d1_door` (0, -1536, 0, facing north), once DD-05 is installed. DD-20's inside arrivals for D4:
  `entrance:d4_guild` (-640, -384, 0) facing 512, `entrance:d4_trapdoor` (3456, -640, -512) facing 0,
  `entrance:d4_shaft` (14208, -1152, -512) facing 1024.
- A3: DD-05's fountains say "The water is cool and refreshing." on a second drink (not "You have had your fill."); register
  DD-05's map qbits 117361 `humble_slain`, 117362 `pious_slain`.
- A2: A8's slot lines match the cards (DD-05 heretics tier 0 [2,3] w75 + tier 1 [1,2] w25; DD-20 stalkers tier 5 [2,3]
  w100; encounter 10).
- A1: a placed monster cannot run a click event (A8 uses a cell's entry and the bed instead in DD-05): a studio/runtime
  word, after merge point 20.

- A2: Sand Worm A 11440 / Great Worm C 11442 now bind `xeen_sandworm.glb` (stands 127 / 146; the rows say 160 / 190;
  mound radius 130 / 149): fix collision heights and radius.
- A5: place XD-16's idols on X7 in place of L3's blockout buildings — `decoration_list_id` 4007 (demon, north spot
  ~[65.1, 43.75]) and 4008 (devil, south ~[65.1, 45.45]), facing 90 (west), origin the plinth's bottom centre (z at
  the ground, sink 10–20 on a slope); the devil's wings reach ±282 north–south: keep its centre ≥ ~350 from the
  mouth's edge, the demon's ≥ ~250.
- A3: the demon idol's eye sockets are empty, to fit `x7.idols`' "their skulls are not here".

- A7 (FD-02, phase 6): place Picard 5704 in the Home of the Aged behind m40's `stair` hook door.
- A7/A8 (phase 5): D-38's voiced lines — XD-19 calls `m35.lord_xeen_sight` once at first sight and `m35.lord_xeen` at
  his death (A7); Sheltem's door line and the confrontation in DD-17 (A8).
- A6: register `xosoot` (D-33) when A7 makes it.
- S (queue): the Northern Sphinx model (+ buried Southern) for X6 (A5).
- A5: D3's `sandcaster_stables` in the fenced yard with `building:sc_stables` (tell A4).
- A3: `m33.sundial_nine` (111663) has no setter: find whose map writes it.
- A6/A8: D4's DD-12/14/20 doors go live on D4's rebuild after A8 installs them.

### 4.2 Lane reports still arriving at the handover

Every lane reported its stop (A1, A5, A7, A8, S) and is folded into §4; nothing was left mid-install. Each lane file's
State is still the authority; read it before starting the lane.

### 4.3 For the user (gate play, not design)

- Ferry price on Lakeside: a one-day trip costs 250 gold (Val 5; Lakeside Yachts and Tern's ferry back).
- Listen: the voiced lines (`level_generation/sounds/xeen_20261120/review/index.html`, group "Voices: lines"; Sheltem's
  near-whisper with a machine flutter, Lord Xeen's 2 s laugh), the declipped `xeen_pyramid_travel`, harpy and lizard
  deaths, batch 2's hornet buzz and snake men.
- Look: the sand worm in the X6 desert once placed (it reads brownish in XD-21's dim light), XD-16's idols on X7;
  X7's signature and lava island (`output/studio_cal/x7/tour/t3/`), D4's jetty view by day and night
  (`output/studio_cal/d4/pics/sheet_s11.jpg`), the rim glow sheets (`output/studio_cal/a6/rim/`), the new creatures
  (mantis, sabertooth, Snow Beast, electrapede, scorpion) in their maps.
- Commits: nothing is staged; the user commits.

## 5. Lessons from this session

- Hard-link copies of `assets_dev` share inodes: never write into a file of a hard-link scratch root (A1 once
  overwrote a world table that way).
- Shared terrain files (`terrain_materials/liquid_edges`) must be regenerated into a temp folder and swapped, and
  announced first (X1 failed to load once mid-run).
- Install a map before baking it, never after: X2 refused to load once ("lighting cooked for different geometry").
- Every map lane runs `oymap audit --world xeen` (dressing included) before calling a map done.
- A lane's sub-agent must never delete files it did not create (a portrait sub-agent once did).
- Lanes stop and report when blocked rather than waiting idle; resume them with the relayed answer.
- Memory (2026-11-20, second orchestrator): systemd-oomd killed the user's GNOME Shell at 17:35 while other sessions ran
  `-j25`/`-j32` builds, several game runs went on and /tmp (a RAM-backed tmpfs) held 40 GB of old Claude scratchpads.
  A1 builds `build-xeen` with -j12 and never beside another build; lanes keep scratch output on disk (`output/`), not in
  /tmp or the session scratchpad; old session scratchpads under /tmp/claude-1000 are cleaned when /tmp grows.
- Engine table rows shared with other worlds (A1's lava rows in MM7's tile table) stale every bake that hashes the
  table: check `stale_bakes.py` after any engine table change; `tools/lighting/refresh_tile_table_dependency.py`
  refreshes a bake's recorded hash only after proving its rows and tile sets are untouched.
- A world.yml table contribution whose file does not exist yet breaks the world's load: add the line only after the
  owning lane has written the file, then run `--headless-validate-actor-models` and the first playthrough segment.
- Agents waiting on helpers send many "still waiting" stops; tell them to wait quietly and report once.
- A lane relaying a texture or table change that stales another lane's bakes must name the stale maps to their owner.
- Keep the agent-id list and pending relays in a durable file, not the session scratchpad (a reboot clears /tmp).


# Xeen: handoff to the fourth orchestrator (2026-11-21, ~17:00)

The third orchestrator stops here because of usage limits. Read this file first, then
[HANDOFF_ORCHESTRATOR.md](HANDOFF_ORCHESTRATOR.md) §1, §2 and §5 (what the program is, how to run it, lessons; its §3–§4 are
superseded by this file), [ORCHESTRATOR_SESSION3.md](ORCHESTRATOR_SESSION3.md) (the full record: agents table, deciders, relays, log)
and [STATUS.md](STATUS.md).

## 1. Where it stands

- **All 82 maps are installed, every door between them is open, 0 stale lighting bakes.** Every placed monster and NPC has a 3D body
  (335 descriptors on 83 models, 0 refused); 18 new creature projects; tier colours match their names (S session 12).
- **Engine:** merge points 4–34 released (game `build-xeen/game/openyamm`, studio `openyamm-studio/build-xeen/oymap`); merge point 35
  was in progress at the handover (see §3). Merge points 31, 33 and 34 changed MM6–MM9 behaviour (hidden monsters in kill checks;
  magical age survives rest; shops keep to their loot pools) — all accepted by the Reviewer.
- **Balance:** every act within 1.02–1.15 of its kill-XP budget; quest XP under every trigger; 17 stat gates reachable; 35 temporary
  sources daily-guarded (D-70); A2's shop check found nothing to raise.
- **Tests (MM9-style, not in CI):**
  - Main campaign `tests/playthrough/xeen/`: segments 01–99, M1–M42, a new game to the ending; passes normal and `--reload` on merge
    points 33/34 (A3 30th). A3 31st was adding D-82's end-of-segment health checks and rerunning.
  - Promotions `tests/playthrough/xeen/promotions/`: 41 segments, class table 24/24; passed both modes on the 14:00 checkpoints; A3-promo
    5th was refreshing on A3 30th's rewritten checkpoints.
  - Side quests `tests/scenarios/xeen/side_quests/`: 70 scenarios, all pass both modes on merge point 33.
- **Guide:** published at https://jasicek.net/openyamm/xeen-guide/ (lane G, `tools/xeen_site/`, deploy `tools/xeen_site/deploy.sh`;
  SSH/sudo work without a password). Current with D-76, D-79, D-80, A3's 44 answers and all 286 recaptured portraits. The MM9 guide is
  unchanged (shared front end `tools/mm9_site/web/`; G checks MM9's `data/guide.js` is byte-identical on every rebuild).
- **Review:** the Reviewer decided all 78 review rows (`reviews/G3_REVIEW_20261121.md`: 73 accepted, 5 needed work); the five fixes were
  being made by A6, A7, A8 and S at the handover.
- **Decisions:** DECISIONS.md runs to **D-82**; the next number is **D-83**. User decisions: U-1 (no new item art), U-2 (early
  Grandmasters fine), U-3 (new-game cards: Xeen first, marked Experimental).

## 2. Standing rules (unchanged; from the user and the handoffs)

- Lanes are background agents (general-purpose); a session lasts ~200–350k tokens; start a fresh one when a lane's context grows long.
  Each lane keeps its State/Next/Log in `devdocs/xeen/lanes/<lane>.md` — the brief's first read.
- **Design questions never go to the user**: each DECIDE goes to a new Opus decider agent (read-only, self-contained brief, answer shape
  DECISION / WHY / WHO ACTS / REVERSIBLE + a SUMMARY ROW), saved under `devdocs/xeen/reviews/` or `mockups/`, recorded in DECISIONS.md,
  relayed. Review rows ("look at this in game") go to a **Reviewer** agent (the user's request, 2026-11-21), not the user.
- What goes to the user: commits (never stage or commit), new kinds of spending, and items for the **MM9 guide owner** (theirs).
- Only A1 builds (`build-xeen/`, -j12, never beside another build). Install before bake. Scratch under `output/`, never /tmp.
  Game runs `--isolated`, minimised, at most two per lane; wait on exact PIDs. Never delete others' files.
- World files `world.yml` and `source/maps.yml` are the orchestrator's (world.yml edits under
  `flock output/studio_cal/a5/locks/terrain.lock`). QUESTS.md / MAPS.md / MONSTERS_AND_ITEMS.md text edits are the orchestrator's.
- Spending: Meshy within the program's approval (lane total 330 credits); **ElevenLabs: the user lifted the cap** ("use however much you
  need, if it makes sense"); AU's job budget is 140,000 (37,791 charged, 132,950 committed).
- Sub-agents of lanes: at most two, and they may not fork further (lane G's first session forked five).
- Agent ownership of the three A3 test sets: A3 main = `m*.yml` and the main chain; A3-side = `q-*/q-f*` quest files and side-quest
  scenarios; A3-promo = `t1-*/t2-*`, `Xeen.Promotions` and the promotion chain. Each regenerates (`build_world.py --only gen_quests`)
  only when `--check` shows nothing but its own change.

## 3. Sessions at the handover

All were told at ~17:00 to finish at a safe checkpoint, update their lane file and report. **Read each lane file's State/Next before
starting its next session**; the reports that arrived after this file was written are summarised in ORCHESTRATOR_SESSION3.md's Log.

| Lane | Session | Was doing |
| --- | --- | --- |
| A1 | 31st | **reported, stopped — merge point 35 released** (game 16:34:21, copied 16:43:29; oymap 12:46:47): loader takes `clear_hostiles: {radius, height, min}` and `walk_to` `clear_height`; a waiting given item is the party's and saved (**save version 199**; older saves load with none — shared MM6–MM9, nothing waits in MM6–MM8); D-82 point 1 (PARTY DOWN for `playthrough`/`side_quest` tags — **not yet run against the chains**: 93 Xeen + 96 MM9 playthrough files, 70 Xeen + 16 MM9 side quests carry the tags); Garrote Gorge regression. Release script: `bash output/xeen_a1/mp28/release_game.sh`. Open: the headless `app` case (next: gdb on `GameplayScreenRuntime::triggerPortraitFaceAnimation`) |
| A3 | 31st | **reported, stopped**: D-82 check is in `run.py` (shared by the promotion chain) + PLAYBOOK bullet; ending OK (the Return key closing the ceremony also toggled turn-based: minor input leak → A1); D2 Petrify not reproduced, no load cause (likelier DD-14's Gargoyle Overlords). **Checkpoints NOT rewritten** (still session 30's). The chain with the check will fail at 61 (Gargoyle Sentinels paralyse on DD-14's south-west tower top, step 106, no clear). Next (A3.md session 31, Next item 0): clears on 61's and 67's DD-14 walks, then the whole chain both modes (rewrites checkpoints → tell A3-promo), then 77's keys after MP35 |
| A3-promo | 5th | **reported, stopped**: 41/41 normal and `--reload` on A3 30th's checkpoints (merge point 34); D-77 tags; segment 21 asserts the Clan Master alive; 35 and 89 fixed for storey clears. D-82 not started — but A3 31st put D-82's end check into the shared `tests/playthrough/xeen/run.py`, which `promotions/run.py` calls: expect PARTY DOWN where a start checkpoint from 61–81 has Paralyzed members until the main chain's checkpoints are rewritten (A3's next session) |
| A6 | 28th | **reported, stopped — nothing installed**: Olympus' dressing (MM8 temple marble kit, gilt trim, pilasters, cornices, parapets, a columned temple, column gates) built in scratch (`output/studio_cal/d7/tools/gen.py.s28_wip`; 63 coplanar warnings to fix before install); P1 battered crater walls and a molten vent at the heat column built in scratch (`output/studio_cal/p1/tools/gen.py`, `PROGRESS.md`). Resume steps in A6.md Next 1–2. Preview: `output/studio_cal/a6/s28/d7/sheet_before_vs_wip.jpg` |
| A7 | 24th | **reported, stopped**: FD-02 thin edged blades (installed with bake, 20/20, audit 0/0); XD-05's line no longer names Gunther (Lua-only, 12/12); XD-22 Clan Master item closed; placed names were already in (XD-01/03/04/05). **Open: XD-19's ceilings still pale** — moving the fill lights didn't help (bounce off the pale vault texture `gnecclg2`); next: a map-only bake profile `tools/lighting/baked_indoors/profiles/xeen_xd19.yml` (`bounce_scale` ~2.5 and/or `max_lighting` 1.0), else a darker vault texture; also XD-19's audit warning on event 61 (cinematic cue bound to nothing) |
| A8 | 23rd | **reported, stopped**: DD-02 dimmer (profile 0.9/0.9/0.45) + `pan: false`; FD-01 textured levers + black-stone pyramid; DD-10C cold nest (frost, ice, blue light); XD-12 re-shot; DD-14 Queen faces her cell — all installed, baked (DD-14 rebaked 16:43), 4/4, audit 0. **Open: DD-14's main playtest fails 4/4 at step 115** (the walk west through the Count's hall sticks at (-231, 2766)) — also on the 06:34 map, so it predates the Queen edit; likely merge point 33's storey-bound clears (A3 30th found a Royal Vampire barring the Count's hall in segment 61): fight the hall or add `clear_hostiles: {height}` (MP35 keys) in the playtest. Sheets `output/studio_cal/a8_s23/shots/check_all.jpg` |
| S | 13th | **reported, stopped**: Hell Hornet (lighter crimson, ember wings), Guardian of Air (gold), Power/Skeletal Lich own skins on `xeen_lch` — installed, 0 refused. Optional heart jar glass and P2 basket built but **not installed** (resume steps in each project's README, "Session 13") |

Stopped and idle: A2 (21st), A4 (16th), A5 (25th), A3-side (2nd), G (4th), AU (5th), Reviewer (1st).

## 3b. State at the final check (~17:15)

All sessions stopped; no game or build process running. `tools/lighting/stale_bakes.py --check`: **0 stale bakes**.
`tools/xeen/build_world.py --check`: **0 differ**. The released binaries: game 16:34:21 (merge point 35), studio 12:43:03.

## 4. Open work (de-duplicated; once the sessions above report, drop what they finished)

**Follow-ups of the in-flight work**
- MP35 is out: A3 switches segment 77's Lua clears to the YAML keys; A3, A3-promo and A3-side rerun their sets on MP35 — the PARTY DOWN runner check fires for the first time there. **The MM9 chains also carry the `playthrough`/`side_quest` tags** (96 + 16 files): run MM9's main chain once on MP35 to see whether the check trips there (the user's MM9 program; report results to the user).
- D-82 point 2/5 note: A3 31st already added the end-of-segment PARTY check and report section to `tests/playthrough/xeen/run.py` (A1 thought it was open); confirm and don't redo it.
- D-82 (`reviews/D82_DECISION.md`): A3-promo — end-of-segment check + PARTY report in `promotions/run.py`, per-member asserts before
  hand-ins and class rounds; A3-side — end-condition logs, per-member asserts, the `side_quest` tag; A1 — the D2 case if A3's bisect
  shows a load cause.
- G recaptures the portraits of 11350 (Hell Hornet), 11702 (Guardian of Air), 11284 (Power Lich), 11285 (Skeletal Lich) and republishes (S 13th done).
- S next: finish and install the heart jar and the P2 basket (winding, in-game check); P1's ember disc if A6 asks.
- A7 fixed XD-05's line (16:35): G drops its drums clause and the Q-C22/Q-C9 texts (below), then republishes.

**A3-side**: Q-C9 scenario (lines 284–291) needs two clicks on X6 event 81 (A5 made the Sphinx door two clicks: the first shows the amulet
line and stays, the second enters XD-15) and drop its stale ISSUE comment; Q-C22 asserts a second knock enters house 4647; `q-c9.yml`'s door
`where` → "the map shows this line and stays; the next click enters"; a scenario for Q-D10's mercenary route.
**A3 (main)**: segment 49's comment about Snog/Alicia hidden on reload looks stale. **A3-promo**: `63_hobstadt_tribute.yml` comment still
quotes "Troll Hole. Descend?".
**G**: Q-C9 text ("click the door with the amulet, then click again"); Q-C22 drop the first-visit hint; optional: frame the dragons a
little tighter.
**A2**: `source/monsters.yml` model/skin records for S session 12's families (records only); D-81 — `balance.py` promotion-path gem rows
count fixed choices (`alternative: true` gives; Q-C25 row 36 + one Q-D27 wish = +1); E14 `placed_names:` (ids 401–499: Mr Wobbles, Mrs
Wobbles, Gong Sentry, Schoolmistress, Goblin Warden, Orc Shaman, Tam) — then A7 uses `name:`.
**A5**: X3's sundials and ranger camp, X4/X9's typed prompts → Yes/No buttons at their next rebuild (D-72).
**A8**: rooms in `output/xeen_a1/mp31/room_step_tops.txt` (DD-05, DD-10B, DD-15, XD-06, XD-09, XD-12, XD-21) — check playtests at their
next rebuild; optional DD-12 cage recess.
**AU**: update AUDIO.md (all session-5 lines pasted; the still-panned list cleared).
**A1**: Return closing a text window (the ending ceremony) also reaches the Combat key and toggles turn-based mode (repro `output/a3_s25/p5_ending/tour.yml` vs `output/a3_s31/ending/tour.yml`); the headless `app` case `app_npc_granted_item_enters_held_cursor_slot` (if MP35 didn't close it).
**Decider batch (next D-83)**: A5's two-click Sphinx door (X6 event 81) vs showing the line after arrival in XD-15 — A5's choice, cheap to
undo.
**Optional**: A6 — D1's Yog dies with the Sardaj on the war route (fits his line; change only if he should survive). A5 + A8 — D-42 (4)'s
DD-19 return point on D3 (-10496, 22150, 1728) facing south.

## 5. For the user

- **Commits:** nothing is staged or committed.
- **MM9 guide owner (the user's):** darkpassageway's Gemstone angles and Floor plates order in `tools/mm9_site/extra_pois.yml` (D-79);
  isleofashes a14 shows "special_passage"; `tools/mm9_site/capture_monsters.py` has the same pitch fault G fixed for Xeen; the shared
  `quest_levels` tie-break is unstable (changing it may change MM9's output).
- **MAW:** Xeen isn't offered under MAW yet (a later phase); say if it's wanted sooner.
- Before a release: rerun all three test sets on the final binary, run `tools/lighting/stale_bakes.py`, and A1's release steps
  (`packaging/RELEASE.md`).

## 6. Lessons from the third session

- Agents report "waiting" many times; don't answer each with work — record, and act when the real report arrives. If a session goes quiet
  for long with no game process running, check its output file's time and its lane log; it may have stalled on a lost notification
  (A3 26th did) — read its log and start a fresh session.
- A shared-engine fix often shows up first as a Xeen test failure; give A1 the repro and ask it to name MM6–MM9 behaviour changes.
- When a lane's change breaks another lane's test (runner clears, prompt → buttons), relay the exact step fix in the same message.
- The Reviewer and deciders read code and images well; give them the evidence paths and the owner table.
- Check decider premises against the files (D-80's 50,000-gold deed was 12,000; D-81 found the Grandmaster wasn't tax-gated).

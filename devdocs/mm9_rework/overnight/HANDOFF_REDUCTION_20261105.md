# Handoff: MM9 triangle reduction, finish (2026-11-05, from session openyamm-cf)

The previous orchestrator ran out of quota. This file is everything needed to finish in a new session or account.
Read it, then [REDUCTION_BRIEF_20261104.md](REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](REDUCTION_AGENT_TOWNSFOLK.md) (the standing agent brief).

## State update (2026-11-05, afternoon session)
Annud (b60), Markel (b2) and Hanndl (d7) installed after pre-screen, binding regression PASS (252/114, 647/185). Later: Bjarni b60 and Forad c60 installed; **every reduction row is closed** (85 installed, 28 kept). Lining pass state: `devdocs/mm9_rework/STATUS.md`.

## The record
`level_generation/creatures/REDUCTION_LEDGER.md`, section "MM9 reduction (started 2026-11-04)", 113 rows. Status column:
`installed …`, `kept (no useful gain) …`, `ready for review …`, `reducing …`, `queued …`. Summarise it with a short Python
script that splits on `'|'` (not `' | '`; empty cells shift columns). At handoff: 80 installed (incl. PeasantF2), 26 kept,
7 open. Total over installed rows ≈ 925k → 745k triangles (−19.4 %).

## User rules (all still in force)
- "if they look the same then it is fine with me": the orchestrator installs a candidate after its own pre-screen shows
  no visible change; anything visibly different goes back to the agent (or the user).
- "do all" (2026-11-05): prio-3 unique NPCs/bosses are reduced too; faces always stay exact.
- No Meshy/repaint in reductions; UVs, textures, tiers, clips byte-identical.
- Linings (decided 2026-11-05, user: "do what you recommend"): Bjarni, Sven, Tryggva and PeasantM1d get see-through linings in a separate post-install pass, [LINING_BRIEF_20261105.md](LINING_BRIEF_20261105.md) (Bjarni after his reduction row closes); HOM1/HOM2 stay as they are. Reduction agents still add no linings; see-through no worse.

## Open items (7 rows)
| Row | Model | State at handoff | What to do |
|---|---|---|---|
| 70 | Annud Redeye `mm9_annud.glb` 8,560 | **ready for review**, candidate `level_generation/creatures/mm9_annud_reduce_claude/export/mm9_annud_b60.glb`, 7,068 (−17.4 %), UV audit 0, gates equal (left cuff see-through +1–2 px on an existing sliver) | Pre-screen `review/close_b60_*` and `sheet_body_b60_*`, then install (below) with creature project `level_generation/creatures/mm9_annud_claude` |
| 58 | Hanndl `mm9_hanndl.glb` 10,060 | agent was on candidate d7 (see-through gate running) in `mm9_hanndl_reduce_claude/` | Check `README.md`/`export/` there; if no final report, resume with a fresh agent from that project |
| 69 | Forad Darre `mm9_forad.glb` 8,654 | agent on ladder a60 gates, ladder b queued, in `mm9_forad_reduce_claude/` | same |
| 76 | Markel the Great `mm9_markel.glb` 8,169 | **ready for review**, candidate `mm9_markel_reduce_claude/export/mm9_markel.glb` (b2 r60) 6,891 (−15.6 %), UV audit 0, face exact, crown streak checked (none). Arm/hand: one false reading (Talk L thumb, sign error) and three forearm contacts 1–2 mm deeper at single frames; alternate `export/mm9_markel_c60.glb` (−14.3 %) has none | Pre-screen `review/close_b2_60_*` and install b2 (creature project `level_generation/creatures/mm9_markel_claude`) |
| 74, 75 | Tryggva, Sven | **done: kept (no useful gain)** — separate bodies; passing cuts worsened hands/see-through/jitter, fixes fell below 15 % (`mm9_tryggva_reduce_claude/`, `mm9_sven_reduce_claude/` READMEs) | nothing |
| 78 | Bjarni `mm9_bjarni.glb` 8,089 | queued; his own body (4,569 + 3,520), not shared with Tryggva/Sven | new agent with the standing brief; no linings; expect "kept" likely (same family of problems) |

Agents of the old session stop with it. For each open project: read its `README.md` and the ledger row; if it has an
`export/` candidate with a final report, pre-screen and install; otherwise start a new agent with the standing brief and
"continue from the existing project files" (do not redo finished ladders). Leases (`output/creature_3d_locks/`) of dead
agents may be held; release with `tools/creature_workspace.py release --project <dir> --token <token from the .json>`
after checking no process works on it (`pgrep -af <name>`, project file mtimes).

## Pre-screen and install (orchestrator)
1. Read the candidate's close-up sheets at full size (hands/fingertips, hair from behind and in profile, painted motifs,
   cuffs/hems, held props) and the face diff (must be black on the face). Full-body sheets alone miss defects.
   Typical real defects found today: a light streak in hair (PeasantM5: raise hair ratio), a streak on a boot toe
   (PeasantM7d: keep boot toe faces), a blade-shaped bone (Skraelos: keep palm bones), sliding painted motifs (keep exact).
2. `level_generation/creatures/claude_shared/install_reduced.sh <short> <stem> <candidate.glb> <creature project dir>`
   (`<short>` = the `mm9_<short>_reduce_claude` name). It checks the installed source equals `before/`, runs the UV audit
   (0 LOD0 escaping faces, hard gate), the winding check, `tools/install_model.py`, marks the ledger row installed (today's
   date) and appends the "LOD0 reduced post-install" note to the creature README. Find the creature project by its exact
   directory name (`ls -d level_generation/creatures/mm9_<x>_claude`), not by grepping READMEs (other READMEs mention the
   same GLB; one note once landed in the wrong README).
3. If the agent's "after" count differs from what you installed (e.g. you picked a fallback), fix the ledger row's After
   column under the flock `level_generation/creatures/claude_shared/locks/reduction_ledger.lock`.
4. Binding regression after each install batch:
   `OPENYAMM_REGRESSION_FILTER=actor_models_build_every_binding SDL_AUDIODRIVER=dummy ./build/game/openyamm --world mm9 --headless-run-regression-suite actors`
   (expect 252 descriptors on 114 models, 0 failed; MM6-MM8 647 on 185). If it fails on an unrelated data change, check
   whether `build/game/openyamm` is older than that change (another session edits `worlds/mm9/modifiers.yml`); do not build.

## Process lessons
- Before reporting an agent as running, check its project files are changing (`find <proj> -mmin -15`). PeasantF2 sat
  idle 9 h overnight, then again 3 h, while listed as running; a SendMessage nudge resumed it each time.
- Keep the agent brief's limits: at most three ladders, then pick or record "kept"; light models (< ~9k) often end kept
  (bodies already decimated at build, protected share 50–80 %).
- Memory: every Blender/heavy Python job under `systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0`, one
  Blender per agent, `--threads 4`, up to 8 agents. No engine/game builds.
- Coordination: session `openyamm-30` (MM9 map rebuild) will reconvert all 44 MM9 BLVs and asked to be told; when it
  messages before starting, drop to 3–4 agents for the duration. It already switched NPC placement to the 9000+row MM9
  rows (`mm9r_common/dungeon/content.py` `Content.actor`). Reductions do not affect its conversion or lighting bakes.

## After the last row
- Update `devdocs/mm9_rework/STATUS.md` (reduction state) and the `mm9-reduction-policy` memory if used.
- Tell the user the final totals and the two open decisions: linings on the listed bodies, and (now done by openyamm-30)
  the map reconversion with the new MM9 rows.

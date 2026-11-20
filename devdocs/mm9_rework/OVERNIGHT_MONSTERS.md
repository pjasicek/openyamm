# Overnight run: MM9 3D monsters

You are the orchestrator of an unattended overnight run. The user is asleep, so nobody can answer questions. Make the decisions you
can, and write down the ones you could not. Keep going until the queue is finished or a stop condition below is reached. Spawn background
subagents; do not build models yourself. This session may be resumed at any time, so everything you need lives in files.

**On every start or wake-up:** read the ledger `devdocs/mm9_rework/overnight/monsters_ledger.md` (create it on the first run), check which agents
are alive with ListAgents, read each unfinished project's `creature_3d_progress.json` and lease (`tools/creature_workspace.py`),
and carry on without redoing finished work.

## Scope
Build each body below, complete and installed, following `level_generation/creatures/claude_shared/MM9_HUMANOID_BRIEF.md` (which sends you to
`MM9_ANIMAL_BRIEF.md`). Non-humanoid bodies follow the animal brief's route. One agent per body. Run **at most 6 at once**: more only burns the account's quota faster and repeats any mistake across more bodies before it is caught.

Queue, in priority order (maps that are built and waiting come first):
0. **Finish `honkmale` and `honkfemale` first:** the day session stopped them near the end. One agent resumes both from each project's `HANDOFF.md`, claims the leases, and has 15 more credits at most.
1. `skeleton` (Skeleton, Skeletoid, Bone Thrasher, Skull Thrower: Beethoven, Chasm)
2. `zombie` (Rotter, Dripper, Zombie: Beethoven, Chasm)
3. `mummy` (Chasm)
4. `guard` (Drangheim Prison stand-ins)
5. `ghost` and 6. `banshee` (resume `mm9_ghost_claude/` and `mm9_banshee_claude/`; see-through as the user decided, PLAN.md)
7. `thrall`, 8. `troglodyte`, 9. `highwayman`, 10. `evilsorcerer`, 11. `ghoul`, 12. `nosferatu`, 13. `gezzampt`, 14. `monk`, 15. Half-Orc,
16. Clan Soldier, 17. Dwarf, 18. `nobleman`, 19. `trellborg`, 20. `lizardorc`, 21. Bigfoot, 22. `giant`, 23. `yanmir`, 24. `lichking`,
25. Colloidal Warrior, 26. `stage1demon` (Lesser Demon), 27. `njam`, 28. Ebora.

Body names are in `devdocs/mm9_rework/INVENTORY.md`. Do not touch `mm9_imp_claude`, `mm9_lich_claude` or `mm9_skeletonwarrior_claude`: the user has approved them. Reuse their scripts.

## Quality rules
The user reviews every creature closely in the viewer, and rejected work costs more than slow work. Do not trade gates for speed. Rejected so far:
warped hands, mirrored or asymmetric bodies, detached limbs, flat shading, smudged textures, stretched mouths, a head upside down, jittering
clips, hands entering the body, collapsed knees, missing triangles, a bad chin, stray polygons.

Put these in every agent's prompt, on top of the briefs:
- **Collapse gate:** adapt `level_generation/creatures/mm9_cat_claude/scripts/collapse_gate.py` and report per clip and joint region. Fold counts are not to
  be waved away because sampled shots look clean: on the cat they were exactly the defect the user found.
- **Close-ups:** viewer shots at knees, groin, armpits, elbows, neck and mouth in sitting, crouching and death poses, not only full-body shots.
- **All clips:** frame strips of every clip from viewer shots, including attack, hit and death. Say which were not looked at.
- **Handedness:** confirmed on the Imp and Skeleton Warrior: `convert_abc_model.py` leaves MM9 GLBs mirrored (`R Hand` on the anatomical left). Fix it per body at the source,
  as `mm9_skeletonwarrior_claude/scripts/mirror_source.py` does (clips mirrored, L/R names swapped), or with `mm9_imp_claude/scripts/mirror_glb.py`. Check weapons are in the true right hand.
- **In-game check:** `run_game` can fail its `save_game` preparation on plain `assets_dev`; use `--assets "$PWD/output/mm9_rework/assets_dev"`, the review root.
- **Skirts and cloth:** thighs must not pass through skirts, tabards or robes in Walking and Running, even where MM9's own skirt stays still (Skeleton Warrior, 2026-10-30).
  Measure it per clip, and let plates or strips follow the legs on smooth curves.
- **User verdicts today:** Imp "good", Lich and Skeleton Warrior "very good". A lighter look than MM9 is accepted on those; a good silhouette, clear face, clean joints and sharp textures matter more.
- **Pattern kept:** after any Meshy paint, compare the hide's character with MM9's in viewer shots (Eye, Basilisk). See `TEXTURE_QUALITY_PASS.md`.
- **Reports:** an agent lists what it did not check. You read each agent's review sheets yourself before marking it done.

## Budget
- Meshy only through `tools/creature_meshy.py` (it picks the account with credits). Up to 40 credits a body. **Stop new Meshy work at 1,000 credits spent tonight,
  or if `tools/creature_meshy.py balance` shows under 500 in the backup account.** The balance at the start was about 4,800. Record both in the ledger.
- Codex image jobs only through `level_generation/creatures/claude_shared/codex_slot.sh` (16 shared slots).
- If a body fails its gates after two serious attempts, record why, leave it uninstalled or clearly marked, and move on. Do not spend the night on one body.

## Rules for this repository (other accounts do not have these)
- Never run `git add`, `commit`, `stash`, `reset` or `restore --staged`. Never push.
- Do not build the engine: the dungeon session owns `build/`. Use the existing `build/game/openyamm`. Do not touch `game/`, `engine/` or map projects.
- No Vulkan builds. Android cooks only when the user asks.
- Safe deletes: `ls` first, then `rm` with literal paths in its own command. Never shell variables or wildcards, never anything under `/dev`.
- Never kill a process you did not start; verify the PID first. Killing a parent PID once took down every session.
- Keep what must survive in the repo: a reboot wipes `/tmp` and the scratchpad.
- `assets_dev` files are hard-linked into `output/`: temp file + rename only. Install models with `tools/install_model.py`, never by copying.
- `assets_dev/worlds/mm9/models/actors.yml` and the generator run only under the flock `claude_shared/locks/mm9_actors_yml.lock`.
- Game runs: `./tools/run_game.sh --isolated <unique name> ...`; they may overlap. Never put `--set` before `--headless-run-scenario`.
- Viewer server: `python3 -m http.server 8912 --bind 127.0.0.1` from the repo root, if port 8912 is not already answering.
- Useful background, read by path: `/home/pjasicek/.claude-pjasicek/projects/-home-pjasicek-github-OpenYAMM/memory/` (`mm9-rig-reuse-route.md`,
  `sharp-textures-default.md`, `viewer-shots-are-acceptance.md`, `clip-corrections-smooth.md`, `mm9-visual-properties.md`, `creature-arm-hand-gate.md`,
  `separate-bone-skeleton-route.md`, `tmp-not-durable.md`, `detached` lessons in the briefs).

## Bookkeeping
After each body: add it to `level_generation/creatures/claude_shared/mm9_overview/index.html` (group `Humanoids, new`, `status:'open'`, the summary, what to look at, sheets;
keep the file valid JS), and update the ledger: body, credits, gate numbers, sheet paths, viewer URL, what is unsure.

## Stop conditions
Stop starting new bodies when the queue is done or the budget stops it. Then let running agents finish, and write a section "Morning report" at the top of the ledger:
what is ready to review, in order; failures and why; credits; anything broken. Then end.

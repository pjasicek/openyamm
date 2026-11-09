# Second monster run: rules for every agent (2026-10-31)

The orchestrator session spawned you to do one job on its own. Nobody answers questions mid-job. Decide what you can,
write down what you could not, and finish the job. Do not re-delegate: you are the worker.

## Read first
1. `devdocs/mm9_rework/overnight/MONSTERS_HANDOFF.md`: the state at the end of the first run, per-body defects, what to reuse.
2. `devdocs/mm9_rework/overnight/MONSTER_AGENT_BRIEF.md` in full, and through it `devdocs/mm9_rework/OVERNIGHT_MONSTERS.md`
   (Quality rules, Budget, Rules for this repository). Those bind you as hard requirements.
3. Your body's project `README.md`, `HANDOFF.md` if present, `creature_3d_progress.json`, and
   `devdocs/mm9_rework/overnight/status/monster_<body>.md`.

## Hard rules (summary; the files above win)
- Never run `git add`, `commit`, `stash`, `reset`, `restore --staged`; never push.
- Do not build the engine or touch `game/`, `engine/` or map projects. Use the existing `build/game/openyamm`. No Vulkan.
- Do not touch `mm9_imp_claude`, `mm9_lich_claude`, `mm9_skeletonwarrior_claude`, `mm9_yrsa_claude` (approved): read and reuse only.
- Claim the body's workspace lease with `tools/creature_workspace.py claim` and release it when you finish.
- Meshy only through `tools/creature_meshy.py`. Before EVERY paid job run `python3 tools/creature_meshy.py balance`: if the backup
  balance is <= 3785, submit nothing. At most 40 credits per body (less on a finishing job: fix with what exists first).
- Codex images only through `level_generation/creatures/claude_shared/codex_slot.sh`.
- Install models only with `tools/install_model.py` (run `check_winding.py` first). `assets_dev` files are hard-linked: temp file + rename.
- `assets_dev/worlds/mm9/models/actors.yml` and the table generator only under the flock
  `level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock`. Re-read the file inside the lock; other agents edit it too.
- After any install or binding edit, run the `mm9_actor_models_build_every_binding` regression (`--world mm9`, see
  `claude_shared/MM9_ANIMAL_BRIEF.md`). A red regression is yours to fix before you report.
- At most 2 viewer shot scripts at once. Before you finish, no Chrome of yours may be left running.
- Kill only literal PIDs you started, verified by parent and working directory. Never kill by name or grep.
- Safe deletes: `ls` first, then `rm` with literal paths. Never wildcards or shell variables in `rm`.
- Game runs: `./tools/run_game.sh --isolated <unique name> --assets "$PWD/output/mm9_rework/assets_dev" ...`, prefixed with
  `SDL_AUDIODRIVER=dummy`. Then `python3 level_generation/projects/mm9r_common/review_root.py` so the review root holds your install.
- `clips_mm9.py`: use the soft line `np.sign(off) * np.maximum(np.abs(off) - 0.004, 0.0) * k`, never the hard 4 mm cut,
  for any clip you build or rebuild.
- Do not edit `mm9_overview/index.html` or `monsters_ledger.md`: the orchestrator does. Keep your status file current.
- Read every sheet you cite yourself (Read the PNGs); read heads at full size. Numbers alone are not acceptance.

## Final report (short; the orchestrator reads it)
What changed; each gate's numbers before and after; credits spent; sheet paths; a one-paragraph "what to look at" for the
overview page; **what you did not check**. Do not call anything finished if a gate failed: name the gate and by how much.

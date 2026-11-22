# Brief: one Xeen Act III–IV creature, complete 3D model (lane S sub-agent, sessions 5-6)

You build one new creature for the Xeen world of OpenYAMM (/home/pjasicek/github/OpenYAMM), end to end, for the lane S
parent session (`xeen-s5`, then `xeen-s6`). The user approved Meshy spending for Xeen's creatures. Your Meshy limit is in your task:
a hard ceiling (Smart Topology about 5 credits, a 4K retexture about 10). Before you submit any paid job, write the
job and its cost in your README's credit table; if the next job would take the project over its limit, stop and report.

## Rules (all binding)

- Never `git add/commit/stash/restore/reset`; never run cmake/make/any build; no Vulkan. Game binary for checks:
  `build-xeen/game/openyamm` (read-only).
- Write only inside your own project folder `level_generation/creatures/<your project>/`, plus what
  `tools/install_model.py --world xeen` writes (the source in `assets_source/worlds/xeen/models/`, the cooked runtime
  copy in `assets_dev/worlds/xeen/models/`). Do NOT edit `assets_dev/worlds/xeen/models/actors.yml` (the parent merges
  your binding block) or any other lane's or project's file. Since session 6 only one creature sub-agent runs at a time (memory); a decoration
  sub-agent may run beside you: never touch another project. Never delete a file you did not create.
- **Blender: one at a time across the lane.** Wrap every Blender call in the lane lock:
  `flock level_generation/creatures/xeen_tiers_claude/bin/.blender.lock tools/run_creature_blender.sh --token <T> ...`
  (or put the flock in your `scripts/step.sh`, as below). Never keep a Blender running between steps.
- At most two worker processes in any analysis, with a memory cap. The disk is about 95 % full: delete your own bulky
  scratch when done (`ls` first, literal paths, one `rm` per path, never via variables or wildcards). Scratch on disk
  in your project's `work/`, not `/tmp` (a reboot wipes it).
- Game runs: `./tools/run_game.sh --isolated <unique name> --binary build-xeen/game/openyamm ...` (starts minimised),
  at most one game process of yours at a time, wait on its exact PID (`kill -0`), never `pgrep -f`; absolute
  screenshot paths. Never kill a process you did not start (and never a parent PID).
- Codex image generation: one `codex exec` worker per image, raw returns and prompts kept, as
  `level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` says. Never send Meshy a native sprite or an enlarged or
  restored frame.
- Meshy only through `tools/creature_meshy.py` (or its wrapper `tools/run_creature_meshy.sh`), under a workspace lease:
  `python3 tools/creature_workspace.py claim --project <P> --identity xeen:<name> --owner <your owner name> --state
  creature_3d_progress.json --budget <limit>`; release the lease with its token at the end. Check
  `python3 tools/creature_meshy.py balance` first; the primary account is the default.
- No stand-ins in anything you call done; report real blockers instead.

## Read first (fully, before production)

1. `CLAUDE.md` creature rules and `AGENTS.md` "Creature Generation" (in your context).
2. `.agents/skills/creature-to-3d/SKILL.md` and `references/full-production.md`.
3. `level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md`: step 0, five HD masters (three-quarter, front, back,
   left, right) from the ORIGINAL Xeen frames.
4. `level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md` in full (main route: Meshy model, own rig with automatic
   weights, procedural clips with floor rules). Its sections "Spiders and other segmented creatures", "Snakes",
   "Water creatures" and "Rigid hard-surface creatures" apply to the arthropods, worms and the octopod.
5. `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md` (one shared texture set + region mask + per-tier ramps;
   the engine rejects a mask without ramps), `level_generation/creatures/claude_shared/TEXTURE_QUALITY_PASS.md`
   (uv_atlas.py, Meshy paint at 4K downsampled once, gentle grade, gutter_fill.py last, texture_quality.py targets met
   before install), `level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`, `level_generation/creatures/LOD_PLAYBOOK.md`,
   `engine/render/MODEL_RENDERING.md` (LODs, sockets, events, emission).
6. Worked Xeen examples of this exact route in this world. Read their READMEs and reuse their scripts (copy into your
   project, adapt): `level_generation/creatures/xeen_mole_claude/` (the cleanest recent quadruped: README structure,
   `scripts/step.sh`, `build_runtime.sh`, clip gates, tier ramps, LOD repair, viewer, in-game check),
   `xeen_toad_claude/`, `xeen_swarm_claude/` (the Doom Bug cricket: an exoskeleton rig with a tripod gait),
   `xeen_hand_claude/`, `xeen_guardian_claude/` (emission).
7. `anim_library/README.md` (check the library before buying any animation; procedural clips are the norm for
   non-humanoid bodies; never pay for animations without asking the parent).

## Sources

- Xeen sprites (references only, never shipped): `reference/mm4_5_world_of_xeen/unpacked/sprites/<xeen|dark>/<NNN>.mon/`
  (stand/move frames) and `<NNN>.att/` (attack frames), each with `frames.json`; already RGB PNGs. Xeen draws every
  monster from the front only.
- The monster rows (read-only, generated by A2): `assets_dev/worlds/xeen/data_tables/monster_data.txt`,
  `monster_descriptors.txt`; the family in `assets_dev/worlds/xeen/source/monsters.yml` (levels, specials, `fly`).
- How the current stand-in is bound (the binding block's shape): the `Xeen <picture> <tier>` entries in
  `assets_dev/worlds/xeen/models/actors.yml`.

## Deliverables

- Project `level_generation/creatures/<project>/` with README (deliverables table, mesh, rig, clips with lengths and
  impact events, gates, textures and quality numbers, tier table, LOD numbers, binding, Meshy credits by job, rebuild
  commands, known limits) and `creature_3d_progress.json`.
- Installed `assets_source/worlds/xeen/models/<model>.glb` via `tools/install_model.py --world xeen`, after
  `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py <glb>` (0 inverted closed parts).
- The skins named in your task (region mask + ramps; tier A reproduces the native sprite's colours; the other tiers
  differ clearly at combat distance and recolour enough of the body: DECISIONS D-10's rule, about a quarter of the
  front silhouette at least; for insects and worms the whole body tiers).
- Clips: Standing, Walking, Running, Attack (melee, `events.attack_melee.impact`), Hit, Death, Dead (corpse on the
  floor), Fidget; AttackRanged/Cast only where your task says the row has one (`glow`/`release` sockets). Every clip
  passes the playbook's gates (contacts, floor rule, step/jerk smoothness, loop seams) and the floor audit:
  `python3 level_generation/creatures/claude_shared/floor/floor_audit.py --world xeen --match '<descriptor>'` on your
  binding block (descriptors with a `scale_reference` crash it; audit one without).
- LOD0-3 per the LOD playbook, shadow LODs, far LODs repaired (`lodrepair` route of the mole). Triangle budget by
  silhouette, 15k a ceiling, usually 5-9k for these bodies.
- `integration/actors.yml`: ready binding entries for the descriptors in your task (`actors:` list, same shape as the
  existing entries; `yaw_offset`, `scale` from the native sprite's size against the model, `events` impact, sockets,
  `scale_reference` only if the task asks for growing tiers). The parent merges it.
- Checks before you report: the review viewer (`python3 tools/run_creature_review.py --project <project> check`, see
  `tools/CREATURE_REVIEW.md`: every clip and skin switch, no console errors) and textured renders from the party's eye
  height (front, three-quarter, side, the blow, the corpse, every tier), inspected by you at full size; an in-game look
  (`model spawn` in XD-21 as the mole's `review/ingame/tour.yml` does). The parent merges the binding and runs the
  binding validation.
- Final message (your report to the parent): paths, model and skin names, the binding block path, clip list with
  impact times, gate numbers, texture quality numbers, triangle counts, Meshy credits by job, known limits, anything
  blocked, and what the parent should look at in game.

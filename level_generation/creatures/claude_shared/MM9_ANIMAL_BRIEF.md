# MM9 animal 3D models: common brief (2026-10-30)

Build complete, installed 3D models for MM9 animals: Meshy work, rig, MM9 clips, textures, LODs, runtime binding, viewer,
checks. Quality is key: the user reviews every creature closely in the viewer and has rejected flat shading, detached
parts, smudged textures, wrong head orientation, stretched mouths and jittering clips. Pass the gates below before you
report.

## Route
- Non-humanoid MM9 bodies use the **MM9 rig-reuse route**: Codex HD masters rendered from the MM9 model and skin, a
  Meshy Smart Topology mesh, our own clean-up, the mesh posed to the MM9 bind pose and weighted to the ORIGINAL MM9
  skeleton (ABC via `tools/mm9_import_discovery/convert_abc_model.py`), MM9's own clips resampled, and MM9 clip events
  as contact times. Reference projects:
  - `level_generation/creatures/mm9_dfly_claude/` (the route);
  - `mm9_wolf_claude/` (a quadruped on it: `fit_quad.py` transient-skinning fit, a voxel clean of the Meshy body,
    weight refinement, the fold measure, tooth weights);
  - `mm9_crow_claude/` (a bird on it: head/feet orientation, the throat, the head graft; read its README's lessons).
- Read first:
  - `level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` (step 0: five Codex HD masters before any Meshy job,
    rendered from the MM9 model + skin, never native sprites);
  - `level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md` (general non-humanoid rules, floor rules, pitfalls);
  - `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md`, all of it, especially **"Sharp textures"**;
  - `level_generation/creatures/claude_shared/TEXTURE_QUALITY_PASS.md`;
  - `level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`;
  - `devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md` (carry over MM9 skin alpha cut-outs, glow, etc.: match or gain).
- **Sharp textures from the start:** UVs with `claude_shared/uv_atlas.py` (not Smart UV), a Meshy retexture at
  `texture_resolution: "4k"` downsampled once to 2K, the gentle grade, and the `texture_quality.py` targets met
  (atlas >= 55 %, spread <= 1.3, fragments <= 3 %, stretch p90 <= 1.5).
- **Skins/tiers:** extra MM9 skins of the same body become tiers by region mask + colour ramps (no per-tier baked
  base colours). A skin with a different design (e.g. the ram's horns) may need its own region or part.

## Gates (all, before reporting)
- **Acceptance is the review viewer, not Blender.** Sheets you hand back are made from
  `python3 tools/run_creature_review.py --project <project> --token <lease token> shots <clip>:<time>:<view>:<focus> ...`
  at several angles (side, front, below, ¾), several clip times and every tier. Look at every shot yourself. Blender
  renders are fine for diagnosis but hide defects: they missed a pale collar and a throat step on the crow.
- **Symmetry:** MM9 bodies are usually exactly mirror-symmetric. Measure ours against MM9; if MM9 is symmetric, make
  ours symmetric (keep the better half and mirror it, weights to the matching L/R bones).
- **Orientation:** head and feet must match MM9's full orientation (direction AND roll/up vector) per frame in every
  clip. Measure the head's up vector and the beak/snout direction against MM9's; no chin hanging under the head (crow
  lesson), and soles facing down.
- **Head shape:** compare the head with a real animal's proportions as well as MM9's. The crow's first Meshy head had a
  wading bird's bill and a flat skull, and no weight change could fix it. If the head is wrong, graft a new head-only
  Meshy model early.
- **Attachment:** `python3 level_generation/creatures/claude_shared/detached_parts_audit.py <glb>` gives 0 detached in
  every clip. Root limbs, fins, ears, tails and eyeballs into the body (see `mm9_eye_claude/scripts/root_limbs.py`);
  eyeballs share the socket's weights. Also look for floating rows of plates and stray shards the audit can miss
  (Sea Monster lesson).
- **No folds or flaps:** no fused fur layers, keels or pockets (wolf lesson: voxel-clean the Meshy body first, check for
  folded faces per clip), and no torn shards at mouth corners.
- **Mouths:** if a clip opens the mouth, build a real cavity (gums, palate, tongue, throat) skinned between head and
  jaw, with teeth rigid to their own jaw and none piercing the opposite jaw when closed (Terror, Sea Monster, Dragon
  King lessons). Hinge at the mouth corners.
- **Smooth shading:** `python3 level_generation/creatures/claude_shared/flat_shading_check.py <glb>` gives about 0 flat on
  bodies.
- **Clips:** any correction applied to an MM9 clip is solved on keys or low-passed and blended in and out, never per
  frame. Compare against MM9's untouched clip so nothing jitters, and watch every clip at normal speed in the viewer.
  Loop seams closed. Floor audit OK.
- **Viewer:** a review viewer in `review/viewer/` like the reference projects (manifest with all tiers and clips).
  Then `python3 tools/run_creature_review.py --project <project> check` gives 0 errors (server on port 8912).
- **Binding and regression:** `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py` gives 0
  inverted closed parts. Install with `tools/install_model.py --world mm9`, then run the
  `mm9_actor_models_build_every_binding` regression (`--world mm9`).

## Data and runtime
- These animals are MM9 NPC rows (`IsMonster 0`), so they have no MM9 world descriptor yet. To get one:
  - append your rows to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (columns: source number, legacy visual
    actor id, note; pick a sensible existing legacy actor as the fallback visual; see how rows 54/252/254 were chosen
    in `level_generation/creatures/mm9_annud_claude/README.md`);
  - run `python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py`;
  - do both under the flock `level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock`. Five other animal
    agents edit the same TSV. Re-read it inside the lock and only add your rows.
  The generator writes `assets_dev/worlds/mm9/data_tables/*` via temp + rename. Those files were hard-linked into
  `output/mm9_rework/assets_dev` (the review root), so check whether the review root needs its copy refreshed
  (`level_generation/projects/mm9r_common/review_root.py`).
- Bind in `assets_dev/worlds/mm9/models/actors.yml` under the same flock, via temp + rename. Follow the reference
  projects' binding blocks (scale, strides, roles, impact times, sockets). Animals mostly wander, flee and idle: map
  MM9's clips to Standing/Walking/Running/Fidget/Hit/Death/Dead, and AttackMelee where the row fights (basemelee.scr,
  `Hostility 1`).
- Meshy: only through `tools/creature_meshy.py` (it picks the account with credits; the backup holds the credits).
  Budget: up to 60 credits for your two animals without asking.
- Codex image jobs only through `level_generation/creatures/claude_shared/codex_slot.sh codex exec ...` (16 shared slots).
- Work under the project lease (`tools/creature_workspace.py claim`). Blender through `tools/run_creature_blender.sh`.

## Rules
- Never edit, re-export or copy back from `assets_dev` models.
- `assets_dev` files are hard-linked into `output/` mirrors: use temp + rename.
- Game runs may overlap with other agents' and the user's: no waiting. Use `./tools/run_game.sh --isolated <unique name>`
  (starts minimized), and never kill processes you didn't start. An in-game check is optional.
- Never run git add/commit/stash/reset/restore --staged.
- Safe deletes only: `ls` first, then `rm` with literal paths in its own command. Never `rm` with shell variables or
  wildcards, even on your own scratch files.
- Never put `--set` before `--headless-run-scenario`.
- Don't touch other agents' projects: other `mm9_*_claude` creature projects, the engine renderer, the map projects.
- Keep anything needed across restarts in the project, not in `/tmp`: the machine rebooted once and wiped it.

## Deliverables per animal
- **Project:** `level_generation/creatures/mm9_<name>_claude/`, with a README in the reference projects' format: table,
  route, rebuild, checks with numbers, deviations, and "User artistic acceptance: not recorded".
- **Installed model and binding.**
- **Review sheets:** MM9 vs ours (rest pose + clip extremes), tiers, texture close-up, from viewer shots.

Report briefly per animal: the route taken and its deviations, the gate numbers, credits, sheet paths and the viewer URL
(http://127.0.0.1:8912/level_generation/creatures/<project>/review/viewer/).

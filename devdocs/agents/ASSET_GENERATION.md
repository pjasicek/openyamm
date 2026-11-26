# Asset generation: maps, creatures, sprites and 3D models

Moved from the root `AGENTS.md` on 2026-11-24, unchanged. Read the section for the asset kind you work on.

## Level generation

- `level_generation/` is tracked only in part: its own `.gitignore` admits docs, scripts, review pages and small
  hand-written data and skips the heavy folders (`work/`, `review/`, `meshy/`, renders, venvs). Models and images stay
  local. After creating a project or a large text file there, run `python3 level_generation/update_gitignore.py`,
  which lists the files over 256 KB that the rules would admit.
- For creating or revising indoor/outdoor maps, start with [Level Generation](../../level_generation/README.md), even when
  the user does not name the document. Follow its applicable indoor/outdoor workflow, reference studies, calibration,
  and current pipeline-status notes; example maps are references, not universal layouts or exporters.
- Geometric detail on existing MM6–MM8 BModels (an appended untouchable model with eaves, frames, sills, coping) is an
  experimental project, shelved by the user on 2026-11-12: do not apply it to maps. To resume it, start with its
  [handoff](../../level_generation/projects/mm6_sorpigal_geometry_pilot/HANDOFF.md), then the
  [playbook](../../level_generation/projects/mm6_sorpigal_geometry_pilot/PLAYBOOK.md).
- Use [Blender MCP Startup](../../level_generation/BLENDER_MCP_STARTUP.md) for agent-managed startup/reconnection.
  Prioritize visual authenticity and quick static wiring/build checks; follow the README's criteria for runtime
  scenarios rather than running a scenario for every face, service, or event binding.

## Creature generation

- For local creature viewer checks, screenshots and playback recordings, use the reusable
  [creature review wrapper](../../tools/CREATURE_REVIEW.md): `python3 tools/run_creature_review.py`.
  The user authorized this workflow and its saved command-prefix approval across creature sessions. Reuse that
  prefix when Chrome requires desktop/socket access; do not request a new approval for each creature's capture script.

- Treat `CREATURE_RESTORE <source-pattern>` as an explicit request to follow
  [Creature Restore](../../.agents/skills/creature-restore/SKILL.md), also invocable as `$creature-restore`.
  Honor scope overrides such as front-only, resume, or plan-only; discussing the workflow does not start generation.
- For MM6–MM8 sprites to rigged 3D creatures, Meshy model/rig/texture handoffs and existing model WIP audit/resume,
  use [Creature to 3D](../../.agents/skills/creature-to-3d/SKILL.md), also invocable as `$creature-to-3d` or
  `CREATURE_TO_3D <source-pattern>`. Codex and Claude share the entire Claude production workflow by default:
  [HD master references](../../level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md), the
  [humanoid playbook](../../level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md) or
  [non-humanoid playbook](../../level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md), and
  [creature textures](../../level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md). Read the applicable playbook fully;
  its current default and later corrections take precedence over older worked examples. Humanoids use the
  source-frame rig and gates from `mm6_bar1_claude/` and `mm6_gob2_claude/`, including local animation selection
  before modelling. Complete creature-production requests include agent-operated Meshy, equipment, animation,
  textures, LODs, runtime binding, regression and indoor/outdoor visual checks; `FULL` explicitly requests the same
  scope. Preserve narrower requests and existing resume scope. Skill maintenance, discussion, audit and plan-only
  requests do not start generation or asset changes.
- For MM6–MM8 creature sprite restoration/upscaling, atlas export, masks, or color variants, start with
  [Sprite Atlas and Variants Pipeline](../../level_generation/creatures/SPRITE_ATLAS_VARIANTS_PIPELINE.md), even when the
  user does not name the document. It contains the short generation recipe and separately marked future engine deltas.
- Humanoid animation sources live in the git-ignored [animation library](../../anim_library/README.md): a
  humanoid set, Mixamo clips and stored Meshy library results. Before paying for a Meshy library action, run
  `meshy_anim_library.py check <ids>` (see the README) and retarget stored clips instead of buying them again; after
  every paid animation job, `ingest` the result. Check Mixamo there before asking the user for downloads. Never commit
  raw library clips; commit only retargeted clips baked into creature GLBs under our role names.
- Use [Direct Sprite Workflow](../../level_generation/creatures/DIRECT_SPRITE_WORKFLOW.md) for detailed AI prompting,
  transparency/edge cleanup, alignment, and review. For rigged 3D models,
  [Sprite-to-3D Workflow](../../level_generation/creatures/SPRITE_TO_3D_WORKFLOW.md) supplies supplementary coordinate,
  export and historical calibration details; it does not override the shared playbooks above.
- Build or clean every 3D mesh (creatures, props, decorations) to the
  [game asset modelling guidelines](../../level_generation/GAME_ASSET_MODELLING_GUIDELINES.md): silhouette-first triangle
  budgets, no micro or sliver triangles, hard edges on UV seams, consistent texel density, Khronos PBR ranges,
  transparent parts on their own mesh, about 50 % per LOD. Record engine-driven deviations in the project README.
- Texture every Meshy-textured model for sharpness from the start: UVs from `claude_shared/uv_atlas.py` (since
  2026-11-12 PartUV charts, seam pass and sparrow packing; `charts='xatlas', packer='xatlas', seam_rounds=0` switches
  back), Meshy paint at 4K downsampled once to 2K, gentle grading, nearest-texel gutter re-fill (`gutter_fill.py`)
  last, and the measured atlas/density targets met before install, per the
  [texture quality pass](../../level_generation/creatures/claude_shared/TEXTURE_QUALITY_PASS.md). Smart UV layouts with 2K
  paints came out smudged (MM9, 2026-10-30).
- For a world-wide pass over installed 3D monsters (tier scales against the sprite tables, floor contact of every
  clip, walk/run choice and playback rate, texture relief), follow the
  [creature post-process](../../level_generation/creatures/CREATURE_POSTPROCESS.md); MM8 was done on 2026-10-21.
- Only when the user asks to retopologise or repair an existing creature mesh, follow the
  [creature retopology playbook](../../level_generation/creatures/RETOPOLOGY_PLAYBOOK.md); it is not a default step.
- Keep asset-generation checks focused on visuals and quick manifest/alpha/placement validation. Renderer work and
  its runtime tests are separate scope; proposed engine deltas are not automatically part of each generation task.

## Decoration and effect restoration

- For prepared MM6–MM8 PC/NPC portrait and small HUD/icon sheets, use
  [Dense64 batching](../../level_generation/ui/hud_inventory/BATCHING_DENSE64.md) and the current
  [chat bundle index](../../level_generation/ui/hud_inventory/CHAT_BUNDLES.md). The user selected a maximum of 64
  targets per sheet, constrained by the measured pixel budget; use fewer for larger art. Check retained results
  and superseded assignments before generating. Preparation and raw-return cataloguing do not accept artwork.
- For MM9 player portraits as MM6–MM8 portrait families (56 slots, template family, Codex sheets, landmark
  verification), follow the [MM9 PC portrait playbook](../../level_generation/ui/hud_inventory/mm9_pc_portraits/PLAYBOOK.md).
- For MM6–MM8 non-creature sprite enhancement (decorations, items, projectiles, FX, weather or UI), start with
  [Prepared Sprite Restoration Jobs](../../level_generation/sprites/restoration_jobs/README.md). Use its exact prompts,
  palette references, resumable queue and imagegen skill; planning alone does not authorize generation.
- Preserve native animation/placement and use the relevant soft-effect cleanup rules. Keep visual review concise;
  engine installation and runtime scenarios are separate from asset restoration.

## Installing 3D models

- 3D models (creatures, their held or worn attachments, decorations and props): the accepted GLB is a source in
  `assets_source/worlds/<world>/models/` (shared models in `assets_source/engine/models/`). Decoration models of the
  MM6-MM8 worlds (`mm6_deco_*`, `mm7_deco_*`, `mm8_deco_*`) are engine content, and so are their bindings: install them
  with `--engine` and bind them in `engine/models/decorations.yml`, `indoor_decorations.yml` and
  `decoration_overlays.yml`, which every world reads; a world may extend them with `worlds/<world>/models/` manifests of
  the same names. MM9's (`mm9_deco_*`) are MM9 world content: only MM9 binds them and MM9 ships as its own package, so
  install them with `--world mm9` and bind them in `worlds/mm9/models/` (moved there on 2026-11-08). Before an
  install, run `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py <glb>` (0 inverted closed
  parts). Install with `tools/install_model.py <export.glb>` (`--world`, `--engine`, `--name`), never by copying into
  `assets_dev` directly. The tool then writes the runtime copy at the same path under `assets_dev`, cooked by
  `tools/cook_models.py` ([ASSET_COOKING_PLAN.md](../../devdocs/ASSET_COOKING_PLAN.md) §12). Never edit,
  re-export or copy back from an `assets_dev` model, and run `tools/model_backface_split.py` only on such runtime
  copies, never on a source or a project export. Bindings and tables (`actors.yml`, `decorations.yml`) stay in
  `assets_dev`.

## MM9 equipment art

- When changing MM9 equipment art, use `MM9_EQUIPMENT_PAPERDOLL_GENERATION_GOAL.md` as a maintenance reference and
  `MM9_ARMOR_PAPERDOLL_AI_GENERATION.md` for armor prompting, fitting, and review. For paired armor `vN`/`vNa` changes,
  apply the consistency checks in `MM9_ARMOR_POSE_PAIR_CONSISTENCY_GOAL.md`. The generation run and pose audit are
  completed work; validate affected assets without restarting their historical completion gates.

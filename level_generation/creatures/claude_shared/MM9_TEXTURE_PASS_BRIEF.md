# MM9 texture pass on approved creatures: common brief (2026-10-30)

The user approved these creatures' models and animations and asked for the Magreeb's texture treatment on them. Change
only texture sharpness, never the look, rig, clips or geometry.

## Read first
- `level_generation/creatures/claude_shared/TEXTURE_QUALITY_PASS.md`, the recipe: measure, targets, steps, pitfalls.
- `level_generation/creatures/mm9_magreeb_claude/README.md`, "Texture quality pass" (the pilot).
- `level_generation/creatures/mm9_wingedmutant_claude/README.md`, its texture pass and wing-tone correction: a fresh paint can
  drift in contrast and hue, and the fix is a grade plus a ramp refit on that region.
- `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md`, "Sharp textures".
- Your creature's README: rebuild steps, tiers, and any later fix sections. Those fixes must survive the rebuild.

## What to do
1. Measure every texture set with `claude_shared/texture_quality.py`. If a set already meets the targets, leave it.
2. Apply the recipe: new UVs with `claude_shared/uv_atlas.py`, a Meshy retexture at 4K with the same HD masters, downsampled
   once to 2K, the gentle grade, and region mask and ramps kept for every tier.
3. Keep the approved colours and look. Compare crops of every tier against the approved version. Pin the ramps, or
   correct the region's contrast, if the fresh paint drifts lighter, grainier or to another hue.
4. A repaint comes after the last vertex move, on the exact mesh that is installed. Anything painted per texel by the
   project's scripts (mouth interiors, eyes) must be rebuilt on the new UVs.

Budget: up to 20 Meshy credits per creature on the backup account, only through `tools/creature_meshy.py`. Ask first
if you need more.

## Verification, per creature
- Rebuild per the README, `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py` (0 inverted closed
  parts), install with `tools/install_model.py`.
- `python3 tools/run_creature_review.py --project <project> check`.
- Floor audit, `python3 level_generation/creatures/claude_shared/detached_parts_audit.py <glb>`,
  `python3 level_generation/creatures/claude_shared/flat_shading_check.py <glb>`, and the
  `mm9_actor_models_build_every_binding` regression (`--world mm9`).
- `texture_quality.py` numbers before and after.
- **Acceptance is from review-viewer shots, not Blender:** a before/after sheet with `tools/run_creature_review.py ... shots`
  at identical cameras, close-ups and full body, every tier. Look at every shot yourself.
- Back up the before state in `work/before_texpass/`, and add a dated README section with numbers and credits.

## Rules
- Never edit, re-export or copy back from `assets_dev` models.
- If you touch `assets_dev/worlds/mm9/models/actors.yml`, edit it only under the flock
  `level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock`, via temp + rename.
- Codex only through `level_generation/creatures/claude_shared/codex_slot.sh`.
- Game runs may overlap: use `./tools/run_game.sh --isolated <unique name>`, and never kill processes you didn't start.
- Never run git add/commit/stash/reset/restore --staged.
- Safe deletes only: `ls` first, then `rm` with literal paths in its own command. Never `rm` with shell variables or
  wildcards, even on your own scratch files.
- Keep anything needed later in the project, not /tmp.
- Don't touch other `mm9_*_claude` projects than the ones you were given.

Report per creature: numbers before and after, credits, the viewer sheet path, check results and anything that drifted.

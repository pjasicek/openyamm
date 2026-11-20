# The Bulwark — Round 2 (2026-10-23)

**Built and staged: 10107 The Bulwark and 10141 The Bulwark (coupled). All 73 Hesper scenarios pass.**
The requested desktop smoke was attempted, but SDL stopped before map load: **No available video device**.
The integrator accepted the model and all three viewer palettes on 2026-10-23. Native D7 verification remains with the user.

[Viewer](http://127.0.0.1:8912/level_generation/creatures/hes_bulwark_codex/review/viewer/) ·
[Scorched preview](review/geometry/pbr_b_Standing.png) · [Actor bindings](integration/actors.yml) ·
[Final gates](review/final_gates.json) · [Artifact hashes](review/artifact_hashes.json).
Both game rows use **scorched**. The viewer also offers ivory and gilded; select a `Coupled_*` clip for the cables.
Its coupled walking/run clips are diagnostic poses; the stationary game row binds standing for movement.

Authority: [CREATURE_BUILDS, Round 2](../../../design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md).
The approved concept is [references_hd/concept.png](references_hd/concept.png), left half; the Ion Cannon is another project.
[Five selected HD masters](references_hd/selected_views_review.png), [prompts and provenance](references_hd/generation_runs.json),
[HD validation](references_hd/validation.json). Ten original 1536×1024 RGBA returns are retained, including candidates.
The approved concept governs; the final model is accepted in P3, “Integrator answer: the Bulwark (2026-10-23)”.

## Meshy jobs for the integrator

**Both jobs succeeded. No pending submissions; do not resubmit. Actual total: 15 / 60 credits, backup account.**
No connector changes, paid rig, paid animation or second tier mesh. Raw downloads and canonical Meshy receipts remain unchanged.
Paths below are repository-relative; `@file:` paths in request JSON are project-relative.

| Job | Type / exact input | Settings | Exact target |
|---|---|---|---|
| `bulwark_geometry_v1` — SUCCEEDED, 5 credits | `image-to-3d`; `level_generation/creatures/hes_bulwark_codex/references_hd/00_three_quarter.png` | `meshy-t2`, `model_type: smart-topology`, `target_polycount: 15000`, `should_texture: false`, `target_formats: [glb]`; omit pose mode | `level_generation/creatures/hes_bulwark_codex/meshy/bulwark_geometry_v1/model_urls_glb.glb` |
| `bulwark_retexture_v1` — SUCCEEDED, 10 credits | `retexture`; `level_generation/creatures/hes_bulwark_codex/work/bulwark_texture_upload.glb`; four images below | `meshy-7`, `enable_original_uv: true`, `enable_pbr: true`, `texture_resolution: 2k`, `target_formats: [glb]` | `level_generation/creatures/hes_bulwark_codex/meshy/bulwark_retexture_v1/model_urls_glb.glb`, plus all returned maps and preview in that folder |

Retexture image order:

1. `level_generation/creatures/hes_bulwark_codex/references_hd/01_front.png`
2. `level_generation/creatures/hes_bulwark_codex/references_hd/03_left.png`
3. `level_generation/creatures/hes_bulwark_codex/references_hd/02_back.png`
4. `level_generation/creatures/hes_bulwark_codex/references_hd/04_right.png`

Requests: `requests/bulwark_geometry_v1.json`, `requests/bulwark_retexture_v1.json`.
Frozen upload SHA256: `1d45fa586255cdfe8b20c8e99fee70f01b26c8ef7406e2de11a3d57afaa58c09`.
Retexture return SHA256: `e81cc12152ee552242a2745e36dffc55f08f76f91e017d9434f7f4f28124f81c`.
The returned 10,632 triangles match the upload bijectively: maximum position error **0.000000298 m**, UV error
**0.000061 texels at 2K**, zero corners displaced by half a texel. Our rig is retained.
[Correspondence record](review/geometry/retexture_compare.json).

## Geometry, materials and cables

Meshy returned 14,809 triangles including an unwanted fifth central leg. Removing its 20 components leaves 13,307.
The reduction study selected 10,632; the next 9,571-triangle candidate lost muzzle/armour detail and exceeded measured
surface-distance limits. [Study](review/geometry/reduction.json), [comparison](review/geometry/reduction_sheet.png).
The previous handoff incorrectly described three existing rear sockets: there were **two**. They were moved sideways
by 0.14 m each, and a matching centre socket was added. Four emissive barrel/core inserts bring the body to 11,160.
The original downloads are untouched. [Final construction measurements](review/geometry/finish_geometry.json).

One shared body texture set: base colour 2K; normal, ORM and region mask 1K. R = armour, G = trim; violet resin is
unchanged. Independent mask channels have padded gutters. Three `KHR_materials_variants` select ivory/scorched/gilded
ramps; the latter two reuse the accepted Sentinel palettes fitted to this mesh's luminance. The runtime contains no
per-tier baked base maps. Viewer-only copies bake ramps for Three.js. Material-class maps remain in `textures/`.

Measured normal Y correlation **−0.998963**: green was flipped once to OpenGL. ORM.R is the engine's **specular mask**,
not AO; AO is retained separately and contributes gently to the base map because the return already has shading.
Roughness floors: ceramic .55, trim .42, resin .64. Trim/gilded metallic factor .85 is the recorded indoor-response
choice; ivory/scorched ceramic stays nonmetal. Every glow uses per-tier `emissiveFactor` and bloom, no emissive texture.
[Material report](textures/bulwark_material_report.json), [ramps](textures/bulwark_ramps.json).

The atlas has 1,047 charts, 39.55% sampled coverage, no overlapping sampled texels, no degenerate UV triangles,
and hard normal edges at seams. Actual minimum inter-chart gap is **12.159 texels at 2K**; outer border is eight.
The older 5.72 figure in `uv_pack.json` is scaled single packing padding, not measured chart-to-chart separation.
[Measured gutter](review/geometry/uv_gutter.json), [UV gate](review/geometry/uv_gate.json).

Three resin hoses start at measured rear ports and end in ceramic/bronze plugs. Each blends from `B_Barrel` near
its socket to `B_Root` near the floor; plugs stay fixed in actor space. Their small shared 256² atlas uses the same
region-ramp system. Two narrow emissive filaments run along each hose.
The engine's rigid attachment path does not deform skinned attachments, so the cables are a **separate skinned mesh
in the same actor GLB**, with visibility keyed by clip. The ten mobile clips hide it; ten `Coupled_*` copies reveal it.
This keeps one shared body and allows the row swap to remove all three hoses. `export/hes_bulwark_cables.glb` is a
standalone static copy with variants and LODs for the map integrator; it is not a second runtime attachment.

## Rig and verification

21 bones, including three muzzle sockets. Body plates have one rigid influence; cables have at most two normalized
influences. Hip/knee/foot pivots come from the measured joints. The housing pitches at its flank trunnions; the two
barrels recoil independently. [Library query](review/animation_library.json): available humanoid clips cannot drive
four mechanical legs; the quadruped playbook's local IK route is used.

| Clip | Seconds | Motion |
|---|---:|---|
| Standing / Fidget | 4 / 4 | Narrow / wider turret scan, planted feet |
| Walking | 1.2 | Diagonal gait, .65 m travel per cycle, 65% stance |
| Running | .8 | .9 m cycle, 44% stance, actual aerial phase |
| Attack / Cast | .6 / 1 | Twin shot at .166667 / .5 s |
| Sweep | 1.5 | D7's scripted sweep |
| Hit | .6 | Suspension/head reaction |
| Death / Dead | 1.4 / 1 | Collapse, then exact held endpoint |

Final exported checks sample **all 20 clips at 60 Hz in all four LODs**: worst floor penetration **0.36 mm**,
exact loop and Death/Dead continuity, grounded plugs, correct cable visibility, normalized weights and finite positions.
The source rig's rigid-edge relative error is under .000017, maximum IK reach .99804, planted drift .29 mm walking /
.69 mm running; Running has six samples with all feet above 1 mm. [Final gates](review/final_gates.json),
[source rig](review/geometry/rig_gate.json), [foot plants](review/geometry/upload_gate.json).

All clips pass cable/leg, cable/chassis, exposed-barrel/chassis and head-above-bearing/chassis intersection checks.
The deliberate head bearing is excluded below rest z=2.1 m; hip/breech interlocks are separately recorded in the
[source component gate](review/geometry/contact_components.json). Aim was checked from −15° to +12°; bindings use
−10° to +8°, reserving space for keyed pitch. Whole-actor tactics retain 60°/s traverse and zero added barrel yaw.
[Final contact and aim checks](review/geometry/final_contacts.json).

**1,280 animation samplers pass** strictly increasing finite time checks. Runtime, standalone cable and intermediate
LOD0 exports report **zero inverted closed parts**. The final GLB reimports and is packed into
`export/hes_bulwark.blend`; construction/UV authoring files remain under `work/`.

| Mesh | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body | 11,160 | 5,580 | 3,784 | 2,136 |
| Coupled cables only | 1,824 | 911 | 727 | 545 |

Shared far-LOD repair selected `r35_20` after two more aggressive body reductions failed. Reprojected colour,
normal, ORM and region masks are retained. Every tier passes the final switch-image thresholds: worst body
outline changes **3.3 / 5.9 / 7.6%**, colour differences **13.9 / 14.5 / 8.1**. Cable changes are
**3.8 / 2.7 / 8.9%**, colour **11.4 / 4.9 / 6.3**. The far cable ratios deliberately retain more than half to
preserve thin curves and plug floor contact; the smaller versions failed these gates. Matching shadow LODs are
inset and winding-corrected. [Body tiers](review/final_lods/scores.tsv), [final cable audit](review/cable_lods_final/scores.tsv).
The cable rows in the earlier `final_lods` table are the rejected reduction; `cable_lods_final` supersedes them.

## Staging and review handoff

Rows **10107 / 10141** now bind the shared `hes_bulwark.glb`, scorched variant, scale **100.01103145**, intended
standing height **384** (160 × Heavy 1.2 × Bulwark 2), measured feet/chassis radius **321**. Both have Cast and Sweep;
mobile movement uses Walking/Running, coupled movement uses Coupled_Standing. Muzzle events and sockets are explicit.
Only these rows and this model source were changed in `hesper_stage/monsters.yml`; existing tactics were preserved.
Locked `stage.py` succeeded: one changed GLB and 35 cooked textures. No assets_dev installation or git staging.

`rebuild_all.sh --scenarios-only`: **73 passed, 0 failed**. [Run summary](review/scenarios.log).
Desktop setup passed, then `tools/run_game.sh` failed before map load with `SDL_Init failed: No available video device`.
[Retained run record](review/desktop/run.json), [native log](review/desktop/game.log), [headless preparation](review/desktop/prepare.log).
No desktop screenshot was produced, and no GPU/model-load visual claim is made.

The viewer has three palette copies, all twenty clips, reference images, bones/wireframe and a valid findings array.
Manifest hashes, clip names, dependency paths and JS syntax pass static checks. The integrator accepted the viewer model and palettes; these commands remain available for repeat checks (rule 9):

```sh
python3 tools/run_creature_review.py --project level_generation/creatures/hes_bulwark_codex check
python3 tools/run_creature_review.py --project level_generation/creatures/hes_bulwark_codex playback
```

Desktop rerun from a desktop-enabled session (no build needed):

```sh
flock -s output/hesper_stage/locks/engine_build.lock flock -s output/hesper_stage/locks/stage.lock \
  ./tools/run_game.sh --isolated bulwark-smoke --world hesper --map hes_d07.blv \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --position 4300 6200 -512 --yaw-radians 0.8 --pitch-degrees 3 --warmup 3 --seconds 15 \
  --set debug.immortal=true --set debug.screenshot_delay_seconds=4 \
  --set debug.screenshot_path="$PWD/level_generation/creatures/hes_bulwark_codex/review/desktop/d07.png"
```

**Map-owner follow-up:** D7 actors 22/23 still store the stand-in height **320** and radius **120**. The map owner
must regenerate their placement to get the new 384/321 dimensions; this worker did not edit or rebuild the map.
D7 also has three old `d07_bulwark_cable_*` decoration spans and a separate wreck. Align/replace those map-owned
spans against the new ports/plugs during native review. Actor plugs are fixed in actor space, so whole-actor
traverse rotates them; a world-fixed power-feed join is not established by this model-only change.
The map joins and the user-owned D7 desktop check remain. The accepted model's specular-mask metadata fix is documented below.

## Reproduction

Use `tools/creature_workspace.py claim/run/release` for all project writes. Meshy remains integrator-only.
Blender: `/snap/blender/current/blender --background --factory-startup --threads 4`, bounded by `timeout`; after the
script use `--python-expr 'import sys,os;sys.stdout.flush();sys.stderr.flush();os._exit(0)'` to avoid shutdown hangs.

Geometry/rig: `geometry.py -- build`, `geometry.py -- study`, `rig.py`, `prepare_uv.py --dump`, `pack_uv.py`,
`prepare_uv.py`, `check_contacts.py`, `check_upload.py`. `pack_uv.py` uses the existing xatlas environment.
Finish: `adopt_texture.py`; shared `bake_creature_ao.py` (1024, reach .08, CPU 96 samples); `compose_textures.py`,
`compose_cable.py`, `finish_model.py`, `initial_lods.py`, `materials.py` on the initial LOD export,
`repair_bulwark_lods.py hes_bulwark`, `fix_cable_lods.py`, `finish_runtime.py`, `fix_bulwark_winding.py`,
`final_gate.py`, `final_contacts.py`, `check_uv_gutter.py`, `deliver.py`, `save_master.py`.
The repair script uses the existing pymeshlab/xatlas interpreter through `LOD_REPAIR_PYTHON` and bounded audit wrapper.
`viewer_bake.py` and `audit_lods.sh` produce the retained palette/cable switch comparisons. Raw returns are never overwritten.

## Specular-mask export correction (2026-10-23)

The integrator's native run caught invalid flags on materials 12–14 (`Bulwark_Energy_A/B/C`): a specular mask
requires a metallic-roughness texture, which these factor-only energy materials deliberately do not have.
Removed the flags; `scripts/materials.py` now emits them only when that texture exists and asserts the contract.
Updated the runtime/static exports, viewer copies, derived resume checkpoints and editable master. Binary payloads
are unchanged: no geometry, textures, animation or emission edits. Viewer/artifact hashes are refreshed.
[Correction record](review/specular_mask_fix.json). The stage's exact model-rule validator passes all delivered
GLBs and a fresh run of the corrected generator. Native rendering remains for the user's D7 desktop check.

After the correction, the models entry and rows 10107/10141 were restored from the integrator's hold. Locked staging
passed (one GLB rewritten, zero textures recooked); the cooked energy materials pass the contract.
The fresh `--scenarios-only` run passed **73/73**, with zero failures: [log](review/specular_scenarios.log).
The user runs D7 desktop verification; no desktop run was attempted for this correction.

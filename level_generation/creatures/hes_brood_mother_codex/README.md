# The Brood Mother — Hesper 10111

Round 2 of [CREATURE_BUILDS](../../../design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md), rules 1–10.
Project identity `hesper:brood_mother`; one stationary tier, ×1.5.
**2026-10-23: textured queen/cradle, six clips and four LODs built; row 10111 staged. Integrator visual review remains.**

## Current assembly

The [P2 egg-sac ruling](../../../design/kreegan_world/WORK_PACKAGES/requests/P2.md) and the user's follow-up are
authoritative: **queen and resin cradle only, three empty flat-topped sockets, no eggs in this GLB**.
The independent 10130 Brood Sac actors retain their own geometry, orange glow and death/shield/wave behaviour.
D9's owner changes their placements after applying the queen's final map transform; this project changes no map.

The original `brood_mother_geometry_v2` download is preserved under `meshy/`, with its receipt in
`creature_3d_progress.json`: 16,292 triangles, no UVs, materials, rig or clips. Local work fitted the stalks,
removed cap obstructions, added closed level pads and an inset skin backing beneath the belly-plate gaps,
and restored the missing left little finger. Both hands were fitted clear of the belly. The original four
left-hand digits and five right-hand digits remain; fingers are weighted by connected branches.
The queen retains the returned asymmetric seated pose. No replacement head, shared caste body or egg was added.

The swollen belly, resin cradle and pads are static. The upper body and arms have a fitted source-frame rig;
the head and full horn arcs move rigidly together. The long back plates blend into the seated torso/base.
The cradle is a coarse open resin lattice; the shared atlas carries its ribs, chitin borders and plate patterns. The belly has a separate closed backing; intentional gaps between cradle ribs remain open.

Selected outputs:

- Runtime model: [export/hes_brood_mother.glb](export/hes_brood_mother.glb), **12,043 / 6,019 / 3,010 / 1,505 triangles**, 50 bones.
- Editable textured rig: [export/hes_brood_mother.blend](export/hes_brood_mother.blend), packed maps and semantic mesh parts.
- Retained untextured gate source: [work/texture_ready.glb](work/texture_ready.glb).
- Static, unrigged upload: [texturing/brood_mother_upload.glb](texturing/brood_mother_upload.glb).
- Input hashes, mesh counts and verified face correspondence: [review/upload_manifest.json](review/upload_manifest.json).
- Selected five-view references: `references_hd/cradle_only/`; original approved sheet: `references_hd/concept.png`.
  `references_hd/generation_runs.json` retains prompts, hashes and superseded candidates. The old integrated-sac
  branch and requests under `requests/superseded/` must not be submitted.

## Measured empty sockets

Origin: cradle base on the floor; Blender metres **+Z up, −Y actor forward, +X actor left**.
The model reaches 4.50 m; intended binding scale 100 gives 450 game units, already including the ×1.5 tier scale.
Do not multiply that scale by 1.5 again. The three coordinates locate the **top surface**, where each sac's
base origin belongs. They supersede the earlier unmeasured ±2.20 / rear-1.80 targets, which intersected the
returned queen's arm/crown space. Socket bones `Socket_Sac_left/right/rear` remain fixed on `Base`.

| Socket | Blender metres (X, Y, Z) | glTF metres (X, Y, Z) | Local game units (left, back, up) |
|---|---|---|---|
| Left | (2.70, −0.20, 2.20) | (2.70, 2.20, 0.20) | (270, −20, 220) |
| Right | (−2.90, −0.20, 2.20) | (−2.90, 2.20, 0.20) | (−290, −20, 220) |
| Rear | (0, 3.10, 2.90) | (0, 2.90, −3.10) | (0, 310, 290) |

Each 48-sided pad has a 0.64 m outer radius, **0.6386 m inscribed flat radius**, and a closed tapered underside
that joins its stalk. No prong enters the usable top. Exported measurements and all-clip clearance are in
[socket_layout.json](socket_layout.json) and [review/texture_ready_sockets.json](review/texture_ready_sockets.json).
The clearance check samples both models at 60 Hz, encloses every sac pose and yaw in its measured cylinder,
and checks actual queen triangles against that cylinder's full height, including edges between vertices.
The existing sac's maximum radius is 0.579 m and height 1.2313 m. The pads leave about 0.060 m of support margin.
The final report records the separate clearance above each pad; the left result is a conservative lower bound.

The unchanged sac reads as an orange/dark mottled egg on simple plum tripod legs with thin pale braces; it is
less ornate than the reference's bone cup. This mismatch is reported, not repaired here.
D9 must retain actor height, targeting and shield/wave behaviour after moving its three existing 10130 actors.
The binding uses `fixed_yaw_degrees: 0` and `yaw_offset: -1.570796327`, matching D9's authored east facing.
The existing runtime supports this; no engine change or additional runtime head look is needed.

### D9 placement handoff (map unchanged)

For the current queen actor 77 at **(4300, 2300, −2944)**, fixed east, scale 100, the engine transforms Blender
(X,Y,Z) to world offset **(−100Y, +100X, +100Z)**. These are the sac **base origins**, not their centres:

| Socket | Required world position |
|---|---|
| Left | (4320, 2570, −2724) |
| Right | (4320, 2010, −2724) |
| Rear | (3990, 2300, −2654) |

The current actors 78–80 remain on the floor at their old placements. D9's owner must move them, recompute their
sectors and ensure the elevated Z is retained; a generic floor snap would put them back below the pads. Preserve
ids/groups, targeting, shield linkage and wave/death logic. The binding keeps height 450, collision radius 90,
`special: '0'` and `never_staggers` from the existing stage row. No other monster or map was edited.

## Rig and motion checks

[ANIMATION_PLAN.md](ANIMATION_PLAN.md) records the selected clips and rejected backward fall.
Standing, Fidget and Hit adapt local library motion at its source rate. Attack is a seated acid-spit lean;
Death settles backward into the cradle and lowers the head; Dead holds its exact final pose.
Walking/run will map to Standing because speed is zero. No locomotion or head-bob job is needed.

The [final numeric report](review/texture_ready_gates.json) is bound to the preview GLB hash. It checks all six
clips at 60 Hz, including half frames and endpoints: arm/hand and upper-body edge stretch, wrist swing and arm
roll, fixed base surfaces, floor contact, real surface contacts, loop/return continuity, Death→Dead continuity
and the mouth-release time. Closed belly skin uses containment; the open cradle uses the shared surface probe.
It is a seated upper-body adaptation of the shared gate evaluator, without fictitious leg bones.
Contact tolerance is 2 mm; a passing result does not mean every open-shell distance is exactly zero.
`review/winding.txt` reports zero inverted closed parts. The upload has no armature, animations or materials;
its triangles match the animated rest mesh within 0.01 mm, with a one-to-one face correspondence.

Reduction trials: 14,486 / 12,043 / 9,598 triangles. The selected middle trial retains the cradle's broad ribs
better than the smallest trial; face, hands and moving deformation regions were protected. Original masters
and trial blends remain under `work/`. `review/reduction_*.json` records surface error rather than claiming
that reduction changes no vertices. Static CPU clay inspections are under `review/final_*` and `review/ownership_*`.
These are geometry diagnostics, not browser playback or native game acceptance.

## Textures, LODs and Meshy receipts

**15 / 60 credits spent; no pending or planned jobs.** The integrator completed geometry v2 (5 credits) and
`brood_mother_texture_v2` (10 credits). Original downloads and receipts remain under `meshy/` and in
`creature_3d_progress.json`; do not resubmit them. No paid animation or head pass was used.

`transfer_uv.py` verifies all **12,021 returned triangles** against the retained rig, including winding and corner
correspondence (maximum error 0.0032 mm). Meshy omitted 22 small faces. All 12,043 rigged faces remain: the omitted
faces get padded atlas patches whose colours/MR interpolate their exactly coincident surviving corner samples,
choosing the best-facing adjacent UV at a seam. Their normals are flat in the fresh patch tangent frame.
The patches cover about 0.16 m² of the 227 m² mesh, below 0.1%; original geometry, weights and actions are unchanged.
See [review/uv_transfer.json](review/uv_transfer.json). No unchecked nearest-vertex UV transfer was used.

`compose.py` writes one 2K base and 1K normal, metallic/roughness/specular and padded RGBA region mask, plus
material-class labels. R/G/B regions are violet skin/resin, ivory chitin and gold trim; `hbm` is the only variant.
Ivory/gold ramps reduce the return's brown cast. No per-tier runtime baked skin or egg emission is added.
MR red is the current engine's **specular mask**, not AO; `finish_material.py` restores it after Blender's exporter
packs metallic/roughness. Normal-map convention is measured and green flipped (−0.998 original, +0.71 final).
The paint remains coarser and less ornate than the illustration, especially on the face and resin lattice.

`repair_lods.py` is the shared `lod_repair_claude/scripts/repair.py` route with project-local paths and its audit
inside the leased Blender process. LOD2/3 have their own 512/256 atlases; the first 25%/12.5% rung passes:
outline errors **3.9% / 6.7%**, colour differences **14.1 / 13.5**. Near/far shadow meshes use the shared safe tuck.
LOD0/1/2 rest floor minimum is 1.67 mm; LOD3's coarse base starts 22.86 mm above origin. Its outline is checked at
its switch size, not as a close-up model. No walk/run head-bob pass applies to a stationary queen.

[review/delivery_checks.json](review/delivery_checks.json) verifies the actual final LOD0 against the prior gated
rig: bijective triangle correspondence, **zero rest/posed position error at 60 Hz across every clip**. Thus the
recorded arm/hand, contact, horn, base, socket and timing checks still apply to the delivered model. It also checks
finite attributes, influence sums, materials, variant, LOD chains and winding (**0 inverted closed parts**).
The far-LOD audit is visual/texture coverage, not a claim that coarse LOD surfaces reproduce LOD0 contacts exactly.

## Review and staging

[review/viewer/](review/viewer/) is the existing Kreegan viewer with the final model hash and six durations.
Its GLB has `hbm` ramps baked **only for the viewer**; the staged export retains shared maps/ramps. Local imports,
manifest assets and JavaScript syntax pass. Offline Blender texture views are `review/textured_final_*` and
`review/textured_upper_*` (Attack release). Browser playback/capture remains with the integrator under rule 9:

```sh
python3 tools/run_creature_review.py --project level_generation/creatures/hes_brood_mother_codex check
```

`integration/actors.yml` binds row **10111** with Standing/Fidget/Attack/Hit/Death/Dead, Walking/run = Standing,
a mouth release at **0.7667 s**, cast = Attack, scale 100 and fixed east facing. The stage requires stride fields
even for a stationary actor; both are 1. The first stage attempt caught their omission; the corrected attempt
passed (`review/stage.log`). The shared edit re-read `monsters.yml` under its exclusive lock, changed only 10111's
binding and added the own model path, then verified all other parsed content remained identical.

The minimized desktop smoke run's headless preparation passed, but SDL could not open a video device in this
sandbox. `review/desktop_smoke/` preserves its logs. **Native model load/draw, browser playback and artistic
acceptance remain unverified**; the integrator should rerun the same smoke command on the desktop and inspect
`game.log` for `Actor model load failed`. No screenshots or performance checks were run.
Desktop smoke command (minimized; no screenshot request):

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  ./tools/run_game.sh --isolated brood-mother-smoke --world hesper --map hes_d09.blv \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" --position 5100 2300 -2944 \
  --yaw-radians 3.141592654 --pitch-degrees 0 --warmup 1 --seconds 3
```

**76/76 scenarios passed, runner exit 0**, including D9's `brood_pits_descent`.
Evidence: `review/scenarios.log` and `review/scenarios_summary.json`. Two preliminary sweeps were interrupted
by concurrent runner/binary replacement; their logs are retained. The final sweep used a fixed in-memory copy
of the current `rebuild_all.sh --scenarios-only` and held both shared locks throughout. The snapshot and binary
hash are recorded; no shared runner or engine file was edited.

### Reproduction

Claim this project with `tools/creature_workspace.py` (identity `hesper:brood_mother`) before writing.
Blender steps use `tools/run_creature_blender.sh --token TOKEN <project>/scripts/<script>`; other writing commands
use `tools/creature_workspace.py run --project <project> --token TOKEN -- <command>`.
From the retained `work/texture_ready.blend`:

1. `transfer_uv.py` (Blender), then `compose.py` (system Python).
2. `export_runtime.py` (Blender); `tools/prepare_actor_glb.py work/runtime_lod0.glb work/prepared_lod0.glb`;
   `finish_material.py` (system Python).
3. `initial_lods.py` (Blender), then shared `claude_shared/region_variants.py work/initial_lods.glb
   work/hes_brood_mother_initial_coloured.glb textures/hbm_ramps.json --extra BroodMotherSurface openyamm_specular_mask=true`.
4. `repair_lods.py` (Blender; `LOD_REPAIR_PYTHON` selects an existing interpreter with pymeshlab/xatlas/numpy/scipy/Pillow),
   `finish_runtime.py`, `check_delivery.py` (system Python).
5. Existing `hes_bulwark_codex/scripts/viewer_bake.py export/hes_brood_mother.glb review/viewer/hes_brood_mother.glb hbm`,
   then `prepare_viewer.py` and JavaScript syntax check. This reads the other project's helper, changing no other project.
6. `stage_rows.py` (system Python) takes the stage lock and runs `stage.py`; `check_staged.py` verifies the cook; then
   `level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only` (it takes shared stage/engine locks).

Paths in steps 2/3/5 are relative to this project; invoke helpers by their repository paths. This run reused `/tmp/lancer_lod_venv/bin/python` for the LOD dependencies; set `LOD_REPAIR_PYTHON` explicitly
when reproducing it. The earlier geometry pipeline remains documented in `ANIMATION_PLAN.md` and the retained scripts/reports. `check_handoff.py` checks the
historical pre-texture handoff; use `check_delivery.py` for the current output.
No engine changes, assets_dev writes, Vulkan, performance runs or git staging.

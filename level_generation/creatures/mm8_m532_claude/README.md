# MM8 Centaur — Claude 3D playbook

Native family **m532**, descriptors **Centaur A/B/C** (monster IDs 100–102), palette groups
533/534/535. Complete creature production requested 2026-10-15. Agent technical and visual review
is recorded separately from user artistic acceptance in `creature_3d_progress.json`.

## Review and deliverables

- [Interactive viewer](http://127.0.0.1:8901/level_generation/creatures/mm8_m532_claude/review/viewer/):
  all three tiers, nine actions, frame stepping, speed control and native sprite references.
- [Close views](review/close_review.png), [motion sample sheet](review/motion_review.png), [corrected fall](review/grounded_review.png),
  and [captured live playback](review/playback/playback.json). The playback receipt links every captured frame.
- Editable assembled master: `work/centaur_master.blend` (packed textures, rig and all actions).
- Runtime sources: `export/mm8_centaur.glb`, `export/mm8_centaur_bow.glb`,
  `export/mm8_centaur_quiver.glb`. Bow and quiver are separate rigid attachments; the body retains
  the moving string, nocked arrow, launch and casting sockets.
- Portable assembled tier previews: `review/viewer/centaur_a.glb`, `centaur_b.glb`, `centaur_c.glb`.
  They use the same prepared geometry and sampled actions with the palette ramps baked for three.js.
- Body/head base colour, normal, specular/roughness/metallic maps, semantic classes, masks and
  native palette ramps are in `textures/`. Selected export hashes: `review/asset_validation.json`;
  installed source/runtime hashes: `review/installed.json`.

## Source and construction

`native/inventory.json` retains exact source names, including native filename case. `native/sources.json`
and `references/` document all 160 native frames, five directions, action durations and palettes.
Selected five-view body masters and four head views, prompts, inputs and hashes are retained under
`references_hd/` and `references_head/`. The primary/front body establishes the bind pose; profile arm
projection differs modestly. The reference body is unarmed to improve geometry, while native bow,
quiver and arrows remain required components.

Meshy SmartTopology (`meshy-t2`, target 15k triangles) supplied the body. Two damaged patches were
repaired locally before rigging. The horse/human hybrid uses a local 72-bone rig with five digits per
hand, four hoof chains and a five-bone tail. A fitted bow, quiver and arrows were modelled locally.
Body and head were separately retextured through Meshy at 4K; final maps are reduced to their game
budgets. Unmodified service returns and receipts remain in `meshy/`.

**Meshy total: 25 credits** (5 geometry + 10 body texture + 10 head texture), within the 100-credit
creature budget. The first geometry request was rejected before task creation and incurred no charge.
No paid rigging or animation jobs were needed for this unsupported hybrid anatomy.

The retained source rig receives the returned body UVs by exact face correspondence. Eight
retriangulated tail faces are projected within one source UV chart per triangle, avoiding crossings
between unrelated islands. Palm smoothing preserves forearm influence; the horse belly/back owns
pelvis weights rather than opposing lower legs. Tail strips have tapered ends. Dense checks found and
corrected world/local root translation and quaternion-hemisphere interpolation before final export.
Native indoor review also caught the bow propping up the corpse. The final fall tucks the arm, lays
the bow along the floor and grounds the body independently. `review/corpse_contact.json` checks
hoof contact at 8 mm, horse flank within 21 mm, and bow clearance above the floor.

## Actions and binding

| Action | Duration | Use |
|---|---:|---|
| Standing | 2.0 s | Loop |
| Walking | 0.75 s | Diagonal trot, 1.129 m travel/cycle |
| Running | 0.6667 s | Faster trot, 2.212 m travel/cycle |
| Attack | 1.5 s | Quiver reach, nock, draw, release at 1.0 s, recover |
| Cast | 1.5 s | Free right-hand Shield gesture, impact at 1.0 s |
| Hit | 0.875 s | Within the native hit duration |
| Death | 1.75 s | Native-led rear, bow overhead, side fall |
| Dead | 1.0 s | Stationary corpse loop |
| Fidget | 1.25 s | Look and tail movement |

Stance travel is 0.70 m at duty 0.62 for walking and 1.15 m at duty 0.52 for running;
binding stride lengths divide those distances by duty to describe full-cycle body travel.
`review/stride_calibration.json` verifies compensated hoof drift from the actual export.

All actions are sampled at 48 FPS with linear interpolation and continuous quaternion signs.
Arrow visibility uses STEP scale keys. `Socket_BowRelease` follows the nock and `Socket_CastPalm`
follows the right hand. Body facing is glTF +Z; runtime yaw offset is −π/2. Head look uses Neck/Head.

Native standing alpha height 205 px × sprite scale 1.299988 / model height 2.6 m gives
**102.4990538462 world units per metre**. All three native tiers have the same scale, so each binding
uses that explicit scale. No relative scale lookup is needed for these equal-size palette tiers.
Original monster stats, attacks, spells and gameplay timing are preserved.

**Attack v2 and the bow-carry fix (2026-10-18/19, review of the reduced model in `../mm8_centaur_reduce_claude/`).**
`scripts/animate_attack_v2.py` re-authors Attack (1.5 s, release marker at 1.0 s): torso side-on after the stored
humanoid bow shot, quiver reach, nock in front of the belly, the hooked string pulled to the jaw while the bow arm
pushes out, draw elbow back along the arrow, the forequarters rearing while the bow rises to 34 deg, the bow turned in
the fist so its plane holds the shot with the string toward the chest. `scripts/carry.py` and `scripts/carry_fix.py`
then fix the bow-hand wrist of every clip (114-168 deg -> 1-33 deg) by keeping the bow's pose and re-solving the arm;
Attack starts and ends in the same hold. Gates: `scripts/attack_gate.py` (wrist, twist, arm in torso, nock, bow plane,
pops), `scripts/arm_body_probe.py`, `scripts/hold_match.py`. Masters: `work/centaur_master_attack_v2.blend` (Attack),
`work/centaur_master_carry.blend` (all clips, the current one; `work/carry_lod0.glb` is its LOD0 export). Rebuild:
`../mm8_centaur_reduce_claude/attack_v2/scripts/carry_build.sh`. Details, numbers and sheets: the reduced project's
README. Installed 2026-10-19 with the reduced model (`../mm8_centaur_reduce_claude/`, 9,149 triangles); the installed
source is no longer this project's export.

Installed through `tools/install_model.py --world mm8`, into the source and runtime MM8 model
packages. The current installer cooks runtime textures/geometry; the accepted source GLBs are
unchanged. The existing entries in `assets_dev/worlds/mm8/models/actors.yml` are preserved.

## Geometry and materials

| Mesh | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body, string, nocked arrow | 11159 | 5553 | 1967 | 629 |
| Bow | 400 | 200 | 71 | 17 |
| Quiver and carried arrows | 188 | 91 | 28 | 20 |

Four influences per vertex, 72 joints, no degenerate final triangles. Colour and shadow LOD chains
are retained, with the documented inward correction on reduced shadow meshes. The standard existing
LOD helper reduces more aggressively after LOD1. Bow and quiver remain separate during simplification
to prevent welding to the deforming string. Runtime body has one primitive per mesh and three palette
materials before the installer's back-face pass.

The packed body UV islands did not leave a safe prop swatch, so a 128 px strip extends the body atlas
to 1152×1024. The merged body/head atlas is 2208×1024 including its 32 px gutter. This small atlas
extension keeps one body draw instead of a separate prop material. Normal maps are converted to the
glTF +Y convention. ORM red is the engine's specular mask, not ambient occlusion. Only the green
harness region changes to the native violet/burgundy ramps; skin, coat and equipment remain constant.

## Verification and reproduction

`review/asset_validation.json` checks the actual delivered GLBs, LODs, palette/material coverage,
indices, finite values, influence weights, clip timelines and sockets. `review/export_probe.json`
reimports the delivered body and compares 97 poses per action with the assembled Blender source.
Maximum position disagreement is 0.034 mm; loop endpoints coincide. Measured stance target errors
are 4.2 mm walking / 10.3 mm running, below the 12 mm authoring gate. Skinning strain measurements
are diagnostics alongside visual review, not claims of perfect anatomy.

`review/viewer_check.json` records 27 successful tier/action switches with no browser errors.
`review/playback/playback.json` records 36 normal/quarter-speed front/side runs, plus 21 tier close views.
`review/actor_regression.log` records seven passing MM8 actor cases, including the centaur test for
palette/attachment coverage, sockets, nine durations, LODs, all native animation roles and unchanged
simulation state. The final focused centaur case also passes (`review/centaur_regression.log`).
During the final full-suite rerun, a newly added concurrent Dark Elf Warrior case failed while the
other seven cases passed; that unrelated failure is retained in `review/actor_regression_latest.log`. The ordinary `openyamm` build is recorded in `review/build.log`.
Native desktop records and matching model/sprite captures are under `review/native/`; see
`review/native_review.json` for the final map/camera/results inventory. The desktop checks use the
NVIDIA GPU through OpenGL/Wayland. Original sprites were visible in the outdoor comparison, but
not in the indoor spawn baseline (both Agar and an MM8 house were tried). Indoor model rendering
and contacts were reviewed; indoor sprite comparison is therefore a recorded baseline limitation. Android and Vulkan were not built or tested for this task.

The `pose_*`, `geometry_*` and `stress_*` images directly in `review/` are earlier diagnostic checkpoints;
use the viewer, `playback/` and native records for the final appearance.

To reproduce from retained service outputs, claim this creature workspace and run project-local scripts
with the ownership token. `transfer_uv.py` → `refine_geometry.py` → `animate.py` → `extract_uv.py` →
`compose_textures.py` → `export_model.py` → `prepare_runtime.py` → `build_lods.py` →
`postprocess_runtime.py` → `build_viewer.py` → validation. Blender scripts run through
`tools/run_creature_blender.sh`; the plain Python texture/postprocess/validation scripts run through
`tools/creature_workspace.py run`. Earlier geometry/rig/equipment steps and their inputs are retained
for deeper revisions. Repeat affected export, playback and native checks after any change, then install
all three export GLBs with `tools/install_model.py`; never copy back from runtime assets.

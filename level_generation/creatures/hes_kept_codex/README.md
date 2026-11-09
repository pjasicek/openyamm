# Hesper Kept (Codex)

## Current state — accepted and complete, 2026-10-24

**Kept build accepted and complete; all eight rows staged.** The integrator accepted the original
bodies, heads, clothes and clips in P1. The rejected placeholder add-ons are replaced by the concept's thick,
snug bone/dark-metal collar with spikes and a vertical orange throat slot, a fitted ivory breastplate and straps,
a textured iron/wood pick, and a banded club. Both weapons have fitted closed grips. The Enforcer now uses the
local **MaceAttackR1 overhead swing**, exported as `Kept_ClubAttack`; the club leads the impact at **0.316667 s**.

[Current review sheet](review/final_review.png), [five-outfit viewer](review/viewer/index.html),
[collar and plate close-up](review/kept_c_Standing_0_head_three_quarter.png),
[club impact](review/kept_c_Attack_0.316667_body_left.png), [export checks](review/runtime_validation.json).
The viewer contains the actual runtime geometry, attachment transforms and eight state roles. Its baked tier
colours are review-only; runtime tiers share maps and use region ramps. The integrator's feedback file is preserved.

**Regression: 77/77 Hesper scenarios passed, exit 0**, with no WIP failures; decoration-ID and actor-size checks
also passed. [Stage log](review/addons_v2/stage.log), [scenario log](review/addons_v2/scenarios.log),
[handoff validation](review/finish_validation.json). The requested `--scenarios-only` run made no engine/map build.
**Integrator acceptance, 2026-10-24:** replacement equipment and the Enforcer’s `MaceAttackR1` playback accepted.
Desktop smoke passed **D4, D6, D11, D16, Out1 and Out3**, every map that places the Kept: all exit 0, zero
model-load or LOD errors. See [the P1 decision](../../../design/kreegan_world/WORK_PACKAGES/requests/P1.md#integrator-answer-the-kepts-replacement-equipment-2026-10-24)
and [integrator playback frames](review/integrator_club_20261024.jpg). No work remains; the project is released.

## Exports and staged rows

| Outfit / part | Rows or use | Export (`export/`) | LOD0 / 1 / 2 / 3 triangles |
|---|---|---|---|
| Labourer / Miner core | 10060–10061, 10200–10201 | `hes_kept_m_ragged.glb` | 10,818 / 5,409 / 2,703 / 1,347 |
| Enforcer core + skinned plate | 10062, 10202 | `hes_kept_m_enforcer.glb` | 11,802 / 5,901 / 2,949 / 1,467 |
| Freed male, unchanged | 10260 | `hes_kept_m_freed.glb` | 10,330 / 5,164 / 2,581 / 1,288 |
| Freed female, unchanged | 10261 | `hes_kept_f_freed.glb` | 9,487 / 4,743 / 2,371 / 1,182 |
| Collar | all collared tiers | `hes_kept_collar.glb` | 1,232 / 616 / 307 / 149 |
| Pick | Miner | `hes_kept_pick.glb` | 264 / 132 / 66 / 32 |
| Club | Enforcer | `hes_kept_club.glb` | 372 / 186 / 92 / 46 |

A/B/C share exactly the same male core. C embeds the separately skinned `KeptPlate` mesh
(**984 / 492 / 246 / 120** triangles); it no longer has a rigid plate attachment. The obsolete plate GLB is retired
from exports and registrations, with a historical copy under `work/addons_v2/baseline/`.
Complete equipped LOD0 totals are **12,050 Labourer, 12,314 Miner and 13,406 Enforcer**, below 15k.

[Bindings](integration/actors.yml) retain all row scales, collision dimensions, tactics and strides. The eight
row bindings are in `hesper_stage/monsters.yml`; only our obsolete plate model registration was replaced by the
Enforcer export ([preservation check](review/addons_v2/stage_binding_change.json)). Seven exports are staged.
`attack_ranged` aliases melee; these rows have no ranged attack or cast. Nothing was installed into `assets_dev`.

## Equipment, textures and retained bodies

Four **1536×1024 built-in imagegen HD prop masters** are retained in `references_props_v2/`, with prompts/hashes in
`generation_runs.json`. Locally fitted meshes use front/back projection into padded **1K** maps under
`textures/props_v2/`: base colour, restrained normal relief, and packed specular/roughness/metallic. The collar's
orange slot uses `emissiveFactor`, with no emissive texture. All materials remain opaque and single-sided.
The packed red specular masks survive export (77 for collar/pick/club, 45 for plate); metallic blue is zero.

The collar is rigid on `Kept_Collar`, a fitted carrier parented to `B_Neck`. It follows the covered neck band
through every clip. The plate and its shoulder/torso straps are skinned to the chest. The iron pick head is turned
around its held haft to clear the face while retaining the grip. All three rigid props are transformed once with
the runtime inverse bind matrix; maximum roundtrip error is **0.06 µm**.

The accepted body/head LOD0 atlases are **pixel-identical**, and both freed exports are **byte-identical** to the
accepted base ([contract checks](review/addons_v2/export_contract.json)). The shared collared male core needed
hidden forearm closure beneath the sleeve, interpolated neck topology cuts and covered neck/shoulder weights
for the larger collar and overhead strike. The head motion was retained. Equipped collapse is vertically fitted
as a whole to clear the longer club while preserving relative pose and grip.

Five body/head **1024²** texture sets remain editable in `textures/`: ragged male, freed male, freed female,
shared male head and female head. UV-only transfer from paid returns onto the fitted rigs had maximum position
mismatch **1.05 µm**. The female's accepted hair-cap repair remains unchanged (35 vertices, maximum move 4.52 mm).
Neck seam mean RGB8 errors are **0.89 / 1.02 / 0.35** for ragged male / freed male / female. Runtime body/head
atlases are **2080×1024**, including a 32-pixel gutter: the existing shared material-merge path's documented
exception to the power-of-two preference. The three collared tiers share base/normal/material maps and region ramps.
[Texture composition](review/texture_composition.json), [female head](review/freed_f_Standing_0_head_front.png).

## Motion and checks

| Role | Local source | Duration |
|---|---|---:|
| Standing / Fidget | RelaxIdle / RelaxYes | 2.0 / 0.6667 s |
| Walking / Running | Mixamo Walk / Standard Run | 1.0 / 0.7333 s |
| Unarmed attack | UnarmedAttackR1 | 0.8 s |
| Pick attack | MaceAttackR3 | 0.8 s |
| Club attack | MaceAttackR1 | 0.8 s |
| Hit | UnarmedGetHitF1 | 0.5 s |
| Death / Dead | UnarmedDeath1 / endpoint hold | 1.3 / 0.0333 s |

Collared exports contain **17 actions / 60 bones**, including armed carry variants and four carrier bones;
freed exports retain **8 actions / 56 bones**. Source durations are preserved: collared keys bake at 60 Hz to retain
half-frame equipment fitting; freed keys remain at 30 Hz. Up to eight normalized influences protect heads/hands,
an engine-supported exception to the four-weight preference. Impacts: **0.333333 s unarmed, 0.283333 s pick,
0.316667 s club**. Male walk/run strides **1.71954 / 2.13882 m**, female **1.81623 / 2.10349 m** are unchanged.

- [Final gates](review/addons_v2/final_gates.json): all **17 collared actions**, complete props sampled at half frames;
  **zero closed-skin penetration**, arm p99 maximum **1.837×**, hand stretch maximum **3.472×**. Source-rest joint
  frames remain exact; closed arm skin is manifold and finger heads/midpoints stay inside. Wrist/twist and
  source-relative 48 Hz jerk checks pass. Open-shirt proximity under the plate is reported separately.
- [Runtime floor](review/runtime_floor.json): **4,260 poses, five outfits × eight roles at 120 Hz**, all pass.
  Equipped death also passes the tighter −2 mm gate; run flight is intentional.
- [Export validation](review/runtime_validation.json): **zero inverted closed parts and zero degenerate triangles**,
  finite attributes, normalized weights/quaternions, increasing key times, valid four-level LOD chains,
  shared A/B/C body geometry/maps, correct packed material channels and all viewer attachments present.
- Shared far-LOD reduction/rebake/score route passes first ladder **r25_12** for both revised bodies. Revised
  worst silhouette change **2.8%**, RGB error **4.4/255**. Freed LODs retain their earlier passing results.
  [LOD comparison](review/lod_comparison.png); records under `work/lodrep/hes_kept_*_addons_v2/result.json`.
- Actual assembled runtime CPU renders inspect front/quarter/back, collar, straps, grips, club wind-up/impact,
  pick impact and equipped collapse. The [visual record](review/final_visual_review.json) identifies exact hashes.

## Meshy jobs for the integrator

**None pending; no new jobs needed for this revision. Do not resubmit existing jobs.**
**70/100 credits spent, 30 remain**: two Smart Topology jobs (5 each), two successful rigs (5 each), five retextures
(10 each). Male rig v1 was rejected before charging; v2 succeeded. The nine successes, uncharged rejection,
receipts and paid inputs/returns are unchanged. All **80** receipt-bound hashes were rechecked.
[Canonical progress](creature_3d_progress.json) and [job manifest](meshy/job_manifest.json) agree.

## Resume / reproduce

Current editable master: **`work/addons_v2/equipped.blend`** (candidate actions retained).
Selected production master: **`work/addons_v2/final.blend`** (17 actions, selected club swing named for export).
Freed masters remain `work/{male,female}/runtime_freed.blend`. `work/addons_v2/baseline/` preserves the previous
accepted body exports and rejected equipment for comparison. Older `runtime_ragged.blend`, `build_final.sh` and
pre-revision attachment checks are historical; replaying that old finish chain restores the placeholders.

Claim the workspace with `tools/creature_workspace.py`, export `CREATURE_3D_TOKEN`, and use `scripts/step.sh`
for guarded Blender operations. It applies a 300-second timeout and forced exit after saving, including failure
exit handling. Do not remove lock files. **`scripts/build_addons.sh`** reproduces final exports/LODs/materials,
bindings, viewer and runtime validation from the saved equipped master. Set `LOD_REPAIR_PYTHON` to a Python with
pymeshlab/xatlas (this run: `/tmp/lancer_lod_venv/bin/python`). Full replay is unnecessary for review.

Viewer revision **`kept_addons_20261024`** uses content-hashed URLs. With the repository server running:
`http://127.0.0.1:8912/level_generation/creatures/hes_kept_codex/review/viewer/`.
The integrator completed viewer acceptance and the staged desktop smoke. Future reviews can use the shared
`python3 tools/run_creature_review.py --project level_generation/creatures/hes_kept_codex check` / `playback` workflow.
Keep `review/viewer/feedback/user_feedback.json`. No engine code/build, Vulkan or git staging was performed.

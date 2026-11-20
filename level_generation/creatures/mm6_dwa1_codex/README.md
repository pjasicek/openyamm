# MM6 BDwarf / dwa1 — Codex batch handoff

> Current revision: **Review round 8 — running height**, SHA-256 `7cfa9f965984dc2ef9d03b713dcf22ffc6f5f4a66e370abef09177694a9bd5a3`.
> Running pelvis minimum/mean: **92.51% / 95.58%** of Standing (previously 84.04% / 85.59%).
> Contact L/R: **36.46% / 39.06%**; double flight **24.48%**; highest lowest-sole gap **77.66 mm**.
> Seven other clips, mesh, textures and axe are unchanged. `stride_length` is now **0.455484**.
> Bindings, skin weights, loop closure, pelvis/head smoothness and viewer pass; shared gate exceptions remain.
> [Round 8 handoff](HANDOFF.md#review-round-8-running-height) · [Running sheet](review/round8/Running_sheet.jpg).

**Integration note:** the engine shares stride between Walking and Running. The required run-matched binding also
changes the accepted Walking clip's runtime cadence by **1.954×**, although all Walking keys remain byte-identical.
No engine change was made. This consequence needs the orchestrator's native review; no blanket regression pass is claimed.

This round follows the source's vertical excursion at dwarf leg scale, rebased to the Standing pelvis, with 35% designed
stance per foot. The source's paired foot lifts set flight height; the old 40 mm cap is removed. An integrated heel/toe
contact pivot keeps the boot planted through its roll. Source hunch offset is discarded because the library uses the
Warrok rig. These unattended fitting decisions and all measurements are in [fitting.json](review/round8/fitting.json).

The original [sprite-restore project](../mm6_dwa1/) remains read-only. No installation, game launch, build or commit.

## Deliverables

- [Body runtime GLB](export/mm6_dwa1.glb): 57 joints, eight clips, three tier variants, four colour and four shadow LODs.
- [Axe attachment GLB](export/mm6_dwa1_axe.glb): modelled crescent bit, rear spike, bevel, socket, collars and wrapped
  grip; 2,119 triangles at LOD0 and a detailed 1K material. Attach to the body's `Axe` node.
- [Packed editable Blender master](export/mm6_dwa1.blend): re-import of the prepared runtime LOD0 with corrected
  glTF normals, body/axe separated for editing, all eight clips, embedded textures.
- [Exact actor entries](integration/actors.yml), [proposed regression](integration/regression.md),
  [playbook notes](integration/playbook_notes.md).
- [Interactive viewer](review/viewer/index.html), [front sheets](review/clips_front.jpg),
  [side sheets](review/clips_left.jpg), [three-quarter sheets](review/clips_three_quarter.jpg).
  Each role also has a `review/<Role>_sheet.jpg`; hand closeups include Standing and the actual impact.
- [HD axe design](review/axe_design.png), [PBR axe closeup](review/axe_closeup.png), [grip closeup](review/axe_grip_closeup.png).

Serve the **repository root** with an HTTP server and open
`/level_generation/creatures/mm6_dwa1_codex/review/viewer/`. The viewer uses the existing read-only Three.js vendor
bundle in `mm6_goblin/review_20261006/vendor/` and native reference images in `mm6_dwa1/native/`; opening `file://`
is not supported. It supports tiers, orbit, exact 48 Hz frames, 1×/½× playback, skeleton, wireframe and frame feedback.

## Source and reconstruction decisions

Native authority is `source/native_summary.json`, original `dwa1` frames and engine monster records 520/521/522.
Identity: short, broad adult dwarf; large nose, pointed black beard/moustache, dark tied nape hair, one-spike iron
helmet with brass rim, green short tunic/trousers, brown leather yoke/belt/bracers/cuffed boots and a short right-hand
axe. Independent head views preserve detail. HD body masters are unarmed to prevent fused equipment. Hidden surfaces,
finger anatomy, the exact nape shape and three-dimensional action depth are reconstruction decisions.

Body geometry came from Meshy Smart Topology at the requested 15K target. The source-frame humanoid rig was fitted
to dwarf proportions, with wrist/elbow landmarks measured from the actual mesh and connectivity-based finger chains.
Four arm twist helpers and the Axe node bring the export to 57 joints. Head/hands were protected during reduction.
The shirt was smoothed across anatomical weight transitions; yoke and studs follow their own shells. The lower nape
blends toward the upper spine to clear the collar. A six-degree weapon-arm / five-degree free-arm adjustment clears
carry contact without a broad flared elbow. The free hand retains 45% source finger curl; the weapon grip is fixed.

The careful hand-modelled axe follows the generated standalone native-derived design. It has a detailed Meshy
retexture, dull grey metal, visible edge wear, wood grain and a geometric leather wrap. Its fitted grip radius is
0.01584 m; the solved fingers clear it. Attachment roll is 60°. Blade/body gates test real blade vertices, including
against the gripping arm; only intentional handle/grip contact is excluded from the general prop test.

## Animations

Local sources were chosen and reviewed before body modelling; no paid animation was necessary. G1 source sheets
are `review/g1_*.jpg`. Source filenames and early observations are in [ANIMATION_STUDY.md](ANIMATION_STUDY.md).

| Role | Local source | Export seconds |
|---|---|---:|
| Standing | Mixamo Standard Idle | 3.0 |
| Walking | ArmedWalk | 0.8 |
| Running | RelaxRunForward | 0.8 |
| Attack | Mixamo Sword And Shield Slash | 1.5 |
| Hit | Mixamo Hit Reaction (4), round 2 | 0.5 |
| Death | ArmedDeath1 | 1.066667 |
| Dead | held final Death pose | 1.0 |
| Fidget | Mixamo Standing Taunt Battlecry | 2.833333 |

Retargeting uses source rest deltas with forearm roll moved into the hand. Attack/Fidget plant the stance while keeping
about 20% of source leg motion as discrete IK steps. Attack has a 0.15 s ready lead, reduced forward trunk lean,
controlled axial spine turn and an actual blade-led blow at **0.71875 s**. Hit/Death/Fidget blend from the own
Standing pose; Fidget's early crossed-arm segment is replaced by a smooth open path. Death retains 35% neck/head
motion and 40% local leg motion to suit the broad collar and short tunic. Dead is regenerated from that final endpoint.
Grounding is measured from the evaluated soles/corpse surface at fractional frames. Running now keeps its lowest sole within 8.4 mm of the floor throughout the sampled cycle. Clip duration is animation presentation; this handoff changes no monster combat/recovery data.

All eight clips are reviewed at 48 Hz after GLB export. G4 arm p99 is ≤1.92× (Attack 1.80×), G5 hand stretch ≤2.818×,
and G6 arm/head/axe/blade contacts are zero in this sampled test. No moving group exceeds source angular steps +10°.
Real trouser–tunic triangle crossings are zero in every clip. A rejected open-hem nearest-face diagnostic remains
labelled in the raw report; it is not used as a penetration gate. Posture ranges for every clip are in the final report.
The lowest sampled body point is +1.262 mm in Death; runtime blending remains for orchestration.

## Textures and tiers

Body and independent head maps are 1K each, merged with a 32 px gutter into a 2080×1024 runtime atlas. The separate
axe uses 1024×1024 maps. Base colour, normal, MR/specular, class and region maps live in `textures/`.
Normals are converted from Meshy's DirectX convention to glTF +Y-up in the prepared exports and editable master.
AO is baked into base colour conservatively; MR red stores the current specular mask, green roughness, blue metal.
Skin/cloth specular is low; steel is deliberately darkened and roughened. Materials use the existing engine extras.

Native palettes **195 / 196 / 197** drive green→blue→red tunic and teal→purple→brown trouser ramps. They do not recolour
skin, beard, helmet, leather or axe. Palette statistics, masks and ramps are retained. The final strict UV gate finds
zero overlapping texels and zero collapsed triangles on either atlas; density is recorded for every piece. The head
atlas was repacked from the whole-body return, retaining two omitted triangles as independent islands, and its maps
were reprojected with tangent-normal basis conversion. This preserved the paid painted detail without another job.

| Asset | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body | 11563 | 5938 | 2091 | 629 |
| Axe | 2119 | 1248 | 470 | 149 |

Body/head merge gives one colour primitive per LOD. Shadow LODs are inset locally. After all merging and attachment
splitting, `scripts/normalize_lod_weights.py` jointly normalizes WEIGHTS_0 + WEIGHTS_1 immediately before writing the
final runtime body. The maximum combined sum error over every colour/shadow primitive is **1.22935e-7**.
`scripts/validate_export.py` checks the actual final file with a strict **<1e-4** limit and records its SHA-256.
Final clips and inverse bind matrices match the prepared LOD0 exactly.

## Scale and integration boundary

Native Standing alpha height is 222 px. The exported Standing median is 1.419452369 m, giving A's scale
**101.657985**. B/C reference A so their native scale ratios remain correct. Walking stance travel matches 0.89 m; running matches the engine’s 1.55 multiplier (1.3795 m).
The dwarf has no spells or projectiles; both physical attacks share Attack. Look uses B_Neck/B_Head with 25° yaw and
12° pitch, subject to native combined-pose checks. This is staged asset production; the orchestrator owns registry
merging, asset mounting, focused regression, saves and indoor/outdoor visual checks.

## Budget and reproducibility

**40 / 100 Meshy credits consumed; 60 unspent.** Body geometry 5, rig 5, axe texture 10, body texture 10, head texture 10.
All five tasks succeeded; receipts and request fingerprints remain in `creature_3d_progress.json`. Generated reference
prompts/hashes are in `references_hd/generation_runs.json`. All Meshy operations used the budget helper and all Blender
operations used the leased four-thread background wrapper; no other creature directory was written.

`work/`, `meshy/` and `texturing/` are local resumable scratch/paid returns, ignored for future commits. Raw animation
library clips are never a deliverable. Production scripts are retained locally; `export/mm6_dwa1.blend` is the simplest
editable starting point. Do not rerun earlier diagnostic scripts over the completed master without taking a new backup.
Current output checksums are in `export/SHA256SUMS`. No commit was made.

Final normalized LOD silhouettes are reviewed in [review/lod_sheet.jpg](review/lod_sheet.jpg).


## Review round 1

The first handoff's local normalizer and validator considered only WEIGHTS_0; reduced LODs also contain WEIGHTS_1.
That caused the runtime rejection and invalidated the earlier normalization claim. The final export path and check
now cover both sets together after all packaging. No shared-exporter defect is established by the old partial sums.
Only skin-weight bytes changed in the runtime GLB; geometry, rig, animation, textures and actor entries are identical.
See [Review round 1 handoff](HANDOFF.md#review-round-1), [final per-primitive weights](review/final_skin_weights.json),
[byte parity](review/round1/export_parity.json) and [hash-bound evidence](review/round1/manifest.json).
All offline gates and the 24-switch viewer check were rerun; clip/LOD review sheets were refreshed. No new credits.


## Review round 2

Flattened the boot soles with ankle rotation and two-bone leg IK, preserving the existing pelvis/head motion.
Standing, Fidget and Hit plant both feet; Attack retains its discrete steps with flat landings, and Walking keeps
flat soles through support and short lifts. No body-height offset, mesh, texture, skin weight, rest skeleton or
scale change was made. Because the old hip height exceeds a rigid leg's flat-foot reach, the solve allows bounded
leg extension: at most 2.81% in Standing, 2.56% in Fidget/Hit/Attack and 3.30% in Walking. The limit is asserted at 4%.
All Standing/Fidget heel/toe contact vertices lie 3.54–5.08 mm above the floor and the measured sole tilt is below 0.08°.

Selected `mx/hit_reaction_3e95a7` after checking `anim_library/index.json`: an upright, planted 0.433-second Mixamo
reaction without crouch/weapon caveats. The rest-delta retarget keeps source timing, 20% of pelvis movement and
30% of arm changes, with a brief right-arm clearance correction. Both arms and the axe move; the final pose equals
Standing. Hit remains **0.5 seconds**, within the native **0.75 seconds**, and its role name is unchanged.
The short motion stays below the step threshold, so its feet remain planted. [Source receipt](review/round2/hit_source.json).

The anatomical elbow audit also required correcting upper-arm roll in Attack/Fidget. Elbow/wrist/axe joint centres
remain within 0.006 mm of their authored keys; quaternion interpolation changes Attack's axe joint by at most
9.67 mm between keys (Fidget's maximum joint-path difference is 0.955 mm). Pelvis and head paths remain exact.
The measured attack event stays **0.71875 s**. All eight clips pass the elbow gate, G4/G5/G6, cloth and floor checks.
The accepted Fidget upper-body action remains; the user's explicit foot/Hit scope did not replace it with another idle.

`round2_motion.py` authors the revision from the preserved round 1 master. `round2_rebuild.py` exports it, and
`round2_package.py` copies only the five changed animation streams onto the accepted GLBs, then normalizes and
checks the final body. Geometry, texture payloads, all LOD weights, rest nodes and inverse binds stay exact;
Running/Death/Dead, the axe GLB and `integration/actors.yml` are unchanged. Keep the orchestrator's already-installed
`animation.cast: Attack` alias; this round needs no actor-registry merge.

See [Review round 2 handoff](HANDOFF.md#review-round-2), [boot closeup](review/round2/feet_Standing_front.png),
[Fidget soles](review/round2/feet_Fidget_three_quarter.png), [alternate Hit](review/Hit_sheet.jpg),
[sole measurements](review/round2/sole_gate.json), [elbow gate](review/round2/elbow_gate.json),
[joint-path comparison](review/round2/joint_path_parity.json) and [evidence manifest](review/round2/manifest.json).
The viewer passes 24 switches and 16 normal/slow playbacks. Additional Meshy cost: **0**; total **40/100**.


## Review round 3

Walking now clears the floor by 9.4 cm with 56–57° mid-swing knee bend, heel strike, toe-off and flat support.
Running pelvis motion is lower and steadier; the lowest sole stays 3.7–8.4 mm above the floor (100% contact under
10 mm at 48 Hz). Source upper-body motion and the axe grip remain attached. The two locomotion clips use exact
stride-driven sole targets, fitted-length leg IK and 120 Hz export sampling; both still last 0.8 seconds.
This replaces round 2's small walking lift and round 1's high run flight. The other six animation streams stay exact.

The tunic is a connected shell, so its central front/back panels use one coherent thigh mix across their width,
blending smoothly into side strips and a fixed belt. Covered trouser cuffs and studs share their host's weights.
This adapts the gob2 strip principle without splitting the accepted mesh. All LODs were rebuilt and normalized;
body/axe triangle counts and textures are unchanged. Cloth stretch and actual trouser intersections are gated at 48 Hz.

`scripts/round3_motion.py` starts from the preserved round 2 master. Run `round3_rebuild.py` next for export/LODs,
then host-Python `round3_prepare_checks.py`, Blender `round3_gates.py`, host `finish_review.py`, both viewer checks
and `validate_export.py`. Use the workspace lease wrapper and four-thread background Blender. Do not run older
round authoring scripts over this revision. The export patch deliberately preserves all six accepted non-locomotion
streams and copies only the authored cloth weight mask onto the accepted LOD0 before regeneration.

The local actor snippet now explicitly contains `animation.cast: Attack` for all three tiers, matching the
orchestrator's already-installed alias. There is no timing, scale, clip-name or attack-event change. No assets_dev
writes, game launches, builds or commits. No additional credits; total 40/100.

See [Review round 3 handoff](HANDOFF.md#review-round-3), [Walking](review/round3/Walking_contact_sheet.jpg),
[Running](review/round3/Running_contact_sheet.jpg), [measured gait](review/round3/locomotion_gate.json),
[tunic stretch](review/round3/flap_stretch_gate.json), [preserved accepted animation](review/round3/artifact_parity.json),
[bindings and weights](review/round3/bindings_check.json), and [evidence hashes](review/round3/manifest.json).
All offline gates and 24-switch/16-playback viewer checks pass; native movement/blends remain with the orchestrator.

## Review round 4

Reduced body LODs to 11563 / 5938 / 2091 / 629 and axe LODs to 2119 / 1248 / 470 / 149.
Protected collapse, UV carry, contact checks and eight-view IoU/SSIM determine the stopping point.
Lower levels use their already-accepted meshes as the appearance reference at the 500/200/80-pixel switches.
Rejected trials and this unattended reference decision are recorded in [the reduction curve](review/round4/reduction_curve.md).
A six-vertex covered LOD3 tunic patch restores the original detailed surface and clears its inherited intersection;
all eight animation streams, texture payloads, tier materials, rig and actor entries stay exact.

Every colour LOD passes all-clip deformation/contact/cloth checks; all final skin primitives pass normalization.
The viewer passes 24 switches and 16 playbacks. [Triangle reduction and round-4 handoff](HANDOFF.md#triangle-reduction).
Reproduction: search/refine scripts retain the measured trials; selection.json identifies the chosen local sources.
Run round4_finish_build.py with the leased four-thread Blender wrapper, then finish_review.py, viewer checks,
validate_export.py and round4_record.py. Preserved authoring masters and earlier-round backups remain under work/.
No new Meshy work; total 40/100 credits. No installation, game/build check or commit; the orchestrator integrates.

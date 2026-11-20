# Current delivery: review round 6 — Standard Run and mid-grey steel

Running now uses Mixamo **Standard Run** with a smooth symmetric 12 mm pelvis bob and fitted feet, replacing rejected Jogging. Body/axe steel is the measured perceptual midpoint between round-1 bright and current dark, matte on all tiers. All geometry and seven other clips are unchanged; shield and integration/actors.yml remain byte-identical. No new credits (30/100 total).

[HANDOFF.md](HANDOFF.md) contains hashes, native luminance measurements, 48 Hz jitter diagnostics and shared gate results. [Colour comparison](review/round6/steel_comparison_front.png), [running side sheet](review/round6/running_left.png), [viewer](review/viewer/index.html). Bindings and viewer pass. The shared rig verdict remains FAIL on disclosed inherited grip/posture/LOD limits; all visible LODs pass Running contact/floor checks. No game, build, installation or commit.

Reproduction uses the scripts ending `_r6.py` listed in HANDOFF.md. Decisions: retain the 1.2 m stride binding, solve feet to a fixed smooth root curve, use the archived bright ramp as the colour midpoint reference, keep the accepted shield untouched, preserve texture packing, report the missing shared positional-jitter threshold without adding a custom gate.

## Earlier project record (superseded)

# Current delivery: review round 5 — Running

Running now uses local Mixamo Jogging, fitted to a 0.8-second seamless loop and the unchanged 1.86 m runtime run stride. RelaxRunForward is rejected. Every other clip and all geometry/material data are preserved; axe, shield and integration/actors.yml are byte-identical to round 4. No credits spent this round (30/100 total).

[HANDOFF.md](HANDOFF.md) records the new hashes, shared Running gate results and remaining limits. [Side sheet](review/round5/running_left.png), [viewer](review/viewer/index.html). The shared gate verdict remains FAIL; this is not a full rig-pass claim. No game, build, installation or commit.

The current Running-only builders are scripts/run_retarget_r5.py, run_refit_r5.py, run_patch_r5.py and run_finish_r5.py. Runtime patching preserves the accepted binary payload and changes only the Running animation references. The earlier builders below are historical.

## Earlier project record (superseded)

# Current delivery: review round 4

Axe: **796 / 432 / 196 / 78 triangles**, down from 2122 / 945 / 356 / 118. Body and shield geometry, clips, tiers and bindings are unchanged. The shield GLB is byte-identical to assets_dev. Body and axe each use one shared four-map set across all LODs; body images 16 → 4, axe maps 2K → 1K. Runtime sizes: body 18.67 → 11.71 MB; axe 9.88 → 2.56 MB.

See [HANDOFF.md](HANDOFF.md) for counts, hashes, reproduction, comparisons and the shared runner's FAIL verdict. The accepted baseline also fails; blade/timing checks pass, while grip/body limits remain. LOD3 grip gap increases by 1.488 mm. This was one fixed triangle target with connection/padding repairs, no triangle search; 0 Meshy credits used (30/100 total). No game, build, install or commit.

The authoritative current runtime builder is scripts/package_r4.py. The round-3 per-LOD texture builders below are historical. Current textures are under textures/round4_body and textures/round4_axe; accepted source files are retained in review/round4/before. [Close-up](review/round4/axe_closeup.png), [in-game scale](review/round4/axe_ingame.png), [viewer](review/viewer/index.html).

## Earlier project record (superseded)

# Current delivery: review round 3

LOD colour counts: **10,247 / 5,189 / 2,384 / 898**, from 15,427 / 7,712 / 2,771 / 903. Main body/axe/shield: 6,797 / 2,122 / 1,328. Clips, palette ramps and actors.yml are unchanged. 30/100 credits used overall; 0 credits used in round 3.

**LOD3's 0.95904 pooled IoU remains below 0.97; this is a handoff with an open visual gate.** Existing colour-LOD rig gates, bindings and viewer checks pass. See [HANDOFF.md](HANDOFF.md) for exact hashes, metrics, coverage limits and the texture-memory tradeoff. [Round-3 evidence](review/round3/reduction_results.json).

Reproduction uses the packed `export/mm6_figc_authoring.blend` with `scripts/export_baked.py`, then copies the PNG/+Y-normal raw GLB to `export/mm6_figc_runtime_lod0.glb` and runs `scripts/lods.py` / `scripts/runtime_finish.py`. Lower sources are `review/round3/export_lod1..3/`. Run under a reclaimed workspace lease. The legacy `export_runtime.py` replaces materials and is intentionally restricted to explicit original-UV trial inputs.

Batch decisions: preserve the accepted animation and bindings; retain the stronger original close-up thresholds despite the later relaxed batch text; use the revised pooled silhouette criterion at 550/220/88 pixels; retain the original axe head after close-up rejection of its decimation; keep original source textures untouched and rebake into `textures/round3_lod*`; report the unresolved distant silhouette gate instead of relaxing it. UV charts on the body preserve seam connectivity; props need fresh charts because their original projected UVs overlap.

## Earlier project record

# MM6 FighterChain (figc) — Codex batch

**Review round 2 complete; ready for orchestrator re-integration. Artistic acceptance is pending.**
Created 2026-10-12 under the MM6 Codex batch rules. Meshy used **30 / 100 credits** (70 unused):
Smart Topology 5, rig 5, body retexture 10, head retexture 10. No paid animation jobs.
All job receipts, input hashes and downloaded outputs remain in creature_3d_progress.json and meshy/.

## Deliverables

- [HANDOFF.md](HANDOFF.md): integration entry point, measured gates and remaining limitations.
- [Runtime body](export/mm6_figc.glb), [axe](export/mm6_figc_axe.glb),
  [shield](export/mm6_figc_shield.glb): three native tiers, colour LODs and animated attachment nodes.
- [Portable tier A](export/mm6_figc_portable.glb): standard glTF, all eight clips and equipment included.
- [Packed authoring file](export/mm6_figc_authoring.blend): editable mesh, fitted rig, textures and actions.
- [Viewer](review/viewer/index.html), [front](review/clips_front.png), [side](review/clips_left.png),
  [three-quarter](review/clips_three_quarter.png) sheets.
- [Exact staged bindings](integration/actors.yml), [proposed regression](integration/regression.md),
  [playbook notes](integration/playbook_notes.md).
- [Artifact hashes](export/artifacts.json), [static handoff validation](review/handoff_validation.json).

Serve the repository root over HTTP and open
level_generation/creatures/mm6_figc_codex/review/viewer/ . This reuses the shared viewer/vendor files.
The final viewer check switched all **24 tier/clip combinations**, with no failed switches or console errors
([receipt](review/viewer_check.json)). Full playback at 1x and 0.5x is retained under
[playback_c](review/round2/viewer_c/playback_review.json), including the final Veteran
[standing](review/round2/viewer_c/standing.png) and [corpse](review/round2/viewer_c/corpse.png).
Browser-only tier GLBs bake colours for standard viewers; runtime uses shared textures and region ramps.
Earlier review/browser, browser_b, browser_c and work checkpoints are historical, not acceptance evidence.

## Native identity and decisions

Native descriptors **FighterChain A/B/C (535–537)** use palettes **212/211/210**.
The read-only sprite restoration project ../mm6_figc and preserved
[source inventory](source/native_inventory.json) were the native references.

The native sprite takes authority over the prompt shorthand “swordsman”: **right-hand double axe**,
**left-hand coffin shield**, and **sheathed sword at the left hip**. Body references deliberately omit held
gear so the hands remain separate; both props are original local geometry. The hip sheath/hilt stays
rigged to the pelvis. No other creature project or shared runtime file was edited.

Selected HD front/back/left/right/three-quarter masters and head references are retained in references_hd/
and references_head/, with prompts and generation records. Rejected anatomy/facing variants remain marked.
The model keeps the nasal horned helmet, chainmail, split ochre/burgundy tabard, rimmed pauldrons,
bracers, greaves and steel boots. Tier B uses red/dark red and C uses orange/purple. Review round 2 keeps dull-grey steel consistent
across all tiers, as requested by the user; native tint differences in metal are deliberately superseded.
The rebuilt axe and shield have separate UV material detail. Artistic acceptance of this revision is pending.

## Rig, motion and equipment

58 bones: source-frame skeleton, four twist bones and two animated equipment bones.
Joint fitting used Meshy landmarks plus independent limb-ring fits; rest-frame error is 0 degrees.
Fingers were separated by connectivity, fitted and weighted by their own chains. Source weight correspondence
was within 0.001 mm mean. Mail sleeves blend anatomically; rigid armour stays on its owning segment.

The axe's measured handle radius is 11.5 mm and minimum fitted finger-skin radius is 12.3 mm.
The shield grip is 11 mm, with minimum finger skin at 11.4 mm. Both hand close-ups were reviewed.
Meshy geometry was reduced after fitting weights, protecting face and fingers.

| Role | Local source |
|---|---|
| Standing | Mixamo Standard Idle |
| Walking | ArmedWalk |
| Running | RelaxRunForward |
| Attack | Mixamo Sword And Shield Slash |
| Hit | UnarmedGetHitF1 |
| Fidget | Mixamo Standing Taunt Battlecry |
| Death | Mixamo Standing React Death Backward |
| Dead | Final Death pose, held |

Mixamo uses the shared rest-delta retarget with forearm roll moved to the hand.
Attack and Fidget use a planted stance plus 20% discrete IK steps. Attack trunk lean is restrained;
a short ready lead and return prevent an abrupt idle transition. The left arm carries the shield in guard.
Fidget arms retain 35% of the source movement around that guard. Death releases both props at frame 26,
lands them flat by frame 48, and finishes the backward fall. No new animation library purchases were needed.

Native timing is recorded in [ANIMATION_STUDY.md](ANIMATION_STUDY.md). The 3D motions retain their readable
source action speed rather than reconstructing every sprite frame. Attack is 1.5 s including preparation/
recovery; its actual fastest target-facing axe cut is **0.714583 s**, staged as **0.715 s**.
Hit is 0.5 s, within the native 0.75 s; Fidget/Death finish their full actions. Runtime pacing remains an
integration check. Attack and attack2 share the native melee role.

## Measured gates

The reimported exported GLB was scanned at **48 Hz**, all eight roles, **682 samples**.
These gates were rerun after the review-round-2 geometry and material changes.

| Clip | Seconds | G4 arm p99 | G5 finger max | Head/shoulder mm | Pelvis min m | Trunk max degrees |
|---|---:|---:|---:|---:|---:|---:|
| Standing | 3.000 | 1.256 | 2.419 | 0.000 | 1.053 | 3.33 |
| Walking | 0.800 | 1.220 | 2.419 | 0.000 | 0.988 | 5.65 |
| Running | 0.800 | 1.255 | 2.419 | 4.129 | 0.923 | 3.71 |
| Attack | 1.500 | 1.384 | 2.419 | 4.984 | 0.975 | 19.23 |
| Hit | 0.500 | 1.270 | 2.419 | 4.444 | 0.999 | 14.67 |
| Fidget | 2.833 | 1.271 | 2.419 | 3.758 | 1.027 | 19.38 |
| Death | 3.633 | 1.495 | 2.419 | 4.865 | 0.221 | 96.21 |
| Dead | 1.000 | 1.294 | 2.419 | 4.140 | 0.282 | 86.50 |

[Full exported gates](work/export_full_gates.json) record every role. Arm p99 remains below 1.5x
(the playbook's approximate 1.5–2x gate); fingers remain below 4.5x. Arm and actual prop contact
depths are **0 mm** for both sides and both props in every clip, below the 2-mm gate.
Head/pauldron penetration peaks at **4.984 mm**, below the 10-mm head gate.
Death and Dead trunk angles are intentional fallen postures. Living poses remain upright in the side sheets.

[48-Hz source/export motion traces](work/export_motion_trace.json) have **zero flags** against the
source-plus-10-degree-per-sample threshold. [Actual blade gate](work/blade_gate.json), sampled at 240 Hz:
tip speed **23.707 m/s**, target-forward component **0.6459**, cutting-edge lead share **0.9987**, pass.
The contact scan tests nearest-face candidates within 5 cm plus a three-ray inside majority; it measures
the selected arms, gear and head against the body/shoulder surfaces, not every possible garment contact.

[Export parity](work/export_parity.json): rest correspondence 0.000538 mm; maximum integer-frame
surface difference 0.0233 mm; fractional-frame difference **4.169 mm** (Hit), due to 30-fps export of
denser floor keys. Contact/motion gates used that exported interpolation.
Minimum exported body height above its model plane is **4.290 mm**, in Running.
The staged ground offset puts this approximately **0.972 game units below** the floor at the worst sample.

[UV checks](work/uv_checks.json), at 512-square strict triangle interiors: body 7,778 triangles,
zero degenerate triangles and zero overlapping texels; head 3,733 triangles, zero degenerates and one
boundary/raster overlap texel (0.000739%). Meshy UV transfer matched topology and triangle corners.
Body/head normal maps were corrected to glTF Y-up and checked before packing.

## Runtime format and scale

| LOD | Body | Axe | Shield | Combined triangles |
|---|---:|---:|---:|---:|
| 0 | 11,511 | 2,440 | 1,476 | 15,427 |
| 1 | 5,754 | 1,150 | 808 | 7,712 |
| 2 | 2,067 | 431 | 273 | 2,771 |
| 3 | 685 | 131 | 87 | 903 |

LOD0 exceeds a generic 10k triangle target: this explicit armoured-actor choice preserves the fitted
hands, face and separate plate boundaries. Four body shadow LODs retain matching topology, with reduced
casters inset to avoid coarse self-shadow facets. The base body has one material primitive per colour LOD,
three KHR material variants, and one 58-joint skin. Up to eight skin influences are retained.

Body/head base colour, normal, material response and RGB region mask share a merged **2080x1024** atlas set.
MR.R stores the specular mask, G roughness, B zero metallic; runtime extras enable the specular mask.
Native palette ramps recolour ochre cloth, red cloth and metal; skin and neutral chainmail stay stable.
Separate prop exports inherit the actor's tier.

Scale comes from native standing visible height **247 px x 0.899994 = 222.298518 game units**.
Exported Standing is **1.763883397 m** high. All three bindings therefore use **126.027899** scale,
**-1.512415** z offset and **-1.570796327** yaw offset.
[Calibration receipt](work/scale_calibration.json). The 1.2-m stride and conservative 45/25-degree
head-look settings are staged choices for the orchestrator's runtime validation.

## Limits and remaining work

No blocking failure remains in the measured G4/G5/G6, blade or viewer gates.
The individual worst arm edge reaches **4.628x** during Death despite p99 passing; the broad lower
torso/leg diagnostic reaches **3.185x** during Running (p99 2.414x). These maxima are retained in the
report; they are not substituted for the arm/finger gates. Final sheets/playback show no detached limbs
or props cutting through the body. Garment folds and the revised equipment remain subject to artistic review; the round-2 requested
steel and equipment changes are implemented and documented below.

The orchestrator installed and captured the previous revision. Review round 2 has **not** been
installed or checked in game by this production session. Re-integration, GPU appearance, runtime additive
head-look clearance and artistic review belong to the orchestrator under the batch override. No game launches, CMake builds, shared-file writes or commits.

## Resume

Reclaim mm6:figc with tools/creature_workspace.py before edits; use its returned token for guarded writes.
All Blender commands must use tools/run_creature_blender.sh with this project's script and four threads,
one process at a time. Do not replay paid Meshy jobs; the successful outputs and receipts are retained.

The final motion source is work/final_motion.blend. Preserve the painted gear atlas and calibrated ramps.
If composing textures again, run compose_figc.py, gear_textures_r2.py and calibrate_steel.py in that order,
then export_runtime.py, the shared prepare_actor_glb.py step, lods.py and runtime_finish.py.
Geometry/motion edits must rerun gates_exported.py, motion_trace.py, blade_gate.py and export_parity.py,
followed by render_final.py, compose_sheet.py and the shared check_viewer.mjs. Inspect results before
updating the handoff. Intermediate scripts/checkpoints preserve the complete fitting history.

## Review round 1

**Historical and rejected; superseded by review round 2 below.**

User feedback: duller grey steel, a better axe with surface detail, and a shield closer to the native coffin
shape with a studded rim and star emblem. The in-game comparison in review/ingame/compare.png is the
orchestrator's previous-revision evidence; it is not a capture of this revision.

- All three body/head steel ramps now share a grey linear-light range of about 0.025–0.290 instead of reaching
  0.880–1.0. Armour specular mask is 0.40 and roughness about 0.64; the accepted tier cloth colours remain.
- Axe: curved double bits, a thin cutting edge, bevels, a forged socket/ferrules, scored wood and a helical leather
  grip. Shield: native coffin outline, grey central face, tier-coloured side inlays, blackened four-point star,
  oval bronze boss, bevelled rim and 23 six-triangle rivet caps. Hidden rivet stems/back caps are omitted.
- One authored 1K gear atlas supplies base colour, normal, roughness/specular and region mask. UVs cover real
  texture areas; every gear UV triangle passes the nonzero-area assertion. Normal convention measures +0.97.
- Body LOD0 stays 11,511 triangles; axe 160 -> 732, shield 152 -> 358. Combined +778 triangles (+6.58%).
- Body mesh/rig/grips and action timing stay unchanged. Dropped-gear floor clearance was recomputed for the new
  outlines. Actual fastest target-facing axe cut is 0.714583 s, so integration/actors.yml changes only the
  three melee impact values 0.719 -> 0.715. All scale, look, stride, clip and attachment fields are unchanged.
- Re-exported runtime, portable and packed authoring files; reran all eight G4/G5/G6 and posture scans, blade
  timing, source/export motion, export parity, UV checks, 24 viewer switches, all-clip playback at 1x/0.5x,
  and front/side/three-quarter sheets. No new Meshy jobs: still 30/100 credits.

Historical round-1 visual review: [three tiers](review/round1/tiers.png), [axe close-up](review/round1/details/axe.png),
[shield close-up](review/round1/details/shield.png). File hashes and integration instructions are in the
[Review round 1 handoff](HANDOFF.md#review-round-1). Previous exports/state are preserved in review/round1/before/.

Replay this repair with repair_equipment_r1.py (frozen before/work/final_motion.blend), compose_figc.py,
gear_textures.py, export_runtime.py, prepare_actor_glb.py, lods.py and runtime_finish.py, through the existing
project guards. Then run gates_exported.py and check_round1.py, the viewer and validate_handoff.py.
The older motion_finish.py rebuild precedes this equipment revision; rerunning it alone restores old props.


## Review round 2

The stronger equipment review is handled by four new native-guided Codex imagegen designs and a careful local
mesh with the generated painted surfaces baked into its UV atlas. Selected designs and exact prompts:
[references_hd/round2_equipment](references_hd/round2_equipment/provenance.json).
[Design-to-mesh comparison](review/round2/prop_comparison.png), [three tiers](review/round2/tiers.png),
[final changes, hashes, triangle counts and gates](HANDOFF.md#review-round-2).

Unattended decisions: retain the native compact double axe despite the swordsman shorthand; preserve existing
hand/socket frames and all source motions; use the hand-model route to maintain the fitted grip and spend no
additional Meshy credits; project the new HD painted designs instead of repeating round 1's procedural noise;
keep the star painted, with geometry spent on the curved face, rim, boss and studs. The axe is 2,440 triangles,
the shield 1,476. A shared 2K atlas preserves readable wear and paint chips. Native metal tier tints remain
superseded by the requested common dull-grey steel. The same-camera viewer bracer median falls from 0.493 to
0.266 sRGB after calibration against native armour pixels. Geometry, normal, roughness and colour all carry detail.

All eight clips and the viewer were rechecked; impact remains 0.715 seconds. integration/actors.yml is unchanged.
Budget remains 30/100. Only this project was edited. The orchestrator owns re-installation and game validation;
artistic acceptance of round 2 is still pending. Historical round-1 appearance and hashes are superseded by round 2.

Round-3 cleanup: discarded model/autosave caches are listed in `review/round3/discarded_trial_caches.json`; the baseline, selected sources, curve metrics and review renders remain.

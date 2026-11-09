# MM6 BDwarf / dwa1 — ready for orchestrator

**Review round 4 technical criteria passed. The user-accepted appearance and clips are retained.** Project owner: `codex-batch-dwa1`.
**40 / 100 Meshy credits used; 60 remain.** All five jobs succeeded. No animation purchase, commit, game launch,
build, runtime installation or shared registry/playbook/source edit was made. The sprite-restore project stayed read-only.

## Files to take

| Purpose | File |
|---|---|
| Runtime body, all clips/tiers/LODs | [export/mm6_dwa1.glb](export/mm6_dwa1.glb) |
| Runtime rigid axe, all tiers/LODs | [export/mm6_dwa1_axe.glb](export/mm6_dwa1_axe.glb) |
| Editable packed master, corrected normal maps | [export/mm6_dwa1.blend](export/mm6_dwa1.blend) |
| Exact three descriptor blocks | [integration/actors.yml](integration/actors.yml) |
| Proposed maps, summoned ids and size bounds | [integration/regression.md](integration/regression.md) |
| Shared-workflow findings for later review | [integration/playbook_notes.md](integration/playbook_notes.md) |
| Artifact metadata / checksums | [export/manifest.json](export/manifest.json), [export/SHA256SUMS](export/SHA256SUMS) |
| Decisions, sources, corrections and resume notes | [README.md](README.md), [creature_3d_progress.json](creature_3d_progress.json) |

For round 4, replace both runtime GLBs. Integration/actors.yml is unchanged.
Original installation paths: `worlds/mm6/models/mm6_dwa1.glb` and `worlds/mm6/models/mm6_dwa1_axe.glb`. Descriptors are **BDwarf A/B/C**, ids **520/521/522**, skins **dwa1_a/b/c**.
Attach the axe to **Axe**. Scale A is **101.657985**; B/C use **scale_reference: BDwarf A**. Melee and native secondary
physical attack share Attack with **impact 0.71875 s**. No spells or projectiles; the required `animation.cast` binding aliases Attack.

## Gate results

[Final machine report](review/final_validation.json), [G4 detail](review/g4_exported.json),
[G5 detail](review/g5_exported.json), [G6 contacts/posture](review/g6_exported.json),
[source-relative angular steps](review/motion_metrics_exported.json), [actual cloth intersections](review/skirt_intersections.json).
All eight clips were sampled at **48 Hz after export/re-import**. G4/G5/G6 and cloth gates cover all four colour LODs. Every colour/shadow primitive passes finite-data, index,
joint-count, combined-weight normalization and variant validation; all LODs pass the measured visual limits.

| Clip | G4 arm p99 stretch | G5 max hand stretch | G6 max contact mm | Tunic crossing edges |
|---|---:|---:|---:|---:|
| Standing | 1.26 | 2.818 | 0.000 | 0 |
| Walking | 1.31 | 2.806 | 0.000 | 0 |
| Running | 1.51 | 2.806 | 0.000 | 0 |
| Attack | 1.82 | 2.806 | 0.000 | 0 |
| Hit | 1.28 | 2.806 | 0.000 | 0 |
| Death | 1.96 | 2.806 | 0.000 | 0 |
| Dead | 1.47 | 2.806 | 0.000 | 0 |
| Fidget | 1.55 | 2.806 | 0.000 | 0 |

- G4 arm p99 limit 2×; G5 hand/finger limit 4.5×; all pass. Right-hand shaft radius 15.84 mm, fitted skin clears it.
- No sampled arm, head, axe or actual blade contact. Blade test includes the gripping arm; intentional shaft/grip
  contact alone is excluded from the general prop test. All moving bone groups stay within source angular step +10°.
- **Blade/blow gate:** fastest forward-facing cutting point at **0.71875 s**, speed **18.569 m/s**,
  signed edge lead **+0.94023**, edge-motion share **0.99602**, forward-axis component **0.84278**. This is a cutting strike.
- Strict body/head UV overlap **0**, collapsed triangles **0**, all regions have measured healthy density. Axe UV gate passes.
- Lowest sampled floor point: **+1.262 mm**, Death. Running lowest sole is **+3.671 to +8.354 mm**; all clips pass.
- Body LOD triangles **11563 / 5938 / 2091 / 629**, shadow LODs at those counts; axe **2119 / 1248 / 470 / 149**.
  **57 joints**, exactly eight clips, three variants; body/head one colour primitive per LOD. Skin weight sum error
  **<1.4e-7** across WEIGHTS_0 + WEIGHTS_1. Animation samples and inverse bind matrices are unchanged by packaging/splitting.
- [Viewer check](review/viewer_check.json): **24/24** tier/clip switches pass, zero console errors.
  [Continuous playback](review/playback_check.json): all eight clips finish at **1× and ½×**, **16/16** pass, zero errors.

### Posture (all clips)

Forward trunk lean is positive; negative is backward lean. Death/Dead intentionally approach a horizontal corpse.
Attack stays upright, with short planted steps; Fidget is a dramatic upward battlecry with moving arms/axe.

| Clip | Pelvis height range m | Trunk lean range degrees |
|---|---:|---:|
| Standing | 0.771–0.773 | -2.37–-0.58 |
| Walking | 0.728–0.761 | 5.40–5.82 |
| Running | 0.673–0.704 | 3.09–5.84 |
| Attack | 0.713–0.772 | -0.65–16.37 |
| Hit | 0.769–0.772 | -4.19–-0.65 |
| Death | 0.203–0.810 | -16.44–107.45 |
| Dead | 0.218–0.218 | 83.95–83.95 |
| Fidget | 0.752–0.772 | -14.69–24.53 |

## Visual review

[Interactive viewer](review/viewer/index.html) — serve repository root; see README for dependencies.
[Three tiers](review/tiers.jpg), [front clip sheet](review/clips_front.jpg), [side clip sheet](review/clips_left.jpg),
[three-quarter clip sheet](review/clips_three_quarter.jpg), [LOD sheet](review/lod_sheet.jpg).
[Attack](review/Attack_sheet.jpg), [Hit](review/Hit_sheet.jpg), [Fidget](review/Fidget_sheet.jpg),
[Death](review/Death_sheet.jpg) have separate larger sheets. Current hand closeups use `Attack0.71875`.
[Weapon design](review/axe_design.png), [detailed PBR axe closeup](review/axe_closeup.png),
[grip closeup](review/axe_grip_closeup.png). HD body/head views and generation receipts are retained in `references_hd/`.

The agent inspected all role sheets, the tier portraits/head views, both hands and the weapon closeups. Metal reads dull
and the attachment follows the arm. LOD3 is visibly faceted at close range and is intended for distant use.

## Open faults and remaining ownership

**No known failing offline technical gate.** The user accepted Standing, the new Hit and the axe. Round 3 revises
Walking, Running and the tunic weights; those changes are ready for review. Native actions remain references, not exact 3D frame matches.

Per the Batch rules, the orchestrator still owns installation, native look/blend combinations, indoor/outdoor GPU material
and shadow checks, LOD transition distances, live melee timing, save/load and regression. The proposed test is
`mm6_bdwarf_codex_full`, world mm6, controlled **6d07.blv**, native **6d05.blv / 6d09.blv**, outdoor **oute3.odm**,
ids **520,521,522**. Close runtime checks should include the short neck under look overlays and locomotion contact under actual movement/animation blends. Those are integration checks, not silently claimed offline successes.

The first handoff incorrectly diagnosed partial WEIGHTS_0 sums as a shared-helper issue. Review round 1 fixes the
local normalizer and validator to include WEIGHTS_1; details below supersede that earlier claim. No shared tool was
changed. Ignore scratch/raw library material under `work/`, `meshy/`, `texturing/` and texture backups when preparing
any future commit.


## Review round 1

Historical receipt; round 3 below identifies the current artifact. The [archived final validation](review/round1/final_validation.json)
retains the round 1 hash. Shared review paths elsewhere in this section now show the latest results.

**Fixed the final runtime skin weights; ready for orchestrator reinstall.** The previous local normalizer and validator
only considered WEIGHTS_0. The reduced LODs also contain WEIGHTS_1, so normalizing the first set alone left the combined
sum above one. The old normalization claim was incorrect. `scripts/package_lods.py` now runs
`scripts/normalize_lod_weights.py` after the body/head/shadow merge and attachment split, as the final runtime write.
It normalizes both sets jointly. `scripts/validate_export.py` independently reads every primitive of that final file,
requires combined **max |sum−1| < 1e-4**, and records its hash.

| File | Result | LOD triangles (unchanged) |
|---|---|---|
| `export/mm6_dwa1.glb` | Corrected weights only; 7,574,520 bytes | Body 12502 / 6251 / 2202 / 698; shadow same |
| `export/mm6_dwa1_axe.glb` | Byte-identical | 2630 / 1314 / 472 / 150 |
| `export/mm6_dwa1.blend` | Byte-identical editable LOD0 master | Unchanged |
| `integration/actors.yml` | **No changes** | BDwarf A/B/C descriptors unchanged |
| `integration/regression.md` | No changes | Orchestrator still owns runtime checks |

SHA-256:

- Previous body (rejected): `b54239447717a750d8269efda76a21dfbac970488c218f564f0b79993361b1f6`
- **Corrected body:** `70eeeb311335c45a41e31ea92c065f083528b3880307c84f5e4f2b3c7cb95534`
- Axe (unchanged): `311ab3f0b7ba7a8bf7d300a1c449f876c2ed75c1791279f1f68caf45c82db120`
- Editable master (unchanged): `964579985b8e1be5d86752ae159f35787e6c37fa18255dda273d707424b69085`
- `integration/actors.yml` (unchanged): `6b2fedd95419cd8c1249bae0ad6435b754c4143788f3efc29771e76125979c5b`

Only **8,242 weight bytes** differ in the runtime body. Its JSON, every non-weight binary byte, LOD0/shadow0,
geometry, materials, textures, skeleton, inverse bind matrices and animation are identical to the rejected file.
The three viewer GLBs are also byte-identical. [Parity evidence](review/round1/export_parity.json).

| Final primitive pair (colour + shadow) | Vertices each | Maximum combined sum error (each) |
|---|---:|---:|
| Body / Body_Shadow | 10020 | 1.2293457984924316e-7 |
| Dwarf_LOD1 / Dwarf_LOD1_Shadow | 6049 | 9.033828973770142e-8 |
| Dwarf_LOD2 / Dwarf_LOD2_Shadow | 2869 | 8.987262845039368e-8 |
| Dwarf_LOD3 / Dwarf_LOD3_Shadow | 1330 | 9.100767783820629e-8 |

[Final validation](review/final_validation.json) and [normalization report](review/final_skin_weights.json) bind these
numbers to the corrected body hash above. The orchestrator's `output/codex_batch/check_weights.py` also passes.
The new `scripts/test_normalize_lod_weights.py` regression passes: both sets share the divisor, valid eight-influence
weights stay unchanged, unrelated bytes stay unchanged, normalization is idempotent, and invalid weights are rejected.

Reran the 48 Hz G4/G5/G6, cloth intersection, posture, UV, blade/blow-time, source-motion and floor gates; all pass
with the gate values above. The gate mesh is unchanged LOD0; all four review LODs have exact position/joint/weight
parity with the corrected runtime body. Re-rendered front/side/three-quarter clip sheets, per-role sheets, tier views,
hand closeups and the [LOD sheet](review/lod_sheet.jpg); inspected the refreshed LOD sheet.
The shared viewer checker passes **24/24** tier/clip switches with no console errors or failed checks.
The earlier **16/16** continuous-playback result is retained for the byte-identical viewer GLBs; it was not rerun.
Evidence hashes and the final runtime hash are recorded in [round 1 manifest](review/round1/manifest.json).

Supporting changes: `scripts/finish_review.py` refreshes the LOD sheet; `scripts/round1_gates.py` runs the existing
export gates and asserts the runtime hash is unchanged. README, progress, export manifest/checksums, viewer manifest,
validation reports, review sheets and `integration/playbook_notes.md` now reflect the correction.
**No actor integration entries changed; no assets_dev writes, game launches, builds, shared-tool edits or commits.**
**Additional Meshy spend: 0; total remains 40 / 100 credits.** The orchestrator must replace its installed body with
this corrected GLB, restore the unchanged actor entries and perform the native loading/regression checks.


## Review round 2

Historical receipt; round 3 below is current. Shared review paths now show round 3 results.

**Flattened the soles and replaced Hit; ready for orchestrator reinstall.** The user's base-design acceptance is
preserved. The foot repair uses ankle rotation and two-bone leg IK with no body-height offset. Existing pelvis and
head paths are exact in Standing, Walking, Attack and Fidget. Bounded leg extension reaches the floor without
moving the body: maximum **2.81% Standing**, **2.56% Fidget/Hit/Attack**, **3.30% Walking** (asserted ceiling 4%).
Standing/Fidget/Hit have two planted soles; Attack keeps its discrete steps and Walking its short lifts.

Per-foot measurements over the entire Standing/Fidget clips at 48 Hz, from actual exported sole contact vertices.
Heel/toe columns show the minimum and maximum height of every sampled contact vertex, in millimetres above z=0.
The sole plane limit is 3° and the heel/toe height limit is 10 mm.

| Clip | Foot | Maximum sole tilt | Heel height mm | Toe height mm |
|---|---|---:|---:|---:|
| Standing | L | 0.0298° | 4.343–4.466 | 3.974–4.639 |
| Standing | R | 0.0693° | 4.197–4.252 | 4.256–5.073 |
| Fidget | L | 0.0316° | 3.912–4.439 | 3.544–4.611 |
| Fidget | R | 0.0744° | 3.890–4.252 | 3.972–5.072 |

[Sole report](review/round2/sole_gate.json), [Standing boots](review/round2/feet_Standing_front.png),
[Fidget boots](review/round2/feet_Fidget_three_quarter.png). Hit and Attack's return to rest pass the same contact
checks; Walking's support samples pass, with heel/toe rise permitted during its measured short swing phases.

**Alternate Hit:** local index id `mx/hit_reaction_3e95a7`, Mixamo Hit Reaction (4), upright/planted/no crouch caveat.
The original 0.433-second source timing is retained inside a **0.5-second Hit**, including the return to relaxed
Standing, below the **0.75-second native limit**. It retains 20% pelvis motion and adapted arm movement; both hands
and the axe move (maximum displacement from rest: right hand 186.7 mm, left hand 198.5 mm, axe joint 228.7 mm).
The fixed grip follows the hand. Every measured endpoint joint matches Standing exactly. A transient 24° outward
weapon-arm correction clears the tunic during the flinch, then returns fully to the relaxed rest pose.
[Hit sheet](review/Hit_sheet.jpg), [source receipt](review/round2/hit_source.json).

The elbow gate uses the source-frame anatomical hinge. Attack/Fidget needed upper-arm roll correction to keep the
bend in that plane. Their elbow/wrist/axe authored joint positions remain within **0.006 mm**; between keys the
largest quaternion-interpolation difference is **9.67 mm** at Attack's axe joint and **0.955 mm** in Fidget.
The blow still occurs at **0.71875 s** (18.569 m/s; signed edge lead +0.94023). No clip names or durations changed.
All eight clips pass: elbow flexion **-0.511° to 114.067°**, absolute forearm roll **≤50.183°**, off-plane **≤1.026°**.
[Elbow report](review/round2/elbow_gate.json), [joint-path comparison](review/round2/joint_path_parity.json).

**Files and SHA-256:**

| File | Change | Triangle counts |
|---|---|---|
| `export/mm6_dwa1.glb` | Five revised animation streams; 7,587,644 bytes | Body 12502 / 6251 / 2202 / 698; shadow same |
| `export/mm6_dwa1_axe.glb` | Byte-identical | 2630 / 1314 / 472 / 150 |
| `export/mm6_dwa1.blend` | Updated packed editable animations | Geometry unchanged |
| `review/viewer/mm6_dwa1_a.glb`, `_b.glb`, `_c.glb` | Updated review animations | LOD0 geometry unchanged |
| `integration/actors.yml` | **Unchanged; no merge needed** | Existing BDwarf A/B/C entries retained |

- Previous body: `70eeeb311335c45a41e31ea92c065f083528b3880307c84f5e4f2b3c7cb95534`
- **Round 2 body:** `bff890740c7b49fccd8431bbc767a529561a07ccb2fe8af6c5e1757279b40e5e`
- Axe (unchanged): `311ab3f0b7ba7a8bf7d300a1c449f876c2ed75c1791279f1f68caf45c82db120`
- Editable master: `eb762f9d2ed17f341bfedb727e601df85976bd497f19e160be4ddab5685e7962`
- `integration/actors.yml` (unchanged): `6b2fedd95419cd8c1249bae0ad6435b754c4143788f3efc29771e76125979c5b`

Geometry, indices, all colour/shadow skin weights, texture bytes, materials, rest nodes and inverse binds are exact;
Running/Death/Dead animation streams are unchanged. The current `round2_package.py` replaces only selected animation
streams and runs final normalization immediately before writing the runtime body. All eight skinned primitives
have combined weight-sum error **≤1.22935e-7**, below **1e-4**. The shared `check_weights.py` passes on body and axe
with **no BAD line**. [Artifact parity and checker output](review/round2/artifact_parity.json).

G4/G5/G6 were rerun on every clip at 48 Hz: maximum arm p99 **1.92×**, hand stretch **2.818×**, contact **0 mm**,
cloth crossing edges **0**. UV overlap/collapsed islands **0**; source-relative angular-step flags **0**; lowest floor
point **-1.984 mm**, unchanged Running. The viewer passes **24/24** switches and **16/16** normal/slow playbacks,
zero errors. Refreshed all three clip sheets, per-role sheets, tiers, LOD sheets and the new sole closeups.
[Final validation](review/final_validation.json), [round 2 evidence manifest](review/round2/manifest.json).

Production changes are in `scripts/round2_motion.py`, `round2_package.py`, `round2_rebuild.py`, `round2_gates.py`,
`round2_sole_gate.py`, `round2_elbow_gate.py`, `round2_review.py` and `validate_export.py`; records/manifests and
review files are refreshed. Round 1's selected artifacts are backed up in ignored `work/round2_before/`.
**Integration/actors.yml did not change** because names, durations and event timing did not change. Preserve the
orchestrator's already-installed `animation.cast: Attack` alias; do not replace those installed descriptor blocks.

**No assets_dev writes, game launches, builds, shared-file edits or commits. Additional credits: 0; total 40/100.**
The orchestrator owns reinstalling the corrected body and native load/blend, melee and indoor/outdoor regression.


## Review round 3

**Fixed run height, walking foot clearance and tunic shear. Ready for orchestrator reinstall.** No new paid job.
The user accepted Standing, Hit and axe; their animation/attachment data is preserved exactly. Attack, Fidget,
Death and Dead animation streams are also byte-identical to round 2. Materials, embedded textures, rest rig and
LOD0 positions/UVs/topology are unchanged. Regenerated reduced LODs keep identical topology/counts, with only
float rounding in non-skin attributes (position delta ≤1.014 micrometres). [Parity](review/round3/artifact_parity.json).

Both locomotion clips retain **0.8 seconds** and use two-bone leg IK with fitted bone lengths, heel strike,
toe-off and flat support. Walking recovers the foot behind the knee before advancing into the next step.
Running pelvis height is now **0.673–0.704 m**, removing the old high body bounce. These are local leg/root edits
on the selected source clips; the source upper-body/axe action stays attached to the moving body.
The final two locomotion streams are baked at **120 Hz** so 30 Hz interpolation cannot pull a planted sole sideways.

Measurements below use actual exported sole contact vertices over the entire cycle at **48 Hz** (40 samples,
including the endpoint). Contact means the lowest sole is within **10 mm** of the floor.

| Clip | Lowest sole min / max | Contact samples | L heel / toe swing peak | R heel / toe swing peak |
|---|---:|---:|---:|---:|
| Walking | 3.410 / 4.078 mm | 40/40 — 100% | 9.408 / 9.408 cm | 9.425 / 9.452 cm |
| Running | 3.671 / 8.354 mm | 40/40 — 100% | 12.434 / 12.434 cm | 12.398 / 12.425 cm |

Walking mid-swing knee flexion is **L 56.403°, R 57.336°**; the lowest point of each swinging sole peaks at
**L 9.372 cm, R 9.401 cm**. The running value in the first column measures the lower of both feet, so the
12 cm individual swing does not represent whole-body flight. No sampled running frame exceeds the 4 cm gap limit.
The support phase uses the same **0.89 m walking stride** and engine **1.55× running multiplier (1.3795 m)** as
`stride_length`. Expected sole travel is **1.1125 m/s walking**, **1.724375 m/s running**; maximum measured flat-
stance speed error is **0.000708 / 0.001043 m/s**, respectively. [Full traces](review/round3/locomotion_gate.json).

The connected tunic's central front/back panels now share a coherent thigh mix across their width, blending into
the side-thigh strips and a pelvis-anchored belt. The covered trouser cuffs and hem studs follow that host shell.
**830 authoring vertices** changed weights; geometry was not moved. Every colour/shadow LOD was regenerated and
jointly normalized as the final body write. The entire tunic is now explicitly covered by the edge-stretch gate:
Running **p99 1.447× / max 1.564×** (old running max 2.796×); all-clip max **1.724×**, below the 2.5× ceiling.
Two-way tunic/trouser triangle crossing is **zero on every clip**. [Stretch](review/round3/flap_stretch_gate.json),
[contact](review/skirt_intersections.json).

Standing/Fidget soles still pass the round 2 rest rule: maximum tilt **L 0.0317° / R 0.0744°**, heel/toe contact
vertices **3.544–5.073 mm** above floor. [Per-foot measurements](review/round3/sole_gate.json).
All eight clips pass anatomical elbows and G4/G5/G6 at 48 Hz: max arm p99 **1.92×**, hand stretch **2.818×**,
arm/head/axe/blade contact **0 mm**. UV overlap/collapsed faces and source-relative motion flags are **zero**.
The blade/blow event remains **0.71875 s**, signed edge lead **+0.94023**. Names, durations, scale and impact timings
are unchanged. `check_bindings.py` (including `check_weights.py`) prints **no BAD line** on the staged actors/body/axe.
Maximum combined WEIGHTS_0 + WEIGHTS_1 error over all eight runtime primitives is **1.2293457984924316e-7 < 1e-4**,
bound to the final body hash below. [Validation](review/final_validation.json), [bindings](review/round3/bindings_check.json).

| File | Change | Triangles |
|---|---|---|
| `export/mm6_dwa1.glb` | Walking/Running and cloth weights; 7,644,828 bytes | Body 12502 / 6251 / 2202 / 698; shadows same |
| `export/mm6_dwa1_axe.glb` | Byte-identical | 2630 / 1314 / 472 / 150 |
| `export/mm6_dwa1.blend` | Refreshed packed editable export | LOD0 unchanged topology |
| `review/viewer/mm6_dwa1_a.glb`, `_b.glb`, `_c.glb` | Current locomotion and weights | Body + axe LOD0 |
| `integration/actors.yml` | **Added `cast: Attack` to all three `animation` blocks** | Matches already-installed aliases |

SHA-256:

- Previous round 2 body: `bff890740c7b49fccd8431bbc767a529561a07ccb2fe8af6c5e1757279b40e5e`
- **Round 3 body:** `014229b8c1f0f1bd50b2984c5e37fe094a49f5e0a285232c01cb58e9de602071`
- Axe, unchanged: `311ab3f0b7ba7a8bf7d300a1c449f876c2ed75c1791279f1f68caf45c82db120`
- Editable master: `201937f7dfab8cab2c2ecc1dc119d530ad3f24ba4bc0600338a112204d23e8ab`
- Updated `integration/actors.yml`: `a5e41e99c160da963f399c5f88f4e97abeb85e049d6adedc387eb50445d14ba4`

The viewer passes **24/24** tier/clip switches and **16/16** complete normal/half-speed playbacks, with zero errors.
Front/side/three-quarter clip sheets, role sheets, LOD/tier views, hand views and rest-foot closeups were refreshed.
New floor-relative [Walking contact sheet](review/round3/Walking_contact_sheet.jpg) and
[Running contact sheet](review/round3/Running_contact_sheet.jpg) show nine phases from three views. Agent inspection
confirms visible foot recovery, grounded support and no stretched dark flap; the refreshed Hit and LOD sheets were
also inspected. [Round 3 evidence and file hashes](review/round3/manifest.json).

Production changes: `scripts/round3_motion.py`, `round3_package_lod0.py`, `round3_rebuild.py`,
`round3_prepare_checks.py`, `round3_locomotion_gate.py`, `round3_gates.py`, `export_runtime.py`,
`validate_export.py`; updated reports/sheets, README, progress and manifests. Round 2 sources are retained under
ignored `work/round3_before/`; pilot diagnostics stay under ignored `work/round3_diagnostics/`.
**Integration/actors.yml changed locally; no installed registry or assets_dev file was touched.** The orchestrator
must replace the installed body; axe and installed cast aliases already match. Native load/blend, stride, lighting,
shadows, indoor/outdoor and regression checks remain the orchestrator's work.
**No game launches, builds, shared-file edits or commits. Added credits: 0; total 40/100, 60 remain.**

## Triangle reduction

| Mesh | LOD | Before | After | Reduction | Minimum IoU | Minimum SSIM | Gates |
|---|---:|---:|---:|---:|---:|---:|---|
| Body | 0 | 12502 | 11563 | 7.51% | 0.998488 | 0.991442 | PASS |
| Body | 1 | 6251 | 5938 | 5.01% | 0.998263 | 0.992716 | PASS |
| Body | 2 | 2202 | 2091 | 5.04% | 0.998884 | 0.992509 | PASS |
| Body | 3 | 698 | 629 | 9.89% | 0.995528 | 0.993838 | PASS |
| Axe | 0 | 2630 | 2119 | 19.43% | 0.997857 | 0.985284 | PASS |
| Axe | 1 | 1314 | 1248 | 5.02% | 1.000000 | 0.989445 | PASS |
| Axe | 2 | 472 | 470 | 0.42% | 0.995495 | 0.996159 | PASS |
| Axe | 3 | 150 | 149 | 0.67% | 1.000000 | 0.999539 | PASS |

The measured reduction preserves the accepted appearance, clips, tiers, prop design and bindings.
The strict eight-view limits determine the stopping point; the 15k ceiling is not the chosen target.
[Full curve and method](review/round4/reduction_curve.md), [trial CSV](review/round4/reduction_curve.csv),
[final hash-bound visual scores](review/round4/final_visual.json), [before/after sheet](review/round4/before_after.jpg).

The accepted LOD3 already had a covered trouser/tunic intersection. Six tunic vertices were fitted back to
the accepted full-detail surface (maximum 7.121 mm), with skin weights interpolated
from that same surface. This removes the intersection while preserving the required silhouette and texture scores.
The other candidate cloth corrections that changed the silhouette were rejected. LOD0 anatomy, rest feet,
Walking/Running, alternate Hit, axe grip and all timing remain accepted and unchanged.
[Patch receipt](review/round4/cloth_support.json), [all-LOD gates](review/round4/lod_gates.json).
The head-contact mask excludes the intentionally inserted neck below the measured collar top; the old fixed
height misclassified one far-LOD neck vertex. The existing local contact algorithm remains unchanged.
[Diagnostic correction](review/round4/contact_gate_correction.json).

## Review round 4

**Triangle minimisation complete; ready for orchestrator reinstall.**
Replace both runtime GLBs. Integration/actors.yml is byte-identical; no registry merge or timing change is needed.
All eight animation sample streams, channel targets, rest rig, inverse binds, material definitions, embedded
texture payloads and tier ramps are exact matches to round 3. [Parity](review/round4/artifact_parity.json).

Final files and SHA-256:

| File | SHA-256 | Triangles |
|---|---|---|
| export/mm6_dwa1.glb | a5f8a244baa147be6acca916027f5a15b92ff4aff2d6345cdd041088f6a212e6 | 11563 / 5938 / 2091 / 629; shadows same |
| export/mm6_dwa1_axe.glb | 6c9d4f4691a01ac90173de227e1a8287fc900d25f62d89772f24993fe11f0a44 | 2119 / 1248 / 470 / 149 |
| export/mm6_dwa1.blend | ef6db38ee434c9f42ada0e2431aefb70358dad6ea803728fb5550a7283f33684 | Packed reduced LOD0 master |
| integration/actors.yml | a5e41e99c160da963f399c5f88f4e97abeb85e049d6adedc387eb50445d14ba4 | Unchanged |

Previous body hash: 014229b8c1f0f1bd50b2984c5e37fe094a49f5e0a285232c01cb58e9de602071. Previous axe hash: 311ab3f0b7ba7a8bf7d300a1c449f876c2ed75c1791279f1f68caf45c82db120.
All four body/axe colour LODs, shadows, viewer tier GLBs, editable master, clip/LOD/tier/hand/foot sheets and
manifests were refreshed. The production scripts are scripts/round4_*.py; contact_final.py uses the measured collar plane for exposed-head sampling, and validate_export.py now requires
round-4 evidence. [Evidence hashes](review/round4/manifest.json).

At 48 Hz, every clip on every colour LOD passes G4/G5/G6 and cloth contact/stretch.
LOD0 maximum arm p99 is 1.96×; maximum hand stretch
2.818×. Arm/exposed-head/axe/blade penetration and tunic/trouser
surface crossings are zero. Elbows, accepted palm/grip frames, sole planes, visible walking swing,
grounded running, floor, source-relative motion and the 0.71875 s cutting event pass.
LOD0 UV overlaps/collapsed faces remain zero. Final weight-sum error over every colour/shadow skin primitive is
1.34110450745e-07, below 1e-4. check_bindings.py (including check_weights.py) prints no BAD line.
[Final validation](review/final_validation.json), [bindings](review/round4/bindings_check.json).

The viewer passes 24/24 tier/clip switches and 16/16 complete normal/half-speed playbacks, zero errors.
Agent inspection of the refreshed sheets confirms unchanged accepted rest feet, gait, tunic appearance,
alternate Hit and axe design. Native installation, loading, LOD transitions, lighting/shadows and indoor/outdoor
regression remain the orchestrator's checks.

**Additional credits: 0; total 40/100, 60 remain. No assets_dev writes, game launches, builds, shared-file edits
or commits. Workspace lease released at handoff.**


## Review round 6 (running clip) — 2026-10-13

**Running replaced; shared-gate hold remains.** The user accepted the rest of the creature and prohibited
RelaxRunForward. Running now uses the indexed Mixamo `Jogging.fbx` (one 26-frame cycle retimed to 0.8 s), through
the existing rest-delta/world retarget path. Retained the accepted short-leg IK stance trajectory; aligned soles
with travel, corrected the elbow hinge planes, and carried the axe outside the torso with the swinging arm.
The closed grip is unchanged. All Running channel endpoints, including floating-point scale samples, match exactly.

The stopped round-5 rebake was never promoted. This round uses the accepted round-4 export. Geometry, weights, UVs,
materials, images, tiers, inverse binds, node hierarchy and all seven non-Running clips retain their original
binary payloads and definitions. The standalone axe and `integration/actors.yml` are byte-identical. Duration 0.8 s,
stride_length 0.89 and run multiplier 1.55 remain unchanged (nominal model travel 1.3795 m/cycle, 1.724375 m/s).
[Payload parity](review/round6/artifact_parity.json), [source receipt](review/round6/provenance.json).

| File | SHA-256 | LOD0 / 1 / 2 / 3 triangles, before = after |
|---|---|---|
| export/mm6_dwa1.glb | 7c6ba169da76a1578e13648dd33ad9af8d0d3aa9e96733f771c4cf5920d63271 | 11563 / 5938 / 2091 / 629; shadows identical |
| export/mm6_dwa1_axe.glb | 6c9d4f4691a01ac90173de227e1a8287fc900d25f62d89772f24993fe11f0a44 | 2119 / 1248 / 470 / 149; file unchanged |
| export/mm6_dwa1.blend | efb85ac7c0c5d762cce8607f49cad2e86225ceae109b8591f16431c344be4484 | Editable master, Running action replaced |
| integration/actors.yml | a5e41e99c160da963f399c5f88f4e97abeb85e049d6adedc387eb50445d14ba4 | Unchanged |

Previous body hash: a5f8a244baa147be6acca916027f5a15b92ff4aff2d6345cdd041088f6a212e6.
Updated animation streams in `export/mm6_dwa1_lod0.glb`, `mm6_dwa1_runtime_lod0.glb`, `mm6_dwa1_lods.glb`,
and the three `review/viewer/mm6_dwa1_[abc].glb` files. Updated Running's 15 front/side/three-quarter frames,
[Running sheet](review/Running_sheet.jpg), combined clip sheets, viewer manifest, export manifest and checksums.
New scripts: `scripts/round6_*.py`; new shared-runner intent: `gates.json`. Historical work blends remain historical;
use `export/mm6_dwa1.blend` or the round-6 patch path for the current Running clip.

**Validation on this hash:**

- Shared runner directly evaluates the complete runtime GLB and every LOD, filtered only to Running. Bone samples
  at 48 Hz; mesh samples refined to 48 Hz. Raw verdict: **FAIL**, 835 PASS / 39 FAIL / 4 UNVERIFIED
  (plus INFO/N/A), versus baseline 830 PASS / 44 FAIL / 4 UNVERIFIED. [Full verdict](review/round6/final/gates.md).
- LOD0: 100% foot contact; lowest sole 3.68–5.32 mm; maximum yaw L 2.59°, R 3.36°; arm p99 1.5084×
  (pooled 1.4974×), maximum hand stretch 2.806×; axe/body penetration 0 mm; arm/body penetration 0.135 mm.
  Elbow out-of-plane <=0.0023°, trunk lean <=7.82°, maximum measured arm/hand angular acceleration 7076°/s².
  LOD0–2 floor, run contact, yaw, stretch and body/axe contact pass.
- Shared grip thresholds still fail on the accepted grip: LOD0 thumb 3.881 mm / middle 4.643 mm gaps; palm
  angle 68.95°. These are numerically unchanged from baseline (sub-micron export noise). Coarser accepted
  finger meshes have larger gaps. Tunic boundary setup remains UNVERIFIED at LOD0/3; the accepted axe LOD1
  ratio remains 0.589 against the runner's 0.55 guidance.
- LOD3 contact was already 0% under the 10 mm contact threshold. Its sparse sole-patch yaw now measures
  L 16.57° / R 28.99° after aligning Running's higher-resolution soles; **this is a remaining gate failure,
  not a claimed pass or an established false positive**. The complete comparison is
  [gate_comparison.json](review/round6/gate_comparison.json). No accepted mesh/prop modifications were made
  to mask these results. Full technical completion is therefore not asserted.
- Loop endpoint difference: exactly 0 across all 171 Running channels. Final primitive weight-sum error
  1.34110450745e-07 < 1e-4. `check_bindings.py` (including weights) exits 0 with **no BAD line**.
- Viewer: 24/24 tier/clip switches and 16/16 complete normal/half-speed playbacks; zero console errors.
  [Numeric receipt](review/round6/final_numeric.json), [bindings](review/round6/bindings_check.json),
  [viewer](review/round6/viewer_check.json), [playback](review/round6/playback_check.json).

Agent inspection of the enlarged Running sheet confirms upright jogging, alternating arm swing, ground contact,
and the axe following its hand. Native integration remains the orchestrator's responsibility, including disposition
of the explicitly listed shared-gate failures. Only the body GLB needs replacement if integrated; actors/axe unchanged.

Additional credits: **0; total 40/100**. No installs, assets_dev writes, game launches, builds, shared-file edits
or commits. Workspace lease released at handoff. [Hash manifest](review/round6/manifest.json).


## Review round 7 — 2026-10-13

### Running clip: Standard Run

Replaced the rejected Jogging motion with **anim_library/mixamo/Standard Run.fbx** (23 frames at 30 Hz,
source SHA-256 `64d7e112a4ce95b2543cccfea18a4a654f00bde8fddd0612b40bb43261fdd6bb`). Retargeted through the project's existing Mixamo rest-delta/world path.
The source's arm drive is retained, with elbow/weapon clearance fitting, a 10° forward trunk lean and steady
forward head. The calibrated closed axe grip is unchanged. Short-leg IK uses heel strike, toe-off and a 14 cm
swing-lift target, with a smooth recovery and a brief low flight. The pelvis has two equal analytic bobs per cycle;
one constant centre height was fitted across the complete cycle, with no per-frame reach-clamping jumps.

[Running sheet: front, side and three-quarter](review/round7/Running_sheet.jpg), including flight at 0.376 s.
[Clip provenance and fitting](review/round7/provenance.json).

`Running` remains 0.8 s; **stride_length 0.89 is unchanged**. The engine multiplies run stride by 1.55, so
the in-place stance targets move 1.3795 model metres per complete phase. Their backward speed exactly matches
runtime forward travel during stance. Keeping this binding also preserves the accepted Walking stride.
Each foot has 44% stance; the two designed flight intervals are 6% of the cycle each (0.048 s at nominal playback).
Using the runner's <=10 mm contact threshold, measured LOD0 contact is **94.79%**, with lowest sole
**3.87–18.22 mm**. Thus only 5.21% of sampled cycle time has both soles above 10 mm. LOD1 contact 94.79%,
LOD2 89.58%; maximum lowest-sole height 18.22 / 18.22 / 20.03 / 30.65 mm across LOD0–3.
LOD3's inherited 0% contact result remains disclosed below.

Only Running changed in animation data: all seven other clips retain their exact channel definitions and
key payloads. Geometry, UVs, skin weights, textures, materials, tiers, nodes, inverse binds and props are unchanged.
The standalone axe GLB and **integration/actors.yml are byte-identical**.
[Byte/key comparison](review/round7/artifact_parity.json).

| File | SHA-256 | Triangles, before = after |
|---|---|---|
| export/mm6_dwa1.glb | 147694eba52e932b7375b01d0dff4ea3b8b312e9e4780d5209bd5ec334a9a6d9 | Body 11563 / 5938 / 2091 / 629; shadows identical |
| export/mm6_dwa1_axe.glb | 6c9d4f4691a01ac90173de227e1a8287fc900d25f62d89772f24993fe11f0a44 | Axe 2119 / 1248 / 470 / 149; file unchanged |
| export/mm6_dwa1.blend | 63ed49224d132ba68db491767ffc0e314168eb6d1c1bc772cc7cab372c9585bf | Editable master; only Running action replaced |
| integration/actors.yml | a5e41e99c160da963f399c5f88f4e97abeb85e049d6adedc387eb50445d14ba4 | Unchanged |

Previous body hash: 7c6ba169da76a1578e13648dd33ad9af8d0d3aa9e96733f771c4cf5920d63271.
Also updated Running streams in `export/mm6_dwa1_lod0.glb`, `mm6_dwa1_runtime_lod0.glb`, `mm6_dwa1_lods.glb`
and the three viewer tier GLBs; Running frames/sheets, combined clip sheets, viewer/export manifests, checksums,
README and progress record. Round-specific scripts are `scripts/round7_*.py`. Historical work blends are retained;
`export/mm6_dwa1.blend` and the round-7 patch path contain the current motion.

**Validation bound to this final hash:**

- Shared runner on Running, all colour/shadow LODs: **835 PASS / 39 FAIL / 4 UNVERIFIED**, plus INFO/N/A.
  **Zero newly failed gate rows versus round 6.** [Raw verdict](review/round7/final/gates.md),
  [baseline comparison](review/round7/gate_comparison.json). Full technical gate clearance is not claimed.
- LOD0–2 floor/contact, toe direction, arm/hand stretch, body/axe contact, elbow and arm smoothness pass.
  LOD0 yaw L 2.65° / R 3.46°; arm p99 <=1.527×, hand maximum 2.806×; arm/body and axe/body penetration 0 mm.
  Measured trunk lean <=9.994°.
- Pelvis/head jitter **PASS at 48 Hz**: maximum vertical acceleration 3.046 / 3.087 m/s²; maximum vertical
  sample displacement 3.90 / 3.99 mm; half-cycle height mismatch <0.00001 / 0.123 mm.
  [Jitter receipt and explicit limits](review/round7/jitter.json).
- All 171 Running channel endpoints match **exactly**. Final skin-weight maximum sum error
  1.34110450745e-07 < 1e-4. `check_bindings.py`, including weight checks, exits 0 with **no BAD line**.
- Viewer **24/24 tier/clip switches**, **16/16 complete normal/half-speed playbacks**, zero errors.
  [Numeric receipt](review/round7/final_numeric.json), [bindings](review/round7/bindings_check.json),
  [viewer](review/round7/viewer_check.json), [playback](review/round7/playback_check.json).

Inherited exceptions are the accepted rigid-grip gaps/palm-direction threshold, tunic boundary setup, axe LOD1 ratio,
and LOD3 contact/yaw. These are retained in the raw FAIL verdict, not hidden or waived. The revised run introduces
no new failed rows. Agent inspection of the running sheet shows the stronger run, opposed arm drive, forward gaze
and low flight; native visual acceptance remains with the user/orchestrator.

Additional credits **0; total 40/100**. No installs, assets_dev writes, game launches, builds, shared-file edits
or commits. Only the body GLB needs integration; actors and axe need no update. Lease released at handoff.
[Revision hash manifest](review/round7/manifest.json).


## Review round 8 (running height)

2026-10-13. **Running only** was refitted from `anim_library/mixamo/Standard Run.fbx`
(source SHA-256 `64d7e112a4ce95b2543cccfea18a4a654f00bde8fddd0612b40bb43261fdd6bb`). The old high-contact constraint and 40 mm flight cap were removed.
The source's vertical excursion is preserved at dwarf leg scale, symmetrised and rebased to the relaxed Standing height.
Stance is 35% per foot, with source-derived airborne motion and two-bone leg IK. Stride is fitted to natural-height reach;
the hips are never lowered to reach an arbitrary old stride. Rolling heel/toe contact integrates the accepted sole's
actual pivot. The accepted arm, hand, head, torso and axe motion is retained relative to the rising pelvis.

[Running sheet: front, side, three-quarter](review/round8/Running_sheet.jpg) ·
[Source and fitting decisions](review/round8/fitting.json) · [48 Hz measurements](review/round8/height_contact.json).
Agent sheet inspection shows a taller stance, clear airborne phases and preserved arm/axe swing. Native viewing remains
with the orchestrator; no game was launched.

| Measurement | Round 7 | Round 8 |
|---|---:|---:|
| Standing mean pelvis | 0.771762 m | unchanged |
| Running minimum pelvis / Standing | 84.04% | **92.51%** |
| Running mean pelvis / Standing | 85.59% | **95.58%** |
| Running pelvis min / mean / max | 0.64859 / 0.66051 / 0.67251 m | **0.71395 / 0.73768 / 0.77590 m** |
| Left / right foot contact, sole <=10 mm | 47.92% / 46.87% | **36.46% / 39.06%** |
| Both feet airborne, soles >10 mm | 5.21% | **24.48%** |
| Lowest sole min / max | 3.87 / 18.22 mm | **3.90 / 77.66 mm** |
| Peak swing lift L / R | 143.75 / 143.63 mm | **206.21 / 206.44 mm** |
| stride_length, all three tiers | 0.89 | **0.455484** |

The raw source's scaled double-flight envelope is **88.13 mm**; the fitted boots reach **77.66 mm**, with no fixed flight
cap applied to the motion. Shared runner flight threshold is source envelope +10 mm fitting tolerance (**98.132 mm**),
and combined contact minimum is 60%, corresponding to 30% per foot. These explicit config overrides replace obsolete
shared defaults. Source hip excursion is 79.56 mm before leg scaling; fitted excursion is about 62 mm.
Knee flexion remains below the source's 164.39° peak: fitted L **30.96–125.19°**, R **13.38–121.55°**.

**Plant and smoothness:** fixed-sole drift through flat stance is L **0.038 mm**, R **0.019 mm**. Across the full rolling
stance, accumulated contact-point movement is **2.06 / 2.25 mm**, with maximum sub-sample displacement **0.472 / 0.436 mm**
(85 samples per stance, with runtime travel applied). Pelvis/head maximum vertical acceleration is **20.352 / 20.405 m/s²**,
below the retimed, leg-scaled source's **42.005 m/s²**. Half-cycle height discrepancy is <0.00002 / 0.123 mm;
no alternating-step jump. Shared arm angular-acceleration gates pass. [Stance/jitter receipt](review/round8/stance_jitter.json).

**Stride contract and scope:** Running remains 0.8 s. Full-cycle travel is **0.7060002 model m** =
`0.455484 * 1.55`, nominal **0.882500 model m/s**. This matches the engine's run-phase formula.
`integration/actors.yml` changes **only stride_length** on all three tiers; clip names, impacts and attachments do not change.
The engine uses the same stride binding for Walking, so the unchanged Walking keys now play **1.954× faster
per travelled distance**. This is a disclosed integration consequence, not a claim that Walking playback is unchanged.
Preserving both old Walking cadence and this natural-height run would need separate gait stride support or another
Walking change, outside the requested Running-only scope. No shared engine or installed actor entries were changed here.

All seven non-Running clips retain exact channel definitions and key payloads. Mesh positions, topology, normals, UVs,
weights, textures, tier materials, nodes and inverse binds remain exact. Axe GLB is byte-identical. Retained Running
upper-body local channels differ only by floating point roundoff (maximum **1.46e-07**).
[Byte/key proof](review/round8/artifact_parity.json).

| File | SHA-256 | Triangles, before = after |
|---|---|---|
| export/mm6_dwa1.glb | 7cfa9f965984dc2ef9d03b713dcf22ffc6f5f4a66e370abef09177694a9bd5a3 | Body 11563 / 5938 / 2091 / 629; shadows same counts |
| export/mm6_dwa1_axe.glb | 6c9d4f4691a01ac90173de227e1a8287fc900d25f62d89772f24993fe11f0a44 | Axe 2119 / 1248 / 470 / 149; unchanged file |
| export/mm6_dwa1.blend | c626e2a7285a222bbcaa65e00b8ca387260e6c161aae1537aa730d89849973d2 | Editable master; Running action replaced |
| integration/actors.yml | f1fc79f60a35eab95f5690237de9cb07cd3560204ed760c7eafb6a8fddb207f5 | Only three stride_length values changed |

Previous body SHA-256: `147694eba52e932b7375b01d0dff4ea3b8b312e9e4780d5209bd5ec334a9a6d9`.
Also updated the Running streams in `export/mm6_dwa1_lod0.glb`, `mm6_dwa1_runtime_lod0.glb`, `mm6_dwa1_lods.glb`
and `review/viewer/mm6_dwa1_[abc].glb`; Running frames/sheets, combined sheets, viewer/export manifests, checksums,
`gates.json`, README and progress. Production/check scripts are `scripts/round8_*.py`; preserved authoring data is in
`work/round8/`, with the round7 snapshot under `work/round8_before/`. No geometry rebake or prop edit.

**Validation, bound to the final GLB hash:**

- Shared runner on Running, every colour/shadow LOD: **835 PASS / 39 FAIL / 4 UNVERIFIED**, plus INFO/N/A.
  [Raw verdict](review/round8/final/gates.md), [comparison](review/round8/gate_comparison.json).
  Updated posture passes on all LOD rows. LOD0–2 floor/contact/flight, elbow, arm/hand stretch, toe direction,
  torso lean and body/axe clearance pass. LOD0 yaw L/R 2.71° / 3.56°, trunk lean <=9.994°; arm p99 <=1.527×,
  hand maximum 2.806×. No floor penetration.
- Inherited exceptions remain: grip gaps/palm direction, tunic boundary setup, axe LOD1 ratio and coarse LOD3 yaw/contact.
  **One newly failed row** under the revised criteria: shadow LOD3 combined contact is **46.875% <60%** (its accepted
  simplified sole differs from LOD0). Colour LOD3 still measures 0% contact. Correcting those sole meshes would violate
  the frozen geometry scope; the raw failures are retained. This is **not a blanket shared-gate pass**.
- All 171 Running channel endpoints are exactly equal. Skin weight maximum error **1.34110450745e-7 <1e-4**.
  `check_bindings.py`, including `check_weights.py`, exits 0, **no BAD line**.
- Viewer **24/24 tier/clip switches**, **16/16 complete normal/half-speed playbacks**, zero errors.
  [Numeric receipt](review/round8/final_numeric.json), [bindings](review/round8/bindings_check.json),
  [viewer](review/round8/viewer_check.json), [playback](review/round8/playback_check.json).

Additional credits **0; total 40/100**. No installs, assets_dev writes, game launches, builds or commits.
Orchestrator integrates the body GLB and stride entries; axe needs no update. Workspace lease released at handoff.
[Revision hash manifest](review/round8/manifest.json).

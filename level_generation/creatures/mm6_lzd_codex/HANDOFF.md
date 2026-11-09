# HANDOFF — MM6 LizardArch (mm6:lzd)

**Review round 6 (Walking) technical handoff ready.** Other clips remain accepted and unchanged.
Walking is 0.8 s with symmetric bob and wider counter-swing. Bindings/timings unchanged:
Attack/Cast 1.133333333 s, release 0.489583333333 s from Socket_Arrow; Death 2 s, Dead 1 s.

| File | LOD0 / 1 / 2 / 3 triangles | SHA-256 |
|---|---|---|
| export/mm6_lzd.glb | 9854 / 5141 / 2172 / 691 | b879598d9f0a7639a8f61c380738a67a715cb8c6dc78edf6646ba3156df29b54 |
| export/mm6_lzd_bow.glb | 1788 / 964 / 388 / 110 | 2a789f0493c7e79f786771687f8e1c233c64c61586cc1bea301054b9d4c631ff |

[Current review](review/round6/README.md), [receipt](review/review_round6.json), [viewer](review/viewer/index.html).
Install through tools/install_model.py --world mm6 when accepted; orchestrator owns installation and native checks.
Lease released at handoff. No commit. Budget 60/100 credits.
Historical sections below are superseded by Review round 6 where applicable.

## Review round 1

Historical record. Round 2 below supersedes these hashes and bindings; prior evidence is retained in
[round 1 archive](review/round1_archive.json).
The orchestrator found `KHR_materials_specular` on body and bow materials. The earlier runtime validator did not
check material extensions; its previous pass did not establish loader compatibility. This round removes that
extension from the written JSON, including the raw export, LOD intermediates and all three viewer models.
`scripts/package_runtime.py` now finishes with `scripts/finalize_materials.py`; `validate_runtime.py` rejects unsupported
material extensions. The finalizer verifies that every GLB binary payload is byte-identical to its prior revision.
Geometry, texture pixels, UVs, weights, animation bytes, sockets and LOD counts are unchanged. Engine
`openyamm_specular` / `openyamm_specular_mask` extras and `KHR_materials_variants` are preserved.

Updated runtime files (replace the previously installed copies):

| File | SHA-256 | LOD0 / 1 / 2 / 3 triangles |
|---|---|---|
| `export/mm6_lzd.glb` | `0b658dc182537950dbfed94338f82b9b5547739ed212cd22714b29ae6eea84c3` | 12,987 / 6,485 / 2,317 / 756 |
| `export/mm6_lzd_bow.glb` | `cae3edbb2648b8ceee129b0bae2eeb31ba1a9f45a5621784b1cf22e17f01a2dc` | 2,236 / 1,112 / 396 / 116 |

Other re-exported checkpoints and review models (triangle counts are per mesh; the LOD export lists colour and
shadow meshes):

| File | SHA-256 | Triangles per mesh |
|---|---|---|
| `export/mm6_lzd_lod0.glb` | `06815a871eaeaadbc8f48dfd0881d6475764cd9a4b9e712211df463104a26dae` | 15,223 |
| `export/mm6_lzd_lods.geometry.glb` | `569097c78cca9168e6c72280e70777abeb7056e8c78b241ecab0034e59f5f3eb` | 4,626 / 1,749 / 1,222 / 1,647 / 629 / 437 / 532 / 209 / 131 |
| `export/mm6_lzd_lods.glb` | `ef8924c330f5d2775a0267b8433b668f74f8bbfecdb1a7565a4a7fc29dffbdac` | 15,223 / 7,597 / 2,713 / 872 / 15,223 / 7,597 / 2,713 / 872 |
| `export/mm6_lzd_raw.glb` | `51e971d707fc812799565d7e109f7e38b70bf805c99a27a1ad75a823ff912983` | 15,223 |
| `review/viewer/mm6_lzd_a.glb` | `5692b537585c83025bf3db2c0313e24796449a1605a5bcade0d2d3ddb9398125` | 15,223 |
| `review/viewer/mm6_lzd_b.glb` | `726bac28b767e2b77a63638caea0b55540aa96b767a11e24a2f58d46dc7904b3` | 15,223 |
| `review/viewer/mm6_lzd_c.glb` | `950c798910e23993d92efc232dfe645998086416829d49e1ee1218674a5ae38d` | 15,223 |

`integration/actors.yml` **did not change**; SHA-256
`22597079f93d920789741161dbc6e468cc2dc6f462f247b17a1d428888d5ca28`.
Scale, impact **0.734375 s**, sockets and all descriptor bindings remain the same.

Checks repeated on this revision:

- Orchestrator `output/codex_batch/check_weights.py` on both runtime files: exit **0**, **no BAD lines**;
  both print worst `|sum-1| 0.000000`. [Saved output](review/check_weights_round1.txt).
- G4/G5/G6 and posture on all eight clips, exported grip, ranged release and source-relative motion trace:
  pass, with unchanged gate values and existing artistic limits listed above.
- Runtime retention/material validation: pass. All nine re-exported GLBs retain identical binary payloads.
- Shared viewer checker: **24/24** tier/clip switches, no failures or console errors. Four browser captures refreshed.
- Front/side/three-quarter and per-clip sheets, tier sheet, release strip and hand close-ups rebuilt and inspected.
- All project Python scripts compile. One background Blender process, **four threads**.

[Round 1 receipt](review/review_round1.json) records every before/after hash and binary-payload hash;
[material receipt](review/material_extensions.json), [gate receipt](review/gates.json),
[viewer receipt](review/viewer_check.json) and [runtime validation](review/runtime_validation.json) bind the checks to
these exports. No new paid work: **60 / 100 credits** total. No commit, build, game launch or `assets_dev` write.
The orchestrator owns replacement installation and engine checks; the previously installed exports are superseded.


## Review round 2

**Distinct Cast authored; body and bindings ready for re-integration.** The previous `cast: Attack` alias violated
the spellcaster binding rule for LizardArch C. `validate_runtime.py` now checks the distinct clip, palm node, event
range and all three descriptor bindings in addition to material extensions and weights.

`Cast` is **1.4 s**, with a low carried bow, raised/open right claw, forward palm push, an **8 cm** planted step
(**2.5 cm** lift), and a return to relaxed Standing. The peak forward palm speed selects **0.667708333 s**;
palm/target dot is **0.987659**. `Socket_Palm_R` is a new child of `B_R_Hand` (65 bones total).
The native bow Attack remains at **0.734375 s** through `Socket_Arrow`.

The required signed elbow audit also exposed earlier off-plane free-arm bending and an attack twist helper above
90°. `repair_elbow_frames.py` corrects the right-arm frames and limits that helper to 90°, retaining keyed hand
positions within **0.0003 mm**. Mesh topology, positions, normals, UVs and named skin weights are exactly unchanged.
Other existing animation channels agree within **3.06e-7** per component (1,062 of 1,416 byte-identical).

Runtime files:

| File | SHA-256 | LOD0 / 1 / 2 / 3 triangles |
|---|---|---|
| `export/mm6_lzd.glb` | `979c8a0c10f7b5987b7eed2b6c55ff7fa7c2ebebd7efbde4240dce9d7b18e147` | 12,987 / 6,485 / 2,317 / 756 |
| `export/mm6_lzd_bow.glb` | `cae3edbb2648b8ceee129b0bae2eeb31ba1a9f45a5621784b1cf22e17f01a2dc` | 2,236 / 1,112 / 396 / 116 |

The body changed; the bow is **byte-identical to round 1**. Triangle counts remain unchanged at all colour/shadow
LODs. Other refreshed checkpoints/viewer models:

| File | SHA-256 | Triangles per mesh |
|---|---|---|
| `export/mm6_lzd_lod0.glb` | `42cc6c56e2f405acd3b32ff82f7432fd18a8a39a684dcde86db6d74217c9460f` | 15,223 |
| `export/mm6_lzd_lods.geometry.glb` | `4e616d8cf6e34cd2f22bea15c4cd0022cae1e4537755d483a9bb0b42a843dcf4` | 4,626 / 1,749 / 1,222 / 1,647 / 629 / 437 / 532 / 209 / 131 |
| `export/mm6_lzd_lods.glb` | `38b01ffcc1530532a9fb9322b221905256b11703066f117debd1c46b3de59124` | 15,223 / 7,597 / 2,713 / 872 / 15,223 / 7,597 / 2,713 / 872 |
| `export/mm6_lzd_raw.glb` | `f0939702d15b8d91979b3da8fc23906df5f18c3b43a68679bb2b355bc8358404` | 15,223 |
| `review/viewer/mm6_lzd_a.glb` | `c8f8c69d43fa0d5fa3e3aa4deae70400e42a295198acef25f20a5de03bd68813` | 15,223 |
| `review/viewer/mm6_lzd_b.glb` | `4c344d76df883a06f5808c2629c972f5f66324c1f74f6b5eea55ee60b270e0f4` | 15,223 |
| `review/viewer/mm6_lzd_c.glb` | `7a56b80fc933d8286fa3af22bae27144e44535f6a6c994eb68c1fb598bd54c73` | 15,223 |

**`integration/actors.yml` changed** on all three tiers:

```yaml
animation:
  cast: Cast
  sockets:
    palm_right: Socket_Palm_R
  events:
    cast:
      impact: 0.667708333
      launch_socket: Socket_Palm_R
```

Actor snippet SHA-256: `6f4ce6a490575af168fc743806609b38771e1a11134961ac70ca163d74bdc515`.
Scale, yaw, stride, bow attachment and ranged event remain unchanged. The regression proposal now explicitly
checks C's spell gesture, right-palm glow/launch, relaxed transitions and retention of B's bow fire-arrow action.

Checks on these exports:

- G4/G5/G6 and posture pass on **all nine clips**. Worst arm p99 **1.713x** (dominant-arm profile probes **1.99x**),
  hand maximum **2.890x**, body/weapon contact **0 mm**, export motion trace **0 flags**.
- Signed elbow flexion minimum **2.924°**, bend-plane deviation **0.000247°**, applied forearm twist ≤**90°**.
- Cast: no head contact; foot target error **0.000481 mm**, endpoint mesh difference **0.001341 mm** from Standing.
  The socket stays within **8.12 mm** of the deformed palm surface. Right elbow section ratios **0.87–0.95** at
  chamber/release/extension probes; the existing bow attack's compressed section is now **0.33** at full draw.
- `output/codex_batch/check_weights.py` on both runtime files: exit **0**, **no BAD lines**, worst sums print
  `0.000000`. [Output](review/check_weights_round2.txt). Distinct-cast binding/material validation passes.
- Shared viewer: **27/27** tier/clip switches, no failures or console errors. Eleven browser screenshots refreshed,
  including the blue Wizard casting. Front/side/three-quarter, per-clip, hand, release and tier sheets refreshed.
- All project Python scripts compile. No new Meshy jobs: **60/100 credits** total. Blender remained one background
  process at a time with **four threads**; no game launch, build, install, `assets_dev` write or commit.

Review: [Cast sequence](review/cast_sequence.jpg), [Cast views](review/clip_cast.jpg),
[Wizard cast](review/browser/wizard_cast.png), [Wizard palm](review/browser/wizard_cast_hand.png),
[updated hand sheet](review/exported_hands.jpg). Evidence: [round receipt](review/review_round2.json),
[cast/elbow gate](review/cast_gate.json), [all gates](review/gates.json),
[runtime validation](review/runtime_validation.json), [viewer check](review/viewer_check.json).

The orchestrator must replace the installed body **and update/re-add all three actor entries**. The bow may be
retained from round 1 after checking its hash. Native runtime and indoor/outdoor regression remain unrun in this
batch session. Existing head contact, small ground excursions, rigid bow limbs and provenance limits remain listed
above; artistic acceptance is still pending.

## Review round 3

The vertical carry is solved with the hand closed on the wrap in Standing, Fidget, Walking, Running and Hit.
Bow vertical dot is at least 0.9396 and the string's bodyward dot at least 0.8137; maximum digit-to-wrap distance
is **2.957 mm** (limit 3 mm). The free right hand stays beside the body, with palm-to-thigh dot
**0.9796 Walking** /
**0.9565 Running**.

**Cast choice (b)** uses the sourced 2HandBowAttack1 shot. Cast/Attack channels and 198 samplers are identical.
This retains the library's wind-up and weight transfer and the user's accepted bow-spell route. All tiers bind Cast and
launch at 0.734375000 s from Socket_Arrow. The former palm gesture and palm binding are superseded.
Recovery retimes source frames 23–25 to 23–27, adding two frames while preserving the collision-free pose path,
draw and release interval. The aim grip rolls 120 degrees away from the bow arm, with a 5 mm claw-root adjustment to keep the wrap contact. Thirty fractional keys per string preserve a common nock during draw and snap; the export patch retains keys that the frame-only exporter would omit. The right-arm acceleration peak falls from 50.83 to 21.90 degrees/sample² at 48 Hz;
the wrist peak falls from 51.05 to 22.10. Every clip passes its source-relative acceleration limit.

Feet follow the travel direction, including at rest. Measurements below are from the exported mesh/bones at 48 Hz:

| Clip | Foot | Yaw range (degrees) | Minimum sole (mm) | Peak sole height (cm) |
|---|---|---:|---:|---:|
| Standing | L | -0.0001 to 0.0000 | 1.544 | 0.16 |
| Standing | R | -0.0000 to 0.0000 | 0.400 | 0.04 |
| Fidget | L | -0.0001 to 0.0000 | 1.622 | 0.17 |
| Fidget | R | -0.0000 to 0.0001 | 0.400 | 0.04 |
| Walking | L | -0.0293 to 0.0194 | 0.391 | 10.24 |
| Walking | R | -0.0136 to 0.0506 | 0.459 | 10.37 |
| Running | L | -0.0335 to 0.0198 | 0.399 | 14.37 |
| Running | R | -0.0105 to 0.0393 | 0.656 | 14.32 |

Walking/Running keep at least one foot within 1 cm of the floor for 100% of sampled frames. Walk swing knees are
about 61.6 degrees; Running swing peaks are about 14.3 cm. The loin flap follows the leading leg to avoid cloth penetration.

### Reduction and rebake

Body **12,987 -> 9,858** triangles; bow **2,236 -> 1,788**. Combined LOD0 falls **23.5%**, to 11,646.
The next authored body step (9,545) fails SSIM at 0.92868; the next bow step (1,564) fails IoU at 0.98687.
Final body minimum IoU is **0.994625**, SSIM **0.96079/0.96098/0.96081** for actual A/B/C cloth tiers.
Final bow minimum IoU/SSIM is **0.996461 / 0.992048**.
[CSV/plot, method and paired renders](review/reduction/README.md) record the stopping boundary.

All levels rebake base colour, region mask, ORM and tangent normals from the unreduced surfaces. UVs are refitted,
not carried through collapse. Face, fingers, collar, joints and prop contacts are protected.
LOD1/2/3 comparisons use the assembled actor at 550/220/88 pixels; runtime pooled IoU is
**0.987115 / 0.986629 / 0.970200**.
The far comparison uses paired 64-sample renders; the 16-sample trial (0.969931) is retained in the audit.
Isolated far bow overlap is about 0.916 and is not reported as a standalone pass.
LOD2/3 grip radii gained 3%/8% only around the wrap, preserving UVs, maps and counts. All-clip exported grip gaps are 2.647/2.822 mm.
Export removes 7/21/30 lower-body triangles; all lower runtime meshes were reimported and rechecked on all clips.

### Repeated checks

- The final head checker rejects nearest-face-plane hits outside the struck shoulder component bounds. The former far-LOD 44.3 mm report was outside every component; [the geometric audit](review/rebake/head_plane_audit.json) records the proof. The 10 mm limit is unchanged and all four LODs were rechecked.
- LOD0 G4 arm p99 **1.743x**, G5 hand maximum **2.888x**; G5 bad distal adjacency **0**.
- Body, held equipment and cloth penetration **0 mm** at LOD0; head contact maximum **0.412 mm**.
- Signed elbow flexion minimum **4.649 degrees**, plane deviation **0.000294 degrees**, forearm roll <=90 degrees.
- All four runtime colour LODs pass G4/G5/G6, elbow, grip, palm, gait and cloth checks; detailed lower reports include remaining sub-millimetre contacts.
- Ranged event arrow target dot **0.996786**; held string/finger error **0.372 mm**; forward string speed at event **48.779 m/s**. String junction gap stays below **2.587 mm**, measured at 1920 Hz through draw and release.
- All material extensions and skin weights pass **check_weights.py** and **check_bindings.py**, **no BAD lines**.
- Runtime packaging preserves LOD0 body attributes, rig and animation bytes; Cast copy equality checked.
- Viewer **27/27** tier/clip switches, no failures/console errors; 18 browser captures and all clip/hand/tier sheets refreshed.
- [Skin luminance diagnostic](review/skin_luminance.json) records native and controlled-review mean/p95. The review lighting is brighter than native sprites; no skin darkening or skin tier recolour was added. Native lighting calibration remains integration work.
- All project Python scripts compile. No new paid jobs, game launches, builds, runtime installs or commits.

### Changed files and hashes

These are the current exports and review GLBs. Colour/shadow mesh counts are both shown where present:

| File | SHA-256 | Triangles per mesh |
|---|---|---|
| `export/mm6_lzd.glb` | `d108b6862d7f8f9fbd04a6fa98abc7f382e1102835dd237f16be0014ce1f5e5d` | 9858 / 5231 / 2185 / 720 / 9858 / 5231 / 2185 / 720 |
| `export/mm6_lzd_bow.glb` | `12e7db60a4866e655e64a674d478eb83980fc3f0519d77fee3661e1b8b269989` | 1788 / 982 / 396 / 116 / 1788 / 982 / 396 / 116 |
| `export/mm6_lzd_level1.glb` | `8bb00be2577916271ed30df336a4f692a24cba91c5dac31c9b554192a9ac71e9` | 6213 |
| `export/mm6_lzd_level2.glb` | `2aa7e71663fa74cce490fcd3364d7667223318e9d9a041b4007e75eea2c84876` | 2581 |
| `export/mm6_lzd_level3.glb` | `08b2800c1d876d7a92796bd148407be5870500139177a73090996dd8293437c8` | 836 |
| `export/mm6_lzd_lod0.glb` | `0c297c6e23f4bab0cd5bd7fb23eda4a054fa13d076b17cde6bc2cc5faef69b21` | 11646 |
| `export/mm6_lzd_lods.glb` | `11a796547ff6b6e4abc2048ef03b8c06eb05ddc61989e7cfd46fb081c294dc52` | 11646 / 6213 / 2581 / 836 / 11646 / 6213 / 2581 / 836 |
| `export/mm6_lzd_raw.glb` | `0c297c6e23f4bab0cd5bd7fb23eda4a054fa13d076b17cde6bc2cc5faef69b21` | 11646 |
| `review/viewer/mm6_lzd_a.glb` | `a94280f20223cdcefd2d642ab75d43ca2a70d5585a91cb01b946fec41957e783` | 11646 |
| `review/viewer/mm6_lzd_b.glb` | `cec7ba455122f58a3c93d4a80928d0a012508ec75e74c57ad867732963c52e99` | 11646 |
| `review/viewer/mm6_lzd_c.glb` | `eda7be4e30106c3b69affd033330ab46d61fdc500de64e503cff05b7b07918bd` | 11646 |

**integration/actors.yml changed: YES**, SHA-256 `ebb62aba4ea3dd3a70518953c3c2e2786d4bff730ebf054f62d7879d398bb7ee`.
All tiers now use Cast / Socket_Arrow / 0.734375000, with no palm binding. Scale and stride reflect the corrected rest height
and gait. The shared registry was not edited. [Regression proposal](integration/regression.md) is updated for bow-cast release,
carry, palms, forward feet and the new LODs.

Authoring/review changes include `scripts/round3_motion.py`, `round3_grip_fit.py`, `smooth_recovery.py`,
the `rebake_*.py` pipeline, `runtime_lod_gates.py`, `angular_acceleration.py`, `volume_contact.py`,
export/validation scripts, rebaked maps, selected Blender checkpoints, clip/browser sheets, README and progress state.
Additional validation measurements are linked from the [round receipt](review/review_round3.json).

### Remaining limits

- This already-running round retains separate rebaked LOD texture maps and project-local gates. The batch document changed during the round; its Cost controls item 4 explicitly says new rules are not retroactive. Shared-map/16-pixel-margin migration and shared-runner migration were not performed.
- Wooden bow limbs are rigid; string and arrow animate. Carry-to-aim rotation uses the closed round grip without a separate finger regrip.
- At full draw the existing right elbow section compresses to about 0.33 of its reference projected width. Connected skin and deformation gates pass; artistic review remains pending.
- The 88-pixel distance silhouette is close to the 0.97 threshold and is scored on the assembled actor. Standalone far bow overlap is about 0.916; native LOD distance/lighting review belongs to integration.
- Initial primary-image prompts were not retained verbatim; selected images, later exact reference prompts, hashes and all paid Meshy requests/receipts are retained.
- No engine install, game launch, build, indoor/outdoor capture or cross-world regression was performed, per Batch rules. Native lighting/skin comparison and terrain contact still need orchestration.

## Review round 4

- Library RelaxIdle fitted to native image 58: shoulder-line yaw -0.000001 degrees,
  pelvis yaw relative to bind 0, ankle spacing 0.450 m, wrist heights R 0.925 / L 0.960 m, bow elevation 0 degrees.
  The horizontal carry supersedes round 3's incorrect vertical carry.
- Library UnarmedGetHitF1 supplies backward recoil and recovery. Walking has a neutral free wrist/palm toward thigh.
  UnarmedRunForward replaces RelaxRunForward. Active clips meet the new rest at their boundaries.
- Mixamo Shooting Arrow supplies the draw/release motion, with planted legs and anatomical arm fitting.
  Global yaw is bounded to pelvis 32 / shoulders 72 degrees; the head faces the target.
  The drawing hand anchors by the cheek with a straight wrist, and the string faces the archer.
  Arrow visibility begins after nocking. Cast option (b) remains a byte-exact copy, verified by the packer.
- Lower-body waist extends beneath the tunic, and lower tunic weights blend into the pelvis.
  The former draw gap is covered. Welded body boundary inventory records 20 lower-body edges at the
  covered waist (z 1.049–1.156 m), 22 left-arm and 20 right-arm edges at the covered shoulder/sleeve
  interfaces; these are intentional component openings. No open lower-leg boundary was found.
  See review/round4/body_boundaries.json and exported draw/side captures.
- Death uses the library backward fall; the bow drops as fingers open at 1.0 s.
  Reduced feet and grip surfaces are fitted geometrically. Gate thresholds were not loosened.
- All LODs now share the near texture set, accepted resolutions, and 16 px dilation.
  Body embedded images 32 to 8; bow 16 to 4. See the linked reduction curve and paired images.
- integration/actors.yml **changed**: updated scale/stride metadata and round marker.
  Attack/cast release remains **0.734375 s**, socket **Socket_Arrow**, cast **Cast** on all tiers.
  Actors SHA-256: 6f73209bc9b47a8186d76f2eaf923886c420e339c0a17fb7ba2e733cf3c952fe.
- Shared runner **PASS: 7,416 passing checks, zero FAIL, zero UNVERIFIED**, all nine clips and all colour/shadow LODs.
  check_bindings.py and check_weights.py print **no BAD lines**, worst weight-sum error 0.000000.
  Viewer **27/27** tier/clip switches, zero console errors; clip sheets and browser captures regenerated.

Worst per-foot yaw over each cycle, across all colour LODs:

| Clip | Foot | Maximum absolute yaw (degrees) |
|---|---|---:|
| Standing | L | 8.140 |
| Standing | R | 6.278 |
| Fidget | L | 8.140 |
| Fidget | R | 6.278 |
| Walking | L | 8.285 |
| Walking | R | 6.785 |
| Running | L | 8.208 |
| Running | R | 6.480 |

Walking swing peaks are about 97–98 mm; Running has about 97.4% contact and at most 34.5 mm brief flight.
Full per-clip/LOD wrist, elbow, palm, stretch, penetration and floor metrics are in the shared gate report.

Exported file receipt (triangle lists include colour and shadow meshes where present):

| File | SHA-256 | Triangles per mesh |
|---|---|---|
| export/mm6_lzd.glb | 52ba2b1aa9d87d94d2c5580e1eb878ed7b9d0e7f6237e438ecb31913178e3572 | 9854 / 5141 / 2172 / 691 / 9854 / 5141 / 2172 / 691 |
| export/mm6_lzd_bow.glb | 2a789f0493c7e79f786771687f8e1c233c64c61586cc1bea301054b9d4c631ff | 1788 / 964 / 388 / 110 |
| export/mm6_lzd_level1.glb | ff7c52a27192d13da18aa58cbe76d3cbd7cfd74e95c515ec73ea68e7f2d70067 | 6105 |
| export/mm6_lzd_level2.glb | ca8f2b9010aeabdda305c3f6b8330a627fb148493d9c450439413f3aa9234aa0 | 2560 |
| export/mm6_lzd_level3.glb | d3c84938e76524e5fe3f314fc67ff020eaac0141d840d6ddb5c304476a7d64da | 801 |
| export/mm6_lzd_lod0.glb | 6f355070694af89b0d0c6e1c6c88d248438ab824ece0e71963a5d38bbde093e7 | 11642 |
| export/mm6_lzd_lods.glb | ef2f6323172c863d7251e6a24cdd8ee4fca8c189945ae3148572c57eea16daa7 | 11642 / 6105 / 2560 / 801 / 11642 / 6105 / 2560 / 801 |
| export/mm6_lzd_raw.glb | 6f355070694af89b0d0c6e1c6c88d248438ab824ece0e71963a5d38bbde093e7 | 11642 |
| review/viewer/mm6_lzd_a.glb | 3b72d0302cd814a1285e1966668cd0ff21db8a8adba8d9525ff726766347a3cf | 11642 |
| review/viewer/mm6_lzd_b.glb | 9d9719ab1a9ee25e3fc32d669fb0d7c7af420fff2f39a64a8d0bb8116af0e140 | 11642 |
| review/viewer/mm6_lzd_c.glb | bdafec01bec4da7e1a5e245fe6f63f5e4ef946465e9f3b0494d5b7410f287468 | 11642 |

Current inputs: scripts/round4_author.py and round4_repair.py; maps from round4_textures.py;
review/round4/lod_selection.json; near motion/geometry in round4_refit.py;
selected distance geometry exported by round4_distance_export.py; packaging in round4_pack.py. work/master.blend and work/master_export.blend are current editable/export checkpoints.
Source provenance is recorded in work/round4/authoring_intent.json. Historical round-3 exporters are not current inputs.

Remaining limits: bow limbs are rigid while string/arrow animate; far silhouettes are judged at their switch sizes.
No native install, game lighting comparison, indoor/outdoor capture or runtime regression was run:
Batch rules delegate these to the orchestrator. Artistic acceptance remains pending.

## Review round 5

- Separated shoulder plates/pads and belt/tabard. Matched shoulder/pad weights, transferred belt/buckle weights
  from supporting surfaces, tucked the cloth and fitted the distant shoulder surfaces.
  Minimum sampled clearance: shoulders **3.100 mm**, belt **3.569 mm**.
  Hit and all other clips were checked at every runtime LOD.
- Kept the correct root facing. Replaced inherited walking trunk rotations with smooth absolute frames;
  the late-cycle twist is removed and the native front stance retained.
- Death **4.0 -> 2.0 s**. Limited the middle-fall tabard fold to keep it out of the belt.
  Final Death pose and Dead are preserved against round 4 (matrix errors <1e-5); floor gates pass.
- Attack/Cast **1.7 -> 1.133333333 s**. Socket_Arrow release **0.734375 -> 0.489583333333 s**.
  Cast remains an exact copy. Local timing eases retain total duration/release and remove acceleration/finger-step
  failures exposed by uniform retiming.
- integration/actors.yml **changed**: all tiers' melee/ranged/cast event times and review marker.
  Scale 105.473370075 and stride 1.365689918 remain unchanged. SHA-256: **4512bb62bdca027eb489f7fe6bd67406f2971165b4b23f4208fce680e50ae3ca**.
- Standard shared runner: **7,416 PASS**, zero FAIL/UNVERIFIED.
  Worn-layer shared runner: **7,560 PASS**, zero FAIL/UNVERIFIED.
  The real tunic hem opening is explicit; thresholds are unchanged.
- check_weights.py and check_bindings.py: **no BAD lines**. Viewer **27/27**, no console errors.
  Full clip sheets, hand close-ups and browser captures regenerated.
- Counts, UVs and shared texture maps are unchanged. The round 4 reduction curve is historical evidence;
  this scoped correction did no further reduction, texture work or paid generation.

Measured facing over each complete cycle, absolute yaw in degrees:

| Clip | Pelvis | Shoulders | Shoulder/pelvis difference |
|---|---:|---:|---:|
| Running | 0.343 | 1.742 | 1.850 |
| Standing | 0.000 | 0.645 | 0.644 |
| Walking | 3.266 | 1.296 | 4.383 |

Selected editable source: work/round5/retimed_master.blend (also work/master.blend and work/master_export.blend).
work/round5/lod0.blend through lod3.blend retain original-time authoring/static-LOD inputs.
The round5_motion, round5_repair, round5_contact_fit, round5_flap and round5_leg_contact scripts record fitting;
round5_pack packages LODs and round5_retime retimes fresh exports. Do not apply the retimer twice.

Changed/exported file receipt; triangle lists include colour and shadow meshes where present:

| File | SHA-256 | Triangles per mesh |
|---|---|---|
| export/mm6_lzd.glb | dac38defeeecd294b3c5364cd1efcb195ae7473e5a7887b2e4a4a4676d739d56 | 9854 / 5141 / 2172 / 691 / 9854 / 5141 / 2172 / 691 |
| export/mm6_lzd_bow.glb | 2a789f0493c7e79f786771687f8e1c233c64c61586cc1bea301054b9d4c631ff | 1788 / 964 / 388 / 110 |
| export/mm6_lzd_level1.glb | c9a31d53c5a75ca44420032b4288d63dd495c2cc7e745d05fd7faadc09665dba | 6105 |
| export/mm6_lzd_level2.glb | 23ded18db0247f6c831cc334c66c0cce9be5a254b0ca222ebbb3034319900af2 | 2560 |
| export/mm6_lzd_level3.glb | 9933a46206c775418a546036a0ceeb092b120fdc2fcc7ce0e48be893cb87a7ce | 801 |
| export/mm6_lzd_lod0.glb | c7dd90b6411fa79c479c2c2613c5b8e7181868a4eaabeda09d6853f5cfcc468e | 11642 |
| export/mm6_lzd_lods.glb | 253e13f8199fdf3be608ccc936edbd478ed633eee738e068ecaaa7a3bd4e5517 | 11642 / 6105 / 2560 / 801 / 11642 / 6105 / 2560 / 801 |
| export/mm6_lzd_raw.glb | c7dd90b6411fa79c479c2c2613c5b8e7181868a4eaabeda09d6853f5cfcc468e | 11642 |
| review/viewer/mm6_lzd_a.glb | 914e195d7afe41aba98d8bcde0e36cd2a3d0139b9fc5322df785b3912fb563f8 | 11642 |
| review/viewer/mm6_lzd_b.glb | dfc5f9f208f5c797cb915dbc13c501c6380954a0353b2e8a510f32844b485ade | 11642 |
| review/viewer/mm6_lzd_c.glb | a884a76d0bc65efda488b65647584c777d674e2b24e387a4c5437a4c2aae489d | 11642 |

Limits: bow limbs remain rigid while string/arrow animate. Sampled surface checks are not an exhaustive
continuous collision proof. Native installation, lighting, indoor/outdoor captures and game regression
were not run under the batch rules; those remain orchestration work.

## Review round 6 (walk)

Walking only. Other eight clips, bow geometry, all meshes/maps/LODs and event timings are preserved.
integration/actors.yml **unchanged**, SHA-256 4512bb62bdca027eb489f7fe6bd67406f2971165b4b23f4208fce680e50ae3ca.

- Replaced per-frame pelvis grounding clamps with one smooth, symmetric periodic height curve:
  two equal highs/lows per 0.8-second cycle, fitted once to leg reach. Re-solved knees onto the existing foot paths.
  No root translation workaround. A second harmonic flattens the highs without adding extra extrema.
- Both shoulders counter-swing **±25°** opposite the legs; bow follows its accepted grip.
  Free wrist turns gently toward the thigh. Shared palm worst **30.536°**, wrist roll **41.777°**.
- Identical first/last Walking keys; decoded endpoint matrix difference
  **6.39e-08**. Binding stride **1.365689918 m** unchanged.
  Decoded foot-path differences are <= **1.001 mm**
  (sampling/interpolation and closing the old ~1 mm endpoint mismatch).
- LOD0 swing peaks **97.579 / 97.740 mm**, knees **55.863 / 56.004°**, foot yaw **5.150 / 0.925°**.
  Lowest soles **0.5 / 0.1 mm above floor**. All LOD floor/contact gates pass.
- Standard shared runner **7,416 PASS**, layer runner **7,560 PASS**,
  zero FAIL/UNVERIFIED; unchanged gate configs and thresholds.
- Bindings and weights: no BAD lines. Viewer **27/27**, no console errors.
- 48 Hz pelvis/spine/head traces: Pelvis peak vertical speed: 3.187 -> 1.473 m/s.
Pelvis peak vertical acceleration: 115.647 -> 36.108 m/s².
Head peaks: 1.474 m/s and 36.100 m/s².
  The shared runner currently implements arm angular jitter, but has **no translation-jitter gate for
  pelvis/spine/head**. These height/velocity/acceleration traces use its GLB evaluator and are diagnostics,
  not a claimed shared-gate verdict or a replacement custom gate.
- Updated walk sheets and frames 13–15, plus side, front, hand and three-quarter viewer captures.
  Selected source: work/round6/master.blend, also work/master.blend and work/master_export.blend.
  round6_walk.py authors Walking; round6_pack.py replaces only its runtime channels from the saved round-5 baselines.
- **60 / 100 credits**, zero added. No native install, builds, game launches or commit.

| Runtime file | LOD0 / 1 / 2 / 3 triangles | SHA-256 |
|---|---|---|
| export/mm6_lzd.glb | 9854 / 5141 / 2172 / 691 | b879598d9f0a7639a8f61c380738a67a715cb8c6dc78edf6646ba3156df29b54 |
| export/mm6_lzd_bow.glb | 1788 / 964 / 388 / 110 | 2a789f0493c7e79f786771687f8e1c233c64c61586cc1bea301054b9d4c631ff |

| Changed animated export / viewer file | SHA-256 |
|---|---|
| export/mm6_lzd_raw.glb | b61c558195414774f21aa37598a8df26b9188631449dd05fe3b0ff2982843070 |
| export/mm6_lzd_lod0.glb | b61c558195414774f21aa37598a8df26b9188631449dd05fe3b0ff2982843070 |
| export/mm6_lzd_lods.glb | 650e5fc7ebc15868e843101d053cf8883455c80ac4f820120b6452a3cf7c2e3b |
| export/mm6_lzd.glb | b879598d9f0a7639a8f61c380738a67a715cb8c6dc78edf6646ba3156df29b54 |
| review/viewer/mm6_lzd_c.glb | c2ca1cc090c687b5f80f9397fa7d20ce943e533572a4e2a019642e75b068cc75 |
| review/viewer/mm6_lzd_b.glb | 96ebb676ead279b784b6d3cacaba314b7ddb7377162223560f7e1082d6e5743d |
| review/viewer/mm6_lzd_a.glb | cfb78cca8497090debb23cc621a554a72bf406d0758f8c2116815a1361aa9b33 |

Static LOD intermediates and the bow are unchanged. Triangle reduction and texture rebaking were outside this
walking-only correction; existing reduction evidence remains historical.
[Review](review/round6/README.md), [receipt](review/review_round6.json).
Native integration and game checks remain with the orchestrator.

## Texture size (orchestrator, 2026-10-13)

Oversized embedded maps were scaled down (largest side capped at 2048, Lanczos) with no visible difference at close range;
the previous export is kept as `export/mm6_lzd_prelarge_backup.glb`. Geometry, rig, clips and materials are unchanged.

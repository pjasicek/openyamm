# MM6 demon: source-driven attack study

**Authoring follow-up:** [Attack revision 3](../attack_animation_v3/README.md) contains the keyed motion,
corrected forearm/palm orientation, native-inspired right-foot pivot, exported GLB and review. Revision 2 repaired
the reported hand deformation; revision 3 preserves those fixes and adds the foot motion. This document preserves
the earlier source study and its pre-repair diagnostics; its pending findings are historical. The
[later native foot study](feet_review_20261004/README.md) supersedes its fixed-foot assumptions: support stays steady,
but the right foot pivots and the legs flex. The hand mapping correction below was established during authoring.

The native action is a **right-hand claw attack**: lift and open the claw, rotate the forearm upward, lower it,
sweep across the chest, and recover. Both feet remain planted. This study defines the motion and the checks to
perform before building an attack on the supplied Meshy rig. It is not an authored or accepted 3D attack.

[Interactive source/guide review](index.html) · [Six annotated native poses](annotated_native_attack.png) ·
[All 37 planned samples](planned_frames.csv) · [Machine-readable specification](attack_motion_spec.json).

## Evidence and timing

The current native group is `danatka0`, sprite ID **18794**, Demon A descriptor **502**, palette **688**.
`assets_dev/engine/rendering/sprite_frame_data_common.yml` supplies six frames, `dmnatka0` through `dmnatkf0`,
each with `frame_length_raw: 2`. Each frame lasts 16 game ticks at 128 Hz: **125 ms**, total **750 ms**.
`attack2` aliases this same action. `Image1` repeats the frontal bitmap at all octants; there is **one genuine
attack view**, not eight independent views. The five genuine standing views establish the side/rear anatomy.

I inspected all six native poses at magnified pixel resolution, their head/hand details, and the stored standing
views. Source images are native-color RGBA; transparent cyan is hidden RGB, not visible material. Inspection
plates composite them onto a dark background and enlarge by nearest neighbor. No generated restoration supplies
pose evidence. [Source audit](native_reference_audit.json) records the original paths, hashes and alpha bounds.

Native coordinates use the complete **354 × 330** canvas, X right and Y down, with a common ground row 329.
Anatomical **right is screen left**. Blender uses Z up, front −Y and anatomical right −X. Comparisons must keep
one camera/model transform throughout. Do not independently resize each pose to make it appear to match.

The reference has shading and silhouette variations around the feet, but no clear stepping or relocated
footprints. Planted feet are the supported interpretation; exact pixel equality between foot silhouettes is not.
Joint centers are hand estimates with approximately **±6 native pixels** uncertainty. Small visible features
have approximately **±4 pixels** uncertainty. Occluded tips remain unknown. Do not force anatomical impossibilities
to satisfy a guessed pixel center. The supplied Meshy model also differs in proportions and claw/tail shape;
pixel-fit goals are review aids, not evidence that its geometry exactly reconstructs the original.

## Six anchor poses

The original timing is retained. The 3D plan has **37 samples at 48 fps**, including the 750 ms endpoint.
Source anchors occur at samples **0, 6, 12, 18, 24, 30**. Sample 36 holds F. Native art holds each bitmap;
smooth movement between those observations is an extrapolation. F is different from A and from native standing.
An outgoing standing blend belongs outside the 750 ms clip; do not snap to the Meshy A-pose.

| Native anchor / time / sample | Right shoulder, elbow, wrist and claw | Left arm, body, head and tail |
| --- | --- | --- |
| A / 0 ms / 0 | Low outward guard. Upper arm angles down/out, elbow nearly straight in projection, wrist oblique, fingers hooked. | Left arm hangs lower with hooked hand. Head frontal, small snarl; torso upright. Tail mostly hidden behind legs. |
| B / 125 ms / 6 | Upper arm lifts outward; elbow bends. Wrist turns open palm toward camera, three long digits spread toward screen left, thumb above. | Left elbow bends and hand rises alongside torso. Mouth opens more. Gaze stays toward opponent. |
| C / 250 ms / 12 | Elbow remains bent: forearm rotates upward and claw reaches high screen left. Open palm and finger fan visible. This is not a straight whole-arm overhead raise. | Left hooked hand crosses in front of abdomen/low chest as guard. Mouth widest; slight head tilt. Tail appears behind legs toward screen right. |
| D / 375 ms / 18 | Wrist lowers outward toward shoulder/chest height; elbow stays bent and palm remains open. | Left guard drops. Chest and head dip; mouth stays open. Tail remains on screen-right side behind legs. |
| E / 500 ms / 24 | Upper arm turns inward; elbow comes near own side/waist. Forearm crosses in front of chest, fingers extend toward screen right. Maintain separated tips. | Left arm counterbalances down/out toward screen right, fingers hooked. Small torso turn/lean and head tilt, rather than a full body spin. Tail appears toward screen left. |
| F / 625 ms / 30 | Arm lowers, hand recurls through proximal joints. Return to the observed F guard. | Left arm lowers. Head/torso return toward front, mouth returns toward a snarl, tail settles. Both feet still planted. |
| Endpoint / 750 ms / 36 | Hold F. | Hold F; prepare an external standing blend. |

These manually marked native centers define the arm directions. Full tip/head/clasp annotations and uncertainty
are in the JSON. The three main tip markers use **screen order only**; their positions do not establish which
native finger corresponds to the Meshy Index/Middle/Pinky bone labels.

| Pose | Right shoulder → elbow → wrist, native px | Left shoulder → elbow → wrist, native px | Right / left projected elbow bend |
| --- | --- | --- | --- |
| A | (141,120) → (119,156) → (87,189) | (209,120) → (221,165) → (241,213) | 12.7° / 7.7° |
| B | (142,120) → (111,143) → (76,143) | (209,121) → (219,155) → (215,172) | 36.6° / 29.6° |
| C | (141,122) → (101,139) → (55,105) | (209,124) → (216,155) → (202,165) | 59.5° / 67.2° |
| D | (142,124) → (101,151) → (71,140) | (211,128) → (222,176) → (235,199) | 53.5° / 16.6° |
| E | (143,127) → (149,165) → (188,163) | (210,126) → (245,192) → (271,211) | 84.0° / 25.9° |
| F | (141,120) → (121,165) → (94,210) | (209,121) → (222,170) → (247,229) | 7.0° / 8.1° |

Projected bend is the angle between the two 2D segments, with 0° meaning straight. **It is not a recovered
3D elbow angle.** Foreshortening and guessed joint centers affect it. In particular, D→E and E→F screen guides
can temporarily make the forearm very short in projection. The real arm must retain its length in depth.

## Actual rig mapping and prerequisites

The study uses an isolated copy of `mm6_demon_rig_corrected.blend`. The accepted corrected GLB/Blender files,
original imported rig, Walking/Running actions and native art remain unchanged. Tests clear animation only on
the study copy and reset its pose after each probe. No attack action has been created.

### Arms and shoulders

Use `mixamorig:RightShoulder/LeftShoulder`, `RightArm/LeftArm`, `RightForeArm/LeftForeArm` and `RightHand/LeftHand`.
Derive rotations from real joint centers in one coordinate space and convert into bone-local transforms only
after parent evaluation. Use persistent elbow poles and quaternion interpolation with consistent hemispheres.

Measured rest lengths on the current rig are:

| Chain | Right | Left |
| --- | --- | --- |
| Upper-arm joint center → elbow center | 0.309114 | 0.308943 |
| Elbow center → **Hand.head** wrist center | 0.405831 | 0.406701 |
| ForeArm displayed bone length | 0.306987 | 0.308821 |
| ForeArm.tail → Hand.head offset | 0.098843 | 0.097879 |

The wrist is about **0.098 model units beyond the displayed forearm endpoint**. Use `Hand.head` for pose fitting,
not `ForeArm.tail`; do not connect the hand to that tail and shorten the character's anatomy. Fixed-length IK
must respect the actual child offset. The 2D guide must never become independent XYZ translations of bones.

Shoulder horn chains `Bone_036` and `Bone_041` are attached to the respective shoulders after the earlier repair.
The isolated right-arm raise moved the shoulder tips by **0.0 units** with the shoulder held fixed. A small
clavicle lift can accompany B/C (initial seed up to 4°), but horns must follow that shoulder rigidly, rather than
following forearm rotation or stretching. Check harness straps and clasp after shoulder and spine movement.

### Hands and rigid claws

The initial probe omitted **Ring** and the fourth terminal bones. Each actual hand has **Thumb, Index, Middle,
Pinky and Ring** branches, with four bones per branch. The supplied mesh has **four long claws plus a thumb**;
the native attack exposes three long claws plus a thumb. Authoring preserves the supplied mesh and validates
all ten actual claw tips. The original four-branch probe below is incomplete and remains a historical diagnostic.
Opening C should come from proximal finger flexion/extension and controlled fan spread. Keep the terminal
claw shape and local curvature intact. Do not use scaling to make the fingertips reach their source marks.
The native open fingers are straighter than the supplied model's curved claws; review this shape difference
explicitly rather than flattening a rigid claw with skinning.

For every anchor, mark actual mesh tip vertices, palm center, wrist center and digit bases. Record all ten
pairwise tip distances in 3D and in the comparison projection. The distances **should change** as the hand
opens; each claw's own length/curvature should not. Keep consistent digit identities through the sweep.

An isolated half-straightening test rotated the second knuckles by approximately **13.95° Index, 11.62° Middle,
11.98° Pinky**, while leaving distal local rotations unchanged. Distal regions selected by bone weights showed:

| Selected region | Maximum edge-length ratio | Finding |
| --- | --- | --- |
| Index | 1.000016 | Essentially rigid in this limited probe. |
| Middle | 1.000016 | Essentially rigid in this limited probe. |
| Pinky | **1.125743** | A distal finger region stretches; inspect affected edges and repair partition/weights if they belong to the hard tip. |
| Thumb | No selected edges | Measurement inconclusive; establish actual semantic tip geometry. |

This is a **weight-based diagnostic**, not a semantic ivory-tip mask or proof that all hand poses are safe.
The measured Index–Middle and Middle–Pinky selected-surface gaps remained positive in this one probe, but that
does not prove complete finger/body nonintersection. See [finger report](finger_control_study.json) and the
`probe_right_hand_*` front/profile images. Resolve Pinky stretching and define complete hard-tip masks before
accepting C, E or their subframes.

### Head and jaw: current control fails

Candidate jaw bone **`Bone_025`**, parented to `mixamorig:Head`, has its pivot inside the forward muzzle rather
than at a convincing rear jaw hinge. Its weights affect the upper face and skull as well as the chin.

Isolated opening tests with the head held fixed displaced the upper face by **0.01019 units at 12°** and
**0.02027 units at 24°**. The 24° probe also moved upper-skull points by 0.01095 units. Front/profile images
show the muzzle/upper teeth moving with the chin. This is not a clean jaw opening.

Before authoring the observed wide C/D mouth, position a defensible mandibular hinge and isolate lower jaw /
lower teeth weights. Upper muzzle, upper teeth and skull must remain with Head. Check inside-mouth geometry,
lip seams and tooth clearance from profile, not just a frontal dark mouth gap. Repeat the isolated control test
and inspect opening/closing before using it in the attack. Do not compensate by moving the entire head.

Head yaw/tilt should stay small; the native head remains largely directed toward the opponent. Express head
orientation as a world target, then solve its local compensation after torso motion. Otherwise torso + head yaw
can accidentally double the intended turn. Keep eyes and upper face coherent during the snarl.

### Torso, feet and tail

Use Hips and the existing spine chain for restrained chest dip/yaw; keep object/root scale fixed. Both sole
patches retain the same footprint. Solve hips/knees for contact if a small body-height change is necessary.
There is no source-supported lunge step, jump, humanoid toe curl or sideways foot roll in this attack.

Tail chain is **Bone_020 → 019 → 018 → 017 → 016 → 015**. Bone_020 also blends a small belly region: an isolated
10° base rotation moved belly vertices by up to **0.00262 units**. Start with this root fixed and distribute
restrained movement through 019–015. Add at most one or two samples of distal lag if it improves the motion;
the exact lag and tail depth are inferred. Follow the visible C/D right-side contour and E left-side contour,
keep the tail behind the legs, and inspect the supplied model's much larger blade-shaped tip for collisions.

## Extrapolated samples and initial rotation targets

Every one of the **37 rows** in [planned_frames.csv](planned_frames.csv) contains both projected arm directions,
projected elbow bends, body/head/palm/finger/jaw/tail control seeds, movement instructions and checks. The JSON
also contains per-frame source/target landmarks. Each frame uses the following phase-specific intent:

| Samples | Interval | Movement to construct and verify |
| --- | --- | --- |
| 0–5 | A→B | Lift right upper arm outward, bend elbow, turn palm forward and open proximal fingers. Left elbow bends/hand rises; jaw begins opening. Do not lift shoulder horns with forearm motion. |
| 6–11 | B→C | Rotate bent right forearm upward, not the entire straight arm. Preserve palm face and finger ordering. Left claw enters low-chest guard with real surface clearance; jaw approaches maximum. |
| 12–17 | C→D | Lower right wrist while retaining elbow bend/open hand. Left guard drops. Chest/head dip through rotations; jaw stays open. Inspect elbow volume and the crossing arm surfaces. |
| 18–23 | D→E | Sweep right forearm in front of chest while upper arm turns inward. Keep fixed forearm length even when foreshortened; use depth to avoid an elbow flip or chest penetration. Left arm extends down/out; tail reverses subtly. |
| 24–29 | E→F | Retract right hand away from torso and lower it; recurl proximal finger joints. Left arm settles. Head/torso recover and jaw closes; inspect return sweep clearance as carefully as outgoing sweep. |
| 30–36 | F hold | Hold the recovered native F pose to the 750 ms endpoint. Preserve both footprints and avoid a discontinuity before a later standing blend. |

The source determines ordering, visible directions and extremes. It does **not** uniquely determine hidden
depth, local Euler angles or muscle deformation. These initial semantic rotation/control seeds make the
inference explicit and provide a starting point for fitting the six anchors:

| Target | A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- | --- |
| Torso world yaw | 0° | −3° | −6° | 0° | 16° | 0° |
| Torso nose-down pitch | 0° | 0° | 2° | 7° | 8° | 0° |
| Head world yaw | 0° | 0° | −4° | 0° | 10° | 0° |
| Head nose-down pitch | 0° | 0° | −2° | 4° | 6° | 0° |
| Head screen-clockwise roll | 0° | 0° | 2° | 0° | −6° | 0° |
| Clean jaw hinge opening, **after repair** | 0° | 5° | 18° | 17° | 10° | 0° |
| Right finger extension, normalized | 0.10 | 0.75 | 1.00 | 0.90 | 0.90 | 0.15 |
| Right finger fan half-angle | 5° | 14° | 18° | 15° | 12° | 5° |
| Right thumb spread | 10° | 22° | 28° | 24° | 20° | 10° |
| Tail total world-Z bend | 10° | −4° | −12° | −14° | 12° | 4° |

These are **fitting seeds**, not measured native angles, existing bone-local rotations, or final accepted values.
Calibrate the guarded snarl and proximal finger extension range on the actual mesh first; zero hinge opening
means that calibrated baseline, not an assumption that the imported rest pose is native A.
Positive world-Z yaw turns a forward −Y direction toward +X; positive nose-down pitch rotates forward toward
−Z. Define roll from the comparison screen. Resolve local bone axes from actual rest matrices instead of
copying these numbers into local Euler channels. Tail bend is a distributed-chain target, not a root rotation.

Use fixed-length rotation/IK poses for the anchors before interpolation. Quaternion interpolation and a stable
elbow pole provide continuous joint motion. The CSV's screen lines are approximate fitting guides only: linear
interpolation of 2D joint centers can collapse the apparent forearm during the sweep. Do not translate/scale
the rig to reproduce that collapse. Inspect intermediates in profile and revise depth/arc where required.

A restrained easing seed is recorded for secondary rotations; do not force a stop at every intermediate native
anchor. Once anchor poses pass, use continuous tangents through B/C/D/E and inspect speed/acceleration so the
stroke reads as one attack. Preserve the 750 ms duration. More output samples improve sampling; they do not
automatically improve choreography.

The visual stroke reaches E around 500 ms. That does **not** establish a gameplay damage event there:
the current actor attack path completes impact at action completion. This work defines appearance only and
does not alter combat timing or add an engine event.

## Verification before accepting the future clip

Check **each of 37 output samples**, plus quarter-sample evaluations over the whole clip (**145 times including
endpoints**). Numerical checks identify likely faults; front/profile/rear/three-quarter renders must judge
actual mesh anatomy. Review hands, face, elbows, shoulders and foot contacts at 100% detail as well as full-body
silhouettes. A valid skeleton alone does not pass.

| Check | Required observation / initial measurable review target |
| --- | --- |
| J — joints | Actual shoulder→elbow and elbow→wrist lengths stay fixed to relative error ≤1e−5; bone/object scale remains one. No reversed elbow pole, unexpected twist or discontinuous wrist rotation. |
| S — attachments | Shoulder horns stay rigid in shoulder space; forearm spines follow forearms. No thin fans or stretched horn roots. Harness/clasp remain attached without ballooning, tearing or losing chest contact. |
| C — claws | Mark real semantic hard-tip vertices, not only bone endpoints. All hard-tip edges retain length within 1% as an initial review limit; tip shape/curvature remains consistent. Record all six pair distances per hand, including projected order/spacing. No fingertip swaps, merged digits or hand self-intersections. Existing Pinky/Thumb probes are not a pass. |
| B — body clearance | Evaluate mesh surfaces at both attack and return sweeps, especially left guard C and right forearm E. Aim for ≥0.003-unit visible hard-surface clearance where surfaces should separate; no chest/harness/opposite-hand penetration. Bone-center distances do not establish this. |
| H — head/jaw | During an isolated jaw test with Head fixed, upper skull/muzzle/upper teeth move ≤0.0001 units; jaw/lower teeth hinge as intended. Review mouth cavity and seams, upper/lower teeth collisions, gaze and head tilt. Current jaw control fails this prerequisite. |
| F — feet | Contact patches stay within 0.002 units of their intended planted position; floor penetration ≤0.002 units and no visible hovering. Foot orientation stays flat without toe curling/sideways roll. Inspect forefoot and heel independently. |
| T — tail | Chain lengths fixed, smooth bend, restrained distal lag; no belly pull, thigh penetration, floor piercing or rigid-blade collision. Source-hidden portions remain a cautious inference. |
| P — pose/readability | Fixed-camera source comparison: retain hand-height/direction, elbow location, claw fan, head/chest movement and planted stance. Approximate joint/feature residuals use the uncertainty above. Inspect silhouette, muscle volume, collapsed/inverted triangles and actual surface shading in all review directions. |

These tolerances are **planned acceptance targets**, not achieved results. Track residuals and explain real
limitations rather than relaxing thresholds silently or claiming every pose is undeformed from one probe.
Near-singular projection, soft seams and legitimate skin flexion require visual judgment; rigid anatomy does not.

After a satisfactory Blender clip, export a new staged file and **reimport the actual GLB**. Repeat sample,
duration, joint/mesh and visual checks on the reimport. Confirm 750 ms, nonlooping attack, F endpoint and preserved
Walking/Running clips. Retain any needed attack2 alias in delivery metadata rather than fabricating a second
motion. Only then record attack acceptance. Texturing and gameplay installation remain separate work.

## Completion of this study

Completed: native inventory/timing/view audit, inspection of all six attack poses and standing anatomy views,
isolated arm/jaw/tail/finger control probes, source landmark annotations, a 37-sample motion specification,
and concrete pose/deformation criteria. Input hashes match the accepted corrected rig and original source.
The local interactive reviewer was checked in headless Chrome: six images loaded, all 37 timeline states
displayed their 15 fitting seeds and eight check categories, with no browser errors. This checks the study
viewer only; it does not establish deformation quality. [Viewer check](reviewer_check.json).

Pending before attack acceptance: clean jaw control, Pinky hard-tip diagnosis/weight correction if required,
complete semantic digit markers, six fitted 3D anchors, interpolated motion, complete visual/mesh review and
actual GLB reimport. This distinction is recorded in the JSON; no authored attack or final deformation pass
is being claimed. All study outputs are local to this directory; native assets and accepted packages remain intact.

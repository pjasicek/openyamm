# Authored goblin execution

User authorized execution of the saved plan, with a hard maximum of **15,000 optimized/exported triangles**.
This includes the sword, eyes, teeth, jewelry, all clothing, and evaluated thickness. Final artistic textures
remain the user's Meshy work. Historical sources are preserved as references.

## Start

- Blender 5.2.2 LTS launched on the desktop; default scene was clean and unsaved.
- Blender MCP scene inspection, Python execution and viewport capture verified.
- The installed add-on supports the operations needed here; no add-on or preference changes made.
- Author a new owned scene and new mesh topology. Dense source may guide surface placement or later bakes.
- Preserve native identity, action intent and timing; export an editable project and matching rigged/unrigged GLBs.

## Construction and corrective reviews

- Authored connected torso, limbs, branching palms/fingers, four-toed feet, skull, cupped ears, eye sockets and
  mouth opening. Welded the neck boundary. Dense Meshy surfaces served only as local placement/baking guides.
- Built separate gorget, shoulder/back plates, bracers, shin guards, belt, 17 skirt strips, right pouch,
  right-ear hoops, claws and curved sword. Thin shells and major spikes consume geometry; surface wear is deferred.
- Reviewed plain-shaded front, oblique, side, rear, face and hand views. Corrected exposed eye rows, regular teeth,
  neck continuity, chest/armor clearance, rounded strip shading and belt penetration.
- Created a local 72-joint skeleton, including finger chains, two forearm twist helpers, shoulder and skirt controls.
  Corrected thumb-web weighting and kept thumb orientation relative to the hand to avoid a twist at the palm.
  Fitted the four finger chains around the hilt and solved the opposed thumb separately.
- Fitted animated skirt flare and shoulder clearance against posed skin. Corrected the prone transition’s foot
  pivot so the model did not need a large whole-body lift to clear the ground.
- Authored standing, walk, attack, hit, death, held corpse and fidget. Native clip timings are retained; the attack
  crosses the body and the hit uses the left forearm. Constraints and cloth simulation are not exported.
- Created a shared 2K UV atlas with extra face/hand density. Changed the body unwrap to minimum-stretch with
  additional cuts, then separated 54 remaining folded faces into planar charts. The evaluated triangle count
  stayed unchanged. Final binary validation found no positive-area UV overlap or collapsed UV triangles.
- Baked an optional tangent-normal proof from isolated face/bare-torso portions of the dense sculpt, with influence
  fading out on mismatched regions. This is not a final color/PBR texturing pass.

## Delivery checks

- Actual rigged and unrigged GLBs: **12,916 triangles**, 26 mesh parts, 11 placeholder material regions,
  10,589 GLB vertices after splits; rigged asset has 72 joints and at most three normalized influences per vertex.
- No unrelated default scene objects or dense guide geometry in either GLB. An initial exporter scope error that
  included the default cube was corrected by restricting export to the active scene.
- Matching bind triangles/UVs between the two handoffs, within 0.002 mm numerical tolerance. The unrigged sword
  has a documented parking transform; its local surface matches the rigged weapon.
- Seven correctly timed clips in the delivered binary. Reimport checked all joint positions and skin/sword
  surfaces at 21 poses; maximum surface discrepancy was approximately 0.004 mm.
- Fixed-view and motion previews render the reimported delivery GLB. Review and handoff notes distinguish
  technical portability from visual approval and engine installation.

Current status: **modeling handoff delivered for visual review and the user’s later texturing pass**.
No engine assets were installed, no renderer code changed, and no Meshy generation/texturing job was submitted.

## Hand-side correction after user review

Screenshots 2095–2097 identified the reversed grip and the front-facing relaxed hand; 2098 supplied the native
comparison and the user clarified palms toward hips. The first delivery's bind hands had their thumbs inward and
their dorsal surfaces forward, but the pose code incorrectly flexed fingers toward local +Z (the dorsal side).
The sword had consequently been fitted to the wrong side. This was an anatomical posing error that the earlier
portability checks did not detect.

- Reversed flexion to local −Z, refitted the four right finger chains and opposed thumb, and moved the existing
  sword/attachment 50 mm in bind +Y onto the palm side. The blade, hand topology and UVs remain the same.
- Turned the left relaxed palm toward the hip and kept thumbs forward. Distributed roll through existing distal
  forearm twist bones, with explicit hand orientations for attack, hit and death.
- Inspected both grip sides, the relaxed hand, front/quarter views, raised attack, hit and prone corpse.
- Rebaked all seven clips and exported both GLBs. Still **12,916 triangles** with unchanged UV allocation.
- Added a focused check for the actual failure: inward palm/forward thumb directions, palm-side finger flexion,
  and fixed hilt attachment across 35 baked action samples. Repeated binary/UV validation and 21-pose reimport;
  all passed, maximum reimported surface difference remains approximately 0.004 mm.
- Refreshed previews from the delivered GLB and preserved the earlier stills in
  `review/hand_correction/before/`, plus `checkpoints/before_hand_correction.blend`.

[Before/after hand review](review/hand_correction/index.html). This correction is ready for the user's visual review;
it does not imply final art approval.

## Relaxed thumb and neutral neck follow-up (screenshot 2100)

The left thumb attachment was on the radial side, but its unposed chain still curved toward dorsal local +Z after
the previous finger-curl fix. Authored a relaxed hand-relative thumb pose into local −Z, maintaining the existing
attachment and web weights. The thumb is now slightly opposed toward the palm in all free-hand poses.

The neck rings were centered in the bind mesh. A −2° local chest tilt followed by +2° head counter-tilt displaced
the head approximately 7.7 mm sideways in standing. Removed both offsets from standing and the matching fidget
baseline. Neck and head bone centers now remain on X=0 during the idle cycle; action-specific turns are retained.

Reviewed the relaxed hand from outer, front and inner views, and the neck from a straight-on close-up. Rebaked all
seven clips and refreshed the exported-GLB previews. Hand checks now also verify relaxed thumb opposition across
35 samples and neck/head centering throughout idle. Binary, UV and 21-pose reimport checks pass.
The unrigged texturing file remains byte-identical; the budget remains **12,916 triangles**.

Preserved the preceding project in `checkpoints/before_thumb_neck_correction.blend` and preceding stills under
`review/thumb_neck_correction/before/`. [Before/after review](review/thumb_neck_correction/index.html).

## Attack, upper-arm swing and shoulder-cap correction (screenshots 2101–2103)

Reviewed the annotated attack screenshot, native attack/walk/hit/fidget/death sheets, and restored front-facing
attack B/C/D frames. The reported failures had separate causes: world-space wrist targets kept walking elbows
too fixed; the attack pointed the blade without aligning its cutting edge to travel; and shoulder clearance
used discrete nearest-surface offsets that changed abruptly between frames. The head lacked the native lift
and turn during preparation.

- Replaced walking wrist targets with shoulder-driven swings and soft elbow bends. Both arms remain slightly
  away from the hips and oppose each other. Slowed the cycle from 0.75 to 1 second for the requested cadence;
  other action durations remain unchanged.
- Authored a continuous upward preparation, diagonal descending cut, side follow-through and recovery. During
  the downstroke, the cutting edge follows transverse blade travel. The entire hand rotates with the fixed
  sword attachment, preserving the corrected palm-side grip.
- Added chin lift, slight head turn and a small neck contribution during preparation, then a downward tracking
  motion through the cut. The neutral standing neck remains centered.
- Lowered the preparing sword elbow to match the native silhouette. Authored the free arm relative to the torso
  so its elbow stays below the preparing hand and it balances the turn without being pulled across the chest.
- Replaced stepped shoulder offsets with continuous direction following, independent of humerus axial roll,
  plus a bounded elevation offset. Reviewed raised attack, hit, walk, and prone poses. This is an attachment
  fitted for these clips, not a claim that arbitrary poses are collision-free.
- Rebaked all seven actions, retaining **12,916 triangles**, 72 joints and the prior UVs. The texturing GLB is
  byte-identical to the previous handoff. The rigged GLB now contains the revised one-second walk.

Focused motion checks cover 337 baked frames at 48 fps. Walking upper-arm excursion is now approximately
45.5° right / 49.3° left, versus 25.7° / 19.2°. Arm-swing correlation is −0.9999. Maximum per-frame shoulder-cap
translation relative to its shoulder is 0.76 / 0.82 mm, versus 12.04 / 13.03 mm. Minimum cutting-edge alignment
with transverse travel during the downstroke is 0.9945. Preparation reaches about 25° upward head pitch; the
world-space head turn includes the torso's turn. Loop endpoints agree within numerical tolerance.

The previous grip/thumb/neutral-neck checks still pass across 35 samples. Binary and UV checks pass; the
21-pose reimport comparison again measured about 0.004 mm maximum skin/sword difference. New front attack and
side walk previews supplement the seven usual motion previews, all rendered from the actual reimported GLB.

Preserved the prior project in `checkpoints/before_motion_correction.blend` and its clips/source under
`review/motion_correction/before/`. [Motion comparison](review/motion_correction/index.html), including the native
and restored head references. No final texture generation or engine installation was performed.

## User-supplied Meshy PBR integration

Received `Meshy_AI_mm6_goblin_texturing_0928122704_texture.glb`. Meshy retained all 12,916 triangles, vertex order,
UV values and triangle connectivity, while combining the 26 parts into one material/mesh. Its 2K base-color,
packed metallic/roughness and tangent-normal images were extracted verbatim and archived with the source GLB.

Applied the returned material maps to the existing authored parts, retaining their UVs, semantic material regions,
skeleton, weights and clips. Saved separate `mm6_goblin_textured.blend` and `mm6_goblin_textured_rigged.glb` candidates;
the earlier untextured files remain unchanged. The three exported image payloads match the return byte-for-byte.
All action channels, bind triangles/UVs, joint order and inverse-bind matrices match the preceding delivery.

Face close-ups exposed a generated paint defect: Meshy placed an additional pair of eyes above the real eye
openings. Comparison with the original eye materials confirms this is skin texture content, not an import or UV
shift. Compared Meshy's normals with the old sculpt proof; neither normal choice removes the extra painted eyes.
The candidate retains the incoming Meshy maps and records the needed local face cleanup explicitly.

The textured GLB passes the structural audit and 21-pose reimport check, with approximately 0.004 mm maximum
skin/sword discrepancy. Focused previews cover front/side/back, face, hands, prone corpse, and walk/attack playback.
[Textured review](review/texturing_20260928/index.html), [material notes](textures/meshy_20260928/README.md).

## Eye paint and walking-foot correction

The user requested fixing the eyes and checking walking foot angles against the native animation.
Preserved the incoming textured Blender scene in `checkpoints/before_eye_feet_correction.blend` and the previous
validation receipts beside the original texture review. The raw Meshy GLB/JPEG maps and modeling deliveries are
unchanged.

Used built-in imagegen once to remove the two misplaced skin-painted eyes from a cropped UV patch, preserving
the surrounding olive skin. Mechanically placed the selected patch through two small feathered atlas masks;
neutralized the corresponding false iris normal and roughness shapes. The mask covers 5,730 pixels, 0.137% of
the atlas. All decoded pixels outside it are identical to the Meshy return. Restored the separate modeled eye,
iris and pupil materials, so there is now one aligned eye pair. No geometry or UV movement was needed.
The selected output, input crop, exact prompt, maps and mask are in `textures/eye_repair_20260928/`.

Compared the native six-frame front/side walk and restored references. Native b/e frames show toes-up landing;
c/f show a much more elevated trailing heel. Our previous motion used only 8° toe lift and 18° push-off and kept
the sole too flat. Increased these to 26°/38° and calculated the ankle height and pivot offset from the real sole
vertices. The foot settles onto its sole before rolling forward; swing clearance is about 12 cm. These angles
interpret native silhouettes, rather than claiming to recover native joint data. Feet remain forward-facing;
there is no added lateral splay or ankle roll. Individual toes remain rigid with the existing foot bone.

Rebaked only walk. Binary comparison confirms that only leg and skirt channels changed; all six other actions,
the walk's upper-body/root channels, geometry, UVs, weights and inverse-bind matrices are identical. Both source
and reimported GLB were checked at 97 half-frame samples: planted sole clearance is 1.1–2.8 mm and no ground
penetration occurs. All-joint loop closure error is below 0.001 mm. The 21-pose complete-rig reimport check still
passes with approximately 0.004 mm maximum surface discrepancy. The budget remains **12,916 triangles**.

Refreshed the textured `.blend` and rigged `.glb`, packed the repaired maps, and rendered the actual reimported
GLB: eye close-up, attack preparation, standing views and four walk views. The new
[interactive comparison](review/eyes_feet_correction/index.html) includes native frames, old/new side motion,
foot close-ups, front motion, speed control and frame stepping. No engine installation was performed.

## Whole-body walking correction (screenshots 2117–2118)

The screenshots expose a larger missed motion feature: the native side view alternates a visible chest and back,
while the authored walk barely turns its torso. Measurement confirmed only ±3° chest yaw, almost zero head yaw,
3.5° forward lean and 0.20 m ankle separation at contact. The previous side comparison also aligned opposite
leading legs between the original and model, obscuring pose correspondence. The foot-only correction was too narrow.

Reworked only the walk action. The hips now turn about ±10° while distributed waist/ribcage rotation brings the
chest to about ±36°. The head counter-turns to track travel, with roughly ±13° yaw. Added about 12° forward lean,
a modest lateral shift and the correct height phase: lower at contact and higher over the supporting leg. A longer
stride increases ankle separation at contact to 0.53 m. Extended stance to 68% of the cycle so the trailing foot
remains planted at the opposite heel strike, then rolls through push-off. Existing 26°/38° foot rotation intent,
actual sole-based contact and shoulder-led arm swings are retained and coordinated with the body.

Frame 1 now matches native B: right leg and left arm forward, chest exposed to the fixed side camera. Frame 25
matches E with the other leg forward and the back exposed. The revised review shifts the old clip by half a cycle
to show the same leading leg, uses common model cameras/materials, and preserves one native image scale/offset
throughout. The angles are authored interpretations of source silhouettes, not extracted native 3D data.

Source and reimported GLB checks cover 49 body samples and 97 foot samples. Planted sole clearance stays 1.4–3.1 mm;
loop closure remains below 0.001 mm. Shoulder attachment changes by at most 0.83 mm per 48 fps sample relative to
its shoulder. Hand/grip/neutral-neck checks pass across 35 action samples; the 21-pose reimport error remains about
0.004 mm. Binary checks confirm the other six clips, in-place root, repaired maps, materials, geometry, UVs, weights
and bind transforms are unchanged. The model remains **12,916 triangles and 72 joints**.

Preserved the preceding Blender file in `checkpoints/before_body_motion_correction.blend`; the previous textured
GLB, scripts and receipts are in `review/body_motion_correction/before/`. Updated the existing textured deliveries
and rendered four complete walk views from the actual reimported GLB.
[Whole-body comparison](review/body_motion_correction/index.html), with B/E shortcuts, front/side views and frame stepping.

## Eye visibility (screenshot 2120)

The eye meshes were present, but the prior dark olive sclera and small iris/pupil features blended into the
sockets at full-body scale. The earlier close-up check had missed this readability problem. Compared the supplied
screenshot with the selected front/head design references and tested both close and full-figure renders.

Brightened the three existing eye materials and enlarged the iris/pupil radii by 1.5×/1.55×. Fitted their existing
triangle fans to the curved underlying surfaces and measured interior clearance to prevent globe intersections.
The two eye-part vertex positions change; topology, UVs, weights and all other surfaces are retained. No added
triangles, new atlas maps or emission. The repaired Meshy atlas remains byte-identical.

Re-exported the textured Blender and GLB deliveries. Binary checks confirm all seven animation channels match
the body-motion revision exactly, all non-eye materials match, and the total remains **12,916 triangles**.
The 21-pose reimport check passes. Rendered the actual exported model in front and oblique close-ups, at full-body
scale, through the 24-frame front walk and at four close-up walk phases. Preserved the prior Blender project in
`checkpoints/before_eye_readability.blend`, with the previous GLB/scripts/receipts under `review/eye_readability/before/`.
See the [before/after eye review](review/eye_readability/index.html). Blender opens on the corrected face.

## Complete animation gallery

The user requested one HTML review containing every action and direction of the current model. The eye review
contained only the latest front walk; the previous complete action previews used the earlier modeling materials.

Rendered the actual current textured GLB (`eye_readability_6`) in seven actions from eight independently rendered
directions: **56 MP4s and 1,264 PNG frames**, 960 × 960. The camera stays fixed within each clip. All upright actions
share a scale; death and corpse use wider, higher views. Evaluated mesh bounds retain at least 4% frame margin
for every rendered pose/view, including the full sword swing and fall. Death includes its exact final pose and
a short hold; corpse is an explicitly labeled static pose. MP4s total approximately 8.25 MB.

The [complete gallery](review/complete_gallery/index.html) provides action/direction selection, slow playback,
exact PNG frame stepping, fullscreen, synchronized eight-view playback and all individual video downloads.
The main `review.html` now opens this page. Preserved the previous modeling page as `review_modeling.html` and
linked the complete gallery from the delivery notes, manifest and eye review.

All 56 encoded clips pass dimensions, codec, rate, frame-count and duration checks. Browser checks pass for every
clip, controls, synchronized views, narrow layout and direct-file use, without console exceptions or failed HTTP
requests. The latest GLB also passes the 21-pose reimport check. All six delivery-file hashes are unchanged;
geometry, materials and animation remain exactly as delivered at **12,916 triangles and 72 joints**.

## Attack arms (screenshot 2128)

The opening attack used the generic standing pose: the right elbow flared sideways and the sword pointed at
the camera. Preparation lacked the original's right upper arm across the chest and left hand beneath the grip.
During the cut, the free hand failed to sweep across the abdomen. The prior independent blade-edge alignment
also forced excessive wrist bending at intermediate poses.

Audited the six exact native attack images and restored reference, plus standing side/back views. The native
descriptor marks all attack frames `Image1`; the files contain only `gobat[a-f]0`, with no side/back attack
images. Documented that limitation explicitly instead of treating reconstructed camera views as original data.

Rebuilt only `attack` around native A–F and its 0.75-second timing. Added an attack-specific compact guard,
raised the right upper arm across the chest, cupped the left hand beneath the grip, and opened/swept it across
the abdomen during the cut. Solved the right elbow with the hand orientation, using normalized quaternion
knots to retain a plausible wrist. Kept the head lift/turn and preparatory step. The shared pose helpers and
six other actions are unchanged.

Checked 145 baked samples at 192 Hz: maximum wrist bend 45.09° right / 34.10° left, unit bone scales within
0.000001, loop error below 0.001 mm. Cutting-edge travel stays positive through the sampled downstroke;
this is a directional check, not perfect edge alignment or a full collision audit. Hand checks pass in 35
poses. The reimported GLB matches all joints and skin/sword across 21 poses within approximately 0.004 mm.
Binary checks prove only attack changed; all geometry, packed images, materials, UVs, weights and skin bind
transforms match the prior delivery. **12,916 triangles, 72 joints**.

Updated the textured Blender project and rigged GLB to `attack_arm_7`. Rendered 144 new attack frames from
the actual reimported GLB in the same eight cameras as before; at least 3.1% conservative framing margin.
Replaced eight active gallery videos, retaining the other 48 byte-for-byte after proving identical source
content. Added the [synchronized original / before / revised comparison](review/attack_arm_correction/index.html)
with A–F shortcuts, slow playback and all eight model directions. Browser validation passes 72 full-gallery
checks and 20 comparison checks, including mobile and direct-file use, without exceptions or failed requests.

Preserved the old source at `checkpoints/before_attack_arm_correction.blend`; previous GLB, scripts, receipts,
videos and frames are under `review/attack_arm_correction/before/`. Cleaned the owned validation scene and
saved Blender on attack preparation pose C. No engine installation or change to the four historical modeling
handoff files. [Detailed findings and receipts](review/attack_arm_correction/README.md).

## Attack elbow deformation (frames 8, 9, 10 and 17)

The previous wrist/grip checks missed incorrect elbow bending. Independent aiming of upper arm and forearm
allowed sideways deviation from the anatomical bend plane (up to 79° right / 56° left) and backward flexion on
the right. Joint centers remained connected, so endpoint continuity alone did not expose the skin deformation.

Added a hinged limb solve, used only by the attack arms. The upper arm rotates its rest bend plane into the
target plane and the forearm flexes about that same axis. Also removed hand-driven right elbow placement,
which kicked the elbow upward during the cut and folded it during recovery. Added a forward wrist arc and a
lower/outward elbow path; limited right wrist bend to 35°. Retained the raised native preparation, head turn,
left-hand trajectory, step and 0.75-second duration.

Inspected the four reported frames and transitions from eight directions using the actual reimported GLB.
145 source/exported samples at 192 Hz retain positive elbow flexion and less than 0.0003° off-plane error in
the export. Hand/grip checks and the 21-pose reimport pass. Binary comparison proves only attack changed:
geometry, UVs, weights, skeleton binding, materials, packed maps and the six other clips are identical.
The budget remains **12,916 triangles and 72 joints**.

Updated the textured `.blend`/GLB to `attack_elbow_8`, rendered 144 replacement attack frames and eight MP4s,
and retained the other 48 videos byte-for-byte. The existing comparison now defaults to the reported attack
as “Before” and includes frame 8/9/10/17 shortcuts plus a selector for the original screenshot-2128 baseline.
Browser checks pass: 72 full-gallery and 26 comparison checks. Preserved revision 7 in
`checkpoints/before_attack_elbow_correction.blend` and `review/attack_elbow_correction/before/`.
[Correction notes and receipts](review/attack_elbow_correction/README.md).

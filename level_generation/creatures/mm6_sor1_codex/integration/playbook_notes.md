# Proposed playbook notes — no shared playbook edited

- A closed robe needs a complete under-robe leg silhouette. Generating a robe with isolated shoes left floating
  boots in the fall; add fitted trousers and include their actual closed surfaces in contact checks.
- Separate native staff height from body calibration. sor1 body height is 257 pixels at native scale 0.699997,
  or 179.899 game units; the red staff crown starts higher than the head.
- A full-body reference without equipment is useful for hands, but batch prop production still needs its own
  native-derived HD design. This staff now has a retained design sheet, a 2,888-triangle original model,
  curved crown fingers, a grooved grip and a detailed 1K atlas.
- A cloak simulation cannot be treated as a closed robe without refitting its envelope. For this backward fall,
  a smooth fitted leg drape plus actual surface corrections replaced unstable free-cloth rotations.
- Check subframes on the actual triangulated GLB. Keys that cleared the shoes in Blender still crossed them
  between samples; final export is sampled at 120 Hz and checked at 240 Hz.
- Enforce eight influences before export; Blender can write eleven when export_all_influences is enabled.
  Verify surface parity after reimport, not just bone counts.
- Blender's glTF importer can create an Icosphere custom bone-shape object. Select the named actor mesh,
  not the first mesh in bpy.data.objects, for audits and renders.
- Compute release from the actual casting implement: Attack uses the staff head at 1.220833 s; Cast
  uses the staff head at 0.7375 s. Test the actual crown tip while aimed at the target; the staff
  blow/launch gate applies even though a cutting blade-edge gate does not.
- Reset poses when switching actions. Unkeyed helper locations can otherwise carry over from the previous clip.
- Technical gates and batch completion do not imply artistic acceptance or real-engine validation.

## Review round 1 lessons

- Select a staff cast by rendered weapon motion. The useful 2H Mixamo clip needed one-hand grip adaptation,
  20% body motion and discrete foot IK; the one-hand candidate flung the staff sideways and kicked airborne.
- Bell sleeves need shaft/forearm clearance throughout the cast. Solve staff orientation and the actual
  right-hand grip together; a plausible elbow target alone can drive the shaft through the cuff.
- Retarget free-arm return poses as well as Standing. A forward elbow bend leaves the hand beside the thigh
  without an outward elbow silhouette; test the sleeve against the robe at half-key frames.
- Hit and Fidget must move the prop, knees and weighted hem. A fast blend to an old face-covering hit pose
  introduced excess hand speed; a softer full-body reflex passed the source-relative speed check.
- Purple neck bleed here was overlapping textured head geometry, not the body atlas. Inspect isolated
  head/body layers before repainting a good collar; tuck the redundant lower head apron under the collar.
- Add staff/floor clearance to every clip's audit. The original Walking staff dipped 5.2 mm below floor;
  the revised grip/lift clears both the swinging hem and floor by at least 12.1 mm.

## Review round 2 lessons

- Measure signed elbow flexion about a fixed anatomical rest hinge, transformed by the upper arm. An unsigned
  shoulder/elbow/wrist angle cannot distinguish normal flexion from a reversed elbow. Independently test both
  arms at 48 Hz, including Death and held Dead; use a negative-flexion regression example.
- Unwrap forearm and helper twists over time. Blend the gathering hand from a fixed corrected Standing world
  orientation; blending from a moving neutral forearm frame introduced wrist flips during recovery.
- Fit actual shaft/crown vertices against the deformed sleeve, not only a staff centreline. Include sleeve
  edge stretch in pose selection. The sparse LBS predictor is checked against Blender's evaluated vertices.
- For a second grip, solve a fixed hand-local grip frame onto the dominant hand's shaft. This thrust holds a
  26 cm spacing; the actual reimported off-hand centre stays within 1.78 mm during the support interval.
- A viewer that reads only JOINTS_0/WEIGHTS_0 misrepresents an eight-influence asset. This project's three.js
  shader includes the second set, restores the loader-normalized primary weights and asserts total weight sums.
  Shared viewers were not edited; consider the same correction centrally during integration.
- Test each lower LOD on every animation. Uniform 98/94/90 percent decimation passed standing renders but
  produced 35–39 mm robe/leg penetration during Death. Preserve articulated robe/body/hand vertices and weights;
  reduce head and prop detail only when both the screen-distance image checks and animation gates pass.
- Check the whole boot sole, not only its joint. The old folded swing foot cleared the floor by 18 cm with a
  92-degree knee. A flatter foot orientation retains the source gait with 10.6–10.9 cm clearance and ~64-degree knee.
- Keep user-requested palette preservation explicit when native skin highlight statistics differ. The round-two
  skin diagnostic is an art-review note; do not label it a passed native-ramp rematch.

## Review round 3 lessons

- A fixed off-hand position is insufficient: use a fixed hand-local grip frame, opposing palm normals and one
  continuous roll choice through the held phase. Approach radially, close after contact, open before withdrawal.
- Smooth elbow pole angles across time before solving; independent per-frame angle searches created arm jitter.
  Gate world angular acceleration for both upper arms, forearms and wrists at 48 Hz, with an alternating-error self-test.
- Finger motion needs source-relative speed coverage too. A short closed-fist release introduced fast distal motion
  although the wrists passed; 0.2-second closure/opening now passes all source traces.
- Inspect actual full extension, not only five evenly spaced poses. Add a numeric forward-travel and elbow-opening
  check; this Attack drives 420 mm and opens the leading elbow by 31.8 degrees.
- Recheck actual sole vertices after pelvis translation. Lowering another 33 mm preserved the rear plant; 40 mm
  crossed the robe/leg contact gate.
- On open/cut garment surfaces, inward nearest-normal distance alone reports false penetrations. Require
  containment in each closed garment piece as well; cap cut loops only for classification, never distance.
- Rebuild sparse lower trousers as fitted knee-ring tubes and preserve cloth trajectories. Do not erase trousers
  as hidden when the Death/Dead clips expose them.
- Rebake colour/masks/ORM/normals after protected reduction. Preserve per-LOD texture ownership when splitting
  attachments: the shared splitter selects LOD0's material, so this project's poststep restores lower rebakes.
- Pooled actor IoU and SSIM can pass while a tight collar close-up shows triangular bake marks. Record those
  visible art limits separately; numeric completion is not artistic acceptance.


## Review round 4 — texture-only repair

Per-LOD rebakes must not accumulate unused images or fragment cloth UVs into many poorly padded islands.
This repair shares four 2080×1024 maps across body/head LODs, three 1K maps across staff LODs, and pads masks
identically to colour/normal/ORM. Source-chart interior filtering avoids copying pre-existing atlas-border flecks.
Review at texel scale and explicit 4× downsampling; inspect exported browser close-ups too. Exact per-triangle
skin/position and animation-byte preservation allows a texture-only revision to use shared static gates without
rerunning unrelated motion gates. Current reports and visual evidence are under review/round4/.

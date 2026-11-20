# Lizard batch lessons (shared playbooks left unchanged)

## Round 5 — current

- Match supporting weights as well as separating worn layers; offsets alone cannot prevent contact through a fold.
- Keep the tabard below its belt during the fall; check exact reduced meshes too.
- Declare real hem openings. A non-planar artificial cap can misclassify a buckle below the garment.
- Retiming exposes acceleration/finger steps; ease affected intervals while retaining duration, endpoint and release.
- Attack/Cast release is 0.489583333333 s, duration 1.133333333 s; Death 2 s; Dead unchanged.


## Round 4 — historical, superseded above

- The native frame overrides generic carry advice: square shoulders/pelvis, horizontal hip bow, string above.
- RelaxIdle, UnarmedGetHitF1 and UnarmedRunForward provide upright idle, backward recoil and normal running.
- Shooting Arrow supplies the bow shot; fit elbow planes and cheek anchor, spread forearm roll, keep the string on the archer side. Cast copies Attack exactly.
- Extend the lower body beneath the tunic and blend the hem toward the pelvis; inspect the exported waist from below during the draw.
- All LODs share the rebaked near maps at accepted resolution with 16 px dilation. Shared runtime gates certify all colour/shadow meshes.
- Recheck the final reduced meshes: local bracer/quiver contact and far silhouettes can fail despite a clean near model. Keep rejected reduction trials distinct from the selected receipt.
- Current release is 0.734375 s; the arrow hides then, string relaxation ends at 0.751042 s; Attack/Cast duration is 1.7 s.

## Historical rounds 1–3 — superseded where above differs

1. Fit the non-human silhouette before auto-rigging: the first topology return had a long tail and pointed face.
   Preserve its useful body topology, shorten the tail to the native forearm-length profile, and graft a separately
   reviewed broad head before the one paid rig job. Recheck the neck, shoulder and collar at draw and fall extremes.
2. Meshy's joint guide was biased toward the quiver. Recenter spine/shoulders from body anatomy, fit elbow/wrist
   rings and ankle hinges, and use the owned animation skeleton's original rest frames. The rig transfer matched
   rest positions exactly; three fingers plus thumb follow actual mesh components, not all five source chains.
3. Bracers and shin hardware must follow the correct rigid side. Part IDs 25/26 and 55/57 looked symmetric but were
   opposite the initial guess. Global nearest-bone weights left floating straps; anatomical ownership fixed them.
4. A bow collision gate needs the actual curved limbs, visible arrow and both moving string segments at subframes.
   Checking only the bone or a straight stand-in missed string/forearm crossings. Sample all clips, not only Attack.
5. Unwrap forearm/upper-arm roll before multiplying by a fractional twist factor. Quaternion sign cleanup alone
   cannot remove the 180-degree half-roll snap caused by splitting a wrapped angle. Reimported GLB trace caught it.
6. Freeze or smoothly blend fitted claw articulations; source finger world rotations on different anatomy caused
   needless fast finger motion during death. Check every weighted hand edge and exported textured close-ups.
7. RelaxRunForward keeps this reptile's trunk upright; BowWalk arms preserve its carried bow. A lowered free hand
   needs enough clearance from the thigh and an additional forearm lift in locomotion to clear the moving knees.
8. The source GetHit shrug drove the broad reptilian head into the shoulder. A native-informed planted recoil with
   torso/arm/bow motion and knee flex keeps the required full-body response without the shrug.
9. Measure the release on the equipped export: the string begins its snap at 0.733333 s, reaches sampled peak total speed
   at 0.734375 s and is fully relaxed at 0.766667 s. The projectile event belongs at the velocity peak, where the
   arrow's target dot is 0.9963, rather than the fully relaxed frame where the bow is already rolling down.
10. Arrow/string require an animated material primitive alongside the merged body/head. Temporarily parking that
    primitive as another mesh lets the existing two-material atlas helper work without changing shared tools.
    Final body + rigid bow geometry and skin/animation bytes are independently checked against the gated export.

11. A ranged descriptor can still have a table spell. Validate `animation.cast` against both attack clip names before
    handoff, and use a distinct clip name for spellcasters. A user-approved bow-spell route can copy Attack exactly and use its arrow socket; LizardArch C requires a distinct Cast name.
12. Unsigned elbow flexion and edge stretch did not expose off-plane bending from a global-axis forearm correction.
    Audit signed flexion against the upper-arm hinge axis, plane deviation and the applied twist helper at 48 Hz.
    Align upper/forearm frames to the joint plane while preserving hand targets, then repeat deformation/contact gates.

13. A frame-baked bow string can separate or cross the arm between endpoints. Use a shared nock, stable minimal-roll segment frames and fractional keys for draw/release. Preserve the union of rotation, translation and scale key times; an optimized constant translation sampler alone loses the changing rotation/scale keys.
14. Sample equipment at exact 48 Hz plus the endpoint. A duration-dependent linspace can miss a narrow mid-frame collision. Check string junction error more densely.
15. Validate exact lower runtime meshes, not only Blender candidates. Import the named mesh node, because Blender also creates a mesh for bone display. Retain authored/exported counts and recheck silhouette and all clips after export.


Round 3 final export audit: lower-LOD wrap radius needed a 3%/8% contact fit, tapered out above 11 cm. Recheck actual GLB topology: the exporter omitted 7/21/30 lower-body faces. A nearest shoulder face plane alone produced a false 44.3 mm head contact at far LOD; requiring the tested point to lie inside the struck component bounds eliminated this false hit without relaxing the 10 mm limit. See review/rebake/head_plane_audit.json.

This round was already running when the shared gate runner and single-texture-set requirements arrived. Cost controls item 4 says new rules are not retroactive, so this handoff retains its project gate suite and per-LOD maps; it does not claim those newer migrations.

## Round 6 — Walking

Per-frame pelvis reach/floor clamps produced a 3.187 m/s vertical spike. Fit one periodic height curve to both leg-reach envelopes, then solve knees against the existing feet. Shoulder swing preserves the accepted hand pose, with a small free-wrist adjustment toward the thigh. The shared gate runner covers arm angular jitter, but lacks pelvis/spine/head translation-jitter coverage; diagnostics use its runtime sampler.

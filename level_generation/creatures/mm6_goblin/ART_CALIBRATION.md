# MM6 goblin: source and reconstruction findings

## Native audit — 2026-09-08

The 59 actual goblin frames were traced from the shared sprite table and converted losslessly to RGBA using palette
index zero as transparent. All use a 355×289 canvas and cyan key (0,252,252). The nearby `goblet.bmp` and its unrelated
sprite-table row are excluded. See `source_manifest.json`, `audit_source.py` and `source_audit/` for hashes, descriptors,
frame bounds, contact sheets and playback. The original sheets have no visible margin below the standing feet.

Observed design:

- Lean muscular biped with narrow waist, elongated forearms, long clawed fingers and long forward-projecting clawed feet.
- Compact angular head, heavy low brow, yellow eyes, short broad nose, projecting jaw and pointed irregular teeth.
  Ears rise beside the temples and project backward in profile; the back of the head has a tapered projecting form.
  Small gold ear rings are visible. Do not infer a smooth human skull from the front alone.
- Small dark riveted chest gorget, spiked shoulder caps, separate forearm bracers and shin guards. The belly, thighs
  and most of the back are exposed. Two small riveted plates sit high on the back; there is no full back cuirass.
- Brown belt with pouch at the sword-hand side and an overlapping skirt of separate leather strips ending over the
  upper thighs. Armor straps are visible around ankles and the backs of limbs.
- RIGHT-hand long curved single-edge sword with gold guard. Its full length is revealed by profile and attack views.
  The short frontal silhouette is foreshortening, not a short cleaver. Free hand hangs with curved clawed digits.

Observed actions:

- Walk: alternating forward contacts, substantial opposing arm motion, dipping head/body, sword swings with right arm.
- Attack: draws sword across front, lifts diagonally toward image right with torso turned, then slashes across/down,
  extends sword toward image left and recovers. Free hand counterbalances. Do not substitute an overhead club swing.
- Hit: recoils while lifting the free LEFT forearm across the face; right hand keeps sword to its side; returns to stance.
- Death: bows, knees fold, free hand reaches toward ground, then body falls prone/sideways with spread limbs and sword
  alongside. Corpse holds that final ground pose. A kneeling corpse would contradict the source.
- Fidget: restrained changes around the standing posture. New idle breathing must also remain restrained.

## Restored turnaround v1

The preflight front test captured useful surface character but turned the foreshortened weapon into a short cleaver.
The new turnaround uses all five native views and restores sword length, leaner build and separate upper-back plates.
It is selected as the principal surface/construction guide, with these explicit native-overrides:

- Its frontal sword is held across the figure instead of pointing forward as in native standing. Use native standing
  wrist/weapon direction for the 3D resting pose; use the restored profile to measure actual blade length.
- The restored back resolves ambiguous central bright/dark native markings into a distinct studded spine strap.
  Those pixels could instead describe spinal highlights. Use a conservative exposed-back interpretation; do not claim
  the extra strap is established native costume.
- Neck/muscle grooves and leather wear are interpreted detail. Keep anatomy coherent in actual 3D, not over-carved
  simply to reproduce painted shadows. Jewelry count and precise fingernail shapes remain inferred details.

The right-hand weapon makes this model asymmetric. Deliver eight genuine rendered directions; do not mirror it onto
the opposite hand just because the old sprites used three mirrored octants. Native action views absent from the
source will be supplied by the reconstructed rig, with uncertainty recorded rather than invented source claims.

## Sprite anchoring and timing

The native frame flags omit `Center`. OpenYAMM's `spriteFrameBillboardCenter` in `game/indoor/IndoorRenderer.cpp`
uses the bottom-anchored path in this case. Canvas center is therefore not a ground pivot. Keep the generation pivot
explicit and account for any transparent bottom margin when documenting future placement; do not add `Center` blindly.
Standing front visible bounds are (118,33)–(254,289) on the 355×289 canvas. These bounds describe this source render,
not an instruction to resize each animation image independently.

Use full-quality continuous timing for the dense sheets and a separately documented sample selection for legacy
integer timing. Six native moving frames at raw length 2 give 0.75 seconds; five death frames give 0.625 seconds.
Sixteen distinct legacy attack frames cannot fit 12 raw units without changing duration. Do not conceal that mismatch.

## Head sculpt v1 review

Rejected as a finished shape. Unioning facial ellipsoids made the brow and cheek masses look pasted on, even though
the mesh was connected. Eyes were too exposed and the broad tooth gap too even. Ear interiors were flat sheets,
the rear skull projection had an obvious attachment-like transition, and excessive rim lighting washed out the crown.
Reference-color projection alone could not fix the geometry. The first source script/library are preserved under
`revisions/head_v1/`, and four renders remain under `review/head_v1_*.png`.

Revision 2 replaces the facial masses with one sampled anatomical envelope, including brow, socket, cheek, nose,
lip and chin relief in its actual surface. It recesses/sizes down eyes, closes the mouth gap and reduces teeth and
rim light. It still needs fresh visual review; ear construction is an acknowledged remaining refinement.

## Head revisions 2–3: current unresolved work

Revision 2's per-section smoothstep interpolation made visible horizontal shelves around the cranium. Revision 3
uses Hermite interpolation with neighboring-section slopes, which removed those shelves and improved the continuous
profile. Darker nonprojected skin now fits the reference color better. Eye exposure is reduced and ear pinnae are
concave, but the new separate eyelid tubes still look attached, the teeth read as rounded beads, and subdivision
shrunk the ear interior away from its outer rim at the tips. These are **not accepted finished details**.

Next sculpt correction: integrate eyelid surfaces into the face with actual surrounding skin rather than exposed
tubes; make small irregular tooth crowns with two restrained lower canines; preserve pinna boundary attachment while
refining inner curvature. Recheck the short broad nose and projecting lower jaw against `head_v1.png`. The current
script is revision 3, its library is `sculpt/head_sculpt_library.blend`, and the live current scene is
`MM6 Goblin head sculpt`; previous scenes have revision/rejected names and are preserved.

Optional Blender Hunyuan3D and Hyper3D status checks both reported disabled. No settings were changed and no external
3D-generation job was started. Continue the original Blender sculpt workflow; these optional services are not blockers.

## Head revision 4 and full-body construction

The fourth pass removes separate eyelid tubes and adds the lid relief to the continuous facial envelope. The eyes
now use the reviewed iris/sclera pigment on actual eyeball geometry rather than simple flat yellow disks. Tooth
crowns have tapered sides and smaller staggered lower teeth, with two longer lower canines. Pinna subdivision now
preserves its boundary, closing the gaps at the rim. The resulting front and oblique renders show improvement over
revision 3; retain this as the working head for full-body review, not a claim of final overall quality.

`build_body.py` establishes connected torso/limb/hand/foot skin, separate costume pieces and a rigid scimitar. Named
attachment groups on armor/props will feed the rig. Torso material projection is limited to the exposed torso so
restored armor pixels are not painted onto unrelated limbs. The native resting sword points forward; it will look
short in the front view and long in profile. The first complete figure still needs proportions, contact and material
coherence reviewed before rig/animation packaging.

## Full-body revision 1 review

The first figure exposed a long neck, excessively hemispherical shoulder caps, smooth bulky toe masses, a round
pouch and back plates intersecting the skin. The full torso reference projection also painted a second belt above
the modeled belt because its anatomy/costume alignment was imperfect. This image is rejected as a finished character.

Revision 2 shortens the visible neck by lowering the working head 0.055 units, flattens shoulder caps, moves back
plates outside the torso, gives feet slimmer separate toes, reduces palm bulk and replaces the pouch with a beveled
container and flap. The blade outline is smoother and its resting aim turns 18 degrees inward to make the native
foreshortened frontal blade visible. Review cameras now orbit toward negative X for the native right-side profile.

Whole-torso color projection was replaced by an AI-generated flat olive skin swatch. The body supplies anatomical
relief; stored `SculptPosition` vertex attributes provide consistent material scale without texture sliding during
later deformation. This also avoids the stretched grain caused by normalized bounding-box coordinates on a tall
body. The skin source and exact image-generation prompt are saved locally. Metal and leather base colors were darkened;
further material/detail review remains required after the new renders.

## Full-body revision 3 and first rig

The third body revision replaces the ball-like foot volume with an arch leading into the toes, restores continuous
upper-arm relief instead of protruding biceps ellipsoids, and slopes the shoulder caps outward. The generated brown
leather swatch is applied using stored rest-position attributes. Torso reference color is now limited to the exposed
abdomen with corrected vertical alignment and partial blending; the belt and armor cannot be sampled by that mask.
This is a stylized reference-color treatment, not a claim that the restored portrait is neutral scanned albedo.

The figure is sufficiently complete to test deformation, but armor surface detail, hand/foot anatomy, neutral stance
and overall material balance still need scrutiny. A valid mesh/rig is not final visual acceptance. The next phase
uses `rig_character.py` to create named biped/digit/weapon controls and four-influence skin weights, then renders
neutral, raised-sword and step probes. Those probes are diagnostic poses, not final animation clips or gait proof.

## Full-body revision 4 and rig revisions 2–3

The equal-height `review/body_v3_reference_comparison.png` makes the unfinished areas clear: head and feet too small,
shallow shoulder disks, tube-like guards, regular unbroken skirt and a stiff neutral posture. Revision 4 enlarges the
head around the chin (X 1.16, Y 1.10, Z 1.15), widens/lengthens the feet with dorsal tendons, deepens/slopes shoulder
coverage and gives guards pointed top outlines, rolled edges and more rivets. The ankle plates are separate pieces.
Twenty-two narrower irregular leather strips replace the nearly continuous skirt. Skin and leather pigments are
darkened. Four views are saved as `review/body_v4_*.png`. The shape is improved, but surface finish remains under review;
cloud-like metal noise alone does not establish convincing forged wear. Profile review also needs foot underside and
neck/head join scrutiny. No final artistic acceptance is claimed.

Rig revision 1 accidentally gave hip vertices arm influence because the resting hand is nearby. Revision 2 restricts
candidate influences by anatomical region; `rig/hip_weight_regression.json` records 7,629 tested hip vertices with
zero displacement when the sword arm is raised. Skinning uses ordinary linear deformation for GLB parity. Revision 3
adds independent leather-strip bones and attachments, giving 88 bones in total. Joint probes precede final animation;
weight normalization alone does not prove good deformation.

`animate_character.py` uses explicit foot targets and analytic two-segment limbs, then writes ordinary FK bone keys.
The walk's half-cycle stance travels backward relative to an actor advancing at the documented stride/speed. Attack
targets follow the native cross-body draw, diagonal lift and slash. Hit raises the free left forearm; death bends,
reaches and collapses toward the source's prone pose. First-pass poses and actual playback still require visual review.

## Motion revisions 1–6

The first generated action pass tipped the body onto its back. The root bone's rest matrix aligns bone-local Y with
world Z; replacing it with identity was an actual orientation error. Revision 2 preserves that rest matrix. Its
pose renders establish recognizable diagonal attack, cross-body slash, left-arm shielding hit and a bending fall.
The first full perspective playback is retained in `review/motion_playback_v2/` as rejected/intermediate evidence.

Revision 3 uses each leather strip's hinge to clear the posed thigh capsules and floor, baking the result into its
ordinary bone keys. This fixes the exposed-thigh holes through the skirt. The free hand turns flat on the ground and
the sword wrist is lifted enough for the knuckle guard. Revision 4 redirects the folding knees outward and raises
resting ankles so shin armor no longer passes deeply through the floor. Full playback and contact sheets are saved
in `review/motion_playback_v4/`; `animations/motion_v4_review.json` records the measured bounds and loop/contact checks.

The walk uses a 0.64 m full-cycle stride over 0.75 s, intended forward speed 0.853333 m/s. At the checked subframes,
world-space planted-foot drift was approximately 0.2 mm. Standing/Fidget loop matrix differences were effectively
zero; Walk's maximum matrix difference was about 7.5e-9. These are focused motion measurements, not final mesh/art
acceptance. The early review floor accidentally rendered white; revision 4 explicitly assigns a node material to
make ground contact visible in neutral gray.

Despite clearing most floor intersections, the fourth corpse still arched its chest high above ground. Revision 5
unfolds the spine into a flat prone body during the final fall; the corresponding `motion_v5_corpse_1.00.png` shows the
head and chest settling. The remaining 9 mm penetration midway through Death came from interpolation of solved FK
leg rotations between keys, not the target ankle position. Revision 6 uses four subframe key intervals per display
frame for Death. Preserve those keys when exporting; blindly resampling to one FK key per frame can reintroduce the
contact error. Recheck the actual exported interpolation before claiming parity.

Revision-6 evaluated bounds were checked at 121 Death times, including halfway between the denser keys. Minimum Z
was +0.0011839 m; Corpse has the same minimum. Death endpoint and Corpse start bone matrices match exactly. Evidence
is `animations/motion_v6_ground.json`. This resolves the observed floor penetration in the working Blender motion;
it does not replace the later GLB interpolation and appearance review.

The current checkpoint contains seven draft actions; this is substantial animation progress, not completed final
motion or art. Remaining reviews include shoulder/armpit deformation, hand/weapon grip close-ups, rear/side playback,
more convincing metal/leather wear and coherent skin detail on limbs versus face. Current plain/noisy surfaces still
look too much like a constructed prototype beside the restored design. Finish those causes before baking/exporting
the accepted model or rendering final sprites.

The revision-6 perspective collapse contact sheet was inspected after rendering. The body now falls and lies on the
floor with its hand outstretched, but the back/side skirt strips still fan too stiffly above the hips. Their hinge
solver currently clears collision without accounting sufficiently for gravity in the prone pose. Add settling toward
supporting surfaces and review side/rear close-ups; do not call collision clearance alone finished clothing motion.


## Surface 2, detail 2 and motion 8

Generated worn iron replaces broad cloudy noise with small pits and abrasions. Front/side/rear and close views
revealed that material work alone could not fix the wrist cuff step or stair-like armpit shading. Rebuilding the
palm as a continuous loft into the wrist, adding a heel pad and smoothly gating shoulder skin influences corrected
those geometric/deformation causes. Upper and lower tooth crowns now taper to points while retaining one tooth material.

Matched-camera hand, torso and foot restorations were generated from the actual model close-ups plus the selected
turnaround. Their RGB detail is projected only onto skin, with explicit geometry/facing masks and a conservative
skin-color confidence mask. Armor, claws, equipment and background pixels are excluded. The hand projection was
checked from its source camera and a side camera; torso/feet close-ups plus full oblique/back were also inspected.
The surfaces now carry wrinkles/tendons/pigment detail consistent with the face. The generated inputs remain
interpretations, not recovered original textures. Neck/head joins and motion still need scrutiny in final parity views.

Surface mask generation originally recalculated Blender normals inside a corner loop after UV/color writes, making
it unnecessarily slow. Cache evaluated positions and normals before writing attributes, then use bulk array writes.
This changes preparation cost without reducing the visible model or skipping inspection.

Motion 7 adds gravity bias to the rigid leather-strip hinge solve during the collapse. Motion 8 applies the complete
clip set to the current detailed body and animates the free hand's fingers during Walk, Hit, Death and Corpse.
The right grip stays attached to the sword. The hit/attack/prone previews were inspected; rerun contact and loop checks
because the wrist/heel geometry, shoulder weights and fingers changed after the older positive-ground report.

For baking, export base color through a temporary emission output. A diffuse-lighting bake is not a reliable way to
preserve a metal's base pigment. Restore original shader connections after each channel bake. Export appearance and
normal-map seams still need actual visual comparison; prepared bake scripts are not proof of portable material parity.


## Continuous neck and portable mesh/material preparation

The rear neck close-up exposed a separate head cap sitting on the neck. A localized Boolean union plus smoothing
behind the jaw creates continuous geometry, with neck/head weights blended through the transition. The first union
stretched procedural head pigment because generated coordinates changed; merely copying POINT attributes through
the Boolean was also unreliable for its operand. Revision 3 reconstructs each material's original normalized
coordinates from explicit common rest positions, retains corner projection coordinates, and blends one shared olive
pigment across the rear neck. Front, rear neck, attack and prone views were inspected; the facial relief remains intact.

The joined mesh hit Blender's eight-UV-layer limit. Source projection UVs are stored as named corner vector attributes
for baking, leaving one actual GameUV layout for portable textures. Decimation initially degraded face pigment into
patches: protect the face during reduction rather than accepting this as a texture-resolution limit. The protected
version retains all 14,553 vertices above the jaw while reducing the complete actor from 287,594 to 206,722 triangles.
It has 14 material regions and an 88-bone rig. Matching source/reduced/baked face, hands, feet and full views were reviewed.

Reduction interpolated some skin weights into more than four influences. The final preparation explicitly keeps and
normalizes four for 1,288 affected vertices (maximum discarded weight 0.1094), then checks the evaluated result. Freeze
triangulation before baking tangent normals so exporters can calculate tangents consistently. Bake color by emission,
normal/roughness as dedicated channels, metallic by emission, then pack ORM. The three shared 4096² portable textures
retain the source appearance with some fine-detail softening; categorical region masks are retained separately.

Motion 8's finger spread twisted the resting hand and pushed claws through the floor. Motion 9 constrains the palm
normal and its long axis, spreading digits in the palm plane. Dense sampling then caught a 4 mm toe penetration just
after walking toe-off that the earlier nine-phase check missed. Motion 10 starts swing lift earlier without changing
stride, duration or stance contacts. Updated source and reduced-mesh checks pass weights, loops, 121 Walk/Death samples
and exact Death/Corpse endpoint agreement. These checks alone do not establish final artistic quality or GLB parity.

Blender FULL_COPY can duplicate the active Action, and assigning an Action after a rig copy/rename can leave its
Action Slot unset. This caused Standing to be omitted from the first GLB attempt. Assign the single-armature Action
Slot explicitly in authoring/review/export helpers, canonicalize the active clip before checkpoint writes, and verify
all seven exported clips. Shift GLB animation starts to zero; retaining Blender's frame-1 time adds an unwanted 1/24 s
lead-in for consumers that treat maximum timestamp as clip duration. Keep fractional Death keys, not a 24-fps resample.


## Final export and sprite review

The last reduced torso comparison exposed small triangular pigment patches. Preserving source projection coordinates
as generic corner vectors alone did not retain the interpolation through Decimate. Temporarily restoring them as
true UV layers during reduction, then freezing the result back into attributes, removed the observed patches. The
refreshed bake and actual exported GLB were reviewed in identical studio views, including face, rear neck, torso,
hands, feet, oblique, attack and corpse. The final delivery uses this corrected UV preparation, neck 3 and motion 10.

The actual GLB was imported into an isolated studio and reopened for seven-clip perspective playback. Disable the
importer's optional bone widgets: its hidden unit icosphere was diagnostic geometry, not part of the character, and
otherwise contaminated whole-scene floor measurements. Walk/Death were evaluated at 121 times each; all checked
geometry stayed above the ground (lowest imported Death sample +3.66 mm). Loop and Death/Corpse poses match within
floating-point precision. This is specific evidence from the Blender glTF consumer, not an OpenYAMM runtime test.

The final native/restored/model comparison uses the same visible figure height within each row, retaining each
image's aspect ratio. Front, oblique, profile and rear preserve the lean exposed body, separate armor, tapered head
projection and right-hand scimitar. The AI turnaround's neighboring weapon can overlap its cropped side/back panels;
it is not an extra modeled weapon. Surface interpretation is deliberately less ornate than that generated painting.

Sprite masters use all eight real orientations and one camera/ground pivot. No per-frame fitting or opposite-hand
mirroring is applied. Continuous Blender/GLB motion remains independent of display-frame counts. Death includes its
final resting endpoint; a separate held Corpse is identical there. The dense 16-frame attack and 12-frame death have
precise display timing plus positive-integer legacy subsets of 12 and 10 frames respectively. The 12-pixel ground-pivot
bottom padding must be accounted for during future billboard placement; these staged sprites do not silently replace
the bottom-touching original frames.


The final native-size PNG/indexed comparison was reviewed for front/profile/rear, walking, both-sided attack and
prone poses. The 255-color opaque palette retains olive skin, contrasting dark iron/leather and the bright blade.
BMP contours are intentionally binary and therefore harder than RGBA antialiasing; there is no cyan fringe in the
reconstructed transparency previews. Front Standing visible alpha bounds are (107,22)–(246,279), 257 pixels tall,
close to the native front's 256 pixels without individual pose rescaling. Filtered alpha can extend slightly below
the nominal ground pivot. Eight-view contacts cover the separate sword side, strike extension, walking contacts,
hit shielding, quiet idle/fidget and the settling collapse. Fixed framing leaves useful margin for the longest blade
extension and corpse. The upright posture and rigid leather tassets follow the chosen stylized construction; they
are not simulated cloth or motion capture.

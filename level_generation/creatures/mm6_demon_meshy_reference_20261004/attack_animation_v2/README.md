# MM6 demon Attack — forearm and hand revision 2

This revision corrects the right forearm winding during the crossing strike and the reversed left palm.
It supersedes the earlier `attack_animation/` package, whose hand deformation was rejected by the user.
The previous files remain unchanged for comparison. **The approved shoulder-to-elbow motion is preserved
exactly at every keyed pose.**

[Before/after hand comparison](hand_revision_comparison.png) · [Playback](attack_preview.gif) ·
[Animated GLB](mm6_demon_attack.glb) · [Editable Blender project](mm6_demon_attack.blend) ·
[Native comparison](native_comparison.jpg) · [Local review record](acceptance.json).

Open the Blender project and play **Attack, frames 0–36 at 48 fps**. Its 37 keyed poses retain the six native
125 ms attack observations, giving a **750 ms** action. Walking and Running are also included. Their original
motion and timing are retained. The NLA tracks are muted while Attack is active for ordinary action editing.
The GIF repeats with a 350 ms inspection pause after the 750 ms action; it uses GIF's 10 ms time rounding.

## What caused the reported faults

The previous palm classifier used the sign of a nearly zero Y component. That classified the mirrored left
hand backward. Its palm now uses the actual claw-hook direction to establish which side is the palm, so the
left idle/guard claws hook inward as in the original sprite.

The right E anchor also forced the palm to remain front-facing as the fingers reversed direction across the
chest. Interpolation accumulated almost a full forearm turn during recovery. The twist helpers then wound the
skin even though the endpoint hand orientation appeared plausible. The crossing strike now presents the
hand's back/edge, producing a short, continuous rotation path. The native sprite establishes the crossing
direction; this hidden palm orientation is a restrained 3D interpretation, not a directly observed surface.

The existing forearm twist helpers and repaired claw/jaw weights remain. This revision corrects the orientation
controls instead of further changing weights. The upper arms, clavicles and elbow centers match version 1
exactly. Rest geometry, topology, bind pose, feet, head, jaw, tail, and the Walking/Running clips are retained.

## Review

Both forearms, wrists, palms and claws were checked through all **37 poses**, including frames **18, 19, 21,
23, 26 and 28**. Original-resolution front/profile detail plates are in [review_plates/](review_plates/).
The before/after comparison retains the original render pixels and includes the left idle and frame 21.
Full poses, native observations, other anchor views and the actual exported GLB were also reviewed.

Dense checks evaluate **145 attack times**, at quarter-frame intervals:

| Check | Result |
| --- | ---: |
| Clavicle/upper-arm transform change against rejected version | 0 |
| Shoulder/elbow center change against rejected version | 0 |
| Maximum wrist bend | 45.00001° |
| Lowest pose median forearm core radius / rest radius | 98.814% |
| Same measure in rejected version | 73.337% |
| Lowest individual sampled core radius / rest radius | 88.870% |
| Hand-versus-torso triangle intersections | 0 |
| Minimum distal-claw surface gap | 0.003438 model units |
| Maximum rigid claw edge length error | 0.01345% |
| Triangle area collapse flags below 0.1 of rest | 0 |

Radial measurements screen the middle forearm section; they are not a complete volume or self-intersection
proof. Close-up inspection complements them. The previous length/claw checks alone missed the winding fault.
See [hand_revision_review.json](hand_revision_review.json) and [deformation_review.json](deformation_review.json).

The actual GLB was reimported at 48 fps and compared with the standalone Blender project at **311 times**:
145 Attack, 101 Walking and 65 Running. Maximum mesh-coordinate error is **0.000001908 model units**.
Triangle connectivity and all 85 joints match. The exported file was rendered from front, profile and both
three-quarter directions. [Export audit](export_roundtrip_audit.json) · [Export renders](export_review_frames/).

## Retained model differences

The supplied mesh still has **four long claws plus a thumb** per hand; the native sprite exposes three long
claws plus a thumb. Its curved terminal claws, broad palms, body/head proportions and larger tail blade remain.
This pass fixes the animation on that geometry; it does not sculpt a new hand or claim an exact native silhouette.
Only one genuine frontal native attack view exists, so depth and intermediate motion are inferred.

The package is untextured, with no original UV layer. It is staged for user review and has not been installed
into gameplay. User artistic acceptance of this revision has not been recorded. Source hashes and the preserved
version-1 deliverable hashes are verified in the local review record. Shared tools, skills, runtime assets and
global ledgers were not edited.

## Reproduction

`start_revision.py` records the initial scene copy; run it only once when establishing a new revision.
`author_attack.py` keys `motion.py` into the task-owned scene. `review_attack.py` checks dense deformation and
renders poses; `review_hand_revision.py` measures forearm sections, wrist bend and unchanged upper arms.
`inspect_surface_flags.py` stores posed geometry. `make_review.py` and `make_hand_revision_review.py` compose
the detail plates, comparison and GIF. `export_attack.py`, `normalize_attack.py`, `check_export.py` and
`render_export.py` export, normalize and independently review the delivered files.

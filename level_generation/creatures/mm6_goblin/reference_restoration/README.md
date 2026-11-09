# Goblin AI restoration references

Generated with the built-in image-generation tool following the imagegen skill. Native images control identity,
proportions and pose; AI supplies reviewed interpretations of surface/construction detail. No external image-to-3D
service is involved in these references.

| Output | Inputs | Selection/review |
| --- | --- | --- |
| `turnaround_v1.png` | `../source_audit/standing_strip.png`, `../preflight/restoration_front_test.png` | Selected surface/construction guide; native resting weapon direction overrides frontal pose; omit invented back spine strap |
| `combat_v1.png` | `../source_audit/combat_reference_inputs.png`, `turnaround_v1.png` | Selected attack anticipation/slash, shielding hit and prone corpse poses; key limb direction and death outcome agree with originals |
| `motion_v1.png` | `../source_audit/motion_reference_inputs.png`, `turnaround_v1.png` | Falling and standing/fidget panels selected; walk panels useful for upper-body motion but repeat a leading foot and are not authoritative gait-contact references |
| `motion_v2_attempt.png` | `motion_v1.png`, native motion sheet | Rejected correction: did not convincingly fix the first walk contact |
| `head_v1.png` | `turnaround_v1.png`, native standing strip | Selected face/ear construction and surface guide; frontal and profile depth coherent |
| `walk_contact_attempt.png` | native `gobwaa0.png`, `turnaround_v1.png` | Rejected as the requested left-leading contact: repeats the right-leading step. Keep native contact order for rigging; do not copy this error into motion |
| `../textures/olive_skin.png` | `head_v1.png` | Selected flat skin pigment/grain swatch; no face/body features painted into it; used with stored rest-position coordinates on body skin |
| `../textures/brown_leather.png` | `turnaround_v1.png` | Selected flat brown leather grain swatch for belt, pouch, straps and skirt; geometry supplies garment shape |
| `../textures/worn_iron.png` | `turnaround_v1.png` | Selected dark forged iron with small pits, abrasion and restrained oxidation; replaces broad cloudy armor noise; exact prompt in `iron_material_prompt.txt` |

| `../textures/hand_surface.png` | `../review/surface_v2_detail_hand.png`, `turnaround_v1.png` | Selected matched-pose hand skin detail; only skin projected, side view checked; `hand_surface_prompt.txt` |
| `../textures/torso_surface.png` | `../review/surface_v2_detail_torso.png`, `turnaround_v1.png` | Selected matched-camera torso skin detail; preserves armor coverage; model close-up reviewed; `torso_surface_prompt.txt` |
| `../textures/feet_surface.png` | `../review/surface_v2_detail_feet.png`, `turnaround_v1.png` | Selected toe/foot skin detail; generated armor changes excluded by masks; `feet_surface_prompt.txt` |

Exact prompts are the corresponding `*_prompt.txt` files. All outputs are saved locally and the native contact
sheets retain frame labels. The preflight front test is useful secondary material reference but has a short-weapon
error corrected by the full turnaround. See [calibration notes](../ART_CALIBRATION.md) for explicit native overrides.

These are reference sheets, not sprite deliverables. Final sprites must be actual renders of the completed rig.

The walking attempts establish useful garment and arm detail, but their leading-foot mismatch survived a targeted
edit and a separate single-pose generation. Further broad regeneration is not an animation solution. Use the audited
native walk phases to set explicit left/right foot contact constraints in the rig, and verify the resulting 3D contact
poses directly against those sprites. The fallen and fidget panels and combat references are selected independently.

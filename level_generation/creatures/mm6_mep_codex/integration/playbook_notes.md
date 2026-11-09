# Production lessons

1. **Native grip overrides a generic archetype.** Mep is a one-handed walking-stick NPC. StaffAttack1 and
   StaffCastLAttack3 supply library motion, adapted to a right grip and a relaxed free arm. No invented Baa logo
   or metal staff ornament. The short coat is not an ankle-length monk robe.
2. **Remove false cuff lids.** Meshy produced 19 transverse triangles over the sleeve openings. Removing those
   interior caps, fitting the hidden proximal forearms and retaining the rolled rims solved the real obstruction.
3. **Cloth needs the right geometric test.** This open coat is not a closed robe volume. Use exact finite
   edge/triangle crossings against its actual walls, then report signed penetration. Whole-volume tests mistake
   deliberately enclosed forearms for faults. Reduced coat tails need weights fitted to the reduced trouser surface
   and clearance in the hidden trouser layer, including the full backward fall.
4. **Contact outranks arbitrary triangle ratios.** Preserve the held hand/forearm, cuffs and soles. Aggressive
   reductions passed silhouettes but collapsed the grip or pierced sleeves. Read the recorded curve and the final
   counts; the LOD2/3 counts exceed the approximate budget guidance to retain measured contact and silhouette gates.
5. **Select UV faces explicitly.** Inherited vertex selection packed the whole body into the head atlas. Use face
   selection mode, deselect everything, then select the material faces before smart-projecting. Dedicated head UVs
   retain the separately generated face detail. Body/head ramps must agree before merging their runtime materials.
6. **Bake overlapping pieces separately at lower LODs.** Larger cages fixed misses but projected the coat onto
   the sash and skin. Isolate matching native pieces for the bake and retain the shared UV atlas. Bake base, region
   channels, ORM and tangent normals; carry baked AO into ORM R after glTF export.
7. **Measure surfaces, not vertex distributions.** Use area-weighted sole direction and actual two-sided hand/prop
   surface distances. Sparse prop vertices overestimate a close grip. Solid-angle containment avoids single-ray
   parity errors on a narrow shaft. Rig gates sample all clips at 48 Hz; released props are excluded from held-grip
   checks after their actual release time.
8. **Smooth in world space.** Filtering local attack rotations lost clavicle compensation and increased jerk.
   Filtering world upper-arm/hand rotations, retaining the anatomical elbow hinge and adding a short return to idle
   kept the library stroke and removed its fitted arm spike. Recheck the actual staff-tip timing afterward.
9. **Match the runtime gait contract.** WorldFxSystem advances Running at 1.55 times the walking stride. Fit the
   ankle trajectory to that ratio while preserving the low lift and contact phase. Recheck actual sole skinning;
   the longer stride needed a millimetre-scale upward pelvis correction. Never lower the held staff through the floor.
10. **Validate the exported animation.** This fast stroke needed 240 Hz export sampling for millimetre-level
    parity with the master at 48 Hz. Every LOD must be tested with the same LOD0 actions that the runtime uses;
    appended Blender actions need fake users before saving the review blends.
11. **Review all eight skin influences.** Stock three.js normalizes the first four. The project viewer reuses
    the existing Sorcerer review shader that restores the first set's share and evaluates the second set too.
    Blender's imported bone-handle Icosphere is not the creature mesh: select `Mep` explicitly for framing.

## Review round 1 (supersedes initial smoothing/contact advice)

- Damp local spine joint deltas, not a full world-space source turn: a shortest-path world rotation can reverse across 180 degrees. Distribute wrist roll into forearm helpers while preserving the hand frame, then smooth the fitted quaternion curves, including their torso parents.
- Use semantic piece ownership for sash/button region masks; projection colour is not a reliable region boundary. Rigid button weight sets prevent triangle flecks, and physical sash seating is separate from texture cleanup.
- Run cadence and stride are independent: this run is 0.60 s with 0.958182 m stride, versus a 0.80 s / 0.618182 m walk.
- Shared cloth selectors must distinguish short open clothing, decorative buttons, sewn waist overlap and allowed openings. A reported nearest face can be a temporary cap; preserve that fact in the authoring receipt. Hidden low-LOD waist weights should follow the neighbouring coat during falls.
- Keep shadow cloth/contact positions with the colour mesh; broad normal insets can destroy grip and cloth topology.
- The shared runner currently requires an edge axis for a blunt staff and has no shoulder-volume test. Record UNVERIFIED and visual evidence; do not invent an edge, new per-creature gate code or a numerical PASS.

## Review round 2

- A retexture return is not sufficient evidence of aligned eyes. Register the actual geometry's eye/nose/lip landmarks to the retained HD reference and inspect front, profile and quarter views. Keep face/ears/neck continuous; the seam belongs behind the head.
- Calibrate head and body through the same native palette ramp and measure both mean and highlight luminance after region masks. Texture RGB alone does not establish final skin tone.
- For a belt wrapped around a coat, check the covered coat waist inside the closed belt volume. A cropped coat strip may create false cap collisions; diagnose the shared runner surface without inventing a replacement gate. Coarse LOD chords need extra clearance and matching coat weights.
- When a spell uses Attack motion, export an exact separate Cast action for engine identity. Compare every exported channel and align cast/attack impact times and staff-head launch socket.

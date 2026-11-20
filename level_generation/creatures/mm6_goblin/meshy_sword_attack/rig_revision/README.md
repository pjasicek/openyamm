# Meshy goblin: arm and grip revision

2026-09-23. Review checkpoint following the faults shown in test_img/2025.png–2027.png.
**This is not an accepted production asset.** Original downloads and the previous sword project are preserved.

## Open first

- [Visual review](review.html): native comparison, continuous front/quarter/elevated attack playback and grip close-ups.
- [Editable project](goblin_arm_revision.blend): isolated scene, packed textures, reversible grip shape and source actions.
- [Portable revision](goblin_arm_revision.glb): choose `MM6_Attack_Rig_Revision` or `MM6_Standing_Rig_Revision`.
- [Standalone sword](mm6_goblin_sword.glb): revised handle thickness.

The ten `Meshy_*` animations are retained references. They have not passed sword-contact or deformation review on
this revised rig. The previous project README describes reference provenance and weapon construction.

## Diagnosed causes and changes

| Reported fault | Cause in the previous pass | Revision |
| --- | --- | --- |
| Loose sword grip | Rigid attachment alone did not make the fingers grasp; grip bent already-curled geometry again | Refit finger curl and thumb opposition; thicken handle; fit intersecting finger pads to the handle surface |
| Wrist reversal | Camera-facing blade normal reversed when the slash crossed the body | Consistent blade-up basis; whole-arm solution; constrained hand/forearm bend |
| Forearm distortion | Unbounded wrist/forearm roll, auto weights across the bracer, and discontinuous twist interpolation | Four twist helper bones, unwrapped twist angles, smooth transition weights and rigid bracer weighting |
| Flared free arm | High wrist target and outward elbow target | Lower standing hand and attack counterbalance; revise elbow placement |

The measured angle between hand and forearm axes changed from roughly 60–142 degrees to 17–35 degrees in the
sampled right-arm attack. This measures these bones' axes, not clinical wrist range. It does not prove the animation
is anatomically finished. The 180-degree helper-bone flip has also been removed.

## Evidence and remaining work

- Front, quarter and elevated Workbench playback: 18 frames per view; close-ups on both sides of the grip.
- Material preview: 18 front frames and six quarter poses, with fixed orthographic framing.
- Reimported GLB: 0.75-second attack; 19 samples including endpoint; maximum joint-position error about
  0.0000039 model units; maximum evaluated bounds error about 0.0000027 units. Grip morph is retained at 1.
- `review/export_verification.json`, `review/rotation_steps.json`, `review/after_arm_angles.json` and
  `review/motion_bounds.json` record focused checks. Bounds remained above the ground in sampled attack frames.
- 32 rig bones (original 28 plus four twist helpers), 103,449 triangles, 12 clips. No runtime optimization implied.
- The grip is still a fixed shape key: this rig has no independently articulated fingers. Thumb placement, fist
  volume and remaining gaps need a hand-sculpt pass before close-up acceptance. The cylindrical contact check is
  a diagnostic proxy, not an exact collision test or proof of a convincing grasp.
- Shoulder/elbow gesture, the free hand and whole-body weight transfer still need artistic review against native
  poses. One-shot entry/recovery transitions and all other actions remain unapproved. Repeated playback is for
  review; the attack is not a seamless looping action.
- Final directional billboard captures, game-size readability, lighting and engine installation remain separate work.

No paid generation was used. The wrist flip was introduced by the previous authored animation approach;
export correctness alone was insufficient validation of that pass.

## Reproduction

In Blender, execute `init.py`, `build.py`, `repair_skinning.py`, then `fit_contact.py` in order. Start from the
previous `../goblin_sword.blend`; use an isolated session or unique scene names when rerunning initialization.
`build.py` adds helper bones and authors poses; `repair_skinning.py` then restores original source weights and
applies the bracer/twist treatment; `fit_contact.py` finishes the grip. Rebuilding resets the grip, so rerun both
finishing scripts after changes. All four scripts belong to this revision.

Run `render_review.py` and wait for its queue, then `render_grip.py`, then `render_final.py` and wait for its queue.
Use `package_asset.py` for GLBs and the isolated scene library; run `save_project.py` in a fresh background Blender
for the normal editable project. `verify_export.py` checks the actual export. Run `package_review.py` in ordinary
Python with Pillow for comparison GIFs and contact sheets. GIF timing totals 750 ms.

See [the production sequence](../../MESHY_PRODUCTION_FLOW.md) for acceptance gates and next steps.

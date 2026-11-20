# MM6 demon Attack — foot motion revision 3

The attack now includes a small inward right-foot pivot during the crossing strike, with the right knee following
the turn. The existing pelvis dip and both legs' flex are retained. This implements the
[original six-frame foot study](../attack_study/feet_review_20261004/README.md): ground support stays steady while
the right foot changes orientation. Only the right thigh, shin and foot rotation curves changed.

[Full attack playback](attack_preview.gif) · [Foot playback](feet_preview.gif) ·
[Native / previous / revised feet](foot_revision_comparison.png) ·
[Animated GLB](mm6_demon_attack.glb) · [Editable Blender project](mm6_demon_attack.blend) ·
[Review record](acceptance.json).

Open the Blender project and play **Attack, frames 0–36 at 48 fps**. There are 37 keyed poses across the native
750 ms action; native observations remain at frames 0, 6, 12, 18, 24 and 30. The GIFs add a 350 ms inspection
pause at the endpoint. Walking and Running retain their original timing and motion. The live Blender MCP scene
`MM6_Demon_Attack_v3` also displays this revision; older scenes and packages remain available.

## Motion and preservation

Right-foot yaw at A–F is **0°, −2°, −3°, +12°, +14°, 0°** relative to the previous attack, with smooth transitions.
The knee follows 35% of that turn. A support pivot under the foot, slightly ahead of the ankle, allows a maximum
13.4 mm ankle displacement while retaining foot height. The left supporting foot keeps its previous pose.
The claws move with the whole foot, without individual toe curls or a sideways roll.

These degree values are restrained 3D interpretations. The original has one genuine frontal attack view;
it shows the foot turning but cannot uniquely establish the hidden joint angles. The supplied mesh's broad feet,
curved claws and other proportion differences remain, so this does not claim an exact native foot silhouette.

The corrected forearms, wrists and palms, approved shoulder/elbow motion, torso, head, jaw and tail match revision 2
exactly. The final project has **12 changed quaternion component curves, all on three right-leg bones**, out of
850 Attack curves. Rest geometry, triangle connectivity, all weights and all 85 bind matrices are identical.
There are no weight or rig-structure changes. Walking and Running each have zero changed curves and zero measured
mesh change across 101 and 65 sampled times respectively. [Preservation audit](preservation_review.json).

## Checks and visual review

All 37 poses were reviewed from the front and right profile, with original-resolution leg/ankle/foot plates in
[review_plates/](review_plates/). Six before/after close-ups focus on the changed right foot; the left foot is partly
outside those close-up cameras, and is covered completely in the common front/profile plates.

At 145 quarter-frame times, checks found:

| Check | Result |
| --- | ---: |
| Corrected upper-body world transform / mesh change | 0 |
| Left-foot position change against revision 2 | 0 |
| Maximum sole-height change against revision 2 | 0.088 mm |
| Minimum foot height above the floor | 1.871 mm |
| Maximum rigid foot/claw edge length error | 0.00294% |
| Maximum leg-segment length error | 0.0000358% |
| Lowest median shin core radius relative to revision 2 | 99.9973% |
| Lowest median thigh core radius relative to revision 2 | 99.9999% |
| Collapsed triangles below 10% of rest area | 0 |

Between 48 fps keys, parent quaternion interpolation introduces submillimeter contact residuals. These remain
inside the 2 mm foot clearance; no ground penetration or visible foot lift was found. Section-radius checks
screen the central thigh/shin and complement visual inspection; they are not a complete volume proof.
[Dense contact/deformation audit](foot_deformation_review.json).

The actual GLB was reimported and compared with the final Blender project at **311 times** across Attack,
Walking and Running. Maximum mesh-coordinate error is **0.000001908 model units**. It retains one mesh,
85 joints, 7,899 vertices and 15,686 triangles. Twenty-two actual exported poses were reviewed from the front,
right profile and both three-quarter directions. [Round-trip audit](export_roundtrip_audit.json) ·
[Export renders](export_review_frames/).

The package remains untextured, with no source UV layer. This requested foot-motion revision is complete for
local review; user artistic acceptance is not yet recorded. The original model, native sprites and previous
packages are preserved. No gameplay installation, runtime changes, shared-tool changes or global-ledger edits
were made.

## Reproduction

`author_feet.py` creates/reuses the isolated live MCP scene and keys only the three right-leg rotations.
`review_feet.py` compares the previous file, checks dense poses and renders them. `render_previous.py` renders
the prior Attack explicitly for before/after plates; `make_review.py` composes the plates and previews.
`export_attack.py` exports the checked scene, `normalize_attack.py` makes a normal standalone Blender file,
and `check_export.py`, `check_preservation.py` and `render_export.py` independently inspect the actual files.
`finalize_acceptance.py` checks source hashes and records the completed visual review.

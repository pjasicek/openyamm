# Meshy MM6 goblin: curved sword and native-style attack

Created 2026-09-23 from the head-corrected Meshy goblin. Original downloads and preceding review assets are unchanged.

> Superseded for arm/grip review by [the isolated rig revision](rig_revision/README.md).
> User review identified loose grip, wrist reversal, bracer distortion and an unnatural free arm in this pass.
> Its successful export checks did not establish production quality.

## Open first

- `review.html`: original/model animation comparison, six paired poses, sword render, and asset links.
- `goblin_sword.blend`: normal editable Blender project with packed character textures, the sword parts,
  reversible `SwordGrip` shape key, lights, camera, source actions and authored actions.
- `goblin_sword_attack.glb`: portable animated character, sword and grip correction.
- `mm6_goblin_sword.glb`: standalone reusable sword, centered on its grip.

Choose **MM6_Attack_Native** in a GLB animation viewer. **MM6_Standing_Sword** is the matching armed stance.
The ten **Meshy_*** clips remain available as references. In particular, **Meshy_Attack** and
**Meshy_Right_Hand_Sword_Slash** are the imported motions, not the authored original-style slash.
Other imported clips have not been fully adapted to sword-ground/body contacts or native MM6 poses.

## Native references and interpretation

Authoritative motion references:

- `../source_audit/frames/gobata0.png` through `gobatf0.png`, six native frontal attack frames.
- `../source_audit/standing_strip.png`, especially the profile, which shows the blade's actual length.
- `../direct_ai_attack/edge_cleanup/attack_cleaned_3x2.png`, restored surface/shape reference.
- `../ART_CALIBRATION.md`, native timing, handedness and construction findings.

The sword is an original mesh: a long curved single-edged warm-steel blade, thin bright sharpened edge,
small swept gold crossguard, gold knuckle bow and pommel, and a wrapped dark grip. Blade length is 0.745
model units; the full weapon extends about 0.95 units from pommel to tip. It is rigidly weighted to the
right hand, with no blade bending. The static sword uses Blender +Y as the blade direction and +Z as its curve rise.

The Meshy rig has no independent finger chains. `SwordGrip` closes the right-hand geometry around the handle
while retaining source UVs and the unmodified Basis shape. It is an editable posed grip, not a newly articulated
finger rig. Its default weight is 1 in both the Blender project and the GLB.

The new attack is authored from the source sequence, not retimed from a Meshy preset:

| Time | Source phase |
| --- | --- |
| 0.000 s | Sword drawn diagonally across the front |
| 0.125 s | Torso turns and sword rises toward image-right |
| 0.250 s | High cross-body anticipation, free hand nearby |
| 0.375 s | Blade crosses and descends in front of the torso |
| 0.500 s | Extension toward image-left; blade rolls nearly edge-on |
| 0.625 s | Low, foreshortened recovery |
| 0.750 s | Return toward the armed standing pose |

The six native display intervals are 0.125 seconds each. Continuous FK motion is authored at 48 samples/sec
and the GLB is sampled at 24 fps, preserving the 0.75-second span. Original first-frame pose and the eventual
standing pose differ; this is a one-shot attack, not a seamlessly looping idle.

The original only provides a frontal attack sequence, so depth, wrist roll between samples, and opposite-side
views are inferred. The supplied Meshy anatomy/costume and the restored sword interpretation differ from native
pixels. This is a reviewable reconstruction, not a claim of pixel-exact recovery of the original 3D asset.
The sword/body material lighting is a neutral studio review; it is not final MM6 billboard lighting.

## Focused validation

- Front, three-quarter and profile pose review; textured front playback and six three-quarter samples.
- Fixed orthographic framing and one model scale across the entire attack; no per-frame fitting.
- Original/model comparison normalizes the standing body height (256 native pixels versus 1.700 model units)
  and uses one ground line. Original frames are enlarged with nearest-neighbor filtering.
- Evaluated body and sword bounds checked at all 19 delivered-rate timeline samples, including the endpoint.
  Minimum evaluated height is approximately zero; no sampled below-ground geometry was found for this attack.
- Final GLB reimport checks every attack frame against the authoring scene, including deformed bounds and grip.
  Exact recorded tolerances and shape-key values are in `review/export_verification.json`.
- Blender GLB export filters both selected objects and active scene, excluding unrelated open scenes/widgets.
- The character GLB has 103,449 triangles (97,517 body + 5,932 sword), 28 skin joints, embedded body textures,
  the default grip morph and 12 named animation clips. The standalone sword has 5,932 triangles.
- `review/delivered_attack.png` and `review/sword.png` are rendered from the actual reimported GLBs.

No paid Meshy requests were submitted. No game assets were installed or engine code changed.

## Reproduce

Run Blender-side scripts through the installed Blender MCP in order:

1. `inspect_source.py`: import the corrected source into a separate scene, inventory its rig.
2. `build_sword_attack.py`: build the sword, editable grip and the two authored actions.
3. `render_final.py`: schedule the textured frame renders. Wait for its timer queue to finish.
4. `package_asset.py`: export both GLBs and an isolated scene library in `/tmp`.
5. Run `save_project.py` in a fresh background Blender (`--factory-startup`) to save the normal `.blend` project.
6. `verify_export.py`: reimport the delivered models, check the attack, render the actual delivered assets.
7. Run `python3 package_review.py` from the shell for the review page, comparison GIF and contact sheets.

`construction.json` records the authored controls. `render_review.py` provides optional Workbench pose diagnostics.
The source GLB path in `inspect_source.py` is the earlier corrected-model deliverable in this repository's `output/`.

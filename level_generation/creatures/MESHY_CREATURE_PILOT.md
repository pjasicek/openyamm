# Meshy creature pilot

Research checked 2026-09-23. Planning only: no image generation, Meshy submission, or credits spent.
Use alongside [Sprite-to-3D workflow](SPRITE_TO_3D_WORKFLOW.md). These are proposed settings, not tested results.

Subsequent preparation: [four goblin upload images and prompts](mm6_goblin/meshy_reference_v2/README.md)
are now available. That image-preparation task used built-in image generation; no Meshy job was submitted.

## Recommendation

Start with the green MM6 goblin. Produce an editable rigged master, then render directional sprites in Blender.
Keep the model suitable for a future runtime version. Meshy can supply an initial mesh, textures, skeleton and
motion; native likeness, equipment attachment, deformation and original animation timing still need visual work.

The current [glTF loader](../../engine/models/GltfModelLoader.cpp) rejects joint/weight attributes and visible
mesh skinning. A rigged Meshy GLB is therefore not a drop-in animated creature today. Billboard production can
proceed independently of that engine work.

## Actual references

Use original sprites to settle silhouette, proportions, equipment and motion. Use reviewed restored art for
surface detail. Do not submit originals and restorations as competing views of different-looking bodies.

| Candidate | Local evidence | Pilot decision |
| --- | --- | --- |
| MM6 goblin, green palette 745 | [Native views](mm6_goblin/source_audit/standing_strip.png), [current side comparisons](mm6_goblin/direct_complete/redo_2x/review/standing_sides_redo_01_detail_contact.png), [design audit](mm6_goblin/ART_CALIBRATION.md) | Best first test: established anatomy and equipment notes; restored manifest says `validated_staged_redo`. |
| MM6 ogre, blue spike palette 784 | [Standing comparison](mm6_ogr/redo_2x/review/standing_redo_01_detail_contact.png), [manifest](mm6_ogr/redo_2x/manifest.json) | Useful second test. Manifest still says `pending_full_animation_and_variant_review`; do not describe the entire set as accepted. |

Goblin current restored frames are in `mm6_goblin/direct_complete/redo_2x/aligned_2x/gobsta0.png` through
`gobsta4.png`. Original PNGs are in `mm6_goblin/source_audit/frames/` with the same stems.
Ogre restored frames are in `mm6_ogr/redo_2x/aligned_2x/ogrstda0.png` through `ogrstda4.png`.
The inspected ogre comparison contains native and restored views together for review, not Meshy upload.

The older goblin [turnaround](mm6_goblin/reference_restoration/turnaround_v1.png) is a construction guide with
documented mistakes: its frontal sword crosses the body, and it invents a studded strap down the spine.
The original resting sword points forward; most of the back is exposed, with two small upper-back plates.
Its apparently short frontal sword is foreshortened: the profile establishes a long curved blade.
Current restored side views also need a consistency check against the original before becoming 3D inputs.

Both candidates are armed humanoids. The ogre is not an unarmed, simple rigging control case: it has a long blade,
shoulder spikes, large hands and a skull chest ornament. Its reviewed palette contract changes spike accents only.

## What to supply to Meshy

Prepare four separate full-body views of one design in one neutral A-pose: front, three-quarter, profile, rear.
Use consistent scale, ground level, lighting and anatomy. Keep arms clear of the torso, feet apart and the entire
silhouette visible. Aim for genuinely detailed 1024-pixel reference images; enlarging a small crop adds no information.
Use an even neutral background, no labels, contact-sheet borders, floor props or dramatic shadows.

This is a preparation recommendation: the existing standing frames have not yet been converted into that set.
One coherent view is preferable to adding contradictory views. Do not fill extra slots with attacks, palette variants,
face close-ups or mirrored sword hands. A contact sheet is useful for review; each Meshy slot should show one figure.

The website recommends front/side/back/three-quarter references, consistent lighting and near-orthographic images.
Choose **Multiview** for one creature; **Batch Images to 3D** creates separate assets.
[Website image guide](https://docs.meshy.ai/en/webapp/image-to-3d).

The API accepts 1–4 images; with `meshy-7.1`, put the front image first. Its documented geometry inputs are images
and settings; `texture_prompt` controls texture, not body shape. There is no documented general geometry prompt
or negative-prompt field on this endpoint. [Multi-image API](https://docs.meshy.ai/en/api/multi-image-to-3d).

My preferred preparation is an unarmed body with the original costume, then a separate rigid sword attached to
the right hand in Blender. This deliberately changes only the modeling reference pose and prop staging. Restore the
complete armed design before judging the final character. It avoids betting the rig on separating a blade fused
to the fingers or thigh. The sword can be modeled locally from its native profile without another Meshy generation.
If using the armed references directly, inspect and separate the weapon before rigging; do not assume automatic
part separation or correct weapon weights.

## Prompt for preparing the goblin reference images

This prompt belongs in an image-editing tool with the original and restored references attached. It is not a
Meshy geometry API prompt. Generate the front first, check it, then condition other views on that same front and
the corresponding native view. Review the complete set together before spending on 3D.

```text
Prepare a full-body modeling reference of this exact MM6 goblin.
The original sprite views define its proportions, silhouette and equipment.
The restored references define the fine surface detail and material finish.

Preserve the lean muscular body, narrow waist, long forearms, clawed hands,
long forward-projecting feet, compact angular head, heavy brow, pointed ears
and backward-projecting head silhouette. Keep olive green skin and yellow eyes.
Retain the small dark riveted chest gorget, spiked shoulder caps, separate
forearm and shin guards, brown belt and pouch, and individual leather skirt strips.
Keep the abdomen, thighs and most of the back exposed. Retain the two small
upper-back plates; omit the invented central spine strap in the older restoration.

Place the character in a relaxed A-pose, arms about 35 degrees away from the torso,
legs slightly apart, hands relaxed and fully visible. Preserve its creature
proportions when changing the pose. For this body reference only, omit the sword;
it will be a separate rigid prop in the assembled model. Keep the sword-side pouch.

Output one front view, full figure with clear margins, near-orthographic camera,
even soft lighting and a plain neutral gray background. Match the restored art's
restrained worn iron, brown leather and detailed skin. No new armor, accessories,
pedestal, text, cinematic lighting or exaggerated cartoon anatomy.
```

For subsequent views, replace the output-view sentence and add:

```text
Rotate the same character and the same A-pose to the requested camera angle.
Preserve the approved front design exactly; the attached native angle clarifies
its depth and costume coverage. Keep physical left and right consistent.
```

For an ogre pilot, substitute its observed design: gray-brown skin, heavy brow, tusks, yellow eyes, silver shoulder
and arm armor, blue shoulder/forearm spikes, crossed brown chest straps with a gold skull medallion, belt,
ragged orange-brown loincloth, lower-leg wraps and large clawed feet. Keep its actual body ratios; avoid the
generic round-bellied, club-carrying ogre stereotype. Use palette 784 consistently throughout reference preparation.

Meshy's general prompting guidance favors concrete subject, materials, style and constraints, with the essentials
first. A phrase such as “authentic MM6 goblin” alone cannot specify our exact design.
[Prompting guide](https://docs.meshy.ai/en/webapp/guides/prompting).

## First geometry attempt

My starting choice is High Detail at standard geometry resolution. The priority is testing likeness at reasonable
cost. Keep the dense original; optimize an accepted copy later. Smart Topology is a possible later comparison for
runtime use, not an extra first-round generation. Its current single-image API model is `meshy-t2` and targets
100–15,000 faces. [Image API](https://docs.meshy.ai/en/api/image-to-3d).

Website: choose the available Meshy 7-series High Detail model, Multiview, A-pose, Image Enhancement off,
Ultra off. Inspect the displayed cost and whether texturing is a separate step. The public website guide still
uses “Meshy 7”; API model names need not match the visible UI.
[Website workflow](https://docs.meshy.ai/en/webapp/getting-started).

API geometry-only template, after reference preparation, for `POST /openapi/v1/multi-image-to-3d`:

```json
{
  "image_urls": ["<front PNG URI>", "<three-quarter PNG URI>", "<profile PNG URI>", "<rear PNG URI>"],
  "ai_model": "meshy-7.1",
  "geometry_resolution": "standard",
  "pose_mode": "a-pose",
  "image_enhancement": false,
  "should_texture": false,
  "should_remesh": false,
  "target_formats": ["glb"]
}
```

This pins the documented model rather than `latest`. With remeshing off, a target polycount would not control this
standard model's output. A-pose is a requested transformation, not evidence the generated proportions are correct.
[Multi-image parameters](https://docs.meshy.ai/en/api/multi-image-to-3d).

Reject major head, body or armor errors before texturing. Compare the untextured mesh from front, profile and rear,
then compare a render at actual sprite size. Inspect ears, feet, hands, underarms and leather-strip gaps.
Repair small local faults in Blender; revise the input before retrying a major design failure. Repeating unchanged
paid submissions gives us little information.

## Texture, topology and rig

Prefer reference-image texturing to maintain the selected design. Retexture accepts an exported model URL or data
URI, so the workflow need not depend on multi-image task IDs being accepted by another endpoint. Its documented
multi-view texturing currently requires explicit `meshy-7`, not the geometry endpoint's `meshy-7.1`; availability
is rolled out by account. Use the endpoint's actual model list. Select 4K base color and PBR for the master,
then assess the real render. Preserve usable UVs. [Retexture API](https://docs.meshy.ai/en/api/retexture).

Optional material prompt, if choosing text-driven texturing instead of image guidance:

```text
Olive green goblin skin with restrained natural mottling and fine pores;
yellow eyes, dark worn iron armor with small rivets and muted brass accents;
weathered brown leather belt, pouch and skirt strips. Match the supplied
reference palette and material boundaries. Exposed abdomen, thighs and back
remain skin. Fine realistic surface detail, subdued wear, readable at small
sprite size. No painted shadows, glowing markings or added costume patterns.
```

For generation this is `texture_prompt`; for Retexture it is `text_style_prompt`. Both have an 800-character limit.
Use the appropriate image-guidance field OR text field deliberately: endpoint precedence rules differ.
[Image API](https://docs.meshy.ai/en/api/image-to-3d), [Retexture API](https://docs.meshy.ai/en/api/retexture).

Finalize topology before rigging. For offline billboard production, prioritize rendered appearance and deformation;
there is no mandatory game-runtime polygon budget for the baking model. Retain the dense master. Reduce a copy only
for actual tool limits, editing speed or observed deformation needs, and compare its silhouette/detail before use.
Automatic remeshing does not certify good shoulder, elbow, hip or finger deformation. The earlier 30,000–60,000
suggestion was an optional working-mesh range, not an acceptance target for this billboard task.

The rigging API documents textured humanoid GLBs, clear limbs, a 300,000-face limit for task inputs, and +Z forward
for uploaded models. It returns rigged GLB/FBX and may include basic walk/run clips. Inspect returned clips before
paying for duplicate tests. [Rigging API](https://docs.meshy.ai/en/api/rigging).
The website also advertises quadrupeds, but custom facial/tail rigs need DCC work; do not infer those capabilities
from the humanoid API contract. [Website rigging](https://docs.meshy.ai/en/webapp/guides/3d-model/rigging).

Test one walk and an arm raise first. Check planted feet, knees, shoulders, skirt penetration and weapon grip.
Keep the sword rigid, attached to the correct hand. Add jaw/finger or costume controls locally when required;
“rigged” alone does not establish those controls or animation quality.

## Animation and billboard output

The website exposes an animation preset library and exports animated FBX/GLB.
[Animation guide](https://docs.meshy.ai/en/webapp/guides/animate).
The current API also offers Text to Motion: a separate motion clip generated from up to 400 characters,
2–10 seconds in half-second increments; Prime outputs FBX, Swift BVH.
[Text to Motion](https://docs.meshy.ai/en/api/text-to-motion).
Apply that clip through `motion_task_id` to a biped rig. Preset batches support up to ten distinct actions, charged
individually. Generated motion retargets may return GLB only, so check the actual download fields.
[Animation API](https://docs.meshy.ai/en/api/animation).

Example goblin attack motion prompt, based on the native audit:

```text
A lean biped makes one right-handed sword attack in place. Draw the right hand
across the front, lift diagonally with a torso turn, slash across and downward,
extend across the opposite side, then recover. The left hand counterbalances.
Feet stay near their starting positions. No jump, spin or overhead club strike.
```

Treat this as a motion starting point. Meshy does not accept our sprite sequence as a documented motion constraint
here. Goblin native attack lasts 750 ms, below Text to Motion's minimum; trim and retime the useful action in Blender,
then match anticipation, contact and recovery to the source. Simple speed changes may not preserve those phases.
Also reconstruct standing, walk, hit, fidget, death and held corpse; keep native timing and variant differences.

Render a neutral turntable, walk and attack before completing all clips. Match the original camera/projection and
scale empirically. Use fixed lighting, transparent output, stable ground pivot and common framing through motion.
Render eight true directions for the asymmetric sword rather than flipping hands. Some original actions only have
front art reused in every direction: new side actions are inferred reconstruction. Preserve an explicit distinction
between native-compatible bindings and newly expanded directional coverage. Export through the existing atlas and
placement contract; test light/dark alpha edges and the final small-size appearance.

## Cost checkpoints

Published **API** rates for the proposed standard-resolution path:

| Operation | Credits |
| --- | ---: |
| Geometry only, Meshy 7.1 multi-image | 20 |
| Texture accepted mesh, 2K or 4K | 10 |
| Remesh, if needed | 5 |
| Rigging | 5 |
| One preset animation | 3 |
| Total through one preset, including remesh | 43 |

Without remesh that total is 38. Ultra adds 5; custom motion generation adds 3 (Swift) or 10 (Prime), with motion
application budgeted separately. Image-reference preparation, retries and local cleanup are outside those totals.
[API pricing](https://docs.meshy.ai/en/api/pricing).

Website pricing differs: its docs list remesh/rigging/preset animation at zero credits, but disagree internally
on standard Meshy 7 generation cost. Use the account's actual pre-submit quote; do not apply API totals to the UI.
[Website pricing](https://docs.meshy.ai/en/webapp/pricing).

First proposed paid checkpoint is one geometry attempt after reviewing the four prepared references. Download
every successful result promptly and retain inputs, settings, task IDs and actual credits. API assets are temporary;
generated motion must be applied within its three-day retention window.
[Asset retention](https://docs.meshy.ai/en/api/asset-retention),
[Motion application](https://docs.meshy.ai/en/api/animation).

Next concrete work: prepare and visually agree the goblin's consistent neutral reference views, then run the
single geometry experiment. No model or reference turnaround was generated during this research.

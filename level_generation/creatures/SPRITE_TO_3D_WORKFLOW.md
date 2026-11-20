# Reconstructing an animated 3D creature from low-resolution sprites

For MM6–MM8 Meshy production, staged handoffs and existing model WIP audit/resume, use
[Creature to 3D](../../.agents/skills/creature-to-3d/SKILL.md). Codex and Claude now share the
[humanoid](CLAUDE_HUMANOID_NPC_PLAYBOOK.md) and [non-humanoid](CLAUDE_QUADRUPED_PLAYBOOK.md) playbooks, with
[HD masters](CLAUDE_HD_MASTER_REFERENCES.md) and [shared textures](CLAUDE_CREATURE_TEXTURES.md), as the default.
Their current procedures supersede the historical modeling/animation examples below. This document supplies
supplementary coordinate, export and calibration details; explicit native reconstruction can use its pose studies.
Complete creature production includes agent-operated Meshy, equipment, runtime installation and visual checks;
`FULL` explicitly requests that scope. Preserve narrower requests and selected work on resume. The
[complete-production procedure](../../.agents/skills/creature-to-3d/references/full-production.md) defines durable
jobs, per-family ownership, isolated background Blender and runtime delivery; audit stays read-only.

For in-game 3D production, also use [3D creature model and animation guidelines](CREATURE_3D_GUIDELINES.md).
They define reviewed preset selection, blending-compatible rigs, sockets, casting, engine-owned facing and LODs,
with the demon and verified MM9 examples. They distinguish current engine support from proposed features.

Use this workflow when an agent is asked to turn an existing sprite family or sprite sheet into a textured, rigged
3D model with corresponding animations. It records the process that produced the materially improved `m242` brown
ghost, including the corrections that mattered. The driver accepted that improvement on 2026-09-07.

The historical example below used **inspect sprites → AI reference views → model and texture → iterate poses →
finish animation → inspect export**. New production follows the shared playbooks instead: select motion and review
HD masters, build and gate the model/rig/animation, then texture and verify export/runtime delivery.
Spend most iteration time on appearance and motion. A valid skeleton and export do not establish visual similarity.

The worked example is [brown_ghost](brown_ghost/README.md). Its proportions, 32 bones, seven clips, 69 source poses,
218 timeline samples and brown palette are example-specific choices, not defaults for every creature.
Read [Blender MCP startup](../BLENDER_MCP_STARTUP.md) for launching and reconnecting Blender autonomously.

## Alternative: direct enhanced sprite sheets

When the requested output is 2D sprites for an existing direction and animation, follow
[Direct MM6–MM8 sprite restoration](DIRECT_SPRITE_WORKFLOW.md). Pack the native poses into a common reference sheet,
AI-enhance them together, review their consistency and motion, then extract alpha and decontaminate mixed edge RGB
before premultiplied-alpha resizing. This route does not require building a 3D model. The accepted
[goblin attack and edge cleanup](mm6_goblin/direct_ai_attack/edge_cleanup/README.md) provide the worked example.
The modeling-reference selection guidance below applies to the 3D route; direct restoration instead covers every
requested original pose in the selected direction/action.

## 1. Establish the source, animation inventory and intended deliverable

Inspect the actual source files before modeling. A family may be separate images rather than one atlas. Trace the
runtime frame descriptors as well as filenames: texture prefix, monster identity and animation-group name can differ.
Use local OpenYAMM assets and local behavioral references; follow repository rules against copying reference code.

Record an inventory with these fields:

| Field | What to establish |
| --- | --- |
| Identity | Asset paths, creature descriptor and related palette variants |
| Views | Front, three-quarter, side and rear; genuine views versus runtime mirrors |
| Clips | Idle, locomotion, attacks, hit, death, corpse, fidget and any creature-specific actions |
| Timing | Frame order, durations, loops, held endpoints and any known gameplay contact frames |
| Appearance | Relative sizes, silhouette, visible anatomy, clothing coverage, props and material families |
| Delivery | Editable `.blend`, portable model, previews, directional sprite export, or requested game integration |

For `m242`, there are 124 original BMPs: standing 1×5, attack 8×5, movement 8×5, hit 6×5, four additional death
images, one corpse image and four fidget images. Ghost A/B/C use groups `m243/m244/m245`; there is no `m242.yml`.
The death sequence includes hit frames before the additional death frames. Inspect descriptors to discover such
ordering rather than assuming alphabetical filenames alone define the animation. See the example's
[source audit](brown_ghost/README.md#reference-audit).

Create contact sheets of native views and meaningful action extremes. Keep their aspect ratios. When comparing
silhouettes, align the ground and scale figures to equal height; independently fitting each to the same square can
hide proportion errors. Inspect both magnified pixels and the intended small display size.

Resolve routine choices from the brief and references, documenting assumptions. Do not add approval gates between
ordinary reversible steps. A request for a 3D model does not by itself require replacing game sprites or changing the
engine. Keep the original assets available and unchanged as the comparison baseline.

## 2. Restore modeling references with AI image generation

Use the available **imagegen skill and built-in image-generation tool**. Read the skill's current instructions when
performing generation. In the ghost run, lossless BMP-to-PNG conversion made the inputs readable by the image tool;
the higher-resolution restoration itself came from AI generation. Ordinary image enlargement is not that step.

Start with a small set of complementary references:

1. A neutral front, three-quarter, profile and back sheet establishing one consistent creature.
2. Action extremes showing limb reach, torso posture, clothing movement and unusual deformations.
3. A close-up of an identity-defining ambiguous feature, such as the skull, face, hands or armor construction.
4. Additional views only where an unresolved modeling decision requires them.

Do not restore every source frame before making the first model. The ghost's selected sheets covered key directions
and poses, not all 124 images. Split inputs into manageable batches within the tool's actual limits. Inspect local
reference images before supplying them to the image tool, and identify the role of each input in the prompt.

Preserve the original palette during initial restoration so shape and material identity remain easy to compare.
Apply requested variants, such as brown instead of purple cloth, after the design is understood.

A useful restoration prompt structure is:

```text
Create higher-resolution modeling references for this same creature from the supplied low-resolution sprites.
Input 1: original front view. Input 2: original profile. Input 3: original rear view.
Preserve its proportions, pose, silhouette, clothing coverage, recognizable anatomy and original palette.
Clarify the existing surfaces, folds and material wear without redesigning the character.
Keep the views consistent with one another. Show the full figure without cropping.
Do not invent accessories, extra bones, exaggerated facial features or a different action.
Where pixels are ambiguous, choose a restrained interpretation supported by the other views.
```

Customize this to the actual creature and explicit user changes. Do not impose the ghost's anatomy or torn cloth on
an unrelated subject. Save selected outputs into the project, alongside exact prompts, input filenames, tool mode
and a note identifying accepted versions. Do not leave project dependencies only in the image tool's output folder.

## 3. Review the restoration before treating it as a design reference

AI restoration interprets missing detail; it does not recover a lost original high-resolution model. Use the native
sprites to settle identity, silhouette, pose and event ordering. Use the reviewed restorations to make ambiguous
surfaces and materials concrete. Separate observed features from inferred detail in the notes.

Compare each generated view or pose to its corresponding original. Specifically check limb direction, hand height,
head tilt, exposed versus covered anatomy, proportions and missing or invented parts. For the ghost:

- The first restored hit pose invented a sideways/backward recoil. A targeted correction restored the frontal,
  bowed head and gathered arms.
- The first dying pose put hands on the ground. A correction returned them to their suspended raised positions.
- The skull close-up clarified that the forehead, cheek and jaw surfaces should read as a largely intact skull.

Use narrowly scoped correction prompts: change the incorrect pose or detail while retaining the rest of the accepted
image. Repeated broad regeneration risks changing identity. Retain a clear selected-reference list so later agents
do not accidentally use a rejected sheet. The [restoration README and prompts](brown_ghost/reference_restoration/README.md)
show this process and distinguish interpretation from native evidence.

## 4. Model the whole character from those references

Use Blender through MCP for original geometry, sculpting, materials, rigging and review renders. The successful
ghost run used scripted Blender modeling and a cached skull sculpt; it did not use an automatic image-to-3D service.
Do not assume such a service is available or that image generation itself produces the rigged mesh.

First establish a neutral full-body model with cameras matching the reference views. Compare measurable ratios:
head to body height, shoulder and torso width, limb lengths, hand span, clothing volume and ground clearance.
Use neutral/material lighting as well as a presentation render. Strong lighting should not hide an unsuitable shape.

Build in this order, keeping the complete silhouette visible throughout:

1. Main masses and negative spaces: body, head, limb placement, openings and overall clothing silhouette.
2. Identity-defining anatomy and surfaces: face, skull, characteristic joints, hands and visible torso.
3. Clothing construction and coverage: how the hood meets shoulders, where sleeves end and which bones remain hidden.
4. Material character and secondary geometry: folds, wear, tears, teeth and other details visible at the target size.

Primitive shapes are useful starting volumes. They must become the appropriate surfaces. The early ghost had the
right component names but looked like a toy: facial rods and outlines did not make an intact skull. The improved
sculpt uses a connected cranial/maxillary/jaw shell around actual carved cavities, with separate small teeth.
See [the skull authoring script](brown_ghost/sculpt_skull_blender.py) and
[mesh cache](brown_ghost/sculpt/skull_mesh.json). This is a case-specific construction technique, not a requirement
to voxel-remesh every character or make every anatomical part one connected mesh.

Apply the same reference-driven attention to the entire model. Improving only the face leaves the body inconsistent.
In the accepted body revision, the important changes were:

- Continuous long robe folds and irregular pointed tears, replacing bulky stacked triangular panels.
- A narrower chest opening and partial occlusion of the ribcage, instead of exposing an oversized skeleton.
- Curved, flattened ribs around a sternum, tapered limb shafts, broader joints and paired forearm bones.
- Long jointed fingers hanging across the robe in the resting pose and opening into a fan during attack.
- Shoulder coverage that joins the hood and rises with the arms, plus some volume in the collapsed cloth.
- Hood sides that allow the skull to remain visible in profile.

These are findings about `m242`, not universal anatomy or costume rules. Follow the new creature's references.
When the driver accepts a component, preserve it while revising others. In this run the accepted skull's vertex
positions and faces were retained while tooth materials and the rest of the body changed.

## 5. Derive materials from the restored surfaces

Judge material identity separately from base color. A robe needs woven fiber, folds and fraying; broad cloud noise
alone can look like an unrelated material. Bones should share plausible aged color and roughness across the face,
torso and limbs, with dark cavities distinguished from enamel or exposed bone.

Two methods worked together for the ghost:

| Method | Application | Important constraint |
| --- | --- | --- |
| Reference-color projection | Restored frontal skull color projected onto real sculpted surfaces | Preserve projection UVs under animation and inspect oblique views for painted features conflicting with geometry |
| Material extraction/derivation | An AI-generated flat brown woven-fabric swatch based on the restored purple robe | Let geometry supply major folds and torn silhouettes; do not bake a whole garment silhouette into a repeating texture |

Projection is useful selectively. Projecting both front and profile skull images produced a duplicate painted socket
beside the real socket. The chosen treatment uses frontal reference color fading to neutral bone on sides/rear,
with the profile guiding geometry. Reference images contain lighting; this method is a stylized reference-color
treatment, not a physically neutral scanned albedo.

For a generated material swatch, specify the source material character, requested palette, flat even lighting and
absence of major folds, objects, borders or text. Save the prompt and texture. The ghost's
[cloth prompt](brown_ghost/reference_restoration/cloth_material_prompt.txt) is a concrete example. Its opaque dark
wear spots are surface color; actual openings near the hem are geometry.

Assign materials by part identity where possible. A spatial mouth-shadow rule accidentally included lower tooth
faces. Excluding tooth components from that rule corrected the blackened enamel. Similar mistakes can affect eyes,
claws, armor insets or overlapping pieces; inspect close views instead of compensating with stronger lights.

A later close-up still showed chalky procedural teeth, hands and ribs beside the restored skull. Matching a nominal
ivory color was insufficient. Sampling surface pigment from the same restored skull reference, reducing coarse bump
and sharing the surface response made the material treatment more consistent. Inspect adjacent parts under the same
lighting, and use surface-only sample regions to avoid projecting facial features onto limbs. Also measure garment
clearance: the hood initially left a large empty halo around the skull, even though its overall silhouette was closer
to the reference. Refine that fit in front and profile while preserving folds and space for the cloth to move.

Keep material UVs stable in the rest mesh. Animation must not cause grain or projected anatomy to slide across the
surface. Preserve source nodes and source UVs when creating an export atlas. Compare a close render before and after
baking: the ghost's initial 2048 atlas softened restored detail, so the final export used 4096 with tighter island
spacing. Choose resolution and UV allocation from the visible result, not a fixed rule that every model needs 4K.

## 6. Iterate quickly before packaging all animation

Use a small visual loop: render a representative view/pose, compare it to the matching reference, state the largest
mismatch, change that cause, then re-render the affected views. Record what was fixed and what remains uncertain.
Do not replace this judgment with a long list of successful technical tests.

During shape iteration, render the neutral front and side plus the pose most likely to expose the changed area.
After changing shoulders or hands, inspect the raised-arm pose. After changing cloth, inspect the rear silhouette
and collapse. Once the shape is stable, inspect the complete view set and full motion.

The example's [authoring script](brown_ghost/author_blender.py) supports a temporary single-pose preview:

```python
# Inside Blender, load the script into a module namespace without invoking its __main__ build.
module = {"__name__": "preview"}
exec(compile(script_path.read_text(), str(script_path), "exec"), module)
scene = module["build"](preview_only=True, preview_pose=("s", 0))
# Other useful ghost previews: ("a", .6) for raised attack; ("x", 0) for corpse.
```

Here `script_path` is a `pathlib.Path` to that example's `author_blender.py`. The preview replaces its named working
scene but does not overwrite the saved model or pose manifest. Save manual edits before procedural rebuilding.
Do not export a single-pose preview as the finished animated model. Use an equivalent fast path for future assets;
there is no need to rebuild every clip after each material or silhouette adjustment.

## 7. Rig and reconstruct the required motion

For in-game locomotion, prefer a reviewed compatible 3D gait where it produces better continuous motion; preserve
native identity and gameplay timing through the semantic binding. Exact native-motion or sprite-reconstruction
requests retain their requested source timing. Follow the [shared animation guidelines](CREATURE_3D_GUIDELINES.md)
for clip selection, root motion, action masks and named attachments.

Choose controls from the creature's anatomy and actions: body/root, head, limbs, hands, fingers, jaw or props where
needed, and clothing controls. Use sensible names and weight every intended deforming vertex. Verify normalized
weights and a usable manual posing workflow. Pure skeletal deformation may suffice; add corrective shapes when
specific clothing motion or extreme poses need them. Preserve vertex count/order and face topology when generating
corresponding shape keys procedurally.

Infer timing and pose transitions from the source inventory. Preserve attack anticipation/contact/recovery, hit
reaction, death ordering and held corpse behavior where applicable. Sparse source sprites define key poses; they do
not dictate the final 3D sampling rate. Raising FPS without adding intermediate motion simply changes playback speed.
For the ghost, 69 authored poses were sampled into seven clips at 24 fps with 218 timeline samples. Those counts
are an implementation choice. Loop seams, duration and readable action matter more than raw frame count.

Review actual playback and intermediate frames, not just exact source poses. Three rigging findings are particularly
important for agents generating bone transforms:

- **Scale inheritance:** compressing the body stretched child arms until scale inheritance and parent/rest-space
  conversion were handled explicitly. The ghost uses `inherit_scale='NONE'` and `convert_local_to_pose` with the
  correct parent matrices. Compare evaluated pose-bone matrices with intended targets before trusting corrective
  meshes calculated from those targets. This setting is appropriate to that rig, not a blanket rule for all rigs.
- **Rotation continuity:** a global Z-up tracking frame flipped bone roll near a vertical arm. Exact anchors looked
  right, but the interpolated sleeves flared into wings. Rest-relative bone swing, consistent quaternion signs and
  linear source sampling resolved it. The example contains a focused intermediate-surface regression check.
  Other rigs may need explicit twist controls; do not use interpolation to hide discontinuous bone frames.
- **Coordinate spaces:** world-up is not necessarily local bone Z. Ground-clearance corrections must convert the
  world displacement into the root bone's local coordinates. Verify the evaluated deformed mesh afterward, including
  the death transition and corpse, rather than checking only the object origin.

If skeletal motion and corrective shapes both contribute, package matching named clips for both. Keep their time
ranges synchronized in Blender and in the portable export. Document how to mute/reset both for manual posing.
Adding a bone animation while silently dropping the corrective weights changes the resulting motion.

## 8. Save checkpoints, export, and inspect the delivered asset

For FULL production, use the owned background launcher and project-local checkpoints from the skill. The GUI/MCP
recovery notes below describe interactive authoring; they do not authorize taking over a shared scene during FULL.

Use named scene ownership and preserve unrelated Blender scenes. Store scripts and source assets under the project;
save checkpoints after geometry/rig creation and after packaging clips, before a long render pass. During long MCP
jobs, schedule work through Blender's event loop and write progress/errors to disk. Wait for completion before sending
dependent commands. Do not infer that a temporarily busy renderer needs another Blender process.

Blender did close during one long review run. Recovery worked by checking that the GUI process was actually gone,
launching Blender with the saved checkpoint and verifying MCP again. The bridge process alone is not the GUI.
Follow the [startup procedure](../BLENDER_MCP_STARTUP.md); do not routinely disconnect or restart a working instance.
Switching the viewport to solid shading during batch authoring avoids unnecessary material-preview updates.

Export only the intended scene/objects. The ghost's GLB export needs both active-scene and selected-object filtering;
an unrelated default cube previously leaked into an export. Pack required textures and retain skin weights, clip
names and corrective targets. A Blender library written with `bpy.data.libraries.write` is not a normal startup
project: the example's background [normalization step](brown_ghost/normalize_blend.py) opens the isolated contents
and saves a normal `.blend`. That separate background process does not provide or replace interactive MCP.

Respect each stage's input state. The example's clip-packaging script expects the original source actions, not an
already packaged NLA timeline. Its atlas exporter expects source material colors and UVs. For another bake, restore
those source inputs or rebuild from the appropriate checkpoint; do not accumulate duplicate atlas UV layers or bake
an already baked atlas as though it were the source. Keep the new atlas connected to the intended UV set.

Review the exported appearance, not only the procedural source render. Texture baking or export can introduce blur,
UV mistakes, missing materials or changed deformation. Check the required consumer's skin/morph/material support
when integrating the model. The example's GLB structural checks do not establish an OpenYAMM runtime integration;
the brown ghost remains a standalone model asset.

Keep validation focused:

| Check | Required evidence |
| --- | --- |
| Visual identity | Equal-height native/restored/model comparisons; front, three-quarter, profile and rear |
| Important detail | Close views of face, material boundaries and any specifically corrected feature |
| Motion | Representative extremes, playback, loop seams and intermediate frames near risky transitions |
| Ground and framing | Evaluated deformed bounds; no unintended floor penetration or clipped review frames |
| Rig/export | Intended objects only, normalized weights, required bones/clips/targets, expected durations and packed textures |
| Delivered appearance | Close render using the baked materials; an inspectable normal `.blend` and portable export |

Run these at useful milestones. The ghost's final small review rendered all 218 samples, but full-sequence rendering
is not needed after every static edit. After a material-only change, check the new bake and export; after a deformation
fix, revisit the affected motion and final bounds. Use a focused test for an observed bug such as the bone-roll flip.
Do not run unrelated map scenarios, gameplay transactions or a broad engine build for an isolated art revision.

## Rendering back to directional sprites

When sprites are requested, render the accepted rig and materials in Blender. Keep AI restoration as the modeling
reference; independently generated bitmap poses would lose the rig's motion and directional consistency.
See the [brown ghost sprite export](brown_ghost/spritesheets/README.md) for a completed example and scripts.

Inspect the intended native sprite family and its frame-table flags before choosing directions, timing and filenames.
For m242, five views cover front through back; the other three directions mirror those views. Its original death,
corpse and fidget use one image direction. The example export additionally supplies those actions in five views;
using them requires updating the corresponding frame-table flags during integration.
Do not assume mirroring suits every creature: a weapon, shield or asymmetric costume may require genuine opposite-side
views. Match direction numbering against the native references and consumer, and document which views are mirrors.

Sample the existing animation duration rather than stretching it to an arbitrary frame rate. Ten frames per moving
clip is a useful first pass; use more for a fast attack or a changing collapse silhouette, and one held frame for a
static corpse. Respect the consumer's timing resolution. Omit duplicated loop endpoints, and include the endpoint
for a non-looping action. Record frame durations and source timeline positions in a manifest.
When the consumer uses integer timing units, distribute those units across frames while preserving the clip total,
then sample poses at the resulting times. Ensure every frame has a positive duration; the timing resolution limits
how many distinct frames a short action can play. Inspect anticipation, contact and recovery at the delivered timing.

The driver accepted the brown ghost sprite export with 10 frames each for standing, float, hit and fidget, 16 for
attack, 12 for death, and one held corpse frame. Its five rendered views produce 345 master images; adding the three
mirrors produces 552 PNG frames. These are a worked example, not fixed counts for future creatures.

Fit one orthographic camera to the evaluated bounds of all sampled poses and directions. Keep its scale, lighting
and ground pivot fixed throughout. Render transparent masters at twice the target resolution, then downsample with
premultiplied alpha to avoid dark outlines. Do not crop or resize each pose separately. Put frames in sheet columns
and directions in rows, with exact cell dimensions and no labels in usable sheets.
Render in an isolated copy of the accepted character scene, verifying that the copied mesh uses the copied rig.
Save the source checkpoint first and record its hash with the render settings, source times and output manifest.
Keep the render set tied to that revision. Restore the original active scene afterward so sprite-camera adjustments
do not disrupt the modeling workspace. Preserve masters so palette or sheet-layout changes only require repacking.

Keep transparent PNGs as well as any indexed output. For the m242-style BMP export, reserve palette index zero for
the native cyan key and train one shared opaque palette across all views and animations. Verify the mask after
writing the BMPs, along with unclipped bounds, file counts and total clip timing. Review an animation contact sheet,
direction strip and playback preview before delivery. New frame counts need new runtime table entries; staging
images alone does not install the actor or update its old animation groups.
Review at the actual sprite display size as well as enlarged: facial readability, finger separation, robe silhouette
and contrast can change after downsampling and palette reduction. Use a neutral background for labeled previews and
retain alpha in the usable sheets. Check the indexed version too; a good full-resolution render alone is insufficient.

## Handoff to the next agent

### Additional calibration from the MM6 goblin

The [goblin reconstruction](mm6_goblin/README.md) adds a grounded, asymmetric biped example. Its 88 bones, triangle
count and chosen texture sizes are case-specific. Transfer the procedure, not those numbers:

- Repeated AI walk restorations swapped the leading foot. After targeted attempts failed, the native contact sequence
  remained authoritative; explicit planted-foot targets solved the animation decision without more broad regeneration.
- Matched-camera AI refinements can supply coherent hand, torso and foot pigment. Project only the intended skin,
  combine geometry/facing masks with conservative color masks, and inspect another view. Keep armor/background pixels
  out of those projections. This complements actual anatomy; it does not replace modeled joints or negative spaces.
- Wrist steps, neck joins and stair-like armpits were geometry/weight problems. Fix connected surfaces and smoothly
  changing influences before trying to hide them with texture detail or stronger lighting.
- A planted hand needs both a direction and a palm normal. A shortest-arc aim leaves roll ambiguous. Check actual
  finger/claw bounds as the hand opens, and include toe-off and landing between the obvious walking contact poses.
- Dense checks belong around a demonstrated risk: nine walk phases missed a small toe penetration; denser sampling
  exposed it. Preserve subframe collapse keys when ordinary-frame interpolation changes ground clearance.
- Joining meshes changes Generated coordinates. Preserve source mapping explicitly. Boolean operand POINT attributes
  and decimated generic corner vectors did not always preserve the needed interpolation: reconstruct rest-space mapping
  for procedural pigment and retain true UV interpolation through reduction before freezing projection attributes.
  Render a close comparison after reduction; do not diagnose every blotch as insufficient texture resolution.
- Protect identity-defining geometry during reduction, and enforce the intended influence limit afterward. Reduction
  can combine neighboring four-weight vertices into more than four influences. Review the pruned deformation before
  allowing the exporter to make an undocumented choice.
- Freeze triangulation before tangent-normal baking and export. Bake base color through emission so metallic pigment
  is preserved. Inspect actual baked and reimported close-ups, not only a successful bake/export report.
- In the tested Blender 5.2 workflow, scene copies duplicated the active Action, and a rig copy/rename could leave its
  Action Slot unset. Bind the slot explicitly and verify the exported clip list. For unsampled FK export, explicitly
  normalize key times when the exporter does not honor its start-at-zero option; retain fractional keys and durations.
- Exclude importer-created bone widgets from geometry measurements. Blender's hidden unit icosphere caused a false
  floor-penetration result; disabling custom bone shapes during the import review left the actual asset unchanged.
- Genuine opposite views are needed for the goblin's right-hand weapon. A denser short attack/death sheet exceeds
  the native positive integer timing budget, so provide precise display timing and a separate legacy sample subset.
  Record pose sample times separately from display intervals when including both non-looping endpoints.

Keep these checks proportional to changes. A material fix needs a close bake/export comparison; it does not justify
rebuilding the rig or rerendering every animation before the corrected material has been accepted.

Keep an asset README with the brief, chosen palette, source inventory, selected reference versions, reproduction
steps, clip manifest, posing instructions, output paths, validation results and remaining limitations. Save visual
comparisons and a short correction log. Clearly distinguish native evidence, AI interpretation, current accepted
choices and earlier rejected approaches. Preserve accepted components and useful revision checkpoints.

For `m242`, start from these artifacts:

- [Final comparison](brown_ghost/review/body_comparison.png) and [animation preview](brown_ghost/review/animations.gif).
- [Selected AI references and exact prompt set](brown_ghost/reference_restoration/README.md).
- [Accepted directional sprite export](brown_ghost/spritesheets/README.md),
  [directional playback](brown_ghost/spritesheets/animations_directions.gif) and
  [animation contact sheet](brown_ghost/spritesheets/preview_front.png).
- [Case-specific calibration history](brown_ghost/ART_CALIBRATION.md); its later body findings supersede the earlier
  preference for bulky cloth panels and uniformly hooked resting fingers.
- [Editable model](brown_ghost/brown_ghost.blend), [portable GLB](brown_ghost/brown_ghost.glb) and
  [reproduction instructions](brown_ghost/README.md#files-and-reproduction).
- [Source pose manifest](brown_ghost/poses.json), [clip manifest](brown_ghost/animations.json),
  [authoring](brown_ghost/author_blender.py), [clip packaging/review](brown_ghost/finish_blender.py),
  [export](brown_ghost/export_blender.py) and [structural/visual review](brown_ghost/review_asset.py).

The accepted result is a useful reference for the process, not an assertion that every original detail or motion was
recovered exactly. For another creature, repeat the inspection and restoration stages before reusing construction
choices. The transferable lesson is to make the reference concrete, model all of its visible structure coherently,
and use targeted visual feedback throughout.


### Generated humanoids: grip and deformation gate

The [Meshy goblin production sequence](mm6_goblin/MESHY_PRODUCTION_FLOW.md) records a useful failure case.
The earlier sword/attack pass exported correctly but user review exposed a loose grasp, wrist reversal, bracer
warping and an unnatural free arm. Finish a neutral stance, weapon grip and representative arm extremes before
expanding the animation set. Inspect intermediate frames and multiple views; silhouette matching can hide broken
joints. Keep rigid armor weights stable, distribute skin twist, and ensure orientation bases and twist angles remain
continuous across the slash. Geometry contact checks complement visual review; neither attachment nor export parity
proves a convincing grasp. A generated mesh and automatic rig still require per-creature cleanup.

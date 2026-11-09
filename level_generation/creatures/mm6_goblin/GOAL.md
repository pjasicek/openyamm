# Goal: restore the MM6 goblin as an animated 3D character and directional sprites

## Objective

Reconstruct the MM6 `gob` sprite family as an original, textured, fully rigged 3D goblin with all required animations,
then render its directional animation sheets. First use AI image generation to restore selected original views and
action poses into coherent high-resolution modeling references. Build and iteratively refine the character in Blender
through Blender MCP against those references and the native sprites.

The quality target is a character that could appear in a polished, semi-AAA fantasy game without visibly looking like
a procedural placeholder. Preserve the recognizable MM6 goblin design while giving its anatomy, costume, surfaces
and movement convincing construction. Material techniques are at the agent's discretion. A technically valid rig,
an attractive frontal render, or a distant sprite alone does not satisfy the goal: the actual 3D asset must withstand
front, profile, rear, oblique, close-up and moving inspection.

This document is the brief for a future manually started `/goal`. Creating this document does not start generation.
Once invoked, carry the work through restoration, modeling, visual iteration, rigging, export and sprite delivery.

Live capability checks on 2026-09-08 passed for Blender launch/MCP, scene authoring, rigging, rendering, saving/export,
background reopening and built-in AI reference generation. See [the preflight report](preflight/README.md) for evidence
and current-state limits. Reuse the running GUI if it responds. The preflight image is a candidate requiring the normal
reference audit, not an already accepted design.

## Workflow and scope

Work in `/home/pjasicek/github/OpenYAMM`, following repository `AGENTS.md` and these guides:

- [Generic sprite-to-3D restoration workflow](../SPRITE_TO_3D_WORKFLOW.md): primary procedure and calibration lessons.
- [Blender MCP startup and recovery](../../BLENDER_MCP_STARTUP.md): inspect/reuse a running instance; start one if needed.
- [Brown ghost model and reproduction](../brown_ghost/README.md) and
  [art calibration](../brown_ghost/ART_CALIBRATION.md): worked examples of successful and rejected approaches.
- [Brown ghost sprite export](../brown_ghost/spritesheets/README.md): frame packaging, timing and transparency example.

Read the current imagegen skill when starting AI reference restoration and follow its input and generation rules.
Use actual AI regeneration from the source images, not simple interpolation presented as restored detail. Use Blender
MCP for model authoring, rigging and render review. Render final sprites from the finished animated model.

Keep all new work under `level_generation/creatures/mm6_goblin/`. Reuse useful repository tooling, adapting it to this
creature rather than cloning the ghost's anatomy, floating motion, bone count or material choices. Preserve the ghost
project, unrelated Blender scenes and the original game assets. Stage regenerated sprites here; installing the actor,
overwriting engine sprites, allocating live registry IDs and changing gameplay are outside this goal.

Proceed autonomously through reversible modeling, material, animation and review decisions; record assumptions and
continue without routine approval gates. Respect actual tool and filesystem permission boundaries. Do not assume a
previous Blender connection or approval proves current availability. Save checkpoints before long renders, report
progress to files, and avoid restarting a busy or working Blender instance.

## Source inventory: verified starting evidence

Sources, relative to the repository root:

- `assets_dev/engine/sprites/gob*.bmp`
- `assets_dev/engine/data_tables/monster_descriptors.txt`: merged IDs 550–552, `BGoblin A/B/C`.
- `assets_dev/engine/data_tables/bolster_monsters.txt`: Goblin, Goblin Shaman, Goblin King.
- `assets_dev/engine/rendering/sprite_frame_data_common.yml`: groups `gobata0`, `gobdya0`, `gobdyf0`,
  `gobfia`, `gobsta`, `gobwaa`, `gobwia0`, plus palette/scale variants beginning `gbb` and `gcb`.

The current checkout contains **59 goblin creature BMPs, each 355×289**. Exclude **`goblet.bmp`**: the broad glob also
matches that unrelated asset. Identify required textures from descriptors, not just a filename substring.
This is the MM6 goblin; do not substitute the MM7 `m246` texture family.

| Action | Native texture sequence | Stored images | Native group duration |
| --- | --- | ---: | --- |
| Standing | `gobsta0`–`gobsta4` | 5 views, one pose | Static pose; raw length 2 |
| Walking | `gobwa[a-f][0-4]` | 6 poses × 5 views | Raw length 12 |
| Attack | `gobat[a-f]0` | 6 front images | Raw length 12 |
| Hit | `gobwi[a-f]0` | 6 front images | Raw length 12 |
| Death | `gobdy[a-e]0` | 5 front images | Raw length 10 |
| Corpse | `gobdyf0` | 1 front image | Held pose; raw length 2 |
| Fidget | `gobfi[a-f]0` | 6 front images | Raw length 12 |

Standing/walking use `Mirror5/6/7`; the other actions use `Image1`. The descriptor binds both attack slots to the same
attack group. Variants reuse the same texture family with different palette/scale settings; one reconstructed base
character is required, not three independently designed goblins. Preserve material-region masks so palette variants
can be made later. Audit the variants for reference color interpretation, but a three-variant export is not required.

Recheck these facts when execution starts. Record ordered frames, palettes, transparency, scale, anchors, directions
and timing in a source manifest. Do not transfer the ghost's 256×256 canvas or `Center` flag without inspection.
The current legacy timing conversion is raw length × 8 ticks at 128 ticks/s: raw 12 is 0.75 s and raw 10 is 0.625 s.

## Stage 1: native reference inspection and AI restoration

1. Assemble contact sheets of all native creature frames and native playback previews. Inspect standing/walking in
   front, three-quarter, profile and rear. Identify the attack's anticipation, strike and recovery, hit reaction,
   fidget, death progression and final resting pose. Compare proportions with common ground alignment and aspect ratio.
2. Write a brief visual inventory: head/face, ears, torso, limbs, hands, feet, clothing, equipment and visible materials.
   Establish what the pixels actually show before specifying anatomy or props. Mark ambiguous or occluded details.
3. Generate high-resolution, mutually consistent reference views using the original sprites as image inputs. Include
   neutral front, three-quarter, profile and back; representative walk contacts and attack extremes; hit, death and
   corpse poses; and close references for the face and any unclear hands/equipment or costume construction.
4. Preserve native identity, palette relationships, proportions, pose and clothing coverage during restoration.
   Material detail may be clarified, but do not invent an unrelated generic goblin, new armor or accessories. Infer
   missing action-side views conservatively from the neutral turnaround and native frontal motion.
5. Inspect every selected restoration against its native input. Correct inconsistent face shapes, swapped equipment
   sides, altered limb directions, invented details and pose drift with targeted edits. Save exact prompts, input
   filenames, selected outputs and the reasons for selecting or rejecting them under `reference_restoration/`.

Do not regenerate every low-resolution frame independently. Establish one coherent character and a useful set of
action references. AI restorations are reviewed interpretations, not proof of the lost original high-resolution art.

## Stage 2: model, surface and visual refinement

Establish matching reference cameras, a neutral studio and a full-body blockout. Measure head/body ratio, shoulder
width, limb lengths, hand/foot sizes, silhouette and clothing/equipment fit. Build the actual forms visible from all
sides; primitive volumes are intermediate construction, not a finished face, hand or joint.

Develop face, body, hands, feet, costume and any source-supported equipment to a consistent finish. Model meaningful
openings, thickness, overlapping pieces and attachment points. Skin and facial detail must read coherently beside the
hands and limbs. Distinguish skin, cloth, leather, metal or other observed materials through appropriate surface
response, not arbitrary noisy colors. Preserve the native visual character; avoid toy-like rounding and generic
fantasy redesign unless those shapes are actually supported by the references.

Use sculpting, original mesh modeling, UV textures, generated material swatches and procedural materials as appropriate.
Choose geometry and texture resolution from the intended visible quality. Supply a deformable, practical game mesh
and baked/exportable materials, retaining a sculpt/source version when useful. Avoid relying on a dense sculpt alone
as the deliverable. Record triangle count, material count and texture memory; no arbitrary polygon ceiling is imposed.
If reference color is projected, inspect sides and motion for duplicated painted features, lighting baked into the
wrong places or sliding textures. Inspect the baked material result as carefully as the Blender source shading.

At each milestone, render front/profile/rear and oblique views plus useful close-ups. Compare native → selected
restoration → current model at consistent scale. Record the most visible mismatches in `ART_CALIBRATION.md`, fix their
causes, and re-render affected views. Keep accepted components stable when correcting another part.

Do not stop after the first technically complete pass. Continue targeted iteration until the visual criteria below
are met. Do not manufacture extra revisions when an area already meets them. Assess in neutral lighting and normal
perspective as well as the orthographic sprite camera; dramatic lighting and tiny previews must not conceal defects.

## Stage 3: rig and animation

Create a named, editable armature with controls appropriate to a grounded biped and its observed equipment. Include
body/root, pelvis/spine, head, arms/hands/fingers and legs/feet as needed. Use controlled attachments and appropriate
clothing deformation; add corrective shapes where they solve observed problems. All deforming vertices need sensible,
normalized weights. Document how to pose the model and disable animation/correctives for manual editing.

Deliver named clips for **Standing, Walk, Attack, Hit, Death, Corpse and Fidget**. Standing may become a restrained
breathing/weight-shift loop; it must retain the original stance. Walk must have readable weight transfer, planted
contacts and appropriate stride. Supply an in-place walk with documented intended movement speed/stride; avoid foot
sliding when evaluated at that speed. Keep any root-motion version separately named and documented if supplied.

Preserve the source actions' intent and order. Animate anticipation, strike and recovery with convincing body weight,
and distinguish hit reaction from fidget. Death must settle into the same pose held by Corpse. Animate real intermediate
motion; increased FPS or duplicated frames alone is not improvement. Author continuous animation at 24 or 30 fps,
preserving source action durations by default and documenting any deliberate retiming for readability.

Review playback and risky intermediate poses from several directions: shoulders, elbows, wrists, hips, knees,
equipment grips, cloth intersections, foot contacts, death/ground contact and loop seams. Apply the generic workflow's
lessons about bone rest space, scale inheritance, quaternion continuity and coordinated corrective animation where
relevant. Do not impose the ghost's exact rig settings on this biped without need.

## Stage 4: model export and sprite production

Save an ordinary, reopenable `mm6_goblin.blend` with packed dependencies, usable rig, named clips and review cameras.
Export `mm6_goblin.glb` with intended objects only, skinning, materials/textures and all required animation components.
Inspect the exported asset's appearance and motion, including any baked corrective shapes. Record any actual consumer
limitations explicitly; a structurally valid GLB alone does not establish visual parity.

Then render all actions into directional sprites from the accepted model:

- Target roughly **10 frames** for standing/walk/hit/fidget, **16 for attack**, **12 for death**, and **one held corpse**.
  Adjust sampling when needed to preserve important poses. Keep continuous model animation independent of sheet count.
- Supply an eight-direction RGBA sheet per action. Render genuine opposite-side views when equipment or anatomy is
  asymmetric; use five renders plus mirrors only when visual inspection justifies it. Record this decision and the
  exact view mapping. New views of originally front-only actions must remain consistent with the full 3D character.
- Preserve one scale, camera, lighting setup and ground pivot across every pose and direction. Fit evaluated bounds
  over the whole set, leaving margin for equipment and death. Use transparent masters at least twice the delivery
  resolution, premultiplied-alpha downsampling, and fixed cells with frames in columns and directions in rows.
- Supply individual transparent PNGs, usable unlabeled sheets, indexed BMP frames with a shared palette, and separate
  labeled contact sheets/GIF or video playback. Preserve masters for repacking without rerendering.
- Use the audited native 355×289 canvas for the native-size set unless there is a documented reason to change it.
  Record pivot, visible height and world-scale considerations; do not stretch the character to fill the canvas.

**Resolve timing constraints explicitly.** A 0.75-second legacy action has only 12 positive raw timing units, so a
16-frame attack cannot retain that duration in the current legacy table format. Deliver the full-quality sheet with
precise timing, and a separately identified legacy-compatible sample selection/timing manifest with at most one frame
per raw unit (or explicitly document a chosen retiming). Do the same for the 12-frame death target versus 10 native raw
units. Never write zero-length frames, silently slow an action, or claim the denser sheet is a drop-in native group.

Verify BMP transparency against the audited native key/index convention, palette consistency, nonempty unclipped
frames, direction order, fixed alignment and total animation timing. Review both PNG and palette-reduced output at
actual display size. Stage a separate sprite prefix and record how future frame groups would reference it; do not
allocate live IDs or overwrite `gob` files. Provide a ZIP containing sprites, palettes, timing manifests and usage docs.

## Completion criteria and evidence

The goal is complete only when all of the following are delivered and reviewed:

| Criterion | Required evidence |
| --- | --- |
| Identity and proportions | Native/restored/model comparisons in front, profile, rear and oblique views |
| Model finish | Face, hands/feet, garment/equipment close-ups; no obvious primitive assembly, holes or floating attachments |
| Materials | Coherent related surfaces, intentional material differences, usable UVs and matching exported appearance |
| Deformation and motion | All seven named clips, playback, clean joints, stable grips/contacts and reviewed transitions |
| Practical editable asset | Reopenable `.blend`, working rig, documented posing/reset, packed dependencies and portable GLB |
| Sprite quality | Directional sheets, individual PNG/BMP frames, stable scale/pivot, no clipping or transparency artifacts |
| Timing | Full-quality and legacy-compatible timing clearly distinguished; no zero-length frames or silent duration changes |
| Reproducibility | Source inventory, selected AI references/prompts, authoring/export scripts, manifests and checkpoints |
| Handoff | README with paths and viewing/rebuild instructions, correction history, concise validation and honest limitations |

Keep an updated progress checklist in this directory during execution, recording completed stages and the next concrete
action. Save review evidence under `review/`, source textures under `textures/`, and rendered outputs under
`spritesheets/`. Update the generic workflow with any transferable new findings at the end, without turning goblin-specific
choices into universal rules. Finish with links to the editable model, portable export, visual comparisons, animation
previews and sprite ZIP.

Prioritize visual review and focused asset checks. No unrelated engine build or map scenario suite is required.
The semi-AAA target requires honest artistic judgment backed by views and playback, not a self-assigned quality score.
Do not mark the goal complete with conspicuous unfinished areas or substitute a statement of intended quality for the
actual artifacts. If a required tool is unavailable or a concrete limitation remains, record it accurately.

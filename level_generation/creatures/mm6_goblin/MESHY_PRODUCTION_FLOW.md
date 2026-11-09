# Meshy to MM6 creature production

## Decision for this pilot

Finish one goblin for **rendered billboards first**. Preserve the editable 3D asset for a possible later runtime
model. The generated appearance is a useful starting point; the automatic rig and generic actions require
creature-specific finishing. The current [arm revision](meshy_sword_attack/rig_revision/README.md) is a checkpoint,
not production acceptance.

A billboard source can be dense, but it still needs convincing deformation in every delivered view. For direct
3D use, add runtime budgets, topology/LOD and texture decisions, supported skinning/material checks and engine
integration. Triangle count alone says little about either quality or animation reliability.

## Sequence and acceptance gates

| Stage | Work | Evidence before proceeding |
| --- | --- | --- |
| 1. Appearance | Compare native sprites, restored reference and generated model; settle proportions, face, costume and weapon | Equal-height front/profile/back comparison; reject major identity errors before rig work |
| 2. Rig and grip | Place joints; inspect topology; fit a clenched fist; attach the weapon; separate rigid armor behavior from skin deformation | Neutral stance, raised/cross-body/extended arms and pronation/supination; front/profile/elevated close-ups; no wrist reversal, floating grip or torn bracers |
| 3. One complete attack | Block original anticipation, strike, follow-through and recovery; coordinate torso, shoulders, elbows and free hand | Original/model pose comparison plus continuous playback; physical joint motion, stable contacts and useful silhouette at game size |
| 4. Remaining actions | Adapt idle, walk/run, hit and death; reuse approved grip and rig; author transitions | Review each action with the actual weapon; loop seams, entry/recovery, feet, ground and body contacts |
| 5. Billboard pilot | Render a short representative sequence from required directions with fixed scale, light and ground pivot | Actual target-size preview, readable face/weapon, timing and alpha/placement checks; no asymmetric weapon mirroring mistakes |
| 6. Production export | Batch all approved frames and directions; export metadata and portable 3D source | Reimport final files, compare poses/materials, check counts/durations; integrate and inspect in-game when that scope is requested |

Do not expand the animation set while stage 2 or 3 still fails. A visually attractive standing model does not pass
stage 2 by itself. Matching six front silhouettes does not pass stage 3 if the joints break between them.
A successful GLB export only proves that the authored result survived packaging.

## Next concrete work on this goblin

1. Sculpt a genuinely clenched right hand around the chosen handle, especially the thumb and fist volume. A fixed
   grip shape is enough for a permanently armed billboard character. Add finger controls if opening/changing grip
   is needed; the current Meshy rig has no separate finger chains.
2. Finish the complete attack gesture with the revised wrist/forearm behavior: shoulder and elbow arcs, free-hand
   counterbalance, torso/weight shift and smooth entry/recovery. Preserve native timing and attack intention.
3. Review that stance/attack at intended billboard size and at the required camera angles. Only then use the rig
   as the foundation for the remaining clips.

## Cost and repeatability

No more paid Meshy generations are indicated by the reported arm faults. Those are mesh/rig/pose problems in an
already useful model, including mistakes introduced by the earlier custom animation. More random motion presets
would not verify or repair them.

This pilot establishes tools and an acceptance standard. Rendering, naming, timing, export checks, weapon attachment
and parts of the pose setup are reusable. Generated anatomy, joint positions, armor connections, skin weights and
hand geometry will vary between creatures and need individual inspection. Do not promise unattended conversion or
an exact per-creature effort until the pilot has passed and a second creature has exercised the process.

Production billboards are a reasonable objective, with planned asset cleanup and animation work. If correcting a
part is repeatedly harder than replacing it, remodel that part or manually retopologize its deformation region.
For direct 3D use, close-up scrutiny and runtime constraints can justify more extensive topology and rig work.

Use [Sprite-to-3D Workflow](../SPRITE_TO_3D_WORKFLOW.md) for the shared authoring, export and sprite-capture contract.

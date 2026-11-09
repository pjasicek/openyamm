# AI-restored m242 modeling references

Generated with the **built-in image generation tool** using the imagegen skill. Original game BMPs were converted
losslessly to PNG only because the image tools cannot read these BMPs. The `inputs/` PNGs are not the restoration.
The larger sheets below are AI-generated interpretations of those source sprites.

## Selected references

| File | Size | Native inputs / purpose |
| --- | --- | --- |
| [standing_views_v1.png](standing_views_v1.png) | 1392×1130 | `sa0`, `sa1`, `sa2`, `sa4`: front, three-quarter, profile, back |
| [skull_detail_v1.png](skull_detail_v1.png) | 1402×1122 | `sa0`, `sa2` and restored standing sheet: intact skull/hood detail |
| [action_poses_v2.png](action_poses_v2.png) | 1536×1024 | `ad0`, `wa0`, `na0`: raised attack, compressed floating, bowed hit |
| [death_fidget_v2.png](death_fidget_v2.png) | 1774×887 | `da0`, `xa0`, `fd0`: sinking head/robe, corpse, arms-out fidget |
| [brown_shroud_weave_v1.png](brown_shroud_weave_v1.png) | 1254×1254 | Restored standing/hood fabric character adapted into an opaque brown woven-cloth texture |

These cover the distinctive viewing directions and animation key poses; they are not a frame-by-frame restoration
of all 124 original sprite images. Original silhouettes, anatomy and pose ordering remain authoritative where the AI
fills in ambiguous pixels. In particular, teeth, small cloth holes and fine bone surface detail are interpretations.

The original magenta/violet material is retained in these references. The generated 3D character keeps its requested
brown cloth palette.

## Review and corrections

The standing and skull detail sheets establish a continuous cranium, forehead, cheek/maxillary surfaces and mandible
around actual cavities. This addresses the previous model's appearance of facial outlines assembled from rods.

The first action sheet invented a backward, sideways recoil. `action_poses_v2.png` corrects it to the native frontal,
bowed, gathered-arm pose. The first death/fidget sheet put the dying hands on the ground; `death_fidget_v2.png` restores
the upward suspended hands. The earlier sheets remain for audit but are not the selected pose references.

## Prompt set

- [Standing restoration prompt](prompts.md)
- [Action restoration](action_initial_prompt.txt) and [targeted pose correction](action_correction_prompt.txt)
- [Death/fidget restoration](death_initial_prompt.txt) and [hand-pose correction](death_correction_prompt.txt)
- [Skull detail restoration](skull_detail_prompt.txt)
- [Brown cloth material prompt](cloth_material_prompt.txt)

No CLI/API fallback or third-party 3D generator was used. The 3D adaptation is authored with Blender MCP.

## Adaptation to the 3D model

`../sculpt_skull_blender.py` creates a continuous cranial/maxillary envelope, joins the mandible masses, carves actual
orbital/nasal cavities, and adds normal small teeth. `../sculpt/skull_mesh.json` stores that sculpt's mesh for rig
regeneration. The skull replaces the old facial rods rather than covering them with a picture.

The restored frontal skull color is projected onto the carved face using stored UV coordinates; side/rear surfaces
fade to neutral bone to avoid duplicating the photographed profile socket next to the actual geometric socket.
The profile image guides depth and silhouette. This reference-color projection includes shading from the generated
image; it is a prerendered-game-style texture treatment, not a physically neutral scanned albedo.

The body is modeled against the standing and action sheets: a continuous long-folded shroud, a narrow chest opening,
curved ribs, a flattened sternum, two tapered forearm bones and long jointed fingers. The brown texture supplies woven
fiber wear; folds and ragged silhouette remain three-dimensional geometry. Small dark wear spots in the opaque swatch
are surface color, while actual openings near hems are mesh holes. Bone color is calibrated to the skull's aged ivory;
enamel is excluded from cavity shadows. Its 32-bone rig, seven 24-fps clips, and synchronized cloth correctives remain.

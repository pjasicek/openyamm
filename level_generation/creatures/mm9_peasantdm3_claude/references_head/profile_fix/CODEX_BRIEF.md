# Codex brief: ONE corrective regeneration of the PROFILE head view, PeasantDM3 (mm9_peasantdm3_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdm3_claude/references_head/profile_fix/`.
Do not edit any other file, no builds, no Meshy. Use your built-in image generation tool.

The selected `references_head/02_profile.png` (input 3) is the right dwarf but does NOT fit the 3D mesh: input 4 shows it
with the mesh outline drawn in RED. The beard hangs about 75 px too low (the mesh's beard ends in a point at the red
outline, roughly at the level of the tunic collar's front), and the forehead, nose, lips and beard front stick out about
20-30 px to the LEFT of the red outline. This image is projected onto the mesh, so the outline must match.

## Inputs (attached, in order)
1. `references_head/silhouette/sil_left_white.png` — the mesh in this exact camera (90-degree profile, face to IMAGE LEFT):
   the OUTLINE AUTHORITY. Every contour (forehead, brow, nose tip, lips, beard front, beard tip, hair, back of the hair,
   shoulders) must land exactly on this grey shape.
2. `references_head/01_front.png` — the selected front view: identity, colours, hair and beard style.
3. `references_head/02_profile.png` — the current profile: identity and style to keep (hair, skin, beard texture, light).
4. `references_head/profile_fix_input_overlay.png` — input 3 with the mesh outline in red: what is wrong.

## Deliverable
`profile_fix/02_profile.png`: 1254x1254, true transparent background, the same dwarf as inputs 2-3 in pure left profile,
painted exactly inside input 1's grey silhouette: the beard SHORTER, ending at the silhouette's beard tip; the face moved
right onto the silhouette's face line. Calm, warm expression, mouth closed, one nose, no beads or ties, ears covered by
hair. Keep raw returns in `profile_fix/raw/`; at most TWO attempts; select the one whose outline matches input 1 best and
write `profile_fix/generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason).

# Codex brief: two flat texture swatches for the MM9 Banshee (mm9_banshee_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_banshee_claude/references_swatch/`. Do not edit any other file, do not run builds, do not call Meshy.

These are FLAT TEXTURE IMAGES mapped directly onto game geometry, seen straight on, filling the whole frame edge to edge: not pictures of an object, no background, no perspective, no vignette, no text, no shadows falling across, opaque.

## 1. `cloth.png` (1536x1024 landscape)
Input: `references_swatch/mm9_cloth_patch_x7.png`, the original game texture of her grave-cloak, enlarged. Faithful high-definition restoration of that fabric: a worn mauve-brown shroud of fine linen gauze with long soft darker streaks and folds
running from the TOP edge straight down to the BOTTOM edge of the image, as in the input, pale dusty pink-beige between the dark streaks, near-black shadow in the deepest streaks. Fine woven thread visible at close range, slight fraying. Same hues and same contrast as the input.
The streaks fan slightly outward toward the bottom. The bottom fifth of the image darkens to a charred grey-brown. No holes, no torn edges (those are made separately), no pattern repeats, no figures, no ornaments. It must fill the image entirely.

## 2. `hair.png` (1024x1024 square)
Inputs: `references_swatch/mm9_hair_E_x10.png`, `references_swatch/mm9_hair_A_x10.png` (top area of each: her hair, the first bleached and streaked, the second red-brown). A flat image of long stiff hair strands, all strictly VERTICAL, running from the bottom edge (roots) to the top edge (tips), packed side by side with no gaps,
high contrast between bright and dark strands, as in input 1, in pale straw and ivory with brown and dark umber streaks between them. The very top tenth of the image darkens to near black (the tips are burnt). Fill the whole frame edge to edge. Monochrome-ish, low saturation: it is recoloured per tier in the engine, so the brightness pattern is what matters.

Keep raw returns under `references_swatch/raw/`. One corrective regeneration each at most. Write `generation_runs.json` (prompt, inputs with sha256, output, selected).

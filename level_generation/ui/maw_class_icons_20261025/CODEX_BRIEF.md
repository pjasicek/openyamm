# Codex brief: MAW class icons

## Scope

- Image generation with your built-in image generation tool, plus Python (PIL) only to crop, resize and check your
  own outputs.
- Write only into `level_generation/ui/maw_class_icons_20261025/`. Do not change existing masters or records.
- No builds, no code changes, no other files touched.

## Inputs

**Attached image 1** (`refs_class_icons.png`): the sixteen existing class icons of the game's character creation
screen (bow, ankh, dark elf head, dragon head, tree, sword, bull head, yin-yang, skull, blue shield, book, boots,
compass star, dagger, club, bat), shown on a grey card only for viewing. **Match this icon style**: one realistic
painted emblem object, lit softly from the top left, rich but not glossy, crisp edges, no outline, no frame, no
background, no ground shadow. The new icons must look like members of the same set and be told apart from these
sixteen and from each other at 34 px and at 20 px.

## What to make

`classes.json` lists the new character classes (the four MAW class lines, then the Peasant): `class`, `file`,
`identity` (what the class is) and `subject` (the emblem to paint). The prompt names the list positions to do in this
run; do those, one image generation each.

- The existing set was made with this common prompt; use it as the base of every prompt, then the `subject`:
  "Create a SINGLE simple transparent class icon for the Carved Obsidian fantasy RPG UI. Follow the clarity of
  original Might and Magic VI/VII party creation icons: one immediately recognizable object or symbol, one strong
  clean silhouette. Smooth hand-painted inventory-art shading, lightly worn antique brass, muted silver/ivory,
  restrained natural colors where appropriate. Broad simple shapes and minimal surface detail; clearly readable at
  40-50 screen pixels on dark green-black stone. Soft even highlights from upper left. Center the COMPLETE object
  within a square canvas, occupying about 78% of its longest dimension with empty transparent margin on all sides.
  TRUE transparent alpha background, including inside holes. Absolutely no heraldry, coat of arms, backing plaque,
  ornamental badge, surrounding medallion, filigree, wreath, crown, extra equipment, lettering, labels, border,
  scene, glow, or floor shadow. Only the requested object, nothing behind it. No photorealistic microtexture, no
  cartoon emoji, no pixel art."
- Paint the `subject` as one emblem object, about as wide as tall, centred, filling most of the canvas.
- Its silhouette and main colours must read at 20 px: few large shapes, strong value contrast, no fine clutter.
- **No text, letters, numbers or logos.** Runes, if any, are abstract cut shapes.

## Output

- Ask the image tool for a **transparent background** and keep its alpha.
- Crop to the object with about 8 px of transparent margin, pad to a square (centred, transparent), and scale with
  high-quality resampling to 512 x 512.
- Save `masters/<file>` (RGBA PNG); every raw generation as `raw/<file stem>_<n>.png`.
- Records: write `raw/runs_<file stem>.json` (a JSON list), one record per generated image: `class`, `file` (the
  raw path, `raw/…`), `prompt`, `selected`, `reason`.
- Check each result: one emblem, readable at 20 px, no text, a transparent background with clean edges, the style of
  the reference set. Retry at most once with one targeted correction if a check fails.
- Skip any class whose master already exists, so a rerun resumes.

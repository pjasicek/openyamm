# Codex brief: solo talent icons (MAW talent tree v2)

## Scope

- Image generation with your built-in image generation tool, plus Python (PIL) only to crop, resize and check your
  own outputs.
- Write only into `level_generation/ui/solo_talent_icons_20261114/` (`raw/` and `masters/`). Do not change other
  workers' files, existing masters or records.
- No builds, no code changes, no other files touched. No git commands.

## Inputs

**Attached image 1** (`refs_spell_icons.png`): twelve of the game's own spell icons (Might and Magic VI-VIII
spellbook art: a meteor, winged boots, white wings, a knight's helm, crossed swords, a fist, a clover, a frost star,
an eye, falling stars, a cross medal, a turtle) on the dark page colour. **Ignore the small green and red glyphs
beside them**; they are spellbook labels, not part of the style. **Match this painting style**: one hand-painted
subject in rich, slightly gritty traditional illustration, warm and saturated, lit from the upper left, crisp
readable shapes, a soft painterly glow or speed streaks around the subject where it helps, no outline, no frame.

## What to make

`icons.json` lists the talents of the game's solo run: `id`, `name`, `tree`, `effect` (what the talent does, for
your understanding only), `palette` (the tree's colour identity) and `subject` (what to paint). The prompt names the
list positions to do in this run; do those, one image generation each (plus at most one retry, see Checks).

The icons are **abilities** on an action bar beside the spell icons above, and on a Talents page, drawn at about
40 x 40 screen pixels on a very dark blue-green stone (#151b1c). Each must read at 32-40 px.

Base every prompt on this, then add the `palette` and the `subject`:

"Create ONE square fantasy RPG ability icon in the hand-painted style of the Might and Magic VI/VII/VIII spellbook
spell icons (see the attached reference; ignore its small rune glyphs). One single clear subject with a strong bold
silhouette and strong value contrast, a bright lit subject against nothing, readable at 32-40 screen pixels. Rich
traditional painted illustration, warm saturated colours, light from the upper left, crisp edges, broad shapes and
only a little surface detail. The subject (with its glow, sparks or motion streaks) fills most of the square canvas,
centred, about 85% of the canvas on its longer side, with a small empty margin on all sides. TRUE transparent
alpha background around the subject and its glow. Absolutely no text, letters, numbers, runes that look like
letters, logos, frame, border, badge, plaque, medallion backing, scene background or floor. No photorealism, no
cartoon or emoji look, no pixel art, no 3D render look."

- The tree colour identity must be clear at a glance (a row of one tree's icons should read as that tree), but the
  subject keeps its natural colours (wood stays wood, steel stays steel).
- Each icon must be told apart from the others in `icons.json` and from the reference spell icons by silhouette,
  not only colour.

## Output

- Ask the image tool for a **transparent background** and keep its alpha (soft glows may be semi-transparent).
- Crop to the visible subject (alpha > 16) with about 12 px of transparent margin, pad to a square (centred,
  transparent), and scale with high-quality resampling to 512 x 512.
- Save `masters/<id>.png` (RGBA PNG); every raw generation as `raw/<id>_<n>.png` (n = 1, 2).
- Records: write `raw/runs_<id>.json` (a JSON list), one record per generated image: `id`, `file` (the raw path,
  `raw/...`), `prompt`, `selected`, `reason`.

## Checks

- Look at each result downscaled to 40 x 40 and 32 x 32 on #151b1c. It must show one subject, read at that size, have
  no text or letters, a real transparent background (not a painted checkerboard, not a solid fill), and match the
  reference style.
- If a check fails, retry at most once with one targeted correction, then keep the better one.
- Skip any id whose master already exists, so a rerun resumes.
- In your final message, list each id with the chosen file and one line on how it reads at 40 px.

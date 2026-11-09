# Codex brief: MAW boss badges

## Scope

- Image generation with your built-in image generation tool, plus Python (PIL) only to crop, resize and check your
  own outputs.
- Write only into `level_generation/ui/maw_boss_badges_20261024/`. Do not change existing masters or records.
- No builds, no code changes, no other files touched.

## Inputs

**Attached image 1** (`refs_obsidian_hud.png`): the game's "Obsidian" HUD art: from the left a round personal-buff
medallion (polished gold rim with four small gold points, a dark blue-black obsidian disc with faint veining, a
bright emblem in the middle), two diamond markers and a carved stone skull. **Match the medallion's style**: painted,
lit softly from the top left, crisp edges, no outline, no background, no cast shadow.

## What to make

`items.json` lists 15 small badges that float beside a monster's health bar in a fantasy role-playing game: `key`,
`file`, `name`, `master_box_px` and `emblem`. The prompt names the list positions to do in this run; do those, one
image generation each.

- Every badge is the **same round medallion**: a polished gold rim and a dark obsidian disc, as in the reference
  but **without the four gold points** and slightly thicker rim, so the badges read as one set. Only the emblem in
  the disc changes.
- The emblem follows `emblem`. Make it **bold and simple**: one large shape that fills about 70 % of the disc, strong
  colour against the dark disc, readable when the whole badge is drawn 16 pixels wide. No fine detail that would
  turn to noise at that size.
- Position 1 (the boss skull) uses a **dark red rim tint over the gold** so it stands out as the main boss mark.
- **No text, letters, numbers or logos.** Runes are abstract cut shapes.

## Output

- Ask the image tool for a **transparent background** and keep its alpha.
- Crop to the medallion with about 6 px of transparent margin, then scale (keeping the aspect ratio, high-quality
  resampling) to fit inside `master_box_px`. Do not pad to the box.
- Save `masters/<file>` (RGBA PNG); every raw generation as `raw/<file stem>_<n>.png`.
- Records: write `raw/runs_<file stem>.json` (a JSON list), one record per generated image: `key`, `file` (the raw
  path, `raw/…`), `prompt`, `selected`, `reason`.
- Check each result: a round medallion, the emblem readable when shrunk to 16 px (check a 16 px downscale), no text,
  a transparent background with clean edges. Retry at most once with one targeted correction if a check fails.
- Skip any item whose master already exists, so a rerun resumes.

# Codex brief: HD sky masters (pilot)

## Scope

Image generation only. Write files only into `level_generation/lighting/sky_art/hd_skies/pilot`. Do not build, run the game, edit code or touch any other
folder. Use your built-in image generation tool. The attached images are the inputs listed per sky, in order.

## What these are

Each input is an original sky texture from Might and Magic 6–8 (1990s, 8-bit palette, dithered, 256–512 px). The game
tiles it across a curved sky plane, so each texel is magnified many times and the original looks pixelated and smeared.
Produce an **HD repaint of each input**: the same picture at high resolution with clean painterly detail.

## Rules for every sky

- **Faithful**: keep the input's exact composition. Every cloud keeps its position, size, shape and direction of
  flow; the colours, palette, lighting direction and mood stay the same. This is a restoration, not a new picture:
  no new clouds, no removed clouds, no change of weather or time of day.
- **Detail**: replace dithering, palette banding and blocky pixels with smooth painted gradients and fine cloud
  structure (soft wisps, billows, subtle internal shading), in the hand-painted style of the original.
- **Tiling**: the input tiles seamlessly (its left edge continues into its right edge, top into bottom). Keep that:
  clouds that leave one edge must continue on the opposite edge, exactly as in the input.
- **Size**: square, the largest size your tool produces (2048 × 2048 if possible, at least 1024 × 1024). Do not add
  borders or margins; the picture fills the whole canvas edge to edge, like the input.
- **Do not add**: sun, moon, stars, rays, lens flare, horizon, ground, mountains, birds, buildings, text, logos,
  frames, vignettes or watermarks. No photographic look.

## Skies

### `sky06`

- Input: `inputs/sky06.png` (512 × 512, from `assets_dev/worlds/mm8/textures/sky06.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#3d5994** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #9b8e9e, #797990, #5c678b, #495f91, #3d5994.
- Save as `sky06_hd.png`.

### `sunsetclouds`

- Input: `inputs/sunsetclouds.png` (512 × 512, from `assets_dev/worlds/mm9/textures/sunsetclouds.bmp`).
- **Fully painted sky**: clouds cover the whole tile. Keep every area painted; there is no open sky to flatten.
- Main colours of the original, brightest first: #904a44, #714140, #554045, #5c3a3b, #48353a.
- Save as `sunsetclouds_hd.png`.

## Per-image checks (run before selecting)

1. Square canvas of at least 1024 px, picture fills it edge to edge.
2. Side by side with the input: same cloud layout and colours; nothing added or removed.
3. Open-sky inputs: the gaps between clouds are one flat colour (sample a few gap pixels; they must match).
4. Tile the result 2 × 2 (for example with Python/PIL into a scratch file in this folder) and check that the edges
   continue without a visible seam or cut-off cloud.
5. None of the "Do not add" items appear.

Regenerate a failed image with one targeted correction (at most three attempts per sky). Keep rejected attempts as
`<name>_hd_try<N>.png`.

## Records

Write `generation_runs.json` listing every attempt: sky, file, prompt, selected flag and reason. Write
`selected_review.png`: each selected master beside its input (input scaled to the same size with nearest-neighbour).

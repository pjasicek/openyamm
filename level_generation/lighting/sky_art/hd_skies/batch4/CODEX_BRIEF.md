# Codex brief: HD sky masters (batch4)

## Scope

Image generation only. Write files only into `level_generation/lighting/sky_art/hd_skies/batch4`. Do not build, run the game, edit code or touch any other
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

### `6sky04`

- Input: `inputs/6sky04.png` (512 × 512, from `assets_dev/worlds/mm6/textures/6sky04.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#2a3159** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #eeeeef, #aeaeaf, #7c7d7e, #52525c, #2a3159.
- Save as `6sky04_hd.png`.

### `7plansky3`

- Input: `inputs/7plansky3.png` (512 × 512, from `assets_dev/worlds/mm7/textures/7plansky3.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#30488c** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #b4a48c, #817c8b, #56608b, #38508c, #30488c.
- Save as `7plansky3_hd.png`.

### `cloudsabove`

- Input: `inputs/cloudsabove.png` (512 × 512, from `assets_dev/worlds/mm9/textures/cloudsabove.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#4f4e71** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #e6e0cd, #dac0b1, #b5a0a8, #827789, #4f4e71.
- Save as `cloudsabove_hd.png`.

### `sky02`

- Input: `inputs/sky02.png` (256 × 256, from `assets_dev/worlds/mm8/textures/SKY02.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#464a6e** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #b09782, #8d766b, #796e76, #6c5f65, #464a6e.
- Save as `sky02_hd.png`.

### `sky12`

- Input: `inputs/sky12.png` (256 × 256, from `assets_dev/worlds/mm7/textures/sky12.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#3341ad** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #dddede, #9e9eae, #7171ac, #5455ac, #3341ad.
- Save as `sky12_hd.png`.

## Per-image checks (run before selecting)

1. Square canvas of at least 1024 px, picture fills it edge to edge.
2. Side by side with the input: same cloud layout and colours; nothing added or removed.
3. Open-sky inputs: the gaps between clouds are one flat colour. Sample a few gap pixels: each channel within ±6 of
   the given colour is a pass (the engine keys it out; tiny variation is harmless, so do not spend attempts on it).
4. Tile the result 2 × 2 (for example with Python/PIL into a scratch file in this folder) and check that the edges
   continue without a visible seam or cut-off cloud.
5. None of the "Do not add" items appear.

Regenerate a failed image with one targeted correction (at most three attempts per sky). Keep rejected attempts as
`<name>_hd_try<N>.png`.

## Records

Write `generation_runs.json` listing every attempt: sky, file, prompt, selected flag and reason. Write
`selected_review.png`: each selected master beside its input (input scaled to the same size with nearest-neighbour).

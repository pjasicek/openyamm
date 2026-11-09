# Codex brief: HD sky masters (batch2)

## Scope

Image generation only. Write files only into `level_generation/lighting/sky_art/hd_skies/batch2`. Do not build, run the game, edit code or touch any other
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

### `6sky02`

- Input: `inputs/6sky02.png` (512 × 512, from `assets_dev/worlds/mm6/textures/6sky02.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#3d446c** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #b89e88, #917a6e, #746669, #57546d, #3d446c.
- Save as `6sky02_hd.png`.

### `6sky12`

- Input: `inputs/6sky12.png` (512 × 512, from `assets_dev/worlds/mm6/textures/6sky12.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#3041ac** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #dfdfdf, #9e9eaf, #7171ac, #5454ad, #3041ac.
- Save as `6sky12_hd.png`.

### `7sky02`

- Input: `inputs/7sky02.png` (256 × 256, from `assets_dev/worlds/mm7/textures/7sky02.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#43486c** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #c0a98e, #9c8877, #8a7369, #6c6269, #43486c.
- Save as `7sky02_hd.png`.

### `plansky3`

- Input: `inputs/plansky3.png` (512 × 512, from `assets_dev/worlds/mm8/textures/PLANSKY3.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#809cb0** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #d2c9bd, #a9acb5, #8ea2b4, #859db0, #809cb0.
- Save as `plansky3_hd.png`.

### `sky04`

- Input: `inputs/sky04.png` (512 × 512, from `assets_dev/worlds/mm8/textures/sky04.bmp`).
- **Fully painted sky**: clouds cover the whole tile. Keep every area painted; there is no open sky to flatten.
- Main colours of the original, brightest first: #b0bcde, #90a4c5, #7b8fb3, #6b82a5, #5b749b.
- Save as `sky04_hd.png`.

### `skycity01`

- Input: `inputs/skycity01.png` (256 × 256, from `assets_dev/worlds/mm7/textures/skycity01.bmp`).
- **Fully painted sky**: clouds cover the whole tile. Keep every area painted; there is no open sky to flatten.
- Main colours of the original, brightest first: #d5d7e9, #bbc8e8, #bbc8e8, #bbc8e8, #aebce4.
- Save as `skycity01_hd.png`.

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

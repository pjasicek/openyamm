# Codex brief: HD sky masters (batch3)

## Scope

Image generation only. Write files only into `level_generation/lighting/sky_art/hd_skies/batch3`. Do not build, run the game, edit code or touch any other
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

### `6sky03`

- Input: `inputs/6sky03.png` (512 × 512, from `assets_dev/worlds/mm6/textures/6sky03.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#2042ae** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #9bb2b4, #6291af, #3c75ae, #235bac, #2042ae.
- Save as `6sky03_hd.png`.

### `6sky19`

- Input: `inputs/6sky19.png` (512 × 512, from `assets_dev/worlds/mm6/textures/6sky19.bmp`).
- **Fully painted sky**: clouds cover the whole tile. Keep every area painted; there is no open sky to flatten.
- Main colours of the original, brightest first: #98816d, #887162, #78685d, #6c5e59, #5b5153.
- Save as `6sky19_hd.png`.

### `7sky04`

- Input: `inputs/7sky04.png` (256 × 256, from `assets_dev/worlds/mm7/textures/7sky04.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#2b3158** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #eeefef, #b3b3b3, #828284, #56575d, #2b3158.
- Save as `7sky04_hd.png`.

### `sky01`

- Input: `inputs/sky01.png` (512 × 512, from `assets_dev/worlds/mm8/textures/sky01.bmp`).
- **Fully painted sky**: clouds cover the whole tile. Keep every area painted; there is no open sky to flatten.
- Main colours of the original, brightest first: #e4ede0, #dae6db, #dbddde, #c9dbd6, #bdc5bb.
- Save as `sky01_hd.png`.

### `sky05`

- Input: `inputs/sky05.png` (512 × 512, from `assets_dev/worlds/mm8/textures/sky05.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#bcccf4** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #dddee0, #d4dbed, #c6d1ef, #cbcccc, #bcccf4.
- Save as `sky05_hd.png`.

### `stormclds`

- Input: `inputs/stormclds.png` (512 × 512, from `assets_dev/worlds/mm8/textures/stormclds.bmp`).
- **Fully painted sky**: clouds cover the whole tile. Keep every area painted; there is no open sky to flatten.
- Main colours of the original, brightest first: #b9bfd4, #9da6be, #8994af, #77859f, #65728b.
- Save as `stormclds_hd.png`.

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

# Codex brief: HD sky masters (batch1)

## Scope

Image generation only. Write files only into `level_generation/lighting/sky_art/hd_skies/batch1`. Do not build, run the game, edit code or touch any other
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

### `6plansky1`

- Input: `inputs/6plansky1.png` (512 × 512, from `assets_dev/worlds/mm6/textures/6plansky1.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#30498c** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #c8b98e, #9e928d, #706e8d, #4d5a8e, #30498c.
- Save as `6plansky1_hd.png`.

### `6sky06`

- Input: `inputs/6sky06.png` (512 × 512, from `assets_dev/worlds/mm6/textures/6sky06.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#2242ae** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #baafae, #9389ad, #6a6bad, #4653ae, #2242ae.
- Save as `6sky06_hd.png`.

### `7sky01`

- Input: `inputs/7sky01.png` (256 × 256, from `assets_dev/worlds/mm7/textures/7sky01.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#30488c** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #bfb08c, #91878b, #67698b, #45558c, #30488c.
- Save as `7sky01_hd.png`.

### `plansky1`

- Input: `inputs/plansky1.png` (256 × 256, from `assets_dev/worlds/mm8/textures/PLANSKY1.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#809cb0** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #d3cabd, #abadb6, #95a4b3, #879eb1, #809cb0.
- Save as `plansky1_hd.png`.

### `sky03`

- Input: `inputs/sky03.png` (512 × 512, from `assets_dev/worlds/mm8/textures/sky03.bmp`).
- **Open sky with clouds**: paint every gap between clouds as one perfectly flat, even colour **#5d6b99** (no gradient, noise, haze or texture in the open sky). Clouds keep their own soft edges against it.
- Main colours of the original, brightest first: #c0c7e9, #a6afd7, #909ac4, #7a87b3, #5d6b99.
- Save as `sky03_hd.png`.

### `sky19`

- Input: `inputs/sky19.png` (256 × 256, from `assets_dev/worlds/mm7/textures/sky19.bmp`).
- **Fully painted sky**: clouds cover the whole tile. Keep every area painted; there is no open sky to flatten.
- Main colours of the original, brightest first: #8b7364, #746762, #776457, #675b57, #594d53.
- Save as `sky19_hd.png`.

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

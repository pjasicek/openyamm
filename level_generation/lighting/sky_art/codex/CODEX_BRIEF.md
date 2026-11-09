# Codex brief: Enhanced sky art

## Scope

Image generation only. Write files only into `level_generation/lighting/sky_art/codex/`. Do not build, run the game,
edit code or touch any other folder. Use your built-in image generation tool.

These images are layers of a real-time fantasy RPG sky (Might and Magic 6–8 style worlds: painterly, warm,
slightly storybook, never photographic sci-fi). The engine tints and composites them; it draws the sky gradient,
sun, procedural stars and clouds itself. The art must therefore be **neutral and isolated**, as described per file.

## Deliverables

Save each final selection under exactly these names (PNG). Keep rejected attempts as `<name>_try<N>.png`.

| File | Size | Content |
| --- | --- | --- |
| `horizon_ring_src.png` | 4096 × 512 (or the closest wide size you can make; it is resized later) | A 360° band of distant cloud banks seen on the horizon |
| `night_sky_src.png` | 4096 × 2048 (2:1) | Milky Way band and faint nebula dust on pure black |
| `moon_src.png` | 1024 × 1024 | A single full moon disc, centred, on pure black |

### horizon_ring_src.png

- A continuous, wide panorama of **distant cumulus cloud banks and low haze sitting on the horizon**, seen from
  ground level, filling only the **lower half** of the image. The upper half is plain flat mid-grey (no clouds).
- **Greyscale only**: soft white tops, grey undersides, mid-grey background. No blue sky, no sun, no colour.
- The bottom 15% is an even light haze (the clouds dissolve into mist at the horizon).
- Varied silhouettes: some taller cloud towers, long low banks, gaps. Painterly, soft edges.
- Even, flat lighting (no sun direction, no strong shadows).
- The left and right edges should continue naturally into each other (it will wrap around 360°).

### night_sky_src.png

- An equirectangular (2:1) night sky: **a diagonal Milky Way band** crossing the image with soft dust lanes, faint
  cool blue/violet and warm amber nebula glow, on **pure black**.
- Keep it subtle: the band is a soft glow, not a bright photo. Only small, sparse stars; no big bright stars
  (the engine draws those).
- Top and bottom 10% of the image must be pure black (these are the poles).

### moon_src.png

- One **full moon** disc, centred, filling about 90% of the canvas, on **pure black**.
- **Neutral grey** surface: maria, craters and highlands with soft, painterly detail. No colour cast, no glow, no
  halo, no stars, no phase shadow (the engine shades the phase).
- Evenly lit face-on.

## Do NOT

- No sun, sun rays, lens flare, ground, mountains, trees, water, birds, buildings, people, text, logos, frames,
  watermarks or borders in any image.
- No photographic NASA imagery look; keep a painted fantasy-game finish.
- No colour in the horizon ring or the moon.

## Per-image checks (run before selecting)

1. Correct aspect ratio and canvas as listed.
2. Background requirements met (flat mid-grey upper half for the ring; pure black for the night sky and moon).
3. None of the "Do NOT" items appear.
4. Ring: clouds only in the lower half, horizontal continuity with no obvious left/right seam break.
5. Night sky: poles black, band diagonal and subtle.
6. Moon: centred circle, neutral grey, no halo.

Regenerate a failed image with one targeted correction (at most three attempts per image).

## Records

Write `generation_runs.json` listing every attempt: file, prompt, selected flag and reason. Write
`selected_review.png`, a contact sheet of the three selected images.

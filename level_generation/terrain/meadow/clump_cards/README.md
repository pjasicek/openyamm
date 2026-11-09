# Short grass clump cards (plants_v4 cells 0 and 1)

The short grass is drawn as clumps: five cards in a star around the tuft centre, each leaning outward about 25
degrees. Cells 0 and 1 of `plants_v4.png` are single cards of such a clump: a side view of a bunch of blades rising
from a narrow base and fanning upward. They replace plants_v3's wide, low grass mats, which showed as dark strips
and slivers from raised views. Cells 2-15 are unchanged from plants_v3 (checked texel for texel).

## Source and licence

Poly Haven **Grass Medium 01** (`grass_medium_01`, https://polyhaven.com/a/grass_medium_01), modelling by Rico
Cilliers, photography by Rob Tuytel. Licence: **CC0 1.0** (public domain dedication, https://polyhaven.com/license);
attribution is not required but is given here.

Files used (listed by `https://api.polyhaven.com/files/grass_medium_01`, the 2K glTF plus the 2K alpha map that only
the .blend lists):

- `https://dl.polyhaven.org/file/ph-assets/Models/gltf/2k/grass_medium_01/grass_medium_01_2k.gltf`
- `https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/grass_medium_01/grass_medium_01.bin`
- `https://dl.polyhaven.org/file/ph-assets/Models/jpg/2k/grass_medium_01/grass_medium_01_diff_2k.jpg`
- `https://dl.polyhaven.org/file/ph-assets/Models/jpg/2k/grass_medium_01/grass_medium_01_nor_gl_2k.jpg`
- `https://dl.polyhaven.org/file/ph-assets/Models/jpg/2k/grass_medium_01/grass_medium_01_arm_2k.jpg`
- `https://dl.polyhaven.org/file/ph-assets/Models/png/2k/grass_medium_01/grass_medium_01_alpha_2k.png`

Keep the glTF beside a `textures/` folder holding the four images (about 10 MB in all). The downloads are not
committed; the renders in `renders/` are.

## The cards

`scripts/render_cards.py` merges some of the model's smaller tufts, each turned by its own yaw about a shared base,
and drops blades (loose mesh parts) that lie on the ground, dead leaf sheaths (the dark knot at the base), blades
reaching sideways beyond `max_reach`, and seed stalks above `max_top`:

| Cell | Tufts (yaw) | max_reach | max_top | Character |
| --- | --- | --- | --- | --- |
| 0 | `mid_c` (90), `mid_b` (20) | 0.105 m | 0.14 m | fuller, a little greener |
| 1 | `small_a` (0), `small_b` (130), `mid_b` (220) | 0.08 m | 0.12 m | sparser, finer, a little warmer |

Each card is an orthographic side view at 1024 x 1024, centred on the tuft's axis, with transparent film, alpha
clipped at 0.5, matte material (no specular or normal map) and flat soft light (a white world plus a weak shadowless
top sun). `../process_art.py` then:

- crops symmetrically about the base, so the base sits in the cell's middle column (the clump centre);
- scales to fit 252 x 188 with premultiplied-alpha Lanczos filtering and grounds the plant at row 190;
- raises coverage by 1.5, so blades one to three texels wide survive the game's 0.5 alpha test;
- bleeds colour into transparent texels (as for every cell);
- blends the lowest 28 rows towards the card's mean colour (up to 60 % at the ground row), so the pale leaf sheaths
  do not read as a light knot;
- matches the solid texels' mean to `SHORT_GRASS_MEAN` (0.313, 0.383, 0.218) times a variety factor (cell 0
  (0.98, 1.025, 1.02), cell 1 (1.02, 0.975, 0.98); the factors average to one, so the pair keeps the short-grass
  mean that the rule tints and ground matching rely on), turns the few brown tips that matching tints lilac back to
  straw, and matches once more.

Final cards: cell 0 plant 231 x 188 texels (aspect 1.23), mean (0.307, 0.393, 0.223); cell 1 plant 230 x 188
(aspect 1.22), mean (0.320, 0.374, 0.214); pair mean (0.314, 0.384, 0.219). Both span rows 2-190, centred on
column 128.

## Rebuild

```
level_generation/terrain/meadow/clump_cards/build.sh <glTF dir> [--install]
```

renders the cards (Blender 5.2, headless), runs `../process_art.py` (writes `../plants_v4.png` and
`../art/review.png`; `--install` copies plants_v4.png into `assets_dev/worlds/mm6|mm7|mm8/terrain_decorations/`),
then renders the clump previews and writes `review/clump_review.png`. Logs go to `work/logs/`.

## Review

`scripts/preview_clump.py` builds five-card star clumps in Blender (25 degree lean, cells 0, 1, 0, 1, 0, unlit,
alpha tested, on a ground of the short-grass colour), one clump and a patch of nine, from eye level (10 degrees
down), 45 degrees down and straight down, for plants_v3 and plants_v4.

- `review/clump_review.png`: the current build.
- `review/clump_review_pass0.png`: first cards (single tufts): wispy, lilac dead blades lying at the base.
- `review/clump_review_pass1.png`: merged tufts, filtered blades, base-centred cards, alpha gain.
- `review/clump_review_pass2.png`: plus the base blend and the lilac fix (same as the current build).

The previews are unlit, so they check silhouette, coverage and colour against the ground, not the game's lighting
or mip behaviour.

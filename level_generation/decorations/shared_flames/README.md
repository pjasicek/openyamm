# Shared coloured flames

Flame flipbooks in colours other than the MM torch orange, for fire decorations of any world. They are made by
`make_coloured_flames.py` from the CC0 Unity Labs Flame02 flipbook (`../mm6_dungeons_3d/source/unity_labs_vfx/`,
licence there), with the recipe of `../mm6_dungeons_3d/scripts/make_flames.py`.

| File | Colour measured on | Used by |
|---|---|---|
| `flame02_red_basecolor.png` | MM7 `torch07` | red torches |
| `flame02_purple_basecolor.png` | MM7 `torch05` | purple torches |
| `flame02_green_basecolor.png` | MM7 `torch06` | green torches |
| `flame02_blue_basecolor.png` | MM7 `dec60` | blue beacon fire |
| `flame02_white_basecolor.png` | MM7 `dec63` | white beacon fire |

- The orange flame is `../mm6_dungeons_3d/textures/flame02_basecolor.png`.
- Every sheet is 2048 × 1024, 16 × 4 frames, a seamless 64-frame loop.
- Card recipe and material: `../mm6_dungeons_3d/textures/FLAMES.md` (`openyamm_flipbook: [16, 4, 30]`).
- Each ramp is the mean native flame colour per brightness quantile, sampled in the flame's rows of all eight frames.
  `preview.png` shows the first four frames of each sheet.

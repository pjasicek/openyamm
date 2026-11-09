# Wall torch PBR textures (Revision 2, 2026-10-09)

Real CC0 surfaces for the dungeon wall torches, which are the most-placed dungeon models: `6torch01` (3441 placements)
and `torchnf`, `trchb00` (755) and `nwtrchnf`, and `torch01` (75), each with its `_free` variant. The procedural props
wood, iron, logs and leather, which were tinted almost to flat colours, are replaced by four tileable texture sets
(base colour, OpenGL normal, glTF metallic-roughness: G roughness, B metal). All ten GLBs share these sets. Geometry,
flame cards, wall-mount convention and lit/unlit bracket placement are unchanged; the 6torch01/torchnf clamp is now an
open cage (below).

| Set | Source (Poly Haven, CC0) | Used by | Look |
|---|---|---|---|
| `torchwood` | Rough Wood (Rob Tuytel) | 6torch01/torchnf stick, torch01 stick and holder | weathered, cracked grain along the stick, matte (roughness 0.78) |
| `torchrag` | Hessian 380 (colormass, Rico Cilliers) + procedural tar | 6torch01/torchnf head, torch01 wrap | burlap wound in four slanted laps with shadowed seams, ~2/3 soaked with glossy tar (roughness 0.92 cloth, 0.42 tar) |
| `rustiron` | Rust Coarse 01 (Dimitrios Savva, Rico Cilliers) + bare-iron mask and normal from Rusty Metal 04 (Amal Kumar) | 6torch01/torchnf clamp, arm, plate | rust-brown forged iron with darker, shinier bare patches |
| `darkiron` | Rusty Metal 04 (Amal Kumar) | trchb00/nwtrchnf body and bracket | dark blue-grey iron, gentle mottle, warm copper streaks along the shaft, glossy (roughness ~0.3-0.45, metal 0.15-0.3) |

Licence: every Poly Haven asset is CC0 1.0 (public domain, <https://polyhaven.com/license>); the derived maps here are
project-owned. The embers set (props `embers`) and the flame flipbook (`../textures/flame02_basecolor.png`, CC0 Unity
Labs) are unchanged.

## Open clamp (6torch01 / torchnf)

The pilot's solid ring is replaced by the open iron clamp of the native sprite (`../scripts/build_torch.py`,
`clamp()`), measured from the x2 frames: a flat hoop 22.4 wide at 28.5-32.5 and one 21.2 wide at 40.5-43.2, joined by
thin vertical bars about 2 wide whose outer edges are about 14 apart, with the stick showing between them, and four small
teeth under the lower hoop's rim. LOD0 has six bars and 10-sided hoops, LOD1 four bars and 8-sided hoops, and LOD2 keeps
the old 6-sided solid ring. The hoops have sharp edges (split normals). The arm, wall plate, rivets, stick, head,
flame, tint targets and lit/unlit alignment are unchanged; the arm meets the lower hoop.

The bars are straight. The sprite shows no flare, and the head sits above the clamp, not in a basket.
trchb00/nwtrchnf (a solid fluted bowl on a shaft with a bolted bracket plate) and torch01 (a wooden holder block and
a cloth wrap) have no iron cage in their sprites, so their geometry is unchanged
(`review/closeups.png`).

## Colour

The texture sets are graded to neutral tones a little brighter than any native tone they serve. Each model's COLOR_0
(vertex occlusion times a per-material tint, `tlib.tint`) then darkens them to the native sprite's measured mean.
COLOR_0 is a normalised vertex colour (at most one), so the sets keep that headroom. Flat renders (emission only, light
one) against the sprites, sRGB band means native / model:

| Model | Bands (native units) |
|---|---|
| 6torch01 | stick 0-25 (44,21,8)/(49,25,11) · clamp 26-41 (36,19,10)/(41,22,11) · stick 43-57 (37,20,8)/(38,18,7) · head 59-72 (38,20,9)/(37,20,9) |
| torchnf | (65,41,19)/(71,46,22) · (62,47,32)/(71,53,34) · (68,45,23)/(64,41,19) · (67,44,23)/(67,43,24) |
| trchb00 | foot (43,41,45)/(53,50,60) · lower shaft (55,53,64)/(55,53,66) · bracket (47,48,59)/(54,54,66) · upper shaft (71,68,85)/(65,63,78) · bowl (71,66,76)/(70,66,79) |
| nwtrchnf | (44,43,49)/(54,50,59) · (62,58,69)/(56,53,65) · (60,59,68)/(66,63,73) · (74,71,88)/(67,63,78) · (66,61,71)/(69,65,78) |
| torch01 | stick (69,31,16)/(66,30,16) · holder (60,32,20)/(49,27,17) · upper stick (97,45,29)/(91,44,25) · wrap (81,42,24)/(81,42,24) |

torchnf is lit by its sector, so its sprite is painted much lighter than the self-lit 6torch01. It now has its own
targets; before, it reused the lit torch's night tones and read nearly black next to its sprite.

## Budget

| | LOD triangles | GLB |
|---|---|---|
| `mm6_deco_torch.glb` / `_free` | 454/267/149, free 382/243/125 (was 410/247/149, 338/223/125) | 4.3 MB |
| `mm6_deco_torch_unlit.glb` / `_free` | 412/237/127, free 340/213/103 (was 368/217/127, 296/193/103) | 3.3 MB |
| `mm6_deco_irontorch.glb` / `_free` | 544/336/194, free 484/324/182 | 2.2 MB |
| `mm6_deco_irontorch_unlit.glb` / `_free` | 490/298/166, free 430/286/154 | 1.1 MB |
| `mm6_deco_torch01.glb` / `_free` | 424/256/86 | 3.1 MB |

Texture memory: all maps are 512 x 512 RGBA8. With mips, that is 1.33 MiB per map. The engine shares a GPU texture
between models whose embedded PNG bytes are equal, and the glTF exporter embeds these files unchanged, so all ten
GLBs share 12 maps (16 MiB), plus the existing embers set (4 MiB) and flame atlas (10.7 MiB). This is the same as
before: four 512 props sets at 16 MiB. 1k maps would cost 64 MiB and add nothing. The textures tile tightly: one tile
covers about 0.3 m of stick or shaft circumference. So even at the closest in-game view (about 900 screen pixels per
metre), a 512 tile still gives more than one texel per pixel.

## Scripts

- `scripts/fetch.py`: downloads the 1k Poly Haven maps into `source/<asset>/` (run with `python3 -I`).
- `scripts/make_textures.py`: builds `textures/<set>_{basecolor,normal,mr}.png` (deterministic, tileable).
- `scripts/ttex.py`: the builders' material helper (this folder's sets, else `../torches/scripts/tlib.py`).
- `scripts/review.py`, `scripts/sheet.py`: thin wrappers that run the torch batch's review renders and sheet with
  output in `review/<prop>/` (compare.png: native, flat light one, front, three-quarter, side; lods.png).
- `scripts/closeup.py`, `scripts/closeup_sheet.py`: orthographic close-ups of the clamp and head (front,
  three-quarter, side) next to the same window of the native sprite (`review/<prop>/closeup.png`).
- `scripts/run_all.sh [--install] [prop ...]`: textures, then build, finish, review, sheet and close-up per model.
  Builders: `../scripts/build_torch.py` (6torch01/torchnf), `../torches/scripts/build_irontorch.py`,
  `../torches/scripts/build_torch01.py`.

## Review

- `review/before/`, `review/after/`: gallery screenshots (Studio light), `review/before_after.png` zoomed side by side.
- `review/flat_compare.png`: the five flat-light Blender sheets stacked; per-model sheets in `review/<prop>/`.
- `review/closeups.png`: the five clamp/head close-ups stacked. `review/after_cage/` and
  `review/cage_before_after.png` show the gallery before, with textures, and with textures and the open cage.

## Compromises

- The flat render cannot show the native trchb00's white highlights. In the engine they come from the glossy
  roughness under the torch's own point light, and the gallery's Studio light shows them.
- The torch01 holder is about 10 sRGB levels darker than its band, as before (the band also includes the stick).
- The GLB files grew by about 1.5 MB each, because the new PNG maps compress less than the flat procedural ones.
  GPU memory did not grow.

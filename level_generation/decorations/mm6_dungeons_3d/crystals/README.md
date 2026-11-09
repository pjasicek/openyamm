# MM6 dungeon crystals, stalagmites and column (2026-10-09)

Static 3D replacements for nine MM6 dungeon decoration sprites, built per [the project brief](../BRIEF.md):
procedural Blender geometry fitted to the native sprites, three LODs linked by `tools/link_static_model_lods.py`,
COLOR_0 on every primitive (vertex occlusion x per-material tint x per-vertex shading factors).

| Sprite | Installed GLB | LOD triangles | File |
|---|---|---|---|
| `crystl0` pink glowing cluster (32 placements) | `assets_dev/worlds/mm6/models/mm6_deco_crystl0.glb` | 1264 / 328 / 150 | 382 KB |
| `mcryst01` Memory Crystal (4) | `…/mm6_deco_mcryst01.glb` | 1346 / 338 / 98 | 516 KB |
| `crclstr` quartz cluster (21) | `…/mm6_deco_crclstr.glb` | 1646 / 586 / 281 | 407 KB |
| `crys6` blue crystal mound (17) | `…/mm6_deco_crys6.glb` | 2806 / 885 / 316 | 1.35 MB |
| `crys5` salmon blade rosette (15) | `…/mm6_deco_crys5.glb` | 2658 / 896 / 308 | 561 KB |
| `stlmite1` stalagmite (5) | `…/mm6_deco_stlmite1.glb` | 2210 / 1000 / 300 | 1.3 MB |
| `stlmite2` stalagmite with side spires (9) | `…/mm6_deco_stlmite2.glb` | 2782 / 998 / 299 | 1.3 MB |
| `stlmite3` broad stalagmite (3) | `…/mm6_deco_stlmite3.glb` | 2622 / 999 / 300 | 1.3 MB |
| `corinth` Corinthian column (32) | `…/mm6_deco_corinth.glb` | 2892 / 1092 / 292 | 615 KB |

Budget: tens of placements, LOD0 at most 3000 (`finish.py` checks 3000 / 1200 / 400). The crystal clusters stay
below the brief's 1500 floor where the shape needs no more (faceted prisms: LOD0 is sized to the shape).

## Suggested bindings

Heights are logical height x DSFT frame scale (brief rule). Model bounds heights: crystl0 90, mcryst01 63, crclstr
128, crys6 99, crys5 74, stlmite 207 / 188 / 212, corinth 448. Two sprites carry empty rows above the art, so their
visible height is smaller than the rule's: mcryst01 63 (rule 65) and corinth 448 (rule 455); use those if the
model should match the native art exactly (about 3% and 1.6% smaller).

```yaml
- {name: crystl0,  model: mm6_deco_crystl0.glb,  height: 92}     # pulse: animated, not still
- {name: mcryst01, model: mm6_deco_mcryst01.glb, height: 65}     # flipbook + pulse: animated, not still
- {name: crclstr,  model: mm6_deco_crclstr.glb,  height: 128}
- {name: crys6,    model: mm6_deco_crys6.glb,    height: 98}
- {name: crys5,    model: mm6_deco_crys5.glb,    height: 77}
- {name: stlmite1, model: mm6_deco_stlmite1.glb, height: 208}
- {name: stlmite2, model: mm6_deco_stlmite2.glb, height: 190}
- {name: stlmite3, model: mm6_deco_stlmite3.glb, height: 210}
- {name: corinth,  model: mm6_deco_corinth.glb,  height: 455}
```

All stand on the floor (no `mount`, `free_model`, `swing`), `z_offset: 0`. Yaw: placement yaw or random for the
crystals and stalagmites (they read from every side); the column's square plinth and abacus suit yaw 0 (axis aligned
with the rooms) when columns stand in rows. `crclstr`, `crys6` and `crys5` have one frame (no animation needed);
`crystl0` and `mcryst01` are animated (below), so none needs `still: true`.

## Models

- **crystl0**: a fan of 18 chamfered hexagonal prisms traced from the native frame (logical-pixel base/tip pairs in
  `build_crystals.py`), depth added so the fan reads from every side, radii x1.3 of the traced widths, ten small
  shards at LOD0. Colours from the sprite's own colour ramp (see Colour): dark wine-red roots and tips, a bright
  middle, bright chamfered edges, dark and lit sides and mid-length glints; ramp saturation x1.4, albedo x0.8; glossy
  (`openyamm_specular` 1.0, roughness 0.12-0.18). Inner pink glow `emissiveFactor` [0.06, 0.016, 0.03] (saturated
  native hue; it lifts the darkest facets to about the sprite's dark wine red) with
  `openyamm_pulse: [0.45, 2.0625]`: the native loop is 33/16 s; its six frames move highlights and vary the mean
  luminance by about 8%.
- **mcryst01** (revision 2, user review: "should be a disc, not a bowl"): the stand is a flat disc, 40 across and
  6 high, as the native frames show it (an ellipse 40 x 15 seen from about 16 degrees above: bright back and front
  rim, dark flat top, rounded underside): a lathed lens-like underside, a rolled rim and a flat top only 1 unit below
  the rim. Scratched dark metal: luminance, softened normal and roughness (0.18-0.5, dielectric) from CC0 Poly Haven
  `blue_metal_plate`, projected from above (0.8 m per repeat); COLOR_0 from the sprite's disc texels (bright rim, dark
  top). The ball stays a camera-facing card (`openyamm_billboard`, MASK) with a flipbook
  (`openyamm_flipbook: [3, 2, 4]`, the native 4/16 s per frame) and a lavender emission pulsing `[0.5, 1.5]`. The face
  in the ball is the Memory Crystal's identity, so it is kept; but the six upscaled frames are no longer played:
  `textures/memorb_basecolor.png` (`scripts/make_memory_crystal.py`, 128 texels per frame) repeats one still ball, the
  per-texel median of the six restored frames (no frame-to-frame upscaling shimmer), with a painted glass highlight,
  a darkened edge and a clean round outline, and draws the animation crisply on top: pink-white sparkles and the red
  eye glints at the positions, sizes and colours measured in the six native 44 x 65 frames. A ball looks the same
  from every side, so the impostor holds from every direction (it foreshortens only from well above).
- **crclstr**: quartz prisms traced from the sprite (radii x1.25), small crystals and a bed of icosahedral pebbles
  (warmer, from the sprite's bottom rows) at the foot; glossy quartz, matte-ish pebbles.
- **crys6**: a faceted rock mound fitted to the sprite's crest (row-by-row top of the silhouette, 11 units under it),
  covered by 84 area-sampled chunks: blue crystals (four/five-sided, chamfered) on the left two thirds, blunt grey
  rock chunks on the right and scattered among them, plus the sprite's spike at the crest. Separate ramps from the
  sprite's blue and grey texels (blue saturation x1.3); glossy crystal, matte rock.
- **crys5**: 90 wide, thin blade crystals radiating from two rosette centres under the floor (ellipsoid envelope
  62 x 42 x 94), each turned at random about its length, over a low central boss; dark heart, bright blade tips
  (sprite ramp, saturation x1.1); glossy.
- **stlmite1-3**: spires lathed on the sprite silhouette (row spans inside per-spire column windows; depth 0.85 of
  the width), displaced by noise, drip-column ribs and flowstone ledges every ~7 units, side spires from their own
  windows (`SPIRES` in `build_stalagmite.py`); large light/dark colour patches in COLOR_0; LOD1/LOD2
  collapse-decimated. Native means (132, 111, 100), (158, 130, 116), (131, 110, 100).
- **corinth**: square bevelled plinth, a base of three rows of eight hanging acanthus leaves over a moulded bell,
  plain shaft, astragal, a capital of three rows of eight upright leaves curling outward under a square abacus;
  profile radii are the sprite's half widths row by row (x2 pixels, `build_corinth.py`). Marble (props `marble`)
  tinted to (144, 133, 117); leaves are a separate double-sided material. LOD1 coarser leaves, LOD2 flared lathe
  crowns instead of leaves.

## Textures (textures/, generated by `scripts/make_textures.py`)

Procedural, tileable (FFT-filtered noise), no external sources: `crystal` (near-white clouded crystal, streaks along
the prism, roughness 0.12-0.18), `greyrock` (speckled grey rock), `dripstone` (terraced limestone with painted top light, ochre/umber
mottling, calcite drips), `dishmetal` (smooth dark metal, no longer used); `memball` (the revision 1 flipbook of the restored frames, no
longer used). Revision 2 Memory Crystal (`scripts/make_memory_crystal.py`): `memorb` (ball flipbook, above) and
`memdisc_*` from CC0 Poly Haven [Blue Metal Plate](https://polyhaven.com/a/blue_metal_plate) by Rob Tuytel (1k
diffuse, OpenGL normal and roughness, 8-bit copies in `textures/polyhaven/`, licence CC0). The column uses the outdoor props `marble`
(`../../mm6_new_sorpigal_3d/props/textures/`, read only). Crystals and the cradle use `openyamm_specular` 1.0, the
pebbles 0.5, the rock 0.4.

## Colour

Crystals (crystl0, crclstr, crys6, crys5) and the Memory Crystal cradle: COLOR_0 comes from the native sprite's colour
ramp (`native_ramp` in `crystals_lib.py`: the sprite's opaque texels, or a material's subset, sorted by luminance into
24 equal-count bins). Each vertex gets a rank on that ramp: its facet's (bright chamfered edges 0.85-1, dark faces
0-0.3, lit faces 0.4-0.8, tips 0.25-1, mid-length glints on lit faces) plus the crystal's brightness, a per-model
shift (height or position), 0.3 x the normal's up component (faces toward the light above are bright) minus
0.8 x the vertex occlusion; COLOR_0 = ramp colour / mean texture colour. Spread ranks reproduce the sprite's colour
distribution, not only its mean. A saturation boost on the ramp offsets the gloss's white sheen.

Stalagmites and column: tint per material = linear(native mean sRGB) / mean linear texture colour, divided by the
material's mean of occlusion x shading factors (the displayed mean, crevices included, stays at the native mean).

Review (`review.py`) since the crystal revision: dungeon-like light (grey ambient 0.35, key 0.55, a small torch-like
point light beside the camera, so gloss shows as highlights) plus a dim view (ambient 0.08); `sheet.py` prints
luminance percentiles and saturation of the native sprite and the LOD0 front render. After the revision
(p10/p50/p90, saturation; render vs native): crystl0 65/92/205 0.36 vs 34/81/156 0.45 (the glow lifts the darkest
facets; highlights are the gloss); crclstr 90/195/254 0.16 vs 114/187/238 0.18; crys6 90/172/253 0.12 vs
101/176/234 0.16; crys5 71/161/243 0.35 vs 106/182/225 0.37; mcryst01 52/82/138 0.13 vs 27/62/122 0.18 (ball card
blended in Blender). The stalagmite and column sheets were rendered with the earlier even light (ambient 0.6, key
0.6). The Blender light only approximates the engine's.

Before/after: `review/<prop>/sheet_before.png` (matte pastel, mean-normalised tints, even light) and
`review/<prop>/sheet.png` for crystl0, crclstr, crys6, crys5 and mcryst01. Memory Crystal revision 2: the bowl
version `review/mcryst01/sheet_rev1_bowl.png` and `review/gallery_before/dungeon_mcryst01_side.png`, the disc
`review/mcryst01/sheet.png` and `review/gallery_after/dungeon_mcryst01_{side,model}.png`.

## Build and review

`./build.sh [--install] [prop...]`: textures, `build_crystals.py` / `build_mcryst.py` / `build_stalagmite.py` /
`build_corinth.py` (Blender, headless) to `work/<prop>_export.glb`, `review.py` renders, `sheet.py`, `finish.py`
(materials, LOD link, validation; `--install` copies to `assets_dev/worlds/mm6/models/` with mode 0664 and refuses to
replace a GLB this batch did not install). Review sheets: `review/<prop>/sheet.png` (native sprite, LOD0 front,
three-quarter, side; all LODs); the column also has close-ups of its capital and base (`review/corinth/detail_*.png`).
Blender does not run the billboard, so the Memory Crystal card shows edge-on in the side view and blended rather
than cut out.

## Compromises

- The crystal clusters are opaque: translucency is painted with per-facet COLOR_0 ramp colours rather than blending.
- The engine's emission is one flat colour per material, so crystl0's glow also lifts its dark bases; it is kept at
  the level of the sprite's darkest wine red.
- crys5's blades are randomly turned, so the dense face-on petal look of the sprite is only partly reproduced.
- The stalagmites are less contrasty than the painted sprite (its strong white highlights are partly lighting).
- Model bounds differ slightly from the logical heights (crys6 99 vs 98, crys5 74 vs 77, crystl0 90 vs 92); the
  binding height rescales them to the rule's value.

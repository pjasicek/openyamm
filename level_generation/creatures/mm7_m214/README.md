# MM7 Elf Archer restoration

Staged restoration of all 120 native unique frames, all referenced, for descriptors 247/248/249. Palette 216 supplies the sole generated base: silver hair and green garments. Fixed native ACT transforms derive palette 215 olive garments/blond hair and palette 217 red garments/brown hair. Original assets remain unchanged; this package is not installed into gameplay.

## Coverage and native playback

Five stored views retain mirrors for directions 5–7. Standing has five images, walking and attack/shoot each have eight poses per stored view, and hit has five. Death plays na0, nb0, da0, db0, dc0, dd0; corpse holds xa0; fidget plays fa0 through fe0. Death, corpse and fidget retain Image1 for all eight directions. Durations are 125 ms except the native 250 ms ad attack and fc fidget holds. Native 256×256 logical canvas, bottom pivot (128,256), Center flag and scale 1 remain in metadata.

## Artwork, masks and processing

Twenty-one selected sheets come from 24 built-in imagegen outputs; exact prompts, references, hashes and raw outputs remain in generation.json and the corresponding directories. Uniform 0.80 tone preserves native shadow weight. Connected pose extraction uses common per-sheet anatomical scale and native baseline translation. Premultiplied Lanczos produces 2× runtime pixels with preserved thin strings and arrow details. Processing settings and per-frame registration retain actual raw dimensions and scale.

RGB8 linear masks use R for enhanced green garments and G for enhanced silver hair; B is reserved zero. Cloth uses enhanced chroma and connected material support. Hair uses enhanced neutral/cool connected pixels, selected through coarse head rectangles. These are authored enhanced masks; native masks are not resized. Review corrected missed cool shadows and the nb1 head selector. Twenty enhanced feather-overlap exclusion polygons protect arrows across the hair; two prone head polygons protect skin and ivory trim. The rectangles and corrections remain in hair_regions.json and hair_overlap_corrections.json. Alpha-normalized sigma-0.45 feathering and overlap normalization preserve contour opacity. Native ACT indices 104–171 calibrate cloth matrices; neutral hair entries 62–103 calibrate fixed luminance matrices. Base palette 216 bypasses recoloring exactly. Skin, white trim, arrow fletchings, brown quiver/bow/bracer, gold fittings and red studs remain protected.

## Export and review

Two matching atlas/mask pages. Decoded RGBA8 + RGB8 including padding: 96,008,192 bytes (91.56 MiB); tight frame payload 86,282,826 bytes. All 120 native/restored frames and all 360 frame/palette combinations were reviewed in ordered action contacts. Enlarged edge contacts cover thin bowstrings, arrows, hands and feathers on light/dark backgrounds. Offline browser captures cover mirrored red attack and olive Image1 death. validation.json passes complete coverage, unchanged source hashes, unclipped raw cells, exact crop/atlas reconstruction, valid masks, unchanged variant alpha, base bypass and native timing/flag preservation; zero residual candidates above 32. Final acceptance hashes are in review/acceptance.json.

A transient disk-full error interrupted the first processing export; the full processing pass was rerun successfully before packaging and review. No generated artwork was lost.

The two undersampled attack sheets were replaced by five smaller overlapping sheets, retaining all other
selected artwork. A targeted v2 restores the exact arrow-loading phase rather than a fully drawn shot.
The 16 replacement frames measure 2.33398–2.77233 actual generated pixels per native pixel; all 120 frames
now exceed 2.04770. Prior accepted metadata is retained in checkpoints/before_sampling_repair, and
detail_rebatch_plan.json records common crops, overlap-only poses and actual sampling.
Updated enhanced head selectors avoid arrow feathers. Local head polygons protect the raised hand and
bowstring, and two enhanced shaft exclusion polygons keep arrows outside the garment mask.

## Reproduce offline

From repository root:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m214 --tone .80
python3 level_generation/creatures/mm7_m214/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m214
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m214
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m214
python3 level_generation/creatures/mm7_m214/review_variants.py
```

Open viewer.html directly for native/enhanced playback, all palettes, masks and timeline inspection. Rebuilds require renewed visual acceptance; manifest existence alone does not establish completion.

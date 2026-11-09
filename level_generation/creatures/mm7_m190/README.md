# MM7 Dwarf warrior restoration

Staged restoration of all 124 native unique frames, all referenced, for descriptors 229/230/231 and palettes 191/192/193. Base palette 191 is dark green cloth; fixed masked native ACT transforms derive blue-violet and muted red cloth. Original assets are unchanged; not installed into gameplay.

## Native coverage and placement

Five stored directions retain native mirrored views 5–7. Standing uses five images; walking and attack/shoot each use eight poses per stored view; hit uses six per view. Death is na0, nb0, da0, db0, dc0, dd0; corpse holds xa0. Fidget plays fa0, fb0, fc0, fd0, fc0, fb0. Death, corpse and fidget retain Image1 for all eight directions. Durations are 125 ms except the native 187.5 ms fd0 fidget hold. Native 256×256 logical canvas, bottom pivot (128,256), Center flag and descriptor scales 1, 1.049988, 1.099991 remain in metadata.

## Artwork and deterministic processing

Built-in imagegen supplied 18 selected sheets from 20 retained raw outputs, with exact prompts and reference hashes in generation.json. Standing v2 fixes blue cloth to native green; n0 v2 restores backward recoil of the head and beard. Original rejected versions remain under raw/. The other blue-cloth outputs receive a documented enhanced-pixel correction before resizing: saturated blue connected cloth support maps RGB to (0.70G,0.78B,0.68G), preserving alpha and protecting neutral steel. Green collar/skirt masks are authored on enhanced pixels, not enlarged native masks. R8 coverage uses green chroma with connected support and alpha-normalized sigma-0.45 feathering; native ACT indices 199–233 calibrate fixed variant matrices. The original beard, hair, skin, steel, chainmail, ivory, brass and brown leather remain protected. Palette 191 is an exact bypass.

Uniform 0.80 tone preserves native weight. Connected pose extraction uses common per-sheet anatomical scale and native baseline translation. Premultiplied Lanczos exports two physical pixels per logical pixel. Enhanced material hue repair removes demonstrated reddish beard-tip contamination; green fringe adjacent to neutral steel borrows nearby nonmagenta interior hue at original luminance before/after resize. Settings remain in config.json and processing_settings.json; alpha and thin details are preserved.

## Export and review

Two matching base/mask pages: 2048×3901 and 2048×1210. Decoded RGBA8 + R8 including atlas padding: 52,336,640 bytes (49.91 MiB); tight frame payload 46,584,000 bytes. Actual generation detail and common sheet scale are recorded per frame in registration.json.

Reviewed all 124 native/restored frames in ordered action contacts and all 372 frame/palette combinations. Enlarged light/dark edge contacts and browser captures cover mirrored blue attack and red Image1 death. validation.json verifies complete coverage, unchanged native hashes, unclipped raw cells, exact crop/atlas reconstruction, valid masks, unchanged variant alpha, exact base bypass and native group timings/flags. Final acceptance and artifact hashes are in review/acceptance.json.

## Reproduce offline

From repository root, using retained raw selections:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m190 --tone .80
python3 level_generation/creatures/mm7_m190/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m190
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m190
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m190
python3 level_generation/creatures/mm7_m190/review_variants.py
```

Open viewer.html directly for offline native/enhanced playback, palette selection, masks, mirrors and timeline inspection. Rebuilds require renewed visual acceptance; manifest existence alone is not completion.

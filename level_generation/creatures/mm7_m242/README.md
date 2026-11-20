# MM7 ghost — validated, staged only

All 124 native frames are restored: five standing, 40 flight, 40 attacks, 30 recoil, four frontal fidget, four collapse and one corpse. All are referenced. Eighteen selected sheets and all 19 built-in imagegen outputs, exact prompts and references remain in generation.json. The second rear recoil sheet corrects two upright poses to expose the skull during the native backward lean.

Base palette 244 preserves the dark umber robe, yellowed ivory skeleton, black sockets and fine ragged silhouette. Enhanced-art R8 cloth masks derive gray-white 243 and near-black 245 using fixed native pixel-frequency-weighted luminance-to-RGB fits over ACT indices 84–250. Weighting by actual source usage corrected an initially weak gray/black tonal range. Bone hue exclusions and four authored enhanced hand regions protect fingers from robe recoloring. No alternate palette art was generated; base bypass is exact and alpha is unchanged.

Descriptors 268/269/270 bind m243/m244/m245 groups at native default scale 1 with Center. Logical canvas 256×256, bottom pivot (128,256), 2× physical export. All frames last 125 ms. Standing uses sa, flight/walk wa..wh, attack/shoot aa..ah, hit na..nf. Death uses na0 nb0 da0 db0 dc0 dd0; corpse holds xa0; fidget uses fa0..fd0. Five stored views and mirrors 5–7 are preserved; death/corpse/fidget use native Image1 reuse. The disconnected hands and flat cloth collapse retain their native placement.

Processing uses tone 0.80, magenta core tolerance 24, warm protection, connected extraction with one anatomical scale per batch, and native baseline registration. Collapse uses the exact fixed grid to preserve disconnected bones. Material edge hue repair and exclusion of magenta interior samples correct demonstrated fine finger/robe fringe at unchanged alpha and luminance before premultiplied Lanczos resizing. Before-repair contacts remain under review/checkpoints. Raw generated dimensions are recorded per attempt; generated detail differs from 2× export size.

Two shared RGBA8-base/R8-mask pages measure 2048×3973 and 2048×359. Decoded base plus masks including padding is 44,359,680 bytes (42.31 MiB); tight crops use 39,602,055 bytes. All palettes share this allocation.

All 124 native/restored pairs and 372 palette combinations were reviewed in ordered contacts across native sequences. Final hand exclusions, mask overlays, corrected cloth and light/dark edges were inspected. Browser captures verify mirrored gray recoil and black Image1 collapse. validation.json passes source hashes, exact crop reconstruction/extraction, timings/flags, mask weights, base bypass and variant alpha; cleaned and final atlas edge audits have zero candidates above 32. review/acceptance.json pins reviewed artifacts. Fine surface detail is an interpreted restoration. No original edits or gameplay installation.

Reproduce offline in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m242 --tone .80
python3 level_generation/creatures/mm7_m242/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m242
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m242
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m242
python3 level_generation/creatures/mm7_m242/review_variants.py
```

Open viewer.html locally. Reuse accepted checkpoints, rerun only affected stages, and renew acceptance after changes.

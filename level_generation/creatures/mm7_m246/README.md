# MM7 goblin — validated, staged only

All 124 native frames are restored: five standing, 40 walking, 40 attacks, 30 recoil, five frontal fidget-named poses, three collapse and one corpse. All are referenced. Twenty-eight selected built-in imagegen sheets, exact prompts and references remain in generation.json. All 33 raw outputs are preserved. Fifteen new four-pose sheets replace the five undersampled attack sheets, restoring all 40 attack poses while reusing 84 reviewed poses. The minimum actual generated sampling is 2.032203 pixels per native pixel; no enlarged undersampled sheet remains selected.

Base palette 248 preserves green skin, reddish brown hair, brass crest/armor, blue-teal vest, navy trousers and bracers, brown boots and the native split silver blade with burgundy inner shading. Enhanced RGB8 masks use R for vest and G for trousers/bracers; B is reserved zero. Native ACT indices 156–180 and 181–254 guide independent fixed luminance-to-RGB fits for olive/green 247 and red/brown 249. Pixel-frequency and inverse squared native luminance weighting preserve the dominant dark cloth tones. This corrects the initial muted trouser colors. Blue chroma and G/B material separation keep navy highlights out of the vest mask. Skin, hair, brass, boots and blade stay protected; no alternate palette art was generated. Base bypass is exact and alpha is unchanged.

Descriptors 271/272/273 bind m247/m248/m249 groups at native default scale 1 with Center. Logical canvas 256×256, bottom pivot (128,256), 2× physical export. Every frame lasts 125 ms. Standing/fidget use sa; walking wa..wh; attack/shoot aa..ah. Hit uses na..nf followed by fa0..fe0, with Image1 reuse on the final five poses. Death uses na0 nb0 nc0 da0 db0 dc0 xa0 dc0: the repeated collapse after the corpse is native and retained. Corpse holds xa0. Five stored views and mirrors 5–7 are preserved; death/corpse use Image1 reuse.

Processing uses tone 0.80, magenta core tolerance 24, warm protection, connected pose extraction with one anatomical scale per batch, native baseline registration and premultiplied Lanczos resizing. Native burgundy blade shading is intentional and retained. Raw generated dimensions are recorded per attempt; generated detail differs from 2× export size.

Two shared RGBA8-base/RGB8-mask pages measure 2048×4011 and 2048×3082. Decoded base plus masks including padding is 101,685,248 bytes (96.97 MiB); tight crops use 91,525,924 bytes. All palettes share this allocation.

All 124 native/restored pairs, 372 palette combinations and all enhanced mask overlays were reviewed in ordered contacts. Light/dark edges were inspected; cleaned and final atlas audits have zero candidates above 32. Earlier browser captures verify the green Image1 hit tail and final red collapse; renewed captures verify mirrored green attack and playing red rear attack. All 40 replacement poses, 120 palette appearances, corresponding enhanced masks and final light/dark edges were inspected. Prior acceptance is retained for the 84 reused poses. validation.json passes source hashes, exact crop reconstruction/extraction, timings/flags, mask weights, base bypass and variant alpha. review/acceptance.json pins reviewed artifacts. Fine surface detail is an interpreted restoration. No original edits or gameplay installation.

Reproduce offline in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m246 --tone .80
python3 level_generation/creatures/mm7_m246/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m246
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m246
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m246
python3 level_generation/creatures/mm7_m246/review_variants.py
python3 level_generation/creatures/mm7_m246/review_masks.py
```

Open viewer.html locally. Reuse accepted checkpoints, rerun only affected stages, and renew acceptance after changes.

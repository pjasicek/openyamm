# MM7 fire elemental — validated staged restoration

All 108 native frames are restored: 6 front idle/fidget, 40 moving poses, 25 attack poses,
30 reactions, 6 extinction poses and 1 ash corpse. Seventeen accepted raw sheets retain the
crimson body, pale eyes, orange/gold flames, curved attack jets and charcoal-to-ash sequence.
The last moving sheet succeeded on resume after two earlier service rejections; all request
records, exact prompts, raw outputs and selections remain in generation.json.

Descriptors 238–240 share palette 496 from the explicitly hashed MM8 pal496.act. Their native
scales are 1.099991, 1.5 and 2.0. Native stored views, direction mirrors and Lit/Center flags
are preserved. At 125 ms per entry: idle/fidget 6, walk 8, attack/shoot 11 (including native
frame reuse), hit 6, death 6 and corpse 1. Death/corpse hold the last entry. No extra native
poses or palettes were invented. The matching zero R8 masks express the single exact-bypass variant.

The 2× export preserves logical canvas 256×256 and bottom-center pivot (128,256), with explicit
crop origins. Shared atlas pages are 2048×4083 and 2048×616; RGBA8 base plus R8 masks and padding
use 48,117,760 decoded bytes (45.89 MiB). Actual accepted raw dimensions are recorded per sheet;
2× export resolution is distinct from generated detail. Open viewer.html locally for playback,
native/restored comparison, all descriptor scales/views, mask overlay and light/dark backgrounds.

Processing uses tone 0.90, magenta core tolerance 8, protected warm contours, no green neutralization,
connected pose extraction, a common uniform scale per batch and native baseline placement.
Premultiplied Lanczos resizing and local contour repair precede matching atlas crops and padding.
All 108 native/restored poses in comparison_0.png through comparison_5.png were visually reviewed.
Animation order, timing, mirrors and scales were checked against source groups; browser captures
show the mirrored attack jet and low ash corpse. Cleaned and final atlas contours were inspected
on light/dark backgrounds. All validation.json gates pass, including source hashes, full coverage,
unclipped raw silhouettes, exact crop reconstruction/extraction, base bypass, mask/alpha and native
flags/timing. The residual spill audit has zero candidates above 32. Acceptance hashes freeze
these reviewed outputs in review/acceptance.json.

Reproduce from the repository root:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m202 --tone 0.90
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m202
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m202
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m202
```

Staged only; originals and gameplay untouched. Fine flame shapes, baked shading and estimated
single-background edge opacity remain artistic approximations. Re-review affected outputs after changes.

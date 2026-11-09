# MM7 golem — staged native restoration

Open [viewer.html](viewer.html) directly for native/restored animation, native mirrors, descriptor selection,
all three palettes, matching mask overlays and light/dark backgrounds. Nothing is installed into gameplay.

All 120 native unique frames are restored: five standing, 40 walking, 40 attack, 25 reaction, five fidget,
four collapse and one corpse. Descriptors 277–279 retain palettes 255/256/257 and native scale 1.299988.
Five stored directions and three mirrors are preserved. Collapse, corpse and fidget retain Image1 behavior.
All native frame durations are 125 ms. The six-phase death sequence reuses na0/nb0 before da0–dd0.
Logical size remains 256×256, Center enabled, with bottom pivot (128,256); crop offsets and storage origins
preserve native placement. No new poses or palette artwork are generated.

Twenty built-in imagegen outputs are retained, with 18 selected sheets. Targeted a_1/a_3 v2 repairs restored
clear margins around extended hands. Prompts, raw outputs, reference hashes and selected versions are in
generation.json. Shared sequence crops have six native pixels of padding; detail_budget.json records layouts
chosen against observed output sizes. All native foreground pixels reconstruct exactly from these crops.
Minimum measured generated detail is 2.348661 pixels per native pixel, independently of the 2× runtime export.
Do not rerun prepare.py over these revised crops and batches.

The gold statue, ivory horns, black collar/cuffs and green striped headdress/loincloth retain native colors
and tonal weight. A fixed 0.80 RGB multiplier and shared sheet registration preserve restrained highlights.
Demonstrated pink contour contamination is corrected using nearest opaque material hue at unchanged luminance
and alpha, before and after resizing. All source art remains unchanged.

Two enhanced-art coverage masks distinguish dark and light green cloth stripes; native palette differences
identify recolorable materials but native masks are not enlarged onto the new artwork. Cloth-weighted local
brightness separates painted stripes consistently through shadows, with soft alpha-normalized boundaries.
Fixed pixel-frequency-weighted native ACT luminance-to-RGB transforms plus frozen standing shade calibration
produce blue/cyan and red/tan palettes. Gold, ivory and black materials are protected. The base preset bypasses
recoloring exactly. variants.py and processing_settings.json preserve the complete deterministic settings.

Runtime RGBA8 base pages occupy 49,807,360 bytes and matching RGB8 masks 37,355,520 bytes: 87,162,880 decoded
bytes (83.125 MiB), including atlas padding. Tight base/mask pixels occupy 78,275,946 bytes. Preview images and
the self-contained viewer are excluded from runtime memory. Four-pixel crop padding and invisible edge RGB
extrusion support filtering; placement metadata identifies the exact shared base/mask rectangles.

Review covers all 120 native/restored poses, 360 palette appearances, all cloth mask overlays, native ordered
sequences, mirrored attack and collapse viewer captures, and final light/dark edge closeups. Coverage, source
hashes, sampling, raw cell margins, exact crop/atlas reconstruction, alpha, mask weights, timing and native
flags pass validation.json. Final residual spill checks report zero candidates above 32. Fine surface and
facial details are interpretations of the low-resolution native artwork.

Reproduce from retained selected artwork:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m254 --tone .80
python3 level_generation/creatures/mm7_m254/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m254
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m254
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m254
python3 level_generation/creatures/mm7_m254/review_variants.py
python3 level_generation/creatures/mm7_m254/review_masks.py
python3 level_generation/creatures/mm7_m254/review_identity.py
```

Wait for packaging before building the viewer and reviews. Reinspect changed outputs and renew acceptance
hashes after changes. All artifacts remain staged under level_generation/creatures/.

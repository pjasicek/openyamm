# MM7 leather fighter — validated, staged only

All 120 native frames are restored: five standing views, 40 walk, 40 attack, 25 hit, five frontal fidget and five death/corpse images. Every frame is referenced by native groups; none were omitted. Twenty selected sheets use built-in imagegen, with twenty-three raw outputs retained. The profile reaction sheet n_2 v2 repairs m226nd2's incorrectly broad sword face to the native narrow edge-on rotation. Original v1 and exact repair prompt remain in generation.json and prompts/submitted/.

Base palette 52 preserves the green jacket, collar, hair tie and small laced thigh panel. A soft enhanced-art R8 coverage mask derives blue 228 and red 229 through fixed native ACT RGB fits over green entries in 146–252. Brown-black hair, pale skin, silver blade and fittings, brown shoulder yoke and trousers, dark boots and brass remain protected. No alternate palette artwork was generated. Final mask review exposed cool metal/boot highlights in the original chroma classifier. Strong green seeds now require (G-R)/G > 0.30 and G > 1.25B, with positive G-B support; every final palette appearance was rechecked. variants.py records connected chroma selection, alpha-normalized smoothing and fixed transforms; base is an exact bypass and alpha is unchanged.

Native descriptor bindings 256/257/258 use groups m227/m228/m229. All frames last 125 ms and retain scale 0.899994 and Center flags. Native logical canvas is 256×256 with bottom pivot (128,256); physical masters are 2×. Standing/walk/attack/hit store views 0–4 and native mirrors 5–7. Death, corpse and fidget retain Image1 reuse in all eight directions. Standing holds sa, walk uses wa..wh, attack and shoot share aa..ah, hit na..ne, death na0 nb0 da0 db0 dc0 dd0, corpse holds xa0 and fidget fa0..fe0.

Four overlapping six-pose detail sheets replace the sixteen oblique/rear attack poses; repeated transition references are exported once. All 120 frames now meet actual generated sampling of at least 2.020869 pixels per native pixel. Prior accepted metadata is preserved under checkpoints/before_sampling_repair. Processing uses tone 0.80, matte core tolerance 24, warm contour protection, connected pose extraction and one common anatomical scale per batch, with native baseline registration and premultiplied Lanczos resizing. All raw, cleaned and aligned masters plus registration and settings are retained.

Two shared base/R8-mask atlas pages measure 2048×3828 and 2048×2521. Decoded base plus masks and packing uses 65,013,760 bytes (62.00 MiB); tight crops would use 58,064,650 bytes. Palette variants share this allocation. Preview PNGs are deterministic offline review outputs.

All 120 native/restored pairs and all 360 palette combinations were visually reviewed through ordered contacts, including full native action sequences, collapse and held corpse. The corrected profile reaction and blue mirrored hit browser capture were reviewed; red Image1 death capture verifies native placement and timeline metadata. Light/dark worst-edge contacts and all-frame cleaned/final extraction audits show no confirmed matte fringe. Source hashes, exact crop reconstruction, atlas extraction, mask weights, unchanged variant alpha, base bypass, timings and flags all pass validation.json. review/acceptance.json pins reviewed artifacts. Surface detail is a faithful interpreted restoration, not recovered original high-resolution art. No engine installation or gameplay edits were made.

To reproduce the accepted offline package from retained raw sheets, run in order from the repository root:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m226 --tone 0.80
python3 level_generation/creatures/mm7_m226/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m226
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m226
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m226
python3 level_generation/creatures/mm7_m226/review_variants.py
```

Open viewer.html locally for native/restored animation, palette, mirror and mask comparison. Reuse this accepted checkpoint; rerun only stages affected by demonstrated changes, then renew visual acceptance before refreshing inventory.

# MM7 dragonfly — validated offline restoration

All 125 native frame names (124 unique pixel images) are restored across palettes 187–189 and descriptors 226–228. Open `viewer.html` for native/restored playback, palette masks and mirrored views. Assets are staged only; originals are unchanged and nothing is installed into gameplay.

The 38 selected built-in imagegen sheets preserve the thin segmented brown-gray body, pale belly plates, green dorsal spines, orange eyes, ivory jaws, gold bristles and forked tail, and translucent gray wings with red-brown veins. All 52 raw outputs and exact submitted prompts remain recorded in `generation.json`. The sampling repair generated 34 compact sheets, replacing 99 frames while retaining 26 prior frames with exactly unchanged registration. Minimum actual generated sampling is **2.1411042944785272 pixels per native pixel**, measured before the 2× export resampling. No replacement uses interpolation to claim missing generated detail. Native palette variants are derived offline from shared base artwork.

Sixteen selected replacement sheets contain genuine RGBA transparency; the other selected sheets retain their original magenta matte. The first eight RGBA deliveries differed from the submitted magenta request; the final eight explicitly request transparency following the user's preference. Their earlier unsubmitted prompt drafts are retained in `checkpoints/before_alpha_request/`. `process.py` preserves all delivered alpha except disconnected gutter components whose maximum opacity is only 1/255. Complete soft edges of every stronger component remain unchanged during extraction. Numeric evidence is in `review/native_alpha_delivery.json`; final light/dark composites were inspected with no painted checkerboards.

Coverage includes 117 referenced frames and eight additional family-owned images: ah0, ah4, dg0 and nh0–4. These unused frames are exported without invented playback bindings. Native df0 and dg0 have identical pixels; `preserve_aliases.py` preserves their exact enhanced-art identity. Standing/walk use eight wa–wh poses; attack/shoot use seven aa–ag; hit uses seven na–ng. Death uses na0, nb0, nc0, da0, db0, dc0, dd0, de0, df0; corpse holds xa0; fidget uses wa0, wb0, na0, wd0, we0. Timed poses remain 125 ms. Five stored views, mirrors 5–7, Image1 action reuse, Center flags, logical 256×256 canvas, bottom pivot (128,256), and native scales 0.5/0.699997/1.199997 are preserved.

Processing uses tone 0.80, warm contour protection, core threshold 24, connected pose extraction, a common anatomical scale per sheet, matte extraction for opaque RGB sheets or preservation of genuine RGBA, and premultiplied 2× resizing. Enhanced-art R8 masks recolor green dorsal spines to native blue/red variants through fixed ACT RGB fits. Eyes, neutral wings, brown shell and gold tail remain protected. Palette 187 bypasses exactly; variants preserve alpha.

Three RGBA8 base/R8 mask page pairs measure 2048×4036, 2048×3882 and 2048×881. Decoded shared memory including packing and masks is 90,101,760 bytes (85.93 MiB). Placement, animation and variant metadata accompany aligned masters, tight crops and the self-contained viewer.

Review covered every replacement with its native reference, all 297 replacement frame/palette appearances and their masks, ordered front/rear flight, profile attack, front/oblique recoil and the collapse sequence. The 26 retained frames reuse prior visual acceptance. Final mirrored blue-spine recoil, green profile attack and playing red-spine collapse browser captures were inspected, along with enlarged light/dark edges and RGBA composites. Native df0/dg0 remain exact enhanced aliases. All package validation checks pass: source hashes, full coverage, actual sampling >=2, unclipped raw poses, exact crop/atlas reconstruction, native timing/flags, valid masks, unchanged variant alpha and exact base bypass. The final edge audit reports zero residual candidates above 32. No family blockers remain.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m186/process.py
python3 level_generation/creatures/mm7_m186/preserve_aliases.py
python3 level_generation/creatures/mm7_m186/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m186
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m186
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m186
python3 level_generation/creatures/mm7_m186/review_variants.py
python3 level_generation/creatures/mm7_m186/review_repair.py
```

Reproduction requires renewed visual acceptance and refreshed acceptance hashes. Generated detail is a reviewed interpretation of native art; actual generated sampling is measured separately from export dimensions and exceeds the required 2× minimum throughout.

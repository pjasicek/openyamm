# MM7 sun cleric — validated offline restoration

All 120 native frames are restored across palettes 40–42 and descriptors 217–219. Open `viewer.html` for native/restored playback, masks and mirrored views. Assets remain staged offline, with originals unchanged and no gameplay installation.

Eighteen accepted built-in imagegen sheets preserve the gold sun mask and rays, gray rear cap, broad wavy gold mantle, scarlet striped robe, bare hands and decorated teal stole. Twenty-two raw outputs and exact submitted prompts/reference hashes are retained. Casting corrections move hand flecks to the source hand, restore missing flecks and remove an invented green rear buckle. All palette variants derive from the single enhanced base.

Coverage includes 114 referenced and six stored unused frames: we0–we4 and dd0. Standing holds sa; native walk is wa, wb, wc, wd, wf, wg, wh (we remains available without adding it to playback). Attack/shoot use aa–ag; hit na–nf. Death uses na0, da0, db0, dc0, de0; corpse holds xa0. Fidget uses fa0, fb0, fc0, fd0, fc0, fb0. Standard timed frames are 125 ms. Descriptor 217 death dc0 is 187.5 ms and de0 62.5 ms; its fidget fd0 is 250 ms. Descriptors 218/219 death frames are 125 ms and their second fc0 fidget occurrence is 250 ms. Native corpse timing metadata is retained with held playback. Death Lit flags and glow radii 64/128/256/128 remain in metadata. Five stored views, mirrors 5–7 and Image1 death/corpse/fidget reuse are preserved. Logical size is 256×256 with pivot (128,256), Center flag and native scale 1.199997.

Processing uses tone 0.90, warm contour protection, core threshold 24 and premultiplied 2× resizing. Common anatomical scale is calibrated per batch. The death sheet explicitly uses fixed cell extraction: connected nearest-pose ownership incorrectly assigned bottom-row particles to the first pose and displaced its baseline; fixed cells corrected both defects. R8 enhanced-art masks isolate the teal stole and buckle, retaining gold decoration, mask, mantle, particles, red robe, gray cap and skin. Native ACT entries within 227–238 define fixed RGB fits for violet and black; base palette 40 bypasses exactly. Connected mask support includes narrow side-view stole strips and uses alpha-normalized Gaussian feathering of 0.45 pixels.

Two RGBA8 base/R8 mask page pairs measure 2048×3912 and 2048×2604. Shared decoded memory including masks and packing is 66,723,840 bytes (63.63 MiB). Placement, animation, palette and descriptor metadata accompany aligned masters, tight crops and the self-contained viewer.

Review covered all 120 native/restored frames, all 360 frame/palette combinations, native palette references, ordered action sequences, enlarged light/dark edges, mirrored violet casting and black Image1 death browser captures. All package checks pass for native sources, complete coverage, unclipped raw cells, exact crop/atlas reconstruction, timing/flags, mask weights, unchanged variant alpha and exact base bypass. Residual edge candidates above 32: zero. No family blockers remain.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m174 --tone .90
python3 level_generation/creatures/mm7_m174/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m174
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m174
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m174
python3 level_generation/creatures/mm7_m174/review_variants.py
```

Reproduction requires renewed visual acceptance and refreshed hashes. Generated detail is a reviewed interpretation of native artwork; physical 2× export does not imply identical generation resolution per pose.

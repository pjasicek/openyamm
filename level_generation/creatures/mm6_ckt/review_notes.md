# Cockatrice review and reproduction

Accepted all 59 unique native images: 58 referenced and unused cktwncf0. All five stored views, mirrored aliases, native timing, scale, logical size and anchoring are preserved. Native hit bindings use death-pose images; the unused/separate wince artwork is also covered without rewriting native bindings.

Reviewed all native/raw sheets, ordered base/mask contacts, standing palettes, magnified light/dark contours and offline viewer comparisons: mirrored walk view 6 / palette 682 / frame 4, hit view 0 / palette 680 / frame 3. All walking leg phases, lifted wings, head-turn fidget, talon-first attack and collapsed corpse follow native silhouettes. Enhanced mottled wing texture and leathery body detail remain close to native, with interpretive fine creases and scales. A fixed 0.90 gain retains native tonal weight.

R8 enhanced turquoise membrane coverage protects brown body/tail, pink neck, orange beak/legs and ivory wing bones/spikes/claws. Initial green-only coverage missed cyan flecks in darker wing mottling; widened green/cyan coverage and rechecked the red mirrored profile. Final variants use fixed native-used sigma=4 luminance LUTs. Export carries the explicit masked_luminance_lut_v1 contract and exact base bypass.

All source/palette/provenance hashes, complete coverage, exact crop and atlas reconstruction, variant alpha, protected material and native sequence checks pass. Zero magenta candidates in cleaned images, exported tiles and atlas extraction. No demonstrated contour spill remains. Contacts and paused-viewer checks are not GPU performance measurements.

Rebuild from repository root:
```
python3 level_generation/creatures/mm6_ckt/process.py
python3 level_generation/creatures/mm6_ckt/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py ckt
```
Rebuild resets visual acceptance. Staged only; originals and gameplay remain unchanged.

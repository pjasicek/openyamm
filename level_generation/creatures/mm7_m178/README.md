# MM7 devil — validated offline restoration

All 120 native frames are restored across palettes 44–46 and descriptors 220–222. Open `viewer.html` for native/restored playback, masks and mirrored views. Assets remain staged offline, with originals unchanged and no gameplay installation.

Twenty-nine selected built-in imagegen sheets (35 preserved raw outputs) preserve the ochre-brown pebbled hide, long arms and oversized clawed hands, thin spiked tail, ivory shoulder spikes, slate-violet chest plates and feet, and bright yellow eyes. All raw outputs, submitted prompts, references and hashes are retained. The native teal-green and red appearances derive deterministically from the single enhanced base.

Coverage includes all 120 referenced frames: five standing, 40 walk, 40 attack/shoot, 25 hit, five fidget, four additional death and one corpse. Standing holds sa; walk wa–wh, attack/shoot aa–ah and hit na–ne preserve five stored views and mirrors 5–7. Death uses na0, nb0, da0, db0, dc0, dd0; corpse holds xa0; fidget uses fa0–fe0. Death, corpse and fidget retain Image1 reuse across all eight views. Native timed frames are 125 ms. Logical size is 256×256 with pivot (128,256), Center flag and descriptor scale 1.

Processing uses tone 0.80, warm contour protection, core threshold 24, connected pose extraction, common anatomical scale per batch and premultiplied 2× resizing. RGB8 enhanced-art masks use red for hide and green for ventral plates; blue is zero. Native ACT hide entries selected from 140–215 and plates from 60–87 define fixed RGB fits. Base palette 44 bypasses exactly. Targeted bright-yellow eye exclusions correct the demonstrated eye recoloring spill; ivory spikes, claws and teeth remain protected. Masks use alpha-normalized 0.45-pixel Gaussian feathering.

Shared decoded atlas memory including RGBA8 base, RGB8 masks and packing is 118,530,048 bytes (113.04 MiB); tight content is 106,153,187 bytes. Placement, animation, palette and descriptor metadata accompany aligned masters, tight crops and the self-contained viewer.

Review covered all 120 native/restored frames, all 360 frame/palette combinations, native palette references, ordered action sequences, enlarged light/dark edges, mirrored teal-green attack and red Image1 death browser captures. All package checks pass for native sources, complete coverage, unclipped raw cells, exact crop/atlas reconstruction, timing/flags, mask weights, unchanged variant alpha and exact base bypass. Residual edge candidates above 32: zero. No family blockers remain.

Sampling repair replaced 45 attack/front-hit frames with 17 compact sheets and reused 75 registrations unchanged. Every frame now has at least 2.010030190 actual generated pixels per native pixel. All 45 replacements, their 135 palette appearances and masks, ordered native comparisons, light/dark edges, mirrored teal attack and playing red hit were reviewed. The neutral-gray plate mask was extended using broad enhanced-art connected surfaces; fifteen reviewed side-eye exclusions in `eye_regions.json` prevent eye recoloring. Thin ivory spikes and claws remain protected.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m178 --tone .80
python3 level_generation/creatures/mm7_m178/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m178
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m178
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m178
python3 level_generation/creatures/mm7_m178/review_variants.py
```

Reproduction requires renewed visual acceptance and refreshed hashes. Generated detail is a reviewed interpretation of native artwork; physical 2× export does not imply identical generation resolution per pose.

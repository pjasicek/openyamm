# Harpy acceptance

Accepted 2026-09-13: all 48 unique native images, 9 batches, five stored flight views and mirrors; palettes 751/752/753. Standing and fidget reuse the six-moment native flight sequence with 187.5 ms timing and original scale/anchoring. Every native/raw sheet and final base/mask contact was visually reviewed, plus three palette rows, worst-edge contact and offline viewer mirrored flight view 6/palette 753/frame 3, attack palette 752/frame 2 and death palette 751/frame 4.

Flight wing angles, forward talon attack, raised-arm hit and folded fall/corpse remain distinct and correctly placed. One enhanced-art R8 mask covers green chest and inner-wing feathers; usage-weighted native luminance LUTs derive red and blue while protecting skin, brown flight feathers, spotted thighs and ochre talons. Base is exact bypass. Initial wrong red identity and failed deterministic color experiment are preserved as rejected; accepted color-only imagegen correction became the identity reference for all later calls. RGB gain .80 matches the native dark tonal weight.

All quick checks pass, including exact crop/atlas reconstruction, source/palette/raw provenance hashes, native bindings, unchanged variant alpha, protected zero-mask pixels and zero residual spill candidates above 16 in cleaned/exported/atlas frames. No raw cell clipping. Decoded base+R8 masks including atlas padding: 78,820,190 bytes (75.17 MiB), excluding variant previews. Physical 2x export; actual generated standing body detail is roughly 350 pixels high.

Visible limitations: feather shapes and thigh spots are more strongly modeled than the pixelated source, and fingers/talons are slightly rounder. Offline checks establish appearance and native pose order/placement, not GPU performance. Staged only; LUT-aware runtime loading or deterministic baking is required before gameplay installation.

Palette maintenance: corrected copied blue-channel luminance coefficient to standard .0722 and regenerated LUTs/package. Base and masks unchanged, updated three-palette contact visually rechecked; all structural and zero-spill checks still pass.

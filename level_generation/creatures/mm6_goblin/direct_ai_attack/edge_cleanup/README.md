# Deterministic edge cleanup of the approved AI attack sheet

[Before/after guard comparison](guard_before_after.png): untouched generated RGB, previous alpha-only key,
and new color-decontaminated RGBA. Top/bottom use dark/light backgrounds. Enlargements use nearest-neighbor
solely to expose existing pixels.

- [Transparent 3×2 sheet](attack_cleaned_3x2.png).
- [Transparent 1×6 strip](attack_cleaned_1x6.png), six 601×508 cells.
- [Individual RGBA frames](frames_rgba/), fixed previous canvas positions.
- [Playback](attack_cleaned.gif), original total duration 0.75 seconds.
- [Light](all_frames_light.png) and [dark](all_frames_dark.png) review of all six figures.
- [Raw generation versus previous extraction](raw_vs_old_guard.png).

## Cause

The pink contour exists in `../attack_restored_v1.png`, before our extraction or preview resizing. Every opaque
frame crop was checked against its original generated-sheet rectangle: RGB is identical. The previous RGBA key
also retains exactly those RGB values wherever alpha is nonzero. It changes transparency only. Resizing was used
later for comparison previews; it did not originate the pink in the saved full-resolution RGBA frames.

A flattened mixed edge approximately follows `C = alpha * F + (1 - alpha) * B`, where C is observed RGB, F is
foreground and B is background. Setting alpha without subtracting the background contribution leaves a colored
fringe. Exact RGB-magenta replacement misses mixed pixels and variations in the generated background. The generator
may also paint colored reflections: an image alone cannot distinguish those from ordinary antialiasing. Original
foreground color and alpha are not uniquely recoverable from a single flattened RGB image.

## Cleanup and limits

`../clean_edges.py` runs locally with NumPy, SciPy and Pillow; no model/API generation is involved. It estimates
nearby reliable foreground and magenta background colors, fits alpha along their RGB mixture, subtracts the estimated
background contribution, and limits remaining magenta excess. It assumes this character has no intended magenta
material. Clean foreground RGB (magenta dominance ≤8/255) stays byte-for-byte unchanged, verified on all six frames.
No poses, per-frame scale or alignment are regenerated. The approved raw sheet and old extraction are preserved.

Inspection on light/dark backgrounds shows substantially less pink fringe, including the reported guard. This remains
an estimated matte: very thin details without a reliable foreground core can become softer or acquire a color bias.
Bronze/pinkish interior blade pigment is not necessarily background spill and is not globally recolored. Lower measured
magenta alone is not proof of perfect material/shape recovery. All crops have actual alpha and remain unclipped.
`validation.json` records bounds and affected pixel counts.

## Future workflow using current tools

Keep the approved original-size RGB generation. Extract a soft matte AND decontaminate edge RGB before resizing.
Save an RGBA master, then resize with premultiplied alpha; inspect on bright/dark backgrounds and in motion. Avoid
regenerating approved figures just to remove a background, since that can change their design and poses.
Magenta is useful for separating this green/brass/iron character, provided its edge contribution is cleaned up.
A neutral-background experiment might reduce colored spill but makes gray metal harder to separate; it has not
been tested here. Separately AI-generated black/white versions are not guaranteed to match pixel-for-pixel and must
not be treated as a mathematically exact pair for alpha extraction.

Reproduce from the repository root:

```sh
python3 level_generation/creatures/mm6_goblin/direct_ai_attack/clean_edges.py
```

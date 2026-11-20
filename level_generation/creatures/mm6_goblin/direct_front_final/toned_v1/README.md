# Goblin front: darker color trial

This is a reversible deterministic color grade of the restored front set, prompted by the brightness comparison in
`test_img/1257.png`. No AI generation was used. The driver accepted this darker appearance after reviewing the trial;
it remains a separate derivative so the brighter reconstruction masters are retained.

- [Original / restored master / darker variant comparison](comparison.png), on light and dark backgrounds.
- [Animation viewer](review.html): native original on the left, darker variant on the right.
- [Complete 2x transparent sheet](front_all_actions_2x.png).
- [All actions on dark](previews/all_actions_dark.png) and [light](previews/all_actions_light.png).
- `aligned_1x/`, `aligned_2x/`, `trimmed_1x/`, `trimmed_2x/`, and `action_sheets_2x/` contain the complete 31-frame set.
- [Manifest](manifest.json) retains the original timing, dimensions, offsets, pivots, and atlas coordinates.

The grade applies the same fixed sRGB luma curve to every pixel in every frame. Input/output curve points are
`0→0, .08→.08, .20→.181, .40→.348, .65→.552, 1→.90`. RGB scales together by the resulting luma ratio, followed by
a subtle cool balance of `R×.98, G×1, B×1.02`. Midtones and highlights are subdued; very deep shadows are largely
preserved. The balance reduces the yellow warmth slightly. This is an artistic display-space adjustment, not
physical relighting or a per-frame histogram match. There is no material segmentation that could vary between poses.

The alpha channel is copied exactly. Fully transparent pixels are also retained. All 31 frames in both resolution
tiers have unchanged silhouettes and alignment. The trimmed exports reconstruct their aligned counterparts exactly;
atlas alpha/layout is unchanged. Master file hashes are verified unchanged. Texture allocation and runtime crop
support requirements are identical to the [original delivery](../README.md).

Rebuild from the repository root:

```bash
python3 level_generation/creatures/mm6_goblin/direct_front_final/tone_variant.py
```

Use `--preview` to rebuild only the three-column comparison. Native artwork and the brighter restored masters remain
in their existing locations. Inspect this trial in the viewer before choosing a color target for eventual in-game use.

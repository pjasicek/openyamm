# MM6 Cobra restoration

Accepted staged descriptors 493–495: 59 native source frames, 53 unique enhanced images, all native actions/views, palettes 677/678/679. Open `review.html` directly for animation stepping, mirrors and native comparisons. Review evidence and limits are in `review_notes.md`.

2× shared RGBA8 base and RGBA8 material-mask atlases: 111,195,464 decoded bytes including padding (106.04 MiB), 10,393,212 shipping bytes. Long native side-view tails account for broad frames. Three material channels are used; preview PNGs are offline only. Future installation needs the staged multi-region recolor contract.

Rebuild from repository root:

```sh
python3 level_generation/creatures/mm6_cob/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py cob
python3 level_generation/creatures/mm6_peasants/build_viewer.py cob
```

Packaging resets visual acceptance. Preserve prompts, raw sheets including rejected walk_1, correction provenance, registration, material settings and back_ring_views.json. No originals overwritten or gameplay installation.

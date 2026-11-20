# MM6 Sorcerer restoration

Accepted staged descriptors 631–633: all 59 native unique poses, palettes 819/820/821. Open `review.html` directly for native/enhanced animation stepping, mirrors and variants. Review evidence and interpretation limits are in `review_notes.md`.

2× shared RGBA8 base and RGBA8 material-mask atlases: 70,431,376 decoded bytes including padding (67.17 MiB), 8,758,807 shipping bytes. Only two mask channels are used; preview images are offline only. Metadata describes the staged multi-region recolor contract, requiring compatible future loading support before installation.

Rebuild from repository root:

```sh
python3 level_generation/creatures/mm6_sor1/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py sor1
python3 level_generation/creatures/mm6_peasants/build_viewer.py sor1
```

Packaging resets visual acceptance. Preserve prompts, raw sheets, source hashes, registration, material/landmark processing and tone settings. The generic key-color audit flags intentional purple; consult reviewed evidence rather than erasing the robe to force a zero score. No originals overwritten or gameplay installation.

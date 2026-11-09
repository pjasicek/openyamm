# MM6 Spider restoration

Accepted staged restoration of descriptors 634–636: all 58 native unique images/actions/views, palettes 822/823/824. Open `review.html` directly for native/enhanced animation stepping, mirrors and variants. See `review_notes.md`, `validation.json` and `acceptance.json`.

2× shared RGBA8 base and R8 material-mask atlases: 31,197,125 decoded bytes including padding (29.75 MiB), 5,456,325 shipping bytes. Variant PNGs are offline previews only. Actual generation sizes and provenance are retained.

Rebuild from repository root:

```sh
python3 level_generation/creatures/mm6_spi1/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py spi1
python3 level_generation/creatures/mm6_peasants/build_viewer.py spi1
```

Packaging resets visual acceptance. Preserve raw sheets, rejected checkpoints, prompts, enhanced masks and settings. Originals and gameplay remain unchanged.

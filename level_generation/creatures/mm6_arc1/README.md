# MM6 Archer restoration

Validated and staged only. Open [review.html](review.html) for native/enhanced animation and palette comparison.
58 unique native images, 57 referenced, three native palettes (660/661/662), five stored views and native mirror aliases.
All original actions and timings retained. One restored base plus R8 cloth coverage; native images are unchanged.

[Review notes](review_notes.md), [validation](validation.json), [generation provenance](generation.json),
[source inventory](sources.json), [atlas manifest](manifest.json).

Rebuild after an intentional revision:

```bash
python3 level_generation/creatures/mm6_arc1/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py arc1
python3 level_generation/creatures/mm6_peasants/build_viewer.py arc1
```

Rebuilding resets visual acceptance; inspect changed results before marking validated again. Preparation scripts
recreate native references and metadata but do not issue AI calls. Preserve raw sheets and submitted prompts.

Runtime pages: 3 RGBA8 base pages plus matching R8 masks, 39.31 MiB decoded including packing (before any mipmaps).
Shipping manifest and atlas PNGs are about 6.69 MiB. Review PNGs and aligned masters are offline authoring artifacts.

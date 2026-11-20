# MM6 Thief restoration

Accepted staged restoration of descriptors 637–639. 59 native BMPs / 58 unique images, all native actions/views and palettes 825/826/827. Open `review.html` directly for native/enhanced animation stepping, mirrors and variants. Review evidence: `review_notes.md`, `validation.json`, `acceptance.json`.

2× manifest with shared RGBA8 base and R8 material mask atlases: 37,218,000 bytes decoded including padding (35.49 MiB), 8,884,674 bytes for manifest/atlas files. Preview PNGs are offline only. Actual 1465×1073/1074 generation dimensions are recorded; runtime geometry is 2× with necessary resampling.

Rebuild from repository root:

```sh
python3 level_generation/creatures/mm6_thf/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py thf
python3 level_generation/creatures/mm6_peasants/build_viewer.py thf
```

Packaging resets visual acceptance. Prompts, original raw sheets including rejected hit draft, accepted correction, source/variant hashes, registration and tone settings are retained. No originals overwritten or gameplay installation performed.

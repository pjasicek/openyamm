# MM6 Merchant restoration

Accepted staged 2× restoration: 58 unique native frames, all actions and stored views, descriptors 577–579, palettes 252/253/770. Open `review.html` directly for native/enhanced comparison, animation stepping, mirrors and variants. See `review_notes.md`, `validation.json` and `acceptance.json`.

Runtime output is `manifest.json` plus its referenced base/mask atlases. Decoded padded base plus R8 mask: 40,853,020 bytes (38.96 MiB); manifest/atlas files: 8,393,755 bytes. Offline previews are excluded. Actual generated dimensions are recorded in `generation.json`; 2× is export geometry, with resampling where needed.

Rebuild from repository root:

```sh
python3 level_generation/creatures/mm6_mer1/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py mer1
python3 level_generation/creatures/mm6_peasants/build_viewer.py mer1
```

Packaging resets visual acceptance; review changed output before accepting again. Exact submitted prompts, raw generator outputs, source hashes, registration and fixed tone settings are retained. No original assets overwritten; no gameplay installation.

# MM6 Dwarf restoration

Accepted staged package: [offline viewer](review.html), [manifest](manifest.json), [validation](validation.json), [visual review](review_notes.md).

59 unique native images (58 referenced), all actions/stored views/mirrors and three palette appearances. One 2× base with matching two-region RGBA8 coverage pages; native originals are unchanged. Decoded base plus mask pages including atlas padding: 60,240,792 bytes (57.45 MiB). Shipping manifest and atlas PNGs: 8,137,768 bytes. Variant preview pages are offline review assets and excluded from runtime memory.

Rebuild from saved generation checkpoints:

```sh
python3 level_generation/creatures/mm6_dwa1/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py dwa1
python3 level_generation/creatures/mm6_peasants/build_viewer.py dwa1
```

Processing uses `materials.py`, `hem_overrides.json`, recorded native offsets and a fixed 0.90 RGB gain. Raw outputs and exact submitted prompts are in `raw/`, `prompts/` and `generation.json`. Repackaging resets visual acceptance; review changed output before setting it again.

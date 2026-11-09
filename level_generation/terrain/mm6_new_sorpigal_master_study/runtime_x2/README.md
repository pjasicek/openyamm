# Runtime terrain materials — x2

Four selected materials, exported at **256×256 RGB PNG** from the unchanged 512×512 authoring masters.

- `materials/grass.png`: grass v1.
- `materials/dirt.png`: dirt v6.
- `materials/cobbles.png`: cobbles v1, for masked composition over dirt.
- `materials/volcano.png`: volcanic rock v2, retained with the earlier brightness note.

`overrides/worlds/mm6/terrain_x2/` contains only the three standalone native base replacements.
There is deliberately no full-tile cobble replacement. This is a partial base-material export, not a finished
terrain pack. Complete connected land and roads are in the sibling transition project; shoreline and water remain pending. No original runtime assets were installed
or overwritten by this export. The runtime terrain setting for these files is `x2`.

Build the final mixed tiles from the 512px masters and masks, then downsample the completed composites to 256px.
The standalone 256px cobble file is a runtime-sized material reference; use its 512px master for authoring roads.

`manifest.json` records selected versions, source and output hashes, roles and paths. Rebuild from the repository root:

```sh
python3 level_generation/terrain/mm6_new_sorpigal_master_study/export_runtime.py
```

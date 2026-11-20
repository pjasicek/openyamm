# Remaining MM6 material masters — v1

[Compare originals, restored masters and tiled previews](index.html).

Five imagegen masters are prepared for artistic review. `materials/` contains the 512×512 repeating masters; `runtime_x2/worlds/mm6/terrain_x2/` contains 256×256 exports. These have not replaced the current enhanced terrain or generated the remaining transitions.

| Material | Master | Runtime name | Original features retained |
| --- | --- | --- | --- |
| Sand | `materials/sand.png` | `6sandtyl.png` | Warm gold, grain and sinuous dune contours |
| Snow | `materials/snow.png` | `snotyl.png` | Near-white surface, pale cyan drift shadows |
| Cracked ground | `materials/cracked.png` | `crktyl.png` | Muted clay plates and grey/olive fissures |
| Tropical | `materials/tropical.png` | `troptyl.png` | Angular interleaving yellow/olive green forms |
| Swamp | `materials/swamp.png` | `swmtyl.png` | Olive muddy patches and baked dark teal channels |

All five used the built-in imagegen tool, with the corresponding original tile as primary reference and accepted grass as a restrained-detail reference. Sand/snow retain their distinctive ridges rather than simply recolouring grass. Prompts are in `prompts/`; raw generated files are retained in `raw/`. Tropical used a second edit (`prompts/tropical_fix.txt`) to remove an internal line, coarsen the pattern and reduce saturation. Its first output remains `raw/tropical_first.png`.

`build.py` resizes authoring to 512px, applies the same cyclic minimum-error quilting used for the accepted terrain, and downsamples using wrapped gutters. It leaves each generated master's central 384px square unchanged and does not recolour it. The runtime images are RGB, including swamp: its channels are static painted material, not transparent animated-water openings.

Both-axis local 16px seam-window checks pass for all five exports. `report.json` binds checks to source/master/runtime hashes and records palette means and border detail. Visual review covered original comparisons, 3×3 repeats and half-tile offset images. Sand/snow retain visibly recurring broad ridge motifs, as in the originals; seamless does not mean non-repeating. No in-engine terrain-transition or performance certification is claimed at this master-only stage.

Rebuild from repository root:

```sh
python3 level_generation/terrain/mm6_remaining/masters/v1/build.py
```

Next stage: create the sixty material-to-dirt transitions using the accepted shared dirt and the native directional topology, then review connected contexts and map views. Master palette/pattern acceptance should precede that work.

# Organic ground items redo — 2026-10-18

**All nine installed.** These are the herbs and flowers the [organic batch](../items_wip_organic/README.md) kept as
flat reliefs; each is now a closed 3D model lying naturally on the ground, built entirely in Blender (no image
generation, no Meshy). [Review sheet: icon / above / three-quarter / low](review/sheet_final.png).

| Icon | Item | Design | Triangles |
|---|---|---|---:|
| `rose` | Rose | Open red bloom of five cupped petal rings (inner wrap, outer turn back) on three leaves, short stem | 2052 |
| `7item269` | Flower (Rose) | Long-stem rose lying on its side: bloom, sepals, two three-leaflet leaves, thorns | 2100 |
| `7item144` | Crushed Rose Petals | Pink ruffled bloom on a short leafy stem, eleven loose curled petals scattered around it | 2664 |
| `7item147` | Dragon's Eye | Flat bronze pendant: frame torus with eight studs, red enamel ring, glossy domed slit-pupil eye, bail | 2096 |
| `item167` | Datura | White five-lobed trumpet (thick lathe shell) with green calyx, stem and a broad leaf | 1580 |
| `clover` | Four Leaf Clover | Four heart-shaped leaflets with pale chevrons, curved stem | 240 |
| `7item143` | Poppysnaps | Bunch of ten yellow five-petal flowers on stems with eleven lance leaves | 1892 |
| `herb01` | Poppysnaps (MM6) | Sprig of three stems, pale lance leaves and seven pale-yellow star flowers | 1018 |
| `item304` | Dragonbane Flower | Large red-orange five-petal flower with yellow throat streaks and stamens, leafy stem, two buds | 1264 |

## How they are built

`scripts/organic_kit.py` provides closed low-poly parts with their own UVs into one 4x4 atlas cell each: lens-section
blades for petals and leaves (pointed or rounded profiles, cup, bend, twist), tubes, tori, ellipsoids, thin-lens
star discs and outline slabs (shared outline, no sliver rim strips), and a thick surface of revolution. Cells are
painted procedurally with numpy (petal gradients and veins, leaf midribs and lateral veins, stems, radial flower
faces, metal, enamel, the slit-pupil eye) into 512 px base colour, packed metallic/roughness (G roughness, B binary
metal; only the Dragon's Eye bronze is metal) and an OpenGL tangent normal map from each cell's height field. One
single-sided material per model, embedded PNGs. `scripts/build_designs.py` holds one function per icon.

```sh
blender --background --python level_generation/props/items_organic_redo_20261018/scripts/build_designs.py -- [icon ...]
blender --background --python level_generation/props/items_organic_redo_20261018/scripts/review.py -- <icon ...>
python3 level_generation/props/items_organic_redo_20261018/scripts/contact.py sheet_final <icon ...>
```

## Checks

- Winding: 0 inverted closed parts for all nine.
- Zero exposed back faces (rays from 60 directions) and no corner normals opposing their face.
- No triangle with aspect (longest edge squared over equilateral-equivalent area) above 30.
- Centred footprint, lowest point zero; 240–2664 triangles.
- Baseline source/runtime hashes confirmed unchanged before each install (`references/`, `references/baseline_sha256.txt`);
  installed with `tools/install_model.py --world-items`; each desktop cook verified with 0 problems.
  Export, source and runtime hashes are in [receipts.json](receipts.json).

Binding lengths are unchanged and fit the new shapes; `items.yml` was not edited (bounds are recomputed by the
coordinator with `tools/item_model_shapes.py`). No game run, Android cook, build or commit.

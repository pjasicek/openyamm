# Mounted gems and harpy feather in 3D — 2026-10-18

**4 of 4 installed.** The three mounted gems the [jewellery batch](../items_wip_jewellery/README.md) kept as flat
reliefs and the harpy feather the [sculpture batch](../items_wip_sculpture/README.md) kept are now real 3D models,
built in Blender (`scripts/build_items.py`). No Meshy, no image generation.

[Icon beside above / three-quarter / low review views](review/final_sheet.png) (back faces removed as in game;
earlier iterations `review/v1`–`v3`).

| Icon | Item | Triangles | Construction |
|---|---|---:|---|
| `7item146` | Ruby | 2,768 | Pointed-oval gold back plate with engraved trim, deep garnet enamel field, closed gold rim, twelve gold filigree scrolls with beads, engraved raised bezel and four claws round a large oval ruby cabochon, two small side rubies, point beads |
| `7item154` | Yellow Topaz | 1,288 | Blackened rounded tray with rim, 30-bead gold border, stepped inner frame, gold shaped bezel and four claws round an emerald-cut golden topaz |
| `7item264` | Diamond | 1,348 | Engraved gold back and bezel, ten gold leaf claws with beads, large pale-blue round brilliant |
| `quill` | Harpy Feather | 674 | Curved closed lens-section vane (wider on its left, drooping edges, slight arch and lifted tip) with a raised tapering rachis and bare calamus, lying flat |

**Materials.** The gems reuse the jewellery batch's builders by importing `build_jewellery.py`: its palette, glass
shell over a darker solid core (glass on a separate `_glass` node, BLEND, opaque parts on the other node), bezels and
the engraved gold trim tiles from `surface_detail.py`. Three stone colours are added because the icons' stones are
more saturated than that batch's loose-gem palette (`ruby`, `topaz`, `moonblue`), plus `garnet_enamel` and a dark
dielectric `blackened` tray. The ruby and diamond carry the engraved trim textures (base colour, metallic-roughness,
normal). The topaz uses constant PBR materials only, like the batch's loose gems: the engraved tile on its tray read
mauve, so it was removed. The feather has generated 512 px base colour (cream vane, brown chevron bars, darker tip,
golden rachis column), metallic-roughness (0.72 vane, 0.45 rachis, metal 0) and barb-groove OpenGL normal maps on
parametric UVs. All materials are single-sided.

**Gates.** Every export: closed manifold parts, no degenerate faces, `check_winding.py` 0 inverted, zero exposed
back faces from 60 sampled directions, no corner normals opposing their face (applied to the glass shells too, which
are closed copies of the cores), lowest point 0, centred footprint, at most two transform-free nodes with the glass
node BLEND and the opaque node OPAQUE, UVs within 0–1. The jewellery batch's `tube()` frame (Y reference) twists
tubes running along Y, which inverted the ruby's filigree end caps; its scrolls use `flat_tube()` with a Z reference.

**Install.** Baseline source/runtime hashes were confirmed unchanged against `references/baseline_sha256.txt`, then
each export was installed with `tools/install_model.py --world-items` and passed
`tools/cook_models.py --verify --profile desktop` (`receipts/`). Installed hashes: `receipts/installed_sha256.txt`.

**Bindings.** No length change proposed: the gems keep 22.4, 22.7 and 21.1 (heights about 7, 9 and 9 units) and
the feather keeps 58.5. `items.yml` was not edited; bounds are left to the main session's `tools/item_model_shapes.py`.

Not done: no game run, Android cook, build or commit.

```sh
blender --background --python level_generation/props/items_gems_feather_redo_20261018/scripts/build_items.py [-- icon ...]
blender --background --python level_generation/props/items_gems_feather_redo_20261018/scripts/review.py -- final
python3 level_generation/props/items_gems_feather_redo_20261018/scripts/sheet.py final
```

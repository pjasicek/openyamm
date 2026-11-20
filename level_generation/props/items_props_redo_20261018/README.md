# Props redone in 3D — 2026-10-18

**11 of 11 installed.** The props batch had kept these as flat icon reliefs; the user asked for real 3D models. All are
built in Blender (`scripts/build_props.py` on the shared kit `scripts/propkit.py`), with no image generation and no Meshy.

Every part is a closed solid with real thickness (key bows, shafts and bits; rings; bezels and cabochons; blade, socket
and shaft). Part materials are procedural (noise colour variation, ambient-occlusion cavity darkening, declared binary
metalness and roughness, scratch/pit/chip/grain bump) and baked into one 512 px set per model: base colour, packed
metallic/roughness (G roughness, B metal) and an OpenGL tangent normal map, single-sided. Cycles bakes diffuse colour as
albedo x (1 - metallic), so metalness is carried as emission and baked separately.

Review sheets (icon, above, three-quarter, low; back faces culled): [sheet A](review/sheet_final_a.png),
[sheet B](review/sheet_final_b.png).

| Icon | Item | Design | Triangles |
|---|---|---|---:|
| `7item150` | Moonstone | Oval blue-white moonstone cabochon in a gold bezel, rolled frame and sixteen scallop beads on a gold back | 2554 |
| `7item159` | Philosopher's Stone | Smoky violet four-point faceted cushion, gold corner caps, crossed gold wires over the crown, gold cap with a small diamond | 888 |
| `7item363` | Altar Piece | Violet stone bracket ">" block with raised outer rim, recessed channel and inner lip (mirror of 7item364) | 828 |
| `7item364` | Altar Piece | Violet stone bracket "<" block with raised outer rim, recessed channel and inner lip, slightly wider arms | 828 |
| `ankh` | Ankh | Gold ankh: flared stem and crossbar, oval loop, bevelled 3D thickness | 976 |
| `item263` | Telelocator | Gold rod with ring bands, carved spiral, collars and a skull head (dark sockets), tilted so skull and butt both rest on the ground | 2778 |
| `item295` | Ring of Keys | Brass ring with links and beads; four brass keys side by side, bows set with pearl, amethyst crystal, peridot and amber | 2640 |
| `item327` | Enchanted Amulet | Gold shield/teardrop pendant: rim, central aquamarine in a bezel, two rows of turquoise/sapphire cabochons, gold beads, bail | 3070 |
| `keyring` | Dragon Tower Keys | Large copper ring with an iron bead; five keys (copper, rust, iron, old brass, iron trefoil) hanging side by side | 3192 |
| `keys2` | Key to Snergle's Chambers (shared by four keys) | Copper key with fleur bow, collars and an ornate stepped bit | 1284 |
| `shovel` | Shovel | Tapered wooden shaft and grip cap, steel socket, dished pointed spade blade resting on its underside | 636 |

## Checks

- `check_winding.py`: 0 inverted closed parts for all eleven.
- Zero exposed back faces (rays from 60 directions whose first hit is a back face) and no corner normals opposing their face.
- `scripts/validate.py` ([validation.json](review/validation.json)): finite attributes, UVs in range, no degenerate triangles, lowest point zero, centred footprint, one single-sided material with three embedded 512 px PNG maps.
- Installed with `tools/install_model.py --world-items`; `tools/cook_models.py --verify --profile desktop` passed for each (`review/install_<icon>.log`). Before installing, source and runtime matched the baselines in `references/baseline_sha256.txt`; installed sources are byte-identical to `work/<icon>_export.glb`.

Binding lengths are unchanged (each model's longest horizontal side matches the icon's long axis); no length changes
proposed. `items.yml` was not edited: bounds need `tools/item_model_shapes.py`. No in-game run, Android cook, build or commit.

## Rebuild

```sh
blender --background --python level_generation/props/items_props_redo_20261018/scripts/build_props.py -- <icon> [...]
blender --background --python level_generation/props/items_props_redo_20261018/scripts/review.py -- <icon> [...]
python3 level_generation/props/items_props_redo_20261018/scripts/contact.py <sheet> <icon> [...]
python3 level_generation/props/items_props_redo_20261018/scripts/validate.py <icon> [...]
```

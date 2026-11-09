# Letters, documents and Parson's Quill in 3D — 2026-10-18

**11 icons rebuilt as real 3D models and installed** (the "12" in the request was a miscount: seven sealed letters,
three documents and the quill). They were the last flat icon reliefs among letters/documents and now match the
[scrolls batch](../items_wip_scrolls_20261018/README.md): same folded-envelope construction and `7item251` parchment.

Review sheets (icon | above | three-quarter | low, back faces culled): [letters beside the batch's 7item251](review/sheet_final_a.png),
[skull letter, report, vouchers, book, quill](review/sheet_final_b.png).

| Icon | Item | Design | Triangles |
|---|---|---|---:|
| `7item252` | Sealed Letter 2 | Folded envelope, raised gold crescent ring with two purple gems (gold metal) | 924 |
| `7item253` | Sealed Letter 3 | Envelope, raised green fern sprig | 930 |
| `7item254` | Sealed Letter 4 | Envelope, raised orange-red butterfly | 924 |
| `7item255` | Sealed Letter 5 | Envelope, raised green serpent | 928 |
| `7item256` | Sealed Letter 6 | Envelope, raised silver-blue caduceus ornament (metal) | 936 |
| `7item257` | Sealed Letter 7 | Envelope, raised red bat | 930 |
| `7item258` | Letter from Norbert Thrush to Lord Markham | Envelope, raised ivory skull | 936 |
| `item266` | False Report | Landscape sheet with folded-down flap, raised red rosette wax seal | 920 |
| `item318` | Forged Vouchers | Thick aged sheet, mostly rolled (about two turns) with a short lifted tail | 2,012 |
| `item320` | Prophecies of the Snake | Closed book: boards, page block, rounded spine, raised gold cobra head on the red cover | 1,158 |
| `7item247` | Parson's Quill | Peacock feather on the harpy feather's vane/rachis geometry: green barbs, eye spot | 674 |

## How they are built

`scripts/build_letters.py` (Blender) imports the scrolls batch's builder (`build_scrolls.py`: `mesh`, `sheet`,
`uv_tile`, `material`) so the envelope body/flaps, sheet construction and atlas layout are the batch's own. Emblems
are closed raised solids extruded from their painting's own mask (stepped heightfield domed by distance to the
silhouette, voxel-merged, smoothed, collapse-reduced, fold-over slivers collapsed), mapped top-down onto that
painting, and placed at each icon's measured position and size. The book is closed boxes plus a closed half-round
spine; its snake head is the same relief, mapped onto the cover painting. The quill reuses
`items_gems_feather_redo_20261018/scripts/build_items.py`'s feather with a peacock texture.

Textures (`scripts/prepare_textures.py`): one 512 px atlas per icon (base colour, packed metallic/roughness, OpenGL
tangent normal), single-sided. Paper is the scrolls batch's `7item251` parchment. Emblems, the book cover and spine
were painted with Codex's built-in image generation (`codex/CODEX_BRIEF.md`, `codex/generation_runs.json`,
raw outputs kept unchanged; the spine came back 3:1 instead of 6:1 and is fitted to its strip). Gold and silver
emblem pixels are metal (binary); wax, enamel, leather and paper are not. No Meshy.

## Checks

- Every export: `check_winding.py` 0 inverted parts; zero exposed back faces from 60 sampled directions; no corner
  normal opposing its face; footprint centred and lowest point zero; three embedded 512 px PNG maps; one material,
  not double-sided; no degenerate triangles ([validation](review/validation.json)).
- Installed with `tools/install_model.py --world-items` after confirming the baseline source/runtime hashes
  (`references/baseline_sha256.txt`, originals in `references/baseline/`); installed sources equal the exports;
  desktop cook verify 0 problems each (`work/install_receipts.jsonl`).
- Binding lengths unchanged (the envelopes' 54.9-55.8 match the batch's `7item251` at 54.9). `items.yml` was not
  edited: bounds must be refreshed with `tools/item_model_shapes.py`.
- Not done: in-game captures, Android cook, builds, commits.

## Rebuild

```sh
python3 level_generation/props/items_letters_redo_20261018/scripts/prepare_textures.py
blender --background --python level_generation/props/items_letters_redo_20261018/scripts/build_letters.py -- [icon ...]
python3 level_generation/props/items_letters_redo_20261018/scripts/validate_exports.py <icon ...>
blender --background --python level_generation/props/items_letters_redo_20261018/scripts/review_letters.py -- <icon ...>
python3 level_generation/props/items_letters_redo_20261018/scripts/sheet.py <sheet name> <icon ...>
```

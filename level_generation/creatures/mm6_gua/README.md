# MM6 guard — restored `gua*.bmp`

Complete enhanced art package, **installed in the isolated enhanced New Sorpigal playtest**.
[Open the animation viewer](review.html), [compare the three appearances](review/standing_variants.png),
or inspect the [validation report](validation.json).

All **59 unique native creature images** are restored. `guardang.bmp` also matches the wildcard but is an unrelated
Guardian Angel spell sprite and is excluded. Merged descriptors 553–555 use palettes 748/749/750 and animation
groups `gua*`, `gub*`, `guc*`, all referencing the same `gua` image family.

| Action | Frames per sequence | Original view behavior |
| --- | ---: | --- |
| Standing | 1 | Five stored directions, three mirrored |
| Walking | 6 | Five stored directions, three mirrored |
| Attack / second attack | 6 | Same native frontal sequence reused |
| Hit reaction | 6 | Frontal image for every angle |
| Fidget | 6 | Frontal image for every angle |
| Death | 5 | Frontal image for every angle |
| Corpse | 1 | Frontal held pose |

Frames retain **125 ms** timing and native scale **0.799988**. Five viewing-direction review sheets are under
`sheets/`; nonfrontal single-view action rows are empty because those actions reuse their frontal artwork at runtime.
The JSON records every action/view/palette sequence, including the shared second attack and native mirror flags.

## Art, variants and placement

The correctly paletted 748 appearance is the enhanced base: bronze mail, navy sleeves, dark teal trousers,
brown leather and a dark iron halberd. The side references reveal the long wooden polearm shaft hidden by frontal
foreshortening. The accepted standing sheet fixes the identity/materials for all subsequent action sheets.

Ten selected sheets were generated with **built-in imagegen**. Actual outputs are 1657×949 or 1658×949; the
**2× physical export tier** describes resampling/placement, not twice the source detail in every figure.
The logical canvas is **350×296**, with bottom-center pivot **175,296**. Cleanup estimates alpha from a magenta
matte, removes residual contour spill before/after premultiplied resampling, and aligns anatomy and ground placement
to the native frame. Tight crops retain offsets, four-pixel padding and three-pixel transparent RGB/mask extrusion.

One RGBA mask stores four independent coverage channels:

- R: navy sleeves and blue polearm binding.
- G: teal trousers.
- B: warm bronze mail highlights and helmet trim.
- A: remaining skin, leather, wood and dark metal, including their subtle native palette shifts.

Mask alpha is **coverage data**, not sprite opacity. The base PNG's alpha remains unchanged for every palette.
[materials.py](materials.py) defines the enhanced-pixel selection and fixed native-palette luminance fits.
Palette 748 bypasses recoloring exactly; 749/750 are deterministic previews, not additional AI generations.
The operation is `multi_mask_luminance_rgb_v1`, as recorded in [manifest.json](manifest.json).

The shared engine atlas renderer supports this four-channel/four-vector operation alongside the existing
single-mask and two-mask operations. RGBA8 masks retain all four weights without premultiplying mask RGB; only
base alpha controls opacity. The viewer uses the matching deterministic preview operation. All variants share
the same base/mask pages; no baked variant pages are installed. See [installation](ENGINE_INTEGRATION.md).

## Deliverables and checks

- `atlas/base_*.png` / `atlas/mask_*.png`: four matched page pairs, shared by all appearances and actors.
- [manifest.json](manifest.json): frames, atlas rectangles, crop origins, animation sequences and palette vectors.
- `aligned_2x/`, `trimmed_2x/`, `masks_2x/`, `trimmed_masks_2x/`: masters and exact extraction exports.
- [sources.json](sources.json), [inventory.json](inventory.json), [generation.json](generation.json),
  [submitted prompts](prompts/submitted/): provenance, native metadata and exact generation inputs.
- [All base frames](review/all_base_dark.png), [mask overlays](review/all_masks_light.png),
  [edge closeups](review/edge_current.png), [review notes](review_notes.md).

All crop reconstruction, atlas extraction, source hashes, native sequences, palette alpha, base bypass and mask-sum
checks pass. Residual-matte scans find zero candidates over the configured 16/255 threshold in cleaned, cropped and
atlas-extracted frames. The all-frame contacts and representative mirrored-walk/red-attack viewer captures were
reviewed. No engine build or gameplay scenarios were run for this art restoration.

Shipping PNGs plus manifest total **11.45 MiB**. Decoded shared pages total **80.80 MiB**: **40.40 MiB base** plus
**40.40 MiB four-channel masks**. Original BMPs total **3.17 MiB on disk**, or **12.31 MiB decoded RGBA** for one
palette. Page dimensions are 1807×1644, 2005×1570, 1962×1553 and 1829×779. Review/baked variant images and
intermediate art are excluded from shipping figures. No FPS claim follows from these sizes.

## Reproduce from accepted outputs

From the repository root, without new AI calls:

```sh
python3 level_generation/creatures/mm6_peasants/process_family.py gua
python3 level_generation/creatures/mm6_peasants/package_family.py gua
python3 level_generation/creatures/mm6_peasants/build_viewer.py gua
```

The shared helpers load this family's own `inventory.json` through `config.json`. Native reference preparation is
`python3 level_generation/creatures/mm6_peasants/prepare_family.py gua`; it rewrites prompt templates, so preserve
the exact submitted prompts when reproducing a generation. Use the [approved capture helper](../../../tools/CAPTURE_LOCAL_HTML.md)
for browser screenshots. See the [creature-restore skill](../../../.agents/skills/creature-restore/SKILL.md) and
[atlas pipeline](../SPRITE_ATLAS_VARIANTS_PIPELINE.md) for subsequent restorations.

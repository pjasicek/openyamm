# Scroll and letter volumes — 2026-10-18

**Nine remaining icon reliefs rebuilt and installed in the development WIP.** All 18 icons used by the merged
scroll category were examined (514 item rows): eight already have component-built rolled-scroll models, one is
an existing Blender book (`item207`), and nine needed replacements. No deferred designs.

- [Before / after comparison](review/comparison.jpg): inventory icon, old low view, new above and low views.
- [Native outdoor and indoor gallery](review/native_gallery.jpg), with full captures in `review/native_*/`.
- [LOD comparison](review/lod_comparison.jpg), [model statistics](review/model_stats.csv),
  [per-icon ledger](ledger.json), [coordinator handoff](handoff.json).

The new scrolls use closed parchment sheets following real spiral cross-sections, with actual sheet thickness,
inner surfaces and end rims. The five MM6 designs have separate turned spindle finials; `scroll5` has purple
embroidered collars and brass rims. The tied roll has real cords and tails. The sealed letter has overlapping
folded flaps and a raised wax seal. Letters retain ink and weathered/clean identities. No paid Meshy jobs.

| Icon | Design | LOD0 triangles | LOD1 triangles |
|---|---|---:|---:|
| item264 | Weathered written letter | 1,616 | — |
| item265 | Ivory written letter | 1,616 | — |
| 7item251 | Folded and wax-sealed letter | 556 | — |
| 7item182 | Tied parchment roll / shared messages | 2,880 | 1,280 |
| scroll1 | Ochre double-ended scroll | 3,088 | 1,512 |
| scroll2 | Grey parchment and steel fittings | 3,088 | 1,512 |
| scroll3 | Slate blue parchment and ivory filigree | 3,088 | 1,512 |
| scroll4 | Grey parchment and large ivory vines | 3,088 | 1,512 |
| scroll5 | Written parchment, purple/gold collars | 3,872 | 2,024 |

Total **22,892 LOD0 triangles**. Each replacement has **one material and one primitive per LOD**, with embedded
512-square base colour, packed metallic/roughness and OpenGL tangent normal PNGs. The six complex designs have
authored simpler geometry rather than decimation of the thin paper. The simpler letter designs need no LOD.

## Art and UVs

Parchment and ink were painted with the **built-in Imagegen tool** using the inventory contact sheet as a design
reference. Retained output: [parchment atlas](references/parchment_atlas_raw.png);
exact [generation prompt](references/atlas_prompt.txt); [receipt and material provenance](receipts/textures.json).
Gold, bronze, steel, red and purple paintings reuse the retained Imagegen materials from the amulets/gauntlets
project, with local copies and hashes recorded in the receipt. No inventory icon is projected onto the new geometry.

`prepare_textures.py` crops the nine-cell painting and packs front, reverse, fittings and trim into one atlas per
icon. Parchment UVs follow physical surface arc length, with the painting fitted to that UV rectangle; this avoids
stretching the rolls into streaks. UV rectangles have gutters; duplicated colour on the reverse of decorative
scrolls is intentional. Written letters have plain reverse parchment. Paper texel density at the existing binding
length is recorded per model in `review/model_stats.json`; fitting regions are allocated separately in the atlas.
Hard end caps and paper rims have split normals and UV seams. Very thin paper rims are necessary for closed,
backface-culled sheets; their triangles are deliberately narrow. No zero-area triangles or open sheets are accepted.

Metallic follows binary material classes and the explicit embroidered stitch mask. Physical roughness is declared
per surface class. Restrained high-frequency painted detail supplies tangent normals; it is not a high-poly normal
bake. Base colour channels are clamped to sRGB 30–243. Neither lighting nor reflections are painted into the maps.

## Validation and installation

- Nine base models and six LODs pass closed-component topology, positive volume/outward winding, finite positions,
  unit normals, UV range, nonzero triangle area and centred/grounded rest-pose checks.
- Every material has all three maps; embedded source PNGs, albedo ranges and binary metalness pass validation.
- Every export was re-imported into isolated Blender and inspected above, low and from underneath. Representative
  checker renders are under `review/checker/`; all six LODs have independent renders under `review/lod/`.
- Per-model installation used `tools/install_model.py --world-items`, followed by exact per-model desktop cook
  verification. [Install receipts](receipts/installed.json) guard against concurrent source changes. Source/runtime
  triangle counts and LOD links match. The other nine scroll-category source models remain byte-identical.
- Three isolated MM7 `out10.odm` runs covered all nine replacements; one MM6 `6d19.blv` run checked a letter and two
  decorative scrolls indoors. Native checks passed with no model-load errors; [records](receipts/native_review.json).
  Runs used the existing desktop build and OpenGL 3.3. These minimized-window captures are visual checks, not
  performance benchmarks.

Source models: `assets_source/engine/world_items/models/item_<icon>.glb`.
Runtime: `assets_dev/engine/world_items/models/item_<icon>.glb` and its cooked textures.
Unprocessed exports and editable sources remain in `work/finished/` and `blends/`.
Original models are preserved in `baseline/`; the rollback archive is untouched.

**Coordinator action:** apply the nine measured collision/picking `bounds_proposals` from [handoff.json](handoff.json).
Existing binding lengths are preserved. Shared `items.yml` was not edited, following the parallel asset handoff;
until those proposals are applied, picking and collision can still use the old thin relief boxes.

The original all-items save is unchanged (SHA256
`795fffeb87a7d95962e0e4e5af72b166ca9b6986400f43ad96c0d95edbe2fffa`).
No engine changes/build, Android test/cook, release promotion, git staging or commits.

## Reproduction

Run from the repository root. For fresh geometry, first prepare textures, build once to record physical UV
rectangles, then prepare textures and build again to embed paintings fitted to those rectangles:

```sh
python3 level_generation/props/items_wip_scrolls_20261018/scripts/prepare_textures.py
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_scrolls_20261018/scripts/build_scrolls.py
```

Build the lower resolutions with the same builder and
`-- --lod 7item182 scroll1 scroll2 scroll3 scroll4 scroll5`. Combine them with `scripts/stage_lods.py`, passing
the same six icon names after `--`; link each staged GLB through `tools/link_static_model_lods.py` into its
`work/finished/scroll_<icon>_export.glb`. `scripts/validate_scrolls.py` uses the existing strict item validator.
`scripts/review_scrolls.py -- finished`, `-- baseline`, `-- checker` or `-- lod` produce review views.
Only after visual inspection, record the exact accepted hashes in `review/approved_exports.json` and run
`scripts/install_scrolls.py`. Native check commands/tours are retained under `work/native_*`; run records/logs
are copied into `receipts/native_runs/`. `scripts/report_scrolls.py` produces the final ledger and bounds proposals.

# HUD classification and queue preparation

**Preparation is complete.** The counts and verification below record its pre-generation handoff.
The subsequently authorized artwork phase has started; see [ARTWORK_PROGRESS.md](ARTWORK_PROGRESS.md) and
the live queue checkpoint for generation/review status.
The scope of this handoff is classification, frozen exact-x2 targets and an executable resumable queue.
Artwork acceptance, generated exports and restored in-game previews are the subsequent restoration phase.

Read [QUEUE.md](QUEUE.md) for commands and [COMPLETION.md](COMPLETION.md) for the requirement-by-requirement audit.

## Final accounting

- 14,736 files recursively inventoried in engine/world icon roots; every file has a final disposition.
- 56 additional sources: 54 native MM9 map images, one authored dialogue background, and the recovered Shadow's Mask.
- 14,780 restoration targets; 12 non-target files retained with evidence (10 shadowed filename variants,
  one malformed mask contact sheet and one provenance document). No source bytes or generated appearances were
  silently merged. Matching render hashes remain unapproved sharing candidates.
- 4,268 jobs / 14,966 cells: 4,254 imagegen-sheet recipes, 3 deterministic font-region jobs and 11 deterministic
  uniform-region jobs. Those deterministic atlas jobs cover four glyph regions and 66 uniform unused regions.
- 12 font families and five generated/external dependency categories have explicit existing owners.
- Zero required missing sources, zero generation calls, zero accepted artwork and no production checkpoint attempts.

## Source and dimension evidence

`source_audit.json` verifies 13,566 native-library bitmap baselines against 12,736 extracted originals.
`import_audit.json` verifies all 881 MM9 bitmap baselines using import/authored manifests, including reviewed
pose-pair repairs and the two deliberately extended soft-cap canvases. `authored_audit.json` binds the remaining
project-authored canvases to checked-in bytes/dimensions or the explicit dialogue renderer contract and historical
hashes. These are native dimension baselines, not claims that existing artwork is an accepted x2 restoration.

The current Shadow's Mask runtime file, `7item344.bmp`, is a malformed 996x2880 contact sheet. Its actual native
50x55 source is retained under `sources/native_overrides/`; the required output is 100x110. Runtime bitmap files
remain untouched. Same-name PNG/BMP/PCX and case collisions were resolved through actual image-loader ordering;
`winBG.PCX` is the selected case-folded entry, with its sibling retained rather than exported over it.

All 54 external map images match native MM9 PCX bytes. The dialogue background has its authored native 540x192
canvas. Fonts remain on their deterministic pipeline. External images export into `ui_x2`, whose preview tier is
selected separately with `ui=x2`; `prefer_restored_icons` handles the icon roots.

## One necessary source cleanup

Removed the seven-line mobile `OutdoorBuffSkull_Immolation` entry requesting absent `asiR08`. The same layout already
uses `asiL10` for `OutdoorBuffBody_Immolation`, and both renderer conditions check the same party buff. This resolves
a duplicate broken dependency without inventing artwork. `repairs/source_repairs.json` records the before/after
hashes and retained patch. The inventory and all frozen inputs were explicitly reconciled afterward.

The other eleven formerly missing names are evidenced non-targets: four beard names are metadata-only `headAsset`
fields, and seven pc30 body names belong to an unavailable reserved character. No shipped roster picture 29 selects
that character. No engine code, settings, saves, launchers, or runtime bitmap files were modified.

## Prepared runtime semantics and grouping

`expected_targets.json` records full canvases, exact x2 dimensions, namespaces, output paths, every YAML usage and
ancestor chain, native item/equipment rows, table-driven animation timing, expression frames, state aliases and
palette/render fingerprints. It retains five spell-state canvases that differ from their YAML draw rectangles.
Menu PCX, menu BMP, HUD and item transparency are distinguished. The 2,223 sources with differing consumer masks
retain key/index-aware BMP/PCX export contracts instead of one incompatible flattened PNG mask.

Spell pairs stay side by side and depend on accepted school-page crops at resolved coordinates. Normal/hover states
share page pixels; pressed aliases remain aliases. Portrait batches use authoritative table prefixes, including
`girla`, `malea`, `wets_` and other non-PC names, with accepted identity seeds. Equipment families retain native
registration and MM9 world-local offsets. Arcomage has all 102 active card slot/name bindings, separate glyph/blank
regions, and exact full-canvas reconstruction. Large backgrounds remain individual full-image jobs.

Queue mutations are locked across CLI processes and saved atomically. Each attempt retains its raw master, exact
submitted prompt and copies of all reference images. Page/seed hash changes invalidate dependent acceptance;
failed cells preserve accepted siblings. Native/generated inventories never contain mutable acceptance state.

## Verification

- `audit_preparation.py` passed against the full current census, classification, manifests, source hashes and sheets.
  It verifies exact x2 region coverage, unique outputs, state/portrait/page bindings, dependency DAG, ownership and
  zero pending missing references. See `review/classification/completion_audit.json`.
- Fourteen focused tests pass, including indexed transparency, extra menu keys, variable-size spell pairs,
  Torchlight's actual center-anchor crop, nonstandard portrait prefixes, MM9 offsets, exact page-crop payloads,
  concurrent checkpoint updates, raw recording, independent acceptance/defer/resume and full RGB atlas reconstruction.
  Synthetic fixtures stay in temporary checkpoints; they are never accepted production artwork.
- Representative originals, native inventory screenshot, accepted decoration fidelity comparison, and prepared spell,
  portrait, inventory, fitted-equipment and revised Arcomage sheets were visually inspected. This establishes
  preparation treatment; it is not visual approval of any generated restoration.

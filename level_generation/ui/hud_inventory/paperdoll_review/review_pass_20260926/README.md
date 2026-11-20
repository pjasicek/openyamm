# Equipment review repair/staging pass — 2026-09-26

Open [the repaired-item queue](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=repairs).
The server serves the repository root on port 8899:

```sh
python3 -m http.server 8899 --bind 127.0.0.1
```

Use **Repaired candidates** to review replacements and **Staged accepted** to revisit the original approval set.
The inspector retains the original note, offers the original staged image, and lists the repair as an alternate attempt.
F1–F9 select equipment categories, Space advances, Shift+Space accepts, arrows move one native pixel, and Tab cycles
male/female/minotaur/troll/dwarf. Editing a note or select keeps normal keyboard behavior; Escape resumes shortcuts.
Export review JSON after reviewing. Equipment acceptance remains per image/hash, including each body/arm-pose variant.
Shared weapon art has one artwork decision; its placement edits remain per item/body type/slot.

Enable **Hide accepted / staged** above the previews to show only images still needing acceptance. It filters
the queue and item lists; Space and item arrows skip accepted entries. Flagged or changed images remain visible,
including repairs of staged originals. Body and arm-pose variants are checked separately. The toggle is remembered
without changing review records. [Open with accepted images hidden](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?hide_accepted=1).
An isolated browser check verified filtering, persistence, Space navigation, variant independence and unchanged
decisions/notes/placements.

## Preserved work

- `review.original.json` is an immutable copy of `/home/pjasicek/Downloads/openyamm-paperdoll-review_2.json`.
- All **849 decisions (594 approve, 255 flag)** and original notes are preserved in `stage_manifest.json`.
- `staged-accepted/` contains the **594 exact approved images**, verified against their recorded SHA-256 hashes.
- **591 original placement records** are preserved byte-for-byte as JSON values in `placements.json`.
- **92 missing wand placements** inherit from the earliest reviewed item using the same display sprite, body type and slot.
  Existing manual entries always win. Three groups with differing explicit values remain intact in `inheritance_conflicts`.
- `placement_proposals.csv` provides **683 rows**, including two explicitly inactive legacy global-grip records.
  Complex equipment offsets map to `complex_item_pictures.txt`; per-item/type/slot weapon offsets require corresponding
  runtime support when eventually installed. They cannot safely be collapsed into the global `items.txt` grip fields.
- Existing browser entries win during the one-time import. Exact prior local-storage values are backed up under
  `openyamm-paperdoll-stage-import-20260926-backup`. Clear/Reset is not undone on subsequent loads.

The checkpoint and runtime tables/assets were not modified. No new equipment was accepted into the ledger.
The already accepted ESRGAN body/limb set remains the doll source.
The stage manifest explicitly blocks final ledger acceptance and identifies previously approved originals with
pending replacements; the staged folder alone is not an installation manifest.

## Repairs and crop audit

**869 reviewed/automatically screened assets** were audited against native sprites and retained raw sheets,
including all 594 approved images. All 29 source comparison sheets were visually inspected.
The crop audit found reflowed sheet rows, truncated pieces and neighboring-cell contamination. Complete raw subjects
were extracted and fitted to the native foreground bounds on a native-canvas-sized 2× image. The resulting silhouette
can still differ inside that bounding box; native-sized canvases do not prove equipment fit.

`repairs.json` identifies **492 replacement candidates**, including **217 previously approved targets**.
The entire **313-target note/automatic-findings queue** is covered. Repaired approved targets require renewed review;
their original approved files are still staged and unchanged. The remaining 377 staged approvals have no replacement
from this pass. Unreviewed held-weapon armor variants remain unapproved.

- Crop repairs use retained masters; boot pairs retain both disconnected boots.
- Reported magenta/green spill is cleaned without regeneration solely for spill. Purple material and gems are retained;
  color screening still needs visual judgment. The scan in `validation.json` records remaining purple-color findings.
- Quality/identity repairs use native-reference generation, with prompts and raw masters under `generated/`.
- `chipped_blades` supersedes the earlier saw-tooth interpretations for item001, item011 and item006. The user clarified
  that the damage is small, uneven chips in cheap blades, not regular serrations.
- Dark sleeve/wrist/neckline/boot interiors were removed using native transparency and inspected local cutouts.
  Gold armor `7item235v2a` includes the user's explicitly requested sleeve-interior removal.
- Thick handles were narrowed toward native widths with a smoothly varying warp; every carried placement still needs
  a visual fit check after changed artwork. Preserving an offset does not certify a replacement silhouette.

All new images have exactly twice the native canvas dimensions, with zero RGB in fully transparent pixels.
Original hashes, repair operations, raw crop rectangles, prompts and master hashes are recorded for traceability.
Only files listed in `repairs.json` are active; earlier intermediate outputs can remain in the working directory.
`repair_contacts/` contains all native/old/repaired comparisons, in that order.

## Belt size

The questioned belts already occupy the broad native footprint. For example item119v1 is 66×24 native pixels
(132×48 candidate), item119v3/v4 are 73×26 (146×52), and item120v1 is 60×35 (120×70).
See `belt_dimensions.csv`. The viewer draws both native and restored art at `asset.size × 2`; it does not apply another
belt-specific enlargement. Local OpenEnroth behavioral reference `src/GUI/UI/UICharacter.cpp` selects the body-type belt
texture/offset at lines 1090–1102 and draws it through `CharacterUI_DrawItem` without extra belt scaling (line 1289 onward).
The belt footprint was therefore retained rather than arbitrarily reduced.

## Reproduce/check

Run from the repository root, with Pillow, NumPy and SciPy available:

```sh
python3 level_generation/ui/hud_inventory/paperdoll_review/review_pass_20260926/repair_assets.py
python3 level_generation/ui/hud_inventory/paperdoll_review/review_pass_20260926/build_overlay.py
python3 level_generation/ui/hud_inventory/paperdoll_review/review_pass_20260926/validate_pass.py
```

`stage_review.py`, `inspect_sources.py`, and `map_crops.py` document preparation. Do not rerun `prepare_generation.py`
as a resume command: additional retained correction batches were appended to `generated/batches.json` after preparation.
The browser smoke check uses an isolated temporary Chrome profile, so the user's active review storage is untouched.
Final checks and screenshots are retained beside this README. Visual acceptance remains the user's next step.

# Spell foreground review v2

Open [index.html](index.html) in a browser. Search by spell name, switch the backdrop between checker, dark and
light, and compare both color/sepia states against the native originals. Approve or flag each state, then export the
review JSON. The user approved all 222 states. `../spell_review_acceptance.json` binds that decision to each
source/candidate SHA-256 pair, and `../staged_spell_icons/` holds exact copied PNGs for later integration.
The restoration checkpoint and game assets are unchanged; subsequent browser flags stay local until exported.

## What changed

The first transparent stage reused previews that had already lost glyphs or full-canvas content. This stage starts
from the retained **full-resolution raw masters**. It measures actual returned sheet gutters, extracts full cells,
and fits the complete paired art to exact 2× native canvases with uniform **downscaling only**. It does not enlarge
the original pixel art to produce candidate pixels.

| Source | States | Method |
| --- | ---: | --- |
| Transparent retained masters | 152 | Full raw-sheet recrop, paired fit; includes four Air states cleaned from full magenta masters. |
| Paper-backed restored masters | 52 | Eight imagegen batch returns, using fixed-size cells, 32-pixel reference gutters, original and restored source grids, then measured return gutters. |
| Accepted Air ink | 18 | Existing separately saved foregrounds from the Air page workflow. |
| **Total** | **222** | **111 color/sepia pairs; all exact 2× RGBA canvases.** |

The [atlas audit](../spell_atlas_audit/manifest.json) records all 26 source sheets and 204 full raw slots. Its
`alpha_candidates.json` and `paper_candidates.json` record each fitted crop, scale and hash. Every batch under
`../spell_atlas_audit/paper_batches/NN/` retains both input reference grids, layout, exact submitted prompt and raw
returned sheet. Batch 01 used a distinct pilot prompt; its submitted text is retained separately from the prepared
generic text.
The [v2 manifest](manifest.json) binds every browser candidate to those files.

The `sba04` and `sba11` paper-edit input mistakenly omitted detached glyphs by isolating only the largest magenta
component. Their returned paper-edit rows are excluded. The v2 candidates instead come from the **complete**
retained magenta master, including its original glyph groups, with local chroma cleanup. An isolated next-row
fragment below `sbdk11a/b` was removed from the review fit after checking both raw slots and native originals.

## Review limits

All candidates have real alpha and the correct 2× canvas size; the reference sheets stayed below the measured
1.36-megapixel preparation budget, and all returned paper-edit gutters passed the empty-gutter check. These
measurements do not prove exact glyph shapes, identity, native placement, or edge quality. Inspect every glyph and
fine stroke at actual 2× over light and dark backdrops. The only 62 pixels reported by the saturated-magenta color
detector are inside `sbde04a`'s intentionally purple magic beam, not a sheet edge.

To refresh crop records from the retained source sheets, run these commands from the repository root with Python 3,
Pillow, NumPy and SciPy installed:

```sh
python3 level_generation/ui/mm8_art_review/spell_atlas_audit/prepare.py
python3 level_generation/ui/mm8_art_review/spell_atlas_audit/finalize_alpha.py
python3 level_generation/ui/mm8_art_review/spell_atlas_audit/finalize_paper_batches.py
python3 level_generation/ui/mm8_art_review/spell_foreground_stage_v2/build.py
```

`prepare_paper_batches.py` verifies the frozen imagegen reference hashes; it does not overwrite a returned batch.
The four commands above regenerate candidates and the browser catalog, but do not grant approval. Run
`python3 level_generation/ui/mm8_art_review/accept_spell_foregrounds.py` only for the already approved v2 candidate
set to verify and reproduce its hash-bound staging files.

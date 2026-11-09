# Transparent PC restoration — 2026-09-27

Fresh restoration of every available canonical PC family from archived native originals.
**Accepted and installed by explicit user instruction on 2026-09-27.** All 4,032 aligned exports
are now the current accepted PC portrait solution in `assets_dev/engine/icons_x2/`.
The [acceptance transaction](../pc_transparent_acceptance_20260927/README.md) retains the exact
approved PNGs and updates the canonical icon index and ledger. [acceptance.json](acceptance.json)
binds this viewer to that immutable revision. Global offset at publication was `[0, 0]`.

Open [the review page](http://127.0.0.1:9100/level_generation/ui/hud_inventory/pc_transparent_regen_20260927/index.html).
Select a family and state; compare original and aligned art with the same selection ring,
vertical center guide, and bottom guide. Global half-pixel X/Y offsets persist across families
and in the URL; downloads include those offsets. Basebar and character-selection layouts
follow the existing game UI geometry. Height/contact measurements are displayed in 2× pixels.
The HUD and preview omit the legacy `FACEMASK` overlay after the user's follow-up instruction.
The shared 60×80 logical portrait viewport and selection-ring placement are preserved;
see [HUD facemask removal](../hud_facemask_removal_20260927/README.md).

## Review coverage

- All 4,032 portraits are available: 144 of 144 sheets passed the assistant's technical
  and visual checks. All 72 active families have 56 candidates in the browser.
- `7pc02_B`, `girld_B`, and `maled_B` use `attempt_02` with reduced injury, as requested by
  the user. Injury states use intact skin with faint bruising or tired/dazed expressions;
  blood and open wounds are removed. Their first attempts' safety rejections remain in
  `attempt_01/state_at_supersession.json`; the new instructions are recorded in each
  `attempt_02/scope_change.json`. No sheets remain held.
- [Validation report](audit.json) checks dimensions, source preservation, raw alpha, export
  hashes and placement measurements. [Browser check](browser-check.json) records the viewer
  checks; [browser screenshot](browser.png) shows the paired selection-ring preview.
- Sheet review notes remain visible in the viewer. For example, `pc09` has a more prominent
  earring in sheet A, `pc27-36` has slightly more visible gold cap tips, `pc32-39` has fainter
  forehead discoloration, and the palest `pc38` states read more solidly than their originals.
  The reduced-injury `maled54` reads as anger with much less redness/swelling.
  These observations are retained as part of the accepted review history.

## Sources and generation

- 72 present families, 56 states each: 4,032 native portraits. The catalogue's `pc30` family
  has no native assets and is explicitly recorded as missing.
- Four additional archived families (`7pc09`, `7pc11`, `7pc21`, `7pc22`) have all 56 states
  explicitly marked `archived_unused` by the runtime-install scope receipt. They are excluded
  from the active PC slice; see `scope_audit.json`.
- Native sources: archived BMPs under `assets_legacy/icons_20260926/engine/icons/`.
  `catalogue.json` pins original and previously accepted hashes and runtime mappings.
- Two sheets per family: A = 01–28, B = 29–56, seven columns by four rows.
- `families/<family>/<A|B>/reference.png` contains exact nearest-neighbor 2× native originals.
- Each `attempt_01/` retains the exact `prompt.txt`, `request.json`, immutable imagegen
  `raw.png`, its hash, measured extraction report, final frames, raw placement previews,
  alpha images, and an original/aligned comparison plate.
- Generation uses the built-in imagegen tool. The request requires actual RGBA transparency,
  preserved identity/states/props/stone and pale features, more than 2× native detail, and
  native height/center/bottom registration. Full wording is in each saved prompt.
- Historical tool rejections remain in the superseded attempt records. User-requested reductions
  in injury resolved all three holds; every current sheet has generated artwork.

## Placement and alpha

Imagegen alpha supplies every final outline; no green-key cleanup, native mask, or oval
stencil alters it. Native background estimates only measure the original silhouette.
Master cells split at measured transparent gutters. Uneven sheets can carry a reviewed
`extraction_grid.json` pinned to the raw hash; its separate row cuts per column must all
cross alpha ≤8. This preserves complete silhouettes when one column sits lower than another.
Height and center measurements use the
largest 8-connected alpha-128 component; isolated droplets cannot define the crown. The full
generated RGBA cell is resampled, including detached status particles. The extractor fits height separately
from width so horizontal fringe containment cannot shrink a face vertically. A short lower
contact strip provides the bottom anchor; this avoids single-pixel color ambiguities in
green-skinned originals. If exact contact and head center conflict, a horizontal correction of
at most four output pixels balances them while retaining the full horizontal fringe. A small
vertical refinement checks the actual downsampled crown and bottom.
Center checks also use the actual downsampled silhouette; reports retain the predicted
continuous-coordinate center separately. Six original measurement guides received corrections
after pixel inspection: `pc17-39` excludes status spray above the hair; `pc38-11` and `pc38-36`
measure their very faint complete heads; `wets_12` includes the lower half of the stone helmet;
and `pc25-38` and `pc25-50` exclude green backing beside the lower neck from the contact strip.
Original pixels and generated alpha remain unchanged. Each correction preserves its prior
record, guide, export and comparison under `history/native_head_measurement/`.
Every output is 118×158 RGBA, twice the 59×79 native canvas, downsampled with premultiplied
alpha and Lanczos filtering. Original pose asymmetry is retained instead of centering the nose.

Reports flag insufficient master sampling, height/contact/center mismatches, excessive shape
correction, and weak exterior transparency. Each master and all original/aligned pairs also
need visual inspection for expression, detail, accessories and cutoffs. A `reviewed` status
records that assistant check; it is not user acceptance.
`pc12_A`, `pc26_B`, and `pc36_B` use `attempt_02`: their first masters had insufficient transparent
row gaps, so fresh native-based generations with wider gutters replaced them. `pc25_B` also
uses `attempt_02`, generated to improve head/contact alignment. The first attempts are retained.
Two later individual alternatives for `pc25-38` and `pc25-50` are retained with raw masters and
receipts under `families/pc25/B/attempt_02/repairs/`; they are not selected. Correcting the native
contact measurements resolved placement using the existing 28-pose sheet.

## Resume

Use `python3 level_generation/ui/hud_inventory/pc_transparent_regen_20260927/run.py` with:

```
progress
next --count 4
claim <family>_<A|B>
record <family>_<A|B> /absolute/imagegen/output.png
process <family>_<A|B>
review <family>_<A|B> pass "Observed visual checks"
review <family>_<A|B> repair "Observed defect"
tool-error <family>_<A|B> "Exact tool rejection"
browser-data
```

`prepare` is a one-time operation and refuses to overwrite the catalogue. `claim` precedes
the built-in tool call; `record` copies the master once, then extracts it. Preserve rejected
or superseded attempts. Do not retry a safety rejection by rephrasing the same request.

# Remaining inventory and UI art review

Open [all 177 accepted PC effect catalog assets](index.html?effects=1) for the separate `sp*`/`spell*` review, or
[play the 22 multi-frame animations](pc_effect_sequences/index.html). Four standalone effect images (`sp73e`,
`sp75e`, `spell69e`, and `spell1`) are accepted in the same effect ledger. The separate HUD target `sp21a10` appears in
the animation player and has [its own decision card](review_repairs/remaining_sequences/first_frame.html), outside
this 1,718-target catalog. Open [all inventory and UI art](index.html) for
the full catalog, or choose **New imagegen slice (590)** for that batch. Each native original is beside its exact
2× replacement; earlier flags and notes remain visible as history. The initial full-catalog
view shows one representative per identical original; choose **All targets** to see every destination. Light, dark and
checker backdrops expose transparency and edge defects. If the browser blocks local files, serve the repository root
with `python3 -m http.server 8765 --bind 127.0.0.1` and open
`http://127.0.0.1:8765/level_generation/ui/remaining_art_review/`.

For motion and consistency review, open the [PC effect sequence viewer](pc_effect_sequences/index.html). It reads
the engine's `icon_frame_data.txt` order and plays all 22 referenced multi-frame `sp*`/`spell*` families: 174 frames
in total. The native frame and current 2× candidate appear side by side, with a frame strip, scrubber, backdrop and
native effect-envelope guide. Each frame links to its decision card. `sp21a10` belongs to the separate HUD
inventory; its new candidate was generated with the other seven `sp21a` frames and is accepted in the effect ledger.
Regenerate the static browser data with
`python3 -B level_generation/ui/remaining_art_review/pc_effect_sequences/build.py` after changing candidates.

The six slices contain 1,718 active source targets: 770 inventory items, 473 animation frames, 20 frames/panels, 75
button/control states, 87 UI backgrounds/loading images, and 293 other referenced UI artworks. Every target has a
fitted 2× candidate. The user's blanket approval covers **1,541 non-effect targets**: all 770 inventory items, 442
UI animation frames, 20 frames/panels, 75 controls, 87 backgrounds and 147 other UI artworks. On 2026-09-24, the user approved **all 22 PC effect sequences and four standalone effects**,
including the fixed-core Fly, Water Walk and Levitate candidates. The
[effect acceptance ledger](effect_acceptance.json) records **178 accepted images**: 177 catalog targets plus
supplemental HUD frame `sp21a10`. All exact PNGs are in the [effect stage](staged_approved_effects/manifest.json).
There are **zero pending effects**, and all **1,718 catalog targets are accepted**. The
[earlier four-sequence approval](review_repairs/four_kept_effect_acceptance.json) is preserved unchanged;
the current ledger extends those 32 approvals with 146 newly accepted images. The
[non-effect acceptance ledger](review_acceptance.json) is the historical non-effect slice: its
`pending_effect_ids` records the original 177-target boundary, now fully covered by the effect ledger. It
binds its 1,541 approvals to native and candidate SHA-256 values; its exact PNGs and
[stage manifest](staged_approved/manifest.json) are under `staged_approved/`. Both stages are arranged by `engine`
or world `icons_x2` destination. These icons are staged for integration; native icon files and runtime lookup have
not changed.

## Imagegen replacement for the old fallback slice

All 590 targets that previously offered a Real-ESRGAN candidate were initially given a new review candidate:
587 from imagegen returns, plus smooth redraws of two 7×7 direction arrows and preservation of one intentionally
transparent 1×1 sprite after imagegen returned them empty twice. Later review repairs supersede some of those
imagegen candidates, including `item160` and `item162` with approved world art. No Real-ESRGAN option is offered
in this viewer.
The earlier [fallback manifest](restored_fallback/manifest.json) remains as historical provenance only.

The [imagegen plan](imagegen_regen/plan.json) records 95 first-pass sheets from the original native art. The
[first-pass report](imagegen_regen/report.json), [complete inventory component crops](imagegen_regen/component_report.json),
[complete effect/strip component crops](imagegen_regen/edge_component_report.json),
[19-sheet retry report](imagegen_regen/retry_report.json),
[manual strip/title-panel registrations](imagegen_regen/special_report.json),
[enlarged-reference inventory](imagegen_regen/third_report.json) and
[spell-effect animation](imagegen_regen/third_effects_report.json) reports retain raw-return hashes, exact crop regions,
native bounding boxes and fitted 2× hashes. The [title assembly](imagegen_regen/title_assembly.json) records six
overlapping imagegen tiles. The [palette correction](imagegen_regen/palette_report.json) fixes a white fading ankh
that one return colored pink; the [tiny-art/backing report](imagegen_regen/tail_report.json) records the final four
cases. The [ten potion states](imagegen_regen/potion_report.json) were regenerated as two isolated five-icon rows
after an earlier sheet joined vertically adjacent bottles. The [wide cape](imagegen_regen/cape_report.json) was
regenerated separately to preserve its low silhouette. Raw imagegen returns and reference sheets remain under
`imagegen_regen/returns/`, `retry_returns/` and
`references/`. The [prompts](imagegen_regen/prompts/) and [retry prompts](imagegen_regen/retry_prompts/) are retained.
The [additional submission log](imagegen_regen/extra_submissions.md) records the exact prompts for the targeted passes.

## Opaque magenta perimeter cleanup

All 243 `terra*`, 12 `t_*` and 14 `bt_*` review candidates have an isolated one-pixel border repair. Their original
rendered images contain no visible magenta, while the review candidates carried magenta from the generated sheet
gutters along the outer edge. Seven more opaque icons named in the latest review export (`ticon03`, `ticon04`,
`tpharmon`, `tpisl`, `tpmist`, `tpwarl`, `outside`) received the same repair. The
[repair report](magenta_perimeter/report.json) binds each new candidate to its input
hash and records 50,522 removed border-magenta pixels across 276 targets. The artwork inside the perimeter is unchanged. Four `terra*`
frames also had a few keyed pixels one row inward; those spots were reconstructed from the next interior pixel.
The repaired candidates are primary in the viewer, and the contaminated variants are no longer offered.

Imagegen sometimes expanded sparse effects or thin inventory objects within their cells. Enlarged source sheets
and measured foreground fitting restored their native placement while retaining the generated artwork and alpha.
The viewer is the visual quality gate for identity, animation state, lettering, color and texture. Technical crop
checks do not imply artistic approval.

## Repairs after the 2026-09-24 review

All 72 flagged candidates now have a different primary candidate bound to the same native-source hash. The first
[repair reports](review_repairs/) cover 32 complete objects recovered from existing imagegen component sheets, 17
regenerated spell-effect frames, 19 regenerated inventory and status sprites, two local magenta-spill repairs, and
two exact 2× UI geometry redraws (`loadprog` and `map-pin2`). Eight note-only targets were also repaired: `tp_regna`,
`7item134`, `amulet1`, `6ring12`, and four tall items whose restored artwork sat below the original placement.
The bow `item245` and ring `6ring12` were regenerated from their originals to recover the string and bronze base;
`7item119` and `7item263` needed only local spill cleanup. The 32 reused inventory candidates were visually checked
for complete silhouettes. The [imagegen submission log](review_repairs/submissions.md) identifies all reference
sheets and prompts; raw returns are retained in `review_repairs/returns/`.

The first four affected PC effect animations were regenerated as [complete eight-frame sequences](review_repairs/full_sequences/index.html)
from **all** native frames in each sequence: `sp05e`, `spell14e`, `spell36e`, and `spell68e`. These 32 candidates
supersede the earlier 17 frame-only effect repairs and add their 15 companion frames. The returned full sheets,
[source layouts](review_repairs/full_sequences/jobs.json), [fitted extraction report](review_repairs/full_sequences/report.json),
and [submission prompts](review_repairs/full_sequences/submissions.md) remain available. Each sequence uses one
shared native oval envelope on identical 118×158 canvases, centered at (59, 79); sparse phases retain their gaps
while their oval placement stays steady. The frames keep genuine alpha and sample at least 2.5 generated pixels
per final 2× pixel. The user approved these four sequences; all 32 exact candidate PNGs are staged separately.

The other 18 referenced sequences were regenerated from [all 142 native frames](review_repairs/remaining_sequences/jobs.json).
The [20 selected imagegen returns](review_repairs/remaining_sequences/generation_log.json) produced 142 new exact 2×
RGBA frames, including the separate HUD frame `sp21a10`. The 12-frame red curtain used three smaller sheets to
retain at least 2.36 generated pixels per final pixel. Raw artwork stays at least 18 pixels inside its assigned
cell. The extraction keeps each phase on its native canvas and placement, so sparse opening and closing frames
remain sparse. Most effect envelopes are centered on the portrait; the light band `sp58e` stays at its native upper
position, while the curtain and full-square texture keep their intended geometry. A two-pixel stray mark in the
`sp109` raw return was removed before fitting so its figure holds a steady scale. Compare the
[native and new contact sheets](review_repairs/remaining_sequences/contacts/) or
[play all 22 sequences](pc_effect_sequences/index.html). The new 141 catalog frames and supplemental HUD frame
were accepted by the user on 2026-09-24.

The idle HUD sequences `sp21a`, `sp27a`, and `sp109` first received placement registration in the
[stabilization report](review_repairs/remaining_sequences/stabilization_report.json). The drawings still changed
shape between phases, so the [fixed-core pass](review_repairs/remaining_sequences/idle_core_report.json) now uses
one restored master for each main figure. The Fly boot and wing joints stay fixed while the upper wings and stars
animate. The Water Walk figure and platform stay in place while water light and stars pulse. The Levitate figure
stays fixed while light travels across the cloud. Each of the 22 final 2× candidates is hash-bound to its previous
candidate and its chosen master. The [contact sheets](review_repairs/remaining_sequences/contacts/index.html) show
native, initial restoration, registered, and fixed-core rows. These three sequences were accepted by the user on 2026-09-24.

`item160` and `item162` now use lossless inventory placements of the already approved world sprites `obj143`
and `obj145`. The [inventory/world crosswalk](review_repairs/world_item_links/report.json) follows
`items.txt` **Pic File → Sprite Index** and `object_list.txt` **ObjectId → SpriteName**. The game already uses that
link for placed item rendering; inventory icons still have separate image files. Of 770 inventory targets, 139
share the same native drawing with an approved ground sprite. For 138, the accepted inventory candidate uses that
ground master: 112 preserve its pixels exactly, two translate its complete foreground inside the inventory canvas,
and 24 scale the whole foreground uniformly to fit. The exception is `7item263`: its selected inventory restoration
is used for both inventory and `7obj263_p9` on the ground. The [world override stage](staged_approved/engine/decorations_x2/7obj263_p9.png)
places it on the original 256×256 ground canvas, and [its installed binding](../../../assets_dev/engine/decorations_x2/manifest.json)
now points to that exact staged image. The historical ground sprite installation plan remains intact, with this
post-approval override recorded in the live manifest. Two pearls share only a coincidental alpha shape and were
excluded. The world preview and [139-item filter](index.html?world=1) show the crosswalk.

The [validator](validate_catalog.py) requires all 72 flagged hashes to be superseded and all
236 current repair candidates to be primary, then checks source hashes, PNG hashes, 2× canvases, complete effect
sequences, native placement, raw-cell insets, sampling, and approved world donor candidates. All sequence frames are now accepted; earlier browser decisions remain visible as review history.

## Earlier candidates and duplicates

Other candidate sources remain available in the selector: measured crops from retained generated sheets,
121 transparent `hglas` restorations, local UI repairs, earlier direct 2× candidates, and exact-original reuse.
The [duplicate report](duplicate_report.json) identifies 20 targets matching previously approved art and 55 groups
containing 118 repeated originals in this review. Native rendered pixels, dimensions and placement must match before
reuse is offered. Each destination still needs its own visual decision.

The user's [earlier review](user_review_2026-09-23.json) remains unchanged. The
[2026-09-24 export](user_review_2026-09-24.json) records 72 flags and 17 note-only entries and is merged into the
viewer's review history. Flags against replaced candidates appear as history. The approved non-effect targets load
from `acceptance.js`, and all approved effects load from `effect_acceptance.js`; new browser decisions
use a fresh storage key. Export or copy later review changes to
keep them. Browser export does not alter the acceptance ledger, restoration checkpoint, or runtime icon assets.

The [catalog builder](build_catalog.py) checks the frozen inventory, native hashes, 590-target imagegen coverage and
candidate dimensions. The [validator](validate_catalog.py) checks all paths, hashes, exact canvases, two-pixel
magenta border cleanliness for all 276 opaque repairs, and completeness
of still-selected first-pass alpha crops; it writes a
color-edge inspection ranking in [validation_report.json](validation_report.json). Saturated materials can appear in
that ranking, so it is a diagnostic rather than automatic visual approval. The browser smoke check is
`node level_generation/ui/remaining_art_review/test_viewer.mjs`. Verify the approved stage with
`python3 -B level_generation/ui/remaining_art_review/accept_review_slice.py --verify` and the installed ground
override with `python3 -B level_generation/ui/remaining_art_review/apply_world_override.py --verify`. Verify the
complete effect ledger and stage with `python3 -B level_generation/ui/remaining_art_review/accept_kept_sequences.py --verify`.

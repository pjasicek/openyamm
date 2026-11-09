# Faithful x2 restoration of the shared HUD and its bitmap dependencies

Use [README.md](README.md), [inventory.json](inventory.json) and the whole-folder [scope.json](scope.json) to
complete a faithful restoration of the shared MM8-style HUD used across worlds, its related UI screens and the
bitmap dependencies those screens display. Preserve the existing design, interaction, native logical size and
alignment. Every restored asset/state/variant must have **exactly 2× its own native width and 2× its own native
height**, including transparent margins. Do not redesign the UI.

This document describes the full restoration goal. Classification, frozen targets, exact prompts, reference sheets
and the executable HUD queue are now prepared; see [PREPARATION.md](PREPARATION.md), [QUEUE.md](QUEUE.md) and
[COMPLETION.md](COMPLETION.md). Preparation has made no image-generation calls. A future explicitly requested artwork
goal should resume this HUD queue through reviewed exports and an isolated in-game preview; do not substitute the
separate sprite queue or regenerate frozen inventories over accepted state. The full artwork completion gate below
remains applicable to that subsequent phase.

The artwork phase must also follow [MATTE_AND_FITTING.md](MATTE_AND_FITTING.md): explicit pure-magenta cutout
requests, creature-workflow edge decontamination, measured footprint checks and actual internal-landmark review.
Exact x2 canvas dimensions alone never establish drop-in fitting.

**Current batching policy (2026-09-10): use 3×3 sheets for compatible small artwork.**
Follow [BATCHING.md](BATCHING.md), including execution batches across existing frozen inventory jobs.
The nine-item experiment demonstrated this approach; it did not accept its candidates into production.
Do not resume serial per-icon generation as the default or rebuild frozen manifests to obtain new packing.

**External portrait bundles (corrected 2026-09-13):** these are independent native-reference first passes.
Do not require cross-chat style-pilot approval or a supplement before generation. The former requirement
caused zero-output handoffs and was corrected after the user's report. Final local visual acceptance remains
mandatory. Bundles 007–015 cover NPC portraits and player seed groups. Bundles 016–025 also include expression
followers with their same-character native identity references supplied inside each ZIP. These use the explicit
`external_portrait_native_identity_first_pass` policy: no cross-chat generation gate, but local follower acceptance
still requires accepted seed hashes and cross-expression comparison evidence. Spell icons still require restored
page crops. See `CHAT_BUNDLES.md`; older waiting instructions for bundles 007–015 are superseded.

**First-pass priority:** review each sheet, accept its passing cells, and flag failures with specific defects
using `queue.py defer`. Then move to fresh artwork. Do not interrupt first-pass throughput with repeated
single-cell repairs or keep mixing failed cells into new sheets. After the first pass over eligible artwork,
inspect the deferred ledger and group compatible failures into new 3×3 retry sheets. Failures remain required,
unfinished targets. Review retained outputs before generating duplicates; never lower acceptance standards.

## Authoritative scope and full accounting

- Inventory **every file** in `assets_dev/engine/icons/` and `assets_dev/worlds/*/icons/`, recursively, as recorded
  in scope.json. These directories include shared UI, items, portraits, legacy UI, world presentation, imported art
  and support files. Do not apply one generic imagegen treatment to the entire folder.
- Restore all referenced shared HUD/screen bitmap assets and required dynamic states: spell icons, inventory/shop
  icons, equipped variants, party/NPC portraits, UI animation frames, chest backgrounds and travel presentation.
  Include desktop, standard/expanded, mobile, hover/pressed/selected, disabled and conditional variants actually
  supplied by the source. Reuse shared state files where the original aliases them; do not invent extra variants.
- Resolve the conservative C++/table matches and naming-family candidates against their consumers. Same-name
  engine/world copies are not automatically interchangeable; preserve mount selection and namespaced provenance.
- Every file without a proven use still needs an explicit disposition. Trace source data/code and existing import
  provenance. Default to restoring plausible UI dependencies rather than dropping them merely because a static
  search found no literal. Evidence-backed obsolete UI, unrelated art and utility data can be retained/excluded
  from this HUD restoration queue with a precise reason. Unknown is unfinished, not excluded.
- Account for font dependencies and generated/external graphics in inventory.json. Use the existing faithful font
  pipeline for glyphs. Generated minimaps, text, coloured quads and save/beacon captures are not imagegen jobs.
  Creature sprites and house video used inside UI remain owned by their respective pipelines; record their links.
- Find any additional HUD images loaded from outside the icon roots, including world/custom presentation paths,
  during the usage review and add them explicitly. Do not claim arbitrary future mod coverage.
- Source the missing referenced names from the native/import sources or prove that their use is obsolete.
  Required missing artwork is a blocker to 100% completion; it is not an accepted empty/placeholder export.

All folder rows start as `pending_classification`: the route labels are batching hints, not exclusions or visual
approvals. A whole-folder census closes accounting gaps; it does not mean that all files are currently drawn by the HUD.
Existing MM9/imported/generated artwork also needs provenance review before deciding which image is the native
dimension baseline—never blindly double an already enhanced export again.

## 1. Freeze targets and prepare resumable work

1. Read the inventory README and the relevant renderer/asset-loader references it links. Rebuild with `build.py`
   and `prepare_scope.py` only before work starts or as an explicit source-drift reconciliation. Keep accepted job
   state separate from these generated inventories; rerunning an inventory must not erase progress.
2. Give every scope row a disposition with evidence: `restore`, `reuse_verified_x2`, `alias_verified_x2`,
   `retain_non_target`, or `missing_required`. Preserve unclassified rows until resolved. Do not reduce scope to
   a convenient subset to satisfy a progress percentage.
3. Freeze `expected_targets.json`: source path/hash, namespace, native size, exact x2 size, every usage/state,
   transparency/palette rules, logical rectangle/anchor, animation/variant group and output path. Track every
   alias back to a real, dimension-checked accepted artifact. Byte hashes are deduplication candidates only;
   verify native canvas and rendered appearance/compositing before sharing work.
4. Prepare a compact resumable queue under this project: stable job ids, explicit target members, fixed reference
   cell rectangles/gutters, exact prompts, cleanup route, dependencies and per-target acceptance state. Keep raw
   outputs, submitted prompts, source references and validation results. Accept and stage passing cells independently;
   a failed or questionable sibling does not block them. Mark each such cell deferred with a concrete inspection
   reason and retained evidence, then continue fresh first-pass work. A batch is fully complete only when all of its
   target cells pass; revisit compatible deferred cells together in later retry batches.
5. Inspect representative originals and native screenshots to establish visual treatment and grouping. Use the
   existing accepted terrain/decor restoration for fidelity, not as a universal texture style for every UI material.

## 2. Batch by visual treatment and dependencies

Use the **imagegen skill and built-in imagegen tool** for restoration artwork. The requested multi-icon sheet is
one generation image, later extracted into individual assets. No paid API/CLI fallback unless explicitly authorized.
Inspect references before generation. No new 3D workflow or UI redesign.

| Asset family | Initial generation grouping |
| --- | --- |
| Spellbook school pages / large backgrounds | One complete page/background, accepted before dependent crops |
| Spellbook icons | 4–6 normal/hover pairs (8–12 cells), each with its accepted page crop |
| Small inventory icons / buttons | Up to nine similarly sized related cells in 3×3; keep complete state sets together |
| Large detailed inventory art | Smaller batches with enough pixels for the exact x2 output |
| Player faces | One identity, 4–8 expressions/frames, with an accepted identity reference |
| NPC portraits | 3×3 when each face has sufficient detail resolution; preserve distinct identities and framing |
| Equipped variants / paperdoll pieces | One item/body family with compatible poses and shared registration |
| UI animations / hourglass / journal effects | Consecutive frames from one sequence, typically 4–8 initially |
| Frame strips / adjoining borders | Small coordinated groups with fixed join profiles |
| Fonts, palettes, generated graphics, documentation | Relevant deterministic pipeline or evidenced non-target disposition |

3×3 is the production default for suitable small art, not a requirement to fill every sheet. Split if per-cell detail, identity or registration
degrades. Do not batch unrelated cleanup modes or backgrounds just to reduce call count. Fewer calls do not imply
proportional wall-clock savings. Inventory trials are recorded in `experiments/eight_items_v1/` and
`experiments/nine_items_v1/`; other treatments still require their own representative review before expanding.
Keep individual exact-x2 exports and acceptance records, but generate, extract and inspect a combined comparison
sheet per batch. Retry only visibly defective cells or inseparable state groups, preserving successful siblings.

For spellbook icons follow the README's **page-first** recipe: accept the restored school page, crop the actual
resolved icon rectangles with context, and use those crops plus both native states to make matched unhovered/hovered
art. Preserve the same background pixels between states. Record accepted page hashes/crop rectangles as dependencies;
page changes invalidate the corresponding icon reviews. Preserve pressed/hover aliases and any baked-in page artwork.

## 3. Export, inspect and resume

- The isolated preview must support preferring restored icons while falling back to original files that have not
  been restored yet. Preserve world/mod precedence. Propagate each resolved file's actual physical tier/native
  logical canvas through loading, dimension queries and hit testing; do not divide every icon by a global x2
  preference. A 64×64 restored version of a 32×32 icon and its 32×32 original fallback must both occupy 32×32
  logical pixels. Cache that information at load time, without resampling fallback files during rendering.
  The engine implements this via `[video_quality] prefer_restored_icons=true`; see README.md for paths and semantics.
  Keep validating exact native/x2 canvases and state registration in each restored batch.
- Validate a deliberately mixed preview containing a restored x2 icon and an original x1 fallback, including
  inventory placement, state changes and picking. Record fallback use in validation: acceptable during partial
  restoration, but a required target that falls back is not counted as restored or accepted by the completion gate.
- Treat generated sheets as masters. Validate every expected cell; register to the reference layout, then extract
  into each target's exact x2 full native canvas. Do not trust imagegen to return exact dimensions or grid spacing.
- Preserve silhouette placement, margins, thin features, colour-key/alpha semantics and animation/state alignment.
  Use actual native palettes. Keep opaque UI backgrounds, cutout items and translucent effects on appropriate
  cleanup paths. Never apply generic opaque-prop erosion to a glow or to tiny UI strokes.
- Imagegen must contribute sufficient restored detail at final resolution. A nearest-neighbour enlargement or
  resizing a tiny generated cell merely to meet dimensions is not an accepted restoration.
- Check every exported state at its final x2 size; use combined contact sheets for efficiency. Review pairs by
  alternating states and animations with native timing. Reject shifts, clipped icons, changed identity, unintended
  text/symbol changes, halos, seams or background colour changes on hover.
- Reuse verified accepted work and record deferred items with their specific defect. Finish the first pass before
  batching compatible failures for retries; retain successful siblings. Use `next --phase first-pass` for fresh
  work, `next --phase review` for unreviewed retained outputs, and `next --phase retry` for the deferred ledger.
  Deferred/missing/in-flight work remains unfinished. On resume inspect checkpoints/results before resubmitting.
- Validate the isolated UI preview by representative screen/state families and affected layouts, including mobile
  geometry, rather than compiling or running a game scenario for every bitmap. Use the approved wrappers and exit
  owned game processes. Preserve the user's ordinary saves/settings and the peasants enhanced launcher.
- Stage exports in this project and a separate preview asset root. Do not overwrite originals or globally install
  into default launchers as part of this generation goal. Necessary reversible preview wiring is part of the work;
  document any engine asset-loading limitation instead of masking it with incorrect scale or runtime placement.

## Completion gate

The goal is complete only when:

1. Every census row and newly discovered dependency has an evidenced final scope disposition; none remain unknown.
2. Every frozen target/state/variant has an accepted or verified reused/aliased output. Required missing references,
   failed cells, deferred jobs and in-flight calls are zero. Non-target accounting is reported separately from restoration coverage.
3. Every exported bitmap passes `width == 2 * native_width` and `height == 2 * native_height`. For packed atlases,
   reconstruction must return the full exact x2 canvas. State aliases, transparency, placement and timing remain correct.
4. All spellbook pairs depend on accepted page versions and pass full-page normal/hover review without seams.
5. The source-to-output manifest is complete, hash-checked and reproducible; raw masters/prompts/registration metadata
   and brief visual acceptance notes are retained. No dimensions or missing states are silently repaired by fallback.
6. Representative in-game screen checks pass at the same logical UI size, and the isolated preview can be launched
   by the user. Report target/restored/reused/aliased/non-target counts, preview command and any scope limitations.

Do not call this complete because every generation call returned, because all files were processed once, or because
the first HUD screenshot looks good. Required source gaps or a tool blocker must be reported honestly with saved progress.

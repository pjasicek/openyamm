# Shared HUD restoration inventory

**Latest approved in-game HUD design, 2026-09-27:**
[Obsidian refinement 04](../hud_concepts_20260927/README.md#latest-approved-design), with a preserved screenshot
and interactive mockup. Use it as the design baseline when revisiting the gameplay HUD; runtime integration remains
future work.

**Accepted PC portraits, 2026-09-27:** [Transparent portrait revision](pc_transparent_acceptance_20260927/README.md).
All 4,032 reviewed portraits across 72 active families replace the prior accepted PC artwork and are installed
in `assets_dev/engine/icons_x2/`. The [port 9100 preview](http://127.0.0.1:9100/level_generation/ui/hud_inventory/pc_transparent_regen_20260927/index.html)
shows the accepted exports; the canonical index and ledger point to their new revision.

**Current workspace, 2026-09-26:** [Workspace and redeployment guide](WORKSPACE.md).
The [runtime installation](runtime_install_20260926/README.md) consolidates **9,920 accepted exact-2× exports**
and installs them in development assets, with all 726 active placements and 79 inventory fits imported.
Original MM6–MM8 icon roots are archived outside runtime mounts; MM9 retains its separate native scope.
`checkpoint/state.json` is the live ledger. The dated acceptance/export directories are immutable snapshots.
The older preparation and audit sections below describe historical states, not remaining work.

**Earlier review plan:** [Second-pass plan](SECOND_PASS_PLAN.md) consolidates per-icon detail, artifact, sampling,
registration, transparency and family review, acceptance/staging, and preparation of targeted third-pass repairs.
The plan is prepared; execution has not started.

**GUI compositing correction (2026-09-22):** Restore separable overlay objects on transparent PNG canvases;
omit copied panel backing while preserving the object's own materials and native placement. Complete pages and
backgrounds remain opaque. See [foreground/background handling](MATTE_AND_FITTING.md#gui-foregrounds-over-separately-restored-backgrounds)
for prompting, historical-contract overrides and review requirements.

**Current restoration handoff (2026-09-16):** [Dense64 work bundles](chat_bundles/dense64_20260916/README.md)
prepare 5,954 remaining unique small-art targets on 188 sheets. See [batching limits](BATCHING_DENSE64.md) and
[returned/assigned work](CHAT_BUNDLES.md). The initial preparation snapshot below is historical;
`checkpoint/state.json` and retained return/experiment manifests track subsequent work.

Start with [the searchable visual catalogue](index.html). It inventories the shared **MM8-style interface used across
worlds**, not separate MM6/MM7 HUD designs. This package prepares source classification, exact-x2 targets and generation jobs. No restoration artwork has
been generated or installed. One redundant mobile YAML reference to absent artwork was removed during source cleanup.

For a future restoration run, use **[GOAL.md](GOAL.md)** as the `/goal` handoff. It defines full folder accounting,
classification, page-first spell icons, generation-sheet batching, resumable acceptance and exact x2 completion.
Classification/queue preparation is complete; see [PREPARATION.md](PREPARATION.md) and [COMPLETION.md](COMPLETION.md).
No generation has started. The verified handoff contains 14,780 targets and 4,268 jobs. See [QUEUE.md](QUEUE.md)
for the executable queue and the boundary between preparation and artwork acceptance.

The complementary **[whole-folder census](scope.csv)** accounts for every file under the engine and world icon roots:
**14,736 files, including 14,735 bitmaps**. Of those, 10,553 files have associations in the usage inventory and
4,183 have none (including one documentation file). The census retains its original pending flags; final
dispositions are stored separately in [classification.json](classification.json). [scope.json](scope.json) retains hashes, native/exact x2 sizes,
usage references and duplicate candidates; [scope_summary.json](scope_summary.json) records counts and roots.
The census sizes come from current source files; its original `native_baseline_verified` flags are not updated in place.
Dimension evidence is recorded in the source/import/authored audits and frozen [expected_targets.json](expected_targets.json).
For already enhanced imports, establish the actual native baseline before freezing restoration targets.
Run `python3 level_generation/ui/hud_inventory/prepare_scope.py` after building the usage inventory to regenerate
this census. Never store accepted generation state in these overwritten inventory outputs.

Current snapshot:

| Scope | Count |
| --- | ---: |
| Named assets in gameplay.yml + gameplay_mobile.yml | 84 |
| Shared UI layout files, including menus and related screens | 27 |
| Explicit YAML asset/state references | 1,017 |
| Distinct YAML asset names, case-insensitive | 587 |
| YAML names with source bitmaps | 586 |
| Generated YAML asset placeholders | 1 |
| Missing YAML bitmap names | 0 |
| All inventoried names including dynamic families and static candidates | 10,328 |
| Distinct source files / unique file hashes | 10,608 / 9,310 |
| Font names from YAML and code | 12 |

Counts overlap between categories. The broad inventory is dominated by player/NPC portraits, inventory items,
and fitted equipment artwork; these are not merely HUD skin images. Candidate
families enumerate available frames/variants conservatively and can include unused historical members.

## What to use

- [index.html](index.html): offline, searchable preview cards; filter by screen, gameplay HUD, YAML references,
  dynamic-only assets or missing files. Expand a card for element ids, states, source lines and alternate source files.
- [inventory.json](inventory.json): full references, per-use logical layout sizes, source file hashes/dimensions,
  expected x2 canvases, existing x2/x4 siblings, dynamic format families, fonts and generated dependencies.
- [assets.csv](assets.csv): flattened restoration checklist, one row per normalized asset name.
- [summary.json](summary.json): counts and extraction limits.
- [build.py](build.py): reproducible scanner. Run `python3 level_generation/ui/hud_inventory/build.py` from the repository.
  It writes only this catalogue and its deduplicated thumbnails. Source assets and frozen sprite restoration jobs stay untouched.

Previews show the native file palette and alpha, without guessing colour-key removal. Magenta/teal backgrounds can
therefore appear. HUD bitmap loading uses magenta/teal keys; mapdir/micon also use black; item icons additionally
use palette index zero. These distinctions must be preserved by a future restorer. Hash deduplication here compares
file bytes, not palette-adjusted rendered appearances; it does not authorize merging different semantic assets.

## Why YAML alone is insufficient

The authoritative layout reader is `game/ui/UiLayoutManager.cpp`. All seven supported asset fields are inventoried:
default, highlighted, pressed, selected, frame, health_bar and mana_bar. The actual loaded gameplay layout list is
in `game/ui/GameplayUiController.cpp`; mobile is Android-only. Other screens load their own layouts. This catalogue
includes the entire checked-in engine UI directory, including legacy/standard/expanded variants, so a YAML
reference is not proof that a particular current desktop screen draws that element.

Additional families are traced through:

| Family | Source / selection |
| --- | --- |
| Player faces and paperdoll body/hand pieces | character_data.txt plus GameplayUiRuntime portrait naming |
| NPC/follower portraits | `npc%04u` in dialogue, party and HUD renderers; engine and world-local candidates retained |
| Inventory and shop items | items.txt `Pic File`; merged/base registry |
| Equipped item artwork | item icon + `v1`…`v5`, optional `a`; slot/doll/hand-pose selection in GameplayScreenRuntime |
| Portrait FX, flight, turn-based indicators | referenced icon_frame_data.txt animation groups, portrait_fx_events.txt |
| Rest sky and hourglass | `terra%04d`, `HGLAS%03d` in GameplayPartyOverlayRenderer |
| Journal hover animations | `IRA-1`…`IRA-4` + numbered suffix in GameplayPartyOverlayRenderer |
| Loading animation | `ia02-%03d` in LoadingOverlayScreen |
| Chest, travel and map presentation | matching references in chest_data, town_portal_switch, continent_settings, map_stats |
| Fonts | engine/fonts legacy FNT and faithful TrueType files/configuration |

Exact matching C++ string literals and presentation-table tokens have **candidate** labels. The scanner is not a
C++ compiler or a runtime call-graph analysis. It enumerates known naming patterns and existing files rather than
inventing missing frames. NPC and player frame-family scans deliberately include possible states beyond those
visible in a single screenshot. A missing dynamically constructed frame outside these existing-file families is
not automatically detected.

Asset resolution follows the HUD's bare-name convention into icons; PNG/BMP/PCX priority is recorded by file order.
All engine/world-local same-name candidates remain listed, because mounted world/mod priority is a runtime decision.
The first preview is a representative source, not a claim that every world resolves that file. Custom mods and
world-specific UI overlays outside `assets_dev/engine/ui` require their own scan before declaring runtime coverage complete.

Generated minimaps, save/beacon snapshots, text and coloured quads have no single restoration bitmap. Actor inspection
can show world creature sprites, and dialogue can show house video: those assets belong to the relevant world/sprite/video
pipeline, not the shared HUD skin queue. These boundaries are also recorded in `generated_and_external` in the JSON.

## Findings and proposed first restoration batch

- `MINIMAP` is generated content, not a missing bitmap. Restore its frame, controls and authored symbols.
- The redundant mobile `OutdoorBuffSkull_Immolation` reference to absent `asiR08` was removed. The existing body
  indicator still uses `asiL10`; source-repair provenance and reconciled hashes are recorded under `repairs/`.
- Eleven paperdoll-table names have evidenced non-target dispositions: four metadata-only beard fields and seven
  parts for reserved, unavailable character pc30. No substitute or additional native state was invented.
- Fonts already have faithful TrueType counterparts. Improve or use that pipeline rather than generating text with AI.

Use the **Gameplay HUD only** filter to start with the 84 names, then select one related screen such as Character.
Review legacy/mobile variants before scheduling a batch; some artwork is shared with several other screens. Keep
original logical dimensions and anchors while doubling source canvases. Restore button state sets and adjoining
frame pieces together. Inventory portraits, item icons and fitted equipment should remain separate tracked batches.

## Exact x2 export and multi-icon generation sheets

The engine supports incremental restoration with this startup setting (restart after changing it):

```ini
[video_quality]
prefer_restored_icons=true
icons=x1
```

Place exact x2 exports in `assets_dev/engine/icons_x2/` or the corresponding `assets_dev/worlds/<world>/icons_x2/`,
using the original lowercase stem. PNG, BMP and PCX are supported; a restored file wins even when its original has
another extension. Original `icons/` files remain the per-file fallback, including when no `icons_x2/` directory exists.
Packaged content uses the same sibling directories inside its ZIP. Package-qualified lookups retain their namespace;
unqualified lookups retain the mounted precedence within each tier.

`prefer_restored_icons=false` restores the ordinary `icons=` tier choice; its default is x1. The preference itself
is false by default, and enabled in this checkout's `settings.ini`. It affects icons, including HUD/menu art and
paperdoll pieces stored there; it does not change UI YAML or fonts. The engine tracks the selected file's actual tier:
a native 32×32 fallback and a restored 64×64 image both occupy 32×32 logical pixels, including inventory grid sizing
and opaque bounds. Image paths and uploaded texture dimensions are cached. Paperdoll pieces are fitted together when
the cached composite is rebuilt, not each frame. Each selected x2 texture uses four times the original pixel storage;
fallback images keep their native storage. No additional draw calls are needed for this preference.

Fallback is useful for incremental playtesting; it must not conceal incomplete restoration coverage in the final audit.
Restored canvases must be authored at exact x2; the loader does not infer native dimensions from arbitrary generated art.

Engine verification: 67 focused tests passed; [mixed/original inventory comparison](review/restored_icon_loading/README.md)
includes isolated in-game picking and placement checks.

User requirement: **every restored bitmap and every state/variant must export at exactly twice its own native
width and twice its own native height, with 100% coverage of the agreed restoration scope**. Use the full native
canvas, including transparent margins. Preserve logical size, alignment and anchors. If two native states have
different canvas dimensions, each receives its own exact x2 canvas; do not force both into one common output size.
The inventory's per-file `size` and `x2_size` fields provide the dimensional targets.

Batching small compatible icons into **3×3 imagegen sheets is the default**; see [BATCHING.md](BATCHING.md).
Prepare a fixed reference grid with gutters
and a manifest linking every cell to its source asset/state, native canvas and target canvas. Group related art
with similar sizes and restoration treatment. Use up to nine small/simple cells; detailed or large art needs
smaller batches, and page backgrounds are generated separately. Spell pairs, animation sequences and equipped
variants keep their specialized layouts and dependencies. Do not split related states or shrink oversized art
to fill nine slots. `queue.py batch-payload` supports small inventory execution sheets across frozen jobs.

Treat the returned image as a generation master. Inspect every cell for identity, completeness, alignment, clipping,
neighbour contamination and sufficient detail at the intended export size. Register the sheet to the reference
layout, then extract cells using recorded coordinates and place the accepted artwork on each exact x2 native canvas.
Imagegen is not responsible for pixel-exact final dimensions. Do not assume its grid spacing or object placement
is perfect, stretch individual silhouettes to fill cells, or hide inadequate generated detail behind a final resize.
Accept passing cells independently. When registration or fidelity fails, record the affected cell with a
concrete reason using `queue.py defer CELL --reason ...`, retain its raw attempt and crops, and move to fresh
artwork. Finish the first pass before inspecting and batching compatible deferred cells for retries; preserve
accepted siblings. Use `queue.py next --phase retry` to inspect the repair ledger. Deferred cells remain
unfinished and cannot count toward full restoration coverage.

The future exporter must reject an incomplete scope or any dimension mismatch: for every expected asset/state,
`output.width == 2 * source.width` and `output.height == 2 * source.height`. Retain explicit state aliases, and
reconstruct full canvases when validating atlas-packed outputs. Exact dimensions alone do not pass visual review;
missing, clipped or misregistered artwork remains unfinished. Keep generation sheets separate from any runtime atlas.

For spell icons, this batching scheme follows the page-first workflow below: each pair uses its own crop of the
accepted restored school background. Keep both states together and preserve that crop between them. Establish a
small accepted pilot before expanding sheet size. Fewer requests can reduce overhead, but generation latency,
per-cell detail and repair rates determine the actual time saved.

## Spellbook restoration order: page first, then matched icon states

User-specified workflow: **restore and accept each spellbook page background at x2 before generating its spell icons**.
The icons must visually belong to that restored page, including its paper texture, shading and surrounding artwork.
Do not schedule them as independent, context-free icon restorations.

1. Restore the relevant school background from `spellbook.yml` (for example, Fire uses `sbf000`). Preserve the
   native composition and logical page size; the 640×480 page becomes a 1280×960 source image at x2.
2. Resolve each spell's actual page-relative drawing rectangle, then crop that area from the accepted x2 page.
   Respect anchors, offsets and the original state canvases; YAML offsets are not necessarily top-left coordinates.
   Include a little surrounding context for generation and record the exact final crop separately.
3. Give imagegen that restored background crop **and both original icon states**. Generate the normal/unhovered
   and highlighted/hovered states as a matched pair, using the same page patch, registration, silhouette and scale.
   Preserve the native state difference; do not independently repaint or relight the background between states.
   If generating sequentially, use the accepted first state as an additional reference for the second.
4. Export each state to its exact x2 native canvas and retain the original transparency/compositing behaviour.
   Where state images include opaque page pixels, reuse the accepted page pixels outside the actual icon/state
   treatment so rectangular seams or hover-time background changes cannot appear. Check which artwork is already
   baked into the page before compositing, to avoid doubling it.
5. Review both states placed back on the **full restored page**, and alternate hover on/off in game. Check position,
   neighbouring icons, edge seams, colour continuity and hover/pressed feedback. Preserve existing state aliases:
   Fire/Torchlight, for example, uses `sbf01b` for default and `sbf01a` for both highlighted and pressed.

Future generation jobs should record the accepted page artifact/hash and crop rectangle as dependencies of each
icon pair. A page revision invalidates the corresponding crop-based reviews. This note records the workflow;
no background or spell-icon generation has been started by the inventory work.

This is complete extraction of the explicit shared YAML references, with an auditable dynamic dependency inventory.
It is not yet a claim of exhaustive runtime use across every screen, world, state and mod. Before declaring a full
restoration complete, reconcile these rows with actual asset-loader observations while exercising the relevant UI
states; a single gameplay screenshot cannot establish that coverage.

Validation: all inventoried bitmap files decoded for previews; no unknown YAML asset-state keys were found.
The HTML catalogue was opened through the approved browser capture wrapper and visually inspected. No game build
or gameplay tests were needed because this change only reads source data and writes a standalone catalogue.

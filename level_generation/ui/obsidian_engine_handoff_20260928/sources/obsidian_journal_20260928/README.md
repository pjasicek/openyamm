# Carved Obsidian — approved journal and map revision 01

**Current integration preparation:** [consolidated HUD handoff](../obsidian_engine_handoff_20260928/README.md).
It retains the approved justified bodies and widened submenu gutter alongside all other in-game overlays.

**USER APPROVED · revision 01 · 28 September 2026.** The user accepted the review with “OK I like this, prepare it”.
Use this as the current journal/map design reference. The [staged integration package](staging/README.md) contains
the approved graphics, font files and layout draft, with [recorded approval and captures](staging/approval.json).
The user's subsequent typography refinement uses **justified (block-aligned) bodies** for quests, story and autonotes.
Paragraph final lines and single-line entries remain left aligned; a paragraph continuing onto the next page stays
justified. The browser's **Body alignment** control compares the previous left-aligned treatment. The original approval
and three body captures are preserved under [staging/history/r01-left-aligned/](staging/history/r01-left-aligned/).

[Open the interactive browser review](http://127.0.0.1:8899/level_generation/ui/obsidian_journal_20260928/index.html).
This extends the [approved overlays r03](../obsidian_overlays_20260928/README.md) and its
[staging package](../obsidian_overlays_20260928/staging/README.md). Both are approved design handoffs;
runtime integration remains separate work.

## Screens

| View | Treatment and retained purpose | Preview |
| --- | --- | --- |
| Map / expanded minimap | New Sorpigal's installed map, fixed 300×300 logical viewport, three zoom levels, drag/pan, party arrow, discovered pins, coordinates and note strip. New compass icon and labelled zoom controls. | [Map](previews/map.png), [fully explored](previews/map-full.png), [sparse](previews/map-sparse.png), [pin note](previews/map-note.png) |
| Current quests | Plain native text entries and separators on dark stone; Previous/Next. No invented quest cards, objectives, rewards or tracking buttons. The reference preset shows Sulman's actual letter quest. | [Quests](previews/quests.png), [2092 state](previews/quests-reference.png), [long](previews/quests-long.png) |
| Story | Native Book2 title and Autonote body, bounded pages with the existing previous/next purpose. Empty state stays empty. | [Story](previews/story.png), [next page](previews/story-page-two.png), [2093 state](previews/story-reference.png) |
| Autonotes | All six existing categories: potions, fountains, obelisks, seer, miscellaneous and trainers. Separate generated illustrations on matching plates, with readable labels and clear selection. | [Notes](previews/notes.png), [fountains](previews/notes-fountain.png), [trainers](previews/notes-trainer.png), [2094 state](previews/notes-reference.png) |
| 2090 status strip | 2090 is a cropped **character-creation readiness strip**, not a journal screen. A separate short/long strip specimen shows soft ivory and the recreated Lucida family, with the original crop for comparison. This does not redesign the creation screen. | [Strip](previews/status.png) |

The root remains centred **640×480 logical**, shown at **1.875×** in a 1600×900 review stage. Widescreen side panels use
dark stone while the journal is open. Close returns to the approved HUD beneath; the outside toolbar can reopen it.
Four main navigation controls remain on the far right, with page/zoom controls and six note categories on the adjacent rail.
Button rectangles are regularized and kept clear of the ornament. Following the marked gap in **2105**, the text
viewport is **360×293 logical**, at `(101,96)`, giving **28.07 logical pixels** between the body and submenu column
(previously 11.07). Font and button sizes/positions stay the same; the page counter centres under the narrower body.
The map viewport retains its exact `(131,101,300,300)` rectangle.

Dark rough material, real alpha frame slices and the brass edge come from the approved package. Repeated corners/edges
surround the fixed book workspace. Text remains live. Book2 keeps the original calligraphic titles; Autonote keeps the
original 18px × 0.9 body scale. Heading colour is `#e4c793`, body `#e5dcc7`; Fondamento uses the already-selected
normal/hover/pressed/selected/disabled treatment. The accepted page counter is hidden in sparse reference mode.

## Art and provenance

Nine new individual transparent icons were produced using the **built-in imagegen tool**: map, quests, story and six
autonote categories. Every generated master is saved in [assets/generated/](assets/generated/), preserving its true alpha.
Notes reuses the approved journal + quill + ink **Books v2** icon. There are no generated labels or glyph strings in the art.
The exact [prompt set](generation_prompts.json), [original generated paths](generated_sources.json),
[source receipts](asset_sources.json) and [asset manifest](asset_manifest.json) are retained.

The New Sorpigal map is a lossless PNG conversion of **the currently installed**
`assets_dev/worlds/mm6/icons_x2/oute3.bmp`. It is not regenerated or taken from an unapproved minimap-art trial.
Exploration masks, pin locations and party marker placement are illustrative browser fixtures; they are not extracted
from a save and do not claim world-coordinate calibration. Runtime integration keeps the existing map transform,
reveal data, identification/unlock rules and pin data. The approved design changes its frame/controls only.

Quest, story and note strings are read from the installed shared English tables. Review fixtures may combine entries
that the current party has not unlocked. Story uses an actual MM8 table passage to stress long text, while the map
and sparse quest example match the supplied MM6 screenshots. Empty reference states preserve what 2093/2094 show.
The small text divisions reuse the installed `divbar` art. Earlier generated icon files are never overwritten.

## Draft for later implementation

[drafts/journal.yml](drafts/journal.yml) preserves every existing journal ID and input action. It references all exported
background, plate and glyph assets and adds explicit icon/label children plus an optional page-count field.
[review_geometry.json](review_geometry.json) records measured browser geometry; [reference_layouts/](reference_layouts/)
pins the originals. The [staged copy](staging/engine/ui/gameplay/journal.yml) is an approved **runtime layout draft**;
the renderer hooks below are still required before installation.

Runtime hooks still required:

- Reuse the existing `Engine::loadTrueTypeFontAtlas` / Fondamento descriptor in gameplay font loading, as described in
  the approved staging notes. The menu font path already supports it. Do not build another font subsystem.
- Preserve Autonote shapes and FNT metrics. The staged descriptor changes `black-ink` to the already-supported
  `tintable` presentation, allowing ivory text. The original descriptor is archived; the current UI layout audit finds
  Autonote only in the journal. Recheck consumers when integrating. Book2 remains the title face.
- `renderJournalOverlay` currently overrides main icon names with `IRA-*` hover animations and draws individual known
  elements. Bind the new state plates and live icon/label children instead of silently retaining that override.
  Honour existing visibility for map vs page controls and note categories. Use the existing localization path for labels.
- Keep native pagination, global quest/autonote/history data and unlock checks. Browser pagination measures real fonts
  to demonstrate fit; it is not a substitute for the existing native text-measurement path.
- Add shared native justification for these body paragraphs: distribute line slack between words after wrapping, retain
  left alignment on paragraph endings and single-line entries, and preserve paragraph continuity across page breaks.
  Keep glyph spacing/metrics and automatic hyphenation unchanged. The current parser supports only left/center/right,
  so the parseable draft records the requirement in its notes and `staging/design/theme.yml` instead of an unsupported key.
- Keep the existing map renderer and its input behavior: three zoom steps (384/768/1536), button zoom recentring on the
  party, wheel zoom, pan, note hover/selection and coordinates. Draw the new note strip and border around that output.
- Full-screen journal is independent of the gameplay party bar; do not expose clipped gameplay resource or minimap
  widgets in the side wings. The revised compact gameplay minimap remains the approved r04 design.

[Browser checks](browser_review.json) cover navigation, all six categories, sparse/empty states, native faces, long
text/page boundaries, map pan/zoom, note strip, non-overlapping controls, Close/Reopen and original comparisons.
The draft is parsed with the actual `UiLayoutManager`, and all new asset references resolve in the manifest.
No game build/runtime integration is claimed. Rebuild the handoff from its preserved approved sources with:

```sh
node level_generation/ui/obsidian_journal_20260928/check_browser.mjs
python3 level_generation/ui/obsidian_journal_20260928/prepare_drafts.py
python3 level_generation/ui/obsidian_journal_20260928/staging/prepare_stage.py
python3 level_generation/ui/obsidian_journal_20260928/staging/validate_stage.py
```

`prepare_assets.py` is the initial runtime-fixture import, not a routine approved-art rebuild step. It protects pinned
fonts/layouts from source drift. The reviewed Create font differs from the newer runtime version; see the
[recorded font difference](staging/runtime_font_differences.json) and reconcile it at integration time.

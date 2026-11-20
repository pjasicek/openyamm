# Journal runtime integration notes

The visual design is approved; this directory supplies assets and a concrete YAML draft. Runtime work belongs in the
shared gameplay/UI path. Preserve map-specific world data and the existing native journal mechanics.

## Asset and layout installation

Rebase `engine/ui/gameplay/journal.yml` against `reference_layouts/journal.yml` and the current runtime layout before
installing. Intended destinations are recorded in `manifest.json`; assets are base-owned under `assets_dev/engine/`.
Retain the legacy icon-package registration and lookup conventions. Do not install review screenshots, the New Sorpigal
map fixture, browser exploration masks, pin positions or `content.js` as gameplay content.

The draft includes every existing journal ID and interactive target. Button icon/label child rectangles now come from
measured browser geometry. Draw these children without giving them separate input targets. Existing handlers continue
to own Map/Quests/Story/Notes, six note categories, Previous/Next, map zoom and Close. All English labels are design
examples; bind through the existing localization system.

`GameplayPartyOverlayRenderer::renderJournalOverlay` currently draws individually named elements and overrides the four
main icons with animated `IRA-*` texture names. Remove that override for the approved skin and draw the new plate plus
icon/label children. Draw main selection and note-category selection from native state. Use `design/button_states.yml`
for normal, hover, pressed, selected and disabled appearance. The current layout schema has no disabled asset field;
choose those explicit staged PNGs in the shared button renderer rather than adding an ignored YAML key. Preserve the
selected border when hovering a selected entry. The main selected outline is `#dfbe78`, as recorded in the CSS recipe.

The draft still needs visibility/binding for `JournalMapFrame` (map view only) and `JournalPageNumber` (nonempty records
only). Disabled page/zoom controls must retain native input limits. Close returns to the current gameplay view.

## Drawing and geometry

- Centre the original **640×480 logical** workspace. The complete blank 1280×960 background scales with that workspace.
  Its frame, spine and right rail are already baked into this fixed-size skin; do not draw another border over it.
- Draw `obsidian_journal_backdrop_tile` behind the full viewport, including widescreen wings, repeated at its recorded
  logical size. Centre the pattern and retain the soft black shadow behind the journal. Hide gameplay HUD widgets while
  this full-screen journal is open; Close restores them through the current view behavior.
- Keep the map and hit rectangle exactly **(131, 101, 300, 300)**. The transparent map-frame PNG sits at
  **(118.2, 88.2, 325.6, 325.6)** above the map, with a clear interior. It does not expand the map input area.
- Preserve the existing map texture/vector-map renderer, coordinate transform, reveal mask, discovered pins,
  hover/selected note, party marker, drag/pan and three zoom steps (384/768/1536). Zoom buttons recentre on the party;
  keep current wheel behavior. No browser fixture is a replacement for native map state.
- The body viewport is **360×293**, at **(101,96)**, after the 2105 refinement. Its **28.07-logical gap** to the submenu
  column gives the justified text breathing room. Retain the existing submenu positions and font size, and centre the
  page counter under the body. Reuse native text measurement and pagination, including
  variable-length entries and localized strings. Quest/autonote dividers use the separate alpha divider; story remains
  uninterrupted paragraphs. Page count is live `page / total`, hidden for the map and empty content.
- Justify quest, story and autonote body paragraphs to both edges by distributing spare line width between words after
  wrapping. Keep final paragraph lines and single-line entries left aligned, with native glyph advances and no automatic
  hyphenation. A paragraph continuing onto the next page is not a paragraph ending: justify that last page line too.
  Preserve formatting runs, explicit paragraph breaks and source content. The current parser accepts only left/center/right;
  add shared native justification support during implementation. The draft records this in `JournalTextViewport.notes`
  and `design/theme.yml: body_alignment` rather than storing an unsupported alignment value. The browser comparison toggle
  is a review control, not an additional in-game setting.
- Body, titles, coordinates, notes and labels remain live text. Use the original quest/autonote/history tables, unlock
  checks and substitutions. Keep original sparse/empty behavior. No extra quest-card, reward or tracking semantics.
- Icon files are original high-resolution alpha masters. Render with aspect-ratio containment in the measured child
  bounds. Their display sizes differ between primary navigation, category buttons and the small top-left emblem.
- `obsidian_journal_status_strip` is a blank **2090 treatment specimen**, accompanied by Lucida sizing/padding in
  `design/theme.yml`. Apply it within the current character-creation status area when integrating that design. There is
  deliberately no full creation-layout replacement here; use the separately approved menu package for that screen.

## Font loading

The staged **Create** TTF is the exact approved browser font. A later runtime revision changes its glyph/advance tables
while retaining the same cell/baseline metrics; the previous overlay package already carries that newer revision.
`runtime_font_differences.json` records both hashes. Reconcile that existing font work and compare map coordinates/note
text before installing fonts. Do not copy this older global font over the newer one as an incidental skin-install step.

`GameplayHudCommon::loadHudFont` still looks up legacy FNT/PCX faces. Reuse the existing
`Engine::loadTrueTypeFontAtlas` path used by `MenuScreenBase::ensureFont` for Fondamento; its descriptor has
`metrics: freetype`, logical height 32 and baseline 25. The draft scales each label by its logical size / 32. Do not
substitute Fondamento into a legacy font's incompatible advance table or introduce another font subsystem.

For recreated Book2/Autonote/Create/Smallnum/Lucida, keep the faithful TTF path with native FNT advances and the original
cell heights/baselines. The staged Autonote descriptor uses the already-supported **tintable** presentation. The current
layout audit finds Autonote only in the journal; check new consumers when integrating and preserve dark-text consumers
through their text tint if any have been added. The original `black-ink` descriptor is archived in `reference_fonts/`.

Book2 titles stay at 30 logical pixels (shrink long titles only to 22.4); body is Autonote 18 × 0.9; Create handles map
text; Smallnum handles the page count. Body is soft ivory `#e5dcc7`, titles `#e4c793`, coordinates `#d0c7b0`. Match modest
shadows and all Fondamento highlight/pressed styles using the frozen CSS recipe. Black-ink shadow-only rendering cannot
be recoloured just by setting the text tint; install the prepared presentation change with the new journal skin.

## Native checks after implementation

Check a native outdoor and indoor map, three zoom levels and their limits, drag, wheel, visible pins and note selection;
all four views and six note categories; empty and multi-page content; long/localized titles and entries; selection,
hover/pressed/disabled controls; Close and reopening at representative UI scales/aspect ratios. Verify the ivory body
and native font metrics in the real atlas. Existing quest unlocks, journal entries and save state must remain intact.
Build only the normal game target when implementation requires it; this staging task does not require a game build.

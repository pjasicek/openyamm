# Carved Obsidian — extended overlay collection

**28 September 2026 · proposal 01.** [Open the interactive collection](index.html).

Fondamento is the **user-accepted button font**. The new screens, body-font pairing, paper and border in this
collection are proposals for review. The selected frame remains
[Carved Obsidian revision 06](../hud_overlay_study_20260927/README.md); the gameplay base remains
[Obsidian refinement 04](../hud_concepts_20260927/README.md#latest-approved-design).
The approved screenshots are preserved. This collection changes browser mockups only.

Local server: [open the collection](http://127.0.0.1:8899/level_generation/ui/obsidian_overlays_20260928/index.html).
The page also runs directly from `index.html`, with its two sibling study folders present. Fonts and art are local.

## What to review

| Tab | Proposal and interactive comparisons |
| --- | --- |
| Inventory | Engraved grid, subtle inset alternative, or original grid. Click actual items to inspect them. |
| Stats | Grouped attributes, vitality, experience, combat and all six character resistances. Select a value to inspect. |
| Skills | Four skill groups; separate mastery, rank and upgrade columns. Hover `+` for cost; click to spend sample points. |
| Awards | Scrollable record on vellum or dark stone, using actual strings from the merged awards table. |
| Rest | Real sky and hourglass art, eight-hour rest, food cost, dawn/hour/five-minute waits and date. Buttons advance a sample clock. |
| Party quickref | All fourteen original fields, including Name, for one or five members. Both damage rows remain. |
| Dialogue | Indoor house or outdoor NPC; short, medium, long, overflowing or custom text. Height follows wrapped content. |
| Inspect | Item, monster, stat, skill, spell and buff examples; width and text-length controls; dark or light reading surface. |
| Buff icons | All 22 party effects at equal icon-box size; active HUD strip supports four plus overflow or two rows. |
| Frame & paper | Resize the window, show the eight cuts, or place the actual transparent frame over a checkerboard. |
| Fonts & colour | Same text on both surfaces, with proposed or recreated reading fonts and ivory/white stone-text comparison. |

The toolbar changes the reading fonts and surface across the collection. Fondamento stays on action labels and
headings. Full screen enlarges the game composition; Escape leaves full screen. Inspect windows also close with Escape.

## Design recommendation

Use the carved frame as the common outer structure. Keep the dense character pages, inventory and quick reference
dark; use warm vellum for sustained reading in dialogue, awards and inspectors. The surface switch also demonstrates
a fully dark alternative. Retain worn stone, quiet brass and sculpted corners, with most ornament at structural edges.

Use **Fondamento** for buttons and section headings, **Source Serif 4** for paragraphs, and **Source Sans 3** for
dense labels, values and timers. The latter two keep paragraphs and numerical comparisons open and legible without
requiring decorative lettering everywhere. The recreated **Arrus** and **Lucida** option retains more of the familiar
sloping letterforms. This is a font-family comparison inside the new layout, not a pixel reconstruction of every old
screen's font mapping. Nominal sizes differ to account for the fonts' different visible letter heights.

| Role | Proposed colour |
| --- | --- |
| Main text on stone | Soft ivory `#e5dcc7` |
| Secondary text on stone | Muted ivory `#bdb6a2` |
| Headings on stone | Pale brass `#e4c793` |
| Paragraphs on paper | Charcoal ink `#292c24` |
| Secondary text on paper | Olive charcoal `#505143` |
| Headings on paper | Umber `#72532f` |

The white comparison changes stone text to `#ffffff` and headings to the existing inspector yellow `#ffff9b`.
It leaves dark ink on paper. Numbers use stable widths where supported. Static surfaces and text remain still;
the accepted button highlight/press treatment supplies feedback without an idle glow animation.

## Geometry and content retained

The browser composition is 1600 × 900. The centred full-screen workspace remains 1200 × 900, representing 640 × 480
at 1.875×. It reuses the accepted full-screen viewer, including the quiet top rail, rough carved basebar, smaller hanging
shields, empty-slot banners and the final portrait/bars offset of **3 right, 5 down**.

The [character layout](../../../assets_dev/engine/ui/gameplay/character.yml) places the inventory page at `(0,24)`
and its grid at `(7,8)` inside the page. Therefore the authoritative grid starts at **(7,32)**, has size **448 × 288**,
and contains **14 × 9 cells of 32 × 32**. In this study that is stage rectangle **(213.125,60,840,540)**. Both new cell
treatments use that exact rectangle. The original-comparison crop includes its old rim, so its image bounds are larger
than the actual hit grid. The prototype's item arrangement and footprints are illustrative; it does not edit item data.

The equipment column and its paperdoll remain the same source capture. House dialogue keeps the original video
rectangle and aspect, with a growing text sheet over its lower portion. The whole-frame geometry, characters and
existing video art are not regenerated. The rest panorama also retains its aspect ratio.

Source content/layout references:

- [Character pages](../../../assets_dev/engine/ui/gameplay/character.yml): seven attributes, HP/SP/AC, age/level/XP,
  combat values, six resistances, condition, quick spell, skill groups/points and awards.
- [Rest](../../../assets_dev/engine/ui/gameplay/rest.yml) and
  [quick reference](../../../assets_dev/engine/ui/gameplay/quick_reference.yml): the existing actions and fields.
  `QuickReferenceRows` in [GameplayPartyOverlayRenderer.cpp](../../../game/ui/GameplayPartyOverlayRenderer.cpp)
  has fourteen entries including Name; the new table retains thirteen body rows plus that name header.
- [Awards table](../../../assets_dev/engine/data_tables/english/awards.txt): real award strings; the mixed-world
  selection is a text-length specimen, not a claim about a saved party's accomplishments.
- [Dialogue layout](../../../assets_dev/engine/ui/gameplay/dialogue.yml) and
  [GameplayDialogueRenderer.cpp](../../../game/ui/GameplayDialogueRenderer.cpp): `DialogueFrame`, `DialogueFrameEndCap`,
  text measurement, width overrides and dynamically computed frame height.
- [Item](../../../assets_dev/engine/ui/gameplay/item_inspect.yml),
  [actor](../../../assets_dev/engine/ui/gameplay/actor_inspect.yml),
  [character](../../../assets_dev/engine/ui/gameplay/character_inspect.yml),
  [character detail](../../../assets_dev/engine/ui/gameplay/character_detail.yml),
  [spell](../../../assets_dev/engine/ui/gameplay/spell_inspect.yml) and
  [buff](../../../assets_dev/engine/ui/gameplay/buff_inspect.yml) inspector layouts.

Names, values, descriptions, party composition and sample interactions are review fixtures, not gameplay data exports.
The monster specimen includes its image, effects, HP, AC, attack, damage, spell and **all ten resistance fields**.
The actual runtime's knowledge/identification restrictions must still determine which values it reveals.

## Shared border and paper

The existing inspector layouts already use a background plus **four corners and four edges**. Their mounted asset
named `parchment` is presently a dark stone texture. This proposal therefore extends that construction, with a new
reading surface and shared art, rather than requiring a separate window renderer for every inspector.

New artwork generated with built-in imagegen:

- [Whole transparent border](assets/generated/frame-v1.png): original **1536 × 1024 RGBA**, preserved unchanged.
- [Trimmed border master](assets/generated/frame-cropped.png): exact crop `(48,72,1488,952)`, 1440 × 880.
- [Separate vellum](assets/generated/vellum-v1.png): original **1254 × 1254 RGB**, preserved unchanged.
- [Eight slice coordinates](frame_slices.json), [exact generation prompts and raw paths](generated_prompts.json),
  [source hashes](asset_sources.json), and [alpha measurements](alpha_verification.json).

The frame has real transparent pixels, not a painted checkerboard or a paper-filled opening. Alpha is 0–254;
82.55% of its pixels are exactly transparent. The central 1000 × 540 sample contains only alpha 0–1, and the four
outer corners are zero. No alpha repair was needed. The checkerboard shown in the viewer is a separate CSS layer.

The four corner cuts are 164 × 164 source pixels. Top/bottom edge tiles are 256 × 164; left/right are 164 × 256.
The browser draws corners at **58 × 58**, and repeats the edge strips at the same scale, clipping the final repeat.
There is no centre slice. The dialogue sheet uses the top and side pieces and meets the party bar at its open bottom.

The paper is drawn independently at **627 × 627 review pixels**. Increasing the window reveals more of the sheet;
it never scales the grain to the window's dimensions. At larger extents the subtle texture repeats. A larger paper
master could extend the crop-only range, but a fixed-scale texture remains necessary to prevent stretched fibres.
The border and paper are visually reviewed browser assets; any later atlas/mipmap export still needs its own seam and
alpha-edge check at the engine's actual rendering scales.

For runtime: measure the chosen font's wrapped text at the intended width, add padding/title/footer, fit the result
inside the viewport, then draw paper, edges/corners and content. Keep one shared skin/palette definition across the
existing inspector owners. Keep font size steady for long text. This study proposes bounded scrolling when text no
longer fits; the current dialogue renderer can fall back from Arrus to Create beyond its primary-height threshold.
The scrolling proposal is **not implemented in the engine here**. Existing hover/hold inspection input and placement
should remain separate from this graphics change; the browser's persistent click-to-inspect windows aid review.

## Buff illustrations without lettering

The catalogue covers the **22 current party-buff slots**, inherited from the earlier
[buff research](../hud_concepts_20260927/buffs.js). It does not add personal effects to that count or claim that all
22 normally coexist. Four earliest expiries plus `+N` remains the compact default; two rows show eight plus `+N`.

All coloured spell PNGs are unchanged copies from `assets_dev/engine/icons_x2`. In these installed families the
coloured illustrations are in the **A** files; the B files are the sepia counterparts. The lettering is excluded by
per-illustration display polygons, not by a colour key. That avoids erasing green objects while also removing brown
rune rows. The content bounds are then fitted, preserving aspect, into **36 × 36** HUD boxes or **44 × 44** catalogue
boxes. Timers remain separate live text. The catalogue's ordinary spell names are review labels, not baked glyphs.

[Clipping data](buff_art.json) and [browser helper](buff-art.js) preserve the original source art and document each
crop. A few silhouettes use close crops where lettering approaches the art; this is a reuse proposal, not newly
painted spell art. A later raster export can apply these same masks to separate buff thumbnails, preserving the full
spellbook illustrations. Avoid stretching each illustration to a square.

The older HUD viewer opts into these thumbnails only with `buffArt=clean`. Its default and approved image keep the
previous illustrations. The new collection requests the cleaned version and leaves the accepted controls and party
layout in place.

## Fonts and later integration

- [Fondamento](https://github.com/google/fonts/tree/main/ofl/fondamento) is reused from the accepted
  [button study](../hud_overlay_study_20260927/BUTTON_TYPOGRAPHY.md), with its locally bundled licence and state recipe.
- [Source Serif 4](https://github.com/adobe-fonts/source-serif) and
  [Source Sans 3](https://github.com/adobe-fonts/source-sans) are locally bundled variable TTFs from Google Fonts'
  official repository. Their [Serif licence](assets/fonts/SourceSerif4-OFL.txt) and
  [Sans licence](assets/fonts/SourceSans3-OFL.txt) are included. Download URLs and hashes are in `asset_sources.json`.
- Recreated Arrus/Lucida are unchanged copies of the project's existing faithful TTFs. The current engine mixes
  Create, Lucida, Arrus, Comic and SMALLNUM depending on screen and role; this study does not silently replace them.

The current [FontAsset loader](../../../engine/FontAsset.cpp) attaches TTF replacements to legacy FNT metrics and
Windows-1252 coverage. A future integration needs explicit metrics for the new faces, rather than dropping them
under an unrelated FNT descriptor or forcing their letters into old widths. Reuse the shared FreeType/atlas path,
cache the limited palette, and preserve existing data and hit rectangles. Browser Unicode support does not establish
runtime localisation support.

## Review artifacts

[Browser review report](browser_review.json) records layout, asset/font loading and interaction checks. It covers
grid bounds, contained item art, inspector dismissal/focus, skill cost, rest time/food, all quick-reference fields,
dynamic dialogue/overflow, the six inspector types, buff overflow, font switching and fixed corner/paper scale.
No game build, game launch, mounted-asset installation or save modification was performed.

Representative captures: [inventory](previews/inventory.png), [inset grid](previews/inventory-inset.png),
[stats](previews/stats.png), [skills](previews/skills.png), [awards](previews/awards.png), [rest](previews/rest.png),
[quick reference](previews/quickref.png), [indoor dialogue](previews/dialogue.png),
[outdoor dialogue](previews/dialogue-outdoor.png), [monster](previews/inspect-monster.png),
[spell](previews/inspect-spell.png), [dark inspector](previews/inspect-stone.png), [buffs](previews/buffs.png),
[enlarged buff illustrations](previews/buff-art-detail.png),
[type comparison](previews/type.png), [recreated fonts](previews/type-native.png),
[border alpha and cuts](previews/materials-alpha.png).

`prepare_assets.py` recreates byte-for-byte review copies, exact border crops and the SVG clipping catalogue.
It does not invoke image generation, download fonts, or change any source assets. The generated originals and
downloaded fonts must already be present.

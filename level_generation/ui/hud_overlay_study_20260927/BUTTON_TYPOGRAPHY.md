# Button lettering and states — proposal 01

**2026-09-28: the user accepted Fondamento.** It is the chosen button face for subsequent Obsidian designs.
The other typefaces remain comparisons. The [extended overlay study](../obsidian_overlays_20260928/index.html)
uses the accepted face; runtime integration remains separate work.

Open [the interactive comparison](buttons.html). This is a proposal layered over Carved Obsidian revision 06;
it does not supersede that frame reference or the approved gameplay HUD. The normal frame viewer still opens with
revision 06 lettering. Its new **Button lettering** control can preview the three candidates.

## Findings from the actual assets and code

The familiar Stats, Skills, Inventory, Awards and Exit lettering is part of the button artwork. It is not a label
drawn with the ordinary Arrus/Create/Lucida UI font. Each word has three separate restored textures in the active
`assets_dev/engine/icons_x2/` package:

| Label | Normal | Highlight | Pressed |
| --- | --- | --- | --- |
| Stats | but20u | but20h | but20d |
| Skills | but21u | but21h | but21d |
| Inventory | but22u | but22h | but22d |
| Awards | but23u | but23h | but23d |
| Exit | but24u | but24h | but24d |

[Character layout](../../../assets_dev/engine/ui/gameplay/character.yml) maps U/H/D to default/highlighted/pressed,
with 75×26 logical bounds. The restored PNGs shown in the comparison are 150×52. Copies are unchanged and their
hashes are recorded in [button_sources.json](button_sources.json). The selector above the original samples switches
between all five labels and all three states. These are the current restored source textures, not a claim that the
PNG pixels are untouched 1998/2000 originals.

[GameplayHudCommon::resolveInteractiveAssetName](../../../game/ui/GameplayHudCommon.cpp) chooses pressed art when
the mouse is held inside an interactive element, then hover art, otherwise normal art. The character renderer in
[GameplayPartyOverlayRenderer.cpp](../../../game/ui/GameplayPartyOverlayRenderer.cpp) also forces the current
Stats/Skills/Inventory/Awards page to its pressed texture before applying that pointer result.

Visually, the appeal is the combination of broad-pen strokes, sweeping capitals, high stroke contrast, dark ink
with a pale cut edge, and a physical bevel. The H textures add a warm yellow light behind the lettering; D changes
the depth and lettering position. Merely changing a flat font colour misses much of that effect.

The revision 06 browser mockup declares Georgia with a system-serif fallback. It uses warm ivory, a small dark
shadow, brighter hover and a gold selected slab. It has no separate `:active` treatment. Georgia is not bundled,
so its exact fallback also depends on the machine. The proposed faces are bundled for a repeatable comparison.

## Recommendation

Use **Fondamento Regular** for short action labels, with pale-gold raised lettering on the existing dark stone
buttons. It is my preferred visual compromise: calligraphic capitals and terminals, open lowercase shapes and
enough weight to survive at the inventory tab size. The browser uses 25 review pixels, approximately 13.3 legacy
logical units at this study's 1.875 scale. Match visible cap height and baseline, rather than applying the same
numeric font size to every face.

The same study also offers:

- **Almendra Regular**, 26 review pixels: sharper and more medieval, with narrower, more angular forms.
- **OpenYAMM ENDGAME Faithful**, 30 review pixels: less flourish, stronger broad-pen serif weight; already available
  in the project. Its smaller ink height within the em requires a larger nominal size.

None of these is claimed to be the historical typeface used in the painted tabs. An exact reconstruction would
be a separate alphabet-design task: the five labels alone cannot establish every letter, accent or numeral.

Keep one chosen typeface and optical size across inventory tabs, Close/Cancel, Rest, journal/menu actions and
similar short text buttons. Open dialogue/service rows can share the lettering, colours and input response while
keeping their existing row layout. Icon-only controls use the same frame/response rules with the current artwork.
Portraits, buffs, sliders, checkboxes and other specialised controls keep their own appropriate visual affordances.
Paragraphs, tooltips and compact numerical readouts should retain their readable body/number fonts.

## Shared state recipe

| State | Lettering | Surface / response |
| --- | --- | --- |
| Normal | Pale gold `#e8d1a4`; a restrained top light and dark lower edge | Worn raised brass rim, dark textured centre |
| Hover | Warmer ivory `#fff0c0`; soft local gold light | Slightly brighter upper edge, about 110ms transition |
| Held press | Duller gold `#d7bc86`; move ink down one review pixel | Immediate recessed bevel and darker centre |
| Selected tab | Gold `#ffe3a8`, stable position | Persistent inset gold rim and warm stone; still responds to hover/press |
| Disabled | Muted `#888b7b`, readable silhouette | Quiet rim; no hover light or press response |
| Keyboard focus | Preserve current state | Fine outer focus edge; does not falsely imply selection |

No font-weight change between states, so words do not resize. No idle pulsing or animated grain. Pressing does not
move the hit target, its neighbouring controls or the frame. Focus is independent of selected/pressed; a tab stays
selected after the pointer leaves, while an action such as Close does not. The browser demonstrates mouse, native
keyboard button activation, disabled and forced state samples. Reduced-motion preference removes transitions.

The study renders one live label above one reusable blank surface. It reuses existing rough stone; it does not
generate or repaint words. The sample text field demonstrates different label lengths with wrapping at a maximum
width. In the fixed inventory row, labels must be checked against the available width and side rivets; translation
must use a declared fit/wrap/layout policy rather than distorting glyph widths.

## Proposed runtime implementation, not installed here

1. Put the shared button font, blank frame art and state palette in global engine/base UI content. Use a single
   nine-slice surround for framed buttons, preserving the corners and bevel at different widths. Reuse the existing
   image widgets and input bounds; labels become ordinary text data instead of baked word textures.
2. Add a shared button appearance/state description to the existing gameplay layout/rendering owners, alongside
   `UiLayoutManager::LayoutElement` text fields. Resolve enabled, hovered, held, selected and keyboard-focused state
   once; feed that into both surface and label drawing. Do not duplicate this per inventory/shop/rest screen.
3. Reuse the font atlas/FreeType rendering path. There is a real integration detail: today's
   [FontAsset](../../../engine/FontAsset.cpp) TTF replacements obtain their metrics from an existing FNT and check
   descriptor height/baseline/Windows-1252 coverage. A new Fondamento face cannot simply replace Create under its
   descriptor without reconciling metrics. Add an explicit standalone font-metrics source to the shared loader,
   or author a dedicated button metrics asset; keep the established legacy metrics path intact. ENDGAME can reuse
   its current descriptor/atlas if chosen. Do not rescale every glyph into unrelated legacy character widths.
4. Draw the label's dark depth, thin light edge and foreground from the same cached glyph coverage. Warm tint plus
   a subtle cached halo can supply the hover response. A sophisticated bevel/SDF shader is optional; a small fixed
   set of layers is sufficient for this proposal. Cache masks/colours and avoid rasterising strings every frame.
   The current renderer caches complete tinted font atlases per colour, so evaluate atlas cost and avoid generating
   a new colour texture for every animation step. The browser's CSS glow is a visual target, not measured bgfx output.
5. Migrate one group first: the five character tabs plus contextual Close. Check hit areas, held/released input,
   selected-page state and scaling. Then reuse the same style for other text actions and optional icon button frames.
   Keep the fixed 4:3/video geometry and approved party placement.

Scope for a later runtime change: bounds at actual supported scales, mouse release/cancellation semantics,
keyboard/controller focus, short/long labels and required character coverage. Existing rendering is CP1252-based;
this browser's Unicode text support does not establish engine localisation support. No game build or runtime
integration was performed for this design comparison.

## Fonts and review artifacts

- [Fondamento from Google Fonts](https://github.com/google/fonts/tree/main/ofl/fondamento), by Brian J. Bonislawsky /
  Astigmatic. [Bundled SIL OFL 1.1](assets/fonts/fondamento-OFL.txt).
- [Almendra from Google Fonts](https://github.com/google/fonts/tree/main/ofl/almendra), by Ana Sanfelippo.
  [Bundled SIL OFL 1.1](assets/fonts/almendra-OFL.txt). Regular is used; the downloaded Bold is retained as a surveyed
  reference and is not used by the proposal.
- [Downloaded file hashes and source URLs](assets/fonts/sources.json); fonts are hosted locally by this viewer.
- [Existing ENDGAME provenance](../../../tools/font_upscale/endgame_faithful/README.md); its copied TTF hash is in
  [button_sources.json](button_sources.json).
- [Comparison board](previews/buttons-r01-board.png), [inventory](previews/buttons-r01-inventory.png),
  [shop](previews/buttons-r01-shop.png).

The accepted frame and gameplay references remain separately recorded in [README.md](README.md).

[Browser review](button_browser_review.json): 30 checks passed for local assets/fonts, all three typefaces across
inventory/house/shop, label fit, Close placement, mouse hover/hold/release, independent selection, Enter activation,
long-label wrapping and switching back to current lettering. No browser runtime exceptions. Source inventory,
paperdoll and shop-video pixels match the proposal captures; the default inventory capture is pixel-identical to
the recorded revision 06 reference. These are browser checks, not runtime engine validation.

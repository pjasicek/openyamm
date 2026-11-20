# Obsidian and legacy full-screen views — 27 September 2026

**Integration handoff and 2116 follow-up:** [consolidated package](../obsidian_engine_handoff_20260928/README.md).
The current browser includes a requested clear status/input rail, sampled from the new status-v3 master; the original
r06 approval captures below remain unchanged. The rail grows from 28 to 42 review pixels, removes its central ornament,
and supports `?status=short|long|bank|withdraw|password`. Party slots move down with the rail while keeping their prior
local +3/+5 adjustment. The original v2 body/right panel and top-bar art remain in use.

**Selected full-screen direction: Carved Obsidian (2026-09-27). Current reference: revision 06.**
The user chose this route and requested refinements in [2065.png](../../../test_img/2065.png),
[2066.png](../../../test_img/2066.png) and [2067.png](../../../test_img/2067.png).
The user accepted revision 05 ("lgthm") with one requested alignment adjustment, applied in revision 06 below.
The earlier flat `frames` treatment was **not accepted**: the user found it too plain, with insufficient basebar
ornament and surface roughness. Retain that feedback when revisiting this study; do not treat revision 01 as approved.
The approved gameplay design remains
[Obsidian refinement 04](../hud_concepts_20260927/README.md#latest-approved-design).
This study does not supersede that approval or change any runtime code or mounted UI assets.

Open [the browser comparison](index.html) to switch between all three screenshots and four treatments. It runs directly
from a local file or the existing repository server. Party size, optional short/long dialogue text and outlines of
preserved content are available in the review toolbar.

## Revision 06 — requested portrait alignment

**Button font accepted, 2026-09-28: Fondamento.** Use it for the shared button treatment in subsequent designs.
The [extended overlay study](../obsidian_overlays_20260928/index.html) applies this selection to all new screens.
The original revision 06 frame captures remain preserved below.

[Button lettering and state comparison](buttons.html), with
[findings and a shared implementation approach](BUTTON_TYPOGRAPHY.md). It compares actual U/H/D button art with
the current type and three live-font candidates. The main viewer's **Button lettering** selector previews the
selected treatment on inventory, Close and shop topics; its historical default retains revision 06 lettering.

Move each occupied party portrait and its HP/mana bars 3 review units right and 5 review units down. The selection
diamond, danger indicator and personal-buff medallion move with the portrait. The offset applies to occupied slots;
empty-slot crests and the frame remain in their established positions. Units are CSS pixels in the 1600×900 study.

Current previews: [inventory](previews/r06-2060-carved.png), [house occupants](previews/r06-2061-carved.png),
[shop dialogue](previews/r06-2062-carved.png), [five-member party and long response](previews/r06-five-party-dialogue.png).
The offset was visually checked with one and five occupied slots. The revision 05 preserved-content report below
remains the most recent frame/content comparison; revision 06 only adjusts occupied portrait groups.

## Revision 05 — previous refinements from 2067

- Give the left video edge a softer, warmer patina. Its narrow inner edge now uses the same brass colour as the
  top bar's lower edge; the rail's texture is toned separately so bright highlights do not dominate.
- Use the basebar's stone texture behind the top resources, cropped from the unadorned interior. This replaces
  the magnified sidebar stone and brings the top and bottom materials closer together.
- Make the basebar's braided upper band about 25% shallower: roughly 38 to 28 review pixels. Its width is retained.
  The browser renders the existing PNG in three slices: the left upper band, the left body and the right Close panel.
  The body fills the freed space; the Close panel retains its original proportions. Portraits, crests, HP/mana bars
  and selection controls retain their positions and sizes.

This revision uses native browser layout and colour treatment of existing art; no new raster artwork was generated.
The source PNGs remain unchanged. Revision 05 previews: [inventory](previews/r05-2060-carved.png),
[house occupants](previews/r05-2061-carved.png), [shop dialogue](previews/r05-2062-carved.png),
[five-member party and long response](previews/r05-five-party-dialogue.png).

## Revision 04 — previous refinements from 2066

- Remove the flourish directly above Close. Keep the button's single centred label.
- Reduce the four small hanging riveted shields to about two-thirds of their previous dimensions, with their
  attachment positions retained. These are part of the basebar artwork, separate from the empty-party crests.
- Enlarge empty-party crests from 84×116 to 98×136 review pixels (about 17%). Restyle all four individually with
  weathered metal, aged brass and dark enamel while retaining their castle, lion, paired-creature and vine identities.
- Make the top bar quieter: keep subdued stone grain, replace its ornate rim with a thin brass edge.

The basebar size correction and four crest restyles use built-in imagegen. The PNG returns are saved unchanged;
all four crests retain generated transparency. [Revision 04 artwork and exact prompts](generated_refinements_r04.json)
record their references, paths, hashes, dimensions and alpha information.

Revision 04 previews: [inventory](previews/r04-2060-carved.png), [house occupants](previews/r04-2061-carved.png),
[shop dialogue](previews/r04-2062-carved.png), [five-member party and long response](previews/r04-five-party-dialogue.png).
The viewer opens the house-occupants screen to match the latest feedback screenshot.

## Revision 03 — previous refinements

- Finish the top resource bar with the same rough slate, worn brass rim and corner details as the chosen sidebar.
- Finish the narrow left video border with the sidebar's metal edge and end details, within its existing 14px bounds.
- Remove displayed party names. Move both health and mana bars up by 21 review pixels, directly beneath the portraits.
  Names remain available in accessible control labels; merchant names are still shown.
- Centre the Close button's single label and remove its displayed `ESC` hint.

The new edges reuse the chosen artwork through CSS background placement and border slicing. No new image generation
was needed. The five-member layout, existing 4:3 content bounds and other chosen frame details are retained.

Revision 03 previews: [inventory](previews/r03-2060-carved.png), [house occupants](previews/r03-2061-carved.png),
[shop dialogue](previews/r03-2062-carved.png), [five-member party and long response](previews/r03-five-party-dialogue.png).

## Revision 02 — earlier comparison

The revised frames restore visible material, sculpted edges and ornament around the approved portrait treatment:

- **Carved Obsidian** (default): rough dark slate, aged brass, raised corner mounts, curling end ornaments and a
  relief braid across the basebar. The new basebar and sidebar are imagegen edits of the existing frame artwork.
  [Shop preview](previews/r02-2062-carved.png).
- **Weathered Stone**: the existing green stone and scrollwork, with deeper patina, stronger empty-slot heraldry,
  warm type and bevelled controls. Uses existing frame textures without generated replacements.
  [Shop preview](previews/r02-2062-stone.png).
- **Legacy reference**: the source screenshot for comparison.
- **Previous flat**: the rejected revision, retained only to compare the change in texture and ornament.

Both material treatments reuse the same inventory, video and portrait content. Raised button rims, small rivets,
engraved separators and restrained flourishes connect the remaining controls to the frame materials. The five-member
preview checks that decoration stays between or outside the portraits and their health/mana bars.

The user selected Carved Obsidian from this comparison. Runtime integration remains separate work; this frame
pass does not require a new inventory layout or changes to fixed footage.

Retain the centred 4:3 workspace and current video window. Fixed footage constrains its own viewport; it does not
require retaining green stone around it. Keeping the complete 640×480 composition also preserves the relationships
between the inventory grid, equipment art, dialogue panel, party selector and contextual controls.

The older **Shared bars only** treatment remains accessible through `treatment=bars` for historical comparison,
but is no longer one of the review tabs. The previous recommendation of the flat `frames` treatment is superseded
by the user's feedback above.

## Per-screen scope

| Source | Preserve | Proposed frame pass |
| --- | --- | --- |
| [2060: inventory](assets/2060.png) | Grid dimensions and item placement; paperdoll, equipment art and equipment placement; character pages | Rough stone surround, inset grid border, bevelled tabs, ornamental basebar and shared resources |
| [2061: house occupants](assets/2061.png) | House-video window and scene, the four real NPC portraits, portrait selection | Carved or original stone panel, stronger house title, same two-column portrait grouping, framed Close control |
| [2062: shop dialogue](assets/2062.png) | House-video window, merchant portrait, topics and existing service destinations | Matching material and border ornament, clear name/profession hierarchy, readable topic rows and hover state |

The proposal reuses the approved portrait rim, selection diamond, shaded HP/SP bars, bright unmarked alert jewels
and personal-buff medallion. It keeps five fixed party positions in the left portion of the bottom bar. Empty slots
retain their heraldic identities, restyled and enlarged in revision 04. Their subdued finish distinguishes them from
the selected portrait. The right portion remains available for screen-specific controls. Gameplay-only minimap and command
strips do not need to appear inside these full-screen views.

The optional response text overlays the lower part of the existing video window without changing the footage's
scale. It previews type size and wrapping, not a new event/dialogue flow. An actual implementation must retain the
existing long-text sizing, scrolling and input behaviour.

## What the current code establishes

- [Character layout](../../../assets_dev/engine/ui/gameplay/character.yml): `CharacterRoot` is centred, 640×480;
  its top bar and character-page controls belong to that screen.
- [Dialogue layout](../../../assets_dev/engine/ui/gameplay/dialogue.yml): `DialogueRoot` is centred, 640×480;
  `DialogueVideoArea` is declared at offset (8, 28), 460×344, with its bottom attached to `OutdoorBasebar`.
  `DialogueEventDialog` is a 172-wide right panel. The authored video rectangle is therefore separate from the
  aspect ratio of the entire screen; the bottom constraint also participates in its resolved size.
- [Overlay party layout](../../../assets_dev/engine/ui/gameplay/gameplay.yml): `OutdoorBasebar` is the legacy
  overlay bar, 640×114. `OutdoorPartyStrip` is 483×114. `CharShield_1` through `CharShield_5` explicitly represent
  empty overlay slots.
- [HUD renderer](../../../game/ui/GameplayHudRenderer.cpp): `isOverlayHudState` and `isLimitedOverlayHud` already
  select an overlay HUD independently of the Standard/Widescreen gameplay layouts.
- [Video submission](../../../game/ui/GameplayUiRuntime.cpp): `renderHouseVideoFrame` submits the current movie
  texture into the supplied rectangle. Stretching that rectangle would stretch the footage; this study keeps it.
- [Screen and dialogue policies](../../../game/ui/GameplayOverlayTypes.h): house-dialogue world occlusion,
  live-gameplay scenes and MM9 RUDE presentation have separate rules. Those other dialogue forms are not represented
  by these three screenshots and should not automatically inherit this house-screen treatment.

Any later implementation should reuse the shared gameplay UI/layout/input owners. Visual bounds, selection,
inspection, drag/drop, held-item presentation and contextual controls must remain aligned. A browser mockup does
not validate those runtime interactions or video playback.

## Art and evidence

- Sources are exactly `test_img/2060.png`, `2061.png` and `2062.png`, copied unchanged.
- The matching first PC is the existing `pc03-01.png`. Existing `ibshield01–04.png` are the references for the four
  restyled empty-slot crests; historical treatments still use the source versions.
- Other party portraits, gold/food art and the personal-buff medallion come from the approved gameplay study.
- The browser clips original screenshot regions with CSS and covers only proposed frame regions. No inventory item,
  paperdoll, NPC portrait or movie content was generated, stretched, repainted or retouched. All proposed rectangles
  are positioned within a 1200×900 review workspace, equivalent to the 640×480 composition at 1.875× display scale.
- Existing `basebar`, `ib-mb-a`, `evt`, `topbar`, `ib-8pxbar` and `endcap` art is copied from
  `assets_dev/engine/icons_x2/`. Browser colour filters affect frame textures only.
- The initial built-in imagegen pass produced two reference-image edits, saved unchanged as
  [original Carved Obsidian basebar](assets/generated/carved-obsidian-basebar-v1.png) and
  [Carved Obsidian sidebar](assets/generated/carved-obsidian-sidebar-v1.png).
  [Generated-frame provenance](generated_materials.json) records exact prompts, references, returned image paths,
  dimensions and hashes. The basebar return has black padding above and below the artwork; CSS clips that padding
  when displaying it. Revision 03 used the sidebar's interior and border slices for the top bar and its left edge
  for the narrow video frame. Revision 04 replaced the top bar's ornate border with a thin edge; revision 05 uses
  the basebar's stone behind the resources and softens the left rail's finish.
- Revision 04 uses [basebar v2](assets/generated/carved-obsidian-basebar-v2.png) and
  `assets/generated/carved-obsidian-empty-slot-01-v1.png` through `-04-v1.png`.
  [Their provenance and prompts](generated_refinements_r04.json) are separate from the initial frame generation.
  All returned PNGs and original source files are preserved unchanged.
- Names, HP/SP values, personal Bless, five-member parties and optional response paragraphs are sample data.
  The captured grid and paperdoll remain the same when selecting another preview portrait.
- [Asset provenance](asset_sources.json) records copied source hashes.
  [Revision 05 content preservation](content_preservation_r05.json) verifies identical source and browser-capture
  pixels inside the grid, paperdoll and two house-video windows. Frame boundaries are excluded.
  Reports for [revision 04](content_preservation_r04.json), [revision 03](content_preservation_r03.json),
  [revision 02](content_preservation_r02.json) and
  [revision 01](content_preservation.json) are retained.
- [Previews](previews/) named `r06-*` show the current reference. Earlier files record the preceding revisions
  and the initial proposals.
- Validation: JavaScript syntax check, browser captures, visual review of party capacity and text, and the pixel
  comparisons above. No runtime code changed and no game build was run.

Review URLs:

```text
index.html?screen=2060&treatment=carved
index.html?screen=2061&treatment=legacy
index.html?screen=2062&treatment=stone
index.html?screen=2062&treatment=carved&party=5&speech=long
index.html?screen=2060&treatment=carved&preserved=1
index.html?screen=2062&treatment=frames
```

Add `export=1` to capture only the 1600×900 scene. The generated preview files are browser screenshots, not game captures.

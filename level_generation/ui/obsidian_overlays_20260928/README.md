# Carved Obsidian — extended overlay collection

**Current integration preparation:** [consolidated HUD handoff](../obsidian_engine_handoff_20260928/README.md), including
the subsequent 2116 clear status/input rail. Earlier approval captures remain preserved here.

**28 September 2026 · revision 03 · USER APPROVED.** [Open the browser collection](http://127.0.0.1:8899/level_generation/ui/obsidian_overlays_20260928/index.html).

The user approved the complete revision 03 and requested staging for future use. The
[staged integration package](staging/README.md) contains exported graphics, eleven layout drafts, fonts,
palette/geometry contracts, source receipts and validation. It is unmounted; see its [runtime requirements](staging/INTEGRATION.md).

The user selected **dark obsidian reading surfaces, soft ivory text and the recreated MM reading fonts**.
**Fondamento remains the selected button typeface.** This revision follows the user's feedback and
`test_img/2078.png`–`2088.png`. Its revised screen treatments and exact semantic colour shades are now approved.

The accepted bases remain [Carved Obsidian revision 06](../hud_overlay_study_20260927/README.md) and
[gameplay Obsidian refinement 04](../hud_concepts_20260927/README.md#latest-approved-design).
Their preserved screenshots and default mockups are unchanged. This collection is **browser design work only**:
no engine integration, mounted UI changes or save changes.

The [proposal 01 notes](PROPOSAL_01.md), [revision 02 notes](REVISION_02.md) and their captures are historical comparisons.
Current images are under [previews/r03/](previews/r03/); unchanged inspector/dialogue examples retain their r02 links.
Earlier Source-font and vellum options remain available
in the review toolbar; they are no longer the default or recommendation. The page also works from local files with
its sibling study folders present. Fonts and art are bundled locally.

## Revision 03

The latest refinements are a bottom-anchored item-value footer, pale blue upgradeable skill rows, the three rest blocks
marked in [2087](../../../test_img/2087.png), removal of the rest screen's standalone `Food: 7`, clearer stat section
edges following [2088](../../../test_img/2088.png), tighter native skill spacing, and a wider quick-reference label
column with stronger vertical dividers. These are the latest approved overlay baseline.

| Screen | What changed | Preview |
| --- | --- | --- |
| Inventory | Exact 32 × 32 logical cells. No hover overlay, native tooltip or label above Stats. Hold RMB to inspect; release closes it, including release outside the item. LMB does not inspect. | [Inventory](previews/r03/inventory.png) |
| Stats | Six groups with clearer brass and inset stone edges. Their geometry, current/base formatting and original font roles remain. | [Stats](previews/r03/stats.png) |
| Skills | Whole-row upgrade clicks. Pale blue eligible rows, ordinary unavailable rows; no `+` control. Lucida at native size with tighter row spacing, plus a slightly smaller comparison. | [Some available](previews/r03/skills-some-available.png), [smaller type](previews/r03/skills-smaller.png) |
| Awards | Arrus and the runtime's priority colours. Plain scrolling list directly on the surface; no nested border, bullets or rules. | [Awards](previews/r03/awards.png) |
| Rest | Framed actions block, nested wait block and hourglass/date block. Existing action positions retained. No standalone food count; the food icon and cost remain on Rest & Heal. | [Rest](previews/r03/rest.png) |
| Quick reference | Label column widened from 146 to 184 review pixels; clearer column dividers. All fourteen rows, five character columns, numeric HP/SP, Reputation and Fame remain. | [Five members](previews/r03/quickref.png), [one member](previews/r03/quickref-one.png) |
| Dialogue | Body only: no extra speaker/topic heading or Continue button. Dynamic height, bounded Arrus adjustment, then Create fallback. | [Dialogue](previews/r03/dialogue.png), [fallback](previews/r02/dialogue-fallback.png) |
| Item inspect | Original font roles. `Value: N` and its divider are a separate bottom footer, aligned with the text column. Long descriptions scroll independently. | [Potion](previews/r03/inspect-potion.png), [helm](previews/r03/inspect-helm.png), [tall sword](previews/r03/inspect-sword.png), [long text](previews/r03/inspect-long.png) |
| Stat / skill inspect | Original Create title and Smallnum body. No invented Current/Base/Bonus table. Skill mastery descriptions and the original `Skill bonus: +N` line remain. | [Endurance](previews/r02/inspect-stat.png), [Sword](previews/r02/inspect-skill.png) |
| Monster inspect | Centred title, HP bar, square image left, Effects beneath, main values right and all ten resistances in one vertical column. | [Monster](previews/r02/inspect-monster.png) |
| Buffs | Previous uniform glyph-free illustrations retained. Twenty-two party effects, four plus overflow or two rows. | [Catalogue](previews/r03/buffs.png) |

The **Inspect tab shows stationary specimens for visual review**. Inventory, stats, skills and the buff catalogue
use held RMB. Release, lost pointer capture or window focus loss closes that inspection. Preview actions spend sample
skill points or advance a sample clock; they do not change game data. The review toolbar remains outside the game image.

## Font roles

Preserve the original roles, rather than applying one reading font everywhere. All five faithful TTFs come from
`assets_dev/engine/fonts/truetype/`. There is no synthetic italic or bold applied to these native faces.

| Content | Face | Typical logical size / 1.875× review size |
| --- | --- | --- |
| Buttons and tabs | Fondamento | Accepted button study recipe |
| Character name, class, skill-point header; rest time/date | Create | 18–19 / 33.75–35.625 px |
| Stats labels and values | Lucida | 18 / 33.75 px |
| Skill names and ranks | Lucida | Native 17 / 31.875 px; optional 16 / 30 px comparison |
| Skill group headings; awards; quick reference | Arrus | 19 / 35.625 px |
| Item title | Arrus | 19 / 35.625 px |
| Item Type, details and Value | Comic | 19 / 35.625 px |
| Item/stat/skill/spell/buff descriptions; monster fields | Smallnum | 14 / 26.25 px |
| Stat/skill/spell/buff/monster titles and monster subheadings | Create | 18 / 33.75 px |
| Dialogue | Arrus, then Create | See bounded fitting below |

Skill type was checked against `renderSkillGroup` in
[GameplayPartyOverlayRenderer.cpp](../../../game/ui/GameplayPartyOverlayRenderer.cpp),
[character.yml](../../../assets_dev/engine/ui/gameplay/character.yml) and the
[Lucida descriptor](../../../assets_dev/engine/fonts/truetype/lucida.yml). The game assigns **Lucida** to names and
ranks, with a **17px logical cell height**; row pitch is `fontHeight - 3`, or **14 logical pixels**. The browser was
already using the same recreated font and nominal size, but its rows were 35 review pixels apart. Revision 03 uses
the native **26.25 review-pixel pitch** and offers a **16px** comparison in the Skills toolbar. Native size remains
the default. Weapons/Magic occupy the left column and Armor/Miscellaneous the right, matching the runtime layout.
The engine's current upgradeable-row colour is already blue (`#4a78ff`); this study proposes a softer, brighter blue.

The quick-reference table uses the available width and height. Unusually long individual cells, such as
“Lightning Bolt,” can reduce their Arrus size down to 14 logical pixels to avoid running into another column;
ordinary cells stay at 19. No HP/SP meters take space from the numbers.

See [font and colour specimen](previews/r03/type.png). Source Serif / Sans and their bundled OFL licences are retained
only for the earlier comparison. Fondamento and its accepted hover, press, selected and focus treatment are reused from
[the button study](../hud_overlay_study_20260927/BUTTON_TYPOGRAPHY.md).

## Shared text colour rules

| Meaning | Colour | Usage |
| --- | --- | --- |
| Ordinary | Soft ivory `#e5dcc7` | Main text, unchanged values and the base half of current/base pairs |
| Positive / available points | Jade `#85df8b` | Actual above base, positive skill bonus, available skill points |
| Upgradeable skill | Pale blue `#8ebcfa` | Eligible whole skill rows; hover brightens to `#c5e0ff` |
| Negative | Coral `#ee8275` | Actual below base, harmful condition, HP/SP at or below zero |
| Low resource | Amber `#e6c36c` | Positive HP/SP below half maximum; ordinary spent resources above half remain ivory |
| Heading / class | Pale brass `#e4c793` | Inspector title, class beside name and monster field labels |

These semantics follow the existing comparison/resource rules in
[GameplayPartyOverlayRenderer.cpp](../../../game/ui/GameplayPartyOverlayRenderer.cpp).
The exact jade/blue/coral/amber shades are approved for this surface. The Stats and Quickref toolbar presets compare
ordinary values, bonuses, penalties and a mixed example. Green is not used to decorate every normal condition.

Awards retain their separate **existing priority palette**:
`#f86ca0`, `#70dcf8`, `#c0c0f0`, `#40f460`, `#e8f460`, `#f0fcc0`.
The first four entries match the order and category colours in 2082; additional actual award strings exercise scrolling.

## Geometry and source content

The browser stage is 1600 × 900. Its centred 1200 × 900 workspace represents the original 640 × 480 at **1.875×**.
It retains the accepted basebar and final portrait/bars shift of **3 right, 5 down**. The equipment column and house
video remain actual project captures, not regenerated images.

The [character layout](../../../assets_dev/engine/ui/gameplay/character.yml) puts the inventory at `(7,32)`,
size **448 × 288**, with **14 × 9 cells of 32 × 32 logical pixels**. In the review stage this is exactly
**(213.125,60,840,540)**; grid lines repeat every **60 review pixels**. Both engraved and inset treatments use it.
Item arrangement and footprints are visual fixtures, not modifications to item definitions.

Rest and quick reference fill the original upper workspace from `(200,0)` to `(1400,690)`; they cover the underlying
inventory resource strip. The rest panorama is `(180,48.75,832.5,202.5)` relative to that workspace. Rest 8 Hours is
`(114.375,290.625,510,78.75)`. Wait buttons share x187.5 and start at y448.125, with 60-pixel vertical increments.
Exit Rest is `(676.875,560.625,346.875,80.625)`. Revision 03 frames those actions without moving their hit rectangles:
the overall action block is `(88,274,572,382)` and its wait block is `(166,381,397,261)`. The calendar block groups
the hourglass and date, with a vertical separator. The separate food count is removed from this screen, while
the sample rest action still checks and consumes food. The original upright hourglass animation begins at `hglas060`,
not `hglas001`; this revision uses the appropriate frame and the 9 am sky (`terra0091`).

[prepare_assets.py](prepare_assets.py) copies local source art/fonts and exports [content.js](content.js) from
`english/stats.txt`, `english/skill_des.txt`, `items.txt` and `english/awards.txt`. The item's description, name,
unidentified type and value come from these tables; sample equipment modifiers and character/monster values are
fixtures. The spell and NPC prose are also illustrative. The monster is an existing restored MM6 goblin; it shows the
layout without changing or claiming the identification state of a saved party.

Reference screenshots: [2078 item](../../../test_img/2078.png), [2079 stat](../../../test_img/2079.png),
[2080 stats](../../../test_img/2080.png), [2081 stat colours](../../../test_img/2081.png),
[2082 awards](../../../test_img/2082.png), [2083 rest](../../../test_img/2083.png),
[2084 quickref](../../../test_img/2084.png), [2085 helm](../../../test_img/2085.png),
[2086 monster](../../../test_img/2086.png), [2087 rest blocks](../../../test_img/2087.png),
[2088 section edges](../../../test_img/2088.png).

Authoritative layout references:
[rest](../../../assets_dev/engine/ui/gameplay/rest.yml),
[quick reference](../../../assets_dev/engine/ui/gameplay/quick_reference.yml),
[dialogue](../../../assets_dev/engine/ui/gameplay/dialogue.yml),
[item](../../../assets_dev/engine/ui/gameplay/item_inspect.yml),
[actor](../../../assets_dev/engine/ui/gameplay/actor_inspect.yml),
[character inspector](../../../assets_dev/engine/ui/gameplay/character_inspect.yml),
[character detail](../../../assets_dev/engine/ui/gameplay/character_detail.yml),
[spell](../../../assets_dev/engine/ui/gameplay/spell_inspect.yml) and
[buff](../../../assets_dev/engine/ui/gameplay/buff_inspect.yml).

## Dialogue fitting

The sheet contains only wrapped body text and the shared upper/side edge. It grows upward from the basebar.
The font sequence in this browser prototype is:

1. Arrus at **19 logical px**, with original-style 16px line advance.
2. Arrus at **18 logical px** if needed — a bounded reduction of about 5%.
3. Create at **18 logical px**, then **17 logical px** if needed.
4. Only text that still exceeds the available area scrolls at that minimum size; it never shrinks indefinitely.

The prototype measures the actual loaded fonts. The toolbar reports the selected face and size. “Longer · font
fallback” demonstrates the font change without scrolling; “Extreme overflow” exercises the final bounded case.
The inspector stress setting separately exercises bounded scrolling. Runtime integration should use its text-measurement
code and preserve existing input/placement. The existing
[dialogue renderer](../../../game/ui/GameplayDialogueRenderer.cpp) already has an Arrus-to-Create fallback beyond
`DialogueTextPrimaryFontMaxHeight` (344 logical pixels); this browser's viewport fitting is a design demonstration,
not an engine change or a pixel-exact port of that algorithm.

## Shared border and surfaces

Existing inspector construction already separates background, four corners and four edges. The current mounted
asset called `parchment` is a dark stone texture. The selected obsidian treatment follows that separation.

The generated artwork from proposal 01 is reused unchanged:

- [Whole frame](assets/generated/frame-v1.png): **1536 × 1024 RGBA**, true alpha, no paper in the opening.
- [Cropped master](assets/generated/frame-cropped.png): `(48,72,1488,952)`, **1440 × 880**.
- [Eight slice coordinates](frame_slices.json): four 164px source corners and four 256px-long edge tiles.
- [Alpha report](alpha_verification.json): 82.55% exactly transparent; centre sample alpha 0–1.
- [Earlier comparison vellum](assets/generated/vellum-v1.png): **1254 × 1254**, separate from the frame.
- [Original prompts](generated_prompts.json) and [source receipts](asset_sources.json).

Corners draw at **58 × 58 review pixels**. Edges repeat at the same scale. Background texture also uses a fixed
scale: increasing window size reveals more texture, rather than stretching the grain. No centre image is baked into
the border. The dialogue uses the top and side pieces, meeting the party bar at its open bottom. A later engine export
still needs alpha/seam checks at its actual drawing scale.

## Buff art retained

All **22 party-effect slots** retain their glyph-free illustrations from proposal 01. Installed coloured A-family
spell PNGs remain unchanged. Per-illustration SVG clip polygons exclude both the large letter and smaller rune rows;
the remaining artwork fits, with aspect preserved, into uniform **36 × 36 HUD boxes** and **44 × 44 catalogue boxes**.
The catalogue's ordinary spell names are review labels, not baked glyphs. Timers remain separate text.

[Clipping data](buff_art.json), [browser helper](buff-art.js) and source hashes preserve that provenance. The older
HUD viewer uses these thumbnails only with `buffArt=clean`; its default approved presentation is unchanged.

## Verification

[Revision 03 browser report](browser_review_r03.json) records **22 passing checks**, including footer placement for
short and tall items, a stationary footer while long descriptions scroll, held-RMB release outside the inventory,
blue skill-row interaction and native spacing, the three rest blocks and unchanged button positions, clock/food
behaviour without the food label, and five-column quick-reference fit. No browser exceptions or failed assets.
Captures under `previews/r03/` show all tabs and the affected cases. The
[revision 02 report](browser_review_r02.json) preserves the earlier broader interaction/font/grid verification.

No C++ build or game runtime test is needed for this browser-only revision.

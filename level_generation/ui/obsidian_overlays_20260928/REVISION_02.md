# Carved Obsidian — extended overlay collection

Historical revision 02 notes. See [the current review](README.md) for the latest refinements.

**28 September 2026 · revision 02.** [Open the browser collection](http://127.0.0.1:8899/level_generation/ui/obsidian_overlays_20260928/index.html).

The user selected **dark obsidian reading surfaces, soft ivory text and the recreated MM reading fonts**.
**Fondamento remains the selected button typeface.** This revision follows the user's feedback and
`test_img/2078.png`–`2086.png`. Its revised screen treatments and exact semantic colour shades still await visual review.

The accepted bases remain [Carved Obsidian revision 06](../hud_overlay_study_20260927/README.md) and
[gameplay Obsidian refinement 04](../hud_concepts_20260927/README.md#latest-approved-design).
Their preserved screenshots and default mockups are unchanged. This collection is **browser design work only**:
no engine integration, mounted UI changes or save changes.

The [proposal 01 notes](PROPOSAL_01.md) and its images directly under `previews/` are historical comparisons.
Current images are under [previews/r02/](previews/r02/). Earlier Source-font and vellum options remain available
in the review toolbar; they are no longer the default or recommendation. The page also works from local files with
its sibling study folders present. Fonts and art are bundled locally.

## Revision 02

| Screen | What changed | Preview |
| --- | --- | --- |
| Inventory | Exact 32 × 32 logical cells. No hover overlay, native tooltip or label above Stats. Hold RMB to inspect; release closes it, including release outside the item. LMB does not inspect. | [Inventory](previews/r02/inventory.png) |
| Stats | Name and differently coloured class on one line; `Skill Points: N`. Original six groups and current/base formatting, without added group headings. Original font roles and descriptions. | [Stats](previews/r02/stats.png) |
| Skills | Whole-row upgrade clicks. Green eligible rows, ordinary unavailable rows; no `+` control. RMB inspection works on either. Point presets show all/some/none available. | [Some available](previews/r02/skills-some-available.png) |
| Awards | Arrus and the runtime's priority colours. Plain scrolling list directly on the surface; no nested border, bullets or rules. | [Awards](previews/r02/awards.png) |
| Rest | Original panorama rectangle, large eight-hour action, vertical wait buttons, upright hourglass, compact date and Exit Rest position. Food icon and cost retained. | [Rest](previews/r02/rest.png) |
| Quick reference | Original fourteen rows including Name, five columns, larger Arrus, numeric HP/SP, Reputation and Fame footer. Empty slots are blank. | [Five members](previews/r02/quickref.png), [one member](previews/r02/quickref-one.png) |
| Dialogue | Body only: no extra speaker/topic heading or Continue button. Dynamic height, bounded Arrus adjustment, then Create fallback. | [Dialogue](previews/r02/dialogue.png), [fallback](previews/r02/dialogue-fallback.png) |
| Item inspect | Centred Arrus title; Comic Type/details/Value; Smallnum description. Separator above a left-aligned `Value: N` line. Actual potion and helm text. | [Potion](previews/r02/inspect-item.png), [helm](previews/r02/inspect-helm.png) |
| Stat / skill inspect | Original Create title and Smallnum body. No invented Current/Base/Bonus table. Skill mastery descriptions and the original `Skill bonus: +N` line remain. | [Endurance](previews/r02/inspect-stat.png), [Sword](previews/r02/inspect-skill.png) |
| Monster inspect | Centred title, HP bar, square image left, Effects beneath, main values right and all ten resistances in one vertical column. | [Monster](previews/r02/inspect-monster.png) |
| Buffs | Previous uniform glyph-free illustrations retained. Twenty-two party effects, four plus overflow or two rows. | [Catalogue](previews/r02/buffs.png) |

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
| Stats labels, values and skill rows | Lucida | 17–18 / 31.875–33.75 px |
| Skill group headings; awards; quick reference | Arrus | 19 / 35.625 px |
| Item title | Arrus | 19 / 35.625 px |
| Item Type, details and Value | Comic | 19 / 35.625 px |
| Item/stat/skill/spell/buff descriptions; monster fields | Smallnum | 14 / 26.25 px |
| Stat/skill/spell/buff/monster titles and monster subheadings | Create | 18 / 33.75 px |
| Dialogue | Arrus, then Create | See bounded fitting below |

The quick-reference table uses the available width and height. Unusually long individual cells, such as
“Lightning Bolt,” can reduce their Arrus size down to 14 logical pixels to avoid running into another column;
ordinary cells stay at 19. No HP/SP meters take space from the numbers.

See [font and colour specimen](previews/r02/type.png). Source Serif / Sans and their bundled OFL licences are retained
only for the earlier comparison. Fondamento and its accepted hover, press, selected and focus treatment are reused from
[the button study](../hud_overlay_study_20260927/BUTTON_TYPOGRAPHY.md).

## Shared text colour rules

| Meaning | Colour | Usage |
| --- | --- | --- |
| Ordinary | Soft ivory `#e5dcc7` | Main text, unchanged values and the base half of current/base pairs |
| Positive / available | Jade `#85df8b` | Actual above base, positive skill bonus, available skill points, eligible upgrade rows |
| Negative | Coral `#ee8275` | Actual below base, harmful condition, HP/SP at or below zero |
| Low resource | Amber `#e6c36c` | Positive HP/SP below half maximum; ordinary spent resources above half remain ivory |
| Heading / class | Pale brass `#e4c793` | Inspector title, class beside name and monster field labels |

These semantics follow the existing comparison/resource rules in
[GameplayPartyOverlayRenderer.cpp](../../../game/ui/GameplayPartyOverlayRenderer.cpp).
The exact jade/coral/amber shades are proposals for this surface. The Stats and Quickref toolbar presets compare
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
Exit Rest is `(676.875,560.625,346.875,80.625)`. The original upright hourglass animation begins at `hglas060`,
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
[2086 monster](../../../test_img/2086.png).

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

[Browser review report](browser_review_r02.json) records the revision checks. Captures under `previews/r02/` cover
all tabs, six inspector types, both item reference examples, five-member quick reference, dialogue size/fallback
cases and the actual held-RMB inventory interaction. Checks exercise press/release outside the item, unavailable
skill inspection, spending points, clock/food changes, font roles, content bounds, grid geometry and asset loading.

No C++ build or game runtime test is needed for this browser-only revision.

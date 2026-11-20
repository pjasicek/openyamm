# Remaining gameplay UI — native Obsidian integration

Implemented 2026-09-29, including the vertical bottom-left control column, Attack/Spell beside the party at 2:1,
and the context popup above that right-hand pair.
[Open the review gallery](http://127.0.0.1:8899/level_generation/ui/obsidian_remaining_20260929/index.html)
or [its local HTML](index.html). All screen examples are native game captures. Android examples load its YAML
supplement into the desktop renderer; they are layout previews, not device captures.

## Latest approved Android layout

**User approved 2026-09-29.** Preserve the bottom-left column (Turn Mode, Inventory, Inspect from bottom to top),
the large right-hand Attack/Spell pair with Quick Cast, the context popup above it, and Fly-only flight controls.
The column clears the full party at 4:3; Attack/Spell stay beside the party at 2:1 with the accepted slight reduction.
This supersedes the earlier left-hand button pair and raised 2:1 action group.

Approved reference captures: [4:3](native/images/touch-column-4by3.png),
[2:1](native/images/touch-column-2by1.png), [wide phone](native/images/touch-column-phone.png).
The installed layout is [`touch_controls.yml`](../../../assets_dev/engine/ui/gameplay/touch_controls.yml).

## Installed behavior

- **Lloyd’s Beacon:** shared carved frame and dark reading surface, soft ivory slot text, muted brass slot edges,
  live Fondamento Set/Recall/Close buttons. Original five slot rectangles, screenshots, location/expiry text,
  spell rules and input actions are preserved. Empty slots remain hidden in Recall mode.
- **Town Portal / Dimension Door:** the shared Obsidian Close button and live type. Existing destination art is retained.
- **Inventory jewelry:** shared dark framed panel and recessed equipment cells centered on the original item positions.
  The 2026-09-30 follow-up adds four logical pixels around each cell: rings are 40 × 40, gauntlets/amulets 40 × 72.
  Item size and placement stay unchanged. [Enlarged cells](../../../output/jewelry_cells_20260930/jewelry.png).
  The 2026-09-30 correction restores the previous backdrop alpha of 134/255, showing the paperdoll through the
  surface while keeping the frame, cells and jewelry opaque. [Native capture](../../../output/jewelry_alpha_20260930/jewelry.png).
  The new magnifier has normal, hover, held and selected states. Held-RMB inspection behavior is retained.
- **Context actions:** a compact carved panel, live Fondamento label and new true-alpha illustrations selected by
  semantic IDs in `context_actions.yml`. Related interactions share illustrations. Dropping a held item still shows
  that actual item. The old generic icon fallback chain is removed.
- **Dialogue/shop:** removed the `evt` background definitions and the renderer's fallback to that frame asset.
  Shop profiles own their explicit merchandise backgrounds; house video rendering continues to own its video region.
- **Spellbook:** its intentional artwork and layout are preserved.

## Android correction: preserve the thumb arrangement

`touch_controls.yml` loads after the shared desktop gameplay YAML on Android. The retired `gameplay_mobile.yml`
remains unmounted. The first small, edge-mounted control proposal is superseded by this implementation.

Attack and Spell are side by side at their original **104 × 104** authored size. Quick Cast is the original
**56 × 56** badge over Spell's upper-left edge. The left group is now a single **80 × 256** column: bottom to top
**Turn Mode, Inventory, Inspect**, each **80 × 80**, separated by eight-unit gaps. Its 965-wide reference scaling
and 24-unit left / 16-unit bottom insets are retained. The column fits beside the full party and end ornament
even at 4:3, using less than half the previous group's width without shrinking its touch targets.
The right group uses a **1024-wide reference**, reducing it by about 6% at 2:1 so it fits beside a full five-member
party. At 1800 × 900, Attack/Spell each measure 182.8 pixels instead of 194.0. Wide phones such as 2100 × 900
still reach the original full size. Both main groups retain their 24-unit side inset.

The groups stay at the bottom whenever they clear the live party frame, including its end ornaments. When a group
would overlap that frame, `GameplayHudCommon::touchPanelVerticalOffset` lifts the entire group just above it with
a 12-scaled-unit gap. Children and hit regions receive the same displacement. Party portraits are unchanged.
The Quick Cast overlap is intentional; it retains hit-test priority over Attack/Spell.

The Android context popup is a **220 × 42** child of the right-hand action panel, at `(0, -56)` relative to it.
It sits above Attack/Spell with a four-unit gap above Quick Cast, inherits the group's scale and follows its
party-frame displacement. Its actual hit rectangle follows the same layout. Desktop popup placement is unchanged.

Flight controls are paired below the minimap. Expanded followers sit to its left, clear of flight, actions and the
context popup. Their Android offsets also clear the popup when the main group is raised at intermediate widths.
Both flight rendering and touch hit regions require the **Fly party buff to be active outdoors**. Levitate or
Water Walk alone does not expose them. The earlier review save intentionally had Fly active; the new gallery
also includes a no-Fly capture. This existing runtime condition required no engine change.
The overlay inspection control fits within the existing top strip. Turn mode uses its active plate
and Resume symbol; inspection uses a held/active state. The floating joystick retains its existing behavior with
new restrained translucent artwork.

Touch classification now receives actual resolved HUD rectangles, including the dynamic party width and open
followers. Stale hardcoded legacy touch zones have been removed. Utility spell screens accept ordinary UI taps;
an open personal-buff popup consumes dismissal taps instead of starting movement.

## Graphics and source

The **built-in imagegen tool** generated fourteen independent true-alpha illustrations: magnifier, attack, cast,
talk, door, chest, pouch, hand, lever, fountain, shrine, obelisk, read and portal. No background extraction was used.
Original outputs are retained under [art/raw](art/raw); [art/generated_sources.json](art/generated_sources.json)
records their generated-image provenance. The complete final prompt set is [art/prompt_set.json](art/prompt_set.json).

Basic pause/resume/arrow/quick-cast symbols, four state plates and two joystick elements are code-authored MVG
geometry under `art/`. [export_art.py](export_art.py) exports those and uniformly fits the generated illustrations,
preserving alpha. All **25 runtime PNGs** are 256 × 256, lowercase and mode 0644 in
[`assets_dev/engine/icons_x2`](../../../assets_dev/engine/icons_x2).
[export.json](export.json) lists exact filenames, dimensions, source paths and SHA-256 checksums.

Runtime layout ownership:

- [`lloyds_beacon.yml`](../../../assets_dev/engine/ui/gameplay/lloyds_beacon.yml)
- [`town_portal.yml`](../../../assets_dev/engine/ui/gameplay/town_portal.yml)
- [`character.yml`](../../../assets_dev/engine/ui/gameplay/character.yml)
- [`dialogue.yml`](../../../assets_dev/engine/ui/gameplay/dialogue.yml)
- [`context_actions.yml`](../../../assets_dev/engine/ui/gameplay/context_actions.yml)
- [`touch_controls.yml`](../../../assets_dev/engine/ui/gameplay/touch_controls.yml)

The shared button skin owns state rendering; labels remain live text. Assets are installed in development mounts.
No release ZIP/APK was repacked.

## Checks

- Normal `openyamm` and unit-test targets built. **42 focused test cases / 2,887 assertions passed**, including
  thumb-group clearance, Obsidian geometry, Lloyd's Beacon, Town Portal, context actions, shops and input.
- The native layout resolver passed **492 containment/overlap/placement checks** at 640 × 480, 1200 × 900, 1600 × 900,
  1800 × 900 and 2100 × 900 with a full five-member frame and expanded followers. This includes the context popup;
  the original Quick Cast badge overlap is exempt.
- Compiling the real Android input branch against host SDL passed **375 simulated-touch checks** at those sizes:
  HUD taps, held flight, two-finger inspection, release, movement outside controls and overlay input.
  The full column's HUD hit region is included, verifying that its Inspect button still takes modifier priority.
  Other Android-conditional changed source also passed host syntax checks.
- Seven successful isolated native runs used **OpenGL 3.3 / NVIDIA / SDL Wayland**. Reviewed Beacon empty/saved
  states, jewelry and magnifier states, Town Portal Close, house context activation, and Android arrangements at
  three aspect ratios including expanded followers and turn mode. Normal saves/settings were untouched.
- The previous context-placement pass captured 2100 × 900, 1800 × 900 and 1200 × 900, including expanded followers.
  Its raised 2:1 group is superseded by the fitted version described above; its wider-phone placement is retained.
- The fitted 2:1 native capture confirms bottom placement beside all five portraits, with the popup above and
  expanded followers clear. Its held state and activation successfully open the house. A second capture with
  only Fly removed confirms the flight arrows disappear; the narrower 4:3 preview is refreshed as well.
- The latest bottom-left column captures cover 1200 × 900, 1800 × 900 and 2100 × 900. At 4:3 the unchanged-size
  buttons fit beside all five portraits; native clicks toggle turn mode and open Inventory from their new positions.
  Held Inspect is shown, and the host Android input check verifies its two-finger modifier inside the column.
- All runtime export hashes and file modes match their manifest. Browser checks cover the gallery's native views,
  nineteen displayed symbols and four plate states; see [browser-check.json](browser-check.json).

[native/validation.json](native/validation.json), [native/tests.log](native/tests.log),
[native/geometry-input.log](native/geometry-input.log), `native/runs/`, `native/tours/` and `native/images/` retain evidence.
`python3 native/prepare.py` regenerates the private fixtures and runs geometry and host Android-input checks after
the normal development build.

The Android release build was attempted but blocked by this host: Gradle 8.12 rejects Java 25 (`class file major
version 69`), and `android/local.properties` points to the missing `/home/pjasicek/android-sdk`. No APK/device pass
is claimed. This does not affect the completed native desktop build or layout/input checks.

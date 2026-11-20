# In-game HUD studies — 27 September 2026

**Current integration preparation:** [consolidated HUD handoff](../obsidian_engine_handoff_20260928/README.md), with
content-free component exports, the complete gameplay layout draft, font choices and renderer/input contracts.

## Latest approved design

**Obsidian refinement 04 is the latest best in-game HUD design, approved by the user on 2026-09-27.**
Start from this revision when revisiting the HUD. Verdigris, Field journal and earlier Obsidian revisions are
historical alternatives.

- [Approved reference screenshot](approved/obsidian-r04.png) — preserved separately from regenerated previews.
- [Interactive design](index.html?concept=obsidian&state=explore&party=5&buffLayout=compact&buffs=12&bars=shaded&status=off&turn=0).
- [Generated icon files and prompts](generated_icons.json); Books uses `assets/generated/obsidian-books-v2.png`.

The accepted version has the journal/quill/inkwell Books icon, no old skull/doll controls, bright unmarked
green/yellow/red alert diamonds, stronger portrait rim and selection diamond, no horizontal portrait underlines,
bold location text, bounded timed party buffs and a clickable personal-buff medallion. Preserve this screenshot
when exploring later revisions.

This approval records the browser design reference. Runtime integration remains future work; the scope is the
in-game HUD, with existing portraits and other full-screen UI retained.

## Prototype

The [2026-09-28 overlay collection](../obsidian_overlays_20260928/README.md) includes the requested uniform,
glyph-free buff treatment. `buffArt=clean` opts this HUD viewer into the sibling collection's display clips;
the default appearance and frozen approved screenshot retain refinement 04. The optional helper lives in that
sibling folder; the PNG spell sources remain unchanged.

Related proposal: [legacy inventory and house-dialogue frame study](../hud_overlay_study_20260927/README.md), using
`test_img/2060.png`–`2062.png`. This is a separate review and does not replace the approved gameplay design above.

Open `index.html` directly in a browser. Obsidian refinement 04 is now the default. It is a self-contained static
prototype with no dependencies or network requests.
The original assets in `assets/` are byte-for-byte copies of existing game assets; `asset_sources.json` records their
origins and hashes. The six active Obsidian icons and the earlier Books variant live in `assets/generated/`;
`generated_icons.json` records their prompts
and generation provenance. This directory changes no runtime code, mounted content, settings or other screen designs.

## The three proposals

1. **Verdigris — evolution.** Dark green patina, aged brass, ivory type and restrained geometric engraving.
   A single shallow lower plinth visually connects the interface. Original oval portraits remain large and central;
   health and spell points retain the existing vertical pairing. Gold and food share a tray. The original body/skull
   tableaux sit beside individually inspectable timed effects. The square map stays at lower right.
   This is the smallest visual departure; its continuous bottom edge uses more scenery than Obsidian.
2. **Obsidian — reduction.** Charcoal surfaces, pale brass, floating oval portraits, horizontal HP/SP bars and a
   circular upper-right map. Scenery remains visible between the party members and command group. Active effects
   move to the upper left, replacing the legacy skull/doll tableaux above the commands.
   This gives the strongest modernisation without abandoning the portrait-based party identity. The round map
   crops the corners of the square viewport, so full-map access remains explicit. A square map could be retained
   independently if preferred.
3. **Field journal — recomposition.** Leather brown, vellum, antique brass and muted oxblood health bars.
   The party becomes a left-side roster with named, numbered resources beside the same portraits. Named buffs
   sit under a square navigation chart. Gold/food and the four tools occupy separate bottom trays.
   This feels like an expedition kit and supports explicit statistics, but changes established scanning habits and
   uses more of the left edge.

The user selected **Obsidian**. The other two studies remain available for comparison.

## Obsidian refinement 04

- Removed the old skull and doll icons from the lower-left corner. Party effects remain inspectable in the upper-left
  timed strip and its overflow; individual effects remain on their portrait medallion.
- Replaced the open-book icon with a closed leather field journal, ivory quill and inkwell in the same pale-brass style.
  The Books label and its journal/books destination stay the same. `obsidian-books-v2.png` is the active version;
  the previous generated icon is retained with its original provenance.

### Retained from refinement 03

- Alert diamonds now use brighter green, yellow and red facets with no checkmark, exclamation, cross or dash inside.
  The unlit incapacity jewel and timed recovery arc retain their separate behaviour. The portrait's accessible label
  also carries the danger state.
- Generated a coordinated set of sculpted pale-brass/ivory icons for Books, Party, Rest, Options and Followers, plus
  a round moonstone-star medallion for personal buffs. Each is an individual transparent image generated with the
  built-in imagegen tool. The other two variants retain their previous command art.
- Removed the horizontal lines beneath portraits; the oval rim and diamond above the selected face carry selection.
- Increased New Sorpigal from 12 px regular to 16 px bold, reduced letter spacing, and reinforced its shadow.
- The personal-buff medallion is a separate clickable button with a larger 28 px hit area. It appears only for a
  character with personal effects. Click Kareth's jewel to inspect his example Bless and remaining duration; it
  does not select the character. Clicking it again or pressing Escape closes the panel.

### Retained from refinement 02

Applied the user's review to the browser prototype:

- Removed top-centre area/danger text and the real-time control. The turn indicator appears beside the lower-left
  tools only when a turn phase is selected. The review toolbar can preview attack, movement and waiting.
- Removed “The company,” portrait slot numbers and idle “Ready” text. Recovery and conditions retain their specific
  presentation. No action-ready light is shown during recovery or incapacity.
- Replaced the old status jewel art with small faceted vector sigils. Incapacity uses an unlit dark sigil;
  recovery uses a muted timed arc. Danger/readiness semantics still come from the existing gameplay rules.
- Increased the selected portrait's rim from one to two pixels, brightened its outer edge and enlarged the diamond
  from eight to twelve pixels. Other portraits keep the quieter rim. No selection pulsing.
- Gave HP/SP fills a restrained static highlight/shadow and inset track. Flat and shaded styles can be compared.
  “Play damage” shows a short trailing damage segment and a brief edge flash, then restores the sample. The optional
  low-HP pulse affects only living characters at 25% HP or less. `prefers-reduced-motion` disables these animations.
- Added status examples: Off, Short, Long, Two lines and Custom. The text sits directly above the portrait group,
  sizes to its content up to 620 pixels, and wraps. Unusually long custom text has bounded height and scrolling.
  A pinned preview stays visible when selecting a character. Off hides the example and allows ordinary temporary
  hover/action feedback to use the same space.

### Buff capacity and overflow

`game/party/Party.h` currently defines **22 distinct party buff slots** and **10 character buff types**.
The latter belong to individual members and should not be repeated in the shared strip. These are runtime capacity
counts, not a claim that all effects normally coexist. This matters especially for combinations, different spell
sources, conditional effects and character-versus-party variants of Glamour.

Party slots, in enum order:

| Group | Types |
| --- | --- |
| Utility / movement | Torch Light, Wizard Eye, Feather Fall, Detect Life, Water Walk, Fly, Invisibility |
| Protection / statistics | Stone Skin, Day of the Gods, Protection from Magic |
| Resistances | Fire, Water, Air, Earth, Mind, Body |
| Combat | Shield, Heroism, Haste, Immolation |
| Racial / additional | Glamour, Levitate |

Character types: Bless, Fate, Preservation, Regeneration, Hammerhands, Pain Reflection, Fire Aura,
Vampiric Weapon, Mistform and Glamour.

`applyCompositePartyBuff` in `game/party/PartySpellSystem.cpp` establishes a realistic busy case:

- Day of Protection applies six resistance buffs, Feather Fall and Wizard Eye: **8 party effects**.
- Hour of Power applies Heroism, Shield, Stone Skin and, when permitted, Haste: **up to 4 more party effects**.
  It also applies personal Bless. Haste can have a different duration from the other component effects.

Default proposal: **4 earliest expiries + N hidden**. The “+N” button counts only the hidden effects and opens a
two-column, scrollable panel beneath the strip. Click an entry for its details; return to the list, click outside,
click +N again or press Escape to close. With four or fewer active effects, no aggregate button appears. With zero,
the strip disappears. The alternative shows up to eight effects in two rows, plus the same overflow control.
Both modes stay **268 pixels wide** in the 1600 × 900 study; no effect count stretches them across the screen.

The review includes 0-, 4-, 12- and 22-slot samples. Twelve models the composite-spell set above; 22 is explicitly a
capacity demonstration. `buffs.js` lists each actual runtime party ID once, maps it to existing art, and sorts sample
remaining durations with enum order as a stable tie-break. Icons are effect-specific; multiple components are not
collapsed into a single composite-spell icon because they can expire or be replaced independently.

Timers are frozen examples. In a runtime implementation, update the order when effects change/expire, keep equal
durations stable, and hold order while pointer/focus or an inspector is on the strip so controls do not move under
the user. The expansion limit does not drop effects: every active party slot must remain inspectable. Strength,
mastery, remaining protections and other effect-specific data belong in each inspector when available.

## What the current HUD actually does

Reviewed the current shared renderer and input code, rather than treating a screenshot as the complete specification:

- `assets_dev/engine/ui/gameplay/gameplay.yml`: separate overlay, standard and widescreen gameplay layouts.
  The widescreen party-sized base uses `Basebar_cut`, `Basebar_ender` and four stepped side ornaments. The party
  uses `FACEMASK`, `selring`, `manaFRM`, `ManaG` and `manaB`. Gold and food/rest are separate upper-corner strips.
  Books, quick reference and options occupy the bottom-left strip. Body/skull buff tableaux sit above it. The
  square minimap, zoom controls and follower toggle sit at lower right.
- `game/ui/GameplayUiRenderer.cpp`: portraits, selection rings, health/SP bars, danger/readiness jewels,
  personal Bless indicators, portrait effects, Mistform tint and turn-based indicator. HP changes to yellow
  at 50% or below, red at 25% or below. The selected gameplay ring depends on ability to take action.
- `classifyPortraitAggroIndicator` in the same source: the jewel is hidden for characters unable to act or
  still recovering. Ready characters use green/yellow/red according to nearest hostile distance and engagement
  range. It does **not** indicate which individual character an enemy is targeting.
- `game/ui/GameplayHudRenderer.cpp`: status/hover text, resource labels, buff panels and layout selection.
  Gameplay layout selection is separate from character, spellbook, rest, dialogue and other overlay states.
- `game/gameplay/GameplayHudInputController.cpp`: portrait selection/double-click, item use, command activation,
  map zoom and follower interaction. UI controls are part of the shared gameplay path.
- `game/ui/GameplayPartyOverlayRenderer.cpp`: existing inspection, journal/map and other overlay rendering.
- `game/ui/WizardEyeMinimapRules.h`: minimap awareness has visibility rules; a restyle must preserve those rules.

The current art is cohesive in origin, but its repeated thick green frames give almost every group similar visual
weight. Small recovery/danger distinctions and narrow bars compete with large panel borders. The proposals reduce
the frame weight, distinguish primary party information from secondary tools, and provide a clearer place for effects.

## Prototype controls and limits

- Change direction using the three tabs; Current HUD displays the untouched `test_img/2000.png` reference.
- Switch between one, four and five characters, and between exploration, nearby enemies and melee danger.
- Combat shows low HP, recovery and unconsciousness together. Ready characters retain the corresponding danger
  jewel; recovering characters show a distinct proposed timer instead of a falsely ready jewel. Incapacitated
  characters keep their portrait and condition label.
- Click an available portrait to select it. Double-click or right-click to inspect the sample character.
  The proposed number shortcuts are slot labels; this browser does not rebind game controls.
- Inspect a buff, the original tableaux, followers or any command. Existing full-screen destinations are represented
  by a handoff notice, not redesigned inside this prototype. Game attack/cast/movement bindings are unchanged in scope.
- Use map zoom or click the minimap for a full-chart preview. The chart retains the existing map art.
- In refined Obsidian, use the review toolbar's Turns selector to show the lower-left turn indicator. Its button
  cycles attack, movement, waiting and off. The other two studies retain their initial top-centre mode control.
- Compare all shows the three directions under identical example conditions. Full screen enlarges the review;
  Design notes adds explanations. Dusk darkens the same scene for a simulated contrast check.

All proposed directions use **the same centred 940 × 528.75 crop** of `test_img/2000.png`, scaled to 1600 × 900.
The crop excludes the original interface and preserves the original centre reticle. It is intentionally tighter than
the raw screenshot. No scenery was inpainted, generated or retouched, and no portrait was redrawn. Frames, gradients,
ornaments and clipping are CSS/SVG. Names, statistics, buff durations, map position and follower count are sample data.
These are interactive visual studies, not a playable engine build or performance evidence.

Queries are shareable, for example:

```text
index.html?concept=obsidian&state=combat&party=5&dusk=1
index.html?concept=obsidian&buffs=22&buffLayout=rows&status=wrapped
index.html?concept=obsidian&state=combat&bars=pulse&turn=1
index.html?concept=journal&party=4&notes=1
index.html?concept=verdigris&export=1
```

`export=1` hides the review page around the 16:9 game view, useful for standalone screenshots.

## If this design moves into the game

Keep this scoped to the gameplay HUD. Retain the shared rendering/input ownership and its distinction between gameplay
and overlay layouts. Existing inventory, books, dialogue, spellbook, rest and other screens should continue to use
their current layouts. Decorative art can become a small set of reusable border/corner textures rather than a new
large texture for each panel. Reuse restored portrait frames and animation sources; preserve item use, inspection,
personal buffs, conditions and recovery semantics. Map marker visibility, fog and zoom continue to use the existing
runtime systems. Any additional effect timers or relocated hitboxes must read the current authoritative state.

Before runtime adoption, review busy buff lists, long names/localisation, wider gold totals, held items and cast
targeting, portrait FX, follower scrolling, narrow desktop aspect ratios and HUD scaling. These are integration
follow-ups, not implicit approval to redesign other screens or start an engine change.

## Validation

Browser captures and interaction checks are recorded in `browser_validation.json`.
Standalone direction captures are in `previews/`. This is an HTML/CSS/JS-only change; no game build is needed.

# Solo action HUD: implementation plan

The HUD for the solo action mode (one character in first person), as chosen on 2026-11-13 in the study
[solo_action_hud_20261113](../../level_generation/ui/solo_action_hud_20261113/README.md), view `?view=a2&frame=wow`.
Stages 1–5 are built (2026-11-13, see "What is built" at the end); the special-skills screen and Android are not. The
mode itself is described in [README.md](README.md). The talent rules behind the special skills are a separate design
and are only referenced here.

## The chosen design

- **Unit frame, top left.** One box in the native Obsidian frame holds a name row (name in gold Fondamento, class on
  the right) and the HP and SP bars with their numbers centred. An oval portrait medallion with one brass ring and the
  whole head overlaps the box's left end. The level sits on a brass coin at the medallion's foot, and the weapon in
  hand sits in a small socket at its shoulder.
- **Buffs and debuffs.** Two rows of timed icons under the box: buffs first (gold rim for special skills), then
  debuffs (red rim).
- **Action bar, bottom centre.** It sits in the party basebar's panel, flush with the screen bottom, with the potion
  and scroll sockets at its ends. Keys are 1–0, with an optional Shift row. The layout is still open (2 × 5, one row
  with slim sides, or 2 × 10).
- **MAW map progress.** The installed channel and tab sit on the action bar's top band, with the status line above
  the tab.
- **Crosshair.** The installed ivory cross, plus two recovery brackets.
- **Kept as installed.** Top bar, minimap, enemy health bars and combat log are unchanged. The optional thin HP/SP
  strip on the bar is off.

## Coordinates

The mockup draws at 1600 × 900. The gameplay layouts (`assets_dev/engine/ui/gameplay/gameplay.yml`) are in units of
a 480-high reference, so at 1600 × 900 one unit is 1.875 screen pixels (the party basebar's 446 units are its 832
pixels). The mockup's numbers in layout units:

| Element | Mockup (px at 1600 × 900) | Layout units |
|---|---|---|
| Unit frame box | 316 × 98 | 168.5 × 52.3 |
| Medallion (ring) | 120 × 156 | 64 × 83.2 |
| Medallion overlap into the box | 26 | 13.9 |
| Level coin, weapon socket | 38, 28 | 20.3, 14.9 |
| Buff tile, gap | 26, 9 | 13.9, 4.8 |
| Action slot, gap, row gap | 52, 6, 8 | 27.7, 3.2, 4.3 |
| Bar border + padding (2 × 5) | 16 + 7 | 8.5 + 3.7 |
| Bar border + padding (slim row) | 9 + 4 | 4.8 + 2.1 |

## Switching the HUD

**The flag.** Solo mode is a property of the game, chosen at new game and carried by the save. The HUD reads one
query, `GameplayScreenRuntime::soloHud()`. There are two candidates for where the flag lives; it must work in
Standard and in MAW either way, because `RulesetOptions` is ignored by Standard games:

- beside the ruleset selection in the save (`RulesetSelection`);
- in `Party` as a fixed party-of-one flag.

A one-shot `[debug] solo_hud` setting previews the HUD on any party, for captures and tours. Like the other `[debug]`
launch directives, it is never written back.

**One HUD, not two.** Solo mode reuses the element ids that other code already anchors to. Above all,
`OutdoorGameplayBasebar` stays the bottom frame in both modes: only its width and contents change. Six things already
anchor to that rect and follow it without changes:

- the status plate, `OutdoorGameplayStatusBar`, a `center_above` child;
- the potion and scroll sockets (`GameplayUiSkin::partyBasebarSocket`, `GameplayQuickItems`);
- the MAW channel `MapProgressChannel` and its tab (`GameplayMapProgressBar`);
- the breath meter (`GameplayUiRenderer`);
- the combat log panel;
- the MM9 talk bar, and the Android panels' lift (`touchPanelVerticalOffset`).

`GameplayScreenRuntime::resolveHudLayoutElement` already resizes this rect by member count. The solo branch sizes it
from the bar layout instead.

| Element (layout id) | Party HUD | Solo HUD |
|---|---|---|
| `OutdoorGameplayBasebar` frame | portraits, width by members | action bar slots, width by bar layout |
| `ObsidianPc1..5` and their arcs, gems, readiness, personal buffs | drawn | not drawn; the unit frame carries them |
| `ObsidianHeroBuffPanel`, `ObsidianSkullBuffPanel` | drawn | hidden; their buffs move to the buff rows |
| `OutdoorFly/Levitate/WaterWalk/FleetFootBuffIcon` | beside the skull | beside the unit frame box, still animated |
| `ObsidianPartyBuffStrip` (reserved, `visible: false`) | hidden | becomes the buff rows (see below) |
| `MapProgressChannel` and its tab | on the party frame | on the action bar, unchanged code |
| `OutdoorGameplayStatusBar` | above the frame | above the frame, and above the MAW tab when it shows |
| `OutdoorTopBar`, minimap, combat log toggle, followers toggle | unchanged | unchanged |
| Enemy health bars (`EnemyHealthBarRenderer`) | per setting | unchanged (target mode suits solo) |
| Crosshair (`renderGameplayMouseLookOverlay`) | ivory cross | ivory cross + recovery brackets |
| `Mm9HirelingRail` | MM9 only | unchanged |
| Number keys 1–5 | select a member | action bar |

The `party_frame` setting (hides the frame on plain gameplay) applies to the action bar's panel too. The slots then
draw on a soft shadow, as in the study's minimal variant.

## Unit frame

**Where.** A new `SoloUnitFrame` group in `gameplay.yml`, anchored the way the hero panels are today, below
`OutdoorTopBar` (`x = bar.x + 3`, `y = bar.y + bar.height + 6` in `resolveHudLayoutElement`). Its children:
`SoloUnitFrameBox`, `SoloUnitFrameMedallion`, `SoloUnitFrameFace`, `SoloUnitFrameName`, `SoloUnitFrameClass`,
`SoloUnitFrameHealth`, `SoloUnitFrameMana`, `SoloUnitFrameCoin`, `SoloUnitFrameWeapon`, `SoloUnitFrameReadiness`
and `SoloUnitFrameCounter`.

**Drawing.** In a new `game/ui/GameplaySoloHud.{h,cpp}`, called from `GameplayUiRenderer::renderGameplayHudArt` in
place of the portrait loop when the HUD is solo. Everything is drawn with existing helpers and existing art:

| Part | How | Art |
|---|---|---|
| Box | `GameplayUiSkin::renderPanel(context, rect, false, borderScale)`: the native nine pieces `obsidian_frame_tl/tr/bl/br/top/bottom/left/right` and the surface. The mockup's `frame9.png` only stands in for these in the browser | existing |
| Name, class | `renderLayoutLabel`; Fondamento gold `#f2d27a` for the name, Lucida for the class | fonts existing |
| HP, SP bars | straight meters: track, fill by `GameplayUiSkin::healthBand` (green ≥ 66 %, amber, red ≤ 33 %, as the approved HUD), numbers centred in Arrus | `obsidian_party_meter_track` existing; fills are solid quads |
| HP damage trail | `updatePortraitHealthTrail` on the member's `GameplayPortraitMeterState`, drawn as an amber segment | none |
| Reserved HP/SP (MAW auras) | a dark end segment and a mark, as `renderReservedArc` and `renderReservedMark` do on the arcs; needs straight-bar versions | none |
| Personal energy shield | a thin cyan line along the HP bar's top edge (the arc's `Shield`/`ShieldFlash`/`ShieldDown` materials) | none |
| Medallion backing | `submitHudTexturedEllipse` with the `__portrait_backing__` solid fill | none |
| Face | the portrait texture (`resolvePortraitTextureName`) fitted at about 88 % of the ring's inner height, centred slightly low, so the whole head shows; the ellipse only trims portraits that have a background. Mistform, invisibility and incapacitation modulate it as on the party frame | existing |
| Ring | `GameplayUiSkin::renderArc` through 360° with the rim material. Not `obsidian_hud_portrait_rim_selected`, which has two gold ovals (the "double oval" the user rejected) | none |
| Level coin | a solid ellipse, a 360° `renderArc` ring and the level in Arrus gold | none |
| Weapon socket | the same ring and the main-hand item's inventory icon | existing icons |
| Rage (Arms path, 2026-11-18) | `renderArc` round the medallion's right side, 3.8 units outside the ring, from the foot up to the crown (start 85°, sweep −165°): track, then `ArcMaterial::Rage` to the bar's share, `RageFull` (gold) when full; the weapon socket sits over it. See `ARCHETYPES_BUILD.md` | none |
| Readiness (aggro gem) | `renderPortraitReadiness`, placed at the medallion's lower right | existing |
| Class counter (MAW combo points, Elementalist stacks) | `renderCounterGemRow` along the box's top edge (built) | existing |

**Data.** The active member (`Party::activeMember()`): `health` and `spellPoints`, the effective maxima
(`GameMechanics::calculateEffectiveCharacterMaxHealth`, `calculateEffectiveCharacterMaxSpellPoints`), the level, the
class name and `equipment.mainHand`. The SP bar hides when maximum SP is 0, as the party frame's mana arc does.

**Input.**
- Hovering the frame gives the status text the portrait gives today.
- A click opens the character screen.
- A held right button inspects, the same `CharacterInspect` path as a portrait.

## Buff rows

**Where.** The reserved `ObsidianPartyBuffStrip` (eight `ObsidianPartyBuffN` slots plus overflow, `visible: false`,
whose note keeps it "for future special modifiers") becomes the solo buff rows, positioned under the unit frame box. A
second strip with the same template holds the debuffs.

**Contents, in order.**
1. Special-skill effects (gold rim). They come from the talent runtime.
2. Party buffs (`Party::partyBuff`, `GameplayBuffHudDefinitions`). Their icons are the `pIcon` atlases already listed
   there (`obsidian_buff_sb*a`). This includes the resistances, Torch Light, Wizard Eye, Day of the Gods and the rest.
3. Personal buffs (`Party::characterBuff`), timed potion effects (`gameplayPotionEffectLines`) and MAW auras
   (`gameplayUnslottedAuraLines`): what the personal-buff medallion's popup lists today.
4. Debuffs, in the second row: the member's conditions with a duration (`conditionExpireGameMinutes`).

**As built (2026-11-14, the user's follow-ups).** 17-unit tiles 2.4 apart, seven to a row: the buffs wrap under the
box, the conditions start a row of their own below (`placeTiles` in `game/ui/GameplaySoloHud.cpp`). Each tile names
itself: hovering it (or holding the right button on it, under mouse look) shows that buff's name, time left and power
(`GameplaySoloHud::buffTileAt`, `GameplayHudOverlaySupport::updateBuffInspectOverlay`); the hidden hero and skull
panels no longer answer there. A timed potion effect shows the buff it matches: an aura potion its buff's icon (Haste,
Heroism, Bless, Stoneskin ...), regeneration Regeneration's, an immunity the spell that cures its first condition; a
skill bonus keeps the generic potion art.

**Icons and gaps.**
- Debuff icons reuse the enemy bar's `obsidian_debuff_*` set (stun, paralyze, fear, slow, shrink, dark grasp, charm and
  the rest).
- MM conditions without an icon there (poison, disease, curse, weakness, insanity, asleep and others) need a small new
  set, in the same style as the existing debuff icons.
- Fly, Levitate, Water Walk and Fleet Foot keep their separate animated indicators (`gameplayMovementIndicators`), as
  the approved HUD requires. They are never folded into the rows.

**Timer.** Each tile has a clockwise sweep and the remaining time below it (`formatRemainingDuration`).
- The sweep needs the buff's total duration, which `PartyBuffState` and `CharacterBuffState` do not keep. One new
  field, `durationSeconds`, is set where a buff is applied.
- It could be saved, with a version bump (the current save version is 179), or kept transient and taken from the first
  frame after a load. Saving is the honest choice.

**Input.**
- A held right button on a tile opens `BuffInspect` (`updateBuffInspectOverlay`, `buff_inspect.yml`).
- A tap on Android opens the same view.

## Action bar

**Frame.** `OutdoorGameplayBasebar` is drawn by `GameplayUiSkin::renderPartyBasebar`: the panel plus the end
ornaments, or the sockets when the potion and scroll popups are on. Its solo width is
`cols × slot + (cols − 1) × gap + 2 × (border + padding)`, and its height is set by the rows. The slim-sides layout
passes a smaller `borderScale` to `renderPanel` and scales the ornaments to the bar's height. The sockets keep working,
because `partyBasebarSocket` is computed from the rect.

**Slots.** A template element `SoloActionSlot` with `gapX`/`gapY` (as `ObsidianPc1`/`ObsidianPc2` give the party gap).
The positions are computed for the chosen layout: 2 × 5 means keys 1–5 over 6–0; 2 × 10 means the Shift row over the
main row. They are drawn in `GameplaySoloHud`, with one quad batch for all slot frames, as the HUD batches today.

**What a slot holds** (`ActionBarSlot`, a small variant):

| Kind | Stored as | What pressing it does |
|---|---|---|
| Spell | spell id | the quick-cast path: `GameplaySpellActionController::tryBeginQuickSpellCast` generalised from "main or extra slot" to a spell source, so a bar spell gets the same targeting, failure, recovery, hold, repeat and attack fallback (`QuickSpellState`) |
| Special skill | talent id | the talent runtime's activation (its cooldown and recovery) |
| Item kind | a `QuickItemSlot` (the potion radial's shape: a kind of potion or scroll) | the quick item use path in `GameplayQuickItems`; the strongest bottle or scroll of the kind first (user, 2026-11-16; the bar has no weakest-first choice, unlike the radial) |
| Weapon action | Melee / Shoot | the battle orders' order kinds, for players who want the swing on a key |
| Empty | — | nothing, and the key stays reserved |

**Save data.**
- `Character::actionBar`, twenty slots (`std::array<ActionBarSlot, 20>`), saved with a new `SaveVersionActionBar`.
- In a solo game the bar is one character's.
- The four MMMerge quick spells (`Character::extraQuickSpellNames`) and Quick Cast stay as they are. A new solo game
  pre-fills the bar from them and from the battle orders' first spells; nothing is migrated in party games.

**States**, computed while drawing from state the game already keeps:

| State | Look | Source |
|---|---|---|
| Ready | cost tab (SP) top left, key top right | spell cost: the cost check battle orders use ("cannot pay") |
| Recovering | light wedge on every slot that needs a ready member | `Character::recoverySecondsRemaining` against the recovery it started from (see Crosshair) |
| Cooldown | dark clockwise wedge; seconds above 1.5 s | the talent runtime's per-character cooldowns |
| No mana | blue veil, cost in red | the same cost check |
| Out of range | red veil, key in red | the hover target's distance against the spell's or skill's range; only for targeted entries |
| Active / aura | gold rim and underline | the party or character buff the entry raises, or a MAW aura (`rules().spells`) |
| Proc | gold glow and spark | the talent runtime's proc flag |
| Charges | count and pips | the talent runtime |
| Item stack | count | items of that kind carried, cached on the inventory's change and not counted every frame |
| Unusable | greyed | the entry's requirement fails (Shield Bash without a shield) |

**Keys.**
- New `KeyboardAction` entries `ActionBar1..ActionBar10` (ini keys `action_bar_1..action_bar_10`, defaults 1–9 and
  0). They are listed in `settings_catalog.yml` and in the keyboard settings only in a solo game, the way the MAW keys
  are listed only in MAW.
- The Shift row is Shift held with the same keys, handled in code the way the bag keys read Shift. `InputBinding` has
  no modifiers, so it needs no second set of actions.
- A left click on a key (the cursor free: the classic controls, or the right button held under mouse look) uses it as
  its key does, held while the button stays down, so a spell repeats as a held key does (built 2026-11-16, at the
  user's request; `SoloBarSelectorState::clickedSlot`, read where the bar keys are read in
  `GameplayInputController`). The click is the bar's: the world does not attack or interact under it, and a click on
  an empty key does nothing. The hover hint says "{name} (click: use, Ctrl+click: change this key)".
- Conflicts that solo mode resolves:
  - The number keys select party members through `NumberHotkeyScancodes` in `GameplayScreenController`. With one
    member there is nothing to select, so the bar takes them.
  - Follower 1–4 default to 6–9. In a solo game their defaults are cleared (the follower panel stays on its key).
  - Bag 1–4 act only on the inventory page, so they do not collide.

**Assigning slots.**
- Drag from the spellbook. The spellbook's spell menu (the quick right-click menu that sets Quick Cast and the Quick
  Spell keys) gains "Put on bar".
- Drag from the special-skills screen, and from the inventory for potions and scrolls (as the quick item rings take
  them).
- Drag within the bar to rearrange; a right click clears a slot.
- A setting locks the bar against accidental drags.

**Tooltip.**
- Spells use the existing spell inspect view (`updateSpellInspectOverlay`), and items the item inspect view.
- Special skills get the same layout, filled from the talent data: name, school and mastery, cost, cooldown, recovery,
  description, and where it came from.

**MAW channel.** `MapProgressChannel` is a child of `OutdoorGameplayBasebar` and already spans its width, so it lies in
the action bar's top band without code changes. The tab rises from the right corner, and the revival notch and hover
popup are unchanged.
- The status plate today sits six units above the frame. When the progress tab shows, it must clear the tab:
  `renderGameplayHud` already lifts the plate over the turn dock and the MM9 talk bar, and the tab is one more such
  case.

## Crosshair recovery brackets

Two thin arcs, left and right of the cross. They are drawn in
`GameplayHudOverlaySupport::renderGameplayMouseLookOverlay` with the HUD arc mesh (`GameplayHudArcMesh`) and fill as
the member's recovery runs out: faint when ready, bright while recovering.
- They need the recovery's starting length, which is not kept: one transient field, `Character::recoveryTotalSeconds`,
  set where `Party::applyRecoveryToMember` applies a recovery.
- In real time they show only in a solo game; in turn-based they are hidden.

## Special skills screen

Built as layout A behind a Skills / Talents switch, not as a separate page: see [TALENTS.md](TALENTS.md).

- **Where.** A page beside Skills on the character screen: `CharacterPage::SpecialSkills` in `GameplayUiController`,
  a `CharacterSpecialSkillsButton` in `character.yml` next to `CharacterSkillsButton`, drawn in the shared
  character overlay of `GameplayPartyOverlayRenderer` (the Carved Obsidian 4:3 frame).
- **Layout (from the study).**
  - The schools on the left: weapon, armour and magic skills, coloured by mastery as on the party creation screen
    (grey, white, turquoise, gold).
  - The selected school's three tiers in the middle (Expert, Master, Grandmaster).
  - A detail card on the right with "Put on bar".
  - The points and the next point's level in the header.
- **Data.** Talent definitions live in an engine data table (proposed `assets_dev/engine/data_tables/talents.yml`, which
  a ruleset can patch as it patches other tables). The learned talents are saved as `Character::talents`. Points are
  derived from the level and promotions, and only what was spent is saved. The rules (rate, tiers, respec) belong to
  the talent design, not to this plan.

## Android and touch

- The bar takes the party frame's place at the bottom, as 2 × 5 with larger slots: about 40 units, against the
  approved 80-unit thumb buttons. The approved touch groups stay: Attack, Spell and Quick Cast on the right, and the
  Turn Mode / Inventory / Inspect column on the left.
- `touch_controls.yml` gains the slot size, and the existing lift of those groups over the basebar
  (`touchPanelVerticalOffset`) handles overlap.
- **Built 2026-11-23** (Android report: the desktop column lay under the Turn Mode / Inventory / Inspect column, keys
  4-0 covered at 2:1, and the keys below 160 logical units started the movement stick). `touch_controls.yml` overrides
  `SoloActionBar` as 2 × 5 keys of 40 units at the bottom centre, two units above the edge (232 × 100 units); in a solo
  run the touch groups lift over that bar instead of the hidden basebar, the bar is a HUD touch zone
  (`mobileTouchControls`) and the status line sits six units above it (`soloStatusLineTop`). No group needs a lift
  from 4:3 to 21:9 (`GameplayHudGeometryTests`, "solo action bar on touch screens"). Desktop keeps the left column.
- A long press shows the tooltip. Dragging and assigning happen in the spellbook and special-skills screens, not on
  the bar.
- The unit frame and buff rows use the desktop layout. A tap on a buff opens its inspect view.

## Scale, localization, performance

- **Scale.** Every new element is a layout element with the shared `scale` limits, so it follows the HUD scale like
  the rest. Captures cover 1600 × 900, 800 × 600, 4:3, 21:9 and a phone at 2:1.
- **Localization.** All visible text goes through `Engine::tr` with named placeholders:
  - the slot tooltips' lines ("{cost} SP", "Cooldown {seconds} s");
  - the "Put on bar" menu entries;
  - the special-skills page's headings and point line;
  - key names, through the keyboard settings' existing names.
  
  Talent names and descriptions follow the rules spell names follow ([Localization](../LOCALIZATION.md)).
- **Performance.** Nothing new polls per frame. Everything is read where it is drawn, from state the game already
  updates:
  - meters, buffs, recovery, cooldowns and the hover target's distance;
  - item counts, cached on the inventory's change;
  - the buff list, built from `Party` when the rows draw, a handful of entries.
  
  The solo HUD draws instead of the party portraits, not on top of them, so its cost replaces theirs.

  **Measured and corrected on 2026-11-15.** As first built the HUD cost about 130 µs of main-thread time and 173
  draws a frame at the New Sorpigal start (1020–1085 FPS against 1380–1420 with the party HUD; the dragon hands
  were not the cost). After the pass: about 55 µs and 52 draws more than the party HUD, 1150–1230 FPS against
  1360–1395. What it changed, and the rules for anything added to this HUD:
  - Solid fills and frames go through `GameplayObsidianPainter::addFill`/`addFrame` into a `Quads` list and one
    `submit`: the colours share the HUD palette texture, so a list is one draw whatever it holds. A frame was four
    draws, a fill built a texture name string and looked it up.
  - Things repeated per slot or tile are collected across the row and drawn once: the action bar draws all slot
    backings, then the contents, then all frames, then all key labels (`painter.texts`, two draws for any number
    of lines).
  - Outlined text is its eight copies in one `texts` call (four draws with the text itself, it was eighteen); a run
    that repeats the previous text reuses its glyph layout.
  - Nothing that walks the map's actors or the party's bags runs per frame: the MAW progress reading (asked three
    times a frame by the bar, the tab's bounds and the buff rows) is read ten times a second, the scroll and potion
    buttons' "carries any" four times a second (`GameplayOverlayInteractionState`).
  - The same day the whole HUD moved to one draw list ([HUD rendering](../HUD_RENDERING.md)): the solo HUD is 110
    draws and 1285–1375 FPS against the party HUD's 65 draws and 1410–1470. All HUD draws together now cost about
    50 µs of the frame, so what is left here (the unit frame's ovals, arcs and texts) is not worth more work.
  How to measure it again: [perf workflow](../../tools/PERF_PROFILING.md#fastest-route-where-does-the-frame-time-go).

## Stages

Each stage builds (`cmake --build build --target openyamm -j25`), runs its unit tests, and is checked with
engine-native captures from an input tour (`debug.menu_input_tour_path`, `capture:` steps) under `--isolated`, at the
resolutions above. Party-mode captures are taken too, to show nothing changed for parties.

1. **Flag and frame swap.** The solo flag with its `[debug] solo_hud` preview, `soloHud()`, the hero and skull panels
   hidden, and `OutdoorGameplayBasebar` sized by the bar layout with empty slots.
   - Check: a capture with MAW map progress, sockets and status plate all in place. A unit test of the solo basebar
     width per layout.
2. **Unit frame.** Read-only, from the member.
   - Unit tests of its geometry (a pure function from the resolved rect) and of the bar fills.
   - Captures at full, mid and low HP, with a personal shield, with MAW reserved points and with combo gems.
3. **Buff rows.** `durationSeconds` saved; the debuff icon gaps listed for art.
   - Unit tests of ordering and the sweep fraction, and a save round trip of the duration.
   - A capture with ten buffs and three debuffs.
4. **Action bar, input and save.** `Character::actionBar` and its save version, the `ActionBar1..10` actions, the
   generalised quick-cast source, item and special-skill entries, and the state overlays.
   - Unit tests: a save round trip, the key conflicts in a solo game.
   - A scenario in `tests/scenarios/` (a bar slot casts its spell with the quick cast's recovery and fallback).
   - An input tour pressing 1–0 and Shift+1.
5. **Crosshair brackets.** `recoveryTotalSeconds`; captures at ready, half and nearly ready.
6. **Special skills screen.** Once the talent rules exist; captures of each tier state; drag to the bar in a tour.
7. **Android.** The touch layout; a release APK, as the Android rules require.

## Open decisions

- **Basebar layout:** 2 × 5 (the mockup default, narrowest, full-size sockets), one row with slim sides, or 2 × 10.
- **Where the solo flag lives:** beside the ruleset selection or on the party. Is it a new-game option in both
  Standard and MAW, or MAW only?
- **The Shift row:** Shift or Ctrl. Shift is easier to reach while moving with WASD, and Ctrl often crouches.
- **A signature slot:** one Grandmaster skill on its own key (R) with a recharge bar, as the study's action bar sheet
  shows. Yes or no, and does it recharge by damage dealt or by time?
- **Buff durations:** saved in the save (honest sweep after a load) or transient.
- **The thin HP/SP strip on the bar:** off for now. Bring it back later, or only below 50 % HP?
- **The followers' 6–9 keys in a solo game:** cleared, or moved to Shift+6–9 (which collides with a Shift row on
  those keys).

## Progress note (2026-11-13, in progress)

Built and compiling: the gate, the solo HUD (unit frame, buff rows, 2 × 5 bar with sockets, MAW channel and tab, status
plate lift, crosshair brackets), bar keys 1–0, bar saving, assigning from the spellbook menu and the potion/scroll
popups, the bar's pre-fill. Every new-game path with the solo option goes through `makeSoloRunParty` (Party.cpp): the
New Game screen, the debug start (`--ruleset maw:solo`) and scenarios' `new_game_flow` (which the isolated launcher
uses to prepare its save). Captures done (below); stages 6 (special skills, another fork) and 7 (Android) remain.

**Talents hook (user decision 2026-11-13).** The talents use layout A of
`level_generation/ui/solo_talents_20261113` (its README, "Chosen"), reached through a Skills / Talents switch on the
Skills page; another fork builds them. What this work leaves them: `GameplayScreenRuntime::soloRun()` (MAW and solo:
the talents' gate) and `ActionBarSlotKind::Talent` (`id` the talent's id), which the bar draws as a filled slot and
saves, but does not yet use.

**Files touched.** `game/content/RulesetOptions.{h,cpp}` (flag, `solo` id, badge); `game/maps/SaveGame.cpp`
(version 181, flag and bar); `game/party/ActionBarSlot.h` (new), `game/party/Party.{h,cpp}` (`actionBar`,
`recoveryTotalSeconds`, `prefillSoloActionBar`, `makeSoloRunParty`); `game/ui/screens/NewGameScreen{.h,.cpp,PartySheet.cpp}`
(the toggle); `game/app/GameApplication.cpp` (view model gate, new-game paths); `game/scenario/ScenarioRuntimeDriver.cpp`;
`game/app/GameSettings.{h,cpp}` (`[debug] solo_hud`); `game/gameplay/GameplayScreenRuntime.{h,cpp}` (`soloRun`,
`soloHud`, layout branches); `game/ui/GameplaySoloHud.{h,cpp}`, `game/ui/SoloHudLayout.h` (new);
`game/ui/GameplayUiRenderer.cpp`, `GameplayBuffHud.cpp`, `GameplayHudOverlaySupport.cpp`, `GameplayHudRenderer.cpp`,
`GameplayMapProgressBar.{h,cpp}`, `GameplayOverlayTypes.h`, `GameplayBattleOrders.cpp`, `GameplayQuickItems.cpp`;
`game/gameplay/GameplayInputController.cpp`, `GameplayScreenController.cpp`, `GameplayScreenState.h`,
`GameplaySpellService.{h,cpp}`, `GameplaySpellActionController.{h,cpp}`, `GameplayItemService.{h,cpp}`;
`assets_dev/engine/ui/gameplay/gameplay.yml`; `game/CMakeLists.txt`; `tests/SoloRunTests.cpp` (new),
`tests/RulesetTests.cpp` (`eraseSoloRun` for the legacy save conversions), `tests/CMakeLists.txt`; `tools/RUN_GAME.md`.

## What is built (2026-11-13)

**The gate.** `RulesetOptions::soloRun` ("augmented solo run"), beside the ruleset selection in the save
(`SaveVersionSoloRun` = 181; older saves read as party games). It lives there rather than on `Party` because it is
chosen at new game and fixed for the adventure like the randomizer, the Load screen's badge reads it from the save's
summary (`describeRulesetSelection`: "Solo run", also for Standard), and it works the same in Standard and MAW (Standard
ignores the other options, not this one). It changes no rule: `GameplayScreenRuntime::soloRun()` is the one query; the
solo HUD reads `soloHud()` (a solo run or the one-shot `[debug] solo_hud` preview). The talents' hook is `soloRun()`
under MAW.

- **New game.** The party sheet's roster offers "Solo run" while the party is one adventurer
  (`NewGameScreenPartySheet.cpp`); on, it hides "+ Add adventurer". `startNewSessionFromCharacterCreation` keeps one
  member for a solo run (a direct start, `--ruleset maw:solo` or `--ruleset mmerge:solo`, keeps the first of its
  party) and fills the bar (`prefillSoloActionBar`: the weapon on 1, the known spells in book order on 2–0). MAW's
  party-of-one rules apply unchanged; they come from the party's size, not from this flag.
- **Presentation.** `GameApplication::renderFirstPersonViewModel` runs only with `soloHud()` and arms
  (`[debug] view_model_path`). Without them `ViewModelLink::meleeSwings` stays false, so party games never defer a
  blow even with `view_model_path` set, and a swing still waiting when the arms go away lands at once.

**The HUD** (`game/ui/GameplaySoloHud.{h,cpp}`, geometry in `game/ui/SoloHudLayout.h`, layout elements `SoloUnitFrame`,
`SoloActionBar`, `SoloActionSlot`, `SoloActionSlotRight`, `SoloActionSlotBelow` in `gameplay.yml`):

- `OutdoorGameplayBasebar` and `MapProgressChannel` resolve to `SoloActionBar` in a solo HUD, so the sockets, the MAW
  channel and tab, the breath meter and the status plate follow the bar. The plate rises above MAW's tab when they
  would overlap (`GameplayMapProgressBar::tabBounds`, solo only).
- The unit frame: the box is `renderPanel` at half border (the native frame pieces); the medallion a dark oval, the
  whole head (`submitHudTexturedEllipse` over the face area) and one brass ring (`renderArc` 360°, `NormalRim`); the
  level on a coin; the main-hand item's icon in the shoulder socket. HP and SP bars: track, the party HUD's fills
  (`healthMeterTexture`, `obsidian_hud_meter_sp`), the damage trail, the reserved share (MAW auras), the personal
  shield as a cyan line, numbers centred in Arrus.
- Buff rows under the box: party buffs (not the movement ones, which keep their animated indicators, now right of the
  box), the member's buffs and timed potion effects, oldest last; the sweep's whole is the longest remaining time seen
  while the tile shows (`GameplayOverlayInteractionState::soloBuffLongestSeconds`: transient, nothing saved). Debuffs:
  the conditions with an icon from the enemy bars' set (curse, weakness, sleep, fear, drunk, insanity, paralysis) or
  the curing spell's icon (poison, disease). Hovering a buff tile opens the party buff or personal buff popup.
- The hero and skull panels are not drawn and not hit-tested in a solo HUD.
- The action bar: the grid follows the layout (2 × 5 now: keys 1–5 over 6–0). A slot shows its icon (spell from the
  spellbook art, item or weapon icon), the key, a spell's SP cost (red without the mana, a blue veil), an item kind's
  carried count, and the member's recovery as a shade lifting from the top.
- Crosshair brackets (`renderCrosshairBrackets` from `renderGameplayMouseLookOverlay`), real time only.
  `Character::recoveryTotalSeconds` (transient) is set by `Party::applyRecoveryToMember`.

**Keys and slots.** `Character::actionBar` (twenty `ActionBarSlot`s: empty, spell, item kind, weapon, talent reserved),
saved. In a solo HUD the bar's keys (Shift up) drive it: the rebindable actions `ActionBar1`–`ActionBar10` (Controls,
"Solo run" group, their own `solo_bar` context; the number keys 1–0 by default, since 2026-11-15; were fixed scancodes),
and each slot shows its bound key's name. With the default keys the number keys no longer select members, and the
followers' 6–9 are left to the follower panel. A spell slot casts through the quick spell's path
(`QuickSpellState::barSpellName`, `GameplaySpellService::tryStartQuickSpellCast`'s new `barSpellName`): the same
hold, repeat, recovery and attack fallback. An item slot uses the kind as a quick item slot does
(`GameplayItemService::useQuickItemKind`). The weapon slot pulses Attack.

**Assigning (the cheaper route first).** The spellbook's spell menu gains "Put on the action bar" / "Take off the
action bar (N)" in a solo HUD (first empty of keys 1–0). The basebar's potion and scroll popups put a kind on the bar
with a right click (and take it off), and so does the Talents page for a learned active talent. To choose the key
itself, hold Ctrl and click a key or press its number: the slot selector (below, built 2026-11-14). No drag yet.

**Inspecting a key (user, 2026-11-15).** A held right button on a filled key shows what it holds, beside the key, in
the popups the rest of the game uses (`GameplaySoloHud::barInspectAt`):
- a spell gets the spellbook's spell card (`updateSpellInspectOverlay`);
- a potion or scroll gets the item card of the bottle the key would use, or of the kind when none is left;
- the attack key gets the main hand's weapon card, and the swap key the bow's
  (`GameplayHudOverlaySupport::tryPopulateItemInspectOverlayFromSoloBar`);
- a talent gets its kind, cooldown and effect at the rank learnt, in the buff popup (`updateBuffInspectOverlay`).

While the pointer is on the bar, the world under it is not inspected.

**Tests.** `tests/SoloRunTests.cpp`: the option id and badge, the save round trip of the flag and the bar (and a party
save staying a party game), the bar's pre-fill, the grid for 2 × 5, one row and 2 × 10, recovery and sweep fractions,
and the recovery total.

**Captures** (`level_generation/ui/solo_action_hud_20261113/native/`): `solo_maw_*` (MAW solo at 1600 × 900: the
filled bar, key 2 casting Torch Light, the MAW tab with the plate above it, the no-mana veil), `solo_43_*` (Standard
solo at 1280 × 960: key 3 casting and killing), `party_*` (a party game with `view_model_path` set: the party frame,
hero and skull panels as before, no arms).

**Tests run.** `SoloRunTests` (6 cases) pass; the focused save, ruleset, battle orders, quick item, creation, HUD,
shield and melee tests pass except three ruleset legacy-save conversions ("saves written before rulesets", "the save
list reads…", "saves before the MM9 formation") that fail with or without this work: checked by switching this work's
save fields off, they come from another uncommitted save change in the tree (version 180).

**Not built yet.**
- Rebindable bar keys (`ActionBar1..10` actions), the Shift row and the signature slot; the weapon slot does not
  repeat while held.
- Drag and drop onto the bar; a slot's tooltip; cooldown, proc, charges and range states (they need talents).
- The unit frame's aggro gem (the class counter gems are built, see "Class counter gems" below); conditions without
  timers; icons of their own for poison, disease and the other conditions.
- The special-skills screen (stage 6) and Android (stage 7: the bar's touch slots and `touch_controls.yml`).

**Decisions taken here.** The flag beside the ruleset selection (above). Number keys read as scancodes rather than new
bindable actions, so nothing changes in the keyboard settings of party games. Buff sweeps transient. The 2 × 5 layout
as the default (the open decision stands; the others are layout changes).

## Left-bar layout (built 2026-11-13)

The user moved the bar to the left after seeing the 2 × 5 bar in game, and approved the study's `view=a3`
(`topbar=right`, `lbar=corner`, `lslot=64`, `sct=center`). They then changed the clock: it is not hidden but sits
as a small plate on the minimap's lower rim, between the zoom buttons, as WoW shows its time. Everything below applies
only while `GameplayScreenRuntime::soloHud()` holds; party games are unchanged (`native/left_party_unchanged.png`).

- **Top right.** `OutdoorTopBar` and its children shift to the top-right corner. `OutdoorMinimapFrame`, its tabs, the
  follower panel and MM9's hireling rail drop by `SoloTopRightDrop` (16 units), which puts the minimap's rim just under
  the bar. All of this happens in `GameplayScreenRuntime::resolveHudLayoutElement`'s solo walk over each element's
  owners, so every child, hover and click follows.
- **Clock.** `ObsidianMinimapClock` resolves to a 40 × 11 unit plate centred on the circle's lower edge, with its text at
  0.62 of its scale. The plate draws with the label (`GameplayUiRenderer`), over the minimap. Its own layout element
  resolves empty so the layout pass does not draw it under the circle.
- **Unit frame.** It sits in the freed top-left corner (`SoloUnitFrame` at 7.47, 6.4 units).
- **Potion and scroll buttons.** Two round sockets sit on the medallion's upper-left rim
  (`SoloUnitFrameLayout::scrollSocket`, `potionSocket`) and mirror the coin. `GameplayQuickItems::itemButtonAnchor`
  places the buttons there in a solo HUD. They draw as the frame-off buttons (dark disc, brass ring, lit while their
  popup is open) and open the same popups, which stay centred on the screen as before.
- **Action bar.** `SoloActionBar` is one column of keys 1–0 down the left edge under the frame: 64 px slots at
  1600 × 900 (34.13 units), 5.9-unit border, 2.67-unit gaps. `soloActionBarGrid` reads a panel one slot wide as up to
  ten rows. The panel is `renderPanel` at half border, the unit frame box's frame pieces. A thin brass rule between keys
  5 and 6 splits the column into two blocks of five (the only eye candy that fitted cleanly: there is no room for a foot
  ornament).
  - **Short screens.** When the column would run past the bottom edge (HUD scale), the resolver shortens it to end
    2 units above the edge, and the renderer scales the slots, gaps and keys by the same factor, so they shrink to fit.
  - **Frame setting off.** The slots stand on a soft shadow.
- **No bottom frame.** `renderPartyBasebar` is skipped in a solo HUD. `OutdoorGameplayBasebar` still resolves (to a
  one-member frame at the bottom centre) for what measures from it: the potion popups' scale, the breath meter, an
  MM9 talk.
- **Status line.** It is pinned 8 units above the bottom edge.
- **MAW progress.** `MapProgressChannel` is set into the unit frame box's bottom band, under the bars, 2.13 units
  high. Its tab stands at the box's right end, level with the channel and with its whole text, and its hover popup
  hangs below (`GameplayMapProgressBar::Popup::above`). The status plate's lift over the tab now applies only when the
  tab is in the screen's lower half.
- **Self combat text.**
  - *Events.* `Party` pushes `SelfTextEvent`s (damage with the points a raised shield took, heal, condition gained,
    condition cleared) from `applyDamageToMember`, `healMember`, `applyMemberCondition` and `clearMemberCondition`,
    capped at 16 waiting. `GameplaySoloHud::renderHud` takes them where it draws: no per-frame polling of HP.
  - *Drawing.* The lines show below and right of the crosshair in Alegreya SemiBold with a dark outline: newest at the
    bottom, held 1.4 s, then faded over 0.8 s, eight at most. Heals are green, damage red ("-180 (64 blocked)"),
    conditions amber, "… fades" grey.
  - *Regeneration.* Regeneration ticks (`healMember`'s `regeneration` flag: MAW's regeneration, ten ticks a second,
    and the Regeneration spell) are their own event kind. The HUD sums them and shows one line per half second
    (user, 2026-11-16: a line per tick came far too often).
  - *Filter.* Amounts below 1 % of maximum HP (aura ticks, leech, half a second of slow regeneration) are left out.
  - *Not yet.* SP gains and "resisted" are not shown: SP changes have no single entry point, and resistance is folded
    into the damage before the party sees it.
- **Android.** The left column is the layout there too, but touch slots are still stage 7 (not built); the old 2 × 5
  touch plan is superseded by this layout's column.

**Captures** (`level_generation/ui/solo_action_hud_20261113/native/`), with the Oblivion arms set:
- `left_maw_hud`, `left_maw_key2` (MAW solo at 1600 × 900, key 2 casting);
- `left_maw_potions` (the potion popup from the socket, opened with V: a tour click cannot reach a HUD button while the
  mouse looks);
- `left_43_hud`, `left_43_key2` (1280 × 960);
- `left_std_selftext_damage` (−320, Poisoned, −180) and `left_std_selftext_heal` (+11 from a potion);
- `left_party_unchanged` (a MAW party game with `view_model_path` set).

**Tests.** `tests/SoloRunTests.cpp` adds the column grid and the sockets' place, and the self text queue (kinds,
amounts, the cap of 16).

## Alert glow (built 2026-11-14, replacing the alert gem)

The user first asked for an aggro indicator on the minimap's upper-left rim, after MM9's compass gem, then (the same
day) for a more visible one: a shaded oval round the portrait's oval and the minimap. A solo HUD now draws a soft glow
just outside the medallion (8 units, under the box and the ring) and outside the minimap circle (9 units):
`GameplaySoloHud::soloAlert` decides the state, `GameplaySoloHud::renderAlertGlow` draws it (one white texture made
at run time, clear inside the oval and fading outwards, tinted per state):

| State | When | Glow |
|---|---|---|
| Unlit | the member cannot act | none |
| Blue | turn-based combat | bright blue |
| Red | a hostile within melee range (`PartyRedAlertDistance`) | bright red, breathing once a second |
| Yellow | a hostile within the yellow alert range and the engagement range | bright yellow |
| Green | otherwise | quiet green |

Unlike the diamonds it shows danger alone, not readiness (the bar's keys show recovery). It reads the nearest-hostile
distance the HUD already measures each frame. The gem art (`obsidian_solo_alert_<state>`,
[the gem study](../../level_generation/ui/solo_alert_gem_20261114/README.md)) is no longer drawn.

## Slot selector (built 2026-11-14)

The user asked to choose which key a thing goes on: Ctrl and a key opens a searchable list of everything the member
can put there (`game/ui/GameplaySoloBarSelector.{h,cpp}`; the pure filter and assignment in
`game/ui/SoloBarSelectorModel.h`). Only in a solo HUD on plain gameplay; the three right-click routes stay.

- **Holding Ctrl** (the user's follow-up) pauses the game as the potion popups do (`gateStandardWorldInput`), frees the
  cursor from mouse look, lights every key of the bar with a gold rim and a soft glow and says "Click a key to choose
  what goes on it" in the status line. Letting go resumes play. Not while an action is bound to the held Ctrl key, and
  with the debug turbo movement (`[debug] turbo_movement`, also Ctrl) not while a movement key is held: Ctrl pressed
  standing still arms the bar, a movement key then gives it back to the turbo.
- **Opening.** Ctrl and a bar key (`ActionBar1`–`ActionBar10`, 1-0 by default), or a Ctrl
  click on a key (also under the cursor of the classic controls). Neither fires the key. Hovering a key with the
  cursor free says "Ctrl+click: choose what goes on this key" (empty) or the thing's name. With the selector open,
  Ctrl and another key moves it to that key.
- **The window** stands beside the bar, level with the chosen key and clamped on screen, in the potion popups' look
  (their panel colours, Fondamento title and buttons, Arrus names, Alegreya details, rows, scrollbar); the chosen key
  gets a gold rim. Header "Key N" and Close; a search field that always types (the game's SDL text input, as the
  Battle Orders search: `GameApplication::applicationTextInputActive`, `Engine::Utf8::appendPrintable`; Backspace
  edits; Escape clears the text, then closes); tabs All, Spells, Talents, Potions, Scrolls, Actions (a tab without
  entries is greyed); the list (All groups the categories under headings; wheel and scrollbar); "Empty this key".
  A click away closes it. While it is open the keyboard is text: the hotkeys, journal keys, number keys and follower
  keys are off, as for the other searches.
- **What it lists**, built once when it opens (a tab or search change filters the same entries again): the known
  spells (`knownSpellIds`, the spellbook's) in book order with school and SP cost (`PartySpellSystem::manaCost`, the
  bar's check); learned active talents with rank and cooldown (MAW solo only); one row per potion and scroll kind the
  party carries (`QuickItemSlots::partyItemKinds`, as the popups) with the count; Attack (with the weapon's name) and
  Swap weapon when a bow is equipped. What the key holds now stays listed even when not known or carried (greyed).
  A row on this key is drawn selected; a row on another key carries that key's number.
- **Choosing** puts the thing on the key; the same thing on another key is taken off there (a move;
  `soloBarAssign`, `soloBarSameEntry`: a potion kind matches whatever bottle rule). The status line says
  "{name} is on key {key}".
- **Android** (not built): a long press on a key should open the selector (the touch bar is stage 7); the search field
  then needs the on-screen keyboard (the managed SDL text input already raises it), and the tabs alone are enough
  without typing.

**Found here.** Key 0 is also the default Follower Panel key, so in a solo run a plain 0 both uses the bar's key 0 and
toggles the follower panel (before this work; Ctrl+0 no longer does). Ctrl+click on a monster or villager is Steal in
the world; in a solo HUD Ctrl now arms the bar and pauses, so a solo run cannot steal with Ctrl+click.

**Tests.** `tests/SoloRunTests.cpp`: the filter by tab and by a case-insensitive part of the name (headings only for
matching categories, disabled tabs) and put/move/empty on the bar.

**Captures** (`level_generation/ui/solo_action_hud_20261113/native/`, MAW solo Cleric at 1600 x 900):
`selector_ctrl_held` (lit keys and the hint), `selector_ctrl_click_opened` (Ctrl click on key 0),
`selector_ctrl_released` (key 0 emptied), `selector_empty_key` (Ctrl+0 on the empty key), `selector_spells_tab`,
`selector_search` ("bolt"), `selector_potions_tab`, `selector_potion_assigned` (Cure Wounds on key 0, count 4),
`selector_move_before` and `selector_spell_moved` (Fire Bolt from key 3 to key 9).

## Class counter gems (built 2026-11-17)

A solo run showed no combo points or Elementalist stacks: the party portraits draw them round the HP arc
(`level_generation/ui/maw_combo_points_20261025`, option B), and the solo HUD draws no portraits. The unit frame now
draws the same gems, a straight row centred over the bars on the box's top edge, right of the weapon socket
(`SoloUnitFrameLayout::counterX/counterY`, `renderCounterGemRow` and the pure `counterGemRowPlaces` in
`GameplayPortraitGems`). The bottom band was not free: MAW's map progress channel and its tab sit there. Five rubies
for an Assassin (radius 4.4 units, half-lit for an arrow's half point); ten amber gems for an Elementalist (radius 3.3)
with the number badge right of the row and the pale gold second lap past ten. The row's badge is wider than the arc's
(6 + 6 units a digit), because Lucida's digits came out wider than the pill at the unit frame's scale. Hovering the row
opens the counter's popup below it (`GameplaySoloHud::counterAt`); in solo play the party portraits' hidden gems no
longer answer the hover. Test: `SoloRunTests` (the row clears the weapon socket and the name row and stays inside the
box).

# Party creation study — 1 November 2026

Mockups for a redesigned, full-screen party creation screen in the approved Carved Obsidian style. Three approaches,
each an interactive page on real game data, plus a comparison and a recommendation in [index.html](index.html).
Nothing in the game changed; everything lives in this folder.

**Recommendation:** approach C (focus sheet + roster rail), with approach B's skill board as C's "Party board"
overlay. See [index.html](index.html#comparison) for the comparison table and the reasons.

## Running it

Serve the repository root and open the index:

```sh
python3 -m http.server 8917 --bind 127.0.0.1        # from the repository root
# http://127.0.0.1:8917/level_generation/ui/party_creation_study_20261101/
```

The pages load fonts, portraits, class icons, menu art and voice WAVs from `../menu_study_20260928/assets/` and
`../../../assets_dev/engine/`, so they need the server (fonts are blocked from `file://`).

The review bar above the canvas switches approach, Standard/MAW rules, starting continent, view (16:9, 4:3 window,
phone) and party (a sample five or a fresh one-member start). URL parameters do the same:
`?ruleset=maw&continent=jadame&device=phone&party=fresh`, and `export=1` hides the bar for screenshots.

- **Mouse:** click a skill to choose it (or to plan it in Plan mode); hover or right-click for its card.
- **Touch (phone view):** tap selects and opens the skill card with large Choose / Plan buttons. No hover, no right
  button: Android menus have no long-press right click, so everything important is visible or one tap away.
- **Phone view** draws a 6.5″ 20:9 phone with a 9 mm fingertip under the pointer. "Mark <5 mm targets" outlines
  every interactive element shorter than 5 mm on that phone.

## Files

| File | Purpose |
| --- | --- |
| [index.html](index.html) | Overview, comparison, recommendation, screenshots |
| [a.html](a.html), [b.html](b.html), [c.html](c.html) | The three approaches |
| [common.js](common.js), [common.css](common.css) | Shared model, creation rules, popups, audio decoder, stage scaling and device views |
| [board.js](board.js) | The party skill board (approach B, and C's overlay) |
| [extract_data.py](extract_data.py) → [data.js](data.js) | Real data from the tables (rerun after table changes) |
| [test_browser.mjs](test_browser.mjs) → [validation.json](validation.json), [shots/](shots/) | Headless Chrome check (48 checks, no console errors) and screenshots |

## Revision C2 (chosen approach, Discord feedback)

The user chose C. [c2.html](c2.html) applies the first round of feedback; [c.html](c.html) stays for comparison.
Screenshots: [shots/c2-desktop.png](shots/c2-desktop.png), [shots/c2-maw.png](shots/c2-maw.png),
[shots/c2-phone.png](shots/c2-phone.png).

- Layout: identity (name, class, voice), attributes and the race card share a compact top strip; the skill list sits
  below it in three columns; the creation paperdoll fills a full-height column on the right, composited like
  `NewGameScreen::buildCreationPreviewDollPixels` (background, body, open hands), with Change portrait / Default /
  Remove under it.
- Every roster card has a "−" in its top-right corner that removes that character (hidden when only one is left;
  removing a card above the selected one keeps the same character selected). Remove under the doll stays too.
- No large portrait. Clicking the doll or the selected roster card's portrait opens the portrait grid (hover shows
  "change"; always shown on touch).
- Name and class fields carry field labels; help captions ("racial traits", "own voice of #N", "change") are gone.
- The voice card is the voice field: its title ("Voice 1 ▼") opens the voice picker, with three sample lines below
  (Choose me, Hello, Yes). "Other voices…", "Victory" and the line count are gone.
- The race card no longer lists the race's classes, and attributes with identical start/maximum/cost share one line.
  Per-attribute limits moved off the stepper rows (the ▲/▼ mark stays, with the detail on hover).
- The skill list shows only skills the class line can learn (now or after promotion). The mastery letters ("M›G") are
  replaced by the name colour for the best mastery reachable with promotions, as the familiar game rarity tiers: grey
  Normal `#9c9e92`, white Expert `#f0ece2`, turquoise Master `#8fd8cc`, gold Grandmaster `#f2c94c`. The game has no
  per-mastery colour code yet; this one could become the convention for the character skills screen too. The skill
  card uses the same colours and drops the mastery letter; a level the class line can never reach is the whole row
  in the game's penalty red (`#ee8275`, `GameplayUiSkin::Penalty`). Details stay on hover / right click. Rows tighten above 25 and 30 skills; every Standard and MAW
  race/class combination (up to 37 skills) fits three columns, and every race card fits (checked in headless Chrome).
- No per-skill markers for other members on the sheet: whole-party coverage lives in the Party board overlay (the
  header keeps the "Party covers N of M skills" summary).
- No skill planner: Plan mode, ⚑ plans and "Plan for later" are gone from C2 (`App.planning = false`; A, B and C
  keep them). Coverage counts only skills the party actually starts with.
- Legend reduced to ◆ starting, ○ can pick and the colour key.

## Native implementation (2 November 2026)

C2 replaced the old single-member `NewGameScreen` in the game. Captures from the running game (1600x900 unless noted)
are in [native/captures/](native/captures/).

- Layout: `assets_dev/engine/ui/gameplay/character_creation.yml`, generated by
  [native/make_layout.py](native/make_layout.py) from c2.html's geometry. It holds the regions and fixed labels; the
  repeated rows (roster cards, attribute rows, skill rows, popups) are laid out in
  `game/ui/screens/NewGameScreenPartySheet.cpp` in the mockup's 1600x900 pixels.
- Rules shown on the sheet (skill states, class lines, race card lines, party coverage) live in
  `game/ui/screens/PartyCreationSheet.cpp`, with tests in `tests/PartyCreationSheetTests.cpp` and the screen's
  add/remove/rename/board behaviour in `tests/NewGameScreenTests.cpp` (both in `openyamm_runtime_tests`).
- Symbols: the menu fonts have none of the mockup's symbols, so ◆ ✓ ○ • ▲ ▼ ★ ✦ ▶ − are white 48x48 PNGs
  (`assets_dev/engine/hud_x2/menus/omenu_glyph_*.png`, made by [native/make_glyphs.py](native/make_glyphs.py)) tinted
  when drawn.
- Popups: portrait grid (by race, with the race's attribute trends; # numbers, party badges, voice under each),
  voice picker (voices of the portrait's sex, three sample lines each), class picker (cards with the skills each class
  takes to Grandmaster, the class text and its line's mastery table for this race), mastery table and party board
  (click a circle to choose another adventurer's skill). Escape or Close closes them.
- The skill card opens after the pointer rests on a skill (0.35 s) or at once with the right button; the right button
  on an attribute name or the class shows the game's own help.
- Behaviour kept from the old screen: the 15-point pool and race steps, two skill choices, the race's fixed ability,
  name entry, Default, continent caster swaps, the MAW tooltip text and the God Lich debug preset. New: a typed name
  survives a portrait change, a new adventurer starts from an unused portrait, and removing an adventurer keeps the
  same one selected.
- Standard race card notes: `ClassRules::raceNotes` now lists the Undead (Mind and Body) and Vampire (Mind)
  immunities; MAW keeps its own notes.
- Skills a teacher can teach only later (not a starting choice) are drawn at about half opacity, in their mastery
  colour, so the starting skill and the choices stand out (user, 2 November 2026).
- The race card scrolls when a race has more lines than fit (the MAW Dragon), with a scrollbar and narrower text
  while it does. Every menu scroll box (`MenuDesignScreen::scrollViewport`) also scrolls by dragging its content, for
  touch screens: a press that moves 6 logical units becomes a drag and no longer clicks what it started on; settings
  sliders keep their own drags.

## The three approaches

**A · Five columns.** The vanilla MM7 layout in OpenYAMM style: five 288 px columns, each with portrait (opens the
grid), name, class, voice, a one-line racial summary, seven attribute steppers and the starting skills. A strip
below shows the selected column's whole skill list as 40 chips (44 in MAW) with mastery "now › after promotion" and
numbered party markers. It shows the whole party at once but is dense and has seventy small stepper buttons.

**B · Skill board.** The skill bingo takes most of the screen: two half-boards with skills as rows and the five
members as columns. Each cell shows that member's state (◆ fixed, ✓ chosen, ○ choosable, dim letter = learnable later,
›X = only after promotion) and mastery; the right column gives the best mastery the party covers, and the header
counts covered skills. Clicking any cell edits that member directly. A full one-member editor sits on the left.
Best for planning, heaviest to read, worst for touch.

**C · Focus + rail.** A roster rail of five cards (portrait, class, race, "7 pts · 1 skill to go") and one large
sheet: portrait, name, class, a voice card with playable lines, a race card in sentences, attributes with large
steppers, and the full skill list as wide rows in four columns with party markers. **Party board** opens B's board
as an overlay, so whole-party planning is one click away. Most readable, largest targets, closest to the current
single-member `NewGameScreen` flow.

## Design notes

- **Skill states** are the same in every approach: fixed starting skill (◆ gold), chosen (✓), choosable (○),
  learnable later from a teacher (•), only after promotion (›X), never (–). Mastery letters N/E/M/G use the game's
  help-text colours (Master gold, Grandmaster red); "M›G" means Master now, Grandmaster after promotion.
- **Coverage markers** are numbered member badges in the member's colour: filled = has it, hollow = planned.
- **Planner.** Plan mode, or the card's "Plan for later", marks skills a member should learn later, including ones
  that open only after promotion. Plans only affect the markers; they never count as starting skills.
- **Structured mastery.** The class picker and "Mastery table" show a table: skills × the class line (starting class,
  first promotion, both second promotions), ranks a promotion adds shaded, ◆/○ for starting skills, race tags on rows.
  The skill card shows each mastery's effect with "✓ now", the promotion(s) that unlock it, or "never".
- **Racial bonuses** appear on the portrait grid's race headers, in every member's race line or card and as tags on
  the skills they change: ▲/▼ attributes with their point cost and maximum, the race skill rules grouped by effect,
  MAW's flat +3 skills and resistances/immunities.
- **Voices** are numbered after the portrait whose own voice they are: "Voice N" belongs to portrait #N (the lowest
  such portrait when shared), and a voice no offered portrait owns is an "Extra voice". With this scheme every
  Standard starting portrait shows its own number except the two dragons that share a voice (#72 uses Voice 26, #75
  Voice 25). The raw voice id is usually portrait − 1, but not for the elves (#32 uses id 33, #34 uses id 31) and the
  dragons, so numbering by raw id would mislabel them. The picker lists voices of the portrait's kind (Man, Woman,
  Dragon…; "All voices" lifts the filter), shows the portraits that use each voice, and plays real lines. The game's
  voice WAVs are IMA ADPCM, which browsers cannot play, so common.js decodes them itself.
- **Paperdoll.** None of the approaches keeps the current screen's paperdoll: in A and B there is no room, and in C
  the space went to the race and voice cards. A small paperdoll could replace C's portrait-change caption area if
  wanted.
- **Canvas.** Everything is authored at 1600×900 browser pixels, the game's 853⅓×480 canvas at 15/8
  (`MenuDesignScreen.cpp` BrowserToLogical = 8/15), so positions translate straight into layout YAML.

## Touch measurements

On a 6.5″ 20:9 phone the 480-unit canvas is 67.7 mm tall (0.141 mm per unit, 0.075 mm per stage pixel). Measured over
every interactive element in phone view (`smallTargetAudit()` in common.js):

| | Targets | ≥ 5 mm tall | ≥ 7 mm both ways | Median height |
| --- | --- | --- | --- | --- |
| A | 161 | 3 % | 0 % | 1.7 mm |
| B | 277 | 4 % | 0 % | 1.8 mm |
| C | 74 | 8 % | 8 % | 2.3 mm |

No layout that keeps all 40 skills visible can reach the usual 7 mm (40 rows × 7 mm = 280 mm), so all three use a
two-step touch interaction: tap to select, then act on the skill card, whose buttons are about 6 mm in touch mode.
C's rows are at least wide (about 22 mm), which makes the first tap forgiving.

## Data sources

Extracted by [extract_data.py](extract_data.py) into [data.js](data.js); nothing is invented.

| Data | Source |
| --- | --- |
| Class caps per skill | `assets_dev/engine/data_tables/class_skills.txt` (columns are class ids) |
| Class kinds, promotion steps, names | `class_extra.txt`, canonical names from `game/party/SkillData.cpp`; mana mode from `class_multipliers.txt` |
| Fixed / choosable starting skills | `class_starting_skills.txt`, plus the race's ability as a fixed skill (`NewGameScreen::refreshSkillChoices`) |
| Race attributes, maxima, point steps | `class_starting_stats.txt` (`RaceStartingStatsTable` parsing) |
| Classes per race, continents | `character_selection.yml` (caster swap by continent as `startingCasterClassId`) |
| Race skill rules | `race_skills.yml`, applied as `ClassSkillTable::getEffectiveCap` (min, max, +rank, class-kind and warrior exceptions) |
| Portraits | `character_data.txt` (available at start, race, sex, default class and voice); images from `assets_dev/engine/icons_x2/` |
| Voices and lines | `character_voices.txt` (line categories, Man/Woman/Dragon/Undead kinds, notes), `sounds.txt`, `assets_dev/engine/audio/` |
| Skill and class text | `english/skill_des.txt`, `english/class.txt` |
| Names | `english/pc_names.txt` |
| MAW | `rulesets/maw/` patches applied as `RulesetDefinition.h` describes: cell overrides, appended rows and columns (Seraphim, Death Knight, Shaman, Elementalist; Cover, Mana Shield, Enlightenment, Retaliation), replaced `character_selection.yml` (free selection, 20 classes) and `race_skills.yml` (shift without class cap); MAW's flat +3 skills and resistances copied as display data from `MawClassRules.cpp` |

Creation rules mirrored in common.js: the 15-point bonus pool and its stat steps (`bonusPoolForState`,
`tryIncreaseStat`, `tryDecreaseStat`, at most 2 below base), exactly two optional skills, and the readiness message.
"Now" is `getEffectiveCap` for the starting class; "after promotion" is the best effective cap over the class's
promotion tree (same kind, next step), as `getHighestPromotionEffectiveCap`.

## Observations from the data

- `character_selection.yml` lists `available_race_ids` per continent, but `NewGameScreen::rebuildCandidates` never
  reads them: Standard offers every race on every continent (Antagarich lists races 0, 3, 7, 8, 9, yet Vampire,
  Dark Elf, Troll and Dragon portraits appear). The mockups mirror the code.
- Race skill rules that grant a minimum rank also create starting choices: a Dark Elf Knight may choose Meditation
  (Expert) because the Dark Elf rule applies to classes without mana (`raceSkillRuleApplies`, warrior code −5), and a
  Minotaur Cleric, Druid or Sorcerer may choose Throwing (classes whose own cap is none). The mockups show these as
  ordinary choosable skills with a race tag.
- Promotions are derived from `class_extra.txt` kind and step, so Sorcerer lists Arch Mage, Dark ArchMage and Master
  Wizard as second promotions, and Cleric lists Priest of the Light, Priest of the Dark and High Priest.

## Open questions for the user

1. Which approach: A (MM7 columns), B (board first) or C (focus + rail)? Should C keep B's board as an overlay?
2. Is the "Voice N = portrait #N's own voice" naming right? Should the voice list stay limited to the portrait's kind
   (today's behaviour), or offer every voice behind a toggle as here?
3. How many lines should the preview offer: a fixed sampler (Choose me, Hello, Yes, Thanks, Victory…) or the full list
   (50–100 per voice)?
4. Should planned skills persist after creation (for example as a note on the character sheet or in the journal)?
5. Drop the paperdoll from creation, or keep a small one?
6. Should Standard filter races by the continent's `available_race_ids`, which the data declares but the code ignores?
7. For Android, may the menu canvas widen to the phone's full 20:9 width? That gives 25 % more room for larger targets.
8. MAW starting classes number 20 per race; is a two-column class picker with the mastery table beside it enough, or
   should classes be grouped (might, hybrid, magic)?

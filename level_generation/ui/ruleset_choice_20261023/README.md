# Ruleset choice — mockup, 23 October 2026

Browser mockup for MAW phase 1 ([handoff](../../../devdocs/maw/HANDOFF.md)): the Standard/MAW switch on
**Choose Starting Continent** and the **MAW Rules** panel. The user approved this revision on 2026-10-23 and it is
integrated natively.

**Native implementation.** `assets_dev/engine/ui/gameplay/continent_selection.yml` (ruleset row, shorter cards) and
`ruleset_rules.yml` (the panel), drawn by `NewGameScreen::drawRulesetSwitch` and `drawRulesPanel`. The table values
and descriptions come from the ruleset's own `rulesPanel` in `assets_dev/rulesets/<id>/ruleset.yml`; the switch
appears only when a ruleset package is installed. Selects open the shared choice dialog. Desktop captures at
1600×900 are in [native/](native/).

Open [index.html](index.html) directly; the buttons at the top switch between the three states, and the switch,
difficulty rows, progression tabs, selects, toggles and the scrollbar respond. `?view=standard|maw|rules&export=1`
gives the captures in [previews/](previews/).

- Built from the native Carved Obsidian graphics (`assets_dev/engine/hud_x2/menus/`) and fonts at their native
  positions: the 853.33×480 layout canvas times 1.875. The approved continent cards keep their art and text; they
  are about 35 units shorter (65 px at 1600×900) to make room for the ruleset row.
- **Continent screen.** A two-tab switch under the head rule. Standard shows one line of explanation; MAW shows the
  chosen difficulty and progression and a **Rules…** button. Choosing a card still opens party creation at once.
- **Rules panel.** Replaces the continent content inside the same frame. Everything between the head rule and the
  footer is one scrolling body, so later options can be added below; it uses the shared menu scrollbar
  (`MenuDesignScreen::scrollViewport`: wheel, drag, page on a track click, hidden while everything fits).
  - Difficulty is a selectable table: monster HP and damage relative to MAW for a level-100 party
    (`devdocs/maw/data/difficulty.yml`), group sizes, loot bonus, and the selected level's special rules below.
  - Progression is a two-tab switch with its rule and the mastery thresholds that follow from it.
  - Challenge mode (None, Doom, Road to Insanity, Beyond Madness, Austerity) and the randomizer are live controls with
    a description of the chosen mode. A challenge mode keeps the difficulty for the whole adventure; Beyond Madness
    also sets Horizontal progression. Natively each control is enabled only when the ruleset package offers the
    choice (`ruleset.yml`), so they show disabled ("Coming in a later update") until phase 9 adds the rules.
  - Preferences can change at any time. The MAW team's credits sit under the table.
- **Defaults are MAW's own** for a new game: MAW difficulty, Free progression ("monster bolster on"), no challenge,
  no randomizer, homing on, friendly fire off, loot filter off (`MenuExtraSettings.lua` `BeforeLoadMap`,
  `zz_Maw-initialize.lua` `mawSettings`). Restore Defaults returns to them.
- `?view=rules&difficulty=hell&challenge=madness&randomizer=1&scroll=bottom` sets any state for a capture.
- Normal uses MAW's unreachable difficulty index 2 (deviation 1 in `devdocs/maw/DEVIATIONS.md`, pending approval).

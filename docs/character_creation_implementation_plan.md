# Character Creation Implementation Plan

## Purpose

Implement the full MM8-style character creation screen using OpenYAMM code and data, with OE used only as behavioral reference.

This document covers:

- screen layout and rendering
- selectable character roster and identity data
- class and race driven stat / skill rules
- interaction behavior
- starting a fresh single-character game from the screen
- asset and data gaps that must be resolved explicitly

No OE code should be copied. OE is reference-only.

## Source Material Analyzed

### Local layout and assets

- [character_creation_ui_layout.md](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/scaled/character_creation_ui_layout.md)
- reference image `test_img/dwi_missing/scaled/char_create.png`
- background template `assets_dev/Data/icons/makeme.pcx`

### Local runtime and tables

- [CHARACTER_DATA.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/CHARACTER_DATA.txt)
- [CLASS_STARTING_SKILLS.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/CLASS_STARTING_SKILLS.txt)
- [CLASS_SKILLS.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/CLASS_SKILLS.txt)
- [CharacterDollTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/CharacterDollTable.cpp)
- [ClassSkillTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/ClassSkillTable.cpp)
- [SkillData.cpp](/home/pjasicek/github/OpenYAMM/game/party/SkillData.cpp)
- [Party.h](/home/pjasicek/github/OpenYAMM/game/party/Party.h)
- [Party.cpp](/home/pjasicek/github/OpenYAMM/game/party/Party.cpp)
- [GameApplication.cpp](/home/pjasicek/github/OpenYAMM/game/app/GameApplication.cpp)
- [NewGameScreen.cpp](/home/pjasicek/github/OpenYAMM/game/ui/screens/NewGameScreen.cpp)

### OE reference examined

- `reference/OpenEnroth-git/src/GUI/UI/UIPartyCreation.cpp`
- `reference/OpenEnroth-git/src/Engine/Objects/Character.cpp`
- `reference/OpenEnroth-git/src/Engine/mm7_data.cpp`

## Required Gameplay Behavior

The new screen must support the following behavior.

### Default state

- There are `20` distributable stat points.
- A selected creation candidate provides:
  - portrait
  - doll / body preview assets
  - default class
  - default voice
  - race
- Current stat values start from race / class specific defaults.
- Current skill state starts from class defaults.

### Stat rules

- Max configurable stat on this screen is `25`.
- Min configurable stat is `default - 2`.
- Stat color rules:
  - white: current == default
  - red: current < default
  - green: current > default
- Some races apply asymmetric stat step rules.
  - Example from the requirement: Troll endurance uses `2 stat per 1 pool point`.
  - Subtracting must mirror the same rule.

### Skill rules

- Default class-granted skills are shown in yellow.
- Optional selected skills are shown in blue.
- Optional unselected skills are shown in white.
- Clicking a blue selected skill unselects it.
- At most `2` optional skills can be selected.
- Selected optional skills fill the free skill slots in the top skill box.

### Start game behavior

Clicking `OK` must start a completely fresh game with:

- one party member only
- `5` food
- `200` gold
- fresh world state
- no carried qbits or previous session state
- default epoch / date state
- start map `Dagger Wound Island`
- standard starting position for the map

## Visual Breakdown

### What is already baked into `makeme.pcx`

The template already contains most of the static frame art and labels:

- title
- name/class labels and fields
- portrait / voice labels
- bonus pool label and frame
- attribute area frame
- selected / available skills boxes
- bottom action area
- right-side cyan placeholder region

This means the implementation should render a small set of dynamic overlays on top of the template instead of reconstructing the entire screen from separate assets.

### Dynamic visual elements to render

- current name
- current class name
- portrait image
- portrait left/right controls
- voice left/right controls
- voice default button
- bonus pool value
- stat values plus plus/minus buttons
- selected skills
- available skills
- right-side preview panel
- bottom action buttons

### Right-side preview content

The filled reference screen shows the cyan placeholder replaced by a proper preview panel.

The panel content must be driven from `CharacterDollTable` data:

- background asset
- body asset
- head asset when present
- left hand unequipped art
- right hand unequipped art
- body offset X/Y

This should use the same asset composition approach already used by paperdoll-style rendering elsewhere, but assembled into a static character-creation preview instead of a gameplay equipment screen.

## Data Model Findings

## Selectable creation candidates

`CHARACTER_DATA.txt` already contains the right base identity table.

Important fields:

- `id`
- `defaultClassId`
- `defaultVoiceId`
- `defaultSex`
- `availableAtStart`
- `backgroundAsset`
- `bodyAsset`
- `headAsset`
- left/right hand assets
- `facePicturesPrefix`
- `raceId`
- body offset

This table is already loaded by `CharacterDollTable`.

### Important selection-policy issue

`availableAtStart` currently marks `52` entries as start-selectable in this repo.

That includes:

- core MM8 human entries
- dark elves
- minotaurs
- trolls
- dragons
- extra elf entries
- MM6 imports
- MM7 imports
- goblin imports

This is broader than a stock MM8 creation screen.

Implementation must make this explicit instead of silently accepting the full set.

Recommended policy:

1. Build character creation from `availableAtStart`.
2. Add a small filter layer for creation mode.
3. Default the filter to the MM8-native subset unless the user explicitly wants cross-game starts.

Recommended filter input:

- either a new column in `CHARACTER_DATA.txt`
- or a new `CHARACTER_CREATION_DATA.txt`
- or a hardcoded temporary allowlist keyed by `characterDataId`, with a clear TODO to data-drive it later

The temporary hardcoded allowlist is acceptable only as a bootstrap step.

## Class mapping

The local code already has the MM8 class-id bridge needed to connect `CHARACTER_DATA.defaultClassId` to class-skill tables:

- `mm8ClassIdForClassName(...)`
- `classNameForMm8ClassId(...)`

This removes the need for ad hoc mapping logic.

## Class skill data

`CLASS_STARTING_SKILLS.txt` already encodes creation-time skill availability:

- `F` = class default skill
- `C` = class can choose this skill at creation
- `-` = unavailable

This is the correct source for:

- yellow default skills
- white/blue optional skill list
- max-two optional-skill selection validation

`CLASS_SKILLS.txt` remains relevant after the character is created because it defines long-term class mastery caps, but the creation screen should primarily consume `CLASS_STARTING_SKILLS.txt`.

## Race and stat data

The current repo does not appear to have a dedicated character-creation race-stat table that directly expresses:

- base stat defaults by race
- stat step size by race and stat
- creation-time min/max rules by race and stat

The user requirement clearly needs one.

Recommended approach:

Create a new data table for creation-only race rules, for example:

- `assets_dev/Data/CHARACTER_CREATION_RACE_STATS.txt`

Each row should define:

- race id
- race name
- base values for all 7 stats
- minimum offset from base
- maximum creation value
- per-stat increase step
- per-stat decrease step
- optional UI order / grouping metadata if needed later

Example shape:

```text
RaceId  RaceName  MightBase  IntellectBase  PersonalityBase  EnduranceBase  AccuracyBase  SpeedBase  LuckBase  MinOffset  MaxValue  MightStep  IntellectStep  PersonalityStep  EnduranceStep  AccuracyStep  SpeedStep  LuckStep
4       Troll     18         5              5                13             15            14         7         -2         25        1          1              1                2              1             1          1
```

This data-driven table is preferable to hardcoding race math in UI logic.

## Recommended Architecture

## Screen ownership

Keep character creation as a standalone menu-mode screen, not a gameplay overlay.

Reason:

- it starts a new session from scratch
- it replaces the current roster-based `NewGameScreen`
- it is conceptually closer to main-menu flow than gameplay HUD flow

Recommended screen ownership:

- replace the current `NewGameScreen` implementation with a real character creation screen
- keep the `AppMode::NewGame` mode

## New runtime state object

Introduce a dedicated state object for the screen, separate from `Character`.

Recommended type:

- `CharacterCreationState`

Recommended contents:

- selected creation candidate index
- selected character data id
- selected portrait variant index
- selected voice id
- typed name
- resolved class name
- race id
- base/default stats
- current stats
- remaining bonus pool
- default skills
- optional skills available for selection
- optional selected skills
- preview asset references
- last-click timestamps for future double-click behavior if needed

Do not mutate a live `Party::Character` directly during UI interaction.
Build a final `Character` only when `OK` is pressed.

## Runtime services the screen needs

The screen will need read-only access to:

- `CharacterDollTable`
- `ClassSkillTable`
- localized stat / skill display names
- audio system for voice preview

It will also need a final handoff callback into `GameApplication` that accepts a fully built creation result rather than a roster id.

Recommended callback contract:

- replace `ContinueAction(std::optional<uint32_t> rosterId)` with a richer creation result

Example:

```cpp
struct CharacterCreationResult
{
    Character member;
};
```

Then use:

- `ContinueAction(const CharacterCreationResult &result)`

This is cleaner than reusing roster ids for a system that is no longer roster-based.

## Fresh Session Start Path

The current `GameApplication::startNewSession(std::optional<uint32_t> rosterId, ...)` is built around roster seeding and simulated multi-member startup.

That path should not be reused directly without refactoring.

### Recommended new flow

Add a new explicit entry point for character creation:

- `startNewSessionFromCharacterCreation(const CharacterCreationResult &result)`

This path should:

1. clear current session state
2. clear current save path
3. create a fresh one-member `PartySeed`
4. set:
   - `gold = 200`
   - `food = 5`
5. load `out01.odm`
6. seed only the created member
7. initialize outdoor runtime normally
8. place the party at the normal Dagger Wound Island start position
9. ensure event/qbit state is fresh
10. ensure time starts from the default epoch derived by normal world initialization

### Party seed contents

Build a one-member `PartySeed` with:

- one `Character`
- empty inventory, unless creation is later extended to include starter items
- `food = 5`
- `gold = 200`

The final created `Character` should explicitly set:

- `name`
- `className`
- `role`
- `portraitTextureName`
- `portraitPictureId`
- `characterDataId`
- `sexId`
- `raceId`
- stats
- selected creation skills

Health and spell points should be initialized from class/race defaults through a dedicated helper instead of ad hoc values in the screen class.

## Detailed Feature Plan

## Phase 1: Creation Data Layer

Goal: make the rules data-driven before building UI behavior on top.

Tasks:

1. Add a creation race-stat table.
2. Add a loader for that table.
3. Add a small creation-model helper module.

Recommended new module:

- `game/character_creation/CharacterCreationRules.h`
- `game/character_creation/CharacterCreationRules.cpp`

Responsibilities:

- resolve selectable creation candidates
- resolve class default skills
- resolve class optional skills
- resolve race base stats
- resolve stat step multipliers
- compute plus/minus validity
- compute stat color
- compute final selected skill list

This phase should be testable without UI.

## Phase 2: Screen State and Navigation

Goal: replace the current placeholder new-game screen with a stateful creation screen.

Tasks:

1. Replace the roster-list `NewGameScreen` state with `CharacterCreationState`.
2. Implement:
   - left/right portrait selection
   - left/right voice selection
   - default voice reset
3. Implement name editing.
4. Resolve class and race from the selected candidate.
5. Rebuild stat and skill state when the candidate changes.

Candidate-change behavior should be explicit:

- portrait change selects a different creation candidate
- class, race, default voice, stats, and skills all refresh from that candidate
- name can either:
  - stay user-edited after candidate switches
  - or reset to candidate default/random name

Recommended first pass:

- preserve manually typed name across portrait switches only after the user has edited it

## Phase 3: Stat Interaction

Goal: implement attribute editing with pool accounting and race-specific steps.

Tasks:

1. Add plus/minus buttons per stat.
2. Validate against:
   - min `default - 2`
   - max `25`
   - remaining pool
3. Apply race step rules.
4. Recompute remaining pool after every change.
5. Render white/red/green values correctly.

Recommended accounting model:

- store current stat values
- derive pool delta from `(current - default)` using each stat's step rule
- do not store pool and stats as independent mutable truths

Reason:

- this avoids drift and off-by-one bugs on asymmetric races
- the pool becomes a derived value from defaults and current allocation

## Phase 4: Skill Interaction

Goal: implement class-driven skill selection behavior.

Tasks:

1. Split skill set into:
   - default selected skills
   - optional available skills
   - optional selected skills
2. Enforce max `2` optional selections.
3. Clicking white optional skill selects it if capacity exists.
4. Clicking blue optional skill unselects it.
5. Render top selected-skills box from:
   - default skills first
   - optional selected skills after

Recommended ordering:

- preserve table order from `CLASS_STARTING_SKILLS.txt`

Reason:

- it gives stable UI positions
- it avoids reflow churn when toggling skills

## Phase 5: Visual Preview Panel

Goal: replace the cyan placeholder with the full preview composition.

Tasks:

1. Render background panel art.
2. Render doll background from character data.
3. Render body.
4. Render head when present.
5. Render left/right unequipped hands.
6. Apply the stored body offset.

This should be implemented with a small preview compositor helper rather than inline screen code.

Recommended helper:

- `CharacterCreationPreviewRenderer`

It should accept only:

- candidate data
- target rect
- scale

and produce the assembled preview.

## Phase 6: Voice Preview

Goal: make voice switching functional and OE-like.

Tasks:

1. Add a small audio entry point to preview a character voice.
2. When voice changes:
   - play a short preview line or reaction sound
3. When `Default` is clicked:
   - restore the candidate default voice
   - optionally replay preview

Current gap:

- the runtime can resolve default voice ids, but there is no dedicated character-creation voice-preview path yet

This will likely require a small audio API addition rather than heavy screen logic.

## Phase 7: Start Game Handoff

Goal: wire `OK` to a real fresh start.

Tasks:

1. Convert `CharacterCreationState` into a final `Character`.
2. Build a one-member `PartySeed`.
3. Call the new `GameApplication` fresh-start path.
4. Ensure the current menu/new-game mode closes cleanly.

Validation before allowing `OK`:

- bonus pool must be exactly `0`
- optional selected skill count must be `<= 2`
- name must not be empty after trimming

If the original game allows nonzero leftover pool, that can be revisited later. For now, consuming the full pool is the safer initial rule.

## Phase 8: Cleanup and Diagnostics

Goal: make the feature debuggable and safe to iterate on.

Tasks:

1. Add screen-local debug logging behind a debug flag for:
   - selected candidate id
   - class name
   - race id
   - stat defaults/current/pool
   - selected optional skills
2. Add small unit-style tests where feasible for:
   - stat pool accounting
   - race step behavior
   - class default/optional skill resolution

The stat/pool logic is the most bug-prone area and should be validated first.

## Asset Status

## Assets confirmed locally

- `makeme.pcx`
- portrait images for candidate characters
- doll/background/body/hand assets referenced by `CHARACTER_DATA.txt`
- portrait / voice left arrow:
  - `cc_up_L.bmp`
  - `cc_ht_L.bmp`
  - `cc_dn_L.bmp`
- portrait / voice right arrow:
  - `cc_up_R.bmp`
  - `cc_ht_R.bmp`
  - `cc_dn_R.bmp`
- stat plus button:
  - `cPlusup.bmp`
  - `cPlusht.bmp`
  - `cPlusdn.bmp`
- stat minus button:
  - `cMinup.bmp`
  - `cMinHT.bmp`
  - `cMindn.bmp`
- voice default button:
  - `bt_DfltU.bmp`
  - `bt_DfltH.bmp`
  - `bt_DfltD.bmp`
- bottom clear button:
  - `c_clr_up.bmp`
  - `c_clr_ht.bmp`
  - `c_clr_dn.bmp`
- bottom cancel button:
  - `c_cncl_up.bmp`
  - `c_cncl_ht.bmp`
  - `c_cncl_dn.bmp`
- bottom OK button:
  - `c_ok_up.bmp`
  - `c_ok_ht.bmp`
  - `c_ok_dn.bmp`

## Asset naming note

Earlier OE-driven assumptions pointed at some MM7-specific asset names.
Those should not drive the OpenYAMM implementation here.

For this screen, the local MM8-style asset set above is the correct source of truth.

## Assets still needing confirmation

I no longer consider the OE/MM7 names below to be required for the MM8 implementation:

- `presleft`
- `presrigh`
- `buttplus`
- `buttminu`
- `aframe1`
- `maketop`
- `makesky`
- `buttmake`
- `buttmake2`

If any additional creation-screen assets exist beyond the set above, they should be treated as optional polish until they are actually identified in the local asset dump.

## Open Design Decisions

These need explicit confirmation before or during implementation.

### Which creation candidates are valid

Because `availableAtStart` currently exposes 52 entries, we need to decide:

- strict MM8-native starts only
- all `availableAtStart` entries
- configurable filter

Recommended initial implementation:

- strict MM8-native subset

### Where race creation rules live

There is no existing local table for the creation-specific stat math.

Recommended answer:

- add a new dedicated creation-race table

## Proposed Initial OpenYAMM Creation Table

The user-provided direction for the first pass is:

- use OpenYAMM-native MM8 races/classes
- apply race-specific creation step rules for:
  - Troll: `+2/-2 Endurance` per pool point
  - Minotaur: `+2/-2 Might` per pool point
  - Dark Elf: `+2/-2 Accuracy` per pool point
  - Dark Elf: `-2/+2 Endurance` per pool point when moving away/toward base
- everything else defaults to `+1/-1`
- all creation base-stat rows should total `77`
- min base stat `7`
- max base stat `14`
- any stat with a `+2` increase rule can reach `30` instead of `25`
- any stat with a `+2` increase rule should start at base `14`

### Recommended structure

Use two data tables instead of one overloaded table:

1. class base distributions
2. race stat-step modifiers

That keeps class semantics separate from race-specific pool math.

### Proposed class base distributions

All rows sum to `77`.

```text
Race/Class    Might  Intellect  Personality  Endurance  Accuracy  Speed  Luck  Total
Human         11     11         11           11         11        11     11    77
Troll         13     7          7            14         13        11     12    77
Minotaur      14     8          7            13         13        10     12    77
DarkElf       9      12         10           9          14        12     11    77
Vampire       11     11         11           10         11        11     12    77
Dragon        13     10         9            13         11        10     11    77
```

### Proposed race creation-step modifiers

This table affects how plus/minus clicks interact with the bonus pool.
It does not change the class base row by itself.

```text
Race       Might  Intellect  Personality  Endurance  Accuracy  Speed  Luck
Human      1/1    1/1        1/1          1/1        1/1       1/1    1/1
Vampire    1/1    1/1        1/1          1/1        1/1       1/1    1/1
Dragon     1/1    1/1        1/1          1/1        1/1       1/1    1/1
Troll      1/1    1/1        1/1          2/2        1/1       1/1    1/1
Minotaur   2/2    1/1        1/1          1/1        1/1       1/1    1/1
DarkElf    1/1    1/1        1/1          2/2        2/2       1/1    1/1
```

Interpretation:

- `1/1` means:
  - `+` spends 1 pool point and changes stat by 1
  - `-` refunds 1 pool point and changes stat by 1
- `2/2` means:
  - `+` spends 1 pool point and changes stat by 2
  - `-` refunds 1 pool point and changes stat by 2

### Notes on the proposed values

- Knight and Minotaur are front-loaded into Might / Endurance / Accuracy.
- Cleric is biased toward Personality with balanced support stats.
- Necromancer is biased toward Intellect with lower physical toughness.
- Troll is a very physical spread with weak social/mental stats.
- Dark Elf is accuracy/speed/intellect leaning, with lighter endurance.
- Vampire is intentionally more even, but still fast and accurate.
- Dragon is powerful and sturdy, but not socially oriented.

### Recommended first-pass mapping

Use class-based base rows with the current MM8 race/class pairing:

```text
Knight       -> Human
Cleric       -> Human
Necromancer  -> Dark Elf
Troll        -> Troll
Minotaur     -> Minotaur
DarkElf      -> Dark Elf
Vampire      -> Vampire
Dragon       -> Dragon
```

If later data introduces race/class combinations beyond those defaults, the same two-table model still holds.

### Name defaulting

The reference behavior randomizes names in OE when face changes.
If random-name support is not yet available in OpenYAMM, implement:

- stable default name from candidate data if available
- otherwise blank name plus manual edit

Random name generation can be a follow-up.

### Starting loadout

The user only specified:

- 5 food
- 200 gold
- single created character

This plan assumes:

- no extra starter inventory unless explicitly specified later

## Recommended File Changes

Likely new files:

- `docs/character_creation_implementation_plan.md`
- `assets_dev/Data/CHARACTER_CREATION_RACE_STATS.txt`
- `game/character_creation/CharacterCreationRules.h`
- `game/character_creation/CharacterCreationRules.cpp`
- `game/ui/screens/CharacterCreationScreenState.h`

Likely modified files:

- [game/ui/screens/NewGameScreen.h](/home/pjasicek/github/OpenYAMM/game/ui/screens/NewGameScreen.h)
- [game/ui/screens/NewGameScreen.cpp](/home/pjasicek/github/OpenYAMM/game/ui/screens/NewGameScreen.cpp)
- [game/app/GameApplication.cpp](/home/pjasicek/github/OpenYAMM/game/app/GameApplication.cpp)
- [game/party/Party.h](/home/pjasicek/github/OpenYAMM/game/party/Party.h)
- [game/party/Party.cpp](/home/pjasicek/github/OpenYAMM/game/party/Party.cpp)
- [game/tables/CharacterDollTable.h](/home/pjasicek/github/OpenYAMM/game/tables/CharacterDollTable.h)
- [game/tables/CharacterDollTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/CharacterDollTable.cpp)

Potential audio touchpoints:

- `game/audio/GameAudioSystem.*`

## Suggested Implementation Order

1. Add creation race-stat data and loader.
2. Add pure rules/helpers for candidate, stat, and skill resolution.
3. Refactor `NewGameScreen` from roster-list mode into creation-state mode.
4. Implement stat editing and pool accounting.
5. Implement skill selection and coloring.
6. Implement preview panel composition.
7. Add voice preview.
8. Add fresh single-character game start path.
9. Add diagnostics and edge-case cleanup.

## Verification Checklist

### Data and UI

- portrait switching updates class, race, preview, stats, and skills
- voice switching changes voice only
- default voice button restores the candidate default voice
- stat colors switch correctly between white/red/green
- stat min/max rules are enforced
- race-specific step rules work in both directions
- optional skill limit of 2 is enforced
- clicking a selected blue skill unselects it

### Start game

- `OK` creates a fresh game with one member
- party starts with `200` gold
- party starts with `5` food
- map is Dagger Wound Island
- start position is correct
- time/year is reset to default epoch
- no previous qbits or save-state carry over

### Regression checks

- existing load game still works
- existing quickstart/debug startup still works
- main menu navigation still works

## Summary

The major implementation risks are not rendering. They are:

- selecting the correct subset of creation candidates
- introducing a proper race-stat creation table
- separating creation-state editing from live `Character` runtime data
- adding a clean fresh-session start path that does not reuse the current roster-seeding logic

If those are solved cleanly first, the rest of the feature is straightforward UI work.

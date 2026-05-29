# Service House Implementation Plan

Date: 2026-03-28

Scope:
- Service houses only.
- Adventurer's Inn is explicitly out of scope here.
- This is an execution plan for follow-up implementation prompts.

Primary references:
- OpenYAMM current service runtime:
  - [game/gameplay/HouseInteraction.cpp](/home/pjasicek/github/OpenYAMM/game/gameplay/HouseInteraction.cpp)
  - [game/events/EventDialogContent.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventDialogContent.cpp)
  - [game/tables/HouseTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/HouseTable.cpp)
- MM8 house data:
  - [assets_dev/Data/HOUSE_DATA.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/HOUSE_DATA.txt)
  - [assets_dev/Data/HOUSE_ANIMATIONS.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/HOUSE_ANIMATIONS.txt)
- OE behavior reference:
  - [reference/OpenEnroth-git/src/Engine/PriceCalculator.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/PriceCalculator.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Houses/Shops.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Shops.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Houses/MagicGuild.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/MagicGuild.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Houses/Transport.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Transport.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Houses/Temple.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Temple.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Houses/Tavern.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Tavern.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Houses/Bank.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Bank.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Houses/Training.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Training.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Houses/TownHall.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/TownHall.cpp)

## 1. Current OpenYAMM Baseline

Implemented now:
- Temple:
  - heal
  - donate
  - learn skills
- Tavern:
  - rent room
  - buy food
  - learn skills
  - Arcomage submenu shell only
- Training:
  - train active member
  - learn skills
- Bank:
  - deposit all
  - withdraw all
- Shop:
  - shell only
- Guild:
  - shell only
  - learn skills only

Recognized in dialog presentation but not backed by service logic:
- Stables
- Boats
- Town Hall

## 2. Service Types In MM8 Data

The relevant service-house types in [HOUSE_DATA.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/HOUSE_DATA.txt) are:
- Weapon Shop
- Armor Shop
- Magic Shop
- Alchemist
- Temple
- Bank
- Tavern
- Training
- Spell Shop
- Elemental Guild
- Self Guild
- Light Guild
- Dark Guild
- Stables
- Boats
- Town Hall

Important distinction:
- `Magic Shop` in the data is an item shop.
- Spellbook-selling service is handled by `Spell Shop` and the guild house types.

## 3. Shared Implementation Principles

1. Keep service-house visuals data-driven.
   - House animation/video stem stays driven by house data.
   - Do not add a pile of new service YAML files.
   - Extend the existing house/dialogue HUD layout with the minimum extra elements needed.
   - For buy UI, the only expected new art element is the reusable shop buy overlay frame.
   - Buy/stock overlays should still be driven by YAML and house data, not hardcoded in C++.
2. Reuse the existing nested inventory overlay for shop service actions.
   - Sell
   - Identify
   - Repair
3. Move pricing and stock logic into shared backend helpers.
   - Do not scatter formulas across the UI code.
4. Persist generated house stock in party/runtime state.
   - Required for OE parity.
5. Treat service UI and service logic separately.
   - UI chooses target and action.
   - Backend validates item/funds/skill/restrictions and applies results.

## 4. Shared Foundation Work

These tasks should be done before starting the specific service flows.

### 4.1 Add house-service backend helpers

Add a new shared service helper layer, for example:
- [game/gameplay/HouseServiceRuntime.h](/home/pjasicek/github/OpenYAMM/game/gameplay/HouseServiceRuntime.h)
- [game/gameplay/HouseServiceRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/gameplay/HouseServiceRuntime.cpp)

Responsibilities:
- house service classification
- item family compatibility checks per house type
- price calculations
- generated shop/guild stock
- service action results
- merchant phrase/status text selection

### 4.2 Add persistent stock state

OpenYAMM needs party-level or save-level runtime state for:
- shop standard stock
- shop special stock
- guild spellbook stock
- next refresh time for each shop/guild
- shop ban time if we later match OE stealing/banned behavior

Suggested location:
- [game/party/Party.h](/home/pjasicek/github/OpenYAMM/game/party/Party.h)
- [game/party/Party.cpp](/home/pjasicek/github/OpenYAMM/game/party/Party.cpp)

### 4.3 Add price calculator parity helpers

Implement OE-matching formulas in a reusable place, not in UI code.

Needed formulas from OE:
- buy:
  - `applyMerchantDiscount(realValue * priceMultiplier)`
  - minimum real item value
- sell:
  - `realValue / (priceMultiplier + 2.0) + realValue * merchant / 100`
  - clamp to `[1, realValue]`
  - broken item sells for `1`
- identify:
  - base `priceMultiplier * 50`
  - merchant discount
  - minimum one third of base
- repair:
  - base `realValue / (6.0 - priceMultiplier)`
  - merchant discount
  - minimum one third of base
- skill learning:
  - guilds use house `priceMultiplier`
  - other houses use `skillPriceMultiplier`
- transport:
  - stable base `25`
  - boat base `50`
- tavern room:
  - `multiplier^2 / 10`
- tavern food:
  - `multiplier^3 / 100`
- temple healing:
  - condition-severity and days-passed formula
- training:
  - level * priceMultiplier * class tier, only if enough experience

Suggested files:
- [game/items/PriceCalculator.h](/home/pjasicek/github/OpenYAMM/game/items/PriceCalculator.h)
- [game/items/PriceCalculator.cpp](/home/pjasicek/github/OpenYAMM/game/items/PriceCalculator.cpp)

### 4.4 Extend existing HUD layout with minimal service overlay art

Requirements:
- overlay art drawn over the house animation area
- house animation pauses when buy UI is active
- background/image stems remain data-driven through layout entries
- buy items are rendered dynamically on top of the frame and must be inspectable
- avoid new dedicated service YAML files unless a later constraint makes it unavoidable

Plan:
- add one reusable shop buy overlay frame element to the existing house/dialogue layout
- keep slot positions temporary and simple at first
- let the backend own item generation and the UI only own slot placement

Do not hardcode asset names in C++.

### 4.5 Add shared right-frame text builder

OE shows action-dependent text on the right frame when hovering items.

OpenYAMM should add a shared helper that formats service text for:
- buy
- sell
- identify
- repair
- guild spellbook buy

That text should be built from:
- item
- house type
- action mode
- active member
- merchant skill
- house price multiplier
- current eligibility

## 5. Phase 1: Shops And Guilds

This is the highest-priority implementation phase.

### 5.1 Shop stock generation

Implement generated stock for:
- Weapon Shop
- Armor Shop
- Magic Shop
- Alchemist

Reference:
- [reference/OpenEnroth-git/src/GUI/UI/Houses/Shops.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Shops.cpp)

OE concept:
- standard stock and special stock use different treasure tiers
- shop type constrains item families
- layout slot count depends on shop type

OpenYAMM plan:
- Keep stock generation backend-driven.
- Keep slot layout YAML-driven.
- Do not couple slot count to item generation logic.

Initial slot counts for OpenYAMM:
- weapon shops: 6
- armor shops: 8 if we decide to follow OE exactly, otherwise let layout own the count
- magic/alchemy shops: let layout own the count
- guild spellbook shops: target `2 x 8` in the first MM8 implementation

Recommendation:
- Implement slot count from layout elements, not from hardcoded house type.

### 5.2 Shop buy flows

Implement:
- Buy Standard
- Buy Special

Needed behavior:
- hover shows merchant text/price on the right frame
- hovered buy items are inspectable with the normal inspect popup flow
- click buys item if enough gold and there is room
- if inventory is full:
  - check OE feedback
  - likely status text + face reaction + sound
- if not enough gold:
  - status text + sound + face reaction
- on success:
  - deduct gold
  - remove item from stock
  - move item to inventory
  - speech/sound/face reaction

### 5.3 Sell / identify / repair via nested inventory overlay

Reuse the existing inventory nested overlay built for chest/shop flows.

Implement service modes:
- `ShopSell`
- `ShopIdentify`
- `ShopRepair`

Rules:
- only allow items accepted by the house family
  - weapon shop: weapons
  - armor shop: armor/shields/helmets/etc.
  - alchemist: potions/reagents/recipes as appropriate
  - magic shop: magical item categories accepted by OE rules
- clicking an item in overlay performs the service

Action details:
- Sell:
  - remove item
  - add gold by OE formula
- Identify:
  - if already identified, show correct feedback
  - otherwise charge and identify
- Repair:
  - only broken items
  - charge and repair

UI details:
- status bar prompt changes by mode
- right frame text changes by mode

### 5.4 Guild spellbook buying

Implement OE-like guild spellbook service for:
- Spell Shop
- Elemental Guild
- Self Guild
- Light Guild
- Dark Guild

Reference:
- [reference/OpenEnroth-git/src/GUI/UI/Houses/MagicGuild.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/MagicGuild.cpp)

Needed behavior:
- school-specific spellbook pool
- mastery-limited stock
- stock refresh timer
- right-frame buy text
- purchase result feedback

Important note:
- MM8 combined guilds differ from OE MM7 guild layout.
- In MM8, interacting with these guilds is not gated behind membership.
- Use OE logic for mastery and stock generation shape, but keep MM8 school/grouping data-driven.

### 5.5 Shop/guild sounds and reactions

Wire service results to:
- merchant interaction sound
- gold change sound
- success/failure status text
- portrait face reaction
- character speech where appropriate

## 6. Phase 2: Transport

Implement:
- Stables
- Boats

Reference:
- [reference/OpenEnroth-git/src/GUI/UI/Houses/Transport.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Transport.cpp)

Needed data:
- schedules
- route destinations
- travel days
- arrival map and spawn point
- required qbits

Tasks:
1. Inspect current MM8 data tables for stable/boat schedules.
2. If original data is incomplete in OpenYAMM, add a supplemental TSV.
3. Implement route availability by weekday and qbit.
4. Implement price using OE formula.
5. Implement travel time modifiers from hirelings only if hirelings are already in runtime.
   - If hirelings are not in runtime yet, keep hook points and leave modifiers disabled.
6. Implement actual travel:
   - map change
   - party reposition
   - world time advance
   - party restore behavior if applicable
7. Add horse/boat sounds and speech reactions.

This phase is self-contained and should be done before Town Hall.

## 7. Phase 3: Temple Parity

Reference:
- [reference/OpenEnroth-git/src/GUI/UI/Houses/Temple.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Temple.cpp)
- [reference/OpenEnroth-git/src/Engine/PriceCalculator.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/PriceCalculator.cpp)

Tasks:
1. Replace current flat heal pricing with OE formula.
2. Implement healability based on:
   - worst condition
   - condition elapsed days
   - health/mana state
3. Implement zombie temple behavior.
4. Implement donation reputation effect.
5. Implement donation-triggered spell reward logic.
   - day-based counter
   - temple reward spells
6. Ensure temple sounds and face reactions match OE behavior.

## 8. Phase 4: Bank Input Parity

Reference:
- [reference/OpenEnroth-git/src/GUI/UI/Houses/Bank.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Bank.cpp)

Tasks:
1. Replace `deposit all` / `withdraw all` with typed amount flow.
2. Input prompt should appear in the status text area, not a separate overlay, unless that proves too awkward.
3. Use OE wording closely:
   - deposit
   - withdraw
   - balance
   - how much
4. Clamp entered amount by available carried/banked gold.
5. Play correct sounds and face reactions.

## 9. Phase 5: Training Parity Cleanup

Reference:
- [reference/OpenEnroth-git/src/GUI/UI/Houses/Training.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Training.cpp)

Current OpenYAMM training exists, but needs parity fixes:
- exp eligibility
- correct price formula
- correct max-level restrictions
- correct fail text
- correct time advance after training milestone
- level-up feedback text/sound

Tasks:
1. Move training pricing to shared price calculator.
2. Gate training on required experience for next level.
3. Replace simplified fail cases with OE-like text.
4. Match training hall max-level restrictions from data or supplemental table.
5. Confirm whether MM8 data already contains all max levels.
   - If not, add a supplemental table instead of hardcoding.

## 10. Phase 6: Tavern Arcomage

Reference:
- [reference/OpenEnroth-git/src/GUI/UI/Houses/Tavern.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/Tavern.cpp)
- [reference/OpenEnroth-git/src/Arcomage/Arcomage.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Arcomage/Arcomage.cpp)
- [assets_dev/Data/NPC_TOPIC_TEXT.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/NPC_TOPIC_TEXT.txt)
- [reference/OpenEnroth-git/src/Engine/Data/HouseEnumFunctions.h](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Data/HouseEnumFunctions.h)

Tasks:
1. Parse the tavern-specific Arcomage rule texts from data.
   - The generic rules text is in topic `136`.
   - The victory-condition texts are already present in data as topics `137..149`.
   - OE maps taverns to victory-condition topics with `arcomageTopicForTavern(...)`.
2. Convert those texts into structured rules:
   - starting tower
   - starting wall
   - tower-height win target
   - resource win target
   - tower destruction is always a valid win condition
3. Store the parsed rules in runtime data instead of hardcoding per tavern values.
4. Add proper tavern Arcomage menu flow:
   - Rules
   - Victory Conditions
   - Play
5. Integrate the actual Arcomage game.
6. Persist per-tavern wins.
7. Add Arcomage champion progression if MM8 data supports it.

This phase is large and should be deferred until shops/guilds/transport are stable.

## 11. Phase 7: Town Hall

Reference:
- [reference/OpenEnroth-git/src/GUI/UI/Houses/TownHall.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Houses/TownHall.cpp)

Lower priority for now.

Tasks:
1. Add Town Hall to service runtime classification.
2. Implement bounty hunt board:
   - monthly generation
   - target monster
   - reward claim
3. Implement fine payment typed input.
4. Add sounds/reactions/status text.

## 12. Suggested Execution Order

Recommended order for follow-up implementation prompts:

1. Shared price calculator and persistent stock state.
2. Shop buy flows.
3. Shop sell/identify/repair via nested inventory overlay.
4. Guild spellbook buying.
5. Transport.
6. Temple parity.
7. Bank typed input parity.
8. Training parity cleanup.
9. Town Hall.
10. Arcomage.

## 13. Recommended Prompt Breakdown

To keep patches reviewable, execute in these prompt-sized slices:

1. "Implement shared house price calculator, stock persistence, and shop standard/special buy for weapon/armor/magic/alchemy shops."
2. "Implement shop nested-inventory service modes for sell/identify/repair with OE-style pricing and right-frame text."
3. "Implement guild/spell shop spellbook buying with generated stock and refresh timers, without membership gating."
4. "Implement stables and boats using OE-like schedules, pricing, time advance, and travel."
5. "Implement temple OE parity: heal pricing, zombie rules, donation effects, and sounds."
6. "Implement bank typed deposit/withdraw UI and logic in the status bar."
7. "Bring training to OE parity."
8. "Implement Town Hall bounty hunt and pay fine."
9. "Implement full Arcomage by parsing tavern-specific rule texts from data into structured win conditions."

## 14. Acceptance Criteria

Before closing each phase:
- build succeeds
- relevant headless regressions are added
- at least one live interaction path is manually tested
- no hardcoded house art names remain in C++ when YAML/data can own them
- stock/pricing logic lives in shared backend, not duplicated across UI paths

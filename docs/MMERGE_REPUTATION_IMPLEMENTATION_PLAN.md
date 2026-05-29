# Reputation Implementation Plan

This is the implementation inventory for reproducing OE/MMerge reputation behavior in OpenYAMM. Reputation is a
signed "badness" value: lower values are better, higher values are worse. In EVT terms this means `Add Reputation`
worsens reputation and `Subtract Reputation` improves it.

## Source References

OpenEnroth:

- Storage sign: `reference/OpenEnroth-git/src/Engine/Graphics/LocationInfo.h:7`.
- Effective party reputation: `reference/OpenEnroth-git/src/Engine/Party.cpp:831`.
- Fame formula: `reference/OpenEnroth-git/src/Engine/Party.cpp:374`.
- Reputation labels: `reference/OpenEnroth-git/src/GUI/UI/UIGame.cpp:1688`.
- EVT compare/set/add/subtract semantics:
  - compare: `reference/OpenEnroth-git/src/Engine/Objects/Character.cpp:3921`
  - set cap: `reference/OpenEnroth-git/src/Engine/Objects/Character.cpp:4358`
  - add cap: `reference/OpenEnroth-git/src/Engine/Objects/Character.cpp:4941`
  - subtract cap: `reference/OpenEnroth-git/src/Engine/Objects/Character.cpp:5635`
- Temple donation: `reference/OpenEnroth-git/src/GUI/UI/Houses/Temple.cpp:76`.
- Friendly/peasant kill penalty and fines: `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp:1090`.
- Actor stealing: `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp:1231` and
  `reference/OpenEnroth-git/src/Engine/Objects/Character.cpp:1195`.
- Shop stealing: `reference/OpenEnroth-git/src/GUI/UI/Houses/Shops.cpp:1094` and
  `reference/OpenEnroth-git/src/GUI/UI/Houses/Shops.cpp:1143`.
- Merchant pricing: `reference/OpenEnroth-git/src/Engine/PriceCalculator.cpp:143`.
- Throne-room jail/fine handling: `reference/OpenEnroth-git/src/GUI/UI/UIHouses.cpp:348`.
- Dark sacrifice reputation penalty: `reference/OpenEnroth-git/src/Engine/Spells/CastSpellInfo.cpp:2810`.
- UI display and text substitution:
  - quick reference: `reference/OpenEnroth-git/src/GUI/UI/UIQuickReference.cpp:134`
  - `%11/%12`: `reference/OpenEnroth-git/src/GUI/GUIWindow.cpp:844`.
- NPC profession modifiers: `reference/OpenEnroth-git/src/Engine/Objects/NPCEnums.h:73`.

MMerge:

- Continent settings parse: `reference/mmmerge/Scripts/General/MenuChooseContinent.lua:35`.
- Per-continent reputation/fame storage: `reference/mmmerge/Scripts/Global/Reputation.lua:2`.
- Store/restore active continent reputation: `reference/mmmerge/Scripts/Global/Reputation.lua:148` and
  `reference/mmmerge/Scripts/Global/Reputation.lua:279`.
- Shop/guard state changes: `reference/mmmerge/Scripts/Global/Reputation.lua:96`,
  `reference/mmmerge/Scripts/Global/Reputation.lua:112`, `reference/mmmerge/Scripts/Global/Reputation.lua:298`.
- Peasant kill/bounty handling: `reference/mmmerge/Scripts/Global/Reputation.lua:175`.
- Donation surcharge and shop ban behavior: `reference/mmmerge/Scripts/Global/Reputation.lua:236`.
- Baa temple donation penalty: `reference/mmmerge/Scripts/Global/StdQuestsFunctions.lua:79`.
- BTB/NPC reputation/fame gates:
  - gate: `reference/mmmerge/Scripts/General/NPCFollowers.lua:521`
  - greet/text substitution: `reference/mmmerge/Scripts/General/NPCNewsTopics.lua:456`.
- MMerge stealing hooks:
  - shop/guild stealing: `reference/mmmerge/Scripts/General/Stealing.lua:48`
  - monster/NPC stealing: `reference/mmmerge/Scripts/General/Stealing.lua:182`.
- Bounty-hunt reward reputation: `reference/mmmerge/Scripts/General/BountyHunt.lua:43`.
- MMerge EVT reputation bounds patches: `reference/mmmerge/Scripts/General/ExtEvt.lua:155` and
  `reference/mmmerge/Scripts/General/ExtEvt.lua:206`.

Current OpenYAMM:

- World runtime storage API: `game/gameplay/GameplayRuntimeInterfaces.h:393`.
- Outdoor storage: `game/outdoor/OutdoorWorldRuntime.cpp:5819`.
- Indoor storage: `game/indoor/IndoorWorldRuntime.cpp:6308`.
- Save/map delta storage: `game/maps/MapDeltaData.h:18`, `game/maps/SaveGame.cpp:1933`.
- Temple donation consumer: `game/gameplay/HouseInteraction.cpp:1099`.
- Random NPC BTB gate: `game/events/EventDialogContent.cpp:227`.
- Merged BTB/continent-table fields: `game/tables/MergedBaseTables.h:67` and
  `game/tables/MergedBaseTables.h:248`.
- Current gap: `EvtVariable::ReputationInCurrentLocation` is classified as party state and falls through to generic
  `Party::eventVariables`; see `game/events/EventRuntime.cpp:1998`, `game/events/EventRuntime.cpp:2429`,
  `game/events/EventRuntime.cpp:3094`, `game/events/EventRuntime.cpp:3603`, `game/events/EventRuntime.cpp:4019`.

## OE Semantics Inventory

### Stored vs Effective Reputation

- Stored reputation lives in the current location DDM/DLV info.
- Negative is good, positive is bad.
- Effective party reputation is `storedLocationReputation + hirelingPenalty`.
- OE hireling penalties are `+5` each for Pirate, Burglar, Gypsy, Duper, and Fallen Wizard.
- OE does not include Bard in `GetPartyReputation()` even though some profession text implies a reputation benefit.
  For parity, implement OE behavior first and keep Bard out unless original-game testing proves otherwise.
- Fame is independent and is total party experience divided by 1000.

### Reputation Levels

Use the OE/MMerge thresholds:

| Effective reputation | Label |
| --- | --- |
| `>= 25` | Hated / Notorious |
| `6..24` | Unfriendly |
| `-5..5` | Neutral |
| `-24..-6` | Friendly |
| `<= -25` | Liked / Saintly |

MMerge text helpers use equivalent cutoffs: `> 24`, `> 5`, `> -6`, `> -25`, otherwise saintly.

### EVT Semantics

- `Cmp Reputation, X`: true when stored current-location reputation is `>= X`.
- `Set Reputation, X`: sets stored reputation and caps the high side to `10000`.
- `Add Reputation, X`: increases stored reputation, worsening it, capped to `10000`.
- `Subtract Reputation, X`: decreases stored reputation, improving it, capped to `-10000`.
- MMerge patches MM6-style `ReputationIs` to use the same current reputation storage and bounds.

### Reputation Gain/Loss Sources

- Temple donation:
  - If party can pay, decrease stored reputation by `1` while stored reputation is greater than `-5`.
  - This means normal temples can improve reputation only down to `-5`.
  - Donation buff thresholds use stored reputation: `<= -5`, `<= -10`, `<= -15`, `<= -20`, `<= -25`.
- Scripted quest rewards/penalties:
  - MM6 scripts use `ReputationIs`; MM7/MM8 use `Reputation`.
  - Our exported Lua already has many `AddValue(ReputationInCurrentLocation, ...)` and
    `SubtractValue(ReputationInCurrentLocation, ...)` calls. These must affect the same storage as the gameplay
    systems.
- Killing friendly peasants/NPCs:
  - Applies a fine based on base map stealing fine, killed actor level, and effective party reputation.
  - Increments stored reputation by `1`, capped at `10000`.
  - OE exempts evil parties in Bracada/Celeste and good parties in Deyja/Pit.
  - Adds the fine award if a fine exists.
- Stealing:
  - OE uses effective party reputation as part of the stealing difficulty/fine formula.
  - Actor/NPC stealing increments stored reputation by `1` immediately through `v6->reputation++`.
  - Shop stealing applies `+1` or `+2` stored reputation depending on result, sets a shop ban on caught theft, and adds
    fine when caught.
  - MMerge rewrites stealing more broadly: shop/guild success still adds `+1`, caught failure adds `+2`, uncaught
    failure adds `+1`; monster/NPC stealing drops reputation only for guards or peasant-creed monsters.
- Dark sacrifice:
  - Sacrificing a hireling heals/refills party and adds `+15` bad reputation, capped to `10000`.
- Bounty hunt:
  - OE has town-hall bounty/fine systems, but MMerge adds explicit reputation improvement for bounty rewards.
  - MMerge `BountyHuntFunctions.AddBountyHuntReward` subtracts `ceil(gold / 2000)` from reputation.
  - MMerge also improves reputation on killing the active bounty target, bounded around `-20`, and nudges continent
    reputation toward good.
- Baa temple donation:
  - MMerge worsens reputation by `+2` on Baa temple donations when the effective reputation is below `9`.

### Effects

- Merchant prices:
  - Effective party reputation is subtracted from the merchant discount formula.
  - Bad reputation worsens prices; good reputation improves them.
  - Grandmaster Merchant ignores this path and returns 100.
- Temple buffs:
  - Donation spell list depends on stored reputation thresholds.
- Fines and jail:
  - Bad effective reputation raises fines for peasant kills/stealing.
  - Throne rooms send the party to jail if a fine exists, clear the fine, advance time, increment prison terms, and add
    the prison award.
- Random NPC / BTB:
  - Text tokens `%11` and `%12` need effective reputation labels.
  - MMerge gates random NPCs by NPC alignment, required reputation, and required fame.
  - Beg, Threat, and Bribe can temporarily unlock conversation and swap greetings.
- Continent-specific MMerge effects:
  - `UseRep` is derived from `RepGuards || RepShops || RepNPC`.
  - Only continents with `UseRep` get MMerge's per-continent store/restore behavior.
  - `RepGuards`: guards become hostile around terrible reputation. MMerge uses `>=25` on load and `>=20` after peasant
    kills.
  - `RepShops`: shops close/ban the party at terrible reputation; MMerge uses `>=25` on load and `>25` while clicking
    shop topics.
  - `RepNPC`: random NPC BTB gating is active.

## Current OpenYAMM Gaps

- Dark Sacrifice is not currently an active runtime action in the merged spell table because spell id `96` is Dark
  Grasp. Do not add a competing Sacrifice hook unless content exposes Sacrifice separately again.
- Fame exists in some systems, but BTB should consistently use the OE/MMerge fame formula and MMerge's continent-fame
  behavior where required.
- Exact jail/throne movie presentation and optional map-wide bounty spawn placement need follow-up if visual parity
  becomes important.

## Implementation Plan

### 1. Add a Shared Reputation API

Add a small gameplay-owned API, not world-specific ad hoc code:

- `storedCurrentLocationReputation()`
- `setStoredCurrentLocationReputation(value)`
- `addStoredCurrentLocationReputation(delta)`
- `effectivePartyReputation()`
- `reputationLabel(value)`
- `partyFame()`

Rules:

- Stored value clamps to `[-10000, 10000]`.
- Add/subtract semantics match OE exactly.
- Effective value adds `+5` for each hired Pirate, Burglar, Gypsy, Duper, and Fallen Wizard.
- Keep the active map's current reputation in the world runtime because DDM/DLV already owns that state.

### 2. Fix EVT Reputation Variables

Special-case `EvtVariable::ReputationInCurrentLocation` in get/set/add/subtract/compare paths:

- Reads come from `IGameplayWorldRuntime::currentLocationReputation()`.
- Set writes to `setCurrentLocationReputation(clamp(value))`.
- Add writes `clamp(current + value)`.
- Subtract writes `clamp(current - value)`.
- Compare uses `current >= value`.

This is the highest-priority fix because all generated quest reputation changes depend on it.

### 3. Add MMerge Continent Sync

Use `MergedContinentSettingEntry`:

- Define `useReputation = reputationAffectsGuards || reputationAffectsShops || reputationAffectsNpc`.
- Store per-continent base reputation in save/party state.
- On map leave and before save: if `useReputation`, store the active world's current reputation into that continent.
- On map load: if `useReputation`, initialize the active world's current reputation from the continent value.
- If `useReputation` is false, leave OE per-map DDM/DLV reputation behavior alone.

This mirrors MMerge and avoids forcing MM7/MM8 into a global reputation mode when their continent settings do not ask
for it.

### 4. Wire Gameplay Mutators

All gameplay reputation changes should call the shared API:

- Temple donate: improve down to `-5`, then calculate buff thresholds from stored reputation.
- Baa temple donate: add `+2` bad reputation under MMerge's conditions.
- Peasant/friendly kill:
  - Identify peasant/friendly via monster creed/hostility data.
  - Apply OE alignment exceptions.
  - Add fine using map base stealing fine, actor level, and effective reputation.
  - Add `+1` bad reputation.
  - Trigger guard/shop state checks where continent settings enable them.
- Shop theft:
  - Use effective reputation in stealing difficulty/fine.
  - Apply `+1`/`+2` reputation deltas and fine/shop ban behavior.
  - Preserve MMerge's longer configurable ban/fine behavior only if we intentionally choose MMerge over OE here.
- Actor/NPC theft:
  - Apply OE actor stealing recovery/status behavior.
  - For MMerge parity, only drop reputation for guards or peasant-creed monsters.
- Dark sacrifice: add `+15` bad reputation.
- Bounty rewards/targets: subtract reputation per MMerge reward formulas.

### 5. Wire Effects

- Merchant pricing must call `effectivePartyReputation()`.
- Quick reference UI must display `reputationLabel(effectivePartyReputation())` with good/bad coloring.
- Dialogue string expansion must implement `%11` as party reputation label and `%12` as the required NPC reputation
  label.
- Random NPC BTB gate must use MMerge logic:
  - skip gate if not random NPC, already hired/follower, already unlocked today, or continent does not affect NPC rep.
  - good NPC refuses bad reputation; evil NPC refuses too-good reputation.
  - required absolute reputation and required fame must be honored.
  - Beg/Threat/Bribe success should unlock the NPC for the day and choose correct greeting text.
- Guard hostility and shop closure/refusal use shared runtime state and should continue to respect continent settings
  where the current map load path supplies them.
- Town hall fine payment and throne sentence handling use the same fine state used by killing/stealing.

### 6. Data and Save

- Save:
  - active map reputation already round-trips.
  - add per-continent reputation map/array for MMerge `UseRep` continents.
  - no migration is needed for development saves.
- Data:
  - keep `continent_settings.txt` authoritative for `RepGuards`, `RepShops`, and `RepNPC`.
  - keep `npc_btb.txt` authoritative for BTB thresholds/text/personality behavior.
  - use map stats base stealing fine for fine formulas.
  - use monster bolster/source creed to identify peasant-creed targets in merged content.

### 7. Tests

Add focused tests before broad runtime testing:

- EVT `Set/Add/Subtract/Cmp ReputationInCurrentLocation` reads/writes world runtime reputation, not party event vars.
- Donation improves only to `-5` and applies correct spell thresholds.
- Effective reputation includes exactly the OE hireling modifiers.
- Reputation labels match the OE thresholds.
- Per-continent sync:
  - continent with `UseRep` stores/restores across map switches.
  - continent without `UseRep` keeps per-map behavior.
- Merchant pricing changes with reputation.
- Peasant kill adds fine and `+1` bad reputation, with alignment exceptions.
- Shop theft applies fine, ban, item stolen flag, and reputation deltas.
- Guard hostility and shop refusal/ban policy responds to terrible reputation.
- Throne sentence handling clears fines and increments prison terms without taking precedence over throne NPC dialogue
  when no fine is owed.
- BTB gate and `%11/%12` text substitution use effective reputation and fame.
- Baa temple donation adds `+2` bad reputation.
- Bounty reward subtracts reputation according to MMerge.

## Implementation Order

1. Done: fix EVT reputation routing and add tests.
2. Done: add effective reputation helper, labels, and hireling modifiers.
3. Done: route existing BTB checks and shop-exit rude handling through effective reputation.
4. Done: add per-continent MMerge sync behind `UseRep`.
5. Done: wire merchant pricing and BTB `%11/%12` text substitutions.
6. Done for current runtime scope: wire peasant kill reputation/fine mutation and shared stealing/fine appliers.
   - Shop/guild stock stealing and live indoor/outdoor actor stealing are wired through Ctrl-click actions and covered
     by unit tests where pure logic is practical.
   - Caught-theft house bans, terrible-reputation shop refusal, guard hostility propagation, town-hall fine payment,
     throne sentence handling, and bounty reward/kill state are wired.
   - Still pending only for exact visual parity: jail/throne movie presentation.
7. Done: wire MMerge-specific Baa donation and bounty reward result effects.
8. Pending: add headless gameplay regressions for representative MM6 Enroth, MM7 Antagarich, and MM8 Jadame maps.

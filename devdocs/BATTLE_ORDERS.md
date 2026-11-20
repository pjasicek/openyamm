# Battle orders

Each member's battle orders say what Attack does: F, the left mouse button, smart left click, and the acting member in
turn-based combat. The same in every ruleset (Standard and MAW). The design is the chosen layout A of the study
[combat_orders_20261108](../level_generation/ui/combat_orders_20261108/README.md) (2026-11-08), from a Discord request
(puzzleR1). The place condition and the [upkeep list](#upkeep) followed on 2026-11-12, from two more (heron, Tyrkys).
[Potions in the upkeep list](#potions), with a stock the Upkeep key can brew, followed on 2026-11-16 (the user, for MAW
and its solo runs: self-buff potions such as Champion's and Paladin's kept up and kept in stock).

## Rules

- **Orders.** Attack walks the member's orders top to bottom and does the first that holds and can be done now. There
  are at most sixteen (`BattleOrderLimit`). An order is one of three kinds:
  - a spell;
  - **Melee**: a blow, only with a target in the weapon's reach;
  - **Shoot**: the ranged weapon (bow, crossbow, wand, blaster, a dragon's breath), only with one;
  - **a talent** (a MAW solo run's learned active talent, [below](#talent-orders)).
- **Conditions.** Each order has optional conditions, and all of them must hold:
  - **Target distance**: a range in game units (0–5120; a maximum of 5120 means any). The presets are *in melee reach*
    (0–407) and *beyond melee reach* (407 up). 407 stands for the blow's exact reach, 407.2 units. A minimum is
    exclusive and a maximum inclusive, so the two presets meet exactly. An order with a distance fails when there is no
    target.
  - **An ally's HP is below** N % (10–90): the lowest HP share among the members a heal can still reach (not dead,
    eradicated or stoned). The row's *own* chip makes it the acting member's own HP instead (`BattleOrder::ownHealth`,
    OY-645; save version 183), for a drink or a self-heal before the attack.
  - **Keep SP after casting** at least N % (0–80): spells only, against the member's reachable maximum.
  - **Place**: anywhere, indoors or outdoors, as the spells tell the two apart (a map open to the sky is outdoors,
    `IGameplayWorldRuntime::isOpenAirMap`). For a spell that works in both but is worth casting in one: Sparks
    indoors, another spell outdoors.
- **Automatic checks.** A spell order is also passed over when:
  - the member does not know it, or cannot pay for it (mana, or the rules' other means: an Assassin's combo points);
  - its party buff is already up (`PartySpellDescriptor::partyBuff`);
  - the place or the hour forbids it (`PartySpellSystem::worldAllowsSpell`: outdoor-only spells indoors, the
    indoor-only ones outdoors, Sunray at night; Sunray indoors where the rules allow it);
  - the cast finds no target (`AttackCastDisposition::NoTarget`). For example, a Heal with nobody hurt, or a cure with
    nobody affected (quick-cast targeting, `quickCastCharacterTarget`).
- **Switching an order off** skips it and keeps its settings.
- **Fallback.** When no order applies, the member does one of two things:
  - **the weapon** (the default): a blow in reach, the ranged weapon beyond, as before battle orders;
  - **hold**: nothing.
- **Hold in real time.** The holder spends no recovery and stays ready. The press goes to the next ready combatant,
  each tried once per press (`GameplayActionController::executePartyAttack`). When everyone ready holds, nothing
  happens: the selection stays with the first holder, and a fresh press says "{member} holds" (not each repeat of a
  held button).
- **Hold in turn-based.** The queue waits for the member at its front, so a holder passes: the Pass key's action and
  cost, the member's melee recovery (`GameplayScreenRuntime::passTurnBasedTurn`).
- **Cost of holding the button.** A held Attack repeats after 0.5 s, then every 0.14 s, not every frame. Each repeat
  checks at most the party's orders. A holding member keeps `hasReadyMember` true, but that was already true while
  anyone could act (`Party::hasSelectableMemberInGameplay` ignores recovery), so the fast repeat's "a member became
  ready" trigger is unchanged.
- **Quick keys.** Quick Cast and Quick Spell 1–4 keep their single spells and take no conditions.
- **MAW.**
  - The Elementalist's rotation turns the order that names the cast spell, where it used to turn the attack spell.
  - The power report reads the first spell order.

## Talent orders

Built 2026-11-16 at the user's request: in a MAW solo run the orders also take the character's active talents (Power
Shot, Multishot, Cleave, Charge, Blink, Binding Circle, Shield Wall, Spell Surge).

- **When.** The order is used where it stands in the list when its conditions hold and the talent can act now: learned,
  off cooldown, and with what it needs (a target in reach for Cleave or Charge, the bow drawn for a bow talent). Else
  it is passed over like a spell without a target. Never in turn-based combat (the talents are real-time only), so
  there the orders below it decide.
- **Where it lands.** The talent is used where the Attack lands (`PartyAttackConfig::useTalentOrder`, called from
  the order walk in `GameplayActionController::executePartyAttack`; `useSoloTalent` with a `TalentOrderUse`). With the
  arms shown, the Attack's ordinary swing or bow draw plays and the talent strikes at its blow or release, with no
  clip of its own after it; the clip's time comes off the recovery as for any blow. A ready talent order above the
  first spell order keeps the swing (no cast clip at the press). It starts its cooldown and pays its recovery as when
  used from the action bar.
- **Conditions.** Target distance, HP and place, as for the weapon orders; "Keep SP" is for spells only. Its line says
  "when ready", or "not learned" (a talent taken back).
- **In the window.** The palette lists the learned active talents after Melee and Shoot (their talent icons; hovering
  one shows its effect at the current rank). Copy from another member skips a talent the member has not learned.
- **Data.** `BattleOrderKind::Talent` with `BattleOrder::talentId` (the talents.yml id), saved from version 189
  (`SaveVersionTalentOrders`). Scenarios: `{talent: <id>}` in `battle_orders`
  (`tests/scenarios/rulesets/maw_solo_talent_battle_order.yml`).
- **Not done.** A press with the arms shown that ends in a talent also strikes Sweeping Blows' extra blows first, as
  any Attack whose target is in reach does (also when a spell order casts).

## Upkeep

Each member also has an upkeep list: the buffs, heals, cures and buff potions they keep up outside the fight. It is the
same orders in a second list (`Character::upkeepOrders`, at most sixteen as well), spells and [potions](#potions), with
its own key.

- **The Upkeep key** (`upkeep`, F11 by default; `GameplayActionController::executePartyUpkeep`):
  - A ready member casts the first spell of their list that is on, known, due, allowed here and paid for. The cast
    is an ordinary one: its mana, its recovery, its chance to fail.
  - In real time the active member is tried first, then the other ready members, and there is one cast per press. The
    caster becomes the active member and the selection moves on, as after an attack.
  - A held key repeats as Attack does (after 0.5 s, then every 0.14 s), so holding it goes through the lists as the
    members come ready.
  - In turn-based mode only the member whose turn it is casts, and the cast is that turn. In the movement phase the
    press ends the phase, as Quick Cast does.
  - A fresh press that casts nothing says why: nothing set, nobody ready, not enough spell points for a due
    spell, a due potion nobody carries, or nothing to cast.
- **Upkeep spells** (`PartySpellSystem::isUpkeepSpell`):
  - the party buffs, but not Invisibility (any other cast ends it);
  - the buffs on members: Bless, Preservation, Regeneration, Hammerhands, Pain Reflection, Glamour, Mistform;
  - the heals, cures and revivals a quick cast aims by itself, Power Cure and Awaken.
- **When a spell is due** (`PartySpellSystem::upkeepNeed`):
  - A buff: it is gone, or, with **Renew when less is left than** N game minutes (5–120, 30 for a new order), less
    than that is left. A buff is never renewed before half of what this member's cast gives has run
    (`upkeepBuffDue`): a cast never shortens a buff, so a ten-minute buff would otherwise be cast at every press.
  - A spell of several party buffs (Day of Protection, Hour of Power, Traveler's Boon, Levitate): any of them is
    due. Hour of Power's Haste is not counted, since a weak member stops it.
  - A buff on members: any member who can still be healed lacks it. The one with the least left is the target; the
    spell's party-wide masteries ignore the target.
  - A heal, cure or revival: the quick cast's choice finds a member. Power Cure: someone is wounded. Awaken: someone
    sleeps.
  - Never a spell the rules cast as an aura (MAW), which a second press would switch off again. The list does not
    take those.
- **Conditions.** An ally's HP, the SP kept and the place apply as for an attack order; the target distance does not.
- **In the window.** The On Attack / Upkeep switch over the rows shows the list. The palette then offers only upkeep
  spells, and the Add chips put in what the list lacks:
  - **Buffs**: the member's lasting buffs, the strongest first, without those a known wider spell gives (Day of
    Protection's resistances, Hour of Power's Heroism), Torch Light indoors only;
  - **Healing**: Heal for an ally below 90 % HP, then the cures;
  - **Copy from...**: another member's list, without what this member cannot cast.
  - While the upkeep list shows, the window's bottom strip is the **Upkeep key** in place of the quick keys: a click
    on its box, then a key, binds it (Escape keeps the old one, a right click clears it). A key another action has
    is refused, since one press would then do both; mouse buttons and the wheel are bound in Settings. The binding is
    the settings' `upkeep`, one for the whole party.
- The spellbook's spell menu adds a spell to the upkeep list, and the Quick Reference's pointed cell lists it.
- Android has no touch control for the key yet. A solo run's action bar takes an **Upkeep** slot (in the selector's
  Actions), which acts as the key held (`ActionBarSlotKind::Upkeep`).

## Potions

A potion with a timed effect can be an upkeep entry (`BattleOrderKind::Potion`; `game/items/PotionUpkeep.h`): MAW's
aura potions (Haste, Bless, Champion's, Paladin's, the resistances, Divine Blessing...), the immunities, Meditation,
Regeneration and Standard's buff potions. Restoring and curing potions are not entries: they are not kept up.

- **When it is drunk** (`PotionUpkeep::potionDue`): the press works as for a spell. The member's entry is tried in its
  place in the list, one drink per press; a held key goes on through the lists. One of the potion's timed effects must
  be gone, or have less left than the entry's renew time (and half of what the drink gives, `upkeepBuffDue`). Two
  effects never count as due:
  - an effect still running stronger than the bottle gives (a drink would replace it by a weaker one: a Haste potion
    while Champion's Haste of a higher power runs), and
  - under MAW, an aura the party's own aura outdoes (`PotionRules::potionAuraCounts`: only the stronger counts), or
    under Standard a buff its condition stops (Haste while weak).
- **Which bottle** (`PotionUpkeep::orderBottle`): the strongest, or the weakest, as the entry says; from the member's
  bags first, then the others', as a quick item slot. A drink is an ordinary one: its recovery where the rules charge
  it (MAW: near monsters only, so out of a fight a held key drinks one due potion after another).
- **Stock** (`BattleOrder::stockDrinks`, 0–50 drinks, two bottles' worth for a new entry): the party keeps that many
  drinks. Several members' entries of one potion add up; the highest brew power counts (`PotionUpkeep::stockTargets`).
  Only bottles at least at the brew power count.
- **Brew power** (`brewPower`, off: the strongest the ingredients make): every brewed bottle has at least this power,
  mixed from the weakest ingredients that reach it, so the best reagents stay for later (the planner's aim,
  `AlchemyChainPlanner::plan`). A power the ingredients cannot reach brews nothing and says so.
- **Restock** (`PotionUpkeep::restock`, `GameplayItemService::restockUpkeepPotions`): the short potions, in the
  lists' order, each from what the party carries through `AlchemyChainPlanner`, which mixes only known recipes the
  alchemist cannot fail. Every stocked potion's counted bottles are held back from the mixes (the planner's
  `reserved` copies), so Champion's is never brewed out of the stocked Haste. The status line names what was brewed
  and the first potion still short, with why (no bottle, a missing reagent, an unknown step, too little Alchemy, a
  power out of reach). It keeps the Workbench's *keep mixed potions* setting. An empty bottle without room goes to the
  cursor, as at the Workbench.
- **Auto-brew** (`GameSettings::upkeepAutoBrew`, `upkeep_auto_brew`, off by default): a fresh press of the Upkeep key
  restocks first, so a potion that ran out is brewed and drunk on the same press. It is the tick beside the Upkeep key
  in the window, the popup's Auto-brew button and Settings' *Upkeep brews its potions* (Alchemy group). A brew message
  stays in the status line over the drink's.
- **Messages.** A due potion nobody carries says *Upkeep: no {potion} left* when nothing else was used.

Where it is set:

- **Battle Orders window**, upkeep list: the palette lists the upkeep potions the party carries or knows a recipe for
  (after the spells, with their carried drinks when pointed at); the **Potions** chip adds every one the party carries.
  A potion row shows its carried drinks (red under the stock). Its editor: renew time, *Keep in stock* (drinks, with
  the carried count), *Brew at power at least*, *Drink* strongest or weakest, and the place. Copy from another member
  copies the potions as they are.
- **Potion popup** (the basebar's potion button): its **Upkeep** button shows the chosen member's upkeep potions
  instead of what the party carries: carried / kept drinks, the time left or *due now*, - and + chips (one bottle less
  or more in stock), a click drinks one now. The footer has **Brew now**, the **Auto-brew** tick and **Battle Orders**
  (the window on that member's upkeep list). In the Potions list, a right click's strip has an **Upkeep** chip that
  puts the potion in the member's list or takes it out; a potion in the list carries a **U** pin.

## Data

- `game/party/BattleOrders.h`: `BattleOrder`, `BattleOrderFallback`, `battleOrderConditionsHold`, `upkeepBuffDue`
  and `setAttackSpell`.
- `Character::battleOrders` and `battleOrderFallback` replace `attackSpellName`. They are saved from version 167
  (`SaveVersionBattleOrders`).
- An order's place and renew time, and `Character::upkeepOrders`, are saved from version 176
  (`SaveVersionUpkeepOrders`); an older save has every order anywhere and no upkeep list.
- A potion entry's item, bottle, stock and brew power are saved from version 191 (`SaveVersionPotionUpkeep`); the
  action bar's Upkeep slot is a new slot kind there too.
- An older save's attack spell becomes one unconditional order. A spell for a member (Heal, the cures, the revivals)
  gets the hold fallback, because the attack spell did nothing when nobody needed it (OY-190).
- `party_attack`'s `attack_spell` in scenarios makes that spell the member's only order for the step, with the weapon
  as fallback.

## Interface

- **Battle Orders window** (`game/ui/GameplayBattleOrders.cpp`), over the spellbook (`SpellbookState::battleOrders`):
  - It has member tabs, the orders with their on/off ticks and move and remove buttons, and the fallback switch.
  - A list longer than its rows (six attack orders over the fallback, eight upkeep spells) scrolls: the wheel over
    the rows, or the bar beside them. Adding or moving an order scrolls to it.
  - The editor sets the selected order's conditions with sliders, and the place with three chips. The distance slider
    gives its first half to 0–1024 units.
  - The palette lists the member's spells and the two weapon orders; a click adds an order. Its search field filters
    by name; while it has focus, keys are text, not hotkeys (`GameplayUiController::spellbookSearchActive`), Escape
    clears it and a right click empties it.
  - The quick keys: click one, then a spell; a right click clears it.
  - There are starting plans and Copy from another member:
    - Fighter: no orders;
    - Archer: shoot beyond melee reach;
    - Caster: the strongest known single-target missile;
    - Healer: Heal below 50 % and the cures, otherwise hold.
  - The frame is the Settings frame drawn as a nine-slice (`GameplayObsidianPainter::sliced`), so its corners stay
    sharp at any size.
- **Opening it.**
  - The spellbook's left column has, from the bottom up, Close, Attack Spell, Quick Cast and the Battle Orders button
    (`SpellbookBattleOrdersButton`). The Quick Spell 1–4 buttons are gone (the window and the spell menu set them).
  - The Battle Orders key (`battle_orders`, unbound by default) opens the book with the window and closes both
    together.
- **Quick setup.** For players who want no plan, the spellbook's Quick Cast and Attack Spell buttons work as before
  battle orders: a click sets the selected spell, and the same spell again, or no spell selected, clears it.
  - Quick Cast sets the member's Quick Cast key.
  - Attack Spell makes the spell the member's only order, replacing any plan, with the fallback an older save's attack
    spell gets (`setAttackSpell`: hold for a spell for a member, otherwise the weapon). Clearing it leaves no orders
    and the weapon.
- **Spell menu.** A quick right click (released within 300 ms) on a spell in the book opens a short menu. It sets Quick
  Cast or a Quick Spell key (or clears one), adds the spell to the attack orders or to the upkeep list, or opens the
  window. The right button shows the spell's description as soon as it goes down, as before the menu existed (a
  Discord report on 2026-11-15 found the 300 ms wait for it a delay); a quick release then swaps it for the menu.
- **Quick Reference.**
  - An Orders row under QSpell shows each member's orders that are on, as small icons, with the fallback's mark last;
    of more than six, the first five and how many follow. Pointing at a member's cell lists the first ten orders
    with their conditions, the upkeep spells and the quick keys.
  - The rows below Name are 20 units apart instead of 21.67, so the table keeps its height. The background
    (`obsidian_quickref_surface`) has one more band.

## Tests

- **Unit** (`tests/BattleOrdersTests.cpp`): distances, conditions, the place, when an upkeep buff is due, the
  migration and the save round trip (a potion entry and the Upkeep bar slot too).
- **Unit, potions** (`tests/PotionUpkeepTests.cpp`, "potion upkeep ..."): which potions are entries; due when gone or
  under the renew time, never over a stronger effect or while weak for Haste; drinks counted at the brew power; the
  members' stock added up; a restock that brews the missing drinks without mixing the stocked potions, and one that
  says why it could not; the planner keeping the strongest reserved copies.
- **Runtime** (`tests/GameplaySpellServiceTests.cpp`, "battle orders: ..."):
  - a spell with no target passes to the next order;
  - an order that is off is skipped;
  - a holder hands the press on;
  - everyone holding leaves the selection alone.
- **Runtime, upkeep** ("upkeep: a press casts the first due spell of a ready member's list"):
  - a missing party buff is cast once, and one under its renew time again;
  - a spell that is off or for another place is passed over;
  - a buff on one member goes to each living member in turn;
  - a heal waits for a wound;
  - a member in recovery leaves the press to the next;
  - a due spell the caster cannot pay for is not cast;
  - a due potion is drunk from another member's bags, and not again while its buff lasts;
  - a due potion nobody carries is passed over for the next entry;
  - with auto-brew, a press brews the missing stock and drinks it.

# Battle orders

Each member's battle orders say what Attack does: F, the left mouse button, smart left click, and the acting member in
turn-based combat. The same in every ruleset (Standard and MAW). The design is the chosen layout A of the study
[combat_orders_20261108](../level_generation/ui/combat_orders_20261108/README.md) (2026-11-08), from a Discord request
(puzzleR1). The place condition and the [upkeep list](#upkeep) followed on 2026-11-12, from two more (heron, Tyrkys).

## Rules

- **Orders.** Attack walks the member's orders top to bottom and does the first that holds and can be done now. There
  are at most sixteen (`BattleOrderLimit`). An order is one of three kinds:
  - a spell;
  - **Melee**: a blow, only with a target in the weapon's reach;
  - **Shoot**: the ranged weapon (bow, crossbow, wand, blaster, a dragon's breath), only with one.
- **Conditions.** Each order has optional conditions, and all of them must hold:
  - **Target distance**: a range in game units (0–5120; a maximum of 5120 means any). The presets are *in melee reach*
    (0–407) and *beyond melee reach* (407 up). 407 stands for the blow's exact reach, 407.2 units. A minimum is
    exclusive and a maximum inclusive, so the two presets meet exactly. An order with a distance fails when there is no
    target.
  - **An ally's HP is below** N % (10–90): the lowest HP share among the members a heal can still reach (not dead,
    eradicated or stoned).
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

## Upkeep

Each member also has an upkeep list: the buffs, heals and cures they keep up outside the fight. It is the same
orders in a second list (`Character::upkeepOrders`, at most sixteen as well), spells only, with its own key.

- **The Upkeep key** (`upkeep`, F11 by default; `GameplayActionController::executePartyUpkeep`):
  - A ready member casts the first spell of their list that is on, known, due, allowed here and paid for. The cast
    is an ordinary one: its mana, its recovery, its chance to fail.
  - In real time the active member is tried first, then the other ready members, and there is one cast per press. The
    caster becomes the active member and the selection moves on, as after an attack.
  - A held key repeats as Attack does (after 0.5 s, then every 0.14 s), so holding it goes through the lists as the
    members come ready.
  - In turn-based mode only the member whose turn it is casts, and the cast is that turn. In the movement phase the
    press ends the phase, as Quick Cast does.
  - A fresh press that casts nothing says why: no upkeep spells set, nobody ready, not enough spell points for a due
    spell, or nothing to cast.
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
- Android has no touch control for the key yet.

## Data

- `game/party/BattleOrders.h`: `BattleOrder`, `BattleOrderFallback`, `battleOrderConditionsHold`, `upkeepBuffDue`
  and `setAttackSpell`.
- `Character::battleOrders` and `battleOrderFallback` replace `attackSpellName`. They are saved from version 167
  (`SaveVersionBattleOrders`).
- An order's place and renew time, and `Character::upkeepOrders`, are saved from version 176
  (`SaveVersionUpkeepOrders`); an older save has every order anywhere and no upkeep list.
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
- **Spell menu.** A quick right click (up to 300 ms) on a spell in the book opens a short menu. It sets Quick Cast or a
  Quick Spell key (or clears one), adds the spell to the attack orders or to the upkeep list, or opens the window. Held
  longer, the right button shows the spell's description as before.
- **Quick Reference.**
  - An Orders row under QSpell shows each member's orders that are on, as small icons, with the fallback's mark last;
    of more than six, the first five and how many follow. Pointing at a member's cell lists the first ten orders
    with their conditions, the upkeep spells and the quick keys.
  - The rows below Name are 20 units apart instead of 21.67, so the table keeps its height. The background
    (`obsidian_quickref_surface`) has one more band.

## Tests

- **Unit** (`tests/BattleOrdersTests.cpp`): distances, conditions, the place, when an upkeep buff is due, the
  migration and the save round trip.
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
  - a due spell the caster cannot pay for is not cast.

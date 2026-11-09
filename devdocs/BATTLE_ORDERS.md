# Battle orders

Each member's battle orders say what Attack does: F, the left mouse button, smart left click, and the acting member in
turn-based combat. The same in every ruleset (Standard and MAW). The design is the chosen layout A of the study
[combat_orders_20261108](../level_generation/ui/combat_orders_20261108/README.md) (2026-11-08), from a Discord request
(puzzleR1).

## Rules

- **Orders.** Attack walks the member's orders top to bottom and does the first that holds and can be done now. There
  are at most six (`BattleOrderLimit`). An order is one of three kinds:
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

## Data

- `game/party/BattleOrders.h`: `BattleOrder`, `BattleOrderFallback`, `battleOrderConditionsHold` and
  `setAttackSpell`.
- `Character::battleOrders` and `battleOrderFallback` replace `attackSpellName`. They are saved from version 167
  (`SaveVersionBattleOrders`).
- An older save's attack spell becomes one unconditional order. A spell for a member (Heal, the cures, the revivals)
  gets the hold fallback, because the attack spell did nothing when nobody needed it (OY-190).
- `party_attack`'s `attack_spell` in scenarios makes that spell the member's only order for the step, with the weapon
  as fallback.

## Interface

- **Battle Orders window** (`game/ui/GameplayBattleOrders.cpp`), over the spellbook (`SpellbookState::battleOrders`):
  - It has member tabs, the orders with their on/off ticks and move and remove buttons, and the fallback switch.
  - The editor sets the selected order's conditions with sliders. The distance slider gives its first half to
    0–1024 units.
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
  Quick Spell key (or clears one), adds the spell to the attack orders, or opens the window. Held longer, the right
  button shows the spell's description as before.
- **Quick Reference.**
  - An Orders row under QSpell shows each member's orders that are on, as small icons, with the fallback's mark last.
    Pointing at a member's cell lists the orders with their conditions and the quick keys.
  - The rows below Name are 20 units apart instead of 21.67, so the table keeps its height. The background
    (`obsidian_quickref_surface`) has one more band.

## Tests

- **Unit** (`tests/BattleOrdersTests.cpp`): distances, conditions, the migration and the save round trip.
- **Runtime** (`tests/GameplaySpellServiceTests.cpp`, "battle orders: ..."):
  - a spell with no target passes to the next order;
  - an order that is off is skipped;
  - a holder hands the press on;
  - everyone holding leaves the selection alone.

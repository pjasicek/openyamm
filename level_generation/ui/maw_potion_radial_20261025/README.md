# Potion quick-slots — study, 25 October 2026

Browser study for MAW H.6's potion quick-slots ([GAPS](../../../devdocs/maw/GAPS.md) H.6, §11 D.16: "every piece
gets a browser mockup in the approved Obsidian style and the user's approval before native work"). It follows the
user's idea: six potion slots per character, opened from a small round button at each portrait or by holding a key
for the active member, filled from the character's inventory filtered to what they can drink, and drunk with a click
or a hotkey. Nothing is built natively.

Open [index.html](index.html) directly. The buttons at the top switch between the two options, the assignment screen
and the key bindings; the checkboxes switch enemies near, Ariel recovering and nobody ready. Click a slot to drink,
click an empty slot or right-click a filled one to choose its potion. `?view=radial|strip|assign|keys&open=N&export=1`
(plus `&drink=S`, `&recovering=1`, `&nobody=1`, `&calm=1`, `&slot=S`) gives the captures in [previews/](previews/).

The scenes are drawn over native 1600x900 captures of the split-arc party frame and the inventory screen
(from the [curved portraits](../obsidian_curved_portraits_20260929/native/README.md) captures), with the menu art
(`hud_x2/menus/omenu_*`), the Fondamento and Lucida fonts and the real potion icons (`icons_x2/item177` ...).

## What a slot is (both options)

- A slot holds a **potion kind** (Cure Wounds, Magic Potion, Haste ...), not one bottle: it drinks from the first
  matching bottle in that character's bags and shows the **drinks left** (MAW's bottles hold five). The count turns
  amber at 2 or fewer and red at 0; an empty-handed slot greys its icon and says "None left" but keeps its kind, so
  restocking needs no reassignment.
- **Which bottle**: weakest first (default, saves the strong ones), strongest first, or only one strength (the
  "power band"), chosen when assigning.
- **Who drinks and who pays** (MAW's rule, `potion_effects.yml` `combat_recovery`): a drink needs a ready member —
  the drinker if ready, else the active member, else the first ready one — and near monsters it costs that member 60
  recovery; elsewhere nothing. The status line says who gave it ("Lys gives Ariel a Cure Wounds (strength 40)
  +240 HP · Lys recovers"); with nobody ready the slot shows an hourglass and the drink is refused ("Nobody is ready").
- **Assigning**: an empty slot (click) or a filled one (right-click) opens that character's inventory with everything
  they cannot drink veiled and their bottles framed in gold (drinks left on each); a click picks the kind, the chips
  pick the bottle rule, Assign or Clear slot closes it and returns to play.

## A · Radial

![Ring open](previews/radial.jpg)

- A small round potion button at each portrait's upper right (clear of the HP and mana arcs, the aggro diamond and
  the buff star), for any member, active or not.
- It opens a ring of six slots above that portrait: slot 1 on top, clockwise, the hub naming the member and whether
  they are ready, recovering (and who feeds the next drink) or nobody is ready. Names under the slots, the hotkey
  number on each, the count bottom right. A second click on the button, Escape or a click outside closes it.
- Holding the **Potion wheel** key opens the active member's ring; releasing it over a slot drinks (the mouse picks
  the slot, as a weapon wheel does), releasing elsewhere does nothing.

| Drink | Fed by the next ready member | Nobody ready |
| --- | --- | --- |
| ![Drink](previews/radial_drink.jpg) | ![Fed](previews/radial_fed.jpg) | ![Nobody](previews/radial_nobody.jpg) |

## B · Slot strip

![Strip](previews/strip.jpg)

- A slim strip of six square slots docked above the party frame, always showing the **selected** member's slots
  (clicking a portrait selects as today, so the strip follows); a small pip at each portrait counts its filled slots.
- One click drinks; the same assignment screen and states as A. It costs a strip of screen over play but needs no
  extra click to open.

![Strip, nobody ready](previews/strip_nobody.jpg)

## Assigning (both)

![Assign](previews/assign.jpg)

## Hotkeys

![Key bindings](previews/keys.jpg)

A new **Potions** group in the key bindings: **Potion wheel (hold)** on V (A only) and **Potion slot 1-6** on
Keypad 1-6, which drink the active member's slot. Neither clashes: digits 6-9 and 0 are MMMerge's follower keys,
F5-F8 the extra quick spells, and the keypad digits pick dialogue options only while a dialogue is open.

## Open questions for the choice

- A (on demand, any member, no screen cost) or B (always visible for the selected member, one click), or both (B for
  the active member, A's button for the others)?
- The default bottle rule (weakest first here) and whether "only one strength" is worth its chip.
- Whether the slots belong to MAW only or to both rulesets (Standard has no drink recovery, so a drink there is always
  the drinker's own and free).
- Whether a slot may also hold a scroll (the user's idea names drinkables; scrolls would need a target).

## Native notes (when approved)

- Per character: six slots of {item kind, bottle rule, strength}; a save version for them.
- The drink goes through the existing potion path (`InventoryItemUseRuntime`, `PotionRules`) with MAW's recovery
  payer; the picker reuses the inventory screen with a filter; the ring and strip are new HUD layout elements in
  `gameplay.yml` drawn with the existing arc and HUD-quad helpers.
- Keys: `potion_wheel` and `potion_slot_1..6` in `KeyboardBindings` and the settings catalog.

## Native (2026-10-25)

The user approved option **A · Radial** for potions and scrolls (no wands) in both rulesets, weakest bottle first by
default. The core (slots on `Character::quickItemSlots`, save 125; `QuickItemSlots::canHold/findItem/countItems`;
`GameplayItemService::useQuickItemSlot`; keys Potion Wheel V and Potion Slot 1-6 on the keypad) is described with it;
the HUD is `game/ui/GameplayQuickItems.cpp`:

- A small round obsidian button at each portrait's upper right, for any member, shows a miniature of slot 1's item
  with the party's count (greyed when nobody carries one); with slot 1 empty, a black socket. It opens or closes that
  member's ring. The Potion Wheel key (V) opens the active member's ring on a tap (it stays open; the key again or
  Escape closes it); held longer, it uses the slot it is released over. Quick Potion (N) uses the active member's
  slot 1; slots 2-6 are unbound by default. While the ring is open, mouse look is off so the cursor can point.
- The ring above the portrait: slot 1 on top, clockwise, each with its key when one is bound, the potion or scroll,
  the count of that kind in the whole party's bags (amber at two or fewer; red with the icon greyed at none, the kind
  kept) and its name; the hub names the member and says ready, recovering (and, where drinks cost recovery, who gives
  the next one), or nobody ready. A click uses the slot (the core takes the item from the owner first, then the other
  members, and puts back what remains); an empty slot, or a right click, opens the picker; a click on the hub or
  away closes the ring.
- The picker opens beside the ring, on the side with more room, without leaving play: every potion and scroll the
  party carries, one row per kind and strength (icon, name, count, strength and who carries it), potions first; the
  wheel and the scrollbar scroll it. A click on a row fills the slot; Weakest first / Strongest first set the bottle
  rule; Clear slot empties it; Close, Escape or a click away closes the picker first, then the ring. Clicks on the
  ring and the picker are theirs: Attack bound to the left button does not also attack.

| Ring, empty | Picker over the party's list | Slot 1 filled | Buttons: miniature, sockets |
| --- | --- | --- | --- |
| ![](native/ring_empty.jpg) | ![](native/picker_full.jpg) | ![](native/ring_assigned.jpg) | ![](native/buttons.jpg) |

## Superseded as the default (2 November 2026)

The [basebar popups](../potion_scroll_popups_20261102/README.md) replace the per-portrait buttons and rings by default.
The ring and its picker remain, behind the Quick item rings setting (`quick_item_rings`, off by default), and the six
quick slots and their keys work either way.

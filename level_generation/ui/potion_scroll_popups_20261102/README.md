# Potion and scroll popups — study, 2 November 2026

The user's idea:
- a **potion** button at the left end of the party basebar and a **scroll** button at the right end;
- each button opens a popup that pauses the game and lists what the party carries;
- a click drinks the potion (or reads the scroll) as the active member;
- the per-portrait quick item rings ([the radial study](../maw_potion_radial_20261025/README.md)) become a setting,
  off by default.

Nothing is built natively.

Open [index.html](index.html) through the local server
(`http://127.0.0.1:8917/level_generation/ui/potion_scroll_popups_20261102/index.html`; the fonts do not load from
`file://`).
- The buttons at the top switch views and the two button placements.
- In the page you can click the medallions (or press V / T), hover and click rows, click a portrait to change the
  drinker, and press Escape.
- `?view=bar|potions|scrolls|target|settings&variant=a|b&member=N&hot=N&export=1` gives the captures in
  [previews/](previews/).

It is drawn over the radial study's native 1600x900 capture of the five-member split-arc basebar, using the Carved
Obsidian menu art, the Fondamento, Arrus and Lucida fonts and the real potion and scroll icons.

## The buttons

| A · on the end ornament (as circled) | B · beside it on a bracket |
| --- | --- |
| ![A](previews/bar.jpg) | ![B](previews/bar_b.jpg) |

- A carved brass medallion on each end ornament. It follows the ornaments when the frame narrows for a smaller party.
- The key letter sits top left and the party's count bottom right; the medallion greys out when the party carries
  none.
- A has nothing outside the frame. B keeps the ornament's scrollwork visible but widens the frame by about 45 px on
  each side.

## Potion popup

![Potions](previews/potions.jpg)

- **Game state:** the game pauses as it does in the inventory. The scene dims under a "Paused" tag; the basebar stays
  bright and live.
- **Position:** the popup rises from the button that opened it.
- **Drinker:** the active member, shown in the header with HP and SP bars. A striped ghost on the bar previews what
  the hovered potion restores.
- **Changing the drinker:** clicking another portrait below changes who drinks without closing the popup. The
  portrait gets a gold rim, and the "no effect now" marks follow the new drinker.

  ![Another drinker](previews/potions_gerrard.jpg)
- **Rows:** the existing quick item picker's rows, in two columns: one row per kind and strength, with icon, name,
  "strength · whose pack" and the count.
- **"No effect now":** a cure for a condition the drinker doesn't have, or a Magic Potion for a member without SP, is
  dimmed and marked. It can still be drunk.
- **Footer:** the hovered potion's effect on the drinker, for example "+30 HP (96 → 126 of 180)" or "Cures Gerrard:
  no longer poisoned".
- **Drinking:** a click drinks and closes the popup; the status line reports it, as now.
- **Quick keys:** right-clicking a row puts that potion on one of the quick keys (Num 1–6, the existing slots). With
  the rings off, this is how the keys get filled. A small number on a row shows its key.
- **Closing:** Close, Escape, the key again or a click away.

## Scroll popup and targets

![Scrolls](previews/scrolls.jpg)

- The same popup, rising from the right-hand button. Each row shows the spell's school dot, whose pack it is in, the
  count and what the spell needs: **on an ally**, **at a monster**, **the party** or **no target**.
- **Party or no-target spells:** a click reads the scroll at once. Town Portal and Lloyd's Beacon open their own
  windows, as they do now.
- **Targeted spells:** the popup closes and the game resumes. The usual target choice follows: the portraits are
  ringed and the status line says what to click; Escape puts the scroll back unread.

  ![Target](previews/target.jpg)
- **Monster targets:** the normal spell targeting cursor.

## Settings

![Settings](previews/settings.jpg)

- **Gameplay:**
  - **Potion and scroll buttons:** on by default.
  - **Quick item rings at portraits:** off by default. With it on, the portrait buttons and rings come back as they
    are now.
- **Controls:**
  - **Potions (V):** replaces Potion Wheel's binding. With the rings on, a held V still opens the active member's
    ring.
  - **Scrolls (T):** T and O are the only free letter keys today.
  - **Unchanged:** Quick Potion (N) and Potion Slot 1–6 (keypad).

## Buttons built into the end ornaments (second pass)

The user asked for the end ornaments themselves to hold the buttons. Three versions of the compact end ornament with a
round socket carved into it were generated:
- **Tool:** the Codex built-in image tool, in edit mode, from the installed `obsidian_party_endcap_compact.png`.
- **Briefs:** `art/CODEX_BRIEF_v1.md`–`v3.md`.
- **Outputs:** `art/endcap_socket_v1.png`–`v3.png`, 992×1586 RGBA with true alpha, unchanged.

The socket's inside is empty dark obsidian: the engine would draw the potion or scroll icon, the key and the count
into it. The rail, the rivets and the height are kept, so each version attaches to the frame as the current one does;
only the width grows outward (57 → 78 / 87 / 82 px at 1600×900).

![Sockets](previews/sockets_compare.jpg)

| v1 · wrapped scrollwork | v2 · medallion boss | v3 · leaf crown |
| --- | --- | --- |
| ![](previews/socket_v1.jpg) | ![](previews/socket_v2.jpg) | ![](previews/socket_v3.jpg) |

![v2 with the potion popup](previews/socket_v2_potions.jpg)

How the mockup shows them:
- `art/composite.py` removes the current ornament from the capture (with its own alpha, filled with the grass beside
  it) and draws the new one at the engine's position, with the right ornament mirrored.
- It also measures where the socket lands on screen.
- In the page, the socket variants (`variant=v1|v2|v3`) draw only the button's contents in the socket, plus a gold
  hover glow and an "open" ring.

Native notes for a socket version:
- **Sprite:** it replaces `obsidian_party_endcap_compact` in `GameplayUiSkin::renderPartyBasebar`, with new
  registered UVs and its own width-to-height ratio.
- **Click area:** the socket centre and radius become the buttons' click circle.
- **Phones:** the medallion (v2) has the largest opening, about 50 px across at 1600×900. That is still small for a
  thumb on a phone, where the click circle may need to cover the whole ornament.

## Open questions

- Which button: **A** (on the ornament), **B** (beside it), or one of the sockets built into the ornament
  (**v1**, **v2**, **v3**)?
- Should the popup close after one drink (as drawn), or stay open for another, perhaps with Shift held?
- Should "no effect now" rows stay in place (as drawn, so rows don't move) or sink to the end?
- **Turn-based and MAW:** should a drink in turn-based combat use the drinker's turn, and should the paused drink keep
  MAW's recovery cost near enemies? The mockup assumes yes to both.
- **Android:** the medallions are 66 units across, which is thumb-sized. At 4:3 the left medallion may need to give
  way to the lower-left touch column (Turn Mode / Inventory / Inspect).
- Should wands go in the scroll popup? They are left out, as they were in the radial study.

## Native notes (if approved)

- **Medallions:** two new HUD elements anchored to the basebar's end ornaments, drawn with the existing HUD helpers.
- **Popups:** pause the game as the inventory does, and reuse the quick item picker's party-wide list
  (`GameplayQuickItems`) in two columns. The potion popup filters to potions, the scroll popup to scrolls.
- **Using an item:** goes through the existing paths. Potions use `GameplayItemService` and `PotionRules`; a scroll
  read uses the spell cast with its targeting.
- **Settings and keys:** `GameplayQuickItems` draws the portrait buttons and rings only when the new setting is on.
  The keys go in `KeyboardBindings` and the settings catalog.

## Native implementation (2 November 2026)

The user chose the button **built into the ornament** with socket **v2 · medallion boss**, potions on the **right** and
scrolls on the **left**. (A first pass drew separate medallions over the plain ornament, as option A; the user
corrected that.) Further decisions:
- **Buttons:** icon only, with no key letter or count. They stay visible with the party frame turned off.
- **Scroll rows:** no target tag and no explanation lines; reading a scroll goes into exactly the same spell targeting
  as using it from the inventory.

Ornament:
- **Source:** `assets_source/engine/icons_x2/obsidian_party_endcap_socket.png` is `art/endcap_socket_v2.png`
  unchanged, from the Codex image edit in `art/CODEX_BRIEF_v2.md`. It is 992×1586 RGBA, SHA-256
  `9f0dd85385926cd9ce573c0bfc66cb64106c9b350c52637ba3c0b58a558ddf02`.
- **Cooked:** with `tools/cook_ui_textures.py` for both profiles.
- **Drawing:** `GameplayUiSkin::renderPartyBasebar` draws it instead of the compact ornament in plain gameplay while
  the buttons setting is on; other screens keep the compact one. Its registered bounds are [156, 104, 745, 1430]. The
  rail meets the frame where the compact one's did, and the ornament grows outward.
- **Socket:** `partyBasebarSocket` gives the socket's place, at 0.407 of the width from the outer edge and the middle
  of the height, with a radius 0.130 of the height. The button is only the icon in the socket, with a gold rim while
  its popup is open. With the frame hidden, a round obsidian plate stands just outside where the frame's border
  would be, closer to the portraits and a little lower than the sockets.

Code:
- **Drawing and input:** `game/ui/GameplayQuickItems.cpp`, beside the quick item ring, sharing its painter.
- **Listing:** `QuickItemSlots::partyItemKinds` (one entry per kind and power; potions with nothing to drink, such as
  Recharge Item, are left out) and `findPartyItemOfPower`.
- **Using:** `GameplayItemService::useCarriedItem`, the quick slots' path. It lends the item out as a held item and
  uses it on the chosen member, as one dropped on their portrait; whatever is left goes back where it lay.
- **Preview:** `InventoryItemUseRuntime::previewPotion` gives the HP and SP a drink would restore, clamped as the drink
  is, and the conditions it would cure. Restore- or cure-only potions that would do nothing are marked "no effect
  now" and can still be drunk.

Behaviour:
- **Placement:** after the user's correction, the popup is centred over the scene, about 1000 px wide at 1600×900,
  between the top HUD and the frame. Its contents are drawn 1.3 times the study's size, and the scene is neither
  dimmed nor labelled.
- **Pausing:** an open popup pauses the game through the standard world input gate, as the inventory does. It frees
  the cursor and hides the world's hover text; Escape closes the popup (the quick-slot chooser first) and does not
  open the game menu.
- **Who uses it:** the popup opens for the active member; clicking a portrait changes the member, whose rim turns gold.
- **Using an item:** a click drinks or reads it and closes the popup. A scroll closes the popup first, so its target
  is chosen over the running game.
- **Quick slots:** a right click opens six chips that put the kind in one of the member's quick slots (or take it
  out); a small number on a row shows its slot.
- **Layout:** the popup grows with its entries, up to six rows in two columns, and the wheel or the scrollbar scrolls
  it. Potions have a footer describing the hovered potion.

Settings and keys:
- **Potion and scroll buttons:** `item_buttons`, on by default.
- **Quick item rings:** `quick_item_rings` (formerly `potion_buttons`), off by default. The ini key is new, so saved
  settings start with the rings off.
- **Potions (V):** still the `quick_item_wheel` binding. It opens the potion popup, or the ring when the rings are on.
- **Scrolls (T):** the new `scroll_popup` binding.

Tests:
- **Unit tests:** `QuickItemSlotTests.cpp` covers the listing, the exact-power lookup and the preview.
- **Scenario:** `tests/scenarios/rulesets/potion_slot_keys.yml` checks the keys through the new
  `assert: {quick_item_popup: {kind, member_index}}`.

Desktop captures, 1600×900:

| Potions, hovered | Quick slot 1 on Cure Wounds | Another drinker (gold rim), still paused |
| --- | --- | --- |
| ![](native/potions.jpg) | ![](native/quick_slot.jpg) | ![](native/other_drinker.jpg) |

| Socketed ornaments, three members | One member | Frame off: the buttons alone |
| --- | --- | --- |
| ![](native/buttons.jpg) | ![](native/buttons_one_member.jpg) | ![](native/buttons_no_frame.jpg) |

| Potions, centred | Scrolls, centred | Heal read: the usual target choice |
| --- | --- | --- |
| ![](native/potions_open.jpg) | ![](native/scrolls_open.jpg) | ![](native/scroll_heal_target.jpg) |

The first three popup captures (the first table) come from the first pass: medallions beside the plain ornament, a
smaller popup over its button on a dimmed scene with a PAUSED tag.

Not checked on Android. At 4:3, the left button may come close to the lower-left touch column.

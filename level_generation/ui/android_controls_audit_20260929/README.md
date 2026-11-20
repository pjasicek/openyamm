# Android controls and menus audit — 2026-09-29

The main Obsidian gameplay controls are present, but the UI is not yet complete for touch-only use.
This is an audit and proposed interaction contract; no runtime behavior was changed for this audit.

## Coverage

| Surface / operation | Current state | Remaining work |
| --- | --- | --- |
| Movement, camera, jump | Joystick, camera drag and double-tap jump are implemented. | Validate comfort and camera behavior on a release APK/device. |
| Attack, cast, quick cast, turn mode | Explicit touch buttons; left vertical column and right action/context group use the approved layout. | Device validation. The pause-shaped left button toggles turn mode; the options gear opens the pause/menu screen. |
| Context action, followers, party/personal buffs | Tappable controls and popups are present. | Device validation of overlap, dismissal and small targets. |
| Flight | Up/down buttons are conditional on the Fly buff outdoors. | Device validation. |
| Spellbook and targeting | Spell selection, quick-cast assignment, casting and cancellation have touch paths. | Device validation. |
| Inventory movement/equipment | Tap pickup/placement and touch drag/drop are implemented. Portrait taps transfer held items. While an item is held, the inventory page's Sort button reads Drop and drops it in front of the party (2026-10-30). | Keep these operations separate from consuming/mixing items. |
| Inventory inspection | Magnifier modifier plus another touch simulates held RMB. | Overlay magnifier is only 24 logical pixels; consider a larger hit area. |
| Potion mixing / reagent bottles / wand recharge | Shared gameplay rules exist, but activation needs a fresh RMB press over the target. | **Blocking:** the normal modifier-first touch sequence supplies no fresh RMB press on the target. |
| Using a held item on a character | Shared potion/item/scroll use exists through RMB on a portrait. | **Blocking:** modifier-first interaction can latch before the target portrait is touched. A normal portrait tap transfers the item instead. |
| Stats, skills, awards, rest, quick reference | Tappable controls; skills/awards have draggable scrollbar/track paging. | Larger scroll hit targets and content swipe would improve touch use. |
| Journal, map, quests, story, autonotes | Tappable paging/zoom controls and map drag paths exist. | Device validation; no pinch gesture is required for functional access. |
| Shops, chests, dialogue, beacon/portal windows | Normal selection and visible close/action controls have touch paths. The chest's Inventory button swaps the chest grid for the party's packs, to put items in, and reads Chest to swap back (2026-10-30). | Check long topic lists and text prompts on device. |
| Arcomage | Android tap-to-play and upward card-swipe discard are implemented. | Device validation. |
| Main/pause, save/load, settings | Buttons, fields, sliders and scroll tracks accept touch through normal pointer input. | List-body swipe is absent; scrollbar ergonomics need review. |
| Choice popups | First eight choices are tappable; additional choices require wheel/keyboard navigation. | **Blocking:** add touch scrolling and an explicit Cancel control. Selection-only popups cannot currently be dismissed with touch without selecting a value. |
| Character creation help | Class, skill and stat descriptions require RMB; active menu screens do not receive the gameplay magnifier modifier. | **Blocking:** long-press inspection or a Help control. |
| Software keyboard | Engine-managed Android text input is wired for active screen fields, save names, bank amounts and pending text prompts. | Validate IME confirmation/back behavior; add visible OK/Cancel for bank/puzzle prompts. Numeric amounts could request a numeric keyboard. |
| Android system Back | AC_BACK is not mapped to the Escape/cancel path, and the application does not explicitly trap Back. | **Blocking:** close/cancel the current surface first, otherwise open pause; coordinate with keyboard dismissal. Actual OS behavior still needs device verification. |

## Inventory: current behavior

On desktop, pick up potion A with LMB and press RMB on potion B to attempt a mix. A normal drop moves/swaps
items. RMB on a party portrait applies a held item to that character; LMB on the portrait transfers it.

On Android, the Inspect button makes RMB held immediately, before another finger has selected a target.
Mixing listens for `rightMouseButton.pressed`, so holding Inspect and then touching potion B does **not**
produce the edge required to mix. Touching B first and then pressing Inspect does produce the edge, but that
finger-order dependency is unsuitable as the supported interaction. Modifier-only presses also retain the
previous pointer position. Portrait item use has a related one-attempt latch: it is set while an item is held
even if the pointer has not reached a portrait yet.

The existing item service already owns recipes, best-party Alchemy, bottles, catalyst behavior, skill failures,
explosions, sounds and recipe autonotes. Reagent + empty bottle works in either direction; recharge potion on
a wand is also supported. These rules should be reused by the touch UI. This audit does not establish support
for additional equipment-coating/enchantment actions.

## Proposed touch contract

1. Tap an item to pick it up, or drag it to move/equip it, as today.
2. While a usable item is held, show a reachable contextual **Use** / **Mix** / **Apply** control in the inventory
   chrome. It should not cover grid cells or disturb the fixed inventory layout.
3. Tap that control to arm one operation. For mixing, tap the second potion; for drinking, tap the intended
   portrait; for reagent/bottle or wand recharge, tap the corresponding item. A single-target drink action could
   also offer **Use on selected character**, provided that the target is explicit.
4. Show a visible Cancel action, and clear the armed operation when the inventory is closed or its held item
   changes. Return to ordinary movement after an attempt.
5. Call the existing item service directly. Preserve unknown-recipe experiments and legitimate Alchemy failures;
   do not silently limit targets to combinations guaranteed to succeed.

Keep Inspect dedicated to inspection. Normal drag/drop must not automatically mix potions or consume items.
The same explicit use path should cover the existing held-item use actions, including consumables and scrolls.

## Recommended order

1. Explicit held-item Use/Mix/Apply targeting.
2. Shared choice-popup Cancel and touch scrolling; current Antagarich data declares nine base class choices
   before race filtering, while the popup shows at most eight. There is no exposed class-cycle button in the
   current creation view.
3. Android Back routing and touch access to character-creation help.
4. Visible text-prompt confirmation/cancellation and larger scrollbar/inspection hit targets.
5. Release APK validation on a device across 4:3, 16:9 and 2:1, different party sizes, keyboard open/closed,
   Fly on/off, long lists and inventory use/mixing successes/failures.

## Evidence and limits

- `current_touch_controls.log`: 375 checks passed against the actual Android conditional input branch and
  current YAML hit rectangles at 640×480, 1200×900, 1600×900, 1800×900 and 2100×900.
- `gesture_order.log`: modifier-first versus target-first RMB edge behavior, normal drag release, active-menu
  touch behavior and lack of Escape mapping for AC_BACK. The probe uses the real `GameInputSystem.cpp` with
  synthetic SDL events, compiled on the host with `__ANDROID__` defined.
- `unit-tests.log`: 22 existing focused tests / 154 assertions passed for mixing, potion notes/explosions,
  mobile movement and input event behavior. These validate shared rules, not a complete in-game touch session.
- `run_probes.py` reproduces the two input probes after the normal development build exists.
- `source_receipt.json` records source hashes at audit completion; concurrent work can change these later.
- **No release APK or physical-device validation was performed.** The configured SDK directory
  `/home/pjasicek/android-sdk` is absent and the expected JDK 17 is unavailable in the current environment.

## Authoritative source paths

- Layout: `assets_dev/engine/ui/gameplay/touch_controls.yml`.
- Touch classification/edges: `game/app/GameInputSystem.cpp`.
- Touch activation scope: `game/app/GameApplication.cpp` (controls supplied only without an active menu screen).
- Inventory RMB application and normal drag/drop: `game/gameplay/GameplayPartyOverlayInputController.cpp`.
- Portrait item-use latch and LMB transfer: `game/gameplay/GameplayHudInputController.cpp`;
  `GameplayScreenController.cpp` passes RMB held state to it.
- Item behavior: `game/gameplay/GameplayItemService.cpp`, `game/items/InventoryItemMixingRuntime.cpp`.
- Choice popups and scroll tracks: `game/ui/MenuDesignScreen.cpp`.
- Creation descriptions/class popup: `game/ui/screens/NewGameScreen.cpp`;
  class declarations: `assets_dev/engine/data_tables/character_selection.yml`.
- Managed keyboard: `engine/EngineApplication.cpp`; field-state callback and prompt event handling:
  `game/app/GameApplication.cpp`.
- Bank/text prompts: `game/gameplay/GameplayOverlayInputController.cpp`.
- Arcomage gestures: `game/ui/screens/ArcomageScreen.cpp`.

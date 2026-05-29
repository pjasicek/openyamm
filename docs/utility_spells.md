# Utility Spells

## Implemented flow

- `Fire Aura` and `Vampiric Weapon` now open the caster inventory and wait for an item target.
- `Enchant Item` also opens the caster inventory and only works on inventory items.
- `Town Portal` opens a continent-aware destination picker driven by
  `assets_dev/engine/data_tables/town_portal_switch.txt` and
  `assets_dev/engine/ui/gameplay/town_portal.yml`.
- `Lloyd's Beacon` opens a set/recall overlay with slot count based on Water mastery.

## Item targeting

- Item-target spells reuse the normal character inventory screen.
- While a spell is waiting for an item target, normal inventory manipulation is suppressed.
- `Esc` or the character close button cancels the pending spell selection.

## Enchant rules

- `Fire Aura`
  - valid on unenchanted common weapons
  - applies `of Fire`, `of Flame`, or `of Infernos` based on mastery
  - Grandmaster makes it permanent
- `Vampiric Weapon`
  - valid on unenchanted common weapons
  - applies `Vampiric`
  - Grandmaster makes it permanent
- `Enchant Item`
  - valid on normal, unbroken, unenchanted inventory items
  - success chance is `10% * Water Magic skill`
  - low-quality items break instead of enchanting
  - Master and Grandmaster can roll stronger enchantments

## Town Portal

- Destinations, backgrounds, button icons, and button positions are defined in
  [town_portal_switch.txt](/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/town_portal_switch.txt).
- The Town Portal overlay shell is defined in
  [town_portal.yml](/home/pjasicek/github/OpenYAMM/assets_dev/engine/ui/gameplay/town_portal.yml).
- Each destination can be gated by its switch-table QBit.
- Destination placement comes from the switch-table target map and coordinates.
- Non-Grandmaster casting still respects the hostile-nearby restriction and pre-book success roll.

## Lloyd's Beacon

- Beacon duration is `1 week * Water Magic skill`.
- Slot count is `1 / 3 / 5 / 5` for Normal / Expert / Master / Grandmaster.
- Beacons store map name, location label, position, facing direction, and remaining lifetime.
- Expired beacons are cleared during party timed-state updates.

## Tuning points

- Town Portal destinations: [town_portal_switch.txt](/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/town_portal_switch.txt)
- Overlay visuals: [GameplayPartyOverlayRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayPartyOverlayRenderer.cpp)
- Input flow: [GameplayPartyOverlayInputController.cpp](/home/pjasicek/github/OpenYAMM/game/gameplay/GameplayPartyOverlayInputController.cpp)
- Spell behavior: [PartySpellSystem.cpp](/home/pjasicek/github/OpenYAMM/game/party/PartySpellSystem.cpp)

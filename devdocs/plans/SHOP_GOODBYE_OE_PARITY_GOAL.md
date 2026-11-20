# Shop Goodbye OE Parity Goal

Goal: match OpenEnroth shop-exit audio behavior for weapon, armor, magic, and alchemy shops.

## OE Behavior

- Shops track whether a real transaction happened during the current visit.
- Transactions are successful buy, sell, identify, and repair actions.
- Normal shops on house close:
  - If party is not shop-banned and a transaction happened, play `ShopGoodbyePolite`.
  - If party is not shop-banned, no transaction happened, and party gold is greater than 10000, play
    `ShopGoodbyeRude`.
  - If party is not shop-banned, no transaction happened, and party gold is 10000 or less, play no shop goodbye sound.
  - If rude goodbye path is taken, schedule `ShopRude` speech on a random active character after a short delay.
- Alchemy shops:
  - If not banned, play `AlchemyShopGoodbyeBought` after a transaction, otherwise `AlchemyShopGoodbyeRegular`.
  - Only banned alchemy-shop exits schedule `ShopRude`.

## Current Gap

- `HouseShopOverlayState` does not record transaction state.
- Buy/sell/identify/repair success paths do not mark the current shop visit as having a transaction.
- Shop close handling only plays rude goodbye for bad reputation and does not use transaction state.
- `ShopRude` is played immediately on the active character instead of delayed on a random active character.
- Alchemy-shop goodbye special handling is missing.

## Implementation Plan

1. Add per-visit shop transaction state to the UI/dialog state used by shop overlays and inventory service overlays.
2. Mark transaction state on successful non-steal buy, sell, identify, and repair.
3. On final house close, select goodbye sound using OE rules, including the `gold > 10000` rude threshold.
4. Add delayed party speech support or reuse an existing pending-audio mechanism so `ShopRude` plays after the
   proprietor line.
5. Add alchemy-shop-specific goodbye selection.
6. Cover with focused tests for normal shop transaction/no-transaction exits, low-gold no-transaction exit, and alchemy
   shop exits.

# Who knows this spell: markers under spellbooks — 13 November 2026

Request: in magic guilds and in spellbook descriptions, show which party members already know a spell, so that in a
new guild it is clear at a glance whether, say, every cleric already has Hammerhands.

**Status: chosen and implemented natively (2026-11-13).** The browser mockup offered more (portrait badges while
hovering, a status-line summary, a Party section with faces in the inspect popup and in the spellbook's spell
description); the user kept only the row of markers under each book on the shelf and the same row under the book's
picture in the inspect popup. Mockup canvas (trimmed to the chosen design):
https://claude.ai/artifact/118if19tEdYgo26foDqu1f

## The markers

One marker per party member, in portrait order, on a small dark plate:

| Marker | Meaning |
| --- | --- |
| Gold disc with a tick | Knows the spell (by any means, also a class that reads no books) |
| Blue ring with a plus | Can learn it from this book now |
| Grey ring with an up chevron | Could learn it after training: lacks the school or its mastery, but the class reaches it |
| Dash | Never can: the class cannot reach the mastery, or reads no books (MAW) |

Shapes differ as well as colours, so the states read without colour vision.

## Where they show

- Guild shelves (`GameplayDialogueRenderer`, under each book).
- Merchant lists (`GameplayHouseShopLedgerRenderer`, MM9's merchants and Shops as lists): in the Stat column, which
  spellbooks leave empty.
- The item inspect popup of any spellbook, wherever it is inspected (`GameplayPartyOverlayRenderer`, under the
  picture).

## Rule and drawing

- `InventoryItemUseRuntime::checkSpellbookLearn` is the one learning check: using a book on a member calls it, and
  `spellbookKnowledge` maps it to the four markers, so the markers cannot disagree with learning.
  "Could learn after training" compares the class's skill cap (`ClassSkillTable::getEffectiveCap`) with the mastery
  the book needs.
- `game/ui/SpellbookKnowledgeMarkers.cpp` rasterizes each plate once per state combination and on-screen size
  (anti-aliased distance fields, cached dynamic HUD texture), so it stays sharp at every HUD scale and costs one quad.
- Unit test: `spellbook knowledge markers follow the learning rule for each member`
  (`tests/InventoryEquipRegressionTests.cpp`).

## Native captures

`native/`: MM6 Initiate Guild of the Self, Body shelf (two Expert/Normal clerics, a cleric without Body, a knight, a
druid), its inspect popup, and MM9's Sea of Magic list (Thjorgard). Test parties were built with headless scenarios
and the guild membership set through `lua evt.SetPartyVariable(32783, 1)`.

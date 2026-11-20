# MM9 Buy view study — 5 November 2026

Browser mockups of alternative **Buy** views for MM9 vendors. Scope from the user: sell, identify, repair and the
party-inventory screens stay as they are; only the view opened by Buy Standard / Buy Special changes.

**Status 2026-11-05: the user chose A, the ledger; it is implemented natively** for every MM9 vendor (vendors.txt
`buy_view` `Ledger`), and since 2026-11-06 a restock is MM9's 15 rolls per range in one merchant list behind a single
Buy, instead of Standard and Special pages padded to shelf sizes. See "Buy view: the ledger" in
[MM9_VENDOR_SHOP_INTEGRATION_GOAL.md](../../../devdocs/mm9/MM9_VENDOR_SHOP_INTEGRATION_GOAL.md). The other views
remain here as the record of the comparison.

Open [index.html](index.html) (or the published artifact). Regenerate its data and assets with
`python3 prepare.py`. Nothing here touches runtime code or mounted assets.

## What MM9 did

`mm9/extracted/ART/ART/INTERFACESCREENS/MERCHANT/MERCHANT-COORDS.txt` and `MERCHANTBG.pcx` (800×600) define the
original screen: two open books. The store list on the left shows 9 rows of a 32×32 icon plus a 168-pixel name
column, with a scrollbar and six filter tabs (Weapons, Armor, Gloves/Boots, Jewelry, Potions/Misc, Quest). The
active character's list on the right has 8 rows and the same tabs. Buy/Sell buttons with running totals sit under
each list; four party faces, Repair, Identify and Exit sit in the middle column.

## Original MM9 stock (from `mm9/game/data/object.lto`)

Rizin on `object.lto` (SHA-256 `b1271f37…f162`, base `0x10000000`):

- `fcn.100b7b40` loads `data\mmixshops.txt` into 0x540-byte records at `0x102a49e8`. It reads only columns A
  (name), B (NPC id), C (type), F (merchant base), G/H (first range, concat %), I/J (second range, concat %) and
  L (restock: `2 Weeks` = 14 days, `2 Months` = 60). It never reads D (Merchandise), E (Wealth) or K (Quanity),
  so a magic shop named for one school is not filtered by school. Record `+0x538` is hard-coded to **15**.
- `fcn.100b8040` returns a shop's container and refills it when it is empty or `days × 86400` seconds have
  passed: `fcn.10048230` clears it, `fcn.100b8310` refills it.
- `fcn.100b8310` makes 15 rolls with the first range and 15 with the second: **30 rolls per restock**. Shop types
  map to generator categories 2 Weapon, 3 Armor, 4 Magic, 5 Apothecary, 6 General Store, 7 Library.
- `fcn.10046fe0` picks a treasure level in the range, converts it to an item level with `fcn.100468d0` (TL0: L1 75%,
  L2 25%; TL1: L1 50%, L2 40%, L3 10%; TL2: L1 25%, L2 50%, L3 25%; TL3: L1 15%, L2 40%, L3 30%, L4 15%; TL4: L2 20%,
  L3 40%, L4 30%, L5 10%), then picks a random item of that level whose type the shop accepts (`fcn.100486a0`).
  Rolls are independent, so copies are common. A roll with no eligible item adds nothing.
- `fcn.10048270` adds to the container, capped at 256 entries.
- Accepted types (enum from the `MasterItemList.csv` parser at `0x10045c40`): Weapon = Weapon, Weapon2H, Ranged
  Weapon; Armor = Armor, Helm, Shield, Gloves, Boots, Belt; Magic = `Magic` (spells); Apothecary = rings,
  amulets, potions, belts, magic scrolls, runestones (no wands); General Store = rings, gloves, potions, belts,
  scrolls, runestones, Weapon, Ranged Weapon; Library = `Items_Skill`.
- `fcn.100b7550` gives each new item a chance of a concat, set by the range's minimum treasure level (40% for TL1–2,
  50% TL3, 60% TL4, 75% TL5). Whether the H/J percentages from the table are used anywhere was not traced.

Simulated over 4,000 restocks per shop, using `MASTERITEMLIST.csv` column 4 as the item level: libraries show 28–30
books, 12–14 different titles (22 skill books exist); magic shops 30 spells, 18–22 different (47 exist); armour
16–23 different, weapons 17–22, apothecaries 23–25, general stores 24–26, all from 30 entries.

## What our stock looks like

From `assets_dev/worlds/mm9/data_tables/vendor_stock.txt` (generation version 1):

- 48 vendors, 3,816 slots. Pages are sized to the MM6–MM8 shelf they are drawn on
  ([HouseShopLayout.cpp](../../../game/ui/HouseShopLayout.cpp)): weapons 6, armour and general store 8,
  apothecary, library and spellbook 12.
- **706 slots are padding**: the same item repeated on one page. Worst cases: Thorkell's Light, The Dark Hand and
  Frigg's Sprit have 2 distinct spellbooks, six copies each; Eye of Newt has 4 items ×3 on all eight pages; the
  Arslegard school shops have 4 books ×3.
- In all 48 vendors the Buy Special page lists the same item ids as Buy Standard; only enchantments differ.
- Every slot has quantity 1.

## Views compared

| View | Holds | Notes |
| --- | --- | --- |
| Today: MM6–MM8 shelf | 6, 8 or 12 | Shelf art from another world; padding copies visible; long polearms cropped |
| A · Ledger | Any (scrolls) | MM9's list on the Obsidian reading surface; MM9 filter tabs as chips; copies grouped with a count; name, enchantment, stat and price per row |
| B · Merchant's chest | 13×9 cells of 32 logical px (~20–30 items; a full MM9 restock often does not fit) | Same cells as the party inventory; real footprints; prices on hover or a toggle; books become identical covers |
| C · Display niches | 12 per page | Equal wells, scaled items, names and prices always shown; best on touch |
| D · Counter | Any (scrolls) | Live shop room stays visible; narrow list plus a detail plate with Buy |

## Recommendation

A (ledger) for MM9 vendors, with B as the low-cost fallback. Either way the vendor generator should stop padding
pages to shelf sizes: drop the duplicate slots or emit them as `quantity`, and turn the importer's slot-count check
into a per-profile maximum. Buy Special could become an "enchanted only" filter of one list.

## Sources

- Frame: native capture `../obsidian_curved_portraits_20260929/native/overlay_arcs/images/house-topic.png` with the
  runtime `obsidian_house_sidebar` pasted over its right panel at layout size (172×368 logical).
- Panels: runtime `obsidian_reading_surface` and the eight carved `obsidian_frame_*` slices
  (composited into `assets/frame9.png`), `obsidian_button_close_*`.
- Shop rooms: `level_generation/projects/mm9r_thjorgardcity/review/v03/` captures cropped to the media rectangle.
- Item art: `assets_dev/worlds/mm9/icons_x2` and engine spellbook icons; shelves from `assets_dev/engine/icons_x2`.
- Fonts: the faithful Arrus, Create, Comic, Smallnum and Lucida TTFs and Fondamento (OFL).
- MM9 merchant background converted from `MERCHANTBG.pcx` for reference.
- MM9 has no NPC portraits; the sidebar uses an initial in a brass ring, as the MM9 talk bar does.

Prices in the mockups are item values; the shop price formula is not applied.

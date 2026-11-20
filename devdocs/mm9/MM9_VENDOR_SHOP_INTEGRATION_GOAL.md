# MM9 Vendor And Shop Integration Goal

## Status

Implemented on 2026-08-27 from an audit of MM9 RUDE service rows, `MMIXSHOPS.txt`, the imported MM9 item catalogue,
shared OpenYAMM house/shop runtime, dialogue rendering, shop stock persistence, and MM9 item-quality documentation.

The checked-in generation currently contains 48 canonical vendors, 48 aliases, and 3,816 deterministic stock slots.
The 48 reachable RUDE `-2` rows across 47 source NPC ids all resolve. Source selling vendor 138 is retained as the
explicit audited exception because the recovered RUDE data contains no shop row for it. Runtime stock generation is
version 1. The generated runtime tables contain only ordinary item/enchant fields; Normal/Good/Excellent and source
`Q` exist only in `vendor_stock_audit.yml`. The strongest ordinary result is L6, while L7 remains reserved for
artifacts, relics, and other authored rare content.

The importer also retains all 104 headerless `CONCAT.csv` rows losslessly. Its 238 deterministic equipment concats
carry exact source ids, rows, applicability flags, tiers, and reviewed ordinary OpenYAMM mappings; non-equipment
spellbook and skill-book slots are explicitly concat-ineligible.

The same composition now includes 16 MM9 temple/training service venues: eight training arenas, seven normal temples,
and the quest-unlocked Thronheim midwife. RUDE opcodes `-3`, `-8`, and `-16` open the shared OpenYAMM training,
healing, and donation actions over live gameplay and return to the suspended RUDE conversation. MM9 supplies only the
venue identity and authored price multiplier. Training uses the shared unlimited-cap value `0` because no MM9 source
level cap was found; temple healing tier `0` delegates all supported conditions to the shared temple logic.

No part of this goal is complete merely because selecting "show me your wares" displays a menu. Completion requires
source-owned vendor identity, deterministic and audited stock, correct one-time quality conversion, complete transaction behavior,
RUDE return semantics, persistence, and regression coverage.

## Objective

Implement every MM9 item-selling vendor through shared OpenYAMM shop systems so that:

- selecting an MM9 RUDE shop row temporarily hides the RUDE overlay;
- the standard MM6-MM8-style shop dialogue opens over the live gameplay scene;
- no looping house video, empty video frame, or dark video placeholder is rendered;
- the vendor root offers `Buy` (one merchant list, as in MM9; see "Restock size" below) and `Display Equipment`
  where enabled by its profile;
- nested buy, sell, identify, and repair behavior uses shared gameplay transactions;
- closing the vendor returns to the exact suspended RUDE conversation;
- `OnRudeExit` does not run when entering or leaving the vendor and runs exactly once when RUDE itself closes;
- every stock slot and concat is deterministic content data produced by a one-time MM9-to-OpenYAMM quality conversion;
- the strongest ordinary shop item is effective tier L6, immediately below L7 artifacts and relics; and
- mounting no MM9 content adds no meaningful vendor data, loading work, runtime branching, or memory use.

## Source Authority

Use local sources in this order:

1. `mm9/extracted/DATA/DATA/MMIXSHOPS.txt` for shop identity, raw NPC id, shop category, merchandise family, merchant
   base, both treasure-level ranges, both concat percentages, and restock period.
2. The matching `assets_dev/worlds/mm9/dialogue/rude/NPC*.rude` rows for actual invocation, response text, opening
   conditions, and service opcode `-2`.
3. Required dialogue-linked SCR, including `CLOSESHOP.scr`, for source opening and closing behavior.
4. `MASTERITEMLIST.csv` and the generated MM9 `items.txt` contribution for base item identity, source treasure level,
   category, restrictions, normalized tier, and content flags.
5. `CONCAT.csv` for MM9 enchantment identities and applicability.
6. `SKILLBOOK.scr` and reviewed item-source overrides for skill-book identity.
7. The MM9 manual and strategy guide for the distinction between treasure level, item quality, and concatenations.
8. Shared OpenYAMM house, item, enchantment, inventory, pricing, and save behavior as the target runtime contract.

The extracted shop table is authoritative for a vendor's permitted progression band, but it does not provide a fixed
item id for every inventory slot or an explicit Normal/Good/Excellent assignment. Those missing decisions must be
authored and reviewed in generated world data. They must not be recreated through runtime randomness.

Do not parse `MMIXSHOPS.txt`, `MASTERITEMLIST.csv`, or `CONCAT.csv` at runtime. Import them into validated MM9 world
contributions with retained source provenance.

## Terminology

Keep these concepts separate throughout data, code, diagnostics, and UI:

| Term | Meaning |
| --- | --- |
| Source treasure level | MM9 base progression level of an item definition, normally 1 through 5 |
| Shop treasure range | Per-vendor source constraint such as `1,2` or `3,4` |
| Normal/Good/Excellent | Offline MM9 source-quality labels used only while generating overlay data |
| Effective tier | Offline OpenYAMM target tier used to select or author ordinary MM6-MM8-compatible output |
| Concat | MM9 enchantment or special property attached to an eligible item |
| Standard/Special lane | OpenYAMM vendor actions backed by separately authored stock rosters |
| Restock page | A complete deterministic roster selected for one vendor restock interval |

`Wealth` and `Merchant base` do not mean item quality. Wealth is retained as source provenance. Merchant base feeds the
reviewed pricing conversion. Neither field may silently raise or lower an item's progression tier.

## Audited MM9 Shop Baseline

`MMIXSHOPS.txt` contains 48 item-selling vendors:

| MM9 shop type | Count | Required OpenYAMM stock profile |
| --- | ---: | --- |
| Weapon | 8 | Weapons |
| Armor | 8 | Armor |
| Magic | 15 | Existing OpenYAMM spellbooks with an MM9 school filter |
| Apothecary | 5 | Explicit MM9 apothecary assortment |
| General Store | 6 | Explicit MM9 mixed assortment |
| Library | 6 | MM9 Normal-skill books |

Bank, Dock, Tavern, and Town Hall rows are service hosts but are not vendor-stock rows in this goal. Temple and
Training Arena rows are composed as non-stock `HouseEntry` service venues and use shared house-service behavior.

The source shop ranges are location- and vendor-specific:

| Location or vendor group | Raw source treasure range |
| --- | --- |
| Thjorgard shops | 1-2 |
| Sturmford shops | 0-1 |
| Drangheim shops | 0-1 |
| Guberland shops and library | 1-1 |
| Frosgard principal shops | 2-3 |
| The Light of Life library | 1-1 |
| Halfdan's Books library | 2-3 |
| Thronheim principal shops and library | 1-2 |
| Bergthora's Weapons and Cobthach's Armor | 1-1 |
| Lindisfarne shops | 1-2 |
| Ulf's Junk in Yorwick | 3-4 |
| Arslegard equipment, magic, and general shops | 3-4 |
| The Bored Reader in Arslegard | 2-3 |

Both source treasure-range columns currently contain the same range for each selling vendor. Their adjacent concat
percentages sometimes differ, especially in Lindisfarne and Arslegard. Provisionally map the first pair to Standard
stock and the second pair to Special stock, because that is the best structural match to the requested OpenYAMM UI.
Retain that decision as reviewed importer policy and report it explicitly. If executable-backed research proves
different source semantics, update the importer and regenerate the rosters rather than adding a runtime exception.

Raw range `0-1` requires explicit normalization. The current ordinary MM9 item catalogue has no useful shop tier below
L1. Preserve raw zero in provenance, normalize it to an L1 candidate floor for stock authoring, and emit a reviewed
warning in the audit. Do not silently clamp it inside the runtime generator.

## Architectural Decision

Reuse the shared shop transaction pipeline, but make vendor identity and stock policy package-owned data.

```text
MM9 RUDE row with service -2
            |
            v
resolve raw RUDE/NPC shop alias
            |
            v
canonical mounted MM9 vendor record
            |
            v
suspend RUDE -> open shared HouseService UI with LiveGameplay scene policy
            |
            v
shared buy/sell/identify/repair operations over deterministic vendor roster
            |
            v
close vendor -> restore suspended RUDE -> later close RUDE -> OnRudeExit once
```

Do not add a second MM9 inventory, pricing system, shop overlay, item instance, or save subsystem. Do not implement a
hardcoded `switch` from RUDE id to stock type. Do not reuse an unrelated MM6-MM8 house id as an MM9 vendor id.

The shared service runtime currently accepts `HouseEntry`. Prefer composing mounted MM9 vendor/service-venue records
into the same authoritative service table or generalizing that record narrowly. Do not add an adapter layer that owns
a duplicate vendor definition solely to translate into `HouseEntry` at each transaction call.

## Package-Owned Vendor Data

Add a stable vendor id domain to the MM9 manifest. Raw MM9 shop/NPC ids are import aliases, not global ids. Canonical
vendor ids must be stable, declared, collision-checked, and available as keys for party stock persistence.

Use a world-owned layout equivalent to:

```text
assets_dev/worlds/mm9/
  world.yml
  data_tables/
    vendors.txt
    vendor_aliases.txt
    vendor_stock.txt
    vendor_stock_profiles.txt
    vendor_concat_mappings.txt
  state/
    vendor_import_report.yml
    vendor_stock_audit.yml
```

The exact filenames may change if the table registry has a better established name, but ownership must remain this
narrow and explicit.

### Vendor record

Each `vendors` row must retain at least:

- canonical vendor id;
- package id;
- source shop/NPC id;
- source name and location;
- source shop type and merchandise text;
- normalized service type;
- normalized stock profile;
- magic-school filter when applicable;
- source wealth and merchant base;
- Standard source treasure minimum and maximum;
- Standard source concat percentage;
- Special source treasure minimum and maximum;
- Special source concat percentage;
- source restock period;
- normalized restock duration;
- opening-hours policy and its RUDE/SCR provenance;
- supported sell, identify, and repair capabilities;
- dialogue scene policy `LiveGameplay`;
- legacy house audio policy, normally disabled for a RUDE-launched vendor; and
- complete source-file and source-row provenance.

### Vendor alias record

Resolve service opcode `-2` through an explicit alias keyed by mounted package and raw MM9 shop identity. Retain the
source actor index where needed for diagnostics and `OnRudeExit`, but do not use prompt text to infer vendor identity.

Duplicate or ambiguous aliases are composition errors. An unresolved reachable shop row must display a specific
unavailable result containing source provenance; it must not open a generic fallback shop.

## Vendor Type Mapping

Separate transaction capabilities from stock selection. All item-selling MM9 services use the ordinary Shop root even
when their merchandise is spellbooks or skill books.

| MM9 type | Service UI | Stock profile | Notes |
| --- | --- | --- | --- |
| Weapon | Shop | Weapon | Source and normalized weapon categories only |
| Armor | Shop | Armor | Armor, helms, gloves, boots, shields, and belts |
| Magic | Shop | Spellbook | Use existing OpenYAMM spell catalogue; filter by source school text |
| Apothecary | Shop | Mm9Apothecary | Explicit rings, amulets, potions, belts, scrolls, and mapped runestones |
| General Store | Shop | Mm9GeneralStore | Explicit mixed roster; do not approximate it as Alchemist |
| Library | Shop | Mm9Library | Explicit MM9 skill-learning books |

MM9 Magic vendors are not OpenYAMM `Magic Shop` equipment generators and are not guild-membership services. They sell
spells according to `MMIXSHOPS.txt`, so their items come from explicitly mapped existing OpenYAMM spellbooks. MM9
spell identities remain excluded.

Libraries sell Normal-skill books. They do not directly teach skills and do not expose the generic `Learn Skills`
house action. Consuming a purchased book remains the shared `LearnSkill` item operation.

Shop item placement must resolve the explicit stock profile before considering legacy house-type strings. Weapon and
Armor reuse their corresponding layouts. `Mm9Apothecary` uses the six-by-two general shelf, `Mm9GeneralStore` uses a
four-by-two general shelf, and `Mm9Library` uses the six-by-two book shelf. Rendering and pointer hit-testing must use
the same profile mapping and slot geometry; a valid stock page must never become invisible because its MM9 display
type has no legacy MM6-MM8 house-type match.

These shelves now serve only vendors whose `buy_view` is `Shelf` (absent or empty). MM9 vendors use the ledger below.

### Buy view: the ledger (2026-11-05)

Every MM9 vendor row has `buy_view` `Ledger` (vendors.txt column 35, written by `generate_mm9_vendors.py`; other
values are a load error). Buy then lists the stock as MM9's merchant screen did
(`MERCHANT-COORDS.txt`): one scrolling row per kind of item in the shop overlay frame, with icon, name, a count of
identical copies, the inspect popup's type and stat lines and the shop's buy price, filtered by MM9's merchant tabs
(Weapons, Armor, Gloves/Boots, Jewelry, Potions/Misc, plus Books). Sell, Identify, Repair, Display Equipment, the
vendor root and the transactions are unchanged; a click buys the row's first copy through the shared buy and steal
path, hovering gives the merchant's price line and held RMB inspects. Pure model and geometry:
`game/ui/HouseShopLedger.{h,cpp}` (tests in `tests/HouseShopLedgerTests.cpp`); drawing:
`game/ui/GameplayHouseShopLedgerRenderer.cpp`; text styles: `DialogueShopLedger*` in `engine/ui/gameplay/dialogue.yml`.
Design study, original MM9 stock research and mockups: `level_generation/ui/mm9_shop_buy_study_20261105/`.

Sorting (2026-11-06, user request): clicking the Wares heading sorts the list by type (merchant tab order, then the
type line, so swords and axes group; spellbooks by school, then spell order), clicking Price by the buy price. A
second click on the same heading reverses it and a third restores the stock's order; a brass triangle marks the
direction and hovering a heading says what a click does. Equal rows keep the stock's order. The choice lasts for the
shop visit only (`HouseShopOverlayState::ledgerSort`, reset when the overlay opens); MM9's screen had no sorting.

#### Restock size and one list: MM9's rolls (2026-11-06)

The original game rolls 30 items per restock, 15 from each treasure range, with independent picks, into one merchant
container (`object.lto` `fcn.100b8310`; details in the study README); its merchant screen has no Standard/Special
split. `generate_mm9_vendors.py` (stock generation version 2) now does the same: each restock page holds 30 rolls in
the `standard` lane, slots 0-14 from the first range (with the former Standard quality rules and concat percentage)
and 15-29 from the second (the former Special rules). A roll picks a treasure level in the range, turns it into an
item level with MM9's weights (`fcn.100468d0`), restricted to the item levels the range admits, and picks a seeded
random candidate of that level, so copies occur and the ledger groups them. Candidate filters are unchanged; a vendor
has as many pages as the larger of its two former page counts.

The pages are no longer padded to the shelf sizes: for a Ledger vendor the loader accepts 1-64 items per page and no
special rows, while Shelf vendors keep both lanes and the exact sizes of `expectedVendorStockSlotCount`. The runtime
slot count of a vendor-table shop is the size of its largest page. A vendor-table shop without special pages offers a
single `Buy` (the Standard stock mode) instead of `Buy Standard` and `Buy Special`, and its ledger heading reads
"Wares". A restock now offers 2-25 different items (2 at the one-school magic shops whose range admits only two
spellbooks; libraries 9-14, armour 8-21, weapons 7-20), against 2-12 per list before. A saved game keeps its current
stock until the next restock; a saved Special stock of an MM9 shop is no longer reachable.

#### Spellbook shops: one book per spell, school tabs (2026-11-06)

A magic shop stocks each spell at most once per restock (user decision 2026-11-06): a roll that lands on a stocked
spell takes an unstocked one of the nearest level, and the page ends when every spell is stocked. Since 2026-11-08 the
shops sell MM9's own books (`tools/mm9_import_discovery/mm9_spellbooks.py`, items 10901-10999, one per spell, World:mm9)
instead of MM6's: four book designs by the mastery the spell needs (Normal, Expert, Master, Grandmaster), the same for
every school, with the MM6 books' shop tiers, so the shops stock the same spells (stock generation version 6). They
also drop as random loot in MM9, weighted like the same spell's MM8 book. A shop of more schools stocks more books: its
ranges must admit six spells for each school it sells (`SPELLBOOK_SPELLS_PER_SCHOOL`; All 9 schools, Elemental 4,
Spirit 3, Light and Dark 1), else they take the next tier up, then down, instead of copies (`spellbook_vendor`), and
each range rolls up to three books per school (at least MM9's 15). So the first-tier shops of every school
(Magical Touches, The Mage's Hand) offer spells 1-6 of each school, four Normal and two Expert, 54 books; Fre's Rain
24, Frigg's Sprit 18, the one-school shops of Guberland 6, Arslegard's Light and Dark shops 7 (Expert to Grandmaster).
These pools are small enough that each restock now stocks all of them. Spirit shops sell Spirit, Mind and Body books,
the three MM6-MM8 schools MM9's Spirit merged, as they teach them; Elemental shops already sold all four elements.

Since 2026-11-09 (user decision, stock generation version 7) three shops also stock every Expert and Master book of
some schools on each restock, whatever their ranges (`SPELLBOOK_STOCKED_SCHOOLS`): Frosgard's Darkened Towers the Dark
books and The Free Spirit the Spirit, Mind and Body books, and Lindisfarne's Rober's Magic the Fire, Air, Water, Earth
and Light books (Town Portal and Fly among them; the Grandmaster books, Lloyd's Beacon among them, stay in
Arslegard). They open the list and the rolls skip them, so Rober's Magic holds 74 books, Darkened Towers 8 and The Free
Spirit 24; the ledger's page limit is 128 (`MaxLedgerStockPageSlots`).

In the ledger, a stock of spellbooks only is listed in spell order (school by school, Normal to Grandmaster), its tabs
are All and the schools it holds (the chips narrow to share the bar, so nine schools fit), and each book's second line
is its school and the mastery the spell needs ("Fire Magic - Expert") instead of "Book of Learning".

### Transaction capabilities

Define capabilities in data rather than deriving all behavior from a display type string:

| Profile | Buy | Sell | Identify | Repair |
| --- | --- | --- | --- | --- |
| Weapon | Yes | Any item with a value | Yes | Accepted weapon families |
| Armor | Yes | Any item with a value | Yes | Accepted armor families |
| Spellbook | Yes | Any item with a value | Yes | No |
| Mm9Apothecary | Yes | Any item with a value | Yes | No |
| Mm9GeneralStore | Yes | Any item with a value | Yes | Authored policy |
| Mm9Library | Yes | Any item with a value | No | No |

Since 2026-11-12 every MM9 vendor buys any item with a value above 0, like the MM6-MM8 shops; the stock profile
limits only what a vendor stocks, identifies and repairs.

The vendor root must contain the three requested actions. Unsupported nested operations should be omitted rather than
shown as working and then rejected. `Display Equipment` may still open a display-only inventory before the player
chooses a supported sell, identify, or repair operation.

## Deterministic Stock Contract

Runtime stock selection for MM9 vendors must use no random-number generator.

`vendor_stock.txt` must contain one row per concrete runtime stock slot with:

- canonical vendor id;
- lane: Standard or Special;
- deterministic restock page index;
- visual slot index;
- canonical item id;
- quantity;
- optional standard enchant id and power;
- optional concat/special-enchant id;
- identified state;
- stock-generation version.

Source treasure level, source range, concat percentage, import rule, and provenance belong in
`vendor_stock_audit.yml`, not in the runtime table.

Checked-in stock rows are the authority. Runtime code only selects the page for the current restock ordinal and loads
its explicit slots. It does not choose an item, enchantment, power, or quantity randomly. MM9 quality labels and raw
quality power are not runtime columns; the importer has already mapped them to ordinary OpenYAMM item definitions and
enchant fields.

### Deterministic restock pages

Restocking may rotate inventory without becoming random:

1. An offline generator builds a finite, checked-in sequence of pages for every vendor and lane.
2. Candidate ordering uses canonical item id after all category, tier, restriction, and package filters.
3. Page construction uses an explicit algorithm version and stable vendor id, never process RNG or filesystem order.
4. The current page is `restockOrdinal % pageCount`.
5. The restock ordinal advances only after the authored two-week or two-month interval.
6. Save/load persists current stock and restock timing through the existing party stock state.
7. Regeneration produces a diffable audit of every changed slot.

If exact original inventory pages are later recovered, replace generated pages with source-authored rows and retain the
same runtime contract.

### Candidate admission

Every equipment candidate must satisfy all of the following:

- its canonical definition exists in the composed item table;
- its package and source identity are retained;
- it is not `Quest`, `NoShop`, a unique artifact, a relic, or an authored unique/set item;
- its merchandise family matches the vendor profile;
- its raw source treasure level is inside the vendor's normalized source range;
- its normalized base tier is consistent with the imported balance profile;
- its visuals and inventory dimensions pass existing item acceptance gates; and
- its class and proficiency restrictions remain intact.

`NoRandom` is not synonymous with `NoShop`. MM9 skill books intentionally retain `NoRandom` and enter only explicit
Library stock rows. Conversely, `NoShop` always excludes an item unless a separately reviewed quest operation buys it
back for source-specific reasons.

## Offline MM9 Quality Estimation

### Design requirements

The one-time import model must:

- retain MM9's Normal, Good, and Excellent labels only in the import audit;
- keep base item identity and source treasure level unchanged;
- produce deterministic quality per stock slot;
- map the improvement to ordinary MM6-MM8-compatible item ids, enchant ids, powers, and authored values;
- fit OpenYAMM's normalized progression envelopes;
- prevent ordinary shop stock from becoming an artifact or relic;
- place the strongest Excellent shop equipment at effective tier L6; and
- reserve L7 for artifacts, relics, authored unique items, and approved set pieces.

### Effective-tier estimation

Use this reviewed initial model:

| Quality | Tier offset |
| --- | ---: |
| Normal | +0 |
| Good | +1 |
| Excellent | +2 |

```text
effectiveTier = clamp(normalizedBaseTier + qualityOffset, L1, L6)
```

Examples:

| Base item tier | Normal | Good | Excellent |
| ---: | ---: | ---: | ---: |
| L1 | L1 | L2 | L3 |
| L2 | L2 | L3 | L4 |
| L3 | L3 | L4 | L5 |
| L4 | L4 | L5 | L6 |
| L5 | L5 | L6 | L6 |
| L6 | L6 | L6 | L6 |

The source MM9 shop table reaches raw treasure level 4. Therefore a treasure-level-4 Excellent item becomes L6, the
strongest ordinary vendor item and exactly one tier below L7 artifacts/relics. Tier capping does not convert an item
into a rare item and must never set `artifactId`.

Quality estimation does not apply to spellbooks, skill books, readable documents, ordinary consumables, quest items,
or other definitions whose source mechanics do not use equipment quality. Those slots retain their authored base
behavior without a quality marker.

### Source `Q` power

MM9's documented equipment formula derives `Q` from source treasure level and quality:

| Source treasure level | Normal Q | Good Q | Excellent Q |
| ---: | ---: | ---: | ---: |
| 1 | 0 | 1 | 2 |
| 2 | 2 | 3 | 4 |
| 3 | 4 | 5 | 6 |
| 4 | 6 | 7 | 8 |
| 5 | 8 | 9 | 10 |

Retain that source value in the generated import audit only. Do not write raw `Q` or a runtime quality enum into the
overlay tables, and do not add raw Q after normalized OpenYAMM stats have already incorporated equivalent power.

For the initial implementation, derive the generated overlay result from the audited difference between the item's
base-tier role envelope and effective-tier role envelope:

- weapon damage and attack treatment use the weapon's handedness and proficiency envelope;
- armor and shields use the matching armor-class envelope;
- helms, boots, gloves, and belts use their concrete equipment-family envelope;
- value, identification difficulty, and repair difficulty use the effective-tier envelope; and
- jewelry quality is permitted only if its source row uses quality and its normalized effect remains within L6.

The generated report must show source Q, base normalized statistics, effective tier, target envelope, applied delta,
and final overlay statistics. If an item cannot reach the target envelope without changing its intended role, select
a reviewed existing item/enchant mapping or add a reviewed overlay definition rather than a gameplay item-id
conditional.

This avoids both double-counting imported MM9 `Q` power and discarding quality entirely. It also ensures that an L6
Excellent ordinary item remains weaker overall than the weakest comparable L7 artifact or relic after accounting for
unique effects.

### Deterministic quality assignment by shop band

Use the following initial authoring profile. Individual checked-in rows may use reviewed overrides, but runtime code
must not infer quality from location.

| Vendor raw range | Standard lane | Special lane | Maximum effective tier |
| --- | --- | --- | ---: |
| 0-1 | L1 Normal | L1 Good | L2 |
| 1-1 | L1 Normal | L1 Good | L2 |
| 1-2 | L1-L2 Normal | L2 Good, selected L2 Excellent | L4 |
| 2-3 | L2-L3 Normal/Good | L3 Good/Excellent | L5 |
| 3-4 | L3-L4 Good | L4 Excellent | L6 |

Offline quality selection within a page is explicit and balanced by slot:

- Standard pages emphasize base merchandise and progression breadth.
- Special pages emphasize the upper source tier and improved quality.
- An Excellent slot must not duplicate an otherwise identical Good slot on the same page unless source merchandise
  scarcity makes that necessary and the audit records it.
- L6 Excellent stock is limited to the highest source `3-4` vendors and may never contain artifacts, relics, or set
  pieces.
- Libraries and spellbook-only lanes use `NotApplicable`; their source ranges filter book eligibility or spell level,
  not equipment quality.

The initial L6 shop sources are therefore the top L4 Special slots at Ulf's Junk and Arslegard's applicable equipment
and general-store vendors. If Ulf's source merchandise restriction admits no valid L4 candidate for a category, leave
the slot at L5 or empty rather than borrowing an unrelated item.

### Concat estimation and authoring

Concat percentage is a source probability, not item quality. Preserve it separately.

Because runtime stock is deterministic, convert percentages into checked-in roster coverage:

1. Count concat-eligible slots across the complete authored page cycle for one vendor and lane.
2. Compute the target count from the source percentage with a documented largest-remainder rule.
3. Assign exact concat ids and powers offline using item applicability, concat tier, and effective-tier budget.
4. Spread concat slots across pages through a stable authored schedule.
5. Emit expected percentage, realized percentage, slot count, and deviation in the audit.

Zero-percent vendors receive no concatenated stock. Small values such as 2% may require a longer deterministic page
cycle to preserve a nonzero occurrence. Do not silently round every low percentage to zero. A concat may not push an
ordinary L6 item beyond the comparable L6 envelope; select a lower concat tier or lower base item when necessary.

## One-Time Overlay Conversion

Do not add `ItemQuality` to `InventoryItem`, equipped state, saves, inspection UI, or runtime calculations. Normal,
Good, Excellent, and MM9 `Q` are importer concepts only. Generated vendor stock must contain normal OpenYAMM item ids
and the already-supported enchant ids and powers. When a source quality requires base statistics that no existing item
can represent cleanly, add a reviewed MM9 overlay item definition with final MM6-MM8-style values; do not carry the MM9
quality formula into runtime.

Two source-quality variants may therefore resolve to different existing item ids, to different explicit enchants on
the same item id, or to reviewed overlay definitions. The audit retains why. Runtime transactions, inventory,
equipment, pricing, save/load, and rendering remain entirely on the established MM6-MM8 item representation.

## RUDE And Vendor Dialogue Lifecycle

### Entering a vendor

When the player selects a visible RUDE row whose result is service opcode `-2`:

1. Apply the row's authored RUDE actions exactly once.
2. Resolve the canonical vendor through the mounted MM9 alias table.
3. Capture a typed return frame containing the exact RUDE source id, node id, actor index, callback state, selection,
   and required pending/runtime context.
4. Do not execute `OnRudeExit`.
5. Hide the RUDE presentation.
6. Set the canonical vendor as the service host.
7. Open the standard shared shop root with scene policy `LiveGameplay`.

Do not clear and rebuild the RUDE node into an "unimplemented service" state before suspension. Do not use only the
existing house menu-id stack as the parent record; it cannot preserve RUDE actor and callback identity.

### Returning from a vendor

Escape and Back must unwind in this order:

1. Buy/sell/identify/repair overlay to its vendor submenu or root.
2. `Display Equipment` submenu to vendor root.
3. Vendor root to the suspended RUDE dialogue.
4. RUDE close to gameplay.

Returning from the vendor restores the RUDE overlay over live gameplay at the preserved node. It does not return
directly to unrestricted gameplay. Leaving the vendor may perform vendor-specific transaction cleanup, but it must not
play an unrelated legacy house goodbye, execute `OnRudeExit`, or discard the RUDE source actor.

If a transaction or service initiates a map transition, movie, death, or another terminal interaction, define the
return-frame disposition explicitly. It must never leave a hidden active RUDE callback or execute the callback twice.

## Live-Gameplay Shop Presentation

An empty `videoName` is not a no-video implementation. The current standard house renderer reserves a video frame for
any host house and draws a dark placeholder when no frame is available. House dialogue also currently marks the world
as fully occluded.

Add an explicit dialogue scene policy, provisionally:

```text
DialogueScenePolicy::HouseVideo
DialogueScenePolicy::LiveGameplay
```

For MM9 RUDE-launched vendors, `LiveGameplay` must:

- continue indoor or outdoor world rendering through the shared world-render decision;
- select the full shared house-dialogue presentation with its alternate/limited party panel rather than preserving the
  ordinary gameplay HUD used by RUDE;
- render the standard shop dialogue frame and action list across the view;
- omit the house-video layout element entirely;
- avoid starting, updating, or stopping house video playback;
- avoid drawing a dark substitute video rectangle; and
- block world movement and interaction while the shop UI owns input.

The policy belongs to dialogue presentation state, not to `HouseEntry::videoName`, vendor type, active world name, or
an MM9 check in indoor/outdoor renderers.

## Stock Persistence And Restocking

Reuse `Party::HouseStockState` or rename/generalize its authoritative ownership if necessary. Preserve one stable stock
state per canonical vendor id, including Standard, Special, and any book-specific inventory used by the final profile.

Required behavior:

- opening and closing a vendor without reaching its restock time preserves the exact roster and sold-out slots;
- save/load preserves item id, concat/enchant fields, enchant power, quantity, and sold state;
- two-week and two-month periods come from the source vendor record;
- the deterministic page ordinal advances only at a real restock boundary;
- visiting another map or world does not reroll or regenerate the stock;
- remount validation rejects a save whose required vendor or item contribution is unavailable;
- MM6-MM8 house stock remains byte-for-byte behaviorally compatible; and
- MM9 stock is not generated or retained when the MM9 package is not mounted.

Stock generation-version changes require an explicit migration policy. Do not silently replace persisted stock merely
because checked-in page data changed.

The initial migration policy is: preserve a loaded concrete roster, sold slots, and its recorded generation version
until that vendor's already-scheduled restock boundary. At that boundary, advance the normal restock ordinal, load the
corresponding page from the currently mounted stock generation, and record its version. Required-content validation
rejects saves whose versioned vendor definition or stock item package is unavailable.

## Pricing

Reuse shared OpenYAMM buy and sell calculations. Add reviewed data conversion for MM9 `Merchant base`, but retain the
raw value independently.

Pricing must account for:

- normalized base item value;
- the final authored OpenYAMM item value selected by the offline effective-tier conversion;
- concat/enchantment value;
- vendor merchant multiplier;
- active character or party Merchant skill according to shared policy;
- general-store buyback penalty where authored;
- identification and repair charges; and
- reputation or theft policy only where it is intended for MM9 vendors.

Do not use source `Wealth` as a second hidden price multiplier. Quality-derived price changes must already be baked
into the reviewed overlay item/enchant mapping.

## Opening Hours

Many RUDE shop rows already use MM9 key 5017 to choose between an open service row and a closed response. The related
SCR toggles that key around the source day/night boundary.

Use one authoritative opening decision. Prefer the compiled RUDE/SCR condition when it is complete. A vendor record
may retain opening hours for audit and direct-entry validation, but do not apply a second divergent house-hours check
after RUDE has already admitted the service.

Source vendors whose RUDE rows are always available must remain available unless another authoritative source proves a
schedule. Do not infer opening hours from nearby vendors.

## Importer And Audit Tooling

Add a deterministic importer/auditor under `tools/mm9_import_discovery/` that:

- parses every `MMIXSHOPS.txt` row losslessly;
- identifies all item-selling and non-item services;
- cross-checks every selling raw NPC id against an opcode `-2` RUDE row;
- validates vendor ids and aliases against the MM9 manifest range;
- maps source merchandise descriptions through reviewed profile rules;
- resolves every explicit stock item to a canonical mounted item id;
- validates source and normalized tier eligibility;
- validates quality and effective-tier calculations;
- validates that no ordinary slot exceeds L6;
- validates that no artifact, relic, set piece, quest item, or `NoShop` item enters stock;
- validates library coverage and class/race-usable skill-book mappings;
- validates magic-shop school coverage against existing OpenYAMM spellbooks;
- computes deterministic concat coverage and deviation;
- validates slot counts against the selected shop visual layout (Shelf vendors; Ledger vendors take 15 rolls);
- emits source provenance for every normalized field;
- fails on duplicate aliases, unresolved candidates, or nondeterministic ordering; and
- regenerates byte-identical output from identical inputs.

The audit report must contain at least:

- all 48 selling vendors and their disposition;
- every raw and canonical id mapping;
- both raw treasure ranges and concat percentages;
- every stock page and slot;
- item source tier, normalized base tier, quality, effective tier, and concat;
- quality-envelope calculations and final stat/value deltas;
- rejected candidate counts with reasons;
- missing category, library, and magic-school coverage;
- realized concat coverage; and
- every reviewed override with an owner and reason.

## Implementation Sequence

### Phase 1: Data recovery and schema

- Add the MM9 vendor id domain and contribution declarations.
- Implement the lossless `MMIXSHOPS.txt` parser and audit.
- Add reviewed mappings for vendor profiles, location, Standard/Special source-pair interpretation, and raw range zero.
- Generate vendor records and aliases without enabling runtime service behavior.

### Phase 2: Deterministic stock authoring

- Build eligible item inventories from the composed catalogue and source provenance.
- Add explicit Library and mapped spellbook candidates.
- Author or generate deterministic Standard and Special pages.
- Estimate source quality and effective tier offline, then emit only normal OpenYAMM item/enchant fields.
- Assign deterministic concats and validate budget/coverage.
- Review the complete generated stock audit before runtime activation.

### Phase 3: One-time quality conversion

- Add pure importer functions for source quality, source Q, and effective-tier estimation.
- Resolve each estimate to an existing ordinary item/enchant combination or a reviewed MM9 overlay definition.
- Emit no runtime quality field and require byte-identical regenerated tables and audits.
- Add importer coverage before vendor integration.

### Phase 4: Shared vendor runtime

- Compose MM9 vendors into the authoritative service venue table.
- Load explicit stock pages without RNG.
- Reuse shared transaction operations and stable party stock state.
- Add data-owned capabilities for sell, identify, and repair.
- Preserve MM6-MM8 behavior when no MM9 vendor contribution exists.

### Phase 5: RUDE lifecycle and presentation

- Replace opcode `-2` placeholder handling with canonical vendor resolution.
- Add typed suspended-dialogue return state.
- Add `LiveGameplay` scene policy.
- Implement the complete Escape/Back chain.
- Ensure `OnRudeExit` executes exactly once only when RUDE ends.

### Phase 6: Save, migration, and regression hardening

- Persist vendor page ordinal, restock timing, and concrete stock through the existing item representation.
- Validate MM9 remount and cross-world inventory behavior.
- Run focused MM9 tests and affected MM6-MM8 shop/dialogue tests.

## Required Automated Coverage

### Data and importer tests

- All 48 selling rows import with no silently ignored fields.
- Every reachable opcode `-2` shop row resolves one canonical vendor.
- Every canonical vendor has at least one valid enabled action or a specific audited unavailable reason.
- Repeated generation produces byte-identical vendor and stock files.
- Every stock row falls inside its source range and normalized profile.
- All 104 headerless `CONCAT.csv` rows round-trip losslessly in the audit.
- Every authored concat retains its exact source id, row, applicability flags, tier, target mapping, owner, and reason.
- Concat percentages use equipment-eligible slots as the denominator; spellbooks and skill books are ineligible.
- No ordinary stock row has effective tier above L6.
- No L7 artifact, relic, unique set piece, quest item, or `NoShop` item appears in vendor stock.
- Raw `0-1` normalization is preserved and reported.

### Offline quality-conversion tests

- Normal, Good, and Excellent produce offsets 0, 1, and 2.
- Effective tier clamps at L6 and never emits a rare item.
- A base L4 Excellent item is L6.
- A base L5 Excellent item remains L6.
- Quality-bearing source rows emit the audited ordinary item/enchant mapping exactly once.
- Non-quality source rows emit no quality-derived enchant or overlay.
- Runtime stock rows contain no MM9 quality or Q field.
- Comparable L6 ordinary equipment remains below L7 artifacts and relics in the balance audit.

### Stock and transaction tests

- Vendor stock remains unchanged before its restock boundary.
- Restocking advances to the exact next authored page without RNG.
- Sold slots remain sold until restock.
- Standard and Special lanes use their corresponding explicit rows.
- Buy, sell, identify, repair, insufficient-gold, inventory-full, and refusal outcomes remain atomic.
- Library purchases grant the exact skill book and consume it only after successful `LearnSkill` use.
- Magic vendors expose only their authored existing-OpenYAMM spellbook schools.

### Dialogue and rendering tests

- Selecting a RUDE shop row hides RUDE and opens the standard shop root.
- The active world continues rendering behind the full house-dialogue presentation.
- The standard alternate/limited party panel is used instead of the ordinary gameplay HUD retained by RUDE.
- No house video playback or placeholder video rectangle is requested.
- World movement and interaction remain blocked while the vendor is active.
- Closing overlays and submenus follows the required unwind order.
- Closing the vendor restores the exact RUDE id, node, actor, and selection context.
- Entering and leaving the vendor does not execute `OnRudeExit`.
- Closing the restored RUDE dialogue executes `OnRudeExit` exactly once.
- An unresolved vendor fails visibly without closing or corrupting RUDE.

### Regression tests

- Existing MM6-MM8 house videos still render and loop normally.
- Existing house shop stock generation and restocking remain unchanged.
- Existing HouseService menu-stack Escape behavior remains unchanged.
- Existing MM6-MM8 buy, sell, identify, repair, theft, reputation, greeting, and goodbye behavior remains unchanged.
- MM9-unmounted startup, map load, render, update, memory, and save behavior has no meaningful regression.

## Headless Acceptance Scenarios

At minimum, add scenarios for:

1. A low-band Sturmford weapon vendor showing only authored L1 Normal/Good equipment.
2. A Guberland school-specific magic vendor showing only the mapped OpenYAMM school.
3. Frosgard's L2-L3 equipment stock and two-month restock behavior.
4. The Light of Life and Halfdan's Books exposing different skill-book progression bands.
5. Thronheim's main and secondary weapon/armor vendors preserving their different ranges.
6. Ulf's Junk exposing an authored high-level mixed roster without unrelated categories.
7. An Arslegard Special slot containing an L4 Excellent item evaluated as L6, not L7.
8. A zero-concat magic or library vendor producing no enchantment.
9. A low nonzero concat vendor realizing its authored concat only on the intended deterministic page.
10. Save/load while a vendor stock contains Normal, Good, and Excellent items.
11. RUDE -> vendor -> equipment submenu -> sell -> back -> vendor root -> RUDE -> gameplay.
12. `OnRudeExit` executing once across every vendor return and final-close path.

## Completion Gates

This goal is complete only when:

- all 48 MM9 item-selling vendors have canonical world-owned definitions and RUDE bindings;
- every vendor has reviewed deterministic Standard and Special stock or an explicit source-backed exception;
- runtime MM9 vendor stock uses no random-number generator;
- every equipment stock row has an audited offline quality/effective-tier mapping to ordinary runtime fields;
- no ordinary stock item exceeds L6 and no L7 rare item enters shop stock;
- all quality, concat, and pricing calculations are audited and reproducible;
- all six Libraries distribute their reviewed skill-book selections;
- all 15 Magic vendors use existing OpenYAMM spellbooks with correct school filters;
- live-gameplay shop presentation contains no house video or placeholder frame;
- the complete vendor Back/Escape chain restores RUDE correctly;
- `OnRudeExit` is exactly-once on every final RUDE close path;
- concrete stock and restock state survive save/load through existing item fields;
- all focused unit, headless, save/load, and rendering tests pass; and
- affected MM6-MM8 shop, dialogue, video, item, and save tests pass without regression.

## Explicit Non-Goals

- Recreating the original MM9 merchant inventory screen as a whole (its two-book Buy/Sell layout). Only its scrolling
  merchant list returned, as the ledger Buy view above.
- Adding MM9 spell identities, spell scroll definitions, potions, runestones, or wands as a second catalogue.
- Making artifacts, relics, set pieces, or quest equipment ordinary vendor stock.
- Runtime parsing of extracted MM9 design files.
- Runtime random selection of MM9 vendor items, quality, concats, or quantities.
- Guessing exact original stock slots where no source survives without recording a reviewed authored policy.
- Adding a second MM9-only item, inventory, pricing, dialogue, shop, renderer, or save runtime.
- Changing ordinary MM6-MM8 house video or stock behavior merely to accommodate MM9 presentation.

## Completion Evidence

- `python3 -m unittest tools/mm9_import_discovery/test_generate_mm9_vendors.py`: 2/2 passed.
- The checked-in concat mapping covers 238 deterministic equipment slots through exact `CONCAT.csv` source rows;
  all 104 source rows are retained losslessly and all generated mappings pass applicability and tier-budget checks.
- Focused mounted-data, vendor persistence, RUDE lifecycle, unavailable-vendor, exactly-once callback, and
  live-presentation coverage: 293/293 assertions passed.
- `build/tests/openyamm_unit_tests --test-case="*shop*"`: 16/16 cases and 9,096/9,096 assertions passed.
- `build/tests/openyamm_unit_tests --test-case="*house*"`: 37/37 cases and 747/747 assertions passed.
- MM9-unmounted house composition coverage proves no vendor definitions, aliases, service venues, or deterministic
  stock are loaded by the default MM8 composition.
- `cmake --build build --target openyamm -j25`: passed.
- Broad `*MM9*` coverage: 65/68 cases and 2,497/2,502 assertions passed. The three unrelated failures are the
  pre-existing quest-interaction-count, Old Man generated-event, and arming-doublet fixtures; none exercise vendors,
  shop transactions, RUDE vendor return, vendor rendering, or vendor persistence.

#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
// MM9's merchant tabs (MERCHANT-COORDS.txt) as filters of a Ledger shop's list (HouseShopLedger), plus Books for
// spellbooks and skill books, the nine magic schools for a shop that sells spellbooks of several, and the kinds of
// weapon and armour for a shop that sells only weapons or only armour.
enum class HouseShopLedgerCategory : uint8_t
{
    All = 0,
    Weapons,
    Armor,
    GlovesBoots,
    Jewelry,
    PotionsMisc,
    Books,
    FireBooks,
    AirBooks,
    WaterBooks,
    EarthBooks,
    SpiritBooks,
    MindBooks,
    BodyBooks,
    LightBooks,
    DarkBooks,
    Swords,
    Daggers,
    Axes,
    Spears,
    Maces,
    Staves,
    Bows,
    Blasters,
    BodyArmor,
    Shields,
    Helms,
    Belts,
    Cloaks,
};

// The order of a Ledger shop's list, chosen by clicking a column heading for the rest of the visit: the stock's own
// order (a magic shop's: spell order), by item type (Wares) or by price (Price).
enum class HouseShopLedgerSortKey : uint8_t
{
    Stock = 0,
    Type,
    Price,
};

struct HouseShopLedgerSort
{
    HouseShopLedgerSortKey key = HouseShopLedgerSortKey::Stock;
    bool descending = false;
};
}

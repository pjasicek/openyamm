#include "game/ui/HouseShopLedger.h"

#include "game/tables/ItemTable.h"

#include "engine/Localization.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <tuple>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
using Rect = GameplayResolvedHudLayoutElement;

constexpr int SpellsPerSchool = 11;
constexpr int SchoolCount = 9;

bool contains(const Rect &rect, float x, float y)
{
    return x >= rect.x && x < rect.x + rect.width && y >= rect.y && y < rect.y + rect.height;
}

// Two stock entries share a row when nothing the player could tell apart differs; grid placement does not count.
bool sameKind(const InventoryItem &left, const InventoryItem &right)
{
    InventoryItem a = left;
    InventoryItem b = right;
    a.gridX = b.gridX = 0;
    a.gridY = b.gridY = 0;
    return a == b;
}
}

const char *houseShopLedgerCategoryLabel(HouseShopLedgerCategory category)
{
    // English, shown through tr().
    switch (category)
    {
        case HouseShopLedgerCategory::All:
            return Engine::trNoop("All").data();
        case HouseShopLedgerCategory::Weapons:
            return Engine::trNoop("Weapons").data();
        case HouseShopLedgerCategory::Armor:
            return Engine::trNoop("Armor").data();
        case HouseShopLedgerCategory::GlovesBoots:
            return Engine::trNoop("Gloves/Boots").data();
        case HouseShopLedgerCategory::Jewelry:
            return Engine::trNoop("Jewelry").data();
        case HouseShopLedgerCategory::PotionsMisc:
            return Engine::trNoop("Potions/Misc").data();
        case HouseShopLedgerCategory::Books:
            return Engine::trNoop("Books").data();
        case HouseShopLedgerCategory::FireBooks:
            return Engine::trNoop("Fire").data();
        case HouseShopLedgerCategory::AirBooks:
            return Engine::trNoop("Air").data();
        case HouseShopLedgerCategory::WaterBooks:
            return Engine::trNoop("Water").data();
        case HouseShopLedgerCategory::EarthBooks:
            return Engine::trNoop("Earth").data();
        case HouseShopLedgerCategory::SpiritBooks:
            return Engine::trNoop("Spirit").data();
        case HouseShopLedgerCategory::MindBooks:
            return Engine::trNoop("Mind").data();
        case HouseShopLedgerCategory::BodyBooks:
            return Engine::trNoop("Body").data();
        case HouseShopLedgerCategory::LightBooks:
            return Engine::trNoop("Light").data();
        case HouseShopLedgerCategory::DarkBooks:
            return Engine::trNoop("Dark").data();
        case HouseShopLedgerCategory::Swords:
            return Engine::trNoop("Swords").data();
        case HouseShopLedgerCategory::Daggers:
            return Engine::trNoop("Daggers").data();
        case HouseShopLedgerCategory::Axes:
            return Engine::trNoop("Axes").data();
        case HouseShopLedgerCategory::Spears:
            return Engine::trNoop("Spears").data();
        case HouseShopLedgerCategory::Maces:
            return Engine::trNoop("Maces").data();
        case HouseShopLedgerCategory::Staves:
            return Engine::trNoop("Staves").data();
        case HouseShopLedgerCategory::Bows:
            return Engine::trNoop("Bows").data();
        case HouseShopLedgerCategory::Blasters:
            return Engine::trNoop("Blasters").data();
        case HouseShopLedgerCategory::BodyArmor:
            return Engine::trNoop("Body Armor").data();
        case HouseShopLedgerCategory::Shields:
            return Engine::trNoop("Shields").data();
        case HouseShopLedgerCategory::Helms:
            return Engine::trNoop("Helms").data();
        case HouseShopLedgerCategory::Belts:
            return Engine::trNoop("Belts").data();
        case HouseShopLedgerCategory::Cloaks:
            return Engine::trNoop("Cloaks").data();
    }

    return "";
}

std::optional<int> houseShopLedgerSpellNumber(const ItemDefinition &definition)
{
    if (definition.equipStat != "Book" || definition.mod1.size() < 2 || definition.mod1[0] != 'S')
    {
        return std::nullopt;
    }

    int number = 0;

    for (size_t index = 1; index < definition.mod1.size(); ++index)
    {
        if (!std::isdigit(static_cast<unsigned char>(definition.mod1[index])))
        {
            return std::nullopt;
        }

        number = number * 10 + (definition.mod1[index] - '0');
    }

    return number >= 1 && number <= SpellsPerSchool * SchoolCount ? std::optional<int>(number) : std::nullopt;
}

std::optional<HouseShopLedgerCategory> houseShopLedgerSpellSchoolOf(const ItemDefinition &definition)
{
    const std::optional<int> spell = houseShopLedgerSpellNumber(definition);

    if (!spell)
    {
        return std::nullopt;
    }

    return HouseShopLedgerCategory(int(HouseShopLedgerCategory::FireBooks) + (*spell - 1) / SpellsPerSchool);
}

std::string houseShopLedgerSpellbookLine(const ItemDefinition &definition)
{
    const std::optional<int> spell = houseShopLedgerSpellNumber(definition);

    if (!spell)
    {
        return {};
    }

    // MM6-MM8 spells by their place in the school: 1-4 Normal, 5-7 Expert, 8-10 Master, 11 Grandmaster.
    const int place = (*spell - 1) % SpellsPerSchool + 1;
    const char *pMastery = place <= 4 ? "Normal" : place <= 7 ? "Expert" : place <= 10 ? "Master" : "Grandmaster";
    const std::string skill = std::string(houseShopLedgerCategoryLabel(*houseShopLedgerSpellSchoolOf(definition)))
        + " Magic";
    return Engine::tr("{skill} - {mastery}",
                      {{"skill", Engine::localize(skill, "skill")}, {"mastery", Engine::localize(pMastery, "mastery")}});
}

HouseShopLedgerCategory houseShopLedgerCategoryOf(const ItemDefinition &definition)
{
    const std::string &equip = definition.equipStat;

    // Wands are not the weapon smith's goods in MM9; they stay with potions and scrolls.
    if (equip == "Weapon" || equip == "Weapon1or2" || equip == "Weapon2" || equip == "Missile")
    {
        return HouseShopLedgerCategory::Weapons;
    }

    if (equip == "Armor" || equip == "Shield" || equip == "Helm" || equip == "Belt" || equip == "Cloak")
    {
        return HouseShopLedgerCategory::Armor;
    }

    if (equip == "Gauntlets" || equip == "Boots")
    {
        return HouseShopLedgerCategory::GlovesBoots;
    }

    if (equip == "Ring" || equip == "Amulet")
    {
        return HouseShopLedgerCategory::Jewelry;
    }

    if (equip == "Book" || equip == "LearnSkill")
    {
        return HouseShopLedgerCategory::Books;
    }

    return HouseShopLedgerCategory::PotionsMisc;
}

std::optional<HouseShopLedgerCategory> houseShopLedgerKindOf(const ItemDefinition &definition)
{
    const std::string &equip = definition.equipStat;
    const std::string &skill = definition.skillGroup;
    const HouseShopLedgerCategory category = houseShopLedgerCategoryOf(definition);

    if (category == HouseShopLedgerCategory::Weapons)
    {
        // By the skill that wields it: MM9's halberds are Spear, its hammers Mace.
        constexpr std::array<std::pair<const char *, HouseShopLedgerCategory>, 9> WeaponKinds = {{
            {"Sword", HouseShopLedgerCategory::Swords},
            {"Dagger", HouseShopLedgerCategory::Daggers},
            {"Axe", HouseShopLedgerCategory::Axes},
            {"Spear", HouseShopLedgerCategory::Spears},
            {"Mace", HouseShopLedgerCategory::Maces},
            {"Club", HouseShopLedgerCategory::Maces},
            {"Staff", HouseShopLedgerCategory::Staves},
            {"Bow", HouseShopLedgerCategory::Bows},
            {"Blaster", HouseShopLedgerCategory::Blasters},
        }};

        for (const auto &[pSkill, kind] : WeaponKinds)
        {
            if (skill == pSkill)
            {
                return kind;
            }
        }

        return std::nullopt;
    }

    if (category == HouseShopLedgerCategory::Armor)
    {
        if (equip == "Armor")
        {
            return HouseShopLedgerCategory::BodyArmor;
        }

        if (equip == "Shield")
        {
            return HouseShopLedgerCategory::Shields;
        }

        if (equip == "Helm")
        {
            return HouseShopLedgerCategory::Helms;
        }

        if (equip == "Belt")
        {
            return HouseShopLedgerCategory::Belts;
        }

        if (equip == "Cloak")
        {
            return HouseShopLedgerCategory::Cloaks;
        }
    }

    return std::nullopt;
}

HouseShopLedgerModel buildHouseShopLedgerModel(
    const std::vector<InventoryItem> &stock,
    size_t slotCount,
    const ItemTable &itemTable,
    HouseShopLedgerCategory requestedFilter)
{
    HouseShopLedgerModel model = {};
    std::vector<HouseShopLedgerRow> allRows;
    const size_t end = std::min(slotCount, stock.size());

    for (size_t index = 0; index < end; ++index)
    {
        const InventoryItem &item = stock[index];
        const ItemDefinition *pDefinition = item.objectDescriptionId != 0 ? itemTable.get(item.objectDescriptionId)
                                                                           : nullptr;

        if (pDefinition == nullptr)
        {
            continue;
        }

        ++model.itemsForSale;
        const auto row = std::find_if(allRows.begin(), allRows.end(),
            [&stock, &item](const HouseShopLedgerRow &candidate)
            {
                return sameKind(stock[candidate.stockIndices.front()], item);
            });

        if (row != allRows.end())
        {
            row->stockIndices.push_back(index);
            ++model.copiesGrouped;
            continue;
        }

        HouseShopLedgerRow newRow = {};
        newRow.stockIndices.push_back(index);
        newRow.category = houseShopLedgerCategoryOf(*pDefinition);
        newRow.school = houseShopLedgerSpellSchoolOf(*pDefinition);
        newRow.kind = houseShopLedgerKindOf(*pDefinition);
        newRow.spellNumber = houseShopLedgerSpellNumber(*pDefinition).value_or(0);
        allRows.push_back(std::move(newRow));
    }

    // Chips follow MM9's tab order.
    constexpr std::array<HouseShopLedgerCategory, 6> TabOrder = {
        HouseShopLedgerCategory::Weapons,
        HouseShopLedgerCategory::Armor,
        HouseShopLedgerCategory::GlovesBoots,
        HouseShopLedgerCategory::Jewelry,
        HouseShopLedgerCategory::PotionsMisc,
        HouseShopLedgerCategory::Books,
    };
    std::vector<HouseShopLedgerChip> categoryChips;

    for (HouseShopLedgerCategory category : TabOrder)
    {
        const size_t count = size_t(std::count_if(allRows.begin(), allRows.end(),
            [category](const HouseShopLedgerRow &row) { return row.category == category; }));

        if (count > 0)
        {
            categoryChips.push_back({category, count});
        }
    }

    // Spellbooks only (a magic shop): their schools are the tabs, and the books go in spell order.
    const bool spellbooksOnly = !allRows.empty() && std::all_of(allRows.begin(), allRows.end(),
        [](const HouseShopLedgerRow &row) { return row.school.has_value(); });

    if (spellbooksOnly)
    {
        std::stable_sort(allRows.begin(), allRows.end(),
            [](const HouseShopLedgerRow &left, const HouseShopLedgerRow &right)
            {
                return left.spellNumber < right.spellNumber;
            });
        categoryChips.clear();

        for (int school = int(HouseShopLedgerCategory::FireBooks); school <= int(HouseShopLedgerCategory::DarkBooks);
             ++school)
        {
            const HouseShopLedgerCategory category = HouseShopLedgerCategory(school);
            const size_t count = size_t(std::count_if(allRows.begin(), allRows.end(),
                [category](const HouseShopLedgerRow &row) { return row.school == category; }));

            if (count > 0)
            {
                categoryChips.push_back({category, count});
            }
        }
    }

    // Weapons only or armour only (a smith): their kinds are the tabs, in the order of the enum.
    if (!spellbooksOnly && categoryChips.size() == 1)
    {
        std::vector<HouseShopLedgerChip> kindChips;

        for (int kind = int(HouseShopLedgerCategory::Swords); kind <= int(HouseShopLedgerCategory::Cloaks); ++kind)
        {
            const HouseShopLedgerCategory category = HouseShopLedgerCategory(kind);
            const size_t count = size_t(std::count_if(allRows.begin(), allRows.end(),
                [category](const HouseShopLedgerRow &row) { return row.kind == category; }));

            if (count > 0)
            {
                kindChips.push_back({category, count});
            }
        }

        categoryChips = std::move(kindChips);
    }

    if (categoryChips.size() > 1)
    {
        model.chips.push_back({HouseShopLedgerCategory::All, allRows.size()});
        model.chips.insert(model.chips.end(), categoryChips.begin(), categoryChips.end());
    }

    const bool filterPresent = std::any_of(model.chips.begin(), model.chips.end(),
        [requestedFilter](const HouseShopLedgerChip &chip) { return chip.category == requestedFilter; });
    model.filter = filterPresent ? requestedFilter : HouseShopLedgerCategory::All;

    for (HouseShopLedgerRow &row : allRows)
    {
        if (model.filter == HouseShopLedgerCategory::All || row.category == model.filter || row.school == model.filter
            || row.kind == model.filter)
        {
            model.rows.push_back(std::move(row));
        }
    }

    return model;
}

HouseShopLedgerSort nextHouseShopLedgerSort(HouseShopLedgerSort current, HouseShopLedgerSortKey clicked)
{
    if (clicked == HouseShopLedgerSortKey::Stock || current.key != clicked)
    {
        return {clicked, false};
    }

    if (!current.descending)
    {
        return {clicked, true};
    }

    return {};
}

void sortHouseShopLedgerRows(std::vector<HouseShopLedgerRow> &rows, HouseShopLedgerSort sort)
{
    if (sort.key == HouseShopLedgerSortKey::Stock)
    {
        return;
    }

    const auto before = [sort](const HouseShopLedgerRow &left, const HouseShopLedgerRow &right)
    {
        if (sort.key == HouseShopLedgerSortKey::Price)
        {
            return left.price < right.price;
        }

        // Spellbooks go school by school in spell order (Normal before Expert), not by their type line's words.
        const int leftSchool = left.school ? int(*left.school) : 0;
        const int rightSchool = right.school ? int(*right.school) : 0;
        const std::string &leftType = left.school ? std::string() : left.typeText;
        const std::string &rightType = right.school ? std::string() : right.typeText;
        return std::tie(left.category, leftSchool, leftType, left.spellNumber)
            < std::tie(right.category, rightSchool, rightType, right.spellNumber);
    };
    std::stable_sort(rows.begin(), rows.end(),
        [&before, sort](const HouseShopLedgerRow &left, const HouseShopLedgerRow &right)
        {
            return sort.descending ? before(right, left) : before(left, right);
        });
}

HouseShopLedgerLayout buildHouseShopLedgerLayout(const Rect &frame)
{
    using namespace HouseShopLedgerMetrics;
    const float s = frame.scale;
    HouseShopLedgerLayout layout = {};
    layout.panel = frame;
    const float left = frame.x + ContentInset * s;
    const float top = frame.y + ContentInset * s;
    const float width = std::max(0.0f, frame.width - 2 * ContentInset * s);
    const float bottom = frame.y + frame.height - ContentInset * s;
    layout.chipBar = {left, top, width, ChipHeight * s, s};
    layout.columns = {left, top + (ChipHeight + 3) * s, width, ColumnsHeight * s, s};
    const float listTop = layout.columns.y + (ColumnsHeight + 2) * s;
    layout.footer = {left, bottom - FooterHeight * s, width, FooterHeight * s, s};
    const float listHeight = std::max(0.0f, layout.footer.y - 2 * s - listTop);
    layout.rowHeight = RowHeight * s;
    layout.visibleRows = layout.rowHeight > 0 ? size_t(std::floor(listHeight / layout.rowHeight)) : 0;
    // The list is exactly its whole rows tall, so the scrollbar track ends with the last row.
    layout.list = {left, listTop, width, float(layout.visibleRows) * layout.rowHeight, s};
    return layout;
}

std::vector<Rect> houseShopLedgerChipRects(const HouseShopLedgerLayout &layout, size_t chipCount)
{
    using namespace HouseShopLedgerMetrics;
    std::vector<Rect> rects;
    const float s = layout.chipBar.scale;

    // Chips narrow to share the bar when there are many (a magic shop's nine schools), down to MinimumChipWidth;
    // the ones past the bar are left out.
    const float shared = chipCount > 0
        ? (layout.chipBar.width / s - float(chipCount - 1) * ChipGap) / float(chipCount) : ChipWidth;
    const float chipWidth = std::clamp(shared, MinimumChipWidth, ChipWidth);

    for (size_t index = 0; index < chipCount; ++index)
    {
        const float x = layout.chipBar.x + float(index) * (chipWidth + ChipGap) * s;

        if (x + chipWidth * s > layout.chipBar.x + layout.chipBar.width + 0.5f)
        {
            break;
        }

        rects.push_back({x, layout.chipBar.y, chipWidth * s, layout.chipBar.height, s});
    }

    return rects;
}

size_t houseShopLedgerMaximumFirstRow(const HouseShopLedgerLayout &layout, size_t rowCount)
{
    return rowCount > layout.visibleRows ? rowCount - layout.visibleRows : 0;
}

std::vector<HouseShopLedgerRowRect> houseShopLedgerVisibleRows(
    const HouseShopLedgerLayout &layout,
    size_t rowCount,
    size_t firstRow)
{
    std::vector<HouseShopLedgerRowRect> rows;
    firstRow = std::min(firstRow, houseShopLedgerMaximumFirstRow(layout, rowCount));
    const float scrollbar = rowCount > layout.visibleRows ? HouseShopLedgerMetrics::ScrollbarWidth * layout.list.scale
                                                          : 0.0f;

    for (size_t shown = 0; shown < layout.visibleRows && firstRow + shown < rowCount; ++shown)
    {
        rows.push_back({firstRow + shown,
            {layout.list.x, layout.list.y + float(shown) * layout.rowHeight, layout.list.width - scrollbar,
                layout.rowHeight, layout.list.scale}});
    }

    return rows;
}

std::optional<size_t> houseShopLedgerRowAt(
    const HouseShopLedgerLayout &layout,
    size_t rowCount,
    size_t firstRow,
    float x,
    float y)
{
    for (const HouseShopLedgerRowRect &row : houseShopLedgerVisibleRows(layout, rowCount, firstRow))
    {
        if (contains(row.rect, x, y))
        {
            return row.rowIndex;
        }
    }

    return std::nullopt;
}

std::optional<size_t> houseShopLedgerChipAt(const HouseShopLedgerLayout &layout, size_t chipCount, float x, float y)
{
    const std::vector<Rect> rects = houseShopLedgerChipRects(layout, chipCount);

    for (size_t index = 0; index < rects.size(); ++index)
    {
        if (contains(rects[index], x, y))
        {
            return index;
        }
    }

    return std::nullopt;
}

HouseShopLedgerColumnRects houseShopLedgerColumnRects(const HouseShopLedgerLayout &layout)
{
    using namespace HouseShopLedgerMetrics;
    const Rect &columns = layout.columns;
    const float s = columns.scale;
    const float right = layout.list.x + layout.list.width - (ScrollbarWidth + 4) * s;
    const float statX = right - (PriceWidth + StatWidth) * s;
    HouseShopLedgerColumnRects rects = {};
    rects.wares = {columns.x + (IconWell + 8) * s, columns.y, statX - columns.x - (IconWell + 8 + 4) * s,
        columns.height, s};
    rects.stat = {statX, columns.y, StatWidth * s, columns.height, s};
    rects.price = {right - PriceWidth * s, columns.y, PriceWidth * s, columns.height, s};
    return rects;
}

std::optional<HouseShopLedgerSortKey> houseShopLedgerColumnAt(const HouseShopLedgerLayout &layout, float x, float y)
{
    const HouseShopLedgerColumnRects rects = houseShopLedgerColumnRects(layout);

    if (contains(rects.wares, x, y))
    {
        return HouseShopLedgerSortKey::Type;
    }

    if (contains(rects.price, x, y))
    {
        return HouseShopLedgerSortKey::Price;
    }

    return std::nullopt;
}

bool houseShopLedgerOnScrollbar(const HouseShopLedgerLayout &layout, float x, float y)
{
    const float width = HouseShopLedgerMetrics::ScrollbarWidth * layout.list.scale;
    return contains({layout.list.x + layout.list.width - width, layout.list.y, width, layout.list.height,
        layout.list.scale}, x, y);
}
}

#include "game/rules/LootFilter.h"

#include "engine/Localization.h"

#include <algorithm>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
// The study's presets (level_generation/ui/maw_loot_progress_20261025/index.html PRESETS), by RulesetLootFilterPreset.
// The names here are English; the window translates them where it shows them.
const std::array<LootFilterPresetDefinition, 6> Presets = {{
    {Engine::trNoop("Every drop stays an item.").data(), 0, {}},
    {Engine::trNoop("Plain Common weapons and armour only. A first game.").data(), 1, {{{1, 30}, {1, 30}, {0, 0}}}},
    {Engine::trNoop("Common and Uncommon gear; Rare once 20 levels behind.").data(), 2, {{{2, 20}, {2, 20}, {1, 20}}}},
    {Engine::trNoop("Gear up to Rare, Epic once 20 levels behind; scrolls too.").data(), 3,
        {{{3, 20}, {3, 20}, {2, 20}}}},
    {Engine::trNoop("Only Ancient and Primordial gear stays; wands and scrolls go. Late game.").data(), 4,
        {{{4, 30}, {4, 30}, {3, 20}}}},
    {Engine::trNoop("Your own rules, from the preset you had.").data(), -1, {}},
}};
}

const LootFilterPresetDefinition &lootFilterPreset(RulesetLootFilterPreset preset)
{
    return Presets[std::min<size_t>(size_t(preset), Presets.size() - 1)];
}

const char *lootFilterGroupName(LootFilterGroup group)
{
    constexpr std::array<std::string_view, LootFilterGroupCount> Names = {
        Engine::trNoop("Weapons"), Engine::trNoop("Armour"), Engine::trNoop("Jewellery")};
    return Names[size_t(group)].data();
}

const char *lootFilterRarityName(int rarity)
{
    constexpr std::array<std::string_view, LootFilterRarityCount> Names = {Engine::trNoop("Common"),
        Engine::trNoop("Uncommon"), Engine::trNoop("Rare"), Engine::trNoop("Epic"), Engine::trNoop("Ancient"),
        Engine::trNoop("Primordial")};
    return rarity >= 1 && rarity <= LootFilterRarityCount ? Names[size_t(rarity - 1)].data() : "";
}

const char *lootFilterKindName(RulesetLootKind kind)
{
    constexpr std::array<std::string_view, RulesetLootKindCount> Names = {Engine::trNoop("Wands"),
        Engine::trNoop("Scrolls"), Engine::trNoop("Potions"), Engine::trNoop("Reagents"), Engine::trNoop("Gems")};
    return Names[size_t(kind)].data();
}

// The cell's English, compared by the window and the tests; the window shows its translation.
std::string lootFilterCellText(RulesetLootFilterPreset preset, LootFilterGroup group, int rarity)
{
    const LootFilterPresetColumn &column = lootFilterPreset(preset).columns[size_t(group)];

    if (rarity <= column.goldUpTo)
    {
        return "gold";
    }

    if (rarity == column.goldUpTo + 1 && column.levelGap > 0)
    {
        return "gold if " + std::to_string(column.levelGap) + "+ levels below";
    }

    return "keep";
}

LootFilterVerdict evaluateLootFilter(const RulesetLootFilter &filter, const LootFilterFacts &facts, int partyLevel)
{
    bool filtered = false;

    if (facts.alwaysKept)
    {
        return LootFilterVerdict::Keep;
    }

    if (facts.kind)
    {
        filtered = filter.turnsKindIntoGold(*facts.kind);
    }
    else if (facts.group && facts.rarity > 0)
    {
        const LootFilterPresetColumn &column = lootFilterPreset(filter.preset).columns[size_t(*facts.group)];
        filtered = facts.rarity <= column.goldUpTo
            || (facts.rarity == column.goldUpTo + 1 && column.levelGap > 0 && facts.itemLevel > 0
                && partyLevel - facts.itemLevel >= column.levelGap);
    }

    if (!filtered)
    {
        return LootFilterVerdict::Keep;
    }

    return filter.leaveOnGround ? LootFilterVerdict::Ground : LootFilterVerdict::Gold;
}

bool isSellTrash(const LootFilterFacts &facts, int partyLevel)
{
    if (facts.alwaysKept)
    {
        return false;
    }

    if (facts.kind)
    {
        return *facts.kind == RulesetLootKind::Gems;
    }

    if (!facts.group || facts.rarity <= 0)
    {
        return false;
    }

    // Rarities up to alwaysUpTo always go, the next one 10+ levels below the party and the one after 20+ below.
    const int alwaysUpTo = *facts.group == LootFilterGroup::Jewellery ? 1 : 2;
    const int levelsBelow = facts.itemLevel > 0 ? partyLevel - facts.itemLevel : 0;

    if (facts.rarity <= alwaysUpTo)
    {
        return true;
    }

    if (facts.rarity == alwaysUpTo + 1)
    {
        return levelsBelow >= 10;
    }

    return facts.rarity == alwaysUpTo + 2 && levelsBelow >= 20;
}

void RecentLootDrops::add(const RecentLootDrop &drop)
{
    m_drops.push_back(drop);

    while (m_drops.size() > MaxDrops)
    {
        m_drops.pop_front();
    }
}

const std::deque<RecentLootDrop> &RecentLootDrops::drops() const
{
    return m_drops;
}

LootFilterTrial tryLootFilter(const RulesetLootFilter &filter, const std::deque<RecentLootDrop> &drops)
{
    LootFilterTrial trial;
    trial.drops = drops.size();

    for (const RecentLootDrop &drop : drops)
    {
        if (evaluateLootFilter(filter, drop.facts, drop.partyLevel) != LootFilterVerdict::Keep)
        {
            ++trial.filtered;
            trial.gold += drop.gold;
        }
    }

    return trial;
}
}

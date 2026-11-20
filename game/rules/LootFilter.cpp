#include "game/rules/LootFilter.h"

#include "engine/Localization.h"

#include <algorithm>
#include <span>
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

const char *lootItemTypeName(LootItemType type)
{
    constexpr std::array<std::string_view, LootItemTypeCount> Names = {Engine::trNoop("Sword"),
        Engine::trNoop("Dagger"), Engine::trNoop("Axe"), Engine::trNoop("Spear"), Engine::trNoop("Mace"),
        Engine::trNoop("Club"), Engine::trNoop("Staff"), Engine::trNoop("Bow"), Engine::trNoop("Throwing"),
        Engine::trNoop("Leather"), Engine::trNoop("Chain"), Engine::trNoop("Plate"), Engine::trNoop("Shield"),
        Engine::trNoop("Helm"), Engine::trNoop("Belt"), Engine::trNoop("Cloak"), Engine::trNoop("Gauntlets"),
        Engine::trNoop("Boots"), Engine::trNoop("Ring"), Engine::trNoop("Amulet"), Engine::trNoop("Wands"),
        Engine::trNoop("Scrolls"), Engine::trNoop("Potions"), Engine::trNoop("Reagents"), Engine::trNoop("Gems")};
    return size_t(type) < Names.size() ? Names[size_t(type)].data() : "";
}

std::optional<LootItemType> lootItemType(const std::string &equipStat, const std::string &skillGroup)
{
    struct Named
    {
        std::string_view name;
        LootItemType type;
    };
    // Weapons and body armour by their skill; the other slots and the kinds by their equip stat.
    static constexpr std::array<Named, 12> BySkill = {{{"Sword", LootItemType::Sword},
        {"Dagger", LootItemType::Dagger}, {"Axe", LootItemType::Axe}, {"Spear", LootItemType::Spear},
        {"Mace", LootItemType::Mace}, {"Club", LootItemType::Club}, {"Staff", LootItemType::Staff},
        {"Bow", LootItemType::Bow}, {"Throwing", LootItemType::Throwing}, {"Leather", LootItemType::Leather},
        {"Chain", LootItemType::Chain}, {"Plate", LootItemType::Plate}}};
    static constexpr std::array<Named, 14> ByStat = {{{"Shield", LootItemType::Shield},
        {"Helm", LootItemType::Helm}, {"Belt", LootItemType::Belt}, {"Cloak", LootItemType::Cloak},
        {"Gauntlets", LootItemType::Gauntlets}, {"Boots", LootItemType::Boots}, {"Ring", LootItemType::Ring},
        {"Amulet", LootItemType::Amulet}, {"WeaponW", LootItemType::Wands}, {"Sscroll", LootItemType::Scrolls},
        {"Bottle", LootItemType::Potions}, {"Reagent", LootItemType::Reagents}, {"Herb", LootItemType::Reagents},
        {"Gem", LootItemType::Gems}}};
    const bool bySkill = equipStat == "Weapon" || equipStat == "Weapon2" || equipStat == "Weapon1or2"
        || equipStat == "Missile" || equipStat == "Armor";

    for (const Named &named : bySkill ? std::span<const Named>(BySkill) : std::span<const Named>(ByStat))
    {
        if ((bySkill ? skillGroup : equipStat) == named.name)
        {
            return named.type;
        }
    }

    return std::nullopt;
}

uint32_t lootItemTypesOfGroup(LootFilterGroup group)
{
    const auto range = [](LootItemType first, LootItemType last)
    { return ((1u << (unsigned(last) + 1)) - 1) & ~((1u << unsigned(first)) - 1); };

    switch (group)
    {
        case LootFilterGroup::Weapons:
            return range(LootItemType::Sword, LootItemType::Throwing);
        case LootFilterGroup::Armour:
            return range(LootItemType::Leather, LootItemType::Boots);
        case LootFilterGroup::Jewellery:
            return range(LootItemType::Ring, LootItemType::Amulet);
    }

    return 0;
}

uint32_t lootItemTypesWithoutRarity()
{
    return ((1u << LootItemTypeCount) - 1) & ~((1u << unsigned(LootItemType::Wands)) - 1);
}

RulesetLootFilter lootFilterAsCustom(const RulesetLootFilter &filter)
{
    if (filter.preset == RulesetLootFilterPreset::Custom)
    {
        return filter;
    }

    RulesetLootFilter custom;
    custom.preset = RulesetLootFilterPreset::Custom;
    custom.leaveOnGround = filter.leaveOnGround;
    const LootFilterAction action = filter.leaveOnGround ? LootFilterAction::Ground : LootFilterAction::Gold;
    // Groups with the same cell share a rule: "Uncommon or below · weapons, armour".
    const auto add = [&custom, action](uint32_t types, int rarityAtMost, int levelsBelow)
    {
        for (RulesetLootFilterRule &rule : custom.rules)
        {
            if (rule.rarityAtMost == rarityAtMost && rule.levelsBelow == levelsBelow)
            {
                rule.types |= types;
                return;
            }
        }

        custom.rules.push_back({types, uint8_t(rarityAtMost), uint8_t(levelsBelow), action});
    };
    const LootFilterPresetDefinition &preset = lootFilterPreset(filter.preset);

    for (size_t group = 0; group < LootFilterGroupCount; ++group)
    {
        const LootFilterPresetColumn &column = preset.columns[group];
        const uint32_t types = lootItemTypesOfGroup(LootFilterGroup(group));

        if (column.goldUpTo > 0)
        {
            add(types, column.goldUpTo, 0);
        }

        if (column.levelGap > 0 && column.goldUpTo < LootFilterRarityCount)
        {
            add(types, column.goldUpTo + 1, column.levelGap);
        }
    }

    uint32_t kinds = 0;

    for (size_t kind = 0; kind < RulesetLootKindCount; ++kind)
    {
        if (filter.turnsKindIntoGold(RulesetLootKind(kind)))
        {
            kinds |= 1u << (unsigned(LootItemType::Wands) + unsigned(kind));
        }
    }

    if (kinds != 0)
    {
        custom.rules.push_back({kinds, uint8_t(LootFilterRarityCount), 0, action});
    }

    return custom;
}

std::optional<size_t> matchingLootFilterRule(const RulesetLootFilter &filter, const LootFilterFacts &facts,
    int partyLevel)
{
    if (facts.alwaysKept || !facts.type)
    {
        return std::nullopt;
    }

    for (size_t index = 0; index < filter.rules.size(); ++index)
    {
        const RulesetLootFilterRule &rule = filter.rules[index];
        // The kinds without rarity take any rule that names them, whatever its rarity.
        const bool rarityFits = facts.kind || facts.rarity <= rule.rarityAtMost;
        const bool levelFits = rule.levelsBelow == 0
            || (facts.itemLevel > 0 && partyLevel - facts.itemLevel >= rule.levelsBelow);

        if ((rule.types & (1u << unsigned(*facts.type))) != 0 && rarityFits && levelFits)
        {
            return index;
        }
    }

    return std::nullopt;
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

    if (filter.preset == RulesetLootFilterPreset::Custom)
    {
        const std::optional<size_t> rule = matchingLootFilterRule(filter, facts, partyLevel);
        return rule ? filter.rules[*rule].action : filter.otherwise;
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
        const LootFilterVerdict verdict = evaluateLootFilter(filter, drop.facts, drop.partyLevel);

        if (verdict != LootFilterVerdict::Keep)
        {
            ++trial.filtered;
            // Only drops that turn into gold pay; those left on the ground do not.
            trial.gold += verdict == LootFilterVerdict::Gold ? drop.gold : 0;
        }

        if (filter.preset == RulesetLootFilterPreset::Custom && !drop.facts.alwaysKept)
        {
            const std::optional<size_t> rule = matchingLootFilterRule(filter, drop.facts, drop.partyLevel);
            ++(rule ? trial.byRule[*rule] : trial.byOtherwise);
        }
    }

    return trial;
}
}

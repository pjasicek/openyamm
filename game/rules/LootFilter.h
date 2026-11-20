#pragma once

#include "game/content/RulesetOptions.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
// The loot filter's decision on a monster's or chest's drop (RulesetLootFilter; the ruleset describes the drop with
// ItemRules::lootFilterFacts). Only weapons, armour and jewellery have a rarity; the kinds without one are switched
// whole.
enum class LootFilterGroup : uint8_t
{
    Weapons = 0,
    Armour = 1,
    Jewellery = 2,
};
inline constexpr size_t LootFilterGroupCount = 3;
// The rarities a preset grades, 1 Common .. 6 Primordial (MAW's).
inline constexpr int LootFilterRarityCount = 6;

// What the filter needs of a drop.
struct LootFilterFacts
{
    std::optional<LootFilterGroup> group;
    std::optional<RulesetLootKind> kind;
    // The finer type Custom rules name; none for a weapon of a skill no rule names (a blaster).
    std::optional<LootItemType> type;
    // The gear's rarity, 1 Common .. 6 Primordial.
    int rarity = 0;
    // The item's level (MAW's drop level); 0 when it has none, which no level rule takes.
    int itemLevel = 0;
    // Legendary, Celestial, artifacts and the like: never filtered.
    bool alwaysKept = false;
};

// The filter's decision is what a Custom rule does: keep, gold or ground.
using LootFilterVerdict = LootFilterAction;

// A preset's column for one group: rarities up to goldUpTo turn into gold (0: none), and the next one does once the
// item's level is at least levelGap below the party's (0: never).
struct LootFilterPresetColumn
{
    int goldUpTo = 0;
    int levelGap = 0;
};

struct LootFilterPresetDefinition
{
    const char *description = "";
    // 0-4 for the strictness marker; -1 for Custom.
    int strictness = 0;
    std::array<LootFilterPresetColumn, LootFilterGroupCount> columns = {};
};

const LootFilterPresetDefinition &lootFilterPreset(RulesetLootFilterPreset preset);
const char *lootFilterGroupName(LootFilterGroup group);
// "Common" .. "Primordial" for 1-6; empty otherwise.
const char *lootFilterRarityName(int rarity);
const char *lootFilterKindName(RulesetLootKind kind);
// "Sword" .. "Gems".
const char *lootItemTypeName(LootItemType type);
// The type an item of this equip stat and skill group is; none for the items no rule names.
std::optional<LootItemType> lootItemType(const std::string &equipStat, const std::string &skillGroup);
// The bits of the weapons, the armour, the jewellery or the kinds without rarity (RulesetLootFilterRule::types).
uint32_t lootItemTypesOfGroup(LootFilterGroup group);
uint32_t lootItemTypesWithoutRarity();
// The filter as Custom rules that do what it does ("from the preset you had"); a Custom filter comes back as it is.
RulesetLootFilter lootFilterAsCustom(const RulesetLootFilter &filter);
// The Custom rule that decides a drop (its index), or none when "Everything else" does; none for a drop always kept.
std::optional<size_t> matchingLootFilterRule(const RulesetLootFilter &filter, const LootFilterFacts &facts,
    int partyLevel);
// A cell of the window's grid: "keep", "gold" or "gold if 20+ levels below".
std::string lootFilterCellText(RulesetLootFilterPreset preset, LootFilterGroup group, int rarity);
LootFilterVerdict evaluateLootFilter(const RulesetLootFilter &filter, const LootFilterFacts &facts, int partyLevel);
// Whether a shop's Sell trash picks the item (MAW): Common and Uncommon weapons and armour, Rare ones 10+ levels below
// the party and Epic ones 20+ below; Common jewellery, Uncommon 10+ below and Rare 20+ below; every gem. The player
// changes the pick before selling; never anything the loot filter always keeps.
bool isSellTrash(const LootFilterFacts &facts, int partyLevel);

// A drop the filter saw this session, for the window's "your last 50 drops" (not saved).
struct RecentLootDrop
{
    LootFilterFacts facts;
    int partyLevel = 0;
    // The gold it turns into when filtered.
    int gold = 0;
};

class RecentLootDrops
{
public:
    static constexpr size_t MaxDrops = 50;

    void add(const RecentLootDrop &drop);
    const std::deque<RecentLootDrop> &drops() const;

private:
    std::deque<RecentLootDrop> m_drops;
};

// What a filter would have done with the recent drops.
struct LootFilterTrial
{
    size_t drops = 0;
    size_t filtered = 0;
    int gold = 0;
    // Custom: how many of the drops each rule decided, and "Everything else".
    std::array<size_t, RulesetLootFilterMaxRules> byRule = {};
    size_t byOtherwise = 0;
};
LootFilterTrial tryLootFilter(const RulesetLootFilter &filter, const std::deque<RecentLootDrop> &drops);
}

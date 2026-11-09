#include "doctest/doctest.h"
#include "game/gameplay/CombatLog.h"
#include "game/gameplay/GameplayLootFilter.h"
#include "game/party/Party.h"
#include "game/rules/LootFilter.h"
#include "game/rules/maw/MawItemFormulas.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/ItemTable.h"

#include <string>

using namespace OpenYAMM::Game;

// MAW's loot filter presets (level_generation/ui/maw_loot_progress_20261025, view A).
namespace
{
LootFilterFacts gear(LootFilterGroup group, int rarity, int itemLevel = 0)
{
    LootFilterFacts facts;
    facts.group = group;
    facts.rarity = rarity;
    facts.itemLevel = itemLevel;
    return facts;
}

LootFilterFacts kind(RulesetLootKind lootKind)
{
    LootFilterFacts facts;
    facts.kind = lootKind;
    return facts;
}

ItemDefinition definition(uint32_t itemId, const std::string &equipStat, const std::string &name)
{
    ItemDefinition result;
    result.itemId = itemId;
    result.equipStat = equipStat;
    result.name = name;
    result.value = 1000;
    return result;
}
}

TEST_CASE("loot filter presets: the rarity grid, the level rule and the kinds without rarity")
{
    const RulesetLootFilter regular = rulesetLootFilterWithPreset(RulesetLootFilterPreset::Regular);

    // Regular: Common and Uncommon weapons and armour to gold, Rare once 20 levels behind the party.
    CHECK(evaluateLootFilter(regular, gear(LootFilterGroup::Weapons, 1), 50) == LootFilterVerdict::Gold);
    CHECK(evaluateLootFilter(regular, gear(LootFilterGroup::Armour, 2), 50) == LootFilterVerdict::Gold);
    CHECK(evaluateLootFilter(regular, gear(LootFilterGroup::Weapons, 3, 31), 50) == LootFilterVerdict::Keep);
    CHECK(evaluateLootFilter(regular, gear(LootFilterGroup::Weapons, 3, 30), 50) == LootFilterVerdict::Gold);
    // An item without a level never meets the level rule.
    CHECK(evaluateLootFilter(regular, gear(LootFilterGroup::Weapons, 3, 0), 50) == LootFilterVerdict::Keep);
    CHECK(evaluateLootFilter(regular, gear(LootFilterGroup::Weapons, 4, 1), 50) == LootFilterVerdict::Keep);
    // Jewellery a step gentler: Common, and Uncommon once 20 behind.
    CHECK(evaluateLootFilter(regular, gear(LootFilterGroup::Jewellery, 1), 50) == LootFilterVerdict::Gold);
    CHECK(evaluateLootFilter(regular, gear(LootFilterGroup::Jewellery, 2, 40), 50) == LootFilterVerdict::Keep);
    CHECK(evaluateLootFilter(regular, gear(LootFilterGroup::Jewellery, 2, 30), 50) == LootFilterVerdict::Gold);
    CHECK_EQ(lootFilterCellText(RulesetLootFilterPreset::Regular, LootFilterGroup::Weapons, 3),
        "gold if 20+ levels below");
    CHECK_EQ(lootFilterCellText(RulesetLootFilterPreset::Regular, LootFilterGroup::Weapons, 2), "gold");
    CHECK_EQ(lootFilterCellText(RulesetLootFilterPreset::Regular, LootFilterGroup::Weapons, 4), "keep");

    // Legendary, Celestial and artifacts are never filtered, whatever their rarity.
    LootFilterFacts legendary = gear(LootFilterGroup::Weapons, 1);
    legendary.alwaysKept = true;
    CHECK(evaluateLootFilter(rulesetLootFilterWithPreset(RulesetLootFilterPreset::VeryStrict), legendary, 99)
        == LootFilterVerdict::Keep);

    // The kinds without rarity: Strict turns scrolls into gold, Very strict wands too; the player may flip them.
    const RulesetLootFilter strict = rulesetLootFilterWithPreset(RulesetLootFilterPreset::Strict);
    CHECK(evaluateLootFilter(strict, kind(RulesetLootKind::Scrolls), 1) == LootFilterVerdict::Gold);
    CHECK(evaluateLootFilter(strict, kind(RulesetLootKind::Wands), 1) == LootFilterVerdict::Keep);
    CHECK(evaluateLootFilter(rulesetLootFilterWithPreset(RulesetLootFilterPreset::VeryStrict),
              kind(RulesetLootKind::Wands), 1)
        == LootFilterVerdict::Gold);
    RulesetLootFilter potions = regular;
    potions.goldKinds |= 1u << unsigned(RulesetLootKind::Potions);
    CHECK(evaluateLootFilter(potions, kind(RulesetLootKind::Potions), 1) == LootFilterVerdict::Gold);
    CHECK(evaluateLootFilter(regular, kind(RulesetLootKind::Potions), 1) == LootFilterVerdict::Keep);

    // Off keeps everything; "stay on the ground" leaves a filtered drop where it fell.
    const RulesetLootFilter off = rulesetLootFilterWithPreset(RulesetLootFilterPreset::Off);
    CHECK(evaluateLootFilter(off, gear(LootFilterGroup::Weapons, 1), 99) == LootFilterVerdict::Keep);
    const RulesetLootFilter ground = rulesetLootFilterWithPreset(RulesetLootFilterPreset::Regular, true);
    CHECK(evaluateLootFilter(ground, gear(LootFilterGroup::Weapons, 1), 50) == LootFilterVerdict::Ground);
}

TEST_CASE("loot filter: MAW's old rarity threshold becomes the nearest preset (save 126)")
{
    CHECK(rulesetLootFilterFromLegacyRarity(0).preset == RulesetLootFilterPreset::Off);
    CHECK(rulesetLootFilterFromLegacyRarity(1).preset == RulesetLootFilterPreset::Soft);
    CHECK(rulesetLootFilterFromLegacyRarity(2).preset == RulesetLootFilterPreset::Regular);
    CHECK(rulesetLootFilterFromLegacyRarity(3).preset == RulesetLootFilterPreset::Strict);
    CHECK(rulesetLootFilterFromLegacyRarity(6).preset == RulesetLootFilterPreset::VeryStrict);
    CHECK(rulesetLootFilterFromLegacyRarity(3).turnsKindIntoGold(RulesetLootKind::Scrolls));
}

TEST_CASE("loot filter on a MAW drop: gold with a combat log line, or left greyed; the recent drops try presets")
{
    RulesetOptions options;
    options.preferences.lootFilter = rulesetLootFilterWithPreset(RulesetLootFilterPreset::Regular);
    MawRules rules(options, MawMapLevels{});
    Character member;
    member.level = 50;
    PartySeed seed;
    seed.members = {member, member};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    CombatLog log;
    log.setRecording(true);
    bindCombatLog(&log);

    const ItemDefinition longsword = definition(1, "Weapon", "Longsword");
    InventoryItem uncommon;
    uncommon.objectDescriptionId = 1;
    uncommon.rulesetFields.lootRarity = uint8_t(MawRarity::Uncommon);
    uncommon.rulesetFields.dropLevel = 48;
    const FilteredLoot filtered = filterDroppedLoot(uncommon, longsword, &party, nullptr, nullptr);
    CHECK(filtered.verdict == LootFilterVerdict::Gold);
    CHECK_GT(filtered.gold, 0u);
    REQUIRE_EQ(log.entries().size(), 1u);
    CHECK(log.entries()[0].kind == CombatLogKind::Loot);
    CHECK_EQ(log.entries()[0].rarity, "Uncommon");
    CHECK_EQ(log.entries()[0].target, "Longsword");
    CHECK_EQ(log.entries()[0].amount, int(filtered.gold));
    CHECK(log.entries()[0].stages.empty());

    // An Epic sword stays; a legendary Common one too.
    InventoryItem epic = uncommon;
    epic.rulesetFields.lootRarity = uint8_t(MawRarity::Epic);
    CHECK(filterDroppedLoot(epic, longsword, &party, nullptr, nullptr).verdict == LootFilterVerdict::Keep);
    InventoryItem legendary = uncommon;
    legendary.rulesetFields.lootRarity = uint8_t(MawRarity::Common);
    legendary.rulesetFields.legendaryAffixId = 12;
    CHECK(filterDroppedLoot(legendary, longsword, &party, nullptr, nullptr).verdict == LootFilterVerdict::Keep);
    CHECK_EQ(log.entries().size(), 1u);

    // Every drop the filter could take is in the recent drops; Very strict would also have taken the Epic sword.
    const RecentLootDrops *pRecent = rules.gameRules().items.recentLootDrops();
    REQUIRE(pRecent != nullptr);
    REQUIRE_EQ(pRecent->drops().size(), 3u);
    const LootFilterTrial veryStrict =
        tryLootFilter(rulesetLootFilterWithPreset(RulesetLootFilterPreset::VeryStrict), pRecent->drops());
    CHECK_EQ(veryStrict.drops, 3u);
    CHECK_EQ(veryStrict.filtered, 2u);
    CHECK_EQ(tryLootFilter(rulesetLootFilterWithPreset(RulesetLootFilterPreset::Off), pRecent->drops()).filtered, 0u);

    // "Stay on the ground": the drop stays an item, marked for its grey outline; no gold, no log line.
    options.preferences.lootFilter = rulesetLootFilterWithPreset(RulesetLootFilterPreset::Regular, true);
    rules.setOptions(options);
    InventoryItem left = uncommon;
    const FilteredLoot leftResult = filterDroppedLoot(left, longsword, &party, nullptr, nullptr);
    CHECK(leftResult.verdict == LootFilterVerdict::Ground);
    CHECK_EQ(leftResult.gold, 0u);
    CHECK_EQ(left.rulesetFields.lootFiltered, 1);
    CHECK_EQ(log.entries().size(), 1u);

    // A spellbook is never filtered; Standard has no filter.
    InventoryItem book;
    book.objectDescriptionId = 400;
    CHECK(filterDroppedLoot(book, definition(400, "Book", "Fire Bolt"), &party, nullptr, nullptr).verdict
        == LootFilterVerdict::Keep);
    Party standard;
    standard.seed(seed);
    CHECK(filterDroppedLoot(uncommon, longsword, &standard, nullptr, nullptr).verdict == LootFilterVerdict::Keep);
    bindCombatLog(nullptr);
}

TEST_CASE("recent loot drops keep the last 50")
{
    RecentLootDrops recent;

    for (int index = 0; index < 60; ++index)
    {
        recent.add({gear(LootFilterGroup::Weapons, 1), index, index});
    }

    REQUIRE_EQ(recent.drops().size(), RecentLootDrops::MaxDrops);
    CHECK_EQ(recent.drops().front().partyLevel, 10);
    CHECK_EQ(recent.drops().back().partyLevel, 59);
}

TEST_CASE("Sell trash picks plain gear, gear far below the party and gems")
{
    using G = LootFilterGroup;
    CHECK(isSellTrash(gear(G::Weapons, 1), 30));
    CHECK(isSellTrash(gear(G::Armour, 2), 30));
    CHECK_FALSE(isSellTrash(gear(G::Weapons, 3, 25), 30));
    CHECK(isSellTrash(gear(G::Weapons, 3, 20), 30));
    CHECK_FALSE(isSellTrash(gear(G::Armour, 4, 15), 30));
    CHECK(isSellTrash(gear(G::Armour, 4, 10), 30));
    CHECK_FALSE(isSellTrash(gear(G::Armour, 5, 1), 60));
    // An item without a level never goes by the level rules.
    CHECK_FALSE(isSellTrash(gear(G::Weapons, 3, 0), 60));

    CHECK(isSellTrash(gear(G::Jewellery, 1), 30));
    CHECK_FALSE(isSellTrash(gear(G::Jewellery, 2, 25), 30));
    CHECK(isSellTrash(gear(G::Jewellery, 2, 20), 30));
    CHECK_FALSE(isSellTrash(gear(G::Jewellery, 3, 15), 30));
    CHECK(isSellTrash(gear(G::Jewellery, 3, 10), 30));
    CHECK_FALSE(isSellTrash(gear(G::Jewellery, 4, 1), 60));

    CHECK(isSellTrash(kind(RulesetLootKind::Gems), 1));
    CHECK_FALSE(isSellTrash(kind(RulesetLootKind::Wands), 60));
    CHECK_FALSE(isSellTrash(kind(RulesetLootKind::Reagents), 60));

    LootFilterFacts kept = gear(G::Weapons, 1);
    kept.alwaysKept = true;
    CHECK_FALSE(isSellTrash(kept, 60));
}

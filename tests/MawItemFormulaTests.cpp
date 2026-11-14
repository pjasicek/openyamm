#include "doctest/doctest.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/party/Party.h"
#include "game/rules/maw/MawItemFormulas.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <random>
#include <sstream>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

// The tables of devdocs/maw/data/loot.yml and data/rarity_golden.csv, computed by running MAW's own Lua.
namespace
{
// The item's inspect line with this text, or an empty string: MAW lists an item's special among its inspect lines.
std::string inspectLine(const ItemRules &items, const InventoryItem &item, const ItemDefinition &definition,
    const Character *pViewer, const std::string &text)
{
    for (const ItemInspectLine &line : items.inspectLines(item, definition, nullptr, nullptr, pViewer))
    {
        if (line.text == text)
        {
            return line.text;
        }
    }

    return {};
}

const std::filesystem::path MawData = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "devdocs/maw/data";

YAML::Node lootTables()
{
    return YAML::LoadFile((MawData / "loot.yml").string());
}

MawItemData installedItemData()
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/items.yml");
    const std::string text((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    MawItemData data;
    std::string error;
    REQUIRE_MESSAGE(data.loadFromYaml(text, error), error);
    return data;
}

ItemDefinition itemDefinition(uint32_t itemId, const std::string &equipStat, const std::string &skill)
{
    ItemDefinition definition;
    definition.itemId = itemId;
    definition.equipStat = equipStat;
    definition.skillGroup = skill;
    definition.value = 100;
    return definition;
}

std::vector<std::string> splitCsv(const std::string &line)
{
    std::vector<std::string> cells;
    std::stringstream stream(line);
    std::string cell;

    while (std::getline(stream, cell, ','))
    {
        cells.push_back(cell);
    }

    return cells;
}
}

TEST_CASE("MAW long-run rarity shares match the golden table of the loot guide")
{
    std::ifstream input(MawData / "rarity_golden.csv");
    REQUIRE(input.good());
    std::string line;
    std::getline(input, line);
    size_t rows = 0;

    while (std::getline(input, line))
    {
        const std::vector<std::string> cells = splitCsv(line);

        if (cells.size() < 14 || cells[3] != "pity_longrun")
        {
            continue;
        }

        const int difficulty = std::stoi(cells[0]);
        const bool boss = cells[2] == "boss";
        const int tier = std::stoi(cells[4]);
        CHECK(mawRarityUpgradeMultiplier(tier, difficulty, boss) == doctest::Approx(std::stod(cells[5])));
        const std::array<double, 8> shares = mawLongRunRarityShares(tier, difficulty, boss);

        for (size_t rarity = 0; rarity < shares.size(); ++rarity)
        {
            INFO(line, " rarity ", rarity + 1);
            CHECK(shares[rarity] == doctest::Approx(std::stod(cells[6 + rarity])).epsilon(1e-5));
        }

        ++rows;
    }

    CHECK_EQ(rows, 378u);
}

TEST_CASE("MAW enchant strength follows the tier table")
{
    const YAML::Node rows = lootTables()["enchant_strength_by_tier"]["rows"];
    REQUIRE(rows.size() > 30);
    const MawLootConfig normal;
    MawLootConfig insanity;
    insanity.enchantPower = 1.2;

    for (const YAML::Node &row : rows)
    {
        const int tier = row[0].as<int>();
        INFO("tier ", tier);
        CHECK_EQ(mawEnchantStrengthCurve(tier, false), row[1].as<int>());
        CHECK_EQ(mawEnchantStrengthCurve(tier, true), row[2].as<int>());
        CHECK_EQ(mawEnchantStrength(tier, MawRarity::Epic, 8, normal), row[3].as<int>());
        CHECK_EQ(mawEnchantStrength(tier, MawRarity::Common, 20, normal), row[4].as<int>());
        CHECK_EQ(mawEnchantStrength(tier, MawRarity::Legendary, 16, normal), row[5].as<int>());
        CHECK_EQ(mawEnchantStrength(tier, MawRarity::Legendary, 20, normal), row[6].as<int>());
        CHECK_EQ(mawEnchantStrength(tier, MawRarity::Ancient, 20, normal), row[7].as<int>());
        CHECK_EQ(mawEnchantStrength(tier, MawRarity::Ancient, 25, normal), row[8].as<int>());
        CHECK_EQ(mawEnchantStrength(tier, MawRarity::Primordial, 25, normal), row[9].as<int>());
        CHECK_EQ(mawEnchantStrength(tier, MawRarity::Celestial, 25, insanity), row[10].as<int>());
    }
}

TEST_CASE("MAW level requirements follow the drop-level table")
{
    const YAML::Node rows = lootTables()["level_requirement_by_drop_level"]["rows"];
    REQUIRE(rows.size() > 20);
    const MawLevelRequirementRules normal;
    const MawLevelRequirementRules nightmare{.nightmare = true};
    const MawLevelRequirementRules doom{.nightmare = true, .doom = true};

    for (const YAML::Node &row : rows)
    {
        const int dropLevel = row[0].as<int>();
        INFO("drop level ", dropLevel);
        CHECK_EQ(mawItemPowerForLevel(dropLevel), row[1].as<int>());
        CHECK_EQ(mawLevelRequirement(dropLevel, 1, normal), row[2].as<int>());
        CHECK_EQ(mawLevelRequirement(dropLevel, 2.25, normal), row[3].as<int>());
        CHECK_EQ(mawLevelRequirement(dropLevel, 3.5, normal), row[4].as<int>());
        CHECK_EQ(mawLevelRequirement(dropLevel, 4.75, normal), row[5].as<int>());
        CHECK_EQ(mawLevelRequirement(dropLevel, 6, normal), row[6].as<int>());
        CHECK_EQ(mawLevelRequirement(dropLevel, 1, nightmare), row[7].as<int>());
        CHECK_EQ(mawLevelRequirement(dropLevel, 6, nightmare), row[8].as<int>());
        CHECK_EQ(mawLevelRequirement(dropLevel, 6, doom), row[9].as<int>());
    }
}

TEST_CASE("MAW weapon damage follows the item-power table")
{
    const YAML::Node table = lootTables()["weapon_damage_by_power"];
    const std::vector<int> powers = {0, 10, 20, 40, 60, 80, 100};
    size_t checked = 0;

    for (const auto &entry : table)
    {
        const std::string key = entry.first.as<std::string>();

        if (key == "columns")
        {
            continue;
        }

        // "1H r2.25 d3"
        std::stringstream stream(key);
        std::string hands;
        std::string rung;
        std::string dice;
        stream >> hands >> rung >> dice;
        const bool twoHanded = hands == "2H";
        const double ladderRung = std::stod(rung.substr(1));
        const int diceCount = std::stoi(dice.substr(1));

        for (size_t column = 0; column < powers.size(); ++column)
        {
            const MawWeaponDamage damage = mawWeaponDamage(powers[column] * 5.0, twoHanded, ladderRung, diceCount);
            const std::string shown = "+" + std::to_string(damage.shownBonus) + " " + std::to_string(damage.minimum)
                + "-" + std::to_string(damage.maximum);
            INFO(key, " P", powers[column]);
            CHECK_EQ(shown, entry.second[column].as<std::string>());
            ++checked;
        }
    }

    CHECK(checked > 100);
}

TEST_CASE("MAW armour class and attack speed follow the item tables")
{
    const YAML::Node tables = lootTables();
    const std::vector<int> powers = {0, 20, 40, 60, 80, 100, 120};

    for (const auto &entry : tables["armor_bases"])
    {
        const YAML::Node &row = entry.second;
        INFO("armour ", entry.first.as<int>());

        for (size_t column = 0; column < powers.size(); ++column)
        {
            CHECK_EQ(mawArmorClass(row[3].as<int>(), row[4].as<int>(), powers[column]), row[5 + column].as<int>());
        }
    }

    const std::vector<int> levels = {0, 50, 100, 200, 300, 400, 500, 600};
    const std::vector<std::pair<std::string, std::pair<int, bool>>> weapons = {
        {"dagger_1h", {60, false}}, {"sword_1h", {80, false}}, {"sword_2h", {80, true}},
        {"mace_1h", {100, false}}, {"staff_2h", {120, true}}, {"spear_1h", {120, false}},
        {"axe_2h", {140, true}}, {"blaster_1h", {40, false}},
    };

    for (const auto &[name, weapon] : weapons)
    {
        const YAML::Node row = tables["attack_speed_by_item_level"][name];

        for (size_t column = 0; column < levels.size(); ++column)
        {
            INFO(name, " level ", levels[column]);
            CHECK(mawItemRecovery(weapon.first, levels[column], weapon.second) / 100.0
                  == doctest::Approx(row[column].as<double>()));
        }
    }
}

TEST_CASE("MAW item power and loot tier")
{
    CHECK_EQ(mawItemPower(100, MawRarity::Common, 20), 20);
    CHECK_EQ(mawItemPower(100, MawRarity::Common, 12), 12);
    CHECK_EQ(mawItemPower(100, MawRarity::Ancient, 20), 22);
    CHECK_EQ(mawItemPower(100, MawRarity::Ancient, 24), 24);
    CHECK_EQ(mawItemPower(100, MawRarity::Primordial, 24), 24);
    CHECK_EQ(mawItemPower(5, MawRarity::Primordial, 24), 5);
    CHECK_EQ(mawItemPower(2000, MawRarity::Celestial, 24), 120);

    // Grade 3 at drop level 50: 3 + 3, and +1 when the draw falls under 5/15.
    CHECK_EQ(mawLootTier(3, 50, false, false, 0, 0.5), 6);
    CHECK_EQ(mawLootTier(3, 50, false, false, 0, 0.2), 7);
    CHECK_EQ(mawLootTier(3, 50, true, true, 0, 0.5), 8);
    CHECK(mawPityChance(0.03, 0) == doctest::Approx(std::pow(0.03, 1.38)));
    CHECK(mawPityChance(0.03, 92) >= 1);
}

TEST_CASE("MAW rarity rolls reach the long-run shares of the loot guide")
{
    struct Case
    {
        int difficulty;
        bool boss;
        int tier;
    };

    for (const Case &row : {Case{3, false, 20}, Case{3, true, 20}, Case{9, true, 20}, Case{5, false, 4}})
    {
        const std::array<double, 8> expected = mawLongRunRarityShares(row.tier, row.difficulty, row.boss);
        MawRarityRollInputs inputs;
        inputs.lootTier = row.tier;
        inputs.difficulty = row.difficulty;
        inputs.boss = row.boss;
        MawRarityPity pity;
        std::mt19937 rng(20261023);
        std::array<int, 9> counts = {};
        constexpr int Rolls = 2000000;

        for (int roll = 0; roll < Rolls; ++roll)
        {
            ++counts[size_t(mawRollRarity(inputs, pity, rng))];
        }

        for (size_t rarity = 1; rarity <= 8; ++rarity)
        {
            const double share = 100.0 * counts[rarity] / Rolls;
            INFO("difficulty ", row.difficulty, " boss ", row.boss, " tier ", row.tier, " rarity ", rarity);
            CHECK(std::abs(share - expected[rarity - 1]) <= std::max(0.15, expected[rarity - 1] * 0.12));
        }
    }
}

TEST_CASE("MAW shops and Austerity never roll Legendary or Celestial")
{
    MawRarityRollInputs shop;
    shop.lootTier = 30;
    shop.difficulty = 9;
    shop.boss = true;
    shop.shop = true;
    MawRarityRollInputs austerity = shop;
    austerity.shop = false;
    austerity.noLegendary = true;
    MawRarityPity pity;
    std::mt19937 rng(7);
    std::array<int, 9> shopCounts = {};
    std::array<int, 9> austerityCounts = {};

    for (int roll = 0; roll < 200000; ++roll)
    {
        ++shopCounts[size_t(mawRollRarity(shop, pity, rng))];
        ++austerityCounts[size_t(mawRollRarity(austerity, pity, rng))];
    }

    CHECK(shopCounts[size_t(MawRarity::Ancient)] > 0);
    CHECK_EQ(shopCounts[size_t(MawRarity::Primordial)], 0);
    CHECK_EQ(shopCounts[size_t(MawRarity::Legendary)] + shopCounts[size_t(MawRarity::Celestial)], 0);
    CHECK(austerityCounts[size_t(MawRarity::Primordial)] > 0);
    CHECK_EQ(austerityCounts[size_t(MawRarity::Legendary)] + austerityCounts[size_t(MawRarity::Celestial)], 0);

    MawRarityRollInputs omnipotent;
    omnipotent.omnipotent = true;
    CHECK_EQ(mawRollRarity(omnipotent, pity, rng), MawRarity::Celestial);
}

TEST_CASE("MAW item values and prices")
{
    MawValueInputs inputs;
    inputs.baseValue = 100;
    inputs.itemPower = 20;
    inputs.enchant1Type = 1;
    inputs.enchant1Strength = 30;
    inputs.enchant2Type = 8;
    inputs.enchant2Strength = 40;
    const double hitPoints = 5 * (std::sqrt(180.0) - 10) * 100;
    CHECK(mawItemValue(inputs) == doctest::Approx(100 + 100 + 3000 + hitPoints));
    inputs.legendary = true;
    CHECK(mawItemValue(inputs) == doctest::Approx((100 + 100 + 3000 + hitPoints) * 2.5));

    inputs = {};
    inputs.baseValue = 1000;
    inputs.itemPower = 40;
    inputs.specialValue = 10;
    inputs.enchant1Type = 20;
    inputs.enchant1Strength = 4;
    CHECK(mawItemValue(inputs) == doctest::Approx(1000 + 2000 * 10 * 2.5 + 16 * 100));

    // A stat special's price grows with the item's power before the factor-or-gold test (GAPS.md A2.11): 3 x 40 / 20
    // is a factor of 6; 500 x 2 is 1000 gold added.
    inputs.enchant1Type = 0;
    inputs.specialValue = 3;
    inputs.specialScales = true;
    CHECK(mawItemValue(inputs) == doctest::Approx(1000 + 2000 * 6));
    inputs.specialValue = 500;
    CHECK(mawItemValue(inputs) == doctest::Approx(1000 + 2000 + 1000));

    CHECK_EQ(mawRoundPrice(1963.3), 2000);
    CHECK_EQ(mawRoundPrice(57240), 57000);
    CHECK_EQ(mawRoundPrice(250400), 250000);
    CHECK_EQ(mawRoundPrice(155), 160);
    CHECK(mawShopBuyValue(1000, 2, false) == doctest::Approx(std::pow(1000.0, 1.16)));
    CHECK(mawShopBuyValue(1000, 3, true) == doctest::Approx(std::pow(1000.0, 1.4)));

    CHECK_EQ(mawEnchantReadPower(8, 40, true, 1, false), 72);
    CHECK_EQ(mawEnchantReadPower(9, 300, false, 1.5, false), 1500);
    CHECK_EQ(mawEnchantReadPower(11, 30, true, 0.75, true), 20);
    CHECK_EQ(mawEnchantReadPower(11, 30, false, 1, false), 30);
    CHECK_EQ(mawEnchantReadPower(1, 30, true, 2, false), 30);
}

TEST_CASE("MAW items read their damage, armour and level requirement from item power")
{
    const MawItemData data = installedItemData();
    REQUIRE(data.baseItem(1) != nullptr);
    CHECK_EQ(data.baseItem(1)->diceCount, 2);
    CHECK(data.baseItem(84)->referenceArmorClass == 32);
    CHECK(data.artifact(500) != nullptr);
    // 103 artifacts a drop can become, and 28 that never drop but scale all the same (GAPS.md A2.5).
    CHECK_EQ(data.artifacts().size(), 131u);
    CHECK_EQ(std::count_if(data.artifacts().begin(), data.artifacts().end(),
                 [](const MawArtifact &artifact) { return artifact.dropWeight > 0; }),
        103);
    REQUIRE(data.artifact(540) != nullptr);
    CHECK_EQ(data.artifact(540)->dropWeight, 0);
    CHECK(data.artifact(532)->rung == doctest::Approx(3.5));
    CHECK_FALSE(data.legendaryAffixText(28).empty());

    RulesetOptions options;
    MawRules rules(options, MawMapLevels{}, data);
    const ItemRules &items = rules.gameRules().items;
    const ItemDefinition longsword = itemDefinition(1, "Weapon", "Sword");
    ItemRulesetFields fields;
    fields.itemPower = 20;
    fields.dropLevel = 100;
    fields.lootRarity = uint8_t(MawRarity::Rare);
    const std::optional<ItemBaseStats> stats = items.baseStats(longsword, fields, 30);
    REQUIRE(stats.has_value());
    const MawWeaponDamage damage = mawWeaponDamage(100, false, 1, 2);
    CHECK_EQ(stats->attackBonus, damage.shownBonus);
    CHECK_EQ(stats->minimumDamage, damage.minimum);
    CHECK_EQ(stats->maximumDamage, damage.maximum);
    CHECK_EQ(items.levelRequirement(longsword, fields), mawLevelRequirement(100, 1, {}));

    const ItemDefinition jerkin = itemDefinition(84, "Armor", "Leather");
    fields.itemPower = 40;
    CHECK_EQ(items.baseStats(jerkin, fields, 30)->armorClass, 40);

    fields.lootRarity = uint8_t(MawRarity::Celestial);
    CHECK_EQ(items.levelRequirement(longsword, fields), 1);

    // Anything but a base item keeps the table's numbers.
    CHECK_FALSE(items.baseStats(itemDefinition(222, "Bottle", "Misc"), fields, 30).has_value());
    CHECK_EQ(items.levelRequirement(itemDefinition(222, "Bottle", "Misc"), fields), 0);

    options.difficulty = RulesetDifficulty::Nightmare;
    rules.setOptions(options);
    fields.lootRarity = uint8_t(MawRarity::Rare);
    CHECK_EQ(items.levelRequirement(longsword, fields), mawLevelRequirement(100, 1, {.nightmare = true}));
}

TEST_CASE("MAW damage enchantments show the range they roll at the item's level")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const ItemDefinition longsword = itemDefinition(1, "Weapon", "Sword");
    InventoryItem item;
    item.objectDescriptionId = 1;
    item.specialEnchantId = 4;
    item.rulesetFields.itemPower = 20;
    const MawEnchantRange range =
        mawEnchantDamageRange(rules.model(1).weaponLevelDamage(100, false, 0), 3, 4, 0.2, false);
    REQUIRE(range.minimum > 3);
    const std::string cold = "Adds " + std::to_string(int(std::floor(range.minimum))) + "-"
        + std::to_string(int(std::floor(range.maximum))) + " points of Cold damage.";
    CHECK_EQ(inspectLine(rules.gameRules().items, item, longsword, nullptr, cold), cold);

    // A weak weapon keeps half the table's range; Body's range is one number.
    item.specialEnchantId = 13;
    item.rulesetFields.itemPower = 0;
    CHECK_EQ(inspectLine(rules.gameRules().items, item, longsword, nullptr, "Adds 2 points of Body damage."),
        "Adds 2 points of Body damage.");
}

TEST_CASE("MAW base enchantments apply both slots through the read transforms")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const ItemRules &items = rules.gameRules().items;
    const ItemDefinition ring = itemDefinition(137, "Ring", "Misc");
    EquippedItemRuntimeState state;
    state.standardEnchantId = 11;
    state.standardEnchantPower = 30;
    state.rulesetFields.secondStandardEnchantId = 8;
    state.rulesetFields.secondStandardEnchantPower = 40;
    state.rulesetFields.lootRarity = uint8_t(MawRarity::Rare);
    Character wearer;
    Character bonuses;
    items.applyEquippedEnchantEffects(ring, state, nullptr, nullptr, wearer, bonuses);
    // Fire resistance: +10 on the first enchantment, halved on a ring, kept apart from the resistances (it cuts damage
    // on its own); HP amplified by its size on a 0.75 slot.
    CHECK_EQ(bonuses.itemResistanceEnchants.fire, 20);
    CHECK_EQ(bonuses.magicalBonuses.resistances.fire, 0);
    CHECK_EQ(bonuses.magicalBonuses.maxHealth, mawEnchantReadPower(8, 40, false, 0.75, true));

    // Skill enchantments give at most the wearer's own skill.
    state = {};
    state.standardEnchantId = 22;
    state.standardEnchantPower = 9;
    state.rulesetFields.lootRarity = uint8_t(MawRarity::Uncommon);
    bonuses = {};
    items.applyEquippedEnchantEffects(ring, state, nullptr, nullptr, wearer, bonuses);
    CHECK_EQ(bonuses.itemSkillBonuses["Armsmaster"], 0);
    wearer.skills["Armsmaster"] = CharacterSkill{"Armsmaster", 4, SkillMastery::Normal};
    bonuses = {};
    items.applyEquippedEnchantEffects(ring, state, nullptr, nullptr, wearer, bonuses);
    CHECK_EQ(bonuses.itemSkillBonuses["Armsmaster"], 4);
}

TEST_CASE("MAW loot filter facts and shop rerolls")
{
    RulesetOptions options;
    options.preferences.lootFilter = rulesetLootFilterWithPreset(RulesetLootFilterPreset::Strict);
    MawRules rules(options, MawMapLevels{}, installedItemData());
    const ItemRules &items = rules.gameRules().items;
    REQUIRE(items.lootFilter() != nullptr);
    CHECK(items.lootFilter()->preset == RulesetLootFilterPreset::Strict);
    ItemDefinition sword;
    sword.itemId = 2;
    sword.equipStat = "Weapon";
    // Items without a price are never filtered (DEVIATIONS 182).
    sword.value = 100;
    InventoryItem item;
    item.objectDescriptionId = 2;
    item.rulesetFields.lootRarity = uint8_t(MawRarity::Rare);
    item.rulesetFields.dropLevel = 30;
    std::optional<LootFilterFacts> facts = items.lootFilterFacts(item, sword);
    REQUIRE(facts);
    CHECK(facts->group == LootFilterGroup::Weapons);
    CHECK_EQ(facts->rarity, 3);
    CHECK_EQ(facts->itemLevel, 30);
    CHECK_FALSE(facts->alwaysKept);
    CHECK(evaluateLootFilter(*items.lootFilter(), *facts, 30) == LootFilterVerdict::Gold);
    item.rulesetFields.lootRarity = uint8_t(MawRarity::Epic);
    CHECK(evaluateLootFilter(*items.lootFilter(), *items.lootFilterFacts(item, sword), 30) == LootFilterVerdict::Keep);
    // A spellbook or a quest item is never the filter's.
    ItemDefinition book;
    book.equipStat = "Book";
    book.value = 100;
    CHECK_FALSE(items.lootFilterFacts(item, book).has_value());
    CHECK(standardItemRules().lootFilter() == nullptr);
    CHECK_FALSE(standardItemRules().lootFilterFacts(item, sword).has_value());

    HouseEntry shop;
    shop.type = "Weapon Shop";
    shop.worldId = "mm8";
    MawGameState state;
    state.continentLevels = {40, 30, 20, 0};
    rules.setState(state);
    // P = 90 - min(40 / 2, 54) = 70 -> tier 4; S = min(floor(40 / 18) + 2, 5) = 4.
    CHECK_EQ(items.shopRerollCost(Party{}, shop), (4 + 4) * (4 + 4) * 250);
    shop.type = "Temple";
    CHECK_FALSE(items.shopRerollCost(Party{}, shop).has_value());
    CHECK_FALSE(standardItemRules().shopRerollCost(Party{}, HouseEntry{}).has_value());
}

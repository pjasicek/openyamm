#include "PartySpellTestHarness.h"
#include "RegressionGameData.h"
#include "doctest/doctest.h"
#include "game/content/ContentManifest.h"
#include "game/content/RulesetDefinition.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayMonsterSpawn.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/tables/HouseTable.h"
#include "game/maps/SaveGame.h"
#include "game/party/SkillData.h"
#include "game/party/SpellIds.h"
#include "game/rules/CorpseLoot.h"
#include "game/rules/CraftingRules.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawDimensionMaps.h"
#include "game/rules/maw/MawExperienceCurve.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawMonsterLevels.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawTexts.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include <yaml-cpp/yaml.h>

using namespace OpenYAMM::Game;

// The fixes of devdocs/maw/GAPS.md, by gap id.
namespace
{
MawItemData installedItemData()
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/items.yml");
    const std::string text((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    MawItemData data;
    std::string error;
    REQUIRE_MESSAGE(data.loadFromYaml(text, error), error);
    return data;
}

std::string readSource(const std::string &path)
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / path);
    return std::string((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
}

MawCraftingData installedCraftingData()
{
    MawCraftingData data;
    std::string error;
    REQUIRE_MESSAGE(data.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/crafting.yml"), error), error);
    return data;
}

// A monster table row: id, picture, level, 100 HP, walking melee with 1d6 physical, the treasure given.
std::vector<std::string> monsterRow(int id, const std::string &picture, int level, const std::string &treasure = "")
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = picture;
    row[2] = picture;
    row[3] = std::to_string(level);
    row[4] = "100";
    row[7] = treasure;
    row[10] = "Short";
    row[11] = "Normal";
    row[17] = "Phys";
    row[18] = "1d6";
    return row;
}

// The Human Mercenary family (193-195, levels 10/17/24) on Ravenshore's wilds (out05, band 20/25/30).
struct MercenaryMap
{
    MonsterTable monsters;
    MawMapLevels mapLevels;
    MapStatsEntry map = {};

    MercenaryMap()
    {
        REQUIRE(monsters.loadStatsFromRows({monsterRow(193, "Human Mercenary A", 10, "3d10"),
            monsterRow(194, "Human Mercenary B", 17, "3d10"), monsterRow(195, "Human Mercenary C", 24, "3d10")}));
        std::string error;
        REQUIRE_MESSAGE(mapLevels.loadFromYaml("bands:\n  out05.odm: [20, 25, 30]\nhorizontal_starter_maps: []\n"
                                               "madness:\n  starting_maps: []\n  levels: {}\n",
                            error),
            error);
        map.fileName = "out05.odm";
        map.name = "Wilds";
        map.encounter1.pictureName = "Human Mercenary";
    }

    GameplayBolsterRuntimeContext context(const ActorRulesetFacts *pExisting = nullptr) const
    {
        GameplayBolsterRuntimeContext result = {};
        result.pMap = &map;
        result.pMonsterTable = &monsters;
        result.pExistingFacts = pExisting;
        return result;
    }
};

ItemDefinition itemDefinition(uint32_t itemId, const std::string &equipStat, const std::string &skill)
{
    ItemDefinition definition;
    definition.itemId = itemId;
    definition.equipStat = equipStat;
    definition.skillGroup = skill;
    definition.value = 100;
    return definition;
}

// The engine's map table, as installed.
MapStats installedMapStats()
{
    std::istringstream input(readSource("assets_dev/engine/data_tables/map_stats.txt"));
    std::vector<std::vector<std::string>> rows;
    std::string line;

    while (std::getline(input, line))
    {
        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        std::vector<std::string> row;
        std::istringstream cells(line);
        std::string cell;

        while (std::getline(cells, cell, '\t'))
        {
            row.push_back(cell);
        }

        rows.push_back(row);
    }

    MapStats stats;
    REQUIRE(stats.loadFromRows(rows));
    return stats;
}

// Puts an amulet carrying a legendary affix on the character.
void wearLegendary(Character &character, int affixId)
{
    character.equipment.amulet = 1;
    character.equipmentRuntime.amulet.rulesetFields.legendaryAffixId = uint16_t(affixId);
}

// What one worn item with this special at this item power gives its wearer under MAW.
Character specialBonuses(
    const MawRules &rules,
    uint16_t specialId,
    int itemPower,
    const Character &wearer = {},
    const SpecialItemEnchantTable *pSpecialTable = nullptr)
{
    EquippedItemRuntimeState state;
    state.specialEnchantId = specialId;
    state.rulesetFields.itemPower = uint16_t(itemPower);
    state.rulesetFields.lootRarity = uint8_t(MawRarity::Rare);
    Character bonuses;
    rules.gameRules().items.applyEquippedEnchantEffects(
        itemDefinition(137, "Ring", "Misc"), state, nullptr, pSpecialTable, wearer, bonuses);
    return bonuses;
}
}

TEST_CASE("MAW weapon guard reads the ladder flat plus the top rung x item power / 30 (audit FITM-2-2)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const MawItemRules &itemRules = rules.itemRules();
    ItemRulesetFields fields;
    fields.itemPower = 40;
    fields.qualityPercent = 20;

    // Bone Staff (83, top rung): 16 + round(16 x 40 / 30) = 37, quality left out.
    REQUIRE(items.get(83) != nullptr);
    CHECK_EQ(itemRules.weaponGuardBase(*items.get(83), fields, 50), 37);
    // A one-handed top-rung weapon halves both: 8 + round(8 x 40 / 30) = 19.
    REQUIRE(items.get(5) != nullptr);
    CHECK_EQ(itemRules.weaponGuardBase(*items.get(5), fields, 50), 19);
    // The power has no cap: 16 + round(16 x 255 / 30) = 152.
    fields.itemPower = 255;
    CHECK_EQ(itemRules.weaponGuardBase(*items.get(83), fields, 50), 152);
    // An artifact: its printed flat after MAW's upscaler (Volcano 505: 19 x 3).
    REQUIRE(items.get(505) != nullptr);
    CHECK_EQ(itemRules.weaponGuardBase(*items.get(505), ItemRulesetFields{}, 50), 57);

    // Grandmaster Staff 50 with the power-40 staff: 4 % x 37 x (50 + 10) = 89 resistance for the party.
    Character holder;
    holder.level = 50;
    holder.equipment.mainHand = 83;
    holder.equipmentRuntime.mainHand.rulesetFields.itemPower = 40;
    holder.skills["Staff"] = {"Staff", 50, SkillMastery::Grandmaster};
    CHECK_EQ(mawStaffPartyResistance(rules, holder, items), 89);
}

TEST_CASE("MAW artifact data and powers: rungs, printed armour, Stoneskin, Excalibur, Medusa's Mirror (audit ITM-A2..A5)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    const MawItemData data = installedItemData();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, data);

    // A2: the Tournament Bow and Ethric's Staff sit on their ladder runs' rungs.
    CHECK(data.artifact(531)->rung == doctest::Approx(3.5));
    CHECK(data.artifact(1317)->rung == doctest::Approx(1.357));

    // A3: a flat artifact keeps its printed armour (Odin 10).
    REQUIRE(items.get(2044) != nullptr);
    CHECK_EQ(rules.itemRules().armorClass(*items.get(2044), ItemRulesetFields{}, 50), 10);

    const auto worn = [&rules, &items](uint32_t itemId, const Character &wearer)
    {
        EquippedItemRuntimeState state;
        Character bonuses = wearer;
        rules.gameRules().items.applyEquippedEnchantEffects(*items.get(itemId), state, nullptr, nullptr, wearer, bonuses);
        return bonuses;
    };

    // A4: Galahad's Stoneskin gives 20 armour; Excalibur's Bless 3 attack, not Standard's skill-scaled amount.
    Character knight;
    knight.className = "Knight";
    knight.skills["Sword"] = {"Sword", 50, SkillMastery::Grandmaster};
    REQUIRE(items.get(2026) != nullptr);
    CHECK_EQ(worn(2026, knight).magicalBonuses.armorClass, 20);
    REQUIRE(items.get(2023) != nullptr);
    CHECK(worn(2023, knight).magicalBonuses.meleeAttack <= 3);

    // A5: Medusa's Mirror guards against stone in both rulesets.
    REQUIRE(items.get(1341) != nullptr);
    CHECK(worn(1341, knight).magicalConditionImmunities.test(size_t(CharacterCondition::Petrified)));
    Character standard;
    EquippedItemRuntimeState state;
    standardGameRules().items.applyEquippedEnchantEffects(*items.get(1341), state, nullptr, nullptr, standard, standard);
    CHECK(standard.magicalConditionImmunities.test(size_t(CharacterCondition::Petrified)));

    // L8, L7: the texts say what legendaries 28 and 30 do.
    CHECK(data.legendaryAffixText(28).find("50%") != std::string::npos);
    CHECK(data.legendaryAffixText(30).find("higher of HP and SP") != std::string::npos);
}

TEST_CASE("MAW artifact popups show MAW's bonuses, not MMMerge's special powers (audit FITM-2-5)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.setItemTable(&gameData.itemTable);
    rules.state().continentLevels = {0, 100, 0, 0};
    InventoryItem elderaxe;
    elderaxe.objectDescriptionId = 504;
    elderaxe.identified = true;
    const std::vector<ItemInspectLine> lines = rules.gameRules().items.inspectLines(
        elderaxe, *gameData.itemTable.get(504), &gameData.standardItemEnchantTable, nullptr, nullptr);
    const auto hasLine = [&lines](const std::string &text)
    {
        return std::any_of(lines.begin(), lines.end(),
            [&text](const ItemInspectLine &line) { return line.text.find(text) != std::string::npos; });
    };
    CHECK(hasLine("Might +"));
    CHECK(hasLine("Artifact level"));

    // The description loses the "(...)" part MMMerge prints its numbers in; Standard keeps it.
    CHECK_EQ(mawArtifactDescription("(Might +20, Swift) An axe of old."), "An axe of old.");
    CHECK_EQ(mawArtifactDescription("A sword. (Special Powers: +30 Might)"), "A sword.");
    const std::optional<std::string> description = rules.gameRules().items.itemDescription(elderaxe, nullptr);
    REQUIRE(description.has_value());
    CHECK(description->find("(") == std::string::npos);
    CHECK_FALSE(standardItemRules().itemDescription(elderaxe, nullptr).has_value());
}

TEST_CASE("MAW makes the halberd artifact Guardian two-handed, its budget doubled (audit ITM-A1)")
{
    const MawItemData items = installedItemData();
    const MawArtifact *pGuardian = items.artifact(507);
    REQUIRE(pGuardian != nullptr);
    CHECK(pGuardian->twoHanded);
    CHECK(pGuardian->slotMultiplier == doctest::Approx(2));
}

TEST_CASE("MAW shows a Celestial item at its viewer's level (audit ITM-4)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const ItemTable &table = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.state().continentLevels = {0, 200, 0, 0};
    InventoryItem hat;
    hat.objectDescriptionId = 114;
    hat.standardEnchantId = 1;
    hat.standardEnchantPower = 5;
    hat.rulesetFields.lootRarity = uint8_t(MawRarity::Celestial);
    hat.rulesetFields.itemPower = 2;
    Character viewer;
    viewer.level = 150;
    const InventoryItem scaled = rules.itemRules().celestialAtLevel(hat, *table.get(114), int(viewer.level));
    REQUIRE(scaled.standardEnchantPower > hat.standardEnchantPower);
    CHECK(scaled.rulesetFields.itemPower > hat.rulesetFields.itemPower);

    // The popup's enchantment line reads the scaled strength (a hat: x1.5 rounded up).
    const auto hasLine = [](const std::vector<ItemInspectLine> &lines, const std::string &text)
    {
        return std::any_of(lines.begin(), lines.end(),
            [&text](const ItemInspectLine &line) { return line.text.find(text) != std::string::npos; });
    };
    const std::vector<ItemInspectLine> lines =
        rules.gameRules().items.inspectLines(hat, *table.get(114),
            &OpenYAMM::Tests::regressionGameData().standardItemEnchantTable, nullptr, &viewer);
    CHECK(hasLine(lines, "+" + std::to_string(int(std::ceil(scaled.standardEnchantPower * 1.5)))));
}

TEST_CASE("MAW dragons triple their items' Dodging and Unarmed too (audit FITM-2-3)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const auto bonusOf = [&rules](int raceId)
    {
        Character wearer;
        wearer.raceId = raceId;
        wearer.skills["Dodging"] = {"Dodging", 20, SkillMastery::Expert};
        EquippedItemRuntimeState state;
        state.standardEnchantId = 23;
        state.standardEnchantPower = 4;
        Character bonuses;
        rules.gameRules().items.applyEquippedEnchantEffects(
            itemDefinition(109, "Helm", "Misc"), state, nullptr, nullptr, wearer, bonuses);
        return bonuses.itemSkillBonuses["Dodging"];
    };
    const int human = bonusOf(0);
    REQUIRE(human > 0);
    CHECK_EQ(bonusOf(5), std::min(3 * human, 20));
}

TEST_CASE("MAW hats read hit points after their growth, then x1.5 rounded up (audit ITM-2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const auto worn = [&rules](uint32_t itemId, int type, int power)
    {
        EquippedItemRuntimeState state;
        state.standardEnchantId = uint16_t(type);
        state.standardEnchantPower = uint16_t(power);
        Character bonuses;
        rules.gameRules().items.applyEquippedEnchantEffects(
            itemDefinition(itemId, "Helm", "Misc"), state, nullptr, nullptr, Character{}, bonuses);
        return bonuses.magicalBonuses;
    };

    // Citizen Hat (114), HP power 100: round(100 x (1 + 100 / 50 / 1.875)) = 207, then ceil(207 x 1.5) = 311.
    CHECK_EQ(worn(114, 8, 100).maxHealth, 311);
    CHECK_EQ(worn(114, 8, 300).maxHealth, 1890);
    // Intellect 11 on a hat: ceil(16.5).
    CHECK_EQ(worn(114, 2, 11).intellect, 17);

    // MAW's hat is a helm without a flat armour bonus: the Horned Helm (891, one die) is one, the Helm (109) not
    // (audit ITM-3).
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const ItemTable &table = OpenYAMM::Tests::regressionGameData().itemTable;
    const auto wornReal = [&rules, &table](uint32_t itemId)
    {
        EquippedItemRuntimeState state;
        state.standardEnchantId = 2;
        state.standardEnchantPower = 10;
        Character bonuses;
        rules.gameRules().items.applyEquippedEnchantEffects(
            *table.get(itemId), state, nullptr, nullptr, Character{}, bonuses);
        return bonuses.magicalBonuses.intellect;
    };
    CHECK_EQ(wornReal(891), 15);
    CHECK_EQ(wornReal(109), 10);
}

TEST_CASE("MAW gives Standard-only specials no stats or skills, only the engine powers it keeps (audit ITM-7)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const SpecialItemEnchantTable &specials = OpenYAMM::Tests::regressionGameData().specialItemEnchantTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());

    // Monks' (60): Standard's +3 Dodging and Unarmed are gone.
    const Character monks = specialBonuses(rules, 60, 0, {}, &specials);
    CHECK(monks.itemSkillBonuses.empty());
    CHECK_EQ(monks.magicalBonuses.armorClass, 0);

    // Carnage still fires explosive arrows.
    for (size_t index = 0; index < specials.entries().size(); ++index)
    {
        if (specials.entries()[index].kind == SpecialItemEnchantKind::Carnage)
        {
            const Character carnage = specialBonuses(rules, uint16_t(index + 1), 0, {}, &specials);
            CHECK(carnage.equippedItemEffectFlags.contains("ExplosiveArrows"));
        }
    }
}

TEST_CASE("MAW special enchantments give MAW's stats, scaled by item power (A2.1, A2.2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());

    // "of Doom" (42): +3 to all sixteen at x min(1 + power / 25, 5); power 50 gives +9.
    const Character doom = specialBonuses(rules, 42, 50);
    CHECK_EQ(doom.magicalBonuses.might, 9);
    CHECK_EQ(doom.magicalBonuses.luck, 9);
    CHECK_EQ(doom.magicalBonuses.maxHealth, 9);
    CHECK_EQ(doom.magicalBonuses.armorClass, 9);
    CHECK_EQ(doom.magicalBonuses.resistances.fire, 9);
    CHECK_EQ(doom.magicalBonuses.resistances.body, 9);
    // The scale stops at x5.
    CHECK_EQ(specialBonuses(rules, 42, 500).magicalBonuses.might, 15);

    // MAW's own specials: Paladins' (74) +20 Personality and Accuracy, Divines' (80) +5 to all.
    const Character paladin = specialBonuses(rules, 74, 0);
    CHECK_EQ(paladin.magicalBonuses.personality, 20);
    CHECK_EQ(paladin.magicalBonuses.accuracy, 20);
    CHECK_EQ(paladin.magicalBonuses.might, 0);
    CHECK_EQ(specialBonuses(rules, 80, 0).magicalBonuses.resistances.mind, 5);
    // "of Ascension" (39): +25 Intellect and Personality before the scale.
    CHECK_EQ(specialBonuses(rules, 39, 25).magicalBonuses.intellect, 50);

    // A school special adds floor(power / 4) + 5 to its school, up to the trained skill.
    Character mage;
    mage.skills["FireMagic"] = {"FireMagic", 20, SkillMastery::Master};
    mage.skills["Meditation"] = {"Meditation", 4, SkillMastery::Normal};
    CHECK_EQ(specialBonuses(rules, 30, 40, mage).itemSkillBonuses["FireMagic"], 15);
    mage.skills["FireMagic"].level = 10;
    CHECK_EQ(specialBonuses(rules, 30, 40, mage).itemSkillBonuses["FireMagic"], 10);
    // "of Mana" (38) raises Meditation by floor(power x 3 / 20) + 3, here capped by the trained 4.
    CHECK_EQ(specialBonuses(rules, 38, 20, mage).itemSkillBonuses["Meditation"], 4);

    // The immunity specials guard against two conditions each.
    const Character immunity = specialBonuses(rules, 18, 0);
    CHECK(immunity.magicalConditionImmunities.test(size_t(CharacterCondition::DiseaseSevere)));
    CHECK(immunity.magicalConditionImmunities.test(size_t(CharacterCondition::Cursed)));
    CHECK(specialBonuses(rules, 19, 0).manaDrainImmune);
    CHECK(specialBonuses(rules, 21, 0).magicalConditionImmunities.test(size_t(CharacterCondition::Weak)));
    const Character medusa = specialBonuses(rules, 23, 0);
    CHECK(medusa.magicalConditionImmunities.test(size_t(CharacterCondition::Petrified)));
    CHECK(medusa.agingImmune);
    CHECK(specialBonuses(rules, 25, 0).magicalConditionImmunities.test(size_t(CharacterCondition::Eradicated)));

    // The popup reads the same numbers.
    InventoryItem item;
    item.objectDescriptionId = 137;
    item.specialEnchantId = 42;
    item.rulesetFields.itemPower = 50;
    const ItemDefinition ring = itemDefinition(137, "Ring", "Misc");
    CHECK_EQ(rules.gameRules().items.enchantDescription(item, ring, nullptr, nullptr, nullptr),
        " +9 to Seven Stats, HP, SP, Armor, Resistances.");
    item.specialEnchantId = 30;
    item.rulesetFields.itemPower = 40;
    CHECK_EQ(rules.gameRules().items.enchantDescription(item, ring, nullptr, nullptr, nullptr), "Fire Magic Skill +15");
}

TEST_CASE("MAW turns the engine's vampiric heal and flat regeneration off and keeps the specials it leaves alone")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const SpecialItemEnchantTable &table = OpenYAMM::Tests::regressionGameData().specialItemEnchantTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());

    // A1.2: Vampiric (16) and "of Darkness" (41) leech through MAW's leech only.
    CHECK_EQ(specialBonuses(rules, 16, 0, {}, &table).vampiricHealFraction, 0.0f);
    CHECK_EQ(specialBonuses(rules, 41, 0, {}, &table).vampiricHealFraction, 0.0f);
    // A2.3: the regeneration specials heal through MAW's regeneration, not the engine's +1 a second.
    CHECK_EQ(specialBonuses(rules, 37, 0, {}, &table).healthRegenPerSecond, 0.0f);
    CHECK_EQ(specialBonuses(rules, 59, 0, {}, &table).attackRecoveryReductionTicks, 0);
    // A1.3: Shielding (36) cuts physical damage in MAW's mitigation, not missiles by half.
    CHECK_FALSE(specialBonuses(rules, 36, 0, {}, &table).halfMissileDamage);
    // Monks' (60) gives none of Standard's +3 Unarmed and Dodging: MAW's own table has no row for it (audit ITM-7).
    Character monk;
    monk.skills["Unarmed"] = {"Unarmed", 10, SkillMastery::Expert};
    CHECK_EQ(specialBonuses(rules, 60, 0, monk, &table).itemSkillBonuses["Unarmed"], 0);

    // The same item under Standard keeps Standard's effects.
    Character standard;
    EquippedItemRuntimeState state;
    state.specialEnchantId = 16;
    standardGameRules().items.applyEquippedEnchantEffects(
        itemDefinition(137, "Ring", "Misc"), state, nullptr, &table, standard, standard);
    CHECK_GT(standard.vampiricHealFraction, 0.0f);
}

TEST_CASE("MAW item resistance enchantments and Shielding cut damage on their own (A1.1, A1.3)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());

    // A +100 fire enchantment halves fire damage at any level; as a sheet resistance it cuts less at level 150.
    MawMitigationInputs hit;
    hit.damage = 1000;
    hit.attackerLevel = 150;
    hit.type = CombatDamageType::Fire;
    hit.itemResistances[0] = 100;
    CHECK(mawMitigatedDamage(hit) == doctest::Approx(500).epsilon(0.002));
    hit.itemResistances[0] = 0;
    hit.resistances[0] = 100;
    // Resistances are divided by 100 + the attacker's level (MAW 249b00da; 100 + 12 L before).
    CHECK(mawMitigatedDamage(hit) == doctest::Approx(1000 / (100.0 / 250 + 1)).epsilon(0.002));

    // The best resistance enchantment per element counts, not their sum.
    EquippedItemRuntimeState state;
    state.standardEnchantId = 11;
    state.standardEnchantPower = 40;
    state.rulesetFields.lootRarity = uint8_t(MawRarity::Rare);
    Character wearer;
    Character bonuses;
    const ItemDefinition cloak = itemDefinition(137, "Ring", "Misc");
    rules.gameRules().items.applyEquippedEnchantEffects(cloak, state, nullptr, nullptr, wearer, bonuses);
    rules.gameRules().items.applyEquippedEnchantEffects(cloak, state, nullptr, nullptr, wearer, bonuses);
    CHECK_EQ(bonuses.itemResistanceEnchants.fire, 25);

    // Shielding: x0.85 physical damage taken.
    MawMitigationInputs blow;
    blow.damage = 1000;
    blow.attackerLevel = 50;
    const double plain = mawMitigatedDamage(blow);
    blow.shieldingEnchantment = true;
    CHECK(mawMitigatedDamage(blow) == doctest::Approx(plain * 0.85).epsilon(0.002));
}

TEST_CASE("MAW swiftness speeds weapon attacks and vampiric artifacts leech (A1.3, A1.2)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());

    Character knight;
    knight.className = "Knight";
    knight.level = 20;
    knight.equipment.mainHand = 1;
    const int plain = mawCharacterAttackDelay(rules, knight, items, CharacterAttackMode::Melee, 0).delay;
    knight.equipmentRuntime.mainHand.specialEnchantId = 59;
    const int swift = mawCharacterAttackDelay(rules, knight, items, CharacterAttackMode::Melee, 0).delay;
    CHECK(double(swift) == doctest::Approx(plain / 1.15).epsilon(0.02));

    // Foulfang (508), Spiritslayer (527) and 2020 leech like "of Darkness".
    Character vampire;
    vampire.equipment.mainHand = 508;
    CHECK(mawLeech(rules, vampire, &items).melee == doctest::Approx(0.10));
    CHECK(mawLeech(rules, vampire, &items).ranged == doctest::Approx(0.05));
}

TEST_CASE("MAW level-7 chest slots roll a boss's drop: enchantable equipment (audit OVR1-2-1)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    std::mt19937 rng(17);
    const auto roll = [&](ItemGenerationMode mode)
    {
        ItemGenerationRequest request;
        request.treasureLevel = 7;
        request.rareItemsOnly = true;
        request.mode = mode;
        return ItemGenerator::generateRandomInventoryItem(gameData.itemTable, gameData.standardItemEnchantTable,
            gameData.specialItemEnchantTable, request, &party, rng);
    };
    bool plainNonEquipment = false;

    for (int trial = 0; trial < 100; ++trial)
    {
        const std::optional<InventoryItem> chest = roll(ItemGenerationMode::ChestLoot);
        REQUIRE(chest.has_value());
        const ItemDefinition *pChest = gameData.itemTable.get(chest->objectDescriptionId);
        REQUIRE(pChest != nullptr);
        CHECK(ItemEnchantRuntime::isEnchantable(*pChest));

        if (const std::optional<InventoryItem> plain = roll(ItemGenerationMode::Generic))
        {
            const ItemDefinition *pPlain = gameData.itemTable.get(plain->objectDescriptionId);
            plainNonEquipment = plainNonEquipment || (pPlain != nullptr && !ItemEnchantRuntime::isEnchantable(*pPlain));
        }
    }

    CHECK(plainNonEquipment);
}

TEST_CASE("MAW friendly fire, Fly on high difficulties and level-7 treasure (A1.13, A3.3, A2.6)")
{
    RulesetOptions options;
    MawRules rules(options, MawMapLevels{}, installedItemData());
    CHECK_FALSE(rules.gameRules().combat.harmsFriendlyActors());
    CHECK(standardGameRules().combat.harmsFriendlyActors());
    options.preferences.friendlyFire = true;
    rules.setOptions(options);
    CHECK(rules.gameRules().combat.harmsFriendlyActors());

    // From Hard up and in Austerity a blow ends Fly, except on the flight maps.
    options.difficulty = RulesetDifficulty::Maw;
    CHECK_FALSE(mawAttackingEndsFly(options, "out01.odm"));
    options.difficulty = RulesetDifficulty::Hard;
    CHECK(mawAttackingEndsFly(options, "out01.odm"));
    CHECK_FALSE(mawAttackingEndsFly(options, "outb3.odm"));
    options.difficulty = RulesetDifficulty::Easy;
    options.challengeMode = RulesetChallengeMode::Austerity;
    CHECK(mawAttackingEndsFly(options, "out01.odm"));

    // The Fly the party had goes on as Feather Fall.
    options = {};
    options.difficulty = RulesetDifficulty::Hell;
    rules.setOptions(options);
    rules.setCurrentMap("out02.odm");
    PartySeed seed;
    seed.members.resize(1);
    Party party;
    party.seed(seed);
    party.applyPartyBuff(PartyBuffId::Fly, 600.0f, 1, spellIdValue(SpellId::Fly), 10, SkillMastery::Master, 0);
    const ActorRulesetFacts target;
    PartyHitOnMonster hit;
    hit.damage = 10;
    hit.pTarget = &target;
    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::Fly));
    REQUIRE(party.partyBuff(PartyBuffId::FeatherFall) != nullptr);
    CHECK(party.partyBuff(PartyBuffId::FeatherFall)->remainingSeconds == doctest::Approx(600.0f));

    // Level-7 slots roll level-6 items under MAW; Standard gives a rare item.
    CHECK_FALSE(rules.gameRules().items.levelSevenGivesRareItem());
    CHECK(standardGameRules().items.levelSevenGivesRareItem());
}

TEST_CASE("MAW reagents take an item level from where they drop (A4.2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.state().continentLevels = {60, 30, 0, 0};
    const ItemDefinition reagent = itemDefinition(200, "Reagent", "Misc");

    // A third of the lower of the drop level and the party's total level.
    InventoryItem item;
    ItemGenerationRequest request;
    request.dropLevel = 60;
    rules.gameRules().items.rollPlainItem(item, reagent, request);
    CHECK_EQ(item.rulesetFields.dropLevel, 20);
    request.dropLevel = 300;
    rules.gameRules().items.rollPlainItem(item, reagent, request);
    CHECK_EQ(item.rulesetFields.dropLevel, 30);

    // Shops at 0.75 of the total level; Austerity divides by 8.
    request = {};
    request.mode = ItemGenerationMode::Shop;
    rules.gameRules().items.rollPlainItem(item, reagent, request);
    CHECK_EQ(item.rulesetFields.dropLevel, 23);
    RulesetOptions austerity;
    austerity.challengeMode = RulesetChallengeMode::Austerity;
    rules.setOptions(austerity);
    rules.gameRules().items.rollPlainItem(item, reagent, request);
    CHECK_EQ(item.rulesetFields.dropLevel, 8);

    // Other items keep their fields.
    InventoryItem potion;
    rules.gameRules().items.rollPlainItem(potion, itemDefinition(222, "Bottle", "Misc"), request);
    CHECK(potion.rulesetFields.empty());
}

TEST_CASE("MAW clubs keep a rolled Unarmed; a second enchantment within one takes the first's strength (audit ITM-8)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.state().continentLevels = {0, 80, 0, 0};
    const ItemRollTables tables{gameData.itemTable, gameData.standardItemEnchantTable, gameData.specialItemEnchantTable};
    ItemGenerationRequest request;
    request.mode = ItemGenerationMode::Shop;
    std::mt19937 rng(11);
    bool unarmedClub = false;

    for (int roll = 0; roll < 4000; ++roll)
    {
        InventoryItem club;
        club.objectDescriptionId = 862;
        rules.gameRules().items.rollEnchantments(club, *gameData.itemTable.get(862), tables, request, nullptr, rng);
        unarmedClub = unarmedClub || club.standardEnchantId == 24;

        if (club.standardEnchantId != 0 && club.rulesetFields.secondStandardEnchantId != 0)
        {
            CHECK_NE(std::abs(int(club.rulesetFields.secondStandardEnchantPower) - int(club.standardEnchantPower)), 1);
        }
    }

    CHECK(unarmedClub);
}

TEST_CASE("MAW mercenaries' gear leaves the loot's bad-luck counters alone (audit ROB-2-7)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.state().continentLevels = {60, 30, 0, 0};
    const ItemRollTables tables{gameData.itemTable, gameData.standardItemEnchantTable, gameData.specialItemEnchantTable};
    std::mt19937 rng(5);
    const auto rollMany = [&](bool sparesLuck)
    {
        ItemGenerationRequest request;
        request.allowRareItems = false;
        request.sparesLuck = sparesLuck;

        for (int roll = 0; roll < 50; ++roll)
        {
            InventoryItem helm;
            helm.objectDescriptionId = 109;
            rules.gameRules().items.rollEnchantments(helm, *gameData.itemTable.get(109), tables, request, nullptr, rng);
        }
    };

    rollMany(true);
    CHECK_EQ(rules.state().celestialPity, 0.0);
    CHECK_EQ(rules.state().legendaryPity, 0.0);
    rollMany(false);
    CHECK(rules.state().legendaryPity + rules.state().celestialPity + rules.state().primordialPity > 0);
}

TEST_CASE("MAW stores an item's drop level floored (audit ITM-6)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    // A shop rolls at 0.75 x the total level of 90: 67.5.
    rules.state().continentLevels = {60, 30, 0, 0};
    const ItemRollTables tables{gameData.itemTable, gameData.standardItemEnchantTable, gameData.specialItemEnchantTable};
    ItemGenerationRequest request;
    request.mode = ItemGenerationMode::Shop;
    std::mt19937 rng(3);
    InventoryItem helm;
    helm.objectDescriptionId = 109;
    rules.gameRules().items.rollEnchantments(helm, *gameData.itemTable.get(109), tables, request, nullptr, rng);
    CHECK_EQ(helm.rulesetFields.dropLevel, 67);
}

TEST_CASE("a promotion to Lich changes only the class when asked (A6.5)")
{
    PartySeed seed;
    seed.members.resize(2);
    seed.members[0].className = "Necromancer";
    seed.members[1].className = "Necromancer";
    Party party;
    party.seed(seed);

    REQUIRE(party.setMemberClassName(0, "Lich", true));
    CHECK_EQ(party.members()[0].className, "Lich");
    CHECK_EQ(party.members()[0].baseResistances.fire, 0);

    REQUIRE(party.setMemberClassName(1, "Lich"));
    CHECK_EQ(party.members()[1].baseResistances.fire, 20);
}

TEST_CASE("MAW monsters take the map's level on every resolve, bosses inside their band (A3.2, A3.5)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(195);
    const int fresh = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts.level;
    REQUIRE(fresh > 0);

    // A saved actor with an old level takes the level the map gives now, and follows the banks.
    ActorRulesetFacts saved;
    saved.level = 999;
    saved.familyLevel = 999;
    saved.tier = 3;
    CHECK_EQ(monsters.resolveMonster(world.context(&saved), stats, nullptr).rulesetFacts.level, fresh);
    rules.state().continentLevels = {0, 0, 100, 0};
    const int banked = monsters.resolveMonster(world.context(&saved), stats, nullptr).rulesetFacts.level;
    CHECK(banked > fresh + 50);

    // A boss: C + (C - B) when that lies in [1.1 C, 1.3 C] below level 100, else drawn inside [C + 10, C + 30].
    saved.bossAffix = 1;
    saved.bossLevelDraw = 0.5f;
    const GameplayMonsterBolsterResult boss = monsters.resolveMonster(world.context(&saved), stats, nullptr);
    const ActorRulesetFacts plain = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
    const int candidate = 2 * plain.level - plain.familyLevel;
    const bool inBand = plain.level < 100 ? candidate >= 1.1 * plain.level && candidate <= 1.3 * plain.level
                                          : candidate >= plain.level + 10 && candidate <= plain.level + 30;
    const int expected = inBand ? candidate
        : plain.level < 100      ? int(std::lround(plain.level * 1.2))
                                 : plain.level + 20;
    CHECK_EQ(boss.rulesetFacts.level, expected);
    CHECK_EQ(boss.rulesetFacts.bossAffix, 1);
    // A boss is worth its row's experience; its own level enters only through its health (audit MON-7).
    CHECK_EQ(boss.rulesetFacts.experience, plain.experience);

    // An A or B row's boss starts from the next tier's level, then the same band (audit MON-8).
    const auto bossOf = [&](int monsterId)
    {
        ActorRulesetFacts facts;
        facts.bossAffix = 1;
        facts.bossLevelDraw = 0.5f;
        return monsters.resolveMonster(world.context(&facts), *world.monsters.findStatsById(int16_t(monsterId)),
            nullptr).rulesetFacts.level;
    };
    const auto levelOfRow = [&](int monsterId)
    {
        return monsters.resolveMonster(world.context(), *world.monsters.findStatsById(int16_t(monsterId)), nullptr)
            .rulesetFacts.level;
    };
    const auto banded = [](int row, int start)
    {
        const bool inside = row < 100 ? start >= 1.1 * row && start <= 1.3 * row : start >= row + 10 && start <= row + 30;
        return inside ? start : row < 100 ? int(std::lround(row * 1.2)) : row + 20;
    };
    CHECK_EQ(bossOf(193), banded(levelOfRow(193), levelOfRow(194)));
    CHECK_EQ(bossOf(194), banded(levelOfRow(194), levelOfRow(195)));

    // A unique monster's level is not capped at 255 (audit MON-13).
    rules.state().continentLevels = {0, 0, 600, 0};
    ActorRulesetFacts unique;
    unique.unique = true;
    CHECK(monsters.resolveMonster(world.context(&unique), stats, nullptr).rulesetFacts.level > 255);
}

TEST_CASE("MAW bosses cast their spell at its skill times the damage multiplier (audit FMON-2-4)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData());
    MonsterTable::MonsterStatsEntry caster = *world.monsters.findStatsById(195);
    caster.spell1SkillLevel = 10;
    const GameplayMonsterBolsterResult plain = rules.gameRules().monsters.resolveMonster(world.context(), caster, nullptr);
    REQUIRE_EQ(plain.spell1SkillLevel, 10u);
    ActorRulesetFacts boss;
    boss.bossAffix = 1;
    boss.bossDamageMultiplier = 1.37f;
    const GameplayMonsterBolsterResult strong =
        rules.gameRules().monsters.resolveMonster(world.context(&boss), caster, nullptr);
    CHECK_EQ(strong.spell1SkillLevel, 13u);
}

TEST_CASE("MAW gives walking melee monsters a ranged attack from Hell up, outside the starting maps (A3.3)")
{
    MercenaryMap world;
    RulesetOptions options;
    options.difficulty = RulesetDifficulty::Hard;
    MawRules rules(options, world.mapLevels, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(195);
    CHECK_FALSE(monsters.resolveMonster(world.context(), stats, nullptr).generatedAttack2);

    options.difficulty = RulesetDifficulty::Hell;
    rules.setOptions(options);
    const GameplayMonsterBolsterResult hell = monsters.resolveMonster(world.context(), stats, nullptr);
    CHECK(hell.generatedAttack2);
    CHECK(hell.generatedAttack2IsRanged);
    CHECK_EQ(hell.generatedAttack2Chance, 30);
    // 1d6 becomes ceil(1 / 1.4) d ceil(6 / 1.4): a shot about 60 % of the blow.
    CHECK(hell.rulesetFacts.attack2Damage == doctest::Approx(hell.rulesetFacts.attack1Damage * 3.0 / 3.5));

    world.map.fileName = "out02.odm";
    CHECK_FALSE(monsters.resolveMonster(world.context(), stats, nullptr).generatedAttack2);
}

TEST_CASE("MAW's Endless Arena: wave corpses carry no gold or item, the wave boss keeps its loot (audit MON-4)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(194);
    ActorRulesetFacts facts = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
    CorpseLootContext context;
    context.pStats = &stats;
    context.pMonsterTable = &world.monsters;
    context.pFacts = &facts;
    context.pMap = &world.map;
    facts.level = 100;
    const CorpseLoot field = monsters.corpseLoot(context);
    REQUIRE_GT(field.loot.goldDiceRolls, 0);

    world.map.fileName = "d42.blv";
    const CorpseLoot wave = monsters.corpseLoot(context);
    CHECK_EQ(wave.loot.goldDiceRolls, 0);
    CHECK_EQ(wave.loot.itemChance, 0);
    facts.bossAffix = 1;
    const CorpseLoot boss = monsters.corpseLoot(context);
    CHECK_GT(boss.loot.goldDiceRolls, 0);
    CHECK_EQ(boss.loot.itemChance, 100);
}

TEST_CASE("MAW risen monsters' corpses hold a quarter of the item chance and gold dice sides (audit FITM-2-1)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(194);
    ActorRulesetFacts facts = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
    facts.level = 100;
    CorpseLootContext context;
    context.pStats = &stats;
    context.pMonsterTable = &world.monsters;
    context.pFacts = &facts;
    context.pMap = &world.map;
    const CorpseLoot alive = monsters.corpseLoot(context);
    REQUIRE_GT(alive.loot.goldDiceSides, 4);
    REQUIRE_GT(alive.loot.itemChance, 4);

    facts.risen = true;
    const CorpseLoot risen = monsters.corpseLoot(context);
    CHECK_EQ(risen.loot.itemChance, int(std::floor(alive.loot.itemChance / 4.0 + 0.5)));
    CHECK_EQ(risen.loot.goldDiceSides, int(std::floor(alive.loot.goldDiceSides / 4.0 + 0.5)));
    CHECK_EQ(risen.loot.goldDiceRolls, alive.loot.goldDiceRolls);

    // Road to Insanity empties the corpse instead.
    RulesetOptions insanity;
    insanity.challengeMode = RulesetChallengeMode::RoadToInsanity;
    rules.setOptions(insanity);
    CHECK_EQ(monsters.corpseLoot(context).loot.itemChance, 0);
    CHECK_EQ(monsters.corpseLoot(context).loot.goldDiceRolls, 0);
}

TEST_CASE("MAW risen monsters still drop reagents in Road to Insanity (audit ALC-12)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MercenaryMap world;
    RulesetOptions insanity;
    insanity.challengeMode = RulesetChallengeMode::RoadToInsanity;
    MawRules rules(insanity, world.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(OpenYAMM::Tests::regressionGameData());
    party.setRules(&rules.gameRules());
    party.member(0)->skills["Alchemy"] = {"Alchemy", 30, SkillMastery::Grandmaster};
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(194);
    ActorRulesetFacts facts = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
    facts.risen = true;
    CorpseLootContext context;
    context.pStats = &stats;
    context.pMonsterTable = &world.monsters;
    context.pFacts = &facts;
    context.pMap = &world.map;
    context.pParty = &party;
    size_t extras = 0;

    for (uint32_t actorIndex = 0; actorIndex < 1000; ++actorIndex)
    {
        context.actorIndex = actorIndex;
        const CorpseLoot loot = monsters.corpseLoot(context);
        CHECK_EQ(loot.loot.itemChance, 0);
        extras += loot.extraItems.size();
    }

    // 2 % reagents, the Endless Potion chance on top; no gems or specials from the risen.
    CHECK(extras > 5);
}

TEST_CASE("MAW Telepathy reveals the table's loot only; crafting and map drops wait for the kill (audit ALC-13)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(194);
    ActorRulesetFacts facts = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
    facts.level = 100;
    CorpseLootContext context;
    context.pStats = &stats;
    context.pMonsterTable = &world.monsters;
    context.pFacts = &facts;
    context.pMap = &world.map;
    context.part = CorpseLootPart::Table;

    for (uint32_t actorIndex = 0; actorIndex < 200; ++actorIndex)
    {
        context.actorIndex = actorIndex;
        CHECK(monsters.corpseLoot(context).extraItems.empty());
    }

    CHECK(rules.state().craftingPity.empty());
    CHECK_EQ(rules.state().mapDropPity, 0.0);

    // The kill's part: the extra drops alone.
    context.part = CorpseLootPart::Extras;
    const CorpseLoot extras = monsters.corpseLoot(context);
    CHECK_EQ(extras.loot.goldDiceRolls, 0);
    CHECK_EQ(extras.loot.itemChance, 0);
    CHECK_FALSE(rules.state().craftingPity.empty());
    CHECK_EQ(standardGameRules().monsters.corpseLoot(context).loot.itemChance, 0);
}

TEST_CASE("MAW gives Morcarack a boss's item roll, not a boss's gold (audit ITM-5)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(195);
    ActorRulesetFacts facts = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
    facts.unique = true;
    CorpseLootContext context;
    context.pStats = &stats;
    context.pMonsterTable = &world.monsters;
    context.pFacts = &facts;
    context.pMap = &world.map;
    context.uniqueNameId = 12;
    const CorpseLoot other = monsters.corpseLoot(context);
    context.uniqueNameId = 160;
    const CorpseLoot morcarack = monsters.corpseLoot(context);
    CHECK_FALSE(other.boss);
    CHECK(morcarack.boss);
    CHECK_EQ(morcarack.loot.itemChance, 100);
    CHECK_EQ(morcarack.loot.goldDiceRolls, other.loot.goldDiceRolls);
    CHECK_EQ(morcarack.loot.goldDiceSides, other.loot.goldDiceSides);
}

// The Human Mercenary family with armour 20, 30 and 40 on out05.
MonsterTable armouredMercenaries()
{
    std::vector<std::string> a = monsterRow(193, "Human Mercenary A", 10, "3d10");
    std::vector<std::string> b = monsterRow(194, "Human Mercenary B", 17, "3d10");
    std::vector<std::string> c = monsterRow(195, "Human Mercenary C", 24, "3d10");
    a[5] = "20";
    b[5] = "30";
    c[5] = "40";
    MonsterTable table;
    REQUIRE(table.loadStatsFromRows({a, b, c}));
    return table;
}

TEST_CASE("MAW boss and unique monsters keep their row's armour on the map, not their own level's (MON:751)")
{
    MercenaryMap world;
    world.monsters = armouredMercenaries();
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;

    // Without banks and with 100 banked levels: the boss's and the unique's levels lie above the row's.
    for (const double banked : {0.0, 100.0})
    {
        rules.state().continentLevels = {0, banked, banked, 0};

        for (const int monsterId : {193, 194, 195})
        {
            CAPTURE(banked);
            CAPTURE(monsterId);
            const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(int16_t(monsterId));
            const GameplayMonsterBolsterResult plain = monsters.resolveMonster(world.context(), stats, nullptr);
            ActorRulesetFacts bossFacts;
            bossFacts.bossAffix = 1;
            bossFacts.bossLevelDraw = 0.5f;
            const GameplayMonsterBolsterResult boss = monsters.resolveMonster(world.context(&bossFacts), stats, nullptr);
            ActorRulesetFacts uniqueFacts;
            uniqueFacts.unique = true;
            const GameplayMonsterBolsterResult unique =
                monsters.resolveMonster(world.context(&uniqueFacts), stats, nullptr);

            REQUIRE_GT(boss.rulesetFacts.level, plain.rulesetFacts.level);
            REQUIRE_NE(unique.rulesetFacts.level, plain.rulesetFacts.level);
            // The row's armour grown from the table's B level (17) to the row's level on the map.
            const int expected =
                int(std::lround(stats.armorClass * (plain.rulesetFacts.level + 10.0) / (17 + 10)));
            CHECK_EQ(plain.armorClass, expected);
            CHECK_EQ(boss.armorClass, plain.armorClass);
            CHECK_EQ(unique.armorClass, plain.armorClass);
        }
    }
}

TEST_CASE("MAW a boss's loot grade reads its level when it was drawn again, else its row's (IT:283-293)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    // The map's low level (20) and the table row's level (24): grade 24 / 20 + 2 = 3.2, so 3 or 4.
    const double mapLow = world.mapLevels.band(world.map.fileName)[0];
    REQUIRE_EQ(mapLow, 20.0);

    // Every grade the corpses of an actor with these facts show over many rolls.
    const auto grades = [&](const MonsterTable::MonsterStatsEntry &stats, const ActorRulesetFacts &facts)
    {
        CorpseLootContext context;
        context.pStats = &stats;
        context.pMonsterTable = &world.monsters;
        context.pFacts = &facts;
        context.pMap = &world.map;
        std::set<int> result;

        for (uint32_t actorIndex = 0; actorIndex < 400; ++actorIndex)
        {
            context.actorIndex = actorIndex;
            result.insert(int(monsters.corpseLoot(context).loot.itemLevel));
        }

        return result;
    };
    // The grades a level gives: L / 20 + 2, its fraction a chance to round up, within 2-6.
    const auto gradesOf = [](double level)
    {
        const double grade = level / 20 + 2;
        std::set<int> result = {std::clamp(int(std::floor(grade)), 2, 6)};

        if (grade > std::floor(grade))
        {
            result.insert(std::clamp(int(std::floor(grade)) + 1, 2, 6));
        }

        return result;
    };
    const auto bossFacts = [&](const MonsterTable::MonsterStatsEntry &stats)
    {
        ActorRulesetFacts facts;
        facts.bossAffix = 1;
        facts.bossLevelDraw = 0.5f;
        return monsters.resolveMonster(world.context(&facts), stats, nullptr).rulesetFacts;
    };
    const auto redrawn = [&](const MonsterTable::MonsterStatsEntry &stats)
    {
        const ActorRulesetFacts plain = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
        const int candidate = 2 * plain.level - plain.familyLevel;
        return plain.level < 100 ? candidate < 1.1 * plain.level || candidate > 1.3 * plain.level
                                 : candidate < plain.level + 10 || candidate > plain.level + 30;
    };
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(195);

    // 100 banked levels: the C row's boss level was drawn again, far above the row; its grade reads that level.
    rules.state().continentLevels = {0, 100, 100, 0};
    {
        REQUIRE(redrawn(stats));
        const ActorRulesetFacts boss = bossFacts(stats);
        CAPTURE(boss.level);
        REQUIRE(gradesOf(boss.level) != gradesOf(std::max<double>(stats.level, mapLow)));
        CHECK_EQ(grades(stats, boss), gradesOf(boss.level));
    }

    // No banks: the boss's level (C + (C - B)) lies inside its band and is kept, so the grade reads the row's level.
    rules.state().continentLevels = {};
    {
        CAPTURE(bossFacts(stats).level);
        REQUIRE_FALSE(redrawn(stats));
        const ActorRulesetFacts boss = bossFacts(stats);
        CHECK_EQ(grades(stats, boss), gradesOf(std::max<double>(stats.level, mapLow)));
    }

    // A unique boss reads its own level (2.5 x the row's on a map outside the horizontal starters: 60, grade 5).
    RulesetOptions horizontal;
    horizontal.progression = RulesetProgression::Horizontal;
    rules.setOptions(horizontal);
    {
        ActorRulesetFacts facts;
        facts.unique = true;
        facts = monsters.resolveMonster(world.context(&facts), stats, nullptr).rulesetFacts;
        facts.bossAffix = 1;
        REQUIRE_EQ(facts.level, 60);
        CHECK_EQ(grades(stats, facts), std::set<int>{5});
    }
}

TEST_CASE("MAW corpse loot: boss gold, the 255 cap and crafting drops for any party size (A2.7, A2.8, A4.1)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(194);
    ActorRulesetFacts facts = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
    CorpseLootContext context;
    context.pStats = &stats;
    context.pMonsterTable = &world.monsters;
    context.pFacts = &facts;
    context.pMap = &world.map;

    // A boss carries sqrt(100 L)d sqrt(100 L) gold, even when its row has none.
    facts.bossAffix = 1;
    facts.level = 400;
    CorpseLoot boss = monsters.corpseLoot(context);
    CHECK_EQ(boss.loot.goldDiceRolls, 159);
    CHECK_EQ(boss.loot.goldDiceSides, 159);
    // A boss's drop is one of MAW's twelve equipment kinds, each as often (audit FITM-2-4).
    std::unordered_map<int, int> kinds;

    for (uint32_t actorIndex = 0; actorIndex < 1200; ++actorIndex)
    {
        context.actorIndex = actorIndex;
        ++kinds[int(monsters.corpseLoot(context).loot.itemKind)];
    }

    context.actorIndex = 0;
    CHECK_FALSE(kinds.contains(int(MonsterTable::LootItemKind::Any)));
    CHECK(kinds[int(MonsterTable::LootItemKind::Ring)] > 60);
    CHECK(kinds[int(MonsterTable::LootItemKind::Ring)] < 140);
    CHECK(kinds[int(MonsterTable::LootItemKind::Weapon)] > 2 * 60);

    // Crafting drops do not depend on the party's size.
    facts.bossAffix = 0;
    facts.level = 200;
    PartySeed one;
    one.members.resize(1);
    PartySeed five;
    five.members.resize(5);
    Party small;
    small.seed(one);
    Party large;
    large.seed(five);

    // Each party from the same bad-luck counters.
    const auto drops = [&](const Party &party)
    {
        rules.state().craftingPity.clear();
        context.pParty = &party;
        size_t count = 0;

        for (uint32_t actor = 0; actor < 400; ++actor)
        {
            context.actorIndex = actor;
            count += monsters.corpseLoot(context).extraItems.size();
        }

        return count;
    };
    const size_t smallDrops = drops(small);
    const size_t largeDrops = drops(large);

    CHECK(smallDrops > 0);
    CHECK_EQ(largeDrops, smallDrops);
}

TEST_CASE("MAW real-time poison drains HP every second until it wears off (A1.5)")
{
    RulesetOptions options;
    options.difficulty = RulesetDifficulty::Hard;
    MawRules rules(options, MawMapLevels{}, installedItemData());
    PartySeed seed;
    seed.members.resize(2);
    seed.members[0].name = "Venom";
    seed.members[0].maxHealth = 1000;
    seed.members[0].health = 1000;
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;

    // A poisoning starts its timer at 25 s, a renewed one adds 5 up to 50.
    REQUIRE(party.applyMemberCondition(0, CharacterCondition::PoisonSevere));
    CHECK(party.members()[0].rulesetState.poisonSeconds == doctest::Approx(25));
    REQUIRE(party.applyMemberCondition(0, CharacterCondition::PoisonSevere));
    CHECK(party.members()[0].rulesetState.poisonSeconds == doctest::Approx(30));

    // Severe poison: ceil(1 % of full HP) x bolster 150 / 100 = 15 a second.
    rules.gameRules().combat.updateCombat(party, world, 1.0f);
    CHECK_EQ(party.members()[0].health, 985);
    CHECK(party.members()[0].rulesetState.poisonSeconds == doctest::Approx(29));

    for (int second = 0; second < 40; ++second)
    {
        rules.gameRules().combat.updateCombat(party, world, 1.0f);
    }

    CHECK_FALSE(party.members()[0].conditions.test(size_t(CharacterCondition::PoisonSevere)));
    CHECK_EQ(party.members()[0].health, 1000 - 29 * 15);
    REQUIRE_FALSE(world.eventRuntimeState()->statusMessages.empty());
    CHECK_EQ(world.eventRuntimeState()->statusMessages.back(), "Venom's poison effect expired");
}

TEST_CASE("MAW trap damage, every-hit shields and death thresholds (A1.6, A1.7, A6.8)")
{
    RulesetOptions options;
    options.difficulty = RulesetDifficulty::Nightmare;
    MawRules rules(options, MawMapLevels{}, installedItemData());
    rules.state().continentLevels = {50, 0, 0, 0};
    PartySeed seed;
    seed.members.resize(2);
    seed.members[0].className = "Knight";
    seed.members[0].level = 50;
    seed.members[0].maxHealth = 400;
    seed.members[0].health = 400;
    seed.members[0].spellPoints = 30;
    seed.members[1].className = "Seraphim";
    seed.members[1].level = 50;
    seed.members[1].maxHealth = 400;
    seed.members[1].health = 400;
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    const CombatRules &combat = rules.gameRules().combat;

    // A fall indoors is a trap at the party's level; outdoors it keeps its own number.
    const int indoor = combat.environmentDamage(party, 0, 7, CombatDamageType::Physical, true);
    CHECK(indoor > 7);
    CHECK_EQ(combat.environmentDamage(party, 0, 7, CombatDamageType::Physical, false), 7);
    CHECK(combat.environmentDamage(party, 0, 7, CombatDamageType::Fire, false) > 7);

    // From Nightmare a hit below minus full HP kills and empties SP; below twice that eradicates.
    REQUIRE(party.applyDamageToMember(0, 900, ""));
    CHECK(party.members()[0].conditions.test(size_t(CharacterCondition::Dead)));
    CHECK_EQ(party.members()[0].spellPoints, 0);
    CHECK_FALSE(party.members()[0].conditions.test(size_t(CharacterCondition::Eradicated)));

    // Divine Protection takes any lethal hit once per 150 game minutes, kept with the Seraphim.
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    combat.updateCombat(party, world, 0.0f);
    REQUIRE(party.applyDamageToMember(1, 5000, ""));
    CHECK(party.members()[1].health >= 1);
    CHECK(party.members()[1].rulesetState.divineProtectionReadyGameMinutes == doctest::Approx(150));
    REQUIRE(party.applyDamageToMember(1, 5000, ""));
    CHECK(party.members()[1].health < 0);
}

TEST_CASE("MAW monster-hit details: disease alone, Mist Form, Blades (A1.7, A1.14, A1.10)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const CombatRules &combat = rules.gameRules().combat;
    Character member;
    member.level = 20;
    member.maxHealth = 500;
    member.health = 500;
    member.conditions.set(size_t(CharacterCondition::DiseaseSevere));
    std::mt19937 rng(7);
    const auto blow = [&](int partyCount)
    {
        CharacterDamageHit hit;
        hit.amount = 100;
        hit.pCharacter = &member;
        hit.monsterAttack = true;
        hit.attackerLevel = 20;
        hit.attackerFacts.level = 20;
        hit.attackerFacts.familyLevel = 20;
        hit.attackerFacts.tier = 2;
        hit.attackerFacts.attack1Damage = 100;
        hit.partyCount = partyCount;
        hit.pRng = &rng;
        double total = 0;

        for (int i = 0; i < 400; ++i)
        {
            CharacterDamageHit copy = hit;
            total += combat.damageToCharacter(copy);
        }

        return total / 400;
    };
    // Severe disease: x2 for a party, x1.5 alone.
    CHECK(blow(1) / blow(5) == doctest::Approx(0.75).epsilon(0.05));

    // Mist Form lets a quarter of physical hits through.
    member.conditions.reset();
    const double plain = blow(5);
    member.mistFormPhysicalShare = 0.25f;
    CHECK(blow(5) / plain == doctest::Approx(0.25).epsilon(0.05));
    CHECK(combat.mistFormPhysicalShare() == doctest::Approx(0.25f));
    CHECK(standardGameRules().combat.mistFormPhysicalShare() == doctest::Approx(0.0f));

    CHECK_EQ(combat.partySpellDamageType(39, CombatDamageType::Earth), CombatDamageType::Physical);
    CHECK_EQ(combat.partySpellDamageType(6, CombatDamageType::Fire), CombatDamageType::Fire);
}

TEST_CASE("MAW Grandmaster spear stacks and fire arrows (A1.8, A1.9)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());

    // (2 + 0.02 s) x the speed multiplier: a Steel Spear (42) at GM 50.
    Character lancer;
    lancer.className = "Knight";
    lancer.equipment.mainHand = 42;
    lancer.skills["Spear"] = {"Spear", 50, SkillMastery::Grandmaster};
    const double stack = mawSpearStackPercent(rules, lancer, items);
    CHECK(stack > 2.5);

    MonsterDamageHit hit;
    hit.amount = 1000;
    hit.pMeleeAttacker = &lancer;
    hit.pItemTable = &items;
    hit.targetFacts.spearDamageTaken = 10;
    std::mt19937 rng(3);
    hit.pRng = &rng;
    const int boosted = rules.gameRules().combat.damageToMonster(hit);
    MonsterDamageHit plainHit;
    plainHit.amount = 1000;
    plainHit.pRng = &rng;
    const int plain = rules.gameRules().combat.damageToMonster(plainHit);
    CHECK(double(boosted) / plain == doctest::Approx(1 + (10 + stack) / 100).epsilon(0.01));

    // A missile's spear stacks still count; magic does not.
    MonsterDamageHit spell;
    spell.amount = 1000;
    spell.type = CombatDamageType::Fire;
    spell.targetFacts.spearDamageTaken = 50;
    spell.pRng = &rng;
    MonsterDamageHit fire = spell;
    fire.targetFacts.spearDamageTaken = 0;
    CHECK_EQ(rules.gameRules().combat.damageToMonster(spell), rules.gameRules().combat.damageToMonster(fire));

    // A Grandmaster bow fires burning arrows.
    Character archer;
    archer.className = "Archer";
    archer.equipment.bow = 56;
    archer.skills["Bow"] = {"Bow", 20, SkillMastery::Grandmaster};
    CharacterAttackResult attack;
    attack.mode = CharacterAttackMode::Bow;
    attack.canAttack = true;
    CharacterAttackOnMonster context;
    context.pCharacter = &archer;
    context.pItemTable = &items;
    context.minimumDamage = 10;
    context.maximumDamage = 20;
    context.pRng = &rng;
    rules.gameRules().combat.resolveCharacterAttack(attack, context);
    CHECK(attack.fireArrow);
    archer.skills["Bow"].mastery = SkillMastery::Master;
    CharacterAttackResult masterShot;
    masterShot.mode = CharacterAttackMode::Bow;
    masterShot.canAttack = true;
    rules.gameRules().combat.resolveCharacterAttack(masterShot, context);
    CHECK_FALSE(masterShot.fireArrow);
}

TEST_CASE("MAW monster missiles home on the party only while it moves slowly across their flight (L3.5)")
{
    GameplayProjectileService::ProjectileState projectile;
    projectile.velocityX = 1000.0f;
    GameplayProjectileService::ProjectileHoming homing;
    homing.turnRadiansPerSecond = 1000.0f;
    homing.speed = 1000.0f;
    // 60 degrees a second: 1 degree in a 1/60 s step, 0.5 degrees in a 1/120 s one.
    homing.lockRadiansPerSecond = 60.0f * 3.14159265f / 180.0f;
    projectile.homing = homing;

    // The party just off the line of flight: the missile turns onto it.
    GameplayWorldPoint target = {1000.0f, 5.0f, 0.0f};
    GameplayProjectileService::steerHomingProjectile(projectile, &target, 0.016f);
    CHECK_FALSE(projectile.homing->lost);
    CHECK(projectile.velocityY > 0.0f);

    // A sidestep out of the cone: it flies straight on, but the lock is tested again each frame (FSPS-2-10).
    target = {1000.0f, 200.0f, 0.0f};
    const float velocityY = projectile.velocityY;
    GameplayProjectileService::steerHomingProjectile(projectile, &target, 0.016f);
    CHECK_FALSE(projectile.homing->lost);
    CHECK(projectile.velocityY == doctest::Approx(velocityY));

    // Walking back into its line, the party is taken again.
    target = {projectile.x + projectile.velocityX, projectile.y + projectile.velocityY + 5.0f, 0.0f};
    GameplayProjectileService::steerHomingProjectile(projectile, &target, 0.016f);
    CHECK(projectile.velocityY > velocityY);

    // The lock is a rate, the same at any frame rate: a party 0.75 degrees off its flight is held over a 1/60 s step,
    // but not over a 1/120 s one (it moved faster across the flight than 60 degrees a second).
    const auto steeredWithin = [&](float stepSeconds)
    {
        GameplayProjectileService::ProjectileState straight;
        straight.velocityX = 1000.0f;
        straight.homing = homing;
        const float offRadians = 0.75f * 3.14159265f / 180.0f;
        GameplayWorldPoint offTarget = {1000.0f * std::cos(offRadians), 1000.0f * std::sin(offRadians), 0.0f};
        GameplayProjectileService::steerHomingProjectile(straight, &offTarget, stepSeconds);
        return straight.velocityY > 0.0f;
    };
    CHECK(steeredWithin(1.0f / 60.0f));
    CHECK_FALSE(steeredWithin(1.0f / 120.0f));

    // The fanned and falling spells never home: Meteor Shower, Sparks, Starburst, Poison Spray, Ice Blast, Shrapmetal.
    RulesetOptions options;
    MawRules rules(options, MawMapLevels{}, installedItemData());
    const CombatRules &combat = rules.gameRules().combat;
    CHECK(combat.monsterMissileHomingLockRate(spellIdValue(SpellId::FireBolt)) > 0.0f);
    CHECK(combat.monsterMissileHomingLockRate(0) > 0.0f);

    for (SpellId spell : {SpellId::MeteorShower, SpellId::Sparks, SpellId::Starburst, SpellId::PoisonSpray,
             SpellId::IceBlast, SpellId::Shrapmetal})
    {
        CHECK(combat.monsterMissileHomingLockRate(spellIdValue(spell)) == doctest::Approx(0.0f));
    }

    options.preferences.homingProjectiles = false;
    rules.setOptions(options);
    CHECK(combat.monsterMissileHomingLockRate(0) == doctest::Approx(0.0f));
}

TEST_CASE("MAW blasters shoot with the melee rows and put the bow away (A1.11)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    Character gunner;
    gunner.className = "Knight";
    gunner.level = 30;
    gunner.equipment.mainHand = 866;
    gunner.equipment.bow = 56;
    gunner.skills["Blaster"] = {"Blaster", 10, SkillMastery::Expert};
    gunner.skills["Bow"] = {"Bow", 10, SkillMastery::Expert};
    const CharacterCombatRows rows = mawCombatRows(rules, gunner, items, {50, 50, 50});
    REQUIRE(rows.blasterDamage);
    CHECK_EQ(rows.blasterDamage->first, rows.meleeMinimumDamage);
    CHECK_EQ(rows.blasterDamage->second, rows.meleeMaximumDamage);
    // The bow's rows are gone: only Might's share is left of the ranged damage.
    CHECK(rows.rangedMaximumDamage < 10);
}

TEST_CASE("MAW dimension map drops read the monster level capped at 255 (audit ALC-4)")
{
    MawDimensionData dimensions;
    std::string error;
    REQUIRE_MESSAGE(
        dimensions.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/dimension_maps.yml"), error), error);
    const MercenaryMap world;
    const MapStats mapStats = installedMapStats();
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData(), MawPromotionData{}, MawCraftingData{},
        MawTextData{}, dimensions);
    rules.setMapTable(&mapStats);
    rules.state().dimensionQuest.done = true;

    for (uint16_t mapId : dimensions.dungeons())
    {
        if (const MapStatsEntry *pMap = mapStats.findById(mapId))
        {
            std::string fileName = pMap->fileName;
            std::transform(fileName.begin(), fileName.end(), fileName.begin(),
                [](unsigned char c) { return char(std::tolower(c)); });
            rules.state().completedMaps.insert(fileName);
        }
    }

    REQUIRE_FALSE(rules.dimensionMapPool().empty());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(194);
    ActorRulesetFacts facts = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
    CorpseLootContext context;
    context.pStats = &stats;
    context.pMonsterTable = &world.monsters;
    context.pFacts = &facts;
    context.pMap = &world.map;
    const auto mapDrops = [&](int level)
    {
        int drops = 0;
        facts.level = level;

        for (uint32_t actorIndex = 0; actorIndex < 400; ++actorIndex)
        {
            // Enough bad luck behind that the base chance is about 20 %: 0.001^(1.38 - 0.001 x 2294 x 0.5).
            rules.state().mapDropPity = 2294;
            rules.state().mapsDropped.clear();
            context.actorIndex = actorIndex;

            for (const CorpseLoot::ExtraItem &item : monsters.corpseLoot(context).extraItems)
            {
                drops += item.itemId == dimensions.mapItemId() ? 1 : 0;
            }
        }

        return drops;
    };

    const int low = mapDrops(std::max(dimensions.dropLevelRequired(), 100));
    const int capped = mapDrops(255);
    CHECK(low < capped);
    CHECK_EQ(mapDrops(1000), capped);
}

TEST_CASE("MAW's Crafting Cube moves a Plane of Earth map among the indoor maps (audit ALC-15, MAW 54f1ef13)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawDimensionData dimensions;
    std::string error;
    REQUIRE_MESSAGE(
        dimensions.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/dimension_maps.yml"), error), error);
    const MapStats mapStats = installedMapStats();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData(), MawPromotionData{}, installedCraftingData(),
        MawTextData{}, dimensions);
    rules.setMapTable(&mapStats);

    for (uint16_t mapId : dimensions.dungeons())
    {
        if (const MapStatsEntry *pMap = mapStats.findById(mapId))
        {
            std::string fileName = pMap->fileName;
            std::transform(fileName.begin(), fileName.end(), fileName.begin(),
                [](unsigned char c) { return char(std::tolower(c)); });
            rules.state().completedMaps.insert(fileName);
        }
    }

    InventoryItem map;
    map.objectDescriptionId = dimensions.mapItemId();
    MawDimensionMap earth;
    earth.mapId = 10;
    earth.power = 10;
    ItemRulesetFields fields;
    earth.writeFields(fields);
    map.rulesetFields = fields;
    InventoryItem cube;
    cube.objectDescriptionId = 1070;
    CraftingContext context;
    context.pItemTable = &gameData.itemTable;
    context.ownerLevel = 200;

    for (uint32_t seed = 1; seed <= 10; ++seed)
    {
        map.rulesetFields.craftSeed = seed;
        const CraftResult result = rules.gameRules().crafting.craft(map, cube, context);
        REQUIRE(result.possible);
        const MapStatsEntry *pTarget = mapStats.findById(MawDimensionMap::fromFields(result.target.rulesetFields).mapId);
        REQUIRE(pTarget != nullptr);
        INFO(pTarget->fileName);
        CHECK(pTarget->fileName.ends_with(".blv"));
    }
}

TEST_CASE("MAW chests: gold from the map's level, removed potions rerolled, placed equipment filtered (L4.4)")
{
    const MercenaryMap mercenaries;
    const MapStats mapStats = installedMapStats();
    RulesetOptions options;
    MawRules rules(options, mercenaries.mapLevels, installedItemData());
    rules.setMapTable(&mapStats);
    rules.setCurrentMap("out05.odm");
    const ItemRules &items = rules.gameRules().items;
    std::mt19937 rng(11);

    // 10 x (band mean 25 + bolster 0) x 1, 2 or 4 by the pile x 0.66-1.32.
    for (int roll = 0; roll < 50; ++roll)
    {
        const std::optional<uint32_t> small = items.chestGoldAmount(0, rng);
        const std::optional<uint32_t> large = items.chestGoldAmount(2, rng);
        REQUIRE(small);
        REQUIRE(large);
        CHECK(*small >= 165);
        CHECK(*small <= 330);
        CHECK(*large >= 660);
        CHECK(*large <= 1320);
    }

    // A higher bank bolsters it: 10 x (25 + 46) at level 50 banked elsewhere.
    rules.state().continentLevels = {0, 50, 0, 0};
    const MapStatsEntry *pMap = mapStats.findByFileName("out05.odm");
    REQUIRE(pMap != nullptr);
    CHECK(rules.mapBolster(*pMap) > 0);
    const uint32_t bolstered = *items.chestGoldAmount(1, rng);
    CHECK(bolstered >= uint32_t(20 * (25 + rules.mapBolster(*pMap)) * 0.66) - 1);
    CHECK_FALSE(standardItemRules().chestGoldAmount(0, rng).has_value());

    // The removed potions become black ones; nothing else changes.
    for (int roll = 0; roll < 50; ++roll)
    {
        const uint32_t placed = items.placedItemId(270, rng);
        CHECK(placed >= 252);
        CHECK(placed <= 263);
    }

    CHECK_EQ(items.placedItemId(222, rng), 222u);
    CHECK_EQ(items.placedItemId(290, rng), 290u);
    CHECK_EQ(standardItemRules().placedItemId(270, rng), 270u);

    // Placed equipment MAW never rolled ranks as Common plus one per enchantment.
    ItemDefinition longsword;
    longsword.itemId = 1;
    longsword.equipStat = "Weapon";
    // Items without a price are never filtered (DEVIATIONS 182).
    longsword.value = 100;
    InventoryItem sword;
    sword.objectDescriptionId = 1;
    CHECK_EQ(items.lootFilterFacts(sword, longsword)->rarity, 1);
    CHECK_FALSE(items.nameColor(sword).has_value());
    sword.standardEnchantId = 1;
    CHECK_EQ(items.lootFilterFacts(sword, longsword)->rarity, 2);
    // Its name takes the same colour: one enchantment is Uncommon green, two Rare blue (zzMaw-Items.lua:1741-1747).
    CHECK_EQ(items.nameColor(sword), std::optional<uint32_t>(0x1eff00));
    sword.specialEnchantId = 1;
    CHECK_EQ(items.nameColor(sword), std::optional<uint32_t>(0x0096ff));
    sword.specialEnchantId = 0;
    // An item stored as Common and enchanted later still colours by its enchantments (OY-438); Ancient keeps its own.
    sword.rulesetFields.lootRarity = uint8_t(MawRarity::Common);
    CHECK_EQ(items.nameColor(sword), std::optional<uint32_t>(0x1eff00));
    sword.rulesetFields.lootRarity = uint8_t(MawRarity::Ancient);
    CHECK_EQ(items.nameColor(sword), std::optional<uint32_t>(0xff8000));
    sword.rulesetFields.lootRarity = 0;
    // A potion has no rarity: it is a kind, switched whole.
    ItemDefinition cureWounds;
    cureWounds.itemId = 222;
    cureWounds.equipStat = "Bottle";
    cureWounds.value = 10;
    InventoryItem potion;
    potion.objectDescriptionId = 222;
    CHECK(items.lootFilterFacts(potion, cureWounds)->kind == RulesetLootKind::Potions);
    CHECK_EQ(items.lootFilterFacts(potion, cureWounds)->rarity, 0);
    potion.standardEnchantId = 5;
    CHECK_FALSE(items.nameColor(potion).has_value());
}

TEST_CASE("MAW item popups: Legendary 19 in the range, resistances as reductions, live counts (L4.6, A2.14)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const ItemRules &items = rules.gameRules().items;
    const ItemDefinition longsword = itemDefinition(1, "Weapon", "Sword");
    InventoryItem blade;
    blade.objectDescriptionId = 1;
    blade.specialEnchantId = 4;
    blade.rulesetFields.itemPower = 20;
    const MawEnchantRange range =
        mawEnchantDamageRange(rules.model(1).weaponLevelDamage(100, false, 0), 3, 4, 0.2, false);
    Character viewer;
    wearLegendary(viewer, 19);
    CHECK_EQ(items.enchantDescription(blade, longsword, nullptr, nullptr, &viewer),
        "Adds " + std::to_string(int(std::floor(range.minimum * 1.5))) + "-"
            + std::to_string(int(std::floor(range.maximum * 1.5))) + " points of Cold damage.");

    // A ring's +40 fire resistance: (40 + 10) / 2 = 25 points, a fifth of the damage stopped.
    const ItemDefinition ring = itemDefinition(137, "Ring", "Misc");
    InventoryItem band;
    band.objectDescriptionId = 137;
    band.identified = true;
    band.standardEnchantId = 11;
    band.standardEnchantPower = 40;
    band.rulesetFields.lootRarity = uint8_t(MawRarity::Rare);
    const auto texts = [&](const InventoryItem &item, const Character *pViewer)
    {
        std::vector<std::string> result;

        for (const ItemInspectLine &line : items.inspectLines(item, ring, nullptr, nullptr, pViewer))
        {
            result.push_back(line.text);
        }

        return result;
    };
    const auto has = [](const std::vector<std::string> &lines, const std::string &text)
    {
        return std::any_of(lines.begin(), lines.end(),
            [&text](const std::string &line) { return line.find(text) != std::string::npos; });
    };
    CHECK(has(texts(band, nullptr), " +20%"));

    // Legendaries 21 and 22 count the monsters near the party now.
    rules.setNearbyMonsters(3);
    band.rulesetFields.legendaryAffixId = 21;
    CHECK(has(texts(band, nullptr), "Current bonus Damage: 15%"));
    band.rulesetFields.legendaryAffixId = 22;
    CHECK(has(texts(band, nullptr), "Current Reduction: 8.73%"));
}

TEST_CASE("MAW Legendary 17 on missiles and spells, 18 and 22 against hits (L4.1)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const CombatRules &combat = rules.gameRules().combat;
    Character mage;
    mage.className = "Sorcerer";
    wearLegendary(mage, 17);
    const auto spellHit = [&](uint32_t spellId, const Character *pAttacker)
    {
        MonsterDamageHit hit;
        hit.amount = 1000;
        hit.type = CombatDamageType::Fire;
        hit.pMissileAttacker = pAttacker;
        hit.missileSpellId = spellId;
        hit.pItemTable = &items;
        hit.targetCurrentHp = 10000;
        std::mt19937 rng(5);
        hit.pRng = &rng;
        return combat.damageToMonster(hit);
    };

    // 2 % of 10000 HP on a single-target spell (x 1.015^0), half on an area spell.
    const int plain = spellHit(11, nullptr);
    CHECK_EQ(spellHit(11, &mage) - plain, 200);
    CHECK_EQ(spellHit(6, &mage) - plain, 100);
    Character noAffix;
    CHECK_EQ(spellHit(11, &noAffix), plain);

    // 18: 10 % off every hit; 22: 3 % per nearby monster.
    Character member;
    member.level = 20;
    member.maxHealth = 500;
    member.health = 500;
    const auto taken = [&](const Character &target)
    {
        CharacterDamageHit hit;
        hit.amount = 100;
        hit.pCharacter = &target;
        hit.monsterAttack = true;
        hit.attackerLevel = 20;
        hit.attackerFacts.level = 20;
        hit.attackerFacts.familyLevel = 20;
        hit.attackerFacts.tier = 2;
        hit.attackerFacts.attack1Damage = 100;
        std::mt19937 rng(9);
        hit.pRng = &rng;
        return combat.damageToCharacter(hit);
    };
    const int base = taken(member);
    REQUIRE(base > 20);
    Character tough = member;
    wearLegendary(tough, 18);
    CHECK(taken(tough) == doctest::Approx(base * 0.9).epsilon(0.03));
    Character crowd = member;
    wearLegendary(crowd, 22);
    rules.setNearbyMonsters(5);
    CHECK(taken(crowd) == doctest::Approx(base * std::pow(0.97, 5)).epsilon(0.03));
}

TEST_CASE("Carnage bows shoot exploding fire arrows; MAW's deal a quarter (D.5)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    Character archer;
    ItemEnchantRuntime::applySpecialEnchantBonus(archer, SpecialItemEnchantKind::Carnage);
    CHECK(archer.equippedItemEffectFlags.contains("ExplosiveArrows"));

    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    archer.className = "Archer";
    archer.level = 20;
    archer.equipment.bow = 56;
    archer.skills["Bow"] = {"Bow", 10, SkillMastery::Expert};
    const auto shoot = [&](bool explosive)
    {
        CharacterAttackResult attack;
        attack.mode = CharacterAttackMode::Bow;
        attack.canAttack = true;
        attack.explosiveArrow = explosive;
        CharacterAttackOnMonster context;
        context.pCharacter = &archer;
        context.pItemTable = &items;
        context.minimumDamage = 100;
        context.maximumDamage = 200;
        std::mt19937 rng(4);
        context.pRng = &rng;
        rules.gameRules().combat.resolveCharacterAttack(attack, context);
        return attack;
    };
    const CharacterAttackResult plain = shoot(false);
    const CharacterAttackResult carnage = shoot(true);
    REQUIRE(plain.maximumDamage > 40);
    CHECK(carnage.maximumDamage == doctest::Approx(plain.maximumDamage * 0.25).epsilon(0.05));
    CHECK(carnage.minimumDamage == doctest::Approx(plain.minimumDamage * 0.25).epsilon(0.1));
}

TEST_CASE("MAW artifacts: on-hit spells, Ethric's Staff, Cycle of Life, the Horn of Ros, Excalibur (L4.3)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.setSpellTable(&gameData.spellTable);
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    REQUIRE(party.members().size() >= 4);
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    GameplayRuntimeActorState actor = {};
    actor.preciseX = 1024.0f;
    actor.height = 128;
    actor.hostileToParty = true;
    const size_t actorIndex = world.addActor(actor);
    const CombatRules &combat = rules.gameRules().combat;
    combat.updateCombat(party, world, 0.016f);

    // Splitter casts Fireball on the monster it strikes, at the wielder's Axe skill.
    Character &axeman = *party.member(0);
    axeman.equipment.mainHand = 1308;
    axeman.skills["Axe"] = {"Axe", 8, SkillMastery::Expert};
    const ActorRulesetFacts target;
    PartyHitOnMonster hit;
    hit.memberIndex = 0;
    hit.damage = 10;
    hit.pTarget = &target;
    hit.melee = true;
    hit.pWorld = &world;
    hit.targetActorIndex = actorIndex;
    combat.applyPartyHitEffects(party, hit);
    combat.updateCombat(party, world, 0.016f);
    REQUIRE_EQ(world.projectileRequests().size(), 1u);
    CHECK_EQ(world.projectileRequests().front().spellId, spellIdValue(SpellId::Fireball));

    // Thor casts its Lightning Bolt only on a monster that survives.
    axeman.equipment.mainHand = 2021;
    axeman.skills["Mace"] = {"Mace", 8, SkillMastery::Expert};
    hit.killed = true;
    combat.applyPartyHitEffects(party, hit);
    combat.updateCombat(party, world, 0.016f);
    CHECK_EQ(world.projectileRequests().size(), 1u);
    axeman.equipment.mainHand = 0;

    // Every 5 game minutes: Ethric's Staff drains 3 HP from all but a Lich; Cycle of Life pulls its wearer up.
    for (size_t index = 0; index < 4; ++index)
    {
        Character &member = *party.member(index);
        member.className = "Knight";
        member.conditions.reset();
        member.maxHealth = 200;
    }

    Character &wearer = *party.member(0);
    wearer.equipment.ring1 = 543;
    wearer.health = 10;
    party.member(1)->health = 100;
    party.member(2)->health = 60;
    party.member(2)->className = "Lich";
    party.member(2)->equipment.mainHand = 1317;
    party.member(3)->health = 5;
    party.member(3)->equipment.mainHand = 1317;
    world.advanceGameMinutes(5);
    combat.updateCombat(party, world, 0.016f);
    // Pool 170 over 3, middle 56: the donors give half of what they hold above it (22 and 2).
    CHECK_EQ(wearer.health, 34);
    CHECK_EQ(party.members()[1].health, 78);
    CHECK_EQ(party.members()[2].health, 58);
    CHECK_EQ(party.members()[3].health, 2);
    // Not again until the next tick.
    combat.updateCombat(party, world, 0.016f);
    CHECK_EQ(party.members()[3].health, 2);

    // The Horn of Ros carried anywhere keeps Detect Life on the party.
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::DetectLife));
    InventoryItem horn;
    horn.objectDescriptionId = 2055;
    party.member(1)->inventory.push_back(horn);
    world.advanceGameMinutes(1);
    combat.updateCombat(party, world, 0.016f);
    CHECK(party.hasPartyBuff(PartyBuffId::DetectLife));

    // The Ghost Ring keeps Preservation on its wearer.
    party.member(2)->equipment.ring2 = 1347;
    world.advanceGameMinutes(1);
    combat.updateCombat(party, world, 0.016f);
    CHECK(party.hasCharacterBuff(2, CharacterBuffId::Preservation));
    CHECK_FALSE(party.hasCharacterBuff(1, CharacterBuffId::Preservation));

    // Excalibur blesses its wielder's swings without a Bless aura.
    Character knight;
    CHECK_FALSE(rules.blessHitSkill(knight).has_value());
    knight.equipment.mainHand = 2023;
    REQUIRE(rules.blessHitSkill(knight).has_value());
    CHECK(*rules.blessHitSkill(knight) == doctest::Approx(0.0));
}

TEST_CASE("MAW legendary affixes on kills, lethal hits, skills and damage stacks (L4.1)")
{
    RulesetOptions options;
    MawRules rules(options, MawMapLevels{}, installedItemData());
    PartySeed seed;
    seed.members.resize(2);
    seed.members[0].className = "Knight";
    seed.members[0].level = 30;
    seed.members[0].maxHealth = 400;
    seed.members[0].health = 100;
    seed.members[1] = seed.members[0];
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    const CombatRules &combat = rules.gameRules().combat;
    Character &killer = *party.member(0);
    const ActorRulesetFacts target;
    PartyHitOnMonster hit;
    hit.damage = 50;
    hit.pTarget = &target;
    hit.melee = true;
    hit.killed = true;

    // 24: a kill restores 10 % of full HP; 11: a single-target kill halves the recovery.
    wearLegendary(killer, 24);
    const int full = Party::effectiveMaximumHealth(killer);
    combat.applyPartyHitEffects(party, hit);
    CHECK_EQ(killer.health, 100 + full / 10);
    // A killing blow's own recovery is halved before it is applied (CMB-2); a spell kill halves what the cast set.
    wearLegendary(killer, 11);
    CHECK_EQ(combat.killRecoveryScale(killer), doctest::Approx(0.5f));
    CHECK_EQ(standardGameRules().combat.killRecoveryScale(killer), doctest::Approx(1.0f));
    hit.melee = false;
    hit.spellId = 2;
    killer.recoverySecondsRemaining = 2.0f;
    combat.applyPartyHitEffects(party, hit);
    CHECK(killer.recoverySecondsRemaining == doctest::Approx(1.0f));
    hit.spellId = 6;
    killer.recoverySecondsRemaining = 2.0f;
    combat.applyPartyHitEffects(party, hit);
    CHECK(killer.recoverySecondsRemaining == doctest::Approx(2.0f));

    // 13: monsters' special attacks pass the wearer by.
    CHECK_FALSE(combat.immuneToMonsterSpecialAttacks(killer));
    wearLegendary(killer, 13);
    CHECK(combat.immuneToMonsterSpecialAttacks(killer));

    // 15: a lethal hit leaves a quarter of full HP, once per 150 game minutes.
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    combat.updateCombat(party, world, 0.0f);
    wearLegendary(killer, 15);
    killer.health = 100;
    REQUIRE(party.applyDamageToMember(0, 5000, ""));
    CHECK_EQ(killer.health, Party::effectiveMaximumHealth(killer) / 4);
    CHECK(killer.rulesetState.legendaryProtectionReadyGameMinutes == doctest::Approx(150));
    REQUIRE(party.applyDamageToMember(0, 5000, ""));
    CHECK(killer.health < 0);

    // 25 and 33: Ascension and the melee skills +10, from the item that carries them.
    Character wearer;
    wearer.equipment.amulet = 1;
    wearer.equipmentRuntime.amulet.rulesetFields.legendaryAffixId = 25;
    Character bonuses;
    rules.gameRules().items.applyEquippedEnchantEffects(itemDefinition(1, "Amulet", "Misc"),
        wearer.equipmentRuntime.amulet, nullptr, nullptr, wearer, bonuses);
    CHECK_EQ(bonuses.itemSkillBonuses["Learning"], 10);
    wearer.equipmentRuntime.amulet.rulesetFields.legendaryAffixId = 33;
    Character melee;
    rules.gameRules().items.applyEquippedEnchantEffects(itemDefinition(1, "Amulet", "Misc"),
        wearer.equipmentRuntime.amulet, nullptr, nullptr, wearer, melee);
    CHECK_EQ(melee.itemSkillBonuses["Sword"], 10);
    CHECK_EQ(melee.itemSkillBonuses["Mace"], 10);

    // 29: each attack, this one included, adds 1 % to every later hit; a missile's too.
    Character archer;
    wearLegendary(archer, 29);
    const auto struck = [&](double stacks, const Character *pMissileAttacker)
    {
        MonsterDamageHit damage;
        damage.amount = 1000;
        damage.type = CombatDamageType::Fire;
        damage.targetFacts.legendaryDamageTaken = float(stacks);
        damage.pMissileAttacker = pMissileAttacker;
        std::mt19937 rng(2);
        damage.pRng = &rng;
        return combat.damageToMonster(damage);
    };
    const int plain = struck(0, nullptr);
    CHECK(double(struck(10, nullptr)) / plain == doctest::Approx(1.10).epsilon(0.005));
    CHECK(double(struck(10, &archer)) / plain == doctest::Approx(1.11).epsilon(0.005));
}

TEST_CASE("MAW legendaries 15, 18/22, 24, 27 and 30 in MAW's order and on MAW's pools (audit ITM-L3..L7)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    RulesetOptions nightmare;
    nightmare.difficulty = RulesetDifficulty::Nightmare;
    MawRules rules(nightmare, MawMapLevels{}, installedItemData());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(OpenYAMM::Tests::regressionGameData());
    party.setRules(&rules.gameRules());
    const CombatRules &combat = rules.gameRules().combat;
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    combat.updateCombat(party, world, 0.0f);
    Character &mage = *party.member(0);

    // L3: Mana Shield takes its share first; legendary 15 only acts on what is still lethal after it.
    mage.maxHealth = 400;
    mage.health = 100;
    mage.maxSpellPoints = 100000;
    mage.spellPoints = 100000;
    mage.skills["ManaShield"] = {"ManaShield", 30, SkillMastery::Grandmaster};
    wearLegendary(mage, 15);
    const int absorbed = combat.absorbCharacterDamage(party, 0, 150);
    CHECK(absorbed < 100);
    CHECK(mage.rulesetState.legendaryProtectionReadyGameMinutes == doctest::Approx(0));

    // L4: legendary 18 cuts before the flat class reduction: 100 x 0.9 - 50 = 40.
    MawMitigationInputs inputs;
    inputs.damage = 100;
    inputs.type = CombatDamageType::Physical;
    inputs.flatReduction = 50;
    inputs.legendaryMultiplier = 0.9;
    CHECK_EQ(int(mawMitigatedDamage(inputs)), 40);

    // L7: legendary 30's death threshold is the higher bar times the Mana Shield efficiency: 1000 x 2.95 here, so
    // -2500 HP does not eradicate in Nightmare (it would at 1000: below -2 x 1000).
    mage.maxHealth = 1000;
    mage.maxSpellPoints = 200;
    mage.spellPoints = 0;
    mage.health = 1000;
    wearLegendary(mage, 30);
    REQUIRE(mawManaShieldEfficiency(30) > 2.5);
    mage.skills["ManaShield"] = {"ManaShield", 30, SkillMastery::Grandmaster};
    REQUIRE(party.applyDamageToMember(0, 3500, ""));
    CHECK(mage.health <= -2500);
    CHECK_FALSE(mage.conditions.test(size_t(CharacterCondition::Eradicated)));

    // L5: legendary 24 restores 5 % of the SP pool left after an aura holds back its share.
    Character &killer = *party.member(1);
    killer.maxSpellPoints = 1000;
    const SpellRules &spells = rules.gameRules().spells;
    int reserved = 0;

    for (const uint32_t aura : {3u, 5u, 14u, 17u, 38u, 46u, 83u, 85u})
    {
        rules.state().auraHolders = {{aura, 1}};
        spells.updateAuras(party, 0.5f);
        reserved = spells.reservedSpellPoints(party, 1);

        if (reserved > 0)
        {
            break;
        }
    }

    REQUIRE(reserved > 0);
    killer.spellPoints = 0;
    wearLegendary(killer, 24);
    const ActorRulesetFacts target;
    PartyHitOnMonster kill;
    kill.memberIndex = 1;
    kill.damage = 50;
    kill.pTarget = &target;
    kill.melee = true;
    kill.killed = true;
    combat.applyPartyHitEffects(party, kill);
    CHECK_EQ(killer.spellPoints, int((Party::effectiveMaximumSpellPoints(killer) - reserved) * 0.05));
    rules.state().auraHolders.clear();

    // L6: legendary 27 sends a leech's overheal to the lowest member, an unconscious one too.
    Character &biter = *party.member(2);
    biter.equipment.mainHand = 508;
    biter.health = Party::effectiveMaximumHealth(biter);
    wearLegendary(biter, 27);
    Character &fallen = *party.member(3);
    fallen.health = -5;
    party.applyMemberCondition(3, CharacterCondition::Unconscious);
    ActorRulesetFacts monster;
    monster.level = 30;
    monster.familyLevel = 30;
    monster.tier = 2;
    monster.maxHp = 500;
    PartyHitOnMonster bite;
    bite.memberIndex = 2;
    bite.damage = 400;
    bite.pTarget = &monster;
    bite.melee = true;
    combat.applyPartyHitEffects(party, bite);
    CHECK(fallen.health > -5);
}

TEST_CASE("MAW artifacts strike with their own damage and slow, speed and school bonuses (L4.3)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.state().continentLevels = {40, 0, 0, 0};

    // Supreme Plate, Excalibur's peers: x0.9 attack delay.
    Character knight;
    CHECK(mawArtifactAttackDelayMultiplier(rules, knight) == doctest::Approx(1.0));
    knight.equipment.armor = 515;
    CHECK(mawArtifactAttackDelayMultiplier(rules, knight) == doctest::Approx(0.9));

    // Wyrm Spitter (506) hits dragons twice as hard; Elsenrail (500) adds light.
    Character swordsman;
    swordsman.className = "Knight";
    swordsman.level = 40;
    swordsman.skills["Sword"] = {"Sword", 10, SkillMastery::Expert};
    swordsman.skills["Dagger"] = {"Dagger", 10, SkillMastery::Expert};
    const auto blow = [&](uint32_t weaponId, uint32_t kinds)
    {
        swordsman.equipment.mainHand = weaponId;
        CharacterAttackResult attack;
        attack.mode = CharacterAttackMode::Melee;
        attack.canAttack = true;
        attack.attackBonus = 10000;
        ActorRulesetFacts facts;
        facts.level = 40;
        CharacterAttackOnMonster context;
        context.pTargetFacts = &facts;
        context.pCharacter = &swordsman;
        context.pItemTable = &items;
        context.minimumDamage = 20;
        context.maximumDamage = 20;
        context.targetKindFlags = kinds;
        std::mt19937 rng(8);
        context.pRng = &rng;
        rules.gameRules().combat.resolveCharacterAttack(attack, context);
        return attack;
    };
    // The on-hit damage rides apart, by kind, to join after the boss affixes and legendaries (ITM-A7).
    const auto onHit = [](const CharacterAttackResult &attack, CombatDamageType type)
    {
        return attack.rulesLateDamage[size_t(type)];
    };
    const int plainWyrm = onHit(blow(506, 0), CombatDamageType::Physical);
    const int dragonWyrm = onHit(blow(506, monsterKindFlag(MonsterKind::Dragon)), CombatDamageType::Physical);
    CHECK(dragonWyrm > plainWyrm);
    CHECK(onHit(blow(500, 0), CombatDamageType::Light) > 0);

    // Crown of Final Dominion (521) gives Dark Magic half the trained skill.
    Character lich;
    lich.level = 40;
    lich.skills["DarkMagic"] = {"DarkMagic", 20, SkillMastery::Master};
    lich.equipment.helm = 521;
    Character bonuses;
    rules.gameRules().items.applyEquippedEnchantEffects(*items.get(521), lich.equipmentRuntime.helm, nullptr, nullptr,
        lich, bonuses);
    CHECK_EQ(bonuses.itemSkillBonuses["DarkMagic"], 10);
}

TEST_CASE("MAW shops want quest items only once their quest is done, and unique items once (A2.13)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    PartySeed seed;
    seed.members.resize(1);
    Party party;
    party.seed(seed);
    const ItemRules &items = rules.gameRules().items;
    InventoryItem quest;
    quest.objectDescriptionId = 1342;
    CHECK(items.sellRefusal(party, quest).has_value());
    party.setQuestBit(1564, true);
    CHECK_FALSE(items.sellRefusal(party, quest).has_value());

    // A sold unique item is bought once; the seer's bit is cleared to hand it out again.
    InventoryItem relic;
    relic.objectDescriptionId = 539;
    party.setQuestBit(1540, true);
    party.setQuestBit(199, true);
    REQUIRE_FALSE(items.sellRefusal(party, relic).has_value());
    items.itemSold(party, relic);
    CHECK_FALSE(party.hasQuestBit(199));
    CHECK_EQ(items.sellRefusal(party, relic).value_or(""), "I have already bought an item like that.");
    InventoryItem sword;
    sword.objectDescriptionId = 1;
    CHECK_FALSE(items.sellRefusal(party, sword).has_value());
}

TEST_CASE("MAW chest and ground loot drop at the map's own monsters' level (A2.9)")
{
    const MercenaryMap mercenaries;
    MawRules rules(RulesetOptions{}, mercenaries.mapLevels, installedItemData());
    rules.setCurrentMap(mercenaries.map.fileName);
    const std::unordered_map<int, int> &levels = rules.monsterLevels(mercenaries.monsters, mercenaries.map);
    REQUIRE(levels.contains(194));
    CHECK(rules.mapDropLevel() == doctest::Approx(levels.at(194)));

    // Without natives: 7/8 of the band's sum.
    MercenaryMap empty;
    empty.map.encounter1.pictureName.clear();
    MawRules fallback(RulesetOptions{}, empty.mapLevels, installedItemData());
    fallback.setCurrentMap(empty.map.fileName);
    fallback.monsterLevels(empty.monsters, empty.map);
    CHECK(fallback.mapDropLevel() == doctest::Approx(75 * 7 / 8.0));

    // Two families: only their B rows count, so the lower family's B level, not its C (audit MON-9).
    MercenaryMap two;
    REQUIRE(two.monsters.loadStatsFromRows({monsterRow(193, "Human Mercenary A", 10, "3d10"),
        monsterRow(194, "Human Mercenary B", 17, "3d10"), monsterRow(195, "Human Mercenary C", 24, "3d10"),
        monsterRow(196, "Bandit A", 35), monsterRow(197, "Bandit B", 40), monsterRow(198, "Bandit C", 45)}));
    two.map.encounter2.pictureName = "Bandit";
    MawRules twoFamilies(RulesetOptions{}, two.mapLevels, installedItemData());
    twoFamilies.setCurrentMap(two.map.fileName);
    const std::unordered_map<int, int> &twoLevels = twoFamilies.monsterLevels(two.monsters, two.map);
    REQUIRE(twoLevels.contains(194));
    REQUIRE(twoLevels.at(195) != twoLevels.at(194));
    CHECK(twoFamilies.mapDropLevel() == doctest::Approx(twoLevels.at(194)));

    // Another map's cached levels do not count: on a map without its own, the fallback of that map (audit ROB-2-2).
    twoFamilies.setCurrentMap("d01.blv");
    CHECK(twoFamilies.mapDropLevel() != doctest::Approx(twoLevels.at(194)));
}

namespace
{
// Records what the boss rules ask of the world.
class BossTestWorld : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    std::vector<size_t> spawnMonsters(const GameplayMonsterSpawnRequest &request) override
    {
        spawns.push_back(request);
        return {};
    }

    bool swapActorPlaces(size_t actorIndex, std::optional<size_t> otherActorIndex) override
    {
        swaps.emplace_back(actorIndex, otherActorIndex);
        return true;
    }

    bool launchParty(float headingRadians, float horizontalSpeed, float verticalSpeed) override
    {
        launches.push_back({headingRadians, horizontalSpeed, verticalSpeed});
        return true;
    }

    std::vector<GameplayMonsterSpawnRequest> spawns;
    std::vector<std::pair<size_t, std::optional<size_t>>> swaps;
    std::vector<std::array<float, 3>> launches;
};

GameplayRuntimeActorState bossActor(uint32_t actorId, int16_t monsterId, MawBossAffix affix, float x)
{
    GameplayRuntimeActorState actor = {};
    actor.actorId = actorId;
    actor.monsterId = monsterId;
    actor.preciseX = x;
    actor.radius = 32;
    actor.height = 128;
    actor.hostileToParty = true;
    actor.currentHp = 100;
    actor.maxHp = 100;
    actor.rulesetFacts.level = 30;
    actor.rulesetFacts.bossAffix = uint8_t(affix);
    return actor;
}
}

TEST_CASE("MAW bosses roll Swapper and Puller, Broodlords and Omnipotent ones (L3.1, L3.2)")
{
    RulesetOptions options;
    MawRules rules(options, MawMapLevels{}, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    int broodlords = 0;
    int omnipotent = 0;
    bool swapper = false;
    bool puller = false;
    constexpr int Bosses = 20000;

    for (uint64_t seed = 1; seed <= Bosses; ++seed)
    {
        ActorRulesetFacts facts;
        facts.level = 50;
        facts.familyLevel = 40;
        REQUIRE(monsters.makeBoss(facts, seed * 7919, 0));
        broodlords += facts.bossAffix == uint8_t(MawBossAffix::Broodlord) ? 1 : 0;
        omnipotent += facts.bossAffix == uint8_t(MawBossAffix::Omnipotent) ? 1 : 0;
        swapper = swapper || facts.bossAffix == uint8_t(MawBossAffix::Swapper);
        puller = puller || facts.bossAffix == uint8_t(MawBossAffix::Puller);

        if (facts.bossAffix == uint8_t(MawBossAffix::Omnipotent))
        {
            CHECK(facts.bossHealthMultiplier >= 10.0f);
            CHECK(facts.bossDamageMultiplier >= 2.0f);
        }
    }

    CHECK(swapper);
    CHECK(puller);
    CHECK(broodlords > Bosses * 0.007);
    CHECK(broodlords < Bosses * 0.013);
    CHECK(omnipotent > 3);
    CHECK(omnipotent < 50);

    // A forced affix is kept as given.
    ActorRulesetFacts broodling;
    broodling.level = 50;
    REQUIRE(monsters.makeBoss(broodling, 5, uint8_t(MawBossAffix::Broodling)));
    CHECK_EQ(broodling.bossAffix, uint8_t(MawBossAffix::Broodling));

    // Omnipotent has every affix; a Broodlord none of them.
    ActorRulesetFacts all;
    all.bossAffix = uint8_t(MawBossAffix::Omnipotent);
    CHECK(mawHasBossAffix(all, MawBossAffix::Swapper));
    CHECK(mawHasBossAffix(all, MawBossAffix::Shadow));
    CHECK_FALSE(mawHasBossAffix(all, MawBossAffix::Broodling));
    ActorRulesetFacts lord;
    lord.bossAffix = uint8_t(MawBossAffix::Broodlord);
    CHECK_FALSE(mawHasBossAffix(lord, MawBossAffix::Swapper));
    CHECK_EQ(monsters.actorBadges(lord), std::vector<std::string>{"maw_boss_skull"});
}

TEST_CASE("MAW special bosses hatch Broodlings and affix bosses as they die (L3.2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.setCurrentMap("out05.odm");
    const MonsterRules &monsters = rules.gameRules().monsters;
    BossTestWorld world;
    const size_t lord = world.addActor(bossActor(1, 195, MawBossAffix::Broodlord, 500));
    const size_t brood = world.addActor(bossActor(2, 195, MawBossAffix::Broodling, 600));
    const size_t small = world.addActor(bossActor(3, 193, MawBossAffix::Broodling, 700));
    const size_t god = world.addActor(bossActor(4, 195, MawBossAffix::Omnipotent, 800));
    // The later affixes hatch nothing.
    const size_t later = world.addActor(bossActor(5, 195, MawBossAffix::Skilled, 900));
    monsters.updateMonsters(world, 0.016f);
    CHECK(world.spawns.empty());

    for (const size_t index : {lord, brood, small, god, later})
    {
        world.actor(index).isDead = true;
        world.actor(index).currentHp = 0;
    }

    monsters.updateMonsters(world, 0.016f);
    // Broodlord: 3 C Broodlings; C Broodling: 3 B; A Broodling: none; Omnipotent: 14 affix bosses and 3 Broodlings.
    REQUIRE_EQ(world.spawns.size(), 2u + 15u);
    CHECK_EQ(world.spawns[0].monsterId, 195);
    CHECK_EQ(world.spawns[0].count, 3u);
    CHECK_EQ(world.spawns[0].bossAffix, uint8_t(MawBossAffix::Broodling));
    CHECK(world.spawns[0].boss);
    CHECK_EQ(world.spawns[1].monsterId, 194);
    CHECK_EQ(world.spawns[1].bossAffix, uint8_t(MawBossAffix::Broodling));
    CHECK_EQ(world.spawns[2].bossAffix, uint8_t(MawBossAffix::Summoner));
    CHECK_EQ(world.spawns[15].bossAffix, uint8_t(MawBossAffix::Shadow));
    CHECK_EQ(world.spawns[16].count, 3u);

    // The dead hatch once.
    monsters.updateMonsters(world, 0.016f);
    CHECK_EQ(world.spawns.size(), 17u);
}

TEST_CASE("MAW Omnipotent bounty targets bring 100-200 of their kin (audit MON-15)")
{
    // The hunt's boss comes out with the affix given here.
    class HuntWorld : public BossTestWorld
    {
    public:
        explicit HuntWorld(MawBossAffix affix)
            : m_affix(affix)
        {
        }

        std::vector<size_t> spawnMonsters(const GameplayMonsterSpawnRequest &request) override
        {
            spawns.push_back(request);
            return request.boss ? std::vector<size_t>{addActor(bossActor(99, request.monsterId, m_affix, 0))}
                                : std::vector<size_t>{};
        }

    private:
        MawBossAffix m_affix;
    };

    const MercenaryMap mercenaries;
    MawRules rules(RulesetOptions{}, mercenaries.mapLevels, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    HuntWorld omnipotent(MawBossAffix::Omnipotent);
    omnipotent.bindMonsterTable(&mercenaries.monsters);
    const std::optional<BountyTarget> target = monsters.spawnBountyTarget(omnipotent, 0, 0, 0, 7);
    REQUIRE(target);
    // The texts name the boss by its affix and a note marks it (GAPS H.11).
    CHECK_EQ(target->bossAffix, uint8_t(MawBossAffix::Omnipotent));
    CHECK_EQ(target->mapNote, "Bounty");
    REQUIRE_EQ(omnipotent.spawns.size(), 3u);
    CHECK(omnipotent.spawns[1].count >= 100);
    CHECK(omnipotent.spawns[1].count <= 200);
    CHECK_EQ(omnipotent.spawns[1].radius, 2048.0f);
    CHECK(omnipotent.spawns[2].count <= 15);

    HuntWorld plain(MawBossAffix::Swift);
    plain.bindMonsterTable(&mercenaries.monsters);
    REQUIRE(monsters.spawnBountyTarget(plain, 0, 0, 0, 7));
    CHECK_EQ(plain.spawns.size(), 2u);
}

TEST_CASE("MAW Regenerating bosses start each map unhit (audit ROB-2-4)")
{
    // Records the heals the boss rules give.
    class HealWorld : public BossTestWorld
    {
    public:
        bool healMapActor(size_t, int amount) override
        {
            healed += amount;
            return true;
        }

        int healed = 0;
    };

    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    HealWorld world;
    rules.setCurrentMap("out05.odm");
    const size_t boss = world.addActor(bossActor(1, 195, MawBossAffix::Regenerating, 5000));
    monsters.updateMonsters(world, 0.2f);
    // A drop in health is no party hit: the party's hits are counted with the actor (FCOR-2-6).
    world.actor(boss).currentHp = 50;
    monsters.updateMonsters(world, 0.2f);
    monsters.updateMonsters(world, 0.2f);
    CHECK_EQ(world.healed, 0);
    world.actor(boss).rulesetFacts.regeneratingHits = 1;
    monsters.updateMonsters(world, 0.2f);
    monsters.updateMonsters(world, 0.2f);
    REQUIRE(world.healed > 0);

    // The next map's runtime (here the same object) with an actor of the same id: no hit yet, no healing.
    rules.setCurrentMap("out06.odm");
    world.healed = 0;
    world.actor(boss).currentHp = 50;
    world.actor(boss).rulesetFacts.regeneratingHits = 0;
    monsters.updateMonsters(world, 0.2f);
    monsters.updateMonsters(world, 0.2f);
    CHECK_EQ(world.healed, 0);
}

TEST_CASE("MAW Leecher bosses drain one after another and carry the fractions (audit MON-12)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.setCurrentMap("out05.odm");
    const MonsterRules &monsters = rules.gameRules().monsters;
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(OpenYAMM::Tests::regressionGameData());
    party.setRules(&rules.gameRules());
    Character &member = *party.member(0);
    member.maxHealth = 10;
    member.health = 10;
    member.spellPoints = 0;
    BossTestWorld world;
    world.bindParty(&party);
    world.addActor(bossActor(1, 195, MawBossAffix::Leecher, 0));
    world.addActor(bossActor(2, 195, MawBossAffix::Leecher, 0));

    // At point blank each drains 5 % of 10 hit points a tick: half a point each, one point between the two.
    monsters.updateMonsters(world, 0.6f);
    CHECK_EQ(member.health, 9);
    monsters.updateMonsters(world, 0.6f);
    CHECK_EQ(member.health, 8);
}

TEST_CASE("MAW Swapper bosses swap places and turn hits aside; Pullers jump the party at them (L3.1)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const CombatRules &combat = rules.gameRules().combat;
    BossTestWorld world;
    const size_t swapper = world.addActor(bossActor(1, 195, MawBossAffix::Swapper, 1000));

    // Alone it takes the hit.
    CHECK_FALSE(combat.deflectsPartyHit(world, swapper));
    GameplayRuntimeActorState minion = bossActor(2, 193, MawBossAffix::None, 300);
    const size_t first = world.addActor(minion);
    minion.actorId = 3;
    const size_t second = world.addActor(minion);
    GameplayRuntimeActorState friendly = minion;
    friendly.actorId = 4;
    friendly.hostileToParty = false;
    world.addActor(friendly);
    CHECK(combat.deflectsPartyHit(world, swapper));
    REQUIRE_EQ(world.swaps.size(), 2u);
    CHECK_EQ(world.swaps[0].second, std::optional<size_t>(first));
    CHECK_EQ(world.swaps[1].second, std::optional<size_t>(second));
    CHECK_FALSE(combat.deflectsPartyHit(world, first));

    // Its own hits trade places with the party.
    PartySeed seed;
    seed.members.resize(1);
    seed.members[0].maxHealth = 100;
    seed.members[0].health = 100;
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    world.swaps.clear();
    combat.applyMonsterHitEffects(party, &world, 0, world.actor(swapper).rulesetFacts, 1, 10,
        CombatDamageType::Physical);
    REQUIRE_EQ(world.swaps.size(), 1u);
    CHECK_EQ(world.swaps[0].first, swapper);
    CHECK_FALSE(world.swaps[0].second.has_value());

    // A Puller to the east launches the party east at 1000 and 22.5 degrees up.
    const size_t puller = world.addActor(bossActor(5, 195, MawBossAffix::Puller, 2000));
    combat.applyMonsterHitEffects(party, &world, 0, world.actor(puller).rulesetFacts, 5, 10,
        CombatDamageType::Physical);
    REQUIRE_EQ(world.launches.size(), 1u);
    CHECK(world.launches[0][0] == doctest::Approx(0.0f));
    CHECK(world.launches[0][1] == doctest::Approx(923.88f).epsilon(0.001));
    CHECK(world.launches[0][2] == doctest::Approx(382.68f).epsilon(0.001));
}

TEST_CASE("MAW Broodlings drop items by tier (L3.2)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const auto chance = [&](int16_t monsterId, MawBossAffix affix)
    {
        const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(monsterId);
        ActorRulesetFacts facts = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
        facts.bossAffix = uint8_t(affix);
        CorpseLootContext context;
        context.pStats = &stats;
        context.pMonsterTable = &world.monsters;
        context.pFacts = &facts;
        context.pMap = &world.map;
        return monsters.corpseLoot(context).loot.itemChance;
    };
    CHECK_EQ(chance(195, MawBossAffix::Broodling), 30);
    CHECK_EQ(chance(194, MawBossAffix::Broodling), 10);
    CHECK_EQ(chance(193, MawBossAffix::Broodling), 4);
    CHECK_EQ(chance(195, MawBossAffix::Swapper), 100);
}

TEST_CASE("MAW unique monsters level with the party, not the map (A3.4)")
{
    const MercenaryMap world;
    RulesetOptions options;
    MawRules rules(options, world.mapLevels, installedItemData());
    rules.state().continentLevels = {0, 40, 0, 0};
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(193);

    // Placing the map marks its named monsters (1-219) unique; NPCs and others stay as they are.
    ActorRulesetFacts unique = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts;
    ActorRulesetFacts plain = unique;
    std::vector<MapMonsterPlacement> placements = {
        {&stats, true, true, &unique, 12}, {&stats, true, true, &plain, 0}};
    monsters.placeMapMonsters(world.context(), placements);
    CHECK(unique.unique);
    CHECK_FALSE(plain.unique);

    // Free progression: its own level 10 climbed by the 40 levels banked elsewhere, without MAW's -4.
    const double banked = rules.state().levelOutside(world.map.mergedContinentId);
    CHECK_EQ(monsters.resolveMonster(world.context(&unique), stats, nullptr).rulesetFacts.level,
        int(mawRound(mawBolsteredLevel(banked, 10))));
    CHECK_NE(monsters.resolveMonster(world.context(&plain), stats, nullptr).rulesetFacts.level,
        int(mawRound(mawBolsteredLevel(banked, 10))));

    // Horizontal progression away from the starting maps: 2.5 x its level.
    options.progression = RulesetProgression::Horizontal;
    rules.setOptions(options);
    CHECK_EQ(monsters.resolveMonster(world.context(&unique), stats, nullptr).rulesetFacts.level, 25);
    // Beyond Madness on a map without a fixed level: 3 x its level (P9.M3).
    options.challengeMode = RulesetChallengeMode::BeyondMadness;
    options.difficulty = RulesetDifficulty::Nightmare;
    rules.setOptions(options);
    CHECK_EQ(monsters.resolveMonster(world.context(&unique), stats, nullptr).rulesetFacts.level, 30);
}

TEST_CASE("MAW Shadow bosses blind the Wizard Eye aura too (A3.6)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    PartySeed seed;
    seed.members.resize(1);
    seed.members[0].className = "Sorcerer";
    seed.members[0].level = 10;
    seed.members[0].maxSpellPoints = 100;
    seed.members[0].spellPoints = 100;
    seed.members[0].skills["AirMagic"] = {"AirMagic", 5, SkillMastery::Expert};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    rules.state().auraHolders[12] = 0;
    rules.gameRules().spells.updateAuras(party, 0.5f);
    REQUIRE(party.hasPartyBuff(PartyBuffId::WizardEye));

    rules.setShadowBossNearby(true);
    party.clearPartyBuff(PartyBuffId::WizardEye);
    rules.gameRules().spells.updateAuras(party, 0.5f);
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::WizardEye));
    rules.setShadowBossNearby(false);
    rules.gameRules().spells.updateAuras(party, 0.5f);
    CHECK(party.hasPartyBuff(PartyBuffId::WizardEye));
}

TEST_CASE("MAW thins monster death drops: a fifth stay, a twenty-fifth of trophies and reagents (A3.9)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const ItemDefinition pelt = itemDefinition(633, "N / A", "Misc");
    const ItemDefinition reagent = itemDefinition(201, "Reagent", "Misc");
    const ItemDefinition other = itemDefinition(222, "Bottle", "Misc");
    std::mt19937 rng(17);
    const auto kept = [&](const ItemDefinition &item)
    {
        int count = 0;

        for (int roll = 0; roll < 20000; ++roll)
        {
            count += monsters.keepsDeathDrop(item, rng) ? 1 : 0;
        }

        return count / 20000.0;
    };
    CHECK(kept(other) == doctest::Approx(0.2).epsilon(0.1));
    CHECK(kept(pelt) == doctest::Approx(0.04).epsilon(0.2));
    CHECK(kept(reagent) == doctest::Approx(0.04).epsilon(0.2));
    CHECK(standardGameRules().monsters.keepsDeathDrop(pelt, rng));
}

TEST_CASE("MAW bounty maps put every monster at its table level plus the bounty, and their walkers shoot (A3.3)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData());
    rules.setCurrentMap("out05.odm");
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(195);
    const GameplayMonsterBolsterResult plain = monsters.resolveMonster(world.context(), stats, nullptr);
    CHECK_FALSE(plain.generatedAttack2);

    rules.setBountyLevel(30);
    const GameplayMonsterBolsterResult bounty = monsters.resolveMonster(world.context(), stats, nullptr);
    CHECK_EQ(bounty.rulesetFacts.level, 24 + 30);
    CHECK(bounty.generatedAttack2);
    CHECK(bounty.generatedAttack2IsRanged);

    // The flag follows the map: another map has no bounty.
    world.map.fileName = "out06.odm";
    CHECK_NE(monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts.level, 54);
}

TEST_CASE("MAW monster armour grows from the table's B level, weak diseases become poisons, any C row may be a boss (A3.8, A3.10, A3.11)")
{
    std::vector<std::string> weak = monsterRow(193, "Human Mercenary A", 10);
    weak[16] = "Disease1";
    std::vector<std::string> strong = monsterRow(195, "Human Mercenary C", 24);
    strong[16] = "Disease3";
    strong[5] = "30";
    MercenaryMap world;
    REQUIRE(world.monsters.loadStatsFromRows({weak, monsterRow(194, "Human Mercenary B", 17), strong}));
    world.map.fileName = "nowhere.odm";
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;

    const GameplayMonsterBolsterResult a = monsters.resolveMonster(world.context(), *world.monsters.findStatsById(193),
        nullptr);
    REQUIRE(a.rulesetFacts.level < 20);
    REQUIRE(a.specialAttackKind.has_value());
    CHECK_EQ(*a.specialAttackKind, MonsterSpecialAttackKind::PoisonWeak);

    // On Ravenshore's wilds the C keeps its disease; its armour is 30 x (L + 10) / (17 + 10).
    world.map.fileName = "out05.odm";
    const GameplayMonsterBolsterResult c = monsters.resolveMonster(world.context(), *world.monsters.findStatsById(195),
        nullptr);
    REQUIRE(c.rulesetFacts.level >= 20);
    CHECK_FALSE(c.specialAttackKind.has_value());
    CHECK_EQ(c.armorClass, int(mawRound(30.0 * (c.rulesetFacts.level + 10) / 27)));

    // Bosses are picked among non-hostile C rows too.
    RulesetOptions options;
    options.difficulty = RulesetDifficulty::Maw;
    rules.setOptions(options);
    std::vector<ActorRulesetFacts> facts(400, c.rulesetFacts);
    std::vector<MapMonsterPlacement> placements;

    for (ActorRulesetFacts &fact : facts)
    {
        placements.push_back({world.monsters.findStatsById(195), false, false, &fact});
    }

    REQUIRE(monsters.placeMapMonsters(world.context(), placements));
    CHECK(std::any_of(facts.begin(), facts.end(), [](const ActorRulesetFacts &f) { return f.bossAffix != 0; }));
}

TEST_CASE("MAW bosses are drawn larger and fast monsters keep their speed bonus for a fight (A3.12, A3.14)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    ActorRulesetFacts facts;
    CHECK(monsters.actorDrawScale(facts, false) == doctest::Approx(1.0f));
    facts.bossAffix = uint8_t(MawBossAffix::Thorn);
    CHECK(monsters.actorDrawScale(facts, true) == doctest::Approx(1.4f));
    CHECK(monsters.actorDrawScale(facts, false) == doctest::Approx(2.0f));
    facts.bossAffix = uint8_t(MawBossAffix::Omnipotent);
    CHECK(monsters.actorDrawScale(facts, false) == doctest::Approx(2.5f));
    CHECK(standardGameRules().monsters.actorDrawScale(facts, false) == doctest::Approx(1.0f));

    // A fast melee monster: the bonus speed for a fight, its own while calm.
    std::vector<std::string> row = monsterRow(193, "Human Mercenary A", 10);
    row[13] = "300";
    MercenaryMap world;
    REQUIRE(world.monsters.loadStatsFromRows({row, monsterRow(194, "Human Mercenary B", 17),
        monsterRow(195, "Human Mercenary C", 24)}));
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(193);
    REQUIRE(stats.speed == 300);
    const GameplayMonsterBolsterResult fast = monsters.resolveMonster(world.context(), stats, nullptr);
    CHECK_EQ(fast.moveSpeed, 300 + 50 + 100);
    CHECK_EQ(fast.calmMoveSpeed, 300);
}

TEST_CASE("MAW map completion: the Arena never, mdt15 one fewer, hidden hostiles only counts as cleared (A3.13)")
{
    MapKillProgress progress;
    progress.mapFileName = "d05.blv";
    progress.indoor = true;
    progress.countedMonsters = 200;
    progress.slainMonsters = 197;
    // 0.99^2 of 200 is needed: 197 of 200 is enough.
    MawMapCompletion completion = mawMapCompletion(progress, false);
    CHECK(completion.counts);
    CHECK(completion.complete);
    CHECK(completion.percent == doctest::Approx(100.0));
    progress.slainMonsters = 150;
    completion = mawMapCompletion(progress, false);
    CHECK_FALSE(completion.complete);
    CHECK(completion.percent == doctest::Approx(76.5));

    progress.mapFileName = "d42.blv";
    CHECK_FALSE(mawMapCompletion(progress, false).counts);

    // mdt15 has one monster that cannot be slain.
    progress.mapFileName = "mdt15.blv";
    progress.countedMonsters = 10;
    progress.slainMonsters = 9;
    CHECK(mawMapCompletion(progress, false).complete);

    // Nothing left but hidden hostiles: cleared; nothing at all: no share.
    progress.mapFileName = "d24.blv";
    progress.countedMonsters = 0;
    progress.slainMonsters = 0;
    progress.hiddenMonsters = 3;
    CHECK(mawMapCompletion(progress, false).complete);
    progress.hiddenMonsters = 0;
    CHECK_FALSE(mawMapCompletion(progress, false).counts);
}

TEST_CASE("MAW Antagarich monsters give twice the experience, at most 1000 more (A3.15)")
{
    MercenaryMap world;
    MawRules rules(RulesetOptions{}, world.mapLevels, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const MonsterTable::MonsterStatsEntry &stats = *world.monsters.findStatsById(195);
    world.map.mergedContinentId = 1;
    const uint32_t jadame = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts.experience;
    world.map.mergedContinentId = 2;
    const uint32_t antagarich = monsters.resolveMonster(world.context(), stats, nullptr).rulesetFacts.experience;
    REQUIRE(jadame > 0);
    CHECK(antagarich > jadame);
    CHECK(antagarich <= 2 * jadame + 1);
}

TEST_CASE("MAW respecs forget the four added skills, the taught skill's memory counts, repairs mend themselves (A5.1, A5.9, A5.2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const SkillRules &skills = rules.gameRules().skills;
    Character knight;
    knight.className = "Knight";
    knight.level = 30;
    knight.skills["Sword"] = {"Sword", 10, SkillMastery::Master};
    knight.skills["Cover"] = {"Cover", 10, SkillMastery::Master};
    REQUIRE(skills.resetSkills(knight));
    CHECK(knight.rulesetState.rememberedMasteries.contains("Sword"));
    CHECK_FALSE(knight.rulesetState.rememberedMasteries.contains("Cover"));

    // A remembered Master Sword makes its own Expert lesson dearer: twice the base price.
    const int fresh = skills.masteryTeacherCost(Character{}, "Sword", SkillMastery::Expert, 0);
    CHECK_EQ(skills.masteryTeacherCost(knight, "Sword", SkillMastery::Expert, 0), 2 * fresh);

    // The best Repair (s x m) of those who can act mends what it reaches on the 5-minute tick.
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    Character &smith = *party.member(0);
    smith.skills["RepairItem"] = {"RepairItem", 10, SkillMastery::Expert};
    const ItemDefinition *pSword = gameData.itemTable.get(1);
    REQUIRE(pSword != nullptr);
    REQUIRE(pSword->identifyRepairDifficulty <= 20);
    InventoryItem sword;
    sword.objectDescriptionId = 1;
    sword.broken = true;
    party.member(1)->inventory.push_back(sword);
    rules.gameRules().combat.updateCombat(party, world, 0.016f);
    world.advanceGameMinutes(5);
    rules.gameRules().combat.updateCombat(party, world, 0.016f);
    CHECK_FALSE(party.members()[1].inventory.back().broken);
}

TEST_CASE("MAW switching to horizontal progression takes masteries the levels do not reach; switching back returns them (L5.2, A5.3)")
{
    RulesetOptions options;
    MawRules rules(options, MawMapLevels{}, installedItemData());
    PartySeed seed;
    seed.members.resize(1);
    seed.members[0].className = "Knight";
    seed.members[0].level = 30;
    seed.members[0].skills["Sword"] = {"Sword", 4, SkillMastery::Master};
    seed.members[0].skills["Bodybuilding"] = {"Bodybuilding", 2, SkillMastery::Master};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    const SkillRules &skills = rules.gameRules().skills;
    skills.updateRegeneration(party, world, 0.1f);
    CHECK_EQ(party.members()[0].findSkill("Sword")->mastery, SkillMastery::Master);

    options.progression = RulesetProgression::Horizontal;
    rules.setOptions(options);
    skills.updateRegeneration(party, world, 0.1f);
    const SkillMastery stripped = party.members()[0].findSkill("Sword")->mastery;
    CHECK(stripped < SkillMastery::Master);
    CHECK_EQ(party.members()[0].rulesetState.progressionStoredMasteries.at("Sword"), SkillMastery::Master);
    // Skills past 0-23 keep theirs.
    CHECK_EQ(party.members()[0].findSkill("Bodybuilding")->mastery, SkillMastery::Master);

    options.progression = RulesetProgression::Free;
    rules.setOptions(options);
    skills.updateRegeneration(party, world, 0.1f);
    CHECK_EQ(party.members()[0].findSkill("Sword")->mastery, SkillMastery::Master);
    CHECK(party.members()[0].rulesetState.progressionStoredMasteries.empty());
}

TEST_CASE("MAW counts only the strongest follower's skill bonus (A5.4)")
{
    std::vector<HiredNpcFollower> followers(2);
    followers[0].professionId = 13;
    followers[1].professionId = 14;
    CHECK_EQ(hiredNpcSkillBonus(followers, "Learning"), 25);
    CHECK_EQ(hiredNpcSkillBonus(followers, "Learning", true), 15);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    CHECK_FALSE(rules.gameRules().skills.followerSkillBonusesStack());
    CHECK(standardGameRules().skills.followerSkillBonusesStack());
}

TEST_CASE("MAW skill limits and Learning: base 500, capped skills at twice the cap, no Learning experience (A5.5, A5.10)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const SkillRules &skills = rules.gameRules().skills;
    CHECK_EQ(skills.skillLevelCap("Sword").value_or(0), 500u);
    CHECK_EQ(skills.skillLevelCap("Alchemy").value_or(0), 60u);
    CHECK_FALSE(standardSkillRules().skillLevelCap("Sword").has_value());

    // Cover caps at 30: items take it no further than 60.
    Character member;
    member.skills["Cover"] = {"Cover", 30, SkillMastery::Master};
    member.itemSkillBonuses["Cover"] = 50;
    skills.applyStatBonuses(member);
    CHECK_EQ(30 + member.skillBonus("Cover"), 60);

    CHECK_FALSE(rules.gameRules().experience.learningGrantsExperience());
    CHECK(standardGameRules().experience.learningGrantsExperience());
}

TEST_CASE("MAW gives a lone character utility masteries by base level and gives the old ones back (L5.3)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    PartySeed seed;
    seed.members.resize(1);
    seed.members[0].className = "Knight";
    seed.members[0].skills["Merchant"] = {"Merchant", 8, SkillMastery::Normal};
    seed.members[0].skills["Perception"] = {"Perception", 2, SkillMastery::Grandmaster};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    const SkillRules &skills = rules.gameRules().skills;
    skills.updateRegeneration(party, world, 0.1f);
    // 8 reaches 1, 4 and 7: Master; 2 reaches only 1, so Perception falls to Normal.
    CHECK_EQ(party.members()[0].findSkill("Merchant")->mastery, SkillMastery::Master);
    CHECK_EQ(party.members()[0].findSkill("Perception")->mastery, SkillMastery::Normal);

    // A second member: the Merchant Normal it had comes back.
    PartySeed two = seed;
    two.members.resize(2);
    two.members[0] = party.members()[0];
    Party grown;
    grown.seed(two);
    grown.setRules(&rules.gameRules());
    skills.updateRegeneration(grown, world, 0.1f);
    CHECK_EQ(grown.members()[0].findSkill("Merchant")->mastery, SkillMastery::Normal);
    CHECK(grown.members()[0].rulesetState.soloStoredMasteries.empty());
}

TEST_CASE("MAW skill tooltips show live numbers: Mace paralysis, Retaliation, the switches, Supreme (L5.4, A5.7)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    std::string error;
    MawTextData texts;
    REQUIRE_MESSAGE(texts.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/texts.yml"), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData(), MawPromotionData{}, MawCraftingData{}, texts);
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    Character &knight = *party.member(0);
    knight.className = "Knight";
    knight.skills["Mace"] = {"Mace", 20, SkillMastery::Master};
    knight.equipment.mainHand = 66;
    knight.skills["Cover"] = {"Cover", 10, SkillMastery::Expert};
    knight.rulesetState.coverDisabled = true;
    knight.skills["Retaliation"] = {"Retaliation", 10, SkillMastery::Normal};
    const SkillRules &skills = rules.gameRules().skills;
    REQUIRE(gameData.itemTable.get(66) != nullptr);
    REQUIRE_EQ(canonicalSkillName(gameData.itemTable.get(66)->skillGroup), "Mace");
    CHECK(skills.skillTooltip(party, knight, "Mace", {}).description.find("Chance to paralyse vs level")
        != std::string::npos);
    CHECK(skills.skillTooltip(party, knight, "Cover", {}).description.find("Currently disabled") != std::string::npos);
    CHECK(skills.skillTooltip(party, knight, "Retaliation", {}).description.find("Melee Power") != std::string::npos);
    CHECK(skills.skillTooltip(party, knight, "Armsmaster", {}).description.find("30") != std::string::npos);
}

TEST_CASE("A dragon's Regeneration popup shows its bite leech (L5.4)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawTextData texts;
    std::string error;
    REQUIRE_MESSAGE(texts.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/texts.yml"), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData(), MawPromotionData{}, MawCraftingData{}, texts);
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    Character &member = *party.member(0);
    member.skills["Regeneration"] = {"Regeneration", 10, SkillMastery::Expert};
    const SkillRules &skills = rules.gameRules().skills;

    member.raceId = 0;
    CHECK(skills.skillTooltip(party, member, "Regeneration", {}).description.find("leech") == std::string::npos);
    member.raceId = 5;
    const std::string text = skills.skillTooltip(party, member, "Regeneration", {}).description;
    CHECK(text.find("Melee life leech vs equal level") != std::string::npos);
    CHECK(text.find("{dragon_leech}") == std::string::npos);

    // Before the dragon learns it (character creation): the leech still shows, and one more point means learning it.
    member.skills.erase("Regeneration");
    const std::string unlearned = skills.skillTooltip(party, member, "Regeneration", {}).description;
    CHECK(unlearned.find("Melee life leech vs equal level") != std::string::npos);
    // "(\f02016<value>\f00000 with one more point": the value between the colour codes is not 0.
    const size_t next = unlearned.find("\f00000 with one more point");
    REQUIRE(next != std::string::npos);
    const size_t value = unlearned.rfind("(\f02016", next);
    REQUIRE(value != std::string::npos);
    CHECK(std::stod(unlearned.substr(value + 7, next - value - 7)) > 0);
}

TEST_CASE("Dragon Ability and an Elementalist's schools have MAW's own popups")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawTextData texts;
    std::string error;
    REQUIRE_MESSAGE(texts.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/texts.yml"), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData(), MawPromotionData{}, MawCraftingData{}, texts);
    rules.setSpellTable(&gameData.spellTable);
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    Character &member = *party.member(0);
    const SkillRules &skills = rules.gameRules().skills;

    member.className = "Dragon";
    member.raceId = 5;
    member.skills["DragonAbility"] = {"DragonAbility", 5, SkillMastery::Expert};
    const std::string dragon = skills.skillTooltip(party, member, "DragonAbility", {}).description;
    CHECK(dragon.find("Breath damage is 20 + 2 per level (up to level 600)") != std::string::npos);
    CHECK(dragon.find('{') == std::string::npos);

    // A new Elementalist knows the first two tiers; the third (Fire Resistance, Air Resistance) comes next.
    member.className = "Elementalist";
    member.raceId = 0;
    member.skills["FireMagic"] = {"FireMagic", 5, SkillMastery::Normal};
    member.skills["AirMagic"] = {"AirMagic", 5, SkillMastery::Normal};
    member.rulesetState.elementalProgress = {250, 0, 0, 320000};
    const std::string fire = skills.skillTooltip(party, member, "FireMagic", {}).description;
    CHECK(fire.find("Progress toward learning Fire Resistance: ") != std::string::npos);
    CHECK(fire.find("50 %") != std::string::npos);
    CHECK(skills.skillTooltip(party, member, "AirMagic", {}).description.find("learning Air Resistance")
        != std::string::npos);
    member.skills["EarthMagic"] = {"EarthMagic", 5, SkillMastery::Normal};
    CHECK(skills.skillTooltip(party, member, "EarthMagic", {}).description.find("taught every spell")
        != std::string::npos);
}

TEST_CASE("The armour skills' popups show the worn armour's numbers (L5.4)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawTextData texts;
    std::string error;
    REQUIRE_MESSAGE(texts.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/texts.yml"), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData(), MawPromotionData{}, MawCraftingData{}, texts);
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    REQUIRE(party.itemTable() != nullptr);
    Character &member = *party.member(0);
    member.equipment = {};
    member.skills["LeatherArmor"] = {"LeatherArmor", 10, SkillMastery::Expert};
    member.skills["ChainArmor"] = {"ChainArmor", 10, SkillMastery::Expert};
    const SkillRules &skills = rules.gameRules().skills;
    CHECK(skills.skillTooltip(party, member, "LeatherArmor", {}).description.find("from items") == std::string::npos);

    // A leather armour (item 84) is read by Leather Armor's popup, not Chain's; 10 Expert points add 40 %.
    REQUIRE(party.itemTable()->get(84) != nullptr);
    REQUIRE_EQ(canonicalSkillName(party.itemTable()->get(84)->skillGroup), "LeatherArmor");
    member.equipment.armor = 84;
    const MawArmorBreakdown armor = mawArmorBreakdown(rules, member, *party.itemTable());
    CHECK_GT(armor.pieces, 0);
    CHECK_EQ(armor.bodySkillArmor, int(mawRound(armor.pieces * 0.4)));
    const std::string leather = skills.skillTooltip(party, member, "LeatherArmor", {}).description;
    CHECK(leather.find("Current Armor Class from items") != std::string::npos);
    CHECK(leather.find("{armor_items}") == std::string::npos);
    CHECK(skills.skillTooltip(party, member, "ChainArmor", {}).description.find("from items") == std::string::npos);
}

TEST_CASE("A ruleset game's save requires the ruleset package at its content schema (E.3)")
{
    GameSaveData save;
    save.ruleset.id = "maw";
    const ItemTable items;
    const HouseTable houses;
    std::unordered_map<std::string, uint32_t> loaded = {{"engine", 1}, {"rulesets/maw", 1}};
    save.requiredContentPackages = collectRequiredContentPackages(save, items, houses, loaded);
    REQUIRE(save.requiredContentPackages.contains("rulesets/maw"));
    std::string error;
    CHECK(validateRequiredContentPackages(save, items, houses, loaded, error));

    // Another schema, or no MAW package at all, refuses the save.
    loaded["rulesets/maw"] = 2;
    CHECK_FALSE(validateRequiredContentPackages(save, items, houses, loaded, error));
    loaded.erase("rulesets/maw");
    CHECK_FALSE(validateRequiredContentPackages(save, items, houses, loaded, error));
    CHECK(error.find("rulesets/maw") != std::string::npos);

    // A Standard game asks for nothing of the kind.
    GameSaveData standard;
    CHECK(collectRequiredContentPackages(standard, items, houses, loaded).empty());
}

TEST_CASE("MAW's id ranges are declared and clash with no mounted world (E.3)")
{
    std::string error;
    const std::optional<RulesetDefinition> maw =
        parseRulesetDefinition(readSource("assets_dev/engine/rulesets/maw/ruleset.yml"), "maw", error);
    REQUIRE_MESSAGE(maw.has_value(), error);
    REQUIRE_EQ(maw->idRanges.size(), 4);

    for (const char *pWorld : {"mm6", "mm7", "mm8", "mm9"})
    {
        const std::filesystem::path path =
            std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds" / pWorld / "world.yml";
        std::vector<ContentIdRangeDefinition> worldRanges;
        REQUIRE_MESSAGE(
            parseContentIdRanges(YAML::LoadFile(path.string())["idRanges"], "world.yml", worldRanges, error), error);
        CHECK_MESSAGE(!overlappingContentIdRange(maw->idRanges, worldRanges).has_value(), pWorld);
    }

    // A world claiming MAW's quest bits is refused by domain; the same numbers in another domain are not.
    const std::vector<ContentIdRangeDefinition> clashing = {{"qbits", 10050, 10200}};
    CHECK_EQ(overlappingContentIdRange(maw->idRanges, clashing).value_or(""), "qbits");
    const std::vector<ContentIdRangeDefinition> otherDomain = {{"items", 10001, 10099}};
    CHECK_FALSE(overlappingContentIdRange(maw->idRanges, otherDomain).has_value());
}

TEST_CASE("Road to Insanity: no refills, revived monsters drop nothing, dungeons cap the food (P9.I1, I2, I6)")
{
    MercenaryMap mapWorld;
    RulesetOptions insanity;
    insanity.challengeMode = RulesetChallengeMode::RoadToInsanity;
    insanity.difficulty = RulesetDifficulty::Nightmare;
    MawRules rules(insanity, mapWorld.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    MawRules plain(RulesetOptions{}, mapWorld.mapLevels, installedItemData(), MawPromotionData{}, installedCraftingData());
    const MonsterRules &monsters = rules.gameRules().monsters;

    MapStatsEntry refilling = mapWorld.map;
    refilling.id = 20;
    refilling.respawnIntervalDays = 30;
    CHECK_EQ(plain.gameRules().monsters.mapRespawnDays(refilling), 30);
    CHECK_EQ(monsters.mapRespawnDays(refilling), 0);

    // A resurrected monster's corpse: no gold, no item.
    const MonsterTable::MonsterStatsEntry &stats = *mapWorld.monsters.findStatsById(195);
    ActorRulesetFacts facts = monsters.resolveMonster(mapWorld.context(), stats, nullptr).rulesetFacts;
    facts.risen = true;
    CorpseLootContext context;
    context.pStats = &stats;
    context.pMonsterTable = &mapWorld.monsters;
    context.pFacts = &facts;
    context.pMap = &mapWorld.map;
    const CorpseLoot risen = monsters.corpseLoot(context);
    CHECK_EQ(risen.loot.itemChance, 0);
    CHECK_EQ(risen.loot.goldDiceRolls, 0);
    CHECK_GT(plain.gameRules().monsters.corpseLoot(context).loot.itemChance, 0);

    // Entering a dungeon with 50 monsters caps the food at 15 + 49 / 25 = 16; the next outdoor map returns the rest.
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(OpenYAMM::Tests::regressionGameData());
    party.setRules(&rules.gameRules());
    party.addFood(40 - party.food());
    BossTestWorld world;
    world.bindParty(&party);
    world.setIndoorMap(true);

    for (uint32_t index = 0; index < 50; ++index)
    {
        world.addActor(bossActor(index + 1, 193, MawBossAffix::None, 100));
    }

    rules.setCurrentMap("d01.blv");
    monsters.updateMonsters(world, 0.016f);
    CHECK_EQ(party.food(), 16);
    CHECK_EQ(rules.state().heldFood, 24);
    monsters.updateMonsters(world, 0.016f);
    CHECK_EQ(party.food(), 16);

    world.setIndoorMap(false);
    rules.setCurrentMap("out01.odm");
    monsters.updateMonsters(world, 0.016f);
    CHECK_EQ(party.food(), 40);
    CHECK_EQ(rules.state().heldFood, 0);
}

TEST_CASE("Beyond Madness: special bosses carry bad-luck protection, none in the Arena (P9.M4)")
{
    RulesetOptions madness;
    madness.challengeMode = RulesetChallengeMode::BeyondMadness;
    madness.difficulty = RulesetDifficulty::Nightmare;
    madness.progression = RulesetProgression::Horizontal;
    MawRules rules(madness, MawMapLevels{}, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const auto roll = [&](uint64_t seed)
    {
        ActorRulesetFacts facts;
        facts.level = 80;
        facts.familyLevel = 60;
        REQUIRE(monsters.makeBoss(facts, seed, 0));
        return facts;
    };

    rules.setCurrentMap("out05.odm");
    int broodlords = 0;

    for (uint64_t seed = 1; seed <= 400; ++seed)
    {
        const ActorRulesetFacts facts = roll(seed * 7919);

        if (facts.bossAffix == uint8_t(MawBossAffix::Broodlord))
        {
            ++broodlords;
            CHECK_EQ(rules.state().broodlordPity, 0.0);
        }
    }

    // 3 % with protection: at least a few in 400 bosses.
    CHECK_GE(broodlords, 6);

    rules.setCurrentMap("d42.blv");
    const double pity = rules.state().broodlordPity;

    for (uint64_t seed = 1; seed <= 400; ++seed)
    {
        const uint8_t affix = roll(seed * 104729).bossAffix;
        CHECK((affix != uint8_t(MawBossAffix::Broodlord) && affix != uint8_t(MawBossAffix::Omnipotent)));
    }

    CHECK_EQ(rules.state().broodlordPity, pity);
}

TEST_CASE("Beyond Madness: no experience or loot in the arenas, 7d05 and bounty maps (P9.M5)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    RulesetOptions madness;
    madness.challengeMode = RulesetChallengeMode::BeyondMadness;
    madness.difficulty = RulesetDifficulty::Nightmare;
    madness.progression = RulesetProgression::Horizontal;
    MawRules rules(madness, MawMapLevels{}, installedItemData());
    RulesetOptions insanity = madness;
    insanity.challengeMode = RulesetChallengeMode::RoadToInsanity;
    MawRules insane(insanity, MawMapLevels{}, installedItemData());

    for (const char *pMap : {"zarena.blv", "D42.blv", "7d05.blv"})
    {
        CHECK(rules.madnessRewardlessMap(pMap));
        CHECK_FALSE(insane.madnessRewardlessMap(pMap));
    }

    rules.setCurrentMap("out05.odm");
    CHECK_FALSE(rules.madnessRewardlessMap("out05.odm"));
    rules.setBountyLevel(10);
    CHECK(rules.madnessRewardlessMap("out05.odm"));
    CHECK_FALSE(rules.madnessRewardlessMap("out06.odm"));
    rules.setBountyLevel(std::nullopt);

    Party party = OpenYAMM::Tests::makeSpellRegressionParty(OpenYAMM::Tests::regressionGameData());
    party.setRules(&rules.gameRules());
    MonsterKillReward kill;
    kill.facts.level = 50;
    kill.facts.experience = 5000;
    kill.maxHp = 20000;
    CHECK_GT(rules.gameRules().experience.grantKillExperience(party, kill), 0u);
    rules.setCurrentMap("d42.blv");
    CHECK_EQ(rules.gameRules().experience.grantKillExperience(party, kill), 0u);
}

TEST_CASE("MAW's used stat barrels stay empty through refills (L8.1, zzMaw-Maps.lua:240-283)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    PartySeed seed;
    seed.members.resize(1);
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    EventRuntimeState state;
    state.mapFileName = "D05.blv";
    state.decorVars[3] = 0;
    state.decorVars[4] = 0;

    // A barrel that raised a stat is remembered with the state its event left it in; one that raised nothing is not.
    const std::vector<int64_t> before = partyBaseStatSnapshot(party);
    reportDecorationStatGain(party, state, 4, before);
    party.member(0)->might += 2;
    reportDecorationStatGain(party, state, 3, before);
    CHECK(rules.state().usedStatDecorations == std::unordered_map<std::string, std::unordered_map<uint8_t, uint8_t>>{
        {"d05.blv", {{3, 0}}}});

    // A refill rolls the barrels again; the first update after the load empties the used one.
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindEventRuntimeState(&state);
    state.decorVars[3] = 5;
    state.decorVars[4] = 6;
    monsters.mapLoaded("d05.blv", true);
    monsters.updateMonsters(world, 0.016f);
    CHECK_EQ(state.decorVars[3], 0);
    CHECK_EQ(state.decorVars[4], 6);

    // Standard keeps no barrels.
    standardGameRules().monsters.decorationRaisedStats("d05.blv", 4, 0);
    CHECK_EQ(rules.state().usedStatDecorations.size(), 1);

    // A save from before MMerge's campfire list renumbers the map's decorations; the used barrel moves with them.
    const std::vector<int16_t> remap = {0, 1, -1, 4};
    monsters.decorationsRenumbered("D05.blv", remap);
    CHECK(rules.state().usedStatDecorations == std::unordered_map<std::string, std::unordered_map<uint8_t, uint8_t>>{
        {"d05.blv", {{4, 0}}}});
}

TEST_CASE("MAW readiness fixes: utility auras need their full cost free, falls skip Mist Form, two weapons average "
          "unrounded")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());

    // Torch Light costs 5; Grandmaster Enlightenment would reserve 3, but the cast needs all 5 free (SP:2779-2794).
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    Character &caster = *party.member(3);
    caster.skills["Enlightenment"] = {"Enlightenment", 10, SkillMastery::Grandmaster};
    const int bonus = Party::effectiveMaximumSpellPoints(caster) - caster.maxSpellPoints;
    caster.maxSpellPoints = 4 - bonus;
    caster.spellPoints = Party::effectiveMaximumSpellPoints(caster);
    REQUIRE_EQ(Party::effectiveMaximumSpellPoints(caster), 4);
    REQUIRE_EQ(mawUtilityAuraReservation(5, 4), 3);
    CHECK(rules.gameRules().spells.castAura(party, 3, 1) == AuraCastResult::NotEnoughMana);
    caster.maxSpellPoints = 5 - bonus;
    CHECK(rules.gameRules().spells.castAura(party, 3, 1) == AuraCastResult::Held);

    // A fall outdoors is no monster's hit: Mist Form leaves it alone (DM:1622-1692).
    Character faller;
    faller.level = 20;
    faller.maxHealth = 500;
    faller.health = 500;
    std::mt19937 rng(5);
    const auto fall = [&]()
    {
        CharacterDamageHit hit;
        hit.amount = 100;
        hit.type = CombatDamageType::Physical;
        hit.pCharacter = &faller;
        hit.pRng = &rng;
        return rules.gameRules().combat.damageToCharacter(hit);
    };
    const int plain = fall();
    faller.mistFormPhysicalShare = 0.25f;
    CHECK_EQ(fall(), plain);

    // Two weapons average their recoveries without rounding; only the delay is rounded (S:514-524).
    MawAttackDelayInputs inputs;
    inputs.baseRecovery = 85;
    inputs.bonusPercent = 0;
    CHECK_EQ(mawAttackDelay(inputs).delay, 85);
    inputs.baseRecovery = 84.5;
    inputs.bonusPercent = 30;
    CHECK_EQ(mawAttackDelay(inputs).delay, int(mawRound(84.5 / 1.3)));
}

TEST_CASE("Only MAW outlines items in their rarity colour; Standard MMerge has no rarity glow")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_FALSE(standardGameRules().items.glowsItemRarity());
    CHECK(rules.gameRules().items.glowsItemRarity());
}

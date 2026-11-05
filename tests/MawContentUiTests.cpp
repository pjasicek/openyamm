#include "doctest/doctest.h"
#include "game/app/KeyboardBindings.h"
#include "game/gameplay/GameplayWorldItemPolicy.h"
#include "game/items/InventoryBags.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/rules/ClassRules.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/PotionRules.h"
#include "game/rules/SkillRules.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawCraftingData.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawExperienceRules.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/rules/maw/MawMonsterInspect.h"
#include "game/rules/maw/MawPotionRules.h"
#include "game/rules/maw/MawTexts.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/PotionEffectTable.h"
#include "game/tables/SpellTable.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <random>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

// Session C's MAW rows (devdocs/maw/GAPS.md §7-§9): alchemy, the multibag and the monster inspect panel.
namespace
{
Party mawParty(const MawRules &rules, size_t memberCount)
{
    Character member = {};
    member.name = "Member";
    member.level = 50;
    member.maxHealth = 100000;
    member.health = 100000;
    member.birthYear = CharacterAgeReferenceYear - 30;
    PartySeed seed = {};
    seed.members.assign(memberCount, member);
    Party party = {};
    party.seed(seed);
    party.setRules(&rules.gameRules());
    return party;
}

InventoryItem packItem(uint32_t itemId, uint8_t width, uint8_t height)
{
    InventoryItem item;
    item.objectDescriptionId = itemId;
    item.width = width;
    item.height = height;
    return item;
}

std::optional<GameSaveData> roundTrip(const GameSaveData &save, std::string &error)
{
    const uint64_t ticks = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / ("openyamm_maw_bags_" + std::to_string(ticks) + ".oysav");
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);
    std::optional<GameSaveData> restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    return restored;
}
}

TEST_CASE("MAW reagent power past 255 adds half the excess, at most 900 (A4.5)")
{
    CHECK_EQ(mawCappedReagentPower(200), 200);
    CHECK_EQ(mawCappedReagentPower(255), 255);
    CHECK_EQ(mawCappedReagentPower(300), 255 + 22);
    CHECK_EQ(mawCappedReagentPower(5000), 255 + 900);
}

TEST_CASE("MAW mixes with the Alchemy skill and its item bonus, at most twice the cap (A4.6)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character alchemist;
    alchemist.skills["Alchemy"] = {"Alchemy", 40, SkillMastery::Grandmaster};
    alchemist.itemSkillBonuses["Alchemy"] = 30;
    // Standard mixes with the effective level too; MAW counts the item bonus once, then caps it.
    CHECK_EQ(standardPotionRules().mixingAlchemyLevel(alchemist), 70u);
    CHECK_EQ(rules.gameRules().potions.mixingAlchemyLevel(alchemist), 70u);
    alchemist.itemSkillBonuses["Alchemy"] = 500;
    CHECK_EQ(rules.gameRules().potions.mixingAlchemyLevel(alchemist), 120u);
}

TEST_CASE("MAW catalyst mixes add the powers up to Alchemy x mastery / 2 (A4.8)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const PotionRules &maw = rules.gameRules().potions;

    // round(max(T + M / 2, T / 2 + M)) = 130, inside 100 x 4 / 2.
    CHECK_EQ(maw.catalystMixPower(100, 60, false, SkillMastery::Grandmaster, 100), 130);
    // A weak alchemist's limit (20 x 4 / 2 = 40) never takes the potion below either input.
    CHECK_EQ(maw.catalystMixPower(100, 60, false, SkillMastery::Grandmaster, 20), 100);
    CHECK_EQ(maw.catalystMixPower(30, 50, true, SkillMastery::Expert, 30), 50);
    CHECK_EQ(maw.catalystMixPower(30, 50, true, SkillMastery::Expert, 100), 65);

    // Standard: the held item's power, the stronger one for two catalysts.
    CHECK_EQ(standardPotionRules().catalystMixPower(100, 60, false, SkillMastery::Grandmaster, 100), 60);
    CHECK_EQ(standardPotionRules().catalystMixPower(100, 60, true, SkillMastery::Grandmaster, 100), 100);
}

TEST_CASE("MAW drinks need a ready member even away from monsters (A4.7)")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    std::ifstream input(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/content/potion_effects.yml");
    std::ostringstream text;
    text << input.rdbuf();
    PotionEffectTable effects;
    std::string error;
    REQUIRE_MESSAGE(effects.loadFromYaml(text.str(), error), error);
    MergedPotionSettingTable potions = OpenYAMM::Tests::regressionGameData().mergedPotionSettingTable;
    potions.setEffects(effects);
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(rules, 2);
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const auto drink =
        [&](bool enemiesNear)
        {
            InventoryItem potion;
            potion.objectDescriptionId = 227;
            potion.standardEnchantPower = 10;
            InventoryItemUseContext context;
            context.enemiesNear = enemiesNear;
            return InventoryItemUseRuntime::useItemOnMember(
                party, 0, potion, gameData.itemTable, &gameData.readableScrollTable, &potions, nullptr, context);
        };

    // Away from monsters a drink costs nobody recovery.
    CHECK(drink(false).consumed);
    CHECK_EQ(party.members()[0].recoverySecondsRemaining, 0.0f);

    // With every member recovering, no drink, monsters or not.
    party.applyRecoveryToMember(0, 5.0f);
    party.applyRecoveryToMember(1, 5.0f);
    const InventoryItemUseResult refused = drink(false);
    CHECK_FALSE(refused.consumed);
    CHECK_EQ(refused.statusText, "Player must be active to consume the potion");
}

TEST_CASE("multibag: MAW gives four bags, five tabs of four to a party of one; opening a bag swaps the pack (H.1)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_EQ(standardItemRules().bagCount(mawParty(rules, 4)), 1);
    CHECK_EQ(rules.gameRules().items.bagCount(mawParty(rules, 4)), 4);
    CHECK_EQ(rules.gameRules().items.bagCount(mawParty(rules, 1)), 20);
    CHECK_EQ(InventoryBags::tabCount(20), 5);
    CHECK_EQ(InventoryBags::tabCount(4), 1);

    Character character;
    REQUIRE(character.addInventoryItem(packItem(100, 1, 3)));
    CHECK_FALSE(InventoryBags::openBag(character, 0, 4));
    CHECK_FALSE(InventoryBags::openBag(character, 4, 4));

    REQUIRE(InventoryBags::openBag(character, 2, 4));
    CHECK(character.inventory.empty());
    CHECK_EQ(character.rulesetState.currentBag, 2);
    CHECK_EQ(InventoryBags::storedItemCount(character), 1u);
    REQUIRE(character.addInventoryItem(packItem(200, 2, 2)));

    REQUIRE(InventoryBags::openBag(character, 0, 4));
    REQUIRE_EQ(character.inventory.size(), 1u);
    CHECK_EQ(character.inventory[0].objectDescriptionId, 100u);
    CHECK_EQ(character.rulesetState.storedBags.at(2)[0].objectDescriptionId, 200u);
    CHECK_FALSE(character.rulesetState.storedBags.contains(0));
}

TEST_CASE("multibag: an item the party gets goes into any bag with room before the next member (user, 2026-10-25)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(rules, 2);
    REQUIRE(party.member(0)->addInventoryItem(packItem(100, Character::InventoryWidth, Character::InventoryHeight)));
    REQUIRE(party.member(1)->addInventoryItem(packItem(101, 1, 1)));

    size_t recipient = 9;
    REQUIRE(party.tryGrantInventoryItem(packItem(200, 2, 4), &recipient));
    CHECK_EQ(recipient, 0u);
    CHECK_EQ(party.member(0)->rulesetState.currentBag, 0);
    REQUIRE(party.member(0)->rulesetState.storedBags.contains(1));
    CHECK_EQ(party.member(0)->rulesetState.storedBags.at(1).front().objectDescriptionId, 200u);

    // With one bag (Standard), a full member's item goes to the next member.
    Party standard = mawParty(rules, 2);
    standard.setRules(nullptr);
    REQUIRE(standard.member(0)->addInventoryItem(packItem(100, Character::InventoryWidth, Character::InventoryHeight)));
    REQUIRE(standard.tryGrantInventoryItem(packItem(200, 2, 4), &recipient));
    CHECK_EQ(recipient, 1u);
}

TEST_CASE("multibag: an item put on a member's portrait goes into their next bag with room (user, 2026-10-29)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(rules, 2);
    REQUIRE(party.member(1)->addInventoryItem(packItem(100, Character::InventoryWidth, Character::InventoryHeight)));

    REQUIRE(party.tryAutoPlaceItemInMemberInventory(1, packItem(200, 2, 4)));
    CHECK_EQ(party.member(1)->rulesetState.currentBag, 0);
    REQUIRE(party.member(1)->rulesetState.storedBags.contains(1));
    CHECK_EQ(party.member(1)->rulesetState.storedBags.at(1).front().objectDescriptionId, 200u);
    CHECK(party.member(0)->inventory.empty());
}

TEST_CASE("multibag: event item checks see every bag (user, 2026-10-26: Markham's Contestant's Shield)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(rules, 4);
    Character &holder = *party.member(2);
    REQUIRE(InventoryBags::openBag(holder, 2, 4));
    REQUIRE(holder.addInventoryItem(packItem(1460, 2, 2)));
    REQUIRE(holder.addInventoryItem(packItem(1437, 1, 1)));
    REQUIRE(InventoryBags::openBag(holder, 0, 4));
    REQUIRE(holder.inventory.empty());

    CHECK_EQ(party.inventoryItemCount(1460), 1);
    CHECK_EQ(party.inventoryItemCount(1460, 2), 1);
    CHECK_EQ(party.inventoryItemCount(1460, 0), 0);
    CHECK(party.hasItemAnywhere(1460));

    REQUIRE(party.removeItem(1460));
    REQUIRE(party.removeItemFromMember(2, 1437));
    CHECK_EQ(party.inventoryItemCount(1460), 0);
    CHECK_EQ(party.inventoryItemCount(1437), 0);
    CHECK_EQ(holder.rulesetState.currentBag, 0);
    CHECK_FALSE(party.removeItem(1460));
}

TEST_CASE("multibag: sorting all bags puts the tallest first and fills the bags in order (H.1)")
{
    Character character;
    REQUIRE(character.addInventoryItem(packItem(10, 1, 1)));
    REQUIRE(InventoryBags::openBag(character, 3, 5));
    REQUIRE(character.addInventoryItem(packItem(20, 2, 4)));
    REQUIRE(character.addInventoryItem(packItem(30, 2, 1)));

    REQUIRE(InventoryBags::sortAllBags(character, 5, nullptr));
    CHECK_EQ(character.rulesetState.currentBag, 3);
    CHECK(character.inventory.empty());
    REQUIRE(character.rulesetState.storedBags.contains(0));
    const std::vector<InventoryItem> &first = character.rulesetState.storedBags.at(0);
    REQUIRE_EQ(first.size(), 3u);
    // Height 4, then the wide one-cell item (MAW's 1.5), then the small one, column by column.
    CHECK_EQ(first[0].objectDescriptionId, 20u);
    CHECK_EQ(first[0].gridX, 0);
    CHECK_EQ(first[0].gridY, 0);
    CHECK_EQ(first[1].objectDescriptionId, 30u);
    CHECK_EQ(first[1].gridY, 4);
    CHECK_EQ(first[2].objectDescriptionId, 10u);

    // A full bag overflows into the next one.
    Character full;

    for (int index = 0; index < 63; ++index)
    {
        REQUIRE(full.addInventoryItem(packItem(40, 2, 1)));
    }

    REQUIRE(InventoryBags::openBag(full, 1, 5));
    REQUIRE(full.addInventoryItem(packItem(50, 2, 1)));
    REQUIRE(InventoryBags::sortAllBags(full, 5, nullptr));
    CHECK_EQ(full.inventory.size(), 1u);
    CHECK_EQ(full.rulesetState.storedBags.at(0).size(), 63u);
    CHECK_EQ(full.inventory[0].objectDescriptionId, 50u);
    CHECK_EQ(InventoryBags::storedItemCount(full), 63u);

    // Too many items for the bags: nothing changes.
    REQUIRE_FALSE(InventoryBags::sortAllBags(full, 1, nullptr));
    CHECK_EQ(full.inventory.size(), 1u);
}

TEST_CASE("multibag bags survive a save; a Standard character saves none (H.1)")
{
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.saveName = "bags";
    Character standard;
    standard.name = "Standard";
    REQUIRE(standard.addInventoryItem(packItem(100, 1, 1)));
    Character maw;
    maw.name = "Maw";
    REQUIRE(maw.addInventoryItem(packItem(100, 1, 1)));
    REQUIRE(InventoryBags::openBag(maw, 4, 5));
    REQUIRE(maw.addInventoryItem(packItem(200, 2, 3)));
    save.party.members = {standard, maw};

    std::string error;
    const std::optional<GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    REQUIRE_EQ(restored->party.members.size(), 2u);
    CHECK(restored->party.members[0].rulesetState.empty());
    CHECK(restored->party.members[0].rulesetState.storedBags.empty());
    CHECK(restored->party.members[1].rulesetState == maw.rulesetState);
    CHECK_EQ(restored->party.members[1].rulesetState.currentBag, 4);
    CHECK(restored->party.members[1].inventory == maw.inventory);
}

TEST_CASE("MAW's short numbers: whole below 1000, three digits with a coloured suffix above")
{
    CHECK_EQ(mawShortNumber(999), "999");
    CHECK_EQ(mawShortNumber(1234), "\f655161.23K\f00000");
    CHECK_EQ(mawShortNumber(56789), "\f6551656.8K\f00000");
    CHECK_EQ(mawShortNumber(999999), "\f648001M\f00000");
    CHECK_EQ(mawShortNumber(2500000000.0), "\f634882.5B\f00000");
}

TEST_CASE("MAW's inspect panel: level, 95 % damage ranges after the viewer's defences, experience (H.2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(rules, 1);
    MonsterTable::MonsterStatsEntry stats;
    stats.attack1Type = "Phys";
    stats.attack2Type = "Fire";
    stats.specialAttackKind = MonsterSpecialAttackKind::PoisonMedium;
    ActorRulesetFacts facts;
    facts.level = 40;
    facts.familyLevel = 40;
    facts.tier = 2;
    facts.attack1Damage = 100;
    facts.attack2Damage = 50;
    facts.experience = 1000;
    facts.spearDamageTaken = 12.4f;
    MonsterInspectQuery query;
    query.pStats = &stats;
    query.pFacts = &facts;
    query.pParty = &party;
    query.hasAttack2 = true;
    query.spellId = 6;
    query.spellDamageType = CombatDamageType::Fire;
    query.maxHp = 5000;
    query.rawNumbers = true;

    // Raw: mean 100 +- 1.96 x 100 x 0.5 / sqrt(24) = 80-120; attack 2 at 40-60; Fireball x its multiplier.
    const MonsterInspectNumbers raw = mawMonsterInspectNumbers(rules, query);
    CHECK_EQ(raw.level, 40);
    REQUIRE_EQ(raw.damageRows.size(), 2u);
    CHECK_EQ(raw.damageRows[0], "80-120");
    CHECK_EQ(raw.damageRows[1], "40-60");
    // A spell deals the monster's damage for its element, not attack 1's (MAW 249b00da).
    const double fireball =
        mawMonsterBaseDamage(rules, facts, 1, CombatDamageType::Fire) * mawMonsterSpellMultiplier(6);
    const double halfWidth = std::sqrt(std::pow(fireball * 0.5, 2) / 24) * 1.96;
    CHECK_EQ(raw.spellDamage, std::to_string(int(mawRound(fireball - halfWidth))) + "-"
            + std::to_string(int(mawRound(fireball + halfWidth))));

    // Special attack, the viewer's share of the kill (one member: all of it, by HP over a member-level monster's),
    // and the spear stack.
    const MawMemberKillExperience share = mawMemberKillExperience(rules, party.members()[0], 1, 1000, 5000);
    REQUIRE_GE(raw.effectLines.size(), 3u);
    CHECK_EQ(raw.effectLines[0], "Special: Poison 2");
    CHECK_EQ(raw.effectLines[1], "Experience: " + std::to_string(int64_t(mawRound(share.award))));
    CHECK_EQ(raw.effectLines[2], "Physical damage taken: +12%");

    // After the viewer's defences: never more than raw.
    query.rawNumbers = false;
    const MonsterInspectNumbers mitigated = mawMonsterInspectNumbers(rules, query);
    REQUIRE_EQ(mitigated.damageRows.size(), 2u);
    CHECK_LE(std::stoi(mitigated.damageRows[0].substr(mitigated.damageRows[0].find('-') + 1)), 120);

    // Standard leaves the panel to the monster table.
    CHECK_FALSE(standardGameRules().monsters.inspectNumbers(query).has_value());
}

TEST_CASE("MAW monsters without a corpse drop their crafting rolls; water monsters' go to the party (A4.4)")
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/crafting.yml");
    std::ostringstream text;
    text << input.rdbuf();
    MawCraftingData crafting;
    std::string error;
    REQUIRE_MESSAGE(crafting.loadFromYaml(text.str(), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, std::move(crafting));
    const MonsterRules &monsters = rules.gameRules().monsters;
    const auto monsterRow =
        [](int id, const std::string &picture)
        {
            std::vector<std::string> row(38);
            row[0] = std::to_string(id);
            row[1] = picture;
            row[2] = picture;
            row[3] = "60";
            row[4] = "100";
            row[10] = "Short";
            row[11] = "Normal";
            row[17] = "Phys";
            row[18] = "1d6";
            return row;
        };
    MonsterTable monsterTable;
    REQUIRE(monsterTable.loadStatsFromRows({monsterRow(243, "Air Elemental C"), monsterRow(627, "Sea Serpent C")}));
    MapStatsEntry map = {};
    map.fileName = "out01.odm";
    ActorRulesetFacts facts;
    facts.level = 300;
    facts.tier = 3;
    CorpseLootContext context;
    context.pMonsterTable = &monsterTable;
    context.pFacts = &facts;
    context.pMap = &map;

    // A Sea Serpent C sinks: its drops go to the party; an Air Elemental's land on the ground.
    context.pStats = monsterTable.findStatsById(627);
    REQUIRE(context.pStats != nullptr);
    CHECK(monsters.lootWithoutCorpse(context).toParty);
    context.pStats = monsterTable.findStatsById(243);
    REQUIRE(context.pStats != nullptr);
    CHECK_FALSE(monsters.lootWithoutCorpse(context).toParty);

    // The rolls are the corpse's: the same items, kill by kill, from the same bad-luck counters.
    size_t drops = 0;

    for (uint32_t actor = 0; actor < 200; ++actor)
    {
        context.actorIndex = actor;
        rules.state().craftingPity.clear();
        const std::vector<CorpseLoot::ExtraItem> withoutCorpse = monsters.lootWithoutCorpse(context).items;
        rules.state().craftingPity.clear();
        const std::vector<CorpseLoot::ExtraItem> corpse = monsters.corpseLoot(context).extraItems;
        REQUIRE_EQ(withoutCorpse.size(), corpse.size());

        for (size_t index = 0; index < corpse.size(); ++index)
        {
            CHECK_EQ(withoutCorpse[index].itemId, corpse[index].itemId);
        }

        drops += corpse.size();
    }

    CHECK_GT(drops, 0u);
    CHECK(standardGameRules().monsters.lootWithoutCorpse(context).items.empty());
}

TEST_CASE("MAW's power report and the item popup's Power and Vitality comparison (L4.5)")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/items.yml");
    std::ostringstream text;
    text << input.rdbuf();
    MawItemData itemData;
    std::string error;
    REQUIRE_MESSAGE(itemData.loadFromYaml(text.str(), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, std::move(itemData));

    Character knight;
    knight.name = "Knight";
    knight.className = "Knight";
    knight.level = 20;
    knight.might = 40;
    knight.accuracy = 40;
    knight.speed = 30;
    knight.maxHealth = 400;
    knight.health = 400;
    knight.skills["Sword"] = {"Sword", 10, SkillMastery::Expert};
    knight.equipment.mainHand = 1;
    PartySeed seed;
    seed.members = {knight};
    Party party;
    party.seed(seed);
    party.setItemTable(&items);
    party.setRules(&rules.gameRules());

    const MawPowerReport report = mawPowerReport(rules, *party.member(0), items, nullptr, nullptr, 1);
    CHECK_GT(report.melee, 0);
    CHECK_GT(report.vitality, 0);
    CHECK_EQ(report.spell, 0);

    // The sword worn compares as no change; a stronger one as more power.
    const ItemDefinition &sword = *items.get(1);
    InventoryItem same;
    same.objectDescriptionId = 1;
    CHECK(rules.gameRules().items.comparisonLines(party, 0, same, sword).empty());
    InventoryItem stronger = same;
    stronger.rulesetFields.itemPower = 200;
    const std::vector<ItemInspectLine> lines = rules.gameRules().items.comparisonLines(party, 0, stronger, sword);
    REQUIRE_FALSE(lines.empty());
    CHECK(lines.front().text.starts_with("Power: +"));
    CHECK_EQ(lines.front().color, 0x00ff00u);

    // Standard compares nothing.
    CHECK(standardItemRules().comparisonLines(party, 0, stronger, sword).empty());

    // The stats page shows Melee Power in the Condition row, Ranged Power in the Quick Spell row, then Spell Power ("-"
    // without a damage spell) and Vitality in two added rows; Standard keeps both rows and adds none.
    const std::optional<CharacterStatRowText> melee =
        rules.gameRules().skills.statRowText(party, *party.member(0), "Condition");
    REQUIRE(melee.has_value());
    CHECK_EQ(melee->label, "Melee Power:");
    const std::optional<CharacterStatRowText> ranged =
        rules.gameRules().skills.statRowText(party, *party.member(0), "QuickSpell");
    REQUIRE(ranged.has_value());
    CHECK_EQ(ranged->label, "Ranged Power:");
    const std::optional<CharacterStatRowText> spell =
        rules.gameRules().skills.statRowText(party, *party.member(0), "SpellPower");
    REQUIRE(spell.has_value());
    CHECK_EQ(spell->label, "Spell Power:");
    const std::optional<CharacterStatRowText> vitality =
        rules.gameRules().skills.statRowText(party, *party.member(0), "Vitality");
    REQUIRE(vitality.has_value());
    CHECK_EQ(vitality->label, "Vitality:");
    CHECK_FALSE(standardGameRules().skills.statRowText(party, *party.member(0), "Vitality").has_value());
    CHECK_FALSE(standardGameRules().skills.statRowText(party, *party.member(0), "SpellPower").has_value());
    CHECK_FALSE(rules.gameRules().skills.statRowText(party, *party.member(0), "Might").has_value());
    CHECK_FALSE(standardGameRules().skills.statRowText(party, *party.member(0), "Condition").has_value());
}

TEST_CASE("MAW potion descriptions carry their numbers at the potion's power (L7.5)")
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/texts.yml");
    std::ostringstream text;
    text << input.rdbuf();
    MawTextData texts;
    std::string error;
    REQUIRE_MESSAGE(texts.loadFromYaml(text.str(), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{}, texts);
    const ItemRules &items = rules.gameRules().items;

    // Healing at power 50: 20 + a quarter of the HP a level-50 character is expected to have.
    InventoryItem healing;
    healing.objectDescriptionId = 222;
    healing.standardEnchantPower = 50;
    const int heal =
        int(mawRound(20 + rules.gameRules().potions.estimatedPool(PotionPool::HitPoints, 50) * 0.25));
    const std::optional<std::string> healText = items.itemDescription(healing, nullptr);
    REQUIRE(healText.has_value());
    CHECK_NE(healText->find("Heals " + std::to_string(heal) + " Hit Points"), std::string::npos);

    // Haste's percent grows with the power.
    InventoryItem haste;
    haste.objectDescriptionId = 228;
    haste.standardEnchantPower = 10;
    const std::string weak = *items.itemDescription(haste, nullptr);
    haste.standardEnchantPower = 200;
    const std::string strong = *items.itemDescription(haste, nullptr);
    CHECK_NE(weak, strong);
    CHECK_EQ(strong.find('{'), std::string::npos);

    // Transcendence at power 120: step 2, 50 skill points; the drinker's best step shows.
    InventoryItem transcendence;
    transcendence.objectDescriptionId = 259;
    transcendence.standardEnchantPower = 120;
    Character drinker;
    drinker.rulesetState.potionSteps[259] = 1;
    const std::string steps = *items.itemDescription(transcendence, &drinker);
    CHECK_NE(steps.find("50 Skill Points (step 2)"), std::string::npos);
    CHECK_NE(steps.find("Best step already taken: 1 (20 Skill Points)"), std::string::npos);

    // Items without a text and Standard keep the item table's notes.
    InventoryItem sword;
    sword.objectDescriptionId = 1;
    CHECK_FALSE(items.itemDescription(sword, nullptr).has_value());
    CHECK_FALSE(standardItemRules().itemDescription(healing, nullptr).has_value());
}

TEST_CASE("MAW mercenaries' gear loses its special or its second enchantment, even odds (H.8)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    InventoryItem item;
    item.objectDescriptionId = 1;
    item.specialEnchantId = 7;
    item.rulesetFields.secondStandardEnchantId = 3;
    item.rulesetFields.secondStandardEnchantPower = 12;
    std::mt19937 rng(5);
    int specials = 0;
    int seconds = 0;

    for (int roll = 0; roll < 400; ++roll)
    {
        InventoryItem trimmed = item;
        rules.gameRules().items.trimMercenaryItem(trimmed, rng);
        CHECK_NE(trimmed.specialEnchantId == 0, trimmed.rulesetFields.secondStandardEnchantId == 0);
        specials += trimmed.specialEnchantId == 0 ? 1 : 0;
        seconds += trimmed.rulesetFields.secondStandardEnchantId == 0 ? 1 : 0;
    }

    CHECK_GT(specials, 150);
    CHECK_GT(seconds, 150);

    // An item with only one of them keeps it; Standard changes nothing.
    InventoryItem single = item;
    single.rulesetFields.secondStandardEnchantId = 0;
    rules.gameRules().items.trimMercenaryItem(single, rng);
    CHECK_EQ(single.specialEnchantId, 7);
    InventoryItem standard = item;
    standardItemRules().trimMercenaryItem(standard, rng);
    CHECK(standard == item);
}

TEST_CASE("MAW mercenaries: skill points by level and class kinds by continent (H.8)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ClassRules &maw = rules.gameRules().classes;

    // Levels 2-9 give 5 each, 10-19 give 6: level 12 has 8 x 5 + 3 x 6.
    CHECK_EQ(maw.mercenarySkillPoints(1), 0u);
    CHECK_EQ(maw.mercenarySkillPoints(9), 40u);
    CHECK_EQ(maw.mercenarySkillPoints(12), 58u);
    CHECK_EQ(standardClassRules().mercenarySkillPoints(12), 55u);

    // MAW's own classes come from Enroth; every continent has Peasants.
    const std::vector<uint32_t> enroth = maw.mercenaryClassKinds(3, {6});
    CHECK(std::find(enroth.begin(), enroth.end(), 17u) != enroth.end());
    CHECK(std::find(enroth.begin(), enroth.end(), 20u) != enroth.end());
    const std::vector<uint32_t> jadame = maw.mercenaryClassKinds(1, {6});
    CHECK(std::find(jadame.begin(), jadame.end(), 16u) != jadame.end());
    CHECK(std::find(jadame.begin(), jadame.end(), 17u) == jadame.end());
    CHECK_EQ(standardClassRules().mercenaryClassKinds(1, {2, 6}), std::vector<uint32_t>{2, 6});
}

TEST_CASE("MAW's combat status line: the spell as attacker, crits, kills and an area spell's total (H.4)")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    rules.setSpellTable(&OpenYAMM::Tests::regressionGameData().spellTable);
    const CombatRules &combat = rules.gameRules().combat;
    PartyHitStatus blow;
    blow.attackerName = "Ariel";
    blow.targetName = "Goblin";
    blow.damage = 1234;
    blow.critical = true;
    CHECK_EQ(*combat.partyHitStatusText(blow), "Ariel hits Goblin for \f655161.234K\f00000 points!\f65516(CRIT!)\f00000");

    PartyHitStatus arrow = blow;
    arrow.critical = false;
    arrow.missile = true;
    arrow.damage = 57;
    CHECK_EQ(*combat.partyHitStatusText(arrow), "Ariel shoots Goblin for 57 points!");
    arrow.killed = true;
    CHECK_EQ(*combat.partyHitStatusText(arrow), "Ariel inflicts 57 points killing Goblin!");

    // Fireball (6) names itself; on several monsters it gives the total.
    const std::string fireball = OpenYAMM::Tests::regressionGameData().spellTable.findById(6)->name;
    PartyHitStatus spell = arrow;
    spell.killed = false;
    spell.spellId = 6;
    CHECK_EQ(*combat.partyHitStatusText(spell), fireball + " hits Goblin for 57 points!");
    spell.monstersHit = 3;
    spell.damage = 171;
    CHECK_EQ(*combat.partyHitStatusText(spell), fireball + " hits for a total of 171 points!");

    // Standard keeps the engine's own line.
    CHECK_FALSE(standardGameRules().combat.partyHitStatusText(blow).has_value());
}

TEST_CASE("MAW gem popups give the tier and the caps by item class (L7.5)")
{
    const auto read = [](const char *pPath)
    {
        std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / pPath);
        std::ostringstream text;
        text << input.rdbuf();
        return text.str();
    };
    MawTextData texts;
    MawCraftingData crafting;
    std::string error;
    REQUIRE_MESSAGE(texts.loadFromYaml(read("assets_dev/engine/rulesets/maw/data/texts.yml"), error), error);
    REQUIRE_MESSAGE(crafting.loadFromYaml(read("assets_dev/engine/rulesets/maw/data/crafting.yml"), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, std::move(crafting), texts);

    // Tier 20 on a x1 item reaches the Primordial maximum (125 up to Hell), two-handed weapons twice that.
    InventoryItem gem;
    gem.objectDescriptionId = 1060;
    const std::optional<std::string> text = rules.gameRules().items.itemDescription(gem, nullptr);
    REQUIRE(text.has_value());
    CHECK_NE(text->find("Tier: \f65516" "20"), std::string::npos);
    CHECK_NE(text->find("Max Power: \f65516" "125"), std::string::npos);
    CHECK_NE(text->find("Two Handed Weapons: \f65516" "250"), std::string::npos);
    CHECK_EQ(text->find('{'), std::string::npos);

    // A black potion names its step at this power and the best one drunk.
    InventoryItem black;
    black.objectDescriptionId = 252;
    black.standardEnchantPower = 120;
    Character drinker;
    drinker.rulesetState.potionSteps[252] = 1;
    CHECK_NE(rules.gameRules().items.itemDescription(black, &drinker)->find("step 2. Best step already drunk: 1"),
        std::string::npos);
}

TEST_CASE("MAW seals spellbooks found outside shops; a reader with the mastery opens them (A7.14)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure());
    const ItemTable &itemTable = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    rules.setItemTable(&itemTable);
    const ItemRules &items = rules.gameRules().items;
    const auto rolled = [&itemTable, &items](uint32_t itemId, ItemGenerationMode mode)
    {
        ItemGenerationRequest request;
        request.mode = mode;
        InventoryItem item = ItemGenerator::makeInventoryItem(itemId, itemTable, mode);
        items.rollPlainItem(item, *itemTable.get(itemId), request);
        return item;
    };

    // Fireball (identify difficulty 5) from a chest becomes the Fire Magic Book; shop stock stays a book.
    InventoryItem book = rolled(405, ItemGenerationMode::ChestLoot);
    CHECK_EQ(book.objectDescriptionId, 971);
    CHECK_EQ(book.rulesetFields.craftState, 405);
    CHECK_EQ(rolled(405, ItemGenerationMode::Shop).objectDescriptionId, 405);
    // The MM7 and MM6 books seal by their own school ranges: Light Bolt (MM7) to Light, Souldrinker (MM6) to Dark.
    CHECK_EQ(rolled(1279, ItemGenerationMode::MonsterLoot).objectDescriptionId, 978);
    CHECK_EQ(rolled(2018, ItemGenerationMode::Generic).objectDescriptionId, 979);
    CHECK_EQ(rolled(1914, ItemGenerationMode::MonsterLoot).objectDescriptionId, 971);

    // A sealed book is worth its book and says what opens it.
    const InventoryItem fireball = ItemGenerator::makeInventoryItem(405, itemTable, ItemGenerationMode::Shop);
    CHECK_EQ(items.itemValue(book, *itemTable.get(971), nullptr, nullptr, 1),
        standardItemRules().itemValue(fireball, *itemTable.get(405), nullptr, nullptr, 1));
    const std::optional<std::string> text = items.itemDescription(book, nullptr);
    REQUIRE(text.has_value());
    CHECK_NE(text->find("You need at least Expert skill in Fire Magic to open the book"), std::string::npos);

    // A Novice cannot open it, an Expert can; Standard seals nothing.
    Character reader;
    reader.skills["FireMagic"] = {"FireMagic", 4, SkillMastery::Normal};
    CHECK_FALSE(items.openSealedItem(book, reader));
    CHECK_FALSE(standardItemRules().openSealedItem(book, reader));
    reader.skills["FireMagic"].mastery = SkillMastery::Expert;
    REQUIRE(items.openSealedItem(book, reader));
    CHECK_EQ(book.objectDescriptionId, 405);
    CHECK_EQ(book.rulesetFields.craftState, 0);

    // Without an item table nothing opens and the description is the plain one.
    MawRules bare(RulesetOptions{}, MawMapLevels{});
    InventoryItem sealed = rolled(405, ItemGenerationMode::ChestLoot);
    CHECK_FALSE(bare.gameRules().items.openSealedItem(sealed, reader));
    CHECK_FALSE(bare.gameRules().items.itemDescription(sealed, nullptr).has_value());
}

TEST_CASE("MAW spellbook keys: R releases every aura, Tab turns the school (A7.13)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party;
    rules.state().auraHolders[5] = 0;
    rules.state().auraHolders[83] = MawGameState::FixedAuraHolder;
    rules.state().fixedAuraMaps[83] = "oute3.odm";
    const std::optional<std::string> status = rules.gameRules().spells.removeAllBuffs(party);
    REQUIRE(status.has_value());
    CHECK_EQ(*status, "All buffs have been removed");
    CHECK(rules.state().auraHolders.empty());
    CHECK(rules.state().fixedAuraMaps.empty());
    CHECK(rules.gameRules().spells.tabCyclesSpellbookSchools());
    CHECK_FALSE(standardGameRules().spells.removeAllBuffs(party).has_value());
    CHECK_FALSE(standardGameRules().spells.tabCyclesSpellbookSchools());
}

TEST_CASE("MAW race cards list the race's skill bonuses, resistances and immunities (A6.11)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ClassRules &classes = rules.gameRules().classes;
    Character elf;
    elf.raceId = 7;
    const std::vector<std::string> elfNotes = classes.raceNotes(elf);
    REQUIRE_EQ(elfNotes.size(), 2);
    CHECK_EQ(elfNotes[0], "+3 to " + displaySkillName("Bow") + ", " + displaySkillName("Spear") + " and "
            + displaySkillName("Meditation") + ", and +1 more per 10 skill levels.");
    CHECK_EQ(elfNotes[1], "Fire, Air, Water and Earth resistance +25, and +1 per level.");

    Character vampire;
    vampire.raceId = 1;
    const std::vector<std::string> vampireNotes = classes.raceNotes(vampire);
    REQUIRE_EQ(vampireNotes.size(), 2);
    CHECK_EQ(vampireNotes[0], "Immune to Mind magic.");
    CHECK_EQ(vampireNotes[1], "Preservation at night and in dungeons.");

    // The table drives the bonuses too: an undead character is immune to Body and Mind, a level-10 dragon resists fire
    // by 120.
    Character undead;
    undead.raceId = 6;
    classes.applyClassBonuses(undead);
    CHECK(undead.magicalImmunities.body);
    CHECK(undead.magicalImmunities.mind);
    Character dragon;
    dragon.raceId = 5;
    dragon.level = 10;
    classes.applyClassBonuses(dragon);
    CHECK_EQ(dragon.magicalBonuses.resistances.fire, 120);

    CHECK(classes.showsCreationSkillMatrix());
    CHECK(standardGameRules().classes.raceNotes(elf).empty());
    CHECK_FALSE(standardGameRules().classes.showsCreationSkillMatrix());
}

TEST_CASE("MAW's alchemist takes the party's alchemy items when it sorts (L7.2, D.18)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ItemRules &items = rules.gameRules().items;
    Party party = mawParty(rules, 2);

    // Potions first, the highest id first, then the reagent and crafting order; other items have no rank.
    InventoryItem potion = packItem(240, 1, 2);
    InventoryItem lowPotion = packItem(222, 1, 2);
    InventoryItem reagent = packItem(1002, 1, 1);
    InventoryItem sword = packItem(1, 1, 3);
    REQUIRE(items.alchemySortRank(potion).has_value());
    CHECK_LT(*items.alchemySortRank(potion), *items.alchemySortRank(lowPotion));
    CHECK_LT(*items.alchemySortRank(lowPotion), *items.alchemySortRank(reagent));
    CHECK_FALSE(items.alchemySortRank(sword).has_value());
    CHECK_FALSE(standardItemRules().alchemySortRank(potion).has_value());

    // E picks the member and picks nobody when pressed again.
    CHECK_FALSE(items.alchemist(party).has_value());
    REQUIRE(items.pickAlchemist(party, 1).has_value());
    CHECK_EQ(items.alchemist(party), std::optional<size_t>(1));
    CHECK_EQ(*items.pickAlchemist(party, 1), "No alchemy preference when sorting");
    CHECK_FALSE(items.alchemist(party).has_value());
    CHECK_FALSE(standardItemRules().pickAlchemist(party, 1).has_value());
    REQUIRE(items.pickAlchemist(party, 1).has_value());

    // The first member's potion and reagent go to the alchemist, potion first; the sword stays.
    REQUIRE(party.member(0)->addInventoryItem(sword));
    REQUIRE(party.member(0)->addInventoryItem(reagent));
    REQUIRE(party.member(0)->addInventoryItem(potion));
    REQUIRE(party.member(1)->addInventoryItem(lowPotion));
    const auto rank = [&items](const InventoryItem &item)
    {
        return items.alchemySortRank(item);
    };
    REQUIRE(InventoryBags::sortPartyBags(party, {0}, false, 5, items.alchemist(party), rank));
    REQUIRE_EQ(party.member(0)->inventory.size(), 1u);
    CHECK_EQ(party.member(0)->inventory[0].objectDescriptionId, 1u);
    const std::vector<InventoryItem> &alchemistItems = party.member(1)->inventory;
    REQUIRE_EQ(alchemistItems.size(), 3u);
    CHECK_EQ(alchemistItems[0].objectDescriptionId, 240u);
    CHECK_EQ(alchemistItems[1].objectDescriptionId, 222u);
    CHECK_EQ(alchemistItems[2].objectDescriptionId, 1002u);

    // Without an alchemist each member sorts alone.
    REQUIRE(InventoryBags::sortPartyBags(party, {0, 1}, true, 5, std::nullopt, rank));
    CHECK_EQ(party.member(0)->inventory.size(), 1u);
    CHECK_EQ(party.member(1)->inventory.size(), 3u);

    // The pick is saved with the MAW state.
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.saveName = "alchemist";
    save.party.members = {*party.member(0), *party.member(1)};
    save.mawState = rules.state();
    std::string error;
    const std::optional<GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    REQUIRE(restored->mawState.has_value());
    CHECK_EQ(restored->mawState->alchemistMember, 1);
}

TEST_CASE("A save from when MAW had more bags fits them into four; what fits nowhere waits for the floor (save 121)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(rules, 2);
    Character &solo = *party.member(0);
    // Bag 8 open, items in bags 0, 5 and 8.
    solo.rulesetState.currentBag = 7;
    solo.rulesetState.storedBags[0] = {packItem(1, 1, 3)};
    solo.rulesetState.storedBags[5] = {packItem(2, 2, 2)};
    REQUIRE(solo.addInventoryItem(packItem(3, 1, 1)));

    CHECK_EQ(InventoryBags::fitIntoBagCount(party, 4), 0u);
    CHECK_EQ(solo.rulesetState.currentBag, 0);
    CHECK(std::all_of(solo.rulesetState.storedBags.begin(), solo.rulesetState.storedBags.end(),
        [](const auto &entry) { return entry.first < 4; }));
    // Everything is in bag 1 now, apart and on the grid.
    REQUIRE_EQ(solo.inventory.size(), 3u);
    CHECK(InventoryBags::takeOverflow(solo).empty());

    // Every bag of both members full: the extra item waits in the overflow bag, then goes to the world.
    for (Character *pMember : {party.member(0), party.member(1)})
    {
        pMember->inventory.clear();
        pMember->rulesetState.storedBags.clear();
        pMember->rulesetState.currentBag = 0;
        REQUIRE(pMember->addInventoryItem(packItem(10, Character::InventoryWidth, Character::InventoryHeight)));

        for (uint8_t bag = 1; bag < 4; ++bag)
        {
            InventoryItem full = packItem(10, Character::InventoryWidth, Character::InventoryHeight);
            pMember->rulesetState.storedBags[bag] = {full};
        }
    }

    solo.rulesetState.storedBags[12] = {packItem(4, 1, 1)};
    CHECK_EQ(InventoryBags::fitIntoBagCount(party, 4), 1u);
    CHECK(solo.rulesetState.storedBags.contains(InventoryBags::OverflowBag));
    const std::vector<InventoryItem> overflow = InventoryBags::takeOverflow(solo);
    REQUIRE_EQ(overflow.size(), 1u);
    CHECK_EQ(overflow[0].objectDescriptionId, 4u);
    CHECK(InventoryBags::takeOverflow(solo).empty());
}

TEST_CASE("A party of one's tabs: Shift+Sort sorts the open tab, and the other tabs wait while the party is bigger")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(rules, 1);
    const int bagCount = rules.gameRules().items.bagCount(party);
    REQUIRE_EQ(bagCount, 20);
    Character &solo = *party.member(0);

    // Tab II (bags 4-7) open at its second bag; an item in tab I and two in tab II.
    REQUIRE(InventoryBags::openBag(solo, 5, bagCount));
    solo.rulesetState.storedBags[0] = {packItem(1, 1, 3)};
    solo.rulesetState.storedBags[6] = {packItem(2, 2, 2)};
    REQUIRE(solo.addInventoryItem(packItem(3, 1, 1)));

    // Sorting every bag sorts tab II only: its items go to its first bag; tab I keeps its item.
    REQUIRE(InventoryBags::sortPartyBags(party, {0}, true, bagCount, std::nullopt,
        [](const InventoryItem &) { return std::optional<int>(); }));
    CHECK_EQ(solo.rulesetState.currentBag, 5);
    REQUIRE(solo.rulesetState.storedBags.contains(0));
    CHECK_EQ(solo.rulesetState.storedBags.at(0)[0].objectDescriptionId, 1u);
    REQUIRE(solo.rulesetState.storedBags.contains(4));
    CHECK_EQ(solo.rulesetState.storedBags.at(4).size(), 2u);
    CHECK(solo.inventory.empty());
    CHECK_FALSE(solo.rulesetState.storedBags.contains(6));

    // With four bags (another member joined) tab II is out of reach but keeps its items: nothing is overflow.
    CHECK(InventoryBags::takeOverflow(solo).empty());
    REQUIRE(InventoryBags::openBag(solo, 0, 4));
    CHECK_EQ(solo.rulesetState.storedBags.at(4).size(), 2u);
    CHECK_EQ(InventoryBags::storedItemCount(solo), 2u);
}

TEST_CASE("MAW's crafting and alchemy bags take what the party picks up: the picker's first, then the others' (H.10)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const ItemTable &itemTable = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(rules, 3);
    party.member(0)->name = "First";
    party.member(2)->name = "Third";
    REQUIRE_EQ(party.activeMemberIndex(), 0u);
    const auto pickUp = [&party, &itemTable](uint32_t itemId)
    {
        return storePickedUpItem(party, packItem(itemId, 1, 1), &itemTable);
    };
    const auto bagHolds = [&party](size_t member, uint8_t bag, uint32_t itemId)
    {
        const std::vector<InventoryItem> &items = InventoryBags::itemsInBag(*party.member(member), bag);
        return std::any_of(items.begin(), items.end(),
            [itemId](const InventoryItem &item) { return item.objectDescriptionId == itemId; });
    };

    // No tagged bag: the inventory, as before.
    std::optional<StoredPickup> stored = pickUp(1041);
    REQUIRE(stored);
    CHECK_FALSE(stored->taggedBag);
    CHECK(bagHolds(0, 0, 1041));

    // Another member's crafting bag takes a crafting item, named in the status line (zzzMaw_CraftingBag.lua:240-245).
    CHECK(InventoryBags::toggleTag(*party.member(2), 2, BagTag::Crafting));
    CHECK(InventoryBags::toggleTag(*party.member(1), 1, BagTag::Alchemy));
    stored = pickUp(1042);
    REQUIRE(stored);
    CHECK(stored->taggedBag);
    CHECK_EQ(stored->memberIndex, 2u);
    CHECK(bagHolds(2, 2, 1042));
    CHECK_EQ(party.member(2)->rulesetState.currentBag, 0);
    CHECK_EQ(storedPickupOwnerSuffix(party, *stored), " -- Third");

    // The picker's own crafting bag comes first, with no name.
    CHECK(InventoryBags::toggleTag(*party.member(0), 3, BagTag::Crafting));
    stored = pickUp(1043);
    REQUIRE(stored);
    CHECK_EQ(stored->memberIndex, 0u);
    CHECK(bagHolds(0, 3, 1043));
    CHECK_EQ(storedPickupOwnerSuffix(party, *stored), "");

    // Potions go to the alchemy bag; other items do not care for tags.
    stored = pickUp(222);
    REQUIRE(stored);
    CHECK_EQ(stored->memberIndex, 1u);
    CHECK(bagHolds(1, 1, 222));
    stored = pickUp(1);
    REQUIRE(stored);
    CHECK_FALSE(stored->taggedBag);

    // Full crafting bags pass the item on, in the end to the inventory.
    party.member(0)->rulesetState.storedBags[3] = {packItem(10, Character::InventoryWidth, Character::InventoryHeight)};
    stored = pickUp(1044);
    REQUIRE(stored);
    CHECK_EQ(stored->memberIndex, 2u);
    party.member(2)->rulesetState.storedBags[2] = {packItem(10, Character::InventoryWidth, Character::InventoryHeight)};
    stored = pickUp(1045);
    REQUIRE(stored);
    CHECK_FALSE(stored->taggedBag);
    CHECK(bagHolds(0, 0, 1045));

    // Untagging; Standard has no tags, whatever a character carries.
    CHECK_FALSE(InventoryBags::toggleTag(*party.member(0), 3, BagTag::Crafting));
    CHECK_FALSE(InventoryBags::hasTag(*party.member(0), 3, BagTag::Crafting));
    Party standard = {};
    standard.seed(PartySeed{{Character{}}});
    InventoryBags::toggleTag(*standard.member(0), 0, BagTag::Crafting);
    stored = storePickedUpItem(standard, packItem(1046, 1, 1), &itemTable);
    REQUIRE(stored);
    CHECK_FALSE(stored->taggedBag);
}

TEST_CASE("MAW bag tags survive a save (H.10, save 123)")
{
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.saveName = "tags";
    Character maw;
    maw.name = "Maw";
    InventoryBags::toggleTag(maw, 1, BagTag::Crafting);
    InventoryBags::toggleTag(maw, 3, BagTag::Crafting);
    InventoryBags::toggleTag(maw, 3, BagTag::Alchemy);
    save.party.members = {maw};

    std::string error;
    const std::optional<GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    const Character &loaded = restored->party.members.at(0);
    CHECK(InventoryBags::hasTag(loaded, 1, BagTag::Crafting));
    CHECK(InventoryBags::hasTag(loaded, 3, BagTag::Crafting));
    CHECK(InventoryBags::hasTag(loaded, 3, BagTag::Alchemy));
    CHECK_FALSE(InventoryBags::hasTag(loaded, 1, BagTag::Alchemy));
    CHECK_FALSE(InventoryBags::hasTag(loaded, 0, BagTag::Crafting));
}

TEST_CASE("MAW's sort takes items of one height in the engine's skill order, Sword before Axe (audit TXT-2-B3)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const ItemTable &itemTable = OpenYAMM::Tests::regressionGameData().itemTable;
    Character character;
    REQUIRE(character.addInventoryItem(packItem(31, 1, 3)));
    REQUIRE(character.addInventoryItem(packItem(1, 1, 3)));
    REQUIRE(InventoryBags::sortAllBags(character, 5, &itemTable));
    REQUIRE_EQ(character.inventory.size(), 2u);
    const auto columnOf = [&character](uint32_t itemId)
    {
        for (const InventoryItem &item : character.inventory)
        {
            if (item.objectDescriptionId == itemId)
            {
                return int(item.gridX) * 100 + int(item.gridY);
            }
        }

        return -1;
    };
    CHECK(columnOf(1) < columnOf(31));
}

TEST_CASE("MAW's gather key brings corpses and crafting items; Standard has none (L7.2, D.18)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ItemRules &items = rules.gameRules().items;
    REQUIRE(items.lootGathering().has_value());
    CHECK_EQ(items.lootGathering()->corpses, 30u);
    CHECK_EQ(items.lootGathering()->items, 30u);
    CHECK(items.gathersItem(packItem(1041, 1, 1)));
    CHECK(items.gathersItem(packItem(1069, 1, 1)));
    CHECK(items.gathersItem(packItem(290, 1, 1)));
    // The Crafting Cube (1070) is a crafting item too (audit TXT-2-B4).
    CHECK(items.gathersItem(packItem(1070, 1, 1)));
    CHECK_FALSE(items.gathersItem(packItem(1071, 1, 1)));
    CHECK_FALSE(items.gathersItem(packItem(1040, 1, 1)));
    CHECK_FALSE(standardItemRules().lootGathering().has_value());

    // The keys: MAW's actions have their own ini names and defaults.
    CHECK_EQ(keyboardBindingDefinition(KeyboardAction::GatherLoot).iniKey, "gather_loot");
    CHECK_EQ(keyboardBindingDefinition(KeyboardAction::GatherLoot).defaultBinding.scancode, SDL_SCANCODE_G);
    CHECK_EQ(keyboardBindingDefinition(KeyboardAction::Unstuck).defaultBinding.kind, InputBindingKind::None);
    CHECK_EQ(keyboardBindingDefinition(KeyboardAction::AlchemistPick).defaultBinding.scancode, SDL_SCANCODE_A);
}

TEST_CASE("MAW Doom: chests need Disarm Traps for the map's lock, unidentified items are not worn, shop prices (P9.D3-D5)")
{
    RulesetOptions doomOptions;
    doomOptions.challengeMode = RulesetChallengeMode::Doom;
    MawRules doom(doomOptions, MawMapLevels{});
    MawRules plain(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(doom, 2);

    // Lock 3 needs skill x mastery 3; lock 5 needs 10; a Grandmaster opens anything; no lock needs nothing.
    party.member(1)->skills["DisarmTraps"] = {"DisarmTraps", 3, SkillMastery::Normal};
    const ItemRules &items = doom.gameRules().items;
    CHECK_FALSE(items.chestOpenRefusal(party, 3).has_value());
    CHECK_FALSE(items.chestOpenRefusal(party, 0).has_value());
    REQUIRE(items.chestOpenRefusal(party, 5).has_value());
    CHECK_EQ(*items.chestOpenRefusal(party, 5), "Not enough disarm skill");
    party.member(1)->skills["DisarmTraps"] = {"DisarmTraps", 5, SkillMastery::Expert};
    CHECK_FALSE(items.chestOpenRefusal(party, 5).has_value());
    CHECK(items.chestOpenRefusal(party, 6).has_value());
    party.member(0)->skills["DisarmTraps"] = {"DisarmTraps", 1, SkillMastery::Grandmaster};
    CHECK_FALSE(items.chestOpenRefusal(party, 50).has_value());
    CHECK_FALSE(plain.gameRules().items.chestOpenRefusal(mawParty(plain, 1), 50).has_value());

    // Unidentified items cannot be worn in Doom.
    InventoryItem unknown;
    unknown.objectDescriptionId = 1;
    unknown.identified = false;
    CHECK(items.wearRefusal(unknown).has_value());
    unknown.identified = true;
    CHECK_FALSE(items.wearRefusal(unknown).has_value());
    unknown.identified = false;
    CHECK_FALSE(plain.gameRules().items.wearRefusal(unknown).has_value());

    // Identify takes the identify difficulty squared as the shop's multiplier, repairs 5.
    ItemDefinition definition;
    definition.idRepSt = "7";
    CHECK_EQ(items.shopServiceMultiplier(definition, true, 1.5f), doctest::Approx(49.0f));
    CHECK_EQ(items.shopServiceMultiplier(definition, false, 1.5f), doctest::Approx(5.0f));
    CHECK_EQ(plain.gameRules().items.shopServiceMultiplier(definition, true, 1.5f), doctest::Approx(1.5f));
}

TEST_CASE("MAW Doom: equipping an unidentified item is refused (P9.D3)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure());
    RulesetOptions doomOptions;
    doomOptions.challengeMode = RulesetChallengeMode::Doom;
    MawRules doom(doomOptions, MawMapLevels{});
    Party party = mawParty(doom, 1);
    party.setItemTable(&OpenYAMM::Tests::regressionGameData().itemTable);
    party.member(0)->className = "Knight";
    InventoryItem ring = ItemGenerator::makeInventoryItem(137, OpenYAMM::Tests::regressionGameData().itemTable,
        ItemGenerationMode::Generic);
    ring.identified = false;
    std::optional<InventoryItem> held;
    CHECK_FALSE(party.tryEquipItemOnMember(0, EquipmentSlot::Ring1, ring, std::nullopt, false, held));
    CHECK_EQ(party.lastStatus(), "Identify the item first");
    ring.identified = true;
    CHECK(party.tryEquipItemOnMember(0, EquipmentSlot::Ring1, ring, std::nullopt, false, held));
}

TEST_CASE("MAW Doom: NPC followers join only in houses 1466 and 1486 (P9.D6)")
{
    RulesetOptions doomOptions;
    doomOptions.challengeMode = RulesetChallengeMode::RoadToInsanity;
    MawRules doom(doomOptions, MawMapLevels{});
    MawRules plain(RulesetOptions{}, MawMapLevels{});
    const ClassRules &classes = doom.gameRules().classes;
    REQUIRE(classes.followerHireRefusal(0).has_value());
    CHECK_EQ(classes.followerHireRefusal(0)->topic, "Following you would be foolish");
    CHECK(classes.followerHireRefusal(120).has_value());
    CHECK_FALSE(classes.followerHireRefusal(1466).has_value());
    CHECK_FALSE(classes.followerHireRefusal(1486).has_value());
    CHECK_FALSE(plain.gameRules().classes.followerHireRefusal(0).has_value());
    CHECK_FALSE(standardGameRules().classes.followerHireRefusal(0).has_value());
}

TEST_CASE("MAW Insanity: spellbooks cost more in shops by their place, training by the expected skill (P9.I5)")
{
    RulesetOptions insanityOptions;
    insanityOptions.challengeMode = RulesetChallengeMode::RoadToInsanity;
    MawRules insanity(insanityOptions, MawMapLevels{});
    MawRules plain(RulesetOptions{}, MawMapLevels{});
    const auto book = [](uint32_t itemId)
    {
        ItemDefinition definition;
        definition.itemId = itemId;
        definition.value = 100;
        InventoryItem item;
        item.objectDescriptionId = itemId;
        return std::pair(definition, item);
    };
    const auto price = [](const MawRules &rules, const std::pair<ItemDefinition, InventoryItem> &entry)
    {
        return rules.gameRules().items.shopBuyValue(entry.second, entry.first, nullptr, nullptr);
    };

    // MM8 Fire: Torch Light (1st) x1, Fireball (6th) x5, Inferno (10th) x10, Incinerate (11th) x20.
    CHECK_EQ(price(insanity, book(400)), price(plain, book(400)));
    CHECK_EQ(price(insanity, book(405)), 5 * price(plain, book(405)));
    CHECK_EQ(price(insanity, book(409)), 10 * price(plain, book(409)));
    CHECK_EQ(price(insanity, book(410)), 20 * price(plain, book(410)));
    // MM6's thirteen books share places: the 13th Fire book (Incinerate, 1914) is the 11th.
    CHECK_EQ(price(insanity, book(1914)), 20 * price(plain, book(1914)));

    Character trainee;
    trainee.level = 50;
    const float multiplier = insanity.gameRules().skills.trainingPriceMultiplier(trainee, 2.0f);
    CHECK_EQ(multiplier, doctest::Approx(insanity.model(1).skill(50) + 4));
    CHECK_EQ(plain.gameRules().skills.trainingPriceMultiplier(trainee, 2.0f), doctest::Approx(2.0f));
}

TEST_CASE("MAW Insanity: a town names another town's open bounty instead of a new one (P9.I8)")
{
    RulesetOptions insanityOptions;
    insanityOptions.challengeMode = RulesetChallengeMode::RoadToInsanity;
    MawRules insanity(insanityOptions, MawMapLevels{});
    MawRules plain(RulesetOptions{}, MawMapLevels{});
    MapStats maps;
    insanity.setMapTable(&maps);
    const std::vector<OpenBounty> open = {{"out02.odm", 12}, {"out03.odm", 40}};
    const std::optional<std::pair<OpenBounty, std::string>> named = insanity.gameRules().monsters.bountyElsewhere(open);
    REQUIRE(named.has_value());
    CHECK_EQ(named->first.monsterId, 12);
    CHECK_EQ(named->second, "out02.odm");
    CHECK_FALSE(insanity.gameRules().monsters.bountyElsewhere({}).has_value());
    CHECK_FALSE(plain.gameRules().monsters.bountyElsewhere(open).has_value());
}

TEST_CASE("MAW Beyond Madness: the death count, the pending seconds and the load warning (P9.M8 UI)")
{
    RulesetOptions madnessOptions;
    madnessOptions.challengeMode = RulesetChallengeMode::BeyondMadness;
    MawRules madness(madnessOptions, MawMapLevels{});
    const std::filesystem::path ledger =
        std::filesystem::temp_directory_path() / ("maw_ledger_ui_" + std::to_string(std::random_device{}()) + ".txt");
    madness.setMadnessLedgerFile(ledger);
    madness.setRandomRootSeed(77);
    const ExperienceRules &experience = madness.gameRules().experience;

    CHECK_EQ(experience.runDeaths(), std::optional<int>(0));
    CHECK_FALSE(experience.deathPendingSeconds(100).has_value());
    CHECK_FALSE(experience.loadWarning().has_value());

    // A hit: five game minutes pending, ten real seconds at the hit.
    madness.markMadnessHit(100);
    CHECK_EQ(experience.deathPendingSeconds(100), std::optional<int>(10));
    CHECK_EQ(experience.deathPendingSeconds(102.6), std::optional<int>(5));
    REQUIRE(experience.loadWarning().has_value());
    CHECK_EQ(*experience.loadWarning(), "Loading now will count as death, are you sure to proceed?");

    MawRules plain(RulesetOptions{}, MawMapLevels{});
    CHECK_FALSE(plain.gameRules().experience.runDeaths().has_value());
    CHECK_FALSE(standardGameRules().experience.loadWarning().has_value());
    std::error_code error;
    std::filesystem::remove(ledger, error);
}

TEST_CASE("MAW's disintegration preference survives a save (P9.I3 preference)")
{
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.saveName = "disintegration";
    save.ruleset.id = "maw";
    save.ruleset.options.challengeMode = RulesetChallengeMode::RoadToInsanity;
    save.ruleset.options.difficulty = RulesetDifficulty::Nightmare;
    save.ruleset.options.preferences.disintegration = false;
    Character member;
    member.name = "Member";
    save.party.members = {member};
    std::string error;
    const std::optional<GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK_FALSE(restored->ruleset.options.preferences.disintegration);
    CHECK(RulesetPreferences{}.disintegration);
}

TEST_CASE("MAW shows each raise's cost and the schools that share it; Standard shows none (D.16)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SkillRules &skills = rules.gameRules().skills;
    Character sorcerer;
    sorcerer.className = "Sorcerer";

    for (const auto &[name, level] : std::vector<std::pair<std::string, uint32_t>>{
             {"FireMagic", 10}, {"AirMagic", 10}, {"WaterMagic", 7}, {"Meditation", 5}})
    {
        sorcerer.skills[name] = CharacterSkill{name, level, SkillMastery::Normal};
    }

    // Water 7 to 8 is shared with Fire and Air (both at 8 or more): ceil(8 / 3) = 3.
    const std::optional<SkillRaiseCost> water = skills.skillRaiseCostDetail(sorcerer, "WaterMagic");
    REQUIRE(water.has_value());
    CHECK_EQ(water->cost, 3u);
    CHECK_EQ(water->fullCost, 8u);
    std::vector<std::string> sharedWith = water->sharedWith;
    std::sort(sharedWith.begin(), sharedWith.end());
    CHECK_EQ(sharedWith, std::vector<std::string>{"Air Magic", "Fire Magic"});

    // Fire 10 to 11 has nobody at 11: the full cost, shared with nobody.
    const std::optional<SkillRaiseCost> fire = skills.skillRaiseCostDetail(sorcerer, "FireMagic");
    REQUIRE(fire.has_value());
    CHECK_EQ(fire->cost, 11u);
    CHECK_EQ(fire->fullCost, 11u);
    CHECK(fire->sharedWith.empty());

    // Outside the shared set the raise costs the new level.
    const std::optional<SkillRaiseCost> meditation = skills.skillRaiseCostDetail(sorcerer, "Meditation");
    REQUIRE(meditation.has_value());
    CHECK_EQ(meditation->cost, 6u);
    CHECK(meditation->sharedWith.empty());

    CHECK_FALSE(skills.skillRaiseCostDetail(sorcerer, "EarthMagic").has_value());
    CHECK_FALSE(standardSkillRules().skillRaiseCostDetail(sorcerer, "WaterMagic").has_value());
}

TEST_CASE("Bag overview: items go into and come out of any bag while the open bag stays open (H.1, four bags)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawParty(rules, 2);
    const int bagCount = rules.gameRules().items.bagCount(party);
    REQUIRE_EQ(bagCount, 4);
    Character &member = *party.member(0);
    const InventoryItem sword = packItem(1, 1, 3);
    const InventoryItem potion = packItem(222, 1, 2);

    // Into bag 3 at (4, 2) while bag 1 stays open; the grid of bag 3 holds it there.
    std::optional<InventoryItem> replaced;
    REQUIRE(InventoryBags::placeInBag(party, 0, 2, bagCount, sword, 4, 2, replaced));
    CHECK_FALSE(replaced.has_value());
    CHECK_EQ(member.rulesetState.currentBag, 0);
    CHECK(member.inventory.empty());
    REQUIRE_EQ(InventoryBags::itemsInBag(member, 2).size(), 1u);
    const InventoryItem *pPlaced = InventoryBags::itemInBagAt(member, 2, 4, 4);
    REQUIRE(pPlaced != nullptr);
    CHECK_EQ(pPlaced->gridX, 4);
    CHECK_EQ(pPlaced->gridY, 2);
    CHECK(InventoryBags::itemInBagAt(member, 2, 5, 2) == nullptr);
    CHECK(InventoryBags::itemInBagAt(member, 1, 4, 2) == nullptr);

    // The open bag takes items as before, through the same calls.
    REQUIRE(InventoryBags::placeInBag(party, 0, 0, bagCount, potion, 0, 0, replaced));
    REQUIRE_EQ(member.inventory.size(), 1u);
    CHECK_EQ(member.inventory[0].objectDescriptionId, 222u);

    // Dropping on an item swaps them, as on the full-size grid.
    REQUIRE(InventoryBags::placeInBag(party, 0, 2, bagCount, potion, 4, 2, replaced));
    REQUIRE(replaced.has_value());
    CHECK_EQ(replaced->objectDescriptionId, 1u);
    CHECK_EQ(InventoryBags::itemInBagAt(member, 2, 4, 2)->objectDescriptionId, 222u);

    // Out of bag 3 by any of its cells; the bag is empty again and bag 1 still open.
    InventoryItem taken = {};
    REQUIRE(InventoryBags::takeFromBag(party, 0, 2, bagCount, 4, 3, taken));
    CHECK_EQ(taken.objectDescriptionId, 222u);
    CHECK(InventoryBags::itemsInBag(member, 2).empty());
    CHECK_FALSE(member.rulesetState.storedBags.contains(2));
    CHECK_EQ(member.rulesetState.currentBag, 0);
    CHECK_FALSE(InventoryBags::takeFromBag(party, 0, 2, bagCount, 4, 3, taken));

    // A bag beyond the ruleset's count and a place off the grid are refused, with nothing changed.
    CHECK_FALSE(InventoryBags::placeInBag(party, 0, uint8_t(bagCount), bagCount, sword, 0, 0, replaced));
    CHECK_FALSE(InventoryBags::placeInBag(party, 0, 1, bagCount, sword, 0, Character::InventoryHeight - 1, replaced));
    CHECK(InventoryBags::itemsInBag(member, 1).empty());
    CHECK_EQ(member.inventory.size(), 1u);
}

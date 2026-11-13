#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/gameplay/GameMechanics.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"

#include "tests/RegressionGameData.h"

#include <filesystem>
#include <random>

namespace
{
const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

OpenYAMM::Game::Character makeRegressionPartyMember(
    const std::string &name,
    const std::string &className,
    const std::string &portraitTextureName,
    uint32_t characterDataId)
{
    OpenYAMM::Game::Character member = {};
    member.name = name;
    member.className = className;
    member.role = className;
    member.portraitTextureName = portraitTextureName;
    member.characterDataId = characterDataId;
    member.birthYear = 1160;
    member.experience = 0;
    member.level = 1;
    member.skillPoints = 5;
    member.might = 14;
    member.intellect = 14;
    member.personality = 14;
    member.endurance = 14;
    member.speed = 14;
    member.accuracy = 14;
    member.luck = 14;
    member.maxHealth = 40;
    member.health = 40;
    member.maxSpellPoints = 20;
    member.spellPoints = 20;
    return member;
}

OpenYAMM::Game::PartySeed createRegressionPartySeed()
{
    OpenYAMM::Game::PartySeed seed = {};
    seed.gold = 200;
    seed.food = 7;
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));
    seed.members.push_back(makeRegressionPartyMember("Brom", "Cleric", "PC03-01", 3));
    seed.members.push_back(makeRegressionPartyMember("Cedric", "Druid", "PC05-01", 5));
    seed.members.push_back(makeRegressionPartyMember("Daria", "Sorcerer", "PC07-01", 7));
    return seed;
}

OpenYAMM::Game::Party makeRegressionParty(const OpenYAMM::Tests::RegressionGameData &gameData)
{
    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setCharacterDollTable(&gameData.characterDollTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);
    party.setClassMultiplierTable(&gameData.classMultiplierTable);
    party.setClassSkillTable(&gameData.classSkillTable);
    party.seed(createRegressionPartySeed());
    return party;
}

OpenYAMM::Game::ItemTable makeSkillLearningItemTable(const std::string &targetSkills)
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1));

    std::vector<std::string> itemRow(26);
    itemRow[0] = "10000";
    itemRow[1] = "missing_test_icon";
    itemRow[2] = "Skill Learning Scroll";
    itemRow[4] = "LearnSkill";
    itemRow[17] = "test";
    itemRow[18] = "test:item/skill_learning_scroll";
    itemRow[19] = "1";
    itemRow[22] = "LearnSkill";
    itemRow[23] = targetSkills;

    OpenYAMM::Game::ItemTable itemTable;
    REQUIRE(itemTable.load(assetFileSystem, {itemRow}, {}));
    return itemTable;
}

// MM9's Clover as its item table has it: a misc item whose use gives VarA skill points.
OpenYAMM::Game::ItemTable makeCloverItemTable()
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1));

    std::vector<std::string> itemRow(26);
    itemRow[0] = "10590";
    itemRow[1] = "missing_test_icon";
    itemRow[2] = "Clover";
    itemRow[4] = "Misc";
    itemRow[12] = "1";
    itemRow[17] = "test";
    itemRow[18] = "test:item/clover";
    itemRow[19] = "590";
    itemRow[22] = "GrantSkillPoints";

    OpenYAMM::Game::ItemTable itemTable;
    REQUIRE(itemTable.load(assetFileSystem, {itemRow}, {}));
    return itemTable;
}

std::optional<uint16_t> findSpecialEnchantId(
    const OpenYAMM::Game::SpecialItemEnchantTable &table,
    OpenYAMM::Game::SpecialItemEnchantKind kind)
{
    const std::vector<OpenYAMM::Game::SpecialItemEnchantEntry> &entries = table.entries();

    for (size_t index = 0; index < entries.size(); ++index)
    {
        if (entries[index].kind == kind)
        {
            return static_cast<uint16_t>(index + 1);
        }
    }

    return std::nullopt;
}

void applyMergedRareItemEffects(
    const OpenYAMM::Tests::RegressionGameData &gameData,
    uint32_t itemId,
    OpenYAMM::Game::Character &character)
{
    const OpenYAMM::Game::ItemDefinition *pDefinition = gameData.itemTable.get(itemId);
    REQUIRE(pDefinition != nullptr);

    OpenYAMM::Game::EquippedItemRuntimeState runtimeState = {};
    runtimeState.artifactId = static_cast<uint16_t>(itemId);
    runtimeState.rarity = pDefinition->rarity;
    OpenYAMM::Game::ItemEnchantRuntime::applyEquippedEnchantEffects(
        *pDefinition,
        runtimeState,
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable,
        character);
}
}

TEST_CASE("inventory item use spell scroll prepares a master cast")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);

    OpenYAMM::Game::InventoryItem scroll = {};
    scroll.objectDescriptionId = 300;

    const OpenYAMM::Game::InventoryItemUseResult result = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        scroll,
        gameData.itemTable,
        &gameData.readableScrollTable);

    REQUIRE(result.handled);
    CHECK(result.action == OpenYAMM::Game::InventoryItemUseAction::CastScroll);
    CHECK_EQ(result.spellId, OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::TorchLight));
    CHECK_EQ(result.spellSkillLevelOverride, 7u);
    CHECK(result.spellSkillMasteryOverride == OpenYAMM::Game::SkillMastery::Master);
    CHECK(result.spellBypassRequiredMastery);
    CHECK(result.consumed);
}

TEST_CASE("inventory item use: the Dimension Door scroll and Verdant's connector stones do nothing")
{
    // Dimensional travel is the towns' pedestals and fountains and the Town Portal continent buttons (Verdant removed,
    // 2026-11-09): the scroll (a Gem item) and the stones are not usable: a use is refused and spends nothing.
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);

    for (uint32_t itemId : {190u, 624u, 625u})
    {
        OpenYAMM::Game::InventoryItem item = {};
        item.objectDescriptionId = itemId;

        const OpenYAMM::Game::InventoryItemUseResult result =
            OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
                party,
                0,
                item,
                gameData.itemTable,
                &gameData.readableScrollTable);

        CHECK(result.action != OpenYAMM::Game::InventoryItemUseAction::CastScroll);
        CHECK_FALSE(result.consumed);
        CHECK_EQ(result.spellId, 0u);
        CHECK_FALSE(result.statusText.empty());
    }
}

TEST_CASE("inventory item use spellbook consumes on success with matching school and mastery")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->skills["FireMagic"] = {"FireMagic", 4, OpenYAMM::Game::SkillMastery::Normal};
    pMember->forgetSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt));

    OpenYAMM::Game::InventoryItem spellbook = {};
    spellbook.objectDescriptionId = 401;

    const OpenYAMM::Game::InventoryItemUseResult result = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        spellbook,
        gameData.itemTable,
        &gameData.readableScrollTable);

    REQUIRE(result.handled);
    CHECK(result.action == OpenYAMM::Game::InventoryItemUseAction::LearnSpell);
    CHECK(result.consumed);
    CHECK(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt)));
    CHECK(result.speechId == OpenYAMM::Game::SpeechId::LearnSpell);
}

TEST_CASE("inventory item use skill scroll learns a core skill for the targeted member")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    CHECK(gameData.classSkillTable.getClassCap("Assassin", "Throwing")
        == OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK(gameData.classSkillTable.getClassCap("Champion", "Throwing")
        == OpenYAMM::Game::SkillMastery::Master);
    CHECK(gameData.classSkillTable.getClassCap("MinotaurLord", "Throwing")
        == OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK(gameData.classSkillTable.getClassCap("WarTroll", "Throwing")
        == OpenYAMM::Game::SkillMastery::Master);
    CHECK(gameData.classSkillTable.getClassCap("Cleric", "Throwing")
        == OpenYAMM::Game::SkillMastery::None);
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::ItemTable itemTable = makeSkillLearningItemTable("Throwing");
    party.setItemTable(&itemTable);

    OpenYAMM::Game::Character *pTargetMember = party.member(0);
    REQUIRE(pTargetMember != nullptr);
    pTargetMember->skills.erase("Throwing");

    OpenYAMM::Game::InventoryItem skillScroll = {};
    skillScroll.objectDescriptionId = 10000;
    const OpenYAMM::Game::InventoryItemUseResult learned =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
            party,
            0,
            skillScroll,
            itemTable,
            nullptr);

    REQUIRE(learned.handled);
    CHECK(learned.action == OpenYAMM::Game::InventoryItemUseAction::LearnSkill);
    CHECK(learned.consumed);
    REQUIRE_EQ(learned.learnedSkills.size(), 1);
    CHECK_EQ(learned.learnedSkills[0], "Throwing");
    CHECK(pTargetMember->hasSkill("Throwing"));

    const OpenYAMM::Game::InventoryItemUseResult repeated =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
            party,
            0,
            skillScroll,
            itemTable,
            nullptr);
    CHECK(repeated.handled);
    CHECK_FALSE(repeated.consumed);
    CHECK(repeated.alreadyKnown);
}

TEST_CASE("inventory item use learns composite skills atomically")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::ItemTable itemTable = makeSkillLearningItemTable("Sword|Dagger");
    party.setItemTable(&itemTable);
    OpenYAMM::Game::Character *pTargetMember = party.member(0);
    REQUIRE(pTargetMember != nullptr);
    pTargetMember->skills.erase("Sword");
    pTargetMember->skills.erase("Dagger");

    OpenYAMM::Game::InventoryItem skillBook = {};
    skillBook.objectDescriptionId = 10000;
    const OpenYAMM::Game::InventoryItemUseResult result =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(party, 0, skillBook, itemTable, nullptr);

    REQUIRE(result.handled);
    CHECK(result.consumed);
    CHECK((result.learnedSkills == std::vector<std::string>{"Sword", "Dagger"}));
    CHECK(pTargetMember->hasSkill("Sword"));
    CHECK(pTargetMember->hasSkill("Dagger"));
}

TEST_CASE("inventory item use rejects an ineligible composite skill without partial mutation")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::ItemTable itemTable = makeSkillLearningItemTable("Sword|DarkMagic");
    party.setItemTable(&itemTable);
    OpenYAMM::Game::Character *pTargetMember = party.member(0);
    REQUIRE(pTargetMember != nullptr);
    pTargetMember->skills.erase("Sword");
    pTargetMember->skills.erase("DarkMagic");

    OpenYAMM::Game::InventoryItem skillBook = {};
    skillBook.objectDescriptionId = 10000;
    const OpenYAMM::Game::InventoryItemUseResult result =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(party, 0, skillBook, itemTable, nullptr);

    REQUIRE(result.handled);
    CHECK_FALSE(result.consumed);
    CHECK_FALSE(pTargetMember->hasSkill("Sword"));
    CHECK_FALSE(pTargetMember->hasSkill("DarkMagic"));
}

TEST_CASE("inventory item use spellbook fails when the spell is already known")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->skills["FireMagic"] = {"FireMagic", 4, OpenYAMM::Game::SkillMastery::Normal};
    pMember->learnSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::TorchLight));

    OpenYAMM::Game::InventoryItem spellbook = {};
    spellbook.objectDescriptionId = 400;

    const OpenYAMM::Game::InventoryItemUseResult result = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        spellbook,
        gameData.itemTable,
        &gameData.readableScrollTable);

    REQUIRE(result.handled);
    CHECK(result.action == OpenYAMM::Game::InventoryItemUseAction::LearnSpell);
    CHECK_FALSE(result.consumed);
    CHECK(result.alreadyKnown);
    CHECK_FALSE(result.speechId.has_value());
}

TEST_CASE("inventory item use spellbook fails without matching school and preserves the item")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->skills.erase("AirMagic");
    pMember->forgetSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WizardEye));

    OpenYAMM::Game::InventoryItem spellbook = {};
    spellbook.objectDescriptionId = 411;

    const OpenYAMM::Game::InventoryItemUseResult result = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        spellbook,
        gameData.itemTable,
        &gameData.readableScrollTable);

    REQUIRE(result.handled);
    CHECK(result.action == OpenYAMM::Game::InventoryItemUseAction::LearnSpell);
    CHECK_FALSE(result.consumed);
    CHECK_FALSE(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WizardEye)));
    CHECK(result.speechId == OpenYAMM::Game::SpeechId::CantLearnSpell);
}

TEST_CASE("inventory item use spellbook fails without required mastery and preserves the item")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->skills["FireMagic"] = {"FireMagic", 10, OpenYAMM::Game::SkillMastery::Master};
    pMember->forgetSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Incinerate));

    OpenYAMM::Game::InventoryItem spellbook = {};
    spellbook.objectDescriptionId = 410;

    const OpenYAMM::Game::InventoryItemUseResult result = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        spellbook,
        gameData.itemTable,
        &gameData.readableScrollTable);

    REQUIRE(result.handled);
    CHECK(result.action == OpenYAMM::Game::InventoryItemUseAction::LearnSpell);
    CHECK_FALSE(result.consumed);
    CHECK_FALSE(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Incinerate)));
    CHECK(result.speechId == OpenYAMM::Game::SpeechId::CantLearnSpell);
}

TEST_CASE("inventory item use readable scroll returns text without consuming it")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);

    OpenYAMM::Game::InventoryItem readable = {};
    readable.objectDescriptionId = 741;

    const OpenYAMM::Game::InventoryItemUseResult result = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        readable,
        gameData.itemTable,
        &gameData.readableScrollTable);

    REQUIRE(result.handled);
    CHECK(result.action == OpenYAMM::Game::InventoryItemUseAction::ReadMessageScroll);
    CHECK_FALSE(result.consumed);
    CHECK_EQ(result.readableTitle, "Dadeross' Letter to Fellmoon");
    CHECK_FALSE(result.readableBody.empty());
}

TEST_CASE("inventory item use Letter for YOU reads Verdant greeting without consuming it")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);

    OpenYAMM::Game::InventoryItem letter = {};
    letter.objectDescriptionId = 770;

    const OpenYAMM::Game::InventoryItemUseResult result = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        letter,
        gameData.itemTable,
        &gameData.readableScrollTable);

    REQUIRE(result.handled);
    CHECK(result.action == OpenYAMM::Game::InventoryItemUseAction::ReadMessageScroll);
    CHECK_FALSE(result.consumed);
    CHECK_EQ(result.readableTitle, "Letter for YOU.");
    CHECK(result.readableBody.find("Hello, caravaneer") != std::string::npos);
    CHECK_FALSE(result.speechId.has_value());
}

TEST_CASE("inventory item use Deck of Fate applies MMerge month and week reward")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    OpenYAMM::Game::InventoryItem deck = {};
    deck.objectDescriptionId = 2067;

    OpenYAMM::Game::InventoryItemUseContext januaryContext = {};
    januaryContext.gameMinutes = 0.0f;

    const OpenYAMM::Game::InventoryItemUseResult januaryResult =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
            party,
            0,
            deck,
            gameData.itemTable,
            &gameData.readableScrollTable,
            nullptr,
            nullptr,
            januaryContext);

    REQUIRE(januaryResult.handled);
    CHECK(januaryResult.action == OpenYAMM::Game::InventoryItemUseAction::UseDeckOfFate);
    CHECK(januaryResult.consumed);
    CHECK_EQ(januaryResult.statusText, "+1 Might!");
    CHECK_EQ(pMember->permanentBonuses.might, 1);

    OpenYAMM::Game::InventoryItemUseContext decemberContext = {};
    decemberContext.gameMinutes = static_cast<float>(((11 * 28) + (3 * 7)) * 24 * 60);

    const OpenYAMM::Game::InventoryItemUseResult decemberResult =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
            party,
            0,
            deck,
            gameData.itemTable,
            &gameData.readableScrollTable,
            nullptr,
            nullptr,
            decemberContext);

    REQUIRE(decemberResult.handled);
    CHECK(decemberResult.consumed);
    CHECK_EQ(decemberResult.statusText, "+4 Body Resistance!");
    CHECK_EQ(pMember->permanentBonuses.resistances.body, 4);
}

TEST_CASE("inventory item use potions and horseshoe apply the expected effects")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->health = 10;
    pMember->maxSpellPoints = 20;
    pMember->spellPoints = 0;
    pMember->skillPoints = 3;
    pMember->permanentBonuses.intellect = 0;

    OpenYAMM::Game::InventoryItem cureWounds = {};
    cureWounds.objectDescriptionId = 222;
    const OpenYAMM::Game::InventoryItemUseResult healResult = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        cureWounds,
        gameData.itemTable,
        &gameData.readableScrollTable,
        &gameData.mergedPotionSettingTable);

    OpenYAMM::Game::InventoryItem magicPotion = {};
    magicPotion.objectDescriptionId = 223;
    const OpenYAMM::Game::InventoryItemUseResult manaResult = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        magicPotion,
        gameData.itemTable,
        &gameData.readableScrollTable,
        &gameData.mergedPotionSettingTable);

    OpenYAMM::Game::InventoryItem blackPotion = {};
    blackPotion.objectDescriptionId = 266;
    const OpenYAMM::Game::InventoryItemUseResult statResult = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        blackPotion,
        gameData.itemTable,
        &gameData.readableScrollTable,
        &gameData.mergedPotionSettingTable);

    OpenYAMM::Game::InventoryItem horseshoe = {};
    horseshoe.objectDescriptionId = 656;
    const OpenYAMM::Game::InventoryItemUseResult horseshoeResult =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
            party,
            0,
            horseshoe,
            gameData.itemTable,
            &gameData.readableScrollTable);

    CHECK(healResult.consumed);
    CHECK_GT(pMember->health, 10);
    CHECK(manaResult.consumed);
    CHECK_GT(pMember->spellPoints, 0);
    CHECK(statResult.consumed);
    CHECK_EQ(pMember->permanentBonuses.intellect, 50);
    CHECK(horseshoeResult.consumed);
    CHECK_EQ(pMember->skillPoints, 5u);
}

TEST_CASE("a Clover gives the member who uses it one skill point")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::ItemTable itemTable = makeCloverItemTable();
    party.setItemTable(&itemTable);
    OpenYAMM::Game::Character *pMember = party.member(1);
    REQUIRE(pMember != nullptr);
    pMember->skillPoints = 3;
    const uint32_t otherMemberPoints = party.member(0)->skillPoints;

    OpenYAMM::Game::InventoryItem clover = {};
    clover.objectDescriptionId = 10590;
    clover.identified = true;
    CHECK(OpenYAMM::Game::InventoryItemUseRuntime::classifyItemUse(clover, itemTable)
        == OpenYAMM::Game::InventoryItemUseAction::GrantSkillPoints);
    const OpenYAMM::Game::InventoryItemUseResult result =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(party, 1, clover, itemTable, nullptr);

    CHECK(result.handled);
    CHECK(result.consumed);
    CHECK_EQ(result.statusText, "+1 Skill Point!");
    CHECK_EQ(pMember->skillPoints, 4u);
    CHECK_EQ(party.member(0)->skillPoints, otherMemberPoints);
}

TEST_CASE("item generator unique rare item marks party and does not repeat")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(createRegressionPartySeed());

    std::mt19937 rng(1337);
    std::optional<OpenYAMM::Game::InventoryItem> firstRare;

    for (int attempt = 0; attempt < 2000 && !firstRare; ++attempt)
    {
        firstRare = OpenYAMM::Game::ItemGenerator::generateRandomInventoryItem(
            gameData.itemTable,
            gameData.standardItemEnchantTable,
            gameData.specialItemEnchantTable,
            // Ring of Planes is MM8's: artifacts roll only in their own world (World:<id>).
            OpenYAMM::Game::ItemGenerationRequest{6, OpenYAMM::Game::ItemGenerationMode::ChestLoot, true, false, "mm8"},
            &party,
            rng,
            [](const OpenYAMM::Game::ItemDefinition &entry)
            {
                return entry.itemId == 519;
            });
    }

    REQUIRE(firstRare.has_value());
    CHECK_EQ(firstRare->objectDescriptionId, 519u);
    CHECK_EQ(firstRare->artifactId, 519u);
    CHECK(firstRare->rarity == OpenYAMM::Game::ItemRarity::Artifact);
    CHECK(party.hasFoundArtifactItem(519));

    for (int attempt = 0; attempt < 256; ++attempt)
    {
        const std::optional<OpenYAMM::Game::InventoryItem> repeatedRare =
            OpenYAMM::Game::ItemGenerator::generateRandomInventoryItem(
                gameData.itemTable,
                gameData.standardItemEnchantTable,
                gameData.specialItemEnchantTable,
                OpenYAMM::Game::ItemGenerationRequest{6, OpenYAMM::Game::ItemGenerationMode::ChestLoot, true},
                &party,
                rng,
                [](const OpenYAMM::Game::ItemDefinition &entry)
                {
                    return entry.itemId == 519;
                });

        CHECK_FALSE(repeatedRare.has_value());
    }
}

TEST_CASE("equip plan requires the skill and respects the doll type")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};
    character.skills["Sword"] = {"Sword", 1, OpenYAMM::Game::SkillMastery::Normal};

    OpenYAMM::Game::CharacterDollTypeEntry dollType = {};
    dollType.canEquipArmor = true;
    dollType.canEquipHelm = false;
    dollType.canEquipWeapon = true;

    const OpenYAMM::Game::ItemDefinition *pLeatherArmor = gameData.itemTable.get(84);
    const OpenYAMM::Game::ItemDefinition *pHelm = gameData.itemTable.get(109);
    REQUIRE(pLeatherArmor != nullptr);
    REQUIRE(pHelm != nullptr);

    CHECK_FALSE(OpenYAMM::Game::GameMechanics::canCharacterEquipItem(character, *pLeatherArmor, &dollType));

    character.skills["LeatherArmor"] = {"LeatherArmor", 1, OpenYAMM::Game::SkillMastery::Normal};

    CHECK(OpenYAMM::Game::GameMechanics::canCharacterEquipItem(character, *pLeatherArmor, &dollType));
    CHECK_FALSE(OpenYAMM::Game::GameMechanics::canCharacterEquipItem(character, *pHelm, &dollType));
}

TEST_CASE("clubs equip without a learned skill")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};

    OpenYAMM::Game::CharacterDollTypeEntry dollType = {};
    dollType.canEquipArmor = true;
    dollType.canEquipHelm = true;
    dollType.canEquipWeapon = true;

    for (const uint32_t clubItemId : {76u, 860u, 1660u})
    {
        CAPTURE(clubItemId);
        const OpenYAMM::Game::ItemDefinition *pClub = gameData.itemTable.get(clubItemId);
        REQUIRE(pClub != nullptr);

        CHECK(OpenYAMM::Game::GameMechanics::canCharacterEquipItem(character, *pClub, &dollType));

        const std::optional<OpenYAMM::Game::CharacterEquipPlan> plan =
            OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
                character,
                *pClub,
                &gameData.itemTable,
                &dollType,
                std::nullopt,
                false);
        REQUIRE(plan.has_value());
        CHECK(plan->targetSlot == OpenYAMM::Game::EquipmentSlot::MainHand);
    }
}

TEST_CASE("negative accuracy does not block items without a stat requirement")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    // A low-accuracy Sorcerer wielding the Lightning Crossbow (Accuracy -50), GitHub issue #14.
    OpenYAMM::Game::Character character = {};
    character.accuracy = 10;
    character.magicalBonuses.accuracy = -50;

    OpenYAMM::Game::CharacterDollTypeEntry dollType = {};
    dollType.canEquipCloak = true;

    for (const uint32_t itemId : {137u, 122u})
    {
        CAPTURE(itemId);
        const OpenYAMM::Game::ItemDefinition *pItem = gameData.itemTable.get(itemId);
        REQUIRE(pItem != nullptr);
        CHECK(OpenYAMM::Game::GameMechanics::canCharacterEquipItem(character, *pItem, &dollType));
    }
}

TEST_CASE("wetsuit equip rules require empty equipment except blasters")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ItemDefinition *pWetsuit = gameData.itemTable.get(1406);
    const OpenYAMM::Game::ItemDefinition *pMm7Blaster = gameData.itemTable.get(866);
    const OpenYAMM::Game::ItemDefinition *pMm6BlasterRifle = gameData.itemTable.get(1667);
    const OpenYAMM::Game::ItemDefinition *pRing = gameData.itemTable.get(138);
    REQUIRE(pWetsuit != nullptr);
    REQUIRE(pMm7Blaster != nullptr);
    REQUIRE(pMm6BlasterRifle != nullptr);
    REQUIRE(pRing != nullptr);

    OpenYAMM::Game::Character character = {};
    character.skills["Blaster"] = {"Blaster", 1, OpenYAMM::Game::SkillMastery::Normal};

    std::optional<OpenYAMM::Game::CharacterEquipPlan> plan =
        OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
            character,
            *pWetsuit,
            &gameData.itemTable,
            nullptr,
            std::nullopt,
            false);
    REQUIRE(plan.has_value());
    CHECK(plan->targetSlot == OpenYAMM::Game::EquipmentSlot::Armor);

    character.equipment.ring1 = pRing->itemId;
    CHECK_FALSE(OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        character,
        *pWetsuit,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false));

    character.equipment = {};
    character.equipment.mainHand = pMm7Blaster->itemId;
    CHECK(OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        character,
        *pWetsuit,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false));

    character.equipment = {};
    character.equipment.armor = pWetsuit->itemId;
    CHECK_FALSE(OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        character,
        *pRing,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false));
    CHECK(OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        character,
        *pMm6BlasterRifle,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false));

    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->equipment = {};
    pMember->equipment.armor = pWetsuit->itemId;
    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;
    CHECK_FALSE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::Ring1,
        OpenYAMM::Game::ItemGenerator::makeInventoryItem(
            pRing->itemId,
            gameData.itemTable,
            OpenYAMM::Game::ItemGenerationMode::ChestLoot),
        std::nullopt,
        false,
        heldReplacement));
    CHECK_EQ(party.lastStatus(), "cannot equip");
}

TEST_CASE("blaster shotgun fans seven half-strength bolts with slower recovery than the blaster rifle")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ItemDefinition *pBlasterRifle = gameData.itemTable.get(1667);
    const OpenYAMM::Game::ItemDefinition *pBlasterShotgun = gameData.itemTable.get(2201);
    REQUIRE(pBlasterRifle != nullptr);
    REQUIRE(pBlasterShotgun != nullptr);
    CHECK(pBlasterShotgun->hasContentFlag("ScatterBlaster"));

    OpenYAMM::Game::Character character = {};
    character.skills["Blaster"] = {"Blaster", 1, OpenYAMM::Game::SkillMastery::Normal};
    character.equipment.mainHand = pBlasterRifle->itemId;
    const OpenYAMM::Game::CharacterAttackProfile rifle =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(character, &gameData.itemTable, nullptr);
    character.equipment.mainHand = pBlasterShotgun->itemId;
    const OpenYAMM::Game::CharacterAttackProfile shotgun =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(character, &gameData.itemTable, nullptr);

    REQUIRE(rifle.hasBlaster);
    REQUIRE(shotgun.hasBlaster);
    CHECK_EQ(rifle.rangedProjectileCount, 1);
    CHECK_EQ(rifle.rangedSpreadArcRadians, 0.0f);
    CHECK_EQ(shotgun.rangedProjectileCount, 7);
    CHECK(shotgun.rangedSpreadArcRadians > 0.0f);
    CHECK_EQ(shotgun.rangedMinDamage + shotgun.rangedMaxDamage,
        doctest::Approx((rifle.rangedMinDamage + rifle.rangedMaxDamage) / 2.0).epsilon(0.05));
    CHECK(shotgun.rangedRecoverySeconds > rifle.rangedRecoverySeconds);
}

TEST_CASE("projectile fans spread evenly across the arc around the aim")
{
    using OpenYAMM::Game::GameMechanics;
    CHECK_EQ(GameMechanics::projectileFanYawOffsetRadians(1, 0, 1.2f), 0.0f);
    CHECK_EQ(GameMechanics::projectileFanYawOffsetRadians(7, 0, 1.2f), doctest::Approx(-0.6f));
    CHECK_EQ(GameMechanics::projectileFanYawOffsetRadians(7, 3, 1.2f), doctest::Approx(0.0f));
    CHECK_EQ(GameMechanics::projectileFanYawOffsetRadians(7, 6, 1.2f), doctest::Approx(0.6f));
    CHECK_EQ(GameMechanics::projectileFanYawOffsetRadians(7, 1, 1.2f), doctest::Approx(-0.4f));
}

TEST_CASE("party rejects a race restricted artifact for the wrong member")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->equipment = {};
    pMember->className = "Knight";
    pMember->raceId = 0;
    OpenYAMM::Game::InventoryItem glomenmail =
        OpenYAMM::Game::ItemGenerator::makeInventoryItem(
            514,
            gameData.itemTable,
            OpenYAMM::Game::ItemGenerationMode::ChestLoot);
    glomenmail.identified = true;
    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;

    CHECK_FALSE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::Armor,
        glomenmail,
        std::nullopt,
        false,
        heldReplacement));
    CHECK_EQ(party.lastStatus(), "Dark Elves only");

    pMember->raceId = 2;

    REQUIRE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::Armor,
        glomenmail,
        std::nullopt,
        false,
        heldReplacement));
    CHECK_EQ(pMember->equipment.armor, 514u);
}

TEST_CASE("forge gauntlets require a dwarf race member")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ItemDefinition *pForgeGauntlets = gameData.itemTable.get(1336);
    REQUIRE(pForgeGauntlets != nullptr);
    CHECK_EQ(pForgeGauntlets->name, "Forge Gauntlets");

    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    OpenYAMM::Game::InventoryItem forgeGauntlets =
        OpenYAMM::Game::ItemGenerator::makeInventoryItem(
            1336,
            gameData.itemTable,
            OpenYAMM::Game::ItemGenerationMode::ChestLoot);
    forgeGauntlets.identified = true;
    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;

    pMember->equipment = {};
    pMember->className = "Knight";
    pMember->raceId = 0;
    CHECK_FALSE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::Gauntlets,
        forgeGauntlets,
        std::nullopt,
        false,
        heldReplacement));
    CHECK_EQ(party.lastStatus(), "Dwarves only");

    pMember->raceId = 9;
    REQUIRE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::Gauntlets,
        forgeGauntlets,
        std::nullopt,
        false,
        heldReplacement));
    CHECK_EQ(pMember->equipment.gauntlets, 1336u);
}

TEST_CASE("equip rules respect class restricted artifacts")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ItemDefinition *pCrown = gameData.itemTable.get(521);
    REQUIRE(pCrown != nullptr);

    OpenYAMM::Game::CharacterDollTypeEntry dollType = {};
    dollType.canEquipHelm = true;

    OpenYAMM::Game::Character necromancer = {};
    necromancer.className = "Necromancer";
    CHECK_FALSE(OpenYAMM::Game::GameMechanics::canCharacterEquipItem(necromancer, *pCrown, &dollType));

    OpenYAMM::Game::Character lich = {};
    lich.className = "Lich";
    CHECK(OpenYAMM::Game::GameMechanics::canCharacterEquipItem(lich, *pCrown, &dollType));
}

TEST_CASE("a refused gated artifact says who may wear it")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ItemDefinition *pSupremePlate = gameData.itemTable.get(515);
    REQUIRE(pSupremePlate != nullptr);

    OpenYAMM::Game::CharacterDollTypeEntry dollType = {};
    dollType.canEquipArmor = true;

    OpenYAMM::Game::Character paladin = {};
    paladin.className = "Paladin";
    CHECK(OpenYAMM::Game::GameMechanics::equipRefusalReason(paladin, *pSupremePlate, &dollType)
        == "Requires the Plate Armor skill");

    paladin.skills["PlateArmor"] = {"PlateArmor", 1, OpenYAMM::Game::SkillMastery::Normal};
    CHECK(OpenYAMM::Game::GameMechanics::equipRefusalReason(paladin, *pSupremePlate, &dollType) == "Knights only");

    OpenYAMM::Game::Character champion = paladin;
    champion.className = "Champion";
    CHECK(OpenYAMM::Game::GameMechanics::canCharacterEquipItem(champion, *pSupremePlate, &dollType));
    CHECK_FALSE(OpenYAMM::Game::GameMechanics::equipRefusalReason(champion, *pSupremePlate, &dollType).has_value());
}

TEST_CASE("artifact ring of planes applies resistance bonuses")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->equipment = {};
    pMember->equipmentRuntime = {};
    pMember->magicalBonuses = {};

    OpenYAMM::Game::InventoryItem ringOfPlanes =
        OpenYAMM::Game::ItemGenerator::makeInventoryItem(
            519,
            gameData.itemTable,
            OpenYAMM::Game::ItemGenerationMode::ChestLoot);
    ringOfPlanes.identified = true;
    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;

    REQUIRE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::Ring1,
        ringOfPlanes,
        std::nullopt,
        false,
        heldReplacement));

    CHECK_EQ(pMember->magicalBonuses.resistances.fire, 40);
    CHECK_EQ(pMember->magicalBonuses.resistances.air, 40);
    CHECK_EQ(pMember->magicalBonuses.resistances.water, 40);
    CHECK_EQ(pMember->magicalBonuses.resistances.earth, 40);
    CHECK(party.hasFoundArtifactItem(519));
}

TEST_CASE("artifact shield blocks condition application")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->equipment = {};
    pMember->equipmentRuntime = {};
    pMember->conditions = {};

    OpenYAMM::Game::InventoryItem shield =
        OpenYAMM::Game::ItemGenerator::makeInventoryItem(
            534,
            gameData.itemTable,
            OpenYAMM::Game::ItemGenerationMode::ChestLoot);
    shield.identified = true;
    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;

    REQUIRE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::OffHand,
        shield,
        std::nullopt,
        false,
        heldReplacement));

    const std::array<OpenYAMM::Game::CharacterCondition, 4> conditions = {{
        OpenYAMM::Game::CharacterCondition::Fear,
        OpenYAMM::Game::CharacterCondition::Petrified,
        OpenYAMM::Game::CharacterCondition::Paralyzed,
        OpenYAMM::Game::CharacterCondition::Asleep,
    }};

    for (OpenYAMM::Game::CharacterCondition condition : conditions)
    {
        CHECK(party.hasMemberConditionImmunity(0, condition));
        CHECK_FALSE(party.applyMemberCondition(0, condition));
        CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(condition)));
    }
}

TEST_CASE("special antidotes enchant blocks poison application")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const std::optional<uint16_t> antidotesEnchantId =
        findSpecialEnchantId(gameData.specialItemEnchantTable, OpenYAMM::Game::SpecialItemEnchantKind::Antidotes);
    const OpenYAMM::Game::ItemDefinition *pRingDefinition = gameData.itemTable.get(137);
    REQUIRE(antidotesEnchantId.has_value());
    REQUIRE(pRingDefinition != nullptr);

    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->equipment = {};
    pMember->equipmentRuntime = {};
    pMember->conditions = {};

    OpenYAMM::Game::InventoryItem ring =
        OpenYAMM::Game::ItemGenerator::makeInventoryItem(
            pRingDefinition->itemId,
            gameData.itemTable,
            OpenYAMM::Game::ItemGenerationMode::ChestLoot);
    ring.identified = true;
    ring.specialEnchantId = *antidotesEnchantId;
    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;

    REQUIRE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::Ring1,
        ring,
        std::nullopt,
        false,
        heldReplacement));

    const std::array<OpenYAMM::Game::CharacterCondition, 3> conditions = {{
        OpenYAMM::Game::CharacterCondition::PoisonWeak,
        OpenYAMM::Game::CharacterCondition::PoisonMedium,
        OpenYAMM::Game::CharacterCondition::PoisonSevere,
    }};

    for (OpenYAMM::Game::CharacterCondition condition : conditions)
    {
        CHECK(party.hasMemberConditionImmunity(0, condition));
        CHECK_FALSE(party.applyMemberCondition(0, condition));
        CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(condition)));
    }
}

TEST_CASE("rare and special slaying damage multipliers match the target family")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const std::optional<uint16_t> dragonSlayingEnchantId =
        findSpecialEnchantId(gameData.specialItemEnchantTable, OpenYAMM::Game::SpecialItemEnchantKind::DragonSlaying);
    const std::optional<uint16_t> davidEnchantId =
        findSpecialEnchantId(gameData.specialItemEnchantTable, OpenYAMM::Game::SpecialItemEnchantKind::David);
    const OpenYAMM::Game::ItemDefinition *pBowDefinition = gameData.itemTable.get(56);
    REQUIRE(dragonSlayingEnchantId.has_value());
    REQUIRE(davidEnchantId.has_value());
    REQUIRE(pBowDefinition != nullptr);

    OpenYAMM::Game::Character meleeCharacter = {};
    meleeCharacter.equipment.mainHand = 503;
    meleeCharacter.equipmentRuntime.mainHand.artifactId = 503;
    meleeCharacter.equipmentRuntime.mainHand.rarity = OpenYAMM::Game::ItemRarity::Artifact;

    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            meleeCharacter,
            OpenYAMM::Game::CharacterAttackMode::Melee,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable,
            OpenYAMM::Game::monsterKindFlag(OpenYAMM::Game::MonsterKind::Ogre)),
        2);
    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            meleeCharacter,
            OpenYAMM::Game::CharacterAttackMode::Melee,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable),
        1);

    OpenYAMM::Game::Character rangedCharacter = {};
    rangedCharacter.equipment.bow = pBowDefinition->itemId;
    rangedCharacter.equipmentRuntime.bow.specialEnchantId = *dragonSlayingEnchantId;

    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            rangedCharacter,
            OpenYAMM::Game::CharacterAttackMode::Bow,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable,
            OpenYAMM::Game::monsterKindFlag(OpenYAMM::Game::MonsterKind::Dragon)),
        2);
    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            rangedCharacter,
            OpenYAMM::Game::CharacterAttackMode::Bow,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable,
            OpenYAMM::Game::monsterKindFlag(OpenYAMM::Game::MonsterKind::Dragon)),
        2);
    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            rangedCharacter,
            OpenYAMM::Game::CharacterAttackMode::Bow,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable),
        1);

    rangedCharacter.equipmentRuntime.bow.specialEnchantId = *davidEnchantId;

    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            rangedCharacter,
            OpenYAMM::Game::CharacterAttackMode::Bow,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable,
            OpenYAMM::Game::monsterKindFlag(OpenYAMM::Game::MonsterKind::Titan)),
        2);
}

TEST_CASE("weapon elemental damage keeps its resistance type")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const std::optional<uint16_t> flameEnchantId =
        findSpecialEnchantId(gameData.specialItemEnchantTable, OpenYAMM::Game::SpecialItemEnchantKind::Flame);
    REQUIRE(flameEnchantId.has_value());

    OpenYAMM::Game::Character character = {};
    character.equipment.mainHand = 1;
    character.equipmentRuntime.mainHand.specialEnchantId = *flameEnchantId;

    const OpenYAMM::Game::ElementalDamageRange range =
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackElementalDamageRange(
            character,
            OpenYAMM::Game::CharacterAttackMode::Melee,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable);

    CHECK_EQ(range.minimum.fire, 2);
    CHECK_EQ(range.maximum.fire, 12);
    CHECK_EQ(range.maximum.total(), 12);
}

TEST_CASE("Hades adds poison damage without turning the whole hit into body damage")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character character = {};
    character.equipment.mainHand = 2035;

    const OpenYAMM::Game::ElementalDamageBonuses damage =
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackElementalDamageRange(
            character,
            OpenYAMM::Game::CharacterAttackMode::Melee,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable).maximum;
    CHECK_EQ(damage.body, 20);
    CHECK_EQ(damage.total(), 20);

    // Against a body-immune dragon (physical and fire 90) a 500 point blow keeps its physical part: only the body
    // component is lost. Before the fix the whole blow was body damage and dealt nothing.
    OpenYAMM::Game::MonsterDamageResistances dragon = {};
    dragon.fire = 90;
    dragon.physical = 90;
    dragon.body = 200;
    int total = 0;
    for (uint32_t seed = 1; seed <= 64; ++seed)
    {
        std::mt19937 rng(seed);
        total += OpenYAMM::Game::GameMechanics::resolveMonsterIncomingWeaponDamage(
            500,
            OpenYAMM::Game::CombatDamageType::Physical,
            damage,
            dragon,
            0,
            rng);
    }
    CHECK(total / 64 > 100);
}

TEST_CASE("merged MM7 artifacts and relics apply their MMerge passive effects")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    SUBCASE("Mind's Eye grants both casting stats and spell regeneration")
    {
        OpenYAMM::Game::Character character = {};
        applyMergedRareItemEffects(gameData, 1334, character);
        CHECK_EQ(character.magicalBonuses.intellect, 15);
        CHECK_EQ(character.magicalBonuses.personality, 15);
        CHECK_EQ(character.spellRegenPerSecond, doctest::Approx(1.0f));
    }

    SUBCASE("Scholar's Cap and Hands of the Master grant skill bonuses")
    {
        OpenYAMM::Game::Character character = {};
        applyMergedRareItemEffects(gameData, 1324, character);
        applyMergedRareItemEffects(gameData, 1313, character);
        CHECK_EQ(character.magicalBonuses.endurance, -50);
        CHECK_EQ(character.itemSkillBonuses["Learning"], 15);
        CHECK_EQ(character.itemSkillBonuses["Unarmed"], 10);
        CHECK_EQ(character.itemSkillBonuses["Dodging"], 10);
    }

    SUBCASE("Yoruba grants the MMerge condition immunity set")
    {
        OpenYAMM::Game::Character character = {};
        applyMergedRareItemEffects(gameData, 1307, character);
        CHECK_EQ(character.magicalBonuses.endurance, 25);
        CHECK(character.magicalConditionImmunities.test(
            static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Insane)));
        CHECK(character.magicalConditionImmunities.test(
            static_cast<size_t>(OpenYAMM::Game::CharacterCondition::PoisonSevere)));
        CHECK(character.magicalConditionImmunities.test(
            static_cast<size_t>(OpenYAMM::Game::CharacterCondition::DiseaseSevere)));
        CHECK(character.magicalConditionImmunities.test(
            static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Petrified)));
    }

    SUBCASE("Gibbet grants its flat weapon damage bonus")
    {
        OpenYAMM::Game::Character character = {};
        applyMergedRareItemEffects(gameData, 1310, character);
        CHECK_EQ(character.meleeWeaponDamageBonus, 15);
        CHECK_EQ(character.rangedWeaponDamageBonus, 0);
    }

    SUBCASE("Ethric's Staff drains living wielders but not liches")
    {
        OpenYAMM::Game::Character livingCharacter = {};
        livingCharacter.className = "Sorcerer";
        livingCharacter.skills["DarkMagic"] = {"DarkMagic", 8, OpenYAMM::Game::SkillMastery::Master};
        applyMergedRareItemEffects(gameData, 1317, livingCharacter);
        CHECK_EQ(livingCharacter.itemSkillBonuses["DarkMagic"], 4);
        CHECK_EQ(livingCharacter.itemSkillBonuses["Meditation"], 15);
        CHECK_EQ(livingCharacter.healthRegenPerSecond, doctest::Approx(-1.0f));

        OpenYAMM::Game::Character lich = livingCharacter;
        lich.className = "Lich";
        lich.itemSkillBonuses.clear();
        lich.healthRegenPerSecond = 0.0f;
        applyMergedRareItemEffects(gameData, 1317, lich);
        CHECK_EQ(lich.healthRegenPerSecond, doctest::Approx(0.0f));
    }
}

TEST_CASE("merged MM6 artifacts and relics apply their MMerge passive effects")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    SUBCASE("Arthur grants all primary stats and spell points")
    {
        OpenYAMM::Game::Character character = {};
        applyMergedRareItemEffects(gameData, 2029, character);
        CHECK_EQ(character.magicalBonuses.might, 10);
        CHECK_EQ(character.magicalBonuses.intellect, 10);
        CHECK_EQ(character.magicalBonuses.personality, 10);
        CHECK_EQ(character.magicalBonuses.endurance, 10);
        CHECK_EQ(character.magicalBonuses.speed, 10);
        CHECK_EQ(character.magicalBonuses.accuracy, 10);
        CHECK_EQ(character.magicalBonuses.luck, 10);
        CHECK_EQ(character.magicalBonuses.maxSpellPoints, 25);
    }

    SUBCASE("Aegis grants shielding, luck, petrification immunity, and its speed penalty")
    {
        OpenYAMM::Game::Character character = {};
        applyMergedRareItemEffects(gameData, 2043, character);
        CHECK(character.halfMissileDamage);
        CHECK_EQ(character.magicalBonuses.luck, 20);
        CHECK_EQ(character.magicalBonuses.speed, -20);
        CHECK(character.magicalConditionImmunities.test(
            static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Petrified)));
    }

    SUBCASE("Hades grants poison damage, disarm, luck, and negative regeneration")
    {
        OpenYAMM::Game::Party party = makeRegressionParty(gameData);
        OpenYAMM::Game::Character *pCharacter = party.member(0);
        REQUIRE(pCharacter != nullptr);
        applyMergedRareItemEffects(gameData, 2035, *pCharacter);
        CHECK_EQ(pCharacter->magicalBonuses.luck, 20);
        CHECK_EQ(pCharacter->itemSkillBonuses["DisarmTraps"], 10);
        // The +20 is a separate body component rolled with each blow (rareItemElementalDamageBonuses), not a flat
        // bonus; the sword's own hit stays physical.
        CHECK_EQ(pCharacter->meleeWeaponDamageBonus, 0);
        CHECK_EQ(pCharacter->healthRegenPerSecond, doctest::Approx(-1.0f));
        CHECK_FALSE(pCharacter->equippedItemEffectFlags.contains("PoisonWeaponDamage"));

        pCharacter->health = 20;
        party.updateRecovery(2.0f);
        CHECK_EQ(pCharacter->health, 18);
    }
}

TEST_CASE("merged rare slaying recognizes MMerge demon and elf families")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character character = {};
    character.equipment.mainHand = 1310;
    character.equipmentRuntime.mainHand.artifactId = 1310;
    character.equipmentRuntime.mainHand.rarity = OpenYAMM::Game::ItemRarity::Artifact;

    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            character,
            OpenYAMM::Game::CharacterAttackMode::Melee,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable,
            OpenYAMM::Game::monsterKindFlag(OpenYAMM::Game::MonsterKind::Demon)),
        2);

    character.equipment.mainHand = 1333;
    character.equipmentRuntime.mainHand.artifactId = 1333;
    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            character,
            OpenYAMM::Game::CharacterAttackMode::Melee,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable,
            OpenYAMM::Game::monsterKindFlag(OpenYAMM::Game::MonsterKind::Elf)),
        2);
}

TEST_CASE("MMerge gender-restricted artifacts enforce their wearer sex")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ItemDefinition *pHeroBelt = gameData.itemTable.get(1337);
    const OpenYAMM::Game::ItemDefinition *pLadyEscort = gameData.itemTable.get(1338);
    REQUIRE(pHeroBelt != nullptr);
    REQUIRE(pLadyEscort != nullptr);

    OpenYAMM::Game::Character character = {};
    character.sexId = 0;
    CHECK(OpenYAMM::Game::ItemRuntime::characterMeetsRaceRestriction(character, *pHeroBelt));
    CHECK_FALSE(OpenYAMM::Game::ItemRuntime::characterMeetsRaceRestriction(character, *pLadyEscort));

    character.sexId = 1;
    CHECK_FALSE(OpenYAMM::Game::ItemRuntime::characterMeetsRaceRestriction(character, *pHeroBelt));
    CHECK(OpenYAMM::Game::ItemRuntime::characterMeetsRaceRestriction(character, *pLadyEscort));
}

TEST_CASE("ring auto equip uses the first free slot then replaces the first ring")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->equipment = {};
    const OpenYAMM::Game::ItemDefinition *pFirstRing = gameData.itemTable.get(137);
    const OpenYAMM::Game::ItemDefinition *pReplacementRing = gameData.itemTable.get(143);
    REQUIRE(pFirstRing != nullptr);
    REQUIRE(pReplacementRing != nullptr);

    std::optional<OpenYAMM::Game::CharacterEquipPlan> plan = OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        *pMember,
        *pFirstRing,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false);

    REQUIRE(plan.has_value());
    CHECK(plan->targetSlot == OpenYAMM::Game::EquipmentSlot::Ring1);
    CHECK_FALSE(plan->displacedSlot.has_value());

    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;
    OpenYAMM::Game::InventoryItem heldRing = {
        pFirstRing->itemId,
        1,
        pFirstRing->inventoryWidth,
        pFirstRing->inventoryHeight,
        0,
        0
    };

    REQUIRE(party.tryEquipItemOnMember(
        0,
        plan->targetSlot,
        heldRing,
        plan->displacedSlot,
        plan->autoStoreDisplacedItem,
        heldReplacement));

    pMember->equipment.ring2 = 138;
    pMember->equipment.ring3 = 139;
    pMember->equipment.ring4 = 140;
    pMember->equipment.ring5 = 141;
    pMember->equipment.ring6 = 142;

    plan = OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        *pMember,
        *pReplacementRing,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false);

    REQUIRE(plan.has_value());
    CHECK(plan->targetSlot == OpenYAMM::Game::EquipmentSlot::Ring1);
    CHECK(plan->displacedSlot == OpenYAMM::Game::EquipmentSlot::Ring1);

    heldRing = {
        pReplacementRing->itemId,
        1,
        pReplacementRing->inventoryWidth,
        pReplacementRing->inventoryHeight,
        0,
        0
    };
    heldReplacement.reset();

    REQUIRE(party.tryEquipItemOnMember(
        0,
        plan->targetSlot,
        heldRing,
        plan->displacedSlot,
        plan->autoStoreDisplacedItem,
        heldReplacement));

    CHECK_EQ(pMember->equipment.ring1, pReplacementRing->itemId);
    REQUIRE(heldReplacement.has_value());
    CHECK_EQ(heldReplacement->objectDescriptionId, pFirstRing->itemId);
}

TEST_CASE("amulet replacement keeps the displaced item held")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->equipment = {};
    pMember->inventory.clear();
    pMember->equipment.amulet = 147;
    const OpenYAMM::Game::ItemDefinition *pNewAmulet = gameData.itemTable.get(148);
    REQUIRE(pNewAmulet != nullptr);

    const std::optional<OpenYAMM::Game::CharacterEquipPlan> plan =
        OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
            *pMember,
            *pNewAmulet,
            &gameData.itemTable,
            nullptr,
            std::nullopt,
            false);

    REQUIRE(plan.has_value());
    CHECK_FALSE(plan->autoStoreDisplacedItem);
    CHECK(plan->displacedSlot == OpenYAMM::Game::EquipmentSlot::Amulet);

    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;
    const OpenYAMM::Game::InventoryItem heldAmulet = {
        pNewAmulet->itemId,
        1,
        pNewAmulet->inventoryWidth,
        pNewAmulet->inventoryHeight,
        0,
        0
    };

    REQUIRE(party.tryEquipItemOnMember(
        0,
        plan->targetSlot,
        heldAmulet,
        plan->displacedSlot,
        plan->autoStoreDisplacedItem,
        heldReplacement));

    REQUIRE(heldReplacement.has_value());
    CHECK_EQ(heldReplacement->objectDescriptionId, 147u);
    CHECK_EQ(pMember->equipment.amulet, pNewAmulet->itemId);
}

TEST_CASE("explicit ring slot replaces the selected ring even with free slots")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->equipment = {};
    pMember->equipment.ring3 = 139;

    const OpenYAMM::Game::ItemDefinition *pReplacementRing = gameData.itemTable.get(145);
    REQUIRE(pReplacementRing != nullptr);

    const std::optional<OpenYAMM::Game::CharacterEquipPlan> plan =
        OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
            *pMember,
            *pReplacementRing,
            &gameData.itemTable,
            nullptr,
            OpenYAMM::Game::EquipmentSlot::Ring3,
            false);

    REQUIRE(plan.has_value());
    CHECK(plan->targetSlot == OpenYAMM::Game::EquipmentSlot::Ring3);
    CHECK(plan->displacedSlot == OpenYAMM::Game::EquipmentSlot::Ring3);

    const OpenYAMM::Game::InventoryItem heldRing = {
        pReplacementRing->itemId,
        1,
        pReplacementRing->inventoryWidth,
        pReplacementRing->inventoryHeight,
        0,
        0
    };
    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;

    REQUIRE(party.tryEquipItemOnMember(
        0,
        plan->targetSlot,
        heldRing,
        plan->displacedSlot,
        plan->autoStoreDisplacedItem,
        heldReplacement));

    CHECK_EQ(pMember->equipment.ring3, pReplacementRing->itemId);
    REQUIRE(heldReplacement.has_value());
    CHECK_EQ(heldReplacement->objectDescriptionId, 139u);
    CHECK_EQ(pMember->equipment.ring1, 0u);
    CHECK_EQ(pMember->equipment.ring2, 0u);
    CHECK_EQ(pMember->equipment.ring4, 0u);
    CHECK_EQ(pMember->equipment.ring5, 0u);
    CHECK_EQ(pMember->equipment.ring6, 0u);
}

TEST_CASE("weapon conflict rules match the expected cases")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ItemDefinition *pShield = gameData.itemTable.get(104);
    const OpenYAMM::Game::ItemDefinition *pSpear = gameData.itemTable.get(52);
    const OpenYAMM::Game::ItemDefinition *pTwoHandedSword = gameData.itemTable.get(6);
    REQUIRE(pShield != nullptr);
    REQUIRE(pSpear != nullptr);
    REQUIRE(pTwoHandedSword != nullptr);

    OpenYAMM::Game::Character character = {};
    character.skills["Shield"] = {"Shield", 1, OpenYAMM::Game::SkillMastery::Normal};
    character.skills["Spear"] = {"Spear", 1, OpenYAMM::Game::SkillMastery::Normal};
    character.skills["Sword"] = {"Sword", 1, OpenYAMM::Game::SkillMastery::Normal};
    character.equipment.mainHand = pSpear->itemId;

    CHECK_FALSE(OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        character,
        *pShield,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false));

    character.skills["Spear"].mastery = OpenYAMM::Game::SkillMastery::Master;

    std::optional<OpenYAMM::Game::CharacterEquipPlan> plan = OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        character,
        *pShield,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false);

    REQUIRE(plan.has_value());
    CHECK(plan->targetSlot == OpenYAMM::Game::EquipmentSlot::OffHand);

    character.equipment = {};
    character.equipment.mainHand = pTwoHandedSword->itemId;

    plan = OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        character,
        *pShield,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false);

    REQUIRE(plan.has_value());
    CHECK(plan->displacedSlot == OpenYAMM::Game::EquipmentSlot::MainHand);

    character.equipment.mainHand = 1;
    character.equipment.offHand = 104;

    CHECK_FALSE(OpenYAMM::Game::GameMechanics::resolveCharacterEquipPlan(
        character,
        *pTwoHandedSword,
        &gameData.itemTable,
        nullptr,
        std::nullopt,
        false));
}

TEST_CASE("special items carry the enchantment their item row names (OY-553)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const OpenYAMM::Game::ItemDefinition *pBow = gameData.itemTable.get(542);
    REQUIRE(pBow != nullptr);
    const OpenYAMM::Game::SpecialItemEnchantEntry *pCarnage =
        gameData.specialItemEnchantTable.get(pBow->specialItemSpecialEnchantId);
    REQUIRE(pCarnage != nullptr);
    CHECK(pCarnage->kind == OpenYAMM::Game::SpecialItemEnchantKind::Carnage);

    // A Noblebone Bow is made with Carnage, keeps its own name and shoots explosive arrows.
    OpenYAMM::Game::InventoryItem bow = OpenYAMM::Game::ItemGenerator::makeInventoryItem(
        542, gameData.itemTable, OpenYAMM::Game::ItemGenerationMode::Generic);
    CHECK(bow.specialEnchantId == pBow->specialItemSpecialEnchantId);
    CHECK(OpenYAMM::Game::ItemRuntime::identifiedDisplayName(
              bow, *pBow, &gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable)
        == "Noblebone Bow");

    OpenYAMM::Game::EquippedItemRuntimeState worn = {};
    worn.specialEnchantId = bow.specialEnchantId;
    worn.artifactId = bow.artifactId;
    OpenYAMM::Game::Character archer = {};
    OpenYAMM::Game::ItemEnchantRuntime::applyEquippedEnchantEffects(
        *pBow, worn, &gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable, archer);
    CHECK(archer.equippedItemEffectFlags.contains("ExplosiveArrows"));

    // A standard enchantment comes at its row's power: Minotaur's Axe "of Might" 25.
    const OpenYAMM::Game::InventoryItem axe = OpenYAMM::Game::ItemGenerator::makeInventoryItem(
        1353, gameData.itemTable, OpenYAMM::Game::ItemGenerationMode::Generic);
    const OpenYAMM::Game::StandardItemEnchantEntry *pMight =
        gameData.standardItemEnchantTable.get(axe.standardEnchantId);
    REQUIRE(pMight != nullptr);
    CHECK(pMight->kind == OpenYAMM::Game::StandardItemEnchantKind::Might);
    CHECK(axe.standardEnchantPower == 25);

    // Every Special item's name resolves except Grognard's Cutlass, whose Elf Slaying is an artifact power.
    OpenYAMM::Game::ItemTable itemTable = gameData.itemTable;
    CHECK(itemTable.resolveSpecialItemEnchants(gameData.standardItemEnchantTable, gameData.specialItemEnchantTable)
        == std::vector<uint32_t>{1354});

    // A save from before carries the bow without its enchantment, in a bag and worn; loading gives it back.
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    OpenYAMM::Game::InventoryItem oldBow = bow;
    oldBow.specialEnchantId = 0;
    pMember->rulesetState.storedBags[1].push_back(oldBow);
    pMember->equipment.bow = 542;
    pMember->equipmentRuntime.bow = {};
    party.assignSpecialItemEnchants();
    CHECK(pMember->rulesetState.storedBags[1].back().specialEnchantId == pBow->specialItemSpecialEnchantId);
    CHECK(pMember->equipmentRuntime.bow.specialEnchantId == pBow->specialItemSpecialEnchantId);
}

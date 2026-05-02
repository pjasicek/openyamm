#include "doctest/doctest.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/JournalQuestRuntime.h"
#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/JournalQuestTable.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <array>
#include <filesystem>
#include <optional>

namespace
{
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

OpenYAMM::Game::InventoryItem makeInventoryItem(uint32_t objectDescriptionId, uint8_t width, uint8_t height)
{
    OpenYAMM::Game::InventoryItem item = {};
    item.objectDescriptionId = objectDescriptionId;
    item.quantity = 1;
    item.width = width;
    item.height = height;
    item.identified = true;
    return item;
}

OpenYAMM::Game::Party makeInventoryParty()
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        OpenYAMM::Game::Character *pMember = party.member(memberIndex);

        if (pMember != nullptr)
        {
            pMember->inventory.clear();
        }
    }

    return party;
}
}

TEST_CASE("default party seed only creates the first test member")
{
    OpenYAMM::Game::Party party = {};
    party.reset();

    const std::vector<OpenYAMM::Game::Character> &members = party.members();

    REQUIRE_EQ(members.size(), 1u);
    CHECK_EQ(members[0].name, "Ariel");
    CHECK_EQ(members[0].portraitPictureId, 2u);
    CHECK_EQ(members[0].characterDataId, 3u);
}

TEST_CASE("current quest journal entries come from party qbits and non-empty quest text")
{
    OpenYAMM::Game::JournalQuestTable questTable = {};
    REQUIRE(questTable.loadFromRows({
        {"1", "Recover the crystal.", "Shown while active.", "test"},
        {"2", "Find the hidden port.", "Not active.", "test"},
        {"3", "", "Internal completion bit.", "test"},
    }));

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    party.setQuestBit(1, true);
    party.setQuestBit(3, true);
    party.setQuestBit(999, true);

    const std::vector<std::string> questTexts =
        OpenYAMM::Game::buildCurrentQuestTexts(questTable, party);

    REQUIRE_EQ(questTexts.size(), 1u);
    CHECK_EQ(questTexts[0], "Recover the crystal.");
}

TEST_CASE("journal quest table rejects malformed qbit ids")
{
    OpenYAMM::Game::JournalQuestTable questTable = {};

    CHECK_FALSE(questTable.loadFromRows({
        {"Q Bit", "Quest Note Text", "Notes", "Owner"},
        {"abc", "Broken quest.", "", "test"},
    }));
    CHECK(questTable.entries().empty());
}

TEST_CASE("journal quest table rejects duplicate qbit ids")
{
    OpenYAMM::Game::JournalQuestTable questTable = {};

    CHECK_FALSE(questTable.loadFromRows({
        {"Q Bit", "Quest Note Text", "Notes", "Owner"},
        {"10000", "First custom quest.", "", "test"},
        {"10000", "Duplicate custom quest.", "", "test"},
    }));
    CHECK(questTable.entries().empty());
}

TEST_CASE("party quest bits survive save data round trip")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    party.setQuestBit(6, true);
    party.setQuestBit(36, true);

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.mapFileName = "quest_roundtrip.odm";
    saveData.party = party.snapshot();

    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_quest_bits_roundtrip.oysav";
    std::string error;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(savePath, saveData, error));

    const std::optional<OpenYAMM::Game::GameSaveData> loaded =
        OpenYAMM::Game::loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);

    REQUIRE(loaded.has_value());

    OpenYAMM::Game::Party restoredParty = {};
    restoredParty.seed(createRegressionPartySeed());
    restoredParty.restoreSnapshot(loaded->party);

    CHECK(restoredParty.hasQuestBit(6));
    CHECK(restoredParty.hasQuestBit(36));
    CHECK_FALSE(restoredParty.hasQuestBit(37));
}

TEST_CASE("monster target selection prefers matching living members")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    const std::optional<size_t> targetIndex = party.chooseMonsterAttackTarget(0x0010, 1);

    REQUIRE(targetIndex.has_value());
    CHECK_EQ(*targetIndex, 1u);
}

TEST_CASE("monster target selection skips invalid preferred members")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pCleric = party.member(1);
    OpenYAMM::Game::Character *pKnight = party.member(0);

    REQUIRE(pCleric != nullptr);
    REQUIRE(pKnight != nullptr);

    pCleric->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Unconscious));
    pKnight->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead));
    pKnight->health = 0;

    const std::optional<size_t> targetIndex = party.chooseMonsterAttackTarget(0x0010, 7);

    REQUIRE(targetIndex.has_value());
    CHECK_NE(*targetIndex, 0u);
    CHECK_NE(*targetIndex, 1u);
}

TEST_CASE("default seed monster target selection matches female preference")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());

    OpenYAMM::Game::Party party = {};
    party.setCharacterDollTable(&OpenYAMM::Tests::regressionGameData().characterDollTable);
    party.setClassMultiplierTable(&OpenYAMM::Tests::regressionGameData().classMultiplierTable);
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());

    const std::optional<size_t> targetIndex = party.chooseMonsterAttackTarget(0x0400, 3);

    REQUIRE(targetIndex.has_value());
    CHECK_EQ(*targetIndex, 0u);
}

TEST_CASE("party damage sets unconscious within endurance threshold")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->health = 10;
    pMember->endurance = 14;

    REQUIRE(party.applyDamageToMember(0, 12, ""));
    CHECK(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Unconscious)));
    CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead)));
}

TEST_CASE("party damage sets dead below endurance threshold")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->health = 10;
    pMember->endurance = 5;

    REQUIRE(party.applyDamageToMember(0, 20, ""));
    CHECK(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead)));
    CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Unconscious)));
}

TEST_CASE("aoe damage can move unconscious member to dead")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->health = -1;
    pMember->endurance = 3;
    pMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Unconscious));

    CHECK_FALSE(party.applyDamageToMember(0, 5, ""));
    REQUIRE(party.applyDamageToMember(0, 5, "", true));
    CHECK_EQ(pMember->health, -6);
    CHECK(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead)));
    CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Unconscious)));
}

TEST_CASE("debug damage immunity preserves hit handling while leaving health unchanged")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->health = 10;
    pMember->endurance = 5;
    party.setDebugDamageImmune(true);

    REQUIRE(party.applyDamageToMember(0, 20, "debug hit"));
    CHECK_EQ(pMember->health, 10);
    CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead)));
    CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Unconscious)));
    CHECK_EQ(party.lastStatus(), "debug hit");
}

TEST_CASE("gameplay selection blocks impairing conditions")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    const std::array<OpenYAMM::Game::CharacterCondition, 6> blockedConditions = {{
        OpenYAMM::Game::CharacterCondition::Asleep,
        OpenYAMM::Game::CharacterCondition::Paralyzed,
        OpenYAMM::Game::CharacterCondition::Unconscious,
        OpenYAMM::Game::CharacterCondition::Dead,
        OpenYAMM::Game::CharacterCondition::Petrified,
        OpenYAMM::Game::CharacterCondition::Eradicated,
    }};

    for (OpenYAMM::Game::CharacterCondition condition : blockedConditions)
    {
        pMember->conditions.reset();
        pMember->conditions.set(static_cast<size_t>(condition));
        CHECK_FALSE(party.canSelectMemberInGameplay(0));
    }

    pMember->conditions.reset();
    pMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak));
    CHECK(party.canSelectMemberInGameplay(0));

    pMember->conditions.reset();
    pMember->health = 0;
    CHECK_FALSE(party.canSelectMemberInGameplay(0));

    pMember->health = 10;
    pMember->recoverySecondsRemaining = 0.5f;
    CHECK(party.canSelectMemberInGameplay(0));
    CHECK_FALSE(OpenYAMM::Game::GameMechanics::canTakeGameplayAction(*pMember));
}

TEST_CASE("party shared experience uses learning and skips incapacitated members")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pFirst = party.member(0);
    OpenYAMM::Game::Character *pSecond = party.member(1);
    OpenYAMM::Game::Character *pThird = party.member(2);
    OpenYAMM::Game::Character *pFourth = party.member(3);
    REQUIRE(pFirst != nullptr);
    REQUIRE(pSecond != nullptr);
    REQUIRE(pThird != nullptr);
    REQUIRE(pFourth != nullptr);

    pFirst->skills["Learning"] = {"Learning", 5, OpenYAMM::Game::SkillMastery::Normal};
    pFourth->skills["Learning"] = {"Learning", 10, OpenYAMM::Game::SkillMastery::Grandmaster};
    pSecond->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Unconscious));
    pThird->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Eradicated));

    const uint32_t totalGrantedExperience = party.grantSharedExperience(200);

    CHECK_EQ(pFirst->experience, 114u);
    CHECK_EQ(pSecond->experience, 0u);
    CHECK_EQ(pThird->experience, 0u);
    CHECK_EQ(pFourth->experience, 159u);
    CHECK_EQ(totalGrantedExperience, 273u);
}

TEST_CASE("member experience mutation clamps like OE")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    CHECK_EQ(party.setMemberExperience(0, 3999999990u), 3999999990u);
    CHECK_EQ(party.addExperienceToMember(0, 1000), 4000000000u);
    CHECK_EQ(party.addExperienceToMember(0, -5000000000ll), 0u);
}

TEST_CASE("dragon ability mastery grants innate dragon spells")
{
    OpenYAMM::Game::Character dragon = makeRegressionPartyMember("Duroth", "Dragon", "PC13-01", 13);
    dragon.skills["DragonAbility"] = {"DragonAbility", 10, OpenYAMM::Game::SkillMastery::Normal};

    CHECK(dragon.setSkillMastery("DragonAbility", OpenYAMM::Game::SkillMastery::Expert));
    CHECK(dragon.knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Fear)));
    CHECK(dragon.knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FlameBlast)));
    CHECK_FALSE(dragon.knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Flight)));
    CHECK_FALSE(dragon.knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WingBuffet)));

    CHECK(dragon.setSkillMastery("DragonAbility", OpenYAMM::Game::SkillMastery::Master));
    CHECK(dragon.knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Flight)));
    CHECK_FALSE(dragon.knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WingBuffet)));

    CHECK(dragon.setSkillMastery("DragonAbility", OpenYAMM::Game::SkillMastery::Grandmaster));
    CHECK(dragon.knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WingBuffet)));
}

TEST_CASE("default party seed grants first member full spell access and preserves inventory")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());

    OpenYAMM::Game::Party party = {};
    party.setClassMultiplierTable(&OpenYAMM::Tests::regressionGameData().classMultiplierTable);
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());

    const OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    static constexpr std::array<const char *, 12> ExpectedSpellSkills = {{
        "FireMagic",
        "AirMagic",
        "WaterMagic",
        "EarthMagic",
        "SpiritMagic",
        "MindMagic",
        "BodyMagic",
        "LightMagic",
        "DarkMagic",
        "DarkElfAbility",
        "VampireAbility",
        "DragonAbility",
    }};

    REQUIRE_EQ(party.members().size(), 1u);

    for (const char *pSkillName : ExpectedSpellSkills)
    {
        const OpenYAMM::Game::CharacterSkill *pSkill = pMember->findSkill(pSkillName);
        REQUIRE(pSkill != nullptr);
        CHECK(pSkill->level == 200u);
        CHECK(pSkill->mastery == OpenYAMM::Game::SkillMastery::Grandmaster);
    }

    CHECK(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::TorchLight)));
    CHECK(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Incinerate)));
    CHECK(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Starburst)));
    CHECK(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::SoulDrinker)));
    CHECK(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::DarkfireBolt)));
    CHECK(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Mistform)));
    CHECK(pMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WingBuffet)));

    for (const std::string &skillName : OpenYAMM::Game::allCanonicalSkillNames())
    {
        const OpenYAMM::Game::CharacterSkill *pSkill = pMember->findSkill(skillName);
        REQUIRE(pSkill != nullptr);
        CHECK(pSkill->level == 200);
        CHECK(pSkill->mastery == OpenYAMM::Game::SkillMastery::Grandmaster);
    }

    CHECK_EQ(pMember->maxHealth, 2037);
    CHECK_EQ(pMember->health, pMember->maxHealth);
    CHECK_EQ(pMember->maxSpellPoints, 3034);
    CHECK_EQ(pMember->spellPoints, pMember->maxSpellPoints);

    static constexpr std::array<uint32_t, 10> ExpectedInventoryIds = {{
        401,
        410,
        411,
        400,
        741,
        222,
        223,
        266,
        253,
        656,
    }};

    for (uint32_t itemId : ExpectedInventoryIds)
    {
        const bool found = std::any_of(
            pMember->inventory.begin(),
            pMember->inventory.end(),
            [itemId](const OpenYAMM::Game::InventoryItem &item)
            {
                return item.objectDescriptionId == itemId;
            });

        CHECK(found);
    }
}

TEST_CASE("default party reset does not seed secondary test members")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&OpenYAMM::Tests::regressionGameData().itemTable);
    party.reset();

    CHECK_EQ(party.members().size(), 1u);
    CHECK(party.member(1) == nullptr);
    CHECK(party.member(2) == nullptr);
}

TEST_CASE("inventory auto placement uses grid rules")
{
    OpenYAMM::Game::Character member = {};

    REQUIRE(member.addInventoryItem(makeInventoryItem(104, 2, 2)));
    REQUIRE(member.addInventoryItem(makeInventoryItem(111, 1, 2)));
    REQUIRE(member.addInventoryItem(makeInventoryItem(25, 2, 3)));
    REQUIRE(member.addInventoryItem(makeInventoryItem(94, 3, 2)));

    const OpenYAMM::Game::InventoryItem *pShield = member.inventoryItemAt(0, 0);
    const OpenYAMM::Game::InventoryItem *pFullHelm = member.inventoryItemAt(0, 2);
    const OpenYAMM::Game::InventoryItem *pFangedBlade = member.inventoryItemAt(0, 4);
    const OpenYAMM::Game::InventoryItem *pBreastplate = member.inventoryItemAt(0, 7);

    REQUIRE(pShield != nullptr);
    REQUIRE(pFullHelm != nullptr);
    REQUIRE(pFangedBlade != nullptr);
    REQUIRE(pBreastplate != nullptr);
    CHECK_EQ(pShield->objectDescriptionId, 104u);
    CHECK_EQ(pFullHelm->objectDescriptionId, 111u);
    CHECK_EQ(pFangedBlade->objectDescriptionId, 25u);
    CHECK_EQ(pBreastplate->objectDescriptionId, 94u);
}

TEST_CASE("inventory auto placement fills columns vertically")
{
    OpenYAMM::Game::Character member = {};

    for (int index = 0; index < 20; ++index)
    {
        REQUIRE(member.addInventoryItem(makeInventoryItem(109, 1, 1)));
    }

    CHECK(member.inventoryItemAt(0, 0) != nullptr);
    CHECK(member.inventoryItemAt(0, 8) != nullptr);
    CHECK(member.inventoryItemAt(1, 0) != nullptr);
    CHECK(member.inventoryItemAt(1, 8) != nullptr);
    CHECK(member.inventoryItemAt(2, 0) != nullptr);
    CHECK(member.inventoryItemAt(2, 1) != nullptr);
    CHECK(member.inventoryItemAt(2, 2) == nullptr);
}

TEST_CASE("inventory move accepts rejects and swaps by grid rules")
{
    OpenYAMM::Game::Party party = makeInventoryParty();
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    REQUIRE(pMember->addInventoryItemAt(makeInventoryItem(104, 2, 2), 0, 0));
    REQUIRE(pMember->addInventoryItemAt(makeInventoryItem(111, 1, 2), 0, 2));

    OpenYAMM::Game::InventoryItem heldItem = {};
    REQUIRE(party.takeItemFromMemberInventoryCell(0, 0, 0, heldItem));

    std::optional<OpenYAMM::Game::InventoryItem> replacedItem;

    REQUIRE(party.tryPlaceItemInMemberInventoryCell(0, heldItem, 4, 4, replacedItem));
    CHECK_FALSE(replacedItem.has_value());

    const OpenYAMM::Game::InventoryItem *pMovedItem = pMember->inventoryItemAt(4, 4);
    REQUIRE(pMovedItem != nullptr);
    CHECK_EQ(pMovedItem->objectDescriptionId, 104u);

    REQUIRE(party.takeItemFromMemberInventoryCell(0, 4, 4, heldItem));
    CHECK_FALSE(party.tryPlaceItemInMemberInventoryCell(0, heldItem, 13, 8, replacedItem));
    REQUIRE(party.tryPlaceItemInMemberInventoryCell(0, heldItem, 0, 2, replacedItem));
    REQUIRE(replacedItem.has_value());
    CHECK_EQ(replacedItem->objectDescriptionId, 111u);

    pMovedItem = pMember->inventoryItemAt(0, 2);
    REQUIRE(pMovedItem != nullptr);
    CHECK_EQ(pMovedItem->objectDescriptionId, 104u);
}

TEST_CASE("inventory swap stores held item in first free slot when target origin is blocked")
{
    OpenYAMM::Game::Party party = makeInventoryParty();
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    REQUIRE(pMember->addInventoryItemAt(makeInventoryItem(109, 1, 1), 0, 0));
    REQUIRE(pMember->addInventoryItemAt(makeInventoryItem(111, 1, 1), 1, 0));

    std::optional<OpenYAMM::Game::InventoryItem> replacedItem;
    const OpenYAMM::Game::InventoryItem heldItem = makeInventoryItem(104, 2, 2);

    REQUIRE(party.tryPlaceItemInMemberInventoryCell(0, heldItem, 0, 0, replacedItem));
    REQUIRE(replacedItem.has_value());
    CHECK_EQ(replacedItem->objectDescriptionId, 109u);

    const OpenYAMM::Game::InventoryItem *pFallbackPlacedItem = pMember->inventoryItemAt(0, 1);
    REQUIRE(pFallbackPlacedItem != nullptr);
    CHECK_EQ(pFallbackPlacedItem->objectDescriptionId, 104u);

    const OpenYAMM::Game::InventoryItem *pBlockingItem = pMember->inventoryItemAt(1, 0);
    REQUIRE(pBlockingItem != nullptr);
    CHECK_EQ(pBlockingItem->objectDescriptionId, 111u);
}

TEST_CASE("inventory swap restores clicked item when held item has no fallback slot")
{
    OpenYAMM::Game::Party party = makeInventoryParty();
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    for (int gridY = 0; gridY < OpenYAMM::Game::Character::InventoryHeight; ++gridY)
    {
        for (int gridX = 0; gridX < OpenYAMM::Game::Character::InventoryWidth; ++gridX)
        {
            const uint32_t itemId = gridX == 0 && gridY == 0 ? 109u : 111u;
            REQUIRE(pMember->addInventoryItemAt(
                makeInventoryItem(itemId, 1, 1),
                static_cast<uint8_t>(gridX),
                static_cast<uint8_t>(gridY)));
        }
    }

    std::optional<OpenYAMM::Game::InventoryItem> replacedItem;
    const OpenYAMM::Game::InventoryItem heldItem = makeInventoryItem(104, 2, 2);

    CHECK_FALSE(party.tryPlaceItemInMemberInventoryCell(0, heldItem, 0, 0, replacedItem));
    CHECK_FALSE(replacedItem.has_value());

    const OpenYAMM::Game::InventoryItem *pRestoredItem = pMember->inventoryItemAt(0, 0);
    REQUIRE(pRestoredItem != nullptr);
    CHECK_EQ(pRestoredItem->objectDescriptionId, 109u);
    CHECK_EQ(pMember->inventoryItemCount(), pMember->inventoryCapacity());
}

TEST_CASE("inventory cross member move and full destination rejection")
{
    OpenYAMM::Game::Party party = makeInventoryParty();
    OpenYAMM::Game::Character *pSourceMember = party.member(0);
    OpenYAMM::Game::Character *pDestinationMember = party.member(1);
    REQUIRE(pSourceMember != nullptr);
    REQUIRE(pDestinationMember != nullptr);
    REQUIRE(pSourceMember->addInventoryItemAt(makeInventoryItem(111, 1, 2), 0, 0));

    OpenYAMM::Game::InventoryItem heldItem = {};
    REQUIRE(party.takeItemFromMemberInventoryCell(0, 0, 0, heldItem));

    std::optional<OpenYAMM::Game::InventoryItem> replacedItem;
    REQUIRE(party.tryPlaceItemInMemberInventoryCell(1, heldItem, 0, 0, replacedItem));
    CHECK_FALSE(replacedItem.has_value());

    const OpenYAMM::Game::InventoryItem *pTransferredItem = pDestinationMember->inventoryItemAt(0, 0);
    REQUIRE(pTransferredItem != nullptr);
    CHECK_EQ(pTransferredItem->objectDescriptionId, 111u);

    OpenYAMM::Game::Character *pFullMember = party.member(2);
    REQUIRE(pFullMember != nullptr);

    for (int gridY = 0; gridY < OpenYAMM::Game::Character::InventoryHeight; ++gridY)
    {
        for (int gridX = 0; gridX < OpenYAMM::Game::Character::InventoryWidth; ++gridX)
        {
            REQUIRE(pFullMember->addInventoryItemAt(
                makeInventoryItem(109, 1, 1),
                static_cast<uint8_t>(gridX),
                static_cast<uint8_t>(gridY)));
        }
    }

    heldItem = makeInventoryItem(104, 2, 2);
    CHECK_FALSE(party.tryPlaceItemInMemberInventoryCell(2, heldItem, 0, 0, replacedItem));
    CHECK_EQ(heldItem.objectDescriptionId, 104u);
    CHECK_EQ(pFullMember->inventoryItemCount(), pFullMember->inventoryCapacity());
}

TEST_CASE("inventory member auto transfer places item in first free slot")
{
    OpenYAMM::Game::Party party = makeInventoryParty();
    OpenYAMM::Game::Character *pDestinationMember = party.member(1);
    OpenYAMM::Game::Character *pFullMember = party.member(2);
    REQUIRE(pDestinationMember != nullptr);
    REQUIRE(pFullMember != nullptr);
    REQUIRE(pDestinationMember->addInventoryItemAt(makeInventoryItem(109, 1, 1), 0, 0));

    const OpenYAMM::Game::InventoryItem heldItem = makeInventoryItem(104, 2, 2);
    REQUIRE(party.tryAutoPlaceItemInMemberInventory(1, heldItem));

    const OpenYAMM::Game::InventoryItem *pTransferredItem = pDestinationMember->inventoryItemAt(0, 1);
    REQUIRE(pTransferredItem != nullptr);
    CHECK_EQ(pTransferredItem->objectDescriptionId, 104u);
    CHECK_EQ(pTransferredItem->gridX, 0u);
    CHECK_EQ(pTransferredItem->gridY, 1u);

    for (int gridY = 0; gridY < OpenYAMM::Game::Character::InventoryHeight; ++gridY)
    {
        for (int gridX = 0; gridX < OpenYAMM::Game::Character::InventoryWidth; ++gridX)
        {
            REQUIRE(pFullMember->addInventoryItemAt(
                makeInventoryItem(109, 1, 1),
                static_cast<uint8_t>(gridX),
                static_cast<uint8_t>(gridY)));
        }
    }

    CHECK_FALSE(party.tryAutoPlaceItemInMemberInventory(2, heldItem));
    CHECK_EQ(party.lastStatus(), "inventory full");
    CHECK_EQ(pFullMember->inventoryItemCount(), pFullMember->inventoryCapacity());
}

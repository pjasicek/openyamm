#include "doctest/doctest.h"

#include "game/gameplay/GameMechanics.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/tables/CharacterDollTable.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <array>

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

TEST_CASE("default party seed preserves unique portrait picture ids")
{
    OpenYAMM::Game::Party party = {};
    party.reset();

    const std::vector<OpenYAMM::Game::Character> &members = party.members();

    REQUIRE_GE(members.size(), 4u);

    static constexpr std::array<uint32_t, 4> ExpectedPictureIds = {{2, 1, 20, 22}};

    for (size_t memberIndex = 0; memberIndex < ExpectedPictureIds.size(); ++memberIndex)
    {
        CHECK_EQ(members[memberIndex].portraitPictureId, ExpectedPictureIds[memberIndex]);
    }
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
    CHECK_EQ(*targetIndex, 1u);
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

TEST_CASE("default party seed grants every member full spell access and preserves inventory")
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

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const OpenYAMM::Game::Character *pSeedMember = party.member(memberIndex);
        REQUIRE(pSeedMember != nullptr);

        for (const char *pSkillName : ExpectedSpellSkills)
        {
            const OpenYAMM::Game::CharacterSkill *pSkill = pSeedMember->findSkill(pSkillName);
            REQUIRE(pSkill != nullptr);
            CHECK(pSkill->level == (memberIndex == 0 ? 200u : 10u));
            CHECK(pSkill->mastery == OpenYAMM::Game::SkillMastery::Grandmaster);
        }

        CHECK(pSeedMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::TorchLight)));
        CHECK(pSeedMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Incinerate)));
        CHECK(pSeedMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Starburst)));
        CHECK(pSeedMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::SoulDrinker)));
        CHECK(pSeedMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::DarkfireBolt)));
        CHECK(pSeedMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Mistform)));
        CHECK(pSeedMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WingBuffet)));
    }

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

TEST_CASE("default party reset seeds all wand types into second member with third member overflow")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&OpenYAMM::Tests::regressionGameData().itemTable);
    party.reset();

    const OpenYAMM::Game::Character *pSecondMember = party.member(1);
    const OpenYAMM::Game::Character *pThirdMember = party.member(2);
    REQUIRE(pSecondMember != nullptr);
    REQUIRE(pThirdMember != nullptr);

    for (uint32_t itemId = 152; itemId <= 176; ++itemId)
    {
        const auto isRequestedWand =
            [itemId](const OpenYAMM::Game::InventoryItem &item)
            {
                return item.objectDescriptionId == itemId;
            };

        const auto secondIt =
            std::find_if(pSecondMember->inventory.begin(), pSecondMember->inventory.end(), isRequestedWand);
        const auto thirdIt =
            std::find_if(pThirdMember->inventory.begin(), pThirdMember->inventory.end(), isRequestedWand);
        const bool found = secondIt != pSecondMember->inventory.end() || thirdIt != pThirdMember->inventory.end();
        REQUIRE(found);

        const OpenYAMM::Game::InventoryItem &wand =
            secondIt != pSecondMember->inventory.end() ? *secondIt : *thirdIt;
        CHECK(wand.identified);
        CHECK_GT(wand.currentCharges, 0);
        CHECK_EQ(wand.currentCharges, wand.maxCharges);
    }
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

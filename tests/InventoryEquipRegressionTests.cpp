#include "doctest/doctest.h"

#include "game/gameplay/GameMechanics.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"

#include "tests/RegressionGameData.h"

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
    party.setClassSkillTable(&gameData.classSkillTable);
    party.seed(createRegressionPartySeed());
    return party;
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
    CHECK_EQ(result.spellSkillLevelOverride, 5u);
    CHECK(result.spellSkillMasteryOverride == OpenYAMM::Game::SkillMastery::Master);
    CHECK(result.consumed);
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

TEST_CASE("inventory item use potions and horseshoe apply the expected effects")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->health = 10;
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
        &gameData.readableScrollTable);

    OpenYAMM::Game::InventoryItem magicPotion = {};
    magicPotion.objectDescriptionId = 223;
    const OpenYAMM::Game::InventoryItemUseResult manaResult = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        magicPotion,
        gameData.itemTable,
        &gameData.readableScrollTable);

    OpenYAMM::Game::InventoryItem blackPotion = {};
    blackPotion.objectDescriptionId = 266;
    const OpenYAMM::Game::InventoryItemUseResult statResult = OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        blackPotion,
        gameData.itemTable,
        &gameData.readableScrollTable);

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
            OpenYAMM::Game::ItemGenerationRequest{6, OpenYAMM::Game::ItemGenerationMode::ChestLoot, true},
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

TEST_CASE("party rejects a race restricted artifact for the wrong member")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->equipment = {};
    pMember->className = "Knight";
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
    CHECK_EQ(party.lastStatus(), "cannot equip");

    pMember->className = "Patriarch";

    REQUIRE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::Armor,
        glomenmail,
        std::nullopt,
        false,
        heldReplacement));
    CHECK_EQ(pMember->equipment.armor, 514u);
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
    const OpenYAMM::Game::ItemDefinition *pBowDefinition = gameData.itemTable.get(56);
    REQUIRE(dragonSlayingEnchantId.has_value());
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
            "Cyclops",
            "Cyclops"),
        2);
    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            meleeCharacter,
            OpenYAMM::Game::CharacterAttackMode::Melee,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable,
            "Lizardman",
            "Lizardman"),
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
            "Red Dragon",
            "Dragon"),
        2);
    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            rangedCharacter,
            OpenYAMM::Game::CharacterAttackMode::Bow,
            &gameData.itemTable,
            &gameData.specialItemEnchantTable,
            "Minotaur",
            "Minotaur"),
        1);
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

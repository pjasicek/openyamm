#include "doctest/doctest.h"

#include "game/StringUtils.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"

#include "tests/PartySpellTestHarness.h"
#include "tests/RegressionGameData.h"

#include <optional>

namespace
{
const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

size_t seedDefaultSpellTarget(OpenYAMM::Tests::PartySpellTestWorldRuntime &worldRuntime)
{
    OpenYAMM::Game::GameplayRuntimeActorState actor = {};
    actor.preciseX = 1024.0f;
    actor.preciseY = 0.0f;
    actor.preciseZ = 0.0f;
    actor.height = 160;
    actor.radius = 48;
    actor.hostileToParty = true;
    actor.hasDetectedParty = true;
    return worldRuntime.addActor(actor);
}

uint32_t findFirstWeaponItemId(const OpenYAMM::Game::ItemTable &itemTable)
{
    for (const OpenYAMM::Game::ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId != 0
            && entry.skillGroup == "Sword"
            && entry.rarity == OpenYAMM::Game::ItemRarity::Common)
        {
            return entry.itemId;
        }
    }

    return 0;
}
}

TEST_CASE("party spell backend rejects cast without spell points")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    const size_t targetActorIndex = seedDefaultSpellTarget(worldRuntime);

    OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);

    pCaster->skills["FireMagic"] = {"FireMagic", 5, OpenYAMM::Game::SkillMastery::Normal};
    pCaster->spellPoints = 0;

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt);
    request.targetActorIndex = targetActorIndex;

    const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    CHECK(
        result.status == OpenYAMM::Game::PartySpellCastStatus::NotEnoughSpellPoints);
    CHECK(worldRuntime.projectileRequests().empty());
}

TEST_CASE("party spell backend haste applies party buff and spends mana")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    seedDefaultSpellTarget(worldRuntime);

    OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);

    pCaster->skills["FireMagic"] = {"FireMagic", 6, OpenYAMM::Game::SkillMastery::Expert};
    const int initialSpellPoints = pCaster->spellPoints;

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Haste);

    const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    REQUIRE(result.succeeded());
    CHECK(party.hasPartyBuff(OpenYAMM::Game::PartyBuffId::Haste));
    CHECK_EQ(pCaster->spellPoints, initialSpellPoints - 5);
    CHECK(worldRuntime.syncSpellMovementStatesCalled());
}

TEST_CASE("party spell backend fire bolt spawns projectile")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    const size_t targetActorIndex = seedDefaultSpellTarget(worldRuntime);

    OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);

    pCaster->skills["FireMagic"] = {"FireMagic", 5, OpenYAMM::Game::SkillMastery::Expert};

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt);
    request.targetActorIndex = targetActorIndex;

    const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    REQUIRE(result.succeeded());
    REQUIRE_EQ(worldRuntime.projectileRequests().size(), 1u);
    CHECK_EQ(worldRuntime.projectileRequests().front().spellId, request.spellId);
    CHECK_EQ(worldRuntime.projectileRequests().front().casterMemberIndex, 0u);
    CHECK_EQ(worldRuntime.projectileRequests().front().targetX, 1024.0f);
}

TEST_CASE("party spell backend bless applies character target buff")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);

    OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);

    pCaster->skills["SpiritMagic"] = {"SpiritMagic", 8, OpenYAMM::Game::SkillMastery::Normal};
    const int initialSpellPoints = pCaster->spellPoints;

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Bless);
    request.targetCharacterIndex = 1;

    const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    REQUIRE(result.succeeded());
    CHECK(party.hasCharacterBuff(1, OpenYAMM::Game::CharacterBuffId::Bless));
    CHECK_FALSE(party.hasCharacterBuff(0, OpenYAMM::Game::CharacterBuffId::Bless));
    CHECK_LT(pCaster->spellPoints, initialSpellPoints);
}

TEST_CASE("party spell backend supports all defined non utility spells")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    const size_t targetActorIndex = seedDefaultSpellTarget(worldRuntime);

    const uint32_t weaponItemId = findFirstWeaponItemId(gameData.itemTable);
    REQUIRE_NE(weaponItemId, 0u);

    const auto expectedUtilitySelectionStatus =
        [](uint32_t spellId) -> std::optional<OpenYAMM::Game::PartySpellCastStatus>
    {
        if (spellId == OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::RechargeItem)
            || spellId == OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::EnchantItem))
        {
            return OpenYAMM::Game::PartySpellCastStatus::NeedInventoryItemTarget;
        }

        if (spellId == OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::TownPortal)
            || spellId == OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::LloydsBeacon)
            || spellId == OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Telekinesis)
            || spellId == OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Telepathy))
        {
            return OpenYAMM::Game::PartySpellCastStatus::NeedUtilityUi;
        }

        return std::nullopt;
    };

    for (uint32_t spellId = 1;
         spellId <= OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WingBuffet);
         ++spellId)
    {
        const OpenYAMM::Game::SpellEntry *pSpellEntry =
            gameData.spellTable.findById(static_cast<int>(spellId));

        if (pSpellEntry == nullptr
            || pSpellEntry->name.empty()
            || OpenYAMM::Game::toLowerCopy(pSpellEntry->name).find("unused") != std::string::npos)
        {
            continue;
        }

        OpenYAMM::Game::PartySpellCastRequest request = {};
        request.casterMemberIndex = 0;
        request.spellId = spellId;
        request.targetActorIndex = targetActorIndex;
        request.targetCharacterIndex = 1;
        request.hasTargetPoint = true;
        request.targetX = 1024.0f;
        request.targetY = 0.0f;
        request.targetZ = 0.0f;
        request.skillLevelOverride = 10;
        request.skillMasteryOverride = OpenYAMM::Game::SkillMastery::Grandmaster;
        request.spendMana = false;
        request.applyRecovery = false;

        if (spellId == OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireAura)
            || spellId == OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::VampiricWeapon))
        {
            OpenYAMM::Game::Character *pCaster = party.member(0);
            REQUIRE(pCaster != nullptr);

            pCaster->equipment.mainHand = weaponItemId;
            pCaster->equipmentRuntime.mainHand = {};
            request.targetItemMemberIndex = 0;
            request.targetEquipmentSlot = OpenYAMM::Game::EquipmentSlot::MainHand;
        }

        const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
            party,
            worldRuntime,
            gameData.spellTable,
            request);

        const std::optional<OpenYAMM::Game::PartySpellCastStatus> expectedUtilityStatus =
            expectedUtilitySelectionStatus(spellId);

        if (expectedUtilityStatus.has_value())
        {
            INFO(pSpellEntry->name);
            CHECK(result.status == *expectedUtilityStatus);
            continue;
        }

        INFO(pSpellEntry->name);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::InvalidCaster);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::InvalidSpell);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::NotSkilledEnough);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::NeedActorTarget);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::NeedCharacterTarget);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::NeedActorOrCharacterTarget);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::NeedGroundPoint);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::NeedInventoryItemTarget);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::NeedUtilityUi);
        CHECK(result.status != OpenYAMM::Game::PartySpellCastStatus::Unsupported);
    }
}

TEST_CASE("party spell scroll override cast uses fixed master skill without mana")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    seedDefaultSpellTarget(worldRuntime);

    OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);

    pCaster->skills.clear();
    const int initialSpellPoints = pCaster->spellPoints;

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Haste);
    request.skillLevelOverride = 5;
    request.skillMasteryOverride = OpenYAMM::Game::SkillMastery::Master;
    request.spendMana = false;
    request.applyRecovery = false;

    const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    REQUIRE(result.succeeded());
    CHECK(party.hasPartyBuff(OpenYAMM::Game::PartyBuffId::Haste));
    CHECK_EQ(pCaster->spellPoints, initialSpellPoints);
}

#include "doctest/doctest.h"

#include "game/StringUtils.h"
#include "game/maps/SaveGame.h"
#include "game/party/LloydsBeaconRuntime.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"

#include "tests/PartySpellTestHarness.h"
#include "tests/RegressionGameData.h"

#include <filesystem>
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

TEST_CASE("party spell backend lets wands bypass learned mastery requirements")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    const size_t targetActorIndex = seedDefaultSpellTarget(worldRuntime);

    OpenYAMM::Game::PartySpellCastRequest blockedRequest = {};
    blockedRequest.casterMemberIndex = 0;
    blockedRequest.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Incinerate);
    blockedRequest.targetActorIndex = targetActorIndex;
    blockedRequest.skillLevelOverride = 8;
    blockedRequest.skillMasteryOverride = OpenYAMM::Game::SkillMastery::Normal;
    blockedRequest.spendMana = false;
    blockedRequest.applyRecovery = false;

    const OpenYAMM::Game::PartySpellCastResult blockedResult = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        blockedRequest);

    CHECK(blockedResult.status == OpenYAMM::Game::PartySpellCastStatus::NotSkilledEnough);
    CHECK(worldRuntime.projectileRequests().empty());

    OpenYAMM::Game::PartySpellCastRequest wandRequest = blockedRequest;
    wandRequest.bypassRequiredMastery = true;

    const OpenYAMM::Game::PartySpellCastResult wandResult = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        wandRequest);

    REQUIRE(wandResult.succeeded());
    REQUIRE_EQ(worldRuntime.projectileRequests().size(), 1u);
    CHECK_EQ(worldRuntime.projectileRequests().front().spellId, wandRequest.spellId);
    CHECK_EQ(worldRuntime.projectileRequests().front().skillLevel, 8u);
    CHECK(worldRuntime.projectileRequests().front().skillMastery == OpenYAMM::Game::SkillMastery::Normal);
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

TEST_CASE("party spell backend recharge item restores wand charges")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);

    OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    pCaster->skills["WaterMagic"] = {"WaterMagic", 10, OpenYAMM::Game::SkillMastery::Expert};

    OpenYAMM::Game::InventoryItem wand = {};
    wand.objectDescriptionId = 152;
    wand.currentCharges = 5;
    wand.maxCharges = 20;
    REQUIRE(pCaster->addInventoryItemAt(wand, 0, 0));

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::RechargeItem);
    request.targetItemMemberIndex = 0;
    request.targetInventoryGridX = 0;
    request.targetInventoryGridY = 0;

    const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    REQUIRE(result.succeeded());

    const OpenYAMM::Game::InventoryItem *pRechargedWand = party.memberInventoryItem(0, 0, 0);
    REQUIRE(pRechargedWand != nullptr);
    CHECK_EQ(pRechargedWand->currentCharges, 12u);
    CHECK_EQ(pRechargedWand->maxCharges, 12u);
}

TEST_CASE("party spell backend recharge item rejects invalid and already charged targets")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);

    OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    pCaster->skills["WaterMagic"] = {"WaterMagic", 10, OpenYAMM::Game::SkillMastery::Expert};

    OpenYAMM::Game::InventoryItem sword = {};
    sword.objectDescriptionId = findFirstWeaponItemId(gameData.itemTable);
    REQUIRE_NE(sword.objectDescriptionId, 0u);
    REQUIRE(pCaster->addInventoryItemAt(sword, 0, 0));

    OpenYAMM::Game::PartySpellCastRequest invalidTargetRequest = {};
    invalidTargetRequest.casterMemberIndex = 0;
    invalidTargetRequest.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::RechargeItem);
    invalidTargetRequest.targetItemMemberIndex = 0;
    invalidTargetRequest.targetInventoryGridX = 0;
    invalidTargetRequest.targetInventoryGridY = 0;

    const OpenYAMM::Game::PartySpellCastResult invalidTargetResult =
        OpenYAMM::Game::PartySpellSystem::castSpell(
            party,
            worldRuntime,
            gameData.spellTable,
            invalidTargetRequest);

    CHECK(invalidTargetResult.status == OpenYAMM::Game::PartySpellCastStatus::Failed);

    OpenYAMM::Game::InventoryItem wand = {};
    wand.objectDescriptionId = 152;
    wand.currentCharges = 18;
    wand.maxCharges = 20;
    REQUIRE(pCaster->addInventoryItemAt(wand, 2, 0));

    OpenYAMM::Game::PartySpellCastRequest chargedWandRequest = invalidTargetRequest;
    chargedWandRequest.targetInventoryGridX = 2;
    chargedWandRequest.targetInventoryGridY = 0;

    const OpenYAMM::Game::PartySpellCastResult chargedWandResult =
        OpenYAMM::Game::PartySpellSystem::castSpell(
            party,
            worldRuntime,
            gameData.spellTable,
            chargedWandRequest);

    CHECK(chargedWandResult.status == OpenYAMM::Game::PartySpellCastStatus::Failed);
    CHECK_EQ(chargedWandResult.statusText, "Wand already charged");
}

TEST_CASE("party spell backend summon wisp adds one friendly summon per cast up to the active limit")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::SummonWisp);
    request.skillLevelOverride = 3;
    request.skillMasteryOverride = OpenYAMM::Game::SkillMastery::Grandmaster;
    request.spendMana = false;
    request.applyRecovery = false;

    for (size_t castIndex = 0; castIndex < 5; ++castIndex)
    {
        const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
            party,
            worldRuntime,
            gameData.spellTable,
            request);

        REQUIRE(result.succeeded());
        REQUIRE_EQ(worldRuntime.friendlySummonRequests().size(), castIndex + 1);
        CHECK_EQ(worldRuntime.friendlySummonRequests().back().monsterId, 99);
        CHECK_EQ(worldRuntime.friendlySummonRequests().back().count, 1u);
        CHECK_EQ(worldRuntime.friendlySummonRequests().back().durationSeconds, 3.0f * 60.0f * 60.0f);
    }

    const OpenYAMM::Game::PartySpellCastResult limitResult = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    CHECK(limitResult.status == OpenYAMM::Game::PartySpellCastStatus::Failed);
    CHECK_EQ(limitResult.statusText, "Too many summoned wisps");
    CHECK_EQ(worldRuntime.friendlySummonRequests().size(), 5u);
}

TEST_CASE("party spell backend enforces indoor outdoor spell gates in shared spell rules")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.skillLevelOverride = 10;
    request.skillMasteryOverride = OpenYAMM::Game::SkillMastery::Grandmaster;
    request.spendMana = false;
    request.applyRecovery = false;
    request.hasTargetPoint = true;
    request.targetX = 512.0f;
    request.targetY = 0.0f;
    request.targetZ = 0.0f;

    worldRuntime.setIndoorMap(true);
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::MeteorShower);
    const OpenYAMM::Game::PartySpellCastResult meteorResult = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    CHECK(meteorResult.status == OpenYAMM::Game::PartySpellCastStatus::Failed);
    CHECK_EQ(meteorResult.statusText, "Can't cast Meteor Shower indoors!");

    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Starburst);
    const OpenYAMM::Game::PartySpellCastResult starburstResult = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    CHECK(starburstResult.status == OpenYAMM::Game::PartySpellCastStatus::Failed);
    CHECK_EQ(starburstResult.statusText, "Can't cast Starburst indoors!");

    worldRuntime.setIndoorMap(false);
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Inferno);
    const OpenYAMM::Game::PartySpellCastResult infernoResult = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    CHECK(infernoResult.status == OpenYAMM::Game::PartySpellCastStatus::Failed);
    CHECK_EQ(infernoResult.statusText, "Can't cast Inferno outdoors!");

    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::PrismaticLight);
    const OpenYAMM::Game::PartySpellCastResult prismaticResult = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    CHECK(prismaticResult.status == OpenYAMM::Game::PartySpellCastStatus::Failed);
    CHECK_EQ(prismaticResult.statusText, "Can't cast Prismatic Light outdoors!");
}

TEST_CASE("party spell backend prismatic light damages visible indoor creatures")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    worldRuntime.setIndoorMap(true);

    OpenYAMM::Game::GameplayRuntimeActorState visibleCreature = {};
    visibleCreature.preciseX = 512.0f;
    visibleCreature.preciseY = 0.0f;
    visibleCreature.preciseZ = 0.0f;
    visibleCreature.radius = 32;
    visibleCreature.height = 128;
    visibleCreature.hostileToParty = false;
    worldRuntime.addActor(visibleCreature);

    OpenYAMM::Game::GameplayRuntimeActorState hiddenCreature = visibleCreature;
    hiddenCreature.preciseX = -512.0f;
    hiddenCreature.hostileToParty = true;
    worldRuntime.addActor(hiddenCreature);

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::PrismaticLight);
    request.skillLevelOverride = 7;
    request.skillMasteryOverride = OpenYAMM::Game::SkillMastery::Expert;
    request.spendMana = false;
    request.applyRecovery = false;
    request.hasViewTransform = true;
    request.viewX = 0.0f;
    request.viewY = 0.0f;
    request.viewZ = 96.0f;
    request.viewYawRadians = 0.0f;
    request.viewPitchRadians = 0.0f;
    request.viewAspectRatio = 4.0f / 3.0f;

    const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    REQUIRE(result.succeeded());
    REQUIRE_EQ(worldRuntime.appliedSpellRequests().size(), 1u);
    CHECK_EQ(worldRuntime.appliedSpellRequests().front().actorIndex, 0u);
    CHECK_EQ(worldRuntime.appliedSpellRequests().front().damage, 32);
    REQUIRE(result.screenOverlayRequest.has_value());
    CHECK_EQ(result.screenOverlayRequest->colorAbgr, 0xffe0ffffu);
}

TEST_CASE("party spell backend soul drinker drains visible indoor creatures and heals party")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    worldRuntime.setIndoorMap(true);

    OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    pCaster->health = 20;

    OpenYAMM::Game::GameplayRuntimeActorState visibleCreature = {};
    visibleCreature.preciseX = 512.0f;
    visibleCreature.preciseY = 0.0f;
    visibleCreature.preciseZ = 0.0f;
    visibleCreature.radius = 32;
    visibleCreature.height = 128;
    visibleCreature.hostileToParty = false;
    worldRuntime.addActor(visibleCreature);

    OpenYAMM::Game::GameplayRuntimeActorState hiddenCreature = visibleCreature;
    hiddenCreature.preciseX = -512.0f;
    hiddenCreature.hostileToParty = true;
    worldRuntime.addActor(hiddenCreature);

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::SoulDrinker);
    request.skillLevelOverride = 1;
    request.skillMasteryOverride = OpenYAMM::Game::SkillMastery::Grandmaster;
    request.spendMana = false;
    request.applyRecovery = false;
    request.hasViewTransform = true;
    request.viewX = 0.0f;
    request.viewY = 0.0f;
    request.viewZ = 96.0f;
    request.viewYawRadians = 0.0f;
    request.viewPitchRadians = 0.0f;
    request.viewAspectRatio = 4.0f / 3.0f;

    const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        request);

    REQUIRE(result.succeeded());
    REQUIRE_EQ(worldRuntime.appliedSpellRequests().size(), 1u);
    CHECK_EQ(worldRuntime.appliedSpellRequests().front().actorIndex, 0u);
    CHECK_GT(worldRuntime.appliedSpellRequests().front().damage, 25);
    CHECK_LT(worldRuntime.appliedSpellRequests().front().damage, 34);
    CHECK_GT(party.members().front().health, 20);
    REQUIRE(result.screenOverlayRequest.has_value());
    CHECK_EQ(result.screenOverlayRequest->colorAbgr, 0xff0c0038u);
}

TEST_CASE("lloyds beacon slots and duration follow water mastery and skill level")
{
    CHECK_EQ(
        OpenYAMM::Game::lloydsBeaconMaxSlotsForMastery(OpenYAMM::Game::SkillMastery::Normal),
        1u);
    CHECK_EQ(
        OpenYAMM::Game::lloydsBeaconMaxSlotsForMastery(OpenYAMM::Game::SkillMastery::Expert),
        3u);
    CHECK_EQ(
        OpenYAMM::Game::lloydsBeaconMaxSlotsForMastery(OpenYAMM::Game::SkillMastery::Master),
        5u);
    CHECK_EQ(
        OpenYAMM::Game::lloydsBeaconDurationSeconds(2),
        14.0f * 24.0f * 60.0f * 60.0f);
}

TEST_CASE("lloyds beacon set stores location preview and recall queues map move")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    worldRuntime.setPartyPosition(10.0f, 20.0f, 30.0f);

    OpenYAMM::Game::PartySpellCastRequest setRequest = {};
    setRequest.casterMemberIndex = 0;
    setRequest.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::LloydsBeacon);
    setRequest.skillLevelOverride = 4;
    setRequest.skillMasteryOverride = OpenYAMM::Game::SkillMastery::Grandmaster;
    setRequest.spendMana = false;
    setRequest.utilityAction = OpenYAMM::Game::PartySpellUtilityActionKind::LloydsBeaconSet;
    setRequest.utilitySlotIndex = 0;
    setRequest.utilityStatusText = "Spell Test";
    setRequest.utilityMapMoveDirectionDegrees = 90;
    setRequest.utilityPreviewWidth = 2;
    setRequest.utilityPreviewHeight = 1;
    setRequest.utilityPreviewPixelsBgra = {1, 2, 3, 255, 4, 5, 6, 255};

    const OpenYAMM::Game::PartySpellCastResult setResult = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        setRequest);

    REQUIRE(setResult.succeeded());

    const OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    REQUIRE(pCaster->lloydsBeacons[0].has_value());

    const OpenYAMM::Game::LloydBeacon &beacon = *pCaster->lloydsBeacons[0];
    CHECK_EQ(beacon.mapName, "spell_test.odm");
    CHECK_EQ(beacon.locationName, "Spell Test");
    CHECK_EQ(beacon.x, 10.0f);
    CHECK_EQ(beacon.y, 20.0f);
    CHECK_EQ(beacon.z, 30.0f);
    CHECK_EQ(beacon.directionDegrees, 90.0f);
    CHECK_EQ(beacon.remainingSeconds, OpenYAMM::Game::lloydsBeaconDurationSeconds(4));
    CHECK_EQ(beacon.previewWidth, 2);
    CHECK_EQ(beacon.previewHeight, 1);
    CHECK_EQ(beacon.previewPixelsBgra, setRequest.utilityPreviewPixelsBgra);

    OpenYAMM::Game::PartySpellCastRequest recallRequest = {};
    recallRequest.casterMemberIndex = 0;
    recallRequest.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::LloydsBeacon);
    recallRequest.skillLevelOverride = 4;
    recallRequest.skillMasteryOverride = OpenYAMM::Game::SkillMastery::Grandmaster;
    recallRequest.spendMana = false;
    recallRequest.utilityAction = OpenYAMM::Game::PartySpellUtilityActionKind::LloydsBeaconRecall;
    recallRequest.utilitySlotIndex = 0;

    const OpenYAMM::Game::PartySpellCastResult recallResult = OpenYAMM::Game::PartySpellSystem::castSpell(
        party,
        worldRuntime,
        gameData.spellTable,
        recallRequest);

    REQUIRE(recallResult.succeeded());
    REQUIRE(worldRuntime.eventRuntimeState()->pendingMapMove.has_value());
    CHECK_EQ(worldRuntime.eventRuntimeState()->pendingMapMove->mapName, std::optional<std::string>("spell_test.odm"));
    CHECK_EQ(worldRuntime.eventRuntimeState()->pendingMapMove->x, 10);
    CHECK_EQ(worldRuntime.eventRuntimeState()->pendingMapMove->y, 20);
    CHECK_EQ(worldRuntime.eventRuntimeState()->pendingMapMove->z, 30);
    CHECK_EQ(worldRuntime.eventRuntimeState()->pendingMapMove->directionDegrees, 90);
}

TEST_CASE("lloyds beacon preview data survives save round trip")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);

    OpenYAMM::Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);

    OpenYAMM::Game::LloydBeacon beacon = {};
    beacon.mapName = "spell_test.odm";
    beacon.locationName = "Spell Test";
    beacon.remainingSeconds = OpenYAMM::Game::lloydsBeaconDurationSeconds(3);
    beacon.previewWidth = 2;
    beacon.previewHeight = 1;
    beacon.previewPixelsBgra = {10, 20, 30, 255, 40, 50, 60, 255};
    pCaster->lloydsBeacons[0] = beacon;

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.mapFileName = "spell_test.odm";
    saveData.party = party.snapshot();

    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_lloyds_beacon_roundtrip.oysav";
    std::string error;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(savePath, saveData, error));

    const std::optional<OpenYAMM::Game::GameSaveData> loaded =
        OpenYAMM::Game::loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);

    REQUIRE(loaded.has_value());
    REQUIRE_FALSE(loaded->party.members.empty());
    REQUIRE(loaded->party.members[0].lloydsBeacons[0].has_value());

    const OpenYAMM::Game::LloydBeacon &loadedBeacon = *loaded->party.members[0].lloydsBeacons[0];
    CHECK_EQ(loadedBeacon.mapName, beacon.mapName);
    CHECK_EQ(loadedBeacon.locationName, beacon.locationName);
    CHECK_EQ(loadedBeacon.remainingSeconds, beacon.remainingSeconds);
    CHECK_EQ(loadedBeacon.previewWidth, beacon.previewWidth);
    CHECK_EQ(loadedBeacon.previewHeight, beacon.previewHeight);
    CHECK_EQ(loadedBeacon.previewPixelsBgra, beacon.previewPixelsBgra);
}

TEST_CASE("indoor scene runtime state survives save round trip")
{
    OpenYAMM::Game::IndoorSceneRuntime::Snapshot snapshot = {};
    snapshot.mapDeltaData.emplace();
    snapshot.mapDeltaData->actors.push_back({});
    snapshot.mapDeltaData->actors[0].name = "Placed Actor";
    snapshot.mapDeltaData->actors[0].hp = 17;
    snapshot.mapDeltaData->actors[0].x = 100;
    snapshot.mapDeltaData->actors[0].y = 200;
    snapshot.mapDeltaData->actors[0].z = 300;
    snapshot.mapDeltaData->actors[0].currentActionAnimation = 4;
    snapshot.mapDeltaData->spriteObjects.push_back({});
    snapshot.mapDeltaData->spriteObjects[0].objectDescriptionId = 91;
    snapshot.mapDeltaData->spriteObjects[0].x = 11;
    snapshot.mapDeltaData->spriteObjects[0].rawContainingItem = {1, 2, 3, 4};
    snapshot.mapDeltaData->doorSlotCount = 1;
    snapshot.mapDeltaData->doors.push_back({});
    snapshot.mapDeltaData->doors[0].doorId = 7;
    snapshot.mapDeltaData->doors[0].timeSinceTriggered = 1234;
    snapshot.mapDeltaData->doors[0].state = 2;
    snapshot.mapDeltaData->doorsData = {5, 6, 7};

    snapshot.eventRuntimeState.emplace();
    OpenYAMM::Game::RuntimeMechanismState mechanism = {};
    mechanism.state = 2;
    mechanism.timeSinceTriggeredMs = 350.0f;
    mechanism.currentDistance = 64.0f;
    mechanism.isMoving = true;
    snapshot.eventRuntimeState->mechanisms[7] = mechanism;
    OpenYAMM::Game::EventRuntimeState::PendingSound sound = {};
    sound.soundId = 42;
    sound.x = 10;
    sound.y = 20;
    sound.z = 30;
    sound.positional = true;
    sound.hasExplicitZ = true;
    snapshot.eventRuntimeState->pendingSounds.push_back(sound);

    snapshot.worldRuntime.gameMinutes = 123.0f;
    snapshot.worldRuntime.currentLocationReputation = -5;
    snapshot.worldRuntime.sessionChestSeed = 99;
    OpenYAMM::Game::IndoorWorldRuntime::MapActorAiState actorState = {};
    actorState.actorId = 12;
    actorState.monsterId = 34;
    actorState.displayName = "Saved Actor";
    actorState.spriteFrameIndex = 56;
    actorState.actionSpriteFrameIndices = {1, 2, 3, 4, 5, 6, 7, 8};
    actorState.collisionRadius = 48;
    actorState.collisionHeight = 144;
    actorState.movementSpeed = 220;
    actorState.hostileToParty = true;
    actorState.hasDetectedParty = true;
    actorState.motionState = OpenYAMM::Game::ActorAiMotionState::Pursuing;
    actorState.animationState = OpenYAMM::Game::ActorAiAnimationState::GotHit;
    actorState.queuedAttackAbility = OpenYAMM::Game::GameplayActorAttackAbility::Spell2;
    actorState.preciseX = 101.0f;
    actorState.preciseY = 202.0f;
    actorState.preciseZ = 303.0f;
    actorState.homePreciseX = 91.0f;
    actorState.homePreciseY = 92.0f;
    actorState.homePreciseZ = 93.0f;
    actorState.moveDirectionX = 0.25f;
    actorState.moveDirectionY = -0.5f;
    actorState.velocityX = 1.0f;
    actorState.velocityY = 2.0f;
    actorState.velocityZ = 3.0f;
    actorState.sectorId = 4;
    actorState.eyeSectorId = 5;
    actorState.supportFaceIndex = 6;
    actorState.grounded = true;
    actorState.yawRadians = 1.5f;
    actorState.animationTimeTicks = 77.0f;
    actorState.recoverySeconds = 0.8f;
    actorState.attackAnimationSeconds = 0.9f;
    actorState.meleeAttackAnimationSeconds = 0.7f;
    actorState.rangedAttackAnimationSeconds = 0.6f;
    actorState.dyingAnimationSeconds = 1.1f;
    actorState.attackCooldownSeconds = 2.0f;
    actorState.idleDecisionSeconds = 3.0f;
    actorState.actionSeconds = 4.0f;
    actorState.crowdSideLockRemainingSeconds = 0.1f;
    actorState.crowdNoProgressSeconds = 0.2f;
    actorState.crowdLastEdgeDistance = 0.3f;
    actorState.crowdRetreatRemainingSeconds = 0.4f;
    actorState.crowdStandRemainingSeconds = 0.5f;
    actorState.crowdProbeEdgeDistance = 0.6f;
    actorState.crowdProbeElapsedSeconds = 0.7f;
    actorState.idleDecisionCount = 8;
    actorState.pursueDecisionCount = 9;
    actorState.attackDecisionCount = 10;
    actorState.crowdEscapeAttempts = 11;
    actorState.crowdSideSign = -1;
    actorState.attackImpactTriggered = true;
    snapshot.worldRuntime.mapActorAiStates.push_back(actorState);

    OpenYAMM::Game::GameplayCorpseViewState corpseView = {};
    corpseView.fromSummonedMonster = true;
    corpseView.sourceIndex = 0;
    corpseView.title = "Saved Corpse";
    corpseView.items.push_back({});
    corpseView.items[0].itemId = 540;
    snapshot.worldRuntime.mapActorCorpseViews.push_back(corpseView);

    OpenYAMM::Game::IndoorWorldRuntime::BloodSplatState bloodSplat = {};
    bloodSplat.sourceActorId = 12;
    bloodSplat.x = 1.0f;
    bloodSplat.y = 2.0f;
    bloodSplat.z = 3.0f;
    bloodSplat.radius = 4.0f;
    bloodSplat.vertices.push_back({1.0f, 2.0f, 3.0f, 0.25f, 0.75f});
    snapshot.worldRuntime.bloodSplats.push_back(bloodSplat);
    snapshot.worldRuntime.actorUpdateAccumulatorSeconds = 0.125f;

    OpenYAMM::Game::IndoorSceneRuntime::TimerState timer = {};
    timer.eventId = 88;
    timer.repeating = true;
    timer.targetHour = 12;
    timer.intervalGameMinutes = 30.0f;
    timer.remainingGameMinutes = 12.5f;
    timer.hasFired = true;
    snapshot.timers.push_back(timer);
    OpenYAMM::Game::IndoorMoveState moveState = {};
    moveState.x = 10.0f;
    moveState.y = 20.0f;
    moveState.footZ = 30.0f;
    moveState.eyeHeight = 160.0f;
    moveState.verticalVelocity = -4.0f;
    moveState.sectorId = 2;
    moveState.eyeSectorId = 3;
    moveState.supportFaceIndex = 4;
    moveState.grounded = true;
    snapshot.lastProcessedPartyMoveStateForFaceTriggers = moveState;
    snapshot.mechanismAccumulatorMilliseconds = 16.0f;

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.currentSceneKind = OpenYAMM::Game::SceneKind::Indoor;
    saveData.mapFileName = "save_test.blv";
    saveData.hasIndoorSceneState = true;
    saveData.indoorScene = snapshot;
    saveData.indoorSceneStates[saveData.mapFileName] = snapshot;

    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_indoor_scene_roundtrip.oysav";
    std::string error;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(savePath, saveData, error));

    const std::optional<OpenYAMM::Game::GameSaveData> loaded =
        OpenYAMM::Game::loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);

    REQUIRE(loaded.has_value());
    REQUIRE(loaded->hasIndoorSceneState);
    const OpenYAMM::Game::IndoorSceneRuntime::Snapshot &loadedSnapshot = loaded->indoorScene;
    REQUIRE(loadedSnapshot.mapDeltaData.has_value());
    REQUIRE_EQ(loadedSnapshot.mapDeltaData->actors.size(), 1u);
    CHECK_EQ(loadedSnapshot.mapDeltaData->actors[0].name, "Placed Actor");
    CHECK_EQ(loadedSnapshot.mapDeltaData->actors[0].currentActionAnimation, 4);
    REQUIRE_EQ(loadedSnapshot.mapDeltaData->spriteObjects.size(), 1u);
    CHECK_EQ(loadedSnapshot.mapDeltaData->spriteObjects[0].rawContainingItem, std::vector<uint8_t>({1, 2, 3, 4}));
    REQUIRE_EQ(loadedSnapshot.mapDeltaData->doors.size(), 1u);
    CHECK_EQ(loadedSnapshot.mapDeltaData->doors[0].state, 2);
    CHECK_EQ(loadedSnapshot.mapDeltaData->doorsData, std::vector<int16_t>({5, 6, 7}));

    REQUIRE(loadedSnapshot.eventRuntimeState.has_value());
    REQUIRE(loadedSnapshot.eventRuntimeState->mechanisms.contains(7));
    CHECK(loadedSnapshot.eventRuntimeState->mechanisms.at(7).isMoving);
    CHECK_EQ(loadedSnapshot.eventRuntimeState->mechanisms.at(7).currentDistance, 64.0f);
    REQUIRE_EQ(loadedSnapshot.eventRuntimeState->pendingSounds.size(), 1u);
    CHECK_EQ(loadedSnapshot.eventRuntimeState->pendingSounds[0].z, 30);
    CHECK(loadedSnapshot.eventRuntimeState->pendingSounds[0].hasExplicitZ);

    REQUIRE_EQ(loadedSnapshot.worldRuntime.mapActorAiStates.size(), 1u);
    const OpenYAMM::Game::IndoorWorldRuntime::MapActorAiState &loadedActorState =
        loadedSnapshot.worldRuntime.mapActorAiStates[0];
    CHECK_EQ(loadedActorState.spriteFrameIndex, 56);
    CHECK_EQ(loadedActorState.actionSpriteFrameIndices[7], 8);
    CHECK_EQ(loadedActorState.collisionHeight, 144);
    CHECK_EQ(loadedActorState.sectorId, 4);
    CHECK_EQ(loadedActorState.eyeSectorId, 5);
    CHECK_EQ(loadedActorState.supportFaceIndex, 6u);
    CHECK(loadedActorState.grounded);
    CHECK_EQ(loadedActorState.meleeAttackAnimationSeconds, 0.7f);
    CHECK_EQ(loadedActorState.rangedAttackAnimationSeconds, 0.6f);
    CHECK_EQ(loadedActorState.dyingAnimationSeconds, 1.1f);
    CHECK_EQ(loadedActorState.crowdRetreatRemainingSeconds, 0.4f);
    CHECK_EQ(loadedActorState.crowdEscapeAttempts, 11);
    CHECK_EQ(loadedActorState.crowdSideSign, -1);

    REQUIRE_EQ(loadedSnapshot.worldRuntime.mapActorCorpseViews.size(), 1u);
    REQUIRE(loadedSnapshot.worldRuntime.mapActorCorpseViews[0].has_value());
    CHECK_EQ(loadedSnapshot.worldRuntime.mapActorCorpseViews[0]->title, "Saved Corpse");
    CHECK_EQ(loadedSnapshot.worldRuntime.mapActorCorpseViews[0]->items[0].itemId, 540u);
    REQUIRE_EQ(loadedSnapshot.worldRuntime.bloodSplats.size(), 1u);
    CHECK_EQ(loadedSnapshot.worldRuntime.bloodSplats[0].vertices[0].v, 0.75f);
    CHECK_EQ(loadedSnapshot.worldRuntime.actorUpdateAccumulatorSeconds, 0.125f);

    REQUIRE_EQ(loadedSnapshot.timers.size(), 1u);
    CHECK_EQ(loadedSnapshot.timers[0].eventId, 88);
    CHECK_EQ(loadedSnapshot.timers[0].remainingGameMinutes, 12.5f);
    REQUIRE(loadedSnapshot.lastProcessedPartyMoveStateForFaceTriggers.has_value());
    CHECK_EQ(loadedSnapshot.lastProcessedPartyMoveStateForFaceTriggers->supportFaceIndex, 4u);
    CHECK_EQ(loadedSnapshot.mechanismAccumulatorMilliseconds, 16.0f);
    REQUIRE(loaded->indoorSceneStates.contains("save_test.blv"));
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

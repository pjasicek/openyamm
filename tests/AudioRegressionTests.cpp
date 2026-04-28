#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/audio/GameAudioSystem.h"
#include "game/audio/SoundIds.h"
#include "game/gameplay/GameplaySpeechRules.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"

#include "tests/RegressionGameData.h"

#include <SDL3/SDL.h>

#include <array>
#include <filesystem>
#include <string>

namespace
{
const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

bool initializeRegressionAssetFileSystem(
    OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetsRoot = sourceRoot / "assets_dev";

    if (!assetFileSystem.initialize(sourceRoot, assetsRoot, OpenYAMM::Engine::AssetScaleTier::X1))
    {
        failure = "could not initialize asset file system for regression audio tests";
        return false;
    }

    return true;
}

bool initializeRegressionAudioSystem(
    const OpenYAMM::Tests::RegressionGameData &gameData,
    OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    OpenYAMM::Game::GameAudioSystem &audioSystem,
    std::string &failure)
{
    SDL_Environment *pEnvironment = SDL_GetEnvironment();

    if (pEnvironment == nullptr || !SDL_SetEnvironmentVariable(pEnvironment, "SDL_AUDIODRIVER", "dummy", true))
    {
        failure = "could not force dummy audio driver for regression audio tests";
        return false;
    }

    if (!initializeRegressionAssetFileSystem(assetFileSystem, failure))
    {
        return false;
    }

    if (!audioSystem.initialize(assetFileSystem, gameData.characterDollTable, gameData.spellTable))
    {
        failure = "could not initialize game audio system for regression audio tests";
        return false;
    }

    return true;
}

OpenYAMM::Game::Party makeAudioRegressionParty(const OpenYAMM::Tests::RegressionGameData &gameData)
{
    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setCharacterDollTable(&gameData.characterDollTable);
    party.setItemEnchantTables(
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable);
    party.setClassMultiplierTable(&gameData.classMultiplierTable);
    party.setClassSkillTable(&gameData.classSkillTable);
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());
    return party;
}

uint32_t findFirstItemIdBySkillGroup(
    const OpenYAMM::Game::ItemTable &itemTable,
    const std::string &skillGroup)
{
    for (const OpenYAMM::Game::ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId != 0 && entry.skillGroup == skillGroup)
        {
            return entry.itemId;
        }
    }

    return 0;
}

bool isDullImpactSound(OpenYAMM::Game::SoundId soundId)
{
    return soundId == OpenYAMM::Game::SoundId::DullStrike
        || soundId == OpenYAMM::Game::SoundId::DullArmorStrike01
        || soundId == OpenYAMM::Game::SoundId::DullArmorStrike02
        || soundId == OpenYAMM::Game::SoundId::DullArmorStrike03;
}

bool isMetalImpactSound(OpenYAMM::Game::SoundId soundId)
{
    return soundId == OpenYAMM::Game::SoundId::MetalVsMetal01
        || soundId == OpenYAMM::Game::SoundId::MetalArmorStrike01
        || soundId == OpenYAMM::Game::SoundId::MetalArmorStrike02
        || soundId == OpenYAMM::Game::SoundId::MetalArmorStrike03;
}
}

TEST_CASE("spellbook speech audio resolves for success failure and store closed")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    OpenYAMM::Game::GameAudioSystem audioSystem;
    std::string failure;

    REQUIRE_MESSAGE(
        initializeRegressionAudioSystem(gameData, assetFileSystem, audioSystem, failure),
        failure.c_str());

    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.member(0);

    REQUIRE(pMember != nullptr);

    pMember->skills["FireMagic"] = {"FireMagic", 4, OpenYAMM::Game::SkillMastery::Normal};
    pMember->forgetSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt));
    pMember->skills.erase("AirMagic");
    pMember->forgetSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WizardEye));

    OpenYAMM::Game::InventoryItem fireBoltBook = {};
    fireBoltBook.objectDescriptionId = 401;

    const OpenYAMM::Game::InventoryItemUseResult successResult =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
            party,
            0,
            fireBoltBook,
            gameData.itemTable,
            &gameData.readableScrollTable);

    REQUIRE(successResult.speechId.has_value());
    CHECK_EQ(*successResult.speechId, OpenYAMM::Game::SpeechId::LearnSpell);
    CHECK(audioSystem.playSpeech(*pMember, *successResult.speechId, 0x1234u, 1u));

    OpenYAMM::Game::InventoryItem wizardEyeBook = {};
    wizardEyeBook.objectDescriptionId = 411;

    const OpenYAMM::Game::InventoryItemUseResult failureResult =
        OpenYAMM::Game::InventoryItemUseRuntime::useItemOnMember(
            party,
            0,
            wizardEyeBook,
            gameData.itemTable,
            &gameData.readableScrollTable);

    REQUIRE(failureResult.speechId.has_value());
    CHECK_EQ(*failureResult.speechId, OpenYAMM::Game::SpeechId::CantLearnSpell);
    CHECK(audioSystem.playSpeech(*pMember, *failureResult.speechId, 0x5678u, 1u));
    CHECK(audioSystem.playSpeech(*pMember, OpenYAMM::Game::SpeechId::StoreClosed, 0x9abcu, 1u));
}

TEST_CASE("damage speech audio resolves for all default seed members")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    OpenYAMM::Game::GameAudioSystem audioSystem;
    std::string failure;

    REQUIRE_MESSAGE(
        initializeRegressionAudioSystem(gameData, assetFileSystem, audioSystem, failure),
        failure.c_str());

    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        CAPTURE(memberIndex);

        OpenYAMM::Game::Character *pMember = party.member(memberIndex);
        REQUIRE(pMember != nullptr);

        CHECK_MESSAGE(
            audioSystem.playSpeech(
                *pMember,
                OpenYAMM::Game::SpeechId::DamageMinor,
                0x1000u + static_cast<uint32_t>(memberIndex),
                static_cast<uint32_t>(memberIndex + 1)),
            "DamageMinor speech did not resolve for member ",
            memberIndex);
        CHECK_MESSAGE(
            audioSystem.playSpeech(
                *pMember,
                OpenYAMM::Game::SpeechId::DamageMajor,
                0x2000u + static_cast<uint32_t>(memberIndex),
                static_cast<uint32_t>(memberIndex + 1)),
            "DamageMajor speech did not resolve for member ",
            memberIndex);
    }
}

TEST_CASE("damage speech audio resolves for roster seeded party members")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    OpenYAMM::Game::GameAudioSystem audioSystem;
    std::string failure;

    REQUIRE_MESSAGE(
        initializeRegressionAudioSystem(gameData, assetFileSystem, audioSystem, failure),
        failure.c_str());

    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);
    const std::array<uint32_t, 3> rosterIds = {11, 5, 4};

    for (size_t rosterIndex = 0; rosterIndex < rosterIds.size(); ++rosterIndex)
    {
        const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(rosterIds[rosterIndex]);

        REQUIRE(pRosterEntry != nullptr);
        REQUIRE(party.replaceMemberWithRosterEntry(rosterIndex + 1, *pRosterEntry));
    }

    for (size_t memberIndex = 1; memberIndex < party.members().size(); ++memberIndex)
    {
        CAPTURE(memberIndex);
        CAPTURE(rosterIds[memberIndex - 1]);

        OpenYAMM::Game::Character *pMember = party.member(memberIndex);
        REQUIRE(pMember != nullptr);

        CHECK_MESSAGE(
            audioSystem.playSpeech(
                *pMember,
                OpenYAMM::Game::SpeechId::DamageMinor,
                0x3000u + static_cast<uint32_t>(memberIndex),
                static_cast<uint32_t>(memberIndex + 1)),
            "DamageMinor speech did not resolve for roster seeded member ",
            memberIndex);
        CHECK_MESSAGE(
            audioSystem.playSpeech(
                *pMember,
                OpenYAMM::Game::SpeechId::DamageMajor,
                0x4000u + static_cast<uint32_t>(memberIndex),
                static_cast<uint32_t>(memberIndex + 1)),
            "DamageMajor speech did not resolve for roster seeded member ",
            memberIndex);
    }
}

TEST_CASE("ordinary damage queues minor speech reaction")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);
    const size_t memberIndex = party.activeMemberIndex();

    party.clearPendingAudioRequests();

    REQUIRE(party.applyDamageToMember(memberIndex, 5, ""));

    const std::vector<OpenYAMM::Game::Party::PendingAudioRequest> &requests = party.pendingAudioRequests();
    REQUIRE_EQ(requests.size(), 1u);
    CHECK_EQ(requests[0].kind, OpenYAMM::Game::Party::PendingAudioRequest::Kind::Speech);
    CHECK_EQ(requests[0].speechId, OpenYAMM::Game::SpeechId::DamageMinor);
}

TEST_CASE("major damage threshold queues minor and major speech reactions")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);
    const size_t memberIndex = party.activeMemberIndex();
    OpenYAMM::Game::Character *pMember = party.activeMember();

    REQUIRE(pMember != nullptr);

    pMember->health = pMember->maxHealth;
    party.clearPendingAudioRequests();

    const int damage = std::max(1, pMember->maxHealth - std::max(1, pMember->maxHealth / 4));

    REQUIRE(party.applyDamageToMember(memberIndex, damage, ""));

    const std::vector<OpenYAMM::Game::Party::PendingAudioRequest> &requests = party.pendingAudioRequests();
    REQUIRE_EQ(requests.size(), 2u);
    CHECK_EQ(requests[0].kind, OpenYAMM::Game::Party::PendingAudioRequest::Kind::Speech);
    CHECK_EQ(requests[0].speechId, OpenYAMM::Game::SpeechId::DamageMinor);
    CHECK_EQ(requests[1].kind, OpenYAMM::Game::Party::PendingAudioRequest::Kind::Speech);
    CHECK_EQ(requests[1].speechId, OpenYAMM::Game::SpeechId::DamageMajor);
}

TEST_CASE("damage minor speech ignores combat cooldown")
{
    OpenYAMM::Game::GameplayPortraitPresentationState presentationState = {};
    presentationState.memberSpeechCooldownUntilTicks = {1000u};
    presentationState.memberCombatSpeechCooldownUntilTicks = {4000u};

    CHECK(OpenYAMM::Game::canPlaySpeechReactionForPresentationState(
        presentationState,
        0,
        OpenYAMM::Game::SpeechId::DamageMinor,
        1500u));
}

TEST_CASE("damage major speech bypasses active speech cooldowns")
{
    OpenYAMM::Game::GameplayPortraitPresentationState presentationState = {};
    presentationState.memberSpeechCooldownUntilTicks = {4000u};
    presentationState.memberCombatSpeechCooldownUntilTicks = {4000u};

    CHECK(OpenYAMM::Game::canPlaySpeechReactionForPresentationState(
        presentationState,
        0,
        OpenYAMM::Game::SpeechId::DamageMajor,
        1500u));
}

TEST_CASE("damage impact sound request uses armor family mapping")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);
    OpenYAMM::Game::Character *pMember = party.activeMember();

    REQUIRE(pMember != nullptr);

    party.clearPendingAudioRequests();
    pMember->equipment.armor = 0;
    party.requestDamageImpactSoundForMember(party.activeMemberIndex());

    const std::vector<OpenYAMM::Game::Party::PendingAudioRequest> &unarmoredRequests = party.pendingAudioRequests();
    REQUIRE_EQ(unarmoredRequests.size(), 1u);
    CHECK_EQ(unarmoredRequests[0].kind, OpenYAMM::Game::Party::PendingAudioRequest::Kind::Sound);
    CHECK(isDullImpactSound(unarmoredRequests[0].soundId));

    const uint32_t chainArmorId = findFirstItemIdBySkillGroup(gameData.itemTable, "Chain");
    REQUIRE_NE(chainArmorId, 0u);

    party.clearPendingAudioRequests();
    pMember->equipment.armor = chainArmorId;
    party.requestDamageImpactSoundForMember(party.activeMemberIndex());

    const std::vector<OpenYAMM::Game::Party::PendingAudioRequest> &armoredRequests = party.pendingAudioRequests();
    REQUIRE_EQ(armoredRequests.size(), 1u);
    CHECK_EQ(armoredRequests[0].kind, OpenYAMM::Game::Party::PendingAudioRequest::Kind::Sound);
    CHECK(isMetalImpactSound(armoredRequests[0].soundId));
}

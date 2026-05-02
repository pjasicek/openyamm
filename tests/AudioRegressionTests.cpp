#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/TextTable.h"
#include "game/audio/GameAudioSystem.h"
#include "game/audio/SoundCatalog.h"
#include "game/audio/SoundIds.h"
#include "game/gameplay/GameplaySpeechRules.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"

#include "tests/RegressionGameData.h"

#include <SDL3/SDL.h>

#include <array>
#include <cctype>
#include <filesystem>
#include <string>
#include <unordered_set>
#include <vector>

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

std::vector<std::vector<std::string>> rowsFromTextTable(const OpenYAMM::Engine::TextTable &textTable)
{
    std::vector<std::vector<std::string>> rows;
    rows.reserve(textTable.getRowCount());

    for (size_t rowIndex = 0; rowIndex < textTable.getRowCount(); ++rowIndex)
    {
        rows.push_back(textTable.getRow(rowIndex));
    }

    return rows;
}

bool isUnsignedIntegerString(const std::string &value)
{
    if (value.empty())
    {
        return false;
    }

    for (const char character : value)
    {
        if (std::isdigit(static_cast<unsigned char>(character)) == 0)
        {
            return false;
        }
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
        REQUIRE(party.recruitRosterMember(*pRosterEntry));
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

TEST_CASE("speech catalog maps lich reaction voices from sound id blocks")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    std::string failure;

    REQUIRE_MESSAGE(initializeRegressionAssetFileSystem(assetFileSystem, failure), failure.c_str());

    const std::optional<std::string> engineSoundCatalogText =
        assetFileSystem.readTextFile("engine/data_tables/sounds.txt");
    REQUIRE(engineSoundCatalogText.has_value());

    const std::optional<OpenYAMM::Engine::TextTable> parsedEngineSoundCatalog =
        OpenYAMM::Engine::TextTable::parseTabSeparated(*engineSoundCatalogText);
    REQUIRE(parsedEngineSoundCatalog.has_value());

    OpenYAMM::Game::SoundCatalog soundCatalog;
    std::string errorMessage;
    REQUIRE(soundCatalog.loadFromScopedRows(
        rowsFromTextTable(*parsedEngineSoundCatalog),
        {},
        errorMessage));

    const std::optional<uint32_t> maleLichTrap =
        soundCatalog.pickSpeechSoundId(26, "disarm_trap", 0);
    const std::optional<uint32_t> femaleLichTrap =
        soundCatalog.pickSpeechSoundId(27, "disarm_trap", 0);
    const std::optional<uint32_t> ordinaryVoiceTrap =
        soundCatalog.pickSpeechSoundId(1, "disarm_trap", 2);

    REQUIRE(maleLichTrap.has_value());
    REQUIRE(femaleLichTrap.has_value());
    REQUIRE(ordinaryVoiceTrap.has_value());
    CHECK_EQ(*maleLichTrap, 7600);
    CHECK_EQ(*femaleLichTrap, 7700);
    CHECK(*ordinaryVoiceTrap < 5200);
}

TEST_CASE("sound catalog scopes world monster sounds independently from engine sounds")
{
    OpenYAMM::Game::SoundCatalog soundCatalog;
    std::string errorMessage;

    const std::vector<std::vector<std::string>> engineRows = {
        {"click", "19", "system", "0"},
        {"engine shared", "1000", "0", "0"},
    };
    const std::vector<std::vector<std::string>> worldRows = {
        {"monster attack", "1000", "0", "0"},
    };

    REQUIRE(soundCatalog.loadFromScopedRows(engineRows, worldRows, errorMessage));
    REQUIRE(soundCatalog.findById(19) != nullptr);
    REQUIRE(soundCatalog.findById(OpenYAMM::Game::engineSound(1000)) != nullptr);
    REQUIRE(soundCatalog.findById(OpenYAMM::Game::worldSound(1000)) != nullptr);

    const std::vector<std::vector<std::string>> duplicateWorldRows = {
        {"monster attack", "1000", "0", "0"},
        {"duplicate monster attack", "1000", "0", "0"},
    };

    CHECK_FALSE(soundCatalog.loadFromScopedRows(engineRows, duplicateWorldRows, errorMessage));
    CHECK(errorMessage.find("duplicate world sound id 1000") != std::string::npos);
}

TEST_CASE("sound catalog resolves flat sound rows against engine and world audio files")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    std::string failure;

    REQUIRE_MESSAGE(initializeRegressionAssetFileSystem(assetFileSystem, failure), failure.c_str());

    const std::optional<std::string> engineSoundCatalogText =
        assetFileSystem.readTextFile("engine/data_tables/sounds.txt");
    REQUIRE(engineSoundCatalogText.has_value());

    const std::optional<OpenYAMM::Engine::TextTable> parsedEngineSoundCatalog =
        OpenYAMM::Engine::TextTable::parseTabSeparated(*engineSoundCatalogText);
    REQUIRE(parsedEngineSoundCatalog.has_value());

    OpenYAMM::Game::SoundCatalog soundCatalog;
    std::string errorMessage;
    REQUIRE(soundCatalog.loadFromScopedRows(
        rowsFromTextTable(*parsedEngineSoundCatalog),
        {},
        errorMessage));
    soundCatalog.initializeVirtualPathIndex(assetFileSystem);

    const std::optional<std::string> enginePath = soundCatalog.buildVirtualPath(19);
    const std::optional<std::string> worldMonsterPath =
        soundCatalog.buildVirtualPath(OpenYAMM::Game::worldSound(1000));
    const std::optional<std::string> worldHousePath =
        soundCatalog.buildVirtualPath(OpenYAMM::Game::worldSound(30101));
    const std::optional<std::string> flatHousePath =
        soundCatalog.buildVirtualPath(OpenYAMM::Game::engineSound(30101));

    REQUIRE(enginePath.has_value());
    REQUIRE(worldMonsterPath.has_value());
    REQUIRE(worldHousePath.has_value());
    REQUIRE(flatHousePath.has_value());
    CHECK(enginePath->starts_with("audio/"));
    CHECK(worldMonsterPath->starts_with("audio/"));
    CHECK(worldHousePath->starts_with("audio/"));
    CHECK(flatHousePath->starts_with("audio/"));
    CHECK(assetFileSystem.exists(*enginePath));
    CHECK(assetFileSystem.exists(*worldMonsterPath));
    CHECK(assetFileSystem.exists(*worldHousePath));
    CHECK(assetFileSystem.exists(*flatHousePath));
}

TEST_CASE("sound catalog resolves registered physical audio through merged audio namespace")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    std::string failure;

    REQUIRE_MESSAGE(initializeRegressionAssetFileSystem(assetFileSystem, failure), failure.c_str());

    const std::optional<std::string> engineSoundCatalogText =
        assetFileSystem.readTextFile("engine/data_tables/sounds.txt");
    REQUIRE(engineSoundCatalogText.has_value());

    const std::optional<OpenYAMM::Engine::TextTable> parsedEngineSoundCatalog =
        OpenYAMM::Engine::TextTable::parseTabSeparated(*engineSoundCatalogText);
    REQUIRE(parsedEngineSoundCatalog.has_value());

    OpenYAMM::Game::SoundCatalog soundCatalog;
    std::string errorMessage;
    REQUIRE(soundCatalog.loadFromScopedRows(
        rowsFromTextTable(*parsedEngineSoundCatalog),
        {},
        errorMessage));
    soundCatalog.initializeVirtualPathIndex(assetFileSystem);

    std::unordered_set<uint32_t> checkedSoundIds;
    size_t resolvedSoundCount = 0;

    for (size_t rowIndex = 0; rowIndex < parsedEngineSoundCatalog->getRowCount(); ++rowIndex)
    {
        const std::vector<std::string> row = parsedEngineSoundCatalog->getRow(rowIndex);

        if (row.size() < 2 || row[0].empty() || row[0][0] == '/')
        {
            continue;
        }

        if (!isUnsignedIntegerString(row[1]))
        {
            continue;
        }

        const uint32_t soundId = static_cast<uint32_t>(std::stoul(row[1]));

        if (soundId == 0 || !checkedSoundIds.insert(soundId).second)
        {
            continue;
        }

        const std::string audioPath = "Data/EnglishD/" + row[0] + ".wav";

        if (!assetFileSystem.exists(audioPath))
        {
            continue;
        }

        const std::optional<std::string> resolvedPath = soundCatalog.buildVirtualPath(soundId);
        REQUIRE_MESSAGE(resolvedPath.has_value(), row[0].c_str());
        CHECK_MESSAGE(resolvedPath->starts_with("audio/"), resolvedPath->c_str());
        CHECK_MESSAGE(assetFileSystem.exists(*resolvedPath), resolvedPath->c_str());
        ++resolvedSoundCount;
    }

    CHECK(resolvedSoundCount > 7000);
}

TEST_CASE("monster descriptor sound ids resolve through merged sound registry")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    std::string failure;

    REQUIRE_MESSAGE(initializeRegressionAssetFileSystem(assetFileSystem, failure), failure.c_str());

    const std::optional<std::string> engineSoundCatalogText =
        assetFileSystem.readTextFile("engine/data_tables/sounds.txt");
    REQUIRE(engineSoundCatalogText.has_value());

    const std::optional<OpenYAMM::Engine::TextTable> parsedEngineSoundCatalog =
        OpenYAMM::Engine::TextTable::parseTabSeparated(*engineSoundCatalogText);
    REQUIRE(parsedEngineSoundCatalog.has_value());

    const std::optional<std::string> monsterDescriptorText =
        assetFileSystem.readTextFile("engine/data_tables/monster_descriptors.txt");
    REQUIRE(monsterDescriptorText.has_value());

    const std::optional<OpenYAMM::Engine::TextTable> parsedMonsterDescriptors =
        OpenYAMM::Engine::TextTable::parseTabSeparated(*monsterDescriptorText);
    REQUIRE(parsedMonsterDescriptors.has_value());

    OpenYAMM::Game::SoundCatalog soundCatalog;
    std::string errorMessage;
    REQUIRE(soundCatalog.loadFromScopedRows(
        rowsFromTextTable(*parsedEngineSoundCatalog),
        {},
        errorMessage));
    soundCatalog.initializeVirtualPathIndex(assetFileSystem);

    std::unordered_set<uint32_t> checkedMonsterSoundIds;

    for (size_t rowIndex = 0; rowIndex < parsedMonsterDescriptors->getRowCount(); ++rowIndex)
    {
        const std::vector<std::string> row = parsedMonsterDescriptors->getRow(rowIndex);

        if (row.size() < 11 || !isUnsignedIntegerString(row[0]))
        {
            continue;
        }

        for (size_t columnIndex = 7; columnIndex <= 10; ++columnIndex)
        {
            if (row[columnIndex].empty())
            {
                continue;
            }

            if (!isUnsignedIntegerString(row[columnIndex]))
            {
                continue;
            }

            const uint32_t soundId = static_cast<uint32_t>(std::stoul(row[columnIndex]));

            if (soundId == 0 || !checkedMonsterSoundIds.insert(soundId).second)
            {
                continue;
            }

            const std::optional<std::string> resolvedPath = soundCatalog.buildVirtualPath(soundId);
            REQUIRE_MESSAGE(resolvedPath.has_value(), row[columnIndex].c_str());
            CHECK_MESSAGE(resolvedPath->starts_with("audio/"), resolvedPath->c_str());
            CHECK_MESSAGE(assetFileSystem.exists(*resolvedPath), resolvedPath->c_str());
        }
    }

    CHECK(checkedMonsterSoundIds.size() > 700);
}

TEST_CASE("lich character speech audio resolves from character data voice ids")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    OpenYAMM::Game::GameAudioSystem audioSystem;
    std::string failure;

    REQUIRE_MESSAGE(
        initializeRegressionAudioSystem(gameData, assetFileSystem, audioSystem, failure),
        failure.c_str());

    OpenYAMM::Game::Character maleLich = {};
    maleLich.characterDataId = 27;

    OpenYAMM::Game::Character femaleLich = {};
    femaleLich.characterDataId = 28;

    CHECK(audioSystem.playSpeech(maleLich, OpenYAMM::Game::SpeechId::DamageMinor, 0x5100u, 1u));
    CHECK(audioSystem.playSpeech(femaleLich, OpenYAMM::Game::SpeechId::DamageMinor, 0x5200u, 2u));
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

TEST_CASE("debug damage immunity still queues damage speech reaction")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);
    const size_t memberIndex = party.activeMemberIndex();
    const OpenYAMM::Game::Character *pMember = party.member(memberIndex);

    REQUIRE(pMember != nullptr);
    const int initialHealth = pMember->health;

    party.setDebugDamageImmune(true);
    party.clearPendingAudioRequests();

    REQUIRE(party.applyDamageToMember(memberIndex, 5, ""));
    CHECK_EQ(pMember->health, initialHealth);

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

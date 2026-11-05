#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/AudioSpatialization.h"
#include "engine/TextTable.h"
#include "game/audio/GameAudioSystem.h"
#include "game/audio/MusicStream.h"
#include "game/audio/ActorAudioRules.h"
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
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <numbers>
#include <string>
#include <thread>
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

TEST_CASE("registered audio clips can be released from the decode cache")
{
    OpenYAMM::Engine::AudioSystem audioSystem;
    std::vector<float> samples(32, 0.25f);

    REQUIRE(audioSystem.registerClip("test-release", std::move(samples)));
    CHECK_EQ(audioSystem.cacheStats().clipCount, 1);
    CHECK_EQ(audioSystem.cacheStats().sampleBytes, 32 * sizeof(float));
    CHECK(audioSystem.releaseClip("test-release"));
    CHECK_EQ(audioSystem.cacheStats().clipCount, 0);
    CHECK_EQ(audioSystem.cacheStats().sampleBytes, 0);
    CHECK_FALSE(audioSystem.releaseClip("test-release"));
}

// Reads frameCount frames as the mixer would, waiting while the stream's decoder catches up.
std::vector<float> readMusicStream(OpenYAMM::Game::MusicStream &stream, uint32_t frameCount)
{
    std::vector<float> samples;
    std::vector<float> chunk(1024 * 2);

    for (int idleReads = 0; samples.size() / 2 < frameCount && idleReads < 20000;)
    {
        const uint32_t wanted = std::min<uint32_t>(1024, frameCount - uint32_t(samples.size() / 2));
        const uint32_t read = stream.read(chunk.data(), wanted);

        if (read == 0)
        {
            ++idleReads;
            std::this_thread::sleep_for(std::chrono::microseconds(100));
            continue;
        }

        idleReads = 0;
        samples.insert(samples.end(), chunk.begin(), chunk.begin() + read * 2);
    }

    return samples;
}

class SilentStreamSource : public OpenYAMM::Engine::AudioStreamSource
{
public:
    uint32_t read(float *pSamples, uint32_t frameCount) override
    {
        std::fill(pSamples, pSamples + frameCount * 2, 0.0f);
        return frameCount;
    }

    bool finished() const override
    {
        return false;
    }
};

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

    if (!audioSystem.initialize(
            assetFileSystem,
            gameData.characterDollTable,
            gameData.mergedCharacterVoiceTable))
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

std::string toLowerAsciiCopy(std::string value)
{
    for (char &character : value)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return value;
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

TEST_CASE("audio starts on the silent dummy driver when no playback device opens")
{
    // SDL_Quit frees the environment, so it is fetched after each quit.
    SDL_Quit();
    REQUIRE(SDL_SetEnvironmentVariable(SDL_GetEnvironment(), "SDL_AUDIODRIVER", "no_such_driver", true));

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    std::string failure;
    REQUIRE_MESSAGE(initializeRegressionAssetFileSystem(assetFileSystem, failure), failure);

    OpenYAMM::Engine::AudioSystem audioSystem;
    CHECK(audioSystem.initialize(assetFileSystem));
    const char *pDriver = SDL_GetCurrentAudioDriver();
    REQUIRE(pDriver != nullptr);
    CHECK_EQ(std::string(pDriver), "dummy");

    audioSystem.shutdown();
    SDL_ResetHint(SDL_HINT_AUDIO_DRIVER);
    SDL_Quit();
    CHECK(SDL_SetEnvironmentVariable(SDL_GetEnvironment(), "SDL_AUDIODRIVER", "dummy", true));
}

TEST_CASE("music streams decode a track the same way every time")
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm7/music/32.mp3",
        std::ios::binary);
    REQUIRE(file);
    const std::shared_ptr<const std::vector<uint8_t>> pTrack = std::make_shared<const std::vector<uint8_t>>(
        std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
    OpenYAMM::Game::MusicStream first(pTrack);
    OpenYAMM::Game::MusicStream second(pTrack);
    const std::vector<float> firstSamples = readMusicStream(first, 96000);
    const std::vector<float> secondSamples = readMusicStream(second, 96000);

    REQUIRE_EQ(firstSamples.size(), 96000 * 2);
    CHECK(firstSamples == secondSamples);
    CHECK(std::any_of(firstSamples.begin(), firstSamples.end(), [](float sample) { return sample != 0.0f; }));
    CHECK_FALSE(first.finished());
}

TEST_CASE("a music stream that cannot be decoded finishes")
{
    OpenYAMM::Game::MusicStream stream(std::make_shared<const std::vector<uint8_t>>(4096, uint8_t(0)));

    for (int attempt = 0; attempt < 2000 && !stream.finished(); ++attempt)
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }

    CHECK(stream.finished());
}

TEST_CASE("streams play until stopped like clips")
{
    OpenYAMM::Engine::AudioSystem audioSystem;
    const uint64_t instanceId = audioSystem.playStream(std::make_shared<SilentStreamSource>(), {});

    REQUIRE_NE(instanceId, 0);
    CHECK(audioSystem.isClipPlaying(instanceId));
    audioSystem.stopClip(instanceId);
    CHECK_FALSE(audioSystem.isClipPlaying(instanceId));
    CHECK_EQ(audioSystem.playStream(nullptr, {}), 0);
}

TEST_CASE("background music pause remains active across cutscene track requests")
{
    OpenYAMM::Game::GameAudioSystem audioSystem;

    CHECK_FALSE(audioSystem.isBackgroundMusicPaused());
    audioSystem.pauseBackgroundMusic();
    CHECK(audioSystem.isBackgroundMusicPaused());

    audioSystem.setBackgroundMusicTrack(3);
    CHECK(audioSystem.isBackgroundMusicPaused());

    audioSystem.resumeBackgroundMusic();
    CHECK_FALSE(audioSystem.isBackgroundMusicPaused());
}

TEST_CASE("spell and Arcomage sounds load on demand from an empty cache")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    OpenYAMM::Game::GameAudioSystem audioSystem;
    std::string failure;

    REQUIRE_MESSAGE(
        initializeRegressionAudioSystem(gameData, assetFileSystem, audioSystem, failure),
        failure.c_str());
    CHECK_EQ(audioSystem.cacheStats().clipCount, 0);
    CHECK_EQ(audioSystem.cacheStats().sampleBytes, 0);

    const OpenYAMM::Game::SpellEntry *pFireBolt =
        gameData.spellTable.findById(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt));
    REQUIRE(pFireBolt != nullptr);
    REQUIRE(pFireBolt->effectSoundId > 0);
    REQUIRE(audioSystem.playSound(
        static_cast<uint32_t>(pFireBolt->effectSoundId),
        OpenYAMM::Game::GameAudioSystem::PlaybackGroup::Ui));

    const OpenYAMM::Engine::AudioSystem::CacheStats spellCacheStats = audioSystem.cacheStats();
    CHECK_EQ(spellCacheStats.clipCount, 1);
    CHECK(spellCacheStats.sampleBytes > 0);

    REQUIRE(audioSystem.playCommonSound(
        OpenYAMM::Game::SoundId::ArcomageDeal,
        OpenYAMM::Game::GameAudioSystem::PlaybackGroup::Ui));

    const OpenYAMM::Engine::AudioSystem::CacheStats arcomageCacheStats = audioSystem.cacheStats();
    CHECK_EQ(arcomageCacheStats.clipCount, 2);
    CHECK(arcomageCacheStats.sampleBytes > spellCacheStats.sampleBytes);
    audioSystem.shutdown();
}

TEST_CASE("map music starts after replacing an in-flight menu music decode")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    OpenYAMM::Game::GameAudioSystem audioSystem;
    std::string failure;

    REQUIRE_MESSAGE(
        initializeRegressionAudioSystem(gameData, assetFileSystem, audioSystem, failure),
        failure.c_str());

    audioSystem.setBackgroundMusicTrack(14);
    audioSystem.stopBackgroundMusicImmediate();
    audioSystem.setBackgroundMusicTrack(38);

    constexpr int MaxUpdateAttempts = 10000;

    for (int attempt = 0;
         attempt < MaxUpdateAttempts && audioSystem.currentBackgroundMusicTrack() != 38;
         ++attempt)
    {
        audioSystem.update(0.0f, 0.0f, 0.0f, 0.001f);
        SDL_Delay(1);
    }

    CHECK_EQ(audioSystem.currentBackgroundMusicTrack(), 38);
    audioSystem.shutdown();
}

TEST_CASE("MM9 namespaced map music decodes and starts through the shared player")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    OpenYAMM::Game::GameAudioSystem audioSystem;
    std::string failure;

    REQUIRE_MESSAGE(
        initializeRegressionAudioSystem(gameData, assetFileSystem, audioSystem, failure),
        failure.c_str());

    audioSystem.setBackgroundMusicTrack(90007);
    constexpr int MaxUpdateAttempts = 10000;

    for (int attempt = 0;
         attempt < MaxUpdateAttempts && audioSystem.currentBackgroundMusicTrack() != 90007;
         ++attempt)
    {
        audioSystem.update(0.0f, 0.0f, 0.0f, 0.001f);
        SDL_Delay(1);
    }

    CHECK_EQ(audioSystem.currentBackgroundMusicTrack(), 90007);
    audioSystem.shutdown();
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

TEST_CASE("character voice table maps lich reaction voices directly")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    std::string failure;

    REQUIRE_MESSAGE(initializeRegressionAssetFileSystem(assetFileSystem, failure), failure.c_str());

    const std::optional<std::string> characterVoiceText =
        assetFileSystem.readTextFile("engine/data_tables/character_voices.txt");
    REQUIRE(characterVoiceText.has_value());

    const std::optional<OpenYAMM::Engine::TextTable> parsedCharacterVoices =
        OpenYAMM::Engine::TextTable::parseTabSeparated(*characterVoiceText);
    REQUIRE(parsedCharacterVoices.has_value());

    OpenYAMM::Game::MergedCharacterVoiceTable characterVoiceTable;
    REQUIRE(characterVoiceTable.loadFromRows(rowsFromTextTable(*parsedCharacterVoices)));

    const std::vector<uint32_t> maleLichTrap =
        characterVoiceTable.soundIdsForTypes(26, {"Disarmed"});
    const std::vector<uint32_t> femaleLichTrap =
        characterVoiceTable.soundIdsForTypes(27, {"Disarmed"});
    const std::vector<uint32_t> ordinaryVoiceTrap =
        characterVoiceTable.soundIdsForTypes(1, {"Disarmed"});

    REQUIRE_FALSE(maleLichTrap.empty());
    REQUIRE_FALSE(femaleLichTrap.empty());
    REQUIRE_FALSE(ordinaryVoiceTrap.empty());
    CHECK_EQ(maleLichTrap[0], 7600);
    CHECK_EQ(femaleLichTrap[0], 7700);
    CHECK_EQ(ordinaryVoiceTrap[0], 5100);
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

    std::unordered_set<std::string> audioFileNamesByLowerName;
    for (const std::string &entry : assetFileSystem.enumerate("audio"))
    {
        const std::string lowerEntry = toLowerAsciiCopy(entry);

        if (lowerEntry.size() >= 5 && lowerEntry.substr(lowerEntry.size() - 4) == ".wav")
        {
            audioFileNamesByLowerName.insert(lowerEntry);
        }
    }

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

        const std::string audioFileName = toLowerAsciiCopy(row[0] + ".wav");
        if (audioFileNamesByLowerName.find(audioFileName) == audioFileNamesByLowerName.end())
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

TEST_CASE("lich item inspection speech audio resolves for identify and repair outcomes")
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

    const std::array<OpenYAMM::Game::SpeechId, 5> itemInspectionSpeechIds = {{
        OpenYAMM::Game::SpeechId::IdentifyWeakItem,
        OpenYAMM::Game::SpeechId::IdentifyGreatItem,
        OpenYAMM::Game::SpeechId::IdentifyFailItem,
        OpenYAMM::Game::SpeechId::RepairSuccess,
        OpenYAMM::Game::SpeechId::RepairFail,
    }};

    for (size_t reactionIndex = 0; reactionIndex < itemInspectionSpeechIds.size(); ++reactionIndex)
    {
        CAPTURE(reactionIndex);
        CHECK(audioSystem.playSpeech(
            maleLich,
            itemInspectionSpeechIds[reactionIndex],
            0x5300u + static_cast<uint32_t>(reactionIndex),
            1u));
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

namespace
{
size_t countSpeech(const OpenYAMM::Game::Party &party, size_t memberIndex, OpenYAMM::Game::SpeechId speechId)
{
    size_t count = 0;

    for (const OpenYAMM::Game::Party::PendingAudioRequest &request : party.pendingAudioRequests())
    {
        if (request.kind == OpenYAMM::Game::Party::PendingAudioRequest::Kind::Speech
            && request.memberIndex == memberIndex
            && request.speechId == speechId)
        {
            ++count;
        }
    }

    return count;
}
}

TEST_CASE("an unconscious member hit by area damage queues no dying speech")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);
    const size_t memberIndex = party.activeMemberIndex();
    OpenYAMM::Game::Character *pMember = party.activeMember();

    REQUIRE(pMember != nullptr);

    pMember->health = -5;
    pMember->conditions.set(size_t(OpenYAMM::Game::CharacterCondition::Unconscious));
    party.clearPendingAudioRequests();

    REQUIRE(party.applyDamageToMember(memberIndex, 5, "", true));
    CHECK_LT(pMember->health, -5);

    for (const OpenYAMM::Game::Party::PendingAudioRequest &request : party.pendingAudioRequests())
    {
        CHECK_FALSE((request.kind == OpenYAMM::Game::Party::PendingAudioRequest::Kind::Speech
            && request.memberIndex == memberIndex));
    }
}

TEST_CASE("dying speech is queued once, when health crosses zero")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);
    const size_t memberIndex = party.activeMemberIndex();
    OpenYAMM::Game::Character *pMember = party.activeMember();

    REQUIRE(pMember != nullptr);

    pMember->health = 3;
    party.clearPendingAudioRequests();

    REQUIRE(party.applyDamageToMember(memberIndex, 10, ""));
    CHECK_EQ(countSpeech(party, memberIndex, OpenYAMM::Game::SpeechId::Dying), 1u);
    CHECK_EQ(countSpeech(party, memberIndex, OpenYAMM::Game::SpeechId::DamageMinor), 0u);
}

TEST_CASE("falling speech needs a member who could act before the fall")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeAudioRegressionParty(gameData);
    const size_t memberIndex = party.activeMemberIndex();
    OpenYAMM::Game::Character *pMember = party.activeMember();

    REQUIRE(pMember != nullptr);

    pMember->health = pMember->maxHealth;
    party.clearPendingAudioRequests();
    REQUIRE(party.applyDamageToMember(memberIndex, 1, "falling"));
    CHECK_EQ(countSpeech(party, memberIndex, OpenYAMM::Game::SpeechId::Falling), 1u);

    pMember->conditions.set(size_t(OpenYAMM::Game::CharacterCondition::Asleep));
    party.clearPendingAudioRequests();
    REQUIRE(party.applyDamageToMember(memberIndex, 1, "falling"));
    CHECK_EQ(countSpeech(party, memberIndex, OpenYAMM::Game::SpeechId::Falling), 0u);
}

TEST_CASE("incapacitated members only speak about their state")
{
    using OpenYAMM::Game::CharacterCondition;
    using OpenYAMM::Game::SpeechId;
    using OpenYAMM::Game::canMemberSpeak;
    OpenYAMM::Game::Character healthy;
    healthy.maxHealth = 50;
    healthy.health = 50;

    for (SpeechId speechId : {SpeechId::AttackHit, SpeechId::KillWeakEnemy, SpeechId::Falling, SpeechId::Dying,
             SpeechId::CheatedDeath, SpeechId::Awaken, SpeechId::DamageMinor})
    {
        CAPTURE(uint32_t(speechId));
        CHECK(canMemberSpeak(healthy, speechId));
    }

    OpenYAMM::Game::Character unconscious = healthy;
    unconscious.health = -3;
    unconscious.conditions.set(size_t(CharacterCondition::Unconscious));
    CHECK_FALSE(canMemberSpeak(unconscious, SpeechId::AttackHit));
    CHECK_FALSE(canMemberSpeak(unconscious, SpeechId::KillWeakEnemy));
    CHECK_FALSE(canMemberSpeak(unconscious, SpeechId::DamageMinor));
    CHECK(canMemberSpeak(unconscious, SpeechId::Dying));
    CHECK(canMemberSpeak(unconscious, SpeechId::CheatedDeath));
    CHECK(canMemberSpeak(unconscious, SpeechId::Awaken));

    OpenYAMM::Game::Character asleep = healthy;
    asleep.conditions.set(size_t(CharacterCondition::Asleep));
    CHECK_FALSE(canMemberSpeak(asleep, SpeechId::AttackMiss));
    CHECK(canMemberSpeak(asleep, SpeechId::Awaken));

    for (CharacterCondition condition :
        {CharacterCondition::Dead, CharacterCondition::Petrified, CharacterCondition::Eradicated})
    {
        OpenYAMM::Game::Character member = healthy;
        member.conditions.set(size_t(condition));
        CAPTURE(size_t(condition));
        CHECK_FALSE(canMemberSpeak(member, SpeechId::Awaken));
        CHECK_FALSE(canMemberSpeak(member, SpeechId::KillStrongEnemy));
    }
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

TEST_CASE("item inspection speech bypasses active speech cooldowns")
{
    OpenYAMM::Game::GameplayPortraitPresentationState presentationState = {};
    presentationState.memberSpeechCooldownUntilTicks = {4000u};
    presentationState.memberCombatSpeechCooldownUntilTicks = {4000u};

    const std::array<OpenYAMM::Game::SpeechId, 5> itemInspectionSpeechIds = {{
        OpenYAMM::Game::SpeechId::IdentifyWeakItem,
        OpenYAMM::Game::SpeechId::IdentifyGreatItem,
        OpenYAMM::Game::SpeechId::IdentifyFailItem,
        OpenYAMM::Game::SpeechId::RepairSuccess,
        OpenYAMM::Game::SpeechId::RepairFail,
    }};

    for (const OpenYAMM::Game::SpeechId speechId : itemInspectionSpeechIds)
    {
        CAPTURE(static_cast<uint32_t>(speechId));
        CHECK(OpenYAMM::Game::canPlaySpeechReactionForPresentationState(
            presentationState,
            0,
            speechId,
            1500u));
    }
}

TEST_CASE("repeated voice line interval holds back only the same line of the same member")
{
    using OpenYAMM::Game::SpeechId;
    using OpenYAMM::Game::isRepeatedSpeechReaction;

    OpenYAMM::Game::GameplayPortraitPresentationState presentationState = {};
    presentationState.memberSpeechLastPlayedTicks.resize(2);
    presentationState.memberSpeechLastPlayedTicks[0][SpeechId::DamageMinor] = 1000u;

    // Off: every repeat plays, as before the setting.
    CHECK_FALSE(isRepeatedSpeechReaction(presentationState, 0, SpeechId::DamageMinor, 1001u, 0u));

    CHECK(isRepeatedSpeechReaction(presentationState, 0, SpeechId::DamageMinor, 1999u, 1000u));
    CHECK_FALSE(isRepeatedSpeechReaction(presentationState, 0, SpeechId::DamageMinor, 2000u, 1000u));
    CHECK_FALSE(isRepeatedSpeechReaction(presentationState, 0, SpeechId::DamageMajor, 1500u, 1000u));
    CHECK_FALSE(isRepeatedSpeechReaction(presentationState, 1, SpeechId::DamageMinor, 1500u, 1000u));
    CHECK_FALSE(isRepeatedSpeechReaction(presentationState, 4, SpeechId::DamageMinor, 1500u, 1000u));

    // The tick counter wrapping past zero still measures the interval.
    presentationState.memberSpeechLastPlayedTicks[0][SpeechId::RepairSuccess] = 0xffffff00u;
    CHECK(isRepeatedSpeechReaction(presentationState, 0, SpeechId::RepairSuccess, 0x100u, 1000u));
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

TEST_CASE("actor audio uses MM8 integer distance and inclusive 8192 boundary")
{
    using OpenYAMM::Game::actorVoiceVolume;
    CHECK_EQ(actorVoiceVolume(0, 0, 0), 114);
    CHECK_EQ(actorVoiceVolume(4096, 0, 0), 64);
    CHECK_EQ(actorVoiceVolume(0, 0, -4096), 64);
    CHECK_EQ(actorVoiceVolume(4096, 4096, 4096), 35);
    CHECK_EQ(actorVoiceVolume(-4096, 4096, -4096), 35);
    CHECK_EQ(actorVoiceVolume(6144, 6144, 0), 0);
    CHECK_EQ(actorVoiceVolume(8191, 0, 0), 15);
    CHECK_EQ(actorVoiceVolume(8192, 0, 0), 14);
    CHECK_EQ(actorVoiceVolume(8193, 0, 0), 0);
    CHECK_EQ(actorVoiceVolume(0, -8192, 0), 14);
    CHECK_EQ(actorVoiceVolume(0, 0, 8193), 0);
    CHECK_EQ(actorVoiceVolume(8192, 0, 4), 0);
    CHECK_EQ(actorVoiceVolume(1000000000, 0, 0), 0);
}

TEST_CASE("positional audio rotates with listener yaw and preserves relative bearing")
{
    using OpenYAMM::Engine::positionalAudioPan;
    constexpr float pi = std::numbers::pi_v<float>;
    CHECK(positionalAudioPan(0, -100, 0) == doctest::Approx(1));
    CHECK(positionalAudioPan(0, -100, pi) == doctest::Approx(-1));
    CHECK(positionalAudioPan(100, 0, 0) == doctest::Approx(0));
    CHECK(positionalAudioPan(-100, 0, 0) == doctest::Approx(0));
    CHECK(positionalAudioPan(0, 100, pi / 2) == doctest::Approx(0).epsilon(0.0001));
    CHECK(positionalAudioPan(0, 0, pi) == doctest::Approx(0));
    CHECK(positionalAudioPan(1300 - 1200, 4200 - 4000, 0.75f)
        == doctest::Approx(positionalAudioPan(100, 200, 0.75f)));
    CHECK(positionalAudioPan(100, 200, 0.75f)
        == doctest::Approx(positionalAudioPan(1000, 2000, 0.75f)));
}

TEST_CASE("actor audio uses verified Shrink powers without undefined pitch")
{
    using OpenYAMM::Game::actorVoicePitch;
    CHECK_EQ(actorVoicePitch(0, 0.25f), 1.0f);
    CHECK_EQ(actorVoicePitch(10, 0.5f), 1.5f);
    CHECK_EQ(actorVoicePitch(10, 1.0f / 3), 2.0f);
    CHECK_EQ(actorVoicePitch(10, 0.25f), 2.5f);
    CHECK_EQ(actorVoicePitch(10, 1), 1.0f);
    CHECK_EQ(actorVoicePitch(10, 0), 1.0f);
}

TEST_CASE("actor audio owns four moving voices and replaces only quieter actors")
{
    using OpenYAMM::Game::GameAudioSystem;
    using OpenYAMM::Game::worldSound;
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    GameAudioSystem audio;
    std::string failure;
    REQUIRE_MESSAGE(initializeRegressionAudioSystem(gameData, assetFileSystem, audio, failure), failure.c_str());

    const uint64_t first = audio.playActorSound(0, worldSound(1030), {100, 0, 0});
    REQUIRE(first != 0);
    CHECK_EQ(audio.playActorSound(0, worldSound(1030), {100, 0, 0}), first);
    const uint64_t replacement = audio.playActorSound(0, worldSound(1031), {100, 0, 0});
    REQUIRE(replacement != 0);
    CHECK_NE(replacement, first);
    CHECK_FALSE(audio.isSoundInstancePlaying(first));

    const uint64_t second = audio.playActorSound(1, worldSound(1030), {2000, 0, 0});
    const uint64_t third = audio.playActorSound(2, worldSound(1030), {4000, 0, 0});
    const uint64_t fourth = audio.playActorSound(3, worldSound(1030), {6000, 0, 0});
    REQUIRE(second != 0);
    REQUIRE(third != 0);
    REQUIRE(fourth != 0);
    CHECK_NE(second, third);
    CHECK_EQ(audio.playActorSound(4, worldSound(1030), {6000, 0, 0}), 0);
    CHECK_EQ(audio.playActorSound(4, worldSound(1030), {7000, 0, 0}), 0);
    CHECK_EQ(audio.playActorSound(4, worldSound(1030), {8193, 0, 0}), 0);
    const uint64_t nearer = audio.playActorSound(4, worldSound(1030), {1000, 0, 0});
    REQUIRE(nearer != 0);
    CHECK_FALSE(audio.isSoundInstancePlaying(fourth));
    CHECK(audio.isSoundInstancePlaying(third));

    audio.updateActorVoices({}, [](size_t index) -> std::optional<GameAudioSystem::WorldPosition>
    {
        if (index == 1)
        {
            return std::nullopt;
        }
        return GameAudioSystem::WorldPosition{index == 0 ? 8193.0f : 8192.0f, 0, 0};
    });
    CHECK_FALSE(audio.isSoundInstancePlaying(replacement));
    CHECK_FALSE(audio.isSoundInstancePlaying(second));
    CHECK(audio.isSoundInstancePlaying(third));
    CHECK(audio.isSoundInstancePlaying(nearer));

    const uint64_t ui = audio.playSoundInstance(worldSound(1030), GameAudioSystem::PlaybackGroup::Ui, {}, false);
    REQUIRE(ui != 0);
    audio.beginMapSoundPreload();
    CHECK_FALSE(audio.isSoundInstancePlaying(third));
    CHECK_FALSE(audio.isSoundInstancePlaying(nearer));
    CHECK(audio.isSoundInstancePlaying(ui));
    audio.endMapSoundPreload();
    CHECK(audio.playActorSound(0, worldSound(1030), {8192, 0, 0}) != 0);
    audio.stopAllPlayback();
    CHECK_FALSE(audio.isSoundInstancePlaying(ui));
}

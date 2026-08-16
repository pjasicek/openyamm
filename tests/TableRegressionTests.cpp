#include "doctest/doctest.h"

#include "engine/TextTable.h"
#include "game/app/GameSettings.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpriteTables.h"

#include "tests/RegressionGameData.h"

#include <cctype>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <set>
#include <sstream>
#include <vector>

namespace
{
TEST_CASE("merged class display names hide mechanics keys")
{
    CHECK_EQ(OpenYAMM::Game::displayClassName("GreatWyrm"), "Great Wyrm");
    CHECK_EQ(OpenYAMM::Game::displayClassName("Great Wyrm"), "Great Wyrm");
    CHECK_EQ(OpenYAMM::Game::displayClassName("PriestLight"), "Priest of the Light");
    CHECK_EQ(OpenYAMM::Game::displayClassName("Priest of the Light"), "Priest of the Light");
}

const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

bool runtimeItemIsIdentified(
    const OpenYAMM::Game::EquippedItemRuntimeState &runtimeState,
    uint32_t equippedItemId)
{
    return equippedItemId == 0 || runtimeState.identified;
}

bool characterHasAnyEquippedItem(const OpenYAMM::Game::Character &character)
{
    return character.equipment.mainHand != 0
        || character.equipment.offHand != 0
        || character.equipment.bow != 0
        || character.equipment.armor != 0
        || character.equipment.helm != 0
        || character.equipment.belt != 0
        || character.equipment.cloak != 0
        || character.equipment.gauntlets != 0
        || character.equipment.boots != 0
        || character.equipment.amulet != 0
        || character.equipment.ring1 != 0
        || character.equipment.ring2 != 0
        || character.equipment.ring3 != 0
        || character.equipment.ring4 != 0
        || character.equipment.ring5 != 0
        || character.equipment.ring6 != 0;
}

bool characterHasItem(const OpenYAMM::Game::Character &character, uint32_t itemId)
{
    if (itemId == 0)
    {
        return false;
    }

    for (const OpenYAMM::Game::InventoryItem &item : character.inventory)
    {
        if (item.objectDescriptionId == itemId)
        {
            return true;
        }
    }

    return character.equipment.mainHand == itemId
        || character.equipment.offHand == itemId
        || character.equipment.bow == itemId
        || character.equipment.armor == itemId
        || character.equipment.helm == itemId
        || character.equipment.belt == itemId
        || character.equipment.cloak == itemId
        || character.equipment.gauntlets == itemId
        || character.equipment.boots == itemId
        || character.equipment.amulet == itemId
        || character.equipment.ring1 == itemId
        || character.equipment.ring2 == itemId
        || character.equipment.ring3 == itemId
        || character.equipment.ring4 == itemId
        || character.equipment.ring5 == itemId
        || character.equipment.ring6 == itemId;
}

std::string readSourceTextFile(const std::filesystem::path &path)
{
    std::ifstream stream(path);
    REQUIRE(stream.is_open());

    std::ostringstream buffer;
    buffer << stream.rdbuf();
    return buffer.str();
}

std::vector<uint8_t> readSourceBinaryFile(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    REQUIRE(stream.good());

    return std::vector<uint8_t>(
        std::istreambuf_iterator<char>(stream),
        std::istreambuf_iterator<char>());
}

uint64_t fnv1a64(const std::vector<uint8_t> &bytes)
{
    uint64_t hash = 14695981039346656037ull;

    for (uint8_t byte : bytes)
    {
        hash ^= byte;
        hash *= 1099511628211ull;
    }

    return hash;
}

OpenYAMM::Game::SpriteFrameTable loadCommonSpriteFrameTable()
{
    const std::string yamlText =
        readSourceTextFile(
            std::filesystem::path(OPENYAMM_SOURCE_DIR)
            / "assets_dev/engine/rendering/sprite_frame_data_common.yml");

    OpenYAMM::Game::SpriteFrameTable spriteFrameTable;
    std::string errorMessage;
    REQUIRE(spriteFrameTable.loadFromYaml(yamlText, errorMessage, false));

    return spriteFrameTable;
}

std::vector<std::vector<std::string>> loadAssetTextTableRows(const std::string &relativePath)
{
    const std::optional<OpenYAMM::Engine::TextTable> textTable =
        OpenYAMM::Engine::TextTable::parseTabSeparated(readSourceTextFile(
            std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath));
    REQUIRE(textTable.has_value());

    std::vector<std::vector<std::string>> rows;
    rows.reserve(textTable->getRowCount());

    for (size_t index = 0; index < textTable->getRowCount(); ++index)
    {
        rows.push_back(textTable->getRow(index));
    }

    return rows;
}

std::string lowercaseFileName(const std::filesystem::path &path)
{
    std::string name = path.filename().string();
    for (char &character : name)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }
    return name;
}

void checkFirstSpriteFrameTexture(
    const OpenYAMM::Game::SpriteFrameTable &spriteFrameTable,
    const std::string &spriteName,
    const std::string &expectedTextureName,
    const std::string &expectedAssetFileName)
{
    const std::optional<uint16_t> spriteFrameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);
    REQUIRE(spriteFrameIndex.has_value());

    const OpenYAMM::Game::SpriteFrameEntry *pFrame = spriteFrameTable.getFrame(*spriteFrameIndex, 0);
    REQUIRE(pFrame != nullptr);

    const OpenYAMM::Game::ResolvedSpriteTexture texture = OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
    CHECK_EQ(texture.textureName, expectedTextureName);
    CHECK(std::filesystem::exists(
        std::filesystem::path(OPENYAMM_SOURCE_DIR)
        / "assets_dev/engine/sprites"
        / expectedAssetFileName));
}
}

TEST_CASE("settings debug startup options round trip")
{
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "openyamm_debug_god_lich_settings.ini";

    OpenYAMM::Game::GameSettings settings = OpenYAMM::Game::GameSettings::createDefault();
    CHECK_FALSE(settings.spriteOutline);
    settings.settingsProfileName = "test";
    settings.settingsProfileVersion = 7;
    settings.startWorldId = "mm7";
    settings.startMapFile.clear();
    settings.spriteOutline = true;
    settings.viewDistance = "unlimited";
    settings.outdoorBillboardDepthSlice = 0.0f;
    settings.skipEventCutscenes = true;
    settings.waitForLevelSprites = false;
    settings.newGameGodLich = true;
    settings.bolsterMonsters = true;
    settings.outdoorPathfinding = true;
    settings.monsterProjectileVisuals = OpenYAMM::Game::MonsterProjectileVisuals::Sprites;
    settings.logIndoorVisibility = true;
    settings.logOutdoorPathfinding = true;
    settings.fpsTrace = true;
    settings.hitchTrace = true;
    settings.hitchThresholdMilliseconds = 12.5f;
    settings.gameplayTrace = true;
    settings.gameplayTraceFile = "tmp/gameplay.log";
    settings.gameplayTraceAppend = false;
    settings.combatTrace = true;
    settings.combatTraceFile = "tmp/combat.log";
    settings.combatTraceAppend = false;
    settings.contextActionPopup = true;
    settings.verticalSync = true;
    settings.mouseSensitivity = 42;

    std::string error;
    REQUIRE(OpenYAMM::Game::saveGameSettings(path, settings, error));

    const std::optional<OpenYAMM::Game::GameSettings> loadedSettings =
        OpenYAMM::Game::loadGameSettings(path, error);

    REQUIRE(loadedSettings.has_value());
    CHECK_EQ(loadedSettings->settingsProfileName, "test");
    CHECK_EQ(loadedSettings->settingsProfileVersion, 7);
    CHECK_EQ(loadedSettings->startWorldId, "mm7");
    CHECK(loadedSettings->startMapFile.empty());
    CHECK(loadedSettings->spriteOutline);
    CHECK_EQ(loadedSettings->viewDistance, "unlimited");
    CHECK_EQ(OpenYAMM::Game::resolveViewDistanceSetting(loadedSettings->viewDistance, 16192.0f), 200000.0f);
    CHECK(loadedSettings->outdoorBillboardDepthSlice == doctest::Approx(0.0f));
    CHECK(loadedSettings->skipEventCutscenes);
    CHECK_FALSE(loadedSettings->waitForLevelSprites);
    CHECK(loadedSettings->newGameGodLich);
    CHECK(loadedSettings->bolsterMonsters);
    CHECK(loadedSettings->outdoorPathfinding);
    CHECK(loadedSettings->monsterProjectileVisuals == OpenYAMM::Game::MonsterProjectileVisuals::Sprites);
    CHECK(loadedSettings->logIndoorVisibility);
    CHECK(loadedSettings->logOutdoorPathfinding);
    CHECK(loadedSettings->fpsTrace);
    CHECK(loadedSettings->hitchTrace);
    CHECK(loadedSettings->hitchThresholdMilliseconds == doctest::Approx(12.5f));
    CHECK(loadedSettings->gameplayTrace);
    CHECK_EQ(loadedSettings->gameplayTraceFile, "tmp/gameplay.log");
    CHECK_FALSE(loadedSettings->gameplayTraceAppend);
    CHECK(loadedSettings->combatTrace);
    CHECK_EQ(loadedSettings->combatTraceFile, "tmp/combat.log");
    CHECK_FALSE(loadedSettings->combatTraceAppend);
    CHECK(loadedSettings->contextActionPopup);
    CHECK(loadedSettings->verticalSync);
    CHECK_EQ(loadedSettings->mouseSensitivity, 42);

    std::filesystem::remove(path);
}

TEST_CASE("android settings profile uses mobile interaction defaults without diagnostic logging")
{
    const std::filesystem::path path =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "android/settings.ini";
    std::string error;
    const std::optional<OpenYAMM::Game::GameSettings> settings =
        OpenYAMM::Game::loadGameSettings(path, error);

    REQUIRE_MESSAGE(settings.has_value(), error.c_str());
    CHECK_EQ(settings->settingsProfileName, "android");
    CHECK_EQ(settings->settingsProfileVersion, 2);
    CHECK(settings->contextActionPopup);
    CHECK(settings->startInMainMenu);
    CHECK(settings->verticalSync);
    CHECK_FALSE(settings->preseedParty);
    CHECK_FALSE(settings->newGameGodLich);
    CHECK_FALSE(settings->allowIncompleteCharacterCreation);
    CHECK(settings->debugConsole);
    CHECK_FALSE(settings->immortal);
    CHECK_FALSE(settings->unlimitedMana);
    CHECK_FALSE(settings->logIndoorVisibility);
    CHECK_FALSE(settings->logIndoorPathfinding);
    CHECK_FALSE(settings->logOutdoorPathfinding);
    CHECK_FALSE(settings->fpsTrace);
    CHECK_FALSE(settings->performanceTrace);
    CHECK_FALSE(settings->hitchTrace);
    CHECK_FALSE(settings->collisionTrace);
    CHECK_FALSE(settings->gameplayTrace);
    CHECK_FALSE(settings->combatTrace);

    const OpenYAMM::Game::InputBinding attackBinding =
        settings->keyboard.binding(OpenYAMM::Game::KeyboardAction::Attack);
    CHECK_EQ(attackBinding.kind, OpenYAMM::Game::InputBindingKind::MouseButton);
    CHECK_EQ(attackBinding.mouseButton, SDL_BUTTON_LEFT);
}

TEST_CASE("legacy Android settings migration changes platform defaults once and preserves user settings")
{
    OpenYAMM::Game::GameSettings settings = OpenYAMM::Game::GameSettings::createDefault();
    settings.soundVolume = 3;
    settings.musicVolume = 4;
    settings.resolutionWidth = 1920;
    settings.resolutionHeight = 1080;
    settings.contextActionPopup = false;
    settings.startInMainMenu = false;
    settings.verticalSync = false;
    settings.logIndoorVisibility = true;
    settings.logIndoorPathfinding = true;
    settings.logOutdoorPathfinding = true;
    settings.fpsTrace = true;
    settings.performanceTrace = true;
    settings.hitchTrace = true;
    settings.collisionTrace = true;
    settings.gameplayTrace = true;
    settings.combatTrace = true;
    settings.newGameGodLich = false;
    settings.overrideStartPosition = true;
    settings.startWorldId = "mm6";

    REQUIRE(OpenYAMM::Game::migrateLegacyAndroidSettings(settings));
    CHECK_EQ(settings.settingsProfileName, "android");
    CHECK_EQ(settings.settingsProfileVersion, 2);
    CHECK(settings.contextActionPopup);
    CHECK(settings.startInMainMenu);
    CHECK(settings.verticalSync);
    CHECK_FALSE(settings.preseedParty);
    CHECK_FALSE(settings.newGameGodLich);
    CHECK_FALSE(settings.allowIncompleteCharacterCreation);
    CHECK_FALSE(settings.overrideStartPosition);
    CHECK_EQ(settings.startWorldId, "mm8");
    CHECK_FALSE(settings.logIndoorVisibility);
    CHECK_FALSE(settings.logIndoorPathfinding);
    CHECK_FALSE(settings.logOutdoorPathfinding);
    CHECK_FALSE(settings.fpsTrace);
    CHECK_FALSE(settings.performanceTrace);
    CHECK_FALSE(settings.hitchTrace);
    CHECK_FALSE(settings.collisionTrace);
    CHECK_FALSE(settings.gameplayTrace);
    CHECK_FALSE(settings.combatTrace);
    CHECK_EQ(settings.soundVolume, 3);
    CHECK_EQ(settings.musicVolume, 4);
    CHECK_EQ(settings.resolutionWidth, 1920);
    CHECK_EQ(settings.resolutionHeight, 1080);

    settings.contextActionPopup = false;
    settings.soundVolume = 5;
    CHECK_FALSE(OpenYAMM::Game::migrateLegacyAndroidSettings(settings));
    CHECK_FALSE(settings.contextActionPopup);
    CHECK_EQ(settings.soundVolume, 5);
}

TEST_CASE("Android profile version two only migrates character creation defaults")
{
    OpenYAMM::Game::GameSettings settings = OpenYAMM::Game::GameSettings::createDefault();
    settings.settingsProfileName = "android";
    settings.settingsProfileVersion = 1;
    settings.soundVolume = 5;
    settings.startWorldId = "mm6";
    settings.contextActionPopup = false;
    settings.preseedParty = true;
    settings.newGameGodLich = true;
    settings.allowIncompleteCharacterCreation = true;

    REQUIRE(OpenYAMM::Game::migrateLegacyAndroidSettings(settings));
    CHECK_EQ(settings.settingsProfileVersion, 2);
    CHECK_EQ(settings.soundVolume, 5);
    CHECK_EQ(settings.startWorldId, "mm6");
    CHECK_FALSE(settings.contextActionPopup);
    CHECK_FALSE(settings.preseedParty);
    CHECK_FALSE(settings.newGameGodLich);
    CHECK_FALSE(settings.allowIncompleteCharacterCreation);
}

TEST_CASE("settings monster bolster feature defaults off")
{
    CHECK_FALSE(OpenYAMM::Game::GameSettings::createDefault().bolsterMonsters);
    CHECK(
        OpenYAMM::Game::GameSettings::createDefault().monsterProjectileVisuals
        == OpenYAMM::Game::MonsterProjectileVisuals::FxRecipes);
    CHECK(
        OpenYAMM::Game::GameSettings::createDefault().blasterSkillScaling
        == OpenYAMM::Game::BlasterSkillScalingMode::Default);
    CHECK_EQ(OpenYAMM::Game::GameSettings::createDefault().blasterMinimumRecoveryTicks, 0);

    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "openyamm_default_bolster_settings.ini";

    {
        std::ofstream output(path);
        REQUIRE(output.good());
        output << "[audio]\n";
        output << "sound_volume=4\n";
    }

    std::string error;
    const std::optional<OpenYAMM::Game::GameSettings> loadedSettings =
        OpenYAMM::Game::loadGameSettings(path, error);

    REQUIRE(loadedSettings.has_value());
    CHECK_FALSE(loadedSettings->bolsterMonsters);
    CHECK_FALSE(loadedSettings->outdoorPathfinding);
    CHECK(loadedSettings->monsterProjectileVisuals == OpenYAMM::Game::MonsterProjectileVisuals::FxRecipes);
    CHECK(loadedSettings->blasterSkillScaling == OpenYAMM::Game::BlasterSkillScalingMode::Default);
    CHECK_EQ(loadedSettings->blasterMinimumRecoveryTicks, 0);
    CHECK_FALSE(loadedSettings->logIndoorVisibility);
    CHECK_FALSE(loadedSettings->logOutdoorPathfinding);
    CHECK_FALSE(loadedSettings->fpsTrace);
    CHECK_FALSE(loadedSettings->gameplayTrace);
    CHECK_EQ(loadedSettings->gameplayTraceFile, "logs/gameplay_trace.log");
    CHECK(loadedSettings->gameplayTraceAppend);
    CHECK_FALSE(loadedSettings->combatTrace);
    CHECK_EQ(loadedSettings->combatTraceFile, "logs/combat_trace.log");
    CHECK(loadedSettings->combatTraceAppend);
    CHECK_EQ(loadedSettings->contextActionPopup, OpenYAMM::Game::GameSettings::createDefault().contextActionPopup);
    CHECK(loadedSettings->outdoorBillboardDepthSlice == doctest::Approx(256.0f));
    CHECK_FALSE(loadedSettings->skipEventCutscenes);
    CHECK_FALSE(loadedSettings->waitForLevelSprites);

    std::filesystem::remove(path);
}

TEST_CASE("gameplay trace writes only when settings-backed sink is enabled")
{
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "openyamm_gameplay_trace_test.log";
    std::filesystem::remove(path);

    OpenYAMM::Game::configureGameplayDebugTrace(false, path.string(), false);
    GAMEPLAY_DEBUG_TRACE("disabled gameplay message");
    CHECK_FALSE(std::filesystem::exists(path));

    OpenYAMM::Game::configureGameplayDebugTrace(true, path.string(), false);
    GAMEPLAY_DEBUG_TRACE("enabled gameplay message");
    OpenYAMM::Game::configureGameplayDebugTrace(false, path.string(), true);

    std::ifstream input(path);
    REQUIRE(input.good());
    std::ostringstream buffer;
    buffer << input.rdbuf();
    CHECK(buffer.str().find("[GameplayTrace] enabled gameplay message") != std::string::npos);
    CHECK(buffer.str().find("disabled gameplay message") == std::string::npos);

    std::filesystem::remove(path);
}

TEST_CASE("combat trace writes only when settings-backed sink is enabled")
{
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "openyamm_combat_trace_test.log";
    std::filesystem::remove(path);

    OpenYAMM::Game::configureGameplayCombatTrace(false, path.string(), false);
    GAMEPLAY_COMBAT_TRACE("disabled message");
    CHECK_FALSE(std::filesystem::exists(path));

    OpenYAMM::Game::configureGameplayCombatTrace(true, path.string(), false);
    GAMEPLAY_COMBAT_TRACE("enabled message");
    OpenYAMM::Game::configureGameplayCombatTrace(false, path.string(), true);

    std::ifstream input(path);
    REQUIRE(input.good());
    std::ostringstream buffer;
    buffer << input.rdbuf();
    CHECK(buffer.str().find("[CombatTrace] enabled message") != std::string::npos);
    CHECK(buffer.str().find("disabled message") == std::string::npos);

    std::filesystem::remove(path);
}

TEST_CASE("settings parse blaster combat feature knobs")
{
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "openyamm_blaster_feature_settings.ini";

    {
        std::ofstream output(path);
        REQUIRE(output.good());
        output << "[features]\n";
        output << "blaster_skill_scaling=scaling_damage\n";
        output << "blaster_min_recovery=10\n";
    }

    std::string error;
    const std::optional<OpenYAMM::Game::GameSettings> loadedSettings =
        OpenYAMM::Game::loadGameSettings(path, error);

    REQUIRE(loadedSettings.has_value());
    CHECK(loadedSettings->blasterSkillScaling == OpenYAMM::Game::BlasterSkillScalingMode::ScalingDamage);
    CHECK_EQ(loadedSettings->blasterMinimumRecoveryTicks, 10);

    const OpenYAMM::Game::CharacterAttackTuning attackTuning =
        OpenYAMM::Game::characterAttackTuningFromSettings(*loadedSettings);
    CHECK(attackTuning.blasterSkillScaling == OpenYAMM::Game::BlasterSkillScalingMode::ScalingDamage);
    CHECK_EQ(attackTuning.blasterMinimumRecoveryTicks, 10);

    std::filesystem::remove(path);
}

TEST_CASE("house data magic guild types are explicit")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    const OpenYAMM::Game::HouseEntry *pElementalGuild = gameData.houseTable.get(139);
    const OpenYAMM::Game::HouseEntry *pLightGuild = gameData.houseTable.get(170);
    const OpenYAMM::Game::HouseEntry *pDarkGuild = gameData.houseTable.get(175);

    REQUIRE(pElementalGuild != nullptr);
    REQUIRE(pLightGuild != nullptr);
    REQUIRE(pDarkGuild != nullptr);

    CHECK_EQ(pElementalGuild->type, "Air Guild");
    CHECK_EQ(pLightGuild->type, "Light Guild");
    CHECK_EQ(pDarkGuild->type, "Dark Guild");
}

TEST_CASE("merged house movie metadata drives videos and proprietor portraits")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    const OpenYAMM::Game::HouseEntry *pMm8Temple = gameData.houseTable.get(303);
    const OpenYAMM::Game::HouseEntry *pMm6Temple = gameData.houseTable.get(325);
    const OpenYAMM::Game::HouseEntry *pMm7WeaponShop = gameData.houseTable.get(11);
    const OpenYAMM::Game::HouseEntry *pMm7DungeonEntrance = gameData.houseTable.get(399);

    REQUIRE(pMm8Temple != nullptr);
    REQUIRE(pMm6Temple != nullptr);
    REQUIRE(pMm7WeaponShop != nullptr);
    REQUIRE(pMm7DungeonEntrance != nullptr);

    CHECK_EQ(pMm8Temple->mapId, 1u);
    CHECK_EQ(pMm8Temple->videoName, "ltemple");
    CHECK_EQ(pMm8Temple->proprietorPictureId, 1130u);
    CHECK_EQ(pMm6Temple->videoName, "temprich");
    CHECK_EQ(pMm6Temple->proprietorPictureId, 1035u);
    CHECK_EQ(pMm7WeaponShop->mapId, 65u);
    CHECK_EQ(pMm7WeaponShop->videoName, "elf weapon smith");
    CHECK_EQ(pMm7WeaponShop->proprietorPictureId, 527u);
    CHECK_EQ(pMm7DungeonEntrance->videoName, "out06 red dwarf mines");

    const std::filesystem::path assetRoot = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev";
    const std::filesystem::path engineRoot = assetRoot / "engine";
    const std::filesystem::path mm6WorldRoot = assetRoot / "worlds/mm6";
    const std::filesystem::path mm7WorldRoot = assetRoot / "worlds/mm7";
    const std::filesystem::path mm8WorldRoot = assetRoot / "worlds/mm8";
    CHECK(std::filesystem::exists(mm6WorldRoot / "videos/Houses/temprich.ogv"));
    CHECK(std::filesystem::exists(mm7WorldRoot / "icons" / "npc0527.bmp"));
    CHECK(std::filesystem::exists(mm7WorldRoot / "videos/Houses/elf weapon smith.ogv"));
    CHECK(std::filesystem::exists(mm7WorldRoot / "videos/Transitions/out06 red dwarf mines.ogv"));
    CHECK(std::filesystem::exists(engineRoot / "icons" / "npc1582.bmp"));
    CHECK(std::filesystem::exists(mm8WorldRoot / "videos/Houses/ltemple.ogv"));
    CHECK_FALSE(std::filesystem::exists(engineRoot / "videos"));
    CHECK(std::filesystem::exists(mm8WorldRoot / "icons/npc1465.bmp"));
    CHECK(std::filesystem::exists(mm8WorldRoot / "icons/npc1325.bmp"));
}

TEST_CASE("character doll weapon anchors follow MMerge hold offsets")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    const OpenYAMM::Game::CharacterDollTypeEntry *pDollType = gameData.characterDollTable.getDollType(4);
    REQUIRE(pDollType != nullptr);

    CHECK_EQ(pDollType->mainHandWeaponAnchorX(), 17);
    CHECK_EQ(pDollType->mainHandWeaponAnchorY(), 171);
    CHECK_EQ(pDollType->offHandWeaponAnchorX(), 128);
    CHECK_EQ(pDollType->offHandWeaponAnchorY(), 165);
}

TEST_CASE("outdoor minimap icons are world-owned")
{
    const std::filesystem::path assetRoot = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev";
    const std::filesystem::path engineIcons = assetRoot / "engine/icons";
    const std::filesystem::path mm6Icons = assetRoot / "worlds/mm6/icons";
    const std::filesystem::path mm7Icons = assetRoot / "worlds/mm7/icons";
    const std::filesystem::path mm8Icons = assetRoot / "worlds/mm8/icons";

    const std::pair<std::filesystem::path, const char *> expectedWorldIcons[] = {
        {mm6Icons, "outc1.bmp"},
        {mm6Icons, "6outside.bmp"},
        {mm7Icons, "7out15.bmp"},
        {mm7Icons, "out14.bmp"},
        {mm8Icons, "out06.bmp"},
        {mm8Icons, "out13.bmp"},
        {mm8Icons, "elema.bmp"},
        {mm8Icons, "pbp.bmp"},
        {mm8Icons, "outside.bmp"},
    };

    for (const std::pair<std::filesystem::path, const char *> &entry : expectedWorldIcons)
    {
        const std::filesystem::path iconPath = entry.first / entry.second;
        CHECK(std::filesystem::exists(iconPath));
        CHECK_EQ(
            std::filesystem::status(iconPath).permissions() & std::filesystem::perms::all,
            std::filesystem::perms::owner_read
                | std::filesystem::perms::owner_write
                | std::filesystem::perms::group_read
                | std::filesystem::perms::others_read);
    }

    const char *engineForbiddenIcons[] = {
        "out06.bmp",
        "out13.bmp",
        "outc1.bmp",
        "7out15.bmp",
        "elema.bmp",
        "pbp.bmp",
        "outside.bmp",
        "6outside.bmp",
        "7outside.bmp",
    };

    for (const char *iconName : engineForbiddenIcons)
    {
        CHECK_FALSE(std::filesystem::exists(engineIcons / iconName));
    }
}

TEST_CASE("mm8 icons do not duplicate engine-owned icons")
{
    const std::filesystem::path assetRoot = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev";
    const std::filesystem::path engineIcons = assetRoot / "engine/icons";
    const std::filesystem::path mm8Icons = assetRoot / "worlds/mm8/icons";

    std::set<std::string> engineIconNames;
    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(engineIcons))
    {
        if (entry.is_regular_file())
        {
            engineIconNames.insert(lowercaseFileName(entry.path()));
        }
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(mm8Icons))
    {
        if (!entry.is_regular_file())
        {
            continue;
        }

        CHECK_FALSE(engineIconNames.contains(lowercaseFileName(entry.path())));
    }
}

TEST_CASE("mm8 screen backgrounds remain the engine defaults")
{
    const std::filesystem::path engineIcons =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/icons";

    struct ExpectedBackground
    {
        const char *fileName;
        uintmax_t fileSize;
        uint64_t fnvHash;
    };

    const ExpectedBackground expectedBackgrounds[] = {
        {"title.pcx", 826904u, 0xacb405aa6d8fa528ull},
        {"makeme.pcx", 712504u, 0x00f643e26313af10ull},
        {"restmain.bmp", 235318u, 0x31067b73f0375f04ull},
    };

    for (const ExpectedBackground &expectedBackground : expectedBackgrounds)
    {
        const std::filesystem::path path = engineIcons / expectedBackground.fileName;
        REQUIRE(std::filesystem::exists(path));
        CHECK_EQ(std::filesystem::file_size(path), expectedBackground.fileSize);
        CHECK_EQ(fnv1a64(readSourceBinaryFile(path)), expectedBackground.fnvHash);
        CHECK_EQ(
            std::filesystem::status(path).permissions() & std::filesystem::perms::all,
            std::filesystem::perms::owner_read
                | std::filesystem::perms::owner_write
                | std::filesystem::perms::group_read
                | std::filesystem::perms::others_read);
    }
}

TEST_CASE("monster spell descriptors preserve skill mastery and level")
{
    OpenYAMM::Game::MonsterTable monsterTable;
    std::vector<std::string> row(37, "0");
    row[0] = "999";
    row[1] = "Test Caster";
    row[2] = "test caster";
    row[3] = "12";
    row[4] = "40";
    row[5] = "3";
    row[12] = "2";
    row[13] = "200";
    row[14] = "80";
    row[24] = "35";
    row[25] = "Lightning Bolt,M,7";
    row[26] = "45";
    row[27] = "Fireball,G,9";

    REQUIRE(monsterTable.loadStatsFromRows({row}));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(999);
    REQUIRE(pStats != nullptr);
    CHECK_EQ(pStats->spell1Name, "lightning bolt");
    CHECK_EQ(pStats->spell1SkillMastery, OpenYAMM::Game::SkillMastery::Master);
    CHECK_EQ(pStats->spell1SkillLevel, 7u);
    CHECK_EQ(pStats->spell2Name, "fireball");
    CHECK_EQ(pStats->spell2SkillMastery, OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_EQ(pStats->spell2SkillLevel, 9u);
}

TEST_CASE("runtime monster table carries promoted MMerge monster kind flags")
{
    OpenYAMM::Game::MonsterTable monsterTable;
    REQUIRE(monsterTable.loadStatsFromRows(loadAssetTextTableRows("assets_dev/engine/data_tables/monster_data.txt")));
    OpenYAMM::Game::MergedBolsterMonsterTable bolsterMonsterTable;
    REQUIRE(
        bolsterMonsterTable.loadFromRows(loadAssetTextTableRows("assets_dev/engine/data_tables/bolster_monsters.txt")));
    REQUIRE(monsterTable.applyKindFlagsFromBolsterMonsterTable(bolsterMonsterTable));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pLizardmanPeasant =
        monsterTable.findStatsById(1);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pTownPeasant =
        monsterTable.findStatsById(313);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pGoblinPeasant =
        monsterTable.findStatsById(430);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pVampire =
        monsterTable.findStatsById(52);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pDragon =
        monsterTable.findStatsById(70);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pWaterElemental =
        monsterTable.findStatsById(76);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pTitan =
        monsterTable.findStatsById(640);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pDragonTurtle =
        monsterTable.findStatsById(136);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pBoulder =
        monsterTable.findStatsById(142);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMm7Devil =
        monsterTable.findStatsById(220);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMm6DemonFly =
        monsterTable.findStatsById(499);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMm6Demon =
        monsterTable.findStatsById(502);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMm6MerchantPeasant =
        monsterTable.findStatsById(577);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMm6NewSorpigalPeasantFemale =
        monsterTable.findStatsById(595);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMm6Cutpurse =
        monsterTable.findStatsById(601);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMm6NewSorpigalPeasantMale =
        monsterTable.findStatsById(607);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMm6Mage =
        monsterTable.findStatsById(610);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pReactor =
        monsterTable.findStatsById(652);

    REQUIRE(pLizardmanPeasant != nullptr);
    REQUIRE(pTownPeasant != nullptr);
    REQUIRE(pGoblinPeasant != nullptr);
    REQUIRE(pVampire != nullptr);
    REQUIRE(pDragon != nullptr);
    REQUIRE(pWaterElemental != nullptr);
    REQUIRE(pTitan != nullptr);
    REQUIRE(pDragonTurtle != nullptr);
    REQUIRE(pBoulder != nullptr);
    REQUIRE(pMm7Devil != nullptr);
    REQUIRE(pMm6DemonFly != nullptr);
    REQUIRE(pMm6Demon != nullptr);
    REQUIRE(pMm6MerchantPeasant != nullptr);
    REQUIRE(pMm6NewSorpigalPeasantFemale != nullptr);
    REQUIRE(pMm6Cutpurse != nullptr);
    REQUIRE(pMm6NewSorpigalPeasantMale != nullptr);
    REQUIRE(pMm6Mage != nullptr);
    REQUIRE(pReactor != nullptr);
    CHECK(pLizardmanPeasant->hasKind(OpenYAMM::Game::MonsterKind::Peasant));
    CHECK(pLizardmanPeasant->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK(pTownPeasant->hasKind(OpenYAMM::Game::MonsterKind::Peasant));
    CHECK(pTownPeasant->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK(pGoblinPeasant->hasKind(OpenYAMM::Game::MonsterKind::Peasant));
    CHECK(pGoblinPeasant->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK(pVampire->hasKind(OpenYAMM::Game::MonsterKind::Undead));
    CHECK(pDragon->hasKind(OpenYAMM::Game::MonsterKind::Dragon));
    CHECK(pWaterElemental->hasKind(OpenYAMM::Game::MonsterKind::Swimmer));
    CHECK(pWaterElemental->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK(pWaterElemental->hasKind(OpenYAMM::Game::MonsterKind::Elemental));
    CHECK(pTitan->hasKind(OpenYAMM::Game::MonsterKind::Titan));
    CHECK(pDragonTurtle->hasKind(OpenYAMM::Game::MonsterKind::Dragon));
    CHECK(pDragonTurtle->hasKind(OpenYAMM::Game::MonsterKind::Swimmer));
    CHECK(pDragonTurtle->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK(pBoulder->hasKind(OpenYAMM::Game::MonsterKind::Immobile));
    CHECK(pBoulder->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK_FALSE(pMm7Devil->hasKind(OpenYAMM::Game::MonsterKind::NoCorpse));
    CHECK(pMm6DemonFly->hasKind(OpenYAMM::Game::MonsterKind::NoCorpse));
    CHECK(pMm6Demon->hasKind(OpenYAMM::Game::MonsterKind::NoCorpse));
    CHECK(pMm6MerchantPeasant->hasKind(OpenYAMM::Game::MonsterKind::Peasant));
    CHECK(pMm6MerchantPeasant->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK(pMm6NewSorpigalPeasantFemale->hasKind(OpenYAMM::Game::MonsterKind::Peasant));
    CHECK(pMm6NewSorpigalPeasantFemale->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK_FALSE(pMm6Cutpurse->hasKind(OpenYAMM::Game::MonsterKind::Peasant));
    CHECK(pMm6NewSorpigalPeasantMale->hasKind(OpenYAMM::Game::MonsterKind::Peasant));
    CHECK(pMm6NewSorpigalPeasantMale->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK_FALSE(pMm6Mage->hasKind(OpenYAMM::Game::MonsterKind::Peasant));
    CHECK(pReactor->hasKind(OpenYAMM::Game::MonsterKind::Immobile));
    CHECK(pReactor->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
}

TEST_CASE("monster hostility table follows merged merged party relations")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    CHECK_FALSE(gameData.monsterTable.isHostileToParty(49));
    CHECK_FALSE(gameData.monsterTable.isHostileToParty(52));
    CHECK(gameData.monsterTable.isHostileToParty(73));
    CHECK(gameData.monsterTable.isHostileToParty(74));
    CHECK(gameData.monsterTable.isHostileToParty(75));
}

TEST_CASE("harm projectile sprite resolves to an existing billboard texture")
{
    const OpenYAMM::Game::SpriteFrameTable spriteFrameTable = loadCommonSpriteFrameTable();

    checkFirstSpriteFrameTexture(spriteFrameTable, "spell70", "spell70b10", "Spell70b10.bmp");
}

TEST_CASE("light bolt sprites resolve to existing billboard textures")
{
    const OpenYAMM::Game::SpriteFrameTable spriteFrameTable = loadCommonSpriteFrameTable();

    checkFirstSpriteFrameTexture(spriteFrameTable, "spell78b", "sp78b", "sp78b.bmp");
    checkFirstSpriteFrameTexture(spriteFrameTable, "spell78c", "sp78c", "sp78c.bmp");
}

TEST_CASE("directional sprite bases resolve with an octant suffix")
{
    OpenYAMM::Game::SpriteFrameEntry frame;
    frame.textureName = "pfemsta";
    frame.flags =
        static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::First)
        | static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::Mirror5)
        | static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::Mirror6)
        | static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::Mirror7);

    OpenYAMM::Game::ResolvedSpriteTexture frontTexture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(frame, 0);
    OpenYAMM::Game::ResolvedSpriteTexture sideTexture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(frame, 3);
    OpenYAMM::Game::ResolvedSpriteTexture mirroredSideTexture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(frame, 5);

    CHECK_EQ(frontTexture.textureName, "pfemsta0");
    CHECK_FALSE(frontTexture.mirrored);
    CHECK_EQ(sideTexture.textureName, "pfemsta3");
    CHECK_FALSE(sideTexture.mirrored);
    CHECK_EQ(mirroredSideTexture.textureName, "pfemsta3");
    CHECK(mirroredSideTexture.mirrored);
}

TEST_CASE("already resolved directional texture names are preserved")
{
    OpenYAMM::Game::SpriteFrameEntry frame;
    frame.textureName = "m528aa0";
    frame.flags = static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::First);

    OpenYAMM::Game::ResolvedSpriteTexture texture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(frame, 2);

    CHECK_EQ(texture.textureName, "m528aa0");
}

TEST_CASE("roster join offer mapping samples")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    struct ExpectedRosterJoinOffer
    {
        uint32_t topicId = 0;
        uint32_t rosterId = 0;
        uint32_t inviteTextId = 0;
        uint32_t partyFullTextId = 0;
    };

    const std::array<ExpectedRosterJoinOffer, 9> expectedOffers = {{
        {602, 2, 202, 203},
        {604, 4, 206, 207},
        {606, 6, 210, 211},
        {611, 11, 220, 221},
        {627, 27, 252, 253},
        {630, 30, 258, 259},
        {632, 32, 262, 263},
        {634, 34, 266, 267},
        {635, 35, 268, 269},
    }};

    for (const ExpectedRosterJoinOffer &expectedOffer : expectedOffers)
    {
        const std::optional<OpenYAMM::Game::NpcDialogTable::RosterJoinOffer> actualOffer =
            gameData.npcDialogTable.getRosterJoinOfferForTopic(expectedOffer.topicId);

        REQUIRE(actualOffer.has_value());
        CHECK_EQ(actualOffer->rosterId, expectedOffer.rosterId);
        CHECK_EQ(actualOffer->inviteTextId, expectedOffer.inviteTextId);
        CHECK_EQ(actualOffer->partyFullTextId, expectedOffer.partyFullTextId);
    }

    CHECK_FALSE(gameData.npcDialogTable.getRosterJoinOfferForTopic(600).has_value());
    CHECK_FALSE(gameData.npcDialogTable.getRosterJoinOfferForTopic(650).has_value());
}

TEST_CASE("volog roster join text stays tied to troll homeland quest")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const std::optional<OpenYAMM::Game::NpcDialogTable::RosterJoinOffer> offer =
        gameData.npcDialogTable.getRosterJoinOfferForTopic(612);

    REQUIRE(offer.has_value());
    CHECK_EQ(offer->rosterId, 12);
    CHECK_EQ(offer->inviteTextId, 222);

    const std::optional<std::string> inviteText = gameData.npcDialogTable.getText(offer->inviteTextId);
    REQUIRE(inviteText.has_value());
    CHECK(inviteText->find("Ancient Troll Home") != std::string::npos);
    CHECK(inviteText->find("village of Rust") != std::string::npos);
    CHECK(inviteText->find("Balthazar") == std::string::npos);
    CHECK(inviteText->find("Axe") == std::string::npos);
}

TEST_CASE("recruit roster member loads birth experience resistances and items")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(3);
    const OpenYAMM::Game::RosterEntry *pBlazenRosterEntry = gameData.rosterTable.get(35);

    REQUIRE(pRosterEntry != nullptr);
    REQUIRE(pBlazenRosterEntry != nullptr);
    CHECK_EQ(pRosterEntry->unlockQuestBitId, 403u);
    CHECK_EQ(pBlazenRosterEntry->unlockQuestBitId, 435u);

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);

    REQUIRE(party.recruitRosterMember(*pRosterEntry));

    const OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    CHECK_EQ(pMember->birthYear, pRosterEntry->birthYear);
    CHECK_EQ(pMember->experience, pRosterEntry->experience);
    CHECK_EQ(pMember->baseResistances.fire, pRosterEntry->baseResistances.fire);
    CHECK_EQ(pMember->baseResistances.body, pRosterEntry->baseResistances.body);
    CHECK((!pMember->inventory.empty() || characterHasAnyEquippedItem(*pMember)));

    for (const OpenYAMM::Game::InventoryItem &item : pMember->inventory)
    {
        CHECK(item.identified);
    }

    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.mainHand, pMember->equipment.mainHand));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.offHand, pMember->equipment.offHand));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.bow, pMember->equipment.bow));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.armor, pMember->equipment.armor));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.helm, pMember->equipment.helm));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.belt, pMember->equipment.belt));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.cloak, pMember->equipment.cloak));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.gauntlets, pMember->equipment.gauntlets));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.boots, pMember->equipment.boots));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.amulet, pMember->equipment.amulet));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring1, pMember->equipment.ring1));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring2, pMember->equipment.ring2));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring3, pMember->equipment.ring3));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring4, pMember->equipment.ring4));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring5, pMember->equipment.ring5));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring6, pMember->equipment.ring6));

    for (uint32_t itemId : pRosterEntry->startingInventoryItemIds)
    {
        CHECK(characterHasItem(*pMember, itemId));
    }

    REQUIRE_FALSE(pBlazenRosterEntry->startingItems.empty());
    CHECK_EQ(pBlazenRosterEntry->startingItems[0].rawValue, 5005u);
    CHECK_EQ(pBlazenRosterEntry->startingItems[0].itemId, 5u);
    CHECK_EQ(pBlazenRosterEntry->startingItems[0].enchantmentLevel, 5u);

    OpenYAMM::Game::Party blazenParty = {};
    blazenParty.setItemTable(&gameData.itemTable);
    blazenParty.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);

    REQUIRE(blazenParty.recruitRosterMember(*pBlazenRosterEntry));

    const OpenYAMM::Game::Character *pBlazen = blazenParty.member(0);
    REQUIRE(pBlazen != nullptr);
    CHECK(characterHasAnyEquippedItem(*pBlazen));

    for (uint32_t itemId : pBlazenRosterEntry->startingInventoryItemIds)
    {
        CHECK(characterHasItem(*pBlazen, itemId));
    }
}

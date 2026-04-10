#include "game/app/GameApplication.h"

#include "game/gameplay/GameMechanics.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/party/SkillData.h"
#include "game/party/SpellIds.h"
#include "game/party/SpellSchool.h"
#include "game/tables/ItemTable.h"
#include "game/ui/screens/ArcomageScreen.h"
#include "game/ui/screens/LoadMenuScreen.h"
#include "game/ui/screens/MainMenuScreen.h"
#include "game/ui/screens/NewGameScreen.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <algorithm>
#include <array>
#include <filesystem>
#include <functional>
#include <iostream>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr uint32_t DefaultRosterPartyMemberCount = 3;
constexpr const char *DefaultStartupMapFile = "out01.odm";
constexpr uint32_t BronzeRingItemId = 137;
constexpr uint32_t GoldRingItemId = 138;
constexpr uint32_t PotionBottleItemId = 220;
constexpr std::array<uint32_t, 3> Level1ReagentItemIds = {{200, 205, 210}};

float mapMoveHeadingDegreesToOutdoorYawRadians(int32_t directionDegrees)
{
    return -static_cast<float>(directionDegrees) * Pi / 180.0f;
}

std::optional<uint32_t> starterItemIdForSkill(const std::string &skillName)
{
    const std::string canonicalName = canonicalSkillName(skillName);

    if (canonicalName == "Staff")
    {
        return 79;
    }

    if (canonicalName == "Sword")
    {
        return 1;
    }

    if (canonicalName == "Dagger")
    {
        return 21;
    }

    if (canonicalName == "Axe")
    {
        return 31;
    }

    if (canonicalName == "Spear")
    {
        return 41;
    }

    if (canonicalName == "Bow")
    {
        return 56;
    }

    if (canonicalName == "Mace")
    {
        return 66;
    }

    if (canonicalName == "Shield")
    {
        return 99;
    }

    if (canonicalName == "LeatherArmor")
    {
        return 84;
    }

    if (canonicalName == "ChainArmor")
    {
        return 89;
    }

    if (canonicalName == "PlateArmor")
    {
        return 94;
    }

    return std::nullopt;
}

bool isStarterMagicSkill(const std::string &skillName)
{
    const std::string canonicalName = canonicalSkillName(skillName);

    return canonicalName == "FireMagic"
        || canonicalName == "AirMagic"
        || canonicalName == "WaterMagic"
        || canonicalName == "EarthMagic"
        || canonicalName == "SpiritMagic"
        || canonicalName == "MindMagic"
        || canonicalName == "BodyMagic"
        || canonicalName == "LightMagic"
        || canonicalName == "DarkMagic";
}

std::optional<uint32_t> spellbookItemIdForSpell(
    const ItemTable &itemTable,
    uint32_t spellId)
{
    if (spellId == 0 || spellId > spellIdValue(SpellId::SoulDrinker))
    {
        return std::nullopt;
    }

    const uint32_t itemId = 399 + spellId;
    const ItemDefinition *pDefinition = itemTable.get(itemId);

    if (pDefinition == nullptr || pDefinition->equipStat != "Book")
    {
        return std::nullopt;
    }

    return itemId;
}

void addStarterInventoryItem(Character &character, InventoryItem item)
{
    item.identified = true;
    character.addInventoryItem(item);
}

InventoryItem makeStarterInventoryItem(
    uint32_t itemId,
    const ItemTable &itemTable)
{
    InventoryItem item = ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::Generic);
    item.identified = true;
    return item;
}

InventoryItem generateStarterRing(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable)
{
    std::random_device randomDevice;
    std::mt19937 rng(randomDevice());
    const ItemGenerationRequest request = {
        .treasureLevel = 2,
        .mode = ItemGenerationMode::Generic,
        .allowRareItems = false
    };

    const std::optional<InventoryItem> generatedRing = ItemGenerator::generateRandomInventoryItem(
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        request,
        nullptr,
        rng,
        [](const ItemDefinition &entry)
        {
            return entry.equipStat == "Ring"
                && (entry.itemId == BronzeRingItemId || entry.itemId == GoldRingItemId);
        });

    if (generatedRing)
    {
        InventoryItem ring = *generatedRing;
        ring.identified = true;
        return ring;
    }

    return makeStarterInventoryItem(BronzeRingItemId, itemTable);
}

void grantCreatedCharacterStarterItems(
    Character &character,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable)
{
    addStarterInventoryItem(
        character,
        generateStarterRing(itemTable, standardItemEnchantTable, specialItemEnchantTable));
    addStarterInventoryItem(character, makeStarterInventoryItem(PotionBottleItemId, itemTable));

    std::random_device randomDevice;
    std::mt19937 rng(randomDevice());
    const size_t reagentIndex = std::uniform_int_distribution<size_t>(0, Level1ReagentItemIds.size() - 1)(rng);
    addStarterInventoryItem(character, makeStarterInventoryItem(Level1ReagentItemIds[reagentIndex], itemTable));

    for (const auto &[skillName, skill] : character.skills)
    {
        if (skill.level == 0)
        {
            continue;
        }

        const std::optional<uint32_t> starterItemId = starterItemIdForSkill(skillName);

        if (starterItemId)
        {
            addStarterInventoryItem(character, makeStarterInventoryItem(*starterItemId, itemTable));
            continue;
        }

        if (!isStarterMagicSkill(skillName))
        {
            continue;
        }

        const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(skillName);

        if (!spellRange)
        {
            continue;
        }

        for (uint32_t spellId = spellRange->first;
             spellId <= spellRange->second && spellId < spellRange->first + 2;
             ++spellId)
        {
            const std::optional<uint32_t> spellbookItemId = spellbookItemIdForSpell(itemTable, spellId);

            if (!spellbookItemId)
            {
                continue;
            }

            addStarterInventoryItem(character, makeStarterInventoryItem(*spellbookItemId, itemTable));
        }
    }
}

void seedSimulatedPartyFromRoster(
    Party &party,
    const RosterTable &rosterTable,
    std::optional<uint32_t> selectedRosterId)
{
    static constexpr std::array<uint32_t, DefaultRosterPartyMemberCount> DefaultPartyRosterIds = {{11, 5, 4}};

    std::vector<uint32_t> rosterIds;
    rosterIds.reserve(DefaultRosterPartyMemberCount);

    if (selectedRosterId.has_value())
    {
        rosterIds.push_back(*selectedRosterId);
    }

    for (uint32_t rosterId : DefaultPartyRosterIds)
    {
        if (selectedRosterId.has_value() && rosterId == *selectedRosterId)
        {
            continue;
        }

        rosterIds.push_back(rosterId);

        if (rosterIds.size() >= DefaultRosterPartyMemberCount)
        {
            break;
        }
    }

    if (rosterIds.size() < DefaultRosterPartyMemberCount)
    {
        for (const RosterEntry *pEntry : rosterTable.getEntriesSortedById())
        {
            if (pEntry == nullptr)
            {
                continue;
            }

            if (std::find(rosterIds.begin(), rosterIds.end(), pEntry->id) != rosterIds.end())
            {
                continue;
            }

            rosterIds.push_back(pEntry->id);

            if (rosterIds.size() >= DefaultRosterPartyMemberCount)
            {
                break;
            }
        }
    }

    if (party.members().size() <= 1)
    {
        return;
    }

    const size_t replaceCount = std::min(party.members().size() - 1, rosterIds.size());

    for (size_t memberIndex = 0; memberIndex < replaceCount; ++memberIndex)
    {
        const RosterEntry *pRosterEntry = rosterTable.get(rosterIds[memberIndex]);

        if (pRosterEntry != nullptr)
        {
            party.replaceMemberWithRosterEntry(memberIndex + 1, *pRosterEntry);
        }
    }
}

void seedSimulatedAdventurersInn(
    Party &party,
    const RosterTable &rosterTable,
    const NpcDialogTable &npcDialogTable,
    std::optional<uint32_t> selectedRosterId)
{
    static constexpr std::array<uint32_t, 2> DefaultAdventurersInnRosterIds = {{1, 7}};

    party.clearAdventurersInnMembers();

    for (uint32_t rosterId : DefaultAdventurersInnRosterIds)
    {
        if (selectedRosterId.has_value() && rosterId == *selectedRosterId)
        {
            continue;
        }

        if (party.hasRosterMember(rosterId))
        {
            continue;
        }

        const RosterEntry *pEntry = rosterTable.get(rosterId);

        if (pEntry == nullptr)
        {
            continue;
        }

        const NpcEntry *pNpcEntry = npcDialogTable.findNpcByName(pEntry->name);
        const uint32_t innPortraitPictureId = pNpcEntry != nullptr ? pNpcEntry->pictureId : 0;
        party.addAdventurersInnMember(*pEntry, innPortraitPictureId);
    }
}

float normalizedVolumeLevel(int level)
{
    return std::clamp(static_cast<float>(level) / 9.0f, 0.0f, 1.0f);
}

float mouseRotateSpeedForTurnRate(TurnRateMode turnRate)
{
    switch (turnRate)
    {
    case TurnRateMode::X16:
        return 0.0030f;

    case TurnRateMode::X32:
        return 0.0045f;

    case TurnRateMode::Smooth:
        return 0.0060f;
    }

    return 0.0045f;
}

Character buildFreshCreatedCharacter(
    const Character &sourceCharacter,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable)
{
    Character character = sourceCharacter;
    character.rosterId = 0;
    character.birthYear = character.birthYear != 0 ? character.birthYear : 1150;
    character.experience = 0;
    character.level = 1;
    character.skillPoints = 0;
    character.quickSpellName.clear();
    character.knownSpellIds.clear();
    character.baseResistances = {};
    character.permanentBonuses = {};
    character.magicalBonuses = {};
    character.permanentImmunities = {};
    character.magicalImmunities = {};
    character.permanentConditionImmunities = {};
    character.magicalConditionImmunities = {};
    character.equipment = {};
    character.equipmentRuntime = {};
    character.conditions = {};
    character.awards.clear();
    character.eventVariables.clear();
    character.recoverySecondsRemaining = 0.0f;
    character.armorClassModifier = 0;
    character.levelModifier = 0;
    character.ageModifier = 0;
    character.playerBits = 0;
    character.npcs2 = 0;
    character.merchantBonus = 0;
    character.weaponEnchantmentDamageBonus = 0;
    character.vampiricHealFraction = 0.0f;
    character.physicalAttackDisabled = false;
    character.physicalDamageImmune = false;
    character.halfMissileDamage = false;
    character.waterWalking = false;
    character.featherFalling = false;
    character.healthRegenPerSecond = 0.0f;
    character.spellRegenPerSecond = 0.0f;
    character.healthRegenAccumulator = 0.0f;
    character.spellRegenAccumulator = 0.0f;
    character.attackRecoveryReductionTicks = 0;
    character.recoveryProgressMultiplier = 1.0f;
    character.itemSkillBonuses.clear();
    character.inventory.clear();

    character.maxHealth = GameMechanics::calculateBaseCharacterMaxHealth(character);
    character.health = character.maxHealth;
    character.maxSpellPoints = GameMechanics::calculateBaseCharacterMaxSpellPoints(character);
    character.spellPoints = character.maxSpellPoints;
    grantCreatedCharacterStarterItems(character, itemTable, standardItemEnchantTable, specialItemEnchantTable);
    return character;
}
}

GameApplication::GameApplication(const Engine::ApplicationConfig &config)
    : m_engineApplication(
        config,
        std::bind(&GameApplication::loadGameData, this, std::placeholders::_1),
        std::bind(&GameApplication::initializeRenderer, this),
        std::bind(&GameApplication::handleSdlEvent, this, std::placeholders::_1),
        std::bind(
            &GameApplication::renderFrame,
            this,
            std::placeholders::_1,
            std::placeholders::_2,
            std::placeholders::_3,
            std::placeholders::_4
        ),
        std::bind(&GameApplication::shutdownApplication, this)
    )
    , m_pAssetFileSystem(nullptr)
    , m_mapPickerIndex(0)
    , m_showMapPicker(false)
    , m_pickerToggleLatch(false)
    , m_pickerApplyLatch(false)
    , m_pickerNextUpRepeatTick(0)
    , m_pickerNextDownRepeatTick(0)
{
}

int GameApplication::run()
{
    return m_engineApplication.run();
}

void GameApplication::handleSdlEvent(const SDL_Event &event)
{
    IScreen *pActiveScreen = m_screenManager.activeScreen();

    if (pActiveScreen != nullptr)
    {
        pActiveScreen->handleSdlEvent(event);
    }
}

std::filesystem::path GameApplication::settingsFilePath() const
{
    return std::filesystem::path("settings.ini");
}

void GameApplication::loadOrCreateSettings()
{
    m_settings = GameSettings::createDefault();
    const std::filesystem::path path = settingsFilePath();
    std::string error;

    if (std::filesystem::exists(path))
    {
        const std::optional<GameSettings> loadedSettings = loadGameSettings(path, error);

        if (loadedSettings.has_value())
        {
            m_settings = *loadedSettings;
        }
        else
        {
            std::cerr << "GameApplication: failed to load " << path.string() << ": " << error << '\n';
        }
    }

    if (!saveGameSettings(path, m_settings, error))
    {
        std::cerr << "GameApplication: failed to write " << path.string() << ": " << error << '\n';
    }
}

void GameApplication::applyCurrentSettingsToActiveRuntime()
{
    m_gameAudioSystem.setSoundVolume(normalizedVolumeLevel(m_settings.soundVolume));
    m_gameAudioSystem.setMusicVolume(normalizedVolumeLevel(m_settings.musicVolume));
    m_gameAudioSystem.setVoiceVolume(normalizedVolumeLevel(m_settings.voiceVolume));
    m_outdoorGameView.setMouseRotateSpeed(mouseRotateSpeedForTurnRate(m_settings.turnRate));
    m_outdoorGameView.setWalkSoundEnabled(m_settings.walksound);
    m_outdoorGameView.setShowHitStatusMessages(m_settings.showHits);
    m_outdoorGameView.setFlipOnExitEnabled(m_settings.flipOnExit);
    m_outdoorGameView.setSettingsSnapshot(m_settings);

    if (m_pOutdoorPartyRuntime != nullptr)
    {
        m_pOutdoorPartyRuntime->setRunning(m_settings.alwaysRun);
        m_pOutdoorPartyRuntime->setDebugFlyingOverride(m_settings.startFlying);
        m_pOutdoorPartyRuntime->setMovementSpeedMultiplier(m_settings.movementSpeedMultiplier);
    }
}

void GameApplication::applyStartupDebugSettingsToActiveRuntime()
{
    if (m_pMapSceneRuntime == nullptr
        || m_pMapSceneRuntime->kind() != SceneKind::Outdoor
        || m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    if (m_settings.overrideStartPosition)
    {
        m_pOutdoorPartyRuntime->teleportTo(m_settings.startX, m_settings.startY, m_settings.startZ);
    }
}

void GameApplication::shutdownApplication()
{
    m_screenManager.setActiveScreen(nullptr);
    shutdownRenderer();
    m_gameAudioSystem.shutdown();
}

bool GameApplication::loadGameData(const Engine::AssetFileSystem &assetFileSystem)
{
    m_pAssetFileSystem = &assetFileSystem;
    m_gameSession.clear();
    m_gameplayController.bindSession(m_gameSession);
    m_gameplayController.clearRuntime();
    m_screenManager.setActiveScreen(nullptr);

    if (!m_gameDataLoader.loadForGameplay(assetFileSystem))
    {
        return false;
    }

    loadOrCreateSettings();

    if (!m_gameAudioSystem.initialize(
            assetFileSystem,
            m_gameDataLoader.getCharacterDollTable(),
            m_gameDataLoader.getSpellTable()))
    {
        return false;
    }

    const std::vector<MapStatsEntry> &entries = m_gameDataLoader.getMapStats().getEntries();
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!entries.empty() && selectedMap)
    {
        m_gameSession.setCurrentMapFileName(selectedMap->map.fileName);

        for (size_t mapIndex = 0; mapIndex < entries.size(); ++mapIndex)
        {
            if (entries[mapIndex].id == selectedMap->map.id)
            {
                m_mapPickerIndex = mapIndex;
                break;
            }
        }
    }

    applyCurrentSettingsToActiveRuntime();
    m_screenManager.setCurrentMode(AppMode::MainMenu);
    m_bootSeededDwiOnNextRendererInit = !m_settings.startInMainMenu;

    return true;
}

bool GameApplication::initializeRenderer()
{
    shutdownRenderer();

    if (m_bootSeededDwiOnNextRendererInit)
    {
        return initializeStartupSession(true);
    }

    if (m_screenManager.currentMode() == AppMode::MainMenu
        || m_screenManager.currentMode() == AppMode::LoadMenu
        || m_screenManager.currentMode() == AppMode::NewGame)
    {
        openMainMenuScreen();
        return true;
    }

    return initializeSelectedMapRuntime(true);
}

bool GameApplication::initializeStartupSession(bool initializeView)
{
    if (!m_bootSeededDwiOnNextRendererInit)
    {
        return false;
    }

    m_bootSeededDwiOnNextRendererInit = false;
    return startNewSession(std::nullopt, initializeView);
}

bool GameApplication::initializeSelectedMapRuntime(bool initializeView)
{
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap)
    {
        return false;
    }

    if (selectedMap->outdoorMapData)
    {
        m_gameSession.setCurrentSceneKind(SceneKind::Outdoor);
        m_gameSession.setCurrentMapFileName(selectedMap->map.fileName);
        m_pOutdoorPartyRuntime = std::make_unique<OutdoorPartyRuntime>(
            OutdoorMovementDriver(
                *selectedMap->outdoorMapData,
                selectedMap->map.outdoorBounds.enabled
                    ? std::optional<MapBounds>(selectedMap->map.outdoorBounds)
                    : std::nullopt,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                selectedMap->outdoorActorCollisionSet,
                selectedMap->outdoorSpriteObjectCollisionSet
            ),
            m_gameDataLoader.getItemTable()
        );
        bindPartyDependencies(m_pOutdoorPartyRuntime->party());

        if (m_gameSession.partyState())
        {
            bindPartyDependencies(*m_gameSession.partyState());
            m_pOutdoorPartyRuntime->setParty(*m_gameSession.partyState());
        }
        else
        {
            m_pOutdoorPartyRuntime->party().reset();
            m_gameSession.setPartyState(m_pOutdoorPartyRuntime->party());
        }

        m_pOutdoorWorldRuntime = std::make_unique<OutdoorWorldRuntime>();
        m_pOutdoorWorldRuntime->initialize(
            selectedMap->map,
            m_gameDataLoader.getMonsterTable(),
            m_gameDataLoader.getMonsterProjectileTable(),
            m_gameDataLoader.getObjectTable(),
            m_gameDataLoader.getSpellTable(),
            m_gameDataLoader.getItemTable(),
            &m_pOutdoorPartyRuntime->party(),
            m_gameDataLoader.getStandardItemEnchantTable(),
            m_gameDataLoader.getSpecialItemEnchantTable(),
            &m_gameDataLoader.getChestTable(),
            selectedMap->outdoorMapData,
            selectedMap->outdoorMapDeltaData,
            selectedMap->eventRuntimeState,
            selectedMap->outdoorActorPreviewBillboardSet,
            selectedMap->outdoorLandMask,
            selectedMap->outdoorDecorationCollisionSet,
            selectedMap->outdoorActorCollisionSet,
            selectedMap->outdoorSpriteObjectCollisionSet,
            selectedMap->outdoorSpriteObjectBillboardSet
        );

        restoreSavedOutdoorWorldStateForSelectedMap();
        m_pMapSceneRuntime = std::make_unique<OutdoorSceneRuntime>(
            selectedMap->map.fileName,
            selectedMap->map,
            *m_pOutdoorPartyRuntime,
            *m_pOutdoorWorldRuntime,
            selectedMap->localEventIrProgram,
            selectedMap->globalEventIrProgram);
        m_gameplayController.bindRuntime(m_pMapSceneRuntime.get());
        m_screenManager.setCurrentMode(AppMode::GameplayOutdoor);

        m_gameAudioSystem.setBackgroundMusicTrack(selectedMap->map.redbookTrack);
        applyCurrentSettingsToActiveRuntime();

        if (!initializeView)
        {
            return true;
        }

        return m_outdoorGameView.initialize(
            *m_pAssetFileSystem,
            selectedMap->map,
            m_gameDataLoader.getMonsterTable(),
            *selectedMap->outdoorMapData,
            selectedMap->outdoorLandMask,
            selectedMap->outdoorTileColors,
            selectedMap->outdoorTerrainTextureAtlas,
            selectedMap->outdoorBModelTextureSet,
            selectedMap->outdoorDecorationCollisionSet,
            selectedMap->outdoorActorCollisionSet,
            selectedMap->outdoorSpriteObjectCollisionSet,
            selectedMap->outdoorDecorationBillboardSet,
            selectedMap->outdoorActorPreviewBillboardSet,
            selectedMap->outdoorSpriteObjectBillboardSet,
            selectedMap->outdoorMapDeltaData,
            m_gameDataLoader.getChestTable(),
            m_gameDataLoader.getHouseTable(),
            m_gameDataLoader.getClassSkillTable(),
            m_gameDataLoader.getNpcDialogTable(),
            m_gameDataLoader.getRosterTable(),
            m_gameDataLoader.getArcomageLibrary(),
            m_gameDataLoader.getCharacterDollTable(),
            m_gameDataLoader.getCharacterInspectTable(),
            m_gameDataLoader.getObjectTable(),
            m_gameDataLoader.getSpellTable(),
            m_gameDataLoader.getJournalQuestTable(),
            m_gameDataLoader.getJournalHistoryTable(),
            m_gameDataLoader.getJournalAutonoteTable(),
            m_gameDataLoader.getItemTable(),
            m_gameDataLoader.getReadableScrollTable(),
            m_gameDataLoader.getStandardItemEnchantTable(),
            m_gameDataLoader.getSpecialItemEnchantTable(),
            m_gameDataLoader.getItemEquipPosTable(),
            selectedMap->localStrTable,
            selectedMap->localEvtProgram,
            selectedMap->globalEvtProgram,
            &m_gameAudioSystem,
            *static_cast<OutdoorSceneRuntime *>(m_pMapSceneRuntime.get()),
            m_settings,
            m_gameDataLoader.getMapStats().getEntries(),
            [this](
                const std::filesystem::path &path,
                const std::string &saveName,
                const std::vector<uint8_t> &previewBmp,
                std::string &error) -> bool
            {
                static_cast<void>(error);
                return quickSaveToPath(path, saveName, previewBmp);
            },
            [this](const std::filesystem::path &path, std::string &error) -> bool
            {
                static_cast<void>(error);
                return quickLoadFromPath(path, true);
            },
            [this](const GameSettings &settings)
            {
                m_settings = settings;
                std::string error;

                if (!saveGameSettings(settingsFilePath(), m_settings, error))
                {
                    std::cerr << "GameApplication: failed to write settings.ini: " << error << '\n';
                }

                applyCurrentSettingsToActiveRuntime();
            }
        );
    }

    if (selectedMap->indoorMapData)
    {
        m_gameSession.setCurrentSceneKind(SceneKind::Indoor);
        m_gameSession.setCurrentMapFileName(selectedMap->map.fileName);
        m_screenManager.setCurrentMode(AppMode::GameplayIndoor);
        m_gameAudioSystem.setBackgroundMusicTrack(selectedMap->map.redbookTrack);
        applyCurrentSettingsToActiveRuntime();
        Party &party = ensureSessionPartyState();
        std::unique_ptr<IndoorSceneRuntime> pIndoorSceneRuntime = std::make_unique<IndoorSceneRuntime>(
            selectedMap->map.fileName,
            party,
            selectedMap->indoorMapDeltaData,
            selectedMap->eventRuntimeState,
            selectedMap->localEventIrProgram,
            selectedMap->globalEventIrProgram
        );
        const std::unordered_map<std::string, IndoorSceneRuntime::Snapshot>::const_iterator indoorStateIt =
            m_gameSession.indoorSceneStates().find(selectedMap->map.fileName);

        if (indoorStateIt != m_gameSession.indoorSceneStates().end())
        {
            pIndoorSceneRuntime->restoreSnapshot(indoorStateIt->second);
        }

        if (initializeView
            && !m_indoorDebugRenderer.initialize(
                m_pAssetFileSystem != nullptr ? m_pAssetFileSystem->getAssetScaleTier() : Engine::AssetScaleTier::X1,
                selectedMap->map,
                m_gameDataLoader.getMonsterTable(),
                *selectedMap->indoorMapData,
                selectedMap->indoorTextureSet,
                selectedMap->indoorDecorationBillboardSet,
                selectedMap->indoorActorPreviewBillboardSet,
                selectedMap->indoorSpriteObjectBillboardSet,
                *pIndoorSceneRuntime,
                m_gameDataLoader.getChestTable(),
                m_gameDataLoader.getHouseTable(),
                selectedMap->localStrTable,
                selectedMap->localEvtProgram,
                selectedMap->globalEvtProgram))
        {
            return false;
        }

        m_pMapSceneRuntime = std::move(pIndoorSceneRuntime);
        m_gameplayController.bindRuntime(m_pMapSceneRuntime.get());
        return true;
    }

    return false;
}

Party &GameApplication::ensureSessionPartyState()
{
    if (!m_gameSession.partyState())
    {
        Party party = {};
        bindPartyDependencies(party);
        party.reset();
        m_gameSession.setPartyState(std::move(party));
    }
    else
    {
        bindPartyDependencies(*m_gameSession.partyState());
    }

    return *m_gameSession.partyState();
}

void GameApplication::bindPartyDependencies(Party &party) const
{
    party.setItemTable(&m_gameDataLoader.getItemTable());
    party.setCharacterDollTable(&m_gameDataLoader.getCharacterDollTable());
    party.setItemEnchantTables(
        &m_gameDataLoader.getStandardItemEnchantTable(),
        &m_gameDataLoader.getSpecialItemEnchantTable());
    party.setClassSkillTable(&m_gameDataLoader.getClassSkillTable());
}

void GameApplication::synchronizeSessionFromRuntime()
{
    if (m_pMapSceneRuntime == nullptr)
    {
        return;
    }

    m_gameplayController.synchronizeSessionFromRuntime();
    m_gameSession.setCurrentSceneKind(m_pMapSceneRuntime->kind());
    m_gameSession.setCurrentMapFileName(m_pMapSceneRuntime->currentMapFileName());

    if (m_pMapSceneRuntime->kind() == SceneKind::Outdoor
        && m_pOutdoorPartyRuntime != nullptr
        && m_pOutdoorWorldRuntime != nullptr)
    {
        m_gameSession.captureOutdoorRuntimeState(
            m_pMapSceneRuntime->currentMapFileName(),
            m_pMapSceneRuntime->party(),
            m_pOutdoorPartyRuntime->snapshot(),
            m_pOutdoorWorldRuntime->snapshot(),
            m_outdoorGameView.cameraYawRadians(),
            m_outdoorGameView.cameraPitchRadians());
        return;
    }

    if (m_pMapSceneRuntime->kind() == SceneKind::Indoor)
    {
        const IndoorSceneRuntime *pIndoorRuntime = static_cast<const IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
        m_gameSession.captureIndoorRuntimeState(
            m_pMapSceneRuntime->currentMapFileName(),
            m_pMapSceneRuntime->party(),
            pIndoorRuntime->snapshot());
    }
}

bool GameApplication::loadCurrentSessionMap(bool initializeView)
{
    if (m_pAssetFileSystem == nullptr || !m_gameSession.hasCurrentMapFileName())
    {
        return false;
    }

    if (!m_gameDataLoader.loadMapByFileNameForGameplay(*m_pAssetFileSystem, m_gameSession.currentMapFileName()))
    {
        return false;
    }

    shutdownRenderer();

    if (!initializeSelectedMapRuntime(initializeView))
    {
        return false;
    }

    syncMapPickerToSelectedMap();
    return true;
}

bool GameApplication::applyCurrentSessionToRuntime(bool initializeView)
{
    if (m_pMapSceneRuntime == nullptr)
    {
        return true;
    }

    if (m_pMapSceneRuntime->kind() == SceneKind::Outdoor && m_pOutdoorPartyRuntime != nullptr)
    {
        if (m_gameSession.outdoorPartyState())
        {
            m_pOutdoorPartyRuntime->restoreSnapshot(*m_gameSession.outdoorPartyState());
        }

        if (initializeView)
        {
            m_outdoorGameView.setCameraAngles(
                m_gameSession.outdoorCameraYawRadians(),
                m_gameSession.outdoorCameraPitchRadians());
        }

        applyCurrentSettingsToActiveRuntime();
    }

    synchronizeSessionFromRuntime();
    return true;
}

void GameApplication::syncMapPickerToSelectedMap()
{
    const std::vector<MapStatsEntry> &entries = m_gameDataLoader.getMapStats().getEntries();
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap)
    {
        return;
    }

    for (size_t mapIndex = 0; mapIndex < entries.size(); ++mapIndex)
    {
        if (entries[mapIndex].id == selectedMap->map.id)
        {
            m_mapPickerIndex = mapIndex;
            break;
        }
    }
}

void GameApplication::captureCurrentSceneState()
{
    synchronizeSessionFromRuntime();
}

void GameApplication::restoreSavedOutdoorWorldStateForSelectedMap()
{
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap || m_pOutdoorWorldRuntime == nullptr || !selectedMap->outdoorMapData)
    {
        return;
    }

    const std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot>::const_iterator stateIt =
        m_gameSession.outdoorWorldStates().find(selectedMap->map.fileName);

    if (stateIt == m_gameSession.outdoorWorldStates().end())
    {
        return;
    }

    m_pOutdoorWorldRuntime->restoreSnapshot(stateIt->second);
}

void GameApplication::shutdownRenderer()
{
    m_outdoorGameView.shutdown();
    m_indoorDebugRenderer.shutdown();
    m_gameplayController.clearRuntime();
    m_pMapSceneRuntime.reset();
    m_pOutdoorPartyRuntime.reset();
    m_pOutdoorWorldRuntime.reset();
}

bool GameApplication::reloadSelectedMap()
{
    if (m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    captureCurrentSceneState();

    const std::vector<MapStatsEntry> &entries = m_gameDataLoader.getMapStats().getEntries();

    if (entries.empty() || m_mapPickerIndex >= entries.size())
    {
        return false;
    }

    if (!m_gameDataLoader.loadMapById(*m_pAssetFileSystem, entries[m_mapPickerIndex].id))
    {
        return false;
    }

    return initializeRenderer();
}

void GameApplication::updateQuickSaveInput()
{
    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);

    if (pKeyboardState == nullptr)
    {
        return;
    }

    if (pKeyboardState[SDL_SCANCODE_F9])
    {
        if (!m_quickSaveLatch)
        {
            m_pendingQuickSave = true;
            m_quickSaveLatch = true;
        }
    }
    else
    {
        m_quickSaveLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F10])
    {
        if (!m_quickLoadLatch)
        {
            m_pendingQuickLoad = true;
            m_quickLoadLatch = true;
        }
    }
    else
    {
        m_quickLoadLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F5])
    {
        if (!m_advanceTimeLatch)
        {
            m_pendingAdvanceTime = true;
            m_advanceTimeLatch = true;
        }
    }
    else
    {
        m_advanceTimeLatch = false;
    }
}

bool GameApplication::processPendingQuickSaveInput()
{
    if (m_pendingAdvanceTime)
    {
        m_pendingAdvanceTime = false;

        if (m_gameplayController.advanceGameMinutes(60.0f))
        {
            reportQuickSaveStatus("Advanced time by 1 hour");
            return true;
        }

        reportQuickSaveStatus("Time advance unavailable");
        return false;
    }

    if (m_pendingQuickLoad)
    {
        m_pendingQuickLoad = false;
        m_pendingQuickSave = false;
        return quickLoad();
    }

    if (m_pendingQuickSave)
    {
        m_pendingQuickSave = false;
        return quickSave();
    }

    return false;
}

bool GameApplication::quickSave()
{
    if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Outdoor)
    {
        return m_outdoorGameView.requestQuickSave();
    }

    return quickSaveToPath(std::filesystem::path("saves") / "quicksave.oysav");
}

bool GameApplication::quickSaveToPath(
    const std::filesystem::path &path,
    const std::string &saveName,
    const std::vector<uint8_t> &previewBmp)
{
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap || m_pMapSceneRuntime == nullptr)
    {
        reportQuickSaveStatus("Quick save unavailable");
        return false;
    }

    synchronizeSessionFromRuntime();
    std::optional<GameSaveData> saveData = m_gameSession.buildSaveData();

    if (!saveData)
    {
        reportQuickSaveStatus("Quick save unavailable");
        return false;
    }

    saveData->saveName = saveName;
    saveData->previewBmp = previewBmp;

    std::string error;

    if (!saveGameDataToPath(path, *saveData, error))
    {
        reportQuickSaveStatus("Quick save failed: " + error);
        return false;
    }

    m_gameSession.setCurrentSavePath(path);
    reportQuickSaveStatus("Quick save written");
    return true;
}

bool GameApplication::quickLoad()
{
    return quickLoadFromPath(std::filesystem::path("saves") / "quicksave.oysav", true);
}

bool GameApplication::quickLoadFromPath(const std::filesystem::path &path, bool initializeView)
{
    if (m_pAssetFileSystem == nullptr)
    {
        reportQuickSaveStatus("Quick load unavailable");
        return false;
    }

    std::string error;
    const std::optional<GameSaveData> saveData = loadGameDataFromPath(path, error);

    if (!saveData)
    {
        reportQuickSaveStatus("Quick load failed: " + error);
        return false;
    }

    m_gameSession.restoreFromSaveData(
        *saveData,
        m_gameDataLoader.getItemTable(),
        m_gameDataLoader.getStandardItemEnchantTable(),
        m_gameDataLoader.getSpecialItemEnchantTable(),
        m_gameDataLoader.getClassSkillTable());
    m_gameSession.setCurrentSavePath(path);

    if (!loadCurrentSessionMap(initializeView))
    {
        reportQuickSaveStatus("Quick load failed: runtime init failed");
        return false;
    }

    if (!applyCurrentSessionToRuntime(initializeView))
    {
        reportQuickSaveStatus("Quick load failed: runtime apply failed");
        return false;
    }

    reportQuickSaveStatus("Quick load applied");
    return true;
}

void GameApplication::openMainMenuScreen()
{
    if (m_pAssetFileSystem == nullptr)
    {
        return;
    }

    m_screenManager.setActiveScreen(std::make_unique<MainMenuScreen>(
        *m_pAssetFileSystem,
        [this]()
        {
            openNewGameScreen();
        },
        [this]()
        {
            openLoadMenuScreen();
        },
        [this]()
        {
            requestApplicationQuit();
        }));
}

void GameApplication::openLoadMenuScreen()
{
    if (m_pAssetFileSystem == nullptr)
    {
        return;
    }

    m_screenManager.setActiveScreen(std::make_unique<LoadMenuScreen>(
        *m_pAssetFileSystem,
        m_gameDataLoader.getMapStats().getEntries(),
        [this](const std::filesystem::path &path)
        {
            loadSessionFromPath(path);
        },
        [this]()
        {
            openMainMenuScreen();
        }));
}

void GameApplication::openNewGameScreen(bool returnToGameplayMenu)
{
    if (m_pAssetFileSystem == nullptr)
    {
        return;
    }

    m_gameAudioSystem.stopBackgroundMusicImmediate();

    m_screenManager.setActiveScreen(std::make_unique<NewGameScreen>(
        *m_pAssetFileSystem,
        &m_gameAudioSystem,
        m_gameDataLoader.getCharacterDollTable(),
        m_gameDataLoader.getCharacterInspectTable(),
        m_gameDataLoader.getClassSkillTable(),
        [this](const Character &character)
        {
            startNewSessionFromCharacterCreation(character);
        },
        [this, returnToGameplayMenu]()
        {
            if (returnToGameplayMenu)
            {
                const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

                m_screenManager.setActiveScreen(nullptr);
                m_outdoorGameView.reopenMenuScreen();

                if (selectedMap)
                {
                    m_gameAudioSystem.stopBackgroundMusicImmediate();
                    m_gameAudioSystem.setBackgroundMusicTrack(selectedMap->map.redbookTrack);
                }
            }
            else
            {
                openMainMenuScreen();
            }
        }));
}

bool GameApplication::startNewSession(std::optional<uint32_t> rosterId, bool initializeView)
{
    if (m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    m_screenManager.setActiveScreen(nullptr);
    shutdownRenderer();
    m_gameSession.clear();
    m_gameSession.clearCurrentSavePath();
    m_gameSession.setCurrentSceneKind(SceneKind::Outdoor);
    m_gameSession.setCurrentMapFileName(
        m_settings.startMapFile.empty() ? std::string(DefaultStartupMapFile) : m_settings.startMapFile);

    if (!loadCurrentSessionMap(initializeView))
    {
        if (m_gameSession.currentMapFileName() != DefaultStartupMapFile)
        {
            m_gameSession.setCurrentMapFileName(DefaultStartupMapFile);

            if (loadCurrentSessionMap(initializeView))
            {
                // Use the default startup map when the configured one cannot be loaded.
            }
            else
            {
                openMainMenuScreen();
                return false;
            }
        }
        else
        {
            openMainMenuScreen();
            return false;
        }
    }

    if (m_pOutdoorPartyRuntime == nullptr)
    {
        openMainMenuScreen();
        return false;
    }

    const bool shouldSeedParty = rosterId.has_value() || m_settings.preseedParty;
    std::optional<uint32_t> effectiveRosterId = rosterId;

    if (!effectiveRosterId.has_value() && m_settings.preseedParty && m_settings.partySeedRosterId != 0)
    {
        effectiveRosterId = m_settings.partySeedRosterId;
    }

    if (shouldSeedParty)
    {
        const RosterEntry *pRosterEntry =
            effectiveRosterId.has_value() ? m_gameDataLoader.getRosterTable().get(*effectiveRosterId) : nullptr;

        if (effectiveRosterId.has_value() && pRosterEntry == nullptr)
        {
            seedSimulatedPartyFromRoster(
                m_pOutdoorPartyRuntime->party(),
                m_gameDataLoader.getRosterTable(),
                std::nullopt);
            seedSimulatedAdventurersInn(
                m_pOutdoorPartyRuntime->party(),
                m_gameDataLoader.getRosterTable(),
                m_gameDataLoader.getNpcDialogTable(),
                std::nullopt);
        }
        else
        {
            seedSimulatedPartyFromRoster(
                m_pOutdoorPartyRuntime->party(),
                m_gameDataLoader.getRosterTable(),
                effectiveRosterId);
            seedSimulatedAdventurersInn(
                m_pOutdoorPartyRuntime->party(),
                m_gameDataLoader.getRosterTable(),
                m_gameDataLoader.getNpcDialogTable(),
                effectiveRosterId);
        }
    }

    applyCurrentSettingsToActiveRuntime();
    applyStartupDebugSettingsToActiveRuntime();
    synchronizeSessionFromRuntime();
    return true;
}

bool GameApplication::startNewSessionFromCharacterCreation(const Character &character, bool initializeView)
{
    if (m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    m_screenManager.setActiveScreen(nullptr);
    shutdownRenderer();
    m_gameSession.clear();
    m_gameSession.clearCurrentSavePath();
    m_gameSession.setCurrentSceneKind(SceneKind::Outdoor);
    m_gameSession.setCurrentMapFileName(DefaultStartupMapFile);

    if (!loadCurrentSessionMap(initializeView))
    {
        openMainMenuScreen();
        return false;
    }

    if (m_pOutdoorPartyRuntime == nullptr)
    {
        openMainMenuScreen();
        return false;
    }

    PartySeed seed = {};
    seed.gold = 200;
    seed.food = 5;
    seed.members.push_back(
        buildFreshCreatedCharacter(
            character,
            m_gameDataLoader.getItemTable(),
            m_gameDataLoader.getStandardItemEnchantTable(),
            m_gameDataLoader.getSpecialItemEnchantTable()));
    m_pOutdoorPartyRuntime->party().seed(seed);
    seedSimulatedAdventurersInn(
        m_pOutdoorPartyRuntime->party(),
        m_gameDataLoader.getRosterTable(),
        m_gameDataLoader.getNpcDialogTable(),
        std::nullopt);
    applyCurrentSettingsToActiveRuntime();
    synchronizeSessionFromRuntime();
    return true;
}

bool GameApplication::loadSessionFromPath(const std::filesystem::path &path)
{
    m_screenManager.setActiveScreen(nullptr);

    if (quickLoadFromPath(path, true))
    {
        return true;
    }

    openLoadMenuScreen();
    return false;
}

void GameApplication::requestApplicationQuit() const
{
    SDL_Event event = {};
    event.type = SDL_EVENT_QUIT;
    SDL_PushEvent(&event);
}

void GameApplication::reportQuickSaveStatus(const std::string &status)
{
    std::cout << status << '\n';

    if (EventRuntimeState *pEventRuntimeState = m_gameplayController.eventRuntimeState())
    {
        pEventRuntimeState->lastActivationResult = status;
    }
}

void GameApplication::updateMapPickerInput()
{
    constexpr uint64_t InitialRepeatDelayMs = 300;
    constexpr uint64_t HeldRepeatIntervalMs = 70;

    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);

    if (pKeyboardState == nullptr)
    {
        return;
    }

    if (pKeyboardState[SDL_SCANCODE_F8])
    {
        if (!m_pickerToggleLatch)
        {
            m_showMapPicker = !m_showMapPicker;
            m_pickerToggleLatch = true;
        }
    }
    else
    {
        m_pickerToggleLatch = false;
    }

    if (!m_showMapPicker)
    {
        m_pickerApplyLatch = false;
        m_pickerNextUpRepeatTick = 0;
        m_pickerNextDownRepeatTick = 0;
        return;
    }

    const std::vector<MapStatsEntry> &entries = m_gameDataLoader.getMapStats().getEntries();

    if (entries.empty())
    {
        return;
    }

    const uint64_t currentTickCount = SDL_GetTicks();

    if (pKeyboardState[SDL_SCANCODE_UP])
    {
        if (m_pickerNextUpRepeatTick == 0 || currentTickCount >= m_pickerNextUpRepeatTick)
        {
            m_mapPickerIndex = (m_mapPickerIndex == 0) ? (entries.size() - 1) : (m_mapPickerIndex - 1);
            m_pickerNextUpRepeatTick = (m_pickerNextUpRepeatTick == 0)
                ? (currentTickCount + InitialRepeatDelayMs)
                : (currentTickCount + HeldRepeatIntervalMs);
        }
    }
    else
    {
        m_pickerNextUpRepeatTick = 0;
    }

    if (pKeyboardState[SDL_SCANCODE_DOWN])
    {
        if (m_pickerNextDownRepeatTick == 0 || currentTickCount >= m_pickerNextDownRepeatTick)
        {
            m_mapPickerIndex = (m_mapPickerIndex + 1) % entries.size();
            m_pickerNextDownRepeatTick = (m_pickerNextDownRepeatTick == 0)
                ? (currentTickCount + InitialRepeatDelayMs)
                : (currentTickCount + HeldRepeatIntervalMs);
        }
    }
    else
    {
        m_pickerNextDownRepeatTick = 0;
    }

    if (pKeyboardState[SDL_SCANCODE_RETURN])
    {
        if (!m_pickerApplyLatch)
        {
            const bool reloadSucceeded = reloadSelectedMap();
            (void)reloadSucceeded;
            m_pickerApplyLatch = true;
        }
    }
    else
    {
        m_pickerApplyLatch = false;
    }
}

void GameApplication::renderMapPickerOverlay() const
{
    if (!m_showMapPicker)
    {
        return;
    }

    const std::vector<MapStatsEntry> &entries = m_gameDataLoader.getMapStats().getEntries();
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();
    bgfx::dbgTextPrintf(0, 13, 0x0f, "Map Picker: Up/Down select  Enter load  F8 close");

    if (selectedMap)
    {
        bgfx::dbgTextPrintf(
            0,
            14,
            0x0f,
            "Current: %d %s (%s)",
            selectedMap->map.id,
            selectedMap->map.name.c_str(),
            selectedMap->map.fileName.c_str()
        );
    }

    if (entries.empty())
    {
        bgfx::dbgTextPrintf(0, 15, 0x0c, "No maps available");
        return;
    }

    const size_t visibleLineCount = 10;
    const size_t startIndex = (m_mapPickerIndex > 4) ? (m_mapPickerIndex - 4) : 0;
    const size_t endIndex = std::min(entries.size(), startIndex + visibleLineCount);

    for (size_t index = startIndex; index < endIndex; ++index)
    {
        const MapStatsEntry &entry = entries[index];
        const bool isHighlighted = index == m_mapPickerIndex;
        const uint8_t color = isHighlighted ? 0x0e : 0x0f;
        const char *pKind = entry.isTopLevelArea ? "ODM" : "BLV";

        bgfx::dbgTextPrintf(
            0,
            static_cast<uint16_t>(15 + (index - startIndex)),
            color,
            "%c %3d %-3s %-28s %s",
            isHighlighted ? '>' : ' ',
            entry.id,
            pKind,
            entry.name.c_str(),
            entry.fileName.c_str()
        );
    }
}

void GameApplication::renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds)
{
    processPendingArcomageGame();

    if (IScreen *pActiveScreen = m_screenManager.activeScreen())
    {
        pActiveScreen->renderFrame(width, height, mouseWheelDelta, deltaSeconds);
        handleCompletedArcomageScreen();
        m_gameAudioSystem.update(0.0f, 0.0f, 0.0f, deltaSeconds);
        return;
    }

    updateQuickSaveInput();
    updateMapPickerInput();
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (m_pMapSceneRuntime != nullptr
        && m_pMapSceneRuntime->kind() == SceneKind::Outdoor
        && selectedMap
        && selectedMap->outdoorMapData)
    {
        m_outdoorGameView.render(width, height, mouseWheelDelta, deltaSeconds);

        if (m_outdoorGameView.consumePendingOpenNewGameScreenRequest())
        {
            openNewGameScreen(true);
            return;
        }

        if (m_pOutdoorPartyRuntime != nullptr)
        {
            const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
            m_gameAudioSystem.update(moveState.x, moveState.y, moveState.footZ + 96.0f, deltaSeconds);
        }
        else
        {
            m_gameAudioSystem.update(0.0f, 0.0f, 0.0f, deltaSeconds);
        }

        processPendingMapMove();

        if (processPendingQuickSaveInput())
        {
            return;
        }

        renderMapPickerOverlay();
        return;
    }

    if (m_pMapSceneRuntime != nullptr
        && m_pMapSceneRuntime->kind() == SceneKind::Indoor
        && selectedMap
        && selectedMap->indoorMapData)
    {
        m_indoorDebugRenderer.render(width, height, mouseWheelDelta, deltaSeconds);
        m_gameAudioSystem.update(0.0f, 0.0f, 0.0f, deltaSeconds);
        processPendingMapMove();

        if (processPendingQuickSaveInput())
        {
            return;
        }

        renderMapPickerOverlay();
    }
}

bool GameApplication::processPendingMapMove()
{
    if (m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    std::optional<EventRuntimeState::PendingMapMove> pendingMapMove = m_gameplayController.consumePendingMapMove();

    if (!pendingMapMove)
    {
        return false;
    }

    synchronizeSessionFromRuntime();

    const bool isSameMapTeleport =
        !pendingMapMove->mapName || pendingMapMove->mapName->empty() || *pendingMapMove->mapName == "0";

    if (isSameMapTeleport)
    {
        if (m_pMapSceneRuntime != nullptr
            && m_pMapSceneRuntime->kind() == SceneKind::Outdoor
            && m_pOutdoorPartyRuntime != nullptr)
        {
            m_pOutdoorPartyRuntime->teleportTo(
                static_cast<float>(-pendingMapMove->x),
                static_cast<float>(pendingMapMove->y),
                static_cast<float>(pendingMapMove->z)
            );
        }

        if (pendingMapMove->directionDegrees.has_value()
            && m_pMapSceneRuntime != nullptr
            && m_pMapSceneRuntime->kind() == SceneKind::Outdoor)
        {
            const float yawRadians = mapMoveHeadingDegreesToOutdoorYawRadians(*pendingMapMove->directionDegrees);
            m_outdoorGameView.setCameraAngles(yawRadians, m_outdoorGameView.cameraPitchRadians());
        }

        synchronizeSessionFromRuntime();
        return true;
    }

    const std::string targetMapName = *pendingMapMove->mapName;
    const std::string previousMapFileName = m_gameSession.currentMapFileName();

    captureCurrentSceneState();

    m_gameSession.setCurrentMapFileName(targetMapName);

    if (!loadCurrentSessionMap(true))
    {
        m_gameSession.setCurrentMapFileName(previousMapFileName);
        return false;
    }

    if (m_pMapSceneRuntime != nullptr
        && m_pMapSceneRuntime->kind() == SceneKind::Outdoor
        && m_pOutdoorPartyRuntime != nullptr
        && !pendingMapMove->useMapStartPosition)
    {
        m_pOutdoorPartyRuntime->teleportTo(
            static_cast<float>(-pendingMapMove->x),
            static_cast<float>(pendingMapMove->y),
            static_cast<float>(pendingMapMove->z)
        );
    }

    if (pendingMapMove->directionDegrees.has_value()
        && m_pMapSceneRuntime != nullptr
        && m_pMapSceneRuntime->kind() == SceneKind::Outdoor)
    {
        const float yawRadians = mapMoveHeadingDegreesToOutdoorYawRadians(*pendingMapMove->directionDegrees);
        m_outdoorGameView.setCameraAngles(yawRadians, m_outdoorGameView.cameraPitchRadians());
    }

    synchronizeSessionFromRuntime();
    return true;
}

bool GameApplication::processPendingArcomageGame()
{
    if (m_screenManager.activeScreen() != nullptr || m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    const std::optional<EventRuntimeState::PendingArcomageGame> pendingArcomageGame =
        m_gameplayController.consumePendingArcomageGame();

    if (!pendingArcomageGame.has_value())
    {
        return false;
    }

    Party *pParty = nullptr;

    if (m_pOutdoorPartyRuntime != nullptr)
    {
        pParty = &m_pOutdoorPartyRuntime->party();
    }
    else if (m_gameSession.partyState().has_value())
    {
        pParty = &*m_gameSession.partyState();
    }

    if (pParty == nullptr)
    {
        return false;
    }

    const HouseEntry *pHouseEntry = m_gameDataLoader.getHouseTable().get(pendingArcomageGame->houseId);
    const ArcomageTavernRule *pRule = m_gameDataLoader.getArcomageLibrary().ruleForHouse(pendingArcomageGame->houseId);

    if (pHouseEntry == nullptr || pRule == nullptr)
    {
        return false;
    }

    const Character *pActiveMember = pParty->activeMember();
    const std::string playerName =
        (pActiveMember != nullptr && !pActiveMember->name.empty()) ? pActiveMember->name : "Party";
    const std::string opponentName =
        !pHouseEntry->proprietorName.empty() ? pHouseEntry->proprietorName : pHouseEntry->name;
    int winGoldReward = 0;

    if (!pParty->hasArcomageWinAt(pendingArcomageGame->houseId))
    {
        winGoldReward = static_cast<int>(pHouseEntry->priceMultiplier * 100.0f);
    }

    m_screenManager.setActiveScreen(std::make_unique<ArcomageScreen>(
        *m_pAssetFileSystem,
        &m_gameAudioSystem,
        m_gameDataLoader.getArcomageLibrary(),
        pendingArcomageGame->houseId,
        playerName,
        opponentName,
        winGoldReward,
        SDL_GetTicks()
    ));

    return true;
}

void GameApplication::handleCompletedArcomageScreen()
{
    ArcomageScreen *pArcomageScreen = dynamic_cast<ArcomageScreen *>(m_screenManager.activeScreen());

    if (pArcomageScreen == nullptr || !pArcomageScreen->shouldClose())
    {
        return;
    }

    const ArcomageState &state = pArcomageScreen->state();
    Party *pParty = nullptr;

    if (m_pOutdoorPartyRuntime != nullptr)
    {
        pParty = &m_pOutdoorPartyRuntime->party();
    }
    else if (m_gameSession.partyState().has_value())
    {
        pParty = &*m_gameSession.partyState();
    }

    std::optional<std::string> arcomageStatusText;

    if (pParty != nullptr && state.result.finished && state.result.winnerIndex.has_value())
    {
        if (*state.result.winnerIndex == 0)
        {
            int goldReward = 0;
            const HouseEntry *pHouseEntry = m_gameDataLoader.getHouseTable().get(state.houseId);

            if (pHouseEntry != nullptr && !pParty->hasArcomageWinAt(state.houseId))
            {
                goldReward = static_cast<int>(pHouseEntry->priceMultiplier * 100.0f);
            }

            uint32_t firstWinAwardId = 0;
            const ArcomageTavernRule *pRule = m_gameDataLoader.getArcomageLibrary().ruleForHouse(state.houseId);

            if (pRule != nullptr)
            {
                firstWinAwardId = pRule->firstWinAwardId;
            }

            pParty->recordArcomageWin(state.houseId, goldReward, firstWinAwardId);
            arcomageStatusText = "You have won " + std::to_string(goldReward) + " gold!";
        }
        else if (*state.result.winnerIndex == 1)
        {
            pParty->recordArcomageLoss();
        }

        if (m_pOutdoorPartyRuntime != nullptr)
        {
            synchronizeSessionFromRuntime();
        }
        else
        {
            m_gameSession.setPartyState(*pParty);
        }
    }

    m_screenManager.setActiveScreen(nullptr);

    if (arcomageStatusText.has_value())
    {
        if (EventRuntimeState *pEventRuntimeState = m_gameplayController.eventRuntimeState())
        {
            pEventRuntimeState->lastActivationResult = *arcomageStatusText;
        }

        if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Outdoor)
        {
            m_outdoorGameView.showStatusBarEvent(*arcomageStatusText, 4.0f);
        }
    }

    if (m_pMapSceneRuntime != nullptr)
    {
        m_screenManager.setCurrentMode(
            m_pMapSceneRuntime->kind() == SceneKind::Outdoor ? AppMode::GameplayOutdoor : AppMode::GameplayIndoor
        );
    }
}
}

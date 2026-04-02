#include "game/app/GameApplication.h"

#include "game/scene/IndoorSceneRuntime.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/ui/screens/LoadMenuScreen.h"
#include "game/ui/screens/MainMenuScreen.h"
#include "game/ui/screens/NewGameScreen.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <algorithm>
#include <filesystem>
#include <functional>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
}

GameApplication::GameApplication(const Engine::ApplicationConfig &config)
    : m_engineApplication(
        config,
        std::bind(&GameApplication::loadGameData, this, std::placeholders::_1),
        std::bind(&GameApplication::initializeRenderer, this),
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

void GameApplication::shutdownApplication()
{
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

    m_screenManager.setCurrentMode(AppMode::MainMenu);
    m_bootSeededDwiOnNextRendererInit = true;

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
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                selectedMap->outdoorActorCollisionSet,
                selectedMap->outdoorSpriteObjectCollisionSet
            ),
            m_gameDataLoader.getItemTable()
        );
        m_pOutdoorPartyRuntime->party().setItemEnchantTables(
            &m_gameDataLoader.getStandardItemEnchantTable(),
            &m_gameDataLoader.getSpecialItemEnchantTable());
        m_pOutdoorPartyRuntime->party().setClassSkillTable(&m_gameDataLoader.getClassSkillTable());

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
            *m_pOutdoorPartyRuntime,
            *m_pOutdoorWorldRuntime,
            selectedMap->localEventIrProgram,
            selectedMap->globalEventIrProgram);
        m_gameplayController.bindRuntime(m_pMapSceneRuntime.get());
        m_screenManager.setCurrentMode(AppMode::GameplayOutdoor);

        m_gameAudioSystem.setBackgroundMusicTrack(selectedMap->map.redbookTrack);

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
            m_gameDataLoader.getCharacterDollTable(),
            m_gameDataLoader.getCharacterInspectTable(),
            m_gameDataLoader.getObjectTable(),
            m_gameDataLoader.getSpellTable(),
            m_gameDataLoader.getItemTable(),
            m_gameDataLoader.getReadableScrollTable(),
            m_gameDataLoader.getStandardItemEnchantTable(),
            m_gameDataLoader.getSpecialItemEnchantTable(),
            m_gameDataLoader.getItemEquipPosTable(),
            selectedMap->localStrTable,
            selectedMap->localEvtProgram,
            selectedMap->globalEvtProgram,
            &m_gameAudioSystem,
            *static_cast<OutdoorSceneRuntime *>(m_pMapSceneRuntime.get())
        );
    }

    if (selectedMap->indoorMapData)
    {
        m_gameSession.setCurrentSceneKind(SceneKind::Indoor);
        m_gameSession.setCurrentMapFileName(selectedMap->map.fileName);
        m_screenManager.setCurrentMode(AppMode::GameplayIndoor);
        m_gameAudioSystem.setBackgroundMusicTrack(selectedMap->map.redbookTrack);
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
    return quickSaveToPath(std::filesystem::path("saves") / "quicksave.oysav");
}

bool GameApplication::quickSaveToPath(const std::filesystem::path &path)
{
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap || m_pMapSceneRuntime == nullptr)
    {
        reportQuickSaveStatus("Quick save unavailable");
        return false;
    }

    synchronizeSessionFromRuntime();
    const std::optional<GameSaveData> saveData = m_gameSession.buildSaveData();

    if (!saveData)
    {
        reportQuickSaveStatus("Quick save unavailable");
        return false;
    }

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

void GameApplication::openNewGameScreen()
{
    if (m_pAssetFileSystem == nullptr)
    {
        return;
    }

    m_screenManager.setActiveScreen(std::make_unique<NewGameScreen>(
        *m_pAssetFileSystem,
        m_gameDataLoader.getRosterTable(),
        [this](std::optional<uint32_t> rosterId)
        {
            startNewSession(rosterId);
        },
        [this]()
        {
            openMainMenuScreen();
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
    m_gameSession.setCurrentMapFileName("out01.odm");

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

    if (!rosterId.has_value() || m_pOutdoorPartyRuntime == nullptr)
    {
        synchronizeSessionFromRuntime();
        return true;
    }

    const RosterEntry *pRosterEntry = m_gameDataLoader.getRosterTable().get(*rosterId);

    if (pRosterEntry == nullptr)
    {
        synchronizeSessionFromRuntime();
        return true;
    }

    m_pOutdoorPartyRuntime->party().replaceMemberWithRosterEntry(0, *pRosterEntry);
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
    if (IScreen *pActiveScreen = m_screenManager.activeScreen())
    {
        pActiveScreen->renderFrame(width, height, mouseWheelDelta, deltaSeconds);
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
            const float yawRadians = static_cast<float>(*pendingMapMove->directionDegrees) * Pi / 180.0f;
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
        const float yawRadians = static_cast<float>(*pendingMapMove->directionDegrees) * Pi / 180.0f;
        m_outdoorGameView.setCameraAngles(yawRadians, m_outdoorGameView.cameraPitchRadians());
    }

    synchronizeSessionFromRuntime();
    return true;
}
}

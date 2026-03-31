#include "game/GameApplication.h"

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
    m_outdoorWorldStates.clear();

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
        for (size_t mapIndex = 0; mapIndex < entries.size(); ++mapIndex)
        {
            if (entries[mapIndex].id == selectedMap->map.id)
            {
                m_mapPickerIndex = mapIndex;
                break;
            }
        }
    }

    return true;
}

bool GameApplication::initializeRenderer()
{
    shutdownRenderer();
    return initializeSelectedMapRuntime(true);
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

        if (m_partyState)
        {
            m_partyState->setItemTable(&m_gameDataLoader.getItemTable());
            m_partyState->setItemEnchantTables(
                &m_gameDataLoader.getStandardItemEnchantTable(),
                &m_gameDataLoader.getSpecialItemEnchantTable());
            m_partyState->setClassSkillTable(&m_gameDataLoader.getClassSkillTable());
            m_pOutdoorPartyRuntime->setParty(*m_partyState);
        }
        else
        {
            m_pOutdoorPartyRuntime->party().reset();
            m_partyState = m_pOutdoorPartyRuntime->party();
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
            selectedMap->localEventIrProgram,
            selectedMap->globalEventIrProgram,
            &m_gameAudioSystem,
            m_pOutdoorPartyRuntime.get(),
            m_pOutdoorWorldRuntime.get()
        );
    }

    if (selectedMap->indoorMapData)
    {
        if (!initializeView)
        {
            return true;
        }

        return m_indoorDebugRenderer.initialize(
            selectedMap->map,
            m_gameDataLoader.getMonsterTable(),
            *selectedMap->indoorMapData,
            selectedMap->indoorMapDeltaData,
            selectedMap->indoorTextureSet,
            selectedMap->indoorDecorationBillboardSet,
            selectedMap->indoorActorPreviewBillboardSet,
            selectedMap->indoorSpriteObjectBillboardSet,
            selectedMap->eventRuntimeState,
            m_gameDataLoader.getChestTable(),
            m_gameDataLoader.getHouseTable(),
            selectedMap->localStrTable,
            selectedMap->localEvtProgram,
            selectedMap->globalEvtProgram,
            selectedMap->localEventIrProgram,
            selectedMap->globalEventIrProgram
        );
    }

    return false;
}

void GameApplication::captureCurrentOutdoorWorldState()
{
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap || m_pOutdoorWorldRuntime == nullptr || !selectedMap->outdoorMapData)
    {
        return;
    }

    m_outdoorWorldStates[selectedMap->map.fileName] = m_pOutdoorWorldRuntime->snapshot();
}

void GameApplication::restoreSavedOutdoorWorldStateForSelectedMap()
{
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap || m_pOutdoorWorldRuntime == nullptr || !selectedMap->outdoorMapData)
    {
        return;
    }

    const std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot>::const_iterator stateIt =
        m_outdoorWorldStates.find(selectedMap->map.fileName);

    if (stateIt == m_outdoorWorldStates.end())
    {
        return;
    }

    m_pOutdoorWorldRuntime->restoreSnapshot(stateIt->second);
}

void GameApplication::shutdownRenderer()
{
    m_outdoorGameView.shutdown();
    m_indoorDebugRenderer.shutdown();
    m_pOutdoorPartyRuntime.reset();
    m_pOutdoorWorldRuntime.reset();
}

bool GameApplication::reloadSelectedMap()
{
    if (m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    captureCurrentOutdoorWorldState();

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
}

bool GameApplication::processPendingQuickSaveInput()
{
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

    if (!selectedMap || m_pOutdoorPartyRuntime == nullptr || m_pOutdoorWorldRuntime == nullptr)
    {
        reportQuickSaveStatus("Quick save unavailable");
        return false;
    }

    GameSaveData saveData = {};
    saveData.mapFileName = selectedMap->map.fileName;
    saveData.party = m_pOutdoorPartyRuntime->party().snapshot();
    saveData.outdoorParty = m_pOutdoorPartyRuntime->snapshot();
    saveData.outdoorWorld = m_pOutdoorWorldRuntime->snapshot();
    captureCurrentOutdoorWorldState();
    saveData.outdoorWorldStates = m_outdoorWorldStates;
    saveData.outdoorCameraYawRadians = m_outdoorGameView.cameraYawRadians();
    saveData.outdoorCameraPitchRadians = m_outdoorGameView.cameraPitchRadians();

    std::string error;

    if (!saveGameDataToPath(path, saveData, error))
    {
        reportQuickSaveStatus("Quick save failed: " + error);
        return false;
    }

    m_partyState = m_pOutdoorPartyRuntime->party();
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

    Party restoredParty = {};
    restoredParty.setItemTable(&m_gameDataLoader.getItemTable());
    restoredParty.setItemEnchantTables(
        &m_gameDataLoader.getStandardItemEnchantTable(),
        &m_gameDataLoader.getSpecialItemEnchantTable());
    restoredParty.setClassSkillTable(&m_gameDataLoader.getClassSkillTable());
    restoredParty.restoreSnapshot(saveData->party);
    m_partyState = restoredParty;
    m_outdoorWorldStates = saveData->outdoorWorldStates;
    m_outdoorWorldStates[saveData->mapFileName] = saveData->outdoorWorld;

    if (!m_gameDataLoader.loadMapByFileNameForGameplay(*m_pAssetFileSystem, saveData->mapFileName))
    {
        reportQuickSaveStatus("Quick load failed: map load failed");
        return false;
    }

    shutdownRenderer();

    if (!initializeSelectedMapRuntime(initializeView) || m_pOutdoorPartyRuntime == nullptr || m_pOutdoorWorldRuntime == nullptr)
    {
        reportQuickSaveStatus("Quick load failed: runtime init failed");
        return false;
    }

    m_outdoorGameView.setCameraAngles(saveData->outdoorCameraYawRadians, saveData->outdoorCameraPitchRadians);
    m_pOutdoorPartyRuntime->restoreSnapshot(saveData->outdoorParty);
    m_partyState = m_pOutdoorPartyRuntime->party();

    const std::vector<MapStatsEntry> &entries = m_gameDataLoader.getMapStats().getEntries();
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (selectedMap)
    {
        for (size_t mapIndex = 0; mapIndex < entries.size(); ++mapIndex)
        {
            if (entries[mapIndex].id == selectedMap->map.id)
            {
                m_mapPickerIndex = mapIndex;
                break;
            }
        }
    }

    reportQuickSaveStatus("Quick load applied");
    return true;
}

void GameApplication::reportQuickSaveStatus(const std::string &status) const
{
    std::cout << status << '\n';

    if (m_pOutdoorWorldRuntime != nullptr)
    {
        if (EventRuntimeState *pEventRuntimeState = m_pOutdoorWorldRuntime->eventRuntimeState())
        {
            pEventRuntimeState->lastActivationResult = status;
        }
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
    updateQuickSaveInput();
    updateMapPickerInput();
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (selectedMap && selectedMap->outdoorMapData)
    {
        m_outdoorGameView.render(width, height, mouseWheelDelta, deltaSeconds);

        if (m_pOutdoorPartyRuntime != nullptr)
        {
            const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
            m_gameAudioSystem.update(moveState.x, moveState.y, moveState.footZ + 96.0f);
        }
        else
        {
            m_gameAudioSystem.update(0.0f, 0.0f, 0.0f);
        }

        processPendingOutdoorMapMove();

        if (processPendingQuickSaveInput())
        {
            return;
        }

        renderMapPickerOverlay();
        return;
    }

    if (selectedMap && selectedMap->indoorMapData)
    {
        m_indoorDebugRenderer.render(width, height, mouseWheelDelta, deltaSeconds);
        m_gameAudioSystem.update(0.0f, 0.0f, 0.0f);

        if (processPendingQuickSaveInput())
        {
            return;
        }

        renderMapPickerOverlay();
    }
}

bool GameApplication::processPendingOutdoorMapMove()
{
    if (m_pOutdoorWorldRuntime == nullptr || m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    const std::optional<EventRuntimeState::PendingMapMove> pendingMapMove =
        m_pOutdoorWorldRuntime->consumePendingMapMove();

    if (!pendingMapMove)
    {
        return false;
    }

    if (m_pOutdoorPartyRuntime != nullptr)
    {
        m_partyState = m_pOutdoorPartyRuntime->party();
    }

    const bool isSameMapTeleport =
        !pendingMapMove->mapName || pendingMapMove->mapName->empty() || *pendingMapMove->mapName == "0";

    if (isSameMapTeleport)
    {
        if (m_pOutdoorPartyRuntime != nullptr)
        {
            m_pOutdoorPartyRuntime->teleportTo(
                static_cast<float>(-pendingMapMove->x),
                static_cast<float>(pendingMapMove->y),
                static_cast<float>(pendingMapMove->z)
            );
        }

        if (pendingMapMove->directionDegrees.has_value())
        {
            const float yawRadians = static_cast<float>(*pendingMapMove->directionDegrees) * Pi / 180.0f;
            m_outdoorGameView.setCameraAngles(yawRadians, m_outdoorGameView.cameraPitchRadians());
        }

        return true;
    }

    const std::string targetMapName = *pendingMapMove->mapName;
    captureCurrentOutdoorWorldState();

    if (!m_gameDataLoader.loadMapByFileNameForGameplay(*m_pAssetFileSystem, targetMapName))
    {
        return false;
    }

    if (!initializeRenderer())
    {
        return false;
    }

    if (m_pOutdoorPartyRuntime != nullptr && !pendingMapMove->useMapStartPosition)
    {
        m_pOutdoorPartyRuntime->teleportTo(
            static_cast<float>(-pendingMapMove->x),
            static_cast<float>(pendingMapMove->y),
            static_cast<float>(pendingMapMove->z)
        );
    }

    if (pendingMapMove->directionDegrees.has_value())
    {
        const float yawRadians = static_cast<float>(*pendingMapMove->directionDegrees) * Pi / 180.0f;
        m_outdoorGameView.setCameraAngles(yawRadians, m_outdoorGameView.cameraPitchRadians());
    }

    const std::vector<MapStatsEntry> &entries = m_gameDataLoader.getMapStats().getEntries();
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (selectedMap)
    {
        for (size_t mapIndex = 0; mapIndex < entries.size(); ++mapIndex)
        {
            if (entries[mapIndex].id == selectedMap->map.id)
            {
                m_mapPickerIndex = mapIndex;
                break;
            }
        }
    }

    return true;
}
}

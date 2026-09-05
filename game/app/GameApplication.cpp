#include "game/app/GameApplication.h"

#include "game/StringUtils.h"
#include "game/app/GprofControl.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayHeldItemController.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/party/SkillData.h"
#include "game/party/SpellIds.h"
#include "game/party/SpellSchool.h"
#include "game/render/TextureFiltering.h"
#include "game/events/EventDialogContent.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/maps/MapIdentity.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/NpcDialogTable.h"
#include "game/ui/screens/ArcomageScreen.h"
#include "game/ui/screens/CutsceneVideoScreen.h"
#include "game/ui/screens/LoadGameScreen.h"
#include "game/ui/screens/LoadingOverlayScreen.h"
#include "game/ui/screens/MainMenuScreen.h"
#include "game/ui/screens/NewGameScreen.h"
#include "game/ui/screens/WinGameScreen.h"
#include "engine/BgfxContext.h"
#include "engine/TextTable.h"

#include <imgui.h>
#include <backends/imgui_impl_sdl3.h>
#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <functional>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <random>
#include <set>
#include <sstream>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#if defined(__GLIBC__)
#include <malloc.h>
#endif

namespace OpenYAMM::Game
{
namespace
{
#if defined(__ANDROID__)
constexpr bool IncludeGodLichCharacterCreationCandidate = true;
#else
constexpr bool IncludeGodLichCharacterCreationCandidate = false;
#endif

constexpr float DefaultOutdoorPartyEyeHeight = 176.0f;
constexpr float DefaultOutdoorPartyCollisionRadius = 37.0f;
constexpr float DefaultOutdoorPartyCollisionHeight = 192.0f;
constexpr float DefaultOutdoorPartyMaxStepHeight = 128.0f;

struct PendingMapLeaveOutputs
{
    std::optional<EventRuntimeState::PendingMovie> pendingMovie;
    std::optional<EventRuntimeState::PendingWinGame> pendingWinGame;
    bool pendingReturnToMainMenu = false;
    std::vector<EventRuntimeState::PendingSound> pendingSounds;
};

double millisecondsFromNanoseconds(uint64_t nanoseconds)
{
    return static_cast<double>(nanoseconds) / 1000000.0;
}

uint64_t averageNanoseconds(uint64_t totalNanoseconds, uint64_t count)
{
    return count != 0 ? totalNanoseconds / count : 0;
}

uint64_t nanosecondsToMicroseconds(uint64_t nanoseconds)
{
    return nanoseconds / 1000ULL;
}

void releaseUnusedHeapPages()
{
#if defined(__GLIBC__)
    static_cast<void>(malloc_trim(0));
#endif
}

const char *gameplayUiAssetLoadKindName(GameplayUiAssetLoadKind kind)
{
    switch (kind)
    {
        case GameplayUiAssetLoadKind::HudTexture:
            return "hud_texture";
        case GameplayUiAssetLoadKind::ItemIcon:
            return "item_icon";
        case GameplayUiAssetLoadKind::HudFont:
            return "hud_font";
        case GameplayUiAssetLoadKind::SolidTexture:
            return "solid_texture";
        case GameplayUiAssetLoadKind::DynamicTexture:
            return "dynamic_texture";
        case GameplayUiAssetLoadKind::HudTextureColor:
            return "hud_texture_color";
        case GameplayUiAssetLoadKind::HudTextureColorModulated:
            return "hud_texture_color_modulated";
        case GameplayUiAssetLoadKind::HudFontColor:
            return "hud_font_color";
    }

    return "unknown";
}

#if defined(__ANDROID__)
bool isAndroidFingerEvent(const SDL_Event &event)
{
    return event.type == SDL_EVENT_FINGER_DOWN
        || event.type == SDL_EVENT_FINGER_MOTION
        || event.type == SDL_EVENT_FINGER_UP
        || event.type == SDL_EVENT_FINGER_CANCELED;
}

SDL_Window *focusedSdlWindow()
{
    SDL_Window *pWindow = SDL_GetKeyboardFocus();

    if (pWindow != nullptr)
    {
        return pWindow;
    }

    pWindow = SDL_GetMouseFocus();

    if (pWindow != nullptr)
    {
        return pWindow;
    }

    int windowCount = 0;
    SDL_Window **ppWindows = SDL_GetWindows(&windowCount);

    if (ppWindows == nullptr || windowCount <= 0)
    {
        return nullptr;
    }

    pWindow = ppWindows[0];
    SDL_free(ppWindows);
    return pWindow;
}

bool submitAndroidFingerEventToImGui(const SDL_Event &event)
{
    if (!isAndroidFingerEvent(event))
    {
        return false;
    }

    SDL_Window *pWindow = focusedSdlWindow();

    if (pWindow == nullptr)
    {
        return false;
    }

    int windowWidth = 0;
    int windowHeight = 0;
    SDL_GetWindowSize(pWindow, &windowWidth, &windowHeight);

    if (windowWidth <= 0 || windowHeight <= 0)
    {
        return false;
    }

    ImGuiIO &io = ImGui::GetIO();
    const float mouseX = std::clamp(event.tfinger.x, 0.0f, 1.0f) * static_cast<float>(windowWidth);
    const float mouseY = std::clamp(event.tfinger.y, 0.0f, 1.0f) * static_cast<float>(windowHeight);
    io.AddMouseSourceEvent(ImGuiMouseSource_TouchScreen);
    io.AddMousePosEvent(mouseX, mouseY);

    if (event.type == SDL_EVENT_FINGER_DOWN)
    {
        io.AddMouseButtonEvent(0, true);
    }
    else if (event.type == SDL_EVENT_FINGER_UP || event.type == SDL_EVENT_FINGER_CANCELED)
    {
        io.AddMouseButtonEvent(0, false);
    }

    return true;
}
#endif

uint64_t soundPreloadKey(SoundRef sound)
{
    return (static_cast<uint64_t>(sound.scope == SoundScope::World ? 1u : 0u) << 32u) | sound.id;
}

void preloadSoundOnce(GameAudioSystem &audioSystem, std::unordered_set<uint64_t> &preloadedSounds, SoundRef sound)
{
    if (sound.id == 0 || !preloadedSounds.insert(soundPreloadKey(sound)).second)
    {
        return;
    }

    audioSystem.preloadSound(sound);
}

void preloadMonsterSpellSound(
    GameAudioSystem &audioSystem,
    std::unordered_set<uint64_t> &preloadedSounds,
    const SpellTable &spellTable,
    const std::string &spellName)
{
    if (spellName.empty())
    {
        return;
    }

    const SpellEntry *pSpellEntry = spellTable.findByName(spellName);

    if (pSpellEntry == nullptr || pSpellEntry->effectSoundId <= 0)
    {
        return;
    }

    preloadSoundOnce(audioSystem, preloadedSounds, engineSound(static_cast<uint32_t>(pSpellEntry->effectSoundId)));
}

void preloadMonsterStatsSounds(
    GameAudioSystem &audioSystem,
    std::unordered_set<uint64_t> &preloadedSounds,
    const SpellTable &spellTable,
    const MonsterTable::MonsterStatsEntry &stats)
{
    preloadSoundOnce(audioSystem, preloadedSounds, worldSound(stats.boredSoundId));
    preloadSoundOnce(audioSystem, preloadedSounds, worldSound(stats.attackSoundId));
    preloadSoundOnce(audioSystem, preloadedSounds, worldSound(stats.winceSoundId));
    preloadSoundOnce(audioSystem, preloadedSounds, worldSound(stats.deathSoundId));

    preloadMonsterSpellSound(audioSystem, preloadedSounds, spellTable, stats.spell1Name);
    preloadMonsterSpellSound(audioSystem, preloadedSounds, spellTable, stats.spell2Name);
}

void preloadMapGameplaySounds(
    GameAudioSystem &audioSystem,
    const MonsterTable &monsterTable,
    const SpellTable &spellTable,
    const MapAssetInfo &map)
{
    audioSystem.beginMapSoundPreload();
    constexpr std::array<int16_t, 3> SummonWispMonsterIds = {97, 98, 99};
    constexpr std::array<SoundId, 12> OutdoorFootstepSoundIds = {
        SoundId::RunCarpet,
        SoundId::RunDirt,
        SoundId::RunGrass,
        SoundId::RunRoad,
        SoundId::RunStone,
        SoundId::RunWood,
        SoundId::WalkCarpet,
        SoundId::WalkDirt,
        SoundId::WalkGrass,
        SoundId::WalkRoad,
        SoundId::WalkStone,
        SoundId::WalkWood,
    };
    const MapDeltaData *pMapDeltaData = nullptr;

    if (map.indoorMapDeltaData)
    {
        pMapDeltaData = &*map.indoorMapDeltaData;
    }
    else if (map.outdoorMapDeltaData)
    {
        pMapDeltaData = &*map.outdoorMapDeltaData;
    }

    std::unordered_set<uint64_t> preloadedSounds;
    std::unordered_set<int16_t> preloadedMonsterIds;

    if (map.outdoorMapData)
    {
        for (SoundId soundId : OutdoorFootstepSoundIds)
        {
            preloadSoundOnce(audioSystem, preloadedSounds, engineSound(static_cast<uint32_t>(soundId)));
        }

        for (const OutdoorTerrainFootstepSoundOverride &overrideEntry :
             map.outdoorMapData->terrainFootstepSoundOverrides)
        {
            preloadSoundOnce(audioSystem, preloadedSounds, engineSound(overrideEntry.walkSoundId));
            preloadSoundOnce(audioSystem, preloadedSounds, engineSound(overrideEntry.runSoundId));
        }
    }
    else if (map.indoorMapData)
    {
        preloadSoundOnce(
            audioSystem,
            preloadedSounds,
            engineSound(static_cast<uint32_t>(SoundId::WalkStoneHall)));
    }

    const auto preloadMonsterId = [&](int16_t monsterId)
    {
        if (monsterId <= 0 || !preloadedMonsterIds.insert(monsterId).second)
        {
            return;
        }

        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(monsterId);

        if (pStats != nullptr)
        {
            preloadMonsterStatsSounds(audioSystem, preloadedSounds, spellTable, *pStats);
        }
    };

    if (pMapDeltaData != nullptr)
    {
        for (const MapDeltaActor &actor : pMapDeltaData->actors)
        {
            const std::array<int16_t, 2> candidateMonsterIds = {
                actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId,
                actor.monsterId
            };

            for (int16_t monsterId : candidateMonsterIds)
            {
                preloadMonsterId(monsterId);
            }
        }

        for (const MapDeltaSpriteObject &spriteObject : pMapDeltaData->spriteObjects)
        {
            preloadSoundOnce(audioSystem, preloadedSounds, worldSound(spriteObject.soundId));
        }
    }

    const ActorPreviewBillboardSet *pActorBillboardSet =
        map.indoorActorPreviewBillboardSet
            ? &*map.indoorActorPreviewBillboardSet
            : (map.outdoorActorPreviewBillboardSet ? &*map.outdoorActorPreviewBillboardSet : nullptr);

    if (pActorBillboardSet != nullptr)
    {
        for (const ActorPreviewBillboard &billboard : pActorBillboardSet->billboards)
        {
            preloadMonsterId(billboard.monsterId);
        }
    }

    for (int16_t summonMonsterId : SummonWispMonsterIds)
    {
        preloadMonsterId(summonMonsterId);
    }

    audioSystem.endMapSoundPreload();
}

size_t findMapDeltaActorFilterIndex(const MapDeltaData &mapDeltaData, size_t uniqueActorIndex)
{
    for (size_t actorIndex = 0; actorIndex < mapDeltaData.actors.size(); ++actorIndex)
    {
        if (mapDeltaData.actors[actorIndex].diagnosticSourceActorIndex == uniqueActorIndex)
        {
            return actorIndex;
        }
    }

    if (uniqueActorIndex < mapDeltaData.actors.size())
    {
        return uniqueActorIndex;
    }

    return static_cast<size_t>(-1);
}

bool filterMapDeltaDataToActorIndex(
    MapDeltaData &mapDeltaData,
    size_t selectedActorIndex,
    size_t uniqueActorIndex,
    const std::string &mapFileName,
    const char *pSceneKind)
{
    if (selectedActorIndex >= mapDeltaData.actors.size())
    {
        std::cerr
            << "GameApplication: --load-unique-actor " << uniqueActorIndex
            << " is out of range for " << pSceneKind << " map " << mapFileName
            << " actor_count=" << mapDeltaData.actors.size() << '\n';
        return false;
    }

    MapDeltaActor selectedActor = mapDeltaData.actors[selectedActorIndex];
    selectedActor.diagnosticSourceActorIndex = uniqueActorIndex;
    mapDeltaData.actors.clear();
    mapDeltaData.actors.push_back(selectedActor);

    std::cout
        << "[ActorLoadFilter] map=\"" << mapFileName << "\" scene=" << pSceneKind
        << " unique_actor=" << uniqueActorIndex
        << " loaded_actor_count=1\n";
    GAMEPLAY_DEBUG_TRACE(
        "actor_load_filter map=\"" + mapFileName + "\""
        + " scene=" + std::string(pSceneKind)
        + " unique_actor=" + std::to_string(uniqueActorIndex)
        + " loaded_actor_count=1");
    return true;
}

size_t findIndoorRuntimeActorFilterIndex(
    const IndoorWorldRuntime::Snapshot &snapshot,
    size_t uniqueActorIndex)
{
    for (size_t actorIndex = 0; actorIndex < snapshot.mapActorAiStates.size(); ++actorIndex)
    {
        if (snapshot.mapActorAiStates[actorIndex].actorId == uniqueActorIndex)
        {
            return actorIndex;
        }
    }

    return static_cast<size_t>(-1);
}

template <typename T>
void filterVectorToActorIndex(std::vector<T> &values, size_t selectedActorIndex)
{
    if (selectedActorIndex >= values.size())
    {
        values.clear();
        return;
    }

    T selectedValue = values[selectedActorIndex];
    values.clear();
    values.push_back(std::move(selectedValue));
}

template <typename T>
void filterCorpseViewsToActorIndex(
    std::vector<std::optional<T>> &corpseViews,
    std::optional<T> &activeCorpseView,
    size_t selectedActorIndex)
{
    std::optional<T> selectedCorpseView;

    if (selectedActorIndex < corpseViews.size())
    {
        selectedCorpseView = corpseViews[selectedActorIndex];

        if (selectedCorpseView)
        {
            selectedCorpseView->sourceIndex = 0;
        }
    }

    corpseViews.clear();
    corpseViews.push_back(selectedCorpseView);

    if (activeCorpseView && activeCorpseView->sourceIndex == selectedActorIndex)
    {
        activeCorpseView->sourceIndex = 0;
    }
    else
    {
        activeCorpseView.reset();
    }
}

size_t findOutdoorRuntimeActorFilterIndex(
    const OutdoorWorldRuntime::Snapshot &snapshot,
    size_t uniqueActorIndex)
{
    for (size_t actorIndex = 0; actorIndex < snapshot.mapActors.size(); ++actorIndex)
    {
        if (snapshot.mapActors[actorIndex].actorId == uniqueActorIndex)
        {
            return actorIndex;
        }
    }

    return static_cast<size_t>(-1);
}

bool filterOutdoorRuntimeToUniqueActor(
    OutdoorWorldRuntime &worldRuntime,
    size_t uniqueActorIndex,
    const std::string &mapFileName)
{
    MapDeltaData *pMapDeltaData = worldRuntime.mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        std::cerr
            << "GameApplication: --load-unique-actor cannot filter outdoor map "
            << mapFileName << " without map delta actors\n";
        return false;
    }

    OutdoorWorldRuntime::Snapshot snapshot = worldRuntime.snapshot();
    size_t selectedRuntimeActorIndex = findOutdoorRuntimeActorFilterIndex(snapshot, uniqueActorIndex);

    if (selectedRuntimeActorIndex == static_cast<size_t>(-1))
    {
        selectedRuntimeActorIndex = findMapDeltaActorFilterIndex(*pMapDeltaData, uniqueActorIndex);
    }

    if (selectedRuntimeActorIndex == static_cast<size_t>(-1))
    {
        std::cerr
            << "GameApplication: --load-unique-actor " << uniqueActorIndex
            << " is out of range for outdoor runtime map " << mapFileName
            << " actor_count=" << snapshot.mapActors.size() << '\n';
        return false;
    }

    if (!filterMapDeltaDataToActorIndex(
            *pMapDeltaData,
            selectedRuntimeActorIndex,
            uniqueActorIndex,
            mapFileName,
            "outdoor"))
    {
        return false;
    }

    filterVectorToActorIndex(snapshot.mapActors, selectedRuntimeActorIndex);
    filterCorpseViewsToActorIndex(
        snapshot.mapActorCorpseViews,
        snapshot.activeCorpseView,
        selectedRuntimeActorIndex);
    worldRuntime.restoreSnapshot(snapshot);
    return true;
}

bool filterIndoorRuntimeToUniqueActor(
    IndoorWorldRuntime &worldRuntime,
    size_t uniqueActorIndex,
    const std::string &mapFileName)
{
    MapDeltaData *pMapDeltaData = worldRuntime.mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        std::cerr
            << "GameApplication: --load-unique-actor cannot filter indoor map "
            << mapFileName << " without map delta actors\n";
        return false;
    }

    IndoorWorldRuntime::Snapshot snapshot = worldRuntime.snapshot();
    size_t selectedRuntimeActorIndex = findIndoorRuntimeActorFilterIndex(snapshot, uniqueActorIndex);

    if (selectedRuntimeActorIndex == static_cast<size_t>(-1))
    {
        selectedRuntimeActorIndex = findMapDeltaActorFilterIndex(*pMapDeltaData, uniqueActorIndex);
    }

    if (selectedRuntimeActorIndex == static_cast<size_t>(-1))
    {
        std::cerr
            << "GameApplication: --load-unique-actor " << uniqueActorIndex
            << " is out of range for indoor runtime map " << mapFileName
            << " actor_count=" << snapshot.mapActorAiStates.size() << '\n';
        return false;
    }

    if (!filterMapDeltaDataToActorIndex(
            *pMapDeltaData,
            selectedRuntimeActorIndex,
            uniqueActorIndex,
            mapFileName,
            "indoor"))
    {
        return false;
    }

    filterVectorToActorIndex(snapshot.mapActorAiStates, selectedRuntimeActorIndex);
    filterVectorToActorIndex(snapshot.mapActorSpellEffectStates, selectedRuntimeActorIndex);
    filterCorpseViewsToActorIndex(
        snapshot.mapActorCorpseViews,
        snapshot.activeCorpseView,
        selectedRuntimeActorIndex);
    worldRuntime.restoreSnapshot(snapshot);
    return true;
}

bool mapLoadTimingEnabled()
{
    const char *pValue = std::getenv("OPENYAMM_MAP_LOAD_TIMING");
    return pValue != nullptr && std::string_view(pValue) != "0" && std::string_view(pValue) != "false";
}

std::string traceEnvironmentValue(const char *pName)
{
    const char *pValue = std::getenv(pName);
    return pValue != nullptr ? std::string(pValue) : std::string();
}

void logMapArrived(
    const std::string &previousMapFileName,
    const std::string &targetMapFileName,
    const EventRuntimeState::PendingMapMove &pendingMapMove,
    bool sameMap,
    float gameMinutes)
{
    GAMEPLAY_DEBUG_TRACE(
        "map_arrived previous_map=\"" + previousMapFileName + "\""
        + " map=\"" + targetMapFileName + "\""
        + " game_minutes=" + std::to_string(gameMinutes)
        + " same_map=" + (sameMap ? "true" : "false")
        + " use_start_position=" + (pendingMapMove.useMapStartPosition ? "true" : "false")
        + (!pendingMapMove.traceSourceKind.empty()
            ? " source_kind=\"" + pendingMapMove.traceSourceKind + "\""
                + " source_id=" + std::to_string(pendingMapMove.traceSourceId)
                + " action_id=" + std::to_string(pendingMapMove.traceActionId)
                + " event_id=" + std::to_string(pendingMapMove.traceEventId)
                + " destination_name=\"" + pendingMapMove.traceDestinationName + "\""
            : "")
        + " pos=(" + std::to_string(pendingMapMove.x)
        + "," + std::to_string(pendingMapMove.y)
        + "," + std::to_string(pendingMapMove.z) + ")"
        + " direction_degrees="
        + (pendingMapMove.directionDegrees.has_value()
            ? std::to_string(*pendingMapMove.directionDegrees)
            : std::string("none")));
}

PendingMapLeaveOutputs consumePendingMapLeaveOutputs(EventRuntimeState &runtimeState)
{
    PendingMapLeaveOutputs outputs = {};
    outputs.pendingMovie = std::move(runtimeState.pendingMovie);
    runtimeState.pendingMovie.reset();
    outputs.pendingWinGame = std::move(runtimeState.pendingWinGame);
    runtimeState.pendingWinGame.reset();
    outputs.pendingReturnToMainMenu = runtimeState.pendingReturnToMainMenu;
    runtimeState.pendingReturnToMainMenu = false;
    outputs.pendingSounds = std::move(runtimeState.pendingSounds);
    runtimeState.pendingSounds.clear();
    return outputs;
}

void appendPendingMapLeaveOutputs(EventRuntimeState &runtimeState, PendingMapLeaveOutputs &&outputs)
{
    if (outputs.pendingMovie.has_value())
    {
        runtimeState.pendingMovie = std::move(outputs.pendingMovie);
    }

    if (outputs.pendingWinGame.has_value())
    {
        runtimeState.pendingWinGame = std::move(outputs.pendingWinGame);
    }

    runtimeState.pendingReturnToMainMenu = runtimeState.pendingReturnToMainMenu || outputs.pendingReturnToMainMenu;
    runtimeState.pendingSounds.insert(
        runtimeState.pendingSounds.end(),
        std::make_move_iterator(outputs.pendingSounds.begin()),
        std::make_move_iterator(outputs.pendingSounds.end()));
}

const char *sceneKindName(SceneKind kind)
{
    switch (kind)
    {
        case SceneKind::Outdoor:
            return "outdoor";
        case SceneKind::Indoor:
            return "indoor";
    }

    return "unknown";
}

std::vector<uint32_t> sortedIds(const std::unordered_set<uint32_t> &ids)
{
    std::vector<uint32_t> sorted(ids.begin(), ids.end());
    std::sort(sorted.begin(), sorted.end());
    return sorted;
}

template<typename Key, typename Value>
std::vector<std::pair<Key, Value>> sortedMap(const std::unordered_map<Key, Value> &values)
{
    std::vector<std::pair<Key, Value>> sorted(values.begin(), values.end());
    std::sort(
        sorted.begin(),
        sorted.end(),
        [](const std::pair<Key, Value> &left, const std::pair<Key, Value> &right)
        {
            return left.first < right.first;
        });
    return sorted;
}

std::vector<std::pair<std::string, int32_t>> sortedStringIntMap(const std::unordered_map<std::string, int32_t> &values)
{
    std::vector<std::pair<std::string, int32_t>> sorted(values.begin(), values.end());
    std::sort(
        sorted.begin(),
        sorted.end(),
        [](const std::pair<std::string, int32_t> &left, const std::pair<std::string, int32_t> &right)
        {
            return left.first < right.first;
        });
    return sorted;
}

const char *traceEquipmentSlotName(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return "OffHand";
        case EquipmentSlot::MainHand:
            return "MainHand";
        case EquipmentSlot::Bow:
            return "Bow";
        case EquipmentSlot::Armor:
            return "Armor";
        case EquipmentSlot::Helm:
            return "Helm";
        case EquipmentSlot::Belt:
            return "Belt";
        case EquipmentSlot::Cloak:
            return "Cloak";
        case EquipmentSlot::Gauntlets:
            return "Gauntlets";
        case EquipmentSlot::Boots:
            return "Boots";
        case EquipmentSlot::Amulet:
            return "Amulet";
        case EquipmentSlot::Ring1:
            return "Ring1";
        case EquipmentSlot::Ring2:
            return "Ring2";
        case EquipmentSlot::Ring3:
            return "Ring3";
        case EquipmentSlot::Ring4:
            return "Ring4";
        case EquipmentSlot::Ring5:
            return "Ring5";
        case EquipmentSlot::Ring6:
            return "Ring6";
    }

    return "Unknown";
}

std::array<EquipmentSlot, 16> traceEquipmentSlots()
{
    return {
        EquipmentSlot::OffHand,
        EquipmentSlot::MainHand,
        EquipmentSlot::Bow,
        EquipmentSlot::Armor,
        EquipmentSlot::Helm,
        EquipmentSlot::Belt,
        EquipmentSlot::Cloak,
        EquipmentSlot::Gauntlets,
        EquipmentSlot::Boots,
        EquipmentSlot::Amulet,
        EquipmentSlot::Ring1,
        EquipmentSlot::Ring2,
        EquipmentSlot::Ring3,
        EquipmentSlot::Ring4,
        EquipmentSlot::Ring5,
        EquipmentSlot::Ring6,
    };
}

uint32_t equipmentItemId(const CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipment.offHand;
        case EquipmentSlot::MainHand:
            return equipment.mainHand;
        case EquipmentSlot::Bow:
            return equipment.bow;
        case EquipmentSlot::Armor:
            return equipment.armor;
        case EquipmentSlot::Helm:
            return equipment.helm;
        case EquipmentSlot::Belt:
            return equipment.belt;
        case EquipmentSlot::Cloak:
            return equipment.cloak;
        case EquipmentSlot::Gauntlets:
            return equipment.gauntlets;
        case EquipmentSlot::Boots:
            return equipment.boots;
        case EquipmentSlot::Amulet:
            return equipment.amulet;
        case EquipmentSlot::Ring1:
            return equipment.ring1;
        case EquipmentSlot::Ring2:
            return equipment.ring2;
        case EquipmentSlot::Ring3:
            return equipment.ring3;
        case EquipmentSlot::Ring4:
            return equipment.ring4;
        case EquipmentSlot::Ring5:
            return equipment.ring5;
        case EquipmentSlot::Ring6:
            return equipment.ring6;
    }

    return 0;
}

std::string traceItemInstanceSummary(const InventoryItem &item, const ItemTable *pItemTable)
{
    return "item_id=" + std::to_string(item.objectDescriptionId)
        + gameplayDebugTraceItemSummary(item.objectDescriptionId, pItemTable)
        + " quantity=" + std::to_string(item.quantity)
        + " identified=" + (item.identified ? "true" : "false")
        + " broken=" + (item.broken ? "true" : "false")
        + " stolen=" + (item.stolen ? "true" : "false")
        + " standard_enchant_id=" + std::to_string(item.standardEnchantId)
        + " special_enchant_id=" + std::to_string(item.specialEnchantId)
        + " artifact_id=" + std::to_string(item.artifactId)
        + " charges=" + std::to_string(item.currentCharges)
        + "/" + std::to_string(item.maxCharges);
}

uint64_t traceFingerprintUpdate(uint64_t hash, uint64_t value)
{
    constexpr uint64_t FnvaPrime = 1099511628211ull;
    hash ^= value;
    hash *= FnvaPrime;
    return hash;
}

std::string traceCompactSkillSnapshot(const std::vector<std::pair<std::string, CharacterSkill>> &skills)
{
    std::ostringstream out;

    for (size_t index = 0; index < skills.size(); ++index)
    {
        if (index > 0)
        {
            out << ',';
        }

        out << skills[index].first << ':'
            << skills[index].second.level << ':'
            << static_cast<uint32_t>(skills[index].second.mastery);
    }

    return out.str();
}

std::string traceCompactMapVarSnapshot(const std::array<uint8_t, 75> &mapVars, size_t &nonZeroCount)
{
    std::ostringstream out;
    bool first = true;
    nonZeroCount = 0;

    for (size_t index = 0; index < mapVars.size(); ++index)
    {
        if (mapVars[index] == 0)
        {
            continue;
        }

        if (!first)
        {
            out << ',';
        }

        out << index << ':' << static_cast<uint32_t>(mapVars[index]);
        first = false;
        ++nonZeroCount;
    }

    return out.str();
}

uint64_t traceMapVarFingerprint(const std::array<uint8_t, 75> &mapVars)
{
    uint64_t hash = 1469598103934665603ull;

    for (size_t index = 0; index < mapVars.size(); ++index)
    {
        hash = traceFingerprintUpdate(hash, index);
        hash = traceFingerprintUpdate(hash, mapVars[index]);
    }

    return hash;
}

void tracePartySnapshot(
    const std::string &eventPrefix,
    const Party::Snapshot &snapshot,
    const ItemTable *pItemTable)
{
    GAMEPLAY_DEBUG_TRACE(
        eventPrefix
        + "_party gold=" + std::to_string(snapshot.gold)
        + " bank_gold=" + std::to_string(snapshot.bankGold)
        + " food=" + std::to_string(snapshot.food)
        + " active_member_index=" + std::to_string(snapshot.activeMemberIndex)
        + " member_count=" + std::to_string(snapshot.members.size())
        + " hireling_count=" + std::to_string(snapshot.hiredNpcFollowers.size()));

    for (size_t memberIndex = 0; memberIndex < snapshot.members.size(); ++memberIndex)
    {
        const Character &member = snapshot.members[memberIndex];
        GAMEPLAY_DEBUG_TRACE(
            eventPrefix
            + "_party_member member_index=" + std::to_string(memberIndex)
            + " name=\"" + member.name + "\""
            + " class=\"" + member.className + "\""
            + " role=\"" + member.role + "\""
            + " race_id=" + std::to_string(member.raceId)
            + " sex_id=" + std::to_string(member.sexId)
            + " portrait_id=" + std::to_string(member.portraitPictureId)
            + " voice_id=" + std::to_string(member.voiceId)
            + " level=" + std::to_string(member.level)
            + " hp=" + std::to_string(member.health)
            + "/" + std::to_string(member.maxHealth)
            + " sp=" + std::to_string(member.spellPoints)
            + "/" + std::to_string(member.maxSpellPoints)
            + " inventory_count=" + std::to_string(member.inventory.size())
            + " award_count=" + std::to_string(member.awards.size()));

        std::vector<std::pair<std::string, CharacterSkill>> skills(member.skills.begin(), member.skills.end());
        std::sort(
            skills.begin(),
            skills.end(),
            [](const std::pair<std::string, CharacterSkill> &left,
                const std::pair<std::string, CharacterSkill> &right)
            {
                return left.first < right.first;
            });

        if (!skills.empty())
        {
            GAMEPLAY_DEBUG_TRACE(
                eventPrefix
                + "_party_skills member_index=" + std::to_string(memberIndex)
                + " count=" + std::to_string(skills.size())
                + " skills=\"" + traceCompactSkillSnapshot(skills) + "\"");
        }

        for (uint32_t awardId : sortedIds(member.awards))
        {
            GAMEPLAY_DEBUG_TRACE(
                eventPrefix
                + "_party_award member_index=" + std::to_string(memberIndex)
                + " award_id=" + std::to_string(awardId));
        }

        for (const InventoryItem &item : member.inventory)
        {
            GAMEPLAY_DEBUG_TRACE(
                eventPrefix
                + "_party_inventory member_index=" + std::to_string(memberIndex)
                + " grid=(" + std::to_string(item.gridX)
                + "," + std::to_string(item.gridY) + ") "
                + traceItemInstanceSummary(item, pItemTable));
        }

        for (EquipmentSlot slot : traceEquipmentSlots())
        {
            const uint32_t itemId = equipmentItemId(member.equipment, slot);
            if (itemId == 0)
            {
                continue;
            }

            GAMEPLAY_DEBUG_TRACE(
                eventPrefix
                + "_party_equipped member_index=" + std::to_string(memberIndex)
                + " slot=" + traceEquipmentSlotName(slot)
                + " item_id=" + std::to_string(itemId)
                + gameplayDebugTraceItemSummary(itemId, pItemTable));
        }
    }

    for (uint32_t qbitId : sortedIds(snapshot.questBits))
    {
        GAMEPLAY_DEBUG_TRACE(eventPrefix + "_qbit id=" + std::to_string(qbitId));
    }

    for (const auto &[variableId, value] : sortedMap(snapshot.eventVariables))
    {
        GAMEPLAY_DEBUG_TRACE(
            eventPrefix
            + "_party_event_var id=" + std::to_string(variableId)
            + " value=" + std::to_string(value));
    }

    std::vector<HiredNpcFollower> hirelings = snapshot.hiredNpcFollowers;
    std::sort(
        hirelings.begin(),
        hirelings.end(),
        [](const HiredNpcFollower &left, const HiredNpcFollower &right)
        {
            return left.npcId < right.npcId;
        });

    for (const HiredNpcFollower &hireling : hirelings)
    {
        GAMEPLAY_DEBUG_TRACE(
            eventPrefix
            + "_hireling npc_id=" + std::to_string(hireling.npcId)
            + " profession_id=" + std::to_string(hireling.professionId)
            + " weekly_cost=" + std::to_string(hireling.weeklyCost));
    }
}

void traceEventRuntimeStateMapVars(
    const std::string &eventPrefix,
    const std::string &fallbackMapName,
    const char *pSceneKind,
    const EventRuntimeState &runtimeState)
{
    const std::string mapName = runtimeState.mapFileName.empty() ? fallbackMapName : runtimeState.mapFileName;

    size_t nonZeroCount = 0;
    const std::string nonZeroValues = traceCompactMapVarSnapshot(runtimeState.mapVars, nonZeroCount);
    GAMEPLAY_DEBUG_TRACE(
        eventPrefix
        + "_map_vars map=\"" + mapName + "\""
        + " scene_kind=" + pSceneKind
        + " count=" + std::to_string(runtimeState.mapVars.size())
        + " nonzero_count=" + std::to_string(nonZeroCount)
        + " fingerprint=" + std::to_string(traceMapVarFingerprint(runtimeState.mapVars))
        + " values=\"" + nonZeroValues + "\"");

    for (const auto &[name, value] : sortedStringIntMap(runtimeState.namedMapVars))
    {
        GAMEPLAY_DEBUG_TRACE(
            eventPrefix
            + "_named_map_var map=\"" + mapName + "\""
            + " scene_kind=" + pSceneKind
            + " name=\"" + name + "\""
            + " value=" + std::to_string(value));
    }
}

void traceSaveDataStateDump(
    const std::string &phase,
    const std::filesystem::path &path,
    const GameSaveData &saveData,
    const ItemTable *pItemTable)
{
    const std::string eventPrefix = "state_dump_" + phase;
    GAMEPLAY_DEBUG_TRACE(
        eventPrefix
        + "_begin path=\"" + path.string() + "\""
        + " map=\"" + saveData.mapFileName + "\""
        + " scene_kind=" + sceneKindName(saveData.currentSceneKind)
        + " game_minutes=" + std::to_string(saveData.savedGameMinutes));

    tracePartySnapshot(eventPrefix, saveData.party, pItemTable);

    for (const auto &[name, value] : sortedStringIntMap(saveData.namedGlobalVars))
    {
        GAMEPLAY_DEBUG_TRACE(
            eventPrefix
            + "_named_global_var name=\"" + name + "\""
            + " value=" + std::to_string(value));
    }

    if (saveData.hasOutdoorRuntimeState && saveData.outdoorWorld.eventRuntimeState)
    {
        traceEventRuntimeStateMapVars(
            eventPrefix,
            saveData.mapFileName,
            "outdoor",
            *saveData.outdoorWorld.eventRuntimeState);
    }

    std::vector<std::pair<std::string, OutdoorWorldRuntime::Snapshot>> outdoorStates(
        saveData.outdoorWorldStates.begin(),
        saveData.outdoorWorldStates.end());
    std::sort(
        outdoorStates.begin(),
        outdoorStates.end(),
        [](const auto &left, const auto &right)
        {
            return left.first < right.first;
        });

    for (const auto &[mapName, worldState] : outdoorStates)
    {
        if (worldState.eventRuntimeState)
        {
            traceEventRuntimeStateMapVars(eventPrefix, mapName, "outdoor", *worldState.eventRuntimeState);
        }
    }

    if (saveData.hasIndoorSceneState && saveData.indoorScene.eventRuntimeState)
    {
        traceEventRuntimeStateMapVars(
            eventPrefix,
            saveData.mapFileName,
            "indoor",
            *saveData.indoorScene.eventRuntimeState);
    }

    std::vector<std::pair<std::string, IndoorSceneRuntime::Snapshot>> indoorStates(
        saveData.indoorSceneStates.begin(),
        saveData.indoorSceneStates.end());
    std::sort(
        indoorStates.begin(),
        indoorStates.end(),
        [](const auto &left, const auto &right)
        {
            return left.first < right.first;
        });

    for (const auto &[mapName, sceneState] : indoorStates)
    {
        if (sceneState.eventRuntimeState)
        {
            traceEventRuntimeStateMapVars(eventPrefix, mapName, "indoor", *sceneState.eventRuntimeState);
        }
    }

    GAMEPLAY_DEBUG_TRACE(eventPrefix + "_end path=\"" + path.string() + "\"");
}

TextureFilterMode textureFilterModeFromSetting(const std::string &value, TextureFilterMode fallback)
{
    const std::string normalized = toLowerCopy(value);

    if (normalized == "nearest" || normalized == "point")
    {
        return TextureFilterMode::Nearest;
    }

    if (normalized == "linear" || normalized == "bilinear")
    {
        return TextureFilterMode::Linear;
    }

    if (normalized == "anisotropic" || normalized == "aniso")
    {
        return TextureFilterMode::Anisotropic;
    }

    return fallback;
}

TextureFilteringConfig textureFilteringConfigFromSettings(const GameSettings &settings)
{
    TextureFilteringConfig config = {};
    config.enabled = settings.textureFiltering;
    config.terrain = textureFilterModeFromSetting(settings.terrainFiltering, TextureFilterMode::Anisotropic);
    config.bmodel = textureFilterModeFromSetting(settings.bmodelFiltering, TextureFilterMode::Anisotropic);
    config.sky = config.terrain;
    config.billboard = textureFilterModeFromSetting(settings.billboardFiltering, TextureFilterMode::Linear);
    config.ui = textureFilterModeFromSetting(settings.uiFiltering, TextureFilterMode::Linear);
    config.text = textureFilterModeFromSetting(settings.textFiltering, TextureFilterMode::Nearest);
    return config;
}

class MapLoadTimingLogger
{
public:
    MapLoadTimingLogger(const std::string &mapFileName, const std::string &scope)
        : m_enabled(mapLoadTimingEnabled())
        , m_mapFileName(mapFileName)
        , m_scope(scope)
        , m_startTickNanoseconds(SDL_GetTicksNS())
        , m_lastTickNanoseconds(m_startTickNanoseconds)
    {
        if (m_enabled)
        {
            std::cerr
                << "[MapLoadTiming] map=" << m_mapFileName
                << " begin=" << m_scope
                << '\n';
        }
    }

    void beginStage(const std::string &stageName) const
    {
        if (!m_enabled)
        {
            return;
        }

        const uint64_t totalNanoseconds = SDL_GetTicksNS() - m_startTickNanoseconds;
        std::cerr
            << "[MapLoadTiming] map=" << m_mapFileName
            << " scope=" << m_scope
            << " stage=\"" << stageName << "\""
            << " event=begin"
            << " total_ms=" << millisecondsFromNanoseconds(totalNanoseconds)
            << '\n';
    }

    void stage(const std::string &stageName)
    {
        if (!m_enabled)
        {
            return;
        }

        const uint64_t nowNanoseconds = SDL_GetTicksNS();
        const uint64_t stageNanoseconds = nowNanoseconds - m_lastTickNanoseconds;
        const uint64_t totalNanoseconds = nowNanoseconds - m_startTickNanoseconds;
        m_lastTickNanoseconds = nowNanoseconds;

        std::cerr
            << "[MapLoadTiming] map=" << m_mapFileName
            << " scope=" << m_scope
            << " stage=\"" << stageName << "\""
            << " delta_ms=" << millisecondsFromNanoseconds(stageNanoseconds)
            << " total_ms=" << millisecondsFromNanoseconds(totalNanoseconds)
            << '\n';
    }

private:
    bool m_enabled = false;
    std::string m_mapFileName;
    std::string m_scope;
    uint64_t m_startTickNanoseconds = 0;
    uint64_t m_lastTickNanoseconds = 0;
};

constexpr float Pi = 3.14159265358979323846f;
constexpr uint32_t DefaultRosterPartyMemberCount = 3;
constexpr const char *DefaultStartupMapFile = "out01.odm";
constexpr int MainMenuMusicTrack = 14;
constexpr int LoadingOverlayBackgroundCount = 5;
constexpr uint32_t DungeonTransitionOverlayFrameMilliseconds = 16;
constexpr uint32_t BronzeRingItemId = 137;
constexpr uint32_t GoldRingItemId = 138;
constexpr uint32_t PotionBottleItemId = 220;
constexpr uint32_t FirstDebugWandItemId = 152;
constexpr uint32_t LastDebugWandItemId = 176;
constexpr const char *DwiRespawnMapFile = "out01.odm";
constexpr const char *RavenshoreRespawnMapFile = "out02.odm";
constexpr const char *PartyDefeatCutsceneDirectory = "Videos/Cutscenes";
constexpr const char *PartyDefeatCutsceneStem = "LoseGame";
constexpr const char *EventMovieCutsceneDirectory = "Videos/Cutscenes";
constexpr const char *WinGameCutsceneStem = "wingame";
constexpr size_t MaxPendingInputLength = 64;
constexpr std::array<uint32_t, 3> Level1ReagentItemIds = {{200, 205, 210}};
constexpr std::array<uint32_t, 18> DebugUnlockedTownPortalQBits = {{
    301, 302, 303, 304, 305, 306,
    310, 311, 312, 313, 314, 315,
    718, 719, 720, 721, 722, 723}};
constexpr int32_t DebugBreachEntryMapId = 205;
constexpr std::array<std::pair<std::string_view, int32_t>, 15> DebugBreachEntryGlobals = {{
    {"MMerge.CrossContinents.GotMainQuest", 1},
    {"MMerge.CrossContinents.FinalQuestStarted", 1},
    {"MMerge.CrossContinents.GotFinalQuest", 1},
    {"MMerge.CrossContinents.GotInstructions", 1},
    {"MMerge.CrossContinents.QuestFinished", 0},
    {"MMerge.CrossContinents.GotEndCard", 0},
    {"MMerge.CrossContinents.EnteredBreach", 0},
    {"MMerge.CrossContinents.EnteredBasement", 0},
    {"MMerge.CrossContinents.BreachSplit", 0},
    {"MMerge.CrossContinents.BrFirstFloor", 0},
    {"MMerge.CrossContinents.BrSecFloor", 0},
    {"MMerge.CrossContinents.BrThirdFloor", 0},
    {"MMerge.CrossContinents.CaughtChaos", 0},
    {"MMerge.CrossContinents.CoughtChaos", 0},
    {"MMerge.CrossContinents.GotFQHints", 0},
}};
constexpr std::array<std::string_view, 8> DebugBreachEntryClearedGlobals = {{
    "MMerge.CrossContinents.GotFQHint1",
    "MMerge.CrossContinents.GotFQHint2",
    "MMerge.CrossContinents.GotFQHint3",
    "MMerge.CrossContinents.GotFQHint4",
    "MMerge.CrossContinents.HintByNPC.772",
    "MMerge.CrossContinents.HintByNPC.773",
    "MMerge.CrossContinents.HintByNPC.774",
    "MMerge.CrossContinents.HintByNPC.775",
}};
constexpr float EnterDungeonSpeechDelaySeconds = 2.0f;
constexpr float GameMinutesPerLocationDay = 24.0f * 60.0f;

bool sameMapFileName(const std::string &left, const std::string &right)
{
    return toLowerCopy(left) == toLowerCopy(right);
}

int32_t currentLocationDay(float gameMinutes)
{
    return static_cast<int32_t>(std::floor(std::max(0.0f, gameMinutes) / GameMinutesPerLocationDay)) + 1;
}

bool timedMapRespawnDue(
    const MapStatsEntry &map,
    const MapDeltaLocationInfo &locationInfo,
    int32_t currentLocationDay)
{
    return map.respawnIntervalDays > 0
        && locationInfo.lastRespawnDay > 0
        && currentLocationDay - locationInfo.lastRespawnDay >= map.respawnIntervalDays;
}

const OutdoorWorldRuntime::Snapshot *findSavedOutdoorWorldState(
    const GameSession &session,
    const MapAssetInfo &mapAssetInfo)
{
    const std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &states = session.outdoorWorldStates();
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot>::const_iterator stateIt = states.end();

    if (!mapAssetInfo.map.canonicalId.empty())
    {
        stateIt = states.find(mapAssetInfo.map.canonicalId);
    }

    if (stateIt == states.end())
    {
        stateIt = states.find(mapAssetInfo.map.fileName);
    }

    return stateIt != states.end() ? &stateIt->second : nullptr;
}

const IndoorSceneRuntime::Snapshot *findSavedIndoorSceneState(
    const GameSession &session,
    const MapAssetInfo &mapAssetInfo)
{
    const std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &states = session.indoorSceneStates();
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot>::const_iterator stateIt = states.end();

    if (!mapAssetInfo.map.canonicalId.empty())
    {
        stateIt = states.find(mapAssetInfo.map.canonicalId);
    }

    if (stateIt == states.end())
    {
        stateIt = states.find(mapAssetInfo.map.fileName);
    }

    return stateIt != states.end() ? &stateIt->second : nullptr;
}

bool savedSelectedMapStateNeedsFreshAssets(
    const GameSession &session,
    const MapAssetInfo &mapAssetInfo,
    int32_t currentLocationDay)
{
    if (mapAssetInfo.outdoorMapData)
    {
        const OutdoorWorldRuntime::Snapshot *pSnapshot = findSavedOutdoorWorldState(session, mapAssetInfo);
        return pSnapshot != nullptr
            && timedMapRespawnDue(mapAssetInfo.map, pSnapshot->locationInfo, currentLocationDay);
    }

    if (mapAssetInfo.indoorMapData)
    {
        const IndoorSceneRuntime::Snapshot *pSnapshot = findSavedIndoorSceneState(session, mapAssetInfo);
        return pSnapshot != nullptr
            && pSnapshot->mapDeltaData
            && timedMapRespawnDue(
                mapAssetInfo.map,
                pSnapshot->mapDeltaData->locationInfo,
                currentLocationDay);
    }

    return false;
}

bool isAutosavePath(const std::filesystem::path &path)
{
    return toLowerCopy(path.stem().string()) == "autosave";
}

int effectiveRespawnAreaIdForMap(const MapStatsEntry &mapEntry, const std::string &mapFileName)
{
    const bool indoorMap = toLowerCopy(mapFileName).ends_with(".blv");

    if (indoorMap && mapEntry.areaId != 0)
    {
        return mapEntry.areaId;
    }

    return mapEntry.isTopLevelArea ? mapEntry.id : mapEntry.areaId;
}

const MergedContinentSettingEntry *mergedContinentSettingForMap(
    const MapStatsEntry &map,
    const MergedContinentSettingTable &continentSettingTable)
{
    if (map.mergedContinentId == 0)
    {
        return nullptr;
    }

    return continentSettingTable.findById(map.mergedContinentId);
}

void applyPartyReputationToWorld(
    const Party &party,
    IGameplayWorldRuntime &worldRuntime,
    const MapStatsEntry &map,
    const MergedContinentSettingTable &continentSettingTable)
{
    const MergedContinentSettingEntry *pContinentSetting =
        mergedContinentSettingForMap(map, continentSettingTable);

    if (!continentUsesMergedReputation(pContinentSetting))
    {
        return;
    }

    worldRuntime.setCurrentLocationReputation(party.continentReputation(map.mergedContinentId));
    applyReputationGuardHostility(worldRuntime, 25);
}

void storeWorldReputationInParty(
    Party &party,
    const IGameplayWorldRuntime &worldRuntime,
    const MapStatsEntry &map,
    const MergedContinentSettingTable &continentSettingTable)
{
    const MergedContinentSettingEntry *pContinentSetting =
        mergedContinentSettingForMap(map, continentSettingTable);

    if (!continentUsesMergedReputation(pContinentSetting))
    {
        return;
    }

    party.setContinentReputation(map.mergedContinentId, worldRuntime.currentLocationReputation());
}

bool mapMatchesDeathDestination(
    const MapStatsEntry &currentMap,
    const std::string &currentMapFileName,
    const MapStatsEntry *pDeathMap)
{
    if (pDeathMap == nullptr)
    {
        return false;
    }

    if (sameMapFileName(currentMapFileName, pDeathMap->fileName))
    {
        return true;
    }

    const int currentAreaId = effectiveRespawnAreaIdForMap(currentMap, currentMapFileName);
    const int deathMapAreaId = effectiveRespawnAreaIdForMap(*pDeathMap, pDeathMap->fileName);
    return currentAreaId != 0 && deathMapAreaId != 0 && currentAreaId == deathMapAreaId;
}

std::string trimCopy(std::string_view value);

std::string normalizedDeathMapName(const std::string &mapFileName)
{
    return toLowerCopy(trimCopy(mapFileName));
}

bool isDungeonMapFileName(const std::string &mapFileName)
{
    return toLowerCopy(mapFileName).ends_with(".blv");
}

std::string trimCopy(std::string_view value)
{
    size_t first = 0;

    while (first < value.size() && std::isspace(static_cast<unsigned char>(value[first])) != 0)
    {
        ++first;
    }

    size_t last = value.size();

    while (last > first && std::isspace(static_cast<unsigned char>(value[last - 1])) != 0)
    {
        --last;
    }

    return std::string(value.substr(first, last - first));
}

std::optional<int32_t> parseInt32Argument(const std::string &value)
{
    if (value.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const long parsed = std::strtol(value.c_str(), &pEnd, 10);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return static_cast<int32_t>(parsed);
}

std::optional<float> parseFloatArgument(const std::string &value)
{
    if (value.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const float parsed = std::strtof(value.c_str(), &pEnd);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return parsed;
}

std::string boolString(bool value)
{
    return value ? "true" : "false";
}

std::optional<std::string> debugResolveClassName(const std::string &argument, const ClassSkillTable &classSkillTable)
{
    const std::optional<int32_t> parsedClassId = parseInt32Argument(argument);

    if (parsedClassId)
    {
        if (*parsedClassId < 0)
        {
            return std::nullopt;
        }

        return classSkillTable.classNameForId(static_cast<uint32_t>(*parsedClassId));
    }

    const std::optional<uint32_t> classId = classSkillTable.classIdForName(argument);

    if (!classId)
    {
        return std::nullopt;
    }

    return classSkillTable.classNameForId(*classId);
}

const CharacterDollEntry *debugCharacterDollForClass(
    const CharacterDollTable &characterDollTable,
    uint32_t classId,
    size_t memberCount)
{
    std::vector<const CharacterDollEntry *> matches;
    std::vector<const CharacterDollEntry *> fallbacks;

    for (const auto &[characterId, entry] : characterDollTable.characters())
    {
        (void)characterId;

        if (!entry.availableAtStart)
        {
            continue;
        }

        if (entry.defaultClassId == classId)
        {
            matches.push_back(&entry);
        }

        fallbacks.push_back(&entry);
    }

    std::vector<const CharacterDollEntry *> &choices = !matches.empty() ? matches : fallbacks;

    if (choices.empty())
    {
        return nullptr;
    }

    std::sort(
        choices.begin(),
        choices.end(),
        [](const CharacterDollEntry *pLeft, const CharacterDollEntry *pRight)
        {
            return pLeft->id < pRight->id;
        });

    return choices[memberCount % choices.size()];
}

Character debugCreatePlayerCharacter(
    const std::string &className,
    uint32_t classId,
    const std::string &name,
    const CharacterDollTable &characterDollTable,
    size_t memberCount)
{
    Character character = {};
    character.name = name.empty() ? "Debug " + displayClassName(className) : name;
    character.className = className;
    character.role = displayClassName(className);
    character.level = 1;
    character.experience = 0;
    character.skillPoints = 0;
    character.might = 10;
    character.intellect = 10;
    character.personality = 10;
    character.endurance = 10;
    character.speed = 10;
    character.accuracy = 10;
    character.luck = 10;

    const CharacterDollEntry *pDollEntry = debugCharacterDollForClass(characterDollTable, classId, memberCount);

    if (pDollEntry != nullptr)
    {
        character.characterDataId = pDollEntry->id;
        character.portraitPictureId = pDollEntry->id - 1;

        if (!pDollEntry->facePicturesPrefix.empty())
        {
            character.portraitTextureName = pDollEntry->facePicturesPrefix + "01";
        }
    }

    return character;
}

constexpr size_t DebugMaxNpcFollowerCount = 4;
constexpr uint32_t DebugMaxNpcFollowerFeePercent = 100;

bool debugHasHiredNpcFollower(const EventRuntimeState &runtimeState, uint32_t npcId)
{
    return std::find_if(
        runtimeState.hiredNpcFollowers.begin(),
        runtimeState.hiredNpcFollowers.end(),
        [npcId](const HiredNpcFollower &follower)
        {
            return follower.npcId == npcId;
        }) != runtimeState.hiredNpcFollowers.end();
}

uint32_t debugHiredNpcFollowerFeePercent(const EventRuntimeState &runtimeState)
{
    uint32_t total = 0;

    for (const HiredNpcFollower &follower : runtimeState.hiredNpcFollowers)
    {
        total += follower.weeklyCost / 100u;
    }

    return total;
}

NpcEntry debugNpcEntryWithRuntimeOverrides(NpcEntry entry, const EventRuntimeState &runtimeState)
{
    const std::unordered_map<uint32_t, std::string>::const_iterator nameIt =
        runtimeState.npcNameOverrides.find(entry.id);
    if (nameIt != runtimeState.npcNameOverrides.end())
    {
        entry.name = nameIt->second;
    }

    const std::unordered_map<uint32_t, uint32_t>::const_iterator pictureIt =
        runtimeState.npcPictureOverrides.find(entry.id);
    if (pictureIt != runtimeState.npcPictureOverrides.end())
    {
        entry.pictureId = pictureIt->second;
    }

    const std::unordered_map<uint32_t, uint32_t>::const_iterator professionIt =
        runtimeState.npcProfessionOverrides.find(entry.id);
    if (professionIt != runtimeState.npcProfessionOverrides.end())
    {
        entry.professionId = professionIt->second;
    }

    return entry;
}

std::vector<NpcEntry> debugNpcEntriesForProfession(
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &runtimeState,
    uint32_t professionId)
{
    std::vector<NpcEntry> entries;
    std::unordered_set<uint32_t> baseNpcIds;

    for (const NpcEntry &baseEntry : npcDialogTable.entries())
    {
        baseNpcIds.insert(baseEntry.id);
        NpcEntry entry = debugNpcEntryWithRuntimeOverrides(baseEntry, runtimeState);

        if (entry.professionId == professionId)
        {
            entries.push_back(std::move(entry));
        }
    }

    for (const auto &[npcId, runtimeProfessionId] : runtimeState.npcProfessionOverrides)
    {
        if (baseNpcIds.contains(npcId) || runtimeProfessionId != professionId)
        {
            continue;
        }

        NpcEntry entry = {};
        entry.id = npcId;
        entry.name = "NPC " + std::to_string(npcId);
        entry.professionId = runtimeProfessionId;
        entries.push_back(debugNpcEntryWithRuntimeOverrides(std::move(entry), runtimeState));
    }

    std::sort(
        entries.begin(),
        entries.end(),
        [](const NpcEntry &left, const NpcEntry &right)
        {
            return left.id < right.id;
        });

    return entries;
}

bool debugNpcCanOfferProfessionHire(const NpcEntry &npc, const MergedNpcProfessionEntry &profession)
{
    return npc.joins || profession.joins;
}

bool debugContinentAllowsNpcFollowers(
    const std::optional<MapAssetInfo> &selectedMap,
    const MergedContinentSettingTable &continentSettingTable)
{
    if (!selectedMap || selectedMap->map.mergedContinentId == 0)
    {
        return true;
    }

    const MergedContinentSettingEntry *pContinentSetting =
        continentSettingTable.findById(selectedMap->map.mergedContinentId);
    return pContinentSetting == nullptr || pContinentSetting->npcFollowers;
}

struct DebugCivilTime
{
    int year = 1168;
    int month = 1;
    int day = 1;
    int dayOfWeek = 1;
    int hour24 = 0;
    int minute = 0;
};

DebugCivilTime debugCivilTimeFromGameMinutes(float gameMinutes)
{
    constexpr int MinutesPerDay = 24 * 60;
    constexpr int DaysPerMonth = 28;
    constexpr int MonthsPerYear = 12;

    const int totalMinutes = std::max(0, static_cast<int>(std::floor(gameMinutes)));
    const int totalDays = totalMinutes / MinutesPerDay;
    DebugCivilTime time = {};
    time.year = 1168 + totalDays / (DaysPerMonth * MonthsPerYear);
    time.month = 1 + (totalDays / DaysPerMonth) % MonthsPerYear;
    time.day = 1 + totalDays % DaysPerMonth;
    time.dayOfWeek = 1 + totalDays % 7;
    time.hour24 = (totalMinutes / 60) % 24;
    time.minute = totalMinutes % 60;
    return time;
}

std::string debugWeekdayName(int dayOfWeek)
{
    static constexpr std::array<const char *, 7> Names = {
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    };

    return Names[std::clamp(dayOfWeek, 1, 7) - 1];
}

std::string debugMonthName(int month)
{
    static constexpr std::array<const char *, 12> Names = {
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    };

    return Names[std::clamp(month, 1, 12) - 1];
}

std::string formatDebugGameDate(float gameMinutes)
{
    const DebugCivilTime time = debugCivilTimeFromGameMinutes(gameMinutes);
    const int hour12 = time.hour24 % 12 == 0 ? 12 : time.hour24 % 12;
    const char *pMeridiem = time.hour24 >= 12 ? "PM" : "AM";

    std::ostringstream out;
    out << debugWeekdayName(time.dayOfWeek)
        << ", " << time.day << " " << debugMonthName(time.month) << " " << time.year
        << " " << hour12 << ":";

    if (time.minute < 10)
    {
        out << '0';
    }

    out << time.minute << " " << pMeridiem
        << " (game_minutes=" << static_cast<int>(std::floor(std::max(0.0f, gameMinutes))) << ")";
    return out.str();
}

std::string debugEngineEnglishDataTablePath(std::string_view fileName)
{
    return "engine/data_tables/english/" + std::string(fileName);
}

std::vector<std::vector<std::string>> rowsFromTextTable(const Engine::TextTable &table)
{
    std::vector<std::vector<std::string>> rows;
    rows.reserve(table.getRowCount());

    for (size_t rowIndex = 0; rowIndex < table.getRowCount(); ++rowIndex)
    {
        rows.push_back(table.getRow(rowIndex));
    }

    return rows;
}

std::string lowerSearchText(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        if (std::isalnum(static_cast<unsigned char>(character)) != 0)
        {
            result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
        }
        else if (!result.empty() && result.back() != ' ')
        {
            result.push_back(' ');
        }
    }

    while (!result.empty() && result.back() == ' ')
    {
        result.pop_back();
    }

    return result;
}

std::string compactSearchText(const std::string &value)
{
    std::string result;

    for (char character : lowerSearchText(value))
    {
        if (character != ' ')
        {
            result.push_back(character);
        }
    }

    return result;
}

const JournalQuestEntry *findJournalQuestEntry(
    const std::vector<JournalQuestEntry> &entries,
    uint32_t qbitId)
{
    const std::vector<JournalQuestEntry>::const_iterator iterator = std::lower_bound(
        entries.begin(),
        entries.end(),
        qbitId,
        [](const JournalQuestEntry &entry, uint32_t value)
        {
            return entry.qbitId < value;
        });

    return iterator != entries.end() && iterator->qbitId == qbitId ? &*iterator : nullptr;
}

std::string journalQuestEntryDetails(const JournalQuestEntry *pEntry)
{
    if (pEntry == nullptr)
    {
        return "<undocumented>";
    }

    std::vector<std::string> parts;

    if (!pEntry->text.empty())
    {
        parts.push_back(pEntry->text);
    }

    if (!pEntry->notes.empty())
    {
        parts.push_back("notes: " + pEntry->notes);
    }

    if (!pEntry->owner.empty())
    {
        parts.push_back("owner: " + pEntry->owner);
    }

    if (parts.empty())
    {
        return "<no description>";
    }

    std::ostringstream out;

    for (size_t partIndex = 0; partIndex < parts.size(); ++partIndex)
    {
        if (partIndex > 0)
        {
            out << " | ";
        }

        out << parts[partIndex];
    }

    return out.str();
}

std::string journalQuestEntrySearchText(uint32_t qbitId, const JournalQuestEntry *pEntry)
{
    if (pEntry == nullptr)
    {
        return std::to_string(qbitId);
    }

    return lowerSearchText(
        std::to_string(qbitId)
        + " "
        + pEntry->text
        + " "
        + pEntry->notes
        + " "
        + pEntry->owner);
}

std::vector<std::string> searchTokens(const std::string &query)
{
    std::vector<std::string> tokens;
    std::istringstream stream(lowerSearchText(query));
    std::string token;

    while (stream >> token)
    {
        tokens.push_back(token);
    }

    return tokens;
}

std::string upperSearchText(std::string value)
{
    for (char &character : value)
    {
        character = static_cast<char>(std::toupper(static_cast<unsigned char>(character)));
    }

    return value;
}

int itemSearchScore(const ItemDefinition &item, const std::string &query)
{
    const std::string normalizedQuery = lowerSearchText(query);
    const std::string compactQuery = compactSearchText(query);

    if (normalizedQuery.empty())
    {
        return 0;
    }

    const std::string idText = std::to_string(item.itemId);

    if (idText == normalizedQuery)
    {
        return 20000;
    }

    const std::string haystack =
        item.name + " " + item.unidentifiedName + " " + item.iconName + " " + item.skillGroup + " " + item.notes;
    const std::string normalizedHaystack = lowerSearchText(haystack);
    const std::string compactHaystack = compactSearchText(haystack);
    int score = 0;

    if (lowerSearchText(item.name) == normalizedQuery)
    {
        score = std::max(score, 12000);
    }

    if (!compactQuery.empty() && compactSearchText(item.name).find(compactQuery) != std::string::npos)
    {
        score = std::max(score, 9000 - static_cast<int>(item.name.size()));
    }

    if (!compactQuery.empty() && compactHaystack.find(compactQuery) != std::string::npos)
    {
        score = std::max(score, 7000 - static_cast<int>(compactHaystack.find(compactQuery)));
    }

    const std::vector<std::string> tokens = searchTokens(query);
    int tokenScore = 0;

    for (const std::string &token : tokens)
    {
        if (normalizedHaystack.find(token) == std::string::npos)
        {
            tokenScore = 0;
            break;
        }

        tokenScore += 500;
    }

    return std::max(score, tokenScore);
}

std::vector<const ItemDefinition *> findItemMatches(const ItemTable &itemTable, const std::string &query, size_t limit)
{
    struct ScoredItem
    {
        const ItemDefinition *pItem = nullptr;
        int score = 0;
    };

    std::vector<ScoredItem> scoredItems;

    for (const ItemDefinition &item : itemTable.entries())
    {
        const int score = itemSearchScore(item, query);

        if (score > 0)
        {
            scoredItems.push_back({.pItem = &item, .score = score});
        }
    }

    std::sort(
        scoredItems.begin(),
        scoredItems.end(),
        [](const ScoredItem &left, const ScoredItem &right)
        {
            if (left.score != right.score)
            {
                return left.score > right.score;
            }

            return left.pItem->itemId < right.pItem->itemId;
        });

    std::vector<const ItemDefinition *> result;
    result.reserve(std::min(limit, scoredItems.size()));

    for (const ScoredItem &scoredItem : scoredItems)
    {
        if (result.size() >= limit)
        {
            break;
        }

        result.push_back(scoredItem.pItem);
    }

    return result;
}

struct DebugAwardEntry
{
    uint32_t id = 0;
    std::string text;
    std::string notes;
};

std::vector<DebugAwardEntry> loadDebugAwardEntries(const Engine::AssetFileSystem *pAssetFileSystem)
{
    std::vector<DebugAwardEntry> entries;

    if (pAssetFileSystem == nullptr)
    {
        return entries;
    }

    const std::optional<std::string> contents =
        pAssetFileSystem->readTextFile(debugEngineEnglishDataTablePath("awards.txt"));

    if (!contents)
    {
        return entries;
    }

    const std::optional<Engine::TextTable> table = Engine::TextTable::parseTabSeparated(*contents);

    if (!table)
    {
        return entries;
    }

    for (const std::vector<std::string> &row : rowsFromTextTable(*table))
    {
        if (row.size() < 2 || row[0] == "A Bit")
        {
            continue;
        }

        const std::optional<int32_t> id = parseInt32Argument(row[0]);

        if (!id || *id <= 0)
        {
            continue;
        }

        DebugAwardEntry entry = {};
        entry.id = static_cast<uint32_t>(*id);
        entry.text = row[1];
        entry.notes = row.size() > 3 ? row[3] : std::string();
        entries.push_back(std::move(entry));
    }

    return entries;
}

std::string normalizePromptAnswer(const std::string &value)
{
    return toLowerCopy(trimCopy(value));
}

std::string traceInputPromptQuoted(const std::string &value)
{
    std::string quoted = "\"";

    for (char character : value)
    {
        if (character == '\\' || character == '"')
        {
            quoted.push_back('\\');
        }

        quoted.push_back(character);
    }

    quoted.push_back('"');
    return quoted;
}

std::string traceInputPromptFields(
    const EventRuntimeState::PendingInputPrompt &prompt,
    const std::string &mapName,
    float gameMinutes)
{
    return " map=" + traceInputPromptQuoted(mapName)
        + " game_minutes=" + std::to_string(gameMinutes)
        + " event_id=" + std::to_string(prompt.eventId)
        + " continue_step=" + std::to_string(prompt.continueStep)
        + " correct_step=" + std::to_string(prompt.correctStep)
        + " text_id=" + std::to_string(prompt.textId)
        + " prompt=" + traceInputPromptQuoted(prompt.text.value_or(std::string()))
        + " answer_count=" + std::to_string(prompt.answers.size());
}

std::string trimEventMovieName(const std::string &movieName)
{
    size_t first = 0;
    while (first < movieName.size() && std::isspace(static_cast<unsigned char>(movieName[first])) != 0)
    {
        ++first;
    }

    size_t last = movieName.size();
    while (last > first && std::isspace(static_cast<unsigned char>(movieName[last - 1])) != 0)
    {
        --last;
    }

    std::string trimmed = movieName.substr(first, last - first);
    while (trimmed.size() >= 2 && trimmed.front() == '"' && trimmed.back() == '"')
    {
        trimmed = trimmed.substr(1, trimmed.size() - 2);
    }

    return trimmed;
}

std::string eventMovieStemFromName(const std::string &movieName)
{
    std::string stem = trimEventMovieName(movieName);
    std::replace(stem.begin(), stem.end(), '\\', '/');

    const size_t slashPosition = stem.find_last_of('/');
    if (slashPosition != std::string::npos)
    {
        stem = stem.substr(slashPosition + 1);
    }

    if (toLowerCopy(stem).ends_with(".ogv"))
    {
        stem.resize(stem.size() - 4);
    }

    return trimEventMovieName(stem);
}

std::string pluralizedUnit(uint64_t value, const char *pSingular, const char *pPlural)
{
    return value == 1 ? pSingular : pPlural;
}

std::string formatWinGameDuration(float currentGameMinutes)
{
    constexpr float GameStartMinutes = 9.0f * 60.0f;
    constexpr uint64_t MinutesPerDay = 24u * 60u;
    constexpr uint64_t DaysPerMonth = 28u;
    constexpr uint64_t MonthsPerYear = 12u;

    const float elapsedGameMinutes = std::max(0.0f, currentGameMinutes - GameStartMinutes);
    uint64_t totalDays = static_cast<uint64_t>(std::floor(elapsedGameMinutes / static_cast<float>(MinutesPerDay)));
    const uint64_t years = totalDays / (DaysPerMonth * MonthsPerYear);
    totalDays %= DaysPerMonth * MonthsPerYear;
    const uint64_t months = totalDays / DaysPerMonth;
    const uint64_t days = totalDays % DaysPerMonth;

    return "Total Time: " + std::to_string(years) + " " + pluralizedUnit(years, "Year", "Years")
        + ", " + std::to_string(months) + " " + pluralizedUnit(months, "Month", "Months")
        + ", " + std::to_string(days) + " " + pluralizedUnit(days, "Day", "Days");
}

uint64_t calculateWinGameScore(const Party &party, float currentGameMinutes)
{
    constexpr float GameStartMinutes = 9.0f * 60.0f;
    constexpr uint64_t MinutesPerDay = 24u * 60u;

    const float elapsedGameMinutes = std::max(0.0f, currentGameMinutes - GameStartMinutes);
    const uint64_t totalDays = std::max<uint64_t>(
        1u,
        static_cast<uint64_t>(std::floor(elapsedGameMinutes / static_cast<float>(MinutesPerDay))));
    uint64_t totalExperience = 0;

    for (const Character &member : party.members())
    {
        totalExperience += member.experience;
    }

    return totalExperience / totalDays;
}

std::string winGameCharacterLine(const Party &party)
{
    const std::vector<Character> &members = party.members();

    if (members.empty())
    {
        return "Adventurer the Level 1 Adventurer";
    }

    const Character &leader = members.front();
    const std::string className = !leader.className.empty() ? leader.className : leader.role;
    const std::string displayClass = !className.empty() ? displayClassName(className) : "Adventurer";
    const uint32_t level = std::max<uint32_t>(1u, leader.level);

    return leader.name + " the Level " + std::to_string(level) + " " + displayClass;
}

std::string resolveEventMovieStem(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &movieName)
{
    const std::string requestedStem = eventMovieStemFromName(movieName);

    if (requestedStem.empty())
    {
        return {};
    }

    const std::string requestedFileName = toLowerCopy(requestedStem + ".ogv");
    const std::vector<std::string> entries = assetFileSystem.enumerate(EventMovieCutsceneDirectory);

    for (const std::string &entry : entries)
    {
        if (toLowerCopy(entry) == requestedFileName)
        {
            return std::filesystem::path(entry).stem().string();
        }
    }

    return requestedStem;
}

std::optional<size_t> chooseRandomActablePartyMember(const Party &party)
{
    std::vector<size_t> actableMemberIndices;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const Character *pMember = party.member(memberIndex);

        if (pMember != nullptr && GameMechanics::canAct(*pMember))
        {
            actableMemberIndices.push_back(memberIndex);
        }
    }

    if (actableMemberIndices.empty())
    {
        return std::nullopt;
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<size_t> distribution(0, actableMemberIndices.size() - 1);
    return actableMemberIndices[distribution(rng)];
}

int remapLoadingProgress(int localProgress, int startProgress, int endProgress)
{
    const int clampedLocal = std::clamp(localProgress, 0, 100);
    return startProgress + (endProgress - startProgress) * clampedLocal / 100;
}

float mapMoveHeadingDegreesToYawRadians(int32_t directionDegrees)
{
    return static_cast<float>(directionDegrees) * Pi / 180.0f;
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
    constexpr uint32_t FirstSpellbookItemId = 400;

    if (spellId == 0 || spellId > spellIdValue(SpellId::SoulDrinker))
    {
        return std::nullopt;
    }

    const uint32_t itemId = FirstSpellbookItemId + (spellId - spellIdValue(SpellId::TorchLight));
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

bool partyMemberHasInventoryItem(const Character &character, uint32_t itemId)
{
    return std::any_of(
        character.inventory.begin(),
        character.inventory.end(),
        [itemId](const InventoryItem &item)
        {
            return item.objectDescriptionId == itemId;
        });
}

void seedDebugWandsIntoParty(Party &party, const ItemTable &itemTable)
{
    Character *pPrimaryMember = party.member(1);
    Character *pOverflowMember = party.member(2);

    if (pPrimaryMember == nullptr)
    {
        return;
    }

    for (uint32_t itemId = FirstDebugWandItemId; itemId <= LastDebugWandItemId; ++itemId)
    {
        if (partyMemberHasInventoryItem(*pPrimaryMember, itemId)
            || (pOverflowMember != nullptr && partyMemberHasInventoryItem(*pOverflowMember, itemId)))
        {
            continue;
        }

        InventoryItem item = ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::Generic);
        item.identified = true;

        if (pPrimaryMember->addInventoryItem(item))
        {
            continue;
        }

        if (pOverflowMember != nullptr)
        {
            pOverflowMember->addInventoryItem(item);
        }
    }
}

float normalizedVolumeLevel(int level)
{
    return std::clamp(static_cast<float>(level) / 9.0f, 0.0f, 1.0f);
}

Engine::WindowMode engineWindowModeForSettings(WindowMode mode)
{
    switch (mode)
    {
    case WindowMode::Windowed:
        return Engine::WindowMode::Windowed;

    case WindowMode::WindowedFullscreen:
        return Engine::WindowMode::WindowedFullscreen;

    case WindowMode::Fullscreen:
        return Engine::WindowMode::Fullscreen;
    }

    return Engine::WindowMode::Windowed;
}

float mouseRotateSpeedForTurnRate(TurnRateMode turnRate)
{
    switch (turnRate)
    {
    case TurnRateMode::X16:
        return 0.0024f;

    case TurnRateMode::X32:
        return 0.0034f;

    case TurnRateMode::Smooth:
        return 0.0045f;
    }

    return 0.0034f;
}

Character buildFreshCreatedCharacter(
    const Character &sourceCharacter,
    const ClassMultiplierTable &classMultiplierTable,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    bool preserveDebugLoadout)
{
    Character character = sourceCharacter;
    character.rosterId = 0;
    character.birthYear = character.birthYear != 0 ? character.birthYear : 1150;

    if (!preserveDebugLoadout)
    {
        character.experience = 0;
        character.level = 1;
        character.skillPoints = 0;
        character.knownSpellIds.clear();
        character.equipment = {};
        character.equipmentRuntime = {};
    }

    character.quickSpellName.clear();
    character.attackSpellName.clear();
    character.baseResistances = {};
    character.permanentBonuses = {};
    character.magicalBonuses = {};
    character.permanentImmunities = {};
    character.magicalImmunities = {};
    character.permanentConditionImmunities = {};
    character.magicalConditionImmunities = {};
    character.conditions = {};
    character.awards.clear();
    character.eventVariables.clear();
    character.recoverySecondsRemaining = 0.0f;
    character.armorClassModifier = 0;
    character.levelModifier = 0;
    character.ageModifier = 0;
    character.playerBits.clear();
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

    character.maxHealth = GameMechanics::calculateBaseCharacterMaxHealth(character, &classMultiplierTable);
    character.health = character.maxHealth;
    character.maxSpellPoints = GameMechanics::calculateBaseCharacterMaxSpellPoints(character, &classMultiplierTable);
    character.spellPoints = character.maxSpellPoints;

    if (!preserveDebugLoadout)
    {
        grantCreatedCharacterStarterItems(character, itemTable, standardItemEnchantTable, specialItemEnchantTable);
    }

    return character;
}

void setDebugTownPortalUnlocks(Party &party, bool unlocked)
{
    for (uint32_t qbitId : DebugUnlockedTownPortalQBits)
    {
        party.setQuestBit(qbitId, unlocked);
    }
}
}

GameApplication::GameApplication(const Engine::ApplicationConfig &config)
    : m_config(config)
    , m_engineApplication(
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
        std::bind(&GameApplication::shutdownApplication, this),
        std::bind(&GameApplication::applicationTextInputActive, this)
    )
    , m_gameSession()
    , m_indoorGameView(m_gameSession)
    , m_outdoorGameView(m_gameSession)
    , m_pAssetFileSystem(nullptr)
    , m_lastFrameWidth(config.windowWidth)
    , m_lastFrameHeight(config.windowHeight)
{
    m_gameSession.setSaveGameToPathCallback(
        [this](
            const std::filesystem::path &path,
            const std::string &saveName,
            const std::vector<uint8_t> &previewBmp,
            std::string &error) -> bool
        {
            static_cast<void>(error);
            return quickSaveToPath(path, saveName, previewBmp);
        });
    m_gameSession.setSettingsChangedCallback(
        [this](const GameSettings &settings)
        {
            m_settings = settings;
            std::string error;

            if (!saveGameSettings(settingsFilePath(), m_settings, error))
            {
                std::cerr << "GameApplication: failed to write settings.ini: " << error << '\n';
            }

            applyCurrentSettingsToActiveRuntime();
        });
}

int GameApplication::run()
{
    return m_engineApplication.run();
}

void GameApplication::configureDebugConsoleStyle()
{
    ImGuiStyle &style = ImGui::GetStyle();
    style.WindowRounding = 4.0f;
    style.FrameRounding = 3.0f;
    style.PopupRounding = 4.0f;
    style.ScrollbarRounding = 4.0f;
    style.WindowBorderSize = 1.0f;
    style.FrameBorderSize = 1.0f;
    style.WindowPadding = ImVec2(8.0f, 8.0f);
    style.FramePadding = ImVec2(7.0f, 4.0f);
    style.ItemSpacing = ImVec2(8.0f, 6.0f);

    ImVec4 *pColors = style.Colors;
    pColors[ImGuiCol_Text] = ImVec4(0.91f, 0.92f, 0.93f, 1.0f);
    pColors[ImGuiCol_WindowBg] = ImVec4(0.08f, 0.09f, 0.10f, 0.94f);
    pColors[ImGuiCol_ChildBg] = ImVec4(0.11f, 0.12f, 0.14f, 0.96f);
    pColors[ImGuiCol_PopupBg] = ImVec4(0.10f, 0.11f, 0.13f, 0.98f);
    pColors[ImGuiCol_Border] = ImVec4(0.20f, 0.23f, 0.27f, 1.0f);
    pColors[ImGuiCol_FrameBg] = ImVec4(0.15f, 0.17f, 0.19f, 1.0f);
    pColors[ImGuiCol_FrameBgHovered] = ImVec4(0.18f, 0.20f, 0.23f, 1.0f);
    pColors[ImGuiCol_FrameBgActive] = ImVec4(0.22f, 0.25f, 0.29f, 1.0f);
    pColors[ImGuiCol_Button] = ImVec4(0.14f, 0.16f, 0.18f, 1.0f);
    pColors[ImGuiCol_ButtonHovered] = ImVec4(0.18f, 0.20f, 0.23f, 1.0f);
    pColors[ImGuiCol_ButtonActive] = ImVec4(0.22f, 0.25f, 0.29f, 1.0f);
    pColors[ImGuiCol_Header] = ImVec4(0.16f, 0.18f, 0.20f, 1.0f);
    pColors[ImGuiCol_HeaderHovered] = ImVec4(0.20f, 0.23f, 0.26f, 1.0f);
    pColors[ImGuiCol_HeaderActive] = ImVec4(0.34f, 0.25f, 0.14f, 1.0f);
    pColors[ImGuiCol_CheckMark] = ImVec4(0.82f, 0.67f, 0.34f, 1.0f);
}

void GameApplication::registerDebugConsoleCommands()
{
    if (m_debugConsoleCommandsRegistered)
    {
        return;
    }

    const auto commandResult = [](bool success, const std::string &message)
    {
        return DebugConsole::CommandResult{.success = success, .message = message};
    };

    const auto activeParty = [this]() -> Party *
    {
        if (m_pMapSceneRuntime != nullptr)
        {
            return &m_pMapSceneRuntime->party();
        }

        return m_gameSession.partyState() ? &*m_gameSession.partyState() : nullptr;
    };

    const auto activeEventRuntimeState = [this]() -> EventRuntimeState *
    {
        return m_pMapSceneRuntime != nullptr ? m_pMapSceneRuntime->eventRuntimeState() : nullptr;
    };

    const auto activeGameplayWorld = [this]() -> IGameplayWorldRuntime *
    {
        if (m_pMapSceneRuntime == nullptr)
        {
            return nullptr;
        }

        if (m_pMapSceneRuntime->kind() == SceneKind::Outdoor)
        {
            return m_pOutdoorWorldRuntime.get();
        }

        IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
        return &pIndoorRuntime->worldRuntime();
    };

    m_debugConsole.registerCommand({
        .name = "help",
        .description = "Show available commands.",
        .usage = "help",
        .callback = [this, commandResult](const DebugConsole::CommandContext &)
        {
            std::ostringstream out;
            out << "Commands: help, cls, map, loc, setup breach, event <id>, "
                << "actor count <monster-id> [monster-id...], "
                << "time [advance [days]], "
                << "qbit get|set|clear <id> [id...], qbit dump [active|all|filter], "
                << "npc greeting get|reset|set <npc-id> [greeting-id], "
                << "global get|set|clear <name> [value], global dump [filter], "
                << "mapvar get|set|clear <index> [value], mapvar dump, "
                << "award get|set|clear <id>, award dump [active|all|filter], "
                << "arcomage win <house-id|mm8>, "
                << "player add <class-id|class-name> [name], hire <profession-id>, gold get|add|set <amount>, "
                << "food get|add|set <amount>, hp full, item search <text>, item give <id|text> [qty], "
                << "tp <x> <y> <z>, config get|set|toggle immortal|unlimited_mana|invisible, "
                << "memory, reload map";
            return commandResult(true, out.str());
        }});

    m_debugConsole.registerCommand({
        .name = "actor",
        .description = "Count remaining actors for one or more monster-table ids on the current map.",
        .usage = "actor count <monster-id> [monster-id...]",
        .callback = [this, activeGameplayWorld, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.size() < 2 || toLowerCopy(context.args[0]) != "count")
            {
                return commandResult(false, "Usage: actor count <monster-id> [monster-id...]");
            }

            IGameplayWorldRuntime *pWorldRuntime = activeGameplayWorld();

            if (pWorldRuntime == nullptr)
            {
                return commandResult(false, "No active map runtime.");
            }

            const MonsterTable &monsterTable = m_gameDataLoader.getMonsterTable();
            std::vector<int16_t> monsterIds;
            std::unordered_set<int16_t> seenMonsterIds;

            for (size_t argumentIndex = 1; argumentIndex < context.args.size(); ++argumentIndex)
            {
                const std::optional<int32_t> parsedId = parseInt32Argument(context.args[argumentIndex]);

                if (!parsedId || *parsedId <= 0 || *parsedId > std::numeric_limits<int16_t>::max())
                {
                    return commandResult(false, "Invalid monster id: " + context.args[argumentIndex]);
                }

                const int16_t monsterId = static_cast<int16_t>(*parsedId);

                if (monsterTable.findStatsById(monsterId) == nullptr)
                {
                    return commandResult(false, "Unknown monster id: " + std::to_string(monsterId));
                }

                if (seenMonsterIds.insert(monsterId).second)
                {
                    monsterIds.push_back(monsterId);
                }
            }

            struct ActorCounts
            {
                size_t total = 0;
                size_t remaining = 0;
            };

            std::unordered_map<int16_t, ActorCounts> countsByMonsterId;

            for (size_t actorIndex = 0; actorIndex < pWorldRuntime->mapActorCount(); ++actorIndex)
            {
                GameplayRuntimeActorState runtimeState = {};

                if (!pWorldRuntime->actorRuntimeState(actorIndex, runtimeState)
                    || !seenMonsterIds.contains(runtimeState.monsterId))
                {
                    continue;
                }

                GameplayActorInspectState inspectState = {};
                const bool hasInspectState = pWorldRuntime->actorInspectState(actorIndex, 0, inspectState);
                const bool defeated = runtimeState.isDead
                    || runtimeState.isInvisible
                    || (hasInspectState && inspectState.currentHp <= 0);
                ActorCounts &counts = countsByMonsterId[runtimeState.monsterId];
                ++counts.total;

                if (!defeated)
                {
                    ++counts.remaining;
                }
            }

            std::ostringstream out;
            size_t combinedRemaining = 0;

            for (size_t idIndex = 0; idIndex < monsterIds.size(); ++idIndex)
            {
                const int16_t monsterId = monsterIds[idIndex];
                const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(monsterId);
                const ActorCounts &counts = countsByMonsterId[monsterId];
                combinedRemaining += counts.remaining;

                if (idIndex > 0)
                {
                    out << '\n';
                }

                out << monsterId << ' ' << pStats->name
                    << ": remaining=" << counts.remaining
                    << " defeated=" << (counts.total - counts.remaining)
                    << " total=" << counts.total;
            }

            if (monsterIds.size() > 1)
            {
                out << "\nCombined remaining=" << combinedRemaining;
            }

            return commandResult(true, out.str());
        }});

    m_debugConsole.registerCommand({
        .name = "memory",
        .description = "Show retained decoded map and audio cache bytes.",
        .usage = "memory",
        .callback = [this, commandResult](const DebugConsole::CommandContext &)
        {
            const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();
            const size_t mapPixelBytes = selectedMap ? mapRenderSourcePixelBytes(*selectedMap) : 0;
            const Engine::AudioSystem::CacheStats audioStats = m_gameAudioSystem.cacheStats();
            std::ostringstream out;
            out << "map_render_source_bytes=" << mapPixelBytes
                << " map_last_released_bytes=" << m_gameDataLoader.lastReleasedMapRenderSourcePixelBytes()
                << " map_sources_released="
                << (m_gameDataLoader.selectedMapRenderSourcePixelsReleased() ? "true" : "false")
                << " audio_clip_count=" << audioStats.clipCount
                << " audio_sample_bytes=" << audioStats.sampleBytes;
            return commandResult(true, out.str());
        }});

    m_debugConsole.registerCommand({
        .name = "time",
        .description = "Show or advance the current game date.",
        .usage = "time [advance [days]]",
        .callback = [this, commandResult](const DebugConsole::CommandContext &context)
        {
            constexpr float MinutesPerDay = 24.0f * 60.0f;

            if (context.args.empty() || toLowerCopy(context.args[0]) == "get")
            {
                return commandResult(true, "Current date: " + formatDebugGameDate(m_gameSession.gameMinutes()));
            }

            const std::string action = toLowerCopy(context.args[0]);

            if (action != "advance" && action != "add" && action != "day")
            {
                return commandResult(false, "Usage: time [advance [days]]");
            }

            std::optional<int32_t> days = 1;

            if (action != "day" && context.args.size() >= 2)
            {
                days = parseInt32Argument(context.args[1]);
            }

            if (!days || *days <= 0)
            {
                return commandResult(false, "Invalid day count.");
            }

            const float minutes = static_cast<float>(*days) * MinutesPerDay;

            if (m_pMapSceneRuntime != nullptr)
            {
                if (!m_gameplayController.advanceGameMinutes(minutes))
                {
                    return commandResult(false, "Time advance unavailable.");
                }

                synchronizeSessionFromRuntime();
            }
            else
            {
                m_gameSession.setGameMinutes(m_gameSession.gameMinutes() + minutes);

                std::optional<Party> &partyState = m_gameSession.partyState();

                if (partyState)
                {
                    partyState->advanceTimedStates(minutes * 60.0f);
                }
            }

            return commandResult(true, "Current date: " + formatDebugGameDate(m_gameSession.gameMinutes()));
        }});

    m_debugConsole.registerCommand({
        .name = "cls",
        .description = "Clear console output.",
        .usage = "cls",
        .callback = [this, commandResult](const DebugConsole::CommandContext &)
        {
            m_debugConsole.clearMessages();
            m_debugConsole.addMessage(DebugConsole::MessageKind::Info, "Console cleared.");
            return commandResult(true, "");
        }});

    m_debugConsole.registerCommand({
        .name = "map",
        .description = "Show current map information.",
        .usage = "map",
        .callback = [this, commandResult](const DebugConsole::CommandContext &)
        {
            const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();
            std::ostringstream out;
            out << "world=" << m_activeWorldManifest.id
                << " session_map=" << m_gameSession.currentMapFileName();

            if (selectedMap)
            {
                out << " selected=" << selectedMap->map.fileName
                    << " canonical=" << selectedMap->map.canonicalId
                    << " scene=" << (selectedMap->outdoorMapData ? "outdoor" : "indoor")
                    << " local_events=" << (selectedMap->localEventProgram
                        ? selectedMap->localEventProgram->eventIds().size() : 0)
                    << " global_events=" << (selectedMap->globalEventProgram
                        ? selectedMap->globalEventProgram->eventIds().size() : 0);
            }

            return commandResult(true, out.str());
        }});

    m_debugConsole.registerCommand({
        .name = "loc",
        .description = "Show current party position and heading.",
        .usage = "loc",
        .callback = [activeGameplayWorld, commandResult](const DebugConsole::CommandContext &context)
        {
            if (!context.args.empty())
            {
                return commandResult(false, "Usage: loc");
            }

            IGameplayWorldRuntime *pWorldRuntime = activeGameplayWorld();

            if (pWorldRuntime == nullptr)
            {
                return commandResult(false, "No active map runtime.");
            }

            constexpr float FullCircleRadians = Pi * 2.0f;
            float normalizedYawRadians = std::fmod(pWorldRuntime->gameplayCameraYawRadians(), FullCircleRadians);

            if (normalizedYawRadians < 0.0f)
            {
                normalizedYawRadians += FullCircleRadians;
            }

            const float headingDegrees = normalizedYawRadians * 180.0f / Pi;
            const int headingYawUnits = static_cast<int>(
                std::lround(normalizedYawRadians * 2048.0f / FullCircleRadians)) % 2048;
            const float pitchDegrees = pWorldRuntime->gameplayCameraPitchRadians() * 180.0f / Pi;
            std::ostringstream out;
            out << std::fixed << std::setprecision(3)
                << "map=\"" << pWorldRuntime->mapName() << '"'
                << " position=(" << pWorldRuntime->partyX()
                << ", " << pWorldRuntime->partyY()
                << ", " << pWorldRuntime->partyFootZ() << ')'
                << " heading_yaw_units=" << headingYawUnits
                << " heading_degrees=" << headingDegrees
                << " yaw_radians=" << normalizedYawRadians
                << " pitch_degrees=" << pitchDegrees;
            return commandResult(true, out.str());
        }});

    m_debugConsole.registerCommand({
        .name = "goto",
        .description = "Jump directly to a map by merged map id.",
        .usage = "goto <map-id> [x y z direction-yaw-units]",
        .callback = [this, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.empty())
            {
                return commandResult(false, "Usage: goto <map-id> [x y z direction-yaw-units]");
            }

            const std::optional<int32_t> mapId = parseInt32Argument(context.args[0]);

            if (!mapId || *mapId <= 0)
            {
                return commandResult(false, "Invalid map id.");
            }

            if (m_gameDataLoader.getMapStats().findById(static_cast<uint32_t>(*mapId)) == nullptr)
            {
                return commandResult(false, "Unknown map id.");
            }

            PendingDebugMapJump pendingJump = {};
            pendingJump.mapId = *mapId;

            if (context.args.size() != 1 && context.args.size() != 5)
            {
                return commandResult(false, "Usage: goto <map-id> [x y z direction-yaw-units]");
            }

            if (context.args.size() == 5)
            {
                std::optional<int32_t> x = parseInt32Argument(context.args[1]);
                std::optional<int32_t> y = parseInt32Argument(context.args[2]);
                std::optional<int32_t> z = parseInt32Argument(context.args[3]);
                std::optional<int32_t> direction = parseInt32Argument(context.args[4]);

                if (!x || !y || !z || !direction)
                {
                    return commandResult(false, "Invalid map start coordinates.");
                }

                pendingJump.start = DebugMapJumpStart{
                    .x = *x,
                    .y = *y,
                    .z = *z,
                    .directionYawUnits = *direction,
                };
            }

            m_pendingDebugMapJump = pendingJump;
            return commandResult(true, "Queued map jump " + std::to_string(*mapId));
        }});

    m_debugConsole.registerCommand({
        .name = "setup",
        .description = "Apply predefined debug story states.",
        .usage = "setup breach",
        .callback = [this, activeParty, activeEventRuntimeState, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.size() != 1 || toLowerCopy(context.args[0]) != "breach")
            {
                return commandResult(false, "Usage: setup breach");
            }

            Party *pParty = activeParty();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            EventRuntimeState *pRuntimeState = activeEventRuntimeState();

            if (pRuntimeState != nullptr)
            {
                m_gameSession.mergeNamedGlobalVarsFromRuntime(*pRuntimeState);
            }

            for (const std::pair<std::string_view, int32_t> &entry : DebugBreachEntryGlobals)
            {
                const std::string name(entry.first);
                m_gameSession.setNamedGlobalVar(name, entry.second);

                if (pRuntimeState != nullptr)
                {
                    pRuntimeState->namedGlobalVars[name] = entry.second;
                }
            }

            for (std::string_view globalName : DebugBreachEntryClearedGlobals)
            {
                const std::string name(globalName);
                m_gameSession.clearNamedGlobalVar(name);

                if (pRuntimeState != nullptr)
                {
                    pRuntimeState->namedGlobalVars.erase(name);
                }
            }

            pParty->setQuestBit(1713, true);  // Enter The Controlled Breach and bring Runaway Chaos back.
            pParty->setQuestBit(1714, false); // Find your friends.
            pParty->setQuestBit(1715, false); // Find entrance to the main Breach structure.

            PendingDebugMapJump pendingJump = {};
            pendingJump.mapId = DebugBreachEntryMapId;
            m_pendingDebugMapJump = pendingJump;
            return commandResult(true, "Set clean Breach quest state and queued BrAlvar jump.");
        }});

    m_debugConsole.registerCommand({
        .name = "event",
        .description = "Execute a map event by id.",
        .usage = "event <id>",
        .callback = [this, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.empty())
            {
                return commandResult(false, "Usage: event <id>");
            }

            const std::optional<int32_t> eventId = parseInt32Argument(context.args[0]);

            if (!eventId || *eventId < 0 || *eventId > 65535)
            {
                return commandResult(false, "Invalid event id.");
            }

            if (m_pMapSceneRuntime == nullptr || m_pMapSceneRuntime->eventRuntimeState() == nullptr)
            {
                return commandResult(false, "No active map runtime.");
            }

            const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

            if (!selectedMap)
            {
                return commandResult(false, "No selected map.");
            }

            EventRuntime eventRuntime(&m_gameDataLoader.getHouseTable(), &m_gameDataLoader.getNpcDialogTable());
            const bool executed = eventRuntime.executeEventById(
                selectedMap->localEventProgram,
                selectedMap->globalEventProgram,
                static_cast<uint16_t>(*eventId),
                *m_pMapSceneRuntime->eventRuntimeState(),
                &m_pMapSceneRuntime->party(),
                m_pMapSceneRuntime->sceneEventContext());
            return commandResult(executed, executed ? "Executed event " + std::to_string(*eventId) : "Event failed.");
        }});

    m_debugConsole.registerCommand({
        .name = "qbit",
        .description = "Inspect or mutate party quest bits.",
        .usage = "qbit get|set|clear <id> [id...] | qbit dump [active|all|filter]",
        .callback = [this, activeParty, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.empty())
            {
                return commandResult(false, "Usage: qbit get|set|clear <id> [id...] | qbit dump [active|all|filter]");
            }

            Party *pParty = activeParty();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            const std::string action = toLowerCopy(context.args[0]);

            if (action == "dump")
            {
                const std::string filter = context.args.size() >= 2 ? lowerSearchText(context.args[1]) : "active";
                const bool activeOnly = filter.empty() || filter == "active";
                const bool allRows = filter == "all";
                const Party::Snapshot snapshot = pParty->snapshot();
                const std::vector<JournalQuestEntry> &questEntries =
                    m_gameSession.data().journalQuestTable().entries();
                std::set<uint32_t> qbitIds;
                std::ostringstream out;
                size_t emitted = 0;

                out << "QBits";

                if (activeOnly)
                {
                    out << " active";
                }
                else if (!allRows)
                {
                    out << " matching '" << context.args[1] << "'";
                }

                out << ":\n";

                if (activeOnly)
                {
                    qbitIds.insert(snapshot.questBits.begin(), snapshot.questBits.end());
                }
                else
                {
                    for (const JournalQuestEntry &entry : questEntries)
                    {
                        if (!allRows)
                        {
                            const std::string haystack = journalQuestEntrySearchText(entry.qbitId, &entry);

                            if (haystack.find(filter) == std::string::npos)
                            {
                                continue;
                            }
                        }

                        qbitIds.insert(entry.qbitId);
                    }

                    for (uint32_t qbitId : snapshot.questBits)
                    {
                        if (allRows)
                        {
                            qbitIds.insert(qbitId);
                            continue;
                        }

                        const JournalQuestEntry *pEntry = findJournalQuestEntry(questEntries, qbitId);
                        const std::string haystack = journalQuestEntrySearchText(qbitId, pEntry);

                        if (haystack.find(filter) != std::string::npos)
                        {
                            qbitIds.insert(qbitId);
                        }
                    }
                }

                for (uint32_t qbitId : qbitIds)
                {
                    if (qbitId == 0)
                    {
                        continue;
                    }

                    const bool isActive = snapshot.questBits.contains(qbitId);

                    if (activeOnly && !isActive)
                    {
                        continue;
                    }

                    const JournalQuestEntry *pEntry = findJournalQuestEntry(questEntries, qbitId);
                    out << qbitId << " [" << (isActive ? "set" : "clear") << "] "
                        << journalQuestEntryDetails(pEntry) << '\n';
                    ++emitted;

                    if (emitted >= 120)
                    {
                        out << "... truncated\n";
                        break;
                    }
                }

                if (emitted == 0)
                {
                    out << "<none>";
                }

                return commandResult(true, out.str());
            }

            if (context.args.size() < 2)
            {
                return commandResult(false, "Usage: qbit get|set|clear <id> [id...] | qbit dump [active|all|filter]");
            }

            std::vector<uint32_t> qbitIds;
            qbitIds.reserve(context.args.size() - 1);

            for (size_t argumentIndex = 1; argumentIndex < context.args.size(); ++argumentIndex)
            {
                const std::optional<int32_t> qbitId = parseInt32Argument(context.args[argumentIndex]);

                if (!qbitId || *qbitId < 0)
                {
                    return commandResult(false, "Invalid qbit id: " + context.args[argumentIndex]);
                }

                qbitIds.push_back(static_cast<uint32_t>(*qbitId));
            }

            const auto formatQBitResults =
                [pParty](const std::vector<uint32_t> &ids) -> std::string
                {
                    std::ostringstream out;

                    for (size_t index = 0; index < ids.size(); ++index)
                    {
                        const uint32_t id = ids[index];

                        if (index != 0)
                        {
                            out << ", ";
                        }

                        out << "qbit " << id << "=" << boolString(pParty->hasQuestBit(id));
                    }

                    return out.str();
                };

            if (action == "get")
            {
                return commandResult(true, formatQBitResults(qbitIds));
            }

            if (action == "set")
            {
                for (uint32_t id : qbitIds)
                {
                    pParty->setQuestBit(id, true);
                }

                return commandResult(true, formatQBitResults(qbitIds));
            }

            if (action == "clear")
            {
                for (uint32_t id : qbitIds)
                {
                    pParty->setQuestBit(id, false);
                }

                return commandResult(true, formatQBitResults(qbitIds));
            }

            return commandResult(false, "Usage: qbit get|set|clear <id> [id...] | qbit dump [active|all|filter]");
        }});

    m_debugConsole.registerCommand({
        .name = "npc",
        .description = "Inspect or mutate NPC debug state.",
        .usage = "npc greeting get|reset|set <npc-id> [greeting-id]",
        .callback = [this, activeParty, activeEventRuntimeState, commandResult](
            const DebugConsole::CommandContext &context)
        {
            if (context.args.size() < 3 || toLowerCopy(context.args[0]) != "greeting")
            {
                return commandResult(false, "Usage: npc greeting get|reset|set <npc-id> [greeting-id]");
            }

            const std::string action = toLowerCopy(context.args[1]);
            const std::optional<int32_t> parsedNpcId = parseInt32Argument(context.args[2]);

            if (!parsedNpcId || *parsedNpcId < 0)
            {
                return commandResult(false, "Invalid npc id.");
            }

            const uint32_t npcId = static_cast<uint32_t>(*parsedNpcId);
            const NpcEntry *pNpc = m_gameDataLoader.getNpcDialogTable().getNpc(npcId);

            if (pNpc == nullptr)
            {
                return commandResult(false, "Unknown npc id.");
            }

            Party *pParty = activeParty();
            EventRuntimeState *pRuntimeState = activeEventRuntimeState();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            const Party::Snapshot partySnapshot = pParty->snapshot();
            uint32_t greetingId = pNpc->greetId;
            uint32_t displayCount = 0;
            const char *pSource = "base";

            const std::unordered_map<uint32_t, uint32_t>::const_iterator runtimeGreetingIt =
                pRuntimeState != nullptr ? pRuntimeState->npcGreetingOverrides.find(npcId)
                                         : std::unordered_map<uint32_t, uint32_t>::const_iterator();

            if (pRuntimeState != nullptr && runtimeGreetingIt != pRuntimeState->npcGreetingOverrides.end())
            {
                greetingId = runtimeGreetingIt->second;
                pSource = "runtime override";
            }
            else
            {
                const std::unordered_map<uint32_t, uint32_t>::const_iterator partyGreetingIt =
                    partySnapshot.npcGreetingOverrides.find(npcId);

                if (partyGreetingIt != partySnapshot.npcGreetingOverrides.end())
                {
                    greetingId = partyGreetingIt->second;
                    pSource = "party override";
                }
            }

            const std::unordered_map<uint32_t, uint32_t> *pDisplayCounts =
                pRuntimeState != nullptr ? &pRuntimeState->npcGreetingDisplayCounts
                                         : &partySnapshot.npcGreetingDisplayCounts;
            const std::unordered_map<uint32_t, uint32_t>::const_iterator displayIt = pDisplayCounts->find(npcId);

            if (displayIt != pDisplayCounts->end())
            {
                displayCount = displayIt->second;
            }

            if (action == "get")
            {
                std::ostringstream out;
                out << "npc " << npcId << " greeting=" << greetingId << " (" << pSource << ")"
                    << " display_count=" << displayCount << " name=\"" << pNpc->name << "\"";
                return commandResult(true, out.str());
            }

            if (action != "reset" && action != "set")
            {
                return commandResult(false, "Usage: npc greeting get|reset|set <npc-id> [greeting-id]");
            }

            if (action == "set")
            {
                if (context.args.size() < 4)
                {
                    return commandResult(false, "Usage: npc greeting set <npc-id> <greeting-id>");
                }

                const std::optional<int32_t> parsedGreetingId = parseInt32Argument(context.args[3]);

                if (!parsedGreetingId || *parsedGreetingId < 0)
                {
                    return commandResult(false, "Invalid greeting id.");
                }

                greetingId = static_cast<uint32_t>(*parsedGreetingId);
            }
            else if (context.args.size() >= 4)
            {
                const std::optional<int32_t> parsedGreetingId = parseInt32Argument(context.args[3]);

                if (!parsedGreetingId || *parsedGreetingId < 0)
                {
                    return commandResult(false, "Invalid greeting id.");
                }

                greetingId = static_cast<uint32_t>(*parsedGreetingId);
            }

            if (m_gameDataLoader.getNpcDialogTable().getGreeting(greetingId) == nullptr)
            {
                return commandResult(false, "Unknown greeting id.");
            }

            pParty->setNpcGreetingOverride(npcId, greetingId);

            if (pRuntimeState != nullptr)
            {
                pRuntimeState->npcGreetingOverrides[npcId] = greetingId;
                pRuntimeState->npcGreetingDisplayCounts[npcId] = 0;
            }

            return commandResult(
                true,
                "npc " + std::to_string(npcId) + " greeting=" + std::to_string(greetingId)
                    + " display_count=0 name=\"" + pNpc->name + "\"");
        }});

    m_debugConsole.registerCommand({
        .name = "mapvar",
        .description = "Inspect or mutate current map variables.",
        .usage = "mapvar get|set|clear <index> [value] | mapvar dump",
        .callback = [activeEventRuntimeState, commandResult](const DebugConsole::CommandContext &context)
        {
            EventRuntimeState *pRuntimeState = activeEventRuntimeState();

            if (pRuntimeState == nullptr)
            {
                return commandResult(false, "No active map runtime.");
            }

            if (context.args.empty())
            {
                return commandResult(false, "Usage: mapvar get|set|clear <index> [value] | mapvar dump");
            }

            const std::string action = toLowerCopy(context.args[0]);

            if (action == "dump")
            {
                std::ostringstream out;
                out << "Map vars:\n";
                size_t emitted = 0;

                for (size_t index = 0; index < pRuntimeState->mapVars.size(); ++index)
                {
                    const uint32_t value = static_cast<uint32_t>(pRuntimeState->mapVars[index]);

                    if (value == 0)
                    {
                        continue;
                    }

                    out << index << "=" << value << '\n';
                    ++emitted;
                }

                if (emitted == 0)
                {
                    out << "<none>";
                }

                return commandResult(true, out.str());
            }

            if (context.args.size() < 2)
            {
                return commandResult(false, "Usage: mapvar get|set|clear <index> [value] | mapvar dump");
            }

            const std::optional<int32_t> parsedIndex = parseInt32Argument(context.args[1]);

            if (!parsedIndex || *parsedIndex < 0
                || static_cast<size_t>(*parsedIndex) >= pRuntimeState->mapVars.size())
            {
                return commandResult(false, "Invalid map var index.");
            }

            const size_t index = static_cast<size_t>(*parsedIndex);

            if (action == "get")
            {
                return commandResult(
                    true,
                    "mapvar " + std::to_string(index) + "="
                        + std::to_string(static_cast<uint32_t>(pRuntimeState->mapVars[index])));
            }

            if (action == "set")
            {
                if (context.args.size() < 3)
                {
                    return commandResult(false, "Usage: mapvar set <index> <value>");
                }

                const std::optional<int32_t> parsedValue = parseInt32Argument(context.args[2]);

                if (!parsedValue || *parsedValue < 0 || *parsedValue > 255)
                {
                    return commandResult(false, "Invalid map var value.");
                }

                pRuntimeState->mapVars[index] = static_cast<uint8_t>(*parsedValue);
                return commandResult(
                    true,
                    "mapvar " + std::to_string(index) + "=" + std::to_string(*parsedValue));
            }

            if (action == "clear")
            {
                pRuntimeState->mapVars[index] = 0;
                return commandResult(true, "mapvar " + std::to_string(index) + "=0");
            }

            return commandResult(false, "Usage: mapvar get|set|clear <index> [value] | mapvar dump");
        }});

    m_debugConsole.registerCommand({
        .name = "global",
        .description = "Inspect or mutate named Lua runtime globals.",
        .usage = "global get|set|clear <name> [value] | global dump [filter]",
        .callback = [this, activeEventRuntimeState, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.empty())
            {
                return commandResult(false, "Usage: global get|set|clear <name> [value] | global dump [filter]");
            }

            if (EventRuntimeState *pRuntimeState = activeEventRuntimeState())
            {
                m_gameSession.mergeNamedGlobalVarsFromRuntime(*pRuntimeState);
            }

            const std::string action = toLowerCopy(context.args[0]);

            if (action == "dump")
            {
                const std::string filter = context.args.size() >= 2 ? lowerSearchText(context.args[1]) : "";
                std::vector<std::pair<std::string, int32_t>> entries;

                for (const auto &[name, value] : m_gameSession.namedGlobalVars())
                {
                    if (!filter.empty() && lowerSearchText(name).find(filter) == std::string::npos)
                    {
                        continue;
                    }

                    entries.emplace_back(name, value);
                }

                std::sort(
                    entries.begin(),
                    entries.end(),
                    [](const auto &left, const auto &right)
                    {
                        return left.first < right.first;
                    });

                std::ostringstream out;
                out << "Named globals";

                if (!filter.empty())
                {
                    out << " matching '" << context.args[1] << "'";
                }

                out << ":\n";

                size_t emitted = 0;

                for (const auto &[name, value] : entries)
                {
                    out << name << "=" << value << '\n';
                    ++emitted;

                    if (emitted >= 120)
                    {
                        out << "... truncated\n";
                        break;
                    }
                }

                if (emitted == 0)
                {
                    out << "<none>";
                }

                return commandResult(true, out.str());
            }

            if (context.args.size() < 2)
            {
                return commandResult(false, "Usage: global get|set|clear <name> [value] | global dump [filter]");
            }

            const std::string &name = context.args[1];

            if (name.empty())
            {
                return commandResult(false, "Invalid global name.");
            }

            if (action == "get")
            {
                const std::unordered_map<std::string, int32_t> &globals = m_gameSession.namedGlobalVars();
                const std::unordered_map<std::string, int32_t>::const_iterator it = globals.find(name);

                if (it == globals.end())
                {
                    return commandResult(true, "global " + name + "=0 (default)");
                }

                return commandResult(true, "global " + name + "=" + std::to_string(it->second));
            }

            if (action == "set")
            {
                if (context.args.size() < 3)
                {
                    return commandResult(false, "Usage: global set <name> <value>");
                }

                const std::optional<int32_t> value = parseInt32Argument(context.args[2]);

                if (!value)
                {
                    return commandResult(false, "Invalid global value.");
                }

                m_gameSession.setNamedGlobalVar(name, *value);

                if (EventRuntimeState *pRuntimeState = activeEventRuntimeState())
                {
                    pRuntimeState->namedGlobalVars[name] = *value;
                }

                return commandResult(true, "global " + name + "=" + std::to_string(*value));
            }

            if (action == "clear")
            {
                m_gameSession.clearNamedGlobalVar(name);

                if (EventRuntimeState *pRuntimeState = activeEventRuntimeState())
                {
                    pRuntimeState->namedGlobalVars.erase(name);
                }

                return commandResult(true, "global " + name + " cleared");
            }

            return commandResult(false, "Usage: global get|set|clear <name> [value] | global dump [filter]");
        }});

    m_debugConsole.registerCommand({
        .name = "award",
        .description = "Inspect or mutate party awards.",
        .usage = "award get|set|clear <id> | award dump [active|all|filter]",
        .callback = [this, activeParty, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.empty())
            {
                return commandResult(false, "Usage: award get|set|clear <id> | award dump [active|all|filter]");
            }

            Party *pParty = activeParty();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            const std::string action = toLowerCopy(context.args[0]);

            if (action == "dump")
            {
                const std::string filter = context.args.size() >= 2 ? lowerSearchText(context.args[1]) : "active";
                const bool activeOnly = filter.empty() || filter == "active";
                const bool allRows = filter == "all";
                const std::vector<DebugAwardEntry> awards = loadDebugAwardEntries(m_pAssetFileSystem);
                std::ostringstream out;
                size_t emitted = 0;

                out << "Awards";

                if (activeOnly)
                {
                    out << " active";
                }
                else if (!allRows)
                {
                    out << " matching '" << context.args[1] << "'";
                }

                out << ":\n";

                for (const DebugAwardEntry &entry : awards)
                {
                    const bool isActive = pParty->hasAward(entry.id);
                    const std::string haystack = lowerSearchText(entry.text + " " + entry.notes);

                    if ((activeOnly && !isActive)
                        || (!activeOnly && !allRows && haystack.find(filter) == std::string::npos))
                    {
                        continue;
                    }

                    out << entry.id << " [" << (isActive ? "set" : "clear") << "] " << entry.text << '\n';
                    ++emitted;

                    if (emitted >= 120)
                    {
                        out << "... truncated\n";
                        break;
                    }
                }

                if (emitted == 0)
                {
                    out << "<none>";
                }

                return commandResult(true, out.str());
            }

            if (context.args.size() < 2)
            {
                return commandResult(false, "Usage: award get|set|clear <id> | award dump [active|all|filter]");
            }

            const std::optional<int32_t> awardId = parseInt32Argument(context.args[1]);

            if (!awardId || *awardId < 0)
            {
                return commandResult(false, "Invalid award id.");
            }

            const uint32_t id = static_cast<uint32_t>(*awardId);

            if (action == "get")
            {
                return commandResult(true, "award " + std::to_string(id) + "=" + boolString(pParty->hasAward(id)));
            }

            if (action == "set")
            {
                pParty->addAward(id);
                return commandResult(true, "award " + std::to_string(id) + "=true");
            }

            if (action == "clear")
            {
                pParty->removeAward(id);
                return commandResult(true, "award " + std::to_string(id) + "=false");
            }

            return commandResult(false, "Usage: award get|set|clear <id> | award dump [active|all|filter]");
        }});

    m_debugConsole.registerCommand({
        .name = "arcomage",
        .description = "Simulate Arcomage results using the same party bookkeeping as a finished match.",
        .usage = "arcomage win <house-id|mm8>",
        .callback = [this, activeParty, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.size() < 2 || toLowerCopy(context.args[0]) != "win")
            {
                return commandResult(false, "Usage: arcomage win <house-id|mm8>");
            }

            Party *pParty = activeParty();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            std::vector<uint32_t> houseIds;
            const std::string target = toLowerCopy(context.args[1]);

            if (target == "mm8" || target == "jadame")
            {
                for (uint32_t houseId = 228; houseId <= 238; ++houseId)
                {
                    houseIds.push_back(houseId);
                }
            }
            else
            {
                const std::optional<int32_t> parsedHouseId = parseInt32Argument(context.args[1]);

                if (!parsedHouseId || *parsedHouseId <= 0)
                {
                    return commandResult(false, "Invalid Arcomage house id.");
                }

                houseIds.push_back(static_cast<uint32_t>(*parsedHouseId));
            }

            int totalGoldReward = 0;
            size_t firstWinCount = 0;
            std::ostringstream out;
            out << "Arcomage wins:";

            for (uint32_t houseId : houseIds)
            {
                const HouseEntry *pHouseEntry = m_gameDataLoader.getHouseTable().get(houseId);
                const ArcomageTavernRule *pRule = m_gameDataLoader.getArcomageLibrary().ruleForHouse(houseId);

                if (pHouseEntry == nullptr || pRule == nullptr)
                {
                    return commandResult(false, "Unknown Arcomage tavern house id: " + std::to_string(houseId));
                }

                const bool firstWin = !pParty->hasArcomageWinAt(houseId);
                const int goldReward = firstWin ? static_cast<int>(pHouseEntry->priceMultiplier * 100.0f) : 0;
                const uint32_t firstWinAwardId = pRule->firstWinAwardId;
                pParty->recordArcomageWin(houseId, goldReward, firstWinAwardId);

                totalGoldReward += goldReward;
                firstWinCount += firstWin ? 1u : 0u;
                out << ' ' << houseId << (firstWin ? "(first)" : "(repeat)");
            }

            if (m_pMapSceneRuntime != nullptr)
            {
                synchronizeSessionFromRuntime();
            }
            else
            {
                m_gameSession.setPartyState(*pParty);
            }

            out << "; first_wins=" << firstWinCount
                << "; gold=" << totalGoldReward
                << "; qbit174=" << boolString(pParty->hasQuestBit(174))
                << "; award41=" << boolString(pParty->hasAward(41));
            return commandResult(true, out.str());
        }});

    m_debugConsole.registerCommand({
        .name = "gold",
        .description = "Inspect or mutate party gold.",
        .usage = "gold get|add|set <amount>",
        .callback = [activeParty, commandResult](const DebugConsole::CommandContext &context)
        {
            Party *pParty = activeParty();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            if (context.args.empty() || toLowerCopy(context.args[0]) == "get")
            {
                return commandResult(true, "gold=" + std::to_string(pParty->gold()));
            }

            if (context.args.size() < 2)
            {
                return commandResult(false, "Usage: gold get|add|set <amount>");
            }

            const std::optional<int32_t> amount = parseInt32Argument(context.args[1]);

            if (!amount)
            {
                return commandResult(false, "Invalid amount.");
            }

            if (toLowerCopy(context.args[0]) == "add")
            {
                pParty->addGold(*amount);
            }
            else if (toLowerCopy(context.args[0]) == "set")
            {
                pParty->addGold(*amount - pParty->gold());
            }
            else
            {
                return commandResult(false, "Usage: gold get|add|set <amount>");
            }

            return commandResult(true, "gold=" + std::to_string(pParty->gold()));
        }});

    m_debugConsole.registerCommand({
        .name = "food",
        .description = "Inspect or mutate party food.",
        .usage = "food get|add|set <amount>",
        .callback = [activeParty, commandResult](const DebugConsole::CommandContext &context)
        {
            Party *pParty = activeParty();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            if (context.args.empty() || toLowerCopy(context.args[0]) == "get")
            {
                return commandResult(true, "food=" + std::to_string(pParty->food()));
            }

            if (context.args.size() < 2)
            {
                return commandResult(false, "Usage: food get|add|set <amount>");
            }

            const std::optional<int32_t> amount = parseInt32Argument(context.args[1]);

            if (!amount)
            {
                return commandResult(false, "Invalid amount.");
            }

            if (toLowerCopy(context.args[0]) == "add")
            {
                pParty->addFood(*amount);
            }
            else if (toLowerCopy(context.args[0]) == "set")
            {
                pParty->addFood(*amount - pParty->food());
            }
            else
            {
                return commandResult(false, "Usage: food get|add|set <amount>");
            }

            return commandResult(true, "food=" + std::to_string(pParty->food()));
        }});

    m_debugConsole.registerCommand({
        .name = "hp",
        .description = "Heal the party.",
        .usage = "hp full",
        .callback = [activeParty, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.empty() || toLowerCopy(context.args[0]) != "full")
            {
                return commandResult(false, "Usage: hp full");
            }

            Party *pParty = activeParty();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            pParty->reviveAndRestoreAll();
            return commandResult(true, "Party restored.");
        }});

    m_debugConsole.registerCommand({
        .name = "player",
        .description = "Create a level-1 player character and add it to the party.",
        .usage = "player add <class-id|class-name> [name]",
        .callback = [this, activeParty, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.size() < 2 || toLowerCopy(context.args[0]) != "add")
            {
                return commandResult(false, "Usage: player add <class-id|class-name> [name]");
            }

            Party *pParty = activeParty();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            if (pParty->isFull())
            {
                return commandResult(false, "Party is full.");
            }

            const ClassSkillTable &classSkillTable = m_gameDataLoader.getClassSkillTable();
            const std::optional<std::string> className = debugResolveClassName(context.args[1], classSkillTable);

            if (!className)
            {
                return commandResult(false, "Unknown class: " + context.args[1]);
            }

            const std::optional<uint32_t> classId = classSkillTable.classIdForName(*className);

            if (!classId)
            {
                return commandResult(false, "Unknown class: " + context.args[1]);
            }

            std::string name;

            if (context.args.size() >= 3)
            {
                std::ostringstream nameStream;

                for (size_t index = 2; index < context.args.size(); ++index)
                {
                    if (index != 2)
                    {
                        nameStream << ' ';
                    }

                    nameStream << context.args[index];
                }

                name = trimCopy(nameStream.str());
            }

            Character character = debugCreatePlayerCharacter(
                *className,
                *classId,
                name,
                m_gameDataLoader.getCharacterDollTable(),
                pParty->memberCount());

            if (!pParty->recruitCharacter(character))
            {
                return commandResult(false, "Could not add player character.");
            }

            synchronizeSessionFromRuntime();

            const Character *pMember = pParty->member(pParty->memberCount() - 1);
            const std::string addedName = pMember != nullptr ? pMember->name : character.name;
            return commandResult(
                true,
                "Added " + addedName + " as " + displayClassName(*className) + " (class "
                    + std::to_string(*classId) + ").");
        }});

    m_debugConsole.registerCommand({
        .name = "hire",
        .description = "Hire an available NPC by profession id.",
        .usage = "hire <profession-id>",
        .callback = [this, activeParty, activeEventRuntimeState, commandResult](
            const DebugConsole::CommandContext &context)
        {
            if (context.args.size() != 1)
            {
                return commandResult(false, "Usage: hire <profession-id>");
            }

            const std::optional<int32_t> parsedProfessionId = parseInt32Argument(context.args[0]);

            if (!parsedProfessionId || *parsedProfessionId <= 0)
            {
                return commandResult(false, "Invalid profession id.");
            }

            Party *pParty = activeParty();
            EventRuntimeState *pRuntimeState = activeEventRuntimeState();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            if (pRuntimeState == nullptr)
            {
                return commandResult(false, "No active map runtime.");
            }

            if (!debugContinentAllowsNpcFollowers(
                    m_gameDataLoader.getSelectedMap(),
                    m_gameDataLoader.getMergedContinentSettingTable()))
            {
                return commandResult(false, "This continent does not allow NPC followers.");
            }

            const uint32_t professionId = static_cast<uint32_t>(*parsedProfessionId);
            const MergedNpcProfessionEntry *pProfession =
                m_gameDataLoader.getMergedNpcProfessionTable().get(professionId);

            if (pProfession == nullptr)
            {
                return commandResult(false, "Unknown NPC profession id.");
            }

            std::optional<NpcEntry> selectedNpc;
            std::optional<NpcEntry> alreadyHiredNpc;
            bool sawHireableNpc = false;

            for (const NpcEntry &npc : debugNpcEntriesForProfession(
                    m_gameDataLoader.getNpcDialogTable(),
                    *pRuntimeState,
                    professionId))
            {
                if (!debugNpcCanOfferProfessionHire(npc, *pProfession))
                {
                    continue;
                }

                sawHireableNpc = true;

                if (debugHasHiredNpcFollower(*pRuntimeState, npc.id))
                {
                    if (!alreadyHiredNpc)
                    {
                        alreadyHiredNpc = npc;
                    }

                    continue;
                }

                if (pRuntimeState->unavailableNpcIds.contains(npc.id))
                {
                    continue;
                }

                selectedNpc = npc;
                break;
            }

            if (!selectedNpc)
            {
                if (alreadyHiredNpc)
                {
                    return commandResult(
                        false,
                        alreadyHiredNpc->name + " is already following you.");
                }

                if (sawHireableNpc)
                {
                    return commandResult(false, "All matching NPCs are unavailable.");
                }

                return commandResult(
                    false,
                    "No hireable NPC found for profession " + std::to_string(professionId) + " ("
                        + pProfession->profession + ").");
            }

            if (pRuntimeState->hiredNpcFollowers.size() >= DebugMaxNpcFollowerCount
                || debugHiredNpcFollowerFeePercent(*pRuntimeState) >= DebugMaxNpcFollowerFeePercent)
            {
                return commandResult(false, "You already have enough followers.");
            }

            if (pParty->gold() < static_cast<int>(pProfession->weeklyCost))
            {
                return commandResult(false, "You do not have enough gold.");
            }

            pParty->addGold(-static_cast<int>(pProfession->weeklyCost));

            HiredNpcFollower follower = {};
            follower.npcId = selectedNpc->id;
            follower.professionId = selectedNpc->professionId;
            follower.weeklyCost = pProfession->weeklyCost;
            pRuntimeState->hiredNpcFollowers.push_back(follower);
            pRuntimeState->unavailableNpcIds.insert(selectedNpc->id);
            pRuntimeState->npcHouseOverrides.erase(selectedNpc->id);
            pParty->addHiredNpcFollower(follower);
            pParty->setNpcUnavailable(selectedNpc->id, true);
            pParty->clearNpcHouseOverride(selectedNpc->id);

            if (m_pMapSceneRuntime != nullptr)
            {
                if (m_pMapSceneRuntime->kind() == SceneKind::Outdoor && m_pOutdoorWorldRuntime != nullptr)
                {
                    m_pOutdoorWorldRuntime->applyEventRuntimeState();
                    if (m_pOutdoorPartyRuntime != nullptr)
                    {
                        m_pOutdoorPartyRuntime->applyEventRuntimeState(*pRuntimeState, false);
                    }
                }
                else if (m_pMapSceneRuntime->kind() == SceneKind::Indoor)
                {
                    IndoorSceneRuntime *pIndoorRuntime =
                        static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
                    pIndoorRuntime->worldRuntime().applyEventRuntimeState();
                    pIndoorRuntime->party().applyEventRuntimeState(*pRuntimeState, false);
                }
            }

            synchronizeSessionFromRuntime();

            return commandResult(
                true,
                "Hired " + selectedNpc->name + " (npc " + std::to_string(selectedNpc->id)
                    + ", profession " + std::to_string(professionId) + " " + pProfession->profession + ").");
        }});

    m_debugConsole.registerCommand({
        .name = "item",
        .description = "Search for or grant an item to the party.",
        .usage = "item search <text> | item give <id|text> [qty] | item add <id> [qty]",
        .callback = [this, activeParty, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.size() < 2)
            {
                return commandResult(false, "Usage: item search <text> | item give <id|text> [qty]");
            }

            const std::string action = toLowerCopy(context.args[0]);
            const ItemTable &itemTable = m_gameDataLoader.getItemTable();

            if (action == "search")
            {
                const std::vector<const ItemDefinition *> matches = findItemMatches(itemTable, context.args[1], 24);
                std::ostringstream out;
                out << "Item matches for '" << context.args[1] << "':\n";

                for (const ItemDefinition *pItem : matches)
                {
                    out << pItem->itemId << " " << pItem->name;

                    if (!pItem->unidentifiedName.empty() && pItem->unidentifiedName != pItem->name)
                    {
                        out << " (" << pItem->unidentifiedName << ")";
                    }

                    if (!pItem->skillGroup.empty())
                    {
                        out << " [" << pItem->skillGroup << "]";
                    }

                    out << '\n';
                }

                if (matches.empty())
                {
                    out << "<none>";
                }

                return commandResult(true, out.str());
            }

            if (action != "add" && action != "give")
            {
                return commandResult(false, "Usage: item search <text> | item give <id|text> [qty]");
            }

            Party *pParty = activeParty();

            if (pParty == nullptr)
            {
                return commandResult(false, "No active party.");
            }

            const std::optional<int32_t> quantity =
                context.args.size() >= 3 ? parseInt32Argument(context.args[2]) : std::optional<int32_t>(1);

            if (!quantity || *quantity <= 0)
            {
                return commandResult(false, "Invalid quantity.");
            }

            const std::optional<int32_t> parsedItemId = parseInt32Argument(context.args[1]);
            const ItemDefinition *pItem = nullptr;

            if (parsedItemId && *parsedItemId > 0)
            {
                pItem = itemTable.get(static_cast<uint32_t>(*parsedItemId));
            }
            else
            {
                const std::vector<const ItemDefinition *> matches = findItemMatches(itemTable, context.args[1], 1);
                pItem = !matches.empty() ? matches.front() : nullptr;
            }

            if (pItem == nullptr)
            {
                return commandResult(false, "No matching item.");
            }

            pParty->grantItem(pItem->itemId, static_cast<uint32_t>(*quantity));
            return commandResult(
                true,
                "Granted " + std::to_string(*quantity) + "x " + pItem->name
                    + " (" + std::to_string(pItem->itemId) + ")");
        }});

    m_debugConsole.registerCommand({
        .name = "tp",
        .description = "Teleport the party on the current map.",
        .usage = "tp <x> <y> <z>",
        .callback = [this, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.size() < 3)
            {
                return commandResult(false, "Usage: tp <x> <y> <z>");
            }

            const std::optional<float> x = parseFloatArgument(context.args[0]);
            const std::optional<float> y = parseFloatArgument(context.args[1]);
            const std::optional<float> z = parseFloatArgument(context.args[2]);

            if (!x || !y || !z)
            {
                return commandResult(false, "Invalid coordinates.");
            }

            if (m_pMapSceneRuntime == nullptr)
            {
                return commandResult(false, "No active map runtime.");
            }

            if (m_pMapSceneRuntime->kind() == SceneKind::Outdoor && m_pOutdoorPartyRuntime != nullptr)
            {
                m_pOutdoorPartyRuntime->teleportTo(*x, *y, *z);
            }
            else if (m_pMapSceneRuntime->kind() == SceneKind::Indoor)
            {
                IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
                pIndoorRuntime->partyRuntime().teleportPartyPosition(*x, *y, *z);
            }

            synchronizeSessionFromRuntime();
            return commandResult(true, "Teleported.");
        }});

    m_debugConsole.registerCommand({
        .name = "config",
        .description = "Inspect or mutate debug settings.",
        .usage = "config get|set|toggle <name> [value]",
        .callback = [this, activeParty, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.size() < 2)
            {
                return commandResult(
                    false,
                    "Usage: config get|set|toggle immortal|unlimited_mana|invisible|start_flying [value]");
            }

            const std::string action = toLowerCopy(context.args[0]);
            const std::string name = toLowerCopy(context.args[1]);

            const auto getSetting = [this, activeParty, &name]() -> std::optional<bool>
            {
                if (name == "immortal")
                {
                    return m_settings.immortal;
                }

                if (name == "unlimited_mana")
                {
                    return m_settings.unlimitedMana;
                }

                if (name == "start_flying" || name == "flying")
                {
                    return m_settings.startFlying;
                }

                if (name == "invisible" || name == "invisibility")
                {
                    Party *pParty = activeParty();
                    return pParty != nullptr
                        ? std::optional<bool>(pParty->hasPartyBuff(PartyBuffId::Invisibility))
                        : std::nullopt;
                }

                return std::nullopt;
            };

            const auto setSetting = [this, &name](bool value) -> bool
            {
                if (name == "immortal")
                {
                    m_settings.immortal = value;
                }
                else if (name == "unlimited_mana")
                {
                    m_settings.unlimitedMana = value;
                }
                else if (name == "start_flying" || name == "flying")
                {
                    m_settings.startFlying = value;
                }
                else
                {
                    return false;
                }

                applyCurrentSettingsToActiveRuntime();

                if (Party *pParty = m_pMapSceneRuntime != nullptr ? &m_pMapSceneRuntime->party() : nullptr)
                {
                    pParty->setDebugDamageImmune(m_settings.immortal);
                    pParty->setDebugUnlimitedMana(m_settings.unlimitedMana);
                }

                std::string error;

                if (!saveGameSettings(settingsFilePath(), m_settings, error))
                {
                    std::cerr << "GameApplication: failed to write settings.ini: " << error << '\n';
                }

                return true;
            };

            const auto setRuntimeSetting = [activeParty, &name](bool value) -> bool
            {
                if (name != "invisible" && name != "invisibility")
                {
                    return false;
                }

                Party *pParty = activeParty();

                if (pParty == nullptr)
                {
                    return false;
                }

                if (value)
                {
                    pParty->applyPartyBuff(
                        PartyBuffId::Invisibility,
                        365.0f * 24.0f * 60.0f * 60.0f,
                        0,
                        static_cast<uint32_t>(SpellId::Invisibility),
                        10,
                        SkillMastery::Grandmaster,
                        0);
                }
                else
                {
                    pParty->clearPartyBuff(PartyBuffId::Invisibility);
                }

                return true;
            };

            if (action == "get")
            {
                const std::optional<bool> value = getSetting();
                return value
                    ? commandResult(true, name + "=" + boolString(*value))
                    : commandResult(false, "Unknown setting.");
            }

            if (action == "toggle")
            {
                const std::optional<bool> value = getSetting();

                if (!value || (!setSetting(!*value) && !setRuntimeSetting(!*value)))
                {
                    return commandResult(false, "Unknown setting.");
                }

                return commandResult(true, name + "=" + boolString(!*value));
            }

            if (action == "set")
            {
                if (context.args.size() < 3)
                {
                    return commandResult(false, "Usage: config set <name> true|false");
                }

                const std::string raw = toLowerCopy(context.args[2]);
                const bool value = raw == "1" || raw == "true" || raw == "yes" || raw == "on";

                if (!setSetting(value) && !setRuntimeSetting(value))
                {
                    return commandResult(false, "Unknown setting.");
                }

                return commandResult(true, name + "=" + boolString(value));
            }

            return commandResult(false, "Usage: config get|set|toggle <name> [value]");
        }});

    m_debugConsole.registerCommand({
        .name = "reload",
        .description = "Reload current map.",
        .usage = "reload map",
        .callback = [this, commandResult](const DebugConsole::CommandContext &context)
        {
            if (context.args.empty() || toLowerCopy(context.args[0]) != "map")
            {
                return commandResult(false, "Usage: reload map");
            }

            if (m_pAssetFileSystem == nullptr || m_gameSession.currentMapFileName().empty())
            {
                return commandResult(false, "No map to reload.");
            }

            synchronizeSessionFromRuntime();

            if (!loadCurrentSessionMap(true))
            {
                return commandResult(false, "Reload failed.");
            }

            return commandResult(true, "Reloaded " + m_gameSession.currentMapFileName());
        }});

    updateDebugConsoleDataOptions();
    m_debugConsole.addMessage(DebugConsole::MessageKind::Info, "OpenYAMM debug console ready. Type help.");
    m_debugConsoleCommandsRegistered = true;
}

void GameApplication::updateDebugConsoleDataOptions()
{
    std::vector<DebugConsole::ItemOption> itemOptions;

    if (m_commonGameDataLoaded)
    {
        for (const ItemDefinition &item : m_gameDataLoader.getItemTable().entries())
        {
            if (item.itemId == 0 || item.name.empty())
            {
                continue;
            }

            itemOptions.push_back({
                .itemId = item.itemId,
                .name = item.name,
                .unidentifiedName = item.unidentifiedName,
                .iconName = item.iconName,
                .skillGroup = item.skillGroup,
                .notes = item.notes,
            });
        }
    }

    m_debugConsole.setItemOptions(std::move(itemOptions));

    if (m_commonGameDataLoaded)
    {
        m_debugConsole.setMapOptionsFromMapStats(m_gameDataLoader.getMapStats());
    }
    else
    {
        m_debugConsole.setMapOptions({});
    }
}

bool GameApplication::initializeDebugConsoleRenderer()
{
    if (!m_settings.debugConsole)
    {
        return true;
    }

    if (m_debugConsoleRendererInitialized)
    {
        return true;
    }

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO &io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    io.IniFilename = nullptr;
    configureDebugConsoleStyle();

    SDL_Window *pWindow = SDL_GetKeyboardFocus();

    if (pWindow == nullptr)
    {
        pWindow = SDL_GetMouseFocus();
    }

    if (pWindow == nullptr)
    {
        int windowCount = 0;
        SDL_Window **ppWindows = SDL_GetWindows(&windowCount);

        if (ppWindows != nullptr && windowCount > 0)
        {
            pWindow = ppWindows[0];
        }

        SDL_free(ppWindows);
    }

    if (pWindow == nullptr || !ImGui_ImplSDL3_InitForOther(pWindow))
    {
        return false;
    }

    if (!m_debugConsoleRenderer.initialize())
    {
        ImGui_ImplSDL3_Shutdown();
        ImGui::DestroyContext();
        return false;
    }

    registerDebugConsoleCommands();
    m_debugConsoleRendererInitialized = true;
    return true;
}

void GameApplication::shutdownDebugConsoleRenderer()
{
    if (!m_debugConsoleRendererInitialized)
    {
        return;
    }

    m_debugConsoleRenderer.shutdown();
    ImGui_ImplSDL3_Shutdown();
    ImGui::DestroyContext();
    m_debugConsoleRendererInitialized = false;
    m_debugConsoleFrameBegun = false;
}

void GameApplication::beginDebugConsoleFrame()
{
    if (!m_debugConsoleRendererInitialized || m_debugConsoleFrameBegun)
    {
        return;
    }

    if (m_debugConsole.enabled())
    {
        SDL_Window *pWindow = SDL_GetMouseFocus();

        if (pWindow == nullptr)
        {
            pWindow = SDL_GetKeyboardFocus();
        }

        if (pWindow != nullptr)
        {
            SDL_SetWindowRelativeMouseMode(pWindow, false);
        }

        SDL_ShowCursor();
    }

    ImGui_ImplSDL3_NewFrame();
    m_debugConsoleRenderer.newFrame();
    ImGui::NewFrame();
    m_debugConsoleFrameBegun = true;
}

void GameApplication::renderDebugConsoleFrame(int width, int height)
{
    if (!m_debugConsoleRendererInitialized || !m_debugConsoleFrameBegun)
    {
        return;
    }

    const Party *pActiveParty = nullptr;

    if (m_pMapSceneRuntime != nullptr)
    {
        pActiveParty = &m_pMapSceneRuntime->party();
    }
    else if (m_gameSession.partyState())
    {
        pActiveParty = &*m_gameSession.partyState();
    }

    m_debugConsole.setDebugToggleStates(
        m_settings.immortal,
        m_settings.unlimitedMana,
        pActiveParty != nullptr && pActiveParty->hasPartyBuff(PartyBuffId::Invisibility));
    m_debugConsole.render(width, height);
    ImGui::Render();
    m_debugConsoleRenderer.renderDrawData(ImGui::GetDrawData());
    m_debugConsoleFrameBegun = false;
}

bool GameApplication::processPendingDebugMapJump()
{
    if (!m_pendingDebugMapJump.has_value())
    {
        return false;
    }

    const PendingDebugMapJump pendingJump = *m_pendingDebugMapJump;
    const int mapId = pendingJump.mapId;
    m_pendingDebugMapJump.reset();

    if (m_pAssetFileSystem == nullptr)
    {
        m_debugConsole.addMessage(DebugConsole::MessageKind::Error, "Map jump unavailable: no asset filesystem.");
        return false;
    }

    const MapStatsEntry *pTargetMap = m_gameDataLoader.getMapStats().findById(static_cast<uint32_t>(mapId));

    if (pTargetMap == nullptr)
    {
        m_debugConsole.addMessage(DebugConsole::MessageKind::Error, "Map jump failed: unknown map id.");
        return false;
    }

    const std::string previousMapFileName = m_gameSession.currentMapFileName();
    const bool isSameMapJump = sameMapFileName(pTargetMap->fileName, previousMapFileName);
    EventRuntimeState *pLeavingRuntimeState =
        m_pMapSceneRuntime != nullptr ? m_pMapSceneRuntime->eventRuntimeState() : nullptr;
    PendingMapLeaveOutputs onLeaveOutputs = {};

    if (!isSameMapJump)
    {
        executeCurrentMapOnLeaveEvents();
        onLeaveOutputs = pLeavingRuntimeState != nullptr
            ? consumePendingMapLeaveOutputs(*pLeavingRuntimeState)
            : PendingMapLeaveOutputs{};
    }

    captureCurrentSceneState();

    if (!activateWorldForMap(*pTargetMap))
    {
        if (pLeavingRuntimeState != nullptr
            && m_pMapSceneRuntime != nullptr
            && m_pMapSceneRuntime->eventRuntimeState() == pLeavingRuntimeState)
        {
            appendPendingMapLeaveOutputs(*pLeavingRuntimeState, std::move(onLeaveOutputs));
        }

        m_debugConsole.addMessage(DebugConsole::MessageKind::Error, "Map jump failed: world switch failed.");
        return false;
    }
    const std::string targetWorldId = normalizeWorldId(pTargetMap->worldId);
    MapLoadTimingLogger timingLogger(pTargetMap->fileName, "debug_map_jump");
    timingLogger.stage("world activated");

    beginLoadingOverlay(LoadingOverlayScreen::Presentation::Fullscreen);
    renderLoadingOverlayProgress(15);
    timingLogger.stage("loading overlay begun");

    if (!m_gameDataLoader.loadMapByIdForGameplay(*m_pAssetFileSystem, mapId))
    {
        if (pLeavingRuntimeState != nullptr
            && m_pMapSceneRuntime != nullptr
            && m_pMapSceneRuntime->eventRuntimeState() == pLeavingRuntimeState)
        {
            appendPendingMapLeaveOutputs(*pLeavingRuntimeState, std::move(onLeaveOutputs));
        }

        cancelLoadingOverlay();
        m_debugConsole.addMessage(DebugConsole::MessageKind::Error, "Map jump failed: map load failed.");
        return false;
    }
    timingLogger.stage("game data loader map load");

    renderLoadingOverlayProgress(70);
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap)
    {
        if (pLeavingRuntimeState != nullptr
            && m_pMapSceneRuntime != nullptr
            && m_pMapSceneRuntime->eventRuntimeState() == pLeavingRuntimeState)
        {
            appendPendingMapLeaveOutputs(*pLeavingRuntimeState, std::move(onLeaveOutputs));
        }

        cancelLoadingOverlay();
        m_debugConsole.addMessage(DebugConsole::MessageKind::Error, "Map jump failed: selected map missing.");
        return false;
    }

    m_gameSession.setCurrentMapFileName(selectedMap->map.fileName);
    shutdownRenderer();
    timingLogger.stage("renderer shutdown");

    if (!initializeSelectedMapRuntime(true))
    {
        cancelLoadingOverlay();
        m_debugConsole.addMessage(DebugConsole::MessageKind::Error, "Map jump failed: runtime init failed.");
        return false;
    }
    timingLogger.stage("runtime and view initialized");

    if (!isSameMapJump)
    {
        EventRuntimeState *pArrivingRuntimeState =
            m_pMapSceneRuntime != nullptr ? m_pMapSceneRuntime->eventRuntimeState() : nullptr;

        if (pArrivingRuntimeState != nullptr)
        {
            appendPendingMapLeaveOutputs(*pArrivingRuntimeState, std::move(onLeaveOutputs));
        }
    }

    std::optional<int32_t> debugStartDirectionDegrees;

    if (pendingJump.start.has_value())
    {
        const DebugMapJumpStart &start = *pendingJump.start;

        if (m_pMapSceneRuntime != nullptr
            && m_pMapSceneRuntime->kind() == SceneKind::Outdoor
            && m_pOutdoorPartyRuntime != nullptr)
        {
            m_pOutdoorPartyRuntime->teleportTo(
                static_cast<float>(start.x),
                static_cast<float>(start.y),
                static_cast<float>(start.z));
        }
        else if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
        {
            IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
            pIndoorRuntime->partyRuntime().teleportPartyPosition(
                static_cast<float>(start.x),
                static_cast<float>(start.y),
                static_cast<float>(start.z));
        }

        const int32_t normalizedYawUnits = ((start.directionYawUnits % 2048) + 2048) % 2048;
        const int32_t directionDegrees = normalizedYawUnits * 360 / 2048;
        debugStartDirectionDegrees = directionDegrees;
        const float yawRadians = mapMoveHeadingDegreesToYawRadians(directionDegrees);

        if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Outdoor)
        {
            m_outdoorGameView.setCameraAngles(yawRadians, m_outdoorGameView.cameraPitchRadians());
        }
        else if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
        {
            m_indoorRenderer.setCameraAngles(yawRadians, m_indoorRenderer.cameraPitchRadians());
        }
    }
    else if (selectedMap->indoorMapData.has_value()
        && selectedMap->indoorMapData->partyStartPoint.has_value()
        && m_pMapSceneRuntime != nullptr
        && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
    {
        int32_t directionDegrees = selectedMap->indoorMapData->partyStartPoint->facingDegrees % 360;

        if (directionDegrees < 0)
        {
            directionDegrees += 360;
        }

        debugStartDirectionDegrees = directionDegrees;
        const float yawRadians = mapMoveHeadingDegreesToYawRadians(directionDegrees);
        m_indoorRenderer.setCameraAngles(yawRadians, m_indoorRenderer.cameraPitchRadians());
    }
    timingLogger.stage("debug start applied");
    const std::string sceneKind =
        m_pMapSceneRuntime != nullptr ? sceneKindName(m_pMapSceneRuntime->kind()) : "none";
    GAMEPLAY_DEBUG_TRACE(
        "map_loaded source=debug_console map=\"" + selectedMap->map.fileName + "\""
        + " scene_kind=" + sceneKind
        + " game_minutes=" + std::to_string(m_gameSession.gameMinutes())
        + " initialize_view=true"
        + " start_override=" + (pendingJump.start.has_value() ? "true" : "false"));
    GAMEPLAY_DEBUG_TRACE(
        "console_debug_map_load_travel map=\"" + selectedMap->map.fileName + "\""
        + " target=\"" + selectedMap->map.name + "\""
        + " map_id=" + std::to_string(selectedMap->map.id)
        + " scene_kind=" + sceneKind
        + " game_minutes=" + std::to_string(m_gameSession.gameMinutes())
        + " source=debug_console"
        + " start_override=" + (pendingJump.start.has_value() ? "true" : "false")
        + " pos="
        + (pendingJump.start.has_value()
            ? "(" + std::to_string(pendingJump.start->x)
                + "," + std::to_string(pendingJump.start->y)
                + "," + std::to_string(pendingJump.start->z) + ")"
            : std::string("none"))
        + " direction_degrees="
        + (debugStartDirectionDegrees.has_value()
            ? std::to_string(*debugStartDirectionDegrees)
            : std::string("none")));

    renderLoadingOverlayProgress(95);
    completeLoadingOverlay();
    synchronizeSessionFromRuntime();
    timingLogger.stage("debug map jump complete");
    m_debugConsole.addMessage(
        DebugConsole::MessageKind::Success,
        "Jumped to [" + upperSearchText(targetWorldId) + "] "
            + selectedMap->map.fileName + " - " + selectedMap->map.name);

    if (selectedMap->indoorMapData.has_value()
        && !selectedMap->indoorMapData->partyStartPoint.has_value()
        && !pendingJump.start.has_value())
    {
        m_debugConsole.addMessage(
            DebugConsole::MessageKind::Warning,
            "Indoor debug jump used the fallback start because this BLV has no Party Start marker.");
    }

    m_debugConsole.setEnabled(false);
    m_gameSession.requestRelativeMouseMotionReset();
    return true;
}

void GameApplication::handleSdlEvent(const SDL_Event &event)
{
    if (m_debugConsoleRendererInitialized)
    {
        ImGui_ImplSDL3_ProcessEvent(&event);
#if defined(__ANDROID__)
        const bool debugConsoleConsumedAndroidTouch =
            m_debugConsole.enabled() && submitAndroidFingerEventToImGui(event);
#else
        const bool debugConsoleConsumedAndroidTouch = false;
#endif

        if (m_settings.debugConsole
            && event.type == SDL_EVENT_KEY_DOWN
            && !event.key.repeat
            && (event.key.key == SDLK_GRAVE || event.key.scancode == SDL_SCANCODE_GRAVE))
        {
            m_debugConsole.toggleEnabled();
            m_gameSession.requestRelativeMouseMotionReset();
            return;
        }

        if (m_debugConsole.wantsGameplayInputBlocked())
        {
            const ImGuiIO &io = ImGui::GetIO();

            if (event.type == SDL_EVENT_TEXT_INPUT
                || event.type == SDL_EVENT_KEY_DOWN
                || event.type == SDL_EVENT_KEY_UP
                || event.type == SDL_EVENT_MOUSE_BUTTON_DOWN
                || event.type == SDL_EVENT_MOUSE_BUTTON_UP
                || event.type == SDL_EVENT_MOUSE_WHEEL
                || debugConsoleConsumedAndroidTouch
#if defined(__ANDROID__)
                || isAndroidFingerEvent(event)
#endif
                || io.WantCaptureKeyboard
                || io.WantCaptureMouse)
            {
                return;
            }
        }
    }

    if (handlePendingInputPromptSdlEvent(event))
    {
        return;
    }

    IScreen *pActiveScreen = m_screenManager.activeScreen();

    if (isGamepadSdlEvent(event))
    {
        m_gameInputSystem.handleSdlEvent(event);
        return;
    }

#if defined(__ANDROID__)
    const bool activeScreenHandlesTouchDirectly =
        pActiveScreen != nullptr
        && (dynamic_cast<CutsceneVideoScreen *>(pActiveScreen) != nullptr
            || dynamic_cast<WinGameScreen *>(pActiveScreen) != nullptr);

    if (activeScreenHandlesTouchDirectly && isAndroidFingerEvent(event))
    {
        pActiveScreen->handleSdlEvent(event);
        return;
    }

    m_gameInputSystem.handleSdlEvent(event);

    if (m_gameInputSystem.consumeMobileDebugConsoleToggleRequested())
    {
        if (m_settings.debugConsole && m_debugConsoleRendererInitialized)
        {
            m_debugConsole.toggleEnabled();
            m_gameSession.requestRelativeMouseMotionReset();
        }

        return;
    }
#endif

    if (pActiveScreen != nullptr)
    {
        pActiveScreen->handleSdlEvent(event);
    }
}

bool GameApplication::pendingInputPromptActive() const
{
    if (m_screenManager.activeScreen() != nullptr)
    {
        return false;
    }

    const IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();
    const EventRuntimeState *pRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;
    const EventDialogContent &activeDialog = m_gameSession.gameplayScreenRuntime().activeEventDialog();

    return activeDialog.isActive
        && pRuntimeState != nullptr
        && pRuntimeState->pendingInputPrompt
        && pRuntimeState->pendingInputPrompt->kind == EventRuntimeState::PendingInputPrompt::Kind::InputString;
}

bool GameApplication::applicationTextInputActive() const
{
    if (m_debugConsoleRendererInitialized && m_debugConsole.enabled() && ImGui::GetIO().WantTextInput)
    {
        return true;
    }

    const IScreen *pActiveScreen = m_screenManager.activeScreen();

    if (pActiveScreen != nullptr)
    {
        const NewGameScreen *pNewGameScreen = dynamic_cast<const NewGameScreen *>(pActiveScreen);
        return pNewGameScreen != nullptr && pNewGameScreen->textInputActive();
    }

    if (pendingInputPromptActive())
    {
        return true;
    }

    const GameplayScreenRuntime &gameplayScreenRuntime = m_gameSession.gameplayScreenRuntime();
    const GameplayUiController::SaveGameScreenState &saveGameScreen = gameplayScreenRuntime.saveGameScreenState();

    return (saveGameScreen.active && saveGameScreen.editActive)
        || gameplayScreenRuntime.houseBankState().inputActive();
}

bool GameApplication::handlePendingInputPromptSdlEvent(const SDL_Event &event)
{
    if (!pendingInputPromptActive())
    {
        return false;
    }

    if (event.type == SDL_EVENT_TEXT_INPUT)
    {
        if (event.text.text != nullptr && m_pendingInputText.size() < MaxPendingInputLength)
        {
            const size_t remaining = MaxPendingInputLength - m_pendingInputText.size();
            m_pendingInputText.append(event.text.text, std::min(remaining, std::strlen(event.text.text)));
            GAMEPLAY_DEBUG_TRACE(
                "input_prompt_text_input text=" + traceInputPromptQuoted(event.text.text)
                + " current=" + traceInputPromptQuoted(m_pendingInputText));
        }

        return true;
    }

    if (event.type != SDL_EVENT_KEY_DOWN)
    {
        return false;
    }

    if (event.key.repeat)
    {
        return true;
    }

    GAMEPLAY_DEBUG_TRACE(
        "input_prompt_key_down key=" + std::to_string(static_cast<int>(event.key.key))
        + " scancode=" + std::to_string(static_cast<int>(event.key.scancode)));

    switch (event.key.key)
    {
        case SDLK_RETURN:
        case SDLK_KP_ENTER:
            finishPendingInputPrompt(true);
            return true;

        case SDLK_ESCAPE:
            finishPendingInputPrompt(false);
            return true;

        case SDLK_BACKSPACE:
            if (!m_pendingInputText.empty())
            {
                m_pendingInputText.pop_back();
            }
            return true;

        default:
            return true;
    }
}

void GameApplication::clearPendingInputPromptUi(bool clearStatusBar)
{
#if !defined(__ANDROID__)
    if (m_pendingInputTextActive)
    {
        SDL_Window *pWindow = SDL_GetKeyboardFocus();

        if (pWindow != nullptr)
        {
            SDL_StopTextInput(pWindow);
        }
    }
#endif

    m_pendingInputTextActive = false;
    m_pendingInputText.clear();
    m_pendingInputStatusText.clear();

    if (clearStatusBar)
    {
        m_gameSession.gameplayScreenRuntime().setStatusBarEvent(" ", 0.01f);
    }
}

void GameApplication::updatePendingInputPrompt()
{
    {
        IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();
        EventRuntimeState *pRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

        if (pRuntimeState != nullptr
            && pRuntimeState->pendingInputPrompt
            && pRuntimeState->pendingDialogueContext
            && !m_gameSession.gameplayScreenRuntime().activeEventDialog().isActive)
        {
            m_gameSession.gameplayScreenRuntime().ensurePendingEventDialogPresented(true);
        }
    }

    if (!pendingInputPromptActive())
    {
        IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();
        EventRuntimeState *pRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;
        const EventDialogContent &activeDialog = m_gameSession.gameplayScreenRuntime().activeEventDialog();

        if (pRuntimeState != nullptr && pRuntimeState->pendingInputPrompt)
        {
            GAMEPLAY_DEBUG_TRACE(
                "input_prompt_not_active"
                + traceInputPromptFields(
                    *pRuntimeState->pendingInputPrompt,
                    pWorldRuntime != nullptr ? pWorldRuntime->mapName() : std::string(),
                    pWorldRuntime != nullptr ? pWorldRuntime->gameMinutes() : -1.0f)
                + " active_screen=" + (m_screenManager.activeScreen() != nullptr ? std::string("true") : std::string("false"))
                + " active_dialog=" + (activeDialog.isActive ? std::string("true") : std::string("false"))
                + " will_reset=" + (!activeDialog.isActive ? std::string("true") : std::string("false")));
        }

        if (pRuntimeState != nullptr && pRuntimeState->pendingInputPrompt
            && !activeDialog.isActive
            && !pRuntimeState->pendingDialogueContext)
        {
            pRuntimeState->pendingInputPrompt.reset();
        }

        clearPendingInputPromptUi(m_pendingInputTextActive || !m_pendingInputStatusText.empty());
        return;
    }

    if (!m_pendingInputTextActive)
    {
#if !defined(__ANDROID__)
        SDL_Window *pWindow = SDL_GetKeyboardFocus();

        if (pWindow != nullptr)
        {
            SDL_StartTextInput(pWindow);
        }
#endif

        m_pendingInputTextActive = true;

        IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();
        EventRuntimeState *pRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

        if (pWorldRuntime != nullptr && pRuntimeState != nullptr && pRuntimeState->pendingInputPrompt)
        {
            GAMEPLAY_DEBUG_TRACE(
                "input_prompt_opened"
                + traceInputPromptFields(
                    *pRuntimeState->pendingInputPrompt,
                    pWorldRuntime->mapName(),
                    pWorldRuntime->gameMinutes()));
        }
    }

    const std::string statusText = "Answer: " + m_pendingInputText + "_";

    if (statusText != m_pendingInputStatusText)
    {
        m_pendingInputStatusText = statusText;
        m_gameSession.gameplayScreenRuntime().setStatusBarEvent(statusText, 3600.0f);
    }
}

void GameApplication::finishPendingInputPrompt(bool accepted)
{
    IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();
    EventRuntimeState *pRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

    if (pWorldRuntime == nullptr || pRuntimeState == nullptr || !pRuntimeState->pendingInputPrompt)
    {
        clearPendingInputPromptUi(false);
        return;
    }

    const EventRuntimeState::PendingInputPrompt prompt = *pRuntimeState->pendingInputPrompt;
    pRuntimeState->pendingInputPrompt.reset();
    const std::string submittedInput = m_pendingInputText;
    const std::string promptMapName = pWorldRuntime->mapName();
    const float promptGameMinutes = pWorldRuntime->gameMinutes();

    clearPendingInputPromptUi(true);

    if (!accepted)
    {
        GAMEPLAY_DEBUG_TRACE(
            "input_prompt_canceled"
            + traceInputPromptFields(prompt, promptMapName, promptGameMinutes));
        m_skipGameplayUpdateUntilPromptSubmitKeysReleased = true;
        return;
    }

    const std::string normalizedInput = normalizePromptAnswer(submittedInput);

    bool matchedAnswer = false;
    size_t matchedAnswerIndex = 0;
    const std::vector<std::string> answers = resolvePendingInputAnswers(prompt);

    for (size_t answerIndex = 0; answerIndex < answers.size(); ++answerIndex)
    {
        const std::string &answer = answers[answerIndex];
        const std::string normalizedAnswer = normalizePromptAnswer(answer);

        if (!answer.empty() && normalizedAnswer == normalizedInput)
        {
            matchedAnswer = true;
            matchedAnswerIndex = answerIndex;
            break;
        }
    }

    uint8_t continueStep = prompt.continueStep;
    if (matchedAnswer)
    {
        if (matchedAnswerIndex < prompt.answerContinueSteps.size()
            && prompt.answerContinueSteps[matchedAnswerIndex] != 0)
        {
            continueStep = prompt.answerContinueSteps[matchedAnswerIndex];
        }
        else if (prompt.correctStep != 0)
        {
            continueStep = prompt.correctStep;
        }
    }
    const EventDialogContent previousDialog = m_gameSession.gameplayScreenRuntime().activeEventDialog();
    const bool promptStartedFromMapEvent =
        pRuntimeState->pendingDialogueContext
        && pRuntimeState->pendingDialogueContext->kind == DialogueContextKind::MapEvent;
    size_t previousMessageCount = 0;
    const bool executed = promptStartedFromMapEvent
        ? pWorldRuntime->executeMapEvent(prompt.eventId, previousMessageCount, continueStep)
        : pWorldRuntime->executeNpcTopicEvent(prompt.eventId, previousMessageCount, continueStep);

    GAMEPLAY_DEBUG_TRACE(
        "input_prompt_answered"
        + traceInputPromptFields(prompt, promptMapName, promptGameMinutes)
        + " answer=" + traceInputPromptQuoted(submittedInput)
        + " matched=" + (matchedAnswer ? "true" : "false")
        + " matched_index=" + (matchedAnswer ? std::to_string(matchedAnswerIndex) : std::string("none"))
        + " selected_continue_step=" + std::to_string(continueStep)
        + " executed=" + (executed ? "true" : "false")
        + " source_kind=" + (promptStartedFromMapEvent ? std::string("map_event") : std::string("npc_topic")));

    if (executed && promptStartedFromMapEvent)
    {
        previousMessageCount = 0;
    }

    if (executed && !pRuntimeState->pendingDialogueContext && previousDialog.isActive && previousDialog.sourceId != 0)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = previousDialog.isHouseDialog ? DialogueContextKind::HouseService : DialogueContextKind::NpcTalk;
        context.sourceId = previousDialog.sourceId;
        context.hostHouseId = pRuntimeState->dialogueState.hostHouseId;

        if (context.kind == DialogueContextKind::HouseService && context.hostHouseId == 0)
        {
            context.hostHouseId = context.sourceId;
        }

        pRuntimeState->pendingDialogueContext = std::move(context);
    }

    if (executed)
    {
        GameplayHeldItemController::applyGrantedEventItemsToHeldInventory(
            m_gameSession.gameplayScreenRuntime(),
            *pRuntimeState,
            m_gameSession.data().itemTable());
    }

    if (executed
        && pRuntimeState->pendingDialogueContext
        && pRuntimeState->pendingDialogueContext->kind == DialogueContextKind::MapEvent
        && pRuntimeState->messages.size() <= previousMessageCount
        && !pRuntimeState->pendingInputPrompt)
    {
        pRuntimeState->pendingDialogueContext.reset();
    }

    if (executed && !pRuntimeState->pendingDialogueContext)
    {
        m_gameSession.gameplayScreenRuntime().activeEventDialog() = {};
    }

    m_skipGameplayUpdateUntilPromptSubmitKeysReleased = true;

    if (executed)
    {
        presentPendingInputPromptDialogResult(previousMessageCount);
    }
}

void GameApplication::presentPendingInputPromptDialogResult(size_t previousMessageCount)
{
    IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();
    EventRuntimeState *pRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

    if (pWorldRuntime == nullptr || pRuntimeState == nullptr || !pRuntimeState->pendingDialogueContext)
    {
        return;
    }

    const MapStatsEntry *pCurrentMap =
        m_gameDataLoader.getMapStats().findByFileName(m_gameSession.currentMapFileName());

    m_gameSession.gameplayScreenRuntime().activeEventDialog() = buildEventDialogContent(
        *pRuntimeState,
        previousMessageCount,
        true,
        pWorldRuntime->globalEventProgram(),
        &m_gameDataLoader.getHouseTable(),
        &m_gameDataLoader.getClassSkillTable(),
        &m_gameDataLoader.getNpcDialogTable(),
        &m_gameDataLoader.getTransitionTable(),
        pCurrentMap,
        &m_gameDataLoader.getMapStats().getEntries(),
        pWorldRuntime->party(),
        pWorldRuntime,
        pWorldRuntime->gameMinutes(),
        &m_gameDataLoader.getMergedNpcProfessionTable(),
        &m_gameDataLoader.getMergedNewsProfessionTopicTable(),
        &m_gameDataLoader.getMergedNpcBtbTable(),
        nullptr,
        &m_gameDataLoader.getMergedContinentSettingTable());

}

std::vector<std::string> GameApplication::resolvePendingInputAnswers(
    const EventRuntimeState::PendingInputPrompt &prompt) const
{
    return prompt.answers;
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

#if defined(__ANDROID__)
    if (migrateLegacyAndroidSettings(m_settings))
    {
        m_config.activeWorldId = m_settings.startWorldId;
        std::cout << "GameApplication: migrated legacy settings to Android profile version "
                  << m_settings.settingsProfileVersion << '\n';
    }
#endif

    m_settings.startWorldId = normalizeWorldId(m_config.activeWorldId);

    if (!saveGameSettings(path, m_settings, error))
    {
        std::cerr << "GameApplication: failed to write " << path.string() << ": " << error << '\n';
    }

    if (m_config.loadUniqueActorIndex.has_value())
    {
        m_settings.indoorPathfinding = true;
        m_settings.logIndoorPathfinding = true;
    }

    m_config.windowWidth = m_settings.resolutionWidth;
    m_config.windowHeight = m_settings.resolutionHeight;
    m_config.windowMode = engineWindowModeForSettings(m_settings.windowMode);
    m_config.verticalSync = m_settings.verticalSync;
    m_config.fpsTrace = m_settings.fpsTrace;
    m_config.performanceTrace = m_settings.performanceTrace;
    m_engineApplication.setConfiguration(m_config);
    configureGameplayDebugTrace(m_settings.gameplayTrace, m_settings.gameplayTraceFile, m_settings.gameplayTraceAppend);
    configureGameplayCombatTrace(m_settings.combatTrace, m_settings.combatTraceFile, m_settings.combatTraceAppend);
}

void GameApplication::applyCurrentSettingsToActiveRuntime()
{
    configureGameplayDebugTrace(m_settings.gameplayTrace, m_settings.gameplayTraceFile, m_settings.gameplayTraceAppend);
    configureGameplayCombatTrace(m_settings.combatTrace, m_settings.combatTraceFile, m_settings.combatTraceAppend);
    setTextureFilteringConfig(textureFilteringConfigFromSettings(m_settings));
    m_gameAudioSystem.setSoundVolume(normalizedVolumeLevel(m_settings.soundVolume));
    m_gameAudioSystem.setMusicVolume(normalizedVolumeLevel(m_settings.musicVolume));
    m_gameAudioSystem.setVoiceVolume(normalizedVolumeLevel(m_settings.voiceVolume));
    m_outdoorGameView.setMouseRotateSpeed(mouseRotateSpeedForTurnRate(m_settings.turnRate));
    m_outdoorGameView.setWalkSoundEnabled(m_settings.walksound);
    m_outdoorGameView.setShowHitStatusMessages(m_settings.showHits);
    m_outdoorGameView.setFlipOnExitEnabled(m_settings.flipOnExit);
    m_outdoorGameView.setSettingsSnapshot(m_settings);
    m_indoorGameView.setSettingsSnapshot(m_settings);

    if (m_pOutdoorWorldRuntime != nullptr)
    {
        m_pOutdoorWorldRuntime->setBolsterMonstersEnabled(m_settings.bolsterMonsters);
        m_pOutdoorWorldRuntime->setOutdoorPathfindingSettings(
            m_settings.outdoorPathfinding,
            m_settings.logOutdoorPathfinding);
    }

    if (m_pOutdoorPartyRuntime != nullptr)
    {
        m_pOutdoorPartyRuntime->setRunning(m_settings.alwaysRun);
        m_pOutdoorPartyRuntime->setDebugFlyingOverride(m_settings.startFlying);
        m_pOutdoorPartyRuntime->setMovementSpeedMultiplier(m_settings.movementSpeedMultiplier);
        m_pOutdoorPartyRuntime->setCollisionTraceEnabled(
            m_settings.collisionTrace,
            m_gameSession.currentMapFileName());
    }

    if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
    {
        IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
        pIndoorRuntime->worldRuntime().setBolsterMonstersEnabled(m_settings.bolsterMonsters);
        pIndoorRuntime->partyRuntime().setAlwaysRunEnabled(m_settings.alwaysRun);
        pIndoorRuntime->partyRuntime().setMovementSpeedMultiplier(m_settings.movementSpeedMultiplier);
        pIndoorRuntime->partyRuntime().setCollisionTraceEnabled(
            m_settings.collisionTrace,
            pIndoorRuntime->currentMapFileName());
    }

    if (m_pMapSceneRuntime != nullptr)
    {
        m_pMapSceneRuntime->party().setDebugDamageImmune(m_settings.immortal);
        m_pMapSceneRuntime->party().setDebugUnlimitedMana(m_settings.unlimitedMana);
    }
}

void GameApplication::applyStartupDebugSettingsToActiveRuntime()
{
    if (m_pMapSceneRuntime == nullptr)
    {
        return;
    }

    if (m_settings.overrideStartPosition)
    {
        if (m_pMapSceneRuntime->kind() == SceneKind::Outdoor && m_pOutdoorPartyRuntime != nullptr)
        {
            m_pOutdoorPartyRuntime->teleportTo(m_settings.startX, m_settings.startY, m_settings.startZ);
        }
        else if (m_pMapSceneRuntime->kind() == SceneKind::Indoor)
        {
            IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
            pIndoorRuntime->partyRuntime().teleportPartyPosition(m_settings.startX, m_settings.startY, m_settings.startZ);
        }
    }

}

void GameApplication::shutdownApplication()
{
    m_screenManager.setActiveScreen(nullptr);
    m_pLoadingOverlayScreen.reset();
    m_gameSession.gameplayScreenRuntime().clearSharedUiRuntime();
    shutdownRenderer();
    shutdownDebugConsoleRenderer();
    m_gameAudioSystem.shutdown();
}

bool GameApplication::loadGameData(Engine::AssetFileSystem &assetFileSystem)
{
    m_pAssetFileSystem = &assetFileSystem;
    m_gameSession.clear();
    m_gameDataRepository.clear();
    m_gameSession.bindDataRepository(&m_gameDataRepository);
    m_gameplayController.bindSession(m_gameSession);
    m_gameplayController.clearRuntime();
    m_screenManager.setActiveScreen(nullptr);

    std::string manifestError;
    m_activeWorldManifest = loadActiveWorldManifestOrDefault(
        assetFileSystem,
        m_config.activeWorldId,
        manifestError);

    if (!manifestError.empty())
    {
        std::cerr << manifestError << '\n';
        return false;
    }

    if (m_activeWorldManifest.id != normalizeWorldId(m_config.activeWorldId))
    {
        std::cerr
            << "world.yml id '" << m_activeWorldManifest.id
            << "' does not match active world '" << normalizeWorldId(m_config.activeWorldId) << "'\n";
        return false;
    }

    m_gameDataLoader.setActiveWorldId(m_activeWorldManifest.id);
    m_gameDataLoader.setInitialMapFileName(m_activeWorldManifest.start.mapFileName);

    loadOrCreateSettings();

    if (!m_gameAudioSystem.initializeMenuAudio(assetFileSystem))
    {
        return false;
    }

    applyCurrentSettingsToActiveRuntime();
    m_screenManager.setCurrentMode(AppMode::MainMenu);
    m_bootSeededDwiOnNextRendererInit = !m_settings.startInMainMenu;
    m_commonGameDataLoaded = false;
    m_commonGameDataLoadFailed = false;
    m_deferredCommonGameDataLoadPending = m_settings.startInMainMenu;
    m_mainMenuRenderedFrameCount = 0;
    m_deferredMainMenuChildWarmupStage = 0;

    return true;
}

bool GameApplication::ensureCommonGameDataLoaded()
{
    if (m_commonGameDataLoaded)
    {
        return true;
    }

    if (m_commonGameDataLoadFailed || m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    m_gameDataLoader.setActiveWorldId(m_activeWorldManifest.id);
    m_gameDataLoader.setInitialMapFileName(m_activeWorldManifest.start.mapFileName);

    if (!m_gameDataLoader.loadCommonForGameplay(*m_pAssetFileSystem))
    {
        m_commonGameDataLoadFailed = true;
        std::cerr << "GameApplication: failed to load common gameplay data\n";
        return false;
    }

    m_gameDataRepository.bind(m_gameDataLoader);
    m_gameSession.bindDataRepository(&m_gameDataRepository);
    m_gameAudioSystem.bindGameplayTables(
        m_gameDataLoader.getCharacterDollTable(),
        m_gameDataLoader.getMergedCharacterVoiceTable());

    if (gameplayDebugTraceEnabled() && !m_traceSessionHeaderLogged)
    {
        m_traceSessionHeaderLogged = true;
        GAMEPLAY_DEBUG_TRACE(
            "trace_session_begin"
            " world_id=\"" + m_activeWorldManifest.id + "\""
            + " configured_world_id=\"" + m_config.activeWorldId + "\""
            + " startup_map=\"" + resolveStartupMapFile() + "\""
            + " trace_file=\"" + traceEnvironmentValue("OPENYAMM_GAMEPLAY_TRACE_FILE") + "\""
            + " unix_time=" + std::to_string(static_cast<int64_t>(std::time(nullptr)))
            + " map_load_timing=" + (mapLoadTimingEnabled() ? "true" : "false")
            + " route_trace=" + (traceEnvironmentValue("OPENYAMM_ROUTE_TRACE").empty() ? "false" : "true")
            + " gameplay_trace="
            + (traceEnvironmentValue("OPENYAMM_GAMEPLAY_TRACE").empty() ? "false" : "true"));
    }

    applyCurrentSettingsToActiveRuntime();
    m_commonGameDataLoaded = true;
    m_deferredCommonGameDataLoadPending = false;
    updateDebugConsoleDataOptions();
    return true;
}

void GameApplication::updateDeferredStartupLoads()
{
    if (!m_deferredCommonGameDataLoadPending || m_commonGameDataLoaded || m_commonGameDataLoadFailed)
    {
        updateDeferredMainMenuChildWarmup();
        return;
    }

    if (m_screenManager.currentMode() == AppMode::MainMenu && m_mainMenuRenderedFrameCount == 0)
    {
        return;
    }

    (void)ensureCommonGameDataLoaded();
}

void GameApplication::updateDeferredMainMenuChildWarmup()
{
    if (m_mainMenuChildScreensPrepared
        || m_deferredMainMenuChildWarmupStage == 0
        || m_screenManager.currentMode() != AppMode::MainMenu
        || m_mainMenuRenderedFrameCount == 0
        || !m_commonGameDataLoaded
        || m_pAssetFileSystem == nullptr)
    {
        return;
    }

    if (m_deferredMainMenuChildWarmupStage == 1)
    {
        NewGameScreen warmupScreen(
            *m_pAssetFileSystem,
            &m_gameAudioSystem,
            m_gameSession.data(),
            m_settings.newGameGodLich,
            IncludeGodLichCharacterCreationCandidate,
            m_settings.allowIncompleteCharacterCreation,
            [](const std::vector<Character> &, uint32_t, bool)
            {
            },
            []()
            {
            });
        warmupScreen.prepareForFirstFrame();
        m_deferredMainMenuChildWarmupStage = 2;
        return;
    }

    if (m_deferredMainMenuChildWarmupStage == 2)
    {
        LoadGameScreen warmupScreen(
            *m_pAssetFileSystem,
            m_gameSession.data(),
            [](const std::filesystem::path &) -> bool
            {
                return false;
            },
            []()
            {
            });
        warmupScreen.prepareForFirstFrame();
        m_mainMenuChildScreensPrepared = true;
        m_deferredMainMenuChildWarmupStage = 0;
    }
}

bool GameApplication::activateWorldForMap(const MapStatsEntry &map)
{
    if (m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    const std::string targetWorldId = normalizeWorldId(map.worldId);
    const std::string currentWorldId = normalizeWorldId(m_pAssetFileSystem->getActiveWorldId());

    if (currentWorldId != targetWorldId)
    {
        if (!m_pAssetFileSystem->switchActiveWorld(targetWorldId))
        {
            std::cerr
                << "GameApplication: failed to switch active world from "
                << currentWorldId
                << " to "
                << targetWorldId
                << " for map "
                << map.fileName
                << '\n';
            return false;
        }

        m_gameSession.gameplayScreenRuntime().clearSharedUiRuntime();
    }

    std::string manifestError;
    WorldManifest targetManifest = loadActiveWorldManifestOrDefault(*m_pAssetFileSystem, targetWorldId, manifestError);

    if (!manifestError.empty())
    {
        std::cerr << manifestError << '\n';
        return false;
    }

    if (targetManifest.id != targetWorldId)
    {
        std::cerr
            << "world.yml id '" << targetManifest.id
            << "' does not match active world '" << targetWorldId << "'\n";
        return false;
    }

    m_config.activeWorldId = targetWorldId;
    m_activeWorldManifest = std::move(targetManifest);
    m_gameDataLoader.setActiveWorldId(targetWorldId);
    m_gameDataLoader.setInitialMapFileName(m_activeWorldManifest.start.mapFileName);
    return true;
}

bool GameApplication::activateWorldForMapFileName(const std::string &mapFileName)
{
    const MapStatsEntry *pMap = m_gameDataLoader.getMapStats().findByFileName(mapFileName);

    if (pMap == nullptr)
    {
        std::cerr
            << "GameApplication: cannot resolve map world for "
            << mapFileName
            << '\n';
        return false;
    }

    return activateWorldForMap(*pMap);
}

bool GameApplication::initializeRenderer()
{
    shutdownRenderer();

    if (!initializeDebugConsoleRenderer())
    {
        std::cerr << "GameApplication: debug console renderer initialization failed\n";
        return false;
    }

    if (m_bootSeededDwiOnNextRendererInit)
    {
        const bool initialized = initializeStartupSession(true);

        if (!initialized)
        {
            std::cerr << "GameApplication: initializeRenderer failed during startup session initialization\n";
        }

        return initialized;
    }

    if (m_screenManager.currentMode() == AppMode::MainMenu
        || m_screenManager.currentMode() == AppMode::LoadMenu
        || m_screenManager.currentMode() == AppMode::NewGame)
    {
        openMainMenuScreen();
        return true;
    }

    const bool initialized = initializeSelectedMapRuntime(true);

    if (!initialized)
    {
        std::cerr << "GameApplication: initializeRenderer failed to initialize selected map runtime\n";
    }

    return initialized;
}

bool GameApplication::initializeStartupSession(bool initializeView)
{
    if (!m_bootSeededDwiOnNextRendererInit)
    {
        std::cerr << "GameApplication: initializeStartupSession called without boot flag\n";
        return false;
    }

    m_bootSeededDwiOnNextRendererInit = false;

    if (!ensureCommonGameDataLoaded())
    {
        std::cerr << "GameApplication: initializeStartupSession failed to load common gameplay data\n";
        return false;
    }

    const bool initialized = startNewSession(std::nullopt, initializeView);

    if (!initialized)
    {
        std::cerr << "GameApplication: initializeStartupSession failed to start a new session\n";
    }

    return initialized;
}

bool GameApplication::initializeSelectedMapRuntime(bool initializeView)
{
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap)
    {
        std::cerr << "GameApplication: initializeSelectedMapRuntime has no selected map\n";
        return false;
    }

    MapLoadTimingLogger timingLogger(selectedMap->map.fileName, "selected_map_runtime");
    const WorldActorAwarenessDefinition &actorAwareness = m_activeWorldManifest.actorAwareness;
    m_gameSession.gameplayActorService().setPartyEngagementRange(
        actorAwareness.declared
            ? actorAwareness.partyEngagementRange
            : GameplayActorService::MaximumPartyEngagementRange);

    if (selectedMap->outdoorMapData)
    {
        const WorldPartyMovementDefinition &partyMovement = m_activeWorldManifest.partyMovement;
        const float partyEyeHeight = partyMovement.declared
            ? partyMovement.eyeHeight
            : DefaultOutdoorPartyEyeHeight;
        const float partyCollisionRadius = partyMovement.declared
            ? partyMovement.collisionRadius
            : DefaultOutdoorPartyCollisionRadius;
        const float partyCollisionHeight = partyMovement.declared
            ? partyMovement.collisionHeight
            : DefaultOutdoorPartyCollisionHeight;
        const float partyMaxStepHeight = partyMovement.declared
            ? partyMovement.maxStepHeight
            : DefaultOutdoorPartyMaxStepHeight;

        m_gameSession.setCurrentSceneKind(SceneKind::Outdoor);
        m_gameSession.setCurrentMapFileName(selectedMap->map.fileName);
        m_outdoorGameView.setCameraEyeHeight(partyEyeHeight);
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
        m_pOutdoorPartyRuntime->setBodyDimensions(
            partyCollisionRadius,
            partyCollisionHeight,
            partyMaxStepHeight);
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

        const int32_t currentMapDay = currentLocationDay(m_gameSession.gameMinutes());
        const OutdoorWorldRuntime::Snapshot *pSavedOutdoorState =
            findSavedOutdoorWorldState(m_gameSession, *selectedMap);
        const bool outdoorTimedRespawn =
            pSavedOutdoorState != nullptr
                && timedMapRespawnDue(selectedMap->map, pSavedOutdoorState->locationInfo, currentMapDay);
        const bool restoreSavedOutdoorState = pSavedOutdoorState != nullptr && !outdoorTimedRespawn;
        const int32_t previousOutdoorProcessedRespawnCount =
            pSavedOutdoorState != nullptr ? pSavedOutdoorState->locationInfo.respawnCount : 0;
        MapDeltaLocationInfo outdoorLocationInfo =
            pSavedOutdoorState != nullptr
                ? pSavedOutdoorState->locationInfo
                : (selectedMap->outdoorMapDeltaData
                    ? selectedMap->outdoorMapDeltaData->locationInfo
                    : MapDeltaLocationInfo{});

        if (outdoorTimedRespawn)
        {
            outdoorLocationInfo.respawnCount++;
        }
        outdoorLocationInfo.lastRespawnDay = currentMapDay;

        std::optional<MapDeltaData> *pOutdoorMapDeltaData =
            const_cast<std::optional<MapDeltaData> *>(&selectedMap->outdoorMapDeltaData);
        if (pOutdoorMapDeltaData != nullptr && pOutdoorMapDeltaData->has_value() && !restoreSavedOutdoorState)
        {
            (*pOutdoorMapDeltaData)->locationInfo = outdoorLocationInfo;
            (*pOutdoorMapDeltaData)->locationInfo.lastRespawnDay = 0;
        }

        m_pOutdoorWorldRuntime = std::make_unique<OutdoorWorldRuntime>();
        m_pOutdoorWorldRuntime->setPartyCollisionDimensions(partyCollisionRadius, partyCollisionHeight);
        m_pOutdoorWorldRuntime->setBolsterMonstersEnabled(m_settings.bolsterMonsters);
        m_pOutdoorWorldRuntime->initialize(
            selectedMap->map,
            m_gameDataLoader.getMonsterTable(),
            m_gameDataLoader.getMonsterProjectileTable(),
            m_gameDataLoader.getObjectTable(),
            m_gameDataLoader.getSpellTable(),
            m_gameDataLoader.getItemTable(),
            &m_pOutdoorPartyRuntime->party(),
            m_pOutdoorPartyRuntime.get(),
            m_gameDataLoader.getStandardItemEnchantTable(),
            m_gameDataLoader.getSpecialItemEnchantTable(),
            &m_gameDataLoader.getChestTable(),
            selectedMap->outdoorMapData,
            selectedMap->outdoorMapDeltaData,
            selectedMap->outdoorWeatherProfile,
            selectedMap->eventRuntimeState,
            selectedMap->outdoorActorPreviewBillboardSet,
            selectedMap->outdoorLandMask,
            selectedMap->outdoorDecorationCollisionSet,
            selectedMap->outdoorActorCollisionSet,
            selectedMap->outdoorSpriteObjectCollisionSet,
            selectedMap->outdoorSpriteObjectBillboardSet,
            &m_gameSession.gameplayActorService(),
            &m_gameSession.gameplayProjectileService(),
            &m_gameSession.gameplayCombatController(),
            &m_gameSession.gameplayFxService(),
            &m_gameDataLoader.getMergedBolsterMapTable(),
            &m_gameDataLoader.getMergedBolsterMonsterTable(),
            selectedMap->itemSourceData ? &*selectedMap->itemSourceData : nullptr
        );
        timingLogger.stage("outdoor runtime initialized");

        if (restoreSavedOutdoorState)
        {
            m_pOutdoorWorldRuntime->restoreSnapshot(*pSavedOutdoorState);
        }
        OutdoorWorldRuntime::Snapshot outdoorTimeSnapshot = m_pOutdoorWorldRuntime->snapshot();
        outdoorTimeSnapshot.gameMinutes = m_gameSession.gameMinutes();
        if (!restoreSavedOutdoorState || outdoorTimeSnapshot.locationInfo.lastRespawnDay <= 0)
        {
            outdoorTimeSnapshot.locationInfo = outdoorLocationInfo;
        }
        if (outdoorTimedRespawn && pSavedOutdoorState != nullptr)
        {
            outdoorTimeSnapshot.locationTime = pSavedOutdoorState->locationTime;
            outdoorTimeSnapshot.hasLocationTime = pSavedOutdoorState->hasLocationTime;
            outdoorTimeSnapshot.fullyRevealedCells = pSavedOutdoorState->fullyRevealedCells;
            outdoorTimeSnapshot.partiallyRevealedCells = pSavedOutdoorState->partiallyRevealedCells;
            if (outdoorTimeSnapshot.eventRuntimeState)
            {
                outdoorTimeSnapshot.eventRuntimeState->processedMapRespawnCount =
                    previousOutdoorProcessedRespawnCount;
            }
        }
        m_pOutdoorWorldRuntime->restoreSnapshot(outdoorTimeSnapshot);
        if (!m_loadingSavedGameRuntime)
        {
            m_pOutdoorWorldRuntime->applyMapReentryReset();
        }
        applyPartyReputationToWorld(
            m_pOutdoorPartyRuntime->party(),
            *m_pOutdoorWorldRuntime,
            selectedMap->map,
            m_gameDataLoader.getMergedContinentSettingTable());
        m_pOutdoorWorldRuntime->prepareTimers(
            selectedMap->localEventProgram,
            selectedMap->globalEventProgram);

        if (EventRuntimeState *pEventRuntimeState = m_pOutdoorWorldRuntime->eventRuntimeState())
        {
            m_gameSession.applyNamedGlobalVarsToRuntime(*pEventRuntimeState);

            EventRuntime eventRuntime(&m_gameDataLoader.getHouseTable(), &m_gameDataLoader.getNpcDialogTable());

            eventRuntime.executeOnLoadEvents(
                selectedMap->localEventProgram,
                selectedMap->globalEventProgram,
                *pEventRuntimeState,
                &m_pOutdoorPartyRuntime->party(),
                m_pOutdoorWorldRuntime.get());
            eventRuntime.executeMapRefillHooks(
                selectedMap->localEventProgram,
                selectedMap->globalEventProgram,
                selectedMap->outdoorMapDeltaData,
                *pEventRuntimeState,
                &m_pOutdoorPartyRuntime->party(),
                m_pOutdoorWorldRuntime.get());
            m_pOutdoorWorldRuntime->applyEventRuntimeState(true);
            m_pOutdoorPartyRuntime->applyEventRuntimeState(*pEventRuntimeState, false);
        }

        if (m_config.loadUniqueActorIndex.has_value()
            && !filterOutdoorRuntimeToUniqueActor(
                *m_pOutdoorWorldRuntime,
                *m_config.loadUniqueActorIndex,
                selectedMap->map.fileName))
        {
            return false;
        }
        timingLogger.stage("outdoor on-load events applied");

        preloadMapGameplaySounds(
            m_gameAudioSystem,
            m_gameDataLoader.getMonsterTable(),
            m_gameDataLoader.getSpellTable(),
            *selectedMap);
        timingLogger.stage("outdoor gameplay sounds preloaded");

        m_pMapSceneRuntime = std::make_unique<OutdoorSceneRuntime>(
            selectedMap->map.fileName,
            selectedMap->map,
            *m_pOutdoorPartyRuntime,
            *m_pOutdoorWorldRuntime,
            selectedMap->localEventProgram,
            selectedMap->globalEventProgram,
            &m_gameDataLoader.getHouseTable(),
            &m_gameDataLoader.getNpcDialogTable(),
            &m_gameDataLoader.getMm9MapTransitionTable(),
            &m_gameDataLoader.getMm9TeacherScheduleTable());
        timingLogger.stage("outdoor scene runtime created");
        m_gameplayController.bindRuntime(m_pMapSceneRuntime.get());
        timingLogger.stage("outdoor gameplay runtime bound");
        m_screenManager.setCurrentMode(AppMode::GameplayOutdoor);
        timingLogger.stage("outdoor app mode set");

        m_gameAudioSystem.setBackgroundMusicTrack(selectedMap->map.redbookTrack);
        timingLogger.stage("outdoor background music set");
        applyCurrentSettingsToActiveRuntime();
        timingLogger.stage("outdoor settings applied");

        if (!initializeView)
        {
            releaseUnusedHeapPages();
            return true;
        }

        const bool initialized = m_outdoorGameView.initialize(
            *m_pAssetFileSystem,
            selectedMap->map,
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
            &m_gameAudioSystem,
            *static_cast<OutdoorSceneRuntime *>(m_pMapSceneRuntime.get()),
                m_settings);
        timingLogger.stage("outdoor view initialized");

        if (!initialized)
        {
            std::cerr
                << "GameApplication: outdoor view initialization failed for map "
                << selectedMap->map.fileName
                << '\n';
        }

        if (initialized && bgfx::getRendererType() != bgfx::RendererType::Noop)
        {
            m_gameDataLoader.releaseSelectedMapRenderSourcePixels();
        }

        if (initialized)
        {
            releaseUnusedHeapPages();
        }

        return initialized;
    }

    if (selectedMap->indoorMapData)
    {
        m_gameSession.setCurrentSceneKind(SceneKind::Indoor);
        m_gameSession.setCurrentMapFileName(selectedMap->map.fileName);
        m_screenManager.setCurrentMode(AppMode::GameplayIndoor);
        m_gameAudioSystem.setBackgroundMusicTrack(selectedMap->map.redbookTrack);
        applyCurrentSettingsToActiveRuntime();
        Party &party = ensureSessionPartyState();
        const SpriteFrameTable *pIndoorActorSpriteFrameTable =
            selectedMap->indoorActorPreviewBillboardSet
                ? &selectedMap->indoorActorPreviewBillboardSet->spriteFrameTable
                : nullptr;
        const SpriteFrameTable *pIndoorProjectileSpriteFrameTable =
            selectedMap->indoorSpriteObjectBillboardSet
                ? &selectedMap->indoorSpriteObjectBillboardSet->spriteFrameTable
                : pIndoorActorSpriteFrameTable;
        const int32_t currentMapDay = currentLocationDay(m_gameSession.gameMinutes());
        const IndoorSceneRuntime::Snapshot *pSavedIndoorState =
            findSavedIndoorSceneState(m_gameSession, *selectedMap);
        const bool indoorTimedRespawn =
            pSavedIndoorState != nullptr
            && pSavedIndoorState->mapDeltaData
            && timedMapRespawnDue(
                selectedMap->map,
                pSavedIndoorState->mapDeltaData->locationInfo,
                currentMapDay);
        const bool restoreSavedIndoorState = pSavedIndoorState != nullptr && !indoorTimedRespawn;
        const int32_t previousIndoorProcessedRespawnCount =
            pSavedIndoorState != nullptr
                && pSavedIndoorState->mapDeltaData
                    ? pSavedIndoorState->mapDeltaData->locationInfo.respawnCount
                    : 0;
        MapDeltaLocationInfo indoorLocationInfo =
            pSavedIndoorState != nullptr && pSavedIndoorState->mapDeltaData
                ? pSavedIndoorState->mapDeltaData->locationInfo
                : (selectedMap->indoorMapDeltaData
                    ? selectedMap->indoorMapDeltaData->locationInfo
                    : MapDeltaLocationInfo{});

        if (indoorTimedRespawn)
        {
            indoorLocationInfo.respawnCount++;
        }
        indoorLocationInfo.lastRespawnDay = currentMapDay;

        std::optional<MapDeltaData> indoorMapDeltaDataForRuntime = selectedMap->indoorMapDeltaData;
        if (indoorMapDeltaDataForRuntime && !restoreSavedIndoorState)
        {
            indoorMapDeltaDataForRuntime->locationInfo = indoorLocationInfo;
            indoorMapDeltaDataForRuntime->locationInfo.lastRespawnDay = 0;
            if (pSavedIndoorState != nullptr && pSavedIndoorState->mapDeltaData)
            {
                indoorMapDeltaDataForRuntime->locationTime = pSavedIndoorState->mapDeltaData->locationTime;
            }
        }

        std::unique_ptr<IndoorSceneRuntime> pIndoorSceneRuntime = std::make_unique<IndoorSceneRuntime>(
            selectedMap->map.fileName,
            selectedMap->map,
            *selectedMap->indoorMapData,
            m_gameDataLoader.getMonsterTable(),
            m_gameDataLoader.getMonsterProjectileTable(),
            m_gameDataLoader.getObjectTable(),
            m_gameDataLoader.getSpellTable(),
            m_gameDataLoader.getItemTable(),
            m_gameDataLoader.getChestTable(),
            party,
            indoorMapDeltaDataForRuntime,
            selectedMap->eventRuntimeState,
            selectedMap->localEventProgram,
            selectedMap->globalEventProgram,
            &m_gameSession.gameplayActorService(),
            &m_gameSession.gameplayProjectileService(),
            &m_gameSession.gameplayCombatController(),
            pIndoorActorSpriteFrameTable,
            pIndoorProjectileSpriteFrameTable,
            selectedMap->indoorDecorationBillboardSet ? &*selectedMap->indoorDecorationBillboardSet : nullptr,
            &m_gameDataLoader.getMergedBolsterMapTable(),
            &m_gameDataLoader.getMergedBolsterMonsterTable(),
            m_settings.bolsterMonsters,
            &m_gameDataLoader.getNpcDialogTable(),
            selectedMap->itemSourceData ? &*selectedMap->itemSourceData : nullptr,
            &m_gameDataLoader.getMm9MapTransitionTable(),
            &m_gameDataLoader.getMm9TeacherScheduleTable()
        );
        timingLogger.stage("indoor runtime initialized");

        if (restoreSavedIndoorState && pSavedIndoorState != nullptr)
        {
            pIndoorSceneRuntime->restoreSnapshot(*pSavedIndoorState);
        }

        IndoorSceneRuntime::Snapshot indoorTimeSnapshot = pIndoorSceneRuntime->snapshot();
        indoorTimeSnapshot.worldRuntime.gameMinutes = m_gameSession.gameMinutes();
        if (indoorTimeSnapshot.mapDeltaData
            && (!restoreSavedIndoorState || indoorTimeSnapshot.mapDeltaData->locationInfo.lastRespawnDay <= 0))
        {
            indoorTimeSnapshot.mapDeltaData->locationInfo = indoorLocationInfo;
        }
        if (indoorTimedRespawn && pSavedIndoorState != nullptr && pSavedIndoorState->mapDeltaData)
        {
            if (indoorTimeSnapshot.mapDeltaData)
            {
                indoorTimeSnapshot.mapDeltaData->visibleOutlines = pSavedIndoorState->mapDeltaData->visibleOutlines;
            }
            if (indoorTimeSnapshot.eventRuntimeState)
            {
                indoorTimeSnapshot.eventRuntimeState->processedMapRespawnCount =
                    previousIndoorProcessedRespawnCount;
            }
        }
        pIndoorSceneRuntime->restoreSnapshot(indoorTimeSnapshot);
        if (!m_loadingSavedGameRuntime)
        {
            pIndoorSceneRuntime->applyMapReentryReset();
        }
        applyPartyReputationToWorld(
            pIndoorSceneRuntime->party(),
            pIndoorSceneRuntime->worldRuntime(),
            selectedMap->map,
            m_gameDataLoader.getMergedContinentSettingTable());
        pIndoorSceneRuntime->prepareTimers();

        timingLogger.stage("indoor saved state restored");

        if (EventRuntimeState *pEventRuntimeState = pIndoorSceneRuntime->eventRuntimeState())
        {
            m_gameSession.applyNamedGlobalVarsToRuntime(*pEventRuntimeState);

            EventRuntime eventRuntime(&m_gameDataLoader.getHouseTable(), &m_gameDataLoader.getNpcDialogTable());
            eventRuntime.executeOnLoadEvents(
                selectedMap->localEventProgram,
                selectedMap->globalEventProgram,
                *pEventRuntimeState,
                &pIndoorSceneRuntime->party(),
                pIndoorSceneRuntime->sceneEventContext());
            eventRuntime.executeMapRefillHooks(
                selectedMap->localEventProgram,
                selectedMap->globalEventProgram,
                pIndoorSceneRuntime->mapDeltaData(),
                *pEventRuntimeState,
                &pIndoorSceneRuntime->party(),
                pIndoorSceneRuntime->sceneEventContext());
            pIndoorSceneRuntime->worldRuntime().applyEventRuntimeState(true);
            pIndoorSceneRuntime->party().applyEventRuntimeState(*pEventRuntimeState, false);
        }

        if (m_config.loadUniqueActorIndex.has_value()
            && !filterIndoorRuntimeToUniqueActor(
                pIndoorSceneRuntime->worldRuntime(),
                *m_config.loadUniqueActorIndex,
                selectedMap->map.fileName))
        {
            return false;
        }

        preloadMapGameplaySounds(
            m_gameAudioSystem,
            m_gameDataLoader.getMonsterTable(),
            m_gameDataLoader.getSpellTable(),
            *selectedMap);
        timingLogger.stage("indoor gameplay sounds preloaded");

        pIndoorSceneRuntime->partyRuntime().setMovementSpeedMultiplier(m_settings.movementSpeedMultiplier);
        pIndoorSceneRuntime->partyRuntime().setAlwaysRunEnabled(m_settings.alwaysRun);
        pIndoorSceneRuntime->partyRuntime().setCollisionTraceEnabled(
            m_settings.collisionTrace,
            selectedMap->map.fileName);

        if (initializeView
            && !m_indoorRenderer.initialize(
                m_pAssetFileSystem,
                m_pAssetFileSystem != nullptr ? m_pAssetFileSystem->getAssetScaleTier() : Engine::AssetScaleTier::X1,
                selectedMap->map,
                m_gameDataLoader.getMonsterTable(),
                *selectedMap->indoorMapData,
                selectedMap->indoorTextureSet,
                selectedMap->indoorDecorationBillboardSet,
                selectedMap->indoorActorPreviewBillboardSet,
                selectedMap->indoorSpriteObjectBillboardSet,
                *pIndoorSceneRuntime,
                m_gameDataLoader.getObjectTable(),
                m_gameDataLoader.getItemTable(),
                m_gameDataLoader.getChestTable(),
                m_gameDataLoader.getHouseTable()))
        {
            std::cerr
                << "GameApplication: indoor renderer initialization failed for map "
                << selectedMap->map.fileName
                << '\n';
            return false;
        }
        timingLogger.stage("indoor renderer initialized");

        if (initializeView)
        {
            pIndoorSceneRuntime->worldRuntime().bindRenderer(&m_indoorRenderer);
        }

        if (initializeView
            && !m_indoorGameView.initialize(
                *m_pAssetFileSystem,
                selectedMap->map,
                m_indoorRenderer,
                *pIndoorSceneRuntime,
                &m_gameAudioSystem))
        {
            std::cerr
                << "GameApplication: indoor gameplay view initialization failed for map "
                << selectedMap->map.fileName
                << '\n';
            return false;
        }
        timingLogger.stage("indoor view initialized");

        if (initializeView && bgfx::getRendererType() != bgfx::RendererType::Noop)
        {
            m_gameDataLoader.releaseSelectedMapRenderSourcePixels();
        }

        m_indoorGameView.setSettingsSnapshot(m_settings);

        m_pMapSceneRuntime = std::move(pIndoorSceneRuntime);
        m_gameplayController.bindRuntime(m_pMapSceneRuntime.get());
        timingLogger.stage("indoor scene runtime bound");
        releaseUnusedHeapPages();
        return true;
    }

    std::cerr
        << "GameApplication: selected map "
        << selectedMap->map.fileName
        << " has neither outdoor nor indoor runtime data\n";
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
    const GameDataRepository &data = m_gameSession.data();
    party.setItemTable(&data.itemTable());
    party.setJournalQuestTable(&data.journalQuestTable());
    party.setCharacterDollTable(&data.characterDollTable());
    party.setItemEnchantTables(&data.standardItemEnchantTable(), &data.specialItemEnchantTable());
    party.setClassMultiplierTable(&data.classMultiplierTable());
    party.setClassSkillTable(&data.classSkillTable());
}

void GameApplication::synchronizeActiveReputationToParty()
{
    if (m_pMapSceneRuntime == nullptr)
    {
        return;
    }

    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();
    IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();

    if (!selectedMap || pWorldRuntime == nullptr)
    {
        return;
    }

    storeWorldReputationInParty(
        m_pMapSceneRuntime->party(),
        *pWorldRuntime,
        selectedMap->map,
        m_gameDataLoader.getMergedContinentSettingTable());
}

void GameApplication::synchronizeSessionFromRuntime()
{
    if (m_pMapSceneRuntime == nullptr)
    {
        return;
    }

    m_gameplayController.synchronizeSessionFromRuntime();
    synchronizeActiveReputationToParty();
    m_gameSession.setCurrentSceneKind(m_pMapSceneRuntime->kind());
    m_gameSession.setCurrentMapFileName(m_pMapSceneRuntime->currentMapFileName());

    if (m_pMapSceneRuntime->kind() == SceneKind::Outdoor
        && m_pOutdoorPartyRuntime != nullptr
        && m_pOutdoorWorldRuntime != nullptr)
    {
        const OutdoorWorldRuntime::Snapshot worldSnapshot = m_pOutdoorWorldRuntime->snapshot();
        m_gameSession.captureOutdoorRuntimeState(
            m_pMapSceneRuntime->currentMapFileName(),
            m_pMapSceneRuntime->party(),
            m_pOutdoorPartyRuntime->snapshot(),
            worldSnapshot,
            m_outdoorGameView.cameraYawRadians(),
            m_outdoorGameView.cameraPitchRadians());

        const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

        if (selectedMap && !selectedMap->map.canonicalId.empty())
        {
            m_gameSession.storeOutdoorWorldState(selectedMap->map.canonicalId, worldSnapshot);
        }

        return;
    }

    if (m_pMapSceneRuntime->kind() == SceneKind::Indoor)
    {
        const IndoorSceneRuntime *pIndoorRuntime = static_cast<const IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
        const IndoorSceneRuntime::Snapshot snapshot = pIndoorRuntime->snapshot();
        m_gameSession.captureIndoorRuntimeState(
            m_pMapSceneRuntime->currentMapFileName(),
            m_pMapSceneRuntime->party(),
            snapshot);

        const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

        if (selectedMap && !selectedMap->map.canonicalId.empty())
        {
            m_gameSession.storeIndoorSceneState(selectedMap->map.canonicalId, snapshot);
        }
    }
}

bool GameApplication::loadCurrentSessionMap(
    bool initializeView,
    const std::function<void(int)> &progressCallback)
{
    setGprofProfilingEnabled(false);

    if (m_pAssetFileSystem == nullptr || !m_gameSession.hasCurrentMapFileName())
    {
        std::cerr
            << "GameApplication: loadCurrentSessionMap missing prerequisites"
            << " asset_fs=" << (m_pAssetFileSystem != nullptr ? "yes" : "no")
            << " has_map=" << (m_gameSession.hasCurrentMapFileName() ? "yes" : "no")
            << '\n';
        return false;
    }

    if (!ensureCommonGameDataLoaded())
    {
        std::cerr << "GameApplication: loadCurrentSessionMap failed to load common gameplay data\n";
        return false;
    }

    MapLoadTimingLogger timingLogger(m_gameSession.currentMapFileName(), "current_session_map");

    if (progressCallback)
    {
        progressCallback(10);
    }

    timingLogger.beginStage("world activation");
    if (!activateWorldForMapFileName(m_gameSession.currentMapFileName()))
    {
        return false;
    }
    timingLogger.stage("world activated");

    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();
    const bool selectedMapMatchesSession =
        selectedMap.has_value() && sameMapFileName(selectedMap->map.fileName, m_gameSession.currentMapFileName());
    const bool forceReloadSelectedMapForRespawn =
        selectedMapMatchesSession
        && savedSelectedMapStateNeedsFreshAssets(
            m_gameSession,
            *selectedMap,
            currentLocationDay(m_gameSession.gameMinutes()));
    const bool forceReloadSelectedMapForRenderer =
        selectedMapMatchesSession
        && initializeView
        && m_gameDataLoader.selectedMapRenderSourcePixelsReleased();
    const bool forceReloadSelectedMap =
        forceReloadSelectedMapForRespawn || forceReloadSelectedMapForRenderer;

    timingLogger.beginStage("renderer shutdown");
    shutdownRenderer();
    timingLogger.stage("renderer shutdown");

    if (!selectedMapMatchesSession || forceReloadSelectedMap)
    {
        timingLogger.beginStage("game data loader map load");
    }

    if ((!selectedMapMatchesSession || forceReloadSelectedMap)
        && !m_gameDataLoader.loadMapByFileNameForGameplay(
                *m_pAssetFileSystem,
                m_gameSession.currentMapFileName(),
                [this]()
                {
                    pumpLoadingOverlayAnimation();
                }))
    {
        std::cerr
            << "GameApplication: loadCurrentSessionMap failed to load map assets for "
            << m_gameSession.currentMapFileName()
            << '\n';
        return false;
    }

    timingLogger.stage(
        selectedMapMatchesSession && !forceReloadSelectedMap
            ? "game data loader map load reused selected map"
            : "game data loader map load");

    if (progressCallback)
    {
        progressCallback(55);
    }

    timingLogger.beginStage(initializeView ? "runtime and view initialization" : "runtime initialization");
    if (!initializeSelectedMapRuntime(initializeView))
    {
        std::cerr
            << "GameApplication: loadCurrentSessionMap failed to initialize runtime for "
            << m_gameSession.currentMapFileName()
            << '\n';
        return false;
    }

    timingLogger.stage(initializeView ? "runtime and view initialized" : "runtime initialized");
    const std::string sceneKind =
        m_pMapSceneRuntime != nullptr ? sceneKindName(m_pMapSceneRuntime->kind()) : "none";
    std::string poseDetails;
    float traceGameMinutes = m_gameSession.gameMinutes();
    if (IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime())
    {
        traceGameMinutes = pWorldRuntime->gameMinutes();
        poseDetails =
            " party=(" + std::to_string(pWorldRuntime->partyX())
            + "," + std::to_string(pWorldRuntime->partyY())
            + "," + std::to_string(pWorldRuntime->partyFootZ()) + ")"
            + " yaw=" + std::to_string(pWorldRuntime->gameplayCameraYawRadians())
            + " pitch=" + std::to_string(pWorldRuntime->gameplayCameraPitchRadians());
    }
    GAMEPLAY_DEBUG_TRACE(
        "map_loaded map=\"" + m_gameSession.currentMapFileName() + "\""
        + " scene_kind=" + sceneKind
        + " game_minutes=" + std::to_string(traceGameMinutes)
        + " initialize_view=" + (initializeView ? "true" : "false")
        + poseDetails);

    if (progressCallback)
    {
        progressCallback(90);
    }

    if (progressCallback)
    {
        progressCallback(100);
    }

    timingLogger.stage("current session map load complete");
    return true;
}

void GameApplication::beginLoadingOverlay(LoadingOverlayScreen::Presentation presentation)
{
    setGprofProfilingEnabled(false);

    if (m_pAssetFileSystem == nullptr)
    {
        return;
    }

    const char *pDisableOverlay = std::getenv("OPENYAMM_DISABLE_LOADING_OVERLAY");

    if (pDisableOverlay != nullptr && std::string(pDisableOverlay) == "1")
    {
        cancelLoadingOverlay();
        return;
    }

    const char *pVideoDriver = SDL_GetCurrentVideoDriver();

    if (pVideoDriver != nullptr && std::string(pVideoDriver) == "dummy")
    {
        cancelLoadingOverlay();
        return;
    }

    if (m_pLoadingOverlayScreen == nullptr)
    {
        m_pLoadingOverlayScreen = std::make_unique<LoadingOverlayScreen>(*m_pAssetFileSystem);
    }

    m_pLoadingOverlayScreen->setPresentation(presentation);
    m_loadingOverlayPresentation = presentation;
    m_loadingOverlayCurrentProgressPercent = 0;
    m_loadingOverlayNextAnimationFrameTick = 0;

    if (presentation == LoadingOverlayScreen::Presentation::Fullscreen)
    {
        std::random_device randomDevice;
        std::mt19937 rng(randomDevice());
        const int backgroundIndex = std::uniform_int_distribution<int>(1, LoadingOverlayBackgroundCount)(rng);
        m_loadingOverlayBackgroundTextureName = "loading" + std::to_string(backgroundIndex);
    }
    else
    {
        m_loadingOverlayBackgroundTextureName = "bardata";
    }

    m_loadingOverlayActive = true;
    renderLoadingOverlayProgress(0);
}

void GameApplication::renderLoadingOverlayProgress(int progressPercent)
{
    if (!m_loadingOverlayActive || m_pLoadingOverlayScreen == nullptr)
    {
        return;
    }

    m_loadingOverlayCurrentProgressPercent = std::clamp(progressPercent, 0, 100);
    m_pLoadingOverlayScreen->setBackgroundTextureName(m_loadingOverlayBackgroundTextureName);
    m_pLoadingOverlayScreen->setProgressPercent(progressPercent);
    SDL_PumpEvents();
    m_pLoadingOverlayScreen->renderFrame(
        std::max(1, m_lastFrameWidth),
        std::max(1, m_lastFrameHeight),
        m_gameInputSystem.frame(),
        1.0f / 60.0f);
    bgfx::frame();
}

bool GameApplication::logFramePerformanceDiagnostics(uint32_t currentTick)
{
    constexpr uint32_t LogIntervalMs = 1000;

    if (!m_framePerformanceDiagnostics.hasActivity()
        || currentTick - m_lastFramePerformanceLogTick < LogIntervalMs)
    {
        return false;
    }

    m_lastFramePerformanceLogTick = currentTick;

    const FramePerformanceDiagnostics diagnostics = m_framePerformanceDiagnostics;
    const uint64_t measuredNanoseconds =
        diagnostics.pendingDebugMapJumpNanoseconds
        + diagnostics.debugConsoleBeginNanoseconds
        + diagnostics.inputNanoseconds
        + diagnostics.activeScreenNanoseconds
        + diagnostics.pendingStateNanoseconds
        + diagnostics.gameplayUpdateNanoseconds
        + diagnostics.worldUpdateNanoseconds
        + diagnostics.renderWorldNanoseconds
        + diagnostics.renderGameplayUiNanoseconds
        + diagnostics.audioNanoseconds
        + diagnostics.postWorldNanoseconds
        + diagnostics.debugConsoleRenderNanoseconds
        + diagnostics.performanceTraceLogNanoseconds;
    const uint64_t untrackedNanoseconds =
        diagnostics.totalNanoseconds > measuredNanoseconds
            ? diagnostics.totalNanoseconds - measuredNanoseconds
            : 0;

    std::cout << "[GameFramePerf]"
              << " frames=" << diagnostics.frames
              << " active_screen_frames=" << diagnostics.activeScreenFrames
              << " gameplay_world_frames=" << diagnostics.gameplayWorldFrames
              << " avg_total_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.totalNanoseconds,
                  diagnostics.frames))
              << " avg_untracked_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  untrackedNanoseconds,
                  diagnostics.frames))
              << " avg_pending_debug_jump_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.pendingDebugMapJumpNanoseconds,
                  diagnostics.frames))
              << " avg_debug_console_begin_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.debugConsoleBeginNanoseconds,
                  diagnostics.frames))
              << " avg_input_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.inputNanoseconds,
                  diagnostics.frames))
              << " avg_active_screen_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.activeScreenNanoseconds,
                  diagnostics.frames))
              << " avg_pending_state_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.pendingStateNanoseconds,
                  diagnostics.frames))
              << " avg_gameplay_update_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.gameplayUpdateNanoseconds,
                  diagnostics.frames))
              << " avg_world_update_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.worldUpdateNanoseconds,
                  diagnostics.frames))
              << " avg_render_world_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.renderWorldNanoseconds,
                  diagnostics.frames))
              << " avg_render_gameplay_ui_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.renderGameplayUiNanoseconds,
                  diagnostics.frames))
              << " avg_audio_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.audioNanoseconds,
                  diagnostics.frames))
              << " avg_post_world_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.postWorldNanoseconds,
                  diagnostics.frames))
              << " avg_debug_console_render_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.debugConsoleRenderNanoseconds,
                  diagnostics.frames))
              << " avg_performance_trace_log_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.performanceTraceLogNanoseconds,
                  diagnostics.frames))
              << '\n';

    m_framePerformanceDiagnostics = {};
    return true;
}

void GameApplication::logFrameHitchDiagnostics(const FramePerformanceDiagnostics &diagnostics) const
{
    const uint64_t measuredNanoseconds =
        diagnostics.pendingDebugMapJumpNanoseconds
        + diagnostics.debugConsoleBeginNanoseconds
        + diagnostics.inputNanoseconds
        + diagnostics.activeScreenNanoseconds
        + diagnostics.pendingStateNanoseconds
        + diagnostics.gameplayUpdateNanoseconds
        + diagnostics.worldUpdateNanoseconds
        + diagnostics.renderWorldNanoseconds
        + diagnostics.renderGameplayUiNanoseconds
        + diagnostics.audioNanoseconds
        + diagnostics.postWorldNanoseconds
        + diagnostics.debugConsoleRenderNanoseconds
        + diagnostics.performanceTraceLogNanoseconds;
    const uint64_t untrackedNanoseconds =
        diagnostics.totalNanoseconds > measuredNanoseconds
            ? diagnostics.totalNanoseconds - measuredNanoseconds
            : 0;
    const char *pSceneKind =
        m_pMapSceneRuntime != nullptr ? sceneKindName(m_pMapSceneRuntime->kind()) : "none";

    std::cout << "[GameFrameHitchDetail]"
              << " map=\"" << m_gameSession.currentMapFileName() << "\""
              << " scene=" << pSceneKind
              << " total_us=" << nanosecondsToMicroseconds(diagnostics.totalNanoseconds)
              << " untracked_us=" << nanosecondsToMicroseconds(untrackedNanoseconds)
              << " pending_debug_jump_us="
              << nanosecondsToMicroseconds(diagnostics.pendingDebugMapJumpNanoseconds)
              << " debug_console_begin_us="
              << nanosecondsToMicroseconds(diagnostics.debugConsoleBeginNanoseconds)
              << " input_us=" << nanosecondsToMicroseconds(diagnostics.inputNanoseconds)
              << " active_screen_us=" << nanosecondsToMicroseconds(diagnostics.activeScreenNanoseconds)
              << " pending_state_us=" << nanosecondsToMicroseconds(diagnostics.pendingStateNanoseconds)
              << " gameplay_update_us=" << nanosecondsToMicroseconds(diagnostics.gameplayUpdateNanoseconds)
              << " world_update_us=" << nanosecondsToMicroseconds(diagnostics.worldUpdateNanoseconds)
              << " render_world_us=" << nanosecondsToMicroseconds(diagnostics.renderWorldNanoseconds)
              << " render_gameplay_ui_us="
              << nanosecondsToMicroseconds(diagnostics.renderGameplayUiNanoseconds)
              << " audio_us=" << nanosecondsToMicroseconds(diagnostics.audioNanoseconds)
              << " post_world_us=" << nanosecondsToMicroseconds(diagnostics.postWorldNanoseconds)
              << " debug_console_render_us="
              << nanosecondsToMicroseconds(diagnostics.debugConsoleRenderNanoseconds)
              << " performance_trace_log_us="
              << nanosecondsToMicroseconds(diagnostics.performanceTraceLogNanoseconds)
              << '\n';

    const GameplayUpdateFramePerformanceDiagnostics &gameplayUpdate =
        m_gameSession.lastGameplayUpdateFramePerformanceDiagnostics();

    if (gameplayUpdate.collected && gameplayUpdate.totalNanoseconds != 0)
    {
        const uint64_t gameplayUpdateMeasuredNanoseconds =
            gameplayUpdate.sharedFrameStateNanoseconds
            + gameplayUpdate.worldInteractionStateNanoseconds
            + gameplayUpdate.activeMemberSyncNanoseconds
            + gameplayUpdate.sharedInputNanoseconds
            + gameplayUpdate.worldMovementNanoseconds
            + gameplayUpdate.actorAiNanoseconds
            + gameplayUpdate.combatEventsNanoseconds
            + gameplayUpdate.interactionFrameNanoseconds
            + gameplayUpdate.projectileAndCooldownNanoseconds
            + gameplayUpdate.performanceTraceLogNanoseconds;
        const uint64_t gameplayUpdateUntrackedNanoseconds =
            gameplayUpdate.totalNanoseconds > gameplayUpdateMeasuredNanoseconds
                ? gameplayUpdate.totalNanoseconds - gameplayUpdateMeasuredNanoseconds
                : 0;

        std::cout << "[GameplayUpdateHitchDetail]"
                  << " total_us=" << nanosecondsToMicroseconds(gameplayUpdate.totalNanoseconds)
                  << " untracked_us=" << nanosecondsToMicroseconds(gameplayUpdateUntrackedNanoseconds)
                  << " shared_frame_state_us="
                  << nanosecondsToMicroseconds(gameplayUpdate.sharedFrameStateNanoseconds)
                  << " world_interaction_state_us="
                  << nanosecondsToMicroseconds(gameplayUpdate.worldInteractionStateNanoseconds)
                  << " active_member_sync_us="
                  << nanosecondsToMicroseconds(gameplayUpdate.activeMemberSyncNanoseconds)
                  << " shared_input_us=" << nanosecondsToMicroseconds(gameplayUpdate.sharedInputNanoseconds)
                  << " world_movement_us=" << nanosecondsToMicroseconds(gameplayUpdate.worldMovementNanoseconds)
                  << " actor_ai_us=" << nanosecondsToMicroseconds(gameplayUpdate.actorAiNanoseconds)
                  << " combat_events_us=" << nanosecondsToMicroseconds(gameplayUpdate.combatEventsNanoseconds)
                  << " interaction_frame_us="
                  << nanosecondsToMicroseconds(gameplayUpdate.interactionFrameNanoseconds)
                  << " projectile_cooldown_us="
                  << nanosecondsToMicroseconds(gameplayUpdate.projectileAndCooldownNanoseconds)
                  << " performance_trace_log_us="
                  << nanosecondsToMicroseconds(gameplayUpdate.performanceTraceLogNanoseconds)
                  << '\n';
    }

    const GameplayWorldMovementFrameDiagnostics &movement = gameplayUpdate.worldMovement;

    if (movement.collected)
    {
        const uint64_t controllerUntrackedNanoseconds =
            movement.controllerNanoseconds > movement.sceneAdvanceNanoseconds
                ? movement.controllerNanoseconds - movement.sceneAdvanceNanoseconds
                : 0;
        const uint64_t sceneMeasuredNanoseconds =
            movement.actorColliderBuildNanoseconds
            + movement.partyUpdateNanoseconds
            + movement.timerNanoseconds
            + movement.partyEventApplyNanoseconds
            + movement.pressurePlateNanoseconds
            + movement.boundaryTransitionNanoseconds
            + movement.actorQueueAndContactsNanoseconds;
        const uint64_t sceneUntrackedNanoseconds =
            movement.sceneAdvanceNanoseconds > sceneMeasuredNanoseconds
                ? movement.sceneAdvanceNanoseconds - sceneMeasuredNanoseconds
                : 0;
        const uint64_t partyMeasuredNanoseconds =
            movement.movementDriverNanoseconds
            + movement.partyRecoveryNanoseconds
            + movement.partyTimedStateNanoseconds
            + movement.partySpellStateNanoseconds
            + movement.partyEffectsNanoseconds;
        const uint64_t partyUntrackedNanoseconds =
            movement.partyUpdateNanoseconds > partyMeasuredNanoseconds
                ? movement.partyUpdateNanoseconds - partyMeasuredNanoseconds
                : 0;
        const uint64_t movementMeasuredNanoseconds =
            movement.movementInputNanoseconds
            + movement.movementCollisionNanoseconds
            + movement.movementTraceNanoseconds
            + movement.movementContactsNanoseconds
            + movement.movementConsequencesNanoseconds;
        const uint64_t movementUntrackedNanoseconds =
            movement.movementDriverNanoseconds > movementMeasuredNanoseconds
                ? movement.movementDriverNanoseconds - movementMeasuredNanoseconds
                : 0;
        const uint64_t timerMeasuredNanoseconds =
            movement.timerEventExecutionNanoseconds + movement.timerEventApplyNanoseconds;
        const uint64_t timerUntrackedNanoseconds =
            movement.timerNanoseconds > timerMeasuredNanoseconds
                ? movement.timerNanoseconds - timerMeasuredNanoseconds
                : 0;

        std::cout << "[OutdoorMovementHitchDetail]"
                  << " total_us=" << nanosecondsToMicroseconds(movement.totalNanoseconds)
                  << " controller_us=" << nanosecondsToMicroseconds(movement.controllerNanoseconds)
                  << " controller_untracked_us="
                  << nanosecondsToMicroseconds(controllerUntrackedNanoseconds)
                  << " scene_advance_us=" << nanosecondsToMicroseconds(movement.sceneAdvanceNanoseconds)
                  << " scene_untracked_us=" << nanosecondsToMicroseconds(sceneUntrackedNanoseconds)
                  << " actor_collider_build_us="
                  << nanosecondsToMicroseconds(movement.actorColliderBuildNanoseconds)
                  << " party_update_us=" << nanosecondsToMicroseconds(movement.partyUpdateNanoseconds)
                  << " party_untracked_us=" << nanosecondsToMicroseconds(partyUntrackedNanoseconds)
                  << " movement_driver_us=" << nanosecondsToMicroseconds(movement.movementDriverNanoseconds)
                  << " movement_untracked_us=" << nanosecondsToMicroseconds(movementUntrackedNanoseconds)
                  << " movement_input_us=" << nanosecondsToMicroseconds(movement.movementInputNanoseconds)
                  << " movement_collision_us="
                  << nanosecondsToMicroseconds(movement.movementCollisionNanoseconds)
                  << " movement_trace_us=" << nanosecondsToMicroseconds(movement.movementTraceNanoseconds)
                  << " movement_contacts_us=" << nanosecondsToMicroseconds(movement.movementContactsNanoseconds)
                  << " movement_consequences_us="
                  << nanosecondsToMicroseconds(movement.movementConsequencesNanoseconds)
                  << " party_recovery_us=" << nanosecondsToMicroseconds(movement.partyRecoveryNanoseconds)
                  << " party_timed_state_us="
                  << nanosecondsToMicroseconds(movement.partyTimedStateNanoseconds)
                  << " party_spell_state_us="
                  << nanosecondsToMicroseconds(movement.partySpellStateNanoseconds)
                  << " party_effects_us=" << nanosecondsToMicroseconds(movement.partyEffectsNanoseconds)
                  << " timer_us=" << nanosecondsToMicroseconds(movement.timerNanoseconds)
                  << " timer_untracked_us=" << nanosecondsToMicroseconds(timerUntrackedNanoseconds)
                  << " timer_event_execution_us="
                  << nanosecondsToMicroseconds(movement.timerEventExecutionNanoseconds)
                  << " timer_event_apply_us="
                  << nanosecondsToMicroseconds(movement.timerEventApplyNanoseconds)
                  << " party_event_apply_us="
                  << nanosecondsToMicroseconds(movement.partyEventApplyNanoseconds)
                  << " pressure_plate_us=" << nanosecondsToMicroseconds(movement.pressurePlateNanoseconds)
                  << " boundary_transition_us="
                  << nanosecondsToMicroseconds(movement.boundaryTransitionNanoseconds)
                  << " actor_queue_contacts_us="
                  << nanosecondsToMicroseconds(movement.actorQueueAndContactsNanoseconds)
                  << " movement_steps=" << movement.movementStepCount
                  << " timer_events_fired=" << movement.timerEventsFired
                  << " timer_event_ids=";

        if (movement.storedTimerEventIdCount == 0)
        {
            std::cout << "none";
        }
        else
        {
            for (size_t eventIndex = 0; eventIndex < movement.storedTimerEventIdCount; ++eventIndex)
            {
                if (eventIndex != 0)
                {
                    std::cout << ',';
                }

                std::cout << movement.timerEventIds[eventIndex];
            }
        }

        std::cout << '\n';
    }

    const GameplayUiFramePerformanceDiagnostics &gameplayUi =
        m_gameSession.lastGameplayUiFramePerformanceDiagnostics();
    const GameplayUiOverlayFramePerformanceDiagnostics &overlays = gameplayUi.overlays;

    if (gameplayUi.collected && gameplayUi.totalNanoseconds != 0)
    {
        const uint64_t gameplayUiMeasuredNanoseconds =
            gameplayUi.worldUiRenderStateNanoseconds
            + gameplayUi.standardUiNanoseconds
            + gameplayUi.pendingSpellOverlayNanoseconds;
        const uint64_t gameplayUiUntrackedNanoseconds =
            gameplayUi.totalNanoseconds > gameplayUiMeasuredNanoseconds
                ? gameplayUi.totalNanoseconds - gameplayUiMeasuredNanoseconds
                : 0;
        const uint64_t overlayMeasuredNanoseconds =
            overlays.beginInspectableFrameNanoseconds
            + overlays.pendingDialogNanoseconds
            + overlays.screenFxNanoseconds
            + overlays.chestBelowNanoseconds
            + overlays.inventoryBelowNanoseconds
            + overlays.dialogueBelowNanoseconds
            + overlays.characterBelowNanoseconds
            + overlays.hudArtNanoseconds
            + overlays.hudNanoseconds
            + overlays.chestAboveNanoseconds
            + overlays.inventoryAboveNanoseconds
            + overlays.characterAboveNanoseconds
            + overlays.dialogueAboveNanoseconds
            + overlays.restNanoseconds
            + overlays.menuNanoseconds
            + overlays.controlsNanoseconds
            + overlays.keyboardNanoseconds
            + overlays.videoOptionsNanoseconds
            + overlays.saveGameNanoseconds
            + overlays.loadGameNanoseconds
            + overlays.journalNanoseconds
            + overlays.quickReferenceNanoseconds
            + overlays.spellbookNanoseconds
            + overlays.heldItemNanoseconds
            + overlays.itemInspectNanoseconds
            + overlays.mouseLookNanoseconds
            + overlays.deferredInventoryNanoseconds
            + overlays.utilitySpellNanoseconds
            + overlays.characterInspectNanoseconds
            + overlays.buffInspectNanoseconds
            + overlays.characterDetailNanoseconds
            + overlays.actorInspectNanoseconds
            + overlays.spellInspectNanoseconds
            + overlays.readableScrollNanoseconds;
        const uint64_t overlayUntrackedNanoseconds =
            overlays.totalNanoseconds > overlayMeasuredNanoseconds
                ? overlays.totalNanoseconds - overlayMeasuredNanoseconds
                : 0;

        std::cout << "[GameplayUiHitchDetail]"
                  << " total_us=" << nanosecondsToMicroseconds(gameplayUi.totalNanoseconds)
                  << " untracked_us=" << nanosecondsToMicroseconds(gameplayUiUntrackedNanoseconds)
                  << " world_ui_state_us="
                  << nanosecondsToMicroseconds(gameplayUi.worldUiRenderStateNanoseconds)
                  << " standard_ui_us=" << nanosecondsToMicroseconds(gameplayUi.standardUiNanoseconds)
                  << " pending_spell_overlay_us="
                  << nanosecondsToMicroseconds(gameplayUi.pendingSpellOverlayNanoseconds)
                  << " overlays_total_us=" << nanosecondsToMicroseconds(overlays.totalNanoseconds)
                  << " overlays_untracked_us=" << nanosecondsToMicroseconds(overlayUntrackedNanoseconds)
                  << " inspect_frame_us="
                  << nanosecondsToMicroseconds(overlays.beginInspectableFrameNanoseconds)
                  << " pending_dialog_us=" << nanosecondsToMicroseconds(overlays.pendingDialogNanoseconds)
                  << " screen_fx_us=" << nanosecondsToMicroseconds(overlays.screenFxNanoseconds)
                  << " chest_below_us=" << nanosecondsToMicroseconds(overlays.chestBelowNanoseconds)
                  << " inventory_below_us=" << nanosecondsToMicroseconds(overlays.inventoryBelowNanoseconds)
                  << " dialogue_below_us=" << nanosecondsToMicroseconds(overlays.dialogueBelowNanoseconds)
                  << " character_below_us=" << nanosecondsToMicroseconds(overlays.characterBelowNanoseconds)
                  << " hud_art_us=" << nanosecondsToMicroseconds(overlays.hudArtNanoseconds)
                  << " hud_us=" << nanosecondsToMicroseconds(overlays.hudNanoseconds)
                  << " chest_above_us=" << nanosecondsToMicroseconds(overlays.chestAboveNanoseconds)
                  << " inventory_above_us=" << nanosecondsToMicroseconds(overlays.inventoryAboveNanoseconds)
                  << " character_above_us=" << nanosecondsToMicroseconds(overlays.characterAboveNanoseconds)
                  << " dialogue_above_us=" << nanosecondsToMicroseconds(overlays.dialogueAboveNanoseconds)
                  << " rest_us=" << nanosecondsToMicroseconds(overlays.restNanoseconds)
                  << " menu_us=" << nanosecondsToMicroseconds(overlays.menuNanoseconds)
                  << " controls_us=" << nanosecondsToMicroseconds(overlays.controlsNanoseconds)
                  << " keyboard_us=" << nanosecondsToMicroseconds(overlays.keyboardNanoseconds)
                  << " video_options_us=" << nanosecondsToMicroseconds(overlays.videoOptionsNanoseconds)
                  << " save_game_us=" << nanosecondsToMicroseconds(overlays.saveGameNanoseconds)
                  << " load_game_us=" << nanosecondsToMicroseconds(overlays.loadGameNanoseconds)
                  << " journal_us=" << nanosecondsToMicroseconds(overlays.journalNanoseconds)
                  << " quick_reference_us=" << nanosecondsToMicroseconds(overlays.quickReferenceNanoseconds)
                  << " spellbook_us=" << nanosecondsToMicroseconds(overlays.spellbookNanoseconds)
                  << " held_item_us=" << nanosecondsToMicroseconds(overlays.heldItemNanoseconds)
                  << " item_inspect_us=" << nanosecondsToMicroseconds(overlays.itemInspectNanoseconds)
                  << " mouse_look_us=" << nanosecondsToMicroseconds(overlays.mouseLookNanoseconds)
                  << " deferred_inventory_us="
                  << nanosecondsToMicroseconds(overlays.deferredInventoryNanoseconds)
                  << " utility_spell_us=" << nanosecondsToMicroseconds(overlays.utilitySpellNanoseconds)
                  << " character_inspect_us="
                  << nanosecondsToMicroseconds(overlays.characterInspectNanoseconds)
                  << " buff_inspect_us=" << nanosecondsToMicroseconds(overlays.buffInspectNanoseconds)
                  << " character_detail_us="
                  << nanosecondsToMicroseconds(overlays.characterDetailNanoseconds)
                  << " actor_inspect_us=" << nanosecondsToMicroseconds(overlays.actorInspectNanoseconds)
                  << " spell_inspect_us=" << nanosecondsToMicroseconds(overlays.spellInspectNanoseconds)
                  << " readable_scroll_us=" << nanosecondsToMicroseconds(overlays.readableScrollNanoseconds)
                  << '\n';
    }

    const GameplayUiRuntime &uiRuntime = m_gameSession.gameplayUiRuntime();

    for (const GameplayUiAssetLoadPerformanceEvent &event : uiRuntime.performanceAssetLoadEvents())
    {
        std::cout << "[UiAssetLoadPerf]"
                  << " kind=" << gameplayUiAssetLoadKindName(event.kind)
                  << " name=\"" << event.name << "\""
                  << " load_us=" << nanosecondsToMicroseconds(event.loadNanoseconds)
                  << " result=" << (event.success ? "loaded" : "failed")
                  << " size=" << event.width << 'x' << event.height;

        if (event.hasColor)
        {
            std::cout << " color_abgr=" << event.colorAbgr;
        }

        std::cout << '\n';
    }

    if (uiRuntime.performanceAssetLoadEventOverflowCount() != 0)
    {
        std::cout << "[UiAssetLoadPerf] overflow="
                  << uiRuntime.performanceAssetLoadEventOverflowCount()
                  << '\n';
    }
}

void GameApplication::pumpLoadingOverlayAnimation()
{
    if (!m_loadingOverlayActive
        || m_loadingOverlayPresentation != LoadingOverlayScreen::Presentation::DungeonTransition)
    {
        return;
    }

    const uint64_t now = SDL_GetTicks();

    if (m_loadingOverlayNextAnimationFrameTick != 0 && now < m_loadingOverlayNextAnimationFrameTick)
    {
        return;
    }

    renderLoadingOverlayProgress(m_loadingOverlayCurrentProgressPercent);
    m_loadingOverlayNextAnimationFrameTick = SDL_GetTicks() + DungeonTransitionOverlayFrameMilliseconds;
}

void GameApplication::completeLoadingOverlay()
{
    if (!m_loadingOverlayActive)
    {
        return;
    }

    renderLoadingOverlayProgress(100);
    m_loadingOverlayActive = false;
    m_loadingOverlayBackgroundTextureName.clear();
    m_loadingOverlayPresentation = LoadingOverlayScreen::Presentation::Fullscreen;
    m_loadingOverlayCurrentProgressPercent = 0;
    m_loadingOverlayNextAnimationFrameTick = 0;
    m_pLoadingOverlayScreen.reset();
}

void GameApplication::cancelLoadingOverlay()
{
    m_loadingOverlayActive = false;
    m_loadingOverlayBackgroundTextureName.clear();
    m_loadingOverlayPresentation = LoadingOverlayScreen::Presentation::Fullscreen;
    m_loadingOverlayCurrentProgressPercent = 0;
    m_loadingOverlayNextAnimationFrameTick = 0;
    m_pLoadingOverlayScreen.reset();
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

void GameApplication::captureCurrentSceneState()
{
    if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
    {
        IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
        pIndoorRuntime->stampLastVisitTime();
    }
    else if (m_pOutdoorWorldRuntime != nullptr)
    {
        m_pOutdoorWorldRuntime->stampLastVisitTime();
    }

    synchronizeSessionFromRuntime();
}

void GameApplication::restoreSavedOutdoorWorldStateForSelectedMap()
{
    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();

    if (!selectedMap || m_pOutdoorWorldRuntime == nullptr || !selectedMap->outdoorMapData)
    {
        return;
    }

    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot>::const_iterator stateIt =
        m_gameSession.outdoorWorldStates().find(selectedMap->map.canonicalId);

    if (stateIt == m_gameSession.outdoorWorldStates().end())
    {
        stateIt = m_gameSession.outdoorWorldStates().find(selectedMap->map.fileName);
    }

    if (stateIt == m_gameSession.outdoorWorldStates().end())
    {
        return;
    }

    m_pOutdoorWorldRuntime->restoreSnapshot(stateIt->second);
}

void GameApplication::shutdownRenderer()
{
    m_gameAudioSystem.stopAllPlayback();
    MenuScreenBase::shutdownSharedResources();
    m_mainMenuChildScreensPrepared = false;
    m_outdoorGameView.shutdown();
    m_indoorGameView.shutdown();
    m_indoorRenderer.shutdown();
    m_gameplayController.clearRuntime();
    m_pMapSceneRuntime.reset();
    m_pOutdoorPartyRuntime.reset();
    m_pOutdoorWorldRuntime.reset();

    if (Engine::BgfxContext::isBgfxInitialized())
    {
        // bgfx defers freeing destroyed handles until the next frame. Map transitions reconstruct the renderer
        // immediately, so advance the resource lifecycle before the next map starts allocating handles.
        bgfx::frame();
    }
}

void GameApplication::updateQuickSaveInput()
{
    const GameplayInputFrame &inputFrame = m_gameInputSystem.frame();

    if (inputFrame.isScancodeHeld(SDL_SCANCODE_F9))
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

    if (inputFrame.isScancodeHeld(SDL_SCANCODE_F10))
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

void GameApplication::updateDoubleSpeedInput()
{
    if (m_gameSession.gameplayScreenRuntime().currentHudScreenState() != GameplayHudScreenState::Gameplay)
    {
        return;
    }

    const GameplayInputFrame &inputFrame = m_gameInputSystem.frame();

    if (!inputFrame.action(KeyboardAction::DoubleSpeed).pressed)
    {
        return;
    }

    m_doubleSpeedActive = !m_doubleSpeedActive;
    m_gameSession.gameplayScreenRuntime().setStatusBarEvent(
        m_doubleSpeedActive ? "Fast mode (2x)" : "Normal mode (1x)");
}

float GameApplication::gameplayDeltaSeconds(float deltaSeconds) const
{
    return m_doubleSpeedActive ? deltaSeconds * 2.0f : deltaSeconds;
}

void GameApplication::updateGameplayTraceSnapshotHotkeys()
{
    if (!gameplayDebugTraceEnabled())
    {
        return;
    }

    const GameplayInputFrame &inputFrame = m_gameInputSystem.frame();
    const bool startPressed = inputFrame.isScancodeHeld(SDL_SCANCODE_F3);
    const bool endPressed = inputFrame.isScancodeHeld(SDL_SCANCODE_F4);
    const bool markerPressed = inputFrame.isScancodeHeld(SDL_SCANCODE_F5);
    const bool forwardHeld =
        inputFrame.action(KeyboardAction::Forward).held
        || inputFrame.isScancodeHeld(SDL_SCANCODE_W);
    const bool shiftHeld = inputFrame.isScancodeHeld(SDL_SCANCODE_LSHIFT)
        || inputFrame.isScancodeHeld(SDL_SCANCODE_RSHIFT);
    const bool ctrlHeld = inputFrame.isScancodeHeld(SDL_SCANCODE_LCTRL)
        || inputFrame.isScancodeHeld(SDL_SCANCODE_RCTRL);
    const bool altHeld = inputFrame.isScancodeHeld(SDL_SCANCODE_LALT)
        || inputFrame.isScancodeHeld(SDL_SCANCODE_RALT);

    const auto captureSnapshot =
        [this, &inputFrame, forwardHeld, shiftHeld, ctrlHeld, altHeld]() -> std::optional<GameplayTraceMovementSnapshot>
        {
            IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();

            if (pWorldRuntime == nullptr)
            {
                return std::nullopt;
            }

            GameplayTraceMovementSnapshot snapshot = {};
            snapshot.mapName = pWorldRuntime->mapName();
            snapshot.indoor = pWorldRuntime->isIndoorMap();
            snapshot.partyX = pWorldRuntime->partyX();
            snapshot.partyY = pWorldRuntime->partyY();
            snapshot.partyZ = pWorldRuntime->partyFootZ();
            snapshot.yawRadians = pWorldRuntime->gameplayCameraYawRadians();
            snapshot.pitchRadians = pWorldRuntime->gameplayCameraPitchRadians();
            snapshot.gameMinutes = pWorldRuntime->gameMinutes();
            snapshot.tickMilliseconds = SDL_GetTicks();
            snapshot.forwardHeld = forwardHeld;
            snapshot.runWalkModifierHeld = shiftHeld;
            snapshot.turboHeld = ctrlHeld;
            snapshot.shiftHeld = shiftHeld;
            snapshot.ctrlHeld = ctrlHeld;
            snapshot.altHeld = altHeld;

            const GameplayUiController::HeldInventoryItemState &heldItem =
                m_gameSession.gameplayScreenRuntime().heldInventoryItem();
            snapshot.heldItemActive = heldItem.active;
            snapshot.heldItemId = heldItem.active ? heldItem.item.objectDescriptionId : 0;

            if (m_pMapSceneRuntime != nullptr
                && m_pMapSceneRuntime->kind() == SceneKind::Outdoor
                && m_pOutdoorPartyRuntime != nullptr)
            {
                const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
                const OutdoorPartyMovementState &partyMovementState = m_pOutdoorPartyRuntime->partyMovementState();
                snapshot.outdoorRunning = partyMovementState.running;
                snapshot.outdoorFlying = partyMovementState.flying;
                snapshot.outdoorWaterWalk = partyMovementState.waterWalk;
                snapshot.outdoorFeatherFall = partyMovementState.featherFall;
                snapshot.outdoorAirborne = moveState.airborne;
                snapshot.outdoorSupportKind = static_cast<uint32_t>(moveState.supportKind);
                snapshot.outdoorSupportBModelIndex = moveState.supportBModelIndex;
                snapshot.outdoorSupportFaceIndex = moveState.supportFaceIndex;
            }
            else if (m_pMapSceneRuntime != nullptr
                && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
            {
                const IndoorSceneRuntime *pIndoorRuntime =
                    static_cast<const IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
                const IndoorMoveState &moveState = pIndoorRuntime->partyRuntime().movementState();
                snapshot.indoorGrounded = moveState.grounded;
                snapshot.indoorSectorId = moveState.sectorId;
                snapshot.indoorEyeSectorId = moveState.eyeSectorId;
                snapshot.indoorSupportFaceIndex = moveState.supportFaceIndex;
            }

            return snapshot;
        };

    const auto snapshotDetails =
        [](const GameplayTraceMovementSnapshot &snapshot)
        {
            return " map=\"" + snapshot.mapName + "\""
                + " scene_kind=" + (snapshot.indoor ? std::string("indoor") : std::string("outdoor"))
                + " party=(" + std::to_string(snapshot.partyX)
                + "," + std::to_string(snapshot.partyY)
                + "," + std::to_string(snapshot.partyZ) + ")"
                + " yaw=" + std::to_string(snapshot.yawRadians)
                + " pitch=" + std::to_string(snapshot.pitchRadians)
                + " game_minutes=" + std::to_string(snapshot.gameMinutes)
                + " tick_ms=" + std::to_string(snapshot.tickMilliseconds)
                + " forward_held=" + (snapshot.forwardHeld ? "true" : "false")
                + " run_walk_modifier=" + (snapshot.runWalkModifierHeld ? "true" : "false")
                + " turbo=" + (snapshot.turboHeld ? "true" : "false")
                + " shift=" + (snapshot.shiftHeld ? "true" : "false")
                + " ctrl=" + (snapshot.ctrlHeld ? "true" : "false")
                + " alt=" + (snapshot.altHeld ? "true" : "false")
                + " held_item_active=" + (snapshot.heldItemActive ? "true" : "false")
                + " held_item_id=" + std::to_string(snapshot.heldItemId)
                + " outdoor_running=" + (snapshot.outdoorRunning ? "true" : "false")
                + " outdoor_flying=" + (snapshot.outdoorFlying ? "true" : "false")
                + " outdoor_water_walk=" + (snapshot.outdoorWaterWalk ? "true" : "false")
                + " outdoor_feather_fall=" + (snapshot.outdoorFeatherFall ? "true" : "false")
                + " outdoor_airborne=" + (snapshot.outdoorAirborne ? "true" : "false")
                + " outdoor_support_kind=" + std::to_string(snapshot.outdoorSupportKind)
                + " outdoor_support_bmodel=" + std::to_string(snapshot.outdoorSupportBModelIndex)
                + " outdoor_support_face=" + std::to_string(snapshot.outdoorSupportFaceIndex)
                + " indoor_grounded=" + (snapshot.indoorGrounded ? "true" : "false")
                + " indoor_sector=" + std::to_string(snapshot.indoorSectorId)
                + " indoor_eye_sector=" + std::to_string(snapshot.indoorEyeSectorId)
                + " indoor_support_face=" + std::to_string(snapshot.indoorSupportFaceIndex);
        };

    if (markerPressed)
    {
        if (!m_traceMarkerLatch)
        {
            ++m_traceMarkerSequence;
            const std::optional<GameplayTraceMovementSnapshot> snapshot = captureSnapshot();
            GAMEPLAY_DEBUG_TRACE(
                "trace_marker index=" + std::to_string(m_traceMarkerSequence)
                + (snapshot.has_value() ? snapshotDetails(*snapshot) : std::string()));
            m_traceMarkerLatch = true;
        }
    }
    else
    {
        m_traceMarkerLatch = false;
    }

    if (startPressed)
    {
        if (!m_traceSnapshotStartLatch)
        {
            ++m_traceMovementCapture.sequence;
            m_traceMovementCapture.armed = true;
            m_traceMovementCapture.hasStart = false;
            m_traceMovementCapture.hasStop = false;
            m_traceMovementCapture.committed = false;
            m_traceMovementCapture.previousForwardHeld = forwardHeld;
            m_traceMovementCapture.start = {};
            m_traceMovementCapture.stop = {};
            m_traceSnapshotStartLatch = true;
        }
    }
    else
    {
        m_traceSnapshotStartLatch = false;
    }

    if (m_traceMovementCapture.armed
        && !m_traceMovementCapture.hasStart
        && forwardHeld
        && !m_traceMovementCapture.previousForwardHeld)
    {
        const std::optional<GameplayTraceMovementSnapshot> snapshot = captureSnapshot();

        if (snapshot.has_value())
        {
            m_traceMovementCapture.start = *snapshot;
            m_traceMovementCapture.hasStart = true;
        }
    }

    if (m_traceMovementCapture.armed
        && m_traceMovementCapture.hasStart
        && !m_traceMovementCapture.hasStop
        && !forwardHeld
        && m_traceMovementCapture.previousForwardHeld)
    {
        const std::optional<GameplayTraceMovementSnapshot> snapshot = captureSnapshot();

        if (snapshot.has_value())
        {
            m_traceMovementCapture.stop = *snapshot;
            m_traceMovementCapture.hasStop = true;
        }
    }

    if (endPressed)
    {
        if (!m_traceSnapshotEndLatch)
        {
            if (m_traceMovementCapture.armed
                && m_traceMovementCapture.hasStart
                && m_traceMovementCapture.hasStop
                && !m_traceMovementCapture.committed)
            {
                const uint64_t durationMilliseconds =
                    m_traceMovementCapture.stop.tickMilliseconds >= m_traceMovementCapture.start.tickMilliseconds
                        ? m_traceMovementCapture.stop.tickMilliseconds - m_traceMovementCapture.start.tickMilliseconds
                        : 0;
                const float deltaGameMinutes =
                    m_traceMovementCapture.stop.gameMinutes - m_traceMovementCapture.start.gameMinutes;

                GAMEPLAY_DEBUG_TRACE(
                    "movement_segment sequence=" + std::to_string(m_traceMovementCapture.sequence)
                    + " input=forward"
                    + " duration_ms=" + std::to_string(durationMilliseconds)
                    + " delta_game_minutes=" + std::to_string(deltaGameMinutes)
                    + " accepted=true");
                GAMEPLAY_DEBUG_TRACE(
                    "movement_segment_snapshot sequence=" + std::to_string(m_traceMovementCapture.sequence)
                    + " label=start"
                    + snapshotDetails(m_traceMovementCapture.start));
                GAMEPLAY_DEBUG_TRACE(
                    "movement_segment_snapshot sequence=" + std::to_string(m_traceMovementCapture.sequence)
                    + " label=stop"
                    + snapshotDetails(m_traceMovementCapture.stop));
                m_traceMovementCapture.committed = true;
            }
            else
            {
                std::string reason = "not_armed";

                if (m_traceMovementCapture.committed)
                {
                    reason = "already_committed";
                }
                else if (m_traceMovementCapture.armed && !m_traceMovementCapture.hasStart)
                {
                    reason = "missing_start";
                }
                else if (m_traceMovementCapture.armed && !m_traceMovementCapture.hasStop)
                {
                    reason = "missing_stop";
                }

                GAMEPLAY_DEBUG_TRACE(
                    "movement_segment_status sequence=" + std::to_string(m_traceMovementCapture.sequence)
                    + " accepted=false"
                    + " reason=" + reason
                    + " armed=" + (m_traceMovementCapture.armed ? "true" : "false")
                    + " has_start=" + (m_traceMovementCapture.hasStart ? "true" : "false")
                    + " has_stop=" + (m_traceMovementCapture.hasStop ? "true" : "false"));
            }
            m_traceSnapshotEndLatch = true;
        }
    }
    else
    {
        m_traceSnapshotEndLatch = false;
    }

    m_traceMovementCapture.previousForwardHeld = forwardHeld;
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

    if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
    {
        return m_indoorGameView.requestQuickSave();
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
        GAMEPLAY_DEBUG_TRACE("save_game_failed path=\"" + path.string() + "\" reason=unavailable");
        reportQuickSaveStatus("Quick save unavailable");
        return false;
    }

    if (!selectedMap->map.runtimeRestrictions.allowSaveGame && !isAutosavePath(path))
    {
        GAMEPLAY_DEBUG_TRACE("save_game_failed path=\"" + path.string() + "\" reason=restricted_map");
        reportQuickSaveStatus("Quick save unavailable here");
        return false;
    }

    captureCurrentSceneState();
    std::optional<GameSaveData> saveData = m_gameSession.buildSaveData();

    if (!saveData)
    {
        GAMEPLAY_DEBUG_TRACE("save_game_failed path=\"" + path.string() + "\" reason=no_save_data");
        reportQuickSaveStatus("Quick save unavailable");
        return false;
    }

    saveData->saveName = saveName;
    saveData->previewBmp = previewBmp;
    saveData->requiredContentPackages = collectRequiredContentPackages(
        *saveData,
        m_gameDataLoader.getItemTable(),
        m_gameDataLoader.getHouseTable(),
        m_gameDataLoader.getLoadedContentPackageSchemas());

    std::string error;

    if (!saveGameDataToPath(path, *saveData, error))
    {
        GAMEPLAY_DEBUG_TRACE(
            "save_game_failed path=\"" + path.string() + "\""
            + " map=\"" + saveData->mapFileName + "\""
            + " reason=\"" + error + "\"");
        reportQuickSaveStatus("Quick save failed: " + error);
        return false;
    }

    m_gameSession.setCurrentSavePath(path);
    LoadGameScreen::invalidateCachedSaveSlots();
    GAMEPLAY_DEBUG_TRACE(
        "save_game_written path=\"" + path.string() + "\""
        + " map=\"" + saveData->mapFileName + "\""
        + " scene_kind=" + sceneKindName(saveData->currentSceneKind)
        + " game_minutes=" + std::to_string(saveData->savedGameMinutes));
    GAMEPLAY_DEBUG_TRACE_BLOCK(
        traceSaveDataStateDump("save", path, *saveData, &m_gameDataLoader.getItemTable());
    );
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
        GAMEPLAY_DEBUG_TRACE("load_game_failed path=\"" + path.string() + "\" reason=unavailable");
        reportQuickSaveStatus("Quick load unavailable");
        return false;
    }

    if (!ensureCommonGameDataLoaded())
    {
        GAMEPLAY_DEBUG_TRACE("load_game_failed path=\"" + path.string() + "\" reason=common_data_unavailable");
        reportQuickSaveStatus("Quick load unavailable");
        return false;
    }

    GAMEPLAY_DEBUG_TRACE(
        "load_game_started path=\"" + path.string() + "\""
        + " initialize_view=" + (initializeView ? "true" : "false"));
    beginLoadingOverlay();

    std::string error;
    const std::optional<GameSaveData> saveData = loadGameDataFromPath(path, error);

    if (!saveData)
    {
        cancelLoadingOverlay();
        GAMEPLAY_DEBUG_TRACE(
            "load_game_failed path=\"" + path.string() + "\""
            + " reason=\"" + error + "\"");
        reportQuickSaveStatus("Quick load failed: " + error);
        return false;
    }

    if (!validateRequiredContentPackages(
            *saveData,
            m_gameDataLoader.getItemTable(),
            m_gameDataLoader.getHouseTable(),
            m_gameDataLoader.getLoadedContentPackageSchemas(),
            error))
    {
        cancelLoadingOverlay();
        GAMEPLAY_DEBUG_TRACE(
            "load_game_failed path=\"" + path.string() + "\""
            + " reason=\"" + error + "\"");
        reportQuickSaveStatus("Quick load failed: " + error);
        return false;
    }

    GAMEPLAY_DEBUG_TRACE_BLOCK(
        traceSaveDataStateDump("load_file", path, *saveData, &m_gameDataLoader.getItemTable());
    );
    renderLoadingOverlayProgress(20);

    m_gameSession.restoreFromSaveData(*saveData);
    m_gameSession.setCurrentSavePath(path);

    renderLoadingOverlayProgress(35);

    const bool previousLoadingSavedGameRuntime = m_loadingSavedGameRuntime;
    m_loadingSavedGameRuntime = true;
    const bool mapLoaded = loadCurrentSessionMap(
        initializeView,
        [this](int localProgress)
        {
            renderLoadingOverlayProgress(remapLoadingProgress(localProgress, 40, 85));
        });
    m_loadingSavedGameRuntime = previousLoadingSavedGameRuntime;

    if (!mapLoaded)
    {
        cancelLoadingOverlay();
        GAMEPLAY_DEBUG_TRACE(
            "load_game_failed path=\"" + path.string() + "\""
            + " map=\"" + saveData->mapFileName + "\""
            + " reason=runtime_init_failed");
        reportQuickSaveStatus("Quick load failed: runtime init failed");
        return false;
    }

    renderLoadingOverlayProgress(90);

    if (!applyCurrentSessionToRuntime(initializeView))
    {
        cancelLoadingOverlay();
        GAMEPLAY_DEBUG_TRACE(
            "load_game_failed path=\"" + path.string() + "\""
            + " map=\"" + saveData->mapFileName + "\""
            + " reason=runtime_apply_failed");
        reportQuickSaveStatus("Quick load failed: runtime apply failed");
        return false;
    }

    m_gameSession.restoreHeldInventoryItemFromSaveData(*saveData);

    renderLoadingOverlayProgress(95);
    completeLoadingOverlay();
    GAMEPLAY_DEBUG_TRACE(
        "load_game_applied path=\"" + path.string() + "\""
        + " map=\"" + m_gameSession.currentMapFileName() + "\""
        + " scene_kind=" + sceneKindName(m_gameSession.currentSceneKind())
        + " game_minutes=" + std::to_string(m_gameSession.gameMinutes()));
    if (const std::optional<GameSaveData> appliedSaveData = m_gameSession.buildSaveData())
    {
        GAMEPLAY_DEBUG_TRACE_BLOCK(
            traceSaveDataStateDump("load_applied", path, *appliedSaveData, &m_gameDataLoader.getItemTable());
        );
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

    std::unique_ptr<MainMenuScreen> pScreen = std::make_unique<MainMenuScreen>(
        *m_pAssetFileSystem,
        &m_gameAudioSystem,
        [this]()
        {
            GAMEPLAY_DEBUG_TRACE("menu_action action=new_game source=main_menu");
            if (!ensureCommonGameDataLoaded())
            {
                return;
            }
            openNewGameScreen("main_menu");
        },
        [this]()
        {
            GAMEPLAY_DEBUG_TRACE("menu_action action=load_game source=main_menu");
            if (!ensureCommonGameDataLoaded())
            {
                return;
            }
            openLoadGameScreen(false, "main_menu");
        },
        [this]()
        {
            requestApplicationQuit();
        });

    pScreen->prepareForFirstFrame();

    m_gameAudioSystem.setBackgroundMusicTrack(MainMenuMusicTrack);
    m_mainMenuRenderedFrameCount = 0;
    m_deferredMainMenuChildWarmupStage = m_mainMenuChildScreensPrepared ? 0 : 1;
    m_screenManager.setActiveScreen(std::move(pScreen));
}

void GameApplication::openLoadGameScreen(bool returnToGameplayMenu, const std::string &source)
{
    if (m_pAssetFileSystem == nullptr)
    {
        return;
    }

    if (!ensureCommonGameDataLoaded())
    {
        return;
    }

    GAMEPLAY_DEBUG_TRACE(
        "load_game_screen_opened source=\"" + source + "\""
        + " return_to_gameplay_menu=" + (returnToGameplayMenu ? "true" : "false"));

    std::unique_ptr<LoadGameScreen> pScreen = std::make_unique<LoadGameScreen>(
        *m_pAssetFileSystem,
        m_gameSession.data(),
        [this](const std::filesystem::path &path) -> bool
        {
            return loadSessionFromPath(path);
        },
        [this, returnToGameplayMenu]()
        {
            if (returnToGameplayMenu)
            {
                m_screenManager.setActiveScreen(nullptr);

                if (m_pMapSceneRuntime != nullptr)
                {
                    m_screenManager.setCurrentMode(
                        m_pMapSceneRuntime->kind() == SceneKind::Indoor
                            ? AppMode::GameplayIndoor
                            : AppMode::GameplayOutdoor);
                }

                if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
                {
                    m_indoorGameView.reopenMenuScreen();
                }
                else
                {
                    m_outdoorGameView.reopenMenuScreen();
                }
            }
            else
            {
                openMainMenuScreen();
            }
        });

    if (!m_mainMenuChildScreensPrepared)
    {
        pScreen->prepareForFirstFrame();
    }

    m_screenManager.setActiveScreen(std::move(pScreen));
}

void GameApplication::openNewGameScreen(const std::string &source)
{
    if (m_pAssetFileSystem == nullptr)
    {
        return;
    }

    if (!ensureCommonGameDataLoaded())
    {
        return;
    }

    GAMEPLAY_DEBUG_TRACE("new_game_screen_opened source=\"" + source + "\"");

    std::unique_ptr<NewGameScreen> pScreen = std::make_unique<NewGameScreen>(
        *m_pAssetFileSystem,
        &m_gameAudioSystem,
        m_gameSession.data(),
        m_settings.newGameGodLich,
        IncludeGodLichCharacterCreationCandidate,
        m_settings.allowIncompleteCharacterCreation,
        [this](const std::vector<Character> &characters, uint32_t continentId, bool preserveDebugLoadout)
        {
            startNewSessionFromCharacterCreation(characters, continentId, preserveDebugLoadout, true);
        },
        [this]()
        {
            openMainMenuScreen();
        });

    if (!m_mainMenuChildScreensPrepared)
    {
        pScreen->prepareForFirstFrame();
    }

    m_gameAudioSystem.stopBackgroundMusicImmediate();
    m_screenManager.setActiveScreen(std::move(pScreen));
}

std::optional<uint32_t> GameApplication::activeWorldContinentId() const
{
    const std::string activeWorldId = normalizeWorldId(m_activeWorldManifest.id);

    if (activeWorldId == "mm8")
    {
        return 1u;
    }

    if (activeWorldId == "mm7")
    {
        return 2u;
    }

    if (activeWorldId == "mm6")
    {
        return 3u;
    }

    return std::nullopt;
}

std::optional<GameApplication::MapStartDestination> GameApplication::resolveContinentStartDestination(
    uint32_t continentId) const
{
    const MergedContinentSettingEntry *pContinentSetting =
        m_gameDataLoader.getMergedContinentSettingTable().findById(continentId);

    if (pContinentSetting == nullptr || trimCopy(pContinentSetting->deathMap1).empty())
    {
        return std::nullopt;
    }

    return MapStartDestination{
        .mapFileName = normalizedDeathMapName(pContinentSetting->deathMap1),
        .start = DebugMapJumpStart{
            .x = pContinentSetting->deathMap1X,
            .y = pContinentSetting->deathMap1Y,
            .z = pContinentSetting->deathMap1Z,
            .directionYawUnits = pContinentSetting->deathMap1Direction,
        },
    };
}

GameApplication::MapStartDestination GameApplication::resolveStartupDestination() const
{
    if (!m_config.startupMapFileOverride.empty())
    {
        return MapStartDestination{.mapFileName = m_config.startupMapFileOverride};
    }

    if (!m_settings.startMapFile.empty())
    {
        return MapStartDestination{.mapFileName = m_settings.startMapFile};
    }

    const std::string manifestStartMap = m_activeWorldManifest.start.mapFileName.empty()
        ? DefaultStartupMapFile
        : m_activeWorldManifest.start.mapFileName;

    const std::optional<uint32_t> continentId = activeWorldContinentId();

    if (continentId.has_value())
    {
        const std::optional<MapStartDestination> continentStart =
            resolveContinentStartDestination(*continentId);

        if (continentStart.has_value() && sameMapFileName(continentStart->mapFileName, manifestStartMap))
        {
            return *continentStart;
        }
    }

    return MapStartDestination{.mapFileName = manifestStartMap};
}

std::string GameApplication::resolveStartupMapFile() const
{
    return resolveStartupDestination().mapFileName;
}

void GameApplication::applyMapStartDestination(const MapStartDestination &destination)
{
    if (!destination.start.has_value())
    {
        return;
    }

    if (!destination.mapFileName.empty()
        && !sameMapFileName(destination.mapFileName, m_gameSession.currentMapFileName()))
    {
        return;
    }

    const DebugMapJumpStart &start = *destination.start;

    if (m_pMapSceneRuntime != nullptr
        && m_pMapSceneRuntime->kind() == SceneKind::Outdoor
        && m_pOutdoorPartyRuntime != nullptr)
    {
        m_pOutdoorPartyRuntime->teleportTo(
            static_cast<float>(start.x),
            static_cast<float>(start.y),
            static_cast<float>(start.z));
    }
    else if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
    {
        IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
        pIndoorRuntime->partyRuntime().teleportPartyPosition(
            static_cast<float>(start.x),
            static_cast<float>(start.y),
            static_cast<float>(start.z));
    }

    const int32_t normalizedYawUnits = ((start.directionYawUnits % 2048) + 2048) % 2048;
    const int32_t directionDegrees = normalizedYawUnits * 360 / 2048;
    const float yawRadians = mapMoveHeadingDegreesToYawRadians(directionDegrees);

    if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Outdoor)
    {
        m_outdoorGameView.setCameraAngles(yawRadians, m_outdoorGameView.cameraPitchRadians());
    }
    else if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
    {
        m_indoorRenderer.setCameraAngles(yawRadians, m_indoorRenderer.cameraPitchRadians());
    }
}

bool GameApplication::startNewSession(std::optional<uint32_t> rosterId, bool initializeView)
{
    if (m_pAssetFileSystem == nullptr)
    {
        std::cerr << "GameApplication: startNewSession has no asset filesystem\n";
        return false;
    }

    if (!ensureCommonGameDataLoaded())
    {
        std::cerr << "GameApplication: startNewSession failed to load common gameplay data\n";
        return false;
    }

    m_gameAudioSystem.stopBackgroundMusicImmediate();
    m_screenManager.setActiveScreen(nullptr);
    m_gameSession.gameplayScreenRuntime().clearSharedUiRuntime();
    shutdownRenderer();
    m_gameSession.clear();
    m_gameSession.clearCurrentSavePath();
    m_gameSession.setCurrentSceneKind(SceneKind::Outdoor);
    const MapStartDestination startupDestination = resolveStartupDestination();
    m_gameSession.setCurrentMapFileName(startupDestination.mapFileName);

    const bool shouldSeedParty = rosterId.has_value() || m_settings.preseedParty;
    std::optional<uint32_t> effectiveRosterId = rosterId;

    if (!effectiveRosterId.has_value() && m_settings.preseedParty && m_settings.partySeedRosterId != 0)
    {
        effectiveRosterId = m_settings.partySeedRosterId;
    }

    if (shouldSeedParty)
    {
        Party &party = ensureSessionPartyState();
        const RosterEntry *pRosterEntry =
            effectiveRosterId.has_value() ? m_gameDataLoader.getRosterTable().get(*effectiveRosterId) : nullptr;

        seedSimulatedPartyFromRoster(
            party,
            m_gameDataLoader.getRosterTable(),
            effectiveRosterId.has_value() && pRosterEntry != nullptr ? effectiveRosterId : std::nullopt);
        seedDebugWandsIntoParty(party, m_gameDataLoader.getItemTable());
        setDebugTownPortalUnlocks(party, true);
    }

    if (!loadCurrentSessionMap(initializeView))
    {
        std::cerr
            << "GameApplication: startNewSession failed to load configured startup map "
            << m_gameSession.currentMapFileName()
            << '\n';

        const std::string fallbackStartupMapFile = m_activeWorldManifest.start.mapFileName.empty()
            ? DefaultStartupMapFile
            : m_activeWorldManifest.start.mapFileName;

        if (m_gameSession.currentMapFileName() != fallbackStartupMapFile)
        {
            m_gameSession.setCurrentMapFileName(fallbackStartupMapFile);

            if (loadCurrentSessionMap(initializeView))
            {
                // Use the world manifest startup map when the configured one cannot be loaded.
                std::cerr
                    << "GameApplication: startNewSession fell back to world startup map "
                    << fallbackStartupMapFile
                    << '\n';
            }
            else
            {
                std::cerr
                    << "GameApplication: startNewSession fallback startup map also failed "
                    << fallbackStartupMapFile
                    << '\n';
                openMainMenuScreen();
                return false;
            }
        }
        else
        {
            std::cerr << "GameApplication: startNewSession default startup map failed without fallback\n";
            openMainMenuScreen();
            return false;
        }
    }

    if (m_pMapSceneRuntime == nullptr)
    {
        std::cerr
            << "GameApplication: startNewSession expected active scene runtime after startup map load, but none exists\n";
        openMainMenuScreen();
        return false;
    }

    applyCurrentSettingsToActiveRuntime();
    applyMapStartDestination(startupDestination);
    applyStartupDebugSettingsToActiveRuntime();
    synchronizeSessionFromRuntime();
    return true;
}

bool GameApplication::startNewSessionFromCharacterCreation(
    const std::vector<Character> &characters,
    bool initializeView)
{
    return startNewSessionFromCharacterCreation(characters, 0, false, initializeView);
}

bool GameApplication::startNewSessionFromCharacterCreation(
    const std::vector<Character> &characters,
    uint32_t continentId,
    bool preserveDebugLoadout,
    bool initializeView)
{
    if (m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    if (!ensureCommonGameDataLoaded())
    {
        std::cerr << "GameApplication: startNewSessionFromCharacterCreation failed to load common gameplay data\n";
        return false;
    }

    m_gameAudioSystem.stopBackgroundMusicImmediate();
    m_screenManager.setActiveScreen(nullptr);
    beginLoadingOverlay();
    m_gameSession.gameplayScreenRuntime().clearSharedUiRuntime();
    shutdownRenderer();
    m_gameSession.clear();
    m_gameSession.clearCurrentSavePath();
    m_gameSession.setCurrentSceneKind(SceneKind::Outdoor);
    const std::optional<MapStartDestination> continentStartDestination =
        continentId != 0 ? resolveContinentStartDestination(continentId) : std::nullopt;
    const MapStartDestination startupDestination =
        continentStartDestination.value_or(resolveStartupDestination());
    const MergedContinentSettingEntry *pContinentSetting =
        continentId != 0 ? m_gameDataLoader.getMergedContinentSettingTable().findById(continentId) : nullptr;
    GAMEPLAY_DEBUG_TRACE(
        "new_game_starting continent_id=" + std::to_string(continentId)
        + " continent_note=\"" + (pContinentSetting != nullptr ? pContinentSetting->note : std::string()) + "\""
        + " map=\"" + startupDestination.mapFileName + "\""
        + " start_override=" + (startupDestination.start.has_value() ? "true" : "false")
        + " member_count=" + std::to_string(characters.size()));
    m_gameSession.setCurrentMapFileName(startupDestination.mapFileName);
    PartySeed seed = {};
    seed.gold = 200;
    seed.food = 5;

    for (const Character &character : characters)
    {
        seed.members.push_back(
            buildFreshCreatedCharacter(
                character,
                m_gameDataLoader.getClassMultiplierTable(),
                m_gameDataLoader.getItemTable(),
                m_gameDataLoader.getStandardItemEnchantTable(),
                m_gameDataLoader.getSpecialItemEnchantTable(),
                preserveDebugLoadout));
    }

    Party &sessionParty = ensureSessionPartyState();
    sessionParty.seed(seed);
    setDebugTownPortalUnlocks(sessionParty, false);
    renderLoadingOverlayProgress(15);

    if (!loadCurrentSessionMap(
            initializeView,
            [this](int localProgress)
            {
                renderLoadingOverlayProgress(remapLoadingProgress(localProgress, 20, 80));
            }))
    {
        cancelLoadingOverlay();
        openMainMenuScreen();
        return false;
    }

    if (m_pOutdoorPartyRuntime == nullptr)
    {
        cancelLoadingOverlay();
        openMainMenuScreen();
        return false;
    }

    renderLoadingOverlayProgress(90);
    applyCurrentSettingsToActiveRuntime();
    applyMapStartDestination(startupDestination);
    synchronizeSessionFromRuntime();
    GAMEPLAY_DEBUG_TRACE(
        "new_game_started continent_id=" + std::to_string(continentId)
        + " continent_note=\"" + (pContinentSetting != nullptr ? pContinentSetting->note : std::string()) + "\""
        + " map=\"" + m_gameSession.currentMapFileName() + "\""
        + " party=("
        + (m_gameSession.activeWorldRuntime() != nullptr
            ? std::to_string(m_gameSession.activeWorldRuntime()->partyX())
                + "," + std::to_string(m_gameSession.activeWorldRuntime()->partyY())
                + "," + std::to_string(m_gameSession.activeWorldRuntime()->partyFootZ())
            : std::string("0,0,0"))
        + ")");
    GAMEPLAY_DEBUG_TRACE_BLOCK(
        tracePartySnapshot(
            "new_game_started",
            sessionParty.snapshot(),
            &m_gameDataLoader.getItemTable());
    );
    renderLoadingOverlayProgress(95);
    completeLoadingOverlay();
    return true;
}

bool GameApplication::loadSessionFromPath(const std::filesystem::path &path)
{
    if (quickLoadFromPath(path, true))
    {
        m_screenManager.setActiveScreen(nullptr);
        return true;
    }

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
    if (EventRuntimeState *pEventRuntimeState = m_gameplayController.eventRuntimeState())
    {
        pEventRuntimeState->lastActivationResult = status;
    }
}

void GameApplication::renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds)
{
    const bool gameplayLoaded =
        !m_loadingOverlayActive
        && m_screenManager.activeScreen() == nullptr
        && m_pMapSceneRuntime != nullptr
        && m_gameSession.activeWorldRuntime() != nullptr;
    setGprofProfilingEnabled(gameplayLoaded);

    const bool collectFrameDiagnostics = m_config.performanceTrace;
    const uint64_t frameBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
    std::optional<FramePerformanceDiagnostics> frameDiagnosticsAtStart;

    if (collectFrameDiagnostics)
    {
        frameDiagnosticsAtStart = m_framePerformanceDiagnostics;
        m_gameSession.beginFramePerformanceDiagnostics(true);
        ++m_framePerformanceDiagnostics.frames;
    }

    const auto recordFrameDiagnostics =
        [&](uint64_t &field, uint64_t beginTickCount)
    {
        if (collectFrameDiagnostics)
        {
            field += SDL_GetTicksNS() - beginTickCount;
        }
    };
    const auto finishFrameDiagnostics =
        [&]()
    {
        if (collectFrameDiagnostics)
        {
            m_framePerformanceDiagnostics.totalNanoseconds += SDL_GetTicksNS() - frameBeginTickCount;
            FramePerformanceDiagnostics currentFrameDiagnostics = {};
            currentFrameDiagnostics.frames =
                m_framePerformanceDiagnostics.frames - frameDiagnosticsAtStart->frames;
            currentFrameDiagnostics.totalNanoseconds =
                m_framePerformanceDiagnostics.totalNanoseconds - frameDiagnosticsAtStart->totalNanoseconds;
            currentFrameDiagnostics.pendingDebugMapJumpNanoseconds =
                m_framePerformanceDiagnostics.pendingDebugMapJumpNanoseconds
                - frameDiagnosticsAtStart->pendingDebugMapJumpNanoseconds;
            currentFrameDiagnostics.debugConsoleBeginNanoseconds =
                m_framePerformanceDiagnostics.debugConsoleBeginNanoseconds
                - frameDiagnosticsAtStart->debugConsoleBeginNanoseconds;
            currentFrameDiagnostics.inputNanoseconds =
                m_framePerformanceDiagnostics.inputNanoseconds - frameDiagnosticsAtStart->inputNanoseconds;
            currentFrameDiagnostics.activeScreenNanoseconds =
                m_framePerformanceDiagnostics.activeScreenNanoseconds
                - frameDiagnosticsAtStart->activeScreenNanoseconds;
            currentFrameDiagnostics.pendingStateNanoseconds =
                m_framePerformanceDiagnostics.pendingStateNanoseconds
                - frameDiagnosticsAtStart->pendingStateNanoseconds;
            currentFrameDiagnostics.gameplayUpdateNanoseconds =
                m_framePerformanceDiagnostics.gameplayUpdateNanoseconds
                - frameDiagnosticsAtStart->gameplayUpdateNanoseconds;
            currentFrameDiagnostics.worldUpdateNanoseconds =
                m_framePerformanceDiagnostics.worldUpdateNanoseconds
                - frameDiagnosticsAtStart->worldUpdateNanoseconds;
            currentFrameDiagnostics.renderWorldNanoseconds =
                m_framePerformanceDiagnostics.renderWorldNanoseconds
                - frameDiagnosticsAtStart->renderWorldNanoseconds;
            currentFrameDiagnostics.renderGameplayUiNanoseconds =
                m_framePerformanceDiagnostics.renderGameplayUiNanoseconds
                - frameDiagnosticsAtStart->renderGameplayUiNanoseconds;
            currentFrameDiagnostics.audioNanoseconds =
                m_framePerformanceDiagnostics.audioNanoseconds - frameDiagnosticsAtStart->audioNanoseconds;
            currentFrameDiagnostics.postWorldNanoseconds =
                m_framePerformanceDiagnostics.postWorldNanoseconds
                - frameDiagnosticsAtStart->postWorldNanoseconds;
            currentFrameDiagnostics.debugConsoleRenderNanoseconds =
                m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds
                - frameDiagnosticsAtStart->debugConsoleRenderNanoseconds;
            currentFrameDiagnostics.performanceTraceLogNanoseconds =
                m_framePerformanceDiagnostics.performanceTraceLogNanoseconds
                - frameDiagnosticsAtStart->performanceTraceLogNanoseconds;
            currentFrameDiagnostics.activeScreenFrames =
                m_framePerformanceDiagnostics.activeScreenFrames - frameDiagnosticsAtStart->activeScreenFrames;
            currentFrameDiagnostics.gameplayWorldFrames =
                m_framePerformanceDiagnostics.gameplayWorldFrames - frameDiagnosticsAtStart->gameplayWorldFrames;
            const uint64_t performanceLogBeginTickCount = SDL_GetTicksNS();
            const bool loggedPerformanceDiagnostics = logFramePerformanceDiagnostics(SDL_GetTicks());
            const uint64_t performanceLogNanoseconds = SDL_GetTicksNS() - performanceLogBeginTickCount;
            currentFrameDiagnostics.performanceTraceLogNanoseconds += performanceLogNanoseconds;
            currentFrameDiagnostics.totalNanoseconds += performanceLogNanoseconds;

            if (!loggedPerformanceDiagnostics)
            {
                m_framePerformanceDiagnostics.performanceTraceLogNanoseconds += performanceLogNanoseconds;
                m_framePerformanceDiagnostics.totalNanoseconds += performanceLogNanoseconds;
            }

            const uint64_t hitchThresholdNanoseconds = static_cast<uint64_t>(
                std::max(0.1f, m_settings.hitchThresholdMilliseconds) * 1000000.0f);

            if (currentFrameDiagnostics.totalNanoseconds >= hitchThresholdNanoseconds)
            {
                logFrameHitchDiagnostics(currentFrameDiagnostics);
            }
        }
    };

    m_lastFrameWidth = width;
    m_lastFrameHeight = height;

    const uint64_t pendingDebugMapJumpBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;

    if (processPendingDebugMapJump())
    {
        recordFrameDiagnostics(
            m_framePerformanceDiagnostics.pendingDebugMapJumpNanoseconds,
            pendingDebugMapJumpBeginTickCount);
        finishFrameDiagnostics();
        return;
    }

    recordFrameDiagnostics(
        m_framePerformanceDiagnostics.pendingDebugMapJumpNanoseconds,
        pendingDebugMapJumpBeginTickCount);

    const uint64_t debugConsoleBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
    beginDebugConsoleFrame();
    const bool debugConsoleOpen = m_debugConsole.wantsGameplayInputBlocked();
    const bool debugConsoleFreezesGameplay = m_debugConsole.freezesGameplay();
    recordFrameDiagnostics(
        m_framePerformanceDiagnostics.debugConsoleBeginNanoseconds,
        debugConsoleBeginTickCount);

    const uint64_t inputBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
    if (m_gameSession.consumeRelativeMouseMotionResetRequest())
    {
        m_gameInputSystem.resetRelativeMouseMotion();
    }

    const IScreen *pActiveScreenForInput = m_screenManager.activeScreen();
    const GameplayScreenState::PendingSpellTargetState &pendingSpellTargetForInput =
        m_gameSession.gameplayScreenState().pendingSpellTarget();
    const bool mobileGameplayTouchControlsEnabled =
        pActiveScreenForInput == nullptr
        && !pendingSpellTargetForInput.active
        && m_gameSession.gameplayScreenRuntime().currentHudScreenState() == GameplayHudScreenState::Gameplay;
    const bool mobileJumpGestureEnabled =
        mobileGameplayTouchControlsEnabled
        && !m_gameSession.turnBasedCombatRuntime().active();
    const bool mobileFlightControlsEnabled =
        mobileGameplayTouchControlsEnabled
        && m_gameSession.gameplayScreenRuntime().mobileFlightControlsAvailable();
    const bool mobileInspectControlEnabled =
        pActiveScreenForInput == nullptr
        && m_gameSession.gameplayScreenRuntime().mobileInspectControlAvailable();

    m_gameInputSystem.updateFromEngineInput(
        width,
        height,
        mouseWheelDelta,
        m_settings,
        debugConsoleOpen,
        mobileGameplayTouchControlsEnabled,
        mobileJumpGestureEnabled,
        mobileFlightControlsEnabled,
        mobileInspectControlEnabled);
    m_gameSession.bindCurrentGameplayInputFrame(&m_gameInputSystem.frame());
    recordFrameDiagnostics(m_framePerformanceDiagnostics.inputNanoseconds, inputBeginTickCount);

    if (debugConsoleFreezesGameplay)
    {
        m_gameSession.clearSharedInputFrameResult();
    }
    else
    {
        processPendingArcomageGame();
    }

    if (IScreen *pActiveScreen = m_screenManager.activeScreen())
    {
        updateDeferredStartupLoads();

        const uint64_t activeScreenBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        const bool renderedMainMenu = pActiveScreen->mode() == AppMode::MainMenu;
        m_screenManager.beginActiveScreenRender();
        pActiveScreen->renderFrame(width, height, m_gameInputSystem.frame(), deltaSeconds);
        m_screenManager.endActiveScreenRender();
        if (renderedMainMenu && m_mainMenuRenderedFrameCount < std::numeric_limits<uint32_t>::max())
        {
            ++m_mainMenuRenderedFrameCount;
        }
        handleCompletedPartyDefeatScreen();
        handleCompletedEventMovieScreen();
        handleCompletedWinGameScreen();
        handleCompletedArcomageScreen();
        recordFrameDiagnostics(m_framePerformanceDiagnostics.activeScreenNanoseconds, activeScreenBeginTickCount);

        if (collectFrameDiagnostics)
        {
            ++m_framePerformanceDiagnostics.activeScreenFrames;
        }

        const uint64_t audioBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        m_gameAudioSystem.update(0.0f, 0.0f, 0.0f, deltaSeconds);
        recordFrameDiagnostics(m_framePerformanceDiagnostics.audioNanoseconds, audioBeginTickCount);
        const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        renderDebugConsoleFrame(width, height);
        recordFrameDiagnostics(
            m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
            debugConsoleRenderBeginTickCount);
        finishFrameDiagnostics();
        return;
    }

    const uint64_t pendingStateBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
    updateQuickSaveInput();
    updateDoubleSpeedInput();
    updateGameplayTraceSnapshotHotkeys();

    if (processPendingPartyDefeat())
    {
        if (IScreen *pActiveScreen = m_screenManager.activeScreen())
        {
            pActiveScreen->renderFrame(width, height, m_gameInputSystem.frame(), deltaSeconds);
            handleCompletedPartyDefeatScreen();
            handleCompletedEventMovieScreen();
            handleCompletedWinGameScreen();
        }

        recordFrameDiagnostics(m_framePerformanceDiagnostics.pendingStateNanoseconds, pendingStateBeginTickCount);
        const uint64_t audioBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        m_gameAudioSystem.update(0.0f, 0.0f, 0.0f, deltaSeconds);
        recordFrameDiagnostics(m_framePerformanceDiagnostics.audioNanoseconds, audioBeginTickCount);
        const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        renderDebugConsoleFrame(width, height);
        recordFrameDiagnostics(
            m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
            debugConsoleRenderBeginTickCount);
        finishFrameDiagnostics();
        return;
    }

    if (processPendingWinGame())
    {
        if (IScreen *pActiveScreen = m_screenManager.activeScreen())
        {
            pActiveScreen->renderFrame(width, height, m_gameInputSystem.frame(), deltaSeconds);
            handleCompletedEventMovieScreen();
            handleCompletedWinGameScreen();
        }

        recordFrameDiagnostics(m_framePerformanceDiagnostics.pendingStateNanoseconds, pendingStateBeginTickCount);
        const uint64_t audioBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        m_gameAudioSystem.update(0.0f, 0.0f, 0.0f, deltaSeconds);
        recordFrameDiagnostics(m_framePerformanceDiagnostics.audioNanoseconds, audioBeginTickCount);
        const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        renderDebugConsoleFrame(width, height);
        recordFrameDiagnostics(
            m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
            debugConsoleRenderBeginTickCount);
        finishFrameDiagnostics();
        return;
    }

    if (processPendingEventMovie())
    {
        if (IScreen *pActiveScreen = m_screenManager.activeScreen())
        {
            pActiveScreen->renderFrame(width, height, m_gameInputSystem.frame(), deltaSeconds);
            handleCompletedEventMovieScreen();
            handleCompletedWinGameScreen();
        }

        recordFrameDiagnostics(m_framePerformanceDiagnostics.pendingStateNanoseconds, pendingStateBeginTickCount);
        const uint64_t audioBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        m_gameAudioSystem.update(0.0f, 0.0f, 0.0f, deltaSeconds);
        recordFrameDiagnostics(m_framePerformanceDiagnostics.audioNanoseconds, audioBeginTickCount);
        const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        renderDebugConsoleFrame(width, height);
        recordFrameDiagnostics(
            m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
            debugConsoleRenderBeginTickCount);
        finishFrameDiagnostics();
        return;
    }

    if (processPendingReturnToMainMenu())
    {
        if (IScreen *pActiveScreen = m_screenManager.activeScreen())
        {
            pActiveScreen->renderFrame(width, height, m_gameInputSystem.frame(), deltaSeconds);
        }

        recordFrameDiagnostics(m_framePerformanceDiagnostics.pendingStateNanoseconds, pendingStateBeginTickCount);
        const uint64_t audioBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        m_gameAudioSystem.update(0.0f, 0.0f, 0.0f, deltaSeconds);
        recordFrameDiagnostics(m_framePerformanceDiagnostics.audioNanoseconds, audioBeginTickCount);
        const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        renderDebugConsoleFrame(width, height);
        recordFrameDiagnostics(
            m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
            debugConsoleRenderBeginTickCount);
        finishFrameDiagnostics();
        return;
    }

    const std::optional<MapAssetInfo> &selectedMap = m_gameDataLoader.getSelectedMap();
    const bool *pKeyboardState = m_gameInputSystem.frame().keyboardState();
    bool skipGameplayUpdateAfterInputPrompt = false;

    if (m_skipGameplayUpdateUntilPromptSubmitKeysReleased)
    {
        skipGameplayUpdateAfterInputPrompt =
            pKeyboardState[SDL_SCANCODE_RETURN]
            || pKeyboardState[SDL_SCANCODE_KP_ENTER]
            || pKeyboardState[SDL_SCANCODE_SPACE];

        if (!skipGameplayUpdateAfterInputPrompt)
        {
            m_skipGameplayUpdateUntilPromptSubmitKeysReleased = false;
        }
    }

    recordFrameDiagnostics(m_framePerformanceDiagnostics.pendingStateNanoseconds, pendingStateBeginTickCount);
    const float scaledGameplayDeltaSeconds = gameplayDeltaSeconds(deltaSeconds);

    if (!debugConsoleFreezesGameplay && !skipGameplayUpdateAfterInputPrompt)
    {
        const uint64_t gameplayUpdateBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        m_gameSession.updateGameplay(m_gameInputSystem.frame(), scaledGameplayDeltaSeconds, collectFrameDiagnostics);
        const float turnBasedGameMinutes =
            m_gameSession.turnBasedCombatRuntime().consumePendingGameTimeAdvanceMinutes();

        if (turnBasedGameMinutes > 0.0f)
        {
            m_gameplayController.advanceTurnBasedGameMinutes(turnBasedGameMinutes);
        }

        recordFrameDiagnostics(m_framePerformanceDiagnostics.gameplayUpdateNanoseconds, gameplayUpdateBeginTickCount);
    }

    const uint64_t pendingPromptBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;

    if (!debugConsoleFreezesGameplay)
    {
        updatePendingInputPrompt();
        processPendingDimensionDoorOverlay();
    }
    recordFrameDiagnostics(m_framePerformanceDiagnostics.pendingStateNanoseconds, pendingPromptBeginTickCount);

    IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();

    if (pWorldRuntime != nullptr && m_pMapSceneRuntime != nullptr && selectedMap)
    {
        const GameplaySharedInputFrameResult &sharedInput = m_gameSession.sharedInputFrameResult();
        const bool pendingSpellTargetActive = m_gameSession.gameplayScreenState().pendingSpellTarget().active;
        const bool rightMouseInspectPauseActive = m_gameInputSystem.frame().rightMouseButton.held;
        const bool gameplayWorldPaused =
            sharedInput.worldInputBlocked
            || pendingSpellTargetActive
            || m_gameSession.sharedWorldInteractionBlockedThisFrame()
            || debugConsoleFreezesGameplay
            || rightMouseInspectPauseActive;

        if (!gameplayWorldPaused)
        {
            const uint64_t worldUpdateBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
            pWorldRuntime->updateWorld(scaledGameplayDeltaSeconds);
            recordFrameDiagnostics(m_framePerformanceDiagnostics.worldUpdateNanoseconds, worldUpdateBeginTickCount);
        }

        const uint64_t postWorldBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        m_gameSession.consumePendingGameplayAudioRequests();
        recordFrameDiagnostics(m_framePerformanceDiagnostics.postWorldNanoseconds, postWorldBeginTickCount);
        const uint64_t renderWorldBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        const float worldRenderDeltaSeconds = gameplayWorldPaused ? deltaSeconds : scaledGameplayDeltaSeconds;
        pWorldRuntime->renderWorld(width, height, m_gameInputSystem.frame(), worldRenderDeltaSeconds);
        recordFrameDiagnostics(m_framePerformanceDiagnostics.renderWorldNanoseconds, renderWorldBeginTickCount);
        const uint64_t renderGameplayUiBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        m_gameSession.renderGameplayUi(width, height);
        recordFrameDiagnostics(
            m_framePerformanceDiagnostics.renderGameplayUiNanoseconds,
            renderGameplayUiBeginTickCount);

        if (collectFrameDiagnostics)
        {
            ++m_framePerformanceDiagnostics.gameplayWorldFrames;
        }

        const uint64_t postRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        if (m_gameSession.consumeRelativeMouseMotionResetRequest())
        {
            m_gameInputSystem.resetRelativeMouseMotion();
        }

        if (m_gameSession.consumePendingOpenNewGameScreenRequest())
        {
            GAMEPLAY_DEBUG_TRACE("menu_action action=new_game source=gameplay_menu");
            openNewGameScreen("gameplay_menu");
            recordFrameDiagnostics(m_framePerformanceDiagnostics.postWorldNanoseconds, postRenderBeginTickCount);
            const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
            renderDebugConsoleFrame(width, height);
            recordFrameDiagnostics(
                m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
                debugConsoleRenderBeginTickCount);
            finishFrameDiagnostics();
            return;
        }

        if (m_gameSession.consumePendingOpenLoadGameScreenRequest())
        {
            GAMEPLAY_DEBUG_TRACE("menu_action action=load_game source=gameplay_menu");
            openLoadGameScreen(true, "gameplay_menu");
            recordFrameDiagnostics(m_framePerformanceDiagnostics.postWorldNanoseconds, postRenderBeginTickCount);
            const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
            renderDebugConsoleFrame(width, height);
            recordFrameDiagnostics(
                m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
                debugConsoleRenderBeginTickCount);
            finishFrameDiagnostics();
            return;
        }

        recordFrameDiagnostics(m_framePerformanceDiagnostics.postWorldNanoseconds, postRenderBeginTickCount);
        const uint64_t audioBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;

        if (m_pMapSceneRuntime->kind() == SceneKind::Outdoor && m_pOutdoorPartyRuntime != nullptr)
        {
            const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
            m_gameAudioSystem.update(moveState.x, moveState.y, moveState.footZ + 96.0f, deltaSeconds);
        }
        else if (m_pMapSceneRuntime->kind() == SceneKind::Indoor)
        {
            const IndoorSceneRuntime *pIndoorRuntime =
                static_cast<const IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
            const IndoorMoveState &moveState = pIndoorRuntime->partyRuntime().movementState();
            m_gameAudioSystem.update(moveState.x, moveState.y, moveState.eyeZ(), deltaSeconds);
        }
        else
        {
            m_gameAudioSystem.update(0.0f, 0.0f, 0.0f, deltaSeconds);
        }

        recordFrameDiagnostics(m_framePerformanceDiagnostics.audioNanoseconds, audioBeginTickCount);
        const uint64_t postAudioBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;

        if (processPendingWinGame())
        {
            recordFrameDiagnostics(m_framePerformanceDiagnostics.postWorldNanoseconds, postAudioBeginTickCount);
            const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
            renderDebugConsoleFrame(width, height);
            recordFrameDiagnostics(
                m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
                debugConsoleRenderBeginTickCount);
            finishFrameDiagnostics();
            return;
        }

        if (processPendingEventMovie())
        {
            recordFrameDiagnostics(m_framePerformanceDiagnostics.postWorldNanoseconds, postAudioBeginTickCount);
            const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
            renderDebugConsoleFrame(width, height);
            recordFrameDiagnostics(
                m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
                debugConsoleRenderBeginTickCount);
            finishFrameDiagnostics();
            return;
        }

        if (processPendingReturnToMainMenu())
        {
            recordFrameDiagnostics(m_framePerformanceDiagnostics.postWorldNanoseconds, postAudioBeginTickCount);
            const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
            renderDebugConsoleFrame(width, height);
            recordFrameDiagnostics(
                m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
                debugConsoleRenderBeginTickCount);
            finishFrameDiagnostics();
            return;
        }

        processPendingMapMove();

        if (processPendingQuickSaveInput())
        {
            recordFrameDiagnostics(m_framePerformanceDiagnostics.postWorldNanoseconds, postAudioBeginTickCount);
            const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
            renderDebugConsoleFrame(width, height);
            recordFrameDiagnostics(
                m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
                debugConsoleRenderBeginTickCount);
            finishFrameDiagnostics();
            return;
        }

        recordFrameDiagnostics(m_framePerformanceDiagnostics.postWorldNanoseconds, postAudioBeginTickCount);
        const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
        renderDebugConsoleFrame(width, height);
        recordFrameDiagnostics(
            m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
            debugConsoleRenderBeginTickCount);
        finishFrameDiagnostics();
        return;
    }

    const uint64_t debugConsoleRenderBeginTickCount = collectFrameDiagnostics ? SDL_GetTicksNS() : 0;
    renderDebugConsoleFrame(width, height);
    recordFrameDiagnostics(
        m_framePerformanceDiagnostics.debugConsoleRenderNanoseconds,
        debugConsoleRenderBeginTickCount);
    finishFrameDiagnostics();
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
    closeTransientGameplayUiForMapMove();

    const bool isSameMapTeleport =
        !pendingMapMove->mapName
        || pendingMapMove->mapName->empty()
        || *pendingMapMove->mapName == "0"
        || *pendingMapMove->mapName == "0."
        || (!pendingMapMove->useMapStartPosition
            && sameMapFileName(*pendingMapMove->mapName, m_gameSession.currentMapFileName()));

    const auto applyMapMoveDirection = [this, &pendingMapMove]()
    {
        if (!pendingMapMove->directionDegrees.has_value() || m_pMapSceneRuntime == nullptr)
        {
            return;
        }

        const float yawRadians = mapMoveHeadingDegreesToYawRadians(*pendingMapMove->directionDegrees);

        if (m_pMapSceneRuntime->kind() == SceneKind::Outdoor)
        {
            m_outdoorGameView.setCameraAngles(yawRadians, m_outdoorGameView.cameraPitchRadians());
        }
        else if (m_pMapSceneRuntime->kind() == SceneKind::Indoor)
        {
            m_indoorRenderer.setCameraAngles(yawRadians, m_indoorRenderer.cameraPitchRadians());
        }
    };
    if (isSameMapTeleport)
    {
        const std::string previousMapFileName = m_gameSession.currentMapFileName();
        if (m_pMapSceneRuntime != nullptr
            && m_pMapSceneRuntime->kind() == SceneKind::Outdoor
            && m_pOutdoorPartyRuntime != nullptr)
        {
            m_pOutdoorPartyRuntime->teleportTo(
                static_cast<float>(pendingMapMove->x),
                static_cast<float>(pendingMapMove->y),
                static_cast<float>(pendingMapMove->z)
            );
        }
        else if (m_pMapSceneRuntime != nullptr && m_pMapSceneRuntime->kind() == SceneKind::Indoor)
        {
            IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
            pIndoorRuntime->partyRuntime().teleportPartyPosition(
                static_cast<float>(pendingMapMove->x),
                static_cast<float>(pendingMapMove->y),
                static_cast<float>(pendingMapMove->z));
        }

        applyMapMoveDirection();

        m_gameAudioSystem.playCommonSound(SoundId::Teleport, GameAudioSystem::PlaybackGroup::Ui);
        synchronizeSessionFromRuntime();
        GAMEPLAY_DEBUG_TRACE_BLOCK(
            logMapArrived(
                previousMapFileName,
                m_gameSession.currentMapFileName(),
                *pendingMapMove,
                true,
                m_gameSession.gameMinutes());
        );
        return true;
    }

    EventRuntimeState *pLeavingRuntimeState =
        m_pMapSceneRuntime != nullptr ? m_pMapSceneRuntime->eventRuntimeState() : nullptr;
    executeCurrentMapOnLeaveEvents();
    PendingMapLeaveOutputs onLeaveOutputs = pLeavingRuntimeState != nullptr
        ? consumePendingMapLeaveOutputs(*pLeavingRuntimeState)
        : PendingMapLeaveOutputs{};

    const std::string targetMapName = *pendingMapMove->mapName;
    const std::string previousMapFileName = m_gameSession.currentMapFileName();

    captureCurrentSceneState();

    m_gameSession.setCurrentMapFileName(targetMapName);
    const LoadingOverlayScreen::Presentation loadingPresentation = pendingMapMove->useFullscreenLoading
        ? LoadingOverlayScreen::Presentation::Fullscreen
        : LoadingOverlayScreen::Presentation::DungeonTransition;
    beginLoadingOverlay(loadingPresentation);
    renderLoadingOverlayProgress(15);

    if (!loadCurrentSessionMap(
            true,
            [this](int localProgress)
            {
                renderLoadingOverlayProgress(remapLoadingProgress(localProgress, 20, 85));
            }))
    {
        m_gameSession.setCurrentMapFileName(previousMapFileName);
        const bool previousMapRestored = loadCurrentSessionMap(
            true,
            [this](int localProgress)
            {
                renderLoadingOverlayProgress(remapLoadingProgress(localProgress, 20, 85));
            });

        if (previousMapRestored && m_pMapSceneRuntime != nullptr)
        {
            EventRuntimeState *pRestoredRuntimeState = m_pMapSceneRuntime->eventRuntimeState();

            if (pRestoredRuntimeState != nullptr)
            {
                appendPendingMapLeaveOutputs(*pRestoredRuntimeState, std::move(onLeaveOutputs));
            }
        }

        cancelLoadingOverlay();
        return false;
    }

    EventRuntimeState *pArrivingRuntimeState =
        m_pMapSceneRuntime != nullptr ? m_pMapSceneRuntime->eventRuntimeState() : nullptr;

    if (pArrivingRuntimeState != nullptr)
    {
        appendPendingMapLeaveOutputs(*pArrivingRuntimeState, std::move(onLeaveOutputs));
    }

    if (m_pMapSceneRuntime != nullptr
        && m_pMapSceneRuntime->kind() == SceneKind::Outdoor
        && m_pOutdoorPartyRuntime != nullptr
        && !pendingMapMove->useMapStartPosition)
    {
        m_pOutdoorPartyRuntime->teleportTo(
            static_cast<float>(pendingMapMove->x),
            static_cast<float>(pendingMapMove->y),
            static_cast<float>(pendingMapMove->z)
        );
    }
    else if (m_pMapSceneRuntime != nullptr
             && m_pMapSceneRuntime->kind() == SceneKind::Indoor
             && !pendingMapMove->useMapStartPosition)
    {
        IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(m_pMapSceneRuntime.get());
        pIndoorRuntime->partyRuntime().teleportPartyPosition(
            static_cast<float>(pendingMapMove->x),
            static_cast<float>(pendingMapMove->y),
            static_cast<float>(pendingMapMove->z));
    }

    applyMapMoveDirection();
    float arrivedGameMinutes = m_gameSession.gameMinutes();
    if (IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime())
    {
        arrivedGameMinutes = pWorldRuntime->gameMinutes();
    }
    GAMEPLAY_DEBUG_TRACE_BLOCK(
        logMapArrived(previousMapFileName, targetMapName, *pendingMapMove, false, arrivedGameMinutes);
    );

    if (isDungeonMapFileName(targetMapName) && !sameMapFileName(previousMapFileName, targetMapName))
    {
        Party *pParty = m_pMapSceneRuntime != nullptr ? &m_pMapSceneRuntime->party() : nullptr;
        const std::optional<size_t> memberIndex =
            pParty != nullptr ? chooseRandomActablePartyMember(*pParty) : std::nullopt;

        if (memberIndex.has_value())
        {
            m_gameSession.gameplayScreenRuntime().queueDelayedSpeechReaction(
                *memberIndex,
                SpeechId::EnterDungeon,
                EnterDungeonSpeechDelaySeconds);
        }
    }

    synchronizeSessionFromRuntime();
    renderLoadingOverlayProgress(95);
    completeLoadingOverlay();

    if (IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime())
    {
        pWorldRuntime->requestTravelAutosave();
    }

    return true;
}

void GameApplication::closeTransientGameplayUiForMapMove()
{
    IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();

    if (pWorldRuntime != nullptr)
    {
        if (pWorldRuntime->activeChestView() != nullptr)
        {
            pWorldRuntime->commitActiveChestView();
            pWorldRuntime->closeActiveChestView();
        }

        if (pWorldRuntime->activeCorpseView() != nullptr)
        {
            pWorldRuntime->commitActiveCorpseView();
            pWorldRuntime->closeActiveCorpseView();
        }
    }

    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    m_gameAudioSystem.resumeBackgroundMusic();
    screenRuntime.stopHouseVideoPlayback();
    screenRuntime.closeHouseShopOverlay();
    screenRuntime.closeInventoryNestedOverlay();
    screenRuntime.closeActiveEventDialog();
    screenRuntime.resetLootOverlayInteractionState();
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

bool GameApplication::processPendingPartyDefeat()
{
    if (m_pAssetFileSystem == nullptr
        || m_screenManager.activeScreen() != nullptr
        || m_pendingPartyDefeatRespawnMapFileName.has_value()
        || !shouldTriggerPartyDefeat())
    {
        return false;
    }

    const MapStartDestination respawnDestination = resolvePartyDefeatRespawnDestination();
    m_pendingPartyDefeatRespawnMapFileName = respawnDestination.mapFileName;
    m_pendingPartyDefeatRespawnStart = respawnDestination.start;
    const std::string cutsceneStem = resolvePartyDefeatCutsceneStem();
    m_screenManager.setActiveScreen(std::make_unique<CutsceneVideoScreen>(
        *m_pAssetFileSystem,
        &m_gameAudioSystem,
        PartyDefeatCutsceneDirectory,
        cutsceneStem,
        m_screenManager.currentMode()));
    return true;
}

bool GameApplication::executeCurrentMapOnLeaveEvents()
{
    if (m_pMapSceneRuntime == nullptr)
    {
        return false;
    }

    EventRuntimeState *pRuntimeState = m_pMapSceneRuntime->eventRuntimeState();

    if (pRuntimeState == nullptr)
    {
        return false;
    }

    EventRuntime eventRuntime = {};
    eventRuntime.bindHouseTable(&m_gameDataLoader.getHouseTable());
    eventRuntime.bindNpcDialogTable(&m_gameDataLoader.getNpcDialogTable());
    return eventRuntime.executeOnLeaveEvents(
        m_pMapSceneRuntime->localEventProgram(),
        m_pMapSceneRuntime->globalEventProgram(),
        *pRuntimeState,
        &m_pMapSceneRuntime->party(),
        m_pMapSceneRuntime->sceneEventContext());
}

WinGameCertificate GameApplication::buildWinGameCertificate() const
{
    WinGameCertificate certificate = {};
    const Party *pParty = nullptr;

    if (m_pMapSceneRuntime != nullptr)
    {
        pParty = &m_pMapSceneRuntime->party();
    }
    else if (m_gameSession.partyState().has_value())
    {
        pParty = &*m_gameSession.partyState();
    }

    const IGameplayWorldRuntime *pWorldRuntime = m_gameSession.activeWorldRuntime();
    const float currentGameMinutes = pWorldRuntime != nullptr ? pWorldRuntime->gameMinutes() : 9.0f * 60.0f;

    if (pParty != nullptr)
    {
        certificate.characterLine = winGameCharacterLine(*pParty);
        certificate.scoreLine = "Your score: " + std::to_string(calculateWinGameScore(*pParty, currentGameMinutes));
    }
    else
    {
        certificate.characterLine = "Adventurer the Level 1 Adventurer";
        certificate.scoreLine = "Your score: 0";
    }

    certificate.endingText =
        "Excellent work! By thwarting the Destroyer of Worlds, you have pulled your world from the brink of "
        "unending oblivion. Not only may life continue, but a new peace reigns over Jadame. The mighty alliance "
        "you forged will see to the land's restoration and eventual prosperity.";
    certificate.totalTimeLine = formatWinGameDuration(currentGameMinutes);
    return certificate;
}

bool GameApplication::processPendingWinGame()
{
    if (m_pAssetFileSystem == nullptr || m_screenManager.activeScreen() != nullptr)
    {
        return false;
    }

    EventRuntimeState *pRuntimeState = m_gameplayController.eventRuntimeState();

    if (pRuntimeState == nullptr || !pRuntimeState->pendingWinGame.has_value())
    {
        return false;
    }

    pRuntimeState->pendingWinGame.reset();
    m_gameSession.gameplayScreenRuntime().closeActiveEventDialog();
    m_pendingWinGameCertificateAfterMovie = true;

    if (resolveEventMovieStem(*m_pAssetFileSystem, WinGameCutsceneStem).empty())
    {
        m_screenManager.setActiveScreen(std::make_unique<WinGameScreen>(
            *m_pAssetFileSystem,
            buildWinGameCertificate(),
            m_screenManager.currentMode()));
        m_pendingWinGameCertificateAfterMovie = false;
        return true;
    }

    m_screenManager.setActiveScreen(std::make_unique<CutsceneVideoScreen>(
        *m_pAssetFileSystem,
        &m_gameAudioSystem,
        EventMovieCutsceneDirectory,
        WinGameCutsceneStem,
        m_screenManager.currentMode()));
    return true;
}

bool GameApplication::processPendingEventMovie()
{
    if (m_pAssetFileSystem == nullptr || m_screenManager.activeScreen() != nullptr)
    {
        return false;
    }

    EventRuntimeState *pRuntimeState = m_gameplayController.eventRuntimeState();

    if (pRuntimeState == nullptr || !pRuntimeState->pendingMovie.has_value())
    {
        return false;
    }

    std::optional<EventRuntimeState::PendingMovie> pendingMovie = std::move(pRuntimeState->pendingMovie);
    pRuntimeState->pendingMovie.reset();

    if (m_settings.skipEventCutscenes)
    {
        return true;
    }

    const std::string movieStem = resolveEventMovieStem(*m_pAssetFileSystem, pendingMovie->movieName);

    if (movieStem.empty())
    {
        return false;
    }

    m_screenManager.setActiveScreen(std::make_unique<CutsceneVideoScreen>(
        *m_pAssetFileSystem,
        &m_gameAudioSystem,
        EventMovieCutsceneDirectory,
        movieStem,
        m_screenManager.currentMode()));
    return true;
}

bool GameApplication::processPendingReturnToMainMenu()
{
    if (m_screenManager.activeScreen() != nullptr)
    {
        return false;
    }

    EventRuntimeState *pRuntimeState = m_gameplayController.eventRuntimeState();

    if (pRuntimeState == nullptr
        || !pRuntimeState->pendingReturnToMainMenu
        || pRuntimeState->pendingMovie.has_value()
        || pRuntimeState->pendingWinGame.has_value())
    {
        return false;
    }

    pRuntimeState->pendingReturnToMainMenu = false;
    m_gameSession.gameplayScreenRuntime().closeActiveEventDialog();
    openMainMenuScreen();
    return true;
}

bool GameApplication::processPendingDimensionDoorOverlay()
{
    EventRuntimeState *pRuntimeState = m_gameplayController.eventRuntimeState();

    if (pRuntimeState == nullptr || !pRuntimeState->pendingDimensionDoorOverlay)
    {
        return false;
    }

    pRuntimeState->pendingDimensionDoorOverlay = false;

    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();

    if (!screenRuntime.ensureDimensionDoorDestinationsLoaded())
    {
        screenRuntime.setStatusBarEvent("Dimension Door destinations unavailable");
        return false;
    }

    const Party *pParty = screenRuntime.partyReadOnly();
    const size_t casterMemberIndex = pParty != nullptr ? pParty->activeMemberIndex() : 0;
    screenRuntime.openUtilitySpellOverlay(
        GameplayUiController::UtilitySpellOverlayMode::DimensionDoor,
        spellIdValue(SpellId::TownPortal),
        casterMemberIndex);
    screenRuntime.resetUtilitySpellOverlayInteractionState();
    screenRuntime.setStatusBarEvent("You feel high magic presence here.", 4.0f);
    return true;
}

void GameApplication::handleCompletedPartyDefeatScreen()
{
    if (!m_pendingPartyDefeatRespawnMapFileName.has_value())
    {
        return;
    }

    CutsceneVideoScreen *pCutsceneScreen = dynamic_cast<CutsceneVideoScreen *>(m_screenManager.activeScreen());

    if (pCutsceneScreen == nullptr || !pCutsceneScreen->shouldClose())
    {
        return;
    }

    m_gameInputSystem.suppressMouseButtonsUntilReleased();
    m_screenManager.setActiveScreen(nullptr);
    m_gameSession.gameplayScreenRuntime().interactionState().menuToggleLatch = true;
    applyPartyDefeatConsequences();
    respawnPartyAfterDefeat(true);
    m_pendingPartyDefeatRespawnMapFileName.reset();
    m_pendingPartyDefeatRespawnStart.reset();
}

void GameApplication::handleCompletedEventMovieScreen()
{
    if (m_pendingPartyDefeatRespawnMapFileName.has_value())
    {
        return;
    }

    CutsceneVideoScreen *pCutsceneScreen = dynamic_cast<CutsceneVideoScreen *>(m_screenManager.activeScreen());

    if (pCutsceneScreen == nullptr || !pCutsceneScreen->shouldClose())
    {
        return;
    }

    if (m_pendingWinGameCertificateAfterMovie && m_pAssetFileSystem != nullptr)
    {
        m_gameInputSystem.suppressMouseButtonsUntilReleased();
        m_screenManager.setActiveScreen(std::make_unique<WinGameScreen>(
            *m_pAssetFileSystem,
            buildWinGameCertificate(),
            pCutsceneScreen->mode()));
        m_pendingWinGameCertificateAfterMovie = false;
        return;
    }

    EventRuntimeState *pRuntimeState = m_gameplayController.eventRuntimeState();

    if (pRuntimeState != nullptr && pRuntimeState->pendingReturnToMainMenu)
    {
        pRuntimeState->pendingReturnToMainMenu = false;
        m_gameInputSystem.suppressMouseButtonsUntilReleased();
        openMainMenuScreen();
        return;
    }

    m_gameInputSystem.suppressMouseButtonsUntilReleased();
    m_screenManager.setActiveScreen(nullptr);
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    screenRuntime.updatePreviousKeyboardStateSnapshot(m_gameInputSystem.frame().keyboardState());
    screenRuntime.interactionState().menuToggleLatch = true;
}

void GameApplication::handleCompletedWinGameScreen()
{
    WinGameScreen *pWinGameScreen = dynamic_cast<WinGameScreen *>(m_screenManager.activeScreen());

    if (pWinGameScreen == nullptr || !pWinGameScreen->shouldClose())
    {
        return;
    }

    m_screenManager.setActiveScreen(nullptr);
}

bool GameApplication::shouldTriggerPartyDefeat() const
{
    if (m_pMapSceneRuntime == nullptr)
    {
        return false;
    }

    return !m_pMapSceneRuntime->party().hasActableMember();
}

std::string GameApplication::resolvePartyDefeatRespawnMapFileName() const
{
    return resolvePartyDefeatRespawnDestination().mapFileName;
}

GameApplication::MapStartDestination GameApplication::resolvePartyDefeatRespawnDestination() const
{
    const std::string currentMapFileName = toLowerCopy(m_gameSession.currentMapFileName());
    const MapStatsEntry *pCurrentMap = m_gameDataLoader.getMapStats().findByFileName(currentMapFileName);

    if (pCurrentMap != nullptr)
    {
        const MergedContinentSettingEntry *pContinentSetting =
            m_gameDataLoader.findMergedContinentSettingsForMap(*pCurrentMap);

        if (pContinentSetting != nullptr)
        {
            const std::string deathMap1 = normalizedDeathMapName(pContinentSetting->deathMap1);
            const std::string deathMap2 = normalizedDeathMapName(pContinentSetting->deathMap2);

            if (!deathMap1.empty() || !deathMap2.empty())
            {
                const MapStatsEntry *pDeathMap1 = !deathMap1.empty()
                    ? m_gameDataLoader.getMapStats().findByFileName(deathMap1)
                    : nullptr;

                if (!deathMap1.empty()
                    && (sameMapFileName(currentMapFileName, deathMap1)
                        || mapMatchesDeathDestination(*pCurrentMap, currentMapFileName, pDeathMap1)))
                {
                    return MapStartDestination{
                        .mapFileName = deathMap1,
                        .start = DebugMapJumpStart{
                            .x = pContinentSetting->deathMap1X,
                            .y = pContinentSetting->deathMap1Y,
                            .z = pContinentSetting->deathMap1Z,
                            .directionYawUnits = pContinentSetting->deathMap1Direction,
                        },
                    };
                }

                if (!deathMap2.empty())
                {
                    return MapStartDestination{
                        .mapFileName = deathMap2,
                        .start = DebugMapJumpStart{
                            .x = pContinentSetting->deathMap2X,
                            .y = pContinentSetting->deathMap2Y,
                            .z = pContinentSetting->deathMap2Z,
                            .directionYawUnits = pContinentSetting->deathMap2Direction,
                        },
                    };
                }

                return MapStartDestination{
                    .mapFileName = deathMap1,
                    .start = DebugMapJumpStart{
                        .x = pContinentSetting->deathMap1X,
                        .y = pContinentSetting->deathMap1Y,
                        .z = pContinentSetting->deathMap1Z,
                        .directionYawUnits = pContinentSetting->deathMap1Direction,
                    },
                };
            }
        }
    }

    if (currentMapFileName == DwiRespawnMapFile)
    {
        return MapStartDestination{.mapFileName = DwiRespawnMapFile};
    }

    return MapStartDestination{.mapFileName = RavenshoreRespawnMapFile};
}

std::string GameApplication::resolvePartyDefeatCutsceneStem() const
{
    if (m_pAssetFileSystem == nullptr)
    {
        return PartyDefeatCutsceneStem;
    }

    const std::string currentMapFileName = toLowerCopy(m_gameSession.currentMapFileName());
    const MapStatsEntry *pCurrentMap = m_gameDataLoader.getMapStats().findByFileName(currentMapFileName);

    if (pCurrentMap != nullptr)
    {
        const MergedContinentSettingEntry *pContinentSetting =
            m_gameDataLoader.findMergedContinentSettingsForMap(*pCurrentMap);

        if (pContinentSetting != nullptr && !trimCopy(pContinentSetting->deathMovie).empty())
        {
            const std::string resolvedMovieStem =
                resolveEventMovieStem(*m_pAssetFileSystem, pContinentSetting->deathMovie);

            if (!resolvedMovieStem.empty())
            {
                return resolvedMovieStem;
            }
        }
    }

    return PartyDefeatCutsceneStem;
}

void GameApplication::applyPartyDefeatConsequences()
{
    if (m_pMapSceneRuntime == nullptr)
    {
        return;
    }

    Party &party = m_pMapSceneRuntime->party();
    const int carriedGold = party.gold();

    if (carriedGold > 0)
    {
        party.addGold(-carriedGold);
        m_gameAudioSystem.playCommonSound(SoundId::Gold, GameAudioSystem::PlaybackGroup::Ui);
    }

    const uint16_t numDeathsVariableId = static_cast<uint16_t>(EvtVariable::NumDeaths);
    party.setEventVariableValue(numDeathsVariableId, party.eventVariableValue(numDeathsVariableId) + 1);
    party.reviveAndRestoreAll();
    synchronizeSessionFromRuntime();
}

bool GameApplication::respawnPartyAfterDefeat(bool initializeView)
{
    if (!m_pendingPartyDefeatRespawnMapFileName.has_value())
    {
        return false;
    }

    const std::string previousMapFileName = m_gameSession.currentMapFileName();

    if (!sameMapFileName(previousMapFileName, *m_pendingPartyDefeatRespawnMapFileName))
    {
        executeCurrentMapOnLeaveEvents();
    }

    captureCurrentSceneState();
    m_gameSession.setCurrentMapFileName(*m_pendingPartyDefeatRespawnMapFileName);
    beginLoadingOverlay();
    renderLoadingOverlayProgress(15);

    if (!loadCurrentSessionMap(
            initializeView,
            [this](int localProgress)
            {
                renderLoadingOverlayProgress(remapLoadingProgress(localProgress, 20, 85));
            }))
    {
        cancelLoadingOverlay();
        m_gameSession.setCurrentMapFileName(previousMapFileName);
        return false;
    }

    applyMapStartDestination(MapStartDestination{
        .mapFileName = *m_pendingPartyDefeatRespawnMapFileName,
        .start = m_pendingPartyDefeatRespawnStart,
    });
    synchronizeSessionFromRuntime();
    renderLoadingOverlayProgress(95);
    completeLoadingOverlay();
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

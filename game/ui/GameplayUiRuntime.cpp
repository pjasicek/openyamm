#include "game/ui/GameplayUiRuntime.h"

#include "game/render/ActorModelPreview.h"
#include "game/ui/GameplayHudGeometry.h"

#include "engine/BgfxContext.h"
#include "game/StringUtils.h"
#include "game/render/SpriteAtlasCache.h"
#include "game/render/TextureFiltering.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <array>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cctype>
#include <functional>
#include <optional>
#include <string_view>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
template <typename T>
void hashCombine(size_t &seed, const T &value)
{
    seed ^= std::hash<T>{}(value) + 0x9e3779b97f4a7c15ull + (seed << 6) + (seed >> 2);
}

bool canUseBgfxResources()
{
    return Engine::BgfxContext::isBgfxInitialized();
}

constexpr int32_t MergedYawUnitsPerTurn = 2048;
constexpr int32_t DegreesPerTurn = 360;
constexpr size_t MaxPerformanceAssetLoadEvents = 32;
constexpr std::string_view EagerGameplayHudScreen = "outdoorhud";
struct TownPortalDestinationOverride
{
    uint32_t mapId = 0;
    std::string iconName;
    bool useMapStartPosition = false;
    bool clearUnlockQBit = false;
    bool clearDirection = false;
    int32_t hitX = 0;
    int32_t hitY = 0;
    uint32_t hitWidth = 0;
    uint32_t hitHeight = 0;
};

int32_t directionDegreesFromMergedYawUnits(int32_t yawUnits)
{
    const int32_t normalizedYawUnits =
        ((yawUnits % MergedYawUnitsPerTurn) + MergedYawUnitsPerTurn) % MergedYawUnitsPerTurn;
    return normalizedYawUnits * DegreesPerTurn / MergedYawUnitsPerTurn;
}

std::string townPortalIconTextureName(const std::string &iconName)
{
    const std::string normalizedIconName = toLowerCopy(iconName);

    if (normalizedIconName == "tpharmndy")
    {
        return "tp_alvar";
    }

    if (normalizedIconName == "tpelf")
    {
        return "tp_ravenshore";
    }

    if (normalizedIconName == "tpwarlock")
    {
        return "tp_balthazarlair";
    }

    if (normalizedIconName == "tpisland")
    {
        return "tp_regna";
    }

    if (normalizedIconName == "tpheaven")
    {
        return "tp_shadowspire";
    }

    if (normalizedIconName == "tphell")
    {
        return "tp_daggerwoundislands";
    }

    return normalizedIconName;
}

const MapStatsEntry *findMapEntryById(const std::vector<MapStatsEntry> &mapEntries, uint32_t mapId)
{
    for (const MapStatsEntry &entry : mapEntries)
    {
        if (entry.id == static_cast<int>(mapId))
        {
            return &entry;
        }
    }

    return nullptr;
}

const MergedTownPortalSwitchGroup *findTownPortalGroup(
    const MergedTownPortalSwitchTable &townPortalSwitchTable,
    const std::string &groupName)
{
    const std::string normalizedGroupName = toLowerCopy(groupName);

    for (const MergedTownPortalSwitchGroup &group : townPortalSwitchTable.groups())
    {
        if (toLowerCopy(group.name) == normalizedGroupName)
        {
            return &group;
        }
    }

    return nullptr;
}

std::string townPortalGroupNameForMap(const MapStatsEntry &mapEntry)
{
    if (mapEntry.id >= 62 && mapEntry.id <= 136)
    {
        return "Antagrich";
    }

    if (mapEntry.id >= 137 && mapEntry.id <= 203)
    {
        return "TPEnroth";
    }

    return "townport";
}

bool appendTownPortalDestination(
    std::vector<GameplayTownPortalDestination> &destinations,
    const MergedTownPortalSwitchGroup &group,
    const MergedTownPortalDestination &sourceDestination,
    const std::vector<MapStatsEntry> &mapEntries,
    const TownPortalDestinationOverride *pOverride = nullptr)
{
    const std::string &iconName =
        pOverride != nullptr && !pOverride->iconName.empty() ? pOverride->iconName : sourceDestination.iconName;

    if (iconName.empty() || toLowerCopy(iconName) == "none")
    {
        return false;
    }

    const uint32_t mapId =
        pOverride != nullptr && pOverride->mapId != 0 ? pOverride->mapId : sourceDestination.mapId;
    const MapStatsEntry *pDestinationMap = findMapEntryById(mapEntries, mapId);

    if (pDestinationMap == nullptr)
    {
        return false;
    }

    GameplayTownPortalDestination destination = {};
    destination.id = group.name + ":" + std::to_string(sourceDestination.id);
    destination.label =
        sourceDestination.description.empty() ? pDestinationMap->name : sourceDestination.description;
    destination.iconTextureName = townPortalIconTextureName(iconName);
    destination.mapName = pDestinationMap->fileName;
    destination.x = sourceDestination.x;
    destination.y = sourceDestination.y;
    destination.z = sourceDestination.z;
    if (pOverride == nullptr || !pOverride->clearDirection)
    {
        destination.directionDegrees = directionDegreesFromMergedYawUnits(sourceDestination.direction);
    }
    destination.useMapStartPosition = pOverride != nullptr && pOverride->useMapStartPosition;
    destination.unlockQBitId =
        pOverride != nullptr && pOverride->clearUnlockQBit ? 0 : sourceDestination.qbitIndex;
    destination.iconX = sourceDestination.iconX;
    destination.iconY = sourceDestination.iconY;
    destination.iconWidth = sourceDestination.iconWidth.value_or(0);
    destination.iconHeight = sourceDestination.iconHeight.value_or(0);
    destination.hitX = pOverride != nullptr && pOverride->hitWidth != 0
        ? pOverride->hitX
        : destination.iconX;
    destination.hitY = pOverride != nullptr && pOverride->hitHeight != 0
        ? pOverride->hitY
        : destination.iconY;
    destination.hitWidth = pOverride != nullptr && pOverride->hitWidth != 0
        ? pOverride->hitWidth
        : destination.iconWidth;
    destination.hitHeight = pOverride != nullptr && pOverride->hitHeight != 0
        ? pOverride->hitHeight
        : destination.iconHeight;
    destinations.push_back(std::move(destination));
    return true;
}

bool resolveDimensionDoorDestinationOverride(
    const MergedTownPortalDestination &sourceDestination,
    uint32_t /*dayIndex*/,
    TownPortalDestinationOverride &destinationOverride)
{
    const std::string description = toLowerCopy(sourceDestination.description);

    destinationOverride = {};
    destinationOverride.clearUnlockQBit = true;
    destinationOverride.clearDirection = true;
    destinationOverride.iconName = "ui/gameplay/dimensional_travel/" + toLowerCopy(sourceDestination.iconName);

    if (description == "jadame")
    {
        destinationOverride.mapId = 1;
        destinationOverride.hitX = 0;
        destinationOverride.hitY = 0;
        destinationOverride.hitWidth = 213;
        destinationOverride.hitHeight = 480;
        return true;
    }

    if (description == "antagarich")
    {
        destinationOverride.mapId = 62;
        destinationOverride.hitX = 427;
        destinationOverride.hitY = 0;
        destinationOverride.hitWidth = 213;
        destinationOverride.hitHeight = 480;
        return true;
    }

    if (description == "enroth")
    {
        destinationOverride.mapId = 151;
        destinationOverride.hitX = 213;
        destinationOverride.hitY = 0;
        destinationOverride.hitWidth = 214;
        destinationOverride.hitHeight = 480;
        return true;
    }

    return false;
}

uint32_t currentAnimationTicks()
{
    return (static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL;
}

std::string portraitTextureNameForPictureFrame(uint32_t pictureId, uint16_t frameIndex)
{
    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-%02u", pictureId + 1, std::max<uint16_t>(1, frameIndex));
    return buffer;
}

std::string portraitTextureNameForTextureFrame(const std::string &textureName, uint16_t frameIndex)
{
    if (textureName.empty())
    {
        return {};
    }

    std::string frameTextureName = textureName;

    if (frameTextureName.size() >= 2
        && std::isdigit(static_cast<unsigned char>(frameTextureName[frameTextureName.size() - 2])) != 0
        && std::isdigit(static_cast<unsigned char>(frameTextureName[frameTextureName.size() - 1])) != 0)
    {
        char frameSuffix[8] = {};
        std::snprintf(frameSuffix, sizeof(frameSuffix), "%02u", std::max<uint16_t>(1, frameIndex));
        frameTextureName.replace(frameTextureName.size() - 2, 2, frameSuffix);
    }

    return frameTextureName;
}

std::string portraitTextureNameForCharacterFrame(const Character &character, uint16_t frameIndex)
{
    const std::string textureFrameName =
        portraitTextureNameForTextureFrame(character.portraitTextureName, frameIndex);

    if (!textureFrameName.empty())
    {
        return textureFrameName;
    }

    return portraitTextureNameForPictureFrame(character.portraitPictureId, frameIndex);
}

const bgfx::VertexLayout &gameplayHudQuadVertexLayout()
{
    static const bgfx::VertexLayout layout = []()
    {
        bgfx::VertexLayout result;
        result.begin()
            .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
            .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
            .end();
        return result;
    }();

    return layout;
}
}

size_t GameplayUiRuntime::HudLayoutResolutionCacheKeyHash::operator()(
    const HudLayoutResolutionCacheKey &key) const
{
    return (*this)(HudLayoutResolutionCacheView{
        key.layoutId, key.screenWidth, key.screenHeight, key.fallbackWidth, key.fallbackHeight});
}

size_t GameplayUiRuntime::HudLayoutResolutionCacheKeyHash::operator()(
    const HudLayoutResolutionCacheView &key) const
{
    size_t seed = 0;
    hashCombine(seed, key.layoutId);
    hashCombine(seed, key.screenWidth);
    hashCombine(seed, key.screenHeight);
    hashCombine(seed, key.fallbackWidth);
    hashCombine(seed, key.fallbackHeight);
    return seed;
}

void GameplayUiRuntime::beginPerformanceFrame(bool enabled)
{
    m_performanceFrameEnabled = enabled;

    if (!enabled)
    {
        return;
    }

    m_performanceAssetLoadEvents.clear();
    m_performanceAssetLoadEventOverflowCount = 0;
    m_lastOverlayFramePerformanceDiagnostics = {};
}

const std::vector<GameplayUiAssetLoadPerformanceEvent> &GameplayUiRuntime::performanceAssetLoadEvents() const
{
    return m_performanceAssetLoadEvents;
}

size_t GameplayUiRuntime::performanceAssetLoadEventOverflowCount() const
{
    return m_performanceAssetLoadEventOverflowCount;
}

void GameplayUiRuntime::setLastOverlayFramePerformanceDiagnostics(
    const GameplayUiOverlayFramePerformanceDiagnostics &diagnostics)
{
    m_lastOverlayFramePerformanceDiagnostics = diagnostics;
}

const GameplayUiOverlayFramePerformanceDiagnostics &
GameplayUiRuntime::lastOverlayFramePerformanceDiagnostics() const
{
    return m_lastOverlayFramePerformanceDiagnostics;
}

void GameplayUiRuntime::recordPerformanceAssetLoad(
    GameplayUiAssetLoadKind kind,
    const std::string &name,
    uint64_t loadNanoseconds,
    bool success,
    int width,
    int height,
    bool hasColor,
    uint32_t colorAbgr)
{
    if (!m_performanceFrameEnabled)
    {
        return;
    }

    if (m_performanceAssetLoadEvents.size() >= MaxPerformanceAssetLoadEvents)
    {
        ++m_performanceAssetLoadEventOverflowCount;
        return;
    }

    m_performanceAssetLoadEvents.push_back(GameplayUiAssetLoadPerformanceEvent{
        .kind = kind,
        .name = name,
        .loadNanoseconds = loadNanoseconds,
        .colorAbgr = colorAbgr,
        .width = width,
        .height = height,
        .success = success,
        .hasColor = hasColor,
    });
}

void GameplayUiRuntime::clearHudLayoutLookupCaches() const
{
    m_hudLayoutElementLookupCache.clear();
    m_staticHudLayoutElementLookupCache.clear();
    m_hudLayoutResolutionCache.clear();
}

void GameplayUiRuntime::clear()
{
    shutdownHouseVideoPlayer();
    clearPortraitRuntime();
    clearHudResources();
    m_hudArcMeshCache.clear();
    m_layoutManager.clear();
    clearHudLayoutLookupCaches();
    m_hudLayoutRuntimeWidthOverrides.clear();
    m_hudLayoutRuntimeHeightOverrides.clear();
    m_renderedInspectableHudItems.clear();
    m_renderedInspectableHudScreenState = GameplayHudScreenState::Gameplay;
    m_townPortalDestinationsMapFileName.clear();
    m_townPortalBackgroundTextureName.clear();
    m_townPortalDestinations.clear();
    m_townPortalDestinationsLoaded = false;
    m_hudRenderBackend = {};
    m_flyBuffIconAnimationState = {};
    m_actorInspectClock = {};
    m_assetLoadCache = {};
    m_performanceFrameEnabled = false;
    m_performanceAssetLoadEvents.clear();
    m_performanceAssetLoadEventOverflowCount = 0;
    m_lastOverlayFramePerformanceDiagnostics = {};
    m_pAssetFileSystem = nullptr;
    m_assetWorldId.clear();
    m_iconAssetScaleTier = Engine::AssetScaleTier::X1;
    m_layoutsLoaded = false;
    m_assetsPreloaded = false;
}

void GameplayUiRuntime::bindDataRepository(const GameDataRepository *pDataRepository)
{
    if (m_pDataRepository == pDataRepository)
    {
        return;
    }

    clearPortraitRuntime();
    m_townPortalDestinationsMapFileName.clear();
    m_townPortalBackgroundTextureName.clear();
    m_townPortalDestinations.clear();
    m_townPortalDestinationsLoaded = false;
    m_pDataRepository = pDataRepository;
}

void GameplayUiRuntime::bindAssetFileSystem(const Engine::AssetFileSystem *pAssetFileSystem)
{
    const bool bindingsMatch =
        pAssetFileSystem != nullptr
        && m_pAssetFileSystem == pAssetFileSystem
        && m_assetWorldId == pAssetFileSystem->getActiveWorldId()
        && m_iconAssetScaleTier == pAssetFileSystem->getAssetScaleTier(Engine::AssetScaleCategory::Icons);

    if (bindingsMatch || (pAssetFileSystem == nullptr && m_pAssetFileSystem == nullptr))
    {
        return;
    }

    clear();
    m_pAssetFileSystem = pAssetFileSystem;

    if (pAssetFileSystem != nullptr)
    {
        m_assetWorldId = pAssetFileSystem->getActiveWorldId();
        m_iconAssetScaleTier = pAssetFileSystem->getAssetScaleTier(Engine::AssetScaleCategory::Icons);
    }
}

const Engine::AssetFileSystem *GameplayUiRuntime::assetFileSystem() const
{
    return m_pAssetFileSystem;
}

bool GameplayUiRuntime::ensureGameplayLayoutsLoaded(const GameplayUiController &uiController)
{
    if (m_layoutsLoaded)
    {
        return true;
    }

    if (m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    m_layoutManager.clear();
    clearHudLayoutLookupCaches();

    const bool loaded = uiController.loadGameplayLayouts(
        *m_pAssetFileSystem,
        [this](const std::string &path) -> bool
        {
            return m_layoutManager.loadLayoutFile(*m_pAssetFileSystem, path);
        });

    if (!loaded)
    {
        clearHudLayoutLookupCaches();
        return false;
    }

    clearHudLayoutLookupCaches();
    m_layoutsLoaded = true;
    return true;
}

void GameplayUiRuntime::preloadReferencedAssets()
{
    if (m_assetsPreloaded)
    {
        return;
    }

    if (!canUseBgfxResources())
    {
        return;
    }

    std::vector<std::string> fontNames;
    for (const auto &[id, element] : m_layoutManager.elements())
    {
        (void)id;

        const bool inspection = element.normalizedScreen == "iteminspect"
            || element.normalizedScreen == "spellinspect"
            || element.normalizedScreen == "actorinspect";
        if (element.normalizedScreen != EagerGameplayHudScreen && !inspection)
        {
            continue;
        }

        for (const std::string *pAssetName : {
                 &element.primaryAsset,
                 &element.hoverAsset,
                 &element.pressedAsset,
                 &element.secondaryAsset,
                 &element.tertiaryAsset,
                 &element.quaternaryAsset,
                 &element.quinaryAsset})
        {
            if (!pAssetName->empty())
            {
                loadHudTexture(*pAssetName);
            }
        }

        // Common inspection panels must be ready before the first world-item or spell hover.
        if (!element.fontName.empty())
        {
            fontNames.push_back(element.fontName);
        }
    }

    // Rasterized and mip-filtered together on the load workers.
    GameplayHudCommon::loadHudFonts(m_pAssetFileSystem, fontNames, m_hudFontHandles);
    m_assetsPreloaded = true;
}

GameplayAssetLoadCache &GameplayUiRuntime::assetLoadCache()
{
    return m_assetLoadCache;
}

const GameplayAssetLoadCache &GameplayUiRuntime::assetLoadCache() const
{
    return m_assetLoadCache;
}

const std::vector<GameplayHudLayoutEntry> &GameplayUiRuntime::gameplayHudLayoutEntries()
{
    return m_gameplayHudLayoutCache.entries(m_layoutManager);
}

UiLayoutManager &GameplayUiRuntime::layoutManager()
{
    return m_layoutManager;
}

const UiLayoutManager &GameplayUiRuntime::layoutManager() const
{
    return m_layoutManager;
}

std::vector<GameplayHudTextureData> &GameplayUiRuntime::hudTextureHandles()
{
    return m_hudTextureHandles;
}

const std::vector<GameplayHudTextureData> &GameplayUiRuntime::hudTextureHandles() const
{
    return m_hudTextureHandles;
}

std::unordered_map<std::string, size_t> &GameplayUiRuntime::hudTextureIndexByName()
{
    return m_hudTextureIndexByName;
}

const std::unordered_map<std::string, size_t> &GameplayUiRuntime::hudTextureIndexByName() const
{
    return m_hudTextureIndexByName;
}

std::vector<GameplayHudFontData> &GameplayUiRuntime::hudFontHandles()
{
    return m_hudFontHandles;
}

const std::vector<GameplayHudFontData> &GameplayUiRuntime::hudFontHandles() const
{
    return m_hudFontHandles;
}

std::vector<GameplayHudTextureColorTextureData> &GameplayUiRuntime::hudTextureColorTextureHandles()
{
    return m_hudTextureColorTextureHandles;
}

const std::vector<GameplayHudTextureColorTextureData> &GameplayUiRuntime::hudTextureColorTextureHandles() const
{
    return m_hudTextureColorTextureHandles;
}

std::unordered_map<std::string, float> &GameplayUiRuntime::hudLayoutRuntimeHeightOverrides()
{
    return m_hudLayoutRuntimeHeightOverrides;
}

const std::unordered_map<std::string, float> &GameplayUiRuntime::hudLayoutRuntimeHeightOverrides() const
{
    return m_hudLayoutRuntimeHeightOverrides;
}

std::vector<GameplayRenderedInspectableHudItem> &GameplayUiRuntime::renderedInspectableHudItems()
{
    return m_renderedInspectableHudItems;
}

const std::vector<GameplayRenderedInspectableHudItem> &GameplayUiRuntime::renderedInspectableHudItems() const
{
    return m_renderedInspectableHudItems;
}

void GameplayUiRuntime::clearRenderedInspectableHudItems()
{
    m_renderedInspectableHudItems.clear();
}

GameplayHudScreenState GameplayUiRuntime::renderedInspectableHudScreenState() const
{
    return m_renderedInspectableHudScreenState;
}

void GameplayUiRuntime::setRenderedInspectableHudScreenState(GameplayHudScreenState state)
{
    m_renderedInspectableHudScreenState = state;
}

bool GameplayUiRuntime::ensureTownPortalDestinationsLoaded(const std::string &currentMapFileName)
{
    if (m_townPortalDestinationsLoaded
        && toLowerCopy(m_townPortalDestinationsMapFileName) == toLowerCopy(currentMapFileName))
    {
        return !m_townPortalDestinations.empty();
    }

    m_townPortalDestinationsMapFileName = currentMapFileName;
    m_townPortalBackgroundTextureName.clear();
    m_townPortalDestinations.clear();
    m_townPortalDestinationsLoaded = false;

    if (m_pDataRepository == nullptr || !m_pDataRepository->isBound())
    {
        return false;
    }

    const MapStatsEntry *pCurrentMap = m_pDataRepository->mapStats().findByFileName(currentMapFileName);

    if (pCurrentMap == nullptr)
    {
        return false;
    }

    const MergedTownPortalSwitchGroup *pGroup = findTownPortalGroup(
        m_pDataRepository->mergedTownPortalSwitchTable(),
        townPortalGroupNameForMap(*pCurrentMap));

    if (pGroup == nullptr)
    {
        return false;
    }

    std::vector<GameplayTownPortalDestination> destinations;
    const std::vector<MapStatsEntry> &mapEntries = m_pDataRepository->mapEntries();

    for (const MergedTownPortalDestination &sourceDestination : pGroup->destinations)
    {
        appendTownPortalDestination(destinations, *pGroup, sourceDestination, mapEntries);
    }

    m_townPortalBackgroundTextureName = townPortalIconTextureName(pGroup->name);
    m_townPortalDestinations = std::move(destinations);
    m_townPortalDestinationsLoaded = true;
    return !m_townPortalDestinations.empty();
}

bool GameplayUiRuntime::ensureDimensionDoorDestinationsLoaded(uint32_t dayIndex, bool crossContinentsUnlocked)
{
    const std::string cacheKey = "__dimension_door:" + std::to_string(dayIndex)
        + (crossContinentsUnlocked ? ":unlocked" : ":locked");

    if (m_townPortalDestinationsLoaded
        && toLowerCopy(m_townPortalDestinationsMapFileName) == toLowerCopy(cacheKey))
    {
        return !m_townPortalDestinations.empty();
    }

    m_townPortalDestinationsMapFileName = cacheKey;
    m_townPortalBackgroundTextureName.clear();
    m_townPortalDestinations.clear();
    m_townPortalDestinationsLoaded = false;

    if (!crossContinentsUnlocked)
    {
        m_townPortalDestinationsLoaded = true;
        return false;
    }

    if (m_pDataRepository == nullptr || !m_pDataRepository->isBound())
    {
        return false;
    }

    const MergedTownPortalSwitchGroup *pGroup = findTownPortalGroup(
        m_pDataRepository->mergedTownPortalSwitchTable(),
        "TPGlobal");

    if (pGroup == nullptr)
    {
        return false;
    }

    std::vector<GameplayTownPortalDestination> destinations;
    const std::vector<MapStatsEntry> &mapEntries = m_pDataRepository->mapEntries();

    for (const MergedTownPortalDestination &sourceDestination : pGroup->destinations)
    {
        TownPortalDestinationOverride destinationOverride = {};
        const bool hasOverride =
            resolveDimensionDoorDestinationOverride(sourceDestination, dayIndex, destinationOverride);
        appendTownPortalDestination(
            destinations,
            *pGroup,
            sourceDestination,
            mapEntries,
            hasOverride ? &destinationOverride : nullptr);
    }

    m_townPortalBackgroundTextureName = "ui/gameplay/dimensional_travel/tpglobal";
    m_townPortalDestinations = std::move(destinations);
    m_townPortalDestinationsLoaded = true;
    return !m_townPortalDestinations.empty();
}

const std::string &GameplayUiRuntime::townPortalBackgroundTextureName() const
{
    return m_townPortalBackgroundTextureName;
}

const std::vector<GameplayTownPortalDestination> &GameplayUiRuntime::townPortalDestinations() const
{
    return m_townPortalDestinations;
}

bool GameplayUiRuntime::loadHudTexture(const std::string &textureName)
{
    if (!canUseBgfxResources())
    {
        return false;
    }

    const bool cacheMiss =
        m_performanceFrameEnabled
        && GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName) == nullptr;
    const uint64_t loadBeginTickCount = cacheMiss ? SDL_GetTicksNS() : 0;
    const size_t firstNewTexture = m_hudTextureHandles.size();
    const bool loaded = GameplayHudCommon::loadHudTexture(
        m_pAssetFileSystem,
        m_assetLoadCache,
        textureName,
        m_hudTextureHandles,
        m_hudTextureIndexByName);
    registerHudTextureUvScales(firstNewTexture);

    if (cacheMiss)
    {
        const GameplayHudTextureData *pTexture =
            GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName);
        recordPerformanceAssetLoad(
            GameplayUiAssetLoadKind::HudTexture,
            textureName,
            SDL_GetTicksNS() - loadBeginTickCount,
            loaded,
            pTexture != nullptr ? pTexture->physicalWidth : 0,
            pTexture != nullptr ? pTexture->physicalHeight : 0);
    }

    return loaded;
}

bool GameplayUiRuntime::loadItemIconTexture(const std::string &textureName)
{
    if (!canUseBgfxResources())
    {
        return false;
    }

    const bool cacheMiss =
        m_performanceFrameEnabled
        && GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName) == nullptr;
    const uint64_t loadBeginTickCount = cacheMiss ? SDL_GetTicksNS() : 0;
    const size_t firstNewTexture = m_hudTextureHandles.size();
    const bool loaded = GameplayHudCommon::loadHudTexture(
        m_pAssetFileSystem,
        m_assetLoadCache,
        textureName,
        m_hudTextureHandles,
        m_hudTextureIndexByName,
        GameplayHudBitmapTransparencyMode::ItemIcon);
    registerHudTextureUvScales(firstNewTexture);

    if (cacheMiss)
    {
        const GameplayHudTextureData *pTexture =
            GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName);
        recordPerformanceAssetLoad(
            GameplayUiAssetLoadKind::ItemIcon,
            textureName,
            SDL_GetTicksNS() - loadBeginTickCount,
            loaded,
            pTexture != nullptr ? pTexture->physicalWidth : 0,
            pTexture != nullptr ? pTexture->physicalHeight : 0);
    }

    return loaded;
}

bool GameplayUiRuntime::loadHudFont(const std::string &fontName)
{
    if (!canUseBgfxResources())
    {
        return false;
    }

    const bool cacheMiss =
        m_performanceFrameEnabled && GameplayHudCommon::findHudFont(m_hudFontHandles, fontName) == nullptr;
    const uint64_t loadBeginTickCount = cacheMiss ? SDL_GetTicksNS() : 0;
    const bool loaded = GameplayHudCommon::loadHudFont(m_pAssetFileSystem, fontName, m_hudFontHandles);

    if (cacheMiss)
    {
        const GameplayHudFontData *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, fontName);
        recordPerformanceAssetLoad(
            GameplayUiAssetLoadKind::HudFont,
            fontName,
            SDL_GetTicksNS() - loadBeginTickCount,
            loaded,
            pFont != nullptr ? pFont->atlasWidth : 0,
            pFont != nullptr ? pFont->atlasHeight : 0);
    }

    return loaded;
}

std::optional<std::vector<uint8_t>> GameplayUiRuntime::loadHudBitmapPixelsBgraCached(
    const std::string &textureName,
    int &width,
    int &height,
    Engine::AssetScaleTier *pLoadedTier)
{
    return GameplayHudCommon::loadHudBitmapPixelsBgraCached(
        m_pAssetFileSystem,
        m_assetLoadCache,
        textureName,
        width,
        height,
        GameplayHudBitmapTransparencyMode::HudColorKey,
        pLoadedTier);
}

std::optional<std::vector<uint8_t>> GameplayUiRuntime::loadItemIconBitmapPixelsBgraCached(
    const std::string &textureName,
    int &width,
    int &height,
    Engine::AssetScaleTier *pLoadedTier)
{
    return GameplayHudCommon::loadHudBitmapPixelsBgraCached(
        m_pAssetFileSystem,
        m_assetLoadCache,
        textureName,
        width,
        height,
        GameplayHudBitmapTransparencyMode::ItemIcon,
        pLoadedTier);
}

std::optional<std::vector<uint8_t>> GameplayUiRuntime::loadSpriteBitmapPixelsBgraCached(
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height,
    Engine::AssetScaleTier *pLoadedTier)
{
    return GameplayHudCommon::loadSpriteBitmapPixelsBgraCached(
        m_pAssetFileSystem,
        m_assetLoadCache,
        textureName,
        paletteId,
        width,
        height,
        m_assetWorldId,
        pLoadedTier);
}

void GameplayUiRuntime::clearHudLayoutRuntimeHeightOverrides()
{
    m_hudLayoutRuntimeWidthOverrides.clear();
    m_hudLayoutRuntimeHeightOverrides.clear();
    m_hudLayoutResolutionCache.clear();
}

void GameplayUiRuntime::setHudLayoutRuntimeWidthOverride(const std::string &layoutId, float width)
{
    m_hudLayoutRuntimeWidthOverrides[toLowerCopy(layoutId)] = width;
    m_hudLayoutResolutionCache.clear();
}

void GameplayUiRuntime::setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height)
{
    m_hudLayoutRuntimeHeightOverrides[toLowerCopy(layoutId)] = height;
    m_hudLayoutResolutionCache.clear();
}

const UiLayoutManager::LayoutElement *GameplayUiRuntime::findHudLayoutElement(const std::string &layoutId) const
{
    const std::unordered_map<std::string, const UiLayoutManager::LayoutElement *>::const_iterator cachedIterator =
        m_hudLayoutElementLookupCache.find(layoutId);

    if (cachedIterator != m_hudLayoutElementLookupCache.end())
    {
        return cachedIterator->second;
    }

    const UiLayoutManager::LayoutElement *pElement = m_layoutManager.findElement(layoutId);
    m_hudLayoutElementLookupCache.emplace(layoutId, pElement);
    return pElement;
}

const UiLayoutManager::LayoutElement *GameplayUiRuntime::findStaticHudLayoutElement(const char *pLayoutId) const
{
    const std::unordered_map<const char *, const UiLayoutManager::LayoutElement *>::const_iterator cachedIterator =
        m_staticHudLayoutElementLookupCache.find(pLayoutId);

    if (cachedIterator != m_staticHudLayoutElementLookupCache.end())
    {
        return cachedIterator->second;
    }

    const UiLayoutManager::LayoutElement *pElement = m_layoutManager.findElement(pLayoutId);
    m_staticHudLayoutElementLookupCache.emplace(pLayoutId, pElement);
    return pElement;
}

int GameplayUiRuntime::defaultHudLayoutZIndexForScreen(const std::string &screen) const
{
    return UiLayoutManager::defaultZIndexForScreen(screen);
}

const std::vector<std::string> &GameplayUiRuntime::sortedHudLayoutIdsForScreen(const std::string &screen) const
{
    return m_layoutManager.sortedLayoutIdsForScreenCached(screen);
}

std::optional<GameplayResolvedHudLayoutElement> GameplayUiRuntime::resolveHudLayoutElement(
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight) const
{
    const HudLayoutResolutionCacheView cacheView = {layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight};
    const auto cachedIterator = m_hudLayoutResolutionCache.find(cacheView);

    if (cachedIterator != m_hudLayoutResolutionCache.end())
    {
        return cachedIterator->second;
    }

    std::optional<GameplayResolvedHudLayoutElement> resolved =
        GameplayHudCommon::resolveHudLayoutElement(
            m_layoutManager,
            m_hudLayoutRuntimeWidthOverrides,
            m_hudLayoutRuntimeHeightOverrides,
            layoutId,
            screenWidth,
            screenHeight,
            fallbackWidth,
            fallbackHeight);
    m_hudLayoutResolutionCache.emplace(
        HudLayoutResolutionCacheKey{layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight}, resolved);
    return resolved;
}

std::optional<GameplayHudTextureHandle> GameplayUiRuntime::ensureHudTextureLoaded(const std::string &textureName)
{
    if (textureName.empty() || !canUseBgfxResources())
    {
        return std::nullopt;
    }

    const GameplayHudTextureData *pTexture =
        GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName);
    if (pTexture == nullptr && loadHudTexture(textureName))
    {
        pTexture = GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName);
    }

    if (pTexture == nullptr)
    {
        return std::nullopt;
    }

    GameplayHudTextureHandle result = {};
    result.textureName = pTexture->textureName;
    result.width = pTexture->width;
    result.height = pTexture->height;
    result.textureHandle = pTexture->textureHandle;
    return result;
}

std::optional<GameplayHudTextureHandle> GameplayUiRuntime::ensureItemIconTextureLoaded(const std::string &textureName)
{
    if (textureName.empty() || !canUseBgfxResources())
    {
        return std::nullopt;
    }

    const GameplayHudTextureData *pTexture =
        GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName);
    if (pTexture == nullptr && loadItemIconTexture(textureName))
    {
        pTexture = GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName);
    }

    if (pTexture == nullptr)
    {
        return std::nullopt;
    }

    GameplayHudTextureHandle result = {};
    result.textureName = pTexture->textureName;
    result.width = pTexture->width;
    result.height = pTexture->height;
    result.textureHandle = pTexture->textureHandle;
    return result;
}

std::optional<std::string> GameplayUiRuntime::iconAnimationFrameTextureName(
    const std::string &animationName,
    std::optional<uint32_t> elapsedTicks) const
{
    if (m_pDataRepository == nullptr || animationName.empty())
    {
        return std::nullopt;
    }

    const std::optional<size_t> animationId = m_pDataRepository->iconFrameTable().findAnimationIdByName(animationName);

    if (!animationId)
    {
        return std::nullopt;
    }

    const IconFrameEntry *pFrame = m_pDataRepository->iconFrameTable().getFrame(
        *animationId, elapsedTicks ? *elapsedTicks : currentAnimationTicks());

    if (pFrame == nullptr || pFrame->textureName.empty())
    {
        return std::nullopt;
    }

    return pFrame->textureName;
}

std::optional<std::string> GameplayUiRuntime::flyBuffIconAnimationFrameTextureName(
    bool active,
    uint32_t tickDivisor)
{
    constexpr const char *pFlyBuffAnimationName = "spell21";
    const uint32_t nowTicks = currentAnimationTicks();

    if (!m_flyBuffIconAnimationState.initialized
        || m_flyBuffIconAnimationState.animationName != pFlyBuffAnimationName)
    {
        m_flyBuffIconAnimationState = {};
        m_flyBuffIconAnimationState.initialized = true;
        m_flyBuffIconAnimationState.animationName = pFlyBuffAnimationName;
        m_flyBuffIconAnimationState.lastSourceTicks = nowTicks;
    }

    if (active && m_flyBuffIconAnimationState.advancing)
    {
        m_flyBuffIconAnimationState.accumulatedSourceTicks +=
            nowTicks - m_flyBuffIconAnimationState.lastSourceTicks;
    }

    m_flyBuffIconAnimationState.advancing = active;
    m_flyBuffIconAnimationState.lastSourceTicks = nowTicks;

    const uint32_t safeTickDivisor = std::max<uint32_t>(tickDivisor, 1);
    return iconAnimationFrameTextureName(
        m_flyBuffIconAnimationState.animationName,
        m_flyBuffIconAnimationState.accumulatedSourceTicks / safeTickDivisor);
}

GameplayHudBatchQuad gameplayHudPaletteQuad(
    const GameplayHudPaletteColor &color, float x, float y, float width, float height)
{
    GameplayHudBatchQuad quad;
    quad.textureHandle = color.textureHandle;
    quad.x = x;
    quad.y = y;
    quad.width = width;
    quad.height = height;
    quad.u0 = color.u;
    quad.u1 = color.u;
    quad.v0 = color.v;
    quad.v1 = color.v;
    return quad;
}

std::optional<GameplayHudPaletteColor> GameplayUiRuntime::ensureHudPaletteColor(uint32_t abgrColor)
{
    constexpr uint16_t PaletteSize = 64;
    auto slot = m_hudPaletteSlotByColor.find(abgrColor);

    if (slot == m_hudPaletteSlotByColor.end())
    {
        if (m_hudPaletteSlotByColor.size() >= size_t(PaletteSize) * PaletteSize)
        {
            return std::nullopt;
        }

        if (!bgfx::isValid(m_hudPaletteTextureHandle))
        {
            m_hudPaletteTextureHandle = bgfx::createTexture2D(PaletteSize, PaletteSize, false, 1,
                bgraTextureUploadFormat(), BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

            if (!bgfx::isValid(m_hudPaletteTextureHandle))
            {
                return std::nullopt;
            }
        }

        const uint16_t index = uint16_t(m_hudPaletteSlotByColor.size());
        const std::array<uint8_t, 4> pixel = {
            uint8_t((abgrColor >> 16) & 0xffu),
            uint8_t((abgrColor >> 8) & 0xffu),
            uint8_t(abgrColor & 0xffu),
            uint8_t((abgrColor >> 24) & 0xffu)
        };
        bgfx::updateTexture2D(m_hudPaletteTextureHandle, 0, 0, index % PaletteSize, index / PaletteSize, 1, 1,
            copyBgraTextureUploadMemory(pixel.data(), uint32_t(pixel.size())));
        slot = m_hudPaletteSlotByColor.emplace(abgrColor, index).first;
    }

    // The texel centre: every sample of a quad with constant UVs reads only this colour, whatever the filtering.
    GameplayHudPaletteColor color;
    color.textureHandle = m_hudPaletteTextureHandle;
    color.u = (float(slot->second % PaletteSize) + 0.5f) / PaletteSize;
    color.v = (float(slot->second / PaletteSize) + 0.5f) / PaletteSize;
    return color;
}

std::optional<GameplayHudTextureHandle> GameplayUiRuntime::ensureSolidHudTextureLoaded(
    const std::string &textureName,
    uint32_t abgrColor)
{
    if (textureName.empty())
    {
        return std::nullopt;
    }

    const std::string cacheTextureName =
        toLowerCopy(textureName)
        + "_"
        + std::to_string((abgrColor >> 24) & 0xffu)
        + "_"
        + std::to_string((abgrColor >> 16) & 0xffu)
        + "_"
        + std::to_string((abgrColor >> 8) & 0xffu)
        + "_"
        + std::to_string(abgrColor & 0xffu);
    const auto existingIterator = m_hudTextureIndexByName.find(cacheTextureName);

    if (existingIterator != m_hudTextureIndexByName.end() && existingIterator->second < m_hudTextureHandles.size())
    {
        const GameplayHudTextureData &existing = m_hudTextureHandles[existingIterator->second];
        GameplayHudTextureHandle result = {};
        result.textureName = existing.textureName;
        result.width = existing.width;
        result.height = existing.height;
        result.textureHandle = existing.textureHandle;
        return result;
    }

    const uint64_t loadBeginTickCount = m_performanceFrameEnabled ? SDL_GetTicksNS() : 0;

    const std::array<uint8_t, 4> pixel = {
        static_cast<uint8_t>((abgrColor >> 16) & 0xffu),
        static_cast<uint8_t>((abgrColor >> 8) & 0xffu),
        static_cast<uint8_t>(abgrColor & 0xffu),
        static_cast<uint8_t>((abgrColor >> 24) & 0xffu)
    };

    GameplayHudTextureData textureHandle = {};
    textureHandle.textureName = cacheTextureName;
    textureHandle.width = 1;
    textureHandle.height = 1;
    textureHandle.physicalWidth = 1;
    textureHandle.physicalHeight = 1;
    textureHandle.bgraPixels.assign(pixel.begin(), pixel.end());
    textureHandle.textureHandle = createBgraTexture2D(
        1,
        1,
        pixel.data(),
        uint32_t(pixel.size()),
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        if (m_performanceFrameEnabled)
        {
            recordPerformanceAssetLoad(
                GameplayUiAssetLoadKind::SolidTexture,
                cacheTextureName,
                SDL_GetTicksNS() - loadBeginTickCount,
                false,
                1,
                1,
                true,
                abgrColor);
        }

        return std::nullopt;
    }

    const size_t index = m_hudTextureHandles.size();
    m_hudTextureHandles.push_back(std::move(textureHandle));
    m_hudTextureIndexByName[m_hudTextureHandles.back().textureName] = index;

    GameplayHudTextureHandle result = {};
    result.textureName = m_hudTextureHandles.back().textureName;
    result.width = m_hudTextureHandles.back().width;
    result.height = m_hudTextureHandles.back().height;
    result.textureHandle = m_hudTextureHandles.back().textureHandle;

    if (m_performanceFrameEnabled)
    {
        recordPerformanceAssetLoad(
            GameplayUiAssetLoadKind::SolidTexture,
            cacheTextureName,
            SDL_GetTicksNS() - loadBeginTickCount,
            true,
            1,
            1,
            true,
            abgrColor);
    }

    return result;
}

std::optional<GameplayHudTextureHandle> GameplayUiRuntime::ensureDynamicHudTexture(
    const std::string &textureName,
    int width,
    int height,
    const std::vector<uint8_t> &bgraPixels)
{
    const GameplayHudTextureData *pExistingTexture =
        m_performanceFrameEnabled
            ? GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName)
            : nullptr;
    const bool createsResource =
        m_performanceFrameEnabled
        && (pExistingTexture == nullptr
            || pExistingTexture->physicalWidth != width
            || pExistingTexture->physicalHeight != height);
    const uint64_t loadBeginTickCount = createsResource ? SDL_GetTicksNS() : 0;
    const std::optional<GameplayHudTextureHandle> result = GameplayHudCommon::ensureDynamicHudTexture(
        textureName,
        width,
        height,
        bgraPixels,
        m_hudTextureHandles,
        m_hudTextureIndexByName);

    if (createsResource)
    {
        recordPerformanceAssetLoad(
            GameplayUiAssetLoadKind::DynamicTexture,
            textureName,
            SDL_GetTicksNS() - loadBeginTickCount,
            result.has_value(),
            width,
            height);
    }

    return result;
}

std::optional<GameplayHudTextureHandle> GameplayUiRuntime::findCachedDynamicHudTexture(
    const std::string &textureName,
    const std::string &contentSignature) const
{
    auto signatureIterator = m_dynamicHudTextureContentSignatures.find(textureName);
    if (signatureIterator == m_dynamicHudTextureContentSignatures.end())
    {
        signatureIterator = m_dynamicHudTextureContentSignatures.find(toLowerCopy(textureName));
    }

    if (signatureIterator == m_dynamicHudTextureContentSignatures.end()
        || signatureIterator->second != contentSignature)
    {
        return std::nullopt;
    }

    const GameplayHudTextureData *pTexture = GameplayHudCommon::findHudTexture(
        m_hudTextureHandles,
        m_hudTextureIndexByName,
        textureName);

    if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
    {
        return std::nullopt;
    }

    return GameplayHudTextureHandle{
        .textureName = pTexture->textureName,
        .width = pTexture->width,
        .height = pTexture->height,
        .textureHandle = pTexture->textureHandle,
    };
}

void GameplayUiRuntime::setDynamicHudTextureContentSignature(
    const std::string &textureName,
    const std::string &contentSignature)
{
    m_dynamicHudTextureContentSignatures[toLowerCopy(textureName)] = contentSignature;
}

const std::vector<uint8_t> *GameplayUiRuntime::hudTexturePixels(
    const std::string &textureName,
    int &width,
    int &height)
{
    const std::optional<GameplayHudTextureHandle> texture = ensureHudTextureLoaded(textureName);

    if (!texture)
    {
        width = 0;
        height = 0;
        return nullptr;
    }

    const auto textureIt = m_hudTextureIndexByName.find(toLowerCopy(textureName));

    if (textureIt == m_hudTextureIndexByName.end() || textureIt->second >= m_hudTextureHandles.size())
    {
        width = 0;
        height = 0;
        return nullptr;
    }

    const GameplayHudTextureData &sourceTexture = m_hudTextureHandles[textureIt->second];
    width = sourceTexture.physicalWidth;
    height = sourceTexture.physicalHeight;
    return &GameplayHudCommon::hudTexturePixels(sourceTexture);
}

bool GameplayUiRuntime::ensureHudTextureDimensions(const std::string &textureName, int &width, int &height)
{
    const std::optional<GameplayHudTextureHandle> texture = ensureHudTextureLoaded(textureName);

    if (!texture)
    {
        width = 0;
        height = 0;
        return false;
    }

    width = texture->width;
    height = texture->height;
    return true;
}

bool GameplayUiRuntime::ensureItemIconTextureDimensions(const std::string &textureName, int &width, int &height)
{
    const std::optional<GameplayHudTextureHandle> texture = ensureItemIconTextureLoaded(textureName);

    if (!texture)
    {
        width = 0;
        height = 0;
        return false;
    }

    width = texture->width;
    height = texture->height;
    return true;
}

bool GameplayUiRuntime::tryGetOpaqueHudTextureBounds(
    const std::string &textureName,
    int &width,
    int &height,
    int &opaqueMinX,
    int &opaqueMinY,
    int &opaqueMaxX,
    int &opaqueMaxY)
{
    const std::optional<GameplayHudTextureHandle> texture = ensureHudTextureLoaded(textureName);

    if (!texture)
    {
        width = 0;
        height = 0;
        opaqueMinX = -1;
        opaqueMinY = -1;
        opaqueMaxX = -1;
        opaqueMaxY = -1;
        return false;
    }

    const GameplayHudTextureData *pTexture =
        GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName);

    if (pTexture == nullptr)
    {
        return false;
    }

    return GameplayHudCommon::tryGetOpaqueHudTextureBounds(
        *pTexture,
        pTexture->assetScaleTier,
        width,
        height,
        opaqueMinX,
        opaqueMinY,
        opaqueMaxX,
        opaqueMaxY);
}

std::optional<GameplayHudFontHandle> GameplayUiRuntime::findHudFont(const std::string &fontName)
{
    if (fontName.empty() || !loadHudFont(fontName))
    {
        return std::nullopt;
    }

    const GameplayHudFontData *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, fontName);

    if (pFont == nullptr)
    {
        return std::nullopt;
    }

    GameplayHudFontHandle result = {};
    result.fontName = pFont->fontName;
    result.fontHeight = pFont->fontHeight;
    result.mainTextureHandle = pFont->mainTextureHandle;
    result.shadowTextureHandle = pFont->shadowTextureHandle;
    return result;
}

float GameplayUiRuntime::measureHudTextWidth(const GameplayHudFontHandle &font, const std::string &text) const
{
    const GameplayHudFontData *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, font.fontName);
    return pFont != nullptr ? GameplayHudCommon::measureHudTextWidth(*pFont, text) : 0.0f;
}

std::vector<std::string> GameplayUiRuntime::wrapHudTextToWidth(
    const GameplayHudFontHandle &font,
    const std::string &text,
    float maxWidth) const
{
    const GameplayHudFontData *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, font.fontName);
    return pFont != nullptr ? GameplayHudCommon::wrapHudTextToWidth(*pFont, text, maxWidth)
                            : std::vector<std::string>{text};
}

bgfx::TextureHandle GameplayUiRuntime::ensureHudTextureColor(
    const GameplayHudTextureHandle &texture,
    uint32_t colorAbgr)
{
    const GameplayHudTextureData *pTexture =
        GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, texture.textureName);

    if (pTexture == nullptr)
    {
        bgfx::TextureHandle invalidHandle = BGFX_INVALID_HANDLE;
        return invalidHandle;
    }

    const bool cacheMiss =
        m_performanceFrameEnabled
        && std::none_of(
            m_hudTextureColorTextureHandles.begin(),
            m_hudTextureColorTextureHandles.end(),
            [&texture, colorAbgr](const GameplayHudTextureColorTextureData &entry)
            {
                return entry.textureName == texture.textureName
                    && entry.colorAbgr == colorAbgr
                    && entry.colorMode == GameplayHudTextureColorMode::Solid;
            });
    const uint64_t loadBeginTickCount = cacheMiss ? SDL_GetTicksNS() : 0;
    const bgfx::TextureHandle result =
        GameplayHudCommon::ensureHudTextureColor(*pTexture, colorAbgr, m_hudTextureColorTextureHandles);

    if (cacheMiss)
    {
        recordPerformanceAssetLoad(
            GameplayUiAssetLoadKind::HudTextureColor,
            texture.textureName,
            SDL_GetTicksNS() - loadBeginTickCount,
            bgfx::isValid(result),
            pTexture->physicalWidth,
            pTexture->physicalHeight,
            true,
            colorAbgr);
    }

    return result;
}

bgfx::TextureHandle GameplayUiRuntime::ensureHudTextureColorModulated(
    const GameplayHudTextureHandle &texture,
    uint32_t colorAbgr)
{
    const GameplayHudTextureData *pTexture =
        GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, texture.textureName);

    if (pTexture == nullptr)
    {
        return BGFX_INVALID_HANDLE;
    }

    const bool cacheMiss =
        m_performanceFrameEnabled
        && std::none_of(
            m_hudTextureColorTextureHandles.begin(),
            m_hudTextureColorTextureHandles.end(),
            [&texture, colorAbgr](const GameplayHudTextureColorTextureData &entry)
            {
                return entry.textureName == texture.textureName
                    && entry.colorAbgr == colorAbgr
                    && entry.colorMode == GameplayHudTextureColorMode::Modulated;
            });
    const uint64_t loadBeginTickCount = cacheMiss ? SDL_GetTicksNS() : 0;
    const bgfx::TextureHandle result = GameplayHudCommon::ensureHudTextureColorModulated(
        *pTexture,
        colorAbgr,
        m_hudTextureColorTextureHandles);

    if (cacheMiss)
    {
        recordPerformanceAssetLoad(
            GameplayUiAssetLoadKind::HudTextureColorModulated,
            texture.textureName,
            SDL_GetTicksNS() - loadBeginTickCount,
            bgfx::isValid(result),
            pTexture->physicalWidth,
            pTexture->physicalHeight,
            true,
            colorAbgr);
    }

    return result;
}

GameplayHudFontLayer GameplayUiRuntime::hudFontMainLayer(const GameplayHudFontHandle &font, uint32_t colorAbgr) const
{
    const GameplayHudFontData *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, font.fontName);
    return pFont != nullptr ? GameplayHudCommon::hudFontMainLayer(*pFont, colorAbgr) : GameplayHudFontLayer();
}

void GameplayUiRuntime::addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item)
{
    m_renderedInspectableHudItems.push_back(item);
}

bool GameplayUiRuntime::isOpaqueHudPixelAtPoint(const GameplayRenderedInspectableHudItem &item, float x, float y)
{
    if (item.textureName.empty()
        || item.width <= 0.0f
        || item.height <= 0.0f
        || x < item.x
        || x >= item.x + item.width
        || y < item.y
        || y >= item.y + item.height)
    {
        return false;
    }

    int textureWidth = 0;
    int textureHeight = 0;
    const std::optional<std::vector<uint8_t>> decodedPixels =
        GameplayHudCommon::loadHudBitmapPixelsBgraCached(
            m_pAssetFileSystem,
            m_assetLoadCache,
            item.textureName,
            textureWidth,
            textureHeight,
            item.textureUsesItemIconTransparency
                ? GameplayHudBitmapTransparencyMode::ItemIcon
                : GameplayHudBitmapTransparencyMode::HudColorKey);

    const std::vector<uint8_t> *pPixels = decodedPixels ? &*decodedPixels : nullptr;

    // Cooked-only art (Obsidian, cook_ui_textures.py) has no image to decode: use the loaded texture's pixels.
    if (pPixels == nullptr && !item.textureUsesItemIconTransparency && ensureHudTextureLoaded(item.textureName))
    {
        const GameplayHudTextureData *pTexture =
            GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, item.textureName);

        if (pTexture != nullptr && (pTexture->cookedSource != nullptr || pTexture->pCookedAssetFileSystem != nullptr))
        {
            pPixels = &GameplayHudCommon::hudTexturePixels(*pTexture);
            textureWidth = pTexture->physicalWidth;
            textureHeight = pTexture->physicalHeight;
        }
    }

    if (pPixels == nullptr || textureWidth <= 0 || textureHeight <= 0)
    {
        return true;
    }

    float normalizedX = std::clamp((x - item.x) / item.width, 0.0f, 0.999999f);
    float normalizedY = std::clamp((y - item.y) / item.height, 0.0f, 0.999999f);

    if (item.rotatedCounterClockwise)
    {
        const float rotatedX = std::clamp(1.0f - ((y - item.y) / item.height), 0.0f, 0.999999f);
        const float rotatedY = normalizedX;
        normalizedX = rotatedX;
        normalizedY = rotatedY;
    }

    const int pixelX = std::clamp(int(normalizedX * textureWidth), 0, textureWidth - 1);
    const int pixelY = std::clamp(int(normalizedY * textureHeight), 0, textureHeight - 1);
    const size_t pixelOffset =
        (static_cast<size_t>(pixelY) * static_cast<size_t>(textureWidth) + static_cast<size_t>(pixelX)) * 4;

    if (pixelOffset + 3 >= pPixels->size())
    {
        return false;
    }

    return (*pPixels)[pixelOffset + 3] > 0;
}

void GameplayUiRuntime::releaseHudGpuResources(bool destroyBgfxResources)
{
    for (bgfx::UniformHandle &uniform : m_previewUniforms)
    {
        if (destroyBgfxResources && bgfx::isValid(uniform))
        {
            bgfx::destroy(uniform);
        }
        uniform = BGFX_INVALID_HANDLE;
    }
    if (destroyBgfxResources)
    {
        clearHudResources();
        return;
    }

    for (GameplayHudTextureData &textureHandle : m_hudTextureHandles)
    {
        textureHandle.textureHandle = BGFX_INVALID_HANDLE;
    }

    for (GameplayHudFontData &fontHandle : m_hudFontHandles)
    {
        fontHandle.mainTextureHandle = BGFX_INVALID_HANDLE;
        fontHandle.shadowTextureHandle = BGFX_INVALID_HANDLE;
        fontHandle.tintTextureHandle = BGFX_INVALID_HANDLE;
    }

    for (GameplayHudTextureColorTextureData &textureHandle : m_hudTextureColorTextureHandles)
    {
        textureHandle.textureHandle = BGFX_INVALID_HANDLE;
    }

    m_hudTextureHandles.clear();
    m_hudTextureUvScales.clear();
    m_hudTextureIndexByName.clear();
    m_hudFontHandles.clear();
    m_hudTextureColorTextureHandles.clear();
    m_hudPaletteTextureHandle = BGFX_INVALID_HANDLE;
    m_hudPaletteSlotByColor.clear();
}

void GameplayUiRuntime::bindHudRenderBackend(const GameplayHudRenderBackend &backend)
{
    m_hudRenderBackend = backend;
}

void GameplayUiRuntime::bindSpriteAtlasCache(SpriteAtlasCache &cache)
{
    m_pSpriteAtlasCache = &cache;
}

uint32_t GameplayUiRuntime::actorInspectAnimationTicks(bool visible, uint32_t nowTicks)
{
    return m_actorInspectClock.update(visible, nowTicks);
}

void GameplayUiRuntime::bindActorModelPreview(ActorModelPreview &preview)
{
    m_pActorModelPreview = &preview;
}

void GameplayUiRuntime::renderActorInspectPreview(const IGameplayWorldRuntime &world, size_t actorIndex,
    uint32_t animationTicks, const std::string &name, int16_t paletteId, const GameplayResolvedHudLayoutElement &rect,
    float scale, int yOffset)
{
    if (!hasHudRenderResources())
    {
        return;
    }
    if (m_pActorModelPreview != nullptr && m_pAssetFileSystem != nullptr)
    {
        const bgfx::TextureHandle portrait =
            m_pActorModelPreview->render(world, actorIndex, rect.width, animationTicks, *m_pAssetFileSystem);
        if (bgfx::isValid(portrait))
        {
            const bool bottomUp = bgfx::getCaps()->originBottomLeft;
            submitHudTexturedQuad(portrait, rect.x, rect.y, rect.width, rect.width, 0.0f, bottomUp ? 1.0f : 0.0f,
                1.0f, bottomUp ? 0.0f : 1.0f, TextureFilterProfile::UiIllustration);
            return;
        }
    }
    if (m_pAssetFileSystem == nullptr || name.empty())
    {
        return;
    }
    SpriteBillboardTexture texture;
    if (Engine::parseSpriteAtlasReference(name))
    {
        if (m_pSpriteAtlasCache == nullptr
            || !m_pSpriteAtlasCache->load(*m_pAssetFileSystem, name, paletteId, texture))
        {
            return;
        }
    }
    else
    {
        int width = 0;
        int height = 0;
        Engine::AssetScaleTier loadedTier = Engine::AssetScaleTier::X1;
        const std::optional<std::vector<uint8_t>> pixels =
            loadSpriteBitmapPixelsBgraCached(name, paletteId, width, height, &loadedTier);
        if (!pixels || width <= 0 || height <= 0)
        {
            return;
        }
        const std::optional<GameplayHudTextureHandle> bitmap = ensureDynamicHudTexture(
            "__actor_inspect_preview_" + name + "_" + std::to_string(paletteId), width, height, *pixels);
        if (!bitmap)
        {
            return;
        }
        texture.textureHandle = bitmap->textureHandle;
        texture.width = Engine::scalePhysicalPixelsToLogical(width, loadedTier);
        texture.height = Engine::scalePhysicalPixelsToLogical(height, loadedTier);
        texture.canvasWidth = texture.width;
        texture.canvasHeight = texture.height;
    }
    const HudSpritePreviewQuad quad = actorInspectSpriteQuad(rect.x, rect.y, rect.width, scale,
        texture.width, texture.height, texture.offsetX, texture.offsetY, texture.canvasHeight, yOffset);
    if (quad.width <= 0 || quad.height <= 0)
    {
        return;
    }
    if (!texture.atlas)
    {
        submitHudTexturedQuad(texture.textureHandle, quad.x, quad.y, quad.width, quad.height,
            quad.u0, quad.v0, quad.u1, quad.v1, TextureFilterProfile::Billboard);
        return;
    }
    bgfx::VertexLayout layout;
    layout.begin().add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true).end();
    bgfx::TransientVertexBuffer vertices = {};
    bgfx::TransientIndexBuffer indices = {};
    if (!bgfx::allocTransientBuffers(&vertices, layout, 4, &indices, 6))
    {
        return;
    }
    struct Vertex { float x; float y; float z; float u; float v; uint32_t color; };
    Vertex *pVertices = reinterpret_cast<Vertex *>(vertices.data);
    pVertices[0] = {quad.x, quad.y, 0, quad.u0, quad.v0, 0xffffffffu};
    pVertices[1] = {quad.x + quad.width, quad.y, 0, quad.u1, quad.v0, 0xffffffffu};
    pVertices[2] = {quad.x + quad.width, quad.y + quad.height, 0, quad.u1, quad.v1, 0xffffffffu};
    pVertices[3] = {quad.x, quad.y + quad.height, 0, quad.u0, quad.v1, 0xffffffffu};
    const std::array<uint16_t, 6> corners = {{0, 1, 2, 0, 2, 3}};
    std::copy(corners.begin(), corners.end(), reinterpret_cast<uint16_t *>(indices.data));
    constexpr std::array<const char *, 6> names = {{"u_billboardAmbient", "u_billboardOverrideColor",
        "u_billboardOutlineParams", "u_fogColor", "u_fogDensities", "u_fogDistances"}};
    const float clear[4] = {0, 0, 0, 0};
    const float distances[4] = {1, 2, 3, 0};
    for (size_t i = 0; i < names.size(); ++i)
    {
        if (!bgfx::isValid(m_previewUniforms[i]))
        {
            m_previewUniforms[i] = bgfx::createUniform(names[i], bgfx::UniformType::Vec4);
        }
        bgfx::setUniform(m_previewUniforms[i], i == names.size() - 1 ? distances : clear);
    }
    float model[16] = {};
    bx::mtxIdentity(model);
    bgfx::setTransform(model);
    bgfx::setVertexBuffer(0, &vertices);
    bgfx::setIndexBuffer(&indices);
    bindTexture(0, m_hudRenderBackend.textureSamplerHandle, texture.textureHandle,
        TextureFilterProfile::Billboard, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(m_hudRenderBackend.viewId, m_pSpriteAtlasCache->bind(texture, BGFX_INVALID_HANDLE));
}

void GameplayUiRuntime::clearHudRenderBackend()
{
    m_hudRenderBackend = {};
}

bool GameplayUiRuntime::hasHudRenderResources() const
{
    return bgfx::isValid(m_hudRenderBackend.texturedProgramHandle)
        && bgfx::isValid(m_hudRenderBackend.tintedProgramHandle)
        && bgfx::isValid(m_hudRenderBackend.tintUniformHandle)
        && bgfx::isValid(m_hudRenderBackend.textureSamplerHandle);
}

void GameplayUiRuntime::prepareHudView(int width, int height) const
{
    if (!hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }

    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth);
    bgfx::setViewRect(m_hudRenderBackend.viewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewMode(m_hudRenderBackend.viewId, bgfx::ViewMode::Sequential);
    bgfx::setViewTransform(m_hudRenderBackend.viewId, nullptr, projectionMatrix);
    bgfx::touch(m_hudRenderBackend.viewId);
}

void GameplayUiRuntime::registerHudTextureUvScales(size_t firstTexture)
{
    for (size_t index = firstTexture; index < m_hudTextureHandles.size(); ++index)
    {
        const GameplayHudTextureData &texture = m_hudTextureHandles[index];
        if (texture.uScale != 1.0f || texture.vScale != 1.0f)
        {
            m_hudTextureUvScales[texture.textureHandle.idx] = {texture.uScale, texture.vScale};
        }
    }
}

std::array<float, 2> GameplayUiRuntime::hudTextureUvScale(bgfx::TextureHandle textureHandle) const
{
    const auto scale = m_hudTextureUvScales.find(textureHandle.idx);
    return scale != m_hudTextureUvScales.end() ? scale->second : std::array<float, 2>{1.0f, 1.0f};
}

void GameplayUiRuntime::submitHudTexturedQuad(
    bgfx::TextureHandle textureHandle,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    float u0,
    float v0,
    float u1,
    float v1,
    TextureFilterProfile filterProfile,
    float rotationRadians) const
{
    if (!hasHudRenderResources()
        || !bgfx::isValid(textureHandle)
        || quadWidth <= 0.0f
        || quadHeight <= 0.0f)
    {
        return;
    }

    bgfx::TransientVertexBuffer vertexBuffer = {};
    bgfx::TransientIndexBuffer indexBuffer = {};

    if (!bgfx::allocTransientBuffers(
            &vertexBuffer,
            gameplayHudQuadVertexLayout(),
            4,
            &indexBuffer,
            6))
    {
        return;
    }

    struct HudQuadVertex
    {
        float x;
        float y;
        float z;
        float u;
        float v;
    };

    const std::array<float, 2> uvScale = hudTextureUvScale(textureHandle);
    u0 *= uvScale[0];
    u1 *= uvScale[0];
    v0 *= uvScale[1];
    v1 *= uvScale[1];
    HudQuadVertex *pVertices = reinterpret_cast<HudQuadVertex *>(vertexBuffer.data);
    pVertices[0] = {x, y, 0.0f, u0, v0};
    pVertices[1] = {x + quadWidth, y, 0.0f, u1, v0};
    pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
    pVertices[3] = {x, y + quadHeight, 0.0f, u0, v1};

    if (rotationRadians != 0.0f)
    {
        const float centerX = x + quadWidth * 0.5f;
        const float centerY = y + quadHeight * 0.5f;
        const float cosine = std::cos(rotationRadians);
        const float sine = std::sin(rotationRadians);
        for (size_t i = 0; i < 4; ++i)
        {
            const float dx = pVertices[i].x - centerX;
            const float dy = pVertices[i].y - centerY;
            pVertices[i].x = centerX + dx * cosine - dy * sine;
            pVertices[i].y = centerY + dx * sine + dy * cosine;
        }
    }

    uint16_t *pIndices = reinterpret_cast<uint16_t *>(indexBuffer.data);
    pIndices[0] = 0;
    pIndices[1] = 1;
    pIndices[2] = 2;
    pIndices[3] = 0;
    pIndices[4] = 2;
    pIndices[5] = 3;

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &vertexBuffer);
    bgfx::setIndexBuffer(&indexBuffer);
    bindTexture(
        0,
        m_hudRenderBackend.textureSamplerHandle,
        textureHandle,
        filterProfile,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(m_hudRenderBackend.viewId, m_hudRenderBackend.texturedProgramHandle);
}

void GameplayUiRuntime::submitHudTexturedEllipse(
    bgfx::TextureHandle textureHandle, float x, float y, float width, float height,
    float u0, float v0, float u1, float v1) const
{
    if (!hasHudRenderResources() || !bgfx::isValid(textureHandle) || width <= 0.0f || height <= 0.0f)
    {
        return;
    }
    constexpr uint16_t segments = 96;
    bgfx::TransientVertexBuffer vertices = {};
    bgfx::TransientIndexBuffer indices = {};
    if (!bgfx::allocTransientBuffers(&vertices, gameplayHudQuadVertexLayout(), segments + 1,
        &indices, segments * 3))
    {
        return;
    }
    struct Vertex { float x; float y; float z; float u; float v; };
    Vertex *pVertices = reinterpret_cast<Vertex *>(vertices.data);
    uint16_t *pIndices = reinterpret_cast<uint16_t *>(indices.data);
    const std::array<float, 2> uvScale = hudTextureUvScale(textureHandle);
    u0 *= uvScale[0];
    u1 *= uvScale[0];
    v0 *= uvScale[1];
    v1 *= uvScale[1];
    pVertices[0] = {x + width * 0.5f, y + height * 0.5f, 0.0f, (u0 + u1) * 0.5f, (v0 + v1) * 0.5f};
    for (uint16_t i = 0; i < segments; ++i)
    {
        const float angle = i * 6.28318530718f / segments;
        const float u = 0.5f + 0.5f * std::cos(angle);
        const float v = 0.5f + 0.5f * std::sin(angle);
        pVertices[i + 1] = {x + width * u, y + height * v, 0.0f, u0 + (u1 - u0) * u, v0 + (v1 - v0) * v};
        pIndices[i * 3] = 0;
        pIndices[i * 3 + 1] = i + 1;
        pIndices[i * 3 + 2] = (i + 1) % segments + 1;
    }
    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &vertices);
    bgfx::setIndexBuffer(&indices);
    bindTexture(0, m_hudRenderBackend.textureSamplerHandle, textureHandle, TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(m_hudRenderBackend.viewId, m_hudRenderBackend.texturedProgramHandle);
}

void GameplayUiRuntime::submitHudTexturedArc(bgfx::TextureHandle textureHandle,
    const GameplayResolvedHudLayoutElement &rect, float strokeWidth, float startDegrees, float sweepDegrees,
    float begin, float end, float uRepeat) const
{
    const HudArcRange range = hudArcRange(sweepDegrees, begin, end);
    if (!hasHudRenderResources() || !bgfx::isValid(textureHandle) || range.segments == 0
        || rect.width <= 0 || rect.height <= 0 || strokeWidth <= 0 || !std::isfinite(startDegrees))
    {
        return;
    }
    bgfx::TransientVertexBuffer vertices = {};
    bgfx::TransientIndexBuffer indices = {};
    if (!bgfx::allocTransientBuffers(&vertices, gameplayHudQuadVertexLayout(), 4 * (range.segments + 1),
        &indices, 18 * range.segments))
    {
        return;
    }
    const HudArcMesh &mesh = m_hudArcMeshCache.get({rect.x, rect.y, rect.width, rect.height,
        strokeWidth, startDegrees, sweepDegrees, range.begin, range.end});
    HudArcMeshVertex *pArcVertices = reinterpret_cast<HudArcMeshVertex *>(vertices.data);
    std::copy(mesh.vertices.begin(), mesh.vertices.end(), pArcVertices);
    const std::array<float, 2> uvScale = hudTextureUvScale(textureHandle);
    for (size_t index = 0; index < mesh.vertices.size(); ++index)
    {
        pArcVertices[index].u *= uvScale[0] * uRepeat;
        pArcVertices[index].v *= uvScale[1];
    }
    std::copy(mesh.indices.begin(), mesh.indices.end(), reinterpret_cast<uint16_t *>(indices.data));
    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &vertices);
    bgfx::setIndexBuffer(&indices);
    bindTexture(0, m_hudRenderBackend.textureSamplerHandle, textureHandle, TextureFilterProfile::Ui,
        (uRepeat == 1 ? BGFX_SAMPLER_U_CLAMP : 0) | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(m_hudRenderBackend.viewId, m_hudRenderBackend.texturedProgramHandle);
}

void GameplayUiRuntime::submitHudTexturedQuadRotatedCounterClockwise(
    bgfx::TextureHandle textureHandle,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    TextureFilterProfile filterProfile) const
{
    if (!hasHudRenderResources()
        || !bgfx::isValid(textureHandle)
        || quadWidth <= 0.0f
        || quadHeight <= 0.0f)
    {
        return;
    }

    bgfx::TransientVertexBuffer vertexBuffer = {};
    bgfx::TransientIndexBuffer indexBuffer = {};

    if (!bgfx::allocTransientBuffers(
            &vertexBuffer,
            gameplayHudQuadVertexLayout(),
            4,
            &indexBuffer,
            6))
    {
        return;
    }

    struct HudQuadVertex
    {
        float x;
        float y;
        float z;
        float u;
        float v;
    };

    HudQuadVertex *pVertices = reinterpret_cast<HudQuadVertex *>(vertexBuffer.data);
    const std::array<float, 2> uvScale = hudTextureUvScale(textureHandle);
    pVertices[0] = {x, y, 0.0f, uvScale[0], 0.0f};
    pVertices[1] = {x + quadWidth, y, 0.0f, uvScale[0], uvScale[1]};
    pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, 0.0f, uvScale[1]};
    pVertices[3] = {x, y + quadHeight, 0.0f, 0.0f, 0.0f};

    uint16_t *pIndices = reinterpret_cast<uint16_t *>(indexBuffer.data);
    pIndices[0] = 0;
    pIndices[1] = 1;
    pIndices[2] = 2;
    pIndices[3] = 0;
    pIndices[4] = 2;
    pIndices[5] = 3;

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &vertexBuffer);
    bgfx::setIndexBuffer(&indexBuffer);
    bindTexture(
        0,
        m_hudRenderBackend.textureSamplerHandle,
        textureHandle,
        filterProfile,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(m_hudRenderBackend.viewId, m_hudRenderBackend.texturedProgramHandle);
}

void GameplayUiRuntime::submitHudQuadBatch(
    std::span<const GameplayHudBatchQuad> quads,
    TextureFilterProfile filterProfile) const
{
    if (!hasHudRenderResources() || quads.empty())
    {
        return;
    }

    const auto canBatchRun =
        [](const GameplayHudBatchQuad &left, const GameplayHudBatchQuad &right) -> bool
        {
            if (left.textureHandle.idx != right.textureHandle.idx
                || left.clipped != right.clipped
                || left.tintAbgr != right.tintAbgr)
            {
                return false;
            }

            if (!left.clipped)
            {
                return true;
            }

            return left.scissorX == right.scissorX
                && left.scissorY == right.scissorY
                && left.scissorWidth == right.scissorWidth
                && left.scissorHeight == right.scissorHeight;
        };

    struct HudQuadVertex
    {
        float x;
        float y;
        float z;
        float u;
        float v;
    };

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    const uint32_t identityTransform = bgfx::setTransform(modelMatrix);
    size_t quadIndex = 0;

    while (quadIndex < quads.size())
    {
        size_t runEnd = quadIndex + 1;

        while (runEnd < quads.size() && canBatchRun(quads[runEnd - 1], quads[runEnd]))
        {
            ++runEnd;
        }

        while (quadIndex < runEnd)
        {
            const uint32_t availableVertexCount = bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>((runEnd - quadIndex) * 6),
                gameplayHudQuadVertexLayout());

            if (availableVertexCount < 6)
            {
                return;
            }

            const size_t quadCount = std::min<size_t>(runEnd - quadIndex, availableVertexCount / 6);
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(quadCount * 6),
                gameplayHudQuadVertexLayout());
            HudQuadVertex *pVertices = reinterpret_cast<HudQuadVertex *>(transientVertexBuffer.data);

            for (size_t localIndex = 0; localIndex < quadCount; ++localIndex)
            {
                const GameplayHudBatchQuad &quad = quads[quadIndex + localIndex];
                HudQuadVertex *pQuadVertices = pVertices + localIndex * 6;

                if (quad.line)
                {
                    const float dx = quad.x2 - quad.x;
                    const float dy = quad.y2 - quad.y;
                    const float length = std::sqrt(dx * dx + dy * dy);
                    float normalX = 0.0f;
                    float normalY = 0.0f;

                    if (length > 0.0001f)
                    {
                        const float halfThickness = std::max(1.0f, quad.width) * 0.5f;
                        normalX = -dy / length * halfThickness;
                        normalY = dx / length * halfThickness;
                    }

                    pQuadVertices[0] = {quad.x + normalX, quad.y + normalY, 0.0f, quad.u0, quad.v0};
                    pQuadVertices[1] = {quad.x2 + normalX, quad.y2 + normalY, 0.0f, quad.u1, quad.v0};
                    pQuadVertices[2] = {quad.x2 - normalX, quad.y2 - normalY, 0.0f, quad.u1, quad.v1};
                    pQuadVertices[3] = {quad.x + normalX, quad.y + normalY, 0.0f, quad.u0, quad.v0};
                    pQuadVertices[4] = {quad.x2 - normalX, quad.y2 - normalY, 0.0f, quad.u1, quad.v1};
                    pQuadVertices[5] = {quad.x - normalX, quad.y - normalY, 0.0f, quad.u0, quad.v1};
                }
                else
                {
                    pQuadVertices[0] = {quad.x, quad.y, 0.0f, quad.u0, quad.v0};
                    pQuadVertices[1] = {quad.x + quad.width, quad.y, 0.0f, quad.u1, quad.v0};
                    pQuadVertices[2] = {quad.x + quad.width, quad.y + quad.height, 0.0f, quad.u1, quad.v1};
                    pQuadVertices[3] = {quad.x, quad.y, 0.0f, quad.u0, quad.v0};
                    pQuadVertices[4] = {quad.x + quad.width, quad.y + quad.height, 0.0f, quad.u1, quad.v1};
                    pQuadVertices[5] = {quad.x, quad.y + quad.height, 0.0f, quad.u0, quad.v1};
                }

                const std::array<float, 2> uvScale = hudTextureUvScale(quad.textureHandle);
                for (size_t vertex = 0; vertex < 6; ++vertex)
                {
                    pQuadVertices[vertex].u *= uvScale[0];
                    pQuadVertices[vertex].v *= uvScale[1];
                }
            }

            const GameplayHudBatchQuad &firstQuad = quads[quadIndex];
            bgfx::setTransform(identityTransform);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bindTexture(
                0,
                m_hudRenderBackend.textureSamplerHandle,
                firstQuad.textureHandle,
                filterProfile,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

            if (firstQuad.clipped)
            {
                bgfx::setScissor(
                    firstQuad.scissorX,
                    firstQuad.scissorY,
                    firstQuad.scissorWidth,
                    firstQuad.scissorHeight);
            }

            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(m_hudRenderBackend.viewId, hudProgramForTint(firstQuad.tintAbgr));
            quadIndex += quadCount;
        }
    }
}

bgfx::ProgramHandle GameplayUiRuntime::hudProgramForTint(uint32_t tintAbgr) const
{
    if (tintAbgr == 0xffffffffu)
    {
        return m_hudRenderBackend.texturedProgramHandle;
    }

    const float tint[4] = {
        float(tintAbgr & 0xffu) / 255.0f,
        float((tintAbgr >> 8) & 0xffu) / 255.0f,
        float((tintAbgr >> 16) & 0xffu) / 255.0f,
        float((tintAbgr >> 24) & 0xffu) / 255.0f};
    bgfx::setUniform(m_hudRenderBackend.tintUniformHandle, tint);
    return m_hudRenderBackend.tintedProgramHandle;
}

void GameplayUiRuntime::submitWorldHudQuadBatch(std::span<const GameplayHudBatchQuad> quads,
    uint16_t viewId, const bx::Vec3 &origin, const bx::Vec3 &right, const bx::Vec3 &up,
    TextureFilterProfile filterProfile) const
{
    if (!hasHudRenderResources())
    {
        return;
    }
    float identity[16];
    bx::mtxIdentity(identity);
    size_t first = 0;
    while (first < quads.size())
    {
        size_t end = first + 1;
        while (end < quads.size()
            && quads[end].textureHandle.idx == quads[first].textureHandle.idx
            && quads[end].tintAbgr == quads[first].tintAbgr)
        {
            ++end;
        }
        const uint32_t count = uint32_t((end - first) * 6);
        bgfx::TransientVertexBuffer buffer;
        if (bgfx::getAvailTransientVertexBuffer(count, gameplayHudQuadVertexLayout()) != count)
        {
            return;
        }
        bgfx::allocTransientVertexBuffer(&buffer, count, gameplayHudQuadVertexLayout());
        HudArcMeshVertex *pVertices = reinterpret_cast<HudArcMeshVertex *>(buffer.data);
        const auto vertex = [&](float x, float y, float u, float v)
        {
            return HudArcMeshVertex{origin.x + right.x * x - up.x * y,
                origin.y + right.y * x - up.y * y, origin.z + right.z * x - up.z * y, u, v};
        };
        for (size_t index = first; index < end; ++index)
        {
            const GameplayHudBatchQuad &q = quads[index];
            const std::array<float, 2> uvScale = hudTextureUvScale(q.textureHandle);
            const float u0 = q.u0 * uvScale[0];
            const float u1 = q.u1 * uvScale[0];
            const float v0 = q.v0 * uvScale[1];
            const float v1 = q.v1 * uvScale[1];
            const HudArcMeshVertex tl = vertex(q.x, q.y, u0, v0);
            const HudArcMeshVertex tr = vertex(q.x + q.width, q.y, u1, v0);
            const HudArcMeshVertex br = vertex(q.x + q.width, q.y + q.height, u1, v1);
            const HudArcMeshVertex bl = vertex(q.x, q.y + q.height, u0, v1);
            *pVertices++ = tl;
            *pVertices++ = tr;
            *pVertices++ = br;
            *pVertices++ = tl;
            *pVertices++ = br;
            *pVertices++ = bl;
        }
        bgfx::setTransform(identity);
        bgfx::setVertexBuffer(0, &buffer);
        bindTexture(0, m_hudRenderBackend.textureSamplerHandle, quads[first].textureHandle,
            filterProfile, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA
            | BGFX_STATE_DEPTH_TEST_LEQUAL);
        bgfx::submit(viewId, hudProgramForTint(quads[first].tintAbgr));
        first = end;
    }
}

void GameplayUiRuntime::renderHudFontLayer(
    const GameplayHudFontHandle &font,
    const GameplayHudFontLayer &layer,
    const std::string &text,
    float textX,
    float textY,
    float fontScale,
    const GameplayResolvedHudLayoutElement *pClip) const
{
    const GameplayHudFontData *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, font.fontName);

    if (pFont == nullptr || !hasHudRenderResources() || !bgfx::isValid(layer.textureHandle))
    {
        return;
    }

    // Bound scratch space and preserve glyph/layer order, including unusually long unwrapped lines.
    std::array<GameplayHudBatchQuad, 128> quads;
    size_t quadCount = 0;
    const TextureFilterProfile filter = pFont->smooth
        ? TextureFilterProfile::SmoothText : TextureFilterProfile::Text;
    const auto flush = [this, &quads, &quadCount, filter]()
    {
        // Font quads do not use per-quad scissor overrides.
        submitHudQuadBatch(std::span<const GameplayHudBatchQuad>(quads.data(), quadCount), filter);
        quadCount = 0;
    };

    GameplayHudCommon::renderHudFontLayer(
        *pFont,
        layer,
        text,
        textX,
        textY,
        fontScale,
        [&quads, &quadCount, &flush, pClip](bgfx::TextureHandle submittedTextureHandle,
               float x,
               float y,
               float quadWidth,
               float quadHeight,
               float u0,
               float v0,
               float u1,
               float v1,
               TextureFilterProfile,
               uint32_t tintAbgr)
        {
            if (quadWidth <= 0.0f || quadHeight <= 0.0f)
            {
                return;
            }
            if (pClip != nullptr)
            {
                const float left = std::max(x, pClip->x);
                const float top = std::max(y, pClip->y);
                const float right = std::min(x + quadWidth, pClip->x + pClip->width);
                const float bottom = std::min(y + quadHeight, pClip->y + pClip->height);
                if (left >= right || top >= bottom)
                {
                    return;
                }
                const float uSpan = u1 - u0;
                const float vSpan = v1 - v0;
                u1 = u0 + uSpan * (right - x) / quadWidth;
                v1 = v0 + vSpan * (bottom - y) / quadHeight;
                u0 += uSpan * (left - x) / quadWidth;
                v0 += vSpan * (top - y) / quadHeight;
                x = left;
                y = top;
                quadWidth = right - left;
                quadHeight = bottom - top;
            }
            GameplayHudBatchQuad &quad = quads[quadCount++];
            quad = {};
            quad.textureHandle = submittedTextureHandle;
            quad.tintAbgr = tintAbgr;
            quad.x = x;
            quad.y = y;
            quad.width = quadWidth;
            quad.height = quadHeight;
            quad.u0 = u0;
            quad.v0 = v0;
            quad.u1 = u1;
            quad.v1 = v1;
            if (quadCount == quads.size())
            {
                flush();
            }
        });
    flush();
}

bool GameplayUiRuntime::ensurePortraitRuntimeLoaded()
{
    if (m_portraitRuntimeLoaded)
    {
        return true;
    }

    if (m_pDataRepository == nullptr)
    {
        return false;
    }

    m_portraitRuntimeLoaded = true;
    return true;
}

void GameplayUiRuntime::resetPortraitFxStates(size_t memberCount)
{
    m_portraitFxStates.assign(memberCount, {});
}

void GameplayUiRuntime::resetPortraitPresentationState(size_t memberCount)
{
    m_portraitPresentationState.meters = {};
    m_portraitPresentationState.lastAnimationUpdateTicks = 0;
    m_portraitPresentationState.memberSpeechCooldownUntilTicks.assign(memberCount, 0);
    m_portraitPresentationState.memberCombatSpeechCooldownUntilTicks.assign(memberCount, 0);
    m_portraitPresentationState.memberSpeechLastPlayedTicks.assign(memberCount, {});
}

GameplayPortraitPresentationState &GameplayUiRuntime::portraitPresentationState()
{
    return m_portraitPresentationState;
}

const GameplayPortraitPresentationState &GameplayUiRuntime::portraitPresentationState() const
{
    return m_portraitPresentationState;
}

std::string GameplayUiRuntime::resolvePortraitTextureName(const Character &character) const
{
    if (character.portraitState == PortraitId::Eradicated)
    {
        return "ERADCATE";
    }

    if (character.portraitState == PortraitId::Dead)
    {
        return "DEAD";
    }

    if (!m_portraitRuntimeLoaded)
    {
        return character.portraitTextureName;
    }

    if (character.portraitState == PortraitId::Normal)
    {
        return portraitTextureNameForCharacterFrame(character, 1);
    }

    const PortraitFrameEntry *pFrame =
        m_pDataRepository->portraitFrameTable().getFrame(character.portraitState, character.portraitElapsedTicks);

    if (pFrame != nullptr && pFrame->textureIndex > 0)
    {
        return portraitTextureNameForCharacterFrame(character, pFrame->textureIndex);
    }

    return character.portraitTextureName;
}

bool GameplayUiRuntime::triggerPortraitFxAnimation(
    const std::string &animationName,
    const std::vector<size_t> &memberIndices)
{
    if (!ensurePortraitRuntimeLoaded() || memberIndices.empty())
    {
        return false;
    }

    const std::optional<size_t> animationId = m_pDataRepository->iconFrameTable().findAnimationIdByName(animationName);

    if (!animationId)
    {
        return false;
    }

    const uint32_t startedTicks = currentAnimationTicks();
    bool triggered = false;

    for (size_t memberIndex : memberIndices)
    {
        if (memberIndex >= m_portraitFxStates.size())
        {
            // Party members can be recruited without reinitializing the current map UI.
            m_portraitFxStates.resize(memberIndex + 1);
        }

        GameplayPortraitFxState &state = m_portraitFxStates[memberIndex];
        state.active = true;
        state.animationId = *animationId;
        state.startedTicks = startedTicks;
        triggered = true;
    }

    return triggered;
}

void GameplayUiRuntime::triggerPortraitSpellFx(const PartySpellCastResult &result)
{
    if (!ensurePortraitRuntimeLoaded())
    {
        return;
    }

    const SpellFxEntry *pSpellFxEntry = m_pDataRepository->spellFxTable().findBySpellId(result.spellId);

    if (pSpellFxEntry == nullptr)
    {
        return;
    }

    triggerPortraitFxAnimation(pSpellFxEntry->animationName, result.affectedCharacterIndices);
}

const PortraitFxEventEntry *GameplayUiRuntime::findPortraitFxEvent(PortraitFxEventKind kind) const
{
    return m_pDataRepository != nullptr ? m_pDataRepository->portraitFxEventTable().findByKind(kind) : nullptr;
}

const FaceAnimationEntry *GameplayUiRuntime::findFaceAnimation(FaceAnimationId animationId) const
{
    return m_portraitRuntimeLoaded ? m_pDataRepository->faceAnimationTable().find(animationId) : nullptr;
}

uint32_t GameplayUiRuntime::defaultPortraitAnimationLengthTicks(PortraitId portraitId) const
{
    const int32_t animationLengthTicks = m_pDataRepository->portraitFrameTable().animationLengthTicks(portraitId);

    if (animationLengthTicks > 0)
    {
        return animationLengthTicks;
    }

    return 48u;
}

void GameplayUiRuntime::renderPortraitFx(
    size_t memberIndex,
    float portraitX,
    float portraitY,
    float portraitWidth,
    float portraitHeight) const
{
    if (memberIndex >= m_portraitFxStates.size() || !m_portraitRuntimeLoaded)
    {
        return;
    }

    const GameplayPortraitFxState &state = m_portraitFxStates[memberIndex];

    if (!state.active)
    {
        return;
    }

    const int32_t animationLengthTicks = m_pDataRepository->iconFrameTable().animationLengthTicks(state.animationId);
    const uint32_t nowTicks = currentAnimationTicks();
    const uint32_t elapsedTicks = nowTicks - state.startedTicks;

    if (animationLengthTicks <= 0 || elapsedTicks >= static_cast<uint32_t>(animationLengthTicks))
    {
        return;
    }

    const IconFrameEntry *pFrame = m_pDataRepository->iconFrameTable().getFrame(state.animationId, elapsedTicks);

    if (pFrame == nullptr || pFrame->textureName.empty())
    {
        return;
    }

    const std::optional<GameplayHudTextureHandle> texture =
        const_cast<GameplayUiRuntime *>(this)->ensureHudTextureLoaded(pFrame->textureName);

    if (!texture || texture->width <= 0 || texture->height <= 0)
    {
        return;
    }

    const float textureAspectRatio = static_cast<float>(texture->width) / static_cast<float>(texture->height);
    const float renderHeight = portraitHeight;
    const float renderWidth = renderHeight * textureAspectRatio;
    const float renderX = portraitX + (portraitWidth - renderWidth) * 0.5f;
    const float renderY = portraitY;
    submitHudTexturedQuad(texture->textureHandle, renderX, renderY, renderWidth, renderHeight);
}

bool GameplayUiRuntime::initializeHouseVideoPlayer()
{
    if (m_houseVideoPlayerInitialized)
    {
        return true;
    }

    m_houseVideoPlayerInitialized = m_houseVideoPlayer.initialize();
    return m_houseVideoPlayerInitialized;
}

void GameplayUiRuntime::shutdownHouseVideoPlayer()
{
    if (!m_houseVideoPlayerInitialized)
    {
        return;
    }

    m_houseVideoPlayer.shutdown();
    m_houseVideoPlayerInitialized = false;
}

void GameplayUiRuntime::stopHouseVideoPlayback()
{
    if (m_houseVideoPlayerInitialized)
    {
        m_houseVideoPlayer.stop();
    }
}

bool GameplayUiRuntime::playHouseVideo(const std::string &videoStem)
{
    return initializeHouseVideoPlayer()
        && m_pAssetFileSystem != nullptr
        && m_houseVideoPlayer.play(*m_pAssetFileSystem, videoStem);
}

bool GameplayUiRuntime::playHouseVideo(const std::string &videoStem, const std::string &videoDirectory)
{
    return initializeHouseVideoPlayer()
        && m_pAssetFileSystem != nullptr
        && m_houseVideoPlayer.play(*m_pAssetFileSystem, videoStem, videoDirectory);
}

void GameplayUiRuntime::setHouseVideoAudioVolume(float volume)
{
    if (initializeHouseVideoPlayer())
    {
        m_houseVideoPlayer.setAudioVolume(volume);
    }
}

void GameplayUiRuntime::updateHouseVideoPlayback(float deltaSeconds)
{
    if (m_houseVideoPlayerInitialized)
    {
        m_houseVideoPlayer.update(deltaSeconds);
    }
}

bool GameplayUiRuntime::renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const
{
    if (!m_houseVideoPlayerInitialized || !m_houseVideoPlayer.hasActiveFrame())
    {
        return false;
    }

    submitHudTexturedQuad(m_houseVideoPlayer.textureHandle(), x, y, quadWidth, quadHeight);
    return true;
}

void GameplayUiRuntime::clearPortraitRuntime()
{
    m_portraitRuntimeLoaded = false;
    m_portraitFxStates.clear();
    m_portraitPresentationState = {};
}

void GameplayUiRuntime::clearHudResources()
{
    for (bgfx::UniformHandle &uniform : m_previewUniforms)
    {
        if (canUseBgfxResources() && bgfx::isValid(uniform))
        {
            bgfx::destroy(uniform);
        }
        uniform = BGFX_INVALID_HANDLE;
    }
    if (!canUseBgfxResources())
    {
        for (GameplayHudTextureData &textureHandle : m_hudTextureHandles)
        {
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }

        for (GameplayHudFontData &fontHandle : m_hudFontHandles)
        {
            fontHandle.mainTextureHandle = BGFX_INVALID_HANDLE;
            fontHandle.shadowTextureHandle = BGFX_INVALID_HANDLE;
            fontHandle.tintTextureHandle = BGFX_INVALID_HANDLE;
        }

        for (GameplayHudTextureColorTextureData &textureHandle : m_hudTextureColorTextureHandles)
        {
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }

        m_hudTextureHandles.clear();
    m_hudTextureUvScales.clear();
        m_hudTextureIndexByName.clear();
        m_dynamicHudTextureContentSignatures.clear();
        m_hudFontHandles.clear();
            m_hudTextureColorTextureHandles.clear();
        m_hudPaletteTextureHandle = BGFX_INVALID_HANDLE;
        m_hudPaletteSlotByColor.clear();
        return;
    }

    for (GameplayHudTextureData &textureHandle : m_hudTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    // The font textures belong to SharedFontCache; m_hudFontHandles only views them.

    for (GameplayHudTextureColorTextureData &textureHandle : m_hudTextureColorTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    if (bgfx::isValid(m_hudPaletteTextureHandle))
    {
        bgfx::destroy(m_hudPaletteTextureHandle);
        m_hudPaletteTextureHandle = BGFX_INVALID_HANDLE;
    }

    m_hudTextureHandles.clear();
    m_hudTextureUvScales.clear();
    m_hudTextureIndexByName.clear();
    m_dynamicHudTextureContentSignatures.clear();
    m_hudFontHandles.clear();
    m_hudTextureColorTextureHandles.clear();
    m_hudPaletteSlotByColor.clear();
}
}

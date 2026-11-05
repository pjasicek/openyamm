#pragma once

#include "engine/render/LightGrid.h"
#include "game/indoor/IndoorLightReach.h"
#include "game/indoor/IndoorPortalVisibility.h"
#include "game/render/lighting/FxLightClustering.h"
#include "game/render/lighting/LightingStats.h"

#include <bx/math.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
class WorldFxSystem;
struct DecorationBillboardSet;
struct EventRuntimeState;
struct IndoorMapData;

static constexpr size_t MaxIndoorDrawLights = 12;

// The sectors a light reaches (IndoorLightReach), as the light grid carries them; count 0: everywhere (no sector, or
// more sectors than fit).
struct IndoorLightReachList
{
    std::array<int16_t, Engine::LightGridMaxReach> sectors = {};
    uint8_t count = 0;

    void assign(const std::vector<int16_t> &reached);
    bool reaches(int16_t sector) const;
    // A face or batch with front and back sectors (-1: none); one without either takes every light.
    bool reachesReceiver(int16_t sector, int16_t backSector) const;
};

enum class IndoorRenderLightKind : uint8_t
{
    Static,
    Decoration,
    Torch,
    Fx,
};

struct IndoorRenderLight
{
    bx::Vec3 position = {0.0f, 0.0f, 0.0f};
    float radius = 0.0f;
    uint32_t colorAbgr = 0xffffffffu;
    float intensity = 1.0f;
    int16_t sectorId = -1;
    IndoorRenderLightKind kind = IndoorRenderLightKind::Static;
    uint32_t stableId = 0;
    IndoorLightReachList reach;
};

enum class IndoorLightingSampleFilter : uint8_t
{
    All,
    StaticDetailOnly,
    DynamicOnly,
};

struct IndoorLightingFrame
{
    // The darkest visible sector's ambient (lights without a sector, the frame default) and every sector's own.
    float ambient = 1.0f;
    std::vector<float> sectorAmbient;
    uint64_t indoorLightRevision = 0;
    bool coloredLights = true;
    std::vector<IndoorRenderLight> lights;
    std::vector<std::vector<uint32_t>> lightIndicesBySector;
    std::vector<std::vector<uint32_t>> dynamicLightIndicesBySector;
    std::vector<uint32_t> globalLightIndices;
    std::vector<uint32_t> fxLightIndices;
    uint32_t sourceFxLightCount = 0;
    uint32_t clusteredFxLightCount = 0;
};

struct IndoorDrawLightSet
{
    std::array<float, MaxIndoorDrawLights * 4> positions = {};
    std::array<float, MaxIndoorDrawLights * 4> colors = {};
    std::array<float, 4> params = {};
    std::array<uint32_t, MaxIndoorDrawLights> stableIds = {};
    size_t lightCount = 0;
};

struct IndoorLightSelectionBounds
{
    bx::Vec3 min = {0.0f, 0.0f, 0.0f};
    bx::Vec3 max = {0.0f, 0.0f, 0.0f};
    bool valid = false;
};

struct IndoorLightingFrameInput
{
    const IndoorMapData *pMapData = nullptr;
    const EventRuntimeState *pEventRuntimeState = nullptr;
    const DecorationBillboardSet *pDecorationBillboardSet = nullptr;
    const WorldFxSystem *pWorldFxSystem = nullptr;
    const Party *pParty = nullptr;
    const std::vector<uint8_t> *pVisibleSectorMask = nullptr;
    const std::vector<std::vector<IndoorVisibilityFrustum>> *pVisibleSectorFrustums = nullptr;
    bx::Vec3 cameraPosition = {0.0f, 0.0f, 0.0f};
    bool coloredLights = true;
    bool warmTorchLight = false;
    // FX lights per sector before nearby ones merge (FxLightClusterThresholdHigh/Low, by the light grid's quality).
    uint32_t fxClusterThreshold = FxLightClusterThresholdHigh;
    // Scene model_lighting (MM9 lights its models without occlusion): a static light joins the frame when its sphere
    // reaches any visible room's view, not only through the rooms it reaches.
    bool lightsIgnoreReach = false;
    // The renderer's clock: the scene pulsing lights' phase.
    float timeSeconds = 0.0f;
};

class IndoorLightingRuntime
{
public:
    void rebuildStaticCache(
        const IndoorMapData &mapData,
        const DecorationBillboardSet *pDecorationBillboardSet,
        const EventRuntimeState *pState = nullptr);
    void clearStaticCache();
    IndoorLightingFrame buildFrame(const IndoorLightingFrameInput &input) const;

    static bool isBlvLightEnabledByState(uint32_t attributes, const EventRuntimeState *pState, size_t lightId);
    static float ambientFromMinAmbientLightLevel(int minAmbientLightLevel);
    // A sector's ambient level (0-31): an event's evt.SetSectorAmbient, else the map's minAmbientLightLevel.
    static int sectorAmbientLevel(const IndoorMapData &mapData, const EventRuntimeState *pState, size_t sectorId);
    // The sector's own ambient; the frame's for no sector.
    static float sectorAmbient(const IndoorLightingFrame &frame, int16_t sectorId);
    const IndoorLightReach &lightReach() const
    {
        return m_lightReach;
    }
    // A map light's own sector (where it stands, else the first sector listing it); -1 when unknown.
    int16_t mapLightSector(size_t lightId) const
    {
        return lightId < m_mapLightSectors.size() ? m_mapLightSectors[lightId] : int16_t(-1);
    }
    // The strength a map light's colour carries in the frame (its alpha and the renderer's light scale): the scene
    // model_lighting divides it out to light models at the BLV light's own colour.
    static float mapLightStrength();
    // MM9's model light at a point without N.L (scene model_lighting, for sprites): every light of the frame (MM9 has
    // no occlusion), its colour at map-light strength x lightScale x (1 - d^2/r^2); without the room ambient,
    // unclamped.
    static std::array<float, 3> sampleModelLightRgb(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &position,
        float lightScale);
    static std::array<float, 3> sampleLightingRgb(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &position,
        LightingStats *pStats = nullptr,
        IndoorLightingSampleFilter filter = IndoorLightingSampleFilter::All);
    static std::array<float, 3> sampleLightingRgbForSectors(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &position,
        int16_t sectorId,
        int16_t backSectorId = -1,
        LightingStats *pStats = nullptr,
        IndoorLightingSampleFilter filter = IndoorLightingSampleFilter::All);
    static IndoorDrawLightSet selectDrawLightSetForPoint(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &position,
        const bx::Vec3 &viewForward,
        LightingStats *pStats = nullptr,
        bool includeStaticLights = true);
    static IndoorDrawLightSet selectDrawLightSetForSectors(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &referencePosition,
        const bx::Vec3 &viewForward,
        int16_t sectorId,
        int16_t backSectorId,
        LightingStats *pStats = nullptr,
        bool includeStaticLights = true);
    // Every light of the frame (static, decoration, torch, FX) for the clustered light grid, coloured and scaled as
    // the per-draw light sets pack them; torch and FX lights are its dynamic ones, with their sectors.
    static std::vector<Engine::LightGridLight> gridLights(const IndoorLightingFrame &frame);
    static IndoorDrawLightSet selectDrawLightSetForBounds(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &referencePosition,
        const bx::Vec3 &viewForward,
        int16_t sectorId,
        int16_t backSectorId,
        const IndoorLightSelectionBounds &bounds,
        LightingStats *pStats = nullptr,
        bool includeStaticLights = true);

private:
    struct CachedLightSource
    {
        bx::Vec3 position = {0.0f, 0.0f, 0.0f};
        float radius = 0.0f;
        uint8_t red = 255;
        uint8_t green = 255;
        uint8_t blue = 255;
        uint8_t alpha = 255;
        float intensity = 1.0f;
        int16_t sectorId = -1;
        IndoorRenderLightKind kind = IndoorRenderLightKind::Static;
        uint32_t sourceAttributes = 0;
        uint32_t runtimeOverrideKey = 0;
        size_t sourceLightId = static_cast<size_t>(-1);
        size_t decorationDecorVarIndex = static_cast<size_t>(-1);
        uint8_t decorationClearedState = 0;
        bool hideDecorationWhenCleared = false;
        IndoorLightReachList reach;
    };

    struct StaticLightCache
    {
        std::vector<CachedLightSource> sources;
        std::vector<std::vector<uint32_t>> sourceIndicesBySector;
        uint64_t lightRevision = 0;
        bool valid = false;
    };

    static StaticLightCache buildStaticCache(
        const IndoorMapData &mapData,
        const DecorationBillboardSet *pDecorationBillboardSet,
        const EventRuntimeState *pState,
        const std::vector<int16_t> &mapLightSectors);
    static uint32_t lightColorAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha, bool coloredLights);

    // Gives every cached source its reach.
    void assignReach(StaticLightCache &cache) const;

    mutable StaticLightCache m_staticLightCache;
    IndoorLightReach m_lightReach;
    std::vector<int16_t> m_mapLightSectors;
    // Each scene pulsing light's sector (where it stands; -1 outside every sector).
    std::vector<int16_t> m_pulsingLightSectors;
};
}

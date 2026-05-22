#pragma once

#include "game/indoor/IndoorPortalVisibility.h"
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
};

struct IndoorLightingFrame
{
    float ambient = 1.0f;
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

struct IndoorLightSelectionHistory
{
    std::array<uint32_t, MaxIndoorDrawLights> lightStableIds = {};
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
    bx::Vec3 torchPosition = {0.0f, 0.0f, 0.0f};
    bool hasTorchPosition = false;
    bool coloredLights = true;
};

class IndoorLightingRuntime
{
public:
    void rebuildStaticCache(
        const IndoorMapData &mapData,
        const DecorationBillboardSet *pDecorationBillboardSet);
    void clearStaticCache();
    IndoorLightingFrame buildFrame(const IndoorLightingFrameInput &input) const;

    static bool isBlvLightEnabledByState(uint32_t attributes, const EventRuntimeState *pState, size_t lightId);
    static float ambientFromMinAmbientLightLevel(int minAmbientLightLevel);
    static std::array<float, 3> sampleLightingRgb(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &position,
        LightingStats *pStats = nullptr);
    static std::array<float, 3> sampleLightingRgbForSectors(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &position,
        int16_t sectorId,
        int16_t backSectorId = -1,
        LightingStats *pStats = nullptr);
    static IndoorDrawLightSet selectDrawLightSetForPoint(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &position,
        const bx::Vec3 &viewForward,
        LightingStats *pStats = nullptr);
    static IndoorDrawLightSet selectDrawLightSetForSectors(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &referencePosition,
        const bx::Vec3 &viewForward,
        int16_t sectorId,
        int16_t backSectorId,
        LightingStats *pStats = nullptr,
        const IndoorLightSelectionHistory *pPreviousSelection = nullptr);
    static IndoorDrawLightSet selectDrawLightSetForBounds(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &referencePosition,
        const bx::Vec3 &viewForward,
        int16_t sectorId,
        int16_t backSectorId,
        const IndoorLightSelectionBounds &bounds,
        LightingStats *pStats = nullptr,
        const IndoorLightSelectionHistory *pPreviousSelection = nullptr);

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
    };

    struct StaticLightCache
    {
        std::vector<CachedLightSource> sources;
        std::vector<std::vector<uint32_t>> sourceIndicesBySector;
        bool valid = false;
    };

    static StaticLightCache buildStaticCache(
        const IndoorMapData &mapData,
        const DecorationBillboardSet *pDecorationBillboardSet);
    static uint32_t lightColorAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha, bool coloredLights);

    StaticLightCache m_staticLightCache;
};
}

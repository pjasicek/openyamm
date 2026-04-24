#pragma once

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

static constexpr size_t MaxIndoorRenderLights = 40;

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
    IndoorRenderLightKind kind = IndoorRenderLightKind::Static;
};

struct IndoorLightingFrame
{
    float ambient = 1.0f;
    std::vector<IndoorRenderLight> lights;
};

struct IndoorLightingFrameInput
{
    const IndoorMapData *pMapData = nullptr;
    const EventRuntimeState *pEventRuntimeState = nullptr;
    const DecorationBillboardSet *pDecorationBillboardSet = nullptr;
    const WorldFxSystem *pWorldFxSystem = nullptr;
    const Party *pParty = nullptr;
    const std::vector<uint8_t> *pVisibleSectorMask = nullptr;
    bx::Vec3 cameraPosition = {0.0f, 0.0f, 0.0f};
    bool coloredLights = true;
};

class IndoorLightingRuntime
{
public:
    IndoorLightingFrame buildFrame(const IndoorLightingFrameInput &input) const;

    static bool isBlvLightEnabledByState(uint32_t attributes, const EventRuntimeState *pState, size_t lightId);
    static float ambientFromMinAmbientLightLevel(int minAmbientLightLevel);
    static std::array<float, 3> sampleLightingRgb(
        const IndoorLightingFrame &frame,
        const bx::Vec3 &position);

private:
    static uint32_t lightColorAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha, bool coloredLights);
};
}

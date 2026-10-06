#pragma once

#include "game/render/WaterMath.h"
#include "game/fx/WaterRippleRuntime.h"
#include "game/render/WaterReflectionUpdate.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <array>
#include <map>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class ViewFrustum;
struct IndoorLightingFrame;
struct BillboardQuad;

struct WaterVertex
{
    float x, y, z;
    float normalX, normalY, normalZ;
    float u, v;
    float layer;
    float shoreline;
    uint32_t colorAbgr;
};

struct WaterSurfaceGeometry
{
    std::vector<WaterVertex> vertices;
    // Bounds of individual patches prevent a whole-map ocean bounding box from defeating culling.
    std::vector<std::array<bx::Vec3, 2>> patches;
    float height = 0.0f;
    bool planar = true;
    int16_t sectorId = -1;
    int16_t backSectorId = -1;
};

class WaterRenderer
{
public:
    struct Reflection
    {
        bgfx::FrameBufferHandle frameBuffer = BGFX_INVALID_HANDLE;
        bgfx::TextureHandle texture = BGFX_INVALID_HANDLE;
        std::array<float, 16> view = {};
        std::array<float, 16> projection = {};
        std::array<float, 16> sourceProjection = {};
        std::array<float, 16> viewProjection = {};
        bx::Vec3 camera = {0.0f, 0.0f, 0.0f};
        float height = 0.0f;
        float projectionScale = 1.0f;
        uint16_t skyView = FirstWaterReflectionView;
        uint16_t worldView = FirstWaterReflectionView + 1;
        bool update = true;
        int16_t sectorId = -1;
        uint16_t size = 0;
    };

    bool initialize(const Engine::AssetFileSystem &assets, std::vector<WaterSurfaceGeometry> geometry,
        std::span<const std::vector<uint8_t>> coverageMasks = {}, bool indoor = false);
    bool updateGeometry(std::vector<WaterSurfaceGeometry> geometry, bool buildings = false);
    void shutdown();
    bool isReady() const;
    void prepare(const ViewFrustum &frustum, const bx::Vec3 &camera, const float *pView, const float *pProjection,
        bool reflections, uint16_t size, float seconds, uint64_t visualRevision, bool buildings,
        std::span<const uint8_t> visibleSectors = {}, int16_t reflectionSectorId = -1, bool billboards = false);
    std::span<const Reflection> reflections() const;
    void bindCoverage(uint8_t stage) const;
    void render(uint16_t viewId, float seconds,
        const std::array<float, 4> &sunDirection, const std::array<float, 4> &sunColor,
        const std::array<float, 4> &skyColor, float rainIntensity, const WaterRippleRuntime *pRipples = nullptr,
        const Reflection *pReflection = nullptr);
    void renderIndoor(uint16_t viewId, float seconds, const IndoorLightingFrame &lighting,
        const bx::Vec3 &camera, const bx::Vec3 &forward, const WaterRippleRuntime *pRipples = nullptr,
        const Reflection *pReflection = nullptr, std::span<const uint8_t> visibleSectors = {});
    void renderBillboard(uint16_t viewId, std::span<const WaterVertex> vertices,
        bgfx::TextureHandle sprite, float seconds,
        const std::array<float, 4> &sunDirection, const std::array<float, 4> &sunColor,
        const std::array<float, 4> &skyColor, float rainIntensity);
    void appendBillboardGeometry(std::vector<WaterVertex> &vertices, const std::string &textureName,
        const BillboardQuad &quad, bool mirrored) const;

private:
    struct Surface
    {
        bgfx::VertexBufferHandle buffer = BGFX_INVALID_HANDLE;
        std::vector<std::array<bx::Vec3, 2>> patches;
        uint32_t vertexCount = 0;
        float height = 0.0f;
        float distanceSquared = 0.0f;
        bool planar = true;
        bool visible = false;
        bool building = false;
        int reflection = -1;
        int16_t sectorId = -1;
        int16_t backSectorId = -1;
    };

    bool resizeReflection(size_t index, uint16_t size);
    void prepareRippleResources(const WaterRippleRuntime *pRipples);
    void submitSurface(const Surface &surface, uint16_t viewId, float seconds, float rainIntensity,
        const WaterRippleRuntime *pRipples);
    std::vector<Surface> m_surfaces;
    std::array<Reflection, MaxWaterReflections> m_reflections;
    std::array<uint16_t, MaxWaterReflections> m_reflectionSizes = {};
    std::array<WaterReflectionUpdate, MaxWaterReflections> m_reflectionUpdates;
    size_t m_reflectionCount = 0;
    bgfx::ProgramHandle m_program = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_rippleProgram = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_rippleRings = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_rippleParams = BGFX_INVALID_HANDLE;
    bx::Vec3 m_camera = {0.0f, 0.0f, 0.0f};
    bgfx::TextureHandle m_normalTexture = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_emptyReflection = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_coverageTexture = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_coverageSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_normalSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_spriteSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_reflectionSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_params = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_sunDirection = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_sunColor = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_skyColor = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_reflectionMatrix = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_cameraPosition = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_indoorLightPositions = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_indoorLightColors = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_indoorLightParams = BGFX_INVALID_HANDLE;
    bool m_indoor = false;
    std::map<std::string, std::vector<std::vector<std::array<float, 3>>>> m_spriteWaterStrips;
};
}

#pragma once

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace OpenYAMM::Game
{
// Every bgfx view id the game uses outside 0 (sky or indoor world), 1 (outdoor world) and 2 (HUD) is declared here,
// so a new view cannot silently share an id: the check below fails the build on a duplicate. A shared id merges
// two passes (the pause menu drawn into the bloom target, 2026-10-16).
// The indoor portal view's per-pass GPU timing (`portals gpu`, IndoorDebugPass): decorations, actors, open sky and
// translucent, each in its own view right after the world view 0; unused (no draws) otherwise.
constexpr uint16_t FirstIndoorDebugPassView = 220;
constexpr size_t IndoorDebugPassViews = 4;
// Bloom (lighting plan, phase 7): emitters drawn again into a glow target, then reduced and blurred.
constexpr uint16_t WorldGlowView = 227;
constexpr uint16_t BloomDownsampleView = 228;
constexpr uint16_t BloomBlurHorizontalView = 229;
constexpr uint16_t BloomBlurVerticalView = 230;
// One per sun shadow cascade (ModelSunShadowCascades).
constexpr uint16_t FirstSunShadowView = 231;
constexpr size_t SunShadowViews = 3;
constexpr uint16_t FirstWaterReflectionView = 234;
constexpr size_t MaxWaterReflections = 2;
// Reduced-resolution Enhanced sky, rendered before the main sky view upscales it.
constexpr uint16_t SkyImageView = 238;
// Offscreen actor inspect portrait (ActorModelPreview), rendered before the HUD view that draws it.
constexpr uint16_t ActorPortraitView = 239;
// The second actor portrait: a speaking MM9 actor's head and shoulders (ActorModelPreview, ActorPortraitKind::Talk).
constexpr uint16_t ActorTalkPortraitView = 243;
// MenuDesignScreen menus (pause, settings, save and load), drawn after the world and the HUD.
constexpr uint16_t MenuDesignView = 240;
// Screen-space reflections of surface materials: the finished world's colour and positions at half resolution, which
// the next frame's smooth faces trace (CinematicGrading, devdocs/SURFACE_MATERIALS_PLAN.md).
constexpr uint16_t ReflectionHistoryColorView = 241;
constexpr uint16_t ReflectionHistoryPositionView = 242;
constexpr uint16_t AmbientOcclusionDepthView = 244;
constexpr uint16_t AmbientOcclusionView = 245;
constexpr uint16_t AmbientOcclusionBlurView = 246;
constexpr uint16_t AmbientOcclusionCompositeView = 247;
constexpr uint16_t WorldTransparentView = 248;
constexpr uint16_t WorldGradingView = 249;
// The debug ImGui overlay, the loading screen's completion readback and the loading screen itself.
constexpr uint16_t DebugImGuiView = 250;
constexpr uint16_t LoadingReadbackView = 253;
constexpr uint16_t LoadingOverlayView = 254;

constexpr bool uniqueGameViewIds()
{
    std::array<uint16_t, 32> views = {};
    size_t count = 0;
    for (uint16_t view = WorldGlowView; view <= BloomBlurVerticalView; ++view)
    {
        views[count++] = view;
    }
    for (uint16_t view = FirstSunShadowView; view < FirstSunShadowView + SunShadowViews; ++view)
    {
        views[count++] = view;
    }
    for (uint16_t view = FirstWaterReflectionView; view < FirstWaterReflectionView + MaxWaterReflections * 2; ++view)
    {
        views[count++] = view;
    }
    for (uint16_t view = FirstIndoorDebugPassView; view < FirstIndoorDebugPassView + IndoorDebugPassViews; ++view)
    {
        views[count++] = view;
    }
    for (uint16_t view : {SkyImageView, ActorPortraitView, ActorTalkPortraitView, MenuDesignView,
             ReflectionHistoryColorView, ReflectionHistoryPositionView, AmbientOcclusionDepthView,
             AmbientOcclusionView, AmbientOcclusionBlurView, AmbientOcclusionCompositeView, WorldTransparentView,
             WorldGradingView, DebugImGuiView, LoadingReadbackView, LoadingOverlayView})
    {
        views[count++] = view;
    }
    for (size_t first = 0; first < count; ++first)
    {
        if (views[first] <= 2)
        {
            return false;
        }
        for (size_t second = first + 1; second < count; ++second)
        {
            if (views[first] == views[second])
            {
                return false;
            }
        }
    }
    return true;
}
static_assert(uniqueGameViewIds(), "Two game passes share a bgfx view id");

// Matches the maximum normalized UV offset passed to waterReflection by both water shaders.
constexpr float WaterReflectionDistortion = 0.014f;
constexpr float IndoorWaterReflectionGuardBand = 1.125f;

inline uint16_t waterReflectionCaptureSize(uint16_t size, uint16_t maxTextureSize)
{
    // Use available headroom for the guard band; retain the requested detail at the device limit.
    return std::max(size, std::min(uint16_t(size * IndoorWaterReflectionGuardBand), maxTextureSize));
}

// Widen a right-handed perspective capture without reducing its pixel density.
// Extend depth as well: rotation can move points across the original near/far planes.
inline void waterReflectionCaptureProjection(float *pResult, const float *pProjection, float scale,
    bool homogeneousDepth)
{
    std::copy_n(pProjection, 16, pResult);
    const float nearClip = pProjection[14] / (pProjection[10] - (homogeneousDepth ? 1.0f : 0.0f)) / scale;
    const float farClip = pProjection[14] / (pProjection[10] + 1.0f) * scale;
    pResult[0] /= scale;
    pResult[5] /= scale;
    pResult[10] = -(homogeneousDepth ? farClip + nearClip : farClip) / (farClip - nearClip);
    pResult[14] = -(homogeneousDepth ? 2.0f : 1.0f) * nearClip * farClip / (farClip - nearClip);
}

// With an unchanged eye, perspective reprojection is exact. Require the entire
// current frustum, including distorted/bilinear samples, to fit inside the capture.
inline bool waterReflectionViewCovered(const float *pCapturedView, const float *pCapturedProjection,
    const float *pView, const float *pProjection, uint16_t size, bool homogeneousDepth)
{
    // Compare camera-relative rotations rather than inverting a world-space matrix:
    // large map coordinates otherwise lose precision at the distant frustum corners.
    float inverseView[16];
    float capturedView[16];
    float rotation[16];
    float inverseProjection[16];
    float viewReproject[16];
    float reproject[16];
    bx::mtxTranspose(inverseView, pView);
    inverseView[3] = inverseView[7] = inverseView[11] = 0.0f;
    std::copy_n(pCapturedView, 16, capturedView);
    capturedView[12] = capturedView[13] = capturedView[14] = 0.0f;
    bx::mtxMul(rotation, inverseView, capturedView);
    bx::mtxInverse(inverseProjection, pProjection);
    bx::mtxMul(viewReproject, inverseProjection, rotation);
    bx::mtxMul(reproject, viewReproject, pCapturedProjection);
    const float limit = 1.0f - 2.0f * WaterReflectionDistortion - 4.0f / size;
    for (float depth : {homogeneousDepth ? -1.0f : 0.0f, 1.0f})
    {
        for (float x : {-1.0f, 1.0f})
        {
            for (float y : {-1.0f, 1.0f})
            {
                const float corner[] = {x, y, depth, 1.0f};
                float clip[4];
                bx::vec4MulMtx(clip, corner, reproject);
                const float nearDepth = homogeneousDepth ? -clip[3] : 0.0f;
                if (!(clip[3] > 0.0f && std::abs(clip[0]) <= limit * clip[3]
                    && std::abs(clip[1]) <= limit * clip[3] && clip[2] >= nearDepth && clip[2] <= clip[3]))
                {
                    return false;
                }
            }
        }
    }
    return true;
}

struct WaterReflectionScissor
{
    uint16_t x = 0;
    uint16_t y = 0;
    uint16_t width = 0;
    uint16_t height = 0;
};

inline WaterReflectionScissor waterReflectionScissor(const float *pViewProjection,
    const bx::Vec3 &reflectedCamera, uint16_t size)
{
    float inverse[16];
    bx::mtxInverse(inverse, pViewProjection);
    constexpr std::array<std::array<float, 2>, 4> corners = {{{-1.0f, -1.0f}, {1.0f, -1.0f},
        {1.0f, 1.0f}, {-1.0f, 1.0f}}};
    std::array<float, 4> rayHeights;
    for (size_t index = 0; index < corners.size(); ++index)
    {
        const float clip[] = {corners[index][0], corners[index][1], 1.0f, 1.0f};
        float world[4];
        bx::vec4MulMtx(world, clip, inverse);
        rayHeights[index] = world[2] - reflectedCamera.z * world[3];
    }
    float minX = 1.0f;
    float minY = 1.0f;
    float maxX = -1.0f;
    float maxY = -1.0f;
    const auto include = [&](float x, float y)
    {
        minX = std::min(minX, x);
        minY = std::min(minY, y);
        maxX = std::max(maxX, x);
        maxY = std::max(maxY, y);
    };
    // The reflected camera is below the surface: only ascending rays can reach water.
    // Clip the screen rectangle against that horizon before taking its pixel bounds.
    for (size_t index = 0; index < corners.size(); ++index)
    {
        const size_t next = (index + 1) % corners.size();
        if (rayHeights[index] >= 0.0f)
        {
            include(corners[index][0], corners[index][1]);
        }
        if ((rayHeights[index] >= 0.0f) != (rayHeights[next] >= 0.0f))
        {
            const float t = rayHeights[index] / (rayHeights[index] - rayHeights[next]);
            include(corners[index][0] + t * (corners[next][0] - corners[index][0]),
                corners[index][1] + t * (corners[next][1] - corners[index][1]));
        }
    }
    if (minX > maxX || minY > maxY)
    {
        return {};
    }
    const int margin = int(std::ceil(size * WaterReflectionDistortion)) + 2;
    const int left = std::clamp(int(std::floor((minX + 1.0f) * 0.5f * size)) - margin, 0, int(size));
    const int top = std::clamp(int(std::floor((1.0f - maxY) * 0.5f * size)) - margin, 0, int(size));
    const int right = std::clamp(int(std::ceil((maxX + 1.0f) * 0.5f * size)) + margin, 0, int(size));
    const int bottom = std::clamp(int(std::ceil((1.0f - minY) * 0.5f * size)) + margin, 0, int(size));
    return {uint16_t(left), uint16_t(top), uint16_t(right - left), uint16_t(bottom - top)};
}

constexpr std::array<uint16_t, WorldGradingView + 1> worldRenderViewOrder(bool grading, bool ambientOcclusion = false,
    bool bloom = false, bool reflections = false)
{
    std::array<uint16_t, WorldGradingView + 1> order = {};
    size_t index = 0;
    for (uint16_t view = FirstSunShadowView; view < FirstSunShadowView + SunShadowViews; ++view)
    {
        order[index++] = view;
    }
    for (uint16_t view = FirstWaterReflectionView; view < FirstWaterReflectionView + MaxWaterReflections * 2; ++view)
    {
        order[index++] = view;
    }
    order[index++] = SkyImageView;
    order[index++] = ActorPortraitView;
    order[index++] = ActorTalkPortraitView;
    order[index++] = 0;
    for (uint16_t view = FirstIndoorDebugPassView; view < FirstIndoorDebugPassView + IndoorDebugPassViews; ++view)
    {
        order[index++] = view;
    }
    order[index++] = 1;
    if (ambientOcclusion)
    {
        for (uint16_t view = AmbientOcclusionDepthView; view <= WorldTransparentView; ++view)
        {
            order[index++] = view;
        }
    }
    if (bloom)
    {
        for (uint16_t view = WorldGlowView; view <= BloomBlurVerticalView; ++view)
        {
            order[index++] = view;
        }
    }
    // Before the presentation: the backbuffer stays the last bound target (bgfx's OpenGL screenshots read it).
    if (reflections)
    {
        order[index++] = ReflectionHistoryColorView;
        order[index++] = ReflectionHistoryPositionView;
    }
    if (grading)
    {
        order[index++] = WorldGradingView;
    }
    for (uint16_t view = 2; view <= WorldGradingView; ++view)
    {
        if ((view < FirstSunShadowView || view >= FirstSunShadowView + SunShadowViews)
            && (view < FirstWaterReflectionView || view >= FirstWaterReflectionView + MaxWaterReflections * 2)
            && view != SkyImageView
            && view != ActorPortraitView
            && view != ActorTalkPortraitView
            && (view < FirstIndoorDebugPassView || view >= FirstIndoorDebugPassView + IndoorDebugPassViews)
            && (!grading || view != WorldGradingView)
            && (!ambientOcclusion || view < AmbientOcclusionDepthView || view > WorldTransparentView)
            && (!bloom || view < WorldGlowView || view > BloomBlurVerticalView)
            && (!reflections || (view != ReflectionHistoryColorView && view != ReflectionHistoryPositionView)))
        {
            order[index++] = view;
        }
    }
    return order;
}

inline bx::Vec3 reflectWaterPoint(const bx::Vec3 &point, float height)
{
    return {point.x, point.y, 2.0f * height - point.z};
}

inline void waterReflectionView(float *pResult, const float *pView, float height)
{
    float mirror[16];
    bx::mtxIdentity(mirror);
    mirror[10] = -1.0f;
    mirror[14] = 2.0f * height;
    bx::mtxMul(pResult, mirror, pView);
}
}

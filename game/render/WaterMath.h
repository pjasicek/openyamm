#pragma once

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>

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
// The prototype first-person view model (FirstPersonViewModel): drawn into the finished world target with its own
// depth and projection, after every world pass (AO, bloom, reflections) and before the grading.
constexpr uint16_t FirstPersonViewModelView = 251;
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
             WorldGradingView, FirstPersonViewModelView, DebugImGuiView, LoadingReadbackView, LoadingOverlayView})
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

// normal: the reflecting plane's normal toward the real camera (water: up).
inline WaterReflectionScissor waterReflectionScissor(const float *pViewProjection,
    const bx::Vec3 &reflectedCamera, uint16_t size, const bx::Vec3 &normal = {0.0f, 0.0f, 1.0f})
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
        rayHeights[index] = bx::dot(normal, bx::sub(bx::Vec3{world[0], world[1], world[2]},
            bx::mul(reflectedCamera, world[3])));
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
    // The reflected camera is behind the surface: only rays heading toward its front can reach it.
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

// The part of a capture's scissor (above) where a box's faces can sample it: its projected corners plus the distortion
// margin. A box that reaches behind the capture's eye keeps the whole scissor.
inline WaterReflectionScissor waterReflectionBoundsScissor(const float *pViewProjection, const bx::Vec3 &min,
    const bx::Vec3 &max, uint16_t size, const WaterReflectionScissor &scissor)
{
    if (min.x > max.x || min.y > max.y || min.z > max.z)
    {
        return {};
    }
    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float maxX = -std::numeric_limits<float>::max();
    float maxY = -std::numeric_limits<float>::max();
    for (size_t corner = 0; corner < 8; ++corner)
    {
        const float world[] = {(corner & 1) != 0 ? max.x : min.x, (corner & 2) != 0 ? max.y : min.y,
            (corner & 4) != 0 ? max.z : min.z, 1.0f};
        float clip[4];
        bx::vec4MulMtx(clip, world, pViewProjection);
        if (clip[3] <= 0.001f)
        {
            return scissor;
        }
        minX = std::min(minX, clip[0] / clip[3]);
        minY = std::min(minY, clip[1] / clip[3]);
        maxX = std::max(maxX, clip[0] / clip[3]);
        maxY = std::max(maxY, clip[1] / clip[3]);
    }
    const int margin = int(std::ceil(size * WaterReflectionDistortion)) + 2;
    const int left = std::max(int(std::floor((minX + 1.0f) * 0.5f * size)) - margin, int(scissor.x));
    const int top = std::max(int(std::floor((1.0f - maxY) * 0.5f * size)) - margin, int(scissor.y));
    const int right = std::min(int(std::ceil((maxX + 1.0f) * 0.5f * size)) + margin, scissor.x + scissor.width);
    const int bottom = std::min(int(std::ceil((1.0f - minY) * 0.5f * size)) + margin, scissor.y + scissor.height);
    if (right <= left || bottom <= top)
    {
        return {};
    }
    return {uint16_t(left), uint16_t(top), uint16_t(right - left), uint16_t(bottom - top)};
}

constexpr std::array<uint16_t, FirstPersonViewModelView + 1> worldRenderViewOrder(bool grading, bool ambientOcclusion = false,
    bool bloom = false, bool reflections = false)
{
    std::array<uint16_t, FirstPersonViewModelView + 1> order = {};
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
    order[index++] = FirstPersonViewModelView;
    if (grading)
    {
        order[index++] = WorldGradingView;
    }
    for (uint16_t view = 2; view <= FirstPersonViewModelView; ++view)
    {
        if ((view < FirstSunShadowView || view >= FirstSunShadowView + SunShadowViews)
            && (view < FirstWaterReflectionView || view >= FirstWaterReflectionView + MaxWaterReflections * 2)
            && view != SkyImageView
            && view != ActorPortraitView
            && view != ActorTalkPortraitView
            && view != FirstPersonViewModelView
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

// A reflecting plane: unit normal (x, y, z) toward the side that sees it and w = -dot(normal, point on it), so a point
// p is in front where dot(normal, p) + w > 0. It is also the reflection passes' world clip plane.
using ReflectionPlane = std::array<float, 4>;

inline ReflectionPlane waterReflectionPlane(float height)
{
    return {0.0f, 0.0f, 1.0f, -height};
}

inline float reflectionPlaneDistance(const ReflectionPlane &plane, const bx::Vec3 &point)
{
    return plane[0] * point.x + plane[1] * point.y + plane[2] * point.z + plane[3];
}

inline bx::Vec3 reflectPlanePoint(const bx::Vec3 &point, const ReflectionPlane &plane)
{
    const float twice = 2.0f * reflectionPlaneDistance(plane, point);
    return {point.x - twice * plane[0], point.y - twice * plane[1], point.z - twice * plane[2]};
}

inline bx::Vec3 reflectPlaneDirection(const bx::Vec3 &direction, const ReflectionPlane &plane)
{
    const float twice = 2.0f * (plane[0] * direction.x + plane[1] * direction.y + plane[2] * direction.z);
    return {direction.x - twice * plane[0], direction.y - twice * plane[1], direction.z - twice * plane[2]};
}

// Some part of the box lies in front of the plane (its corner farthest along the normal).
inline bool reflectionPlaneBoundsInFront(const ReflectionPlane &plane, const bx::Vec3 &min, const bx::Vec3 &max)
{
    return reflectionPlaneDistance(plane, {plane[0] >= 0.0f ? max.x : min.x, plane[1] >= 0.0f ? max.y : min.y,
        plane[2] >= 0.0f ? max.z : min.z}) >= 0.0f;
}

inline bx::Vec3 reflectWaterPoint(const bx::Vec3 &point, float height)
{
    return reflectPlanePoint(point, waterReflectionPlane(height));
}

// The view of the world mirrored in the plane: world points are reflected first, then seen through pView.
inline void reflectionPlaneView(float *pResult, const float *pView, const ReflectionPlane &plane)
{
    float mirror[16];
    bx::mtxIdentity(mirror);
    for (size_t row = 0; row < 3; ++row)
    {
        for (size_t column = 0; column < 3; ++column)
        {
            mirror[row * 4 + column] -= 2.0f * plane[row] * plane[column];
        }
        mirror[12 + row] = -2.0f * plane[3] * plane[row];
    }
    bx::mtxMul(pResult, mirror, pView);
}

inline void waterReflectionView(float *pResult, const float *pView, float height)
{
    reflectionPlaneView(pResult, pView, waterReflectionPlane(height));
}
}

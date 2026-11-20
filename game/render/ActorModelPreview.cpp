#include "game/render/ActorModelPreview.h"

#include "engine/BgfxContext.h"
#include "engine/render/ModelRenderer.h"
#include "game/fx/ParticleRenderer.h"
#include "game/fx/WorldFxSystem.h"
#include "game/render/RuntimeShader.h"
#include "game/render/WaterMath.h"

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cfloat>
#include <cmath>
#include <iostream>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// A long lens: little perspective, so a creature's near end does not loom over the rest.
constexpr float PortraitFovDegrees = 16.0f;
// Fraction of the square the creature's standing and fidget poses fill; an attacking body may reach out to the edge
// (a swung weapon past it).
constexpr float PortraitRestFill = 0.85f;
constexpr float PortraitAttackFill = 1.0f;
// The portrait faces +X; the camera stands a little to the creature's left and above, for a three-quarter view. A
// speaker's portrait looks at them from the front, a little above eye level.
constexpr float PortraitTurnRadians = 0.45f;
constexpr float PortraitPitchRadians = 0.14f;
constexpr float TalkPortraitTurnRadians = 0.0f;
constexpr float TalkPortraitPitchRadians = 0.06f;
// Fixed magnification over that framing (a narrower lens about the same centre): every portrait grows by exactly this,
// so the attack and a carried weapon may cross the edge.
constexpr float PortraitZoom = 1.15f;
// Target pixels per HUD pixel: the bilinear minification smooths the silhouette.
constexpr float PortraitSupersample = 2.0f;

bx::Vec3 portraitToCamera(ActorPortraitKind kind)
{
    const bool talk = kind == ActorPortraitKind::Talk;
    const float turn = talk ? TalkPortraitTurnRadians : PortraitTurnRadians;
    const float pitch = talk ? TalkPortraitPitchRadians : PortraitPitchRadians;
    return {std::cos(turn) * std::cos(pitch), std::sin(turn) * std::cos(pitch), std::sin(pitch)};
}

// A neutral key light from above the camera's left: the creature's own colours, with its form readable.
Engine::ModelRenderLighting portraitLighting(ActorPortraitKind kind)
{
    const bx::Vec3 toCamera = portraitToCamera(kind);
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    const bx::Vec3 right = bx::normalize(bx::cross(bx::neg(toCamera), worldUp));
    const bx::Vec3 light = bx::normalize(bx::add(bx::add(bx::mul(toCamera, 0.6f), bx::mul(worldUp, 0.7f)),
        bx::mul(right, -0.45f)));
    Engine::ModelRenderLighting lighting;
    lighting.displaySpaceLighting = true;
    lighting.ambient = 0.6f;
    lighting.direct = 0.6f;
    lighting.lightDirection = {light.x, light.y, light.z};
    return lighting;
}
}

ActorModelPreview::ActorModelPreview(ActorPortraitKind kind)
    : m_kind(kind)
    , m_viewId(kind == ActorPortraitKind::Talk ? ActorTalkPortraitView : ActorPortraitView)
{
}

void ActorModelPreview::bindScene(WorldFxSystem *pWorldFx, Engine::ModelRenderer *pModelRenderer,
    DecorationModelLookup decorationModels)
{
    m_pWorldFx = pWorldFx;
    m_pModelRenderer = pModelRenderer;
    m_decorationModels = std::move(decorationModels);
}

bgfx::TextureHandle ActorModelPreview::render(const IGameplayWorldRuntime &world, size_t actorIndex, float pixelSize,
    uint32_t animationTicks, const Engine::AssetFileSystem &assets)
{
    if (m_pWorldFx == nullptr || m_pModelRenderer == nullptr || m_failed || pixelSize <= 0.0f
        || bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return BGFX_INVALID_HANDLE;
    }
    const WorldFxSystem::InspectPortrait *pPortrait =
        m_pWorldFx->syncInspectPortrait(world, actorIndex, animationTicks, m_kind);
    if (pPortrait == nullptr)
    {
        return BGFX_INVALID_HANDLE;
    }
    return draw(pPortrait->handle, pPortrait->framePoints, pPortrait->restPointCount,
        pPortrait->effects ? &*pPortrait->effects : nullptr, pixelSize, assets);
}

bgfx::TextureHandle ActorModelPreview::renderDecoration(uint32_t decorationKey, float pixelSize,
    const Engine::AssetFileSystem &assets)
{
    if (m_pWorldFx == nullptr || m_pModelRenderer == nullptr || m_failed || pixelSize <= 0.0f
        || m_kind != ActorPortraitKind::Talk || !m_decorationModels
        || bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return BGFX_INVALID_HANDLE;
    }
    const std::optional<DecorationPortraitModel> model = m_decorationModels(decorationKey);
    const WorldFxSystem::InspectPortrait *pPortrait =
        model ? m_pWorldFx->syncDecorationTalkPortrait(decorationKey, *model) : nullptr;
    if (pPortrait == nullptr)
    {
        return BGFX_INVALID_HANDLE;
    }
    return draw(pPortrait->handle, pPortrait->framePoints, pPortrait->restPointCount, nullptr, pixelSize, assets);
}

bgfx::TextureHandle ActorModelPreview::draw(Engine::ModelInstanceHandle handle,
    const std::vector<std::array<float, 3>> &framePoints, size_t restPointCount, const EffectSystem *pEffects,
    float pixelSize, const Engine::AssetFileSystem &assets)
{
    if (framePoints.empty())
    {
        return BGFX_INVALID_HANDLE;
    }
    const uint32_t maxSize = std::min<uint32_t>(1024, bgfx::getCaps()->limits.maxTextureSize);
    const uint32_t wanted = (uint32_t(std::ceil(pixelSize * PortraitSupersample)) + 63u) / 64u * 64u;
    if (!ensureTarget(uint16_t(std::clamp<uint32_t>(wanted, 64u, maxSize))))
    {
        return BGFX_INVALID_HANDLE;
    }

    if (handle != m_framedHandle)
    {
        frame(framePoints, restPointCount);
        m_framedHandle = handle;
    }
    bgfx::setViewName(m_viewId, m_kind == ActorPortraitKind::Talk ? "Actor talk portrait" : "Actor portrait");
    bgfx::setViewFrameBuffer(m_viewId, m_frameBuffer);
    bgfx::setViewRect(m_viewId, 0, 0, m_size, m_size);
    bgfx::setViewClear(m_viewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x00000000u, 1.0f, 0);
    bgfx::setViewMode(m_viewId, bgfx::ViewMode::Sequential);
    bgfx::setViewTransform(m_viewId, m_view.data(), m_projection.data());
    bgfx::touch(m_viewId);

    // A view drawn before the world's may inherit its water reflection clip plane: the portrait clips nothing.
    const float noClip[4] = {};
    bgfx::setUniform(m_worldClipPlaneUniform, noClip);
    m_pModelRenderer->renderPortrait(m_pWorldFx->models(), handle, m_viewId, m_eye, portraitLighting(m_kind));
    if (pEffects != nullptr)
    {
        if (!bgfx::isValid(m_effectResources.particleParamsUniformHandle()))
        {
            m_effectResources.setParticleProgramHandle(loadRuntimeProgram("vs_particle", "fs_particle"));
            ParticleRenderer::initializeResources(m_effectResources);
        }
        m_effectRenderer.render(m_effectResources, *pEffects, m_pWorldFx->namedEffectResources(), assets,
            m_viewId, m_view.data(), {m_eye[0], m_eye[1], m_eye[2]});
    }
    return m_colorTexture;
}

void ActorModelPreview::frame(const std::vector<std::array<float, 3>> &points, size_t restPointCount)
{
    const bx::Vec3 toCamera = portraitToCamera(m_kind);
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    const bx::Vec3 right = bx::normalize(bx::cross(bx::neg(toCamera), worldUp));
    const bx::Vec3 up = bx::cross(right, bx::neg(toCamera));
    // A talk portrait's frame already holds its margins (headAndShouldersFrame): it fills the square.
    const float restFill = m_kind == ActorPortraitKind::Talk ? 1.0f : PortraitRestFill;
    const float zoom = m_kind == ActorPortraitKind::Talk ? 1.0f : PortraitZoom;
    // Centre the standing and fidget poses on screen, then take the nearest camera distance that keeps each framed
    // point inside its share of the field of view at its own depth. A near end looms larger than a far one (a long
    // creature seen from an angle), so the centre is refined on the projected outline.
    const size_t restCount = restPointCount > 0 ? restPointCount : points.size();
    std::vector<std::array<float, 3>> projected(points.size());
    float nearest = -FLT_MAX;
    float farthest = FLT_MAX;
    for (size_t index = 0; index < points.size(); ++index)
    {
        const bx::Vec3 position = {points[index][0], points[index][1], points[index][2]};
        projected[index] = {bx::dot(position, right), bx::dot(position, up), bx::dot(position, toCamera)};
        nearest = std::max(nearest, projected[index][2]);
        farthest = std::min(farthest, projected[index][2]);
    }
    std::array<float, 3> middle = {0.0f, 0.0f, (nearest + farthest) * 0.5f};
    const float tanHalf = std::tan(bx::toRad(PortraitFovDegrees) * 0.5f);
    float distance = 1.0f;
    for (int pass = 0; pass < 4; ++pass)
    {
        // Screen extents of the rest poses (at unit distance), around the current centre.
        std::array<float, 2> minimum = {FLT_MAX, FLT_MAX};
        std::array<float, 2> maximum = {-FLT_MAX, -FLT_MAX};
        for (size_t index = 0; index < restCount; ++index)
        {
            const float depth = pass == 0 ? 1.0f : distance - (projected[index][2] - middle[2]);
            for (size_t axis = 0; axis < 2; ++axis)
            {
                const float screen = (projected[index][axis] - middle[axis]) / depth;
                minimum[axis] = std::min(minimum[axis], screen);
                maximum[axis] = std::max(maximum[axis], screen);
            }
        }
        for (size_t axis = 0; axis < 2; ++axis)
        {
            middle[axis] += (minimum[axis] + maximum[axis]) * 0.5f * (pass == 0 ? 1.0f : distance);
        }
        distance = 1.0f;
        for (size_t index = 0; index < points.size(); ++index)
        {
            const float extent = std::max(std::abs(projected[index][0] - middle[0]),
                std::abs(projected[index][1] - middle[1]));
            const float fill = index < restCount ? restFill : PortraitAttackFill;
            distance = std::max(distance, extent / (tanHalf * fill) + projected[index][2] - middle[2]);
        }
    }
    const bx::Vec3 center = bx::add(bx::add(bx::mul(right, middle[0]), bx::mul(up, middle[1])),
        bx::mul(toCamera, middle[2]));
    const float depthExtent = (nearest - farthest) * 0.5f;
    const bx::Vec3 eye = bx::add(center, bx::mul(toCamera, distance));
    m_eye = {eye.x, eye.y, eye.z};
    bx::mtxLookAt(m_view.data(), eye, center, worldUp, bx::Handedness::Right);
    const float zoomedFovDegrees = bx::toDeg(2.0f * std::atan(tanHalf / zoom));
    bx::mtxProj(m_projection.data(), zoomedFovDegrees, 1.0f, std::max(1.0f, (distance - depthExtent) * 0.5f),
        distance + depthExtent * 2.0f, bgfx::getCaps()->homogeneousDepth, bx::Handedness::Right);
}

bool ActorModelPreview::ensureTarget(uint16_t size)
{
    if (bgfx::isValid(m_frameBuffer) && m_size == size)
    {
        return true;
    }
    destroyTarget();
    const bgfx::TextureFormat::Enum depthFormat =
        bgfx::isTextureValid(0, false, 1, bgfx::TextureFormat::D24S8, BGFX_TEXTURE_RT_WRITE_ONLY)
        ? bgfx::TextureFormat::D24S8 : bgfx::TextureFormat::D16;
    const std::array<bgfx::TextureHandle, 2> attachments = {
        bgfx::createTexture2D(size, size, false, 1, bgfx::TextureFormat::RGBA8,
            BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP),
        bgfx::createTexture2D(size, size, false, 1, depthFormat, BGFX_TEXTURE_RT_WRITE_ONLY)};
    if (bgfx::isValid(attachments[0]) && bgfx::isValid(attachments[1]))
    {
        m_frameBuffer = bgfx::createFrameBuffer(uint8_t(attachments.size()), attachments.data(), true);
    }
    if (!bgfx::isValid(m_frameBuffer))
    {
        for (const bgfx::TextureHandle texture : attachments)
        {
            if (bgfx::isValid(texture))
            {
                bgfx::destroy(texture);
            }
        }
        std::cerr << "Actor portrait render target unavailable; the inspect popup keeps sprite previews.\n";
        m_failed = true;
        return false;
    }
    if (!bgfx::isValid(m_worldClipPlaneUniform))
    {
        m_worldClipPlaneUniform = bgfx::createUniform("u_worldClipPlane", bgfx::UniformType::Vec4);
    }
    m_colorTexture = attachments[0];
    m_size = size;
    return true;
}

void ActorModelPreview::destroyTarget()
{
    if (bgfx::isValid(m_frameBuffer))
    {
        bgfx::destroy(m_frameBuffer);
    }
    m_frameBuffer = BGFX_INVALID_HANDLE;
    m_colorTexture = BGFX_INVALID_HANDLE;
    m_size = 0;
}

void ActorModelPreview::shutdown()
{
    m_effectRenderer.shutdown(Engine::BgfxContext::isBgfxInitialized());
    m_effectResources.shutdown();
    m_pWorldFx = nullptr;
    m_pModelRenderer = nullptr;
    m_decorationModels = {};
    m_failed = false;
    m_framedHandle = {};
    if (!Engine::BgfxContext::isBgfxInitialized())
    {
        m_frameBuffer = BGFX_INVALID_HANDLE;
        m_colorTexture = BGFX_INVALID_HANDLE;
        m_worldClipPlaneUniform = BGFX_INVALID_HANDLE;
        m_size = 0;
        return;
    }
    destroyTarget();
    if (bgfx::isValid(m_worldClipPlaneUniform))
    {
        bgfx::destroy(m_worldClipPlaneUniform);
        m_worldClipPlaneUniform = BGFX_INVALID_HANDLE;
    }
}
}

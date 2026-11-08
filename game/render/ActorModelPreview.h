#pragma once

#include "engine/models/ModelInstance.h"
#include "game/fx/ActorPortraitKind.h"
#include "game/fx/EffectRenderer.h"
#include "game/fx/TalkPortraitFrame.h"
#include "game/fx/WorldFxRenderResources.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <vector>

namespace OpenYAMM::Engine
{
class ModelRenderer;
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class EffectSystem;
class IGameplayWorldRuntime;
class WorldFxSystem;

// The actor inspect popup's 3D portrait: the inspected actor's portrait model (WorldFxSystem::syncInspectPortrait)
// drawn alone into a small offscreen target (ActorPortraitView, ordered before the HUD view that shows it). While the
// popup shows a modelled actor it costs one posed skeleton and one draw into a few hundred pixels square; otherwise
// nothing. Actors without a model keep their sprite preview. A Talk preview is a second one, in its own view
// (ActorTalkPortraitView): a speaking MM9 actor's head and shoulders for the talk ring and a venue's sidebar.
class ActorModelPreview
{
public:
    explicit ActorModelPreview(ActorPortraitKind kind = ActorPortraitKind::Inspect);

    // The model a decoration shows now, by its sprite override key (the scene's DecorationModelSet::portraitModel).
    using DecorationModelLookup = std::function<std::optional<DecorationPortraitModel>(uint32_t decorationKey)>;

    // The active scene's actor models and their renderer (null outside a map), and its decoration models.
    void bindScene(WorldFxSystem *pWorldFx, Engine::ModelRenderer *pModelRenderer,
        DecorationModelLookup decorationModels = {});
    // This frame's portrait of the actor for a square of pixelSize HUD pixels, or an invalid handle when the actor
    // has no model. The texture's rows run bottom-up when the renderer's origin is bottom-left.
    bgfx::TextureHandle render(const IGameplayWorldRuntime &world, size_t actorIndex, float pixelSize,
        uint32_t animationTicks, const Engine::AssetFileSystem &assets);
    // A Talk preview of a posed talking prop (an MM9 RUDEProp decoration): its decoration's model, framed and lit as
    // a speaking actor's. Invalid when the decoration draws no model.
    bgfx::TextureHandle renderDecoration(uint32_t decorationKey, float pixelSize,
        const Engine::AssetFileSystem &assets);
    void shutdown();

private:
    // Draws a synced portrait (WorldFxSystem::InspectPortrait's handle, framing and effects) into the target.
    bgfx::TextureHandle draw(Engine::ModelInstanceHandle handle, const std::vector<std::array<float, 3>> &framePoints,
        size_t restPointCount, const EffectSystem *pEffects, float pixelSize, const Engine::AssetFileSystem &assets);
    // Camera for a new portrait (WorldFxSystem::InspectPortrait framing), held while it plays.
    void frame(const std::vector<std::array<float, 3>> &points, size_t restPointCount);
    bool ensureTarget(uint16_t size);
    void destroyTarget();

    ActorPortraitKind m_kind = ActorPortraitKind::Inspect;
    uint16_t m_viewId = 0;
    WorldFxSystem *m_pWorldFx = nullptr;
    Engine::ModelRenderer *m_pModelRenderer = nullptr;
    DecorationModelLookup m_decorationModels;
    bgfx::FrameBufferHandle m_frameBuffer = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_colorTexture = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_worldClipPlaneUniform = BGFX_INVALID_HANDLE;
    uint16_t m_size = 0;
    Engine::ModelInstanceHandle m_framedHandle;
    std::array<float, 16> m_view = {};
    std::array<float, 16> m_projection = {};
    std::array<float, 3> m_eye = {};
    bool m_failed = false;
    EffectRenderer m_effectRenderer;
    WorldFxRenderResources m_effectResources;
};
}

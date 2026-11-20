#include "game/ui/screens/LoadingOverlayScreen.h"
#include "engine/BgfxContext.h"
#include "game/render/WaterMath.h"
#include "game/ui/RestHourglassAnimation.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ReferenceWidth = 640.0f;
constexpr float ReferenceHeight = 480.0f;
constexpr float MaxUiScale = 8.0f;
constexpr float ProgressBarX = 173.0f;
constexpr float ProgressBarY = 459.0f;
constexpr float ProgressBarWidth = 299.0f;
constexpr float ProgressBarHeight = 14.0f;
constexpr int ProgressStepPercent = 5;
constexpr int ProgressStepCount = 20;
constexpr float LoadingHourglassSpeed = 4.0f;
}

LoadingOverlayScreen::LoadingOverlayScreen(const Engine::AssetFileSystem &assetFileSystem)
    : MenuDesignScreen(assetFileSystem)
{
    // Loading can start after world, HUD or menu draws have already been submitted.
    // Cover them with the retained screen or loading artwork on every loading frame.
    setRenderViewId(LoadingOverlayView);
    setClearBackground(true);
}

LoadingOverlayScreen::~LoadingOverlayScreen()
{
    if (bgfx::isValid(m_transitionBackground) && Engine::BgfxContext::isBgfxInitialized())
    {
        bgfx::destroy(m_transitionBackground);
    }
}

bgfx::FrameBufferHandle LoadingOverlayScreen::createTransitionBackground(int width, int height)
{
    if (bgfx::isValid(m_transitionBackground))
    {
        bgfx::destroy(m_transitionBackground);
        m_transitionBackground = BGFX_INVALID_HANDLE;
    }

    const uint64_t flags = BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP;
    const bgfx::TextureHandle attachments[] = {
        bgfx::createTexture2D(uint16_t(width), uint16_t(height), false, 1, bgfx::TextureFormat::RGBA8, flags),
        bgfx::createTexture2D(
            uint16_t(width), uint16_t(height), false, 1, bgfx::TextureFormat::D24S8, BGFX_TEXTURE_RT_WRITE_ONLY)
    };
    if (!bgfx::isValid(attachments[0]) || !bgfx::isValid(attachments[1]))
    {
        for (bgfx::TextureHandle texture : attachments)
        {
            if (bgfx::isValid(texture))
            {
                bgfx::destroy(texture);
            }
        }
        throw std::runtime_error("Unable to allocate transition background textures");
    }
    m_transitionBackground = bgfx::createFrameBuffer(2, attachments, true);
    if (!bgfx::isValid(m_transitionBackground))
    {
        throw std::runtime_error("Unable to allocate transition background framebuffer");
    }
    return m_transitionBackground;
}

AppMode LoadingOverlayScreen::mode() const
{
    return AppMode::LoadMenu;
}

void LoadingOverlayScreen::setPresentation(Presentation presentation)
{
    m_presentation = presentation;
    m_animationStartTicks = SDL_GetTicks();
    if (presentation == Presentation::DungeonTransition)
    {
        loadDesign("gameplay/loading");
        preloadLayoutAssets(m_designLayouts);
    }
}

void LoadingOverlayScreen::setBackgroundTextureName(const std::string &textureName)
{
    m_backgroundTextureName = textureName;
}

void LoadingOverlayScreen::setProgressPercent(int progressPercent)
{
    m_progressPercent = std::clamp(progressPercent, 0, 100);
}

void LoadingOverlayScreen::drawHourglass(const Rect &rect)
{
    namespace Atlas = RestHourglassAtlas;
    const UiLayoutManager::LayoutElement *pLayout = m_designLayouts.findElement("LoadingHourglass");
    const std::optional<TextureSize> sandSize = textureSize(pLayout->primaryAsset);
    if (!sandSize)
    {
        return;
    }
    const uint64_t cycleMilliseconds = uint64_t(RestHourglassCycleSeconds * 1000.0f / LoadingHourglassSpeed);
    const float elapsed = float((SDL_GetTicks() - m_animationStartTicks) % cycleMilliseconds)
        * LoadingHourglassSpeed / 1000.0f;
    const RestHourglassFrame pose = restHourglassFrame(elapsed);
    const float sourceScaleX = sandSize->width / float(Atlas::atlasWidth);
    const float sourceScaleY = sandSize->height / float(Atlas::atlasHeight);
    const SourceRect crop{
        float((pose.sandFrame % Atlas::columns) * Atlas::cellWidth + Atlas::padding) * sourceScaleX,
        float((pose.sandFrame / Atlas::columns) * Atlas::cellHeight + Atlas::padding) * sourceScaleY,
        float(Atlas::cropWidth) * sourceScaleX, float(Atlas::cropHeight) * sourceScaleY};
    const float sx = rect.width / float(Atlas::canvasWidth);
    const float sy = rect.height / float(Atlas::canvasHeight);
    // Both atlas crop and glass shell share the same centre, including during the turn.
    drawTextureRegionColor(pLayout->primaryAsset, crop,
        {rect.x + float(Atlas::cropX) * sx, rect.y + float(Atlas::cropY) * sy,
         float(Atlas::cropWidth) * sx, float(Atlas::cropHeight) * sy}, 0xffffffffu, pose.sandRotationRadians);
    drawTextureRegionColor(pLayout->tertiaryAsset, {}, rect, 0xffffffffu, pose.frameRotationRadians);
}

void LoadingOverlayScreen::drawTransition()
{
    const UiLayoutManager::LayoutElement *pPanel = m_designLayouts.findElement("LoadingPanel");
    drawTexture(pPanel->primaryAsset, designRect("LoadingPanel"));
    drawHourglass(designRect("LoadingHourglass"));
    label("LoadingTitle", m_designLayouts.findElement("LoadingTitle")->labelText);

    const Rect track = designRect("LoadingProgress");
    const float line = std::max(1.0f, designScale());
    drawSolidRect(track, 0xff556975u);
    const Rect inside{track.x + line, track.y + line, track.width - 2 * line, track.height - 2 * line};
    drawSolidRect(inside, 0xff111813u);
    const float filledWidth = inside.width * float(m_progressPercent) / 100.0f;
    if (filledWidth > 0)
    {
        drawSolidRect({inside.x, inside.y, filledWidth, inside.height}, 0xff3134cfu);
        drawSolidRect({inside.x, inside.y, filledWidth, line}, 0xff4752e6u);
        drawSolidRect({inside.x, inside.y + inside.height - line, filledWidth, line}, 0xff1e208cu);
    }
}

void LoadingOverlayScreen::drawScreen(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);
    bgfx::setViewFrameBuffer(LoadingOverlayView, BGFX_INVALID_HANDLE);

    const float baseScale = std::min(
        std::min(
            static_cast<float>(frameWidth()) / ReferenceWidth,
            static_cast<float>(frameHeight()) / ReferenceHeight),
        MaxUiScale);
    const float viewportWidth = ReferenceWidth * baseScale;
    const float viewportHeight = ReferenceHeight * baseScale;
    const float viewportX = (static_cast<float>(frameWidth()) - viewportWidth) * 0.5f;
    const float viewportY = (static_cast<float>(frameHeight()) - viewportHeight) * 0.5f;

    if (m_presentation == Presentation::DungeonTransition)
    {
        drawTextureHandle(
            bgfx::getTexture(m_transitionBackground),
            Rect{0.0f, 0.0f, float(frameWidth()), float(frameHeight())},
            bgfx::getCaps()->originBottomLeft,
            false);

        drawTransition();
        return;
    }

    drawTexture(
        m_backgroundTextureName,
        Rect{
            std::round(viewportX),
            std::round(viewportY),
            std::round(viewportWidth),
            std::round(viewportHeight)
        });

    const int filledSteps = m_progressPercent >= 100
        ? ProgressStepCount
        : std::clamp(m_progressPercent / ProgressStepPercent, 0, ProgressStepCount - 1);

    if (filledSteps <= 0)
    {
        return;
    }

    const float fillFraction = static_cast<float>(filledSteps) / static_cast<float>(ProgressStepCount);
    const float filledWidth = ProgressBarWidth * fillFraction;
    const Rect destinationRect = {
        std::round(viewportX + ProgressBarX * baseScale),
        std::round(viewportY + ProgressBarY * baseScale),
        std::round(filledWidth * baseScale),
        std::round(ProgressBarHeight * baseScale)
    };
    const SourceRect sourceRect = {
        0.0f,
        0.0f,
        filledWidth,
        ProgressBarHeight
    };

    drawTextureRegion("loadprog", sourceRect, destinationRect);
}
}

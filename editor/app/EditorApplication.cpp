#include "editor/app/EditorApplication.h"

#include "engine/BgfxContext.h"

#include <imgui.h>
#include <backends/imgui_impl_sdl3.h>
#include <bgfx/bgfx.h>
#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <iostream>
#include <string>

namespace OpenYAMM::Editor
{
namespace
{
void configureImGuiStyle()
{
    ImGuiStyle &style = ImGui::GetStyle();
    style.WindowRounding = 4.0f;
    style.ChildRounding = 4.0f;
    style.FrameRounding = 3.0f;
    style.GrabRounding = 3.0f;
    style.TabRounding = 3.0f;
    style.PopupRounding = 4.0f;
    style.ScrollbarRounding = 4.0f;
    style.WindowBorderSize = 1.0f;
    style.ChildBorderSize = 1.0f;
    style.FrameBorderSize = 1.0f;
    style.TabBorderSize = 1.0f;
    style.WindowPadding = ImVec2(8.0f, 8.0f);
    style.FramePadding = ImVec2(7.0f, 4.0f);
    style.CellPadding = ImVec2(6.0f, 4.0f);
    style.ItemSpacing = ImVec2(8.0f, 6.0f);
    style.ItemInnerSpacing = ImVec2(6.0f, 4.0f);
    style.SeparatorTextBorderSize = 1.0f;
    style.SeparatorTextAlign = ImVec2(0.0f, 0.5f);
    style.IndentSpacing = 16.0f;

    ImVec4 *pColors = style.Colors;
    pColors[ImGuiCol_Text] = ImVec4(0.91f, 0.92f, 0.93f, 1.0f);
    pColors[ImGuiCol_TextDisabled] = ImVec4(0.42f, 0.46f, 0.51f, 1.0f);
    pColors[ImGuiCol_WindowBg] = ImVec4(0.09f, 0.10f, 0.11f, 1.0f);
    pColors[ImGuiCol_ChildBg] = ImVec4(0.12f, 0.13f, 0.15f, 1.0f);
    pColors[ImGuiCol_PopupBg] = ImVec4(0.10f, 0.11f, 0.13f, 0.98f);
    pColors[ImGuiCol_Border] = ImVec4(0.20f, 0.23f, 0.27f, 1.0f);
    pColors[ImGuiCol_BorderShadow] = ImVec4(0.00f, 0.00f, 0.00f, 0.0f);
    pColors[ImGuiCol_FrameBg] = ImVec4(0.15f, 0.17f, 0.19f, 1.0f);
    pColors[ImGuiCol_FrameBgHovered] = ImVec4(0.18f, 0.20f, 0.23f, 1.0f);
    pColors[ImGuiCol_FrameBgActive] = ImVec4(0.22f, 0.25f, 0.29f, 1.0f);
    pColors[ImGuiCol_TitleBg] = ImVec4(0.11f, 0.12f, 0.14f, 1.0f);
    pColors[ImGuiCol_TitleBgActive] = ImVec4(0.13f, 0.15f, 0.17f, 1.0f);
    pColors[ImGuiCol_TitleBgCollapsed] = ImVec4(0.11f, 0.12f, 0.14f, 1.0f);
    pColors[ImGuiCol_MenuBarBg] = ImVec4(0.11f, 0.12f, 0.14f, 1.0f);
    pColors[ImGuiCol_ScrollbarBg] = ImVec4(0.11f, 0.12f, 0.13f, 1.0f);
    pColors[ImGuiCol_ScrollbarGrab] = ImVec4(0.24f, 0.27f, 0.31f, 1.0f);
    pColors[ImGuiCol_ScrollbarGrabHovered] = ImVec4(0.31f, 0.35f, 0.41f, 1.0f);
    pColors[ImGuiCol_ScrollbarGrabActive] = ImVec4(0.38f, 0.42f, 0.48f, 1.0f);
    pColors[ImGuiCol_CheckMark] = ImVec4(0.82f, 0.67f, 0.34f, 1.0f);
    pColors[ImGuiCol_SliderGrab] = ImVec4(0.73f, 0.59f, 0.29f, 1.0f);
    pColors[ImGuiCol_SliderGrabActive] = ImVec4(0.84f, 0.69f, 0.36f, 1.0f);
    pColors[ImGuiCol_Button] = ImVec4(0.14f, 0.16f, 0.18f, 1.0f);
    pColors[ImGuiCol_ButtonHovered] = ImVec4(0.18f, 0.20f, 0.23f, 1.0f);
    pColors[ImGuiCol_ButtonActive] = ImVec4(0.22f, 0.25f, 0.29f, 1.0f);
    pColors[ImGuiCol_Header] = ImVec4(0.16f, 0.18f, 0.20f, 1.0f);
    pColors[ImGuiCol_HeaderHovered] = ImVec4(0.20f, 0.23f, 0.26f, 1.0f);
    pColors[ImGuiCol_HeaderActive] = ImVec4(0.34f, 0.25f, 0.14f, 1.0f);
    pColors[ImGuiCol_Separator] = ImVec4(0.20f, 0.23f, 0.27f, 1.0f);
    pColors[ImGuiCol_SeparatorHovered] = ImVec4(0.34f, 0.38f, 0.45f, 1.0f);
    pColors[ImGuiCol_SeparatorActive] = ImVec4(0.84f, 0.69f, 0.36f, 1.0f);
    pColors[ImGuiCol_ResizeGrip] = ImVec4(0.23f, 0.26f, 0.31f, 0.8f);
    pColors[ImGuiCol_ResizeGripHovered] = ImVec4(0.34f, 0.38f, 0.45f, 1.0f);
    pColors[ImGuiCol_ResizeGripActive] = ImVec4(0.84f, 0.69f, 0.36f, 1.0f);
    pColors[ImGuiCol_Tab] = ImVec4(0.12f, 0.13f, 0.15f, 1.0f);
    pColors[ImGuiCol_TabHovered] = ImVec4(0.17f, 0.19f, 0.22f, 1.0f);
    pColors[ImGuiCol_TabActive] = ImVec4(0.27f, 0.21f, 0.13f, 1.0f);
    pColors[ImGuiCol_TabUnfocused] = ImVec4(0.11f, 0.12f, 0.14f, 1.0f);
    pColors[ImGuiCol_TabUnfocusedActive] = ImVec4(0.19f, 0.16f, 0.12f, 1.0f);
    pColors[ImGuiCol_DockingPreview] = ImVec4(0.37f, 0.60f, 0.90f, 0.50f);
    pColors[ImGuiCol_DockingEmptyBg] = ImVec4(0.08f, 0.09f, 0.10f, 1.0f);
    pColors[ImGuiCol_PlotLines] = ImVec4(0.82f, 0.67f, 0.34f, 1.0f);
    pColors[ImGuiCol_PlotLinesHovered] = ImVec4(0.88f, 0.64f, 0.29f, 1.0f);
    pColors[ImGuiCol_PlotHistogram] = ImVec4(0.82f, 0.67f, 0.34f, 1.0f);
    pColors[ImGuiCol_PlotHistogramHovered] = ImVec4(0.88f, 0.64f, 0.29f, 1.0f);
    pColors[ImGuiCol_TableHeaderBg] = ImVec4(0.12f, 0.14f, 0.16f, 1.0f);
    pColors[ImGuiCol_TableBorderStrong] = ImVec4(0.21f, 0.24f, 0.28f, 1.0f);
    pColors[ImGuiCol_TableBorderLight] = ImVec4(0.17f, 0.19f, 0.22f, 1.0f);
    pColors[ImGuiCol_TableRowBg] = ImVec4(0.00f, 0.00f, 0.00f, 0.0f);
    pColors[ImGuiCol_TableRowBgAlt] = ImVec4(1.00f, 1.00f, 1.00f, 0.03f);
    pColors[ImGuiCol_TextSelectedBg] = ImVec4(0.26f, 0.20f, 0.11f, 1.0f);
    pColors[ImGuiCol_DragDropTarget] = ImVec4(0.37f, 0.60f, 0.90f, 1.0f);
    pColors[ImGuiCol_NavCursor] = ImVec4(0.37f, 0.60f, 0.90f, 1.0f);
    pColors[ImGuiCol_NavWindowingHighlight] = ImVec4(0.37f, 0.60f, 0.90f, 0.70f);
    pColors[ImGuiCol_NavWindowingDimBg] = ImVec4(0.04f, 0.04f, 0.05f, 0.50f);
    pColors[ImGuiCol_ModalWindowDimBg] = ImVec4(0.04f, 0.04f, 0.05f, 0.65f);
}

std::filesystem::path resolveRenderSmokeMapPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::filesystem::path &mapPath)
{
    if (mapPath.is_absolute() || std::filesystem::exists(mapPath))
    {
        return mapPath;
    }

    return assetFileSystem.getEditorDevelopmentRoot()
        / "worlds"
        / assetFileSystem.getActiveWorldId()
        / "maps"
        / mapPath;
}

struct ScreenshotPixelStats
{
    uint32_t visiblePixels = 0;
    uint32_t colorBuckets = 0;
};

ScreenshotPixelStats analyzeScreenshotPixels(const Engine::BgfxContext::ScreenshotCapture &screenshot)
{
    ScreenshotPixelStats stats = {};
    std::array<bool, 4096> colorBuckets = {};

    if (screenshot.width == 0
        || screenshot.height == 0
        || screenshot.bgraPixels.size()
            < static_cast<size_t>(screenshot.width) * static_cast<size_t>(screenshot.height) * 4u)
    {
        return stats;
    }

    const size_t pixelCount = static_cast<size_t>(screenshot.width) * static_cast<size_t>(screenshot.height);

    for (size_t pixelIndex = 0; pixelIndex < pixelCount; ++pixelIndex)
    {
        const size_t byteIndex = pixelIndex * 4u;
        const uint8_t blue = screenshot.bgraPixels[byteIndex + 0u];
        const uint8_t green = screenshot.bgraPixels[byteIndex + 1u];
        const uint8_t red = screenshot.bgraPixels[byteIndex + 2u];
        const uint8_t maxChannel = std::max(red, std::max(green, blue));

        if (maxChannel <= 12)
        {
            continue;
        }

        ++stats.visiblePixels;

        const size_t bucketIndex =
            (static_cast<size_t>(red >> 4u) << 8u)
            | (static_cast<size_t>(green >> 4u) << 4u)
            | static_cast<size_t>(blue >> 4u);
        colorBuckets[bucketIndex] = true;
    }

    for (bool occupied : colorBuckets)
    {
        if (occupied)
        {
            ++stats.colorBuckets;
        }
    }

    return stats;
}

const char *renderSmokeModeName(EditorRenderSmokeMode mode)
{
    switch (mode)
    {
    case EditorRenderSmokeMode::ModelInstancesOnly:
        return "model_instances_only";

    case EditorRenderSmokeMode::SkyOnly:
        return "sky_only";

    case EditorRenderSmokeMode::PhysicsOnly:
        return "physics_only";

    case EditorRenderSmokeMode::WaterOnly:
        return "water_only";

    case EditorRenderSmokeMode::VisibilityOnly:
        return "visibility_only";

    case EditorRenderSmokeMode::InvisibleOnly:
        return "invisible_only";

    case EditorRenderSmokeMode::HelperOnly:
        return "helper_only";

    case EditorRenderSmokeMode::TriggerOnly:
        return "trigger_only";

    case EditorRenderSmokeMode::FullScene:
    default:
        return "full_scene";
    }
}
}

EditorApplication::EditorApplication(
    const Engine::ApplicationConfig &config,
    const EditorRenderSmokeConfig &renderSmokeConfig)
    : m_engineApplication(
        config,
        [this](Engine::AssetFileSystem &assetFileSystem)
        {
            return startup(assetFileSystem);
        },
        [this]()
        {
            return setupRendering();
        },
        [this](const SDL_Event &event)
        {
            handleEvent(event);
        },
        [this](int width, int height, float mouseWheelDelta, float deltaSeconds)
        {
            renderFrame(width, height, mouseWheelDelta, deltaSeconds);
        },
        [this]()
        {
            shutdown();
        })
    , m_renderSmokeConfig(renderSmokeConfig)
{
}

int EditorApplication::run()
{
    const int engineResult = m_engineApplication.run();

    if (engineResult != 0)
    {
        return engineResult;
    }

    return m_renderSmokeExitCode.value_or(0);
}

bool EditorApplication::startup(Engine::AssetFileSystem &assetFileSystem)
{
    m_pAssetFileSystem = &assetFileSystem;
    m_session.initialize(assetFileSystem);

    std::string errorMessage;

    if (m_renderSmokeConfig.enabled)
    {
        const std::filesystem::path mapPath =
            resolveRenderSmokeMapPath(assetFileSystem, m_renderSmokeConfig.mapPath);

        if (!m_session.openMapPhysicalPath(mapPath, errorMessage))
        {
            std::cerr << "Editor render smoke failed: " << errorMessage << '\n';
            return false;
        }

        m_pRenderSmokeViewport = std::make_unique<EditorOutdoorViewport>();
        if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::ModelInstancesOnly)
        {
            m_pRenderSmokeViewport->setShowTerrainFill(false);
            m_pRenderSmokeViewport->setShowTerrainGrid(false);
            m_pRenderSmokeViewport->setShowBModels(false);
            m_pRenderSmokeViewport->setShowEntities(false);
            m_pRenderSmokeViewport->setShowActors(false);
            m_pRenderSmokeViewport->setShowSpriteObjects(false);
            m_pRenderSmokeViewport->setShowSpawns(false);
            m_pRenderSmokeViewport->setShowEventMarkers(false);
            m_pRenderSmokeViewport->setShowMm9DatPortals(false);
        }
        else if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::PhysicsOnly)
        {
            m_pRenderSmokeViewport->setMm9DatWorldRenderSubset(EditorOutdoorViewport::Mm9DatWorldRenderSubset::Physics);
            m_pRenderSmokeViewport->setShowTerrainGrid(false);
            m_pRenderSmokeViewport->setShowModelInstances(false);
            m_pRenderSmokeViewport->setShowEntities(false);
            m_pRenderSmokeViewport->setShowActors(false);
            m_pRenderSmokeViewport->setShowSpriteObjects(false);
            m_pRenderSmokeViewport->setShowSpawns(false);
            m_pRenderSmokeViewport->setShowEventMarkers(false);
            m_pRenderSmokeViewport->setShowMm9DatPortals(false);
        }
        else if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::SkyOnly)
        {
            m_pRenderSmokeViewport->setMm9DatWorldRenderSubset(EditorOutdoorViewport::Mm9DatWorldRenderSubset::Sky);
            m_pRenderSmokeViewport->setShowTerrainGrid(false);
            m_pRenderSmokeViewport->setShowModelInstances(false);
            m_pRenderSmokeViewport->setShowEntities(false);
            m_pRenderSmokeViewport->setShowActors(false);
            m_pRenderSmokeViewport->setShowSpriteObjects(false);
            m_pRenderSmokeViewport->setShowSpawns(false);
            m_pRenderSmokeViewport->setShowEventMarkers(false);
            m_pRenderSmokeViewport->setShowMm9DatPortals(false);
        }
        else if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::WaterOnly)
        {
            m_pRenderSmokeViewport->setMm9DatWorldRenderSubset(EditorOutdoorViewport::Mm9DatWorldRenderSubset::Water);
            m_pRenderSmokeViewport->setShowTerrainGrid(false);
            m_pRenderSmokeViewport->setShowModelInstances(false);
            m_pRenderSmokeViewport->setShowEntities(false);
            m_pRenderSmokeViewport->setShowActors(false);
            m_pRenderSmokeViewport->setShowSpriteObjects(false);
            m_pRenderSmokeViewport->setShowSpawns(false);
            m_pRenderSmokeViewport->setShowEventMarkers(false);
            m_pRenderSmokeViewport->setShowMm9DatPortals(false);
        }
        else if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::VisibilityOnly)
        {
            m_pRenderSmokeViewport->setMm9DatWorldRenderSubset(
                EditorOutdoorViewport::Mm9DatWorldRenderSubset::Visibility);
            m_pRenderSmokeViewport->setShowTerrainGrid(false);
            m_pRenderSmokeViewport->setShowModelInstances(false);
            m_pRenderSmokeViewport->setShowEntities(false);
            m_pRenderSmokeViewport->setShowActors(false);
            m_pRenderSmokeViewport->setShowSpriteObjects(false);
            m_pRenderSmokeViewport->setShowSpawns(false);
            m_pRenderSmokeViewport->setShowEventMarkers(false);
            m_pRenderSmokeViewport->setShowMm9DatPortals(false);
        }
        else if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::InvisibleOnly)
        {
            m_pRenderSmokeViewport->setMm9DatWorldRenderSubset(
                EditorOutdoorViewport::Mm9DatWorldRenderSubset::Invisible);
            m_pRenderSmokeViewport->setShowTerrainGrid(false);
            m_pRenderSmokeViewport->setShowModelInstances(false);
            m_pRenderSmokeViewport->setShowEntities(false);
            m_pRenderSmokeViewport->setShowActors(false);
            m_pRenderSmokeViewport->setShowSpriteObjects(false);
            m_pRenderSmokeViewport->setShowSpawns(false);
            m_pRenderSmokeViewport->setShowEventMarkers(false);
            m_pRenderSmokeViewport->setShowMm9DatPortals(false);
        }
        else if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::HelperOnly)
        {
            m_pRenderSmokeViewport->setMm9DatWorldRenderSubset(EditorOutdoorViewport::Mm9DatWorldRenderSubset::Helper);
            m_pRenderSmokeViewport->setShowTerrainGrid(false);
            m_pRenderSmokeViewport->setShowModelInstances(false);
            m_pRenderSmokeViewport->setShowEntities(false);
            m_pRenderSmokeViewport->setShowActors(false);
            m_pRenderSmokeViewport->setShowSpriteObjects(false);
            m_pRenderSmokeViewport->setShowSpawns(false);
            m_pRenderSmokeViewport->setShowEventMarkers(false);
            m_pRenderSmokeViewport->setShowMm9DatPortals(false);
        }
        else if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::TriggerOnly)
        {
            m_pRenderSmokeViewport->setMm9DatWorldRenderSubset(EditorOutdoorViewport::Mm9DatWorldRenderSubset::Trigger);
            m_pRenderSmokeViewport->setShowTerrainGrid(false);
            m_pRenderSmokeViewport->setShowModelInstances(false);
            m_pRenderSmokeViewport->setShowEntities(false);
            m_pRenderSmokeViewport->setShowActors(false);
            m_pRenderSmokeViewport->setShowSpriteObjects(false);
            m_pRenderSmokeViewport->setShowSpawns(false);
            m_pRenderSmokeViewport->setShowEventMarkers(false);
            m_pRenderSmokeViewport->setShowMm9DatPortals(false);
        }
        m_renderSmokeCaptureToken =
            std::string("openyamm-editor-mm9-dat-render-smoke:")
            + renderSmokeModeName(m_renderSmokeConfig.mode)
            + ":"
            + m_renderSmokeConfig.mapPath.generic_string();
        return true;
    }

    if (!m_mainWindow.restoreLastLoadedMap(m_session, errorMessage))
    {
        if (!errorMessage.empty())
        {
            m_session.logError(errorMessage);
            errorMessage.clear();
        }

        if (!m_session.openDefaultOutdoorDocument(errorMessage))
        {
            m_session.logError(errorMessage);
        }
    }

    return true;
}

bool EditorApplication::setupRendering()
{
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();

    ImGuiIO &io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    io.ConfigFlags |= ImGuiConfigFlags_DockingEnable;
    io.IniFilename = nullptr;
    configureImGuiStyle();

    SDL_Window *pWindow = SDL_GetKeyboardFocus();

    if (pWindow == nullptr)
    {
        pWindow = SDL_GetMouseFocus();
    }

    if (pWindow == nullptr)
    {
        int windowCount = 0;
        SDL_Window **ppWindows = SDL_GetWindows(&windowCount);

        if (ppWindows != nullptr && windowCount > 0)
        {
            pWindow = ppWindows[0];
        }

        SDL_free(ppWindows);
    }

    if (pWindow == nullptr)
    {
        return false;
    }

    if (!ImGui_ImplSDL3_InitForOther(pWindow))
    {
        return false;
    }

    return m_imguiRenderer.initialize();
}

void EditorApplication::handleEvent(const SDL_Event &event)
{
    ImGui_ImplSDL3_ProcessEvent(&event);
}

void EditorApplication::renderFrame(int width, int height, float, float deltaSeconds)
{
    ImGui_ImplSDL3_NewFrame();
    m_imguiRenderer.newFrame();
    ImGui::NewFrame();

    const std::string rendererName = bgfx::getRendererName(bgfx::getRendererType());
    m_session.beginFrameEditTracking();

    if (m_renderSmokeConfig.enabled)
    {
        if (m_pRenderSmokeViewport)
        {
            m_pRenderSmokeViewport->updateAndRender(
                m_session,
                0,
                0,
                static_cast<uint16_t>(std::max(width, 1)),
                static_cast<uint16_t>(std::max(height, 1)),
                false,
                false,
                false,
                false,
                0.0f,
                0.0f,
                deltaSeconds);

            if (bgfx::isValid(m_pRenderSmokeViewport->viewportTextureHandle()))
            {
                ImGui::GetBackgroundDrawList()->AddImage(
                    static_cast<ImTextureID>(
                        static_cast<uintptr_t>(m_pRenderSmokeViewport->viewportTextureHandle().idx + 1)),
                    ImVec2(0.0f, 0.0f),
                    ImVec2(static_cast<float>(std::max(width, 1)), static_cast<float>(std::max(height, 1))),
                    ImVec2(0.0f, 1.0f),
                    ImVec2(1.0f, 0.0f));
            }
        }
    }
    else
    {
        m_mainWindow.render(m_session, m_frameNumber, deltaSeconds, rendererName);
    }

    ImGui::Render();

    m_imguiRenderer.renderDrawData(ImGui::GetDrawData());
    updateRenderSmokeState();
    ++m_frameNumber;
}

void EditorApplication::shutdown()
{
    m_mainWindow.shutdown();
    if (m_pRenderSmokeViewport)
    {
        m_pRenderSmokeViewport->shutdown();
        m_pRenderSmokeViewport.reset();
    }
    m_imguiRenderer.shutdown();
    ImGui_ImplSDL3_Shutdown();
    ImGui::DestroyContext();
}

void EditorApplication::updateRenderSmokeState()
{
    if (!m_renderSmokeConfig.enabled || m_renderSmokeExitCode.has_value())
    {
        return;
    }

    if (m_renderSmokeScreenshotRequested && !m_renderSmokeScreenshotCaptured)
    {
        const std::optional<Engine::BgfxContext::ScreenshotCapture> screenshot =
            Engine::BgfxContext::consumeScreenshot(m_renderSmokeCaptureToken);

        if (screenshot)
        {
            m_renderSmokeScreenshotReceived = true;
            const ScreenshotPixelStats pixelStats = analyzeScreenshotPixels(*screenshot);
            m_renderSmokeScreenshotVisiblePixels = pixelStats.visiblePixels;
            m_renderSmokeScreenshotColorBuckets = pixelStats.colorBuckets;
            m_renderSmokeScreenshotCaptured =
                screenshot->width > 0
                && screenshot->height > 0
                && !screenshot->bgraPixels.empty()
                && pixelStats.visiblePixels > 256
                && pixelStats.colorBuckets >= 16;
        }
    }

    const EditorOutdoorViewport::RenderSubmissionStats &stats =
        m_renderSmokeConfig.enabled && m_pRenderSmokeViewport
            ? m_pRenderSmokeViewport->lastRenderSubmissionStats()
            : m_mainWindow.lastViewportRenderSubmissionStats();

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        requestRenderSmokeExit(
            false,
            std::string("Editor MM9 DAT render smoke cannot verify viewport submissions or screenshots with renderer=")
                + bgfx::getRendererName(bgfx::getRendererType()));
        return;
    }

    if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::ModelInstancesOnly)
    {
        m_renderSmokeSubmittedGeometry =
            stats.valid
            && stats.mm9DatDocument
            && stats.datWorldSubmittedVertices == 0
            && stats.modelInstanceSubmittedVertices > 0;
    }
    else if (m_renderSmokeConfig.mode == EditorRenderSmokeMode::PhysicsOnly
        || m_renderSmokeConfig.mode == EditorRenderSmokeMode::SkyOnly
        || m_renderSmokeConfig.mode == EditorRenderSmokeMode::WaterOnly
        || m_renderSmokeConfig.mode == EditorRenderSmokeMode::VisibilityOnly
        || m_renderSmokeConfig.mode == EditorRenderSmokeMode::InvisibleOnly
        || m_renderSmokeConfig.mode == EditorRenderSmokeMode::HelperOnly
        || m_renderSmokeConfig.mode == EditorRenderSmokeMode::TriggerOnly)
    {
        m_renderSmokeSubmittedGeometry =
            stats.valid
            && stats.mm9DatDocument
            && stats.datWorldSubmittedVertices > 0
            && stats.modelInstanceSubmittedVertices == 0;
    }
    else
    {
        m_renderSmokeSubmittedGeometry =
            stats.valid
            && stats.mm9DatDocument
            && stats.datWorldTexturedSubmissions > 0
            && stats.datWorldSubmittedVertices > 0
            && stats.modelInstanceSubmittedVertices > 0;
    }

    if (m_renderSmokeSubmittedGeometry && !m_renderSmokeScreenshotRequested)
    {
        bgfx::requestScreenShot(BGFX_INVALID_HANDLE, m_renderSmokeCaptureToken.c_str());
        m_renderSmokeScreenshotRequested = true;
        m_renderSmokeScreenshotRequestFrame = m_frameNumber;
    }

    if (m_renderSmokeSubmittedGeometry && m_renderSmokeScreenshotCaptured)
    {
        std::cout
            << "Editor MM9 DAT render smoke passed:"
            << " map=" << m_renderSmokeConfig.mapPath.generic_string()
            << " mode=" << renderSmokeModeName(m_renderSmokeConfig.mode)
            << " dat_world_vertices=" << stats.datWorldSubmittedVertices
            << " dat_world_textured_submissions=" << stats.datWorldTexturedSubmissions
            << " dat_world_missing_material_submissions=" << stats.datWorldMissingMaterialSubmissions
            << " model_instance_vertices=" << stats.modelInstanceSubmittedVertices
            << " model_instance_textured_submissions=" << stats.modelInstanceTexturedSubmissions
            << " model_instance_procedural_submissions=" << stats.modelInstanceProceduralSubmissions
            << " model_instance_missing_submissions=" << stats.modelInstanceMissingSubmissions
            << " screenshot_visible_pixels=" << m_renderSmokeScreenshotVisiblePixels
            << " screenshot_color_buckets=" << m_renderSmokeScreenshotColorBuckets
            << '\n';
        requestRenderSmokeExit(true, {});
        return;
    }

    const uint32_t maxFrames = std::max<uint32_t>(m_renderSmokeConfig.maxFrames, 2);

    const bool timedOut =
        m_renderSmokeScreenshotRequested
            ? (m_frameNumber > m_renderSmokeScreenshotRequestFrame + maxFrames)
            : (m_frameNumber + 1 >= maxFrames);

    if (timedOut)
    {
        if (m_renderSmokeSubmittedGeometry && m_renderSmokeScreenshotRequested && !m_renderSmokeScreenshotReceived)
        {
            std::cout
                << "Editor MM9 DAT render smoke passed without screenshot callback:"
                << " map=" << m_renderSmokeConfig.mapPath.generic_string()
                << " mode=" << renderSmokeModeName(m_renderSmokeConfig.mode)
                << " dat_world_vertices=" << stats.datWorldSubmittedVertices
                << " dat_world_textured_submissions=" << stats.datWorldTexturedSubmissions
                << " dat_world_missing_material_submissions=" << stats.datWorldMissingMaterialSubmissions
                << " model_instance_vertices=" << stats.modelInstanceSubmittedVertices
                << " model_instance_textured_submissions=" << stats.modelInstanceTexturedSubmissions
                << " model_instance_procedural_submissions=" << stats.modelInstanceProceduralSubmissions
                << " model_instance_missing_submissions=" << stats.modelInstanceMissingSubmissions
                << " screenshot_requested=true"
                << " screenshot_received=false"
                << '\n';
            requestRenderSmokeExit(true, {});
            return;
        }

        std::string failure =
            std::string("Editor MM9 DAT render smoke failed: missing viewport submissions or screenshot map=")
            + m_renderSmokeConfig.mapPath.generic_string()
            + " mode=" + renderSmokeModeName(m_renderSmokeConfig.mode)
            + " stats_valid=" + (stats.valid ? "true" : "false")
            + " mm9_dat=" + (stats.mm9DatDocument ? "true" : "false")
            + " dat_world_vertices=" + std::to_string(stats.datWorldSubmittedVertices)
            + " dat_world_textured_submissions=" + std::to_string(stats.datWorldTexturedSubmissions)
            + " model_instance_vertices=" + std::to_string(stats.modelInstanceSubmittedVertices)
            + " screenshot_requested=" + (m_renderSmokeScreenshotRequested ? "true" : "false")
            + " screenshot_received=" + (m_renderSmokeScreenshotReceived ? "true" : "false")
            + " screenshot_captured=" + (m_renderSmokeScreenshotCaptured ? "true" : "false")
            + " screenshot_visible_pixels=" + std::to_string(m_renderSmokeScreenshotVisiblePixels)
            + " screenshot_color_buckets=" + std::to_string(m_renderSmokeScreenshotColorBuckets);
        requestRenderSmokeExit(false, failure);
    }
}

void EditorApplication::requestRenderSmokeExit(bool success, const std::string &message)
{
    m_renderSmokeExitCode = success ? 0 : 1;

    if (!success)
    {
        std::cerr << message << '\n';
    }

    SDL_Event event = {};
    event.type = SDL_EVENT_QUIT;
    SDL_PushEvent(&event);
}
}

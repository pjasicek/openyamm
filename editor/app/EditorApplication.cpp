#include "editor/app/EditorApplication.h"

#include <imgui.h>
#include <backends/imgui_impl_sdl3.h>
#include <bgfx/bgfx.h>
#include <SDL3/SDL.h>

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
    pColors[ImGuiCol_Text] = ImVec4(0.90f, 0.91f, 0.92f, 1.0f);
    pColors[ImGuiCol_TextDisabled] = ImVec4(0.38f, 0.42f, 0.46f, 1.0f);
    pColors[ImGuiCol_WindowBg] = ImVec4(0.11f, 0.13f, 0.15f, 1.0f);
    pColors[ImGuiCol_ChildBg] = ImVec4(0.13f, 0.15f, 0.19f, 1.0f);
    pColors[ImGuiCol_PopupBg] = ImVec4(0.11f, 0.13f, 0.16f, 0.98f);
    pColors[ImGuiCol_Border] = ImVec4(0.23f, 0.26f, 0.31f, 1.0f);
    pColors[ImGuiCol_BorderShadow] = ImVec4(0.00f, 0.00f, 0.00f, 0.0f);
    pColors[ImGuiCol_FrameBg] = ImVec4(0.08f, 0.09f, 0.11f, 1.0f);
    pColors[ImGuiCol_FrameBgHovered] = ImVec4(0.15f, 0.18f, 0.22f, 1.0f);
    pColors[ImGuiCol_FrameBgActive] = ImVec4(0.12f, 0.16f, 0.22f, 1.0f);
    pColors[ImGuiCol_TitleBg] = ImVec4(0.09f, 0.10f, 0.12f, 1.0f);
    pColors[ImGuiCol_TitleBgActive] = ImVec4(0.11f, 0.13f, 0.16f, 1.0f);
    pColors[ImGuiCol_TitleBgCollapsed] = ImVec4(0.09f, 0.10f, 0.12f, 1.0f);
    pColors[ImGuiCol_MenuBarBg] = ImVec4(0.09f, 0.10f, 0.12f, 1.0f);
    pColors[ImGuiCol_ScrollbarBg] = ImVec4(0.08f, 0.09f, 0.11f, 1.0f);
    pColors[ImGuiCol_ScrollbarGrab] = ImVec4(0.23f, 0.26f, 0.31f, 1.0f);
    pColors[ImGuiCol_ScrollbarGrabHovered] = ImVec4(0.34f, 0.38f, 0.45f, 1.0f);
    pColors[ImGuiCol_ScrollbarGrabActive] = ImVec4(0.40f, 0.44f, 0.52f, 1.0f);
    pColors[ImGuiCol_CheckMark] = ImVec4(0.37f, 0.60f, 0.90f, 1.0f);
    pColors[ImGuiCol_SliderGrab] = ImVec4(0.73f, 0.59f, 0.29f, 1.0f);
    pColors[ImGuiCol_SliderGrabActive] = ImVec4(0.82f, 0.67f, 0.34f, 1.0f);
    pColors[ImGuiCol_Button] = ImVec4(0.13f, 0.15f, 0.19f, 1.0f);
    pColors[ImGuiCol_ButtonHovered] = ImVec4(0.15f, 0.18f, 0.22f, 1.0f);
    pColors[ImGuiCol_ButtonActive] = ImVec4(0.10f, 0.11f, 0.13f, 1.0f);
    pColors[ImGuiCol_Header] = ImVec4(0.13f, 0.15f, 0.19f, 1.0f);
    pColors[ImGuiCol_HeaderHovered] = ImVec4(0.15f, 0.18f, 0.22f, 1.0f);
    pColors[ImGuiCol_HeaderActive] = ImVec4(0.23f, 0.17f, 0.09f, 1.0f);
    pColors[ImGuiCol_Separator] = ImVec4(0.17f, 0.19f, 0.23f, 1.0f);
    pColors[ImGuiCol_SeparatorHovered] = ImVec4(0.34f, 0.38f, 0.45f, 1.0f);
    pColors[ImGuiCol_SeparatorActive] = ImVec4(0.37f, 0.60f, 0.90f, 1.0f);
    pColors[ImGuiCol_ResizeGrip] = ImVec4(0.23f, 0.26f, 0.31f, 1.0f);
    pColors[ImGuiCol_ResizeGripHovered] = ImVec4(0.34f, 0.38f, 0.45f, 1.0f);
    pColors[ImGuiCol_ResizeGripActive] = ImVec4(0.37f, 0.60f, 0.90f, 1.0f);
    pColors[ImGuiCol_Tab] = ImVec4(0.11f, 0.13f, 0.16f, 1.0f);
    pColors[ImGuiCol_TabHovered] = ImVec4(0.16f, 0.19f, 0.23f, 1.0f);
    pColors[ImGuiCol_TabActive] = ImVec4(0.23f, 0.17f, 0.09f, 1.0f);
    pColors[ImGuiCol_TabUnfocused] = ImVec4(0.10f, 0.11f, 0.13f, 1.0f);
    pColors[ImGuiCol_TabUnfocusedActive] = ImVec4(0.17f, 0.14f, 0.10f, 1.0f);
    pColors[ImGuiCol_DockingPreview] = ImVec4(0.37f, 0.60f, 0.90f, 0.50f);
    pColors[ImGuiCol_DockingEmptyBg] = ImVec4(0.08f, 0.09f, 0.11f, 1.0f);
    pColors[ImGuiCol_PlotLines] = ImVec4(0.82f, 0.67f, 0.34f, 1.0f);
    pColors[ImGuiCol_PlotLinesHovered] = ImVec4(0.88f, 0.64f, 0.29f, 1.0f);
    pColors[ImGuiCol_PlotHistogram] = ImVec4(0.82f, 0.67f, 0.34f, 1.0f);
    pColors[ImGuiCol_PlotHistogramHovered] = ImVec4(0.88f, 0.64f, 0.29f, 1.0f);
    pColors[ImGuiCol_TableHeaderBg] = ImVec4(0.10f, 0.11f, 0.13f, 1.0f);
    pColors[ImGuiCol_TableBorderStrong] = ImVec4(0.23f, 0.26f, 0.31f, 1.0f);
    pColors[ImGuiCol_TableBorderLight] = ImVec4(0.17f, 0.19f, 0.23f, 1.0f);
    pColors[ImGuiCol_TableRowBg] = ImVec4(0.00f, 0.00f, 0.00f, 0.0f);
    pColors[ImGuiCol_TableRowBgAlt] = ImVec4(1.00f, 1.00f, 1.00f, 0.02f);
    pColors[ImGuiCol_TextSelectedBg] = ImVec4(0.11f, 0.16f, 0.25f, 1.0f);
    pColors[ImGuiCol_DragDropTarget] = ImVec4(0.37f, 0.60f, 0.90f, 1.0f);
    pColors[ImGuiCol_NavCursor] = ImVec4(0.37f, 0.60f, 0.90f, 1.0f);
    pColors[ImGuiCol_NavWindowingHighlight] = ImVec4(0.37f, 0.60f, 0.90f, 0.70f);
    pColors[ImGuiCol_NavWindowingDimBg] = ImVec4(0.04f, 0.04f, 0.05f, 0.50f);
    pColors[ImGuiCol_ModalWindowDimBg] = ImVec4(0.04f, 0.04f, 0.05f, 0.65f);
}
}

EditorApplication::EditorApplication(const Engine::ApplicationConfig &config)
    : m_engineApplication(
        config,
        [this](const Engine::AssetFileSystem &assetFileSystem)
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
{
}

int EditorApplication::run()
{
    return m_engineApplication.run();
}

bool EditorApplication::startup(const Engine::AssetFileSystem &assetFileSystem)
{
    m_pAssetFileSystem = &assetFileSystem;
    m_session.initialize(assetFileSystem);

    std::string errorMessage;

    if (!m_session.openDefaultOutdoorDocument(errorMessage))
    {
        m_session.logError(errorMessage);
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
    m_mainWindow.render(m_session, m_frameNumber, deltaSeconds, rendererName);
    ImGui::Render();

    m_imguiRenderer.renderDrawData(ImGui::GetDrawData());
    ++m_frameNumber;
}

void EditorApplication::shutdown()
{
    m_mainWindow.shutdown();
    m_imguiRenderer.shutdown();
    ImGui_ImplSDL3_Shutdown();
    ImGui::DestroyContext();
}
}

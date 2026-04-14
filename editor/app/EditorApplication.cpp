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
    style.FrameRounding = 3.0f;
    style.GrabRounding = 3.0f;
    style.TabRounding = 3.0f;

    ImVec4 *pColors = style.Colors;
    pColors[ImGuiCol_WindowBg] = ImVec4(0.12f, 0.13f, 0.11f, 1.0f);
    pColors[ImGuiCol_TitleBg] = ImVec4(0.18f, 0.15f, 0.11f, 1.0f);
    pColors[ImGuiCol_TitleBgActive] = ImVec4(0.33f, 0.24f, 0.11f, 1.0f);
    pColors[ImGuiCol_MenuBarBg] = ImVec4(0.15f, 0.14f, 0.12f, 1.0f);
    pColors[ImGuiCol_Header] = ImVec4(0.36f, 0.29f, 0.15f, 0.65f);
    pColors[ImGuiCol_HeaderHovered] = ImVec4(0.49f, 0.38f, 0.17f, 0.80f);
    pColors[ImGuiCol_HeaderActive] = ImVec4(0.59f, 0.42f, 0.15f, 1.0f);
    pColors[ImGuiCol_Button] = ImVec4(0.39f, 0.28f, 0.12f, 0.65f);
    pColors[ImGuiCol_ButtonHovered] = ImVec4(0.53f, 0.37f, 0.14f, 0.85f);
    pColors[ImGuiCol_ButtonActive] = ImVec4(0.63f, 0.42f, 0.13f, 1.0f);
    pColors[ImGuiCol_FrameBg] = ImVec4(0.20f, 0.19f, 0.16f, 1.0f);
    pColors[ImGuiCol_FrameBgHovered] = ImVec4(0.28f, 0.25f, 0.17f, 1.0f);
    pColors[ImGuiCol_FrameBgActive] = ImVec4(0.36f, 0.30f, 0.14f, 1.0f);
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

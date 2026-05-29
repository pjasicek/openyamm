#include "engine/BgfxContext.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/SavePreviewImage.h"
#include "game/mm9/Mm9DatSceneRuntime.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <string>
#include <vector>

namespace
{
constexpr int SmokeWidth = 1280;
constexpr int SmokeHeight = 720;

struct Arguments
{
    std::filesystem::path sourceRoot = ".";
    std::filesystem::path outputPath = "mm9_dat_world_smoke.bmp";
    std::string mapId = "thjorgardcity";
    std::string startName;
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
    int warmupFrames = 8;
    bool requirePixels = true;
};

struct PixelStats
{
    uint8_t maxRed = 0;
    uint8_t maxGreen = 0;
    uint8_t maxBlue = 0;
    size_t litPixels = 0;
};

void printUsage()
{
    std::cerr
        << "usage: mm9_dat_world_render_smoke"
        << " [--source-root <repo-root>]"
        << " [--map-id thjorgardcity]"
        << " [--start-name StartPointTerrain]"
        << " [--yaw-deg 0]"
        << " [--pitch-deg 0]"
        << " [--frames 8]"
        << " [--allow-no-pixels]"
        << " --output <screenshot.bmp>\n";
}

bool readValue(int argc, char **argv, int &index, std::string &value)
{
    if (index + 1 >= argc)
    {
        std::cerr << "missing value for " << argv[index] << '\n';
        return false;
    }

    value = argv[++index];
    return true;
}

bool parseArguments(int argc, char **argv, Arguments &arguments)
{
    for (int index = 1; index < argc; ++index)
    {
        const std::string name = argv[index];
        std::string value;

        if (name == "--source-root")
        {
            if (!readValue(argc, argv, index, value))
            {
                return false;
            }
            arguments.sourceRoot = value;
        }
        else if (name == "--map-id")
        {
            if (!readValue(argc, argv, index, value))
            {
                return false;
            }
            arguments.mapId = value;
        }
        else if (name == "--start-name")
        {
            if (!readValue(argc, argv, index, value))
            {
                return false;
            }
            arguments.startName = value;
        }
        else if (name == "--frames")
        {
            if (!readValue(argc, argv, index, value))
            {
                return false;
            }
            arguments.warmupFrames = std::max(1, std::stoi(value));
        }
        else if (name == "--yaw-deg")
        {
            if (!readValue(argc, argv, index, value))
            {
                return false;
            }
            arguments.yawRadians = std::stof(value) * 3.14159265358979323846f / 180.0f;
        }
        else if (name == "--pitch-deg")
        {
            if (!readValue(argc, argv, index, value))
            {
                return false;
            }
            arguments.pitchRadians = std::stof(value) * 3.14159265358979323846f / 180.0f;
        }
        else if (name == "--output")
        {
            if (!readValue(argc, argv, index, value))
            {
                return false;
            }
            arguments.outputPath = value;
        }
        else if (name == "--allow-no-pixels")
        {
            arguments.requirePixels = false;
        }
        else
        {
            std::cerr << "unknown argument: " << name << '\n';
            return false;
        }
    }

    if (arguments.startName.empty())
    {
        if (arguments.mapId == "thjorgard")
        {
            arguments.startName = "ThjorgardCityTerrainExit";
        }
        else if (arguments.mapId == "thjorgardcity")
        {
            arguments.startName = "StartPointTerrain";
        }
    }

    return true;
}

PixelStats bgraPixelStats(const std::vector<uint8_t> &pixels)
{
    PixelStats stats = {};

    for (size_t index = 0; index + 3 < pixels.size(); index += 4)
    {
        const uint8_t blue = pixels[index];
        const uint8_t green = pixels[index + 1];
        const uint8_t red = pixels[index + 2];
        stats.maxRed = std::max(stats.maxRed, red);
        stats.maxGreen = std::max(stats.maxGreen, green);
        stats.maxBlue = std::max(stats.maxBlue, blue);

        if (red > 8 || green > 8 || blue > 8)
        {
            ++stats.litPixels;
        }
    }

    return stats;
}

bool ensureVideoDriver()
{
    SDL_Environment *pEnvironment = SDL_GetEnvironment();
    if (pEnvironment == nullptr)
    {
        return false;
    }

    const char *pConfiguredDriver = SDL_GetEnvironmentVariable(pEnvironment, "SDL_VIDEODRIVER");
    if (pConfiguredDriver == nullptr || pConfiguredDriver[0] == '\0')
    {
        if (std::getenv("DISPLAY") != nullptr || std::getenv("WAYLAND_DISPLAY") != nullptr)
        {
            return true;
        }

        return SDL_SetEnvironmentVariable(pEnvironment, "SDL_VIDEODRIVER", "offscreen", false);
    }

    return true;
}

bool writeScreenshotBmp(
    const std::filesystem::path &path,
    const OpenYAMM::Engine::BgfxContext::ScreenshotCapture &screenshot)
{
    const std::vector<uint8_t> bmp =
        OpenYAMM::Game::SavePreviewImage::encodeBgraToBmp(
            static_cast<int>(screenshot.width),
            static_cast<int>(screenshot.height),
            screenshot.bgraPixels);

    std::ofstream output(path, std::ios::binary);
    if (!output)
    {
        return false;
    }

    output.write(reinterpret_cast<const char *>(bmp.data()), static_cast<std::streamsize>(bmp.size()));
    return static_cast<bool>(output);
}
}

int main(int argc, char **argv)
{
    Arguments arguments = {};
    if (!parseArguments(argc, argv, arguments))
    {
        printUsage();
        return 2;
    }

    OpenYAMM::Game::Mm9DatRuntimeDevEntryRequest request = {};
    request.sourceRoot = arguments.sourceRoot;
    request.mapId = arguments.mapId;
    request.preferredStartName = arguments.startName;

    std::string errorMessage;
    std::optional<OpenYAMM::Game::Mm9DatRuntimeDevEntryResult> entry =
        OpenYAMM::Game::loadMm9DatRuntimeForDevEntry(request, errorMessage);
    if (!entry)
    {
        std::cerr << errorMessage << '\n';
        return 1;
    }

    if (!ensureVideoDriver() || !SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS))
    {
        std::cerr << "SDL_Init failed: " << SDL_GetError() << '\n';
        return 1;
    }

    SDL_Window *pWindow = SDL_CreateWindow(
        "MM9 DAT World Render Smoke",
        SmokeWidth,
        SmokeHeight,
        0);
    if (pWindow == nullptr)
    {
        std::cerr << "SDL_CreateWindow failed: " << SDL_GetError() << '\n';
        SDL_Quit();
        return 1;
    }

    OpenYAMM::Engine::BgfxContext bgfxContext;
    if (!bgfxContext.initialize(pWindow, SmokeWidth, SmokeHeight, false))
    {
        std::cerr << "bgfx initialization failed\n";
        SDL_DestroyWindow(pWindow);
        SDL_Quit();
        return 1;
    }

    PixelStats stats = {};
    OpenYAMM::Game::Mm9DatWorldRuntimeStats runtimeStats = {};
    bgfx::RendererType::Enum rendererType = bgfxContext.getRendererType();

    {
        OpenYAMM::Game::Party party = {};
        OpenYAMM::Game::Mm9DatSceneRuntime sceneRuntime(
            arguments.mapId + ".odm",
            std::move(*entry),
            party,
            9.0f * 60.0f);
        sceneRuntime.worldRuntime().partyRuntimeState().yawRadians = arguments.yawRadians;
        sceneRuntime.worldRuntime().partyRuntimeState().pitchRadians = arguments.pitchRadians;

        OpenYAMM::Game::GameplayInputFrame input = {};
        for (int frameIndex = 0; frameIndex < arguments.warmupFrames; ++frameIndex)
        {
            sceneRuntime.worldRuntime().updateWorld(1.0f / 60.0f);
            sceneRuntime.worldRuntime().renderWorld(SmokeWidth, SmokeHeight, input, 1.0f / 60.0f);
            bgfx::frame();
        }

        const std::string screenshotToken = "mm9_dat_world_render_smoke";
        bgfx::requestScreenShot(BGFX_INVALID_HANDLE, screenshotToken.c_str());
        sceneRuntime.worldRuntime().renderWorld(SmokeWidth, SmokeHeight, input, 1.0f / 60.0f);
        bgfx::frame();
        bgfx::frame();
        bgfx::frame();

        const std::optional<OpenYAMM::Engine::BgfxContext::ScreenshotCapture> screenshot =
            OpenYAMM::Engine::BgfxContext::consumeScreenshot(screenshotToken);
        if (!screenshot)
        {
            std::cerr << "screenshot was unavailable\n";
            bgfxContext.shutdown();
            SDL_DestroyWindow(pWindow);
            SDL_Quit();
            return 1;
        }

        stats = bgraPixelStats(screenshot->bgraPixels);
        if (arguments.requirePixels && stats.litPixels == 0)
        {
            std::cerr << "screenshot was blank\n";
            bgfxContext.shutdown();
            SDL_DestroyWindow(pWindow);
            SDL_Quit();
            return 1;
        }

        if (!writeScreenshotBmp(arguments.outputPath, *screenshot))
        {
            std::cerr << "failed to write screenshot: " << arguments.outputPath.string() << '\n';
            bgfxContext.shutdown();
            SDL_DestroyWindow(pWindow);
            SDL_Quit();
            return 1;
        }

        runtimeStats = sceneRuntime.worldRuntime().datRuntime().stats;
    }

    std::cout << "mm9_dat_world_render_smoke.map_id: " << arguments.mapId << '\n';
    std::cout << "mm9_dat_world_render_smoke.renderer: "
              << bgfx::getRendererName(rendererType) << '\n';
    std::cout << "mm9_dat_world_render_smoke.screenshot: " << arguments.outputPath.string() << '\n';
    std::cout << "mm9_dat_world_render_smoke.lit_pixels: " << stats.litPixels << '\n';
    std::cout << "mm9_dat_world_render_smoke.render_tris: " << runtimeStats.renderTriangleCount << '\n';
    std::cout << "mm9_dat_world_render_smoke.draw_calls: " << runtimeStats.renderDrawCallCount << '\n';
    std::cout << "mm9_dat_world_render_smoke.collision_tris: " << runtimeStats.collisionTriangleCount << '\n';
    std::cout << "mm9_dat_world_render_smoke.active_mechanisms: "
              << runtimeStats.activeMechanismCount << '\n';

    bgfxContext.shutdown();
    SDL_DestroyWindow(pWindow);
    SDL_Quit();
    return 0;
}

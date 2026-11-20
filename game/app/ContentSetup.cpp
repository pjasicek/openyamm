#include "game/app/ContentSetup.h"

#include "engine/AssetPackIndex.h"
#include "game/app/GameUpdater.h"

#include <SDL3/SDL.h>

#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// Logical layout; SDL scales it to the window. Text uses SDL's built-in 8x8 font, so nothing here needs game content.
constexpr int ScreenWidth = 640;
constexpr int ScreenHeight = 360;
constexpr float Margin = 24.0f;
constexpr float GlyphSize = float(SDL_DEBUG_TEXT_FONT_CHARACTER_SIZE);
#if defined(__APPLE__)
constexpr const char *FirstStartText = "The game installs itself and downloads its content on the first start. Your "
                                       "saves and settings stay in ~/Library/Application Support/OpenYAMM.";
#else
constexpr const char *FirstStartText = "The game downloads its content on the first start. Your saves and settings "
                                       "stay in this folder.";
#endif

// What the window says it is doing: the first start of a new installation, or restoring the packs of one that
// lost or changed some.
std::string setupIntro(const std::filesystem::path &assetRoot, const std::string &languageId)
{
    std::string error;
    const std::optional<Engine::AssetPackIndex> index =
        Engine::loadAssetPackIndex(assetRoot / Engine::AssetPackIndexFileName, error);

    if (index && Engine::validateAssetPackFiles(*index, assetRoot / index->store, error))
    {
        return "The game downloads the voices, sounds and videos of the language you chose (" + languageId
            + "). Your saves and settings stay as they are.";
    }

    std::string restoredPack;
    bool anyPackPresent = false;

    for (const Engine::AssetPackRecord &pack : index ? index->packs : std::vector<Engine::AssetPackRecord>())
    {
        if (!pack.language.empty())
        {
            continue;
        }

        std::error_code sizeError;
        const uintmax_t size = std::filesystem::file_size(assetRoot / index->store / pack.file, sizeError);
        anyPackPresent = anyPackPresent || !sizeError;

        if (restoredPack.empty() && (sizeError || size != pack.size))
        {
            restoredPack = pack.file;
        }
    }

    if (!anyPackPresent)
    {
        return FirstStartText;
    }

    return "Some game content is missing or was changed (" + restoredPack + "), so the game downloads it again. "
        "Your saves and settings stay as they are. To change game files, put them into the mods folder.";
}

struct Button
{
    const char *pLabel = nullptr;
    SDL_FRect rect = {};
};

std::vector<std::string> wrapText(const std::string &text, size_t columns)
{
    std::vector<std::string> lines;
    std::string line;
    size_t start = 0;

    while (start < text.size())
    {
        size_t end = text.find(' ', start);
        end = end == std::string::npos ? text.size() : end;
        const std::string word = text.substr(start, end - start);

        if (!line.empty() && line.size() + 1 + word.size() > columns)
        {
            lines.push_back(line);
            line.clear();
        }

        line += (line.empty() ? "" : " ") + word;
        start = end + 1;
    }

    if (!line.empty())
    {
        lines.push_back(line);
    }

    return lines;
}

void drawText(SDL_Renderer *pRenderer, float x, float y, float scale, const std::string &text)
{
    SDL_SetRenderScale(pRenderer, scale, scale);
    SDL_RenderDebugText(pRenderer, x / scale, y / scale, text.c_str());
    SDL_SetRenderScale(pRenderer, 1.0f, 1.0f);
}

std::string megabytes(uint64_t bytes)
{
    return std::to_string((bytes + 999999) / 1000000) + " MB";
}

bool contains(const SDL_FRect &rect, float x, float y)
{
    return x >= rect.x && y >= rect.y && x < rect.x + rect.w && y < rect.y + rect.h;
}

std::vector<Button> buttonsFor(Engine::UpdateState state)
{
    const float width = 128.0f;
    const float height = 32.0f;
    const float y = float(ScreenHeight) - Margin - height;
    const float right = float(ScreenWidth) - Margin;

    if (state == Engine::UpdateState::Failed)
    {
        return {{"Retry", {right - 2.0f * width - 16.0f, y, width, height}},
                {"Quit", {right - width, y, width, height}}};
    }

    return {{state == Engine::UpdateState::Downloading ? "Cancel" : "Quit", {right - width, y, width, height}}};
}
}

bool installedContentMissing(const std::filesystem::path &assetRoot)
{
    std::string error;
    const std::optional<Engine::AssetPackIndex> index =
        Engine::loadAssetPackIndex(assetRoot / Engine::AssetPackIndexFileName, error);
    return index && !Engine::validateAssetPackFiles(*index, assetRoot / index->store, error);
}

bool languageContentMissing(const std::filesystem::path &assetRoot, const std::string &languageId)
{
    std::string error;
    const std::optional<Engine::AssetPackIndex> index =
        Engine::loadAssetPackIndex(assetRoot / Engine::AssetPackIndexFileName, error);
    return index && Engine::missingLanguagePackBytes(*index, assetRoot / index->store, languageId) > 0;
}

bool modifiedContentComplete(const std::filesystem::path &assetRoot)
{
    std::string error;
    const std::optional<Engine::AssetPackIndex> index =
        Engine::loadAssetPackIndex(assetRoot / Engine::AssetPackIndexFileName, error);

    if (!index || Engine::assetPackFilesExist(*index, assetRoot / index->store, error))
    {
        return true;
    }

    const std::string message = "The game cannot start: " + error + ".\n\nsettings.ini has keep_modified_packs=on, "
        "so the game does not download it again. Put the pack back, or set keep_modified_packs=off: the game then "
        "restores it, and also replaces every pack you changed.";
    std::cerr << message << '\n';
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "OpenYAMM", message.c_str(), nullptr);
    return false;
}

ContentSetupResult runContentSetup(const std::string &updateChannelUrl, const std::filesystem::path &assetRoot,
                                   const std::string &languageId)
{
    const std::string intro = setupIntro(assetRoot, languageId);

    std::unique_ptr<GameUpdater> pUpdater = GameUpdater::create(updateChannelUrl, false, languageId);

    // Without the updater a language's packs stay missing and the game plays in English.
    if ((!pUpdater || !pUpdater->updatesInGame()) && !installedContentMissing(assetRoot))
    {
        return ContentSetupResult::Quit;
    }

    if (!pUpdater || !pUpdater->updatesInGame())
    {
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "OpenYAMM",
                                 "The game content is missing, and this installation cannot download it. "
                                 "Download OpenYAMM again from the website.",
                                 nullptr);
        return ContentSetupResult::Quit;
    }

    SDL_Window *pWindow = nullptr;
    SDL_Renderer *pRenderer = nullptr;

    if (!SDL_InitSubSystem(SDL_INIT_VIDEO)
        || !SDL_CreateWindowAndRenderer("OpenYAMM", ScreenWidth * 2, ScreenHeight * 2, SDL_WINDOW_RESIZABLE, &pWindow,
                                        &pRenderer))
    {
        std::cerr << "Content setup: cannot open a window: " << SDL_GetError() << '\n';
        return ContentSetupResult::Quit;
    }

    SDL_SetRenderLogicalPresentation(pRenderer, ScreenWidth, ScreenHeight, SDL_LOGICAL_PRESENTATION_LETTERBOX);
    SDL_SetRenderVSync(pRenderer, 1);
    std::cout << "Content setup: the game content is missing; checking " << updateChannelUrl << '\n';
    pUpdater->check();

    ContentSetupResult result = ContentSetupResult::Quit;
    Engine::UpdateState loggedState = Engine::UpdateState::Idle;
    std::string finishError;
    bool running = true;

    while (running)
    {
        Engine::UpdateStatus status = pUpdater->status();

        if (status.state == Engine::UpdateState::Available)
        {
            // The game cannot start without its content, so the download starts by itself; Cancel stops it.
            pUpdater->startUpdate();
        }
        else if (status.state == Engine::UpdateState::UpToDate)
        {
            // A channel whose release is older than this package offers nothing to complete it.
            status.state = Engine::UpdateState::Failed;
            status.message = "The update server offers no content for OpenYAMM " + pUpdater->installedVersion()
                + ". Download the current release from the website.";
        }
        else if (status.state == Engine::UpdateState::Ready && finishError.empty())
        {
            if (status.contentOnly)
            {
                result = ContentSetupResult::Ready;
                running = false;
            }
            else if (pUpdater->restartIntoUpdate(finishError))
            {
                result = ContentSetupResult::Restarted;
                running = false;
            }
        }

        if (!finishError.empty())
        {
            status.state = Engine::UpdateState::Failed;
            status.message = "OpenYAMM " + status.release + " could not start: " + finishError;
        }

        if (status.state != loggedState)
        {
            std::cout << "Content setup: " << status.message << '\n';
            loggedState = status.state;
        }

        const std::vector<Button> buttons = buttonsFor(status.state);
        SDL_Event event;

        while (SDL_PollEvent(&event))
        {
            SDL_ConvertEventToRenderCoordinates(pRenderer, &event);
            const char *pAction = nullptr;

            if (event.type == SDL_EVENT_QUIT)
            {
                pAction = "Quit";
            }
            else if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_ESCAPE)
            {
                pAction = buttons.back().pLabel;
            }
            else if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_RETURN
                     && status.state == Engine::UpdateState::Failed)
            {
                pAction = "Retry";
            }
            else if (event.type == SDL_EVENT_MOUSE_BUTTON_UP && event.button.button == SDL_BUTTON_LEFT)
            {
                for (const Button &button : buttons)
                {
                    pAction = contains(button.rect, event.button.x, event.button.y) ? button.pLabel : pAction;
                }
            }

            const std::string action = pAction != nullptr ? pAction : "";

            if (action == "Quit")
            {
                pUpdater->cancel();
                running = false;
            }
            else if (action == "Cancel")
            {
                pUpdater->cancel();
            }
            else if (action == "Retry")
            {
                finishError.clear();
                pUpdater->check();
            }
        }

        SDL_SetRenderDrawColor(pRenderer, 10, 10, 13, 255);
        SDL_RenderClear(pRenderer);
        SDL_SetRenderDrawColor(pRenderer, 214, 178, 106, 255);
        drawText(pRenderer, Margin, Margin, 3.0f, "OpenYAMM " + pUpdater->installedVersion());
        SDL_SetRenderDrawColor(pRenderer, 232, 226, 210, 255);
        const size_t columns = size_t((ScreenWidth - 2.0f * Margin) / GlyphSize);
        float y = Margin + 40.0f;

        for (const std::string &line : wrapText(intro, columns))
        {
            drawText(pRenderer, Margin, y, 1.0f, line);
            y += GlyphSize + 6.0f;
        }

        y += 2.0f * GlyphSize;

        for (const std::string &line : wrapText(status.message, columns))
        {
            drawText(pRenderer, Margin, y, 1.0f, line);
            y += GlyphSize + 6.0f;
        }

        if (status.state == Engine::UpdateState::Downloading && status.totalBytes > 0)
        {
            const SDL_FRect frame = {Margin, 200.0f, float(ScreenWidth) - 2.0f * Margin, 20.0f};
            const float done = float(double(status.doneBytes) / double(status.totalBytes));
            const SDL_FRect bar = {frame.x + 2.0f, frame.y + 2.0f, (frame.w - 4.0f) * done, frame.h - 4.0f};
            SDL_SetRenderDrawColor(pRenderer, 120, 98, 58, 255);
            SDL_RenderRect(pRenderer, &frame);
            SDL_SetRenderDrawColor(pRenderer, 214, 178, 106, 255);
            SDL_RenderFillRect(pRenderer, &bar);
            SDL_SetRenderDrawColor(pRenderer, 232, 226, 210, 255);
            drawText(pRenderer, Margin, 232.0f, 1.0f,
                     megabytes(status.doneBytes) + " of " + megabytes(status.totalBytes));
        }

        for (const Button &button : buttons)
        {
            SDL_SetRenderDrawColor(pRenderer, 34, 32, 36, 255);
            SDL_RenderFillRect(pRenderer, &button.rect);
            SDL_SetRenderDrawColor(pRenderer, 214, 178, 106, 255);
            SDL_RenderRect(pRenderer, &button.rect);
            const float textWidth = float(SDL_strlen(button.pLabel)) * GlyphSize;
            drawText(pRenderer, button.rect.x + (button.rect.w - textWidth) * 0.5f,
                     button.rect.y + (button.rect.h - GlyphSize) * 0.5f, 1.0f, button.pLabel);
        }

        SDL_RenderPresent(pRenderer);
        SDL_Delay(16);
    }

    SDL_DestroyRenderer(pRenderer);
    SDL_DestroyWindow(pWindow);
    SDL_QuitSubSystem(SDL_INIT_VIDEO);
    return result;
}
}

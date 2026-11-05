#include "game/ui/screens/LoadGameScreen.h"

#include "engine/Utf8Text.h"
#include "game/content/RulesetDefinition.h"
#include "game/maps/SaveGame.h"
#include "engine/UserDataPaths.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <atomic>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <future>
#include <optional>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{

struct CivilTime
{
    int year = 1168;
    int month = 1;
    int day = 1;
    int dayOfWeek = 1;
    int hour24 = 9;
    int hour12 = 9;
    int minute = 0;
    bool isPm = false;
};

std::string toLowerCopy(const std::string &value)
{
    std::string normalized = value;

    for (char &character : normalized)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return normalized;
}

CivilTime civilTimeFromGameMinutes(float gameMinutes)
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(gameMinutes)));
    const int totalDays = totalMinutes / (24 * 60);
    CivilTime time = {};
    time.year = 1168 + totalDays / (12 * 28);
    time.month = 1 + (totalDays / 28) % 12;
    time.day = 1 + totalDays % 28;
    time.dayOfWeek = 1 + totalDays % 7;
    time.hour24 = (totalMinutes / 60) % 24;
    time.minute = totalMinutes % 60;
    time.isPm = time.hour24 >= 12;
    time.hour12 = time.hour24 % 12;

    if (time.hour12 == 0)
    {
        time.hour12 = 12;
    }

    return time;
}

std::string weekdayName(int dayOfWeek)
{
    static const std::array<const char *, 7> names = {"Monday", "Tuesday",  "Wednesday", "Thursday",
                                                      "Friday", "Saturday", "Sunday"};
    return names[std::clamp(dayOfWeek, 1, 7) - 1];
}

std::string monthName(int month)
{
    static const std::array<const char *, 12> names = {"January",   "February", "March",    "April",
                                                       "May",       "June",     "July",     "August",
                                                       "September", "October",  "November", "December"};
    return names[std::clamp(month, 1, 12) - 1];
}

std::string formatClock(const CivilTime &time)
{
    char buffer[32] = {};
    std::snprintf(buffer, sizeof(buffer), "%s %02d:%02d%s", weekdayName(time.dayOfWeek).c_str(), time.hour12,
                  time.minute, time.isPm ? "PM" : "AM");
    return buffer;
}

std::string formatDate(const CivilTime &time)
{
    char buffer[64] = {};
    std::snprintf(buffer, sizeof(buffer), "%d %s %d", time.day, monthName(time.month).c_str(), time.year);
    return buffer;
}

std::string friendlySaveFileLabel(const std::filesystem::path &path)
{
    const std::string stem = toLowerCopy(path.stem().string());

    if (stem == "autosave")
    {
        return "Autosave";
    }

    if (stem == "quicksave")
    {
        return "Quicksave";
    }

    if (stem.rfind("save", 0) == 0 && stem.size() > 4)
    {
        const std::string suffix = stem.substr(4);
        const bool allDigits = std::all_of(suffix.begin(), suffix.end(), [](char character)
                                           { return std::isdigit(static_cast<unsigned char>(character)) != 0; });

        if (allDigits)
        {
            return "Save " + std::to_string(std::max(1, std::stoi(suffix)));
        }
    }

    std::string label = path.stem().string();

    if (!label.empty())
    {
        label[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(label[0])));
    }

    return label;
}

bool decodeBmpBytesToBgra(const std::vector<uint8_t> &bmpBytes, int &width, int &height, std::vector<uint8_t> &pixels)
{
    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bmpBytes.data(), bmpBytes.size());

    if (pIoStream == nullptr)
    {
        return false;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return false;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return false;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height) * 4;
    pixels.resize(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);
    SDL_DestroySurface(pConvertedSurface);
    return true;
}

// The saves folder's save files by name, size and time, so a list read earlier can tell it is out of date (saves
// copied in from outside, or written by another game).
uint64_t saveFolderSignature()
{
    uint64_t signature = 14695981039346656037ull;
    const auto mix = [&signature](uint64_t value)
    {
        signature = (signature ^ value) * 1099511628211ull;
    };
    std::error_code error;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator("saves", error))
    {
        if (!entry.is_regular_file(error) || toLowerCopy(entry.path().extension().string()) != ".oysav")
        {
            continue;
        }

        mix(std::hash<std::string>{}(entry.path().filename().string()));
        mix(entry.file_size(error));
        mix(uint64_t(entry.last_write_time(error).time_since_epoch().count()));
    }

    return signature;
}

// A save file as the list read it, kept while the file's size and time are unchanged.
struct ScannedSave
{
    std::filesystem::path path;
    uintmax_t fileSize = 0;
    std::optional<std::filesystem::file_time_type> modified;
    std::optional<GameSaveSummary> summary;
    bool newerVersion = false;
    int previewWidth = 0;
    int previewHeight = 0;
    std::vector<uint8_t> previewPixelsBgra;
};

// Set while LoadGameScreen::stopSaveScan waits for the worker; the scan stops at its next save.
std::atomic<bool> g_saveScanStopping = false;

// The saves folder's save files, reading only those that are not in `known` at the same size and time. It touches
// nothing but the files, so it runs on any thread.
std::vector<ScannedSave> scanSaves(std::vector<ScannedSave> known)
{
    std::unordered_map<std::string, size_t> knownIndices;

    for (size_t index = 0; index < known.size(); ++index)
    {
        knownIndices.emplace(known[index].path.string(), index);
    }

    std::vector<ScannedSave> scanned;
    std::error_code error;
    std::filesystem::create_directories("saves", error);

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator("saves", error))
    {
        if (g_saveScanStopping)
        {
            break;
        }

        std::error_code entryError;

        if (!entry.is_regular_file(entryError) || toLowerCopy(entry.path().extension().string()) != ".oysav")
        {
            continue;
        }

        ScannedSave save;
        save.path = entry.path();
        save.fileSize = entry.file_size(entryError);
        const std::filesystem::file_time_type modified = entry.last_write_time(entryError);

        if (!entryError)
        {
            save.modified = modified;
        }

        const auto knownIndex = knownIndices.find(save.path.string());

        if (knownIndex != knownIndices.end() && known[knownIndex->second].fileSize == save.fileSize
            && known[knownIndex->second].modified == save.modified)
        {
            scanned.push_back(std::move(known[knownIndex->second]));
            continue;
        }

        std::string loadError;
        save.summary = loadGameSaveSummaryFromPath(save.path, loadError);
        save.newerVersion = !save.summary && loadError == SaveFromNewerVersionError;

        if (save.summary && !save.summary->previewBmp.empty())
        {
            decodeBmpBytesToBgra(save.summary->previewBmp, save.previewWidth, save.previewHeight,
                save.previewPixelsBgra);
            save.summary->previewBmp = std::vector<uint8_t>();
        }

        scanned.push_back(std::move(save));
    }

    return scanned;
}

// Every list of the session reads from these: a save is read once, and again only after it changes.
std::vector<ScannedSave> g_scannedSaves;
// The first read of the folder, on a worker thread (LoadGameScreen::startSaveScan): saves older than
// SaveVersionSummaryFirst are read whole, which takes seconds for a folder of late saves.
std::future<std::vector<ScannedSave>> g_pendingSaveScan;

} // namespace

LoadGameScreen::LoadGameScreen(const Engine::AssetFileSystem &assetFileSystem, const GameDataRepository &gameData,
                               LoadAction loadAction, CancelAction cancelAction, bool fromGameplay,
                               GameAudioSystem *pAudio, std::string loadWarning)
    : MenuDesignScreen(assetFileSystem, fromGameplay, pAudio), m_pGameData(&gameData),
      m_loadAction(std::move(loadAction)), m_cancelAction(std::move(cancelAction)), m_fromGameplay(fromGameplay),
      m_loadWarning(std::move(loadWarning))
{
}

void LoadGameScreen::startSaveScan()
{
    if (!g_pendingSaveScan.valid())
    {
        g_pendingSaveScan = std::async(std::launch::async, scanSaves, std::move(g_scannedSaves));
    }
}

void LoadGameScreen::stopSaveScan()
{
    if (g_pendingSaveScan.valid())
    {
        g_saveScanStopping = true;
        g_pendingSaveScan.wait();
        g_pendingSaveScan = {};
        g_saveScanStopping = false;
    }

    g_scannedSaves.clear();
}

AppMode LoadGameScreen::mode() const
{
    return AppMode::LoadMenu;
}

void LoadGameScreen::prepareForFirstFrame()
{
    loadDesign("gameplay/load_game");
    preloadLayoutAssets(m_designLayouts);
    startSaveScan();
}

void LoadGameScreen::onEnter()
{
    // The folder may have changed since the list was read: saves copied in, or written by another game.
    if (!m_slotsLoaded || m_slotsSignature != saveFolderSignature())
    {
        refreshSaveSlots();
    }
}

void LoadGameScreen::configureSave(SaveAction action, const std::string &location, float gameMinutes,
                                   const std::vector<uint8_t> &previewBmp, SaveFoodCost foodCost)
{
    m_saveAction = std::move(action);
    m_foodCost = foodCost;
    m_currentLocation = location;
    m_saveName = location;
    const CivilTime time = civilTimeFromGameMinutes(gameMinutes);
    m_currentDate = formatDate(time);
    m_currentClock = formatClock(time);
    if (!previewBmp.empty())
    {
        decodeBmpBytesToBgra(previewBmp, m_previewWidth, m_previewHeight, m_previewPixels);
    }
    setTextEditing(true);
    m_nameEditing = true;
}

void LoadGameScreen::handleSdlEvent(const SDL_Event &event)
{
    if (!m_saveAction || !m_nameEditing || modalOpen())
    {
        return;
    }
    if (event.type == SDL_EVENT_TEXT_INPUT)
    {
        Engine::Utf8::appendPrintable(m_saveName, event.text.text != nullptr ? event.text.text : "", 40);
    }
    if (event.type == SDL_EVENT_KEY_DOWN && event.key.scancode == SDL_SCANCODE_BACKSPACE && !m_saveName.empty())
    {
        Engine::Utf8::popBack(m_saveName);
    }
    if (event.type == SDL_EVENT_KEY_DOWN && event.key.scancode == SDL_SCANCODE_RETURN && !event.key.repeat)
    {
        m_commitRequested = true;
        m_nameEditing = false;
        setTextEditing(false);
    }
}

std::optional<std::filesystem::path> LoadGameScreen::mostRecentSave(std::string &mapFileName)
{
    mapFileName.clear();
    std::error_code error;
    std::vector<std::filesystem::directory_entry> entries;
    for (const auto &entry : std::filesystem::directory_iterator("saves", error))
    {
        if (entry.is_regular_file(error) && toLowerCopy(entry.path().extension().string()) == ".oysav")
        {
            entries.push_back(entry);
        }
    }
    std::sort(entries.begin(), entries.end(),
              [](const auto &left, const auto &right)
              {
                  std::error_code firstError, secondError;
                  return left.last_write_time(firstError) > right.last_write_time(secondError);
              });
    for (const auto &entry : entries)
    {
        std::string message;
        if (const std::optional<GameSaveSummary> summary = loadGameSaveSummaryFromPath(entry.path(), message))
        {
            mapFileName = summary->mapFileName;
            return entry.path();
        }
    }
    return std::nullopt;
}

void LoadGameScreen::requestLoad()
{
    if (m_slots.empty())
    {
        return;
    }
    const auto load = [this]()
    {
        if (!tryLoadSelectedSlot())
        {
            m_error = "Unable to load this save. Check its required content packages.";
        }
    };
    if (m_fromGameplay)
    {
        confirm("Load Adventure?",
                m_loadWarning.empty() ? "Unsaved progress in the current adventure will be lost." : m_loadWarning,
                {"Cancel", "Load"},
                [load](int choice)
                {
                    if (choice == 1)
                    {
                        load();
                    }
                });
    }
    else
    {
        load();
    }
}

void LoadGameScreen::commitSave()
{
    const size_t first = m_saveName.find_first_not_of(" \t");
    const size_t last = m_saveName.find_last_not_of(" \t");
    const std::string name = first == std::string::npos ? "" : m_saveName.substr(first, last - first + 1);
    const std::string lower = toLowerCopy(name);
    if (name.empty() || lower == "autosave" || lower == "quicksave")
    {
        m_error = "Choose a name other than Autosave or Quicksave.";
        return;
    }
    std::filesystem::path path;
    if (!m_newSave && m_selectedIndex < m_slots.size())
    {
        path = m_slots[m_selectedIndex].path;
    }
    else
    {
        for (size_t index = 1;; ++index)
        {
            path = std::filesystem::path("saves") / ("save" + std::to_string(index) + ".oysav");
            if (!std::filesystem::exists(path))
            {
                break;
            }
        }
    }
    for (const SaveSlotSummary &slot : m_slots)
    {
        if (toLowerCopy(slot.fileLabel) == lower && slot.path != path)
        {
            m_error = "A save already uses that name. Select it to replace it.";
            return;
        }
    }
    const auto save = [this, path, name]()
    {
        if (!m_saveAction(path, name))
        {
            m_error = "Saving failed or is not allowed in this location.";
        }
    };
    if (!m_newSave)
    {
        confirm("Replace Saved Adventure?", "Replace " + m_slots[m_selectedIndex].fileLabel + "?",
                {"Cancel", "Replace"},
                [save](int choice)
                {
                    if (choice == 1)
                    {
                        save();
                    }
                });
    }
    else
    {
        save();
    }
}

void LoadGameScreen::requestImportSaves()
{
    m_error.clear();
    m_folderPick = std::make_shared<FolderPick>();
    SDL_ShowOpenFolderDialog(
        [](void *pUserData, const char *const *pFileList, int)
        {
            std::unique_ptr<std::shared_ptr<FolderPick>> pPick(static_cast<std::shared_ptr<FolderPick> *>(pUserData));
            std::lock_guard lock((*pPick)->mutex);
            if (pFileList != nullptr && pFileList[0] != nullptr)
            {
                (*pPick)->folder = std::filesystem::path(pFileList[0]);
            }
            (*pPick)->finished = true;
        },
        new std::shared_ptr<FolderPick>(m_folderPick), nullptr, nullptr, false);
}

void LoadGameScreen::finishImportSaves()
{
    if (m_folderPick == nullptr)
    {
        return;
    }

    std::optional<std::filesystem::path> folder;
    {
        std::lock_guard lock(m_folderPick->mutex);
        if (!m_folderPick->finished)
        {
            return;
        }
        folder = m_folderPick->folder;
    }
    m_folderPick.reset();

    if (!folder)
    {
        return;
    }

    const Engine::SaveImportResult result = Engine::importSaveFiles(*folder, "saves");
    refreshSaveSlots();
    m_revealSelection = true;

    std::string body = result.imported == 1 ? "Imported 1 save." : "Imported " + std::to_string(result.imported)
                                                                    + " saves.";
    if (result.imported == 0 && result.skipped == 0 && result.failed == 0)
    {
        body = "No saves were found in that folder or in a \"saves\" folder inside it.";
    }
    if (result.skipped > 0)
    {
        body += "\n" + std::to_string(result.skipped) + " skipped: a save with the same name already exists.";
    }
    if (result.failed > 0)
    {
        body += "\n" + std::to_string(result.failed) + " could not be copied.";
    }
    confirm("Import Saves", body, {"OK"}, [](int) {});
}

void LoadGameScreen::requestDelete()
{
    if (m_newSave || m_selectedIndex >= m_slots.size())
    {
        return;
    }

    const SaveSlotSummary &slot = m_slots[m_selectedIndex];
    const std::filesystem::path path = slot.path;
    m_commitRequested = false;
    m_nameEditing = false;
    setTextEditing(false);
    m_error.clear();
    confirm("Delete Save?", "Permanently delete \"" + slot.fileLabel + "\"?", {"Cancel", "Delete"},
            [this, path](int choice)
            {
                if (choice != 1)
                {
                    return;
                }

                std::error_code error;
                if (!std::filesystem::remove(path, error))
                {
                    m_error = error ? "Unable to delete this save: " + error.message() : "This save no longer exists.";
                    return;
                }

                refreshSaveSlots();
                if (m_saveAction)
                {
                    m_saveName = m_currentLocation;
                }
                m_revealSelection = true;
            });
}

void LoadGameScreen::drawScreen(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);
    const bool saving = bool(m_saveAction);
    const bool saveAffordable = m_foodCost.food <= m_foodCost.carried;
    const std::string prefix = saving ? "SaveGame" : "LoadGame";
    loadDesign(saving ? "gameplay/save_game" : "gameplay/load_game");
    beginDesign(prefix);
    drawDesign();
    if (!modalOpen() && keyPressed(SDL_SCANCODE_ESCAPE))
    {
        cancel();
        return;
    }
    if (drawSortButtons(prefix))
    {
        m_scrollOffset = 0;
        m_revealSelection = true;
    }
    if (drawRulesetFilters(prefix))
    {
        m_scrollOffset = 0;
        m_revealSelection = true;
        if (saving)
        {
            m_newSave = true;
            m_saveName = m_currentLocation;
        }
    }
    // Rows of the list: the new-save row when saving, then the shown slots.
    const std::vector<size_t> shown = shownSlots();
    const size_t firstSlotRow = saving ? 1 : 0;
    std::optional<size_t> selectedSlotRow;
    for (size_t row = 0; row < shown.size(); ++row)
    {
        if (shown[row] == m_selectedIndex)
        {
            selectedSlotRow = row;
        }
    }
    if (!selectedSlotRow && !shown.empty())
    {
        m_selectedIndex = shown.front();
        selectedSlotRow = 0;
    }
    if (saving && !selectedSlotRow)
    {
        m_newSave = true;
    }
    const Rect viewport = designRect(prefix + "ListViewport");
    const size_t total = shown.size() + firstSlotRow;
    const float unit = designScale();
    const Rect firstRow = designRect(prefix + "SlotRow0");
    const float rowPitch = firstRow.height / unit + 3.2f;
    const int visibleRows = std::max(1, int(viewport.height / (rowPitch * unit)));
    const float contentHeight = total > 0 ? total * rowPitch - 3.2f : 0;
    if (saving && m_nameEditing &&
        (keyPressed(SDL_SCANCODE_TAB) || (leftMouseJustPressed() && !pointerInside(designRect(prefix + "NameField")))))
    {
        m_nameEditing = false;
        setTextEditing(false);
    }
    if (!modalOpen() && !m_nameEditing && total > 0)
    {
        const int delta = int(keyPressed(SDL_SCANCODE_DOWN)) - int(keyPressed(SDL_SCANCODE_UP)) +
                          visibleRows * (int(keyPressed(SDL_SCANCODE_PAGEDOWN)) - int(keyPressed(SDL_SCANCODE_PAGEUP)));
        if (delta != 0)
        {
            const int current = saving && m_newSave ? 0 : int(selectedSlotRow.value_or(0) + firstSlotRow);
            const size_t selected = size_t(std::clamp(current + delta, 0, int(total) - 1));
            m_newSave = saving && selected == 0;
            if (!m_newSave)
            {
                selectedSlotRow = selected - firstSlotRow;
                m_selectedIndex = shown[*selectedSlotRow];
            }
            if (saving)
            {
                m_saveName = m_newSave ? m_currentLocation : m_slots[m_selectedIndex].fileLabel;
            }
            m_revealSelection = true;
        }
    }
    if (m_revealSelection)
    {
        const size_t selected = saving && m_newSave ? 0 : selectedSlotRow.value_or(0) + firstSlotRow;
        const float top = selected * rowPitch;
        m_scrollOffset = std::clamp(m_scrollOffset, top + firstRow.height / unit - viewport.height / unit, top);
        m_revealSelection = false;
    }
    scrollViewport(viewport, contentHeight, m_scrollOffset, rowPitch);
    setDesignClip(viewport);
    const size_t firstIndex = size_t(m_scrollOffset / rowPitch);
    for (size_t index = firstIndex; index < total; ++index)
    {
        const bool newRow = saving && index == 0;
        const size_t slotIndex = newRow ? 0 : shown[index - firstSlotRow];
        const SaveSlotSummary *pSlot = newRow ? nullptr : &m_slots[slotIndex];
        const std::string id = prefix + "SlotRow" + std::to_string(index);
        Rect rect = firstRow;
        const float offset = index * rowPitch - m_scrollOffset;
        rect.y += offset * unit;
        if (rect.y >= viewport.y + viewport.height)
        {
            break;
        }
        if (button(id, rect, "", "save_row", true, newRow ? m_newSave : !m_newSave && slotIndex == m_selectedIndex))
        {
            m_newSave = newRow;
            if (newRow)
            {
                m_saveName = m_currentLocation;
            }
            else
            {
                m_selectedIndex = slotIndex;
                if (saving)
                {
                    m_saveName = pSlot->fileLabel;
                }
                if (!saving && m_lastClickedSlotIndex == slotIndex && SDL_GetTicks() - m_lastClickedSlotTicks < 500)
                {
                    requestLoad();
                }
                m_lastClickedSlotIndex = slotIndex;
                m_lastClickedSlotTicks = SDL_GetTicks();
            }
        }
        if (newRow)
        {
            textInRect({rect.x + 10 * unit, rect.y + 4 * unit, rect.width - 20 * unit, 22 * unit}, "Create a new save",
                       "menu_arrus", 15.36f);
        }
        else
        {
            label(prefix + "SlotRow0Name", pSlot->fileLabel, 0, offset);
            label(prefix + "SlotRow0Location", pSlot->locationName, 0, offset);
        }
    }
    setDesignClip(std::nullopt);
    const SaveSlotSummary *pSlot = !m_newSave && selectedSlotRow ? &m_slots[m_selectedIndex] : nullptr;
    if (pSlot || saving)
    {
        const std::string kind = !pSlot                              ? "New save"
                                 : pSlot->path.stem() == "autosave"  ? "Automatic"
                                 : pSlot->path.stem() == "quicksave" ? "Quick"
                                                                     : "Manual";
        const std::string worldAndKind =
            pSlot && !pSlot->worldName.empty() ? pSlot->worldName + " - " + kind : kind;
        label(prefix + "SelectedWorldAndKind", worldAndKind);
        label(prefix + "SelectedName", pSlot ? pSlot->locationName : m_currentLocation);
        const Rect preview = designRect(prefix + "PreviewRect");
        const auto drawPreview =
            [this, &preview](const std::string &key, int width, int height, const std::vector<uint8_t> &pixels)
        {
            const float scale = std::max(preview.width / width, preview.height / height);
            const Rect imageRect = {preview.x + (preview.width - width * scale) / 2,
                                    preview.y + (preview.height - height * scale) / 2, width * scale, height * scale};
            setDesignClip(preview);
            drawPixelsBgra(key, width, height, pixels, imageRect);
            setDesignClip(std::nullopt);
        };
        if (saving && m_newSave && !m_previewPixels.empty())
        {
            drawPreview("menu_current_save", m_previewWidth, m_previewHeight, m_previewPixels);
        }
        else if (pSlot && !pSlot->previewPixelsBgra.empty())
        {
            drawPreview("menu_save:" + pSlot->path.string(), pSlot->previewWidth, pSlot->previewHeight,
                        pSlot->previewPixelsBgra);
        }
        else
        {
            drawSolidRect(preview, 0xff121a14u);
            textInRect(preview, "No screenshot available", "menu_lucida", 12, 0xff9bb6c2u, true);
        }
        label(prefix + "PreviewLine1", pSlot ? pSlot->dateText : m_currentDate);
        label(prefix + "PreviewLine2", pSlot ? pSlot->weekdayClockText : m_currentClock);
        if (saving)
        {
            const Rect field = designRect(prefix + "NameField");
            if (button("save-name", field, "", "text_field") || (keyPressed(SDL_SCANCODE_TAB) && focused("save-name")))
            {
                m_nameEditing = true;
                setTextEditing(true);
            }
            label(prefix + "NameField", m_saveName + (m_nameEditing ? "_" : ""));
            if (m_foodCost.food > 0 || m_foodCost.foodWithEnemiesNear > 0)
            {
                std::string text = m_foodCost.food > 0 ? "Saving here costs " + std::to_string(m_foodCost.food) +
                                                             " food, you carry " + std::to_string(m_foodCost.carried)
                                                       : std::string("Saving here is free now");
                if (m_foodCost.foodWithEnemiesNear > m_foodCost.food)
                {
                    text += "\nWith enemies near: " + std::to_string(m_foodCost.foodWithEnemiesNear) + " food";
                }
                label(prefix + "FoodCost", text, saveAffordable ? 0 : 0xff5c5ce0u);
            }
        }
        else
        {
            label(prefix + "SelectedMetadata", pSlot->fileLabel + "\nSaved " + pSlot->savedAt);
            label(prefix + "SelectedRuleset", pSlot->rulesetBadge);
        }
    }
    else
    {
        const std::string text = m_slots.empty() ? "No saved games\nStart a new game from the main menu."
                                                 : "No saved games with this ruleset";
        textInRect(viewport, text, "menu_arrus", 15, 0xffc6dfeau, true);
    }
    if (action(prefix + "CancelButton"))
    {
        cancel();
        return;
    }
    if (action(prefix + "DeleteButton", pSlot != nullptr))
    {
        requestDelete();
    }
#if !defined(__ANDROID__) && !defined(OPENYAMM_IOS)
    // Phones pick no folders here; on iOS, Finder and the Files app reach the saves in the app's Documents folder.
    if (!saving)
    {
        if (action(prefix + "ImportButton", m_folderPick == nullptr))
        {
            requestImportSaves();
        }
        if (action(prefix + "OpenFolderButton"))
        {
            std::error_code error;
            SDL_OpenURL(Engine::folderUrl(std::filesystem::current_path(error)).c_str());
        }
        finishImportSaves();
    }
#endif
    if (action(prefix + "ConfirmButton", saving ? !m_saveName.empty() && saveAffordable : pSlot != nullptr) ||
        m_commitRequested)
    {
        m_commitRequested = false;
        if (saving && !saveAffordable)
        {
            m_error = "Not enough food: saving here costs " + std::to_string(m_foodCost.food) + ".";
        }
        else if (saving)
        {
            commitSave();
        }
        else
        {
            requestLoad();
        }
    }
    if (!m_error.empty())
    {
        textInRect(canvasRect(438.4f, 372, 323.2f, 28), m_error, "menu_lucida", 10.5f);
    }
    else if (m_newerSaveCount > 0)
    {
        textInRect(canvasRect(438.4f, 372, 323.2f, 28),
                   std::to_string(m_newerSaveCount) + (m_newerSaveCount == 1 ? " save needs" : " saves need")
                       + " a newer version of OpenYAMM and is not listed.",
                   "menu_lucida", 10.5f);
    }
    drawConfirmation();
}

void LoadGameScreen::refreshSaveSlots()
{
    m_slots.clear();
    m_slotsLoaded = false;
    m_newerSaveCount = 0;

    // The scan started with the menu has read most of the folder; this one reads only what changed since.
    if (g_pendingSaveScan.valid())
    {
        g_scannedSaves = g_pendingSaveScan.get();
    }

    g_scannedSaves = scanSaves(std::move(g_scannedSaves));
    m_slotsSignature = saveFolderSignature();
    std::unordered_map<std::string, std::string> rulesetNames;

    for (const ScannedSave &save : g_scannedSaves)
    {
        if (m_saveAction && (toLowerCopy(save.path.stem().string()) == "autosave" ||
                             toLowerCopy(save.path.stem().string()) == "quicksave"))
        {
            continue;
        }

        if (!save.summary)
        {
            if (save.newerVersion)
            {
                ++m_newerSaveCount;
            }
            continue;
        }

        const GameSaveSummary &summary = *save.summary;
        SaveSlotSummary slot = {};
        slot.path = save.path;
        slot.fileLabel = !summary.saveName.empty() ? summary.saveName : friendlySaveFileLabel(save.path);
        slot.locationName = summary.mapFileName;
        slot.populated = true;
        slot.rulesetId = summary.ruleset.id;

        if (!summary.ruleset.isStandard())
        {
            auto rulesetName = rulesetNames.find(summary.ruleset.id);

            if (rulesetName == rulesetNames.end())
            {
                std::string rulesetError;
                const std::optional<RulesetDefinition> ruleset =
                    loadRulesetDefinition(assetFileSystem(), summary.ruleset.id, rulesetError);
                rulesetName = rulesetNames.emplace(
                    summary.ruleset.id,
                    ruleset ? ruleset->name : summary.ruleset.id + " (not installed)").first;
            }

            slot.rulesetBadge = describeRulesetSelection(summary.ruleset, rulesetName->second);
        }

        const CivilTime civilTime = civilTimeFromGameMinutes(summary.savedGameMinutes);
        slot.weekdayClockText = formatClock(civilTime);
        slot.dateText = formatDate(civilTime);
        if (save.modified)
        {
            slot.modified = *save.modified;
            const std::time_t timestamp =
                std::chrono::system_clock::to_time_t(
                    std::chrono::time_point_cast<std::chrono::system_clock::duration>(
                        std::chrono::file_clock::to_sys(*save.modified)));
            if (const std::tm *pLocal = std::localtime(&timestamp))
            {
                std::ostringstream formatted;
                formatted << std::put_time(pLocal, "%Y-%m-%d %H:%M");
                slot.savedAt = formatted.str();
            }
        }

        if (m_pGameData != nullptr)
        {
            for (const MapStatsEntry &entryMap : m_pGameData->mapEntries())
            {
                if (toLowerCopy(entryMap.canonicalId) == toLowerCopy(summary.mapFileName) ||
                    toLowerCopy(entryMap.fileName) == toLowerCopy(summary.mapFileName))
                {
                    slot.locationName = entryMap.name;
                    slot.worldName = entryMap.worldId;
                    for (const MergedCharacterSelectionContinent &continent :
                         m_pGameData->mergedCharacterSelectionTable().continents())
                    {
                        if (continent.id == entryMap.mergedContinentId)
                        {
                            slot.worldName = continent.name;
                            break;
                        }
                    }
                    break;
                }
            }
        }

        slot.previewWidth = save.previewWidth;
        slot.previewHeight = save.previewHeight;
        slot.previewPixelsBgra = save.previewPixelsBgra;
        m_slots.push_back(std::move(slot));
    }

    sortSlots();

    if (m_selectedIndex >= m_slots.size())
    {
        m_selectedIndex = 0;
    }

    m_scrollOffset = 0;
    m_lastClickedSlotIndex = static_cast<size_t>(-1);
    m_lastClickedSlotTicks = 0;
    m_newSave = bool(m_saveAction);
    m_slotsLoaded = true;
    refreshRulesetFilters();
}

void LoadGameScreen::refreshRulesetFilters()
{
    // Only the rulesets the saves were played with, so a player who never started a game of another ruleset sees no
    // filter (audit STD2-M2). Their names are read from the ruleset packages once, when a second ruleset appears.
    static std::unordered_map<std::string, std::string> s_rulesetNames;
    m_rulesetFilters.clear();

    for (const SaveSlotSummary &slot : m_slots)
    {
        const bool listed = std::any_of(m_rulesetFilters.begin(), m_rulesetFilters.end(),
                                        [&slot](const RulesetFilter &filter) { return filter.id == slot.rulesetId; });

        if (!listed)
        {
            m_rulesetFilters.push_back({slot.rulesetId, slot.rulesetId});
        }
    }

    if (m_rulesetFilters.size() >= 2 && s_rulesetNames.empty())
    {
        std::vector<RulesetDefinition> rulesets;
        std::string error;
        loadAvailableRulesets(assetFileSystem(), rulesets, error);

        for (const RulesetDefinition &ruleset : rulesets)
        {
            s_rulesetNames[ruleset.id] = ruleset.isStandard() ? "Standard" : ruleset.name;
        }
    }

    for (RulesetFilter &filter : m_rulesetFilters)
    {
        const auto name = s_rulesetNames.find(filter.id);
        filter.name = name != s_rulesetNames.end() ? name->second : filter.id;
    }

    std::stable_sort(m_rulesetFilters.begin(), m_rulesetFilters.end(),
        [](const RulesetFilter &left, const RulesetFilter &right)
        {
            return (left.id == StandardRulesetId) != (right.id == StandardRulesetId)
                ? left.id == StandardRulesetId
                : left.id < right.id;
        });

    const bool filterListed =
        std::any_of(m_rulesetFilters.begin(), m_rulesetFilters.end(),
                    [this](const RulesetFilter &filter) { return filter.id == m_rulesetFilter; });

    if (!filterListed)
    {
        m_rulesetFilter.clear();
    }
}

std::vector<size_t> LoadGameScreen::shownSlots() const
{
    std::vector<size_t> shown;

    for (size_t index = 0; index < m_slots.size(); ++index)
    {
        if (m_rulesetFilter.empty() || m_slots[index].rulesetId == m_rulesetFilter)
        {
            shown.push_back(index);
        }
    }

    return shown;
}

bool LoadGameScreen::drawRulesetFilters(const std::string &prefix)
{
    if (m_rulesetFilters.size() < 2)
    {
        return false;
    }

    const Rect area = designRect(prefix + "RulesetFilters");
    const float unit = designScale();
    const float gap = 6 * unit;
    const size_t count = m_rulesetFilters.size() + 1;
    const float width = std::min(96 * unit, (area.width - gap * float(count - 1)) / float(count));
    bool changed = false;

    for (size_t index = 0; index < count; ++index)
    {
        const std::string id = index == 0 ? std::string() : m_rulesetFilters[index - 1].id;
        const std::string text = index == 0 ? "All" : m_rulesetFilters[index - 1].name;
        const Rect rect = {area.x + area.width - float(count - index) * (width + gap) + gap, area.y, width,
                           area.height};

        if (button(prefix + "RulesetFilter" + std::to_string(index), rect, text, "tab", true, id == m_rulesetFilter)
            && id != m_rulesetFilter)
        {
            m_rulesetFilter = id;
            changed = true;
        }
    }

    return changed;
}

void LoadGameScreen::configureSortOrder(bool newestFirst, SortOrderAction changed)
{
    m_newestFirst = newestFirst;
    m_sortOrderChanged = std::move(changed);
    sortSlots();
}

void LoadGameScreen::sortSlots()
{
    std::stable_sort(m_slots.begin(), m_slots.end(), [this](const SaveSlotSummary &left, const SaveSlotSummary &right)
        {
            if (m_newestFirst && left.modified != right.modified)
            {
                return left.modified > right.modified;
            }
            return compareSavesForDisplay(left.path, left.fileLabel, right.path, right.fileLabel);
        });
}

bool LoadGameScreen::drawSortButtons(const std::string &prefix)
{
    const Rect area = designRect(prefix + "SortButtons");
    const float gap = 6 * designScale();
    const float width = (area.width - gap) / 2;
    bool newestFirst = m_newestFirst;

    if (button(prefix + "SortByName", {area.x, area.y, width, area.height}, "Name", "tab", true, !m_newestFirst))
    {
        newestFirst = false;
    }

    if (button(prefix + "SortByNewest", {area.x + width + gap, area.y, width, area.height}, "Newest", "tab", true,
            m_newestFirst))
    {
        newestFirst = true;
    }

    if (newestFirst == m_newestFirst)
    {
        return false;
    }

    // The selected save stays selected in the new order.
    const std::optional<std::filesystem::path> selected = m_selectedIndex < m_slots.size()
        ? std::optional<std::filesystem::path>(m_slots[m_selectedIndex].path) : std::nullopt;
    m_newestFirst = newestFirst;
    sortSlots();

    for (size_t index = 0; selected && index < m_slots.size(); ++index)
    {
        if (m_slots[index].path == *selected)
        {
            m_selectedIndex = index;
        }
    }

    if (m_sortOrderChanged)
    {
        m_sortOrderChanged(m_newestFirst);
    }

    return true;
}

bool LoadGameScreen::tryLoadSelectedSlot()
{
    if (m_slots.empty() || m_selectedIndex >= m_slots.size() || !m_loadAction)
    {
        return false;
    }

    return m_loadAction(m_slots[m_selectedIndex].path);
}

void LoadGameScreen::cancel()
{
    if (m_cancelAction)
    {
        m_cancelAction();
    }
}
} // namespace OpenYAMM::Game

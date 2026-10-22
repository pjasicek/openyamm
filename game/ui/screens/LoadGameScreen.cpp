#include "game/ui/screens/LoadGameScreen.h"

#include "game/maps/SaveGame.h"
#include "engine/UserDataPaths.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <optional>
#include <string_view>
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

} // namespace

LoadGameScreen::LoadGameScreen(const Engine::AssetFileSystem &assetFileSystem, const GameDataRepository &gameData,
                               LoadAction loadAction, CancelAction cancelAction, bool fromGameplay,
                               GameAudioSystem *pAudio)
    : MenuDesignScreen(assetFileSystem, fromGameplay, pAudio), m_pGameData(&gameData),
      m_loadAction(std::move(loadAction)), m_cancelAction(std::move(cancelAction)), m_fromGameplay(fromGameplay)
{
}

std::vector<LoadGameScreen::SaveSlotSummary> LoadGameScreen::s_cachedSlots;
bool LoadGameScreen::s_cachedSlotsValid = false;
size_t LoadGameScreen::s_cachedNewerSaveCount = 0;

void LoadGameScreen::invalidateCachedSaveSlots()
{
    s_cachedSlots.clear();
    s_cachedSlotsValid = false;
}

AppMode LoadGameScreen::mode() const
{
    return AppMode::LoadMenu;
}

void LoadGameScreen::prepareForFirstFrame()
{
    loadDesign("gameplay/load_game");
    preloadLayoutAssets(m_designLayouts);

    if (s_cachedSlotsValid && !m_saveAction)
    {
        loadCachedSaveSlots();
    }
    else
    {
        refreshSaveSlots();
    }
}

void LoadGameScreen::onEnter()
{
    if (!m_slotsLoaded)
    {
        if (s_cachedSlotsValid && !m_saveAction)
        {
            loadCachedSaveSlots();
        }
        else
        {
            refreshSaveSlots();
        }
    }
}

void LoadGameScreen::configureSave(SaveAction action, const std::string &location, float gameMinutes,
                                   const std::vector<uint8_t> &previewBmp)
{
    m_saveAction = std::move(action);
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
        for (const unsigned char character : std::string(event.text.text))
        {
            if (character >= 32 && character < 127 && m_saveName.size() < 40)
            {
                m_saveName += char(character);
            }
        }
    }
    if (event.type == SDL_EVENT_KEY_DOWN && event.key.scancode == SDL_SCANCODE_BACKSPACE && !m_saveName.empty())
    {
        m_saveName.pop_back();
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
        if (const std::optional<GameSaveData> data = loadGameDataFromPath(entry.path(), message))
        {
            mapFileName = data->mapFileName;
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
        confirm("Load Adventure?", "Unsaved progress in the current adventure will be lost.", {"Cancel", "Load"},
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
        if (m_saveAction(path, name))
        {
            invalidateCachedSaveSlots();
        }
        else
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
    invalidateCachedSaveSlots();
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

                invalidateCachedSaveSlots();
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
    const std::string prefix = saving ? "SaveGame" : "LoadGame";
    loadDesign(saving ? "gameplay/save_game" : "gameplay/load_game");
    beginDesign(prefix);
    drawDesign();
    if (!modalOpen() && keyPressed(SDL_SCANCODE_ESCAPE))
    {
        cancel();
        return;
    }
    const Rect viewport = designRect(prefix + "ListViewport");
    const size_t total = m_slots.size() + (saving ? 1 : 0);
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
            const int current = saving && m_newSave ? 0 : int(m_selectedIndex) + (saving ? 1 : 0);
            const size_t selected = size_t(std::clamp(current + delta, 0, int(total) - 1));
            m_newSave = saving && selected == 0;
            m_selectedIndex = saving && selected > 0 ? selected - 1 : selected;
            if (saving)
            {
                m_saveName = m_newSave ? m_currentLocation : m_slots[m_selectedIndex].fileLabel;
            }
            m_revealSelection = true;
        }
    }
    if (m_revealSelection)
    {
        const size_t selected = saving && m_newSave ? 0 : m_selectedIndex + (saving ? 1 : 0);
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
        const size_t slotIndex = saving && index > 0 ? index - 1 : index;
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
    const SaveSlotSummary *pSlot = !m_newSave && m_selectedIndex < m_slots.size() ? &m_slots[m_selectedIndex] : nullptr;
    if (pSlot || saving)
    {
        const std::string kind = !pSlot                              ? "New save"
                                 : pSlot->path.stem() == "autosave"  ? "Automatic"
                                 : pSlot->path.stem() == "quicksave" ? "Quick"
                                                                     : "Manual";
        label(prefix + "SelectedWorldAndKind",
              pSlot && !pSlot->worldName.empty() ? pSlot->worldName + " - " + kind : kind);
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
        }
        else
        {
            label(prefix + "SelectedMetadata", pSlot->fileLabel + "\nSaved " + pSlot->savedAt);
        }
    }
    else
    {
        textInRect(viewport, "No saved games\nStart a new game from the main menu.", "menu_arrus", 15, 0xffc6dfeau,
                   true);
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
    if (action(prefix + "ConfirmButton", saving ? !m_saveName.empty() : pSlot != nullptr) || m_commitRequested)
    {
        m_commitRequested = false;
        if (saving)
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
    std::filesystem::create_directories("saves");

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator("saves"))
    {
        if (!entry.is_regular_file() || toLowerCopy(entry.path().extension().string()) != ".oysav")
        {
            continue;
        }

        if (m_saveAction && (toLowerCopy(entry.path().stem().string()) == "autosave" ||
                             toLowerCopy(entry.path().stem().string()) == "quicksave"))
        {
            continue;
        }
        std::string error;
        const std::optional<GameSaveData> saveData = loadGameDataFromPath(entry.path(), error);

        if (!saveData)
        {
            if (error == SaveFromNewerVersionError)
            {
                ++m_newerSaveCount;
            }
            continue;
        }

        SaveSlotSummary slot = {};
        slot.path = entry.path();
        slot.fileLabel = !saveData->saveName.empty() ? saveData->saveName : friendlySaveFileLabel(entry.path());
        slot.locationName = saveData->mapFileName;
        slot.populated = true;
        const CivilTime civilTime = civilTimeFromGameMinutes(saveData->savedGameMinutes);
        slot.weekdayClockText = formatClock(civilTime);
        slot.dateText = formatDate(civilTime);
        std::error_code timestampError;
        const std::filesystem::file_time_type modified = entry.last_write_time(timestampError);
        if (!timestampError)
        {
            const std::time_t timestamp =
                std::chrono::system_clock::to_time_t(
                    std::chrono::time_point_cast<std::chrono::system_clock::duration>(
                        std::chrono::file_clock::to_sys(modified)));
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
                if (toLowerCopy(entryMap.canonicalId) == toLowerCopy(saveData->mapFileName) ||
                    toLowerCopy(entryMap.fileName) == toLowerCopy(saveData->mapFileName))
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

        if (!saveData->previewBmp.empty())
        {
            decodeBmpBytesToBgra(saveData->previewBmp, slot.previewWidth, slot.previewHeight, slot.previewPixelsBgra);
        }

        m_slots.push_back(std::move(slot));
    }

    std::sort(m_slots.begin(), m_slots.end(), [](const SaveSlotSummary &left, const SaveSlotSummary &right)
              { return compareSavePathsForDisplay(left.path, right.path); });

    if (m_selectedIndex >= m_slots.size())
    {
        m_selectedIndex = 0;
    }

    m_scrollOffset = 0;
    m_lastClickedSlotIndex = static_cast<size_t>(-1);
    m_lastClickedSlotTicks = 0;
    m_newSave = bool(m_saveAction);
    m_slotsLoaded = true;
    if (!m_saveAction)
    {
        s_cachedSlots = m_slots;
        s_cachedNewerSaveCount = m_newerSaveCount;
        s_cachedSlotsValid = true;
    }
}

void LoadGameScreen::loadCachedSaveSlots()
{
    m_slots = s_cachedSlots;
    m_newerSaveCount = s_cachedNewerSaveCount;

    if (m_selectedIndex >= m_slots.size())
    {
        m_selectedIndex = 0;
    }

    m_scrollOffset = 0;
    m_lastClickedSlotIndex = static_cast<size_t>(-1);
    m_lastClickedSlotTicks = 0;
    m_newSave = bool(m_saveAction);
    m_slotsLoaded = true;
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

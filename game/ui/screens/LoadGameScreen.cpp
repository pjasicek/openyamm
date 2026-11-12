#include "game/ui/screens/LoadGameScreen.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"
#include "game/content/RulesetDefinition.h"
#include "game/maps/SaveGame.h"
#include "game/party/PlaythroughNames.h"
#include "game/ui/CalendarText.h"
#include "engine/UserDataPaths.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <atomic>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
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

// "Monday 09:05PM": the list's own clock, with the calendar's weekday names.
std::string formatClock(const CivilTime &time)
{
    char hour[8] = {};
    char minute[8] = {};
    std::snprintf(hour, sizeof(hour), "%02d", time.hour12);
    std::snprintf(minute, sizeof(minute), "%02d", time.minute);
    const std::string weekday = weekdayName(time.dayOfWeek);
    return time.isPm
        ? Engine::tr("{weekday} {hour}:{minute}PM", {{"weekday", weekday}, {"hour", hour}, {"minute", minute}})
        : Engine::tr("{weekday} {hour}:{minute}AM", {{"weekday", weekday}, {"hour", hour}, {"minute", minute}});
}

std::string formatDate(const CivilTime &time)
{
    return formatCalendarDate(time.day, time.month, time.year);
}

std::string friendlySaveFileLabel(const std::filesystem::path &path)
{
    const std::string stem = toLowerCopy(path.stem().string());

    if (isAutosavePath(path))
    {
        return Engine::tr("Autosave");
    }

    if (const int quickSlot = quickSaveSlot(path); quickSlot != 0)
    {
        // The newest is plain "Quicksave", the two before it "Quicksave 2" and "Quicksave 3".
        return quickSlot == 1 ? Engine::tr("Quicksave") : Engine::tr("Quicksave {number}", {{"number", quickSlot}});
    }

    if (stem.rfind("save", 0) == 0 && stem.size() > 4)
    {
        const std::string suffix = stem.substr(4);
        const bool allDigits = std::all_of(suffix.begin(), suffix.end(), [](char character)
                                           { return std::isdigit(static_cast<unsigned char>(character)) != 0; });

        if (allDigits)
        {
            return Engine::tr("Save {number}", {{"number", std::max(1, std::stoi(suffix))}});
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

std::filesystem::path playthroughsDirectory()
{
    return std::filesystem::path("saves") / "playthroughs";
}

// A save file as the list read it, kept while the file's size and time are unchanged.
struct ScannedSave
{
    std::filesystem::path path;
    uintmax_t fileSize = 0;
    std::optional<std::filesystem::file_time_type> modified;
    std::optional<GameSaveSummary> summary;
    // The save's playthrough: its summary's, else (a save from before the summary held it) the save index's or a read
    // of the whole save.
    std::optional<SavePlaythroughInfo> playthrough;
    bool newerVersion = false;
    int previewWidth = 0;
    int previewHeight = 0;
    std::vector<uint8_t> previewPixelsBgra;
};

// A playthrough's statistics file as the list read it, kept while the file's time is unchanged.
struct ScannedPlaythrough
{
    std::filesystem::path file;
    std::optional<std::filesystem::file_time_type> modified;
    std::optional<PlaythroughStatistics::StoredSummary> summary;
};

struct SaveScan
{
    std::vector<ScannedSave> saves;
    // By playthrough id, for the playthroughs the saves name.
    std::unordered_map<std::string, ScannedPlaythrough> playthroughs;
};

// saves/playthroughs/save_index.tsv: the playthrough of each save written before the summary held it, by file name
// with the file's size and time. Such a save is read whole once (seconds for a large one) and not at every start.
struct IndexedSave
{
    uintmax_t fileSize = 0;
    int64_t modified = 0;
    SavePlaythroughInfo playthrough;
};

using SaveIndex = std::unordered_map<std::string, IndexedSave>;

std::filesystem::path saveIndexPath()
{
    return playthroughsDirectory() / "save_index.tsv";
}

SaveIndex readSaveIndex()
{
    SaveIndex index;
    std::ifstream file(saveIndexPath(), std::ios::binary);
    std::string line;

    while (std::getline(file, line))
    {
        std::vector<std::string> fields;
        std::istringstream cells(line);
        std::string cell;

        while (std::getline(cells, cell, '\t'))
        {
            fields.push_back(cell);
        }

        if (fields.size() != 5)
        {
            continue;
        }

        try
        {
            IndexedSave entry;
            entry.fileSize = std::stoull(fields[1]);
            entry.modified = std::stoll(fields[2]);
            entry.playthrough.id = fields[3];
            entry.playthrough.playedSeconds = std::stod(fields[4]);
            index[fields[0]] = std::move(entry);
        }
        catch (const std::exception &)
        {
        }
    }

    return index;
}

void writeSaveIndex(const SaveIndex &index)
{
    std::error_code error;
    std::filesystem::create_directories(playthroughsDirectory(), error);
    std::ofstream file(saveIndexPath(), std::ios::binary | std::ios::trunc);

    for (const auto &[name, entry] : index)
    {
        file << name << '\t' << entry.fileSize << '\t' << entry.modified << '\t' << entry.playthrough.id << '\t'
             << uint64_t(std::max(0.0, entry.playthrough.playedSeconds)) << '\n';
    }
}

// Set while LoadGameScreen::stopSaveScan waits for the worker; the scan stops at its next save.
std::atomic<bool> g_saveScanStopping = false;

// The saves folder's save files and their playthroughs' statistics, reading only those that are not in `known` at
// the same size and time. It touches nothing but the files, so it runs on any thread.
SaveScan scanSaves(SaveScan known)
{
    std::unordered_map<std::string, size_t> knownIndices;

    for (size_t index = 0; index < known.saves.size(); ++index)
    {
        knownIndices.emplace(known.saves[index].path.string(), index);
    }

    SaveScan scanned;
    std::error_code error;
    std::filesystem::create_directories("saves", error);
    SaveIndex saveIndex = readSaveIndex();
    std::unordered_set<std::string> indexedNames;
    bool saveIndexChanged = false;
    bool complete = true;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator("saves", error))
    {
        if (g_saveScanStopping)
        {
            complete = false;
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

        if (knownIndex != knownIndices.end() && known.saves[knownIndex->second].fileSize == save.fileSize
            && known.saves[knownIndex->second].modified == save.modified)
        {
            save = std::move(known.saves[knownIndex->second]);
        }
        else
        {
            std::string loadError;
            save.summary = loadGameSaveSummaryFromPath(save.path, loadError);
            save.newerVersion = !save.summary && loadError == SaveFromNewerVersionError;

            if (save.summary && !save.summary->previewBmp.empty())
            {
                decodeBmpBytesToBgra(save.summary->previewBmp, save.previewWidth, save.previewHeight,
                    save.previewPixelsBgra);
                save.summary->previewBmp = std::vector<uint8_t>();
            }

            if (save.summary)
            {
                save.playthrough = save.summary->playthrough;
            }
        }

        if (save.summary && !save.summary->playthrough)
        {
            // A save from before the summary held its playthrough: the index, else the whole save.
            const std::string name = save.path.filename().string();
            const int64_t modifiedTicks = save.modified ? int64_t(save.modified->time_since_epoch().count()) : 0;
            const auto indexed = saveIndex.find(name);
            indexedNames.insert(name);

            if (indexed != saveIndex.end() && indexed->second.fileSize == save.fileSize
                && indexed->second.modified == modifiedTicks)
            {
                save.playthrough = indexed->second.playthrough;
            }
            else
            {
                std::string loadError;

                if (!save.playthrough)
                {
                    save.playthrough = loadSavePlaythroughInfoFromPath(save.path, loadError);
                }

                if (save.playthrough && save.modified)
                {
                    saveIndex[name] = {save.fileSize, modifiedTicks, *save.playthrough};
                    saveIndexChanged = true;
                }
            }
        }

        scanned.saves.push_back(std::move(save));
    }

    if (complete)
    {
        // Saves that are gone, or were written again with their playthrough in the summary.
        saveIndexChanged = std::erase_if(saveIndex, [&indexedNames](const auto &entry)
            {
                return !indexedNames.contains(entry.first);
            }) > 0 || saveIndexChanged;
    }

    if (saveIndexChanged)
    {
        writeSaveIndex(saveIndex);
    }

    for (const ScannedSave &save : scanned.saves)
    {
        if (!save.playthrough || save.playthrough->id.empty() || scanned.playthroughs.contains(save.playthrough->id))
        {
            continue;
        }

        const std::string &id = save.playthrough->id;
        ScannedPlaythrough playthrough;

        for (const std::filesystem::path &path : PlaythroughStatistics::storedPaths(playthroughsDirectory(), id))
        {
            std::error_code timeError;
            const std::filesystem::file_time_type modified = std::filesystem::last_write_time(path, timeError);

            if (!timeError)
            {
                playthrough.file = path;
                playthrough.modified = modified;
                break;
            }
        }

        const auto knownPlaythrough = known.playthroughs.find(id);

        if (knownPlaythrough != known.playthroughs.end() && knownPlaythrough->second.file == playthrough.file
            && knownPlaythrough->second.modified == playthrough.modified)
        {
            playthrough.summary = knownPlaythrough->second.summary;
        }
        else if (playthrough.modified)
        {
            playthrough.summary = PlaythroughStatistics::readStoredSummary(playthroughsDirectory(), id);
        }

        scanned.playthroughs.emplace(id, std::move(playthrough));
    }

    return scanned;
}

// Every list of the session reads from this: a save is read once, and again only after it changes.
SaveScan g_saveScan;
// The first read of the folder, on a worker thread (LoadGameScreen::startSaveScan): saves older than
// SaveVersionSummaryFirst are read whole, which takes seconds for a folder of late saves.
std::future<SaveScan> g_pendingSaveScan;

std::optional<std::tm> localTimeOf(const std::filesystem::file_time_type &time)
{
    const std::time_t timestamp = std::chrono::system_clock::to_time_t(
        std::chrono::time_point_cast<std::chrono::system_clock::duration>(std::chrono::file_clock::to_sys(time)));
    const std::tm *pLocal = std::localtime(&timestamp);
    return pLocal != nullptr ? std::optional<std::tm>(*pLocal) : std::nullopt;
}

// "6 h 05 min": real time played.
std::string playedTimeText(double seconds)
{
    const uint64_t minutes = uint64_t(std::max(0.0, seconds)) / 60;
    char padded[8] = {};
    std::snprintf(padded, sizeof(padded), "%02d", int(minutes % 60));
    return Engine::tr("{hours} h {minutes} min", {{"hours", int64_t(minutes / 60)}, {"minutes", padded}});
}

// Text colours of the save details, as ABGR.
constexpr uint32_t FactLabelColor = 0xffa3b2aeu;
constexpr uint32_t FactValueColor = 0xffc6dfeau;
constexpr uint32_t NoteColor = 0xffa9bbb7u;
constexpr uint32_t GroupNameColor = 0xffa8d1e6u;
constexpr uint32_t GroupMetaColor = 0xffa6b2abu;
constexpr uint32_t BrassColor = 0xff80bbd6u;
// A save row's inset under its playthrough's heading, in design units.
constexpr float GroupIndent = 12.0f;

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
        g_pendingSaveScan = std::async(std::launch::async, scanSaves, std::move(g_saveScan));
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

    g_saveScan = {};
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
    m_selection = Selection::NewSave;
    setTextEditing(true);
    m_textEdit = TextEdit::SaveName;
}

void LoadGameScreen::configureCurrentPlaythrough(const std::string &playthroughId, double playedSeconds,
                                                 double saveSeconds)
{
    m_currentPlaythroughId = playthroughId;
    m_currentPlayedSeconds = playedSeconds;
    m_currentSaveSeconds = saveSeconds;
}

void LoadGameScreen::handleSdlEvent(const SDL_Event &event)
{
    if (m_textEdit == TextEdit::None || modalOpen())
    {
        return;
    }
    std::string &text = m_textEdit == TextEdit::SaveName ? m_saveName : m_playthroughName;
    if (event.type == SDL_EVENT_TEXT_INPUT)
    {
        Engine::Utf8::appendPrintable(text, event.text.text != nullptr ? event.text.text : "", 40);
    }
    if (event.type == SDL_EVENT_KEY_DOWN && event.key.scancode == SDL_SCANCODE_BACKSPACE && !text.empty())
    {
        Engine::Utf8::popBack(text);
    }
    if (event.type == SDL_EVENT_KEY_DOWN && event.key.scancode == SDL_SCANCODE_RETURN && !event.key.repeat)
    {
        m_commitRequested = m_textEdit == TextEdit::SaveName;
        finishTextEdit();
    }
}

void LoadGameScreen::finishTextEdit()
{
    if (m_textEdit == TextEdit::PlaythroughName)
    {
        commitPlaythroughName();
    }

    m_textEdit = TextEdit::None;
    setTextEditing(false);
}

void LoadGameScreen::commitPlaythroughName()
{
    const PlaythroughGroup *pGroup = findGroup(m_editedGroupId);

    if (pGroup == nullptr || m_editedGroupId.empty())
    {
        return;
    }

    const size_t first = m_playthroughName.find_first_not_of(" \t");
    const size_t last = m_playthroughName.find_last_not_of(" \t");
    std::string name = first == std::string::npos ? "" : m_playthroughName.substr(first, last - first + 1);

    // Its automatic name is no name of its own: it follows the playthrough's rules and the interface language.
    if (name == pGroup->automaticName)
    {
        name.clear();
    }

    if (!writePlaythroughName(playthroughsDirectory(), m_editedGroupId, name))
    {
        m_error = Engine::tr("Unable to save the playthrough's name.");
        return;
    }

    if (name.empty())
    {
        m_playthroughNames.erase(m_editedGroupId);
    }
    else
    {
        m_playthroughNames[m_editedGroupId] = name;
    }

    rebuildGroups();
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
            m_error = Engine::tr("Unable to load this save. Check its required content packages.");
        }
    };
    if (m_fromGameplay)
    {
        confirm(Engine::tr("Load Adventure?"),
                m_loadWarning.empty() ? Engine::tr("Unsaved progress in the current adventure will be lost.")
                                      : Engine::localizeKnown(m_loadWarning),
                {Engine::tr("Cancel"), Engine::tr("Load")},
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
    // Typed names compare without case in any language.
    const std::string lower = Engine::Utf8::lower(name);
    if (name.empty() || lower == "autosave" || lower == "quicksave")
    {
        m_error = Engine::tr("Choose a name other than Autosave or Quicksave.");
        return;
    }
    const bool replacing = m_selection == Selection::Slot && m_selectedIndex < m_slots.size();
    std::filesystem::path path;
    if (replacing)
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
    // A name is taken only within the playthrough being saved; another playthrough may use it too.
    for (const SaveSlotSummary &slot : m_slots)
    {
        if (slot.playthroughId == m_currentPlaythroughId && Engine::Utf8::lower(slot.fileLabel) == lower
            && slot.path != path)
        {
            m_error = Engine::tr("A save already uses that name. Select it to replace it.");
            return;
        }
    }
    const auto save = [this, path, name]()
    {
        if (!m_saveAction(path, name))
        {
            m_error = Engine::tr("Saving failed or is not allowed in this location.");
        }
    };
    if (replacing)
    {
        confirm(Engine::tr("Replace Saved Adventure?"),
                Engine::tr("Replace {save}?", {{"save", m_slots[m_selectedIndex].fileLabel}}),
                {Engine::tr("Cancel"), Engine::tr("Replace")},
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

    std::string body = Engine::trn("Imported {count} save.", "Imported {count} saves.", uint64_t(result.imported),
                                   {{"count", int64_t(result.imported)}});
    if (result.imported == 0 && result.skipped == 0 && result.failed == 0)
    {
        body = Engine::tr("No saves were found in that folder or in a \"saves\" folder inside it.");
    }
    if (result.skipped > 0)
    {
        body += "\n"
            + Engine::tr("{count} skipped: a save with the same name already exists.",
                         {{"count", int64_t(result.skipped)}});
    }
    if (result.failed > 0)
    {
        body += "\n" + Engine::tr("{count} could not be copied.", {{"count", int64_t(result.failed)}});
    }
    confirm(Engine::tr("Import Saves"), body, {Engine::tr("OK")}, [](int) {});
}

void LoadGameScreen::requestDelete()
{
    if (m_selection != Selection::Slot || m_selectedIndex >= m_slots.size())
    {
        return;
    }

    const SaveSlotSummary &slot = m_slots[m_selectedIndex];
    const std::filesystem::path path = slot.path;
    m_commitRequested = false;
    finishTextEdit();
    m_error.clear();
    confirm(Engine::tr("Delete Save?"), Engine::tr("Permanently delete \"{save}\"?", {{"save", slot.fileLabel}}),
            {Engine::tr("Cancel"), Engine::tr("Delete")},
            [this, path](int choice)
            {
                if (choice != 1)
                {
                    return;
                }

                std::error_code error;
                if (!std::filesystem::remove(path, error))
                {
                    m_error = error ? Engine::tr("Unable to delete this save: {error}", {{"error", error.message()}})
                                   : Engine::tr("This save no longer exists.");
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

void LoadGameScreen::requestDeletePlaythrough()
{
    const PlaythroughGroup *pGroup = m_selection == Selection::Group ? findGroup(m_selectedGroupId) : nullptr;

    // Not the saves that name no playthrough, and not the playthrough being played.
    if (pGroup == nullptr || pGroup->id.empty() || pGroup->id == m_currentPlaythroughId)
    {
        return;
    }

    // Every save of the playthrough, with the Quicksave and Autosave the Save screen does not list.
    std::vector<std::filesystem::path> paths;

    for (const ScannedSave &save : g_saveScan.saves)
    {
        if (save.playthrough && save.playthrough->id == pGroup->id)
        {
            paths.push_back(save.path);
        }
    }

    const std::string id = pGroup->id;
    m_commitRequested = false;
    finishTextEdit();
    m_error.clear();
    confirm(Engine::tr("Delete Playthrough?"),
            Engine::trn("Permanently delete \"{playthrough}\", its {count} save and its statistics?",
                        "Permanently delete \"{playthrough}\", its {count} saves and its statistics?",
                        uint64_t(paths.size()), {{"playthrough", pGroup->name}, {"count", int64_t(paths.size())}}),
            {Engine::tr("Cancel"), Engine::tr("Delete")},
            [this, id, paths](int choice)
            {
                if (choice != 1)
                {
                    return;
                }

                size_t failed = 0;

                for (const std::filesystem::path &path : paths)
                {
                    std::error_code error;
                    std::filesystem::remove(path, error);
                    failed += error ? 1 : 0;
                }

                if (failed == 0)
                {
                    PlaythroughStatistics::removeStored(playthroughsDirectory(), id);
                    writePlaythroughName(playthroughsDirectory(), id, "");
                }
                else
                {
                    m_error = Engine::tr("{count} could not be deleted.", {{"count", int64_t(failed)}});
                }

                refreshSaveSlots();
                m_revealSelection = true;
            });
}

const LoadGameScreen::PlaythroughGroup *LoadGameScreen::findGroup(const std::string &playthroughId) const
{
    for (const PlaythroughGroup &group : m_groups)
    {
        if (group.id == playthroughId)
        {
            return &group;
        }
    }

    return nullptr;
}

std::vector<LoadGameScreen::ListRow> LoadGameScreen::listRows() const
{
    std::vector<ListRow> rows;
    const bool saving = bool(m_saveAction);

    if (saving)
    {
        rows.push_back({RowKind::NewSave, 0});
    }

    for (size_t groupIndex = 0; groupIndex < m_groups.size(); ++groupIndex)
    {
        const PlaythroughGroup &group = m_groups[groupIndex];

        if (saving && !m_showAllPlaythroughs && !m_currentPlaythroughId.empty() && group.id != m_currentPlaythroughId)
        {
            continue;
        }

        // Under the ruleset filter a playthrough is listed by its saves of that ruleset.
        const auto shown = [this](size_t slotIndex)
        {
            return m_rulesetFilter.empty() || m_slots[slotIndex].rulesetId == m_rulesetFilter;
        };

        if (!m_rulesetFilter.empty() && std::none_of(group.slots.begin(), group.slots.end(), shown))
        {
            continue;
        }

        rows.push_back({RowKind::Group, groupIndex});

        if (m_expandedGroups.contains(group.id))
        {
            for (const size_t slotIndex : group.slots)
            {
                if (shown(slotIndex))
                {
                    rows.push_back({RowKind::Slot, slotIndex});
                }
            }
        }
    }

    return rows;
}

std::optional<size_t> LoadGameScreen::selectedRow(const std::vector<ListRow> &rows) const
{
    for (size_t index = 0; index < rows.size(); ++index)
    {
        const ListRow &row = rows[index];
        const bool selected = row.kind == RowKind::NewSave ? m_selection == Selection::NewSave
            : row.kind == RowKind::Slot ? m_selection == Selection::Slot && row.index == m_selectedIndex
            : m_selection == Selection::Group && m_groups[row.index].id == m_selectedGroupId;

        if (selected)
        {
            return index;
        }
    }

    return std::nullopt;
}

void LoadGameScreen::selectRow(const ListRow &row)
{
    if (m_textEdit == TextEdit::PlaythroughName)
    {
        finishTextEdit();
    }

    switch (row.kind)
    {
    case RowKind::NewSave:
        m_selection = Selection::NewSave;
        m_saveName = m_currentLocation;
        break;

    case RowKind::Slot:
        m_selection = Selection::Slot;
        m_selectedIndex = row.index;

        if (m_saveAction)
        {
            m_saveName = m_slots[row.index].fileLabel;
        }

        break;

    case RowKind::Group:
        m_selection = Selection::Group;
        m_selectedGroupId = m_groups[row.index].id;
        break;
    }
}

void LoadGameScreen::selectDefaultRow(const std::vector<ListRow> &rows)
{
    m_selection = Selection::None;

    // A new save when saving; else the first save shown, else the first playthrough.
    for (const RowKind kind : {RowKind::NewSave, RowKind::Slot, RowKind::Group})
    {
        for (const ListRow &row : rows)
        {
            if (row.kind == kind)
            {
                selectRow(row);
                return;
            }
        }
    }
}

void LoadGameScreen::activateRow(const ListRow &row)
{
    if (row.kind == RowKind::Group)
    {
        // A click unfolds a folded playthrough; a click on the selected one folds or unfolds it.
        const std::string id = m_groups[row.index].id;
        const bool wasSelected = m_selection == Selection::Group && m_selectedGroupId == id;

        if (!m_expandedGroups.contains(id))
        {
            m_expandedGroups.insert(id);
        }
        else if (wasSelected)
        {
            m_expandedGroups.erase(id);
        }

        selectRow(row);
        return;
    }

    selectRow(row);

    if (row.kind == RowKind::Slot && !m_saveAction)
    {
        if (m_lastClickedSlotIndex == row.index && SDL_GetTicks() - m_lastClickedSlotTicks < 500)
        {
            requestLoad();
        }

        m_lastClickedSlotIndex = row.index;
        m_lastClickedSlotTicks = SDL_GetTicks();
    }
}

LoadGameScreen::Rect LoadGameScreen::playthroughNameField() const
{
    return canvasRect(438.4f, 178.0f, 323.2f, 22.4f);
}

bool LoadGameScreen::drawGroupRow(const std::string &id, const Rect &rect, const PlaythroughGroup &group,
                                  bool selected)
{
    const float unit = designScale();
    const float rule = std::max(1.0f, std::round(0.5333f * unit));

    if (selected)
    {
        skin("save_row_selected", rect, true);
    }
    else
    {
        drawSolidRect({rect.x, rect.y + rect.height - rule, rect.width, rule}, 0x5577a4b5u);
    }

    const Hotspot input = hotspot(id, rect);

    if (input.hovered && !selected)
    {
        drawSolidRect(rect, 0x1280bbd6u);
    }

    const float centerY = rect.y + rect.height / 2;

    if (m_expandedGroups.contains(group.id))
    {
        drawTextureColor("hud_x2/menus/omenu_chevron_down.png",
                         {rect.x + 6 * unit, centerY - 3 * unit, 9 * unit, 6 * unit}, BrassColor);
    }
    else
    {
        drawTextureColor("hud_x2/menus/omenu_glyph_play.png",
                         {rect.x + 7 * unit, centerY - 4 * unit, 7 * unit, 8 * unit}, BrassColor);
    }

    // The time played and the last day of play at the right; the name takes the rest, on one line.
    std::string meta = group.played;

    if (!group.lastPlayed.empty())
    {
        meta += (meta.empty() ? "" : " \xC2\xB7 ") + group.lastPlayed;
    }

    constexpr float MetaSize = 10.24f;
    const float metaWidth =
        measureTextWidth("menu_lucida", meta, unit * MetaSize / std::max(1, fontHeight("menu_lucida"))) + 1;
    const float right = rect.x + rect.width - 10 * unit;
    textInRect({right - metaWidth, rect.y + 6 * unit, metaWidth, rect.height - 12 * unit}, meta, "menu_lucida",
               MetaSize, GroupMetaColor);
    const float nameLeft = rect.x + 21 * unit;
    textInRect({nameLeft, rect.y + 5 * unit, std::max(1.0f, right - metaWidth - 8 * unit - nameLeft),
                rect.height - 10 * unit},
               group.name, "fondamento", 14.0f, selected ? FactValueColor : GroupNameColor);
    return input.activated;
}

void LoadGameScreen::drawSaveDetails(const std::string &prefix, const SaveSlotSummary *pSlot, bool saveAffordable)
{
    const bool saving = bool(m_saveAction);
    const std::string kind = !pSlot                       ? Engine::tr("New save")
                             : isAutosavePath(pSlot->path)  ? Engine::tr("Automatic")
                             : isQuickSavePath(pSlot->path) ? Engine::tr("Quick")
                                                            : Engine::tr("Manual");
    const std::string worldAndKind = pSlot && !pSlot->worldName.empty() ? pSlot->worldName + " - " + kind : kind;
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
    if (!pSlot && !m_previewPixels.empty())
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
        textInRect(preview, Engine::tr("No screenshot available"), "menu_lucida", 12, 0xff9bb6c2u, true);
    }

    // A new save belongs to the playthrough being played.
    const PlaythroughGroup *pGroup = findGroup(pSlot ? pSlot->playthroughId : m_currentPlaythroughId);
    label(prefix + "PreviewLabel1", Engine::tr("Game date"));
    label(prefix + "PreviewLine1", pSlot ? pSlot->dateText : m_currentDate);
    label(prefix + "PreviewLabel2", Engine::tr("Game time"));
    label(prefix + "PreviewLine2", pSlot ? pSlot->weekdayClockText : m_currentClock);
    label(prefix + "PreviewLabel3", Engine::tr("Time played"));
    label(prefix + "PreviewLine3", pSlot ? pSlot->playedText
        : m_currentSaveSeconds >= 60.0 ? playedTimeText(m_currentSaveSeconds) : std::string("-"));
    label(prefix + "PreviewLabel4", Engine::tr("Playthrough"));
    label(prefix + "PreviewLine4", pGroup != nullptr ? pGroup->name : std::string("-"));

    if (saving)
    {
        const Rect field = designRect(prefix + "NameField");
        label(prefix + "NameLabel", Engine::tr("Save name"));
        if (button("save-name", field, "", "text_field") || (keyPressed(SDL_SCANCODE_TAB) && focused("save-name")))
        {
            m_textEdit = TextEdit::SaveName;
            setTextEditing(true);
        }
        label(prefix + "NameField", m_saveName + (m_textEdit == TextEdit::SaveName ? "_" : ""));
        if (m_error.empty() && (m_foodCost.food > 0 || m_foodCost.foodWithEnemiesNear > 0))
        {
            std::string text = m_foodCost.food > 0
                ? Engine::tr("Saving here costs {food} food, you carry {carried}",
                             {{"food", int64_t(m_foodCost.food)}, {"carried", int64_t(m_foodCost.carried)}})
                : Engine::tr("Saving here is free now");
            if (m_foodCost.foodWithEnemiesNear > m_foodCost.food)
            {
                text += "\n"
                    + Engine::tr("With enemies near: {food} food",
                                 {{"food", int64_t(m_foodCost.foodWithEnemiesNear)}});
            }
            label(prefix + "FoodCost", text, saveAffordable ? 0 : 0xff5c5ce0u);
        }
    }
    else if (m_error.empty() && m_newerSaveCount == 0)
    {
        label(prefix + "SelectedMetadata",
            Engine::tr("{save}\nSaved {saved_at}", {{"save", pSlot->fileLabel}, {"saved_at", pSlot->savedAt}}));
        label(prefix + "SelectedRuleset", pSlot->rulesetBadge);
    }
}

void LoadGameScreen::drawPlaythroughDetails(const PlaythroughGroup &group)
{
    const std::string prefix = m_saveAction ? "SaveGame" : "LoadGame";
    constexpr float Left = 438.4f;
    constexpr float SecondColumn = 603.4667f;
    constexpr float ColumnWidth = 158.1333f;
    constexpr float LabelSize = 8.96f;
    constexpr float ValueSize = 12.16f;
    label(prefix + "SelectedWorldAndKind", group.id.empty() ? Engine::tr("Saves") : Engine::tr("Playthrough"));
    label(prefix + "SelectedName", group.name);
    float top = 165.85f;

    if (!group.id.empty())
    {
        textInRect(canvasRect(Left, top, 323.2f, 10.67f), Engine::tr("Playthrough name"), "menu_lucida", 10.88f,
                   FactLabelColor);
        const Rect field = playthroughNameField();
        const bool editing = m_textEdit == TextEdit::PlaythroughName && m_editedGroupId == group.id;

        if (button("playthrough-name", field, "", "text_field") && !editing)
        {
            m_textEdit = TextEdit::PlaythroughName;
            m_editedGroupId = group.id;
            m_playthroughName = group.name;
            setTextEditing(true);
        }

        const float pad = 6.9333f * designScale();
        textInRect({field.x + pad, field.y, field.width - 2 * pad, field.height},
                   editing ? m_playthroughName + "_" : group.name, "menu_lucida", ValueSize, 0xffc0dce9u);
        top = 210.0f;
    }

    const auto fact = [&](float x, float y, const std::string &name, const std::string &value)
    {
        textInRect(canvasRect(x, y, ColumnWidth, 9.07f), name, "menu_lucida", LabelSize, FactLabelColor);
        textInRect(canvasRect(x, y + 10.6f, ColumnWidth, 12.27f), value.empty() ? std::string("-") : value,
                   "menu_arrus", ValueSize, FactValueColor);
    };
    fact(Left, top, Engine::tr("Rules"), group.rules);
    fact(SecondColumn, top, Engine::tr("Difficulty"), group.difficulty);
    fact(Left, top + 26, Engine::tr("Started in"), group.startedIn);
    fact(SecondColumn, top + 26, Engine::tr("Started"), group.started);
    fact(Left, top + 52, Engine::tr("Last played"), group.lastPlayed);
    fact(SecondColumn, top + 52, Engine::tr("Time played"), group.played);
    std::string note = Engine::trn("{count} save", "{count} saves", uint64_t(group.slots.size()),
                                   {{"count", int64_t(group.slots.size())}});

    if (group.id.empty())
    {
        note += "\n" + Engine::tr("These saves name no playthrough. Load one and save again to start its record.");
    }
    else if (!group.hasStatistics)
    {
        note += "\n"
            + Engine::tr("This playthrough has no statistics here yet. Its record starts when a save is loaded.");
    }

    textInRect(canvasRect(Left, top + 82, 323.2f, 40.0f), note, "menu_lucida", 10.24f, NoteColor);
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
    // A text field loses the keyboard to Tab or a click elsewhere; a playthrough's name is kept as typed.
    if (m_textEdit != TextEdit::None && !modalOpen())
    {
        const Rect field =
            m_textEdit == TextEdit::SaveName ? designRect(prefix + "NameField") : playthroughNameField();
        if (keyPressed(SDL_SCANCODE_TAB) || (leftMouseJustPressed() && !pointerInside(field)))
        {
            finishTextEdit();
        }
    }
    if (drawSortButtons(prefix))
    {
        m_scrollOffset = 0;
        m_revealSelection = true;
    }
    if (saving ? drawScopeButtons(prefix) : drawRulesetFilters(prefix))
    {
        m_scrollOffset = 0;
        m_revealSelection = true;
    }
    // Rows of the list: the new-save row when saving, then each playthrough's heading and, unfolded, its saves.
    std::vector<ListRow> rows = listRows();
    std::optional<size_t> selected = selectedRow(rows);
    if (!selected)
    {
        // Nothing chosen yet, or the selection left the list (a folded playthrough, a deleted save).
        selectDefaultRow(rows);
        selected = selectedRow(rows);
    }
    const Rect viewport = designRect(prefix + "ListViewport");
    const float unit = designScale();
    const Rect firstRow = designRect(prefix + "SlotRow0");
    const float rowPitch = firstRow.height / unit + 3.2f;
    const int visibleRows = std::max(1, int(viewport.height / (rowPitch * unit)));
    if (!modalOpen() && m_textEdit == TextEdit::None && !rows.empty())
    {
        const int delta = int(keyPressed(SDL_SCANCODE_DOWN)) - int(keyPressed(SDL_SCANCODE_UP)) +
                          visibleRows * (int(keyPressed(SDL_SCANCODE_PAGEDOWN)) - int(keyPressed(SDL_SCANCODE_PAGEUP)));
        if (delta != 0)
        {
            const size_t target = size_t(std::clamp(int(selected.value_or(0)) + delta, 0, int(rows.size()) - 1));
            selectRow(rows[target]);
            selected = target;
            m_revealSelection = true;
        }
        else if (m_selection == Selection::Group
                 && keyPressed(SDL_SCANCODE_RIGHT) != keyPressed(SDL_SCANCODE_LEFT))
        {
            // Right unfolds the selected playthrough, Left folds it.
            if (keyPressed(SDL_SCANCODE_RIGHT))
            {
                m_expandedGroups.insert(m_selectedGroupId);
            }
            else
            {
                m_expandedGroups.erase(m_selectedGroupId);
            }
            rows = listRows();
            selected = selectedRow(rows);
        }
    }
    const float contentHeight = rows.empty() ? 0 : rows.size() * rowPitch - 3.2f;
    if (m_revealSelection)
    {
        const float top = selected.value_or(0) * rowPitch;
        m_scrollOffset = std::clamp(m_scrollOffset, top + firstRow.height / unit - viewport.height / unit, top);
        m_revealSelection = false;
    }
    scrollViewport(viewport, contentHeight, m_scrollOffset, rowPitch);
    setDesignClip(viewport);
    std::optional<ListRow> activated;
    for (size_t index = size_t(m_scrollOffset / rowPitch); index < rows.size(); ++index)
    {
        const ListRow &row = rows[index];
        const std::string id = prefix + "SlotRow" + std::to_string(index);
        Rect rect = firstRow;
        const float offset = index * rowPitch - m_scrollOffset;
        rect.y += offset * unit;
        if (rect.y >= viewport.y + viewport.height)
        {
            break;
        }
        const bool rowSelected = selected && *selected == index;
        if (row.kind == RowKind::Group)
        {
            if (drawGroupRow(id, rect, m_groups[row.index], rowSelected))
            {
                activated = row;
            }
            continue;
        }
        const float indent = row.kind == RowKind::Slot ? GroupIndent : 0;
        rect.x += indent * unit;
        rect.width -= indent * unit;
        if (button(id, rect, "", "save_row", true, rowSelected))
        {
            activated = row;
        }
        if (row.kind == RowKind::NewSave)
        {
            textInRect({rect.x + 10 * unit, rect.y + 4 * unit, rect.width - 20 * unit, 22 * unit},
                       Engine::tr("Create a new save"),
                       "menu_arrus", 15.36f);
        }
        else
        {
            label(prefix + "SlotRow0Name", m_slots[row.index].fileLabel, 0, offset, indent);
            label(prefix + "SlotRow0Location", m_slots[row.index].locationName, 0, offset);
        }
    }
    setDesignClip(std::nullopt);
    if (activated)
    {
        activateRow(*activated);
    }
    const SaveSlotSummary *pSlot =
        m_selection == Selection::Slot && m_selectedIndex < m_slots.size() ? &m_slots[m_selectedIndex] : nullptr;
    const PlaythroughGroup *pGroup = m_selection == Selection::Group ? findGroup(m_selectedGroupId) : nullptr;
    if (pGroup != nullptr)
    {
        drawPlaythroughDetails(*pGroup);
    }
    else if (pSlot != nullptr || m_selection == Selection::NewSave)
    {
        drawSaveDetails(prefix, pSlot, saveAffordable);
    }
    else
    {
        textInRect(viewport, Engine::tr("No saved games\nStart a new game from the main menu."), "menu_arrus", 15,
                   0xffc6dfeau, true);
    }
    if (action(prefix + "CancelButton"))
    {
        cancel();
        return;
    }
    if (pGroup != nullptr)
    {
        // The playthrough being played keeps its saves; so does the heading of saves that name none.
        if (action(prefix + "DeleteButton", !pGroup->id.empty() && pGroup->id != m_currentPlaythroughId,
                   Engine::tr("Delete Playthrough")))
        {
            requestDeletePlaythrough();
        }
    }
    else if (action(prefix + "DeleteButton", pSlot != nullptr))
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
    // Re-read: a deletion confirmed above may have rebuilt the list.
    pGroup = m_selection == Selection::Group ? findGroup(m_selectedGroupId) : nullptr;
    pSlot = m_selection == Selection::Slot && m_selectedIndex < m_slots.size() ? &m_slots[m_selectedIndex] : nullptr;
    const bool canConfirm = pGroup != nullptr ? !saving && !pGroup->slots.empty()
        : saving ? !m_saveName.empty() && saveAffordable : pSlot != nullptr;
    const std::string confirmText = pGroup != nullptr && !saving ? Engine::tr("Load Newest Save") : std::string();
    if (action(prefix + "ConfirmButton", canConfirm, confirmText) || (m_commitRequested && pGroup == nullptr))
    {
        m_commitRequested = false;
        if (pGroup != nullptr)
        {
            m_selectedIndex = pGroup->newestSlot;
            requestLoad();
        }
        else if (saving && !saveAffordable)
        {
            m_error = Engine::tr("Not enough food: saving here costs {food}.", {{"food", int64_t(m_foodCost.food)}});
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
    m_commitRequested = false;
    // In the place of the save's last lines.
    const Rect notice = saving ? canvasRect(438.4f, 381.5f, 323.2f, 22) : canvasRect(438.4f, 346.5f, 323.2f, 28);
    if (!m_error.empty())
    {
        textInRect(notice, m_error, "menu_lucida", 10.5f);
    }
    else if (m_newerSaveCount > 0)
    {
        textInRect(notice,
                   Engine::trn("{count} save needs a newer version of OpenYAMM and is not listed.",
                               "{count} saves need a newer version of OpenYAMM and are not listed.",
                               uint64_t(m_newerSaveCount), {{"count", int64_t(m_newerSaveCount)}}),
                   "menu_lucida", 10.5f);
    }
    drawConfirmation();
}

const std::string &LoadGameScreen::rulesetDisplayName(const std::string &rulesetId)
{
    const auto found = m_rulesetNames.find(rulesetId);

    if (found != m_rulesetNames.end())
    {
        return found->second;
    }

    if (rulesetId.empty() || rulesetId == StandardRulesetId)
    {
        return m_rulesetNames.emplace(rulesetId, Engine::tr("Standard")).first->second;
    }

    // The names are English (ruleset.yml); the list shows them in the interface language.
    std::string error;
    const std::optional<RulesetDefinition> ruleset = loadRulesetDefinition(assetFileSystem(), rulesetId, error);
    return m_rulesetNames.emplace(
        rulesetId,
        ruleset ? Engine::localize(ruleset->name)
                : Engine::tr("{ruleset} (not installed)", {{"ruleset", rulesetId}})).first->second;
}

std::string LoadGameScreen::continentNameOfWorld(const std::string &worldId) const
{
    if (m_pGameData == nullptr || worldId.empty())
    {
        return {};
    }

    for (const MapStatsEntry &map : m_pGameData->mapEntries())
    {
        if (map.worldId != worldId)
        {
            continue;
        }

        for (const MergedCharacterSelectionContinent &continent :
             m_pGameData->mergedCharacterSelectionTable().continents())
        {
            if (continent.id == map.mergedContinentId)
            {
                return Engine::localizeKnown(continent.name);
            }
        }

        break;
    }

    return {};
}

void LoadGameScreen::refreshSaveSlots()
{
    m_slots.clear();
    m_slotsLoaded = false;
    m_newerSaveCount = 0;

    // The scan started with the menu has read most of the folder; this one reads only what changed since.
    if (g_pendingSaveScan.valid())
    {
        g_saveScan = g_pendingSaveScan.get();
    }

    g_saveScan = scanSaves(std::move(g_saveScan));
    m_slotsSignature = saveFolderSignature();
    m_playthroughRecords.clear();

    for (const auto &[id, playthrough] : g_saveScan.playthroughs)
    {
        if (playthrough.summary)
        {
            m_playthroughRecords.emplace(id, *playthrough.summary);
        }
    }

    m_playthroughNames = readPlaythroughNames(playthroughsDirectory());

    for (const ScannedSave &save : g_saveScan.saves)
    {
        // The game writes these itself; they are not replaced by hand.
        if (m_saveAction && (isAutosavePath(save.path) || isQuickSavePath(save.path)))
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
        slot.rulesetName = rulesetDisplayName(summary.ruleset.isStandard() ? std::string() : summary.ruleset.id);

        if (!summary.ruleset.isStandard())
        {
            slot.difficultyName = Engine::tr(rulesetDifficultyName(summary.ruleset.options.difficulty));
            slot.rulesetBadge = describeRulesetSelection(summary.ruleset, slot.rulesetName);
        }

        if (save.playthrough)
        {
            slot.playthroughId = save.playthrough->id;
        }

        slot.playedText = save.playthrough && save.playthrough->playedSeconds >= 60.0
            ? playedTimeText(save.playthrough->playedSeconds) : std::string("-");
        const CivilTime civilTime = civilTimeFromGameMinutes(summary.savedGameMinutes);
        slot.weekdayClockText = formatClock(civilTime);
        slot.dateText = formatDate(civilTime);
        if (save.modified)
        {
            slot.modified = *save.modified;
            if (const std::optional<std::tm> local = localTimeOf(*save.modified))
            {
                std::ostringstream formatted;
                formatted << std::put_time(&*local, "%Y-%m-%d %H:%M");
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
                    // map_stats.txt and character_selection.yml texts are English.
                    slot.locationName = Engine::localize(entryMap.name);
                    slot.worldName = entryMap.worldId;
                    for (const MergedCharacterSelectionContinent &continent :
                         m_pGameData->mergedCharacterSelectionTable().continents())
                    {
                        if (continent.id == entryMap.mergedContinentId)
                        {
                            slot.worldName = Engine::localizeKnown(continent.name);
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
    m_selection = m_saveAction ? Selection::NewSave : Selection::None;
    m_selectedIndex = 0;
    m_scrollOffset = 0;
    m_lastClickedSlotIndex = static_cast<size_t>(-1);
    m_lastClickedSlotTicks = 0;
    m_slotsLoaded = true;
}

void LoadGameScreen::rebuildGroups()
{
    m_groups.clear();
    std::unordered_map<std::string, size_t> groupIndices;

    for (size_t slotIndex = 0; slotIndex < m_slots.size(); ++slotIndex)
    {
        const SaveSlotSummary &slot = m_slots[slotIndex];
        const auto [found, added] = groupIndices.try_emplace(slot.playthroughId, m_groups.size());

        if (added)
        {
            m_groups.emplace_back();
            m_groups.back().id = slot.playthroughId;
            m_groups.back().newestSlot = slotIndex;
        }

        PlaythroughGroup &group = m_groups[found->second];
        group.slots.push_back(slotIndex);

        if (slot.modified > m_slots[group.newestSlot].modified)
        {
            group.newestSlot = slotIndex;
        }
    }

    // The playthrough being played has its heading on the Save screen before its first save by hand.
    if (m_saveAction && !m_currentPlaythroughId.empty() && !groupIndices.contains(m_currentPlaythroughId))
    {
        m_groups.emplace_back();
        m_groups.back().id = m_currentPlaythroughId;
    }

    for (PlaythroughGroup &group : m_groups)
    {
        describeGroup(group);
    }

    // The playthrough being played, the others by their newest save, and last the saves that name none.
    const auto rank = [this](const PlaythroughGroup &group)
    {
        return group.id.empty() ? 2 : !m_currentPlaythroughId.empty() && group.id == m_currentPlaythroughId ? 0 : 1;
    };
    std::stable_sort(m_groups.begin(), m_groups.end(),
        [this, &rank](const PlaythroughGroup &left, const PlaythroughGroup &right)
        {
            if (rank(left) != rank(right))
            {
                return rank(left) < rank(right);
            }

            if (left.slots.empty() || right.slots.empty())
            {
                return !left.slots.empty() && right.slots.empty();
            }

            return m_slots[left.newestSlot].modified > m_slots[right.newestSlot].modified;
        });

    if (!m_expansionChosen && !m_groups.empty())
    {
        m_expandedGroups.insert(m_groups.front().id);
        m_expansionChosen = true;
    }

    // Only the rulesets the saves were played with, so a player who never started a game of another ruleset sees no
    // filter (audit STD2-M2).
    m_rulesetFilters.clear();

    for (const SaveSlotSummary &slot : m_slots)
    {
        if (std::find(m_rulesetFilters.begin(), m_rulesetFilters.end(), slot.rulesetId) == m_rulesetFilters.end())
        {
            m_rulesetFilters.push_back(slot.rulesetId);
        }
    }

    std::sort(m_rulesetFilters.begin(), m_rulesetFilters.end(), [](const std::string &left, const std::string &right)
        {
            const bool leftStandard = left == StandardRulesetId;
            return leftStandard != (right == StandardRulesetId) ? leftStandard : left < right;
        });

    if (std::find(m_rulesetFilters.begin(), m_rulesetFilters.end(), m_rulesetFilter) == m_rulesetFilters.end())
    {
        m_rulesetFilter.clear();
    }
}

void LoadGameScreen::describeGroup(PlaythroughGroup &group)
{
    const SaveSlotSummary *pNewest = group.slots.empty() ? nullptr : &m_slots[group.newestSlot];
    const auto record = m_playthroughRecords.find(group.id);
    const PlaythroughStatistics::StoredSummary *pRecord =
        record != m_playthroughRecords.end() ? &record->second : nullptr;
    group.hasStatistics = pRecord != nullptr;

    // The rules of its newest save (the difficulty may change within a playthrough), else of its start.
    if (pNewest != nullptr)
    {
        group.rules = pNewest->rulesetName;
        group.difficulty = pNewest->difficultyName;
    }
    else if (pRecord != nullptr)
    {
        group.rules = rulesetDisplayName(pRecord->header.ruleset);

        if (const std::optional<RulesetDifficulty> difficulty = parseRulesetDifficulty(pRecord->header.difficulty))
        {
            group.difficulty = Engine::tr(rulesetDifficultyName(*difficulty));
        }
    }

    std::optional<double> playedSeconds;

    if (pRecord != nullptr)
    {
        group.startedIn = continentNameOfWorld(pRecord->header.startWorld);
        group.started = formatUtcDate(pRecord->header.createdUtc);
        group.lastPlayed = formatUtcDate(pRecord->header.lastPlayedUtc);
        playedSeconds = pRecord->playedSeconds;
    }

    if (group.lastPlayed.empty() && pNewest != nullptr)
    {
        if (const std::optional<std::tm> local = localTimeOf(pNewest->modified))
        {
            group.lastPlayed = formatCalendarDate(local->tm_mday, local->tm_mon + 1, local->tm_year + 1900);
        }
    }

    // The statistics file of the playthrough being played is written every so often; the game knows its time now.
    if (!group.id.empty() && group.id == m_currentPlaythroughId)
    {
        playedSeconds = m_currentPlayedSeconds;
    }

    // Under a minute reads as no time: a save from before the statistics, or a game just begun.
    group.played = playedSeconds && *playedSeconds >= 60.0 ? playedTimeText(*playedSeconds) : std::string();

    if (group.id.empty())
    {
        group.automaticName = Engine::tr("Older saves");
    }
    else
    {
        // MAW's own difficulty carries the ruleset's name: "MAW", not "MAW MAW".
        group.automaticName =
            group.rules + (group.difficulty.empty() || group.difficulty == group.rules ? "" : " " + group.difficulty);

        if (!group.startedIn.empty())
        {
            group.automaticName = group.startedIn + " \xC2\xB7 " + group.automaticName;
        }
    }

    const auto name = m_playthroughNames.find(group.id);
    group.name = name != m_playthroughNames.end() && !group.id.empty() ? name->second : group.automaticName;
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
    rebuildGroups();
}

bool LoadGameScreen::drawScopeButtons(const std::string &prefix)
{
    // Nothing to choose while every listed save is the playthrough's own.
    const bool othersExist = std::any_of(m_groups.begin(), m_groups.end(),
        [this](const PlaythroughGroup &group) { return group.id != m_currentPlaythroughId; });

    if (m_currentPlaythroughId.empty() || !othersExist)
    {
        return false;
    }

    // One row of choices: the playthrough being played, every playthrough, then (when the saves were played with
    // more than one ruleset) every playthrough's saves of one ruleset.
    struct Choice
    {
        std::string text;
        bool all = false;
        std::string rulesetId;
    };
    std::vector<Choice> choices = {{Engine::tr("This playthrough"), false, {}}, {Engine::tr("All"), true, {}}};

    if (m_rulesetFilters.size() >= 2)
    {
        for (const std::string &rulesetId : m_rulesetFilters)
        {
            choices.push_back({rulesetDisplayName(rulesetId), true, rulesetId});
        }
    }

    const Rect area = designRect(prefix + "ScopeButtons");
    const float unit = designScale();
    const float gap = 6 * unit;
    const float ownWidth = 112 * unit;
    const size_t others = choices.size() - 1;
    const float otherWidth = std::min(64 * unit, (area.width - ownWidth - gap * float(others)) / float(others));
    float x = area.x + area.width - ownWidth - float(others) * (otherWidth + gap);
    bool changed = false;

    for (size_t index = 0; index < choices.size(); ++index)
    {
        const Choice &choice = choices[index];
        const float width = index == 0 ? ownWidth : otherWidth;
        const bool selected = choice.all == m_showAllPlaythroughs && choice.rulesetId == m_rulesetFilter;

        if (button(prefix + "Scope" + std::to_string(index), {x, area.y, width, area.height}, choice.text, "tab", true,
                   selected)
            && !selected)
        {
            m_showAllPlaythroughs = choice.all;
            m_rulesetFilter = choice.rulesetId;
            changed = true;
        }

        x += width + gap;
    }

    return changed;
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
        const std::string id = index == 0 ? std::string() : m_rulesetFilters[index - 1];
        const std::string text = index == 0 ? Engine::tr("All") : rulesetDisplayName(id);
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

bool LoadGameScreen::drawSortButtons(const std::string &prefix)
{
    const Rect area = designRect(prefix + "SortButtons");
    const float gap = 6 * designScale();
    const float width = (area.width - gap) / 2;
    bool newestFirst = m_newestFirst;

    if (button(prefix + "SortByName", {area.x, area.y, width, area.height}, Engine::tr("Name"), "tab", true,
               !m_newestFirst))
    {
        newestFirst = false;
    }

    if (button(prefix + "SortByNewest", {area.x + width + gap, area.y, width, area.height}, Engine::tr("Newest"), "tab",
               true,
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

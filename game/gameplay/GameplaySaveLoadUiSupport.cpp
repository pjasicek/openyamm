#include "game/gameplay/GameplaySaveLoadUiSupport.h"

#include "engine/Localization.h"
#include "game/gameplay/SavePreviewImage.h"
#include "game/maps/SaveGame.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
struct CivilTime
{
    int year = 1168;
    int month = 0;
    int day = 1;
    int hour = 0;
    int minute = 0;
    int weekday = 0;
};

// The save slots' short day and month names, under their own contexts ("May" is short and long in English).
std::string weekdayShortName(int weekday)
{
    switch (weekday)
    {
        case 0: return Engine::trc("weekday short", "Mon");
        case 1: return Engine::trc("weekday short", "Tue");
        case 2: return Engine::trc("weekday short", "Wed");
        case 3: return Engine::trc("weekday short", "Thu");
        case 4: return Engine::trc("weekday short", "Fri");
        case 5: return Engine::trc("weekday short", "Sat");
        default: return Engine::trc("weekday short", "Sun");
    }
}

std::string monthShortName(int month)
{
    switch (month)
    {
        case 0: return Engine::trc("month short", "Jan");
        case 1: return Engine::trc("month short", "Feb");
        case 2: return Engine::trc("month short", "Mar");
        case 3: return Engine::trc("month short", "Apr");
        case 4: return Engine::trc("month short", "May");
        case 5: return Engine::trc("month short", "Jun");
        case 6: return Engine::trc("month short", "Jul");
        case 7: return Engine::trc("month short", "Aug");
        case 8: return Engine::trc("month short", "Sep");
        case 9: return Engine::trc("month short", "Oct");
        case 10: return Engine::trc("month short", "Nov");
        default: return Engine::trc("month short", "Dec");
    }
}

CivilTime civilTimeFromGameMinutes(float gameMinutes)
{
    int totalMinutes = static_cast<int>(std::floor(std::max(0.0f, gameMinutes)));
    CivilTime time = {};

    time.minute = totalMinutes % 60;
    totalMinutes /= 60;
    time.hour = totalMinutes % 24;
    int totalDays = totalMinutes / 24;
    time.weekday = totalDays % 7;
    time.day = totalDays + 1;
    return time;
}

std::string formatClock(const CivilTime &time)
{
    int hour = time.hour % 12;

    if (hour == 0)
    {
        hour = 12;
    }

    const std::string minute = (time.minute < 10 ? "0" : "") + std::to_string(time.minute);
    const std::string weekday = weekdayShortName(time.weekday);
    return time.hour >= 12
        ? Engine::tr("{weekday} {hour}:{minute} PM", {{"weekday", weekday}, {"hour", hour}, {"minute", minute}})
        : Engine::tr("{weekday} {hour}:{minute} AM", {{"weekday", weekday}, {"hour", hour}, {"minute", minute}});
}

std::string formatDate(const CivilTime &time)
{
    return Engine::tr("{month} {day}, {year}",
        {{"month", monthShortName(time.month)}, {"day", time.day}, {"year", time.year}});
}

std::string friendlySaveFileLabel(const std::filesystem::path &path)
{
    std::string stem = path.stem().string();

    if (!stem.empty())
    {
        stem[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(stem[0])));
    }

    return stem;
}

std::string normalizeSaveGameConflictName(const std::string &value)
{
    size_t begin = 0;
    size_t end = value.size();

    while (begin < end && std::isspace(static_cast<unsigned char>(value[begin])))
    {
        ++begin;
    }

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return toLowerCopy(value.substr(begin, end - begin));
}

} // namespace

void clampJournalMapState(GameplayUiController::JournalScreenState &journalScreen)
{
    journalScreen.mapZoomStep = std::clamp(
        journalScreen.mapZoomStep,
        0,
        static_cast<int>(GameplayJournalMapZoomLevels.size()) - 1);

    const int zoom = GameplayJournalMapZoomLevels[journalScreen.mapZoomStep];
    const float zoomFactor = static_cast<float>(zoom) / 384.0f;
    const float visibleWorldHalfExtent = GameplayJournalMapWorldHalfExtent / zoomFactor;
    const float maxOffset = std::max(0.0f, GameplayJournalMapWorldHalfExtent - visibleWorldHalfExtent);
    journalScreen.mapCenterX = std::clamp(journalScreen.mapCenterX, -maxOffset, maxOffset);
    journalScreen.mapCenterY = std::clamp(journalScreen.mapCenterY, -maxOffset, maxOffset);
}

std::string resolveSaveLocationName(const std::vector<MapStatsEntry> &mapEntries, const std::string &mapFileName)
{
    const std::string mapId = toLowerCopy(mapFileName);
    if (mapId.empty())
    {
        return {};
    }
    for (const MapStatsEntry &entry : mapEntries)
    {
        if (toLowerCopy(entry.fileName) == mapId || toLowerCopy(entry.canonicalId) == mapId)
        {
            // map_stats.txt names are English; the save lists show them in the interface language.
            return Engine::localize(entry.name);
        }
    }

    return mapFileName;
}

void refreshSaveGameSlots(
    GameplayUiController::SaveGameScreenState &saveGameScreen,
    const std::vector<MapStatsEntry> &mapEntries)
{
    saveGameScreen.slots.clear();
    std::filesystem::create_directories("saves");

    for (size_t index = 0; index < GameplaySaveLoadVisibleSlotCount; ++index)
    {
        GameplayUiController::SaveSlotSummary slot = {};
        slot.path = std::filesystem::path("saves") / ("save" + std::to_string(index + 1) + ".oysav");

        if (std::filesystem::exists(slot.path))
        {
            std::string error;
            const std::optional<GameSaveData> saveData = loadGameDataFromPath(slot.path, error);

            if (saveData)
            {
                slot.populated = true;
                slot.fileLabel = !saveData->saveName.empty() ? saveData->saveName : friendlySaveFileLabel(slot.path);
                slot.locationName = resolveSaveLocationName(mapEntries, saveData->mapFileName);
                const CivilTime civilTime = civilTimeFromGameMinutes(saveData->savedGameMinutes);
                slot.weekdayClockText = formatClock(civilTime);
                slot.dateText = formatDate(civilTime);

                if (!saveData->previewBmp.empty())
                {
                    SavePreviewImage::decodeBmpBytesToBgra(
                        saveData->previewBmp,
                        slot.previewWidth,
                        slot.previewHeight,
                        slot.previewPixelsBgra);
                }
            }
        }

        if (slot.fileLabel.empty())
        {
            // Compared as English by the save screen's input; translated where it is drawn.
            slot.fileLabel = "Empty";
        }

        saveGameScreen.slots.push_back(std::move(slot));
    }

    if (saveGameScreen.selectedIndex >= saveGameScreen.slots.size())
    {
        saveGameScreen.selectedIndex = 0;
    }

    saveGameScreen.scrollOffset = 0;
    saveGameScreen.editActive = false;
    saveGameScreen.editSlotIndex = 0;
    saveGameScreen.editBuffer.clear();
    saveGameScreen.errorText.clear();
}

void refreshLoadGameSlots(
    GameplayUiController::LoadGameScreenState &loadGameScreen,
    const std::vector<MapStatsEntry> &mapEntries)
{
    loadGameScreen.slots.clear();
    std::filesystem::create_directories("saves");

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator("saves"))
    {
        if (!entry.is_regular_file() || toLowerCopy(entry.path().extension().string()) != ".oysav")
        {
            continue;
        }

        std::string error;
        const std::optional<GameSaveData> saveData = loadGameDataFromPath(entry.path(), error);

        if (!saveData)
        {
            continue;
        }

        GameplayUiController::SaveSlotSummary slot = {};
        slot.path = entry.path();
        slot.fileLabel = !saveData->saveName.empty() ? saveData->saveName : friendlySaveFileLabel(entry.path());
        slot.locationName = resolveSaveLocationName(mapEntries, saveData->mapFileName);
        slot.populated = true;
        const CivilTime civilTime = civilTimeFromGameMinutes(saveData->savedGameMinutes);
        slot.weekdayClockText = formatClock(civilTime);
        slot.dateText = formatDate(civilTime);

        if (!saveData->previewBmp.empty())
        {
            SavePreviewImage::decodeBmpBytesToBgra(
                saveData->previewBmp,
                slot.previewWidth,
                slot.previewHeight,
                slot.previewPixelsBgra);
        }

        loadGameScreen.slots.push_back(std::move(slot));
    }

    std::sort(
        loadGameScreen.slots.begin(),
        loadGameScreen.slots.end(),
        [](const GameplayUiController::SaveSlotSummary &left, const GameplayUiController::SaveSlotSummary &right)
        {
            return compareSavesForDisplay(left.path, left.fileLabel, right.path, right.fileLabel);
        });

    if (loadGameScreen.selectedIndex >= loadGameScreen.slots.size())
    {
        loadGameScreen.selectedIndex = 0;
    }

    loadGameScreen.scrollOffset = 0;
}

bool saveGameNameConflictsWithExistingSlot(
    const GameplayUiController::SaveGameScreenState &saveGameScreen,
    const std::string &saveName,
    size_t targetSlotIndex)
{
    const std::string normalizedSaveName = normalizeSaveGameConflictName(saveName);

    if (normalizedSaveName.empty())
    {
        return false;
    }

    for (size_t slotIndex = 0; slotIndex < saveGameScreen.slots.size(); ++slotIndex)
    {
        if (slotIndex == targetSlotIndex)
        {
            continue;
        }

        const GameplayUiController::SaveSlotSummary &slot = saveGameScreen.slots[slotIndex];

        if (!slot.populated)
        {
            continue;
        }

        if (normalizeSaveGameConflictName(slot.fileLabel) == normalizedSaveName)
        {
            return true;
        }
    }

    return false;
}
} // namespace OpenYAMM::Game

#include "game/gameplay/GameplaySaveLoadUiSupport.h"

#include "game/gameplay/SavePreviewImage.h"
#include "game/maps/SaveGame.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
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

constexpr std::array<const char *, 7> WeekdayNames = {
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun"
};

constexpr std::array<const char *, 12> MonthNames = {
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec"
};

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

    const char *pMeridiem = time.hour >= 12 ? "PM" : "AM";
    return std::string(WeekdayNames[time.weekday])
        + " "
        + std::to_string(hour)
        + ":"
        + (time.minute < 10 ? "0" : "")
        + std::to_string(time.minute)
        + " "
        + pMeridiem;
}

std::string formatDate(const CivilTime &time)
{
    return std::string(MonthNames[time.month]) + " " + std::to_string(time.day) + ", " + std::to_string(time.year);
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
    for (const MapStatsEntry &entry : mapEntries)
    {
        if (toLowerCopy(entry.fileName) == toLowerCopy(mapFileName))
        {
            return entry.name;
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
            return compareSavePathsForDisplay(left.path, right.path);
        });

    if (loadGameScreen.selectedIndex >= loadGameScreen.slots.size())
    {
        loadGameScreen.selectedIndex = 0;
    }

    loadGameScreen.scrollOffset = 0;
}
} // namespace OpenYAMM::Game

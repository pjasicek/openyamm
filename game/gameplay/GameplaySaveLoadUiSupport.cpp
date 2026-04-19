#include "game/gameplay/GameplaySaveLoadUiSupport.h"

#include "game/maps/SaveGame.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
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

bool decodeBmpBytesToBgra(
    const std::vector<uint8_t> &bmpBytes,
    int &width,
    int &height,
    std::vector<uint8_t> &pixels)
{
    width = 0;
    height = 0;
    pixels.clear();

    if (bmpBytes.size() < 54 || bmpBytes[0] != 'B' || bmpBytes[1] != 'M')
    {
        return false;
    }

    auto readUint32Le =
        [&bmpBytes](size_t offset) -> uint32_t
        {
            return static_cast<uint32_t>(bmpBytes[offset])
                | (static_cast<uint32_t>(bmpBytes[offset + 1]) << 8)
                | (static_cast<uint32_t>(bmpBytes[offset + 2]) << 16)
                | (static_cast<uint32_t>(bmpBytes[offset + 3]) << 24);
        };
    auto readInt32Le =
        [&readUint32Le](size_t offset) -> int32_t
        {
            return static_cast<int32_t>(readUint32Le(offset));
        };
    const uint32_t pixelOffset = readUint32Le(10);
    const int32_t signedWidth = readInt32Le(18);
    const int32_t signedHeight = readInt32Le(22);
    const uint16_t bitsPerPixel =
        static_cast<uint16_t>(bmpBytes[28]) | (static_cast<uint16_t>(bmpBytes[29]) << 8);
    const bool topDown = signedHeight < 0;
    width = std::abs(signedWidth);
    height = std::abs(signedHeight);

    if (width <= 0 || height <= 0 || bitsPerPixel != 24)
    {
        return false;
    }

    const size_t rowStride = ((static_cast<size_t>(width) * 3u) + 3u) & ~3u;

    if (pixelOffset + rowStride * static_cast<size_t>(height) > bmpBytes.size())
    {
        return false;
    }

    pixels.resize(static_cast<size_t>(width) * static_cast<size_t>(height) * 4u);

    for (int y = 0; y < height; ++y)
    {
        const int sourceY = topDown ? y : (height - 1 - y);
        const size_t sourceRow = pixelOffset + rowStride * static_cast<size_t>(sourceY);

        for (int x = 0; x < width; ++x)
        {
            const size_t sourceIndex = sourceRow + static_cast<size_t>(x) * 3u;
            const size_t targetIndex = (static_cast<size_t>(y) * static_cast<size_t>(width) + static_cast<size_t>(x)) * 4u;
            pixels[targetIndex + 0] = bmpBytes[sourceIndex + 0];
            pixels[targetIndex + 1] = bmpBytes[sourceIndex + 1];
            pixels[targetIndex + 2] = bmpBytes[sourceIndex + 2];
            pixels[targetIndex + 3] = 255u;
        }
    }

    return true;
}
} // namespace

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
                    decodeBmpBytesToBgra(
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
            decodeBmpBytesToBgra(
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

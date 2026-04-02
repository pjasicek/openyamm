#include "game/ui/screens/LoadMenuScreen.h"

#include "game/maps/SaveGame.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdio>
#include <cmath>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
std::string toLowerCopy(const std::string &value)
{
    std::string normalized = value;

    for (char &character : normalized)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return normalized;
}

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
    static const std::array<const char *, 7> names = {
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    };
    return names[std::clamp(dayOfWeek, 1, 7) - 1];
}

std::string monthName(int month)
{
    static const std::array<const char *, 12> names = {
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    };
    return names[std::clamp(month, 1, 12) - 1];
}

std::string formatClock(const CivilTime &time)
{
    char buffer[32] = {};
    std::snprintf(
        buffer,
        sizeof(buffer),
        "%s %02d:%02d%s",
        weekdayName(time.dayOfWeek).c_str(),
        time.hour12,
        time.minute,
        time.isPm ? "PM" : "AM");
    return buffer;
}

std::string formatDate(const CivilTime &time)
{
    char buffer[64] = {};
    std::snprintf(buffer, sizeof(buffer), "%d %s %d", time.day, monthName(time.month).c_str(), time.year);
    return buffer;
}
}

LoadMenuScreen::LoadMenuScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<MapStatsEntry> &mapEntries,
    LoadAction loadAction,
    CancelAction cancelAction)
    : MenuScreenBase(assetFileSystem)
    , m_mapEntries(mapEntries)
    , m_loadAction(std::move(loadAction))
    , m_cancelAction(std::move(cancelAction))
{
}

AppMode LoadMenuScreen::mode() const
{
    return AppMode::LoadMenu;
}

void LoadMenuScreen::onEnter()
{
    refreshSaveSlots();
}

void LoadMenuScreen::drawScreen(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);

    constexpr float RootWidth = 640.0f;
    constexpr float RootHeight = 480.0f;
    constexpr size_t VisibleSlots = 14;
    const float scale = std::min(
        static_cast<float>(frameWidth()) / RootWidth,
        static_cast<float>(frameHeight()) / RootHeight);
    const float rootX = (static_cast<float>(frameWidth()) - RootWidth * scale) * 0.5f;
    const float rootY = (static_cast<float>(frameHeight()) - RootHeight * scale) * 0.5f;

    drawTexture("lsave640", Rect{rootX, rootY, RootWidth * scale, RootHeight * scale});

    if (!m_saveSlots.empty() && m_selectedIndex >= m_saveSlots.size())
    {
        m_selectedIndex = m_saveSlots.size() - 1;
    }

    if (mouseWheelDelta() > 0.0f && m_scrollOffset > 0)
    {
        --m_scrollOffset;
    }
    else if (mouseWheelDelta() < 0.0f && m_scrollOffset + VisibleSlots < m_saveSlots.size())
    {
        ++m_scrollOffset;
    }

    const Rect upButtonRect{rootX + 262.0f * scale, rootY + 58.0f * scale, 24.0f * scale, 24.0f * scale};
    const Rect downButtonRect{rootX + 262.0f * scale, rootY + 348.0f * scale, 24.0f * scale, 24.0f * scale};
    const Rect loadButtonRect{rootX + 512.0f * scale, rootY + 428.0f * scale, 92.0f * scale, 34.0f * scale};
    const Rect cancelButtonRect{rootX + 626.0f * scale, rootY + 428.0f * scale, 92.0f * scale, 34.0f * scale};

    if (drawButton(ButtonVisualSet{"bt_16xU", "", "bt_16xD"}, upButtonRect).clicked && m_scrollOffset > 0)
    {
        --m_scrollOffset;
    }

    if (drawButton(ButtonVisualSet{"bt_16xU", "", "bt_16xD"}, downButtonRect).clicked
        && m_scrollOffset + VisibleSlots < m_saveSlots.size())
    {
        ++m_scrollOffset;
    }

    const ButtonState loadButton =
        drawButton(ButtonVisualSet{"bu_loadU", "bu_loadH", "bu_loadD"}, loadButtonRect);
    const ButtonState cancelButton =
        drawButton(ButtonVisualSet{"bu_rtrnU", "bu_rtrnH", "bu_rtrnD"}, cancelButtonRect);

    if (cancelButton.clicked && m_cancelAction)
    {
        m_cancelAction();
        return;
    }

    const size_t visibleEnd = std::min(m_saveSlots.size(), m_scrollOffset + VisibleSlots);

    for (size_t rowIndex = m_scrollOffset; rowIndex < visibleEnd; ++rowIndex)
    {
        const float rowY = rootY + (64.0f + static_cast<float>(rowIndex - m_scrollOffset) * 21.0f) * scale;
        const Rect rowRect{rootX + 42.0f * scale, rowY, 214.0f * scale, 18.0f * scale};

        if (hitTest(rowRect) && leftMouseJustReleased())
        {
            m_selectedIndex = rowIndex;
        }

        drawDebugText(
            static_cast<int>(rowRect.x),
            static_cast<int>(rowRect.y),
            rowIndex == m_selectedIndex ? 0x0e : 0x0f,
            m_saveSlots[rowIndex].fileLabel);
    }

    if (!m_saveSlots.empty())
    {
        if (loadButton.clicked && m_loadAction)
        {
            m_loadAction(m_saveSlots[m_selectedIndex].path);
            return;
        }

        const SaveSlotSummary &selectedSlot = m_saveSlots[m_selectedIndex];
        drawDebugText(static_cast<int>(rootX + 326.0f * scale), static_cast<int>(rootY + 60.0f * scale), 0x0f, selectedSlot.locationName);
        drawDebugText(static_cast<int>(rootX + 326.0f * scale), static_cast<int>(rootY + 270.0f * scale), 0x0f, selectedSlot.weekdayClockText);
        drawDebugText(static_cast<int>(rootX + 326.0f * scale), static_cast<int>(rootY + 286.0f * scale), 0x0f, selectedSlot.dateText);
        drawDebugText(static_cast<int>(rootX + 350.0f * scale), static_cast<int>(rootY + 180.0f * scale), 0x08, "Preview unavailable");
    }
    else
    {
        drawDebugText(static_cast<int>(rootX + 48.0f * scale), static_cast<int>(rootY + 90.0f * scale), 0x0c, "No save files found");
    }

    const float trackHeight = 254.0f * scale;
    const float knobHeight = 48.0f * scale;
    float knobY = rootY + 136.0f * scale;

    if (m_saveSlots.size() > VisibleSlots)
    {
        const float range = static_cast<float>(m_saveSlots.size() - VisibleSlots);
        knobY = rootY + 88.0f * scale + ((trackHeight - knobHeight) * (static_cast<float>(m_scrollOffset) / range));
    }

    drawTexture("bt_32xU", Rect{rootX + 262.0f * scale, knobY, 24.0f * scale, knobHeight});
}

void LoadMenuScreen::refreshSaveSlots()
{
    m_saveSlots.clear();
    std::filesystem::create_directories("saves");

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator("saves"))
    {
        if (!entry.is_regular_file() || entry.path().extension() != ".oysav")
        {
            continue;
        }

        std::string error;
        const std::optional<GameSaveData> saveData = loadGameDataFromPath(entry.path(), error);

        if (!saveData)
        {
            continue;
        }

        SaveSlotSummary summary = {};
        summary.path = entry.path();
        summary.fileLabel = entry.path().filename().string();
        summary.locationName = saveData->mapFileName;

        for (const MapStatsEntry &mapEntry : m_mapEntries)
        {
            if (toLowerCopy(mapEntry.fileName) == toLowerCopy(saveData->mapFileName))
            {
                summary.locationName = mapEntry.name;
                break;
            }
        }

        const CivilTime civilTime = civilTimeFromGameMinutes(saveData->savedGameMinutes);
        summary.weekdayClockText = formatClock(civilTime);
        summary.dateText = formatDate(civilTime);
        m_saveSlots.push_back(std::move(summary));
    }

    std::sort(
        m_saveSlots.begin(),
        m_saveSlots.end(),
        [](const SaveSlotSummary &left, const SaveSlotSummary &right)
        {
            return left.path.filename().string() < right.path.filename().string();
        });

    m_selectedIndex = 0;
    m_scrollOffset = 0;
}
}

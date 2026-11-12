#include "game/ui/CalendarText.h"

#include "engine/Localization.h"

#include <algorithm>
#include <array>
#include <cstdio>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<std::string_view, 7> WeekdayNames = {
    Engine::trNoop("Monday"), Engine::trNoop("Tuesday"), Engine::trNoop("Wednesday"), Engine::trNoop("Thursday"),
    Engine::trNoop("Friday"), Engine::trNoop("Saturday"), Engine::trNoop("Sunday")};

constexpr std::array<std::string_view, 12> MonthNames = {
    Engine::trNoop("January"), Engine::trNoop("February"), Engine::trNoop("March"), Engine::trNoop("April"),
    Engine::trNoop("May"), Engine::trNoop("June"), Engine::trNoop("July"), Engine::trNoop("August"),
    Engine::trNoop("September"), Engine::trNoop("October"), Engine::trNoop("November"), Engine::trNoop("December")};

// The month as it stands in a date ("15 марта"): the same English under the context "date".
std::string monthNameInDate(int month)
{
    switch (std::clamp(month, 1, 12))
    {
    case 1: return Engine::trc("date", "January");
    case 2: return Engine::trc("date", "February");
    case 3: return Engine::trc("date", "March");
    case 4: return Engine::trc("date", "April");
    case 5: return Engine::trc("date", "May");
    case 6: return Engine::trc("date", "June");
    case 7: return Engine::trc("date", "July");
    case 8: return Engine::trc("date", "August");
    case 9: return Engine::trc("date", "September");
    case 10: return Engine::trc("date", "October");
    case 11: return Engine::trc("date", "November");
    default: return Engine::trc("date", "December");
    }
}
}

std::string weekdayName(int dayOfWeek)
{
    return Engine::tr(WeekdayNames[size_t(std::clamp(dayOfWeek, 1, 7) - 1)]);
}

std::string monthName(int month)
{
    return Engine::tr(MonthNames[size_t(std::clamp(month, 1, 12) - 1)]);
}

std::string formatCalendarDate(int day, int month, int year)
{
    return Engine::tr("{day} {month} {year}", {{"day", day}, {"month", monthNameInDate(month)}, {"year", year}});
}

std::string formatUtcDate(const std::string &utc)
{
    int year = 0;
    int month = 0;
    int day = 0;

    if (std::sscanf(utc.c_str(), "%d-%d-%d", &year, &month, &day) != 3 || month < 1 || month > 12)
    {
        return utc;
    }

    return formatCalendarDate(day, month, year);
}

std::string formatClockTime(int hour24, int minute)
{
    const int hour12 = hour24 % 12 == 0 ? 12 : hour24 % 12;
    char minutes[8] = {};
    std::snprintf(minutes, sizeof(minutes), "%02d", std::clamp(minute, 0, 59));
    return hour24 % 24 >= 12 ? Engine::tr("{hour}:{minute} PM", {{"hour", hour12}, {"minute", minutes}})
                             : Engine::tr("{hour}:{minute} AM", {{"hour", hour12}, {"minute", minutes}});
}
}

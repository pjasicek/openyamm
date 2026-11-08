#pragma once

#include <string>

namespace OpenYAMM::Game
{
// Names of the game's calendar in the interface language. Day of the week 1 (Monday) to 7, month 1 to 12.
std::string weekdayName(int dayOfWeek);
std::string monthName(int month);
// "15 March 1172": the month in the form a date takes (genitive in Russian), in the language's order.
std::string formatCalendarDate(int day, int month, int year);
// "9:05 PM" from a 24-hour time.
std::string formatClockTime(int hour24, int minute);
}

#include "game/ui/HudReading.h"

#include <doctest/doctest.h>

using OpenYAMM::Game::HudReading;

TEST_CASE("HUD reading is worked out once and reused until its age limit")
{
    HudReading<int, int> reading;
    int computed = 0;
    const auto compute = [&computed]() { return ++computed; };
    CHECK(reading.get(1, 1000, 100, compute) == 1);
    CHECK(reading.get(1, 1001, 100, compute) == 1);
    CHECK(reading.get(1, 1099, 100, compute) == 1);
    CHECK(computed == 1);
    // At the limit it is read again, and the limit counts from that reading.
    CHECK(reading.get(1, 1100, 100, compute) == 2);
    CHECK(reading.get(1, 1199, 100, compute) == 2);
    CHECK(reading.get(1, 1200, 100, compute) == 3);
}

TEST_CASE("HUD reading is worked out again at once for another subject")
{
    HudReading<int, int> reading;
    int computed = 0;
    const auto compute = [&computed]() { return ++computed; };
    CHECK(reading.get(1, 1000, 100, compute) == 1);
    CHECK(reading.get(2, 1001, 100, compute) == 2);
    CHECK(reading.get(2, 1002, 100, compute) == 2);
    CHECK(reading.get(1, 1003, 100, compute) == 3);
}

TEST_CASE("HUD reading does not trust a clock that went back, and reset forgets it")
{
    HudReading<int, int> reading;
    int computed = 0;
    const auto compute = [&computed]() { return ++computed; };
    CHECK(reading.get(1, 1000, 100, compute) == 1);
    CHECK(reading.get(1, 900, 100, compute) == 2);
    CHECK(reading.get(1, 901, 100, compute) == 2);
    reading.reset();
    CHECK(reading.get(1, 902, 100, compute) == 3);
    // A limit of zero reads every time.
    CHECK(reading.get(1, 902, 0, compute) == 4);
}

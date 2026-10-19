#include "engine/Utf8.h"

#include <doctest/doctest.h>

using namespace OpenYAMM::Engine;

TEST_CASE("UTF-8 decoder handles Cyrillic and supplementary characters")
{
    const std::vector<Utf8CodePoint> points = decodeUtf8("AБё😀");
    REQUIRE(points.size() == 4);
    CHECK(points[0].value == 'A');
    CHECK(points[1].value == 0x411);
    CHECK(points[2].value == 0x451);
    CHECK(points[3].value == 0x1f600);
    CHECK(utf8Length("Сила") == 4);

    size_t offset = 0;
    CHECK(nextUtf8CodePoint("Я", offset).value == 0x42f);
    CHECK(offset == std::string("Я").size());
}

TEST_CASE("UTF-8 editing never splits a code point")
{
    std::string text = "Ёж";
    eraseLastUtf8CodePoint(text);
    CHECK(text == "Ё");
    eraseLastUtf8CodePoint(text);
    CHECK(text.empty());
    CHECK(truncateUtf8("Привет", 3) == "При");
}

TEST_CASE("UTF-8 decoder preserves invalid legacy bytes")
{
    const std::string legacy(1, static_cast<char>(0x96));
    const std::vector<Utf8CodePoint> points = decodeUtf8(legacy);
    REQUIRE(points.size() == 1);
    CHECK(points[0].value == 0x96);
    CHECK(points[0].byteLength == 1);

    std::string text = std::string("A") + static_cast<char>(0x80);
    eraseLastUtf8CodePoint(text);
    CHECK(text == "A");
}

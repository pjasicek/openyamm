#include "engine/Utf8Text.h"

#include <doctest/doctest.h>

#include <string>
#include <vector>

using namespace OpenYAMM::Engine;

namespace
{
std::vector<uint32_t> charactersOf(const std::string &text)
{
    std::vector<uint32_t> points;

    for (const uint32_t point : Utf8::codePoints(text))
    {
        points.push_back(point);
    }

    return points;
}

// One unit per character, so the tests read widths as character counts.
float characterCount(const std::string &text)
{
    return static_cast<float>(Utf8::length(text));
}
}

TEST_CASE("UTF-8 decodes the well-formed sequences and reads any other byte as Windows-1252")
{
    CHECK_EQ(charactersOf("A\xc3\xa9\xd0\x96\xe4\xb8\xad\xf0\x9f\x98\x80"),
        std::vector<uint32_t>{'A', 0xe9, 0x416, 0x4e2d, 0x1f600});

    // Curly quotes and a dash as the imported English tables keep them.
    CHECK_EQ(charactersOf("\x93Ok\x94 \x96"), std::vector<uint32_t>{0x201c, 'O', 'k', 0x201d, ' ', 0x2013});

    // An overlong form, a surrogate, a point past U+10FFFF and a cut sequence are no characters: each byte stands alone.
    CHECK_EQ(charactersOf("\xc0\xaf"), std::vector<uint32_t>{0xc0, 0xaf});
    CHECK_EQ(charactersOf("\xe0\x80\xaf"), std::vector<uint32_t>{0xe0, 0x20ac, 0xaf});
    CHECK_EQ(charactersOf("\xed\xa0\x80").front(), 0xedu);
    CHECK_EQ(charactersOf("\xf4\x90\x80\x80").front(), 0xf4u);
    CHECK_EQ(charactersOf("\xe4\xb8"), std::vector<uint32_t>{0xe4, 0xb8});

    size_t offset = 1;
    CHECK_EQ(Utf8::next("x", offset), 0u);
    CHECK_EQ(offset, 1u);
}

TEST_CASE("UTF-8 encodes every length and Windows-1252 maps both ways")
{
    std::string text;

    for (const uint32_t point : {0x24u, 0xa2u, 0x20acu, 0x10348u})
    {
        Utf8::append(text, point);
    }

    CHECK_EQ(text, "\x24\xc2\xa2\xe2\x82\xac\xf0\x90\x8d\x88");
    CHECK_EQ(Utf8::normalized("\x93x\x94"), "\xe2\x80\x9cx\xe2\x80\x9d");
    CHECK_EQ(Utf8::toCp1252(0x20ac), std::optional<uint8_t>(0x80));
    CHECK_EQ(Utf8::toCp1252(0xe9), std::optional<uint8_t>(0xe9));
    // An unassigned byte stands for itself, so it finds its way back to the legacy glyph it names.
    CHECK_EQ(Utf8::toCp1252(0x81), std::optional<uint8_t>(0x81));
    CHECK_FALSE(Utf8::toCp1252(0x416).has_value());
}

TEST_CASE("UTF-8 counts and removes whole characters")
{
    std::string text = "\xc3\x89p\xc3\xa9\xd0\x96\xe4\xb8\xad";
    CHECK_EQ(Utf8::length(text), 5u);
    Utf8::popBack(text);
    CHECK_EQ(text, "\xc3\x89p\xc3\xa9\xd0\x96");
    Utf8::popBack(text);
    Utf8::popBack(text);
    Utf8::popBack(text);
    Utf8::popBack(text);
    CHECK(text.empty());
    Utf8::popBack(text);
    CHECK(text.empty());
}

TEST_CASE("UTF-8 capitals and small letters of the Latin, Greek and Cyrillic alphabets")
{
    CHECK_EQ(Utf8::upper("\xc3\xa9p\xc3\xa9\xc3\xbf \xce\xbb\xcf\x82 \xd0\xb6\xd1\x91 \xc5\x82"),
        "\xc3\x89P\xc3\x89\xc5\xb8 \xce\x9b\xce\xa3 \xd0\x96\xd0\x81 \xc5\x81");
    CHECK_EQ(Utf8::lower("\xc3\x89P\xc3\x89\xc5\xb8 \xce\x9b \xd0\x96\xd0\x81 \xc5\x81"),
        "\xc3\xa9p\xc3\xa9\xc3\xbf \xce\xbb \xd0\xb6\xd1\x91 \xc5\x82");
    // Signs without case stay.
    CHECK_EQ(Utf8::upper("\xc3\x97\xc3\xb7 1 \xe4\xb8\xad"), "\xc3\x97\xc3\xb7 1 \xe4\xb8\xad");
}

TEST_CASE("typed text keeps whole characters within its length and drops control characters")
{
    std::string typed = "ab";
    Utf8::appendPrintable(typed, "c\x01\t\xd0\x96\xd0\x97\xd0\x98", 5);
    CHECK_EQ(typed, "abc\xd0\x96\xd0\x97");
    Utf8::appendPrintable(typed, "z", 5);
    CHECK_EQ(typed, "abc\xd0\x96\xd0\x97");
}

TEST_CASE("wrapping breaks at spaces and around CJK characters, and gives a word wider than a line its own line")
{
    CHECK_EQ(Utf8::wrap("the quick brown fox", 9, characterCount),
        std::vector<std::string>{"the quick", "brown fox"});
    CHECK_EQ(Utf8::wrap("\xd1\x81\xd0\xbb\xd0\xbe\xd0\xb2\xd0\xbe \xd0\xb7\xd0\xb0 \xd1\x81\xd0\xbb\xd0\xbe\xd0\xb2\xd0\xbe", 8,
                 characterCount),
        std::vector<std::string>{"\xd1\x81\xd0\xbb\xd0\xbe\xd0\xb2\xd0\xbe \xd0\xb7\xd0\xb0",
            "\xd1\x81\xd0\xbb\xd0\xbe\xd0\xb2\xd0\xbe"});
    CHECK_EQ(Utf8::wrap("abcdefghij", 4, characterCount), std::vector<std::string>{"abcdefghij"});
    CHECK_EQ(Utf8::wrap("ab abcdefghij cd", 4, characterCount), std::vector<std::string>{"ab", "abcdefghij", "cd"});
    // A tab is no break: it stays in its word, as the HUD always kept it.
    CHECK_EQ(Utf8::wrap("a\tb c", 3, characterCount), std::vector<std::string>{"a\tb", "c"});

    // Six Han characters and a full stop: the stop never starts a line, it stays with the character before it.
    const std::string han = "\xe4\xb8\xad\xe6\x96\x87\xe5\xad\x97\xe7\xac\xa6\xe6\xb5\x8b\xe8\xaf\x95";
    const std::string stop = "\xe3\x80\x82";
    CHECK_EQ(Utf8::wrap(han + stop, 3, characterCount),
        std::vector<std::string>{"\xe4\xb8\xad\xe6\x96\x87\xe5\xad\x97", "\xe7\xac\xa6\xe6\xb5\x8b",
            "\xe8\xaf\x95" + stop});
    CHECK_EQ(Utf8::wrap("ab " + han, 5, characterCount),
        std::vector<std::string>{"ab \xe4\xb8\xad\xe6\x96\x87", "\xe5\xad\x97\xe7\xac\xa6\xe6\xb5\x8b\xe8\xaf\x95"});

    // A colour code ("\f" and five digits) between Han characters is never cut: the party creation screen once
    // split it and showed the digits.
    const std::string coloured = "\xe4\xb8\xad\f655166\f00000\xe6\x96\x87";
    for (const std::string &line : Utf8::wrap(coloured + coloured + coloured, 2, characterCount))
    {
        for (size_t code = line.find('\f'); code != std::string::npos; code = line.find('\f', code + 1))
        {
            CHECK_GE(line.size(), code + 6);
        }

        CHECK_NE(line.front(), '6');
        CHECK_NE(line.front(), '0');
    }
}

TEST_CASE("wrapping keeps line breaks, adds no line for a final newline and gives an empty text one empty line")
{
    CHECK_EQ(Utf8::wrap("one\r\ntwo\n", 10, characterCount), std::vector<std::string>{"one", "two"});
    CHECK_EQ(Utf8::wrap("one\n\n", 10, characterCount), std::vector<std::string>{"one", ""});
    CHECK_EQ(Utf8::wrap("\n", 10, characterCount), std::vector<std::string>{""});
    CHECK_EQ(Utf8::wrap("", 10, characterCount), std::vector<std::string>{""});
    CHECK_EQ(Utf8::wrap("  lead", 10, characterCount), std::vector<std::string>{"lead"});
    CHECK_EQ(Utf8::wrap("no limit here", 0, characterCount), std::vector<std::string>{"no limit here"});
}

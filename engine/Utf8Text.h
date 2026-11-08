#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

// Text by characters rather than bytes. The engine's text is UTF-8, but the tables imported from the original games
// still hold single Windows-1252 bytes (curly quotes, dashes, accented names), so a byte that does not begin a
// well-formed UTF-8 sequence is read as that code page instead of being rejected.
namespace OpenYAMM::Engine::Utf8
{
// The character a Windows-1252 byte stands for. Bytes below 0x80 and from 0xa0 are Latin-1 already; the five bytes the
// code page leaves unassigned stand for themselves.
constexpr uint32_t fromCp1252(uint8_t byte)
{
    switch (byte)
    {
    case 0x80: return 0x20ac;
    case 0x82: return 0x201a;
    case 0x83: return 0x0192;
    case 0x84: return 0x201e;
    case 0x85: return 0x2026;
    case 0x86: return 0x2020;
    case 0x87: return 0x2021;
    case 0x88: return 0x02c6;
    case 0x89: return 0x2030;
    case 0x8a: return 0x0160;
    case 0x8b: return 0x2039;
    case 0x8c: return 0x0152;
    case 0x8e: return 0x017d;
    case 0x91: return 0x2018;
    case 0x92: return 0x2019;
    case 0x93: return 0x201c;
    case 0x94: return 0x201d;
    case 0x95: return 0x2022;
    case 0x96: return 0x2013;
    case 0x97: return 0x2014;
    case 0x98: return 0x02dc;
    case 0x99: return 0x2122;
    case 0x9a: return 0x0161;
    case 0x9b: return 0x203a;
    case 0x9c: return 0x0153;
    case 0x9e: return 0x017e;
    case 0x9f: return 0x0178;
    default: return byte;
    }
}

// The Windows-1252 byte of a character, when the code page has one.
inline std::optional<uint8_t> toCp1252(uint32_t point)
{
    if (point < 0x80 || (point >= 0xa0 && point <= 0xff))
    {
        return uint8_t(point);
    }

    for (unsigned byte = 0x80; byte < 0xa0; ++byte)
    {
        if (fromCp1252(uint8_t(byte)) == point)
        {
            return uint8_t(byte);
        }
    }

    return std::nullopt;
}

struct Character
{
    uint32_t point = 0;
    // Bytes it takes in the text: 0 past the end, 1 for ASCII and a byte read as Windows-1252.
    size_t size = 0;
};

// The character at offset. Well-formed UTF-8 follows table 3-7 of the Unicode standard: the second byte's narrower
// range is what rules out overlong forms, surrogates and points past U+10FFFF.
inline Character decode(std::string_view text, size_t offset)
{
    if (offset >= text.size())
    {
        return {};
    }

    const uint8_t lead = uint8_t(text[offset]);

    if (lead < 0x80)
    {
        return {lead, 1};
    }

    size_t size = 0;
    uint32_t point = 0;
    uint8_t secondLow = 0x80;
    uint8_t secondHigh = 0xbf;

    if (lead >= 0xc2 && lead <= 0xdf)
    {
        size = 2;
        point = lead & 0x1fu;
    }
    else if (lead >= 0xe0 && lead <= 0xef)
    {
        size = 3;
        point = lead & 0x0fu;
        secondLow = lead == 0xe0 ? 0xa0 : 0x80;
        secondHigh = lead == 0xed ? 0x9f : 0xbf;
    }
    else if (lead >= 0xf0 && lead <= 0xf4)
    {
        size = 4;
        point = lead & 0x07u;
        secondLow = lead == 0xf0 ? 0x90 : 0x80;
        secondHigh = lead == 0xf4 ? 0x8f : 0xbf;
    }

    if (size == 0 || offset + size > text.size())
    {
        return {fromCp1252(lead), 1};
    }

    for (size_t index = 1; index < size; ++index)
    {
        const uint8_t byte = uint8_t(text[offset + index]);
        const uint8_t low = index == 1 ? secondLow : 0x80;
        const uint8_t high = index == 1 ? secondHigh : 0xbf;

        if (byte < low || byte > high)
        {
            return {fromCp1252(lead), 1};
        }

        point = (point << 6) | (byte & 0x3fu);
    }

    return {point, size};
}

// The character at offset, moving offset past it; 0 at the end, where offset stays.
inline uint32_t next(std::string_view text, size_t &offset)
{
    const Character character = decode(text, offset);
    offset += character.size;
    return character.point;
}

// The characters of a text, for a range-for loop.
class CodePoints
{
public:
    class Iterator
    {
    public:
        Iterator(std::string_view text, size_t offset) : m_text(text), m_offset(offset) {}

        uint32_t operator*() const { return decode(m_text, m_offset).point; }

        Iterator &operator++()
        {
            m_offset += decode(m_text, m_offset).size;
            return *this;
        }

        bool operator!=(const Iterator &other) const { return m_offset != other.m_offset; }

    private:
        std::string_view m_text;
        size_t m_offset = 0;
    };

    explicit CodePoints(std::string_view text) : m_text(text) {}

    Iterator begin() const { return {m_text, 0}; }
    Iterator end() const { return {m_text, m_text.size()}; }

private:
    std::string_view m_text;
};

inline CodePoints codePoints(std::string_view text)
{
    return CodePoints(text);
}

// Appends a character as UTF-8.
inline void append(std::string &text, uint32_t point)
{
    if (point < 0x80)
    {
        text += char(point);
        return;
    }

    const int size = point < 0x800 ? 2 : point < 0x10000 ? 3 : 4;
    constexpr uint8_t LeadMarks[] = {0, 0, 0xc0, 0xe0, 0xf0};
    text += char(LeadMarks[size] | (point >> (6 * (size - 1))));

    for (int shift = 6 * (size - 2); shift >= 0; shift -= 6)
    {
        text += char(0x80 | ((point >> shift) & 0x3fu));
    }
}

// The text with each character replaced by what convert gives for it, as UTF-8.
template <typename Convert>
std::string mapped(std::string_view text, const Convert &convert)
{
    std::string result;
    result.reserve(text.size());

    for (const uint32_t point : codePoints(text))
    {
        append(result, convert(point));
    }

    return result;
}

// The text as well-formed UTF-8: its Windows-1252 bytes become the characters they stand for.
inline std::string normalized(std::string_view text)
{
    return mapped(text, [](uint32_t point) { return point; });
}

// The capital of a small letter of the Latin, Greek and Cyrillic alphabets; other characters stay as they are.
inline uint32_t upper(uint32_t point)
{
    if ((point >= 'a' && point <= 'z') || (point >= 0xe0 && point <= 0xfe && point != 0xf7)
        || (point >= 0x3b1 && point <= 0x3cb && point != 0x3c2) || (point >= 0x430 && point <= 0x44f))
    {
        return point - 0x20;
    }

    if (point == 0xff)
    {
        return 0x178;
    }

    if (point == 0x3c2)
    {
        return 0x3a3;
    }

    if (point >= 0x450 && point <= 0x45f)
    {
        return point - 0x50;
    }

    // Latin Extended-A pairs a capital with the small letter after it, in two runs offset by the unpaired ĸ and ŉ.
    if (((point >= 0x100 && point <= 0x137) || (point >= 0x14a && point <= 0x177)) && point % 2 == 1)
    {
        return point - 1;
    }

    if (((point >= 0x139 && point <= 0x148) || (point >= 0x179 && point <= 0x17e)) && point % 2 == 0)
    {
        return point - 1;
    }

    return point;
}

inline std::string upper(std::string_view text)
{
    return mapped(text, [](uint32_t point) { return upper(point); });
}

// The small letter of a capital of the Latin, Greek and Cyrillic alphabets; other characters stay as they are.
inline uint32_t lower(uint32_t point)
{
    if ((point >= 'A' && point <= 'Z') || (point >= 0xc0 && point <= 0xde && point != 0xd7)
        || (point >= 0x391 && point <= 0x3ab && point != 0x3a2) || (point >= 0x410 && point <= 0x42f))
    {
        return point + 0x20;
    }

    if (point == 0x178)
    {
        return 0xff;
    }

    if (point >= 0x400 && point <= 0x40f)
    {
        return point + 0x50;
    }

    if (((point >= 0x100 && point <= 0x137) || (point >= 0x14a && point <= 0x177)) && point % 2 == 0)
    {
        return point + 1;
    }

    if (((point >= 0x139 && point <= 0x148) || (point >= 0x179 && point <= 0x17e)) && point % 2 == 1)
    {
        return point + 1;
    }

    return point;
}

inline std::string lower(std::string_view text)
{
    return mapped(text, [](uint32_t point) { return lower(point); });
}

// The text with its first character as a capital ("меч" → "Меч"), for a name shown at the start of a sentence.
inline std::string capitalizedFirst(std::string_view text)
{
    if (text.empty())
    {
        return {};
    }

    const Character first = decode(text, 0);
    std::string result;
    append(result, upper(first.point));
    result.append(text.substr(first.size));
    return result;
}

// The number of characters.
inline size_t length(std::string_view text)
{
    size_t count = 0;

    for (size_t offset = 0; offset < text.size(); offset += decode(text, offset).size)
    {
        ++count;
    }

    return count;
}

// Removes the last character, all of its bytes.
inline void popBack(std::string &text)
{
    size_t lastStart = 0;

    for (size_t offset = 0; offset < text.size(); offset += decode(text, offset).size)
    {
        lastStart = offset;
    }

    text.resize(lastStart);
}

// Whether typed text may take the character: no control character, byte order mark or replacement character.
inline bool isTypeable(uint32_t point)
{
    const bool control = point < 0x20 || (point >= 0x7f && point < 0xa0);
    return !control && point != 0xfeff && point != 0xfffd;
}

// Appends the characters of input that accept() takes to typed text, while it holds fewer than maximumCharacters.
template <typename Accept>
void appendTyped(std::string &typed, std::string_view input, size_t maximumCharacters, const Accept &accept)
{
    size_t count = length(typed);

    for (size_t offset = 0; offset < input.size() && count < maximumCharacters;)
    {
        const Character character = decode(input, offset);

        if (accept(character.point))
        {
            typed.append(input.substr(offset, character.size));
            ++count;
        }

        offset += character.size;
    }
}

// Appends the typeable characters of input to typed text, while it holds fewer than maximumCharacters.
inline void appendPrintable(std::string &typed, std::string_view input, size_t maximumCharacters)
{
    appendTyped(typed, input, maximumCharacters, isTypeable);
}

// Characters of scripts written without spaces between words (CJK ideographs, kana, Hangul syllables, full-width
// forms): a line may break before and after each of them.
inline bool breaksAround(uint32_t point)
{
    return (point >= 0x2e80 && point <= 0x2fdf) // CJK and Kangxi radicals
        || (point >= 0x3000 && point <= 0x30ff) // CJK punctuation, hiragana, katakana
        || (point >= 0x3400 && point <= 0x4dbf) // CJK extension A
        || (point >= 0x4e00 && point <= 0x9fff) // CJK unified ideographs
        || (point >= 0xac00 && point <= 0xd7a3) // Hangul syllables
        || (point >= 0xf900 && point <= 0xfaff) // CJK compatibility ideographs
        || (point >= 0xff00 && point <= 0xffef) // half-width and full-width forms
        || (point >= 0x20000 && point <= 0x3134f); // CJK extensions B to G
}

// Closing punctuation of those scripts, which must not begin a line: it stays with the character before it.
inline bool staysWithPrevious(uint32_t point)
{
    switch (point)
    {
    case 0x3001: // 、
    case 0x3002: // 。
    case 0x3009: // 〉
    case 0x300b: // 》
    case 0x300d: // 」
    case 0x300f: // 』
    case 0x3011: // 】
    case 0xff01: // ！
    case 0xff09: // ）
    case 0xff0c: // ，
    case 0xff0e: // ．
    case 0xff1a: // ：
    case 0xff1b: // ；
    case 0xff1f: // ？
        return true;
    default:
        return false;
    }
}

// The text in lines that measure() finds no wider than maxWidth. Lines break at spaces and newlines and around the
// characters breaksAround() names; a word wider than a line keeps a line of its own. A final newline adds no empty
// line; an empty text is one empty line.
template <typename Measure>
std::vector<std::string> wrap(std::string_view text, float maxWidth, const Measure &measure)
{
    if (maxWidth <= 0.0f)
    {
        return {std::string(text)};
    }

    std::vector<std::string> lines(1);

    // Puts a piece on the current line, after a space when spaced, or on a new line when it does not fit there.
    const auto place =
        [&lines, &measure, maxWidth](const std::string &piece, bool spaced)
        {
            if (piece.empty())
            {
                return;
            }

            std::string &current = lines.back();

            if (current.empty())
            {
                current = piece;
                return;
            }

            const std::string joined = current + (spaced ? " " : "") + piece;

            if (measure(joined) <= maxWidth)
            {
                current = joined;
                return;
            }

            lines.push_back(piece);
        };

    std::string word;
    bool spaceBeforeWord = false;
    bool wordEndsBreakable = false;

    const auto endWord =
        [&]()
        {
            place(word, spaceBeforeWord);
            spaceBeforeWord = false;
            wordEndsBreakable = false;
            word.clear();
        };

    for (size_t offset = 0; offset < text.size();)
    {
        const Character character = decode(text, offset);
        const std::string_view bytes = text.substr(offset, character.size);
        offset += character.size;

        if (character.point == '\r')
        {
            continue;
        }

        if (character.point == '\n')
        {
            endWord();
            lines.emplace_back();
            continue;
        }

        if (character.point == ' ')
        {
            if (!word.empty())
            {
                endWord();
            }

            spaceBeforeWord = true;
            continue;
        }

        const bool breakable = breaksAround(character.point);
        const bool attached = staysWithPrevious(character.point);

        if (!word.empty() && (wordEndsBreakable || breakable) && !attached)
        {
            endWord();
        }

        word.append(bytes);
        wordEndsBreakable = breakable;
    }

    endWord();

    if (lines.size() > 1 && lines.back().empty())
    {
        lines.pop_back();
    }

    return lines;
}
}

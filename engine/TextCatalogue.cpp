#include "engine/TextCatalogue.h"

#include "engine/AssetFileSystem.h"
#include "engine/TextTable.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Engine
{
namespace
{
constexpr const char *Windows1252 = "windows-1252";
constexpr const char *Windows1251 = "windows-1251";

// Bytes 0x80-0x9f of windows-1252; 0 where the code page assigns nothing.
constexpr std::array<uint32_t, 32> Windows1252High = {
    0x20ac, 0x0000, 0x201a, 0x0192, 0x201e, 0x2026, 0x2020, 0x2021,
    0x02c6, 0x2030, 0x0160, 0x2039, 0x0152, 0x0000, 0x017d, 0x0000,
    0x0000, 0x2018, 0x2019, 0x201c, 0x201d, 0x2022, 0x2013, 0x2014,
    0x02dc, 0x2122, 0x0161, 0x203a, 0x0153, 0x0000, 0x017e, 0x0178
};

// Bytes 0x80-0xbf of windows-1251; 0xc0-0xff are А-я in order.
constexpr std::array<uint32_t, 64> Windows1251High = {
    0x0402, 0x0403, 0x201a, 0x0453, 0x201e, 0x2026, 0x2020, 0x2021,
    0x20ac, 0x2030, 0x0409, 0x2039, 0x040a, 0x040c, 0x040b, 0x040f,
    0x0452, 0x2018, 0x2019, 0x201c, 0x201d, 0x2022, 0x2013, 0x2014,
    0x0000, 0x2122, 0x0459, 0x203a, 0x045a, 0x045c, 0x045b, 0x045f,
    0x00a0, 0x040e, 0x045e, 0x0408, 0x00a4, 0x0490, 0x00a6, 0x00a7,
    0x0401, 0x00a9, 0x0404, 0x00ab, 0x00ac, 0x00ad, 0x00ae, 0x0407,
    0x00b0, 0x00b1, 0x0406, 0x0456, 0x0491, 0x00b5, 0x00b6, 0x00b7,
    0x0451, 0x2116, 0x0454, 0x00bb, 0x0458, 0x0405, 0x0455, 0x0457
};

bool isSupportedEncoding(const std::string &encoding)
{
    return encoding == Windows1252 || encoding == Windows1251;
}

// A catalogue entry whose English text formats values, such as "%s hits %s for %lu damage". Text drawn after
// formatting is matched against the literal segments, and the values go into the translated segments in order.
struct CataloguePattern
{
    std::vector<std::string> literals;
    // 's' for text, 'd' for an integer; one per value.
    std::string conversions;
    std::vector<std::string> translatedLiterals;
    size_t literalSize = 0;
    // Short entries such as "the %s" apply only to names that the catalogue itself translates.
    bool requiresKnownValue = false;
};

struct TextHash
{
    using is_transparent = void;

    size_t operator()(std::string_view text) const
    {
        return std::hash<std::string_view>()(text);
    }
};

std::map<std::string, std::string, std::less<>> g_catalogue;
std::vector<CataloguePattern> g_patterns;
std::string g_languageId = EnglishLanguageId;
std::string g_encoding = Windows1252;
std::atomic<uint32_t> g_catalogueGeneration = 0;

// Formatted text repeats every frame; each thread keeps its matches. Results stay valid until the catalogue reloads,
// except the few beyond the cache limit, which rotate through a short ring.
struct PatternMatchCache
{
    static constexpr size_t MaxEntries = 4096;

    uint32_t generation = 0;
    std::unordered_map<std::string, std::optional<std::string>, TextHash, std::equal_to<>> results;
    std::array<std::string, 16> overflow;
    size_t nextOverflow = 0;
};

thread_local PatternMatchCache t_patternMatchCache;

// For translators: with OPENYAMM_UNTRANSLATED_TEXT_LOG=<file>, each text with English words that the loaded catalogue
// does not translate is appended to the file once, digit runs written as %d and control characters escaped (\\n, \\t,
// \\f), so that the lines can become catalogue entries. Wrapped and shortened texts also log their pieces.
void logUntranslatedText(std::string_view text)
{
    static const char *pPath = std::getenv("OPENYAMM_UNTRANSLATED_TEXT_LOG");

    if (pPath == nullptr || *pPath == '\0')
    {
        return;
    }

    std::string shape;
    bool words = false;

    for (size_t index = 0; index < text.size(); ++index)
    {
        const unsigned char character = static_cast<unsigned char>(text[index]);

        // Bytes of the language's code page: a translation, or a piece of one that wrapping measures.
        if (character >= 0x80)
        {
            return;
        }

        words = words
            || (index > 0 && std::isalpha(character) && std::isalpha(static_cast<unsigned char>(text[index - 1])));

        if (std::isdigit(character))
        {
            if (!shape.ends_with("%d"))
            {
                shape += "%d";
            }
        }
        else if (character == '\n')
        {
            shape += "\\n";
        }
        else if (character == '\t')
        {
            shape += "\\t";
        }
        else if (character == '\f')
        {
            shape += "\\f";
        }
        else if (character != '\r')
        {
            shape += static_cast<char>(character);
        }
    }

    static std::mutex mutex;
    static std::unordered_set<std::string> logged;
    std::lock_guard<std::mutex> lock(mutex);

    if (words && logged.insert(shape).second)
    {
        std::ofstream(pPath, std::ios::app) << shape << '\n';
    }
}

// Splits printf-style text into literal segments around %s, %d, %i and %u values with optional flags, width and
// length. %% is a literal percent; anything else, such as the %31 codes of story texts, stays literal.
struct FormatSegments
{
    // One more literal than conversions: the text before, between and after the values.
    std::vector<std::string> literals;
    std::string conversions;
};

FormatSegments splitFormat(std::string_view text)
{
    std::vector<std::string> literals(1);
    std::string conversions;

    for (size_t index = 0; index < text.size(); ++index)
    {
        if (text[index] != '%')
        {
            literals.back() += text[index];
            continue;
        }

        if (index + 1 < text.size() && text[index + 1] == '%')
        {
            literals.back() += '%';
            ++index;
            continue;
        }

        size_t end = index + 1;

        while (end < text.size() && std::string_view("-+0#").find(text[end]) != std::string_view::npos)
        {
            ++end;
        }

        while (end < text.size() && std::isdigit(static_cast<unsigned char>(text[end])) != 0)
        {
            ++end;
        }

        while (end < text.size() && (text[end] == 'l' || text[end] == 'h'))
        {
            ++end;
        }

        const char conversion = end < text.size() ? text[end] : '\0';

        if (conversion != 's' && conversion != 'd' && conversion != 'i' && conversion != 'u')
        {
            literals.back() += '%';
            continue;
        }

        conversions += conversion == 's' ? 's' : 'd';
        literals.emplace_back();
        index = end;
    }

    return FormatSegments{std::move(literals), std::move(conversions)};
}

std::optional<CataloguePattern> makePattern(const std::string &key, const std::string &translation)
{
    FormatSegments source = splitFormat(key);
    FormatSegments target = splitFormat(translation);

    if (source.conversions.empty() || source.conversions != target.conversions)
    {
        return std::nullopt;
    }

    size_t letters = 0;

    for (size_t index = 0; index < source.literals.size(); ++index)
    {
        const std::string &literal = source.literals[index];

        // Adjacent values have no literal between them, so the text cannot be split back into values.
        if (index > 0 && index + 1 < source.literals.size() && literal.empty())
        {
            return std::nullopt;
        }

        letters += size_t(std::count_if(literal.begin(), literal.end(), [](char character)
            {
                return std::isalpha(static_cast<unsigned char>(character)) != 0;
            }));
    }

    // Entries such as "%s, %s" would match almost any text, so a short entry applies only when every text value is
    // itself translated by the catalogue: "the %s" for class titles, "%s, %s" for a proprietor and a title.
    const bool requiresKnownValue = letters < 4;

    if (requiresKnownValue && source.conversions.find('s') == std::string::npos)
    {
        return std::nullopt;
    }

    CataloguePattern pattern;
    pattern.requiresKnownValue = requiresKnownValue;

    for (const std::string &literal : source.literals)
    {
        pattern.literalSize += literal.size();
    }

    pattern.literals = std::move(source.literals);
    pattern.conversions = std::move(source.conversions);
    pattern.translatedLiterals = std::move(target.literals);
    return pattern;
}

// Matches the values from `index` on. A text value ends at the earliest following literal that lets the rest of the
// text match, so a multi-word topic still fits "%s %d Gold".
bool matchPatternValues(const CataloguePattern &pattern, std::string_view text, size_t index, size_t position,
    size_t end, std::vector<std::string_view> &values)
{
    if (index == pattern.conversions.size())
    {
        return position == end;
    }

    const bool last = index + 1 == pattern.conversions.size();
    const std::string &next = pattern.literals[index + 1];

    if (pattern.conversions[index] == 'd')
    {
        size_t valueEnd = position;

        if (valueEnd < end && text[valueEnd] == '-')
        {
            ++valueEnd;
        }

        const size_t digits = valueEnd;

        while (valueEnd < end && std::isdigit(static_cast<unsigned char>(text[valueEnd])) != 0)
        {
            ++valueEnd;
        }

        const bool nextMatches = last ? valueEnd == end
            : valueEnd + next.size() <= end && text.compare(valueEnd, next.size(), next) == 0;

        if (valueEnd == digits || !nextMatches)
        {
            return false;
        }

        values.push_back(text.substr(position, valueEnd - position));

        if (matchPatternValues(pattern, text, index + 1, valueEnd + (last ? 0 : next.size()), end, values))
        {
            return true;
        }

        values.pop_back();
        return false;
    }

    if (last)
    {
        if (end <= position)
        {
            return false;
        }

        values.push_back(text.substr(position, end - position));
        return true;
    }

    for (size_t valueEnd = text.find(next, position + 1);
        valueEnd != std::string_view::npos && valueEnd + next.size() <= end;
        valueEnd = text.find(next, valueEnd + 1))
    {
        values.push_back(text.substr(position, valueEnd - position));

        if (matchPatternValues(pattern, text, index + 1, valueEnd + next.size(), end, values))
        {
            return true;
        }

        values.pop_back();
    }

    return false;
}

std::optional<std::vector<std::string_view>> matchPattern(const CataloguePattern &pattern, std::string_view text)
{
    if (text.size() <= pattern.literalSize || !text.starts_with(pattern.literals.front())
        || !text.ends_with(pattern.literals.back()))
    {
        return std::nullopt;
    }

    std::vector<std::string_view> values;

    if (!matchPatternValues(pattern, text, 0, pattern.literals.front().size(),
            text.size() - pattern.literals.back().size(), values))
    {
        return std::nullopt;
    }

    return values;
}

std::optional<std::string> translateFormattedText(std::string_view text, bool translateFormattedValues)
{
    for (const CataloguePattern &pattern : g_patterns)
    {
        const std::optional<std::vector<std::string_view>> values = matchPattern(pattern, text);

        if (!values)
        {
            continue;
        }

        std::vector<std::string> translatedValues;
        bool allTextValuesKnown = true;

        for (size_t index = 0; index < values->size(); ++index)
        {
            // Text values are usually names from the game tables; translate those that the catalogue knows. A value
            // can be assembled itself, such as an item name with its enchantment inside a shop phrase.
            const std::string_view value = (*values)[index];

            if (pattern.conversions[index] != 's')
            {
                translatedValues.emplace_back(value);
                continue;
            }

            const auto found = g_catalogue.find(value);
            std::optional<std::string> translated = found != g_catalogue.end()
                ? std::optional<std::string>(found->second)
                : translateFormattedValues ? translateFormattedText(value, false) : std::nullopt;
            allTextValuesKnown = allTextValuesKnown && translated.has_value();
            translatedValues.push_back(translated ? std::move(*translated) : std::string(value));
        }

        if (pattern.requiresKnownValue && !allTextValuesKnown)
        {
            continue;
        }

        std::string result = pattern.translatedLiterals.front();

        for (size_t index = 0; index < translatedValues.size(); ++index)
        {
            result += translatedValues[index];
            result += pattern.translatedLiterals[index + 1];
        }

        return result;
    }

    return std::nullopt;
}

size_t readCatalogueEntries(const std::string &contents, const std::string &encoding,
    std::map<std::string, std::string, std::less<>> &catalogue)
{
    const std::optional<TextTable> table = TextTable::parseTabSeparated(contents);

    if (!table)
    {
        throw std::runtime_error("Could not parse the text catalogue");
    }

    for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
    {
        const std::vector<std::string> &row = table->getRow(rowIndex);

        if (row.size() != 2 || row[0].empty())
        {
            throw std::runtime_error("Text catalogue row " + std::to_string(rowIndex + 1)
                + " needs the English text and its translation");
        }

        // Game text is windows-1252; the translation is drawn in the language's code page.
        catalogue.insert_or_assign(encodeCodePageText(row[0], Windows1252), encodeCodePageText(row[1], encoding));
    }

    return table->getRowCount();
}

std::string languagePath(const std::string &language, const std::string &path)
{
    return "localization/" + language + "/" + path;
}

std::optional<InterfaceLanguage> readLanguage(const AssetFileSystem &assetFileSystem, const std::string &id)
{
    const std::optional<std::string> text = assetFileSystem.readTextFile(languagePath(id, "language.yml"));

    if (!text)
    {
        return std::nullopt;
    }

    InterfaceLanguage language;
    language.id = id;

    try
    {
        const YAML::Node node = YAML::Load(*text);
        language.name = node["name"].as<std::string>(id);
        language.encoding = node["encoding"].as<std::string>(Windows1252);
    }
    catch (const YAML::Exception &exception)
    {
        throw std::runtime_error("Invalid " + languagePath(id, "language.yml") + ": " + exception.what());
    }

    if (!isSupportedEncoding(language.encoding))
    {
        throw std::runtime_error(languagePath(id, "language.yml") + " names an unsupported encoding: "
            + language.encoding);
    }

    return language;
}
} // namespace

bool validLanguageId(std::string_view id)
{
    return !id.empty() && id.size() <= 16 && std::all_of(id.begin(), id.end(), [](char character)
        {
            return (character >= 'a' && character <= 'z') || (character >= '0' && character <= '9') || character == '-'
                || character == '_';
        });
}

uint32_t codePageCharacter(const std::string &encoding, uint8_t byte)
{
    if (byte < 0x20 || byte == 0x7f)
    {
        return 0;
    }

    if (byte < 0x80)
    {
        return byte;
    }

    if (encoding == Windows1251)
    {
        return byte >= 0xc0 ? 0x0410 + (byte - 0xc0) : Windows1251High[byte - 0x80];
    }

    return byte < 0xa0 ? Windows1252High[byte - 0x80] : byte;
}

std::string encodeCodePageText(std::string_view utf8Text, const std::string &encoding)
{
    if (!isSupportedEncoding(encoding))
    {
        throw std::runtime_error("Unsupported text encoding: " + encoding);
    }

    std::string result;
    result.reserve(utf8Text.size());

    for (size_t index = 0; index < utf8Text.size();)
    {
        const uint8_t first = static_cast<uint8_t>(utf8Text[index++]);

        if (first < 0x80)
        {
            result += static_cast<char>(first);
            continue;
        }

        const int continuationCount = first >= 0xc2 && first <= 0xdf ? 1 : first >= 0xe0 && first <= 0xef ? 2 : -1;

        if (continuationCount < 0 || index + continuationCount > utf8Text.size())
        {
            throw std::runtime_error("Text is not UTF-8");
        }

        uint32_t character = first & (continuationCount == 1 ? 0x1f : 0x0f);

        for (int continuation = 0; continuation < continuationCount; ++continuation)
        {
            const uint8_t byte = static_cast<uint8_t>(utf8Text[index++]);

            if ((byte & 0xc0) != 0x80)
            {
                throw std::runtime_error("Text is not UTF-8");
            }

            character = (character << 6) | (byte & 0x3f);
        }

        if ((continuationCount == 2 && character < 0x0800) || (character >= 0xd800 && character <= 0xdfff))
        {
            throw std::runtime_error("Text is not UTF-8");
        }

        bool found = false;

        for (int byte = 0x80; byte <= 0xff && !found; ++byte)
        {
            if (codePageCharacter(encoding, uint8_t(byte)) == character)
            {
                result += static_cast<char>(byte);
                found = true;
            }
        }

        if (!found)
        {
            throw std::runtime_error("Text has a character " + encoding + " lacks");
        }
    }

    return result;
}

std::string encodeTypedText(std::string_view utf8Text)
{
    std::string result;

    for (size_t index = 0; index < utf8Text.size();)
    {
        const uint8_t first = static_cast<uint8_t>(utf8Text[index]);
        const size_t length = first >= 0xf0 ? 4 : first >= 0xe0 ? 3 : first >= 0xc0 ? 2 : 1;

        try
        {
            result += encodeCodePageText(utf8Text.substr(index, length), g_encoding);
        }
        catch (const std::runtime_error &)
        {
            // A character the code page lacks, or no UTF-8: left out.
        }

        index += length;
    }

    return result;
}

std::string lowercaseCodePageText(std::string_view text, const std::string &encoding)
{
    std::string result(text);

    for (char &character : result)
    {
        const uint8_t byte = static_cast<uint8_t>(character);

        if (byte < 0x80)
        {
            character = static_cast<char>(std::tolower(byte));
            continue;
        }

        // Capitals of the Latin-1 and Cyrillic blocks, and those of the code pages' other letters.
        const uint32_t upper = codePageCharacter(encoding, byte);
        const uint32_t lower = (upper >= 0x00c0 && upper <= 0x00de && upper != 0x00d7)
                || (upper >= 0x0410 && upper <= 0x042f)
            ? upper + 0x20
            : upper >= 0x0400 && upper <= 0x040f ? upper + 0x50
            : upper == 0x0152 || upper == 0x0160 || upper == 0x017d || upper == 0x0490 ? upper + 1
            : upper == 0x0178 ? 0x00ff
            : 0;

        for (int candidate = 0x80; lower != 0 && candidate <= 0xff; ++candidate)
        {
            if (codePageCharacter(encoding, uint8_t(candidate)) == lower)
            {
                character = static_cast<char>(candidate);
                break;
            }
        }
    }

    return result;
}

std::vector<InterfaceLanguage> availableInterfaceLanguages(const AssetFileSystem &assetFileSystem)
{
    std::vector<InterfaceLanguage> languages = {{EnglishLanguageId, "English", Windows1252}};

    for (const std::string &entry : assetFileSystem.enumerate("localization"))
    {
        if (!validLanguageId(entry))
        {
            continue;
        }

        try
        {
            if (std::optional<InterfaceLanguage> language = readLanguage(assetFileSystem, entry))
            {
                languages.push_back(std::move(*language));
            }
        }
        catch (const std::runtime_error &exception)
        {
            std::cerr << "Interface language " << entry << " skipped: " << exception.what() << '\n';
        }
    }

    return languages;
}

void loadTextCatalogue(const AssetFileSystem &assetFileSystem, const std::string &language)
{
    const std::optional<InterfaceLanguage> definition =
        language == EnglishLanguageId || !validLanguageId(language) ? std::nullopt : readLanguage(assetFileSystem, language);

    if (!definition)
    {
        if (!language.empty() && language != EnglishLanguageId)
        {
            std::cerr << "Interface language " << language << " is not installed; the interface stays English\n";
        }

        g_catalogue.clear();
        g_patterns.clear();
        g_languageId = EnglishLanguageId;
        g_encoding = Windows1252;
        ++g_catalogueGeneration;
        return;
    }

    std::map<std::string, std::string, std::less<>> catalogue;
    size_t entries = 0;
    // Every .tsv of the language folder but the world's, in name order: a later file's entry wins.
    std::vector<std::string> files;

    for (const std::string &entry : assetFileSystem.enumerate("localization/" + language))
    {
        if (entry.ends_with(".tsv") && entry != "world_strings.tsv")
        {
            files.push_back(entry);
        }
    }

    std::sort(files.begin(), files.end());

    for (const std::string &file : files)
    {
        if (const std::optional<std::string> shared = assetFileSystem.readTextFile(languagePath(language, file)))
        {
            entries += readCatalogueEntries(*shared, definition->encoding, catalogue);
        }
    }

    // The active world's files overlay the engine's at the same paths, so its catalogue has a name of its own.
    size_t worldEntries = 0;

    if (const std::optional<std::string> world =
            assetFileSystem.readTextFile(languagePath(language, "world_strings.tsv")))
    {
        worldEntries = readCatalogueEntries(*world, definition->encoding, catalogue);
    }

    std::vector<CataloguePattern> patterns;

    for (const auto &[key, translation] : catalogue)
    {
        if (std::optional<CataloguePattern> pattern = makePattern(key, translation))
        {
            patterns.push_back(std::move(*pattern));
        }
    }

    // The most specific entry wins when several patterns match the same text.
    std::stable_sort(patterns.begin(), patterns.end(),
        [](const CataloguePattern &left, const CataloguePattern &right)
        {
            return left.literalSize > right.literalSize;
        });
    g_catalogue = std::move(catalogue);
    g_patterns = std::move(patterns);
    g_languageId = definition->id;
    g_encoding = definition->encoding;
    ++g_catalogueGeneration;
    std::cout << "Interface language " << definition->name << ": " << entries << " catalogue entries, " << worldEntries
              << " for the active world\n";
}

const std::string &interfaceLanguageId()
{
    return g_languageId;
}

const std::string &interfaceTextEncoding()
{
    return g_encoding;
}

std::string localizedAssetPath(const AssetFileSystem &assetFileSystem, const std::string &path)
{
    if (g_languageId == EnglishLanguageId)
    {
        return path;
    }

    std::string localized = languagePath(g_languageId, path);
    return assetFileSystem.exists(localized) ? localized : path;
}

std::string_view localizeDisplayText(std::string_view text)
{
    const auto found = g_catalogue.find(text);

    if (found != g_catalogue.end())
    {
        return found->second;
    }

    if (g_patterns.empty())
    {
        return text;
    }

    PatternMatchCache &cache = t_patternMatchCache;
    const uint32_t generation = g_catalogueGeneration.load(std::memory_order_relaxed);

    if (cache.generation != generation)
    {
        cache.results.clear();
        cache.generation = generation;
    }

    const auto cached = cache.results.find(text);

    if (cached != cache.results.end())
    {
        return cached->second ? std::string_view(*cached->second) : text;
    }

    std::optional<std::string> translated = translateFormattedText(text, true);

    if (!translated)
    {
        logUntranslatedText(text);
    }

    if (cache.results.size() < PatternMatchCache::MaxEntries)
    {
        const auto inserted = cache.results.emplace(std::string(text), std::move(translated)).first;
        return inserted->second ? std::string_view(*inserted->second) : text;
    }

    if (!translated)
    {
        return text;
    }

    std::string &slot = cache.overflow[cache.nextOverflow++ % cache.overflow.size()];
    slot = std::move(*translated);
    return slot;
}

std::string formatDisplayText(std::string_view format, std::initializer_list<std::string_view> values)
{
    FormatSegments segments = splitFormat(format);
    const auto found = g_catalogue.find(format);

    if (found != g_catalogue.end())
    {
        FormatSegments translated = splitFormat(found->second);

        if (translated.conversions == segments.conversions)
        {
            segments = std::move(translated);
        }
    }

    std::string result = segments.literals.front();
    size_t index = 0;

    for (const std::string_view value : values)
    {
        if (index >= segments.conversions.size())
        {
            break;
        }

        result += segments.conversions[index] == 's' ? localizeDisplayText(value) : value;
        result += segments.literals[++index];
    }

    return result;
}

bool hasTextCatalogue()
{
    return !g_catalogue.empty();
}
}

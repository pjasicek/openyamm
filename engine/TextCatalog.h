#pragma once

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

// Translations of the game's English text (devdocs/LOCALIZATION.md). The English text is the key: a catalogue maps it,
// with an optional context, to its translation. Files are gettext .po; this is our own reader, not the gettext library.
namespace OpenYAMM::Engine
{
// One entry of a .po file. An entry without translation, or marked fuzzy, translates nothing.
struct PoEntry
{
    std::string context;
    std::string english;
    std::string englishPlural;
    // One per plural form; a single one for an entry without a plural.
    std::vector<std::string> translations;
    bool fuzzy = false;
    int line = 0;
};

struct PoFile
{
    // Without the header (the entry whose English is empty).
    std::vector<PoEntry> entries;
    // The header's Plural-Forms value, empty when it has none.
    std::string pluralForms;
};

// The entries of .po text; nullopt with error set on malformed text. Obsolete entries (#~) are left out.
std::optional<PoFile> parsePoFile(std::string_view text, std::string &error);

// A gettext Plural-Forms rule: "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : ...);". The formula is C: n, numbers,
// parentheses, ?:, ||, &&, comparisons, + - * / % and !.
class PluralRule
{
public:
    static std::optional<PluralRule> parse(std::string_view pluralForms, std::string &error);
    // English's rule: one for 1, another for every other number.
    static PluralRule english();

    size_t formCount() const;
    // The form a number takes; 0 when the formula gives no valid form.
    size_t form(uint64_t number) const;

private:
    size_t m_formCount = 2;
    std::string m_formula = "n != 1";
};

// What a translation lost or changed of its English: {placeholders}, printf values (in order), story codes (%01) and
// colour codes (\f and five digits). Empty when the translation keeps them all.
std::string translationMismatch(std::string_view english, std::string_view translation);

// A named value for a text's {name} placeholder.
struct TextArgument
{
    TextArgument(std::string_view name, std::string_view value);
    TextArgument(std::string_view name, const std::string &value);
    TextArgument(std::string_view name, const char *pValue);
    TextArgument(std::string_view name, int value);
    TextArgument(std::string_view name, unsigned value);
    TextArgument(std::string_view name, long value);
    TextArgument(std::string_view name, unsigned long value);
    TextArgument(std::string_view name, long long value);
    TextArgument(std::string_view name, unsigned long long value);

    std::string name;
    std::string value;
};

// The text with each {name} of an argument replaced by its value. Braces naming no argument stay as they are, so text
// other code formats later (MAW's {add*2}) passes through.
std::string formatText(std::string_view text, std::span<const TextArgument> arguments);

// The pseudo-language: the text marked, accented and about a third longer ("Settings" becomes "[Séttíñgs···]"),
// keeping placeholders, printf values, story and colour codes and line breaks as they are.
std::string pseudoLocalize(std::string_view text);

// The translations of one language, merged from its files.
class TextCatalog
{
public:
    // Adds a file's translated entries. An entry without context takes defaultContext ("world:mm7" for a world's file).
    // Entries that change their English's placeholders or codes are refused and reported in warnings, as is a plural
    // rule that differs from one an earlier file gave.
    void add(const PoFile &file, std::string_view fileName, std::string_view defaultContext,
             std::vector<std::string> &warnings);

    // The translation of English text in a context ("" for none); nullptr when the catalogue has none.
    const std::string *find(std::string_view context, std::string_view english) const;
    // The translation of a plural entry for a number; nullptr when the catalogue has none.
    const std::string *findPlural(std::string_view context, std::string_view english, uint64_t number) const;
    // The translation a world's file gives the text, for a world's text shown in another world (an MM9 item carried
    // to Jadame, where "world:mm9" is not the active context): the first file context, in name order, that has one.
    const std::string *findInWorldFiles(std::string_view english) const;

    size_t size() const;
    bool empty() const;

private:
    static std::string key(std::string_view context, std::string_view english);

    std::unordered_map<std::string, std::vector<std::string>> m_translations;
    // The default contexts of the files added ("world:mm7"), sorted.
    std::vector<std::string> m_fileContexts;
    std::optional<PluralRule> m_pluralRule;
};
}

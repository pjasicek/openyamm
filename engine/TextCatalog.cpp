#include "engine/TextCatalog.h"

#include "engine/Utf8Text.h"

#include <algorithm>
#include <cctype>
#include <charconv>

namespace OpenYAMM::Engine
{
namespace
{
bool isAsciiDigit(char character)
{
    return character >= '0' && character <= '9';
}

bool isPlaceholderStart(char character)
{
    return (character >= 'a' && character <= 'z') || (character >= 'A' && character <= 'Z') || character == '_';
}

// The length of a {placeholder} at offset, 0 when none starts there. Its name begins with a letter; anything up to the
// closing brace belongs to it ({add*2}, {skill:1}), but not another brace or a line break.
size_t placeholderLength(std::string_view text, size_t offset)
{
    constexpr size_t MaximumLength = 64;

    if (offset + 2 >= text.size() || text[offset] != '{' || !isPlaceholderStart(text[offset + 1]))
    {
        return 0;
    }

    for (size_t index = offset + 2; index < text.size() && index - offset < MaximumLength; ++index)
    {
        const char character = text[index];

        if (character == '}')
        {
            return index - offset + 1;
        }

        if (character == '{' || character == '\n')
        {
            return 0;
        }
    }

    return 0;
}

// The length of a printf conversion at offset ("%d", "%-5.1f", "%%"), 0 when none starts there. A space is not taken
// as a flag, so "50% chance" holds no conversion.
size_t printfLength(std::string_view text, size_t offset)
{
    if (offset + 1 >= text.size() || text[offset] != '%')
    {
        return 0;
    }

    size_t index = offset + 1;

    if (text[index] == '%')
    {
        return 2;
    }

    while (index < text.size() && std::string_view("-+#0").find(text[index]) != std::string_view::npos)
    {
        ++index;
    }

    while (index < text.size() && isAsciiDigit(text[index]))
    {
        ++index;
    }

    if (index < text.size() && text[index] == '.')
    {
        ++index;

        while (index < text.size() && isAsciiDigit(text[index]))
        {
            ++index;
        }
    }

    while (index < text.size() && (text[index] == 'h' || text[index] == 'l' || text[index] == 'z'))
    {
        ++index;
    }

    if (index < text.size() && std::string_view("diouxXfFeEgGsc").find(text[index]) != std::string_view::npos)
    {
        return index - offset + 1;
    }

    return 0;
}

// Might and Magic's story code ("%01": the party's name and the like): a percent sign and two digits.
size_t storyCodeLength(std::string_view text, size_t offset)
{
    return offset + 2 < text.size() && text[offset] == '%' && isAsciiDigit(text[offset + 1])
            && isAsciiDigit(text[offset + 2])
        ? 3
        : 0;
}

// An inline colour: a form feed and five digits.
size_t colorCodeLength(std::string_view text, size_t offset)
{
    if (text[offset] != '\f' || offset + 5 >= text.size())
    {
        return 0;
    }

    for (size_t index = offset + 1; index <= offset + 5; ++index)
    {
        if (!isAsciiDigit(text[index]))
        {
            return 0;
        }
    }

    return 6;
}

enum class TokenKind
{
    Placeholder,
    Printf,
    StoryCode,
    ColorCode
};

struct Token
{
    TokenKind kind;
    size_t length = 0;
};

// The protected part of text starting at offset, if any: what a translation keeps and the pseudo-language leaves alone.
std::optional<Token> tokenAt(std::string_view text, size_t offset)
{
    if (const size_t length = placeholderLength(text, offset))
    {
        return Token{TokenKind::Placeholder, length};
    }

    if (const size_t length = printfLength(text, offset))
    {
        return Token{TokenKind::Printf, length};
    }

    if (const size_t length = storyCodeLength(text, offset))
    {
        return Token{TokenKind::StoryCode, length};
    }

    if (const size_t length = colorCodeLength(text, offset))
    {
        return Token{TokenKind::ColorCode, length};
    }

    return std::nullopt;
}

struct TextTokens
{
    std::vector<std::string> placeholders;
    std::vector<std::string> printf;
    std::vector<std::string> storyCodes;
    std::vector<std::string> colorCodes;
};

TextTokens tokensOf(std::string_view text)
{
    TextTokens tokens;

    for (size_t offset = 0; offset < text.size();)
    {
        const std::optional<Token> token = tokenAt(text, offset);

        if (!token)
        {
            ++offset;
            continue;
        }

        std::string value(text.substr(offset, token->length));

        switch (token->kind)
        {
        case TokenKind::Placeholder: tokens.placeholders.push_back(std::move(value)); break;
        case TokenKind::Printf: tokens.printf.push_back(std::move(value)); break;
        case TokenKind::StoryCode: tokens.storyCodes.push_back(std::move(value)); break;
        case TokenKind::ColorCode: tokens.colorCodes.push_back(std::move(value)); break;
        }

        offset += token->length;
    }

    std::sort(tokens.placeholders.begin(), tokens.placeholders.end());
    std::sort(tokens.storyCodes.begin(), tokens.storyCodes.end());
    std::sort(tokens.colorCodes.begin(), tokens.colorCodes.end());
    return tokens;
}

std::string joined(const std::vector<std::string> &values)
{
    std::string text;

    for (const std::string &value : values)
    {
        if (!text.empty())
        {
            text += ' ';
        }

        text += value;
    }

    return text.empty() ? "none" : text;
}

// A gettext plural formula, evaluated for one number by recursive descent.
class PluralFormula
{
public:
    PluralFormula(std::string_view formula, uint64_t number)
        : m_formula(formula)
        , m_number(number)
    {
    }

    std::optional<uint64_t> evaluate()
    {
        const uint64_t value = ternary();
        skipSpaces();

        if (m_failed || m_offset != m_formula.size())
        {
            return std::nullopt;
        }

        return value;
    }

private:
    void skipSpaces()
    {
        while (m_offset < m_formula.size() && (m_formula[m_offset] == ' ' || m_formula[m_offset] == '\t'))
        {
            ++m_offset;
        }
    }

    bool accept(std::string_view symbol)
    {
        skipSpaces();

        if (m_formula.substr(m_offset, symbol.size()) != symbol)
        {
            return false;
        }

        // "<" must not take the first character of "<=", nor "!" that of "!=".
        if (symbol.size() == 1 && m_offset + 1 < m_formula.size() && m_formula[m_offset + 1] == '='
            && (symbol == "<" || symbol == ">" || symbol == "!" || symbol == "="))
        {
            return false;
        }

        m_offset += symbol.size();
        return true;
    }

    uint64_t ternary()
    {
        const uint64_t condition = logicalOr();

        if (!accept("?"))
        {
            return condition;
        }

        const uint64_t whenTrue = ternary();

        if (!accept(":"))
        {
            m_failed = true;
            return 0;
        }

        const uint64_t whenFalse = ternary();
        return condition != 0 ? whenTrue : whenFalse;
    }

    uint64_t logicalOr()
    {
        uint64_t value = logicalAnd();

        while (accept("||"))
        {
            const uint64_t right = logicalAnd();
            value = (value != 0 || right != 0) ? 1 : 0;
        }

        return value;
    }

    uint64_t logicalAnd()
    {
        uint64_t value = equality();

        while (accept("&&"))
        {
            const uint64_t right = equality();
            value = (value != 0 && right != 0) ? 1 : 0;
        }

        return value;
    }

    uint64_t equality()
    {
        uint64_t value = relational();

        while (true)
        {
            if (accept("=="))
            {
                value = value == relational() ? 1 : 0;
            }
            else if (accept("!="))
            {
                value = value != relational() ? 1 : 0;
            }
            else
            {
                return value;
            }
        }
    }

    uint64_t relational()
    {
        uint64_t value = additive();

        while (true)
        {
            if (accept("<="))
            {
                value = value <= additive() ? 1 : 0;
            }
            else if (accept(">="))
            {
                value = value >= additive() ? 1 : 0;
            }
            else if (accept("<"))
            {
                value = value < additive() ? 1 : 0;
            }
            else if (accept(">"))
            {
                value = value > additive() ? 1 : 0;
            }
            else
            {
                return value;
            }
        }
    }

    uint64_t additive()
    {
        uint64_t value = multiplicative();

        while (true)
        {
            if (accept("+"))
            {
                value += multiplicative();
            }
            else if (accept("-"))
            {
                value -= multiplicative();
            }
            else
            {
                return value;
            }
        }
    }

    uint64_t multiplicative()
    {
        uint64_t value = unary();

        while (true)
        {
            const bool multiply = accept("*");
            const bool divide = !multiply && accept("/");
            const bool remainder = !multiply && !divide && accept("%");

            if (!multiply && !divide && !remainder)
            {
                return value;
            }

            const uint64_t right = unary();

            if (multiply)
            {
                value *= right;
            }
            else if (right == 0)
            {
                // A branch the number does not take may divide by zero; it gives no form rather than failing.
                value = 0;
            }
            else
            {
                value = divide ? value / right : value % right;
            }
        }
    }

    uint64_t unary()
    {
        if (accept("!"))
        {
            return unary() == 0 ? 1 : 0;
        }

        return primary();
    }

    uint64_t primary()
    {
        skipSpaces();

        if (accept("("))
        {
            const uint64_t value = ternary();

            if (!accept(")"))
            {
                m_failed = true;
            }

            return value;
        }

        if (m_offset < m_formula.size() && m_formula[m_offset] == 'n')
        {
            ++m_offset;
            return m_number;
        }

        uint64_t value = 0;
        const char *pBegin = m_formula.data() + m_offset;
        const char *pEnd = m_formula.data() + m_formula.size();
        const std::from_chars_result result = std::from_chars(pBegin, pEnd, value);

        if (result.ec != std::errc() || result.ptr == pBegin)
        {
            m_failed = true;
            return 0;
        }

        m_offset += size_t(result.ptr - pBegin);
        return value;
    }

    std::string_view m_formula;
    uint64_t m_number = 0;
    size_t m_offset = 0;
    bool m_failed = false;
};

std::string_view trimmed(std::string_view text)
{
    while (!text.empty() && (text.front() == ' ' || text.front() == '\t'))
    {
        text.remove_prefix(1);
    }

    while (!text.empty() && (text.back() == ' ' || text.back() == '\t' || text.back() == '\r'))
    {
        text.remove_suffix(1);
    }

    return text;
}

// A quoted .po string with C escapes; nullopt when it is not one.
std::optional<std::string> parseQuoted(std::string_view text)
{
    text = trimmed(text);

    if (text.size() < 2 || text.front() != '"' || text.back() != '"')
    {
        return std::nullopt;
    }

    std::string value;
    const std::string_view body = text.substr(1, text.size() - 2);

    for (size_t index = 0; index < body.size(); ++index)
    {
        const char character = body[index];

        if (character == '"')
        {
            return std::nullopt;
        }

        if (character != '\\')
        {
            value += character;
            continue;
        }

        if (++index >= body.size())
        {
            return std::nullopt;
        }

        const char escape = body[index];

        switch (escape)
        {
        case 'n': value += '\n'; break;
        case 't': value += '\t'; break;
        case 'r': value += '\r'; break;
        case 'f': value += '\f'; break;
        case 'v': value += '\v'; break;
        case 'a': value += '\a'; break;
        case 'b': value += '\b'; break;
        case '\\': value += '\\'; break;
        case '"': value += '"'; break;
        case '\'': value += '\''; break;
        case '?': value += '?'; break;
        case 'x':
        {
            unsigned code = 0;
            size_t digits = 0;

            while (index + 1 < body.size() && digits < 2 && std::isxdigit(static_cast<unsigned char>(body[index + 1])))
            {
                const char digit = body[++index];
                code = code * 16 + unsigned(isAsciiDigit(digit) ? digit - '0' : (digit | 0x20) - 'a' + 10);
                ++digits;
            }

            if (digits == 0)
            {
                return std::nullopt;
            }

            value += char(code);
            break;
        }
        default:
            if (escape >= '0' && escape <= '7')
            {
                unsigned code = unsigned(escape - '0');

                for (int digit = 0; digit < 2 && index + 1 < body.size() && body[index + 1] >= '0'
                     && body[index + 1] <= '7'; ++digit)
                {
                    code = code * 8 + unsigned(body[++index] - '0');
                }

                value += char(code);
                break;
            }

            return std::nullopt;
        }
    }

    return value;
}

// The value of a header field ("Plural-Forms: ...") of a .po header.
std::string headerField(std::string_view header, std::string_view name)
{
    size_t offset = 0;

    while (offset < header.size())
    {
        size_t end = header.find('\n', offset);

        if (end == std::string_view::npos)
        {
            end = header.size();
        }

        const std::string_view line = header.substr(offset, end - offset);

        if (line.size() > name.size() && line.substr(0, name.size()) == name && line[name.size()] == ':')
        {
            return std::string(trimmed(line.substr(name.size() + 1)));
        }

        offset = end + 1;
    }

    return {};
}

void appendAccented(std::string &result, uint32_t point)
{
    switch (point)
    {
    case 'a': point = 0xe1; break;
    case 'e': point = 0xe9; break;
    case 'i': point = 0xed; break;
    case 'o': point = 0xf3; break;
    case 'u': point = 0xfa; break;
    case 'y': point = 0xfd; break;
    case 'n': point = 0xf1; break;
    case 'c': point = 0xe7; break;
    case 'A': point = 0xc1; break;
    case 'E': point = 0xc9; break;
    case 'I': point = 0xcd; break;
    case 'O': point = 0xd3; break;
    case 'U': point = 0xda; break;
    case 'Y': point = 0xdd; break;
    case 'N': point = 0xd1; break;
    case 'C': point = 0xc7; break;
    default: break;
    }

    Utf8::append(result, point);
}
}

std::optional<PoFile> parsePoFile(std::string_view text, std::string &error)
{
    error.clear();
    PoFile file;

    enum class Field
    {
        None,
        Context,
        English,
        EnglishPlural,
        Translation
    };

    PoEntry entry;
    bool hasEnglish = false;
    bool hasTranslation = false;
    bool obsolete = false;
    Field field = Field::None;
    size_t translationIndex = 0;
    int lineNumber = 0;

    const auto fail = [&error, &lineNumber](const std::string &message) -> std::optional<PoFile>
    {
        error = "line " + std::to_string(lineNumber) + ": " + message;
        return std::nullopt;
    };

    // Ends the entry read so far: the header gives the plural rule, any other entry joins the file.
    const auto finishEntry = [&]()
    {
        if (hasEnglish && hasTranslation && !obsolete)
        {
            if (entry.english.empty() && entry.context.empty())
            {
                if (!entry.translations.empty())
                {
                    file.pluralForms = headerField(entry.translations.front(), "Plural-Forms");
                }
            }
            else
            {
                file.entries.push_back(std::move(entry));
            }
        }

        entry = PoEntry();
        hasEnglish = false;
        hasTranslation = false;
        obsolete = false;
        field = Field::None;
    };

    size_t offset = 0;

    if (text.substr(0, 3) == "\xef\xbb\xbf")
    {
        offset = 3;
    }

    while (offset <= text.size())
    {
        size_t end = text.find('\n', offset);

        if (end == std::string_view::npos)
        {
            end = text.size();
        }

        const std::string_view line = trimmed(text.substr(offset, end - offset));
        offset = end + 1;
        ++lineNumber;

        if (line.empty())
        {
            if (hasTranslation)
            {
                finishEntry();
            }

            continue;
        }

        if (line.front() == '#')
        {
            if (hasTranslation)
            {
                finishEntry();
            }

            if (line.starts_with("#~"))
            {
                obsolete = true;
            }
            else if (line.starts_with("#,") && line.find("fuzzy") != std::string_view::npos)
            {
                entry.fuzzy = true;
            }

            continue;
        }

        if (line.front() == '"')
        {
            const std::optional<std::string> value = parseQuoted(line);

            if (!value)
            {
                return fail("malformed string");
            }

            switch (field)
            {
            case Field::Context: entry.context += *value; break;
            case Field::English: entry.english += *value; break;
            case Field::EnglishPlural: entry.englishPlural += *value; break;
            case Field::Translation: entry.translations[translationIndex] += *value; break;
            case Field::None: return fail("a string continues no keyword");
            }

            continue;
        }

        const size_t space = line.find_first_of(" \t");
        const std::string_view keyword = line.substr(0, space);
        const std::optional<std::string> value =
            space == std::string_view::npos ? std::nullopt : parseQuoted(line.substr(space));

        if (!value)
        {
            return fail("malformed " + std::string(keyword));
        }

        if (keyword == "msgctxt" || keyword == "msgid")
        {
            // Without a blank line or comment between them, the next entry starts here.
            if (hasTranslation)
            {
                finishEntry();
            }

            if (keyword == "msgctxt")
            {
                if (hasEnglish || !entry.context.empty())
                {
                    return fail("msgctxt after msgid");
                }

                entry.context = *value;
                field = Field::Context;
            }
            else
            {
                if (hasEnglish)
                {
                    return fail("msgid without msgstr");
                }

                entry.english = *value;
                entry.line = lineNumber;
                hasEnglish = true;
                field = Field::English;
            }

            continue;
        }

        if (!hasEnglish)
        {
            return fail(std::string(keyword) + " before msgid");
        }

        if (keyword == "msgid_plural")
        {
            entry.englishPlural = *value;
            field = Field::EnglishPlural;
            continue;
        }

        if (keyword == "msgstr")
        {
            if (!entry.englishPlural.empty() || hasTranslation)
            {
                return fail("msgstr in a plural entry or twice");
            }

            entry.translations.push_back(*value);
            translationIndex = 0;
            hasTranslation = true;
            field = Field::Translation;
            continue;
        }

        if (keyword.starts_with("msgstr[") && keyword.back() == ']')
        {
            size_t index = 0;
            const std::string_view digits = keyword.substr(7, keyword.size() - 8);
            const std::from_chars_result result = std::from_chars(digits.data(), digits.data() + digits.size(), index);

            if (entry.englishPlural.empty() || result.ec != std::errc() || result.ptr != digits.data() + digits.size()
                || index != entry.translations.size())
            {
                return fail("msgstr[] out of order or without msgid_plural");
            }

            entry.translations.push_back(*value);
            translationIndex = index;
            hasTranslation = true;
            field = Field::Translation;
            continue;
        }

        return fail("unknown keyword " + std::string(keyword));
    }

    if (hasEnglish && !hasTranslation)
    {
        return fail("msgid without msgstr at the end");
    }

    finishEntry();
    return file;
}

std::optional<PluralRule> PluralRule::parse(std::string_view pluralForms, std::string &error)
{
    error.clear();
    const size_t countAt = pluralForms.find("nplurals");
    size_t formulaAt = std::string_view::npos;

    for (size_t at = pluralForms.find("plural"); at != std::string_view::npos; at = pluralForms.find("plural", at + 1))
    {
        if (at == 0 || pluralForms[at - 1] != 'n')
        {
            formulaAt = at;
            break;
        }
    }

    if (countAt == std::string_view::npos || formulaAt == std::string_view::npos)
    {
        error = "Plural-Forms needs nplurals and plural";
        return std::nullopt;
    }

    std::string_view countText = trimmed(pluralForms.substr(countAt + 8));

    if (countText.empty() || countText.front() != '=')
    {
        error = "Plural-Forms: nplurals without a value";
        return std::nullopt;
    }

    countText = trimmed(countText.substr(1));
    size_t formCount = 0;
    const std::from_chars_result countResult =
        std::from_chars(countText.data(), countText.data() + countText.size(), formCount);

    if (countResult.ec != std::errc() || formCount == 0 || formCount > 6)
    {
        error = "Plural-Forms: nplurals must be 1 to 6";
        return std::nullopt;
    }

    std::string_view formula = trimmed(pluralForms.substr(formulaAt + 6));

    if (formula.empty() || formula.front() != '=')
    {
        error = "Plural-Forms: plural without a formula";
        return std::nullopt;
    }

    formula = formula.substr(1);
    formula = trimmed(formula.substr(0, formula.find(';')));

    PluralRule rule;
    rule.m_formCount = formCount;
    rule.m_formula = std::string(formula);

    // Every number up to a thousand must give a form the rule has; the endings repeat beyond it.
    for (uint64_t number = 0; number <= 1000; ++number)
    {
        const std::optional<uint64_t> form = PluralFormula(rule.m_formula, number).evaluate();

        if (!form || *form >= formCount)
        {
            error = "Plural-Forms: the formula gives no valid form for " + std::to_string(number);
            return std::nullopt;
        }
    }

    return rule;
}

PluralRule PluralRule::english()
{
    return PluralRule();
}

size_t PluralRule::formCount() const
{
    return m_formCount;
}

size_t PluralRule::form(uint64_t number) const
{
    const std::optional<uint64_t> form = PluralFormula(m_formula, number).evaluate();
    return form && *form < m_formCount ? size_t(*form) : 0;
}

std::string translationMismatch(std::string_view english, std::string_view translation)
{
    const TextTokens expected = tokensOf(english);
    const TextTokens actual = tokensOf(translation);
    std::string mismatch;

    const auto compare = [&mismatch](const char *pWhat, const std::vector<std::string> &want,
                                     const std::vector<std::string> &have)
    {
        if (want != have)
        {
            mismatch += std::string(mismatch.empty() ? "" : "; ") + pWhat + " " + joined(want) + " became "
                + joined(have);
        }
    };

    compare("placeholders", expected.placeholders, actual.placeholders);
    compare("printf values", expected.printf, actual.printf);
    compare("story codes", expected.storyCodes, actual.storyCodes);
    compare("colour codes", expected.colorCodes, actual.colorCodes);
    return mismatch;
}

TextArgument::TextArgument(std::string_view name, std::string_view value)
    : name(name)
    , value(value)
{
}

TextArgument::TextArgument(std::string_view name, const std::string &value)
    : name(name)
    , value(value)
{
}

TextArgument::TextArgument(std::string_view name, const char *pValue)
    : name(name)
    , value(pValue != nullptr ? pValue : "")
{
}

TextArgument::TextArgument(std::string_view name, int value)
    : name(name)
    , value(std::to_string(value))
{
}

TextArgument::TextArgument(std::string_view name, unsigned value)
    : name(name)
    , value(std::to_string(value))
{
}

TextArgument::TextArgument(std::string_view name, long value)
    : name(name)
    , value(std::to_string(value))
{
}

TextArgument::TextArgument(std::string_view name, unsigned long value)
    : name(name)
    , value(std::to_string(value))
{
}

TextArgument::TextArgument(std::string_view name, long long value)
    : name(name)
    , value(std::to_string(value))
{
}

TextArgument::TextArgument(std::string_view name, unsigned long long value)
    : name(name)
    , value(std::to_string(value))
{
}

std::string formatText(std::string_view text, std::span<const TextArgument> arguments)
{
    if (arguments.empty() || text.find('{') == std::string_view::npos)
    {
        return std::string(text);
    }

    std::string result;
    result.reserve(text.size() + 16);

    for (size_t offset = 0; offset < text.size();)
    {
        if (text[offset] == '{')
        {
            const size_t close = text.find('}', offset + 1);

            if (close != std::string_view::npos)
            {
                const std::string_view name = text.substr(offset + 1, close - offset - 1);
                const auto argument = std::find_if(arguments.begin(), arguments.end(),
                                                   [name](const TextArgument &candidate)
                                                   {
                                                       return candidate.name == name;
                                                   });

                if (argument != arguments.end())
                {
                    result += argument->value;
                    offset = close + 1;
                    continue;
                }
            }
        }

        result += text[offset];
        ++offset;
    }

    return result;
}

std::string pseudoLocalize(std::string_view text)
{
    if (text.empty())
    {
        return std::string(text);
    }

    std::string result = "[";
    size_t letters = 0;

    for (size_t offset = 0; offset < text.size();)
    {
        if (const std::optional<Token> token = tokenAt(text, offset))
        {
            result += text.substr(offset, token->length);
            offset += token->length;
            continue;
        }

        const Utf8::Character character = Utf8::decode(text, offset);

        if (character.size == 0)
        {
            break;
        }

        if (character.point != '\n' && character.point != ' ')
        {
            ++letters;
        }

        appendAccented(result, character.point);
        offset += character.size;
    }

    // A third longer: the room a longer language needs. U+00B7 exists in the Windows-1252 faces too.
    for (size_t pad = 0; pad < std::max<size_t>(1, letters / 3); ++pad)
    {
        result += "\xc2\xb7";
    }

    result += ']';
    return result;
}

void TextCatalog::add(const PoFile &file, std::string_view fileName, std::string_view defaultContext,
                      std::vector<std::string> &warnings)
{
    if (!file.pluralForms.empty())
    {
        std::string error;
        std::optional<PluralRule> rule = PluralRule::parse(file.pluralForms, error);

        if (!rule)
        {
            warnings.push_back(std::string(fileName) + ": " + error + "; plurals use English's rule");
        }
        else if (!m_pluralRule)
        {
            m_pluralRule = std::move(rule);
        }
        else if (m_pluralRule->formCount() != rule->formCount())
        {
            warnings.push_back(std::string(fileName) + ": its Plural-Forms differs from an earlier file's; kept the"
                               " earlier one");
        }
    }

    if (!defaultContext.empty())
    {
        const auto position = std::lower_bound(m_fileContexts.begin(), m_fileContexts.end(), defaultContext);

        if (position == m_fileContexts.end() || *position != defaultContext)
        {
            m_fileContexts.insert(position, std::string(defaultContext));
        }
    }

    for (const PoEntry &entry : file.entries)
    {
        if (entry.fuzzy || entry.translations.empty())
        {
            continue;
        }

        const bool plural = !entry.englishPlural.empty();
        bool translated = false;
        std::string mismatch;

        for (size_t form = 0; form < entry.translations.size() && mismatch.empty(); ++form)
        {
            if (entry.translations[form].empty())
            {
                continue;
            }

            translated = true;
            mismatch = translationMismatch(plural && form > 0 ? entry.englishPlural : entry.english,
                                           entry.translations[form]);

            // A language with a single form translates the plural English.
            if (!mismatch.empty() && plural && form == 0)
            {
                mismatch = translationMismatch(entry.englishPlural, entry.translations[form]);
            }
        }

        if (!translated)
        {
            continue;
        }

        if (!mismatch.empty())
        {
            warnings.push_back(std::string(fileName) + ":" + std::to_string(entry.line) + ": refused, " + mismatch);
            continue;
        }

        const std::string_view context = entry.context.empty() ? defaultContext : std::string_view(entry.context);
        m_translations[key(context, entry.english)] = entry.translations;
    }
}

const std::string *TextCatalog::find(std::string_view context, std::string_view english) const
{
    const auto entry = m_translations.find(key(context, english));

    if (entry == m_translations.end() || entry->second.empty() || entry->second.front().empty())
    {
        return nullptr;
    }

    return &entry->second.front();
}

const std::string *TextCatalog::findPlural(std::string_view context, std::string_view english, uint64_t number) const
{
    const auto entry = m_translations.find(key(context, english));

    if (entry == m_translations.end())
    {
        return nullptr;
    }

    const size_t form = m_pluralRule ? m_pluralRule->form(number) : PluralRule::english().form(number);

    if (form >= entry->second.size() || entry->second[form].empty())
    {
        return nullptr;
    }

    return &entry->second[form];
}

const std::string *TextCatalog::findInWorldFiles(std::string_view english) const
{
    for (const std::string &context : m_fileContexts)
    {
        if (const std::string *pTranslation = find(context, english))
        {
            return pTranslation;
        }
    }

    return nullptr;
}

size_t TextCatalog::size() const
{
    return m_translations.size();
}

bool TextCatalog::empty() const
{
    return m_translations.empty();
}

std::string TextCatalog::key(std::string_view context, std::string_view english)
{
    // gettext's own separator of context and text.
    std::string key;
    key.reserve(context.size() + english.size() + 1);
    key += context;
    key += '\x04';
    key += english;
    return key;
}
}

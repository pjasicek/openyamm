#include "core/Json.h"

#include <charconv>
#include <cmath>
#include <cstdio>

namespace OpenYAMM::Studio
{
namespace
{
bool isIntegerText(const std::string &text)
{
    if (text.empty())
    {
        return false;
    }

    size_t index = (text[0] == '-' || text[0] == '+') ? 1 : 0;

    if (index >= text.size() || text.size() - index > 18)
    {
        return false;
    }

    for (; index < text.size(); ++index)
    {
        if (text[index] < '0' || text[index] > '9')
        {
            return false;
        }
    }

    return true;
}

bool isNumberText(const std::string &text)
{
    if (text.empty())
    {
        return false;
    }

    const char first = text[0];

    if (!((first >= '0' && first <= '9') || first == '-' || first == '+' || first == '.'))
    {
        return false;
    }

    bool hasDigit = false;

    for (const char character : text)
    {
        if (character >= '0' && character <= '9')
        {
            hasDigit = true;
        }
        else if (character != '-' && character != '+' && character != '.' && character != 'e' && character != 'E')
        {
            return false;
        }
    }

    if (!hasDigit)
    {
        return false;
    }

    double parsed = 0.0;
    const char *pBegin = text.data() + (first == '+' ? 1 : 0);
    const char *pEnd = text.data() + text.size();
    const std::from_chars_result result = std::from_chars(pBegin, pEnd, parsed);
    return result.ec == std::errc() && result.ptr == pEnd && std::isfinite(parsed);
}
}

ScalarKind classifyScalar(const YAML::Node &yamlNode)
{
    if (yamlNode.IsNull())
    {
        return ScalarKind::Null;
    }

    // yaml-cpp tags a quoted scalar "!" and a plain one "?".
    if (yamlNode.Tag() == "!")
    {
        return ScalarKind::String;
    }

    const std::string &text = yamlNode.Scalar();

    if (text == "true" || text == "false")
    {
        return ScalarKind::Boolean;
    }

    if (text == "null" || text == "~" || text.empty())
    {
        return ScalarKind::Null;
    }

    if (isIntegerText(text))
    {
        return ScalarKind::Integer;
    }

    if (isNumberText(text))
    {
        return ScalarKind::Number;
    }

    return ScalarKind::String;
}

std::string jsonQuote(std::string_view text)
{
    std::string result;
    result.reserve(text.size() + 2);
    result.push_back('"');

    for (const char character : text)
    {
        switch (character)
        {
        case '"':
            result += "\\\"";
            break;

        case '\\':
            result += "\\\\";
            break;

        case '\n':
            result += "\\n";
            break;

        case '\r':
            result += "\\r";
            break;

        case '\t':
            result += "\\t";
            break;

        default:
            if (static_cast<unsigned char>(character) < 0x20)
            {
                char buffer[8];
                std::snprintf(buffer, sizeof(buffer), "\\u%04x", static_cast<unsigned char>(character));
                result += buffer;
            }
            else
            {
                result.push_back(character);
            }

            break;
        }
    }

    result.push_back('"');
    return result;
}

std::string formatNumber(double number)
{
    if (!std::isfinite(number))
    {
        return "0";
    }

    if (number == 0.0)
    {
        return "0";
    }

    if (number == std::floor(number) && std::fabs(number) < 1.0e15)
    {
        char buffer[32];
        const std::to_chars_result result =
            std::to_chars(buffer, buffer + sizeof(buffer), static_cast<int64_t>(number));
        return std::string(buffer, result.ptr);
    }

    char buffer[64];
    const std::to_chars_result result = std::to_chars(buffer, buffer + sizeof(buffer), number);
    return std::string(buffer, result.ptr);
}

JsonWriter::JsonWriter(bool pretty)
    : m_pretty(pretty)
{
}

void JsonWriter::newLine()
{
    if (!m_pretty)
    {
        return;
    }

    m_text.push_back('\n');
    m_text.append(m_levels.size() * 2, ' ');
}

void JsonWriter::beforeValue()
{
    if (m_afterKey)
    {
        m_afterKey = false;
        return;
    }

    if (m_levels.empty())
    {
        return;
    }

    Level &level = m_levels.back();

    if (level.hasItems)
    {
        m_text.push_back(',');

        if (level.compact && m_pretty)
        {
            m_text.push_back(' ');
        }
    }

    level.hasItems = true;

    if (!level.compact)
    {
        newLine();
    }
}

void JsonWriter::beginObject()
{
    beforeValue();

    // A container inside a compact array ends its compactness: lay the rest out on lines.
    if (!m_levels.empty())
    {
        m_levels.back().compact = false;
    }

    m_text.push_back('{');
    m_levels.push_back({true, false, false});
}

void JsonWriter::endObject()
{
    const bool hadItems = m_levels.back().hasItems;
    m_levels.pop_back();

    if (hadItems)
    {
        newLine();
    }

    m_text.push_back('}');
}

void JsonWriter::beginArray()
{
    beforeValue();

    if (!m_levels.empty())
    {
        m_levels.back().compact = false;
    }

    m_text.push_back('[');
    m_levels.push_back({false, false, true});
}

void JsonWriter::endArray()
{
    const Level level = m_levels.back();
    m_levels.pop_back();

    if (level.hasItems && !level.compact)
    {
        newLine();
    }

    m_text.push_back(']');
}

void JsonWriter::key(std::string_view name)
{
    beforeValue();
    m_text += jsonQuote(name);
    m_text.push_back(':');

    if (m_pretty)
    {
        m_text.push_back(' ');
    }

    m_afterKey = true;
}

void JsonWriter::value(std::string_view text)
{
    beforeValue();
    m_text += jsonQuote(text);
}

void JsonWriter::raw(std::string_view json)
{
    beforeValue();
    m_text += json;
}

void JsonWriter::rawMembers(std::string_view members)
{
    if (members.empty() || m_levels.empty())
    {
        return;
    }

    Level &level = m_levels.back();

    if (level.hasItems)
    {
        m_text.push_back(',');
    }

    m_text += members;
    level.hasItems = true;
}

void JsonWriter::value(const char *pText)
{
    value(std::string_view(pText));
}

void JsonWriter::value(const std::string &text)
{
    value(std::string_view(text));
}

void JsonWriter::value(bool flag)
{
    beforeValue();
    m_text += flag ? "true" : "false";
}

void JsonWriter::value(int64_t number)
{
    beforeValue();
    m_text += std::to_string(number);
}

void JsonWriter::value(uint64_t number)
{
    beforeValue();
    m_text += std::to_string(number);
}

void JsonWriter::value(int number)
{
    value(static_cast<int64_t>(number));
}

void JsonWriter::value(unsigned number)
{
    value(static_cast<uint64_t>(number));
}

void JsonWriter::value(double number)
{
    beforeValue();
    m_text += formatNumber(number);
}

void JsonWriter::value(float number)
{
    beforeValue();

    if (!std::isfinite(number))
    {
        m_text += "0";
        return;
    }

    if (number == std::floor(number) && std::fabs(number) < 1.0e9f)
    {
        m_text += std::to_string(static_cast<int64_t>(number));
        return;
    }

    // Shortest text that reads back to the same float, not the double it widens to.
    char buffer[64];
    const std::to_chars_result result = std::to_chars(buffer, buffer + sizeof(buffer), number);
    m_text.append(buffer, result.ptr);
}

void JsonWriter::null()
{
    beforeValue();
    m_text += "null";
}

void JsonWriter::node(const YAML::Node &yamlNode)
{
    if (yamlNode.IsMap())
    {
        beginObject();

        for (YAML::const_iterator iterator = yamlNode.begin(); iterator != yamlNode.end(); ++iterator)
        {
            key(iterator->first.Scalar());
            node(iterator->second);
        }

        endObject();
        return;
    }

    if (yamlNode.IsSequence())
    {
        beginArray();

        for (const YAML::Node &item : yamlNode)
        {
            node(item);
        }

        endArray();
        return;
    }

    if (!yamlNode.IsDefined())
    {
        null();
        return;
    }

    switch (classifyScalar(yamlNode))
    {
    case ScalarKind::Null:
        null();
        break;

    case ScalarKind::Boolean:
        value(yamlNode.Scalar() == "true");
        break;

    case ScalarKind::Integer:
    case ScalarKind::Number:
    {
        beforeValue();
        const std::string &text = yamlNode.Scalar();
        double parsed = 0.0;
        const char *pBegin = text.data() + (text[0] == '+' ? 1 : 0);
        std::from_chars(pBegin, text.data() + text.size(), parsed);
        m_text += formatNumber(parsed);
        break;
    }

    case ScalarKind::String:
        value(yamlNode.Scalar());
        break;
    }
}

const std::string &JsonWriter::text() const
{
    return m_text;
}

std::string JsonWriter::take()
{
    return std::move(m_text);
}

std::string toJson(const YAML::Node &yamlNode, bool pretty)
{
    JsonWriter writer(pretty);
    writer.node(yamlNode);
    return writer.take();
}
}

#include "game/localization/LocalizationCatalog.h"

#include "engine/AssetFileSystem.h"
#include "engine/Utf8.h"
#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <iostream>
#include <numeric>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
std::vector<uint32_t> normalizedAnswer(const std::string &text)
{
    std::vector<uint32_t> result;
    for (const Engine::Utf8CodePoint &character : Engine::decodeUtf8(text))
    {
        uint32_t value = character.value;
        if ((value >= 'A' && value <= 'Z') || (value >= 0x0410 && value <= 0x042f))
        {
            value += 32;
        }
        else if (value == 0x0401)
        {
            value = 0x0451; // Cyrillic Yo.
        }
        result.push_back(value);
    }

    const auto isSpace = [](uint32_t value)
    {
        return value == ' ' || (value >= '\t' && value <= '\r');
    };
    const auto first = std::find_if_not(result.begin(), result.end(), isSpace);
    const auto last = std::find_if_not(result.rbegin(), result.rend(), isSpace).base();
    return first < last ? std::vector<uint32_t>(first, last) : std::vector<uint32_t>{};
}
}

bool LocalizationCatalog::matchesAnswer(const std::string &source, const std::string &input) const
{
    const std::vector<uint32_t> normalizedInput = normalizedAnswer(input);
    if (normalizedInput.empty())
    {
        return false;
    }
    return normalizedInput == normalizedAnswer(source) || normalizedInput == normalizedAnswer(translate(source));
}

bool LocalizationCatalog::load(const Engine::AssetFileSystem &assetFileSystem, const std::string &language)
{
    m_language = toLowerCopy(language) == "ru" ? "ru" : "en";
    m_translations.clear();
    m_templates.clear();

    if (m_language == "en")
    {
        return true;
    }

    const std::array<std::string, 3> catalogNames = {"ui.yml", "gameplay.yml", "events.yml"};
    for (const std::string &catalogName : catalogNames)
    {
        const std::string path = "localization/" + m_language + "/" + catalogName;
        const std::optional<std::string> contents = assetFileSystem.readTextFile(path);
        if (!contents)
        {
            if (catalogName == "ui.yml")
            {
                std::cerr << "LocalizationCatalog: missing required catalog " << path << '\n';
                return false;
            }
            continue;
        }

        try
        {
            const YAML::Node root = YAML::Load(*contents);
            const YAML::Node translations = root["translations"];
            if (!translations || !translations.IsMap())
            {
                std::cerr << "LocalizationCatalog: missing translations map in " << path << '\n';
                return false;
            }

            for (const auto &entry : translations)
            {
                m_translations[entry.first.as<std::string>()] = entry.second.as<std::string>();
            }
        }
        catch (const YAML::Exception &exception)
        {
            std::cerr << "LocalizationCatalog: failed to parse " << path << ": " << exception.what() << '\n';
            m_translations.clear();
            return false;
        }
    }

    for (const std::pair<const std::string, std::string> &entry : m_translations)
    {
        TranslationTemplate translationTemplate;
        translationTemplate.translation = entry.second;

        size_t offset = 0;
        while (offset < entry.first.size())
        {
            const size_t placeholderStart = entry.first.find('{', offset);
            if (placeholderStart == std::string::npos)
            {
                translationTemplate.sourceParts.push_back(entry.first.substr(offset));
                break;
            }

            const size_t placeholderEnd = entry.first.find('}', placeholderStart + 1);
            if (placeholderEnd == std::string::npos)
            {
                translationTemplate.sourceParts.clear();
                break;
            }

            translationTemplate.sourceParts.push_back(entry.first.substr(offset, placeholderStart - offset));
            translationTemplate.placeholderNames.push_back(
                entry.first.substr(placeholderStart + 1, placeholderEnd - placeholderStart - 1));
            offset = placeholderEnd + 1;
        }

        size_t literalCharacterCount = 0;
        for (const std::string &part : translationTemplate.sourceParts)
        {
            literalCharacterCount += part.size();
        }

        if (!translationTemplate.placeholderNames.empty() && literalCharacterCount > 0)
        {
            if (translationTemplate.sourceParts.size() == translationTemplate.placeholderNames.size())
            {
                translationTemplate.sourceParts.emplace_back();
            }
            m_templates.push_back(std::move(translationTemplate));
        }
    }

    std::sort(
        m_templates.begin(),
        m_templates.end(),
        [](const TranslationTemplate &left, const TranslationTemplate &right)
        {
            const size_t leftLiteralSize = std::accumulate(
                left.sourceParts.begin(), left.sourceParts.end(), static_cast<size_t>(0),
                [](size_t size, const std::string &part) { return size + part.size(); });
            const size_t rightLiteralSize = std::accumulate(
                right.sourceParts.begin(), right.sourceParts.end(), static_cast<size_t>(0),
                [](size_t size, const std::string &part) { return size + part.size(); });
            return leftLiteralSize > rightLiteralSize;
        });

    return true;
}

const std::string &LocalizationCatalog::translate(const std::string &source) const
{
    const std::unordered_map<std::string, std::string>::const_iterator iterator = m_translations.find(source);
    return iterator == m_translations.end() ? source : iterator->second;
}

void LocalizationCatalog::addExactTranslation(const std::string &source, const std::string &translation)
{
    if (!source.empty() && !translation.empty() && source != translation)
    {
        m_translations[source] = translation;
    }
}

std::string LocalizationCatalog::translateText(const std::string &source) const
{
    const std::unordered_map<std::string, std::string>::const_iterator exactIterator = m_translations.find(source);
    if (exactIterator != m_translations.end())
    {
        return exactIterator->second;
    }

    for (const TranslationTemplate &translationTemplate : m_templates)
    {
        if (!source.starts_with(translationTemplate.sourceParts.front()))
        {
            continue;
        }

        std::vector<std::pair<std::string, std::string>> values;
        size_t offset = translationTemplate.sourceParts.front().size();
        bool matched = true;

        for (size_t index = 0; index < translationTemplate.placeholderNames.size(); ++index)
        {
            const std::string &nextPart = translationTemplate.sourceParts[index + 1];
            const size_t nextOffset = nextPart.empty() && index + 1 == translationTemplate.placeholderNames.size()
                ? source.size()
                : source.find(nextPart, offset);
            if (nextOffset == std::string::npos)
            {
                matched = false;
                break;
            }

            values.emplace_back(
                translationTemplate.placeholderNames[index], source.substr(offset, nextOffset - offset));
            offset = nextOffset + nextPart.size();
        }

        if (!matched || offset != source.size())
        {
            continue;
        }

        std::string result = translationTemplate.translation;
        for (const std::pair<std::string, std::string> &value : values)
        {
            const std::string placeholder = "{" + value.first + "}";
            size_t resultOffset = 0;
            while ((resultOffset = result.find(placeholder, resultOffset)) != std::string::npos)
            {
                std::string localizedValue = translate(value.second);
                if (value.first == "classes")
                {
                    // Promotion requirements can list any number of alternative classes.
                    localizedValue.clear();
                    size_t classOffset = 0;
                    while (classOffset < value.second.size())
                    {
                        const size_t commaOffset = value.second.find(", ", classOffset);
                        const size_t orOffset = value.second.find(" or ", classOffset);
                        const size_t separatorOffset = std::min(commaOffset, orOffset);
                        localizedValue += translate(value.second.substr(classOffset, separatorOffset - classOffset));
                        if (separatorOffset == std::string::npos)
                        {
                            break;
                        }
                        const std::string separator = separatorOffset == orOffset ? " or " : ", ";
                        localizedValue += translate(separator);
                        classOffset = separatorOffset + separator.size();
                    }
                }
                result.replace(resultOffset, placeholder.size(), localizedValue);
                resultOffset += localizedValue.size();
            }
        }
        return result;
    }

    return source;
}

std::string LocalizationCatalog::format(
    const std::string &source,
    const std::vector<std::pair<std::string, std::string>> &values
) const
{
    std::string result = translate(source);
    for (const std::pair<std::string, std::string> &value : values)
    {
        const std::string placeholder = "{" + value.first + "}";
        size_t offset = 0;
        while ((offset = result.find(placeholder, offset)) != std::string::npos)
        {
            result.replace(offset, placeholder.size(), value.second);
            offset += value.second.size();
        }
    }
    return result;
}

const std::string &LocalizationCatalog::language() const
{
    return m_language;
}
}

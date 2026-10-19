#include "game/localization/LocalizationCatalog.h"

#include "engine/AssetFileSystem.h"
#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <iostream>
#include <optional>

namespace OpenYAMM::Game
{
bool LocalizationCatalog::load(const Engine::AssetFileSystem &assetFileSystem, const std::string &language)
{
    m_language = toLowerCopy(language) == "ru" ? "ru" : "en";
    m_translations.clear();

    if (m_language == "en")
    {
        return true;
    }

    const std::string path = "localization/" + m_language + "/ui.yml";
    const std::optional<std::string> contents = assetFileSystem.readTextFile(path);
    if (!contents)
    {
        std::cerr << "LocalizationCatalog: missing optional catalog " << path << '\n';
        return false;
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

    return true;
}

const std::string &LocalizationCatalog::translate(const std::string &source) const
{
    const std::unordered_map<std::string, std::string>::const_iterator iterator = m_translations.find(source);
    return iterator == m_translations.end() ? source : iterator->second;
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

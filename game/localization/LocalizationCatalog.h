#pragma once

#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class LocalizationCatalog
{
public:
    bool load(const Engine::AssetFileSystem &assetFileSystem, const std::string &language);
    const std::string &translate(const std::string &source) const;
    std::string format(
        const std::string &source,
        const std::vector<std::pair<std::string, std::string>> &values
    ) const;
    const std::string &language() const;

private:
    std::string m_language = "en";
    std::unordered_map<std::string, std::string> m_translations;
};
}

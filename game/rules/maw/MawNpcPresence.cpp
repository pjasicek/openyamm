#include "game/rules/maw/MawNpcPresence.h"

#include <yaml-cpp/yaml.h>

#include <exception>

namespace OpenYAMM::Game
{
bool loadMawNpcExtraHouses(
    const std::string &text,
    std::unordered_map<uint32_t, std::vector<uint32_t>> &extraHouses,
    std::string &errorMessage)
{
    try
    {
        for (const auto &entry : YAML::Load(text)["extra_houses"])
        {
            extraHouses[entry.first.as<uint32_t>()] = entry.second.as<std::vector<uint32_t>>();
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    return true;
}
}

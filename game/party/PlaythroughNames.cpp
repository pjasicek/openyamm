#include "game/party/PlaythroughNames.h"

#include <yaml-cpp/yaml.h>

#include <fstream>
#include <map>

namespace OpenYAMM::Game
{
namespace
{
std::filesystem::path namesPath(const std::filesystem::path &directory)
{
    return directory / "names.yml";
}
}

std::unordered_map<std::string, std::string> readPlaythroughNames(const std::filesystem::path &directory)
{
    std::unordered_map<std::string, std::string> names;
    std::ifstream file(namesPath(directory), std::ios::binary);

    if (!file)
    {
        return names;
    }

    try
    {
        const YAML::Node root = YAML::Load(file);

        if (root && root.IsMap())
        {
            for (const auto &entry : root)
            {
                const std::string name = entry.second.as<std::string>("");

                if (!name.empty())
                {
                    names[entry.first.as<std::string>("")] = name;
                }
            }
        }
    }
    catch (const YAML::Exception &)
    {
        names.clear();
    }

    return names;
}

bool writePlaythroughName(
    const std::filesystem::path &directory,
    const std::string &playthroughId,
    const std::string &name)
{
    if (playthroughId.empty())
    {
        return false;
    }

    const std::unordered_map<std::string, std::string> stored = readPlaythroughNames(directory);
    // By id, so the file does not reorder between writes.
    std::map<std::string, std::string> names(stored.begin(), stored.end());

    if (name.empty())
    {
        names.erase(playthroughId);
    }
    else
    {
        names[playthroughId] = name;
    }

    YAML::Emitter out;
    out << YAML::BeginMap;

    for (const auto &[id, value] : names)
    {
        out << YAML::Key << id << YAML::Value << YAML::DoubleQuoted << value;
    }

    out << YAML::EndMap;
    std::error_code error;
    std::filesystem::create_directories(directory, error);
    std::ofstream file(namesPath(directory), std::ios::binary | std::ios::trunc);
    file << out.c_str() << '\n';
    return bool(file);
}
}

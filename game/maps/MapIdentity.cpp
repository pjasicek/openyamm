#include "game/maps/MapIdentity.h"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
std::string trimCopy(const std::string &value)
{
    size_t start = 0;
    size_t end = value.size();

    while (start < end && std::isspace(static_cast<unsigned char>(value[start])))
    {
        ++start;
    }

    while (end > start && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return value.substr(start, end - start);
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}
}

std::string normalizeWorldId(const std::string &worldId)
{
    const std::string normalizedWorldId = toLowerCopy(trimCopy(worldId));
    return normalizedWorldId.empty() ? DefaultWorldId : normalizedWorldId;
}

std::string normalizeMapFileStem(const std::string &fileName)
{
    const std::filesystem::path filePath(trimCopy(fileName));
    const std::string stem = filePath.stem().generic_string();
    const std::string normalizedStem = toLowerCopy(trimCopy(stem));

    if (!normalizedStem.empty())
    {
        return normalizedStem;
    }

    const std::string fallback = toLowerCopy(trimCopy(fileName));
    return fallback.empty() ? "unknown" : fallback;
}

std::string buildCanonicalMapId(const std::string &worldId, const std::string &fileName)
{
    return "world." + normalizeWorldId(worldId) + ".map." + normalizeMapFileStem(fileName);
}
}


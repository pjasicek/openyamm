#include "game/maps/MapRegistry.h"

#include "game/maps/MapIdentity.h"

#include <algorithm>
#include <cctype>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
void MapRegistry::initialize(const std::vector<MapStatsEntry> &entries)
{
    m_entries = entries;
}

std::optional<MapStatsEntry> MapRegistry::findById(int id) const
{
    for (const MapStatsEntry &entry : m_entries)
    {
        if (entry.id == id)
        {
            return entry;
        }
    }

    return std::nullopt;
}

std::optional<MapStatsEntry> MapRegistry::findByCanonicalId(const std::string &canonicalId) const
{
    const std::string normalizedCanonicalId = normalizeCanonicalId(canonicalId);

    for (const MapStatsEntry &entry : m_entries)
    {
        if (normalizeCanonicalId(entry.canonicalId) == normalizedCanonicalId)
        {
            return entry;
        }
    }

    return std::nullopt;
}

std::optional<MapStatsEntry> MapRegistry::findByFileName(const std::string &fileName) const
{
    const std::string normalizedFileName = normalizeFileName(fileName);

    for (const MapStatsEntry &entry : m_entries)
    {
        if (normalizeFileName(entry.fileName) == normalizedFileName)
        {
            return entry;
        }
    }

    return std::nullopt;
}

std::optional<MapStatsEntry> MapRegistry::findByWorldAndFileName(
    const std::string &worldId,
    const std::string &fileName) const
{
    return findByCanonicalId(buildCanonicalMapId(worldId, fileName));
}

const std::vector<MapStatsEntry> &MapRegistry::getEntries() const
{
    return m_entries;
}

std::string MapRegistry::normalizeCanonicalId(const std::string &canonicalId)
{
    std::string normalized = canonicalId;

    for (char &character : normalized)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return normalized;
}

std::string MapRegistry::normalizeFileName(const std::string &fileName)
{
    std::string normalized = fileName;

    for (char &character : normalized)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return normalized;
}
}

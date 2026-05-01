#pragma once

#include "game/tables/MapStats.h"

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class MapRegistry
{
public:
    void initialize(const std::vector<MapStatsEntry> &entries);

    std::optional<MapStatsEntry> findById(int id) const;
    std::optional<MapStatsEntry> findByCanonicalId(const std::string &canonicalId) const;
    std::optional<MapStatsEntry> findByFileName(const std::string &fileName) const;
    std::optional<MapStatsEntry> findByWorldAndFileName(
        const std::string &worldId,
        const std::string &fileName
    ) const;
    const std::vector<MapStatsEntry> &getEntries() const;

private:
    static std::string normalizeCanonicalId(const std::string &canonicalId);
    static std::string normalizeFileName(const std::string &fileName);

    std::vector<MapStatsEntry> m_entries;
};
}

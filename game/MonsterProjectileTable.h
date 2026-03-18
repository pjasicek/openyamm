#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct MonsterProjectileEntry
{
    std::string token;
    std::string normalizedToken;
    int objectId = 0;
    int impactObjectId = 0;
};

class MonsterProjectileTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const MonsterProjectileEntry *findByToken(const std::string &token) const;

private:
    std::vector<MonsterProjectileEntry> m_entries;
    std::unordered_map<std::string, size_t> m_entryIndexByNormalizedToken;
};
}

#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct MonsterEntry
{
    uint16_t height = 0;
    uint16_t radius = 0;
    uint16_t movementSpeed = 0;
    int16_t toHitRadius = 0;
    uint32_t tintColor = 0;
    std::array<uint16_t, 4> soundSampleIds = {};
    std::string internalName;
    std::array<std::string, 8> spriteNames = {};
};

class MonsterTable
{
public:
    struct MonsterDisplayNameEntry
    {
        int id = 0;
        std::string pictureName;
        std::string displayName;
    };

    bool loadFromBytes(const std::vector<uint8_t> &bytes);
    bool loadDisplayNamesFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadUniqueNamesFromRows(const std::vector<std::vector<std::string>> &rows);
    const MonsterEntry *findByInternalName(const std::string &internalName) const;
    const MonsterEntry *findById(int16_t monsterId) const;
    const MonsterDisplayNameEntry *findDisplayEntryById(int id) const;
    std::optional<std::string> findDisplayNameByInternalName(const std::string &internalName) const;
    std::optional<std::string> getUniqueName(int32_t uniqueNameIndex) const;
    const std::vector<MonsterEntry> &getEntries() const;

private:
    std::vector<MonsterEntry> m_entries;
    std::vector<MonsterDisplayNameEntry> m_displayNames;
    std::vector<std::string> m_uniqueNames;
};
}

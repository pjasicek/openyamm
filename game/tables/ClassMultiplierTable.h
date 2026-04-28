#pragma once

#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class ClassManaMode
{
    None,
    Intellect,
    Personality,
    Mixed,
    Level,
};

struct ClassMultiplierEntry
{
    std::string className;
    int baseHealth = 0;
    int healthPerLevel = 0;
    int baseMana = 0;
    int manaPerLevel = 0;
    ClassManaMode manaMode = ClassManaMode::None;
};

class ClassMultiplierTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const ClassMultiplierEntry *get(const std::string &className) const;
    const std::unordered_map<std::string, ClassMultiplierEntry> &entries() const;

private:
    std::unordered_map<std::string, ClassMultiplierEntry> m_entries;
};
}

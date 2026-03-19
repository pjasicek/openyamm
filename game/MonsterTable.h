#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
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
    enum class MonsterMovementType
    {
        Short,
        Medium,
        Long,
        Global,
        Free,
        Stationary,
    };

    enum class MonsterAiType
    {
        Suicide,
        Wimp,
        Normal,
        Aggressive,
    };

    enum class MonsterAttackStyle
    {
        MeleeOnly,
        MixedMeleeRanged,
        Ranged,
    };

    enum class LootItemKind
    {
        None,
        Any,
        Gem,
        Ring,
        Amulet,
        Boots,
        Gauntlets,
        Cloak,
        Wand,
        Ore,
        Scroll,
        Sword,
        Dagger,
        Spear,
        Chain,
        Plate,
        Club,
        Staff,
        Bow,
    };

    struct LootPrototype
    {
        int goldDiceRolls = 0;
        int goldDiceSides = 0;
        int itemChance = 0;
        int itemLevel = 0;
        LootItemKind itemKind = LootItemKind::None;
    };

    struct MonsterStatsEntry
    {
        struct DamageProfile
        {
            int diceRolls = 0;
            int diceSides = 0;
            int bonus = 0;
        };

        int id = 0;
        std::string name;
        std::string pictureName;
        int level = 0;
        int hitPoints = 0;
        int armorClass = 0;
        int hostility = 0;
        int speed = 0;
        int recovery = 0;
        bool canFly = false;
        MonsterMovementType movementType = MonsterMovementType::Short;
        MonsterAiType aiType = MonsterAiType::Suicide;
        std::string attack1MissileType;
        bool attack1HasMissile = false;
        DamageProfile attack1Damage = {};
        std::string attack2MissileType;
        bool attack2HasMissile = false;
        int attack2Chance = 0;
        DamageProfile attack2Damage = {};
        std::string spell1Descriptor;
        std::string spell1Name;
        bool hasSpell1 = false;
        int spell1UseChance = 0;
        std::string spell2Descriptor;
        std::string spell2Name;
        bool hasSpell2 = false;
        int spell2UseChance = 0;
        MonsterAttackStyle attackStyle = MonsterAttackStyle::MeleeOnly;
        std::string treasureDefinition;
        LootPrototype loot = {};
        uint16_t attackSoundId = 0;
        uint16_t deathSoundId = 0;
        uint16_t winceSoundId = 0;
        uint16_t awareSoundId = 0;
    };

    struct MonsterDisplayNameEntry
    {
        int id = 0;
        std::string pictureName;
        std::string displayName;
    };

    bool loadFromBytes(const std::vector<uint8_t> &bytes);
    bool loadDisplayNamesFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadStatsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadRelationsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadUniqueNamesFromRows(const std::vector<std::vector<std::string>> &rows);
    const MonsterEntry *findByInternalName(const std::string &internalName) const;
    const MonsterEntry *findById(int16_t monsterId) const;
    const MonsterStatsEntry *findStatsById(int16_t monsterId) const;
    const MonsterStatsEntry *findStatsByPictureName(const std::string &pictureName) const;
    const MonsterDisplayNameEntry *findDisplayEntryById(int id) const;
    std::optional<std::string> findDisplayNameByInternalName(const std::string &internalName) const;
    std::optional<std::string> getUniqueName(int32_t uniqueNameIndex) const;
    int getRelationToParty(int16_t monsterId) const;
    int getRelationBetweenMonsters(int16_t leftMonsterId, int16_t rightMonsterId) const;
    bool isHostileToParty(int16_t monsterId) const;
    bool isLikelySameFaction(int16_t leftMonsterId, int16_t rightMonsterId) const;
    const std::vector<MonsterEntry> &getEntries() const;

private:
    static size_t relationIndexForMonsterId(int16_t monsterId);

    std::vector<MonsterEntry> m_entries;
    std::vector<MonsterDisplayNameEntry> m_displayNames;
    std::vector<std::string> m_uniqueNames;
    std::unordered_map<int, MonsterStatsEntry> m_statsById;
    std::unordered_map<std::string, int> m_statsIdByPictureName;
    std::vector<std::string> m_relationLabels;
    std::vector<std::vector<int>> m_relations;
};
}

#pragma once

#include "game/party/CharacterState.h"
#include "game/party/SkillData.h"
#include "game/tables/MonsterTable.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class CombatDamageType;

// The MM9 world's hirelings (worlds/mm9/data_tables/hirelings.txt, written by
// tools/mm9_import_discovery/generate_mm9_hirelings.py; devdocs/mm9/MM9_HIRELINGS_PLAN.md).
enum class Mm9HirelingKind : uint8_t
{
    // A paid retainer: at most two at a time.
    Paid,
    // Forad or Tamur: the third slot.
    Story,
};

// The hireling's -15 dialogue service, once per cooldown.
enum class Mm9HirelingService : uint8_t
{
    None,
    TownPortal,
    Heal,
    HealCure,
};

struct Mm9HirelingSkillBonus
{
    // A canonical OpenYAMM skill name (SkillData.h).
    std::string skillName;
    int amount = 0;
};

// What having the hireling along gives the party.
struct Mm9HirelingPassives
{
    int goldPercent = 0;
    int experiencePercent = 0;
    bool identifyAlways = false;
    bool repairAlways = false;
    std::vector<Mm9HirelingSkillBonus> skillBonuses;
};

struct Mm9HirelingAttack
{
    bool present = false;
    CombatDamageType damageType = {};
    MonsterTable::MonsterStatsEntry::DamageProfile damage = {};
    // The engine missile token of a ranged attack; empty for melee.
    std::string missile;
};

struct Mm9HirelingSpell
{
    // Lowercased, as monster spell names (parseMonsterSpellName).
    std::string name;
    SkillMastery mastery = SkillMastery::None;
    uint32_t skillLevel = 0;
};

struct Mm9Hireling
{
    uint32_t rudeId = 0;
    std::string name;
    Mm9HirelingKind kind = Mm9HirelingKind::Paid;
    // The first face of its portrait family (9npcNN-01).
    std::string portrait;
    uint32_t monsterRow = 0;
    // Set while the hireling is with the party (MM9 key + 90000).
    uint32_t hireQBit = 0;
    int hireFee = 0;
    // Gold every 28 days.
    int wage = 0;
    // The share of found gold the dialogue names; MM9 never takes it (MM9_HIRELINGS.md section 5).
    int goldSharePercent = 0;
    Mm9HirelingService service = Mm9HirelingService::None;
    int serviceCooldownHours = 0;
    std::vector<CharacterCondition> curedConditions;
    Mm9HirelingPassives passives;
    uint32_t level = 0;
    int hitPoints = 0;
    int armorClass = 0;
    float recoverySeconds = 0.0f;
    // Attack 1 in reach, attack 2 beyond it.
    Mm9HirelingAttack attack1;
    Mm9HirelingAttack attack2;
    // The casters' two spells; spell1SharePercent of their casts use the first.
    std::vector<Mm9HirelingSpell> spells;
    int spell1SharePercent = 0;
    // On the MM6-MM8 schools; magic is unused.
    CharacterResistanceSet resistances = {};
};

class Mm9HirelingTable
{
public:
    void clear();
    // The first row is the header; false (with errors()) when a row is malformed or the table is empty.
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const Mm9Hireling *find(uint32_t rudeId) const;
    const std::vector<Mm9Hireling> &entries() const;
    const std::vector<std::string> &errors() const;

private:
    void addError(size_t rowNumber, const std::string &message);

    std::vector<Mm9Hireling> m_entries;
    std::unordered_map<uint32_t, size_t> m_entryIndexByRudeId;
    std::vector<std::string> m_errors;
};
}

#include "game/mm9/Mm9HirelingTable.h"

#include "game/gameplay/GameMechanics.h"

#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <cstdlib>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<std::string_view, 35> ExpectedColumns = {
    "rude_id", "name", "kind", "portrait", "monster_row", "hire_qbit", "hire_fee", "wage", "gold_share_percent",
    "service", "service_cooldown_hours", "cured_conditions", "passive",
    "level", "hp", "ac", "recovery_seconds",
    "attack1_type", "attack1_damage", "attack2_type", "attack2_damage", "attack2_missile",
    "spell1", "spell1_share_percent", "spell2",
    "res_fire", "res_air", "res_water", "res_earth", "res_spirit", "res_mind", "res_body", "res_light", "res_dark",
    "res_physical",
};

enum Column : size_t
{
    RudeId,
    Name,
    Kind,
    Portrait,
    MonsterRow,
    HireQBit,
    HireFee,
    Wage,
    GoldSharePercent,
    Service,
    ServiceCooldownHours,
    CuredConditions,
    Passive,
    Level,
    HitPoints,
    ArmorClass,
    RecoverySeconds,
    Attack1Type,
    Attack1Damage,
    Attack2Type,
    Attack2Damage,
    Attack2Missile,
    Spell1,
    Spell1SharePercent,
    Spell2,
    ResistanceFire,
    ResistanceAir,
    ResistanceWater,
    ResistanceEarth,
    ResistanceSpirit,
    ResistanceMind,
    ResistanceBody,
    ResistanceLight,
    ResistanceDark,
    ResistancePhysical,
};

bool parseInt(const std::string &value, int &result, int minimum = 0)
{
    const char *pBegin = value.data();
    const char *pEnd = pBegin + value.size();
    const std::from_chars_result parseResult = std::from_chars(pBegin, pEnd, result);
    return parseResult.ec == std::errc() && parseResult.ptr == pEnd && result >= minimum;
}

bool parseUnsigned(const std::string &value, uint32_t &result)
{
    const char *pBegin = value.data();
    const char *pEnd = pBegin + value.size();
    const std::from_chars_result parseResult = std::from_chars(pBegin, pEnd, result);
    return parseResult.ec == std::errc() && parseResult.ptr == pEnd;
}

// strtof: Android's libc++ has no floating-point from_chars.
bool parsePositiveFloat(const std::string &value, float &result)
{
    if (value.empty())
    {
        return false;
    }
    char *pEnd = nullptr;
    result = std::strtof(value.c_str(), &pEnd);
    return pEnd == value.c_str() + value.size() && std::isfinite(result) && result > 0.0f;
}

std::vector<std::string> splitList(const std::string &value)
{
    std::vector<std::string> result;
    size_t begin = 0;
    while (begin < value.size())
    {
        const size_t end = value.find('|', begin);
        result.push_back(value.substr(begin, end == std::string::npos ? std::string::npos : end - begin));
        if (end == std::string::npos)
        {
            break;
        }
        begin = end + 1;
    }
    return result;
}

bool parseKind(const std::string &value, Mm9HirelingKind &kind)
{
    if (value == "paid")
    {
        kind = Mm9HirelingKind::Paid;
        return true;
    }
    if (value == "story")
    {
        kind = Mm9HirelingKind::Story;
        return true;
    }
    return false;
}

bool parseService(const std::string &value, Mm9HirelingService &service)
{
    if (value == "none")
    {
        service = Mm9HirelingService::None;
    }
    else if (value == "town_portal")
    {
        service = Mm9HirelingService::TownPortal;
    }
    else if (value == "heal")
    {
        service = Mm9HirelingService::Heal;
    }
    else if (value == "heal_cure")
    {
        service = Mm9HirelingService::HealCure;
    }
    else
    {
        return false;
    }
    return true;
}

bool parseConditions(const std::string &value, std::vector<CharacterCondition> &conditions)
{
    for (const std::string &name : splitList(value))
    {
        bool found = false;
        for (const auto &[candidate, condition] : CharacterConditionNames)
        {
            if (candidate == name)
            {
                conditions.push_back(condition);
                found = true;
                break;
            }
        }
        if (!found)
        {
            return false;
        }
    }
    return true;
}

// gold_percent:N, experience_percent:N, identify_always, repair_always and skill:Name+N, joined by |.
bool parsePassives(const std::string &value, Mm9HirelingPassives &passives)
{
    for (const std::string &token : splitList(value))
    {
        const size_t colon = token.find(':');
        const std::string key = token.substr(0, colon);
        const std::string argument = colon == std::string::npos ? std::string() : token.substr(colon + 1);
        if (key == "identify_always" && colon == std::string::npos)
        {
            passives.identifyAlways = true;
        }
        else if (key == "repair_always" && colon == std::string::npos)
        {
            passives.repairAlways = true;
        }
        else if (key == "gold_percent")
        {
            if (!parseInt(argument, passives.goldPercent, 1))
            {
                return false;
            }
        }
        else if (key == "experience_percent")
        {
            if (!parseInt(argument, passives.experiencePercent, 1))
            {
                return false;
            }
        }
        else if (key == "skill")
        {
            const size_t plus = argument.find('+');
            Mm9HirelingSkillBonus bonus = {};
            bonus.skillName = argument.substr(0, plus);
            if (plus == std::string::npos || !skillIdForSkillName(bonus.skillName)
                || canonicalSkillName(bonus.skillName) != bonus.skillName
                || !parseInt(argument.substr(plus + 1), bonus.amount, 1))
            {
                return false;
            }
            passives.skillBonuses.push_back(std::move(bonus));
        }
        else
        {
            return false;
        }
    }
    return true;
}

bool parseAttack(const std::string &type, const std::string &damage, Mm9HirelingAttack &attack)
{
    if (type == "0")
    {
        return damage == "0";
    }
    attack.damage = parseDamageProfile(damage);
    if (type.empty() || attack.damage.diceRolls <= 0 || attack.damage.diceSides <= 0)
    {
        return false;
    }
    attack.present = true;
    attack.damageType = GameMechanics::parseCombatDamageType(type);
    return true;
}

// Name,Mastery,Skill (MM9_SPELL_MAPPING.md names, N/B/E/M/G masteries); empty for none.
bool parseSpell(const std::string &value, std::vector<Mm9HirelingSpell> &spells)
{
    if (value.empty())
    {
        return true;
    }
    Mm9HirelingSpell spell = {};
    spell.name = parseMonsterSpellName(value);
    spell.mastery = parseMonsterSpellSkillMastery(value);
    spell.skillLevel = parseMonsterSpellSkillLevel(value);
    if (spell.name.empty() || spell.mastery == SkillMastery::None || spell.skillLevel == 0)
    {
        return false;
    }
    spells.push_back(std::move(spell));
    return true;
}

bool parseResistance(const std::string &value, int &resistance)
{
    resistance = parseMonsterResistanceValue(value);
    return resistance != 0 || value == "0";
}
}

void Mm9HirelingTable::clear()
{
    m_entries.clear();
    m_entryIndexByRudeId.clear();
    m_errors.clear();
}

bool Mm9HirelingTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    clear();
    if (rows.empty() || rows[0].size() != ExpectedColumns.size()
        || !std::equal(ExpectedColumns.begin(), ExpectedColumns.end(), rows[0].begin()))
    {
        addError(1, "the header does not name the expected 35 columns");
        return false;
    }

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];
        const size_t rowNumber = rowIndex + 1;
        if (row.empty() || (row.size() == 1 && row[0].empty()))
        {
            continue;
        }
        if (row.size() != ExpectedColumns.size())
        {
            addError(rowNumber, "expected 35 columns");
            continue;
        }

        Mm9Hireling entry = {};
        entry.name = row[Name];
        entry.portrait = row[Portrait];
        if (!parseUnsigned(row[RudeId], entry.rudeId) || entry.rudeId == 0 || entry.name.empty()
            || !parseKind(row[Kind], entry.kind) || entry.portrait.empty()
            || !parseUnsigned(row[MonsterRow], entry.monsterRow)
            || !parseUnsigned(row[HireQBit], entry.hireQBit) || entry.hireQBit == 0)
        {
            addError(rowNumber, "invalid identity (rude id, name, kind, portrait, monster row or hire qbit)");
            continue;
        }
        if (!parseInt(row[HireFee], entry.hireFee) || !parseInt(row[Wage], entry.wage)
            || !parseInt(row[GoldSharePercent], entry.goldSharePercent) || entry.goldSharePercent > 100
            || (entry.kind == Mm9HirelingKind::Story && (entry.hireFee != 0 || entry.wage != 0)))
        {
            addError(rowNumber, "invalid fee, wage or gold share (story companions are free)");
            continue;
        }
        if (!parseService(row[Service], entry.service)
            || !parseInt(row[ServiceCooldownHours], entry.serviceCooldownHours)
            || (entry.service == Mm9HirelingService::None) != (entry.serviceCooldownHours == 0)
            || !parseConditions(row[CuredConditions], entry.curedConditions)
            || (entry.service == Mm9HirelingService::HealCure) == entry.curedConditions.empty())
        {
            addError(rowNumber, "invalid service, cooldown or cured conditions");
            continue;
        }
        if (!parsePassives(row[Passive], entry.passives))
        {
            addError(rowNumber, "invalid passive '" + row[Passive] + "'");
            continue;
        }
        if (!parseUnsigned(row[Level], entry.level) || entry.level == 0
            || !parseInt(row[HitPoints], entry.hitPoints, 1) || !parseInt(row[ArmorClass], entry.armorClass)
            || !parsePositiveFloat(row[RecoverySeconds], entry.recoverySeconds))
        {
            addError(rowNumber, "invalid level, hit points, armor class or recovery");
            continue;
        }
        if (!parseAttack(row[Attack1Type], row[Attack1Damage], entry.attack1) || !entry.attack1.present
            || !parseAttack(row[Attack2Type], row[Attack2Damage], entry.attack2)
            || (entry.attack2.present ? row[Attack2Missile] == "0" : row[Attack2Missile] != "0"))
        {
            addError(rowNumber, "invalid attack (attack 1 is required; attack 2 needs a missile)");
            continue;
        }
        entry.attack2.missile = entry.attack2.present ? row[Attack2Missile] : std::string();
        if (!parseSpell(row[Spell1], entry.spells) || !parseSpell(row[Spell2], entry.spells)
            || (row[Spell1].empty() && !row[Spell2].empty())
            || !parseInt(row[Spell1SharePercent], entry.spell1SharePercent) || entry.spell1SharePercent > 100
            || entry.spells.empty() != (entry.spell1SharePercent == 0)
            || (entry.spells.size() == 1 && entry.spell1SharePercent != 100))
        {
            addError(rowNumber, "invalid spells or spell share");
            continue;
        }
        CharacterResistanceSet &resistances = entry.resistances;
        if (!parseResistance(row[ResistanceFire], resistances.fire)
            || !parseResistance(row[ResistanceAir], resistances.air)
            || !parseResistance(row[ResistanceWater], resistances.water)
            || !parseResistance(row[ResistanceEarth], resistances.earth)
            || !parseResistance(row[ResistanceSpirit], resistances.spirit)
            || !parseResistance(row[ResistanceMind], resistances.mind)
            || !parseResistance(row[ResistanceBody], resistances.body)
            || !parseResistance(row[ResistanceLight], resistances.light)
            || !parseResistance(row[ResistanceDark], resistances.dark)
            || !parseResistance(row[ResistancePhysical], resistances.physical))
        {
            addError(rowNumber, "invalid resistance");
            continue;
        }
        if (m_entryIndexByRudeId.contains(entry.rudeId))
        {
            addError(rowNumber, "duplicate rude id " + row[RudeId]);
            continue;
        }

        m_entryIndexByRudeId[entry.rudeId] = m_entries.size();
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty() && m_errors.empty();
}

const Mm9Hireling *Mm9HirelingTable::find(uint32_t rudeId) const
{
    const auto iterator = m_entryIndexByRudeId.find(rudeId);
    return iterator != m_entryIndexByRudeId.end() ? &m_entries[iterator->second] : nullptr;
}

const std::vector<Mm9Hireling> &Mm9HirelingTable::entries() const
{
    return m_entries;
}

const std::vector<std::string> &Mm9HirelingTable::errors() const
{
    return m_errors;
}

void Mm9HirelingTable::addError(size_t rowNumber, const std::string &message)
{
    m_errors.push_back("hirelings.txt row " + std::to_string(rowNumber) + ": " + message);
}
}

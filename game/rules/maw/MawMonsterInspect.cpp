#include "game/rules/maw/MawMonsterInspect.h"

#include "game/party/Party.h"
#include "game/rules/ActorRulesetFacts.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawExperienceRules.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/rules/maw/MawRules.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>

namespace OpenYAMM::Game
{
namespace
{
// The special attacks MAW names on the panel (effectNames, zzMaw-Monsters.lua:3682-3688); the others show nothing.
std::string specialAttackName(MonsterSpecialAttackKind kind)
{
    switch (kind)
    {
        case MonsterSpecialAttackKind::Curse: return "Curse";
        case MonsterSpecialAttackKind::Weak: return "Weakness";
        case MonsterSpecialAttackKind::Sleep: return "Sleep";
        case MonsterSpecialAttackKind::Fear: return "Fear";
        case MonsterSpecialAttackKind::Insane: return "Insanity";
        case MonsterSpecialAttackKind::PoisonWeak: return "Poison 1";
        case MonsterSpecialAttackKind::PoisonMedium: return "Poison 2";
        case MonsterSpecialAttackKind::PoisonSevere: return "Poison 3";
        case MonsterSpecialAttackKind::DiseaseWeak: return "Disease 1";
        case MonsterSpecialAttackKind::DiseaseMedium: return "Disease 2";
        case MonsterSpecialAttackKind::DiseaseSevere: return "Disease 3";
        case MonsterSpecialAttackKind::Paralyze: return "Paralysis";
        case MonsterSpecialAttackKind::Unconscious: return "Unconscious";
        case MonsterSpecialAttackKind::Dead: return "Death";
        case MonsterSpecialAttackKind::Petrify: return "Stone";
        case MonsterSpecialAttackKind::Eradicate: return "Eradication";
        case MonsterSpecialAttackKind::Aging: return "Premature ageing";
        case MonsterSpecialAttackKind::ManaDrain: return "Spell drain";
        default: return {};
    }
}

// The range 95 % of hits of mean `damage` fall in: the mean of two draws of 75-125 %, whose standard deviation is
// damage x 0.5 / sqrt(24), x 1.96, inside the spread's bounds. MAW widens attack 2's range as if it rolled once, but
// both attacks roll twice (DEVIATIONS 130).
std::string damageRange(const MawRules &rules, const MonsterInspectQuery &query, double damage, CombatDamageType type)
{
    const double halfWidth = std::sqrt(std::pow(damage * 0.5, 2) / 12 / 2) * 1.96;
    double low = mawRound(std::max(damage - halfWidth, damage * 0.75));
    double high = mawRound(std::min(damage + halfWidth, damage * 1.25));
    const Character *pViewer = query.pParty != nullptr ? query.pParty->member(query.viewerIndex) : nullptr;

    if (!query.rawNumbers && pViewer != nullptr)
    {
        const double taken = mawDamageTakenPercent(rules, *pViewer, query.pParty->itemTable(),
            query.pParty->standardItemEnchantTable(), query.pParty->specialItemEnchantTable(), type,
            query.pFacts->level) / 100;
        low = mawRound(low * taken);
        high = mawRound(high * taken);
    }

    return mawShortNumber(low) + "-" + mawShortNumber(high);
}
}

std::string mawShortNumber(double number, bool coloured, int digits)
{
    static constexpr std::array<std::pair<double, const char *>, 3> Scales = {{
        {1e9, "B"}, {1e6, "M"}, {1e3, "K"},
    }};
    // K yellow, M orange, B red, as Might and Magic's inline colour codes (R5G6B5).
    static constexpr std::array<const char *, 3> Colours = {"\f63488", "\f64800", "\f65516"};

    for (size_t scale = 0; scale < Scales.size(); ++scale)
    {
        if (std::abs(number) < Scales[scale].first)
        {
            continue;
        }

        double value = number / Scales[scale].first;
        size_t shown = scale;
        const auto decimalsFor = [digits](double shownValue)
        {
            const int integerDigits = std::abs(shownValue) < 10 ? 1 : (std::abs(shownValue) < 100 ? 2 : 3);
            return std::max(0, digits - integerDigits);
        };

        // Rounding to the digits shown may reach 1000: carry it to the next suffix.
        if (std::abs(value) >= 1000 - 0.5 * std::pow(10.0, -decimalsFor(value)) && shown > 0)
        {
            value /= 1000;
            --shown;
        }

        const int decimals = decimalsFor(value);
        char buffer[32] = {};
        std::snprintf(buffer, sizeof(buffer), "%.*f", decimals, value);
        std::string text = buffer;

        if (text.find('.') != std::string::npos)
        {
            text.erase(text.find_last_not_of('0') + 1);

            if (text.back() == '.')
            {
                text.pop_back();
            }
        }

        return coloured ? std::string(Colours[shown]) + text + Scales[shown].second + "\f00000"
                        : text + Scales[shown].second;
    }

    return std::to_string(int64_t(mawRound(number)));
}

MonsterInspectNumbers mawMonsterInspectNumbers(const MawRules &rules, const MonsterInspectQuery &query)
{
    MonsterInspectNumbers numbers;

    if (query.pStats == nullptr || query.pFacts == nullptr || query.pFacts->empty())
    {
        return numbers;
    }

    const MonsterTable::MonsterStatsEntry &stats = *query.pStats;
    const ActorRulesetFacts &facts = *query.pFacts;
    numbers.level = facts.level;

    // A dimension map's monster damage affix shows in the numbers (zzMaw-Monsters.lua:1989-1991).
    const double mapDamage = 1 + rules.mapAffix(MawMapAffix::MonsterDamage).value_or(0) / 100;
    numbers.damageRows.push_back(damageRange(
        rules, query, facts.attack1Damage * mapDamage, GameMechanics::parseCombatDamageType(stats.attack1Type)));

    if (query.hasAttack2)
    {
        numbers.damageRows.push_back(damageRange(
            rules, query, facts.attack2Damage * mapDamage, GameMechanics::parseCombatDamageType(stats.attack2Type)));
    }

    if (query.spellId != 0)
    {
        // A spell deals the monster's damage for its element (zzMaw-Monsters.lua:2037-2046).
        const int partyCount = query.pParty != nullptr ? int(std::max<size_t>(1, query.pParty->members().size())) : 5;
        const double spellBase = mawMonsterBaseDamage(rules, facts, partyCount, query.spellDamageType);
        numbers.spellDamage = damageRange(
            rules, query, spellBase * mapDamage * mawMonsterSpellMultiplier(query.spellId), query.spellDamageType);
    }

    // The attack the monster lands: the Doom modes' roll in place of its own, poisons for diseases below level 20
    // (MON:3741-3747). MAW names a rolled one even when the monster's attack has no strength to land it; here the roll
    // shows only on an attack that can carry it (GAPS P9.D2).
    const bool doomRoll = facts.doomSpecialAttack != 0 && stats.specialAttackLevel > 0;
    MonsterSpecialAttackKind kind =
        doomRoll ? MonsterSpecialAttackKind(facts.doomSpecialAttack) : stats.specialAttackKind;

    if (facts.level < 20 && kind >= MonsterSpecialAttackKind::DiseaseWeak
        && kind <= MonsterSpecialAttackKind::DiseaseSevere)
    {
        kind = MonsterSpecialAttackKind(int(kind) - 3);
    }

    const std::string special = specialAttackName(kind);

    if (!special.empty())
    {
        numbers.effectLines.push_back("Special: " + special);
    }

    const Character *pViewer = query.pParty != nullptr ? query.pParty->member(query.viewerIndex) : nullptr;

    if (pViewer != nullptr && query.maxHp > 0)
    {
        const int partySize = int(std::max<size_t>(1, query.pParty->members().size()));
        const MawMemberKillExperience share = mawMemberKillExperience(
            rules, *pViewer, partySize, double(facts.experience) / partySize, query.maxHp);
        numbers.effectLines.push_back("Experience: " + std::to_string(int64_t(mawRound(share.award))));
    }

    if (facts.spearDamageTaken > 0)
    {
        numbers.effectLines.push_back(
            "Physical damage taken: +" + std::to_string(int(mawRound(facts.spearDamageTaken))) + "%");
    }

    if (facts.legendaryDamageTaken > 0)
    {
        numbers.effectLines.push_back(
            "All damage taken: +" + std::to_string(int(mawRound(facts.legendaryDamageTaken))) + "%");
    }

    return numbers;
}
}

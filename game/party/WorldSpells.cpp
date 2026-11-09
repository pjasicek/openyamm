#include "game/party/WorldSpells.h"

#include "engine/Localization.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/SpellRules.h"
#include "game/tables/SpellTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
// The speed-up's share added while the party is in the green state.
constexpr float FleetFootGreenBonus = 0.25f;
constexpr char FleetFootName[] = "Fleet Foot";
}

bool castsFleetFoot(const Party &party, uint32_t spellId)
{
    // Air Magic's Fly and the Dragon's Flight (MAW's dragons, the user 2026-11-09): MM9 has no flying.
    return party.fleetFootWorld()
        && (spellId == spellIdValue(SpellId::Fly) || spellId == spellIdValue(SpellId::Flight));
}

int fleetFootSpeedPercent(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Grandmaster:
            return 175;
        case SkillMastery::Master:
            return 150;
        default:
            return 125;
    }
}

float fleetFootDurationSeconds(uint32_t skillLevel, SkillMastery mastery)
{
    const float minutesPerPoint = mastery == SkillMastery::Grandmaster ? 60.0f
        : mastery == SkillMastery::Master                              ? 30.0f
                                                                       : 15.0f;
    return float(skillLevel) * minutesPerPoint * 60.0f;
}

float fleetFootSpeedMultiplier(int speedPercent, bool greenAlert)
{
    const float speedUp = float(std::max(speedPercent - 100, 0)) / 100.0f;
    return 1.0f + speedUp * (greenAlert ? 1.0f + FleetFootGreenBonus : 1.0f);
}

std::string partySpellName(const Party *pParty, const Character &caster, const SpellEntry &spell)
{
    if (pParty != nullptr && castsFleetFoot(*pParty, uint32_t(spell.id)))
    {
        return FleetFootName;
    }

    return gameRulesFor(pParty).spells.spellName(caster, spell);
}

SpellTooltipText partySpellTooltip(const Party &party, const Character &caster, const SpellEntry &spell)
{
    if (!castsFleetFoot(party, uint32_t(spell.id)))
    {
        return party.rules().spells.spellTooltip(party, caster, spell);
    }

    // Translated here, as a ruleset's own texts are; the slot's mastery requirement stays the table's (Master).
    const auto masteryLine = [](SkillMastery mastery, const std::string &duration)
    {
        return Engine::tr("Speed +{percent} %, {duration}",
            {{"percent", int64_t(fleetFootSpeedPercent(mastery) - 100)}, {"duration", duration}});
    };
    SpellTooltipText text;
    text.name = FleetFootName;
    text.description = Engine::tr(
        "Fleet Foot quickens the party's step, so it walks and runs faster. The spell works a quarter better while no "
        "hostile creature is near.");
    text.masteryLines = {spell.normalText, spell.expertText,
        masteryLine(SkillMastery::Master, Engine::tr("30 minutes per point of skill")),
        masteryLine(SkillMastery::Grandmaster, Engine::tr("1 hour per point of skill"))};
    return text;
}
}

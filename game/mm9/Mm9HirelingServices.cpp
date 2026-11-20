#include "game/mm9/Mm9HirelingServices.h"

#include "engine/Localization.h"
#include "game/audio/SoundIds.h"
#include "game/gameplay/GameMechanics.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"

#include <algorithm>
#include <array>

namespace OpenYAMM::Game
{
namespace
{
// object@0x100556c0 pays the retainers by MONSTERS row in this order.
constexpr std::array<uint32_t, 13> Mm9WageOrderMonsterRows = {
    279, 280, 281, 282, 284, 285, 286, 288, 289, 290, 291, 283, 287};

size_t wageOrderRank(uint32_t monsterRow)
{
    const auto found = std::find(Mm9WageOrderMonsterRows.begin(), Mm9WageOrderMonsterRows.end(), monsterRow);
    return size_t(found - Mm9WageOrderMonsterRows.begin());
}

void setHireKey(Party &party, const Mm9Hireling &row, bool value)
{
    if (row.hireQBit != 0)
    {
        party.setQuestBit(row.hireQBit, value);
    }
}

// MM9: the first member able to speak says voice event 23 (object@0x100559ad).
void speakNotEnoughGold(Party &party)
{
    for (size_t memberIndex = 0; memberIndex < party.memberCount(); ++memberIndex)
    {
        const Character *pMember = party.member(memberIndex);

        if (pMember != nullptr && GameMechanics::canAct(*pMember))
        {
            party.requestSpeech(memberIndex, SpeechId::NotEnoughGold);
            return;
        }
    }
}
}

Mm9HireOutcome hireMm9Hireling(Party &party, const Mm9Hireling &row)
{
    if (!party.canAddHireling(row))
    {
        return Mm9HireOutcome::Refused;
    }

    if (row.kind == Mm9HirelingKind::Paid && party.rules().classes.paidHirelingRefusal())
    {
        return Mm9HireOutcome::Declines;
    }

    const int fee = row.kind == Mm9HirelingKind::Paid ? std::max(0, row.hireFee) : 0;

    if (party.gold() < fee)
    {
        return Mm9HireOutcome::NotEnoughGold;
    }

    if (!party.addHireling(row))
    {
        return Mm9HireOutcome::Refused;
    }

    if (fee > 0)
    {
        party.addGold(-fee, GoldReason::Other);
        party.requestSound(SoundId::Gold);
    }

    setHireKey(party, row, true);
    return Mm9HireOutcome::Hired;
}

bool dismissMm9Hireling(Party &party, const Mm9Hireling &row)
{
    if (!party.removeHireling(row.rudeId))
    {
        return false;
    }

    setHireKey(party, row, false);
    return true;
}

Mm9HirelingServiceOutcome useMm9HirelingService(Party &party, const Mm9Hireling &row)
{
    Mm9PartyHireling *pHireling = party.findHireling(row.rudeId);

    if (pHireling == nullptr || row.service == Mm9HirelingService::None)
    {
        return Mm9HirelingServiceOutcome::Unavailable;
    }

    const float now = party.gameMinutes();

    if (now < pHireling->serviceReadyGameMinutes)
    {
        return Mm9HirelingServiceOutcome::CoolingDown;
    }

    pHireling->serviceReadyGameMinutes = now + float(std::max(0, row.serviceCooldownHours)) * 60.0f;

    if (row.service == Mm9HirelingService::TownPortal)
    {
        return Mm9HirelingServiceOutcome::TownPortal;
    }

    // Every slot to its maximum HP (cshell@0x1002b03d), which wakes a knocked-out hireling; the dead stay dead.
    for (size_t combatantIndex = 0; combatantIndex < party.combatantCount(); ++combatantIndex)
    {
        const Character *pCombatant = party.combatant(combatantIndex);
        const int missing = pCombatant != nullptr
            ? party.reachableMaximumHealth(combatantIndex) - pCombatant->health
            : 0;

        if (missing > 0)
        {
            party.healMember(combatantIndex, missing);
        }

        if (row.service == Mm9HirelingService::HealCure)
        {
            for (CharacterCondition condition : row.curedConditions)
            {
                party.clearMemberCondition(combatantIndex, condition);
            }
        }
    }

    party.requestSound(SoundId::Heal);
    return Mm9HirelingServiceOutcome::Healed;
}

std::string mm9HirelingServiceCooldownText(const std::string &name)
{
    return Engine::tr("{name} can cast this but once per day!", {{"name", name}});
}

Mm9HirelingPassives mm9PartyHirelingPassives(const Party &party, const Mm9HirelingTable &table)
{
    Mm9HirelingPassives total = {};

    for (const Mm9PartyHireling &hireling : party.hirelings())
    {
        const Mm9Hireling *pRow = table.find(hireling.rudeId);

        if (pRow == nullptr)
        {
            continue;
        }

        const Mm9HirelingPassives &passives = pRow->passives;
        total.goldPercent += passives.goldPercent;
        total.experiencePercent += passives.experiencePercent;
        total.identifyAlways = total.identifyAlways || passives.identifyAlways;
        total.repairAlways = total.repairAlways || passives.repairAlways;
        total.skillBonuses.insert(total.skillBonuses.end(), passives.skillBonuses.begin(), passives.skillBonuses.end());
    }

    return total;
}

std::vector<uint32_t> payMm9HirelingWages(Party &party, const Mm9HirelingTable &table)
{
    std::vector<uint32_t> departed;
    const float now = party.gameMinutes();

    // Every wage due by now, the earliest first; wages due at once go in MM9's order.
    while (true)
    {
        const Mm9PartyHireling *pDue = nullptr;
        const Mm9Hireling *pDueRow = nullptr;

        for (const Mm9PartyHireling &hireling : party.hirelings())
        {
            const Mm9Hireling *pRow = table.find(hireling.rudeId);

            if (pRow == nullptr || hireling.kind != Mm9HirelingKind::Paid || hireling.nextWageGameMinutes <= 0.0f
                || hireling.nextWageGameMinutes > now)
            {
                continue;
            }

            if (pDue == nullptr || hireling.nextWageGameMinutes < pDue->nextWageGameMinutes
                || (hireling.nextWageGameMinutes == pDue->nextWageGameMinutes
                    && wageOrderRank(pRow->monsterRow) < wageOrderRank(pDueRow->monsterRow)))
            {
                pDue = &hireling;
                pDueRow = pRow;
            }
        }

        if (pDue == nullptr)
        {
            break;
        }

        const int wage = std::max(0, pDueRow->wage);

        if (party.gold() >= wage)
        {
            party.addGold(-wage, GoldReason::Other);
            party.findHireling(pDueRow->rudeId)->nextWageGameMinutes += Party::Mm9HirelingWagePeriodGameMinutes;
            continue;
        }

        party.addGold(-party.gold(), GoldReason::Other);
        departed.push_back(pDueRow->rudeId);
        dismissMm9Hireling(party, *pDueRow);
    }

    if (!departed.empty())
    {
        speakNotEnoughGold(party);
    }

    return departed;
}
}

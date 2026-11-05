#include "game/gameplay/NpcFollowerRuntime.h"

#include "game/party/Party.h"
#include "game/rules/SkillRules.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"

#include <algorithm>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t SailorProfessionId = 8;
constexpr uint32_t NavigatorProfessionId = 9;
constexpr uint32_t HorsemanProfessionId = 35;
constexpr uint32_t ExplorerProfessionId = 44;
constexpr uint32_t PirateProfessionId = 45;

NpcEntry resolvedNpcEntry(
    const EventRuntimeState &eventRuntimeState,
    const NpcDialogTable &npcDialogTable,
    uint32_t npcId)
{
    NpcEntry npc = {};
    const NpcEntry *pBaseNpc = npcDialogTable.getNpc(npcId);

    if (pBaseNpc != nullptr)
    {
        npc = *pBaseNpc;
    }
    else
    {
        npc.id = npcId;
    }

    const std::unordered_map<uint32_t, std::string>::const_iterator nameIt =
        eventRuntimeState.npcNameOverrides.find(npcId);

    if (nameIt != eventRuntimeState.npcNameOverrides.end())
    {
        npc.name = nameIt->second;
    }

    const std::unordered_map<uint32_t, uint32_t>::const_iterator pictureIt =
        eventRuntimeState.npcPictureOverrides.find(npcId);

    if (pictureIt != eventRuntimeState.npcPictureOverrides.end())
    {
        npc.pictureId = pictureIt->second;
    }

    const std::unordered_map<uint32_t, uint32_t>::const_iterator professionIt =
        eventRuntimeState.npcProfessionOverrides.find(npcId);

    if (professionIt != eventRuntimeState.npcProfessionOverrides.end())
    {
        npc.professionId = professionIt->second;
    }

    return npc;
}

int professionTransportDayReduction(uint32_t professionId, bool stable)
{
    if (stable)
    {
        switch (professionId)
        {
            case HorsemanProfessionId:
                return 2;

            case ExplorerProfessionId:
                return 1;

            default:
                return 0;
        }
    }

    switch (professionId)
    {
        case SailorProfessionId:
        case PirateProfessionId:
            return 2;

        case NavigatorProfessionId:
            return 3;

        case ExplorerProfessionId:
            return 1;

        default:
            return 0;
    }
}

}

std::vector<HiredNpcFollowerView> buildHiredNpcFollowerViews(
    const EventRuntimeState &eventRuntimeState,
    const NpcDialogTable &npcDialogTable,
    const MergedNpcProfessionTable &npcProfessionTable
)
{
    std::vector<HiredNpcFollowerView> views;
    views.reserve(eventRuntimeState.hiredNpcFollowers.size());

    for (const EventRuntimeState::HiredNpcFollower &follower : eventRuntimeState.hiredNpcFollowers)
    {
        const NpcEntry npc = resolvedNpcEntry(eventRuntimeState, npcDialogTable, follower.npcId);
        const uint32_t professionId = follower.professionId != 0 ? follower.professionId : npc.professionId;
        const MergedNpcProfessionEntry *pProfession = npcProfessionTable.get(professionId);

        HiredNpcFollowerView view = {};
        view.npcId = follower.npcId;
        view.professionId = professionId;
        view.weeklyCost = follower.weeklyCost;
        view.feePercent = follower.weeklyCost / 100u;
        view.portraitPictureId = npc.pictureId;
        view.name = npc.name;
        view.profession = pProfession != nullptr ? pProfession->profession : std::string();
        views.push_back(std::move(view));
    }

    return views;
}

std::vector<HiredNpcFollowerView> buildHiredNpcFollowerViews(
    const EventRuntimeState &eventRuntimeState,
    const Party *pParty,
    const NpcDialogTable &npcDialogTable,
    const MergedNpcProfessionTable &npcProfessionTable
)
{
    if (pParty == nullptr)
    {
        return buildHiredNpcFollowerViews(eventRuntimeState, npcDialogTable, npcProfessionTable);
    }

    EventRuntimeState syncedRuntimeState = eventRuntimeState;
    pParty->applyGlobalNpcStateTo(syncedRuntimeState);
    return buildHiredNpcFollowerViews(syncedRuntimeState, npcDialogTable, npcProfessionTable);
}

bool hiredNpcHasProfession(std::span<const HiredNpcFollower> followers, uint32_t professionId)
{
    return std::find_if(
        followers.begin(),
        followers.end(),
        [professionId](const EventRuntimeState::HiredNpcFollower &follower)
        {
            return follower.npcId != 0 && follower.professionId == professionId;
        }) != followers.end();
}

int hiredNpcTransportDayReduction(const EventRuntimeState &eventRuntimeState, bool stable)
{
    int reduction = 0;

    for (const EventRuntimeState::HiredNpcFollower &follower : eventRuntimeState.hiredNpcFollowers)
    {
        reduction += professionTransportDayReduction(follower.professionId, stable);
    }

    return reduction;
}

int hiredNpcCrossMapDayReduction(const EventRuntimeState &eventRuntimeState)
{
    int reduction = 0;

    for (const EventRuntimeState::HiredNpcFollower &follower : eventRuntimeState.hiredNpcFollowers)
    {
        switch (follower.professionId)
        {
            case 5:
                reduction += 1;
                break;
            case 6:
                reduction += 2;
                break;
            case 7:
                reduction += 3;
                break;
            case ExplorerProfessionId:
                reduction += 1;
                break;
            default:
                break;
        }
    }

    return reduction;
}

int hiredNpcWalkingTravelDays(int baseDays, const EventRuntimeState &eventRuntimeState)
{
    return baseDays <= 0 ? 0 : std::max(1, baseDays - hiredNpcCrossMapDayReduction(eventRuntimeState));
}

int hiredNpcCampingFoodCost(int baseCost, const EventRuntimeState &eventRuntimeState)
{
    return baseCost <= 0 ? 0 : std::max(1, baseCost - hiredNpcRestFoodReduction(eventRuntimeState));
}

int hiredNpcRestFoodReduction(const EventRuntimeState &eventRuntimeState)
{
    int reduction = 0;

    for (const EventRuntimeState::HiredNpcFollower &follower : eventRuntimeState.hiredNpcFollowers)
    {
        if (follower.professionId == 29 || follower.professionId == 48)
        {
            reduction += 1;
        }
        else if (follower.professionId == 30)
        {
            reduction += 2;
        }
    }

    return reduction;
}

int hiredNpcSkillBonus(
    std::span<const HiredNpcFollower> followers,
    const std::string &skillName,
    bool strongestOnly,
    const SkillRules *pRules)
{
    int bonus = 0;

    for (const EventRuntimeState::HiredNpcFollower &follower : followers)
    {
        const uint32_t professionId = follower.professionId;
        // MMerge adds every follower's bonus; a ruleset may count only the strongest (MAW) or change the amount.
        const auto add = [&bonus, strongestOnly, pRules, professionId, &skillName](int amount)
        {
            const int adjusted =
                pRules != nullptr ? pRules->followerSkillBonus(professionId, skillName, amount) : amount;
            bonus = strongestOnly ? std::max(bonus, adjusted) : bonus + adjusted;
        };

        if (skillName == "Learning")
        {
            if (professionId == 4) add(5);
            else if (professionId == 13) add(10);
            else if (professionId == 14) add(15);
        }
        else if (skillName == "Merchant")
        {
            if (professionId == 20) add(4);
            else if (professionId == 21) add(6);
            else if (professionId == 48) add(3);
            else if (professionId == 49) add(4);
            else if (professionId == 50) add(8);
        }
        else if (skillName == "DisarmTraps")
        {
            if (professionId == 25) add(4);
            else if (professionId == 26) add(6);
            else if (professionId == 51) add(8);
        }
        else if (skillName == "Perception")
        {
            if (professionId == 22) add(6);
            else if (professionId == 47) add(5);
        }
        else if (skillName == "LeatherArmor" || skillName == "ChainArmor" || skillName == "PlateArmor")
        {
            if (professionId == 46) add(2);
        }
        else if (skillName == "Staff" || skillName == "Sword" || skillName == "Dagger" || skillName == "Axe"
            || skillName == "Spear" || skillName == "Bow" || skillName == "Mace")
        {
            if (professionId == 15) add(2);
            else if (professionId == 16) add(3);
            else if (professionId == 46) add(2);
        }
        else if (skillName == "FireMagic" || skillName == "AirMagic" || skillName == "WaterMagic"
            || skillName == "EarthMagic" || skillName == "SpiritMagic" || skillName == "MindMagic"
            || skillName == "BodyMagic" || skillName == "LightMagic" || skillName == "DarkMagic")
        {
            if (professionId == 17) add(2);
            else if (professionId == 18) add(3);
            else if (professionId == 19) add(4);
        }
    }

    return bonus;
}

int hiredNpcPrimaryStatBonus(std::span<const HiredNpcFollower> followers, const std::string &statName)
{
    if (statName != "Luck")
    {
        return 0;
    }

    int bonus = 0;

    for (const EventRuntimeState::HiredNpcFollower &follower : followers)
    {
        if (follower.professionId == 27)
        {
            bonus += 5;
        }
        else if (follower.professionId == 28)
        {
            bonus += 20;
        }
        else if (follower.professionId == 47)
        {
            bonus += 10;
        }
    }

    return bonus;
}

int hiredNpcResistanceBonus(std::span<const HiredNpcFollower> followers, const std::string &resistanceName)
{
    if (resistanceName != "Fire" && resistanceName != "Air" && resistanceName != "Water" && resistanceName != "Earth")
    {
        return 0;
    }

    return 20 * std::count_if(followers.begin(), followers.end(), [](const HiredNpcFollower &follower)
    {
        return follower.professionId == 37;
    });
}

FoundGold resolveFoundGold(uint32_t goldAmount, const EventRuntimeState *pEventRuntimeState)
{
    FoundGold foundGold = {};
    foundGold.amount = goldAmount;

    if (pEventRuntimeState == nullptr || goldAmount == 0)
    {
        foundGold.partyAmount = goldAmount;
        return foundGold;
    }

    const std::vector<HiredNpcFollower> &followers = pEventRuntimeState->hiredNpcFollowers;
    uint32_t totalWeeklyCost = 0;

    for (const HiredNpcFollower &follower : followers)
    {
        totalWeeklyCost += follower.weeklyCost;
    }

    // Factor, Banker and Pirate each raise the find once, in this order.
    constexpr uint32_t FactorProfessionId = 31;
    constexpr uint32_t BankerProfessionId = 32;
    constexpr uint32_t PirateProfessionId = 45;

    if (hiredNpcHasProfession(followers, FactorProfessionId))
    {
        foundGold.amount += foundGold.amount * 10 / 100;
    }

    if (hiredNpcHasProfession(followers, BankerProfessionId))
    {
        foundGold.amount += foundGold.amount * 20 / 100;
    }

    if (hiredNpcHasProfession(followers, PirateProfessionId))
    {
        foundGold.amount += foundGold.amount * 10 / 100;
    }

    // Weekly costs are hundredths of a percent of the find; anyone with a fee takes at least one coin.
    if (totalWeeklyCost != 0)
    {
        const uint64_t share = uint64_t(foundGold.amount) * totalWeeklyCost / 10000;
        foundGold.followerShare = std::min<uint32_t>(std::max<uint64_t>(share, 1), foundGold.amount);
    }

    foundGold.partyAmount = foundGold.amount - foundGold.followerShare;
    return foundGold;
}

std::string foundGoldStatusText(const FoundGold &foundGold)
{
    if (foundGold.followerShare > 0)
    {
        return "You found " + std::to_string(foundGold.amount) + " gold (followers take "
            + std::to_string(foundGold.followerShare) + ")!";
    }

    return "You found " + std::to_string(foundGold.amount) + " gold!";
}

bool hiredNpcCanRepairItemKind(std::span<const HiredNpcFollower> followers, const std::string &equipStat)
{
    if (equipStat == "Armor" || equipStat == "Shield" || equipStat == "Helm" || equipStat == "Belt"
        || equipStat == "Cloak" || equipStat == "Gauntlets" || equipStat == "Boots")
    {
        return hiredNpcHasProfession(followers, 2);
    }

    if (equipStat == "Ring" || equipStat == "Amulet" || equipStat == "WeaponW"
        || equipStat == "Bottle" || equipStat == "Reagent" || equipStat == "Sscroll"
        || equipStat == "Book" || equipStat == "Mscroll")
    {
        return hiredNpcHasProfession(followers, 3);
    }

    return (equipStat == "Weapon" || equipStat == "Weapon2" || equipStat == "Weapon1or2"
        || equipStat == "Missile") && hiredNpcHasProfession(followers, 1);
}

}

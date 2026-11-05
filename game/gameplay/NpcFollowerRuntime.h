#pragma once

#include "game/events/EventRuntime.h"

#include <cstdint>
#include <string>
#include <span>
#include <vector>

namespace OpenYAMM::Game
{
class MergedNpcProfessionTable;
class NpcDialogTable;
class Party;
class SkillRules;

struct HiredNpcFollowerView
{
    uint32_t npcId = 0;
    uint32_t professionId = 0;
    uint32_t weeklyCost = 0;
    uint32_t feePercent = 0;
    uint32_t portraitPictureId = 0;
    std::string name;
    std::string profession;
};

// Gold the party finds in the world, chests or corpses: follower find bonuses apply, then hired followers
// take their share.
struct FoundGold
{
    uint32_t amount = 0;
    uint32_t followerShare = 0;
    uint32_t partyAmount = 0;
};

std::vector<HiredNpcFollowerView> buildHiredNpcFollowerViews(
    const EventRuntimeState &eventRuntimeState,
    const NpcDialogTable &npcDialogTable,
    const MergedNpcProfessionTable &npcProfessionTable
);

std::vector<HiredNpcFollowerView> buildHiredNpcFollowerViews(
    const EventRuntimeState &eventRuntimeState,
    const Party *pParty,
    const NpcDialogTable &npcDialogTable,
    const MergedNpcProfessionTable &npcProfessionTable
);

bool hiredNpcHasProfession(std::span<const HiredNpcFollower> followers, uint32_t professionId);
int hiredNpcTransportDayReduction(const EventRuntimeState &eventRuntimeState, bool stable);
int hiredNpcCrossMapDayReduction(const EventRuntimeState &eventRuntimeState);
int hiredNpcWalkingTravelDays(int baseDays, const EventRuntimeState &eventRuntimeState);
int hiredNpcRestFoodReduction(const EventRuntimeState &eventRuntimeState);
int hiredNpcCampingFoodCost(int baseCost, const EventRuntimeState &eventRuntimeState);
// The followers' bonus to a skill: every follower's added up, or the strongest only; a ruleset may change a
// profession's amount (SkillRules::followerSkillBonus).
int hiredNpcSkillBonus(
    std::span<const HiredNpcFollower> followers,
    const std::string &skillName,
    bool strongestOnly = false,
    const SkillRules *pRules = nullptr);
int hiredNpcPrimaryStatBonus(std::span<const HiredNpcFollower> followers, const std::string &statName);
int hiredNpcResistanceBonus(std::span<const HiredNpcFollower> followers, const std::string &resistanceName);
FoundGold resolveFoundGold(uint32_t goldAmount, const EventRuntimeState *pEventRuntimeState);
std::string foundGoldStatusText(const FoundGold &foundGold);
bool hiredNpcCanRepairItemKind(std::span<const HiredNpcFollower> followers, const std::string &equipStat);
}

#pragma once

#include "game/rules/ActorRulesetFacts.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/MergedBaseTables.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct BountyHuntEntry
{
    uint32_t month = 0;
    int16_t monsterId = 0;
    bool done = false;
    bool claimed = false;
    // The affix of the boss the rules spawned (MAW), which the bounty texts name; 0 for a plain target.
    uint8_t bossAffix = 0;
    // Posted by another map's office and not placed yet: the target appears when the party next enters the map
    // (spawnPendingBountyHunt).
    bool pending = false;
};

// The map a bounty office posts its hunt on when that is not the office's own (an MM9 Jarl's region): its name, which
// keys the hunt as a town's own does (MMerge.BountyHunt.<name>), and its file.
struct BountyHuntRemoteMap
{
    std::string mapName;
    std::string mapFileName;
};

struct BountyHuntClaimResult
{
    bool claimed = false;
    uint32_t goldReward = 0;
    int32_t reputationDelta = 0;
    uint32_t bountyTotalDelta = 0;
};

struct BountyHuntInteractionResult
{
    bool succeeded = false;
    std::vector<std::string> messages;
};

class IGameplayWorldRuntime;
class NpcDialogTable;
class Party;

uint32_t bountyHuntRewardForMonster(const MonsterTable::MonsterStatsEntry &stats);
bool bountyHuntMonsterAllowed(
    const MonsterTable::MonsterStatsEntry &stats,
    const MergedBolsterMonsterTable *pBolsterMonsterTable,
    uint32_t maximumLevel);
std::vector<int16_t> collectBountyHuntMonsterIds(
    const MonsterTable &monsterTable,
    const MergedBolsterMonsterTable *pBolsterMonsterTable,
    uint32_t maximumLevel);
std::optional<int16_t> chooseBountyHuntMonsterId(
    const MonsterTable &monsterTable,
    const MergedBolsterMonsterTable *pBolsterMonsterTable,
    uint32_t maximumLevel,
    uint32_t seed);
bool bountyHuntEntryExpired(const BountyHuntEntry &entry, uint32_t currentMonth);
bool markBountyHuntMonsterKilled(BountyHuntEntry &entry, int16_t monsterId, uint32_t currentMonth);
BountyHuntClaimResult claimBountyHuntReward(
    BountyHuntEntry &entry,
    const MonsterTable &monsterTable,
    uint32_t currentMonth,
    bool awardGold);
bool markRuntimeBountyHuntMonsterKilled(IGameplayWorldRuntime &worldRuntime, int16_t monsterId);
// The rules may require more of the kill than the monster's id (MAW: the boss) and that a party member struck the
// killing blow (MAW: any other death of the target drops the bounty).
bool markRuntimeBountyHuntMonsterKilled(
    IGameplayWorldRuntime &worldRuntime,
    int16_t monsterId,
    const MonsterTable *pMonsterTable,
    const ActorRulesetFacts &facts = {},
    bool killedByParty = true);
// The office of the current map, or with pRemoteMap of that map: a new hunt there is posted with its target chosen
// and placed when the party next enters it.
BountyHuntInteractionResult performBountyHuntInteraction(
    IGameplayWorldRuntime &worldRuntime,
    Party *pParty,
    bool awardGold,
    const NpcDialogTable *pNpcDialogTable = nullptr,
    const BountyHuntRemoteMap *pRemoteMap = nullptr);
// On entering a map: places the target of this month's hunt another office posted on it (BountyHuntEntry::pending).
void spawnPendingBountyHunt(IGameplayWorldRuntime &worldRuntime, Party *pParty);
std::string bountyHuntTargetText(
    const MonsterTable::MonsterStatsEntry &stats,
    const NpcDialogTable *pNpcDialogTable = nullptr);
std::string bountyHuntRewardText(
    const MonsterTable::MonsterStatsEntry &stats,
    const NpcDialogTable *pNpcDialogTable = nullptr);
std::string bountyHuntClaimedText(const NpcDialogTable *pNpcDialogTable = nullptr);
void applyBountyHuntClaimResult(
    IGameplayWorldRuntime &worldRuntime,
    Party *pParty,
    const BountyHuntClaimResult &result);
}

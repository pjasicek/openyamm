#include "game/rules/MonsterRules.h"
#include "engine/Localization.h"

#include "game/tables/MapStats.h"

#include <algorithm>

namespace OpenYAMM::Game
{
GameplayMonsterBolsterResult MonsterRules::resolveMonster(
    const GameplayBolsterRuntimeContext &context,
    const MonsterTable::MonsterStatsEntry &stats,
    const MonsterEntry *pMonsterEntry) const
{
    return resolveGameplayMonsterBolster(context, stats, pMonsterEntry);
}

bool MonsterRules::placeMapMonsters(const GameplayBolsterRuntimeContext &, std::vector<MapMonsterPlacement> &) const
{
    return false;
}

void MonsterRules::adjustMapEncounters(MapStatsEntry &) const
{
}

void MonsterRules::enterMap(MapStatsEntry &, const MonsterTable &) const
{
}

char MonsterRules::spawnTier(const MapStatsEntry &, char tier, uint32_t) const
{
    return tier;
}

std::optional<std::string> MonsterRules::rulesTopic(const std::string &, Party &) const
{
    return std::nullopt;
}

void MonsterRules::updateMonsters(IGameplayWorldRuntime &, float) const
{
}

std::string MonsterRules::teleportBlockedText(bool) const
{
    return Engine::tr("Can't teleport now");
}

bool MonsterRules::teleportBlockedNearEnemies() const
{
    return false;
}

int MonsterRules::saveFoodCost(const std::string &, bool, bool) const
{
    return 0;
}

LootWithoutCorpse MonsterRules::lootWithoutCorpse(const CorpseLootContext &) const
{
    return {};
}

bool MonsterRules::keepsDeathDrop(const ItemDefinition &, std::mt19937 &) const
{
    return true;
}

CorpseLoot MonsterRules::corpseLoot(const CorpseLootContext &context) const
{
    // Standard has no extra drops.
    if (context.part == CorpseLootPart::Extras)
    {
        return CorpseLoot{};
    }

    return CorpseLoot{gameplayBolsterLootPrototype(
        context.pStats->loot, context.pStats->hitPoints, context.bolsterRewardMultiplier)};
}

std::optional<RulesetMapProgress> MonsterRules::mapProgress(const IGameplayWorldRuntime &) const
{
    return std::nullopt;
}

bool MonsterRules::countsForMapCompletion(const MapStatsEntry &, const MonsterTable::MonsterStatsEntry &) const
{
    return true;
}

double MonsterRules::packDensityFactor(const MapStatsEntry &) const
{
    return 1;
}

bool MonsterRules::keepsUsedBarrelsThroughRefill() const
{
    return false;
}

void MonsterRules::leaveMap(IGameplayWorldRuntime &) const
{
}

void MonsterRules::decorationRaisedStats(const std::string &, uint8_t, uint8_t) const
{
}

void MonsterRules::decorationsRenumbered(const std::string &, std::span<const int16_t>) const
{
}

uint32_t MonsterRules::bountyReward(const MonsterTable::MonsterStatsEntry &stats) const
{
    return uint32_t(std::max(0, stats.level) * 100);
}

std::optional<std::string> MonsterRules::bountyRefusal(const IGameplayWorldRuntime &) const
{
    return std::nullopt;
}

std::optional<std::string> MonsterRules::bountyRefusalForMap(const std::string &, const std::string &) const
{
    return std::nullopt;
}

std::optional<int16_t> MonsterRules::bountyTargetMonster(const MonsterTable &, uint32_t) const
{
    return std::nullopt;
}

std::optional<BountyTarget> MonsterRules::spawnBountyTarget(IGameplayWorldRuntime &, float, float, float, uint32_t) const
{
    return std::nullopt;
}

bool MonsterRules::bountyKillCounts(const ActorRulesetFacts &) const
{
    return true;
}

bool MonsterRules::bountyKillCountsElsewhere() const
{
    return true;
}

bool MonsterRules::bountyCancelledByOtherKill() const
{
    return false;
}

void MonsterRules::bountyClaimed() const
{
}

bool MonsterRules::hasProgressTab() const
{
    return false;
}

std::optional<RulesetProgressSummary> MonsterRules::progressSummary(const RulesetProgressQuery &) const
{
    return std::nullopt;
}

size_t MonsterRules::arenaMinimumTypes() const
{
    return 0;
}

int MonsterRules::arenaDrawLevel(
    const MonsterTable::MonsterStatsEntry &stats, const MonsterTable &, const MapStatsEntry &) const
{
    return stats.level;
}

int16_t MonsterRules::arenaWaveMonster(int, const MonsterTable &) const
{
    return 0;
}

RulesetScriptInfo MonsterRules::scriptInfo(uint32_t) const
{
    return {};
}

int MonsterRules::mapRespawnDays(const MapStatsEntry &map) const
{
    return map.respawnIntervalDays;
}

std::optional<std::string> MonsterRules::mapResetOffer(const std::string &) const
{
    return std::nullopt;
}

void MonsterRules::resetMap(const std::string &) const
{
}

bool MonsterRules::mapRefillForced(const std::string &) const
{
    return false;
}

void MonsterRules::mapLoaded(const std::string &, bool) const
{
}

std::vector<std::string> MonsterRules::actorBadges(const ActorRulesetFacts &) const
{
    return {};
}

float MonsterRules::actorDrawScale(const ActorRulesetFacts &, bool) const
{
    return 1.0f;
}

bool MonsterRules::makeBoss(ActorRulesetFacts &, uint64_t, uint8_t) const
{
    return false;
}

std::string MonsterRules::actorDisplayName(const ActorRulesetFacts &, const std::string &name) const
{
    return name;
}

std::string MonsterRules::monsterResistanceText(int resistance, const ActorRulesetFacts &) const
{
    return resistance >= 200 ? Engine::tr("Imm") : std::to_string(resistance);
}

std::optional<MonsterInspectNumbers> MonsterRules::inspectNumbers(const MonsterInspectQuery &) const
{
    return std::nullopt;
}

std::optional<std::pair<OpenBounty, std::string>> MonsterRules::bountyElsewhere(const std::vector<OpenBounty> &) const
{
    return std::nullopt;
}
}

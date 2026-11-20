#include "game/gameplay/BountyHuntRuntime.h"
#include "engine/Localization.h"

#include "game/events/EvtEnums.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/party/Party.h"
#include "game/tables/NpcDialogTable.h"

#include <algorithm>
#include <cmath>
#include <functional>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MinutesPerDay = 24 * 60;
constexpr uint32_t BountyHuntGroup = 39;
constexpr uint32_t MMergeBountyHuntTextId = 133;
constexpr uint32_t MMergeBountyRewardTextId = 134;
constexpr uint32_t MMergeBountyClaimedTextId = 135;
constexpr int MMergeBountyHuntLocalReputationLimit = -20;
constexpr int MMergeBountyHuntContinentReputationLimit = -5;
// The journal map note marking a target the rules placed (MAW's Note.Id 9999, BountyHunt.lua:226).
constexpr uint32_t BountyMapNoteId = 9999;

uint32_t monthFromGameMinutes(float currentGameMinutes)
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(currentGameMinutes)));
    const int totalDays = totalMinutes / MinutesPerDay;
    return static_cast<uint32_t>(totalDays / 28);
}

std::string bountyHuntVarPrefix(const IGameplayWorldRuntime &worldRuntime)
{
    return "MMerge.BountyHunt." + worldRuntime.mapName();
}

int32_t namedGlobalVarValue(const EventRuntimeState &state, const std::string &name)
{
    const auto iterator = state.namedGlobalVars.find(name);
    return iterator != state.namedGlobalVars.end() ? iterator->second : 0;
}

// Every field is written, a cleared one as 0, never erased: the session takes a map's global vars back by merging
// (GameSession::mergeNamedGlobalVarsFromRuntime), so an erased Pending came back on the next map load and the target
// was placed again each time the party re-entered its map that month (Guberland, 2026-11-11).
void writeRuntimeBountyHuntEntry(EventRuntimeState &state, const std::string &prefix, const BountyHuntEntry &entry)
{
    state.namedGlobalVars[prefix + ".Month"] = static_cast<int32_t>(entry.month);
    state.namedGlobalVars[prefix + ".MonsterId"] = static_cast<int32_t>(entry.monsterId);
    state.namedGlobalVars[prefix + ".Done"] = entry.done ? 1 : 0;
    state.namedGlobalVars[prefix + ".Claimed"] = entry.claimed ? 1 : 0;
    state.namedGlobalVars[prefix + ".BossAffix"] = entry.bossAffix;
    state.namedGlobalVars[prefix + ".Pending"] = entry.pending ? 1 : 0;
}

BountyHuntEntry readRuntimeBountyHuntEntry(const EventRuntimeState &state, const std::string &prefix)
{
    BountyHuntEntry entry = {};
    entry.month = static_cast<uint32_t>(std::max<int32_t>(0, namedGlobalVarValue(state, prefix + ".Month")));
    entry.monsterId = static_cast<int16_t>(namedGlobalVarValue(state, prefix + ".MonsterId"));
    entry.done = namedGlobalVarValue(state, prefix + ".Done") != 0;
    entry.claimed = namedGlobalVarValue(state, prefix + ".Claimed") != 0;
    entry.bossAffix = uint8_t(std::clamp(namedGlobalVarValue(state, prefix + ".BossAffix"), 0, 255));
    entry.pending = namedGlobalVarValue(state, prefix + ".Pending") != 0;
    return entry;
}

// The target as the bounty texts name it: a spawned boss by its affix (MAW's Entry.MonName).
MonsterTable::MonsterStatsEntry bountyNamedStats(
    const MonsterTable::MonsterStatsEntry &stats,
    uint8_t bossAffix,
    const Party *pParty)
{
    MonsterTable::MonsterStatsEntry named = stats;

    if (bossAffix != 0)
    {
        ActorRulesetFacts facts;
        facts.bossAffix = bossAffix;
        named.name = gameRulesFor(pParty).monsters.actorDisplayName(facts, stats.name);
    }

    return named;
}

std::string lowercaseMapName(const std::string &mapName)
{
    std::string lower = mapName;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) { return char(std::tolower(c)); });
    return lower;
}

uint32_t activeBountyMaximumLevel(const Party *pParty)
{
    const Character *pMember = pParty != nullptr ? pParty->member(0) : nullptr;
    return pMember != nullptr ? pMember->level + 20u : 20u;
}

void replaceFirst(std::string &text, const std::string &needle, const std::string &replacement)
{
    const size_t position = text.find(needle);

    if (position != std::string::npos)
    {
        text.replace(position, needle.size(), replacement);
    }
}

std::optional<std::string> npcText(const NpcDialogTable *pNpcDialogTable, uint32_t textId)
{
    if (pNpcDialogTable == nullptr)
    {
        return std::nullopt;
    }

    return pNpcDialogTable->getText(textId);
}

int32_t bountyHuntReputationDeltaForKilledMonster(
    const MonsterTable::MonsterStatsEntry &stats,
    int32_t storedReputation)
{
    int32_t reputationDelta = 0;

    if (storedReputation >= MMergeBountyHuntLocalReputationLimit)
    {
        reputationDelta -= static_cast<int32_t>(std::max(0, stats.level) / 20);
    }

    if (storedReputation > MMergeBountyHuntContinentReputationLimit)
    {
        reputationDelta -= 1;
    }

    return reputationDelta;
}
}

uint32_t bountyHuntRewardForMonster(const MonsterTable::MonsterStatsEntry &stats)
{
    return boundGameRules().monsters.bountyReward(stats);
}

bool bountyHuntMonsterAllowed(
    const MonsterTable::MonsterStatsEntry &stats,
    const MergedBolsterMonsterTable *pBolsterMonsterTable,
    uint32_t maximumLevel)
{
    if (stats.id <= 0 || stats.level <= 0 || static_cast<uint32_t>(stats.level) > maximumLevel)
    {
        return false;
    }

    if (stats.hasKind(MonsterKind::NoArena))
    {
        return false;
    }

    const MergedBolsterMonsterEntry *pBolsterMonster =
        pBolsterMonsterTable != nullptr ? pBolsterMonsterTable->findById(static_cast<uint32_t>(stats.id)) : nullptr;
    return pBolsterMonster == nullptr || !pBolsterMonster->noBountyHunt;
}

std::vector<int16_t> collectBountyHuntMonsterIds(
    const MonsterTable &monsterTable,
    const MergedBolsterMonsterTable *pBolsterMonsterTable,
    uint32_t maximumLevel)
{
    std::vector<int16_t> monsterIds;

    for (const auto &entry : monsterTable.statsEntries())
    {
        if (bountyHuntMonsterAllowed(entry.second, pBolsterMonsterTable, maximumLevel))
        {
            monsterIds.push_back(static_cast<int16_t>(entry.first));
        }
    }

    std::sort(monsterIds.begin(), monsterIds.end());
    return monsterIds;
}

std::optional<int16_t> chooseBountyHuntMonsterId(
    const MonsterTable &monsterTable,
    const MergedBolsterMonsterTable *pBolsterMonsterTable,
    uint32_t maximumLevel,
    uint32_t seed)
{
    const std::vector<int16_t> monsterIds =
        collectBountyHuntMonsterIds(monsterTable, pBolsterMonsterTable, maximumLevel);

    if (monsterIds.empty())
    {
        return std::nullopt;
    }

    std::mt19937 rng(seed);
    return monsterIds[std::uniform_int_distribution<size_t>(0, monsterIds.size() - 1u)(rng)];
}

bool bountyHuntEntryExpired(const BountyHuntEntry &entry, uint32_t currentMonth)
{
    return entry.monsterId == 0 || entry.month != currentMonth;
}

bool markBountyHuntMonsterKilled(BountyHuntEntry &entry, int16_t monsterId, uint32_t currentMonth)
{
    if (bountyHuntEntryExpired(entry, currentMonth) || entry.done || entry.claimed || entry.monsterId != monsterId)
    {
        return false;
    }

    entry.done = true;
    return true;
}

bool markRuntimeBountyHuntMonsterKilled(IGameplayWorldRuntime &worldRuntime, int16_t monsterId)
{
    return markRuntimeBountyHuntMonsterKilled(worldRuntime, monsterId, nullptr);
}

bool markRuntimeBountyHuntMonsterKilled(
    IGameplayWorldRuntime &worldRuntime,
    int16_t monsterId,
    const MonsterTable *pMonsterTable,
    const ActorRulesetFacts &facts,
    bool killedByParty)
{
    EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr || monsterId <= 0)
    {
        return false;
    }

    // The death of this map's spawned target, by any hand, takes its map note down; slain by anyone but a party
    // member, it calls the bounty off where the rules say so (BountyHunt.lua:241-251).
    const std::string currentPrefix = bountyHuntVarPrefix(worldRuntime);
    const BountyHuntEntry current = readRuntimeBountyHuntEntry(*pEventRuntimeState, currentPrefix);

    if (current.monsterId == monsterId && current.bossAffix != 0 && current.bossAffix == facts.bossAffix)
    {
        if (Party *pParty = worldRuntime.party())
        {
            pParty->removeJournalMapNote(lowercaseMapName(pEventRuntimeState->mapFileName), BountyMapNoteId);
        }

        if (!killedByParty && gameRulesFor(worldRuntime.party()).monsters.bountyCancelledByOtherKill())
        {
            // No hunt (all fields 0, as writeRuntimeBountyHuntEntry clears them).
            writeRuntimeBountyHuntEntry(*pEventRuntimeState, currentPrefix, BountyHuntEntry{});
            return false;
        }
    }

    if (!gameRulesFor(worldRuntime.party()).monsters.bountyKillCounts(facts))
    {
        return false;
    }

    const uint32_t currentMonth = monthFromGameMinutes(worldRuntime.gameMinutes());
    const bool countsElsewhere = gameRulesFor(worldRuntime.party()).monsters.bountyKillCountsElsewhere();
    bool markedAnyEntry = false;
    bool markedCurrentMapEntry = false;

    std::vector<std::string> prefixes;
    prefixes.reserve(pEventRuntimeState->namedGlobalVars.size());

    for (const auto &entry : pEventRuntimeState->namedGlobalVars)
    {
        constexpr const char *pMonsterIdSuffix = ".MonsterId";
        const std::string &name = entry.first;

        if (name.size() <= std::char_traits<char>::length(pMonsterIdSuffix)
            || name.compare(
                name.size() - std::char_traits<char>::length(pMonsterIdSuffix),
                std::char_traits<char>::length(pMonsterIdSuffix),
                pMonsterIdSuffix) != 0
            || name.rfind("MMerge.BountyHunt.", 0) != 0)
        {
            continue;
        }

        std::string prefix = name.substr(0, name.size() - std::char_traits<char>::length(pMonsterIdSuffix));

        if (countsElsewhere || prefix == currentPrefix)
        {
            prefixes.push_back(std::move(prefix));
        }
    }

    for (const std::string &prefix : prefixes)
    {
        BountyHuntEntry entry = readRuntimeBountyHuntEntry(*pEventRuntimeState, prefix);

        if (markBountyHuntMonsterKilled(entry, monsterId, currentMonth))
        {
            writeRuntimeBountyHuntEntry(*pEventRuntimeState, prefix, entry);
            markedAnyEntry = true;
            markedCurrentMapEntry = markedCurrentMapEntry || prefix == currentPrefix;
        }
    }

    if (!markedAnyEntry)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats =
        pMonsterTable != nullptr ? pMonsterTable->findStatsById(monsterId) : nullptr;

    if (markedCurrentMapEntry && pStats != nullptr)
    {
        addStoredCurrentLocationReputation(
            worldRuntime,
            bountyHuntReputationDeltaForKilledMonster(*pStats, worldRuntime.currentLocationReputation()));
    }

    return true;
}

BountyHuntClaimResult claimBountyHuntReward(
    BountyHuntEntry &entry,
    const MonsterTable &monsterTable,
    uint32_t currentMonth,
    bool awardGold)
{
    BountyHuntClaimResult result = {};

    if (bountyHuntEntryExpired(entry, currentMonth) || !entry.done || entry.claimed)
    {
        return result;
    }

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(entry.monsterId);

    if (pStats == nullptr)
    {
        return result;
    }

    result.claimed = true;
    result.goldReward = bountyHuntRewardForMonster(*pStats);
    result.bountyTotalDelta = result.goldReward;
    result.reputationDelta = -static_cast<int32_t>(
        std::ceil(static_cast<double>(result.bountyTotalDelta) / 2000.0));

    if (!awardGold)
    {
        result.goldReward = 0;
    }

    entry.claimed = true;
    return result;
}

namespace
{
uint32_t bountyHuntSeed(const std::string &prefix, uint32_t month)
{
    return static_cast<uint32_t>(std::hash<std::string>{}(prefix)) ^ static_cast<uint32_t>(month * 1103515245u);
}

// Places the hunt's target on the current map (the rules' boss, else the monster itself) and its journal note.
void placeBountyHuntTarget(IGameplayWorldRuntime &worldRuntime, Party *pParty, BountyHuntEntry &entry, uint32_t seed)
{
    const GameplayWorldPoint spawnPoint = worldRuntime.chooseBountyHuntSpawnPoint(seed);
    const std::optional<BountyTarget> target = gameRulesFor(pParty).monsters.spawnBountyTarget(
        worldRuntime, spawnPoint.x, spawnPoint.y, spawnPoint.z, seed);

    if (!target)
    {
        worldRuntime.summonHostileMonsterById(
            entry.monsterId, 1, spawnPoint.x, spawnPoint.y, spawnPoint.z, BountyHuntGroup);
        return;
    }

    entry.monsterId = target->monsterId;
    entry.bossAffix = target->bossAffix;
    const EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

    if (!target->mapNote.empty() && pParty != nullptr && pEventRuntimeState != nullptr)
    {
        JournalMapNote note;
        note.id = BountyMapNoteId;
        note.x = int32_t(std::lround(spawnPoint.x));
        note.y = int32_t(std::lround(spawnPoint.y));
        note.mapFileName = lowercaseMapName(pEventRuntimeState->mapFileName);
        note.text = target->mapNote;
        pParty->setJournalMapNote(note);
    }
}
}

void spawnPendingBountyHunt(IGameplayWorldRuntime &worldRuntime, Party *pParty)
{
    EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    const std::string prefix = bountyHuntVarPrefix(worldRuntime);
    BountyHuntEntry entry = readRuntimeBountyHuntEntry(*pEventRuntimeState, prefix);

    if (!entry.pending)
    {
        return;
    }

    // A hunt whose month passed before the party came stays unplaced; its office posts a new one.
    entry.pending = false;
    const uint32_t currentMonth = monthFromGameMinutes(worldRuntime.gameMinutes());

    if (entry.month == currentMonth && !entry.done)
    {
        placeBountyHuntTarget(worldRuntime, pParty, entry, bountyHuntSeed(prefix, entry.month));
    }

    writeRuntimeBountyHuntEntry(*pEventRuntimeState, prefix, entry);
}

BountyHuntInteractionResult performBountyHuntInteraction(
    IGameplayWorldRuntime &worldRuntime,
    Party *pParty,
    bool awardGold,
    const NpcDialogTable *pNpcDialogTable,
    const BountyHuntRemoteMap *pRemoteMap)
{
    BountyHuntInteractionResult result = {};
    const MonsterTable *pMonsterTable = worldRuntime.monsterTable();

    if (pMonsterTable == nullptr)
    {
        result.messages.push_back(Engine::tr("The bounty office is unavailable right now."));
        return result;
    }

    EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        result.messages.push_back(Engine::tr("The bounty office is unavailable right now."));
        return result;
    }

    const uint32_t currentMonth = monthFromGameMinutes(worldRuntime.gameMinutes());
    const std::string prefix =
        pRemoteMap != nullptr ? "MMerge.BountyHunt." + pRemoteMap->mapName : bountyHuntVarPrefix(worldRuntime);
    BountyHuntEntry entry = readRuntimeBountyHuntEntry(*pEventRuntimeState, prefix);

    if (entry.monsterId <= 0 || bountyHuntEntryExpired(entry, currentMonth))
    {
        const MonsterRules &rules = gameRulesFor(pParty).monsters;

        // Another town's bounty still open this month, which the rules may name instead (MAW's Road to Insanity).
        std::vector<OpenBounty> openBounties;
        const std::string bountyPrefix = "MMerge.BountyHunt.";
        const std::string monthSuffix = ".Month";

        for (const auto &[name, value] : pEventRuntimeState->namedGlobalVars)
        {
            if (!name.starts_with(bountyPrefix) || !name.ends_with(monthSuffix) || name == prefix + monthSuffix)
            {
                continue;
            }

            const std::string otherPrefix = name.substr(0, name.size() - monthSuffix.size());
            const BountyHuntEntry other = readRuntimeBountyHuntEntry(*pEventRuntimeState, otherPrefix);

            if (other.monsterId > 0 && other.month == currentMonth && !other.done)
            {
                openBounties.push_back({otherPrefix.substr(bountyPrefix.size()), other.monsterId, other.bossAffix});
            }
        }

        std::sort(openBounties.begin(), openBounties.end(),
            [](const OpenBounty &left, const OpenBounty &right)
            {
                return left.mapFileName < right.mapFileName;
            });

        if (const std::optional<std::pair<OpenBounty, std::string>> elsewhere = rules.bountyElsewhere(openBounties))
        {
            if (const MonsterTable::MonsterStatsEntry *pOtherStats =
                    pMonsterTable->findStatsById(elsewhere->first.monsterId))
            {
                MonsterTable::MonsterStatsEntry named =
                    bountyNamedStats(*pOtherStats, elsewhere->first.bossAffix, pParty);
                named.name = Engine::tr("{monster} in {place}",
                                        {{"monster", Engine::localizeKnown(named.name)},
                                         {"place", Engine::localizeKnown(elsewhere->second)}});
                result.messages.push_back(bountyHuntTargetText(named, pNpcDialogTable));
                result.succeeded = true;
                return result;
            }
        }

        const std::optional<std::string> refusal = pRemoteMap != nullptr
            ? rules.bountyRefusalForMap(pRemoteMap->mapFileName, pRemoteMap->mapName)
            : rules.bountyRefusal(worldRuntime);

        if (refusal)
        {
            result.messages.push_back(*refusal);
            return result;
        }

        // The target: the rules' pick (MAW's arena families) or one of the map's bounty monsters, by the hunt's seed,
        // which placing it uses again, so a hunt posted for another map is placed as the same monster.
        const uint32_t seed = bountyHuntSeed(prefix, currentMonth);
        std::optional<int16_t> monsterId = rules.bountyTargetMonster(*pMonsterTable, seed);

        if (!monsterId)
        {
            monsterId = chooseBountyHuntMonsterId(
                *pMonsterTable,
                worldRuntime.mergedBolsterMonsterTable(),
                activeBountyMaximumLevel(pParty),
                seed);
        }

        if (!monsterId.has_value())
        {
            result.messages.push_back(Engine::tr("There is no bounty this month."));
            return result;
        }

        entry = {};
        entry.month = currentMonth;
        entry.monsterId = *monsterId;
        entry.pending = pRemoteMap != nullptr;

        if (!entry.pending)
        {
            placeBountyHuntTarget(worldRuntime, pParty, entry, seed);
        }

        writeRuntimeBountyHuntEntry(*pEventRuntimeState, prefix, entry);
    }

    const MonsterTable::MonsterStatsEntry *pTableStats = pMonsterTable->findStatsById(entry.monsterId);

    if (pTableStats == nullptr)
    {
        result.messages.push_back(Engine::tr("The bounty office is unavailable right now."));
        return result;
    }

    const MonsterTable::MonsterStatsEntry named = bountyNamedStats(*pTableStats, entry.bossAffix, pParty);
    const MonsterTable::MonsterStatsEntry *pStats = &named;

    if (!entry.done)
    {
        result.messages.push_back(bountyHuntTargetText(*pStats, pNpcDialogTable));
        result.succeeded = true;
        return result;
    }

    const BountyHuntClaimResult claim = claimBountyHuntReward(entry, *pMonsterTable, currentMonth, awardGold);

    if (!claim.claimed)
    {
        result.messages.push_back(bountyHuntClaimedText(pNpcDialogTable));
        writeRuntimeBountyHuntEntry(*pEventRuntimeState, prefix, entry);
        return result;
    }

    applyBountyHuntClaimResult(worldRuntime, pParty, claim);
    writeRuntimeBountyHuntEntry(*pEventRuntimeState, prefix, entry);
    result.messages.push_back(bountyHuntRewardText(*pStats, pNpcDialogTable));
    result.succeeded = true;
    return result;
}

std::string bountyHuntTargetText(
    const MonsterTable::MonsterStatsEntry &stats,
    const NpcDialogTable *pNpcDialogTable)
{
    const uint32_t reward = bountyHuntRewardForMonster(stats);
    std::optional<std::string> text = npcText(pNpcDialogTable, MMergeBountyHuntTextId);
    const std::string monsterName = Engine::localizeKnown(stats.name);

    if (text && !text->empty())
    {
        *text = Engine::localize(*text);
        replaceFirst(*text, "%s", monsterName);
        replaceFirst(*text, "%lu", std::to_string(reward));
        return *text;
    }

    return Engine::tr("This month's bounty is {monster} for {gold} gold.",
                      {{"monster", monsterName}, {"gold", int64_t(reward)}});
}

std::string bountyHuntRewardText(
    const MonsterTable::MonsterStatsEntry &stats,
    const NpcDialogTable *pNpcDialogTable)
{
    const uint32_t reward = bountyHuntRewardForMonster(stats);
    std::optional<std::string> text = npcText(pNpcDialogTable, MMergeBountyRewardTextId);
    const std::string monsterName = Engine::localizeKnown(stats.name);

    if (text && !text->empty())
    {
        *text = Engine::localize(*text);
        replaceFirst(*text, "%s", monsterName);
        replaceFirst(*text, "%lu", std::to_string(reward));
        return *text;
    }

    return Engine::tr("You eliminated {monster}. Your reward is {gold} gold.",
                      {{"monster", monsterName}, {"gold", int64_t(reward)}});
}

std::string bountyHuntClaimedText(const NpcDialogTable *pNpcDialogTable)
{
    std::optional<std::string> text = npcText(pNpcDialogTable, MMergeBountyClaimedTextId);

    if (text && !text->empty())
    {
        return Engine::localize(*text);
    }

    return Engine::tr("You have already claimed this bounty.");
}

void applyBountyHuntClaimResult(
    IGameplayWorldRuntime &worldRuntime,
    Party *pParty,
    const BountyHuntClaimResult &result)
{
    if (!result.claimed)
    {
        return;
    }

    addStoredCurrentLocationReputation(worldRuntime, result.reputationDelta);
    gameRulesFor(pParty).monsters.bountyClaimed();

    if (pParty != nullptr)
    {
        if (result.goldReward > 0)
        {
            pParty->addGold(static_cast<int>(result.goldReward), GoldReason::Event);
        }

        if (result.bountyTotalDelta > 0)
        {
            pParty->addEventVariableValue(
                static_cast<uint16_t>(EvtVariable::NumBounties),
                static_cast<int32_t>(result.bountyTotalDelta));
            pParty->addAward(44);
        }
    }
}
}

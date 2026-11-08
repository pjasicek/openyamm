#include "game/gameplay/ArenaRuntime.h"
#include "engine/Localization.h"

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/maps/MapArenaDefinition.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"

#include <algorithm>
#include <array>
#include <random>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
// Map variables survive snapshots/save files; an Arena map is refilled on each new visit.
constexpr const char *DifficultyVariable = "OpenYAMM.Arena.Difficulty";
constexpr const char *RewardVariable = "OpenYAMM.Arena.RewardGold";
constexpr const char *ClaimedVariable = "OpenYAMM.Arena.Claimed";
// The original puts every opponent in one group, so they never fight each other (MM8 0x4bc74f).
constexpr uint32_t ArenaOpponentGroup = 1;

int32_t arenaVariable(const EventRuntimeState &state, const char *name)
{
    const auto entry = state.namedMapVars.find(name);
    return entry != state.namedMapVars.end() ? entry->second : 0;
}

void returnToArenaFloor(EventRuntimeState &state, const MapArenaDefinition &arena)
{
    EventRuntimeState::PendingMapMove move = {};
    move.x = arena.partyPosition.x;
    move.y = arena.partyPosition.y;
    move.z = arena.partyPosition.z;
    move.directionDegrees = arena.partyDirectionDegrees;
    state.pendingMapMove = move;
    state.dialogueState.currentOffer.reset();

    EventRuntimeState::PendingSound sound = {};
    sound.soundId = 14060; // Heroism, also used by the original Arena.
    state.pendingSounds.push_back(sound);
}
}

const char *arenaDifficultyName(ArenaDifficulty difficulty)
{
    switch (difficulty)
    {
    // Shown through tr().
    case ArenaDifficulty::Page: return Engine::trNoop("Page").data();
    case ArenaDifficulty::Squire: return Engine::trNoop("Squire").data();
    case ArenaDifficulty::Knight: return Engine::trNoop("Knight").data();
    case ArenaDifficulty::Lord: return Engine::trNoop("Lord").data();
    }
    return "";
}

std::optional<ArenaChallenge> generateArenaChallenge(
    const MonsterTable &monsters, const MapStatsEntry &map,
    const Party &party, ArenaDifficulty difficulty, uint32_t seed)
{
    const uint32_t difficultyId = static_cast<uint32_t>(difficulty);
    if (difficultyId < 1 || difficultyId > 4 || party.members().empty() || !map.arena)
    {
        return std::nullopt;
    }
    const MapArenaDefinition &arena = *map.arena;
    const MonsterRules &monsterRules = gameRulesFor(&party).monsters;

    int maximumPartyLevel = 1;
    for (const Character &member : party.members())
    {
        maximumPartyLevel = std::max(maximumPartyLevel, int(member.level) + member.levelModifier);
    }

    const int minimumLevel = std::clamp(
        difficulty == ArenaDifficulty::Lord ? maximumPartyLevel : maximumPartyLevel / 2, 2, 100);
    const int maximumLevel = std::clamp(
        difficulty == ArenaDifficulty::Page ? maximumPartyLevel
            : difficulty == ArenaDifficulty::Squire ? maximumPartyLevel * 3 / 2 : maximumPartyLevel * 2,
        2, 100);

    std::vector<int16_t> candidates;
    // The arena's other types, by their distance from the level range (the ruleset's nearest-types fallback).
    std::vector<std::pair<int, int16_t>> outside;
    for (const auto &[id, stats] : monsters.statsEntries())
    {
        if (id >= arena.minimumMonsterId && id <= arena.maximumMonsterId && id > 0 && stats.hitPoints > 0
            && !stats.hasKind(MonsterKind::NoArena) && !stats.hasKind(MonsterKind::Peasant)
            && monsters.findById(int16_t(id)) != nullptr)
        {
            const int level = monsterRules.arenaDrawLevel(stats, monsters, map);
            if (level >= minimumLevel && level <= maximumLevel)
            {
                candidates.push_back(int16_t(id));
            }
            else
            {
                outside.emplace_back(std::max(minimumLevel - level, level - maximumLevel), int16_t(id));
            }
        }
    }
    std::sort(candidates.begin(), candidates.end());

    std::mt19937 random(seed);
    const size_t minimumTypes = monsterRules.arenaMinimumTypes();

    if (candidates.size() < minimumTypes && !outside.empty())
    {
        // Nearest first; equally near types in a random order.
        std::shuffle(outside.begin(), outside.end(), random);
        std::stable_sort(outside.begin(), outside.end(),
            [](const auto &left, const auto &right) { return left.first < right.first; });

        for (size_t index = 0; index < outside.size() && candidates.size() < minimumTypes; ++index)
        {
            candidates.push_back(outside[index].second);
        }
    }

    if (candidates.empty())
    {
        return std::nullopt;
    }
    std::uniform_int_distribution<size_t> chooseCandidate(0, candidates.size() - 1);
    std::vector<int16_t> types;
    for (size_t index = 0; index < std::min<size_t>(6, candidates.size()); ++index)
    {
        types.push_back(candidates[chooseCandidate(random)]);
    }

    constexpr std::array<int, 4> minimumCounts = {6, 6, 10, 20};
    constexpr std::array<int, 4> maximumCounts = {8, 12, 20, 20};
    constexpr std::array<int, 4> rewardPerLevel = {50, 100, 200, 500};
    const size_t ruleIndex = difficultyId - 1;
    std::uniform_int_distribution<int> chooseCount(minimumCounts[ruleIndex], maximumCounts[ruleIndex]);
    std::uniform_int_distribution<size_t> chooseType(0, types.size() - 1);
    const int count = chooseCount(random);
    ArenaChallenge challenge = {};
    challenge.goldReward = maximumPartyLevel * rewardPerLevel[ruleIndex];
    for (int index = 0; index < count; ++index)
    {
        challenge.monsterIds.push_back(types[chooseType(random)]);
    }
    return challenge;
}

bool interactWithArena(IGameplayWorldRuntime &world, uint32_t npcId)
{
    EventRuntimeState *pState = world.eventRuntimeState();
    Party *pParty = world.party();
    const MapDeltaData *pMapData = world.mapDeltaData();
    const MapStatsEntry *pArenaMap = world.arenaMap();
    const MapArenaDefinition *pArena = pArenaMap != nullptr ? &*pArenaMap->arena : nullptr;
    if (pState == nullptr)
    {
        return false;
    }
    if (pArena == nullptr || pParty == nullptr || pMapData == nullptr)
    {
        pState->messages.push_back(Engine::tr("The Arena is unavailable here."));
        return false;
    }

    const int32_t difficulty = arenaVariable(*pState, DifficultyVariable);
    if (difficulty == 0)
    {
        EventRuntimeState::DialogueOfferState offer = {};
        offer.kind = DialogueOfferKind::Arena;
        offer.npcId = npcId;
        offer.topicId = ArenaTopicId;
        pState->dialogueState.currentOffer = offer;
        pState->messages.push_back(Engine::tr("Welcome to the Arena. Choose the difficulty of your challenge."));
        return false;
    }
    if (arenaVariable(*pState, ClaimedVariable) != 0)
    {
        pState->messages.push_back(
            Engine::tr("You have already won this Arena challenge. Come back for another tournament."));
        return false;
    }

    // Include hostile offspring as well as the original opponents. Party summons do not block victory.
    for (const MapDeltaActor &actor : pMapData->actors)
    {
        if (actor.hp > 0 && actor.ally != 999u
            && (actor.attributes & uint32_t(EvtActorAttribute::Invisible)) == 0)
        {
            returnToArenaFloor(*pState, *pArena);
            return true;
        }
    }

    const int32_t reward = arenaVariable(*pState, RewardVariable);
    pState->namedMapVars[ClaimedVariable] = 1;
    pParty->addGold(reward, GoldReason::Event);
    pParty->addEventVariableValue(uint16_t(EvtVariable::ArenaWinsPage) + difficulty - 1, 1);
    pParty->addAward(45 + difficulty);
    pState->messages.push_back(Engine::tr("Congratulations! You have won {gold} gold.", {{"gold", reward}}));
    EventRuntimeState::PendingSound sound = {};
    sound.soundId = 14060;
    pState->pendingSounds.push_back(sound);
    return false;
}

bool startArenaChallenge(
    IGameplayWorldRuntime &world, ArenaDifficulty difficulty, uint32_t seed)
{
    EventRuntimeState *pState = world.eventRuntimeState();
    Party *pParty = world.party();
    MapDeltaData *pMapData = world.mapDeltaData();
    const MonsterTable *pMonsters = world.monsterTable();
    const MapStatsEntry *pArenaMap = world.arenaMap();
    if (pState == nullptr || pParty == nullptr || pMapData == nullptr || pMonsters == nullptr
        || pArenaMap == nullptr || arenaVariable(*pState, DifficultyVariable) != 0)
    {
        return false;
    }
    const MapArenaDefinition *pArena = &*pArenaMap->arena;

    const std::optional<ArenaChallenge> challenge =
        generateArenaChallenge(*pMonsters, *pArenaMap, *pParty, difficulty, seed);
    if (!challenge || challenge->monsterIds.size() > pArena->monsterPositions.size())
    {
        pState->messages.push_back(Engine::tr("The Arena cannot prepare opponents for this challenge."));
        return false;
    }

    for (size_t index = 0; index < challenge->monsterIds.size(); ++index)
    {
        const int16_t monsterId = challenge->monsterIds[index];
        const MonsterTable::MonsterStatsEntry &stats = *pMonsters->findStatsById(monsterId);
        const MonsterEntry &monster = *pMonsters->findById(monsterId);
        const ArenaPosition &position = pArena->monsterPositions[index];
        MapDeltaActor actor = {};
        actor.name = stats.name;
        actor.monsterId = monsterId;
        actor.monsterInfoId = monsterId;
        actor.attributes = uint32_t(EvtActorAttribute::Aggressor);
        actor.hostilityType = 4;
        actor.group = ArenaOpponentGroup;
        actor.hp = std::max(1, stats.hitPoints);
        actor.radius = monster.radius;
        actor.height = monster.height;
        actor.moveSpeed = uint16_t(stats.speed);
        actor.x = position.x;
        actor.y = position.y;
        actor.z = position.z;
        actor.proceduralDeathLoot = false;
        pMapData->actors.push_back(std::move(actor));
    }
    pState->namedMapVars[DifficultyVariable] = int32_t(difficulty);
    pState->namedMapVars[RewardVariable] = int32_t(challenge->goldReward);
    pState->namedMapVars[ClaimedVariable] = 0;
    world.applyEventRuntimeState(true);
    returnToArenaFloor(*pState, *pArena);
    return true;
}
}

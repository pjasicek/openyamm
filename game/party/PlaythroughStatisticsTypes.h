#pragma once

#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
// Why party gold changed, for the playthrough statistics (devdocs/PLAYTHROUGH_STATISTICS_PLAN.md). Gains and spending
// are counted per reason, so the statistics add up to the change in party gold.
enum class GoldReason : uint8_t
{
    Other,
    LootCorpse,
    LootChest,
    LootGround,
    Event,
    Sold,
    Shop,
    Training,
    Temple,
    Guild,
    Travel,
    Tavern,
    Bank,
    Defeat,
    Count,
};

// Where experience came from.
enum class ExperienceReason : uint8_t
{
    Other,
    Monster,
    Event,
    Count,
};

enum class StatKillMethod : uint8_t
{
    Melee,
    Missile,
    Spell,
    Count,
};

enum class StatDamageTakenKind : uint8_t
{
    Melee,
    Missile,
    Spell,
    Environment,
    Count,
};

enum class StatSaveKind : uint8_t
{
    Quick,
    Auto,
    Named,
};

enum class StatLoadKind : uint8_t
{
    Quick,
    Menu,
};

// A party member's statistics identity, for recordings that name one.
struct StatMemberRef
{
    uint64_t id = 0;
    std::string name;
    std::string className;
};

class PlaythroughStatistics;
}

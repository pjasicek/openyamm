#include "game/rules/ExperienceRules.h"

#include "game/gameplay/GameplayBolsterRuntime.h"
#include "game/party/Party.h"

namespace OpenYAMM::Game
{
uint64_t ExperienceRules::experienceForNextLevel(uint32_t level) const
{
    return 1000ull * level * (level + 1) / 2;
}

uint32_t ExperienceRules::grantKillExperience(Party &party, const MonsterKillReward &kill) const
{
    if (kill.byPartyAlly)
    {
        return 0;
    }

    const uint32_t experience =
        gameplayBolsterExperienceReward(kill.baseExperience, kill.baseHitPoints, kill.bolsterRewardMultiplier);

    if (experience > 0)
    {
        party.grantSharedExperience(experience);
    }

    return experience;
}

int ExperienceRules::questGoldBonus(int, uint32_t) const
{
    return 0;
}

int64_t ExperienceRules::eventExperience(Party &, int64_t value, uint32_t, size_t) const
{
    return value;
}

uint64_t ExperienceRules::maximumExperience() const
{
    return 4000000000ull;
}

std::string ExperienceRules::rewardMapProgress(Party &, const MapKillProgress &) const
{
    return {};
}

int ExperienceRules::trainingLevelCap(int tableCap) const
{
    return tableCap;
}

float ExperienceRules::trainingDurationMinutes(float standardMinutes) const
{
    return standardMinutes;
}

const ExperienceRules &standardExperienceRules()
{
    static const ExperienceRules Rules;
    return Rules;
}

bool ExperienceRules::learningGrantsExperience() const
{
    return true;
}

void ExperienceRules::prepareNewParty(Party &) const
{
}

void ExperienceRules::prepareRosterCharacter(Character &) const
{
}

std::optional<int> ExperienceRules::runDeaths() const
{
    return std::nullopt;
}

std::optional<int> ExperienceRules::deathPendingSeconds(double) const
{
    return std::nullopt;
}

std::optional<std::string> ExperienceRules::loadWarning() const
{
    return std::nullopt;
}
}

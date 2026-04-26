#include "game/party/LloydsBeaconRuntime.h"

#include "game/party/Party.h"

#include <algorithm>

namespace OpenYAMM::Game
{
size_t lloydsBeaconMaxSlotsForMastery(SkillMastery mastery)
{
    switch (mastery)
    {
    case SkillMastery::Grandmaster:
    case SkillMastery::Master:
        return 5;

    case SkillMastery::Expert:
        return 3;

    case SkillMastery::Normal:
    case SkillMastery::None:
    default:
        return 1;
    }
}

size_t lloydsBeaconMaxSlotsForCharacter(const Character *pCharacter)
{
    if (pCharacter == nullptr)
    {
        return 1;
    }

    const CharacterSkill *pWaterSkill = pCharacter->findSkill("WaterMagic");
    return lloydsBeaconMaxSlotsForMastery(pWaterSkill != nullptr ? pWaterSkill->mastery : SkillMastery::None);
}

bool lloydsBeaconHasRecallableBeacon(const Character *pCharacter)
{
    if (pCharacter == nullptr)
    {
        return false;
    }

    const size_t slotCount = std::min(lloydsBeaconMaxSlotsForCharacter(pCharacter), pCharacter->lloydsBeacons.size());

    for (size_t slotIndex = 0; slotIndex < slotCount; ++slotIndex)
    {
        const std::optional<LloydBeacon> &beacon = pCharacter->lloydsBeacons[slotIndex];

        if (beacon.has_value() && beacon->remainingSeconds > 0.0f)
        {
            return true;
        }
    }

    return false;
}

float lloydsBeaconDurationSeconds(uint32_t waterSkillLevel)
{
    const uint32_t clampedSkillLevel = std::max<uint32_t>(1, waterSkillLevel);
    return static_cast<float>(clampedSkillLevel) * 7.0f * 24.0f * 60.0f * 60.0f;
}
}

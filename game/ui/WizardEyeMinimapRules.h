#pragma once

namespace OpenYAMM::Game
{
inline bool wizardEyeShowsActorMarker(bool isDead, bool hasDetectedParty, bool hostileToParty, bool corpseHasLoot)
{
    if (isDead)
    {
        return corpseHasLoot;
    }

    return hasDetectedParty || !hostileToParty;
}
}

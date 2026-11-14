#pragma once

namespace OpenYAMM::Game
{
// A corpse is marked only while it still holds loot; an empty one sinks away and leaves nothing to find. A living
// actor is marked once it is known, hostile or not, whether or not it has noticed the party. Indoors it is known when
// it has MM's Nearby attribute (MM8 0x44012b: the party's AI range reached it, it saw the party or the party hit it)
// or stands in a room the party has mapped. Outdoors every living actor is known, unlike MM, which marks only Nearby
// actors: our view reaches past the AI range, and monsters the party can see belong on the minimap.
inline bool wizardEyeShowsActorMarker(bool isDead, bool corpseIsEmpty, bool known)
{
    if (isDead)
    {
        return !corpseIsEmpty;
    }

    return known;
}
}

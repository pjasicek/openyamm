#pragma once

namespace OpenYAMM::Game
{
struct MapRuntimeRestrictions
{
    bool allowSaveGame = true;
    bool allowLloydsBeacon = true;
    bool allowRest = true;
    // False where nobody casts at all: spellbook, quick spells and read scrolls refused (MM7's Shoals, OY-350).
    // Not the same as an underwater map: MM8's Plane of Water is underwater and allows casting.
    bool allowSpellcasting = true;
    bool isArena = false;
};
}

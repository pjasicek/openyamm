#pragma once

#include <algorithm>

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
    // With allowSpellcasting false: a solo run casts here all the same (Xeen's Darzog's Tower: a lone mage would have
    // nothing to fight with). A full party keeps the ban. It lifts allowMonsterSpellcasting's ban too.
    bool allowSoloSpellcasting = false;
    // False: the map's monsters choose none of their spells and fight with their attacks (Darzog's Tower's ward). A
    // solo run with allowSoloSpellcasting fights with magic on both sides.
    bool allowMonsterSpellcasting = true;
    // In a solo run, every spell's damage on the map in percent: the solo character's (spells, scrolls, wands,
    // Armageddon's strike on its own party), the monsters' and the map's event spells alike (Darzog's Tower: 50). A
    // party run always deals its full damage.
    int soloSpellDamagePercent = 100;
    bool isArena = false;

    bool allowsSpellcasting(bool soloRun) const
    {
        return allowSpellcasting || (soloRun && allowSoloSpellcasting);
    }

    bool allowsMonsterSpellcasting(bool soloRun) const
    {
        return allowMonsterSpellcasting || (soloRun && allowSoloSpellcasting);
    }

    int spellDamagePercent(bool soloRun) const
    {
        return soloRun ? std::max(0, soloSpellDamagePercent) : 100;
    }

    // A spell's damage at the map's percent; a hit that did damage still does at least 1.
    static int scaledSpellDamage(int damage, int percent)
    {
        if (percent == 100 || damage <= 0)
        {
            return damage;
        }

        return std::max(percent > 0 ? 1 : 0, damage * percent / 100);
    }
};
}

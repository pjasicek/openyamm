#pragma once

#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
// A rectangle in the spellbook's 640 x 480 frame, from its top-left corner.
struct SpellbookSkinRect
{
    float x = 0;
    float y = 0;
    float width = 0;
    float height = 0;
};

// A spell's picture on a class's own spellbook page: the normal and the highlighted (hovered or selected) state.
struct SpellbookSkinSpell
{
    uint32_t spellId = 0;
    const char *pAsset = "";
    const char *pHighlightedAsset = "";
    SpellbookSkinRect rect;
};

// A school's page in a class's own look: the school by its first spell id (as the spellbook's school definitions),
// the page art, the tab's idle and open art, and the pictures of the spells the class knows there.
struct SpellbookSkinPage
{
    uint32_t firstSpellId = 0;
    const char *pPageAsset = "";
    const char *pTabAsset = "";
    const char *pTabSelectedAsset = "";
    std::vector<SpellbookSkinSpell> spells;
};

// A class's own look of the spellbook (MAW's Death Knight and Thief lines). Presentation only: the schools, which
// spells are known, and what a click or a cast does are the standard spellbook's; only the pictures, the tabs and
// where they sit change.
struct SpellbookSkin
{
    std::vector<SpellbookSkinPage> pages;

    const SpellbookSkinPage *page(uint32_t firstSpellId) const
    {
        for (const SpellbookSkinPage &candidate : pages)
        {
            if (candidate.firstSpellId == firstSpellId)
            {
                return &candidate;
            }
        }

        return nullptr;
    }
};
}

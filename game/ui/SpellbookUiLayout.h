#pragma once

#include "game/rules/SpellbookSkin.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"

#include <array>
#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
using SpellbookSchool = GameplayUiController::SpellbookSchool;

struct SpellbookSchoolUiDefinition
{
    SpellbookSchool school = SpellbookSchool::Fire;
    const char *pPageLayoutId = "";
    const char *pButtonLayoutId = "";
    uint32_t firstSpellId = 0;
    uint32_t spellCount = 0;
};

const std::array<SpellbookSchoolUiDefinition, 12> &spellbookSchoolUiDefinitions();

const SpellbookSchoolUiDefinition *findSpellbookSchoolUiDefinition(SpellbookSchool school);

const SpellbookSchoolUiDefinition *findSpellbookSchoolUiDefinitionForSpellId(uint32_t spellId);

const char *spellbookSchoolDisplayName(SpellbookSchool school);

std::string spellbookSpellLayoutId(SpellbookSchool school, uint32_t spellOrdinal);

// The active member's class spellbook look (SpellRules::spellbookSkin), or null for the standard book.
const SpellbookSkin *activeSpellbookSkin(const Party *pParty);
// The active member's class page of a school, or null: the school's standard page.
const SpellbookSkinPage *activeSpellbookSkinPage(const Party *pParty, SpellbookSchool school);

// A school tab of a member with a class spellbook. The tabs stack from the top at the standard tabs' spacing: the
// class's pages in their order, then any other school the member has (a racial page) in the standard order, with
// its standard art (pPage null).
struct SpellbookSkinTab
{
    SpellbookSchool school = SpellbookSchool::Fire;
    const SpellbookSkinPage *pPage = nullptr;
    SpellbookSkinRect rect;
};

std::vector<SpellbookSkinTab> spellbookSkinTabs(
    const SpellbookSkin &skin,
    const std::function<bool(SpellbookSchool)> &memberHasSchool);

// The layout element of the whole book; class spellbook rectangles are placed in it.
inline constexpr const char *SpellbookRootLayoutId = "SpellbookRoot";
// A rectangle of the 640 x 480 book on screen, given the book's resolved root element.
GameplayResolvedHudLayoutElement spellbookSkinScreenRect(
    const GameplayResolvedHudLayoutElement &root,
    const SpellbookSkinRect &rect);
}

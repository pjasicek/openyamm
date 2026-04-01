#pragma once

#include "game/ui/GameplayUiController.h"

#include <array>
#include <cstdint>
#include <string>

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

std::string spellbookSpellLayoutId(SpellbookSchool school, uint32_t spellOrdinal);
}

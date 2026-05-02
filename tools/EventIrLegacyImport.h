#pragma once

#include "tools/EventIr.h"
#include "tools/legacy_events/EvtProgram.h"
#include "tools/legacy_events/StrTable.h"

#include <functional>
#include <optional>

namespace OpenYAMM::Game
{
bool buildEventIrProgramFromLegacySource(
    EventIrProgram &program,
    const EvtProgram &evtProgram,
    const StrTable &strTable,
    const std::function<std::optional<std::string>(uint32_t)> &resolveHouseName,
    const std::function<std::optional<std::string>(uint32_t)> &resolveNpcText,
    int legacyEventVersion = 8
);
}

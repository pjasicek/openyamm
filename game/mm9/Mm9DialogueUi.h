#pragma once

#include "game/events/EventDialogContent.h"
#include "game/mm9/Mm9DialogueRuntime.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
struct Mm9DialogueUiActionResult
{
    bool handled = false;
    Mm9DialogueSelectionResult selection;
    EventDialogContent content;
};

EventDialogContent buildMm9DialogueContent(
    const Mm9DialogueRuntime &runtime,
    const std::string &responseText = {});

Mm9DialogueUiActionResult executeMm9DialogueAction(
    Mm9DialogueRuntime &runtime,
    const EventDialogAction &action,
    Mm9DialogueServiceHandler *pServiceHandler = nullptr);
}

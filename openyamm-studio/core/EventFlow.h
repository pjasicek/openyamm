#pragma once

#include "core/Audit.h"
#include "core/MapLoad.h"

#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// What a map's event handlers read and do, found by running them (PLAN.md section 6, "Flow graph"): each handler
// is run in a Lua sandbox whose `evt` functions only record their calls, once for every way its tests can come out
// (bounded), so that for every path through a handler there is the list of tests with their outcomes and the list
// of effects. Nothing of the game's state exists in the sandbox: the result says what a handler would do under
// which answers, not what the answers are.
//
// Returns a JSON array, one object per event: {event, title, paths: [{tests: [{what, taken}], effects: [text],
// error?}], truncated}. `what` and the effects are written readably ("item 2177", "map_var 5 >= 1",
// "door 12 open"). False with an error message when the sandbox itself fails.
bool exploreEventHandlers(const LoadedMap &map, std::string &json, std::string &errorMessage);

// The names of the functions the game gives event scripts as `evt.<name>`, separated by spaces (generated from the
// game's registration at build time).
extern const char *const EventFunctionNames;

// What a handler written by hand may use, read from the game's own support script by running it: the helper
// functions it defines (IsAtLeast, SetValue, SetAutonote ...), the variable selectors (Gold, HP, BaseLuck ...) and
// the enumerations (DoorAction.Open ...). Plain text. `supportSource` is the support script with the world's
// common scripts, as a map's `fullScriptSource` begins.
bool scriptReference(const std::string &supportSource, std::string &text, std::string &errorMessage);

// What is wrong with the handlers whichever way their tests come out: calls to functions the game does not have,
// variable selectors that are not numbers, and calls of something that is not a function. One line per event and
// problem, "event 20: ...". Other Lua errors are not reported: the sandbox's game functions return nothing, so a
// handler that computes with what the game would answer stops there for no fault of its own.
// `onlyEvents` empty: every event.
std::vector<std::string> eventFlowProblems(const std::string &eventFlowJson, const std::vector<int> &onlyEvents);

// Findings over all handlers of the map: map variables read but never set, and set but never read.
std::vector<AuditFinding> auditEventFlow(const std::string &eventFlowJson);
}

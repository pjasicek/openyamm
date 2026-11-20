#pragma once

#include <memory>

namespace OpenYAMM::Game
{
class GameDataRepository;
class MawRules;
struct RulesetOptions;

// The MAW rules over the loaded MAW data and the session's tables (map, spell and item), or nothing when the MAW data
// is not loaded (GameApplication::activateRuleset loads it).
std::unique_ptr<MawRules> createMawRules(const GameDataRepository &data, const RulesetOptions &options);
}

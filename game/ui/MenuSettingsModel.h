#pragma once

#include "game/app/GameSettings.h"

#include <string>
#include <string_view>

namespace OpenYAMM::Game
{
// The menu edits only its player-facing fields; debug, startup and content settings retain their owner.
std::string menuSettingValue(const GameSettings &settings, std::string_view id);
bool setMenuSettingValue(GameSettings &settings, std::string_view id, const std::string &value);
// Graphics quality presets: "low", "medium" or "high" when every detail option they own matches, else "custom".
std::string graphicsQualityPreset(const GameSettings &settings);
bool applyGraphicsQualityPreset(GameSettings &settings, std::string_view preset);
bool sameMenuBinding(const InputBinding &left, const InputBinding &right);
// Escape, F9, F10, the console key and the party's number keys 1-5; the bag keys may take the numbers, which they
// use only on the inventory pages.
bool reservedMenuBinding(const InputBinding &binding, KeyboardAction action);
} // namespace OpenYAMM::Game

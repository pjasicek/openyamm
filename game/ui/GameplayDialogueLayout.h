#pragma once

#include "game/gameplay/GameplayScreenRuntime.h"

#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct DialogueTitleTextLayout
{
    std::vector<std::string> lines;
    float lineHeight = 0.0f;
    float lineAdvance = 0.0f;
    float height = 0.0f;
};

// Rendering and pointer picking must reserve the same space for wrapped house/NPC titles.
inline DialogueTitleTextLayout resolveDialogueTitleTextLayout(
    const GameplayScreenRuntime &view,
    const GameplayScreenRuntime::HudLayoutElement &layout,
    float width,
    float scale,
    const std::string &label)
{
    DialogueTitleTextLayout result;
    const std::optional<GameplayScreenRuntime::HudFontHandle> font = view.findHudFont(layout.fontName);

    if (label.empty() || !font)
    {
        return result;
    }

    const float fontScale = scale * std::max(0.1f, layout.textScale);
    const float textWidth = std::max(0.0f, width / fontScale - std::abs(layout.textPadX) * 2.0f);
    result.lines = view.wrapHudTextToWidth(*font, view.localizeHudText(label), textWidth);

    if (result.lines.empty())
    {
        result.lines.push_back(label);
    }

    result.lineHeight = static_cast<float>(font->fontHeight) * fontScale;
    result.lineAdvance = static_cast<float>(std::max(1, font->fontHeight - 3)) * fontScale;
    result.height = result.lineHeight + static_cast<float>(result.lines.size() - 1) * result.lineAdvance;
    return result;
}
}

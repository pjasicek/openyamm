#include "game/debug/AiArena.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayUiSkin.h"

namespace OpenYAMM::Game
{
void renderAiTraceOverlay(
    const GameplayScreenRuntime &screenRuntime,
    const ActorAiTrace &trace,
    const std::function<bool(const bx::Vec3 &, float &, float &)> &project)
{
    constexpr const char *FontName = GameplayUiSkin::CombatFontName;
    constexpr float FontScale = 0.6f;
    constexpr float LiftUnits = 40.0f;
    constexpr uint32_t NewestColor = 0xff80ffffu;
    constexpr uint32_t OlderColor = 0xc0d0d0d0u;
    const float lineHeight = float(screenRuntime.hudFontHeight(FontName)) * FontScale;

    for (const ActorAiTrace::OverlayItem &item : trace.overlayItems())
    {
        float screenX = 0.0f;
        float screenY = 0.0f;

        if (!project(bx::Vec3{item.anchor.x, item.anchor.y, item.anchor.z + LiftUnits}, screenX, screenY))
        {
            continue;
        }

        // The newest line sits nearest the actor; older ones stack above it.
        for (size_t lineIndex = 0; lineIndex < item.lines.size(); ++lineIndex)
        {
            const std::string text = "#" + std::to_string(item.actorIndex) + " " + item.lines[lineIndex];
            const float width = screenRuntime.measureHudTextWidth(FontName, text) * FontScale;
            screenRuntime.renderHudTextLine(FontName, lineIndex == 0 ? NewestColor : OlderColor, text,
                screenX - width * 0.5f, screenY - lineHeight * float(lineIndex + 1), FontScale);
        }
    }
}
}

#include "game/ui/KeyboardScreenLayout.h"

#include "game/gameplay/GameplayScreenRuntime.h"

namespace OpenYAMM::Game
{
namespace
{
constexpr float KeyboardRightLabelBaselineX = 411.0f;
constexpr float KeyboardRightValueBaselineX = 543.0f;
constexpr float KeyboardRightLabelOffsetX = -75.0f;
constexpr float KeyboardRightValueOffsetX = -95.0f;
}

std::optional<KeyboardScreenLayout> resolveKeyboardScreenLayout(
    const GameplayScreenRuntime &context,
    int width,
    int height)
{
    const auto *pRootLayout = context.findHudLayoutElement("KeyboardRoot");

    if (pRootLayout == nullptr)
    {
        return std::nullopt;
    }

    const auto resolvedRoot = context.resolveHudLayoutElement(
        "KeyboardRoot",
        width,
        height,
        pRootLayout->width,
        pRootLayout->height);

    if (!resolvedRoot)
    {
        return std::nullopt;
    }

    KeyboardScreenLayout layout = {};
    layout.rootX = resolvedRoot->x;
    layout.rootY = resolvedRoot->y;
    layout.rootWidth = resolvedRoot->width;
    layout.rootHeight = resolvedRoot->height;
    layout.rootScale = resolvedRoot->scale;
    layout.leftTableX = layout.rootX + 93.0f * layout.rootScale;
    layout.rightLabelX =
        layout.rootX + (KeyboardRightLabelBaselineX + KeyboardRightLabelOffsetX) * layout.rootScale;
    layout.rightValueX =
        layout.rootX + (KeyboardRightValueBaselineX + KeyboardRightValueOffsetX) * layout.rootScale;
    layout.tableY = layout.rootY + 149.0f * layout.rootScale;
    layout.rowHeight = 24.0f * layout.rootScale;
    layout.leftLabelWidth = 117.0f * layout.rootScale;
    layout.leftValueWidth = 128.0f * layout.rootScale;
    layout.rightValueWidth = 128.0f * layout.rootScale;
    layout.textPaddingX = 8.0f * layout.rootScale;
    layout.textPaddingY = 5.0f * layout.rootScale;
    layout.footerX = layout.rootX + 86.0f * layout.rootScale;
    layout.footerY = layout.rootY + 350.0f * layout.rootScale;
    return layout;
}
}

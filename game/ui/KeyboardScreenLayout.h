#pragma once

#include "game/app/KeyboardBindings.h"

namespace OpenYAMM::Game
{
class GameplayOverlayContext;
}

#include <optional>

namespace OpenYAMM::Game
{
struct KeyboardScreenLayout
{
    float rootX = 0.0f;
    float rootY = 0.0f;
    float rootWidth = 0.0f;
    float rootHeight = 0.0f;
    float rootScale = 1.0f;
    float leftTableX = 0.0f;
    float rightLabelX = 0.0f;
    float rightValueX = 0.0f;
    float tableY = 0.0f;
    float rowHeight = 0.0f;
    float leftLabelWidth = 0.0f;
    float leftValueWidth = 0.0f;
    float rightValueWidth = 0.0f;
    float textPaddingX = 0.0f;
    float textPaddingY = 0.0f;
    float footerX = 0.0f;
    float footerY = 0.0f;

    float labelColumnX(KeyboardBindingColumn column) const
    {
        return column == KeyboardBindingColumn::Left ? leftTableX : rightLabelX;
    }

    float valueColumnX(KeyboardBindingColumn column) const
    {
        return column == KeyboardBindingColumn::Left
            ? leftTableX + leftLabelWidth
            : rightValueX;
    }

    float rowY(size_t row) const
    {
        return tableY + rowHeight * row;
    }

    float rowWidth(KeyboardBindingColumn column) const
    {
        return column == KeyboardBindingColumn::Left
            ? leftLabelWidth + leftValueWidth
            : (rightValueX + rightValueWidth - rightLabelX);
    }

    float labelWidth(KeyboardBindingColumn column) const
    {
        return column == KeyboardBindingColumn::Left
            ? leftLabelWidth
            : (rightValueX - rightLabelX);
    }
};

std::optional<KeyboardScreenLayout> resolveKeyboardScreenLayout(
    const GameplayOverlayContext &context,
    int width,
    int height);
}

#pragma once

#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <cmath>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
// The Workbench's colours, shared by its alchemy and crafting tabs.
namespace GameplayBenchColors
{
inline constexpr uint32_t WellFillColor = 0x60000000u;
inline constexpr uint32_t WellBorderColor = 0xff36464du;
inline constexpr uint32_t SelectedBorderColor = 0xff4890b8u;
inline constexpr uint32_t SelectedRowColor = 0x5050a0c8u;
inline constexpr uint32_t HoverColor = 0x18ffffffu;
inline constexpr uint32_t DimTextColor = 0xff95abb7u;
inline constexpr uint32_t HeaderTextColor = 0xff5a7d8fu;
inline constexpr uint32_t DisabledTextColor = 0xff70808au;
inline constexpr uint32_t WarningTextColor = 0xff4aa8e0u;
inline constexpr uint32_t ChipOnColor = 0xff5ea6c9u;
inline constexpr uint32_t ChipOnTextColor = 0xff0a141au;
}

// The Workbench's drawing (alchemy and crafting tabs): wells, frames, chips, buttons, text and item icons laid out by
// alchemy_bench.yml.
class GameplayBenchPainter
{
public:
    using Rect = GameplayResolvedHudLayoutElement;

    GameplayBenchPainter(GameplayScreenRuntime &context, int width, int height)
        : m_context(context)
        , m_width(width)
        , m_height(height)
        , m_pInput(context.currentGameplayInputFrame())
    {
    }

    std::optional<Rect> rect(const char *pLayoutId) const
    {
        return m_context.resolveHudLayoutElement(pLayoutId, m_width, m_height, 0, 0);
    }

    bool hovered(const Rect &area) const
    {
        return m_pInput != nullptr
            && GameplayHudCommon::isPointerInsideResolvedElement(area, m_pInput->pointerX, m_pInput->pointerY);
    }

    bool pressed(const Rect &area) const
    {
        return hovered(area) && m_pInput->leftMouseButton.held;
    }

    void fill(const Rect &area, uint32_t colorAbgr) const
    {
        const std::string name = "__alchemy_bench_" + std::to_string(colorAbgr) + "__";
        const std::optional<GameplayHudTextureHandle> texture =
            m_context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colorAbgr);

        if (texture && area.width > 0 && area.height > 0)
        {
            m_context.submitHudTexturedQuad(*texture, area.x, area.y, area.width, area.height);
        }
    }

    void frame(const Rect &area, uint32_t colorAbgr) const
    {
        const float line = std::max(1.0f, std::round(area.scale * 0.75f));
        fill({area.x, area.y, area.width, line, area.scale}, colorAbgr);
        fill({area.x, area.y + area.height - line, area.width, line, area.scale}, colorAbgr);
        fill({area.x, area.y + line, line, area.height - 2 * line, area.scale}, colorAbgr);
        fill({area.x + area.width - line, area.y + line, line, area.height - 2 * line, area.scale}, colorAbgr);
    }

    void well(const Rect &area, uint32_t borderAbgr = GameplayBenchColors::WellBorderColor) const
    {
        fill(area, GameplayBenchColors::WellFillColor);
        frame(area, borderAbgr);
    }

    // Draws text with a layout element's font, scale and alignment in any rectangle.
    void text(const char *pStyleId, const Rect &area, const std::string &value,
        std::optional<uint32_t> colorAbgr = std::nullopt) const
    {
        const UiLayoutManager::LayoutElement *pStyle = m_context.findHudLayoutElement(pStyleId);

        if (pStyle == nullptr || value.empty())
        {
            return;
        }

        UiLayoutManager::LayoutElement style = *pStyle;

        if (colorAbgr)
        {
            style.textColorAbgr = *colorAbgr;
        }

        m_context.renderLayoutLabel(style, area, value, false);
    }

    void label(const char *pLayoutId, const std::string &value, std::optional<uint32_t> colorAbgr = std::nullopt) const
    {
        if (const std::optional<Rect> area = rect(pLayoutId))
        {
            text(pLayoutId, *area, value, colorAbgr);
        }
    }

    // Wraps text to the element's width, one line per font height, starting at lineY.
    float paragraph(const char *pLayoutId, const std::string &value, uint32_t colorAbgr, float lineY) const
    {
        const UiLayoutManager::LayoutElement *pStyle = m_context.findHudLayoutElement(pLayoutId);
        const std::optional<Rect> area = rect(pLayoutId);

        if (pStyle == nullptr || !area)
        {
            return lineY;
        }

        const float fontScale = area->scale * std::max(0.1f, pStyle->textScale);
        const float lineHeight = static_cast<float>(m_context.hudFontHeight(pStyle->fontName)) * fontScale;

        for (const std::string &line : m_context.wrapHudTextToWidth(pStyle->fontName, value, area->width / fontScale))
        {
            // Lines past the element's bottom would run into the buttons below.
            if (lineY + lineHeight > area->y + area->height + 0.5f)
            {
                break;
            }

            text(pLayoutId, {area->x, lineY, area->width, lineHeight, area->scale}, line, colorAbgr);
            lineY += lineHeight;
        }

        return lineY;
    }

    void button(const char *pLayoutId, const std::string &value, bool enabled, bool selected = false) const
    {
        const UiLayoutManager::LayoutElement *pLayout = m_context.findHudLayoutElement(pLayoutId);
        const std::optional<Rect> area = rect(pLayoutId);

        if (pLayout == nullptr || !area)
        {
            return;
        }

        const bool hover = enabled && hovered(*area);
        const bool down = hover && m_pInput->leftMouseButton.held;
        const std::string &asset = !enabled && !pLayout->disabledAsset.empty() ? pLayout->disabledAsset
            : down && !pLayout->pressedAsset.empty() ? pLayout->pressedAsset
            : hover && !pLayout->hoverAsset.empty() ? pLayout->hoverAsset
            : selected && !pLayout->selectedAsset.empty() ? pLayout->selectedAsset : pLayout->primaryAsset;
        GameplayUiSkin::renderTexture(m_context, asset, *area);
        Rect labelArea = *area;
        labelArea.y += down ? area->scale : 0.0f;
        text(pLayoutId, labelArea, value,
            !enabled ? 0xff7e8b96u : hover ? 0xffd4efffu : selected ? GameplayUiSkin::Gold : pLayout->textColorAbgr);
    }

    void chip(const char *pLayoutId, const std::string &value, bool active) const
    {
        const std::optional<Rect> area = rect(pLayoutId);

        if (!area)
        {
            return;
        }

        if (active)
        {
            fill(*area, GameplayBenchColors::ChipOnColor);
        }
        else
        {
            well(*area);

            if (hovered(*area))
            {
                fill(*area, GameplayBenchColors::HoverColor);
            }
        }

        text(pLayoutId, *area, value,
            active ? GameplayBenchColors::ChipOnTextColor : GameplayBenchColors::DimTextColor);
    }

    void itemIcon(const ItemDefinition *pDefinition, const Rect &box, uint8_t alpha = 255) const
    {
        if (pDefinition == nullptr || pDefinition->iconName.empty())
        {
            return;
        }

        const std::optional<GameplayHudTextureHandle> texture =
            m_context.gameplayUiRuntime().ensureItemIconTextureLoaded(pDefinition->iconName);

        if (!texture || texture->width <= 0 || texture->height <= 0)
        {
            return;
        }

        const float fit = std::min(box.width / texture->width, box.height / texture->height);
        const float iconWidth = std::round(texture->width * fit);
        const float iconHeight = std::round(texture->height * fit);
        const float x = std::round(box.x + (box.width - iconWidth) * 0.5f);
        const float y = std::round(box.y + (box.height - iconHeight) * 0.5f);
        if (alpha == 255)
        {
            m_context.submitHudTexturedQuad(*texture, x, y, iconWidth, iconHeight);
            return;
        }

        // Faded icons are tinted at draw time rather than copied per alpha.
        GameplayHudBatchQuad quad = {};
        quad.textureHandle = texture->textureHandle;
        quad.x = x;
        quad.y = y;
        quad.width = iconWidth;
        quad.height = iconHeight;
        quad.tintAbgr = (uint32_t(alpha) << 24) | 0x00ffffffu;
        m_context.submitHudQuadBatch({quad});
    }

private:
    GameplayScreenRuntime &m_context;
    int m_width = 0;
    int m_height = 0;
    const GameplayInputFrame *m_pInput = nullptr;
};
}

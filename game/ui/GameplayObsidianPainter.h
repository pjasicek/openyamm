#pragma once

#include "engine/Utf8Text.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/Party.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/SpellbookUiLayout.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The Carved Obsidian reading colours (the approved overlay studies' palette), as ABGR.
namespace GameplayObsidianColors
{
constexpr uint32_t abgr(uint32_t rgb, uint32_t alpha = 0xff)
{
    return alpha << 24 | (rgb & 0xffu) << 16 | (rgb & 0xff00u) | (rgb >> 16 & 0xffu);
}

inline constexpr uint32_t Ivory = abgr(0xefe0bc);
inline constexpr uint32_t Label = abgr(0xe6d1a8);
inline constexpr uint32_t Body = abgr(0xc8c7a7);
inline constexpr uint32_t Muted = abgr(0x9fa594);
inline constexpr uint32_t Gold = abgr(0xe3c185);
inline constexpr uint32_t Good = abgr(0x8fe08a);
inline constexpr uint32_t Warn = abgr(0xffb347);
inline constexpr uint32_t Bad = abgr(0xff6a5a);
inline constexpr uint32_t Mana = abgr(0x8fc3ff);
inline constexpr uint32_t Brass = abgr(0x8c815f);
}

struct GameplayObsidianRect
{
    float x = 0;
    float y = 0;
    float width = 0;
    float height = 0;

    bool contains(float pointX, float pointY) const
    {
        return pointX >= x && pointX < x + width && pointY >= y && pointY < y + height;
    }
};

// Drawing for the Carved Obsidian gameplay panels laid out in a page's logical units (a resolved layout element's
// origin and scale): fills, frames, text in the menu fonts, the omenu_* art (whole or sliced), spell icons from the
// spellbook and the members' oval faces. Shared by the Journal's aura page and the Battle Orders window.
class GameplayObsidianPainter
{
public:
    using Rect = GameplayObsidianRect;

    GameplayObsidianPainter(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &page)
        : m_context(context)
        , m_page(page)
    {
    }

    float scale() const
    {
        return m_page.scale;
    }

    // A rectangle given in page units, in screen pixels.
    Rect rect(float x, float y, float width, float height) const
    {
        return {m_page.x + x * m_page.scale, m_page.y + y * m_page.scale, width * m_page.scale,
            height * m_page.scale};
    }

    // The font scale that draws the font at a height in page units: whole steps when enlarged, for crisp glyphs.
    static float fontScale(const GameplayScreenRuntime &context, const std::string &font, float logicalHeight,
        float scale)
    {
        const int height = std::max(1, context.hudFontHeight(font));
        const float wanted = logicalHeight * scale / float(height);
        return wanted >= 1.0f ? GameplayHudCommon::snappedHudFontScale(wanted) : std::max(0.5f, wanted);
    }

    void fill(const Rect &area, uint32_t colour) const
    {
        if (const std::optional<GameplayHudTextureHandle> texture = solid(colour);
            texture && area.width > 0 && area.height > 0)
        {
            m_context.submitHudTexturedQuad(*texture, area.x, area.y, area.width, area.height);
        }
    }

    void frame(const Rect &area, uint32_t colour) const
    {
        const float line = std::max(1.0f, std::round(m_page.scale * 0.6f));
        fill({area.x, area.y, area.width, line}, colour);
        fill({area.x, area.y + area.height - line, area.width, line}, colour);
        fill({area.x, area.y, line, area.height}, colour);
        fill({area.x + area.width - line, area.y, line, area.height}, colour);
    }

    // A text's width in page units.
    float width(const std::string &font, float height, const std::string &value) const
    {
        return m_context.measureHudTextWidth(font, value) * fontScale(m_context, font, height, m_page.scale)
            / m_page.scale;
    }

    // Text with its top left at page units (x, y); align 0 left, 1 centred on x, 2 ending at x. Returns its width.
    float text(const std::string &font, float height, uint32_t colour, const std::string &value, float x, float y,
        int align = 0) const
    {
        if (value.empty())
        {
            return 0;
        }

        const float textScale = fontScale(m_context, font, height, m_page.scale);
        const float measured = m_context.measureHudTextWidth(font, value) * textScale;
        float left = m_page.x + x * m_page.scale;
        left -= align == 1 ? measured / 2 : align == 2 ? measured : 0;
        m_context.renderHudTextLine(font, colour, value, std::round(left), std::round(m_page.y + y * m_page.scale),
            textScale);
        return measured / m_page.scale;
    }

    // The text cut with an ellipsis to fit the width (page units).
    std::string fitted(const std::string &font, float height, const std::string &value, float available) const
    {
        if (width(font, height, value) <= available)
        {
            return value;
        }

        std::string result = value;

        while (result.size() > 1)
        {
            // A whole character: shown names may be translated into letters of several bytes.
            Engine::Utf8::popBack(result);

            while (!result.empty() && result.back() == ' ')
            {
                result.pop_back();
            }

            if (width(font, height, result + "...") <= available)
            {
                return result + "...";
            }
        }

        return result;
    }

    std::vector<std::string> wrapped(const std::string &font, float height, const std::string &value,
        float available) const
    {
        const float textScale = fontScale(m_context, font, height, m_page.scale);
        return m_context.wrapHudTextToWidth(font, value, available * m_page.scale / textScale);
    }

    void texture(const std::string &name, const Rect &area, uint32_t tint = 0xffffffffu) const
    {
        textureRegion(name, area, 0, 0, 1, 1, tint);
    }

    // Part of a texture (u and v from 0 to 1) stretched over the rectangle.
    void textureRegion(const std::string &name, const Rect &area, float u0, float v0, float u1, float v1,
        uint32_t tint = 0xffffffffu) const
    {
        const std::optional<GameplayHudTextureHandle> handle =
            m_context.gameplayUiRuntime().ensureHudTextureLoaded(name);

        if (!handle || area.width <= 0 || area.height <= 0)
        {
            return;
        }

        GameplayHudBatchQuad quad;
        quad.textureHandle = handle->textureHandle;
        quad.x = area.x;
        quad.y = area.y;
        quad.width = area.width;
        quad.height = area.height;
        quad.u0 = u0;
        quad.v0 = v0;
        quad.u1 = u1;
        quad.v1 = v1;
        quad.tintAbgr = tint;
        m_context.submitHudQuadBatch({quad});
    }

    // A nine-slice: the texture's corners (`edge` source pixels square) drawn at their own size in screen pixels at
    // `pixelScale` (1 for an x2 texture shown at 1600 x 900), the edges stretched only along their length and the middle
    // filled. A large frame keeps its ornaments sharp at any window size.
    void sliced(const std::string &name, const Rect &area, float edge, float pixelScale) const
    {
        const std::optional<GameplayHudTextureHandle> handle =
            m_context.gameplayUiRuntime().ensureHudTextureLoaded(name);

        if (!handle || handle->width <= 0 || handle->height <= 0)
        {
            return;
        }

        const float textureWidth = float(handle->width);
        const float textureHeight = float(handle->height);
        const float corner = std::min({edge * pixelScale, area.width / 2, area.height / 2});
        const float su[4] = {0, edge / textureWidth, 1 - edge / textureWidth, 1};
        const float sv[4] = {0, edge / textureHeight, 1 - edge / textureHeight, 1};
        const float dx[4] = {area.x, area.x + corner, area.x + area.width - corner, area.x + area.width};
        const float dy[4] = {area.y, area.y + corner, area.y + area.height - corner, area.y + area.height};
        std::vector<GameplayHudBatchQuad> quads;

        for (int row = 0; row < 3; ++row)
        {
            for (int column = 0; column < 3; ++column)
            {
                GameplayHudBatchQuad quad;
                quad.textureHandle = handle->textureHandle;
                quad.x = std::round(dx[column]);
                quad.y = std::round(dy[row]);
                quad.width = std::round(dx[column + 1]) - quad.x;
                quad.height = std::round(dy[row + 1]) - quad.y;
                quad.u0 = su[column];
                quad.u1 = su[column + 1];
                quad.v0 = sv[row];
                quad.v1 = sv[row + 1];

                if (quad.width > 0 && quad.height > 0)
                {
                    quads.push_back(quad);
                }
            }
        }

        m_context.submitHudQuadBatch(quads);
    }

    // A spell's icon fitted into the box, keeping its aspect: the spellbook's own lit icon for the spell (the icons
    // are not numbered in spell order).
    void spellIcon(uint32_t spellId, const Rect &box, bool dim) const
    {
        const SpellbookSchoolUiDefinition *pSchool = findSpellbookSchoolUiDefinitionForSpellId(spellId);

        if (pSchool == nullptr)
        {
            return;
        }

        const GameplayScreenRuntime::HudLayoutElement *pLayout = m_context.findHudLayoutElement(
            spellbookSpellLayoutId(pSchool->school, spellId - pSchool->firstSpellId + 1));

        if (pLayout == nullptr || (pLayout->hoverAsset.empty() && pLayout->primaryAsset.empty()))
        {
            return;
        }

        const std::string name = !pLayout->hoverAsset.empty() ? pLayout->hoverAsset : pLayout->primaryAsset;
        const std::optional<GameplayHudTextureHandle> handle =
            m_context.gameplayUiRuntime().ensureHudTextureLoaded(name);

        if (!handle || handle->width <= 0 || handle->height <= 0)
        {
            return;
        }

        const float fit = std::min(box.width / handle->width, box.height / handle->height);
        const float iconWidth = handle->width * fit;
        const float iconHeight = handle->height * fit;
        texture(name, {box.x + (box.width - iconWidth) / 2, box.y + (box.height - iconHeight) / 2, iconWidth,
            iconHeight}, dim ? 0xff707070u : 0xffffffffu);
    }

    // A member's face in an oval with a brass rim, greyed while they are down.
    void face(const Character &member, const Rect &box, bool down) const
    {
        const std::string name = m_context.resolvePortraitTextureName(member);
        const std::optional<GameplayHudTextureHandle> handle =
            m_context.gameplayUiRuntime().ensureHudTextureLoaded(name);
        const float rim = std::max(1.0f, m_page.scale * 0.8f);
        ellipse(solid(GameplayObsidianColors::Brass), {box.x - rim, box.y - rim, box.width + 2 * rim,
            box.height + 2 * rim});

        if (handle)
        {
            // The face's middle, as the portraits frame it.
            m_context.gameplayUiRuntime().submitHudTexturedEllipse(handle->textureHandle, box.x, box.y, box.width,
                box.height, 0.12f, 0.06f, 0.88f, 0.86f);
        }

        if (down)
        {
            ellipse(solid(GameplayObsidianColors::abgr(0x05090a, 0x90)), box);
        }
    }

    // A Carved Obsidian menu button (omenu_button_small or _danger) with its Fondamento label.
    void button(const Rect &box, const std::string &label, bool danger, bool enabled, bool hovered, bool pressed,
        bool arrow = false) const
    {
        const std::string base = std::string("hud_x2/menus/omenu_button_") + (danger && enabled ? "danger_" : "small_");
        const std::string state = !enabled ? "disabled" : pressed ? "pressed" : hovered ? "hover" : "default";
        texture(base + state + ".png", box);
        const float height = box.height / m_page.scale * 0.6f;
        const float textWidth = width("Fondamento", height, label);
        const float labelWidth = textWidth + (arrow ? 8 : 0);
        const float x = (box.x - m_page.x) / m_page.scale + (box.width / m_page.scale - labelWidth) / 2;
        const float y = (box.y - m_page.y) / m_page.scale + (box.height / m_page.scale - height) / 2 - 0.5f
            + (pressed ? 0.6f : 0);
        const uint32_t colour = !enabled ? GameplayObsidianColors::abgr(0x8c8670)
            : hovered ? GameplayObsidianColors::abgr(0xffefd4) : GameplayObsidianColors::abgr(0xe8d1a4);
        text("Fondamento", height, colour, label, x, y);

        if (arrow)
        {
            const float ax = x + textWidth + 5;
            const float ay = y + height * 0.45f;
            lines({{ax - 2.2f, ay, ax, ay + 2.4f}, {ax, ay + 2.4f, ax + 2.2f, ay}}, colour, 1.1f);
        }
    }

protected:
    struct Segment
    {
        float x1;
        float y1;
        float x2;
        float y2;
    };

    std::optional<GameplayHudTextureHandle> solid(uint32_t colour) const
    {
        char name[40] = {};
        std::snprintf(name, sizeof(name), "__obsidian_solid_%08x", colour);
        return m_context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colour);
    }

    void ellipse(const std::optional<GameplayHudTextureHandle> &texture, const Rect &box) const
    {
        if (texture)
        {
            m_context.gameplayUiRuntime().submitHudTexturedEllipse(texture->textureHandle, box.x, box.y, box.width,
                box.height);
        }
    }

    // Lines between page-unit points, `lineWidth` page units thick.
    void lines(const std::vector<Segment> &segments, uint32_t colour, float lineWidth) const
    {
        const std::optional<GameplayHudTextureHandle> texture = solid(colour);

        if (!texture)
        {
            return;
        }

        std::vector<GameplayHudBatchQuad> quads;

        for (const Segment &segment : segments)
        {
            GameplayHudBatchQuad quad;
            quad.textureHandle = texture->textureHandle;
            quad.line = true;
            quad.width = std::max(1.0f, lineWidth * m_page.scale);
            quad.x = m_page.x + segment.x1 * m_page.scale;
            quad.y = m_page.y + segment.y1 * m_page.scale;
            quad.x2 = m_page.x + segment.x2 * m_page.scale;
            quad.y2 = m_page.y + segment.y2 * m_page.scale;
            quads.push_back(quad);
        }

        m_context.submitHudQuadBatch(quads);
    }

    GameplayScreenRuntime &m_context;
    GameplayResolvedHudLayoutElement m_page;
};
}

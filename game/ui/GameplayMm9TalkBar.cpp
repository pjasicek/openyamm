#include "game/ui/GameplayMm9TalkBar.h"

#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// The study's sizes are its 1600x900 pixels (common.css, a_conversation_bar.html), times `k`: the party basebar's
// height over its 195 pixels there.
constexpr float StudyBasebarHeight = 195.0f;
constexpr float FrameBorder = 34.0f;
constexpr float PaddingX = 14.0f;
constexpr float HeaderHeight = 40.0f;
constexpr float PortraitSize = 104.0f;
constexpr float RuleHeight = 12.0f;
constexpr float OneColumnWidth = 1000.0f;
constexpr float TwoColumnWidth = 1160.0f;
constexpr size_t TwoColumnsFrom = 7;
// The panel stops below this share of the screen's height; its choices scroll beyond it.
constexpr float MaxHeightShare = 0.47f;
constexpr size_t MinimumVisibleRows = 3;
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
constexpr bool TouchRows = true;
#else
constexpr bool TouchRows = false;
#endif

constexpr char NameFont[] = "Fondamento";
constexpr char SpeechFont[] = "Arrus";
constexpr char ChoiceFont[] = "Create";
constexpr char SmallFont[] = "Lucida";
constexpr char DiamondGlyph[] = "hud_x2/menus/omenu_glyph_diamond.png";
constexpr char CheckGlyph[] = "hud_x2/menus/omenu_glyph_check.png";
constexpr char UpGlyph[] = "hud_x2/menus/omenu_glyph_up.png";
constexpr char DownGlyph[] = "hud_x2/menus/omenu_glyph_down.png";

constexpr uint32_t abgr(uint32_t rgb, uint32_t alpha = 0xff)
{
    return alpha << 24 | (rgb & 0xffu) << 16 | (rgb & 0xff00u) | (rgb >> 16 & 0xffu);
}

// The approved overlay colours (obsidian_overlays_20260928 "Shared text colour rules").
constexpr uint32_t Ivory = abgr(0xe5dcc7);
constexpr uint32_t Heading = abgr(0xe4c793);
constexpr uint32_t Muted = abgr(0x9a9b88);
constexpr uint32_t Seen = abgr(0xb3ad98);
constexpr uint32_t Gold = abgr(0xffd98a);
constexpr uint32_t Hot = abgr(0xffe4ac);
constexpr uint32_t NewText = abgr(0xfff3dc);
constexpr uint32_t Brass = abgr(0xa8915c);
constexpr uint32_t RuleLine = abgr(0xa8915c, 0xa0);
constexpr uint32_t Blue = abgr(0x8ebcfa);
constexpr uint32_t KeyFill = abgr(0x121c1b);
constexpr uint32_t KeyBorder = abgr(0x5d6449);
constexpr uint32_t TagBorder = abgr(0x4b5444);
constexpr uint32_t HotFill = abgr(0x2b2a1a, 0xb0);
constexpr uint32_t HotBorder = abgr(0xd6bb80, 0x66);
constexpr uint32_t Shadow = abgr(0x000000, 0xc0);
constexpr uint32_t MedallionFill = abgr(0x1b2725);
constexpr uint32_t ScrollMark = abgr(0x9a9b88, 0xc0);

struct Box
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

struct TextBlock
{
    std::vector<std::string> lines;
    float x = 0;
    float y = 0;
    float lineHeight = 0;
};

struct Row
{
    size_t action = 0;
    Box box;
    std::vector<std::string> lines;
    std::string key;
};

struct Layout
{
    float k = 1;
    bool twoColumns = false;
    Box panel;
    Box content;
    Box portrait;
    float headerY = 0;
    float firstRuleY = 0;
    float secondRuleY = 0;
    TextBlock echo;
    TextBlock speech;
    float choiceFontHeight = 0;
    float choiceLineHeight = 0;
    std::vector<Row> rows;
    bool moreAbove = false;
    bool moreBelow = false;
};

// MM9 puts two spaces after its full stops; the bar collapses every run of spaces.
std::string collapseSpaces(const std::string &text)
{
    std::string result;
    result.reserve(text.size());

    for (char character : text)
    {
        if (character == ' ' && !result.empty() && result.back() == ' ')
        {
            continue;
        }

        result.push_back(character);
    }

    return result;
}

std::string initials(const std::string &name)
{
    std::string result;
    bool wordStart = true;

    for (char character : name)
    {
        if (character == ' ')
        {
            wordStart = true;
            continue;
        }

        if (wordStart && result.size() < 2)
        {
            result.push_back(character);
        }

        wordStart = false;
    }

    return result;
}

class Text
{
public:
    explicit Text(GameplayScreenRuntime &context)
        : m_context(context)
    {
    }

    float scale(const char *pFont, float height) const
    {
        const float wanted = height / float(std::max(1, m_context.hudFontHeight(pFont)));
        return wanted >= 1.0f ? GameplayHudCommon::snappedHudFontScale(wanted) : std::max(0.5f, wanted);
    }

    float width(const char *pFont, float height, const std::string &value) const
    {
        return m_context.measureHudTextWidth(pFont, value) * scale(pFont, height);
    }

    std::vector<std::string> wrap(const char *pFont, float height, const std::string &value, float maxWidth) const
    {
        if (value.empty())
        {
            return {};
        }

        return m_context.wrapHudTextToWidth(pFont, value, maxWidth / scale(pFont, height));
    }

    // Align 0 left, 1 centred on x, 2 ending at x; a soft shadow one pixel below for the scene behind.
    void draw(const char *pFont, float height, uint32_t colour, const std::string &value, float x, float y,
        int align = 0, bool shadow = true) const
    {
        const float fontScale = scale(pFont, height);
        const float textWidth = m_context.measureHudTextWidth(pFont, value) * fontScale;
        x -= align == 1 ? textWidth / 2 : align == 2 ? textWidth : 0;

        if (shadow)
        {
            m_context.renderHudTextLine(pFont, Shadow, value, std::round(x), std::round(y + std::max(1.0f,
                height / 14.0f)), fontScale);
        }

        m_context.renderHudTextLine(pFont, colour, value, std::round(x), std::round(y), fontScale);
    }

private:
    GameplayScreenRuntime &m_context;
};

std::optional<GameplayResolvedHudLayoutElement> basebarRect(GameplayScreenRuntime &context, int width, int height)
{
    return context.resolveHudLayoutElement("OutdoorGameplayBasebar", width, height, 0, 0);
}

std::string keyLabel(const EventDialogContent &dialog, size_t action)
{
    if (GameplayMm9TalkBar::exitAction(dialog) == action)
    {
        return "Esc";
    }

    for (size_t number = 1; number <= 10; ++number)
    {
        if (GameplayMm9TalkBar::actionForNumberKey(dialog, number) == action)
        {
            return std::to_string(number % 10);
        }
    }

    return {};
}

// The bar for the open talk, laid out bottom-up from the basebar: its height follows the text and the rows, up to
// MaxHeightShare of the screen, past which only the rows round the selection show.
std::optional<Layout> layout(GameplayScreenRuntime &context, int width, int height)
{
    const EventDialogContent &dialog = context.activeEventDialog();

    if (!dialog.isActive || dialog.presentation != EventDialogPresentation::Mm9Rude || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const std::optional<GameplayResolvedHudLayoutElement> bar = basebarRect(context, width, height);
    const float k = bar ? bar->height / StudyBasebarHeight : float(height) / 900.0f;
    const float barTop = bar ? bar->y : float(height) - StudyBasebarHeight * k;
    const Text text(context);
    const std::vector<size_t> order = GameplayMm9TalkBar::displayOrder(dialog);

    Layout result;
    result.k = k;
    result.twoColumns = order.size() >= TwoColumnsFrom;
    const float panelWidth = result.twoColumns ? std::min(TwoColumnWidth * k, float(width) - 60 * k)
                                               : std::min(OneColumnWidth * k, float(width) - 120 * k);
    const float inset = (FrameBorder + PaddingX) * k;
    const float contentWidth = panelWidth - 2 * inset;

    // Measured top-down from the content's top (0), then placed.
    float y = 0;
    result.headerY = y;
    y += HeaderHeight * k;
    result.firstRuleY = y + 6 * k;
    y += (6 + RuleHeight + 8) * k;

    if (!dialog.echo.empty())
    {
        result.echo.lines = text.wrap(SmallFont, 17 * k,
            "\xE2\x80\x9C" + collapseSpaces(dialog.echo) + "\xE2\x80\x9D", contentWidth - 4 * k);
        result.echo.lineHeight = 22 * k;
        result.echo.x = 2 * k;
        result.echo.y = y;
        y += float(result.echo.lines.size()) * result.echo.lineHeight + 6 * k;
    }

    std::string reply;

    for (const std::string &line : dialog.lines)
    {
        reply += (reply.empty() ? "" : " ") + collapseSpaces(line);
    }

    result.speech.lines = text.wrap(SpeechFont, 23 * k, reply, contentWidth - 8 * k);
    result.speech.lineHeight = 30 * k;
    result.speech.x = 4 * k;
    result.speech.y = y;
    y += float(result.speech.lines.size()) * result.speech.lineHeight;
    result.secondRuleY = y + 6 * k;
    y += (6 + RuleHeight + 8 + 2) * k;
    const float choicesTop = y;

    // The rows, all of them, before the height limit picks the ones in view.
    result.choiceFontHeight = (result.twoColumns ? 20.0f : 21.0f) * k;
    result.choiceLineHeight = result.choiceFontHeight * 1.18f;
    const float minimumRowHeight = (TouchRows ? 54.0f : 36.0f) * k;
    const float rowGap = 2 * k;
    const float columnGap = 12 * k;
    const float columnWidth = result.twoColumns ? (contentWidth - columnGap) / 2 : contentWidth;
    const float textOffset = (TouchRows ? 34.0f : 70.0f) * k;
    std::vector<Row> rows;
    std::vector<size_t> lineOfRow;
    float rowY = 0;
    size_t lineCount = 0;

    for (size_t index = 0; index < order.size();)
    {
        const size_t action = order[index];
        const bool exitRow = dialog.actions[action].choiceMark == EventDialogChoiceMark::Exit;
        const size_t perLine = result.twoColumns && !exitRow ? 2 : 1;
        float lineHeight = minimumRowHeight;
        const size_t lineStart = rows.size();

        if (exitRow && index > 0)
        {
            rowY += 4 * k;
        }

        for (size_t column = 0; column < perLine && index < order.size(); ++column)
        {
            const size_t columnAction = order[index];

            if (column > 0 && dialog.actions[columnAction].choiceMark == EventDialogChoiceMark::Exit)
            {
                break;
            }

            Row row;
            row.action = columnAction;
            row.key = TouchRows ? std::string() : keyLabel(dialog, columnAction);
            const EventDialogAction &choice = dialog.actions[columnAction];
            const float tagWidth = choice.choiceTag.empty()
                ? 0.0f : text.width(SmallFont, 13 * k, choice.choiceTag) + 26 * k;
            const float rowWidth = exitRow ? contentWidth : columnWidth;
            row.lines = text.wrap(ChoiceFont, result.choiceFontHeight, collapseSpaces(choice.label),
                rowWidth - textOffset - 12 * k - tagWidth);
            row.box = {float(column) * (columnWidth + columnGap), rowY, rowWidth, 0};
            lineHeight = std::max(lineHeight,
                float(std::max<size_t>(1, row.lines.size())) * result.choiceLineHeight + 12 * k);
            rows.push_back(std::move(row));
            ++index;
        }

        for (size_t rowIndex = lineStart; rowIndex < rows.size(); ++rowIndex)
        {
            rows[rowIndex].box.height = lineHeight;
            lineOfRow.push_back(lineCount);
        }

        rowY += lineHeight + rowGap;
        ++lineCount;
    }

    const float bottomInset = (6 + FrameBorder) * k;
    const float topInset = (2 + FrameBorder) * k;
    const float panelBottom = barTop - 8 * k;
    // The room: under the height limit and below the top HUD, the medallion included.
    const float maximumHeight = std::min(float(height) * MaxHeightShare, panelBottom - 150 * k);
    float rowsHeight = rowY > 0 ? rowY - rowGap : 0;
    size_t firstLine = 0;
    size_t visibleLines = lineCount;

    if (topInset + choicesTop + rowsHeight + bottomInset > maximumHeight && lineCount > 0)
    {
        // Whole lines of rows that fit, at least a few, kept round the selection.
        const float room = maximumHeight - topInset - choicesTop - bottomInset;
        visibleLines = 0;
        float used = 0;
        std::vector<float> lineHeights(lineCount, 0.0f);

        for (const Row &row : rows)
        {
            lineHeights[lineOfRow[&row - rows.data()]] = row.box.height;
        }

        for (size_t line = 0; line < lineCount; ++line)
        {
            const float next = used + lineHeights[line] + (line > 0 ? rowGap : 0);

            if (next > room && visibleLines >= MinimumVisibleRows)
            {
                break;
            }

            used = next;
            ++visibleLines;
        }

        visibleLines = std::min(visibleLines, lineCount);
        size_t selectedLine = 0;
        const size_t selection = context.eventDialogSelectionIndex();

        for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
        {
            if (rows[rowIndex].action == selection)
            {
                selectedLine = lineOfRow[rowIndex];
            }
        }

        firstLine = selectedLine >= visibleLines ? selectedLine - visibleLines + 1 : 0;
        result.moreAbove = firstLine > 0;
        result.moreBelow = firstLine + visibleLines < lineCount;
        const float shift = firstLine > 0 ? rows[size_t(std::find(lineOfRow.begin(), lineOfRow.end(), firstLine)
            - lineOfRow.begin())].box.y : 0.0f;
        std::vector<Row> visible;

        for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
        {
            if (lineOfRow[rowIndex] >= firstLine && lineOfRow[rowIndex] < firstLine + visibleLines)
            {
                Row row = rows[rowIndex];
                row.box.y -= shift;
                visible.push_back(std::move(row));
            }
        }

        rows = std::move(visible);
        rowsHeight = 0;

        for (const Row &row : rows)
        {
            rowsHeight = std::max(rowsHeight, row.box.y + row.box.height);
        }
    }

    const float panelHeight = topInset + choicesTop + rowsHeight + bottomInset;
    result.panel = {std::round((float(width) - panelWidth) / 2), std::round(panelBottom - panelHeight), panelWidth,
        panelHeight};
    result.content = {result.panel.x + inset, result.panel.y + topInset, contentWidth,
        panelHeight - topInset - bottomInset};
    const float originX = result.content.x;
    const float originY = result.content.y;
    result.headerY += originY;
    result.firstRuleY += originY;
    result.secondRuleY += originY;
    result.echo.x += originX;
    result.echo.y += originY;
    result.speech.x += originX;
    result.speech.y += originY;

    for (Row &row : rows)
    {
        row.box.x += originX;
        row.box.y += originY + choicesTop;
    }

    result.rows = std::move(rows);
    result.portrait = {originX - 20 * k, result.headerY - 74 * k, PortraitSize * k, PortraitSize * k};
    return result;
}

class Painter
{
public:
    explicit Painter(GameplayScreenRuntime &context)
        : m_context(context)
    {
    }

    void fill(const Box &box, uint32_t colour) const
    {
        if (const std::optional<GameplayHudTextureHandle> texture = solid(colour))
        {
            m_context.submitHudTexturedQuad(*texture, box.x, box.y, box.width, box.height);
        }
    }

    void frame(const Box &box, float line, uint32_t colour) const
    {
        fill({box.x, box.y, box.width, line}, colour);
        fill({box.x, box.y + box.height - line, box.width, line}, colour);
        fill({box.x, box.y, line, box.height}, colour);
        fill({box.x + box.width - line, box.y, line, box.height}, colour);
    }

    void disc(const Box &box, uint32_t colour) const
    {
        if (const std::optional<GameplayHudTextureHandle> texture = solid(colour))
        {
            m_context.gameplayUiRuntime().submitHudTexturedEllipse(texture->textureHandle, box.x, box.y, box.width,
                box.height);
        }
    }

    void glyph(const char *pAsset, const Box &box, uint32_t colour) const
    {
        const std::optional<GameplayHudTextureHandle> texture =
            m_context.gameplayUiRuntime().ensureHudTextureLoaded(pAsset);

        if (!texture)
        {
            return;
        }

        const bgfx::TextureHandle handle = colour == 0xffffffffu ? texture->textureHandle
            : m_context.gameplayUiRuntime().ensureHudTextureColorModulated(*texture, colour);
        m_context.gameplayUiRuntime().submitHudTexturedQuad(handle, box.x, box.y, box.width, box.height);
    }

private:
    std::optional<GameplayHudTextureHandle> solid(uint32_t colour) const
    {
        char name[40] = {};
        std::snprintf(name, sizeof(name), "__mm9_talk_%08x", colour);
        return m_context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colour);
    }

    GameplayScreenRuntime &m_context;
};

// A divider: a brass line fading at both ends, a small diamond in its middle.
void renderRule(const Painter &paint, const Layout &layout, float y)
{
    const float k = layout.k;
    const Box &content = layout.content;
    const float lineY = std::round(y + 6 * k);
    const float fade = content.width * 0.18f;
    constexpr int Steps = 6;

    for (int step = 0; step < Steps; ++step)
    {
        const uint32_t alpha = uint32_t(0xa0 * (step + 1) / (Steps + 1));
        const float segment = fade / Steps;
        paint.fill({content.x + float(step) * segment, lineY, segment, std::max(1.0f, k)}, abgr(0xa8915c, alpha));
        paint.fill({content.x + content.width - float(step + 1) * segment, lineY, segment, std::max(1.0f, k)},
            abgr(0xa8915c, alpha));
    }

    paint.fill({content.x + fade, lineY, content.width - 2 * fade, std::max(1.0f, k)}, RuleLine);
    const float size = 14 * k;
    paint.glyph(DiamondGlyph, {content.x + content.width / 2 - size / 2, lineY - size / 2 + 0.5f * k, size, size},
        abgr(0xa8915c));
}

// The speaker's medallion: MM9 has no portraits for its talking people, so their initials in a brass ring.
void renderMedallion(const Painter &paint, const Text &text, const Layout &layout, const std::string &name)
{
    const Box &box = layout.portrait;
    const float k = layout.k;
    paint.disc({box.x - 7 * k, box.y - 7 * k + 4 * k, box.width + 14 * k, box.height + 14 * k}, abgr(0x000000, 0x90));
    paint.disc({box.x - 7 * k, box.y - 7 * k, box.width + 14 * k, box.height + 14 * k}, abgr(0x2a2617));
    paint.disc({box.x - 5 * k, box.y - 5 * k, box.width + 10 * k, box.height + 10 * k}, Brass);
    paint.disc({box.x - 3 * k, box.y - 3 * k, box.width + 6 * k, box.height + 6 * k}, abgr(0x0b1212));
    paint.disc(box, MedallionFill);
    paint.disc({box.x + box.width * 0.12f, box.y + box.height * 0.08f, box.width * 0.62f, box.height * 0.62f},
        abgr(0x2d3d3a, 0x70));
    const float letters = 44 * k;
    text.draw(NameFont, letters, Heading, initials(name), box.x + box.width / 2,
        box.y + (box.height - letters) / 2 - 2 * k, 1);
}

void renderRow(const Painter &paint, const Text &text, const Layout &layout, const Row &row,
    const EventDialogAction &choice, bool hot)
{
    const float k = layout.k;
    const Box &box = row.box;
    const bool exitRow = choice.choiceMark == EventDialogChoiceMark::Exit;
    const float line = std::max(1.0f, k);

    if (hot)
    {
        paint.fill(box, HotFill);
        paint.frame(box, line, HotBorder);
        paint.fill({box.x, box.y, 3 * k, box.height}, Gold);
    }

    float x = box.x + 8 * k;
    const float middle = box.y + box.height / 2;

    if (!row.key.empty())
    {
        const Box key = {x, middle - 13 * k, std::max(28 * k, text.width(SmallFont, 13 * k, row.key) + 10 * k),
            26 * k};
        paint.fill(key, KeyFill);
        paint.frame(key, line, hot ? Brass : KeyBorder);
        text.draw(SmallFont, 13 * k, hot ? Hot : Heading, row.key, key.x + key.width / 2, key.y + 6 * k, 1, false);
        x += 38 * k;
    }
    else if (!TouchRows)
    {
        x += 38 * k;
    }

    // The mark: a gold diamond for a new quest row, a muted check for one chosen before, a door for the way out.
    const Box mark = {x, middle - 7 * k, 14 * k, 14 * k};

    switch (choice.choiceMark)
    {
        case EventDialogChoiceMark::New:
            paint.glyph(DiamondGlyph, {mark.x - 2 * k, mark.y - 2 * k, 18 * k, 18 * k}, abgr(0xffd98a));
            break;
        case EventDialogChoiceMark::Visited:
            paint.glyph(CheckGlyph, {mark.x - 1 * k, mark.y - 1 * k, 16 * k, 16 * k}, abgr(0x9a9b88, 0xc0));
            break;
        case EventDialogChoiceMark::Exit:
        {
            const float stroke = std::max(1.0f, 2 * k);
            const Box door = {mark.x + 2 * k, mark.y + 1 * k, 10 * k, 13 * k};
            paint.fill({door.x, door.y + 3 * k, stroke, door.height - 3 * k}, Muted);
            paint.fill({door.x + door.width - stroke, door.y + 3 * k, stroke, door.height - 3 * k}, Muted);
            paint.fill({door.x + 2 * k, door.y, door.width - 4 * k, stroke}, Muted);
            paint.fill({door.x + stroke, door.y + 1 * k, 2 * k, stroke}, Muted);
            paint.fill({door.x + door.width - stroke - 2 * k, door.y + 1 * k, 2 * k, stroke}, Muted);
            break;
        }
        case EventDialogChoiceMark::None:
            break;
    }

    x += 24 * k;
    const uint32_t colour = hot ? Hot
        : exitRow ? Muted
        : choice.choiceMark == EventDialogChoiceMark::Visited ? Seen
        : choice.choiceMark == EventDialogChoiceMark::New ? NewText
        : Ivory;
    const float textHeight = float(row.lines.size()) * layout.choiceLineHeight;
    float textY = middle - textHeight / 2 + (layout.choiceLineHeight - layout.choiceFontHeight) / 2;

    for (const std::string &lineText : row.lines)
    {
        text.draw(ChoiceFont, layout.choiceFontHeight, colour, lineText, x, textY);
        textY += layout.choiceLineHeight;
    }

    if (!choice.choiceTag.empty())
    {
        const float tagWidth = text.width(SmallFont, 13 * k, choice.choiceTag) + 16 * k;
        const Box tag = {box.x + box.width - 12 * k - tagWidth, middle - 11 * k, tagWidth, 22 * k};
        paint.frame(tag, line, TagBorder);
        text.draw(SmallFont, 13 * k, Blue, choice.choiceTag, tag.x + 8 * k, tag.y + 4 * k, 0, false);
    }
}
}

std::vector<size_t> GameplayMm9TalkBar::displayOrder(const EventDialogContent &dialog)
{
    std::vector<size_t> order;
    std::vector<size_t> exits;

    for (size_t index = 0; index < dialog.actions.size(); ++index)
    {
        (dialog.actions[index].choiceMark == EventDialogChoiceMark::Exit ? exits : order).push_back(index);
    }

    order.insert(order.end(), exits.begin(), exits.end());
    return order;
}

std::optional<size_t> GameplayMm9TalkBar::exitAction(const EventDialogContent &dialog)
{
    for (size_t index = 0; index < dialog.actions.size(); ++index)
    {
        if (dialog.actions[index].choiceMark == EventDialogChoiceMark::Exit)
        {
            return index;
        }
    }

    return std::nullopt;
}

std::optional<size_t> GameplayMm9TalkBar::actionForNumberKey(const EventDialogContent &dialog, size_t number)
{
    if (number < 1 || number > 10)
    {
        return std::nullopt;
    }

    const std::optional<size_t> exit = exitAction(dialog);
    size_t count = 0;

    for (size_t action : displayOrder(dialog))
    {
        if (action == exit)
        {
            continue;
        }

        if (++count == number)
        {
            return action;
        }
    }

    return std::nullopt;
}

std::optional<size_t> GameplayMm9TalkBar::actionAtPoint(GameplayScreenRuntime &context, int width, int height,
    float x, float y)
{
    const std::optional<Layout> bar = layout(context, width, height);

    if (!bar)
    {
        return std::nullopt;
    }

    for (const Row &row : bar->rows)
    {
        if (row.box.contains(x, y))
        {
            return row.action;
        }
    }

    return std::nullopt;
}

void GameplayMm9TalkBar::render(GameplayScreenRuntime &context, int width, int height, float mouseX, float mouseY)
{
    const std::optional<Layout> bar = layout(context, width, height);

    if (!bar)
    {
        return;
    }

    const EventDialogContent &dialog = context.activeEventDialog();
    const Painter paint(context);
    const Text text(context);
    const float k = bar->k;

    // A soft shade over the floor behind the bar keeps its text legible on bright scenes.
    const float shadeTop = bar->panel.y - 60 * k;
    constexpr int ShadeSteps = 8;

    for (int step = 0; step < ShadeSteps; ++step)
    {
        const float top = shadeTop + (float(height) - shadeTop) * float(step) / ShadeSteps;
        paint.fill({0, std::round(top), float(width), std::ceil((float(height) - shadeTop) / ShadeSteps)},
            abgr(0x000000, uint32_t(0x50 * (step + 1) / ShadeSteps)));
    }

    // The panel: the reading surface inside the carved frame, its corners FrameBorder study pixels.
    const GameplayResolvedHudLayoutElement panelRect = {bar->panel.x, bar->panel.y, bar->panel.width,
        bar->panel.height, FrameBorder * k / 30.933333f};
    GameplayUiSkin::renderPanel(context, panelRect, false, 1.0f, 236);

    renderMedallion(paint, text, *bar, dialog.title);

    // The header: name, place, the key hint.
    const float nameX = bar->content.x + 112 * k;
    const float nameHeight = 30 * k;
    text.draw(NameFont, nameHeight, Heading, dialog.title, nameX, bar->headerY + 6 * k);
    const std::string place = context.mapDisplayName(context.currentMapFileName());

    if (!place.empty())
    {
        text.draw(SmallFont, 14 * k, Muted, place, nameX + text.width(NameFont, nameHeight, dialog.title) + 20 * k,
            bar->headerY + 22 * k, 0, false);
    }

    if (!TouchRows && !dialog.actions.empty())
    {
        std::string hint;
        size_t numbered = 0;

        for (size_t number = 1; number <= 10 && GameplayMm9TalkBar::actionForNumberKey(dialog, number); ++number)
        {
            numbered = number;
        }

        if (numbered > 0)
        {
            hint = numbered == 1 ? "1 choose" : "1-" + std::to_string(numbered % 10) + " choose";
        }

        if (GameplayMm9TalkBar::exitAction(dialog))
        {
            hint += std::string(hint.empty() ? "" : "  \xC2\xB7  ") + "Esc leave";
        }

        text.draw(SmallFont, 13 * k, Muted, hint, bar->content.x + bar->content.width, bar->headerY + 14 * k, 2,
            false);
    }

    renderRule(paint, *bar, bar->firstRuleY);

    float y = bar->echo.y;

    for (const std::string &line : bar->echo.lines)
    {
        text.draw(SmallFont, 17 * k, abgr(0xe4c793, 0xd8), line, bar->echo.x, y);
        y += bar->echo.lineHeight;
    }

    y = bar->speech.y;

    for (const std::string &line : bar->speech.lines)
    {
        text.draw(SpeechFont, 23 * k, Ivory, line, bar->speech.x, y + 3 * k);
        y += bar->speech.lineHeight;
    }

    renderRule(paint, *bar, bar->secondRuleY);

    // The rows: the one under the pointer is hot, else the keyboard's selection.
    std::optional<size_t> hot;

    for (const Row &row : bar->rows)
    {
        if (row.box.contains(mouseX, mouseY))
        {
            hot = row.action;
        }
    }

    if (!hot && !TouchRows && context.eventDialogSelectionIndex() < dialog.actions.size())
    {
        hot = context.eventDialogSelectionIndex();
    }

    for (const Row &row : bar->rows)
    {
        renderRow(paint, text, *bar, row, dialog.actions[row.action], hot == row.action);
    }

    // More rows past the height limit: small chevrons at the list's right edge.
    if (bar->moreAbove || bar->moreBelow)
    {
        const float x = bar->content.x + bar->content.width - 6 * k;
        const float top = bar->rows.empty() ? bar->content.y : bar->rows.front().box.y;
        float bottom = top;

        for (const Row &row : bar->rows)
        {
            bottom = std::max(bottom, row.box.y + row.box.height);
        }

        const float size = 14 * k;

        if (bar->moreAbove)
        {
            paint.glyph(UpGlyph, {x - size / 2, top - size - 1 * k, size, size}, ScrollMark);
        }

        if (bar->moreBelow)
        {
            paint.glyph(DownGlyph, {x - size / 2, bottom + 1 * k, size, size}, ScrollMark);
        }
    }
}
}

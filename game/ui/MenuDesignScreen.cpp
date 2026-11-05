#include "game/ui/MenuDesignScreen.h"

#include "engine/FontAsset.h"
#include "engine/Utf8Text.h"
#include "game/audio/GameAudioSystem.h"
#include "game/audio/SoundIds.h"
#include "game/render/WaterMath.h"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
constexpr float CanvasWidth = 853.333333f;
constexpr float CanvasHeight = 480.0f;
constexpr float BrowserToLogical = 8.0f / 15.0f;
const std::string ArtRoot = "hud_x2/menus/omenu_";
} // namespace

MenuDesignScreen::MenuDesignScreen(const Engine::AssetFileSystem &assetFileSystem, bool overGameplay,
                                   GameAudioSystem *pAudio)
    : MenuScreenBase(assetFileSystem), m_overGameplay(overGameplay), m_pAudio(pAudio)
{
    setRenderViewId(MenuDesignView);
    setClearBackground(!overGameplay);
}

bool MenuDesignScreen::rendersOverGameplay() const
{
    return m_overGameplay;
}
bool MenuDesignScreen::textInputActive() const
{
    return m_textEditing && !modalOpen();
}
bool MenuDesignScreen::modalOpen() const
{
    return m_confirmation.has_value();
}
void MenuDesignScreen::setTextEditing(bool editing)
{
    m_textEditing = editing;
}

void MenuDesignScreen::loadDesign(const std::string &path)
{
    if (m_loadedDesigns.contains(path))
    {
        return;
    }
    if (!m_designLayouts.loadLayoutFile(assetFileSystem(), "ui/" + path + ".yml"))
    {
        throw std::runtime_error("Unable to load menu layout: " + path);
    }
    m_loadedDesigns.insert(path);
}

float MenuDesignScreen::designScale() const
{
    return std::min(frameWidth() / CanvasWidth, frameHeight() / CanvasHeight);
}

MenuScreenBase::Rect MenuDesignScreen::canvasRect(float x, float y, float width, float height) const
{
    const float scale = designScale();
    return {(frameWidth() - CanvasWidth * scale) / 2 + x * scale,
            (frameHeight() - CanvasHeight * scale) / 2 + y * scale, width * scale, height * scale};
}

MenuScreenBase::Rect MenuDesignScreen::designRect(const std::string &id) const
{
    const UiLayoutManager::LayoutElement *pElement = m_designLayouts.findElement(id);
    if (pElement == nullptr)
    {
        throw std::runtime_error("Missing menu element: " + id);
    }
    float x = 0, y = 0;
    const float width = pElement->width, height = pElement->height;
    while (!pElement->parentId.empty())
    {
        x += pElement->gapX;
        y += pElement->gapY;
        pElement = m_designLayouts.findElement(pElement->parentId);
        if (pElement == nullptr)
        {
            throw std::runtime_error("Missing menu parent: " + id);
        }
    }
    return canvasRect(x, y, width, height);
}

bool MenuDesignScreen::keyPressed(SDL_Scancode key) const
{
    return inputFrame().scancodePressCount(key) != 0;
}

void MenuDesignScreen::beginDesign(const std::string &screen)
{
    m_revealFocus.reset();
    if (m_designScreen != screen)
    {
        m_focus.clear();
        m_focusTargets.clear();
        m_pressed.clear();
        m_scrollDragOffset.reset();
        m_contentDrag.reset();
    }
    m_designScreen = screen;
    setDesignClip(std::nullopt);
    if (leftMouseJustPressed() || rightMouseJustPressed())
    {
        m_keyboardFocus = false;
    }
    if (!modalOpen() && keyPressed(SDL_SCANCODE_TAB) && !m_focusTargets.empty())
    {
        m_keyboardFocus = true;
        const auto position = std::find(m_focusTargets.begin(), m_focusTargets.end(), m_focus);
        int index = position == m_focusTargets.end() ? -1 : int(position - m_focusTargets.begin());
        const int step = isScancodeHeld(SDL_SCANCODE_LSHIFT) || isScancodeHeld(SDL_SCANCODE_RSHIFT) ? -1 : 1;
        index = (index + step + int(m_focusTargets.size())) % int(m_focusTargets.size());
        m_focus = m_focusTargets[index];
        const auto rect = m_focusRects.find(m_focus);
        if (rect != m_focusRects.end())
        {
            m_revealFocus = rect->second;
        }
    }
    m_focusTargets.clear();
    m_focusRects.clear();
}

bool MenuDesignScreen::focused(const std::string &id) const
{
    return m_focus == id && !modalOpen();
}

void MenuDesignScreen::revealFocus(const Rect &viewport, float &scroll) const
{
    if (!m_revealFocus || modalOpen())
    {
        return;
    }
    const Rect &rect = *m_revealFocus;
    if (rect.x < viewport.x || rect.x + rect.width > viewport.x + viewport.width)
    {
        return;
    }
    if (rect.y < viewport.y)
    {
        scroll -= (viewport.y - rect.y) / designScale();
    }
    else if (rect.y + rect.height > viewport.y + viewport.height)
    {
        scroll += (rect.y + rect.height - viewport.y - viewport.height) / designScale();
    }
}

void MenuDesignScreen::scrollViewport(const Rect &viewport, float contentHeight, float &scroll, float wheelStep,
                                      bool enabled)
{
    // A press that moves this far (logical units) along the content becomes a drag.
    constexpr float ContentDragThreshold = 6;
    const float unit = designScale();
    const float maxScroll = std::max(0.0f, contentHeight - viewport.height / unit);
    // A confirmation's own scroll box (its notes) takes input while the confirmation draws; a viewport behind it
    // leaves the drag alone, which belongs to the box.
    const bool interactive = enabled && (!modalOpen() || m_drawingConfirmation);
    revealFocus(viewport, scroll);
    if (interactive && pointerInside(viewport))
    {
        scroll -= mouseWheelDelta() * wheelStep;
    }
    scroll = std::clamp(scroll, 0.0f, maxScroll);
    if (interactive && (!leftMouseDown() || maxScroll == 0))
    {
        m_scrollDragOffset.reset();
    }
    if (m_contentDrag && m_contentDrag->pScroll == &scroll && (!leftMouseDown() || !interactive || maxScroll == 0))
    {
        m_contentDrag.reset();
    }
    if (maxScroll == 0)
    {
        return;
    }
    const float thumbHeight =
        std::min(viewport.height, std::max(20 * unit, viewport.height * viewport.height / (contentHeight * unit)));
    const float travel = viewport.height - thumbHeight;
    const Rect track{viewport.x + viewport.width - 12 * unit, viewport.y, 12 * unit, viewport.height};
    float thumbY = viewport.y + travel * scroll / maxScroll;
    if (interactive && leftMouseJustPressed() && pointerInside(track))
    {
        if (mouseY() >= thumbY && mouseY() <= thumbY + thumbHeight)
        {
            m_scrollDragOffset = mouseY() - thumbY;
        }
        else
        {
            // Clicking the track moves one visible page toward the pointer.
            scroll = std::clamp(scroll + (mouseY() < thumbY ? -1 : 1) * viewport.height / unit, 0.0f, maxScroll);
        }
    }
    else if (interactive && leftMouseJustPressed() && pointerInside(viewport))
    {
        m_contentDrag = ContentDrag{&scroll, mouseY(), scroll, false};
    }
    if (interactive && m_scrollDragOffset && travel > 0)
    {
        scroll = std::clamp((mouseY() - viewport.y - *m_scrollDragOffset) / travel, 0.0f, 1.0f) * maxScroll;
    }
    if (m_contentDrag && m_contentDrag->pScroll == &scroll)
    {
        const float moved = mouseY() - m_contentDrag->startY;
        if (!m_contentDrag->moving && std::abs(moved) >= ContentDragThreshold * unit)
        {
            // The press is a drag now: the control under it neither shows as pressed nor clicks on release.
            m_contentDrag->moving = true;
            m_pressed.clear();
        }
        if (m_contentDrag->moving)
        {
            scroll = std::clamp(m_contentDrag->startScroll - moved / unit, 0.0f, maxScroll);
        }
    }
    thumbY = viewport.y + travel * scroll / maxScroll;
    drawSolidRect({track.x + 4.5f * unit, viewport.y, 3 * unit, viewport.height}, 0xff29382au);
    drawSolidRect({track.x + 3 * unit, thumbY, 6 * unit, thumbHeight},
                  (interactive && m_scrollDragOffset) || pointerInside(track) ? 0xff90bedau : 0xff6a8dacu);
}

void MenuDesignScreen::cancelContentDrag()
{
    m_contentDrag.reset();
}

void MenuDesignScreen::drawDesign()
{
    if (m_overGameplay)
    {
        drawSolidRect({0, 0, float(frameWidth()), float(frameHeight())}, 0xcd0d0a03u);
    }
    else
    {
        const UiLayoutManager::LayoutElement *pBackground = m_designLayouts.findElement(m_designScreen + "Background");
        if (pBackground == nullptr)
        {
            throw std::runtime_error("Missing menu background: " + m_designScreen);
        }
        const std::optional<TextureSize> size = textureSize(pBackground->primaryAsset);
        if (!size)
        {
            throw std::runtime_error("Missing menu background texture: " + pBackground->primaryAsset);
        }
        const float scale = std::max(frameWidth() / size->width, frameHeight() / size->height);
        drawTexture(pBackground->primaryAsset,
                    {(frameWidth() - size->width * scale) / 2, (frameHeight() - size->height * scale) / 2,
                     size->width * scale, size->height * scale});
        drawSolidRect({0, 0, float(frameWidth()), float(frameHeight())}, 0x3d110d08u);
    }
    for (const std::string &id : m_designLayouts.sortedLayoutIdsForScreenCached(m_designScreen))
    {
        const UiLayoutManager::LayoutElement &element = *m_designLayouts.findElement(id);
        bool clipped = id.find("ScrollViewport") != std::string::npos || id.find("ListViewport") != std::string::npos;
        const UiLayoutManager::LayoutElement *pAncestor = &element;
        while (!pAncestor->parentId.empty())
        {
            clipped = clipped || pAncestor->parentId.find("Viewport") != std::string::npos;
            pAncestor = m_designLayouts.findElement(pAncestor->parentId);
        }
        if (!element.visible || element.interactive || clipped || id.ends_with("Background"))
        {
            continue;
        }
        const Rect rect = designRect(id);
        if (!element.primaryAsset.empty())
        {
            drawTexture(element.primaryAsset, rect);
        }
        if (id.ends_with("Rule"))
        {
            drawSolidRect(rect, 0x5577a4b5u);
        }
        if (!element.labelText.empty() && element.labelText.find('{') == std::string::npos)
        {
            label(id, element.labelText);
        }
    }
}

// The lines of one paragraph word-wrapped to width (pixels); an empty paragraph is one empty line. Any run of
// whitespace separates words.
std::vector<std::string> MenuDesignScreen::wrapParagraph(const std::string &paragraph, const std::string &font,
                                                         float scale, float width)
{
    std::istringstream input(paragraph);
    std::string word, words;
    while (input >> word)
    {
        words += (words.empty() ? "" : " ") + word;
    }
    return Engine::Utf8::wrap(words, width + 0.5f,
        [&](const std::string &line)
        {
            return measureTextWidth(font, line, scale);
        });
}

void MenuDesignScreen::textInRect(const Rect &rect, const std::string &text, const std::string &font, float logicalSize,
                                  uint32_t color, bool centered)
{
    const int faceHeight = std::max(1, fontHeight(font));
    float scale = designScale() * logicalSize / faceHeight;
    std::string encoded = text;
    if (encoded.find('\n') == std::string::npos && rect.height < logicalSize * designScale() * 1.9f)
    {
        const float width = measureTextWidth(font, encoded, scale);
        const float fit = width > 0 ? std::min(1.0f, std::max(0.85f, rect.width / width)) : 1.0f;
        if (fit < 1.0f)
        {
            // A fractional reduction can round back to the same raster size and wrongly trigger an ellipsis.
            const float fittedHeight = std::max(1.0f, std::floor(std::round(scale * faceHeight) * fit));
            scale = fittedHeight / faceHeight;
            logicalSize = fittedHeight / designScale();
        }
        if (measureTextWidth(font, encoded, scale) > rect.width + 0.5f)
        {
            while (!encoded.empty() && measureTextWidth(font, encoded + "...", scale) > rect.width + 0.5f)
            {
                Engine::Utf8::popBack(encoded);
            }
            encoded += "...";
        }
    }
    const float lineHeight = logicalSize * designScale() * 1.2f;
    std::vector<std::string> lines;
    std::istringstream paragraphs(encoded);
    std::string paragraph;
    while (std::getline(paragraphs, paragraph))
    {
        const std::vector<std::string> wrapped = wrapParagraph(paragraph, font, scale, rect.width);
        lines.insert(lines.end(), wrapped.begin(), wrapped.end());
    }
    const float glyphHeight = logicalSize * designScale();
    const float blockHeight = glyphHeight + (lines.empty() ? 0 : lines.size() - 1) * lineHeight;
    float y = rect.y + std::max(0.0f, (rect.height - blockHeight) / 2);
    for (const std::string &line : lines)
    {
        if (y + glyphHeight > rect.y + rect.height + 3 * designScale())
        {
            break;
        }
        const float x = centered ? rect.x + (rect.width - measureTextWidth(font, line, scale)) / 2 : rect.x;
        drawText(font, line, x, y, color, scale);
        y += lineHeight;
    }
}

float MenuDesignScreen::textBlockHeight(const std::string &text, const std::string &font, float logicalSize,
                                       float width)
{
    const float scale = designScale() * logicalSize / std::max(1, fontHeight(font));
    size_t lineCount = 0;
    std::istringstream paragraphs(text);
    std::string paragraph;
    while (std::getline(paragraphs, paragraph))
    {
        lineCount += wrapParagraph(paragraph, font, scale, width).size();
    }
    const float glyphHeight = logicalSize * designScale();
    return lineCount == 0 ? 0 : glyphHeight + (lineCount - 1) * glyphHeight * 1.2f;
}

void MenuDesignScreen::label(const std::string &id, const std::string &text, uint32_t color, float offsetY)
{
    const UiLayoutManager::LayoutElement *pElement = m_designLayouts.findElement(id);
    if (pElement == nullptr || pElement->fontName.empty())
    {
        return;
    }
    Rect rect = designRect(id);
    rect.y += offsetY * designScale();
    const float padding = pElement->textPadX * designScale();
    rect.x += padding;
    rect.width = std::max(1.0f, rect.width - padding * 2);
    const float size = fontHeight(pElement->fontName) * pElement->textScale;
    if (pElement->textAlignX == UiLayoutManager::TextAlignX::Right)
    {
        const float width =
            measureTextWidth(pElement->fontName, text, pElement->textScale * designScale());
        rect.x += std::max(0.0f, rect.width - width);
        rect.width = std::min(rect.width, width);
    }
    textInRect(rect, text, pElement->fontName, size, color ? color : pElement->textColorAbgr,
               pElement->textAlignX == UiLayoutManager::TextAlignX::Center);
}

void MenuDesignScreen::skin(const std::string &name, const Rect &content, bool sliced, float padding)
{
    const std::string file = name.starts_with("hud_x2/") ? name : ArtRoot + name + ".png";
    const float pad = padding * BrowserToLogical * designScale();
    const Rect rect{content.x - pad, content.y - pad, content.width + pad * 2, content.height + pad * 2};
    if (!sliced)
    {
        drawTexture(file, rect);
        return;
    }
    const std::optional<TextureSize> source = textureSize(file);
    if (!source)
    {
        return;
    }
    // hud_x2 images expose half-size logical source coordinates.
    const float physicalEdge = padding ? 18.0f : 8.0f;
    const float edge = std::min({physicalEdge / 2, source->width / 3, source->height / 3});
    const float e = std::min({physicalEdge * BrowserToLogical * designScale(), rect.width / 3, rect.height / 3});
    const float sx[] = {0, edge, source->width - edge, source->width};
    const float sy[] = {0, edge, source->height - edge, source->height};
    const float dx[] = {rect.x, rect.x + e, rect.x + rect.width - e, rect.x + rect.width};
    const float dy[] = {rect.y, rect.y + e, rect.y + rect.height - e, rect.y + rect.height};
    for (int row = 0; row < 3; ++row)
    {
        for (int col = 0; col < 3; ++col)
        {
            drawTextureRegion(file, {sx[col], sy[row], sx[col + 1] - sx[col], sy[row + 1] - sy[row]},
                              {dx[col], dy[row], dx[col + 1] - dx[col], dy[row + 1] - dy[row]});
        }
    }
}

void MenuDesignScreen::outline(const Rect &rect, uint32_t color)
{
    const float w = std::max(1.0f, designScale());
    drawSolidRect({rect.x, rect.y, rect.width, w}, color);
    drawSolidRect({rect.x, rect.y + rect.height - w, rect.width, w}, color);
    drawSolidRect({rect.x, rect.y, w, rect.height}, color);
    drawSolidRect({rect.x + rect.width - w, rect.y, w, rect.height}, color);
}

bool MenuDesignScreen::pointerInside(const Rect &rect) const
{
    return hitTest(rect) && (!m_designClip || hitTest(*m_designClip));
}

void MenuDesignScreen::setDesignClip(const std::optional<Rect> &rect)
{
    m_designClip = rect;
    setClipRect(rect);
}

MenuDesignScreen::Hotspot MenuDesignScreen::hotspot(const std::string &id, const Rect &rect, bool enabled)
{
    Hotspot result;
    const bool available = enabled && (!modalOpen() || m_drawingConfirmation);
    if (available)
    {
        m_focusTargets.push_back(id);
        if (m_designClip)
        {
            m_focusRects[id] = rect;
        }
    }
    result.hovered = available && pointerInside(rect);
    if (result.hovered && leftMouseJustPressed())
    {
        m_pressed = id;
        m_focus = id;
    }
    result.pressed = result.hovered && leftMouseDown() && m_pressed == id;
    result.activated = available && !(m_drawingConfirmation && m_confirmationNew) &&
                       ((result.hovered && leftMouseJustReleased() && m_pressed == id) ||
                        ((!m_textEditing || m_drawingConfirmation) && m_focus == id &&
                         (keyPressed(SDL_SCANCODE_RETURN) || keyPressed(SDL_SCANCODE_SPACE))));
    if (result.activated)
    {
        m_pressed.clear();
        if (m_pAudio != nullptr)
        {
            m_pAudio->playCommonSound(SoundId::ClickIn, GameAudioSystem::PlaybackGroup::Ui);
        }
    }
    if (m_keyboardFocus && m_focus == id && available)
    {
        outline(rect, 0xff8dc5e1u);
    }
    return result;
}

bool MenuDesignScreen::button(const std::string &id, const Rect &rect, const std::string &text, const std::string &name,
                              bool enabled, bool selected)
{
    const bool available = enabled && (!modalOpen() || m_drawingConfirmation);
    const Hotspot input = hotspot(id, rect, enabled);
    const bool hovered = input.hovered;
    const bool pressed = input.pressed;
    const bool activated = input.activated;
    const bool standard = name.starts_with("button");
    const std::string state = !enabled ? "disabled" : pressed ? "pressed" : hovered ? "hover" : "default";
    // Toggle artwork includes the checkbox; scale the whole plate together rather than stretching its centre.
    const bool sliced = name != "toggle_on" && name != "toggle_off";
    skin(name + (standard ? "_" + state : selected ? "_selected" : ""), rect, sliced, standard ? 6 : 0);
    if (m_keyboardFocus && m_focus == id && available)
    {
        outline(rect, 0xff8dc5e1u);
    }
    if (!text.empty())
    {
        Rect textRect = rect;
        textRect.x += 5 * designScale();
        textRect.width -= 10 * designScale();
        textInRect(textRect, text, "fondamento", name == "button_square" ? 11.7f : 13.8667f,
                   enabled ? hovered ? 0xffc0f0ffu : 0xffa4d1e8u : 0xff6b777au, true);
    }
    return activated;
}

bool MenuDesignScreen::selectBox(const std::string &id, const Rect &rect, const std::string &value, bool enabled,
                                float logicalSize)
{
    const bool available = enabled && (!modalOpen() || m_drawingConfirmation);
    const bool hovered = available && pointerInside(rect);
    const bool activated = button(id, rect, "", "button_quiet", enabled);
    const bool pressed = hovered && leftMouseDown() && m_pressed == id;
    const std::string state = !enabled ? "disabled" : pressed ? "pressed" : hovered ? "hover" : "default";
    const float scale = designScale();
    const Rect arrow{rect.x + rect.width - rect.height, rect.y, rect.height, rect.height};
    skin("button_square_" + state, arrow, true, 6);
    const uint32_t color = !enabled ? 0xff6b777au : hovered ? 0xffc0f0ffu : 0xffc6dfeau;
    textInRect({rect.x + 9 * scale, rect.y, rect.width - arrow.width - 18 * scale, rect.height},
               value, "menu_lucida", logicalSize, color);
    const float centerX = arrow.x + arrow.width / 2;
    const float centerY = arrow.y + arrow.height / 2;
    drawTextureColor(ArtRoot + "chevron_down.png",
                     {centerX - 6 * scale, centerY - 4 * scale, 12 * scale, 8 * scale}, color);
    return activated;
}

bool MenuDesignScreen::action(const std::string &id, bool enabled, const std::string &text)
{
    const UiLayoutManager::LayoutElement *pElement = m_designLayouts.findElement(id);
    if (pElement == nullptr)
    {
        throw std::runtime_error("Missing menu action: " + id);
    }
    std::string name = pElement->primaryAsset;
    const size_t start = name.find("omenu_");
    name = start == std::string::npos ? "button" : name.substr(start + 6);
    const size_t end = name.rfind("_default.png");
    if (end != std::string::npos)
    {
        name.resize(end);
    }
    const bool result = button(id, designRect(id), "", name, enabled);
    label(id, text.empty() ? pElement->labelText : text, enabled ? 0 : 0xff6b777au);
    return result;
}

void MenuDesignScreen::confirm(const std::string &title, const std::string &body, std::vector<std::string> choices,
                               std::function<void(int)> callback, bool dismissOnOutsideClick, bool twoColumns,
                               std::vector<std::string> choiceIcons)
{
    m_confirmation = Confirmation{title, body, std::move(choices), std::move(callback), 0,
                                  dismissOnOutsideClick, twoColumns, std::move(choiceIcons)};
    m_confirmationNew = true;
    m_focus = "modal-0";
    m_pressed.clear();
}

void MenuDesignScreen::closeConfirmation()
{
    m_confirmation.reset();
    m_focus.clear();
}
void MenuDesignScreen::setModalBody(const std::string &text)
{
    if (m_confirmation)
    {
        m_confirmation->body = text;
    }
}
void MenuDesignScreen::setModalNotes(const std::string &text)
{
    if (m_confirmation)
    {
        m_confirmation->notes = text;
        m_confirmation->notesScroll = 0;
    }
}

void MenuDesignScreen::drawConfirmation()
{
    if (!m_confirmation)
    {
        return;
    }
    loadDesign("menu/confirmation");
    setDesignClip(std::nullopt);
    m_drawingConfirmation = true;
    const bool twoColumns = m_confirmation->twoColumns;
    const bool list = m_confirmation->choices.size() > 3;
    const int total = int(m_confirmation->choices.size());
    const int count = twoColumns ? total : std::min(8, total);
    // The grid: two columns, three when two would run off the 480-unit canvas (MAW's twenty classes); rows close up
    // to fit what still would not.
    constexpr float GridTop = 126;
    constexpr float GridBottom = 46;
    constexpr float GridRowPitch = 46;
    constexpr float GridCanvasHeight = 472;
    const int columns = !twoColumns ? 1
        : GridTop + GridBottom + (count + 1) / 2 * GridRowPitch > GridCanvasHeight ? std::min(3, count)
        : std::min(2, count);
    const int gridRows = (count + columns - 1) / columns;
    const float gridRowPitch = gridRows > 0
        ? std::min(GridRowPitch, std::floor((GridCanvasHeight - GridTop - GridBottom) / gridRows)) : GridRowPitch;
    const auto *pPanel = m_designLayouts.findElement("MenuConfirmationPanel");
    const auto *pBody = m_designLayouts.findElement("MenuConfirmationBody");
    const float unit = designScale();
    const float bodySize = pBody->textScale * fontHeight(pBody->fontName);
    const float bodyScale = unit * bodySize / std::max(1, fontHeight(pBody->fontName));
    const float bodyLineHeight = bodySize * 1.2f;
    // Release notes widen the panel so their lines wrap less; the title, body and buttons widen with it.
    constexpr float NotesPanelWidth = 560;
    const float widen = !list && !twoColumns && !m_confirmation->notes.empty()
        ? std::max(0.0f, NotesPanelWidth - pPanel->width) : 0.0f;
    const float bodyWidth = pBody->width + widen;
    // With a row of buttons the panel grows to fit a long body, and by the notes box above it.
    constexpr float NotesPadding = 6;
    float bodyExtra = 0;
    float notesHeight = 0;
    struct NoteLine
    {
        std::string text;
        float indent = 0;
    };
    std::vector<NoteLine> noteLines;
    if (!list && !twoColumns)
    {
        size_t bodyLines = 0;
        std::istringstream paragraphs(m_confirmation->body);
        std::string paragraph;
        while (std::getline(paragraphs, paragraph))
        {
            bodyLines += wrapParagraph(paragraph, pBody->fontName, bodyScale, bodyWidth * unit).size();
        }
        if (bodyLines > 0)
        {
            bodyExtra = std::max(0.0f, bodySize + (bodyLines - 1) * bodyLineHeight - pBody->height);
        }

        // A "- " line is a bullet: its wrapped lines align after the dash.
        constexpr float NotesMaxHeight = 150;
        const float wrapWidth = (bodyWidth - 2 * NotesPadding - 14) * unit;
        std::istringstream notes(m_confirmation->notes);
        while (std::getline(notes, paragraph))
        {
            const bool bullet = paragraph.starts_with("- ");
            const float indent = bullet ? measureTextWidth(pBody->fontName, "- ", bodyScale) : 0;
            const std::vector<std::string> wrapped =
                wrapParagraph(bullet ? paragraph.substr(2) : paragraph, pBody->fontName, bodyScale, wrapWidth - indent);
            for (size_t i = 0; i < wrapped.size(); ++i)
            {
                noteLines.push_back({(bullet && i == 0 ? "- " : "") + wrapped[i], bullet && i > 0 ? indent : 0});
            }
        }
        if (!noteLines.empty())
        {
            notesHeight = std::min(NotesMaxHeight, noteLines.size() * bodyLineHeight + 2 * NotesPadding);
        }
    }
    constexpr float NotesGap = 10;
    const float notesShift = notesHeight > 0 ? notesHeight + NotesGap : 0;
    const float height = twoColumns ? GridTop + gridRows * gridRowPitch + GridBottom
                                   : list ? 155.0f + count * 25 : pPanel->height + bodyExtra + notesShift;
    const float verticalShift = (pPanel->height - height) / 2 * designScale();
    const auto modalRect = [this, verticalShift, widen](const std::string &id)
    {
        Rect rect = designRect(id);
        rect.y += verticalShift;
        if (id != "MenuConfirmationSeal")
        {
            rect.x -= widen / 2 * designScale();
            rect.width += widen * designScale();
        }
        return rect;
    };
    Rect panel = modalRect("MenuConfirmationPanel");
    if (twoColumns)
    {
        const float width = (columns > 2 ? 720 : 600) * designScale();
        panel.x += (panel.width - width) / 2;
        panel.width = width;
    }
    panel.height = height * designScale();
    const auto modalText = [this, &modalRect, twoColumns, &panel](const std::string &id, const std::string &text)
    {
        const auto *pElement = m_designLayouts.findElement(id);
        Rect rect = modalRect(id);
        if (twoColumns)
        {
            rect.x = panel.x + 36 * designScale();
            rect.width = panel.width - 72 * designScale();
        }
        textInRect(rect, text, pElement->fontName, pElement->textScale * fontHeight(pElement->fontName),
                   pElement->textColorAbgr, true);
    };
    drawTexture(m_designLayouts.findElement("MenuConfirmationVeil")->primaryAsset,
                {0, 0, float(frameWidth()), float(frameHeight())});
    drawTexture(pPanel->primaryAsset, panel);
    drawTexture(m_designLayouts.findElement("MenuConfirmationSeal")->primaryAsset, modalRect("MenuConfirmationSeal"));
    modalText("MenuConfirmationTitle", m_confirmation->title);
    if (notesHeight > 0)
    {
        Rect box = modalRect("MenuConfirmationBody");
        box.height = notesHeight * unit;
        outline(box, 0xff29382au);
        const Rect viewport{box.x + NotesPadding * unit, box.y + NotesPadding * unit,
                            box.width - 2 * NotesPadding * unit, box.height - 2 * NotesPadding * unit};
        scrollViewport(viewport, noteLines.size() * bodyLineHeight, m_confirmation->notesScroll, bodyLineHeight * 3);
        setDesignClip(viewport);
        float y = viewport.y - m_confirmation->notesScroll * unit;
        for (const NoteLine &line : noteLines)
        {
            drawText(pBody->fontName, line.text, viewport.x + line.indent, y, pBody->textColorAbgr, bodyScale);
            y += bodyLineHeight * unit;
        }
        setDesignClip(std::nullopt);
    }
    if (twoColumns || list)
    {
        modalText("MenuConfirmationBody", m_confirmation->body);
    }
    else
    {
        Rect body = modalRect("MenuConfirmationBody");
        body.y += notesShift * unit;
        body.height += bodyExtra * unit;
        textInRect(body, m_confirmation->body, pBody->fontName, bodySize, pBody->textColorAbgr, true);
    }
    int selected = -2;
    if (!m_confirmationNew &&
        (keyPressed(SDL_SCANCODE_ESCAPE) ||
         (m_confirmation->dismissOnOutsideClick && leftMouseJustReleased() && !pointerInside(panel))))
    {
        selected = -1;
    }
    if (!m_confirmationNew && list && !twoColumns && mouseWheelDelta() != 0)
    {
        m_confirmation->scroll = std::clamp(m_confirmation->scroll - int(mouseWheelDelta()), 0,
                                            std::max(0, int(m_confirmation->choices.size()) - count));
        m_focus.clear();
    }
    int navigation = 0;
    if (keyPressed(SDL_SCANCODE_DOWN))
    {
        navigation = columns;
    }
    if (keyPressed(SDL_SCANCODE_UP))
    {
        navigation = -columns;
    }
    if (keyPressed(SDL_SCANCODE_RIGHT))
    {
        navigation = 1;
    }
    if (keyPressed(SDL_SCANCODE_LEFT))
    {
        navigation = -1;
    }
    if (keyPressed(SDL_SCANCODE_PAGEDOWN))
    {
        navigation = count;
    }
    if (keyPressed(SDL_SCANCODE_PAGEUP))
    {
        navigation = -count;
    }
    if (keyPressed(SDL_SCANCODE_TAB))
    {
        navigation = isScancodeHeld(SDL_SCANCODE_LSHIFT) || isScancodeHeld(SDL_SCANCODE_RSHIFT) ? -1 : 1;
    }
    if (!m_confirmationNew && (navigation != 0 || keyPressed(SDL_SCANCODE_HOME) || keyPressed(SDL_SCANCODE_END)))
    {
        m_keyboardFocus = true;
        int index = m_focus.starts_with("modal-") ? std::stoi(m_focus.substr(6)) : m_confirmation->scroll;
        index = (index + navigation + total) % total;
        if (keyPressed(SDL_SCANCODE_HOME))
        {
            index = 0;
        }
        if (keyPressed(SDL_SCANCODE_END))
        {
            index = total - 1;
        }
        m_focus = "modal-" + std::to_string(index);
        m_confirmation->scroll = std::clamp(m_confirmation->scroll, std::max(0, index - count + 1), index);
    }
    for (int i = 0; i < count; ++i)
    {
        const int index = i + (list && !twoColumns ? m_confirmation->scroll : 0);
        const float scale = designScale();
        const Rect body = modalRect("MenuConfirmationBody");
        const float width = list ? body.width - 18 * scale : (body.width - 8 * scale) / count - 6 * scale;
        Rect rect = modalRect("MenuConfirmationCancelButton");
        if (twoColumns)
        {
            const float width = (panel.width - 72 * scale - (columns - 1) * 12 * scale) / columns;
            rect = {panel.x + 36 * scale + (i % columns) * (width + 12 * scale),
                    panel.y + (GridTop + (i / columns) * gridRowPitch) * scale, width, (gridRowPitch - 8) * scale};
        }
        else if (list)
        {
            rect = {panel.x + (panel.width - width) / 2, panel.y + (133 + i * 25) * scale, width, 22 * scale};
        }
        else
        {
            rect.x += i * (width + 6 * scale);
            rect.y += (bodyExtra + notesShift) * scale;
            rect.width = width;
        }
        const bool hasIcon = index < int(m_confirmation->choiceIcons.size())
            && !m_confirmation->choiceIcons[index].empty();
        if (button("modal-" + std::to_string(index), rect, hasIcon ? "" : m_confirmation->choices[index],
                   index == count - 1 && !list && !twoColumns ? "button_primary" : "button_quiet"))
        {
            selected = index;
        }
        if (hasIcon)
        {
            drawTexture(m_confirmation->choiceIcons[index],
                        {rect.x + 8 * scale, rect.y + (rect.height - 28 * scale) / 2, 28 * scale, 28 * scale});
            textInRect({rect.x + 44 * scale, rect.y, rect.width - 52 * scale, rect.height},
                       m_confirmation->choices[index], "fondamento", 13.8667f,
                       pointerInside(rect) ? 0xffc0f0ffu : 0xffa4d1e8u);
        }
    }
    m_drawingConfirmation = false;
    m_confirmationNew = false;
    if (selected != -2)
    {
        std::function<void(int)> callback = std::move(m_confirmation->callback);
        closeConfirmation();
        if (callback)
        {
            callback(selected);
        }
    }
}
} // namespace OpenYAMM::Game

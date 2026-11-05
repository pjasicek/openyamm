#pragma once

#include "game/ui/MenuScreenBase.h"
#include "game/ui/UiLayoutManager.h"

#include <functional>
#include <unordered_set>

namespace OpenYAMM::Game
{
class GameAudioSystem;
// Shared presentation and input for the native Carved Obsidian menu screens.
class MenuDesignScreen : public MenuScreenBase
{
  public:
    explicit MenuDesignScreen(const Engine::AssetFileSystem &assetFileSystem, bool overGameplay = false,
                              GameAudioSystem *pAudio = nullptr);
    bool rendersOverGameplay() const override;
    bool textInputActive() const override;

  protected:
    void loadDesign(const std::string &path);
    void beginDesign(const std::string &screen);
    void drawDesign();
    Rect designRect(const std::string &id) const;
    Rect canvasRect(float x, float y, float width, float height) const;
    float designScale() const;
    void label(const std::string &id, const std::string &text, uint32_t color = 0, float offsetY = 0);
    void textInRect(const Rect &rect, const std::string &text, const std::string &font = "menu_arrus",
                    float logicalSize = 12, uint32_t color = 0xffc6dfeau, bool centered = false);
    // The height in pixels of text word-wrapped to width (pixels), laid out as textInRect does.
    float textBlockHeight(const std::string &text, const std::string &font, float logicalSize, float width);
    bool action(const std::string &id, bool enabled = true, const std::string &text = {});
    // The input side of a button without its artwork: hover, press and activation (mouse release over the rect, or
    // Return/Space with keyboard focus). The caller draws the control.
    struct Hotspot
    {
        bool hovered = false;
        bool pressed = false;
        bool activated = false;
    };
    Hotspot hotspot(const std::string &id, const Rect &rect, bool enabled = true);
    bool button(const std::string &id, const Rect &rect, const std::string &text, const std::string &skin = "button",
                bool enabled = true, bool selected = false);
    bool selectBox(const std::string &id, const Rect &rect, const std::string &value, bool enabled = true,
                   float logicalSize = 11.52f);
    void skin(const std::string &name, const Rect &rect, bool sliced = false, float padding = 0);
    void outline(const Rect &rect, uint32_t color);
    void confirm(const std::string &title, const std::string &body, std::vector<std::string> choices,
                 std::function<void(int)> callback, bool dismissOnOutsideClick = false, bool twoColumns = false,
                 std::vector<std::string> choiceIcons = {});
    void drawConfirmation();
    bool modalOpen() const;
    void closeConfirmation();
    void setModalBody(const std::string &text);
    // Release notes for the open confirmation: a left-aligned box between its title and body that scrolls when long.
    void setModalNotes(const std::string &text);
    void setTextEditing(bool editing);
    void setDesignClip(const std::optional<Rect> &rect);
    bool pointerInside(const Rect &rect) const;
    bool keyPressed(SDL_Scancode key) const;
    bool focused(const std::string &id) const;
    void revealFocus(const Rect &viewport, float &scroll) const;
    // A scroll box over viewport: the mouse wheel, a scrollbar when the content is taller, and dragging the content
    // itself (a touch screen's swipe; a press that moves past a few pixels becomes a drag and no longer clicks).
    void scrollViewport(const Rect &viewport, float contentHeight, float &scroll, float wheelStep = 33,
                        bool enabled = true);
    // A control that drags on its own (a slider) keeps the press from becoming a content drag.
    void cancelContentDrag();
    UiLayoutManager m_designLayouts;

  private:
    std::vector<std::string> wrapParagraph(const std::string &paragraph, const std::string &font, float scale,
                                           float width);
    std::string m_designScreen;
    std::unordered_set<std::string> m_loadedDesigns;
    std::vector<std::string> m_focusTargets;
    std::unordered_map<std::string, Rect> m_focusRects;
    std::optional<Rect> m_revealFocus;
    std::optional<float> m_scrollDragOffset;
    struct ContentDrag
    {
        const float *pScroll = nullptr;
        float startY = 0;
        float startScroll = 0;
        bool moving = false;
    };
    std::optional<ContentDrag> m_contentDrag;
    std::string m_focus;
    std::string m_pressed;
    bool m_keyboardFocus = false;
    bool m_overGameplay = false;
    GameAudioSystem *m_pAudio = nullptr;
    bool m_textEditing = false;
    std::optional<Rect> m_designClip;
    struct Confirmation
    {
        std::string title;
        std::string body;
        std::vector<std::string> choices;
        std::function<void(int)> callback;
        int scroll = 0;
        bool dismissOnOutsideClick = false;
        bool twoColumns = false;
        std::vector<std::string> choiceIcons;
        std::string notes;
        float notesScroll = 0;
    };
    std::optional<Confirmation> m_confirmation;
    bool m_drawingConfirmation = false;
    bool m_confirmationNew = false;
};
} // namespace OpenYAMM::Game

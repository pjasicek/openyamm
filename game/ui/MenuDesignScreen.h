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
    bool action(const std::string &id, bool enabled = true, const std::string &text = {});
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
    void setTextEditing(bool editing);
    void setDesignClip(const std::optional<Rect> &rect);
    bool pointerInside(const Rect &rect) const;
    bool keyPressed(SDL_Scancode key) const;
    bool focused(const std::string &id) const;
    void revealFocus(const Rect &viewport, float &scroll) const;
    void scrollViewport(const Rect &viewport, float contentHeight, float &scroll, float wheelStep = 33);
    UiLayoutManager m_designLayouts;

  private:
    std::string m_designScreen;
    std::unordered_set<std::string> m_loadedDesigns;
    std::vector<std::string> m_focusTargets;
    std::unordered_map<std::string, Rect> m_focusRects;
    std::optional<Rect> m_revealFocus;
    std::optional<float> m_scrollDragOffset;
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
    };
    std::optional<Confirmation> m_confirmation;
    bool m_drawingConfirmation = false;
    bool m_confirmationNew = false;
};
} // namespace OpenYAMM::Game

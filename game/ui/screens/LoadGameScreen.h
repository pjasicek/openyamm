#pragma once

#include "game/tables/MapStats.h"
#include "game/ui/MenuScreenBase.h"
#include "game/ui/UiLayoutManager.h"

#include <filesystem>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class LoadGameScreen : public MenuScreenBase
{
public:
    using LoadAction = std::function<bool(const std::filesystem::path &)>;
    using CancelAction = std::function<void()>;

    LoadGameScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::vector<MapStatsEntry> &mapEntries,
        LoadAction loadAction,
        CancelAction cancelAction);

    AppMode mode() const override;
    void onEnter() override;

private:
    struct SaveSlotSummary
    {
        std::filesystem::path path;
        std::string fileLabel;
        std::string locationName;
        std::string weekdayClockText;
        std::string dateText;
        bool populated = false;
        int previewWidth = 0;
        int previewHeight = 0;
        std::vector<uint8_t> previewPixelsBgra;
    };

    void drawScreen(float deltaSeconds) override;
    void refreshSaveSlots();
    bool tryLoadSelectedSlot();
    void cancel();
    bool ensureLayoutLoaded();
    std::optional<Rect> resolveLayoutRect(
        const std::string &layoutId,
        float fallbackWidth = 0.0f,
        float fallbackHeight = 0.0f) const;
    ButtonVisualSet resolveButtonVisuals(
        const std::string &layoutId,
        const ButtonVisualSet &fallbackVisuals) const;
    std::string resolveAssetName(const std::string &layoutId, const std::string &fallbackAssetName) const;
    void drawLayoutText(
        const std::string &layoutId,
        const std::string &text,
        uint32_t colorAbgrOverride = 0) const;

    const std::vector<MapStatsEntry> *m_pMapEntries = nullptr;
    LoadAction m_loadAction;
    CancelAction m_cancelAction;
    UiLayoutManager m_layoutManager;
    bool m_layoutLoaded = false;
    bool m_escapePressed = false;
    bool m_returnPressed = false;
    size_t m_selectedIndex = 0;
    size_t m_scrollOffset = 0;
    uint64_t m_lastClickedSlotTicks = 0;
    size_t m_lastClickedSlotIndex = static_cast<size_t>(-1);
    std::vector<SaveSlotSummary> m_slots;
};
}

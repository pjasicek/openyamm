#pragma once

#include "game/tables/MapStats.h"
#include "game/ui/MenuScreenBase.h"

#include <filesystem>
#include <functional>
#include <vector>

namespace OpenYAMM::Game
{
class LoadMenuScreen : public MenuScreenBase
{
public:
    using LoadAction = std::function<void(const std::filesystem::path &)>;
    using CancelAction = std::function<void()>;

    LoadMenuScreen(
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
    };

    void drawScreen(float deltaSeconds) override;
    void refreshSaveSlots();

    std::vector<MapStatsEntry> m_mapEntries;
    LoadAction m_loadAction;
    CancelAction m_cancelAction;
    std::vector<SaveSlotSummary> m_saveSlots;
    size_t m_selectedIndex = 0;
    size_t m_scrollOffset = 0;
};
}

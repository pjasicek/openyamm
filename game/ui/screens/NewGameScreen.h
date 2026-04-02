#pragma once

#include "game/tables/RosterTable.h"
#include "game/ui/MenuScreenBase.h"

#include <functional>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class NewGameScreen : public MenuScreenBase
{
public:
    using ContinueAction = std::function<void(std::optional<uint32_t>)>;
    using BackAction = std::function<void()>;

    NewGameScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        const RosterTable &rosterTable,
        ContinueAction continueAction,
        BackAction backAction);

    AppMode mode() const override;
    void onEnter() override;

private:
    void drawScreen(float deltaSeconds) override;
    void refreshCandidates();

    const RosterTable *m_pRosterTable = nullptr;
    ContinueAction m_continueAction;
    BackAction m_backAction;
    std::vector<const RosterEntry *> m_candidates;
    size_t m_selectedIndex = 0;
    size_t m_scrollOffset = 0;
};
}

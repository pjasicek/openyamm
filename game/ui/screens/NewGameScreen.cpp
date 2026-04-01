#include "game/ui/screens/NewGameScreen.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
std::string portraitTextureNameFromPictureId(uint32_t pictureId)
{
    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-01", pictureId + 1);
    return buffer;
}
}

NewGameScreen::NewGameScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    const RosterTable &rosterTable,
    ContinueAction continueAction,
    BackAction backAction)
    : MenuScreenBase(assetFileSystem)
    , m_pRosterTable(&rosterTable)
    , m_continueAction(std::move(continueAction))
    , m_backAction(std::move(backAction))
{
}

AppMode NewGameScreen::mode() const
{
    return AppMode::NewGame;
}

void NewGameScreen::onEnter()
{
    refreshCandidates();
}

void NewGameScreen::drawScreen(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);

    constexpr float RootWidth = 640.0f;
    constexpr float RootHeight = 480.0f;
    constexpr size_t VisibleCandidates = 12;
    const float scale = std::min(
        static_cast<float>(frameWidth()) / RootWidth,
        static_cast<float>(frameHeight()) / RootHeight);
    const float rootX = (static_cast<float>(frameWidth()) - RootWidth * scale) * 0.5f;
    const float rootY = (static_cast<float>(frameHeight()) - RootHeight * scale) * 0.5f;

    drawTexture("mm6title", Rect{rootX, rootY, RootWidth * scale, RootHeight * scale});

    if (mouseWheelDelta() > 0.0f && m_scrollOffset > 0)
    {
        --m_scrollOffset;
    }
    else if (mouseWheelDelta() < 0.0f && m_scrollOffset + VisibleCandidates < m_candidates.size())
    {
        ++m_scrollOffset;
    }

    const size_t visibleEnd = std::min(m_candidates.size(), m_scrollOffset + VisibleCandidates);

    for (size_t index = m_scrollOffset; index < visibleEnd; ++index)
    {
        const float rowY = rootY + (40.0f + static_cast<float>(index - m_scrollOffset) * 24.0f) * scale;
        const Rect rowRect{rootX + 30.0f * scale, rowY, 160.0f * scale, 20.0f * scale};

        if (hitTest(rowRect) && leftMouseJustReleased())
        {
            m_selectedIndex = index;
        }

        drawDebugText(
            static_cast<int>(rowRect.x),
            static_cast<int>(rowRect.y),
            index == m_selectedIndex ? 0x0e : 0x0f,
            m_candidates[index]->name);
    }

    const ButtonState backButton = drawButton(
        ButtonVisualSet{"bt_backU", "bt_backH", "bt_backD"},
        Rect{rootX + 26.0f * scale, rootY + 394.0f * scale, 78.0f * scale, 30.0f * scale});
    const ButtonState continueButton = drawButton(
        ButtonVisualSet{"bt_contU", "bt_contH", "bt_contD"},
        Rect{rootX + 120.0f * scale, rootY + 394.0f * scale, 78.0f * scale, 30.0f * scale});

    if (backButton.clicked && m_backAction)
    {
        m_backAction();
        return;
    }

    if (continueButton.clicked && m_continueAction)
    {
        if (!m_candidates.empty())
        {
            m_continueAction(m_candidates[m_selectedIndex]->id);
        }
        else
        {
            m_continueAction(std::nullopt);
        }

        return;
    }

    if (m_candidates.empty())
    {
        drawDebugText(static_cast<int>(rootX + 220.0f * scale), static_cast<int>(rootY + 80.0f * scale), 0x0c, "No roster characters");
        return;
    }

    const RosterEntry &selectedEntry = *m_candidates[m_selectedIndex];
    drawTexture(
        portraitTextureNameFromPictureId(selectedEntry.pictureId),
        Rect{rootX + 233.0f * scale, rootY + 36.0f * scale, 144.0f * scale, 144.0f * scale});
    drawDebugText(static_cast<int>(rootX + 230.0f * scale), static_cast<int>(rootY + 186.0f * scale), 0x0f, selectedEntry.name);
    drawDebugText(static_cast<int>(rootX + 230.0f * scale), static_cast<int>(rootY + 202.0f * scale), 0x0f, selectedEntry.className);

    drawDebugText(static_cast<int>(rootX + 420.0f * scale), static_cast<int>(rootY + 34.0f * scale), 0x0f, "Statistics");
    drawDebugText(static_cast<int>(rootX + 420.0f * scale), static_cast<int>(rootY + 52.0f * scale), 0x0f, "Might       " + std::to_string(selectedEntry.might));
    drawDebugText(static_cast<int>(rootX + 420.0f * scale), static_cast<int>(rootY + 68.0f * scale), 0x0f, "Intellect   " + std::to_string(selectedEntry.intellect));
    drawDebugText(static_cast<int>(rootX + 420.0f * scale), static_cast<int>(rootY + 84.0f * scale), 0x0f, "Personality " + std::to_string(selectedEntry.personality));
    drawDebugText(static_cast<int>(rootX + 420.0f * scale), static_cast<int>(rootY + 100.0f * scale), 0x0f, "Endurance   " + std::to_string(selectedEntry.endurance));
    drawDebugText(static_cast<int>(rootX + 420.0f * scale), static_cast<int>(rootY + 116.0f * scale), 0x0f, "Accuracy    " + std::to_string(selectedEntry.accuracy));
    drawDebugText(static_cast<int>(rootX + 420.0f * scale), static_cast<int>(rootY + 132.0f * scale), 0x0f, "Speed       " + std::to_string(selectedEntry.speed));
    drawDebugText(static_cast<int>(rootX + 420.0f * scale), static_cast<int>(rootY + 148.0f * scale), 0x0f, "Luck        " + std::to_string(selectedEntry.luck));

    drawDebugText(static_cast<int>(rootX + 226.0f * scale), static_cast<int>(rootY + 254.0f * scale), 0x0f, "Starting Skills");

    int skillLineIndex = 0;

    for (const auto &[skillName, skill] : selectedEntry.skills)
    {
        if (skillLineIndex >= 6)
        {
            break;
        }

        drawDebugText(
            static_cast<int>(rootX + 226.0f * scale),
            static_cast<int>(rootY + (272.0f + static_cast<float>(skillLineIndex) * 16.0f) * scale),
            0x0f,
            skillName + " " + std::to_string(skill.level));
        ++skillLineIndex;
    }
}

void NewGameScreen::refreshCandidates()
{
    m_candidates.clear();

    for (const RosterEntry *pEntry : m_pRosterTable->getEntriesSortedById())
    {
        if (pEntry == nullptr || pEntry->name.empty())
        {
            continue;
        }

        m_candidates.push_back(pEntry);
    }

    m_selectedIndex = 0;
    m_scrollOffset = 0;
}
}

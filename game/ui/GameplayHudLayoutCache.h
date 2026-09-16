#pragma once

#include "game/ui/UiLayoutManager.h"

#include <initializer_list>
#include <optional>
#include <string_view>

namespace OpenYAMM::Game
{
enum class GameplayHudLayoutMode
{
    Overlay,
    Standard,
    Widescreen
};

struct GameplayHudLayoutEntry
{
    const UiLayoutManager::LayoutElement *pLayout = nullptr;
    std::string normalizedRoleId;
    bool overlay = false;
    bool standard = false;
    bool widescreen = false;
    bool followerPanel = false;

    bool visibleIn(GameplayHudLayoutMode layout, bool followerPanelOpen) const
    {
        switch (layout)
        {
        case GameplayHudLayoutMode::Overlay:
            return overlay;
        case GameplayHudLayoutMode::Standard:
            return standard;
        case GameplayHudLayoutMode::Widescreen:
            return widescreen && (!followerPanel || followerPanelOpen);
        }
        return false;
    }
};

// Owns only derived metadata. Layout geometry and live UI/gameplay state remain
// authoritative in their existing owners and are evaluated during rendering.
class GameplayHudLayoutCache
{
public:
    const std::vector<GameplayHudLayoutEntry> &entries(const UiLayoutManager &manager)
    {
        if (m_pManager == &manager && m_revision == manager.revision())
        {
            return m_entries;
        }
        m_entries.clear();
        m_pManager = &manager;
        m_revision = manager.revision();
        for (const std::string &id : manager.sortedLayoutIdsForScreenCached("OutdoorHud"))
        {
            const UiLayoutManager::LayoutElement *pLayout = manager.findElement(id);
            if (pLayout == nullptr || manuallyRendered(pLayout->normalizedId))
            {
                continue;
            }
            GameplayHudLayoutEntry entry;
            entry.pLayout = pLayout;
            entry.normalizedRoleId = pLayout->normalizedId;
            constexpr std::string_view standardPrefix = "outdoorstandard";
            if (entry.normalizedRoleId.starts_with(standardPrefix))
            {
                entry.normalizedRoleId = "outdoor" + entry.normalizedRoleId.substr(standardPrefix.size());
            }
            entry.overlay = descendantOfAny(manager, *pLayout, {"outdoorbasebar"});
            entry.standard = descendantOfAny(manager, *pLayout, {"outdoorstandardbasebar", "outdoorstandardtopbar"});
            entry.followerPanel = descendantOfAny(manager, *pLayout, {"outdoorfollowerpanel"});
            entry.widescreen = entry.followerPanel || descendantOfAny(manager, *pLayout, {
                "outdoorfollowertoggle", "outdoorgameplaybasebar", "outdooroptionsbar", "outdoorgoldbar",
                "outdoorfoodrestbar", "outdoorflybufficon", "outdoorbuffbodypanel", "outdoorbuffskullpanel",
                "outdoorminimapframe", "outdoormobileactionpanel", "outdoormobileflightpanel",
                "outdoormobilesystempanel",
                "outdoormobilemovementzone"});
            if (entry.overlay || entry.standard || entry.widescreen)
            {
                m_entries.push_back(std::move(entry));
            }
        }
        return m_entries;
    }

private:
    const UiLayoutManager *m_pManager = nullptr;
    std::optional<uint64_t> m_revision;
    std::vector<GameplayHudLayoutEntry> m_entries;

    static bool descendantOfAny(const UiLayoutManager &manager, const UiLayoutManager::LayoutElement &layout,
        std::initializer_list<std::string_view> ancestors)
    {
        const UiLayoutManager::LayoutElement *pCurrent = &layout;
        while (pCurrent != nullptr)
        {
            for (std::string_view ancestor : ancestors)
            {
                if (pCurrent->normalizedId == ancestor)
                {
                    return true;
                }
            }
            pCurrent = pCurrent->parentId.empty() ? nullptr : manager.findElement(pCurrent->parentId);
        }
        return false;
    }

    static bool manuallyRendered(const std::string &normalizedLayoutId)
    {
        return normalizedLayoutId == "outdoorbasebar"
            || normalizedLayoutId == "outdoorpartystrip"
            || normalizedLayoutId == "outdoorstandardbasebar"
            || normalizedLayoutId == "outdoorstandardpartystrip"
            || normalizedLayoutId == "outdoorstandardstatusbar"
            || normalizedLayoutId == "outdoorgameplaybasebar"
            || normalizedLayoutId == "outdoorgameplaypartystrip"
            || normalizedLayoutId == "outdoorgameplaystatusbar"
            || normalizedLayoutId == "outdoorgameplaybasebar_ornleft1"
            || normalizedLayoutId == "outdoorgameplaybasebar_ornleft2"
            || normalizedLayoutId == "outdoorgameplaybasebar_ornright1"
            || normalizedLayoutId == "outdoorgameplaybasebar_ornright2"
            || normalizedLayoutId == "outdoormobileinspectbutton"
            || normalizedLayoutId == "outdoormobileinspectbuttonicon"
            || normalizedLayoutId.rfind("charshield_", 0) == 0
            || normalizedLayoutId.rfind("outdoorstandardcharshield_", 0) == 0;
    }
};
}

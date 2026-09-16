#include "doctest/doctest.h"

#include "game/ui/GameplayHudLayoutCache.h"

#include <algorithm>

using namespace OpenYAMM::Game;

TEST_CASE("HUD classification caches ancestry and roles while follower visibility stays live")
{
    UiLayoutManager manager;
    REQUIRE(manager.loadLayoutText("hud", R"(
screen: OutdoorHud
elements:
  - id: OutdoorBasebar
    anchor: BottomLeft
    children:
      - {id: OverlayChild, anchor: InsideTopLeft, z_index: 3}
  - id: OutdoorStandardTopbar
    anchor: TopLeft
    children:
      - {id: OutdoorStandardFood, anchor: InsideTopLeft, z_index: 2}
  - id: OutdoorFollowerPanel
    anchor: TopLeft
    children:
      - {id: FollowerChild, anchor: InsideTopLeft, z_index: 1}
  - {id: OutdoorFollowerToggle, anchor: TopLeft}
  - {id: Unrelated, anchor: TopLeft}
)"));
    GameplayHudLayoutCache cache;
    const std::vector<GameplayHudLayoutEntry> &entries = cache.entries(manager);
    const auto find = [&](const std::string &id) -> const GameplayHudLayoutEntry &
    {
        const auto it = std::find_if(entries.begin(), entries.end(),
            [&](const GameplayHudLayoutEntry &entry) { return entry.pLayout->id == id; });
        REQUIRE(it != entries.end());
        return *it;
    };
    CHECK(find("OverlayChild").visibleIn(GameplayHudLayoutMode::Overlay, false));
    CHECK_FALSE(find("OverlayChild").visibleIn(GameplayHudLayoutMode::Standard, true));
    CHECK(find("OutdoorStandardFood").normalizedRoleId == "outdoorfood");
    CHECK(find("OutdoorStandardFood").visibleIn(GameplayHudLayoutMode::Standard, false));
    CHECK_FALSE(find("FollowerChild").visibleIn(GameplayHudLayoutMode::Widescreen, false));
    CHECK(find("FollowerChild").visibleIn(GameplayHudLayoutMode::Widescreen, true));
    CHECK(find("OutdoorFollowerToggle").visibleIn(GameplayHudLayoutMode::Widescreen, false));
    CHECK(std::none_of(entries.begin(), entries.end(), [](const GameplayHudLayoutEntry &entry)
        { return entry.pLayout->id == "Unrelated" || entry.pLayout->id == "OutdoorBasebar"; }));
    CHECK(std::is_sorted(entries.begin(), entries.end(), [](const GameplayHudLayoutEntry &a,
        const GameplayHudLayoutEntry &b) { return a.pLayout->zIndex < b.pLayout->zIndex; }));
    CHECK(cache.entries(manager).data() == entries.data());
}

TEST_CASE("HUD classification refreshes replaced ancestry and clears stale layout pointers")
{
    UiLayoutManager manager;
    GameplayHudLayoutCache cache;
    REQUIRE(manager.loadLayoutText("first", R"(
screen: OutdoorHud
elements:
  - id: OutdoorBasebar
    anchor: BottomLeft
    children:
      - {id: SharedChild, anchor: InsideTopLeft}
)"));
    REQUIRE(cache.entries(manager).size() == 1);
    CHECK(cache.entries(manager)[0].overlay);
    const uint64_t revision = manager.revision();
    REQUIRE(manager.loadLayoutText("override", R"(
screen: OutdoorHud
elements:
  - id: OutdoorStandardBasebar
    anchor: BottomLeft
    children:
      - {id: SharedChild, anchor: InsideTopLeft}
)"));
    CHECK(manager.revision() > revision);
    REQUIRE(cache.entries(manager).size() == 1);
    CHECK_FALSE(cache.entries(manager)[0].overlay);
    CHECK(cache.entries(manager)[0].standard);
    manager.clear();
    CHECK(cache.entries(manager).empty());
    REQUIRE(manager.loadLayoutText("replacement", R"(
screen: OutdoorHud
elements:
  - {id: OutdoorFollowerToggle, anchor: TopLeft}
)"));
    REQUIRE(cache.entries(manager).size() == 1);
    CHECK(cache.entries(manager)[0].pLayout->id == "OutdoorFollowerToggle");
}

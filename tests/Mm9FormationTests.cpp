#include "doctest/doctest.h"

#include "game/mm9/Mm9Formation.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/party/Party.h"
#include "game/ui/UiLayoutManager.h"

#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

// The MM9 formation builder (devdocs/mm9/MM9_HIRELINGS_PLAN.md phase 10): MM9's grid rules, the party's whole
// arrangement and the accepted design's geometry (level_generation/ui/mm9_formation_20261106).
namespace
{
using OpenYAMM::Game::Character;
using OpenYAMM::Game::Mm9FormationGrid;
using OpenYAMM::Game::Mm9FormationRect;
using OpenYAMM::Game::Mm9Hireling;
using OpenYAMM::Game::Mm9HirelingKind;
using OpenYAMM::Game::Party;
using OpenYAMM::Game::UiLayoutManager;
using OpenYAMM::Game::mm9FormationCellAt;
using OpenYAMM::Game::mm9FormationCellRect;
using OpenYAMM::Game::mm9FormationFrontLineCovered;
using OpenYAMM::Game::mm9FormationMove;
using OpenYAMM::Game::mm9FormationOccupant;

Mm9Hireling row(uint32_t rudeId, const std::string &name, Mm9HirelingKind kind)
{
    Mm9Hireling hireling;
    hireling.rudeId = rudeId;
    hireling.name = name;
    hireling.kind = kind;
    hireling.level = 10;
    hireling.hitPoints = 100;
    hireling.armorClass = 10;
    hireling.recoverySeconds = 2.0f;
    return hireling;
}

// The study's party: five members, then two paid retainers and Forad.
Party studyParty()
{
    OpenYAMM::Game::PartySeed seed = {};

    for (size_t memberIndex = 0; memberIndex < 5; ++memberIndex)
    {
        Character member = {};
        member.name = "Member " + std::to_string(memberIndex + 1);
        member.maxHealth = 100;
        member.health = 100;
        seed.members.push_back(member);
    }

    Party party = {};
    party.seed(seed);
    REQUIRE(party.addHireling(row(2, "Forad Darre", Mm9HirelingKind::Story)));
    REQUIRE(party.addHireling(row(280, "Edina A'Mor", Mm9HirelingKind::Paid)));
    REQUIRE(party.addHireling(row(42, "Hrolf Spearmaster", Mm9HirelingKind::Paid)));
    return party;
}

std::string loadSource(const std::filesystem::path &relativePath)
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    std::ostringstream text;
    text << input.rdbuf();
    return text.str();
}

Mm9FormationRect units(const UiLayoutManager &manager, const std::string &id)
{
    const UiLayoutManager::LayoutElement *pElement = manager.findElement(id);
    REQUIRE(pElement != nullptr);
    return {pElement->gapX, pElement->gapY, pElement->width, pElement->height};
}
}

TEST_CASE("MM9 formation builder: the members and hirelings start on the lowest free cells")
{
    const Party party = studyParty();
    // MM9 10.3: the front rank, then middle left and centre for members 4 and 5; the hirelings join at middle right,
    // rear left and rear centre.
    CHECK_EQ(party.formationCells(), std::vector<int32_t>{0, 1, 2, 3, 4, 5, 6, 7});
    CHECK(mm9FormationFrontLineCovered(party.formationCells()));
}

TEST_CASE("MM9 formation builder: a face drops only on an empty cell, with no swap")
{
    std::vector<int32_t> cells = studyParty().formationCells();

    // The third hireling from rear centre to the empty rear right (the study's drag).
    CHECK(mm9FormationMove(cells, 7, 8));
    CHECK_EQ(cells[7], 8);
    CHECK_FALSE(mm9FormationOccupant(cells, 7));
    CHECK_EQ(mm9FormationOccupant(cells, 8), 7u);

    // On an occupied cell the face returns: nothing changes.
    const std::vector<int32_t> before = cells;
    CHECK_FALSE(mm9FormationMove(cells, 0, 4));
    CHECK_FALSE(mm9FormationMove(cells, 7, 8));
    CHECK_FALSE(mm9FormationMove(cells, 0, -1));
    CHECK_FALSE(mm9FormationMove(cells, 0, 9));
    CHECK_FALSE(mm9FormationMove(cells, 8, 7));
    CHECK_EQ(cells, before);
}

TEST_CASE("MM9 formation builder: nobody may stand behind an empty cell")
{
    // The rear centre left empty is allowed: nobody stands behind it.
    CHECK(mm9FormationFrontLineCovered({0, 1, 2, 3, 4, 5, 6, 8}));
    // The front centre emptied with the middle centre held: refused.
    CHECK_FALSE(mm9FormationFrontLineCovered({0, 7, 2, 3, 4, 5, 6, 8}));
    // A rear member behind an empty middle cell: refused.
    CHECK_FALSE(mm9FormationFrontLineCovered({0, 1, 2, 6}));
    // A column may be empty; a single file is covered.
    CHECK(mm9FormationFrontLineCovered({0, 1, 3, 4}));
    CHECK(mm9FormationFrontLineCovered({0, 3, 6}));
    CHECK_FALSE(mm9FormationFrontLineCovered({3}));
    CHECK(mm9FormationFrontLineCovered({}));
}

TEST_CASE("MM9 formation builder: Accept applies the whole arrangement at once")
{
    Party party = studyParty();
    // Two members trade cells through the arrangement (one at a time each move would meet the other's cell).
    std::vector<int32_t> cells = party.formationCells();
    std::swap(cells[0], cells[5]);
    REQUIRE(party.setFormationCells(cells));
    CHECK_EQ(party.formationCell(0), 5);
    CHECK_EQ(party.formationCell(5), 0);

    // Wrong length, a duplicate or an invalid cell changes nothing.
    CHECK_FALSE(party.setFormationCells({0, 1, 2}));
    CHECK_FALSE(party.setFormationCells({0, 1, 2, 3, 4, 5, 6, 6}));
    CHECK_FALSE(party.setFormationCells({0, 1, 2, 3, 4, 5, 6, 9}));
    CHECK_EQ(party.formationCells(), cells);

    // Saved with the party.
    Party restored = {};
    restored.restoreSnapshot(party.snapshot());
    CHECK_EQ(restored.formationCells(), cells);

    // A hireling who leaves frees his cell; the next joiner takes the lowest free one.
    REQUIRE(party.removeHireling(280));
    REQUIRE(party.addHireling(row(281, "Tesar", Mm9HirelingKind::Paid)));
    CHECK_EQ(party.formationCell(7), 6);
}

TEST_CASE("MM9 formation builder keeps the accepted design's geometry")
{
    UiLayoutManager manager;
    REQUIRE(manager.loadLayoutText("mm9_formation.yml", loadSource("assets_dev/engine/ui/gameplay/mm9_formation.yml")));

    // The panel centred in the 640 x 480 frame, 38 units down; the grid 118 / 48 units into it.
    const Mm9FormationRect panel = units(manager, "Mm9FormationPanel");
    CHECK(panel.x + panel.width / 2 == doctest::Approx(320));
    CHECK(panel.y == doctest::Approx(38));
    CHECK(panel.width == doctest::Approx(330));
    CHECK(panel.height == doctest::Approx(334));
    const Mm9FormationRect area = units(manager, "Mm9FormationGrid");
    CHECK(area.x - panel.x == doctest::Approx(118));
    CHECK(area.y - panel.y == doctest::Approx(48));

    // 54 x 66 cells 6 units apart; the 40 x 54 face centred in its cell.
    const Mm9FormationRect cell = units(manager, "Mm9FormationCell");
    const Mm9FormationGrid grid = {{0, 0, area.width, area.height}, cell.width, cell.height};
    CHECK(cell.width == doctest::Approx(54));
    CHECK(cell.height == doctest::Approx(66));
    const Mm9FormationRect centre = mm9FormationCellRect(grid, 4);
    CHECK(centre.x == doctest::Approx(60));
    CHECK(centre.y == doctest::Approx(72));
    const Mm9FormationRect rearRight = mm9FormationCellRect(grid, 8);
    CHECK(rearRight.x + rearRight.width == doctest::Approx(area.width));
    CHECK(rearRight.y + rearRight.height == doctest::Approx(area.height));
    const Mm9FormationRect face = units(manager, "Mm9FormationFace");
    CHECK(face.width == doctest::Approx(40));
    CHECK(face.height == doctest::Approx(54));
    CHECK(face.x * 2 + face.width == doctest::Approx(cell.width));
    CHECK(face.y * 2 + face.height == doctest::Approx(cell.height));

    // Hit testing: the front rank on top, columns left to right, nothing in the gaps.
    CHECK_EQ(mm9FormationCellAt(grid, 1, 1), 0);
    CHECK_EQ(mm9FormationCellAt(grid, 61, 1), 1);
    CHECK_EQ(mm9FormationCellAt(grid, 173, 209), 8);
    CHECK_EQ(mm9FormationCellAt(grid, 1, 150), 6);
    CHECK_FALSE(mm9FormationCellAt(grid, 56, 10));
    CHECK_FALSE(mm9FormationCellAt(grid, 10, 68));

    // Cancel and Accept side by side under the instruction, 8 units either side of the panel's middle.
    const Mm9FormationRect cancel = units(manager, "Mm9FormationCancelButton");
    const Mm9FormationRect accept = units(manager, "Mm9FormationAcceptButton");
    CHECK(cancel.x + cancel.width == doctest::Approx(panel.x + panel.width / 2 - 8));
    CHECK(accept.x == doctest::Approx(panel.x + panel.width / 2 + 8));
    CHECK(cancel.y == doctest::Approx(panel.y + panel.height - 40));

    // The button in the followers' place under the minimap.
    UiLayoutManager hud;
    REQUIRE(hud.loadLayoutText("gameplay.yml", loadSource("assets_dev/engine/ui/gameplay/gameplay.yml")));
    const UiLayoutManager::LayoutElement *pButton = hud.findElement("Mm9FormationButton");
    REQUIRE(pButton != nullptr);
    CHECK(pButton->anchor == UiLayoutManager::LayoutAnchor::TopRight);
    CHECK(pButton->offsetX == doctest::Approx(-4));
    CHECK(pButton->offsetY == doctest::Approx(148));
    CHECK(pButton->width == doctest::Approx(24));
}

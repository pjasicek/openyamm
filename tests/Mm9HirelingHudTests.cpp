#include "doctest/doctest.h"

#include "game/gameplay/GameMechanics.h"
#include "game/mm9/Mm9HirelingHud.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/ui/UiLayoutManager.h"

#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace
{
using OpenYAMM::Game::Mm9Hireling;
using OpenYAMM::Game::Mm9HirelingRailRect;
using OpenYAMM::Game::Mm9HirelingTable;
using OpenYAMM::Game::UiLayoutManager;

std::string loadSource(const std::filesystem::path &relativePath)
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    std::ostringstream text;
    text << input.rdbuf();
    return text.str();
}

// A child's rectangle in its rail's units (offsets from the rail's top-left corner).
Mm9HirelingRailRect railUnits(const UiLayoutManager &manager, const std::string &id)
{
    const UiLayoutManager::LayoutElement *pElement = manager.findElement(id);
    REQUIRE(pElement != nullptr);
    Mm9HirelingRailRect rect = {pElement->gapX, pElement->gapY, pElement->width, pElement->height};

    if (pElement->parentId != "Mm9HirelingRail")
    {
        const Mm9HirelingRailRect parent = railUnits(manager, pElement->parentId);
        rect.x += parent.x;
        rect.y += parent.y;
    }

    return rect;
}
}

TEST_CASE("MM9 hireling rail keeps revision 2's geometry")
{
    UiLayoutManager manager;
    REQUIRE(manager.loadLayoutText("gameplay.yml", loadSource("assets_dev/engine/ui/gameplay/gameplay.yml")));
    const UiLayoutManager::LayoutElement *pRail = manager.findElement("Mm9HirelingRail");
    REQUIRE(pRail != nullptr);
    // Flush with the right edge, 6 units under the combat-log/followers row (it ends at 172), 70 units wide.
    CHECK(pRail->anchor == UiLayoutManager::LayoutAnchor::TopRight);
    CHECK(pRail->offsetX == doctest::Approx(0));
    CHECK(pRail->offsetY == doctest::Approx(178));
    CHECK(pRail->width == doctest::Approx(70));

    const Mm9HirelingRailRect rail = {0, 0, pRail->width, pRail->height};
    const Mm9HirelingRailRect first = railUnits(manager, "Mm9Hireling1");
    const Mm9HirelingRailRect third = railUnits(manager, "Mm9Hireling3");
    // An 8-unit band, 58 units a slot, 2 between: three end at y 372, above the basebar's ornament at 4:3 (377).
    CHECK(first.x == doctest::Approx(8));
    CHECK(first.y == doctest::Approx(8));
    CHECK(first.height == doctest::Approx(58));
    CHECK(railUnits(manager, "Mm9Hireling2").y - first.y == doctest::Approx(60));
    CHECK(pRail->offsetY + OpenYAMM::Game::mm9HirelingRailPanel(rail, first, third).height == doctest::Approx(372));
    CHECK(OpenYAMM::Game::mm9HirelingRailPanel(rail, first, first).height == doctest::Approx(74));
    CHECK(pRail->height == doctest::Approx(OpenYAMM::Game::mm9HirelingRailPanel(rail, first, third).height));

    for (int slot = 1; slot <= 3; ++slot)
    {
        CAPTURE(slot);
        const std::string id = "Mm9Hireling" + std::to_string(slot);
        const Mm9HirelingRailRect face = railUnits(manager, id + "Face");
        const Mm9HirelingRailRect health = railUnits(manager, id + "Health");
        const Mm9HirelingRailRect rim = railUnits(manager, id + "Rim");
        const UiLayoutManager::LayoutElement *pHealth = manager.findElement(id + "Health");
        REQUIRE(pHealth->meterArc);
        // Faces 34 x 46; the party's left HP arc, 4 units out and 3.6 wide; no mana arc.
        CHECK(face.width == doctest::Approx(34));
        CHECK(face.height == doctest::Approx(46));
        CHECK(pHealth->meterArc->strokeWidth == doctest::Approx(3.6));
        CHECK(pHealth->meterArc->startDegrees == doctest::Approx(100));
        CHECK(pHealth->meterArc->sweepDegrees == doctest::Approx(160));
        CHECK(face.x - health.x == doctest::Approx(4));
        CHECK(manager.findElement(id + "Mana") == nullptr);
        // The group is centred: the rail's inner edge to the arc's outer edge equals the rim to the other inner edge.
        const float leftSpace = health.x - pHealth->meterArc->strokeWidth * 0.5f - 8;
        const float rightSpace = 62 - (rim.x + rim.width);
        CHECK(leftSpace == doctest::Approx(rightSpace));
        // Centred on the face as the party's rim and diamond are.
        CHECK(rim.x + rim.width * 0.5f == doctest::Approx(face.x + face.width * 0.5f));
        const Mm9HirelingRailRect diamond = railUnits(manager, id + "Selection");
        CHECK(diamond.x + diamond.width * 0.5f == doctest::Approx(face.x + face.width * 0.5f));
    }
}

TEST_CASE("MM9 hireling rail hit testing finds the live slots only")
{
    const std::vector<Mm9HirelingRailRect> slots = {{10, 20, 54, 58}, {10, 80, 54, 58}};
    CHECK(OpenYAMM::Game::mm9HirelingRailSlotAt(slots, 12, 22) == std::optional<size_t>(0));
    CHECK(OpenYAMM::Game::mm9HirelingRailSlotAt(slots, 63.9f, 137.9f) == std::optional<size_t>(1));
    // The 2-unit gap between the slots and anything past the last live slot take no click.
    CHECK_FALSE(OpenYAMM::Game::mm9HirelingRailSlotAt(slots, 20, 79).has_value());
    CHECK_FALSE(OpenYAMM::Game::mm9HirelingRailSlotAt(slots, 20, 145).has_value());
    CHECK_FALSE(OpenYAMM::Game::mm9HirelingRailSlotAt({}, 20, 30).has_value());
}

TEST_CASE("MM9 hireling inspection names attacks and spells")
{
    const std::vector<std::string> header = {
        "rude_id", "name", "kind", "portrait", "monster_row", "hire_qbit", "hire_fee", "wage", "gold_share_percent",
        "service", "service_cooldown_hours", "cured_conditions", "passive",
        "level", "hp", "ac", "recovery_seconds",
        "attack1_type", "attack1_damage", "attack2_type", "attack2_damage", "attack2_missile",
        "spell1", "spell1_share_percent", "spell2",
        "res_fire", "res_air", "res_water", "res_earth", "res_spirit", "res_mind", "res_body", "res_light", "res_dark",
        "res_physical",
    };
    Mm9HirelingTable table;
    REQUIRE(table.loadFromRows({header,
        {"42", "Hrolf Spearmaster", "paid", "9npc01-01", "279", "90450", "300", "300", "2", "none", "0", "", "",
            "34", "276", "21", "2.310", "Phys", "2d9+17", "Fire", "5d3+10", "Arrow", "", "0", "",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"},
        {"44", "Arienh A'Klindor", "paid", "9npc03-01", "281", "90452", "500", "500", "5", "none", "0", "", "",
            "20", "120", "14", "2.475", "Phys", "2d4-1", "0", "0", "0", "Fireball,E,6", "60", "Toxic Cloud,M,7",
            "20", "20", "20", "20", "20", "20", "20", "20", "20", "0"}}));
    const Mm9Hireling *pArcher = table.find(42);
    const Mm9Hireling *pCaster = table.find(44);
    REQUIRE(pArcher != nullptr);
    REQUIRE(pCaster != nullptr);
    CHECK(OpenYAMM::Game::formatMm9HirelingAttack(pArcher->attack1) == "2d9+17 Physical");
    CHECK(OpenYAMM::Game::formatMm9HirelingAttack(pArcher->attack2) == "5d3+10 Fire, Arrow");
    CHECK(OpenYAMM::Game::formatMm9HirelingAttack(pCaster->attack1) == "2d4-1 Physical");
    CHECK(OpenYAMM::Game::formatMm9HirelingAttack(pCaster->attack2).empty());
    REQUIRE(pCaster->spells.size() == 2);
    CHECK(OpenYAMM::Game::formatMm9HirelingSpell(pCaster->spells[0], "Fire Ball") == "Fire Ball, Expert 6");
    CHECK(OpenYAMM::Game::formatMm9HirelingSpell(pCaster->spells[1], "") == "toxic cloud, Master 7");
}

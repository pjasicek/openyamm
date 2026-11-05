#include "game/items/ItemSearch.h"

#include <doctest/doctest.h>

#include <string>

using namespace OpenYAMM::Game;

namespace
{
bool found(const std::string &query, const std::string &itemText)
{
    return ItemSearch::matches(ItemSearch::parse(query), ItemSearch::toLower(itemText));
}
}

TEST_CASE("item search: every word must appear, | gives alternatives, any case (user, 2026-10-29)")
{
    const std::string ring = "Ring of the Ox  Ring  +12 Might  +8 Endurance";
    CHECK(found("ring might endurance|luck|speed", ring));
    CHECK(found("RING MIGHT", ring));
    CHECK_FALSE(found("ring might luck|speed", ring));
    CHECK_FALSE(found("amulet might", ring));
    CHECK(found("", ring));
    CHECK(ItemSearch::parse("   ").empty());
}

TEST_CASE("item search: ! excludes a word and quotes keep a phrase together")
{
    const std::string sword = "Sword of the Gods  Sword  +10 to all Seven Statistics";
    CHECK(found("!axe sword", sword));
    CHECK_FALSE(found("!sword", sword));
    CHECK(found("\"of the gods\"", sword));
    CHECK_FALSE(found("\"gods of\"", sword));
    CHECK(found("!axe|mace", sword));
    CHECK_FALSE(found("!axe|sword", sword));
    // A lone ! or | is no term at all.
    CHECK(found("! |", sword));
}

TEST_CASE("item search: letters beyond ASCII match in any case")
{
    const std::string sword = "Épée des Dieux  Épée  +10 à toutes les statistiques";
    CHECK(found("ÉPÉE dieux", sword));
    CHECK(found("épée", sword));
    CHECK_FALSE(found("épées", sword));
    CHECK(found("ΘΕΩΝ ξιφος", "Ξιφος των θεων"));
}

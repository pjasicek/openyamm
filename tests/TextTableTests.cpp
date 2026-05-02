#include "engine/TextTable.h"

#include <doctest/doctest.h>

#include <optional>

TEST_CASE("TextTable parses quoted multiline cells and literal quotes inside unquoted cells")
{
    const std::optional<OpenYAMM::Engine::TextTable> table =
        OpenYAMM::Engine::TextTable::parseTabSeparated(
            "#\tTopic\tNotes\n"
            "1\t\"Balthazar of\n"
            "Ravage Roaming\"\t96\n"
            "2\tKorbu\t152. \"Korbu? He was the clue\n");

    REQUIRE(table.has_value());
    REQUIRE(table->getRowCount() == 3);
    CHECK(table->getRow(1).at(1) == "Balthazar of\nRavage Roaming");
    CHECK(table->getRow(2).at(2) == "152. \"Korbu? He was the clue");
}

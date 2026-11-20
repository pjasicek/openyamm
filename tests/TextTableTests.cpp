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

TEST_CASE("TextTable treats a leading quote with no close before the next tab as literal")
{
    const std::optional<OpenYAMM::Engine::TextTable> table =
        OpenYAMM::Engine::TextTable::parseTabSeparated(
            "1\ttext\tLoc\t\"Journal Entry, 2nd Janua\n"
            "2\t\" body\nmore\"\tLoc\tName\n"
            "3\t\"a \"\"b\"\" c\"\tLoc\tName\n");

    REQUIRE(table.has_value());
    REQUIRE(table->getRowCount() == 3);
    CHECK(table->getRow(0).size() == 4);
    CHECK(table->getRow(0).at(3) == "\"Journal Entry, 2nd Janua");
    CHECK(table->getRow(1).at(0) == "2");
    CHECK(table->getRow(1).at(1) == " body\nmore");
    CHECK(table->getRow(1).at(3) == "Name");
    CHECK(table->getRow(2).at(1) == "a \"b\" c");
}

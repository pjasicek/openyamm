#include "doctest/doctest.h"

#include "game/localization/LocalizedTableOverlay.h"

#include <string>
#include <vector>

TEST_CASE("localized table overlay replaces selected cells by canonical row key")
{
    std::vector<std::vector<std::string>> rows = {
        {"#", "Text", "Owner"},
        {"1", "Hello", "Dadeross"},
        {"2", "Goodbye", "Dadeross"}
    };
    const std::string overlay = R"(
rows:
  "1":
    1: "Здравствуйте"
)";
    std::string errorMessage;

    REQUIRE(OpenYAMM::Game::applyLocalizedTableOverlay(overlay, rows, errorMessage));
    CHECK_EQ(rows[1][1], "Здравствуйте");
    CHECK_EQ(rows[1][2], "Dadeross");
    CHECK_EQ(rows[2][1], "Goodbye");
}

TEST_CASE("localized table overlay rejects unknown row keys")
{
    std::vector<std::vector<std::string>> rows = {{"1", "Hello"}};
    const std::string overlay = "rows:\n  \"9\":\n    1: Привет\n";
    std::string errorMessage;

    CHECK_FALSE(OpenYAMM::Game::applyLocalizedTableOverlay(overlay, rows, errorMessage));
    CHECK(errorMessage.find("unknown row key") != std::string::npos);
}

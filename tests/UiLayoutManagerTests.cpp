#include "doctest/doctest.h"

#include "game/ui/UiLayoutManager.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace
{
std::string loadLayoutSource(const std::filesystem::path &relativePath)
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    std::ostringstream text;
    text << input.rdbuf();
    return text.str();
}
}

TEST_CASE("menu settings catalog has complete native layout controls")
{
    const YAML::Node catalog = YAML::Load(loadLayoutSource("assets_dev/engine/ui/menu/settings_catalog.yml"));
    OpenYAMM::Game::UiLayoutManager manager;
    for (const YAML::Node &section : catalog["sections"])
    {
        const std::string path = "assets_dev/engine/ui/gameplay/settings_" + section["id"].as<std::string>() + ".yml";
        REQUIRE(manager.loadLayoutText(path, loadLayoutSource(path)));
    }
    const auto capitalized = [](const std::string &value)
    {
        std::string result;
        bool upper = true;
        for (unsigned char character : value)
        {
            if (character == '_' || character == '-')
            {
                upper = true;
                continue;
            }
            result += upper ? char(std::toupper(character)) : char(character);
            upper = false;
        }
        return result;
    };
    for (const YAML::Node &setting : catalog["settings"])
    {
        const std::string prefix = "Settings" + capitalized(setting["section"].as<std::string>());
        const std::string id = prefix + capitalized(setting["id"].as<std::string>());
        CAPTURE(id);
        for (const char *pSuffix : {"Label", "Description", "Control"})
        {
            CAPTURE(pSuffix);
            const OpenYAMM::Game::UiLayoutManager::LayoutElement *pElement = manager.findElement(id + pSuffix);
            REQUIRE(pElement != nullptr);
            CHECK(pElement->parentId == prefix + "ScrollViewport");
        }
        CHECK(manager.findElement(id + "Control")->interactive);
        if (setting["type"].as<std::string>() == "range")
        {
            CHECK(manager.findElement(id + "Value") != nullptr);
        }
    }
}

TEST_CASE("shared Obsidian gameplay layout preserves command and follower ownership")
{
    OpenYAMM::Game::UiLayoutManager manager;
    REQUIRE(manager.loadLayoutText("gameplay.yml", loadLayoutSource("assets_dev/engine/ui/gameplay/gameplay.yml")));
    for (const char *id : {"OutdoorGoldBar", "OutdoorOptionsBar"})
    {
        const auto *bar = manager.findElement(id);
        REQUIRE(bar != nullptr);
        CHECK(bar->parentId == "OutdoorTopBar");
    }
    for (const char *id : {"OutdoorButtonRest", "OutdoorButtonBooks", "OutdoorButtonQuickReference", "OutdoorButtonOptions"})
    {
        const auto *button = manager.findElement(id);
        REQUIRE(button != nullptr);
        CHECK(button->parentId == "OutdoorOptionsBar");
        CHECK(button->interactive);
    }
    const auto *portrait = manager.findElement("OutdoorFollowerPortrait_1");
    REQUIRE(portrait != nullptr);
    CHECK(portrait->parentId == "OutdoorFollowerPanel");
    const auto *followerPanel = manager.findElement("OutdoorFollowerPanel");
    REQUIRE(followerPanel != nullptr);
    CHECK(followerPanel->visible); // Open/closed state is controlled by the live HUD classification.
    const auto *followerToggle = manager.findElement("OutdoorFollowerToggle");
    REQUIRE(followerToggle != nullptr);
    CHECK(followerToggle->interactive);
    CHECK_FALSE(followerToggle->selectedAsset.empty());
    CHECK(manager.findElement("ObsidianFollowersLabel") == nullptr);
    CHECK(manager.findElement("ObsidianFollowersPlate") == nullptr);
    const auto *clock = manager.findElement("ObsidianMinimapClock");
    REQUIRE(clock != nullptr);
    CHECK(clock->parentId == "OutdoorMinimapFrame");
    for (const char *id : {"OutdoorFlyBuffIcon", "OutdoorWaterWalkBuffIcon"})
    {
        const auto *movement = manager.findElement(id);
        REQUIRE(movement != nullptr);
        CHECK(movement->parentId.empty());
        CHECK_FALSE(movement->primaryAsset.empty());
    }
    for (const char *id : {"OutdoorFollowerScrollUp", "OutdoorFollowerScrollDown"})
    {
        const auto *scroll = manager.findElement(id);
        REQUIRE(scroll != nullptr);
        CHECK(scroll->interactive);
        CHECK_FALSE(scroll->disabledAsset.empty());
        CHECK(scroll->primaryAsset != scroll->disabledAsset);
    }
    const auto ids = manager.sortedLayoutIdsForScreen("OutdoorHud");
    CHECK(std::find(ids.begin(), ids.end(), "OutdoorFollowerPanel")
        < std::find(ids.begin(), ids.end(), "OutdoorFollowerPortrait_1"));
    CHECK(manager.findElement("OutdoorStandardBasebar") == nullptr);
}

TEST_CASE("Obsidian layouts retain inventory geometry and distinct selected and disabled button assets")
{
    OpenYAMM::Game::UiLayoutManager manager;
    REQUIRE(manager.loadLayoutText("character.yml", loadLayoutSource("assets_dev/engine/ui/gameplay/character.yml")));
    const auto *grid = manager.findElement("CharacterInventoryGrid");
    REQUIRE(grid != nullptr);
    CHECK(grid->width == 14 * 32);
    CHECK(grid->height == 9 * 32);
    CHECK(grid->gapX == 7);
    CHECK(grid->gapY == 8);
    REQUIRE(manager.loadLayoutText("journal.yml", loadLayoutSource("assets_dev/engine/ui/gameplay/journal.yml")));
    const auto *button = manager.findElement("JournalNextPageButton");
    REQUIRE(button != nullptr);
    CHECK(button->selectedAsset == "obsidian_journal_page_selected");
    CHECK(button->disabledAsset == "obsidian_journal_page_disabled");
    CHECK(button->selectedAsset != button->pressedAsset);
    const auto *map = manager.findElement("JournalMapViewport");
    REQUIRE(map != nullptr);
    CHECK(map->width == 300);
    CHECK(map->height == 300);
    CHECK(map->gapX == 131);
    CHECK(map->gapY == 101);
}

TEST_CASE("Obsidian split arcs and indicators stay inside the bottom anchored party frame")
{
    using OpenYAMM::Game::UiLayoutManager;
    UiLayoutManager manager;
    REQUIRE(manager.loadLayoutText("gameplay.yml", loadLayoutSource("assets_dev/engine/ui/gameplay/gameplay.yml")));
    const auto *base = manager.findElement("OutdoorGameplayBasebar");
    REQUIRE(base != nullptr);
    CHECK(base->anchor == UiLayoutManager::LayoutAnchor::BottomCenter);
    CHECK(base->anchorSpace == UiLayoutManager::LayoutAnchorSpace::Screen);
    CHECK(base->offsetY == 0);
    const float border = 8.533333f * 0.75f;
    const float corner = 30.933333f * 0.75f;
    for (int count = 1; count <= 5; ++count)
    {
        const float width = base->width - (5 - count) * 80;
        for (int i = 1; i <= count; ++i)
        {
            const std::string id = "ObsidianPc" + std::to_string(i);
            const auto *slot = manager.findElement(id);
            REQUIRE(slot != nullptr);
            for (const char *suffix : {"Face", "Rim", "Selection", "Health", "Mana", "Readiness", "PersonalBuffs"})
            {
                const auto *element = manager.findElement(id + suffix);
                REQUIRE(element != nullptr);
                float x = slot->gapX + element->gapX;
                float y = slot->gapY + element->gapY;
                float w = element->width;
                float h = element->height;
                if (element->meterArc)
                {
                    const float stroke = element->meterArc->strokeWidth + 1.7f;
                    x -= stroke * 0.5f;
                    y -= stroke * 0.5f;
                    w += stroke;
                    h += stroke;
                }
                if (std::string(suffix) == "Readiness")
                {
                    // Include the larger aggro image, not just its layout/hit rectangle.
                    const float unit = element->width / 22;
                    x -= 8 * unit;
                    y -= 8 * unit;
                    w = 38 * unit;
                    h = 41 * unit;
                }
                CAPTURE(count);
                CAPTURE(id);
                CAPTURE(suffix);
                CHECK(x >= border);
                CHECK(y >= border);
                CHECK(x + w <= width - border);
                CHECK(y + h <= base->height - border);
                CHECK(((y >= corner && y + h <= base->height - corner)
                    || (x >= corner && x + w <= width - corner)));
            }
            const auto *health = manager.findElement(id + "Health");
            const auto *mana = manager.findElement(id + "Mana");
            REQUIRE(health->meterArc);
            REQUIRE(mana->meterArc);
            CHECK(health->meterArc->sweepDegrees > 0);
            CHECK(mana->meterArc->sweepDegrees < 0);
        }
    }
    CHECK(manager.findElement("ObsidianOverlayPc1Health")->meterArc);
    CHECK(manager.findElement("ObsidianOverlayPc1Mana")->meterArc);
}

TEST_CASE("Obsidian layout rejects invalid arc geometry")
{
    const std::string prefix = "screen: OutdoorHud\nelements:\n- id: Arc\n  anchor: top_left\n"
        "  width: 60\n  height: 80\n  meter_arc: ";
    for (const char *arc : {"broken", "{sweep_degrees: 0, stroke_width: 4}",
        "{sweep_degrees: 361, stroke_width: 4}", "{sweep_degrees: 160, stroke_width: -1}",
        "{sweep_degrees: 160, stroke_width: 60}", "{start_degrees: .nan, sweep_degrees: 160, stroke_width: 4}"})
    {
        OpenYAMM::Game::UiLayoutManager manager;
        CHECK_FALSE(manager.loadLayoutText("invalid.yml", prefix + arc));
    }
}

TEST_CASE("character doll boots render above armor")
{
    const std::string characterLayout = loadLayoutSource("assets_dev/engine/ui/gameplay/character.yml");
    REQUIRE_FALSE(characterLayout.empty());

    OpenYAMM::Game::UiLayoutManager layoutManager;
    REQUIRE(layoutManager.loadLayoutText("character.yml", characterLayout));

    const OpenYAMM::Game::UiLayoutManager::LayoutElement *pArmor =
        layoutManager.findElement("CharacterDollArmorSlot");
    const OpenYAMM::Game::UiLayoutManager::LayoutElement *pBoots =
        layoutManager.findElement("CharacterDollBootsSlot");
    REQUIRE(pArmor != nullptr);
    REQUIRE(pBoots != nullptr);
    CHECK_GT(pBoots->zIndex, pArmor->zIndex);

    const std::vector<std::string> layoutIds = layoutManager.sortedLayoutIdsForScreen("Character");
    const std::vector<std::string>::const_iterator armorIterator =
        std::find(layoutIds.begin(), layoutIds.end(), "CharacterDollArmorSlot");
    const std::vector<std::string>::const_iterator bootsIterator =
        std::find(layoutIds.begin(), layoutIds.end(), "CharacterDollBootsSlot");
    REQUIRE(armorIterator != layoutIds.end());
    REQUIRE(bootsIterator != layoutIds.end());
    CHECK(armorIterator < bootsIterator);
}

TEST_CASE("character inspect layout provides a skill bonus row")
{
    const std::string inspectLayout = loadLayoutSource("assets_dev/engine/ui/gameplay/character_inspect.yml");
    REQUIRE_FALSE(inspectLayout.empty());

    OpenYAMM::Game::UiLayoutManager layoutManager;
    REQUIRE(layoutManager.loadLayoutText("character_inspect.yml", inspectLayout));

    const OpenYAMM::Game::UiLayoutManager::LayoutElement *pSkillBonus =
        layoutManager.findElement("CharacterInspectSkillBonus");
    REQUIRE(pSkillBonus != nullptr);
    CHECK_EQ(pSkillBonus->parentId, "CharacterInspectRoot");
    CHECK_EQ(pSkillBonus->fontName, "SMALLNUM");
}

#include "engine/AssetFileSystem.h"
#include "engine/ImageAssetLoader.h"
#include "game/data/GameDataLoader.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayHudCommon.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <filesystem>
#include <cmath>

TEST_CASE("HUD label retains the final Cyrillic glyph after content width rounding")
{
    using namespace OpenYAMM::Game;
    GameplayHudFontData font;
    const std::string label = "Дерево";
    const std::array<uint32_t, 5> codePoints = {0x414, 0x435, 0x440, 0x432, 0x43e};
    for (size_t i = 0; i < codePoints.size(); ++i)
    {
        font.glyphsByCodePoint[codePoints[i]] = uint16_t(i + 1);
        font.glyphMetrics[i + 1].outlineAdvance = 7.3f;
    }
    const float width = GameplayHudCommon::measureHudTextWidth(font, label);
    const float roundedDown = std::nextafter(width, 0.0f);
    CHECK(GameplayHudCommon::clampHudTextToWidth(font, label, roundedDown) == label);
    for (int viewportWidth : {640, 853, 1024, 1280, 1366, 1920, 2560, 3840})
    {
        const float uiScale = viewportWidth / 640.0f;
        const float textScale = uiScale * 0.75f;
        const float plateWidth = width * textScale + 16 * uiScale;
        const float availableWidth = (plateWidth - 16 * uiScale) / textScale;
        CHECK(GameplayHudCommon::clampHudTextToWidth(font, label, availableWidth) == label);
    }
    CHECK(GameplayHudCommon::clampHudTextToWidth(font, label, width - 1.0f) == "Дерев");
    CHECK(GameplayHudCommon::clampHudTextToWidth(font, label, 0).empty());
}

TEST_CASE("HUD font snapping preserves fitted labels at fractional viewport scales")
{
    using namespace OpenYAMM;
    using namespace OpenYAMM::Game;
    GameplayHudFontData font;
    font.fontHeight = 17;
    font.glyphsByCodePoint[0x44f] = 1;
    font.glyphMetrics[1].outlineAdvance = 10.0f;
    const std::string label = "яяяяяяяяяя";
    UiLayoutManager::LayoutElement layout = {};
    layout.textScale = 1.0f;
    GameplayResolvedHudLayoutElement resolved = {};
    resolved.scale = 1.95f;
    resolved.height = 36.0f;

    for (float availableWidth : {196.0f, 201.0f})
    {
        resolved.width = availableWidth;
        size_t renderedLayers = 0;
        GameplayHudCommon::renderLayoutLabel(
            layout,
            resolved,
            label,
            [&font](const std::string &) { return &font; },
            [&](const GameplayHudFontData &, const GameplayHudFontLayer &, const std::string &text,
                float, float, float scale)
            {
                CHECK(text == label);
                CHECK(scale == doctest::Approx(availableWidth < 200.0f ? 1.95f : 2.0f));
                CHECK(GameplayHudCommon::measureHudTextWidth(font, text) * scale <= availableWidth);
                ++renderedLayers;
            });
        CHECK(renderedLayers == 2);
    }
}

TEST_CASE("dimensional travel uses original artwork and matching continent hover regions")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    Game::GameDataRepository data;
    data.bind(loader);
    Game::GameplayUiRuntime ui;
    ui.bindDataRepository(&data);
    CHECK_FALSE(ui.ensureDimensionDoorDestinationsLoaded(1, false));
    REQUIRE(ui.ensureDimensionDoorDestinationsLoaded(1, true));
    REQUIRE_EQ(ui.townPortalDestinations().size(), 3);

    Engine::BinaryAssetCache images;
    const std::optional<Engine::ImagePixelsBgra> background =
        Engine::loadImageAssetPixelsBgra(assets, ui.townPortalBackgroundTextureName() + ".bmp", images);
    REQUIRE(background.has_value());
    CHECK_EQ(background->width, 640);
    CHECK_EQ(background->height, 480);
    CHECK(background->assetScaleTier == Engine::AssetScaleTier::X1);

    struct ExpectedDestination
    {
        const char *pLabel;
        const char *pMapName;
        int32_t hitX;
        uint32_t hitWidth;
        int iconWidth;
        int iconHeight;
    };
    const std::array<ExpectedDestination, 3> expected = {{
        {"Jadame", "out01.odm", 0, 213, 450, 360},
        {"Enroth", "oute3.odm", 213, 214, 270, 400},
        {"Antagarich", "7out01.odm", 427, 213, 460, 360},
    }};
    for (const ExpectedDestination &entry : expected)
    {
        const auto destination = std::find_if(ui.townPortalDestinations().begin(), ui.townPortalDestinations().end(),
            [&entry](const Game::GameplayTownPortalDestination &candidate) { return candidate.label == entry.pLabel; });
        REQUIRE(destination != ui.townPortalDestinations().end());
        CHECK_EQ(destination->mapName, entry.pMapName);
        CHECK_EQ(destination->hitX, entry.hitX);
        CHECK_EQ(destination->hitWidth, entry.hitWidth);
        CHECK_EQ(destination->hitY, 0);
        CHECK_EQ(destination->hitHeight, 480);
        const std::optional<Engine::ImagePixelsBgra> icon =
            Engine::loadImageAssetPixelsBgra(assets, destination->iconTextureName + ".bmp", images);
        REQUIRE(icon.has_value());
        CHECK_EQ(icon->width, entry.iconWidth);
        CHECK_EQ(icon->height, entry.iconHeight);
        CHECK(icon->assetScaleTier == Engine::AssetScaleTier::X1);
    }
}

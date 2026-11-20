#include "engine/AssetFileSystem.h"
#include "engine/FontAsset.h"
#include "game/ui/UiLayoutManager.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>

namespace
{
using namespace OpenYAMM;

struct FontFixture
{
    std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("openyamm_font_" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    Engine::AssetFileSystem assets;

    FontFixture()
    {
        const std::filesystem::path source = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/fonts";
        std::filesystem::create_directories(root / "engine/fonts/truetype");
        std::filesystem::copy_file(source / "english_text/Arrus.fnt", root / "engine/fonts/arrus.fnt");
        std::filesystem::copy_file(source / "english_text/create.fnt", root / "engine/fonts/create.fnt");
        std::filesystem::copy_file(source / "english_text/Lucida.fnt", root / "engine/fonts/lucida.fnt");
        std::filesystem::copy_file(source / "english_text/SMALLNUM.fnt", root / "engine/fonts/smallnum.fnt");
        std::filesystem::copy_file(source / "english_text/COMIC.FNT", root / "engine/fonts/comic.fnt");
        std::filesystem::copy_file(source / "english_text/Book2.FNT", root / "engine/fonts/book2.fnt");
        std::filesystem::copy_file(source / "english_text/AUTONOTE.FNT", root / "engine/fonts/autonote.fnt");
        std::filesystem::copy_file(source / "english_text/ENDGAME.FNT", root / "engine/fonts/endgame.fnt");
        std::filesystem::copy_file(source / "english_text/SPELL.FNT", root / "engine/fonts/spell.fnt");
        for (const char *pFile : {"arrus.yml", "openyamm_arrus_faithful.ttf",
            "create.yml", "openyamm_create_faithful.ttf", "lucida.yml", "openyamm_lucida_faithful.ttf",
            "smallnum.yml", "openyamm_smallnum_faithful.ttf", "comic.yml", "openyamm_comic_faithful.ttf",
            "book2.yml", "openyamm_book2_faithful.ttf", "autonote.yml", "openyamm_autonote_faithful.ttf",
            "endgame.yml", "openyamm_endgame_faithful.ttf", "spell.yml", "openyamm_spell_faithful.ttf",
            "fondamento.yml", "fondamento_regular.ttf", "menu_arrus.yml", "menu_lucida.yml",
            "alegreya_semibold.yml", "alegreya_variable.ttf"})
        {
            std::filesystem::copy_file(source / "truetype" / pFile, root / "engine/fonts/truetype" / pFile);
        }
        REQUIRE(assets.initialize(root, root, Engine::AssetScaleTier::X1));
    }

    ~FontFixture()
    {
        assets.shutdown();
        std::filesystem::remove_all(root);
    }
};

int textWidth(const std::array<Engine::FontGlyphMetrics, 256> &metrics, const std::string &text)
{
    int width = 0;
    for (unsigned char character : text)
    {
        width += metrics[character].leftSpacing + metrics[character].width + metrics[character].rightSpacing;
    }
    return width;
}

int32_t fntInt32(const std::vector<uint8_t> &bytes, size_t offset)
{
    return int32_t(uint32_t(bytes[offset]) | (uint32_t(bytes[offset + 1]) << 8) | (uint32_t(bytes[offset + 2]) << 16)
        | (uint32_t(bytes[offset + 3]) << 24));
}

// The layout metrics an original MM7 FNT stores: 32-byte header, then left spacing, width and right spacing per byte.
std::array<Engine::FontGlyphMetrics, 256> fntGlyphMetrics(const std::vector<uint8_t> &bytes)
{
    std::array<Engine::FontGlyphMetrics, 256> metrics = {};
    for (size_t character = 0; character < metrics.size(); ++character)
    {
        metrics[character].leftSpacing = fntInt32(bytes, 32 + character * 12);
        metrics[character].width = fntInt32(bytes, 32 + character * 12 + 4);
        metrics[character].rightSpacing = fntInt32(bytes, 32 + character * 12 + 8);
    }
    return metrics;
}
}

TEST_CASE("menu outline fonts load independently of legacy metrics")
{
    FontFixture fixture;
    std::string error;
    for (const char *pName : {"fondamento", "menu_arrus", "menu_lucida", "alegreya_semibold"})
    {
        const auto image = Engine::loadTrueTypeFontAtlas(fixture.assets, pName, error);
        INFO(error);
        REQUIRE(image);
        CHECK(image->atlas.atlasScale == 1);
        CHECK(image->atlas.glyphMetrics['W'].advance() > image->atlas.glyphMetrics['i'].advance());
        CHECK(image->atlas.glyphMetrics[' '].advance() > 0);
        bool fractionalAdvance = false;
        for (const Engine::FontGlyphMetrics &metrics : image->atlas.glyphMetrics)
        {
            fractionalAdvance = fractionalAdvance || metrics.advance() != std::floor(metrics.advance());
        }
        if (std::string(pName) == "fondamento")
        {
            CHECK(fractionalAdvance);
        }
        CHECK(textWidth(image->atlas.glyphMetrics, "WWW") > textWidth(image->atlas.glyphMetrics, "iii"));
        CHECK(textWidth(image->atlas.glyphMetrics, "Begin Adventure") > 0);
        bool ink = false;
        for (size_t i = 3; i < image->atlas.mainAtlasPixels.size(); i += 4)
            ink = ink || image->atlas.mainAtlasPixels[i] != 0;
        CHECK(ink);
    }
    CHECK_FALSE(Engine::loadTrueTypeFontAtlas(fixture.assets, "../fondamento", error));
    CHECK_FALSE(Engine::loadTrueTypeFontAtlas(fixture.assets, "arrus", error));
}

TEST_CASE("menu outline font atlas rasterizes at display size with antialiased "
          "ink and one shadow mask")
{
    FontFixture fixture;
    std::string error;
    for (const char *pName : {"fondamento", "menu_arrus", "menu_lucida", "alegreya_semibold"})
    {
        for (int pixelHeight : {11, 13, 17, 21, 26, 64, 128})
        {
            CAPTURE(pName);
            CAPTURE(pixelHeight);
            const auto image = Engine::loadTrueTypeFontAtlas(fixture.assets, pName, error, pixelHeight);
            REQUIRE_MESSAGE(image, error);
            const Engine::FontAtlas &font = image->atlas;
            CHECK(font.fontHeight == pixelHeight);
            CHECK(font.atlasScale == 1);
            const int cellWidth = font.atlasCellWidth + 2 * font.atlasPadding;
            const int cellHeight = font.fontHeight + 2 * font.atlasPadding;
            for (unsigned char character : std::string("Wil\xc9\xe9"))
            {
                CAPTURE(character);
                const int cellX = character % 16 * cellWidth;
                const int cellY = character / 16 * cellHeight;
                size_t ink = 0;
                size_t antialiased = 0;
                bool sameShadow = true;
                bool whiteInk = true;
                bool contained = true;
                for (int y = 0; y < cellHeight; ++y)
                {
                    for (int x = 0; x < cellWidth; ++x)
                    {
                        const size_t offset = (size_t(cellY + y) * font.atlasWidth + cellX + x) * 4;
                        const uint8_t alpha = font.mainAtlasPixels[offset + 3];
                        ink += alpha > 0;
                        antialiased += alpha > 0 && alpha < 255;
                        sameShadow &= image->shadowPixels[offset + 3] == alpha;
                        whiteInk &= font.mainAtlasPixels[offset] == 255 && font.mainAtlasPixels[offset + 1] == 255 &&
                                    font.mainAtlasPixels[offset + 2] == 255;
                        if (alpha > 0)
                        {
                            contained &= x > 0 && x < font.glyphMetrics[character].width + 2 * font.atlasPadding - 1 &&
                                         y > 0 && y < cellHeight - 1;
                        }
                    }
                }
                CHECK(ink > 0);
                // Pixel-aligned faithful strokes can be fully opaque at their original
                // sizes.
                if (std::string(pName) == "fondamento")
                {
                    CHECK(antialiased > 0);
                }
                CHECK(sameShadow);
                CHECK(whiteInk);
                CHECK(contained);
            }
        }
    }
    CHECK_FALSE(Engine::loadTrueTypeFontAtlas(fixture.assets, "fondamento", error, -1));
    CHECK_FALSE(Engine::loadTrueTypeFontAtlas(fixture.assets, "fondamento", error, 513));
}

TEST_CASE("enemy label font loads its authored semibold weight and rejects invalid weights")
{
    FontFixture fixture;
    std::string error;
    const std::optional<Engine::FontAtlasImage> semibold =
        Engine::loadTrueTypeFontAtlas(fixture.assets, "alegreya_semibold", error);
    REQUIRE_MESSAGE(semibold, error);
    CHECK(semibold->atlas.fontHeight == 24);
    CHECK(textWidth(semibold->atlas.glyphMetrics, "Guardian of VARN 617/617") * 0.42f < 144.0f);
    CHECK(semibold->atlas.mainAtlasPixels.size() < 2 * 1024 * 1024);

    const auto writeWeight = [&](int weight)
    {
        std::ofstream descriptor(fixture.root / "engine/fonts/truetype/alegreya_semibold.yml");
        descriptor << "file: alegreya_variable.ttf\nmetrics: freetype\nlogical_height: 24\nbaseline: 18\n"
                   << "encoding: windows-1252\nweight: " << weight << '\n';
    };
    writeWeight(400);
    const std::optional<Engine::FontAtlasImage> regular =
        Engine::loadTrueTypeFontAtlas(fixture.assets, "alegreya_semibold", error);
    REQUIRE_MESSAGE(regular, error);
    const auto ink = [](const Engine::FontAtlas &font)
    {
        uint64_t sum = 0;
        for (size_t offset = 3; offset < font.mainAtlasPixels.size(); offset += 4)
        {
            sum += font.mainAtlasPixels[offset];
        }
        return sum;
    };
    CHECK(ink(semibold->atlas) > ink(regular->atlas));

    writeWeight(999);
    CHECK_FALSE(Engine::loadTrueTypeFontAtlas(fixture.assets, "alegreya_semibold", error));
    CHECK(error.find("weight") != std::string::npos);
    writeWeight(0);
    CHECK_FALSE(Engine::loadTrueTypeFontAtlas(fixture.assets, "alegreya_semibold", error));
}

TEST_CASE("menu headings fit their layout at the intended font size across display scales")
{
    FontFixture fixture;
    Game::UiLayoutManager layouts;
    for (const char *pLayout : {"settings_gameplay", "settings_interface", "settings_video", "settings_audio",
                               "settings_controls", "settings_keyboard", "continent_selection", "character_creation",
                               "load_game", "save_game"})
    {
        const std::filesystem::path path = std::filesystem::path(OPENYAMM_SOURCE_DIR) /
                                           "assets_dev/engine/ui/gameplay" / (std::string(pLayout) + ".yml");
        std::ifstream input(path);
        REQUIRE(input.good());
        const std::string text((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
        REQUIRE(layouts.loadLayoutText(path.string(), text));
    }
    std::string error;
    const auto baseFont = Engine::loadTrueTypeFontAtlas(fixture.assets, "fondamento", error);
    REQUIRE_MESSAGE(baseFont, error);
    size_t checkedHeadings = 0;
    for (float scale : {0.9375f, 1.5f, 1.83f, 1.875f, 2.25f})
    {
        std::unordered_map<int, Engine::FontAtlas> sizedFonts;
        for (const auto &[key, element] : layouts.elements())
        {
            const std::string &id = element.id;
            const bool heading = id.ends_with("Title") || id.ends_with("Heading") || id.ends_with("Name") ||
                                 id.ends_with("Section0") || id.ends_with("Section1") || id.ends_with("ConfirmButton");
            if (!heading || element.fontName != "fondamento")
            {
                continue;
            }
            ++checkedHeadings;
            CAPTURE(id);
            CAPTURE(scale);
            const int pixelHeight = int(std::lround(baseFont->atlas.fontHeight * element.textScale * scale));
            if (!sizedFonts.contains(pixelHeight))
            {
                auto image = Engine::loadTrueTypeFontAtlas(fixture.assets, "fondamento", error, pixelHeight);
                REQUIRE_MESSAGE(image, error);
                sizedFonts.emplace(pixelHeight, std::move(image->atlas));
            }
            const Engine::FontAtlas &font = sizedFonts.at(pixelHeight);
            float width = 0;
            uint8_t previous = 0;
            for (unsigned char character : element.labelText)
            {
                width += font.glyphMetrics[character].advance() + font.kerning(previous, character);
                previous = character;
            }
            CHECK(width <= (element.width - 2 * element.textPadX) * scale + 0.5f);
        }
    }
    CHECK(checkedHeadings > 100);
}

TEST_CASE("font atlas TTF preserves native layout and rasterizes all CP1252 cells without clipping")
{
    const char *pName = "Arrus";
    const char *pPath = "fonts/arrus.fnt";
    int height = 19;
    SUBCASE("Arrus")
    {
    }
    SUBCASE("Create")
    {
        pName = "Create";
        pPath = "fonts/create.fnt";
        height = 18;
    }
    SUBCASE("Lucida")
    {
        pName = "Lucida";
        pPath = "fonts/lucida.fnt";
        height = 17;
    }
    SUBCASE("SMALLNUM")
    {
        pName = "SMALLNUM";
        pPath = "fonts/smallnum.fnt";
        height = 14;
    }
    SUBCASE("Comic")
    {
        pName = "Comic";
        pPath = "fonts/comic.fnt";
        height = 19;
    }
    SUBCASE("Book2")
    {
        pName = "Book2";
        pPath = "fonts/book2.fnt";
        height = 30;
    }
    SUBCASE("AUTONOTE")
    {
        pName = "AUTONOTE";
        pPath = "fonts/autonote.fnt";
        height = 18;
    }
    SUBCASE("ENDGAME")
    {
        pName = "ENDGAME";
        pPath = "fonts/endgame.fnt";
        height = 20;
    }
    SUBCASE("SPELL")
    {
        pName = "SPELL";
        pPath = "fonts/spell.fnt";
        height = 16;
    }
    FontFixture fixture;
    const std::optional<std::vector<uint8_t>> bytes = fixture.assets.readBinaryFile(pPath);
    REQUIRE(bytes);
    const std::array<Engine::FontGlyphMetrics, 256> native = fntGlyphMetrics(*bytes);
    int cellWidth = 1;
    for (int character = (*bytes)[0]; character <= (*bytes)[1]; ++character)
    {
        cellWidth = std::max(cellWidth, native[character].width);
    }
    std::string error;
    const std::optional<Engine::FontAtlasImage> ttf = Engine::loadFontAtlas(fixture.assets, *bytes, pName, error);
    REQUIRE_MESSAGE(ttf, error);
    CHECK(ttf->atlas.fontHeight == height);
    CHECK(ttf->atlas.atlasScale == 4);
    CHECK(ttf->atlas.atlasWidth == (cellWidth + 10) * 16 * 4);
    CHECK(ttf->atlas.atlasHeight == (height + 10) * 16 * 4);
    CHECK(ttf->atlas.firstChar == (*bytes)[0]);
    CHECK(ttf->atlas.lastChar == (*bytes)[1]);
    for (int character = 0; character < 256; ++character)
    {
        const Engine::FontGlyphMetrics &replacement = ttf->atlas.glyphMetrics[character];
        CHECK(native[character].leftSpacing == replacement.leftSpacing);
        CHECK(native[character].width == replacement.width);
        CHECK(native[character].rightSpacing == replacement.rightSpacing);
    }
    for (const std::string &text : {"Welcome to New Sorpigal, traveller!", "Illusion, magic & adventure.",
        "A very long conversation about goblins and dragons.", "\x93\xc9lise\x94 \x97 \x80"})
    {
        CHECK(textWidth(ttf->atlas.glyphMetrics, text) == textWidth(native, text));
    }
    const bool noteFace = std::string(pName) == "AUTONOTE";
    size_t partialAlphaCount = 0;
    size_t mainInkCount = 0;
    size_t shadowCount = 0;
    for (size_t offset = 3; offset < ttf->atlas.mainAtlasPixels.size(); offset += 4)
    {
        const uint8_t alpha = ttf->atlas.mainAtlasPixels[offset];
        partialAlphaCount += alpha > 0 && alpha < 255;
        mainInkCount += ttf->atlas.mainAtlasPixels[offset] > 0;
        shadowCount += ttf->shadowPixels[offset] > 0;
    }
    CHECK(partialAlphaCount > 1000);
    if (std::string(pName) == "ENDGAME" || std::string(pName) == "SPELL")
    {
        CHECK(shadowCount == 0);
        CHECK(mainInkCount > 1000);
    }
    else
    {
        CHECK(shadowCount > 1000);
    }
    if (noteFace)
    {
        CHECK(mainInkCount > 1000);
        // Obsidian uses tintable ivory ink; the restored l retains its native stroke and has no shifted shadow.
        const int cellX = (108 % 16) * (ttf->atlas.atlasCellWidth + 10) * 4;
        const int cellY = (108 / 16) * (height + 10) * 4;
        bool coverageMatches = true;
        for (int y = 0; y < (height + 10) * 4; ++y)
        {
            for (int x = 0; x < 44; ++x)
            {
                const size_t offset = (size_t(cellY + y) * ttf->atlas.atlasWidth + cellX + x) * 4;
                const bool ink = x >= 20 && x < 24 && y >= 32 && y < 80;
                coverageMatches &= ttf->atlas.mainAtlasPixels[offset + 3] == (ink ? 255 : 0);
                coverageMatches &= ttf->shadowPixels[offset + 3] == 0;
                coverageMatches &= ttf->shadowPixels[offset] == 0
                    && ttf->shadowPixels[offset + 1] == 0 && ttf->shadowPixels[offset + 2] == 0;
            }
        }
        CHECK(coverageMatches);
    }
}

TEST_CASE("legacy font atlas requires its TTF replacement and reports broken descriptors")
{
    FontFixture fixture;
    const std::optional<std::vector<uint8_t>> bytes = fixture.assets.readBinaryFile("fonts/arrus.fnt");
    REQUIRE(bytes);
    std::string error;
    const std::optional<Engine::FontAtlasImage> arrus = Engine::loadFontAtlas(fixture.assets, *bytes, "Arrus", error);
    REQUIRE_MESSAGE(arrus, error);
    CHECK(arrus->atlas.atlasScale == 4);

    CHECK_FALSE(Engine::loadFontAtlas(fixture.assets, *bytes, "Legal", error));
    CHECK(error.find("missing TTF descriptor") != std::string::npos);
    std::ofstream(fixture.root / "engine/fonts/truetype/arrus.yml")
        << "file: openyamm_arrus_faithful.ttf\nlogical_height: 19\nbaseline: 14\n"
        << "encoding: windows-1252\npresentation: unknown\n";
    CHECK_FALSE(Engine::loadFontAtlas(fixture.assets, *bytes, "Arrus", error));
    CHECK(error.find("unsupported TTF presentation") != std::string::npos);
    std::ofstream(fixture.root / "engine/fonts/truetype/arrus.yml") << "file: bad.ttf\n";
    CHECK_FALSE(Engine::loadFontAtlas(fixture.assets, *bytes, "Arrus", error));
    CHECK(error.find("invalid TTF descriptor") != std::string::npos);
    CHECK_FALSE(Engine::loadFontAtlas(fixture.assets, {0, 1, 2}, "Arrus", error));
    CHECK(error == "invalid legacy FNT");
}

TEST_CASE("UTF-8 text converts to the CP1252 bytes of the legacy faces without the platform's iconv")
{
    // The MAW Rules panel: times, en dash, em dash and middle dot.
    CHECK(Engine::utf8ToCp1252("\xC3\x97" "0.50") == "\xD7" "0.50");
    CHECK(Engine::utf8ToCp1252("1\xE2\x80\x93" "3") == "1\x96" "3");
    CHECK(Engine::utf8ToCp1252("\xE2\x80\x94") == "\x97");
    CHECK(Engine::utf8ToCp1252("once \xC2\xB7 fixed") == "once \xB7 fixed");
    CHECK(Engine::utf8ToCp1252("engine\xE2\x80\x99s \xE2\x82\xAC") == "engine\x92s \x80");
    CHECK(Engine::utf8ToCp1252("plain") == "plain");
    // CP1252 has no arrow; a name imported as CP1252 is not valid UTF-8 and stays as it is.
    CHECK(Engine::utf8ToCp1252("a \xE2\x86\x92 b") == "a ? b");
    CHECK(Engine::utf8ToCp1252("Caf\xE9") == "Caf\xE9");
}

TEST_CASE("a Unicode face packs the characters it lists and draws a character it lacks as '?'")
{
    FontFixture fixture;
    const std::filesystem::path truetype = fixture.root / "engine/fonts/truetype";
    {
        std::ofstream descriptor(truetype / "unicode_test.yml");
        descriptor << "file: alegreya_variable.ttf\nmetrics: freetype\nlogical_height: 24\nbaseline: 18\n"
                   << "encoding: utf-8\ncharacters_file: unicode_test.txt\n";
        // Cyrillic and Greek letters Alegreya has, and a Han character it lacks.
        std::ofstream characters(truetype / "unicode_test.txt");
        characters << "\xd0\x96\xd0\xb6\xce\xa9\xe4\xb8\xad\n";
    }

    std::string error;
    const std::optional<Engine::FontAtlasImage> logical =
        Engine::loadTrueTypeFontAtlas(fixture.assets, "unicode_test", error);
    REQUIRE_MESSAGE(logical.has_value(), error);
    const Engine::FontAtlas &atlas = logical->atlas;
    CHECK(atlas.unicode);
    // At its logical height a face is magnified on screen: it rasters at three times that, capped at 48.
    CHECK_EQ(atlas.fontHeight, 24);
    CHECK_EQ(atlas.rasterHeight, 48);
    CHECK_EQ(atlas.layoutScale, doctest::Approx(0.5f));

    const int zhe = atlas.glyphIndex(0x416);
    const int omega = atlas.glyphIndex(0x3a9);
    const int euro = atlas.glyphIndex(0x20ac);
    REQUIRE(zhe >= 0);
    REQUIRE(omega >= 0);
    REQUIRE(euro >= 0);
    CHECK_EQ(atlas.glyphIndex(0x4e2d), atlas.glyphIndex('?'));
    CHECK(atlas.glyph(zhe).width > 0);
    CHECK(atlas.glyph(zhe).advance() > atlas.glyph(atlas.glyphIndex('.')).advance());

    // Every place lies inside the atlas and overlaps no other.
    const size_t count = atlas.unicodeGlyphPlacements.size();
    REQUIRE_EQ(count, atlas.unicodeGlyphMetrics.size());
    for (size_t index = 0; index < count; ++index)
    {
        const Engine::FontGlyphPlacement &place = atlas.unicodeGlyphPlacements[index];
        CHECK(place.x >= 0);
        CHECK(place.y >= 0);
        CHECK(place.x + place.width <= atlas.atlasWidth);
        CHECK(place.y + place.height <= atlas.atlasHeight);
        for (size_t other = index + 1; other < count; ++other)
        {
            const Engine::FontGlyphPlacement &next = atlas.unicodeGlyphPlacements[other];
            const bool apart = place.x + place.width <= next.x || next.x + next.width <= place.x
                || place.y + place.height <= next.y || next.y + next.height <= place.y;
            CHECK(apart);
        }
    }

    // A capital's ink starts near the top of the line; a full stop's sits near the baseline.
    const int stop = atlas.glyphIndex('.');
    CHECK(atlas.placement(zhe).top < atlas.placement(stop).top);
    CHECK_EQ(atlas.kerning('A', 'V'), 0.0f);

    // A display height between the raster steps shares the next step's raster and scales its layout.
    const std::optional<Engine::FontAtlasImage> display =
        Engine::loadTrueTypeFontAtlas(fixture.assets, "unicode_test", error, 30);
    REQUIRE_MESSAGE(display.has_value(), error);
    CHECK_EQ(display->atlas.fontHeight, 30);
    CHECK_EQ(display->atlas.rasterHeight, 32);
    CHECK_EQ(display->atlas.layoutScale, doctest::Approx(30.0f / 32.0f));
    CHECK_EQ(Engine::unicodeRasterHeight(16, 24), 16);
    CHECK_EQ(Engine::unicodeRasterHeight(17, 24), 24);
    CHECK_EQ(Engine::unicodeRasterHeight(200, 24), 128);
    CHECK_EQ(Engine::unicodeRasterHeight(0, 11), 48);
    CHECK_EQ(Engine::unicodeRasterHeight(0, 7), 24);
    // A pack's max_raster_height caps large text, which is then drawn magnified.
    CHECK_EQ(Engine::unicodeRasterHeight(90, 24, 64), 64);
    CHECK_EQ(Engine::unicodeRasterHeight(30, 24, 64), 32);
}

TEST_CASE("a Unicode face needs its character list")
{
    FontFixture fixture;
    {
        std::ofstream descriptor(fixture.root / "engine/fonts/truetype/unicode_test.yml");
        descriptor << "file: alegreya_variable.ttf\nmetrics: freetype\nlogical_height: 24\nbaseline: 18\n"
                   << "encoding: utf-8\n";
    }
    std::string error;
    CHECK_FALSE(Engine::loadTrueTypeFontAtlas(fixture.assets, "unicode_test", error).has_value());
    CHECK_FALSE(error.empty());

    {
        std::ofstream descriptor(fixture.root / "engine/fonts/truetype/unicode_test.yml");
        descriptor << "file: alegreya_variable.ttf\nmetrics: freetype\nlogical_height: 24\nbaseline: 18\n"
                   << "encoding: utf-8\ncharacters_file: absent.txt\n";
    }
    CHECK_FALSE(Engine::loadTrueTypeFontAtlas(fixture.assets, "unicode_test", error).has_value());
}

TEST_CASE("a legacy face finds the Windows-1252 glyph of a character and its cell in the grid")
{
    FontFixture fixture;
    std::string error;
    const std::optional<Engine::FontAtlasImage> image =
        Engine::loadTrueTypeFontAtlas(fixture.assets, "alegreya_semibold", error);
    REQUIRE_MESSAGE(image.has_value(), error);
    const Engine::FontAtlas &atlas = image->atlas;
    CHECK_FALSE(atlas.unicode);
    CHECK_EQ(atlas.glyphIndex('A'), int('A'));
    CHECK_EQ(atlas.glyphIndex(0x20ac), 0x80);
    CHECK_EQ(atlas.glyphIndex(0xe9), 0xe9);
    // Windows-1252 has no Greek: the face draws '?'.
    CHECK_EQ(atlas.glyphIndex(0x3a9), int('?'));

    const Engine::FontGlyphPlacement place = atlas.placement('A');
    CHECK_EQ(place.x, ('A' % 16) * (atlas.atlasCellWidth + 2 * atlas.atlasPadding));
    CHECK_EQ(place.y, ('A' / 16) * (atlas.fontHeight + 2 * atlas.atlasPadding));
    CHECK_EQ(place.width, atlas.glyphMetrics['A'].width + 2 * atlas.atlasPadding);
    CHECK_EQ(place.height, atlas.fontHeight + 2 * atlas.atlasPadding);
    CHECK_EQ(place.top, -atlas.atlasPadding);
    CHECK_EQ(atlas.layoutScale, 1.0f);
}

#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>
#include <string>
#include <vector>
#include <unordered_map>

namespace OpenYAMM::Engine
{
class AssetFileSystem;

struct FontGlyphMetrics
{
    int leftSpacing = 0;
    int width = 0;
    int rightSpacing = 0;
    float outlineAdvance = 0;

    float advance() const
    {
        return outlineAdvance > 0 ? outlineAdvance : float(leftSpacing + width + rightSpacing);
    }
};

// Where a glyph's image lies in the atlas, padding included, and how far below the top of the line it starts.
struct FontGlyphPlacement
{
    int x = 0;
    int y = 0;
    int width = 0;
    int height = 0;
    int top = 0;
};

// Logs, once per character, that text asked for a character its font lacks: it is drawn as '?'.
void reportMissingGlyph(uint32_t point);

// Legacy faces keep logical geometry with a supersampled atlas. Independent
// faces use screen pixels.
struct FontAtlas
{
    int firstChar = 0;
    int lastChar = 0;
    int fontHeight = 0;
    int atlasCellWidth = 0;
    int atlasWidth = 0;
    int atlasHeight = 0;
    int atlasScale = 1;
    int atlasPadding = 0;
    std::array<FontGlyphMetrics, 256> glyphMetrics = {{}};
    std::unordered_map<uint16_t, float> kerningPairs;
    std::vector<uint8_t> mainAtlasPixels;

    // A Unicode face (descriptor encoding utf-8) holds every character its character list names, packed in the atlas
    // at rasterHeight pixels; its metrics are raster pixels, and layoutScale turns them into fontHeight's.
    bool unicode = false;
    int rasterHeight = 0;
    float layoutScale = 1.0f;
    std::unordered_map<uint32_t, int> unicodeGlyphIndices;
    std::vector<FontGlyphMetrics> unicodeGlyphMetrics;
    std::vector<FontGlyphPlacement> unicodeGlyphPlacements;

    // The glyph that draws a character, -1 for none. A legacy face indexes it by its Windows-1252 byte; a character
    // the face lacks is drawn as '?' and reported.
    int glyphIndex(uint32_t point) const;
    const FontGlyphMetrics &glyph(int index) const;
    // A legacy glyph's cell in the 16 by 16 grid, at logical size; a Unicode glyph's packed place.
    FontGlyphPlacement placement(int index) const;
    float kerning(uint32_t previous, uint32_t current) const;
};

struct FontAtlasImage
{
    FontAtlas atlas;
    std::vector<uint8_t> shadowPixels;
};

// UTF-8 text in the CP1252 bytes the legacy faces index, independent of the platform's iconv. A character CP1252
// lacks becomes '?'; text that is not valid UTF-8 is taken as CP1252 already and returned unchanged.
std::string utf8ToCp1252(const std::string &text);

// A legacy face: its outlines come from fonts/truetype/<name>.yml and the font file it names, while the original FNT
// supplies the layout metrics and the reserved symbol glyphs (CP1252 bytes without a character). A missing or invalid
// replacement returns an explicit error.
std::optional<FontAtlasImage> loadFontAtlas(
    const AssetFileSystem &assetFileSystem,
    const std::vector<uint8_t> &bitmapBytes,
    const std::string &fontName,
    std::string &error);

// Independent outline faces use their own advances, without requiring a legacy
// FNT. Rasterize at the requested display height; zero uses the descriptor's
// logical height. A descriptor with encoding utf-8 makes a Unicode face of the characters in its characters_file.
// The raster height of a Unicode face: the smallest of a few steps that holds the requested display height, so sizes
// close to each other share one atlas (a CJK one holds thousands of glyphs). A face asked at its logical height
// (pixelHeight 0) is magnified on screen, so it rasters at three times that height, up to 48.
int unicodeRasterHeight(int pixelHeight, int logicalHeight);

std::optional<FontAtlasImage> loadTrueTypeFontAtlas(const AssetFileSystem &assetFileSystem, const std::string &fontName,
                                                    std::string &error, int pixelHeight = 0);
}

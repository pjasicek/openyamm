#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
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

// Legacy faces keep logical geometry with a supersampled atlas. Independent
// faces use screen pixels.
struct FontAtlas
{
    static constexpr size_t MaximumGlyphCount = 512;

    int firstChar = 0;
    int lastChar = 0;
    int fontHeight = 0;
    int atlasCellWidth = 0;
    int atlasWidth = 0;
    int atlasHeight = 0;
    int atlasScale = 1;
    int atlasPadding = 0;
    int glyphCount = 256;
    int atlasColumns = 16;
    std::array<FontGlyphMetrics, MaximumGlyphCount> glyphMetrics = {{}};
    std::unordered_map<uint32_t, uint16_t> glyphsByCodePoint;
    std::unordered_map<uint64_t, float> kerningPairs;
    std::vector<uint8_t> mainAtlasPixels;

    std::optional<uint16_t> glyphForCodePoint(uint32_t codePoint) const
    {
        const auto found = glyphsByCodePoint.find(codePoint);
        if (found != glyphsByCodePoint.end())
        {
            return found->second;
        }
        if (codePoint <= 255 && int(codePoint) >= firstChar && int(codePoint) <= lastChar)
        {
            return static_cast<uint16_t>(codePoint);
        }
        return std::nullopt;
    }

    float kerning(uint16_t previous, uint16_t current) const
    {
        const uint64_t key = (uint64_t(previous) << 32) | current;
        const auto found = kerningPairs.find(key);
        return found == kerningPairs.end() ? 0.0f : found->second;
    }
};

struct FontAtlasImage
{
    FontAtlas atlas;
    std::vector<uint8_t> shadowPixels;
};

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
// logical height.
std::optional<FontAtlasImage> loadTrueTypeFontAtlas(const AssetFileSystem &assetFileSystem, const std::string &fontName,
                                                    std::string &error, int pixelHeight = 0);
}

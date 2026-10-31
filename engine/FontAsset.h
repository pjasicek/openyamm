#pragma once

#include <array>
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

    float kerning(uint8_t previous, uint8_t current) const
    {
        const auto found = kerningPairs.find(uint16_t(previous) * 256 + current);
        return found == kerningPairs.end() ? 0.0f : found->second;
    }
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
// supplies the layout metrics and the reserved symbol glyphs (CP1252 bytes without a character). A descriptor saying
// "glyphs: bitmap" keeps the FNT's own pixels instead. The interface language's copy of the descriptor and font file
// (localizedAssetPath) wins. A missing or invalid replacement returns an explicit error.
std::optional<FontAtlasImage> loadFontAtlas(
    const AssetFileSystem &assetFileSystem,
    const std::vector<uint8_t> &bitmapBytes,
    const std::string &fontName,
    std::string &error);

// Independent outline faces use their own advances, without requiring a legacy
// FNT. Rasterize at the requested display height; zero uses the descriptor's
// logical height. The descriptor names the code page of the bytes it draws (windows-1252, or windows-1251 for
// Cyrillic) and may shrink the em within the line (em_scale, 0.5-1); the interface language's copy of the descriptor
// and font file wins.
std::optional<FontAtlasImage> loadTrueTypeFontAtlas(const AssetFileSystem &assetFileSystem, const std::string &fontName,
                                                    std::string &error, int pixelHeight = 0);
}

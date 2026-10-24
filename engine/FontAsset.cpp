#include "engine/FontAsset.h"

#include "engine/AssetFileSystem.h"

#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_MULTIPLE_MASTERS_H
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <cmath>

namespace OpenYAMM::Engine
{
namespace
{
struct BitmapFont
{
    int firstChar = 0;
    int lastChar = 0;
    int fontHeight = 0;
    std::array<FontGlyphMetrics, 256> glyphMetrics = {{}};
    std::array<uint32_t, 256> glyphOffsets = {{}};
    std::vector<uint8_t> pixels;
};

std::string normalizedFontName(std::string name)
{
    std::transform(name.begin(), name.end(), name.begin(), [](unsigned char character)
    {
        return std::tolower(character);
    });
    return name;
}

int32_t readInt32Le(const uint8_t *pBytes)
{
    return static_cast<int32_t>(
        static_cast<uint32_t>(pBytes[0])
        | (static_cast<uint32_t>(pBytes[1]) << 8)
        | (static_cast<uint32_t>(pBytes[2]) << 16)
        | (static_cast<uint32_t>(pBytes[3]) << 24));
}

uint32_t readUint32Le(const uint8_t *pBytes)
{
    return static_cast<uint32_t>(
        static_cast<uint32_t>(pBytes[0])
        | (static_cast<uint32_t>(pBytes[1]) << 8)
        | (static_cast<uint32_t>(pBytes[2]) << 16)
        | (static_cast<uint32_t>(pBytes[3]) << 24));
}

bool validateBitmapFont(
    const BitmapFont &font,
    const std::vector<uint8_t> &pixels)
{
    if (font.firstChar < 0
        || font.firstChar > 255
        || font.lastChar < 0
        || font.lastChar > 255
        || font.firstChar > font.lastChar
        || font.fontHeight <= 0)
    {
        return false;
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const FontGlyphMetrics &metrics = font.glyphMetrics[glyphIndex];

        if (glyphIndex < font.firstChar || glyphIndex > font.lastChar)
        {
            continue;
        }

        if (metrics.width < 0 || metrics.width > 1024 || metrics.leftSpacing < -512 || metrics.leftSpacing > 512
            || metrics.rightSpacing < -512 || metrics.rightSpacing > 512)
        {
            return false;
        }

        const uint64_t glyphSize = static_cast<uint64_t>(font.fontHeight) * static_cast<uint64_t>(metrics.width);
        const uint64_t glyphEnd = static_cast<uint64_t>(font.glyphOffsets[glyphIndex]) + glyphSize;

        if (glyphEnd > pixels.size())
        {
            return false;
        }
    }

    return true;
}

std::optional<BitmapFont> parseBitmapFont(const std::vector<uint8_t> &bytes)
{
    constexpr size_t FontHeaderSize = 32;
    constexpr size_t Mm7AtlasSize = 4096;

    if (bytes.size() < FontHeaderSize + Mm7AtlasSize)
    {
        return std::nullopt;
    }

    const uint8_t *pBytes = bytes.data();

    if (pBytes[2] != 8 || pBytes[3] != 0 || pBytes[4] != 0 || pBytes[6] != 0 || pBytes[7] != 0)
    {
        return std::nullopt;
    }

    BitmapFont font = {};
    font.firstChar = pBytes[0];
    font.lastChar = pBytes[1];
    font.fontHeight = pBytes[5];

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const size_t metricOffset = FontHeaderSize + static_cast<size_t>(glyphIndex) * 12;
        font.glyphMetrics[glyphIndex].leftSpacing = readInt32Le(&pBytes[metricOffset]);
        font.glyphMetrics[glyphIndex].width = readInt32Le(&pBytes[metricOffset + 4]);
        font.glyphMetrics[glyphIndex].rightSpacing = readInt32Le(&pBytes[metricOffset + 8]);
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const size_t offsetPosition = FontHeaderSize + 256 * 12 + static_cast<size_t>(glyphIndex) * 4;
        font.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
    }

    font.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(FontHeaderSize + Mm7AtlasSize), bytes.end());

    if (!validateBitmapFont(font, font.pixels))
    {
        return std::nullopt;
    }

    return font;
}


struct FreeTypeFace
{
    FT_Library library = nullptr;
    FT_Face face = nullptr;

    ~FreeTypeFace()
    {
        if (face != nullptr)
        {
            FT_Done_Face(face);
        }
        if (library != nullptr)
        {
            FT_Done_FreeType(library);
        }
    }
};

uint32_t cp1252CodePoint(int character)
{
    constexpr std::array<uint32_t, 32> Extended = {
        0x20ac, 0, 0x201a, 0x192, 0x201e, 0x2026, 0x2020, 0x2021,
        0x2c6, 0x2030, 0x160, 0x2039, 0x152, 0, 0x17d, 0,
        0, 0x2018, 0x2019, 0x201c, 0x201d, 0x2022, 0x2013, 0x2014,
        0x2dc, 0x2122, 0x161, 0x203a, 0x153, 0, 0x17e, 0x178};
    if (character < 32 || character == 127)
    {
        return 0;
    }
    return character >= 128 && character < 160 ? Extended[character - 128] : uint32_t(character);
}

std::vector<uint32_t> russianCodePoints()
{
    std::vector<uint32_t> result = {0x401, 0x451};
    for (uint32_t codePoint = 0x410; codePoint <= 0x44f; ++codePoint)
    {
        result.push_back(codePoint);
    }
    return result;
}

void allocateAtlas(FontAtlasImage &image, bool white = false)
{
    FontAtlas &atlas = image.atlas;
    const size_t byteCount = size_t(atlas.atlasWidth) * atlas.atlasHeight * 4;
    atlas.mainAtlasPixels.resize(byteCount, white || atlas.atlasScale > 1 ? 255 : 0);
    image.shadowPixels.resize(byteCount, 0);
    // White even outside the ink prevents dark fringes with straight-alpha
    // bilinear filtering.
    for (size_t offset = 3; offset < byteCount; offset += 4)
    {
        atlas.mainAtlasPixels[offset] = 0;
    }
}

void copyBitmapGlyph(const BitmapFont &font, int character, FontAtlasImage &image)
{
    FontAtlas &atlas = image.atlas;
    const int scale = atlas.atlasScale;
    const int cellX = (character % atlas.atlasColumns)
        * (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * scale;
    const int cellY = (character / atlas.atlasColumns)
        * (atlas.fontHeight + 2 * atlas.atlasPadding) * scale;
    const int width = font.glyphMetrics[character].width;
    for (int y = 0; y < font.fontHeight * scale; ++y)
    {
        for (int x = 0; x < width * scale; ++x)
        {
            const uint8_t value = font.pixels[font.glyphOffsets[character] + size_t(y / scale) * width + x / scale];
            const size_t offset = (size_t(cellY + atlas.atlasPadding * scale + y) * atlas.atlasWidth
                + cellX + atlas.atlasPadding * scale + x) * 4;
            if (value > 1)
            {
                atlas.mainAtlasPixels[offset + 0] = 255;
                atlas.mainAtlasPixels[offset + 1] = 255;
                atlas.mainAtlasPixels[offset + 2] = 255;
                atlas.mainAtlasPixels[offset + 3] = 255;
            }
            image.shadowPixels[offset + 3] = value == 1 ? 255 : 0;
        }
    }
}
}

std::optional<FontAtlasImage> loadTrueTypeFontAtlas(const AssetFileSystem &assetFileSystem, const std::string &fontName,
                                                    std::string &error, int pixelHeight)
{
    error.clear();
    const std::string name = normalizedFontName(fontName);
    if (name.empty() || name.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_-") != std::string::npos)
    {
        error = "Invalid outline font name";
        return std::nullopt;
    }
    const std::optional<std::string> descriptorText = assetFileSystem.readTextFile("fonts/truetype/" + name + ".yml");
    FontAtlasImage image;
    FontAtlas &atlas = image.atlas;
    std::string file;
    int baseline = 0;
    std::optional<int> weight;
    try
    {
        const YAML::Node descriptor = YAML::Load(descriptorText.value_or(""));
        file = descriptor["file"].as<std::string>();
        atlas.fontHeight = descriptor["logical_height"].as<int>();
        baseline = descriptor["baseline"].as<int>();
        if (descriptor["weight"])
        {
            weight = descriptor["weight"].as<int>();
        }
        if (descriptor["metrics"].as<std::string>() != "freetype" ||
            descriptor["encoding"].as<std::string>() != "windows-1252" || file.empty() ||
            file.find_first_of("/\\") != std::string::npos || atlas.fontHeight < 8 || atlas.fontHeight > 64 ||
            baseline < 0 || baseline > atlas.fontHeight || (weight && (*weight < 1 || *weight > 1000)))
        {
            error = "Invalid independent outline font descriptor: " + name;
            return std::nullopt;
        }
    }
    catch (const YAML::Exception &exception)
    {
        error = "Invalid outline descriptor: " + name + ": " + exception.what();
        return std::nullopt;
    }
    if (pixelHeight < 0 || pixelHeight > 512)
    {
        error = "Invalid outline font pixel height";
        return std::nullopt;
    }
    const int logicalHeight = atlas.fontHeight;
    atlas.fontHeight = pixelHeight > 0 ? pixelHeight : logicalHeight;
    baseline = int(std::lround(float(baseline) * atlas.fontHeight / logicalHeight));
    atlas.atlasPadding = int(std::ceil(8.0f * atlas.fontHeight / logicalHeight)) + 1;
    const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile("fonts/truetype/" + file);
    FreeTypeFace font;
    atlas.atlasScale = 1;
    atlas.firstChar = 32;
    atlas.lastChar = 255;
    for (int character = atlas.firstChar; character <= atlas.lastChar; ++character)
    {
        const uint32_t codePoint = cp1252CodePoint(character);
        if (codePoint != 0)
        {
            atlas.glyphsByCodePoint[codePoint] = static_cast<uint16_t>(character);
        }
    }
    if (!bytes || bytes->empty() || bytes->size() > 32 * 1024 * 1024 || FT_Init_FreeType(&font.library) != 0 ||
        FT_New_Memory_Face(font.library, bytes->data(), FT_Long(bytes->size()), 0, &font.face) != 0 ||
        !FT_IS_SCALABLE(font.face) || FT_Select_Charmap(font.face, FT_ENCODING_UNICODE) != 0 ||
        FT_Set_Pixel_Sizes(font.face, 0, atlas.fontHeight * atlas.atlasScale) != 0)
    {
        error = "Unable to open outline font: " + file;
        return std::nullopt;
    }
    if (weight)
    {
        FT_MM_Var *pVariations = nullptr;
        if (FT_Get_MM_Var(font.face, &pVariations) != 0)
        {
            error = "Font has no variable weight axis: " + file;
            return std::nullopt;
        }
        std::vector<FT_Fixed> coordinates(pVariations->num_axis);
        const FT_Fixed requestedWeight = FT_Fixed(*weight) * 65536;
        bool validWeight = false;
        for (size_t axisIndex = 0; axisIndex < coordinates.size(); ++axisIndex)
        {
            const FT_Var_Axis &axis = pVariations->axis[axisIndex];
            coordinates[axisIndex] = axis.def;
            if (axis.tag == FT_MAKE_TAG('w', 'g', 'h', 't'))
            {
                validWeight = requestedWeight >= axis.minimum && requestedWeight <= axis.maximum;
                coordinates[axisIndex] = requestedWeight;
            }
        }
        FT_Done_MM_Var(font.library, pVariations);
        if (!validWeight
            || FT_Set_Var_Design_Coordinates(font.face, coordinates.size(), coordinates.data()) != 0)
        {
            error = "Invalid variable font weight: " + file;
            return std::nullopt;
        }
    }

    const std::optional<std::vector<uint8_t>> outlineCyrillicBytes =
        assetFileSystem.readBinaryFile("fonts/truetype/alegreya_variable.ttf");
    FreeTypeFace outlineCyrillicFallback;
    if (!outlineCyrillicBytes || outlineCyrillicBytes->empty()
        || FT_Init_FreeType(&outlineCyrillicFallback.library) != 0
        || FT_New_Memory_Face(outlineCyrillicFallback.library, outlineCyrillicBytes->data(),
                              FT_Long(outlineCyrillicBytes->size()), 0, &outlineCyrillicFallback.face) != 0
        || FT_Select_Charmap(outlineCyrillicFallback.face, FT_ENCODING_UNICODE) != 0
        || FT_Set_Pixel_Sizes(outlineCyrillicFallback.face, 0, atlas.fontHeight * atlas.atlasScale) != 0)
    {
        error = "Unable to open Cyrillic fallback font";
        return std::nullopt;
    }
    for (int character = atlas.firstChar; character <= atlas.lastChar; ++character)
    {
        const uint32_t point = cp1252CodePoint(character);
        if (point == 0)
        {
            continue;
        }
        if (FT_Load_Char(font.face, point, FT_LOAD_TARGET_LIGHT | FT_LOAD_NO_BITMAP) != 0)
        {
            error = "Unable to measure outline glyph: " + std::to_string(point);
            return std::nullopt;
        }
        const FT_GlyphSlot pGlyph = font.face->glyph;
        const float divisor = 64.0f * atlas.atlasScale;
        FontGlyphMetrics &metrics = atlas.glyphMetrics[character];
        metrics.leftSpacing = int(std::floor(pGlyph->metrics.horiBearingX / divisor));
        metrics.width =
            int(std::ceil((pGlyph->metrics.horiBearingX + pGlyph->metrics.width) / divisor)) - metrics.leftSpacing;
        metrics.rightSpacing = int(std::round(pGlyph->advance.x / divisor)) - metrics.leftSpacing - metrics.width;
        // Keep fractional horizontal spacing while light hinting fits glyphs to the
        // target pixel size.
        metrics.outlineAdvance = pGlyph->linearHoriAdvance / 65536.0f;
        atlas.atlasCellWidth = std::max(atlas.atlasCellWidth, metrics.width);
    }
    for (const uint32_t codePoint : russianCodePoints())
    {
        FT_Face sourceFace = FT_Get_Char_Index(font.face, codePoint) != 0 ? font.face : outlineCyrillicFallback.face;
        if (atlas.glyphCount >= int(FontAtlas::MaximumGlyphCount)
            || FT_Load_Char(sourceFace, codePoint, FT_LOAD_TARGET_LIGHT | FT_LOAD_NO_BITMAP) != 0)
        {
            error = "Unable to measure Cyrillic outline glyph: " + std::to_string(codePoint);
            return std::nullopt;
        }
        const int glyphIndex = atlas.glyphCount++;
        const FT_GlyphSlot pGlyph = sourceFace->glyph;
        const float divisor = 64.0f * atlas.atlasScale;
        FontGlyphMetrics &metrics = atlas.glyphMetrics[glyphIndex];
        metrics.leftSpacing = int(std::floor(pGlyph->metrics.horiBearingX / divisor));
        metrics.width = int(std::ceil((pGlyph->metrics.horiBearingX + pGlyph->metrics.width) / divisor))
            - metrics.leftSpacing;
        metrics.rightSpacing = int(std::round(pGlyph->advance.x / divisor)) - metrics.leftSpacing - metrics.width;
        metrics.outlineAdvance = pGlyph->linearHoriAdvance / 65536.0f;
        atlas.atlasCellWidth = std::max(atlas.atlasCellWidth, metrics.width);
        atlas.glyphsByCodePoint[codePoint] = static_cast<uint16_t>(glyphIndex);
    }
    if (FT_HAS_KERNING(font.face))
    {
        for (int previous = atlas.firstChar; previous <= atlas.lastChar; ++previous)
        {
            for (int current = atlas.firstChar; current <= atlas.lastChar; ++current)
            {
                FT_Vector adjustment{};
                FT_Get_Kerning(font.face, FT_Get_Char_Index(font.face, cp1252CodePoint(previous)),
                               FT_Get_Char_Index(font.face, cp1252CodePoint(current)), FT_KERNING_UNFITTED,
                               &adjustment);
                if (adjustment.x != 0)
                {
                    const uint64_t key = (uint64_t(previous) << 32) | uint32_t(current);
                    atlas.kerningPairs[key] = adjustment.x / (64.0f * atlas.atlasScale);
                }
            }
        }
    }
    atlas.atlasWidth =
        (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * atlas.atlasColumns * atlas.atlasScale;
    const int outlineAtlasRows = (atlas.glyphCount + atlas.atlasColumns - 1) / atlas.atlasColumns;
    atlas.atlasHeight =
        (atlas.fontHeight + 2 * atlas.atlasPadding) * outlineAtlasRows * atlas.atlasScale;
    if (atlas.atlasWidth > 8192 || atlas.atlasHeight > 8192)
    {
        error = "Outline atlas exceeds texture limit";
        return std::nullopt;
    }
    allocateAtlas(image, true);
    for (int character = atlas.firstChar; character <= atlas.lastChar; ++character)
    {
        const uint32_t point = cp1252CodePoint(character);
        if (point == 0)
        {
            continue;
        }
        if (FT_Load_Char(font.face, point, FT_LOAD_TARGET_LIGHT | FT_LOAD_NO_BITMAP) != 0 ||
            FT_Render_Glyph(font.face->glyph, FT_RENDER_MODE_NORMAL) != 0)
        {
            error = "Unable to render outline glyph";
            return std::nullopt;
        }
        const FT_GlyphSlot pGlyph = font.face->glyph;
        const FT_Bitmap &raster = pGlyph->bitmap;
        const int scale = atlas.atlasScale;
        const int originX =
            (atlas.atlasPadding - atlas.glyphMetrics[character].leftSpacing) * scale + pGlyph->bitmap_left;
        const int originY = (baseline + atlas.atlasPadding) * scale - pGlyph->bitmap_top;
        const int width = (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * scale;
        const int height = (atlas.fontHeight + 2 * atlas.atlasPadding) * scale;
        if (raster.width != 0 && raster.rows != 0 &&
            (raster.pixel_mode != FT_PIXEL_MODE_GRAY || originX < 0 || originY < 0 ||
             originX + int(raster.width) + scale > width || originY + int(raster.rows) + scale > height))
        {
            error = "Outline glyph exceeds cell: " + std::to_string(point);
            return std::nullopt;
        }
        const int cellX = (character % atlas.atlasColumns) * width;
        const int cellY = (character / atlas.atlasColumns) * height;
        for (unsigned int y = 0; y < raster.rows; ++y)
        {
            const uint8_t *pRow =
                raster.buffer + (raster.pitch >= 0 ? y : raster.rows - 1 - y) * size_t(std::abs(raster.pitch));
            for (unsigned int x = 0; x < raster.width; ++x)
            {
                const size_t offset = (size_t(cellY + originY + y) * atlas.atlasWidth + cellX + originX + x) * 4;
                atlas.mainAtlasPixels[offset + 3] = pRow[x];
                // The renderer positions this mask one display pixel away; do not bake
                // a second offset into it.
                image.shadowPixels[offset + 3] = pRow[x];
            }
        }
    }
    int outlineCyrillicGlyphIndex = 256;
    for (const uint32_t codePoint : russianCodePoints())
    {
        FT_Face sourceFace = FT_Get_Char_Index(font.face, codePoint) != 0 ? font.face : outlineCyrillicFallback.face;
        if (FT_Load_Char(sourceFace, codePoint, FT_LOAD_TARGET_LIGHT | FT_LOAD_NO_BITMAP) != 0
            || FT_Render_Glyph(sourceFace->glyph, FT_RENDER_MODE_NORMAL) != 0)
        {
            error = "Unable to render Cyrillic outline glyph: " + std::to_string(codePoint);
            return std::nullopt;
        }
        const FT_GlyphSlot pGlyph = sourceFace->glyph;
        const FT_Bitmap &raster = pGlyph->bitmap;
        const int scale = atlas.atlasScale;
        const int cellWidth = (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * scale;
        const int cellHeight = (atlas.fontHeight + 2 * atlas.atlasPadding) * scale;
        const FontGlyphMetrics &metrics = atlas.glyphMetrics[outlineCyrillicGlyphIndex];
        const int originX = (atlas.atlasPadding - metrics.leftSpacing) * scale + pGlyph->bitmap_left;
        const int originY = (baseline + atlas.atlasPadding) * scale - pGlyph->bitmap_top;
        const int cellX = (outlineCyrillicGlyphIndex % atlas.atlasColumns) * cellWidth;
        const int cellY = (outlineCyrillicGlyphIndex / atlas.atlasColumns) * cellHeight;
        if (raster.pixel_mode != FT_PIXEL_MODE_GRAY || originX < 0 || originY < 0
            || originX + int(raster.width) > cellWidth || originY + int(raster.rows) > cellHeight)
        {
            error = "Cyrillic outline glyph exceeds atlas cell: " + std::to_string(codePoint);
            return std::nullopt;
        }
        for (unsigned int y = 0; y < raster.rows; ++y)
        {
            const uint8_t *pRow = raster.buffer + (raster.pitch >= 0 ? y : raster.rows - 1 - y)
                * size_t(std::abs(raster.pitch));
            for (unsigned int x = 0; x < raster.width; ++x)
            {
                const size_t offset = (size_t(cellY + originY + y) * atlas.atlasWidth + cellX + originX + x) * 4;
                atlas.mainAtlasPixels[offset + 3] = pRow[x];
                image.shadowPixels[offset + 3] = pRow[x];
            }
        }
        ++outlineCyrillicGlyphIndex;
    }
    return image;
}

std::optional<FontAtlasImage> loadFontAtlas(
    const AssetFileSystem &assetFileSystem,
    const std::vector<uint8_t> &bitmapBytes,
    const std::string &fontName,
    std::string &error)
{
    error.clear();
    const std::optional<BitmapFont> bitmap = parseBitmapFont(bitmapBytes);
    if (!bitmap)
    {
        error = "invalid legacy FNT";
        return std::nullopt;
    }

    FontAtlasImage image;
    FontAtlas &atlas = image.atlas;
    atlas.firstChar = bitmap->firstChar;
    atlas.lastChar = bitmap->lastChar;
    for (int character = atlas.firstChar; character <= atlas.lastChar; ++character)
    {
        const uint32_t codePoint = cp1252CodePoint(character);
        if (codePoint != 0)
        {
            atlas.glyphsByCodePoint[codePoint] = static_cast<uint16_t>(character);
        }
    }
    atlas.fontHeight = bitmap->fontHeight;
    std::copy(bitmap->glyphMetrics.begin(), bitmap->glyphMetrics.end(), atlas.glyphMetrics.begin());
    atlas.atlasCellWidth = 1;
    for (int character = atlas.firstChar; character <= atlas.lastChar; ++character)
    {
        atlas.atlasCellWidth = std::max(atlas.atlasCellWidth, atlas.glyphMetrics[character].width);
    }
    atlas.atlasScale = 4;
    // Includes reconstructed italic overhangs (notably Z-caron) and the one-pixel shadow.
    atlas.atlasPadding = 5;
    atlas.atlasWidth =
        (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * atlas.atlasColumns * atlas.atlasScale;
    atlas.atlasHeight = (atlas.fontHeight + 2 * atlas.atlasPadding)
        * ((atlas.glyphCount + atlas.atlasColumns - 1) / atlas.atlasColumns) * atlas.atlasScale;
    if (atlas.atlasWidth > 8192 || atlas.atlasHeight > 8192)
    {
        error = "font atlas exceeds 8192 pixels";
        return std::nullopt;
    }

    const std::string name = normalizedFontName(fontName);
    if (name.empty() || name.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_-") != std::string::npos)
    {
        error = "invalid TTF replacement name";
        return std::nullopt;
    }
    const std::string descriptorPath = "fonts/truetype/" + name + ".yml";
    const std::optional<std::string> descriptorText = assetFileSystem.readTextFile(descriptorPath);
    if (!descriptorText)
    {
        error = "missing TTF descriptor: " + descriptorPath;
        return std::nullopt;
    }

    std::string fileName;
    int baseline = 0;
    bool blackInk = false;
    bool synthesizeShadow = true;
    try
    {
        const YAML::Node descriptor = YAML::Load(*descriptorText);
        fileName = descriptor["file"].as<std::string>();
        baseline = descriptor["baseline"].as<int>();
        const std::string presentation = descriptor["presentation"].as<std::string>("tintable-with-shadow");
        if (presentation != "tintable-with-shadow" && presentation != "black-ink" && presentation != "tintable")
        {
            error = "unsupported TTF presentation: " + descriptorPath;
            return std::nullopt;
        }
        blackInk = presentation == "black-ink";
        synthesizeShadow = presentation == "tintable-with-shadow";
        if (descriptor["logical_height"].as<int>() != atlas.fontHeight
            || descriptor["encoding"].as<std::string>() != "windows-1252"
            || baseline < 0 || baseline > atlas.fontHeight
            || fileName.empty() || fileName.find_first_of("/\\") != std::string::npos)
        {
            error = "TTF descriptor metrics, encoding or filename invalid: " + descriptorPath;
            return std::nullopt;
        }
    }
    catch (const YAML::Exception &exception)
    {
        error = "invalid TTF descriptor: " + descriptorPath + ": " + exception.what();
        return std::nullopt;
    }

    const std::string fontPath = "fonts/truetype/" + fileName;
    const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(fontPath);
    if (!bytes || bytes->empty() || bytes->size() > 32 * 1024 * 1024)
    {
        error = "missing, empty or oversized TTF: " + fontPath;
        return std::nullopt;
    }
    FreeTypeFace font;
    if (FT_Init_FreeType(&font.library) != 0
        || FT_New_Memory_Face(font.library, bytes->data(), FT_Long(bytes->size()), 0, &font.face) != 0
        || !FT_IS_SCALABLE(font.face)
        || FT_Select_Charmap(font.face, FT_ENCODING_UNICODE) != 0
        || FT_Set_Pixel_Sizes(font.face, 0, atlas.fontHeight * atlas.atlasScale) != 0)
    {
        error = "FreeType could not open scalable Unicode font: " + fontPath;
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> cyrillicBytes =
        assetFileSystem.readBinaryFile("fonts/truetype/alegreya_variable.ttf");
    FreeTypeFace cyrillicFont;
    if (!cyrillicBytes || cyrillicBytes->empty()
        || FT_Init_FreeType(&cyrillicFont.library) != 0
        || FT_New_Memory_Face(cyrillicFont.library, cyrillicBytes->data(), FT_Long(cyrillicBytes->size()), 0,
                              &cyrillicFont.face) != 0
        || FT_Select_Charmap(cyrillicFont.face, FT_ENCODING_UNICODE) != 0
        || FT_Set_Pixel_Sizes(cyrillicFont.face, 0, atlas.fontHeight * atlas.atlasScale) != 0)
    {
        error = "Unable to open Cyrillic fallback font";
        return std::nullopt;
    }

    for (const uint32_t codePoint : russianCodePoints())
    {
        if (atlas.glyphCount >= int(FontAtlas::MaximumGlyphCount)
            || FT_Load_Char(cyrillicFont.face, codePoint, FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP) != 0)
        {
            error = "Unable to measure Cyrillic fallback glyph: " + std::to_string(codePoint);
            return std::nullopt;
        }
        const int glyphIndex = atlas.glyphCount++;
        const FT_GlyphSlot pGlyph = cyrillicFont.face->glyph;
        const float divisor = 64.0f * atlas.atlasScale;
        FontGlyphMetrics &metrics = atlas.glyphMetrics[glyphIndex];
        metrics.leftSpacing = int(std::floor(pGlyph->metrics.horiBearingX / divisor));
        metrics.width = int(std::ceil((pGlyph->metrics.horiBearingX + pGlyph->metrics.width) / divisor))
            - metrics.leftSpacing;
        metrics.rightSpacing = int(std::round(pGlyph->advance.x / divisor)) - metrics.leftSpacing - metrics.width;
        // Advances use logical pixels, just like the legacy metrics, rather than atlas pixels.
        metrics.outlineAdvance = pGlyph->linearHoriAdvance / (65536.0f * atlas.atlasScale);
        atlas.atlasCellWidth = std::max(atlas.atlasCellWidth, metrics.width);
        atlas.glyphsByCodePoint[codePoint] = static_cast<uint16_t>(glyphIndex);
    }

    atlas.atlasWidth = (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * atlas.atlasColumns * atlas.atlasScale;
    const int atlasRows = (atlas.glyphCount + atlas.atlasColumns - 1) / atlas.atlasColumns;
    atlas.atlasHeight = (atlas.fontHeight + 2 * atlas.atlasPadding) * atlasRows * atlas.atlasScale;
    if (atlas.atlasWidth > 8192 || atlas.atlasHeight > 8192)
    {
        error = "font atlas exceeds 8192 pixels";
        return std::nullopt;
    }

    allocateAtlas(image);
    for (int character = atlas.firstChar; character <= atlas.lastChar; ++character)
    {
        const uint32_t codePoint = cp1252CodePoint(character);
        // Reserved byte slots are legacy UI symbols, outside the replacement's printable encoding.
        if (codePoint == 0)
        {
            copyBitmapGlyph(*bitmap, character, image);
            continue;
        }
        const FT_UInt glyphIndex = FT_Get_Char_Index(font.face, codePoint);
        if (glyphIndex == 0
            || FT_Load_Glyph(font.face, glyphIndex, FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP) != 0
            || FT_Render_Glyph(font.face->glyph, FT_RENDER_MODE_NORMAL) != 0)
        {
            error = "TTF missing or unable to rasterize CP1252 byte " + std::to_string(character) + ": " + fontPath;
            return std::nullopt;
        }
        const FT_GlyphSlot pGlyph = font.face->glyph;
        const FT_Bitmap &raster = pGlyph->bitmap;
        const int scale = atlas.atlasScale;
        const int width = (atlas.glyphMetrics[character].width + 2 * atlas.atlasPadding) * scale;
        const int height = (atlas.fontHeight + 2 * atlas.atlasPadding) * scale;
        const int originX = pGlyph->bitmap_left
            + (atlas.atlasPadding - atlas.glyphMetrics[character].leftSpacing) * scale;
        const int originY = (baseline + atlas.atlasPadding) * scale - pGlyph->bitmap_top;
        const int cellX = (character % atlas.atlasColumns)
            * (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * scale;
        const int cellY = (character / atlas.atlasColumns)
            * (atlas.fontHeight + 2 * atlas.atlasPadding) * scale;
        if (raster.width != 0 && raster.rows != 0
            && (raster.pixel_mode != FT_PIXEL_MODE_GRAY || originX < 0 || originY < 0
                || originX + int(raster.width) > width || originY + int(raster.rows) > height))
        {
            error = "TTF glyph exceeds padded legacy cell at CP1252 byte "
                + std::to_string(character) + ": " + fontPath;
            return std::nullopt;
        }
        for (unsigned int y = 0; y < raster.rows; ++y)
        {
            const uint8_t *pRow = raster.buffer + (raster.pitch >= 0 ? y : raster.rows - 1 - y)
                * size_t(std::abs(raster.pitch));
            for (unsigned int x = 0; x < raster.width; ++x)
            {
                const size_t offset = (size_t(cellY + originY + y) * atlas.atlasWidth + cellX + originX + x) * 4;
                // Black-ink sources use the native black layer at the original coordinates.
                // Preserve caller offsets and avoid adding a second, shifted copy of the ink.
                if (blackInk)
                {
                    image.shadowPixels[offset + 3] = pRow[x];
                    continue;
                }
                atlas.mainAtlasPixels[offset + 3] = pRow[x];
                // Legacy HUD callers expect a shadow already shifted one logical pixel.
                if (synthesizeShadow && originX + int(x) + scale < width && originY + int(y) + scale < height)
                {
                    const size_t shadowOffset = offset + (size_t(scale) * atlas.atlasWidth + scale) * 4;
                    image.shadowPixels[shadowOffset + 3] = pRow[x];
                }
            }
        }
    }

    int cyrillicGlyphIndex = 256;
    for (const uint32_t codePoint : russianCodePoints())
    {
        if (FT_Load_Char(cyrillicFont.face, codePoint, FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP) != 0
            || FT_Render_Glyph(cyrillicFont.face->glyph, FT_RENDER_MODE_NORMAL) != 0)
        {
            error = "Unable to rasterize Cyrillic fallback glyph: " + std::to_string(codePoint);
            return std::nullopt;
        }
        const FT_GlyphSlot pGlyph = cyrillicFont.face->glyph;
        const FT_Bitmap &raster = pGlyph->bitmap;
        const int scale = atlas.atlasScale;
        const FontGlyphMetrics &metrics = atlas.glyphMetrics[cyrillicGlyphIndex];
        const int cellWidth = (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * scale;
        const int cellHeight = (atlas.fontHeight + 2 * atlas.atlasPadding) * scale;
        const int originX = pGlyph->bitmap_left + (atlas.atlasPadding - metrics.leftSpacing) * scale;
        const int originY = (baseline + atlas.atlasPadding) * scale - pGlyph->bitmap_top;
        const int cellX = (cyrillicGlyphIndex % atlas.atlasColumns) * cellWidth;
        const int cellY = (cyrillicGlyphIndex / atlas.atlasColumns) * cellHeight;
        if (raster.pixel_mode != FT_PIXEL_MODE_GRAY || originX < 0 || originY < 0
            || originX + int(raster.width) > cellWidth || originY + int(raster.rows) > cellHeight)
        {
            error = "Cyrillic fallback glyph exceeds atlas cell: " + std::to_string(codePoint);
            return std::nullopt;
        }
        for (unsigned int y = 0; y < raster.rows; ++y)
        {
            const uint8_t *pRow = raster.buffer + (raster.pitch >= 0 ? y : raster.rows - 1 - y)
                * size_t(std::abs(raster.pitch));
            for (unsigned int x = 0; x < raster.width; ++x)
            {
                const size_t offset = (size_t(cellY + originY + y) * atlas.atlasWidth + cellX + originX + x) * 4;
                if (blackInk)
                {
                    image.shadowPixels[offset + 3] = pRow[x];
                }
                else
                {
                    atlas.mainAtlasPixels[offset + 3] = pRow[x];
                    if (synthesizeShadow && originX + int(x) + scale < cellWidth
                        && originY + int(y) + scale < cellHeight)
                    {
                        const size_t shadowOffset = offset + (size_t(scale) * atlas.atlasWidth + scale) * 4;
                        image.shadowPixels[shadowOffset + 3] = pRow[x];
                    }
                }
            }
        }
        ++cyrillicGlyphIndex;
    }
    return image;
}
}

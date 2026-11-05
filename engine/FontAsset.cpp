#include "engine/FontAsset.h"

#include "engine/AssetFileSystem.h"
#include "engine/Utf8Text.h"

#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_MULTIPLE_MASTERS_H
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <set>
#include <unordered_set>

namespace OpenYAMM::Engine
{
void reportMissingGlyph(uint32_t point)
{
    static std::mutex mutex;
    static std::unordered_set<uint32_t> reported;
    const std::lock_guard lock(mutex);
    if (!reported.insert(point).second)
    {
        return;
    }
    std::string character;
    Utf8::append(character, point);
    std::cout << "Font: no glyph for U+" << std::hex << std::uppercase << std::setw(4) << std::setfill('0') << point
              << std::dec << std::nouppercase << std::setfill(' ') << " '" << character << "', drawn as '?'\n";
}

int FontAtlas::glyphIndex(uint32_t point) const
{
    if (unicode)
    {
        const auto found = unicodeGlyphIndices.find(point);
        if (found != unicodeGlyphIndices.end())
        {
            return found->second;
        }
        if (point > ' ')
        {
            reportMissingGlyph(point);
        }
        const auto question = unicodeGlyphIndices.find('?');
        return question != unicodeGlyphIndices.end() ? question->second : -1;
    }
    std::optional<uint8_t> byte = Utf8::toCp1252(point);
    if (!byte)
    {
        reportMissingGlyph(point);
        byte = uint8_t('?');
    }
    return *byte >= firstChar && *byte <= lastChar ? int(*byte) : -1;
}

const FontGlyphMetrics &FontAtlas::glyph(int index) const
{
    return unicode ? unicodeGlyphMetrics[size_t(index)] : glyphMetrics[size_t(index)];
}

FontGlyphPlacement FontAtlas::placement(int index) const
{
    if (unicode)
    {
        return unicodeGlyphPlacements[size_t(index)];
    }
    FontGlyphPlacement place;
    place.x = (index % 16) * (atlasCellWidth + 2 * atlasPadding);
    place.y = (index / 16) * (fontHeight + 2 * atlasPadding);
    place.width = glyphMetrics[size_t(index)].width + 2 * atlasPadding;
    place.height = fontHeight + 2 * atlasPadding;
    place.top = -atlasPadding;
    return place;
}

float FontAtlas::kerning(uint32_t previous, uint32_t current) const
{
    // Legacy pairs are Windows-1252 bytes; Unicode faces keep no kerning.
    const std::optional<uint8_t> previousByte = unicode ? std::nullopt : Utf8::toCp1252(previous);
    const std::optional<uint8_t> currentByte = unicode ? std::nullopt : Utf8::toCp1252(current);
    if (!previousByte || !currentByte)
    {
        return 0.0f;
    }
    const auto found = kerningPairs.find(uint16_t(*previousByte * 256 + *currentByte));
    return found == kerningPairs.end() ? 0.0f : found->second;
}

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
    const int cellX = (character % 16) * (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * scale;
    const int cellY = (character / 16) * (atlas.fontHeight + 2 * atlas.atlasPadding) * scale;
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

struct RenderedGlyph
{
    uint32_t point = 0;
    FontGlyphMetrics metrics;
    int rows = 0;
    int top = 0;
    std::vector<uint8_t> coverage;
};

// Packs the glyphs in shelves, the tallest first, and returns the atlas width and height, 0 when it would exceed the
// texture limit. Each place keeps padding pixels clear around the glyph against bilinear bleeding.
std::pair<int, int> packGlyphShelves(
    const std::vector<RenderedGlyph> &glyphs,
    int padding,
    std::vector<FontGlyphPlacement> &placements)
{
    constexpr int MaximumSize = 8192;
    std::vector<size_t> order(glyphs.size());
    size_t area = 0;
    for (size_t index = 0; index < glyphs.size(); ++index)
    {
        order[index] = index;
        area += size_t(glyphs[index].metrics.width + 2 * padding) * size_t(glyphs[index].rows + 2 * padding);
    }
    std::stable_sort(order.begin(), order.end(), [&glyphs](size_t left, size_t right)
    {
        return glyphs[left].rows > glyphs[right].rows;
    });
    int width = 256;
    while (width < MaximumSize && size_t(width) * size_t(width) < area + area / 4)
    {
        width *= 2;
    }
    placements.assign(glyphs.size(), {});
    int shelfX = 0;
    int shelfY = 0;
    int shelfHeight = 0;
    for (const size_t index : order)
    {
        const RenderedGlyph &glyph = glyphs[index];
        const int placeWidth = glyph.metrics.width + 2 * padding;
        const int placeHeight = glyph.rows + 2 * padding;
        if (shelfX + placeWidth > width)
        {
            shelfY += shelfHeight;
            shelfX = 0;
            shelfHeight = 0;
        }
        placements[index] = {shelfX, shelfY, placeWidth, placeHeight, glyph.top - padding};
        shelfX += placeWidth;
        shelfHeight = std::max(shelfHeight, placeHeight);
    }
    const int height = shelfY + shelfHeight;
    return height > MaximumSize ? std::pair{0, 0} : std::pair{width, std::max(1, height)};
}

// A Unicode face: ASCII, the Windows-1252 characters the English tables use and every character of the descriptor's
// character list, each rendered once at rasterHeight and packed. A character the font file lacks is left out, to be
// drawn as '?' and reported when text asks for it.
std::optional<FontAtlasImage> buildUnicodeAtlas(
    FT_Face face,
    const std::string &characterList,
    const std::string &name,
    int displayHeight,
    int rasterHeight,
    int baseline,
    std::string &error)
{
    std::set<uint32_t> points;
    for (int byte = 32; byte < 256; ++byte)
    {
        if (cp1252CodePoint(byte) != 0)
        {
            points.insert(cp1252CodePoint(byte));
        }
    }
    for (const uint32_t point : Utf8::codePoints(characterList))
    {
        if (Utf8::isTypeable(point))
        {
            points.insert(point);
        }
    }
    constexpr size_t MaximumGlyphs = 16384;
    if (points.size() > MaximumGlyphs)
    {
        error = "Unicode font lists more than " + std::to_string(MaximumGlyphs) + " characters: " + name;
        return std::nullopt;
    }

    std::vector<RenderedGlyph> glyphs;
    glyphs.reserve(points.size());
    size_t missing = 0;
    for (const uint32_t point : points)
    {
        if (FT_Get_Char_Index(face, point) == 0)
        {
            ++missing;
            continue;
        }
        if (FT_Load_Char(face, point, FT_LOAD_TARGET_LIGHT | FT_LOAD_NO_BITMAP) != 0
            || FT_Render_Glyph(face->glyph, FT_RENDER_MODE_NORMAL) != 0
            || (face->glyph->bitmap.rows != 0 && face->glyph->bitmap.pixel_mode != FT_PIXEL_MODE_GRAY))
        {
            error = "Unable to render Unicode glyph U+" + std::to_string(point) + ": " + name;
            return std::nullopt;
        }
        const FT_GlyphSlot pGlyph = face->glyph;
        const FT_Bitmap &bitmap = pGlyph->bitmap;
        RenderedGlyph glyph;
        glyph.point = point;
        glyph.metrics.leftSpacing = pGlyph->bitmap_left;
        glyph.metrics.width = int(bitmap.width);
        glyph.metrics.outlineAdvance = pGlyph->linearHoriAdvance / 65536.0f;
        glyph.metrics.rightSpacing =
            int(std::round(glyph.metrics.outlineAdvance)) - glyph.metrics.leftSpacing - glyph.metrics.width;
        glyph.rows = int(bitmap.rows);
        glyph.top = baseline - pGlyph->bitmap_top;
        glyph.coverage.resize(size_t(bitmap.width) * bitmap.rows);
        for (unsigned int y = 0; y < bitmap.rows; ++y)
        {
            const uint8_t *pRow =
                bitmap.buffer + (bitmap.pitch >= 0 ? y : bitmap.rows - 1 - y) * size_t(std::abs(bitmap.pitch));
            std::copy(pRow, pRow + bitmap.width, glyph.coverage.begin() + size_t(y) * bitmap.width);
        }
        glyphs.push_back(std::move(glyph));
    }

    FontAtlasImage image;
    FontAtlas &atlas = image.atlas;
    atlas.unicode = true;
    atlas.atlasScale = 1;
    atlas.atlasPadding = 2;
    atlas.fontHeight = displayHeight;
    atlas.rasterHeight = rasterHeight;
    atlas.layoutScale = float(displayHeight) / float(rasterHeight);
    const auto [width, height] = packGlyphShelves(glyphs, atlas.atlasPadding, atlas.unicodeGlyphPlacements);
    if (width == 0)
    {
        error = "Unicode font atlas exceeds the texture limit: " + name;
        return std::nullopt;
    }
    atlas.atlasWidth = width;
    atlas.atlasHeight = height;
    allocateAtlas(image, true);
    atlas.unicodeGlyphMetrics.reserve(glyphs.size());
    for (size_t index = 0; index < glyphs.size(); ++index)
    {
        const RenderedGlyph &glyph = glyphs[index];
        const FontGlyphPlacement &place = atlas.unicodeGlyphPlacements[index];
        atlas.unicodeGlyphIndices.emplace(glyph.point, int(index));
        atlas.unicodeGlyphMetrics.push_back(glyph.metrics);
        atlas.atlasCellWidth = std::max(atlas.atlasCellWidth, glyph.metrics.width);
        for (int y = 0; y < glyph.rows; ++y)
        {
            for (int x = 0; x < glyph.metrics.width; ++x)
            {
                const size_t offset = (size_t(place.y + atlas.atlasPadding + y) * size_t(width)
                    + size_t(place.x + atlas.atlasPadding + x)) * 4 + 3;
                const uint8_t value = glyph.coverage[size_t(y) * size_t(glyph.metrics.width) + size_t(x)];
                // As with the other outline faces, the renderer offsets the shadow; its mask is the glyph itself.
                atlas.mainAtlasPixels[offset] = value;
                image.shadowPixels[offset] = value;
            }
        }
    }
    std::cout << "Unicode font: " << name << " raster=" << rasterHeight << " glyphs=" << glyphs.size()
              << " missing=" << missing << " atlas=" << width << 'x' << height << '\n';
    return image;
}
}

int unicodeRasterHeight(int pixelHeight, int logicalHeight)
{
    const int displayHeight = pixelHeight > 0 ? pixelHeight : std::min(3 * logicalHeight, 48);
    for (const int height : {16, 24, 32, 48, 64, 96})
    {
        if (displayHeight <= height)
        {
            return height;
        }
    }
    return 128;
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
    bool unicode = false;
    std::string characterListFile;
    try
    {
        const YAML::Node descriptor = YAML::Load(descriptorText.value_or(""));
        file = descriptor["file"].as<std::string>();
        unicode = descriptor["encoding"].as<std::string>() == "utf-8";
        characterListFile = unicode ? descriptor["characters_file"].as<std::string>("") : "";
        atlas.fontHeight = descriptor["logical_height"].as<int>();
        baseline = descriptor["baseline"].as<int>();
        if (descriptor["weight"])
        {
            weight = descriptor["weight"].as<int>();
        }
        if (descriptor["metrics"].as<std::string>() != "freetype" ||
            (!unicode && descriptor["encoding"].as<std::string>() != "windows-1252") || file.empty() ||
            (unicode && (characterListFile.empty() || characterListFile.find_first_of("/\\") != std::string::npos)) ||
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
    const int rasterHeight = unicode ? unicodeRasterHeight(pixelHeight, logicalHeight) : atlas.fontHeight;
    baseline = int(std::lround(float(baseline) * rasterHeight / logicalHeight));
    atlas.atlasPadding = int(std::ceil(8.0f * atlas.fontHeight / logicalHeight)) + 1;
    const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile("fonts/truetype/" + file);
    FreeTypeFace font;
    atlas.atlasScale = 1;
    atlas.firstChar = 32;
    atlas.lastChar = 255;
    if (!bytes || bytes->empty() || bytes->size() > 32 * 1024 * 1024 || FT_Init_FreeType(&font.library) != 0 ||
        FT_New_Memory_Face(font.library, bytes->data(), FT_Long(bytes->size()), 0, &font.face) != 0 ||
        !FT_IS_SCALABLE(font.face) || FT_Select_Charmap(font.face, FT_ENCODING_UNICODE) != 0 ||
        FT_Set_Pixel_Sizes(font.face, 0, rasterHeight * atlas.atlasScale) != 0)
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
    if (unicode)
    {
        const std::optional<std::string> characterList =
            assetFileSystem.readTextFile("fonts/truetype/" + characterListFile);
        if (!characterList)
        {
            error = "Missing character list of Unicode font: " + characterListFile;
            return std::nullopt;
        }
        return buildUnicodeAtlas(font.face, *characterList, name, atlas.fontHeight, rasterHeight, baseline, error);
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
                    atlas.kerningPairs[uint16_t(previous * 256 + current)] = adjustment.x / (64.0f * atlas.atlasScale);
                }
            }
        }
    }
    atlas.atlasWidth = (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * 16 * atlas.atlasScale;
    atlas.atlasHeight = (atlas.fontHeight + 2 * atlas.atlasPadding) * 16 * atlas.atlasScale;
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
        const int cellX = (character % 16) * width;
        const int cellY = (character / 16) * height;
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
    atlas.fontHeight = bitmap->fontHeight;
    atlas.glyphMetrics = bitmap->glyphMetrics;
    atlas.atlasCellWidth = 1;
    for (int character = atlas.firstChar; character <= atlas.lastChar; ++character)
    {
        atlas.atlasCellWidth = std::max(atlas.atlasCellWidth, atlas.glyphMetrics[character].width);
    }
    atlas.atlasScale = 4;
    // Includes reconstructed italic overhangs (notably Z-caron) and the one-pixel shadow.
    atlas.atlasPadding = 5;
    atlas.atlasWidth = (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * 16 * atlas.atlasScale;
    atlas.atlasHeight = (atlas.fontHeight + 2 * atlas.atlasPadding) * 16 * atlas.atlasScale;
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
        const int cellX = (character % 16) * (atlas.atlasCellWidth + 2 * atlas.atlasPadding) * scale;
        const int cellY = (character / 16) * (atlas.fontHeight + 2 * atlas.atlasPadding) * scale;
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
    return image;
}

std::string utf8ToCp1252(const std::string &text)
{
    std::string result;
    result.reserve(text.size());

    for (size_t index = 0; index < text.size();)
    {
        const uint8_t lead = uint8_t(text[index]);
        const size_t length = lead < 0x80 ? 1 : (lead & 0xe0) == 0xc0 ? 2 : (lead & 0xf0) == 0xe0 ? 3
            : (lead & 0xf8) == 0xf0 ? 4 : 0;

        if (length == 0 || index + length > text.size())
        {
            return text;
        }

        uint32_t point = length == 1 ? lead : lead & (0xff >> (length + 1));

        for (size_t offset = 1; offset < length; ++offset)
        {
            const uint8_t next = uint8_t(text[index + offset]);

            if ((next & 0xc0) != 0x80)
            {
                return text;
            }

            point = (point << 6) | (next & 0x3f);
        }

        index += length;
        char byte = '?';

        if (point < 0x80 || (point >= 0xa0 && point <= 0xff))
        {
            byte = char(point);
        }
        else
        {
            for (int character = 0x80; character < 0xa0; ++character)
            {
                if (cp1252CodePoint(character) == point)
                {
                    byte = char(character);
                    break;
                }
            }
        }

        result.push_back(byte);
    }

    return result;
}
}

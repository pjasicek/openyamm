#include "game/ui/MenuScreenBase.h"
#include "engine/BgfxContext.h"
#include "game/render/TextureFiltering.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
struct PcxHeader
{
    uint8_t manufacturer = 0;
    uint8_t version = 0;
    uint8_t encoding = 0;
    uint8_t bitsPerPixel = 0;
    uint16_t xMin = 0;
    uint16_t yMin = 0;
    uint16_t xMax = 0;
    uint16_t yMax = 0;
    uint16_t hDpi = 0;
    uint16_t vDpi = 0;
    uint8_t colorMap[48] = {};
    uint8_t reserved = 0;
    uint8_t colorPlanes = 0;
    uint16_t bytesPerLine = 0;
    uint16_t paletteType = 0;
    uint16_t hScreenSize = 0;
    uint16_t vScreenSize = 0;
    uint8_t filler[54] = {};
};

struct ParsedFontGlyphMetrics
{
    int leftSpacing = 0;
    int width = 0;
    int rightSpacing = 0;
};

struct ParsedBitmapFont
{
    int firstChar = 0;
    int lastChar = 0;
    int fontHeight = 0;
    std::array<ParsedFontGlyphMetrics, 256> glyphMetrics = {{}};
    std::array<uint32_t, 256> glyphOffsets = {{}};
    std::vector<uint8_t> pixels;
};

std::string toLowerCopy(const std::string &value)
{
    std::string normalized = value;

    for (char &character : normalized)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return normalized;
}

std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName)
{
    std::filesystem::path shaderRoot = OPENYAMM_BGFX_SHADER_DIR;
    std::string rendererDirectory;

    switch (rendererType)
    {
    case bgfx::RendererType::OpenGL:
        rendererDirectory = "glsl";
        break;

    case bgfx::RendererType::OpenGLES:
        rendererDirectory = "essl";
        break;

    case bgfx::RendererType::Vulkan:
        rendererDirectory = "spirv";
        break;

    default:
        return {};
    }

    return shaderRoot / rendererDirectory / (std::string(pShaderName) + ".bin");
}

std::vector<uint8_t> readBinaryFile(const std::filesystem::path &path)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        return {};
    }

    input.seekg(0, std::ios::end);
    const std::streamsize size = input.tellg();
    input.seekg(0, std::ios::beg);

    if (size <= 0)
    {
        return {};
    }

    std::vector<uint8_t> bytes(static_cast<size_t>(size));

    if (!input.read(reinterpret_cast<char *>(bytes.data()), size))
    {
        return {};
    }

    return bytes;
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

bool validateParsedBitmapFont(const ParsedBitmapFont &font, const std::vector<uint8_t> &pixels)
{
    if (font.firstChar < 0 || font.firstChar > 255
        || font.lastChar < 0 || font.lastChar > 255
        || font.firstChar > font.lastChar
        || font.fontHeight <= 0)
    {
        return false;
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const ParsedFontGlyphMetrics &metrics = font.glyphMetrics[glyphIndex];

        if (glyphIndex < font.firstChar || glyphIndex > font.lastChar)
        {
            continue;
        }

        if (metrics.width < 0 || metrics.width > 1024
            || metrics.leftSpacing < -512 || metrics.leftSpacing > 512
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

std::optional<ParsedBitmapFont> parseBitmapFont(const std::vector<uint8_t> &bytes)
{
    constexpr size_t FontHeaderSize = 32;
    constexpr size_t Mm7AtlasSize = 4096;
    constexpr size_t MmxAtlasSize = 1280;

    if (bytes.size() < FontHeaderSize + MmxAtlasSize)
    {
        return std::nullopt;
    }

    const uint8_t *pBytes = bytes.data();

    if (pBytes[2] != 8 || pBytes[3] != 0 || pBytes[4] != 0 || pBytes[6] != 0 || pBytes[7] != 0)
    {
        return std::nullopt;
    }

    ParsedBitmapFont mm7Font = {};
    mm7Font.firstChar = pBytes[0];
    mm7Font.lastChar = pBytes[1];
    mm7Font.fontHeight = pBytes[5];

    if (bytes.size() >= FontHeaderSize + Mm7AtlasSize)
    {
        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t metricOffset = FontHeaderSize + static_cast<size_t>(glyphIndex) * 12;
            mm7Font.glyphMetrics[glyphIndex].leftSpacing = readInt32Le(&pBytes[metricOffset]);
            mm7Font.glyphMetrics[glyphIndex].width = readInt32Le(&pBytes[metricOffset + 4]);
            mm7Font.glyphMetrics[glyphIndex].rightSpacing = readInt32Le(&pBytes[metricOffset + 8]);
        }

        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t offsetPosition = FontHeaderSize + 256 * 12 + static_cast<size_t>(glyphIndex) * 4;
            mm7Font.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
        }

        mm7Font.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(FontHeaderSize + Mm7AtlasSize), bytes.end());

        if (validateParsedBitmapFont(mm7Font, mm7Font.pixels))
        {
            return mm7Font;
        }
    }

    ParsedBitmapFont mmxFont = {};
    mmxFont.firstChar = pBytes[0];
    mmxFont.lastChar = pBytes[1];
    mmxFont.fontHeight = pBytes[5];

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        mmxFont.glyphMetrics[glyphIndex].width = pBytes[FontHeaderSize + glyphIndex];
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const size_t offsetPosition = FontHeaderSize + 256 + static_cast<size_t>(glyphIndex) * 4;
        mmxFont.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
    }

    mmxFont.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(FontHeaderSize + MmxAtlasSize), bytes.end());

    if (!validateParsedBitmapFont(mmxFont, mmxFont.pixels))
    {
        return std::nullopt;
    }

    return mmxFont;
}

bgfx::ShaderHandle loadShader(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        std::cerr << "MenuScreenBase could not read shader: " << shaderPath << '\n';
        return BGFX_INVALID_HANDLE;
    }

    const bgfx::Memory *pMemory = bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size()));
    return bgfx::createShader(pMemory);
}

bgfx::ProgramHandle loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShader = loadShader(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShader = loadShader(pFragmentShaderName);

    if (!bgfx::isValid(vertexShader) || !bgfx::isValid(fragmentShader))
    {
        if (bgfx::isValid(vertexShader))
        {
            bgfx::destroy(vertexShader);
        }

        if (bgfx::isValid(fragmentShader))
        {
            bgfx::destroy(fragmentShader);
        }

        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShader, fragmentShader, true);
}

bool decodePcxRleScanline(const std::vector<uint8_t> &bytes, size_t &offset, std::vector<uint8_t> &scanline)
{
    size_t writeOffset = 0;

    while (writeOffset < scanline.size() && offset < bytes.size())
    {
        uint8_t value = bytes[offset++];
        uint8_t count = 1;

        if ((value & 0xc0) == 0xc0)
        {
            count = value & 0x3f;

            if (offset >= bytes.size())
            {
                return false;
            }

            value = bytes[offset++];
        }

        for (uint8_t repeatIndex = 0; repeatIndex < count && writeOffset < scanline.size(); ++repeatIndex)
        {
            scanline[writeOffset++] = value;
        }
    }

    return writeOffset == scanline.size();
}

std::optional<std::vector<uint8_t>> decodePcxPixelsBgra(const std::vector<uint8_t> &bytes, int &width, int &height)
{
    if (bytes.size() < sizeof(PcxHeader))
    {
        return std::nullopt;
    }

    PcxHeader header = {};
    std::memcpy(&header, bytes.data(), sizeof(PcxHeader));

    if (header.manufacturer != 0x0a || header.encoding != 1 || header.bitsPerPixel != 8)
    {
        return std::nullopt;
    }

    width = static_cast<int>(header.xMax) - static_cast<int>(header.xMin) + 1;
    height = static_cast<int>(header.yMax) - static_cast<int>(header.yMin) + 1;

    if (width <= 0 || height <= 0 || header.bytesPerLine == 0)
    {
        return std::nullopt;
    }

    const size_t scanlineSize = static_cast<size_t>(header.bytesPerLine) * header.colorPlanes;
    size_t offset = sizeof(PcxHeader);
    std::vector<uint8_t> scanline(scanlineSize);
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4, 255);

    std::array<uint8_t, 256 * 3> palette = {};
    const bool hasPalette = header.colorPlanes != 1
        || (bytes.size() >= 769 && bytes[bytes.size() - 769] == 0x0c);

    if (header.colorPlanes == 1)
    {
        if (!hasPalette)
        {
            return std::nullopt;
        }

        std::memcpy(palette.data(), bytes.data() + bytes.size() - 768, 768);
    }

    for (int y = 0; y < height; ++y)
    {
        if (!decodePcxRleScanline(bytes, offset, scanline))
        {
            return std::nullopt;
        }

        for (int x = 0; x < width; ++x)
        {
            const size_t pixelOffset = static_cast<size_t>((y * width + x) * 4);
            uint8_t red = 0;
            uint8_t green = 0;
            uint8_t blue = 0;

            if (header.colorPlanes == 1)
            {
                const size_t paletteOffset = static_cast<size_t>(scanline[static_cast<size_t>(x)]) * 3;
                red = palette[paletteOffset + 0];
                green = palette[paletteOffset + 1];
                blue = palette[paletteOffset + 2];
            }
            else if (header.colorPlanes == 3)
            {
                red = scanline[static_cast<size_t>(x)];
                green = scanline[static_cast<size_t>(header.bytesPerLine) + static_cast<size_t>(x)];
                blue = scanline[static_cast<size_t>(header.bytesPerLine) * 2 + static_cast<size_t>(x)];
            }
            else
            {
                return std::nullopt;
            }

            pixels[pixelOffset + 0] = blue;
            pixels[pixelOffset + 1] = green;
            pixels[pixelOffset + 2] = red;

            const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
            const bool isPinkKey = red >= 248 && green >= 48 && green <= 64 && blue >= 248;
            const bool isTealKey = red <= 8 && green >= 248 && blue >= 248;
            const bool isBlueKey = red <= 8 && green <= 8 && blue >= 248;
            pixels[pixelOffset + 3] = (isMagentaKey || isPinkKey || isTealKey || isBlueKey) ? 0 : 255;
        }
    }

    return pixels;
}

std::optional<std::vector<uint8_t>> loadTexturePixelsBgra(
    const std::vector<uint8_t> &bytes,
    const std::string &path,
    int &width,
    int &height)
{
    const std::string lowerPath = toLowerCopy(path);

    if (lowerPath.size() >= 4 && lowerPath.substr(lowerPath.size() - 4) == ".pcx")
    {
        return decodePcxPixelsBgra(bytes, width, height);
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bytes.data(), bytes.size());

    if (pIoStream == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return std::nullopt;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixels.size());
    SDL_DestroySurface(pConvertedSurface);

    for (size_t pixelOffset = 0; pixelOffset + 3 < pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = pixels[pixelOffset + 0];
        const uint8_t green = pixels[pixelOffset + 1];
        const uint8_t red = pixels[pixelOffset + 2];
        const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
        const bool isPinkKey = red >= 248 && green >= 48 && green <= 64 && blue >= 248;
        const bool isTealKey = red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isPinkKey || isTealKey)
        {
            pixels[pixelOffset + 3] = 0;
        }
    }

    return pixels;
}
}

bgfx::VertexLayout MenuScreenBase::MenuVertex::ms_layout;

void MenuScreenBase::MenuVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
}

MenuScreenBase::MenuScreenBase(const Engine::AssetFileSystem &assetFileSystem)
    : m_pAssetFileSystem(&assetFileSystem)
{
}

MenuScreenBase::~MenuScreenBase()
{
    destroyRendererResources();
}

void MenuScreenBase::renderFrame(
    int width,
    int height,
    const GameplayInputFrame &inputFrame,
    float deltaSeconds)
{
    m_frameWidth = width;
    m_frameHeight = height;
    m_pInputFrame = &inputFrame;
    m_mouseWheelDelta = inputFrame.mouseWheelDelta;
    ensureRendererInitialized();

    m_mouseX = inputFrame.pointerX;
    m_mouseY = inputFrame.pointerY;
    m_leftMouseDown = inputFrame.leftMouseButton.held;
    m_rightMouseDown = inputFrame.rightMouseButton.held;

    bgfx::setViewRect(m_renderViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));

    if (m_clearBackground)
    {
        bgfx::setViewClear(m_renderViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x000000ffu, 1.0f, 0);
    }

    bgfx::touch(m_renderViewId);
    bgfx::dbgTextClear();

    float projectionMatrix[16];
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth);
    bgfx::setViewTransform(m_renderViewId, nullptr, projectionMatrix);

    drawScreen(deltaSeconds);
    m_leftMouseDownPrevious = m_leftMouseDown;
    m_rightMouseDownPrevious = m_rightMouseDown;
    m_pInputFrame = nullptr;
}

const Engine::AssetFileSystem &MenuScreenBase::assetFileSystem() const
{
    return *m_pAssetFileSystem;
}

int MenuScreenBase::frameWidth() const
{
    return m_frameWidth;
}

int MenuScreenBase::frameHeight() const
{
    return m_frameHeight;
}

float MenuScreenBase::mouseX() const
{
    return m_mouseX;
}

float MenuScreenBase::mouseY() const
{
    return m_mouseY;
}

float MenuScreenBase::mouseWheelDelta() const
{
    return m_mouseWheelDelta;
}

bool MenuScreenBase::leftMouseDown() const
{
    return m_leftMouseDown;
}

bool MenuScreenBase::leftMouseJustPressed() const
{
    return m_leftMouseDown && !m_leftMouseDownPrevious;
}

bool MenuScreenBase::leftMouseJustReleased() const
{
    return !m_leftMouseDown && m_leftMouseDownPrevious;
}

bool MenuScreenBase::rightMouseDown() const
{
    return m_rightMouseDown;
}

bool MenuScreenBase::rightMouseJustPressed() const
{
    return m_rightMouseDown && !m_rightMouseDownPrevious;
}

bool MenuScreenBase::rightMouseJustReleased() const
{
    return !m_rightMouseDown && m_rightMouseDownPrevious;
}

bool MenuScreenBase::isScancodeHeld(SDL_Scancode scancode) const
{
    return m_pInputFrame != nullptr && m_pInputFrame->isScancodeHeld(scancode);
}

void MenuScreenBase::setRenderViewId(uint16_t viewId)
{
    m_renderViewId = viewId;
}

void MenuScreenBase::setClearBackground(bool clearBackground)
{
    m_clearBackground = clearBackground;
}

void MenuScreenBase::drawTexture(const std::string &textureName, const Rect &rect)
{
    drawTextureColor(textureName, rect, 0xffffffffu);
}

void MenuScreenBase::drawTextureRegion(const std::string &textureName, const SourceRect &sourceRect, const Rect &rect)
{
    drawTextureRegionColor(textureName, sourceRect, rect, 0xffffffffu);
}

void MenuScreenBase::drawTextureColor(const std::string &textureName, const Rect &rect, uint32_t colorAbgr)
{
    drawTextureRegionColor(textureName, SourceRect{}, rect, colorAbgr);
}

void MenuScreenBase::drawPixelsBgra(
    const std::string &cacheKey,
    int width,
    int height,
    const std::vector<uint8_t> &pixelsBgra,
    const Rect &rect)
{
    if (width <= 0 || height <= 0 || pixelsBgra.empty())
    {
        return;
    }

    const bgfx::TextureHandle textureHandle = ensureDynamicTexture(cacheKey, width, height, pixelsBgra);

    if (!bgfx::isValid(textureHandle))
    {
        return;
    }

    bgfx::TransientVertexBuffer vertexBuffer;
    bgfx::TransientIndexBuffer indexBuffer;

    if (bgfx::getAvailTransientVertexBuffer(4, MenuVertex::ms_layout) < 4
        || bgfx::getAvailTransientIndexBuffer(6) < 6)
    {
        return;
    }

    bgfx::allocTransientVertexBuffer(&vertexBuffer, 4, MenuVertex::ms_layout);
    bgfx::allocTransientIndexBuffer(&indexBuffer, 6);

    MenuVertex *pVertices = reinterpret_cast<MenuVertex *>(vertexBuffer.data);
    const float left = rect.x;
    const float right = rect.x + rect.width;
    const float top = rect.y;
    const float bottom = rect.y + rect.height;
    pVertices[0] = MenuVertex{left, top, 0.0f, 0.0f, 0.0f};
    pVertices[1] = MenuVertex{right, top, 0.0f, 1.0f, 0.0f};
    pVertices[2] = MenuVertex{right, bottom, 0.0f, 1.0f, 1.0f};
    pVertices[3] = MenuVertex{left, bottom, 0.0f, 0.0f, 1.0f};

    uint16_t *pIndices = reinterpret_cast<uint16_t *>(indexBuffer.data);
    pIndices[0] = 0;
    pIndices[1] = 1;
    pIndices[2] = 2;
    pIndices[3] = 0;
    pIndices[4] = 2;
    pIndices[5] = 3;

    bgfx::setVertexBuffer(0, &vertexBuffer);
    bgfx::setIndexBuffer(&indexBuffer);
    bindTexture(
        0,
        m_textureUniformHandle,
        textureHandle,
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    bgfx::submit(m_renderViewId, m_texturedProgramHandle);
}

void MenuScreenBase::drawTextureHandle(bgfx::TextureHandle textureHandle, const Rect &rect)
{
    if (!bgfx::isValid(textureHandle))
    {
        return;
    }

    bgfx::TransientVertexBuffer vertexBuffer;
    bgfx::TransientIndexBuffer indexBuffer;

    if (bgfx::getAvailTransientVertexBuffer(4, MenuVertex::ms_layout) < 4
        || bgfx::getAvailTransientIndexBuffer(6) < 6)
    {
        return;
    }

    bgfx::allocTransientVertexBuffer(&vertexBuffer, 4, MenuVertex::ms_layout);
    bgfx::allocTransientIndexBuffer(&indexBuffer, 6);

    MenuVertex *pVertices = reinterpret_cast<MenuVertex *>(vertexBuffer.data);
    const float left = rect.x;
    const float right = rect.x + rect.width;
    const float top = rect.y;
    const float bottom = rect.y + rect.height;
    pVertices[0] = MenuVertex{left, top, 0.0f, 0.0f, 0.0f};
    pVertices[1] = MenuVertex{right, top, 0.0f, 1.0f, 0.0f};
    pVertices[2] = MenuVertex{right, bottom, 0.0f, 1.0f, 1.0f};
    pVertices[3] = MenuVertex{left, bottom, 0.0f, 0.0f, 1.0f};

    uint16_t *pIndices = reinterpret_cast<uint16_t *>(indexBuffer.data);
    pIndices[0] = 0;
    pIndices[1] = 1;
    pIndices[2] = 2;
    pIndices[3] = 0;
    pIndices[4] = 2;
    pIndices[5] = 3;

    bgfx::setVertexBuffer(0, &vertexBuffer);
    bgfx::setIndexBuffer(&indexBuffer);
    bindTexture(
        0,
        m_textureUniformHandle,
        textureHandle,
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    bgfx::submit(m_renderViewId, m_texturedProgramHandle);
}

void MenuScreenBase::drawTextureRegionColor(
    const std::string &textureName,
    const SourceRect &sourceRect,
    const Rect &rect,
    uint32_t colorAbgr)
{
    const TextureHandle *pTexture = ensureTexture(textureName);

    if (pTexture == nullptr)
    {
        return;
    }

    const bgfx::TextureHandle textureHandle = ensureTextureColor(*pTexture, colorAbgr);

    if (!bgfx::isValid(textureHandle))
    {
        return;
    }

    bgfx::TransientVertexBuffer vertexBuffer;
    bgfx::TransientIndexBuffer indexBuffer;

    if (bgfx::getAvailTransientVertexBuffer(4, MenuVertex::ms_layout) < 4
        || bgfx::getAvailTransientIndexBuffer(6) < 6)
    {
        return;
    }

    bgfx::allocTransientVertexBuffer(&vertexBuffer, 4, MenuVertex::ms_layout);
    bgfx::allocTransientIndexBuffer(&indexBuffer, 6);

    MenuVertex *pVertices = reinterpret_cast<MenuVertex *>(vertexBuffer.data);
    const float left = rect.x;
    const float right = rect.x + rect.width;
    const float top = rect.y;
    const float bottom = rect.y + rect.height;
    const bool useSourceRect = sourceRect.width > 0.0f && sourceRect.height > 0.0f;
    const float u0 = useSourceRect ? sourceRect.x / static_cast<float>(pTexture->width) : 0.0f;
    const float v0 = useSourceRect ? sourceRect.y / static_cast<float>(pTexture->height) : 0.0f;
    const float u1 = useSourceRect ? (sourceRect.x + sourceRect.width) / static_cast<float>(pTexture->width) : 1.0f;
    const float v1 = useSourceRect ? (sourceRect.y + sourceRect.height) / static_cast<float>(pTexture->height) : 1.0f;
    pVertices[0] = MenuVertex{left, top, 0.0f, u0, v0};
    pVertices[1] = MenuVertex{right, top, 0.0f, u1, v0};
    pVertices[2] = MenuVertex{right, bottom, 0.0f, u1, v1};
    pVertices[3] = MenuVertex{left, bottom, 0.0f, u0, v1};

    uint16_t *pIndices = reinterpret_cast<uint16_t *>(indexBuffer.data);
    pIndices[0] = 0;
    pIndices[1] = 1;
    pIndices[2] = 2;
    pIndices[3] = 0;
    pIndices[4] = 2;
    pIndices[5] = 3;

    bgfx::setVertexBuffer(0, &vertexBuffer);
    bgfx::setIndexBuffer(&indexBuffer);
    bindTexture(
        0,
        m_textureUniformHandle,
        textureHandle,
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    bgfx::submit(m_renderViewId, m_texturedProgramHandle);
}

std::optional<MenuScreenBase::TextureSize> MenuScreenBase::textureSize(const std::string &textureName)
{
    const TextureHandle *pTexture = ensureTexture(textureName);

    if (pTexture == nullptr || pTexture->width <= 0 || pTexture->height <= 0)
    {
        return std::nullopt;
    }

    return TextureSize{
        static_cast<float>(pTexture->width),
        static_cast<float>(pTexture->height)
    };
}

bool MenuScreenBase::drawText(
    const std::string &fontName,
    const std::string &text,
    float pixelX,
    float pixelY,
    uint32_t colorAbgr,
    float scale,
    bool drawShadow)
{
    const FontHandle *pFont = ensureFont(fontName);

    if (pFont == nullptr || !bgfx::isValid(pFont->mainTextureHandle))
    {
        return false;
    }

    const bgfx::TextureHandle mainTextureHandle = ensureFontColor(*pFont, colorAbgr);

    if (!bgfx::isValid(mainTextureHandle))
    {
        return false;
    }

    uint32_t glyphCount = 0;

    for (unsigned char character : text)
    {
        if (character == '\r' || character == '\n')
        {
            break;
        }

        if (character >= pFont->firstChar
            && character <= pFont->lastChar
            && pFont->glyphMetrics[character].width > 0)
        {
            ++glyphCount;
        }
    }

    if (glyphCount == 0)
    {
        return true;
    }

    const uint32_t vertexCount = glyphCount * 6;

    if (bgfx::getAvailTransientVertexBuffer(vertexCount, MenuVertex::ms_layout) < vertexCount)
    {
        return false;
    }

    const float shadowOffset = std::max(1.0f, scale);

    if (drawShadow && bgfx::isValid(pFont->shadowTextureHandle))
    {
        bgfx::TransientVertexBuffer shadowBuffer;
        bgfx::allocTransientVertexBuffer(&shadowBuffer, vertexCount, MenuVertex::ms_layout);
        MenuVertex *pShadowVertices = reinterpret_cast<MenuVertex *>(shadowBuffer.data);
        float penX = pixelX + shadowOffset;
        uint32_t vertexIndex = 0;

        for (unsigned char character : text)
        {
            if (character == '\r' || character == '\n')
            {
                break;
            }

            if (character < pFont->firstChar || character > pFont->lastChar)
            {
                penX += static_cast<float>(pFont->atlasCellWidth) * scale;
                continue;
            }

            const FontGlyphMetrics &glyphMetrics = pFont->glyphMetrics[character];
            penX += static_cast<float>(glyphMetrics.leftSpacing) * scale;

            if (glyphMetrics.width > 0)
            {
                const int cellX = (character % 16) * pFont->atlasCellWidth;
                const int cellY = (character / 16) * pFont->fontHeight;
                const float u0 = static_cast<float>(cellX) / static_cast<float>(pFont->atlasWidth);
                const float v0 = static_cast<float>(cellY) / static_cast<float>(pFont->atlasHeight);
                const float u1 = static_cast<float>(cellX + glyphMetrics.width)
                    / static_cast<float>(pFont->atlasWidth);
                const float v1 = static_cast<float>(cellY + pFont->fontHeight)
                    / static_cast<float>(pFont->atlasHeight);
                const float glyphWidth = static_cast<float>(glyphMetrics.width) * scale;
                const float glyphHeight = static_cast<float>(pFont->fontHeight) * scale;
                const float top = pixelY + shadowOffset;
                const float bottom = top + glyphHeight;

                pShadowVertices[vertexIndex + 0] = MenuVertex{penX, top, 0.0f, u0, v0};
                pShadowVertices[vertexIndex + 1] = MenuVertex{penX + glyphWidth, top, 0.0f, u1, v0};
                pShadowVertices[vertexIndex + 2] = MenuVertex{penX + glyphWidth, bottom, 0.0f, u1, v1};
                pShadowVertices[vertexIndex + 3] = MenuVertex{penX, top, 0.0f, u0, v0};
                pShadowVertices[vertexIndex + 4] = MenuVertex{penX + glyphWidth, bottom, 0.0f, u1, v1};
                pShadowVertices[vertexIndex + 5] = MenuVertex{penX, bottom, 0.0f, u0, v1};
                vertexIndex += 6;
            }

            penX += static_cast<float>(glyphMetrics.width + glyphMetrics.rightSpacing) * scale;
        }

        bgfx::setVertexBuffer(0, &shadowBuffer);
        bindTexture(0, m_textureUniformHandle, pFont->shadowTextureHandle, TextureFilterProfile::Text);
        bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
        bgfx::submit(m_renderViewId, m_texturedProgramHandle);
    }

    bgfx::TransientVertexBuffer vertexBuffer;
    bgfx::allocTransientVertexBuffer(&vertexBuffer, vertexCount, MenuVertex::ms_layout);
    MenuVertex *pVertices = reinterpret_cast<MenuVertex *>(vertexBuffer.data);
    float penX = pixelX;
    uint32_t vertexIndex = 0;

    for (unsigned char character : text)
    {
        if (character == '\r' || character == '\n')
        {
            break;
        }

        if (character < pFont->firstChar || character > pFont->lastChar)
        {
            penX += static_cast<float>(pFont->atlasCellWidth) * scale;
            continue;
        }

        const FontGlyphMetrics &glyphMetrics = pFont->glyphMetrics[character];
        penX += static_cast<float>(glyphMetrics.leftSpacing) * scale;

        if (glyphMetrics.width > 0)
        {
            const int cellX = (character % 16) * pFont->atlasCellWidth;
            const int cellY = (character / 16) * pFont->fontHeight;
            const float u0 = static_cast<float>(cellX) / static_cast<float>(pFont->atlasWidth);
            const float v0 = static_cast<float>(cellY) / static_cast<float>(pFont->atlasHeight);
            const float u1 = static_cast<float>(cellX + glyphMetrics.width) / static_cast<float>(pFont->atlasWidth);
            const float v1 = static_cast<float>(cellY + pFont->fontHeight) / static_cast<float>(pFont->atlasHeight);
            const float glyphWidth = static_cast<float>(glyphMetrics.width) * scale;
            const float glyphHeight = static_cast<float>(pFont->fontHeight) * scale;
            const float bottom = pixelY + glyphHeight;

            pVertices[vertexIndex + 0] = MenuVertex{penX, pixelY, 0.0f, u0, v0};
            pVertices[vertexIndex + 1] = MenuVertex{penX + glyphWidth, pixelY, 0.0f, u1, v0};
            pVertices[vertexIndex + 2] = MenuVertex{penX + glyphWidth, bottom, 0.0f, u1, v1};
            pVertices[vertexIndex + 3] = MenuVertex{penX, pixelY, 0.0f, u0, v0};
            pVertices[vertexIndex + 4] = MenuVertex{penX + glyphWidth, bottom, 0.0f, u1, v1};
            pVertices[vertexIndex + 5] = MenuVertex{penX, bottom, 0.0f, u0, v1};
            vertexIndex += 6;
        }

        penX += static_cast<float>(glyphMetrics.width + glyphMetrics.rightSpacing) * scale;
    }

    bgfx::setVertexBuffer(0, &vertexBuffer);
    bindTexture(0, m_textureUniformHandle, mainTextureHandle, TextureFilterProfile::Text);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    bgfx::submit(m_renderViewId, m_texturedProgramHandle);
    return true;
}

float MenuScreenBase::measureTextWidth(const std::string &fontName, const std::string &text, float scale)
{
    const FontHandle *pFont = ensureFont(fontName);

    if (pFont == nullptr)
    {
        return 0.0f;
    }

    float widthPixels = 0.0f;

    for (unsigned char character : text)
    {
        if (character == '\r' || character == '\n')
        {
            break;
        }

        if (character < pFont->firstChar || character > pFont->lastChar)
        {
            widthPixels += static_cast<float>(pFont->atlasCellWidth) * scale;
            continue;
        }

        const FontGlyphMetrics &glyphMetrics = pFont->glyphMetrics[character];
        widthPixels += static_cast<float>(
            glyphMetrics.leftSpacing
            + glyphMetrics.width
            + glyphMetrics.rightSpacing) * scale;
    }

    return widthPixels;
}

int MenuScreenBase::fontHeight(const std::string &fontName)
{
    const FontHandle *pFont = ensureFont(fontName);
    return pFont != nullptr ? pFont->fontHeight : 0;
}

MenuScreenBase::ButtonState MenuScreenBase::drawButton(const ButtonVisualSet &visuals, const Rect &rect)
{
    ButtonState state = {};
    state.hovered = hitTest(rect);
    state.pressed = state.hovered && leftMouseDown();
    state.clicked = state.hovered && leftMouseJustReleased();

    const std::string *pTextureName = &visuals.defaultTextureName;

    if (state.pressed && !visuals.pressedTextureName.empty())
    {
        pTextureName = &visuals.pressedTextureName;
    }
    else if (state.hovered && !visuals.highlightedTextureName.empty())
    {
        pTextureName = &visuals.highlightedTextureName;
    }

    if (!pTextureName->empty())
    {
        drawTexture(*pTextureName, rect);
    }

    return state;
}

void MenuScreenBase::drawDebugText(int pixelX, int pixelY, uint8_t color, const std::string &text) const
{
    bgfx::dbgTextPrintf(
        static_cast<uint16_t>(std::max(0, pixelX / 8)),
        static_cast<uint16_t>(std::max(0, pixelY / 16)),
        color,
        "%s",
        text.c_str());
}

bool MenuScreenBase::hitTest(const Rect &rect) const
{
    return m_mouseX >= rect.x && m_mouseX < rect.x + rect.width
        && m_mouseY >= rect.y && m_mouseY < rect.y + rect.height;
}

void MenuScreenBase::drawViewportSidePanels(const std::string &textureName, float logicalWidth, float logicalHeight)
{
    if (m_frameWidth <= 0 || m_frameHeight <= 0 || logicalWidth <= 0.0f || logicalHeight <= 0.0f)
    {
        return;
    }

    const float baseScale = std::min(
        static_cast<float>(m_frameWidth) / logicalWidth,
        static_cast<float>(m_frameHeight) / logicalHeight);
    const float viewportWidth = logicalWidth * baseScale;
    const float viewportX = (static_cast<float>(m_frameWidth) - viewportWidth) * 0.5f;

    if (viewportX <= 0.5f)
    {
        return;
    }

    drawTexture(
        textureName,
        Rect{
            0.0f,
            0.0f,
            viewportX,
            static_cast<float>(m_frameHeight)
        });

    const float rightX = viewportX + viewportWidth;
    const float rightWidth = static_cast<float>(m_frameWidth) - rightX;

    if (rightWidth > 0.5f)
    {
        drawTexture(
            textureName,
            Rect{
                rightX,
                0.0f,
                rightWidth,
                static_cast<float>(m_frameHeight)
            });
    }
}

void MenuScreenBase::ensureRendererInitialized()
{
    if (m_rendererInitialized)
    {
        return;
    }

    MenuVertex::init();
    m_textureUniformHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);
    m_texturedProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_shadowmaps_texture");
    m_rendererInitialized = bgfx::isValid(m_textureUniformHandle) && bgfx::isValid(m_texturedProgramHandle);

    if (!m_rendererInitialized)
    {
        std::cerr << "MenuScreenBase renderer initialization failed\n";
    }
}

void MenuScreenBase::destroyRendererResources()
{
    if (!Engine::BgfxContext::isBgfxInitialized())
    {
        m_textureHandles.clear();
        m_textureIndexByName.clear();
        m_resolvedTexturePaths.clear();
        m_textureColorHandles.clear();
        m_dynamicTextureHandles.clear();
        m_fontHandles.clear();
        m_fontIndexByName.clear();
        m_resolvedFontPaths.clear();
        m_fontColorHandles.clear();
        m_texturedProgramHandle = BGFX_INVALID_HANDLE;
        m_textureUniformHandle = BGFX_INVALID_HANDLE;
        m_rendererInitialized = false;
        return;
    }

    for (TextureHandle &textureHandle : m_textureHandles)
    {
        if (bgfx::isValid(textureHandle.handle))
        {
            bgfx::destroy(textureHandle.handle);
            textureHandle.handle = BGFX_INVALID_HANDLE;
        }
    }

    m_textureHandles.clear();
    m_textureIndexByName.clear();
    m_resolvedTexturePaths.clear();

    for (TextureColorHandle &textureColorHandle : m_textureColorHandles)
    {
        if (bgfx::isValid(textureColorHandle.handle))
        {
            bgfx::destroy(textureColorHandle.handle);
            textureColorHandle.handle = BGFX_INVALID_HANDLE;
        }
    }

    m_textureColorHandles.clear();

    for (DynamicTextureHandle &textureHandle : m_dynamicTextureHandles)
    {
        if (bgfx::isValid(textureHandle.handle))
        {
            bgfx::destroy(textureHandle.handle);
            textureHandle.handle = BGFX_INVALID_HANDLE;
        }
    }

    m_dynamicTextureHandles.clear();

    for (FontHandle &fontHandle : m_fontHandles)
    {
        if (bgfx::isValid(fontHandle.mainTextureHandle))
        {
            bgfx::destroy(fontHandle.mainTextureHandle);
            fontHandle.mainTextureHandle = BGFX_INVALID_HANDLE;
        }

        if (bgfx::isValid(fontHandle.shadowTextureHandle))
        {
            bgfx::destroy(fontHandle.shadowTextureHandle);
            fontHandle.shadowTextureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_fontHandles.clear();
    m_fontIndexByName.clear();
    m_resolvedFontPaths.clear();

    for (FontColorHandle &fontColorHandle : m_fontColorHandles)
    {
        if (bgfx::isValid(fontColorHandle.handle))
        {
            bgfx::destroy(fontColorHandle.handle);
            fontColorHandle.handle = BGFX_INVALID_HANDLE;
        }
    }

    m_fontColorHandles.clear();

    if (bgfx::isValid(m_texturedProgramHandle))
    {
        bgfx::destroy(m_texturedProgramHandle);
        m_texturedProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_textureUniformHandle))
    {
        bgfx::destroy(m_textureUniformHandle);
        m_textureUniformHandle = BGFX_INVALID_HANDLE;
    }

    m_rendererInitialized = false;
}

const MenuScreenBase::TextureHandle *MenuScreenBase::findTexture(const std::string &textureName) const
{
    const std::string normalized = toLowerCopy(textureName);
    const std::unordered_map<std::string, size_t>::const_iterator it = m_textureIndexByName.find(normalized);
    return it != m_textureIndexByName.end() ? &m_textureHandles[it->second] : nullptr;
}

const MenuScreenBase::TextureHandle *MenuScreenBase::ensureTexture(const std::string &textureName)
{
    if (const TextureHandle *pExisting = findTexture(textureName))
    {
        return pExisting;
    }

    const std::optional<std::string> resolvedPath = resolveTexturePath(textureName);

    if (!resolvedPath)
    {
        std::cerr << "MenuScreenBase could not resolve texture: " << textureName << '\n';
        return nullptr;
    }

    const std::optional<std::vector<uint8_t>> bytes = m_pAssetFileSystem->readBinaryFile(*resolvedPath);

    if (!bytes || bytes->empty())
    {
        std::cerr << "MenuScreenBase could not read texture bytes: " << *resolvedPath << '\n';
        return nullptr;
    }

    int width = 0;
    int height = 0;
    const std::optional<std::vector<uint8_t>> pixels = loadTexturePixelsBgra(*bytes, *resolvedPath, width, height);

    if (!pixels || width <= 0 || height <= 0)
    {
        std::cerr << "MenuScreenBase could not decode texture: " << *resolvedPath << '\n';
        return nullptr;
    }

    TextureHandle textureHandle = {};
    textureHandle.normalizedTextureName = toLowerCopy(textureName);
    textureHandle.width = Engine::scalePhysicalPixelsToLogical(width, m_pAssetFileSystem->getAssetScaleTier());
    textureHandle.height = Engine::scalePhysicalPixelsToLogical(height, m_pAssetFileSystem->getAssetScaleTier());
    textureHandle.physicalWidth = width;
    textureHandle.physicalHeight = height;
    textureHandle.bgraPixels = *pixels;
    textureHandle.handle = createBgraTexture2D(
        uint16_t(width),
        uint16_t(height),
        textureHandle.bgraPixels.data(),
        uint32_t(textureHandle.bgraPixels.size()),
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
    );

    if (!bgfx::isValid(textureHandle.handle))
    {
        std::cerr << "MenuScreenBase could not create bgfx texture: "
                  << *resolvedPath
                  << " size="
                  << width
                  << "x"
                  << height
                  << '\n';
        return nullptr;
    }

    m_textureHandles.push_back(std::move(textureHandle));
    m_textureIndexByName[m_textureHandles.back().normalizedTextureName] = m_textureHandles.size() - 1;
    return &m_textureHandles.back();
}

const MenuScreenBase::FontHandle *MenuScreenBase::findFont(const std::string &fontName) const
{
    const std::string normalized = toLowerCopy(fontName);
    const std::unordered_map<std::string, size_t>::const_iterator it = m_fontIndexByName.find(normalized);
    return it != m_fontIndexByName.end() ? &m_fontHandles[it->second] : nullptr;
}

const MenuScreenBase::FontHandle *MenuScreenBase::ensureFont(const std::string &fontName)
{
    if (const FontHandle *pExisting = findFont(fontName))
    {
        return pExisting;
    }

    const std::optional<std::string> resolvedPath = resolveFontPath(fontName);

    if (!resolvedPath)
    {
        return nullptr;
    }

    const std::optional<std::vector<uint8_t>> bytes = m_pAssetFileSystem->readBinaryFile(*resolvedPath);

    if (!bytes || bytes->empty())
    {
        return nullptr;
    }

    const std::optional<ParsedBitmapFont> parsedFont = parseBitmapFont(*bytes);

    if (!parsedFont)
    {
        return nullptr;
    }

    int atlasCellWidth = 1;

    for (const ParsedFontGlyphMetrics &metrics : parsedFont->glyphMetrics)
    {
        atlasCellWidth = std::max(atlasCellWidth, metrics.width);
    }

    const int atlasWidth = atlasCellWidth * 16;
    const int atlasHeight = parsedFont->fontHeight * 16;

    if (atlasWidth <= 0 || atlasHeight <= 0)
    {
        return nullptr;
    }

    std::vector<uint8_t> mainPixels(static_cast<size_t>(atlasWidth) * static_cast<size_t>(atlasHeight) * 4, 0);
    std::vector<uint8_t> shadowPixels(static_cast<size_t>(atlasWidth) * static_cast<size_t>(atlasHeight) * 4, 0);

    for (int glyphIndex = parsedFont->firstChar; glyphIndex <= parsedFont->lastChar; ++glyphIndex)
    {
        const ParsedFontGlyphMetrics &metrics = parsedFont->glyphMetrics[glyphIndex];

        if (metrics.width <= 0)
        {
            continue;
        }

        const int cellX = (glyphIndex % 16) * atlasCellWidth;
        const int cellY = (glyphIndex / 16) * parsedFont->fontHeight;
        const size_t glyphOffset = parsedFont->glyphOffsets[glyphIndex];

        for (int y = 0; y < parsedFont->fontHeight; ++y)
        {
            for (int x = 0; x < metrics.width; ++x)
            {
                const uint8_t pixelValue =
                    parsedFont->pixels[glyphOffset + static_cast<size_t>(y) * static_cast<size_t>(metrics.width) + x];

                if (pixelValue == 0)
                {
                    continue;
                }

                const size_t atlasPixelIndex =
                    (static_cast<size_t>(cellY + y) * static_cast<size_t>(atlasWidth) + static_cast<size_t>(cellX + x))
                    * 4;
                std::vector<uint8_t> &targetPixels = (pixelValue == 1) ? shadowPixels : mainPixels;
                targetPixels[atlasPixelIndex + 0] = (pixelValue == 1) ? 0 : 255;
                targetPixels[atlasPixelIndex + 1] = (pixelValue == 1) ? 0 : 255;
                targetPixels[atlasPixelIndex + 2] = (pixelValue == 1) ? 0 : 255;
                targetPixels[atlasPixelIndex + 3] = 255;
            }
        }
    }

    FontHandle fontHandle = {};
    fontHandle.normalizedFontName = toLowerCopy(fontName);
    fontHandle.firstChar = parsedFont->firstChar;
    fontHandle.lastChar = parsedFont->lastChar;
    fontHandle.fontHeight = parsedFont->fontHeight;
    fontHandle.atlasCellWidth = atlasCellWidth;
    fontHandle.atlasWidth = atlasWidth;
    fontHandle.atlasHeight = atlasHeight;
    fontHandle.mainAtlasPixels = mainPixels;

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        fontHandle.glyphMetrics[glyphIndex].leftSpacing = parsedFont->glyphMetrics[glyphIndex].leftSpacing;
        fontHandle.glyphMetrics[glyphIndex].width = parsedFont->glyphMetrics[glyphIndex].width;
        fontHandle.glyphMetrics[glyphIndex].rightSpacing = parsedFont->glyphMetrics[glyphIndex].rightSpacing;
    }

    fontHandle.mainTextureHandle = createBgraTexture2D(
        uint16_t(atlasWidth),
        uint16_t(atlasHeight),
        mainPixels.data(),
        uint32_t(mainPixels.size()),
        TextureFilterProfile::Text,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
    );
    fontHandle.shadowTextureHandle = createBgraTexture2D(
        uint16_t(atlasWidth),
        uint16_t(atlasHeight),
        shadowPixels.data(),
        uint32_t(shadowPixels.size()),
        TextureFilterProfile::Text,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
    );

    if (!bgfx::isValid(fontHandle.mainTextureHandle) || !bgfx::isValid(fontHandle.shadowTextureHandle))
    {
        if (bgfx::isValid(fontHandle.mainTextureHandle))
        {
            bgfx::destroy(fontHandle.mainTextureHandle);
        }

        if (bgfx::isValid(fontHandle.shadowTextureHandle))
        {
            bgfx::destroy(fontHandle.shadowTextureHandle);
        }

        return nullptr;
    }

    m_fontHandles.push_back(std::move(fontHandle));
    m_fontIndexByName[m_fontHandles.back().normalizedFontName] = m_fontHandles.size() - 1;
    return &m_fontHandles.back();
}

bgfx::TextureHandle MenuScreenBase::ensureDynamicTexture(
    const std::string &cacheKey,
    int width,
    int height,
    const std::vector<uint8_t> &pixelsBgra)
{
    if (width <= 0 || height <= 0 || pixelsBgra.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    for (DynamicTextureHandle &textureHandle : m_dynamicTextureHandles)
    {
        if (textureHandle.cacheKey != cacheKey)
        {
            continue;
        }

        if (!bgfx::isValid(textureHandle.handle)
            || textureHandle.width != width
            || textureHandle.height != height)
        {
            if (bgfx::isValid(textureHandle.handle))
            {
                bgfx::destroy(textureHandle.handle);
            }

            textureHandle.width = width;
            textureHandle.height = height;
            textureHandle.handle = createEmptyBgraTexture2D(
                uint16_t(width),
                uint16_t(height),
                TextureFilterProfile::Ui,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_TEXTURE_BLIT_DST);
        }

        if (!bgfx::isValid(textureHandle.handle))
        {
            return BGFX_INVALID_HANDLE;
        }

        bgfx::updateTexture2D(
            textureHandle.handle,
            0,
            0,
            0,
            0,
            static_cast<uint16_t>(width),
            static_cast<uint16_t>(height),
            bgfx::copy(pixelsBgra.data(), static_cast<uint32_t>(pixelsBgra.size())));
        return textureHandle.handle;
    }

    DynamicTextureHandle textureHandle = {};
    textureHandle.cacheKey = cacheKey;
    textureHandle.width = width;
    textureHandle.height = height;
    textureHandle.handle = createEmptyBgraTexture2D(
        uint16_t(width),
        uint16_t(height),
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_TEXTURE_BLIT_DST);

    if (!bgfx::isValid(textureHandle.handle))
    {
        return BGFX_INVALID_HANDLE;
    }

    bgfx::updateTexture2D(
        textureHandle.handle,
        0,
        0,
        0,
        0,
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        bgfx::copy(pixelsBgra.data(), static_cast<uint32_t>(pixelsBgra.size())));
    m_dynamicTextureHandles.push_back(std::move(textureHandle));
    return m_dynamicTextureHandles.back().handle;
}

bgfx::TextureHandle MenuScreenBase::ensureTextureColor(const TextureHandle &texture, uint32_t colorAbgr)
{
    if (colorAbgr == 0xffffffffu)
    {
        return texture.handle;
    }

    for (const TextureColorHandle &textureColorHandle : m_textureColorHandles)
    {
        if (textureColorHandle.normalizedTextureName == texture.normalizedTextureName
            && textureColorHandle.colorAbgr == colorAbgr)
        {
            return textureColorHandle.handle;
        }
    }

    if (texture.bgraPixels.empty() || texture.physicalWidth <= 0 || texture.physicalHeight <= 0)
    {
        return BGFX_INVALID_HANDLE;
    }

    std::vector<uint8_t> tintedPixels = texture.bgraPixels;
    const uint8_t red = static_cast<uint8_t>(colorAbgr & 0xff);
    const uint8_t green = static_cast<uint8_t>((colorAbgr >> 8) & 0xff);
    const uint8_t blue = static_cast<uint8_t>((colorAbgr >> 16) & 0xff);
    const uint8_t alpha = static_cast<uint8_t>((colorAbgr >> 24) & 0xff);

    for (size_t pixelIndex = 0; pixelIndex + 3 < tintedPixels.size(); pixelIndex += 4)
    {
        const uint8_t sourceAlpha = tintedPixels[pixelIndex + 3];

        if (sourceAlpha == 0)
        {
            continue;
        }

        tintedPixels[pixelIndex + 0] =
            static_cast<uint8_t>((static_cast<uint32_t>(tintedPixels[pixelIndex + 0]) * blue) / 255u);
        tintedPixels[pixelIndex + 1] =
            static_cast<uint8_t>((static_cast<uint32_t>(tintedPixels[pixelIndex + 1]) * green) / 255u);
        tintedPixels[pixelIndex + 2] =
            static_cast<uint8_t>((static_cast<uint32_t>(tintedPixels[pixelIndex + 2]) * red) / 255u);
        tintedPixels[pixelIndex + 3] = static_cast<uint8_t>((static_cast<uint32_t>(sourceAlpha) * alpha) / 255u);
    }

    const bgfx::TextureHandle textureHandle = createBgraTexture2D(
        uint16_t(texture.physicalWidth),
        uint16_t(texture.physicalHeight),
        tintedPixels.data(),
        uint32_t(tintedPixels.size()),
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
    );

    if (!bgfx::isValid(textureHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    TextureColorHandle textureColorHandle = {};
    textureColorHandle.normalizedTextureName = texture.normalizedTextureName;
    textureColorHandle.colorAbgr = colorAbgr;
    textureColorHandle.handle = textureHandle;
    m_textureColorHandles.push_back(std::move(textureColorHandle));
    return m_textureColorHandles.back().handle;
}

bgfx::TextureHandle MenuScreenBase::ensureFontColor(const FontHandle &font, uint32_t colorAbgr)
{
    if (colorAbgr == 0xffffffffu)
    {
        return font.mainTextureHandle;
    }

    for (const FontColorHandle &fontColorHandle : m_fontColorHandles)
    {
        if (fontColorHandle.normalizedFontName == font.normalizedFontName
            && fontColorHandle.colorAbgr == colorAbgr)
        {
            return fontColorHandle.handle;
        }
    }

    if (font.mainAtlasPixels.empty() || font.atlasWidth <= 0 || font.atlasHeight <= 0)
    {
        return BGFX_INVALID_HANDLE;
    }

    std::vector<uint8_t> tintedPixels = font.mainAtlasPixels;
    const uint8_t red = static_cast<uint8_t>(colorAbgr & 0xff);
    const uint8_t green = static_cast<uint8_t>((colorAbgr >> 8) & 0xff);
    const uint8_t blue = static_cast<uint8_t>((colorAbgr >> 16) & 0xff);
    const uint8_t alpha = static_cast<uint8_t>((colorAbgr >> 24) & 0xff);

    for (size_t pixelIndex = 0; pixelIndex + 3 < tintedPixels.size(); pixelIndex += 4)
    {
        const uint8_t sourceAlpha = tintedPixels[pixelIndex + 3];

        if (sourceAlpha == 0)
        {
            continue;
        }

        tintedPixels[pixelIndex + 0] =
            static_cast<uint8_t>((static_cast<uint32_t>(tintedPixels[pixelIndex + 0]) * blue) / 255u);
        tintedPixels[pixelIndex + 1] =
            static_cast<uint8_t>((static_cast<uint32_t>(tintedPixels[pixelIndex + 1]) * green) / 255u);
        tintedPixels[pixelIndex + 2] =
            static_cast<uint8_t>((static_cast<uint32_t>(tintedPixels[pixelIndex + 2]) * red) / 255u);
        tintedPixels[pixelIndex + 3] = static_cast<uint8_t>((static_cast<uint32_t>(sourceAlpha) * alpha) / 255u);
    }

    const bgfx::TextureHandle textureHandle = createBgraTexture2D(
        uint16_t(font.atlasWidth),
        uint16_t(font.atlasHeight),
        tintedPixels.data(),
        uint32_t(tintedPixels.size()),
        TextureFilterProfile::Text,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
    );

    if (!bgfx::isValid(textureHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    FontColorHandle fontColorHandle = {};
    fontColorHandle.normalizedFontName = font.normalizedFontName;
    fontColorHandle.colorAbgr = colorAbgr;
    fontColorHandle.handle = textureHandle;
    m_fontColorHandles.push_back(std::move(fontColorHandle));
    return m_fontColorHandles.back().handle;
}

std::optional<std::string> MenuScreenBase::resolveTexturePath(const std::string &textureName)
{
    const std::string normalizedName = toLowerCopy(textureName);
    const auto cachedIt = m_resolvedTexturePaths.find(normalizedName);

    if (cachedIt != m_resolvedTexturePaths.end())
    {
        return cachedIt->second;
    }

    const std::array<std::string, 1> directories = {
        "Data/icons"
    };
    const std::array<std::string, 2> extensions = {
        ".bmp",
        ".pcx"
    };

    for (const std::string &directory : directories)
    {
        auto entriesIt = m_directoryEntriesByPath.find(directory);

        if (entriesIt == m_directoryEntriesByPath.end())
        {
            std::unordered_map<std::string, std::string> entries;

            for (const std::string &entry : m_pAssetFileSystem->enumerate(directory))
            {
                entries.emplace(toLowerCopy(entry), directory + "/" + entry);
            }

            entriesIt = m_directoryEntriesByPath.emplace(directory, std::move(entries)).first;
        }

        for (const std::string &extension : extensions)
        {
            const auto resolvedIt = entriesIt->second.find(normalizedName + extension);

            if (resolvedIt != entriesIt->second.end())
            {
                m_resolvedTexturePaths[normalizedName] = resolvedIt->second;
                return resolvedIt->second;
            }
        }
    }

    m_resolvedTexturePaths[normalizedName] = std::nullopt;
    return std::nullopt;
}

std::optional<std::string> MenuScreenBase::resolveFontPath(const std::string &fontName)
{
    const std::string normalizedName = toLowerCopy(fontName);
    const std::unordered_map<std::string, std::optional<std::string>>::const_iterator cachedIt =
        m_resolvedFontPaths.find(normalizedName);

    if (cachedIt != m_resolvedFontPaths.end())
    {
        return cachedIt->second;
    }

    const std::array<std::string, 2> directories = {
        "Data/icons",
        "Data/EnglishT"
    };

    for (const std::string &directory : directories)
    {
        std::unordered_map<std::string, std::unordered_map<std::string, std::string>>::iterator entriesIt =
            m_directoryEntriesByPath.find(directory);

        if (entriesIt == m_directoryEntriesByPath.end())
        {
            std::unordered_map<std::string, std::string> entries;

            for (const std::string &entry : m_pAssetFileSystem->enumerate(directory))
            {
                entries.emplace(toLowerCopy(entry), directory + "/" + entry);
            }

            entriesIt = m_directoryEntriesByPath.emplace(directory, std::move(entries)).first;
        }

        const std::unordered_map<std::string, std::string>::const_iterator resolvedIt =
            entriesIt->second.find(normalizedName + ".fnt");

        if (resolvedIt != entriesIt->second.end())
        {
            m_resolvedFontPaths[normalizedName] = resolvedIt->second;
            return resolvedIt->second;
        }
    }

    m_resolvedFontPaths[normalizedName] = std::nullopt;
    return std::nullopt;
}
}

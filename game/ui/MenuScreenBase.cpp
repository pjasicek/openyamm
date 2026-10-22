#include "game/ui/MenuScreenBase.h"
#include "engine/BgfxContext.h"
#include "engine/ImageAssetLoader.h"
#include "engine/render/CookedTexture.h"
#include "game/render/TextureFiltering.h"
#include "game/ui/UiLayoutManager.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <cmath>
#include <array>
#include <cctype>
#include <cstdint>
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
std::string toLowerCopy(const std::string &value)
{
    std::string normalized = value;

    for (char &character : normalized)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return normalized;
}

bool isIndependentOutlineFont(const std::string &fontName)
{
    const std::string name = toLowerCopy(fontName);
    return name.starts_with("menu_") || name == "fondamento";
}

std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName)
{
    const std::filesystem::path configuredShaderRoot = OPENYAMM_BGFX_SHADER_DIR;
    std::string rendererDirectory;

    switch (rendererType)
    {
    case bgfx::RendererType::Direct3D11:
        rendererDirectory = "dxbc";
        break;

    case bgfx::RendererType::OpenGL:
        rendererDirectory = "glsl";
        break;

    case bgfx::RendererType::OpenGLES:
        rendererDirectory = "essl";
        break;

    case bgfx::RendererType::Vulkan:
        rendererDirectory = "spirv";
        break;

    case bgfx::RendererType::Metal:
        rendererDirectory = "metal";
        break;

    default:
        return {};
    }

    const std::filesystem::path shaderName =
        std::filesystem::path(rendererDirectory) / (std::string(pShaderName) + ".bin");

    if (configuredShaderRoot.is_absolute())
    {
        return configuredShaderRoot / shaderName;
    }

    if (const char *pBasePath = SDL_GetBasePath())
    {
        const std::filesystem::path executableRoot = pBasePath;
        const std::filesystem::path packagedPath = executableRoot / configuredShaderRoot / shaderName;

        if (std::filesystem::exists(packagedPath))
        {
            return packagedPath;
        }

        const std::filesystem::path buildTreePath = executableRoot / ".." / configuredShaderRoot / shaderName;

        if (std::filesystem::exists(buildTreePath))
        {
            return buildTreePath;
        }

        return packagedPath;
    }

    return configuredShaderRoot / shaderName;
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

std::optional<std::vector<uint8_t>> loadTexturePixelsBgra(
    const std::vector<uint8_t> &bytes,
    const std::string &path,
    int &width,
    int &height)
{
    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.applyMagentaTransparencyKey = true;
    decodeOptions.applyTealTransparencyKey = true;
    std::optional<Engine::ImagePixelsBgra> image = Engine::decodeImagePixelsBgra(bytes, path, decodeOptions);

    if (!image)
    {
        return std::nullopt;
    }

    // Preserve legacy menu color keys, including PNG replacements with PCX/BMP names.
    const std::string lowerPath = toLowerCopy(path);
    const bool isPcx = lowerPath.ends_with(".pcx");
    const bool isBmp = lowerPath.ends_with(".bmp");
    if (isPcx || isBmp)
    {
        for (size_t offset = 0; offset < image->pixels.size(); offset += 4)
        {
            const uint8_t blue = image->pixels[offset];
            const uint8_t green = image->pixels[offset + 1];
            const uint8_t red = image->pixels[offset + 2];
            const bool isPinkKey = red >= 248 && green >= 48 && green <= 64 && blue >= 248;
            const bool isBlueKey = isPcx && red <= 8 && green <= 8 && blue >= 248;
            if (isPinkKey || isBlueKey)
            {
                image->pixels[offset + 3] = 0;
            }
        }
    }

    width = image->width;
    height = image->height;
    return std::move(image->pixels);
}
}

bgfx::VertexLayout MenuScreenBase::MenuVertex::ms_layout;
std::vector<MenuScreenBase::TextureHandle> MenuScreenBase::s_textureHandles;
std::vector<MenuScreenBase::DynamicTextureHandle> MenuScreenBase::s_dynamicTextureHandles;
std::unordered_map<std::string, size_t> MenuScreenBase::s_textureIndexByName;
int MenuScreenBase::s_fontFrameWidth = 0;
int MenuScreenBase::s_fontFrameHeight = 0;
std::unordered_map<std::string, std::unordered_map<std::string, std::string>>
    MenuScreenBase::s_directoryEntriesByPath;
std::unordered_map<std::string, std::optional<std::string>> MenuScreenBase::s_resolvedTexturePaths;
uint64_t MenuScreenBase::s_assetContentGeneration = 0;

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

void MenuScreenBase::shutdownSharedResources()
{
    releaseSharedTextures();
    SharedFontCache::release(Engine::BgfxContext::isBgfxInitialized());
}

void MenuScreenBase::releaseSharedTextures()
{
    const bool destroyGpu = Engine::BgfxContext::isBgfxInitialized();

    for (TextureHandle &textureHandle : s_textureHandles)
    {
        if (destroyGpu && bgfx::isValid(textureHandle.handle))
        {
            bgfx::destroy(textureHandle.handle);
        }
    }

    for (DynamicTextureHandle &textureHandle : s_dynamicTextureHandles)
    {
        if (destroyGpu && bgfx::isValid(textureHandle.handle))
        {
            bgfx::destroy(textureHandle.handle);
        }
    }

    s_textureHandles.clear();
    s_textureIndexByName.clear();
    s_resolvedTexturePaths.clear();
    s_dynamicTextureHandles.clear();
    s_directoryEntriesByPath.clear();
}

void MenuScreenBase::releaseTexturesIfAssetsChanged()
{
    // Menu art lives for the whole run; a world switch or an asset edit changes what its names resolve to.
    if (m_pAssetFileSystem != nullptr && m_pAssetFileSystem->contentGeneration() != s_assetContentGeneration)
    {
        releaseSharedTextures();
        s_assetContentGeneration = m_pAssetFileSystem->contentGeneration();
    }
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
    releaseTexturesIfAssetsChanged();
    resizeFontCache(width, height);

    m_mouseX = inputFrame.pointerX;
    m_mouseY = inputFrame.pointerY;
    m_leftMouseDown = inputFrame.leftMouseButton.held;
    m_rightMouseDown = inputFrame.rightMouseButton.held;

    bgfx::setViewRect(m_renderViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));

    bgfx::setViewMode(m_renderViewId, bgfx::ViewMode::Sequential);
    bgfx::setViewClear(m_renderViewId, m_clearBackground ? BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH : BGFX_CLEAR_NONE,
                       0x000000ffu, 1.0f, 0);

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

const GameplayInputFrame &MenuScreenBase::inputFrame() const
{
    return *m_pInputFrame;
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

    m_drawTint = 0xffffffffu;
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
    applyClipRect();
    bgfx::submit(m_renderViewId, m_texturedProgramHandle);
}

void MenuScreenBase::drawTextureHandle(
    bgfx::TextureHandle textureHandle, const Rect &rect, bool flipVertically, bool blendAlpha)
{
    m_drawTint = 0xffffffffu;
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
    const float topV = flipVertically ? 1.0f : 0.0f;
    const float bottomV = flipVertically ? 0.0f : 1.0f;
    pVertices[0] = MenuVertex{left, top, 0.0f, 0.0f, topV};
    pVertices[1] = MenuVertex{right, top, 0.0f, 1.0f, topV};
    pVertices[2] = MenuVertex{right, bottom, 0.0f, 1.0f, bottomV};
    pVertices[3] = MenuVertex{left, bottom, 0.0f, 0.0f, bottomV};

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
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_MSAA
        | (blendAlpha ? BGFX_STATE_BLEND_ALPHA : 0));
    applyClipRect();
    bgfx::submit(m_renderViewId, m_texturedProgramHandle);
}

void MenuScreenBase::drawTextureRegionColor(
    const std::string &textureName,
    const SourceRect &sourceRect,
    const Rect &rect,
    uint32_t colorAbgr,
    float rotationRadians)
{
    const TextureHandle *pTexture = ensureTexture(textureName);

    if (pTexture == nullptr)
    {
        return;
    }

    const bgfx::TextureHandle textureHandle = pTexture->handle;
    m_drawTint = colorAbgr;

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
    const float uScale = pTexture->uScale / static_cast<float>(pTexture->width);
    const float vScale = pTexture->vScale / static_cast<float>(pTexture->height);
    const float u0 = useSourceRect ? sourceRect.x * uScale : 0.0f;
    const float v0 = useSourceRect ? sourceRect.y * vScale : 0.0f;
    const float u1 = useSourceRect ? (sourceRect.x + sourceRect.width) * uScale : pTexture->uScale;
    const float v1 = useSourceRect ? (sourceRect.y + sourceRect.height) * vScale : pTexture->vScale;
    pVertices[0] = MenuVertex{left, top, 0.0f, u0, v0};
    pVertices[1] = MenuVertex{right, top, 0.0f, u1, v0};
    pVertices[2] = MenuVertex{right, bottom, 0.0f, u1, v1};
    pVertices[3] = MenuVertex{left, bottom, 0.0f, u0, v1};

    if (rotationRadians != 0.0f)
    {
        const float centerX = rect.x + rect.width * 0.5f;
        const float centerY = rect.y + rect.height * 0.5f;
        const float sine = std::sin(rotationRadians);
        const float cosine = std::cos(rotationRadians);
        for (int i = 0; i < 4; ++i)
        {
            const float x = pVertices[i].x - centerX;
            const float y = pVertices[i].y - centerY;
            pVertices[i].x = centerX + cosine * x - sine * y;
            pVertices[i].y = centerY + sine * x + cosine * y;
        }
    }

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
        pTexture->filterProfile,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    applyClipRect();
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

std::optional<MenuScreenBase::TexturePixelsBgra> MenuScreenBase::texturePixelsBgra(const std::string &textureName)
{
    const TextureHandle *pTexture = ensureTexture(textureName);

    if (pTexture == nullptr
        || pTexture->physicalWidth <= 0
        || pTexture->physicalHeight <= 0
        || pTexture->bgraPixels.empty())
    {
        return std::nullopt;
    }

    return TexturePixelsBgra{
        pTexture->physicalWidth,
        pTexture->physicalHeight,
        pTexture->width,
        pTexture->height,
        pTexture->bgraPixels
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
    const FontHandle *pFont = ensureTextFont(fontName, scale);

    if (pFont == nullptr || !bgfx::isValid(pFont->mainTextureHandle))
    {
        return false;
    }

    const bgfx::TextureHandle mainTextureHandle = pFont->mainTextureHandle;

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

    const bool pixelSized = isIndependentOutlineFont(fontName);
    if (pixelSized)
    {
        pixelY = std::round(pixelY);
    }
    pixelX -= pFont->atlasPadding * scale;
    pixelY -= pFont->atlasPadding * scale;

    const float shadowOffset = std::max(1.0f, scale);

    m_drawTint = 0xffffffffu;
    if (drawShadow && bgfx::isValid(pFont->shadowTextureHandle))
    {
        bgfx::TransientVertexBuffer shadowBuffer;
        bgfx::allocTransientVertexBuffer(&shadowBuffer, vertexCount, MenuVertex::ms_layout);
        MenuVertex *pShadowVertices = reinterpret_cast<MenuVertex *>(shadowBuffer.data);
        float penX = pixelX + shadowOffset;
        uint8_t previous = 0;
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
            penX += (glyphMetrics.leftSpacing + pFont->kerning(previous, character)) * scale;
            previous = character;

            if (glyphMetrics.width > 0)
            {
                const int cellX = (character % 16) * (pFont->atlasCellWidth + 2 * pFont->atlasPadding);
                const int cellY = (character / 16) * (pFont->fontHeight + 2 * pFont->atlasPadding);
                const float u0 = static_cast<float>(cellX) / static_cast<float>(pFont->atlasWidth / pFont->atlasScale);
                const float v0 = static_cast<float>(cellY) / static_cast<float>(pFont->atlasHeight / pFont->atlasScale);
                const float u1 = static_cast<float>(cellX + glyphMetrics.width + 2 * pFont->atlasPadding)
                    / static_cast<float>(pFont->atlasWidth / pFont->atlasScale);
                const float v1 = static_cast<float>(cellY + pFont->fontHeight + 2 * pFont->atlasPadding)
                    / static_cast<float>(pFont->atlasHeight / pFont->atlasScale);
                const float glyphWidth = static_cast<float>(glyphMetrics.width + 2 * pFont->atlasPadding) * scale;
                const float glyphHeight = static_cast<float>(pFont->fontHeight + 2 * pFont->atlasPadding) * scale;
                const float top = pixelY + shadowOffset;
                const float bottom = top + glyphHeight;

                const float left = pixelSized ? std::round(penX) : penX;
                pShadowVertices[vertexIndex + 0] = MenuVertex{left, top, 0.0f, u0, v0};
                pShadowVertices[vertexIndex + 1] = MenuVertex{left + glyphWidth, top, 0.0f, u1, v0};
                pShadowVertices[vertexIndex + 2] = MenuVertex{left + glyphWidth, bottom, 0.0f, u1, v1};
                pShadowVertices[vertexIndex + 3] = MenuVertex{left, top, 0.0f, u0, v0};
                pShadowVertices[vertexIndex + 4] = MenuVertex{left + glyphWidth, bottom, 0.0f, u1, v1};
                pShadowVertices[vertexIndex + 5] = MenuVertex{left, bottom, 0.0f, u0, v1};
                vertexIndex += 6;
            }

            penX += (glyphMetrics.advance() - glyphMetrics.leftSpacing) * scale;
        }

        bgfx::setVertexBuffer(0, &shadowBuffer);
        bindTexture(0, m_textureUniformHandle, pFont->shadowTextureHandle,
                    pixelSized || pFont->atlasScale > 1 ? TextureFilterProfile::SmoothText
                                                        : TextureFilterProfile::Text);
        bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
        applyClipRect();
        bgfx::submit(m_renderViewId, m_texturedProgramHandle);
    }

    bgfx::TransientVertexBuffer vertexBuffer;
    bgfx::allocTransientVertexBuffer(&vertexBuffer, vertexCount, MenuVertex::ms_layout);
    MenuVertex *pVertices = reinterpret_cast<MenuVertex *>(vertexBuffer.data);
    float penX = pixelX;
    uint8_t previous = 0;
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
        penX += (glyphMetrics.leftSpacing + pFont->kerning(previous, character)) * scale;
        previous = character;

        if (glyphMetrics.width > 0)
        {
            const int cellX = (character % 16) * (pFont->atlasCellWidth + 2 * pFont->atlasPadding);
            const int cellY = (character / 16) * (pFont->fontHeight + 2 * pFont->atlasPadding);
            const float u0 = static_cast<float>(cellX) / static_cast<float>(pFont->atlasWidth / pFont->atlasScale);
            const float v0 = static_cast<float>(cellY) / static_cast<float>(pFont->atlasHeight / pFont->atlasScale);
            const float u1 = static_cast<float>(cellX + glyphMetrics.width + 2 * pFont->atlasPadding)
                / static_cast<float>(pFont->atlasWidth / pFont->atlasScale);
            const float v1 = static_cast<float>(cellY + pFont->fontHeight + 2 * pFont->atlasPadding)
                / static_cast<float>(pFont->atlasHeight / pFont->atlasScale);
            const float glyphWidth = static_cast<float>(glyphMetrics.width + 2 * pFont->atlasPadding) * scale;
            const float glyphHeight = static_cast<float>(pFont->fontHeight + 2 * pFont->atlasPadding) * scale;
            const float bottom = pixelY + glyphHeight;

            const float left = pixelSized ? std::round(penX) : penX;
            pVertices[vertexIndex + 0] = MenuVertex{left, pixelY, 0.0f, u0, v0};
            pVertices[vertexIndex + 1] = MenuVertex{left + glyphWidth, pixelY, 0.0f, u1, v0};
            pVertices[vertexIndex + 2] = MenuVertex{left + glyphWidth, bottom, 0.0f, u1, v1};
            pVertices[vertexIndex + 3] = MenuVertex{left, pixelY, 0.0f, u0, v0};
            pVertices[vertexIndex + 4] = MenuVertex{left + glyphWidth, bottom, 0.0f, u1, v1};
            pVertices[vertexIndex + 5] = MenuVertex{left, bottom, 0.0f, u0, v1};
            vertexIndex += 6;
        }

        penX += (glyphMetrics.advance() - glyphMetrics.leftSpacing) * scale;
    }

    bgfx::setVertexBuffer(0, &vertexBuffer);
    m_drawTint = colorAbgr;
    bindTexture(0, m_textureUniformHandle, mainTextureHandle,
                pixelSized || pFont->atlasScale > 1 ? TextureFilterProfile::SmoothText : TextureFilterProfile::Text);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    applyClipRect();
    bgfx::submit(m_renderViewId, m_texturedProgramHandle);
    return true;
}

float MenuScreenBase::measureTextWidth(const std::string &fontName, const std::string &text, float scale)
{
    const FontHandle *pFont = ensureTextFont(fontName, scale);

    if (pFont == nullptr)
    {
        return 0.0f;
    }

    float widthPixels = 0.0f;
    uint8_t previous = 0;

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
        widthPixels += (glyphMetrics.advance() + pFont->kerning(previous, character)) * scale;
        previous = character;
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

    constexpr float MaxUiScale = 8.0f;
    const float baseScale = std::min(
        std::min(
            static_cast<float>(m_frameWidth) / logicalWidth,
            static_cast<float>(m_frameHeight) / logicalHeight),
        MaxUiScale);
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

void MenuScreenBase::preloadTexture(const std::string &textureName)
{
    if (textureName.empty() || !Engine::BgfxContext::isBgfxInitialized())
    {
        return;
    }

    ensureRendererInitialized();
    releaseTexturesIfAssetsChanged();
    ensureTexture(textureName);
}

void MenuScreenBase::preloadFont(const std::string &fontName)
{
    if (fontName.empty() || !Engine::BgfxContext::isBgfxInitialized())
    {
        return;
    }

    ensureRendererInitialized();
    ensureFont(fontName);
}

void MenuScreenBase::preloadLayoutAssets(const UiLayoutManager &layoutManager)
{
    for (const auto &elementPair : layoutManager.elements())
    {
        const UiLayoutManager::LayoutElement &element = elementPair.second;
        preloadTexture(element.primaryAsset);
        preloadTexture(element.hoverAsset);
        preloadTexture(element.pressedAsset);
        preloadTexture(element.secondaryAsset);
        preloadTexture(element.tertiaryAsset);
        preloadTexture(element.quaternaryAsset);
        preloadTexture(element.quinaryAsset);
        preloadFont(element.fontName);
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
    m_tintUniformHandle = bgfx::createUniform("u_menuTint", bgfx::UniformType::Vec4);
    m_texturedProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_menu_tint");
    m_rendererInitialized = bgfx::isValid(m_textureUniformHandle) && bgfx::isValid(m_texturedProgramHandle);

    if (!m_rendererInitialized)
    {
        std::cerr << "MenuScreenBase renderer initialization failed\n";
    }
}

void MenuScreenBase::destroyRendererResources()
{
    if (Engine::BgfxContext::isBgfxInitialized() && bgfx::isValid(m_texturedProgramHandle))
    {
        bgfx::destroy(m_texturedProgramHandle);
        m_texturedProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (Engine::BgfxContext::isBgfxInitialized() && bgfx::isValid(m_textureUniformHandle))
    {
        bgfx::destroy(m_textureUniformHandle);
        m_textureUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (Engine::BgfxContext::isBgfxInitialized() && bgfx::isValid(m_tintUniformHandle))
    {
        bgfx::destroy(m_tintUniformHandle);
        m_tintUniformHandle = BGFX_INVALID_HANDLE;
    }
    m_rendererInitialized = false;
}

const MenuScreenBase::TextureHandle *MenuScreenBase::findTexture(const std::string &textureName) const
{
    const std::string normalized = toLowerCopy(textureName);
    const std::unordered_map<std::string, size_t>::const_iterator it = s_textureIndexByName.find(normalized);
    return it != s_textureIndexByName.end() ? &s_textureHandles[it->second] : nullptr;
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

    if (Engine::hasCookedTextureSignature(*bytes))
    {
        return ensureCookedTexture(textureName, *resolvedPath, *bytes);
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
    const Engine::AssetScaleTier loadedTier = Engine::assetScaleTierFromResolvedPath(*resolvedPath);
    textureHandle.width = Engine::scalePhysicalPixelsToLogical(width, loadedTier);
    textureHandle.height = Engine::scalePhysicalPixelsToLogical(height, loadedTier);
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

    s_textureHandles.push_back(std::move(textureHandle));
    s_textureIndexByName[s_textureHandles.back().normalizedTextureName] = s_textureHandles.size() - 1;
    return &s_textureHandles.back();
}

// HUD art cooked by tools/cook_ui_textures.py (the Obsidian illustrations have no PNG at runtime).
const MenuScreenBase::TextureHandle *MenuScreenBase::ensureCookedTexture(
    const std::string &textureName, const std::string &resolvedPath, const std::vector<uint8_t> &bytes)
{
    TextureHandle textureHandle = {};
    textureHandle.normalizedTextureName = toLowerCopy(textureName);
    textureHandle.filterProfile = textureHandle.normalizedTextureName.starts_with("obsidian_")
        ? TextureFilterProfile::UiIllustration
        : TextureFilterProfile::Ui;
    try
    {
        const Engine::CookedTexture cooked = Engine::decodeCookedTexture(bytes);
        const int width = cooked.contentWidth != 0 ? cooked.contentWidth : cooked.width;
        const int height = cooked.contentHeight != 0 ? cooked.contentHeight : cooked.height;
        const Engine::AssetScaleTier loadedTier = Engine::assetScaleTierFromResolvedPath(resolvedPath);
        textureHandle.width = Engine::scalePhysicalPixelsToLogical(width, loadedTier);
        textureHandle.height = Engine::scalePhysicalPixelsToLogical(height, loadedTier);
        textureHandle.physicalWidth = width;
        textureHandle.physicalHeight = height;
        textureHandle.uScale = float(width) / float(cooked.width);
        textureHandle.vScale = float(height) / float(cooked.height);
        textureHandle.handle = createCookedTexture2D(
            cooked, textureHandle.filterProfile, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    }
    catch (const std::exception &exception)
    {
        std::cerr << "MenuScreenBase could not load cooked texture " << resolvedPath << ": " << exception.what()
                  << '\n';
        return nullptr;
    }

    if (!bgfx::isValid(textureHandle.handle))
    {
        std::cerr << "MenuScreenBase could not create bgfx texture: " << resolvedPath << '\n';
        return nullptr;
    }

    s_textureHandles.push_back(std::move(textureHandle));
    s_textureIndexByName[s_textureHandles.back().normalizedTextureName] = s_textureHandles.size() - 1;
    return &s_textureHandles.back();
}

const MenuScreenBase::FontHandle *MenuScreenBase::findFont(const std::string &fontName, int pixelHeight) const
{
    return SharedFontCache::find(fontName, isIndependentOutlineFont(fontName) ? pixelHeight : 0);
}

const MenuScreenBase::FontHandle *MenuScreenBase::ensureTextFont(const std::string &fontName, float &scale)
{
    const FontHandle *pFont = ensureFont(fontName);
    if (pFont != nullptr && isIndependentOutlineFont(fontName))
    {
        const int pixelHeight = std::max(1, int(std::lround(pFont->fontHeight * scale)));
        // Measurement and rendering use the same face at the same physical size.
        // Never minify a larger atlas.
        if (pixelHeight != pFont->fontHeight)
        {
            pFont = ensureFont(fontName, pixelHeight);
        }
        scale = 1.0f;
    }
    return pFont;
}

void MenuScreenBase::resizeFontCache(int width, int height)
{
    if (width == s_fontFrameWidth && height == s_fontFrameHeight)
    {
        return;
    }
    s_fontFrameWidth = width;
    s_fontFrameHeight = height;
    // Resizing must not accumulate every intermediate raster size. Keep only the base layout faces.
    SharedFontCache::releaseRasterSizes();
}

const MenuScreenBase::FontHandle *MenuScreenBase::ensureFont(const std::string &fontName, int pixelHeight)
{
    if (const FontHandle *pExisting = findFont(fontName, pixelHeight))
    {
        return pExisting;
    }
    if (m_pAssetFileSystem == nullptr)
    {
        return nullptr;
    }
    SharedFontCache::ensure(
        *m_pAssetFileSystem, {{fontName, isIndependentOutlineFont(fontName) ? pixelHeight : 0}});
    return findFont(fontName, pixelHeight);
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

    for (DynamicTextureHandle &textureHandle : s_dynamicTextureHandles)
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
            copyBgraTextureUploadMemory(pixelsBgra.data(), static_cast<uint32_t>(pixelsBgra.size())));
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
        copyBgraTextureUploadMemory(pixelsBgra.data(), static_cast<uint32_t>(pixelsBgra.size())));
    s_dynamicTextureHandles.push_back(std::move(textureHandle));
    return s_dynamicTextureHandles.back().handle;
}

std::optional<std::string> MenuScreenBase::resolveTexturePath(const std::string &textureName)
{
    if (textureName.starts_with("hud_x2/"))
    {
        return m_pAssetFileSystem->resolveExistingFilePath(textureName);
    }
    return Engine::findCookedOrImageAssetPath(
        *m_pAssetFileSystem, "Data/icons", textureName, s_directoryEntriesByPath, s_resolvedTexturePaths);
}

void MenuScreenBase::setClipRect(const std::optional<Rect> &rect)
{
    m_clipRect = rect;
}

void MenuScreenBase::applyClipRect() const
{
    const float tint[] = {float(m_drawTint & 255) / 255, float((m_drawTint >> 8) & 255) / 255,
                          float((m_drawTint >> 16) & 255) / 255, float(m_drawTint >> 24) / 255};
    bgfx::setUniform(m_tintUniformHandle, tint);
    if (m_clipRect)
    {
        const Rect &rect = *m_clipRect;
        bgfx::setScissor(uint16_t(std::max(0.0f, rect.x)), uint16_t(std::max(0.0f, rect.y)),
                         uint16_t(std::max(0.0f, rect.width)), uint16_t(std::max(0.0f, rect.height)));
    }
}

void MenuScreenBase::drawSolidRect(const Rect &rect, uint32_t colorAbgr)
{
    const std::vector<uint8_t> pixel = {uint8_t(colorAbgr >> 16), uint8_t(colorAbgr >> 8), uint8_t(colorAbgr),
                                        uint8_t(colorAbgr >> 24)};
    drawPixelsBgra("menu-solid-" + std::to_string(colorAbgr), 1, 1, pixel, rect);
}

void MenuScreenBase::drawEllipseOutline(const Rect &rect, float thickness, uint32_t colorAbgr)
{
    constexpr int Segments = 128;
    constexpr float TwoPi = 6.283185307f;
    if (rect.width <= 0 || rect.height <= 0 ||
        bgfx::getAvailTransientVertexBuffer(Segments * 6, MenuVertex::ms_layout) < Segments * 6)
    {
        return;
    }
    const bgfx::TextureHandle white = ensureDynamicTexture("menu-white", 1, 1, {255, 255, 255, 255});
    bgfx::TransientVertexBuffer vertices;
    bgfx::allocTransientVertexBuffer(&vertices, Segments * 6, MenuVertex::ms_layout);
    MenuVertex *pVertices = reinterpret_cast<MenuVertex *>(vertices.data);
    const float rx = rect.width / 2;
    const float ry = rect.height / 2;
    const float innerX = std::max(0.0f, rx - thickness);
    const float innerY = std::max(0.0f, ry - thickness);
    for (int i = 0; i < Segments; ++i)
    {
        const float a = i * TwoPi / Segments;
        const float b = (i + 1) * TwoPi / Segments;
        const MenuVertex corners[] = {
            {rect.x + rx + rx * std::cos(a), rect.y + ry + ry * std::sin(a), 0, 0.5f, 0.5f},
            {rect.x + rx + rx * std::cos(b), rect.y + ry + ry * std::sin(b), 0, 0.5f, 0.5f},
            {rect.x + rx + innerX * std::cos(b), rect.y + ry + innerY * std::sin(b), 0, 0.5f, 0.5f},
            {rect.x + rx + innerX * std::cos(a), rect.y + ry + innerY * std::sin(a), 0, 0.5f, 0.5f}};
        for (int j = 0; j < 6; ++j)
        {
            pVertices[i * 6 + j] = corners[std::array{0, 1, 2, 0, 2, 3}[j]];
        }
    }
    m_drawTint = colorAbgr;
    bgfx::setVertexBuffer(0, &vertices);
    bindTexture(0, m_textureUniformHandle, white, TextureFilterProfile::Ui);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    applyClipRect();
    bgfx::submit(m_renderViewId, m_texturedProgramHandle);
}

} // namespace OpenYAMM::Game

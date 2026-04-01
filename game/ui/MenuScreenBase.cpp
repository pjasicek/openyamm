#include "game/ui/MenuScreenBase.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint8_t MenuViewId = 0;

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

    return shaderRoot / rendererDirectory / pShaderName;
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
            const bool isTealKey = red <= 8 && green >= 248 && blue >= 248;
            pixels[pixelOffset + 3] = (isMagentaKey || isTealKey) ? 0 : 255;
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
        const bool isTealKey = red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isTealKey)
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

void MenuScreenBase::renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds)
{
    m_frameWidth = width;
    m_frameHeight = height;
    m_mouseWheelDelta = mouseWheelDelta;
    ensureRendererInitialized();

    float polledMouseX = 0.0f;
    float polledMouseY = 0.0f;
    const uint32_t mouseButtons = SDL_GetMouseState(&polledMouseX, &polledMouseY);
    m_mouseX = polledMouseX;
    m_mouseY = polledMouseY;
    m_leftMouseDown = (mouseButtons & SDL_BUTTON_LMASK) != 0;

    bgfx::setViewRect(MenuViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewClear(MenuViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x000000ffu, 1.0f, 0);
    bgfx::touch(MenuViewId);
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
    bgfx::setViewTransform(MenuViewId, nullptr, projectionMatrix);

    drawScreen(deltaSeconds);
    m_leftMouseDownPrevious = m_leftMouseDown;
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

void MenuScreenBase::drawTexture(const std::string &textureName, const Rect &rect)
{
    const TextureHandle *pTexture = ensureTexture(textureName);

    if (pTexture == nullptr || !bgfx::isValid(pTexture->handle))
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
    bgfx::setTexture(0, m_textureUniformHandle, pTexture->handle);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    bgfx::submit(MenuViewId, m_texturedProgramHandle);
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

void MenuScreenBase::ensureRendererInitialized()
{
    if (m_rendererInitialized)
    {
        return;
    }

    MenuVertex::init();
    m_textureUniformHandle = bgfx::createUniform("s_texture", bgfx::UniformType::Sampler);
    m_texturedProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_shadowmaps_texture");
    m_rendererInitialized = bgfx::isValid(m_textureUniformHandle) && bgfx::isValid(m_texturedProgramHandle);
}

void MenuScreenBase::destroyRendererResources()
{
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
    const auto it = m_textureIndexByName.find(normalized);
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
        return nullptr;
    }

    const std::optional<std::vector<uint8_t>> bytes = m_pAssetFileSystem->readBinaryFile(*resolvedPath);

    if (!bytes || bytes->empty())
    {
        return nullptr;
    }

    int width = 0;
    int height = 0;
    const std::optional<std::vector<uint8_t>> pixels = loadTexturePixelsBgra(*bytes, *resolvedPath, width, height);

    if (!pixels || width <= 0 || height <= 0)
    {
        return nullptr;
    }

    TextureHandle textureHandle = {};
    textureHandle.normalizedTextureName = toLowerCopy(textureName);
    textureHandle.width = width;
    textureHandle.height = height;
    textureHandle.handle = bgfx::createTexture2D(
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(pixels->data(), static_cast<uint32_t>(pixels->size()))
    );

    if (!bgfx::isValid(textureHandle.handle))
    {
        return nullptr;
    }

    m_textureHandles.push_back(std::move(textureHandle));
    m_textureIndexByName[m_textureHandles.back().normalizedTextureName] = m_textureHandles.size() - 1;
    return &m_textureHandles.back();
}

std::optional<std::string> MenuScreenBase::resolveTexturePath(const std::string &textureName)
{
    const std::string normalizedName = toLowerCopy(textureName);
    const auto cachedIt = m_resolvedTexturePaths.find(normalizedName);

    if (cachedIt != m_resolvedTexturePaths.end())
    {
        return cachedIt->second;
    }

    const std::array<std::string, 2> directories = {
        "Data/EnglishD",
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
}

#include "game/render/RuntimeShader.h"

#include <SDL3/SDL.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>

namespace OpenYAMM::Game
{
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


bgfx::ProgramHandle loadRuntimeProgram(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const auto loadShader = [](const char *pName) -> bgfx::ShaderHandle
    {
        const std::filesystem::path path = getShaderPath(bgfx::getRendererType(), pName);
        std::ifstream stream(path, std::ios::binary);
        const std::vector<char> bytes((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
        if (bytes.empty())
        {
            std::cerr << "Failed to read shader: " << path << '\n';
            return BGFX_INVALID_HANDLE;
        }
        return bgfx::createShader(bgfx::copy(bytes.data(), uint32_t(bytes.size())));
    };
    const bgfx::ShaderHandle vertex = loadShader(pVertexShaderName);
    const bgfx::ShaderHandle fragment = loadShader(pFragmentShaderName);
    if (!bgfx::isValid(vertex) || !bgfx::isValid(fragment))
    {
        if (bgfx::isValid(vertex))
        {
            bgfx::destroy(vertex);
        }
        if (bgfx::isValid(fragment))
        {
            bgfx::destroy(fragment);
        }
        return BGFX_INVALID_HANDLE;
    }
    return bgfx::createProgram(vertex, fragment, true);
}
}

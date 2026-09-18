#pragma once

#include <bgfx/bgfx.h>
#include <filesystem>

namespace OpenYAMM::Game
{
std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName);
bgfx::ProgramHandle loadRuntimeProgram(const char *pVertexShaderName, const char *pFragmentShaderName);
}

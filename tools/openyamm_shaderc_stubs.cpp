#include "shaderc.h"

static bool writeUnsupportedBackendMessage(const char *pMessage, bx::WriterI *pMessageWriter)
{
    bx::Error messageError;
    bx::write(pMessageWriter, &messageError, pMessage);
    return false;
}

namespace bgfx
{
bool compileHLSLShader(
    const Options &options,
    uint32_t version,
    const std::string &code,
    bx::WriterI *pShaderWriter,
    bx::WriterI *pMessageWriter)
{
    BX_UNUSED(options, version, code, pShaderWriter);
    return writeUnsupportedBackendMessage("HLSL shader compilation is not enabled.\n", pMessageWriter);
}

bool compileDxilShader(
    const Options &options,
    uint32_t version,
    const std::string &code,
    bx::WriterI *pShaderWriter,
    bx::WriterI *pMessageWriter)
{
    BX_UNUSED(options, version, code, pShaderWriter);
    return writeUnsupportedBackendMessage("DXIL shader compilation is not enabled.\n", pMessageWriter);
}

bool compileMetalShader(
    const Options &options,
    uint32_t version,
    const std::string &code,
    bx::WriterI *pShaderWriter,
    bx::WriterI *pMessageWriter)
{
    BX_UNUSED(options, version, code, pShaderWriter);
    return writeUnsupportedBackendMessage("Metal shader compilation is not enabled.\n", pMessageWriter);
}

bool compilePSSLShader(
    const Options &options,
    uint32_t version,
    const std::string &code,
    bx::WriterI *pShaderWriter,
    bx::WriterI *pMessageWriter)
{
    BX_UNUSED(options, version, code, pShaderWriter);
    return writeUnsupportedBackendMessage("PSSL shader compilation is not enabled.\n", pMessageWriter);
}

bool compileSPIRVShader(
    const Options &options,
    uint32_t version,
    const std::string &code,
    bx::WriterI *pShaderWriter,
    bx::WriterI *pMessageWriter)
{
    BX_UNUSED(options, version, code, pShaderWriter);
    return writeUnsupportedBackendMessage("SPIR-V shader compilation is not enabled.\n", pMessageWriter);
}

bool compileWgslShader(
    const Options &options,
    uint32_t version,
    const std::string &code,
    bx::WriterI *pShaderWriter,
    bx::WriterI *pMessageWriter)
{
    BX_UNUSED(options, version, code, pShaderWriter);
    return writeUnsupportedBackendMessage("WGSL shader compilation is not enabled.\n", pMessageWriter);
}

const char *getPsslPreamble()
{
    return "";
}
} // namespace bgfx

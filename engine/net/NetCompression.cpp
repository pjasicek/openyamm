#include "engine/net/NetCompression.h"

#include <zstd.h>

#include <memory>

namespace OpenYAMM::Engine
{
namespace
{
constexpr int PackLevel = 3;

struct FreeCompressContext
{
    void operator()(ZSTD_CCtx *pContext) const
    {
        ZSTD_freeCCtx(pContext);
    }
};

struct FreeDecompressContext
{
    void operator()(ZSTD_DCtx *pContext) const
    {
        ZSTD_freeDCtx(pContext);
    }
};
}

std::vector<uint8_t> packBytes(std::span<const uint8_t> bytes)
{
    // One context for a thread's many small messages.
    thread_local const std::unique_ptr<ZSTD_CCtx, FreeCompressContext> pContext(ZSTD_createCCtx());
    std::vector<uint8_t> packed(ZSTD_compressBound(bytes.size()));
    const size_t size =
        ZSTD_compressCCtx(pContext.get(), packed.data(), packed.size(), bytes.data(), bytes.size(), PackLevel);

    if (ZSTD_isError(size))
    {
        return {};
    }

    packed.resize(size);
    return packed;
}

std::optional<std::vector<uint8_t>> unpackBytes(std::span<const uint8_t> packed, size_t maxLength)
{
    const unsigned long long length = ZSTD_getFrameContentSize(packed.data(), packed.size());

    if (length == ZSTD_CONTENTSIZE_ERROR || length == ZSTD_CONTENTSIZE_UNKNOWN || length > maxLength)
    {
        return std::nullopt;
    }

    thread_local const std::unique_ptr<ZSTD_DCtx, FreeDecompressContext> pContext(ZSTD_createDCtx());
    std::vector<uint8_t> bytes;
    bytes.resize(length);
    const size_t size = ZSTD_decompressDCtx(pContext.get(), bytes.data(), bytes.size(), packed.data(), packed.size());

    if (ZSTD_isError(size) || size != bytes.size())
    {
        return std::nullopt;
    }

    return bytes;
}
}

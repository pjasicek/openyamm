"""Run the real bgfx Metal upload function without requiring a GPU."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[1]
CANDIDATES = [REPO / 'build/macos/_deps/bgfx-src', REPO / 'build/_deps/bgfx-src']
BGFX = Path(sys.argv[1]) if len(sys.argv) > 1 else next((path for path in CANDIDATES if path.exists()), CANDIDATES[0])

PREAMBLE = r'''
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdlib>

#define BX_ENABLED(_x) (0 != (_x))
#define BX_PLATFORM_IOS 0
#define BX_PLATFORM_VISIONOS 0
#define MTL_RELEASE(_obj, _expected) delete _obj

namespace MTL
{
    enum TextureType { TextureType2D, TextureType3D };
    enum CPUCacheMode { CPUCacheModeDefaultCache };
    enum StorageMode { StorageModeShared, StorageModeManaged };
    enum TextureUsage { TextureUsageUnknown };
    // Values match MTLPixelFormat; bgfx compares them against the PVRTC range.
    enum PixelFormat
    {
        PixelFormatBGRA8Unorm = 80, PixelFormatBC4_RUnorm = 140, PixelFormatBC5_RGUnorm = 142,
        PixelFormatBC7_RGBAUnorm = 152, PixelFormatPVRTC_RGBA_4BPP = 166, PixelFormatEAC_RGBA8 = 178,
        PixelFormatASTC_5x5_LDR = 206,
    };
    struct Origin { size_t x, y, z; static Origin Make(size_t x, size_t y, size_t z) { return {x, y, z}; } };
    struct Size { size_t width, height, depth; static Size Make(size_t w, size_t h, size_t d) { return {w, h, d}; } };
    struct Region
    {
        Origin origin;
        Size size;
        Region(size_t x, size_t y, size_t z, size_t w, size_t h, size_t d) : origin{x, y, z}, size{w, h, d} {}
    };

    struct Upload { bool temporary; size_t x, y, width, height, level, slice, bytesPerRow, bytesPerImage; };
    Upload lastUpload = {};

    // The minimum row stride Apple GPUs accept (the AGX "used_bytes_per_row").
    size_t usedBytesPerRow(PixelFormat format, size_t width)
    {
        switch (format)
        {
        case PixelFormatBGRA8Unorm: return width * 4;
        case PixelFormatBC4_RUnorm: return (width + 3) / 4 * 8;
        case PixelFormatASTC_5x5_LDR: return (width + 4) / 5 * 16;
        case PixelFormatPVRTC_RGBA_4BPP: return 0;
        default: return (width + 3) / 4 * 16;
        }
    }

    struct TextureDescriptor
    {
        TextureType type = TextureType2D;
        PixelFormat format = PixelFormatBGRA8Unorm;
        size_t width = 0, height = 0, depth = 0;
        void setTextureType(TextureType value) { type = value; }
        void setPixelFormat(PixelFormat value) { format = value; }
        void setWidth(size_t value) { width = value; }
        void setHeight(size_t value) { height = value; }
        void setDepth(size_t value) { depth = value; }
        void setMipmapLevelCount(size_t value) { assert(value == 1); }
        void setSampleCount(size_t value) { assert(value == 1); }
        void setArrayLength(size_t value) { assert(value == 1); }
        void setCpuCacheMode(CPUCacheMode) {}
        void setStorageMode(StorageMode) {}
        void setUsage(TextureUsage) {}
    };

    struct Texture
    {
        PixelFormat format;
        bool temporary;
        size_t width, height;
        PixelFormat pixelFormat() const { return format; }
        void replaceRegion(Region region, size_t level, size_t slice, const void *, size_t bytesPerRow,
            size_t bytesPerImage)
        {
            assert(bytesPerRow >= usedBytesPerRow(format, region.size.width));
            lastUpload = {temporary, region.origin.x, region.origin.y, region.size.width, region.size.height,
                level, slice, bytesPerRow, bytesPerImage};
        }
    };

    struct Device
    {
        Texture *newTexture(TextureDescriptor *desc)
        {
            return new Texture{desc->format, true, desc->width, desc->height};
        }
    };

    struct Copy { size_t width, height, level, slice, x, y; };
    struct BlitCommandEncoder
    {
        Copy copy = {};
        void copyFromTexture(Texture *source, size_t sourceSlice, size_t sourceLevel, Origin sourceOrigin, Size size,
            Texture *, size_t slice, size_t level, Origin origin)
        {
            assert(source->temporary && sourceSlice == 0 && sourceLevel == 0 && sourceOrigin.x == 0);
            assert(size.width == source->width && size.height == source->height);
            copy = {size.width, size.height, level, slice, origin.x, origin.y};
        }
    };
}

namespace bimg
{
    namespace TextureFormat { enum Enum { BC4, BC5, BC7, ETC2A, ASTC5x5, PTC14A, BGRA8 }; }
    struct ImageBlockInfo { uint8_t bitsPerPixel, blockWidth, blockHeight, blockSize; };
    bool isCompressed(TextureFormat::Enum format) { return format < TextureFormat::BGRA8; }
    uint8_t getBitsPerPixel(TextureFormat::Enum format) { return format == TextureFormat::BGRA8 ? 32 : 8; }
    const ImageBlockInfo &getBlockInfo(TextureFormat::Enum format)
    {
        static const ImageBlockInfo bc4 = {4, 4, 4, 8}, block16 = {8, 4, 4, 16}, astc = {6, 5, 5, 16},
            pvrtc = {4, 4, 4, 8}, bgra = {32, 1, 1, 4};
        switch (format)
        {
        case TextureFormat::BC4: return bc4;
        case TextureFormat::ASTC5x5: return astc;
        case TextureFormat::PTC14A: return pvrtc;
        case TextureFormat::BGRA8: return bgra;
        default: return block16;
        }
    }
    void imageDecodeToBgra8(void *, void *, const void *, uint32_t, uint32_t, uint32_t, TextureFormat::Enum)
    { std::abort(); } // These checks exercise native uploads, without format conversion.
}

namespace bx
{
    template<class T> T max(T a, T b) { return std::max(a, b); }
    void *alloc(void *, size_t bytes) { return std::malloc(bytes); }
    void free(void *, void *data) { std::free(data); }
}

namespace bgfx
{
    struct Rect { uint16_t m_x, m_y, m_width, m_height; };
    struct Memory { uint8_t *data; };
    void *g_allocator = nullptr;

    struct CommandQueue { void finish(bool) {} };
    struct RendererContextMtl
    {
        void *m_renderCommandEncoder = nullptr;
        CommandQueue m_cmd;
        bool m_hasCPUCacheModesAndStorageModes = true;
        MTL::Device *m_device = nullptr;
        MTL::BlitCommandEncoder *m_blit = nullptr;
        MTL::BlitCommandEncoder *getBlitCommandEncoder() { return m_blit; }
    };
    RendererContextMtl *s_renderMtl;
    MTL::TextureDescriptor *newTextureDescriptor() { return new MTL::TextureDescriptor; }

    struct TextureMtl
    {
        enum Enum { Texture2D, Texture3D, TextureCube };
        MTL::Texture *m_ptr = nullptr;
        uint8_t m_type = Texture2D;
        uint8_t m_requestedFormat = bimg::TextureFormat::BC7;
        uint8_t m_textureFormat = bimg::TextureFormat::BC7;
        void update(uint8_t, uint8_t, const Rect &, uint16_t, uint16_t, uint16_t, const Memory *);
    };
}
'''

CHECKS = r'''
int main()
{
    using namespace bgfx;
    MTL::Device device;
    MTL::BlitCommandEncoder blit;
    int encoder = 0;
    RendererContextMtl renderer;
    renderer.m_device = &device;
    renderer.m_blit = &blit;
    s_renderMtl = &renderer;
    Memory memory = {nullptr};

    struct Profile { bimg::TextureFormat::Enum format; MTL::PixelFormat pixelFormat; uint32_t width, bytes; };
    // Sprite atlas pages (SpriteAtlasCache) are uploaded mip by mip and can be uneven at every mip.
    const Rect atlasMips[] = {{0, 0, 1798, 1731}, {0, 0, 899, 865}, {0, 0, 449, 432}, {0, 0, 224, 216},
        {0, 0, 112, 108}, {0, 0, 1939, 1029}, {0, 0, 969, 514}, {0, 0, 121, 64}, {0, 0, 127, 139},
        {0, 0, 1, 1}, {0, 0, 2, 2}, {0, 0, 4, 4}};
    for (const Profile profile : {Profile{bimg::TextureFormat::BC4, MTL::PixelFormatBC4_RUnorm, 4, 8},
        Profile{bimg::TextureFormat::BC5, MTL::PixelFormatBC5_RGUnorm, 4, 16},
        Profile{bimg::TextureFormat::BC7, MTL::PixelFormatBC7_RGBAUnorm, 4, 16},
        Profile{bimg::TextureFormat::ETC2A, MTL::PixelFormatEAC_RGBA8, 4, 16},
        Profile{bimg::TextureFormat::ASTC5x5, MTL::PixelFormatASTC_5x5_LDR, 5, 16}})
    {
        MTL::Texture target = {profile.pixelFormat, false, 4096, 4096};
        TextureMtl texture;
        texture.m_ptr = &target;
        texture.m_textureFormat = texture.m_requestedFormat = profile.format;
        for (const Rect &rect : atlasMips)
        {
            const size_t pitch = (rect.m_width + profile.width - 1) / profile.width * profile.bytes;

            // Uploads outside a render pass go through a temporary texture and a blit.
            renderer.m_renderCommandEncoder = nullptr;
            texture.update(0, 3, rect, 0, 1, UINT16_MAX, &memory);
            assert(MTL::lastUpload.temporary && MTL::lastUpload.bytesPerRow == pitch);
            assert(MTL::lastUpload.width == rect.m_width && MTL::lastUpload.height == rect.m_height);
            assert(blit.copy.width == rect.m_width && blit.copy.height == rect.m_height && blit.copy.level == 3);

            // Uploads inside a render pass replace the destination mip directly.
            renderer.m_renderCommandEncoder = &encoder;
            texture.update(0, 2, rect, 0, 1, UINT16_MAX, &memory);
            assert(!MTL::lastUpload.temporary && MTL::lastUpload.bytesPerRow == pitch && MTL::lastUpload.level == 2);

            // Explicit source pitches stay untouched.
            texture.update(0, 2, rect, 0, 1, uint16_t(pitch + 32), &memory);
            assert(MTL::lastUpload.bytesPerRow == pitch + 32);
        }
    }

    // Uncompressed and PVRTC uploads keep their original pitches.
    MTL::Texture bgra = {MTL::PixelFormatBGRA8Unorm, false, 64, 64};
    TextureMtl texture;
    texture.m_ptr = &bgra;
    texture.m_textureFormat = texture.m_requestedFormat = bimg::TextureFormat::BGRA8;
    renderer.m_renderCommandEncoder = &encoder;
    texture.update(0, 0, Rect{4, 8, 7, 5}, 0, 1, UINT16_MAX, &memory);
    assert(MTL::lastUpload.bytesPerRow == 28 && MTL::lastUpload.x == 4 && MTL::lastUpload.y == 8);
    texture.m_type = TextureMtl::TextureCube;
    texture.update(5, 0, Rect{0, 0, 7, 5}, 2, 1, 40, &memory);
    assert(MTL::lastUpload.bytesPerRow == 40 && MTL::lastUpload.slice == 2 * 6 + 5);

    MTL::Texture pvrtc = {MTL::PixelFormatPVRTC_RGBA_4BPP, false, 64, 64};
    texture.m_ptr = &pvrtc;
    texture.m_type = TextureMtl::Texture2D;
    texture.m_textureFormat = texture.m_requestedFormat = bimg::TextureFormat::PTC14A;
    texture.update(0, 0, Rect{0, 0, 32, 32}, 0, 1, UINT16_MAX, &memory);
    assert(MTL::lastUpload.bytesPerRow == 0);
}
'''

source = (BGFX / 'src/renderer_mtl.cpp').read_text()
match = re.search(r'void TextureMtl::update\(.*?\n\t\}', source, re.DOTALL)
assert match, 'Cannot find the pinned bgfx upload function'
with tempfile.TemporaryDirectory(prefix='openyamm-metal-upload-check-') as temporary:
    root = Path(temporary)
    cpp = root / 'check.cpp'
    cpp.write_text(PREAMBLE + '\nnamespace bgfx {\n' + match[0] + '\n}\n' + CHECKS)
    subprocess.run(['c++', '-std=c++20', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(root / 'check')],
                   check=True)
    subprocess.run([str(root / 'check')], check=True)
print('Metal texture upload checks passed')

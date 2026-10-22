# bgfx patches

## Anisotropy level

`bgfx-anisotropy-level.patch` adds `BGFX_RESET_MAXANISOTROPY_LEVEL(level)`: reset-flag bits 24–28 carry an
anisotropy limit applied with `BGFX_RESET_MAXANISOTROPY`, clamped to the device maximum (0 keeps the device maximum).
Upstream only switches between the device maximum (16× on desktop GPUs) and none. The OpenGL/GLES, Vulkan and
Direct3D 11 backends honour it, and changing it re-creates their samplers without resetting the back buffer.
`video.terrain_anisotropy` sets the level through `BgfxContext`. The OpenGL path without sampler objects applies a
changed level only when a texture's sampler flags next change.

## Direct3D 11 compressed texture updates

`bgfx-d3d11-compressed-updates.patch` fixes uploads of compressed mip levels with dimensions that are not
multiples of four. Row pitches round up to complete blocks, slice pitches count block rows, and full-mip
updates pass a null destination box so Direct3D accepts the unaligned virtual edges. Partial updates retain
their destination box and explicit source pitches are preserved.

The Windows 1.0 package includes townsfolk mips sized 246×280 and 123×140. The upstream upload uses
976/480-byte BC7 rows instead of 992/496 bytes, and submits nonaligned destination boxes. Rejected uploads
leave distant sprites invisible; trilinear blending between valid and missing levels makes them translucent.
This fixes the Direct3D backend without changing sprite shaders, source assets or the atlas format.

Run `python3 tests/test_bgfx_d3d11_texture_updates.py` after configuring the desktop build. The check compiles
the actual patched upload function against a recording Direct3D context, covering uneven/tiny mips, BC4/BC5/BC7,
partial and pitched updates, array/cube indexing, uncompressed textures, and compressed 3D slice pitches.
It does not replace a visual check on a Windows GPU.

## Metal compressed texture updates

`bgfx-metal-compressed-updates.patch` rounds the row pitch of compressed texture updates up to complete blocks, the
Metal counterpart of the Direct3D 11 fix above. The pinned upload computes `(width / blockWidth) * blockSize`, one
block short whenever the width is not a block multiple. Apple GPUs reject such uploads (`AGX: Texture read/write
assertion failed: bytes_per_row >= used_bytes_per_row`) and leave the mip empty. `SpriteAtlasCache` uploads its
compressed atlas pages mip by mip. In the Apple port, the MM6 creature atlases OpenYAMM used to ship (1798x1731 down
to 112x108) drew as black rectangles on macOS. iOS uses the same upload with ETC2 and ASTC data. The rounding matches
upstream bgfx #3822, but divides instead of calling `bx::alignUp`, whose mask is wrong for ASTC blocks 5, 6, 10 or 12
pixels wide. Initial uploads (`TextureMtl::create`) need no change: bimg already rounds their mip sizes.

Run `python3 tests/test_bgfx_metal_texture_updates.py` after configuring the macOS build. The check compiles the
actual patched upload function against a recording Metal device, covering uneven mip sizes in BC4/BC5/BC7, ETC2 and
ASTC 5x5, both the direct and blit upload paths, explicit pitches, uncompressed and PVRTC textures.

## GLES compressed texture updates

`bgfx-gles-unpack-row-length.patch` recognizes `GL_UNPACK_ROW_LENGTH` as core functionality in GLES 3.
Without this check, GLES 3 drivers that omit the redundant `EXT_unpack_subimage` extension use the pixel-row
copy path even for block-compressed textures. Uneven mip dimensions make that temporary buffer smaller than
the compressed payload, causing an out-of-bounds read during upload. GLES 3 now uploads the original block
buffer directly. Desktop GL retains its existing path.

The Android release regression check loads New Sorpigal's cooked atlases, whose mip dimensions include
254×278 and 127×139, with the emulator's GL pipe checksum enabled:

```sh
python3 android/test_release_apk.py android/app/build/outputs/apk/release/app-release.apk \
  --serial emulator-5554 --world mm6 --map oute3.odm --output /tmp/openyamm-gles-upload-test
```

For local visual checks, start the emulator with `-gpu host` and retain its GL pipe checksum checks.

## Desktop uniform cache

`bgfx-gl-uniform-cache.patch` targets the bgfx revision pinned in `cmake/Dependencies.cmake`:
`a73c12db8f502022d292cc6fb8872482997b0664`.

The patch connects desktop GL uniform upload functions to `engine/GlUniformCache.h`. It keeps values per GL program
and array-element location, skips identical uploads, removes destroyed programs, and clears values with the backend's
cache invalidation/shutdown. Matrix transpose state is part of the comparison. Program switches retain each program's
values; GL stores those values in the program object. This cache belongs to the renderer instance and render thread.

The desktop path uses byte comparisons and copies, avoiding alignment/aliasing assumptions when reading uniform data.
Android/GLES and Emscripten retain the upstream implementation. Other rendering backends are unaffected.

`OPENYAMM_GL_UNIFORM_CACHE` defaults to `ON`. Configure with `-DOPENYAMM_GL_UNIFORM_CACHE=OFF` to build the original
desktop upload path for comparisons. Rebuild `openyamm` after changing it.

`cmake/BgfxGlUniformCache.cmake` applies the patch during dependency configuration, including already-populated build
trees. It recognizes an already-applied patch and fails if neither the forward nor reverse patch matches. When updating
the bgfx pin or patch, rebase the patch deliberately and use a fresh dependency checkout, or reverse the previous patch
first. Do not manually edit generated dependency sources as the permanent fix.

Validation uses `GlUniformCacheTests.cpp` for value/lifetime/array behavior and real-GPU New Sorpigal captures for
integration. See `docs/PERF_NEW_SORPIGAL_SUBMISSIONS.md` for measurements and limitations. GL upload counts alone do
not establish a frame-rate improvement.

## OpenGL multisampled depth resolve

`bgfx-gl-msaa-depth-resolve.patch` lets a frame buffer use a multisampled depth attachment that is later sampled
(neither `BGFX_TEXTURE_RT_WRITE_ONLY` nor `BGFX_TEXTURE_MSAA_SAMPLE`) on the OpenGL and OpenGL ES renderers. Their
backend already resolves such an attachment with a depth blit when the view leaves the frame buffer
(`FrameBufferGL::resolve`); upstream only rejected it in `isFrameBufferValid`. Other backends keep the check: Vulkan
resolves colour only.

`CinematicGrading` uses it to keep ambient occlusion with `video.antialiasing`: the AO passes read the resolved
D32F depth of the multisampled world target. On other renderers AO is switched off while anti-aliasing is on.

## Metal depth-stencil format on iOS

`bgfx-metal-ios-depth-format.patch` asks `isDepth24Stencil8PixelFormatSupported` only on macOS. The pinned Metal
renderer selects the D24S8 format with that query on every Apple platform, but the property is
`API_UNAVAILABLE(ios)` in the iOS SDK, so an iPhone or iPad Metal device does not implement the selector the renderer
sends. iOS keeps `Depth32Float_Stencil8`, the format the renderer already chose for it a few lines earlier; macOS
behaviour is unchanged. The iOS Simulator does not show the problem: its Metal device is the Mac's GPU.

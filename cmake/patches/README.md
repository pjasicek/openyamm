# bgfx desktop OpenGL uniform cache

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

# bgfx EGL opaque window config

`bgfx-egl-opaque-window.patch` targets the same pinned bgfx revision.

The patch requests an EGL config without alpha bits for desktop windowed GL contexts (`EGL_ALPHA_SIZE` 0 plus a
preference pass over the returned config list for a zero-alpha config). Without it, the window buffer is ARGB, and
alpha-blended content leaves partial alpha in the backbuffer; Wayland compositors then re-composite the window
premultiplied, adding background light exactly at those pixels. Observed as glowing/brightened sprite vegetation
("shader flowers") under GNOME on Ubuntu 26.04, while the engine's own frame readback stays correct.

Android and the headless pbuffer path keep the upstream `EGL_ALPHA_SIZE` value. OpenGL ES and other backends are
unaffected. `cmake/BgfxEglOpaqueWindow.cmake` applies the patch during dependency configuration with the same
already-applied/reverse-check handling as the uniform cache patch.

Validation compares an engine screenshot capture (`[debug] screenshot_path`) against a compositor window capture of
the same frame: the engine capture must be opaque (alpha 255) and both captures must match.

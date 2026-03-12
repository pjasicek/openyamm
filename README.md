
# OpenYAMM
Open Yet Another Might and Magic

OpenYAMM is a modern cross-platform reimplementation of the Might and Magic VIII engine written in modern C++.

The project loads the original MM8 assets while replacing only obsolete container or codec technologies.
The goal is to remain faithful to the original game while providing a clean and maintainable modern engine.

This is NOT a decompilation project. The engine is implemented from scratch.

---

# Key Principles

* Modern C++20 codebase
* Cross-platform runtime
* Preserve original gameplay data formats
* Replace obsolete containers/codecs only
* Deterministic gameplay logic
* Data-driven architecture
* Future editor support
* Modding support

---

# Asset Strategy

OpenYAMM intentionally preserves most original data formats.

Only container formats or obsolete codecs are replaced.

| Original | OpenYAMM |
|--------|--------|
| LOD archives | ZIP |
| SMK video | OGV |
| BINK video | OGV |

Preserved formats:

| Asset Type | Format |
|-----------|--------|
| gameplay tables | TXT (tab-separated) |
| textures | original bitmap formats |
| sound effects | WAV |
| music | MP3 / FLAC |
| videos | OGV |

---

# Original Data Layout

Original extracted MM8 assets are stored in:

```
data/
```

Example structure:

```
data/
    Anims/
    Data/
    Music/
```

These files come directly from extracted LOD archives and remain unchanged.

---

# Runtime Asset Packaging

The runtime does not use LOD archives.

Instead assets are packaged in ZIP containers.

Example:

```
assets/base.zip
assets/patch01.zip
mods/example.zip
```

ZIP archives contain original files reorganized for runtime loading.

For development, assets are loaded directly from `assets_dev/` on the plain filesystem so iteration does not
require ZIP repacking.

Example:

```
assets_dev/Anims/
assets_dev/Data/
assets_dev/Music/
```

The bootstrap build uses `assets_dev/` as the default development asset root.

---

# Reference Implementation

The repository includes OpenEnroth as a reference:

```
reference/OpenEnroth-git
```

It is used only for:

* reverse engineering reference
* validating asset parsing
* comparing gameplay behavior

OpenEnroth code must NOT be copied directly.

The repository also includes a mm_mapview2-master as reference for *.odm (outdoor) and *.blv (indoor) map format parsing and rendering:

```
reference/mm_mapview2-master
```

mm_mapview2 code must NOT be copied directly.

---

# Technology Stack

Core language:

* C++20

Build system:

* CMake

Libraries:

* SDL3 — platform, windowing, input, audio
* bgfx — rendering abstraction
* Dear ImGui (docking) — debug tools and future editor UI
* PhysicsFS — virtual filesystem and ZIP archive support
* FreeType — font rendering
* spdlog + fmt — logging and formatting
* FFmpeg — video decoding (OGV playback)

---

# Target Platforms

* Linux
* Windows
* macOS
* Steam Deck (future)

---

# Project Status

Early development.

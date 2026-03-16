
# AI Agent Instructions (Codex)

These rules apply to all AI-generated contributions.

---

# Core Rules

1. Generate NEW code.
2. Never copy code from OpenEnroth.
3. Use OpenEnroth only as a reference.
4. Never copy code from mm_mapview2.
5. Use mm_mapview2 only as a reference.
6. Prefer simple, maintainable solutions.
7. Follow the coding style exactly.

---

# Coding Style

Maximum line length: 120 characters.

Braces on new lines.

Example:

if (condition)
{
    doSomething();
}

Naming conventions:

Classes: CamelCase  
Methods: camelCase  
Variables: camelCase  

Member variables:

m_variable

Pointers:

pPointer

Member pointers:

m_pPointer

---

# C++ Guidelines

Use:

* C++20
* std::shared_ptr
* std::unique_ptr
* std::vector
* std::optional
* enum class

Avoid:

* raw new/delete
* global state
* unnecessary macros

Always:

* use override
* prefer const correctness
* keep headers minimal
* prefer explicit types over `auto`

Use `auto` only when it clearly improves readability or is effectively required.
Examples:

* iterators
* long or dependent template types
* obvious lambda-heavy expressions

Do not use `[[nodiscard]]`.

Prefer unqualified standard integer and size types such as `uint32_t`, `int16_t`, and `size_t`.
Do not prefix them with `std::`.

Do not use `static_cast` unless it is actually necessary for correctness or to resolve an overload/implicit conversion issue.

---

# Engine Architecture

Subsystem layers:

engine/
game/
editor/
tools/

---

# Asset Formats

OpenYAMM keeps original formats whenever possible.

Gameplay data:

TXT (tab separated)

Audio:

WAV

Music:

MP3 / FLAC

Video:

OGV

Containers:

ZIP

Map (outdoor/indoor) format:

Up to you to decide what is better - whether to re-use the odm/ddm/blv format or convert to a new format.

---

# Asset Locations

Original extracted assets:

data/

Runtime packages:

assets/*.zip

For the development, assets are contained directly on filesystem under assets_dev/, e.g.:

assets_dev/Anims/
assets_dev/Data/
assets_dev/Anims/Music/

---

# Rendering

Renderer uses bgfx.

Rendering should remain simple.

Supported features:

* static meshes
* sprites/billboards
* UI rendering
* basic lighting
* fog

Avoid unnecessary advanced rendering features.

---

# Audio

Audio is implemented using SDL3 audio subsystem.

The engine should implement its own mixer layer for:

* sound effects
* music playback
* volume groups
* fading

---

# Video

Video playback is implemented using FFmpeg decoding with OGV containers.

Video system responsibilities:

* decode video frames
* sync audio/video
* support looping playback
* support cutscene playback

---

# Editor

Editor must reuse runtime engine systems.

Avoid duplicating gameplay logic.

---

# Commit Format

Small commits.

Format:

system: short description

Example:

renderer: implement bgfx initialization
assets: add zip resource provider
audio: implement SDL mixer

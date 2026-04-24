
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

# Repository Workflow

OpenEnroth reference repository:

reference/OpenEnroth-git/

Rules:

* Use the local OpenEnroth checkout above as the reference source.
* Do not search OpenEnroth on the web when the local reference is available.
* Never copy code from OpenEnroth, only inspect it for behavior and structure.

Preferred build command:

cmake --build build --target openyamm -j25

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

Indoor/outdoor shared gameplay rule:

* Treat gameplay systems as shared by default.
* Fixes for HUD, UI screens, input semantics, keybinds, inventory, items,
  dialogue, shops, chests, rest, spell casting, projectiles, particles,
  combat rules, monster AI, party state, qbits, journal, save/load, audio
  reactions, and gameplay FX should normally be implemented in shared gameplay
  code.
* Do not implement separate indoor-only or outdoor-only fixes for those systems
  unless the behavior truly depends on BLV/ODM world representation.
* Indoor/outdoor-specific code should normally be limited to map loading,
  geometry rendering, visibility/culling, picking, LOS, collision, floor
  resolution, movement integration, projectile collision against world
  geometry, event-face/decor/mechanism lookup, and world-specific decal
  placement.
* If a bug appears in only indoor or only outdoor, first check whether the
  shared system is being called with different data or missing world hooks.
  Prefer fixing the shared path or the world hook over adding divergent logic
  to `IndoorGameView` or `OutdoorGameView`.
* Do not add adapters or forwarding layers that only hide duplicated ownership.
  Shared ownership should live in shared gameplay code.

---

# Current Wiggum Loop

Active loop:

* Overnight missing-features and bugfixes.

Authoritative files:

* Master plan: `implementation_plan.md`
* Executable queue: `TASK_QUEUE.md`
* Acceptance: `ACCEPTANCE.md`
* Progress: `PROGRESS.md`
* Runner: `scripts/run_refactor.sh`

Loop rules:

* Do not execute `implementation_plan.md` linearly.
* Use `TASK_QUEUE.md` as the executable task order.
* Work one coherent implementation slice at a time, or a tightly related micro-batch when needed to keep the build
  passing.
* Prioritize active regressions before larger features.
* Keep shared gameplay fixes in shared gameplay systems unless the behavior truly depends on BLV/ODM world data.
* Do not duplicate outdoor gameplay paths into indoor.
* Do not add callback bags or forwarding adapters that only hide duplicated ownership.
* Add doctest/unit coverage for pure logic when feasible.
* Add focused headless coverage for runtime/map behavior when unit tests are not enough.
* Update `PROGRESS.md` and `TASK_QUEUE.md` after each meaningful slice.
* Update `ACCEPTANCE.md` only when criteria are actually satisfied.
* Remove temporary diagnostics and noisy logs before marking a task complete.

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

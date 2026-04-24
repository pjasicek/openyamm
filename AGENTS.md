
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

# Current subsystem refactor loops

Authoritative source:

- `docs/world_particle_fx_extraction_plan.md`

Execution control files:

- `PLAN.md`
- `ACCEPTANCE.md`
- `TASK_QUEUE.md`
- `PROGRESS.md`

Execution rules:

- `docs/world_particle_fx_extraction_plan.md` is authoritative for the current refactor loop.
- Do not execute the detailed plan linearly if a smaller coherent slice is safer.
- Use `PLAN.md` for condensed goals.
- Use `TASK_QUEUE.md` as the executable work queue.
- Work in small coherent extraction batches.
- Keep particle FX shared by default.
- Extract `ParticleRenderer`, particle render resources, `ParticleSystem` ownership, projectile trail/impact particles,
  and party spell world particles into shared FX code.
- Outdoor/indoor should only supply genuinely world-specific facts such as view/camera, floor placement, visibility, or
  world-specific emitters.
- Do not add indoor-only spell/projectile particle recipes.
- Do not add callback bags or adapter layers that only hide duplicated ownership.
- Keep the implementation coarse and readable; avoid `Decision`, `Patch`, `EffectDecision`, command-vector, or
  micro-struct extraction plumbing unless it is truly necessary.
- Preserve outdoor particle behavior before wiring indoor.
- Keep the repository buildable after each meaningful slice.
- Update `TASK_QUEUE.md` and `PROGRESS.md` after each meaningful slice.

Validation commands:

- `cmake --build build --target openyamm_unit_tests -j25`
- `ctest --test-dir build --output-on-failure`
- `cmake --build build --target openyamm -j25`

Focused validation guidance:

- Run `timeout 300s build/game/openyamm --headless-run-regression-suite projectiles` after projectile FX ownership
  changes.
- Run `timeout 300s build/game/openyamm --headless-run-regression-suite indoor` after indoor FX wiring changes.
- Manual smoke is required before closing the loop:
  - outdoor projectile trails and impact particles visible;
  - outdoor party spell world particles visible;
  - indoor Fire Bolt / Sparks / Dragon Breath trails visible;
  - indoor projectile impact particles visible;
  - indoor party spell world particles visible.

Stopping conditions:

- Stop only if all acceptance criteria are satisfied and recorded in `PROGRESS.md`.
- Or if `PROGRESS.md` contains exactly: `- Hard blocker: YES`

Context recovery:

- If context becomes compressed or unclear, re-read:
  - `AGENTS.md`
  - `PLAN.md`
  - `ACCEPTANCE.md`
  - `TASK_QUEUE.md`
  - `PROGRESS.md`
  - `docs/world_particle_fx_extraction_plan.md`

---

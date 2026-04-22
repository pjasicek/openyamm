
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

# Current subsystem refactor loop

Architectural background:
- docs/indoor_outdoor_shared_gameplay_extraction_plan.md

Current subsystem plan:
- docs/indoor_oe_collision_physics_plan.md

Execution control files:
- PLAN.md
- ACCEPTANCE.md
- TASK_QUEUE.md
- PROGRESS.md

Execution rules:
- `docs/indoor_oe_collision_physics_plan.md` is authoritative for the current indoor BLV collision/physics work.
- `docs/indoor_outdoor_shared_gameplay_extraction_plan.md` is architectural background and ownership context.
- Do not execute any plan linearly from top to bottom.
- Use PLAN.md for condensed goals.
- Use TASK_QUEUE.md as the executable work queue.
- Use the relevant subsystem document for detailed task requirements and acceptance.
- If task intent is unclear, consult only the relevant sections of the subsystem plan and architectural background, then
  continue.
- Work in small coherent slices.
- Prefer finishing one collision ownership path before starting another.
- Keep the repository buildable after each meaningful slice.
- Update TASK_QUEUE.md and PROGRESS.md after each meaningful slice.
- Do not reintroduce shared gameplay semantics into OutdoorGameView or IndoorGameView.
- Shared gameplay owns what should happen.
- Active world owns world facts and world-specific application.
- For indoor collision: indoor world code owns BLV geometry, sectors, portals, floor/ceiling queries, moving
  mechanisms, collision categories, and movement integration.
- Shared actor AI owns behavior decisions and should only receive movement/contact facts from indoor collision.
- Do not move BLV collision into shared gameplay.
- Do not replace collision ownership with callback bags or adapters that hide ownership.
- Do not copy OpenEnroth code. Use the local checkout only as a behavioral/structural reference.
- The current reduced indoor actor navigation radius is a temporary workaround and must not be treated as the final
  solution.
- The target is an OE-like swept iterative indoor resolver, not destination-position collision plus portal-specific
  heuristics.

Validation commands:
- cmake --build build --target openyamm -j25
- ctest --test-dir build --output-on-failure

Manual smoke tests to note in PROGRESS.md when relevant:
- `blv18` Naga Vault: large Naga actors can pass through portals without perfect center alignment
- indoor actors do not pass through closed doors/walls
- indoor actors slide along walls/portal frames instead of getting pinned
- indoor actor-vs-actor crowding blocks overlap without jamming every portal
- indoor party collides with hostile actors
- opened-door pocket movement does not jitter

Stopping conditions:
- Stop only if all acceptance criteria are satisfied and recorded in PROGRESS.md
- Or if PROGRESS.md contains exactly: - Hard blocker: YES

Context recovery:
- If context becomes compressed or unclear, re-read AGENTS.md, PLAN.md, ACCEPTANCE.md, TASK_QUEUE.md, PROGRESS.md, and:
  - docs/indoor_oe_collision_physics_plan.md
  - docs/indoor_outdoor_shared_gameplay_extraction_plan.md

# AI Agent Instructions

These rules apply to all AI-generated contributions in this repository.

## Core Rules

- Generate new code. Never copy code from OpenEnroth or mm_mapview2.
- Use `reference/OpenEnroth-git/` and mm_mapview2 only as behavioral/structural references.
- Prefer simple, maintainable solutions over clever abstractions.
- Do not add adapter/forwarding layers that only hide duplicated ownership.
- Keep temporary diagnostics and noisy logs out of final changes.

## Workflow

- Use the local OpenEnroth checkout at `reference/OpenEnroth-git/`; do not search OpenEnroth on the web when local
  reference is available.
- Preferred build command: `cmake --build build --target openyamm -j25`.
- Prefer doctest/unit coverage for pure logic.
- Use focused headless coverage for runtime/map behavior when unit tests are not enough.
- If a task explicitly names planning documents, follow those documents for that task only; do not treat stale plans as
  active global instructions.

## Coding Style

- C++20.
- Maximum line length: 120 characters.
- Braces on new lines.
- Naming: classes `CamelCase`, methods/variables `camelCase`, members `m_variable`.
- Pointer names: `pPointer`; member pointers: `m_pPointer`.
- Prefer const correctness and minimal headers.
- Prefer explicit types over `auto`; use `auto` only when it clearly improves readability or is effectively required.
- Do not use `[[nodiscard]]`.
- Prefer unqualified integer and size types: `uint32_t`, `int16_t`, `size_t`.
- Avoid raw `new`/`delete`, global state, unnecessary macros, and unnecessary `static_cast`.
- Always use `override` where applicable.

Example:

```cpp
if (condition)
{
    doSomething();
}
```

## Architecture

Subsystem layers:

- `engine/`
- `game/`
- `editor/`
- `tools/`

Treat gameplay systems as shared by default. Fixes for HUD, UI screens, input/keybind semantics, inventory, items,
dialogue, shops, chests, rest, spell casting, projectiles, particles, combat rules, monster AI, party state, qbits,
journal, save/load, audio reactions, and gameplay FX should normally live in shared gameplay code.

Indoor/outdoor-specific code should normally be limited to BLV/ODM world representation:

- map loading
- geometry rendering
- visibility/culling
- picking and LOS
- collision, floor resolution, and movement integration
- projectile collision against world geometry
- event-face/decor/mechanism lookup
- world-specific decal placement

If a bug appears only indoors or only outdoors, first check whether the shared system is called with different data or
missing world hooks. Prefer fixing the shared path or the world hook over adding divergent logic to `IndoorGameView` or
`OutdoorGameView`.

## Assets And Runtime

- Keep original asset formats whenever practical: TXT gameplay data, WAV audio, MP3/FLAC music, OGV video, ZIP packages.
- Development assets live under `assets_dev/`; runtime packages live under `assets/*.zip`.
- Renderer uses bgfx. Keep rendering simple: static meshes, sprites/billboards, UI, basic lighting, fog.
- Audio uses SDL3 with an engine mixer layer for effects, music, volume groups, and fades.
- Video uses FFmpeg OGV decoding with audio/video sync and looping/cutscene support.
- Editor code must reuse runtime engine systems and must not duplicate gameplay logic.

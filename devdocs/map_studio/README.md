# OpenYAMM Map Studio

Map Studio replaces the desktop editor in `editor/`. It is one C++ core library for maps, built natively and to
WebAssembly, with three front ends: a browser editor, an agent interface (command line and MCP server), and CI.

- **Decided by the user, 2026-11-12:** outdoor maps are built as classic ODM (a height grid with buildings on it),
  the form of MM6 to MM8 and the one the engine's ground, grass, weather and sky are made for. The same plan and
  sketch can later be built as open-air BLV (the MM9 rework's form) for a map whose shape needs it; that is a
  second builder, not the default. Maps will number in the tens to hundreds, indoor and outdoor, so fix-ups live in
  the project (edits, named overrides, imported set pieces), never in a built map.
- [S3](S3.md): indoor authoring, first part: rooms of any shape, corridors, stairs and ramps that the game walks,
  wiring without scripts, projects read without installing, and the first calibration reading. Not finished.
- [S2](S2.md): editing: transactions and history, overlay projects for shipped maps, the MCP host with its
  fourteen tools, the game's development mount, and the first agent evaluation.
- [S1](S1.md): the read side: audits, reachability, the lock-and-key solve, metrics, import, renders, the old
  outdoor build, and the four cuts in `engine/` and `game/` that await review.
- [S0](S0.md): what is built (the `oymap` command line, schema v0, the slice dungeon) and what it taught. The code
  is in `openyamm-studio/` ([README](../../openyamm-studio/README.md)).
- [Handoff](HANDOFF.md): start here when picking up the work: reading order, decisions and their reasons, open
  questions, coordination with the Xeen session, the review to do before implementing.
- Research digests in [research/](research/): MCP and agent tools, editors and level design, the five test maps,
  the code survey. [design_page.html](design_page.html) is the source of the design page.
- [Implementation plan](PLAN.md): architecture, repository layout, what moves out of `engine/`, `game/` and
  `editor/`, the project format, compilers, validation, host, MCP server, web app, tests, milestones and risks.
- [Retiring `editor/`](EDITOR_RETIREMENT.md): what still depends on the old editor, what to move first, and the
  order of deletion. Done in the last milestone (S7, [S7_PLAN.md](S7_PLAN.md), 2026-11-15): the shared code is in
  `core/` and `editor/` is deleted.
- [Calibration](CALIBRATION.md): rebuilding known maps (Ravenshore, Harmondale, Temple of the Moon, Warlord's
  Fortress) from design briefs, comparing with the originals and turning the differences into fixes.
- Design proposal with research, workflow, five test maps and mockups (private artifact, revision 4):
  <https://claude.ai/artifact/SBUwCHsj81N975vCpEbYJX>

## Decisions already made (2026-11-12)

- The browser editor is a static web app with no backend. Assets come from the player's install or the repo, never
  from a server. Agents and live pairing use a local host process on the user's machine: a thin Node process over
  the native core (`oymap serve`). WebAssembly is used by the hosted page only.
- A project is exactly its text files: anyone may edit them with any tool. Revisions are content hashes and history
  is file snapshots, both in the core. Files have one canonical form and no YAML comments (`notes:` fields instead).
- Order of work: a small dungeon built end to end first (S0), then reading and checks, operations and the agent
  interface, indoor and outdoor authoring through operations, and only then the browser editor. Agents can build
  complete maps before any UI exists.
- The engine's C++ is the only implementation of map formats, scene files, compilers and checks. No TypeScript or
  Python re-implementation.
- The studio follows the design order: Plan, Shape, Build, Wire, Populate, Dress, Test.
- The studio makes what carries game rules (heights, rooms, doors, clickable faces, placement). Buildings, props and
  textures are made outside (Blender, Codex image generation, Meshy) and installed through the existing pipelines;
  the studio places them, searches the library first and uses placeholders with a brief for missing art.
- Dungeon shells are drawn as rooms; sectors and portals are derived. Doors come from a door library or are made
  from selected faces. Imported meshes keep their face settings across re-imports.
- Changes to shipped maps are scene and Lua overlays. Generated MM9 map files are never edited in place.
- Agents use the same core through `oymap` (command line, JSON) and an MCP server with about fourteen tools.
- The studio lives in `openyamm-studio/` and is built completely before the old editor is retired. Until then it
  compiles the engine and game sources it needs in place. Four tangled places in `game/` are cut apart early by
  small move-only changes (PLAN.md section 10a); nothing is copied.
- Calibration maps: Ravenshore (`mm8/out02`), Harmondale (`mm7/7out02`), Temple of the Moon (`mm7/7d06`,
  Emerald Island) and Warlord's Fortress (`mm6/6d16`). Held out: New Sorpigal (`mm6/oute3`), Goblinwatch
  (`mm6/6d01`), Shadowspire (`mm8/out06`), the Mad Necromancer's Lab (`mm8/d20`) and Gharik's Forge (`mm6/6d18`).
  First new map: Xeen Act I (`devdocs/xeen/`).

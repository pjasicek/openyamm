# OpenYAMM

OpenYAMM is Open Yet Another Might and Magic: a modern C++ reimplementation of
Might and Magic VI, VII, and VIII, inspired by MMMerge and built on an engine
that started from Might and Magic VIII.

It uses the original game data with HD artwork, a new HUD and menus, modern
rendering, and UX improvements.

## Status

OpenYAMM is playable across Might and Magic VI, VII, and VIII, including
continent travel between the games. Windows, Linux, and Android builds are
supported.

The games share combat, spells, dialogue, quests, inventory, party state, and
save/load systems. Development is active, with ongoing work on gameplay
compatibility, polish, tooling, and the editor.

## Features

- HD textures, items, equipment, portraits, and interface backgrounds
- HD MM6 monsters
- New Obsidian HUD, menus, inventory, dialogue, and journal screens
- Indoor and outdoor water with reflections, lightmaps, and shadows
- Modeled MM6 ships and HD decorations
- Enemy health bars, floating damage, and party recovery indicators
- Android touch controls and context actions

## Screenshots

**New HUD**

![Obsidian gameplay HUD with a five-character party](res/showcase/gameplay-hud.webp)

**HD items and inventory**

![God Lich inventory and equipped paperdoll](res/showcase/inventory.webp)

**Water and reflections**

![Outdoor water with bridge and sailboat reflections](res/showcase/water-shoreline.webp)

**HD MM6 monsters**

![HD MM6 hydra variants](res/showcase/creatures-hydras.webp)

**Android touch controls**

![Android gameplay in New Sorpigal with touch controls](res/showcase/android-gameplay.webp)

<details>
<summary>More interface screenshots</summary>

**Main menu**

![New main menu](res/showcase/main-menu.webp)

**Quest journal**

![Quest journal with restored fonts and navigation icons](res/showcase/journal-quests.webp)

**HD equipment**

![HD plate armor and inventory items](res/showcase/equipment-plate.webp)

**MM6 Town Portal**

![HD Enroth Town Portal map](res/showcase/town-portal-mm6.webp)

**MM8 Town Portal**

![HD Jadame Town Portal map](res/showcase/town-portal-mm8.webp)

**Recovery indicator and enemy health bars**

![Party recovery indicator after an attack, with goblin health bars](res/showcase/hud-recovery-combat.webp)

</details>

<details>
<summary>More rendering and combat screenshots</summary>

**Indoor water**

![Water and reflections in the Tomb of VARN](res/showcase/water-varn.webp)

**Lightmaps and shadows**

![Lightmaps and shadows around buildings and a timber gate](res/showcase/lighting-street.webp)

**HD decorations**

![HD flowers, trees, and stonework in New Sorpigal](res/showcase/world-decorations.webp)

**Modeled MM6 ships**

![Modeled MM6 ships at the harbor](res/showcase/world-ships.webp)

**HD MM6 dragon**

![HD MM6 red dragon](res/showcase/creatures-dragon.webp)

**Floating damage**

![Floating damage number above a Thunder Lizard](res/showcase/combat-floating-damage.webp)

</details>

<details>
<summary>More Android screenshots</summary>

**Shop interaction**

![Touch targeting and the shop interaction button](res/showcase/android-shop.webp)

**NPC interaction**

![NPC target highlight and the conversation button](res/showcase/android-npc.webp)

</details>

## Assets

Development assets are loaded from:

```text
assets_dev/
```

The default development layout is:

```text
assets_dev/
  engine/             shared tables, scripts and presentation
  worlds/mm6/         world-local maps and presentation
  worlds/mm7/
  worlds/mm8/
```

Runtime packages can be distributed as ZIP archives under:

```text
assets/
```

The engine keeps practical original asset formats such as TXT gameplay tables, BMP-style
art assets, WAV sound effects, MP3/FLAC music, and OGV video. Legacy archive and video
container formats are replaced for runtime use.

Runtime assets and the prebuilt Android sprite profile are stored directly
in Git, so a normal clone can build and launch against `assets_dev` and CI can package
Android without texture encoding or Git LFS. The lossless sprite inputs, creature
master bank, original extractions and editor assets are optional local authoring
data. See [asset storage and optional review tools](tools/ASSET_STORAGE.md).
The MM9 world payload is currently local and is excluded from the portable checkout.

## Building

The engine uses C++20, SDL3, bgfx, PhysicsFS, FFmpeg, and Lua. Gameplay tables
use tab-separated text, and scene and UI layouts use YAML.

Native macOS and iPhone/iPad builds (Metal renderer, `.app` bundles, the touch
interface on iOS): see [Building for macOS and iOS](BUILDING-APPLE.md).

Requirements:

- CMake 3.22 or newer
- C++20 compiler
- Git and Python 3.11 or newer
- standard native build tools for your platform

CMake fetches and builds the project dependencies, including Lua 5.4. A separate
system Lua development package is not required.

Configure and build:

```sh
cmake -S . -B build
cmake --build build --target openyamm -j25
```

Run:

```sh
./build/game/openyamm
```

Build tests:

```sh
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests
```

Build the editor:

```sh
cmake -S . -B build -DOPENYAMM_BUILD_EDITOR=ON
cmake --build build --target openyamm-editor -j25
```

Run the editor:

```sh
./build/editor/openyamm-editor
```

## Visual Checks

For repeatable visual checks, see [Desktop runs and native screenshot tours](tools/RUN_GAME.md).
The game can save PNGs directly through bgfx, including the HUD, on Wayland or X11. Use the debug
console command `screenshot [name]`, launch-time capture settings, or a YAML tour to capture several
camera poses in one run. Ready-to-run MM6/MM7/MM8 water viewpoints are in
[`tools/screenshot_tours/`](tools/screenshot_tours/).

## Releases and Updates

Releases are built, checked, signed and published by the
[Packages](https://github.com/pjasicek/openyamm/actions/workflows/packages.yml) workflow when a `vX.Y` tag is pushed
(after an approval), to `https://jasicek.net/openyamm/` and GitHub Releases; see [Releases](packaging/RELEASE.md) and
[Incremental updates](packaging/UPDATER_PLAN.md). Every push to `main` builds and checks the same packages without publishing.

Players download a small package: `OpenYAMM-X.Y-windows-x64.zip`, `OpenYAMM-X.Y-linux-x64.tar.gz` (any distribution
with glibc 2.35 or newer; everything else is linked into the game) or the Android APK. The first start downloads the
game content, and the game updates itself afterwards, downloading only the content packs that changed.

On Windows and Linux, saves, `settings.ini` and `openyamm.log` live in the extracted folder next to the game, and
updates never touch them; on Android they live in the app's external storage. `settings.ini` holds only the values a
player changed; every other setting follows the game's defaults, including defaults a later release changes. The Load
screen imports saves from another installation folder and opens the data folder. Each run rewrites `openyamm.log` with
everything the game prints, so a failed start or a crash can be diagnosed without a console; headless commands keep
no log file.

## Useful CMake Options

```text
OPENYAMM_BUILD_EDITOR=ON      Build the editor target
OPENYAMM_BUILD_TOOLS=ON       Build asset and data tooling
OPENYAMM_BUILD_TESTS=ON       Build unit tests
OPENYAMM_DEV_ASSETS_DIR=...   Override the development asset directory
OPENYAMM_USE_SYSTEM_SDL3=ON   Use an installed SDL3 package
```

## Repository Layout

```text
engine/              shared runtime systems
game/                game application and gameplay systems
editor/              editor application
tools/               asset cooking, reusable review apps and development tools
tests/               unit and regression tests
assets_dev/          development asset root
assets_cooked/android/sprites_new/  prebuilt Android creature GPU packages
assets_source/       optional authoring banks (local; selected binaries can use LFS)
assets_editor_dev/   optional local editor asset root
level_generation/    optional local generation projects (excluded from Git)
reference/           local behavioral/data references (excluded from Git and LFS)
res/                 README screenshots
```

## License

OpenYAMM's original source code, build scripts, tests, and documentation are licensed under the
**GNU General Public License, version 3 or later** (`GPL-3.0-or-later`), unless otherwise stated.
Copyright (C) 2026 Petr Jasicek (pjasicek).

See [LICENSE](LICENSE) for the full license and [COPYRIGHT](COPYRIGHT) for the attribution and scope.
Distributors must preserve the applicable copyright notices and make the corresponding source available
as required by the GPL. OpenYAMM is provided without warranty.

Third-party dependencies retain their own licenses. Original Might and Magic assets, imported game data,
and their converted or restored versions are not covered by the OpenYAMM code license; their distribution
requires the appropriate rights from their respective rights holders.

## Editor Screenshots

![Editor screenshot 1](res/editor_1.webp)
![Editor screenshot 2](res/editor_2.webp)

## Credits

OpenYAMM builds on years of work and research from the Might and Magic community,
with thanks due to:

- the OpenEnroth development team
- Rodril and all MMMerge contributors

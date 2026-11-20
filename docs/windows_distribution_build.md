# Windows Distribution Build

This document describes a local Windows 10 build of the release package using MSYS2 UCRT64 MinGW. Published releases
are built by CI instead (see [Releases](../packaging/RELEASE.md)).

The end result is a single zip file holding the versioned installation of UPDATER_PLAN.md 9.1: the launcher
`OpenYAMM.exe`, `app/<version>/openyamm.exe` with its shaders, and the content packs under `assets/packs/`
(none with `-DOPENYAMM_RELEASE_THIN=ON`: the game then downloads them on the first start). No `settings.ini` ships;
saves and settings are created next to the game.

## Install Toolchain

Install Git for Windows and MSYS2.

Open the **MSYS2 UCRT64** shell, not the plain MSYS shell, then update MSYS2:

```bash
pacman -Syu
```

If MSYS2 asks you to close the shell, close it, reopen **MSYS2 UCRT64**, then run the update again:

```bash
pacman -Syu
```

Install the build packages:

```bash
pacman -S --needed \
  git \
  make \
  mingw-w64-ucrt-x86_64-toolchain \
  mingw-w64-ucrt-x86_64-cmake \
  mingw-w64-ucrt-x86_64-ninja \
  mingw-w64-ucrt-x86_64-pkgconf \
  mingw-w64-ucrt-x86_64-python
```

Optional debugger:

```bash
pacman -S --needed mingw-w64-ucrt-x86_64-gdb
```

## Prepare Source Tree

From the **MSYS2 UCRT64** shell:

```bash
cd /c/Users/YOUR_USER/github
git clone YOUR_REPO_URL OpenYAMM
cd OpenYAMM
```

If the repository already exists, just `cd` into it.

Make sure the final source assets are present:

```bash
ls assets_dev/engine
ls assets_dev/worlds
```

The Windows distribution package target builds runtime asset zips from `assets_dev/`. It does not reuse existing
`assets/*.zip` files.

## Configure Release Build

```bash
cmake -S . -B build-windows-release -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DOPENYAMM_BUILD_TESTS=OFF \
  -DOPENYAMM_BUILD_EDITOR=OFF \
  -DOPENYAMM_BUILD_TOOLS=OFF
```

If the source assets live somewhere else, pass an explicit asset source directory:

```bash
cmake -S . -B build-windows-release -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DOPENYAMM_DEV_ASSETS_DIR=C:/path/to/assets_dev \
  -DOPENYAMM_BUILD_TESTS=OFF \
  -DOPENYAMM_BUILD_EDITOR=OFF \
  -DOPENYAMM_BUILD_TOOLS=OFF
```

The first configure step needs internet access because CMake fetches dependencies.

OpenYAMM configures bx's optional directory-reader implementation off for MinGW because MinGW-w64's `dirent` does not
provide the `d_type` field it requires. No manual patching under the build directory is needed.

## Build

```bash
cmake --build build-windows-release --target openyamm --parallel 16
```

Optional smoke test from the build tree:

```bash
./build-windows-release/game/openyamm.exe
```

## Build Distribution Zip

```bash
cmake --build build-windows-release --target openyamm_release_package --parallel 16
```

Expected output:

```text
build-windows-release/release/OpenYAMM-windows-x64-Release.zip
```

The zip should contain:

```text
OpenYAMM/OpenYAMM.exe
OpenYAMM/app/current
OpenYAMM/app/dev/openyamm.exe
OpenYAMM/app/dev/OpenYAMM-launcher.exe
OpenYAMM/app/dev/index.json
OpenYAMM/app/dev/runtime/shaders/...
OpenYAMM/assets/packs/*.zip
```

The package target also tries to collect required runtime DLLs, including MinGW runtime DLLs if they are dynamically
linked.

## Verify The Package

Inspect the zip:

```bash
cmake -E tar tf build-windows-release/release/OpenYAMM-windows-x64-Release.zip | head -80
```

Test the exact zip from a clean directory:

```bash
mkdir -p /tmp/openyamm-dist-test
cd /tmp/openyamm-dist-test
cmake -E tar xf /c/Users/YOUR_USER/github/OpenYAMM/build-windows-release/release/OpenYAMM-windows-x64-Release.zip
cd OpenYAMM
./OpenYAMM.exe
```

If the game launches from the extracted folder, the distribution package is structurally valid.

## Publish

Published releases come from CI only: a `vX.Y` tag builds, checks, signs and uploads them (see
[Releases](../packaging/RELEASE.md)). A local zip is for testing.

No Visual C++ redistributable should be required when building with MinGW and packaging the required DLLs. Windows
SmartScreen may warn for unsigned executables; signing is the long-term fix for public website distribution.

Only distribute packaged game assets when you have the right to distribute them.

## Running From PowerShell

If invoking the build from PowerShell instead of an already-open **MSYS2 UCRT64** shell, set `MSYSTEM=UCRT64` before
sourcing `/etc/profile` so MSYS2 prepends `/ucrt64/bin` to `PATH`:

```powershell
C:\msys64\usr\bin\bash.exe -lc "export MSYSTEM=UCRT64 && export CHERE_INVOKING=1 && source /etc/profile && cd /home/pjasicek/openyamm && cmake --build build-windows-release --target openyamm --parallel 16"
```

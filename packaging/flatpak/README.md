# OpenYAMM Flatpak

This local Flatpak packaging uses the same asset layout as the Windows release package:

- `assets/engine.zip`
- `assets/worlds/*.zip`

The build script creates those zips fresh from `assets_dev/` in the staged Flatpak source tree, so local root
`assets/*.zip` files do not have to be regenerated before building Flatpak packages.

Build and install locally after the Flatpak runtime and SDK are installed:

```sh
packaging/flatpak/build_flatpak.sh
flatpak run io.github.openyamm.OpenYAMM
```

The same flow is available from CMake:

```sh
cmake --build build --target openyamm_flatpak_release
```

The build script uses the online CPU count minus two parallel jobs by default. Override it when needed:

```sh
packaging/flatpak/build_flatpak.sh --jobs=8
```

Clean local Flatpak build output and legacy `.flatpak-builder` state:

```sh
cmake --build build --target openyamm_flatpak_clean
```

The wrapper runs OpenYAMM from the app data directory so `settings.ini` and `saves/` stay writable. Bundled assets are
mounted read-only from `/app/share/openyamm/assets`.

To let the script install missing Freedesktop runtime dependencies from Flathub, run:

```sh
packaging/flatpak/build_flatpak.sh --add-flathub --install-deps
```

Release builds derive their packaged `settings.ini` from `settings_release.ini` and replace only the `[assets] root`
value with the Flatpak asset path.

Flatpak 1.12 or newer is required for automatic runtime installation from current Flathub metadata. If the runtime and
SDK are already installed, do not pass `--install-deps`.

The build script stages a minimal source tree under `build/flatpak/source` before invoking `flatpak-builder`. This keeps
development assets, Android build outputs, existing CMake build trees, and reference checkouts out of the Flatpak source
copy. Builder state is written under `build/flatpak/state` instead of the repository root `.flatpak-builder` directory.

The manifest currently allows network during the build because the CMake build fetches third-party dependencies. A
Flathub-ready manifest should replace that with explicit Flatpak sources for each dependency.

The local manifest does not install AppStream metainfo because older Ubuntu `flatpak-builder` packages may lack
`appstream-compose`. The metainfo file is kept in this directory for later Flathub-oriented packaging.

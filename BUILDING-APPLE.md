# Building OpenYAMM for macOS and iOS

OpenYAMM runs natively on macOS and on iPhone and iPad: no emulation or translation layer, rendering with bgfx's Metal
backend. Both builds produce `OpenYAMM.app`. The iOS build uses the touch interface and the texture packages of the
Android version.

These instructions were tested on an Apple silicon Mac with macOS 27, Xcode 27.1 (macOS 27.0 and iOS 27.1 SDKs), CMake
3.30, Ninja 1.10 and Python 3.11, running the iOS build in the iOS 27.0 Simulator.

## Requirements

- A Mac with Apple silicon. Builds are arm64 only.
- Xcode with the macOS SDK, and the iOS SDK and Simulator runtime for iOS builds. The command line tools alone are not
  enough for iOS.
- CMake 3.22 or newer and Ninja (for example `brew install cmake ninja`).
- Git and Python 3.11 or newer, as for the other platforms. Python must be on `PATH` when CMake configures the macOS
  build: the host tools need it. Packaging assets with `tools/package_runtime_assets.py` also needs PyYAML
  (`python3 -m pip install pyyaml`).
- `make`, used to build FFmpeg.

CMake fetches the other dependencies (SDL3, bgfx, FFmpeg, Lua, ...) as on Linux.

## macOS

```sh
packaging/apple/build_macos.sh
open build/macos/game/OpenYAMM.app
```

The script configures `build/macos` (Release, arm64, macOS 14.0 deployment target), builds `openyamm` and the host
shader compiler, and signs the bundle ad hoc. `--debug` builds Debug, `--tests` also builds `openyamm_unit_tests`, and
`--build-dir` chooses another build directory. The equivalent CMake commands are:

```sh
cmake -S . -B build/macos -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=14.0 -DOPENYAMM_COOK_ON_BUILD=OFF
cmake --build build/macos --target openyamm
```

`OPENYAMM_COOK_ON_BUILD=OFF` skips the asset cooks, which need the `assets_source` checkout; the script turns them on
when `assets_source/worlds` exists.

### Where the app finds its files

- Shaders (`runtime/shaders/metal`) and the icon are inside the bundle, in `Contents/Resources`. The bundle carries no
  `settings.ini`: the defaults are built in, and `settings.ini` holds only the choices a player changes.
- Launched from Finder, the app keeps its user data in `~/Library/Application Support/OpenYAMM`: `settings.ini`,
  `saves/` and `openyamm.log`. The Apple entry point passes that folder as `--user-data` unless the command line names
  another one, so it also takes precedence over a release installation's own folder, which for a bundle with packaged
  assets would be the bundle itself.
- Launched from a directory that already has a `settings.ini`, such as the repository root, it keeps that directory,
  like the Linux binary:

  ```sh
  build/macos/game/OpenYAMM.app/Contents/MacOS/OpenYAMM
  ```

- With an empty `[assets] root`, the app uses `Contents/Resources/assets` if the bundle has one, and otherwise the
  checkout's `assets_dev` (`OPENYAMM_DEV_ASSETS_DIR`), as on Linux.

### A self-contained app

`--package-assets` packages `assets_dev` with `tools/package_runtime_assets.py` (desktop texture profile) into
`OpenYAMM.app/Contents/Resources/assets`, as the content packs of the release packages (`index.json` and `packs/`, about
5.2 GB):

```sh
packaging/apple/build_macos.sh --package-assets
```

The bundle then runs on another Mac without the checkout. It is signed ad hoc only: a copy downloaded from the internet
needs a Developer ID signature and notarization, or the user has to allow it in System Settings. Set
`-DOPENYAMM_APPLE_BUNDLE_IDENTIFIER` to use another bundle identifier.

### Unit tests

```sh
packaging/apple/build_macos.sh --tests
(cd build/macos && ./tests/openyamm_unit_tests)
```

## iOS and iPadOS

The iOS build is a cross build. It needs a configured macOS build for the host shader compiler
(`OPENYAMM_HOST_SHADERC`) and the sprite atlas checker, and reuses that build's dependency checkouts.

```sh
packaging/apple/build_macos.sh                   # once, for the host tools
packaging/apple/build_ios.sh --simulator         # build/ios-simulator/game/OpenYAMM.app
packaging/apple/build_ios.sh                     # build/ios/game/OpenYAMM.app, for devices
```

Both use arm64 and an iOS 26.0 deployment target. The equivalent CMake configuration is:

```sh
cmake -S . -B build/ios -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_SYSTEM_NAME=iOS \
    -DCMAKE_OSX_SYSROOT="$(xcrun --sdk iphoneos --show-sdk-path)" \
    -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=26.0 \
    -DOPENYAMM_BUILD_TESTS=OFF -DOPENYAMM_HOST_SHADERC="$PWD/build/macos/openyamm_shaderc"
cmake --build build/ios --target openyamm
```

Without `FETCHCONTENT_SOURCE_DIR_<NAME>` options (the script passes the host build's checkouts) CMake downloads the
dependencies again.

### Game data

iPhone and iPad GPUs have no BC texture formats, so iOS uses the Android texture profile: the ASTC/ETC2 textures in
`assets_cooked/android` and the x2 surface textures. Package them with the host sprite atlas checker:

```sh
cmake --build build/macos --target openyamm_sprite_atlas_cook
python3 tools/package_runtime_assets.py --assets-root assets_dev --output build/ios-assets \
    --profile android --cooker build/macos/game/openyamm_sprite_atlas_cook
```

This writes `index.json` and `packs/`, the content packs of the release packages, about 3.2 GB. There are two
ways to get them onto a device:

- Copy the folder into the app's Documents folder as `assets/`. The app keeps its user data in Documents
  (`settings.ini`, `saves/`, `openyamm.log`) and reads `assets/` there. Finder shows the folder under the device's Files tab and the Files app under
  On My iPhone, because the app enables file sharing. From the command line:

  ```sh
  xcrun devicectl list devices
  xcrun devicectl device copy to --device <device id> --domain-type appDataContainer \
      --domain-identifier io.github.openyamm.OpenYAMM --source build/ios-assets --destination Documents/assets
  ```

  The data survives app updates, so later installs only copy the small app.
- Or bundle it: `packaging/apple/build_ios.sh --package-assets` packages it into `OpenYAMM.app/assets`, and the app
  prefers that copy. Each install then transfers the whole app.

### Signing and installing on a device

Device builds need an Apple Development certificate and a provisioning profile that includes the device. The script
signs with both:

```sh
packaging/apple/build_ios.sh --sign "Apple Development: Your Name (TEAMID)" \
    --profile ~/Downloads/OpenYAMM_Development.mobileprovision --bundle-id <identifier your team may use>
xcrun devicectl device install app --device <device id> build/ios/game/OpenYAMM.app
```

The profile's entitlements are copied into the signature. A free personal team cannot use `io.github.openyamm.OpenYAMM`
if another team registered it; pass `--bundle-id` with your own identifier and use it in the `devicectl` commands.
Developer Mode must be on and the device unlocked while installing and launching.

### Simulator

```sh
xcrun simctl create tmp-openyamm "iPhone 17 Pro" <iOS runtime>
xcrun simctl boot <udid>
xcrun simctl install <udid> build/ios-simulator/game/OpenYAMM.app
cp -cR build/ios-assets "$(xcrun simctl get_app_container <udid> io.github.openyamm.OpenYAMM data)/Documents/assets"
xcrun simctl launch --console-pty <udid> io.github.openyamm.OpenYAMM
xcrun simctl io <udid> screenshot screen.png
```

- `xcrun simctl list runtimes` shows the installed runtimes. In Xcode 27.1 the iOS 27.1 runtime offered no iPhone
  device type; iOS 27.0 did.
- The Simulator renders with the Mac's GPU. It does not show device-only GPU limits; for example a selector that iOS
  devices lack (see `cmake/patches/README.md`) works there. bgfx still disables BC formats for iOS builds, so the
  Simulator needs the Android-profile packages too.
- Delete a temporary simulator when done: `xcrun simctl shutdown <udid>` and `xcrun simctl delete <udid>`.

## Known limits

- arm64 only: no Intel Macs, universal binaries or x86_64 Simulator. FFmpeg is configured for a single architecture.
- Deployment targets are macOS 14.0 and iOS 26.0, the versions tested. Older systems are untested.
- macOS renders at the window's point size, like Windows and Linux; there is no Retina (high pixel density) rendering
  yet. iOS renders in device pixels, as Android does.
- bgfx's Metal backend cannot resolve multisampled depth, so ambient occlusion turns off while anti-aliasing is on (the
  game logs this), as with the other renderers except OpenGL.
- No safe-area handling: on iPhones with a camera housing, HUD elements at the screen edges can sit under it in
  landscape.
- iOS keeps the desktop texture cache sizes; Android uses smaller ones.
- bgfx creates the Metal swap chain on its render thread, and UIKit logs "Modifying properties of a view's layer off
  the main thread is not allowed" once at startup. The app runs normally.
- No App Store packaging: the iOS icon uses `CFBundleIconFiles` rather than an asset catalog, and there is no macOS
  release target, notarization or DMG.
- The updater and the first-start content download are not available yet. `engine/update/HttpTransport.cpp` has
  WinHTTP and libcurl backends only, so `GameUpdater::create` finds no updater on Apple platforms and the Updates
  option stays hidden. An NSURLSession backend would let macOS and iOS download and update the content packs, for
  example for a small TestFlight build that fetches its assets from the release server.
- The editor and `tools/run_game.sh` are not adapted to macOS.

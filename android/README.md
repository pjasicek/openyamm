# OpenYAMM Android Build

This Android project builds an SDL3-based OpenYAMM APK.

- Debug builds include `arm64-v8a` and `x86_64` for emulator testing.
- Release builds include only `arm64-v8a` for production sideloading.
- APK assets are mounted from the installed APK. Large runtime asset packages are not extracted to app storage.

The project expects an SDL3 source tree. By default it uses the desktop build's
fetched SDL checkout at:

```text
../build/_deps/sdl3-src
```

Build a debug APK from the repository root using the lightweight wrapper:

```sh
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 android/gradlew :app:assembleDebug
```

Or point at a different SDL3 source checkout:

```sh
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 android/gradlew :app:assembleDebug -POPENYAMM_SDL3_SOURCE_DIR=/path/to/SDL
```

The Android SDK must be discoverable through `ANDROID_HOME`, `ANDROID_SDK_ROOT`,
or `android/local.properties`.

The expected debug output is:

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

Android builds package `android/settings.ini` as the first-launch settings profile. The installed app copies that
profile to its app-specific external `settings.ini` only when the file is missing. Saves and settings are stored under
`Android/data/org.openyamm.android/files/`, where they can be copied through USB file transfer. Android may restrict
on-device file managers from browsing this directory, and uninstalling the app removes it. Profile-version migrations
update Android-required defaults without replacing user-adjustable settings.

To build, start/reuse an emulator, install, launch, and follow logs:

```sh
android/run_debug_emulator.sh
```

Useful overrides:

```sh
OPENYAMM_AVD_NAME=openyamm_api35 android/run_debug_emulator.sh
ANDROID_HOME=/path/to/android-sdk android/run_debug_emulator.sh
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 android/run_debug_emulator.sh
```

## Release APK

Release signing can be configured through `android/signing.properties`, Gradle
properties, or the `OPENYAMM_ANDROID_*` environment variables. For local builds,
the release script can create `android/keystores/openyamm-release.jks`.

```sh
android/build_release_apk.sh
```

Outputs:

```text
android/app/build/outputs/apk/release/app-release.apk
android/app-release.apk
```

To build an optimized x86_64 release APK, start or reuse the configured emulator, install the APK, launch it, and
follow logs:

```sh
android/run_release_emulator.sh
```

The emulator runner signs this local release build with the standard Android debug keystore. It does not replace
`android/app-release.apk`, which is reserved for the production-signed hosted build. Pass `--no-logcat` to return after
launching the game.

Useful release-runner overrides:

```sh
OPENYAMM_BUILD_RELEASE_APK=0 android/run_release_emulator.sh
OPENYAMM_ANDROID_UNINSTALL_ON_SIGNATURE_MISMATCH=0 android/run_release_emulator.sh
OPENYAMM_ANDROID_RELEASE_ABIS=arm64-v8a android/run_release_emulator.sh
```

For manual public builds, bump `openyamm.android.versionName` and `openyamm.android.versionCode` in
`android/gradle.properties`, or provide `OPENYAMM_ANDROID_VERSION_NAME` and `OPENYAMM_ANDROID_VERSION_CODE`.
The code must exceed every published APK being replaced; the local defaults match the original 1.0 release
(`1.0` / `10000`). CI uses `10000 + GITHUB_RUN_NUMBER * 100 + GITHUB_RUN_ATTEMPT` for commits, nightlies and
tags. Tagged builds keep their `X.Y` display name; other builds use `nightly-<run>.<attempt>`.
This allows updates from 1.0 to a nightly and from a nightly to a later tagged build.
Keep the same workflow and signing key to preserve this sequence. See
`android/WEB_HOSTING_CHECKLIST.md` for the hosted APK checklist.

Check the workflow's version handling without building an APK:

```sh
python3 packaging/test_android_versions.py
```

## Package CI Signing

Android shaders target OpenGL ES 3.0, matching the manifest's minimum renderer requirement.
The build generates `AndroidShaderPaths.h` from the CMake runtime shader list. Startup checks
the extracted files against the APK contents and updates missing or changed shaders, including
changes that preserve file size. User settings and saves remain in the existing external directory.

CI builds the signed ARM64 release APK, verifies its signature, resolved version metadata and packaged ABI, and generates a SHA256 checksum
before uploading it. Emulator runtime checks are run manually.

The asset filter retains underscore-prefixed directories so the `_legacy/sprites_original` bake dependencies
included in `engine.zip` also reach the APK. Android's default `<dir>_*` exclusion drops these files and prevents
baked outdoor maps from loading.

Run the runtime check with Python Pillow installed on a disposable emulator (it replaces that emulator's game settings):

```sh
python3 android/test_release_apk.py android/app-release.apk \
  --serial emulator-5554 --output /tmp/openyamm-android-test
```

To test an in-place update, add `--baseline-apk <previous.apk> --save <save.oysav>`.
Both APKs must use the same signing certificate, and the candidate must have a higher version
code. The test installs with `adb install -r`, checks that settings and save bytes survive,
and loads that save. Use `--world` and `--map` when testing another world or map.
Use `--resume-cycles N` to repeat the lifecycle checks (default: 3; 0 skips them).
The check requires a rendered map and verifies every extracted shader against the APK. It also checks rendering after
Home, switching to Settings, and screen off/on, requiring surface recreation and the same game process throughout.
Logs and screenshots are saved in the output directory.

For a release build using already prepared asset ZIPs outside the ordinary `build/android-assets/` directory,
pass `-Popenyamm.android.runtimeAssetsDir=/absolute/path` to Gradle. The directory must contain
`engine.zip` and `worlds/{mm6,mm7,mm8,mmmerge}.zip`.

The GitHub Actions workflow uses the same signed release path for nightly and tagged packages. Configure these
repository secrets before running it:

- `OPENYAMM_ANDROID_KEYSTORE_BASE64`: the release keystore encoded as one-line base64
- `OPENYAMM_ANDROID_KEYSTORE_PASSWORD`: the keystore password

The workflow expects the release script's default `openyamm` key alias and uses the keystore password as the key
password. A keystore created by `android/build_release_apk.sh` has those defaults. On Linux, encode it with:

```sh
base64 -w 0 android/keystores/openyamm-release.jks
```

On Windows PowerShell, use:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("android\keystores\openyamm-release.jks"))
```

Keep the keystore and secrets backed up. Every published update for `org.openyamm.android` must use the same signing
key; replacing it requires users to uninstall the existing app before installing the new build.

### Cooked creature textures

`android/repack_runtime_assets.sh` validates the prebuilt Android ETC2/EAC packages in
`assets_cooked/android/sprites_new/` and creates `build/android-assets/engine.zip` plus world ZIPs.
It checks the complete family set, animation/placement metadata and palette lookups against the
desktop BC7 installation. Repacking and CI need no authoring images, Git LFS or texture encoding.
Each ZIP contains one profile; Gradle rejects desktop sprite packages and keeps `.oyatlas` entries
uncompressed in the APK.

After editing accepted artwork, authors explicitly run `python3 tools/cook_sprite_atlases.py --profile desktop`
and `python3 tools/cook_sprite_atlases.py --profile android` from the repository root, using their local
`assets_source/engine/sprites_new/` inputs. Commit the updated prebuilt profiles before repacking.
See [the deployment contract](../tools/creatures/docs/SPRITE_RUNTIME_DEPLOYMENT.md).

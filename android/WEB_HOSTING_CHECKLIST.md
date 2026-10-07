# Android Web Hosting Checklist

Use this for sideload releases hosted outside Google Play.

## Release Artifact

- Build command: `android/build_release_apk.sh`
- Hosted file: `android/app-release.apk`
- Gradle output: `android/app/build/outputs/apk/release/app-release.apk`
- Package id: `org.openyamm.android`
- Minimum Android version: Android 6.0 / API 23
- Supported production ABI: `arm64-v8a`
- Keep the release keystore and password. Future updates must use the same signing key.

## Versioning Policy

- Tagged `versionName` uses the `X.Y` release tag; other CI builds use `nightly-<run>.<attempt>`.
- `versionCode` must strictly increase for every hosted update.
- CI uses `versionCode = 10000 + GITHUB_RUN_NUMBER * 100 + GITHUB_RUN_ATTEMPT` for every build type.
- Original release 1.0 used `10000`; every new CI build exceeds it. Reruns reserve attempts 1–99 per run.
- Later tagged builds follow the same sequence so they can update installed nightlies.
- Keep this workflow's run sequence intact. Rerunning an older run does not make it newer than subsequent runs.
- Local defaults are `versionName=1.0`, `versionCode=10000`. Publish through CI to keep every public APK in
  the shared sequence. Manual public builds must coordinate their codes with that sequence.

For a manual public build, edit `android/gradle.properties` or supply these overrides:

```text
OPENYAMM_ANDROID_VERSION_NAME=<display-version> \
OPENYAMM_ANDROID_VERSION_CODE=<reserved-increasing-code> \
android/build_release_apk.sh
```

## Build And Verify

```sh
android/build_release_apk.sh
sha256sum android/app-release.apk
/home/pjasicek/android-sdk/build-tools/35.0.0/apksigner verify --verbose android/app-release.apk
zipinfo -1 android/app-release.apk | rg '^lib/' | sed 's#^lib/##; s#/.*##' | sort -u
```

Expected ABI output:

```text
arm64-v8a
```

## Website Copy

Publish:

- `app-release.apk`
- SHA256 checksum from `sha256sum android/app-release.apk`
- Version name and version code
- Minimum Android version: Android 6.0 or newer
- Note that only 64-bit ARM Android devices are supported

## Install Instructions For Users

1. Download `app-release.apk`.
2. Open it on the Android device.
3. If Android blocks the install, allow installs from the browser or file manager used to open the APK.
4. Install the APK.
5. For updates, install the newer APK over the existing one.

If Android refuses an update, compare the signing certificates and version codes of both APKs.
Android rejects a lower version code; an equal code can be reinstalled when sideloading, but published updates
should use a higher code. A different signing certificate also prevents an in-place update.

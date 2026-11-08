# Releases

Releases are built, checked, signed and published by GitHub Actions
([`.github/workflows/packages.yml`](../.github/workflows/packages.yml)); see
[Incremental updates](UPDATER_PLAN.md) for the design. Nothing is built or uploaded by hand.

| Trigger | Result |
|---|---|
| Push to `main` | Builds every package, packs both content profiles, plays the release scenarios on Linux and Windows. Publishes nothing. |
| Tag `vX.Y` | The same, then publishes release X.Y to `https://jasicek.net/openyamm/` and creates the GitHub release. |
| Actions → Packages → Run workflow with a version | The same, then publishes a test release to `https://jasicek.net/openyamm-staging/`. |

Players download a small package of tens of MB (the game without its content): `OpenYAMM-X.Y-windows-x64.zip`,
`OpenYAMM-X.Y-linux-x64.tar.gz`, `OpenYAMM-X.Y-macos-arm64.dmg` or the APK. The first start downloads the content packs
(about 5 GB on the desktop, 3 GB on Android), and every later release downloads only the packs that changed. On
Windows and Linux everything, including `saves/`, `settings.ini` and `openyamm.log`, stays in the extracted folder.
The macOS app, dragged from the disk image to Applications, installs itself into
`~/Library/Application Support/OpenYAMM` on its first start and keeps the player's data there
([UPDATER_PLAN.md 9.4](UPDATER_PLAN.md)). It is signed ad hoc, not notarized: players run
`xattr -dr com.apple.quarantine /Applications/OpenYAMM.app` once or allow it in System Settings → Privacy & Security.

Players who want to change game files use a `mods` folder or `keep_modified_packs=on`; both are described in
[Changing the game's files](MODDING.md). An edited pack is otherwise restored at the next start.

## What the workflow builds

| Job | Runner | Output |
|---|---|---|
| Content packs (desktop, android) | ubuntu-24.04 | `index.json` and `packs/` per profile (`tools/package_runtime_assets.py`); the Android checkout leaves out the desktop-only BC7 textures |
| Windows x64 | ubuntu-24.04 | MinGW-w64 cross build: launcher, game and shaders (`openyamm_release_package`, thin) |
| Linux x64 | ubuntu-22.04 | GCC 13 with static libstdc++: needs only glibc 2.35 or newer (Ubuntu 22.04, Debian 12, Fedora 36, any current Arch); checked by `packaging/check_linux_binary.sh` |
| macOS arm64 | macos-15 | Apple silicon, macOS 14 or newer: `OpenYAMM.app` (Metal) signed ad hoc, the launcher and the players' disk image; checks the bundle's seal and that only system libraries are linked |
| Android arm64 | ubuntu-24.04 | Thin APK (no assets checked out), signed with a throwaway key |
| Scenarios | ubuntu-24.04, windows-latest, macos-15 | The release scenarios (`tests/scenarios/release/scenarios.txt`) with the built game and the desktop packs |
| Publish | ubuntu-24.04, environment `release` | Only for tags and staging runs; see below |

The publish job (`packaging/publish_release.py`):

1. signs the APK with the release key and refuses it when its certificate differs from the published APK's;
2. `prepare`: reads the published manifests, reuses every pack whose content did not change (same `content_id`,
   package and mount keep the published file), assembles the small packages and app archives, and writes the
   manifests and the release history (`updates/history/`);
3. `sign`: signs the manifests with the slot-1 key;
4. `check`: extracts the small Linux package, lets it download its content from a local copy of this release (packs
   the release reuses come from the server) and plays a scenario through the launcher;
5. `upload`: rsync over SSH, packs and apps first and the manifests last, then removes store files that none of the
   newest three releases references and downloads older than the newest two;
6. `verify`: fetches the public manifests and checks the signatures, HTTP Range and caching;
7. for tags, creates the GitHub release with the small packages, the APK and their checksums.

## One-time setup

1. **Deploy login** (done on 2026-10-21; rerun only to repair it). From this PC, which logs in to the server with
   sudo rights:

   ```sh
   packaging/server/setup_deploy_key.sh
   ```

   It creates `~/openyamm-keys/ci-deploy-ed25519` and the server user `openyamm-deploy` (no password), whose only key
   is `command="/usr/bin/rrsync -wo /var/www/html",restrict`: rsync writes below the web root, with no shell, no
   reading and no forwarding. That user owns only `openyamm/updates`, `openyamm/downloads` and `openyamm-staging`.
   sshd also listens on port 2222 (`/etc/ssh/sshd_config.d/openyamm-public.conf`), where it accepts public keys only
   and only `openyamm-deploy`; ufw opens 2222, and port 22 stays limited to the LAN.
2. **Port forward** (done on 2026-10-21). `jasicek.net:22` is answered by the router itself (dropbear), not by the
   server, so the router forwards the public TCP port 2222 to `192.168.1.128:2222`. `packaging/server/known_hosts`
   pins the server's own host key, so the job refuses to upload anywhere else.
3. **Environment.** GitHub → Settings → Environments → New environment `release`:
   - No required reviewers: a tag or a staging run publishes as soon as its builds and scenarios pass. Tick
     Required reviewers (yourself, "Prevent self-review" unticked) to make every publish wait for an approval.
   - Deployment branches and tags: selected only, tag rule `v*` and branch `main` (staging runs start from `main`).
4. **Environment secrets** of `release` (with the GitHub CLI, from the keys folder):

   ```sh
   gh secret set OPENYAMM_MANIFEST_KEY --env release < ~/openyamm-keys/manifest-ed25519.key
   gh secret set OPENYAMM_DEPLOY_SSH_KEY --env release < ~/openyamm-keys/ci-deploy-ed25519
   base64 -w0 ~/openyamm-keys/android-release.jks | gh secret set OPENYAMM_ANDROID_KEYSTORE_BASE64 --env release
   gh secret set OPENYAMM_ANDROID_KEYSTORE_PASSWORD --env release   # prompts
   gh secret set OPENYAMM_ANDROID_KEY_PASSWORD --env release        # only when it differs from the keystore's
   gh secret set OPENYAMM_ANDROID_KEY_ALIAS --env release           # only when it is not "openyamm"
   ```

   The playthrough statistics' sealing key is a **repository** secret, not a `release` one, because every package
   build compiles it in (cmake/PlaythroughStatisticsKey.cmake). The secret is a private C++ source that holds the key
   and assembles it; neither the key nor the scheme is in the repository. The private generator
   `~/openyamm-keys/make_stats_key_source.py` makes `stats-key.hex` once and a new randomized source on every run:

   ```sh
   python3 ~/openyamm-keys/make_stats_key_source.py
   gh secret set OPENYAMM_STATS_KEY_SOURCE < ~/openyamm-keys/stats-key-source.cpp
   ```

   Local release builds use it with `-DOPENYAMM_STATS_KEY_SOURCE=$HOME/openyamm-keys/stats-key-source.cpp`.
   Regenerating with the same `stats-key.hex` changes only the scheme. A new key needs a new version label
   (`--version release-2`), and records sealed with the old key then no longer open.
5. **Repository variables** (Settings → Secrets and variables → Actions → Variables), only when they differ from the
   defaults: `OPENYAMM_DEPLOY_PORT` (default 2222) and `OPENYAMM_DEPLOY_REMOTE` (default `openyamm-deploy@jasicek.net:`).
6. **Offline copies.** The slot-2 manifest key (`manifest-ed25519-offline.key`) never goes to GitHub: it is the
   rotation key if slot 1 leaks. Keep an encrypted offline copy of the whole `~/openyamm-keys`; losing
   `android-release.jks` means installed APKs can never update.

## Making a release

1. Test it on the staging site: Actions → Packages → Run workflow on `main`, version `X.Y`. Point a test
   installation at it with `[updates] url=https://jasicek.net/openyamm-staging/updates/` in its `settings.ini`, or
   extract the small package from `https://jasicek.net/openyamm-staging/downloads/X.Y/` and set the same line before
   the first start. Running the same version again replaces the staged release. On this PC,
   `python3 packaging/rehearse_release.py --site https://jasicek.net/openyamm-staging install X.Y --platform P` (P:
   `linux`, `windows` under Wine, `android` on the emulator) installs the staged packages as a player would and
   renders a map; `clean` removes the installations afterwards.
2. Publish: create an annotated tag whose message is the release notes (plain text, at most 1500 characters; the
   update question shows them in a scrolling box) and push it. Write one change per line as a `- ` bullet (wrapped
   lines align after the dash); a blank line separates groups, and a line such as `MM7:` can head one. Line breaks
   are kept as written, so never write the notes as one long paragraph. Write the message in a file:

   ```sh
   cat > notes.txt <<'EOF'
   - Faster loading.
   - The new 3D monsters.

   MM7:
   - The Priest of the Moon is hostile.
   EOF
   git tag -a v1.7 -F notes.txt
   git push origin v1.7
   ```

3. When the run is green, `python3 packaging/publish_release.py verify --expect 1.7` checks the release from outside.

A failed publish can be re-run from the run page: nothing is visible to players before the manifests upload, and a
release whose manifests went up can be published again only on the staging site. Versions must increase; a tag that
is not newer than the published release fails in `prepare`.

## Rehearsal

Before a first or unusual release, `packaging/rehearse_release.py` replays the whole cycle on this PC, best in a clean
clone of the pushed state. It builds what the workflow builds, publishes it with the real publisher (signed with
`~/openyamm-keys/manifest-ed25519.key`) to a local copy of the server on 127.0.0.1, installs the small packages as a
player would and updates them to a second release whose content differs in one pack:

```sh
python3 packaging/rehearse_release.py all 1.6 1.7 --manual   # about an hour; then:
python3 packaging/rehearse_release.py clean
```

| Platform | Fresh installation of the first release | Update to the second |
|---|---|---|
| Linux | the content setup window downloads every pack, the game renders New Sorpigal | the main menu offers the update (`--manual`; otherwise `--headless-update`); only the changed pack downloads; the new version plays a scenario through the launcher, marks itself healthy and removes the old version and packs |
| Windows | the same under Wine | the same under Wine |
| Android | the emulator (AVD `openyamm_api35`, an x86_64 APK in place of the arm64 one) downloads the content and renders a map | you choose the update in the game's main menu; the update screen and the system's install question are confirmed automatically |

Each step also runs alone (`build`, `publish`, `install`, `update`; see `--help`), for example to repeat one platform's
update. Everything stays in `build-rehearsal/` (the local site, installations, Wine prefix, screenshots); `clean`
removes it, stops the local site, uninstalls the game from the emulator and stops an emulator the rehearsal started.

## Security

- Push builds and the build jobs of a release hold no signing or deploy secrets. Only the publish job, which runs only
  for `v*` tags and manual runs on `main`, sees those keys. The build jobs hold only `OPENYAMM_STATS_KEY_SOURCE`, whose
  key ships inside every package anyway: it deters casual editing of the statistics and protects nothing else.
- Someone who can push tags or start the workflow can publish (with required reviewers, only after an approval). A
  leaked manifest key lets an attacker sign manifests that clients accept: publish a release whose game trusts only
  slot 2, then make a new slot 1 key. A leaked deploy key can change the release folders, but clients reject any
  content that the manifests do not sign; delete `~/openyamm-keys/ci-deploy-ed25519*`, run `setup_deploy_key.sh` again and update the secret.
- The server holds no keys and runs no publishing code; it can be rebuilt by publishing the next release.

## Local work

- `python3 packaging/test_publish_release.py` checks pack reuse, packages, signatures, upload order and the cleanup
  rules (with a real local rsync).
- `cmake --build <build> --target openyamm_release_package` builds the package of the current platform; with
  `-DOPENYAMM_RELEASE_THIN=ON` it is the small one, with `-DOPENYAMM_RELEASE_CONTENT_DIR=<dir>` it bundles prebuilt
  packs, and otherwise it packs `assets_dev`.
- Linux release binaries need `-DOPENYAMM_STATIC_LIBSTDCXX=ON -DOPENYAMM_RUNTIME_SHADER_PATH=runtime/shaders` and an
  old enough build system (the workflow uses Ubuntu 22.04).

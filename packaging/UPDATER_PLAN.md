# Incremental updates — plan

Status: phases 1a, 1b, 2 and 3 implemented on 2026-10-18 (see "Implementation status" below); the Windows and
Android updaters (phases 4 and 5) exist as well. The server facts in §7.5 were checked on the release server
(`ssh server`) and from its nginx logs on 2026-10-18.

**Revision 2026-10-21 (user decisions; supersedes the text below where they differ):**

- **Releases come from GitHub Actions**, not the release machine: a `vX.Y` tag builds, checks, signs and uploads
  (`.github/workflows/packages.yml`, [Releases](RELEASE.md)). The signing keys and a deploy key restricted to
  rsync writes (`rrsync -wo`) are secrets of the protected `release` environment. This replaces §7.4's release machine,
  master tree and local release checks (`build_release_local.sh`, `release_checks.sh` and `LOCAL_RELEASE.md` are
  removed); the server folder is the published state, read back over HTTPS.
- **The Flatpak is dropped.** Linux gets the same versioned installation and self-updater as Windows (§9.1): a
  `tar.gz` with the launcher `OpenYAMM` and `app/<version>/openyamm`, built on Ubuntu 22.04 with static libstdc++, so
  it needs only glibc 2.35. Its HTTPS transport loads the system's libcurl at runtime.
- **Small download packages.** The Windows zip, the Linux tar.gz and the APK carry no content packs. A desktop
  installation's first start shows a setup window (`game/app/ContentSetup.*`, SDL's own renderer and font, so it needs
  no content) that downloads the packs of its own release, or installs a newer release when one is out. Complete
  packages are no longer built.
- **User data stays in the installation folder on Windows and Linux** (§4.1): `saves/`, `settings.ini`,
  `openyamm.log` and screenshots live next to the game, as up to 1.5. Updates never touch them; the per-user folder,
  `portable.txt` and the one-time import from the installation are removed.
- **Changing game files (2026-10-23):** a `mods/` folder in the user data overrides single files and survives updates;
  `keep_modified_packs=on` keeps edited packs and turns updates off (§11, [Changing the game's files](MODDING.md)).
  Before, the start check restored an edited pack at every start, whatever `check_for_updates` said.
- Manifests may name a store file by an absolute https URL whose last segment is its hash (a mirror); relative store
  paths remain the default.

**Revision 2026-10-23:** macOS (Apple silicon) is a fourth desktop platform, `macos-arm64`, with the same versioned
installation in `~/Library/Application Support/OpenYAMM` (§9.4).

## Implementation status

| Phase | State | Where |
|---|---|---|
| 0 | Server done 2026-10-18 (`snippets/openyamm.conf` included in the `jasicek.net` block, `conf.d/openyamm-limits.conf`, `worker_connections 4096`, folders owned by `pjasicek`; backups in `/etc/nginx/backup-openyamm-20261018/`; Range, caching, 403 listings and the 4-connection limit checked). Keys created 2026-10-18 in `~/openyamm-keys` (manifest slots 1 and 2, Flatpak key `58E5963E5B28E5893031E18FFDC59BD5F2ED20D4`); public halves in `packaging/keys/` and `packaging/flatpak/openyamm.gpg`. Still to do: the encrypted offline backup, then moving the slot-2 key offline | `packaging/server/`, `packaging/publish_release.py init-keys` |
| 1a | Done | `engine/UserDataPaths.*`, `game/app/main.cpp`, Load screen **Import Saves…** / **Open Folder**, Flatpak wrapper |
| 1b | Done | `game/app/GameSettings.*`, `SettingsShippedDefaults.inc` (`tools/settings_default_history.py`), templates deleted |
| 2 | Done; Android pack mounting is untested on a device | `tools/runtime_packs.py`, `tools/packaging/packs.yml`, `engine/AssetPackIndex.*`, `AssetFileSystem` |
| 3 | Replaced on 2026-10-21 by the release workflow; first real publish waits for the one-time setup in `packaging/RELEASE.md` | `.github/workflows/packages.yml`, `packaging/publish_release.py`, `packaging/RELEASE.md` |
| 4–5 | Windows and Android updaters done; Linux added 2026-10-21 (launcher, libcurl transport, first-start content setup) | `engine/update/`, `game/launcher/`, `game/app/GameUpdater.*`, `game/app/ContentSetup.*`, `android/.../OpenYammUpdate*.java` |

Deviations from the text below are marked *As implemented* where they occur.

**End-to-end test (2026-10-18, throwaway keys, a local folder standing in for the server):** a copy of the working
tree built 1.6 with `build_release_local.sh` (Windows cross build, Flatpak, APK). `release_checks.sh` passed on
Windows under Wine (all scenarios, `%APPDATA%` import, rendered New Sorpigal) and on the Flatpak (signed bundle,
update remote, scenarios). On Android the APK mounted its packs in place and started rendering, then stopped on the
untracked ground-item work in progress (`assets_dev/engine/world_items/` exists only in desktop formats), which the
current tree needs but releases leave out. `publish_release.py` published 160 packs (6.4 GiB) with signed manifests
in under 4 minutes. A 1.7 with one changed data table reused 111 of 113 published packs byte for byte, and
`flatpak update` from 1.6 downloaded the changed files only: 118 MiB instead of 5 GB (the binary, `engine.core` and
a ground-item pack the other work changed meanwhile).

Goal: players install OpenYAMM once and afterwards download only what changed, on Windows, Linux and Android. Saves
and settings survive every update without manual copying.

Non-goals: an installer wizard, launcher-store integration, updates for development builds (`assets_dev/` runs),
multiplayer content negotiation, and partial installs (only some worlds) in the first version (the design allows them
later, see §11).

## 1. Current state

| | Windows ZIP | Flatpak | Android APK |
|---|---|---|---|
| Download per release (current nightly) | 4.37 GiB ZIP, always complete | 4.25 GiB `.flatpak` bundle | 2.85 GiB APK |
| Content layout | `assets/engine.zip` + `assets/worlds/mm{6,7,8}.zip` | same zips in `/app/share/openyamm/assets` | the same zips unpacked into APK `assets/`, APK mounted at `/` |
| Saves and settings | `saves/`, `settings.ini` relative to the working directory, which is the extracted release folder | `$XDG_DATA_HOME/openyamm` (the wrapper `cd`s there) | app external storage, the working directory set in `openyamm_android_entry.cpp` |
| Settings defaults | code + `settings.ini` from `settings_release.ini` in the ZIP | code + `settings_release.ini`, copied on first start | code + `android/settings.ini`, extracted when missing |
| Updated by | the player, by hand | `flatpak install` of a new bundle | installing a new APK (same signing key keeps data) |

All complete packages are uploaded to a public Nextcloud folder share on `cloud.jasicek.net` (one nightly, every
tag), and GitHub releases link to them.

Problems:

- **Windows loses saves on update** unless the player moves them. A shortcut with a different "Start in" directory
  even writes saves somewhere else.
- **Every platform re-downloads everything.** `engine.zip` is 1.5 GB; a one-line `data_tables` change ships it again.
  OSTree (Flatpak) deduplicates by file, but the whole zip is one file, so it cannot help.
- **Flatpak releases use a per-version branch** (`flatpak_branch="$version"` in `.github/workflows/nightly.yml`), so
  `flatpak update` can never move a player from 0.7 to 0.8.
- **New settings defaults never reach existing players.** The game writes every key on every start, so a player's
  file cannot tell their choices from old defaults. Defaults also live in three places that disagree (code and two
  templates), shipping `settings.ini` in the Windows ZIP overwrites the player's file when extracted over an old
  folder, and `[assets] root` gets copied into the user's file. Details in §4.3.
- **Each package build packages the same content again** (in CI, the Windows, Flatpak and Android jobs each run
  `tools/package_runtime_assets.py`; `packaging/build_release_local.sh` repeats that per target).
- **Server storage and traffic grow with complete packages.** The Nextcloud share holds ~62 GiB and grows by
  ~11 GiB per tag. Players downloaded ~1.8 TiB in the 14 days before 18 October, including two downloads of the whole
  share as one 66.7 GB zip (§7.5).

Useful facts the design builds on:

- `package()` in `tools/package_runtime_assets.py` already writes deterministic zips: sorted entries, fixed
  1980-01-01 timestamps, fixed permissions, `ZIP_STORED` for `.oyatlas`/`.oytex`/`.ogv`.
- `AssetFileSystem` already mounts several archives with mount points (`/engine`, `/worlds/<id>`) through PhysicsFS,
  with the active world prepended and the others appended (`mountPackagedAssetRoot`).
- Android and the Flatpak already keep user data outside the install; only Windows needs the move.
- yaml-cpp already parses JSON in the engine (`SpriteAtlas.cpp`); no new JSON dependency is needed.

## 2. Principles

1. **User data never lives in the install.** Updating, repairing or deleting an installation cannot touch saves.
2. **Content is split into packs; a pack's identity is its logical content.** Unchanged files produce an unchanged
   pack, so it is never downloaded again.
3. **One layout everywhere.** The complete download and an updated install are byte-for-byte the same layout, and
   every platform mounts content through the same pack index. No "old layout" fallback.
4. **Atomic switch, kept rollback.** Updates download beside the running version and switch with one rename. The
   previous version stays until the new one has started successfully once.
5. **Content-addressed, immutable hosting.** Files are never overwritten on the server; only small manifests change.
6. **Verify everything.** HTTPS, a signed manifest, SHA-256 of every downloaded file.
7. **Use what each platform already does well.** Flatpak updates through OSTree (no custom updater). Windows and
   Android use one shared C++ updater core with OS-native HTTPS (WinHTTP, Android Java networking), so no OpenSSL or
   libcurl ships.
8. **Ask before network access** and never update during gameplay.

## 3. Architecture overview

```
Release machine (developer PC, by hand)        Release server (jasicek.net, plain nginx static, §7.5)
 packaging/build_release_local.sh                /var/www/html/openyamm/  = mirror of the master tree
   content packed once per profile ──┐
   Windows ZIP, APK, Flatpak bundle  │          /openyamm/updates/packs/<sha256>.zip          immutable
 release checks (Wine, emulator) ────┤  rsync   /openyamm/updates/apps/<sha256>.zip|.apk      immutable
 packaging/publish_release.py        ├────────► /openyamm/updates/channels/stable/<platform>.json(.sig)
   master tree in ~/openyamm-release:│  over    /openyamm/flatpak/repo/  (OSTree, signed on the PC)
   signed manifests, OSTree repo,    │  SSH     /openyamm/downloads/     (complete packages, last two releases)
   retention and garbage collection ─┘
 secrets: ~/openyamm-keys/ (never leave the PC)

Client (Windows, Android)
 UpdateChecker → ReleaseManifest (verify signature) → UpdatePlanner (diff vs installed index)
   → UpdateDownloader (resume, SHA-256) → UpdateInstaller (stage, atomic switch) → restart
 Game start: launcher/entry picks the current version → AssetFileSystem mounts packs from index.json

Client (Flatpak)
 flatpak update (GNOME Software / Discover) — OSTree downloads only changed pack files
```

## 4. Part A — user data directory (all platforms)

### 4.1 Layout

| Platform | User data root | How it is resolved |
|---|---|---|
| Windows, Linux | the installation folder (next to `OpenYAMM[.exe]`) | a release installation (`app/current` or `assets/index.json`); revised 2026-10-21, see the top |
| Android | app external storage root | unchanged (`SDL_GetAndroidExternalStoragePath`) |
| Development | repository root | unchanged; `--user-data <dir>` overrides |

Inside the root: `settings.ini`, `saves/`, `output/screenshots/`, logs, and later `mods/`.

### 4.2 Code changes

- New `engine/UserDataPaths.{h,cpp}`: resolved once in `runApplication` (`game/app/main.cpp`) from `--user-data`, a
  `portable.txt` marker (`<install>/userdata`), a release installation (`assets/index.json` next to the executable:
  `SDL_GetPrefPath`, `%APPDATA%\OpenYAMM` on Windows) or the working directory (development runs).
- **As implemented:** the game makes that folder its working directory, as Android and the Flatpak wrapper already
  did, instead of changing each `"saves"` and `"settings.ini"` site. Every relative user-data path (saves,
  `settings.ini`, `output/screenshots`, logs, traces) then lands in it. `--user-data` and `--asset-root` resolve
  against the folder the game was started from; other relative command-line paths resolve against the user data
  folder, so the release checks pass absolute ones. The Flatpak wrapper passes both and no longer copies a settings
  file.
- Resolve the **default asset root from the install location** (`SDL_GetBasePath()`), not from the working
  directory. `ApplicationConfig::createDefault()` currently returns the relative `"assets"`.
- **Settings:** the user file holds only the player's own choices, and defaults come from the code; see §4.3.
- **Save and settings import** (explicit migration, runs once): if the user root has no saves and `saves/*.oysav`
  exist next to the executable or the launcher, copy them (never move), then write `saves/.imported-from`. Likewise,
  if the user root has no `settings.ini` and one exists there, copy it; the conversion step (§4.3, item 6) then
  reduces it to the player's choices. The Load menu also gets **Import saves…** (`SDL_ShowOpenFolderDialog`) for
  players who extract the new version into a new folder, and **Open data folder**. *Implemented as* **Import
  Saves…** and **Open Folder** in the Load screen's footer (desktop only); the import never overwrites a save.
- Saves keep their existing version handling: older saves migrate on load; a save written by a newer build is refused
  with a clear message instead of being loaded partially. *Implemented:* the Load screen says how many saves need a
  newer version instead of hiding them silently.
- An update that ships a rebuilt map does not break saves made before it: each saved map state records its map's
  layout identity, and a map whose layout changed starts afresh when the party enters it, keeping the party's own
  state ([saved map states](../devdocs/SAVED_MAP_STATE_IDENTITY.md), save version 160).

### 4.3 Settings and new defaults

**Today** (`game/app/GameSettings.cpp`, `GameApplication::loadOrCreateSettings`):

- Defaults come from three places that disagree: the code (`GameSettings.h` initialisers plus `createDefault()`),
  `settings_release.ini` (desktop and Flatpak) and `android/settings.ini` (APK). For example, `sound_volume` is 9 in
  the code, 3 in the desktop template and 2 on Android. `ambient_occlusion` is off in the code and on in the desktop
  template. Several code defaults are developer values (`immortal=true`, `preseed_party=true`), which the templates
  override.
- The game writes **every** key on every start. Afterwards a player's file cannot distinguish "the player chose
  this" from "this was the default when the file was written", so **a new default never reaches existing players**.
  It only does through a hand-written profile migration (`migrateLegacyAndroidSettings` v1–4,
  `migrateLegacyDesktopSettings` v1), which also has to know the old value.
- The file is written in place (`std::ofstream`). If writing is interrupted, the file is truncated. Unreadable
  values are then replaced by defaults, and the next save makes that permanent.

**Design: three layers, with only the player's choices stored**

| Layer | Source | Persisted |
|---|---|---|
| 1. Defaults | `GameSettings::createDefault()` in code, per platform: the single source of defaults | no |
| 2. Launch overrides | command line (`--set key=value`, the Flatpak's asset root), debug and session-only overrides | no |
| 3. Player choices | the user's `settings.ini`: only keys the player set | yes |

Effective settings = defaults, overlaid with the player's file, then migrated, then overlaid with launch overrides.

1. **One source of defaults.** Move every value from `settings_release.ini` and `android/settings.ini` into
   `createDefault()`. Where the code and a template disagree, take the template value, because that is what
   players actually got. Developer values (`immortal`, `preseed_party`, traces, start map) stop being defaults;
   developers keep them in their own `settings.ini`. Check each developer-flavoured key that neither template sets:
   `debug_console`, for example, is in neither, so players currently get the code default `true`.
   Then delete both templates and the steps that install them:
   `CreateOpenYammReleaseSettings.cmake`, the Flatpak manifest line, the copy in `android/app/build.gradle`, and the
   first-run copy in `openyamm-flatpak`. A fresh install starts with no file and gets pure defaults.
   *As implemented:* the templates set every key except `[rendering] item_models`, so players keep exactly the values
   they got (desktop console off, Android console on). One deviation: the desktop template's
   `override_start_position=true` (a debug teleport to 0,0,0) became `false`. The high graphics preset now turns
   ambient occlusion on, as the desktop defaults do, so Settings shows them as "High" (decided 2026-10-18).
2. **Preferences and remembered state are different keys.** Some keys are state the game remembers, not choices
   with a default: `loadOrCreateSettings` writes `startWorldId` from the launch configuration on every start
   (`m_settings.startWorldId = normalizeWorldId(m_config.activeWorldId)`), and display values may be detected rather
   than chosen. Classify every key once, in the serialiser's key table: **state** keys are always written and never
   compared with defaults; only **preference** keys follow the sparse rule below. Values the game detects at run
   time (a display mode, for example) are applied like launch overrides (item 4) and stored only when the player
   changes them in Settings; otherwise the "changed in this session" rule below would pin them.
3. **A sparse user file.** Saving writes the `[profile]` header, the state keys, plus each preference key that:
   - was already in the file (an earlier choice stays a choice, even when it equals today's default), or
   - differs from its value when the file was loaded (the player changed it in this session), or
   - differs from the default.

   *As implemented:* a key is written when it was in the file or differs from its default; key bindings compare
   against the defaults of the player's control preset. A value set back to its default in a session is not written
   unless it was in the file, which loads the same value. Instead of a new per-setting Reset, the existing **Restore
   Defaults** of each Settings section releases that section's keys.

   Then **a changed default automatically reaches every player who never touched that setting**, and every player
   who did keeps their value. The settings UI needs no change to support this; it keeps editing `GameSettings`
   fields. Only a new **Reset to default** action (per setting and per page) removes keys from the file.
   Implementation: `saveGameSettings` first serialises to an ordered key/value list (the existing writer, without
   streaming), compares it with the serialised defaults and the loaded values, then writes the selected keys in the
   existing section order.
4. **Session-only values are never saved.** Launch overrides and debug forcing are applied to the effective
   settings after loading, never to the stored layer. For example, the `loadUniqueActorIndex` path in
   `loadOrCreateSettings` forces pathfinding settings, and today that happens after the save only because of
   statement order.
5. **Versioned migrations stay, for changes of meaning only**: renamed or moved keys, changed units or ranges,
   removed options, and deliberate resets for everyone (like the earlier `actor_models=true`). One ordered list
   `{version, platforms, step}` runs on the stored key/value layer before parsing, which makes renaming a key a
   one-line step. Desktop and Android continue from their current numbers (desktop 1, Android 4) in one shared
   sequence, so a step can target one platform or both. Every step gets a unit test. A plain default change needs
   no migration at all.
6. **Converting existing full files: one explicit migration** (the first step of the new sequence, profile
   version 5). Every key is in
   today's files, so they would all look like choices. The step removes each key whose value equals a default that
   a release shipped for that platform: the current default or an earlier one. A small generated table of earlier
   shipped values (`tools/settings_default_history.py` reads `settings_release.ini` and `android/settings.ini` at
   tags 1.0–1.5 and the code defaults of those tags, then writes `game/app/SettingsShippedDefaults.inc`) supplies
   the earlier ones. Keys with any other value stay as choices. Limitation: a player who deliberately picked a value
   equal to an old default gets the new default once. That is acceptable, and the release notes can say so.
   *As implemented:* the conversion runs on the key/value layer when a file with a profile version below 5 is loaded,
   before parsing, so a dropped key takes today's default. It also drops keys our releases wrote that this version no
   longer reads (retired keys) and the asset roots release packages wrote. The history covers the templates of tags
   1.0–1.5 and of the last commit that had them; code defaults of keys a template lacked were checked by hand and are
   unchanged except `actor_models`, which an earlier migration already forces. The writer always writes the current
   profile, so a file written by this version is never converted.
7. **Robust writes**: write `settings.ini.tmp`, then rename it over `settings.ini`, keeping the previous file as
   `settings.ini.bak`. A value that fails to parse is logged and ignored for this run, but its line is kept in the
   file, so a parse bug cannot erase choices. *As implemented:* writes go through `.tmp` and keep `.bak`; a file that
   fails to load is not saved over at all. Keeping a single unparsable line is not implemented: such a key is
   written back with its default.
8. **Forward compatibility and rollback**: unknown sections and keys (from a newer version or a mod) are kept
   verbatim on save. A file whose version is newer than the binary is loaded without migrations and saved without
   lowering its version. An updater rollback (§8.2) therefore does not lose settings.
9. **No install paths in the user file.** `[assets] root` remains a developer override; release builds resolve
   assets from the install (§4.2), and the Flatpak wrapper passes its asset root on the command line.
10. **Optional:** when a release changes a default that the player has overridden, Settings can mark it
   ("New default: on") with a one-click reset, instead of changing it silently.

**Tests (doctest):** saving defaults produces only the header and the state keys; load(save(s)) round-trips; a changed
default reaches a file without the key and does not affect a file with it; Reset removes the key; unknown keys survive;
a newer version is left alone; each migration step; the conversion step turns the shipped 1.0–1.5 templates (stored as
test fixtures) into files with only the header and state keys, and keeps a template with a few changed values as
exactly those values; an interrupted write leaves the previous file usable.

The developer's tracked `settings.ini` at the repository root is an ordinary user file under this design. After the
conversion it shrinks to the values that differ from defaults, which also makes it easier to read.

This part ships on its own and already fixes the Windows save problem.

## 5. Part B — splitting the zips into packs

### 5.1 Pack rules

A pack is a deterministic zip that belongs to one **package** (`engine`, `mm6`, `mm7`, `mm8`, later `mm9` or mods)
and one **domain** (top-level directory inside the package).

1. **Small, often-changed domains share one `core` pack per package.** The domains listed under `core` in
   `packs.yml`, plus the root files (`world.yml`, `icon_packages.txt`, licenses, the texture-profile marker), go into
   `<package>.core`: today `data_tables`, `events`, `scripts`, `behaviors`, `ui`, `fonts`, `effects`, `rendering`,
   `hud_x2`, `terrain_decorations`, `liquids`, `branding`. They change in almost every release and cost only a few MB
   together. Membership is listed, not computed from size, for the same reason as rule 5: a domain growing past a
   size threshold would otherwise move out of core and reshuffle. The packager fails on a domain that is listed
   nowhere, and warns when the core pack passes `core_max_mib` (16 MiB) so a domain can be moved out deliberately.
2. **Each large domain gets its own packs**, split into a fixed number of **hash buckets**:
   `bucket = fnv1a64(groupKey) % buckets`. Hash buckets are stable: adding, removing or changing one file changes
   exactly one pack. Sorted ranges would shift every later pack. A domain may **split** files by extension into a
   bucket set of their own, mounted at the same folder: each world's light bakes (`.lighting`, ~210 MiB) are
   `mmX.maps.lighting.N`, so a scene or map edit (~70 MiB of maps in total) does not re-download bakes.
3. **The group key keeps files that change together in one bucket.**
   - `stem` (default): the path up to the first dot of the file name, so `oute3.odm`, `oute3.lighting`,
     `oute3.bake.json`, `oute3.scene.yml` and `oute3.scene.1.yml` stay together. Removing only the last extension
     would split `oute3.bake` and `oute3.scene.1` from the map.
   - `first_dir`: the first subdirectory, for per-family directories (`sprites_new/<family>/…`).
   - `model`: keeps a GLB and its textures together. Model textures are not named after the model:
     `cook_models.py` writes them as `models/textures/<32-hex key>.oytex`, keyed by content, and models may share
     one. The packager therefore reads each GLB's image URIs, and a texture takes the group of the first model
     (sorted by path) that references it; a texture no GLB references groups by its own key. A changed texture gets
     a new key, so it lands with its model instead of in an unrelated bucket.
4. **Target 64 MiB per pack, hard maximum 128 MiB.** The packager fails when a bucket passes the maximum and
   suggests a new bucket count. Changing a domain's bucket count reshuffles that domain once; that is acceptable.
5. **Bucket counts are committed, not computed**, because a computed count would reshuffle every time a domain grows
   past a boundary. They can differ by profile (desktop `textures_x4` is larger than Android `textures_x2`).
6. **Every file lands in exactly one pack.** The packager checks this, and so do the tests.
7. **Entries are relative to the domain**, and the pack is mounted at `<package mount>/<domain>`
   (for example, `engine.icons_x2.3.zip` holds `obsidian_frame.oytex` and mounts at `/engine/icons_x2`). PhysicsFS
   then rejects a lookup by comparing mount-point prefixes, before searching the archive, so 80 mounts cost about
   the same as 4. Core packs mount at the package root.

### 5.2 Configuration (`tools/packaging/packs.yml`)

The committed file lists each package's core domains, every other domain with its bucket count and group rule, the
lighting split, and per-world overrides (MM7 and MM8 have fewer textures than MM6). Measured with the 18 October
content (`tools/package_runtime_assets.py --report`):

- desktop: **110 packs, 4.45 GiB**; every pack under 72 MiB, cores 9–13 MiB;
- Android: the same layout with the ASTC texture tiers; 31 packs (0.92 GiB: audio, maps, light bakes, music, videos,
  world cores) are byte-identical between the profiles;
- a typical small release (tables, one map edit, a few icons) changes `engine.core`, one `mmX.maps.N` and one
  `engine.icons_x2.N`: roughly 70 MB plus the app, instead of 4.4 GB.

### 5.3 Pack identity

- **`content_id`** = SHA-256 over the pack format version and the sorted list of
  `(entry name, size, sha256(entry bytes))`. This is the logical identity, independent of deflate output.
- **`sha256`** = hash of the zip file bytes, used only to verify a download.
- File name: `<pack id>-<first 16 hex of content_id>.zip`, for example `engine.icons_x2.3-1a2b3c4d5e6f7a8b.zip`.
  It stays readable for players and unique in a shared store.
- The client compares packs by `content_id`. A runner whose zlib produces different bytes for the same content does
  not cause a re-download.
- **The published bytes of an unchanged pack are reused everywhere, not only on the server.** OSTree (Flatpak) and
  the complete packages compare files by bytes. If the Flatpak bundle used freshly packed zips, a different zlib on
  the release machine would make every Flatpak player download that pack again. So the release build (§7.4) takes
  the already published file from the master tree for every unchanged `content_id` and feeds those bytes to all
  outputs: the update store, the Windows ZIP, the Flatpak bundle and the APK.

### 5.4 Determinism gates

- Packaging the same `assets_dev` twice gives identical packs (already true; keep it tested).
- Every cooker run on unchanged sources gives identical output (`cook_models.py`, `cook_surface_textures.py`,
  `cook_effect_textures.py`, `cook_sky_textures.py`, `cook_ui_textures.py`, the sprite atlas cooker). A
  non-deterministic encoder would make every release re-download that domain. Add a "cook twice, compare" check per
  cooker. *Status:* releases package the committed cooked files and never re-cook, and the cookers keep receipts
  that skip unchanged outputs (`cook_models.py` re-encodes only when an output is missing or its hash differs), so a
  re-cook of unchanged sources rewrites nothing. The per-cooker checks are not added; add one if a domain starts
  changing without source changes.
- `ZIP_STORED` also for formats that are already compressed (`.ogg`, `.mp3`, `.png`, `.glb` with compressed
  buffers), to save CPU at load time with no size cost.

### 5.5 Packager changes (`tools/package_runtime_assets.py`)

- Keep `package()`'s entry selection and filters (`world_items`, `_legacy`, profile overlays, surface selection,
  lighting dependencies). Only the output step changes: instead of one zip per package, route each entry to its pack
  by the rules above.
- New output: `<out>/packs/*.zip` and `<out>/index.json` (§6.1). The old `engine.zip` + `worlds/*.zip` output is
  removed once all platforms consume packs; no layout fallback is kept.
- `--report` prints domain sizes, bucket sizes and pack counts; it fails on the size limits or on overlaps.
- Android's check for the ETC2/EAC profile (`android/app/build.gradle`) reads `index.json`'s `profile` instead of
  opening `engine.zip`.
- Extend `tools/test_package_runtime_assets.py`: determinism, exactly-one-pack membership, bucket stability (adding a
  file changes exactly one pack), `content_id` independence from compression bytes, size limits.

## 6. Part C — pack index and engine mounting

### 6.1 Installed index (`index.json`, written by the packager and the updater)

```json
{
  "schema": 1,
  "release": "0.8",
  "build": "0.8",
  "profile": "desktop",
  "content_format": 7,
  "store": "../../assets/packs",
  "packs": [
    {"id": "engine.core", "package": "engine", "mount": "/engine",
     "file": "engine.core-3f9a1c2b4d5e6f70.zip", "size": 5123456,
     "content_id": "3f9a…", "sha256": "77ab…"},
    {"id": "mm6.maps.2", "package": "mm6", "mount": "/worlds/mm6/maps",
     "file": "mm6.maps.2-90cd…zip", "size": 61234567, "content_id": "90cd…", "sha256": "e1f2…"}
  ]
}
```

`store` is relative to the index file, so the same index works in the Windows layout, the Flatpak and Android.

### 6.2 `AssetFileSystem`

- New `engine/AssetPackIndex.{h,cpp}`: parses and validates the index with yaml-cpp (schema, unique ids, mount points
  under `/engine` or `/worlds/<id>`, files present, sizes match). It does not hash at startup; hashing 6 GB on
  every launch is too slow. Hashing happens on download and in **Verify game files**.
- `mountPackagedAssetRoot` reads the index instead of probing `engine.zip` and `worlds/*.zip`. Precedence stays the
  same as now, per package: active-world packs prepended, other worlds and the engine appended. Packs within one
  package never overlap, so their order does not matter.
- `switchActiveWorld` keeps working: it re-mounts from the same parsed index.
- Android: content mounts from the store in app storage through the same path. The APK mount
  (`mountAndroidApkAssetRoot`) and `expandAndroidApkAssetCandidates` remain only for the APK's own files (shaders,
  bootstrap pack, §9.3).
- `LookupCache` needs no change in concept, but **measure**: launch-to-New-Sorpigal time, map transition times and
  `enumerate()` of the large merged directories, with ~90 packs against the current 4 zips, on desktop and Android
  release. AGENTS.md forbids startup and loading regressions; mounting at domain mount points (§5.1, rule 7) is the
  main mitigation, and the target size can rise to 128 MiB if needed. On Android this phase still reads packs from
  inside the APK; Phase 5 moves them to app storage, a different read path, and repeats the measurements there.
- *Measured on desktop (18 October, same binary, headless full map loads, median of 5):* 110 packs load
  **0.7–1.5 s faster per map** than the same content as 4 whole-package packs at the old mount points
  (New Sorpigal 2.7 s vs 3.6 s, 6d01 2.3 s vs 3.0 s, MM7 out01 6.0 s vs 7.5 s, MM8 out01 6.3 s vs 7.3 s); smaller
  central directories per archive more than pay for the extra mounts. Unqualified lookups try each package root once
  (packs record their package root), not each of the 110 mounts.

## 7. Part D — release manifest, signing and hosting

### 7.1 Manifest (`channels/<channel>/<platform>.json`)

One manifest per platform (`windows-x64`, `android-arm64`) on the single channel `stable`; there are no nightlies.
The `channel` field and the `channels/<channel>/` path stay so that a beta channel can be added later without a new
schema. The Flatpak uses OSTree and needs no manifest.

```json
{
  "schema": 1,
  "channel": "stable",
  "platform": "windows-x64",
  "release": "0.8",
  "build": "0.8",
  "published": "2026-11-02T10:00:00Z",
  "content_format": 7,
  "min_updater_schema": 1,
  "notes_url": "https://…/releases/0.8",
  "app": {"file": "app-windows-x64-0.8.zip", "url": "apps/<sha256>.zip", "size": 48000000, "sha256": "…",
          "android_version_code": null},
  "packs": [ {"id": "engine.core", "package": "engine", "mount": "/engine", "file": "…", "url": "packs/<sha256>.zip",
              "size": 5123456, "content_id": "…", "sha256": "…"} ]
}
```

- `url` is relative to the channel's base URL, so the host can move without changing manifests.
- A manifest lists the languages' optional packs (`"language": "<id>"`, devdocs/LOCALIZATION.md) apart, under
  `language_packs`, with the same fields, and so does the release's `index.json` in the packages and app archives.
  Updaters before 2.0 read only `packs` and know no language field, so an update from them downloads none of them,
  and their check of the new version's index (every listed pack present) passes. 2.0 and later read both lists:
  desktop fetches a language's packs only for the languages kept installed, Android fetches them all (fonts only) and
  offers the installed release's missing packs as an update.
- `content_format` is an integer bumped whenever a binary needs new content or content needs a new binary
  (a file format version, a new required table). The app and packs of one manifest always match. The client always
  installs a manifest as a whole; `content_format` is a safety check that refuses a mismatched combination.
- `min_updater_schema` lets a future manifest tell an old client "download the full package once".
- **No downgrades through replay.** A signature does not stop a mirror or proxy from serving an older, validly
  signed manifest. The client refuses a manifest whose `published` time is older than that of the installed build.
  The release script likewise refuses to publish a build that is not newer than the published one.

### 7.2 Signing

- Ed25519 signature over the manifest bytes: `<platform>.json.sig`. Verify with Monocypher (BSD-2/CC0,
  GPL-compatible), fetched with `FetchContent` and a pinned `URL_HASH` as the other dependencies are.
- The public key is compiled into the game; two key slots allow rotation. The private key lives only on the release
  machine, in `~/openyamm-keys/manifest-ed25519.key`; the second slot's private key is kept offline (§7.4).
- HTTPS is still required; the signature protects against a compromised mirror or account.

### 7.3 Hosting layout

Under `https://jasicek.net/openyamm/` (files in `/var/www/html/openyamm/`):

```
updates/
  channels/stable/windows-x64.json   (+ .sig)
  channels/stable/android-arm64.json (+ .sig)
  packs/<sha256>.zip                 immutable, cache forever
  apps/<sha256>.zip | .apk           immutable
flatpak/
  repo/                              OSTree repository (§9.2)
  openyamm.flatpakrepo, openyamm.flatpakref, openyamm.gpg
downloads/
  <version>/OpenYAMM-<version>-windows-x64.zip, …-android-arm64.apk, …-x86_64.flatpak (+ .sha256)
1.0/index.html                       existing release page
```

- Manifests: short cache lifetime (`Cache-Control: max-age=300`). Packs and apps: `immutable`.
- **Host: the existing nginx static site on the release server** (§7.5). It already serves `/var/www/html` with
  HTTP Range (checked: `206 Partial Content`) and plain paths, which both resume and the OSTree repository need.
  Player-facing download links point here too.
- **Rejected hosts:**
  - *Nextcloud* runs on the same machine and home upstream, so it saves no bandwidth. Its share URLs
    (`/s/<token>/download?path=…&files=…`) support Range for single files, but cannot serve an OSTree tree, and a
    folder share always offers the whole folder as one zip. The existing share stays only so that links already
    posted keep working, with the same retention, until it is retired.
  - *Google Drive* addresses files by ID, not path, so it cannot hold the pack store, the manifests or the OSTree
    repository. Files over ~100 MB get a virus-scan interstitial, popular files hit "Download quota exceeded" on
    exactly the days that matter, the bundled game content risks a takedown that can lock the whole Google account,
    and ~62 GiB exceeds the free 15 GB.
- **Retention:**
  - packs and apps: everything referenced by any release (cheap, since packs are shared), so in-flight downloads
    and rollbacks keep working; a garbage-collection step deletes unreferenced hashes;
  - complete downloads: the last two releases. The updater upgrades from any older version, so old complete
    packages are not needed.
- The complete downloads (Windows ZIP, `.flatpak` bundle, APK) remain for first installs and are built from the
  same packs.

### 7.4 Releasing from the release machine

*Superseded on 2026-10-21:* releases are built, signed and uploaded by the release workflow; see
[Releases](RELEASE.md). The text below records the original release-machine design.

Releases are made by hand, only from the developer's PC. There are no nightlies, and GitHub Actions holds no
signing keys and publishes nothing.

**Secrets** stay in `~/openyamm-keys/` (`chmod 700`, files `600`; `$OPENYAMM_KEYS_DIR` overrides), outside every
clone, and never leave the PC:

```
~/openyamm-keys/
  android-release.jks       existing APK signing key (losing it means installed APKs can never update)
  release.env               keystore password and alias (packaging/LOCAL_RELEASE.md)
  manifest-ed25519.key      manifest signing key, slot 1 (new)
  flatpak-gnupg/            GnuPG home holding the OSTree signing key (new)
```

The slot-2 manifest key and an encrypted copy of the whole folder are kept offline (for example on a USB stick).
SSH uploads use the developer's normal login to `server`; no upload user or key exists for automation.

**Master tree.** `~/openyamm-release/` (outside the clone, ~40 GiB) is the authoritative copy of everything
published: `www/openyamm/{updates,flatpak,downloads}` exactly as served, plus the OSTree repository. The server is a
mirror of it, so it can be rebuilt from the PC at any time, and the PC always has the published bytes of every pack
for reuse (§5.3) without downloading them.

**Steps:**

1. `packaging/build_release_local.sh --version=X.Y` (existing script) runs the packager once per profile (`desktop`,
   `android`), replaces every pack with an unchanged `content_id` by the published file from the master tree, and
   builds the Windows ZIP, the APK and the Flatpak bundle from those packs.
2. **Release checks** (§12) run against exactly these packages. Publishing refuses to start unless they passed for
   this build.
3. `packaging/publish_release.py --version=X.Y` (new) updates the master tree: refuses a version that is not newer
   than the published one, adds the new packs and apps under their hashes, writes and signs the manifests, imports
   the Flatpak bundle into the local OSTree repository and runs `flatpak build-update-repo` with the GPG key from
   `flatpak-gnupg/`, copies the complete packages to `downloads/X.Y/`, and computes retention and garbage
   collection. `--dry-run` prints every upload and deletion without changing anything.
4. It then uploads with `rsync` over SSH in an order in which no published file ever references a missing one:
   packs and apps; complete downloads; the OSTree repository's `objects/` and `deltas/`, then its `refs/`,
   `summary` and `config`; the manifests last. A final `rsync --delete` pass removes what retention and garbage
   collection dropped.
5. Optionally `gh release create vX.Y` with release notes linking to `https://jasicek.net/openyamm/downloads/X.Y/…`;
   once the APK is thin (§9.3) it can be attached there for Obtainium users.

**GitHub cleanup:** remove the nightly workflow's schedule and publish job, `packaging/upload_nextcloud.py`, and the
secrets `OPENYAMM_ANDROID_KEYSTORE_BASE64`, `OPENYAMM_ANDROID_KEYSTORE_PASSWORD`, `OPENYAMM_NEXTCLOUD_USERNAME` and
`OPENYAMM_NEXTCLOUD_APP_PASSWORD`. Otherwise anyone who can change a workflow can still sign and publish. The
workflow keeps building and testing on push, without secrets (an unsigned or debug-signed APK).

### 7.5 Server: `jasicek.net` (checked 2026-10-18)

The machine behind `cloud.jasicek.net` and `jasicek.net` (public 95.82.160.34; LAN `server`, 192.168.1.128):
Ubuntu 22.04, 8 cores, 31 GiB RAM (about 9 GiB available, swap full, during the check), 1 Gbit/s NIC.
nginx 1.18 terminates TLS (Let's Encrypt) for every subdomain and proxies Nextcloud (127.0.0.1:30001, Docker), along
with several other services. `jasicek.net` serves `/var/www/html` statically; `/var/www/html/openyamm/1.0/` already
holds a release page. SSH (22) is reachable on the public address. `flatpak` 1.12.7 is installed, but with the
OSTree repository built on the release machine (§7.4) the server needs no Flatpak tools. The login user is in `sudo` and
`adm` (so nginx logs are readable) but not `docker`.

**Disk**

| Filesystem | Size | Free | Use |
|---|---:|---:|---|
| `/` (NVMe, LUKS) — nginx root | 914 GiB | 120 GiB | 87 % used |
| `/mnt/hdd` (HDD) | 1.8 TiB | 781 GiB | 56 % used |

Nextcloud's data volume could not be located without root (Docker); check which disk it uses before moving data.

**Current OpenYAMM storage in the Nextcloud share: about 62 GiB** — one old nightly (8.6 GiB) and tags 1.0–1.5 at
9.7–11.6 GiB each (APK + Windows ZIP + Flatpak). At six tags in two weeks, that grows by about 11 GiB per tag.

**Estimated storage with packs**

| Item | Estimate |
|---|---:|
| Pack store baseline: desktop set (~4.3 GiB) + Android set (~2.8 GiB), minus packs shared by both profiles (audio, music, videos, maps, tables) | ~6 GiB |
| Each release (changed packs only; more after a whole-domain re-cook) | 1–3 GiB |
| OSTree repository, `stable`, `--prune-depth=3`, static deltas if they pay off (§9.2; deltas repeat the changed bytes) | 10–20 GiB |
| Complete downloads, last two releases | ~20 GiB |
| **Total in the first months** (store, repository, downloads) | **~35–50 GiB**, growing ~2 GiB per release |

The same amount sits in the master tree on the release machine. For comparison, keeping complete packages of 20
releases would take ~220 GiB. Recommendations:

- Keep the update store and repository on `/` (NVMe) for many concurrent readers; 35–50 GiB fits.
- Keep only the last two releases' complete downloads. The updater upgrades from any older version without needing
  old complete packages. Applying the same rule to the Nextcloud share frees ~40 GiB now.
- If `/` gets tight, move the complete downloads (not the pack store) to `/mnt/hdd`.

**Traffic (nginx logs, 4–18 October 2026)**

- About **1.8 TiB** of OpenYAMM downloads in 14 days; 562 GiB on 17 October alone. The busiest hour (17 October,
  18:00) logged 142 GiB, roughly 340 Mbit/s on average (approximate: nginx logs bytes when a request finishes).
- Requests per file are close to unique addresses (for example, 1.5 Windows ZIP: 74 complete transfers from 73
  addresses), so most traffic is new players, not retries. Only ~10 % (188 GiB) could be attributed to the same
  address fetching a second version. That figure is a lower bound, since home addresses change. Updates help
  returning players most; first installs stay full size.
- **Folder downloads:** two requests fetched the *entire* share as one 66.7 GB zip, and others fetched whole release
  folders (10.5 GB). A Nextcloud folder share always offers that. Serving the public downloads from nginx static
  paths (no directory listing, no folder zips) removes it.
- The home upstream bandwidth is the real limit, not disk. Once traffic grows, consider a CDN or object storage
  with free egress in front of `packs/` and the complete downloads; the content-addressed layout caches perfectly.

**Setup**

1. Directories: `/var/www/html/openyamm/updates/{channels,packs,apps}`, `/var/www/html/openyamm/flatpak/repo`,
   `/var/www/html/openyamm/downloads/`, owned by the developer's login user so that `rsync` needs no `sudo`.
2. nginx, inside the `jasicek.net` server block:

   ```nginx
   location /openyamm/updates/channels/ { add_header Cache-Control "public, max-age=300"; }
   location /openyamm/updates/packs/    { add_header Cache-Control "public, max-age=31536000, immutable";
                                          limit_conn openyamm_per_ip 4; }
   location /openyamm/updates/apps/     { add_header Cache-Control "public, max-age=31536000, immutable";
                                          limit_conn openyamm_per_ip 4; }
   location /openyamm/flatpak/          { add_header Cache-Control "public, max-age=300"; }
   location /openyamm/downloads/        { limit_conn openyamm_per_ip 4; }
   ```

   plus `limit_conn_zone $binary_remote_addr zone=openyamm_per_ip:10m;` in `http {}`, and
   `worker_connections 768` raised to 4096. The per-address limit stops download accelerators that open many
   parallel connections.
3. Nothing else runs on the server for OpenYAMM: no publish script, upload user or signing key. A compromised server
   can serve wrong files, but cannot produce a manifest or Flatpak commit that clients accept.
4. Nextcloud: keep the existing share's public link working for links already posted, apply the same retention to
   it, and retire it once those links no longer matter.
5. The nginx snippet lives in the repository (`packaging/server/nginx-openyamm.conf` with a short README), so the
   server can be rebuilt from it and the master tree.

## 8. Part E — updater core (shared C++, Windows and Android)

### 8.1 Modules (`engine/update/`, compiled when `OPENYAMM_ENABLE_UPDATER` is on: Windows and Android release builds)

| Module | Responsibility | Notes |
|---|---|---|
| `ReleaseManifest` | parse and validate the manifest | pure, unit-tested |
| `ManifestSignature` | Ed25519 check | Monocypher; test vectors |
| `Sha256` | streaming hash | small own implementation with test vectors |
| `UpdatePlanner` | installed index + manifest → plan: packs to download, packs reused, app to download, files to delete later, total bytes | pure, unit-tested |
| `HttpTransport` | interface: `get(url, offset, sink, cancel, progress)` | `WinHttpTransport` (Windows); `AndroidDownloadTransport` (JNI to `DownloadManager`, §9.3) |
| `UpdateDownloader` | worker thread; `.part` files resumed with Range; SHA-256 while writing; rename into the store; retries with backoff; at most 3 parallel transfers | lowest I/O priority while the game runs |
| `UpdateInstaller` | stage the app and index, then the atomic switch, the health check and cleanup | per platform (§9) |

### 8.2 Flow

1. **Check** (main menu only; on start at most every 6 hours, or **Check for updates** in Settings): fetch the
   manifest, verify the signature, compare `build`. Nothing is downloaded yet.
2. **Plan**: show size, release notes and free disk space. Require free space for the download plus a 10 % margin
   before starting.
3. **Download** into `update/` beside the store. Packs that are already present (same `content_id`) are skipped.
   Downloading may continue during play at low priority; applying never happens during play.
4. **Stage**: once everything is verified, write the new index (and on Windows the new app directory).
5. **Switch** atomically (§9), then restart.
6. **Health check**: the new version marks itself healthy after reaching the main menu. Until then the previous
   version and its packs stay. Two failed starts in a row roll back automatically.
7. **Clean up** after a healthy start: delete packs that no index references and the old app directory.

Failure handling: a hash mismatch deletes that file and retries it once, then stops with an error. A bad signature
or an unknown schema stops the update without retrying. Interrupted downloads resume next time. No failure leaves
the current version unusable, because nothing is replaced before the switch.

### 8.3 Settings (`[updates]`)

- `check = ask | auto | off`. Default `ask`: the first start asks once whether the game may check for updates.
- `wifi_only = true` (Android).

### 8.4 Verify game files

A Settings action hashes every pack against the index and re-downloads damaged packs. It is also the support answer
to "the game crashes on start after my disk filled up".

## 9. Part F — platforms

### 9.1 Windows and Linux: launcher plus versioned app directories

*Since 2026-10-21* Linux uses the same layout with `OpenYAMM`, `openyamm` and `OpenYAMM-launcher` without `.exe`:
`game/launcher/UnixLauncher.cpp` replaces itself with the game (`execv`), staged executables get their permission
bits back after extraction, and `HttpTransport` loads `libcurl.so.4` (or Debian's `libcurl-gnutls.so.4`) at runtime.
The player-facing packages are small: no `assets/packs/`, only `app/<version>/index.json`. When that index names
missing packs, `ContentSetup` downloads them through `AppUpdater`'s content-only mode (same release, no app archive,
nothing switches), or installs a newer published release instead. User data lives in the installation folder; the
`%APPDATA%` folder, `portable.txt` and the import below no longer exist.

```
OpenYAMM\
  OpenYAMM.exe                 launcher: tiny, Win32 only, no DLLs
  portable.txt                 optional
  app\current                  text: "0.8"
  app\previous                 text: "0.7"
  app\0.8\openyamm.exe, *.dll, runtime\shaders\…, index.json
  app\0.7\…                    kept until 0.8 is healthy
  assets\packs\*.zip           shared content store
  update\                      downloads in progress
```

- The **launcher** reads `app\current`, starts `app\<v>\openyamm.exe` with the same arguments and exits at once;
  it never waits for the game. The health check needs no communication between the two: before starting a version
  that is not yet healthy, the launcher increments a counter in `app\<v>\starts`, and the game deletes that file when
  it reaches the main menu. When the counter reaches two, the launcher switches back to `previous`. The running
  game's files are never replaced, which avoids Windows file locks, and the binaries and `index.json` switch
  together.
- **Switch** = write `app\current.tmp`, rename it over `app\current` (atomic on NTFS through `MoveFileExW` with
  `MOVEFILE_REPLACE_EXISTING`, which `std::filesystem::rename` uses).
- The **launcher updates itself** rarely: since it has already exited, the game replaces `OpenYAMM.exe` after a
  healthy start (write beside it, then rename over it).
- The complete ZIP ships exactly this layout. Unzipping the complete package and updating produce the same tree.
- If the installation folder is not writable (for example under `Program Files`), the updater is disabled and says
  why. The ZIP is meant to be extracted to a writable folder.
- Recommended: sign the launcher and the game (for example through the free SignPath Foundation programme for open
  source). Self-updating unsigned executables attract antivirus false positives.
- Players on a version without an updater download the complete package one last time; §4's import then copies
  their saves and settings. When the new package is extracted over an old folder, ~4 GB of old `assets\engine.zip`
  and `assets\worlds\*.zip` remain. After the import has succeeded, the first launcher run offers to delete them
  (only those exact files, never `saves\`).
- *As implemented* (`engine/update/`, `game/launcher/WindowsLauncher.cpp`, `game/app/GameUpdater.*`):
  - `AppInstallation` owns the layout above and is the only code the launcher shares with the game (standard library
    only; the launcher imports `KERNEL32`, `USER32` and `msvcrt`). A version is *healthy* once `app\<v>\healthy`
    exists; until then the launcher counts starts in `app\<v>\starts` and, at two, makes `previous` current again and
    records `app\rolled-back`, which the main menu reports once.
  - The game marks its version healthy when it reaches the main menu or finishes a headless scenario (the release
    checks start new versions that way). The first healthy start removes the other version folders, packs the
    index no longer names, `app\previous`, and the 1.5 leftovers (`assets\engine.zip`, `assets\worlds\*.zip`,
    `runtime\`) without asking, and installs `app\<v>\OpenYAMM-launcher.exe` as `OpenYAMM.exe` when it differs.
  - `AppUpdater` checks, downloads (three parallel transfers into `update\*.part`, resumed with Range, SHA-256 checked
    before the rename into `assets\packs\`; one retry from scratch), extracts `OpenYAMM/app/<v>/` from the app
    archive through PhysicsFS into `app\<v>.staging` and renames it, then `activate()` switches `app\current`.
    Unchanged packs keep their file name, so only changed ones download. Manifests older than or equal to the running
    release are ignored, so a replayed manifest cannot downgrade.
  - The transport is WinHTTP (`HttpTransport`): the system's TLS, certificates and proxy settings; no curl or
    OpenSSL to ship and patch. A server that ignores a range is handled in the transport.
  - `openyamm.exe --headless-update [URL]` runs check, download and switch without the menu; the release checks use
    it to update the previous release to the candidate.
  - The main menu shows the running version, asks once whether to check at start (`[updates]
    check_for_updates = ask | auto | off`, also in Settings → Interface), then a quiet *Update to OpenYAMM X (N MB)*
    button, a progress dialog with Cancel and *Restart Now*, which starts the launcher and quits.
  - `[updates] url` selects the channel (default `https://jasicek.net/openyamm/updates/`); staging tests point it at
    `https://jasicek.net/openyamm-staging/updates/` without rebuilding anything.

### 9.2 Flatpak: OSTree repository, no custom updater

*Dropped on 2026-10-21:* Linux players use the self-updating tar.gz of §9.1. The text below is historical.

- **One stable branch name**: publish every release to branch `stable`; stop using the version number as the branch
  (`flatpak_branch="$version"` in `build_release_local.sh` and the workflow). Then `flatpak update` moves between
  releases.
- **Existing installs do not migrate by themselves.** Players on a per-version branch (`//1.5`) who install the
  first `stable` bundle end up with two installs side by side. Saves are safe, because both use the same per-app data
  folder, but the release notes and the download page must give the one-time cleanup:
  `flatpak uninstall io.github.openyamm.OpenYAMM//1.5`.
- **A persistent signed repository**, built on the release machine in the master tree (§7.4):
  `flatpak build-import-bundle repo OpenYAMM.flatpak`, then
  `flatpak build-update-repo --generate-static-deltas --gpg-sign=<key> --gpg-homedir=~/openyamm-keys/flatpak-gnupg
  --prune --prune-depth=3 repo`, and mirrored to `/var/www/html/openyamm/flatpak/repo` (objects before refs and
  summary). The GPG key therefore never reaches the server.
- **Bundles are signed and compressed fast** (*as implemented*). A bundle that records a GPG-verified remote must
  carry its commit's signature, or `flatpak install --bundle` refuses it ("no signatures found"); the build signs
  the commit with `flatpak build-sign` before `flatpak build-bundle`, which copies the detached signature in.
  OSTree compresses bundles and static deltas with single-threaded xz preset 8, hard-coded with no option: about
  1.3 MB/s, an hour for a 5 GB bundle, while our already-compressed packs shrink by under 0.2 %. The build preloads
  `packaging/flatpak/fast_xz_preload.c`, which swaps liblzma's encoder for its multithreaded one at preset 0; the
  output stays standard xz. Measured: 2 min 38 s for the signed 1.6 bundle on a busy machine, 0.5 % larger.
- **Measure whether static deltas pay off.** A changed pack is a new file with a new name, so a delta mostly repeats
  whole changed packs, and a good part of the repository estimate in §7.5 is deltas. Plain object pulls of ~100 large
  files are cheap. Compare update time and repository size with and without `--generate-static-deltas` on the first two
  releases, and keep them only if they help.
- **Bundles carry the remote**:
  `flatpak build-bundle --repo-url=https://jasicek.net/openyamm/flatpak/repo --gpg-keys=openyamm.gpg`.
  Installing the downloaded bundle sets up the remote, so later updates come through `flatpak update` and the
  software centre automatically. Also publish `.flatpakref` files as a one-click install.
- **Packs make OSTree efficient**: OSTree deduplicates files, so unchanged pack files are never downloaded again.
  This needs no Flatpak-specific work beyond §5.
- The game is built with `OPENYAMM_ENABLE_UPDATER=OFF`; Settings says "Updates are managed by Flatpak".
- Flathub is not a target here; its policies would apply to the bundled content.

### 9.3 Android: thin APK, packs in app storage

- **APK contents:** the native library, shaders, licenses and a small **bootstrap pack**
  (a few MB: fonts and the minimum Obsidian UI art for the setup screen). `registerOpenYammApkAssetsTask` in
  `android/app/build.gradle` stops unpacking the content zips. Expected APK size: tens of MB instead of 3.4 GB.
- **Content store** in app external storage (the current working directory):
  `content/current.json`, `content/next.json`, `content/packs/*.zip`, `content/update/`.
- **First start** (no compatible content): a setup screen rendered with the bootstrap pack shows the size, the
  Wi-Fi requirement and progress. The same C++ UI serves later updates.
- **Transport: Android `DownloadManager`** through JNI. It keeps downloading when the app is in the background or the
  screen is off, resumes on its own, shows a system notification and honours Wi-Fi-only. The C++ core queues
  requests and polls their status; hashing and the switch stay in C++. Check free space with `StatFs` first.
- **Updating the APK itself:** the manifest lists the APK with its `versionCode`. The game downloads it, verifies its
  SHA-256 and installs it through the `PackageInstaller` session API (needs `REQUEST_INSTALL_PACKAGES`; the player
  allows "Install unknown apps" once). The signing key must stay `~/openyamm-keys/android-release.jks`, the key
  every published APK so far was signed with. Players who prefer it can use Obtainium against the GitHub releases
  instead (§7.4, step 5).
- **Switch:** new packs download into the store first, while the current version keeps running. The new index is
  written as `content/next.json` with its `content_format`. When an app whose `content_format` matches starts, it
  promotes `next.json` to `current.json` (atomic rename). If the player cancels the APK installation, nothing
  changes. When the content does not match the installed app (a new APK installed by hand, for example), the game
  goes straight to the setup screen for the matching content.
- **Uninstalling deletes app storage**, including saves. Add **Export saves** / **Import saves** through the Storage
  Access Framework (a zip of `saves/`) and mention it in the release notes.
- Optional, later: **Import content** from a content archive downloaded on a PC, for players without suitable
  internet.
- *As implemented* (`android/app/src/main/java/org/openyamm/android/`): the update screen is a plain Android activity
  in Java, not a C++ screen with a bootstrap pack, so the thin APK needs no content at all.
  - The game activity stays the launcher entry, as in 1.5. Before the engine starts it promotes `next.json` when the
    running APK is at least the version it was downloaded for, and checks that `content/index.json` and all its packs
    are present in the format the library reads (`SupportedContentFormat`); otherwise it hands over to
    `OpenYammUpdateActivity` and closes. (A separate translucent start activity was tried first: Android then
    destroyed and recreated the game activity, and SDL, which allows one activity per process run, aborted.)
  - The content lives in app-private storage (`files/content/index.json`, `next.json`, `packs/`), not in external
    storage: other apps cannot change it on old Android versions, and players never see it. The game gets it as
    `--asset-root`. Saves and settings stay in external storage as before.
  - Transport: `HttpURLConnection` in the update activity (three parallel transfers, Range resume, SHA-256 before
    the rename), not `DownloadManager`, which cannot write to private storage. The screen stays on while it
    downloads; an interrupted download resumes next time. The first download starts by itself on an unmetered
    network and starts the game when done.
  - The manifest signature is checked by the game library through JNI (`nativeVerifyManifest`): the same Ed25519
    code and compiled keys as on Windows.
  - The update activity runs in its own process (`:update`) and stops the game's process first. A new APK is
    installed through a `PackageInstaller` session; Android asks the player to allow it once and to confirm.
  - The main menu's notice uses the same C++ code as on Windows; *Update* opens the update activity and quits.
  - Development APKs can still bundle their content (`openyamm.android.content=bundled`, the default);
    `build_release_local.sh` builds release APKs with `download`.
  - Not done yet: Export/Import saves (uninstalling still deletes saves), a Wi-Fi-only setting, notifications.

### 9.4 macOS: the downloaded app installs itself into Application Support

*Since 2026-10-23.* macOS uses the layout of §9.1 in the per-user folder, the same folder as the player's data:

```
~/Library/Application Support/OpenYAMM/
  OpenYAMM                     launcher (game/launcher/UnixLauncher.cpp)
  app/current, app/previous
  app/<v>/OpenYAMM.app         the game; its shaders are bundle resources
  app/<v>/OpenYAMM-launcher, index.json
  assets/packs/*.zip
  saves/, settings.ini, openyamm.log
```

- **Why not the download folder:** macOS runs a downloaded app that is not notarized from a read-only copy at a random
  path (App Translocation) until the player moves it, so the folder next to the app is neither writable nor stable.
  The per-user folder is both, wherever the player keeps the app.
- **Download package** `OpenYAMM-X.Y-macos-arm64.dmg`: a disk image of `OpenYAMM.app` as the macOS job built and
  signed it, a link to Applications to drag it to, and the licences (as OpenEnroth ships its macOS build). The
  publisher ships the image unchanged. The app carries no `index.json`: the publisher writes the index only at publish
  time (§7, reused packs keep their published file names), and changing a signed bundle breaks its seal, which macOS
  reports as a damaged app that cannot be opened at all. The app archive of the update channel holds the same bundle
  in `OpenYAMM/app/<v>/` with the index next to it.
- **The downloaded app never plays from where it is** (`game/app/AppleBundlePaths.*`). A release bundle outside an
  installation's version folder (`OPENYAMM_APPLE_PACKAGE_VERSION`, set for builds with a release version):
  - when the per-user installation has a current version, starts it in place of itself (`execv`), counting the start
    as the launcher does;
  - otherwise opens the content setup window, whose updater installs the published release (the app's own or a newer
    one) into the empty installation: app archive and packs. `AppUpdater` treats an installation without
    `app/current` as empty, and its first activation also installs the version's launcher, which *Restart Now* then
    starts. A channel older than the app offers nothing, as for a stale small package.
- Inside an installation the bundle is an ordinary version: `programDirectory()` maps its base path
  (`OpenYAMM.app/Contents/Resources`) to `app/<v>/`, so the index, the updater and the healthy-start cleanup work as on
  Linux. Downloads through libcurl carry no quarantine flag, so updated versions start without Gatekeeper.
- **Transport:** the libcurl backend of Linux, loaded from `/usr/lib/libcurl.4.dylib`, which every macOS ships.
- **Signing:** ad hoc only (`codesign --sign -` when the package is built), no Developer ID or notarization. The
  player clears the quarantine flag once (`xattr -dr com.apple.quarantine /Applications/OpenYAMM.app`) or allows the
  app on its first start in System Settings → Privacy & Security → *Open Anyway*.
- Not done: Intel Macs, notarization, and replacing the downloaded app itself (it only hands over, so an old copy
  keeps working).

## 10. Part G — user experience

- Main menu: a quiet "Update available — 0.8 (152 MB)" line with **Update** and **Release notes**. Never a modal
  dialog on start, and nothing during gameplay.
- The update screen uses the Obsidian menu style (`level_generation/ui/menu_study_20260928/`): progress, the
  remaining size, Pause/Resume and Cancel; at the end, **Restart now**.
- Settings → Updates: check mode, Wi-Fi only (Android), **Check now**, **Verify game files**,
  **Open data folder**, **Import saves…** / **Export saves**.
- Errors are short and actionable: "Not enough disk space: 1.2 GB needed", "Update server unreachable — retry
  later", "Update signature invalid — download the complete package from the website".

## 11. Part H — compatibility rules

- **Saves:** keep the explicit save-version migrations; refuse newer saves clearly. The updater never touches
  `saves/`. Consider an automatic copy of `saves/` to `saves/.before-<build>/` before the first start of a new
  version that bumps the save format (cheap insurance, removed after a few releases).
- **Settings:** sparse player files over code defaults, with versioned migrations only for changes of meaning
  (§4.3); the updater never replaces the user's file.
- **Binary and content:** always installed together from one manifest; `content_format` guards mismatches.
- **Mods:** loose files in `<user data>/mods/engine/` and `mods/worlds/<id>/` mount in front of the official packs at
  the same virtual paths (`AssetFileSystem::mountMods`), only over a release's packs. The start check, the repair and
  the updater never look at them; each start logs every mod file. `[updates] keep_modified_packs=on` (file only)
  instead mounts packs whose size differs from the index and turns off the repair and every update check. See
  [Changing the game's files](MODDING.md).
- **Optional worlds (future):** packs already carry `package`, so a client could install only `engine` + `mm6`.
  Postponed because MMerge-style cross-world travel expects all worlds mounted.

## 12. Testing

- **Unit (doctest):** manifest parsing and rejection cases (including a replayed older manifest), Ed25519 and SHA-256
  test vectors, `UpdatePlanner` diffs (fresh install, nothing changed, one pack changed, pack removed, `content_format`
  mismatch, app-only change), index validation and mount precedence, user data path resolution including portable mode,
  save and settings import, settings migration, launcher start counter and rollback.
- **Packager (Python):** §5.5 tests, plus cook-twice determinism per cooker.
- **Integration:** a small local HTTPS-capable test server with Range support (Python's `http.server` lacks Range)
  and a headless updater mode, for example `--headless-update --manifest-url …`. Scenarios: fresh install, an
  incremental update, an interrupted then resumed download, a corrupted pack, a bad signature, disk full, a crash
  on first start of the new version → rollback, cleanup after a healthy start.
- **Performance gate:** §6.2 measurements on desktop and Android release builds, before and after the pack split.
- **Settings:** the §4.3 tests.
- **Release scripts:** unit tests for retention, garbage collection (no referenced file is ever deleted) and upload
  order; `--dry-run` before every publish. The very first publish goes to a staging path on the server; download a
  test pack from it from outside the home network and check Range and cache headers before using the real paths.

### 12.1 Release checks (before every publish)

`packaging/release_checks.sh X.Y` (new) runs the checks below on exactly the packages in `build_release/` and
records a pass for that build; `publish_release.py` refuses to run without it. All of it runs on the release
machine, which already has Wine, the Android SDK and emulator, and an `openyamm_api35` AVD.

- **Windows under Wine**, using the release ZIP extracted into a scratch folder, so the shipped `openyamm.exe` is
  tested rather than a development build:
  - **Scripted scenarios:** `wine openyamm.exe --headless-run-scenario <absolute path>` for a small release set in
    `tests/scenarios/release/` (new), assembled from existing scenarios such as
    `shared_fx/mm{6,7,8}_map_lifecycle.yml`, `mm6/smoke_new_game_letter.yml` and `mm6/smoke_route_checkpoint.yml`:
    a new game, maps of all three worlds load, a save and a load. Every scenario must exit with success.
  - **One rendered start** with the engine's screenshot directives (`--set debug.screenshot_path=…`,
    `--set debug.screenshot_delay_seconds=…`) to confirm the game reaches gameplay; inspect the PNG. Wine's
    graphics stack differs from real Windows, so this catches startup, packaging and asset problems, not driver
    issues.
  - After Phase 1a: user data lands in the Wine prefix's `%APPDATA%\OpenYAMM`, and saves and settings import from
    the previous release's folder. After Phase 4: the previous release's install updates to this one from the
    master tree served locally, and a forced failed start rolls back.
- **Android in the emulator** (or a real phone over `adb` when one is connected, which is closer to players):
  - The APK is arm64-only. Android 11+ x86_64 emulator images with Google APIs run arm64 apps through ARM
    translation, slower but enough for a smoke test; confirm the `openyamm_api35` image does, or switch it to one
    that does.
  - `adb install -r` the new APK over the previous release (checks the signing key and that data survive), start
    it, take `adb exec-out screencap` captures, load a save, and scan `logcat` for crashes.
  - After Phase 5: the first-start content download and an update against the local master tree
    (`adb reverse` to a local HTTP server).
- **Flatpak:** install the bundle into a user installation, start it with a screenshot. After Phase 3:
  `flatpak update` from the previous release against the local master tree's repository (a `file://` remote).
- **Every platform:** saves and settings from the previous release are intact.

## 13. Phases

| Phase | Work | Done when |
|---|---|---|
| 0 | Decisions in §15; server setup from §7.5 (directories, nginx locations, retention); keys and offline backup (§7.4) | `https://jasicek.net/openyamm/updates/` serves a test file with Range and the cache headers |
| 1a | User data directory, save and settings import, install-relative asset root (§4.1, §4.2) | a new Windows ZIP extracted anywhere finds the player's saves and settings |
| 1b | Settings layers: one source of defaults, preference and state keys, sparse file, conversion, robust writes (§4.3) | a changed default reaches players who never touched it; existing choices survive |
| 2 | Pack split, `index.json`, engine mounting (§5, §6); all complete packages switch layout | all three platforms run from packs; no startup or map-load regression; packager tests pass |
| 3 | Local release tooling (§7.4): content packed once per profile, master tree, signed manifests, local OSTree repository, retention and garbage collection, ordered `rsync`; release checks (§12.1); complete downloads move to `jasicek.net/openyamm/downloads/`; Flatpak `stable` branch and bundles with `--repo-url` (§9.2); GitHub publish job and secrets removed | a release is published from the PC with one build, one check and one publish command; `flatpak update` downloads only changed packs; manifests published for Windows and Android; Nextcloud no longer needed for releases |
| 4 | Updater core + Windows launcher and versioned app directories + update UI (§8, §9.1, §10) | a Windows install updates release to release by downloading only changed packs, with rollback tested |
| 5 | Android thin APK, `DownloadManager` transport, bootstrap pack, APK self-install, save export (§9.3) | an Android install updates content and APK without a full download; the §6.2 measurements repeated with packs in app storage show no regression |
| 6 (optional) | Entry-level deltas: fetch a changed pack's central directory with Range, reuse unchanged local entries, fetch only changed entries, rebuild and verify the whole file's SHA-256 (falls back to downloading the pack when the rebuild does not match) | a one-icon change downloads about one icon |

Phases 1a and 1b are independent and can each ship immediately and alone; 1a is small and fixes the Windows save
problem, 1b is larger and riskier. Phases 2–3 already make Flatpak updates small, remove the whole-share folder
downloads and cap server storage.

Phases 4–5 are the most expensive and riskiest part (a self-updating executable with antivirus false positives,
APK self-installation), and they save less traffic than the size of a release suggests: about 90 % of the traffic in
§7.5 was first installs, which stay full size. Decide on them after Phase 3 ships, using fresh traffic numbers for
returning players (§15). Phase 6 matters only if 64 MiB granularity proves too coarse.

## 14. Alternatives considered

- **Binary diffs of the complete package** (bsdiff, `zstd --patch-from`): needs memory in proportion to multi-GB
  inputs, one patch per version pair, and a chain for players who skip releases. Packs need no chains.
- **Base package plus patch zips mounted on top:** simple at first, but patches accumulate and need periodic
  compaction; players far behind download a long chain.
- **Loose files with a per-file manifest:** exact deltas, but about 50 000 small files are slow on NTFS with antivirus
  scanning and make first installs slower; packs keep the efficient zip mounting.
- **Velopack / Squirrel (Windows):** good installers with deltas, but they compute deltas over the whole package
  (the multi-GB problem again), install to their own location, and cover neither Android nor the Flatpak.
- **Stores (Steam, itch.io with butler):** they solve updates completely, but depend on their content policies for
  the bundled content. Worth revisiting only as a distribution decision, not as a technical one.

## 15. Open decisions

1. **Hosting:** decided — everything, including player-facing download links, on nginx static paths on
   `jasicek.net` (§7.3, §7.5); the small download packages of the last two releases are kept, and GitHub Releases
   carries them too (2026-10-21). Google Drive is rejected and the
   Nextcloud share only keeps already-posted links working (§7.3). Later, if traffic outgrows the home upstream:
   object storage with free egress in front of `packs/` and `downloads/`.
2. **Releases:** revised on 2026-10-21 — from GitHub Actions on a `vX.Y` tag, with the keys as
   secrets of the `release` environment; test releases go to the staging site from a manual run; one `stable`
   channel ([Releases](RELEASE.md)).
3. **Developer-flavoured defaults that reach players today** (§4.3): for example `debug_console=true`. Decide the
   player value for each when moving defaults into code.
4. **Windows user data location:** decided on 2026-10-21 — the installation folder, on Windows and Linux.
5. **Android distribution:** thin APK only (recommended), or also keep a complete APK for offline installs.
6. **Pack target size:** 64 MiB (recommended), or 128 MiB if the performance gate shows mount costs.
7. **Update checks:** ask once on first start (recommended), or on by default.
8. **Phases 4–5:** built (Windows, Android, and Linux since 2026-10-21).

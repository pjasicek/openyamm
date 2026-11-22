# P: packaging and release size

Started 2026-11-22 by the fourth orchestrator (session openyamm-65). The user approved these savings on 2026-11-22:
"don't duplicate stuff from core engine if it's there; you can use for sure more compact WAV format; 1K textures for
decorations where it doesn't matter is OK; dungeon lighting bakes: if you think it's fine to cook lower detail it's
fine."

## Owns

- Xeen's entry in `tools/packaging/packs.yml` and the packager's rules that only Xeen needs so far
  (`tools/package_runtime_assets.py`: `share_model_textures`, `check_model_references`, table files under `models/`,
  development leftovers, Android x2 PNGs with a cook; tests in `tools/test_package_runtime_assets.py`).
- Xeen's Android cook (`assets_cooked/android/worlds/xeen/`, the Xeen line of `tools/cook_android.sh`).
- The size settings it sets on other lanes' content, logged in those lanes' files: the compact WAV step of AU's
  `level_generation/sounds/xeen_20261120/install.py`, the `xeen_deco_*.cook.yml` sidecars of S's decorations in
  `assets_source/worlds/xeen/models/`, `units_per_texel` in the Xeen indoor bake profiles
  (`tools/lighting/baked_indoors/profiles/xeen_*.yml`).
- Scratch: `output/xeen_p/`.

## Read first

`packaging/RELEASE.md`, `packaging/UPDATER_PLAN.md` (part B, packs), `tools/packaging/packs.yml`,
`devdocs/ASSET_COOKING_PLAN.md` §12-§15, `devdocs/xeen/briefs/FEEDBACK_FIX_RULES.md` (locks, runs), DECISIONS D-44.

## State (2026-11-22, end of session 2)

Xeen's packs, as a release would build them now (sharing on, every bake at 32 units per texel): desktop 23 packs
736.6 MiB, Android 21 packs 501.9 MiB (study before this lane: about 1,149 MiB desktop). Per item:

1. **Shared model textures.** 479 of Xeen's 1,057 cooked model textures (262.9 MiB) are byte copies of the engine's,
   MM6's, MM7's or MM8's (content-keyed names). The packager leaves them out of Xeen's packages when
   `share_model_textures: true` (packs.yml; on since session 2, see Requests), and
   `check_model_references` refuses a package whose GLB names a texture neither it nor a package it may read ships.
   The 78 textures shared with MM9 only (44.3 MiB) stay in Xeen (MM9 is no dependency, D-44; moving them into the
   engine would reshuffle the engine's and MM9's model packs for every player). assets_dev is unchanged: the sharing
   happens when packaging, so the cook and the game in development are untouched.
2. **Compact WAV.** AU's `install.py` writes IMA ADPCM WAVs (512-byte blocks; loops resampled to whole blocks so SDL's
   block padding adds no gap); 264 sounds 77.8 -> 18.9 MiB zipped. One-shots SNR median 33.8 dB (min 16.0 on hiss
   beds); loop seams continuous. Decoded in game (`OPENYAMM_AUDIO_TRACE`, X1's meadow bed).
3. **Decorations.** 22 sidecars: 6 small decorations at 1024 (over 128 texels per metre at 1K), 16 statue-sized ones
   with half-size relief maps (colour kept 2K), the great crown and both sphinxes untouched. Cooked textures
   601.7 -> 565.7 MiB.
4. **Packaging.** Xeen in packs.yml (not yet in `worlds:`, see Decide), `models/decoration_data.txt` ships (a table
   world.yml names), `.build_world.lock` and `maps/*.studio.yml` stay out, Android x2 surface cook and model cook.
5. **Bakes** at 32 units per texel: all 60 Xeen profiles set to 32 (test: XD-04 lit gate hall and DD-02 dark stair
   captured at 16 and 32, mean absolute difference 0.6-2 levels, no visible loss: `output/xeen_p/shots/cmp_*.png`;
   lightmaps about 36 % of their size). Rebake queue `output/xeen_p/bake/rebake_all.sh` (bake.lock first, then the map
   lock without waiting; a held map is retried in later passes, 10 minutes apart); progress in
   `output/xeen_p/bake/rebake.log`. Indoor bakes 153 MiB raw before.

## Requests (open)

None. A1's loader fallback for shared model textures (`GltfModelLoader.cpp` `openSharedModelTexture`, doctest "glTF
loader reads a cooked texture its package leaves out ...") landed in merge point 41 (2026-11-22 00:55); session 2
switched `share_model_textures: true`. **No `CONTENT_FORMAT` bump** (the earlier plan was wrong): the installed
updater (AppUpdater `loadAssetPackIndex` of the new version's index.json) refuses any format but its own, so a bump
would stop every installed 2.x from updating itself; and no old binary ever runs the shared content (desktop installs
app and content as one; Android stages content as next.json and promotes it only once the APK it was downloaded for
runs). The release that ships packs.yml's switch must also ship the fallback's source (`engine/models/GltfModelLoader.cpp`,
uncommitted on 2026-11-22): without it, MM6's peasant man (2 textures), MM8's polearm (1) and 30 MM9 fire decorations
(braziers, candles, chandeliers: 2 textures) would load without textures.

## Release check as CI runs it (the orchestrator's request, 2026-11-22)

`.github/workflows/packages.yml` on a `vX.Y` tag (never tag, push or publish from a lane):

1. **content (desktop, android)**: a sparse checkout of `assets_dev/engine/`, `worlds/mm6`-`mm9`, `languages/`,
   `_legacy/sprites_original/` (android: plus `assets_cooked/android/`, minus every desktop BC7 cook, whose names come
   from the git index); builds `openyamm_sprite_atlas_cook`; runs `tools/package_runtime_assets.py --assets-root
   assets_dev --output content/<profile> --profile <profile> [--sprites assets_cooked/android/sprites_new] --cooker
   build/game/openyamm_sprite_atlas_cook --report`. That run checks: sprite profiles (`--verify`), the profile overlay
   of every cooked model/terrain/effect/sky/HUD texture (Android: any missing ASTC fails), pack sizes (128 MiB, core
   24 MiB), every domain listed in packs.yml. Without sources it skips the surface cook check.
   Local: `python3 tools/package_runtime_assets.py --assets-root assets_dev --output output/xeen_p/ci_<profile>
   --profile <profile> [--sprites assets_cooked/android/sprites_new] --cooker build/game/openyamm_sprite_atlas_cook
   --report` (desktop about 9 GB, android about 6 GB: check `df` first, delete after). Before the Android run:
   `python3 tools/cook_models.py --profile android` (all worlds, incremental: picks up the engine's changed decoration
   and model textures), the cook lines of `tools/cook_android.sh` (without its cmake line: lanes do not build) and
   its `--verify` lines.
2. **windows / linux / macos**: build the thin package and `openyamm_unit_tests`; check the stage's files, the Linux
   binary (`packaging/check_linux_binary.sh`), SDL drivers; run `openyamm_unit_tests
   --source-file='*UpdaterTests.cpp,*UserDataPathsTests.cpp,*LogFileTests.cpp,*AssetPackIndexTests.cpp,
   *SettingsFileTests.cpp'`. Local: A1's build only (lanes do not build); the test binary A1 last built can run.
3. **android**: `android/build_release_apk.sh` (A1 / the orchestrator).
4. **scenarios**: the desktop stage plus the desktop packs play every line of `tests/scenarios/release/scenarios.txt`
   (`--headless-run-scenario`). Local: the same list with `build-xeen/game/openyamm` against the packaged folder.
5. **publish** (`packaging/publish_release.py prepare / sign / check --scenario / upload`): signing keys; `check` plays
   one scenario on a fresh installation. Not run locally beyond `prepare` into a scratch folder, if at all.

**(Resolved in 1afa1b3f2c: Xeen is committed and shipped; kept for the record.)** Xeen could not ship through CI
then: `assets_dev/worlds/xeen/` was git-ignored (`.gitignore` line 44: 0 tracked
files) and so is its Android cook (`assets_cooked/android/worlds/xeen/`), the workflow's checkout lists only
`worlds/mm6`-`mm9`, and packs.yml's `worlds:` lists `[mm6, mm7, mm8, mm9]`. Shipping it needs: un-ignore and commit the
world (the packager already leaves `source/`, `*.studio.yml` and dot files out), commit the Android cook, add
`/assets_dev/worlds/xeen/` (both profiles; android also its `textures_x4/` exclusion, already a wildcard) to the
workflow, `xeen` to `worlds:`, and A1's loader fallback before `share_model_textures: true` (else Xeen ships its
262.9 MiB of shared copies).

Tonight's shipped changes to cover in the Android cook: engine Dimension Door pictures
(`engine/ui/gameplay/dimensional_travel/tp*4.png`: plain PNGs, no cook), Xeen's `tp*5.png` and loading screens
(Xeen UI PNGs), the mirror liquid (`engine/liquids/liquids.yml`, data), the 1K decorations (Xeen model cook),
the engine model textures changed in git status (`engine/models/textures/*.oytex`: the Android model cook), the new
spellbook rows (data). Status of each run: see Log.

## Session 3: the v3.0 tag check on the committed tree (2026-11-22 evening)

Checked on HEAD = d81bed08da as the `v3.0` tag run would see it: a `git clone --shared --no-checkout` into
`output/xeen_p3/wt` with the content job's exact sparse list (desktop, then the android list with its exclusions, so
`sparse_files` reads the left-out BC7 names from the index as on CI), no `assets_source` (CI checks out no
submodule, so the surface cook check is skipped as on CI), `--release 3.0 --build 3.0`, cooker
`build/game/openyamm_sprite_atlas_cook`. Every job through `tools/heavy.sh` (packaging 16, games 6).

| CI step | Result |
|---|---|
| content (desktop) | PASS: 324 packs, 10,642.5 MiB (base 10,018 MiB + 624.5 MiB optional language packs); largest `mm6.models.0` 108.6 MiB; largest core `engine.core` 14.4 MiB; none over 128 / core 24; every domain listed; sprite `--verify` OK. Shared model textures left out: Xeen 275.7 MB, MM6 2.3 MB, MM9 0.8 MB |
| content (android) | PASS: 216 packs, 5,884.1 MiB; largest `engine.icons_x2.7` 69.9 MiB; core 14.4 MiB; every ASTC overlay present (no missing/stale profile texture); sprite profiles match and verify. Xeen 116.6 MB shared |
| installation unit tests (the workflow's `--source-file` list, `build/tests/openyamm_unit_tests` of 17:33) | PASS 38/38 test cases, 310 assertions |
| release scenarios from the packed desktop content (`build/game/openyamm --asset-root ci_desktop`, one user folder) | PASS 16/16 (all "Scenario passed"; logs `output/xeen_p3/scen/`). Extra, from the same packs: Xeen `dimensional_travel_vertigo`, `shop_stock`, `maw_new_game`, `x6_warzone_entrance` pass; 0 untextured actors in any log |
| publish `prepare` | Not runnable here (needs the three desktop stages and a signed APK). Its content half run against the live stable site (`load_content` + `final_index` + `read_notes`): published 2.8, 3.0 is newer; desktop 61 new packs 1,547.6 MiB (Xeen 775.8, engine 339.5, MM9 233.4, MM7 118.5, MM6 62.8, MM8 17.5), 263 reused; Android 52 new 1,058.1 MiB (Xeen 541.1), 164 reused; the draft notes 1,274 of 1,500 characters |
| other local checks | `tools/test_package_runtime_assets.py`, `tools/test_runtime_packs.py` (11), `packaging/test_publish_release.py` (9), `packaging/test_android_versions.py` (5) OK; `tools/lighting/stale_bakes.py --check` 0; `tools/maw/xeen_balance.py --check` 82 maps 0 errors; **`tools/maw/mm9_balance.py --check` FAILS: `guberland.blv: its pack reserve was made for another scene`** (6966c1c87b changed the hag's monster id in `guberland.scene.yml`; at runtime the game ignores the stale reserve, so MAW's Guberland has no extra packs: no crash, no CI failure) |

Xeen per profile (packs.yml `xeen`): desktop 25 packs 775.8 MiB (music 2 packs 43.6, audio 19.7, core 5.6, maps 6.9 +
lighting 4 packs 159.8, models 10 packs 387.0, textures_x4 96.6, icons_x2 44.8, world_items 8.8, ui 2.8,
surface_materials_x4 0.3); Android 23 packs 541.1 MiB (models 226.8, textures_x2 26.0, the rest as desktop).
Totals per world, desktop / Android MiB: engine 1,848.5 / 1,368.1, MM6 1,798.9 / 849.0, MM7 1,330.2 / 720.5, MM8
1,378.8 / 728.0, MM9 2,885.9 / 1,654.9, Xeen 775.8 / 541.1, language packs 624.5 / 22.4 (Android ships fonts only).

What CI sees that git lacks: nothing the jobs need. Untracked in the shipped roots are only
`assets_dev/_legacy/sprites_original/*.bmp` (2,217 ignored archive sources; no lighting bake depends on one, the
packaging passed without them) and `worlds/xeen/.build_world.lock` (left out anyway). `assets_source` is not needed.
`.github/workflows/studio.yml` (Map Studio CI) is untracked, so a tag runs no studio checks.

Version 3.0: the meta job's regex accepts `3.0`; Android versionName `3.0`, versionCode from the commit time, not the
label: 28,139,833 for d81bed08da (v2.8: 27,820,027), so the APK updates 2.8. The installed updaters compare
(major, minor) pairs (`compareReleaseVersions`: (3,0) > (2,8)); the publisher's `version_key` the same. Content
format stays 1 (index.json says 1): `AssetPackIndex` refuses any other format, so a bump would stop every installed
2.x from updating itself, and no 2.x binary runs 3.0's content (desktop installs app and content together; Android
promotes the downloaded content only under the new APK). `UpdaterSchema` stays 1; every pack mounts under `/engine`
or `/worlds/<id>` (checked by `load_content`).

Stale player-facing sizes (not tools; REQUESTS): the GitHub release text in `packages.yml` ("about 9 GB, 5.3 GB on
Android") should read about 10.5 GB and 6.1 GB (bases without optional language packs: 10,018 MiB, 5,862 MiB);
`packaging/RELEASE.md` says 5 GB / 3 GB.

Scratch deleted after reading (the clone, both content folders); kept: logs and indexes in `output/xeen_p3/`.

## Next

1. Xeen is committed and shipped (1afa1b3f2c). Re-run the session 3 check only if content changes before the tag.
2. After any further Xeen or engine model/texture change: `tools/cook_android.sh` (lanes: its lines without cmake,
   `output/xeen_p/s2/android_chain.sh` without its packaging loop).
3. Delete `output/xeen_p/wav/pcm_before/` once the user has heard the ADPCM sounds.
4. Optional: `collect_languages` treats only `mm<N>.po` as world catalogs; a future `text/xeen.po` would ship even in
   a release without Xeen (harmless text).

## Log

- 2026-11-22 session 1: items 1-4 as in State. CI checks run locally: desktop packaging as CI runs it (mm6-mm9,
  share off): 299 packs, 9,868 MiB, no pack over 128 MiB (28 over the 64 MiB target, as before), surface cook 0
  problems; the 16 release scenarios played from those packs with `build-xeen/game/openyamm --asset-root`: 16 passed
  (note: CI pipes each scenario into `| cat`, so a failing scenario does not fail the job); installation unit tests
  38/38 (`build-xeen/tests/openyamm_unit_tests`); `tools/test_package_runtime_assets.py`, `test_runtime_packs.py` OK.
  Android: `output/xeen_p/android_chain.sh` (waits for Xeen's model cook, then every Android cook of
  `cook_android.sh` without cmake, their verifies, the CI-equivalent Android packaging into
  `output/xeen_p/ci_android`, Xeen's Android packs with sharing); log `output/xeen_p/android_chain.log`. Delete
  `output/xeen_p/ci_android` and `pack_android_share` after reading the sizes (several GB).
- 2026-11-22 session 2 (final release check): `share_model_textures: true` (no content format bump, see Requests).
  Rebake queue done (01:01, all 60 at 32), `stale_bakes.py --check` 0. Android: every cook of `cook_android.sh`
  current (0 to cook: models 2,928, surface 5,150 + Xeen 192, terrain 38, effects 15, UI 278, sky 32), every verify 0
  problems. CI as the workflow runs it today (mm6-mm9, share on): desktop 299 packs 9,865.4 MiB, Android 231 packs
  5,943.7 MiB, none over 128 MiB, cores <= 14.4 MiB; 16/16 release scenarios pass from the desktop packs
  (`build-xeen/game/openyamm`); actor models of every world 899 descriptors / 299 models 0 refused from the packs; all
  44 MM9 maps' decoration models load from the packs (10 maps with the shared-texture braziers). With Xeen (dry):
  desktop 322 packs 10,602.1 MiB (Xeen 23 packs 736.6 MiB, 275.7 MB of shared textures left out), Android 252 packs
  6,445.6 MiB (Xeen 21 packs 501.9 MiB, 116.6 MB left out); 16/16 release scenarios; Xeen actors 338 descriptors / 85
  models 0 refused; decoration models of all 81 Xeen maps with decorations load (DD-16 has none), including the 5
  decorations on shared textures; captures from the packs `output/xeen_p/s2/shots/dd01_sheet.jpg` (goblins, ratmen,
  rats, bats textured); Xeen scenarios from the packs: dimensional_travel_vertigo, shop_stock, maw_new_game pass,
  quests_smoke fails at step 10 "Valia gave no Crystal Key" on development assets too (A3's, not packaging).
  Installation unit tests 38/38, packaging tests (`tools/test_package_runtime_assets.py`, `test_runtime_packs.py`,
  `packaging/test_publish_release.py`, `test_android_versions.py`) OK, the publisher's content check
  (`publish_release.load_content`) accepts the desktop content, studio workflow steps (oymap_tests 510/510, fmt,
  slice build, ids.lock) pass, MAW checks 0. Logs and indexes in `output/xeen_p/s2/`; all scratch packs deleted.
- 2026-11-22 session 3 (v3.0 tag check on the committed tree d81bed08da): see "Session 3" above. Content desktop
  324 packs 10,642.5 MiB and Android 216 packs 5,884.1 MiB pass every packager check; installation unit tests 38/38;
  16/16 release scenarios from the packed desktop content (plus 4 Xeen scenarios); packaging and publisher tests OK;
  publish prepare's content half against the live site: 3.0 > 2.8, desktop update 1,547.6 MiB, Android 1,058.1 MiB.
  Open: MM9 Guberland's MAW pack reserve is stale (`mm9_balance.py --check`); release-text sizes in packages.yml.
  No packaging-tool bug found; no tool changed.

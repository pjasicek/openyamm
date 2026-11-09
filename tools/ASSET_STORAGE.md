# Asset storage

The portable repository contains engine/game/editor code, tests, reusable tools,
editable runtime tables/scripts/configuration, and the ready-to-use runtime payloads.
The default game loads `assets_dev`; CI creates release ZIPs from those assets.

| Location | Git ownership |
| --- | --- |
| `assets_dev/` | Runtime payloads, tables, scripts, manifests and configuration in normal Git |
| `assets_dev/worlds/mm9/`, `mm9/` | Optional local MM9 world/import payloads; excluded for now |
| `assets_cooked/android/sprites_new/` | Prebuilt Android ETC2/EAC creature packages in normal Git |
| `assets_dev/engine/effects/authored/textures/*.oytex`, `assets_cooked/android/engine/effects/` | Prebuilt BC7 and ASTC effect sprite atlases in normal Git; their generated PNG frames stay local in `assets_source` (`ASSET_COOKING_PLAN.md` §11) |
| `assets_dev/engine/icons_x2/obsidian_*.oytex`, `assets_cooked/android/engine/icons_x2/` | Prebuilt BC7 and ASTC Obsidian HUD art (and ASTC face atlases) in normal Git; the Obsidian PNG sources are in `assets_source/engine/icons_x2` (`ASSET_COOKING_PLAN.md` §10) |
| `assets_source/` | Submodule [openyamm-source-assets](https://github.com/pjasicek/openyamm-source-assets) (private, plain Git, shallow): the source assets below |
| `assets_source/worlds/mm*/models`, `assets_source/engine/models` | 3D model sources (creatures, attachments, decorations, satchels; `tools/install_model.py`) |
| `assets_source/worlds/mm*/textures*`, `terrain_x2`, `assets_source/engine/terrain` | Original MM6–MM9 BMPs, the x2/x4 surface masters the build cooks and the native terrain tiles `tools/terrain_materials.py` reads |
| `assets_source/engine/terrain_materials`, `assets_source/engine/effects` | Packed terrain material sources (raw CC0 downloads stay local) and generated effect frames |
| `assets_source/creatures/`, `assets_source/engine/sprites_new/` | Local only (ignored by the submodule): the restored x2 sprite creature bank and its exports |
| `assets_editor_dev/` | Local editor overlays |
| `data/` | Local original extraction; unused by the current game |
| `assets_source/textures/native_mm6_mm8/` | Local archive of original MM6–MM8 textures |
| `reference/` | Local references only; excluded from both Git and LFS |
| `level_generation/` | Local generation projects and artwork; excluded from Git and LFS |
| `tools/creatures/`, `tools/paperdoll_review/` | Reusable reviewer code and small workflow documents in normal Git |

Both GPU profiles are already cooked. Builds validate them and CI packages them;
neither operation requires lossless inputs or texture encoding. For artwork changes,
authors retain final base/mask PNG exports, palette lookups and manifests locally at
`assets_source/engine/sprites_new/` and explicitly recook both profiles from those inputs.
The MM6 bank remains at `assets_source/creatures/mm6/`, including `adaptations.json`,
selected masters, composite sheets, guides, provenance and saved review records.

The current Android profile contains all 60 MM6 families in 402 files (419.1 MB).
Removing 1,046.6 MB of cooking inputs from normal Git while adding this profile
reduces the current tracked payload by 627.5 MB. Local inputs remain intact.

MM6–MM9 surface textures are cooked per platform (desktop BC7 x4 into `assets_dev`, Android ASTC x2 into
`assets_cooked/android`; see `ASSET_COOKING_PLAN.md` §9). Their sources, including the original x1 BMPs the lighting
bakes record as dependencies, live in `assets_source` under the same relative paths; `assets_dev/worlds/mm*/textures`
keeps only the `.act` palettes.

## Full game checkout

Clone normally, then build and run:

```sh
cmake -S . -B build
cmake --build build --target openyamm -j25
./build/game/openyamm
```

The source assets are an optional submodule. Without it the game builds and runs from the cooked runtime files in
`assets_dev` (the cooks skip missing sources and keep their outputs; the game skips its stale-bake check). To cook,
bake or install models, fetch it (shallow: only the current snapshot):
`git submodule update --init --depth 1 assets_source`. The portable
checkout includes MM6, MM7, MM8 and MMMerge, with the optional MM9 payload excluded.
Local authoring banks and build outputs use additional space.

CI's sparse checkouts exclude authoring inputs and include the needed prebuilt
profiles. ZIP packaging remains a CI/release step, separate from default development
launches. Use `git clone --depth 1` to avoid downloading old history when it is not needed.

After changing accepted sprite exports, use the explicit maintenance commands:

```sh
cmake --build build --target openyamm_sprite_atlas_cook -j25
python3 tools/cook_sprite_atlases.py --profile desktop
python3 tools/cook_sprite_atlases.py --profile android
android/repack_runtime_assets.sh
```

The Android output defaults to `assets_cooked/android/sprites_new/`. Its metadata and
palette lookups must match the desktop profile before packaging can proceed. Normal
`openyamm` builds only validate prebuilt assets, even when local authoring inputs exist.

## Optional authoring tools

Install Python dependencies with `python3 -m pip install Pillow numpy PyYAML`.

The creature editor code is retained under
`tools/creatures/acceptance_viewer/`, with the selected-bank
entry point in `tools/review_creature_sources.py`. With the local MM6 bank present:

```sh
python3 tools/review_creature_sources.py serve --port 8767
```

The equipment placement app is retained under
`tools/paperdoll_review/`. Its `build.py` consumes the
optional local HUD restoration manifests/checkpoints and artwork to create
`catalog.js`. Serve the repository root with `python3 -m http.server 8899 --bind 127.0.0.1`
and open `/tools/paperdoll_review/index.html`.
Its generated catalog, artwork and review exports stay out of Git.

Back up selected authoring banks as separate versioned archives, keeping their
manifests and adaptations with the referenced images. Restore an archive at its
original repository-relative paths to resume editing. No authoring archive is
published or downloaded automatically by the build.

## Source asset submodule

`assets_source` is the separate repository `openyamm-source-assets`, so binary source history never enters this
repository, and checkouts fetch it only on demand. Commit source changes inside `assets_source`, push that repository
first, then commit the updated submodule pointer here. Its history only matters for going back to an old source
version: to keep the hosted size near the size of the current files, it may be squashed now and then (a fresh
snapshot commit, force-pushed; the main repository's older pointers then no longer resolve).

## Optional LFS authoring material (superseded by the submodule)

`.gitattributes` routes explicitly added binary masters under `assets_source/` to LFS.
Runtime assets under `assets_dev/` and `assets_cooked/` have normal-Git exceptions. Authoring
JSON/YAML manifests, adaptations and provenance remain ordinary Git files when
selectively added alongside a source bank.
Authors must run `git lfs install --local` before adding source binaries and check
`git lfs ls-files` before committing them; attributes alone do not install the filter.

Apart from the world texture sources, no authoring bank is tracked. Other source banks remain
ignored: these attributes are a policy for deliberate future additions, not an upload
of local restoration attempts. Enroll only selected authoritative masters, composite
returns, outline guides and necessary derivation inputs. Keep `reference/`, `data/`,
caches and historical attempts out.

Game-only users and CI need only the world texture sources from LFS. For other LFS banks, a clone can
skip their download using `GIT_LFS_SKIP_SMUDGE=1 git clone <repository-url>` and still
build/package the game. Authors with Git LFS installed can fetch a selected bank with
`git lfs pull --include="assets_source/creatures/mm6/**"` after it is published.
Without LFS, optional files remain pointers; they are not inputs to the game build.
LFS needs a backing store with sufficient quota before source banks can be shared;
configuring attributes alone does not provide that store.

## Existing history

These rules affect the new tree and future additions. Removing files from the
index preserves local files and does not erase blobs already in Git history.
Historical cleanup is a separate migration; a shallow clone avoids downloading
old history. No history rewrite or Git object pruning is part of this storage change.

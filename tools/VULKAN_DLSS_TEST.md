# Vulkan and DLSS Neural Rendering experiment

`OPENYAMM_USE_VULKAN=ON` selects bgfx Vulkan and builds the game's SPIR-V shaders with the compiler sources
shipped in the pinned bgfx checkout. The option defaults to OFF. Normal Linux builds retain OpenGL.
The isolated launcher accepts `--binary` to select the separate build for preparation and rendering.

## Build and run Vulkan

```sh
cmake -S . -B build-vulkan -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DOPENYAMM_USE_VULKAN=ON \
  -DOPENYAMM_BUILD_TESTS=OFF -DOPENYAMM_BUILD_TOOLS=OFF
cmake --build build-vulkan --target openyamm -j25
./tools/run_game.sh --isolated vulkan_mm6 --binary build-vulkan/game/openyamm \
  --world mm6 --map oute3.odm --set video.resolution=1280x720
```

For this workspace, `build-vulkan` was configured with `FETCHCONTENT_SOURCE_DIR_<NAME>` pointing at the
existing `build/_deps/*-src` directories and `FETCHCONTENT_FULLY_DISCONNECTED=ON`. Dependencies are shared
as sources; compilation outputs remain separate. These paths are recorded in `build-vulkan/CMakeCache.txt`.
Reconfiguring that directory preserves them. Deleting the original dependency sources would require reconfiguration.

## Local DLSS layer test

The external layer in `third_party/DLSS5VKLayer` intercepts native Vulkan presentation. A Windows helper
under Wine receives the finished frame and calls the Neural Rendering DLL. Streamline and ReShade are not
part of this path. The HUD is included in the submitted image. This is an experimental external layer,
not an engine DLSS SDK integration.

The test artifacts are isolated under the ignored `build-vulkan/dlss-test/` directory.
The current default runner is GE-Proton11-7 through UMU and Steam Runtime 4 (see the update below).
The initial Wine 8 setup is retained for comparisons:

- `libVkLayer_NV_dlssnr.so`, `VkLayer_NV_dlssnr.json`: locally compiled 64-bit layer and process-local manifest.
- `dlssnr_helper.exe`, `dlssnr-shmctl`: helper and status tool compiled from the same source revision.
- `nvngx_dlssnr.dll`: symlink to the user-provided DLL in `third_party/dlss/`.
- `wine-prefix/`, `shm.bin`, `dxvk.conf`: private Wine prefix, transport and NVIDIA visibility settings.
- `check.py`: local test supervisor; launches the helper and isolated game, captures the game's own X11 window
  by PID, records status and stops the helper. It defaults to the isolated GE-Proton installation;
  `--legacy-proton` selects this machine's original Proton/Wine 8 setup.
- `helper-frames.log`, `wine-frames.log`, `layer.log`, `neural-status.txt`: initialization and frame-processing evidence.
- `*-run.txt`, `*.png`: paths to the isolated run records and screenshots.

Re-run the prepared local experiment from the repository root:

```sh
python3 build-vulkan/dlss-test/check.py mm6 oute3.odm --neural
```

Omit `--neural` for a Vulkan baseline. The supervisor waits for the new helper's Vulkan context before starting
the graphical test. The supervisor is a local build artifact, not an installed launcher.
Rebuilding these artifacts after deleting the test directory requires the external project's build workflow
in `third_party/DLSS5VKLayer/README.md`.

The test uses `VK_LAYER_PATH`, `VK_INSTANCE_LAYERS=VK_LAYER_NV_dlssnr`, `VKLayer_DLSS5=1` and `DLSSNR_SHM`
only for the game process. No global Vulkan layer, desktop environment setting or host driver was installed.
The transport's parent directory must be owned by the user and mode 0700; its file must be mode 0600.

Local build details: Linux layer and CLI were built with GCC; the layer used the installed Linux 5.15 UAPI
`asm/unistd_64.h` for `pidfd_getfd`, absent from the default 5.4 userspace headers. The Windows helper was
built with MinGW GCC 9.3 packages downloaded and extracted into `toolchain/`, without system installation.
The test used Wine 8.0 from the installed `Proton - Experimental` (20230529), with its matching DXVK 2.2
`d3d11.dll`, `dxgi.dll` and DXVK-NVAPI `nvapi64.dll`. `dxgi.nvapiHack=False` and `dxgi.hideNvidiaGpu=False`
are necessary with that DXVK version. DMA-BUF transfer was disabled for the test; shared memory worked.

## Results: 2026-09-16

The initially supplied `third_party/dlss/nvngx_dlssnr.dll` and `nvngx_dlssnr (1).dll` were identical.
The user subsequently replaced the runtime and removed the duplicate; these properties describe the initial file:

| Property | Value |
| --- | --- |
| File version | 310.8.0.0, not 310.9.1 |
| Size | 165,840,496 bytes each |
| SHA-256 | `4b8d19bc3eff58a084f5eca7489c921501c203450169fb82ff4f649a4482ba05` |
| Embedded minimum driver | 615.00 |
| Test GPU / installed driver | RTX 3060 Ti / 535.230.02 |
| External layer revision | `117c953` |

The supplied DLL loaded, the helper selected the RTX 3060 Ti, and a 1280x720 frame crossed the native
Vulkan/Wine transport. With the complete DXVK dependencies and NVIDIA visibility configuration:

```text
VULKAN_Init_Ext(ver=0x14) -> 0x1
GetFeatureRequirements -> 0xbad00005
VULKAN_CreateFeature(18) pass 0 -> 0xbad00001, null handle
model_up=0
helper_frames=0
```

NGX initialization succeeded, but Neural Rendering feature creation failed. The requirements call returned
invalid-parameter, and feature creation returned a generic failure. The layer's `DLSSNR.Available=0` diagnostic
also reports that the queried parameter was missing. These results do not isolate the root cause to the driver:
the old Wine/DXVK stack, hardware support and the layer's private NGX ABI remain possible compatibility factors.
The DLL's embedded driver requirement is substantially newer than the installed driver, but a driver upgrade
alone has not been shown to resolve the failure. **No successful neural frames or DLSS quality comparison.**

### User-supplied patched replacement

The replacement at the same `third_party/dlss/nvngx_dlssnr.dll` path has SHA-256
`8270b350cd82de5ce89806872cdd6b6a9249b80836b91bbeb3573470744cc206` and size 165,840,496 bytes.
Parsing its CUDA fatbin records found 15 CUBIN entries each for SM 75, 86, 89 and 120, plus eight PTX entries
for SM 120. It therefore includes native RTX 3060 Ti / SM 86 kernels. This agrees with the community's
[documented architecture distinction between the RTX40 and SF builds](https://github.com/UgurInanc12/DLSS5Kit#what-it-verifies-rather-than-assumes).

The helper's symlink points directly at the replacement, so no copying or renaming is needed. NGX initializes,
but feature creation now raises a C++ exception. A separate diagnostic helper, built from a temporary copy of
the guard source under `build-vulkan/dlss-test/`, reads the exception message without modifying the runtime:

```text
CubinBackendNGX::get_kernel 'cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8' failed (NvAPI_Status=-1)
```

This is a kernel-loading failure after reaching the patched implementation. It is a different failure from
the initial runtime's immediate generic error; successful DLSS processing is still unverified.
The repository's external-layer sources and original helper were left unchanged.

Retesting with the layer's pinned **DXVK-NVAPI 0.9.2** produced the same kernel-loading exception.
Its release archive matched the upstream launcher's SHA-256
`60c284223530d643c446c263f1e1a96c6de7b5ff21796219646da734d97a70d6`.
The isolated directory now contains this newer `nvapi64.dll`, with the previous copy retained as
`nvapi64-proton2023.dll`. The matching installed Proton `d3d12.dll` and `d3d12core.dll` were also copied into
the test directory to satisfy its imports; the supervisor enables their native overrides.
`nvapi64.log` confirms version 0.9.2, successful NVAPI initialization, RTX 3060 Ti detection and driver 535.230.2.
Thus the final failure is not merely a missing NVAPI DLL. The patched runtime still reports `model_up=0` and
`helper_frames=0`; no driver upgrade or newer Wine runner has been tested. The ordinary helper reproduces the
failure; `--diagnostic` selects the separate helper that also records the exception message.

A separate SF-v2 archive was downloaded while the user was replacing the local DLL, but was not installed or
executed. Its archive hash `1da35941894994eb087e017577829e492454e9bae3a6a9397027069ceb74955c` and contained DLL hash
`6eb209e764f39872625debd6abaf45e2bb6322f6f270f781f70c059ae30b3927` match the
[published Wan2GP checksums](https://github.com/deepbeepmeep/Wan2GP/blob/main/docs/DLSS5.md#tested-component-integrity).

The separate Release Vulkan build and the normal OpenGL build passed compilation. Desktop checks covered
MM6 outdoors (`oute3.odm`) and indoors (`6d01.blv`), MM7 outdoors (`7out01.odm`) and MM8 outdoors (`out01.odm`).
Screenshots verified Vulkan world geometry, textures and UI. The normal OpenGL MM6 run also exited successfully.
The shared fog shader now receives sunlight as a function argument, making its input scope valid for the
SPIR-V/HLSL compiler while preserving the GLSL calculation. These are rendering smoke checks, not performance
benchmarks or exhaustive gameplay validation. Windows and Android were not tested in this experiment.

## Proton update: GE-Proton11-7

Installed the [latest official Proton-GE release](https://github.com/GloriousEggroll/proton-ge-custom/releases/tag/GE-Proton11-7)
available on 2026-09-16 into `build-vulkan/dlss-test/runners/GE-Proton11-7-x86_64/`.
The downloaded x86_64 archive matched the release API's SHA-256
`c5448b76a230384e2d7bc6beb5ccb97bafb7e2c3b6c527cb03a1a546bbcb00a0`; the redundant archive was removed after
extraction and validation. `runner-install.json` preserves the installation and test details.

The test runs through UMU 1.4.4 and Steam Runtime 4 (`4.0.20260805.254769`), following
[Proton-GE's documented outside-Steam launch method](https://github.com/GloriousEggroll/proton-ge-custom#ge-proton).
UMU verified the downloaded runtime's SHA-256 and mtree. It uses the already available Python 3.14 interpreter.
The isolated `ge-prefix/`, `ge-data/` and `ge-cache/` directories hold its prefix, runtime and cache.
The `ge-helper/` directory contains the helper and a symlink to the user-supplied patched NR DLL;
DXVK, VKD3D and NVAPI come from the new Proton itself. No old DLL copies are mixed into this directory.
The host driver and the existing Steam Proton installation were not modified.

Validation: the new runner completed `cmd /c ver`, then selected the RTX 3060 Ti in the DLSS helper and received
an OpenYAMM frame. However, its bundled DXVK `v3.1-19-g601930949d111ed0` rejects driver **535.230.02**:

```text
Found device: NVIDIA GeForce RTX 3060 Ti (GA104, Low Hash Rate) (NVIDIA 535.230.2)
Skipping: Device does not support required feature 'khrLoadStoreOpNone' (extension: VK_KHR_load_store_op_none)
DXVK: No adapters found.
```

This is a confirmed graphics-driver compatibility blocker for the updated runner, before neural feature creation.
The helper's guard captures the resulting initialization exception; no neural frames were processed.
Detailed logs are `ge-wine.log`, `ge-helper.log` and `dlssnr_helper_diagnostic_dxgi.log`.
After upgrading the NVIDIA driver and rebooting, rerun the command above with `--diagnostic` to compare.
No rebuild of OpenYAMM or reinstallation of Proton is required for that check.

## Driver 595 retest: successful neural processing

After the user upgraded the driver, `nvidia-smi` confirmed **595.99.02** on the RTX 3060 Ti.
The existing GE-Proton11-7 runner and patched DLL successfully completed this test:

```sh
python3 build-vulkan/dlss-test/check.py mm6 oute3.odm --neural --diagnostic
```

NGX initialization and Vulkan Feature 18 creation both returned `0x1` (success); creation took 339 ms.
The helper reported `neural ready 1280x720`, completed its first NVIDIA optical-flow pass, and finished with
`model_up=1`, `helper_frames=532`, and `layer_frames=531`. No evaluation failure was logged, and feature release
and shutdown also succeeded. The game exited with code 0. This resolves the earlier driver 535 blockers for
this tested combination of GPU, patched DLL and Proton runner.

The captured `build-vulkan/dlss-test/neural-mm6-oute3.png` shows the outdoor scene and HUD rendering.
The run recorded a median 37.2 FPS; this is an isolated smoke check, not a controlled performance or image-quality
comparison. Its full record is `/tmp/openyamm-desktop-neural-mm6-oute3-vg63cz95/run.json`.
The helper log and counters are in `build-vulkan/dlss-test/ge-helper.log` and `neural-status.txt`.
The normal launcher remains unchanged; neural processing is enabled by the separate test command above.

## Live settings window

The GUI was built with the existing desktop Qt **6.9.0** SDK at `/home/pjasicek/qt-6.9-core`.
From the repository root, open it with:

```sh
./tools/run_dlss_settings.sh
```

The wrapper selects the test's `shm.bin`, patched DLL directory and helper log. GUI configuration and saved
profiles live in `build-vulkan/dlss-test/gui-config/`. It supplies the installed DejaVu font directory because
this Qt SDK was built without fontconfig. No system Qt installation is required.

Run the game in another terminal, keeping it open until you close the game window:

```sh
python3 build-vulkan/dlss-test/check.py mm6 oute3.odm --neural --seconds 0
```

Use the GUI's Rendering, Quality, Composition and Inspect tabs for live controls. The supervisor starts the
helper; the GUI's runner selection and **Start helper** button are not wired to this isolated UMU setup.
The **Stop helper** button and closing the settings window request a helper stop through shared memory.
Restart the test command to start it again. The test resets settings at startup; open the GUI after startup
or reload a saved profile to restore your choices.

Desktop validation showed **Helper: running / Active** with readable controls while the standard helper
processed 815 frames and the game exited successfully. Screenshot: `build-vulkan/dlss-test/settings-window.png`.

To rebuild just the GUI:

```sh
mkdir -p build-vulkan/dlss-test/gui
cd build-vulkan/dlss-test/gui
/home/pjasicek/qt-6.9-core/bin/qmake ../../../third_party/DLSS5VKLayer/gui/dlssnr_gui.pro 'LIBS+=-ldl'
make -j12
```

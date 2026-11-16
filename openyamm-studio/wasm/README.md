# The WebAssembly build

`./build.sh wasm` builds the same core and command line with Emscripten into `build-wasm/` (`oymap.js` and
`oymap.wasm`), linked for Node with the host file system (`-sNODERAWFS=1`), so `node build-wasm/oymap.js <command>`
behaves like the native `oymap`. This is the smoke build that keeps the core portable; the worker bindings for the
hosted page come with milestone S5.

The same build also links `oymap_rpc.js` (since S5a1, from S5-0 spike 4's copy): the request list
(`schema/rpc/`) behind one C function, `oymap_call(method, params JSON)` returning the answer JSON (free it with
`oymap_free`), as a Node module (`createOymapCore`). The contract suite runs it beside the native `oymap serve`:
`node schema/rpc/contract/run.mjs --native build/oymap --wasm build-wasm/oymap_rpc.js`.

The browser's worker (S5a4) is the same request list as an ES module for a Web Worker, `oymap_worker.mjs` and
`oymap_worker.wasm` (an in-memory file system the worker fills); the host serves it at `/core/` (`--core-wasm`,
default `build-wasm-s4` or `build-wasm`). Walk mode runs on it in local mode (`web/src/walk/walk.worker.ts`).

**The hosted page's core (S5c).** The same build is the hosted page's whole core (`web/src/hosted/`): one worker
serves every method of the request list without a host. Its file systems: the open projects in memory under
`/p/<key>` (written back after each change to the person's folder through File System Access, or to the origin's
private storage, OPFS), and the asset root at `/a/root`, a read-only Emscripten file system of the page's own
(`web/src/hosted/packfs.ts`) that shows a player's install (its content packs by the release's `index.json`), the
single packages (`engine.zip`, `worlds/<w>.zip`) or a checkout's loose `assets_dev` as the development tree the core
reads. Packages are read by byte range with `FileReaderSync`; only each zip's central directory is kept; stored
entries (cooked textures) are read by range, deflated ones (tables, maps) inflated on first read into a bounded
cache (fflate, shipped with three.js). PhysicsFS needs nothing more in the worker: Emscripten's own
`/home/web_user` is its user folder there. Two exports serve the page: `oymap_unzstd` (a texture's blocks un-framed
by the core's zstd, so no JavaScript zstd) and `oymap_heap` (malloc's live bytes and arena, the memory size and the
largest arena, for the memory budget; built with mimalloc, `-DOYMAP_WASM_MALLOC=mimalloc`, the bytes in its areas'
used blocks and the memory it took). The build also runs under Node (`ENVIRONMENT=worker,node`, NODEFS), so the
contract suite drives this very module: `node schema/rpc/contract/run.mjs --native build/oymap --worker
build-wasm/oymap_worker.mjs`. `session.release` (not exposed) drops what the core keeps of a project: the hosted
worker keeps one map at a time.

**The wasm's memory above native (R8), traced (S5c).** S5-0 measured 346-407 MB for Node wasm builds of dungeons
against 35-69 MB natively. That is not the wasm heap: it is V8 compiling the 9 MB module with its optimizing tier.
Darkmoor's build: `node oymap.js` 362 MB maximum resident, 139 MB with `--liftoff-only` (no optimizing tier), native
73 MB; the module's own memory after the build 81 MB (malloc's arena 67 MB). In the browser worker all 22 projects
build within 64-133 MB of wasm memory (the memory only grows; malloc's live bytes after each project 22-31 MB).

## Toolchain

Emscripten **4.0.10**, pinned (CI: `.github/workflows/studio.yml`). Locally:

```
git clone --depth 1 https://github.com/emscripten-core/emsdk.git openyamm-studio/emsdk   # git-ignored
openyamm-studio/emsdk/emsdk install 4.0.10 && openyamm-studio/emsdk/emsdk activate 4.0.10
```

`build.sh wasm` sources `emsdk/emsdk_env.sh` itself when `emcmake` is not on the path.

## What was found getting here (2026-11-12)

- **Newer Emscripten fails on `bx::Vec3`.** With the release current on 2026-11-12, libc++'s vector calls `swap`
  unqualified and finds both `std::swap` and `bx::swap` for `std::vector<bx::Vec3>` (`game/indoor/IndoorGeometryUtils`).
  4.0.10 does not. Raising the pin needs either a newer bx or the core's own vector type (PLAN.md section 2,
  `core/collision`).
- **Only bx's math is built** (`bx/src/math.cpp`): the rest of bx does not compile without threads under Emscripten
  and is not used.
- **`-fwasm-exceptions` on every target**, the dependencies included (set before they are declared). yaml-cpp throws.
- **`YAML::Emitter` leaves a broken exit handler** (`null function or function signature mismatch` in
  `__funcs_on_exit` when the program ends). Core code writes YAML through `core/CanonicalYaml` only; the old
  metadata and scene serialisers that use the emitter must not be reached from the core.
- **Environment variables**: Emscripten gives the program an environment of its own. `wasm/node_env.pre.js`
  (linked with `--pre-js`) copies the host's `HOME`, `XDG_DATA_HOME` and `OYMAP_*` into it before `main()`, so
  `OYMAP_ASSETS` works as natively.
- Native and wasm outputs are byte-identical for the slice build and for map exports
  (`tests/native_vs_wasm.sh`). `-ffp-contract=off` is set for both.
- **The asset file system did not open** in the wasm core until 2026-11-14 (`PHYSFS_init failed` with "no error"):
  PhysicsFS needs a user directory (`$HOME`, else `getpwuid`, which Emscripten does not answer), and Emscripten's
  `HOME=/home/web_user` does not exist on the host file system that `NODERAWFS` exposes. With `node_env.pre.js`
  passing the host's `HOME`, every command that reads an asset root works under Node, and an outdoor build is read
  back through a mount folder as natively (the in-memory warning, once the one difference between a native and a
  wasm `build.json`, is gone). The browser worker (S5c) needs a `HOME` folder in its own file system.
- Checked again on the night of 2026-11-12 with everything built that day (outdoor terrain, compare, movers, the
  texture layout of moving parts): the slice and the shapes gallery build to the same bytes, as does the
  Ravenshore terrain (`output/studio_s4/ravenshore`) apart from that warning.

## Same bytes on all 22 calibration projects (2026-11-14, S5-0 spike 6 and its follow-up)

- `tests/native_vs_wasm.sh` builds the 22 L4 projects of the studio's and the Xeen briefs
  (`tests/calibration_projects.sh`) with both cores, each from a fresh copy, and compares every output file, the
  JSON report and the project folder after the build: 22 of 22 identical. It needs the real asset root
  (`assets_dev`) and, for the six Xeen projects, `output/studio_play/xeen_root`; with the fixture root it skips them.
- **Undefined behaviour** is where the two standard libraries can answer differently (libstdc++ natively, libc++ in
  wasm): `std::clamp` with crossed bounds gave libstdc++'s upper bound and libc++'s lower one (13 bytes of Erathia).
  `tests/sanitize.sh native` (GCC ASan and UBSan with `_GLIBCXX_ASSERTIONS`) and `tests/sanitize.sh wasm`
  (Emscripten's ASan with libc++'s extensive hardening; slow) build the 22 projects with sanitizers; both must stay
  clean.
- **Math functions**: glibc and musl differ by an ulp on a few percent of inputs to `hypot`, `sin`, `cos`, `tan`,
  `atan2` and `cbrt`; and `std::hypot(x, y, z)` is a different formula in each standard library. The core calls its
  own (`core/CoreMath.h`: `oy::sin`, `oy::hypot` and the rest), musl's sources compiled into it on both targets
  (`third_party/musl_math`). No byte of the 22 changed natively by the switch. Code compiled in place from `game/`
  and `editor/` still calls the C library (`IndoorMovers` `sinf`/`cosf`, `IndoorDaylight` `sinf`,
  `OutdoorPathfindingBuilder` `atan2f`, `SkyState` `cosf`/`powf`, Lua's math library), and `bx::sqrt` differs
  between the targets (S5-0 spike 3); none of them changed a byte of the 22.


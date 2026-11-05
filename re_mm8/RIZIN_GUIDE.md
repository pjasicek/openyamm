# MM8 behavior research with Rizin

Use Rizin as the main tool for examining `mm8_orig/` to establish how the game implements movement, collision,
monster AI, update scheduling and performance shortcuts. Use local reference projects to suggest names and data
layouts, then check the actual MM8 instructions. Implement OpenYAMM behavior in new code; repository reference-code
restrictions still apply.

This guide records hands-on checks on **2026-09-10**, using Rizin **0.10.0**, commit
`c329b50b1ce87e32168f46e8a29d019b747c4117`, installed under `~/.local` from `third_party/rizin/`.
After a system move it was restored on 2026-10-31 from the old disk (`~/.local/bin/rizin`, `librz_*` in
`~/.local/lib/x86_64-linux-gnu`, rz-ghidra in `.../rizin/plugins`; `pdg` works). If `command -v rizin` fails again, the
in-tree build `third_party/rizin/build/binrz/rizin/rizin` (tools beside it in `build/binrz/`) runs without installing.
Commands below run from the **OpenYAMM repository root**, unless explicitly described as interactive commands.
Generated projects and large exports belong in ignored `re_mm8/work/`; preserve useful conclusions as small,
reviewable Markdown notes and annotation scripts next to this guide.
The supplied game directory is also ignored by Git; search it with explicit paths or `rg --no-ignore` when needed.

## First establish which binary you are studying

The directory name `mm8_orig` does **not** mean the executable is unpatched retail code.

**User-selected default for native-engine research: `mm8_orig/MM8-Rel.exe`.** It was verified byte-for-byte
against the game executable extracted from the supplied GOG installer `setup_mm8_2.0.0.13.exe`.
See [GOG installer verification](GOG_INSTALLER_VERIFICATION.md) for hashes, extraction commands and launcher findings.
This establishes GOG-distribution provenance, not identity with an original retail-disc release. The detailed
address tables, annotation script and example projects below remain specific to the previously examined patched
`mm8.exe`; do not apply them to `MM8-Rel.exe` without separately locating and validating the corresponding routines.

New research on the selected **`MM8-Rel.exe`** lives in [Outdoor rendering](OUTDOOR_RENDERING.md): ODM data,
terrain/model visibility, sprite/billboard queues and rasterization, sky, texture loading, mipmaps and verified
optimization techniques for both Direct3D and software rendering.
Its separate [outdoor annotations](mm8_rel_5326d564_outdoor.rz) use original-executable addresses.

[Precipitation and OpenYAMM](WEATHER.md) traces the retained rain implementation, its unresolved activation,
the no-op `SetSnow` event, and the tradeoffs against OpenYAMM's current particles. Its
[weather annotations](mm8_rel_5326d564_weather.rz) target the same original executable.

[Indoor and outdoor lighting](LIGHTING.md) extends that research with light-source and type classification,
room/face selection, hard limits, projected Direct3D light polygons, software shading and cache invalidation.
Its [lighting annotations](mm8_rel_5326d564_lighting.rz) target the same verified original executable.

[Static dungeon light cost](INDOOR_STATIC_LIGHTS.md) follows the indoor map loader, decoration-light registration,
visible-face dispatch and draw-time lighting to distinguish cached source data from baked illumination.

[Decoration placement and wall occlusion](BILLBOARD_OCCLUSION.md) traces native base anchoring, indoor sprite
and wall depth mapping, hardware depth states, and OpenYAMM's pitch-dependent indoor decoration placement.
Its [occlusion annotations](mm8_rel_5326d564_billboard_occlusion.rz) target the same original executable.

[Creature movement indoors and outdoors](CREATURE_MOVEMENT.md) traces actor steering, floor support,
terrain/building transitions, collision sweeps, sector recovery, drop avoidance and bounded retries in that
original executable. Its [movement annotations](mm8_rel_5326d564_creature_movement.rz) distinguish support
tolerances and action timers from the step-height limits in modern reference implementations.

[Indoor spawning and below-floor recovery](INDOOR_SPAWN_RECOVERY.md) traces encounter validation, room lookup,
floor correction for walkers and flyers, and load-time home resets. It records the original's failure cases
and the stronger deterministic placement/save-migration contract needed for TC_1. Its
[spawn/recovery annotations](mm8_rel_5326d564_indoor_spawn_recovery.rz) target the same original executable.

[Actor sounds and OpenYAMM](ACTOR_AUDIO.md) traces attack, hit, death, fidget and wandering vocalizations,
orientation/state gates, audible distance, and channel ownership. It compares local OpenEnroth and OpenYAMM
and records the remaining actionable fixes. Its [audio annotations](mm8_rel_5326d564_actor_audio.rz) target
the same original executable.

[Actor attack timing](ACTOR_ATTACK_TIMING.md) verifies that melee blows, missiles and monster spells happen
when the whole attack sprite animation has elapsed, not on a drawn contact frame.

[Party target selection](PARTY_TARGET_SELECTION.md) checks default monster targeting, party-slot probabilities,
condition exclusions and melee/projectile callers in original MM8, with a separately fingerprinted MM7 comparison.
Its [MM8 annotations](mm8_rel_5326d564_party_targeting.rz) target the same original executable.

[Monsters hit by the party from far away](PARTY_HIT_AGGRO.md) traces what a party hit sets on a monster, why the
outdoor full-AI list ignores it beyond 5632 units, and how far party projectiles fly (lifetime, speed units).
Its [annotations](mm8_rel_5326d564_party_hit_aggro.rz) target the same original executable.

[Party slope climbing](PARTY_SLOPE_CLIMBING.md) traces the party's outdoor and indoor slope rules (terrain slide,
model-face and dungeon-slope responses), GrayFace's `ClimbBetter` byte patch, and the gaps in OpenEnroth and OpenYAMM.

[Potion power](POTION_POWER.md) traces where a potion's power comes from (random treasure, map placement, monster
loot, shops) and how each drink effect uses it, with the MMerge overrides.

[Chest opening and closing sounds](CHEST_AUDIO.md) verifies the original MM8 request for sound 141
(`openchest0101`), the separate trap-explosion path and silent close-button/Escape exit. Its
[chest-audio annotations](mm8_rel_5326d564_chest_audio.rz) target the same original executable.

[Creature inspect portrait](CREATURE_INSPECT.md) traces front-view selection, native-size rendering,
the complete MM8 family offset table, hardware/software clipping and the independent preview animation.
It verifies the copied-AI-state action choice and 128-tick timing, and compares the current atlas preview.
Its [inspect annotations](mm8_rel_5326d564_creature_inspect.rz) target the same original executable.

[Indoor exploration and actor activation](INDOOR_EXPLORATION_AND_ACTIVATION.md) separates the renderer's
current visible sectors, persistent face/outline discovery, per-actor detection and the full/background AI
schedulers. It traces portal detection and explains why unvisited rooms are not universally inert. Its
[activation annotations](mm8_rel_5326d564_indoor_activation.rz) target the same original executable.

[Arena dialogue and encounters](ARENA.md) records native topic 704, difficulty level bands, opponent counts,
spawn positions, completion and rewards, and the shared implementation for the MM6/MM7/MM8 Arena maps.

[Party-defeat resurrection](PARTY_DEFEAT_RESPAWN.md) verifies QBit 93 as the permanent switch from Dagger Wound
Island to Ravenshore on the first Ravenshore visit, records native placement and compares the MMerge/OpenYAMM rule.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `mm8_orig/mm8.exe` | 1,155,072 | `97be86a7597fbd9763f9b4b0ed1f4a7e47c960703fa30857c32daa056b7d403b` |
| `mm8_orig/MM8-Rel.exe` | 1,163,264 | `5326d56459ca74126447bcfd07a8cc85a419663e2281500f0f043f13ffe77a0b` |
| `mm8_orig/MM8patch.dll` | 380,416 | `f89f52281b042d3e421c3ff1d4e7c70589538a90876359c1f4f57e967c27b05d` |

Both EXEs are little-endian x86 PE32 images with preferred base `0x400000`. Their entry points differ:
`mm8.exe` uses `0x4e7d9c`; `MM8-Rel.exe` uses `0x4df52b`. Do not transfer addresses between them by assumption.
PE timestamp and filename alone do not authenticate a retail revision.

In the tested `mm8.exe`, the entry stub calls `LoadLibraryA` with the string `MM8patch.dll` at `0x4e7db2`, then
transfers to `0x4dc82b`. The adjacent patch readme identifies GrayFace patch 2.5.7. Disk disassembly establishes
the loader behavior; it does not establish which hooks are enabled after initialization. Trace the loaded DLL,
configuration and live bytes when a behavior could be patched. DLL export inspection also works; the patch DLL
has 20 named exports, including `DisableHook` and `GetOptions`.

```bash
sha256sum re_mm8/mm8_orig/mm8.exe re_mm8/mm8_orig/MM8-Rel.exe re_mm8/mm8_orig/MM8patch.dll
rz-bin -Ij re_mm8/mm8_orig/mm8.exe
rz-bin -Sj re_mm8/mm8_orig/mm8.exe
rizin -N -q -e scr.color=0 -c 'ie;pd 7 @ entry0;ps @ 0x4e7db2' re_mm8/mm8_orig/mm8.exe
rz-bin -Ej re_mm8/mm8_orig/MM8patch.dll
```

`rz-bin` reports some generic PE symbol/debug flags, but the inspected symbol list contains imports rather than
useful original gameplay function names. Labels such as `fcn.0046b975` are analysis results, not recovered names.

## Start or resume a research session

```bash
command -v rizin rz-bin rz-asm rz-find rz-diff
rizin -v
mkdir -p re_mm8/work
rizin -N -q -e scr.color=0 -c 'aaa;Ps re_mm8/work/mm8-rel-5326d564-base.rzdb' re_mm8/mm8_orig/MM8-Rel.exe
rizin -N -p re_mm8/work/mm8-rel-5326d564-base.rzdb
```

Use this executable and a separate project for new investigations. The patched-binary annotations supplied with
this guide have not been migrated to this target.

### Reproducing the earlier patched-binary probes

The remaining concrete address examples document the earlier `mm8.exe` probes. Use them only for explicit patched
comparisons or reproducing tool checks; independently locate corresponding routines in `MM8-Rel.exe` for new work.

```bash
rizin -N -q -e scr.color=0 -c 'aaa;Ps re_mm8/work/mm8-97be86a7-base.rzdb' re_mm8/mm8_orig/mm8.exe
rizin -N -p re_mm8/work/mm8-97be86a7-base.rzdb
```

Initial `aaa` analysis took **7.18 seconds**, used about **163 MiB peak RSS**, and found **2,452 candidate functions**
in the tested installation before the Ghidra plugin was added. These are analysis workload measurements, not game
performance measurements. Counts and names may change with versions, settings, plugins and later manual analysis.

After checking the hash, load the supplied reference annotations and save a separate working project:

```bash
rizin -N -q -e scr.color=0 -p re_mm8/work/mm8-97be86a7-base.rzdb \
  -i re_mm8/mm8_97be86a7.rz -c 'Ps re_mm8/work/mm8-97be86a7-notes.rzdb'
rizin -N -p re_mm8/work/mm8-97be86a7-notes.rzdb
```

`-N` disables user startup settings/scripts while allowing installed plugins. `-NN` also disables plugin loading,
so it is unsuitable when using the Ghidra plugin. `-q -c` performs batch commands and exits. Static opening without
`-w` keeps the input file read-only; annotations and project saves modify the analysis database, not the EXE.

Project save/reopen was tested with a renamed function, a comment and a small C structure definition. Keep the
binary available at its recorded path. A project is a cache of analysis, not a substitute for the input hash or
an evidence note. Do not use `Poo` to transplant analysis onto a different executable revision.

The local Rizin build uses Meson 1.11.2 and Ninja 1.10.0. `~/.local/bin` is already in this user's shell PATH;
`hash -r` clears a terminal's cached older executable. To rebuild the already configured Rizin checkout, use
`meson compile -C third_party/rizin/build -j 25` and `meson install -C third_party/rizin/build`.
Rebuild the Ghidra plugin against the same installation after a Rizin ABI change.

## Capability map

The installed tool's `?` help is authoritative for syntax. The [official handbook](https://book.rizin.re/) provides
background, but older handbook examples and radare2 commands can differ from Rizin 0.10.

| Capability | Useful commands or tools | Status and MM8 use |
| --- | --- | --- |
| PE inspection | `iI`, `iS`, `ie`, `ii`, `is`, `il`, `rz-bin` | Tested headers, sections, entries, imports, symbols and DLL exports. |
| Strings and resources | `izj`, `izzj`, `ps`, `psw`, `rz-bin -zj` | Tested normal strings and direct string reads. Raw scanning can expose `.text` strings omitted from normal scans. |
| Disassembly and instruction semantics | `pd`, `pdf`, `pdj`, `pdfj`, `aoj`, `rz-asm` | Tested x86 decode, function listings, operands and lifted semantics. |
| Function discovery | `aa`, `aaa`, `aF`, `af`, `afij`, `aflj` | Tested broad discovery. Inspect boundaries before trusting a function. `aF` is nonrecursive; `aaaa` is experimental. |
| References | `axtj`, `axfj`, `afxj` | Tested incoming calls and global data references. Missing xrefs do not prove a target is unused. |
| Control flow and calls | `afbj`, `agf json`, `agf dot`, `agc json` | Tested a 19-case switch, block JSON, DOT export and a local call graph. |
| Search | `/xj`, `/v4j`, `/s?`, `rz-find` | Tested instruction byte search, 32-bit address search and a monster-table filename search. |
| Types and annotations | `td`, `to`, `tsj`, `afs`, `afvlj`, `afn`, `CC`, `f` | Tested structure creation, variables, renaming, comments and project persistence. Inferred types need validation. |
| Decompilation | `pdg`, `pdgo`, `pdgj` via rz-ghidra | See the plugin section below. Pseudocode is a reading aid; verify important operations in assembly. |
| Emulation | `aei`/`aes`/`arj` (ESIL), `aezi`/`aezs`/`aezvj` (RzIL) | Both tested on MM8 instructions. A signed-immediate discrepancy was found; see below. |
| Binary comparison | `rz-diff -t imports`, `-t functions`, `-t graphs`, `-t command` | Import comparison tested. Structural function matching is available but was not validated across these EXEs. |
| Library recognition | `Fl`, `Fa`, `Fs`, `Fc` | FLIRT interface present; `Fl` listed no signature databases. Do not claim CRT recognition is installed. |
| Classes and vtables | `av?`, `ac?` | Available inspection commands; automatic MM8 C++ class recovery not validated. |
| Automation | JSON commands, `-i` scripts, `-0` pipe protocol, rzpipe, C APIs | JSON subprocess and script workflows tested. Python rzpipe is an optional separate dependency. |
| Interactive inspection | `V`, `VV`, `agf interactive`; Cutter frontend | Terminal visual modes are available; desktop interaction/Cutter was not tested or installed here. |
| Debugging | `db`, `dc`, `ds`, `dso`, `dr`, `dm`, `dbt`, `dt?`, `Ld`, `Lo` | Backend inventory inspected; MM8 was not launched or attached during this guide's static probes. |
| Remote and dump inspection | `gdb://`, `winedbg://`, `winkd://`, PE/minidump readers | Backend-dependent. Presence in the plugin list is not a working MM8 session. |
| Other framework tools | `rz-hash`, `rz-ax`, `rz-run`, `rz-sign`, `rz-gg`; `w?`, `/R?` | Hashing, conversion, execution profiles, signatures, code generation, patching and gadget searches. Secondary to this workflow; no EXE patches applied. |

The [plugin model](https://book.rizin.re/src/plugins/intro.html) also allows adding file formats, architectures,
analysis, IO, debugger, language and other functionality. Enumerate the actual installation with `L?`, `Lc`,
`La`, `Li`, `Ld`, `Lo` and each standalone tool's `-h`; do not assume every optional component is installed.

### Syntax traps observed in this installation

| Older/common example | Working Rizin 0.10 form |
| --- | --- |
| `agfj`, `agfd` | `agf json`, `agf dot` |
| `afvj` | `afvlj` |
| `psz` | `ps` (null-terminated by default) |
| Bare `/ text` | Use the appropriate `/s?` string-search subcommand or `rz-find -s text FILE`. |
| Bare `z?` signature workflow | `F?` for FLIRT management |
| `f name @ address` where a flag already exists | `f+ name @ address` adds another label without replacing it. |

Use `command?` to confirm arguments. Rizin can return shell exit status **0 despite an internal command error**.
Inspect stderr and validate JSON/output, not just the exit code. A command error can prevent later commands in the
same batch from running. Quote comment/type text containing semicolons, for example:

```text
CC "Reference-derived name; not the full AI scheduler" @ 0x457060
```

## Addressing, references and export recipes

Rizin normally seeks using **virtual addresses** in PE mode. `rz-find` reports **file offsets**. For a file-backed
section, convert with `file_offset = section.paddr + (VA - section.vaddr)` and check its raw extent first.
For this EXE, `monsters.txt` is at VA `0x4f85a8`, file offset `0xf85a8`; its discovered referring instruction is
`0x45285c`. Import entries such as `0x4e82a0` are IAT slots, not Windows function bodies.

The `.data` section has only 94,208 raw bytes but 11,632,640 virtual bytes. Globals in its zero-initialized tail
represent runtime state: opening the EXE does not populate monsters, map geometry or timer values. Code/data
references remain useful even when the pointed-to data does not exist in the disk image.

```bash
rz-bin -ij re_mm8/mm8_orig/mm8.exe > re_mm8/work/imports.json
rz-bin -zj re_mm8/mm8_orig/mm8.exe > re_mm8/work/strings.json
rz-find -s monsters.txt re_mm8/mm8_orig/mm8.exe
rizin -N -q -e scr.color=0 -p re_mm8/work/mm8-97be86a7-base.rzdb \
  -c 'axtj @ 0x4f85a8' > re_mm8/work/monster-table-xrefs.json
rizin -N -q -e scr.color=0 -p re_mm8/work/mm8-97be86a7-base.rzdb \
  -c 'agf dot @ 0x457060' > re_mm8/work/monster-graphics.dot
rizin -N -q -e scr.color=0 -p re_mm8/work/mm8-97be86a7-base.rzdb \
  -c 'e search.in=io.maps.x;/xj 0fbf91b8000000' > re_mm8/work/state-read-hits.json
```

The byte search found the instruction at `0x457060`. A `/v4j 0x61c540` search finds encoded references to the monster
array; hits may point **inside instructions** at the immediate/displacement, unlike `axtj` instruction addresses.
Exact-base xrefs omit accesses using base-plus-field constants, interior pointers or registers. Search related
field addresses and inspect callers instead of treating an xref count as complete usage coverage.

In an interactive session:

```text
s 0x46b975
afij
pdf
afbj
afvlj
axtj @ 0x46b975
pd 12 @ 0x44d0a4
agc json
aoj 1 @ 0x46b981
```

`@` temporarily changes seek for one command. `afij`/`afbj` are more useful than assuming a function covers every
address between `offset` and `offset + size`: broad analysis produced overlapping candidates, including one at
`0x43c227` spanning 455,820 bytes. Large functions, implausible signatures, strange self-edges and switch metadata
need manual review. On a fresh disposable session, `aF @ ADDRESS` can analyze a known start without recursive
call expansion. Use `af-`, `afu`, `afb?` only when the bytes support a boundary correction, and save separately.

## Tested MM8 starting points

The semantic names below come from local
[MMExtension common structures](../reference/MMExtension/Scripts/Structs/01%20common%20structs.lua), especially
lines 150, 317–342 and 1383–1481. `mmv` lists MM6, MM7, MM8 alternatives; choose the **third** entry.
Their MM8 addresses were checked against this EXE's disassembly/xrefs. They are leads with corroboration, not
proof that all behavior inside a function has been reconstructed.

| VA | Reference meaning | Observed starting evidence |
| --- | --- | --- |
| `0x46b975` | Indoor floor query | 1,499-byte candidate, 69 blocks, 9 incoming call references. Reads room-indexed geometry. |
| `0x46bf50` | Outdoor floor query | 1,090-byte candidate, 59 blocks, 13 incoming calls; calls `0x481e19`. |
| `0x481e19` | Outdoor ground height | Reference address also reached by the outdoor floor query. |
| `0x4980ba` | Room containing a point | 974-byte candidate, 52 blocks; useful for sector/room transitions. |
| `0x457060` | Monster graphic-state update | 172-byte candidate, 15 blocks, 19-case table, 33 incoming CALL/CODE refs. |
| `0x425203` | Choose target player | MMExtension address; inspect before assuming a complete target-selection policy. |
| `0x61c540` | Monster array base | 113 discovered exact-base data references. Reference layout has stride `0x3cc`. |
| `0x692fb0` | Monster count | 110 discovered references; follow loop bounds and index increments. |
| `0x51d354` | Game logic `TimeDelta` | 35 discovered references. `TimeStruct1` at `0x51d338`, field offset 28. |
| `0x51d32c` | View `TimeDelta2` | Second reference timer at `0x51d310`, field offset 28. |
| `0x5e3000` | Frame counter | Reference-derived address; establish which update loop advances it. |
| `0x4e82a0` | `timeGetTime` IAT slot | 11 discovered CALL/DATA references. |
| `0x4e8070` / `0x4e8074` | Performance counter / frequency IAT slots | `0x4aa654` calls frequency and loads the counter pointer; runtime use needs tracing. |

Timer provenance: [MMExtension offsets](../reference/MMExtension/Scripts/Core/offsets.lua), MM8 block around line 99,
and [game structure fields](../reference/MMExtension/Scripts/Structs/00%20structs.lua), around line 461.
Avoid assuming that a `TimeDelta` integer is milliseconds; recover conversion/scaling from producer and consumers.

### Worked example: state dispatch, rather than guessing from a function name

At `0x457060`, the code reads a **signed 16-bit** field at `ECX + 0xb8`, bounds-checks against 18, then jumps through
19 dword entries at `0x45710c`. Several branches write a 16-bit field at `ECX + 0xba`. This matches MMExtension's
MM8 `MapMonster.AIState` and `GraphicState` offsets (`0xa0/0xa2 + 0x18`). The pointer arrives in ECX even though the
automatic signature prints an unhelpful no-argument/cdecl function.

The table entries for states 6 and 7 both target `0x4570a9`, which writes graphic state 1. MMExtension's
[state constants](../reference/MMExtension/Scripts/Core/ConstAndBits.lua) name those input states Pursue and Flee.
This supports the narrow conclusion that these states share an animation-state assignment here. It does **not**
establish their path selection, steering or update cadence. The incoming callers are where to continue that study.

### Collision and pathing investigation

Start with callers of the indoor/outdoor floor queries, room lookup and monster movement fields. Track radius,
height, position, velocity, room index, candidate face lists, normals, slope tests, portal transitions and response
to a rejected move. Distinguish terrain height, indoor floor selection, swept collision, LOS and steering: a floor
query alone does not reconstruct movement collision.

Reference MM8 monster offsets include radius `0x90`, height `0x92`, XYZ `0x96/0x98/0x9a`, velocity XYZ
`0x9c/0x9e/0xa0`, room `0xa6`, action length `0xa8`, AI state `0xb8`, and elapsed action step `0xc0`.
Validate access width, signedness and `0x3cc` stride in each candidate routine before attaching a full structure.

For pathing, follow decisions that write direction/velocity and switch between pursue/flee/stand. Look for obstacle
tests, alternate headings, stuck counters, search queues and distance thresholds; record what actually exists.
Do not assume native A*. The local `reference/mmmerge/Scripts/Global/MonsterPathfinding.lua` explicitly uses a
separate Pathfinder DLL and improved-pathfinding option. It is a mod behavior reference, not proof of original
MM8 pathfinding. Likewise, OpenEnroth's MM7 addresses are not MM8 addresses.

### AI scheduling and optimization investigation

Intersect callers of graphic-state updates with references to the monster array/count, timer deltas and frame
counter. Follow the loop that advances action time and chooses another action. Record active/inactive tests,
distance bands, visibility/room gates, per-frame budgets, turn-based branches and pause conditions. Distinguish
animation updates, physical movement, target selection and expensive decision updates; they may have different
schedules.

For performance shortcuts, inspect loop bounds, spatial candidate reduction, cached results, fixed-point shifts,
integer distance approximations and early exits. A compiler-generated shift or a performance-counter import does
not alone prove a deliberate gameplay optimization. Static structure suggests cost; measuring frequency and
wall-clock impact requires an actual runtime experiment with recorded map, party position and monster population.

## Ghidra decompiler and Sleigh: installed and tested

The source checkout is `third_party/rz-ghidra/`, branch `dev`, pinned here by the tested commit
`26b6130f310e0fa8027bdfacba65079dbd448e63`. Its Ghidra submodule is
`3e5d774389b3c4ff1c089ddf822f071c10f548a8`; pugixml is `fdf02957533645069bbea7cd2ed85a3014b42cf3`.
It was built in Release mode against the installed Rizin, with the decompiler and Sleigh plugins enabled and
Cutter integration disabled. The plugin uses Ghidra's C++ decompiler; a separate Ghidra GUI or Java installation
is unnecessary. Rizin and plugin revisions must be compatible; the
[upstream compatibility guidance](https://github.com/rizinorg/rz-ghidra#versioning-and-rizin-compatibility)
pairs development branches and specifies release compatibility tags. Do not independently upgrade either side
and assume ABI compatibility.

Installed files:

- `~/.local/lib/x86_64-linux-gnu/rizin/plugins/core_ghidra.so`
- `~/.local/lib/x86_64-linux-gnu/rizin/plugins/asm_ghidra.so`
- `~/.local/lib/x86_64-linux-gnu/rizin/plugins/analysis_ghidra.so`
- Sleigh data in `~/.local/lib/x86_64-linux-gnu/rizin/plugins/rz_ghidra_sleigh/`

For rebuilding the existing checkout:

```bash
cmake -S third_party/rz-ghidra -B third_party/rz-ghidra/build \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$HOME/.local" -DCMAKE_PREFIX_PATH="$HOME/.local"
cmake --build third_party/rz-ghidra/build -j 25
cmake --install third_party/rz-ghidra/build
```

For initial recreation elsewhere, clone `https://github.com/rizinorg/rz-ghidra.git` into that directory, check out
the recorded commit, and run `git submodule update --init --recursive` there before building. The install step is
required to place both shared libraries and language specifications where Rizin finds them. Keep builds in
`third_party/rz-ghidra/build`; no OpenYAMM build integration is required.

Verified checks and exports:

```bash
rizin -N -q -e scr.color=0 -c 'Lc;pdg?;pdgss;e ghidra.sleighhome' re_mm8/mm8_orig/mm8.exe
rizin -N -q -e scr.color=0 -p re_mm8/work/mm8-97be86a7-base.rzdb \
  -c 'pdg @ 0x457060' > re_mm8/work/monster-graphics.c.txt
rizin -N -q -e scr.color=0 -p re_mm8/work/mm8-97be86a7-base.rzdb \
  -c 'pdgo @ 0x46b975' > re_mm8/work/indoor-floor-offsets.txt
rizin -N -q -e scr.color=0 -p re_mm8/work/mm8-97be86a7-base.rzdb \
  -c 'pdgj @ 0x46bf50' > re_mm8/work/outdoor-floor-decompile.json
rizin -N -q -e scr.color=0 -c 'pdgsd 1 @ 0x4aa667' re_mm8/mm8_orig/mm8.exe
```

`Lc` lists `ghidra`; `pdgss` selects `x86:LE:32:default:windows`. Decompilation of `0x457060`, `0x46b975` and
`0x46bf50` succeeded without stderr diagnostics, taking approximately 0.7 seconds per subprocess including project
loading. `pdgo` provides address-linked pseudocode; `pdgj` returns an object with `code` and `annotations`.
The state routine's 19-case dispatch is clearly expressed, including states 6/7 assigning graphic state 1.
The indoor query exposes candidate iteration and XY bounds comparisons, making focused assembly review easier.

Decompiler output still contains unresolved types/register inputs (for example `in_ECX`, `in_EDX`, `extraout_ECX`).
Do not translate these literally into an implementation. Recover the calling convention, structure fields and
callee effects from instructions and callers. Fix justified analysis metadata in a separate project, then rerun
decompilation. Pseudocode cannot prove source-level types, original names, runtime frequencies or unreachable paths.

`pdgsd` prints Ghidra Sleigh disassembly and p-code **without switching the session's default analysis backend**.
For `83 ce ff`, it correctly shows `ESI = INT_OR ESI, 0xffffffff`; this corroborates the emulation limitation below.
`pdga` is available to switch to Sleigh-backed analysis/disassembly, but that changes analysis behavior and was not
used to generate the baseline. Compare backends in separate projects. Installing the plugin alone does not fix
the default x86 ESIL/RzIL behavior. `pdg*` adds decompiler output as comments; prefer targeted annotations and exports
to avoid filling the project with regenerated text.

## Automation for agents

Use JSON to filter before printing. `rz-bin -ij` returns an object containing `imports`; `aflj` and `axtj` return
arrays. Graph JSON is a graph object. Rizin search JSON uses `address`, while xrefs use `from`/`to`.

This standard-library example needs no rzpipe package and reads a saved project:

```python
import json
import subprocess

def query(command):
    result = subprocess.run(
        ["rizin", "-N", "-q", "-e", "scr.color=0",
         "-p", "re_mm8/work/mm8-97be86a7-base.rzdb", "-c", command],
        check=True, capture_output=True, text=True, timeout=30,
    )
    if "ERROR:" in result.stderr:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)

for xref in query("axtj @ 0x46b975"):
    print(hex(xref["from"]), xref["type"])
```

For many queries, keep one session open through [rzpipe](https://github.com/rizinorg/rz-pipe) (`cmd`/`cmdj`) or the
NUL-delimited `rizin -0` protocol instead of repeatedly loading the project. A `.rz` script via `-i` works well for
repeatable annotations. Never use untrusted binary strings as Rizin or shell command text; pass explicit arguments
and keep comments quoted. Keep raw exports out of the agent context until filtered to the question at hand.

## Emulation: tested support and a concrete limitation

Both emulators correctly stepped `xor ecx,ecx` at `0x46b997` with initial ECX 123, producing ECX 0 and PC `0x46b999`:

```bash
rizin -N -q -e scr.color=0 -c 's 0x46b997;aei;ar ecx=123;aeip;aes;arj' re_mm8/mm8_orig/mm8.exe
rizin -N -q -e scr.color=0 -c 's 0x46b997;aezi;aezv ecx 123;aezs;aezvj' re_mm8/mm8_orig/mm8.exe
```

However, `83 ce ff` at `0x4aa667` is decoded as `or esi,0xffffffff`, confirmed with GNU objdump. With ESI initially
zero, **both ESIL and RzIL produced `0x000000ff`**, rather than the architectural `0xffffffff`. `aoj` exposes the
discrepancy: ESIL uses 255 and RzIL zero-extends the 8-bit operand. This is an observed limitation of the tested
default x86 analysis backend, not MM8 behavior. Reproduce after tool upgrades before assuming it is fixed:

```bash
rizin -N -q -e scr.color=0 -c 's 0x4aa667;aei;ar esi=0;aeip;aes;arj' re_mm8/mm8_orig/mm8.exe
rizin -N -q -e scr.color=0 -c 's 0x4aa667;aezi;aezs;aezvj' re_mm8/mm8_orig/mm8.exe
objdump -d -Mintel --start-address=0x4aa667 --stop-address=0x4aa66a re_mm8/mm8_orig/mm8.exe
```

Emulation also lacks the running game's populated globals, Windows API behavior, allocator state and patch hooks.
Use it for bounded, checked instruction experiments with explicit input state; never equate whole-function
emulation over the disk image with a faithful MM8 execution. See the
[official emulation overview](https://book.rizin.re/src/analysis/emulation.html) for the broader model.

## Comparing versions and patches

```bash
rz-diff -C -t imports re_mm8/mm8_orig/MM8-Rel.exe re_mm8/mm8_orig/mm8.exe
```

The tested import diff shows `GetEnvironmentVariableA` and `GetKeyState` added in `mm8.exe`. The diff tool also
emitted incomplete-buffer-read diagnostics on these inputs. Separate `rz-bin -ij` exports completed without
diagnostics and confirmed those two additions, no removals, and 255 versus 253 imports. Confirm diff results this
way when the tool reports read errors. A changed import list is not an account of all code changes.

For code, locate corresponding routines independently in each binary, then compare their instructions, control
flow, constants and callers. `rz-diff -h` describes function/graph/command comparison modes. Runtime patches need
a second comparison between disk bytes and the loaded process; two disk EXEs cannot reveal all DLL-applied hooks.

## Runtime debugging and measurements: available, not validated on MM8 here

Static PE analysis works directly on Linux. `rizin -d mm8.exe` on Linux is not automatically a Windows debugger.
This installation lists native, GDB, IO and WinKD debug backends, plus a `winedbg://` IO plugin. The latter spawns
`winedbg` and parses its prompt/register text; this was confirmed in the
[local implementation](../third_party/rizin/librz/io/p/io_winedbg.c). Its existence does not establish compatibility
with the installed Wine or a functioning MM8 session.

For a future live experiment, run a copied game directory and separate Wine prefix or use a Windows debugger
environment. Preserve the original saves/configuration. First prove attachment, x86 registers, module bases and
memory reads. Then try breakpoints/stepping with `db?`, `dc?`, `ds?`, `dso?`, `dr?`, `dm?`, `dbt?` and `dt?`.
GDB-remote support requires a compatible server; WinKD is a distinct Windows kernel debugging path, not a generic
replacement for Windows user-process attachment.

Rebase each static address using `runtime_module_base + (static_VA - preferred_base)`. Compare instruction bytes
after patch DLL initialization. Sample monster state/position, timer deltas and relevant loop counters at controlled
points. Count calls per simulation tick before claiming an AI update rate. Breakpoint/trace overhead distorts timing;
record the instrumentation and separate behavior counts from performance measurements. Watchpoints and reverse
execution depend on the selected backend and were not tested here.

## Evidence to leave for the next agent

Each behavioral finding should record:

1. Question, input path/full hash, tool/plugin versions, settings and analysis commands.
2. Module, preferred VA/RVA, function start and relevant instruction/basic-block addresses.
3. Observed reads/writes, branches, widths, signedness, constants and calling convention evidence.
4. Reference-derived names/layouts with source path and line, explicitly separated from binary observations.
5. Interpretation and confidence; unresolved callers, indirect edges, patches and alternative explanations.
6. A minimal reproduction or runtime scenario when needed, and the intended OpenYAMM behavior/test consequence.

Save concise notes and reusable annotations. Avoid committing full generated disassemblies, private game binaries,
large project databases or noisy logs as documentation. Recheck binary hashes after work. This guide's static tests
did not execute MM8 or establish complete pathfinding, collision-response or AI-scheduling algorithms.

Final setup validation passed 16 focused analysis/decompiler checks, annotation and type/comment project
persistence, and local documentation links. The three fingerprinted input files retained their original hashes.
The local validation report is `work/validation.json`; project caches and decompiler exports are also retained in
`work/` for this workspace, but are disposable and not required to reproduce the documented commands.

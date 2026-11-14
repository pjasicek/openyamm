# Map Studio S5: the browser editor (design for review)

Status: 2026-11-14, a draft written to be criticised before any S5 code exists. The user: "we CANNOT go blindly into
it; the foundation we pick (library lists, architecture, flows) will be there for the lifetime of the product". No S5
code is written until other sessions have reviewed this and the user has decided the questions of section 6.2
(HANDOFF.md, status of 11:56).

**Revision 2 (2026-11-14, later):** the first review, [S5_REVIEW_A7.md](S5_REVIEW_A7.md) (session openyamm-a7), is
taken in. Its verdict was "go for S5-0 once seven changes are in the document; no go for S5a yet". The seven changes
and the conditions on the decisions are made below; section 0.5 lists each point, what changed and where, and the
places where this document keeps a different view and why. S5a still waits for S5-0's record. The review's second
look at revision 2 (its section 5: go for S5-0, five small points and four smaller ones) is taken in as well; its
rows are at the end of 0.5's table.

**Revision 3 (2026-11-14, evening):** the user answered section 6.3's open questions to session openyamm-a7: "Do what
you recommend. In the end I imagine that a lot of people will want to also make the dungeons and terrains etc. by hand
entirely. Not sure if that's relevant. And some will use agents to do the base and finishing touches by hand." The
review's section 6 turns that into changes, taken in here: 6.3 settled as recommended; two more kinds of people (1.3
F5, F6) with exit tests in S5b1 and S5b2 (6.4); a mechanism for R5 in S5b1 (2.8); D15 extended for land made by hand
(3.18, 6.2, the user's decisions at the end). Review A7's four points on S5-0 spike 7 (schema forms,
`output/s5_spikes/7_forms/REPORT.md`) are taken in with it (2.3, 2.4.2, 3.8, 3.18, 6.4). Their rows are the last ones
of 0.5's table.

**Revision 3.1 (2026-11-14, evening):** review A7 agreed with revision 3's three additions (the smooth reservation as
written) and asked for small fixes: a person can set the hand-edit mark ("Protect this project"); "missing history
counts as a person's" only for the whole-file notice; undo leaves the mark, and the meaning of its `revision` field
(2.7, 2.8, F6); and a mechanical check of what the outdoor lowering reads (3.8, 2.4.2, 6.4 S5b2). Rows at the end of
0.5's table.

**Revision 4 (2026-11-14, night): the S5-0 spikes taken in.** All seven spikes reported (`output/s5_spikes/*/REPORT.md`)
and their record is [S5.md](S5.md): S5-0's exit criteria are met. No decision of 6.2 changes; D2, D5, D6 and D7 hold as
measured. What changes is below the decisions: the indoor commit budget holds only on three conditions (parsed table
lookups kept per asset root, one validation per edit, schemas of changed files only); the 3D view after a commit comes
from the edit's own lowering, not a dry build; the outdoor budgets are set (1.5 s for S5a and S5b1, 500 ms for S5b2
with land kept up to the peaks and the scene write out of the commit); ids are unique per file; the walk and the core
use their own trigonometry; the risk to byte identity is undefined behaviour answered differently by libstdc++ and
libc++, guarded by a sanitizer job and the 22-project comparison in CI; CPU BC decoding is dropped; the schema lint
lands early with today's 1 208 issues as its allow list. Section 0.6 lists every change and where it was made. Two
checks stay open (S5.md, "Still open"): the user's hand check of `F5` and `Ctrl K`, and the indoor 300 ms on a quiet
machine.

**Built from:** PLAN.md (every section), README.md, S0.md to S3.md, EDITOR_RETIREMENT.md, HANDOFF.md, FOR_THE_USER.md,
CALIBRATION.md, REBUILD_PROCEDURE.md, OUTDOOR_REBUILD_PROCEDURE.md, TOWN_FEEL.md, research/ (all four),
design_page.html (revision 4: text, the mockup code and its key table), `openyamm-studio/` (README, `host/`, `cli/`,
`core/` headers, `schema/`, `wasm/README.md`, the CI workflow), `editor/`, the game's debug console and
`tools/run_game.sh`. **Not read:** the published design artifact (claude.ai/artifact/SBUwCHsj81N975vCpEbYJX): the
artifact tool of this session reported it as not found or not shared. Everything said here about the design page
comes from `design_page.html`, its source, which README.md names as such; if the artifact differs, it was not seen.

**Measured for this document** (on copies in a scratch folder, not on the projects): `oymap validate` and
`oymap build` times and memory on three rebuilds, face counts of the largest shipped maps, schema sizes, asset sizes.
Appendix C lists them.

**Wireframes:** [s5_mockups/wireframes.html](s5_mockups/wireframes.html), W1 to W7 (open in a browser; W7, pins from the
game, added in revision 2). The design page's own mockups are named here by their element id (`mock-anatomy`,
`mock-gw-board`, ...); open `design_page.html` to see them. Section 3 also has ASCII wireframes so this file stands
alone.

**Labels used throughout:** **[P]** the prepared material says it (the source is in appendix A), **[N]** new in this
document (a proposal to be criticised), **[C]** the prepared material contradicts itself or the code (appendix B).

Sections: 0 summary, decisions, the review taken in (0.5) and the spikes taken in (0.6); 1 goals, users and their
flows; 2 architecture; 3 the UI; 4 libraries and technologies; 5 workflows in detail; 6 risks, decisions, open
questions and phases; 7 appendices (A: every requirement to its source; B: contradictions; C: numbers).

---

## 0. Summary

### 0.1 What S5 is (PLAN.md section 12) [P]

| Part | Contents | Accepted when |
|---|---|---|
| S5 (a) | Local mode view and review: web app shell, plan and 3D views, walk mode, flow graph view, pins, live pairing | You walk the calibration and held-out maps in the browser, pin one, and an agent resolves the pins live |
| S5 (b) | Authoring UI over the operations of S2 to S4: stage bar, tools, inspector, Wire stage | You rebuild one room wing and one town block by hand |
| S5 (c) | Hosted mode with the wasm core and the asset plan of PLAN section 9 | The hosted page opens a player's install, stays inside its memory budget and builds the slice dungeon byte-identical to the native build |

S5 is sized XL. It comes after S4 on purpose: "the UI comes after the operations it drives have made real maps"
(PLAN section 13). S4's exit criteria were met on 2026-11-14 (HANDOFF.md).

### 0.2 The state S5 starts from (facts, 2026-11-14)

- **Maps exist and are reviewed by playing them.** Sixteen shipped maps are rebuilt as projects (ten dungeons, six
  outdoor), and six new maps were built from briefs (XD-01 to XD-05, X1 Vertigo Meadows). The user reviews by playing
  them in the game from `output/studio_play/PLAY.md`, sending words, `loc` lines (the game's console command that
  prints `map=... position=(x, y, z) heading_yaw_units=... yaw_radians=... pitch_degrees=...`) and screenshots; the
  lead turns poses into screenshot tours (`output/studio_cal/xd01/user_walk1/tour.yml`), traces each fault and sends it
  to an agent. Static review pages (`output/studio_review/index.html`, written by `calibration/review_page.py`) show
  renders and comparisons.
- **Agents author by writing YAML**, often through generator scripts kept beside the project
  (`output/studio_cal/x1/tools/gen.py`, `town.py`, `dress.py`; Darkmoor's `L4/gen/run.sh` with `overrides.py`), and
  run the `oymap` command line by the procedures. The MCP host (fifteen tools) exists and was evaluated, but the
  rebuild rounds use the command line.
- **The vocabulary is large and grows daily.** The JSON Schemas hold about 1 860 properties (sketch.yml 914,
  plan.yml 268, objects.yml 263, rooms.yml 202, project.yml 76, common 73, wiring.yml 40, atmosphere.yml 40). The unit
  suite went from 237 to 321 cases in a day of code batches. Projects reach 4 219 lines of `rooms.yml` (Castle
  Darkmoor) and 5 767 lines of `sketch.yml` (Erathia).
- **Operations cover part of it.** `oymap edit` has four generic operations (`add`, `set`, `remove`, `set_value`)
  over 29 collections in `objects.yml`, `wiring.yml`, `rooms.yml`, `plan.yml`, `project.yml` and `review/pins.yml`.
  **No collection of `sketch.yml`** (structures, roads, scatter, areas, ground, actors, events, heights) is one: the
  outdoor maps were made by writing files. PLAN section 5's named operations (`room.add`, `door.place`,
  `terrain.raise`, `road.add`, ...) and its `schema/ops/` catalogue do not exist **[C]**. (S5-0, spike 4: an id may
  appear in two files, `room:entry` in `plan.yml` and `rooms.yml`, and `oymap edit` took the first; since the
  twenty-third merge ids are unique per file, and `set` and `remove` take a `file` where an id is in more than one.)
- **The core service is stateless and serial.** `oymap serve` answers `run {command, args}` with the command's
  stdout and stderr, one request at a time, and loads everything again for each call. `oymap validate` takes 0.2 to
  1.3 s and `oymap build` 0.46 to 2.1 s on the rebuilds measured; `map_edit` validates before and after, so one edit
  of New Sorpigal costs about 2.6 s. (Review A7's own runs differ; appendix C has both.)
- **Validation is the lowering, and an issue is an issue.** `validateProject()` (`core/IndoorBuild.cpp:1578`) runs
  the schemas and then lowers the whole project; `oymap build` builds only when the issue list is empty
  (`cli/Commands.cpp:803`); a `ProjectIssue` (`core/Project.h`) has a file, a path, a message and a code, and **no
  severity** (only `audit` findings have one). [Review A7 1.2, checked]
- **The revision covers every project file, pins and the id lock included.** `projectFileKinds()`
  (`core/Project.cpp:21`) lists `review/pins.yml` and `ids.lock.yml` beside the source files; `projectRevision()`
  (`core/Ops.cpp:860`) hashes every file of that list (FNV-1a, 12 hex digits); every build that changes the lock
  rewrites the project's `ids.lock.yml` (`core/IndoorBuild.cpp:1878`, `core/OutdoorBuild.cpp:1899`), and the next
  read records that change as a history entry of author `build` (`core/Ops.cpp:424`), undoable like any other.
  [Review A7 1.1, checked] **An indoor build drops the lock entries of ids the project no longer has**
  (`core/IndoorLowering.cpp:20745`, "The lock forgets what the project no longer has": events, doors, a door's second
  leaf, containers, cogs, map variables, lights, sounds; written so that a project that renamed its variables would
  not run out of the 75 a map has); an outdoor build keeps every entry it has given. [Review A7 5 point 1, checked]
- **History is a cursor over whole-file snapshots.** Each entry keeps the before and after text of every changed file;
  `undo` moves a cursor and restores files (`core/Ops.cpp`, `cursor`, `undone`). One edit of Darkmoor's rooms wrote
  330 KB of history (review A7).
- **The wasm build works for project files only.** It builds byte-identical BLV and scene files, but PhysicsFS does
  not start under Emscripten, so every command that reads an asset root fails there (`wasm/README.md`). Byte identity
  is checked on two example projects only (`tests/native_vs_wasm.sh`: `gatehouse_cellars`, `shapes_gallery`); **no
  outdoor project has ever been built in wasm**, and roofs, rounds and domes use trigonometry from two different libms
  (glibc natively, Emscripten's musl-based one in wasm). [Review A7 1.5, checked] (S5-0, spike 6: with a ten-line
  `--pre-js` giving PhysicsFS a HOME and one `#ifdef` removed, the Node wasm build reads an asset root and 21 of the 22
  projects build byte-identical; the 22nd differed by one undefined `std::clamp`, not by libm; written out, 22 of 22.
  These changes are going into the core after S5-0: S5.md.)
- **The game side** has `--extra-mount <dir>` (development roots only), headless scenarios, screenshot and menu-input
  tours, and console commands `loc`, `goto <map-id> x y z dir`, `reload map`, `exec <file>` and `screenshot [name]`.
  It has no reload when files change (PLAN 10b item 2, not made), no channel to control a running game, no way to
  report where the player stood when the game closed, and no way to leave a note at a place (the user types `loc` and
  copies the line by hand).

### 0.3 The proposed foundation, in one table

Each row is argued in the section named and listed as a decision for the user in section 6.2.

| # | Proposal | Keeps or changes the plan | Section |
|---|---|---|---|
| D1 | Keep PLAN's processes: browser, thin Node host, native `oymap serve`; wasm for the hosted page. **First split what the revision covers** (source files; the id lock as a record; pins as their own document), then make `serve` a **caching** service keyed by the source revision (so the files stay the truth) with **two lanes** (interactive and jobs) and a **push channel** to the browser | Keeps P§1, §8; changes P§5's revision; adds what interactive editing needs | 2.4, 2.4.1, 2.8 |
| D2 | **One typed request list** (`openyamm-studio/schema/rpc/`), served by native `serve`, by the wasm worker, and used by the MCP tools and the command line in the same phase (plus a generic `oymap call <method> <json>`); the browser never sends `run` with free arguments | New; makes P§9 "one client interface, two backends" concrete | 2.3 |
| D3 | The browser edits **only through operations**; operations are extended to every list of every file (lists whose items have an `id`, `sketch.yml` included), plus a `patch` operation (JSON Patch with `test`) whose pointers address **keyed lists by key**, **rename**, **ids allocated by the core**, **merging of repeated edits**, an `author` and a `label` on every transaction, and **macros in the core**. Issues get a **severity**; the lowering **skips an object it cannot lower** and builds the rest, so a half-drawn state still shows | Keeps P§5; replaces the unbuilt named-operation catalogue | 2.6, 2.4.2 |
| D4 | **One append-only history**: undo is a new entry that reverts one earlier entry object by object, validated like any transaction; redo reverts the undo; each author's undo position is derived from the log; a stale transaction is **rebased** when its keys and `test` steps still hold. File versions are stored once by hash, compressed | Replaces P§5's cursor over snapshots | 2.7 |
| D5 | The UI covers the vocabulary **through the schemas**: per-field annotations (`x-geom`, `x-unit`, `x-key`, the kinds an id field accepts, a rule for unions, grouping and order), a schema-driven inspector for every field, and the object's canonical YAML as a Source tab; a **schema lint in the unit suite** refuses a schema change that lacks them. Bespoke widgets only for a short list | New; needed because the vocabulary is about 1 860 fields and grows | 3.8, 3.18 |
| D6 | **three.js** on WebGL2 first, version pinned; the core supplies meshes and every object's resolved position; the client draws and never computes a game rule | Keeps P§9's three.js; WebGL2 before WebGPU | 2.9, 4.4 |
| D7 | **Walk mode runs the core's movement code in a wasm worker in both modes**, but walk is **part of the request list** (`walk.load`, `walk.step`, `walk.toggle`) so a native lane can serve it; textures in local mode **do not depend on wasm** (the host un-frames zstd) | Changes P§1/§3 "wasm for the hosted page only" | 2.10, 2.11 |
| D8 | Web app in **TypeScript with a Vite build**; the host stays plain JavaScript with no build. React (P§9), Zustand (P§9), **CodeMirror 6 instead of Monaco**, a **fixed layout first instead of Dockview**, own SVG/Canvas plan view and flow graph, own schema forms; **plain CSS with variables and CSS modules, one headless primitives library, one list virtualiser** (4.16) | Mostly keeps P§9; two substitutions; styling added | 4, 4.16 |
| D9 | **Pins format 1**: pose, picture, author, thread of replies, a claimed state, the revision; **from the game first** (`pin <text>` in the console), answered by agents through the command line before any browser exists; pictures kept outside git by default | Extends `pins.schema.json`; P§8 tool | 2.10, 3.13 |
| D10 | The Python checks the user relies on (`town_feel.py`, `scale_bands.py`, `building_shots.py`, `things_shots.py`, `compare.py`, `texture_use.py`) run as **host jobs in local mode**, with output schemas in the request list and a capability flag where Python is absent; they move into the core only when the hosted page needs them | Names a conflict with "C++ is the only implementation of checks" [C] | 2.4, 3.11 |
| D11 | Phases: **S5-0** (spikes, including native-against-wasm builds of all 22 projects), **S5a in five slices** (pins from the game; open and look; the pin loop in the browser; walk and Play here; scorecard, compare, jobs, flow), **S5b1** (indoor), **S5b2** (outdoor), **S5c**; spike code is thrown away except the request list | Refines P§12 | 6.4 |
| D12 | Where the hosted page lives and whether the release ships the studio (oymap, the host as a single executable, the web app) | Open in the plan | 4.14, 6.2 |
| D13 | Game-side development features S5 wants, **`pin <text>` first**: then run a console file at start (test switches), write the pose on exit, reload on change (no per-frame polling) | P§10b items 2 and 4, plus new | 2.10 |
| D14 | Sharing a mod depends on S6's named mods; S5 exports overlay projects safely and warns that a new map's table rows replace whole tables in today's single `mods/` folder | Names a gap | 1.3 F3, 5 W8 |
| D15 | Terrain for new outdoor maps: whether a designer may sculpt (written as `heights.nodes`) or only describe (points, ridges, cliffs, terraces). **Decided** (15:11, extended in the evening): described first, sculpting in bounded, marked patches; a person may mark a project's land as hand-made, and then the brush covers the whole map; strokes stored as differences over the described land | Was open: the design page draws brushes, the rebuild rule forbids traced height fields [C] | 3.18, 6.2 |

### 0.4 What the prepared material contradicted (details in appendix B)

The design page (revision 4) predates the review that rewrote PLAN on 2026-11-12, and the vocabulary built in S3 and
S4 differs from what both imagined. The main points: the host holds no documents and loads no wasm (the design page
says it does); the MCP SDK is 1.32.2 on protocol 2025-11-25 (not 2.x on 2026-07-28); outdoor projects are
`sketch.yml`, not PLAN section 4's `terrain/` and `geometry/` folders; operations are four generic verbs, not PLAN
section 5's catalogue, and `sketch.yml` has none; the design page's outdoor tools (brushes, coast stamp, road splines
that grade, a kit library of NWC prefabs, plots) are not the words that exist; set-piece import and the Python port
were dropped; pins have no camera or picture; tier 1's incremental compile per room is not built; several user-facing
checks are Python, not core. Review A7 found four more, in the first draft of this document against the code
(B20 to B23): the revision covers pins and the id lock; validation is the whole lowering and issues have no severity;
native and wasm byte identity is checked on two example projects only; `sketch.yml` has no `x-sort`.

### 0.5 Review A7 and how it was taken in

[S5_REVIEW_A7.md](S5_REVIEW_A7.md): go for S5-0 once its seven changes are in; no go for S5a until the spikes report.
Its code findings were checked against `core/Project.cpp`, `core/Ops.cpp`, `core/IndoorBuild.cpp`,
`core/OutdoorBuild.cpp`, `core/Project.h`, `cli/Commands.cpp`, `tests/native_vs_wasm.sh`, the schemas and Node; all
held.

| Review point | Change made | Where |
|---|---|---|
| 1.1 Split the revision | Three classes of file: source (revision, history, undo, caches, `expect_revision`), the id lock (a record, hashed apart, never undone), pins (own document, counter and log); core work before D1's cache, done in S5a1 | 0.2, 2.4.1, 2.8, 3.12, 3.13, D1, 6.4 |
| 1.2 Validation is the lowering | Severities (error, warning, note); a lowering that skips a broken room or structure and builds the rest as a view build that never installs; last good mesh kept and marked stale; core work in S5b1 (rooms) and S5b2 (structures); until then a person's edits that add errors are refused; budget set on Erathia; spike 2 splits the time; the client applies its own patch at once; the review's timings used | 0.2, 2.4, 2.4.2, 2.4.3, 2.5, 2.6 item 8, 2.13, 6.4, C |
| 1.3 Keyed addressing | Every selectable or pinnable sub-object gets a key in the format bump (`x-key`); pointers into keyed lists use the key (a stated departure from RFC 6901); rename; ids allocated by the core; merging of repeated edits (`merge_key`) | 2.6 items 2 to 6, 2.9, 2.15, 3.8, 3.18, W3 |
| 1.4 One undo model | Append-only history; undo is a validated revert entry, redo reverts the undo, positions derived from the log; snapshot restore as the test oracle; file versions stored once by hash, zstd-compressed; D4 replaced | 2.7, 3.12, D4, W5 |
| 1.5 Native and wasm on all projects | The Node wasm build reads an asset root and all 22 projects are built both ways and compared in S5-0, then in CI | 0.2, 4.10, 4.13, R8b, 6.4 |
| 1.6 `pin <text>` first | Console command writing pose, text and screenshot into an inbox; pins format 1; `oymap pins` answers with game pictures; the `loc` paste box dropped | 1.3 F1, 2.10, 3.13, W7 (new), D9, D13, 6.4 S5a1 |
| 1.7 Slice S5a | Five slices: pins from the game; open and look; the pin loop in the browser; walk and Play here; scorecard, compare, jobs, flow; D11's phases replaced | 6.4, D11, R19 |
| D1 conditions | Staleness by size and time then raw bytes; watcher ignores `.oymap/`; outside edits merged; banner for a file that does not parse; cancel kills lane J, writes atomic; hosted mode decided: one worker; the dry run's GLB write measured | 2.4.3 |
| D2 conditions | MCP tools and command line move onto the list in the same phase; `oymap call`; numbers rounded by rule; output schemas for the Python checks | 2.3 |
| D3 conditions | `oymap record` for file-writing agents; collections from "items have an `id`" (not `x-sort`) | 2.6 items 1 and 7, 1.3 F4 |
| D5 conditions | `x-id-kinds`; a rule for the 37 unions; grouping and order; a schema lint in the unit suite; a schema-form spike | 3.8, 4.13, 6.4 S5-0 (7) |
| D6 | No picking tree until spike 1 asks; CI software GPU and BC7 checked | 4.1, 2.11, 6.4 S5-0 (5) |
| D7 conditions | Walk in the request list (`walk.*`) so a native lane can serve it; recorded walk replayed on both; local-mode textures un-framed by the host with `node:zlib` zstd (checked: Node 24.21) | 2.2, 2.3, 2.10, 2.11, 4.11 |
| D8 gap | Styling and primitives proposed with alternatives: plain CSS modules with tokens, Base UI (Radix runner-up, React Aria the accessibility-first option), TanStack Virtual, own palette | 4.1, 4.16, D8 |
| D9 | Pin pictures outside git by default; kept on purpose only; 6.3's first recommendation reversed | 3.13, 2.8, 6.3 |
| D10 | Output schemas and a capability flag | 2.3, D10 |
| D11 | Spike code thrown away except the request list | 6.4 |
| D12 | The review's view added beside the recommendation: an origin of its own | 4.14, D12 |
| D13 | `pin` first; reload on change without per-frame polling | 2.10, D13 |
| D15 | The review's view added beside this document's | D15 |
| 3 Security | `Host` header check; token on the HTTP byte routes | 2.12 |
| 3 Revision length | A 128-bit hash as cache and URL key | 2.3 |
| 3 Numbers | Load recorded with each measurement; Erathia and a real `oymap edit` in appendix C | 2.13, C |
| 3 Tests for an agents' UI | A panel gallery screenshotted by Playwright, looked at before reporting | 4.13, R15 |
| 3 Pointer lock and `Esc` | `Esc` leaves mouse look in walk; no clash with cancelling a drawing | 3.6, 3.17 |
| 4 S5-0 as the review would run it | All its additions are in S5-0: 22-project builds, Erathia split, provenance on Darkmoor, half-drawn room, schema forms | 6.4 |
| 5.1 The lock forgets removed objects | Checked: an indoor build drops the entries of ids the project no longer has (`core/IndoorLowering.cpp:20745`); outdoor builds keep all. The lock now keeps removed ids' numbers until an explicit `oymap lock prune` (never a build or an undo); a table with no free number names the prune; in S5a1 | 0.2, 2.4.1, 2.7, 6.4 S5a1 |
| 5.2 Rename against "the lock is never undone" | Rule: undo never changes a number; a revert of a rename runs as the opposite rename; names in the lock and pins follow renames both ways; a rename by file edit gets a new number; built with rename in S5b1 | 2.4.1, 2.6 item 4, 2.7, 6.4 S5b1 |
| 5.3 Keys optional in files | The schema never requires an `x-key` field; a missing key reads as the one the core would give and is written on the core's next write; a regenerated file's keys are positional again, stated as a limit of generated projects | 2.6 item 2, 2.15, 6.4 S5b1 |
| 5.4 `oymap record` races the watcher | `record` puts its author and label on the unattributed `outside` entries since that author's last entry, changes nothing else in them and lists what it took | 2.6 item 7, 2.7, 6.4 S5a1 |
| 5.5 Pins on sub-objects before keys | Until keys arrive (S5b1 indoor, S5b2 `sketch.yml`) a pin anchors to a top-level id or a point only | 3.13, 6.4 S5a1, S5a3, S5b1 |
| 5 smaller: `merge_key` | Named as the one exception to the append-only history | 2.6 item 6, 2.7 |
| 5 smaller: optimistic `add` | An `add` whose id or key the core allocates is drawn as a ghost until the answer; not applied ahead | 2.4.3 |
| 5 smaller: `<stem>.studio.yml` | Written by every install route the user plays from: `oymap install --mount` and `--root` (the play roots of `output/studio_play`), Play here | 2.10, 6.4 S5a1 |
| 5 smaller: S5-0 size | M, not S (seven spikes) | 6.4 |
| 6.1 Section 6.3 settled as recommended (the user, evening) | Pin inbox at the default, `PLAY.md` says where; map numbers from S6's manifests, a project-root setting until then; the design page's Discord questions asked during S5a, posted by the user (the bot only reads); the project list per map, a world view later; the walk uses the game's movement constants (radius 37 in every world today: `game/outdoor/OutdoorWorldRuntime.h:1872`, `game/indoor/IndoorMovementController.h:45`), no studio setting; lighting bakes later; pins on a shipped map make an empty overlay project; projects never inside `mods/` | 1.3 F1, F2, 2.10, 3.6, 6.3, 6.4 S5a, A |
| 6.2 Three ways of working | Two more kinds of people: F5, the hand author (everything by hand, dungeons and land), and F6, agents' base finished by hand. S5b1's and S5b2's exit criteria each gain a small new map from an empty project entirely in the UI (no Source tab, no YAML, no command line), with every word that forced the Source tab listed in the phase record; S5b1 gains the mixed test (an agent-made map finished by hand, then an agent adds through operations, every hand edit still there) | 1.3 F5, F6, 6.4 |
| 6.3 R5 needs a mechanism | In S5b1: a durable mark in `project.yml`, written by the core at the first source transaction whose author is a person; agents told in `project.open`, `map_open` and every edit result; in a marked project an outside change that replaces objects a person changed last, or drops keys, is recorded with an error notice listing them and one step to revert that entry; agents' operations on such objects are not refused, their result lists them; REBUILD_PROCEDURE.md and OUTDOOR_REBUILD_PROCEDURE.md say agents edit marked projects by operations. Deferred: the procedures shipped with the Studio download | 2.8, R5, 6.4 S5b1, deferred list |
| 6.4 D15 extended | Bounded, marked patches stay the default for maps agents edit; a person may mark a project's land as hand-made (in the sketch), then the brush covers the whole map; no procedure sets the mark, a rebuild refuses it, agents read such land through queries (height at a point, a profile, slope). Raise, lower and smooth strokes stored as differences over the described land, a new word beside `nodes` (checked: `heights.nodes` is absolute, applied last, and overrides every word beneath it); flatten writes a `terraces` entry; settled by one S5b2 test (an agent moves a ridge under a sculpted patch). A stroke is previewed in the browser and committed once on mouse-up. A ground paint brush writing zone outlines in S5b2's tools. Heightmap import outside S5's acceptance, the first addition after S5b2. Spike 2 measures one node-block patch on Erathia | 0.3, 3.18, 6.2 D15, 6.4 S5-0 (2), S5b2, deferred list, the user's decisions |
| Spike 7 (`output/s5_spikes/7_forms/REPORT.md`) as such | Union rule reworded (different JSON types need nothing; one type needs `const` or `x-variant`); `x-discriminator` and `x-kinds` for the 21 kind-selected objects, per-kind `x-unit`/`x-geom`; the spike's result recorded (every building and room of the 22 projects renders; 49 to 68 % complete without hand annotations) | 3.8, 6.2 D5, 6.4 S5-0 (7) |
| Spike 7, review A7 point 1: `x-kinds` enforced by the core | Checked: `structures[].items` has 156 properties over 28 kinds, one `additionalProperties: false` and no per-kind check, so a wrong-kind word validates and is unused. The core reads the same `x-discriminator`/`x-kinds` and reports "word X does not apply to kind Y" as a warning; first run over the 22 projects, each hit settled as a wrong kind-table guess or a dead word | 2.4.2, 3.8, 6.2 D5, 6.4 S5b1, S5b2 |
| Spike 7, point 2: the lint checks existence, not correctness | A corpus rule (each annotated number's values across the 22 projects within its unit's range); each annotation batch checked against the lowering by an agent other than its writer | 3.8, 6.4 S5b1 |
| Spike 7, point 3: defaults decided in the lowering | The inspector shows each field's effective value from the core's resolved read (`project.resolve`, S5b1), not hand-written `default` copies | 2.3, 3.8, 6.4 S5b1 |
| Spike 7, point 4: editable is not usable by hand | In the hand-author exit tests a generic row list where 3.18 promises a bespoke tool (the wall bay strip, for one) counts as a miss | 1.3 F5, 3.18, 6.4 S5b1, S5b2 |
| Spike 7, also | The building words moved into one `$defs` in S5b2's format change, with the check that all 22 projects and the unit suite's refusals validate the same before and after; the inspector's in-browser render time measured in the real app in S5a2 (the spike's times are Node server renders) | 3.8, 6.4 S5a2, S5b2 |
| 3.1 (b1) A person can set the mark | "Protect this project" in the project's settings (and `oymap protect`) writes the same mark, for people who edit the YAML in a text editor, since unattributed outside entries do not mark; only a person sets it by hand or clears it | 2.8 item 1, 1.3 F6 |
| 3.1 (b2) Unknown history only for the whole-file notice | Objects whose last change the kept history does not show count as a person's for the whole-file notice only; operation results list only objects the kept history really shows as a person's; `project.open` and `map_open` say once that history before a date is not known | 2.8 item 3, 0.5 notes |
| 3.1 (b3) Undo and the mark; its `revision` | Reverting the entry that set the mark leaves the mark (the revert skips `edited_by_hand`; only a person clears it). **Decided: keep the field**, defined as the source revision before the marking transaction (the last state agents alone made, so a diff from it shows all the hand work); for a mark set in the settings, the revision at that moment | 2.7, 2.8 item 1 |
| 3.1 (c) A record of what the lowering reads | A checking mode records the keys each object's lowering read; "word X was never read on this object" (conditional reads that the projects never meet as a `note`) catches a kind table allowing an ignored word and generates the first kind tables for the 27 guessed structure kinds, before the 156 entries are filled by hand; the second agent's check stays for reads without effect; the indoor lowering not yet checked. **Verified with a correction:** the counts hold (93, 177, 143, each including the file's own helper definition), but `childOf`/`textOf` are sixteen copies in sixteen files (eleven outdoor), and a few reads walk a map's keys directly, so the copies become one shared helper first and the hour estimate may be two or three | 3.8, 2.4.2, 6.4 S5b2, 0.5 notes |
| 3.1 (a) Smooth strokes | Agreed as written | 0.5 notes, 3.18 |

**Where this document keeps a different view, and why** (both views are kept in the sections named):

- **1.1, a detail:** the review says Play here's lock rewrite makes the watcher report an "outside" change. Today's
  core records a lock-only change as an entry of author `build` (`core/Ops.cpp:424`), not `outside`. The conclusion
  stands (it is still an undoable entry that moves the revision); only the label differs.
- **1.1, the lock "never an outside edit":** a `git checkout` changes the lock and cannot be prevented. This document
  takes such a change as the new record and logs it in the host, outside the undo history (2.4.1), rather than
  calling it an error.
- **1.2, an addition:** a build that skipped objects is a **view build** only; install, Play here and playtests still
  refuse errors, so a partial map never reaches the game (2.4.2). The review's (a) and (b) leave this open.
- **D7, the reason:** the review calls the first draft's reason weak. This document agrees that the review's reason
  (the browser wasm build exists and runs daily from the first slice) is the main one, and keeps the lane argument as
  a secondary one: a third lane would also keep walk off lane I, but every step would still cross two processes
  (2.10).
- **D8, browser keys:** the review proposes an app window because `F5` reloads and `Ctrl K` is the browser's. This
  document's view: a page can take both with `preventDefault` in Chromium and Firefox; the keys a page cannot take
  (`Ctrl W`, `Ctrl T`, `Ctrl N`) are not used. The app window is still proposed for its room and lack of tabs, but the
  key table does not depend on it; spike 5 confirms (3.17).
- **D15:** see the decision table: both views, the difference is whole-map nodes against bounded patches. (Settled:
  the user chose bounded patches at 15:11; the evening's extension adds whole-map sculpting only on land a person
  marks as hand-made, stored as differences, not as `nodes`.)
- **6.3 (the mark), an addition:** which objects a person changed last is read from the history in `.oymap/`, which
  does not travel with git or an exported zip, while the mark does. Where the kept history does not show an object's
  last change (a fresh clone, an unpacked zip, entries past the 1 000 kept), the object counts as changed by a person
  for the whole-file notice only, so a whole-file rewrite of a marked project still gets the notice there (narrowed in
  revision 3.1). Two further additions: only source
  transactions mark a project (a pin, a reply, an accept and `oymap record` do not); and a person may clear the mark in
  the project's settings, knowing that a generator run then erases hand edits; no agent and no procedure clears it
  (2.8). Review A7 agreed with these three additions; revision 3.1 refines them.
- **6.4 point 4 (strokes as differences), a reservation:** raise and lower are differences by nature; smooth is not.
  A smooth stroke is a correction computed from the land as it was; stored as a difference, it carries that land's
  bumps, inverted, onto a base an agent has since moved. So S5b2's test moves a ridge under a smoothed patch as well as
  under a raised one, and if the smoothed one shows ripples, smooth is stored as its own entry (outline and strength,
  applied by the build after the differences) instead of as a difference (3.18). Review A7 agreed as written.
- **Spike 7 point 1, a limit:** the run of the kind check over the 22 projects finds words used where the kind table
  excludes them; it cannot find a table that allows a word the lowering ignores for that kind. That direction rests
  on point 2's check of each annotation batch against the lowering, so the two are one safeguard, not two (2.4.2).
  Review A7 agreed and proposed a mechanical check for that half (revision 3.1): the lowering records which keys of
  each object it read, so "word X was never read on this object" is found by a run, not by an agent (3.8).

**Questions left for the user** (answered since: the user's decisions of 15:11 and of the evening, at the end of this
document; the paragraph is kept as it was asked) (section 6.2 has each with its recommendation): all fifteen decisions
still need his answer before S5a; the review changed D1, D3, D4, D5, D7, D8, D9, D11 and D13, so they are asked in
their revised form. Those that are his alone: **D12** (shipping and hosting; the review agrees with the
recommendation and adds an origin of its own), **D15** (terrain sculpting; two views), and **D8's styling and
primitives** (Base UI, Radix or React Aria; plain CSS modules or another method), which fix the look of every panel.
Also new: **D13's `pin` command is a game change**, the first of S5; it needs his yes like the other game-side
features.

### 0.6 Spikes and how they were taken in (revision 4)

The record of S5-0 is [S5.md](S5.md): what each spike measured, the numbers with the load average, the verdict
against 2.13 and the core bugs found. Its exit criteria are met. Each row is one change the spikes call for, and
where it was made in this document. Spikes 1 and 5 share one report (`output/s5_spikes/1_viewer/REPORT.md`).

| Spike | Finding | Change made | Where |
|---|---|---|---|
| 1 Viewer | Synchronous `zstdDecompressSync` blocks the host up to 32 ms per file; 122 files take 314 ms | The host un-frames with the asynchronous `zlib.zstdDecompress` and keeps an LRU of un-framed blocks | 2.11, 4.1 |
| 1 | Lowest mips first: Darkmoor textured at 181 ms instead of 375 | Lowest mips first is the loading order, not an option | 2.5, 2.11 |
| 1 | Harmondale's two terrain weight images are 32 MiB of GPU memory as RGBA8 | The weight images are cooked to a block format or halved | 2.11, 2.13 |
| 1 | Picking without a tree: p95 1.0-3.3 ms, max under 10 ms (Chrome); three-mesh-bvh's first hit differs from Raycaster's, untraced | No picking tree indoors; outdoors the terrain is picked in chunks of 16 x 16 cells; three-mesh-bvh only if MM9's maps need it, after its hits are checked | 4.1, 2.13 |
| 1 | A fresh headless Chrome lost its WebGL context once | The viewport module handles context loss by re-uploading from its cache | 4.4 |
| 1 | Software GPUs: dungeons at 3.6-16.7 fps, Harmondale 0.5-4 fps | CI takes dungeon screenshots on a software GPU, outdoor maps as single frames at a smaller size | 4.13 |
| 5 Browsers | Every browser tested, CI's software GPUs included, takes BC1, BC5 and BC7 in WebGL2; decodes differ by at most 3 levels | CPU BC decode dropped; CI screenshot tests allow a few levels on BC1 and BC5 | 2.11, 4.1, 4.11, 4.13 |
| 5 | Local network access gates fetch and the WebSocket in Chrome, Chromium and Firefox; Chrome fails at once, Firefox hangs for the prompt | Pairing starts from a button that says the browser will ask; a hanging first request reads as "waiting for your answer", an immediate failure as refused; local mode needs no permission | 2.12, R10 |
| 5 | `F5` and `Ctrl K` reach the page first and can be prevented; whether the browser then skips its own action needs a hand check | The fallback keys stay named until the user's hand check | 3.17 |
| 2 Edit latency | Indoor cached edit 275 / 294 / 300 ms (load 12); without parsed table lookups 387; the hidden cost is 2 050 line-scanning decoration lookups per lowering | The 300 ms budget holds on three conditions: parsed table lookups once per asset root, one validation per edit, schemas of changed files only; re-measured on a quiet machine | 2.4.3, 2.13, 6.4 S5a2 |
| 2 | The view build is 749 ms median, 1 556 p95; BSP and outlines 37-41 % of it; compiled faces are lowered faces with rounded corners | `view.mesh` comes from the edit's own lowering; compiler, BSP, outlines and GLB only for install, Play here and playtests | 2.4.3, 2.5, 2.9, 2.13 |
| 2 | Outdoor edit on Erathia 1 303 / 1 424 ms; land lowering 840, scene write and reader check 238 | Outdoor commit 1.5 s p95 for S5a and S5b1; 500 ms for S5b2 with the land kept up to the peaks (keyed by a hash of the land words without `nodes`) and the scene write and reader check out of the commit; 3D after an outdoor commit: the commit plus 200 ms | 2.4.3, 2.13, 6.4 S5b2 |
| 2 | A brush stroke costs a whole-map lowering (1.3 s at any size); only `set_value` of the whole list reaches `heights.nodes` (16.8 KB a request) | One commit per stroke (on pointer up), the client drawing until then; a keyed or path `patch` into `heights.nodes` (and the stroke word) | 2.6 item 3, 3.18, 6.4 S5b2 |
| 2 | One issue anywhere stops the whole lowering; a schema issue ends validation first; one broken room gives a view of 0 faces | The skipping lowering also skips objects with schema issues (issues attributed to their object) | 2.4.2, 6.4 S5b1 |
| 2 | A bow tie and collinear points are reported as "must run counter-clockwise" | Outline messages say what is wrong ("crosses itself", "has no area") | 2.4.2, 6.4 S5b1 |
| 2 | Erathia's 166 sketch warnings switch the outdoor lowering off; `validateProject` never passes the asset root outdoors (`--assets` runs a second dry build) | Severities first outdoors (S5a2); `validateProject` takes the asset root outdoors: one dry build, not two | 2.4.2, 6.4 S5a2 |
| 2 | Stamping faces in the lowering keeps 97.0 % of faces at exactly one id (99.7 % with the remaining kinds); node names are ambiguous | Provenance is stamped in the lowering, not read from node names; the remaining kinds stamped; platforms get keys (S5b1) | 2.9, 6.4 S5a3 |
| 2 | The indoor dry build writes its GLB into `<project>/build/` | The watcher ignores `build/` as well as `.oymap/` until the view build stops writing files | 2.4.3 |
| 3 Walk | Step p99 55-260 us on 30 605 faces; 60.05 steps a second in both browsers | D7 holds; no native lane needed | 2.10, 2.13 |
| 3 | Native and wasm walks drift with C-library `sin`/`cos` of the yaw, bit-identical with deterministic ones | The walk's input uses the core's own trigonometry; the game's mover rotations (`IndoorMovers`, `OutdoorGeometryUtils`) too, as their own reviewed game change; the contract walk includes a map with a rotating mover | 2.3, 2.10, 4.13 |
| 3 | `walk.toggle` worst case 0.66-0.8 ms Darkmoor, 3.7-4.4 ms Thjorgard | Accepted as a once-per-click cost in the worker | 2.10 |
| 3 | `walk.load` on Harmondale is 190-280 ms of yaml-cpp on the 960 KB scene | `walk.load` takes the scene's movement state, not the whole scene text; the core writes it beside the built map | 2.10 |
| 4 Request list | Kept in `openyamm-studio/schema/rpc/`: version 1, 40/40 native, wasm identical where it had the asset root | Version 1's contents and choices recorded; the core move, the CI check, and the MCP tools and command line onto the list in S5a2 | 2.3, 6.4 S5a2, S5a3 |
| 4 | `oymap edit` took the first of an id found in two files | Ids are unique per file (twenty-third merge); operations, pins, selections and provenance carry the file | 0.2, 2.6 item 11, 3.13 |
| 4 | Erathia has 166 issues yet builds | The severities' first rule exists (`heights`, `coverage` as warnings), set where each issue is found | 2.4.2 |
| 4 | Operations are a union by `op` | An `x-discriminator: op` hint on the operation union; contract cases for `locked` and `failed`; one wasm instance kept alive across the suite | 2.3, 4.13 |
| 6 Native against wasm | 21 of 22 identical; the 22nd an undefined `std::clamp` answered differently by libstdc++ and libc++; libm differs but reaches no byte; five UB sites | 4.10's emphasis moves from libm to UB and the two standard libraries: a sanitizer job (native ASan/UBSan with `_GLIBCXX_ASSERTIONS`, wasm ASan), the UB sites fixed, the 22-project comparison in CI | 4.10, 4.13, R8b |
| 6 | musl's math compiled natively reproduces wasm on 3.2 million inputs at no cost | The core's own math (`oy::sin`, `oy::hypot`, ...) from musl's sources on both sides, as insurance; also used by the walk | 4.10, 2.10 |
| 6 | `inPlane` compares `long double` products (80-bit natively, 128-bit in wasm) | No `long double` in lowering code, or its products under 2^64 by construction | 4.10 |
| 7 Schema forms | Branches of different JSON types need nothing; the real unions are kind-selected objects | The union rule reworded; `x-discriminator` and `x-kinds` (Revision 3 took most of this in) | 3.8 |
| 7 | The description rule finds 122 of 577 numbers with a unit | `x-unit` on every number; the lint requires it | 3.8 |
| 7 | Grouping per property is 69 % of the building's hand work | Grouping per object (`x-groups`), the lint checking each property is in exactly one section, reported per property | 3.8 |
| 7 | 104 `effects`/`else_effects` steps cannot be drawn (untyped lists) | Event steps get a schema (`$defs/effect`, a union by its one key); the event form stays bespoke | 3.8 |
| 7 | A building's `parts` words are written twice (about 40 KB each) | The building words in one `$defs` (taken in by Revision 3) | 3.8 |
| 7 | Today's schemas have 1 208 lint issues | The lint lands in S5a2 with those 1 208 as an allow list that may only shrink, so words added meanwhile need their annotations; it runs in the web app's suite, using the form generator's own classification | 3.8, 4.13, 6.4 S5a2 |

---

## 1. Goals, non-goals and the people who use it

### 1.1 Goals

- **G1. The user reviews agents' maps without a translator.** He opens what an agent built, walks it, pins what is
  wrong where it is wrong, and sees each pin answered with the change and a before-and-after view. Today the lead
  turns his words and `loc` lines into tours and briefs by hand. [P: S5 (a) acceptance; design page "Address review
  pins"] [N: the review-mode emphasis]
- **G2. A person builds and changes maps by hand with the agents' words.** Rooms, openings, doors, events, buildings,
  roads, scatter: the same project files, the same operations, the same checks. [P: S5 (b); README decisions]
- **G3. One core, one set of files.** A map made by hand opens for an agent exactly as left, and the other way round.
  No front end keeps document state. [P: PLAN 5, design page "One core, three front ends"]
- **G4. A player's install is enough.** The hosted page needs no server; assets come from the user's install or
  repository. [P: README decision; PLAN 9]
- **G5. Checks are always on and lead to the object.** Every issue names an object and, where the core knows one, a
  fix. [P: design page principles "Validation is always on", "Errors say how to fix it"]
- **G6. The UI keeps up with the vocabulary without work per word.** A new schema field is editable the day it is
  merged. [N: forced by section 0.2's numbers]
- **G7. Fast enough to think in.** Selecting and hovering never wait for the core; a committed change shows in the
  plan within a third of a second and in 3D within about a second (section 2.13). [P: design page "Test in under a
  second", "What made editors clunky"] [N: the numbers]

### 1.2 Non-goals

- Modelling, UV unwrapping, creatures, art generation: Blender, Codex image generation and Meshy stay outside; the
  studio places, searches the library first and uses placeholders. [P: README decisions; design page "What the
  studio does not do"]
- A second implementation of formats, compilers or checks in TypeScript. [P: README decision] The client may snap a
  pointer to a grid and draw what the core resolved; it does not decide where a door's faces go.
- The game's exact look. 3D views draw the core's meshes with simple materials; "the exact look comes from Play
  here". [P: PLAN 9]
- Editing generated map Lua or MM9 converter output. [P: PLAN 13, AGENTS.md]
- Commits: the studio never creates git commits. [P: PLAN 5]
- Collaboration between several people over a server. Pairing is one person and the agents on their own machine.
  [N, implied by the local host and the static page]
- Touch and phone layouts. [N]
- Full editing in Firefox and Safari in hosted mode (view, review and zip export only). [P: PLAN 9 table]
- In S5: the MCP App viewer, MM9 profiles, named mods (S6); the puzzle simulator, landmark visibility, coast stamp
  and other design-page tools that no acceptance test needs. [P: PLAN 12] [N: the deferral list, section 6.4]

### 1.3 Who uses it, and how, step by step

Six kinds of people use the studio. Each flow names the parts of section 3 it touches and the phase that makes it
possible. F5 and F6 come from the user's answer of 2026-11-14 (evening): "a lot of people will want to also make the
dungeons and terrains etc. by hand entirely ... And some will use agents to do the base and finishing touches by
hand." [Review A7 6.2]

#### F1. The user reviewing agents' maps (S5a)

Today: agent finishes a round, the lead installs the map into a play root and writes a command into `PLAY.md`; the
user plays in the game, reports in words with `loc` lines or pictures (`test_img/NNN.png`); the lead captures each
pose, traces it to the project or the studio, and briefs an agent; the agent fixes and reports; the lead installs
again. The user's own words (OUTDOOR_REBUILD_PROCEDURE.md, 2026-11-14): "I can't take screenshots of all the
buildings for you while you can".

**First, before any browser (S5a slice 1, review A7 1.6):** he plays as today and, where something is wrong, types
`pin <text>` in the game's console. The game writes the pin (text, pose, the map and the project revision it was built
from) and its own screenshot into the pin inbox. `oymap pins import` files each pin into its project; an agent lists
the open pins from the command line, changes the project, takes the after picture in the game at the pin's pose
(`oymap pins tour`, `run_game.sh --isolated`) and replies; the static review page shows each pin with its before and
after pictures. No `loc` line is copied and no tour is written by hand.

With the browser (S5a slices 2 to 5):

1. The host runs on his machine (`oymap studio`, or `node openyamm-studio/host/src/host.mjs studio` until the
   shortcut exists [P: PLAN 8 names `oymap studio`; S2 did not make it]). It opens the browser on
   `http://127.0.0.1:<port>/#token=<pairing token>`.
2. **Project list.** The host's configured project roots (`devdocs/map_studio/briefs/*/L4`,
   `devdocs/xeen/briefs/*/L4`, and any folder he adds) with each project's revision, last change and author, open
   pins, and its last scorecard (compare score, playtest result, town-feel flags, coplanar pairs). The list is per map
   in S5; a world view over many maps comes later (6.3, settled). Projects are folders outside `mods/`; only builds
   are installed there. [N]
3. **Review mode** opens the chosen project read-only for geometry, writable for pins (wireframe W1). Plan and 3D side
   by side, textured, doors as the map starts; the drawer on Pins and Scorecard.
4. He walks it at party size (`G`), or presses `F5` (Play here): the host builds, installs into the mount folder
   (and writes the outdoor terrain material file, without which the game refuses an outdoor map: HANDOFF.md), and
   starts the real game at the camera's place, visible. [P: design page "Play here"; PLAN 8 game bridge]
5. He sees a fault. In the studio he presses `P` and types; the pin takes the picked object (or the point), the camera
   pose and a picture of the view. In the real game he types `pin <text>`, as in slice 1; the host imports the inbox
   and the pin appears in the drawer. [N]
6. The pin is written to the pins document (`review/pins.yml`, its own counter and log, not the map's revision),
   `author: user`. An agent (through MCP or `oymap pins`) reads open pins, claims one (status `claimed`, shown live in
   his drawer), changes the project, and resolves it with a reply. [P: `map_pins`; N: claimed, live]
7. The browser is told of each new revision (section 2.4, push channel). The pin turns green with the agent's reply, a
   link to the history entry's semantic diff, and two pictures from the pin's camera: before and after (studio views,
   or with a job the game's own pictures). He presses Accept or Reopen. [N]
8. For rebuilds, the Compare view (W6) shows the measure's worst places with both maps' cameras locked; for outdoor
   maps the per-building pairs of `building_shots.py` come in as a picture set (a job, about 35 minutes for two maps:
   HANDOFF.md). [P: tools exist; N: in the UI]

#### F2. A designer building a dungeon by hand (S5b1)

1. Starts the host from the repository, or opens the hosted page in Chromium (then without Play here).
2. **New project**: world, indoor, map id (`crypt01`), name, and a `map_stats` row number. The studio proposes the
   next free number in the user's range and refuses one the tables already use. The range comes from S6's world and
   mod manifests; until they exist, from a setting of the project root (6.3, settled). [P: `oymap new`, `map_new`; N:
   the free-number rule]
3. **Plan**: spaces with purpose and size class, links, goals, keys, height bands, drawn as a bubble diagram. The
   checklist fills from it ("space:antechamber has no room"). [P: plan.yml schema; design page "The plan is the
   checklist"]
4. **Shape**: rooms drawn as outlines on the plan (or corridors as paths with a width), openings dragged across the
   gap between two rooms, stairs by a slope, levels and platforms inside a room. Walk after every few rooms. (Section
   5, W1, step by step.)
5. **Build**: themes from the texture library (filtered by texture family, the rule of REBUILD_PROCEDURE.md
   "Textures for a new dungeon"), single walls' surfaces, doors of a kind in openings, lifts, switches, chests.
6. **Wire**: events as presets with conditions and effects; links drawn from a switch to its door; the flow graph
   and the lock-and-key solve show the order the dungeon opens.
7. **Populate**: spawns and placed monsters; density and room sizes against the shipped bands (`scale_bands.py`).
8. **Dress**: lights, decorations, sounds, atmosphere and mist.
9. **Test**: walk, Play here with test switches (items and quest bits given, a test party), a headless playtest; the
   checklist and the issue list empty; the "what the measure does not see" list of REBUILD_PROCEDURE.md as a
   checklist of its own.
10. Commits with git himself.

#### F3. A modder: from installing OpenYAMM to sharing a mod (S5c for the hosted route)

1. Installs an OpenYAMM release: packages `assets/engine.zip` (1.5 GB) and `assets/worlds/*.zip`; user data lives in
   the installation folder. [P: AGENTS.md, packaging/RELEASE.md]
2. Two ways in:
   - **Hosted page** (no tools to install): opens the studio's URL in Chrome or Edge and picks the install folder
     (File System Access). The page reads the packages by byte range in a worker and never loads one whole. [P: PLAN
     9]
   - **Local mode**: the release ships `oymap`, the host and the web app (decision D12); `oymap studio` starts it. Play
     here and agents are available only this way. [P: PLAN 9 table]
3. Chooses what to make:
   - **Change a shipped map** (spawns, chests, an event's handler, a scene object): "Import" makes an overlay project
     whose `base` is the shipped map; its build writes `<stem>_<project id>.lua` and scene overlays that stack with
     other mods' overlays. [P: S2 overlay projects] (Scene overlays that add objects to a shipped map were S3 work
     and exist for handlers only [P: S2 "Not done"]; check the current state before promising more.)
   - **A new map**: as F2.
4. Builds. In hosted mode the build is written into a folder he chose; "Install" writes into the install's
   `mods/worlds/<world>/maps/` and `mods/engine/data_tables/` (the game mounts `<install>/mods` as one merged folder
   mirroring the packages). [P: AssetFileSystem::mountMods]
5. Tests: Play here (local mode), or starts the game himself (hosted: the page says it cannot start the game and how
   to). [P: PLAN 9]
6. Shares: "Export" writes a zip of the project (the source, for other modders) and a zip of the built mod folder
   (for players). **Limit until S6:** `mods/` is one merged folder and a table file in it replaces the package's whole
   table, so two mods that each add a `map_stats.txt` row clash; overlays stack, new maps do not. S5's export warns
   of it and writes a manifest draft for S6's named mods. [P: PLAN 10b item 3, S6] [N: the warning and manifest]

#### F4. Agents working alongside a person (S5a for pins, S5b for pairing)

1. The host is the one process both talk to: the browser over WebSocket, agents over MCP Streamable HTTP or through
   `oymap mcp`, a stdio relay to the running host. **Today every MCP client starts its own `host.mjs mcp` process**,
   so no host knows who else is connected; PLAN 8's relay is what gives one place to see both. [P: PLAN 8 relay; N:
   why it matters for S5] Agents mostly write files and run the command line, not MCP (0.2): they attribute their
   outside changes with `oymap record --author agent:<name> --label ...` (2.6 item 7).
2. **Pins** as in F1.
3. **Live pairing.** Both edit one project. The person's gestures and the agent's `map_edit` calls are transactions
   with an author; an agent that writes files directly appears as an "outside" change found by the host's file
   watcher within about a second. The browser shows each change as a short note on the changed objects ("agent:dress
   added 12 lights in room:crypt") and in History. [P: outside edits recorded since S2; N: watcher, notes]
4. **Conflicts.** A person's change made against an older revision is re-applied on the new one when it touches
   nothing that changed since; otherwise a banner says what clashed and offers to apply it over the other change or
   drop it (W5). Agents keep the strict rule (refused with the diff; they re-read) unless they ask for the rebase.
   [P: PLAN 5 strict rule; N: rebase]
5. **Handing work to an agent.** The person selects objects and writes a pin addressed to an agent ("make these three
   rooms a cave"); a pin is the message. No separate chat channel is built. [N]
6. **Presence.** The status bar lists connected clients (the browser, each MCP session by its client name); an agent
   sees "a person is connected and changed room:x 30 s ago" in `map_open` and in every edit result. [N]

#### F5. A hand author: a whole map by hand, dungeon or land (S5b1 indoor, S5b2 outdoor)

Someone who makes a map entirely by hand, without agents, the YAML or the command line. For a dungeon the steps are
F2's. For an outdoor map:

1. **New project**, outdoor, as F2 step 2. The project starts with described land (an empty sketch: flat grass).
2. **Land**: either described (the grid editor, ridges, cliffs, terraces: 3.18), or, after marking the project's land
   as hand-made in the UI (D15 extended), with the brush over the whole map: raise, lower, smooth and flatten strokes,
   each previewed while the mouse moves and written once on mouse-up (3.18). A heightmap made in another tool comes in
   by the heightmap import, the first addition after S5b2 (6.4).
3. **Ground**: the paint brush lays kinds of land (at most three per map, the classic format's limit), written as zone
   outlines; water, roads, buildings, scatter as W2.
4. **Wire, populate, dress, test** as F2.

What "done" means for this person: a small new map made from an empty project with no Source tab, no YAML and no
command line. Every word that forced the Source tab is listed in the phase record, and that list is the measure of G6
(6.4, S5b1 and S5b2 exit criteria). A word 3.18 promises a bespoke tool for that offers only the generic row list
counts as a miss as well (spike 7, review A7).

#### F6. Agents make the base, a person finishes it (S5b1)

1. An agent makes the map as today, often by generator scripts (0.2), through the procedures.
2. The person opens it and finishes by hand: textures, a room moved, lights, a chest's contents. **At the first source
   transaction whose author is a person, the core marks the project as edited by hand** (2.8). A person who edits
   the YAML in a text editor instead protects the project in its settings, which writes the same mark.
3. From then on an agent opening the project is told so in `project.open`, `map_open` and every edit result, and adds
   through operations, never by running its generator again. If a generator rewrites a file anyway, the change is
   recorded with an error notice listing the objects a person changed last that it replaced (and keys it dropped),
   with one step to revert that entry (2.8).
4. On land, the person's strokes are stored as differences over the described land, so the agent can still move a
   ridge or a road bed underneath and the strokes stay (3.18, D15).

Done means the mixed test of S5b1 (6.4): an agent-made map finished by hand, then an agent adds to it through
operations, and every hand edit is still there.

---

## 2. Architecture

### 2.1 What exists today

```
 Claude Code / Codex ──stdio──> host.mjs mcp ──JSON-RPC lines──> oymap serve ──> project files, assets_dev, mount
 (one host process per MCP client)          (method `run`: argv in, stdout out; stateless; one call at a time)
 browser (none yet) ──ws://127.0.0.1:8765/?token=...──> host.mjs serve ──> its own oymap serve
 game: build/game/openyamm --extra-mount <mount> (started by map_playtest, headless)
```

The host is about 590 lines of plain JavaScript modules (`host.mjs`, `core.mjs`, `tools.mjs`, `call.mjs`) with three
dependencies (`@modelcontextprotocol/sdk` 1.32.2, `ws`, `zod`) and no build step. Its WebSocket endpoint forwards
any method to `oymap serve`, which knows `ping`, `commands` and `run`. [P: S2.md; read in `host/src/`]

### 2.2 The target processes

```
LOCAL MODE (the user's machine; nothing listens beyond 127.0.0.1)

 Browser tab: the web app (static files served by the host)
 ├─ UI thread: React panels · plan view (Canvas2D/SVG) · 3D view (three.js) · stores (Zustand)
 └─ Worker: wasm core ── walk mode (movement controllers; walk.* of the request list)        [D7]
        │  WebSocket JSON-RPC (typed methods, token)   HTTP GET on the same port (meshes, textures, pictures; token)
        ▼
 oymap host (Node LTS, plain JS)
 ├─ RPC router (allow-list of typed methods, path jail)      ├─ MCP server: Streamable HTTP + `oymap mcp` stdio relay
 ├─ file watcher on open projects (not .oymap/) → status → push   ├─ session registry (who is connected)
 ├─ texture bytes: .oytex un-framed with node:zlib zstd, blocks served as they are
 ├─ pin inbox: pins written by the game's `pin` command, imported into each project's pins document
 ├─ job queue (builds to install, compare, renders, tours, playtests, Python checks)
 └─ game bridge (Play here, playtests, screenshot tours)
        │ JSON-RPC lines on stdio                  │ JSON-RPC lines on stdio          │ spawns
        ▼                                          ▼                                  ▼
 oymap serve, lane I (interactive)          oymap serve, lane J (jobs)        openyamm (game); calibration/*.py
 cache keyed by (project, source revision)  same binary, own cache
        │                                          │
        ▼                                          ▼
 project folders (the truth) · <project>/.oymap/ (history, cache files) · asset root (assets_dev or an install) · mount

HOSTED MODE (a static page; no server, no host)

 Browser tab: the same web app
 ├─ UI thread (as above)
 └─ Worker: wasm core with every RPC method of lane I and the builds of lane J
        ├─ asset reads: PhysicsFS over a JavaScript byte-range reader (File handles, FileReaderSync, OPFS)
        └─ project files: File System Access directory (Chromium) or OPFS working copy; zip import and export
 optional: pairing with a local host over ws://127.0.0.1 with a pasted token (Chromium and Firefox; not Safari)
```

Rules that do not change [P: PLAN 1, 3, 5, 8, 14]: the files are the truth; the host holds no map logic and no
document state; there are exactly two builds of the core (native, wasm); native and wasm builds of the same project
give the same bytes; the host never loads wasm. **The change [D7]:** the browser loads the wasm core in local mode
too, for walk mode. It never edits or builds through it in local mode; the authoritative path is the host. Walk is a
group of the request list (2.3), so if the wasm walk fails its spike, lane I (or a third lane) serves the same methods
natively and nothing else changes. Textures do **not** go through wasm in local mode: the host un-frames the zstd
itself and serves the blocks (2.11), so a broken wasm build never blanks the textured view. [Review A7, D7]

### 2.3 One typed RPC catalogue [N, D2]

Today the browser endpoint would pass argv strings to a command line and parse its stdout. That cannot be the
lifetime interface: no types, stdout formats that change with each batch, and any argument the browser sends becomes
a command line (`--out` anywhere on disk). Proposal: a catalogue of methods with JSON Schemas for parameters and
results in `openyamm-studio/schema/rpc/`, compiled into the core like the project schemas are, with TypeScript types
generated from them for the web app. The same catalogue is:

- served by `oymap serve` (native) over stdio lines;
- exported by the wasm build as one C function (`oymap_call(method, json) -> json`) plus transferable buffers for
  bulk data [P: PLAN 3 "a C ABI with JSON in and out ... plus transferable ArrayBuffers"];
- wrapped by the MCP tools (each tool calls one or a few methods; tool texts stay as tuned by the evaluation).

The command line keeps its commands; each becomes a thin printer over the same functions (most already are).
**In the same phase** the MCP tools and the command line move onto the list, and `oymap call <method> <json>` calls
any method from a shell, so `run` with argv does not live on beside the list as a second interface. [Review A7, D2]

Rules of the list [Review A7, D2]:

- **Numbers in results are rounded by rule** (world units to integers, angles and fractions to a stated number of
  decimals, per field in the result schema), or the native-against-wasm suite fails on the last digit.
- **Every job that prints has an output schema in the list**, the Python checks included (D10): `town_feel.py
  --json`, `scale_bands.py`, `compare.py` and the rest declare what they return. Otherwise stdout is the interface
  again.
- **Ids are core business**: a method that creates an object may leave the id out; the result names the id the core
  allocated (2.6).

The methods S5 needs, by group:

| Group | Methods | Notes |
|---|---|---|
| session | `hello` | core version, schema formats, capabilities (mode, game present, jobs present, asset root) |
| project | `list`, `open`, `read`, `resolve`, `status`, `new`, `import`, `fmt`, `record` | `open` returns every file's canonical tree as JSON, the source revision, ids, issues, and the hand-edit mark (2.8); `resolve` (S5b1) is the resolved read of one object or sub-object: every field's **effective** value as the lowering decides it (written, the lowering's default, or derived from the kind or the world), with where it came from, which the inspector shows instead of the schemas' `default` copies (3.8) [spike 7, review A7]; `record` attributes an outside change to an author with a label (2.6) |
| edit | `edit`, `rename`, `history`, `undo`, `redo`, `revert_entry` | `edit` takes `ops`, `expect_revision`, `dry_run`, `allow_errors` (agents and tests only), `author`, `label`, `merge_key`, `rebase`; `undo`, `redo` and `revert_entry` all append a revert entry (2.7) |
| pins | `list`, `add`, `claim`, `reply`, `resolve`, `accept`, `reopen`, `import_inbox` | the pins document (2.4.1, 3.13), with its own change counter |
| walk | `load`, `step`, `toggle` | served by the browser's wasm worker; natively by a lane if the wasm spike fails (D7) |
| view | `layout`, `mesh`, `map_mesh`, `terrain`, `terrain_query` | resolved positions and boxes of every id; built meshes with face provenance (2.9); `terrain_query` (S5b2): height at a point, a profile along a line, slope, how agents read land made by hand (3.18) |
| check | `validate`, `audit`, `reach`, `solve`, `flow_event`, `things`, `coplanar`, `metrics` | tier 0 inside `edit`; the rest on lane J in the background |
| compare | `compare` | indoor rays or outdoor layers; report, points or regions, shots |
| assets | `search`, `texture`, `decoration`, `model`, `tables` | `tables`: house, monster, item, quest-bit names the pickers need |
| build | `build`, `install` | `install` into the mount, the outdoor material file included |
| game | `play`, `playtest`, `tour` | host only; none in hosted mode |
| jobs | `start`, `status`, `cancel`, `list` | host only |
| notices (server to client) | `revision_changed`, `pins_changed`, `job_progress`, `job_done`, `client_joined`, `client_left` | over the same WebSocket; `pins_changed` carries the pins counter, never a revision |

Bulk results (meshes, textures, pictures) are not JSON: in local mode the result carries a URL on the host's HTTP
port (`/mesh/<project>@<revision>/<part>`, `/tex/<world>/<name>`), cached by revision; in hosted mode the worker
returns transferable `ArrayBuffer`s. The byte routes require the pairing token too (2.12). As a cache and URL key the
revision is a longer hash than today's 12 hex digits of FNV-1a (which stay fine for noticing a change): a 128-bit
content hash. [Review A7 3] S5-0 did not choose it: the request list treats the revision as opaque (12 to 64 hex
digits), so the hash is chosen with S5a1's source revision without a version change.

**Version 1, from S5-0's spike 4** (kept in `openyamm-studio/schema/rpc/`; S5.md) [revision 4]. Methods:
`session.hello`, `session.configure` (host or worker only, never exposed), `project.open`, `project.read`,
`project.status`, `edit.apply` (`add`, `set`, `remove`, `patch`), `check.validate`, `check.things`, `build.run` (a dry
run, or into the project's `build/`), `pins.list`. Names are `<group>.<name>`; the table above names the groups'
methods by their second part (`edit` is `edit.apply`, `build` is `build.run`). Each method records `summary`, `since`,
`lane`, `backends`, `exposed`, `writes`, `assets`, `errors`, `params` and `result`; `gen.mjs` lints the catalogue and
generates the TypeScript types (`--check` fails on a stale generated file, in CI). Choices it fixed:

- **A validation layer, not generated C++ structs**: the RPC schemas are embedded like the project schemas, params
  are checked by the core's schema validator before the handler, results by the contract suite.
- **Errors**: JSON-RPC codes (-32700, -32600, -32601, -32602, -32000 for a refusal, -32603 for a core failure) with
  `data.kind` per error; a refusal is a typed error, never `ok: false` (except `check.validate`, whose answer is the
  issue list).
- **The asset root belongs to the session** (`session.configure`, `serve --assets`), never a param; no method takes an
  output path; `project` is a path the host's jail maps.
- **Version 1 promises only what the core does today.** `author`, `label`, `merge_key`, `rebase`, core-allocated ids,
  `rename`, `replace_file`, `set_value`, the pins counter and `x-key` pointers are additions in their phases and keep
  the version number; until `x-key`, keyed pointers use `id`. An object's `/id` and `ids.lock.yml` cannot be patched.
- **`edit.apply` returns the canonical tree of every changed file**, on a dry run too, for the client's own copy.
- **Results**: closed objects (except trees and maps); every non-integer number states `x-decimals`; world positions
  integers; no absolute paths (today's core messages carry some: `missingWorldNote`, project and preview folders;
  a rule for the core's messages, S5a2).
- **Operations carry the file where an id is in more than one** (ids are unique per file, 2.6 item 11).
- **Later**: an `x-discriminator: op` hint on the operation union, so the generated types and forms tell the
  operations apart by `op`.

**Contract test** [N]: one suite of RPC calls with expected results runs against native `serve` and against the wasm
build under Node, and the two must agree byte for byte on everything but timings. It is the S5 form of
`tests/native_vs_wasm.sh`, and it includes a recorded walk replayed on both, which must give the same poses; the walk
includes a map with a rotating mover (spike 3: the movers' rotations are where C-library trigonometry could still
differ). **It keeps one wasm instance alive across all its calls**, as the browser worker does (spike 4: an iterator
bug that natively did nothing crashed a long-lived instance), and gains cases for the `locked` and `failed` refusals.
Spike 4's suite (40 calls on three example projects, read-only calls on real projects with `--project`) is its start.

### 2.4 `oymap serve` as a caching service, in lanes [N, D1]

Measured (appendix C), two sets. This document's first runs: `validate` 0.20 s (the Mad Necromancer's Lab), 0.98 s
(Castle Darkmoor, 267 rooms), 1.30 s (New Sorpigal, outdoor); `build` 0.46 s, 2.13 s and 0.99 s; 34 to 72 MB.
Review A7's runs (load average 1.4; the Darkmoor validate of 0.98 s did not reproduce):

| Project | load + parse + canonical text | validate, no assets | validate with assets | build | one real `oymap edit` |
|---|---|---|---|---|---|
| Goblinwatch | 0.09 s | 0.18 s | 0.31 s | | |
| Castle Darkmoor | 0.11 s | 0.24 s | 0.50 s | 0.83 s | 1.0 s |
| New Sorpigal | 0.09 s | 0.31 s | 0.73 s | 0.51 s | |
| Erathia (largest sketch) | 0.13 s | 0.20 s | 1.64 s | 1.59 s | |

What they say (review A7 1.2): starting the process costs 3 ms; parsing about 250 KB of YAML costs 0.1 s; indoors, a
cached tree and cached tables leave about one lowering (0.15 to 0.25 s) per edit, so 300 ms looks reachable without
incremental validation. Outdoors, validation with assets **is** a full build (1.64 s against 1.59 s on Erathia), and
how much of it a cache removes is not known. `map_edit` validates before and after, so one edit costs about 1 s
indoors today. (S5-0's spike 2 measured both with a cached service: 2.4.3 and S5.md.)

#### 2.4.1 What the revision covers: three classes of file (before the cache) [Review A7 1.1]

Today the revision hashes every file of `projectFileKinds()`, pins and the id lock included (0.2). With that, each pin,
reply and claim would change the project's revision, drop the mesh cache, grey the scorecard and make an agent's
`expect_revision` stale because the user commented; and Play here (build and install) rewrites the lock, so the
user's next Ctrl Z finds a `build` entry on top, and undo could roll back engine numbers, which the lock exists to
prevent ("a number once given stays"). So, as core work **before** the cache of the next item, which is keyed by it:

| Class | Files | Revision | History and undo | Written by |
|---|---|---|---|---|
| **Source** | `project.yml`, `plan.yml`, `sketch.yml`, `rooms.yml`, `objects.yml`, `wiring.yml`, `atmosphere.yml` | the **source revision** is the hash of these alone; caches, `expect_revision`, history, undo and rebase see only it | yes | the core through operations; any tool (then recorded as outside) |
| **Record** | `ids.lock.yml` | hashed separately, as part of the built bytes' identity (a build is source revision plus lock hash) | **never undone**; a lock change is not a history entry; the numbers of removed ids are kept until a prune (below) | builds (and `import`) only, `oymap lock prune`, under the project lock; a change from outside (a `git checkout`) is taken as the new record and noted in the host's log, never put in the undo history |
| **Review** | `review/pins.yml` | none; its own change counter | its own append-only log in `.oymap/pins/`, outside the map's undo | the core's pins methods; the inbox import |

`projectFileKinds()` gains the class; `projectRevision()` hashes the source class; `syncOutsideEdits()` looks at the
source class only, so the `build` entries of `core/Ops.cpp:424` disappear. Migration: on first open after the change
the history head is re-keyed to the source revision (an explicit step, logged). Lua handlers live inline in
`wiring.yml` (the `lua` field), so no `scripts/` folder needs a class.

Taking the lock out of the history is not enough on its own; two more rules make "a number once given stays" hold
through undo. The first is core work of S5a1, with the three classes; the second is a rule for rename and revert
entries, built with them in S5b1, and fixed here so that S5a1's file classes do not contradict it. [Review A7 5,
points 1 and 2]

- **The lock keeps the numbers of removed ids until an explicit prune.** Today an indoor build drops the entry of
  every id the project no longer has (0.2). So: remove a door, press Play here (the build writes the lock), undo, and
  the door comes back with a new engine number, the renumbering the split was meant to prevent, by another route. The
  build stops forgetting: an entry whose id is gone (a removed door, a door's second leaf after it lost it, a deleted
  variable) stays in the lock with its number, which no other id is given, and an undo that brings the object back
  finds it there. Entries are dropped only by **`oymap lock prune <project>`** (`project.lock_prune` in the request
  list), a deliberate step by a person or by a procedure (before sharing or shipping a map), never by a build or an
  undo; it drops the entries of ids no source file has, by today's rule of what is live, and is written like any lock
  change (a record, not a history entry). The reason the code forgets today, a map's 75 variables running out after
  renames, is covered by the next rule (a rename moves the entry, it leaves none behind) and by the prune: when a
  table has no free number left, the build's error names the retired entries and the prune.
- **Undo never changes a number.** A rename re-keys the lock entry and the pins (2.6 item 4). Reverted object by
  object (2.7), it would put the old name back in the source and leave the lock under the new one, so the object
  would get a new number. So **a revert of a rename runs as the opposite rename** (the undo of `rename {from: a, to:
  b}` is `rename {from: b, to: a}`; its redo is the first rename again), and **names in the lock and in pins follow
  renames in both directions**. A revert entry may move a lock entry under another name; it never gives, changes or
  drops a number. A rename written by a file edit (a generator that changes an id) is not seen as a rename: the new id
  gets a new number and the old entry stays until a prune; generators that rename use `oymap edit` with `rename`.

#### 2.4.2 Validation is the lowering: severities and a lowering that skips [Review A7 1.2]

Because `validateProject()` lowers the whole project and a build refuses any issue, the first draft's "incremental
validation, schema checks per changed file, under 0.15 s" is not available (the cost is the lowering, not the
schemas), and its "the browser commits with issues" (2.6 item 4) would give a blank 3D view in the most common state
of authoring. Changes, all core work, listed in phases S5b1 (per room) and S5b2 (per structure) (6.4); the
severity field itself comes earlier, in S5a2:

- **Issues get a severity**: `error` (the map cannot be built as written), `warning` (it builds, but a rule of the
  procedures is broken: unreached room, silent click), `note`. Only errors stop a build to install. **The first rule
  exists** (S5-0, spike 4): `checkSketch` reports `heights` and `coverage` issues that `build` already treats as
  warnings (Erathia has 166 and builds), so `check.validate` and `build.run` disagree today. The severity is set where
  each issue is found, not by its code, since the `heights` code also raises issues that must stop a build (the
  twenty-third merge left it to S5a2 for that reason).
- **Severities first outdoors** (S5-0, spike 2) [revision 4]. Today `validateProject` lowers an outdoor project only
  when the sketch checks found no issue, so Erathia's 166 warnings switch its lowering off and an edit there checks
  nothing; and it never passes the asset root outdoors, so `oymap validate --assets` runs a second full dry build.
  With severities only errors stop the outdoor lowering, and `validateProject` takes the asset root outdoors as it
  does indoors: one dry build per check, not two. In S5a2, with the severity field.
- **The lowering skips an object it cannot lower**, reports it as an error naming the object, and builds the rest:
  per room indoors (with the openings and objects that need that room), per structure outdoors. The result is a
  **view build**: it feeds `view.mesh` and `view.layout`; `install`, Play here and playtests refuse a project with
  errors, so a partial map never reaches the game. **It also skips objects with schema issues** (S5-0, spike 2): today
  a schema issue ends `validateProject` before the lowering starts, and one issue anywhere stops the whole lowering
  (`Lowering::run` returns once any issue was added), so one room with two points or no `floor` gives a view of 0
  faces. Schema issues are attributed to their object, and that object alone is skipped.
- **Outline messages say what is wrong** (spike 2): a bow tie and three collinear points are reported today as "must
  run counter-clockwise"; they get "crosses itself" and "has no area". With the skipping lowering, S5b1.
- **The client keeps the last good mesh of a skipped object** and draws it marked stale (hatched), with the error in
  the Issues drawer.
- **A word that does not apply to the object's kind is a warning** [spike 7, review A7]. Today a structure item
  (`structures[].items`: 156 properties over 28 kinds) has one `additionalProperties: false` for the whole item and no
  per-kind check, so a word written on the wrong kind validates and is silently unused. The core reads the same
  `x-discriminator` and `x-kinds` annotations from the schema that the form reads (3.8) and reports "word X does not
  apply to kind Y" as a warning. Before the check lands it is run over the 22 projects: every hit is either a wrong
  guess in the kind table or a dead word in a project, and each is settled one way or the other. The run checks one
  direction only (a word used where the table excludes it); a table that allows a word the lowering ignores is caught
  by the lowering's read record (3.8: "word X was never read on this object") and, for words read without effect,
  by the second agent's check of the annotations. In S5b1 for the indoor kinds, S5b2 for `sketch.yml`.
- Until the skipping lowering exists, the browser refuses a person's edit that adds errors (as agents' edits are
  refused today) and D3's old item 4 does not apply.

Spike 2 measured how the lowering behaves on a half-drawn room (S5.md): nothing crashed; nine half-drawn states each
stopped the lowering at the first issue; early stops cost 94-190 ms against 265 for a full lowering.

#### 2.4.3 The service

- **Cache by source revision.** `serve` keeps, per open project, the parsed project, its validation result, the asset
  tables and catalogue (once per asset root), the last build in memory and its layout and meshes, each keyed by the
  source revision (2.4.1). The files remain the truth: before any write the core checks whether the files it read
  changed. **Staleness is found cheaply**: file size and modification time first, then a hash of the raw bytes; the
  canonical text (which costs the 0.1 s parse) is computed only for a file that really changed. On a change it
  records the outside entry as today and drops that project's cache. [Review A7, D1]
- **What the cache keeps, and the three conditions of the indoor budget** (S5-0, spike 2) [revision 4]. The
  indoor commit meets 300 ms (275 / 294 / 300 ms median, p95, max on Darkmoor at load 12) only when: (1) the asset
  tables are kept **parsed, with their lookups**, once per asset root, not only their text (today's lowering makes
  2 050 decoration lookups, each scanning `decoration_data.txt` line by line, plus 6 table parses: 118-135 ms per
  lowering; kept as parsed lookups, 1 ms); (2) an edit validates **once** (today's edit validates twice and parses
  everything three times); (3) the schemas run on **the changed files only** (34 ms against 53). The rest of an edit
  is the lowering (150 ms), cross-file checks (23), canonical text and re-parse of the changed file (37), the diff
  (10). The margin is thin; the next savings, in order: validate only the edited tree (about 19 ms), plan references
  on the changed file only (23 ms), then per-room lowering (PLAN 6 tier 1). The number is re-measured on a quiet
  machine before S5a2 builds the cache (S5.md, "Still open").
- **No incremental validation in S5a or S5b1.** With a cached tree and tables, one lowering per edit is the cost; the
  tier 1 "incremental compile keyed by content hash per room or terrain chunk" [P: PLAN 6] stays the next step.
  Spike 2's split says the outdoor budget of S5b2 does not need it either, but needs two narrower changes:
- **Outdoors, the land is kept** (spike 2, for S5b2). Of an Erathia edit's 1 303 ms, the land lowering is 840 ms
  (smoothing 447), and none of it depends on structures: buildings reach the land only in `levelPlots`, node blocks
  only in `setNodeBlocks`, both after the smoothing (from reading `Lowerer::run`, not measured). So the cache keeps the
  land **up to the peaks**, keyed by a hash of the land words without `nodes` (and without the stroke word of 3.18,
  applied after it like `nodes`); a structure edit or a brush stroke then skips about 830 ms. And **the scene write and
  its reader check (238 ms) leave the commit**: they are build checks, and a commit's issue delta does not need them.
  With both, S5b2's outdoor commit budget is 500 ms (2.13). Until then the outdoor budget is 1.5 s.
- **The client does not wait for the core to redraw.** It applies its own `patch` to its copy of the file at once (the
  files are plain JSON trees; no game rule is involved), redraws the plan, then reconciles with the core's answer: the
  core's tree replaces its copy, and a refusal rolls the copy back with the reason. The core's time then governs only
  issues and 3D (2.13). [Review A7 1.2] **The exception: an `add` whose id or key the core allocates** (2.6 item 5)
  cannot be applied ahead of the answer, since the client may not invent the name; it draws the new object as a ghost
  and puts it in its copy when the answer's `ids_allocated` arrives. [Review A7 5]
- **Two lanes.** The host starts two `oymap serve` children of the same binary: lane I answers the browser's reads
  and edits; lane J runs whatever takes more than about a second (builds to install, `compare`, `audit --reach`,
  `solve`, renders, tours, the Python checks). A twenty-minute picture job never blocks a click. The core stays
  single-threaded and deterministic [P: PLAN 3 "no pthreads at first"]; processes are the simplest isolation. Both
  lanes take the project lock file for writes (it exists: holds the writer's process id; a dead writer's lock is
  taken over [P: S3 Findings]).
- **Push.** The host watches every open project folder (Node's recursive `fs.watch`, debounced 200 ms) **except
  `.oymap/`**, where jobs and history are written, **and `build/`**, where the indoor dry build writes and removes its
  GLB (S5-0, spike 2; until the view build stops writing files); asks lane I for `status` (which records an outside
  edit as a history entry) and sends `revision_changed` to every connected browser with the author and the semantic diff lines.
  The MCP side gets the same facts in its next result. Outside edits from generators arrive file by file: changes
  inside the debounce window are merged into one entry. **A file that does not parse** (a generator half way, a typo
  in a text editor) keeps the last good tree in the browser, with a banner naming the file and the parse error; the
  project is read only until it parses. [Review A7, D1]
- **Jobs.** A job has an id, a kind, the project and revision it ran on, progress lines and outputs (files under
  `<project>/.oymap/jobs/<revision>/<job>/` [N]). Results are shown against the revision they belong to; a picture of
  an older revision is labelled so. PLAN 8 planned jobs and MCP Tasks; S2 did not make them because builds answered
  within a call. S5 needs them for `compare` (tens of seconds), `building_shots.py` (about 35 minutes for two maps)
  and playtests. [P: PLAN 8; S2 "Not done"] **Cancelling a job kills lane J** (the core is single-threaded; there is
  no cooperative stop) and the host restarts it; every write a job makes is atomic (temp file and rename, as the core
  does today), so a killed job leaves no half file.
- **The view comes from the edit's own lowering, not a dry build** (S5-0, spike 2) [revision 4]. The indoor dry
  build writes its GLB into `<project>/build/source/<stem>.glb` and removes it (35-45 ms with the compiler's import),
  then compiles, builds the BSP and outlines (283-299 ms, 37-41 % of it) and runs the build checks: 749 ms median and
  1 556 ms p95 on Darkmoor, against the 1 s budget for 3D after a commit. None of it is needed for a view: all 4 659
  compiled faces of Darkmoor are its lowered faces with rounded corners, in order (the compiler adds, drops, merges and
  splits none). So `view.mesh` and `view.layout` are made from the lowering the edit already ran, with the corners
  rounded as the compiler rounds them; the compiler, BSP, outlines and the GLB run only for install, Play here and
  playtests. Outdoors the view build adds about 200 ms to the commit.
- **Hosted mode has one worker** [decision, after review A7]: two wasm instances would double the tables against the
  1 GB budget, and one instance cannot be interrupted. So in hosted mode background checks do not run by themselves;
  they run on request with a visible "checking" state during which edits wait. A second worker for checks is allowed
  only on maps whose measured heap leaves room (S5c measures it).

### 2.5 Data flow

**Opening a project.** `hello` → `project.open` (files as JSON trees, revision, ids, issues) → `view.layout` and
`view.mesh` (plan first, then untextured 3D) → textures by URL, lowest mips of every texture first, then the rest
(S5-0, spike 1: Darkmoor textured at 181 ms instead of 375) → lane J starts `audit --reach`,
`solve` and, for rebuilds, `compare`; the scorecard fills as they finish.

**An edit gesture (for example moving a room's corner).**

```
pointer down on a handle ─► client draws a ghost (no RPC; snapping to grid and walls on the client)
pointer up ─► ops = [{op: patch, id: room:hall,
                      patch: [{test: /outline/2, value: [old]}, {replace: /outline/2, value: [new]}]}]
                      (outline points are a plain list: position plus test; keyed lists use keys, 2.6)
          ─► client applies the same patch to its own copy of rooms.yml and redraws the plan at once
          ─► edit {ops, expect_revision: r1, author: "user", label: "move corner"}
lane I    ─► apply to the cached tree · lower (cached tables) · write files (temp file + rename, under the lock)
             · history entry
          ─► result {revision: r2, changes: ["rooms.yml: room:hall changed outline"], new_issues, fixed_issues,
                     files: {rooms.yml: <tree>}, ids_touched: [room:hall]}
client    ─► replaces its copy with the core's tree (or rolls back on a refusal, with the reason)
             · asks view.layout and view.mesh @r2
lane I    ─► view from the edit's own lowering (no compile, BSP or GLB: 2.4.3; skipped objects reported, 2.4.2)
             · client swaps the 3D mesh
host      ─► revision_changed to the other clients (agents learn it in their next call)
```

**A change from outside** (an agent's file edit, a text editor, `git checkout`): host watcher → `status` on lane I
(records "outside" with its diff) → `revision_changed {author: "outside"}` → the browser reloads the changed files'
trees and shows the note.

**A preview the ghost cannot show** (a roof pitch, a slope, a scatter's result) [N]: `edit` with `dry_run: true,
preview: true` builds into a private folder and returns a mesh URL for that dry state; the client shows it as a
translucent overlay. Debounced to one request in flight.

### 2.6 Documents, operations, transactions [P: PLAN 5, S2] and what S5 adds [N, D3]

What exists: a transaction is a list of operations applied all or nothing; operations are `add` (or `<kind>.add`),
`set` (fields, `null` removes one), `remove`, `set_value` (a path in a file outside the lists); the result is the
semantic diff, the issues introduced and fixed, and the new revision; a change that introduces issues is refused
unless `allow_issues`; `expect_revision` refuses a stale write; history keeps the files before and after each change;
an outside edit is found on the next read and recorded.

What a UI needs that is missing, and the proposal:

1. **Every list is a collection, from the schemas.** Today a hand-kept table in `core/Ops.cpp` names 29 collections;
   `sketch.yml` has none, and `ladders`, `sounds` and `relations` of `objects.yml` are missing. Proposal: derive the
   table from the schemas: **every top-level array whose items have an `id`** is a collection, so a new list is
   editable when its schema lands. (The first draft said "marked `x-sort: id`"; `sketch.schema.json` has no `x-sort`
   at all, so that rule would give nothing for outdoor maps. [Review A7, D3]) Sub-objects inside an object are
   addressed by `patch` (next items). [N]
2. **Keys for everything a person can select or pin.** [Review A7 1.3] `sketch.schema.json` has 57 lists of objects,
   of which 11 carry an `id`; `rooms.schema.json` 14 and 6. Addressing the rest by position breaks as soon as a list
   shifts: a pin or a selection on "part 3" points at another part after someone inserts one, every rebase fails, and
   the provenance table (`thing:building_2` part `p3`) and the patch (`/parts/3/...`) disagree about names. So, in the
   format bump of 2.15, **every sub-object a person can select or pin gets a key unique within its parent**, and the
   schema marks the key field with `x-key`. Parts already carry local ids (`id: p3`); platforms, levels, pillars,
   flights, beams, porches, plots, scatter entries, height features (points, cliffs, ridges, terraces, spires, peaks,
   cuts), roads, effects and conditions get one. A key is short and local (`p3`, `west_ridge`); the full address of a
   sub-object is its owner's id and the path of keys (`thing:building_2/parts/p3`), which pins, selections and
   provenance all use. Plain lists whose items nobody selects alone (outline points, bays of a wall, a road's points)
   stay positional and are always patched with a `test` of the old value. The core allocates a key when the client
   gives none. **Keys are optional in files** [Review A7 5 point 3]: most maps are written by agents' generators,
   which emit no keys, and a required key would break every generator at S5b1. So the schema never requires an `x-key`
   field; a missing key is read as the key the core would give it (derived from the kind and the position), and the
   core writes it into the file on its next write of that file (an edit, `oymap fmt`, a migration). **A known limit of
   generated projects:** a generator that rewrites a file without keys makes that file's keys positional again, so a
   pin or selection on one of its sub-objects may move to another after an insertion (the pin keeps its pose). A
   generator that wants stable keys reads them back and emits them.
3. **`patch`: change part of an object.** An outline's third point, one wall's bays of a building's part, one effect of
   an event: today only `set` of the whole field. Proposal: `{op: patch, id: <id> | file: <file>, patch: [JSON Patch
   operations]}` with pointers into the object's (or the file's) canonical tree. **A pointer segment into a keyed list
   is the key, not a position** (`/parts/p3/walls/s`, `/heights/ridges/west_ridge/height`); positions remain only in
   plain lists. This **departs from RFC 6901**, where an array segment is always a number or `-`: our pointer resolver
   reads a segment into an `x-key` list as a key, and `-` still appends. The rest is RFC 6902 as published (`add`,
   `remove`, `replace`, `move`, `copy`, `test`). `test` steps make a patch safe against concurrent changes at the value
   level. [N] **`heights.nodes` needs it first among the files' fields** (S5-0, spike 2) [revision 4]: today only
   `set_value` of the whole list reaches it, so a brush stroke of 63 nodes sends Erathia's whole node list (16.8 KB)
   and rewrites it. Its node blocks (and the stroke word of 3.18, same block and row form) are addressed by a keyed or
   path `patch` into the block and row the stroke touched. A stroke is **one commit**, sent on pointer up; the client
   draws the stroke until then (3.18).
4. **Rename.** `rename {from: room:hall, to: room:great_hall}` (or a key within its parent) is one transaction that
   updates every reference in every source file, the id lock's entry (so the engine number stays with the object) and
   the pins that name it. Without it a person's first rename breaks the map. Its undo is the opposite rename, so the
   lock and the pins follow it back (2.4.1). [Review A7 1.3; 5 point 2]
5. **Ids allocated by the core.** An `add` without an `id` gets one from the core (`<kind>:<base>_<n>`, the base from
   the kind or the space the object is in), returned in the result's `ids_allocated`. The client never invents ids,
   so two writers cannot pick the same one. [Review A7 1.3]
6. **Merging repeated edits.** A transaction may carry a `merge_key` (`"floor room:hall"`, `"drag door:gate
   speed"`). The core folds it into the previous history entry when that entry has the same author and merge key, is
   the latest entry, and is less than a few seconds old. Ten presses of PgUp or a dragged number make one entry, so
   the 1 000 kept entries (2.7) are not twenty minutes of work. This amends an entry, so it is **the one exception to
   the append-only history** (2.7). [Review A7 1.3; 5]
7. **Author and label.** Every transaction carries `author` (`user`, `agent:<client name>`, `outside` for edits found
   on disk) and a short `label`; history entries keep both. **Agents mostly write files and use the command line**, not
   MCP (0.2), so authorship cannot rest on the MCP relay: `oymap record <project> --author agent:<name> --label
   "<what>"` records the outside change now on disk as one entry with that author (the procedures tell file-writing
   agents to run it after each generator run). [N; review A7, D3] **It races the host's watcher** [Review A7 5 point
   4]: the watcher records the generator's change as `outside` within 200 ms (2.4.3), and `record` a moment later would
   find nothing new. So `record` also takes the **unattributed `outside` entries since that author's last entry** and
   puts its author and label on them. It changes only the author and label of those entries, never what they changed,
   and it lists the entries it took, so an edit by another tool in the same window that it claims by mistake is seen.
8. **Issues and a person's edits.** With severities and the skipping lowering (2.4.2), a person's edit that adds
   warnings is written and the delta shown in the Issues drawer; one that adds errors is written too, and the skipped
   object shows as stale in 3D. Until the skipping lowering exists, a person's edit that adds errors is refused like an
   agent's. Agents keep refusal on errors by default (`allow_errors` for tests and deliberate steps). (The first
   draft's "the browser commits with `allow_issues`" is replaced: without severities and skipping it gave a blank 3D
   view.) [N; review A7 1.2]
9. **Macros in the core** for the named operations PLAN 5 wanted (`room.add` attached to a wall, `opening.between`,
   `door.in_opening`, `stairs.between`, `building.add` with a door to a road, ...). A macro expands, in the core, into
   generic operations, and the history records the expansion. A macro is written only when a UI tool and an agent
   both need it, so neither front end grows its own copy. [P: PLAN 5 operations; README decision "the engine's C++
   is the only implementation"] [N: macro form]
10. **Text edits are operations too.** The Source tab sends `{op: set, id, fields: <whole object>}` or, for a
    file, `{op: replace_file, file, text}` (validated and written in canonical form). [N]
11. **Ids are unique per file, not per project** (S5-0, spike 4; the twenty-third merge) [revision 4]. A plan space
    and its room may share an id (`room:entry` in `plan.yml` and in `rooms.yml`), and `oymap edit` took the first one
    it found, so a `set` meant for the room edited the plan's space. Now `set` and `remove` take a `file`, an id found
    in two files without it is refused, and `add` checks only its own file. So everything that names an object carries
    its file where the id alone is not unique: operations, pins (3.13), selections, the provenance table (2.9) and the
    full address of a sub-object (for example `rooms.yml#room:entry/platforms/<key>`; the written form is fixed with
    pins format 1 in S5a1). Ids allocated by the core (item 5) are unique within their file.

### 2.7 Undo, redo and conflicts with agents' edits [N, D4]

What exists [P: PLAN 5, S2, `core/Ops.h`]: history entries (transactions and outside edits) with the files before and
after; a cursor and an `undone` flag; `undo` restores the files as before the latest entry not undone, `redo` the
reverse; both work on outside edits.

The problem in a shared project: the latest entry is often not yours. A person's Ctrl Z must not undo the agent's
last edit, and restoring whole files from a snapshot would also undo everything else written to those files since.

The first draft (D4 as first written) kept the cursor undo for "your entry when it is also the latest" and added a
selective revert for the rest. Review A7 1.4: that is two mechanisms with different results for ever, and redo of a
revert is undefined in the cursor model. **Replaced by one model** [Review A7 1.4]:

- **The history is append-only.** Nothing is ever marked undone or cut off; every change, undo and redo is an entry.
  **The one exception is `merge_key`** (2.6 item 6): a repeated edit is folded into the latest entry when it has the
  same author and merge key, which amends that entry. (`oymap record`, 2.6 item 7, sets the author and label of
  unattributed outside entries; it never changes what an entry changed.) [Review A7 5]
- **Undo is a new entry that reverts one earlier entry, object by object.** For each object (or, in files outside
  the lists, each field path) the reverted entry changed: if its canonical text now equals what the entry wrote, it
  is put back as it was before the entry; if someone changed it since, it is listed as a conflict and left alone
  unless the person confirms. The entry records `reverts: <sequence>`, author you, label "undo: <label>".
- **Redo reverts the undo** (an entry with `reverts: <the undo's sequence>`).
- **Each author's position is derived from the log**: Ctrl Z takes the author's latest entry that is neither an undo
  nor already reverted; Ctrl Y takes the author's latest undo not yet reverted, as long as the author made no new
  change after it (a new change ends the redo chain, as in every editor). Nothing about positions is stored.
- **A revert is validated like any transaction.** "Nobody changed this object since" does not cover everything: an
  agent may have attached an opening to the room a person's undo would remove. The revert runs the same checks; a
  revert that would add errors is refused (or, for a person, shown with the errors and applied only on confirmation).
- **The snapshot restore stays as the test oracle**: reverting the latest entry must give the same bytes as restoring
  that entry's before-snapshot. The unit suite checks it on every kind of operation.
- **The id lock and pins are never undone** (2.4.1): they are not in the source history at all. **Undo never
  changes a number**: the lock keeps a removed id's number until an explicit prune, so an undone removal gets its
  number back, and the revert of a rename runs as the opposite rename, so the lock entry and the pins follow the name
  back (2.4.1). [Review A7 5 points 1 and 2] **Nor does undo clear the hand-edit mark** (2.8): reverting the entry
  that set it reverts the hand edit and leaves `edited_by_hand` in `project.yml`; only a person clears it.
- **A stale transaction is rebased.** `edit` with `rebase: true` (the browser always sets it) re-applies the same
  operations on the current revision when none of the objects they touch changed between the expected and the current
  revision, or when their `test` steps still hold; with keyed pointers (2.6) a shifted list no longer breaks a
  rebase. Otherwise it refuses with the diff since and the clashing objects; the browser shows W5's banner: "Show
  both", "Apply mine over theirs", "Keep theirs".
- **Autosave is the model.** Every gesture is written; there is no unsaved document. Only an unfinished gesture and a
  field being typed in (committed on Enter or leaving the field) live in the browser. A crash loses at most that.
  [P: design page "autosave"]
- **Storage: each file version once, by its hash, compressed.** Today an entry keeps whole before and after copies of
  each changed file: one edit of Darkmoor's rooms wrote 330 KB (review A7), so 1 000 entries are 330 MB per project.
  Instead, `.oymap/history/blobs/<hash>.zst` holds each distinct file text once, compressed with the zstd the core
  already links; an entry names the blob hashes of the files it changed, before and after. Consecutive versions of a
  4 000-line file share most of their bytes, which a later step may exploit (zstd dictionaries or deltas); the first
  step is hash and compress.
- **Retention.** Keep the last 1 000 entries and named checkpoints; blobs no kept entry names are pruned on open. [N]

### 2.8 File formats and what is the truth

| What | Where | The truth? | Written by |
|---|---|---|---|
| Source files (`project.yml`, `plan.yml`, `rooms.yml`, `objects.yml`, `wiring.yml`, `sketch.yml`, `atmosphere.yml`; Lua handlers inline in `wiring.yml`) | project folder | **yes**; the source revision (2.4.1) | the core in canonical form; any tool (then `oymap fmt`, `oymap record`) |
| `ids.lock.yml` | project folder | yes, a **record** (the build's engine numbers; kept in git); hashed apart, never undone; removed ids kept until a prune | builds, `import` and `oymap lock prune` |
| `review/pins.yml` | project folder | yes, the **review** document: own change counter, own log | the core's pins methods; the inbox import |
| Pin pictures | `.oymap/pins/pictures/` by default; `review/pictures/` only for a picture the user keeps on purpose (3.13) | a record | the game's `pin` command, the studio, jobs |
| `.oymap/` (head, last state, history blobs, pins log, jobs [N], caches [N]) | project folder, git-ignored | a record, never the source | the core, the host |
| Build outputs (`.blv`, `.odm`, `.scene.yml`, `.lua`, `build.json`) | `--out` folder | derived | `oymap build` |
| Mount folder | `output/...` or a configured folder | derived | `oymap install --mount` |
| Asset root | `assets_dev` or an install's packages | read only to the studio | the pipelines; the studio writes only to the mount or `mods/` |
| UI state (layout, camera, selection, recent projects, panel sizes) | browser storage per viewer; host settings in the user's config folder [N] | per viewer | the web app |
| Generator scripts (`gen/`, `tools/gen.py`) | project or scratch | a record; never re-run once the project carries the hand-edit mark | agents [P: REBUILD_PROCEDURE.md] |

**Generators and hand edits: a mark, not a banner** [N; Review A7 6.3]: several projects were written by scripts and
then edited by hand, and F6 (agents make the base, a person finishes) is a way of working many will use. Running such
a script again after a person's gestures would erase them. The first draft answered with a banner and a rule in the
procedures; that is too weak. All in S5b1, when hand edits begin:

1. **A durable mark.** At the first source transaction whose author is a person (`author: user`), the core writes a
   mark into `project.yml` (the first draft's `generated_by` note becomes a state: generators retired):
   `edited_by_hand: {since: <date>, revision: <source revision>}`. `revision` is the source revision **before** the
   marking transaction, the last state a generator or an agent alone made, so a diff from it shows all the hand work;
   for a mark set in the settings (next sentence) it is the revision at that moment. It is in a source file, so it
   travels with git and with an exported zip; `.oymap/` does not. Pins, replies, accepts and `oymap record` are not
   source transactions and do not mark, and neither do unattributed outside entries, since nothing says a person made
   them. So a person who edits the YAML in a text editor **sets the mark by hand**: "Protect this project" in the
   project's settings (and `oymap protect <project>`), which writes the same mark. Only a person clears it, in the
   same settings, told that a generator run then erases hand edits; no agent and no procedure sets or clears it on a
   person's behalf. **Reverting the entry that set the mark leaves the mark**: an undo reverts the hand edit, not the
   protection, and the revert rule of 2.7 skips the `edited_by_hand` field.
2. **Agents are told.** `project.open`, `map_open` and every edit result of a marked project say: this project is
   edited by hand; change it through operations, never by running a generator again.
3. **A whole-file rewrite is caught.** In a marked project, an outside change (found by the watcher or attributed by
   `oymap record`) that replaces objects a person changed last, or drops keys a file had (2.6 item 2), is recorded as
   usual and carries an **error notice** that lists those objects and keys, with one step to revert that entry (an
   ordinary revert entry, 2.7). Which objects a person changed last is read from the history. For this notice only,
   where the kept history does not show an object's last change (a fresh clone, an unpacked zip, entries past the
   1 000 kept), the object counts as a person's, so the notice errs towards warning. Precise operations by agents on
   hand-edited objects are not refused; their result lists the objects a person changed last **as the kept history
   really shows them** ("you changed 3 objects a person edited last"), never the unknown ones, so agents do not learn
   to ignore the line. Where the history does not reach back to the mark, `project.open` and `map_open` say once
   "history before <date> not known: objects changed by hand then are not listed".
4. **The procedures change** (REBUILD_PROCEDURE.md and OUTDOOR_REBUILD_PROCEDURE.md): on a marked project agents edit
   by operations (`oymap edit`, `map_edit`), never by a generator run.

The procedures are what make agents' maps good, and they live in this repository's `devdocs/`. People outside it who
want an agent to make the base need them shipped with the Studio download (as MCP prompts or a folder the host
serves): deferred beyond S5 (6.4), and D12's archive leaves room for it.

### 2.9 Meshes and view data from the core [N]

The browser draws; the core decides where everything is.

- **`view.layout`**: for every id, its resolved geometry in world units: a room's built floor polygons and heights, an
  opening's position, width and the two walls it joins, an object's position and facing (an object placed by `room`
  and `offset` or by `wall` and `along` is resolved by the core), a structure's parts as boxes or outlines, a road's
  cells, a scatter entry's placed points. This is what the plan view draws and what picking maps back to ids.
- **`view.mesh`**: the built map's faces grouped by texture (positions, normals, texture coordinates, indices as
  binary buffers), with a **provenance table**: for each face, the id (and part) that produced it (`room:hall` wall
  3, `door:gate` leaf 1, `thing:building_2` part p3 roof). The lowering knows this when it writes the faces (the
  indoor route names nodes `ROOM_`, `PORTAL_`, `MECH_`; the outdoor build names models); recording it is new core
  work and the base of every pick, highlight and pin. Provenance names sub-objects by the same keys as `patch` and
  pins (`thing:building_2/parts/p3`, 2.6), so a pick, a patch and a pin agree. **Stamped in the lowering, not read
  from node names** (S5-0, spike 2) [revision 4]: about 15 lines in the lowering's face writer stamp each face with
  its object (rooms, walls as `room:x/walls/<edge>`, openings, doors, lifts, movers); on Darkmoor all 4 659 faces keep
  their lowered node and face through the compiler, 97.0 % carry exactly one id, and stamping the remaining kinds
  (panels, boxes and blocks, plates, markers) gives 99.7 %. Node names are ambiguous (121 faces fit two ids, 17 none),
  so they are not the source. The last 0.26 % are two platforms without an id, which get keys in S5b1. Since `view.mesh`
  comes from the edit's own lowering (2.4.3), the stamps are there without the compiler. Provenance names the file
  where an id is not unique (2.6 item 11).
- **Movers**: each door, lift and mover's faces, axis, travel and speed, so the client animates them (the state
  scrubber of the design page) without a build.
- **Outdoor**: the 128 x 128 height grid and tile ids, water and liquids, models, and the decorations' placements with
  their sprite or model names.
- **Shipped maps**: the same methods on a map file, for the Compare view and for overlay projects' bases.

### 2.10 How the game is involved

What exists [P]: `--extra-mount <dir>` in the game and in headless runs (development roots only); `oymap install
--mount`; headless scenarios (`--headless-run-scenario`); `tools/run_game.sh --isolated <name>` with `--position`,
`--yaw-radians`, `--pitch-degrees`, `--set`, `--seconds` (it has no `--extra-mount`, so captures use scratch roots);
screenshot tours and menu-input tours; console commands `loc`, `goto <map-id> x y z dir`, `reload map`, `exec <file>`;
outdoor maps need their terrain material file (`calibration/outdoor_materials.py`) or the game refuses them.

- **`pin <text>`, first, before any browser** [N, D13; review A7 1.6]. F1 says the user reviews by playing and reports
  `loc` lines, and R6 says a map is never reviewed from studio views alone. So the most valuable part of G1 needs no
  browser: a console command in the game that removes the translator. Proposal:
  - `pin <text>` in the game's debug console (beside `loc`, `screenshot`) writes one pin into an **inbox folder**:
    `<inbox>/<date>-<time>-<map stem>.yml` and a picture of the same name. The inbox is a `[debug]` setting
    (`debug.pin_inbox_path`; default `pins_inbox/` in the game's user data folder, which for development runs is the
    repository's), kept across runs (it is not a one-shot capture key). The `PLAY.md` commands leave it at the
    default, and `PLAY.md` says where it is (6.3, settled).
  - The pin file is **pins format 1** (3.13) with `source: game`: the text, the map file and world, the pose as `loc`
    gives it (position, `yaw_radians`, `pitch_degrees`, `heading_yaw_units`), the time, `author: user`, and the project
    folder and source revision the map was built from when the mount says so. **Every install route the user plays
    from** writes them beside the map (`<stem>.studio.yml`: project path, source revision, lock hash): `oymap install`
    with `--mount` and with `--root` (the hard-link play roots of `output/studio_play`, `PLAY.md`, from which the user
    plays today), and Play here; the game copies them into the pin. [Review A7 5] Without that file the importer
    matches the map stem against the project roots and asks when two projects match.
  - The picture is the game's own view **without the console**: the command closes the console and takes the next
    frame through the engine's screenshot readback (`requestScreenshotFile`, as `screenshot` does).
  - Development only, like the other debug commands; no per-frame cost (it acts when typed). A key that opens the
    console with `pin ` typed is a convenience for later.
  - **Answers through the command line**, before the browser: `oymap pins import <inbox>` moves each pin into its
    project's pins document (pictures into `.oymap/pins/pictures/`); `oymap pins list <project> [--open]`, `claim`,
    `reply --text ... --picture ...`, `resolve`, `accept`, `reopen`. `oymap pins tour <project> [--pin pin:p7]` writes
    a screenshot tour (the `debug.screenshot_tour_path` format) at the pins' poses, so the agent takes the **after**
    picture in the game with `tools/run_game.sh --isolated` after its change; the user's own picture is the
    **before**. The static review page (`calibration/review_page.py`) lists each map's pins with the text, both
    pictures and the reply, which is where the user reads answers until S5a's browser slice 3.
  - Size: days of work, no library decision involved; it is slice 1 of S5a (6.4). Wireframe W7.
- **Play here** (local mode only): build, install into the mount, write the outdoor material file, start the game
  visible with `--asset-root <root> --extra-mount <mount> --world <w> --map <file>` and the camera's position and
  facing. Either `run_game.sh` gains `--extra-mount`, or the host starts the binary directly with the same
  environment (`OPENYAMM_START_MINIMIZED` unset, since the user wants to play). [N]
- **Test switches** (items, quest bits, gold, a test party, time of day: design page `mock-gf-test`): the host writes
  a console file (`item ...`, `qbit ...`, `testparty ...`, `gold ...`) and the game runs it at start. **Missing:** a
  launch directive to run a console file once the map is loaded (`--set debug.startup_console_file=<path>`, one-shot
  like the other `[debug]` capture keys). [N, game-side, D13]
- **Coming back to the same camera**: the game writes its last pose (the `loc` line) to a file on exit when asked
  (`debug.exit_pose_path`); the studio moves its camera there. [N, game-side, D13]
- **Reload on change** (PLAN 10b item 2, not made): `reload map` exists as a console command. A development switch
  that watches the mount and reloads the current map keeping the party is the small version; until it exists, Play
  here restarts the game (seconds). [P: PLAN 10b; S2 "Not done"] [N: build it on `reload map`] It must not poll the
  mount per frame (memory "no per-frame cost"; review A7, D13): a file-system notification, or a check on an event
  that already happens (focus regained, a console command).
- **Walk in the studio** [D7]: the core's movement controllers (`IndoorMovementController`,
  `OutdoorMovementController`, linked cleanly since cut G1) run in the browser's wasm worker on the built map's bytes,
  at party size, colliding as the game does. The party's size is the game's own movement constants (radius 37 in
  every world today: `game/outdoor/OutdoorWorldRuntime.h:1872`, `game/indoor/IndoorMovementController.h:45`); the
  studio has no setting of its own, and if the game gets per-world sizes the walk reads the same source (6.3,
  settled). Doors can be toggled by hand; events are **not** run (the core records
  `evt` calls in a sandbox, it does not execute the game's 224 `evt` functions [P: PLAN 2 `core/script`]); monsters
  are not simulated. The page says so in walk mode. The worker reads the map's bytes and the few tables movement needs
  from the host by URL, so PhysicsFS is not needed for it. (Rejected alternative: walk only in the real game.)
  **Why the worker in local mode too:** the good reason (review A7) is that it makes the browser wasm build exist and
  run every day from the first phase, not only in S5c. The first draft's reason, that walking over WebSocket "puts a
  frame-rate loop through the interactive lane", is weaker than it read: a worker also answers through messages, and
  a third lane would keep walk off lane I. It still counts a little (one fewer process round trip per step), so it
  stays as a secondary reason. **Conditions** [Review A7, D7]: walk is part of the request list (`walk.load`,
  `walk.step`, `walk.toggle`), so a native lane can serve it if the wasm spike fails; a recorded walk replayed on
  native and on wasm must give the same poses (in the contract suite).
  **Spike 3 (S5-0) held D7** [revision 4]: the game's two movement controllers, compiled unchanged into a browser
  worker, step a 1/60 s frame in 10-40 us median and at most 260 us p99 on 30 605 faces (Thjorgard), at 60.05 steps a
  second in Chrome and Firefox; the native lane is not needed. What it changed:
  - **The walk's input does not use C-library trigonometry.** With `sinf`/`cosf` of the yaw from glibc natively and
    musl in wasm, two of three recorded walks drifted for a few dozen frames; with deterministic `sin`/`cos` all three
    are bit-identical. The walk uses the core's own math (4.10, the same musl-based functions the lowering uses), and
    so do the game's rotations of movers (`IndoorMovers.cpp` for rotating doors, `OutdoorGeometryUtils` for moving
    models), which could differ the same way (motion changes by at most one ulp; a game change, made as its own
    reviewed change like D13's). `bx::sqrt` and `bx::length` differ between the builds too (bx has no SIMD in this
    Emscripten build); two `bx::length` calls in `IndoorGeometryUtils` are checked in the same change. The contract
    suite's recorded walk includes a map with a rotating mover (2.3).
  - **`walk.toggle` rebuilds the collision cache**: 0.66-0.8 ms on Darkmoor, 3.7-4.4 ms (up to 6.8) on Thjorgard, once
    per click in the worker; accepted as the worst case (the game's incremental `applyMechanismGeometryUpdate` was not
    measured).
  - **`walk.load` takes the scene's movement state, not the scene text.** On Harmondale, 190-280 ms of the 194-290 ms
    load is yaml-cpp reading the 960 KB scene, of which the walk needs the doors, movers and decoration placements.
    The core writes that state beside the built map (with the 32 KB outdoor terrain pack: attributes after tile flags,
    land mask) and the host serves it by URL with the map bytes and `decoration_data.txt`.
  - **Not yet walked** (S5a4 covers them): ladders, water and swimming, outdoor bounds, MM9's own decoration rows,
    decorations hidden by events.
- **Playtests**: headless scenarios as jobs (`map_playtest` today), with their log and pictures in the job's output.
  A helper that turns a studio walk into `walk_to` steps is an S5b idea, not a requirement. [N]
- **Pictures from the game**: screenshot tours of every open pin's pose after a change (the lead's practice, memory
  "verify reported poses"), `things_shots.py`, `building_shots.py`, `ingame_compare.py`, `outdoor_ingame.py` as jobs.
- **Hosted mode**: none of the above but walking; the page says so and offers the project to a local install
  [P: PLAN 9].

### 2.11 Asset delivery

Facts: `assets/engine.zip` 1.5 GB, `worlds/mm6.zip` 703 MB, `mm7.zip` 518 MB, `mm8.zip` 622 MB; `assets_dev` holds
15 243 cooked textures (`.oytex`: a 120-byte header, version 3, zstd-framed block-compressed mips, BC7, BC1, BC4 and BC5
on desktop); MM6's `textures_x4` alone is 1 548 files and 824 MB (about 530 KB each); models are GLB files whose
textures are `.oytex`. [Measured; P: PLAN 9]

**Local mode.** The host serves bytes the core resolves through the game's own `AssetFileSystem` (packages, loose
files, the mount in front): `/tex/<world>/<name>` (the `.oytex` bytes), `/model/<path>`, `/sprite/<name>`, with
long cache headers keyed by the asset root's state. **The host un-frames the zstd itself** (`node:zlib` has zstd in
the machine's Node 24.21; checked for review A7 and again for this revision) and serves the header and the
block-compressed mips as they are (`/tex/...` returns blocks, not the zstd frames), so textures in local mode do not
depend on the wasm build [Review A7, D7]. **It un-frames asynchronously** (`zlib.zstdDecompress`, not the `Sync`
form, which blocked the host up to 32 ms per file in S5-0's spike 1) and **keeps an LRU of un-framed blocks** in
memory, so a texture shared by many maps or asked for again is not un-framed twice [revision 4]. The client uploads
the blocks: WebGL2 `EXT_texture_compression_bptc` (BC7), `WEBGL_compressed_texture_s3tc` (BC1),
`EXT_texture_compression_rgtc` (BC4, BC5); WebGPU `texture-compression-bc`. In hosted mode the worker un-frames with
the core's zstd. **No CPU BC decode** (spike 5) [revision 4]: every browser tested takes BC1, BC5 and BC7 in WebGL2,
Chrome and Firefox on a real GPU and every software GPU CI would use (SwiftShader, lavapipe, llvmpipe, Playwright's
Chromium headless shell); decoded pixels match the real GPU's exactly for BC7 and within 1 (BC1) and 3 (BC5) levels.
A browser without the extensions gets an untextured view with a note, not a decoder. **Lowest mips first**: every
texture's smallest mips load before any larger one (Darkmoor textured at 181 ms instead of 375), then the views
refine; an LRU cache bounds GPU memory (section 2.13). **The terrain's weight images are cooked** to a block format or
halved (spike 1: Harmondale's two take 32 MiB of GPU memory as RGBA8, a quarter of its total). Shader liquids
(`orwtrtyl`, `lavatyl`, `wtrtyl`: no picture) get a simple animated material. [P: PLAN 9 for the method]

**Decorations and creatures.** Decorations draw as their sprite (billboard) or their model where dungeons draw them
as models (`oymap assets` says which). Monsters and actors draw as markers sized by the monster table's radius and
height, with the creature model's far LOD on demand (the game's GLBs are large: MM6's models folder is 688 MB). [N]

**Thumbnails** for the library: textures from a small mip; decoration models rendered by the web app on first sight
and kept in the browser's storage. No central thumbnails exist (about 2 678 GLBs without tags or thumbnails: CODE
SURVEY). [N]

**Hosted mode** [P: PLAN 9]: the user picks the install folder (or single zips); the worker keeps `File` handles and
serves PhysicsFS reads by byte range (`FileReaderSync`, or OPFS sync access handles for copies); only each zip's
central directory is held in memory; textures never pass through the wasm heap as pixels; one map at a time; a repo
checkout (`assets_dev`, 12 GB of loose files) is read through the same directory handle. **To do first:** PhysicsFS
does not start in today's wasm build (`PHYSFS_init failed`) [P: wasm/README.md].

### 2.12 Security and sandboxing

**Local mode.** The host listens on 127.0.0.1 only, checks `Origin` against an allow list and requires the pairing
token (all three exist and are tested [P: S2]). Added [N]:

- **Typed methods only.** The browser's endpoint accepts the catalogue's methods, not `run` with free arguments, and
  never `map_exec` (its `node:vm` context "is a convenience boundary against mistakes, not a security sandbox"
  [P: PLAN 8]).
- **A path jail.** Projects only under configured roots; the asset root read only; writes only into project folders,
  the mount and, when installing a mod, the install's `mods/`. Today `map_open` takes any path.
- **The token in the URL's fragment** (`#token=`), which browsers do not send in requests or log in server logs, then
  kept in session storage.
- **A `Host` header check** on every HTTP request and on the WebSocket upgrade: only `127.0.0.1:<port>` and
  `localhost:<port>` are accepted. DNS rebinding can make a hostile page same-origin with 127.0.0.1, so the `Origin`
  check alone is not enough. [Review A7 3]
- **The token on the HTTP byte routes too** (`/mesh`, `/tex`, `/model`, `/sprite`, pictures), not only on the socket:
  sent as an `Authorization` header by the web app's own loaders (all byte loads go through the RPC client's fetch,
  never through a bare `<img src>`), never in a query string. [Review A7 3]
- **A content security policy** for the web app: scripts from its own origin only, `'wasm-unsafe-eval'` for the
  core, no remote origins at all (fonts and libraries are vendored).
- **Untrusted text** (a stranger's project: notes, names, titles) is only ever rendered as text; React escapes by
  default; no HTML from project files.
- **Limits** on request size, YAML alias expansion and nesting depth in the core's readers; the Lua sandbox already
  has no `dofile`/`loadfile` and an instruction limit [P: PLAN 2, S1].
- **The game** starts only from the binary path the host was given at start (`--game`, as today).

**Opening someone else's project.** In local mode the native core parses untrusted YAML and runs untrusted Lua in its
sandbox. The safer route for a stranger's mod is the hosted page, where everything runs in the browser's wasm
sandbox. The docs say so. [N]

**Hosted mode.** A static origin; nothing leaves the machine; File System Access permission per folder, asked by the
browser; the same content security policy. Pairing with a local host: the page connects to `ws://127.0.0.1:<port>`
with a pasted token. Chromium and Firefox allow it from an https page (loopback counts as potentially trustworthy);
Safari blocks it [P: PLAN 9]. Threads (and the cross-origin isolation headers they need) are not used. [P: PLAN 3]

**The local-network permission, verified** (S5-0, spike 5) [revision 4]. A public https page reaching 127.0.0.1 needs
the browser's local-network-access permission in Chrome 153, Chromium 156 **and** Firefox 157, and the prompt gates
both `fetch` and the WebSocket. Without it Chrome fails at once (and records "denied"), Firefox holds the request
open while its prompt waits (8 s in the spike); with it both work. Local mode (the page served by the host from
127.0.0.1) needs no permission. So pairing: starts **from a button**, never on page load, and the page says first
that the browser will ask for access to this computer's network; a first request that hangs is shown as "waiting for
your answer in the browser's prompt", one that fails at once as "refused: allow it in the site's settings", with how
to find that setting per browser.

### 2.13 Performance budgets

Facts (appendix C): the largest shipped maps are MM9's Thjorgard city (30 605 faces, 36 406 vertices) and Lindisfarne
(30 460 faces); MM6 to MM8 dungeons have 1 400 to 4 700 faces (Castle Darkmoor 4 665, Goblinwatch 2 290); the largest
rebuild is Darkmoor's (267 rooms, 4 659 faces); outdoor maps have 121 to 128 models and 469 to 825 placed things on a
128 x 128 grid; a dungeon uses tens to about a hundred textures.

The S5-0 column (revision 4) is from the spikes; S5.md has each number's method and load. Before S5-0 the "today"
figures were: one real `oymap edit` on Darkmoor 1.0 s; Erathia validate with assets 1.64 s; builds 0.83 s (Darkmoor)
and 1.59 s (Erathia); opening about 2 to 3 s of build; background checks 3 to 15 s per map (S1) (review A7).

| Budget [N] | Target | S5-0 measured (load average) | Verdict | What it takes |
|---|---|---|---|---|
| Hover, select, pan, zoom | under 16 ms, no core call | picking 500 rays without a tree: p95 1.0-3.3 ms, max 5.6-9.3 (Chrome); p95 5-9, max 7-14 (Firefox, Harmondale) (11-30) | met | client-side picking (provenance table); no picking tree indoors; outdoors the terrain in chunks of 16 x 16 cells (4.1) |
| Gesture shown on the plan | the next frame, no core call | n/a | | the client applies its own patch to its copy (2.4.3) |
| Gesture committed by the core, indoor (files written, diff and issue delta shown) | 300 ms at the 95th percentile on Castle Darkmoor | 275 / 294 / 300 ms median, p95, max (11.7-12.7); run 2 279 / 327 / 347 (6-24) | met, thin margin, on three conditions; re-measured on a quiet machine before S5a2 | cache by source revision (2.4.1, 2.4.3); parsed table lookups once per asset root; one validation per edit; schemas of changed files only (2.4.3) |
| Gesture committed, outdoor | **set**: 1.5 s p95 on Erathia for S5a and S5b1; **500 ms** for S5b2 | 1 303 / 1 424 ms median, p95 (9.1-13.3); land lowering 840, scene write and check 238 | set | S5b2: land kept up to the peaks, keyed by the land words without `nodes`; the scene write and reader check out of the commit (2.4.3) |
| A brush stroke's commit | as the outdoor commit: 1.5 s, then 500 ms in S5b2 | 1 305 / 1 468 ms (8 x 8 nodes), 1 294 / 1 398 (32 x 32) (5.8-8.6); about 0.5 s with kept land (from the code, not measured) | set | one commit per stroke on pointer up, the client drawing until then; a keyed or path patch into `heights.nodes` (2.6 item 3, 3.18) |
| 3D after a commit, indoor | 1 s on Darkmoor | dry view build 749 ms median, 1 556 p95 (10.3-12.4); 394-404 without BSP and outlines | design changed | `view.mesh` from the edit's own lowering; compiler, BSP, outlines and GLB only for install, Play here and playtests (2.4.3) |
| 3D after a commit, outdoor | **set**: the commit plus 200 ms | view build 1 208 / 1 246 ms (8.6-9.1) | set | as indoors |
| Opening a project (plan and grey 3D) | 2 s for Darkmoor; textures stream after | browser side textured 0.2-0.4 s (Darkmoor), 0.5-0.9 s (Harmondale) (11-21); cached open 376 ms (12); `project.open` 142 ms native (12-14) | met; governed by the core's `view.mesh` | cache; mesh before textures; lowest mips first (2.11) |
| Background checks (`audit --reach`, `solve`) | under 15 s, never blocking | not measured; `check.validate` with assets 0.4-1.7 s, `check.things` 0.9-1.9 s native (12-14) | S5a5 | lane J |
| Walk mode | 60 frames a second on 30 000 faces; a movement step under 1 ms | 60.05 steps a second; p99 55-260 us on 30 605 faces (12.6-17.8) | met | wasm worker (2.10) |
| GPU memory | textures 512 MB (LRU), meshes 100 MB | Darkmoor +33 MiB, Harmondale +141 MiB (24.3) | met | lowest mips first; terrain weight images cooked or halved (2.11) |
| Wasm heap, hosted | under 1 GB on the largest MM9 region | Node wasm builds 185-407 MB, about 300 MB above native indoors (the heap never shrinks) (20-25) | S5c | PLAN 9's acceptance check; the overhead looked at there (R8) |
| Download of the web app | under 3 MB of compressed script; the wasm core about 2 MB compressed | gzip: three.js 134 KB, React 65, Base UI 79, forms 13, yaml 16; wasm core 2.2 MB (7.4 MB raw with names), the walk 0.36 MB more | script met; wasm estimate replaced by the measurement | whether stripping names lowers the wasm is not measured |

Every measurement records the machine's load average beside it (review A7: the first draft's Darkmoor validate of
0.98 s did not reproduce at a load of 1.4).

### 2.14 Offline

Local mode uses no network beyond 127.0.0.1: libraries and fonts are bundled, nothing comes from a CDN. The hosted page
is cached by a service worker per release, so after the first visit it opens without a network; its assets are the
user's anyway. [N]

### 2.15 Versioning and migration

Facts [P]: every project file carries `format: 0`; `project.yml` `migrated` answers warnings about a changed rule; PLAN
13 promised "until the end of S3 the schema carries a version and `oymap` migrates projects forward". S3 has ended
and no migration step exists.

Proposal [N]:

- **Additive changes keep the format** (a new optional field, a new kind). They are the daily case.
- **A breaking change bumps that file's `format`** and comes with a migration in the core (`oymap migrate`, and
  `project.migrate` in the RPC), recorded as a history entry with author `migration`. The web app never migrates by
  itself; it asks, because migrating rewrites files.
- **The format bump carries the keys** (2.6 item 2): every selectable sub-object gains its key, marked `x-key` in the
  schema, and the migration writes keys into existing projects (from the part ids that exist, otherwise derived from
  the object's kind and position once, then kept). Pins and the lock that name sub-objects are migrated in the same
  step. [Review A7 1.3] The key fields stay optional in the schema: a file without keys (a generator's) still
  validates, the core fills missing keys on its next write, and a regenerated file's keys are positional again, a
  stated limit of generated projects (2.6 item 2). [Review A7 5 point 3]
- **Settle known debts before S5b freezes format 1:** a sized chest's width runs along its `facing`, which every
  author read the other way (HANDOFF.md, "a candidate for a format fix with a migration"); angles come as radians
  (playtest `set_pose`), degrees (shot pitch), 2048 units (`goto`, `loc`) and the `facing` field: the schema should say
  each field's unit (`x-unit`), and the UI shows units beside every number.
- **Versions must match.** `hello` returns the core's version and formats. In local mode the host serves the web app
  built from the same commit and refuses a mismatch with "rebuild the studio". The hosted page lives at a versioned
  path per release (`/studio/<release>/`), opens older projects (offering migration) and refuses newer ones with the
  release that can open them.
- **The RPC catalogue is versioned** like the formats: additive changes keep the version; the MCP tools keep their
  names.

---

## 3. The UI

### 3.1 The frame [P: design page `mock-anatomy`, nine numbered parts]

The design page's frame stays: title bar with search and Play here, stage bar, tool rail, tool options, plan and 3D
views, inspector, drawer, status bar. Added [N]: a Review/Author switch, the connection line in the status bar, and
Pins, History, Pictures and Jobs tabs in the drawer.

```
+--------------------------------------------------------------------------------------------------------------------+
| Map Studio | Goblinwatch rebuild  briefs/mm6_6d01/L4  rev 7c1e   [ Search Ctrl K ]   (Review|Author)  <- ->  > Play F5 |
| 1 Plan ok | 2 Shape 11/14 | 3 Build 4/14 | 4 Wire 0/38 | 5 Populate | 6 Dress | 7 Test     [Plan|Split|3D|Walk|Flow] |
+------+-------------------------------------------------------------------------------------+-----------------------+
| Room | Room: grid 64  floor -447  ceiling 448  theme castle  space antechamber  [x] snap    | Properties Connections|
| Path +------------------------------------------+------------------------------------------+ Notes Source Original |
| Stair| PLAN  band [Caves][Core][Upper]          | 3D  grey | lit   cutaway   [doors 50%]   |                       |
| Open |                                          |                                          | room:vault            |
| Pilla|   +------+----+                          |        ____                              | rooms.yml  2 sectors  |
| Platf|   | hall |barr|  ...                     |       /   /|                             | floor    -447         |
| Level|   |      +----+                          |      /___/ |                             | ceiling   448         |
| Fligh|   +------| VAULT |                       |      |   | /                             | theme    castle  v    |
| Beam |          +-------+                       |      |___|/                              | + slope levels ...    |
| Walk |                                          |                                          |                       |
|      +------------------------------------------+------------------------------------------+ Driven by / drives    |
|      | Library | Checklist 3 | Issues 2 | Outline | History | Pins 1 | Pictures | Jobs       |  door:vault_gate ...  |
|      |  [ ] space:antechamber has no room   [ ] every room reached ...                      |                       |
+------+-------------------------------------------------------------------------------------+-----------------------+
| X 2 816  Y 2 048  Z -447 | sector 31 room:vault | grid 64 | click adds a point, Enter closes | host ok | agent:gw2 |
+--------------------------------------------------------------------------------------------------------------------+
```

Wireframes W1 (review) and W2 (author, Shape) draw the same frame at full size.

### 3.2 Two modes: Review and Author [N]

- **Review** (S5a): geometry and objects are read only; pins, the camera, walking, Play here, checks, compare, history
  and pictures work. It is what the user opens on an agent's map. Switching to Author asks nothing; it is a filter,
  not a lock (an agent may be editing the same project anyway).
- **Author** (S5b): the stage bar and the tools appear. Review's panels stay.

The split exists because the first and most frequent use is reviewing (F1), and a review that can move a wall by an
accidental drag is a bad review.

### 3.3 The stage bar [P: design page "Seven stages"]

Stages filter the tool rail, choose the default view and the checklist; they never lock anything; keys `1` to `7`.
Each stage shows a count of what is open in it. How the stages map onto the files that exist [N]:

| Stage | Indoor (files, lists) | Outdoor (files, lists) | Default view | Done when (from the checks) |
|---|---|---|---|---|
| 1 Plan | `plan.yml` spaces, links, goals, keys, height bands, set pieces, states; `project.yml` card, neighbours, quest bits, items | `plan.yml` (zones, points of interest, landmarks); `project.yml` card, neighbours | plan, full width | every space named with a purpose; the critical path reaches the goals |
| 2 Shape | `rooms.yml` rooms (outline or path, floor, ceiling, slope, levels, platforms, pillars, flights, beams, parapets), openings | `sketch.yml` frame and rim, heights (grid, points, cliffs, ridges, terraces, spires, peaks, cuts, rough, nodes), water, roads | split, grey | every planned space has a room; every room reached |
| 3 Build | themes, walls and bands, surfaces, doors, lifts, movers, plates, floors, ladders, chests as furniture | ground and tile sets; structures (buildings with parts, roofs, wall bays, porches, signs; walls, bridges, wells, fountains, cave mouths ...) | split, lit | no grey faces; every planned door and building exists |
| 4 Wire | `wiring.yml` events (presets, conditions, effects); switches; exits; neighbours | what structures and doors do (`house`, `into`, `effects`, `condition`); `events` | plan with links | no unbound clicked face; the solve opens everything planned |
| 5 Populate | spawns, monsters, items, relations | areas (encounters, items), actors | plan with density | density and sizes within the shipped bands |
| 6 Dress | lights, decorations, sounds; `atmosphere.yml` (mist, flags) | scatter; `atmosphere.yml` (sky, fog, weather, mist, sky theme) | 3D lit | nothing floats or clips; town feel inside its ranges |
| 7 Test | checks, walk, Play here, playtests, compare | same, plus `town_feel`, `building_shots` | split with issues | the checklist and the issue list are empty |

### 3.4 The plan view

Vector drawing on a Canvas2D layer with an SVG layer for handles and labels [N, section 4.5]:

- **Indoor:** the project's room outlines and paths as drawn (from the files), the built sectors' floors under them
  (from `view.layout`), openings (teal, as the design page), doors (red), objects as glyphs by kind with their ids on
  hover, the start, spawn points and their radius, pins. Planned spaces without a room are dashed ghosts.
  **Height bands** from `plan.yml` (`height_bands`) or, when none are given, from the floors' clusters, shown as
  tabs; rooms of other bands are drawn faint. A **section view** (a vertical cut along a line the user draws) shows
  stacked levels, stairs and lift travel [P: design page `mock-nl-lift`].
- **Outdoor:** the built 128 x 128 heights as a shaded raster (with water and tiles as colours), the sketch's grid of
  spot heights, height points, cliff and ridge lines, roads on cell centres, ground zones, structures' parts as boxes,
  outlines and rounds with their doors, scatter areas and their placed points, encounter areas, actors, events, the
  playable square, the rim's stretches; cells of 512 with the sketch's coordinates (cells, x east, y south from the
  north-west corner) and world units both shown.
- **Overlays** (toggles): sectors, portals, doors, ids, issues (a marker per finding with a place), compare heat,
  density heat, pins, links of the selection.
- **Measure** tool; grid sizes `[` `]`; snapping to the grid, to wall lines and to other rooms' corners.

### 3.5 The 3D view

three.js over the core's meshes (2.9) [N, D6]. Grey, textured, and simple-lit modes (no lightmaps at first: the game
look is Play here's job [P: PLAN 9]); cutaway that hides ceilings above the eye or above the current band; doors and
movers on a scrubber (closed to open); fly camera (right mouse to look, WASD), orbit round the selection (Alt and left
mouse), frame (`F`). A click picks a face; the provenance table turns it into its id and part. Labels of ids on
objects as in the core's labelled renders (Set-of-Mark style [P: research, MCP_AND_AGENT_TOOLS]) on request. Outdoor:
terrain mesh, models, decorations as billboards or models, water as flat animated material, the sky as a flat colour.

### 3.6 Walk mode

`G` toggles. Party height and collision from the wasm worker, with the game's own constants and no studio setting
(2.10); mouse look and WASD as the game; doors and lifts
toggled by clicking them (their state is the studio's, not the game's); position, sector or cell, floor height and the
room's id in the status bar. `P` pins here with the camera; `F5` plays here in the real game from this pose. The banner
says: "Walk mode collides like the game. Events, monsters and traps do not run: use Play here". [N] Mouse look needs
the browser's pointer lock, whose exit key is `Esc` and cannot be changed (review A7 3). So in walk mode `Esc` leaves
mouse look (and a second `Esc` leaves walk); no drawing is in progress while walking, so `Esc` as "cancel a drawing"
(3.17) does not clash.

### 3.7 The flow graph

Data from `solve` (the waves: what opens in which step, what each needs) and from `flow` per event (each handler's
tests and effects) [P: S1]. Nodes are rooms of the project (not sectors: S3's lesson that room counts and sector
counts differ), grouped by height band; edges are openings, stairs, lifts, teleports and drops; doors make an edge
conditional and show the condition; approximate edges (from Lua run in the sandbox) are dashed; unknowns are listed,
not guessed [P: PLAN 6]. Columns are the solve's steps, which gives a natural left-to-right layout. The critical path
to `plan.yml`'s goals is drawn thick; issues (unreached rooms, keys behind their own lock, one-way traps) link to
their objects. Clicking a node selects its rooms in the plan. [P: design page `mock-gf-flow`]

**Switch board** [P: design page `mock-gw-board`]: a table of switch events against their targets (open, close,
toggle in the cells), generated from `wiring.yml`, editable cell by cell (each cell edit is a `patch` of one event). It
is a view, not a data type: the design page's switch board and sequence puzzle are not words of the schema [C], and
S5 needs no new one for them.

### 3.8 The inspector [N, D5]

Tabs: **Properties**, **Connections**, **Notes**, **Source**, **Original** (rebuilds), **Issues** (this object's).

- **Properties is generated from the schema.** The schemas use a small part of JSON Schema (counted over all files:
  `type` 1 717, `description` 1 510, `$ref` 493, `minimum` 471, `items` 353, `maximum` 295, `additionalProperties`
  245, `x-flow` 190, `required` 165, `enum` 142, `oneOf` 27, `anyOf` 15, `const` 15, `prefixItems` 8, `pattern` 9).
  A form renderer for that subset is a few thousand lines and covers every field the day it lands.
  - Fields present in the object show first; optional ones are behind "+ add field", each with its description.
  - `$ref` to an id becomes a picker of ids of the right kind, with "pick on map". **Today this has nothing to filter
    on**: every reference is the one generic `common.schema.json#/$defs/id` pattern (`<kind>:<name>`). Each id field
    must say which kinds it accepts (`x-id-kinds: [door, lift, mover]`). [Review A7, D5]
  - Numbers show their unit (`x-unit`, to add) and accept expressions (`512*3`).
  - Points, outlines, lines and boxes carry an `x-geom` annotation (to add: `point2`, `point3`, `cell`, `polygon`,
    `polyline`, `box`, `wall_along`, ...) and get "edit on map": the plan view's handles edit that field.
  - Lists of objects (a building's `parts`, a room's `platforms`) show as sub-tables with add, remove, duplicate and
    reorder; each row opens as a nested form.
  - Pickers over the game's tables: houses (`house_data.txt`, the service picker of `mock-ns-build`), monsters (by
    the map's slots), items, quest bits by name, decorations and textures from the library.
  - Labels come from the property names (`wall_height` reads "wall height"); descriptions are the help text. The
    schemas' descriptions are written for authors and are good help; only 10 properties have a `title`.
  - **Unions need a rule.** `sketch.schema.json` has 37 `oneOf`/`anyOf`, and none is told apart by a constant, so a
    form cannot know which branch an object is in or offer the branches by name. [Review A7, D5] **The rule, as spike
    7 reworded it** [revision 4]: **branches of different JSON types need nothing** (a bare number or `{height,
    steps}`: shown as a toggle; an optional `x-labels` names them); **branches of one JSON type need a `const` per
    branch** (`kind: building`) **or `x-variant`**, naming per branch a label and what selects it: the presence of a
    property (`outline` against `path`) or a shape (`when: {length: 3}` for a line of 2 or 3 numbers). Counted: 33 of
    the 37 and all 73 `type: [a, b]` lists are of the first kind; two presence `oneOf` (`areas[]`, `scatter[]`), one
    same-type union (`structures[].line[]`) and the plan's `footprint_cells` need `x-variant`; implicit choices
    (a room's `outline` or `path`, a floor's `steeper_than` or `at`) are written as presence `oneOf` with `x-variant`.
    The real problems are unions not written as unions: 21 objects whose `kind`, `shape` or `form` decides which
    properties apply (`structures[]`: 156 properties over 28 kinds; a building's `parts[]` 61; plan spaces, doors,
    openings, porches, links) get `x-discriminator: {property, default}` and `x-kinds` on every property, with per-kind
    `x-unit` and `x-geom` where a word changes meaning by kind. **The core enforces `x-kinds` too**: it reads the same
    annotations and reports a word on the wrong kind as a warning (2.4.2), so the kind table is checked by the
    lowering, not only used by the form. [Spike 7; review A7 on it]
  - **Grouping and order, per object** [revision 4]: an object with 10 or more properties carries `x-groups: [[section,
    [property, ...]], ...]`, the sections and their properties in form order; without it the form falls back to schema
    order, which is what authors wrote, not what a form needs. (The first form, `x-group` and `x-order` on each
    property, was 69 % of the building's hand annotations in spike 7: 183 + 183 of 579.) The lint requires every
    property to be in exactly one section and reports a missing one **per property**, so a new property on an allowed
    object does not pass unseen.
  - **Units on every number** [revision 4]: every `number` and `integer` carries `x-unit` (map, cell, deg, ratio,
    count, index, texel, gold, angle2048, none, or per kind), not only those whose description names a unit: that rule
    found 122 of 577 in spike 7.
  - **Event steps have a schema** [revision 4]: `effects` and `else_effects` are untyped lists today, their vocabulary
    only in prose (18 lists; 104 steps in the 22 projects that the generated form cannot draw). They get
    `$defs/effect`, a union told apart by its one key (`opens`, `set_texture`, ...), so the core validates steps and
    the Connections tab reads them; the event form itself stays bespoke (3.18).
  - Sub-objects in keyed lists show their key (`x-key`, 2.6) as the row's name and in the breadcrumb
    (`thing:building_2 › p3`).
  - **Defaults are the lowering's, shown from the core.** What a field left out means is decided in the lowering
    (often by the kind or the world: "a plot that says nothing is the world's ordinary house"), not by the schema's
    `default`, which would be a hand-written copy that drifts. The inspector shows each absent field's **effective
    value** from the core's resolved read of the selected object (`project.resolve`, 2.3; S5b1), greyed and marked
    "not written"; editing it writes the field. [Spike 7; review A7 on it]
- **Connections**: what drives this object and what it drives, from `wiring.yml` and the outdoor `effects`
  (`opens`, `closes`, `toggles`, `show`, `hide`, `set_texture`, `teleport`, ...), each a link that selects.
  [P: design page "Connections are visible"]
- **Notes**: the object's `notes` field (the format has no comments [P: PLAN 4]).
- **Source**: the object's canonical YAML in a text editor with schema-aware completion; Apply sends a `set` of the
  whole object.
- **Original** (projects with `map_stats.reference` or `base`): the original's matching record (door record, faces
  and their textures, the handler as `flow` prints it), from `oymap export` and `things`.

**What keeps the generated inspector honest** [Review A7, D5]:

- **A schema lint** fails a schema change that lacks what the form needs: an id field without `x-id-kinds`, a list
  of selectable objects without `x-key`, a union of one JSON type without a discriminator or `x-variant`, a
  kind-selected object without `x-discriminator` or a property of it without `x-kinds`, a geometric field without
  `x-geom`, a number without `x-unit`, an object of 10 or more properties with a property in no `x-groups` section.
  Without it, G6 ("editable the day it lands") decays within a week of other sessions adding words. **It lands early,
  in S5a2, with today's issues as its allow list** (S5-0, spike 7) [revision 4]: spike 7's draft finds 1 208 issues
  on today's schemas (unit 707, id-kinds 145, key 138, geom 117, group 55, raw 23, kinds 19, union 4) in 20-30 ms; the
  allow list holds exactly those, may only shrink (`--check` fails on a stale entry), and so every word added from
  S5a2 on needs its annotations while the old ones are annotated in S5b1 (rooms, objects, wiring, plan) and S5b2
  (sketch): rule-made annotations first, then the kind tables, then the rest. The lint uses the form generator's own
  classification, so it fails exactly where the form would draw badly; it runs in the web app's Vitest suite and in
  CI beside the core's unit suite.
- **The lint checks that annotations exist, not that they are right** [spike 7; review A7 on it]. Two more checks:
  - **A corpus rule** in the same suite: the values of each annotated number across the 22 projects lie within its
    unit's range (cells within the map, `angle2048` under 2048, degrees, ratios), so a wrong `x-unit` shows as
    values out of range.
  - **Each annotation batch is checked against the lowering by an agent other than its writer**: units, kinds and
    geometry read from what the lowering does with the field, not from its description.
  - **What the lowering reads, recorded** (revision 3.1; review A7) [N]. The outdoor lowering reads the sketch's
    words through small helpers, `childOf` and `textOf` (`core/OutdoorLowering.cpp:271` and `:286`; with their
    definitions, 93 calls in `OutdoorLowering.cpp`, 177 in `OutdoorBuildings.cpp`, 143 in `OutdoorThings.cpp`). A
    checking mode records which keys of each object were read during a lowering; over the 22 projects that gives
    "word X was never read on this object", which catches a kind table that allows a word the lowering ignores (the
    half the corpus rule misses) and generates the first kind tables for the 27 structure kinds the spike guessed,
    before anyone fills 156 entries by hand. A read under a condition that the projects never meet shows as unread:
    a `note`, not a warning. Review A7's estimate: about an hour of S5b2's annotation work. **Checked here, a
    correction to the premise:** the helpers are not one function. Sixteen core files define their own copy (eleven
    of them outdoor: `OutdoorBuild`, `OutdoorBuildings`, `OutdoorEvents`, `OutdoorFalls`, `OutdoorGround`,
    `OutdoorInstall`, `OutdoorLowering`, `OutdoorPlaces`, `OutdoorRim`, `OutdoorThings`, `OutdoorWaysIn`; also
    `Sketch.cpp`), and a few reads walk a map's keys directly (a part's `textures`, event effects in
    `OutdoorEvents.cpp`, `OutdoorPlaces.cpp`'s key loop). So the outdoor copies first become one shared helper, and a
    direct walk counts as reading every key it visits; with that the hour may be two or three. The second agent's
    check stays for words that are read but have no effect. The indoor lowering's reads (`IndoorLowering.cpp`,
    `IndoorBuild.cpp`, each with its own copy) are not yet checked for the same route.
- **The building words in one `$defs`**: a building's `parts` words are written twice in `sketch.schema.json` (about
  40 KB each, 296 annotations twice). The format change of S5b2 moves them into one shared `$defs`, annotated once,
  with the check that all 22 projects and the unit suite's refusals validate the same before and after. [Spike 7]
- **A spike first**: S5-0 renders one building and one room from the schemas (both union forms included) before D5 is
  fixed (6.4). Done (spike 7, `output/s5_spikes/7_forms/REPORT.md`): every building and room of the 22 projects
  renders; every field is editable without annotations, but only 49 to 68 % are complete (unit, id kinds, geometry,
  key, union names) without hand annotations, and about half of all fields need one. Its render times are Node
  server renders (headless Chrome's timings were unusable); **the in-browser render time is measured in the real app
  in S5a2**.

### 3.9 Tool rail and tool options [P: design page]

The rail shows the current stage's tools with one key each; hovering shows a short explanation and an example from a
shipped map ("as Goblinwatch's vault") [P: "Help where you work"]. Tool options sit in the bar above the views and
hold the active tool's settings (grid, heights, theme, kind, snapping), never the selection's properties
[P: "Tool options and object properties are separate"]. Nothing opens in a modal dialog.

### 3.10 The drawer

- **Library**: search over decorations (size, world, whether dungeons draw it as a model), textures (size, texture
  family, the shipped maps that use it, from `texture_use.py`'s data), houses, monsters, items, kit roles; drag onto
  the plan or 3D to place. [P: `oymap assets`; REBUILD_PROCEDURE texture rule]
- **Checklist**: the plan's spaces, points of interest and landmarks not yet built; each stage's "done when"; for
  rebuilds and new maps, REBUILD_PROCEDURE's "what the measure does not see" list as items to tick with a picture.
  [P: design page "The plan is the checklist"; REBUILD_PROCEDURE.md]
- **Issues**: findings of `validate` (inside every edit), the build's warnings, `audit` (`geometry.coplanar`,
  `geometry.eye_sector`, `thing.floating`, `texture.squashed`, `click.silent`, `question.answer`, ...), grouped by
  severity (error, warning, note: the severities of 2.4.2, new for `validate`; `audit` has them already), each with its
  object and place; skipped objects (2.4.2) first, "go to", and **a fix** where the core offers one as operations
  ("Errors say how to fix it" [P]; most findings do not carry fix operations yet [N: a core task]).
- **Outline**: every object by file and list, filterable; double-click frames it.
- **History**, **Pins**, **Pictures**, **Jobs**: sections 3.12, 3.13 and 3.15.

### 3.11 Checks and scorecards

A **scorecard** per project (drawer and project list): the compare score with its parts, the playtests' last results,
reach and solve, coplanar pairs (new against the original), interactive things without a name, floating things, and
the figures outside their ranges from `scale_bands.py` (new dungeons) and `town_feel.py` (outdoor towns, with
`--start` for start maps). Each figure links to the places it counts where the tool gives them (`town_feel.py
--json`). The scorecard records the revision it was measured on and is greyed when the project has moved on.
[P: the tools exist; TOWN_FEEL.md; REBUILD_PROCEDURE.md] The Python ones run only as local jobs (D10).

### 3.12 History

Entries newest last: sequence, author, label, the semantic diff lines (`objects.yml: door:gate changed speed (64 ->
200)`), revisions before and after. Selecting an entry highlights its objects; "show as it was" draws that revision's
geometry as a ghost over the current; Undo (yours), Redo, "Revert this entry" (any entry; all three append a revert
entry, 2.7); undo entries show which entry they revert, and merged entries (`merge_key`) show as one line with a
count; named checkpoints. Pins have their own log (3.13) and never appear here.
[P: `oymap status`, `undo`, `redo`] [N: authors, ghosts, revert entries]

### 3.13 Pins and comments [N, D9]

A pin is a note on an object or a place, made by a person or an agent, answered in a thread. **Pins come from the
game first** (the `pin <text>` console command, 2.10; slice 1 of S5a), and are answered through the command line
before any browser exists; the browser's Pins panel (slice 3) reads and writes the same document.

**The pins document is not part of the map's source** (2.4.1): `review/pins.yml` has its own change counter and its
own append-only log in `.oymap/pins/`; a pin, reply or claim never changes the source revision, never drops a cache,
never greys a scorecard and never makes an agent's `expect_revision` stale. Pins are outside the map's undo.

```yaml
# review/pins.yml, format 1 (proposed; today: id, text, on, at, status open|resolved|declined, author, reply, revision)
format: 1
counter: 42                          # the pins document's own change counter
pins:
  - id: pin:p7                       # allocated by the core
    text: The gate leaf flickers where it meets the jamb.
    on: door:vault_gate              # an id, or a keyed sub-object (thing:building_2/parts/p3); or at: [x, y, z]
    source: game                     # game | studio | agent
    map: 6d01.blv
    pose: {position: [2816, 2048, -380], yaw_radians: 1.571, pitch_degrees: -3.0}   # as `loc` gives it
    picture: .oymap/pins/pictures/p7.png   # outside git by default; `keep: true` copies it to review/pictures/
    author: user
    created: 2026-11-20T10:12
    revision: 7c1e0a...              # the source revision the pin was made against (from the mount's studio file)
    status: resolved                 # open | claimed | resolved | accepted | declined
    claimed_by: agent:gw-round2
    replies:
      - {author: agent:gw-round2, text: "Leaf stops 2 short of the jamb now; game picture after.",
         revision: a90b..., pictures: [.oymap/pins/pictures/p7-after.png]}
```

- **Until keys exist, a pin anchors to a top-level id or a point only** [Review A7 5 point 5]. Pins format 1 arrives
  in S5a1, keys in S5b1 (indoor files) and S5b2 (`sketch.yml`) (6.4). Until a file has keys, `on` names an object
  with an `id` of its own (`door:vault_gate`, `thing:building_2`), or the pin has `at` only; the keyed form
  (`thing:building_2/parts/p3`) is accepted for a file once its format carries keys. A game pin always has its pose,
  so nothing is lost meanwhile.
- **`on` names the file where the id alone is not unique** [revision 4; 2.6 item 11]: ids are unique per file, and a
  plan space and its room may share one (`room:entry` in `plan.yml` and `rooms.yml`). A pin on such an id carries
  `file:` beside `on`, as an operation on it must; a pick in the 3D view gives the file through the provenance table.
- Made by `pin <text>` in the game (with the game's own picture); by `P` in plan, 3D or walk (slice 3 on); by an agent
  (`oymap pins add`, `map_pins add`). The first draft's "paste a `loc` line" box is dropped: the game command makes it
  unnecessary. [Review A7 1.6]
- The pose is stored as the game gives it (`loc`'s numbers, units named in the field), not converted; the studio
  converts for its camera. One less place where radians, degrees and 2048 units get mixed (2.15).
- The drawer lists open pins first; each shows its picture, its object, and its thread; "go to" restores its pose.
- An agent claims (`claimed`), changes the project, replies with what it did and pictures, and sets `resolved`; the
  person sets `accepted` or reopens. `map_pins` and `oymap pins` gain `claim` and the reply fields. [P: `map_pins`
  list, add, resolve]
- After a batch of fixes, `oymap pins tour` (a job in the browser) takes the game's own pictures at every open and
  resolved pin's pose, the lead's present practice made a command.
- **Pictures stay out of git by default** [Review A7, D9; reverses this document's first recommendation in 6.3]: dozens
  of maps with before and after pairs would sit in the repository's history for ever. They live in
  `.oymap/pins/pictures/` (git-ignored); the user keeps one on purpose (`keep: true`, or "Keep picture" in the panel),
  which copies it as a small JPEG into `review/pictures/`. On another clone a pin whose picture is not on the machine
  says so and offers its pose.

### 3.14 Compare with the original

For projects with `map_stats.reference` (rebuilds) [P: `oymap compare`, CALIBRATION.md]. Wireframe W6.

- **Indoor:** the score and its parts (shape, textures, offsets), the 40 worst points and every point that differs,
  as markers on the plan; a heat overlay; `shots.yml`'s places as a list.
- **Outdoor:** eleven parts (heights, relief, cliffs, rim, water, ground, roads, buildings, decorations, spawn points,
  events) and 64 regions as a heat grid; the worst regions with what differs; buildings paired with the original's.
- **Two 3D views with locked cameras**: the original (the shipped map read from the asset root) and the rebuild.
  Clicking a worst place moves both. The in-game pairs of `ingame_compare.py`, `outdoor_ingame.py` and
  `building_shots.py` come in as picture sets from jobs.
- A rebuild is measured again after each change only on request (it takes seconds to tens of seconds); the scorecard
  shows the revision it belongs to.

### 3.15 Render and picture views

The core's labelled plan and isometric renders [P: `oymap render`], and the game's pictures from jobs (screenshot
tours, `things_shots.py`, `building_shots.py`, in-game compare pairs, pin tours) appear in **Pictures**, grouped by job
and revision, as contact sheets that open full size. Any picture can be pinned. Pictures are files under the job's
folder (2.4) and are never part of the project unless a pin keeps one. [N]

### 3.16 Search and commands

`Ctrl K` finds commands (with their keys), objects by id or name, assets, stages and tools. Every action of the UI is
a command there; menus are not needed. [P: design page]

### 3.17 Keyboard and mouse

From the design page's table "Keys that stay the same everywhere" [P], with additions [N].

**Browser keys** [review A7, D8; this document's view beside it]: `F5` reloads the page and `Ctrl K` is the browser's
search key. Review A7 proposes an installable app window (a web manifest; it works on 127.0.0.1) to remove the
browser's keys. This document's view: `F5` and `Ctrl K` are not the problem, since a page can take both with
`preventDefault` on `keydown` in Chromium and Firefox (many web apps use `Ctrl K`); the keys a page cannot take are
`Ctrl W`, `Ctrl T`, `Ctrl N` and their kin, and none is in this table. The app window is still proposed (cheap; no
tabs, no address bar, more room), but the key table does not depend on it. Spike 5 confirms both keys in both
browsers; if one cannot be taken, Play here moves to `Ctrl Enter` and search to `Ctrl P`. **Spike 5's answer**
(S5-0) [revision 4]: in Chrome 153 and Firefox 157, headless and headed, the page receives `F5` and `Ctrl K` first and
can `preventDefault` them; Firefox's shipped key table reserves `Ctrl W` but neither of the two. Whether the browser
then skips its own action cannot be seen by automation, and Chrome's side is unconfirmed, so the user checks it by
hand (S5.md, "Still open"). Until he has, both fallbacks stay named, and the first slice that binds either key
(search in S5a2, Play here in S5a4) waits for the answer before shipping its binding.

| Key or gesture | Does | Source |
|---|---|---|
| `1` to `7` | stage | P |
| `Ctrl K` | search commands, objects, assets | P |
| `F5` / `Shift F5` | play here from the camera / from the party start | P |
| `Tab` | focus plan or 3D | P |
| `Q` | maximise the view under the cursor | P |
| `F` | frame the selection | P |
| `W` `E` `R` | move, rotate, scale (where the word has them: a building's `turn`, a part's `size`) | P |
| `[` `]` | grid smaller, larger | P |
| `PgUp` `PgDn` (`Shift`: ceiling) | floor under the cursor up or down by the grid | P |
| `Ctrl Shift C` / `Ctrl Shift V` | copy and paste a surface | P |
| `L` | link a trigger to a target (then click the target) | P |
| `H` | next height band | P |
| `G` | walk at party size | P |
| `Space` drag or middle mouse, wheel | pan, zoom | P |
| `Ctrl Z` `Ctrl Y` | undo, redo (your own changes, as revert entries, 2.7) | P, N |
| `P` | pin here | N |
| `Enter` / `Esc` / `Backspace` | finish / cancel a drawing / remove its last point (in walk, `Esc` leaves pointer lock: 3.6) | N |
| `Delete` | remove the selection (one transaction) | N |
| `Ctrl D`, `Alt` drag | duplicate | N |
| `Shift` click, box drag | add to the selection | N |
| `Ctrl S` | nothing to save: shows "saved at rev ..." (autosave) | N |
| `?` | the keys of the current tool | N |
| Right mouse in 3D | look; with WASD fly; `Alt` left: orbit the selection | N |
| Double click (plan) | enter a group (a building's parts, a room's platforms); `Esc` leaves it | N |

### 3.18 How each word is made and changed by hand

The vocabulary is what the schemas say today; this table is the plan of tools for S5b. "Generic" means: the tool
places the object with the geometry its `x-geom` fields need, then the inspector holds the rest. Every gesture ends in
one transaction; the operation is shown in the last column. An append (`/-`) into a keyed list gets its key from the
core; later edits address the item by that key (`/levels/<key>/...`), never by position (2.6).

**Editable is not usable by hand** [spike 7; review A7 on it]. Spike 7 made every field editable through the generated
form; that is G6's floor, not a hand author's tool. Where this table promises a bespoke tool (outlines, paths,
openings, doors, the wall bay strip, roads, the event form, the switch board, the brushes), a generic list of rows in
its place counts as a **miss** in the hand-author exit tests of S5b1 and S5b2 (6.4), like a word that forced the
Source tab.

**Indoor (`rooms.yml`, `objects.yml`, `wiring.yml`)**

| Word | Create | Edit by hand | Operations |
|---|---|---|---|
| room (`outline`) | Room tool: click corners on the plan (snaps to grid and other rooms' walls; Shift free angle), Enter | drag corners and edges; insert a corner by double-clicking an edge; floor and ceiling by `PgUp`/`PgDn` or in 3D by dragging the floor or ceiling | `add rooms`; `patch /outline/n` |
| corridor (`path`, `width`, `smooth`, `section`) | Path tool: click points, Enter; width in the options | drag points; width handle; section picked from a list or drawn in a small editor | `add rooms`; `patch /path`, `/width` |
| stairs and ramps (`slope: {to, toward, steps}`) | Stairs tool: drag across a room from the low side to the high side | arrow handle; steps count in options | `patch /slope` |
| levels, ceiling levels, platforms, pillars, beams, parapets, flights | Tool per word inside a selected room: draw an outline or a line | handles as for rooms; heights in the inspector | `patch /levels/-` and so on |
| uneven floors and roofs (`floor_points`, `ceiling_points`, planes, lines) | "Height points" tool in a room: click to add a point with a height | drag points; height by `PgUp`/`PgDn` | `patch /floor_points` |
| single walls, bands, panels, surfaces, `rough` | Select a wall in 3D or plan, then surface from the library (or `Ctrl Shift V`) | inspector | `patch /walls/-` |
| opening (`from`, `to`, `along`, `width`, `height`, `sill`, `shape`, `arch`, `reveal`, `in: floor`) | Opening tool: drag across the gap between two rooms; a floor hole by drawing on a floor | slide along the wall; width and height handles in 3D | `add openings`; `set` |
| theme | Library: pick wall, floor, ceiling textures and bands for a new theme | inspector; apply to rooms by drag | `add themes` |
| door (`kind`, `leaves`, `fold`, `hinge`, `thickness`, `travel`, surfaces) | Door tool: click an opening; the kind from the tool options | state scrubber in 3D; inspector | `add doors` (macro `door.in_opening`) |
| lift, mover (`parts`, `block`, `rides`), plate, floor (lava, water), ladder | Generic: draw the block or line | scrubber shows travel; inspector | `add lifts` and so on |
| switch (`kind: lever | button | plate`, `wall`, `along`, `height`, `side: top`) | click a wall (or a block's top) | slide along the wall | `add switches` |
| chest (`kind`, `size`, `items`, `lid`) | click a floor; kind from the options | facing handle; inspector | `add chests` |
| start, spawns, monsters, items, decorations, lights, sounds, exits, placeholders | click (a wall for wall decorations and torches) | drag; facing handle; radius handle | `add <list>` |
| wiring event (preset, `source`, `condition`, `effects`, `else_effects`, `trigger`, `once`, `side`, `question`, `window`) | Wire stage: select a source, `L`, click targets: makes a `switch` or `door` event; or "+ event" of a preset | the event form (W4): conditions and effects as rows | `add events`; `patch` |
| script handler (`script` preset, `lua`) | "Convert to script" on an event, or "+ script" | text editor with the script reference (`oymap script-reference`) as completion | `set` |
| plan (spaces, links, goals, keys, height bands, states) | Plan stage: bubbles and links on an empty plan | drag bubbles; inspector | `add spaces`, `add links` |

**Outdoor (`sketch.yml`, `atmosphere.yml`, `project.yml`)**

| Word | Create | Edit by hand | Operations |
|---|---|---|---|
| frame (`playable`, `edges`), rim (`side`, `span`, `form`, `crest`, `height`) | Shape stage: rim tool draws a stretch along the edge | handles; inspector | `patch /frame/...` |
| heights: `grid` (spot heights, at most 32 x 32) | Grid editor: each spot height is a handle with its number; `PgUp`/`PgDn` on the hovered spot | the same; paint a value over several spots | `patch /heights/grid/i/j` |
| heights: `points`, `cliffs`, `ridges`, `terraces`, `spires`, `peaks`, `cuts`, `rough` | Tool per word: click a point; draw a line; draw an outline | drag; heights and drops in the inspector | `patch /heights/points/-` and so on |
| heights: `nodes` (single node heights, absolute, applied last; they override every land word beneath them) | Rebuilds, under the lead's ruling; on new maps the brush writes strokes (next rows), not nodes (D15) | inspector; a node block's rows in the grid editor | `patch /heights/nodes/<block>/...` (keyed or path into the block and row: today only `set_value` of the whole list, 2.6 item 3) |
| land made by hand: a mark in the sketch (D15 extended) | Set only by a person in the UI ("this map's land is made by hand"); no procedure sets it, a rebuild refuses it | cleared by a person | `set_value` |
| sculpt strokes: raise, lower, smooth (a new word beside `nodes`, same block and row form, holding **differences** over the described land) | Brush: on maps agents edit (the default) only inside a bounded, marked patch; on land marked as hand-made over the whole map. The stroke is previewed in the browser (the client moves the mesh it has) and written once on mouse-up as one transaction; the core's land then replaces the preview | the brush again; a patch's outline by its handles | `patch /heights/<the new word>/...` |
| flatten stroke | Brush in flatten mode: writes a `terraces` entry (the stroke's outline, the height under the first press) | as a terrace | `patch /heights/terraces/-` |
| ground paint brush | Brush per kind of land: strokes merged per kind into zone outlines (at most three kinds per map, the classic format's limit) | the brush; the outline's handles | `patch /ground/...` |
| water bodies, liquids, tile sets | Draw an outline; pick a tile set | handles | `patch /water/bodies/-` |
| roads (`line` on cell centres, `width`, `surface`, `bed`) | Road tool: click cells; the line steps square or at 45 degrees as the world's tiles allow | drag points; bed heights per point | `add roads` (to make a collection) |
| ground zones (`kind`, `material`, `steeper_than`, `line`) | Draw an outline; pick the kind | handles | `patch /ground/-` |
| districts and plots (`space`, `polygon`, `plots[]`: `building`, `at`, `facing`; the footprint is the plan building's `footprint_cells`) | Draw a district's outline for a plan space; drag a plan building from the Checklist onto it to make its plot | move the plot by its corner; `facing` by the side handle (n, e, s, w); overlap and "inside the outline" are core checks | `patch /districts/<key>/plots/-` |
| structure `kind: building` (`at`, `size`, `turn`, `kit`, `parts`, `door`, `doors`, `porches`, `signs`, roofs) | Building tool: drag a box on the plan; first part made | double-click enters the building: parts as boxes, outlines, rounds; roof kind and pitch; the **wall bay strip** (W3) for each wall; doors by clicking a bay | `add structures`; `patch /parts/<key>/...` |
| other structure kinds (`wall`, `fence`, `bridge`, `well`, `fountain`, `obelisk`, `chest`, `crate`, `sign`, `platform`, `stairs`, `doorway`, `cave_mouth`, `hatch`, `culvert`, `waterfall`, `portal`, `arch`, `stone_ring`, `trilithon`, `walkway`, `deck`, `tent`, `arcade`, `barrier`, `decoration`) | Generic: a point, a line or an outline by the kind's `x-geom`, then the inspector | handles; inspector | `add structures` |
| `kind: model` (a shipped map's models taken whole) | Library tab "Models of shipped maps" of the project's world | move, `raise` | `add structures` |
| what a click does (`title`, `house`, `into`, `chest`, `condition`, `effects`, `else_effects`, `once`, `lua`, `trigger: step`) | Wire stage on the structure or door | the event form (W4) | `patch` |
| areas (encounters, items), actors (`monster`, `at`, `count`, `spread`, `group`, `hostile`) | Draw an area; click for actors | handles | `patch /areas/-` |
| scatter (`decoration` or `kinds`, `count`, `spacing`, `polygon`, `line`, `clusters`, `group`, `edge_thin`, ...) | Draw a polygon or line, pick decorations; the build places them | handles; count; "show placed points" (from the build) | `patch /scatter/-` |
| events (`trigger: load | timer | daily | weekly`) | "+ event" in Wire | the event form | `patch /events/-` |
| atmosphere (`sky`, `fog`, `weather`, `mist`, `sky_theme`, `flags`, `footsteps`) | Dress stage: the inspector on `atmosphere.yml` | inspector | `set_value` |
| map card (`map_stats`, `neighbours`, `qbits`, `items`, `rules`) | Plan stage: the inspector on `project.yml` | inspector | `set_value`; `add neighbours` |

**Land by hand (D15 extended, review A7 6.4)** [N]. The sketch as it stands has no place for land made entirely by
hand: `heights.nodes` holds absolute node heights, applied last, overriding every word beneath it; `heights.grid`
refuses a step finer than 4 cells ("a finer grid is a heightmap, not a sketch"); the ground is at most three kinds of
land laid by zone outlines (checked in `openyamm-studio/schema/sketch.schema.json`). So:

- **Rebuilds:** unchanged (described; `nodes` under the lead's ruling).
- **New maps made with agents (the default):** described first; sculpting only in bounded, marked patches (the user's
  decision of 15:11).
- **Hand-made land:** a person marks the project's land as hand-made; then the brush may cover the whole map. Agents
  see the mark on open and read such land through queries (`view.terrain_query`: height at a point, a profile along a
  line, slope), not by reading rows. The checks run on the built land either way.
- **Strokes are differences, not absolute nodes**, so an agent can still move a ridge or a road bed under a person's
  strokes and the strokes stay; absolute nodes would mask the change without a word. Settled in S5b2 by one test: an
  agent moves a ridge under a sculpted patch. **Reservation** (0.5): raise and lower are differences by nature; a
  smooth stroke is a correction computed from the land as it was and, stored as a difference, carries that land's
  bumps inverted onto a moved base. The test therefore covers a smoothed patch as well as a raised one; if the
  smoothed one ripples, smooth is stored as its own entry (outline and strength, applied by the build after the
  differences).
- **Commit cost:** an outdoor validation takes 0.7 to 1.6 s with assets (Erathia 1.64 s, appendix C), far too slow per
  brush sample, hence the preview and the one transaction on mouse-up. **Measured in S5-0** (spike 2) [revision 4]: a
  stroke on Erathia costs 1 305 ms median, 1 468 p95, the same for 63 nodes as for 676, because every stroke is one
  whole-map land lowering; and the request carries the whole node list (16.8 KB), since only `set_value` reaches
  `heights.nodes`. So: **one commit per stroke**, on pointer up; a keyed or path `patch` into the block and row the
  stroke touched (2.6 item 3); and in S5b2 the land kept up to the peaks (2.4.3), which brings a stroke to about the
  cost of a structure edit, within S5b2's 500 ms (2.13). The stroke word, like `nodes`, is applied after the kept land
  and stays out of its key.

**What the design page drew that does not exist as words** [C], and what S5 does about it:

| Design page tool | What exists | S5 |
|---|---|---|
| Landform brushes, coast stamp, 16-bit heightmap import | spot-height grid, points, lines, terraces and the rest; `heights.nodes` (the lead's ruling, for rebuilds: report scores with and without) | tools that write the existing words; sculpt strokes as differences and flatten as terraces by D15 (above); the heightmap import is outside S5's acceptance and the first addition after S5b2, a writer of the stroke layer (6.4); coast stamp deferred |
| Road splines that grade the land and choose tiles | road lines on cell centres with `bed` heights; the build lays tiles | the road tool above |
| A kit library of NWC prefabs in tiers with facings; plots that turn their door to the road | buildings described by parts, roofs and wall bays with `kit` roles; `kind: model` takes a shipped map's models whole; districts' `plots` place a plan building with a `facing` side (no automatic turn to the road) | a "Duplicate building" and "save as template" in the library [N], no prefab format; a "face the nearest road" button that sets `facing` [N] |
| Door library (portcullis, wooden door, double sliding, secret wall, ...) | door words (`kind`, `leaves`, `fold`, surfaces, `secret`) | a list of door presets in the tool options: each fills the words [N] |
| Switch board, sequence puzzle with simulator, landmark visibility, spell-trap path, puzzle simulator | presets and conditions; `solve` | switch board as a view (3.7); the rest deferred |
| Set-piece import with face matching | dropped on 2026-11-13 (PLAN 2a) | none |

---

## 4. Libraries and technologies

### 4.1 Summary

Licences checked against the repository's GPL-3.0 (`LICENSE`; the host's `package.json` says GPL-3.0-or-later): MIT,
BSD, ISC, zlib, OFL and Apache-2.0 are compatible with GPLv3 (Apache-2.0 with v3, not v2). EPL-2.0 is not, unless the
project names a secondary licence. Sizes are approximate, minified and compressed, from memory of the projects'
published builds: **to measure in spike S5-0**.

| Area | Choice | Alternatives considered | Licence | Size | Risk | Cost to replace |
|---|---|---|---|---|---|---|
| UI framework | React [P] (version 19 [N]) | Preact, Svelte 5, SolidJS, Vue 3, Lit, none | MIT | ~45 KB | low | high (every panel) unless views stay framework-free |
| Layout | fixed CSS grid of the design page's frame [N]; Dockview later if wanted [P] | Dockview, FlexLayout, golden-layout, rc-dock | MIT | 0 | none | low |
| 3D | three.js, pinned, WebGL2 renderer first [P, N] | Babylon.js, PlayCanvas, own WebGL2/WebGPU, bgfx in wasm, regl | MIT | 134 KB gzip (the classes used; spike 1) | medium (monthly releases) | medium (one module) |
| Picking acceleration | none at first: 30 000 triangles need no tree; three-mesh-bvh [P] if spike 1 says so [review A7, D6]. **Spike 1** [revision 4]: no tree indoors (p95 1.0-3.3 ms without one); outdoors the terrain picked in chunks of 16 x 16 cells; three-mesh-bvh only if MM9's maps need it, after checking its hits (its first hit differed from Raycaster's, untraced) | own BVH, GPU picking | MIT | 22 KB gzip (measured) | low | low |
| Plan view | own Canvas2D + SVG [N] | Konva, PixiJS, Paper.js, Fabric | n/a | 0 | none | n/a |
| Flow graph | own SVG, layout by solve steps [N] | Cytoscape.js, dagre, elkjs, React Flow | n/a | 0 | none | n/a |
| UI state | Zustand [P] | Redux Toolkit, Jotai, MobX, signals | MIT | ~1 KB | low | low |
| Server data | own revision-keyed RPC client [N] | TanStack Query | n/a | 0 | none | low |
| Text editor | CodeMirror 6 [N] | Monaco [P] | MIT | ~150-300 KB | low | low |
| Forms | own schema-form renderer [N] | react-jsonschema-form, JSON Forms | n/a | 0 | none | n/a |
| Styling | plain CSS with custom properties (the design tokens) and CSS modules [N, 4.16] | Tailwind, CSS-in-JS (Emotion, vanilla-extract), a component kit's theme | n/a | 0 | none | medium |
| Interface primitives (menus, popovers, combo boxes, dialogs for confirmations, tooltips, trees) | one headless library: **Base UI** recommended, Radix Primitives the runner-up [N, 4.16] | React Aria Components, Ark UI, own code, a styled kit (MUI, Mantine, Chakra) | MIT (Base UI, Radix, Ark UI); Apache-2.0 (React Aria) | tens of KB, to measure | medium | medium |
| Long lists | one virtualiser: TanStack Virtual [N, 4.16] | react-window, Virtuoso, virtua | MIT | ~5 KB | low | low |
| Command palette | own, on the primitives' combo box [N, 4.16] | cmdk | MIT | small | low | low |
| Icons, fonts | the old editor's icon kit (`editor/assets/editor_ux_work/icons/`, 25 SVGs, moved into `web/` before S7 deletes `editor/`) plus Lucide; IBM Plex (the design page's) | Material icons, system fonts | ours; ISC; OFL | small | low | low |
| Language and build | TypeScript, Vite [N] | no build (ES modules, import maps, `htm`, JSDoc types), esbuild alone, Bun | Apache-2.0; MIT | dev only | medium (npm) | medium |
| Wasm toolchain | Emscripten 4.0.10, pinned [P] | none practical for this C++ | MIT/UIUC | dev only | medium (pin) | n/a |
| Wasm bindings | plain C ABI, JSON in and out, buffers [P] | Embind, wasm-bindgen-like generators | n/a | 0 | none | low |
| zstd and BC decode | local mode: the host un-frames with `node:zlib` (zstd in Node 24), asynchronously, with an LRU of un-framed blocks; hosted mode: the core's own zstd in the wasm worker; BC uploaded to the GPU; **no CPU BC decode** (spike 5: every browser and software GPU tested takes BC1, BC5 and BC7) [N; review A7, D7; revision 4] | fzstd (JS), zstd-codec | BSD (zstd) | in Node and the core | low | low |
| Host | Node LTS, plain JS; MCP SDK 1.32.2, ws, zod [P] | Deno, Bun, a C++ host | MIT | n/a | low | high |
| File watching | Node's `fs.watch` recursive [N] | chokidar | n/a | 0 | low | low |
| Tests | Vitest; Playwright [P]; an RPC contract suite native against wasm; a panel gallery screenshotted by Playwright; a schema lint; the 22-project native-against-wasm comparison and a sanitizer job [N; revision 4] | Jest, Cypress | MIT; Apache-2.0 | dev only | low | low |

### 4.2 UI framework

**React** (PLAN 9). Alternatives: Preact (the same API in 4 KB; compatibility layer for libraries), Svelte 5 and
SolidJS (smaller and faster updates, a compiler or signals, smaller ecosystems), Vue 3, Lit (web components), or no
framework. Why React: the panels are forms, lists, tables and trees, which React does well; agents write React more
reliably than any other UI code (the studio will be built and maintained mostly by agents); its ecosystem has
CodeMirror and Dockview bindings; it is stable and not going away. The cost of replacing it is limited by a rule
[N]: **the plan view, the 3D view, the flow graph and the RPC client are framework-free modules** (plain TypeScript
over a canvas or an element) that React panels mount. Only forms, lists and the frame are React. Preact is the
fallback if bundle size ever matters (it will not, against a 2 MB wasm core).

### 4.3 Layout: fixed first, docking later

PLAN 9 names Dockview (MIT; one main maintainer; React and plain bindings). The design page's frame is fixed (rail,
options bar, two views, inspector, drawer) with `Q` to maximise a view and `Tab` to move focus; nothing in the
acceptance tests needs panels dragged around. Proposal [N]: a fixed CSS grid with resizable splitters and saved sizes;
docking only if users ask for it. Panels are components either way, so adding Dockview later costs days. **Changes
PLAN 9** (decision D8).

### 4.4 The 3D renderer

Requirements: draw the core's meshes (tens of thousands of faces, a few hundred textures), BC-compressed textures from
our own container, billboards, lines and labels, picking, a walk camera; work in Chromium and Firefox on desktop;
GPL-compatible; small team, long life.

| Option | For | Against | Verdict |
|---|---|---|---|
| **three.js** (MIT) | the most used web 3D library; compressed textures through `CompressedTexture`; `BufferGeometry` takes our buffers as they are; picking with three-mesh-bvh; WebGL2 mature, WebGPU renderer maturing; agents know it well | a release a month with breaking changes (we pin and upgrade on purpose); its newer WebGPU path uses a different material system (TSL) | **chosen** [P] |
| Babylon.js (Apache-2.0) | stable API with long deprecation; batteries (GUI, inspector, gizmos) | several times larger; fewer agents know it well; the batteries are not what we need | runner-up |
| PlayCanvas engine (MIT) | fast, small | engine built round its editor; smaller community | no |
| Own WebGL2 or WebGPU | smallest, no churn | picking, text, lines, camera controls, texture formats all ours; months of work | no |
| bgfx in wasm (BSD-2), the game's renderer | the game's look and shaders | the game's renderer is not separable (it is part of `engine/` and `game/` with SDL; PLAN 1's cuts keep rendering out of the core); its shaders target the game's data; overlays, picking and editing still to build; the exact look is Play here's job [P: PLAN 9] | no |

WebGL2 first [N]: PLAN 9 says "WebGPU renderer with WebGL2 fallback". WebGL2 runs everywhere the editor must run and
takes BC textures through extensions; three.js's WebGPU renderer and its material system are the newer and moving
part. The views use plain unlit or simply lit materials and one custom shader for the terrain's tile blend and one
for liquids [P: PLAN 9 "terrain blending, lightmaps and fog are the only shaders ported"], small enough to write for
both later. **Changes PLAN 9's order** (decision D8).

Containment [N]: one `viewport` module owns three.js; the rest of the app talks to it in our terms (load mesh, set
texture, highlight ids, camera pose). An upgrade or a replacement touches that module only.

**Measured in S5-0** (spike 1, three.js 0.186.1 pinned, WebGL2) [revision 4]: 59-60 fps on Darkmoor, Harmondale and
Darkmoor seven times over (74 773 triangles) in Chrome and Firefox; GPU memory +33 and +141 MiB; three.js's share of
the bundle 134 KB gzip. **The viewport handles WebGL context loss**: a fresh headless Chrome lost its context once at
about 0.4 s. The viewport keeps what it uploaded (mesh buffers, the un-framed texture blocks) or can fetch it again
by revision, and on `webglcontextrestored` re-uploads everything without asking the core for anything new.

### 4.5 Plan view and flow graph: own code

The plan view draws polygons, lines, glyphs, labels and one raster (outdoor heights): Canvas2D for the bulk (tens of
thousands of segments redraw in milliseconds) and an SVG layer for handles and text. Libraries (Konva, PixiJS,
Paper.js) add a scene graph we would keep in sync with our own state for no gain. The flow graph is a layered drawing
whose layers are the solve's steps; the general layout libraries are either unmaintained (dagre), large (Cytoscape.js,
about 400 KB) or EPL-2.0 (elkjs, a GPL problem). Own code, with Cytoscape.js as the fallback if graphs of a world
(70 Xeen maps) need general layout. [N]

### 4.6 State

- **Documents are not state the client owns.** The client keeps, per project, the files' JSON trees at a revision as
  read-only data; each edit result replaces the files it names. Nothing in the client is the truth. [P: PLAN 5]
- **UI state** (selection, tool, camera, panels, filters) lives in Zustand stores (PLAN 9), small, framework-agnostic,
  usable from the non-React modules.
- **Server data** (layout, meshes, scorecards, history) is cached by revision in a small RPC client; a new revision
  invalidates by key. TanStack Query would do the same with more machinery. [N]

### 4.7 Text editing: CodeMirror 6 instead of Monaco

The Source tab, Lua handlers, playtest scenarios. Monaco (PLAN 9; MIT) is VS Code's editor: about 2.5 to 5 MB, its
own web workers, awkward to bundle and to theme, little gain for YAML and Lua. CodeMirror 6 (MIT) is modular, small,
works inside our layout without workers, has YAML and Lua modes and a completion API we feed from the schemas and the
script reference. **Changes PLAN 9** (decision D8). [N]

### 4.8 Forms from the schemas

Section 3.8. react-jsonschema-form (Apache-2.0) and JSON Forms (MIT) each bring their own layout and validation
models and handle cross-file `$ref` and our `x-` keys only through customisation as large as writing the subset.
Validation stays in the core (README decision): the client checks types while typing and sends; the core decides.
Defaults too: the form shows the effective values the core's resolved read returns (3.8). Own code. [N] Spike 7
drew every building and room of the 22 projects with about 1 300 lines of generator, on Base UI parts; its one gap is
the number field, which cannot take arithmetic (`512*3`), so numbers are an input with an own expression parser.

### 4.9 Build tooling: does "no build step" hold for S5?

PLAN 8, as built in S2: the host is plain JavaScript modules with no build step. **For the host it holds** and should
stay: it is small, it runs from the repository with `node`, and every added step there is friction for the user.

**For the web app it does not** [N]. A no-build web app is possible (ES modules, an import map to vendored copies of
the libraries, `htm` in place of JSX, types as JSDoc checked by `tsc --noEmit`), and it would keep the studio free of
a bundler. Against it: TypeScript types generated from the RPC and project schemas are the main protection against
the interface drifting, and they want real TypeScript; three.js and CodeMirror ship as many small modules that a
browser would fetch one by one; the wasm worker wants bundling; and the hosted page wants hashed, cacheable files.
**Proposal:** `openyamm-studio/web/` in TypeScript, built by **Vite** (MIT; Rollup and esbuild under it), its output
`web/dist/` served by the host. Not committed: built by `./build.sh web` locally and in CI, and shipped in releases
(D12). Development: Vite's dev server on `localhost:5173`, already in the host's Origin allow list.

Supply chain [N]: exact versions, `package-lock.json`, `npm ci`, a short list of direct dependencies (section 4.1),
upgrades on purpose with a changelog read, no post-install scripts allowed (`--ignore-scripts`) where the packages do
not need them.

### 4.10 The wasm toolchain and the core's dependencies in wasm

Emscripten **4.0.10**, pinned [P: wasm/README.md]: newer libc++ fails on `std::vector<bx::Vec3>`; raising the pin
needs a newer bx or the core's own vector type (PLAN 13). Flags: `-fwasm-exceptions` on every target (yaml-cpp
throws), `-sSUPPORT_LONGJMP=wasm` (Lua), `-ffp-contract=off` (same bytes as native), no pthreads [P: PLAN 3]. The
core's dependencies in wasm: yaml-cpp (MIT), PhysicsFS 3.2 (zlib), Lua 5.4.8 (MIT), zstd (BSD), bx's math only
(BSD-2), cgltf (MIT, taken from bgfx's third-party folder today; vendor it [P: PLAN 1]), stb_image_write (public
domain or MIT) [P: CODE_SURVEY, PLAN 1]. Known traps: `YAML::Emitter` breaks the program's exit under wasm (write YAML
through `core/CanonicalYaml` only); environment variables do not pass; `size_t` is 32-bit; no iteration over
unordered containers on the way to output [P: PLAN 3, wasm/README.md].

Two wasm artefacts [N]: the existing command-line build for Node (`-sNODERAWFS=1`, the CI smoke test and the contract
suite), and a **worker build** for the browser exporting `oymap_call` and the buffer functions, with an in-memory
file system for project files and a PhysicsFS `PHYSFS_Io` over JavaScript reads. The worker build needs PhysicsFS to
start under Emscripten, which today fails.

**Byte identity is proven in S5-0, not in S5c** [Review A7 1.5]. Today `tests/native_vs_wasm.sh` builds two example
projects (`gatehouse_cellars`, `shapes_gallery`); the wasm core cannot open an asset root, outdoor validation and builds
read one, so no outdoor project has ever been built in wasm; roofs, rounds and domes use trigonometry, and glibc's libm
and Emscripten's are different libraries. Identical bytes are S5c's acceptance and PLAN's rule (a map's bytes decide
whether saves keep their map state), and PLAN's fallback ("cut hosted mode down to view and review") covers memory, not
this. Found in the last phase, it would mean changing lowering code every calibrated map depends on. So S5-0 makes the
**Node** wasm build read an asset root (with `NODERAWFS` the host file system is there; what fails is PhysicsFS's
start), builds **all 22 projects** (the 16 rebuilds under `devdocs/map_studio/briefs/*/L4` and the 6 new maps under
`devdocs/xeen/briefs/*/L4`) with both builds and compares every output byte. Where they differ, the fix is the core's
own deterministic functions for the trigonometry the lowering uses (or rounding at the point where results become map
units), decided from what the spike finds. The browser worker build and PhysicsFS over JavaScript reads stay S5c's first
task.

**What spike 6 found, and the emphasis it changes** (S5-0; S5.md) [revision 4]. The Node wasm build reads an asset
root with two changes (a ten-line `--pre-js`, `wasm/node_env.pre.js`, copying `HOME`, `XDG_DATA_HOME` and `OYMAP_*`
from Node into Emscripten's environment, since PhysicsFS needs a user directory and Emscripten's `/home/web_user` does
not exist under `NODERAWFS`; and the removal of an `#ifdef __EMSCRIPTEN__` that switched asset reads off outdoors).
This also lifts the trap "environment variables do not pass" for the Node build. The browser worker's PhysicsFS needs a
HOME in its own file system (S5c). With it, 21 of the 22 projects build byte-identical; the 22nd (13 bytes of
Erathia's `.odm`) is **not trigonometry**: a `std::clamp(v, lo, hi)` with `lo > hi` in the deck posts, undefined
behaviour that libstdc++ answers with `hi` and libc++ with `lo`. Written out, 22 of 22 are identical and the native
output is unchanged. glibc's and musl's math do differ (5.4 % of distinct `hypot` inputs, 1-3 % of `sin`, `cos`,
`tan`, `atan2`, `cbrt`, by 1 ulp), but no difference reaches a byte, because the lowering rounds to whole units. So
**the risk to byte identity is undefined behaviour answered differently by the two C++ standard libraries, not libm**,
and the guard is:

- **A sanitizer job over the 22 projects**: natively ASan and UBSan with `_GLIBCXX_ASSERTIONS`, and in wasm ASan (with
  libc++'s container annotations). Each found sites the other missed (five in all: two natively, three more in wasm).
  The wasm half is slow (1.5 to 26 minutes a build under ASan at high load), so it need not run on every merge; where
  it runs is settled when its scripts land.
- **The UB sites fixed**: the yaml-cpp iterator temporaries and `triangulateRegion` (twenty-third merge); the deck-post
  clamp, `mergeFlatTriangles` and `unionTouching` after S5-0. The clamp needs a rule for a post on an edge shorter
  than the post (centre it or skip it), the core owner's to set; until then `std::min(std::max(...))` keeps today's
  bytes.
- **The 22-project comparison in CI** (`tests/native_vs_wasm.sh` extended from two example projects; about 45 s for
  both sides at load 20).
- **The core's own math, as insurance**: musl's math sources (MIT) compiled into the core on both sides behind
  `oy::sin`, `oy::cos`, `oy::hypot` and the rest. Compiled natively they reproduce wasm bit for bit on all 3.2 million
  distinct inputs the 22 builds use, leave all 22 native builds byte-identical, and cost nothing measurable; they also
  remove the dependence on Emscripten's libc version. The walk uses them too (2.10).
- **No `long double` in lowering code**: `HeightMesh.cpp`'s `inPlane` compares `long double` products, 80-bit natively
  and 128-bit in wasm; safe today for whole-unit maps under 2^64, so new code keeps `long double` out or its products
  under 2^64 by construction.

Other facts from the spike: the core uses no `std::*_distribution` and no unordered iteration on the way to build
output (`core/Compare.cpp` iterates an `unordered_map` for a scorecard only); wasm builds of dungeons take about 300 MB
more memory than native in Node (346-407 MB against 35-69; the heap never shrinks), not investigated, a point for S5c's
1 GB budget (R8).

### 4.11 Textures in the browser

Section 2.11. In local mode the host un-frames `.oytex` with `node:zlib`'s zstd and serves the blocks, so textures do
not depend on the wasm build [Review A7, D7]; in hosted mode the worker uses the core's own zstd. No JavaScript zstd
library is needed [N]. BC blocks go to the GPU as they are. ~~A CPU fallback (BC7 decode to RGBA in the worker) is
built only if spike S5-0 finds a target browser without the extensions.~~ **Dropped** (S5-0, spike 5) [revision 4]:
Chrome and Firefox on a real GPU and every software GPU CI would use take BC1, BC5 and BC7 in WebGL2 (2.11).

### 4.12 The host's own dependencies

Node LTS (24 on the development machine), `@modelcontextprotocol/sdk` 1.32.2 (MIT), `ws` (MIT), `zod` (MIT) [P]. S5
adds static file serving and HTTP byte routes (Node's `http`, no framework), the file watcher (`fs.watch` with
`recursive`, supported on Linux, Windows and macOS since Node 20), the job queue and the session registry: no new
dependencies [N]. Streamable HTTP for MCP comes from the SDK.

### 4.13 Testing

- **Core**: doctest as today (`build/oymap_tests`, 323 cases at the twenty-third merge); new cases for the revision
  classes, the cache, keyed `patch`, rename, id allocation, merging, rebase, revert entries (with the snapshot restore
  as the oracle), severities and the skipping lowering, provenance and layout.
- **Schema lint** (3.8): annotations every form needs; an allow list that only shrinks, starting at today's 1 208
  issues; in the web app's Vitest suite (it uses the form generator's classification) and in CI, from S5a2.
  [Review A7, D5; revision 4]
- **RPC contract**: one suite against native `serve` and against the wasm build under Node; results equal; a recorded
  walk replayed on both gives the same poses, on a map with a rotating mover among them; **one wasm instance kept
  alive across the calls**; cases for every typed refusal, `locked` and `failed` included; `gen.mjs --check` in CI.
  [N; revision 4]
- **Native against wasm builds**: all 22 projects, every output byte (from S5-0 on, in CI). [Review A7 1.5]
- **Sanitizers** over the 22 projects: native ASan and UBSan with `_GLIBCXX_ASSERTIONS`, and wasm ASan (4.10).
  [Revision 4]
- **Host**: the existing MCP test (`node test/mcp.test.mjs`), plus WebSocket method tests, path-jail tests and job
  tests; Vitest if the suite grows (PLAN 11). [P, N]
- **Web unit**: Vitest for the RPC client, stores, the schema-form renderer and the plan view's geometry helpers.
- **UI end to end**: Playwright on the five acceptance maps (PLAN 11): open, walk a route, pin, see an agent's
  resolution (a scripted agent: a test that calls `map_pins` and `map_edit`), draw a room, undo, rebase.
- **Visual regression**: the plan view is deterministic Canvas2D and compares exactly; 3D screenshots with a fixed
  camera on a software GPU (SwiftShader or llvmpipe in CI) with a tolerance, since GPUs differ. **Spike 5** [revision
  4]: the software GPUs take BC1, BC5 and BC7, decoding BC7 exactly and BC1 and BC5 within 1 and 3 levels, so the
  tolerance is a few levels and no CPU decode is needed. **Spike 1**: they draw a dungeon at 3.6-16.7 fps and an
  outdoor map at 0.5-4 fps (up to about 4 s a frame on llvmpipe), so CI screenshots dungeons as they are and outdoor
  maps as single frames at a smaller size. Headless Chrome uses SwiftShader unless given `--use-angle=vulkan
  --enable-features=Vulkan --ignore-gpu-blocklist`.
- **A panel gallery for a UI written by agents** [Review A7 3; R15]: agents cannot see the page, so `web/` has a
  gallery page showing every panel in each of its states (empty, loading, error, stale, a long list, a conflict) with
  fixed data; Playwright screenshots it, and the agent that built or changed a panel must look at those pictures
  before reporting. The wireframes (`s5_mockups/wireframes.html`) are the reference the pictures are judged against.
- **Performance**: the budgets of 2.13 as tests over the largest projects, measured on the development machine and
  recorded per merge, as the rebuild scores are.

### 4.14 Packaging and distribution

- **In the repository**: `./build.sh` builds `oymap`; `./build.sh web` builds `web/dist`; `node
  openyamm-studio/host/src/host.mjs studio` starts the host with the web app and opens the browser.
- **For modders and players** (decision D12): (a) a release download that ships `oymap`, the host as a Node single
  executable application (Node's own feature; no Node install needed), and `web/dist`, started by `oymap studio`; or
  (b) only the hosted page, with agents and Play here for those who build from the repository. The hosted page needs
  a static origin: the release server of packaging/RELEASE.md or GitHub Pages, with a versioned path per release.
  Review A7: an **origin of its own** (a subdomain such as `studio.<release host>`), not a path on a shared origin,
  since folder permissions (File System Access) and browser storage are granted per origin. This document agrees;
  the versioned path stays inside that origin.
- **Desktop shells** (Electron, Tauri) were considered and are not proposed: they would make a third front end with
  its own file access and updater, while the browser plus a local process already gives everything [N].

### 4.15 What it costs to change a choice later

The decisions that are expensive to reverse, so they deserve the review: the RPC catalogue (every front end speaks
it); the operation model with `patch`, authors and rebase (agents and history depend on it); the provenance table
(picking, pins and highlights depend on it); `x-geom` and the schema-driven inspector (every field's UI depends on
it); React for the panels; the styling method and the primitives library (every panel uses them, 4.16). Cheap to
change: the layout, the text editor, the state library, the icon set, docking, and (thanks to the viewport module)
the 3D library.

### 4.16 Styling and interface primitives [N, D8; review A7]

Review A7 found a gap: no decision on styling or on the interface primitives (menus, popovers, combo boxes, trees,
long lists, the command palette). Left open, agents will write each one three times. Proposed now, with the
alternatives:

| Need | Proposal | Alternatives and why not first |
|---|---|---|
| Styling | **Plain CSS with custom properties and CSS modules** (Vite supports both without a plugin). The design tokens (colours, spacing, type sizes, the light and dark sets) are custom properties in one file; each component has its `.module.css`. | **Tailwind** (fast to write, agents know it; but class strings become the design system, long markup, a build plugin, and its upgrades have been breaking); **CSS-in-JS** (Emotion: runtime cost and React coupling; vanilla-extract: typed and static, a good second choice, but one more build tool); **a component kit's theme** (MUI, Mantine, Chakra: fast start, their look and their upgrade cadence for the product's lifetime) |
| Primitives | **Base UI** (MIT; headless; from the authors of Radix, Floating UI and MUI; 1.x): menus, popovers, combo box, select, dialog (for confirmations only: 3.9 says no modal dialogs for work), tooltip, tabs, slider, checkbox. **To verify in S5-0:** its version and release history at the time of the choice. | **Radix Primitives** (MIT; the most used, very solid; its own team now works on Base UI, so its future pace is the question): the runner-up and an easy switch, since the component shapes are close; **React Aria Components** (Apache-2.0; the strongest accessibility and keyboard model, internationalisation built in; larger and a more verbose API); **Ark UI** (MIT; state machines, works across frameworks; smaller community); **own code** (focus traps, positioning, keyboard rules: weeks, and wrong in the details) |
| Trees (Outline, file tree) | Own, on the virtualiser below, with the WAI-ARIA tree keyboard rules; React Aria's tree if the primitives choice is React Aria | react-arborist (MIT; complete, but its own drag and data model) |
| Long lists (Outline, Library, Issues, History) | **TanStack Virtual** (MIT, headless, small) | react-window (smaller, fixed shapes), Virtuoso (MIT, convenient, larger), virtua |
| Command palette (`Ctrl K`) | Own, on the primitives' combo box, fed by the command registry (3.16) | **cmdk** (MIT; the usual choice, small; a fine alternative if the own version grows) |
| Icons | Lucide plus the old editor's kit (4.1) | none |

Rules for `web/` that follow (R15): no other UI library without a decision; no inline styles except computed
geometry; every colour from a token; every panel in the gallery (4.13).

Recommendation: plain CSS modules, Base UI, TanStack Virtual, own palette and trees. **A question for the user
(D8)** only in the sense that it fixes the look of every panel for the lifetime of the product; this document
recommends deciding it with D8, not later.

---

## 5. Workflows in detail

Each workflow names the gestures, what goes to the core, and what comes back. Operations are written in the proposed
form (2.6); where today's form differs, it is said.

### W1. Building a dungeon by hand (S5b1)

The Old Crypt of the S3 evaluation ("an L-shaped antechamber, a bent corridor, stairs down, a crypt with pillars and a
dais, a side chamber behind a lever-operated door, two chests"), which an agent built in 59 tool calls [P: S3
Evaluation]; by hand:

1. **New project** (`project.new {folder, id: crypt01, name: "The Old Crypt", world: mm6, stats_id: <next free>}`):
   one masonry theme, no rooms; one issue ("no rooms") in the drawer. [P: `map_new`]
2. **Plan** (stage 1): five bubbles (antechamber, corridor, stairs, crypt, side chamber) with purposes; links; a key
   `key:lever` and a goal (the two chests). `add spaces` ×5, `add links` ×4, `add goals`. The checklist: five spaces
   without rooms.
3. **Antechamber** (stage 2, Room tool `D`): six clicks on the 64 grid draw the L, Enter. The ghost dry-runs on the
   last click (W2's line "+1 room, 0 new issues, 1 fixed"). Enter sends `add rooms {id: room:antechamber, outline:
   [...], floor: 0, ceiling: 384, space: space:antechamber}` and the start: `set_value objects.yml start {room:
   room:antechamber}` (an empty project refuses a first room without a start [P: `map_new` text]). The plan draws the
   room at once; 3D follows in under a second.
4. **Corridor** (Path tool `H`): click four points from the antechamber's east wall; width 256 in the options; Enter:
   `add rooms {id: room:corridor, path: [...], width: 256, smooth: ...}`. A gap of 32 to the antechamber's wall is the
   wall's thickness [P: S0 lesson "walls have thickness"]; the status line says so.
5. **Opening** (`O`): drag across the 32 gap: `add openings {from: room:antechamber, to: room:corridor, along: 0.5,
   width: 192, height: 256}`. Teal on the plan; walls cut in 3D.
6. **Stairs**: a room drawn at the corridor's end, then the Stairs tool dragged from its high side to its low side:
   `patch room:stairs [{add: /slope, value: {to: -512, toward: south, steps: 12}}]`.
7. **Crypt**: a room at floor -512; pillars with the Pillar tool inside it (`patch /pillars/-` ×4); a dais with the
   Platform tool (`patch /platforms/-`, height 64).
8. **Walk** (`G`) from the start through the corridor and down the stairs. A doorway the party cannot pass shows as
   an issue on the opening (from the reach check, `oymap probe`'s reason in its text).
9. **Side chamber and its door**: room, opening, then the Door tool on the opening with kind `slide_up` from the
   options: `add doors {opening: open:crypt_side, kind: slide_up, ...}`; scrubber in 3D.
10. **Lever** (stage 4): Switch tool on the crypt's wall, kind `lever`: `add switches {room: room:crypt, wall: east,
    along: 0.3, kind: lever}`. Then `L` on the lever and a click on the door: `add events {id: evt:lever_gate,
    preset: switch, source: switch:lever, toggles: [door:side_gate], title: Lever}` (section W3).
11. **Chests** (Chest tool, kind `ch1` from the options) in the side chamber and on the dais; contents in the
    inspector.
12. **Theme** (stage 3): pick textures from the library's MM6 crypt family; apply to rooms by dragging onto them.
13. **Lights and torches** (stage 6), **spawns** (stage 5) from the map's monster slots.
14. **Test** (stage 7): the solve shows the side chamber opening at step 2 by `evt:lever_gate`; `scale_bands.py`
    says whether the crypt is big enough; Play here; the checklist empties.

What makes it fast or slow: steps 3 to 7 are about twenty gestures, each one transaction of a few hundred
milliseconds (with the cache of D1). Without the cache each gesture waits about a second.

### W2. Building a town (S5b2)

On an outdoor project (a rebuild's town block, or Vertigo's next pass), following TOWN_FEEL.md and the measured
sections of OUTDOOR_REBUILD_PROCEDURE.md:

1. **Land under the town** (stage 2): spot heights on the grid editor (`patch /heights/grid/i/j`), a terrace for a
   row of shops (`patch /heights/terraces/-`, with `steps`); town feel wants 500 to 1 000 of relief and a flat share
   of 0.73 to 0.97 [P: TOWN_FEEL 8].
2. **Roads** (Road tool): click cells from the arrival to the square; the line steps at right angles with short runs
   (2 to 6 cells), offset junctions, the longest straight under about 11 cells; a road to a neighbour runs to the map
   edge [P: TOWN_FEEL 3; OUTDOOR_REBUILD_PROCEDURE]. `add roads` (a new collection, D3).
3. **Buildings** (Building tool): drag a box for a house; the first part appears with the world's ordinary house
   words [P: "A plot that says nothing is the world's ordinary house"]. Double-click enters it: add a second part for
   an L, set roofs (`hip`, `gable`, ...), and on the **wall bay strip** (W3) place the door bay; the door's `house`
   comes from the service picker over the house table. Houses on the compass axes, setbacks and plot sizes varied, a
   lane to every door within a few hundred units [P: TOWN_FEEL 2, 3].
4. **Services**: tavern among the first houses from the arrival, weapon and armour shops near each other, guilds in a
   pair or row, the temple apart or raised [P: TOWN_FEEL 4]. The scorecard shows these ranks live from the last
   `town_feel.py` job.
5. **Things**: wells and fountains (two to five, one that gives a stat), signs at junctions, an obelisk somewhere on
   the map [P: TOWN_FEEL 6, 7]; their click words in the Wire form.
6. **People and monsters** (stage 5): townsfolk and guards as actors (guards in pairs at gates and bridges, singles
   on streets), the town kept clear of monster groups [P: OUTDOOR_REBUILD_PROCEDURE "Guards in towns", "Monsters by
   habitat"].
7. **Trees and flowers** (stage 6): scatter areas with even spacing (Clark-Evans R 1.4 to 1.8; `clusters` only for
   small things) [P: OUTDOOR_REBUILD_PROCEDURE "Tree spacing"].
8. **Check**: the `town_feel.py` job; its flagged figures in the scorecard with their places; `building_shots.py`
   pairs when it is a rebuild; walk the streets; Play here.

### W3. Wiring a door and a lever

1. Select the lever (made in W1 step 10); press `L`; the cursor shows a link; click the door on the plan or in 3D.
2. The core receives `add events {id: evt:lever_gate, preset: switch, source: switch:lever, toggles:
   [door:side_gate], title: Lever}`. (Today: `{op: add, to: events, value: {...}}`.) The link shows dashed gold in
   both views [P: design page "Connections are visible"].
3. The event form (W4): add a condition (`qbit`, `item`, `map_var`, `gold`, `stat`, `award`, `kills`, `not`, `any`,
   `all`), effects (`text`, `gold`, `add`, `set`, `autonote`, `qbit`, `give_item`, `damage`, `cast`, `summon`,
   `teleport`, ...) and else effects; `once`; the lever's picture follows its state by itself [P: S3 switch kinds].
4. The right column shows what the built handler does (`flow`) and where the solve opens the door. The checks say
   whether a failed condition is silent (`click.silent`) and whether a question's answer is met before it is asked
   (`question.answer`) [P: indoor batch nine].
5. Walk: click the lever; the studio toggles the door (the studio's state only). Play here: the game runs the real
   handler.

### W4. Placing monsters

1. Map card (stage 1): the map's monster slots in `project.yml` `map_stats` (or the reference map's) [P: S0 lesson].
2. Spawn tool (stage 5): click to place `add spawns {room, at, slot or rank, radius, group}` (indoor), or draw an
   encounter area `patch /areas/-` (outdoor). Placed monsters with `group`, `hostile`, `hidden`, `carries`, a boss's
   `hp` and `name` are `add monsters` [P: objects schema].
3. The density overlay shows monsters per area against the shipped bands; the checks warn of a monster where it
   cannot come out to the party (REBUILD_PROCEDURE "Monsters where they can fight") [P]; outdoors the town-feel
   figures (groups 47 to 88, spacing variation above 0.5, nothing within about 4 500 of a start town's doors) [P].
4. Over a lift or mover, a spawn stands on its top as the map starts; the build refuses what cannot [P: S3].

### W5. Checking: audit, town feel, room sizes, compare

- **Always**: tier 0 inside every edit (schema, references, scale) as the Issues drawer's delta. [P: PLAN 6]
- **In the background after each change, on lane J** (debounced: a few seconds after the last gesture): `audit` with
  coplanar faces matched against the original, reach and `solve`. Results replace the previous ones when they finish;
  stale ones are greyed. [N]
- **On request (jobs)**: `compare` against the original; `town_feel.py` and `building_shots.py` (outdoor);
  `scale_bands.py` (new dungeons); `things_shots.py` (every interactive thing before and after use, the user's
  requirement after Gharik's Forge [P: REBUILD_PROCEDURE "What the measure does not see"]); in-game pin tours.
- Every finding links to its object and place; the scorecard keeps the revision it was taken on.

### W6. Playtest in the game

1. **Play here** (`F5`): the host builds, installs into the mount (with the outdoor material file) and starts the
   game at the camera, visible, with sound unless the user turns it off (agents' own runs keep
   `SDL_AUDIODRIVER=dummy` [P: memory "silent game runs"]). Test switches from the options (party level, items,
   quest bits, "all keys of this map", time of day) go into the start-up console file (D13).
2. **A headless playtest**: the project's `playtest.yml` (written by hand or by an agent, form of
   `briefs/mm7_7d06/L4/playtest.yml`) runs as a job; the log's PLAY and FAIL lines show in the job panel with the
   step that failed; playtests that loot chests run several times, as the merge procedure requires
   [P: HANDOFF "Merging code agents' work"].
3. Pictures at points of the walk (`set_pose` and screenshots) show in Pictures.

### W7. Review with pins resolved by an agent (S5a acceptance)

0. **Before the browser (slice 1)** the same loop runs without it: the user pins in the game (`pin <text>`), the
   pins are imported, the agent answers with `oymap pins` and a game picture, and the static review page shows the
   result (2.10).
1. The user opens an agent's map in Review (F1), walks it, pins three things (`pins.add` with pose and picture), or
   pins them in the game and finds them in the drawer.
2. An agent (MCP `map_pins` or `oymap pins`) lists open pins, claims one (`pins.claim pin:p7`); the user's drawer shows
   it claimed within a second. Claims and replies change the pins document's counter, not the map's revision (2.4.1).
3. The agent edits the project (transactions with `author: agent:x`), builds, takes before and after pictures from
   the pin's camera (the studio's render or a game tour job), and resolves with a reply and pictures.
4. The browser receives `revision_changed`; the pin turns resolved; the history entry's diff is one click away; the
   3D view can show the before revision as a ghost.
5. The user accepts or reopens with a reply; the agent sees it on its next `map_pins list`.

For the acceptance run the agent may be a scripted one (a test), and once a real agent (as PLAN 12 says: "an agent
resolves the pins live").

### W8. Sharing a mod

1. **Overlay** (changes to a shipped map): Import (`project.import {map, world, to}`), change handlers and objects,
   build: the outputs are `<stem>_<project id>.lua` and scene overlays. Export packs `mods/worlds/<w>/maps/` and
   `mods/worlds/<w>/events/` files and the project folder as two zips.
2. **New map**: the build plus its table rows (`map_stats.txt`, for outdoor `outdoor_travels.txt` and
   `bolster_maps.txt`, a sky row) [P: README "Leaving the map", "Air"]. In today's `mods/` these rows mean whole
   table files that replace the package's; the export warns ("installing this replaces map_stats.txt; another mod that
   does the same will clash") and writes a manifest draft (`mod.yml`: id, name, author, worlds, maps, rows added,
   quest-bit range used [P: AGENTS.md "custom content starting at 10000+"]) for S6's named mods.
3. A player unzips into `<install>/mods/`; the game mounts it [P: `mountMods`].

### W9. Changing a shipped map (any phase)

`Import` makes the overlay project with the map's own doors, events and sectors named in `ids.lock.yml` (`door:d57`,
`evt:e20`) [P: S1, S2]. Review mode shows the shipped map; Author mode edits what overlays can say (handlers that
replace `evt:eNN`; scene additions as far as the overlay writer allows). The original's own faults appear as issues
(Goblinwatch's events 38, 54, 57, 58 without handlers; the Forge's door 53 without geometry) [P: S1]. Generated map
Lua and MM9 converter output are never edited; changes go through overlays or the converters [P: PLAN 13]. A pin made
on a shipped map that has no project makes an empty overlay project named after the map, so the pin has a home (6.3,
settled).

---

## 6. Risks, decisions, open questions and phases

### 6.1 Risks

| # | Risk | What reduces it |
|---|---|---|
| R1 | **The vocabulary keeps growing** (six outdoor batches in one night; 321 unit cases); hand-made tools per word would never catch up | schema-driven inspector and `x-geom` (D5); bespoke widgets only for the short list; new words editable on merge |
| R2 | **Edits too slow to feel direct** (about 1 s per indoor edit today; outdoor validation with assets is a full build, 1.64 s on Erathia) | the client applies its own patch at once (2.4.3); D1's cache by source revision; spike 2 splits the outdoor time before any outdoor budget is promised. **S5-0** [revision 4]: indoor 300 ms met with almost no margin, on three conditions (2.4.3), to be re-measured on a quiet machine; outdoor budgets set (1.5 s, then 500 ms in S5b2 with kept land); the 3D view from the edit's own lowering |
| R3 | **Operations do not cover what the UI changes** (no `sketch.yml` lists; nested parts only by replacing the whole field; sub-objects addressed by position) | D3: lists from the schemas, keyed `patch`, rename, core-allocated ids; contract tests per collection |
| R4 | **Undo across a person and agents goes wrong** (undoing the agent's work, reverting a file over others' changes, rolling back engine numbers) | D4: one append-only model, undo as a validated revert entry, the snapshot restore as the oracle; the lock and pins outside the undo (2.4.1); rebase only when keys and tests hold; tests with two writers (PLAN 11 has the form) |
| R5 | **Generators overwrite hand edits** (projects written by `gen.py` and then edited; F6, agents' base and a hand finish, as a common way of working) | a durable hand-edit mark in `project.yml` from the first person-authored transaction; agents told at open and in every edit result; an outside rewrite of a marked project that replaces objects a person changed last, or drops keys, recorded with an error notice and one step to revert; the procedures: marked projects are edited by operations (2.8, S5b1); the mixed exit test of S5b1 |
| R6 | **The studio's 3D is not the game's look**, and the user judges by the game | say so in the UI; Play here one key away; game pictures as jobs; never call a map reviewed from studio views alone |
| R7 | **Walk mode differs from the game** (no events, monsters, traps) | banner in walk mode; Play here for behaviour |
| R8 | **Wasm in the browser**: PhysicsFS does not start; memory of the largest MM9 region; the Emscripten pin | walk mode avoids PhysicsFS (map bytes by URL); textures in local mode do not use wasm (2.11); S5c starts with PhysicsFS over JavaScript reads; the memory budget is S5c's acceptance [P: PLAN 13 "cut down to view and review if the budget cannot be met"]. **S5-0** [revision 4]: the Node build's PhysicsFS starts with a HOME (4.10), the browser worker's needs one in its file system; Node wasm builds of dungeons use about 300 MB more than native (346-407 MB; the heap never shrinks), not yet investigated, the first thing S5c looks at against 1 GB; the walk worker uses 20-35 MB |
| R8b | **Native and wasm builds differ** on outdoor maps or curved parts (two libms; no outdoor project ever built in wasm), found only in S5c when every calibrated map depends on the lowering [Review A7 1.5] | S5-0 builds all 22 projects with both and compares every byte; the comparison stays in CI. **S5-0** [revision 4]: 22 of 22 identical once one undefined `std::clamp` was written out; the risk is UB answered differently by libstdc++ and libc++, not libm, so a sanitizer job over the 22 projects, the UB sites fixed, the core's own (musl) math as insurance, no `long double` in lowering (4.10) |
| R9 | **three.js churn**; npm supply chain | pinned versions, one viewport module, deliberate upgrades, few direct dependencies |
| R10 | **Browser limits**: Safari blocks `ws://127.0.0.1` from https; Chromium's local-network permission; Firefox and Safari have no File System Access | the capability table of PLAN 9; verify LNA in spike S5-0; say which browsers in the page. **Confirmed in S5-0** [revision 4]: Chrome, Chromium and Firefox all gate fetch and the WebSocket to 127.0.0.1 behind the prompt; pairing starts from a button and reads a hanging request as "waiting for your answer" (2.12) |
| R11 | **The host as one process** (presence, jobs, watchers) while MCP clients each start their own today | `oymap mcp` relay to the running host [P: PLAN 8]; the host refuses a second instance on the same projects |
| R12 | **Python checks outside the core** cannot run in the hosted page | D10: local jobs; port when hosted mode needs them |
| R13 | **Format debts frozen into the UI** (a chest's width along its facing; mixed angle units) | settle before S5b (2.15) |
| R14 | **Scope drift into the design page's tools** (puzzle simulator, landmark visibility, coast stamp) | acceptance-driven phases (6.4); the deferral list |
| R15 | **Built by agents, reviewed by one person**: UI code quality and consistency; agents cannot see the page | a small set of rules for `web/` (4.16), styling and primitives decided up front (D8), the panel gallery screenshotted by Playwright and looked at before reporting (4.13), the contract and end-to-end tests, review per slice |
| R17 | **Pins and builds churn the revision** (every comment and every Play here would drop caches and stale agents' writes) [Review A7 1.1] | three classes of file before the cache (2.4.1) |
| R18 | **A half-drawn state shows nothing** (validation is the lowering; any issue stops a build) [Review A7 1.2] | severities and a lowering that skips what it cannot lower (2.4.2); until then a person's edits that add errors are refused |
| R19 | **The value arrives last** (one large S5a) [Review A7 1.7] | five slices, each used by the user before the next starts; pins from the game first (6.4) |
| R16 | **S4 calibration still moving** (Erathia's round two, the waterfall batch running) while S5 starts | S5-0 and S5a read maps, they do not depend on outdoor words settling; S5b2 (outdoor authoring) last |

### 6.2 Decisions needed from the user

Each with the recommendation first.

| # | Question | Recommendation | Alternatives and their cost |
|---|---|---|---|
| D1 | Split the revision into source, record (lock) and review (pins) first; then make `oymap serve` a caching service keyed by the source revision, with two lanes and push notices? | **Yes.** Without the split every pin and every Play here drops the cache and stales agents' writes; without the cache no edit meets 300 ms. Conditions taken from review A7: cheap staleness (size and time, then raw bytes), the watcher ignores `.oymap/`, merged outside edits, a banner for a file that does not parse, cancel kills lane J, one worker in hosted mode (2.4) | Threads in the core (breaks PLAN 3's single-threaded rule, risks determinism); one lane (jobs block clicks) |
| D2 | One typed request list shared by native, wasm, MCP and the command line (with `oymap call`)? | **Yes**, before any UI code, and the MCP tools and command line move onto it in the same phase; numbers rounded by rule; output schemas for the Python checks | Keep `run` with argv (stdout formats become the API; no types; unsafe from a browser) |
| D3 | Extend operations: lists from schemas (items with an `id`), keys for every selectable sub-object, keyed `patch`, rename, core-allocated ids, merging of repeated edits, author and label (`oymap record` for file-writing agents), macros in the core; severities and a lowering that skips a broken room or structure? | **Yes.** The keys come with the format bump (2.15); the skipping lowering is core work in S5b1; until it exists a person's edits that add errors are refused | Named operations per word (PLAN 5's catalogue: never finished at this vocabulary's pace); the browser writing files directly (loses checks, diff and authors); positional pointers (pins and rebases break when a list shifts) |
| D4 | One append-only history: undo and redo as validated revert entries, positions derived from the log, file versions stored once by hash and compressed; rebase of stale edits? | **Yes** (replaces the first draft's cursor undo plus selective revert, after review A7) | The first draft's two mechanisms (results differ for ever; redo of a revert undefined); global linear undo (undoes agents' work); refusing every stale edit |
| D5 | The UI covers words through the schemas (`x-geom`, `x-unit`, `x-key`, `x-id-kinds`, a rule for unions, `x-discriminator` and `x-kinds` for kind-selected objects, `x-group`/`x-order`, generated inspector, Source tab), kept honest by a schema lint in the unit suite? | **Yes**, after the S5-0 spike that renders one building and one room from the schemas (spike 7: done, D5 holds; the work is the annotations); bespoke tools for outlines, paths, openings, doors, wall bays, roads, the event form, the switch board. After review A7 on spike 7: the core enforces `x-kinds` as warnings (run over the 22 projects first); the lint gains a corpus rule and each annotation batch is checked against the lowering by another agent; the inspector shows effective values from the core's resolved read, not schema `default` copies; a generic row list where a bespoke tool is promised is a miss in the hand-author tests (3.8, 3.18, 2.4.2, 2.3) | Hand-made panels per word (months, always behind); generated forms without the lint (decays within a week) |
| D6 | three.js on WebGL2 first, pinned, behind one module; no picking tree until spike 1 asks for one? | **Yes** | Babylon.js (runner-up); WebGPU first (PLAN 9's order; the newer, moving path) |
| D7 | Walk mode in a wasm worker in both modes, as `walk.*` methods of the request list; textures in local mode without wasm? | **Yes.** Main reason (review A7): the browser wasm build runs every day from the first slice; a native lane can serve `walk.*` if the wasm spike fails; a recorded walk gives the same poses on both | Walk over WebSocket on native `serve` only (the fallback, not the plan); no studio walk (only Play here) |
| D8 | Web app in TypeScript with Vite; React; Zustand; CodeMirror 6 (not Monaco); fixed layout first (not Dockview); own plan view, flow graph and forms; plain CSS modules with tokens, Base UI primitives, TanStack Virtual (4.16)? | **Yes**; the host stays plain JavaScript; the styling and primitives choice is made now, not left to the first agent | A no-build web app (import maps, `htm`, JSDoc types); Monaco; Dockview from the start; Tailwind or a component kit (4.16); Radix or React Aria instead of Base UI |
| D9 | Pins format 1 (pose, picture, author, thread, claimed, accepted) from the game first (`pin <text>`), answered through the command line before the browser; pictures outside git by default? | **Yes** | Keep pins as they are (no pose: the lead keeps translating); a `loc` paste box in the browser (the first draft: keeps the copying, arrives later) |
| D10 | Python checks as local jobs now, with output schemas and a capability flag, ported to the core only when the hosted page needs them? | **Yes** | Port `town_feel` and `scale_bands` to C++ first (weeks; the README decision says checks are C++); leave them out of the UI |
| D11 | The phases of 6.4: S5-0 spikes (with the 22-project native-against-wasm builds), S5a in five slices each used before the next, then S5b1, S5b2, S5c; spike code thrown away except the request list? | **Yes** | Start with S5a's UI directly (risks R2, R8b, R18 found late); one large S5a (value at its end) |
| D12 | Ship the studio in releases (oymap, the host as a single executable, the web app) and host the page on the release server? | **Hosted page: yes, after S5c. Release download: a separate "Studio" archive, not inside the player package**, from S5b on. **Review A7 agrees**, and adds: an origin of its own (a subdomain), not a path on a shared origin, since folder permissions and storage are per origin; this document takes that in (4.14) | Inside the player package (larger download for every player); GitHub Pages (a second place to keep current); a path on the release site's origin (shares permissions and storage with it) |
| D13 | Game-side development features: **`pin <text>` first**, then run a console file at start, write the pose on exit, reload on change (on `reload map`, no per-frame polling)? | **Yes, each as its own reviewed change, no behaviour change outside development roots** (the rule of PLAN 10); `pin` before any web code | Do without (the lead keeps translating; Play here without test switches or return; restarts instead of reloads) |
| D14 | Sharing new maps waits for S6's named mods; S5 exports with a warning and a manifest draft? | **Yes** (review A7 accepts) | Pull named mods (PLAN 10b item 3) into S5 (a game change of its own) |
| D15 | May a designer sculpt terrain on new outdoor maps (written as `heights.nodes`), or only describe it with points, lines, terraces and the rest? | **This document: describe by default; a sculpt brush that writes `heights.nodes` for new maps, marked in the project**, since the "described, not traced" rule protects rebuild measurements, not new maps. **Review A7's view:** a brush that moves the described words (spot heights, points) first; `heights.nodes` only as marked patches of limited size, so maps stay described and agents can still reason about them. The two agree on "describe first, nodes marked"; they differ on whether nodes may cover a whole new map (this document) or only bounded patches (review A7). The review's limit is the safer default if agents are to keep editing such maps. **Decided** at 15:11 (bounded, marked patches) and **extended** in the evening for hand authors: patches stay the default for maps agents edit; a person may mark a project's land as hand-made, then the brush covers the whole map (never set by a procedure, refused in rebuilds; agents read such land through queries); strokes stored as differences over the described land, flatten as `terraces`, settled by one S5b2 test; a stroke previewed and committed once on mouse-up; a ground paint brush; heightmap import the first addition after S5b2 (3.18; the user's decisions at the end) | Describe only (some land cannot be said: Erathia's sheer drops needed nodes); sculpt freely (projects become height fields, against the format's intent) |

### 6.3 Smaller open questions: settled

The user, 2026-11-14 (evening), to session openyamm-a7: "Do what you recommend." Each question below is settled as
recommended (review A7 6.1); the question is kept for the record.

- ~~Should a pin's picture live in the project (in git) or in `.oymap/`?~~ **Settled by review A7 (D9), reversing
  this document's first recommendation:** in `.oymap/pins/pictures/`, out of git by default (dozens of maps, before
  and after pairs, for ever in history); the user keeps one on purpose, and only that one goes to `review/pictures/`
  as a small JPEG (3.13).
- ~~Where the game's pin inbox lives by default, and whether the `PLAY.md` commands set it explicitly.~~ **Settled:**
  the default (`pins_inbox/` in the game's user data folder), and `output/studio_play/PLAY.md` says where it is
  (2.10).
- ~~Map numbers for new maps: who owns which `map_stats` ranges (the studio's projects use 9130, 9301, 9603, 97xx)?~~
  **Settled:** a range table in S6's world and mod manifests (as QBit ranges are declared [P: AGENTS.md]) lets the
  studio propose a free number; until then a setting of the project root (1.3 F2).
- ~~The Discord questions of the design page (which tasks modders would do, Blender or in-editor, Chrome or Edge only
  for full editing).~~ **Settled:** asked, and during S5a, not before S5c: the answers (which tasks, Blender or
  in-editor) shape S5b's hand tools. The user posts them; the Discord bot only reads (6.4 S5a).
- ~~World projects (Xeen's ~70 maps: `world.yml`, `travel.yml`, `story.yml` [P: PLAN 4]): a project list per map in
  S5?~~ **Settled:** the project list stays per map in S5; a world view comes later (1.3 F1, deferred list).
- ~~Does the studio's walk need the party's real size per world?~~ **Settled:** the walk runs the game's movement
  code with the game's constants (radius 37 in every world today, `game/outdoor/OutdoorWorldRuntime.h:1872`,
  `game/indoor/IndoorMovementController.h:45`). No setting of the studio's own; if the game gets per-world sizes, the
  walk reads the same source (2.10, 3.6).
- ~~Lighting bakes as jobs in S5, or later?~~ **Settled:** later, not jobs in S5; the game shows unbaked maps.
- ~~Whether review-mode pins on shipped maps (no project) create an overlay project automatically.~~ **Settled:** yes,
  an empty overlay project named after the map, so the pins have a home (W9).
- ~~Projects inside `mods/`?~~ **Settled:** never. Projects are folders elsewhere; only builds are installed into
  `mods/` (B8, 1.3 F1).

### 6.4 Phases with exit criteria

Consistent with PLAN 12's three parts; a phase S5-0 before them, S5a in five slices (review A7 1.7), and S5b split by
world kind because the indoor and outdoor vocabularies are separate files and tools.

| Phase | Size | Contents | Exit criteria |
|---|---|---|---|
| **S5-0 Spikes** | M (seven spikes; review A7 5) | (1) **Viewer**: three.js draws Castle Darkmoor's rebuild and Harmondale's with their real `.oytex` textures (un-framed by the host) from a minimal host route; measure load time, frame rate, GPU memory; whether picking needs a tree. (2) **Edit latency**: a cached `serve`; measure an outline edit on Darkmoor and a structure edit on **Erathia**, each split into parse, schemas, lowering, asset reads and the dry run's GLB write; the lowering's behaviour on a half-drawn room; provenance carried through the indoor compiler on Darkmoor, with the share of faces that keep their id; the cost of committing one node-block patch on Erathia, so a sculpt stroke's commit has a budget before S5b2 (3.18; review A7 6.4). (3) **Walk**: the indoor and outdoor movement controllers in a browser worker on a built map's bytes, 60 steps a second. (4) **Request list**: the first methods with generated types, and the contract suite against native and wasm. (5) **Browsers**: the local-network permission, BC extensions in Chromium and Firefox and on the CI's software GPU, whether `F5` and `Ctrl K` can be taken. (6) **Native against wasm on all 22 projects**: the Node wasm build reads an asset root; every output byte compared (4.10). (7) **Schema forms**: one building and one room rendered from the schemas, both union forms (done: `output/s5_spikes/7_forms/REPORT.md`, 3.8). Spike code is thrown away, except the request list | A short record (`S5.md`) with the numbers and the load average of each; the budgets of 2.13 met, set (outdoor) or the design changed; the 22 projects identical or the differences located; the user's answers to 6.2. **Met** (2026-11-14; [S5.md](S5.md), "S5-0 exit"; revision 4 takes the changes in, 0.6). Open, not blocking S5a1: the user's hand check of `F5` and `Ctrl K`; the indoor 300 ms re-measured on a quiet machine |
| **S5a1 Pins from the game** | S | Core: the three classes of file (2.4.1: source revision, its 128-bit hash chosen here, the lock as a record, pins as their own document with counter and log), the lock keeping removed ids' numbers until `oymap lock prune` (2.4.1); pins format 1 (anchored to top-level ids, with their file where an id is in two files (2.6 item 11), or points until keys arrive), `oymap pins` (import, list, claim, reply, resolve, accept, reopen, tour), `oymap record` (attributing the watcher's outside entries); `oymap install` writes `<stem>.studio.yml` on every route (`--mount`, `--root`); game: the `pin <text>` console command (2.10; done 2026-11-14, `game/debug/PinInbox.*`, uncommitted); the static review page lists pins with before and after pictures; the procedures and `PLAY.md` say how | The user pins faults while playing a studio map, and an agent answers at least three of them through the command line with game pictures, without the lead copying a `loc` line or writing a tour |
| **S5a2 Open and look** | M | Request list v1 for reads (`hello`, `project.open`, `view.layout`, `view.mesh`); the cache by source revision and lane I; host: static web app, byte routes with token and `Host` check, project list, path jail; web: the frame, Review mode, plan view and 3D view read-only, textured; severities on issues (the field; the skipping lowering comes in S5b1), shown in the Issues drawer; styling and primitives as decided (4.16), the panel gallery; the generated inspector's render time measured in the real app in the browser (spike 7 measured Node server renders only). **From S5-0** (revision 4): the request list starts from spike 4's catalogue (2.3): its dispatcher, wasm entry, embed script, `patch` and typed refusals move from the spike's copy into the core, `gen.mjs --check` and the contract suite run in CI, and the MCP tools and the command line move onto the list here (D2's "same phase"; was S5a3); no absolute paths in the core's messages; no process-wide statics in `openTarget`; the cache with the three conditions of the indoor budget (parsed table lookups per asset root, one validation per edit, schemas of changed files only; 2.4.3), the 300 ms re-measured on a quiet machine first; `view.mesh` and `view.layout` from the lowering, not a dry build (2.4.3); severities first outdoors and `validateProject` with the asset root outdoors (2.4.2); the schema lint with today's 1 208 issues as its allow list (3.8); textures un-framed asynchronously with a block LRU, lowest mips first, the terrain weight images cooked or halved (2.11); no picking tree indoors, the terrain in chunks outdoors; WebGL context loss handled (4.4); CI screenshots on a software GPU (4.13) | The user opens every rebuild and new map, textured, within the opening budget |
| **S5a3 The pin loop in the browser** | M | Push notices, watcher, sessions, the `oymap mcp` relay; history read (with revert entries shown); the Pins panel (`P` in plan and 3D, the game's pins arriving live, claim, reply, accept, reopen); provenance for picking and pins on objects (top-level ids and points until keys arrive, 3.13), stamped in the lowering for every kind (2.9); the watcher ignores `build/` as well as `.oymap/` (2.4.3) | PLAN 12 (a)'s acceptance without walking: **the user pins in the browser (or the game), and an agent resolves the pins live** |
| **S5a4 Walk and Play here** | M | `walk.*` in the wasm worker (spike 3 held: no native lane); Play here (build, install, start the game at the camera); game-side: run a console file at start, write the pose on exit (D13). **From S5-0** (revision 4): the walk's input on the core's own trigonometry, and the game's mover rotations on it as their own reviewed game change; `walk.load` from the scene's movement state written beside the built map, with the outdoor terrain pack; the contract walk with a rotating mover; ladders, water and outdoor bounds walked (2.10). Needs the core changes after S5-0 in place (the wasm asset root, the UB fixes, the own math) | **The user walks the calibration and held-out maps in the browser** and plays from the camera; a recorded walk gives the same poses natively and in wasm |
| **S5a5 Scorecard, compare, jobs, flow** | M | Lane J and jobs (cancel by kill), the scorecard (with the Python checks as jobs with output schemas), the Compare view, Pictures, `oymap pins tour` as a button, the flow graph from `solve` | Every acceptance map's scorecard fills in the background; the playtests of the projects touched still pass four of four |
| **S5b1 Indoor authoring** | L | Core first: **severities and the lowering that skips a broken room** (2.4.2), the format bump with keys (`x-key`) and its migration, keys optional in files and filled on the core's next write, keyed `patch`, rename (its revert the opposite rename; lock and pins follow both ways, 2.4.1), core-allocated ids, merging, revert entries and history blobs (D4), rebase; pins on keyed sub-objects; lists from schemas; macros for rooms, openings, doors; `x-geom`, `x-unit`, `x-id-kinds`, union rules on `rooms`, `objects`, `wiring`, `plan` with the schema lint; then Author mode, stage bar, tool rail and options, the indoor tools of 3.18, the schema inspector, Source tab, event form, switch board view, Issues with fixes where the core has them, Library, Checklist; the debts of 2.15 settled. **The hand-edit mark** (2.8): written at the first person-authored source transaction, reported in `project.open`, `map_open` and every edit result, outside rewrites of marked projects caught with an error notice and one step to revert; REBUILD_PROCEDURE.md and OUTDOOR_REBUILD_PROCEDURE.md changed (agents edit marked projects by operations). **From spike 7** (review A7 on it): `x-discriminator`/`x-kinds` on the indoor kind-selected objects, enforced by the core as warnings (2.4.2) after a run over the 22 projects; the lint's corpus rule; each annotation batch checked against the lowering by an agent other than its writer; `project.resolve` and effective values in the inspector (2.3, 3.8). **From S5-0** (revision 4): the skipping lowering also skips objects with schema issues, and outline messages say "crosses itself" or "has no area" (2.4.2); keys for the two platforms without an id; `x-unit` on every number and `x-groups` per object on the indoor files, shrinking the lint's allow list; event steps with a schema (`$defs/effect`) before the event form (3.8) | PLAN 12 (b), indoor half: **the user rebuilds one room wing by hand** (a wing of a calibration dungeon, measured by `oymap compare` against the original as the agents' rebuilds are); **a small new dungeon made from an empty project entirely in the UI: no Source tab, no YAML, no command line**, with every word that forced the Source tab, and every word 3.18 promises a bespoke tool for that offered only a generic row list, listed in the phase record as misses (the honest measure of G6; F5); **the mixed test**: an agent-made map is finished by hand, then an agent adds to it through operations, and every hand edit is still there (F6); undo and rebase pass two-writer tests; reverting the latest entry equals the snapshot restore on every operation kind |
| **S5b2 Outdoor authoring** | L | The skipping lowering per structure; `sketch.yml` lists, keys and `patch` paths; the annotations and lint on the sketch schema; the grid editor, road tool, building tool with parts and the wall bay strip, the generic structure tools, scatter and areas; the town-feel scorecard; **D15 as extended** (3.18): the sculpt brush (bounded, marked patches by default; the whole map on land a person marks as hand-made, refused in rebuilds), strokes stored as differences over the described land (a new word beside `nodes`), flatten as `terraces`, preview in the browser and one transaction on mouse-up, `view.terrain_query` for agents; the **ground paint brush** writing zone outlines. **From spike 7**: the outdoor lowering's read record (one shared `childOf`/`textOf`, a checking mode, "word X was never read on this object", the first kind tables generated from it) before the structure annotations are written by hand (3.8); the building words moved into one `$defs`, with the check that all 22 projects and the unit suite's refusals validate the same before and after; `x-discriminator`/`x-kinds` on `structures[]` and `parts[]`, enforced as warnings after the 22-project run. **From S5-0** (revision 4): the land kept up to the peaks (keyed by the land words without `nodes` and the stroke word) and the scene write and reader check out of the commit, for the 500 ms outdoor budget (2.4.3, 2.13); a keyed or path `patch` into `heights.nodes` and the stroke word, one commit per stroke (2.6 item 3, 3.18) | PLAN 12 (b), outdoor half: **the user rebuilds one town block by hand**, measured by `compare` and `town_feel.py`; **a small new outdoor map, land included, made from an empty project entirely in the UI** (no Source tab, no YAML, no command line; misses listed as in S5b1; F5); **an agent moves a ridge under a sculpted patch** (a raised and a smoothed one) and the strokes stay; edits on Erathia, and a stroke's commit, within the budgets set in S5-0 |
| **S5c Hosted mode** | L | the wasm worker build with `oymap_call`; PhysicsFS over JavaScript byte-range reads (with a HOME in the worker's file system, 4.10); File System Access and OPFS; textures from packages; builds in the worker; one worker (2.4.3); the capability table's limits shown; an origin of its own with versioned paths; service worker; pairing from a button with the local-network prompt (2.12); first, the wasm build's memory above native (about 300 MB on dungeons in Node, R8) | PLAN 12 (c): **the hosted page opens a player's install, stays inside its memory budget and builds the slice dungeon byte-identical to the native build**; the RPC contract suite passes on the worker build; the 22-project comparison still identical |

Each S5a slice is used by the user before the next starts (review A7 1.7). The first draft's single S5a (sized L, with
the cache, lanes, push, the request list, provenance, layout, six host features, ten web views, walk in wasm, Play
here and two game features, and its value only at the end) is replaced by these five slices. S5a1 needs no browser
and no library decision; it can start as soon as S5-0's record is accepted, and its core part (the revision split)
is what S5a2's cache is keyed by.

The design page's Discord questions (which tasks modders would do, Blender or in-editor, Chrome or Edge only) are
asked during S5a, posted by the user (the bot only reads), so their answers shape S5b's hand tools (6.3).

Deferred beyond S5 [N]: the puzzle simulator, landmark visibility, coast stamp and landform brushes beyond D15,
lighting bakes as jobs, a world view over many maps, the MCP App viewer (S6), named mods (S6), docking, translations
of the studio's own UI, **the procedures shipped with the Studio download** (as MCP prompts or a folder the host
serves, so people outside this repository can have agents make a base: 2.8; D12's archive leaves room for it). The
**heightmap import** is outside S5's acceptance but is the first addition after S5b2: with a whole-map stroke layer it
is only a writer of that layer, and people who make land by hand come with tools of their own (3.18).

---

## 7. Appendices

### A. Every requirement and where the prepared material says it

"Kept", "changed" or "new" says what this document does with it. Sections of PLAN.md are written P§n; the design page
is DP with its section heading.

| Requirement | Where it is said | Here |
|---|---|---|
| S5 contents (a) (b) (c) and their acceptance | PLAN §12 table; README milestone list | kept: 0.1, 6.4 |
| S5 after the operations made real maps; stop points at S2 and S4 | PLAN §12 text, §13 "Scope", §14 row 1 | kept: 0.1 |
| Web app: React, Dockview, three.js (WebGPU with WebGL2 fallback), three-mesh-bvh, Monaco, Zustand | PLAN §1 layout, §9 | kept React, three.js, three-mesh-bvh, Zustand; changed Monaco → CodeMirror, Dockview → fixed layout first, WebGPU → WebGL2 first: 4 |
| One client interface, two backends (local host over WebSocket, wasm worker) | PLAN §9 | kept, made concrete as the RPC catalogue: 2.3 |
| Screen: stage bar, tool rail, tool options, plan and 3D, inspector (Properties, Connections, Notes), drawer (Library, Checklist, Issues, Outline), command palette | PLAN §9; DP "What is where" (`mock-anatomy`) | kept; added Review/Author, Source, Original, History, Pins, Pictures, Jobs: 3.1 |
| 3D draws core data; only terrain blending, lightmaps and fog shaders ported; exact look from Play here | PLAN §9 | kept: 1.2, 3.5, 4.4 |
| Walk mode uses the core's movement controllers in the worker | PLAN §9 | kept and extended to local mode: 2.10, D7 |
| Capability table per mode (hosted: no Play here, no playtests; editing in Chromium only; pairing not in Safari) | PLAN §9 table | kept: 1.2, 2.12 |
| Hosted mode last in S5, cut to view and review if the memory budget fails | PLAN §9, §13 | kept: 6.4, R8 |
| Assets in the hosted page: byte-range reads, central directory only, compressed textures uploaded directly, low mip first, LRU, one map at a time, 1 GB heap target, repo checkouts by directory handle | PLAN §9 "Assets in the hosted page" | kept: 2.11, 2.13 |
| Local mode: the host serves texture bytes over HTTP on 127.0.0.1 | PLAN §8 "Browser", §9 | kept: 2.11 |
| Host: thin Node process, no map logic, no document state; restarts `oymap serve` | PLAN §8 "Core"; S2 | kept: 2.2 |
| Access: 127.0.0.1, Origin allow list, pairing token | PLAN §8 "Access"; S2 (tested) | kept; added typed methods, path jail, token in fragment, CSP: 2.12 |
| Jobs with progress; game bridge (`--headless-run-scenario`, `run_game.sh --isolated` with a tour) | PLAN §8 "Jobs" | kept; jobs not built in S2: 2.4 |
| WebSocket JSON-RPC with the same schemas as MCP, HTTP on the same port for bytes | PLAN §8 "Browser" | kept: 2.3 |
| MCP tools (fourteen, `map_new` fifteenth), Streamable HTTP plus stdio relay `oymap mcp` | PLAN §8; S2; S3 | kept; relay needed for presence: 1.3 F4 |
| Host is plain JS with no build step; SDK 1.32.2 | PLAN §8 "State after S2"; S2 Findings | kept for the host; web app gets a build: 4.9 |
| `map_exec` is not a security sandbox | PLAN §8 | kept: never over the browser endpoint, 2.12 |
| Files are the truth; revision is a content hash; history is file snapshots; outside edits recorded; temp file plus rename under a lock | PLAN §4, §5; S2 | kept files as truth, outside edits, atomic writes; changed: the revision covers source files only (2.4.1), history is append-only with revert entries and hashed, compressed versions (2.7) |
| Operations are JSON with `op` and arguments; relations over coordinates; transactions with `dry_run`, `fail_fast`; result is diff, check delta, revision | PLAN §5 | kept; `fail_fast` not seen in the code; extended by D3: 2.6 |
| A write against an older revision is rejected with the diff since | PLAN §5 | kept for agents; rebase for the browser: 2.7 |
| Named operations (`room.add`, `door.place`, `terrain.raise`, `road.add`, ...) and `schema/ops/` | PLAN §5 | changed: macros in the core when two front ends need them; not built today [C]: 2.6 |
| The studio never creates git commits | PLAN §5 | kept: 1.2 |
| Canonical form, no YAML comments, `notes:` fields, `oymap fmt` | PLAN §4; README decisions | kept: 3.8 Notes and Source |
| Readable ids, `ids.lock.yml` keeps engine numbers | PLAN §4 | kept: 2.8 |
| Overlay projects; import of shipped maps | PLAN §4; S1; S2 | kept: W9, W8 |
| Face settings keyed by node names survive re-import | PLAN §4; DP "Re-import keeps every setting" | not in S5 (set-piece import dropped, PLAN §2a); no import UI |
| World projects (`world.yml`, `travel.yml`, `story.yml`) | PLAN §4 "World projects" | not built; settled in 6.3: the project list per map in S5, a world view later |
| Checks in three tiers; flow graph with approximate edges and unknowns | PLAN §6 | kept: 3.7, 3.10, 3.11, W5 |
| Tier 1 incremental compile by content hash per room | PLAN §6 | not built [C]; caching first, per-room later: 2.4 |
| `oymap` commands and `--json` | PLAN §7; studio README | kept; become printers over the RPC: 2.3 |
| Wasm: Emscripten, `-fwasm-exceptions`, `SUPPORT_LONGJMP=wasm`, byte-identical builds, no pthreads, byte sources, MEMFS mirrored to OPFS or File System Access, C ABI with JSON plus ArrayBuffers, TypeScript types from schemas | PLAN §3; wasm/README.md | kept: 4.10 |
| PhysicsFS does not start under wasm; asset-root commands fail there | wasm/README.md; S3 "WebAssembly" | a task of S5c; avoided by walk mode: 2.10, 4.10 |
| Emscripten pinned at 4.0.10 for `bx::Vec3` | PLAN §13; wasm/README.md | kept: 4.10 |
| Game-side: development mount (made), reload on change (not made), named mods (not made), scenario steps | PLAN §10b; S2 | kept; reload built on `reload map`: 2.10, D13, D14 |
| Tests: Playwright on the five acceptance maps; Vitest for host and MCP; native against wasm | PLAN §11 | kept; contract suite added: 4.13 |
| Risks: hosted mode unproven; scope; toolchain | PLAN §13 | kept: 6.1 |
| Static web app with no backend; assets from the install or repo; agents through a local host | README "Decisions already made" | kept: 1.1 G4, 2.2 |
| The C++ core is the only implementation of formats, compilers and checks | README "Decisions" | kept; conflicts with the Python checks [C]: D10 |
| Design order Plan, Shape, Build, Wire, Populate, Dress, Test | README "Decisions"; DP "Seven stages" | kept: 3.3 |
| The studio makes what carries game rules; art made outside; library first; placeholders | README "Decisions"; DP "Who makes what", "Assets" | kept: 1.2 |
| Shells drawn as rooms; sectors and portals derived; doors from a library or from faces | README "Decisions"; DP | kept rooms; doors as words with presets [C]: 3.18 |
| Changes to shipped maps as overlays; generated MM9 files never edited | README "Decisions"; PLAN §13 | kept: W9 |
| Ten principles (design order never locked, plan is the checklist, rooms not polygon soup, presets first, connections visible, imported geometry keeps properties, test in under a second, validation always on, tool options and properties separate, help where you work) | DP "Ten principles" | kept except import: 3 |
| Keys that stay the same everywhere | DP "Keys" table | kept, extended: 3.17 |
| No modal dialogs, unlimited undo, autosave, one mode at a time with its name visible | DP "What made editors clunky" | kept: 2.7, 3.9 |
| Play here with test switches, returning to the same camera, reload on save | DP `mock-gf-test` | kept; needs D13 game-side features: 2.10 |
| Flow graph generated, critical path, issues linked | DP `mock-gf-flow` | kept: 3.7 |
| Switch board with simulator, sequence puzzle | DP `mock-gw-board`, preset table | switch board kept as a view; simulator deferred: 3.7, 6.4 |
| Section view for stacked floors, lift scrubber | DP `mock-nl-lift` | kept: 3.4, 3.5 |
| Landmark visibility, coast stamp, landform brushes, heightmap import, road splines, kit library, plots | DP New Sorpigal and Shadowspire steps | not words that exist [C]; D15; deferred: 3.18 |
| Agents' uses: address review pins, live pairing with a revision and "what you changed since" | DP "What agents would use it for" | kept: F1, F4, W7 |
| Pins anchored to objects, with camera and screenshot | DP tool table (`map_pins`); pins.schema.json has `on`, `at` only | changed: pins format 1, from the game's `pin` command first, own document outside the revision, pictures outside git: 2.10, 3.13 [C] |
| Results concise, images at most 1 568 px | PLAN §8 | kept for MCP; not a UI rule |
| Calibration roles (designer, builder, evaluator), comparison metrics, look by fixed cameras | CALIBRATION.md | kept: Compare 3.14 |
| Rebuild rules: original's frame, measured not traced, scripts allowed as records, "a wrong shape that measures better is forbidden", what the measure does not see, can a player read it, room sizes, textures by family | REBUILD_PROCEDURE.md; HANDOFF "Rules that bind" | kept as checklist and checks: 3.10, W1, W5 |
| Outdoor rules: described not traced, `heights.nodes` ruling, town feel, tree spacing, roads to the edge, guards, monsters by habitat, entrances that read, building pictures before the user walks | OUTDOOR_REBUILD_PROCEDURE.md; TOWN_FEEL.md; HANDOFF 09:03 ruling | kept: W2, 3.11, D15 |
| The user reviews results by playing; give run commands; capture every reported pose | HANDOFF "The user's decisions"; memory notes; PLAY.md | kept as F1, pin tours: 3.13 |
| The user reviews in VS Code with `AI:` notes; no git staging by agents | the user's CLAUDE.md | not a studio feature; projects stay plain files in git: 2.8 |
| No per-frame cost for small features | memory "No per-frame cost" | applied: push notices instead of polling, 2.4 |
| `editor/` is retired at S7; until then untouched | EDITOR_RETIREMENT.md; PLAN §1 | kept: the old editor's ImGui panels (Viewport, Tools, Scene, Log, Inspector), terrain brushes and icon kit are not carried over except the icons: 4.1 |

### B. Contradictions found

| # | Where | What it says | What is true (source) | Consequence here |
|---|---|---|---|---|
| B1 | DP "Architecture" | The host holds open documents and their history; the MCP server loads the wasm core; TypeScript SDK 2.x speaking 2026-07-28; Streamable HTTP | PLAN §8 and §14 (host stateless over native `oymap serve`); S2 (SDK 1.32.2, protocol 2025-11-25; stdio only) | PLAN and S2 followed |
| B2 | DP "Milestones" | Browser editor (M3) before indoor and outdoor authoring (M4, M5) | PLAN §12 (S5 after S3 and S4), §14 row 1 | PLAN followed |
| B3 | PLAN §4 | Outdoor project: `terrain/` (height.png, tiles.png, weights), `geometry/` GLBs with `faces.yml`, `objects.yml` | Outdoor projects are `project.yml`, `plan.yml`, `sketch.yml`, `atmosphere.yml` (studio README; briefs) | the UI edits `sketch.yml` (3.18) |
| B4 | PLAN §5 | Named operations and a catalogue in `schema/ops/` | Four generic operations over 29 collections; no `schema/ops/`; no `sketch.yml` collection (`core/Ops.cpp`; S2 "Not done") | D3 |
| B5 | PLAN §6 | Tier 1 incremental compile by content hash per room or terrain chunk | Builds are whole (measured 0.46 to 2.13 s) | caching first: 2.4 |
| B6 | DP outdoor walkthroughs | Landform brushes, coast stamp, heightmap import, road splines that grade, kit library of NWC prefabs, plots | Spot-height grid and described land; road lines with beds; buildings from parts and bays; `kind: model`; the rule "described, not traced" and the `heights.nodes` ruling | 3.18 table; D15 |
| B7 | DP door library, preset table | Library doors (portcullis, wooden, double sliding, secret wall, ...); presets door, lever, switch board, sequence puzzle, lift, chest, house, exit, teleport, lock, trap, fountain, ... | Door words (`kind`, `leaves`, `fold`, ...), "no library of looks" (S3 table); wiring presets door, switch, chest, exit, teleport, text, script with conditions and effects | presets in tool options fill words; switch board a view |
| B8 | DP mockups | The open document is a map file (`mods/worlds/mm6/maps/oute3_rebuild.odm`) | A project is a folder (PLAN §4) | projects never inside `mods/`: 6.3 |
| B9 | DP "Play here" | Returns to the same camera; reload on save | The game has no reload on change (PLAN §10b item 2 not made) and no exit pose; it has `reload map`, `loc`, `exec` | D13 |
| B10 | DP tools table; `map_pins` | Pins with their object, camera and screenshot | `pins.schema.json`: `on`, `at`, `status`, `author`, `reply`, `revision` | pins format 1: 3.13 |
| B11 | README "Decisions" | The C++ core is the only implementation of checks; no Python re-implementation | `town_feel.py` (1 147 lines), `scale_bands.py`, `building_shots.py`, `things_shots.py`, `compare.py`, `texture_use.py` are Python checks the user relies on | D10 |
| B12 | PLAN §1 layout | `kits/` with `calibration.yml` | No `kits/` folder; calibration ranges live in the Python checkers and TOWN_FEEL.md | noted; no S5 dependency |
| B13 | PLAN §3, §9 | Walk mode in the worker; wasm only for the hosted page | Local mode's walk unspecified | D7 |
| B14 | DP Goblinwatch step 10 and "audits" row | "key E reads key D's flag" is an issue of the original | S1 and research/TEST_MAPS.md: a misreading, dropped | not used |
| B15 | PLAN §13 | Until the end of S3 the schema carries a version and `oymap` migrates forward | Every file still `format: 0`; no migration command; S3 closed | 2.15 |
| B16 | DP and PLAN §8 | `oymap studio`, `oymap host`, `oymap mcp` shortcuts | Not made (PLAN §8 "State after S2") | S5a makes them |
| B17 | PLAN §8 | Results with `structuredContent` and output schemas; MCP Tasks; elicitation on undo | Not made in S2 (JSON text results) | the RPC catalogue gives the schemas: 2.3 |
| B18 | PLAN §2a, §12 S3 row | Set-piece import with face matching; the Python port | Both dropped on 2026-11-13 | no import UI |
| B19 | The design artifact | Revision 4 published at claude.ai/artifact/SBUwCHsj81N975vCpEbYJX | Not readable from this session | design_page.html used |
| B20 | This document's first draft (2.4, D1) | Cache by revision; pins written through operations | The revision hashes `review/pins.yml` and `ids.lock.yml` too (`core/Project.cpp:21`, `core/Ops.cpp:860`); builds rewrite the lock (`core/IndoorBuild.cpp:1878`) and the next read records a `build` entry (`core/Ops.cpp:424`) [review A7 1.1] | three classes of file: 2.4.1 |
| B21 | This document's first draft (2.4, 2.6 item 4); DP "Validation is always on" | Incremental validation under 0.15 s; the browser commits with issues | Validation is the whole lowering (`core/IndoorBuild.cpp:1578`); a build refuses any issue (`cli/Commands.cpp:803`); issues have no severity (`core/Project.h`) [review A7 1.2] | severities and a skipping lowering: 2.4.2 |
| B22 | PLAN §3 rule and S5c acceptance | Native and wasm builds give the same bytes | Checked on two example projects only (`tests/native_vs_wasm.sh`); no outdoor project ever built in wasm [review A7 1.5] | all 22 projects in S5-0: 4.10, 6.4 |
| B23 | This document's first draft (2.6 item 1) | Collections from `x-sort: id` | `sketch.schema.json` has no `x-sort` [review A7, D3; counted] | collections from "items have an `id`": 2.6 |

### C. Numbers used

| What | Number | How measured |
|---|---|---|
| `oymap validate` | 0.20 s, 26 MB (the Mad Necromancer's Lab); 0.98 s, 43 MB (Castle Darkmoor); 1.30 s, 72 MB (New Sorpigal) | `/usr/bin/time` on copies of `briefs/<key>/L4` in a scratch folder, 2026-11-14; machine load not recorded |
| Review A7's split (load average 1.4) | load + parse + canonical text: Goblinwatch 0.09 s, Darkmoor 0.11 s, New Sorpigal 0.09 s, Erathia 0.13 s; validate without assets 0.18, 0.24, 0.31, 0.20 s; validate with assets 0.31, 0.50, 0.73, 1.64 s; build Darkmoor 0.83 s, New Sorpigal 0.51 s, Erathia 1.59 s; one real `oymap edit` on Darkmoor 1.0 s; process start 3 ms | review A7, on scratch copies of four projects; the first draft's Darkmoor validate of 0.98 s did not reproduce |
| History per edit | one edit of Darkmoor's rooms wrote 330 KB (whole before and after copies) | review A7 |
| `oymap build` | 0.46 s, 34 MB (Lab: 32 rooms, 1 381 faces); 2.13 s, 68 MB (Darkmoor: 267 rooms, 4 659 faces); 0.99 s, 72 MB (New Sorpigal: 35 buildings, 473 placed things) | same |
| Largest shipped maps | MM9 Thjorgard city 30 605 faces, 36 406 vertices, 89 sectors; MM9 Lindisfarne 30 460 faces | `oymap export --summary` |
| MM6 to MM8 dungeons | Castle Darkmoor 4 665 faces, 195 sectors; Goblinwatch 2 290 faces, 59 sectors | same |
| Outdoor maps | Tularean Forest 128 models, 469 placed things; Ravenshore 121 models, 825 placed things; 128 x 128 grid | same |
| Shipped maps | 247 `.odm` and `.blv` under `assets_dev/worlds` | `ls` |
| Project sizes | `rooms.yml` up to 4 219 lines (Darkmoor), `objects.yml` 3 300, `wiring.yml` 993 (Abandoned Temple); `sketch.yml` up to 5 767 (Erathia) | `wc -l` over `briefs/*/L4` |
| Schemas | 661 KB; about 1 860 properties (sketch 914, plan 268, objects 263, rooms 202, project 76, common 73, wiring 40, atmosphere 40, pins 11, ids lock 10) | counted over `openyamm-studio/schema/*.json` |
| Operation collections | 29 | `core/Ops.cpp` |
| Packages | engine.zip 1.5 GB; mm6 703 MB; mm7 518 MB; mm8 622 MB | `du` on `assets/` |
| Cooked textures | 15 243 `.oytex` in `assets_dev`; MM6 `textures_x4` 1 548 files, 824 MB | `find`, `du` |
| Binaries | `build/oymap` 13.5 MB; `build-wasm/oymap.wasm` 5.2 MB (2026-11-12) | `ls` |
| Host | 590 lines of JavaScript; `node_modules` 29 MB; Node 24 (24.21.0; `zlib.zstdDecompressSync` present) | `wc`, `du`, `node --version`, `node -e` |
| Projects | 22: 16 under `devdocs/map_studio/briefs/*/L4`, 6 under `devdocs/xeen/briefs/*/L4` | `ls` |
| Schema lists | `sketch.schema.json`: 57 lists of objects, 11 with an `id`, 37 `oneOf`/`anyOf`, no `x-sort`; `rooms.schema.json`: 14 lists of objects, 6 with an `id` | review A7; `x-sort` and union counts checked again |
| Unit cases | 321 at the twenty-first merge; 323 at the twenty-third | HANDOFF.md |
| S5-0 spikes (revision 4) | indoor cached edit on Darkmoor 275 / 294 / 300 ms (load 12); outdoor edit on Erathia 1 303 / 1 424 ms (9-13); a brush stroke 1 305 / 1 468 ms (6-9); walk step p99 55-260 us on 30 605 faces (13-18); viewer 59-60 fps, GPU +33 and +141 MiB (11-30); 22 of 22 projects byte-identical native and wasm with one UB written out; schema lint 1 208 issues; wasm core 7.4 MB raw, 2.2 MB gzip; `oymap.wasm` 7.94 MB | [S5.md](S5.md), with each number's method and load; raw data under `output/s5_spikes/` |


## The user's decisions (2026-11-14 15:11)

- **S5-0: go**, including the game's `pin <text>` command (pose, note, screenshot into an inbox) as the first game change.
- **D12:** a separate Studio download beside the game; the hosted page later on its own origin, versioned on the release
  server.
- **D15:** hand-sculpted land only in bounded, marked patches (`heights.nodes` inside a declared patch); the rest stays
  described by the land words.
- **D8:** Base UI primitives with plain CSS modules and design tokens.
- The other decisions D1-D7, D9-D11, D13, D14 go as the document recommends unless the user says otherwise.

## The user's decisions (2026-11-14, evening)

The user answered section 6.3's open questions to session openyamm-a7: "Do what you recommend. In the end I imagine
that a lot of people will want to also make the dungeons and terrains etc. by hand entirely. Not sure if that's
relevant. And some will use agents to do the base and finishing touches by hand." Review A7's section 6 turned it into
the changes of revision 3 (0.5's last rows):

- **6.3:** every smaller question settled as recommended (6.3).
- **Hand authors and mixed authors** (F5, F6): S5b1's and S5b2's exit criteria each gain a small new map made from an
  empty project entirely in the UI; S5b1 gains the mixed test (6.4).
- **R5:** the hand-edit mark and what it does, in S5b1 (2.8).
- **D15, extended by this answer:** bounded, marked patches stay the default for maps agents edit (the decision of
  15:11). A person may mark a project's land as hand-made; then the brush may cover the whole map. No procedure sets
  the mark and a rebuild refuses it; agents read such land through queries. Strokes are stored as differences over the
  described land, flatten as a `terraces` entry; one S5b2 test settles it (an agent moves a ridge under a sculpted
  patch). A stroke is previewed in the browser and committed once on mouse-up. S5b2 gains a ground paint brush; the
  heightmap import is the first addition after S5b2 (3.18).


## The user's key check in Chrome (2026-11-14 17:32)

On `keys.html?prevent=1` in his desktop Chrome: F5 and Ctrl F5 reached the page and were taken (the page never
reloaded: `loads: 1`). Ctrl K never reached the page: only the Ctrl key-down was logged, and the page lost focus (the
browser's address bar takes Ctrl K). So in Chrome the page can take F5 but not Ctrl K: search must not depend on
Ctrl K; 3.17's fallback (`Ctrl P` or `Ctrl Enter`) becomes the binding, to be checked the same way when S5a2 binds
search. Firefox not checked by hand; its shipped key table allows both.

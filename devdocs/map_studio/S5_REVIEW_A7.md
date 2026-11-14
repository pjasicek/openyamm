# Review of the S5 design (session openyamm-a7, 2026-11-14)

Reviewed: [S5_BROWSER_EDITOR.md](S5_BROWSER_EDITOR.md) in full, `s5_mockups/wireframes.html`, PLAN.md in full, and
the code the design rests on (`openyamm-studio/core/Ops.*`, `Project.*`, `IndoorBuild.cpp`, `cli/main.cpp`, `host/src/`,
the schemas, `tests/native_vs_wasm.sh`, `wasm/README.md`). I ran my own timings on scratch copies of four projects.
Not reviewed: `design_page.html`, the Python checks, the game's console code.

## Verdict

**Go for S5-0 (the spikes), once the seven changes of section 1 are in the document. No go for S5a yet:** three of
the findings change what S5a contains, and the spikes must report first.

The direction is right. I would keep without change: the typed request list (D2, the most important decision in the
document), files as the truth, a schema-driven inspector, the 3D library behind one module, view modules without a
framework, TypeScript with Vite, CodeMirror, a fixed layout, spikes before building. Appendix B is valuable and
accurate where I checked it.

What is wrong is mostly below the UI: the document designs the browser well and takes four properties of the core
for granted that the core does not have.

## 1. Changes needed before the foundation is fixed

### 1.1 The revision covers pins and the build's id record. Split it.

`projectFileKinds()` (`core/Project.cpp:21`) lists `review/pins.yml` and `ids.lock.yml`, and `projectRevision()`
(`core/Ops.cpp:860`) hashes every file of that list. Every build that is not private writes the project's
`ids.lock.yml` (`core/IndoorBuild.cpp:1878`). With the design as written:

- Each pin, reply and claim changes the project's revision. The mesh cache (keyed by revision) is dropped, the
  scorecard greys ("the project has moved on"), and an agent's `expect_revision` goes stale because the user
  commented.
- Play here (build and install) rewrites the lock, the watcher reports an "outside" change, and the user's next
  Ctrl Z finds that the latest entry is not theirs. Undo would also be able to roll back engine numbers, which must
  never happen: "a number once given stays" is the rule the lock exists for.

Change: three classes of file. **Source** (project, plan, sketch, rooms, objects, wiring, atmosphere): the revision
is the hash of these alone, and caches, `expect_revision`, history and undo see only these. **Record**
(`ids.lock.yml`): written by builds under the project lock, never an outside edit, never undone, hashed separately
for the built bytes. **Review** (`review/pins.yml`): its own document with its own change counter and its own log,
outside the map's undo. This is a core change and belongs before the cache of D1, which is keyed by it.

### 1.2 Validation is the lowering, and a build refuses any issue. D3's "the browser commits with issues" gives a blank 3D view.

`validateProject()` (`core/IndoorBuild.cpp:1578`) runs the schemas and then lowers the whole project. `oymap build`
builds only when the issue list is empty (`cli/Commands.cpp:803`). A `ProjectIssue` has no severity. So:

- "Incremental validation, under 0.15 s, schema checks per changed file" (2.4) is not available: the cost is the
  lowering (20 900 lines indoor, one pass), not the schemas. Incremental lowering is exactly the tier 1 compile the
  document says it does not need.
- A person's half-drawn state (D3 item 4) has issues, so no mesh can be built, in the most common state of
  authoring.

Change: (a) issues get a severity, and only errors stop a build; (b) the lowering skips an object it cannot lower,
reports it and builds the rest (per room indoors, per structure outdoors); (c) the client keeps the last good mesh
of a skipped object and marks it stale. (b) is real core work that no phase lists. Without it, drop D3 item 4 and
refuse a person's edits that add errors.

What the numbers say (my runs, load average 1.4; the document's Darkmoor figure of 0.98 s did not reproduce):

| Project | load + parse + canonical text | validate, no assets | validate with assets | build | one real `oymap edit` |
|---|---|---|---|---|---|
| Goblinwatch | 0.09 s | 0.18 s | 0.31 s | | |
| Castle Darkmoor | 0.11 s | 0.24 s | 0.50 s | 0.83 s | 1.0 s |
| New Sorpigal | 0.09 s | 0.31 s | 0.73 s | 0.51 s | |
| Erathia (largest sketch) | 0.13 s | 0.20 s | 1.64 s | 1.59 s | |

Reading: the process start is nothing (3 ms); parsing 250 KB of YAML costs 0.1 s; indoors a cached tree and cached
tables leave about one lowering (0.15 to 0.25 s) per edit, so 300 ms looks reachable **without** any incremental
validation. Outdoors, validation with assets is a full build (1.64 s against 1.59 s) and I do not know how much of
it a cache removes. The budget must be set on Erathia, not New Sorpigal, and spike 2 must split the time into parse,
schemas, lowering and asset reads before promising a number.

To make the feel independent of that number: the client applies its own `patch` to its copy of the file at once (it
is plain JSON; no game rule is involved) and redraws the plan, then reconciles with the core's answer and rolls back
on a refusal. The 300 ms then governs only issues and 3D.

### 1.3 `patch` addresses list items by position. Things a person selects need keys.

`sketch.schema.json` has 57 lists of objects; 11 have an `id`. `rooms.schema.json`: 14 and 6. Building parts already
carry local ids (`id: p3`), yet wireframe W3 patches `/parts/3/walls/s`. With positions: a pin or a selection on
"part 3" points at another part after someone inserts one; every rebase fails once a list shifted; the provenance
table ("thing:building_2 part p3") and the patch disagree about names.

Change: in the format bump that 2.15 already plans, every sub-object a person can select or pin gets a key unique
within its parent (parts have one; platforms, levels, pillars, porches, plots, scatter entries, height features,
roads need one), marked in the schema (`x-key`). A pointer segment into a keyed list is the key
(`/parts/p3/walls/s`); positions remain for plain lists (outline points, bays) with `test`. Say in the document that
this departs from RFC 6901 and where.

Also missing from D3 and needed by hand authoring: a **rename** operation (one transaction that updates every
reference in every file, the lock and pins), ids **allocated by the core** when the client gives none, and
**merging of repeated edits** (ten presses of PgUp, a dragged number) into one history entry, or the 1 000-entry
history is twenty minutes of work.

### 1.4 Undo: one model, not two.

D4 keeps today's undo (a cursor and an `undone` flag over file snapshots) for "the latest entry" and adds a
selective revert (a new transaction) for the rest. Two mechanisms with different results forever, and redo of a
revert is undefined in the cursor model. Change: the history is append-only; undo is always a new entry that
reverts one earlier entry object by object; redo reverts the undo; each author's position is derived from the log.
The snapshot restore stays as the test oracle (reverting the latest entry must give the same bytes). The revert is
validated like any transaction, because "nobody changed this object since" does not cover an opening an agent
attached to the room being un-added.

History storage: an entry keeps whole before and after copies of each changed file. One edit of Darkmoor's rooms
wrote 330 KB (measured); 1 000 entries are 330 MB per project. Store each file version once by its hash, compressed.

### 1.5 Native and WebAssembly builds are proven identical on two example projects only.

`tests/native_vs_wasm.sh` builds `gatehouse_cellars` and `shapes_gallery`. The wasm core cannot open an asset root,
and outdoor validation and builds read one, so **no outdoor project has ever been built in wasm**. Roofs, rounds and
domes use trigonometry, and glibc and Emscripten's libm are different libraries. Identical bytes are S5c's
acceptance and PLAN's rule (a map's bytes decide whether saves keep their map state); PLAN's fallback ("cut hosted
mode down to view and review") covers memory, not this. Finding it in the last phase means changing lowering code
that every calibrated map depends on. Move it to S5-0: make the Node wasm build read an asset root, build all 22
projects with both, compare.

### 1.6 The first thing the user needs does not need a browser.

F1 says the user plays in the game and reports `loc` lines, and R6 says a map is never reviewed from studio views
alone. Then the most valuable part of G1 is: a console command in the game, `pin <text>`, that writes the pose, the
text and a screenshot to an inbox; pins format 1; agents answering through the command line with before and after
game pictures. The document puts the in-game pin "later" and builds a paste box for `loc` lines instead. Do the
console command first (days, no library decision involved); it removes the translator before any web code exists.

### 1.7 S5a is one phase of XL size with the value at its end. Slice it.

S5a lists the cache, lanes, push, the request list, provenance, layout, six host features, ten web views, walk in
wasm, Play here and two game features, sized L. Proposed slices, each used by the user before the next starts:

1. **Pins from the game** (1.6) and pins format 1.
2. **Open and look**: `hello`, `open`, `layout`, `mesh`, host bytes, project list, plan and 3D read-only. Exit: the
   user opens every rebuild textured.
3. **The pin loop in the browser**: push, watcher, history (read), pins panel, an agent resolving live. This is
   PLAN 12 (a)'s acceptance without walking.
4. **Walk and Play here.**
5. **Scorecard, compare, pictures, jobs, flow graph.**

## 2. The fifteen decisions

| # | Verdict | Conditions and notes |
|---|---|---|
| D1 caching `serve`, two lanes, push | Accept with 1.1 and 1.2 | Detect staleness by file size and time, then a hash of the raw bytes; hashing "the canonical files" costs the 0.1 s parse. The watcher must ignore `.oymap/` (jobs and history are written there). Outside edits arrive file by file from generators: merge them, and define what the browser shows while a file does not parse (keep the last good tree, a banner). Cancelling a job means killing lane J; say so and keep its writes atomic. Hosted mode has one worker, so a background audit blocks edits there; two wasm instances double the tables against the 1 GB budget. Decide which. Builds go through a GLB written to disk even in a dry run; measure it |
| D2 one typed request list | **Accept, do first** | The MCP tools and the command line must move onto it in the same phase, or `run` with argv lives on beside it: add a generic `oymap call <method> <json>`. Round numbers in results by rule, or the native-against-wasm suite fails on the last digit. The Python checks' output needs schemas in the same list (D10), or stdout is the interface again |
| D3 operations | Accept with 1.2, 1.3 | Agents work mostly by writing files and by the command line, not MCP (0.2 of the document). Then authorship cannot rest on the MCP relay: give a file-writing agent a command that records its outside change with an author and a label. Deriving collections from `x-sort` gives nothing for `sketch.yml`, which has none; derive from "items have an `id`" |
| D4 undo | **Change** (1.4) | |
| D5 schema-driven inspector | Accept with conditions | Needs more than `x-geom` and `x-unit`: `x-key` (1.3); the kinds an id field accepts (every reference is the one generic `id` pattern today, so "a picker of the right kind" has nothing to filter on); a rule for the 37 `oneOf`/`anyOf` of the sketch schema, none of which is told apart by a constant; grouping and order. A lint in the unit suite must fail a schema change that lacks them, or G6 ("editable the day it lands") decays within a week of other sessions adding words. Add a spike: render one building and one room from the schemas before D5 is fixed |
| D6 three.js, WebGL2 first | Accept | Start without three-mesh-bvh: 30 000 triangles need no tree; add it if spike 1 says so. Check that the CI's software GPU takes BC7, or the CPU decode is needed for tests regardless of users' browsers |
| D7 walk in wasm in both modes | Accept with conditions | The stated reason is weak: a worker answers through a message just as a socket does. The good reason is that it makes the browser wasm build exist and run daily from the first phase. Conditions: walk is part of the request list (`walk.load`, `walk.step`, `walk.toggle`), so a native lane can serve it if the wasm spike fails; a recorded walk replayed on native and wasm must give the same poses. **Textures must not depend on wasm in local mode**: the host can un-frame zstd itself (`node:zlib` has zstd in the machine's Node 24; I checked) and serve the blocks |
| D8 TypeScript, Vite, React, Zustand, CodeMirror, fixed layout | Accept | **A gap:** no decision on styling or on the interface primitives (menus, popovers, combo boxes, trees, long lists, the command palette). Left open, agents will write each one three times. Decide now: plain CSS with variables and CSS modules; one headless primitives library (Radix Primitives or Base UI, both MIT); one list virtualiser; no Tailwind, no component kit. `F5` reloads the page and `Ctrl K` is the browser's: an installable app window (a web manifest; works on 127.0.0.1) removes the browser's keys |
| D9 pins format 1 | Accept with 1.1, 1.3, 1.6 | Pin pictures do not belong in git by default (dozens of maps, before and after pairs, for ever in history); keep them in `.oymap/` and let the user keep one on purpose. This reverses 6.3's recommendation |
| D10 Python checks as local jobs | Accept | With output schemas (D2) and a capability flag where Python is absent |
| D11 phases | **Change** (1.5, 1.7) | Say that spike code is thrown away, except the request list |
| D12 shipping and hosting | The user's; I agree with the recommendation | Use an origin of its own, not a path on a shared one: folder permissions and storage are per origin |
| D13 game-side features | Accept | Add `pin <text>` and put it first. Reload on change must not poll per frame |
| D14 sharing waits for S6 | Accept | |
| D15 terrain sculpting | The user's | My view: a brush that moves the described words (spot heights, points) first; `heights.nodes` only as marked patches of limited size, so maps stay described and agents can still reason about them |

## 3. Smaller points

- **Security (2.12).** Add a check of the `Host` header (DNS rebinding makes a hostile page same-origin with
  127.0.0.1) and require the token on the HTTP byte routes too; the document protects only the socket.
- **Revision length.** Twelve hex digits of FNV-1a are fine for noticing a change; as a cache and URL key use a
  longer hash.
- **Numbers.** Record the machine's load with each measurement; add Erathia and a real `oymap edit` to appendix C.
- **Tests for a UI written by agents (R15).** Agents cannot see the page. Add a gallery page of every panel in its
  states, screenshotted by Playwright, which the building agent must look at before reporting; the wireframes are
  the reference.
- **Walk and mouse look** need pointer lock, whose exit key is Esc, which 3.17 uses for cancel.

## 4. S5-0, as I would run it

The document's five items, plus: the native-against-wasm build of all 22 projects (1.5); the time split of an
outdoor edit on Erathia (1.2); provenance carried through the indoor compiler on Darkmoor, with the share of faces
that keep their id; the lowering's behaviour on a half-drawn room (1.2); the two schema forms (D5). Exit as written:
the numbers in `S5.md`, the budgets met or the design changed.

## 5. Second look at the revised document (same day)

Read: 0.5, 2.4 to 2.8, 2.10 to 2.13, 2.15, 3.13, 4.10, 4.13, 4.16, 6.1 to 6.4. All seven changes and the conditions
are taken in as meant. The document's corrections of my review are right: a lock-only change is recorded as `build`,
not `outside` (`core/Ops.cpp:426`); a `git checkout` of the lock is the new record, not an error; a build that
skipped objects must never install.

**Verdict: go for S5-0.** Five small points remain. None blocks the spikes; the first two belong in 2.4.1 before S5a1
builds the three classes of file.

1. **The lock forgets removed objects** (`core/IndoorLowering.cpp:20745`: "The lock forgets what the project no longer
   has"). Remove a door, press Play here (the build writes the lock), undo: the door comes back with a new engine
   number. That is the renumbering the split was meant to prevent, by another route. The lock should keep the numbers
   of removed ids until an explicit prune.
2. **Rename and "the lock is never undone" clash.** A rename re-keys the lock entry and the pins (2.6 item 4).
   Reverting it object by object restores the old name in the source and leaves the lock under the new one, so the
   object gets a new number. A revert of a rename must run as the opposite rename. State the rule as: undo never
   changes a number; names in the lock and in pins follow renames in both directions.
3. **Keys must be optional in files.** Most maps are written by agents' generators, which emit no keys. If the
   format bump makes `x-key` fields required, every generator breaks at S5b1. Say: the core fills a missing key on its
   next write, and a regenerated file's keys are positional again (pins on its sub-objects may move; a known limit of
   generated projects).
4. **`oymap record` races the watcher.** The host's watcher records the generator's change as `outside` within 200 ms;
   the agent's `record` a moment later finds nothing new. `record` must be able to put its author and label on the
   unattributed outside entries since that author's last entry.
5. **Pins on sub-objects before keys exist.** Pins format 1 arrives in S5a1, keys in S5b1. Until then a pin anchors
   to a top-level id or a point only.

Smaller: `merge_key` amends the latest entry, which is the one exception to "append-only" and should be named as
one; an `add` whose id the core allocates cannot be applied by the client ahead of the answer; `<stem>.studio.yml`
must be written by every install route the user plays from (the play roots of `output/studio_play`, not only
`--mount`); S5-0 with seven spikes is size M, not S.

## 6. The user's answers of 2026-11-14 (evening) and what hand authors change

The user said: "Do what you recommend", and added that in the end many people will make dungeons and terrain
entirely by hand, and others will let agents make the base and finish by hand.

### 6.1 The smaller open questions (document section 6.3): settled as recommended

| Question | Answer |
|---|---|
| Where the game's pin inbox lives | The default (`pins_inbox/` in the game's user data folder); `PLAY.md` says where |
| Map numbers for new maps | A range table in S6's manifests; until then a project-root setting |
| The design page's Discord questions | Ask them, and during S5a, not before S5c: the answers (which tasks, Blender or in-editor) shape S5b's hand tools. The user posts them; the bot only reads |
| World projects | The project list stays per map in S5; a world view comes later |
| The party's size in the studio's walk | The walk runs the game's movement code with the game's constants (radius 37 for every world today, `game/outdoor/OutdoorWorldRuntime.h:1872`). No setting of the studio's own; if the game gets per-world sizes, the walk reads the same source |
| Lighting bakes | Later; not jobs in S5 |
| Pins on a shipped map without a project | Yes: an empty overlay project named after the map |
| Projects inside `mods/` | Never; projects are folders elsewhere, and only builds are installed into `mods/` |

### 6.2 Three ways of working, each with an exit test

The architecture does not change: operations only, keys, one history, the schema inspector and the skipping lowering
serve a hand author as they are. What changes is what "done" means. The exit criteria of 6.4 test rebuilds measured
by `compare`; a hand author starts from nothing and never sees YAML. Add:

- **S5b1:** a small new dungeon made from an empty project entirely in the UI: no Source tab, no YAML, no command
  line. Every word that forced the Source tab is listed in the phase record; that list is the honest measure of G6.
- **S5b2:** the same for a small new outdoor map, land included.
- **S5b1 (mixed):** an agent-made map is finished by hand; then an agent adds to it through operations; every hand
  edit is still there.

### 6.3 Agent base, hand finish: R5 needs a mechanism, not a banner

Today agents write whole files from generator scripts (0.2). The document answers "a generator run erases hand
edits" with a banner and a rule in the procedures (2.8, R5). For a way of working that many will use, that is too
weak. Proposed, all in S5b1 when hand edits begin:

1. **A durable mark.** At the first transaction whose author is a person, the core writes a mark into `project.yml`
   (the `generated_by` note of 2.8 becomes a state: generators retired). It travels with git and with an exported
   zip; `.oymap/` does not.
2. **Agents are told.** `project.open`, `map_open` and every edit result of a marked project say: this project is
   edited by hand; change it through operations, never by running a generator again.
3. **A whole-file rewrite is caught.** In a marked project, an outside change that replaces objects a person changed
   last, or drops keys a file had, is recorded with an error notice that lists those objects, with one step to
   revert that entry. Precise operations by agents on hand-edited objects are not refused; their result lists the
   objects ("you changed 3 objects a person edited last").
4. **The procedures change** (REBUILD_PROCEDURE.md and the outdoor one): on a marked project agents edit by
   operations.

Not S5, but D12's archive should leave room for it: the procedures are what make agents' maps good, and they live
in this repository's `devdocs/`. People outside it who want an agent to make the base need them shipped with the
Studio download (as MCP prompts or a folder the host serves). Add to the deferred list.

### 6.4 Land by hand: D15 extended

Facts from `schema/sketch.schema.json`: `heights.nodes` holds absolute node heights in blocks, applied last, and
masks every word beneath it; `heights.grid` refuses a step finer than 4 cells ("a finer grid is a heightmap, not a
sketch"); the ground is at most three kinds of land, laid by zone outlines. So the format as it stands has no place
for land made entirely by hand.

The decision of 15:11 (sculpting only in bounded, marked patches) was my recommendation, made for maps agents keep
editing. It stays the default. With hand-only authors it needs one more case:

1. **Rebuilds:** unchanged (described; `nodes` under the lead's ruling).
2. **New maps made with agents (the default):** described first; sculpting in bounded, marked patches.
3. **Hand-made land (new):** a person may mark a project's land as hand-made in the UI; the mark is in the sketch.
   Then the brush may cover the whole map. No procedure sets the mark and a rebuild refuses it. Agents see the mark
   on open and read such land through queries (height at a point, a profile along a line, slope), not by reading
   rows. The checks run on the built land either way.
4. **Sculpt as differences, not as absolute nodes.** A raise, lower or smooth stroke is stored as a difference over
   the described land (a new word beside `nodes`, same block and row form). Then an agent can still move a ridge or
   a road bed under a person's strokes and the strokes stay; absolute nodes would mask the change without a word. A
   flatten stroke writes a `terraces` entry, which is already a described word. To be settled in S5b2 with one test:
   an agent moves a ridge under a sculpted patch.
5. **A stroke is previewed in the browser and committed once.** An outdoor validation takes 0.7 to 1.6 s with assets
   (Erathia 1.64 s, my timings in 1.2), far too slow per brush sample. The client moves the mesh it has; mouse-up is
   one transaction and the core's land replaces the preview. Add to S5-0 spike 2: the cost of one node-block patch on
   Erathia, so the budget of a stroke's commit is known before S5b2.
6. **Painting ground:** a paint brush that writes zone outlines (strokes merged per kind of land) needs no new word.
   Add it to S5b2's tools. The limit of three kinds of land per map is the classic format's and stays.
7. **Heightmap import** (deferred beyond S5): with a whole-map sculpt layer it is only a writer of that layer. It
   stays out of S5's acceptance but becomes the first addition after S5b2, since people who make land by hand come
   with tools of their own.

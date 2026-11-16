# S8: finishing the open studio work (2026-11-15, the lead)

PLAN.md's milestones S0-S7 are done. S8 collects what they left open that needs no decision from the user, so the
studio is whole before the user's hands-on check sets the next work. Sources: HANDOFF_LEAD.md section 7, S5.md ("S5c",
"S6 leftovers", "S6's game changes G1-G5"), `rounds/NEXT_CODE_BATCH.md`.

Not in S8 (each needs the user): the hosted deploy (D12, S5.md "S5c"); a Mods page in the game's menus (a design);
game changes beyond G1-G5 (ladder stepping out of `IndoorPartyRuntime` so the browser's walk climbs; bakes honouring
`--extra-mount`; the reload of PLAN 10b item 2; the "Not studio work" list of NEXT_CODE_BATCH.md); Xeen's next maps
(when the user wants them); S5's personal checks (a room wing and a town block by hand).

## Workstreams

Run in parallel, one agent each, each in its own build tree (the lead merges into `openyamm-studio/build/`).

| # | Work | Tree | Exit |
|---|---|---|---|
| S8a | Overlay authoring for G1, G2, G5: overlay projects write ladders, monsters and items, and cinematics overlays of a shipped map; operations, MCP, the Overlay tab; stale "waits for G3" texts | `build-s4`, `build-wasm-s4` | an overlay project adds a ladder, a monster, an item and a cinematic to a shipped map, each played headless in the game |
| S8b | Terrain for new open-air BLVs: a core rasteriser, `<stem>_blv_weights0.png`, `<stem>_blv.yml`, atmosphere words, install | `build-geo` | a new open-air BLV with terrain built and walked in the game; an MM9 region's weights from the core against `terrain_blend.py`'s |
| S8c | Indoor code list items 20-22 (checks and words from the user's walks and rounds; earlier items checked against the code first) | `build-fix` | each item built or recorded as refused with a reason, with its repro |
| S8d | Outdoor code list items 20-21 (Castle Ironfist and Erathia words and defects; 18-19 checked against the code first) and the two dead words (`kerb_width`, `facing`) | `build-mov` | as S8c |
| S8e | `kind: waterfall` rebuilt and finished (outdoor items 22, 23) | `build-pan` | Vertigo's falls built by the word, not as a building, beside Alvar's and Emerald's in pictures |
| S8f | The missed hosted budgets: Chrome's first open, indoor commit p95, outdoor commit and stroke + 3D, the 2.98 MB core download | `build-trig`, `build-wasm-perf` | each budget met or the measured reason it cannot be, in both browsers |

## Rules for every workstream

- Nothing existing breaks. At merge the lead runs: `oymap_tests`; `tests/s5_checks.sh`; `tests/native_vs_wasm.sh`;
  the 22 calibration projects and every shipped map's export old binary against new (`output/studio_lead/g/oldnew.sh`);
  every project's playtests (`output/studio_lead/g/play.sh`). A new word is opt-in, so existing projects build
  byte-identical; a deliberate change to existing output (a fixed default) is listed by project with its reason.
- No game changes (S8 is the studio's). A game defect found goes to the record for the user.
- The usual rules: HANDOFF_LEAD.md section 5.

## Record

(Each workstream's record follows here when merged.)

### S8b open-air BLV terrain (agent done 2026-11-15 ~23:30; not merged yet)

`core/GroundTerrain` (a port of `terrain_blend.py`'s steps, scipy's blur and nearest fill exactly; own PNG writer),
`core/RgbaPng`, `cli/GroundCommands` (`oymap ground` on any built BLV); the opt-in `ground` word in atmosphere.yml
(up to four `layers`, `materials`, `slope`, `edge_softness`, `fringe`, `meadow`, `grass`, `covered`); `oymap build`
writes `<stem>_blv_weights0.png`, `<stem>_blv.yml` and the scene's `terrain` block; `install` places them in
`worlds/<w>/terrain_materials/`. Parity on all 12 MM9 regions: weights identical texel for texel, material files equal
(PNG bytes 1.3-2x larger: simpler deflate). Example `examples/s8b_meadow` (studio09, mm9): walked 4/4, screenshots in
`output/s8b/shots/`. For the user (game): a new map cannot join mm9's `openAirMaps`; `assets_dev/worlds/mm9/terrain_materials/world.yml`
lacks `cliff_layered` and `snow`; headless runs load no terrain materials; `parseTerrainMaterialConfig` is not in the
shared core list (the studio compiles it itself). Left: the browser's 3D shows face textures, not the terrain; grass
files are not generated; ground in overlays.

### S8e waterfalls (agent done 2026-11-16 ~00:05; not merged yet)

The brief was stale: `kind: waterfall` was already its own model (`core/OutdoorFalls`, 2026-11-14) and Vertigo uses it.
Built: item 23's finish (one flat sheet with in-plane texels, so no tear along triangle diagonals; top water rising
from 12 under the stream over its first 256 and level over the last 768; `banks` (default on) and `textures.bank`
hide its sides; the land cut keeps one wet stream node per row) and the plot-floor defect (an explicit `floor` wins
over higher water, with a warning; repro `output/s8e/floor_repro/run.sh`). Shipped falls measured (Alvar
`WaterfallC1test`/`C2test`/`C4`, Emerald `CaveFall1a-4_E`; no foam decorations in either). Deliberate output change:
X1 `thing:rim_falls` (144 to 180 faces). Pictures: `output/s8e/shots/compare.jpg`. Vertigo would also want
`line: [[104, 60.4], [106, 60.4]]` and no `back: 768` (not applied: X1 is being edited by the Xeen X2 agent; the lead
applies it after). Game defects for the user: model water faces drawn as level (normal 0,0,1 in `OutdoorRenderer.cpp`:
upright sheets streak, no falling-water foam); model water always opaque with 1/768 waves; hairlines where water faces
meet at an angle (Alvar too); flow time never wrapped. Left: a project key for MM7's `cliff_from` per map.

### S8a overlay authoring (agent done 2026-11-16 ~00:30; not merged yet)

Overlay projects of shipped indoor maps write `scene.ladders` (foot, facing, height, `top_at`, width, reach, exit,
grab flags; base ladders named `ladder:<id>` in a new lock table, moved by `offset`/`facing`, removable),
`scene.monsters` and `scene.items` (appended after the base scene's and earlier world overlays'; `kills: {monster}` and
cinematic cues use that actor number; overlays may place the world's own table rows, e.g. MM9 Skeletoid 9183;
`hostile: false` refused), and cinematics (`wiring.yml cinematics` to `<stem>_<id>.cinematics.yml`; same name as a base
cinematic replaces it; checked by the game's parser; base cinematics in a new lock table). RPC `view.overlay`
(ladders, monsters with actor numbers, items, cinematics), contract fixture `s8a_overlay_tools`, MCP text, the
Overlay tab places ladders, monsters and items; the Cinematics tab marks replacements; stale "waits for G3" texts fixed;
`web/dist` rebuilt. Exit: `examples/s8a_isle_extras` (Isle of Ashes: a ladder, Skeletoid as actor 77, a longsword, a
new cinematic, `book_sinking` replaced) played headless 35/35 with the mount, fails at step 6 without. Deliberate
changes: `oymap import` adds `ladders`/`cinematics` lock tables for maps that have them. Left: projects imported before
S8a need a re-import to change base ladders; outdoor scene overlays still refused; base actors cannot be changed or
removed; the Overlay tab's additions checked by Vitest only.

### S8c indoor code list (agent done 2026-11-16 ~01:00; not merged yet)

Items 16-19 checked first: most already built; added and built `solve` counting floor items, nearer stand points in
`things` (XD-04's cabinet still has none), `thing.floating` sparing `hangs: true` and wall decorations, the silent-click
check needing the clickable bit. Item 20: `solve` `stranded:` monsters and spawns (fliers included; `audit --solve`
`reach.stranded`), `audit` `ride.no_switch`, the `new` project word (default with a `map_code`) and its arrival-text
warning. Item 21: platforms on a tunnel's flat floor (over leaning sides and pillars in tunnels refused: ring-built
floors), `lintel` on openings, the thinnest facing-wall pair for an opening, faces of floorless portal-less sectors left
out of solve/audit/probe/compare; ring kerbs refused (needs a multi-node click source); mist and exit pictures were
built before. Item 22: per-corner `top_heights` for "rests on nothing", a warning for decorations the world draws
nothing for, wall torches default to height 128 (the shipped mode), `bend_radius`/`bend_pieces` on paths and tunnels,
`stalactites`. Output changes: `build.json` warnings only (xd01 +1, xd03 +2, xd04 +1, xd05 -25 false). New audit
warnings: mm6_6d01 `reach.stranded` spawns 37 and 40; mm6_6d18 `ride.no_switch` machine bridge; mm8_d05 lifts
step1_e/w; xd04 the hoist. Game defects for the user: the scenario runner's `triggered_event: 0` for decoration events
(`IndoorRenderer.cpp` ~5727 sets it from `cogTriggered`, 0 for entities); `status()` loses step-event lines. Note for
the merge: contract answers holding "edited_by_hand since <date>" flip at midnight (pre-existing); the calibration
list now also picks up the new Xeen projects (x2, xd21, xd27, ...), so oldnew's project count grows past 22.

### S8d outdoor code list (agent done 2026-11-16 ~01:25; not merged yet)

Item 18 was built (S4R). Item 19 built: `thing.in_doorway` in `oymap audit` (indoor; XD-01's old keg found; 3 warnings
over the 161 shipped MM6-8 dungeons). Item 20: most words were built in batch O-H; new `roof: vault` (tiers or a half
ellipse, `vault_segments`), `porches[].open_corner`, `doors[].sill`, sign `toward` in degrees. Item 21: O-H had built
most words and all four defects (now with regression tests); new `arches.spans`, `pent`, culvert `grating`, a
doorway's `textures.roof` (turf hood), tent `roof: hip` with a door, `flare`, `half_hip`, platform `chamfer`; refused:
a face shown by an event (the game cannot click an outdoor face shown by `SetFacetBit`), `Hhr1bWALL` for mm7 (an MM8
texture; refusing it is right). Dead words made to work: `kerb_width` on bridges (default 32; Erathia's viaduct kerbs
32 to 64 as the original: the one deliberate output change, Erathia's playtest 2/2) and `facing` on doorways (Castle
Ironfist builds byte-identical). Where the words would apply in Castle Ironfist and Erathia (tried in scratch copies,
real projects not edited; pictures `output/s8d/bshots/`): a follow-up round with the user's walk.

### S8g studio fixes from the Xeen maps (started 2026-11-16 ~03:50)

Added after the five Xeen maps (devdocs/xeen/ACT2_BUILD.md): the inverted east-west arrival word in
`core/OutdoorInstall.cpp` (the game reads an arrival "left" as the east start), `install --mount` starting from the
mount's own tables, engine sounds accepted, `--mount` on validate/build, duplicate wiring ids refused, a no-spells map
word, `fit: true` exit pictures, a wall's `surface` over the room's bands, an opt-in bolster row; X1/X2's travel
workaround undone. Tree `build-s4`.

### Merge 37 (2026-11-16 ~05:00; S8a-S8e into `openyamm-studio/build`; before: `output/studio_lead/oymap_before_merge37`)

`oymap_tests` 441/441; contract suite (native, wasm, worker), host, MCP, live, play, jobs, lighting all passed; Vitest
176/176; native vs wasm 24 of 26 identical (XD-21 and XD-27 fail to build in both: the engine sounds S8g accepts);
old vs new: 247/247 maps identical, projects differing only as recorded (Erathia's viaduct kerbs, X1's rim falls,
`build.json` warnings of XD-01/03/04/05); every earlier playtest passes (25 lines, 4/4 or 2/2), XD-06's own 4/4 (its exit
test needs X2 in the mount). Two test fixes by the lead: the contract runner records the hand-edit date as `$TODAY` and,
after it, the revisions as `$REV1...` (they flipped at midnight; the cores are still compared on real hashes); the web
corpus test takes every calibration project (22 or more, the Xeen L4s included) and two stale allow entries (`facing`,
`kerb_width`, now read by the core) are gone. Logs: `output/studio_lead/merge37/`.

### S8g result (agent done 2026-11-16 ~05:30; merged as merge 38)

The arrival word fixed (north up, south down, east arrival `left`, west arrival `right`; own row and the way back);
X1/X2 joined both ways (X2 east to X1's west start, X1 west to X2's east start, both walked); installed travel rows now
equal the shipped ones for Castle Ironfist, New Sorpigal, Ravenshore (left/right) and, after `arrival_side` west to east
on their west edges (the only change to calibration projects), Erathia and Harmondale; Shadowspire's east and south
arrivals still differ from shipped (as before). `install --mount` starts from the mount's `map_stats.txt`,
`outdoor_travels.txt`, `bolster_maps.txt` (rows the root changed later are not picked up). Engine and world sounds found
as the game finds them (case-insensitive, with or without `.wav`, subfolders, root or mount). `--mount` on
validate/build now used. Duplicate wiring event ids refused. `rules: {no_spells: true}` writes the scene's
`runtime_restrictions: {allow_spellcasting: false}` (refused in overlays). `walls[].bands: false` (opt-in; making a
wall's surface always win broke the Hive's dome). `map_stats.bolster` (indoor: a row only when asked). Doorway `floor`
outdoors; model `turn` now rotates models and their planes. Not reproduced: `fit: true` tiling an exit picture. Not done:
`ruin` cap corners (mitring changes every built ruin). Checks: 448/448, native vs wasm 27/27, `s5_checks` rc 0 (Harmondale's
contract answer re-recorded for its edge), oldnew 25/27 identical (XD-21/27 now build), 247/247 maps.

### S8f hosted budgets (agent done 2026-11-16 ~06:00; to merge as merge 39)

Median/p95 ms, 20 runs each, alternating base and final at load 1.5-6 (±10-15 % noise). Met: Chrome's first open of
Darkmoor 7,242-7,691 to 1,423-1,650 (the cause was not lazy wasm compile but the asset folder's file input keeping
81,000 files in form state, copied into every history entry: the start page now empties its inputs); indoor commit + 3D
(a new `--gestures` harness mode, the person's own edit to the mesh drawn) 582-640 to 408-423 Chrome, 704-734 to 481-508
Firefox (history loaded after the views; the core keeps each changed file's parsed tree for the next call and
`project.open`; texture groups looked up per run of faces). Still missed: indoor commit p95 (60 % is re-lowering all 267
rooms and full checks per edit: needs incremental lowering/validation); outdoor commit + 3D over the commit +441-535 to
+198-257 (Chrome borderline, Firefox over); stroke commit; the core download 2.25 MB Brotli (S5c's 2.98 MB gzip was
mis-measured: the local server sent 10 MB raw; `stage_hosted.mjs` now writes `.br`/`.gz`, `hosted_server.mjs` serves
them). Tried and not kept: mimalloc (15 % faster, but Darkmoor's checks grew wasm memory to 1.1 GB; kept as
`-DOYMAP_WASM_MALLOC=mimalloc`), `-Os` (1.86 MB but edits 30 % slower), `-O2`, ThinLTO, no `-fPIC`, post-link wasm-opt.
Checks: native vs wasm 27/27, `s5_checks` with the worker suite passed, Vitest 176/176. `web/dist` needs a rebuild.

### Merges 38 and 39 (2026-11-16 ~06:30; S8g, then S8f's web bundle; before: `oymap_before_merge38`, `_merge39`)

Merge 38 (S8g; S8f's core changes were already in the sources): `oymap_tests` 448/448; `s5_checks` rc 0; native vs wasm
27/27 and both exports; oldnew 24/27 identical with 247/247 maps (XD-12/21/27 differ: their projects changed during the
run and XD-21/27 now build); playtests all pass except the Hive 3 of 4 once (its map byte-identical; 8 of 8 on rerun:
flaky, 1 in 12) and XD-06's exit test (needs X2 in the mount). Merge 39: the native core came out byte-identical (S8f was
already in), so only `web/dist` was rebuilt (`npm run build`); `s5_checks` rc 0, Vitest 176/176.
S8 is finished. Left for later (no decision needed): incremental lowering and validation for the indoor commit p95; the
download budget (`-Os` or wasm-split); `ruin` cap corners; the Castle Ironfist and Erathia words applied with the user's
walk (S8d's list); `things` stand point for XD-04's cabinet; the unbuilt words of indoor items 16-19 (S8c's list).

### Merge 40: monster hostility (2026-11-16 ~07:40; before: `output/studio_lead/m40/oymap_before`)

The user found half the monsters on the new Xeen maps peaceful and some fighting each other (golems and eyes on XD-12,
archers on X2). Cause: monsters placed one by one carry the Aggressor bit, but those from a map's spawn slots take
MMerge's `hostile.txt`, which has many MM7 stand-ins friendly to the party (Archers, Robbers, Moon clerics, Liches,
Golems, Mages) and sets Golems and Mages on Beholders. The fix (an agent): `core/MonsterRelations.{h,cpp}` holds the
one `relations` reader (moved from the indoor lowering), outdoor projects take the same block in `sketch.yml`, the
schemas share `common.schema.json $defs/relations`, and `oymap build` warns, with the row to add, when a slot kind or a
placed monster is friendly to the party unsaid, or two party-hostile kinds of one map fight each other (kinds of a
`map_stats.reference` row's own slots are taken as shipped and not checked). Ten Xeen projects say their relations
(X2 follows with its town change); each has a `playtest_hostility.yml`. Checks: `oymap_tests` 455/455; `s5_checks`
rc 0 after the schema-lint allow list moved the three known `relations` form gaps to `common.schema.json` and added the
outdoor key; native vs wasm 27/27; oldnew 25/27 projects and 247/247 maps identical (X1 differs as the old studio
cannot read its relations; X2's map identical, its build log gains the Archer warning). `web/dist` rebuilt. Installed
X1 and XD-01 to XD-27 (all but X2) into `xeen_root` with `output/studio_lead/xeen_install/install_keys.sh`.
Open (game change, needs the user's yes): indoors a peaceful group wins over a relation toward the party, outdoors
the relation wins.
X2 then installed (07:55) with its compacted town, scenery to the terrain edge (the cut was X2's generator, not the
studio) and its relations; every Xeen playtest from `xeen_root`, hostility checks included, 58/58.

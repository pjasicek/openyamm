# MM9 dungeons at x4: handoff for the texture session (2026-10-31)

You are the one texture session for the `mm9` world. You take every surface texture of the 24 rebuilt MM9 dungeons to
x4 with `tex.py` and Codex image generation, and you are the reviewer who keeps them consistent. The user approved the
job and will look at checkpoints (below); between checkpoints, decide yourself and write down what you decided.

## Read first, in full
1. [PLAYBOOK.md](PLAYBOOK.md), all of it. Its rules and later corrections hold; the sections that matter most here:
   "What a finished master looks like", "The loop", "Rules", "Assemblies", "Rotated copies" (mirrored pairs),
   "Neighbours", "Edge rims and margins", "Large textures", and **"MM9 rework maps"** (the Anskram Keep pilot).
2. `level_generation/projects/mm9r_anskramkeep/README.md`, "Texture density": how MM9's UVs map (1 texel per LithTech
   unit = 0.39 per native unit; door leaves show half of a double-door picture). The engine gap it describes (the 1×
   fallback drawn 4× too dense) **is fixed** since commit `f6bed391c` (`MapAssetLoader.cpp` uses the loaded file's
   tier); confirm once in game on a map without x4 files and correct that README line.
3. `devdocs/mm9_rework/STATUS.md` and `devdocs/mm9_rework/README.md` for where the rework stands.

## The user's three requirements (blocking, not nice-to-have)
1. **No seams in tiled surfaces.** Nearly every MM9 texture repeats on both axes and is mapped in world space on a
   128-unit grid. The wrap splice and the seam/edge/rim checks carry the weight: a texture that fails one is not
   accepted. Judge in game at a seam (close-up, grazing angle), not only on the sheets.
2. **No shading differences between neighbouring materials.** One brightness target for every master (`calibrate`,
   `config.json`); where two different textures continue into each other, `retry --match-neighbor`; where a picture is
   split over textures, an assembly (one canvas, one calibration). Review every map's joints and corners in game,
   native and x4 side by side, and look for a tone or saturation step across a joint.
3. **Double doors must fit exactly.** They are very common. In MM9 a door leaf may show half of one picture (Anskram's
   `anskramdoor`: each 123 × 246 leaf shows half), be one texture flipped by UVs, or be two textures (left/right). Before
   any bulk work, do the **door audit** below.

## Order of work
1. **State.** `python3 tex.py status`. No other x4 session ran since the Anskram Keep pilot (ledger 2026-10-30 00:57,
   23 mm9 masters accepted). Before `inventory` or `calibrate` (they rewrite every world's state), check that no other
   session is accepting (`ledger.jsonl` tail, the `.gen-*.lock` holders); if one is, ask the user.
2. **Inventory over all 24 dungeons:** `python3 tex.py inventory --world mm9 --map <map>.blv` for each built BLV in
   `output/mm9_rework/assets_dev/worlds/mm9/maps/` (the map scope is kept for reruns). The floor-hole re-conversions of
   2026-10-31 are done; another agent may still rebuild `1000terrors.blv` (monster sizes): texture names do not change,
   rerun its inventory scope if its faces changed. Expect about 550 textures (551 measured, 23 done).
3. **Door audit (before generating anything else).** List every door texture across the 24 maps: the faces of every
   mover (`initial_state.doors` in each `<map>.scene.yml`, face ids into the BLV), their textures and how each leaf maps
   the texture (whole picture, half picture, flipped). For each double door: do the two leaves form one picture, and
   does `tex.py`'s assembly detection list them together? Where it doesn't, add the pair to `assembly_overrides.json`
   (members in order, axis), or use `--mirror` for a mirrored pair. Write the table to
   `level_generation/textures_x4/audit/mm9_doors.md`.
4. **Door pilot:** about 10 door types (the common ones first), generated, installed, and looked at in game **closed
   and open** (`SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated tex9_<name> --world mm9 --map <map>.blv --assets
   "$PWD/output/mm9_rework/assets_dev" ...`, a tour YAML for several poses; see AGENTS.md). **Checkpoint 1 with the
   user** (stop and report with screenshots): door pilot plus a few tiled walls/floors from one map.
5. **One full map** (Anskram Keep is half done; then a mid-size map such as Verhoffin Ruins or Temple of Honk):
   everything accepted, installed, reviewed in game for seams, corners, joint tone, doors. **Checkpoint 2 with the
   user.**
6. **The rest, by map**, largest surfaces first (`next --world mm9 --count N` picks coherent sets). Install and review
   per map; keep a per-map line in the ledger section below.

## Throughput
- `gen --world mm9 --parallel 12` to `16` (the user allows about 4 Codex image workers per agent and does not mind
  many in parallel; the mm9 scheduler is one per world, so the parallelism is the workers, not more sessions). No
  MM6–MM8 x4 session is running; if one starts, the workers add up (playbook: about 4 each with three sessions).
- Codex quota: this job runs before the remaining ~960 MM6–MM8 textures.

## Install and review
- `python3 tex.py install --world mm9` cooks accepted masters (BC7 x4 + x2 PNG) into the review root through
  `review_root.install()`. No lighting re-bake is needed (bakes use the 1× bitmaps; the logical size stays 128).
- Review in the review root only (`output/mm9_rework/assets_dev`, the MM9 dungeons live there). Reference shots with
  `--set video.view_distance=unlimited`. MM9 dungeons are dark by design (lighting follows MM9's lightmaps): judge
  texture detail with a brighter view where needed and say so.

## Rules
- Never run `git add`, `commit`, `stash`, `reset` or `restore --staged`; never push. No Vulkan, no Android, no cmake.
- Safe deletes: `ls` first, then `rm` with literal paths only (a hook refuses `$`, `*`, `?` and backticks in an rm);
  never anything under `/dev`.
- Never kill a process you did not start; wait on your own run's exact PID (`kill -0 <pid>`), never `pgrep -f`.
- Every desktop game run starts with `SDL_AUDIODRIVER=dummy`. Runs overlap with other sessions: use `--isolated` with a
  unique `tex9_` name.
- `assets_dev` files are hard-linked into the review root: never write there directly; `tex.py install` handles it.
- Do not change MM6–MM8 data, maps or masters. Do not edit the map projects (`level_generation/projects/mm9r_*`)
  except to correct the density note in Anskram Keep's README.
- Keep durable state in the repo (`level_generation/textures_x4/`), not /tmp.

## Ledger (append one line per map as you finish it)
| Map | Textures | Accepted | Doors checked closed/open | Seams/joints reviewed in game | Notes |
|---|---|---|---|---|---|
| anskramkeep | 22 (+2 helpers) | 22 | yes (anskramdoor, anskramdoor2, thjordoor2) | yes, 6 rooms, 2026-10-31 | pilot 2026-10-30; course spacing in game identical to 1x (measured) |
| templeofhonk | 21 (+3 out of scope) | 21 | yes (honkdoor128, 2 doors) | yes, 7 rooms + spawn, 2026-10-31 | `Default` checker (`defar33vfj`) is on MM9's invisible collision ramps (face attribute Invisible, never drawn): excluded as a helper |
| connectingtunnels | 21 | 21 | closed (2 mover textures; no handler opens them in the tour) | yes, 6 rooms, 2026-11-01 | brightness x4/native per shot 0.96-1.00 |
| darkpassageway | 31 | 31 | yes (16 mover textures, 5 opened) | yes, 6 rooms, 2026-11-01 | 0.94-1.02; lowest is a wall-hugging graze |
| dookscastle | 28 | 28 | yes (dookyy3c4i, dook9r0f95; 1 opened) | yes, 6 rooms, 2026-11-01 | 0.98-1.02 |
| thearena | 19 | 19 | closed (arenadoor; no handler) | yes, 6 rooms + crowd close-ups, 2026-11-01 | crowd cut-out fixed (alpha); 0.98-1.04 |
| yanmirsfort | 15 | 15 | yes (7 mover textures, 2 opened) | yes, 6 rooms, 2026-11-01 | 0.98-1.07 |
| ruinedtemple | 25 | 25 | yes (7 mover textures, 2 opened) | yes, 6 rooms, 2026-11-01 | 0.92-1.01; lowest is a wall-hugging graze, detail not tone |
| 1000terrors | 32 | 32 | yes (10 mover textures, 4 opened) | yes, 6 rooms, scan A/B, 2026-11-01 | 0.97-1.05 |
| bathhouse | 34 | 34 | yes (6, 3 opened) | yes, 6 rooms, scan A/B, 2026-11-01 | 0.97-1.04 |
| beethoven | 37 | 37 | yes (5, 2 opened) | yes, 6 rooms, scan A/B, 2026-11-01 | 0.94-1.03 |
| chasmofthedead | 29 | 29 | yes (9, 1 opened) | yes, 6 rooms, scans A/B and D (reshoot), 2026-11-01 | 0.98-1.02; floor joints slightly red-brown (native has some), kept |
| dragonstadium | 2 (+ shared) | 2 | no movers | yes, 3 rooms, scans A/B and C, 2026-11-01 | 0.97-1.03; cave rock `rouglu1wpl` v5 (cell mosaic removed), x4 reshot |
| drangheimprison | 40 | 40 | yes (7, 5 opened) | yes, 6 rooms, scan A/B, 2026-11-01 | 0.96-1.02 |
| dungeonofsecrets | 24 | 24 | closed (12; none opened) | yes, 6 rooms, scan A/B, 2026-11-01 | 0.95-1.06 |
| hallofthegods | 18 | 18 | no movers | yes, 1 room (5 shots), scan A/B, 2026-11-01 | 0.99-1.00 |
| inventastorca | 30 | 30 | yes (12, 1 opened) | yes, 6 rooms, scans A/B and D, 2026-11-01 | 0.95-1.01 |
| klusoshouse | 24 | 24 | yes (2, 2 opened) | yes, 5 rooms, scans A/B and D, 2026-11-01 | 0.98-1.03; door `thjozz6y06` v3 (drop pull restored), x4 reshot |
| lichlab | 40 | 40 | yes (7, 1 opened) | yes, 8 rooms, scan C, 2026-11-01 | 0.94-1.04; door `verdrahook` v2 (dim copper), x4 reshot; carpet border lines kept |
| lindisfarnemonastery | 30 | 30 | yes (3, 2 opened) | yes, 6 rooms, scan A/B; x4 reshot, scan E, 2026-11-01 | 0.94-1.01 |
| tasaracademy | 30 | 30 | yes (6, 4 opened) | yes, 6 rooms, scan A/B, 2026-11-01 | 0.98-1.07; arch panel without its Greek-key frieze (known) |
| thjoradmine | 36 | 36 | closed (14; none opened) | yes, 6 rooms, scan A/B, 2026-11-01 | 0.91-1.05; lowest a dark room view |
| traininghall | 37 | 37 | yes (11, 1 opened) | yes, 6 rooms, scans A/B and C, 2026-11-01 | 0.96-1.04; `trai39pw68` v5 (bands in place, brush shows no red), x4 reshot |
| verhoffinruins | 35 | 35 | yes (8, 4 opened) | yes, 6 rooms, scan A/B, 2026-11-01 | 0.97-1.07 |
| arslegardcity | 131 | 131 | yes (door shots, joints continue) | toured, top-difference pairs checked; scan E unfinished | 0.98-1.13; door `dark1zba1z` 1.12 (figured wood grain plainer and lighter, kept for now) |
| drangheimcity | 129 | 129 | yes | toured (native and x4 reshot back to back on the 18:20 build); scan not run | 0.98-1.12; one grazing door shot 1.12 |
| frosgardcity | 64 | 64 | yes | toured, top-difference pairs checked; scan E unfinished | 0.95-1.01 |
| guberlandcity | 73 | 73 | yes | toured, top-difference pairs checked; scan F unfinished | 0.97-1.03 |
| sturmfordcity | 102 | 102 | yes | toured, top-difference pairs checked; scan F unfinished | 0.97-1.04 |
| thjorgardcity | 121 | 121 | yes | toured, top-difference pairs checked; scan G unfinished | 0.96-1.03 |
| thronheimcity | 199 | 199 | yes | toured, top-difference pairs checked; scan G unfinished | 0.96-1.03; `thjozz6y06` changed after the x4 tour |

## Decisions and progress (texture session, 2026-10-31)
- **Inventory** over all 24 built dungeons (map scope kept): 544 mm9 entries. Out of scope, by DTX folder/kind
  (`MM9_SKY_FOLDERS`, `MM9_WATER_FOLDERS`, `.spr` in `tex.py`): the skybox art (starfield, the Arslegaard cube in Hall of
  the Gods, Clouds1) as sky; animated `.spr` surfaces (Ocean3/4, slime, Water115/123/125, twinkle, Thjoradtank,
  TorchFlame2, Stream) and the `water115`/`water125`/`slime` frame folders as renderer materials (water shader or
  frame table per the MM9 visual-properties plan, not one static master). The inventory also reads the review root's
  `liquids.yml`. Left: 515 canonical textures, 493 pending after the pilot claims.
- **1× density** confirmed fixed in game (Temple of Honk without x4 files); the Anskram README line and the playbook's
  MM9 density note are corrected.
- **Door audit**: [audit/mm9_doors.md](audit/mm9_doors.md) (script `audit/mm9_doors.py`). No double door uses two
  textures; every pair is one texture, split at its centre column or mirrored, so no `assembly_overrides.json` entries
  and no `--mirror` copies are needed. Rim/edge flags on doors are judged on zoomed edge crops against what the edge
  really touches in the map (door bottom on the floor, black outside a pointed top).
- `tex.py next --names ...` claims a named set (used for the door pilot).
- **In-game review tooling**: `audit/mm9_door_tour.py MAP OUT TEXTURE...` writes a screenshot tour per door (closed
  front, grazing joint close-up, back, then the door's Lua handler via `event <id>` and the open view);
  `audit/mm9_tour_queue.sh ROOT MAP...` runs tours one after another. Native "before" shots are taken before `install`.
- Door pilot job `20261031-1312-mm9-klusoshouse-00`: 13 door textures and 5 Temple of Honk walls/floors/ceilings, all
  accepted (12 first try, 6 after one rolled retry).
- **Checkpoint 1 (2026-10-31, waiting for the user)**: 39 masters installed in the review root. Native and x4 tours
  of 12 maps: `audit/mm9_shots/pilot_native/`, `pilot_x4/`, side-by-side sheets `audit/mm9_shots/compare/<map>.jpg`
  (`audit/mm9_compare.py`). Every pilot door continues across its joint closed (split and mirrored alike); Temple of
  Honk walls/floor/ceiling show no tone step against native. Open: the tours' "open" shot did not open Lich Lab door 13
  (`PeasantDoor`) or Ta'Sar `D0_1` within 5 s; Yanmir's Fort front shot frames the wall under the 1219-unit door
  (the graze shot shows the door). `verify-families` lists 10 older MM6–MM8 mismatches (e.g. `mm8/t13b03l` 11.7),
  none in mm9; not touched.
- User approved checkpoint 1 (2026-10-31: "looks fine"), including the four flag overrides and the Honk door contrast.
- Native baseline for later maps: `output/textures_x4_runs/mm9-native` (hard-linked copy of the review root without the mm9 x4/x2 tiers; recreate it when the review root's maps change). `audit/mm9_room_tour.py` adds room shots (4 directions and the ceiling at the N largest floors); `ASSETS=... audit/mm9_tour_queue.sh` runs a tour on it.
- **Checkpoint 2 (2026-10-31, waiting for the user)**: Anskram Keep and Temple of Honk complete and reviewed; sheets in `audit/mm9_shots/{anskramkeep,templeofhonk}/{native,x4}/` and `audit/mm9_shots/compare/`.
- Found during the Honk review (not texture work, reported to the user 2026-10-31): the converter keeps the undersides of MM9's invisible ramp wedges as invisible ceilings (348 down-facing invisible faces over the 24 maps); on the stair at (-3497, 6556, -458) one sits 30 units above the ramp and every probe up the stair stops there (`audit/mm9_shots/honk_stairs/`). The Honk pool (`water115_0000`) and the other MM9 water frames have no `liquids.yml` entry yet, so they draw as static bitmaps.
- User approved checkpoint 2 (2026-10-31: "textures look very good"); stair and water findings sent to the dungeon session (openyamm-06). Step 6 started.
- **Step 6, 2026-11-01**: batches 3 and 4 reviewed (Dragon Stadium, Bathhouse, Dungeon of Secrets, Training Hall; Drangheim Prison, Thjorad Mine, Hall of the Gods): 147 accepted, 6 retried. Retry reasons: a blue cast on the rust plate `metacppdga`; a blocky artifact on the moss `sewehy7rja`; the native's own light/dark step at the v wrap of three floors/plates (`thjo3rw631`, `thjoj5hw88`, `rustjlf2n5`; the native's seam is removed, not copied); the lost engraved swirl pattern on the door `verdmohry2`. The last 45 textures (Chasm of the Dead, Lindisfarne) are claimed. Flagged wrap joints are judged on 1:1 crops of the u and v joints next to the native's (scratch `wrap.py`): every accepted flag sits on a joint the native has too.
- The maps were rebuilt by the dungeon session on 2026-10-31 afternoon/evening (new face ids, ramp-underside and Firethrough fixes): the native baseline `output/textures_x4_runs/mm9-native` was recreated on 2026-11-01 and the door audit rerun (unchanged except Lindisfarne's Firethrough, no longer a mover). `audit/mm9_doors.py` now reads only the inventory's mm9 `map_scope`: the review root also holds seven MM9 city BLVs since then (Arslegard, Drangheim, Frosgard, Guberland, Sturmford, Thjorgard, Thronheim), out of this job's scope until the user extends it.
- **Cut-out alpha (2026-11-01).** The Arena tour showed the x4 crowd as heads on black: MM9's decoded natives are 32-bit BMPs with alpha in the fourth byte, which the inventory (PIL) read as RGB, so 54 in-scope cut-outs were treated as opaque and 42 accepted that way. Fixed in `tex.py` (`bmp32_alpha`, inventory rerun: only those 54 `cutout` flags changed, no other world touched); the 39 whose art follows the native silhouette got the native alpha (`alpha-from-native`, backups in the session scratchpad); Grill1 `grilunvh56`, the light fixture `refil4lm4w` and the spiked fence `spik67hfer` were reopened (`redo`) and regenerate as cut-outs. Checked in game: the crowd now matches native (`audit/mm9_shots/arena_crowd/`).
- **MM9 cities added (user, 2026-11-01: "do also the textures for all the BLV MM9 cities").** `inventory --world mm9 --map <city>.blv` for Arslegard, Drangheim, Frosgard, Guberland, Sturmford, Thjorgard and Thronheim: 944 mm9 entries, 394 new pending, claimed in 17 jobs `20261101-1523-mm9-*`. Duplicate choice now keeps an already accepted copy canonical (`tex.py`, by_sha sort), so the scope growth did not orphan 3 dungeon masters. 10 accepted masters became uv-wrapped (the cities tile them on both axes); 8 pass the seam check on the new axis, `ston6favlb` and `thjoxaa44b` were redone. Door audit over the cities: 106 pairs, none with two textures (`audit/mm9_doors.md`). The long-running follow scheduler crashed on the grown inventory (it had the old code loaded); restarted as `jobs/gen-follow-20261101.log`.
- **City first pass and dungeon seam scans (2026-11-01).** The 356 city candidates got a first-pass review by four helper agents under `audit/city_review/BRIEF.md` (recommendations only, one `.txt` per job); the session spot-checked the flagged accepts and applied the files with `audit/city_review/apply.py` (accept, retry with roll/note, native alpha for cut-outs). Transparency-only retries (Sturmford timber window, stone window, bracket post, iron lattice; Arslegard balcony, letterbox slot, iron bar) were accepted with `alpha-from-native` instead and checked by eye. 15 more dungeons toured native/x4 (`audit/mm9_tone.py`: per-shot brightness x4/native 0.92-1.07, medians 0.97-1.02) and scanned for seams by two helpers (`audit/mm9_shots/seam_scan_{A,B}.md`, every suspect checked by the session). Redone from the scans: the Dragon Stadium cave rock `rouglu1wpl` (hard crack cells), the training target `trai39pw68` (straw-coloured bottom rows: gold lines along every polygon edge), the fluted column `dungb81u7w` (hard horizontal line), the Klusos crown band `dook9r0f95` (lost dentils), the church wall `sturfpaxnn` (stray broken fragment), the Lindisfarne rose window `windmrpguz` (over-saturated). Judged fine: the Dungeon of Secrets pilaster joint and the Hall of the Gods mural (both as native), the Bathhouse door, the Chasm bas-relief door. Known deviation: Ta'Sar's arch panel `tasa9e789m` lost its Greek-key frieze in all four tries; accepted v4 with a plain band.
- **Round 3 (2026-11-01 evening).** 79 candidates reviewed by the session: 75 accepted (13 cut-outs given the native alpha), 4 retried (`sturtuff78` course breaks at the joint, `celt1qw2pn` turquoise border, `doors33i72` missing grille bars, `thjo8x5sx0` periwinkle glass). The training target takes `trai39pw68` v2 (white rows at both wrap edges; the rolled v3 was misaligned). `sturfpaxnn` (2048 wide, generated in sections) came back split at the centre in both versions: the master is hand-built from v2, mirrored about the native's symmetry column (x 1004 of 2048) with the centre joint of each course removed (`edit` events in the ledger). 896 of 907 in-scope textures accepted and installed; tours of the seven cities and Lich Lab running, plus x4 reshoots of the six dungeons whose textures changed.

## Session 2026-11-01 evening (resumed 17:20)
- **All 907 in-scope textures accepted and installed** (11 more this session). `celt1qw2pn` v3, `doors33i72` v3,
  `worn0xmxl8` v1, `grch2o628c` v2, `stucbxndut` v2, signs `signqbd5l6` v1, `sign0xzevw` v2, `signuth36o` v2 (the
  MAGI and WEAPONS emblems redescribed from the natives: wizard in a purple hat over flames; axe crossed with a sword).
- `sturtuff78` (Sturmford church base wall, the largest city texture) is now **standalone**: its prefill copied the
  church front `sturfpaxnn` (hand-mirrored) and the church upper `sturcwaq6d` (accepted with layout 0.63), whose
  courses differ from the base's native, and every version came out with broken, notched courses. None of the three
  has map neighbours. v3 standalone has the native's straight courses. `fort362ynh` (Guberland, 73 % the same stone)
  copies only from it (`--prefill-from sturtuff78`); v4 accepted over `rim top 0.48`: one dark master row from the wrap
  splice exactly on the native's own wall-to-frieze joint (native 86 | 97), judged at 3x; four versions all drew it.
- `grch2o628c` (Arslegard plain plaster under the frieze) copied grey wedges from the stone arch's shading in
  `grchnijyj9`; now `--prefill-from grchjzo7z3` (the timber arcade, same frieze and beam).
- `thjo8x5sx0` (Thronheim leaded glass) v4 with material "pale grey frosted glass" and native alpha
  (`alpha-from-native`, smooth, 0.60 transparent); its leads line up with the native alpha (corr 0.92).
- The city performance session rebuilt six city BLVs 16:32–17:07 (roof-line portals): `inventory --world mm9` rerun,
  no texture, relation or other-world change; the native baseline `output/textures_x4_runs/mm9-native` recreated
  17:30 (inodes match the review root).
- `verify-families`: 11 mismatches, the 10 known MM6–MM8 ones plus `mm9/sturfpaxnn` against `sturcwaq6d` (14.5): the
  deliberate hand-built mirror, no map neighbours; known deviation.
- Tours shot: Lich Lab native + x4; x4 reshoots of Dragon Stadium, Training Hall, Inventa Storca, Klusos House, Chasm
  of the Dead, Lindisfarne; native (new baseline) + x4 of the seven cities. Brightness x4/native per shot 0.94–1.04 in
  the dungeons and in five cities; Arslegard's door `dark1zba1z` 1.12–1.13.
- **Seam scans C/D** (six dungeons, 287 pairs; `audit/mm9_shots/seam_scan_{C,D}.md`), every suspect checked by the
  session. Redone: `verdrahook` (Lich Lab door, copper panels bright orange against greyed wood; v2 dim copper),
  `trai39pw68` (training bands: the red band 6 rows too high and too low, so the jousting brush showed red; v5 with
  `--ref-blur 0.6` and exact band percentages puts every band within one native row; v4 default blur and v6 rolled
  failed), `rouglu1wpl` (Dragon Stadium cave rock, fine cell/crackle mosaic; v5 `--ref-blur 2.5` without "granular"
  in the note), `thjozz6y06` (Klusos door: its material line said "keyhole plate", the native has a drop pull; v3).
  All four reshot in game and correct. Kept: Lich Lab carpet `carpkip1vt` border lines (the native's medallion rug
  drawn sharper), Klusos crown band (sharper dentils), Chasm floor joints (slightly red-brown, the native has some), the
  fur door's thin side strip and the blue door panel `yanmleoxzq` (mild).
- Another session rebuilt Thronheim, Drangheim, Sturmford and Arslegard again 18:14–18:34, so Drangheim's first
  native/x4 pair compared two builds with different lighting (up to 8.5x). Baseline recreated at 18:40; Drangheim
  reshot native and x4 back to back: median 1.00. The other cities' pairs compare fine.
- **Seam scans E/F/G of the cities stopped unfinished** (Claude 5-hour limit at about 19:40). In their place the session
  checked the five largest-difference pairs of every city: all sharper detail, same layout and tone, double doors
  continuous.

## Resume here (2026-11-01 about 20:10)
Nothing is running. **All 907 in-scope textures accepted and installed** in the review root (24 dungeons + 7 city
BLVs; 944 entries, 37 excluded). The native baseline `output/textures_x4_runs/mm9-native` matches the review root as of
18:40; another session is still rebuilding city BLVs, so recreate it (hard-linked copy without `worlds/mm9/textures_x4`
and `textures_x2`) before any further native/x4 pair, and shoot native and x4 back to back.

Left:
1. City seam scans per `audit/mm9_shots/SEAM_SCAN_BRIEF.md` (ids E/F/G were started, no output written): Arslegard,
   Frosgard, Lindisfarne; Guberland, Sturmford; Thjorgard, Thronheim; Drangheim. Check every suspect yourself.
2. Decide on Arslegard's door `dark1zba1z`: its figured, bookmatched wood grain came out plainer and lighter (in game
   1.12–1.13 against native). Not redone yet.
3. Thronheim, Drangheim and Thjorgard x4 tours predate `thjozz6y06` v3; reshoot if those doors are reviewed again.
4. Known deviations accepted: Ta'Sar `tasa9e789m` without its Greek-key frieze (4 tries); `sturfpaxnn` hand-built
   (small notch under the keystone; `verify-families` lists it against `sturcwaq6d`, no map neighbours); `fort362ynh`
   one dark master row on the native's wall-to-frieze joint; `trai39pw68` one canvas row at the top edge.

Tools added this session: `tex.py` `bmp32_alpha` (MM9 BMP alpha), `alpha-from-native`, accepted-copy-stays-canonical,
`next --names`; `audit/mm9_doors.py` (map_scope only), `mm9_door_tour.py`, `mm9_room_tour.py`, `mm9_tour_queue.sh`,
`mm9_compare.py`, `mm9_tone.py`; `audit/city_review/` (BRIEF.md, rv.py, apply.py, per-job review files).

## Outdoor regions (2026-11-02)
Decision (user): the outdoor regions become outdoor BLVs. Their textures, read from the old import's ODMs (`MM9_*` prop
BModels skipped: the props' skins are a separate batch), were the last 92: four jobs (`20261102-1555-mm9-*`:
lindisfarnemonastery-00, frosgard-01, yorwick-02, wizardslab-03), generated with `tex.py gen --world mm9 --parallel 6
--follow` and reviewed on the sheets. **All 1 002 in-scope MM9 textures accepted and installed** (44 excluded).
- Retries that fixed a flaw: dark bottom/top edges (sturqhghpm, sturiqrkzt, guar7vbbtd), a repeat band (shin9gbl24),
  clover and lilac in grass (sturcr4dba v3, boot3dzfn6 v3), the column arcade (coluw11o92 v2), pink grout
  (marb9xf18f v2), beach sand grains (sand3yuxai v2). Stained glass `archmiulrz`: native alpha (smooth, 0.37).
- Codex image calls took 450-900 s in the afternoon (hangs at the 900 s timeout; a texture gets two attempts per
  scheduler process, so restart the scheduler for the ones that failed twice) and 50-130 s in the evening.
- The Isle of Ashes pilot root (`output/mm9_rework/isleofashes_blv_root`) is a separate hard-linked copy: after
  `tex.py install --world mm9`, link the new `worlds/mm9/textures_x4`/`textures_x2` files into it.
- In game the isle's ground showed MM9's own flaws once sharp (per-polygon mapping, flat light, no blending); its
  ground faces now draw blended terrain materials (devdocs/INDOOR_OPEN_SKY.md "Terrain"), so the x4 masters of
  terrain textures matter only where a map keeps them textured. Measured on the isle's cliffs (before the terrain
  path): the x4 frames came out about 0.67 of the native's brightness, where the dungeons and cities measured
  0.95-1.13; not investigated further (those faces no longer draw their texture).


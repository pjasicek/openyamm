# MM9 Fish (mm9_fish) — 3D model, 2026-10-30

The MM9 fish (`mm9/extracted/MODELS/MODELS/FISH.abc`, 18 joints, 70 tris, one clip) for the MM9 world: row 227 "Fish"
(fish.dtx, fish.scr, no Hostility, `Transparent 1`). Built on the MM9 rig-reuse route of `../mm9_dfly_claude/`,
`../mm9_wolf_claude/` and `../mm9_crow_claude/`: a new HD Meshy body weighted to the original MM9 skeleton, fin leaves
of our own with MM9's alpha cut-outs, MM9's `swim` keys behind every role. Progress, hashes and receipts:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_fish.glb` (cooked copy in `assets_dev`); one skin, no tiers |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_fish_claude`: `MM9 227 Fish`, scale 100 (100 x MONSTERS.txt `Scale` 1) |
| Data | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` row 227, legacy actor 178 (MM8 School of Fish A) |
| Triangles LOD0/1/2/3 | 5,558 / 2,778 / 998 / 332 (LOD0: body 3,598, two eye lenses 512, fin leaves 1,448) |
| Materials | `Fish` (2K colour, 1K normal and ORM, opaque), `FishFin` (1K RGBA atlas from the side master, MASK 0.5) |
| Skeleton | the MM9 one, names unchanged: `XCENTER`, `Xbody`, `Xtail`, `Xtmid`, `Xttop`, `Xtbot`, `Xtopfin`, `Xmidfin`, `Xbotfin`, `Xsfin`, `Xsidefin` (+`01`), `Xbotfin.001`, `Xbotfin01`, `Xmouth`, `Xjaw` + `Socket_Mouth` |
| Clips (30 fps) | Walking 0.7 (swim), Running 0.467 (swim x1.5), Standing 1.167 (swim x0.6, half amplitude), Fidget 1.4 (two beats), Hit 0.333 (swim x2.1, amplitude 1.35, 14 degree roll), Death 2.367 (ours), Dead 1.0 |
| Gait | stride 0.36 per cycle (about a body length per beat), `gait_rate: [0.8, 1.5]` like MM8's School of Fish: no foot contact |
| Floor | swimmer rule since 2026-11-04 (Fly `S`): MM9's origin at the centre of the MM9 body box, +0.4096 m on every living clip (`floor_fix.py --swim`), Death eases into the corpse on its side on the floor; `floor_audit.py --world mm9` ok (kind `swimmer`). Before it a ground lift of +0.018 |
| Meshy credits | **15 / 30** (backup account): Smart Topology 5, 4K retexture 10 |

## Where MM9 places fish, and how they move

- **Placements.** Only Temple of Honk (`TEMPLEOFHONK.dat`) has real fish: six `Fish` objects `Fish0`-`Fish5` around
  (-1184, -192, 2432..2816), `models\fish.abc`, placement `Scale` 0.4-0.7, no script of their own. They are the only use
  of the model. The other objects of class `Fish` are invisible script carriers, not fish: Anskram Keep
  `ImpGateSpawner0-7` (`AK_ImpGate.scr`) and 1000 Terrors `SquareObj*` (`ChessSquare.scr`, `models\flyingicky.abc`).
  The binding keeps table scale 100, so a converter that wants MM9's look must carry the 0.4-0.7 placement scale.
- **`fish.scr`.** `Walk` always (the only clip). On each `Tick`: a 5 % chance to `PlayAnim Jump` when the fish is within 5
  body heights of the top of its liquid container (`GetLiquidContainer`, `GetObjectMinMax`), but FISH.abc has no `Jump`
  clip; otherwise `Rotate` about the vertical by a random 15-90 degrees of random sign, at a rate equal to the angle (so
  about a second per turn), then a 0.5-1 s wait and the next `Tick`. `HandleObstacle` faces the collision normal and
  walks on; `HandleStuck` runs `Tick`. There is no attack, flee or AI state: `WalkVelocity` 30 forever.

## Swimming: the binding since 2026-11-04

The engine swims since 2026-11-02 (`devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md`). Row 9227's Fly cell is `S`
(`generate_mm9_monster_tables.py` SWIMMER_SOURCES, `MonsterStatsEntry::swims`): a fish that starts in a scene water
volume flies in it, bound to it; anywhere else it is a walker.

- **Clips.** MM9's swim keys unchanged; the living clips carry MM9's origin at the centre of the MM9 body box (FISH
  Dims half-height 16 LT: **+0.4096 m**; height 82 = 2 x 16 x 2.56), the rule of the Jellyspore and the Sea Monster
  (`floor_fix.py --swim 0.4096 Death Dead` in `scripts/build_runtime.sh`). Death eases into the corpse lying on its
  side on the floor (it sinks to the bed: no floating corpse). Pre-swim files in `work/before_swim/`.
- **Out of water** (MM9's fish are in no water volume, RE section 6) the walker's body box stands on the floor and the
  fish swims 0.39-0.6 m over it; the row is `Stationary` (all NPC rows), so it idles there, finning.
- **Still open**: `fish.scr`'s free wander with yaw-only turns and the 5 % surface `Jump` (no clip), a floating
  corpse, the 0.4-0.7 placement scale of Temple of Honk (a converter's job).
- **Checks.** `check_winding` 0 inverted; viewer revision `r9_fish_swim_20261104`, `run_creature_review.py check` 7
  switches, 0 errors.

## Decisions

- **Own fins, Meshy body.** Meshy's fins came as thick sheets with outlines that ignore the HD side masters. They are
  removed: the shell's distance field (openvdb, 1 mm), a morphological opening (ball 3 mm, `scripts/fish_open.py`), the
  Meshy surface kept wherever the opening took nothing, mirrored in x. Fins are own closed leaves (two sheets, 0.8 mm
  apart) on a coarse grid (`scripts/build_fins.py`): outline, rays and colour from `references_hd/03_left.png`, cut out by
  its alpha (MASK 0.5, MM9's own technique: MM9's FISH.dtx draws the fins with soft alpha edges on quads, Transparent 1).
  The master's fish is slimmer than Meshy's, so `work/fins_config.json` annotates each fin's root line in the master,
  columns shift so roots sit on our back and belly, and each leaf is buried 26 master px in the body. The pectoral
  overlaps the flank in the master, so its outline is an annotated polygon. Right fins mirror the left.
- **Long fins follow the spine.** MM9's swim holds the fins swept back by a near-constant rotation about one pivot each
  (`Xtopfin` 40, `Xmidfin` 30, `Xbotfin` 44 degrees). On a long leaf one pivot sinks the far end 4 cm into the body and
  compresses the sheet to a fifth, so dorsal and anal take the weights of the body under them; the master's rays already
  lean back. Caudal lobes, pectorals (flap at 60 %) and pelvics keep MM9's bones (`scripts/rig_fins.py`).
- **Paint.** The side masters paint the pectoral onto the flank under our leaf. `compose_fish.py` replaces only the low
  frequencies of that smear with the flank's from 7.5 cm behind at the same elevation (the scale detail stays), and
  softly copies a small dotted oval off the stub Meshy's fin left. Body roughness is 0.68-0.85 and fin roughness 0.92:
  at Meshy's values the viewer showed a white sheen along the back, which the paint does not have (the engine runs
  specular 0).
- **Mouth.** No clip opens it: `Xmouth` and `Xjaw` move together, so they carry only the lips (18 mm of the snout). The
  mouth is the Meshy tube, painted inside, with no gums or teeth (MM9's fish has none). Meshy made it a big round O with
  a thick lip ring, so `scripts/mouth_deform.py` (a stage after the fins: same topology and UVs, retexture kept) scales
  it about the mouth axis, x 0.74 and z 0.5: the cavity fully, lips and snout by a falloff that stops 20 mm behind the
  lips above the mouth (the eyes keep their skin) and 36 mm under it (no step at the chin). `scripts/mouth_measure.py`
  gives the numbers. In the viewer's front shot the opening is now about 0.37 of the head width and 0.70 tall to wide
  (master 0.38 and 0.65; before 0.48-0.55 and about 1.1).
- **Eyes.** Meshy's eyes were small sunk bumps; clean lenses (r 5.8 mm, 2.2 mm proud) rigid with the head, painted by the
  retexture.
- **Shadows.** The engine refuses non-opaque dedicated shadow LODs, and an opaque leaf would cast its square grid cells:
  `scripts/strip_shadow_fins.py` takes the fin triangles out of the shadow meshes. The fins cast no shadow.
- **No tiers.** One skin (FISH.dtx), so no region mask or ramps.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_fish_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
$V $C $M/FISH.abc $P/source/fish --id fish --texture 0=$S/FISH.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/fish/fish.glb $P/work/mm9_fish_rig.blend 0 0.0722
$B $P/scripts/fish_volume.py $P/work/mm9_fish_rig.blend $P/meshy/fish_smart_v1/model_urls_glb.glb $P/work/fish_sdf_v1.npz \
  $P/work/meshy_fit_v1.blend $P/work/fish_volume_v1.json
python3 $P/scripts/fish_open.py $P/work/fish_sdf_v1.npz $P/work/fish_open_v3.npz 0.003
$B $P/scripts/fish_mesh.py $P/work/fish_open_v3.npz $P/work/meshy_fit_v1.blend $PWD/$P/work/open_v3.vdb $P/work/body_v3.blend
$B $P/scripts/dump_mesh.py $P/work/body_v3.blend $P/work/body_v3.npz Body Eyes
python3 $P/scripts/build_fins.py $P/work/body_v3.npz $P/work/fins_v2.npz $P/textures/fish_fins_basecolor.png
$B $P/scripts/add_fins.py $P/work/body_v3.blend $P/work/fins_v2.npz $P/textures/fish_fins_basecolor.png $P/work/finned_v1.blend
$B $P/scripts/reduce_body.py $P/work/finned_v1.blend $P/work/reduced_v1.blend 3600
$B $P/scripts/rig_fish.py $P/work/reduced_v1.blend $P/work/mm9_fish_rig.blend $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/uv_atlas_fish.py $P/work/rig_v1.blend $P/work/uv_v1.blend $P/texturing/fish_body_upload.glb $P/work/uv_v1.json
# xatlas packs differently per run: never re-run the line above once the upload went to Meshy (fish_retexture_v1)
$B $P/scripts/rig_fins.py $P/work/uv_v1.blend $P/work/fins_v2.npz $P/textures/fish_fins_basecolor.png \
  $P/work/mm9_fish_rig.blend $P/work/uv_v2.blend $P/work/rig_fins_v2.json
$P/scripts/mouth_tail.sh $T 0.74 0.5 r8_fish_20261030   # mouth deform (uv_v3), dump_uv3d, AO, texel map, compose, grade,
                                                        # export, runtime, viewer GLB and manifest
python3 tools/creature_workspace.py run --project $P --token $T -- python3 tools/install_model.py $P/export/mm9_fish.glb --world mm9
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \
  python3 $P/scripts/bind_actors.py mm9_fish_claude $P/work/actors_block.yml
python3 level_generation/projects/mm9r_common/review_root.py
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (framing scaled to 0.34 m): `tools/run_creature_review.py check` 1 skin x 7 clips, 0 console
  errors; `playback` recorded every clip at 1x and 0.5x (`review/playback/`).
- Texture (`texture_quality.py`, `review/texture_quality.json`): body atlas 66.7 % (target 55), spread 1.06 (1.3),
  fragments 0.0 % (3), stretch p90 1.05 (1.5), 4K paint downsampled once, gentle grade. Fins: 1K atlas at 3.6 px/mm,
  stretch p90 1.4.
- Symmetry: ours 0 mm mirror error (body mirrored, fins mirrored or on the midline); MM9 0.82 mm max, so MM9 is symmetric.
- Orientation (`scripts/head_gate.py`, Walking against MM9 swim, 22 frames): snout direction 2.2 degrees mean, 4.0 max
  (2.2 of it the bind difference), up vector 6.0 max, no roll.
- Head shape: a broad perch head with a flat oval mouth, large eye and gill cover; matches the masters and a real fish
  after the mouth deform (`review/sheet_viewer_mouth.png`: front, ¾, side, below).
- Attachment: `detached_parts_audit.py` 0 detached in every clip (17 pieces, 16 of them leaf sheets and lenses, all
  rooted; six listed as shallow, 0.8-4.9 mm in the Hit extreme). No stray shards in the viewer.
- Folds (`scripts/fold_measure.py`, 48 fps): worst frame 8 folded faces (Hit), Fidget 6, Walking 3, Standing 2, of 5,558.
- Stretch (`scripts/gates.py`, `review/gates.json`): loop seams 0 (Standing, Walking, Running); edge ratio p1/p99
  0.57-0.76 / 1.37-2.16 per clip; extremes on the root band of the fins, inside the body.
- Smooth shading (`flat_shading_check.py`): body 0.01; fins 0.76, flat leaves by design.
- Clips: every change is on swim's keys (amplitude, an added roll); nothing per frame, the MM9 seam was already 0.
- Floor audit `floor_audit.py --world mm9`: MM9 227 Fish ok. Winding 0 inverted closed parts.
- Regression `mm9_actor_models_build_every_binding` (`--world mm9`): PASS, 61 descriptors on 28 models, 0 failed.
- Sheets from viewer shots, each inspected (`review/sheet_final_clips.png` is the final model; clips and Death sheets predate the mouth deform; `review/sheet_viewer_mouth.png` is
  r8): `review/sheet_viewer_clips.png` (clips and angles: side, front, ¾, below,
  top), `review/sheet_viewer_death.png` (below, Death, corpse), `review/sheet_viewer_closeups.png` (flank, pectoral, belly;
  its mouth view predates the deform), `review/sheet_mm9_vs_ours.png` (rows: MM9, ours, MM9, ours; side and top, four swim times; MM9 rows
  rendered in Blender, MM9 has no viewer). Compared with MM9 the swing of the tail, the head and the body bend match. No in-game run: no MM9 map places the fish as an actor yet.

## Deviations and open points

- Fins do not sweep back as MM9's do (above), and they cast no shadow.
- No tiers. The body is deeper and wider than MM9's (half width 3.1 against 2.3 cm), as Meshy built it from the master.
- MM9 has no Fidget, Hit or Death: those clips are ours, built on the swim keys. MM9's `Jump` was never authored.
- Upward-facing surfaces of the corpse read very bright in the review viewer's overhead light (pale belly, flat fins).
  It is the viewer's light; the paint is unchanged.
- The back's silhouette shows slight facets at the nape close up (3,598 body triangles after the voxel clean).
- A faint hint of the master's pectoral rays stays in the flank's fine detail where the fin swings off it, and at some
  swim phases a small grey notch shows at the right pectoral's root, where the flank meets the leaf.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_fish_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_fish_reduce_claude/before/`.

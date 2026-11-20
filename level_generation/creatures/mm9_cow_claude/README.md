# MM9 cow family (mm9_cow) — 3D model, 2026-10-30

The MM9 cow (`mm9/extracted/MODELS/MODELS/COW.abc`, 38 joints, 453 tris, 15 clips) for the MM9 world: Cow (row 267,
9267, skin COW) and Brown Cow (row 297, 9297, skin COWBROWN), both `cow.scr`, Hostility 2. Built on the MM9 rig-reuse
route of `../mm9_dfly_claude/` and `../mm9_wolf_claude/`: a new HD Meshy mesh weighted to the original MM9 skeleton, the
MM9 clips played with only the listed fixes. Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_cow.glb` (cooked copy in `assets_dev`), skins `cow_a`, `cow_b` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_cow_claude`: `MM9 267 Cow`, `MM9 297 Brown Cow`, scale 100 (MONSTERS.txt `Scale` 1) |
| Descriptors | NPC rows in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 267 -> Gorgon A (124), 297 -> Gorgon B (125), the MM8 bull as fallback visual and sound set |
| Triangles LOD0/1/2/3 | 8,544 / 4,272 / 1,536 / 512 (LOD0 skin 7,142, mouth cavity 682, eyes, teats and tassel 720) |
| Skeleton | the MM9 one, names unchanged (`XCENTER`, `XbackA/B/C`, `Xback`, `Xneckbase`, `Xneckpiv`, `Xheadpiv`, `Xhead`, `Xjawpiv`, ears `Xearpiv(01)`, legs `Xflegpiv-Xfleg-Xfankle-Xffoot`, `Xblegpiv-Xbleg-Xblegmid-Xbankle-Xbfoot` (01 = left), tail `Xtailbase ... Xtail`) |
| Clips (30 fps) | Standing 2.0 (Stand), Walking 1.2 (Walk), Running 0.4 (Run), Fidget 2.5 (Fidget1), Hit 1.3 (Wince1), Death 2.4 (Die1), Dead 1.0 |
| Roles | the cow never fights: attacks and cast play Fidget (as the fish) |
| Gait | stride 0.84 (walk), 1.85 (run) model units per cycle, from the hind hooves' planted speed (`scripts/gait_measure.py`) |
| Floor | ground rule with low-passed shifts (`scripts/floor_smooth.py`); `floor_audit.py --world mm9` Cow, Brown Cow ok |
| Meshy credits | **15** (backup account): Smart Topology 5, 4K retexture 10, no retries |

## Route

0. **HD masters** (`references_hd/`, Codex, two runs, brief `CODEX_BRIEF.md`): inputs are renders of the MM9 model and skin. Pose = the MM9 bind pose.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png`.
2. **Body clean, a new route.** The return is a skin with a second layer 0.5-6 mm under it (41 % of the cow's surface),
   joined at a few places; the front legs hang on that inner layer only. The wolf's voxel remesh made a hollow slab of it
   (1,000 bubbles, collapse decimation stalled at 23k triangles and threw spikes, QuadriFlow refused it) and deleting the
   inner layer cut the front legs off. `scripts/solid_grid.py`: every triangle rasterised into a 2 mm grid, walls dilated
   one voxel, the outside flood-filled, the rest solid, boundary written as a closed mesh. `scripts/finish_solid.py`:
   voxel remesh at 2.5 mm, smooth, shrink back onto the Meshy skin. Result: one closed manifold body of 200k quads
   (0 boundary, 0 non-manifold edges) with legs and tail; eyes, teats and tassel kept as returned.
3. **Fit** (`scripts/fit_quad.py`, from the wolf): global ICP, head ICP with a blend in model units (900 diffusion
   passes; the wolf's 8 rings are 3 mm on this density and tore the nape), legs by transient skinning; the tail is
   labelled, not moved (`FIT_SKIP`).
4. **Weights** (`scripts/rig_body.py`), **reduce** (`scripts/reduce_mod.py`: Decimate modifier, vertices snapped back
   onto the dense skin), **symmetrize** (`scripts/symmetrize.py`), **despike** (`scripts/despike.py`: sharp ticks; the
   pointed poll compressed).
5. **Mouth** (`scripts/mouth.py`): MM9 opens the jaw up to 22 deg, also while chewing in Stand. The muzzle is deepened
   (the Meshy wedge was too pointed for cattle), the lip line cut on a plane read off the bind pose, the lower jaw
   re-weighted, and a cavity of 4 rings behind the slit: roof, floor with a tongue rise, throat cap, hinged at the corners,
   skinned between `Xhead` and `Xjawpiv`. Palate ridges, gums, tongue, lower incisors (cattle have no upper ones) and the
   dark throat are painted (`compose_common.paint_cavity`); no tooth geometry.
6. **UVs** `scripts/uv_atlas_v1.py` (`claude_shared/uv_atlas.py`), **4K retexture** from 01/03/02/04, colour 4K -> 2K once.
7. **Weight refinement after the UVs** (no paint change): `refine_weights.py` (wolf: Gaussian smoothing, midline fade),
   `weights_v2.py`: only the tail tube follows the tail bones (nearest-MM9 labels gave them the rear of the rump: the
   gallop's tail flick raised it as a sheet), limb roots fade to the spine above the mid thigh, no limb share on the
   belly (torn hem in the gallop), hooves rigid on the foot bones, udder and teats on `XbackC`.
8. **Textures** (`scripts/compose_cow.py`, gentle grade). Regions: R white hide, G black hide (Otsu on the paint's
   luminance, soft), B udder and inner ears, A muzzle; hooves, eyes and cavity keep the base colour. The shader mixes
   channels in turn, so two soft neighbours leak the base between them: the mask's R covers all skin and the others lie
   over it, while ramps are fitted on each region's own texels. Brown Cow: COWBROWN has no patches, so R and G map to its
   plain coat, the white hide to the upper and the black to the lower palette half, meeting at the middle (no contour at
   the old patch borders). The white hide is capped under albedo 243 in tier A. Fit errors `textures/cow_ramps.json`.
9. **Clips** (`scripts/clips_mm9.py`): MM9 keys through PCHIP at 30 fps, loop seams closed (Walk 8.7 deg, Run 6.5,
   Stand 0.5). Jaw on the keys: `a' = soft_max(0, a)` (MM9 closes it 3-8 deg past the bind in some clips, which would push
   the lower lip through the upper one).
10. **Runtime** `scripts/build_runtime.sh`: prepare, LODs, shadow shrink, tier skins, `floor_smooth.py`, winding.
    `floor_fix.py`'s `--ground-loop`/`--raise` were not used: they shift the root per key by the lowest point.

## Rebuild

```sh
T=<lease token>; P=level_generation/creatures/mm9_cow_claude; B="tools/run_creature_blender.sh --token $T"
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # numpy, scipy, pygltflib
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
$V $C $M/COW.abc $P/source/cow --id cow --texture 0=$S/COW.dtx --scale 0.0256      # also cowbrown (COWBROWN.dtx)
$B $P/scripts/mm9_rig_source.py $P/source/cow/cow.glb $P/work/mm9_cow_rig.blend 0 0.7811
$V $P/scripts/solid_grid.py $P/meshy/cow_smart_v1/model_urls_glb.glb $P/work/cow_solid_grid.obj 0.002 1
$B $P/scripts/finish_solid.py $P/work/cow_solid_grid.obj $P/meshy/cow_smart_v1/model_urls_glb.glb $P/work/cow_clean_v5.glb 0.0025 8 1
HEAD_DIFFUSE=900 POSE_SIGMA=0.12 $B $P/scripts/fit_quad.py $P/work/mm9_cow_rig.blend $P/work/cow_clean_v5.glb $P/work/fit_v6.blend $P/work/fit_v6.json
RIG_DIFFUSE=200 RIG_HINGE=20 $B $P/scripts/rig_body.py $P/work/fit_v6.blend $P/work/rig_v6.blend $P/work/rig_v6.json
$B $P/scripts/reduce_mod.py $P/work/rig_v6.blend $P/work/reduced_v6.blend $P/work/reduced_v6.json 7000 0.2
$B $P/scripts/symmetrize.py $P/work/reduced_v6.blend $P/work/sym_v6.blend $P/work/sym_v6.json -X
# despike + mouth: scripts/rebuild_mouth.sh (env per animal, the goat's line included)
$B $P/scripts/uv_atlas_v1.py $P/work/mouth_v6.blend $P/work/uv_v1.blend $P/texturing/cow_body_upload.glb $P/work/uv_v1.json
# xatlas packs differently per run: never re-run once the upload went to Meshy (retexture_v1 is on this layout)
export HEAD_GROUPS=Xheadpiv,Xhead,Xjawpiv,Xearpiv,Xearpiv01 JAW_GROUPS=Xjawpiv
ATTRS=cav_t,cav_low,cav_x $B $P/scripts/dump_uv3d.py $P/work/uv_v1.blend $P/work/uv3d_cow.npz Body
$B $P/scripts/dump_uv3d.py $P/source/cow/cow.glb $P/work/uv3d_mm9_cow.npz d_cow.mesh:1 d_ear.mesh:1 d_ear01.mesh:1 d_tail.mesh:1
$B $P/scripts/bake_ao.py $P/work/uv_v1.blend Body $PWD/$P/textures/cow_ao_2k.png 0.1 2048
python3 $P/scripts/compose_cow.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/cow_ao_2k.png --fine 1.0 \
  --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/cow_basecolor.png && python3 $P/scripts/compose_cow.py
scripts/rebuild_tail.sh cow --install      # refine_weights, weights_v2, build_export, build_runtime
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 $P/scripts/bind_actors.py mm9_cow_claude $P/work/actors_block.yml
(cd $P && python3 scripts/viewer_tiers.py && python3 scripts/make_viewer_manifest.py r5_cow_20261030 \
  "cow_a=Cow (Cow A)=review/viewer/cow_a.glb" "cow_b=Brown Cow (Cow B)=review/viewer/cow_b.glb")
python3 $P/scripts/sheets.py cow compare; python3 $P/scripts/sheets.py cow angles; python3 $P/scripts/sheets.py cow texture
```

## Checks (2026-10-30)

Sheets are review-viewer shots (the MM9 row of the comparison is a Blender render of the MM9 reference):
`review/sheet_mm9_vs_ours.png`, `review/sheet_angles_cow_a.png`, `sheet_angles_cow_b.png` (side, front, 3/4, rear,
below x Standing, Walking, Fidget), `review/sheet_texture_cow_a.png`, `sheet_texture_cow_b.png`.

| Gate | Result |
|---|---|
| Symmetry | MM9 mirror distance mean 13 mm, about its 5 mm off-centre mid plane; ours exact about that plane (`symmetrize.py`, right half kept) |
| Orientation | `scripts/head_gate.py` (`review/head_gate.json`), full head orientation vs MM9, max per clip: Standing 6.4, Walking 2.5, Running 5.9, Fidget 6.8, Hit 5.8, Death 14.9 deg. Hooves 0-1 deg in Standing, Fidget, Hit; 7-23 in Walking, Running, Death (mid-swing, PCHIP against MM9's linear keys and the closed seams) |
| Head shape | cattle proportions after the muzzle deepening; shorter than MM9's by 7 cm |
| Attachment | `detached_parts_audit.py` 0 detached in every clip (shallow root note on the tassel, 6.7 mm, Death) |
| Folds | `scripts/fold_measure.py`, outside the head (the closed cavity counts as folded): worst frame Standing 9, Fidget 10, Hit 17, Walking 30, Running 40, Death/Dead 89 (legs folded on the corpse) |
| Mouth | cavity 682 tris, hinged at the corners, no piercing teeth (none modelled) |
| Shading | `flat_shading_check.py` flat 0.02 |
| Textures | `texture_quality.py`: atlas 59.9 %, spread 1.19, fragments 0.1 %, stretch p90 1.08, 2K from a 4K paint |
| Deformation | `scripts/gates.py`: loop seams 0; edge ratio p1/p99 per clip 0.60-0.83 / 1.24-2.15 |
| Floor | `floor_audit.py --world mm9`: Cow, Brown Cow ok |
| Viewer | `tools/run_creature_review.py check`: 2 tiers, 7 clips, 0 console errors; playback in `review/playback/` |
| Winding, regression | `check_winding.py` 0 inverted; `mm9_actor_models_build_every_binding` 65 descriptors on 31 models, 0 failed |

## Deviations and open points

- Solid-grid body clean instead of the wolf's voxel clean (see Route 2).
- The hoof is one piece with a painted cleft (the voxel surface smooths the Meshy cleft).
- The head is smaller than MM9's and the MM9 jaw pivot sits below our chin.
- Hooves in the swing phase differ from MM9 by up to 23 deg (PCHIP through the same keys, not MM9's linear segments).
- Brown Cow: faint darker areas remain where the black patches were, read as coat shading; small pale flecks at the
  fetlocks. The udder is paler than COWBROWN's.
- `cow.scr` tips over when used (Tipover1/2, Standup1/2) and these clips are not exported: the engine has no role for
  them. Fidget2/3, Wince2, Die2 are unused too. MM9 `Velocity` events are not reproduced (clips stay in place).
- The generator gives these rows `Stationary / Aggress`; a wander/flee behaviour is not part of this model work.
- No in-game run: viewer, floor audit and regression only.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_cow_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_cow_reduce_claude/before/`.

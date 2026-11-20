# MM9 sheep (mm9_sheep) — 3D model, 2026-10-30

The MM9 sheep (`mm9/extracted/MODELS/MODELS/SHEEP.abc`, 36 nodes, 387 tris, 12 clips) for Ewe (MONSTERS.txt row 272, skin
SHEEP1.dtx), Bori (258) and Ratatosk (259, basemelee.scr: it fights). On the MM9 rig-reuse route of `../mm9_wolf_claude/`:
a new HD Meshy sheep weighted to the original MM9 skeleton, the MM9 clips played with the listed fixes. The ram
(`../mm9_ram_claude/`) reuses this body. Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_sheep.glb` (cooked copy in `assets_dev`), skin `sheep_a` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_sheep_claude`: MM9 272 Ewe, 258 Bori, 259 Ratatosk, scale 100 (100 x `Scale` 1) |
| Descriptors | NPC rows in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, fallback visual zdog A (469) |
| Triangles LOD0/1/2/3 | 6,370 / 3,184 / 1,146 / 382 (mouth cavity 396 of LOD0) |
| Skeleton | the MM9 one, names unchanged (`XCENTER`, `XbackA/B/C`, `Xback`, neck `Xneckbase/piv`, `Xneck`, head `Xheadpiv`, `Xhead`, `Xjawpiv`, ears `Xearpiv-Xear` (+01), legs `Xflegpiv-Xfleg-Xfankle-Xffoot`, `Xblegpiv-Xbleg-Xblegmid-Xbankle-Xbfoot` (+01 = +X = the sheep's left), `Xtail`) |
| Clips (60 fps) | Standing 1.3 (stand), Walking 1.0 (walk), Running 0.3 (run), Fidget 2.0 (fidget1, grazing), AttackMelee 0.5 (Hattack1, head butt), Hit 0.6 (wince1), Death 1.6 (die1), Dead 1.0 |
| Events | contact 0.244 s (MM9 `Rattack` of Hattack1); `attack_ranged` and `cast` play AttackMelee (no row casts) |
| Gait | stride 0.40 (walk), 0.97 (run) model units per cycle (`scripts/gait_measure.py`) |
| Floor | ground rule; floor correction low-passed (`scripts/smooth_floor.py`); `floor_audit.py --world mm9` ok |
| Meshy credits | **25 / 40** (backup account): Smart Topology 5, 4K retexture v1 10 (layout 50 %, superseded), 4K retexture v2 10 |

## Decisions

- **Blank skin (Bori, Ratatosk).** MM9 has no `SHEEP.dtx`, ABC v13 stores no skin name, and the object class has no Skin
  property: `models\sheep.abc` is the class's default Filename in the DATs (RedWolf and DwarvenMiner objects carry it
  too), so these two rows are peasant-template rows (`BaseName PeasantMale`) left on the placeholder model. No MM9 asset
  names their look; they use SHEEP1, the sheep's first skin, the same as the Ewe. MM9 itself would draw them untextured.
- **Setup-pose offsets removed from the clips.** Every SHEEP.abc clip keeps the same translations against the setup pose
  (`sheepsetup01`), which the mesh and the HD masters follow: the jaw 5 cm into the skull, the front leg root and the hind
  pivot 11 cm up (compensated further down each leg), the ears 1.4 cm off, the tail 5.6 cm off. MM9's rigid skin shows this
  as the V-shaped belly crease and pointed muzzle of `work/offsets_sheet.png`; on a smooth skin it folded the flank. The
  exactly constant part goes in `scripts/mm9_rig_source.py`, the near-constant part (`SETUP_BONES`, mean over
  stand/walk/run) in `scripts/clips_mm9.py`; all rotations and the animated part of the translations stay. Feet land
  1-3 cm from MM9's, the floor pass absorbs the height.
- **Mouth.** MM9 opens the jaw 1.5 cm at the chin in walk, 2 cm in fidget1, 1.6 cm in die1 (3.7 in die2, unused). The Meshy
  head is one shell and nearest-MM9 labels put `Xjawpiv` on the throat. `scripts/mouth.py`: the slit is bisected on the
  dense mesh along the lip plane with the corners left joined (the hinge), the jaw weights are set by position (fading out
  at the jaw angle; the throat's old jaw weight moved to `Xheadpiv`), and after reduction a cavity is extruded from the lip
  loop: a rolled lip, a palate, a floor with a tongue ridge, closed at the throat. No teeth (a closed ewe's mouth shows
  none; lower incisors are not modelled).
- **Eyes.** Meshy's own eye pieces were blobs with threads; clean eyeballs sat near the ear, far behind where Meshy painted
  the eye with lids, so all separate pieces were dropped and the eye is the painted surface. The second paint's iris came
  out grey: `compose_sheep.py` finds its pupil and tints the iris amber (luminance kept).
- **Clean body.** Voxel clean as on the wolf, but the holes had to be filled first, or Blender's remesher builds a hollow
  double shell (261k against 165k quads). A 0.5-unit thread from chin to hoof is removed by edge length.
- **Symmetry.** MM9's body is near mirror-symmetric (mean 3 mm). Ours is mirrored exactly after fitting and again after
  reduction (`scripts/symmetrize.py`, `sym_reduced.py`), L/R groups swapped.
- **Tiers.** One ramp set here (`sheep_a`, identity); region mask R wool, G head skin, B pink (inner ears, nose), A legs,
  so the ram (SHEEP2.dtx) shares these textures through its own ramps (`../mm9_ram_claude/textures/ram_ramps.json`).
  Hooves, eyes and the mouth are out of the mask. Tier-A ramp errors 1.4-2.4 levels.
- **Skin alpha, glow:** SHEEP1/2 are opaque, `Transparent 0`, no FX: nothing to carry over.

## Rebuild

```sh
. work/lease.env; B="scripts/bl.sh $SHEEP_T"; P=level_generation/creatures/mm9_sheep_claude   # paths from the repo root
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python; M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS
$V tools/mm9_import_discovery/convert_abc_model.py $M/SHEEP.abc $P/source/sheep1 --id sheep1 --texture 0=$S/SHEEP1.dtx --scale 0.0256   # also sheep2
$B $P/scripts/mm9_rig_source.py $P/source/sheep1/sheep1.glb $P/work/mm9_sheep_rig.blend 0 0.4907
CLEAN_MODE=none $B $P/scripts/clean_meshy.py $P/meshy/sheep_smart_v1/model_urls_glb.glb $P/work/clean_v1.glb 0.003 0
$B $P/scripts/fit_quad.py $P/work/mm9_sheep_rig.blend $P/work/clean_v1.glb $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/tail_fit.py $P/work/fit_v1.blend $P/work/fit_v1t.blend $P/work/tail_v1.json
$B $P/scripts/symmetrize.py $P/work/fit_v1t.blend $P/work/fit_v1s.blend $P/work/sym_v1.json
RIG_DIFFUSE=120 RIG_HINGE=20 $B $P/scripts/rig_body.py $P/work/fit_v1s.blend $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/eyes.py $P/work/rig_v1.blend $P/work/rig_v1e.blend          # removed again by remove_eyes.py below
MODE=cut $B $P/scripts/mouth.py $P/work/rig_v1e.blend $P/work/rig_v1m.blend $P/work/mouth_cut_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_v1m.blend $P/work/reduced_v4.blend $P/work/reduced_v4.json 0.014 1.0 0.08
$B $P/scripts/sym_reduced.py $P/work/reduced_v4.blend $P/work/sym_v4.blend
MODE=cavity $B $P/scripts/mouth.py $P/work/sym_v4.blend $P/work/mouth_v4.blend $P/work/mouth_v4.json
$B $P/scripts/uv_atlas_sheep.py $P/work/mouth_v4.blend $P/work/uv_v4.blend $P/texturing/sheep_body_upload_v1.glb $P/work/uv_v4.json
$B $P/scripts/remove_eyes.py $P/work/uv_v4.blend $P/work/uv_v5.blend
$B $P/scripts/uv_atlas_sheep.py $P/work/uv_v5.blend $P/work/uv_v6.blend $P/texturing/sheep_body_upload_v2.glb $P/work/uv_v6.json max_cost=0.8 merge_below=20
# xatlas packs differently per run: never re-run after the upload went to Meshy (retexture_v2 belongs to uv_v6)
$B $P/scripts/rigid_hooves.py $P/work/uv_v6.blend $P/work/uv_v7.blend
$B $P/scripts/straighten_hooves.py $P/work/uv_v7.blend $P/work/hoof_p1.blend -11 -16
$B $P/scripts/straighten_hooves.py $P/work/hoof_p1.blend $P/work/uv_v8.blend 0 0
export HEAD_GROUPS=Xheadpiv,Xhead,Xjawpiv,Xearpiv,Xear,Xearpiv01,Xear01 JAW_GROUPS=Xjawpiv
$B $P/scripts/dump_uv3d.py $P/work/uv_v6.blend $P/work/uv3d_sheep.npz Body
$B $P/scripts/dump_uv3d.py $P/work/mm9_sheep_rig.blend $P/work/uv3d_mm9_sheep.npz body.mesh:1 ear.mesh:1 ear1.mesh:1 tail.mesh:1
$B $P/scripts/bake_ao.py $P/work/uv_v6.blend Body $PWD/$P/textures/sheep_ao_2k.png 0.06 2048
(cd $P; python3 scripts/compose_sheep.py && python3 ../claude_shared/grade_basecolor.py --ao textures/sheep_ao_2k.png --fine 1.0 \
  --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/sheep_basecolor.png && python3 scripts/compose_sheep.py)
$B $P/scripts/refine_weights.py $P/work/uv_v8.blend $P/work/uv_v9.blend $P/work/refine_v9.json
$P/scripts/rebuild_export.sh uv_v9.blend v9       # export, runtime (LODs, ramps, floor, smoothing), viewer, check
python3 tools/install_model.py $P/export/mm9_sheep.glb --world mm9
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 $P/scripts/bind_actors.py mm9_sheep_claude $P/work/actors_block.yml
```

## Symmetry and hooves (user review, 2026-10-30)

"Neither are symmetrical in front pose, feet angled a bit." Measured (`scripts/symmetry_gate.py`, `stance_gate.py`,
`hoof_axes.py`; `review/stance.txt`; sheet `review/symmetry_hooves_viewer.png`, viewer shots):
- **Symmetry is MM9's clip, not the mesh.** Bind: ours mirror mean 0.0 mm, max 3.7 mm (MM9 4.3 / 19 mm). Standing: ours
  14-18 mm, MM9's own mesh 33-34 mm. MM9's `stand` rolls the head +6.7 to +8.6 deg, swings it -2 to +4 deg and shifts it 8 mm;
  ours is within 0.1 deg of that per bone. XCENTER and Xback stay at 0, so the body is straight. The clip is kept. The head
  turn is the same clip the ram shows with horns, which makes it more visible. MM9's own skeleton is 8 mm wider on -X at the
  feet (bones kept).
- **Hooves were ours.** The bind hooves came from Meshy and the limb fit: hind toes 18 deg outward, front 11 deg outward once
  levelled, soles tilted up to 10 deg. MM9's point straight forward with level soles. `scripts/straighten_hooves.py` turns
  each hoof rigidly about its centroid (twice, the second pass levels what the first left) on a ramp up the pastern, on
  uv_v7 -> uv_v8: same topology, UVs and weights, no repaint. After: yaw front +-3, hind 0 deg, sole tilt 1.3 deg or less,
  mesh still mirror-exact. Bones say the clip does not turn the feet in Standing, ours or MM9's (0.0 deg).
- **Running / AttackMelee hoof mismatch** was a separate cause: the 30 fps bake between MM9's keys. See Checks.

## Running fold fix (user review, 2026-10-30)

"Running frame 10, some deformation on the belly": a sharp crease and step where the thigh meets the flank, a chest lobe
at the elbow. MM9's mesh at the same frame stays compact (its rigid skin shows hard facets, no fold). Cause: the nearest-MM9
weights gave the hind pivot the flank and belly (24 % each side at mid-belly) and left about 10 % of `Xfleg` (swings up to 98
deg) on the chest. `scripts/refine_weights.py` + `weight_refine.py` (from the wolf, on uv_v8 -> uv_v9, positions, UVs and clips
unchanged): Gaussian smoothing (sigma 0.08) of the torso with no mixing between limbs, then lower-leg weight moved to the
leg's root pivot, the roots faded towards the midline (|x| 0.07-0.15), along the body (hind gone by y 0.14, front by y 0.04)
and above the pivots (front z 0.30-0.40, hind 0.46-0.64), and the spine share smoothed (sigma 0.11) so the belly has no step
at the spine split. The right half mirrors the left exactly (L/R bones swapped). The wolf's untangle is not used: the rest mesh
has no folds outside the cavity.

Fold-over face-frames at 48 fps, before -> after (Running / AttackMelee, max per frame in parentheses):
- outer flank (one side, `|x|` > 0.12): 33 (8) -> 3 (1) / 56 (9) -> 9 (1);
- whole front half: 46 (12) -> 37 (4) / 255 (29) -> 171 (14);
- whole hind half: 101 (17) -> 139 (21) / 210 (28) -> 350 (39): the bend now lands on the inner groin and lower leg, between
  the thighs, instead of the flank. Not seen in the shots; the fold is hidden, not gone.
Sheet: `review/running_folds_viewer.png` (Running frames 5, 10, 15, 20 side and 3/4, wrapped at the 14.4-frame loop, plus 12 and
AttackMelee 12). Before: `review/run_before/`.

## Checks (2026-10-30)

- Viewer `review/viewer/` (own framing for this size; the `¾ back` button is a from-below view): `run_creature_review.py check`
  1 skin x 8 clips, 0 console errors; every clip recorded in `review/playback/` at 1x and 0.5x. Sheets from viewer shots:
  `review/acceptance_viewer_sheet.png` (24 shots), `review/mm9_vs_ours_viewer.png`, `review/tiers_viewer.png`,
  `review/texture_closeup_viewer.png`. The MM9 row of the comparison is a Blender render of the untouched clips.
- `texture_quality.py`: atlas 60.1 %, equivalent 1,588 px, density p10/p50/p90 1399/1440/1512, spread 1.08, 44 islands,
  fragments 0 %, stretch p90 1.10; 4K paint downsampled once. (First layout: atlas 50.2 %, so it was re-laid and repainted.)
- `flat_shading_check.py` 0.00 flat. `detached_parts_audit.py` 1 component, 0 detached in any clip. Winding 0 inverted.
- Symmetry: exact mirror at x = 0 before the cavity (MM9 mean 3 mm). Head shape: a real sheep's convex profile, no change.
- Orientation (`scripts/orient_gate.py`, `review/orient.json`) at MM9's key times, full rotation against MM9's rigid
  mesh: skull 0.4-2.4 deg, hooves 0.2-2.1 deg, Running 6.0 (0.3 s loop, keys 37 ms apart). The bake is 60 fps because 30 fps
  sampled between MM9's keys (Running 16.2 -> 6.0, AttackMelee 8.4 -> 2.1). Skull fold 0.4-2.5.
- Deformation (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 per clip 0.52-0.72 / 1.2-2.8.
  Fold-over face-frames outside the mouth (the cavity folds by construction): 5,601 over all clips at 48 fps.
- Floor correction per frame (`scripts/root_jitter.py`): Walking 1.1 -> 0.25 cm, Running 2.5 -> 0.33 cm, AttackMelee 2.65 -> 1.41 cm (sampled at 30 Hz).
- Floor audit Ewe/Bori/Ratatosk ok. Regression `mm9_actor_models_build_every_binding`: 61 descriptors on 28 models, 0 failed.
- No in-game run (optional in the brief).

## Deviations and open points

- Clips carry the setup-offset removal above, so bodies differ from MM9's clip poses by design (no belly crease, no tucked
  jaw) and hoof paths by 1-3 cm.
- Unused MM9 clips: fidget2, Hattack2, wince2, die2. `lunge` and sound events are not reproduced (clips stay in place).
- Walking floats up to 1.8 world units at keys where MM9's hooves all clear the floor (smoothing keeps the upper envelope).
- Fallback visual (zdog) has height 40 / radius 64: smaller than the model if collision uses it.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_sheep_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_sheep_reduce_claude/before/`.

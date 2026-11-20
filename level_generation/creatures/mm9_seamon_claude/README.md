# MM9 Sea Monster family (mm9_seamon) — 3D model, 2026-10-30

The amphibious sea predator of MM9 (`mm9/extracted/MODELS/MODELS/SEAMONSTER.abc`: horizontal body, toothy fish head,
dorsal sail, long tail with a forked fin, two clawed arms and two webbed hind legs; 32 joints, 718 triangles, about
7.4 m long) for the MM9 world, built on the MM9 rig-reuse route of `../mm9_dfly_claude/` and `../mm9_lobber_claude/`.
Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Descriptors / skins | MM9 Sea Monster A `sea_a` (Sea Monster Male, row 177, SeaCreatureF.dtx), B `sea_b` (Sea Monster Female, row 178, SeaCreatureM.dtx; MONSTERS.txt names the skins crosswise, kept as listed) |
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_seamon.glb` (cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`: A scale 100 (= MM9 size), B scale 120 (MONSTERS.txt `Scale` 1.2) |
| Triangles LOD0/1/2/3 | 6,843 / 3,420 / 1,203 / 382 (after the 2026-10-30 mouth rebuild and fin rooting; was 7,141 / 3,570 / 1,255 / 398) |
| Clips (30 fps) | Standing 1.33 (standwater), Walking 1.33 (swim; also the run: RunVelocity = WalkVelocity), Fidget 1.43 (fidgetwater1), AttackMelee 1.6 (Hattackwater1), AttackRanged 1.4 (Hattackwater2), Hit 1.2 (wincewater1), Death 1.37 (diewater2 convulsion + sprawl), Dead 1.0 |
| Events | attack_melee impact 0.480 s (MM9 `bite`), attack_ranged impact 0.666 s (MM9 `Rattack; Lattack`, a claw strike); no missile |
| Floor | swimmer rule since 2026-11-04 (Fly `S`): MM9's origin at the centre of the MM9 body box, +0.896 m on every living clip, MM9's motion unchanged; Death eases into the corpse on the floor ("Binding: a swimmer"). Before it ground rules: Standing and Walking ground-looped, Fidget/attacks/Hit raised |
| Meshy credits | **25 / 35** (Smart Topology 5, retexture 10, 4K retexture on the xatlas UVs 10 (2026-10-30); backup account) |

## Decisions

- **A water monster without water** (superseded 2026-11-04 by "Binding: a swimmer"). The engine had no swimming, and MM9 data gives the Sea Monster
  Fly 0 (`BaseSwim.scr`), so it is an ordinary ground actor; it is not a `Swimmer` (MonsterKind::Swimmer comes only
  from the MMerge bolster table, and only lets a walker move onto water tiles). Its only placements are two in the
  Wizard's Lab pool (`wizardslab.odm`, z -901). The water clips map as: standwater (treading water, limbs hanging) =
  Standing, standing on its claw tips; swim (limbs swept back) = Walking, the body low over the floor; the lunging
  attacks and the wince keep their authored motion and are raised wherever a limb would go under the floor (the body
  lifts during the lunge). A water surface actor (body at the waterline, limbs under it) would need engine support.
- **Death.** diewater2 is a sinking death that ends hanging head-up with limbs and tail dangling (on a floor it would
  stand on its tail). Death keeps its first 0.45 s (the convulsion), then goes limp over 0.9 s into the swim start pose
  rolled 30 degrees onto its side; the floor pass lowers it onto the floor. Unused MM9 clips: diewater1, fidgetwater2
  (8 s), wincewater2, Jump, static_model.

## Route

0. **HD masters** (`references_hd/`, Codex via `claude_shared/codex_slot.sh`, two runs, 1536x1024): MM9 renders of the
   row-177 model (`mm9_views_tier1.png`), skin x4, top view; `CODEX_BRIEF.md`, `generation_runs.json`,
   `selected_views_review.png`. Gate: likeness good; the far hind foot is hidden behind the tail in 00, claw counts
   vary between views (Codex note), front view shows a third sail point.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png`: one body with all limbs, sail and spines as pieces, and a
   fan of thread triangles between the hidden far hind leg and the tail.
2. **Fit** (`scripts/fit_sea.py`): threads deleted (faces with an edge over 12x the median), holes filled; uniform
   scale + translation by ICP; tail, both legs and both arms posed onto their MM9 chains by per-segment skinning.
   `work/fit_sheet.png`.
3. **Weights** (`scripts/rig_body.py sea`): nearest MM9 vertex label per chain, head/jaw held during diffusion, teeth
   and tail spines rigid with their nearest body vertex, the sail weighted to the MM9 fin bones.
   `work/rigclose_sheet.png`.
4. **Reduce** (`scripts/reduce_body.py 0.4 0.5 0.55`), **UV** (`scripts/uv_export.py sea`, head islands x1.8; since
   2026-10-30 replaced by the head symmetrization, mouth rebuild, xatlas UVs and a 4K retexture, "Mouth rebuild"),
   **retexture** from 01/03/02/04 (`requests/sea_retexture_v1.json`).
5. **Clips** (`scripts/clips_mm9.py` SEA via `scripts/build_export.py`): PCHIP resampling, loop seams closed, Death as
   above, Dead = last pose.
6. **Textures** (`scripts/compose_sea.py`): 2K graded base, 1K normal, 1K ORM; structural regions R body scales,
   G belly (bind normal facing down), B fins (sail, tail spines, tail fin), A hands/claws and teeth. Every tier, A
   included (the retexture came out cyan; MM9 A is navy), takes hue per luminance band from its MM9 skin projected
   onto our texels through the fitted bind pose. `review/sea_texture_classes_tiers.png`, `work/tiers_sheet.png`.
7. **Runtime** (`scripts/build_runtime.sh [--install]`): prepare -> LODs -> shadow shrink -> `region_variants.py` ->
   floor pass (ground rules) -> winding check (0 inverted).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_seamon_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
for t in M F; do $V $C $M/SEAMONSTER.abc $P/source/sea$t --id sea$t --texture 0=$S/SEACREATURE$t.dtx --scale 0.0256; done
$B $P/scripts/mm9_rig_source.py $P/source/seaF/seaF.glb $P/work/mm9_sea.blend 0 0
$B $P/scripts/fit_sea.py $P/work/mm9_sea.blend $P/meshy/sea_smart_v1/model_urls_glb.glb $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_body.py $P/work/fit_v1.blend sea $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.4 0.5 0.55
$B $P/scripts/uv_export.py $P/work/reduced_v1.blend sea $P/work/uv_v1.blend $P/texturing/sea_body_upload.glb
# (retexture_v1 was made on this upload)
# mouth rebuild and texture quality pass (2026-10-30, see "Mouth rebuild" below)
$B $P/scripts/symmetrize_head.py $P/work/uv_v1.blend $P/work/sym_v1.blend $P/work/sym_v1.json
$B $P/scripts/mouth_rebuild.py $P/work/sym_v1.blend $P/work/mouth_v1.blend $P/work/mouth_v1.json
$B $P/scripts/uv_atlas_v2.py $P/work/mouth_v1.blend $P/work/uvx_v2.blend $P/texturing/sea_body_upload_v2.glb $P/work/uvx_v2.json
#   xatlas packs a little differently per run: never re-run this once the upload went to Meshy (retexture_v2 is on it)
python3 tools/creature_meshy.py --project $P --token $T submit --job sea_retexture_v2 --kind retexture \
  --request requests/sea_retexture_v2.json --credits 10      # 4K; then poll / download
$B $P/scripts/root_fins.py $P/work/uvx_v2.blend $P/work/fins_v2.blend $P/work/fins_v2.json
$B $P/scripts/remove_shards.py $P/work/fins_v2.blend $P/work/shards_v2.blend $P/work/shards_v2.json
$B $P/scripts/bake_ao.py $P/work/shards_v2.blend Body $PWD/$P/textures/sea_ao_2k.png 0.05 2048
for s in Bone05,Bone34,Bone35,Bone37:sea Bone19,Bone30,Bone18,Bone29:sea_claws Eye:sea_eye Mouth:sea_mouth \
         MouthCos:sea_mcos MouthSin:sea_msin MouthV:sea_mv; do
  DUMP_GROUPS=${s%%:*} $B $P/scripts/dump_uv3d.py $P/work/shards_v2.blend $P/work/uv3d_${s##*:}.npz Body; done
$B $P/scripts/dump_uv3d.py $P/source/seaF/seaF.glb $P/work/uv3d_mm9_sea.npz "sea monster.mesh:1"
python3 $P/scripts/compose_sea.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/sea_ao_2k.png \
  --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/sea_basecolor.png \
  && python3 $P/scripts/compose_sea.py
$B $P/scripts/build_export.py $P/work/shards_v2.blend $P/work/anim_v5.blend $P/export/mm9_seamon_lod0.glb $P/work/clips_v5.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
python3 $P/scripts/viewer_tiers.py sea && python3 $P/scripts/make_viewer_manifest.py r5_seamon_shards_20261030 \
  "sea_a=Sea Monster Male (A)=$P/review/viewer/sea_a.glb" "sea_b=Sea Monster Female (B)=$P/review/viewer/sea_b.glb"
# mouth gates (all clips at 48 fps) and close-ups; before = work/before/ (the r1 export, its textures and tier GLBs),
# work/before_texpass/ (mouth rebuild on the r1 paint)
$B $P/scripts/mouth_gates.py $PWD/$P/export/mm9_seamon_lod0.glb $PWD/$P/work/shards_v2.blend $PWD/$P/work/mouth/gates_final.json - $PWD/$P/work/mouth_v1.json
$B $P/scripts/fin_gates.py $PWD/$P/export/mm9_seamon.glb $PWD/$P/work/shards_v2.blend $PWD/$P/review/mouth_20261030/fin_gates_after.json
$B $P/scripts/mouth_views.py $PWD/$P/review/viewer/sea_a.glb $PWD/$P/work/mouth/sheet tex_a "closed_front:Standing@0.3:front,..." 640
python3 $P/scripts/mouth_sheet.py $P/review/mouth_20261030/before_after_A.png 380 closed_front,... "r1 (before)=...:before_a" ...
python3 level_generation/creatures/claude_shared/detached_parts_audit.py $P/export/mm9_seamon.glb
python3 level_generation/creatures/claude_shared/texture_quality.py $P/export/mm9_seamon.glb --by-bone
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (2 tiers x 8 clips): `run_creature_review.py check` 0 errors, 16 switches; shots
  `review/shots/`, `review/viewer_shots_sheet.png` (the viewer's fixed body framing crops this 7 m creature).
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0 / 1.3 mm; edge ratio p1/p99 0.62-0.75 / 1.7-2.5.
- Floor audit mm9: Sea Monster A/B ok (ground). Regression `mm9_actor_models_build_every_binding`: 48 descriptors on
  19 models, 0 failed. Winding 0 inverted.
- In game (Wizard's Lab via `goto 9071`, same private `--user-data` route as `../mm9_jelly_claude/`; tour
  `review/ingame_tour.yml`): `review/ingame_sheet.png` (the map's own Sea Monster Male and a spawned Female as 3D
  actors at the party, standing on their claws, biting), `review/ingame_sheet2.png`, `review/ingame_models_sheet.png`
  (static models in the pool: swimming, Death and the sprawled corpse). The pool is dark; close views are better in
  the viewer.

## Mouth rebuild (2026-10-30)

User review (viewer, Fidget frame 36 open, closed mouth): lower teeth through the snout and face when the mouth closes,
torn shards at the mouth corners and the right eye, a flat shiny stretched panel inside the open mouth.

Causes:
- **Wrong hinge.** MM9's jaw joint (Bone08, y -1.14, z 0.354) sits 0.4 m behind and 0.1 m below the corners of
  the Meshy mouth (y -1.55, z 0.45). Every clip closes the jaw 33-41 degrees from the bind (standwater 32.8-37.5,
  Hattackwater1 up to 40.65), so the front of our lower jaw and its teeth swung up through the snout (the tooth by the
  nose) and the jaw's rear end rose through the cheeks and eye sockets.
- **Meshy's right side of the head** (the far side in the three-quarter master) carried a fan of thread triangles from
  the eye socket down to the lower jaw (the shards at the hinge, 403 faces in loose pieces joined only at vertices,
  also two short ones on the left), a crumpled right eye without an eyeball, and only three upper teeth.
- **No mouth interior**: a shallow wedge, the floor a flat panel rising to the palate, its Meshy texels stretched up to
  20x (texel stretch against the head skin) when the jaw opened.
- **Texture** (blotchy, soft): 2K Meshy paint on a Smart UV Project layout using 29 % of the atlas, 820 islands,
  7.2 % of the surface on fragments (each painted as its own blotch), then a strong grade.

Fixes (README "Rebuild"):
- `scripts/symmetrize_head.py`: loose thread pieces removed; the head in front of y = -1.38 cut at its midplane
  (x 0.026) and the right half replaced by the mirror of the left (UVs and weights copied, side bones swapped), teeth
  and eyeball mirrored; the seam at y = -1.38 morphed onto the original right cross-section (at most 1.9 cm) and
  welded, seam slivers collapsed.
- `scripts/mouth_rebuild.py`: the mouth interior found by closing the jaw virtually and casting hemisphere rays
  (525 faces), deleted; one clean lip loop (49 vertices). **Bone08 moved to the mouth corners** (y -1.55, z 0.45;
  its rotations in every clip unchanged). Jaw weights rebuilt: below the plane bisecting the gape -> Bone08, above ->
  Bone07, 10 cm transition, faded out over 32 cm behind the hinge. The jaw closes until its teeth meet the upper lip
  at 54 degrees from the old bind, so it is pre-rotated 12.35 degrees closed: the clips' tightest bite (40.65) stops
  one degree short of contact; the lower teeth interlock in front of the upper lip. **Cavity** (393 triangles, rings
  49/49/49/25/17/14/9/9): lip roll, gum ring, palate and floor domes, a tongue in the lower half, a throat 10 cm
  behind the hinge; upper half on Bone07, lower half on Bone08 fading into the head toward the throat. Its paint
  parameters (u around the lip as the MouthCos/MouthSin groups, v lip -> throat as MouthV) survive any UV layout;
  `compose_sea.py` paints the lining per texel from them (dark lip edge, red-brown gums, MM9's olive-green palate with
  ridges and floor, a paler tongue with a groove, red-black throat; no tier region, so both tiers keep it; flat
  normal, roughness 0.45). 29 teeth seated a quarter of their length into
  the gum (moved 1.7 cm on average, 4 cm at most along their axes), rigid on Bone07 (18 upper) / Bone08 (11 lower).
  Eyeballs are in no tier region either and are repainted red from the paint's shading: both tiers keep MM9's red
  eyes (the r1 tier ramp painted them green, the 4K retexture blue-grey).
- **Texture quality pass** (`../claude_shared/TEXTURE_QUALITY_PASS.md`, after the last vertex move):
  `scripts/uv_atlas_v2.py` (xatlas charts, head x1.8, brute-force packing; a second run with max cost 4 packed only
  40 % and was discarded), 4K retexture `sea_retexture_v2` (10 credits, backup account) from the same HD masters on
  `texturing/sea_body_upload_v2.glb`, colour downsampled once to 2K, normal 1K, AO re-baked on the new layout, gentle
  grade (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`). Tier-A ramp errors stay under
  1 level per region (no region split needed).
- **Spines** (coordinator's detached-parts audit: one tail spine left the back by 5.1 cm in Hit): every spine vertex
  takes the weights of its nearest body vertex instead of one rigid vertex. `detached_parts_audit.py`: 41 components,
  0 detached in any pose (was 1, 50.7 mm).

Numbers (`scripts/mouth_gates.py`, LOD0, all 8 clips at 48 fps, 517 frames; `review/mouth_20261030/`):

| | before | after |
|---|---|---|
| lower teeth x upper exterior skin (triangle pairs, worst frame) | 50 | 0 |
| upper teeth x lower exterior skin | 128 | 0 |
| frames with any tooth through the opposite jaw | 384 / 517 | 0 / 517 |
| mouth lining x exterior skin | 374 | 0 |
| mouth interior edge stretch, posed / bind (max) | 10.0x | 1.79x |
| mouth texel stretch against the head skin (max / p99, any frame) | 20.4x / 4.0x | 2.35x / 1.57x (against the new, 2x denser head skin; worst lining triangle 172 texels/m, r1 head skin median 206) |
| corner slivers / torn edges within 15 cm of a corner (bind; worst frame) | 13; 107 | 8; 9 |
| lower x upper skin crossings behind the corners (worst frame) | 5 | 5 |

The remaining 8 corner slivers are cavity triangles deep in the corners at bind (aspect 13-40, edges 2-10 cm); the
5 skin crossings are folds of the cheek band behind the corners at full closure, as before.
Corner slivers and crossings are unchanged by the texture pass (same geometry). Triangles LOD0/1/2/3: 6,911 /
3,455 / 1,209 / 380. Flat shading 0.00, winding 0 inverted, floor audit ok,
`run_creature_review.py check` 0 errors (16 switches), regression `--world mm9 --headless-run-regression-suite
actors`: `mm9_actor_models_build_every_binding` PASS (r5: 50 descriptors on 21 models, 0 failed),
`detached_parts_audit.py` 0 detached.
Geometry-only before/after sheet (both tiers; closed front, closed side, Fidget 0.75 s front and low, bite side,
texture close-up): `review/mouth_20261030/mouth_before_after.png`.
Texture (`texture_quality.py`; `review/mouth_20261030/texture_quality_*.json`, density/stretch heatmaps `heat_*`
on one scale):

| | r1 | after |
|---|---|---|
| atlas use | 29.2 % | 42.9 % |
| equivalent texture side | 1,107 px | 1,341 px |
| density p10 / p50 / p90 (texels per creature size) | 1,420 / 1,614 / 2,944 | 1,814 / 1,914 / 3,417 |
| spread p90/p10 (head intentionally 1.8x) | 2.07 | 1.88 |
| islands; surface on fragments | 820; 7.2 % | 306; 1.3 % |
| UV stretch p90 | 1.42 | 1.15 |
| Meshy paint | 2K | 4K, downsampled once |

The atlas stays under the recipe's 55-60 %: the long limbs, sail, teeth and tail spines chart into thin strips.
Before/after sheets per tier (r1 / mouth rebuild / + texture pass): `review/mouth_20261030/before_after_A.png`,
`before_after_B.png`. Meshy credits: 10 (total 25 / 35).

### Eyes and tail fins (2026-10-30, user review of r3)

"Eyes not red", "fins are not attached to the tail".
- **Eyes.** The eyeball pieces sit deep in sockets; the 4K paint made each socket a pale blue-grey patch with only a
  thin red slit of eyeball showing, and the tier ramps kept it blue. `compose_sea.py` (`eye_fields`) now paints the
  eyeball and its socket skin out to 6.4 cm from the eyeball centre, by texel bind position in the eye's own frame:
  MM9's red eye (brighter toward the centre), a dark vertical pupil, a dark rim fading into the skin; those texels are
  in no tier region, so both tiers keep it. Front view: `review/mouth_20261030/eyes_front_before_after.png` (the user's
  screenshot, tier A, tier B, close-up).
- **Tail fins.** The seven dorsal fin plates behind the sail floated 6-23 cm above the tail in the bind pose already
  (fin gate: base edge up to 22.7 cm in Hit); one carried a thin Meshy spike down through the tail's flank.
  `scripts/root_fins.py` (after the UVs; translation only, so the retexture stays valid): side spikes dropped, each fin
  moved straight down by the base gap measured along its whole base edge (lowest vertex of every 2 cm slice in the
  lowest 35 % of its height, interpolated along the tail so the base follows the tail's curve) plus 3 cm, fin faces left
  entirely under the tail's top removed, every fin vertex weighted like its nearest tail vertex. `scripts/fin_gates.py`
  (same base-edge measure, bind and all clips at 48 fps): worst base gap per fin 0-22.7 cm before (6 of 7 fins over
  5.8 cm), 0.2 mm at most after; `review/mouth_20261030/fin_gates_*.json`, sheet `fins_before_after.png` (side,
  below, three-quarter at bind; side and below in Hit 0.27 s; side in Walking; the tail end in Hit). LOD0 6,846
  triangles (60 buried fin faces removed).
- Why `detached_parts_audit.py` passed them: a part counts as attached when a chain of touching parts reaches the body;
  the fin plates overlap end to end and the two front ones touch the back, so the whole row passed. Its gap is also a
  minimum over the part's vertices (one touching corner is enough).

### Stray polygons under the tail (2026-10-30, user review of r4)

Two flat two-sided shards hung under the tail (one by the hind legs at y 1.23, one mid-tail at y 2.0, both on the
right side; Meshy leftovers). MM9's tail has no ventral fins (only the dorsal ridge and the forked tail fin), so they
were removed: `scripts/remove_shards.py` (after `root_fins.py`; vertex merges only, UVs and paint stay valid) finds
flat faces under the tail with the test of `scripts/thin_probe.py` (inward ray meets the opposite surface within
1.2 cm), takes their tips (over 2x the tail's local radius from the bone chain, below it) and welds each tip onto its
neighbour nearest the chain. LOD0 6,843 triangles.

Accepted from the review viewer (`viewer_shots.mjs` with explicit cameras aimed at each site's posed position; the
wrapper's fixed views have no low angle): `review/mouth_20261030/shards_viewer_shots.png` (rear 3/4 from slightly
below, side, from below; Standing 0.3 s, Walking 0.5 s, Hit 0.27 s; the pre-fix model as a control, then tiers A and B)
and `shards_viewer_closeups.png` (0.85 m from each site, control and tier A). The control shows both shards in every
clip and view, so the cameras do reach them; the fixed model shows none.

Left as they are: a small darker smeared patch at each site, visible only close up (the surviving faces keep texels
that were painted for the flap), and a crease where the left arm bends into the body at the shoulder (a joint crease,
not a loose piece). The other thin clusters `thin_probe.py` lists were inspected in the viewer in Standing: hind foot,
front hands, forked tail fin and the back are clean. The sail, the mouth and eye rims and the faces over the rooted
fins are thin by construction.

## Binding: a swimmer (2026-11-04)

The engine swims since 2026-11-02 (`devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md`) and the rows' Fly cell is `S`
(`generate_mm9_monster_tables.py` SWIMMER_SOURCES): a Sea Monster that starts in a scene water volume flies in it,
bound to it (its body box's centre kept between bed and surface); out of water it would walk.

- **Clips.** The ground rules are gone: no claw-tip standing, no per-key grounding of the swim, no lunge lifts. The
  living clips (accepted and the script clips Fidget2, Hit2, Jump) carry one constant offset, **+0.896 m**: MM9's
  origin at the centre of MM9's body box (SEAMONSTER static_model Dims half-height 35 LT; heights 179 / 215 = 2 x 35 x
  2.56 x Scale 1 / 1.2, so the same 0.896 m in model space for both tiers), and MM9's motion as recorded. Death and
  Death2 ease from that lift into their corpses, grounded on the floor (`floor_fix.py --swim`; no floor clamp on the
  way, the death starts in the water); the corpse sinks to the bed. Rebuild: `scripts/build_runtime.sh` (accepted
  clips), then `scripts/extra_clips.sh` (its floor lines now `--swim 0.896 Death2 Dead2`; control clips match, 0 deg /
  0 cm; `graft_byte_check.py` OK). Pre-swim files in `work/before_swim/`.
- **What it looks like.** Treading water (standwater) its claws hang 0.75 m under the box and its head and sail rise
  1.9 m over the box centre, so held at the surface (the engine's clamp) the head, sail and back stand out of the
  water, as MM9's own placement at Isle of Ashes shows it (33 LT over the sea). Lunges reach up to 1.6 m under the box:
  into the seabed when it fights a party on the bed (MM9's body box does the same).
- **Placement.** `../../projects/mm9r_common/outdoor_blv.py` `swimmer_foot`: foot = MM9 position - height / 2, then
  lowered until the box is under the surface and kept over the seabed. Isle of Ashes' Sea Monster Male: README of
  `../../projects/mm9r_isleofashes_blv/`.
- **Checks.** `check_winding` 0 inverted; `floor_audit.py --world mm9` (kind `swimmer`) A/B ok; viewer revision
  `r6_seamon_swim_20261104`, `run_creature_review.py check` and `check_viewer.mjs` 24 switches, 0 errors.

## Deviations and open points

- Death is MM9's convulsion plus our sprawl (MM9's diewater ends hanging head-up, sinking).
- Meshy's hind feet are smaller than MM9's big webbed paddles; the hidden far hind leg needed the thread clean-up.
- The descriptor table gives height 179 / radius 192 (MM9's Dims rule, `mm9_monster_body_overrides.tsv`).
- User artistic acceptance: accepted 2026-10-30 ("sea monster ok"), pending removal of stray polygons under the tail.

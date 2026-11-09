# MM9 Greater Demon (mm9_greaterdemon) — 3D model, 2026-10-30

The winged MM9 Greater Demon (`mm9/extracted/MODELS/MODELS/STAGE2DEMON.abc`, 105 joints, 19 clips; skin
`GREATERDEMON.dtx`) for the MM9 world: MONSTERS.txt 242 "Greater Demon", descriptor `MM9 Demon B` (family `demon`
A/B in `tools/mm9_import_discovery/mm9_monster_families.yml`; A is the Lesser Demon, `stage1demon.abc`, a separate
body not built here). Built on the MM9 rig-reuse route of `../mm9_dfly_claude/` and `../mm9_lobber_claude/`: a new
HD Meshy mesh weighted to the ORIGINAL MM9 skeleton, the MM9 clips played with only the listed fixes. Progress,
hashes and receipts: `creature_3d_progress.json`.

The arms end in snake heads (jaw and tongue bones, no fingers), so this is not a humanoid-hand body.

## Rework v2 (2026-10-30, after the user's review) - current

User review of v1 (screenshots of the viewer): "the wings arent grafted onto body? and not sure if this model has a
separate head texture? maybe overall could benefit from better texturing". Before/after at the same cameras:
`review/v2/before_after_sheet.png` (wing root side and back at bind and both flap extremes, the three heads, the
right shoulder/arm of the user's screenshot). Viewer revision `r2_gdemon_20261030`.

**Causes**
- *Wings.* v1 took only the MM9 faces whose three vertices belong to wing bones. That dropped MM9's root web (26
  faces between the spine and the wing), so the wing root floated 33-36 cm behind the back (1.04 m in Death,
  `claude_shared/detached_parts_mm9.md`); the XwarmA hip-strap pieces were left as two floating slivers. The panels
  were flat-shaded (every normal = face normal).
- *Blur.* Smart UV Project (66 deg) on the reduced Meshy mesh made about two thousand tiny islands; with their margins
  only 17 % of the 2K atlas held texels, 128-141 texels/m on the body. Meshy then painted each island on its own
  (blotchy, smeared shoulder hump). The grade also damped half of the fine detail (`--fine 0.5`).
- *Heads.* No head set: the three heads were 2x islands in the same fragmented atlas; the arm heads got ~80 px each in
  the masters. Meshy's right arm head is also a different, short stub (not the long open-jawed head of the masters).

**Changes** (scripts in `scripts/`, chain `rig_v1 -> rig_wings_v2 -> reduced_v2 -> head_v2 -> uv_v2 -> uv_v2m -> uv_v2w
-> uv_v2b -> anim_v2`)
- `build_wings_v2.py` + `wings_v2_config.json`: bat wings on the MM9 wing chain. Bony tubes (smooth, 8/6 sides,
  knuckles) along the bone heads: a humerus that starts 12 cm inside the shoulder blade (the body point nearest the
  Xwing joint) and runs Xwing - XwingA - XwingB - XwingC - XwingD, finger spars to the XwarmC / XwarmB tips, a thumb
  claw on XwingB. Each segment is rigid to its bone with 6 cm joint blends; the buried root takes the body's own
  weights at its nearest body point and blends into Xwing, so it bends with the back. The membrane is three Coons
  patches between the bones (outer, middle, and an inner panel whose edge runs down the back, snapped onto the body
  and tucked 2 cm in, to the hip tip XwarmA), scalloped trailing edges, patch weights = the same Coons blend of the
  edge weights (the edges move exactly with the tubes and the body line with the body), solidified to an 8 mm shell,
  smooth with sharp rims, then `billow_membrane.py` (4.5 cm camber away from the rims, both layers together). MM9's
  flap motion is unchanged (same bones). A first build had no vertex groups for the wing bones (the body had none);
  `transfer_wing_weights.py` copied the fixed weights onto the already unwrapped mesh by position.
- `head_split_v2.py`: face attribute `head` (1 main head by head-bone weight, 2/3 the arm heads cut at the wrist spike
  ring 22 cm before Xawrist; small pieces whole). `uv_v2.py` + `xatlas_uv.py`: xatlas charts, square texels, the
  largest texels/unit that fits one page; body 2K (spikes 0.55x, membrane 0.8x density) and a 1K head atlas.
  Texel density: body 295 texels/m (v1 ~135), spikes 165, membrane 236, heads 340 at 1K.
- Head turnarounds (Codex via `codex_slot.sh`, two runs, `references_head/CODEX_BRIEF_MAIN.md`, `CODEX_BRIEF_ARM.md`):
  grey renders of OUR head meshes (`render_heads.py shape`) as the shape authority, crops of the approved body
  masters as the look authority; front, three-quarter, profile, back, 1254x1254, records `generation_runs_*.json`,
  sheets `selected_views_review_main.png` / `_arm.png`.
- Meshy (backup account, `tools/creature_meshy.py`): `retexture_v2` (body on the xatlas UVs, the v1 body masters),
  `head_retexture_v1` (main head, 4 head views), `armhead_retexture_v1` (left arm head, 4 views).
- `mirror_armhead.py`: the right arm head is the mirrored left one (groups renamed X..01 <-> X..), sharing its HeadUV
  texels (the engine derives normal-map tangents per pixel, so mirrored UVs light correctly); the old stub is removed
  where it lies inside the copy or past its base ring; the remaining right wrist (head 4, 73 faces, the Meshy forearm
  ends 16 cm short of the copy) keeps its own charts, painted through `armhead_mirror_map.py` from the left forearm's
  body texels or the left head's texels at each mirror point.
- `compose_v2.py` (body / head / headfinal), `bake_ao_v2.py` (AO per UV layer), `dump_uv_v2.py`: body base 2K graded
  with `--fine 0.85` (keeps more detail than v1's 0.5), normal/ORM 1K (R AO, G roughness), class maps
  `textures/gdemon_v2_material_classes.png`, `gdemon_v2_head_material_classes.png` (1 hide, 3 membrane, 4 spike,
  7 mouth, 11 the dark chitin plates); head set 1K (base, normal, ORM), main-head neck seam gain 1.107 (measured on the
  shared edges), arm heads 1 (their seam is the wrist band, a change of material).
- `build_export_v2.py`: three materials, `GreaterDemon` (body, wing bones, spikes), `GreaterDemon_Wing` (membrane, kept
  in place by the shadow shrink), `GreaterDemonHead` (the heads, HeadUV copied into the one UV layer); stray loose
  triangles (< 3 faces) dropped. Body base colour stays 2K (a 4 m creature with 3 m wings; a deviation from the 1K
  body rule for head sets).
- `review_v2.py`, `wing_review.py`: the before/after renders and the wing attachment measure.

| Item | v2 |
|---|---|
| Triangles LOD0/1/2/3 | 9,988 / 4,945 / 1,665 / 460 (body material 5,136 incl. 1,520 in the wing bones; membrane 1,648; heads 3,204) |
| Textures | body 2K base + 1K normal/ORM; head set 1K base/normal/ORM |
| Meshy credits | **30** this rework (3 retextures x 10), **45 / 45** in total (backup account) |

**Checks (2026-10-30)**
- Winding: 0 inverted closed parts (`fix_winding.py` flipped 2 collapsed bits). Installed with
  `tools/install_model.py --world mm9`.
- `tools/run_creature_review.py --project ... check`: 9 clips switched, 0 console errors.
- Floor audit `--world mm9`: MM9 Demon B ok (49 bindings, 0 problems). `--headless-validate-actor-models` (mm9):
  49 descriptors on 20 models, only another project's Dagrell refused.
- Wing attachment (`wing_review.py`, every clip, every 2nd frame): the buried root and the membrane's body line stay
  inside the body: at most 3.2 cm out (the root ring in AttackMelee) and 2.2 cm (membrane line; 1.7 cm at bind).
  Largest membrane edge stretch 4.4x at the wing tip (MM9's own tip stretch; v1 4.6-4.9).
- `claude_shared/detached_parts_audit.py`: wings and the XwarmApiv slivers gone; 2 neck spikes (10-12 tris) part by
  at most 8.9 mm in a few Death/Fidget frames (`review/v2/detached_parts_audit.md`).
- Flat shading (glTF normals): body 0.01, heads 0.00, membrane 0.25 (its rims and the flattest panel cores).
- Not done: in-game captures of v2 (optional); the remaining wrist-band texels of the right arm head are a mirror
  transfer, so its band is a little softer than the left one.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_greaterdemon.glb` (installed; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Demon B`, scale 100 (= MM9 size, MONSTERS.txt Scale 1), one skin |
| Triangles LOD0/1/2/3 (v1) | 7,945 / 3,919 / 1,303 / 450 (LOD0: body 6,559 incl. 2,151 in the 152 spikes/teeth, wings 1,386) |
| Skeleton | the MM9 one, 105 joints, names unchanged (`Bip01 Pelvisxx`, `Xspine*`, `Xneck*`, `Bip01 Headx`, `Xhjaw*`, arm-head chains `Xa*`, wing chains `Xwing*`/`Xwarm*`, digitigrade legs `Xl*`, tail `Xtail*`) + `Socket_Mouth` on `Xhead` |
| Clips (30 fps) | Standing 1.9 (stand), Walking 1.2 (walk), Running 0.7 (run), Fidget 1.8 (fidget1), AttackMelee 0.8 (Hattack1), AttackRanged 1.1 (Rattack1, also the cast), Hit 0.73 (wince1), Death 2.5 (die1), Dead 1.0 |
| Events | melee impact 0.390 s (MM9 `Lattack`), ranged/cast impact 0.402 s (MM9 `RangeAttack`), released from `Socket_Mouth` |
| Gait | stride 2.66, run stride 5.62 model units (foot fore-aft travel / stance duty 0.6 and 0.4, `scripts/stride.py`) |
| Floor | ground rule: living clips lifted 0.1648 (MM9 stands with bent knees below its bind pose), tail bent up from `Xtailbase` where MM9 drags it through the floor, corpse grounded; `floor_audit.py --world mm9` ok |
| Meshy credits (v1) | **15** (Smart Topology 5, retexture 10; backup account) |

## Route (v1; v2 replaces steps 4, 5 and 7, see "Rework v2")

0. **HD masters** (`references_hd/`, Codex via `claude_shared/codex_slot.sh`, two runs): renders of the MM9 model
   with its skin (`mm9_views_tier1.png`, ortho 5.3 so the raised wings are not cropped; `mm9_top_tier1.png`; the skin
   ×4). Brief `CODEX_BRIEF.md`, records `generation_runs.json`, `selected_views_review.png`. 1024×1536. Gate: all
   five show the horned head with open jaw, snake-headed arms, raised bat wings, two-toed digitigrade feet and the
   arrow-tipped tail; colour halo only in fully transparent pixels.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/body_smart_v1.json`).
2. **Fit** (`scripts/fit_mm9.py`, config `scripts/fit_config.json`): uniform scale from the height, yaw search (0),
   scale+translation ICP, then an articulated correction: per segment (head, arm/fore-arm/arm-head, thigh/shin/foot,
   tail) a rotation about its MM9 pivot joint from symmetric nearest points, composed root to tip, blended by the
   diffused segment labels. Meshy built the wings in the frontal plane (the masters show them from the front); they
   are dropped (`drop` rules: the three membrane/arm components and the wing-claw spikes).
3. **Weights** (`scripts/rig_mm9.py`, `scripts/rig_config.json`): the barycentric bone blend of the nearest MM9
   surface point (lateral vertices only see their own side), diffused 10 iterations with the jaws held, 2 free;
   spikes and teeth rigid with their nearest body vertex; 4 influences.
4. **Wings** (`scripts/build_wings.py`, `scripts/wings_config.json`): the MM9 wing faces themselves (84 triangles,
   duplicates removed → 74), subdivided (2 cuts) and solidified to a 12 mm closed shell; weights are the barycentric
   blend of the MM9 triangle under each vertex, so the flap and membrane stretch are exactly MM9's. Own material slot
   (`GreaterDemon_Wing`, same maps) so the shadow shrink leaves the thin shell in place.
5. **Reduce** (`scripts/reduce_body.py 0.45 0.35 0.7`: body, spikes/teeth, the three heads; wings kept), **UV**
   (`scripts/uv_export.py`, Smart UV, head islands ×2), **retexture** from 01/03/02/04 on our UVs
   (`requests/retexture_v1.json`; the wings are painted with the body).
6. **Clips** (`scripts/clips_mm9.py`, run by `scripts/build_export.py`): MM9 key poses resampled as PCHIP curves at
   30 fps, loop seams closed (largest 0.35° before), loops end on an exact frame; Dead = die1's last pose.
7. **Textures** (`scripts/compose.py`): 2K base graded once (`grade_basecolor.py`, AO `bake_ao.py` reach 0.05), 1K
   normal, 1K ORM (R AO, G roughness, B 0). One MM9 row and one skin, so no region mask or ramps.
8. **Runtime** (`scripts/build_runtime.sh`): prepare → LODs → shadow shrink (wing shells kept) → material extras
   (specular 0, metallic 0) → floor (lift, tail bend, ground/raise, corpse) → `fix_winding.py` (6 collapsed bits:
   a 6-triangle spike remnant at LOD0 and wing tetrahedra at LOD2, turned outward) → winding check 0.

## Rebuild

v2 (from `work/rig_v1.blend`; T = lease token, B and P as in the v1 block below, XATLAS_PYTHON = a python with
xatlas, e.g. `level_generation/creatures/hes_noble_bosses_claude/work/venv/bin/python`; Meshy jobs as recorded):

```sh
$B $P/scripts/build_wings_v2.py $PWD/$P/work/rig_v1.blend $PWD/$P/work/rig_wings_v2.blend $P/work/wings_v2.json $P/scripts/wings_v2_config.json
$B $P/scripts/reduce_body.py $PWD/$P/work/rig_wings_v2.blend $PWD/$P/work/reduced_v2.blend $P/work/reduced_v2.json 0.45 0.35 0.7   # HEAD_BONES as v1
$B $P/scripts/head_split_v2.py $PWD/$P/work/reduced_v2.blend $PWD/$P/work/head_v2.blend $P/work/head_v2.json
XATLAS_PYTHON=... $B $P/scripts/uv_v2.py $PWD/$P/work/head_v2.blend $PWD/$P/work/uv_v2.blend $PWD/$P/texturing/gdemon_body_upload_v2.glb $PWD/$P/texturing/gdemon_head_upload_v2.glb $PWD/$P/texturing/gdemon_armhead_upload_v2.glb $P/work/uv_v2.json
# (retexture_v2, head_retexture_v1, armhead_retexture_v1 were made on these uploads: requests/*.json)
$B $P/scripts/bake_ao_v2.py $PWD/$P/work/uv_v2.blend UVMap body $PWD/$P/textures/gdemon_ao_v2_2k.png 0.05 2048
$B $P/scripts/bake_ao_v2.py $PWD/$P/work/uv_v2.blend HeadUV head $PWD/$P/textures/gdemon_head_ao_v2_1k.png 0.04 1024
$B $P/scripts/mirror_armhead.py $PWD/$P/work/uv_v2.blend $PWD/$P/work/uv_v2m.blend $P/work/mirror_armhead.json
$B $P/scripts/transfer_wing_weights.py $PWD/$P/work/rig_wings_v2.blend $PWD/$P/work/uv_v2m.blend $PWD/$P/work/uv_v2w.blend
$B $P/scripts/billow_membrane.py $PWD/$P/work/uv_v2w.blend $PWD/$P/work/uv_v2b.blend
$B $P/scripts/armhead_mirror_map.py $PWD/$P/work/uv_v2b.blend $PWD/$P/work/armhead_mirror_2k.npz 2048
$B $P/scripts/dump_uv_v2.py $PWD/$P/work/uv_v2b.blend $PWD/$P/work/uv_v2_tris.npz
G=level_generation/creatures/claude_shared/grade_basecolor.py
python3 $P/scripts/compose_v2.py body && python3 $G --ao $P/textures/gdemon_ao_v2_2k.png --fine 0.85 $P/textures/gdemon_v2_basecolor.png
python3 $P/scripts/compose_v2.py head && python3 $G --ao $P/textures/gdemon_head_ao_v2_1k.png --fine 0.85 $P/textures/gdemon_v2_head_basecolor_2k.png && python3 $P/scripts/compose_v2.py headfinal
$B $P/scripts/build_export_v2.py $PWD/$P/work/uv_v2b.blend $PWD/$P/work/anim_v2.blend $PWD/$P/export/mm9_greaterdemon_lod0.glb $P/work/clips_v2.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
```

v1:

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_greaterdemon_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
$V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/STAGE2DEMON.abc $P/source/tier1 \
  --id gdemon --texture 0=mm9/extracted/SKINS/SKINS/GREATERDEMON.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/tier1/gdemon.glb $PWD/$P/work/mm9_gdemon_ground.blend 0 1.7131
$B $P/scripts/fit_mm9.py $PWD/$P/work/mm9_gdemon_ground.blend $P/meshy/body_smart_v1/model_urls_glb.glb $P/scripts/fit_config.json $PWD/$P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_mm9.py $PWD/$P/work/fit_v1.blend $P/scripts/rig_config.json $PWD/$P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/build_wings.py $PWD/$P/work/rig_v1.blend $PWD/$P/work/mm9_gdemon_ground.blend $PWD/$P/work/rig_wings_v1.blend $P/work/wings_v1.json $P/scripts/wings_config.json
export HEAD_BONES="Bip01 Headx,Xhead,Xhmouth,Xhnose,Xhjawpiv,Xhjaw,Xhchin,Xhtonguepiv,Xhtongue,Xaheadpiv,Xahead,Xajawpiv,Xajaw,Xatonguepiv,Xatongue,Xaheadpiv01,Xahead01,Xajawpiv01,Xajaw01,Xatonguepiv01,Xatongue01"
$B $P/scripts/reduce_body.py $PWD/$P/work/rig_wings_v1.blend $PWD/$P/work/reduced_v1.blend $P/work/reduced_v1.json 0.45 0.35 0.7
HEAD_FACTOR=2.0 $B $P/scripts/uv_export.py $PWD/$P/work/reduced_v1.blend $PWD/$P/work/uv_v1.blend $PWD/$P/texturing/gdemon_body_upload.glb
# (retexture_v1 was made on this upload)
$B $P/scripts/dump_uv3d.py $PWD/$P/work/uv_v1.blend $PWD/$P/work/uv3d_body.npz Body
$B $P/scripts/bake_ao.py $PWD/$P/work/uv_v1.blend Body $PWD/$P/textures/gdemon_ao_2k.png 0.05 2048
python3 $P/scripts/compose.py && python3 level_generation/creatures/claude_shared/grade_basecolor.py --ao $P/textures/gdemon_ao_2k.png $P/textures/gdemon_basecolor.png
$B $P/scripts/build_export.py $PWD/$P/work/uv_v1.blend $PWD/$P/work/anim_v1.blend $PWD/$P/export/mm9_greaterdemon_lod0.glb $P/work/clips_v1.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
(cd $P && python3 scripts/make_viewer_manifest.py r1_gdemon_20261030 "gdemon=Greater Demon (MM9 Demon B)=export/mm9_greaterdemon.glb")
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (1 model × 9 clips): `tools/run_creature_review.py --project ... check` 0 errors; shots
  `review/shots/`, `review/viewer_shots_sheet.png` (the viewer's fixed framing crops this 4 m body; full-body
  Blender renders of every clip from the master: `review/anim_textured_sheet.png`).
- Gates (`scripts/gates.py`, `review/gates.json`, 60 Hz): loop seams 0; edge ratio p1/p99 0.56–0.76 / 1.74–2.14;
  maxima ~4.6–4.9 on wing-shell rims where MM9 stretches the membrane.
- Floor audit `--world mm9`: ok. Between keys (60 Hz) the tail tip dips up to 6.5 cm (Hit), 1.6 % of the height.
- Regression `mm9_actor_models_build_every_binding` (`--world mm9`): 48 descriptors on 19 models, 0 failed
  (2026-10-30 01:47; earlier runs failed only on other agents' bindings while they were being installed).
- Winding: 0 inverted closed parts after `fix_winding.py`.
- In game (Ravensford `bootcamp.odm`, `tools/run_game.sh` minimized, private `--user-data` folder with
  `[startup] start_in_main_menu=false`, `start_map_file=bootcamp.odm`, `immortal=true` and the one-shot
  `menu_input_tour_path`; tours `review/ingame_tour.yml` and `../mm9_wingedmutant_claude/review/ingame_tour.yml`, each
  `exit: true`): `review/ingame_demon_models_sheet.png` (static model: standing, walk, attacks, hit, death, corpse on
  the valley floor), `review/ingame/a01_spawned.png`–`a07` (a spawned `MM9 Demon B` actor and the three harpy tiers
  attacking the party), `../mm9_wingedmutant_claude/review/ingame/w01_all.png` and `d01`–`d07` (profile, ranged
  release, death, corpse). The narrow valley clips the farther orbit cameras. A first run used Isle of Ashes
  coordinates inside a rock (`review/ingame_isle/`, kept for the record).

## Deviations and open points

- (v1, replaced by v2) Wings were MM9's own wing geometry (subdivided, solidified), painted by the retexture; their
  outline is MM9's low-poly silhouette with flat-shaded panels.
- Clips are in place: MM9 `lunge` (Hattack1) and die1's `Velocity` events (the body slides while falling) are not
  reproduced; `DoFX`/`EndFX` (fidget/Rattack glow effects), `block`, `dodgeleft/right`, `taunt`, `fidget2`, `wince2`,
  `Backpedal*`, `skullsetup` and `spawn` (the emergence from the Lesser Demon, `LesserDemon.scr`) are not exported:
  the engine has one clip per role and no spawn role.
- One skin, no tiers. (v1, replaced by v2: no separate 1K head set; the three heads used 2× UV islands in the 2K atlas, as the approved
  MM9 dragonfly and Lobber do).
- The foot is weighted mostly to the toe bones (`Xltoe*`); the MM9 `Xlfoot`/`Xlankle` carry few vertices.
- User artistic acceptance: v2 accepted 2026-10-30 ("greater demon - ok").


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_greaterdemon_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_greaterdemon_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_greaterdemon_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_greaterdemon_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_greaterdemon_reduce_claude/before/`.

# MM9 Lobber family (mm9_lobber, mm9_lobberpod) — 3D models, 2026-10-29

Two bodies for one MM9 family (`tools/mm9_import_discovery/mm9_monster_families.yml`: lobber 84/85/86, ice_lobber
105/106), built on the route of `../mm9_dfly_claude/` (MM9 rig reuse: new HD Meshy mesh weighted to the original MM9
skeleton, the MM9 clips played with only the listed fixes). Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Lobber (`mm9_lobber`) | Lobber Pod (`mm9_lobberpod`) |
|---|---|---|
| MM9 source | `LOBBER.abc` (37 joints, 243 tris, 11 clips) | `LOBBERPOD.abc` (28 joints, 174 tris, 15 clips) |
| Descriptors / skins | MM9 Lobber C `lobber_a` (LOBBER), MM9 Ice Lobber B `lobber_b` (ICELOBBER) | MM9 Lobber A `pod_a` (LOBBERPOD), Lobber B `pod_b` (LOBBERPOD2), Ice Lobber A `pod_c` (ICELOBBERPOD) |
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_lobber.glb` (cooked copy in `assets_dev`) | `assets_source/worlds/mm9/models/mm9_lobberpod.glb` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, scale 100 (= MM9 size) | scale 100; Lobber B and Ice Lobber A 200 (MONSTERS.txt `Scale` 2) |
| Triangles LOD0/1/2/3 | 5,855 / 2,922 / 1,029 / 322 | 4,806 / 2,403 / 864 / 287 |
| Clips (30 fps) | Standing 1.5 (StandAir), Fidget 1.6 (FidgetAir1), AttackRanged 0.8 (Rattack1, also melee), Cast 0.8 (LaunchPod), Hit 0.9 (winceAir2), Death 2.1 (DieAir1 + wilt), Dead 1.0 | Standing 1.6 (stand), Walking 0.6 (walk), Running 0.3 (run: the rolled ball), Fidget 1.8, AttackMelee 0.6 (Hattack1), AttackRanged 0.7 (Rattack1, also the cast), Hit 0.7 (wince1), Death 1.1 (die1), Dead 1.0 |
| Events | RangeAttack / LaunchPod 0.333 s, released from `Socket_Mouth` (on `Xheadpiv`) | rAttack 0.293 s, RangeAttack 0.257 s, from `Socket_Mouth` (on `Xhead`) |
| Meshy credits | **55 / 80** in total (backup account): Lobber Smart Topology 5 + retexture 10 + 4K retexture v2 10; pod Smart Topology 5 + one retry 5 + retexture 10 + 4K retexture v2 10 (limit raised from 40 for the texture pass, see that section) | |

## Decisions

- **The Lobber grows from the floor.** In MM9 it hangs from sewer ceilings (all 16 Beethoven Lobbers at Y 433 or
  -1056, `Gravity 0`; "when the lobber dies, it falls to the floor"; the root piece is hidden in the death clips).
  Our actors stand on the floor and nothing supports ceiling actors, and the hanging body resting on its claw tips read
  wrongly (`work/placement_sheet.png`), so the whole skeleton is turned 180 degrees about the forward axis
  (`scripts/mm9_rig_source.py`: applied to the armature rest pose, so every MM9 clip follows unchanged; the face stays
  forward). The root bulb sits on the floor, the stalk rises, the flytrap head is on top. MM9's fall from the ceiling
  (`fall1`, `falldown1`) would rise in the upright plant, so Death is DieAir1 then a wilt: the stalk topples backward
  from `Xstembase` with a gravity-like ease-in, shared over the four stem bones, angle solved so the head lands on the
  floor (96 degrees), a small bounce and settle. A ceiling variant needs engine support (hanging actors) and the
  original orientation (drop the flip).
- **The pod is a second creature, not a projectile.** MM9 Lobber Pod and Ice Lobbercicle rows are walking monsters
  (`LobberPod.ABC`, `lobberpod.scr` crawler AI, `spiderstep`), placed in Ravensford (bootcamp, 4 + 1), Beethoven and
  the ice maps, and the families use them as tiers A/B (Pod, Pod L2, Lobber) and ice A (Lobbercicle). The Lobber's
  pod launch (MM9 `LaunchPod` spawns a pod) is not reproduced: our Lobber's attack is its MM9 missile, and the
  LaunchPod clip plays as its cast. The pod's own `projectile`/`land` clips (the launched flight) are not exported.
- **MONSTERS.txt `Scale`** reads as a model size multiplier across the table (cat 2.5, wolves 0.4-0.5, specters 1.8),
  so the two `Scale 2` rows get binding scale 200. The descriptor heights (199 for every row) are untouched.
- **Roles:** Lobber walking/run map to Standing (stationary, `Stationary` in monster_data); its melee plays
  AttackRanged. Hit is the 0.9 s winceAir2 (winceAir1 is 1.5 s). The pod runs as MM9's rolled ball (one full roll per
  cycle, run stride 1.5 m from the ball's circumference; walk stride 0.225 m from the foot travel,
  `scripts/gait_measure.py`).

## Route

0. **HD masters** (Codex, two runs per body): renders of the MM9 model with its tier-1 skin (`references_hd*/
   mm9_views_tier1.png`, Lobber flipped upright), skin x4, top view; briefs `CODEX_BRIEF.md`; records
   `generation_runs.json`, `selected_views_review.png`. Lobber 1024x1536, pod 1536x1024.
1. **Meshy** Smart Topology 15k: Lobber from `00_three_quarter.png`; pod v1 from 00 came back with eight limbs (the
   three-quarter view's far limbs duplicated), v2 from `01_front.png` matched MM9 (`work/meshy_pod2_sheet.png`).
2. **Fit** (`scripts/fit_limbs.py`): global scale from the height (+ ICP), then every limb mapped onto its MM9 bone
   chain. Separate limb pieces (all six Lobber limbs, the stalk, four pod limbs): tip = vertex geodesically farthest
   from the attachment, centreline from geodesic bins, arc length mapped piecewise (sharpest Meshy bend onto the
   sharpest MM9 joint), offsets kept in parallel-transported frames. The pod's rear leg grows out of the body: its
   segments are posed onto the MM9 chain by linear blend skinning (`fit_chain_lbs`). Overlays `work/fit_*_sheet.png`.
3. **Weights** (`scripts/rig_body.py`): nearest MM9 vertex label, a limb vertex only from its own chain's bones;
   diffusion with the lid hinge held; mouth strands rigid with their nearest body vertex; 4 influences. Lobber head
   re-weighted after the UVs (`scripts/reweight_head.py`, hinge plane through `Xjawpiv` and the mouth centre): the top
   lid had smeared when MM9 opens it ~120 degrees (`work/headclose.png` before, `work/headclose2.png` after).
4. **Reduce** (`scripts/reduce_body.py`; Lobber bulb 0.2, body 0.5, head 0.6, strands 0.25; pod 0.3/0.4/0.3),
   **UV** (`scripts/uv_export.py`: Smart UV, head islands x2 / x1.6), **retexture** from 01/03/02/04 with our UVs.
5. **Clips** (`scripts/clips_mm9.py`, run by `scripts/build_export.py`): MM9 key poses resampled as PCHIP curves at
   30 fps, loop seams closed (pod stand/run 0.06 degrees before), Lobber death wilt, Dead = last pose.
6. **Textures** (`scripts/compose.py`): 2K graded base (`grade_basecolor.py`, AO `bake_ao.py`), 1K normal, 1K ORM.
   Regions are hue families so one luminance ramp holds tier A (R red/magenta, G olive/brown/yellow, B teal/blue
   mouth, A violet); the same bins on the MM9 tier-1 skin pick the texels sampled in each tier skin. Tier A identity,
   others take their MM9 skin's chroma by luminance percentile (dragonfly method). `review/*_texture_classes_tiers.png`,
   `work/tierprev.png` (base vs every tier with the engine rule).
7. **Roots** (Lobber only, `scripts/root_limbs.py`, 2026-10-30, on the re-weighted UV blend; see also the texture pass): upper arms and middle
   limbs rooted in the head, one tooth made rigid with its neighbour (see the dated section below).
8. **Runtime** (`scripts/build_runtime.sh lobber|pod`): prepare -> LODs -> shadow shrink (margins 1.5-4 mm for the thin
   stalk and limbs) -> `region_variants.py` (specular 0, metallic 0) -> floor pass (ground loops, raises, corpse
   grounding) -> winding check (0 inverted).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_lobber_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C="tools/mm9_import_discovery/convert_abc_model.py"
$V $C $M/LOBBER.abc $P/source/lobber --id lobber --texture 0=$S/LOBBER.dtx --scale 0.0256   # also icelobber,
$V $C $M/LOBBERPOD.abc $P/source/pod --id pod --texture 0=$S/LOBBERPOD.dtx --scale 0.0256   # pod2, icepod
$B $P/scripts/mm9_rig_source.py $P/source/lobber/lobber.glb $P/work/mm9_lobber_upright.blend 1 0.7926
$B $P/scripts/mm9_rig_source.py $P/source/pod/pod.glb $P/work/mm9_pod_ground.blend 0 0.3191
$B $P/scripts/fit_limbs.py $P/work/mm9_lobber_upright.blend $P/meshy/lobber_smart_v1/model_urls_glb.glb lobber $P/work/fit_lobber_v1.blend $P/work/fit_lobber_v1.json
$B $P/scripts/fit_limbs.py $P/work/mm9_pod_ground.blend $P/meshy/pod_smart_v2/model_urls_glb.glb pod $P/work/fit_pod_v2.blend $P/work/fit_pod_v2.json
$B $P/scripts/rig_body.py $P/work/fit_lobber_v1.blend lobber $P/work/rig_lobber_v1.blend $P/work/rig_lobber_v1.json
$B $P/scripts/rig_body.py $P/work/fit_pod_v2.blend pod $P/work/rig_pod_v2.blend $P/work/rig_pod_v2.json
$B $P/scripts/reduce_body.py $P/work/rig_lobber_v1.blend $P/work/reduced_lobber_v1.blend $P/work/reduced_lobber_v1.json 0.5 0.25 0.6 0.2
$B $P/scripts/reduce_body.py $P/work/rig_pod_v2.blend $P/work/reduced_pod_v2.blend $P/work/reduced_pod_v2.json 0.3 0.3 0.4
$B $P/scripts/uv_export.py $P/work/reduced_lobber_v1.blend lobber $P/work/uv_lobber_v1.blend $P/texturing/lobber_body_upload.glb
$B $P/scripts/uv_export.py $P/work/reduced_pod_v2.blend pod $P/work/uv_pod_v2.blend $P/texturing/pod_body_upload.glb
# (the retextures were made on these uploads)
$B $P/scripts/reweight_head.py $P/work/uv_lobber_v1.blend $P/work/mm9_lobber_upright.blend $P/work/uv_lobber_v2.blend $P/work/reweight_lobber_v2.json
for b in "lobber uv_lobber_v2" "pod uv_pod_v2"; do set -- $b
  $B $P/scripts/dump_uv3d.py $P/work/$2.blend $P/work/uv3d_$1.npz Body
  $B $P/scripts/bake_ao.py $P/work/$2.blend Body $PWD/$P/textures/$1_ao_2k.png 0.03 2048; done
$B $P/scripts/dump_uv3d.py $P/source/lobber/lobber.glb $P/work/uv3d_mm9_lobber.npz lobber.mesh:1 root.mesh:2
$B $P/scripts/dump_uv3d.py $P/source/pod/pod.glb $P/work/uv3d_mm9_pod.npz crawler.mesh:1
for b in lobber pod; do python3 $P/scripts/compose.py $b && python3 $P/../claude_shared/grade_basecolor.py \
  --ao $P/textures/${b}_ao_2k.png $P/textures/${b}_basecolor.png && python3 $P/scripts/compose.py $b; done
# texture pass (2026-10-30, the steps above are the v1 maps; `work/before_texpass/` holds them for the tone match)
$B $P/scripts/root_limbs.py $P/work/uv_lobber_v2.blend $P/work/roots_lobber_v1.blend $P/work/roots_lobber_v1.json   # (the first version of the script)
$B $P/scripts/uv_atlas_texpass.py $P/work/roots_lobber_v1.blend lobber $P/work/uv_lobber_v3.blend $P/texturing/lobber_body_upload_v2.glb $P/work/uv_lobber_v3.json
$B $P/scripts/uv_atlas_texpass.py $P/work/uv_pod_v2.blend pod $P/work/uv_pod_v3.blend $P/texturing/pod_body_upload_v2.glb $P/work/uv_pod_v3.json
#   xatlas packs differently per run: never re-run these two, retexture_v2 of each body is on those uploads
for b in lobber pod; do python3 tools/creature_meshy.py --project $P --token $T submit --job ${b}_retexture_v2 --kind retexture \
  --request requests/${b}_retexture_v2.json --credits 10; done      # then poll / download
for b in lobber pod; do $B $P/scripts/dump_uv3d.py $P/work/uv_${b}_v3.blend $PWD/$P/work/uv3d_${b}_v3.npz Body; done
$B $P/scripts/bake_ao.py $P/work/uv_lobber_v3.blend Body $PWD/$P/textures/lobber_ao_2k.png 0.03 2048
$B $P/scripts/bake_ao.py $P/work/uv_pod_v3.blend Body $PWD/$P/textures/pod_ao_2k.png 0.02 2048
(cd $P && work/texpass_compose.sh lobber --push orange=0.98,1.11,1.0 --push yellow=0.98,1.09,1.0 && work/texpass_compose.sh pod)
$B $P/scripts/root_limbs.py $P/work/uv_lobber_v2.blend $P/work/uv_lobber_v4.blend $P/work/roots_lobber_v2.json $P/work/uv_lobber_v3.blend
$B $P/scripts/verify_same_mesh.py $P/work/uv_lobber_v3.blend $P/work/uv_lobber_v4.blend      # max move 0, max UV diff 0
TOKEN=$T $P/work/rebuild_texpass.sh lobber --install; TOKEN=$T $P/work/rebuild_texpass.sh pod --install
```

The pod's AO was baked at reach 0.02 (Lobber 0.03).

## Checks (2026-10-29)

- Viewers: `review/viewer/` (Lobber, 2 tiers x 7 clips) and `review/viewer_pod/` (3 tiers x 9 clips), both
  `check_viewer.mjs` 0 errors. They use the project's own three.js copy (`review/vendor/`, three 0.186.1 from the
  local npm cache): the shared `mm6_goblin/review_20261006/vendor/` was missing on 2026-10-29 (the dragonfly viewer
  fails the same way until it is restored). Shots `review/viewer_shots_lobber.png`, `review/viewer_shots_pod.png`;
  playback `review/playback/` (Lobber, every clip at 1x and 0.5x).
- Gates (`scripts/gates.py`, `review/gates_*.json`): loop seams 0; edge ratio p1/p99 per clip Lobber 0.54-0.88 /
  1.2-2.3, pod 0.50-0.81 / 1.25-2.9; the Lobber's extremes (max 14.6) are tiny mouth-corner edges when MM9 opens the
  lid to vertical.
- Floor audit `floor_audit.py --world mm9`: 11/11 ok. Regression `mm9_actor_models_build_every_binding`: 11
  descriptors on 6 models, 0 failed (suite 4/4). Winding: 0 inverted closed parts.
- In game (Ravensford `bootcamp.odm`, `tools/run_game.sh` minimized, private `--user-data` folder whose
  settings.ini has `[startup] start_in_main_menu=false`, `start_map_file`, `immortal=true` and the one-shot
  `menu_input_tour_path`; tours `review/*_tour.yml`, each `exit: true`): `review/ingame_pods_sheet.png` (the map's own
  Lobber Pods and the L2 pod as 3D actors, a spawned Ice Lobbercicle, attacks, death), `review/ingame_lobber_sheet.png`
  (spawned Lobber and Ice Lobber standing on the valley floor and slope, firing their missiles, the Ice Lobber's
  wilt and loot satchel), `review/ingame_models_sheet.png` (static Lobbers and a pod on the valley floor playing
  Standing, attacks, Cast, Hit, Running and Death to the corpse). The Isle of Ashes coordinates of the dragonfly tour point at a rock on the original map
  (`review/ingame_isle_sheet.png`, only the missiles visible).

## Arms rooted in the head (2026-10-30)

`claude_shared/detached_parts_audit.py` (`claude_shared/detached_parts_mm9.md`) on the installed Lobber: both upper
arms visibly off the head, also two smaller flags. MM9's own Lobber (`source/lobber/lobber.glb`) is one connected mesh
(the arms are part of its body; 0 detached in all its clips), so every gap is ours. The Lobber Pod passed and is
untouched (its installed GLB is byte-identical).

- **Cause.** Upper arms (`XCbase -> XCpiv -> XCarm`, both sides): `fit_limbs.py` starts each separate arm piece at its
  XCbase joint, 1.2-1.5 cm above our HD head shell (1.9-2.8 cm along the root bone's axis); the arm hangs on Xmouth
  while the head under it is about half Xjaw (`reweight_head.py`), so the gap grew when MM9 opens the lid: 11.6 /
  14.6 mm at bind, up to 62.3 mm (XCarm01, Dead) and 31.1 mm (XCarm, Death 0.60 s), visible in 193-208 of 268 poses.
  Middle limbs (`XBpiv -> XBarm`): rooted only 2-6 mm and rigid on XBpiv while the head there blends
  Xjawpiv/Xheadpiv/Xjawbase: 9.3 mm (XBpiv01, AttackRanged 0.27 s, 17 poses) and 4.5 mm (XBpiv, Death 0.87 s).
  One 14-tri tooth at the -x mouth corner (wedged between an upper and a lower tooth, 1.5 cm from the head shell)
  was rigid with a hinge-band head vertex carrying 24 % Xchin (a lid bone): 9.1 mm off in AttackRanged 0.23 s.
- **Fix** (`scripts/root_limbs.py` on `work/uv_lobber_v2.blend`, so UVs, the retexture and the textures stay valid; no
  Meshy spend; AO not re-baked). Each limb's own piece is rooted as in `../mm9_eye_claude/` `root_limbs.py`: the head
  surface is found along the root bone's axis, the first segment stretched along that axis until the cap is one rod
  radius (2.3 cm upper arms, 3 cm middle limbs) inside the head (17-26 cm thick there), J1 and the rest of the limb
  unmoved, vertices moved only along the axis (stretch 1.60 / 1.82 upper arms, 1.16 middle limbs; 162 vertices), the
  buried root's weights blended to the head's at the entry point (upper arms Xmouth 0.54-0.59 / Xjaw 0.37-0.46,
  middle limbs Xjawpiv 0.51-0.54 / Xheadpiv 0.35-0.38). The tooth is rigid with the nearest lower-head tooth (dropping
  only its Xchin share moved the gap to Standing, 5.8 mm). `work/roots_lobber_v1.json`. Clips unchanged
  (`work/clips_lobber_v3.json` = `clips_lobber_v2.json`).
- **Checks.** Detached-parts audit of the installed GLB at 30 and 48 fps: 0 detached (was 5); the "only just attached"
  list is the same parts as before (mouth pieces, the XApivot lower limbs). Triangles 5,855 / 2,922 / 1,029 / 322
  (LOD1 one fewer). `floor_audit.py --world mm9`: Lobber A/B/C, Ice Lobber A/B ok; winding 0 inverted; flat-shading
  0.00 (as before); gates edge ratio unchanged except Dead/Death p99 1.57 -> 1.66, max 4.0 -> 5.0 (the arm roots now
  stretch with the lid); `run_creature_review.py check` 14 switches 0 errors (viewer revision
  `r3_lobber_rootfix_20261030`), `check_viewer.mjs` on `review/viewer_pod/` 27 switches 0 errors; regression
  `mm9_actor_models_build_every_binding` (`--world mm9 --headless-run-regression-suite actors`) PASS, 49 descriptors on 20 models, 0 failed. Sheets: `review/rootfix_worstframes_before_after.png`
  (bind, Dead, Death 0.60, Fidget 0.70, Hit 0.50, AttackRanged 0.27 s), `review/rootfix_closeups_before_after.png`
  (the tooth in AttackRanged 0.23 s, the upper-arm roots at bind). The pre-fix export is kept in
  `work/before_rootfix/`.

## Texture quality pass (2026-10-30) - current maps

`../claude_shared/TEXTURE_QUALITY_PASS.md`, `../claude_shared/MM9_TEXTURE_PASS_BRIEF.md`. Both bodies missed the targets, so
both were done. Vertices, rig and clips are unchanged (`clips_lobber_v4` = `v3`, `clips_pod_v3` = `v2`; LOD triangles as
before); the only rig change is the Lobber's root weights below. **20 Meshy credits** (4K retexture v2, 10 each, backup
account); family total **55 / 80**.

**Limit raised 40 -> 80.** `creature_meshy.py` refused both jobs at the old limit, and the work stopped there. The
coordinator then directed the raise (`claim --budget 80`), reporting the user's approval of the pass; the record is in
`creature_3d_progress.json`, `meshy.credit_limit_changes`. Actual spend is 20 credits.

| `texture_quality.py` (LOD0) | Lobber before | after | Pod before | after |
|---|---|---|---|---|
| Atlas use (2K) | 38.6 % | **60.3 %** | 48.3 % | **62.6 %** |
| Equivalent fully used square | 1,273 px | **1,590 px** | 1,423 px | **1,620 px** |
| Density p10 / p50 / p90 | 829 / 955 / 1,884 | 1,083 / 1,128 / 2,267 | 977 / 1,113 / 1,781 | 1,175 / 1,217 / 1,945 |
| Spread p90/p10 (head denser on purpose) | 2.27 | 2.09 | 1.82 | 1.65 |
| Islands / surface on fragments | 588 / 9.3 % | 226 / **1.1 %** | 559 / 9.6 % | 108 / **0.4 %** |
| Stretch p90 | 1.44 | 1.17 | 1.43 | 1.15 |
| Zero-area UV triangles | - | 0 | - | 0 |
| Fine detail (under 1.5 px, RMS levels) | 8.7 | 16.6 | 8.6 | 14.3 |
| 4-16 px blotch band (RMS levels) | 21.9 | 17.6 | 18.1 | 14.6 |
| Meshy source | 2K, Smart UV | 4K on the new UVs | 2K, Smart UV | 4K on the new UVs |

- **UVs** `scripts/uv_atlas_texpass.py`: the Lobber on the rooted mesh (`work/roots_lobber_v1.blend`, so the gap fix of the
  section below survives), the pod on `uv_pod_v2`; head factors as `uv_export.py` (x2, x1.6). Do not re-run.
- **Grade** gentle; AO re-baked on the new UVs (the Lobber's now includes the rooted limbs). Regions recomputed from the new paint.
- **Tone** `scripts/tone_match.py` (per hue class of the new paint, each channel's distribution mapped to the approved
  paint's at the same surface points; curves only, nothing spatial from the old paint). Measured on the surface
  (`scripts/tone_compare.py`) in the colours the game shows, approved -> final, whole surface: Lobber tier A 147/75/41 sd
  43.8 -> 146/78/42 sd 45.1; Ice Lobber 119/145/170 -> 120/145/170; Pod A 132/55/51 -> 131/54/52; Pod B 107/37/8 -> 105/37/8;
  Pod C 112/125/156 -> 109/122/154. The Lobber's limbs and stalk first drifted browner (G 88.9 -> 78.7 on the yellow class),
  fixed with `--push orange=0.98,1.11,1.0 --push yellow=0.98,1.09,1.0` (G 86.0).
- **Ramps.** Tier A errors stay in line with the approved build: Lobber flesh 14.4 -> 13.3, green 9.1 -> 10.0, mouth 5.4 ->
  7.2, violet 2.7 -> 2.6; pod flesh 15.4 -> 16.6, green 7.2 -> 6.9, mouth 15.8 -> 11.8, violet 10.7 -> 9.4. The flesh regions
  remain above the 10-level guide, as approved; no region was split.
- **Known flaws.** Meshy painted a thin orange stroke across the upper arms at the bend (2 texels wide, inside the charts on all
  four arm charts), visible only close up. The Cast clip's arm zigzag is in the approved clip, not new.

**Root weights, second pass** (`scripts/root_limbs.py`, hardened `detached_parts_audit.py`). Weights only, so the repaint
stays valid: `scripts/verify_same_mesh.py` uv_v3 -> uv_v4 reports max vertex move 0.0, max UV difference 0.0.
- Upper arms: `XCarm01` parted 40.8 mm (Death frame 24, 78/268 poses). The cap stayed in the head (0.4 mm) but the rod above
  the surface hung fully on XCbase/XCpiv, which ride Xmouth, while the surface there is about half Xjaw, so its base
  lifted 4-6 cm. The head's weights now run up the exposed rod and fade out at J1, on both sides.
- Mouth tendril `Xheadpiv` (20 cm, 62 tris, -x side): 16.0 mm off in Cast frame 11. It was rigid on Xheadpiv/Xhead while its
  mirror twin rides Xjawpiv and stays attached; it takes the twin's weights.
- Audit, 5 detached -> 3: both are gone at 30 and 48 fps. Left, not part of the request: `XApivot` and `XApivot01` lower limbs
  (9.2 / 9.1 mm, 7 and 4 of 268 poses) and the 10-tri `Xheadmid` piece (4.9 mm, 5 poses). The pod has 0 detached.

**Checks.** Winding 0 inverted on both; `run_creature_review.py check` 14 switches, `check_viewer.mjs` on `review/viewer_pod/`
27 switches, 0 failed; flat-shading 0.00 on both; floor audit Lobber A/B/C, Ice Lobber A/B ok; regression
`mm9_actor_models_build_every_binding` (`--world mm9`) 65 descriptors on 31 models, 0 failed; gates loop seams 0, Dead/Death
p99 1.66 -> 1.78, max 5.0 -> 4.0 (`review/gates_lobber_texpass.json`). No in-game run. Viewer presets in `review/viewer*/review.js`
are retuned to these bodies. Accepted from review-viewer shots at identical cameras: `review/texpass_lobber_closeups_sheet.png`,
`review/texpass_lobber_body_sheet.png`, `review/texpass_pod_closeups_sheet.png`, `review/texpass_pod_body_sheet.png` (shots in
`review/texpass/`, `review/texpass_pod/`; the pod's come from the wrapper's `viewer_shots.mjs` directly, as the wrapper reaches only
`review/viewer/`). Root fix in the viewer: `review/shots/rootfix_death24.png`, `rootfix_cast11.png`. Before state: `work/before_texpass/`.

## Deviations and open points

- Upright Lobber and its wilt death (above). The MM9 root `HidePiece` is not reproduced (the bulb stays).
- Pod launch by the Lobber and the pod's flight clips are not reproduced; unused MM9 clips (Lobber AwareAir,
  FidgetAir2, winceAir1, fall1, falldown1; pod taunt, wince2, Backpedal, BackpedalRun, static_model, projectile,
  land) are not exported.
- Meshy's pod body is rounder with a shorter beak than MM9's; the pod's arm tips are slightly crumpled from the fit.
- Tier A of the pod: the magenta shell reads a little pinker through its ramp (four hue regions are the limit).
- The descriptor table gives every row height 199 / radius 112 (also the knee-high pod); not changed here.
- User artistic acceptance: not recorded.

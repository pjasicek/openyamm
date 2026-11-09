# MM9 Jellyspore family (mm9_jelly) — 3D model, 2026-10-30

The floating spore jellyfish of MM9 (`mm9/extracted/MODELS/MODELS/JELLYSPORE.abc`: octagonal bell on eight rib chains,
four jointed legs, a stinger with three spikes; 34 joints, 260 triangles) for the MM9 world, built on the MM9 rig-reuse
route of `../mm9_dfly_claude/` and `../mm9_lobber_claude/` (new HD Meshy mesh weighted to the original MM9 skeleton,
the MM9 clips played with only the listed fixes). Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Descriptors / skins | MM9 Jellyspore A `jelly_a` (Jellyspore, JELLYSPORE1), B `jelly_b` (Gelatinous Spore, JELLYSPORE2), C `jelly_c` (Nettle Spore, `NettleSpore.spr` = the eight animated JELLYSPOREBANI frames, mean) |
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_jelly.glb` (cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, scale 100 (= MM9 size; MONSTERS.txt `Scale` 1 for all three) |
| Triangles LOD0/1/2/3 | 5,903 / 2,950 / 1,061 / 352 |
| Clips (30 fps) | Standing 1.5 (standwater), Walking 1.2 (swim), Running 0.87 (swim x1.38), Fidget 2.0 (fidgetwater), AttackMelee 1.0 (hattackwater1), AttackRanged 1.5 (Hattackwater2), Hit 0.8 (wincewater1), Death 2.1 (wincewater2 + collapse), Dead 1.0 |
| Events | attack_melee impact 0.666 s (MM9 `Rattack`), attack_ranged impact 0.441 s (first MM9 `Lattack`); no missile (Projectile 0) |
| Floor | swimmer rule since 2026-11-04 (Fly `YS`): MM9's origin at the centre of the MM9 body box, +0.6656 m on the living clips (`floor_fix.py --swim`), Death eases into the corpse on the floor; before it the flier rule (+1.3991 m) |
| Meshy credits | **15 / 35** (Smart Topology 5, retexture 10; backup account) |

## Decisions

- **Water clips.** MM9 has only water clips for this body (standwater, awarewater, fidgetwater, swim, hattackwater1/2,
  wincewater1/2, jellysetup). Built as a flier (Fly Y, `BaseSwim.scr`; the engine had no swimming), since
  2026-11-04 a swimmer ("Binding: a swimmer" below): standwater = Standing, swim = Walking (and Running at x1.38,
  26 whole frames so the loop closes), hattackwater1/Hattackwater2 = the two attacks, wincewater1 = Hit.
  Unused: awarewater, wincewater2 (used inside Death), jellysetup (a static setup pose).
- **Death is ours.** JELLYSPORE.abc has no death clip. Death = MM9 wincewater2 (the recoil), then limp into the
  closed-bell pose of fidgetwater at 1.2 s while XCENTER tips over sideways 82 degrees with a gravity ease-in, a small
  bounce and settle; the body sinks with the tip angle so the corpse lies on its side on the floor (`build_export.py`).
- **Tiers by ramps.** The MM9 B/C bell is iridescent (purple darks, lavender-blue mids, teal lights); one luminance
  ramp per region cannot hold that, so B/C get a violet-blue bell with purple darks. Nettle Spore's animated skin
  (white "nettle" flicker over the bell) is not reproduced; C uses the mean of its eight frames and reads like B.
  MM9's `Transparent 1` (see-through jelly) is not reproduced: the engine draws actors opaque.

## Route

0. **HD masters** (`references_hd/`, Codex via `claude_shared/codex_slot.sh`, two runs): MM9 renders of the tier-1
   model (`mm9_views_tier1.png`), skin x4, top view; brief `CODEX_BRIEF.md`; records `generation_runs.json`,
   `selected_views_review.png`. 1024x1536. Gate: 00 accepted (bell a little taller than MM9, one of the three node
   spikes hidden); 01-04 consistent.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/jelly_smart_v1.json`): good bell and four legs;
   the stinger's lower half came back as a short detached piece, offset in depth.
2. **Fit** (`scripts/fit_jelly.py`): uniform scale from the bell width, yaw so the four leg tips lie on the MM9 leg
   directions, bell tops aligned; separate legs by arc length in parallel-transported frames, the leg grown out of the
   stalk by per-segment skinning; the stalk onto Xtailpiv -> Xtail; the detached stinger piece onto Xtail -> XtailA ->
   XtailB -> MM9 tail tip (stretch 2.1, so the needle reaches the MM9 length). `work/fit_sheet.png`.
3. **Weights** (`scripts/rig_body.py jelly`): nearest MM9 vertex label (chain vertices from their own chain only; core
   vertices up in the bell only from the MM9 bell), 30 diffusion iterations (soft rib transitions), the bell's
   underside shell copies the weights of the top shell at the same azimuth/relative radius (the two shells fold
   together when MM9 inverts the bell), spikes rigid on Xtail, collar rings on XCENTER. `work/rigposes_sheet*.png`.
4. **Reduce** (`scripts/reduce_body.py 0.38 0.35`), **UV** (`scripts/uv_export.py jelly`: Smart UV, bell islands
   x1.5), **retexture** from 01/03/02/04 with our UVs (`requests/jelly_retexture_v1.json`).
5. **Clips** (`scripts/clips_mm9.py` JELLY, run by `scripts/build_export.py`): MM9 key poses as PCHIP curves at 30 fps,
   loop seams closed, Death built as above, Dead = last pose.
6. **Textures** (`scripts/compose_jelly.py`): 2K graded base (`grade_basecolor.py`, AO `bake_ao.py`), 1K normal, 1K ORM.
   Regions are structural: R bell (both shells), G the "red joints" (collar, collar rings, leg roots, lower stinger:
   red in B/C), B the rest of the legs, A stalk/upper stinger/spikes (`dump_uv3d.py` with `DUMP_GROUPS`). Tier colours
   per region from the MM9 skins projected onto our texels through the fitted bind pose (nearest MM9 surface point;
   `work/mm9_projected_tiers.png`), the bell from the MM9 bell's upward faces; per-luminance-band mean hue with the
   texels' own saturation restored. Tier A identity (HD look). `review/jelly_texture_classes_tiers.png`,
   `work/tiers_sheet.png`.
7. **Roots** (`scripts/root_parts.py`, 2026-10-30, on the UV blend): the bell's underside gathers onto the stalk
   top (MM9's neck weights), the Xarmpiv02 leg root stretched into the stalk (see the dated section below).
8. **Runtime** (`scripts/build_runtime.sh [--install]`): prepare -> LODs -> shadow shrink -> `region_variants.py`
   (specular 0, metallic 0) -> floor pass (hover, corpse grounding) -> winding check (0 inverted).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_jelly_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
for t in 1 2 4; do $V $C $M/JELLYSPORE.abc $P/source/tier$t --id jelly$t --texture 0=$S/JELLYSPORE$t.dtx --scale 0.0256; done
$V $C $M/JELLYSPORE.abc $P/source/nettle --id nettle --texture 0=mm9/extracted/SPRITETEXTURES/SPRITETEXTURES/JELLYSPOREBANI1.dtx --scale 0.0256
# work/nettle_frames/f1..f8.png: decode_dtx() of JELLYSPOREBANI1..8 (see creature_3d_progress.json)
$B $P/scripts/mm9_rig_source.py $P/source/tier1/jelly1.glb $P/work/mm9_jelly.blend 0 0
$B $P/scripts/fit_jelly.py $P/work/mm9_jelly.blend $P/meshy/jelly_smart_v1/model_urls_glb.glb $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_body.py $P/work/fit_v1.blend jelly $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.38 0.35
$B $P/scripts/uv_export.py $P/work/reduced_v1.blend jelly $P/work/uv_v1.blend $P/texturing/jelly_body_upload.glb
# (retexture_v1 was made on this upload)
$B $P/scripts/bake_ao.py $P/work/uv_v1.blend Body $PWD/$P/textures/jelly_ao_2k.png 0.03 2048
DUMP_GROUPS=XCENTER,XtailB,XtailD,Xarmpiv,Xarmpiv01,Xarmpiv02,Xarmpiv03,XarmA,XarmA01,XarmA02,XarmA03 \
  $B $P/scripts/dump_uv3d.py $P/work/uv_v1.blend $P/work/uv3d_jelly.npz Body
$B $P/scripts/dump_uv3d.py $P/source/tier1/jelly1.glb $P/work/uv3d_mm9_jelly.npz bell.mesh:1 arm.mesh:2 arm01.mesh:2 arm02.mesh:2 arm03.mesh:2 arm04.mesh:3 spike.mesh:3 spike01.mesh:3 spike02.mesh:3
python3 $P/scripts/compose_jelly.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/jelly_ao_2k.png $P/textures/jelly_basecolor.png && python3 $P/scripts/compose_jelly.py
$B $P/scripts/root_parts.py $P/work/uv_v1.blend $P/work/roots_v1.blend $P/work/roots_v1.json
$B $P/scripts/build_export.py $P/work/roots_v1.blend $P/work/anim_v2.blend $P/export/mm9_jelly_lod0.glb $P/work/clips_v2.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
python3 $P/scripts/viewer_tiers.py jelly && python3 $P/scripts/make_viewer_manifest.py r2_jelly_rootfix_20261030 \
  "jelly_a=Jellyspore (A)=$P/review/viewer/jelly_a.glb" "jelly_b=Gelatinous Spore (B)=$P/review/viewer/jelly_b.glb" "jelly_c=Nettle Spore (C)=$P/review/viewer/jelly_c.glb"
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (3 tiers x 9 clips): `tools/run_creature_review.py --project ... check` 0 errors, 27
  switches; shots `review/shots/`, `review/viewer_shots_sheet.png`.
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0 (Standing, Walking, Running 0.015 m before the
  whole-frame Running rate, 0 after); edge ratio p1/p99 0.43-0.70 / 1.4-5.6 (max 12.7) since the root fix (before it
  0.42-0.64 / 1.4-7.9, max 58.9: part of that was the underside centre swinging across the cap, below); the rest is
  MM9's own bell rib scale keys (the bell inverts and swells to about twice its rest size in swim/fidget/attack).
- Floor audit `floor_audit.py --world mm9`: Jellyspore A/B/C ok (flier). Regression `mm9_actor_models_build_every_binding`
  (`--world mm9`): 48 descriptors on 19 models, 0 failed. Winding: 0 inverted closed parts.
- In game (Isle of Ashes, `tools/run_game.sh` minimized, private `--user-data` folder with
  `start_in_main_menu=false`, `start_map_file=isleofashes.odm`, `immortal=true` and the one-shot `menu_input_tour_path`;
  tour `review/ingame_tour.yml`): `review/ingame_sheet.png` (the map's own Jellyspore over the sea and spawned
  Gelatinous / Nettle Spores as 3D actors, attacking), `review/ingame_sheet2.png`, `review/ingame_models_sheet.png`
  (static models: attack, Death to the corpse lying on its side at the water level). `actor damage last` did not kill
  the spawned actor in view, so the actor death is checked on the static model and in the viewer.

## Bell and leg rooted in the stalk (2026-10-30)

`claude_shared/detached_parts_audit.py` (`claude_shared/detached_parts_mm9.md`): in Fidget the bell lifted off the
stalk and its legs, two legs left the bell in AttackMelee, one leg root stood off the stalk at bind.

- **MM9 first.** MM9's own Jellyspore (`source/tier1/jelly1.glb`, the same audit at 30 fps over all its clips,
  fidgetwater included): 9 components, 0 detached in any pose. Its bell mesh has a neck: the underside runs from a
  ring on Xbellpiv01-07 at the collar (y 0.285, plus the collar ring on XCENTER/Xtailpiv) through a ring on XbA* to the
  XbC* rim and never uses XbB*; when MM9 inverts the bell the neck stays on the collar and the bell becomes a funnel.
  So the separation was ours, not MM9's pulsing.
- **Cause.** `rig_body.py` gives our underside shell the weights of the top shell at the same azimuth and relative
  radius, so its centre (where the stalk enters, 0.4 m below XbB) rode the cap bones XbB*. When the bell inverts those
  bones turn about 180 degrees and the underside centre swung up with them: the stalk (with the Xarmpiv01 leg grown
  out of it, the stinger and the spikes) was cut off by up to 24.7 cm (Fidget 0.30 s; Walking/Running 21.2 cm,
  AttackMelee 10.9 cm). The audit's Xarmpiv and Xarmpiv03 flags (92.4 / 79.6 mm in AttackMelee) were that same break:
  with the stalk cut off, each leg's middle passing the bell rim was the nearest link. Separately, the Xarmpiv02 leg
  (a separate piece) stopped 1.5 cm short of the stalk in every pose (15.3 mm at bind, 15.8 mm in Walking).
- **Fix** (`scripts/root_parts.py` on the UV blend, so UVs, the retexture and the textures stay valid; no Meshy spend;
  AO not re-baked). Underside: by relative radius rho from the stalk axis the weights blend from MM9's neck bones
  (Xbellpiv*, by azimuth, rho <= 0.15) to its XbA* ring (0.30) and back into the shell's own weights (0.70 and out);
  333 of its 532 vertices, bind pose unchanged. In the inverted poses the underside now gathers into a short neck on
  the stalk top (a short version of MM9's funnel); the cap, the rim and the upright poses move as before. Leg:
  Xarmpiv02's first segment stretched along its root bone's axis into the stalk (4.0 cm to the surface along the axis,
  2.0 cm deep, stretch 1.40, 63 vertices moved only along the axis), its root weights blended to the stalk's at the
  entry point (Xtailpiv 0.59, Xbellpiv01/03 0.40). `work/roots_v1.json`. Clips unchanged (`work/clips_v2.json` =
  `clips_v1.json`).
- **Checks.** Detached-parts audit of the installed GLB at 30 and 48 fps: 0 detached (was 4); the six stinger spikes
  stay "only just attached" (-2.6 to +0.9 mm on Xtail, as before). Triangles 5,903 / 2,950 / 1,061 / 352 (LOD1 one
  fewer). Hover unchanged (+1.3991 m), `floor_audit.py --world mm9` Jellyspore A/B/C ok, winding 0 inverted,
  flat-shading 0.00 (as before), `run_creature_review.py check` 27 switches 0 errors (viewer revision
  `r2_jelly_rootfix_20261030`), regression `mm9_actor_models_build_every_binding` (`--world mm9 --headless-run-regression-suite actors`) PASS, 49 descriptors on 20 models, 0 failed. Sheets:
  `review/rootfix_worstframes_mm9_before_after.png` (MM9 | before | after at Fidget 0.30, AttackMelee 0.30/0.37,
  Walking 0.47 s), `review/rootfix_leg_before_after.png` (the Xarmpiv02 root at bind and in Walking). The pre-fix
  export is kept in `work/before_rootfix/`.

## Binding: a swimmer (2026-11-04)

The engine swims since 2026-11-02 (`devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md`): the row's Fly cell is `YS`
(`generate_mm9_monster_tables.py` SWIMMER_SOURCES), so a spore that starts in a scene water volume flies in it, bound
to it (its body box's centre kept between bed and surface), and flies elsewhere.

- **Where the model sits.** The engine draws model y = 0 at the actor's feet (the bottom of its body box) and keeps the
  box centre in the water. MM9's object position is the centre of its Dims (16, 26, 16 LT for jellysetup; our height
  133 = 2 x 26 x 2.56). So the living clips carry MM9's origin at half the box height, **+0.6656 m**
  (`scripts/build_runtime.sh`, `floor_fix.py --swim 0.6656 Death Dead`): a spore centred where MM9 put it is drawn
  where MM9 draws it, its legs and stinger hanging up to 0.73 m below the box as MM9's do. The flier hover (+1.3991 m,
  the lowest living point on the floor) drew it 0.73 m higher, its bell out of the water at Isle of Ashes' MM9 spots.
  MM9's clips are unchanged (one constant offset). Death eases from the lift into the corpse lying on the floor
  (no floor clamp on the way: it starts in the water); the corpse then sinks to the bed.
- **Placement.** `../../projects/mm9r_common/outdoor_blv.py` `swimmer_foot`: foot = MM9 position - height / 2, kept
  under the surface and over the seabed.
- **Bathhouse** (three spores on dry floors, MM9 Gravity 1): no variant. They fly there (YS); a flier aims its body at
  the party's head, so in a fight the stinger stays about 0.4 m over the floor. Placed or parked on the floor, legs and
  stinger reach about 0.5 m into it, which is MM9's own relation (MM9 sets the box on the floor, MoveToFloor 1).
- **Checks.** `check_winding` 0 inverted; `floor_audit.py --world mm9` (new kind `swimmer`: living clips not judged,
  death not judged, corpse on the floor) Jellyspore A/B/C ok; viewer revision `r3_jelly_swim_20261104`,
  `run_creature_review.py check` and `check_viewer.mjs` 27 switches, 0 errors. The pre-swim export is in
  `work/before_swim/`. In game: `../../projects/mm9r_isleofashes_blv/README.md` "Swimmers".

## Deviations and open points

- Death is a constructed clip (MM9 has none); iridescent B/C bell and the Nettle Spore flicker are approximated by
  ramps; MM9 transparency not reproduced (above).
- Meshy's bell is lower than MM9's; the inverted-bell poses show the two shells (top and dark underside) as a double
  rim. Meshy gives five thin node spikes instead of MM9's three.
- The descriptor table gives height 267 / radius 144; not changed here.
- User artistic acceptance: accepted 2026-10-30 ("jellyspore - good").

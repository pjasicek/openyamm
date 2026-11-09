# MM9 Bird family, the crow (mm9_crow) — 3D model, 2026-10-30

The MM9 crow (`mm9/extracted/MODELS/MODELS/CROW.abc`, 28 joints, 158 tris, 13 clips) for the three MM9 rows named
"Bird": Bird A (9093, L9), Bird B (9094, L13, Air missile), Bird C (9095, L17, Fire missile). Built on the MM9
rig-reuse route of `../mm9_dfly_claude/` and `../mm9_lobber_claude/` (fit and weights from `../mm9_wolf_claude/`):
a new HD Meshy crow weighted to the original MM9 skeleton, the MM9 clips played with only the listed fixes.
Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_crow.glb` (cooked copy in `assets_dev`), skins `crow_a` (crow, Bird A) and `crow_b` (eagle from BIRD.dtx, Bird B/C) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_crow_claude`: MM9 Bird A/B/C, scale 100/125/150 (100 x MONSTERS.txt `Scale` 1/1.25/1.5) |
| Triangles LOD0/1/2/3 | 7,467 / 3,732 / 1,341 / 553 (body 4,482, grafted head and neck 2,985) |
| Skeleton | the MM9 one, names unchanged (`XCENTER`, `Xbody`, neck `Xneckpiv/XneckB/XneckA`, `Xheadpiv`, `Xhead`, `Xbeak`, `Xjawpiv` (unused), wings `Xwingpiv-Xwbase-Xwmid` (+01), tail `Xback`, `Xtailmid`, `Xtailside` (+01), legs `Xlegpiv-Xleg-Xfoot-Xtoe` (+01)) + `Socket_Mouth` |
| Clips (30 fps) | Standing 0.4 (fly), Walking 0.4 (fly), Running 0.3 (fly x 4/3), Fidget 2.0 (fidgetAir1), AttackMelee 0.47 (HattackAir1, also the missile), Hit 0.53 (winceair1), Death 1.83 (dieair1 + fall1 + falldown1), Dead 1.0 |
| Events | bite / missile release 0.299 s (MM9 `bite` of HattackAir1), released from `Socket_Mouth` (beak tip) |
| Floor | flier rule: hover +0.4252 baked in the living clips (the hanging feet at the lowest wing-down frame of Hit meet the floor), eased out over Death, corpse grounded; `floor_audit.py --world mm9` ok |
| Meshy credits | **40 / 40** (backup account): Smart Topology 5, retexture v1 10, 4K retexture v2 10, head Smart Topology 5, 4K head retexture 10 |

## Decisions

- **Crow and eagle, size tiers.** All three Bird rows name `crow.dtx` (Bird C names a missing `drow.dtx`; MM9 then
  uses the model default `crow.dtx`, `devdocs/mm9/MM9_MONSTER_LEGACY_SPRITE_MAPPING.md`). User decision 2026-10-30:
  Bird A stays the crow (`crow_a`), Bird B and C take MM9's unused eagle skin `BIRD.dtx` (`crow_b`) through the
  region mask (R plumage, G beak, B eyes, A legs) and ramps; see "Head, feet and texture pass" below.
- **Meshy wings kept.** Smart Topology returned thin feathered wing and tail sheets (separate primaries in the
  geometry), so the dragonfly's own-leaf wings were not needed. Wings and legs are posed onto the MM9 chains by the
  wolf's transient-skinning fit (`scripts/fit_bird.py`); the tail fan takes barycentric weights of the MM9 tail
  triangle under each vertex (`scripts/rig_body.py`), so it spreads as in MM9 (MM9's own tail is asymmetric:
  `Xtailside01` carries most of the fan).
- **Beak closed.** MM9's lower mandible (`Xjawpiv`) is merged into `Xbeak`: the HD beak is one closed piece and
  opening it would tear the cutting edge; the bite reads as a peck.
- **Roles.** A flier hovers with the flap loop (`fly`) for Standing and Walking; Running plays it 4/3 faster (0.3 s,
  whole frames so the loop stays closed); the missile rows reuse HattackAir1 (MM9 has no ranged clip for the bird):
  `attack_ranged: AttackMelee`, `cast: AttackMelee`, release from the beak at the bite. The perched clips
  (`stand`, `fidget1`) are not used.
- **Shadow LODs.** Wing and tail sheets are a few millimetres thick: the shadow shrink skips vertices dominated by
  wing and tail joints (`scripts/shrink_shadow_lods.py`).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_crow_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
$V $C $M/CROW.abc $P/source/crow --id crow --texture 0=$S/CROW.dtx --scale 0.0256   # also bird (BIRD.dtx)
$B $P/scripts/mm9_rig_source.py $P/source/crow/crow.glb $P/work/mm9_crow_rig.blend 0 0
$B $P/scripts/fit_bird.py $P/work/mm9_crow_rig.blend $P/meshy/crow_smart_v1/model_urls_glb.glb $P/work/fit_v2.blend $P/work/fit_v2.json
$B $P/scripts/rig_body.py $P/work/fit_v2.blend $P/work/rig_v2.blend $P/work/rig_v2.json
$B $P/scripts/reduce_body.py $P/work/rig_v2.blend $P/work/reduced_v2.blend $P/work/reduced_v2.json 0.3 0.5 0.5
$B $P/scripts/uv_export.py $P/work/reduced_v2.blend crow $P/work/uv_v2.blend $P/texturing/crow_body_upload.glb
# (retexture_v1 was made on this upload; superseded by the texture pass below)
$B $P/scripts/repose_head_feet.py $P/work/uv_v2.blend $P/work/uv_v3.blend $P/work/repose_v3.json \
  $P/work/mm9_crow_rig.blend                     # 2026-10-30 head/feet repair (same topology and UVs)
$B $P/scripts/uv_atlas_v4.py $P/work/uv_v3.blend $P/work/uv_v4.blend $P/texturing/crow_body_upload_v2.glb \
  $P/work/uv_v4.json    # xatlas packs differently per run: never re-run once the upload went to Meshy (retexture_v2)
python3 tools/creature_meshy.py --project $P --token $T submit --job crow_retexture_v2 --kind retexture \
  --request requests/crow_retexture_v2.json --credits 10      # then poll / download
$B $P/scripts/repose_head_feet.py $P/work/uv_v4.blend $P/work/uv_v5.blend $P/work/reweight_v5.json \
  $P/work/mm9_crow_rig.blend mode=weights throat=1 throat_from=0.012 throat_to=0.05   # second head pass (weights only)
# head rework (2026-10-30): Codex head turnaround references_head/, head-only Smart Topology head_smart_v1 (5 cr)
$B $P/scripts/graft_head.py $P/work/uv_v5.blend $P/meshy/head_smart_v1/model_urls_glb.glb $P/work/mm9_crow_rig.blend \
  $P/scripts/graft_config.json $P/work/graft_v6.blend $P/texturing/crow_head_upload.glb $P/work/graft_v6.json
#   the head UVs are packed by xatlas, which differs per run: head_retexture_v1 (10 cr) was painted on this exact
#   upload, so never re-run the graft without re-doing the head retexture (protected copy: work/head_v6_retextured_on.blend)
python3 tools/creature_meshy.py --project $P --token $T submit --job head_retexture_v1 --kind retexture \
  --request requests/head_retexture_v1.json --credits 10      # then poll / download
# graft_v6 -> close_holes -> neck_fair -> maps -> export -> runtime (no install) -> viewer tiers:
TOKEN=$T $P/scripts/rebuild_neck.sh -0.01 0.125
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \
  python3 $P/scripts/bind_actors.py mm9_crow_claude $P/work/actors_block.yml
(cd $P && python3 scripts/viewer_tiers.py && python3 scripts/make_viewer_manifest.py r10_crow_20261030 \
  "crow_a=Bird A (crow)=review/viewer/crow_a.glb" "crow_b=Bird B / C (eagle, BIRD.dtx)=review/viewer/crow_b.glb")
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (own title, three.js from `mm6_goblin/review_20261006/vendor/`):
  `tools/run_creature_review.py check` 1 skin x 8 clips, 0 console errors. The viewer frames the small bird far
  away; Blender clip frames of the delivered GLB: `review/blender_clip_sheet.png`.
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 per clip 0.64-0.75 / 1.45-1.91;
  extremes (max 6.2) on small edges at the wing roots, where MM9 translates the wing pivots.
- Floor audit `floor_audit.py --world mm9`: Bird A/B/C ok. Regression `mm9_actor_models_build_every_binding`
  (`--world mm9`): 49 descriptors on 20 models, 0 failed. Winding: 0 inverted.
- In game (Ravensford `bootcamp.odm`, `tools/run_game.sh` minimized, private `--user-data` folder as in
  `../mm9_wolf_claude/README.md`; tour `review/crow_tour.yml`, `exit: true`): `review/ingame_sheet.png` — spawned Bird
  A/B/C as 3D actors flapping over the valley floor and diving at the party. The tour's static models and the final
  death fell outside the camera. `menu_input_tour_path` is one-shot: rewrite it into settings.ini before every run.

## Deviations and open points

- Bird B/C are the eagle (user decision, not MM9's own colours); the eagle's lighter golden nape is a pattern the
  four-region ramps cannot carry, so the eagle is evenly dark brown with a pale beak tip and yellow legs.
- The 4K paint still flecks the plumage (compressed by the tier ramps); the wing tops are softer than the
  `05_wings_top.png` master (only front/left/back/right views go to Meshy).
- MM9 `lunge`/`flap` events are not reproduced (clips in place); the second death set (dieair2, fall2, falldown2)
  and winceair2 are not exported.
- User artistic acceptance: not recorded (head/feet/texture pass and eagle tier pending review).

## Head, feet and texture pass (2026-10-30)

User feedback: in flight the head hung under the chest "upside down" with a pinched throat (white slivers), the feet
looked upside down (soles up, toes curled up like an upturned hand), and the texture was blurry and blotchy.

**What MM9 does.** The bones and clips were never wrong: our skeleton plays MM9's channels and the mesh followed the
bones (head direction within 2 deg of the bone prediction). MM9 binds the head with the beak 59 deg below horizontal
and its flight clips raise it 51 deg (fly), 71 (HattackAir1), 85 (winceair1) and up to 141 (dieair1) relative to the
body, spread over XneckA (15), Xheadpiv (27) and Xhead (15) in fly. It never turns the head over; its own 158-triangle
head is rigid per bone. MM9's feet are closed pointed diamonds that trail straight back in flight (Xleg ~50 deg,
Xfoot ~75-85 deg); a diamond has no sole or curl.

**Head: cause and fix.** The Meshy skull is larger and sits further back than MM9's, so the nearest-MM9-vertex labels
gave the crown and nape to XneckA, the skull to Xheadpiv, the beak to Xbeak and nothing to Xhead. In flight the beak
turned 42 deg more than the crown: the skull folded into a block under the chin with the beak coming out of its
bottom, which read as an upside-down head, and the throat creased. The Meshy bind head also pointed its beak 15-24
deg higher than MM9's. `scripts/repose_head_feet.py` (a stage after `uv_export.py`; same topology and UVs) makes the
skull and eye pieces rigid on Xhead, keeps Xbeak for the beak with a softened Xbeak/Xhead border, blends the neck
XneckA -> Xheadpiv -> Xhead along the neck axis, and turns the head down to MM9's bind direction (skull -> beak tip,
23.6 deg about the skull base, blended over the neck). Measured with `scripts/head_angles.py` (landmarks fixed in the
bind pose, every clip at 48 fps, ours against MM9's mesh at the same time; max over the clip):

| Clip | MM9 head turn | beak direction vs MM9 before -> after | head fold before -> after |
|---|---|---|---|
| Standing / Walking / Running | 51 | 23 -> 3 | 24 -> 3 |
| Fidget | 51 | 25 -> 4 | 25 -> 5 |
| AttackMelee | 71 | 24 -> 5 | 34 -> 4 |
| Hit | 85 | 26 -> 7 | 24 -> 5 |
| Death | 141 | 30 -> 11 | 33 -> 12 |

(fold = change of the skull's own beak/crown angle; a rigid head keeps 0.) Neck/head edge gate
(`scripts/region_gate.py`): flight loops min edge ratio 0.80 -> 0.52 (the neck now takes the bend the skull used to
fold; the pinch at the beak hinge went from 0.08 to 0.47 after softening the border), Death throat 0.49 -> 0.40,
AttackMelee 2 folded triangles at the throat for a few frames.

**Feet: cause and fix.** The toes point where MM9's diamond points (12 deg before, 23 after), but the Meshy foot is a
perching grip whose plantar side faced back in the bind pose; MM9's flight swings the tarsus back ~135 deg, which turns
it up. Each foot is rolled 180 deg about its knee -> toe-tip line, ramped in by surface distance along the tarsus from
the knee (every cross-section turns as one; the hind toe sticking back from the ankle turns fully with the foot), so
the sole faces forward in the bind pose and down in flight, the claws hooking down. Weights are unchanged.

**Texture pass** (`../claude_shared/TEXTURE_QUALITY_PASS.md`): xatlas UVs on the repaired mesh
(`scripts/uv_atlas_v4.py`, head charts x2), a 4K Meshy retexture on them (`crow_retexture_v2`, same four HD masters,
10 credits), colour downsampled 4K -> 2K once, AO re-baked, gentle grade (fine 1.0, local 0.3, AO 0.5, contrast 1.06,
saturation 1.15: the default grade raised the 4-16 px blotch band from 0.051 to 0.070, the gentle one to 0.059).
`texture_quality.py`: atlas 52.1 -> 58.3 %, equivalent 1478 -> 1564 px, density p50 1997 -> 2029, spread 1.14 ->
1.11, islands 479 -> 184, fragments 5.3 -> 2.7 % of the surface, stretch p90 1.31 -> 1.28, and a 4K source instead of
2K. The 4K paint flecks the black plumage with pale specks, so the plumage ramp of tier A compresses luminance above
the region's 75th percentile (soft knee, 0.35). Tier-A ramp errors 1.6-2.1 levels.

**Eagle tier** (user decision): `crow_b` for Bird B/C from BIRD.dtx. BIRD.dtx was painted for another layout (on
CROW.abc's UVs its legs fall on black), so `compose_crow.py` samples each region from the skin art itself (feathers,
the beak triangles, the amber eye, the yellow leg strip) and transfers it by luminance rank (our detail order, the
eagle's colours at 1.35x albedo; upper plumage ranks at half rate against speckle). Ramp errors: plumage 1.7, beak
2.3, eyes 1.7, legs 8.8 levels. One shared texture set; the tiers differ only in ramps.

**Checks.** Winding 0 inverted; LODs 5,239 / 2,618 / 943 / 328 with the shadow shrink skipping wing/tail sheets;
flat-shading 0.00; gates `review/gates.json` (loop seams 0); floor audit Bird A/B/C ok (hover +0.4252 unchanged);
`run_creature_review.py check` 2 skins x 8 clips, 0 console errors; regression `mm9_actor_models_build_every_binding`
49 descriptors on 20 models, 0 failed; `detached_parts_audit.py` 0 detached. Binding: Bird A `crow_a`, Bird B/C
`crow_b`. No in-game run for this pass.

Sheets: `review/head_feet_before_after.png` (MM9 / before / after, worst head frame per clip side and front, feet in
Standing and Hit), `review/texture_tiers_before_after.png` (MM9 crow, Bird A before/after, MM9 BIRD.dtx, eagle on the
old and the new paint). Before files: `work/before_headfix/`, `work/before_texpass/`.
Meshy credits this pass: 10 (project total 25 / 35).

### Second head pass: "still upside down?" (2026-10-30)

User, on the installed model: "head is still rotated 180 degrees? upside down?" (flight, side, slightly from below).
`scripts/head_angles.py` now also measures the head's lateral axis (ours: eye to eye; MM9: Xhead's rotation applied
to the body lateral), the head-up axis and the full orientation against MM9 per frame. There is no roll at any
stage (max over the clip, deg):

| Clip | roll vs MM9: original / 1st fix / now | full head orientation vs MM9: original / 1st fix / now |
|---|---|---|
| Standing / Walking / Running | 4 / 7 / 7 | 23 / 7 / 7 |
| Fidget | 10 / 8 / 8 | 27 / 8 / 8 |
| AttackMelee | 6 / 7 / 7 | 24 / 8 / 8 |
| Hit | 9 / 10 / 10 | 27 / 11 / 11 |
| Death | 9 / 11 / 11 | 30 / 13 / 13 |

The beak's curve also bows to the crown side in every flight frame (the hook points down; the screenshot's tip hooks
down too when zoomed). What read as upside down was the throat: the Meshy crow looks down in the bind pose, so its
throat lies between the beak base and the chest, inside the region the first pass made rigid on Xhead. When MM9 raises
the head ~55 deg, that throat swung under the beak as a hanging chin (37 mm below the beak base in fly frame 0), with
the eye on the beak line and a flat front above it: a chin where a crown should be. Tried and rejected: turning the
skull up about the beak base (`scripts/lift_skull.py`, kept for reference: it tore the face) and moving the skull
border back (bumpier). Fix: `repose_head_feet.py mode=weights throat=1` on uv_v4 (weights only, the retexture stays
valid): the throat below the eyes and behind the beak base blends from Xhead at the beak base to Xheadpiv/XneckA
1.2-5 cm behind it, so it bends with the neck; the skull and beak stay rigid. In flight the head now slopes from the
beak into the neck with the crown above (`review/head_roll_flight_loop.png`). Neck gate (`scripts/region_gate.py`):
flight min edge ratio 0.43 (was 0.52), Hit 0.24, Death/AttackMelee 0.25-0.26 with 3 folded throat triangles for a few
frames. Rebuilt, reinstalled; viewer check 2 skins x 8 clips 0 errors, viewer playback recorded
(`review/playback/`), floor audit ok, regression 49/20 0 failed, winding 0, flat 0.00, detached 0. No Meshy spend.

### Head rework: a new head (2026-10-30)

User review with a reference (a real raven in flight, `references_head/input_raven_reference.png`): our head was a
boxy flat skull with a crest flap, a long thin wading-bird beak (about 2.5x the head length, no depth at the base), a
ragged cluster around the eye, and a flap under the throat; in flight the head read as a small block on the front of
a flat body. The geometry was Meshy's full-body head, so no weighting could fix it: the head was replaced (the
Winged Mutant's option c). Meshy credits: **15** (head Smart Topology 5, 4K head retexture 10; project 40 / 40,
limit raised from 35 for this pass).

1. **References.** Codex head turnaround `references_head/` (brief `CODEX_BRIEF.md`; inputs: the raven, MM9 crow head
   renders `mm9_head_views.png`, the MM9 skin): profile, three-quarter, front and top of a level raven head with a
   domed crown, a short deep hooked beak, the eye just above the gape and a smooth throat, cut at the neck
   (`selected_views_review.png`, `generation_runs.json`).
2. **Model.** Head-only Smart Topology from `00_three_quarter.png` (`requests/head_smart_v1.json`).
3. **Graft** (`scripts/graft_head.py`, `scripts/graft_config.json`, report `work/graft_v6.json`): the old head, its
   eyes and the old beak cut off in front of a plane across the neck (2.5 cm along the XneckB -> XneckA line from
   Xneckpiv); the Meshy head's inner lining (it was double-walled, joined at the mouth slit) removed by ray escape,
   the mouth closed, the shell decimated to 0.25 (symmetric); scaled from the neck's width, turned so its beak axis
   (gape corner -> tip) lies on MM9's bind beak axis, its gape corner on MM9's Xbeak joint (the beak points where MM9's
   does); its neck stub joined to the body by a 5-ring loft along a Hermite curve (the neck is 3.5 cm longer than the
   cut, the head sits forward). Weights: skull, beak and eyes rigid on Xhead (the closed HD bill does not nod with
   Xbeak); the neck stub and the loft take the MM9 neck bone whose segment they lie on (Xneckpiv, XneckB, XneckA,
   Xheadpiv by their neck coordinate, blended between segment centres), the skull's back blended in over 1.7 cm, the
   body ring's own weights faded out over 1.2 cm. The mouth socket sits at the beak tip on Xhead.
4. **Texture.** The head part (head, loft, the body ring copy) has its own UVs (xatlas, 1K, 56 % use, 44 islands,
   0.5 % fragments) and material `CrowHead`; 4K Meshy head retexture on that upload with the four head views
   (`requests/head_retexture_v1.json`). `compose_crow.py` builds the 1K head set (`crow_head_basecolor.png`, normal,
   metal/rough), darkens Meshy's pale silver bill to grey-black horn (x0.4 linear), matches the head plumage to the
   body neck's median luminance (gain 0.51) and fades the body neck into the head's paint over 5 cm
   (`crow_basecolor_final.png`). Region mask `crow_head_region_mask.png`: R plumage, G beak, B eyes; the eagle tier
   `crow_b` recolours the head through the same ramps (head ramp errors: plumage 1.5 / 3.2, beak 1.0 / 1.6, eyes 1.7 /
   8.0 levels for crow / eagle). The body lost its beak and eye regions (neutral ramps there).

**Acceptance** (`review/head_rework_acceptance.png`: the raven, the user's two framings before and now, a 3/4 front,
the eagle tier; `review/head_silhouette_vs_raven.png`):
- Profile against the raven (mirrored, scaled and turned by the beak base -> eye; head length = 2 x beak base ->
  eye): beak / head **1.04** (raven 1.07; gape -> tip / head 1.28); beak base depth / beak **0.55** (raven 0.31). By this
  head-length proxy both birds fall just under the 1.1-1.6 window; the beak's length matches the raven's.
- Orientation (`scripts/beak_axis_gate.py`, `scripts/head_angles.py`, every clip at 48 fps): roll against MM9's Xhead
  1-7 deg; beak axis against MM9's beak axis max 6 deg in the flight loops, 6 AttackMelee, 9 Hit, 10 Fidget, **21
  Death** (MM9 nods its Xbeak up to 20 deg in the death; our bill stays with the skull). The eye -> tip direction
  differs from MM9's by a constant 22 deg because our eye sits above the gape (anatomy, not a turn).
- Folded triangles near the neck (`scripts/region_gate.py`): flight loops **3** (crown, 0.5-10 mm^2), Hit 4, Fidget 5,
  AttackMelee 6, Dead 7, Death 9 (throat and neck sides when MM9 bends the head far past its bind pose). Not zero.
- Gates `review/gates.json`: edge ratio p99 now 2.3-3.1 (was 1.3-1.9), max 12.6 in Death: the loft is bent in the bind
  pose (the bind head looks down as MM9's) and stretches straight in flight.
- Winding 0 inverted; flat-shading 0.00 on both materials; detached parts 0; `run_creature_review.py check` 2 skins x
  8 clips, 0 errors (viewer revision r5, playback recorded in `review/playback/`); floor audit Bird A/B/C ok;
  `mm9_actor_models_build_every_binding` 49 descriptors on 20 models, 0 failed. No in-game run.


**Neck patch and head tone (2026-10-30, no Meshy spend).** (Corrected below: the claim first written here, that the pale patch was only a Workbench artefact, was wrong; the
review viewer showed it too.) Fixed in `compose_crow.py`: the head looked darker and
smoother than the speckled body. The head plumage now takes the body plumage's colours by luminance rank (the body's
neck and shoulders 3-15 cm from the neck ring; 85 % transfer), keeping its own feather pattern, so its tone, blue tint
and pale flecks match the body; the 5 cm fade of the body neck into the head stays. Tier-A head plumage ramp error
0.5 levels, eagle 2.9. `review/head_rework_acceptance.png` re-rendered in EEVEE with the PBR maps (viewer revision r6);
viewer check 2 skins x 8 clips 0 errors, floor audit ok, regression 0 failed, flat-shading 0.00.

### Neck, throat, pale blotches and the wing hole (2026-10-30, viewer revisions r9-r10, no Meshy spend)

The review viewer is the acceptance test; every finding below comes from it.

- **Collar and throat step (r9).** The pale collar was shading, not paint: a solid red head tier still showed it,
  because the shading normals came from the bent bind surface. The step was the loft being narrower than chest and
  head. `scripts/neck_fair.py` solves a biharmonic surface over 583 vertices in the fly pose (max move 82 mm, mean
  24 mm), takes positions back through each vertex's skinning matrix and stores normals computed on the faired fly
  surface. The seam fade now darkens with `min` instead of averaging (the average gave a pale band).
- **Pale blotches (r10).** Screenshot 56: a jagged pale grey patch with the feather normals in it. It is specular,
  not paint. The atlas under those faces is dark (tier texels on the wings and the neck are no paler than the rest);
  the plumage roughness was 0.45-0.7 ("glossy black"), and on black paint nearly all the light is the specular lobe,
  so any patch of the low-poly shell facing a light flares. A debug tier with body roughness 0.9 removed the pale
  panels on the wings and back on the same camera. The exact frame of 56 was not reproduced: 56's silhouette keeps
  the throat step, so it predates r9, and no r9 or r10 shot from that side shows a breast patch. The nearest match
  is the near wing around fly 0.03 s. Tested and ruled out as causes: raw Meshy head paint on the loft, a wider
  averaged seam fade, and the installed 12:03 model. `compose_crow.py` now maps plumage roughness to 0.82-0.92, body
  and head. The engine's `fs_model` uses the same GGX lobe and the same map, so viewer and game share the cause. A
  mild sheen stays on the near wing's upper face around 0.03 s.
- **Wing hole (r10).** Screenshot 57: a 9-edge opening in the -X wing root (bind pose around (-0.08, 0.07, 0.15),
  about 6 cm2 on screen in flight). `graft_head.py` made it: the bisect at the neck plane also caught the wing leading
  edge beside the neck and `clear_outer` removed that piece (absent from `work/before_headfix`). The wing is a closed
  shell with a single-sided material, so one hole shows the background through the culled lower surface. Eight other
  older openings on the wings and body came from the Meshy mesh and its reduction, the largest near (0.33, 0.04, 0)
  at 15 cm2. `scripts/close_holes.py` fills all nine (41 triangles, no new vertices, report `work/close_holes.json`);
  each filled triangle folds over its rim edge and reuses the rim's painted UVs. The two remaining boundary loops at
  the mouth stay, and some pinched loops leave 1-3 edge remnants. A front-faces-only scan (42 camera directions, 8+
  poses per clip) finds no see-through pixels in the fly loop, and two remnants of 0.2-0.3 cm2 in Death and
  AttackMelee at the -X wing (-0.39, 0.05, 0.02).

Checks on r10, installed: viewer check 2 skins x 8 clips, 0 failed; flat-shading 0.00; winding 0 inverted; floor audit
Bird A/B/C ok; roll 1-7 deg; beak axis against MM9 6 flight, 6 Attack, 9 Hit, 10 Fidget, 21 Death; `region_gate` neck
folds 7 in flight, 15 Attack, 9 Death, 9 Fidget, 7 Hit, up from 3-9 before the fairing, none visible in the shots.
Regression `mm9_actor_models_build_every_binding` reports no crow failure; its failures are other agents' models
caught mid-install (Goose, then Fish). Non-manifold edges rose from 11 to 26 with the pinched fills.
In game (Ravensford, `--isolated`): Bird A seen from the front and from above with no blotch and no hole
(`review/ingame_r10_bird_a.png`); Bird B never came into frame, so the eagle in game is checked by the binding only.
Sheets: `review/neck_wing_fix_viewer_crow_a.png`, `review/neck_wing_fix_viewer_crow_b.png` (8 views x 5 flap times).

User artistic acceptance: r10 accepted 2026-10-30 ("bird is good").

# MM9 Terror family (mm9_terror) — 3D model, 2026-10-30

The MM9 tunnel Terror (`mm9/extracted/MODELS/MODELS/TERROR.abc`, 51 joints): a huge fanged head-mouth on two legs,
no arms, six head tentacles (two horn-like tentacles out of the top, two long arching tentacles ending in small
mouths, two short ones under the cheek eyes). For the MM9 world: Amphibious (237), Desert (238) and Reptilian Terror
(239) (`tools/mm9_import_discovery/mm9_monster_families.yml`; not the Banshee row 164 "Terror"). A biped, but not a
humanoid: no arms or hands, so the MM9 rig-reuse route of `../mm9_dfly_claude/` and `../mm9_lobber_claude/` applies
(new HD Meshy mesh weighted to the original MM9 skeleton, the MM9 clips played). Progress, hashes and receipts:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_terror.glb` (installed; cooked copy in `assets_dev`), skins `terror_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`: MM9 Terror A/B/C → `terror_a/b/c` (TERROR1/2/3.dtx), scale 100 (MONSTERS.txt `Scale` 1) |
| Triangles LOD0/1/2/3 | 8,441 / 4,220 / 1,511 / 492 (7,557 / 3,777 / 1,351 / 439 before the 2026-10-30 head fix) |
| Texture (2026-10-30 pass) | 2K base colour from a 4K Meshy paint on xatlas UVs: 60.1 % of the atlas, 179 islands, 1,057 texels per creature size (median) |
| Clips (30 fps) | Standing 1.33 (stand), Walking 1.07 (walk), Running 0.67 (run), Fidget 2.3 (fidget1), AttackMelee 1.2 (Hattack1), AttackRanged 1.0 (Hattack2, the second melee attack), Hit 1.4 (wince1), Death 1.3 (die1), Dead 1.0 |
| Events | melee impact 0.491 s (MM9 `Rattack`, Hattack1), second attack impact 0.4995 s (MM9 `Lattack` 0.506 s in the 1.013 s Hattack2, resampled to 1.0 s); no missile, no cast |
| Gait | stride 1.03 (walk), 1.1 (run): fore-aft travel of the feet (`scripts/gait_measure.py`) |
| Meshy credits | **25 / 35** (Smart Topology 5, retexture v1 10, 4K retexture v2 10 for the texture pass; backup account) |

## Decisions

- **Not a humanoid stop.** The Terror is two-legged but has no arms or hands (MM9 clavicles only, no arm chains), so
  the humanoid playbook's hand problems do not arise; its tentacles are MM9 bone chains like the Lobber's limbs.
- **attack_ranged** plays Hattack2: the Terror has two physical attacks and no missile (`basemelee.scr`).
- **Tiers**: four hue regions on our texture (red: mouth, tongue, eyes; green: skin; blue: belly, tentacle bands;
  bone: pale teeth and claws, few texels), each tier takes its MM9 skin's chroma by luminance percentile.

## Route

0. **HD masters** (`references_hd/`, Codex, two runs): renders of the MM9 model with TERROR1 (`mm9_views_tier1.png`,
   `mm9_top_tier1.png`, skin ×2 to 512), brief `CODEX_BRIEF.md`; `selected_views_review.png`. Known limits: faint
   alpha haze, tight margins, slightly oblique side views.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/terror_smart_v1.json`): one-piece body with all
   six tentacles, separate teeth and eyeballs (`work/meshy_sheet.png`).
2. **Rig source** (`scripts/mm9_rig_source.py`, lift 0.0526), **global fit** (`scripts/align.py`), **tentacle fit**
   (`scripts/fit_terror.py`): each Meshy tentacle tip (local maximum of the chest geodesic nearest the MM9 tip) and
   centreline, cut nearest the MM9 chain root, the root moved halfway to the MM9 root; segment skinning onto the
   MM9 chain (the tip segment unstretched, so the mouth cups keep their shape) inside a capsule of the tentacle's
   mid radius, faded to rest across the cut plane (root zone) and the capsule bound. Legs: soles lowered onto the
   floor (tapered to zero at the hip). Overlays `work/fit_sheet.png`, chain colours `work/ch_sheet.png`.
3. **Weights** (`scripts/rig_body.py terror`): nearest MM9 vertex label per chain (tentacles and legs only from
   their own bones), diffusion with the jaw bones (Bone35–41) held, teeth/eyes rigid, 4 influences.
4. **Reduce** (`scripts/reduce_body.py 0.48 0.5`), **UV** (`scripts/uv_export.py terror`: head islands ×1.4),
   **retexture** from 01/03/02/04 with our UVs (`requests/terror_retexture_v1.json`).
5. **Clips** (`scripts/clips_mm9.py` via `scripts/build_export.py terror`): PCHIP at 30 fps, loop seams closed
   (walk 8.1°, run 16.1° on the calves before; 0 after), the frames span each source duration exactly.
6. **Textures** (`scripts/compose.py terror`), **runtime** (`scripts/build_runtime.sh terror`), install
   (`tools/install_model.py --world mm9`) and binding (`scripts/bind_actors.py`) as for the Basilisk
   (`../mm9_basilisk_claude/README.md`).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_terror_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
C=tools/mm9_import_discovery/convert_abc_model.py; M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS
for t in 1 2 3; do $V $C $M/TERROR.abc $P/source/terror$t --id terror$t --texture 0=$S/TERROR$t.dtx --scale 0.0256; done
$B $P/scripts/mm9_rig_source.py $P/source/terror1/terror1.glb $P/work/mm9_terror_ground.blend 0 0.0526
$B $P/scripts/align.py $P/work/mm9_terror_ground.blend $P/meshy/terror_smart_v1/model_urls_glb.glb $P/work/align_v1.blend $P/work/align al
$B $P/scripts/fit_terror.py $P/work/align_v1.blend $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_body.py $P/work/fit_v1.blend terror $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.48 0.5
$B $P/scripts/uv_export.py $P/work/reduced_v1.blend terror $P/work/uv_v1.blend $P/texturing/terror_body_upload.glb
# (retexture_v1 was made on this upload)
# head fix (2026-10-30): eyes, UV overlap, mouth cavity -> uv_v2.blend + work/head_fix.json
$B $P/scripts/head_fix.py $P/work/uv_v1.blend $P/work/uv_v2.blend $P/work/head_fix.json
$B $P/scripts/dump_uv3d.py $P/work/uv_v2.blend $P/work/uv3d_terror.npz Body
$B $P/scripts/dump_uv3d.py $P/source/terror1/terror1.glb $P/work/uv3d_mm9_terror.npz "The Terror.mesh:1"
python3 $P/scripts/head_fix_tex.py terror        # Meshy maps -> work/retexture_v2 (squeeze, repaint, cavity paint)
$B $P/scripts/bake_ao.py $P/work/uv_v2.blend Body $PWD/$P/textures/terror_ao_2k.png 0.03 2048
python3 $P/scripts/compose.py terror && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/terror_ao_2k.png $P/textures/terror_basecolor.png && python3 $P/scripts/compose.py terror
$B $P/scripts/build_export.py $P/work/uv_v2.blend terror $P/work/anim_v2.blend $P/export/mm9_terror_lod0.glb $P/work/clips_v2.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh terror --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 $P/scripts/bind_actors.py $P/work/binding.yml "MM9 Terror A" "MM9 Terror B" "MM9 Terror C"
python3 $P/scripts/viewer_tiers.py terror && python3 $P/scripts/make_viewer_manifest.py r2_terror_20261030 \
  "terror_a=Amphibious Terror (A)=$P/review/viewer/terror_a.glb" "terror_b=Desert Terror (B)=$P/review/viewer/terror_b.glb" "terror_c=Reptilian Terror (C)=$P/review/viewer/terror_c.glb"
python3 $P/scripts/seat_check.py $P/export/mm9_terror.glb $P/review/seat_check_20261030.json   # eyes, teeth, mouth
```

`head_fix.py` and `head_fix_tex.py` above are the approved v2 route. The current maps come from the texture pass below,
which continues from `uv_v2.blend`; its one-time steps and rebuild are in that section.

## Checks (2026-10-30)

- Viewer `review/viewer/` (3 tiers × 9 clips, three.js from `../mm6_goblin/review_20261006/vendor/`):
  `tools/run_creature_review.py check` 0 console errors, 27 switches, 0 failed; shots `review/viewer_shots_sheet.png`
  (before the head fix; rerun 2026-10-30 after it: same result).
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 per clip 0.60–0.68 / 1.5–2.4;
  extremes (min 0.02, max 7.7) on small edges at the tentacle roots and jaw corners when MM9 swings the head.
- Floor audit `floor_audit.py --world mm9`: 40/40 ok. Regression `mm9_actor_models_build_every_binding` (`--world
  mm9`): 40 descriptors on 16 models, 0 failed. Winding: 0 inverted closed parts.
- In game: `../mm9_basilisk_claude/review/ingame_sheet.png` (Ravensford `bootcamp.odm`, `tools/run_game.sh`
  minimized, private `--user-data`; tour `../mm9_basilisk_claude/review/ingame_tour.yml`): the static Amphibious
  Terror model standing, walking, both attacks, Death and the corpse; spawned Desert and Reptilian Terror actors
  attacking the party, the Reptilian's death.

## Head fix after the user review (2026-10-30)

User screenshots: an upper eye out of its socket, green shards in the blue belly/crotch, a smeared flat mouth
interior when the jaw opens wide (AttackMelee ~29, AttackRanged ~27, viewer frames at 48 fps). Scripts:
`scripts/head_fix.py` (Blender, on the UV'd master), `scripts/head_fix_tex.py` (texture carry-over and paint),
`scripts/seat_check.py` (numbers), `scripts/fix_shots.py` + `scripts/fix_sheet.py` (sheet). No Meshy or Codex spend.

**1. Eye out of its socket.** Cause: `rig_body.py` makes small pieces rigid with the weights of their single nearest
body vertex. The upper eye on the creature's right took the horn tentacle's root bone (Bone05 0.97), its socket half
Bone05 / half Bone38, so the eyeball slid out whenever the tentacle moved (worst Death 40: 0.113 m, 1.5 eyeball
radii). The cheek eye on the left was Head 1.0 in a socket with 14 % lower jaw (AttackRanged 27: 0.076 m). Fix: each
eyeball and its socket (body vertices within 1.45 eyeball radii, fading out by 2.2) take one anchor weight set, the
socket's mean without tentacle-chain bones: upper eyes Bone37 / Bone38 (upper jaw), cheek eyes Bip01 Head.

**2. Belly shards.** Cause: Smart UV Project flattens each island onto one plane, so long islands folded over
themselves: 160 face pairs shared 9,014 texels at 2K, and Meshy painted one surface into both (the long tentacles'
tips over the crotch and the left hip). Fix: per pair the face whose 3D neighbourhood colour differs most from the
shared texels loses; the 71 losing faces (13 islands, one turned 90 degrees) move into a band at the top of the atlas
(every other island squeezed to v x 0.9: axis-aligned, so the normal map stays valid) and are repainted
(29,546 texels) from the clean surface around them in 3D (inverse-distance mean colour plus mirrored skin detail
from a clean patch next to them): their Meshy paint was also a dark smear, those faces are hidden in every reference
view. Region mask and ramps are rebuilt from the repainted base as before.

**3. Mouth interior.** Cause: the Meshy cavity was 272 large faces and its lip rim and palate carried lower-jaw and
head weights all around (nearest MM9 vertex labels), so the upper lip and palate were torn between the jaws: texel
stretch max 5.0 (p99 4.0) inside, and the lips around it 11.7x their bind size. Fix: the cavity (faces inside the
elliptic cylinder through the teeth roots, minus the forward-facing lip fronts) is replaced by a bag: the inner lip
loop (38 vertices, smoothed), 14 rings x 40 columns following the old cavity wall (rays from the mouth axis) to the
throat, closed by a strip cap; 1,156 triangles. Weights: a fan around the mouth axis (upper jaw Bone37 above,
lower jaw Bone35 below, blended over the corners), the roof blending toward the head at the throat; the same fan
re-splits the jaw share of 262 lip/face vertices within 0.3 m and fully re-weights 101 within 0.15 m. Own atlas
island (573 x 186 texels at 2K, 300 texels/m): u around the mouth (seam under the tongue), v along the depth, laid
out at the reference MM9 pose Hattack2 frame 7.52 (gum-line gap 0.761 m; widest 1.142 m at Hattack2 14, bind 0.476),
the lip strip solved by LSCM. Paint from the Meshy mouth's own colours (76k texels, sorted by luminance): gums at the
lip, palate ridges, a tongue-bed groove, folds at the corners, darkening to a near-black throat cap. Teeth and the
tongue are rigid with the gum weights at their root.

| Check (all clips, 48 fps) | Before | After |
|---|---|---|
| Eyeball off its socket, worst eye | 0.113 m (1.51 radii, Death 40) | 0.000 m |
| Tooth root off its gum (rigid fit / root-to-gum gap growth) | 0.178 m / 17 mm | 0.062 m / 7 mm |
| Tongue root off the floor | 0.125 m | 0.002 m |
| Mouth interior texel stretch, max / p99 | 5.02 / 3.96 | 2.49 / 1.97 (AttackRanged 27); AttackMelee 2.28 / 1.75 |
| Lips and face around the mouth, posed/bind, max / p99 | 11.7 / 4.0 | 4.5 / 3.0 (max at a cheek tentacle root in Death) |
| Detached parts (`claude_shared/detached_parts_audit.py`) | mouth piece 9.1 mm off | 0 detached |
| UV texels painted twice | 9,014 | 0 |

`review/seat_check_20261030.json` and `review/seat_check_before_20261030.json` hold the per-clip numbers. Gates:
edge ratio p99 now 1.6-3.1 (AttackRanged 3.07; was 1.5-2.4): the cavity is laid out for a half-open mouth, so its
edges stretch against the bind pose while its texels stay within 2x. Sheet (all tiers, before/after, user framings):
`review/fix_before_after_20261030.png`. Triangles: LOD0 7,557 -> 8,441 (cavity +884), LODs 4,220 / 1,511 / 492.

## Texture quality pass (2026-10-30)

`../claude_shared/TEXTURE_QUALITY_PASS.md`, brief `../claude_shared/MM9_TEXTURE_PASS_BRIEF.md`. Mesh, weights and clips are
unchanged: LOD0 triangles identical (0.0 m), skin weights identical at all 4,290 positions (max delta 0.0), clip keys
identical (delta 0), same nodes and joints, LODs 8,441 / 4,220 / 1,511 / 492. **10 Meshy credits** (4K retexture v2, backup
account); creature total **25 / 35**.

- **UVs** (`scripts/uv_atlas_v3.py`, run on `work/uv_v2.blend`, the head-fixed master): xatlas charts, head x1.4 as before.
  The squeeze and the top band are gone. The mouth bag stays out of the charts and keeps head_fix.py's unwrap, laid out at a
  half-open reference pose (a bind-pose chart would lose the 2x texel bound at the widest opening): it joins the packing as
  its own island by wrapping `uv_atlas`'s pack call, 1.52x denser than before (456 texels/m, the head's density). The
  relocated faces simply rejoin the body charts.
- **Layout repairs** (`scripts/uv_fix_v3.py`, before the upload, keeping the 19-minute pack): the throat cap's planar UVs were
  near-degenerate (7 zero-area triangles, one sliver thrown across the atlas), so its ring sits on a circle in free space;
  one chart corner moved 2 texels to clear a 15-texel fold. `scripts/uv_gates.py`: 0 texels painted twice (26 before, 9,014
  before the head fix), 0 zero-area triangles. **Never re-run these two scripts: the paint is bound to this layout.**
- **Retexture v2** (`requests/terror_retexture_v2.json`): same four HD masters, `meshy-7`, 4K, our UVs; the returned GLB
  reports the same layout.
- **Maps** (`scripts/texpass_tex.py`): every map 4K -> 2K once (Lanczos), then the cavity paint rebuilt from the same palette
  (the approved mouth's colours, from the v1 paint) and the same recipe in the bag's rectangle at the new density, carried
  into the atlas per triangle with the normal vectors turned with the island (180 degrees here). `--refill` repaints the
  relocated faces as the head fix did; it was **not needed**: with no shared texels the crotch and hips are clean.
- **Grade** gentle (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`), AO re-baked on the new UVs.
- **Red drift.** The fresh paint has red slashes on the chest and hips and flecks on the tentacles, and compose picks regions
  by hue, so 5-6 % of the approved green and blue skin took the red ramp. `scripts/approved_on_new.py` resamples the approved
  class map onto the new layout (same mesh, same triangles) and `compose.py` lets the red region grow only within 4 texels
  of it; `bone` stays hue-based, because the paint moves the pale tentacle spots. Ramps stay fitted by luminance.

| Measure (`texture_quality.py`, LOD0) | Before | After |
|---|---|---|
| Atlas use (2K) | 39.3 % | **60.1 %** |
| Equivalent fully used square | 1,283 px | 1,588 px |
| Texels per creature size p10 / p50 / p90 | 774 / 880 / 1,216 | **1,011 / 1,057 / 1,474** (+20 % median) |
| Density spread p90/p10 (head x1.4 by design) | 1.57 | 1.46 |
| Islands / surface on fragments | 548 / 7.3 % | 179 / **0.1 %** |
| UV stretch p90 (rest pose) | 1.54 | 1.14 |
| Fine detail, high-pass RMS inside the islands | 12.3 | 18.2 (x1.48) |
| Blotch band 4-16 px | 19.5 | 16.4 (x0.84) |
| Tier-A ramp error red / green / blue / bone | 13.7 / 10.3 / 7.8 / 11.4 | 14.6 / 9.9 / 8.1 / 5.3 |
| Meshy source | 2K | 4K on 60 % (3,175 px equivalent) |

**Checks.** Winding 0 inverted; `run_creature_review.py check` 0 console errors, no failed switches (revision
`r3_terror_texpass_20261030`); flat-shading 0.01 as before; detached parts 0 (18 components); floor audit 3/3 ok; gates loop
seams 0, extremes unchanged (0.02-7.7); regression `mm9_actor_models_build_every_binding` (`--world mm9`) passed, 65 descriptors on 31 models, 0 failed. `seat_check.py` now measures over welded positions, and `--texpass` finds the cavity
through `work/uv_v3_bag.npz`: mouth interior stretch 2.49 / p99 1.97, the same as before the pass. The same script on both
builds (`review/texpass_20261030/seat_check*.json`, before -> after): eye 0.001 -> 0.000 m, tooth rigid fit 0.101 -> 0.101 m,
tongue root 0.006 -> 0.004 m. Geometry and weights are identical, so these small differences are only which of the split
vertices the sets pick. The welded sets raise the tooth figure against the 0.062 m in the head fix table, so compare only
like with like; the script's lip rows differ per build (their filter depends on vertex order) and are not a comparison.

**Accepted from review-viewer shots:** `review/texpass_viewer_sheet.png` (tiers A/B/C, before | after, identical viewer
presets; shots in `review/texpass_viewer/`). Density heatmaps on one scale (880 texels = green):
`review/texpass_20261030/heat_{before,after}_density.png`. No in-game run. Before state: `work/before_texpass/`.

**Known drift:** the lips read a little brighter and redder on tier A (region mean 134/32/18 -> 140/37/24) and pinker on tier
B; the pattern of black spots and scales is Meshy's new paint, not the approved one, in the same places by region.

Rebuild from the existing paint, never the UV scripts:
```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_terror_claude
# one-time, already done, bound to the Meshy paint:
#   $B $P/scripts/uv_atlas_v3.py $P/work/uv_v2.blend $P/work/uv_v3.blend $P/texturing/terror_body_upload_v2.glb $P/work/uv_v3.json
#   (keep as uv_v3_packed.blend, uv_v3_bag_packed.npz) then
#   $B $P/scripts/uv_fix_v3.py $P/work/uv_v3_packed.blend $P/work/uv_v3.blend $P/texturing/terror_body_upload_v2.glb \
#      $P/work/uv_v3_bag_packed.npz $P/work/uv_v3_bag.npz $P/work/uv_v3_fix.json
#   python3 tools/creature_meshy.py --project $P --token $T submit --job terror_retexture_v2 --kind retexture \
#      --request requests/terror_retexture_v2.json --credits 10      # then poll / download
$B $P/scripts/dump_uv3d.py $P/work/uv_v3.blend $P/work/uv3d_terror_v3.npz Body
$B $P/scripts/bake_ao.py $P/work/uv_v3.blend Body $PWD/$P/textures/terror_ao_2k.png 0.03 2048
python3 $P/scripts/approved_on_new.py terror work/uv3d_terror.npz work/uv3d_terror_v3.npz
python3 $P/scripts/texpass_tex.py && python3 $P/scripts/compose.py terror && python3 $P/../claude_shared/grade_basecolor.py \
  --ao $P/textures/terror_ao_2k.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 \
  $P/textures/terror_basecolor.png
TOKEN=$T $P/scripts/rebuild_texpass.sh --install     # compose, export, runtime, viewer tiers, shots
```

## Deviations and open points

- Unused MM9 clips (fidget2, wince2, die2, Taunt, Backpedal, BackpedalRun, static_model) are not exported; the
  `lunge` events are not reproduced (clips in place). Walking and AttackRanged are resampled 1.6 % / 1.3 % slower /
  faster to whole frames.
- The tentacle roots sit halfway between the Meshy and MM9 positions (up to ~0.15 m off the MM9 pivots); the long
  tentacles are stretched about 1.3× onto the MM9 chains.
- Teeth in tiers B/C take a slightly pink tint (few texels reach the 'bone' region).
- Head fix: a few corner triangles of the cavity reach 2.3-2.5x texel stretch at the widest opening (p99 under 2). The
  band, the squeeze and the synthesised crotch/hip skin ended with the texture pass above.
- User artistic acceptance: accepted "terror - ok" (2026-10-30, after the head fix).

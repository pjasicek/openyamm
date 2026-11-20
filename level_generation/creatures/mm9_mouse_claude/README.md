# MM9 mouse (mm9_mouse) — 3D model, 2026-10-30

The MM9 ambient mouse (`mm9/extracted/MODELS/MODELS/MOUSE.abc`, 7 nodes, 54 triangles, 3 clips) for the MM9 world:
mouse (row 299, Type "mouse A", descriptor `MM9 299 mouse`) and evil mouse (row 300, "mouse C", `MM9 300 evil mouse`).
Built on the MM9 rig-reuse route of `../mm9_dfly_claude/` and `../mm9_wolf_claude/`: a new HD Meshy mesh weighted to the
original MM9 skeleton, the MM9 clips played with only the listed changes, plus one thing MM9 never had: legs.
Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_mouse.glb` (cooked copy in `assets_dev`), skins `mouse_a`, `mouse_c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_mouse_claude`, scale 100 (100 x MONSTERS.txt `Scale` 1), `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` rows 299 (legacy zrat A, 472), 300 (zrat C, 474) |
| Triangles LOD0/1/2/3 | 4,735 / 2,367 / 852 / 282 (LOD0 head 1,819, body 1,308, paws 716, tail 556, eyes 336) |
| Skeleton | the MM9 one, names unchanged: `Bone05` body, `Bone08` neck, `Bone06` snout, `Bone01-03` tail; ours: `LegFL`, `LegFR`, `LegHL`, `LegHR` (one bone per paw under `Bone05`) |
| Clips (30 fps) | Standing 2.5 (stand), Walking 0.43 (run x0.51, body motion 40 %), Running 0.23 (run, 7 frames), Fidget 2.4 (stand + look-around, ours), Hit 0.5 (ours), Death 1.03 (die + paws curl), Dead 1.0 |
| Events | none: the mouse never attacks (cat.scr), `attack_melee`/`attack_ranged` play Fidget as on Yrsa |
| Gait | stride 0.009 (walk), 0.024 (run) model units per clip, the paws' real travel; `gait_rate: [0.5, 2.0]` |
| Floor | ground rule; the tail chain bends up first (`--lift-joints`, tail joints only); `floor_audit.py --world mm9` ok |
| Meshy credits | **15 / 30** (backup account): Smart Topology 5, 4K retexture 10 |

## Decisions

- **There are no mouse skins.** `mouse1.dtx` and `mouse3.dtx` are named in MONSTERS.txt but exist nowhere in the game
  data, and `MOUSE.abc` is placed in no DAT world or script (a string search of all 45 DATs and every `.scr`). So the
  brief's question whether the evil mouse's skin differs in design has no answer in MM9: there is nothing to compare,
  and the model was never textured in any build we have. The HD masters take only pose and proportions from MM9's
  untextured model. The colours are a design choice: `mouse_a` a grey-brown house mouse with a cream belly, `mouse_c`
  a charcoal coat, dusky skin and dark ruby eyes, as ramps on one shared skin. MM9's "evil mouse" differs in data
  only by `Special 1` and 2D4 instead of 2D3.
- **Legs are ours.** MM9's mouse is a legless blob that slides. An HD mouse needs paws, and MM9 has no bones for
  them. Each paw gets one bone under `Bone05`, placed per frame in armature space (`scripts/mouse_clips.py`):
  stance paws fixed on the floor, swing paws lifted in an arc that rides up with the hop. The short stub between paw and
  belly blends paw -> body and stretches with it. Tried first and dropped: three-bone legs with IK, which crumpled
  the hind foot (no pole, a bend the skin cannot follow); `scripts/merge_leg_bones.py` carried the UV'd mesh over.
- **Two strides per run clip.** MM9's run lifts the body 8 mm twice per 0.22 s (two hops), so the paws land at both
  low points. Walking plays the same clip at half rate with `Bone05` at 40 %, a diagonal walk.
- **Speed.** MM9's RunVelocity 175 is 448 world units per second on a 26-unit mouse, 17 body lengths a second, against
  0.1 model units a second authored. Strides stay honest and `gait_rate` caps the clip at 2x: the paws slip at
  full speed, which is a blur at game distance, rather than strobing at 40x.
- **Own tail.** Meshy's tail curled off the centre line, and mirroring would have doubled it. The body is cut on the rump
  and a tube continues from the cut loop (one manifold surface) through the MM9 tail joints, lying on the floor. It
  keeps MM9's S-curve bind, so the clips swing it about the right pivots.
- **Own eyes.** Meshy left shallow pits. Two bead spheres sit in them, 62 % sunk, with their socket's weights.
- **Mirror.** MM9's body is symmetric, the Meshy body was not: the creature's right
  half (the side the three-quarter master shows) is mirrored about x = 0, seam smoothed.
- **Fur strokes replace the Meshy ripple.** The 4K paint had the right colours but turned fur into a high-contrast
  zebra or fingerprint pattern in the viewer. `scripts/fur_detail.py` keeps its low frequencies (blurred per island,
  then in a 3D grid, so no chart edge or long body triangle shows) and replaces the ripple with hair strokes: line
  integral convolution of noise along a snout-to-tail flow field, kept to 3.2 mm on every chart through each
  triangle's UV map. The normal map takes the same split. Tail and paws keep the Meshy paint. No extra credits.
- **Nose.** Meshy painted the whole muzzle-end chart pink, a hard patch. Only the tip (4.5 mm) stays in the skin
  region; the rest takes the fur ramp and strokes.
- **Tiers.** Regions R fur, G skin (tail past its furred root, paws, inner ears, nose tip), B eyes. Tier A identity
  (ramp error fur 2.8, skin 4.4, eyes 1.8 levels). The tail's fur root fades over `tail_t` 0.10-0.16.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_mouse_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
$V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/MOUSE.abc $P/source/mouse --id mouse --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/mouse/mouse.glb $P/work/mm9_mouse_rig.blend 0 0.0165
$B $P/scripts/fit_mouse.py $P/work/mm9_mouse_rig.blend $P/meshy/mouse_smart_v1/model_urls_glb.glb $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_mouse.py $P/work/fit_v1.blend $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/reduce_mouse.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 1500 1900 800 600
$B $P/scripts/uv_atlas_mouse.py $P/work/reduced_v1.blend $P/work/uv_v1.blend $P/texturing/mouse_body_upload.glb $P/work/uv_v1.json
# (retexture_v1 was made on this upload: xatlas packs differently per run, never re-run it. uv_v1 still had the
# three-bone legs; work/uv_v1b.blend comes from scripts/merge_leg_bones.py. rig_mouse.py now makes one bone directly.)
$B $P/scripts/merge_leg_bones.py $P/work/uv_v1.blend $P/work/uv_v1b.blend
HEAD_GROUPS=Bone08,Bone06 JAW_GROUPS=Bone06 $B $P/scripts/dump_uv3d.py $P/work/uv_v1b.blend $P/work/uv3d_mouse.npz Body
$B $P/scripts/bake_ao.py $P/work/uv_v1b.blend Body $PWD/$P/textures/mouse_ao_2k.png 0.01 2048
python3 $P/scripts/compose_mouse.py && python3 level_generation/creatures/claude_shared/grade_basecolor.py \
  --ao $P/textures/mouse_ao_2k.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.0 \
  $P/textures/mouse_basecolor.png && python3 $P/scripts/compose_mouse.py
$P/scripts/rebuild_after_textures.sh $T <revision> --install   # export, runtime GLB, viewer GLBs and manifest
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \
  python3 $P/scripts/bind_actors.py mm9_mouse_claude $P/work/actors_block.yml
```

Rows 299/300 also needed two small generator changes in `generate_mm9_monster_tables.py`: an empty `Recovery` (both
mouse rows) reads as 0, and row 300's stray `1` under a second attack with Att% 0 maps to no projectile.

## Checks (2026-10-30)

- Viewer `review/viewer/` (own title, rescaled to the mouse: `focuses`, grid, camera near plane):
  `tools/run_creature_review.py check` 2 skins x 7 clips, 0 console errors. Playback stills in `review/playback/`.
- Acceptance sheets are viewer shots (`scripts/final_shots.sh`, `scripts/close_shots.sh` for below and close cameras),
  each inspected: `review/sheets/mouse_a_body.png`, `mouse_a_legs.png`, `mouse_a_closeup.png`, `mouse_c_tier.png`, and
  `mouse_mm9_vs_ours.png` (the MM9 row is Blender: MM9 has no skin and no viewer).
- Head (`scripts/head_angles.py`, `review/head_angles.json`, joint rotation from rest against MM9 at 48 fps, snout / up
  max degrees): Standing Bone06 0.84 / 0.78 (MM9 turn 20.7), Running 3.23 / 3.01 (9.6), Death 2.26 / 1.65 (73.5).
  Proportions checked against the masters: pointed muzzle, big round ears, beads 3/4 of the way from ear to nose. No
  head graft needed.
- Symmetry: MM9 body 0.0 mm in front of the rump; ours is mirrored, surface distance p99 0.29, max 0.95 mm after the
  symmetric reduction. The tail is asymmetric in both, by MM9's bind.
- Texture (`claude_shared/texture_quality.py`, `review/texture_quality.json`): atlas 59.7 %, equivalent 1,583 px,
  density p10/p50/p90 2,180 / 2,239 / 4,464, islands 100, fragments 0.0 %, stretch p90 1.14. Spread 2.05 is the head
  at twice the body's density on purpose; p50/p10 is 1.03.
- Attachment: `detached_parts_audit.py` 3 components (body, two eyes), 0 detached in any clip.
- Flat shading 0.00. Winding 0 inverted. Floor audit `MM9 299 mouse`, `MM9 300 evil mouse` ok. Loop seams 0 (Standing,
  Walking, Running).
- Edge ratio p1/p99 per clip 0.53-0.83 / 1.33-2.94 (`scripts/gates.py`, `review/gates.json`); the extremes (max 8.0)
  are the paw stubs, which stretch by design, and the tail root in the roll-over.
- Fold measure (`scripts/fold_measure.py`, from the wolf): worst frame 37 faces at rest, up to 116 in Death, dominated
  by the thin tail tube (Bone01-03), toes and ear sheets, where a neighbourhood normal is a weak test. The viewer shots
  show no flaps or shards.
- Regression `--world mm9 --headless-run-regression-suite actors`: `mm9_actor_models_build_every_binding` PASS
  (61 descriptors on 28 models, 0 failed), `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 / 185, 0 failed).
- No in-game run: no MM9 map places a mouse, and the row is Stationary.

## Deviations and open points

- Legs, Hit and Fidget are not MM9's (MM9 has no such bones or clips); they are authored smooth functions of time.
  Standing, the body/head/tail of Running, and Death's body are MM9's channels unchanged. Walking scales `Bone05`.
- The stretched paw stub shows on single frames of the run when the paw is far from the body at the top of a hop.
- Faint hair discontinuities remain along chart borders in very close views (the strokes change, the colour does not).
- Clips were checked from stills and playback frames, not watched at speed by the user.
- Generated rows give `Move` Stationary and AI Aggress (MM9 `Move 0`, cat.scr drives it): the mouse will not wander or
  flee in game until a behaviour script exists. cat.scr: wander, walk up to actors and sit (`fidgetdown1`, MM9 has
  no such clip on this model), run from dogs and projectiles. MM9 places no mice, so nothing is lost yet.
- The evil mouse's coat, eyes and skin are our design; there is no MM9 reference (see Decisions).
- The ramps carry fur colour by luminance, so a pale patch on tier A turns pale grey on tier C (its belly).
- User artistic acceptance: not recorded.

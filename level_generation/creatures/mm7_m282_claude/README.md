# MM7 Medusa (m282) — Claude 3D model, batch I

Medusa / Queen Medusa / Empress Medusa (monsters 298–300, descriptors Medusa A/B/C, sprite groups m283/m284/m285,
palettes 283/284/285). Batch I ([../mm7_batches/BATCH_I.md](../mm7_batches/BATCH_I.md)): the model stops at project
exports; **nothing is installed or bound**.

![tiers in the review viewer above the native palettes](review/tiers_vs_native.png)

| Item | Value |
|---|---|
| Exports | `export/mm7_m282.glb` (body: LOD0–3 + shadow LODs, 3 tier variants `m282_a/b/c`, body+head material merged), `export/mm7_m282_bow.glb` (node `Bow`), `export/mm7_m282_arrow.glb` (node `Arrow`, scale 0 = hidden), `export/mm7_m282_lod0.glb` (full-detail portable export, viewer source), `export/export_info.json` |
| Editable sources | `work/anim_v2.blend` (rig + clips + UVs + props as separate objects), `work/export_master.blend` (joined export state), `work/rig_v4.blend` (rig + UVs, no clips) |
| Triangles LOD0/1/2/3 | 16,554 / 8,276 / 2,971 / 984 (LOD0: body 14,175 + head 1,319 + bow 764 + arrow 296; the string tube stays in the body) |
| Skeleton | 122 bones: serpent `Root`, `Tail_01..30`, `Col_01..07`; `Pelvis`, `Spine1`, `Spine2`, `Neck`, `Head`; per side `Clavicle`, `UpperArm`, `ForeArm`, `ForeArmTwist`, `Hand`, five 3-bone fingers; 17 two-bone hair-snake chains `Hair_kk_1/2`; props `Bow`, `StringNock`, `StringTips`, `Arrow`, socket `Socket_Arrow_Release` |
| Clips (30 fps) | Standing 2.63 s loop, Walking 0.87 s loop (stride 1.6 m), Running 0.7 s loop (stride 2.1 m), Attack 1.5 s (**release 1.0 s**), Hit 0.73 s, Death 1.5 s, Dead 1.0 s, Fidget 2.0 s |
| Textures | body set 1K (base, normal, ORM, region mask) + head set 1K (base, flat normal, ORM), merged into 2080×1024 atlases; one region (R = scale-mail top); bow and arrow own small textures |
| Meshy credits | **25 of 100**: Smart Topology 5, body retexture 10 (our UVs), head retexture 10 (not used for colour, see Textures) |
| Viewer | `http://127.0.0.1:8912/level_generation/creatures/mm7_m282_claude/review/viewer/index.html` — `run_creature_review.py check`: 3 tiers × 8 clips, 24 switches, no console errors, failed [] |

## Review fixes, 2026-10-20 ("good but check the head")

Before: `review/head_fix_before_user.png` (the user's viewer close-ups). After: `review/head_fix_after_runtime.png`
(runtime GLB) and `review/head_fix_after_viewerglb.png` (viewer GLB), front and both front three-quarters, EEVEE;
`review/head_fix_viewer.png` (review viewer). No Meshy credits.

1. **Faceted face, neck and hair snakes.** Cause, measured: the Smart Topology import is flat-shaded, `sharp_face` was
   set on 15,470 of 15,470 faces in `step1_raw.blend` and every later blend, so the glTF export split every vertex per
   face (about 3 vertices per triangle) and each triangle was lit on its own. The normal maps were not the cause (Meshy's
   body map is converted to +Y up by `prepare_actor_glb.py`; the head map is flat) and neither texture has
   per-triangle shading. Fix at the source: `rig_medusa.py` turns smooth shading on for every face and drops
   `sharp_face`; the rig, hair, UV and clip chain was rerun. The UV layout is identical (coverage masks agree 100 %), so
   every texture stays valid. The exported body now shares vertices (0.92 vertices per triangle: only UV seams split).
2. **Old eyes on the sides of the head (ears and temples).** Cause: the profile mapping in `compose_head.py` was 150 px
   off (the eye column was read as 205 instead of 355), so the profile master's eye and ear landed on the temple,
   about 6 cm behind the real eye. The front view's eye also repeated on side surfaces behind the face. Fixes: correct
   profile column (355); each projection only paints texels that are the front-most surface along its camera ray (a
   z-buffer over the head texels); facing weights cubed; the profile's eye and ear masked out (the mesh has no ear and
   its eyes face forward); snake pixels dilated by 8 px, plus dark hair outside the face, so the snake roots leave no
   grey speckles. Also fixed:
   - the dark band under the chin, which was the collar piece. It is a tall choker that Meshy painted dark grey-green
     above and below the gold band; `compose_m282.py` now paints its non-gold texels with the neck skin;
   - the shadowed neck in the masters, which is now plain skin below the jaw;
   - the seam gain, now a fixed 0.9 (the old measurement sampled the gold-painted skin under the collar).

Clips are unchanged (same scripts, same vertex positions), so the gates below still hold. Viewer check after the
fix: 24 switches, no console errors, failed [].

### Review 2, 2026-10-20 (double nose, neck seam)

Before: `review/head_fix2_before_user.png`. After: `review/head_fix_after2_runtime.png` (runtime GLB),
`review/head_fix_after2_viewerglb.png` (viewer GLB), front and both three-quarters; `review/head_fix2_viewer.png`. No
Meshy credits.

1. **Double nose.** Cause: the vertical mapping put the masters' nose 2 cm too low on the mesh. The old landmarks
   (nose base at z 1.555) were not measured. The mesh tip sampled image row 550 (front) or 562 (profile) instead of
   578 or 600, so the painted bridge sat on the modelled tip and the painted nostrils sat under it.
   - **Measured landmarks:** mesh midline profile (minimum y per z): eyes 1.607, nose tip 1.575, subnasal 1.562,
     mouth line 1.548, jaw 1.505.
   - **Front master (midline luminance):** 487 / 578 / 592 / 638 / 720.
   - **Profile master (silhouette):** 500 / 600 / 638 / 680 / 785. The profile head is drawn about 19 % larger.
   - **Result:** both mappings now pass through these points. Each mesh landmark now projects within 1 px of its
     painted feature (eyes u 709 / 570 vs 708 / 570). The master's nostril shadow, which lands on the low-poly nose's
     camera-facing underside, is lifted to soft shading.
2. **Seam under the jaw.** Causes, all measured:
   - the fills and the neck used the master's bright window median (184), while the projected face measured 195;
   - the gain was a fixed 0.9;
   - the repainted collar choker kept the gold class in the ORM (roughness 0.3, specular 0.8), so it rendered white
     and glossy.

   Fixes:
   - the head's fill and neck colour is the projected face's own skin;
   - the gain is measured against the body's graded upper-chest skin (0.70);
   - the collar's non-gold texels take that same `neck_rgb` and the skin class (specular 0.15, roughness 0.62);
   - head skin specular is 0.15, equal to the body's skin.

   Head, neck, collar and chest now carry one skin tone (texture values 137 / 136 / 141). The neck still blends into
   plain skin over the 5 cm under the jaw.

Viewer check: 24 switches, no console errors, failed []. Clips and geometry are unchanged.

## Native identity

A female medusa: pale blue-grey human upper body with a mask-like face and glowing pupil-less eyes, about 14 hair
snakes (olive with bronze/gold), a scale-mail bra top with gold trim, gold collar and arm rings, a brown leather
quiver diagonal on her back (fletchings over the RIGHT shoulder); from the hips a thick serpent body with lavender
belly scutes, green scales with dark net/oval markings, three gold bands and a segmented rattle at the tail tip. She
holds a dark recurve bow with snake-head tips in her LEFT hand and draws with the right; the native attack is a bow
shot (monster table: physical, missile `Arrow`, no spell), so the model is an archer and Cast reuses Attack.
Tiers differ ONLY in the scale-mail (palette indices 215–237): A 283 charcoal, B 284 silver (the bitmaps' own
palette and the HD masters' colours), C 285 gold.

## Anatomy decisions

- **Two playbooks on one body.** Humanoid playbook for the torso, arms, hands and head; quadruped playbook "Snakes"
  (mm6_cob_claude) for the serpent part. The rig is ours throughout (no Meshy auto-rig: the body has no legs).
- **Serpent = curve-fitted chain.** The centreline comes from a harmonic field on the skin (`scripts/harmonic.py`:
  u = 0 at the rattle, 1 at the crown; level sets are clean rings on the long tail, where edge geodesics zig-zagged),
  smoothed and resampled every 10 cm (`joints_m282.py`): 30 tail segments lying on the floor, a root at the S-bend,
  7 column segments up to the hips. Every clip defines the centreline per frame (`anim_medusa.py`): tail joints keep
  their rest floor height, the heading is integrated from a curvature profile (straight back at rest, a travelling
  wave for Walking/Running with the mean heading cancelled so the tail trails straight), tail frames are locked to
  world up (belly down), the column bends by per-segment pitch/yaw with a floor rule and carries a twist up to the
  hips. Serpent skin weights by smoothed arc position (cobra rule). The rest tail lies diagonally back to her right
  (the three-quarter master); every clip lays it straight behind.
- **Tail stays on the floor.** Tail joints never leave their rest height (the rattle keeps its slight rest lift,
  max 17.6 cm for the gold-banded tip); column joints are clamped at their radius; the corpse column lies on a raised
  floor height so its thick lower part does not sink (lowest skin −0.9 cm).
- **Human torso/arms: heat weights on a voxel proxy**, then the playbook's arm rules: no upper-arm/forearm weight on
  the chest, back, neck or the ribs under the armpit; forearm twist ramp 15–85 % onto `ForeArmTwist` (60 % of the
  hand roll); serpent/heat blend between z 0.80 and 0.95 that never touches the arms. **Armpit web:** Smart Topology
  fused the inner upper arm to the ribs down to ~z 1.19 (about 10 cm below a natural armpit); a hard weight edge
  there tore at 18× when the arm rose, so the weights are diffused over that zone (25 Laplacian passes) and the fused
  skin now stretches gradually (worst single edge ~5×, arm p99 ≤ 1.9).
- **Hands:** separate pieces with five fingers fitted by connectivity (`fit_hands.py`: super-level sets of geodesic
  distance from the wrist; a finger = the earliest component that never splits again), 3 bones each, flexion axis =
  the hand's lateral axis, sign so +X curls toward the palm. The left hand is mirrored (its local X is the pinky
  side), handled explicitly in `hand_frame`. Wrist bracelets copy the skin under them.
- **Arms by hinge-exact IK** (`arm_math`): the elbow flexes only about the forearm's own axis (carrying angle kept);
  the flexion comes from the shoulder–wrist distance and the rigid bent arm is turned so the wrist reaches the target
  and the elbow points at the pole — continuous, no branch flips. The elbow swivel about the shoulder–wrist axis is
  chosen over the whole clip (plan pass + dynamic programming, the playbook's `arm_dp`: forearm twist + wrist swing
  above 35° + distance from the authored pole + continuity). Hand twist and swing are interpolated separately,
  branch-continuous, clamped at 100° twist / 60° swing.
- **Bow, string, arrow** (`make_bow.py` from the Codex prop sheet `references_hd/05_bow.png`, `attach_props.py`):
  bow 1.04 m traced as octagon rings, held in the left fist (`Bow` child of `Hand_L`, grip at the palm + handle
  half-depth); the string is a 6-sided tube in the body mesh (ends on `StringTips`, a non-animated child of `Bow`, so
  `split_attachment.py` keeps the whole string in the body; middle on `StringNock`) with a linen swatch in the body
  atlas; the arrow (0.82 m) is a rigid attachment on the unparented `Arrow` bone, keyed in armature space, scale 0
  when hidden. `Socket_Arrow_Release` sits at the arrow rest pointing out of the bow.
- **Attack after the native m282a* frames** (1.25 s native: aa reach, ab raise, ac arrow up, ad bring, ae draw,
  af 375 ms full draw, ag release, ah recover): the right hand reaches over the right shoulder into the quiver (the
  arrow appears at 0.25 s), lifts the arrow overhead while the bow comes up, brings it to the bow, nocks (0.60 s) and
  draws to an anchor under the RIGHT side of the chin; the torso turns ~75° to her right (side-on, the left shoulder
  toward the target) and the head looks back at the target; the arrow line runs from the anchor to the party and the
  bow wrist sits on it as far out as the left arm reaches. Hold with a slight creep, **release at 1.0 s** (string
  snaps back with a 1 cm overshoot, arrow hidden, the open hand flicks back and out), recovery eased into Standing by
  1.5 s.
- **Death after m282d*/xa0:** recoil and twist, then she topples to her LEFT: the column lies along the floor to her
  left, the torso continues it on her left side with the front toward the party (the native corpse silhouette), the
  bow slips from the fist at 0.4 s and falls flat beside her, the right arm across the body. Dead = the last pose.
- **Hair snakes:** 17 two-bone chains (`rig_hair.py`; floating side curls are rooted at the skull so they can swing).
  Hanging snakes follow the chest by 45/75 % (gravity), all writhe slowly, and a mesh floor rule lifts any chain that
  would pass under the floor (corpse).
- **Quiver and arrows** rigid on `Spine2`; eyes rigid on `Head`; collar and arm rings copy the skin under them.

## Route (replay)

1. HD masters (`references_hd/`, Codex: `CODEX_BRIEF.md`, `generation_runs.json`, contact sheet; inputs built by
   `scripts/native_sheets.py` from the palette-decoded native frames, `scripts/native_palettes.py`), head turnaround
   `references_head/`.
2. Smart Topology 15k of `00_three_quarter.png` (`requests/body_geometry_v1.json`): 15,470 tris, 38 pieces (skin,
   17 hair pieces, hands, quiver, arrows, eyes, studs, rings, collar). `step1_clean.py` (height 1.80 m, YAW 0).
3. `harmonic.py`, `joints_m282.py`, `fit_hands.py` (python3), then Blender: `rig_medusa.py` → `attach_props.py`
   (after `make_bow.py` in python3 and Blender) → `rig_hair.py` → `uv_medusa.py` (head faces own 0..1 layout, uploads)
   → `anim_medusa.py work/rig_v4.blend work/anim_v2.blend`.
4. Textures: `requests/body_retexture_v1.json`, `uv_raster.py` (BODY 1024/2048, HEAD 1024), `bake_ao.py`,
   `compose_m282.py`, `compose_head.py`.
5. `scripts/build_runtime.sh <token>`; viewer `viewer_tiers.py`, `update_viewer_manifest.py`; gates `gates.py`,
   `outliers.py`. Review renders: `sheet.py`, `tex_preview.py`, `views.py`, `render_clip_glb.py`.

## Textures and tiers

- Body: Meshy retexture on our Smart UV layout (42 % coverage), graded by rest AO at 2K and stored at 1K (the merged
  body+head atlas needs equal sizes; the texture guide's 1K body beside a head set).
- **Head: projected, not Meshy.** The head-only retexture painted snake scales over the whole face (the reference
  heads are mostly snakes), so `compose_head.py` projects the Codex head masters onto the head faces instead: front
  and profile mappings fitted to landmarks (eye spacing; eyes, nose base, mouth, chin piecewise vertically, because the
  Smart Topology face is shorter than the master's), weighted by facing, snake-coloured pixels and the scalp above the
  hairline replaced by skin / dark scalp-gap colour, neck seam matched to the body (gain 0.80). Flat normal map.
- Region R = the scale-mail cups and under-band (low-saturation scale pattern in the chest box, smoothed over 2 cm in
  3D, gold and bluish skin excluded, padded into the gutters). Ramps from the native mail pixels (BMP indices 215–237
  through each palette): hue/saturation band-averaged at the texel's luminance quantile, luminance from the texel
  scaled to the native mean × 1.05 (C × 1.12 with saturation × 1.35: band-averaging mixes in the white highlights),
  darkest stops desaturated. Everything else keeps its colour in every tier.
- Material classes `textures/m282_material_classes.png` / `m282_head_material_classes.png` (skin, scales, mail and
  gold = metal, leather, wood, keratin rattle, eyes); ORM red = specular class, `openyamm_specular_mask`, metallic 0.

## Gates (final export, `review/gates.json`; arm log `work/clips.json`)

Edge stretch = posed / rest edge length, every second frame; contacts = signed depth of hands, forearms, bow and arrow
inside the torso/column/head skin (G6); arm log = forearm twist range, max wrist swing, max twist step per frame
(30 fps); jerk = max world-rotation step per frame of the hands (deg).

| Clip | arms p99 / max | hands p99 / max | serpent p99 / max | torso max | contacts (cm) | wrist swing max L/R | twist L / R (deg) | hand jerk max |
|---|---|---|---|---|---|---|---|---|
| Standing | 1.36 / 1.88 | 1.45 / 1.79 | 1.36 / 1.95 | 2.21 | none | 17 / 34 | -5..-4 / 5 | 0.5 |
| Walking | 1.38 / 1.95 | 1.44 / 1.82 | 1.67 / 3.20 | 2.23 | none | 17 / 36 | -5 / 5..7 | 1.9 |
| Running | 1.40 / 2.02 | 1.40 / 1.87 | 1.80 / 3.88 | 2.27 | R hand 0.7 | 15 / 39 | -4 / 5..8 | 2.6 |
| Attack | 1.86 / 3.01 | 2.06 / 3.55 | 1.42 / 2.07 | 5.16 | R hand 3.1 (release frame, jaw), R forearm 2.9 (full draw, jaw/neck), L forearm 1.5 | 51 / 60 | -34..12 / -3..28 | 81 (release flick) |
| Hit | 1.36 / 1.91 | 1.69 / 2.60 | 1.35 / 1.88 | 2.41 | R hand 0.1 | 32 / 51 | -4..4 / -33..9 | 62 (flinch) |
| Fidget | 1.36 / 1.88 | 1.44 / 1.77 | 1.36 / 1.92 | 2.20 | none | 17 / 33 | -7..-4 / 5 | 1.7 |
| Death | 1.67 / 3.55 | 1.49 / 2.22 | 2.43 / 5.75 | 4.34 | R hand 2.9 (falling across the chest) | 21 / 40 | -53..8 / -2..26 | 26 |
| Dead | 1.64 / 3.07 | 1.46 / 2.18 | 2.43 / 4.77 | 3.69 | none | 0 / 38 | 0 / 2 | 0 |

- Humanoid G4 arm p99 ≤ 1.9 everywhere (guideline ≲ 2); G5 hand edges ≤ 3.6× (limit ~4.5×). The worst single edges
  (5–8×) are one armpit-web vertex each side (the fused armpit, see Anatomy decisions) and the corpse's serpent fold.
- Arm and hand gate: wrist swing ≤ 60° (clamped; reached only at the release flick), forearm twist continuous
  (≤ 24° per frame) and within -53..+28°; hands outside the body except the listed contacts.
- Floor: lowest skin vertex 0 cm in every standing clip, -0.9 cm in Death/Dead; hair snakes ≥ 0.8 cm, hands ≥ 0.5 cm and
  the dropped bow 1.0 cm above the floor in the corpse; the tail never leaves the floor (rattle tip max 17.6 cm, its
  rest height).
- Viewer check: 24 tier/clip switches, no console errors, failed []; shots in `review/shots/`, sheets
  `review/actions_sheet.png`, `review/attack_sheet_clay.png`, `review/death_sheet_clay.png`.

## For the user to review

- Motion is procedural (no mocap): an interpretation of the native frames. The attack is a real side-on archery draw
  with a chin anchor; the native sprite draws it more frontally.
- The string hand touches the jaw/hair at full draw and release (up to ~3 cm into the skin surface at the release
  frame) and the release flick is fast (≈80°/frame for one frame).
- The armpits are fused to the ribs by Smart Topology; the diffused weights stretch the side skin like a web when an
  arm is raised high (death throw, quiver reach). A local mesh split was not done (it would need a re-unwrap).
- Corpse: the lying column's thick part sits on a raised floor height, so the lying torso hovers ~6 cm above the
  floor in places; the serpent fold at the corpse bend stretches (p99 2.4).
- The head texture is a projection of the head masters (sharp face, glowing eyes, fixed 2026-10-20: smooth shading,
  no ghost eyes); hidden scalp and the sides under the snakes are a flat skin/dark fill.
- The mask leaves a little silver on the side panels of the cups and a faint tint on the skin at the cup edges in A/C.
- LOD0 is 16.5k triangles (Smart Topology at 15k, not reduced: 17 hair snakes and a 2.3 m tail); a reduction pass like
  `mm7_m278_reduce_claude` could follow.
- No in-game check was run (optional for batch I).

## Install later (not run)

**Reduced version:** [`../mm7_m282_reduce_claude/`](../mm7_m282_reduce_claude/README.md) (2026-10-20, 15,494 -> 9,756
LOD0 triangles, face, hands and textures unchanged) — install its `export/mm7_m282.glb` instead of this one (bow and
arrow are byte-identical copies); the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m282_claude/export/mm7_m282.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m282_claude/export/mm7_m282_bow.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m282_claude/export/mm7_m282_arrow.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`. Scale = native standing silhouette `m282sa0` 159 px (rows
97–256) × frame scale 1 (m283–m285 have no scale key) ÷ Standing height 1.799 m = **88.4**; B/C use the same frame
scale (`scale_reference: Medusa A`). Run threshold 2.4 × 88.4 = 212 units/s: A (speed 200) walks, B (220) and C (240)
run. Arrow launches from `Socket_Arrow_Release` at the release.

```yaml
# MM7 Medusa m282 (298-300): bow and nocked-arrow attachments, arrows launch from Socket_Arrow_Release at 1.0 s.
- descriptor: Medusa A
  model: worlds/mm7/models/mm7_m282.glb
  scale: 88.4
  yaw_offset: -1.570796327
  skin: m282_a
  animation:
    sockets:
      arrow_release: Socket_Arrow_Release
    cast: Attack
    run: Running
    stride_length: 1.6
    run_stride_length: 2.1
    upper_body_root: Spine1
    look:
      nodes: [Neck, Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 25
    events:
      attack_melee: {impact: 1.0}
      attack_ranged: {impact: 1.0, release: arrow_release}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  attachments:
  - model: worlds/mm7/models/mm7_m282_bow.glb
    node: Bow
  - model: worlds/mm7/models/mm7_m282_arrow.glb
    node: Arrow
# Medusa B / C: the same with skin m282_b / m282_c and scale_reference: Medusa A
```

## Notes for shared tools (not changed)

- `tools/run_creature_blender.sh` holds the project write lock for the whole Blender run, so Meshy polls for the same
  project fail with "Another creature operation is running" while a long bake runs; poll between Blender steps.
- `tools/merge_head_material.py` needs every body map and every head map at one size; a 2K body base with 1K
  normal/ORM cannot be merged (here the body set is 1K throughout).
- `claude_shared/head_texture_split.py` / `compose_head_set.py` expect a head retexture that paints the face; for
  hair-covered heads (medusa snakes) a projection of the head masters (`scripts/compose_head.py`) was needed.

# MM6 mage (pmn2) — 3D model, 2026-10-07

New Sorpigal staff-carrying mage (descriptors 610–612 `PeasantM2 A/B/C`), built with the simplified humanoid route:
closed-hand reference → Meshy Smart Topology (pose mode off) → local cleanup and UVs → Meshy auto-rig used as-is.

## Status

| Step | State |
|---|---|
| Reference | `references/00_smart_topology_three_quarter.png`: right hand closed (staff grip), left loosely closed, palms toward the thighs (Codex edit of the stage-1 primary, `raw/pmn2_primary_v3_fist_a.png`) |
| Smart Topology | run by the user in Meshy web. v1 (A-pose mode) reopened the hands and narrowed the arms — rejected; **v2 (pose mode off) kept the fists** — selected, 16,187 tris |
| Cleanup | `scripts/step1_pmn2.py` → `work/step1_v1.blend`, **10,075 tris** |
| UVs | `scripts/uv_pmn2.py` → `work/step1_uv.blend`; gate `scripts/uv_check.py` (+ `draw_uv_layout.py`) |
| Rig handoff | **`export/pmn2_clean_uv.glb`** — 10,403 tris (edge loops added at bracer tops and boot rims), 1.578 m, soles at 0, faces glTF +Z, one mesh, UVs, no material |
| Meshy rig | user (web), `meshy/rig_manual_v1/model.glb`: 1.7 m, 78 bones, clips Idle_9/Walking/Running/Dead; same topology, UVs dropped |
| Rigged master | `scripts/build_rig_v1.py` → `work/rig_v1.blend` (our UV mesh ×1.077, Meshy weights, rigid fists, flat feet); check `scripts/verify_rig.py`; preview `export/pmn2_rig_v1_preview.glb` |
| Staff | `scripts/make_staff.py` (native pmn2sta0: 1.60 m, club head, 332 tris) → `seat_staff.py` (fist tunnel, `Staff`/`StaffTip` bones) → `work/rig_v2.blend` |
| Staff carry | `scripts/carry_staff.py` → `work/rig_v3.blend` (idle/walk/run right arm solved onto the staff); audit `scripts/staff_audit.py`; preview `export/pmn2_rig_v3_staff_preview.glb` |
| Clips | user added Meshy 128 Heavy Hammer Swing, 178 Hit Reaction, 189 Dying Backwards (+ 560 Spear Walk) in the web app → `meshy/rig_manual_v1_anims2/model.glb` (same rig) |
| Chain | `build_rig_v1.py` → `seat_staff.py` → `carry_staff.py` (v3) → `retarget_fbx.py … great_sword_casting.fbx GSC` (v3g) → `attack_staff.py` + `smooth_attack.py` (v4) → `author_hit.py` (v5) → `death_staff.py` + `smooth_attack.py` (Death env, see its docstring) (v6); shared solver `staff_rig.py`; renders `render_clip.py` + `clip_sheet_pmn2.py`; game export `export_game_clips.py` → `export/pmn2_rig_v6_clips_preview.glb` |
| Texture | Meshy retexture_v1 (10 credits, API) on `export/pmn2_clean_uv.glb` with the fist views → `scripts/apply_texture.py` → `work/rig_v8.blend`; staff wood texture `staff_socket_texture.py` |
| Runtime | `scripts/build_runtime.sh --install` → `assets_dev/worlds/mm6/models/mm6_pmn2.glb` (LOD 10,735/5,367/1,931/640, one material: staff packed into the body atlas); bindings PeasantM2 A/B/C in `actors.yml` (scale 105.8 = 257 px × 0.70 / 1.70 m, stride 1.2) |
| Regression | `mm6_pmn2_actor_models_bind_free_haven_mages`, `mm6_pmn2_actor_spell_charge_glows_at_staff_head` |

Rebuild: `analyse_parts.py` needs `work/v2_parts.blend` from `examine_parts.py meshy/smart_topology_manual_v2/model.glb v2`;
then `step1_pmn2.py`, `uv_pmn2.py`, `uv_check.py`, `export_clean.py` (all headless Blender).

## Cleanup (16,187 → 10,075)

- Parts: body (vest/arms/trousers/boots), head, hair+beard, mantle, tunic skirt, two fist shells, rope, knot, two
  rope tails, two pouches. Eyeballs were half shells in front of a closed face: only their visible caps are kept
  (deleting them left pits; the head has no eye surface).
- Decimation runs on selected faces in edit mode, so the face, fists, neck seam, boot soles/rims and the hair's
  face opening keep every vertex. Weighted Decimate modifiers still collapsed zero-weight vertices (rough face,
  saw-tooth hairline) — do not use them for protection.
- Hard cuts only where hidden or cheap: skull under hair, body under mantle/skirt, boot shafts, trousers, rope,
  pouches. Hidden skin within 8 mm of the mantle/skirt is tucked under it (hidden vertices only).

## UV atlas

- No rig yet, so body regions are geometric: upper arm and forearm (bracer) from the shoulder–wrist axis, leg and
  boot per side, torso, plus low-density hidden regions (body under mantle/skirt by ray coverage). The head is split
  by a plane: face at full density, skull/neck/ears (`HeadBack`) lower.
- Bracer tops (t = 0.25 m along the arm) and boot rims (z = 0.40) are measured crease rings; straight edge loops are
  cut there so those texture borders are clean seams instead of saw-tooth region borders.
- `MINIMUM_STRETCH` unwrap: 377 islands, stretch p2–p98 within 0.64–1.87 everywhere (legs worst), ABF was
  0.25–2.87 with 452 islands. Boots, fists, rope and pouches use Smart UV Project.
- Density at 2048: face 25.6 px/cm, body 10.7, fists 15.0, hair 11.8, legs/boots 7.5, hidden 3–4. 1024² overlap
  raster clean.

## Meshy rig fixes (user review 1: deformed hands, feet not flat)

- **Hands:** Meshy added thumb/middle chains under the hand (animated in every clip) and three more finger chains
  parented to the *forearm*; each fist was spread over ~10 of them. Each fist shell is now 100 % on its Hand bone.
- **Feet:** the rest pose is flat (sole pitch −0.2°, roll ≤ 1°); Meshy's clips bring a foreign foot posture
  (idle soles 16–20° tilted, walk/run contact ~15° rolled). The Foot bone is rotated about the ankle per frame to level
  the sole on the ground (roll fades 4→12 cm, pitch 1.5→5 cm, so heel strike/toe-off stay). Grounded tilt after the
  fix: idle 1.9°, walk mean 7°, run mean 12° (maxima are toe-off). Idle also sank 4.3 cm: per-clip Hips offset puts
  the lowest sole at z = 0 in every clip.

## User review 2: wrists (2026-10-07)

Meshy's clips bend the wrist 45–60° even at idle (run up to 87°, ±25° twist): the source body's relaxed open hand,
which on a fist reads as a broken wrist. `build_rig_v1.py` keeps 25 % of the clip's Hand rotation and caps the bend at
25°; after: idle 11–15°, walk 12–16°, run ≤ 22°, twist ≤ 7° (`scripts/wrist_audit.py`). Viewer:
`review/viewer/` (rig v1.1 vs Meshy's return).

## Staff and carry (2026-10-07)

- Staff from the native standing sprite: length 0.943 × body height, club head 26 cm, shaft 5.0→4.2 cm, grip 29 % from
  the top. Seated once on the fist's tunnel (largest-clearance line the fingers wrap, 10 mm); top toward the thumb
  (forward at rest — Meshy's thumb bones lie on the knuckles of a fist). Rigid on a `Staff` bone under RightHand.
- Carry: staff upright at the right side, grip 1.15 m (native) moving with the hips, grip position = least wrist strain
  among points whose idle shaft clears the body by 3 cm (0.24 m right, 0.14 m forward). Right arm: two-bone IK, elbow
  low/back/out, swing-only upper arm/forearm, forearm takes half the hand twist, hand roll about the staff picked
  from 72 candidates. Walk/run: staff sweeps with the left arm (foot trails the stepping right leg) and its foot leans
  out per frame just enough to clear the legs; run tilts it 18° forward.
- Audit: shaft clearance idle 36 mm, walk 29 mm, run −4 mm (upper arm graze above the grip, 2 vertices); staff foot
  ≥ 8 mm above the floor; wrist swing ≤ 36° idle/walk, 47° run, twist ≤ 15°.

## Actions (2026-10-07)

- Standing / Walking / Running: Meshy idle/walk/run with the staff carry (Spear Walk needed 59° wrist bends; unused).
- Attack (0.75 s): user-supplied Mixamo `references/fbx/great_sword_casting.fbx`, retargeted by bone direction +
  twist (`retarget_fbx.py`; T-pose → A-pose rest). Its hands truly share one handle (8–18 cm, grip axes 0.86–0.97), so
  the clip's wrists are kept and the left fist is solved onto the shaft. Frames 16→34→45 on the native keys: drawn up
  behind the head, diagonal above the brow, horizontal overhead, then lowered in front to the carry (the clip's
  point-down turn and kneeling ground plunge are not used). Head 40 % of the clip, body turn 20 %, native crouch,
  feet planted. Staff ≥ 117 mm off the body. The first version (Meshy Heavy Hammer Swing 18→27→37) was rejected:
  head tilted far sideways overhead and a deep forward fold at the strike.
- Review 4 (right arm through the head 0.1–0.5 s): the clip's elbows point forward, so the raised upper arm crossed
  the face (head kept at 20–40 % made it worse). `attack_staff.py` now runs two passes: per frame the cheapest of
  elbows out to the sides (native c/d, tried first), grips moved back/up/down/right, head ducked forward and leaned
  left that clears the face (`staff_rig.head_penetration`, head/eye shells only), smoothed over ±2 frames. Face clear
  in front and ¾ views; remaining: from the side the raised right upper arm still touches the long hair by the ear
  (≈ 20–40 vertices, ≤ 7 cm into the hair shell), and frames 5–7 have the vertical shaft in front of the face.
- Review 5 (staff flipped at viewer frame 5, hands rotated at 7–9 and 15): quaternion keys flipped sign between
  frames (fixed on export) and per-frame solves rolled the hand/forearm ~180° on the round shaft. `smooth_attack.py`
  keeps key frames 0/3/6/10 (viewer 0/6/12/20) and interpolates both hands' targets between them with an anatomical
  twist split; frames 10+ re-solved the same way on their own targets, ends eased into the carry pose. Death: same
  smoothing on the right arm (keys 0/3/7/12/15/18/23, staff ends kept above the floor). Largest frame-to-frame change
  now 71° (attack) / 77° (death, falling); staff ≥ 6.5 mm off the body and above the floor in the death.
- FBX import sets the scene to the file's frame rate (30): `retarget_fbx.py` restores 24 fps, otherwise every clip
  exports 20 % short.
- Hit (0.75 s): authored from the native hit keys on the idle carry pose (recoil + left knee lift, staff thrown wide,
  staff by the face, forward fold, rise). Meshy Hit Reaction (178) was unusable: 60°-turned boxing stance, 0.8 m
  sideways stagger with steps. Staff ≥ 18 mm off the body, wrist ≤ 31°/36°.
- Death (1.0 s) / Dead: Meshy Dying Backwards frames 9→40; staff carried with the chest and solved per frame, ≥ 17 mm
  off the body and ≥ 15 mm above the floor; body never below the floor. Wrist peaks at 85° for ~0.3 s mid-fall; the
  corpse's staff rests slanted (head end ~17 cm up), not flat.

## Spell glow (2026-10-07)

- Their only ranged attack is the spell (Attack 1 is a melee staff hit with no missile), so no ranged hand effect
  applies. Cast = the attack clip, exported a second time as `Cast` (the engine requires a distinct cast clip).
- Engine: `cast_focus_socket` / `cast_focus_glow_scale` add a second charge glow (outer + core, sparks, release
  sparkles) at a held focus; `cast_glow_scale` sizes the palm glow. Mage: palms at the Demon's size (1.0), staff head
  0.6. Element colour comes from the spell: Fire Bolt 255/60/30, Ice Bolt 158/185/241, Lightning 200/200/20.
- In-game captures: `review/ingame/cast_glow_crops.png` (fire at staff head and fists, lightning at the staff head).

## Colour tiers and skin (2026-10-07)

- Tiers A/B/C = native palettes 801 red / 802 green / 803 blue on mantle, pouches and trousers. Instead of three
  base-colour textures (+2 × 2048² RGBA8 with mips ≈ +45 MB GPU, +~10 MB GLB), the engine now supports a material
  tint: glTF material extras `openyamm_tint` (linear RGB); inside the mask in the metallic-roughness red channel the
  base colour becomes luminance × tint (`fs_model.sc`, `u_modelTint`). `add_variants.py` makes Mage_A/B/C materials
  that share every image (uploaded once). Tints in `textures/tints.json` map the masked mean to the palette ramp mean.
- Review: green stayed on the red/blue tiers at the collar and hips (Meshy painted mantle/trouser green onto the
  neighbouring torso texels). The mask is now every green texel of the atlas (green is unique to the recoloured
  cloth); the tint source colour is still measured on the cloth islands only.
- Review: shoulders too high. Meshy's idle shrugs both clavicles 31–35° above rest (attack/hit inherit it):
  `build_rig_v1.py` step 6 keeps every clip's clavicle elevation within 6° of rest (idle lowered 32°, run 16°).
- Review: the free hand floated beside the hip and the staff showed in the left hand. Two causes: (1) lowering the
  clavicles swung the hanging upper arm inward (step 6 now keeps the upper arm's world aim); (2) engine bug:
  `gltfModelPlacement` negated only Z, mirroring every glTF actor (right-handed props in the left hand, also the
  goblin's sword). It now negates X and Z (a proper rotation); unit test checks the handedness.
- Skin: Meshy's skin albedo was nearly flat. `bake_ao.py` (15 cm + 3 cm AO) and `prepare_textures.py` add AO
  (warm shadows on skin), low-frequency tone mottling and fine pore noise. Muscle definition is still absent (smooth
  low-poly arms, near-flat Meshy normal map).

## Single material (2026-10-07)

The staff used to be a second material (its own 256 × 1024 wood map), so every mage was two draws per pass. The body
atlas has no free rectangle (89 % covered), so `prepare_textures.py` squeezes it horizontally to u × 1968/2048 (an
axis scale keeps tangent directions, so the normal map needs no rebake) and writes the staff wood into the strip
u 1976–2040/2048 on the right (staff circumference u 0–1.4 wrapped, edge-extended margins; flat normal, roughness
0.8, no tint mask). `export_runtime.py` remaps both UV sets from `textures/atlas_pack.json` and joins the staff under
the body material; `add_variants.py` now has one primitive per mesh. Body texels lose 4 % horizontally.
60 mages: ~60 fewer draws, GPU 750–790 → ~680 µs (`output/performance/actor_models_20261007/README.md`).

## Known limits

- Grey streak on the hair at the left temple (Meshy projection); hair touches the raised arms in the attack.

- Meshy walk: hands brush the rope tails/pouches in some frames (Meshy arm spacing); to be handled with the staff
  pose in the native walk.

- Four retexture views (front/back/left/right) in the stage-1 package still show open hands; regenerate them with
  fists before the retexture.
- Hair back is simplified (strands come from the texture); bracers are part of the forearm surface, not a shell.

## Head texture set (2026-10-08)

Head-only retexture per [creature textures](../CLAUDE_CREATURE_TEXTURES.md) ("Head-only retexture"):
- `references_head/`: Codex head turnaround (brief `CODEX_BRIEF.md`). Meshy `head_retexture_v1` (10 credits).
- `../claude_shared/head_texture_split.py` marked the head faces in the master (backup `*_pre_head.blend`), and
  `../claude_shared/compose_head_set.py` (run by `build_runtime.sh`) writes the 1K head maps, matching brightness
  across the neck seam.
- The head is one material for all tiers (the skin does not change between palettes). The body base colour is now
  1K, and skin, cloth and metal use `openyamm_specular 0` with metallic 0.
- Capture: `review/head_set_close_20261008.png`. Previous build: `export/mm6_pmn2_prehead.glb`.

## Native shading transfer (2026-10-08)

User request after the Patrol Unit result. Applied with [native shading transfer](../NATIVE_SHADING_TRANSFER.md):
- `native_shading.json`: the five standing views, `height` coordinate, the robe region from the restored mask (R).
- `scripts/native_shading_pmn2.py` (run by `build_runtime.sh` after `prepare_textures.py`): only the recoloured cloth
  (mantle, trousers, pouches) takes the native cloth brightness by height, blended 65 % into Meshy's cloth, so the
  folds stay. Skin, leather and boots are untouched: they share heights, so one height profile cannot separate them.
  The head set is untouched.
- `scripts/tier_ramps.py`: robe ramps from the same native cloth pixels in each palette (gain 1.0, saturation ×1.1)
  instead of the single tint. Tier A is a slightly cleaner, deeper red, tier B a brighter green and tier C a lighter
  blue, all closer to the sprites.
- Comparison: `review/native_shading/before_after_native.png` (left: before/after per tier, right: native standing
  views). In game: `review/native_shading/ingame_0.png`. Pre-transfer files: `textures_pre_native/`.

## Clip timing (2026-10-10)

The 0.75 s Attack (= Cast) squeezed the GSC draw-up and strike up to 3.3x ([audit](../CLIP_TIMING_AUDIT_20261010.md)).
`attack_staff.py` keys are now [0 idle, 3 GSC16, 14 GSC34, 21 GSC45, 29 idle] (draw-up at a uniform ~1.3x; the
per-frame crouch keys are warped from the old layout), then `SMOOTH_KEYS='[0, 3, 11, 21]' smooth_attack.py`, then
`transplant_clips.py` copies the Attack into `work/rig_v8.blend` (v5-v8 do not touch it; backups
`work/rig_v4_pre_clip_timing.blend`, `rig_v8_pre_clip_timing.blend`). Attack/Cast 1.21 s; the staff comes down at
0.979 s -> actors.yml `events` for melee, ranged and cast (bolts and spells from `Socket_Staff_Head`). Full source
speed would need cutting the reviewed draw-up behind the head (0.97 s on its own). Continuity matches the accepted
build (left forearm 92 deg at the grab, was 100). A 4-frame lead-in flipped the left forearm 140 deg: keep 3.
Sheet: `review/timing_attack_sheet.png`.
- Death at source speed (follow-up): `death_staff.py` keys k3 clip 9 -> k34 clip 40 (1.42 s; was ~1.45x), the fall's
  floor fade and frame range scaled; `smooth_attack.py` Death keys `[0, 3, 9, 16, 21, 25, 32]`, `SMOOTH_LAST=33`;
  `transplant_clips.py -- rig_v6.blend Death Dead` into rig_v8. Continuity better than before (worst arm step 65 deg,
  was 86; staff 32, was 52); staff >= 15 mm above the floor and clear of the body. Note: rig_v5-v7 keep the old
  Attack; rig_v8 holds the current clips.

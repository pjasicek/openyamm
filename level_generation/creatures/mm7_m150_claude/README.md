# MM7 Angel (m150): Angel / Angel Lord / Archangel — Claude rig-first project

MM7 batch G, model 1 ([batch file](../mm7_batches/BATCH_G.md)). Descriptors 199 Angel (palette 151, green skirt),
200 Angel Lord (152, blue) and 201 Archangel (153, magenta). **Exported, not installed** (batch rule). Status: **v2**,
rebuilt after the user review of v1 (2026-10-20), pending user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m150_claude/review/viewer/`) ·
[v2 HD masters](references_hd/v2/selected_views_review.png) · [v2 head masters](references_head/v2/) ·
[G1 clip choice](review/g1/G1.md) · [viewer shots](review/shots/) (`f_*.png` = v2)

## v2 (user review of v1, 2026-10-20)

| Review point (v1) | v2 change |
|---|---|
| wings good, sword good | kept (wing rig and motion, Meshy flamberge) |
| helmet does not work (Smart Topology fused it into the head, crest a loop) | new body masters with a **bare head**; the helmet is its own **Meshy model** (Smart Topology + texture of `references_hd/v2/helmet.png`: curled scroll crest, temple wings, teal jewels), fitted on the head by `helmet_fit.py` (scale from the cavity rays, scalp pushed inside), rigid on a `Helmet` bone, its own attachment |
| armour textured wrong (black cuirass with brown discs) | masters with a **polished steel** cuirass; Meshy paints metal as dark albedo + metallic, the runtime is non-metallic, so steel is repainted to one albedo x Meshy's fine shading (`compose_m150.py`); the shoulder straps' Meshy gold/brown discs became steel plates with gold studs, and the cuirass under and beside them is steel (normal map flattened there) |
| shoulders unnatural, the raised arm dragged the cuirass and armhole rim | masters with the arms at 35-40 deg and open armpits; new **armhole rule** in `weights_fix.py` (arm weight only near the upper-arm axis and lateral of the armhole, 5-7 cm fades); straps follow the clavicle (`strap_weights.py`); attack-frame arm stretch p99 1.49-1.93 (v1: up to 2.39 at the same frames before the rule) |
| shield wrong (native: heater shield with a gold emblem) | **Meshy heater shield** (Smart Topology + texture of `references_hd/v2/shield.png`: studded brass rim, gold winged emblem, arm straps), its back 6 cm clear of the forearm (`import_props_v2.py`) |
| dark patches on the skin | the Cycles AO bake had black faces (rays starting inside overlapping shells): `ao_clean` replaces them; the skin repaint keeps only +-20 % of Meshy's detail |

### v3 fixes (second user review, 2026-10-20; no Meshy credits)

| Review point (v2) | Fix |
|---|---|
| helmet looks good but does not fit (cheek guards off the face, hair showing between) | `helmet_fit.py` measures the cheek skin (not the hair, which carries head weight), bends the guards toward it below the brow, and pushes the hair under the guards inside the helmet; the fitted helmet is kept in the master as `HelmetFitted` for the export |
| flight: sword hand facing the wrong way, arm across the chest | `carry_flight.json`: the wrist beside the right hip, the blade level and forward along the flight as in the native wa..wh side frames (hand twist 42 deg, was 160 deg) |
| shield merges with the arm | strap at 55 % of the height, the back 12 cm off the forearm axis (`import_props_v2.py CLEAR=0.12 STRAP_T=0.55`); new `shield_gate.py`: arm vertices through the shield <= 1.9 cm (one vertex, attack), was 7.9 cm |
| attack: a stray dark strip by the sword arm | a feather card behind the right shoulder (P124) was left on the body with upper-arm weights; `strap_weights.py` gives it the nearest wing weights |

### v4 (third user review, 2026-10-20; no Meshy credits)

- **Helmet too wide (ears showing):** the helmet cavity is long front to back, so one uniform scale fitted to the depth
  left the sides wide, and the thick Meshy shell (brow band, rims) added ~2 cm outside. `helmet_fit.py` now scales
  width and depth separately and narrows the width by `SX_TIGHT` 0.88; scalp, hair and ears under the guards are
  pushed inside the shell (299 vertices, open face untouched).
- **Helmet looked soft:** helmet and shield base colours get an unsharp mask (sigma 1.5 px, amount 0.9) and their
  normal-map slopes x2.0 (`compose_m150.py` SHARP_SIGMA / SHARP_AMT / NORMAL_GAIN).

### v5 (fourth user review, 2026-10-20; no Meshy credits)

- **Shoulders slumped forward (idle, hit):** the Mixamo idle and the set's hit carried the source body's rounded
  shoulders (shoulder joints 3-7 cm in front of the neck base and 3-6 cm low; rest 5.5 cm behind). `clavicle_fix.py`
  (after the retarget) keeps each clavicle at its rest relation to the chest plus 25 % of the clip's own motion (60 % in
  the attack) with the upper arms' world direction kept; idle shoulders now 1-4 cm behind the neck base. The hit's
  head snap is halved (72 -> 54 deg at its peak).
- **Blurry armour:** at the 1K body set the steel, gold and leather get an unsharp mask (sigma 1.2 px, amount 0.8) and
  normal slopes x1.6 (`compose_m150.py` BODY_SHARP_*); skin, feathers and cloth stay soft. A 2K body set would need
  every body and head map at 2K (the head merge needs one atlas layout), ~4x the texture memory; not done.
- The overhead raise then brushed the head: `sword_clear.py` treats head faces as 7 cm thicker (the helmet), the blade
  clears the head in the attack.

### v6 (fifth user review, 2026-10-20; no Meshy credits)

- **Two belts in the attack:** the torso shell carries a modelled belt under the separate buckle, studs, skirt top and
  tabs (all on B_Pelvis), but Meshy weighted that band to the spine, so the trunk twist slid them apart (two buckles,
  the hip texture swimming). `weights_fix.py` "belt band": the skin shell between z 0.95 and 1.11 is B_Pelvis, fading
  back to its own weights over 12 cm above. `waist_stretch.py`: waist p99 <= 2.1; the worst edges are under the armpits (<= 5.2x on 3-6 edges in the attack, hit and fidget) and at the belt's lower edge only while lying in the death (6.4x on 8 edges).

### v7 (sixth user review, 2026-10-20; no Meshy credits)

- **Left thigh through the skirt in the attack:** the dress rule let the hem follow the thighs at only 45 % (tabs 60 %),
  so the lifted thigh passed through. `weights_fix.py` now uses 65 % for the skirt and 75 % for the tabs, and
  `skirt_inflate.py` keeps every skirt/tab vertex below the belt >= 2 cm off the thigh skin (7 vertices moved).
  `g6_skirt_poke.py` (adapted to this mesh): thigh skin through the skirt or a tab <= 1.4 cm in the living clips
  (attack 1.4 on one tab, fidget 1.0, hit 0.7); the lying death still reaches 5 cm (thigh under the skirt on the floor).

v1 is archived in `export/v1/`, `work/v1/`, `textures/v1/` (Meshy v1 jobs stay recorded).

| Item | Value |
|---|---|
| Exports | `export/mm7_m150.glb` (body + wings, LODs, 3 tier variants, head merged), attachments `export/mm7_m150_sword.glb` (`Sword`), `export/mm7_m150_shield.glb` (`Shield`), `export/mm7_m150_helmet.glb` (`Helmet`); LOD0 with props `export/mm7_m150_lod0.glb`; editable master `work/rig_v6.blend` |
| Triangles | LOD0 13,816 / 6,888 / 2,439 / 929 incl. props; body 7,718 + wings 2,200 = 9,918; sword 1,000, shield 900, helmet 2,000 (split off as attachments) |
| Meshy credits | **120 of 130** (limit raised by the user for v2): v1 45 (Smart Topology 5, auto-rig 5, body retexture 10, sword 15, head retexture 10); v2 75 (helmet 15, shield 15, Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10) |

## Anatomy decisions

- **Wings**: separate Smart Topology parts, rigged after the body (the auto-rig upload is wingless; its arms were not
  taken by the wings). Three bones per wing on the traced leading edge; the feathers follow by their span position.
  At rest the native angel holds the wings spread high (sa frames), so Standing keeps them spread (8 deg lower than the
  HD pose, a slow breath) instead of folding them; the flight beats them (top at wa, bottom at wc/wd), the attack beats
  once with the cut, the hit throws them up, the death raises them and then lays them flat beside the corpse (a search
  on the last frame for the least-height pose with every wing vertex above the floor, then a per-frame floor rule).
- **Wing size**: the HD masters' wings span 1.55 x the figure height, the native sprites ~1.2 x (sa0 211 px wide over
  179 px tall, sa4 215 px): the wings are scaled about their roots by 0.78 on the textured master (`wings_scale.py`,
  geometry and bones together); span now 2.29 m on a 1.80 m figure.
- **Walk = flight**: the native walk is horizontal flight; there is no foot contact, so Walking is authored over the
  idle pose (no Mixamo walk), hovering at the actor origin (lowest point 5 cm above the floor; no ceiling lift).
- **Arm and hand gate applies** (two arms, sword and shield): numbers below.

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m150_claude/export/mm7_m150.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m150_claude/export/mm7_m150_sword.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m150_claude/export/mm7_m150_shield.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m150_claude/export/mm7_m150_helmet.glb --world mm7
```

Then add [export/actors_binding.yml](export/actors_binding.yml) to `assets_dev/worlds/mm7/models/actors.yml` (scale
132.9 = native stand 179 px x 1.4 over the 1.886 m Standing pose to the helmet crest, B/C via `scale_reference`;
flight stride 1.88 m; blow 0.983 s; spells and ranged attacks charged and released at the sword tip; head look;
sword, shield and helmet attachments). Tier speeds 250/275/300 stay under the run threshold (319), so `run` aliases
the flight.

## Replay

Every step runs in a memory-capped scope (`scripts/cap.sh`, default 12 GB; an unguarded full SVD once took 88 GB).
`TOKEN=<lease> STAGE=rig ELBOW_FROM=meshy WRIST_FROM=meshy FOOT_MIRROR=R scripts/rebuild.sh` (v2 Smart Topology
`st_v2_parts.blend`; the right ankle ring fit caught the greave, so it mirrors the left), then
`STAGE=anim DEATH_UNTIL=12 R_HANDLE=0.013 LEAD=0.3 LEFT_CURL=0.5 SPREAD_MAX=25 SMOOTH_PASSES=6 DEATH_MAX_TURN=75 scripts/rebuild.sh`
(twice on a fresh project), then `STAGE=wings IMPACT=0.983 scripts/rebuild.sh`. Texture chain: `export_uploads.py`
(the uploads must stay byte-identical to `texturing/v2_submitted/`, or the retextures no longer match), Meshy
`retexture_v2` and `head_retexture_v2`, `transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v2 work/rig_v6.blend`.
Props: `import_sword.py` (SWORD_TRIS=1000), `import_props_v2.py` (HELMET_TRIS=2000 CLEAR=0.12 STRAP_T=0.55). Then `scripts/build_runtime.sh`
(sync clips, wing scale, helmet fit and strap weights on the master; rasters, AO, `compose_m150.py`; export, prepare,
LODs, shadow fix, region variants, sword/shield/helmet split, head merge), `viewer_tiers.py`, `update_viewer_manifest.py`.

## Gates (final v2 export)

- G3: joints in the X-ray (`review/xray2_joints_*`); hand frames from the fitted knuckle line (kn-angle <= 8 deg except
  the thumbs ~25 deg); ankles mirrored (the right ring fit sat 14 cm up the greave).
- G4: arm stretch p99 <= 1.93 (attack), max 3.63 (right hand at the cut); standing p99 1.34.
- G5: right (sword) hand <= 2.96x, left (shield) hand <= 1.79x.
- G6: skin contacts <= 0.2 cm in every living clip; in the death the sword rests 2 cm into the lying body for a few
  frames; proximity hits on the open shells (skirt, tabs) are the hands brushing them.
- Blade: edge-leading share 0.76 in the attack (cutting edge first, +0.46).
- Shield: `shield_gate.py` <= 1.9 cm (one left-arm vertex in the attack), 0 in the other clips.
- Winding: 0 inverted closed parts (body, sword, shield, helmet).
- Viewer: `tools/run_creature_review.py ... check`: 3 tiers x 7 clips, no console errors. Not checked in game
  (optional for this batch).

## Known limits / for the user to review

- LOD0 is 13.8k triangles with the props (body + wings 9.9k, helmet 2.0k, sword 1.0k, shield 0.9k), above the ~10k
  humanoid guideline; the helmet's crest and temple wings lose their shape below ~2k.
- Meshy's strap texture was replaced procedurally (steel plate, gold studs, brass rim band); the studs are painted, not
  modelled.
- The wings are skinned, not simulated; the skirt and tabs follow the thighs at 45-60 %.
- Standing keeps the wings spread (as the native sa frames), the flight is authored (no foot contact).

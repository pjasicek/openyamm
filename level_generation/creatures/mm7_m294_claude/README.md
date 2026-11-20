# MM7 Necromancer (m294) — Claude 3D model (batch F, 2026-10-20)

Batch F, model 3 ([batch file](../mm7_batches/BATCH_F.md)). Descriptors 307 Necromancer (palette 295, purple),
308 Speaker for the Dead (296, maroon) and 309 Queen of the Dead (297, grey); native frames in
[`../mm7_m294/`](../mm7_m294/). **Exported, not installed** (batch rule). Status: technically complete and
agent-reviewed in the viewer; user artistic acceptance pending.
[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m294_claude/review/viewer/) (3 tiers, 7 clips,
native frames beside each clip).

## Design deviation: covered outfit (user decision 2026-10-20)

The first HD-master request described the native outfit plainly (purple one-piece with cut-outs, thigh stockings)
and was refused by the image service (`moderation_blocked`, output stage, `safety_violations=[sexual]`, request ID
`6bdd504a-b1bf-4362-8462-a83f05029be6`; brief `references_hd/CODEX_BRIEF_v1_primary.md`). The user then overrode the
batch's no-rewording rule for this model: a non-sexualised reference of a dignified sorceress in a **fully covered**
version of the outfit. The reworded brief (`CODEX_BRIEF_v2_primary.md`) was accepted at the first attempt.

- The model wears an opaque long-sleeved, high-necked purple tunic with black/darker inset panels where the native
  sprite has openings, opaque black leggings and tall heeled boots with the gold knee chevrons. Head, white hair,
  circlet, choker, glowing eyes, the long ragged black split cape, palette and silhouette follow the native.
- So the texture pattern and the tier region differ from the sprite: the native recolours the purple cloth between
  bare skin, the model recolours the tunic's purple between black panels.
- A second decision authorised a fallback to the restored sheets (`mm7_m294/raw/standing_v2.png`, `aligned_2x/`) as
  Meshy inputs if rewording failed. It was **not used**: every Meshy input is a Codex HD master.
- All prompts and the refusal are in `references_hd/generation_runs.json` (with the decision record
  `user_override_20261020`).

## Deliverables (`export/`)

| File | What |
|---|---|
| `mm7_m294.glb` | runtime GLB: LODs 12,015 / 6,006 / 2,161 / 719 triangles + shadow LODs, tiers `m294_a/b/c` (`KHR_materials_variants`, region mask + ramps), head set merged (2080×1024 atlas) |
| `mm7_m294_lod0.glb` | portable animated LOD0 (separate body and head materials) |
| `mm7_m294.blend` | editable master (rig, clips, textures) |
| `actors_binding.yml` | copy of [`actors_m294_binding.yml`](actors_m294_binding.yml), the `actors.yml` entries to add later |

Install later (NOT run, batch rule):

```sh
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py level_generation/creatures/mm7_m294_claude/export/mm7_m294.glb   # 0 inverted (checked)
python3 tools/install_model.py level_generation/creatures/mm7_m294_claude/export/mm7_m294.glb --world mm7
```

then append [`actors_m294_binding.yml`](actors_m294_binding.yml) to `assets_dev/worlds/mm7/models/actors.yml`
(scale 120.0 = native stand 204 px × frame scale 1.0 / 1.70 m posed Standing; run → Walking because speeds 200–240
stay below 2.4 × 120; stride 1.409 m; melee and ranged attacks and spells all play Cast, release 0.633 s from the right
palm with both palms glowing) and a tier/height regression case.

## Model

- **HD masters** (`references_hd/`): `00` = run `m294_three_quarter_v2_corrective` (camera nearer 30–35° than 45°,
  arms near the cape edge); 01–04 run 3 correctives. Head turnaround (`references_head/`, four views) from the body
  masters. Hashes in `creature_3d_progress.json`.
- **Geometry**: Smart Topology 15k (14,789 triangles) of `00`. Meshy fused the body, arms, hands, tunic and the cape
  front/sides into one shell (P00). Legs and boots (P02), the hair shell (P03) and the head (P01) are separate, plus
  cape panels and lining (P04, P05, P10, P11, P15, P16), the tunic's front flap (P14), the circlet, eyes and lips.
  There is **no skin on the back of the torso**: the hair shell is the back (see Weights).
- **Labels** (`creature.json`, `prepare_rig.py`): P00 below 0.96 m becomes cape (garment 2) only in the components
  that reach the floor (the hands below the split stay garment 1). Tunic-hem vertices within 4.5 cm of the legs (z > 0.6)
  and the front flap become a "tight hem" (17).
- **Rig**: source-frame rig (`build_rig.py`, 52 `B_*` bones + twist bones + 14 × 4 robe chains, 114 bones). Joints
  come from Meshy's auto-rig. The wrists are the narrowest arm ring before the fingers separate (`arm_rings.py`
  `wrist_from_rings`, on the arm skin only, not the fused cape). Hands are rigid (open claws, no finger chains), as on
  the Warlock.
- **Weights** (`weights_robe.py`, the Warlock's robe rules plus):
  - The hair follows the trunk chain (`hair_trunk`, interpolated pelvis → head by height), because it is the back of
    the torso. A head → neck → chest blend swung it away from the back in the hit and casts.
  - The cape panels lose all arm weight to the clavicle and trunk, then are smoothed within the panels
    (`cape_no_arm`). Raised arms had pulled them up like a bat wing, and a pelvis/spine step tore one 5× in the walk.
  - The tight hem keeps Meshy's hip/thigh weights (`keep_leg_garments`). On robe chains it swung like a loose skirt
    through the thighs.
  - The rest of the cape (strips, lining, panels below the waist) follows 14 × 4 verlet robe chains baked per clip
    (`robe_sim.py`, leg capsules), with `robe_floor.py` on Death.
- **Reduction** after weighting (`reduce_rigged.py`): cape 3,974 → 2,199, hair 1,722 → 1,299, legs 2,066 → 1,500;
  face, hands and tunic kept. The hem's garment travels as a float flag, because the collapse interpolated the integer
  label and pulled three cape faces into the head set. LOD0 is 12,015 triangles (the head with its scalp is 2,268).

## Clips (humanoid set, `scripts/rebuild.sh`)

| Clip | Source and processing |
|---|---|
| Standing 2.0 s | Relax Idle, arms abducted 6° |
| Walking 0.8 s | Relax Walk Forward, stride 1.409 m (natural 211 units/s; speeds 200/220/240 play at 0.95–1.14×). Relax Walk Female was tried first: stride 0.94 m, 1.4–1.7× too slow |
| Cast 1.3 s | Unarmed Cast Dual Summon 2: arms spread wide. Planted, faced front; release at full forward reach, 0.633 s. **Also used for melee and ranged attacks** (user review 2026-10-20: the native has one action, `m295a`, for both); a separate overhead Attack (Dual Summon 1) was built first and removed |
| Hit 0.5 s | Unarmed Get Hit F1, planted |
| Death 1.3 s / Dead | Unarmed Death 1: falls backwards (native `d`); pelvis travel halved, floor pass; the cape settles flat |
| Fidget 3.33 s | Relax Talk 3 (gestures) |

Chain: retarget → `plant.py` → `face_forward.py` → `wrist_limit.py` → `caster_timing.py` → `twist_bones.py` →
`flatten_feet.py` (heeled boots at their rest pitch) → `floor_pass.py` (new: soles on the floor per frame,
smoothed) → `robe_sim.py` → `robe_floor.py` → `reduce_rigged.py` → `gates.py`.

## Gates (`review/gates_v5.json`, every half frame)

| Clip | arm p99 L/R (max) | wrist swing L/R ° | forearm twist range ° | cape p99 (max) |
|---|---|---|---|---|
| Standing | 1.16 / 1.21 (1.33) | 18 / 16 | −3..9 | 1.17 (1.43) |
| Walking | 1.24 / 1.22 (1.41) | 35 / 34 | −7..14 | 1.40 (2.17) |
| Cast | 2.35 / 1.96 (2.96) | 25 / 32 | −10..17 | 1.39 (1.95) |
| Hit | 2.19 / 1.85 (2.60) | 26 / 40 | −41..30 | 1.20 (1.46) |
| Death | 2.37 / 2.29 (3.30) | 58 / 49 | −21..35 | 2.97 (5.50, lying) |
| Fidget | 1.56 / 1.48 (1.82) | 31 / 27 | −65..53 | 1.25 (1.51) |

- G5 hands: rigid (stretch 1.00).
- G6 contacts on the closed skin (`BODY_GARMENTS=0,1,15`): no hand inside the body in any clip.
  - Against the open cape shells the hands come within 6–8 cm, inside a hanging panel, in Standing, Walking, Fidget
    and Death: the arm hangs or swings right in front of a side panel. This is a proximity contact, not a skin
    penetration.
- Cloth:
  - Robe/cape stretch as in the table.
  - `scripts/g6_cape_poke.py` (gob2 skirt gate on legs vs cape) saturates at its 5 cm search radius even in Standing,
    on the two-layer lining (P05), whose cone test cannot tell the sides apart. It is not a usable number for this cape.
  - Visual check instead: front, quarter and side close-ups of the lower body in Walking and Hit
    (`review/shots_skirt3.png`) show no leg through the tunic or cape.
- Soles (`sole_probe.py`):
  - Standing and Fidget: 0.3 cm.
  - Walking: −0.5..1.1 cm (one frame with both feet above 1 cm).
  - Cast: 0..0.9 cm.
  - Hit: −0.7..1.3 cm (two frames).
- Jerk (`jerk_probe.py`, worst step / second difference per 1/48 s, degrees):
  - Standing 0.4 / 0.1, Walking 12.9 / 8.5, Fidget 15.5 / 6.6.
  - Cast 22.5 / 13.5, Hit 28.6 / 13.1.
  - Death 42 / 23: the source's violent fall.
- Viewer: `tools/run_creature_review.py ... check`: 21 switches (3 tiers × 7 clips), no console errors. Shots of every
  clip on every tier: `review/tier_{a,b,c}_clips.png`.
- Winding: 0 inverted closed parts.

## Textures (`scripts/compose_m294.py`)

- Maps: body 1K and head 1K (Meshy retexture 2K, downsampled); body UVs carried back from Meshy's layout by face
  correspondence (`transfer_uv.py`, 0 mm mismatch).
- One tier region: the tunic's purple texels (hue 250–330°, S > 0.2, garments 1/17 and the tunic hem). The ramps come
  from the native indexed frames, indices 188–232 in palettes 295/296/297.
- **Ramp gains per tier: 0.85 / 0.8 / 0.2**, not the guide's 1.3–1.45×. Review 2026-10-20: at 1.35 tier A rendered
  as hot magenta (median sRGB 137,19,141 against the native 72,0,72). `scripts/tier_match.py` compares viewer shots
  with the native standing frames on the same purple pixels per palette.
  - The gains match the rendered chroma: A 0.255 vs native 0.263, B 0.18 vs 0.20.
  - The R/B channels also match: A 80,_,84 vs 72,_,72; B 71 vs 53.
  - The remaining difference is the viewer's neutral light floor of about +20 per channel, which also shows on tier
    C's near-black tunic (21 vs native 6).
  - Results: `review/tier_match_1.json`; side by side with the native palette frames at the same scale:
    `review/tiers_vs_native_v2.png`.
- Meshy's purple was dark with high-contrast weave noise that the ramp turned into glitter. Inside the region the
  detail above a 3-texel blur is kept at 0.35.
- Hair, skin, cape, boots and gold are unchanged in every tier, as in the native. Skin is not repainted (Meshy's face
  and hands had no patches).
- Gold is re-graded. The AO bake is graded into the base colour and also stored in ORM red.
- Material classes: `textures/m294_material_classes.png`, `textures/m294_head_material_classes.png`.

## Meshy

**30 credits**: Smart Topology 5 (primary account), auto-rig 5, body retexture 10, head retexture 10 (backup account;
the primary had 2 credits left). No paid animation (all clips from the local humanoid set).

## Known limits / for the user to review

- **Covered outfit** instead of the native cut-outs (see above).
- Tier colours were re-fitted to the native frames (deep violet / maroon / near-black); in game lighting they may need a
  final check (not run in game).
- Arm stretch p99 2.35 in the Cast (left armpit, arms spread), above the playbook's ~2 (Warlock Cast 2.96).
- Hands are rigid open claws (no finger motion).
- The cape is opaque (the native's is sheer, the body shows through it from behind).
- Death: the source fall is violent (legs swing up). The corpse lies on its back with one knee slightly raised and the
  cape panels bunched beside the legs.
- Hands brush the hanging side cape panels (6–8 cm proximity, open shell) in Standing, Walking, Fidget and Death.
- Not checked in game (the batch allows it as optional; not run).

## Reproduce

```sh
TOK=<lease> scripts/rebuild.sh all        # rig + clips + reduction + gates (about 3 minutes)
# textures (once per topology): export_uploads.py, requests/*retexture_v1.json via tools/run_creature_meshy.sh,
# transfer_uv.py work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend, uv_raster.py (UVMap, HeadUV 1024),
# bake_ao_natm.py work/rig_v6.blend 1024, python3 scripts/compose_m294.py, python3 scripts/tier_bake.py
TOK=<lease> scripts/build_runtime.sh      # sync clips into rig_v6, export, LODs, shadow fix, tiers, head merge (no install)
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
```

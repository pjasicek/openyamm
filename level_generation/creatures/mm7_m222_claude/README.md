# MM7 Chain Fighter (m222): Conscript / Soldier / Fighter — Claude rig-first project

MM7 batch A, model 1 ([batch file](../mm7_batches/BATCH_A.md)). Built on the humanoid playbook's default route
(source-frame rig with gates; scripts from `mm6_natm_claude/` with bar1's sword timing and blade rules). **Not
installed**: everything stays in this project until the user decides (batch rule).

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [clay clips](review/g7_clay_front.png) ·
[textured clips](review/g7_tex/) · [viewer shots](review/shots/) · [G1 attack candidates](review/g1_atk_front.png)

**Accepted, reduced and installed (2026-10-20):** installed 2026-10-20 from [`../mm7_batches/BATCH_A_stage/`](../mm7_batches/BATCH_A_stage/README.md). **Reduced (user: "reduce tris"):** the exports to install are now the ones in [`../mm7_m222_reduce_claude/`](../mm7_m222_reduce_claude/README.md) (body LOD0 9,666 -> 8,020, scimitar unchanged; same UVs, textures, tiers and clips; install commands there). This project's `export/` is their source and rollback.

## Deliverables

| File | What |
|---|---|
| `export/mm7_m222.glb` | runtime body: LODs 10,224 / 5,108 / 1,829 / 600 triangles (LOD0 incl. the 558-triangle scimitar before the split), shadow LODs, 3 tier variants (`m222_a/b/c`), head material merged, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget |
| `export/mm7_m222_sword.glb` | scimitar attachment on node `Sword` (558 / 278 / 100 / 32 triangles) |
| `export/mm7_m222_lod0.glb` | textured LOD0 master export (tier A base colours) |
| `work/rig_v6.blend` | editable textured master (rig, gated clips, Meshy UVs, head split) |
| `textures/` | body 1K set, head 1K set, region masks, `m222_ramps.json`, material class maps, scimitar maps |
| `integration/actors.yml` | the staged binding (three descriptors) |

Install later (user decision), from the repository root:

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m222_claude/export/mm7_m222.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m222_claude/export/mm7_m222_sword.glb --world mm7
```

then append `integration/actors.yml` to `assets_dev/worlds/mm7/models/actors.yml` (descriptors `Fighter Chain A/B/C`,
scale 96.0 = native `m222sa0` height 204 px × dsft scale 0.8 = 163.2 units over the 1.70 m model; walk stride 1.732 m,
run stride 1.8 m; attack impact 0.983 s; head look on `B_Neck`/`B_Head` 60°/35°; scimitar on node `Sword`).
Speeds 220/240/260 units/s: tier A walks (the 1.732 m Female Walk plays ~1.55x), tiers B and C exceed the engine's
run threshold (2.4 × 96 = 230 units/s) and use Running.

## Model

- HD masters (Codex, `references_hd/`, gated against `source/native_standing_views.png`): primary v3 selected over
  Codex's own pick v2 for open, spread fingers (the rig fits fingers by connectivity); four views and a scimitar
  prop sheet; head turnaround in `references_head/`.
- Smart Topology 15k (14,554 triangles after cleanup). Parts: body (torso, hair slab, legs, boots), separate arm shells
  with gauntlets and fingers, helmet, right shoulder guard, two gold panels, neck trim, 28 belt-chain links, eyes.
  Removed: two spikes behind the shoulders (Meshy's reading of the scabbard top). **Deviation:** the empty scabbard on
  the back is not modelled.
- Rig: source-frame rig (52 bones + twist bones), Meshy auto-rig for the axial joints and elbows (t 0.54/0.51), ring
  centres for wrists/ankles, fingers by connectivity on the arm shells (`fit_fingers.py` restricted to pieces 1/2).
- Weights (`weights_fix.py`): skin = Meshy + shoulder fade + jaw free of the shoulders + hair slab without arm weight;
  helmet/eyes rigid head; shoulder guard copies the skin (arm share ≤ 0.5); gold panels pelvis → thigh strips; neck
  trim copies the skin without arm weight; belt links rigid pelvis. Reduced after weighting to 9,666 triangles.
- Scimitar (`make_scimitar.py`): outline rows and planar texture from `references_hd/scimitar.png`; lens blade with
  the convex cutting edge, flat guard, 1.3 cm grip (= the solved fist), round pommel; 0.95 m. Blade roll 90° from the
  knuckle line (sweep in `blade_edge_gate.py`).

## Clips (G1, chosen before texturing from candidates rendered on this rig)

| Role | Source | Notes |
|---|---|---|
| Standing | Mixamo Standard Idle | scimitar across the thighs like `m222sa0` |
| Walking | Mixamo Female Walk | feet levelled (constant 15° tilt removed), 1.732 m stride |
| Running | Mixamo Standard Run | `run_fit.py` (pelvis 92 % of Standing + bob, 1.8 m stride) |
| Attack | Mixamo Sword And Shield Slash (2) | arms spread, overhead raise, downward chop, low follow-through (native `m222a*`); planted + 20 % of its legs, stepped feet (bar1 `clip_timing`), 0.3 s ready pause, trunk twist ≤ 45°; blow 0.983 s vs the native 1.0 s attack |
| Hit | humanoid set Unarmed get-hit F1 | eased 0.2/0.2 s, floor pass |
| Death | Mixamo Falling Back Death | falls backward, legs up (native `m222d*`); travel halved, floor pass |
| Fidget | Mixamo Sword And Shield Power Up | planted, stepped feet |

`sword_clear.py` (natm's spear clearance on the blade chord, 20 cm search) turns the hand ≤ 30° where the blade
enters the body (death, run, hit; then again on the timed attack/fidget, twist re-baked by `rebake_twist.py`).

## Gates (2026-10-20, final master and export)

- G3: frame error 0; hand frames within 25° of the carried source except the thumbs (30°/49°; their chains are fitted from the mesh).
- G4: arm edge stretch p99 ≤ 1.85, max 2.62 (clavicle at the raise).
- G5: right hand ≤ 2.02x (solved fist, every finger clears the 1.3 cm handle), left ≤ 3.19x (source curl).
- G6 (`g6_contacts.py`, half frames, inside test ≤ 6 cm): no blade, forearm or hand inside the skin, except the Death
  right hand 3.0 cm while lying and 0.3–0.5 cm brushes. The right fist touches the gold panel's surface in Standing/Hit
  (proximity count only).
- Feet (`sole_probe.py`): grounded soles within −1.5…+1.5 cm after a constant 1.1 cm walk lift (`clip_timing.py`); jerks (`jerk_probe.py`) follow the sources (attack: the
  source's overhead whip, sword tip up to 40 m/s for ~0.05 s, a smooth bell — kept).
- Blade (`blade_edge_gate.py`): at the impact the convex edge leads (+0.95); edge-leading share attack 0.68, walk 0.83,
  fidget 0.78, hit 0.97, run 0.89.
- Viewer: `tools/run_creature_review.py check` 24/24 tier/clip switches, no console errors; shots in `review/shots/`.
- In game: not checked (optional in batch A; nothing installed).

## Textures and tiers

`compose_m222.py`: body and head 1K sets from Meshy (body retexture with Meshy's own UVs copied back exactly by
`transfer_uv.py`, head retexture on our head UVs); skin repainted to one albedo × Meshy's fine shading (same albedo on
the head, no neck seam); AO graded; ORM red = per-class specular mask, green = roughness, metallic 0. Two recolour
regions as the native masks: **R = green cloth** (neck trim, arm band, sash), **G = hair**; ramps per tier from the
tier's own palette entries (indices 207–230 / 153–167) over the native stand/walk/attack pixels, rank-matched (gain
1.3 cloth, 1.15 hair): A 223 green / brown, B 224 blue / ginger, C 225 red / blonde.

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

Feet (review 2026-10-20, "slightly angled on the boot edge"): the project's `foot_level.py` also levels the sole's roll
about the heel–toe line on grounded frames (the clips had rolled the boots onto their outer edges; the rest pose is
flat) and moves the pelvis by the change of the lowest sole point, so floor contact is unchanged; the run gets
`Running:rollonly`. Soles and gates re-measured after the rebuild (`review/gates_final.txt`). Walk and run take one constant roll per foot in the foot's own frame and one constant pelvis shift (review 2026-10-20: the per-frame roll switched on and off as the feet landed and lifted, a visible ankle twitch; foot rotation per frame is back to the source's). Hit, Attack, Fidget, Death and Standing: the roll is weighted by flatness (planted and level lengthwise), capped at 20 deg and smoothed over the clip (batch C's rule, mm7_m218_claude; peer report 2026-10-20: the groundedness-only roll snapped a stepping foot in Hit up to 22 deg and a lifting foot in Death up to 65 deg per frame); every clip's foot turn per frame is now within 2 deg of the source's. Walk bob (review 2026-10-20, "uneven head bob"): `walk_bob.py` after `clip_timing.py` smooths the walk's pelvis height over the loop (both steps alike, ankles kept reachable) and re-solves the legs to the same ankle paths and foot rotations; the retarget's floor rule had left a zigzag and up to 3.7 cm frame jumps.

## Replay

```sh
TOKEN=<lease> scripts/rebuild.sh            # STAGE=rig, then STAGE=anim (LEAD=0.3 DEATH_UNTIL=12 R_HANDLE=0.013)
python3 scripts/make_scimitar.py && <blender> scripts/make_scimitar.py
# textures once: export_uploads.py -> Meshy jobs -> transfer_uv.py -> uv_raster.py (UVMap, HeadUV) -> bake_ao_natm.py
python3 scripts/compose_m222.py
TOKEN=<lease> scripts/build_runtime.sh       # no install step
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
```

## Known limits / for user review

- The scabbard on the back is not modelled; the fist touches the gold panel in Standing.
- Tier A walks at ~1.55x the clip's natural speed; tiers B/C always run at full speed.
- The attack's overhead swing is fast (source whip).
- The hit raises the sword arm so the blade passes close in front of the face (no contact).

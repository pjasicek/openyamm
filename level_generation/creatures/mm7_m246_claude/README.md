# MM7 Goblin (m246): Goblin / Hobgoblin / Goblin Lord — Claude rig-first project

MM7 batch F, model 2 ([batch file](../mm7_batches/BATCH_F.md)). Rig-first route of `mm6_gob2_claude/` on a two-armed
non-human body, scripts from the batch A sword fighters (`mm7_m406_claude/`). **Not installed** (batch rule).

[Review viewer](review/viewer/index.html) (serve the repository over http, e.g. port 8912) · [tiers](review/tiers_zoom.png) ·
[attack (downward chop)](review/attack_sheet.png), [G1 attack](review/g1_attack_downward_sheet.png), [clips](review/clips_sheet1.png), [more clips](review/clips_sheet2.png) · [hands](review/hc_sheet.png) · [gates](review/gates.txt)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m246.glb` | runtime body: LODs 11,061 / 5,528 / 1,934 / 588 triangles before the split (body alone 10,431 / 5,214 / 1,822 / 553), shadow LODs, 3 tier variants `m246_a/b/c`, head material merged, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget |
| `export/mm7_m246_sword.glb` | broadsword attachment on node `Sword` (630 / 314 / 112 / 35 triangles) |
| `export/mm7_m246_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export and editable master (rig, gated clips, Meshy UVs, head split) |
| `textures/` | body 1K set, head 1K set, region masks (R vest, G navy cloth), `m246_ramps.json`, material class maps, sword maps |
| `actors_m246_binding.yml` | the staged `actors.yml` binding (Goblin A/B/C) |

Install later (user decision), from the repository root:

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m246_claude/export/mm7_m246.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m246_claude/export/mm7_m246_sword.glb --world mm7
```

then append `actors_m246_binding.yml` to `assets_dev/worlds/mm7/models/actors.yml` (descriptors `Goblin A/B/C`,
scale 110.0 = native `m246sa0` 187 px × dsft scale 1.0 over the 1.70 m model, crest included in both; walk stride
1.748 m measured, run stride 1.8 m; attack impact 1.017 s; head look on `B_Neck`/`B_Head` 60°/35°; broadsword on
`Sword`). Speeds 160/170/180 are below the run threshold (2.4 × 110 = 264): every tier walks (clip at ~0.83–0.94x).
Both GLBs pass `check_winding.py` (0 inverted closed parts).

## Model

- HD masters (Codex, `references_hd/`): primary v3 selected over Codex's own pick v2 for straight, spread fingers
  (one targeted hands/arms correction); four views and `broadsword.png`; head turnaround in `references_head/`.
- Smart Topology 15k (15,598 triangles, 98 parts, nothing removed): body shell (head, torso, arms, trousers, boots),
  separate hands, crest (a long plume hanging down the back), hair, vest, helmet, bracers, belt, pauldron (left), left
  upper-arm plate, strap, ten hip panels, shin guards, cheek pieces, goatee, eyes and 65 spikes/studs. Reduced after
  weighting to 10,431 (head, hands and every piece ≤ 40 triangles protected) — about 4 % over the ~10k guideline.
- Rig: source-frame rig; Meshy shoulders/clavicles (left/right mirror-averaged: the pauldron lifted Meshy's left side
  1.8 cm), elbows, wrists and ankles (`FOOT_FROM=meshy`: the ring ankle locked onto a shin guard); fingers by
  connectivity on the hand shells; the open A-pose thumb points along the fingers, so `fit_fingers.py` re-cuts it along
  its own axis (21 → 47 vertices).
- Weights (`weights_fix.py`, by garment): skin = Meshy + shoulder fade + jaw free; helmet, eyes, cheek pieces, goatee
  rigid head; crest rigid at the root, blending to one back target toward the tip (70 %) so the plume bends instead of
  entering the back; hair copies the skin (no arm weight) and is smoothed along its own edges (20 passes); vest/strap/belt
  copy without arm weight; bracers, plates and shin guards copy as is; pauldron arm share ≤ 0.5; hip panels pelvis →
  thigh with one left/right mixture per strip; spikes and studs one uniform weight set each.
- Broadsword (`make_sword.py`): outline rows and planar texture from `references_hd/broadsword.png`; single-edged
  seax-like blade (wedge section, edge on prop +X), crescent quillons, crossbar, 1.3 cm grip (= the solved fist),
  ball pommel; 1.09 m. Blade roll 15° from the knuckle line (sweep on the downward chop; the cutting edge leads at the blow).

## Clips (G1: chosen from the batch A sword set and checked on this body; Attack replaced after user review 2026-10-20)

| Role | Source | Notes |
|---|---|---|
| Standing | Mixamo Standard Idle | `author_carry.py`: blade diagonally up across the body like `m246sa0` |
| Walking | Mixamo Walk | feet levelled (constant tilt/roll), 1.3 cm lift, walk bob smoothed |
| Running | Mixamo Standard Run | `run_fit.py` (1.8 m stride) |
| Attack | Mixamo Standing Melee Attack Downward + authored lower body | the ogre's overhead chop (user review 2026-10-20; `mm6_ogr_claude/`, `mm7_m178_claude/`), planted, 0.13 s ready pause eased from the carry; the blade goes back over the head and comes down at the target, edge first. **Legs drive the blow** (second user review 2026-10-20: the planted feet took no part): `author_attack_legs.py` + `attack_legs.json` (playbook natm rules, native `m246ac`/`ad` raise a knee and step) - the pelvis sinks 4 cm and draws back 5 cm as the sword goes overhead, then drives 12 cm forward and 8 cm down into the chop; hip yaw (0.35 x the chest's turn, 50 ms ahead of it; the trunk keeps the source chest's world turn) leads; small extra lean (the source already flexes the trunk at the blow); one lunge step of the left foot 28 cm forward (7 cm sine lift, frames 16-26) landing just before the blow, held, stepped back over frames 46-57 (4 cm lift); the rear heel peels up to 20 deg about the ball with the toes flat; legs by IK with the knee over the toes, the pelvis lowered where a leg cannot reach (0.6 cm). Blow 1.017 s (fastest tip motion while pointing forward; native 1.0 s). Renders `review/attack_sheet.png`, `review/attack_feet_sheet.png`, `review/g1_attack_legs_clay.png` |
| Hit | humanoid set Unarmed get-hit F1 | eased 0.2/0.2 s, floor pass |
| Death | Mixamo Falling Back Death | travel halved, floor pass; `arm_clear.py` up to 44° and `sword_clear.py` up to 75° on the fall |
| Fidget | Mixamo Sword And Shield Power Up | planted; the descriptor's fidget group is the standing group in game |

## Gates (2026-10-20, final master `work/rig_v5.blend` and export; numbers in `review/gates.txt`)

- G3: frame error 0; hand frames 85/89° rest swing, fingers within 2–42° of the carried source, thumbs 64°/76° (their chains are fitted from the mesh).
- G4: arm edge stretch p99 ≤ 1.87, max 2.80 (every 6th frame of every clip; the chop's hand roll reaches ~150° against the forearm rest at the overhead, ramped by the twist bones; the wrist close-ups `review/hcd_sheet.png` show no wrap).
- G5: hand stretch ≤ 2.94x right (solved fist), ≤ 3.24x left (attack 3.10x); grip finger clearance 0.3–1.8 cm on the 1.3 cm handle.
- G6 (`g6_contacts.py`, half frames): no forearm, hand or blade inside the skin in Standing, Walking, Running, Attack,
  Hit, Fidget (≤ 0.6 cm brushes). **Death:** the blade base 5.9 cm at frame 29 while falling (t 0.22 m from the grip,
  next to the shoulder) — `sword_clear.py`, which keeps the shoulder skin in its test, reports it clear, so this is
  probably the gate's arm-excluded open shell; the renders show the blade passing close behind the falling body. Right
  hand ≤ 1.8 cm in Death.
- Head clearance ≤ 0.3 cm (Hit; the chop's raised arm keeps ≥ 1.2 cm from the head; the right hand brushes the thigh 1.2 cm at the end
  of the lunge follow-through, frame 39); crest/hair vs body ≤ 0.2 cm
  (`g6_crest.py`); crest/hair stretch ≤ 2.35x (attack 2.08x), hip panels ≤ 1.95x (`g4_skirt.py`).
- `g6_skirt_poke.py` reports 5.0 cm (its search radius) in every clip including Standing; not visible in the renders
  (`review/close_sheet2.png`) — treated as a metric artefact (gob2 saw the same).
- Soles: grounded −2.2…+1.5 cm (attack: the stepping foot lifts 5.3 cm in its step, the planted feet stay −2.2…−0.8, the
  Standing rest height; no sliding: the planted left foot holds its spot, the rear foot moves only by its heel peel about
  the ball). Attack pelvis path: max 3.0 cm per frame, second difference 1.46 cm (walk 1.23); feet steps ≤ 2.3°/frame. Jerk: the sources' own profiles (same values as the batch A fighters on the same clips;
  attack peak tip speed 44.0 m/s for ~0.05 s with the 1.1 m blade).
- Blade (`blade_edge_gate.py`, `EDGE_LOCAL_X=1` for this single straight edge, roll 15°): at the blow the cutting edge
  leads (+0.91); edge-leading share attack 0.71, walk 0.87, run 0.85, fidget 0.82, hit 0.90.
- Viewer: `claude_shared/check_viewer.mjs` and `run_creature_review.py check` 24/24 tier/clip switches, no console errors.
  In game: not checked (nothing installed; the machine was busy with the parallel batch).

## Textures and tiers

`compose_m246.py`: body/head 1K sets (Meshy UVs copied back exactly; head retexture on our head UVs: face, helmet,
cheek pieces, goatee); green skin repainted to one albedo shared by both sets; AO graded; ORM red = per-class specular
mask; class maps. Two recolour regions as the native masks: **R = vest** (palette indices 156–180; the vest piece plus
the teal-painted skin under its open sides) and **G = navy cloth** (indices 181–254: trousers, right bracer, left
sleeve). Tiers from `mm7_m246/variants.json`: A 247 (olive vest, green cloth), B 248 (the art's own blue), C 249 (red
vest, brown cloth). Ramp gain 1.0 (the guide's 1.3 made the dark scaled navy read pale grey-blue next to the native).

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10. No paid animation.

## Replay

```sh
TOKEN=<lease> STAGE=rig FOOT_FROM=meshy SYM_SHOULDERS=1 WRIST_FROM=meshy ELBOW_FROM=meshy scripts/rebuild.sh
TOKEN=<lease> STAGE=anim DEATH_UNTIL=12 R_HANDLE=0.013 LEAD=0.15 LEFT_CURL=0.5 SPREAD_MAX=25 SMOOTH_PASSES=6 \
  DEATH_MAX_TURN=75 DEATH_ARM_MAX=44 scripts/rebuild.sh   # LEAD=0.15 since the downward chop (2026-10-20)        # twice on a fresh project (grip_pose.json)
python3 scripts/make_sword.py && <blender> scripts/make_sword.py
# the attack's legs: author_attack_legs.py runs inside rebuild.sh (AUTHOR_ATTACK_LEGS=1, attack_legs.json)
# textures once: export_uploads.py -> Meshy jobs -> transfer_uv.py (rig_v6) -> uv_raster.py (UVMap, HeadUV) -> bake_ao_natm.py
# after a re-weight: carry_uv.py work/rig_v5.blend work/rig_v6_tex1.blend work/rig_v6.blend
python3 scripts/compose_m246.py
TOKEN=<lease> scripts/build_runtime.sh                     # BLADE_ROLL default 15       # no install step
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
TOKEN=<lease> scripts/gates.sh                               # + g6_crest.py, STRIPS=1,2 g4_skirt.py, blade_edge_gate.py
```

## Known limits / for user review

- User review 2026-10-20 (2): the chop's lower body is authored (lunge step, pelvis drive, hip lead, heel peel); the
  previous planted-feet master is `work/rig_v5_preattackfeet.blend` / `work/rig_v6_preattackfeet.blend`.
- User review 2026-10-20: Attack replaced by the overhead downward chop (previous Sword And Shield Slash (2) build kept
  as `work/rig_v5_slash2.blend` / `work/mm7_m246_slash2_export.glb`).

- Death: the blade passes close behind the falling body around frames 27–31 (gate reading 5.9 cm, see G6).
- LOD0 body 10,431 triangles (~4 % over the guideline); the 65 spikes and studs are kept whole.
- The crest is a horsehair plume hanging down the back (HD master reading of the native's curled segmented crest);
  it bends with the head. The cheek pieces were painted as hair by the head retexture; the goatee reads dark red-purple.
- Blade texture is rust-red down the middle as in the HD prop reference (the native blade reads more silver).
- Tier navy cloth reads lighter than the native's darkest folds (scale highlights through the ramp).

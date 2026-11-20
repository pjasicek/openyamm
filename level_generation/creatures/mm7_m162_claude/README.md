# MM7 Behemoth (m162) — Claude 3D model, batch E

Young Behemoth / Behemoth / Ancient Behemoth (monsters 208–210, sprite groups m163/m164/m165, palettes 163/164/165).
Batch E ([../mm7_batches/BATCH_E.md](../mm7_batches/BATCH_E.md)): the model stops at project exports; nothing is
installed or bound.

![tiers in the review viewer above the native palettes](review/tiers_vs_native.png)

| Item | Value |
|---|---|
| Export | `export/mm7_m162.glb` (LOD0–3 + shadow LODs, three tier variants, body and head merged into one material) |
| Editable sources | `work/rig_v3.blend` (rig + clips), `work/rig_v4.blend` (textured master as exported), `export/mm7_m162_lod0.glb` |
| Triangles LOD0/1/2/3 | 14,752 / 7,322 / 2,453 / 643 |
| Skeleton | 52 `B_*` bones (humanoid set frames) + forearm/upper-arm twist bones; finger bones unweighted (claws ride the hands) |
| Clips (30 fps keys) | Standing 4.03 s, Walking 1.43 s, Running 0.87 s, Attack 1.87 s (impact 0.856 s), Hit 1.10 s, Death 3.33 s, Dead 1.0 s, Fidget 5.40 s |
| Textures | body 1K + head 1K (Meshy retextures), merged into a 2080×1024 atlas; one region (mane + beard), ramps from palettes 163/164/165 |
| Meshy credits | **30 of 100**: Smart Topology 5, auto-rig 5 (joints rejected, see below), body retexture 10, head retexture 10 |
| Viewer | `http://127.0.0.1:8912/level_generation/creatures/mm7_m162_claude/review/viewer/index.html` — check: 3 tiers × 8 clips, no console errors |

## Anatomy decision

The native frames (`../mm7_m162/native/`) show a hunched, ape-like biped: it stands and walks on its two short, bowed
legs (walk `m162w*2`: the hands swing clear of the ground, they never carry weight), and attacks with one arm raised
overhead and brought down (`m162a*0`, `m162nb0`). Two working arms on an upright body, so it takes the **humanoid
playbook** on the `mm6_gob2_claude/` non-human-body route (source-frame rig, `B_*` skeleton, retargeted clips), not the
quadruped route.

- **No horns.** The batch note calls it horned; the native sprites (all views, x2 restorations) show none. The large
  upper and lower tusks are the only head spikes. The HD masters added small pointed ears (kept; they read as part of
  the head silhouette).
- **Hands: three long sickle claws, rigid on the hand bone.** No finger chains and no grip to solve. Every skin vertex
  connected to the paw beyond the wrist plane is 100 % `B_<s>_Hand` (`weights_heat.py`), so no claw tip follows a knee.
- **The hunch is the rest pose, motion is relative to it.** The clips are Mixamo's mutant family (Warrok). The plain
  world-rotation copy (`retarget_mixamo.py` default) copies the set's upright T-pose: the horizontal neck came out
  vertical and the head looked at the sky. With `MX_REF` every bone copies its world rotation change from the mutant
  idle's first frame onto our rest frame, so Standing frame 0 is exactly the modelled native posture. Human one-shots
  (hit, death) use `:self`: the change from the clip's own first frame (against the idle they un-hunched the body).
- **Tiers:** only the mane and beard change colour (green 163, blue-violet 164, red 165): one region.

## Route (replay)

1. HD masters (`references_hd/`, Codex, gated; brief `CODEX_BRIEF.md`) and a head turnaround (`references_head/`).
2. Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`): 14,752 triangles, one skin piece
   plus 356 small pieces (≈270 mane shingles, teeth, tusks, eyes). Normalised to 2.20 m (`step1_clean.py`).
3. **Joints.** Meshy's auto-rig (`rig_v1`, 5 credits) misread the hunched body (feet joints 50 cm behind the legs,
   head joint in the chest; `review/xray_meshy_sheet.png`) and was not used. Joints were read from orthographic grid
   views and horizontal sections of the skin (`grid_plot.py`, `hsections.py`; `review/grid_joints_v1.png`) into
   `work/joints_final.json`. The arms are asymmetric like the three-quarter master (right hand 25 cm further forward).
4. `scripts/rebuild.sh <token>` replays the rest: `build_rig.py` (source frames) → `weights_heat.py` (heat weights on
   a hole-filled voxel proxy at 2.2 cm — 1.5 and 3 cm made the solver fail on every vertex — copied back by Data
   Transfer; claws rigid; head/jaw/ear skin head+neck only; mane shingles copy the skin under them, arm share ≤ 0.25,
   half averaged per shingle) → `retarget_mixamo.py` (`scripts/mx_clips.txt`) → `clip_finish.py` → `twist_bones.py`.
5. Textures: `export_uploads.py` (body upload + head faces in front of the skull base with their own `HeadUV`),
   retextures, `transfer_uv.py` (Meshy UVs back by face; 21 of 14,752 faces off by > 5 mm), `garments.py`,
   `uv_raster.py`, `bake_ao_natm.py`, `compose_m162.py`.
6. `scripts/build_runtime.sh <token>`: sync clips → `export_runtime.py` → `prepare_actor_glb.py` → `build_actor_lods.py`
   → `shrink_shadow_lods.py` → `region_variants.py` → `merge_head_material.py`. Viewer: `viewer_tiers.py`,
   `update_viewer_manifest.py`.

## Clips

| Clip | Source | Notes |
|---|---|---|
| Standing | Mixamo Mutant Breathing Idle | the reference pose: frame 0 = the modelled hunch |
| Walking | Mixamo Mutant Walking (`:inplace`) | stride 2.57 m per 1.43 s cycle; arms abducted 9° (the forearms went 7 cm into the thighs) |
| Running | Mixamo Mutant Run | lifted out of the floor only (flight phases kept); stride 2.83 m: the in-place clip's feet do not plant (foot-slide measure 1.35 m was wrong); the Creature Pack copy with root motion travels 2.081 m per 0.867 s cycle against 1.894 m for Mutant Walking, scaled by our walk's 2.573 / 1.894 |
| Attack | Mixamo Mutant Swiping (`:turn`) | right arm raised overhead facing the party (native `m162nb0`), wind-up 1.6× faster, the source's mid-slam spin replaced by a 0.25 s ease into its slam pose (left claws into the floor in front), source recovery. Impact 0.856 s |
| Hit | Mixamo zombie reaction hit (`:self`) | first 1.1 s, eased out; rears up with the arms out like `m162na0`/`nb0` |
| Death | Mixamo Zombie Dying (`:self`) | staggers, kneels, falls flat on its face (native corpse `m162xa0`); travel halved; chosen from four forward deaths by corpse flatness. Mutant Dying fell on its back and lay 50 cm up on the mane |
| Dead | last Death pose, 1 s | |
| Fidget | Mixamo Mutant Roaring | |

## Gates (rig_v3 / export)

- **G4 arm stretch** at the clip extremes: p99 ≤ 1.91, max ≤ 3.1 (`g4_weights.py`).
- **Edge stretch** (`outliers.py`, every second frame): max 4.7 after the head-weight rule (the ear tip had stretched
  101× on clavicle weight).
- **Soles** (`sole_probe.py`): Standing, Walking, Attack, Hit, Fidget grounded at 0.0 cm every frame; Running flies.
- **Jerk** (`jerk_probe.py`): Attack head 12°/step, forearm 31° — at or below the source's own (17.8° / 31.9°);
  the first cut (source spin kept with the chest held on the party) had a 1000°/s whip and was replaced.
- **G6 contacts** (`g6_claws.py`, forearms and claws vs the rest of the skin): Standing, Walking, Running, Attack, Hit:
  0 cm; Dead 2.3 cm; Fidget right claws 3.5 cm against the head (roar); **Death 1.9–2.4 s: the right claws pass up to
  14 cm through the kneeling calf for ~0.4 s while it collapses** (abduction and forward swing were tried; the collapse
  curls the arms into the belly or the legs either way). Mane shingles brush the forearms in walk (proximity only).
- Viewer: `tools/run_creature_review.py check`: 24 tier/clip switches, no errors.

## For the user to review

- The hide follows the HD masters (pale stone grey with a dark blue-grey chest); the native sprite's hide is darker
  and bluer. Darkening the skin is a compose change, no new Meshy job.
- The Death transient above, and whether Mutant Roaring suits the Behemoth's fidget.
- LOD0 is Smart Topology's full 14,752 triangles (no LOD0 reduction yet; the mane shingles are about a third).
- The head texture uses 20 % of its 1K layout (Smart UV islands with margins); a repack would need a new head retexture.

## Install later (not run)

**Reduced version:** [`../mm7_m162_reduce_claude/`](../mm7_m162_reduce_claude/README.md) (2026-10-20) — install its
`export/mm7_m162.glb` (the command below) instead of this one; the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m162_reduce_claude/export/mm7_m162.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (scale = native stand 132 px × frame scale 2.0 ÷ 2.20 m):

```yaml
- descriptor: Behemoth A
  model: worlds/mm7/models/mm7_m162.glb
  scale: 120.0
  yaw_offset: -1.570796327
  skin: m162_a
  animation:
    sockets: {}
    cast: Attack
    run: Running
    stride_length: 2.573
    run_stride_length: 2.83
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 25
    events:
      attack_melee: {impact: 0.856}
      attack_ranged: {impact: 0.856}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
# Behemoth B / C: the same with skin m162_b / m162_c and scale_reference: Behemoth A (their native frame scales
# 2.2 and 2.5 make them 1.1x and 1.25x larger)
```

No in-game check was run (optional for batch E); the model was checked in Blender renders and the project viewer.

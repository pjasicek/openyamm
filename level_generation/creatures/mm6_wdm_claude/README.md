# MM6 flying demon (wdm) — from-scratch rebuild, 2026-10-07

Replaces the Codex derivative and the first Claude rework (`../mm6_flying_demon_3d/`). DemonFly A/B/C (499–501, Devil
Captain / Master / King), installed as `assets_dev/worlds/mm6/models/mm6_wdm.glb`, opt-in via `debug.actor_models=true`.
Review: <http://127.0.0.1:8901/level_generation/creatures/mm6_wdm_claude/review/viewer/>.

## Current route: HD references → four-view Meshy model (`hd_multiview_v1`)

The first rebuild (below) fed Meshy enlarged sprite frames; face, claws and skin came out soft at any texture size.
The current model starts from HD reference art instead.

| Item | Value |
|---|---|
| References | Codex image generation, `references_hd/` (brief `CODEX_BRIEF.md`; front, back, left, right, three-quarter, 1024×1536) |
| Model | Meshy `multi-image-to-3d` (meshy-7.1, front/left/back/right, textured, PBR, 2k, remesh 20k tris), 30 credits |
| Triangles LOD0/1/2/3 | 24,863 / 12,421 / 4,472 / 1,489 (with the grafted head) |
| Rig | own (`rig_hd.py`): mixamorig body + Wing_L/R Root/Arm/Lead/Finger1–3, 34 bones, 0 unweighted vertices |
| Clips | same `anim_wdm.py` as below (Flight 3.0 s, Attack, Cast, Hit 0.75 s, Death 1.0 s, Dead) |
| Texture | Meshy's own 2k base colour (painted from the HD references), gentle AO grade |
| Tiers | one texture; skin tinted by `openyamm_tint` inside the mask (MR red channel) |
| Meshy credits | 95 of 135 (35 first rebuild + 30 HD model + 30 HD head; budget reset to 100 after the first 35) |

Steps:
1. `prepare_hd.py` — import, weld UV-seam splits, scale to 1.8 m, centre, feet at z 0 → `work/hd_base.blend`;
   copies the Meshy textures to `textures/hd_*.png`.
2. `split_wings_hd.py` → `work/wing_mask.npy` (region grown from the wing tips through vertices behind the back
   surface or above the head); check `review/wing_split_hd_*.png`.
3. `rig_hd.py` → `work/rig_hd.blend` (joints pinned from measurements; same seam weighting as below); `stress_wdm.py`.
3b. `graft_head.py` → `work/rig_head.blend` (see Head graft below).
4. `anim_wdm.py` on `work/rig_head.blend` → `work/anim_v1.blend`; `sheet.py` for a contact sheet.
   (`work/anim_lowres_old.blend` keeps the first rebuild.)
5. `dump_uv3d.py` → `compose_hd.py`: base colour kept; tint mask = purple skin texels off the membrane
   (`review/texture_classes.png`). Tier A's tint reproduces the source skin colour; B/C use their native palette's
   skin chroma (685, 683) with the same saturation boost and relative luminance. Scaling the purple by a palette
   ratio gave orange instead of the native olive for B.
6. `bake_creature_ao.py` on `work/rig_hd.blend`, then
   `grade_basecolor.py --ao textures/wdm_ao_2k.png --ao-strength 0.5 --local 0.4 --contrast 1.08 --saturation 1.1
   textures/wdm_basecolor.png`.
7. `build_runtime.sh --install`, `viewer_tiers.py`, `update_viewer_manifest.py`.

Checks: MM6 actor regression suite 9/9; in game `review/ingame_3d/` (Abandoned Temple hall, `work/tmp/tour_3d.yml`).

### Head graft (review 2026-10-08: "teeth stretched, eyes stretched, face needs to be much more defined")

The full-body references gave the face ~70 px, and the head got 1,452 triangles and 8% of one 2k texture. Fix: a
separate head model.
1. Codex head turnaround `references_head/` (front, three-quarter, right profile, back; 1254², bust cut below the
   jaw; brief `CODEX_BRIEF.md`, input = the accepted body HD views).
2. Meshy `head_v1` (multi-image-to-3d, 12.5k tris, own 2k texture), 30 credits; decimated to ~6.2k tris in the graft
   and the base colour shipped at 1k (runtime cost; no visible loss at close range).
3. `graft_head.py` on `work/rig_hd.blend` -> `work/rig_head.blend`: scale 0.165 + offset fitted by overlay
   (`work/tmp/overlay.py`); old head (Head weight > 0.5) and body faces inside the new head deleted; body rim
   (open edges within 3 cm of the head only; Meshy leaves other small holes, e.g. at the right foot) pulled just
   inside the head; the lowest 4 cm of the head's neck pulled under the body surface; weights from
   the 6 nearest non-wing body vertices; head = material slot 1 `DemonHead`; wing flag kept as point attribute.
4. `compose_head.py`: skin luminance matched to the body skin, tint mask = magenta hues (330-350, fading to 358)
   so mouth/tongue/gums, ivory and eyes stay untinted. Same tier tints as the body.
5. `export_glb.py`, `add_variants.py`, `viewer_tiers.py` handle both materials (Demon_*, DemonHead_*).

Wings (same review: "wings are overlapping"): the flap now sets an absolute root-to-tip elevation (native about
-6..42 deg, capped at 46) instead of adding to the HD rest pose, which already sits at 44 deg.
`check_stretch.py` lists edges that grow > 5 cm and > 3x in any clip, with their vertices' weights.
`check_wings.py` reports midline crossings and the closest left-right gap per clip (now 0 and >= 10 cm).

LOD0 24,863 triangles (body ~18,600 + head ~6,200). GPU textures (uncompressed RGBA8 + mips, shared by all instances
and tiers): body 2k base + 1k normal/MR, head 1k base/normal/MR, about 39 MB. Meshy credits 95 of 135.

### Texture/triangle pass (2026-10-08, CLAUDE_CREATURE_TEXTURES.md)

- **Body reduced 20,563 -> 10,999 triangles** before rigging (`reduce_body.py`: collapse decimation, vertices on
  edges folded > 60 deg kept; Decimate collapses only its vertex group, so the group is inverted). Meshy's atlas is
  fragmented (72% of vertices on a UV seam), so collapsing it in place smeared the texture at seams; `bake_reduced.py`
  gives the reduced mesh a fresh unwrap (smart project 89 deg, concave pack: 42% coverage, no flips/overlaps) and
  bakes base colour, roughness and a tangent normal from the 20k body (Cycles selected-to-active, 2K).
  Checks: same-camera textured views (full, wing, hand, foot) 20k vs 14k/11k/9k; 9k faceted the claws and forearm
  silhouette, 11k showed no loss; extreme poses (arms up/forward, leg kick, twist) match the 20k rig.
  LOD0/1/2/3 now 16,086 / 8,040 / 2,895 / 962 (body ~9.8k after the head graft + head 6.2k).
- **Body base colour 1K** (`wdm_basecolor_graded_1k.png`, from the graded 2K master): in-game captures at the same
  spawn and camera show no difference from 2K.
- **Region mask + ramps** instead of `openyamm_tint`: `compose_hd.py` / `compose_head.py` write
  `wdm_region_mask.png` / `wdm_head_region_mask.png` (skin in R); `compose_ramps.py` writes `wdm_ramps.json`
  (per tier 16 linear stops from that tier's native palette 684/685/683, albedo factor fitted so tier A reproduces
  the accepted look, 1.69; per material 2nd/98th percentile luminance range on the runtime base colour).
  `add_variants.py` embeds the masks and writes `openyamm_region_mask` / `openyamm_region_ramps`;
  `viewer_tiers.py` bakes the same rule for the three.js viewer. Grading stays before masks/ramps.

- **Scale 103 -> 130** (2026-10-08): the native fly frames are 285 logical px tall x frame scale 0.70 = 200 units
  for tier A, the Flight wingbeat's front silhouette was 153 units at 103 (about 23% small). Matching the silhouette
  area gives 130 (height and wingspan agree within 5%). B and C keep `scale_reference: DemonFly A`, so the engine
  multiplies by their frame scales (0.75/0.70, 0.80/0.70): about 139 and 149; regression
  `mm6_wdm_actor_model_tiers_follow_sprite_scales` checks the ratios and the tier A height band.

Pipeline order now: `prepare_hd.py` -> `reduce_body.py` (on hd_base) -> `bake_reduced.py` -> `split_wings_hd.py`
(on hd_reduced) -> `rig_hd.py` -> `graft_head.py` -> `anim_wdm.py` -> `dump_uv3d.py` -> `compose_hd.py` ->
`compose_head.py` -> `bake_creature_ao.py` + `grade_basecolor.py` -> `compose_ramps.py` -> `build_runtime.sh`
-> `viewer_tiers.py` -> `update_viewer_manifest.py`.

## First rebuild (superseded): sprite-frame Smart Topology + retexture

| Item | Value |
|---|---|
| Model | Meshy Smart Topology from the restored spread-wing frame `wdmflyd0` (3D wings included) |
| Triangles LOD0/1/2/3 | 15,507 / 7,753 / 2,788 / 924 |
| Meshy credits | 35 (Smart Topology 5, two auto-rigs 10 — not used, see below — retextures 2 × 10) |

### Pipeline (scripts/)

1. `split_wings.py` — wing vertices = connected region behind the back plane, seeded by the outer membrane
   (`work/wing_mask.npy`); also writes a wingless body for the Meshy auto-rig.
2. Meshy auto-rig: on the full mesh it mapped the arms onto the wings; on the wingless body it gave an asymmetric,
   zig-zag spine (right shoulder 11 cm high, right-arm weights in the head). Not used beyond left-side limb hints.
3. `measure_body.py` → `rig_wdm.py` — skeleton from measured limb centrelines and Meshy's left joints mirrored about
   the body midline (x = −0.025); Blender automatic weights for the body; wing vertices get inverse-distance weights
   to the wing segments (front plane) blended into Spine2 at the root; separate pieces bound rigidly.
4. `uv_export.py` (neutral rest mesh) → Meshy retexture `retexture_v2` with **Meshy's own UVs**
   (`enable_original_uv: false`, four restored 2× views) → `transfer_uv.py` (the returned mesh has the same faces,
   normalised; UVs copied face by face, 1 µm match) → `dump_uv3d.py` → `compose_wdm.py` (skin to native A colour,
   membrane to native membrane colour, tint mask = skin minus wings, `tints.json`) → `bake_creature_ao.py` +
   `grade_basecolor.py --ao-strength 0.4 --local 0.25 --contrast 1.05 --saturation 1.1`.
   The first texture (`retexture_v1`) used a Blender Smart UV Project: ~1,040 islands (620 of ≤ 4 faces), and Meshy's
   paint broke into per-island blobs. A seam-based unwrap crushed the head, hands and feet. Let Meshy unwrap.
4b. `add_claws.py` — Meshy left both ring fingers as clawless stubs: the stub's end cap is removed and a claw is
   grown from the finger's own rim loop (tapering rings along the neighbour claw's direction, length and curl; UVs
   from the matching spot on the neighbour claw, one per face) → `work/rig_claws.blend`. Pasting a copy of the
   neighbour claw looked stuck on (its base is the neighbour's whole, wider fingertip).
5. `anim_wdm.py` (on `work/rig_claws.blend`) — Mixamo FBX clips (`mixamo/`, downloaded by the user) retargeted by direction + twist, each source
   turned to face forward at its first frame and time-windowed; layers: hover lean/bob, dangling legs, wing flap on
   the native 0.75 s cycle (+ raises the wing), Flight arms relaxed 60 % toward hanging; action clips blend from/to
   Flight. `--preview` keys full-length sources for picking windows (`sheet.py`).
6. `build_runtime.sh --install`; `viewer_tiers.py` bakes the tints into per-tier GLBs for the three.js viewer, then
   `update_viewer_manifest.py` (hashes + cache-busting URLs).

Mixamo sources: Floating (Flight), Zombie Swipe Attack 0.35–1.45 s (Attack), Wide Arm Spell Casting 0.25–1.40 s
(Cast), Standing React Large From Front (Hit; recoil 0–0.8 s for Death). Treading Water was tried: it swims horizontally.

Wing attachment (reviews 1-3): Meshy built the wing membrane continuous with the back skin (no separate back
surface; the membrane is part of a closed shell), so cutting it away opens holes in the body - do not cut. Instead:
the wing mask is grown into the leading-edge strut/hook (`split_wings.py`) and excludes the torso width (back skin);
body heat weights are computed with the wing bones non-deforming; wing vertices near the seam blend into the body by
geodesic distance - into Spine2 over 10 cm at the shoulder blades, into the weights of the waist skin they grow from
over a 30 cm web lower down, blended smoothly across z 1.30-1.50; the back skin around the seam follows Spine2 over
8 cm. Check with an edge-stretch heatmap per clip and back three-quarter close-ups with back-face culling.

In game (first rebuild): [3D vs sprites](review/wdm_3d_vs_sprites.png) (Abandoned Temple hall, top 3D).

## Clip timing (2026-10-10)

`anim_wdm.py` plays the Attack and Cast source windows at source speed ([audit](../CLIP_TIMING_AUDIT_20261010.md);
they were x1.47 / x1.53 in 0.75 s). Cast gets a 0.15 s ready pause (source pose eased in, wings beating). The script
prints the markers: claw blow (peak claw speed) 0.646 s into the 1.08 s Attack, cast release (hands widest) 0.75 s
into the 1.29 s Cast -> actors.yml `events` (ranged fire leaves `Socket_Palm_Right`). Wing check 0 crossings,
worst stretch unchanged (7.4 cm). Previous build: `work/anim_v1_pre_clip_timing.blend`; sheet `review/timing_sheet.png`.

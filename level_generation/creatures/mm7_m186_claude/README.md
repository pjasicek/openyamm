# MM7 Dragonfly (m186) — 2026-10-20

> **Reduced (2026-10-21):** install the texture-aware reduction from [`../mm7_m186_reduce_claude/`](../mm7_m186_reduce_claude/README.md)
> (`export/mm7_m186.glb`: body 7,227 / 3,612 / 1,805 / 889, wings 666; MeshLab ladder from the unreduced UV master,
> same textures, tiers, clips and binding). This project's own export used Blender's Decimate, which the retopology
> playbook rules out; keep it only for reference.

Batch H, model 3 ([BATCH_H.md](../mm7_batches/BATCH_H.md)). Identity **mm7:m186**, descriptors **226–228**
(Dragonfly, Fire Dragonfly, Queen Dragonfly), palettes 187 / 188 / 189, frame scales 0.5 / 0.7 / 1.2. Route:
[non-humanoid playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) (Meshy model, own rig, procedural clips, flyer floor rules),
with the segmented-body ideas of the snake and spider notes. Not installed (batch rule).

| Item | Value |
|---|---|
| Export | [`export/mm7_m186.glb`](export/mm7_m186.glb), 6.0 MB, sha256 `07385a5153e9593b53deb55c962eaebdae8ee2fec3537fa183f20702b3d9381d` |
| Triangles | body LOD0 / 1 / 2 / 3: 7,502 / 3,748 / 1,874 / 920; wings 666 (own node, no LODs) — Smart Topology 15,522 |
| Rig | 19 bones: Thorax (root), Abd1–10, Claw, Neck, Head, ForeWing_L/R, HindWing_L/R; `HeadSocket` |
| Clips | Fly 1.0 s loop, Attack 0.875 s, Cast 0.875 s, Hit 0.875 s, Death 1.125 s, Dead 1.0 s |
| Materials | `Dragonfly_A/B/C` (shared skin, region R = green spine crest); `DragonflyWing_A` alpha-blended, double-sided, alpha 0.62, same images |
| Maps | 2K base colour (graded), 1K normal (+Y up), 1K metal/rough (R specular mask), 1K region mask |
| Meshy | **15 / 30 credits**: Smart Topology `meshy-t2.5` 15k (5), retexture `meshy-7` (10) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m186_claude/review/viewer/) |

## References

`references_hd/` (Codex, 1536×1024, two runs, records in `generation_runs.json`): head with orange-red compound eyes,
ivory hooked mandibles and gold bristles, green spine crest, long segmented brown abdomen hanging in the native
S-curve, three-prong olive claw with silver tips, four translucent wings with red-brown veins. Inputs were only the
original bitmaps (`native_views.png` = spread fly frame `m186wc0–4`, `native_identity.png` = side/front frames).
Codex noted margins under the requested 70 px on the primary and front views; nothing is cropped.

## Model and rig

Meshy returned one body/head/claw piece, four separate wing plates, two claw prongs and about 60 small pieces (crest
spines, bristles, mandibles). `rig_plan.py` traces the abdomen centerline numerically (surface shortest path claw →
head, refined to cross-section centroids, smoothed), spaces ten abdomen joints evenly by arc length and weights the
body by hat functions of each vertex's arc position; the head and claw ends are rigid, each wing is bound 100 % to its
bone and every small piece takes the weights of its nearest body vertex (the bloodsucker rule). The first weighting
(nearest segment, half blends) made a sawtooth abdomen in the lunge; the arc-position weights fixed it
(`review/r0_side.png`). `rerig.py` moved the bones and weights on the UV master, so the retexture UVs stayed valid.

## Motion (`anim_dfly.py`)

- **Fly** (native wa–wh, 16 ticks): six wing beats per loop, fore and hind pairs in opposition, a slow wave down the
  abdomen, the claw opening and closing, a small hover bob. Every action ends on whole beats, so it returns exactly to
  the Fly start pose.
- **Attack** (aa–ag, 14 ticks): coils, then lunges with the abdomen swung out horizontally behind the striking head
  (native ae/af), bite at 0.55 s. **Cast** (no native frames; Fire Dragonfly and Queen cast Fire Bolt and the engine
  needs a Cast distinct from Attack): rears up with wings high, then snaps the head forward, release at 0.5 s.
- **Hit** (na–ng): jolt back, twist, wings flung. **Death** (na–nc, da–df, 18 ticks): flinch, wings fold up, the body
  straightens and drops; the corpse lies flat on thorax and abdomen with the wings raised (native `xa`), head lifted
  so the bristles do not prop it up. Dead holds it.
- Floor (`clip_check.py` → `review/clips_r1.json`): Death/Dead rest at 2 mm; flight clips stay within −6 mm of the origin.

## Textures (`compose_dfly.py`) and reduction

Meshy kept our Smart UV layout (head islands 2.5×). Base colour padded and AO-graded (wings without AO). Region R =
green crest texels; tier ramps take the native crest colours (palette indices 228–255 of the fly frames) by luminance
rank in palettes 187 / 188 / 189 (gain 1.25): green, blue, red crests; everything else is the same in every tier, as in
the native palettes. Fit mean / p95 (8-bit): A 7.6 / 22.7, B 4.4 / 13.1, C 8.0 / 23.8 (the native crest has strong
shading; the ramp keeps Meshy's detail). `reduce_lod0.py 0.45 0.7 0.5 0.5` after weighting: 15,522 → 8,168, textured
rest and Attack renders identical to the source, head close-up included (`review/r0_sheet.png`, `review/r1_sheet.png`).

The wings are their own mesh node and material so they can be translucent like the sprite's; they draw blended after
the opaque body and cast no shadow. They do not change between tiers.

## Size

Scale **124** from the mean front silhouette area of the native fly frames (`m186w?0`, frame scale 0.5) against the
Fly clip (`measure_scale.py` → `work/scale.json`): rest height about 65 units (native sprite about 82), wings reach
88 units, span 119 units. The descriptor collision heights are only 20 / 30 / 50, so the model (like the sprite)
extends well above its collision box; low ceilings can clip it.

## Checks

`check_winding.py`: 0 inverted closed parts. `run_creature_review.py check`: 3 tiers × 6 clips, no console errors.
Shots in `review/shots/`. No in-game check (optional in the batch rules). Not verified: how the engine sorts the
blended wing primitive against other transparent effects in game.

## Rebuild

`rig_plan.py` → `rig_dfly.py` → `anim_dfly.py` → `uv_export.py` → `dump_uv3d.py` → (retexture) → `bake_ao.py` →
`compose_dfly.py`; weight/bone changes on the UV master: `rig_plan.py` → `rerig.py work/uv_master.blend` →
`anim_dfly.py work/uv_master.blend work/uv_master.blend`; then `reduce_lod0.py 0.45 0.7 0.5 0.5 work/uv_r1.blend` →
`anim_dfly.py work/uv_r1.blend work/uv_r1.blend` (keys the final corpse pose) → `scripts/build_runtime.sh TOKEN`.

## Install (installed 2026-10-21, reduced export)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m186_reduce_claude/export/mm7_m186.glb --world mm7
```

```yaml
# Dragonfly m186: palettes 187/188/189 (crest only), descriptors 226-228. B and C cast Fire Bolt.
- descriptor: Dragonfly A
  model: worlds/mm7/models/mm7_m186.glb
  scale: 124
  yaw_offset: -1.570796327
  skin: m186_a
  animation:
    cast: Cast
    run: Fly
    stride_length: 3.2       # Fly at its own rate at monster speed 400: 400 x 1.0 s / 124
    run_stride_length: 3.2
    upper_body_root: Neck
    sockets:
      head: HeadSocket
    events:
      attack_melee:
        impact: 0.55
      attack_ranged:
        impact: 0.55
        release: head
      cast:
        impact: 0.5
        glow:
        - head
        release: head
  clips:
    standing: Fly
    walking: Fly
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fly
# Dragonfly B / C: same entry with skin m186_b / m186_c and `scale_reference: Dragonfly A` (0.7 / 0.5 and 1.2 / 0.5).
```

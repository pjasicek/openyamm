# MM7 Bat (m158) — 2026-10-20

> **Reduced export (2026-10-21):** install the texture-aware reduction from
> [`../mm7_m158_reduce_claude/`](../mm7_m158_reduce_claude/README.md) instead of this project's export: LOD0 6,084
> (from the unreduced 15,216; this project's Blender-decimate export below is 8,818), same textures, tiers, clips and
> binding. `python3 tools/install_model.py level_generation/creatures/mm7_m158_reduce_claude/export/mm7_m158.glb --world mm7`

Batch H, model 2 ([BATCH_H.md](../mm7_batches/BATCH_H.md)). Identity **mm7:m158**, descriptors **205–207** (Giant Bat,
Vampire Bat, Inferno Bat), palettes 159 / 160 / 161, frame scales 1.0 / 1.1 / 1.2. Route: [quadruped playbook,
flyers](../CLAUDE_QUADRUPED_PLAYBOOK.md#flyers-mm6-bat-mm6_bat_claude) with the MM6 bat scripts
([mm6_bat_claude](../mm6_bat_claude/README.md)) adapted. Not installed (batch rule).

| Item | Value |
|---|---|
| Export | [`export/mm7_m158.glb`](export/mm7_m158.glb), 6.5 MB, sha256 `87792decbeb06bcf450dc0095e55532afc6d6b9075a100726cd45e7f592b432a` |
| Triangles LOD0 / 1 / 2 / 3 | 8,818 / 4,395 / 2,186 / 1,083 (Smart Topology 15,216, reduced after weighting) |
| Rig | 31 bones: Spine1–2, Neck1, Head, per side UpperArm/ForeArm, Finger1–4 a/b, Thigh/Shin, Ear; `HeadSocket` |
| Clips | Fly 1.1667 s loop, Attack 0.8333 s, Hit 0.8333 s, Death 0.875 s, Dead 1.0 s |
| Maps | 2K base colour (graded), 1K normal (+Y up), 1K metal/rough (R specular mask, G roughness, B 0), 1K region mask |
| Tiers | one shared skin, region R = wing membrane; ramps from palettes 159 / 160 / 161 (`textures/bat_ramps.json`) |
| Meshy | **15 / 30 credits**: Smart Topology `meshy-t2.5` 15k (5), retexture `meshy-7` four HD views (10) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m158_claude/review/viewer/) |

## References

`references_hd/`: five Codex masters (1536×1024, `CODEX_BRIEF.md`, two runs: primary first, then the four views with
the frozen primary as input 1; prompts, input hashes and raw returns in `generation_runs.json`). Inputs were only the
original native bitmaps: `native_views.png` (spread fly frame `m158wc0–4`, 3× nearest) and `native_identity.png`
(close frames). Gate: shaggy grey-brown fur, very large pink ears, red eyes, white fangs, green membrane with pink
veins and pink finger bones, pink feet, no tail; same pose in all five; 03 faces image left, 04 image right. Codex
noted that back/left margins are under the requested 70 px (nothing cropped) and the side views keep some
three-quarter projection; accepted, as they only feed the retexture.

## Model, rig and motion

- Meshy returned the wing membranes as separate pieces from the body/arm-bone piece; Blender automatic weights
  still solved (7 leftover vertices took their nearest weighted neighbour). Wing joints are top-view (x, y) with z
  sampled from the sheet (`rig_bat.py`); the hand wing is raised about 35° in the rest pose, as in the masters.
- `stress.py`: wings up/down/folded and a sprawl show no tearing (`review/stress_sheet.png`).
- `anim_bat.py` (from the MM6 bat): Fly = native wa–wh (wings high "U" upstroke, low sweep, elbow and finger lag,
  fingers fold on the upstroke); Attack = native aa–ag (wings raised, then swept down and forward around the target
  while the head bites, impact 0.44 s); Hit = jolt back with wings flung up; Death = flinch, then drops onto its belly
  with the wings laid flat at belly height (native corpse `xa`); Dead = held. Durations follow the native ticks
  (19 / 13 / 13 / 14 × 1/16 s) in whole 24 fps frames.
- Floor (`clip_check.py` → `review/clips_r1.json`): Death ends at 0.3 mm above z = 0 and Dead holds there; flight clips
  dip below the origin by design (wing downstroke −0.14 m, attack sweep −0.23 m, body ≥ −0.046 m), as the other flyers.
- Reduction (`reduce_lod0.py 0.5 0.75`, after weighting): body/wings 50 %, head/ears 75 % → 8,820 triangles; textured
  renders of rest and Attack, head close-up included, match the 15,216 source (`review/r0_sheet.png`,
  `review/r1_sheet.png`). Not pushed further (MM6 bat ships 8.7k).

## Textures (`compose_bat.py`)

Meshy kept our Smart UV layout (head islands at 2.5× density). Base colour padded into the gutters, AO-graded
(`bake_ao.py`, AO 0.6, contrast 1.08, saturation 1.12; no local contrast, the atlas has many small islands). Membrane
= green texels; the tier ramps rank its texels by luminance and take the native membrane colours of the same rank
(palette indices 64–207 of the fly frames) in each palette, albedo gain 1.3. Fit error mean / p95 (8-bit):
A 3.5 / 10.2, B 2.5 / 8.9, C 5.8 / 17.8. Fur, ears, bones, eyes and teeth do not change between tiers, as in the
native palettes. Material classes `textures/bat_material_classes.png` (fur, skin, membrane, tooth, eye). Edge
shadow-LOD shrink is capped at 1 mm (single-sheet membrane).

## Size

Scale **212** from the mean front silhouette area of the eight native fly frames (`m158w?0`, frame scale 1.0) against
the model's Fly clip (`measure_scale.py` → `work/scale.json`). At that scale the upstroke tops out at 110 units, above
the 96-unit collision height of all three tiers (B/C larger by 1.1 / 1.2), so very low ceilings can clip the wing tips,
as noted for the MM6 bat. Span 216 units.

## Checks

- `check_winding.py`: 0 inverted closed parts. `run_creature_review.py check`: 3 tiers × 5 clips, no console errors.
- Tier and clip shots in `review/shots/`. No in-game check yet (optional in the batch rules).

## Rebuild

Under the project lease: `scripts/rig_bat.py` → `anim_bat.py` → `uv_export.py` → `dump_uv3d.py` → (retexture) →
`bake_ao.py` → `compose_bat.py` → `reduce_lod0.py 0.5 0.75 work/uv_r1.blend` → `scripts/build_runtime.sh TOKEN`
(export, material contract, prepare, LODs, shadow fix, ramps, viewer tiers, winding check). Blender scripts run via
`tools/run_creature_blender.sh --token TOKEN level_generation/creatures/mm7_m158_claude/scripts/<script> [args]`.

## Install (installed 2026-10-21, reduced export)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m158_reduce_claude/export/mm7_m158.glb --world mm7
# (reduced export; this project's own export/mm7_m158.glb is the earlier 8,818-triangle version)
```

```yaml
# Bat m158: palettes 159/160/161 (membrane only), descriptors 205-207. Bat C (Inferno Bat) also shoots fire.
- descriptor: Bat A
  model: worlds/mm7/models/mm7_m158.glb
  scale: 212
  yaw_offset: -1.570796327
  skin: m158_a
  animation:
    cast: Attack
    run: Fly
    stride_length: 1.5       # Fly plays at its own rate at monster speed 280: 280 x 1.167 s / 212
    run_stride_length: 1.5
    upper_body_root: Spine2
    sockets:
      head: HeadSocket
    events:
      attack_melee:
        impact: 0.44
      attack_ranged:
        impact: 0.44
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
# Bat B / Bat C: same entry with skin m158_b / m158_c and `scale_reference: Bat A`.
```

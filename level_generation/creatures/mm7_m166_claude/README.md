# MM7 Beholder (m166) — 2026-10-21

> **Reduced export (2026-10-21):** install the texture-aware reduction from
> [`../mm7_m166_reduce_claude/`](../mm7_m166_reduce_claude/README.md) instead of this project's export: LOD0 6,814
> (from the unreduced 15,154; this project's Blender-decimate export below is 9,419), same textures, tiers, clips and
> binding. `python3 tools/install_model.py level_generation/creatures/mm7_m166_reduce_claude/export/mm7_m166.glb --world mm7`

Batch H, model 4 ([BATCH_H.md](../mm7_batches/BATCH_H.md)). Identity **mm7:m166**, descriptors **211–213**
(Floating Eye, Gazer, Evil Eye), palettes 167 / 168 / 169, frame scales 1.5 / 1.55 / 1.6. Route:
[non-humanoid playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md), floating-head section (reference `mm6_bh_claude`), with the
arc-position chain weights of the dragonfly. Not installed (batch rule).

| Item | Value |
|---|---|
| Export | [`export/mm7_m166.glb`](export/mm7_m166.glb), 6.9 MB, sha256 `194030d0df4951b5bb85d6fbf602eda2afdab341844b8310a5c9f6cff59a53f2` |
| Triangles LOD0 / 1 / 2 / 3 | 9,419 / 4,707 / 2,352 / 1,172 (Smart Topology 15,154) |
| Rig | 56 bones: Body (hover root), Head, Tongue, EyeSocket (non-deforming, at the painted iris), Tentacle1–8 × 5 + Tentacle9 × 3, Stalk1–4 × 2, StalkEye |
| Clips | Fly 1.5 s loop, Attack 0.9167 s, Hit 0.75 s, Death 1.125 s, Dead 1.0 s |
| Tiers | one shared skin, mask R tentacle tips (per tier), G head flesh, B tentacle shafts (native colours, same in all tiers) |
| Maps | 2K base colour (graded), 1K normal (+Y up), 1K metal/rough (R specular mask), 1K region mask |
| Meshy | **15 / 30 credits**: Smart Topology `meshy-t2.5` 15k (5), retexture `meshy-7` (10) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m166_claude/review/viewer/) |

## References

`references_hd/` (Codex, 1024×1536 portrait, two runs, records in `generation_runs.json`): brain-folded head, one
big green central eye, ivory teeth, orange tongue, golden drool, four eye stalks, eight separated tentacles with
green leaf tips. Inputs were only the original bitmaps (`native_views.png` = hover frame `m166wa0–4`,
`native_identity.png`). The masters are redder than the native brown flesh; the G/B regions correct that (below).
Codex noted margins under 60 px on some views; one tentacle tip grazes the frame edge in 01/03/04 (retexture inputs
only).

## Model and rig

Meshy pieces: head (with the painted central eye and the drool), tongue (piece 11), 19 teeth, eight tentacles plus a
short ninth one at the back, four stalks with their eyeballs. `rig_plan.py` traces each tentacle and stalk from its
attachment to its far end (surface shortest path, cross-section centroids, smoothing) and weights it by arc position
between its bones (root few mm follow the head); head, teeth and drool are rigid to Head, the tongue to Tongue.
`fix_rig.py` (on the UV master, UVs kept): the first plan called piece 11 the eyeball; it is the tongue, so the bone is
`Tongue` and `EyeSocket` sits at the painted iris (located from the retexture). The top-left stalk's eyeball is split
off (`mesh.split`) onto its own `StalkEye` bone for the death. That split reordered the vertices, so piece ids for
texture masks and reduction come from `piece_map.py` (`work/piece_master.npy`, matched by position, max error 3e-8 m).
Stress poses (`review/stress_sheet.png`): curled, flung, bent stalks, tipped body: no tearing.

## Motion (`anim_bh.py`, native tier-A timing, 3 ticks of 1/16 s per pose)

- **Fly** (wa–wh): hover bob and sway, every tentacle waves with a lag along its chain and its own phase, stalks sway.
- **Attack** (aa–ae): draws back with tentacles flared while the eye charges, thrusts forward at the release (0.6 s).
- **Hit** (na–nd): recoil, twist, tentacles flung. **Death** (wa0 wb0 da–dd): shudder, the stalk eye pops off, arcs up
  and falls beside the body; the head drops onto the floor and the tentacles drape flat around it; Dead holds it
  (native corpse `xa`: body on the floor, a loose eye beside it).
- Gates (`clip_check.py` → `review/clips_r1.json`, reduced mesh): every action ends exactly on the Fly start pose;
  Death/Dead rest at 2 mm (head, stalk eye) with no vertex under the floor; hover clips dip at most 3.7 cm below the
  origin (tentacle tips).

## Textures (`compose_bh.py`) and reduction

Meshy kept our Smart UV layout. Base colour padded and AO-graded. Regions: R tips (green texels on the tentacles) take
the native tip colours (palette indices 141–239 that are green in 167) of each palette by luminance rank (gain 1.25):
green / blue / red; G head flesh takes the native brown flesh (indices 16–111, gain 1.4) and B the tentacle shafts the
native greys (gain 1.35), identical in all three tiers. Eyes, stalks, tongue, teeth and drool keep their paint. Fit
mean / p95 (8-bit): tips 9.5–12.7 / 28–38 (the native tips run from near-black to bright green), flesh 8.6 / 21.9,
shafts 4.4 / 12.6. `reduce_lod0.py 0.5 0.45` after weighting: head flesh 50 % with the faces within 7.5 cm of the
painted iris kept (an eye texture tears under collapse, `mm6_bh_reduce_claude`), tentacles 45 %, stalks, tongue and
teeth kept; textured renders and the eye close-up match the source (`review/r0_*.png`, `review/r1_*.png`).

## Size

Scale **286** from the mean front silhouette area of the native hover frames (`m166w?0`, frame scale 1.5) against the
Fly clip (`work/scale.json`): about 279 units tall (descriptor height 267), span 240.

## Checks

`check_winding.py`: 0 inverted closed parts. `run_creature_review.py check`: 3 tiers × 5 clips, no console errors.
Shots in `review/shots/` (the viewer's auto-framing crops the head in some shots). No in-game check.
For review: the split stalk leaves an open stalk tip once its eye has popped (visible on the corpse).

## Rebuild

`rig_plan.py` → `rig_bh.py` → `anim_bh.py` → `uv_export.py` → (retexture) → `fix_rig.py` →
`anim_bh.py work/uv_master.blend work/uv_master.blend` → `dump_master_co.py` → `piece_map.py` → `dump_uv3d.py` →
`bake_ao.py` → `compose_bh.py` → `reduce_lod0.py 0.5 0.45 work/uv_r1.blend` → `scripts/build_runtime.sh TOKEN`.

## Install (installed 2026-10-21, reduced export)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m166_reduce_claude/export/mm7_m166.glb --world mm7
# (reduced export; this project's own export/mm7_m166.glb is the earlier 9,419-triangle version)
```

```yaml
# Beholder m166: palettes 167/168/169 (tentacle tips), descriptors 211-213. Ranged attackers, no spells.
- descriptor: Beholder A
  model: worlds/mm7/models/mm7_m166.glb
  scale: 286
  yaw_offset: -1.570796327
  skin: m166_a
  animation:
    cast: Attack
    run: Fly
    stride_length: 0.73      # Fly at its own rate at monster speed 140: 140 x 1.5 s / 286
    run_stride_length: 0.73
    upper_body_root: Head
    look:
      nodes: [Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 30
    sockets:
      eye: EyeSocket
    events:
      attack_melee:
        impact: 0.6
      attack_ranged:
        impact: 0.6
        glow:
        - eye
        release: eye
  clips:
    standing: Fly
    walking: Fly
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fly
# Beholder B / C: same entry with skin m166_b / m166_c and `scale_reference: Beholder A`.
```

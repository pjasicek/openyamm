# MM7 Peasant Goblin Female (m442): 9 outfits/tiers — Claude rig-first project

MM7 batch K, model 5 ([batch file](../mm7_batches/BATCH_K.md)). Humanoid playbook default route (source-frame rig with
gates) on the armed scripts of [`mm7_m226_claude`](../mm7_m226_claude/README.md) (solved fist, prop on a `Sword` bone,
clearance) plus the [`mm7_m352_claude`](../mm7_m352_claude/README.md) fixes; goblin proportions per `mm6_gob2_claude`
(curved blade tested on its real shape). No attack, no run. **Not installed.** No image-service refusal occurred.

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [viewer shots](review/shots/) ·
[clay clips](review/g7_clay_front.png) · [G1 candidates](review/g1_front.png) · [sickle roll](review/roll_r90_Standing0_right.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m442.glb` | runtime body: LODs 9,534 / 4,758 / 1,690 / 545 triangles (10,310 / 5,146 / 1,828 / 591 incl. the sickle before the split), shadow LODs, 9 variants `m442_aa` .. `m442_cc`, head material merged (4 atlases 2080×1024), clips Standing, Walking, Hit, Death, Dead, Fidget |
| `export/mm7_m442_sickle.glb` | sickle attachment on node `Sword` (776 / 388 / 138 / 46 triangles) |
| `export/mm7_m442_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export (tier `ab` base colours, palette 141) and editable master |
| `textures/` | body 1K set, head 1K set, region masks (R purple cloth, G hair), `m442_ramps.json`, class maps, sickle maps |
| `integration/actors.yml` | staged binding for the nine descriptors |

Install later (user decision), from the repository root:

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m442_claude/export/mm7_m442.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m442_claude/export/mm7_m442_sickle.glb --world mm7
```

then append `integration/actors.yml` to `assets_dev/worlds/mm7/models/actors.yml` (descriptors `Peasant Goblin female
<A|B|C> <A|B|C>` = monsters 430–438; scale 118.8 = `m442sa0` 202 px × sprite scale 1.0 over the 1.70 m model; stride
1.127 m; look 60°/35°; sickle on `Sword`). Speed 140 < 2.4 × 118.8: run → Walking. The native attack slots reuse the
walk sprites (`m44Nw`), so `attack_melee`/`attack_ranged` play Walking (no impact event); cast → Standing.

## Variants

One mesh, rig and clip set for all nine looks (identical native frames, drawn in palette 141). Two recolour regions
(`scripts/compose_m442.py`, palette entries from `mm7_m442/variants.json` regions): R = purple cloth (vest stripes,
trousers), G = hair (`native_palette_spatial_support` 118–145); ramps per palette from the native stand/walk pixels,
cloth window 30–97 % of the native luminance distribution.

| Skin | Descriptor | Palette | Cloth / hair |
|---|---|---|---|
| m442_aa | A A (430) | 139 | green / olive |
| m442_ab | A B (431) | 141 | purple / black (the native base) |
| m442_ac | A C (432) | 145 | blue / dark grey |
| m442_ba | B A (433) | 146 | brown / brown |
| m442_bb | B B (434) | 147 | black / orange |
| m442_bc | B C (435) | 148 | olive / grey |
| m442_ca | C A (436) | 149 | white / green |
| m442_cb | C B (437) | 390 | black / grey-white |
| m442_cc | C C (438) | 391 | tan / brown |

## Model

- HD masters (Codex, `references_hd/`): primary v2, four views and `sickle.png` (prop alone); head turnaround in
  `references_head/`. Gated against `source/native_standing_views.png`.
- Smart Topology 15k (15,145 triangles, 46 parts): one fused body shell (head, ponytail, vest, blouse with the wide
  sleeves, sash, trousers, boots), hands P01 (left) / P02 (right), fringe, eyes, ribbon bow and tails, 37 eyelets and
  toggles. Reduced after weighting to 9,534 (skin 8,199 with head and hands protected, eyelets 500).
- Rig: source-frame rig, Meshy auto-rig joints (elbows t 0.53 / 0.53), fingers by connectivity on the hand shells;
  hand frames within 15° except the right middle/pinky directions (33° / 40°; chains inside the fingers, `review/handx_*`).
- Weights (`weights_fix.py`): skin = Meshy + shoulder fade + jaw free; fringe, eyes, ribbon bow rigid head; ribbon tails
  head → neck → chest; eyelets rigid on the dominant bone; **sleeve rule**: arm-dominated skin (the wide sleeve hems)
  loses its pelvis/lower-spine/leg weight to its own arm.
- Sickle (`make_sickle.py`, then `sickle_geo.py` for the frame): outline traced from `references_hd/sickle.png`
  (crescent ear-clipped, 4 mm plate, planar texture), octagonal 1.4 cm handle (= the solved fist), 0.46 m; blade roll
  90° (the crescent rises above the forward-pointing handle; `review/roll_*`).

## Clips (G1: candidates rendered on this rig, `review/g1_front.png`)

| Role | Source | Notes |
|---|---|---|
| Standing | Mixamo Standard Idle | upper arms abducted 8° (`abduct_arms.py`: the sleeve hems went 6 cm into the thighs) |
| Walking | Mixamo Female Walk | abducted 8°, feet levelled; stride 1.127 m |
| Hit 1.0 s | Mixamo Standing React Large From Front, planted | staggers with the sickle arm up (native `m442n*`) |
| Death 2.2 s | Mixamo Falling Back Death | falls backward, legs up (native `m442d*`); travel halved, floor pass. The native throws the sickle; ours keeps it in the fist (no separate prop animation) |
| Fidget 4.5 s | Mixamo Look Around, planted | abducted 14°; turns and looks round (native `m442f*`) |

Right fist solved around the handle (`grip_solve.py`, spread now the fingers' mean ±10°: the independent spread
alternated +38°/−33° and tore the webs 6.4x); left hand 55 % of the source curl. `sword_clear.py` turns the hand ≤ 9°
where the crescent (real outline points) would enter the body.

## Gates (2026-10-20, `work/gates_v5.txt`)

- G4 arm stretch p99 ≤ 1.63 except Death left 2.23 (the fall); Standing/Walking ≤ 1.41.
- G5 hands: right ≤ 3.20x, left ≤ 2.27x.
- G6: no sickle contact in any clip; forearms ≤ 2.6 cm except one sleeve-lining vertex in Hit (5.3 cm, left) and the
  right sleeve hem into the thigh during the fall (Death, a few frames, source motion).
- Soles: Standing −1.1 cm, Walking −1.4…+1.4 cm, Hit/Fidget 0…0.9 cm. Jerk follows the sources.
- Viewer: `tools/run_creature_review.py check` 54/54 tier/clip switches, no console errors; shots in `review/shots/`.
- In game: not checked (optional in batch K; nothing installed).

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

## Replay

```sh
python3 scripts/make_sickle.py && <blender> scripts/make_sickle.py        # sickle shape, texture, work/props.blend
TOKEN=<lease> STAGE=rig scripts/rebuild.sh; TOKEN=<lease> STAGE=anim scripts/rebuild.sh   # twice on a fresh project
# textures once: export_uploads.py -> Meshy jobs -> transfer_uv.py -> uv_raster.py (UVMap, HeadUV) -> bake_ao_natm.py
python3 scripts/compose_m442.py && python3 scripts/tier_preview.py
TOKEN=<lease> scripts/build_runtime.sh        # no install step
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
CLIPS="Standing:90 Walking:35 Hit:30 Death:66 Fidget:134" TOKEN=<lease> scripts/gates.sh
```

## Walk and ankle fix (user review 2026-10-20)

Batch A/J's walk fixes, applied in the chain and replayed; previous masters kept as `work/*_prewalkfix.blend`:
`foot_level.py` updated to batch A's rule (constant roll per foot for the walk, flatness-weighted capped roll elsewhere;
the per-frame roll switched on and off as each foot landed) and `walk_bob.py` after `clip_timing.py` (even pelvis bob,
legs re-solved to the same ankle paths). Head height second difference 2.90 → 0.53 cm (`scripts/walk_probe.py`); foot
rotation step change ≤ 13.4° (the Female Walk's own); viewer check 54/54.

## Sickle grip fix (user review 2026-10-20: "palm should be toward the torso"; then "this is NOT right")

Root cause (present since the build): `grip_solve.py` chose the palm side from the rest fingertips, but the A-pose
goblin fingertips lie level with the knuckles (dot 0.02), and the test picked the BACK of the hand. The handle was
placed on the back, the fingers bent backwards round it, the thumb (rooted 8.4 cm from the handle) could not reach,
and any roll that turned the "palm" in actually turned the back of the hand in. The palm side now comes from the
source fist's own curl centres (dot +1.0). With it the fist closes normally: handle 1.4 cm radius against the palm,
fingers on the handle surface (1.35-1.67 cm from its axis), the thumb closed over the index finger's middle phalanx
(`THUMB_TARGET=index`; the knuckle segment is not pulled onto the handle, `FIST_PULL_FROM=1`).
The carry (batch J's `author_carry.py` + `carry.json`, Standing/Walking/Fidget: wrist beside the right hip, handle
forward 6° out and 10° down in the pelvis frame) now takes the hand roll within 40° of the one whose palm faces the
body (`PALM_IN=1`): palm normal 0.96-0.99 toward the body midline, wrist swing ≤ 8.8° / 8.5° / 11.6°; the blade end
points forward and the crescent rises from it. Hit and Death keep their source arms (eased from the carry).
Gates re-run (`scripts/gates.sh`): no sickle contact in any clip; right fist ≤ 4.04x (middle/ring web); arm p99 ≤ 2.23;
soles −1.4…+1.9 cm; viewer 54/54. Probes: `scripts/palm_dir.py` (palm normal per frame), `scripts/axis_side.py`,
`scripts/hand_sickle_close.py` (close-ups, `review/hand_v5_*`). Previous masters: `work/rig_v5_precarry.blend`,
`work/rig_v6_precarry.blend`.

## Known limits / for user review

- The sickle stays in her hand in the death (the native throws it).
- Smart Topology fused the vest, blouse and sleeves into the body shell; the HD primary shows more cleavage than the
  native (Codex chose v2).
- The native mask restoration (`mm7_m442`) never produced restored frames beyond standing; the viewer compares against
  the original sprites.
- A small dark texel patch behind the left ear stays out of the hair region.

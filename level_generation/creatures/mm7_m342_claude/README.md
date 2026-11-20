# MM7 Peasant Human1 Female (m342): 9 outfits/tiers — Claude project (robe route)

MM7 batch K, model 2 ([batch file](../mm7_batches/BATCH_K.md)). The floor-length skirt uses the batch-B robe route
(the Monk's chain, [`mm7_m290_claude`](../mm7_m290_claude/README.md): skirt chains with a verlet simulation, legs removed
under the skirt), combined with the finger fit, unarmed hands and clip timing of
[`mm7_m352_claude`](../mm7_m352_claude/README.md). Settings in `creature.json`. **Not installed.**

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [viewer shots](review/shots/) ·
[clay clips](review/g7_clay_front.png) · [G1 candidates](review/g1_front.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m342.glb` | runtime: LODs 9,498 / 4,746 / 1,701 / 560 triangles, shadow LODs, 9 variants `m342_aa` .. `m342_cc`, head material merged (4 atlases 2080×1024), clips Standing, Walking, Hit, Death, Dead, Fidget |
| `export/mm7_m342_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export (tier A base colours) and editable master |
| `textures/` | body 1K set, head 1K set (face and hair), region masks (R dress, G hair), `m342_ramps.json`, material class maps |
| `integration/actors.yml` | staged binding for the nine descriptors |

Install later (user decision): `python3 tools/install_model.py level_generation/creatures/mm7_m342_claude/export/mm7_m342.glb --world mm7`,
then append `integration/actors.yml` to `assets_dev/worlds/mm7/models/actors.yml` (descriptors `Peasant Human1
Female<A|B|C> <A|B|C>` = monsters 349–357, skins `m342_<outfit><tier>`; scale 95.3 = `m342sa0` 180 px × dsft 0.899994
= 162.0 units over the 1.70 m model; stride 1.898 m; look 60°/35°). Speed 140 < run threshold: run → Walking; the
native attack reuses the walk poses, so attacks play Walking; cast → Standing.

## Variants

One mesh, rig and clip set; two recolour regions from the native masks with ramps from each palette's own entries
(`scripts/compose_m342.py`): R dress (bodice, straps, skirt: variants.json channel 0 + shades 43–48; window 35–97 %),
G hair (channel 1 + 192–225, 237, 238; the magenta shadow entries 186–190 are a palette artefact and left out).

| Skin | Descriptor | Palette | Dress / hair |
|---|---|---|---|
| m342_aa | FemaleA A | 343 | green / chestnut |
| m342_ab | FemaleA B | 344 | yellow-olive / ginger |
| m342_ac | FemaleA C | 345 | brown / blonde |
| m342_ba | FemaleB A | 346 | red / black |
| m342_bb | FemaleB B | 347 | blue / blonde |
| m342_bc | FemaleB C | 348 | purple / white |
| m342_ca | FemaleC A | 349 | khaki / red-brown |
| m342_cb | FemaleC B | 350 | white / grey |
| m342_cc | FemaleC C | 351 | black / brown |

## Model

- HD masters (Codex, `references_hd/`): primary v2 and four views; head turnaround `references_head/` (second run;
  the first Codex run died during a memory squeeze before saving anything, log kept).
- Smart Topology 15k (14,643 triangles, 55 parts): skin shell with head, shoulders and blouse sleeves; bodice + green
  skirt; white petticoat; legs with shoes; two hand shells; 31 hair strands; dagger scabbard; belt and buckle; eyes,
  lashes, mouth parts. Legs removed above 12 cm (`strip_legs.py`); reduced after weighting to 9,498.
- Rig: source-frame rig, fingers by connectivity on the hand shells (hand frames ≤ 16° except the thumbs 7°/38°),
  14 × 4 robe chains on B_Pelvis.
- Weights (`weights_robe.py` + project rules): bodice loses arm weight below 1.36 m; **blouse sleeves**: arm-dominated
  skin vertices give their pelvis/lower-spine weight to their arm (Meshy had 0.13–0.19 pelvis on the sleeve rim:
  right arm 4.3x in the hit); skirt and petticoat on the chains; **shoes and dagger ride the hem chains** (one sector
  mix per shoe / per scabbard), so the feet stay under the hem; hair head → neck → chest by height.

## Clips (G1 `review/g1_front.png`)

| Role | Source | Notes |
|---|---|---|
| Standing | Mixamo Standard Idle | skirt simulated |
| Walking | humanoid set Relax Walk Forward | short dress walk (batch J m312), feet flattened, bob evened; stride 1.576 m |
| Hit 1.0 s | Mixamo Standing React Large From Front, planted | arms flung out (native `m342n*`) |
| Death 1.3 s | humanoid set Unarmed Death 1, legs damped to 40 % | falls onto her back (native `m342d*`); skirt laid flat (DROP_FLAT) |
| Fidget 5.1 s | Mixamo Standing Idle 03 Examine, planted | looks at her hand (native `m342f*`) |

Hands keep 60 % of the source finger curl. No attack clip (native attack = walk).

## Gates (`review/gates_v5.json`)

- Arm stretch p99 ≤ 1.90 in every clip (Death R; Hit R 1.66 after the sleeve rule, was 2.52); hands ≤ 2.70x; wrist
  swing ≤ 57°.
- Skirt/robe p99 ≤ 1.53 except Death 1.70 (max 3.09 while she falls).
- Hands up to 6 cm inside the skirt surface while the arms hang (the skirt is wider than the hip at hand height).
- Viewer: 54/54 tier/clip switches, no console errors; shots in `review/shots/`. In game: not checked.

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

## Replay

```sh
TOK=<lease> scripts/rebuild.sh all             # rig + anim + gates (gates_summary)
# textures once: export_uploads.py -> Meshy jobs -> transfer_uv.py -> uv_raster.py (UVMap, HeadUV) -> bake_ao_natm.py
PREVIEW=1 python3 scripts/compose_m342.py && python3 scripts/tier_preview.py
TOK=<lease> scripts/build_runtime.sh
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
```

## Walk fix (user review 2026-10-20)

Batch A/J's walk fix (`mm7_m222_claude`, `mm7_m312_claude`): `walk_bob.py` after `clip_timing.py` evens the walk's
pelvis height (both steps alike, legs re-solved to the same ankle paths; the leg capsules that push the skirt follow).
Head height second difference 4.33 → 0.58 cm (`scripts/walk_probe.py`; batch J's dress m312: 0.44). The feet are not
skinned here, so batch J's ankle fix does not apply (the shoes ride the hem chains). Skirt re-simulated, runtime and
viewer rebuilt; previous masters kept as `work/rig_v5_prewalkfix.blend` / `rig_v6_prewalkfix.blend`.

## Floor and walk fix (user review 2026-10-20, 2: "in the air", "walks very funny")

The shoes rode the hem chains, so the whole figure floated with the hem and the shoes splayed and slid instead of
stepping. Now batch J's dress route (`mm7_m312_claude`): the legs and shoes stay on the leg bones under the skirt
(garment 15, `strip_legs` off); the legs above the shoes take one UV point of the white petticoat (white stockings) (`scripts/legs_uv.py`; the Meshy
textures were kept, UVs carried over with `transfer_uv.py` for UVMap and HeadUV). Walking = the humanoid set's short
Relax Walk Forward (0.8 s), feet flattened (`flatten_feet.py`, one constant correction per foot) and the bob evened
(`walk_bob.py`); Death = the set's Unarmed Death 1 with the legs kept at 40 % of their motion (`leg_damp.py`) so they
stay under the skirt. Soles: Standing −0.2…+0.1 cm, Walking −2.3…+1.9 cm; walk head height second difference 0.49 cm; foot
rotation step ≤ 16.8° (the set walk's own, as m312). Stride 1.576 m (binding updated); LOD0 9,920 / 4,957 / 1,778 / 585 triangles.
Previous masters: `work/*_prelegs.blend`, `work/creature_prelegs.json`.

## Known limits / for user review

- The hands sink a little into the wide skirt while the arms hang.
- The gold hoop earrings were not modelled by Smart Topology (painted only where the head texture shows them).
- No attack clip (Walking in place, as the native sprite).

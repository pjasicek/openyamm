# MM7 Roc (m390) — 2026-10-20

> **Reduced export (2026-10-21):** [`../mm7_m390_reduce_claude/`](../mm7_m390_reduce_claude/README.md) reduces this
> model 6,867 -> 6,237 triangles (LOD3 822 -> 742) with the same textures, MM7 ramps and clips: install
> `mm7_m390_reduce_claude/export/mm7_m390.glb` instead of this project's export (same binding). This export stays the
> rollback.

Batch H, model 1 ([BATCH_H.md](../mm7_batches/BATCH_H.md)). Identity **mm7:m390**, descriptors **391–393**
(Roc, Greater Roc, Thunderbird), palettes 553/554/555. Not installed (batch rule): everything stays in this project.

## Decision: same body as the MM8 Thunderbird, MM7 colours

The MM7 Roc sprites are the same render as the MM8 Thunderbird family (`m552`, Mist Hawk / Storm Eagle /
Thunderbird), drawn with the same three palettes (`scripts/identity_check.py` → `review/identity_check.json`):

- all 115 shared frame names match the MM8 bitmaps with alpha IoU 0.96–0.99 (MM7 has 10 extra unreferenced
  frames, `ng*` and `sa*` duplicates);
- the palettes are the same files (`assets_dev/worlds/mm8/textures/pal553–555.act`), and tier A's frame scale is
  the same 2.199997 (MM7 B/C use 2.6 and 3.0, MM8 B/C 2.2).

The only difference is the colour mapping: MM7 draws the flight feathers with palette indices 187–249, which the
three palettes colour differently (Roc grey-olive, Greater Roc red-brown, Thunderbird near-black), while MM8 draws
them with the palette-invariant greens 128–186. A new Meshy model would rebuild the same shape, so this project
follows the batch README's MM8-reuse rule ("same body, MM7 colours"): **0 Meshy credits, no new geometry, rig or
clips**. The batch file listed the Roc as a new build; this is noted under the batch's Open issues.

Source: the installed, reduced Thunderbird `assets_source/worlds/mm8/models/mm8_m552.glb`
(sha256 `88dab93c…`, identical to `mm8_m552_reduce_claude/export/mm8_m552.glb`; production and gates in
[mm8_m552_claude](../mm8_m552_claude/README.md), reduction in [mm8_m552_reduce_claude](../mm8_m552_reduce_claude/README.md)).

## Delivery

| Item | Value |
|---|---|
| Export | [`export/mm7_m390.glb`](export/mm7_m390.glb), 8.3 MB, sha256 `c3edef37a8aa2a8b106e02a6aed4fc424eb1b59ad99e2d72ea5b223fb27945e5` |
| Contents | MM8 Thunderbird geometry, skin, LOD0–3 (6,867 / 3,432 / 1,704 / 822 tris), shadow LODs, six clips, all images byte-identical |
| Changed | glTF JSON only: variants `m390_a/b/c`, materials `Roc_A/B/C`, region ramps from MM7 frames |
| Ramps | [`textures/m390_ramps.json`](textures/m390_ramps.json) from `scripts/tier_ramps.py`; mask = `m552_region_mask.png` (body, flight feathers) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m390_claude/review/viewer/) (ramps baked per tier for three.js) |
| Meshy | 0 / 30 credits |

`scripts/tier_ramps.py` uses the m552 compose method on the MM7 standing frames `m390sa0–4`: each region's texels
ranked by luminance take that region's native colours of the same rank (albedo gains 1.45 body, 1.10 feathers).
Fit error, mean / p95 8-bit levels: body 4.1–4.5 / 14–15 (same as m552), feathers 1.1–2.9 / 2–8.

## Checks

- `check_winding.py`: 0 inverted closed parts (geometry unchanged from the installed MM8 model).
- `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m390_claude check`: 3 tiers × 6
  clips load, no console errors.
- Tier shots `review/shots/q_{a,b,c}.png`, `fly_{a,b,c}.png`: grey-olive, red-brown and black flight feathers on the
  shared brown body, as the MM7 palettes. As in the MM8 production, the wing coverts belong to the brown body
  region, so the feather colour shows on the primaries and secondaries.
- Clip gates (floor, loop, corpse, deformation) are the m552 project's and its reduction's; nothing here changes them.
- No in-game check (optional in the batch rules).

Size note: the m552 flight upstroke reaches 178 units at scale 569 (A). MM7 Roc collision heights are 165 / 200 / 240
(MM8 Thunderbird: 200 for all tiers), so with the frame-scale ratio the wing tips rise about 13 / 11 / 3 units
above the MM7 collision box; low ceilings can clip them, as with the other flyers.

## Install (installed 2026-10-21, reduced export)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m390_claude/export/mm7_m390.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (non-caster: Roc tiers have no spell and no ranged attack, so
`cast: Attack`; the GLB's unused `Cast` clip stays from the source):

```yaml
# Roc m390: MM8 Thunderbird body, MM7 palettes 553/554/555 (feathers on indices 187-249), descriptors 391-393.
- descriptor: Roc A
  model: worlds/mm7/models/mm7_m390.glb
  scale: 569.0313796892026
  yaw_offset: -1.570796327
  skin: m390_a
  animation:
    cast: Attack
    run: Fly
    stride_length: 1.0
    run_stride_length: 1.0
    upper_body_root: Chest
    sockets:
      head: HeadSocket
    events:
      attack_melee:
        impact: 0.875
      attack_ranged:
        impact: 0.875
  clips:
    standing: Fly
    walking: Fly
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fly
# Roc B and Roc C: the same entry with skin m390_b / m390_c and `scale_reference: Roc A`
# (the engine multiplies by the frame-scale ratio 2.6 / 2.2 and 3.0 / 2.2).
```

Alternative with no second copy of the textures (about 8 MB less when both worlds are mounted): add the three MM7
variants to the shared MM8 GLB instead and bind Roc A/B/C to `worlds/mm8/models/mm8_m552.glb`. That changes an
installed MM8 asset, so it is left to the user.

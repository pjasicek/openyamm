# MM7 Peasant Human2 Female (m372): 9 descriptors, 6 skins — Claude batch-B robe route

MM7 batch K, model 4 ([batch file](../mm7_batches/BATCH_K.md)), built in parallel with the other batch-K models (user
request). Humanoid playbook default route on the batch-B robe chain (Monk [`mm7_m290_claude`](../mm7_m290_claude/README.md))
as adapted for the female peasant [`mm7_m342_claude`](../mm7_m342_claude/) (finger fit on the hand shells, unarmed clip
timing, shoes on the hem chains), plus bell-sleeve chains and an axial joint fix. **Not installed.**

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [viewer shots](review/shots/) ·
[clay clips](review/g7_clay_front.png) · [G1 candidates](review/g1_front.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m372.glb` | runtime: LODs 10,563 / 5,281 / 1,895 / 626 triangles, shadow LODs, 6 skins `m372_aa/ab/ac/ba/bb/bc`, head material merged (4 atlases 2080×1024), clips Standing, Walking, Hit, Death, Dead, Fidget |
| `export/mm7_m372_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export (tier A colours) and editable master |
| `textures/` | body 1K set, head 1K set, region masks (R gown, G veil + sleeve lining, B hair), `m372_ramps.json`, material class maps |
| `integration/actors.yml` | staged binding for the nine descriptors |

Install later (user decision), from the repository root:

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m372_claude/export/mm7_m372.glb --world mm7
```

then append `integration/actors.yml` to `assets_dev/worlds/mm7/models/actors.yml` (descriptors `Peasant Human2
Female<A|B|C> <A|B|C>` = monsters 376–384; scale 100.2 = `m372sa0` 213 px × dsft 0.799988 = 170.4 units over the
1.70 m model; stride 1.898 m; look 60°/35°). Speed 140 stays below the run threshold: run → Walking. The native attack
reuses the walk frames: `attack_melee`/`attack_ranged` → Walking; cast → Standing.

## Skins (the native has only six palettes)

| Skin | Descriptors | Palette | Gown / veil + lining / hair |
|---|---|---|---|
| m372_aa | FemaleA A | 373 | green / sage / auburn |
| m372_ab | FemaleA B | 374 | blue / blue-grey / blonde |
| m372_ac | FemaleA C | 375 | red / rose / dark auburn |
| m372_ba | FemaleB A, FemaleC A | 376 | green / sage / blonde |
| m372_bb | FemaleB B, FemaleC B | 377 | blue / blue-grey / auburn |
| m372_bc | FemaleB C, FemaleC C | 378 | red / rose / blonde |

Outfit C's sprites (`m379s`–`m381s`) use palettes 376–378 like outfit B (manifest `descriptor_animations`), so B and C
share skins. Regions from the native masks (`mm7_m372/manifest.json`: emerald gown, sage veil and lining, brown
hair) plus the shades that change with them (`scripts/compose_m372.py`).

## Model

- HD masters (Codex): primary v2 (the belt clasp landed on her right hip, as in the native front frame; the brief had
  it on the left) and four views; head turnaround with the veil in `references_head/`.
- Smart Topology 15k (14,662 triangles, 46 parts): gown with bell sleeves (one shell), head, two hand/forearm
  shells, veil, two lower legs with shoes, belt, clasp, hanging cord, fringe, eyes, beads. The legs under the gown
  are removed above the shoes; seven small strips that read as a dark gash from the chin to the collarbone are dropped
  at export (`drop_pieces`). Reduced after weighting to 10,773 (10,563 exported).
- Rig: source-frame rig; Meshy's auto-rig placed Spine2 8 cm in front of the chest and the neck 4 cm to the side
  (fooled by the veil), which tilted the head 40° back in every clip: `axial_fix.py` re-centres the pelvis, spine
  and neck on the body's cross-sections and puts the head above the neck along the source direction. Fingers by
  connectivity on the hand shells (frames within 29°).
- Weights: batch-B robe rules (gown torso de-armed below `split_z` 1.18, sleeves arm-only, skirt on 14 × 4 robe
  chains, armpit band smoothed 8 passes inside z 1.12–1.30); veil head → neck → chest by height; shoes and cord on
  the hem chains; beads and belt by garment.
- Bell sleeves: 3 × 3 chains per sleeve on the forearm (`sleeve_rig.py`), simulated only in the Death
  (`robe_sim.py` with ROOT=forearm, lying test from B_Spine1, DROP_FLAT) and keyed at rest in the other clips
  (`key_rest.py`): rigid on the forearm they stood up like horns on the corpse; simulated in every clip the cuff
  junction stretched 3–4× (rejected).
- Joints: 132 (126 deforming + palm sockets): the renderer packs 128 joints per palette row and uses two rows.

## Clips (G1 as m342; the same unarmed peasant set)

| Role | Source | Notes |
|---|---|---|
| Standing | Mixamo Standard Idle | skirt chains simulated (loop) |
| Walking | humanoid set Relax Walk Forward | short dress walk (batch J m312), feet flattened, bob evened; stride 1.594 m |
| Hit 1.0 s | Mixamo Standing React Large From Front, planted | arms flung out (native `m372n*`) |
| Death 1.3 s | humanoid set Unarmed Death 1, legs damped to 40 % | falls onto her back (native `m372d*`); skirt and bell sleeves simulated and laid flat |
| Fidget 5.1 s | Mixamo Standing Idle 03 Examine, planted | looks at her hand (native `m372f*` looks down at the hands) |

Hands keep 60 % of the source finger curl.

## Gates (2026-10-20, `review/gates_v5_summary.txt`)

- Arm stretch p99 ≤ 1.96 in every clip except the Death (left 3.30, right 4.60 where the simulated sleeve meets the
  cuff while she falls); hands ≤ 1.52×; wrist ≤ 58°; robe p99 ≤ 1.38 except Death 4.25 (mid-fall).
- hand-in-body up to 8 cm counts the hand inside its own bell sleeve (the bell is not weighted to the arm).
- Viewer: `tools/run_creature_review.py check` 36/36 skin/clip switches, no console errors; shots in `review/shots/`.
- In game: not checked (optional in batch K; nothing installed).

## Textures

Body 1K + head 1K. Skin repainted to one albedo × Meshy's fine shading (face detail clamped 0.75–1.2: Meshy's dark
cheek blotch and a light streak under the eye); hair (fringe and crown inside the veil, which Meshy painted as a
translucent green cap) repainted with the native tier-A auburn; the veil's knit speckle softened before its ramp.

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

## Replay

```sh
TOK=<lease> scripts/rebuild.sh all          # rig (axial_fix, fingers, robe + sleeve chains) and anim (clips, sims, gates)
# textures once: export_uploads.py -> Meshy jobs -> transfer_uv.py -> uv_raster.py (UVMap, HeadUV) -> bake_ao_natm.py
python3 scripts/compose_m372.py && python3 scripts/tier_preview.py
TOK=<lease> scripts/build_runtime.sh        # no install step (clamp_uv.py: one decimated LOD2 vertex at u 1.0002)
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
```

## Walk fix (user review 2026-10-20)

Batch A/J's walk fix (`mm7_m222_claude`, `mm7_m312_claude`): `walk_bob.py` after `clip_timing.py` evens the walk's
pelvis height (both steps alike, legs re-solved to the same ankle paths; the leg capsules that push the skirt follow).
Head height second difference 4.22 → 0.57 cm (`scripts/walk_probe.py`; batch J's dress m312: 0.44). The feet are not
skinned here, so batch J's ankle fix does not apply (the shoes ride the hem chains). Skirt re-simulated, runtime and
viewer rebuilt; previous masters kept as `work/rig_v5_prewalkfix.blend` / `rig_v6_prewalkfix.blend`.

## Floor and walk fix (user review 2026-10-20, 2: "in the air", "walks very funny")

The shoes rode the hem chains, so the whole figure floated with the hem and the shoes splayed and slid instead of
stepping. Now batch J's dress route (`mm7_m312_claude`): the legs and shoes stay on the leg bones under the skirt
(garment 15, `strip_legs` off); the legs above the shoes take one UV point of the robe hem (legs in dress cloth, as m312) (`scripts/legs_uv.py`; the Meshy
textures were kept, UVs carried over with `transfer_uv.py` for UVMap and HeadUV). Walking = the humanoid set's short
Relax Walk Forward (0.8 s), feet flattened (`flatten_feet.py`, one constant correction per foot) and the bob evened
(`walk_bob.py`); Death = the set's Unarmed Death 1 with the legs kept at 40 % of their motion (`leg_damp.py`) so they
stay under the skirt. Soles: Standing −0.1…0.0 cm, Walking −1.9…+3.3 cm; walk head height second difference 0.50 cm; foot
rotation step ≤ 16.8° (the set walk's own, as m312). Stride 1.594 m (binding updated); LOD0 10,944 / 5,471 / 1,964 / 650 triangles.
Previous masters: `work/*_prelegs.blend`, `work/creature_prelegs.json`.

## Known limits / for user review

- Death: arm and robe stretch above the gate while falling (sleeve chains and skirt chains settling).
- The veil hangs rigidly; it does not drape further when she lies down.
- The native veil hangs lower down the back than the HD master's.

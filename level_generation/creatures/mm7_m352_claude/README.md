# MM7 Peasant Human1 Male (m352): 9 outfits/tiers — Claude rig-first project

MM7 batch K, model 1 ([batch file](../mm7_batches/BATCH_K.md)). Humanoid playbook default route (source-frame rig with
gates) on the scripts of [`mm7_m226_claude`](../mm7_m226_claude/README.md), adapted to an unarmed peasant: no prop,
no attack, no run, both hands loosely curled. **Not installed.**

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [viewer shots](review/shots/) ·
[clay clips](review/g7_clay_front.png) · [G1 candidates](review/g1_front.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m352.glb` | runtime: LODs 9,045 / 4,521 / 1,570 / 484 triangles, shadow LODs, 9 variants `m352_aa` .. `m352_cc`, head material merged (4 atlases 2080×1024), clips Standing, Walking, Hit, Death, Dead, Fidget |
| `export/mm7_m352_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export (tier A base colours) and editable master |
| `textures/` | body 1K set, head 1K set, region masks (R tunic, G hair, B beard), `m352_ramps.json`, material class maps |
| `integration/actors.yml` | staged binding for the nine descriptors |

Install later (user decision), from the repository root:

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m352_claude/export/mm7_m352.glb --world mm7
```

then append `integration/actors.yml` to `assets_dev/worlds/mm7/models/actors.yml` (descriptors `Peasant Human1
Male<A|B|C> <A|B|C>` = monsters 358–366, skins `m352_<outfit><tier>`; scale 102.6 = `m352sa0` 218 px × dsft 0.799988 =
174.4 units over the 1.70 m model; stride 1.787 m; look 60°/35°). Speed 140 is below the run threshold (2.4 × 102.6):
run → Walking. The native attack reuses the eight walk poses, so `attack_melee`/`attack_ranged` play Walking (no
impact event); cast → Standing.

## Variants

One mesh, rig and clip set for all nine looks (the native frames are identical across descriptors 358–366; only the
palette changes). Three recolour regions from the native masks, ramps from each palette's own region entries
(`scripts/compose_m352.py`, native stand/walk pixels): R tunic (variants.json channel 0 indices + dark shades
197–210; ramp window 35–97 % of the native luminance distribution so the sprite's baked shadows do not mottle the
cloth), G hair (72–74, 91, 95, 97, 99), B beard (231–248).

| Skin | Descriptor | Palette | Tunic / hair / beard |
|---|---|---|---|
| m352_aa | MaleA A | 353 | green / black / black |
| m352_ab | MaleA B | 354 | blue / black / brown |
| m352_ac | MaleA C | 355 | red / red / dark red |
| m352_ba | MaleB A | 356 | teal / red / brown |
| m352_bb | MaleB B | 357 | black / blonde / blonde |
| m352_bc | MaleB C | 358 | brown / sandy / brown |
| m352_ca | MaleC A | 359 | cream / dark brown / dark brown |
| m352_cb | MaleC B | 360 | grey / brown / brown |
| m352_cc | MaleC C | 361 | red / white / grey |

## Model

- HD masters (Codex, `references_hd/`): primary v2 (corrective run, open hands) and four views; head turnaround in
  `references_head/`. Gated against `source/native_standing_views.png`.
- Smart Topology 15k (14,941 triangles, 69 parts): tunic with belt, trouser legs, head + neck, two hand/forearm shells,
  long hair, shoes, buckle, hanging strap end, eyes, 58 brass studs. Nothing removed. Reduced after weighting to 9,045
  (skin 7,000 with head and hands protected, hair 650, strap 110, studs 1,000).
- Rig: source-frame rig (52 bones + 4 twist), Meshy auto-rig for the axial joints and elbows (t 0.50 / 0.47), ring
  centres for wrists/ankles, fingers by connectivity on the hand shells. Frame error 0; hand frames within 20° except
  the ring/pinky directions (33–38°, the chains sit inside the fingers in `review/handx_*`).
- Weights (`weights_fix.py`): skin = Meshy + shoulder fade + jaw free of the shoulders; eyes rigid head; hair head →
  neck → chest by height; strap end copies the skin without arm weight; studs/buckle rigid on the dominant bone.
  Finger webs: non-adjacent finger weight removed also on unlabelled palm vertices, 6 smoothing passes.

## Clips (G1: candidates rendered on this rig, `review/g1_front.png`)

| Role | Source | Notes |
|---|---|---|
| Standing | Mixamo Standard Idle | feet levelled |
| Walking | Mixamo Standard Walk (upper arms out 6°) | constant foot tilt and roll removed, floor lift; stride 1.787 m |
| Hit 1.0 s | Mixamo Standing React Large From Front, planted | arms flung out, head back (native `m352na–nf`); eased 0.2/0.2 s |
| Death 2.2 s | Mixamo Falling Back Death | falls backward arms spread (native `m352d*`); travel halved, floor pass |
| Fidget 5.1 s | Mixamo Standing Idle 03 Examine, planted | looks at his raised hand (native `m352f*` look at the hands) |

Both hands keep 60 % of the source finger curl (`apply_grip.py UNARMED=1`), a loose fist like the native.
Rejected: the set's Unarmed get-hit (a boxing guard), Reaction (hands to the face), Standing React Death Backward
(longer, stumbles), Looking Down / Thinking fidgets.

## Gates (2026-10-20, `work/gates_final.txt`)

- G4 arm stretch p99 ≤ 2.06 (Hit right, max 3.05 at the fling), Death left 1.97; Standing/Walking ≤ 1.38.
- G5 hands: right ≤ 3.70x (Hit), left ≤ 2.24x (5.1x before the web fix, 6 smoothing passes and curl 0.6).
- G6: forearms ≤ 1.8 cm under the tunic surface (the sleeves are open shells round them), left forearm 3.2 cm against
  the tunic skirt at the walk's back swing; the right hand 4.1 cm into the thigh during the fall (source motion).
- Soles: Standing −0.9 cm, Walking −1.5…+1.5 cm, Hit/Fidget 0…0.6 cm.
- Jerk: follows the sources (the hit's 0.1 s fling and the fall's head snap are in the Mixamo clips).
- Viewer: `tools/run_creature_review.py check` 54/54 tier/clip switches, no console errors; shots in `review/shots/`.
- In game: not checked (optional in batch K; nothing installed).

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

## Replay

```sh
TOKEN=<lease> STAGE=rig scripts/rebuild.sh; TOKEN=<lease> STAGE=anim scripts/rebuild.sh   # SMOOTH_PASSES=6 CURL=0.6
# textures once: export_uploads.py -> Meshy jobs -> transfer_uv.py -> uv_raster.py (UVMap, HeadUV) -> bake_ao_natm.py
python3 scripts/compose_m352.py && python3 scripts/tier_preview.py
TOKEN=<lease> scripts/build_runtime.sh        # no install step
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
TOKEN=<lease> scripts/gates.sh                # G4, G5, G6, soles, jerk
```

## Walk and ankle fix (user review 2026-10-20)

Batch A/J's walk fixes (`mm7_m222_claude`, `mm7_m302_claude`), applied in the chain and replayed (STAGE=anim, runtime,
viewer); previous masters kept as `work/rig_v5_prewalkfix.blend` / `rig_v6_prewalkfix.blend`. Measured by
`scripts/walk_probe.py` (head height second difference, foot world-rotation step change per frame):
- **Ankle twist:** `foot_level.py` updated to batch A's rule: the walk takes one constant roll per foot in the foot's
  own frame and one constant pelvis shift (the per-frame roll switched on and off as each foot landed and lifted); the
  other clips' roll is weighted by flatness, capped at 20° and smoothed.
- **Head zigzag:** `walk_bob.py` after `clip_timing.py` evens the walk's pelvis height (both steps alike, legs re-solved
  to the same ankle paths).
- **Walk clip:** Mixamo Standard Walk replaces Mixamo Walk (as batch J's humans and the MM6 male peasant): Walk's own
  feet change up to 17° per frame, Standard Walk's 10–11°. Its forearms swing into the tunic side, so the walk's upper
  arms are turned out 6° (`abduct_arms.py`, from m442).
- Result: head second difference 4.94 → 0.84 cm; foot rotation step change 28.6° → 11.3/10.4° (batch J: 10.3–11.8);
  soles within −1.4…+1.0 cm; stride 1.787 m (binding updated); viewer check 54/54.

## Known limits / for user review

- No attack clip: the binding plays Walking in place for attacks, as the native sprite does.
- The death ends with one knee raised (Mixamo); the native corpse lies flat with the legs straight.
- The hem tabs are painted (Smart Topology modelled a slightly ragged hem, not separate tabs).
- Eyebrows stay dark in the blonde/white tiers (outside the beard mask).

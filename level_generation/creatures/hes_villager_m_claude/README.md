# Hesper Landfall villager, male: three outfits — Claude humanoid project

> **Reduced (2026-10-22):** [`../hes_villager_m_reduce_claude/`](../hes_villager_m_reduce_claude/README.md) has the triangle-reduced export (LOD0 9,452 -> 7,064, far LODs rebuilt, no retexture); exported, not installed. This project's exports are unchanged.

A Landfall townsman ([concept](../../../design/kreegan_world/concepts/people/villager_male.png), approved
2026-10-22). Humanoid playbook default route; template `mm7_m352_claude/` (unarmed peasant: no prop, no attack).
Monsters 10073–10075. **Exported 2026-10-22, not installed.**

## Variants (one mesh, region mask + ramps)

| Skin | Coat (R) | Front panel, yokes, cuffs (G) | Collar (B) | Hair (A) |
|---|---|---|---|---|
| vm_a | slate blue | off-white | town red | dark brown |
| vm_b | dark slate grey-green | cream | ochre gold | black |
| vm_c | warm grey | pale blue-grey | teal | auburn |

Gold piping, clasps, the belt plate, pouch, boots, skin and trousers stay out of every region.

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [outfits](review/tiers_contact.png) ·
[viewer shots](review/shots/) · [clay clips](review/g7_clay_front.png) · [death candidates](review/g1_death.png)

## Deliverables (2026-10-22, not installed)

| File | What |
|---|---|
| `export/hes_hvm.glb` | runtime: LODs 9,452 / 4,721 / 1,687 / 553 triangles, shadow LODs, 3 variants `vm_a` .. `vm_c` (materials HVM_A/B/C), head material merged (4 atlases 2080×1024), clips Standing, Walking, Hit, Death, Dead, Fidget |
| `export/hes_hvm_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export (outfit A base colours) and editable master |
| `textures/` | body 1K set, head 1K set (face and hair), region masks (R coat, G panel, B collar, A hair), `hvm_ramps.json`, material class maps |
| `integration/actors.yml` | staged binding for the three outfits (scale 102.9 = 175 units / 1.7008 m; stride 1.743 m; look 60°/35°) |

Install later (Hesper goes through `level_generation/projects/hesper_stage`): the runtime GLB as
`worlds/hesper/models/hes_hvm.glb`, plus the staged `actors.yml` entries once the Hesper monster table has the
descriptors for monsters 10073–10075.

## Model

- HD masters (Codex, `references_hd/`) from the approved concept sheet; gated: pouch, pin and lit wrist band on his
  LEFT in every view. Head turnaround in `references_head/`.
- Smart Topology 15k (13,589 triangles, 123 parts): coat with belt P00, head and neck P01, trousers P02, left/right
  hands P03/P04 (separate shells open inside the cuffs), pouch P05, shoes P06/P07, eyes P09/P10, ~100 short hair cards,
  the pin and the coat's gold clasps. Nothing removed. Reduced after weighting to 9,460 (skin 7,000 with head and hands
  protected, hair 1,400, pouch 250, fittings 561).
- Rig: source-frame rig (52 bones + 4 twist), Meshy auto-rig for the axial joints and elbows (t 0.475 / 0.462),
  wrists at the centroid of each hand shell's open edge (`hand_openings.py`: the ring fit put the right wrist 9 cm
  down in the palm), ankles from rings, fingers by connectivity. Frame error 0; hand frames 14–45° (index/middle
  35–43°, more than m352's ≤ 20°; the fitted chains sit inside the fingers, `review/handx_*`).
- Weights (`weights_fix.py`, labels in `garments.py`): skin = Meshy + shoulder fade + jaw free of the shoulders; eyes
  rigid head; hair head → neck by height; pouch copies the skin under it without arm weight; pin and clasps rigid on
  the dominant bone. Finger webs 6 smoothing passes.

## Clips

G1: the m352 set (same body type: unarmed townsman in a knee-length coat), except the death.

| Role | Source | Notes |
|---|---|---|
| Standing 3.0 s | Mixamo Standard Idle | feet levelled; loose hands, 60 % of the source finger curl |
| Walking 1.167 s | Mixamo Standard Walk | upper arms out 6°, constant foot tilt/roll, even pelvis bob; stride 1.743 m |
| Hit 1.0 s | Mixamo Standing React Large From Front, planted | eased 0.2/0.2 s |
| Death 4.6 s / Dead | Mixamo Dying Backwards (travel halved) | sinks to a sit and lies back (`review/g1_death.png` D2); Falling Back Death kicked the legs up and splayed the coat flaps on the corpse |
| Fidget 5.1 s | Mixamo Standing Idle 03 Examine, planted | looks at his raised hand |

## Variants

Authored ramps (`scripts/compose_hvm.py`; no native palette): A is `fit_ramps` against the texture itself (mean error
coat 6.9, panel 3.7, collar 7.4, hair 1.3 8-bit levels); B and C keep A's shading, (stop luminance / region median)^0.7,
on the colours of the table above (B collar 168/124/48, C coat 98/90/84, C collar 40/112/116, C hair 104/46/26 after the
first review render: the full ratio blew the bright stops out). One set of ramps for the body and head materials
(fitted over both, as `merge_head_material.py` requires). Kept out of every mask: gold piping and clasps, the ceramic
belt plate and wrist band, the lit strip, belt, pouch, boots, skin and trousers. Material classes: ceramic and the lit
strip are class 11 ("other").

## Gates (2026-10-22, `work/gates_final.txt`)

- G4 arm stretch p99 ≤ 2.05 (Death left, max 2.89); Standing/Walking ≤ 1.37.
- G5 hands: left ≤ 3.79x (Death), right ≤ 2.52x.
- G6: hands 1.9 cm into the coat skirt's side at rest (the hands hang against it); the right hand 6.0 cm into his
  coat while lying (Death, source motion).
- Soles: Standing −1.4…−1.3 cm, Walking −2.0…+2.0, Hit/Fidget 0…0.4; walk probe head second difference 0.82 cm,
  foot rotation step change 11.8 / 10.1° (m352: 0.84, 11.3 / 10.4).
- `check_winding.py`: 0 inverted closed parts (runtime and LOD0). Viewer: `tools/run_creature_review.py check` 18/18
  outfit/clip switches, no console errors; shots in `review/shots/`. Not checked in game (Hesper not integrated yet).

## Meshy

**30 of 60 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

## Replay

```sh
TOKEN=<lease> STAGE=rig scripts/rebuild.sh; TOKEN=<lease> DEATH_UNTIL=20 STAGE=anim scripts/rebuild.sh
# one-off joint inputs: work/source_rest.json + proportions.json (source) from m352, fit_joints.py, meshy_joints.py,
# hand_openings.py; textures once: export_uploads.py -> Meshy jobs -> transfer_uv.py (rig_v5h -> rig_v6) -> uv_raster.py
# (UVMap, HeadUV) -> bake_ao_natm.py
python3 scripts/compose_hvm.py && python3 scripts/tier_preview.py
TOKEN=<lease> scripts/build_runtime.sh        # no install step
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
TOKEN=<lease> scripts/gates.sh                # G4, G5, G6, soles, jerk
```

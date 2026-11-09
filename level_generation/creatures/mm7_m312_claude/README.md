# MM7 Peasant Dwarf Female (`m312`) — Claude humanoid route (batch J, 2026-10-20)

MM7 batch J model 2 ([BATCH_J.md](../mm7_batches/BATCH_J.md)). Scripts from the Mage `../mm7_m274_claude/` (the batch-B
robed-caster chain, configured by `creature.json`): source-frame rig, rigid open hands, a floor-length dress on 12 × 4
simulated robe chains with leg capsules, shoes kept on the leg bones. **Not installed**: the install command and the
`actors.yml` binding are below. Meshy: **30 of 100 credits** (Smart Topology 5, auto-rig 5 for joint estimates, body
retexture 10, head retexture 10). User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the repository root) · [viewer shots](review/shots_sheet.png) ·
[corpse](review/dead_sheet.png) · [clay clips front](review/cl_front.png) / [left](review/cl_left.png) ·
[textured](review/tex_sheet.png) · [head](review/tex_heads.png) · [gates](review/gates_final.txt)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m312.glb` | runtime: one skinned mesh `M312`, 9 colour variants (`m312_a1`…`m312_c3`) on one merged body+head material (2080×1024 atlases), LODs 10,591 / 5,294 / 1,898 / 623 tris + shadow LODs, 6 clips |
| `export/mm7_m312_lod0.glb` | full-detail portable export |
| `work/rig_v6.blend` | editable textured master (rig, robe chains, clips, Meshy UVs, head split) |
| `textures/` | body and head 1K sets, body + head region masks, `m312_ramps.json`, material class maps |

## Native identity and the nine looks

Native MM7 bitmaps `m312*` (124 frames, `../mm7_m312/`). Short matronly dwarf woman: pale blonde hair in a bun with
ringlets, earrings, a purple laced bodice with a white chemise edge, puffed white sleeves with purple stripes, a
stained white apron with a pocket and a big bow at the back, scissors at the waist, an ankle-length purple dress, brown
shoes. No weapon; attack and shoot alias the walk.

One mesh covers the nine descriptors with two recolour regions: **R cloth** (palette entries 138–239: bodice, sleeve
stripes, skirt and the dress-coloured apron stains, which follow the dress in the native looks) and **G hair**
(entries 28–59: bun, ringlets, painted hairline). Ramps rank-matched to the native pixels (palette 313 order) × 1.35.

| Descriptor | Skin | Palette | Dress / hair |
|---|---|---:|---|
| 313 Peasant Dwarf FemaleA A | `m312_a1` | 313 | purple / blonde |
| 314 FemaleA B | `m312_a2` | 314 | cream / lilac grey |
| 315 FemaleA C | `m312_a3` | 315 | charcoal / ginger |
| 316 FemaleB A | `m312_b1` | 316 | lavender / black |
| 317 FemaleB B | `m312_b2` | 317 | green / white |
| 318 FemaleB C | `m312_b3` | 318 | mustard / grey |
| 319 FemaleC A | `m312_c1` | 319 | red / auburn |
| 320 FemaleC B | `m312_c2` | 320 | blue / ginger |
| 321 FemaleC C | `m312_c3` | 321 | green / black |

## Model, rig and weights

- Smart Topology of `references_hd/00_three_quarter.png` (normalised to 1.7 m, the chain's units): 15.8k tris, 30 shells,
  labelled in `creature.json` (bodice+sleeves, head, skirt, legs+shoes, bun, hands, ringlets, earrings, eyes, lips,
  lacing ×6, apron, pocket, scissors ×4, bow, bow tails, cuff ruffles).
- Rig: Meshy joints, arm rings and `joints_fix.py`; rigid open hands (fingers unweighted, as the chain's casters).
- Weights (`weights_robe.py`): bodice/sleeves on Meshy with the torso below the armpit (z 1.15) free of arm weight;
  bun, ringlets, earrings, eyes and lips rigid on the head; lacing on Meshy's trunk weights without arms; bow rigid on
  the pelvis; cuff ruffles rigid on the forearms; skirt on 12 × 4 robe chains from the waist (0.92) to the hem (0.10,
  new `hem_z` key); apron, pocket, scissors and bow tails each on one robe-chain mix; legs and shoes keep leg weights.
- Reduced after weighting: 15.8k → 10.6k.

## Clips

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 2.00 | humanoid set Relax Idle, arms abducted 6° |
| Walking | 0.80 | humanoid set Relax Walk Forward (Relax Walk Female's hip sway swung the dress sideways); feet flattened |
| Hit | 0.50 | humanoid set Unarmed Get Hit F2, planted: recoils back with the arms out (native `m312na..ne`); GetHitF1 doubled over forward |
| Death | 1.30 | humanoid set Unarmed Death 1 (crouch, falls onto the back as native `m312da..xa`), legs kept at 40 % of the source motion (`leg_damp.py`) so they stay under the dress; robe dropped flat |
| Dead | 1.00 | last Death pose held |
| Fidget | 0.67 | humanoid set Relax Yes (a nod; the native fidget barely moves) |

Tried and rejected for the death: Mixamo Standing React Death Backward (wide stride, legs kicked up: legs out of the
dress), the same with damped legs (it sits first: the legs went 66 cm under the floor), Relax lie-down (lands face
down). The robe is simulated per clip (`robe_sim.py`, leg capsules ×1.3, DROP_FLAT for the corpse).

## Textures (`scripts/compose_m312.py`)

Body 1K + head 1K (head set: the whole head shell with neck and chest, bun, ringlets, earrings, eyes, lips). Hands
repainted to one skin albedo × Meshy's shading. Meshy painted the eye shells skin-coloured: procedural sclera, blue
iris and pupil. The head retexture mixed bodice/chemise paint into the chest skin: repainted to the neck's skin colour
(feathered). The legs above the shoes are painted as dress cloth (in the cloth region): they are hidden in every
standing clip and read as the dress over the legs in the corpse.

## Gates (`review/gates_final.txt`)

- Robe p99 ≤ 1.26 standing/walking/hit/fidget, 1.88 in the death; arm p99 ≤ 1.96; wrist swing ≤ 52°.
- Soles: grounded feet −3.1…0 cm (Standing −1.9…−0.5).
- Jerk: idle, walk and nod smooth; the hit's recoil is fast (upper arm 56° per 1/48 s at 0.1 s, the source's own snap
  compressed by the 0.12 s blend-in); the fall's head step 42°.
- Viewer: 54/54 look/clip switches, no console errors; textured viewer shots and the corpse inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m312_claude/export/mm7_m312.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`. Scale = native standing silhouette 158 px × sprite scale
0.799988 / model height 1.7266 m = **73.21** (every descriptor). Repeat for the other eight descriptors with their
skins from the table above and `scale_reference: Peasant Dwarf FemaleA A`:

```yaml
# MM7 Peasant Dwarf Female m312 (313-321): one body, nine palette looks; simulated dress; no weapon, no attack.
- descriptor: Peasant Dwarf FemaleA A
  model: worlds/mm7/models/mm7_m312.glb
  scale: 73.21
  yaw_offset: -1.570796327
  skin: m312_a1
  animation:
    cast: Standing
    run: Walking
    stride_length: 1.276
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 25
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Standing
    attack_ranged: Standing
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
```

The walk's natural 1.60 m/s × 73.21 = 117 units/s plays at 1.2x for the 140 units/s peasants (run threshold 176).
No in-game check was run.

## Known limits / for user review

- The death is a planted crouch-and-fall with damped legs; the corpse's legs show as dress-coloured tubes with the
  shoes at the hem.
- Rigid open hands (no finger motion).
- The hit recoil is snappy (see Jerk).
- Some Meshy chemise specks remain at the neckline edge; the eyes are procedural.

## Replay

Claim the project, then `TOK=<token> scripts/rebuild.sh all` (rig + anim; `work/source_rest.json` copied from m174).
Texture chain once: `export_uploads.py`, Meshy jobs (`requests/`), `transfer_uv.py` (UVMap, then HeadUV),
`uv_raster.py` (both, 1024), `bake_ao_natm.py`, `compose_m312.py`; then `TOK=<token> scripts/build_runtime.sh`,
`viewer_tiers.py`, `update_viewer_manifest.py` (labels in `work/viewer_clips.json`). Gates: `gates.py` (rebuild),
`sole_probe.py`, `jerk_probe.py`, `stride.py`, `stand_height.py`. Unused copied scripts (staff, cape, cast) remain for
reference.

## Walk and ankle fix (user review 2026-10-20)

- **Ankle twist:** `flatten_feet.py` gained a `:const` mode for the walk (batch A's rule): one constant correction per foot
  in the foot bone's frame (mean of the per-frame levelling over its grounded frames, 7°) and one constant pelvis lift
  (median ankle sink, 7.4 cm); the per-frame weight had switched on and off as each foot landed and lifted. Foot rotation
  step change per frame 21-24 → 17° (the remaining steps are the source walk's own).
- **Head zigzag:** `walk_bob.py` (batch A) after the feet: head height second difference 0.99 → 0.44 cm.
- Robe re-simulated; viewer check 54/54. Previous masters kept as `work/rig_v5_prewalkfix.blend` / `rig_v6_prewalkfix.blend`.

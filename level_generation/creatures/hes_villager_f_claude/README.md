# Hesper Landfall villager, female: three outfits — Claude humanoid project

> **Reduced (2026-10-22):** [`../hes_villager_f_reduce_claude/`](../hes_villager_f_reduce_claude/README.md) has the triangle-reduced export (LOD0 10,468 -> 7,114, far LODs rebuilt, leg-leak and hand-proximity gates still 0, no retexture); exported, not installed. This project's exports are unchanged.

A Landfall townswoman ([concept](../../../design/kreegan_world/concepts/people/villager_female.png), approved
2026-10-22). Humanoid playbook default route on the robe chain of `mm7_m342_claude/` (calf-length coat-dress on 14 x 4
simulated chains) with the m352 finger fit and unarmed clip timing. Monsters 10076–10078
(`design/kreegan_world/data/make_monster_tables.py`). **Exported, not installed** (the Hesper stage integration is
the parent session's).

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [tiers](review/tiers_contact.png) ·
[hands before/after](review/hands_before_after.png) · [hand views](review/hands_after/contact.png) ·
[walk legs before/after](review/walk_legs_closeup_before_after.png) ([before](review/walk_legs_before.png),
[after](review/walk_legs_after.png): front, both three-quarters, both sides at the contact and passing frames) ·
[clay clips](review/g7_clay_front.png)

## Deliverables

| File | What |
|---|---|
| `export/hes_villager_f.glb` | runtime: LODs 10,468 / 5,234 / 1,877 / 619 triangles, shadow LODs, variants `vf_a`, `vf_b`, `vf_c`, head material merged (4 atlases 2080×1024), 114 bones (52 body + 4 twist + 56 robe chain + 2 palm sockets), clips Standing, Walking, Hit, Death, Dead, Fidget |
| `export/hes_villager_f_lod0.glb`, `export/hes_villager_f.blend` | portable textured LOD0 (tier A base colours) and editable master; chain master `work/rig_v6.blend` |
| `textures/` | body 1K set, head 1K set, region masks (R coat, G off-white, B sash, A hair), `hvf_ramps.json`, material class maps |
| `integration/actors.yml` | staged binding (descriptors `Landfall Villager Female A/B/C`, scale 98.8 = 168 units over the 1.70 m model, stride 1.509 m, look 60°/35°) |

Install later (parent/user decision): `python3 tools/install_model.py level_generation/creatures/hes_villager_f_claude/export/hes_villager_f.glb --world hesper`
into the Hesper stage, then bind `integration/actors.yml`. Speed 200 < run threshold (2.4 × 98.8): run → Walking; no
attack clip (villagers flee; attacks play Walking as MM peasants do); cast → Standing.

## Variants (one mesh, region mask + ramps; `scripts/compose_hvf.py`)

No native palette: the ramps are authored. Each tier is fitted (`claude_shared/region_variants.fit_ramps`) to a target
that keeps the texture's luminance per texel with a new mid colour; tier A keeps Meshy's off-white, red and hair, and
its coat takes the concept's slate blue (Meshy painted the coat near black).

| Skin | Coat-dress (R) | Sleeves, under-tunic, trims (G) | Sash (B) | Hair (A) |
|---|---|---|---|---|
| vf_a | slate blue | off-white | town red | dark brown |
| vf_b | slate grey-green | yellow cream | ochre gold | dark blonde (black read the same as A's near-black brown) |
| vf_c | plum grey | pale grey | teal | auburn |

Gold piping, clasps, the ceramic bag and strap, earrings, boots, skin and trousers stay out of every mask.
Texture repairs in the compose: skin and hair one albedo × Meshy's fine shading; the neck below the head cut (710
coarse body texels, Meshy painted hair strands there) one flat colour from the head set's neck with flat normals; the
trousers (Meshy projected the coat's slate and the sash's red onto them above the knees, the **black patch under the
sash** of user review 1) one light-grey albedo × fine shading.

## Model and rig

- HD masters (Codex, `references_hd/`): primary, four views (`03_left` came back mirrored, flipped and recorded in
  `generation_runs.json`); head turnaround `references_head/`.
- Smart Topology 15k (15,451 triangles, 30 parts): coat-dress with sleeves (P00, split below 1.10 m: the central
  component is the skirt, the sleeves stay robe top), head + neck, trousers, bun, two hands, bag, strap, boots, sash
  tail, fringe, eyes, earrings, buttons and clips. Reduced after weighting to 10,468 (head and hands kept).
- Joints: Meshy auto-rig; arm rings and wrists from the hand shells (`arm_rings.py`, `joints_fix.py`); **knees moved
  17 cm** back onto the trouser-leg ring centres (Meshy had put them in front of the legs, where the open coat flaps
  hang). Fingers by connectivity on the hand shells.
- Weights (`weights_robe.py` + creature.json): coat below the waist and the skirt on the chains (waist 0.98 m, the
  arm split at 1.24 m where the sleeves part from the torso); sash tail one sector mix on the chains; bag and its clips
  rigid on the pelvis, the sash knot ends on B_Spine, buttons on B_Spine2; **strap** copies the coat under it, 40
  smoothing passes along it; legs keep their leg bones (the trousers show through the open front), the shins' stray
  thigh share moved to the calf, the trousers' waist above the hips on the pelvis.
- **Front panels on the thighs** (user review 2, 2026-10-22, "feet leak through the coat": the stepping thigh came out
  through the front panel, 66 mm in the walk). The coat's front panels and the sash tail take their own thigh's
  weight (`panel_thigh` in creature.json): full share within 70° of straight ahead fading out by 105°, from 4 cm under
  the chain roots fully 6 cm lower (the sash tail over 55 cm, so the thin strip does not shear), left/right blended
  over ±5 cm of the axis (the coat is closed above the split); the chain mix keeps its 3 largest influences so the
  4-influence cut never drops one. The chains' waist blend reaches 7 cm under the roots. The split now opens around
  the leg.

## Clips

| Role | Source | Notes |
|---|---|---|
| Standing 3.0 s | Mixamo Standard Idle | thighs turned in 4° (`narrow_stance.py`, the A-pose's 38 cm stance) |
| Walking 0.8 s | humanoid set Relax Walk Forward | feet flattened, bob evened; stride 1.509 m |
| Hit 1.0 s | Mixamo Standing React Large From Front, planted | arms flung out |
| Death 1.3 s / Dead | humanoid set Unarmed Death 1, legs at 40 % | falls onto her back; the coat laid 45 % of the way flat (fully flat, its top fell under the hips and the trousers showed over it) |
| Fidget 5.1 s | Mixamo Standing Idle 03 Examine, planted | looks at her hand |

Hands keep 60 % of the source finger curl. **User review 1 (2026-10-22, "hands buried inside body ... in all
animations")**: every clip now turns the upper arms out (`abduct_arms.py`, left 10°, right 18° beside the bag), the
smallest angles at which `scripts/g6_hand_proximity.py` finds no contact.

## Gates (`review/gates_v5.txt`, `review/g6_hands_after.json`, `review/g6_legs_after.json`)

- Arm stretch p99 ≤ 1.91 except Death R 2.13 (max 3.29 Death L); hands ≤ 1.56x; wrist swing ≤ 57°.
- Robe p99 ≤ 1.20 standing (Standing, Hit, Fidget), Walking 1.87 (max 2.69: the front panels ride the thighs, the
  sides the chains), Death 2.34 (max 2.88 while she falls); sash tail p99 ≤ 1.46; legs ≤ 1.66 p99 (Walking max 3.1);
  strap p99 ≤ 1.92 (max 4.8 at the back while lying in Death).
- **G6 legs** (`scripts/g6_leg_leak.py`: every thigh/knee trouser vertex against the coat's outer surface, signed by
  its normal, a vertex counts only when it lies over the panel): before 25/25 Walking frames (up to 17 vertices,
  66 mm) and 40/40 Death (50 vertices, 80 mm); now **0 leg vertices beyond 5 mm in every frame of every clip**.
- **G6 hands** (proximity on the open shells, every frame): **0 contact frames** in every clip, nearest 10.9 mm (left
  hand in Death) / 11.9 mm (right hand to the bag).
- Soles: Standing −0.7…−0.2 cm, Walking −2.0…+0.5, Hit/Fidget 0…0.4. Walk head second difference 0.50 cm, foot
  rotation step change 16.6/16.8° (m342's 16.8°). Jerk follows the sources.
- `check_winding.py` 0 inverted; viewer `tools/run_creature_review.py check` 18/18 tier/clip switches, no console
  errors. In game: not checked.

## Meshy

**30 of 60 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

## Replay

```sh
TOK=<lease> scripts/rebuild.sh all             # rig + anim + gates (gates_summary); HAND_CLEAR_L/R, STANCE_DEG, DEATH_LEGS
# textures once: export_uploads.py -> Meshy jobs -> transfer_uv.py -> uv_raster.py (UVMap, HeadUV) -> bake_ao_natm.py
PREVIEW=1 python3 scripts/compose_hvf.py && python3 scripts/tier_preview.py
TOK=<lease> scripts/build_runtime.sh
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
blender --background --factory-startup --python scripts/g6_hand_proximity.py -- work/rig_v5.blend <tag>
blender --background --factory-startup --python scripts/g6_leg_leak.py -- work/rig_v5.blend <tag>
```

A rig or weight change keeps the textures as long as `export_uploads.py` reproduces the uploads byte for byte (checked
after the knee and the panel fixes); then rebuild `work/rig_v6.blend` with `transfer_uv.py` from the new
`rig_v5h.blend` (`build_runtime.sh` only syncs the clips into `rig_v6`, never weights or bones).

## Known limits / engine notes

- The fringe curls beside the face read as thin dark strips; the hair band is painted only.
- The right arm hangs 8° further out than the left (the bag); symmetric angles left the right elbow on the bag.
- Lying, the coat's sides stay partly raised round the legs (45 % flat); fully flat showed the trousers over the coat.
- Engine: nothing required. The staged binding assumes the Hesper stage mounts `worlds/hesper/models/`.

# MM7 Manticore (m278) — Claude 3D model, batch E

Minicore / Manticore / Scorpicore (monsters 295–297, sprite groups m279/m280/m281, palettes 279/280/281).
Batch E ([../mm7_batches/BATCH_E.md](../mm7_batches/BATCH_E.md)): the model stops at project exports; nothing is
installed or bound.

![tiers in the review viewer above the native palettes](review/tiers_vs_native.png)

| Item | Value |
|---|---|
| Export | `export/mm7_m278.glb` (LOD0–3 + shadow LODs, three tier variants sharing every image) |
| Editable sources | `work/rig_v1.blend` (rig), `work/anim_v2u.blend` (rig + clips + UVs, exported), `export/mm7_m278_lod0.glb` |
| Triangles LOD0/1/2/3 | 16,048 / 8,020 / 2,820 / 831 |
| Skeleton | 23 bones + `Socket_Stinger`: Spine1–3, Neck1, Head, Tail1–6, lion legs UpperArm/ForeArm/FrontPaw and Thigh/Shin/HindPaw |
| Clips (30 fps) | Standing 2.0 s, Walking 1.0 s (stride 1.59 m), Running 0.6 s (2.15 m), Attack 1.0 s (impact 0.62 s), Hit 0.625 s, Death 1.1 s, Dead 1.0 s, Fidget 1.6 s |
| Textures | one atlas: 2K base colour, 1K normal / ORM / region mask; head islands 2.5×; two regions (mane, fur) |
| Meshy credits | **15 of 100**: Smart Topology 5, retexture 10 (our UVs) |
| Viewer | `http://127.0.0.1:8912/level_generation/creatures/mm7_m278_claude/review/viewer/index.html` — check: 3 tiers × 8 clips, no console errors |

## Anatomy decisions

- **Quadruped playbook.** A lion body with a fanged, almost human lion face, a shaggy mane and a scorpion tail; no
  wings in the native frames (none modelled).
- **Scorpion tail = exoskeleton chain.** Smart Topology returned the five chitin segments as separate pieces; each is
  100 % on its own bone (`Tail2`–`Tail6`, stinger last; `Tail1` is the skin tail base), with joints at the measured
  junctions between consecutive pieces (spider rule, `mm6_spi1_claude`). The rest tail leans 24° to the creature's
  right (three-quarter master); every clip rolls it back into the body's middle plane first.
- **Legs on IK footholds** (rat route), standing on symmetric footholds (the rest stance has the right forefoot 27 cm
  ahead). Walk: lateral sequence (LH, LF, RH, RF) on the native 1.0 s cycle; run: bounding trot.
- **Attack** (native `m278ab0/ac0`, `ac2/ad2`): rears up on the hind legs with both forepaws raised, then drops onto
  the paws while the tail lashes forward over the head — the arch swings from its base while the distal segments
  open (a per-segment curl rolled the tail into a ball; a base swing alone drove the stinger into the back). Impact
  0.62 s, stinger above the head. `Socket_Stinger` at the stinger tip for the ranged variant's release (the monster
  table lists a Water missile for attack 1).
- **Death:** rears, twists and falls onto its side (rat floor rules: grounded body, tail segments lifted off the
  floor, lying legs swung clear).

## Route (replay)

1. HD masters (`references_hd/`, Codex, gated); native frames through the three palettes (`scripts/native_palettes.py`).
2. Smart Topology 15k: 16,048 triangles, skin + 173 pieces (five tail segments, mane shingles, claws, teeth, eyes);
   `step1_clean.py` normalises the length to 2.4 m.
3. `rig_manticore.py` (joints `work/joints.json`; body heat weights on a hole-filled voxel proxy, tail segments rigid,
   mane shingles copy the skin under them, teeth/eyes on Head).
4. `anim_manticore.py work/rig_v1.blend work/anim_v1.blend`; `uv_export.py work/anim_v1.blend work/anim_v2u.blend`.
5. Retexture (`requests/retexture_v1.json`), `uv_raster.py` (1K, 2K), `bake_ao.py`, `compose_m278.py`.
6. `scripts/build_runtime.sh <token>`; viewer `viewer_tiers.py`, `update_viewer_manifest.py`.

## Tiers

Native palettes: the mane changes completely (sage + maroon → charcoal + dark violet → crimson + purple), the body fur
from greyish tan to warm tan (280, 281), the chitin tail and dark details stay. Two regions (mane, fur). The ramps
take hue and saturation from each tier's native pixels and luminance from the texel, scaled so the region's mean
matches the native mean × 1.05 (histogram matching copied the sprites' bright end: tier A came out white). The mane
ramp is split by native hue group (its darkest share takes the maroon colours at their own dark luminance, the rest
the sage colours; mixing them gave a muddy pink); the fur uses one chroma per tier. Claws, teeth and eyes are in no
region.

## Gates

- Edge stretch (`outliers.py`): ≤ 4.9× in every clip (hip/thigh junction in the run).
- Floor: body, tail segments and lying legs kept above the floor by the clip floor rules; corpse lowest vertex 4 cm.
- Viewer: 24 tier/clip switches, no errors; shots in `review/shots/`.

## For the user to review

- Motion is procedural and an interpretation of the native frames.
- The pale A body reads lighter in the viewer than the dark-shaded sprite (baked median 1.17× the native colour at
  gain 1.2; now 1.05).
- UV coverage is 28 % of the atlas (the mane shingles take most of it).

## Install later (not run)

**Reduced version:** [`../mm7_m278_reduce_claude/`](../mm7_m278_reduce_claude/README.md) (2026-10-20) — install its
`export/mm7_m278.glb` (the command below) instead of this one; the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m278_reduce_claude/export/mm7_m278.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (scale = native stand 138 px × frame scale 1.5 ÷ 1.983 m Standing
height = 104.4; B/C frame scales 1.75 / 2.0 via `scale_reference`):

```yaml
- descriptor: Manticore A
  model: worlds/mm7/models/mm7_m278.glb
  scale: 104.4
  yaw_offset: -1.570796327
  skin: m278_a
  animation:
    sockets:
      stinger: Socket_Stinger
    cast: Attack
    run: Running
    stride_length: 1.59
    run_stride_length: 2.15
    upper_body_root: Spine2
    look:
      nodes: [Neck1, Head]
      max_yaw_degrees: 40
      max_pitch_degrees: 20
    events:
      attack_melee: {impact: 0.62}
      attack_ranged: {impact: 0.62, release: stinger}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
# Manticore B / C: the same with skin m278_b / m278_c and scale_reference: Manticore A
```

No in-game check was run (optional for batch E).

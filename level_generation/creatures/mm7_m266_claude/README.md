# MM7 Hydra (m266) — Claude 3D model, batch I

Fire Hydra / Air Hydra / Chaos Hydra (monsters 286–288, descriptors Hydra A/B/C, sprite groups m267/m268/m269,
palettes 267 / 57 / 269). Batch I ([../mm7_batches/BATCH_I.md](../mm7_batches/BATCH_I.md)): the model stops at project
exports; nothing is installed or bound.

![tiers in the review viewer above the native palettes](review/tiers_vs_native.png)

| Item | Value |
|---|---|
| Export | `export/mm7_m266.glb` (LOD0–3 + shadow LODs, three tier variants sharing every image) |
| Editable sources | `work/rig_v1.blend` (body rig), `work/graft_v2.blend` (heads grafted), `work/anim_v2.blend` (final mesh, UVs, rig, clips; exported), `export/mm7_m266_lod0.glb` |
| Triangles LOD0/1/2/3 | 17,866 / 8,925 / 3,109 / 913 (five heads 12.3k, body, necks and joint lofts 5.6k) |
| Skeleton | 71 bones + `Socket_Mouth`: Spine1–3, Tail1–8, legs (UpperArm/ForeArm/FrontPaw, Thigh/Shin/HindPaw), five neck chains Neck<k>_00.. + Head<k> (k = 1..5 from the hydra's right to its left) |
| Clips (30 fps) | Standing 2.0 s, Walking 1.0 s (stride 1.3 m), Running 0.6 s (1.9 m), Attack 1.0 s (impact 0.62 s), Hit 0.73 s, Death 1.27 s, Dead 1.0 s, Fidget 1.0 s |
| Textures | body set: 2K base colour, 1K normal / ORM / region mask; head set: 1536×1024 atlas (one 512² tile per head), 768×512 normal / ORM / mask; one region (the hide) per set |
| Meshy credits | **100 of 100**: body Smart Topology 5, five head Smart Topologies 25, five head retextures 50, body retexture 10 (v1, superseded) + 10 (v2) |
| Viewer | `http://127.0.0.1:8912/level_generation/creatures/mm7_m266_claude/review/viewer/index.html` — `run_creature_review.py check`: 3 tiers × 8 clips, no console errors |

## Anatomy decisions

- **Body: quadruped playbook.** A squat four-legged reptile with a spiked tail lying on the floor; IK legs on symmetric
  footholds (the Smart Topology rest stance is skewed by the three-quarter master: the right hind foot stands 0.35 m
  ahead of the left), the tail turned about world Z so it stays on the ground.
- **Five heads, each its own model** (quadruped playbook, multi-headed creatures): the full-body Smart Topology spent
  ~3 % of its mesh per head and lost the identities (no big horns on head 5, fins on the wrong heads). Per head: Codex
  head masters (`references_heads/h<k>/`, five views each, from crops of the accepted body masters), Smart Topology
  15k, `head_prep.py` (decimated per piece so teeth and crest tips survive — one collapse over the head erased the
  teeth — cut behind the skull by a throat-to-nape plane read off `side_plot.py`, unwrapped), retextured on those UVs.
  Head identities (left to right in the front view): 1 dark blue with two ribbed bat-wing fins, 2 violet with a spiky
  black mane, 3 tall centre neck, navy crown of spikes, 4 grey-teal with a rust frill, 5 rust-brown with big ivory horns.
- **Graft** (`graft_hydra.py`, after `mm6_hyd_claude/scripts/graft_heads.py`): each head placed rigidly (snout on our
  snout, forward on our Head bone limited to 15° down so heads look ahead as in the masters, scale 1.4 × our neck width
  / the skull's cheek width × a per-head factor from the native relative sizes); our neck cut a few cm behind the head's
  cut ring and joined by a lofted tube (short tangent at the head ring; a full one bulged into a bald dome behind the
  skull). The head keeps its own UVs (no bake: the grafted mesh is the retextured mesh). Old-head remnants are removed
  by a flood fill restricted to the neck's own chain (it leaked through fused old heads otherwise).
- **Neck 1 is a separate Meshy shell** overlapping the body at its base; it is weighted with the skin (fused voxel
  proxy) and kept by the graft's crumb rule only when it lies behind its cut (v1 deleted it as a crumb and head 1
  floated in the viewer; found by the viewer shots, fixed in v2, which needed the second body retexture).
- **Head 3 moved forward and up** (user review 2026-10-20: "middle head is embedded in the neck": its lower jaw sat
  inside the front of its own neck, which rises above the jaw line): `head_shift.py` moves the head rigidly 7.5 cm
  forward and 4.5 cm up in the finished rest mesh, its loft blending the shift along its length. Applied after the
  UVs, so the body unwrap and the retextures stay valid (a new graft would have needed a new body retexture).
- **Rest-mesh cleanup** (`fin_squeeze.py`): head 1's fins narrowed laterally (×0.6 beyond 10 cm from the skull plane;
  they swept through head 2's crest at rest), six floating head fragments and four loose dorsal spikes of the old heads
  removed.
- **Weights** (`rig_hydra.py`): heat weights on a 2.2 cm voxel proxy of skin + neck 1, then chain ownership by
  geodesic distance from seeds on each neck's upper half: a neck vertex keeps only its own neck + chest, body vertices
  only the two lowest bones of each neck (heat weights leaked between the tightly packed necks); loose spikes copy the
  skin under them. Grafted heads rigid on Head<k>; lofts blend Head<k> → the neck ring's weights.
- **Motion** (`anim_hydra.py`): necks bend by world-space pitch/yaw per bone with the bend weighted toward the head
  (or from the base when they fall in Death); per-neck phases so the heads never move in unison. Heads are kept apart
  by a constant outward spread and an exact per-frame test (BVH overlap of each head with the other heads and upper
  necks on the posed mesh; the touching pair's fan opens 2.5° more, the heads counter-yaw to keep looking ahead).
  Attack (native a frames): the necks rear back (the side strikers less), then the middle three lash forward and down
  with the bend travelling base to head; impact 0.62 s; the outer two follow and spread. Death: brief rear, collapse
  onto the belly, legs sprawled, slight roll, the necks fall forward in a fan onto the ground (native corpse xa).

## Route (replay, all scripts in `scripts/`)

1. `native_palettes.py m266 267 57 269`; HD masters `references_hd/` (Codex, `CODEX_BRIEF.md`; primary corrected once
   for a fifth foot; views 01–04 from the frozen primary).
2. Smart Topology 15k → `step1_clean.py` (height 2.0 m) → `dump_mesh.py`, `limb_trace.py` (legs, necks),
   `medial.py` (joints onto the medial axis) → `rig_hydra.py` (`work/rig_v1.blend`, `work/rig.json`).
3. Heads: briefs `references_heads/h<k>/CODEX_BRIEF.md` → `requests/head<k>_smart_topology_v1.json` → `head_prep.py`
   → `requests/head<k>_retexture_v1.json`.
4. `graft_hydra.py work/graft_v2.blend` → `reduce_body.py graft_v2 red_v2 0.80` → `fin_squeeze.py red_v2 clean_v2` →
   `uv_hydra.py clean_v2 uv_v3` (writes `texturing/body_upload.glb`) → `requests/body_retexture_v2.json` →
   `head_shift.py uv_v3 uv_v4`.
5. `dump_uv.py`, `bake_ao_hydra.py`, `compose_hydra.py` (atlas, AO grade, masks, ramps) →
   `anim_hydra.py uv_v4 anim_v2` → gates `check_hydra.py`, `outliers.py` → `build_runtime.sh <token>` →
   `viewer_tiers.py`, `update_viewer_manifest.py`.

## Tiers

The native recolour is one region, the reptile hide (palette indices 64..191; the sprite restoration manifest's
`blue_reptile_skin`): olive-yellow (267, A), the bitmaps' blue-grey (57, B), red (269, C). Ivory horns/claws/spikes,
silver belly plates, red mouths, the rust head 5 and head 4's teal skin and rust frill keep their colour. Mask: on the
body and heads 1–3 everything but ivory, plates and mouths; on heads 4 and 5 only the blue neck scales. Ramps from the
native hide pixels of every standing/walking frame in each palette, colour by luminance quantile, luminance from the
texel × native mean × 1.05; the darkest stops lose 45 % of their chroma (pure blue/red specks otherwise).

## Gates (`work/anim_v2.blend`)

- Head intersections (`check_hydra.py`, every frame): 0 in Standing, Walking, Running, Hit, Death, Dead, Fidget;
  Attack one frame (13) with 6 overlapping triangle pairs (a horn tip of head 4 grazing head 5 during the wind-up).
- Floor: lowest vertex ≥ −1.2 cm in every clip except Death, where a hind paw dips 3.9 cm under the floor for a few
  frames mid-fall (the corpse lies on the floor).
- Edge stretch (`outliers.py`, edges over 2 mm): ≤ 5.0× in every clip except one short inner edge of neck 1 at 10.3×
  (Attack frame 14) and 7.0× (Hit), no visible tear in close-ups.
- Winding: 0 inverted closed parts (`check_winding.py`); viewer check 24 tier/clip switches, no errors.

## For the user to review

- Motion is procedural and an interpretation of the native frames.
- LOD0 is 17.9k triangles (12.3k of it the five heads) — over the 15k guideline ceiling, like the accepted MM6 hydra
  (17.6k); a further head reduction trades away teeth and crest spikes.
- Tiers read lighter and smoother than the dark-shaded sprites (as noted for the batch E beasts); `RAMP_GAIN` in
  `compose_hydra.py` darkens them.
- The back of each head shows a rounded nape where the loft meets the crest (seen only from behind).
- No in-game check was run (optional for this batch).

## Install later (not run)

**Reduced version:** [`../mm7_m266_reduce_claude/`](../mm7_m266_reduce_claude/README.md) (2026-10-20, 17,866 ->
13,946 triangles; it also fixes head 5, whose eyes are horns in this export) — install its `export/mm7_m266.glb` (the
command below with that path) instead of this one; the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m266_claude/export/mm7_m266.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (scale = native stand 179 px × frame scale 2.0 ÷ 2.098 m rest
height = 170.6; B/C frame scales 2.75 / 3.0 via `scale_reference`). The hydras' Attack 1 is a ranged breath (Fire /
Air / Energy missiles), released from the centre head's snout:

```yaml
- descriptor: Hydra A
  model: worlds/mm7/models/mm7_m266.glb
  scale: 170.6
  yaw_offset: -1.570796327
  skin: m266_a
  animation:
    sockets:
      breath: Socket_Mouth
    cast: Attack
    run: Running
    stride_length: 1.3
    run_stride_length: 1.9
    upper_body_root: Spine2
    events:
      attack_melee: {impact: 0.62}
      attack_ranged: {impact: 0.62, release: breath}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
# Hydra B / C: the same with skin m266_b / m266_c and scale_reference: Hydra A
```

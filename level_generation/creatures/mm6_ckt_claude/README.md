# MM6 Cockatrice (ckt) — 3D model, 2026-10-08

Cockatrice A/B/C (496 Agar's Pet, 497 Agar's Monster, 498 Agar's Abomination; palettes 680 tan / 681 turquoise /
682 red wings; frame scale 0.8 for all). A bipedal vulture-headed bird with bat wings and a spiked tail. Built with
the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) flyer route (bat wings) plus two walking bird legs,
[HD master references](../CLAUDE_HD_MASTER_REFERENCES.md) and [creature textures](../CLAUDE_CREATURE_TEXTURES.md).
Opt-in via `debug.actor_models=true`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_ckt.glb` (skins `ckt_a/b/c`: one shared skin, membrane ramp; separate 1K head set shared by all tiers; body base colour 1K) |
| Triangles LOD0/1/2/3 | 8,672 / 4,269 / 1,456 / 416 (Smart Topology 15,735, reduced per part, head kept at 85 %) |
| Skeleton | 37 bones: Hips, Chest, Neck1–2, Head, Tail1–8; per side UpperArm/ForeArm, Finger1–3 a/b, Thigh/Shin/Tarsus/Foot; `Socket_Head` (cast glow) |
| Clips | Standing 1.5 s, Walking 0.75 s, Attack 0.75 s, Cast 0.75 s, Hit 0.625 s, Death 1.0 s, Dead, Fidget 1.5 s (procedural) |
| Binding | `scale: 428` (native standing height 245 px × SFT scale 0.8 = 196 units over the 0.458 m mean Standing height; the SFT scale is 0.8 for all three tiers, so B/C equal A), B/C `scale_reference: Cockatrice A`, `run: Walking`, `stride_length: 0.3`, `cast: Cast` with `cast_focus_socket: Socket_Head` (Mind Blast) |
| Meshy credits | **25 / 30** (Smart Topology 5, body retexture 10, head retexture 10) |

## Pipeline (scripts/)

1. `references_hd/`: five Codex HD masters (1536×1024, brief `CODEX_BRIEF.md`; inputs: native standing views and
   walk side frames in the turquoise palette, the three-palette sheet, one restored frame for material). The masters
   use the turquoise wings (681) so the membrane separates cleanly by hue from the brown body.
2. Meshy Smart Topology (15k). `components.py`: one main body, two wing leading-edge bone pieces, ~130 ruff/spike
   bits and one stray fragment by the right foot (deleted in `rig_ckt.py`).
3. `analyse.py` + `grid_views.py`: joints from numbers (midline z-range per y, leg centroids per z, wing sheet y per x).
   The wings stand as a near-vertical sheet, so wing joints are given in front view (x, z) and y is sampled from it.
4. `rig_ckt.py`: bat-style wing (upper arm, forearm, three fingers fanning from the wrist), bird leg (thigh, shin,
   tarsus, foot: knee forward, hock back), eight tail bones. **Heat weights failed on the Meshy mesh** (thin membranes,
   loose pieces: 8,265 vertices unweighted, also at 10× scale), so they are solved on a watertight voxel-remeshed
   proxy (4 mm) and copied back by nearest surface (Data Transfer); leftovers take the nearest weighted vertex;
   separate pieces are rebound (long ones per vertex, small ones rigidly). `stress.py` → `review/stress_v1.png`.
5. `anim_ckt.py`: legs by IK — ankle on a foothold, tarsus keeps its rest direction plus a pitch, hock from that,
   Thigh + Shin two-bone IK with the knee pole in front, foot at rest orientation plus toe pitch. Walk: duty 0.6, two
   wing beats per stride as in the native walk; Attack: hop with a wing down-sweep and a two-footed talon kick; Hit and
   Death throw the head back (native); the corpse lies on its belly with the wings fitted flat (bat `fit_down`) and
   the tail laid on the floor (each tail segment aimed to rest at its own radius, so the floor rule never bends the
   tail up). Cast (Mind Blast) rears up with wings high and thrusts the head. Sign lesson: +X rotation tips the front
   (−Y) down and lowers the head; `minz.py` keeps every clip ≥ −6 mm.
6. `uv_export.py` (head and upper neck 2.5×) → Meshy `retexture_v1` from the four HD views.
7. `reduce_lod0.py` (once; full mesh `work/anim_v1_full.blend`): edit-mode decimate of each part's faces (a
   vertex-group Decimate modifier barely reduced this mesh): legs 40 %, wings 50 %, tail 50 %, body 70 %, neck 60 %,
   head 85 %. `review/lod0_reduction_before_after.png` (no visible loss in head, foot or wing close-ups).
8. `compose_ckt.py`: region `membrane` (turquoise wing texels), material classes; AO bake and grade.
9. `tier_ramps.py`: membrane ramps by palette transfer (`claude_shared/native_shading.py`, config
   `native_shading.json`: membrane pixels of the native standing views from the restored mask, matched in 681 and
   read in 680/681/682), gain 1.3.
10. `build_runtime.sh --install`; membrane double-sided; specular 0, metallic 0.

## Checks

- MM6 actor regression suite 16/16.
- In game: `review/ingame/compare_v2.png` (top left 3D, top right sprites, bottom: static 3D model at scale 400 beside
  a sprite cockatrice). Tiers A tan, B turquoise, C red.
- Not seen yet: the creatures flying (Fly Y; the model keeps its walking clips in the air, like the native sprites)
  and the Mind Blast cast glow at the head.
- [Native shading transfer](../NATIVE_SHADING_TRANSFER.md) on the body (2026-10-09, `scripts/native_body_shade.py`
  after `compose_ckt.py`, then the grade with defaults): feathers of body, tail and neck take the native brown
  brightness by height (front and back standing views) at 0.85 and become a second tier region (mask G) whose ramp
  is read from the same native pixels in every palette (`tier_ramps.py`). A first pass that only rescaled brightness
  and kept Meshy's orange-red hue barely changed the look. Pre-transfer files: `textures_pre_native/`.

## Head texture set (2026-10-08)

User review (test_img/2164): teal fringes and smeared red patches around the eyes; the head did not look good. The
body retexture had the head at a few hundred pixels, and the turquoise wings bled into it. Now a separate 1K head set
per [creature textures](../CLAUDE_CREATURE_TEXTURES.md) ("Head-only retexture"):
- `references_head/`: Codex head turnaround (brief `CODEX_BRIEF.md`: clean red eye mask, no teal anywhere, beak
  closed), from the accepted body masters.
- `../claude_shared/head_texture_split.py --groups Head Neck2`: 2,498 head faces (bare head and neck, cut at the ruff
  collar, where the feather pieces hide the seam) get their own UVs; backup `work/anim_v1_pre_head.blend`.
- Meshy `head_retexture_v1` (10 credits) → `compose_head_set.py` in `build_runtime.sh` with `--seam-gain 1.0`: the
  measured seam gain was 1.84 because pale ruff feathers sit on the body side of the boundary and pink skin on the head
  side; applying it brightened the head. The option was added to the shared tool for such cases.
- Export: `CockatriceHead_A` on faces with `head`, one material for every tier (only the membranes change).
- Before/after: `review/ingame/head_before_after.png` (left the reviewed head, right the head set); close-ups
  `review/head_set_v1.png`.

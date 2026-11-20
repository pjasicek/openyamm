# MM7 Robot v2, all metal (m386) — 2026-10-21

Batch H, model 5 ([BATCH_H.md](../mm7_batches/BATCH_H.md)), rebuilt after user review of
[mm7_m386_claude](../mm7_m386_claude/README.md): "it looks like some sort of mini-dinosaur's skeleton merged with
robot parts … this should really be fully metallic robot … attack = shot with the gun there". Identity **mm7:m386**,
descriptors **388–390** (Seeker, Sentinel and Assassin Droid; `Robot A/B/C`), one palette 386 for all tiers, frame
scales 1.0 / 1.3 / 1.7. Route: [non-humanoid playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md), rigid hard-surface creature;
LOD0 reduced with the [retopology playbook](../RETOPOLOGY_PLAYBOOK.md) texture-aware MeshLab ladder. Not installed
(batch rule). The v1 project stays as the rollback.

| Item | Value |
|---|---|
| Export | [`export/mm7_m386.glb`](export/mm7_m386.glb), 7.9 MB, sha256 `2d23242ce6f3bcb7541229728e36b6286894ee3887f694f76d4356293733f0cc` (texture fix, see below; the first v2 export `4067195c…` is `work/mm7_m386_export_smartuv.glb`) |
| Triangles LOD0 / 1 / 2 / 3 | **5,223 / 2,497 / 1,135 / 525** (Smart Topology 14,827 in 249 pieces; 14,929 after the spike split) |
| Unreduced source | `work/mm7_m386_source.glb` (14,929 / 7,433 / 3,662 / 1,730, 9.8 MB, sha256 `f9e64169…`), same textures, tiers and clips |
| Rig | 22 bones: Body (root), Gun, Neck1–2, Head, Jaw, Tail1–8, per leg Leg_XX (sleeve) + Spike_XX; sockets `Socket_Eye`, `Socket_Muzzle` |
| Clips | Standing 1.5 s, Walking 1.25 s (loops), Attack 0.875 s (fires at 0.44 s), Hit 0.875 s, Death 0.75 s, Dead 1.0 s, Fidget 0.75 s |
| UVs | hard-surface layout (`scripts/uv_hardsurface.py`): 844 islands, 813 texels/m (head, jaw, gun 1,625), 8-texel margins at 2K |
| Maps | 2K base colour (Meshy, lightly AO graded), 1K normal, 1K metal/rough (glTF ORM: R AO for specular occlusion, G Meshy roughness, B Meshy metallic capped 0.3), 1K region mask (R green optics, G blue coils) |
| Meshy | **25 credits** (cap 35): Smart Topology `meshy-t2.5` 15k (5), retexture `meshy-7` four HD views on the Smart UV layout (10, superseded), retexture on the hard-surface layout `retexture_v2uv` (10) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m386_v2_claude/review/viewer/) (three tiers) |

## Design: the sprite's silhouette, all machined metal

The native sprite's head, neck and tail are bone-coloured and read as a raptor skeleton; v1 followed that literally
(skull, vertebrae, ribs, teeth). v2 keeps the native silhouette, pose, proportions and colour scheme and rebuilds every
part as a machine (`references_hd/CODEX_BRIEF.md`, "Why this is a v2"): an armoured sensor head of riveted brass and
steel plates with a hinged metal jaw and green optic lenses, a neck of articulated brass collars over a black
cable spine, a tail of interlocking brass ring segments with flat steel cooling vanes underneath and a steel tip,
gunmetal chassis with the white front orb, four straight polished steel stilt spikes in rusty bronze sleeves on rust-red
arm plates (no knees), and a ball-and-barrel gun with blue-violet coils hung under the chassis on a rear bracket.

References: five Codex masters (1536×1024, two runs, `generation_runs.json`; inputs only the original bitmaps
`native_views.png` and `native_identity.png`). Gate: nothing reads as bone or skeleton in any view; four spikes;
gun under the body pointing forward; 03 faces image left, 04 image right. Codex noted top/bottom margins under 60 px
(nothing cropped) and some camera drift between the side views; accepted, as they only feed the retexture.
Selected hashes in `creature_3d_progress.json` (`references_hd`).

## Rig (`scripts/rig_robot.py`)

Built directly from the Smart Topology return (forward −Y, up +Z, left +X):
- Each leg came as one surface: sleeve, arm plate and spike rod. The rod faces are split off at the rod/sleeve seam
  and the rod's open top is extruded 10 cm up its axis inside the sleeve, so the spike can slide out of its sleeve
  (native walk frames) without stretching or showing its end. The rod and its top cap above the ring bind to
  `Spike_XX`; sleeve, ring and arm plate to `Leg_XX`, blending to Body 8–13 cm from the sleeve centre (arm plates bend
  at the chassis); cables near a sleeve blend Body → Leg over 5–10 cm.
- Tail (one piece) and neck: weights by arc position along their centerlines (tail centerline by surface shortest
  path, refined to slab centroids), linear crossfades at the joints; the tail vanes copy their nearest tail vertex.
- Head pieces → Head; lower jaw and its teeth → Jaw (hinge at the jaw's rear disc); gun ball, barrel and rear housing
  → Gun, hinged at the rear bracket (the bracket stays on Body); everything else → Body.
Rest renders: `review/geometry_st1_*.png`; dominant-bone check plots were made from `work/dom.npz`.

## Motion (`scripts/anim_robot.py`)

- **Attack = the gun shot** (native aa–ag timing, 21 frames). The gun is carried stowed muzzle-down (14°) in every
  other clip. In the attack it swings up level onto the target (0.17–0.26 s) while the chassis braces and the head
  holds on target, charges (the binding's `glow` on the muzzle socket lights the coils until the release), and fires
  at **0.44 s** from `Socket_Muzzle` at the barrel tip: the gun slides back 3.5 cm along its barrel and kicks, the
  chassis jolts back, the tail whips and the jaw snaps; then it re-stows. Melee and ranged bindings both use it.
  Close frames: `review/attack_gun.png`.
- **Walking**: diagonal pairs FL+RR / FR+RL, duty 0.55, step 0.18 m, lift 6 cm, chassis carried 1.5 cm higher; each
  sleeve aims at its foothold and the spike slides out to reach it, so the tips stay planted in stance. Slides stay
  within −1.2 … +9 cm (the cap's overlap in its ring above, the hidden rod extension inside the sleeve below); swing
  lift and the corpse splay are clamped to that range. Body travel **0.327 m per cycle** (binding `stride_length`).
- **Hit**: jolt sideways and back, legs skid, head whips, jaw snaps open. **Death**: shudder, spikes splay out, the
  chassis drops, the gun folds up under it and it settles on the gun ball, neck and tail lie on the floor (native
  `xa`); **Dead** holds it (`review/dead_check.png`). **Fidget**: looks left and right. **Standing**: idle hum.
- Floor (`clip_check.py` → `review/clips_r1.json`): spike tips at z 0 in every standing clip; corpse at +3 mm; nothing
  below the floor in any frame. The stowed muzzle hangs 4.1 cm (8 units) above the floor.

## Textures and tiers (texture fix 2026-10-21: `scripts/uv_hardsurface.py`, `scripts/compose_v2.py`)

User review of the first v2 export: "robot looks good, just the texture quality is terrible". Causes, measured
(`review/uv_stats.json`):

- **UV layout.** Smart UV Project (66°) cut the 254 connected pieces into **3,340 islands**, median 24 texels² (about
  5 × 5) at 2K, p10 3.5 texels²; with an 8-texel margin each, the islands filled only **7.5 %** of the atlas (398
  texels/m; the 2.5× head scaling did not survive packing: 427). Meshy painted blobs into those cells and the mips
  bled across the seams: the smeared gun, chassis and jaw.
- **Material.** The creature contract's `metallicFactor 0` (written for skin) dropped Meshy's metal maps, so the
  metallic-workflow base colour drew as flat speckled paint (chalky white spikes).
- **Tiers.** The luminance-rank ramps over steel / brass / rust (p95 up to 20/255) added posterisation.

Fix (10 credits):

1. `uv_hardsurface.py` on the unchanged rig/clip master (`work/uv_master_smartuv.blend` kept as rollback): charts
   start as whole pieces, are unwrapped angle-based from cleared UVs (Blender's unwrap also cuts wherever existing UVs
   disagree, which first kept the old islands) and every chart whose mean angle distortion exceeds 1.35, whose texel
   density spreads more than 0.25 (mean |log|) or that flips is split in two along its strongest crease (two-seed
   region grow over face adjacency; splitting by facing alone shattered charts into fragments). Then even density,
   head / jaw / gun at 2×, Blender packing (cardinal rotation, concave) at 2K with 8-texel margins. xatlas brute-force
   packing (`xatlas_pack.py`, optional) reached only 821 vs 813 texels/m, so the limit is the island count of a
   254-piece hard-surface mesh, not the packer.

   | | Smart UV (old) | hard-surface (new) |
   |---|---:|---:|
   | islands | 3,340 | **844** |
   | island size median / p10 (texels² at 2K) | 24 / 3.5 | **543 / 94** |
   | surface in islands ≥ 32 × 32 texels | 16 % | **78 %** |
   | texels per metre, body / head-jaw-gun | 398 / 427 | **813 / 1,625** |
   | atlas fill (triangles) | 7.5 % | 31 % |
   | mean / p95 angle distortion | 1.16 / 1.47 | 1.17 / 1.60 |
   | flipped faces | 0 | 0 |

   Sweep (`review/uv_stats_*` during the run, summarised): sharp-edge starts at 50–80° gave 1,470–1,680 islands, the
   facing split 1,500–2,300; looser limits (1.45 / 0.30) 759 islands at more distortion. Checker renders and layouts:
   `review/uv/uv_sheet.png`.
2. Meshy retexture `retexture_v2uv` (`meshy-7`, original UVs, PBR, 2K, the same four HD masters): all 14,929 UV
   triangles came back identical (`review/uv/meshy_uv_check.json`, max deviation 0).
3. `compose_v2.py`: Meshy's base colour as is (padded, AO grade 0.25, glows untouched); ORM = R baked AO
   (`openyamm_specular_occlusion: orm`, no specular mask), G Meshy roughness (0.27–0.41), B Meshy metallic
   (~0.95 everywhere) **capped at 0.3**, `metallicFactor 1`. The cap comes from the in-game A/B
   (`review/ingame/ingame_sheet.png`): uncapped, daylight left only the blurred sky reflection (spikes blue-black,
   brass murky); 0.5 still drew the robot darker than the old export in the dim Lincoln, where the shader gives
   metal ambient only as 1 − metallic (`fs_model.sc`); 0.3 matches the old brightness in both and keeps a steel and
   brass sheen.
4. **Tiers** (`tier_factors.py` after `region_variants.py`): all descriptors use palette 386 and the original engine
   multiplies B and C by `TintColor` (Sentinel `0x93c4ba`, Assassin `0xd8c462`), which OpenYAMM parses but does not
   apply. That multiply is now the material's `baseColorFactor` (linear tint: B `[0.292, 0.552, 0.491]`, C
   `[0.687, 0.552, 0.122]`): exact and smooth, metal reflections included. The region mask covers only the green
   optics (R) and blue coils (G); per-tier ramps map the tinted luminance back to the untinted glow colour (fit mean
   10 / p95 32–41 of 255 on these small textured glows). Tier A has no region ramps: Meshy's colour unchanged.
   Viewer tiers apply the factor before the ramps (`viewer_tiers.py`); the viewer gained a studio environment so metal
   reads (`review/viewer/review.js`; the engine reflects its sky instead, darker outdoors).

Old texture set: `textures_smartuv/`; old source / export: `work/mm7_m386_source_smartuv.glb`,
`work/mm7_m386_export_smartuv.glb`.

## Reduction (texture-aware MeshLab ladder, no Blender decimate)

`build_source.sh` exports the unreduced UV master through the full chain to `work/mm7_m386_source.glb`;
`import_source.py` (weld 19,805 → 773 open edges, 106 coincident vertices with other weights kept apart) →
`dump_mesh.py` → `robot_groups.py` (face labels) → `run_ladder.sh` (decimate_tex, reduce_ladder with weight transfer
and piece weights, compare_ladder; thresholds scaled to the 0.96 m length: p99 2.9 mm, max 14 mm).

Labels: spikes and caps **kept exactly** (705 faces; the first runs shortened the cone tips by up to 12 mm and they
are the floor contacts), head + jaw protected at their own ratio (1,595), neck + tail (3,354), small pieces (1,546),
gun (1,606), rest (chassis, sleeves, arm plates, cables: 6,123) takes the remaining budget.

| config (head / chain / small / gun) | step | triangles | p99 / max mm | IoU | SSIM |
|---|---|---:|---|---|---|
| no keep, 0.6 / 0.5 / 0.6 / – | r50 / r44 / r38 / r34 | 7,463 / 6,567 / 5,671 / 5,073 | 3.5 / 4.7 / 7.1 / 11.1 (max 9.8–36.6) | 0.969–0.885 | |
| A 0.6 / 0.4 / 0.6 / 0.45 | r47 / r44 / r41 | 7,013 / 6,565 / 6,117 | 4.0 / 4.7 / 5.7 (max ≤ 11.9) | 0.972–0.965 | 0.985–0.982 |
| B 0.55 / 0.35 / 0.5 / 0.4 | r40 / r37 / r34 | 5,969 / 5,521 / 5,073 | 5.1 / 6.3 / 9.1 (max 18.9) | 0.964–0.950 | |
| C2 0.5 / 0.3 / 0.45 / 0.35 | r50 / r45 / r41 | 7,461 / 6,715 / 6,117 | 4.9 / 5.0 / 5.2 (max 9.8) | 0.963–0.961 | |
| **C 0.5 / 0.3 / 0.45 / 0.35** | r37 / **r35** | 5,521 / **5,223** | 5.6 / **6.1** (max 11.9) | 0.959 / **0.957** | 0.981 / **0.980** |
| C + drift lock (8 mm) | r37 / r35 | 5,519 / 5,221 | 9.3 / 12.6 (max 66.6) | 0.92 | rejected: the lock starves the chassis |

**Pick: C r35, 5,223 triangles.** No step of any configuration meets the numeric gates, not even r50 at 7,463
(p99 3.5 mm): this hard-surface model is hundreds of small bevelled plates, bolts and cables, and every cut moves
their edges by a few millimetres (`probe_bones.py`: the error is spread over chassis, sleeve rings and gun, not one
part). The pick is visual, as for the dragonfly: close-ups of head side/front, neck, gun, sleeve while walking,
chassis, chassis top, tail and corpse (`review/close/sheet_AB.png`, `sheet_BC.png`, `sheet_top.png`; source vs
A44 … C35) show no visible difference at any step down to r34. Largest remaining deviations: the sleeve-top cable
rings and the white orb's rim (11–12 mm in the worst frame; 0.6 % of the length, about 2 game units at scale 200);
the green optic lenses are slightly less round in the head-front close-up.

Checks on r35: no face stretches over 20× in any clip (`stretch_check.py`); texture drift 137 faces over 40
(260 cm²) and 417 dark-sliver faces, against 110 / 452 already at r50: a noise floor of the dark painted crevices
of the chassis, which renders the same as r50 (`sheet_top.png`).

**Re-run after the texture fix** (the old LOD0 carried the old UVs): the same configuration C on the new source
(`ladder_v2uv` in `work/ladder_C.blend`, `work/selection_C.json`):

| step | triangles | p99 / max mm | IoU | SSIM | drift > 40 (faces / cm²) | dark slivers |
|---|---:|---|---|---|---|---:|
| r45 | 6,715 | 5.3 / 10.3 | 0.960 | 0.983 | | |
| r41 | 6,117 | 5.5 / 10.5 | 0.960 | 0.982 | 57 / 85 | 375 |
| r37 | 5,521 | 6.2 / 14.4 | 0.957 | 0.980 | 69 / 117 | 364 |
| **r35** | **5,223** | **6.7 / 14.2** | **0.955** | **0.978** | **75 / 136** | **343** |
| r33 | 4,923 | 7.8 / 15.1 | 0.951 | 0.977 | | |

No step meets the numeric gates (as before). **Pick: r35, 5,223 triangles**, by the same close-ups
(`review/close/sheet_v2uv_head.png`, `sheet_v2uv_body.png`: source / r41 / r37 / r35): no visible difference; the
green lenses are slightly less round from r41 down. Drift and slivers are lower than the old r35 (137 faces / 260 cm²,
417). No stretched faces in any clip.

`build_export.sh`: `export_cand.py` (Cand_35) → `swap_lod0.py` (into the source GLB) → `floor_contacts.py` (every
clip: spike tips and corpse) → `lod_chain.py` (0.5 / 0.25 / 0.125, 4 influences, contacts protected) →
`shrink_shadow_lods.py` (≤ 1 mm) → `carry_variants.py` (7 primitives) → `check_winding.py` → `viewer_tiers.py`.
`lod_check.py` (`work/lod_check_r35v2.json`, every frame of every clip, every LOD): rest bounds kept at every LOD;
lowest point −0.5 mm at LOD1 Walking, 0 at the others; corpse at +3 mm on all LODs; no stretched faces.

## Size

Scale **200**, from the native frames (front height 117 px, side length 184 px) against the model's rest height
0.566 m and length 0.95 m (207 / 194). The rear legs splay wider than the sprite's (front width 0.81 m, 162 units
against the native 137 px). At 200 the tail top is 113 units in the bind pose, up to 119 in Standing and 136 in the Hit rear-up
(tier A collision height 120); B/C scale by 1.3 / 1.7 through `scale_reference`, as the sprites do.

## Checks

`check_winding.py`: 0 inverted closed parts. `run_creature_review.py check`: 3 tiers × 7 clips, 21 switches, no
console errors. Shots `review/shots/` (`tiers_sheet.png`, `clips_sheet.png`; `ab_viewer_sheet.png` = old export vs
the texture fix at the review screenshot's framing).

In game (texture fix, `review/ingame/`): a private hard-linked asset root under `output/` with only the robot GLB and
an `actors.yml` carrying this binding as new files (deleted afterwards; nothing written to `assets_dev`), `debug.actor_spawn_id`
388 on Emerald Island in daylight and 388 / 389 / 390 in The Lincoln (`7d23.blv`, dim; its sprites include m387–m389,
which B/C `scale_reference` needs): all three load and render, tints and green optics as intended
(`ingame_sheet.png`). Metallic-cap A/B in the same captures (see Textures).

## Rebuild

`rig_robot.py` → `anim_robot.py` → `uv_export.py` (then the texture fix: copy `work/uv_master.blend` to
`work/uv_master_smartuv.blend` once and run `uv_hardsurface.py`) → `dump_uv3d.py` → (retexture `retexture_v2uv` with
`texturing/robot_neutral_v2uv.glb`) → `bake_ao.py` → `compose_v2.py` → (clip changes: `anim_robot.py work/uv_master.blend work/uv_master.blend`) →
`build_source.sh TOKEN` → `import_source.py` (REA_GLB=…/work/mm7_m386_source.glb REA_NODE=Robot) → `dump_mesh.py` →
`robot_groups.py` → `REA_PROTECT_RATIO=0.5 REA_GROUP_RATIOS=1:0.3,2:0.45,3:0.35 run_ladder.sh C 0.45,0.41,0.37,0.35,0.33 TOKEN` →
`build_export.sh TOKEN` → `viewer_manifest.py`. Blender scripts run through `tools/run_creature_blender.sh --token`.

## Install (installed 2026-10-21)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m386_v2_claude/export/mm7_m386.glb --world mm7
```

```yaml
# Robot m386 v2: all-metal walker on four sliding spikes (Fly N), gun-shot attack, collapses to a corpse;
# tiers = original descriptor tints as ramps.
- descriptor: Robot A
  model: worlds/mm7/models/mm7_m386.glb
  scale: 200
  yaw_offset: -1.570796327
  skin: m386_a
  animation:
    cast: Attack
    run: Walking
    stride_length: 0.327
    run_stride_length: 0.327
    upper_body_root: Neck1
    sockets:
      eye_left: Socket_Eye
      muzzle: Socket_Muzzle
    eye_color: [90, 255, 60]
    events:
      attack_melee:
        impact: 0.44
      attack_ranged:
        impact: 0.44
        glow:
        - muzzle
        release: muzzle
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
# Robot B / Robot C: same entry with skin m386_b / m386_c and `scale_reference: Robot A`.
```

## For review

- Texture fix: `review/shots/ab_viewer_sheet.png` (viewer, old vs new) and `review/ingame/ingame_sheet.png`. Sharper
  sleeves, gun housing, chassis panels and spikes; real metal sheen but deliberately capped (metallic 0.3) because
  the engine darkens fuller metal outdoors and indoors. The spotted rusty brass on head, neck and tail is Meshy's
  paint following the HD masters, not filtering noise; a cleaner brass would need new masters or a repaint.
- The viewer's studio reflections flatter metal more than the game's sky reflection does.
- File size 7.9 MB (was 5.7): the sharper Meshy base colour compresses worse as PNG.
- The all-metal reading of the head, neck and tail (`review/shots/`, viewer).
- The gun: stowed muzzle-down while walking, swinging level for the shot (Attack in the viewer).
- The walk: spikes slide out of their sleeves by up to 9 cm in the front legs' reach.
- The tinted tiers (Sentinel teal-grey, Assassin ochre), as the original engine's tint multiply.
- `upper_body_root: Neck1` is kept from v1: the gun hangs from Body, so an engine upper-body blend over a walk does
  not tilt the gun; the Attack clip itself carries the gun swing.

## Gait pass: Walk2 and Run2 (2026-10-21)

The [creature post-process](../CREATURE_POSTPROCESS.md) flagged the walk: Walking covers 0.327 m per 1.25 s
(0.26 m/s) and was bound as walk and run, so in game it played 2.3-3.8x wandering and 4.5-7.7x chasing (the tiers
move 0.59-1.00 m/s wandering and twice that chasing, in model units). `gait_gate.py` asks for authored speeds of
0.67-0.78 (walk) and 1.33-1.57 (run). Two new clips, the old ones kept:

| clip | length | stride | speed | gait |
|---|---:|---:|---:|---|
| Walk2 | 0.75 s (18 f) | 0.54 m | 0.72 m/s | four-beat lateral-sequence walk (RL, FL, RR, FR), duty 0.65: two or three spikes planted at all times; chassis 3 cm high, rolls away from the swinging side, dips on each footfall; head held level, neck and tail counter-sway |
| Run2 | 0.583 s (14 f) | 0.85 m | 1.46 m/s | trotting run, diagonal pairs, duty 0.36 with two suspensions per cycle; spikes lift 8 cm; chassis 4 cm high and nose down, sinks at mid-stance; neck stretched forward with the head level, tail lowered and whipping, gun tucked higher |

- `scripts/anim_gait2.py` (on `work/uv_master.blend`, writes `work/gait2.blend` and the donor
  `work/gait2_donor.glb`) keys only the new clips, with the walk's sleeve-aim and spike-slide legs. The spikes reach
  0.30-0.40 m from their hips (slide -1.2 ... +9 cm), so the longer steps are centred near the hips (front feet 5 cm,
  run 8 cm ahead of them) instead of the rest pose's forward splay; the script reports any stance foothold outside the
  slide range (none).
- `scripts/add_clips.py` appends them by node name to the installed export (rest transforms compared first; the
  donor's Walking matches the installed one exactly), so LODs, variants and the other clips are untouched. Pre-pass
  export: `work/mm7_m386_pre_gait2.glb` (sha256 `2d23242c…`); new export sha256 `0a4d2fd7…`.
- Gate: `gait_gate.py --world mm7 --model mm7_m386.glb --candidate work/gait2_cand/mm7_m386.glb --set walking=Walk2
  --set run=Run2 --set stride_length=0.54 --set run_stride_length=0.85` passed: measured 0.528 / 0.836 (spike vertices,
  no foot joints, so untrusted but within 10 %), rates A 1.39 / 1.37, B 1.07 / 1.06, C 0.82 / 0.81, floor ok.
  `check_winding.py` 0 inverted; `lod_check.py` (`REA_NODE=Robot`): no stretched face in the new clips at any LOD,
  lowest point -1.6 mm (LOD1). Viewer check 27 switches, no errors.
- Review: `review/playback/Walking-*.webm`, `Walk2-*`, `Run2-*` (1x and 0.5x); side phases
  `review/shots/g2_{Walking,Walk2,Run2}_0..5.png`, quarter `review/shots/g2q_*.png`.
- Installed with `tools/install_model.py export/mm7_m386.glb --world mm7`. Binding (applied by the coordinator):
  `clips.walking: Walk2`, `animation.run: Run2`, `stride_length: 0.54`, `run_stride_length: 0.85`.

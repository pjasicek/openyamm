# MM7 Sea Monster (m394): Giant Shark / Piranha Shark / Dragon Shark — Claude quadruped route, batch L

MM7 batch L model 2 ([BATCH_L.md](../mm7_batches/BATCH_L.md)). Monsters 394 Giant Shark, 395 Piranha Shark, 396 Dragon
Shark (sprite groups m395/m396/m397, palettes 395/396/397). **Installed 2026-10-21** (the user asked for it after the
batch; the batch itself stopped at exports): the install command and `actors.yml` binding are below. Meshy: **15 of 100
credits** (Smart Topology 5, retexture 10). User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m394_claude/review/viewer/`) ·
[HD masters](references_hd/selected_views_review.png) · [clay clips](review/clips_v1_three_quarter.png),
[side](review/clips_v1_left.png), [front](review/clips_v1_front.png)

| Item | Value |
|---|---|
| Runtime export | `export/mm7_m394.glb`: one skinned mesh `M394`, LODs **6,291** / 3,144 / 1,121 / 363 tris (LOD0 halved on the textured master by `halve_lod0.py` (user, 2026-10-20: "reduce tris now"; collapse before the armature, UV-seam vertices weighted 0.8, small pieces kept whole, head and jaw protected; the teeth are kept)) + shadow LODs, 3 tier variants `m394_a/b/c` sharing every image |
| Portable / editable | `export/mm7_m394_lod0.glb`; `work/anim_v2u.blend` (rig, clips, Meshy UVs); `work/anim_v1.blend` (clip source) |
| Textures | 2K base colour, 1K normal / ORM / region mask (one region: the blue skin), `m394_ramps.json`, class map |
| Skeleton | 12 bones + `Socket_Mouth`: Spine1 (root, mid-body), Spine2, Head, Jaw, Tail1–6 (Tail6 carries the caudal fin), Fin_L / Fin_R |
| Clips (30 fps) | Standing 1.0 s, Walking 1.267 s (38 frames), Attack 1.267 s (impact 0.6 s), Hit 0.867 s, Death 1.5 s, Dead 1.0 s |

## Habitat decision (water)

MM7's sharks live on the underwater map **The Shoals** (`7out15.odm`, map_stats flag `UNDERWATER`, monsters
"Sea Monster") and their monster data has **Fly = Y**: underwater they move in 3D like flyers; there is no surface to
keep them on. So unlike the MM6 sea serpent (cut at the waterline), this is the **whole shark**, swimming in place as
a flyer: the origin is the swimming shark's lowest rest point (pectoral fin tips) with **no hover lift**
(quadruped playbook, flyers), the swimming clips stay within 2 cm of it, and the corpse rests on z = 0 like the
native belly-up corpse. The body and tail carry a lateral travelling swim wave; no legs, no floor contact.

## Model and rig

- HD masters (Codex) from the native views/palettes/actions; the run-1 primary needed one correction (tail margin,
  scar-like streaks). The left side view shows six gill slits instead of five (kept; texture only).
- Smart Topology 15k of `00_three_quarter.png`: a closed shark shell, 36 separate teeth and a gum piece, four flakes
  plugging a hole on the back. `step1b_shark.py`: removes the 18 cm lateral S-bend of the return (centreline shear),
  closes the small holes, and closes the mouth slit's two open loops with fans recessed 7 cm into the head (an
  opening jaw shows a throat, not a hole into the body).
- Facing −Y, a +X rotation pitches the nose down (rat pitfall): the first attack reared nose-down; fixed in
  `anim_shark.py` (+ pitch = nose up) and checked on renders.
- `measure_shark.py` (pectoral roots/tips, mouth corner and lip line) and `rig_shark.py`: centreline bones at fixed
  length fractions (trimmed slab centroids), heat weights, the lower jaw set by geometry (in front of the hinge, below
  the lip line, feathered 1.5 cm), each tooth wholly on Head or Jaw (17 on the jaw).

## Clips (`anim_shark.py`, procedural, after the native m394 actions)

| Clip | Motion |
|---|---|
| Standing | hovering: slow tail beat, slight roll, jaw breathing (native standing/fidget loop, front view opens the jaw); also the fidget |
| Walking | swimming: lateral travelling wave growing to the tail, head counter-sway, fin trim; 38 frames = the native 1.25 s cycle |
| Attack | rears nose-up with the jaws wide (native `m394ad/ae`), lunges forward and snaps shut at **0.6 s** (`af`: jaws at the camera), dives (`ag..ai`) and levels out (`aj`) |
| Hit | twists onto its side (belly flash) and curls, recovers (`m394na..nd`) |
| Death | rolls belly-up with the jaws agape, curls, sinks to the floor and settles on its back and flank (-140°: fully belly-up propped it on the dorsal fin) |
| Dead | the Death end held (native corpse `m394xa`, belly up) |

## Textures and tiers

Meshy retexture with **Meshy's own UVs** (`enable_original_uv: false`) copied back face by face (`transfer_uv.py`;
20 degenerate faces fewer in the return, 2 faces matched > 5 mm): a Smart UV Project of this mesh gave 1,548 islands
(732 single faces). Compose (`compose_m394.py`): AO grade 0.35. One region, **the blue skin** (the package's palette
entries 80–177): hue 165–250° or dark non-red texels of the shell; the white belly, teeth, gums/mouth cavity and eyes
keep their colours in every tier. Ramps from each palette's skin pixels at 1.3× the native brightness; A keeps the
texture's chroma. Native skin medians: A (68, 98, 108) teal-blue, B (94, 83, 114) lavender, C (120, 66, 66) red.

## Gates

- Halved LOD0 (`halve_lod0.py`, 2026-10-20), edge stretch p99: Standing 1.29, Walking 1.20, Attack 2.16, Hit 1.75, Death
  2.01. Viewer, winding and textured renders rechecked.
- Floor: swimming clips' lowest point −2.0 … +2.1 cm against the origin; Attack rises up to 19 cm; the corpse 0.0 cm.
- Edge stretch p99 / max: Standing 1.34 / 1.82, Walking 1.23 / 1.55, Attack 2.38 / 4.13, Hit 1.90 / 3.06, Death
  2.20 / 3.75 (the maxima at the mouth corners when the jaw opens wide).
- Teeth (`reduce_teeth.py`): the 36 teeth and the gum were 3,975 of 15,369 LOD0 triangles (~100 per 4 cm tooth, micro
  triangles); collapse-decimated to 1,191 with UVs and rigid weights kept; open-jaw close-ups in `work/r_close/`.
- `check_winding.py`: 0 inverted closed parts. Viewer: 3 tiers × 6 clips, no console errors. Textured EEVEE frames
  of all tiers, the attack and the death inspected (`work/r_glb/`). Not checked in game (optional for batch L).

## Installed (2026-10-21, user request after the batch)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m394_claude/export/mm7_m394.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (repeat for `Sea Monster B` / `m394_b` and `Sea Monster C` /
`m394_c`; all tiers draw at frame scale 1.0):

```yaml
# MM7 Sea Monster m394 (394-396): swimming shark (underwater flyer, origin at its lowest rest point), bite lunge.
- descriptor: Sea Monster A
  model: worlds/mm7/models/mm7_m394.glb
  scale: 125.85
  yaw_offset: -1.570796327
  skin: m394_a
  animation:
    run: Walking
    stride_length: 2.0
    run_stride_length: 2.0
    upper_body_root: Spine2
    look:
      nodes: [Spine2, Head]
      max_yaw_degrees: 30
      max_pitch_degrees: 20
    sockets:
      mouth: Socket_Mouth
    events:
      attack_melee: {impact: 0.6}
      attack_ranged: {impact: 0.6, release: mouth}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Standing
```

Scale by side-silhouette area (flyer rule, `silhouette_scale.py`): native profile `m394sa2` 7,705 px vs the model's
Standing side view 0.486 m² → **125.85** (length-based 112.5, height-based 130.0: the Meshy fins are a little larger
than the sprite's). The shark is then 252 units long and 89 high (descriptor height 120, radius 50). Speed 200 at
stride 2.0 m plays the swim at the native 1.25 s cycle; the run threshold (302) is never reached.

## For the user to review

- LOD0 is 12.6k triangles (Smart Topology's shell unreduced; teeth reduced); a texture-aware reduction pass (as for
  batch E) could cut the shell further.
- Colours read lighter and more saturated than the dark native sprite (ramp gain 1.3 on the sprite's shaded pixels).
- Motion is procedural and an interpretation of the native frames.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -2.7; living lowest at -2.7 (suggested hover 0.021724).
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m394.glb export/mm7_m394.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --hover 0.021724 Death Dead --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m394.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

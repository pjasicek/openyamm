# Xeen Carnage Hand (Xeen Construct C, monster 11602), 2026-11-20

Lane S project (session `xeen-s3`, identity `xeen:hand`; stage 1-2 by `xeen-s3`, the rest by the sub-agent
`xeen-s3-hand`). Row: `magic_constructs` tier C in `assets_dev/worlds/xeen/source/monsters.yml`, level 35, melee, bonus
BrkArmor, no missile, Fly Y. Clouds of Xeen image 49 (`sprites/xeen/049.mon`, `049.att`). Built with the
[quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) (floating heads, flyers, rigid sections),
[HD masters](../CLAUDE_HD_MASTER_REFERENCES.md), [creature textures](../CLAUDE_CREATURE_TEXTURES.md), the
[texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [LOD playbook](../LOD_PLAYBOOK.md).

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer, in textured renders and in
game (static model spawns in XD-21). The binding is **not** merged (the lane parent owns `actors.yml`): the ready block
is [integration/actors.yml](integration/actors.yml). Not accepted by the user. **Meshy: 15 of 30 credits.**

## Deliverables

| Item | Value |
|---|---|
| Installed | `assets_source/worlds/xeen/models/xeen_hand.glb` = `export/xeen_hand.glb` (sha256 `ab619ab2…`); cooked runtime copy in `assets_dev/worlds/xeen/models/` (`8e4778b8…`) |
| Binding block | `integration/actors.yml` (descriptor `Xeen Construct C`, skin `hand_a`, scale 143, `cast: Attack`) |
| Master | `work/anim_v1.blend` (rig `Hand_Rig`, mesh `Hand`, keyed clips); `work/anim_base.blend` = the locked UV layout; `work/rig_v1.blend`, `work/clean_v2.blend` (face attribute `part`) |
| Masters (Codex) | `references_hd/00`-`04` (from stage 2, unchanged) |
| Textures | `textures/hand_basecolor_graded.png` (2K), `hand_normal_1k.png`, `hand_mr_1k.png` (R baked AO, G roughness, B 0), `hand_region_mask.png` (R skin, G maw, B fangs), `hand_ramps.json`, `hand_material_classes.png` (1 skin, 7 mouth, 5 fangs), `hand_ao_2k.png` |
| Review | `review/textured_sheet.png` (EEVEE, party eye height), `review/clips_front.png`, `review/clips_side.png` (clay clip sheets), `review/viewer_shots.png`, `review/ingame/sheet.png`, `review/lips_sheet.png` (lid opening 0/20/40/55 deg), `review/stress_sheet.png` (weights, fist, spread), `review/fingers_sheet.png`, `review/clean2_sheet.png`, `review/raw_sheet.png`, `review/mouth_sheet.png` (the Meshy lips), `review/texture_quality.json` |
| Viewer | `review/viewer/` (one skin, ramp baked for three.js) |

## Native study

- A huge disembodied **right hand** (thumb at image right when the palm faces the viewer), no wrist: it ends just behind
  the heel of the palm. Warm tan skin (the Flying Feet's palette), heavy knuckles, thick sausage fingers.
- A fanged **mouth in the palm**: a ring of grey-silver fangs (long canines near the corners) round a dark red gullet
  with a red tongue; it shows only when the hand opens.
- Idle (8 frames): fist (0, 4), half open (1, 3, 5, 7: the mouth showing), spread (2, 6). Attack: fist, spread with
  the mouth, the hand lunges with the fingers splayed and the maw gaping (the bite), palm down clawing.
- Size: idle hand area 1408 px (fist) / 1741 (half) / 2572 (spread), mean 1865.5 px; the drop shadow excluded.

## Mesh (`scripts/prep.py`, `frame.py`, `clean.py`)

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter`): 15,810 triangles, the hand plus 9 thin rod fangs.
Scaled to 0.50 m (heel to the highest fingertip), forward -Y (the palm), thumb +X. **The body came back
double-walled**: an inner copy of the whole skin (6,723 triangles, 48 % of the area) joined to the outer one through the
slit of the soft lumpy lips. `clean.py` deletes the lips (an ellipse of 0.105 x 0.062 m round the mouth in the palm
plane) and the rod fangs; the outer skin is then its own connected component and is kept alone (the visibility test of
the feet would also have cut holes into the deep finger crevices). Small holes filled, the skin collapse-decimated
(0.62: 4,105 triangles), folds and pinched spikes relaxed (94 spike vertices), and the mouth hand-built in the palm
frame (`work/mouth.json`: O, n out of the palm, U along the slit, V up the palm):

| Part | Triangles | What |
|---|---|---|
| 0 skin | 4,105 | Meshy hand |
| 1 rim | 94 | radial quad strip from the smoothed cut to a clean elliptical aperture (a 0.075, b 0.045) |
| 2 gullet | 423 | funnel 8.5 cm into the palm (0.19 m thick there) |
| 3 tongue | 100 | low ellipsoid at the bottom |
| 4 fangs | 336 | 14 cones on the aperture rim pointing inward, 10 % tilted out; canines 2.4-3.2 cm near the corners |
| 5 / 6 lip lids | 374 / 374 | closed shells (domed outer face, rolled slit edge, inner face) that meet at the slit and cover the aperture |

**5,806 triangles** (LOD0 budget: a deforming hand; the guidelines' 5-8k for clothed humanoids). The lids turn about a
hinge axis along U, 3.5 cm behind the palm: opening slides each one up (down) under the palm skin like an eyelid and
bares the fang ring (55 deg = fully open, `review/lips_sheet.png`); closed, they make the lipped slit of the masters.

## Rig (`scripts/finger_axes.py`, `rig.py`, `handpose.py`)

`Root` (hover root at the hand's centre) > `Palm` (palm, back, rim, gullet, tongue, fangs: rigid) > per finger
`<F>_1..3` (F = Thumb, Index, Middle, Ring, Pinky) and `LipUpper` / `LipLower` (rigid lids). Finger centrelines from
iso-geodesic contour centres from each tip (`work/fingers.json`); knuckles 2.5 cm proximal of the web (the midpoint of the
shortest skin path between neighbouring tips), middle and end joints at 55 % / 27 % of that arc. The thumb's contour
merges into its ball past 0.26 m: its joints come from the line's own narrowing (end joint 0.10, knuckle 0.20) and a
carpometacarpal joint placed in the ball of the thumb. Skin weights by geodesic distance from the tip along the nearest
finger (1.2 cm blends at the joints, 4 cm ramp into the palm at the knuckle), three smoothing passes; 0 unweighted.
Flexion about each finger's curl-plane axis, spread about the palm normal (`handpose.hand`).

## Clips (`scripts/anim.py`, procedural, 30 fps)

Base orientation: fingers leaned 25 deg to the image left, the palm tilted 10 deg up to the party (native frames: a
wide, fingers-left hand). Openness 0 = fist, 0.5 = the modelled claw, 1 = spread (fingers back 30/30/20 deg, fanned
14 deg); the lids follow the openness (0 below 0.2, 55 deg at 0.7).

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 2.4 s loop | hover bob; two open-close cycles fist -> half -> spread -> half (fingers in a small wave, pinky leading), the mouth bared whenever open | |
| Walking | 1.6 s loop | leaned 14 deg toward the travel direction, half open, crawling finger wave, lips parted 10-26 deg | |
| Running | 1.2 s loop | leaned 22 deg, faster wave | |
| Attack | 1.0 s | draws back and up spreading and gaping (att 1, 0.24 s), lunges 9 cm (att 2, 0.36 s) and bites: the lids snap shut and the fingers clamp into a claw (att 3), then back into the fist | **impact 0.45 s** (the bite) |
| Hit | 0.5 s | knocked back 7 cm with a twist, the fingers spasm open, the mouth gasps | |
| Death | 1.5 s | spasm (spread, gaping), clench, rolls palm down and drops: lies on its curled fingertips and heel | |
| Dead | 1.0 s | Death's last pose | |
| Fidget | 2.0 s | opens to half, drums the fingers pinky to index twice, back into the fist | |

One-shot clips start and end on Standing frame 0 (the fist). No cast clip (`cast: Attack`), no missile
(`attack_ranged: Attack`).

### Gates

- **Flyer rule** (`floor_fix`-equivalent in `anim.py`): one hover lift 0.0265 m (3.8 units) baked into every living
  clip (lowest living point = the Running lean); the Death eases it out in 0.5 s and grounds the corpse exactly.
  Floor audit (`scripts/floor_check.py` = `floor_audit.audit` with this binding on the export; the row says Fly Y):
  **flier, standing 1.8..6.0, walking 1.6..7.4 units, living lowest 0.0, corpse 0.0, no problems.**
- Motion (`scripts/clip_gates.py export/xeen_hand.glb 143`, largest per-frame vertex step / second difference):

  | Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
  |---|---|---|---|---|
  | Standing | 10.65 | 5.88 | 0.00 | +1.79 |
  | Walking | 1.51 | 0.27 | 0.00 | +1.59 |
  | Running | 2.56 | 0.56 | 0.00 | 0.00 |
  | Attack | 21.34 | 19.82 | (one-shot) | +2.14 |
  | Hit | 20.87 | 19.33 | | +4.25 |
  | Death | 20.30 | 19.39 | | 0.00 |
  | Fidget | 8.13 | 6.33 | | +4.10 |

  The large steps are fingertips on 0.25-0.4 m arcs: the bite clamp (0.36-0.45 s), the Hit spasm and the death spasm
  and clench (all slowed once from 39 cm). Loops close exactly.
- **Contacts**: the fist (Standing frame 0, every one-shot's first and last frame) presses the finger pads into the
  palm, the closed lids and the neighbouring fingers (about 250 overlapping triangle pairs between the distal phalanges
  and the rest; 0 in Walking and Running). It is enclosed by the fist: no poke-through from any side in the clay
  sheets, the textured fist close-up or the viewer. The lids never cross the fangs (the fangs sit under the lid shells;
  only the canine tips may touch the lid's inner face at the corners). Winding: 0 inverted closed parts.

## Textures

UVs `scripts/uv.py` (`uv_atlas.unwrap` defaults, lids 1.3x denser): PartUV charts (41 -> 35 after the seam pass),
sparrow pack. Measured on the runtime GLB (`texture_quality.py`): **atlas 72.1 %, density p10/p50/p90 1144/1246/1389
(spread 1.21), 37 islands, fragments 0.0 %, stretch p90 1.13**; per bone density 1102-1246. Meshy `retexture_v1`
(meshy-7, 4K, PBR, original UVs, masters 01/03/02/04) returned the same layout.

`scripts/compose.py`: 4K -> 2K once. Skin and lids keep the Meshy paint (the lids came back as red lips); skin x1.15
(paint median 170, 112, 71 on the sprite's shaded median 180, 112, 68, toward the Flying Feet's accepted skin of the same
palette). The parts the closed lids hide are painted procedurally: rim (skin blending into dark red gum at the aperture),
gullet (gum to nearly black 8 cm down, Meshy's luminance detail x0.8..1.2), tongue (red-pink by facing), fangs
(grey-silver, darker root to light tip; flat normal). Grade `--fine 1.0 --local 0.0 --ao-strength 0.5 --contrast 1.06
--saturation 1.15` (local 0, the Flying Feet's lesson on tight sparrow gutters); procedural texels restored after it
(`keep_procedural.py`); `gutter_fill.py` last on every map. Roughness: skin 0.45-0.9 (Meshy, median 0.77), fangs 0.35,
gullet and tongue 0.4; specular 0, metallic 0.

Skin `hand_a` (`textures/hand_ramps.json`, tier-A fit error mean/p95 in 8-bit levels): skin 1.88/5.3, maw 5.82/16.7,
fangs 5.2/18.8 (the maw and fangs carry designed gradients that one luminance ramp flattens a little). The mask covers
the main colour (R skin), so later Xeen tiers on this model are ramp numbers only.

## Scale, LODs

Scale **143** from the silhouette area (playbook flyers): native idle hand area 1865.5 px x (1.34 units/px)² (the Xeen
witch calibration) against the model's mean front silhouette over Standing, 0.163 m² (`scripts/front_area.py`,
`front_area_px.py`; width alone 152, height 129). The 0.5 m hand is about 72 units tall, the spread hand about 82 wide.

LODs **5,806 / 2,902 / 1,032 / 333** (LOD1 `build_actor_lods.py`; LOD2/3 the `repair.py` ladder in the project copy
`lodrepair/`, first step **r25_12** accepted: LOD2 outline 1.8 %, colour 5.8; LOD3 3.5 %, 7.7); `verify_far_only` OK;
shadow LODs tucked (max push 8.7 / 8.8 / 15 mm). `lodrepair/work/xeen_hand/r25_12.built.glb` and `bake_r25_12/` are kept
for map-only reruns. The project copy of `repair.py` takes `--source` as the installed stand-in when no installed GLB
exists yet (first install).

## Checks

- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_hand_claude check`: 8 clips
  switched, no console errors (served by `python3 -m http.server 8912 --bind 127.0.0.1` from the repo root);
  `review/viewer_shots.png` (fist, open, quarter, gape, bite, hit, dead, walk).
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 1.23 model m = 176 units, 2.6 m away: fist, open,
  quarter, side, the gape, the bite, hit, corpse, walk, mouth and fist close-ups, back).
- In game: `review/ingame/sheet.png` (XD-21, `build-xeen/game/openyamm` of 2026-11-20 17:10, `model spawn` of the
  installed GLB at scale 143 yaw pi: Standing open, Attack gape/bite, Dead, forced LOD 2 and 3); `review/ingame/tour.yml`
  has the command. Exit 0, no load errors.

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture | 5 | `01a1f9aa-f94d-73cd-88d6-d0f3e7fd7a90` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs | 10 | `01a1f9bf-6950-70e3-9922-dd0295259e62` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_hand_claude
TOK=$TOK scripts/step.sh prep.py; TOK=$TOK scripts/step.sh frame.py; TOK=$TOK scripts/step.sh clean.py
TOK=$TOK scripts/step.sh finger_axes.py; TOK=$TOK scripts/step.sh rig.py
# uv.py refuses to run once texturing/hand_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh anim.py
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # only after a layout change
TOK=$TOK scripts/build_runtime.sh [--install]   # compose, grade, gutter fill, ramps, export, LODs, skin, far LODs
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_hand.glb 143; python3 scripts/floor_check.py
TOK=$TOK scripts/step.sh render_textured.py; TOK=$TOK scripts/step.sh clip_sheet.py 8 front && python3 scripts/sheet_join.py clips_front.png
```

Checks: `views.py <blend> <prefix> [parts] [close] [nolids]`, `mouth_views.py <blend> <deg>...`, `stress.py`,
`finger_view.py`, `fist_probe.py`, `scripts/grid.py` (sheets).

## Known limits

- The fist presses the finger pads into the palm and the closed lids (hidden inside the fist; see Gates).
- The rim strip between the cut and the aperture shows faint radial shading streaks in clay renders (thin quads on the
  smoothed cut); under the texture they read as gum folds.
- Fingertip snaps (bite clamp, hit and death spasms) move up to 21 cm a frame on a 0.5 m hand (about 30 units): fast
  by design, not a pop; slow them in `anim.py` (`ATTACK`, `HIT`, `DEATH` keys) if they read as jerky in game.
- The skin paint is Meshy's (wrinkles, knuckles); no nails, as the sprite. The masters' finger creases are kept.
- Standing hovers 1.8 units at its lowest (the Running lean sets the shared flyer lift).
- Seen in game only as debug-spawned models (no binding merged yet); not accepted by the user.

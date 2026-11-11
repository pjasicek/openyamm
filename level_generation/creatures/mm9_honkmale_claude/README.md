# MM9 Honk male (mm9_honkm) — 3D actor, 2026-10-31

Monster rows Honk (`MONSTERS.txt` 216, `MM9 Honk A`, skin HONKM2, bareheaded), Elder Honk (187, `MM9 Honk B`, HONKM3, goose hat) and Honk Seer
(188, `MM9 Honk C`, HONKLEADER, elder hat), `HONKMALE.abc`. Built on the approved MM9 humanoid route ([brief](../claude_shared/MM9_HUMANOID_BRIEF.md)):
MM9 skeleton and clips, never Mixamo. Sister body: [`../mm9_honkfemale_claude/`](../mm9_honkfemale_claude/README.md). History of the day session: `HANDOFF.md`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_honkm.glb`, sha256 `91d439850a90b2...`, identical to `v2/export/mm9_honkm.glb` |
| Hats | `mm9_honkhat.glb` (1,860 tris), `mm9_elderhonkhat.glb` (1,800 tris), from `object.lto` `HonkHat.abc`, `ElderHonkHat.abc`; on `Bip01 Head` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `scripts/honk_binding.yml`: scale 100, stride 1.2 / 3.0, impacts 0.35 / 0.341 / 0.366, release socket `Bip01 L Finger11` |
| Triangles LOD0/1/2/3 | 8,054 / 4,025 / 1,447 / 481 |
| Skeleton | MM9's, plus 15 finger bones per side (`Thumb`, `Index`, `Middle`, `Ring`, `Pinky`) on MPFB hands; robe on MM9's `X*` chains |
| Clips | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Cast `Hattack2` (my choice: MM9 has no cast clip here), Hit `wince1`, Death `die1`, Dead |
| Textures | body 2K colour, normal and ORM 1K; head + hands set the same; one head base colour per tier; region mask + ramps for the Seer's blue |
| Meshy credits | **35** on this body, day session (Smart Topology 5, body retexture 10, head retexture 10, hats 5 + 5). Night pass 0 here. Pair total 70: 60 day + 10 night, on the female; second pass 0 |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_honkmale_claude/review/viewer/ revision `v26-20261031`, tiers `honk_a`, `honk_b`, `honk_c` |

## Route

0. HD masters from the MM9 model and skin, `references_hd/`, head masters `v2/references_head/`, hat references `hats/references/`.
1. Meshy Smart Topology, fit to the MM9 bind pose, five-finger hand graft, head split, retextures at 4K on `uv_atlas.py` UVs (day session; see `HANDOFF.md`).
2. Night pass, master chain `v2/scripts/master_v3.sh`: `fix_v1` -> `sleeve_lining.py near=0.22` -> `sleeves_v3` -> `robe_lining.py` -> `robe_v3` -> `medallion.py` -> `medal_v3`.
3. Runtime: `BLEND=v2/work/medal_v3.blend v2/scripts/build_runtime_v2.sh honkm HonkM v2/scripts/roles_honkm.json`; `clip_relax.py` runs after the floor pass, `mirror_glb.py` last.

**Never rerun `texpass_uv.py` or `texpass_head_uv.py`**: the paid paints belong to `work/uv_tp.blend` and `v2/work/head_uv.blend`.

## Night pass 2026-10-30: what was wrong and what changed

Close-ups and intersection tests found defects the earlier stills and gates had missed.

| Found | Cause | Fix |
|---|---|---|
| Boots through the robe in Running (17 of 21 frames L, 6 R) | Boot shafts reached 0.41 m, and they carried robe weights | Boots weighted to Calf, Foot, Toe0 only; shafts cut with a true plane at 0.28 m (`robe_lining.py`) |
| Boots through the robe in Death and Dead (every Dead frame), floor-side robe folded up through the legs | `floor_fix.py --lift-joints Death Dead` bent the strips | The lift is removed. Corpse 1.2 cm higher, robe stays a round tube as in MM9 |
| Robe one-sided: from below and from a corpse's feet only a jagged inner plate | Meshy cloth, back faces culled | Dark lining with a rim at the hem and a cap (MM9 closes the tube with a dark underside; final form in the second pass); inner plate and folded hem lip deleted |
| Skin-coloured shards and a notch at every cuff | Meshy's forearm remnants inside the sleeve; lining stopped short | Remnants deleted (116 faces), lining to 0.22 m from the wrist. See-through worst 128 -> 26 px of 25,600. A first try at 0.34 m poked through at the elbow crease, and a cap at 0.94 m at the waist crease |
| **Elder and Seer faces: doubled irises, a third eye on the nose bridge, a seam down the nose** | Codex repaints blended from several views (`head_tier_project.py`) | `head_tier_repair.py`: central face rebuilt from tier A's clean texels with one gain per channel from the tier's own skin, brows and moustache greyed on the Elder, irises recoloured. Projected wrinkles, hair and beard kept outside that zone |
| Medallion: heap of plates flying apart in Hit, under black and white flecks | Meshy | Clean domed disc (`medallion.py`), art from the head master painted on a free atlas circle (`medallion_paint.py`). The master's frame cuts the disc, so its lower half is the upper half mirrored; the old medallion painted on the chest went too |
| Collar chain black and white, flesh blotches | Meshy paint. MM9's chain is thin and silver, so not a missing gold trim | Silver at low contrast, blotches back to linen with real weave |
| Neck and head folds in Hit (37 and 40 faces) and Death | MM9's head bend on our deeper head | Head 30 % towards Standing in Hit, Death, Dead (`clip_relax.py`): 19 and 17 |

Also: feet turned 40 deg along the leg from Death 0.7 to 1.2 s so they lie inside the hem ring (`clip_relax.py`), buckle shards deleted.

**Handedness:** `mirror_glb.py` last, as on the Imp: `L Hand` was at x -27.6 in the raw ABC with the nose at +Z, so converted GLBs are the mirror of the game's actor. Inferred from coordinates and bone names, not compared with MM9 footage. `v2/work/mm9_honkm_floor1.glb` is the unmirrored build. MM9 renders in the sheets are unmirrored. Egg release from `Bip01 L Finger11`, the true left hand after mirroring.

## Second pass 2026-10-31 (coordinator's review)

| Item | Result |
|---|---|
| Dark cap with radial streaks from a corpse's feet | The lining took a belt texel; now one plain dark painted patch (`medallion_paint.py dark_patch=`, roughness 1, flat normal). The cap is planar with its own ring, joined to the lining by a strip (`robe_lining.py`). Lining and cap end at 0.60 m, 12 mm behind the wall: at 0.74 m the top showed as a black wedge through the hip pleat in Standing (see-through 329 px in Walking), and at 4 mm the lining came through creases in the corpse as dark dashes. First tries, rejected on the sheets: flat faces on the old ring (bright slash), a planar cap without the strip (black disc in bright spikes). **Left:** a small sliver at the hem edge in `sheet_joints.png` j5 |
| Elder face reddish against grey hair | Measured on the face against HONKM3: R/G 1.65 -> **1.51** (MM9 1.39), B/G 0.755 -> 0.747 (MM9 0.746) (`head_tier_repair.py --grade 0.92,1.03,0.995`). A gain on skin only. Closer, not equal |
| Body atlas 50.1 %, head fragments 4.5 % | **Unchanged, as allowed.** Fixing them needs new UVs, so a repaint |
| Egg release | At the event (AttackRanged 0.341 s) the socket `Bip01 L Finger11` is 0.5 cm from the nearest vertex, a fingertip of the raised hand: `review/sheet_impact.png`. Not caught in flight in a slow-motion in-game capture (`review/ingame_v3/egg/`, 70 frames at time scale 0.3): the Honks closed to melee |

`arm_hand_gate.py --outer-only` now skips faces with no UV area (linings, rims, cap): one face of the cap strip read a hand hanging beside the robe as 5.8 cm inside (Standing, 41 frames). The numbers below are with the filter.

## Checks (final GLB)

| Gate | Result |
|---|---|
| `check_winding.py` | 0 inverted closed parts (body and both hats) |
| `flat_shading_check.py` | 0.02 / 0.00 |
| `scripts/robe_gate.py` (48 fps, edge against triangle) | **Boots through the outer robe wall: 0 frames in all ten clips**, including Walking, Running, Death, Dead. Inner shell: 1 edge at about 0.93 m in up to 4 frames |
| `sleeve_gate.py` (24 fps, four views) | Forearm poke 0 frames; see-through worst 26 px (Death L q34), 18 above34, 10 elsewhere, of 160 x 160 |
| `arm_hand_gate.py --outer-only --exact` | Fidget L 5.8 cm (8 frames over 1 cm), **Hit L 5.8 cm (11)**, Death L 3.5 (8), R 4.5 (18), all others 0. Finger stretch max 3.67 |
| `jitter_gate.py` against MM9's clips | 0 fails |
| `detached_parts_audit.py` | **2 flagged: both boots**, by design: they hang free inside the tube, as MM9's foot mesh does; there is no thigh geometry |
| `floor_audit.py` | OK on all three: stand 0, walk -0.4..+0.2, living -0.9, dead 0 |
| `mm9_actor_models_build_every_binding` | 101 descriptors on 44 models, 0 failed (it failed three times in between on other agents' Mummy and Zombie, mid-install, not on a Honk) |
| `run_creature_review.py check` | 30 switches, 0 failed, 0 console errors |

`texture_quality.py`: body atlas **50.1 %, under the 55 % target**: the charts of the deleted inner plate, boot tops and medallion stay empty, and the UVs must not be redone. Fragments 0.9 %, stretch p90 1.04. Head + hands: atlas 42.3 % (60.3 % on the head square), fragments 4.5 %, over the 3 % target: `scripts/fragments.py` puts 3.4 of it on the forearm stubs hidden in the sleeves and 0.7 on hands. Spread and stretch print meaningless values because linings sit on one texel (spread is by design). Median density 1,313 px/m body.

### Collapse gate (`scripts/collapse_gate.py`, 30 fps, worst single frame per region; exposed = can be seen from some direction at the clip's worst frame)

| Clip | armpit L/R | elbow L/R | hand L/R | neck | head | waist | robe | leg L/R |
|---|---|---|---|---|---|---|---|---|
| Standing | 8 / 9 | 6 / 0 | 2 / 2 | 0 | 0 | 11 | 0 | 0 |
| Walking | 14 / 9 | 0 / 0 | 1 / 0 | 0 | 0 | 13 | 8 | 4 / 3 |
| Running | 15 / 13 | 5 / 2 | 0 / 0 | 3 | 12 | 15 | 15 | 8 / 8 |
| Fidget | 11 / 23 | 27 / 7 | 14 / 2 | 8 | 4 | 14 | 0 | 0 |
| AttackMelee | 11 / 9 | 6 / 4 | 5 / 2 | 8 | 13 | 11 | 2 | 2 / 3 |
| AttackRanged | 8 / 10 | 6 / 0 | 10 / 2 | 9 | 9 | 12 | 4 | 0 / 3 |
| Cast | 8 / 10 | 5 / 1 | 7 / 2 | 2 | 7 | 13 | 4 | 0 |
| Hit | 11 / 12 | 7 / 6 | 3 / 2 | 19 | 17 | 16 | 13 | 1 / 3 |
| Death | 19 / 9 | 10 / 5 | 6 / 2 | 13 | 7 | 21 | 13 | 5 / 12 |
| Dead | 14 / 0 | 1 / 1 | 4 / 2 | 1 | 7 | 7 | 4 | 3 / 0 |

Non-zero, and many are exposed (`review/gates/collapse_gate.txt`). Worst: Fidget elbow L 27 (16 exposed). Standing's counts are the shoulder and belt faces against the bind pose. Looked at in `review/sheet_joints.png`, `sheet_cuffs.png`: the elbow and armpit read as cloth creases with no tear or flap. That is an observation, not a pass; no target was set for these bodies.

## Hide and pattern against MM9

MM9's cloth is a soft pale linen with a fine vertical weave, thin olive knot bands, a thin silver chain. Ours keeps linen, olive bands and silver chain; its weave is a fine pebble rather than vertical threads, and the knot bands are bolder than MM9's. Sheets: `review/sheet_compare.png`, `sheet_close_honk_*.png`. Skins are fully opaque, so no alpha cut-outs to carry over; no glow.

## Sheets (viewer shots, all read)

`review/sheet_compare.png` (MM9 vs ours), `sheet_tiers.png`, `sheet_close_honk_a/b/c.png` (texture), `sheet_joints.png` (armpits, elbows, neck, groin, corpse, hem), `sheet_cuffs.png`, `sheet_impact.png` (egg release), `close_hat_b.png`, `close_hat_c.png` (hats through Running, Hit, Death, Dead; made on an earlier build, with the same clips and hats), `strips_left.png` and `strips_front_c.png` (every clip, 7 frames), `strips_left_before.png` (before the night pass). In game: `review/ingame_v3/sheet_final.png`, `sheet_b.png`. Numbers: `review/gates/`.

## Deviations and open points

- **Symmetry not met:** MM9's bind pose is symmetric to 0.4 mm. Ours median 3.2 mm, p95 12.7, max 17.8 (pre-graft). Mirroring under the paid paint needs a repaint.
- **Hit L 5.8 cm (11 frames)** came with the longer sleeve lining: the hand against the other sleeve. It reads clean in `sheet_cuffs.png`. Fidget L is the same contact, MM9's own gesture. Death 3.5 / 4.5 cm is the right hand in the left sleeve's bell (4.4 cm at 0.38 s), the female's stoop on a smaller scale; `v2/scripts/arm_pulses.py` in the female project could treat it, and was not asked for here.
- **Elder face is younger in the centre:** no wrinkles between brow and lip where the tier A structure went in. A real fix is a head retexture, 10 credits per tier; the pair had 5 left.
- **Hands** read mottled red in close-ups, and the fingers claw-like in some raised poses (MM9's mitten curl on five fingers).
- **Dark specks in game:** three or four tiny dark points low on the robe of the near figure in `review/ingame_v3/sheet_final.png` (left panel, by the right hand), seen after the last build. Not in the viewer sheets, not measured, cause not confirmed; likely the top of the lining (0.60 m) catching through the wall at runtime. Not fixed.
- Cuff: a small sharp corner on the lining at the wrist in `sheet_cuffs.png` u1.
- Lining shines in the viewer (three.js specular on a dark texel); the game's specular is off.

## What was not checked

- Normal-speed playback was captured (`review/playback/`), but judged from its frames: nobody watched the videos.
- Egg release in game: the frame was not caught (see second pass); the socket is confirmed on the viewer pose only. The egg is large; its size is engine data, not this body.
- Foot sliding in game, LOD1-3 and shadow meshes by eye, the Honks in outdoor light, row speeds.
- `Cast` as `Hattack2` for row 216's Dispel Magic, and which row wears which hat (my reading of `SkinName2`).
- The viewer culls skinned meshes by their rest bounds, so tight close-ups of a corpse or raised hand lose the head or body. Corpse heads are present in game; I saw that on the female.

User artistic acceptance: "male can be accepted" (2026-10-31)


## Third pass, hands (2026-10-31)

User feedback: the hands looked grafted (`review/user_feedback_hands_20261031.png`, female).

Cause: not the pass-2 leans, which touch only Death and Dead while the fault shows in Standing. The graft itself was short and bent at bind, the forearm tube was thin and only 5-8 cm long, and the cuff sat off the forearm line. All of it predates pass 2.

Changes: `v2/scripts/hand_fix.py` scales the hand and its finger bones about the wrist and centres the sleeve on the forearm; `v2/scripts/wrist_fix.py` adds one constant Hand rotation to every clip to reach MM9's wrist line; thicker, shorter forearm tube in `sleeve_lining`; lining clamp in `robe_lining.py`. `v2/scripts/master_v3.sh` holds the third-pass chain. 0 credits spent.

Numbers: Hand 16.2 -> 18.5 cm (scale 1.14; MM9 17.9). Standing wrist bend L/R 15.8/16.1 -> 29.5/12.7 deg (MM9 26.2/9.6); Walking 24.5/30.4 -> 15.0/11.6 (10.2/12.6); Running 28.4/32.0 -> 21.2/18.2 (18.4/18.4); AttackRanged 28.6/25.2 -> 29.0/11.0 (24.0/10.6); Hit 30.2/32.9 -> 29.2/21.6 (31.5/18.6). Cuff centre to forearm line in Standing 0.6/8.0 -> 3.9/6.1 cm (left got worse, right better). Forearm skin radius 1.8-3.7 cm, the 1.8-2.0 cm dip at t 0.7 sits inside the sleeve. Sleeve slid 7.0/7.8 cm; hand constant rotation 14.9/22.2 deg.

Measurements: `review/hands/measure_before.txt`, `measure_after.txt`. Acceptance sheets, full size, Standing, Running 0.08 (raised), Walking 0.25 (low), front, left and quarter: `review/hands/accept_*.png`.

Export hash `0bbdb3939692`, viewer revision `v29-20261031`.

Gates on this build (one run): jitter 0, robe gate 0 in every clip, regression `mm9_actor_models_build_every_binding` passed, winding 0 inverted. Sleeve worst 55 px (Death L below), was 26 px; poke max 2.

Trade, arm gate, hands in the body: Standing L 2.7 cm (145 frames over 1 cm) and R 2.5 cm (88), clean in pass 2; Fidget L 5.8 -> 5.4 cm but 8 -> 20 frames; Hit L 5.8 -> 4.0 cm, 11 -> 19 frames; Death L 3.5 (8) unchanged, R 4.5 (18) -> 4.8 cm (22). Comes with the longer hand. The sheets show the Standing R hand clear of the robe, so that reading may be false; not resolved. Fix to try: a few degrees of constant upper-arm lean.

Open: short dark lines low on the robe, Standing and Running, left view (rear hem), lining edges crossing the outer wall; 1 lining vertex clamped did not clear them. Not rerun: floor audit, hair gate, collapse close-ups, standard sheets, in-game check, forearm/hand join close-ups.

## Dropped-clip pass, 2026-10-31 (run 2, 0 credits)

`v2/scripts/extra_clips.sh honkm source/mm9/honkm2.glb` (with `TARGET=` the pre-pass export to rebuild): Fidget2, Hit2, Death2, Dead2, CowerStart, Cower, CowerEnd, Backpedal, BackpedalRun, PropStand, PropFidget, PropFidget2 through the accepted clip steps (`hand_rest_honkm_extra.txt`, wrist_fix, `scripts/floor_ops_extra.txt`, `clip_relax_honkm_extra.txt`, mirror), grafted with `claude_shared/graft_clips.py`. Bound as script clips. Fidget2's fists on the hips needed a 10 cm push (2.5 cm left in, jitter +1.8 deg/f upper arm). Robe gate 0 in all 12. Numbers, strips: `review/clips_restore/`; summary `devdocs/mm9_rework/overnight/status/clips_groupA.md`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_honkm_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_honkm_reduce_claude/before/`.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_pamphlet`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).

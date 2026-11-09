# MM7 Ghost (m242): Shade / Specter / Ghost — Claude project

MM7 batch G, model 5 ([batch file](../mm7_batches/BATCH_G.md)). Descriptors 268 Shade (palette 243, grey-white robe),
269 Specter (244, brown: the native art) and 270 Ghost (245, near-black). **Exported, not installed** (batch rule).
Technically complete; pending user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m242_claude/review/viewer/`) · [viewer shots](review/shots/) ·
[playback](review/playback/) · [HD masters](references_hd/selected_views_review.png) · [head masters](references_head/)
· [G1 clip choice](review/g1/G1.md)

| Item | Value |
|---|---|
| Export | `export/mm7_m242.glb` (body, LODs 8,168 / 4,036 / 1,344 / 353 triangles, shadow LODs, 3 tier variants `m242_a/b/c`, head material merged, 8.9 MB); editable master `work/rig_v6.blend` (textured), clips master `work/rig_v3.blend` |
| Mesh | Smart Topology 15k of the HD three-quarter master: 227 parts — the hood/cape shell, ~70 robe shreds, the skull, spine, ribs, arm bones and every phalanx as separate pieces. Reduced after weighting to 8,200 (skull 1,100, cape 900, shreds 2,600, claws 1,100, other bones 2,500; pieces of <= 24 triangles kept whole) |
| Rig | 52 `B_*` bones on the humanoid set's source frames + 24 robe chain bones; **no Meshy auto-rig** (playbook skeleton rule): joints measured on the bone pieces (vertebral column sampled for pelvis..head, humerus ends for shoulder/elbow, forearm far end for the wrist); every bone piece 100 % on its nearest bone (skull, teeth and jaw on the head, ribs never on the neck or clavicles) |
| Clips (30 fps) | Standing Zombie Idle upper body + 70 % of the reaching arms (4.23 s); Walking authored swoop (1.0 s loop); Attack Zombie Attack window, raise + claw lunge (1.7 s, blow 1.017 s); Hit Zombie Reaction Hit (0.8 s); Fidget Zombie Scream (2.8 s); Death authored collapse (2.2 s); Dead |
| Textures | body 1K + head 1K (Meshy retextures from the HD masters / head turnaround), AO graded, ORM red = per-class specular mask; one region (the robe: every cloth texel); ramps per tier from the native palettes 243/244/245 |
| Meshy credits | **25 of 100**: Smart Topology 5, body retexture 10, head retexture 10 |

## Hood review fixes (user, 2026-10-20)

Screenshots `review/user_feedback_20261020/`: (1) the hood smeared into a long sheet from the shoulder past the skull
in the Fidget; (2) a thin flat plate poked up from the back of the hood.
- **Cause 1 (both shots):** the hood's pointed peak lies 23 cm behind the head axis, outside the hood region of
  `robe_rig.py`, so it stayed on B_Spine2 while the rest of the hood followed the head: 9.6x edge stretch when the
  Zombie Scream bent the head forward (the peak pulled back into a flat plate). Now every cape-shell vertex above the
  head joint is hood; the head share ramps over 18 cm (was 8) into the neck above the collar and B_Spine2 below it.
- **Cause 2:** two hidden fin pieces behind the ribcage and the nape (P190, P202: closed, so filed as bones, rigid on
  the spine) were uncovered when the hood moved. They are deleted (`step1_clean.py` DROP; `hood_fix.py` on the
  textured master, whose topology and Meshy UVs are otherwise kept). Six closed shreds under the arms that were also
  filed as bones are cloth now (a bone piece must lie within 7 cm of the spine, an arm line or the skull).
- The cowl no longer follows a skin neck's full bend: the source's neck and head rotation is damped to 50 %
  (`ghost_motion.py` HEAD_KEEP), and the cape's sleeve share stays off the collar (it starts 5 % along the humerus,
  at most 0.6).
- New gates on every clip: hood stretch (cape shell above 1.40 m) and a structural fin check (rigid trunk pieces inside
  the cowl behind the neck, which would be uncovered when the hood moves; P190/P202 would trip it).
  Hood stretch was max 9.6x; now p99 <= 1.61 and max <= 1.88 in all clips; fins: none.

## Anatomy decisions (batch G: "Genie and Ghost float with no legs")

- **No legs, no foot planting.** Below the pelvis the robe hangs empty. The leg bones exist only so the Mixamo clips
  retarget; they carry no weight and every clip resets them to rest. The pelvis floats at its rest height + 3.5 cm
  (the lowest shred tip just clears the floor) with a +-2.5 cm bob; the retarget's knee drop is discarded. The hover
  stays low on purpose (flyer rule: the descriptor's collision height is 128 units, the model 172).
- **The robe is a soft chain set**, not cloth simulation: 3 columns (left, centre, right) x 2 layers (front, back) x 4
  segments from the pelvis to the hem. Each shred takes ONE column/layer mix from its centre (a strip bends but never
  tears); the cape shell blends per vertex. Above the pelvis the cloth rides the body (hood on the head, cape on the
  spine bones, a sleeve share of the cape over each humerus). The chain roots hang from the world (85 % of the
  pelvis rotation undone), so a hunched trunk does not tilt the robe; waves travel down each chain with a phase lag.
- **Hands**: the claws are rigid bone pieces on the hand bone (no finger motion; Smart Topology returned every phalanx
  as its own piece, held open as in the masters). Deviation from the humanoid arm gate's finger checks, recorded here.
- **Walk = flight swoop** (native wa..wh): body pitched 35 deg forward, head raised, arms reaching ahead, robe trailing
  back nearly horizontally with a travelling wave on the native 1.0 s cycle.
- **Death** (native da..dd, xa): arms rise, then the empty robe collapses straight down: pelvis sinks, trunk folds
  forward, hood drops, arms fall outward onto the floor, robe chains fold outward into a heap; a per-frame floor rule
  raises the pelvis (bones) and opens the fold (cloth). The native hands that detach and lie apart are not modelled
  (they stay on the arms).
- **Eye sockets**: Smart Topology closed them with lid-like bumps; the compose paints the sockets and nasal opening
  black on the skull's front texels (located on its depth map).

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m242_claude/export/mm7_m242.glb --world mm7
```

Then add [export/actors_binding.yml](export/actors_binding.yml) to `assets_dev/worlds/mm7/models/actors.yml`
(`Ghost A/B/C`, scale 91.4 = native stand 169 px x frame scale 1.0 over the 1.85 m rest height; stride 2.63 m, run =
the flight loop because all tiers exceed the run threshold; blow 1.017 s; head look on B_Neck/B_Head).

## Replay

`TOKEN=<lease> STAGE=rig scripts/rebuild.sh` (step1_clean: pieces, hidden fins dropped, cloth flag, joints -> build_rig
-> robe_rig), then
`STAGE=anim` (retarget_mixamo -> ghost_motion -> ghost_gates); `scripts/b.sh reduce_ghost.py work/rig_v3.blend
work/rig_v4.blend`; texture chain once (`export_uploads.py`, Meshy `retexture_v1` and `head_retexture_v1`,
`transfer_uv.py -- work/rig_v4h.blend meshy/retexture_v1 work/rig_v6_pre_hoodfix.blend`), then `hood_fix.py` and
`robe_rig.py` on it -> `work/rig_v6.blend` (the reduction predates the fin removal, so the textured master is patched); `scripts/build_runtime.sh` (uv rasters,
AO, `compose_m242.py`, export, prepare, LODs, shadow fix, region variants, head merge); `viewer_tiers.py`,
`update_viewer_manifest.py`. Every step runs memory-capped (`scripts/cap.sh`, `scripts/b.sh`).

## Gates (final clips, `work/gates.json`, half frames)

- Hood: stretch p99 1.36 (Standing) .. 1.61 (Attack), max <= 1.88; fins (rigid trunk pieces inside the cowl): none.
- Floor: bone pieces >= -0.22 cm (Death), cloth >= -0.25 cm (Standing / Death); airborne clips 2.3 cm and higher.
- Hover: pelvis 1.17..1.22 m in Standing, 1.155..1.235 m in Walking, fixed in Hit and Fidget.
- Stretch: bone pieces rigid (max edge ratio 1.0); cloth p99 1.6 (Standing) .. 2.07 (Attack raise: the cape under the
  armpit when both arms go overhead).
- Jerk: head/hands <= 22 deg per 1/60 s (the source's fast claw swipes; Standing 0.7, Walking 1.3).
- Winding: 0 inverted closed parts (`check_winding.py`). Viewer: `run_creature_review.py check` 21 tier/clip
  switches, no console errors; playback captured. Not checked in game (optional for this batch).

## Known limits / for user review

- Rigid claws (no finger curl); the native's detached hands in the death stay attached.
- Robe motion is procedural (chains), not simulated; shreds can pass through one another in fast clips.
- The UV transfer matched 8,190 of 8,200 faces exactly; 2 small faces sit 2-15 mm from their nearest returned face and
  take its UVs. The head now bends half as far as the source clips (cowl rule).
- Tier A (Shade) reads near-white (native palette 243 x the 1.3 ramp gain); one number (`RAMP_GAIN`) in
  `compose_m242.py` if it should be greyer.
- The descriptors' TintColor (B 0x00ff96ff, C 0x00ff7878) is loaded by `MonsterTable` but used by no renderer.

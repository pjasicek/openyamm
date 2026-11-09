# MM7 Genie (m238): Djinni / Genie / Efreet — Claude rig-first project

Batch G, model 4 ([batch file](../mm7_batches/BATCH_G.md)). Descriptors 265 Djinni (palette 239, green cloth), 266 Genie
(240, violet) and 267 Efreet (241, red). **Exported, not installed** (batch rule). Status: technically complete, pending
user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m238_claude/review/viewer/`) · [viewer shots](review/shots/) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/) · [G1 clip choice](review/g1/G1.md)

| Item | Value |
|---|---|
| Export | `export/mm7_m238.glb` (8.1 MB): body `M238` with LODs 10,972 / 5,486 / 1,973 / 656 + shadow LODs, 3 tier variants (`m238_a/b/c`), head material merged; lamp `M238Lamp` (899 triangles, no LOD chain) as its own skinned mesh node. Editable master `work/rig_v6.blend` |
| Mesh | Smart Topology 15k of the HD three-quarter master: body (torso, arms, head, ponytail, an inner core cone down the vortex), a separate spiral vortex shell, circlet, earrings, eyes, forehead jewel. Reduced after weighting (skin 9.9k -> 7.2k with head and hands protected, vortex 4.5k -> 2.4k) |
| Rig | 52 `B_*` bones cloned from the humanoid set (source-frame rig: Meshy auto-rig joints for spine, clavicles, shoulders, elbows; ring wrists; mesh-measured hands; fingers by connectivity) + forearm/upper-arm twist + an 8-bone `Vortex_00..07` chain + `Lamp` + `Socket_Palm_L/R` |
| Clips (30 fps) | Standing 1.667 s, Walking 1.2 s, Attack 1.733 s (release 1.0 s; also cast and ranged), Hit 0.8 s, Fidget 2.0 s, Death 2.0 s, Dead 1.0 s |
| Textures | body 1K + head 1K (Meshy retextures from the HD masters / head turnaround), skin repainted to one albedo, the vortex mist lifted toward the master's pale blue-white, AO graded; ORM red = per-class specular mask; one region (green cloth: top, collar, cuffs, earrings); lamp 512 px (Meshy maps) |
| Meshy credits | **45 of 100**: lamp image-to-3D (Smart Topology + texture) 15, body Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10 |

## Anatomy decisions (batch G: floating, no legs)

- **No legs, a vortex tail.** Meshy's auto-rig put two legs inside the vortex; every leg weight was moved off them and
  the leg bones stay in the rig unweighted (no clip uses them). The vortex shell and the body's inner core below the
  hips ride an 8-bone soft chain (`vortex.py`: midline from per-height centroids of the shell, linear weights by height,
  blended over 8 cm into the hip weights; the hands, which hang at hip height in the A-pose, are excluded).
- **Steady hover, no foot planting.** The pelvis floats 3 cm above the rest height with a ±1.5 cm breath in every clip;
  the source clips' pelvis drops and turns are damped (hit 0.7, cast 0.5 of the source rotation, 0.3–0.5 of its sideways
  travel). The vortex sways as a lagging chain in every clip (phase lag 0.55 rad per bone, the total bend at the tip
  10–30°), trails 22° behind in the walk and whips in the hit and death. Following the playbook's flyer rule there is
  no extra hover lift: the native frames float ~22 units above the anchor, the model ~3.
- **Folded arms** (native wa frames): no library clip folds the arms, so Standing/Walking/Fidget fold them by a two-bone
  IK in the chest frame, forearms under the bust, the right one on top, elbows out and slightly forward; hands straight
  on the forearm. The first targets put the left forearm 6 cm into the waist (G6); the final ones are clear.
- **Death and the lamp.** The native bursts into a cloud and leaves the lamp. There is no cloud mesh: she raises the
  arms (the cast's top pose), rises 40 cm and spins 540° while the whole body shrinks into the vortex
  (`B_Pelvis` scale to 1e-4 by 1.35 s); the lamp appears at hip height at 0.55 s, falls with gravity, bounces once and
  settles on the floor. The lamp is a separate mesh node on a parentless `Lamp` bone (collapsed in every other clip);
  `tools/model_hide_collapsed_meshes.py` keys the node scales so the renderer skips the collapsed mesh: the body is
  hidden from 1.37 s of Death and in Dead, the lamp in every clip before 0.53 s of Death. Dead = the lamp alone.

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m238_claude/export/mm7_m238.glb --world mm7
```

Then add [actors_m238_binding.yml](actors_m238_binding.yml) to `assets_dev/worlds/mm7/models/actors.yml` (scale 114.3 =
native wa0 187 px x frame scale 1.1 over the 1.80 m pose, the same for all tiers; stride 2.1 m; release 1.0 s with the
charge at both palm sockets, the missile leaving between them; head look on B_Neck/B_Head). Tier speeds 200/220/250
stay under the run threshold (274), so `run: Walking`.

## Replay

`TOKEN=<lease> STAGE=rig scripts/rebuild.sh`, then `STAGE=anim scripts/rebuild.sh` (retarget -> twist -> weights ->
fingers -> reduction -> `author_genie.py` -> twist re-bake); texture chain once (`export_uploads.py`, Meshy
`retexture_v1` and `head_retexture_v1`, `transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend`);
then `scripts/build_runtime.sh` (sync clips, UV rasters, AO, `compose_m238.py`, export, prepare, LODs, shadow fix,
region variants, head merge, collapsed-mesh keys), `viewer_tiers.py`, `update_viewer_manifest.py`. Every Blender and
Python step runs in a memory-capped scope (`scripts/cap.sh`, `scripts/b.sh`).

## Gates (final export)

- G3: Meshy elbows/shoulders, ring wrists (0.9–1.8 cm from Meshy's), hand frames from the fitted knuckle line; fingers
  by connectivity (thumb cut at 7.5–7.8 cm).
- G4: arm stretch p99 1.22–1.28 in the folded poses, 1.96 (max 2.33) with both hands overhead (cast top, death).
- G5: hand stretch <= 3.06x (left hand overhead), 2.35–2.71x in the folded idle.
- G6: forearms and hands vs the torso: 0 cm in Standing, Walking, Fidget, Attack and Hit (the folded forearms touch
  each other by design; `G6_TORSO_ONLY` excludes the other arm). Death: only the vanishing body.
- Winding: 0 inverted closed parts (`check_winding.py`). Viewer: `tools/run_creature_review.py ... check`, 3 tiers x 7
  clips, no console errors. Not checked in game (optional for this batch).

## Known limits / for user review

- No cloud burst in the death (no effect hook in a clip); the body vanishes into the spinning vortex instead.
- The vortex is a solid sculpted spiral (Meshy), not a translucent mist; it is opaque in game.
- Smart Topology modelled the top, collar and cuffs as texture on the body, not separate geometry.
- The lamp keeps no LOD chain (899 triangles, drawn only on the corpse).
- LOD0 is 10,972 body triangles (about 10 % over the ~10k guideline; the head with its tall ponytail is 4.8k).

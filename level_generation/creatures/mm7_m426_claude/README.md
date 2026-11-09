# MM7 Warlock (m426) — Claude 3D model (batch B, 2026-10-20)

Fire / Water / Air Warlock (monsters 418/419/420, descriptors `Warlock A/B/C`, sprite palettes 107/108/109), with the
wand as a separate attachment. Same chain as the [Mage](../mm7_m274_claude/README.md) (settings in `creature.json`).
**Not installed** (batch rule). Status: technically complete, agent-reviewed in the viewer; user artistic acceptance
pending. [Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m426_claude/review/viewer/).

## Deliverables (`export/`)

| File | What |
|---|---|
| `mm7_m426.glb` | runtime body: LODs 10,732 / 5,363 / 1,930 / 643 (+ wand 581 / 290 / 103 / 32 split off), tiers `m426_a/b/c` (gown red / violet / green; cape, hair and gold unchanged as in the native), head set merged |
| `mm7_m426_wand.glb` | wand attachment on node `Staff` (child of the left hand); `Socket_Staff_Head` at the crystal |
| `mm7_m426_lod0.glb`, `mm7_m426.blend` | portable LOD0, editable master |
| `actors_binding.yml` | scale 109.0 (193 px / 1.77 m), run → Walking, stride 1.585, one Cast clip for attack and spell, release 0.8 s from the wand crystal |

Install later (not run): `tools/install_model.py export/mm7_m426.glb --world mm7` and `export/mm7_m426_wand.glb`,
then the binding and a tier/height + wand regression.

## Model

- **HD masters**: `00` = Codex v2 (left fist with a vertical grip, right hand open); 01–04 run 2; head turnaround
  (face and long hair) run 3, all four views used.
- **Geometry**: Smart Topology with `pose_mode` empty (keeps the fist, Mage lesson). Meshy fused body, gown, cape and
  hair into ONE shell (12.6k triangles); only the bare feet, arm/wrist bands, neck ring, eyes and earrings are
  separate. The shell is split by height (`creature.json` `split_piece`, below 0.96 m = skirt).
- **Rig**: source-frame rig; joints from Meshy (straight arms), wrists at the wrist bands; fist rigid.
- **Weights** (all in `weights_robe.py`, enabled by `creature.json`): hands of the fused shell found by distance to
  the forearm axis (`hand_axis_r`) so the cape beside them is not hand; the cape behind the arms (y > 4–8 cm, outside
  6.5 cm of the arm bones) loses its arm weight (5× stretch behind the shoulder otherwise); **legs inside the gown**
  (a skirt vertex whose outward ray hits the shell again, 1,130 vertices) keep Meshy's leg weights with the bare feet,
  the outer gown surface follows 14 × 4 robe chains (leg capsules floor 7.5 cm); interior skirt vertices near the axis
  copy the nearest outer weights. Without the inner-leg rule the Mixamo backward deaths dragged the fused legs out of
  the gown.
- **Wand** (`make_wand.py`, `staff_texture.py m426`): 0.46 m bronze-gold rod, gold knob, five curling gold prongs
  holding a turquoise crystal, from the native; seated in the left fist on the grip tunnel (`grip_from_fist.py`).

## Clips

| Clip | Source |
|---|---|
| Standing / Walking | set Relax Idle / Relax Walk Forward, arms abducted 6°, wand carry (`author_carry.py`) |
| Attack 1.267 s | set Unarmed Cast L Attack 3: the wand hand rises and is flung forward (native aa–ag), planted; release 0.483 s |
| Cast 1.3 s | set Unarmed Cast R Attack 1 (right-palm push), planted; release 0.517 s |
| Hit 0.5 s | set Unarmed Get Hit F1, planted |
| Death 2.0 s / Dead | set Relax Lay Down (the native falls backwards; Mixamo Standing React Death Backward and the set's Unarmed Death 1 were tried first, see Weights) |
| Fidget 2.0 s | authored (`staff_fidget.py`): the wand comes up in front, held with both hands |

## Gates (`review/gates_v5.json`)

Arm stretch p99 ≤ 1.54 standing/walking/fidget; Attack 2.04/2.34, Cast 1.82/2.96 (right armpit, where the fused cape
meets the arm), Hit 1.34/2.23; Death 3.14/2.08 lying. Wrist swing ≤ 58° except Death 77° and Fidget 64°. Gown p99
≤ 1.86 except Cast 2.12 and Death 3.02. Viewer check: 24 switches, no console errors.

## Textures (`scripts/compose_m426.py`)

Body 1K + head 1K + wand 255×512. One tier region, the gown (native indices 152–242), ramps from the indexed bitmaps;
skin repainted; gold re-graded; Meshy's gold paint on the two lid shells under the eyes repainted as skin.

Meshy: **30 credits** (Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10).

## Known limits / for review

- LOD0 11.9k (the fused shell left less to reduce cleanly; reduction ran after weighting with the face protected).
- A few small dark Meshy stains on the skirt show in all tiers.
- The death lies on the side (Relax Lay Down) instead of falling backwards.
- The hands of the fused shell are rigid; a faint outline remains under the eyes.

## Reproduce

`TOK=<lease> scripts/rebuild.sh all`; texture chain (`export_uploads.py`, `requests/`, `transfer_uv.py`,
`uv_raster.py` ×2, `bake_ao_natm.py`, `compose_m426.py`, `staff_texture.py m426 150,92,40 120,215,215`);
`TOK=<lease> scripts/build_runtime.sh`; `viewer_tiers.py`, `update_viewer_manifest.py`.

## Revision 2026-10-20 (user review)

- Attack / Cast: `face_forward.py` (after `plant.py`) turns the pelvis, spine, neck and head back toward the front
  per frame; the set's casts and punches turned the head 45–65° to the side. Head yaw is now 0°, and the arm gates
  held or improved.
- Fidget: `staff_fidget.py` solves both arms for the full pose and blends them in from the clip's own arm rotations (bone-local slerp); solving partway twisted the free arm's upper arm in the first frames.
- Feet: `flatten_feet.py` (before `robe_sim.py`; every clip except Death/Dead) levels each grounded bare foot to its
  rest orientation (keeping its heading) and lifts a sunken ankle back to rest height with a two-bone leg solve; the set
  clips had her on tiptoe, about 20° toe-down. Soles now sit within 5 mm of the floor; a stepping foot keeps the
  clip's motion above 8 cm.

## Reduction (2026-10-20)

A triangle reduction of this export (LOD0 10,732 -> 8,846 on the revision 2026-10-20b source, wand unchanged, no retexture) is in
[`../mm7_m426_reduce_claude/`](../mm7_m426_reduce_claude/README.md), awaiting user review; this project's exports
stay the unreduced production.
- Cape under the floor in Dead (found by the reduction pass): `weights_robe.py`'s inner-leg rule also needs the vertex
  within 12 cm of a thigh/calf bone (`inner_leg_r`); the gown's back surface hit the cape behind it with its outward
  ray, and 592 such vertices took calf weights (cape hem 24 cm under the floor). Inner-leg vertices 856 -> 264.
  `robe_floor.py` (Death, after `robe_sim.py`) then turns robe-chain bones up where their skinned hem dips under the
  floor. Lowest point in Death -24.4 -> -8.2 cm (-2.6 cm in the final Dead pose): 32 vertices of the flared back-left cape hem, which sits about 10 cm
  outside its chain bones. Gown p99 in Death rose to 4.4 (was 3.0): those gown vertices now follow the robe chains.
  The textured master was rebuilt with the same upload and UVs (byte-identical upload, same topology), so the
  textures are unchanged.
- Gold crescents under the eyes: the two loose shells (Smart Topology pieces 8 and 9) are dropped at export
  (`creature.json` `drop_pieces`, `export_actor.py`). The face skin, AO and normals painted beneath them are refilled
  from the surrounding skin (`compose_m426.py`). LOD0 is now 11,740 (the two shells were 170 triangles).

## Revision 2026-10-20b (user review: texture, hair, death, cast, gown patches)

- **Dark patches on the gown:** the fused shell has the gown's inside surface and the legs right behind the outer
  panel. Under the robe chains they poked through it in every pose (about 40 triangles seen from behind per pose).
  `export_actor.py` now drops, at export:
  - the gown's inside surface (gown-masked lower-shell faces facing the body axis, 154; `drop_gown_lining`);
  - inner layers whose outward ray hits the gown again within 8 cm (303; `drop_covered_gown`);
  - the hidden leg shafts above 18 cm (551; `drop_legs_above`; only the bare feet show).

  The compose also classes the gown's red-orange highlights as gown (they had been painted skin and kept the base
  red under the tier ramps), skips AO on the gown and cape, and refills the remaining dark Meshy blotches from the
  surrounding cloth. LOD0 is 10,732 (body; 11,313 with the wand before the split).
- **Death:** the inner-leg weight rule is off (`inner_legs: false`; nothing of the legs inside the gown is left to
  carry). Relax Lay Down stays: with the shafts gone, the gown covers the legs. The Mixamo backward fall splays the
  legs too far for the gown.
- **Hair:** the body set's hair is matched to the head set's copper (per-channel mean and spread in linear light),
  so the seam where they meet is gone.
- **Skin:** the uniform repaint is reduced (SKIN_MIX 0.8 -> 0.3, detail measured against a 24 px blur instead of
  6 px). Meshy's own skin paint is smooth, so the skin still reads clean rather than detailed. A new Meshy retexture
  would be the next step if more is wanted.
- **Cast:** a single clip, Cast, for attack and spell; the right-palm clip is removed. `wand_cast.py` raises the wand
  beside the head and thrusts it forward at chest height with the crystal at the target. Bolts leave the crystal
  (`Socket_Staff_Head`) at 0.8 s. The left wrist is now limited too (SIDES=LR, 58 degrees). The right hand's
  stretch in the old Cast is gone with that clip.
- `smooth_bones.py` smooths the trunk and head in Cast (as on the Monk and Mage).

## Installed 2026-10-20

The reduction (`../mm7_m426_reduce_claude/export/`) is installed through `../mm7_batches/BATCH_B_stage/` (assets_source + runtime copy, bindings in `assets_dev/worlds/mm7/models/actors.yml`). Rollback: `tools/install_model.py level_generation/creatures/mm7_m426_claude/export/mm7_m426.glb --world mm7` (the production export, byte-identical to the reduction's `work/mm7_m426_source_pre_reduce.glb`).

# MM6 female peasant v4 (pfem) — Claude humanoid project

New Sorpigal villager woman (`PeasantF1 A/B`, `Peasantf1 C`, monsters 595–597), rebuilt 2026-10-30 after the user's
review of v3: "the body is good, face is terrible", "hands are terrible, especially in standing", no attack needed.
**Installed**: `assets_dev/worlds/mm6/models/mm6_pfem_v4.glb` (source `assets_source/worlds/mm6/models/`), bound in
`assets_dev/worlds/mm6/models/actors.yml` (the previous `mm6_pfem.glb` is no longer referenced).

In game: [six tiers at the New Sorpigal test spot](review/ingame/peasants_v5_far.png), [closer](review/ingame/peasants_v5_near.png)
(spawned and frozen, both peasants). Close-ups: `review/g7_v8/`.

[Review viewer](review/viewer/index.html) (http://127.0.0.1:8912/level_generation/creatures/mm6_pfem_v4_claude/review/viewer/; tiers A/B/C, every clip; rebuilt by `scripts/viewer_tiers.py` + `scripts/update_viewer_manifest.py`, checked with `tools/run_creature_review.py check`: 18/18 switches, no console errors).

## Triangle reduction (2026-10-30)

`scripts/reduce_head.py` (run by `build_runtime.sh` on the textured master) collapses only the hair of the grafted
head; the face below the brows (front), the neck band and the seam stay, and the seam is re-merged with the body. The
body and its retexture are untouched. Head 9,258 -> 6,301; LODs 10,910 / 6,375 / 4,150 / 2,993 (was 13,878 at LOD0).
The step only acts above `head_reduce.target`, so a rebuild changes nothing.

## Review 5 (2026-10-30)

User: skin pale, graft lines where the head joins the body; a more subtle fidget.
- **Faceted heads (the root of the "clay", smudges and graft lines):** Meshy's GLBs import with their own custom
  split normals, flat per face on the head; Blender keeps them over smooth shading, so the head rendered faceted and
  the normals jumped at the graft. `graft_head_parts.py` clears them on every part.
- **Head skin** carries no normal map any more (`head_skin_normal` 0): the re-baked map still held the facets.
- **Skin colour:** the body skin, the neck fade and the neck spot take the head's own neck colour just above the
  fade (the male's neck is darker than his lit face: 187/131/102 against 216/144/113); the fade covers 4 cm and is
  chosen by distance from the neck axis, not by colour (Meshy's shaded neck side kept a hard edge).
- **Fidget:** Mixamo Weight Shift (9.4 s, posture held) instead of Standing Idle 03 Examine.
- The head's face and neck keep their full density (`protect_below_eye` 0.05, head 9.8k triangles; the colour test
  had spared only 645 vertices and left sliver triangles on the neck); LOD0 13.9k, LODs 7.9k / 4.1k / 2.9k.
- New body retexture `retexture_v6` (the body reduction changed); it painted hair colour over the bust and the strap
  tops again, so `compose_peasant.py` `debrown` turns those texels into skin (decolletage box) or bodice, and
  `deco_flat` keeps the decolletage plain (Meshy painted lace over it). An attempt to relax the neck mesh after the
  weld opened a fold beside the braid and was removed.

## Review 4 (2026-10-30)

User: the cleavage looks strange. Causes: the chest was one smooth mound of 2 cm edges with a 4-edge hole at the
midline (the dark notch), and Meshy painted a crease onto it. `body_fix.py` (creature.json body_fix.cleavage) now
closes small holes by merging their rim, subdivides the decolletage once and presses a soft valley in (11 mm deep,
17 mm wide, from just above the neckline to the bust apex); `reduce_rigged.py` keeps that box at full density
(`reduce_protect_box`). `body_fix.py` freezes the joints it measures the arms from (`work/body_fix_joints.json`):
every rig run rewrote `joints_final.json`, and the re-measured arms no longer matched the retextured mesh. New body
retexture `retexture_v5` with the neckline spelled out in the prompt (`retexture_v4` painted a brown band over the
bust and was discarded). `transfer_uv.py` gained `BARY=1` (UVs interpolated inside the matched source triangle, for
faces subdivided after an upload). Hands clear the skirt in every frame (nearest 12 mm).

## Review 3 (2026-10-30)

User: smudges still on the jaw and neck. Cause: the engine builds the tangent frame per pixel from screen-space
derivatives (`fs_model.sc`), flat per triangle, while the head's normal map was baked against smooth tangents; on the
decimated head with stretched UVs that left triangle-shaped light patches whenever the head turned. Head skin now
keeps 25 % of its normal map (`head_skin_normal`), the face's form is in the full-density geometry. The neck weights
across the graft are smoothed (`neck_weights.py`, 4 cm band) so the look-at turn does not shear the seam.

## Review 2 (2026-10-30)

User: head disproportionate, graft line on the neck, clay skin with grey smudges; arms too thin; body asymmetric,
bust too low. Fixes (all in the replay below):
- **Grey smudges / clay skin**: Meshy's head model is flat shaded and its normal map was baked against those flat
  normals; the smoothed graft applied it on top of smooth normals. `head_normal_bake.py` re-bakes it (Cycles,
  selected to active, from the original head placed by `work/graft.json` head_matrix). Baked AO no longer darkens
  head skin (5 % of the face texels sat under dark AO spots).
- **Graft line**: the two shells used to overlap. Now the old neck is cut exactly on the head's cut plane and tapered
  onto its rim, and `weld_neck.py` (run inside `prepare_rig.py`) merges the two rims into shared vertices; the
  head's neck band fades over 2.2 cm into the body neck's flat skin (`compose_peasant.py`).
- **Head size**: `shrink` 0.9 about the neck cut (crown 1.700 -> 1.675 m).
- **Body** (`body_fix.py`, before the graft, `creature.json` body_fix): mirror-averaged symmetry (the torso missed
  its mirror by up to 18 mm, the bust 3 cm off centre); bust lifted 2.5 cm; arms thickened about ring-fitted
  centres to target radii 40 / 37 / 24 mm below the sleeve / elbow / wrist (they were 28 / 32 / 14 mm).
- **Posture** (`posture_fix.py` after the clip timing): the sources dropped the clavicles 14-16 deg below rest and
  pushed them up to 18 deg forward, and leaned the chest; Standing and Walking are held within 3 deg (drop) / 6 deg
  (raise) / 8 deg (forward) of rest, lean 3 deg, neck 5 deg; Fidget clavicles only. Upper arms keep their world aim.
- New Meshy auto-rig (`rig_v2`) and body retexture (`retexture_v3`: front master + a clean-cloth text prompt; Meshy
  refuses multi-view images together with a prompt). Walk right arm 7 deg out (the straighter shoulders brought the
  hand onto the skirt). Gates: arm p99 <= 1.20 Standing/Walking, <= 2.18 Death; G6 hands 0 contact frames, nearest
  12 mm. Scale 105.1 (176 units over the new 1.675 m).

## What changed against v3

| | v3 | v4 |
|---|---|---|
| Face | Smart Topology head + head retexture | **separate head model** from a Codex HD head turnaround (Meshy multi-image, 30 cr), grafted at the neck, own 1K texture set |
| Hands | hand-authored clasped Standing pose | mocap Standing (Mixamo Standard Idle), relaxed hands at 60 % of the source finger curl, fingers fitted by connectivity |
| Rig | ICP-fitted Mixamo skeleton | source-frame rig (52 bones + twist), Meshy auto-rig joints made symmetric (`joints_sym.py`) |
| Attack | knife clip | none (attack and cast play Standing) |
| Skirt | 12×3 cloth bones | 14×4 robe chains with leg capsules (`robe_sim.py`) |

## Pipeline (replay)

```sh
# head: references_head/ (Codex, CODEX_BRIEF.md) -> meshy/head_v1 (multi-image-to-3d)
TOK=<lease> ... scripts/body_fix.py                     # st_v0_parts -> st_v0_fixed_parts (symmetry, bust, arms)
TOK=<lease> ... scripts/graft_head_parts.py <tag>      # graft.json: cut, braid, fit, shrink, weld -> st_v1_parts
TOK=<lease> ... scripts/head_normal_bake.py            # work/head_normal_rebake.png
TOK=<lease> scripts/rebuild.sh rig                      # prepare_rig (+ weld_neck), Meshy rig_v2 (creature.json rig_job), arm rings, joints_sym, fingers, weights
TOK=<lease> scripts/rebuild.sh anim                     # clips, abduct (8/13 deg; walk 6/3), feet, grip, robe sim, reduce, gates
scripts/export_uploads_graft.py -> meshy/retexture_v6 -> BODY_ONLY=1 transfer_uv.py -> uv_raster.py (UVMap, HeadUV)
  -> bake_ao_natm.py -> python3 scripts/compose_peasant.py -> TOK=<lease> scripts/build_runtime.sh
python3 tools/install_model.py export/mm6_pfem_v4.glb --world mm6
```

- **Head graft** (`scripts/graft_head_parts.py`, parameters in `graft.json`): the head GLB is normalised, Meshy's
  invented bust is cut at the neck (plane split), the braid kept below the cut by its hair colour and re-seated over
  the back; scale 0.43 so the crown meets the old crown with the eyes on the old eye line; the old fused head is
  bisected 2 cm above the new neck bottom and its neck tapers onto the new neck ring; the head's neck band is pulled
  under the old neck only (pulling it onto any part snapped the male's throat onto his collar). Decimated to 6k
  triangles with skin-coloured faces spared.
- **Joints**: Meshy's auto-rig returned shoulders 6 cm apart in x, a clavicle on the midline and knees 13 cm in front
  of the legs; `joints_sym.py` centres the spine on ring centres and mirrors every pair. `arm_select` in
  `creature.json` lets the ring fits work on one arm of the fused bodice/arm/hand shell.
- **Clips**: Standing Mixamo Standard Idle, Walking set Relax Walk Forward (stride 1.627 m), Hit Mixamo Standing React
  Large From Front, Death set Unarmed Death 1 (legs 25 %), Fidget Mixamo Standing Idle 03 Examine.
- **Textures** (`scripts/compose_peasant.py`, `creature.json` compose): body from the retexture, skin repainted with the
  head's own skin albedo, the neck under the head made flat skin (Meshy painted hair along the open rim), garment
  region = the green bodice and hem bands; ramps reuse `mm6_pfem_claude`'s native palette colours (786/787/788) with
  the range refitted. Head set = Meshy's head texture in its own layout (1K).

## Gates (rig_v5)

Arm stretch p99 ≤ 2.04 (Death), hands ≤ 1.45x, wrist swing ≤ 58°; robe p99 ≤ 1.75 (max 5.0 while falling in
Death); G6 hands (`g6_hand_proximity.py`, adapted to the fused shell): 0 contact frames in every clip, nearest 19.8 mm.
`check_winding.py` 0 inverted. Regression `mm6_pfem_actor_models_bind_town_peasants` passes (clips, LODs, tiers).
(First-round numbers; review 2's are in its section above.)

## Runtime

LODs 13,878 / 7,852 / 4,105 / 2,948 (body ratios 0.7/0.4/0.15: at the default 0.5 the decimation across Meshy's
fragmented UV seams frayed the hem bands at LOD1). One 2080×1024 atlas set (body + head merged), three variants
`pfem_a/b/c`. Scale 105.1 keeps the 176-unit standing height.

## Meshy

90 credits: head multi-image 30, auto-rig 5 + 5 (rig_v2), body retexture 10 + 10 (retexture_v3) + 10 + 10 (v4 discarded, v5) + 10 (v6); the first head request was sent with the misspelt flags `should_teture`/`teture_resolution`, so Meshy used its
defaults; the result is textured), auto-rig 5, body retexture 10.

## Known limits

- The head is 60 % of LOD0 (5.8k of 9.6k): the face is kept dense on purpose; the hair could be thinner.
- Meshy's head layout gives the face ~150 px at 1K; a repack failed (decimated UVs no longer join; Smart UV Project
  splinters on the hair cards). A 2K head base colour would double it at ~23 MB more GPU memory.
- The Death clip's mid-fall frame shows the frayed skirt hem and the stripped lower legs briefly.

# MM6 Chain Fighter (`figc`, FighterChain A/B/C) reduction (2026-10-14)

User: "check chain fighter next (including his weapons)". No-retexture route
([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed `mm6_figc.glb` (6,797 tris, one merged
material, three variants, eight influences; Codex batch `../mm6_figc_codex/`, already reduced once after weighting)
and its attachments `mm6_figc_axe.glb` (796) and `mm6_figc_shield.glb` (1,328). No Meshy credits.

## Body
Started with `REA_INFLUENCES=8 REA_PROTECT_HEAD=1 ../reduce_installed.sh figc FighterChain "MM6 Chain Fighter"`;
limits for the 1.756 m height: p99 5.27 mm, max 26.34 mm. The model had little slack left (even 70 % failed).

- **Head and hands kept** (`REA_PROTECT=B_Head,Hand,Finger` in `dump_mesh.py`, 2,379 faces): the hands are fitted
  to the axe handle and shield grip, so keeping them keeps both grips exactly.
- **One drift-lock round** (`texture_drift.py`, `drift_lock.py` from the werewolf, 199 faces): r80 had drifted
  texture on a boot and a leg.
- r80 was rejected visually: the tabard's yellow/red split broke into a jagged notch on the back (Walking, Death),
  which the per-face drift check did not flag (the faces straddle the boundary, so their median colour stays close).

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 6,797 | | | |
| head kept | 80 % | 5,437 | 4.2 / 24.4 | 0.990 | auto pass; hands not kept |
| head + hands | 85 % | 5,777 | 4.4 / 33.3 | 0.990 | max only: one pauldron rim point in Death |
| **head + hands + lock1** | **85 %** | **5,777** | 4.7 / 33.8 | 0.990 | **pick** |
| head + hands + lock1 | 80 % | 5,437 | 6.4 / 32.0 | 0.986 | tabard split jagged on the back |

## Weapons
`scripts/prop_*.py` are the decoration pilot's static chain (`../../decorations/mm6_reduce_pilot/`) with the prop
paths, the longest dimension as the size reference, and `prop_compare.py`/`prop_sheet.py` (textured + clay, four
views; `review/props/<name>_compare.png`).
- **Shield** 1,328 -> **596** (r45; r35 = 464 passes too but turns the boss octagonal). Normals by angle
  (`PROP_NORMALS_ANGLE=35`): the transferred normals smeared dark wedges over the flat back.
- **Axe** 796 -> **556** (handle kept exactly, 210 faces, blades and head at the rest of a 70 % budget;
  `work/axe_dec/`). The plain ladder thinned and split the handle at 55 % (the fist is fitted to its 11.5 mm radius);
  k60 (476) starts to facet the blades.
- Colour variants stay on every primitive; the old LOD1 is dropped where it is no longer coarser than the new LOD0.

## Result (not installed)
`export/mm6_figc.glb` (= `mm6_figc_lock1r85.glb`): LODs 5,777 / 2,885 / 1,034 / 340 (installed 6,797 / 3,610 /
1,725 / 694). `export/mm6_figc_axe.glb` LODs 556 / 432 / 196 / 78; `export/mm6_figc_shield.glb` 596 / 303 / 86.
LOD0 total with weapons 8,921 -> 6,929.
Review: `review/sheet_a.png` (+ `_clay`; rows installed, head+hands 85 %, 80 %), `review/sheet_clips.png` (Attack,
Death, Walking), `review/sheet_back.png` (tabard back), `review/props/axe_compare.png` (rows installed, k70, k60),
`review/props/shield_compare.png` (installed, r45, r35). Viewer `review/viewer/` (body only, installed vs pick per
variant, eight-influence skinning from the Ghost viewer; `check_viewer.mjs` 48 switches, no console errors).

## Installed: weapons only (2026-10-14)

User: "leave the body as it was, keep the reduced axe and shield only". The body stays the installed 6,797-triangle
model (`export/mm6_figc.glb` is a staged candidate only). Previous sources backed up to
`work/mm6_figc_axe_source_pre_reduce.glb` and `work/mm6_figc_shield_source_pre_reduce.glb` (rollback: install
them); `tools/install_model.py export/mm6_figc_{axe,shield}.glb --world mm6`. Same node names and variants; the
shield's `openyamm_lods` lists two levels (the old LOD1 is no longer coarser). The `actors` suite's
`mm6_fighter_chain_actor_model_tiers_share_the_native_height` passes (it does not load the attachments; the other
failures are guard, mage, ooze and DWI cases unrelated to this model). Lease released.

## Round-6 body and matte steel on the reduced props (2026-10-15)

`assets_source` still held Codex round 5 (Jogging run, dark steel). User picked "A, shield lightened to match":
- Body: `../mm6_figc_codex/export/mm6_figc.glb` (round 6: Standard Run, mid-grey matte steel, textures capped at
  2048) installed as is; Attack unchanged, so the reviewed impact 0.85 stays valid.
- Axe and shield: `scripts/matte_steel_r6.py` applies Codex's `materials_r6.py` recipe to the reduced props: the
  round-6 gear steel ramp (taken from the round-6 axe, same luminance range as the shield's steel) on all tiers, and
  the metal-rough texture's steel region with specular capped at 32/255 and roughness at least 220/255. The axe's new
  texture is pixel-identical to Codex's round-6 axe and its ramps equal; the shield (untouched by Codex) now matches.
  `export/mm6_figc_{axe,shield}.glb` are these; the round-5-steel versions are `export/*_r5steel.glb`.
Previous sources: `work/pre_r6_20261015/`. Actor-model tests pass.

## Gait rollout (2026-10-31)

Package h01 of the [gait rollout](../gait_rollout_20261031/README.md) appended `Jog` (humanoid set
Unarmed-Run-Forward, 0.78 s, stride 3.0072) and `Sprint` (Unarmed-Sprint, 0.60 s, 3.7980) to the installed
`mm6_figc.glb` (arms, axe and shield from `Running`, aligned to `Walking`). The walk-as-run binding is replaced by
`Jog`. Existing clips untouched; bindings for the coordinator in `../gait_rollout_20261031/h01/bindings.yml`. Details,
gates and doubts: [h01 README](../gait_rollout_20261031/h01/README.md). Rebuild:
`../gait_rollout_20261031/h01/scripts/rebuild.sh figc`. A far-LOD repair rerun (or any other rebuild of this source)
must re-graft these clips: copy the new source over `h01/work/mm6_figc_pre_gait.glb` and rerun that command, then
install its export.

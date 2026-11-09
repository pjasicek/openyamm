# MM6 Genie / Djinn / Efreet (`djn`, BGenie A/B/C) reduction and body retexture (installed 2026-10-14)

User: "do djinn". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)), scripts from
`mm6_bat_reduce_claude/`; `decimate_tex.py` from `mm6_gst_reduce_claude/` (protected part kept or decimated on its
own) with the `REA_PROTECT_ZMIN` height cut of `mm6_natm_reduce_claude/`. One 2080x1024 atlas: body (u < 0.5) and the
separately retextured head set (u > 0.5, 2,987 faces, all above 1.755 m). Head and neck colours already match on all
three tiers (`review/neck/sheet_installed.png`), so no unify step.

## Ladder rounds (limits scaled to the 2.22 m height: p99 6.7 mm, max 33.4 mm)

| round | protection | pick | triangles | result |
|---|---|---|---:|---|
| 1 | head kept (ratio is of the whole model, so the body cut deeper) | none | | max 43 mm from r70 down |
| 2 | none | r70 (r55 failed on one 43 mm spot) | | |
| 3 | none, piece-aware weights | r55 | 6,633 | face broke up: brows, eyes, goatee (`review/close/sheet.png`) |
| 4 | head set decimated on its own to 70 % | r62 | 7,477 | face fine, a black shard under the goatee |
| 5 | head set and every face above 1.66 m kept | **r70** | **8,443** | **picked**: face and chin as installed |

- **Weights:** the nearest-face transfer mixed the right wrist bracelet's weights with the hand under it (a stretched
  spike in Death, 43 mm). `reduce_ladder.py` now copies weights per connected piece, from the nearest vertex of the
  matching source piece (`REA_PIECE_WEIGHTS`, on by default).
- **Shard under the goatee:** not a UV or normal error; the reduced neck sank slightly and uncovered an installed head
  face behind it. Keeping the upper neck (above 1.66 m) at full detail removed it.
- **UVs:** `scripts/fix_uv_seams.py` re-maps body faces whose UVs land off the painted body islands or in the head half
  of the atlas (16 faces at r70), from the nearest body-side source triangle; head faces are untouched.
- r66 (7,961) misses only the p99 limit (7.1 mm against 6.7 mm), if more saving is wanted.

Build (`scripts/build_cand.sh Cand_70 q70`): export_cand -> swap_lod0 -> build_actor_lods ->
`mm6_djn_claude/scripts/shrink_shadow_lods.py` -> carry_variants: `export/mm6_djn.glb`, LODs 8,443 / 4,220 / 1,517 /
501 (installed 12,063 / 6,029 / 2,169 / 718). No Meshy. Review: `review/close/sheet_q70.png` (installed and three
tiers whole, left hand, vortex tail), `review/close/sheet_chin_q70.png`; viewer installed vs 70 % per tier, 54 loads
pass (`review/viewer/check.json`).

Pre-existing (installed model too): the right wrist bracelet is skinned to its own `GoldBracelet` bone, which does not
follow the wrist in Death, so the bracelet floats off the hand there; faint pale flecks on the neck and chest.

## Round 2: body retexture (2026-10-14)

User on the 70 % result: "good but body might need retexture" (blotchy low-res bracer, dark slash marks on the skin;
both were in the installed body texture). Head set unchanged.

- `scripts/uv_upload.py`: fresh Smart UV islands (66 degrees, concave packing) for the 5,456 body faces of Cand_70,
  placed in the atlas's left 1024 px (u x 1024/2080); the 2,987 head faces keep their atlas UVs. Upload: the body
  square at 92 %, the head half rescaled into a 0.08 corner. The vortex coils unwrap into rings, so the body islands
  cover about 35 % of their square (80 degrees gave 29 %).
- Meshy `requests/body_texture_r1.json` (meshy-7, original UVs, PBR, 4k, the four HD masters), 10 credits; UV parity
  exact (25,329 corners).
- `scripts/compose.py`: body half of the atlas from the Meshy return; regions from its colours and the rig (gold metal,
  blue skin, the `Gold*` accessory bones, `Vortex*` bones). Skin and vortex luminance quantile-matched to the
  installed body (skin median 0.121 both), so the tier ramps keep their look. Gems: Meshy's own red stays (bracer
  centre), the wrist bracelet's stones are painted red, every other stone on the gold pieces dark navy like the
  accepted look (the installed gem ramp is near-black in all tiers; a green base bled through the mask edge).
  PBR as `mm6_djn_claude/scripts/compose_genie.py`. The 32 px gutter takes the body edge.
- `scripts/texture_chain.sh` (15 s): parity, raster, compose, geometry, swap, atlases, LODs 8,443 / 4,220 / 1,517 /
  501, shadow LODs, variant mappings, viewer (`rt`). Review `review/close/sheet_rt.png` (torso installed / new, three
  tiers), `review/close/sheet_gems.png` (bracer, armlet, bracelet); viewer 54 loads pass.

## Installed (2026-10-14)

User: "I dont like the bracer texture on his left hand, but accept this for now." Open item: redo the left-forearm
bracer (`GoldBracer`) texture. Previous source backed up to `work/mm6_djn_source_pre_reduce.glb` (rollback: install
that file with `tools/install_model.py --world mm6`); `export/mm6_djn.glb` installed with `tools/install_model.py`.
Regression `mm6_genie_actor_model_tiers_and_cast_clips` passes.
Dev assets only; `assets/worlds/mm6.zip` and Android not repacked.

# Hesper Glassbacks: three tiers, one body, three crests — Claude quadruped project

> **Reduced (2026-10-22):** `../hes_glassback_reduce_claude/` (default route of `RETOPOLOGY_PLAYBOOK.md`, no
> retexture): body 7,485 -> 5,987 (LODs 2,992 / 1,494 / 748); head set (head, beak, eyes) and feet exact; floor,
> stride and crest-clearance gates pass; the 14 crest attachments unchanged. Exported, not installed; this project's
> exports are untouched and remain the rollback source. Ledger: `../REDUCTION_LEDGER.md`.

Starport Reach's native grazers of the black glassfields ([concept](../../../design/kreegan_world/concepts/monsters/fam_glassbacks.png),
brief `design/kreegan_world/concepts/monsters/CODEX_BRIEF_ZONE1_FAMILIES.md` §2), monsters 10080 Glassback Pup /
10081 Glassback / 10082 Glassback Bull (`design/kreegan_world/data/make_monster_tables.py`, Picture names
`hes_glassback_pup`, `hes_glassback`, `hes_glassback_bull`). Quadruped playbook route (Meshy model, our own rig with
heat weights, procedural clips with floor rules), adapted to six legs (alternating tripod). **Exported, not installed**
(the Hesper stage integrates it). Meshy: **35 of 60 credits**. No user acceptance recorded yet.

[Before/after polish](review/tiers_before_after.png) · [Tiers](review/tiers_contact.png) · [close-ups (head, crest, back)](review/closeups.png) ·
[textured clips](review/clips_textured.png) · [clay clips](review/clips_clay.png) ·
[viewer shots](review/shots/viewer_shots.png) · [Attack strip](review/attack_strip.png) · [HD masters](references_hd/selected_views_review.png) ·
[head masters](references_head/selected_views_review.png) · [floor gate](review/floor_gate.json) ·
[crest clearance](review/crest_clearance.json) · viewer `review/viewer/` (serve the repository, port 8912)

## Deliverables

| File | What |
|---|---|
| `export/hes_glassback.glb` | body: one skinned mesh `Glassback`, body + head sets merged (2080×1024 atlases), LODs **7,485** / 3,741 / 1,346 / 446 triangles + shadow LODs, variants `hgb_a/b/c` (region ramps), clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget; socket bone `Socket_Beak` |
| `export/hes_glassback_crest_<size>_<bone>.glb` | the glass crest: 3 sizes (`short`, `full`, `tall`) × 5 bones (`spine1`, `spine2`, `spine3`, `neck1`, `tail1`), rigid static attachments in their joint's space, own LOD chains (full crest 1,853 / 1,068 / 288 / 135 triangles in all), variants `hgb_a/b/c`; `export/crest_info.json` |
| `integration/actors.yml` | staged bindings for the three descriptors (skin, scale, strides, look, beak socket, impact, five crest attachments each) |
| `textures/` | body and head 1K sets (`hgb_*`, `hgb_head_*`: base graded, normal, ORM, region mask, material classes), `hgb_ramps.json`; glass atlas `hgb_glass_*` (our own procedural art), `hgb_crest_ramps.json` |
| `work/crest_v3.blend` | editable master: reduced, bent-knee rig with clips and every crest piece parented to its bone |

Install later (parent), into the Hesper stage's model set (not `assets_dev`): `tools/install_model.py` on
`export/hes_glassback.glb` and the 14 crest GLBs (no `short_neck1`) with the Hesper world target, then the `integration/actors.yml`
entries. Run `check_winding.py` first (done here: 0 inverted closed parts on all 15 GLBs).

## Tiers (one body; crest size per descriptor)

| Skin | Monster | Scale | Hide (R) | Belly (G) | Rust (A) | Crest | Glow (emissive) |
|---|---|---|---|---|---|---|---|
| hgb_a | 10080 Glassback Pup | 100 | grey basalt | pale grey | = hide | `short` (height ×0.5, rounder, no outer shoulder row or neck spines: 4 attachments) | pale teal (0.55, 0.95, 0.88) |
| hgb_b | 10081 Glassback | 125 | darker grey | grey | = hide | `full` | strong teal (0.12, 1.0, 0.78) |
| hgb_c | 10082 Glassback Bull | 143.75 | near-black | dark grey | rust-red streaks | `tall` (×1.3, leaning twin points) | green-white (0.82, 1.0, 0.86) |

- **Size** (kept by the coordinator's decision, 2026-10-22). The brief puts the Pup (A) at about 1.2 m at the shoulder; the model is metric at A's size (the back
  stands 1.19 m, 2.87 m nose to tail), so A = 100 (100 units a metre), B = A / 0.8, C = B × 1.15. If the 1.2 m beast
  was meant to be B, use 80 / 100 / 115. Explicit scales, no `scale_reference` (Hesper has no sprite frames).
- **Regions** (`scripts/compose.py`): R hide, G belly (pale texels below the flanks), B unused, A rust streaks
  (ridged 3D noise on the upper hide, continuous across UV seams; A and B map it with their hide ramp, so only C
  shows rust). Glass toes, the beak and the eyes are in no region (black glass, dark horn, painted eyes). Ramps are
  from the brief's colours (there is no native palette), inside Khronos 30–243. The head set shares the body's
  ramps (`merge_head_material.py` requires it); its hide luminance is matched to the body at the neck (gain 0.90).
- **Crest** glass: one material with a crack region (the painted cracks, per-tier teal ramps) and a Glow material
  (KHR_materials_unlit, black base, per-tier `emissiveFactor` for the glow strips and root collars, one material per
  variant). Glass is metallic 0, specular 1, roughness 0.16–0.4 (Khronos ranges, glossy).
- **The approved sheet's flaw** (the Pup drawn with an adult crest): the HD masters follow the full-crest design, and
  the Pup gets the `short` crest attachments instead.

## Model

- HD masters (Codex, `references_hd/CODEX_BRIEF.md`) from the approved sheet: a faithful crested three-quarter
  (`00_three_quarter_crest.png`, identity record) and the same creature **with the crest removed** for Meshy (the
  crest is modelled separately, like the guard's rifle): `00_three_quarter`, `01`–`04`, plus `crest.png` (the crest
  alone, side view) and a head turnaround. One correction on the crested primary; the rest first time.
- Meshy Smart Topology: `body_geometry_v1` (three-quarter) and `v2` (same, `symmetry_mode: on`) came back yawed
  and curved with the middle legs 30 cm apart along the body (the three-quarter view confused the six legs; not used,
  10 credits). `v3` from the strict **left profile** with `symmetry_mode: on` gave a straight, near-symmetric body
  (15,873 tris, one piece plus the two eyeballs; the middle legs still differ by 15 cm along the body).
  `scripts/prep.py`: forward −Y, widened ×1.12 (the concept's broad barrel), back at 1.2 m.
- Texture: body retexture with Meshy's own layout copied back face by face (`transfer_uv.py`, 0 mm mismatch), head
  retexture on our `HeadUV` (head = faces in front of the neck cut, y < −1.04 m), both from the HD masters. AO bake,
  grade (local 0.45, contrast 1.08), 1K body + 1K head. ORM: R = specular mask (hide 0.12, belly 0.08, glass toes 0.9,
  beak 0.55, eyes 1.0; `openyamm_specular_mask`, as the guard), G roughness by class, B 0. Material classes
  `textures/hgb_material_classes_1k.png` (1 hide, 4 glass toes/beak, 6 eyes).
- LOD0: region decimation after weighting (`reduce.py`: body ×0.42, head ×0.7, the neck seam's faces kept):
  15,862 → 7,485; with the full crest about 9.3k (siblings 8–10k; the spines are silhouette).

## Rig, weights and gates

- 26 bones (`rig.py`; the rest pose bent afterwards, see the polish pass): Spine1 (root, hips) → Spine2 → Spine3 → Neck1 → Head, Tail1–3 on Spine1, per leg
  `Upper/Lower/Foot_<F|M|H><L|R>` (front on Spine3, middle on Spine2, hind on Spine1), joints from the leg axes
  measured per 5 cm band (`leg_axes.py`), the leg pivots high in the body (z 0.72). Heat weights, 0 unweighted;
  eyeballs rigid on Head. Two weight fixes: feet below the ankle 100 % on `Foot_*` (`fix_feet.py`; soles had sunk
  1.5–6 cm with the knee angle) and the back above z 0.8–0.92 spine-only (`back_weights.py`: the crest stands on it).
- **Crest attachments** (`crest.py`, `crystals.py`, `crest_export.py`, `crest_post.py`): 30 faceted glass plates
  (see the polish pass), roots sunk 1.3 radii, each plate on the bone that dominates the hide under it. The joint-space
  transform uses the body's inverse bind matrices (checked: joint rest world × IBM = identity within 1e−6).
- **Crest clearance gate** (`crest_check.py`, every frame of every clip, `review/crest_clearance.json`): hide offset
  under each root in units of its sink: worst gap −0.25 (Attack); worst swallow 0.97 (Death). Below −1 the open
  bottom would show; none does. Nearest tips of plates on different bones ≥ 12.7 cm (no collisions).
- **Floor gate** (`floor_gate.py` on the runtime GLB with the floor audit's evaluator): every clip within tolerance on
  all tiers, walk/run never with every foot off, corpse at 0.0 (`floor_fix.py --ground-death`: the export had left
  Dead about 2 cm up). Measured strides walk 0.875 / run 1.4583 m
  (all six feet), equal to the binding.
- `check_winding.py`: 0 inverted closed parts on the body and all 15 crest GLBs. Viewer check 24/24 switches, no
  console errors.

## Clips (24 fps, `anim.py`)

| Clip | Length | What |
|---|---|---|
| Standing | 3.0 s | breathing, slow head sway, tail drift |
| Walking | 0.5 s | alternating tripod FL MR HL / FR ML HR (a small back-to-front lead), duty 0.5, stride 0.875 m (1.75 m/s), lift 10 cm, body 1.5 cm low with a heavy bob, roll and sway |
| Running | 0.4167 s | lumbering charge: same tripod, duty 0.4, stride 1.458 m (3.5 m/s), body 3.5 cm low, front 3° down, head low |
| Attack | 1.79 s | (user review) crouches, rears up on the planted hind legs about the hind hips (body −32°), front feet raised and folded like paws, middle pair lifted, a held peak (0.62–0.88 s), then accelerates down into a slam: beak and front feet hit the ground on their own footholds, **impact 1.083 s** (frame 26), a heavy settle to 1.8 s |
| Bite | 1.2 s | secondary (the earlier attack): draws back with the feet planted, lunges and crushes down with the beak, impact 0.583 s |
| Hit | 0.6 s | flinch back and aside, head thrown up |
| Death | 2.0 s | staggers, the legs buckle outward (knees up and out), the belly drops onto the floor, the head sinks aside |
| Dead | 1.0 s | the last Death pose |
| Fidget | 2.5 s | grazing: lowers the head, crops at the ground twice, looks aside |

Footholds (`foothold()`): walk and run move each leg's stance centre along the body toward its hip until both sweep
ends stay within 97.5 % of its reach (see the polish pass); sideways only if that is not enough (never needed). At speed 250/500 the walk and run play at A 1.43, B 1.14, C 0.99.

## Polish pass (2026-10-22, coordinator review)

Before/after: [tiers](review/tiers_before_after.png); the v1 sheets are kept in `review/before_polish/`.

1. **Crest: fewer, chunkier plates.** 53 needle crystals → 30 plates (`crest.py`): midline every 16.5 cm, three
   flanking pairs over the shoulders and two outer pairs (was five and three), three pairs over the mid back; radius
   0.52 × height (was 0.42), 5–7 sides, an elliptic section 1.3 : 0.85 along the spine (thick blades like the
   concept). The two small head spines now ride `Neck1` (the hide under them), so there is no `head` attachment.
2. **Stronger glow.** Emissive per tier raised (table above); glowing root bands that lie on the hide around each
   plate's foot (each prism edge followed down to the hide, 0.22 r wide; a ring at root height read as a flange or a
   cuff), three crack strips 0.15 r wide on the big plates and glowing seams up one or two vertical edges; brighter
   crack ramps and deeper teal near the roots in the glass texture.
3. **Bent rest pose** (`rest_bend.py`): the body lowered 5 cm with every foot on its rest foothold, applied as the new
   rest (hip to ankle 0.90–0.95 of reach, was 0.98), and the whole model scaled ×1.0435 back to the same 1.192 m back
   height (scales unchanged). The walk/run footholds now move only along the body (`foothold()`: front feet 10–15 cm
   back, hind feet 9–16 cm forward, middle 0–2 cm); no foot is pulled in sideways any more (was 6–18 cm).
4. **Feet planted:** the Attack's rear-back keeps the shoulders down (pitch −3.5°, body back 3 cm and 4 cm lower) and
   the lunge is 6.5 cm; Hit and the start of the Death no longer lift the front; the corpse's hind feet reach. IK
   residual 0.0 mm in every clip (was 12 / 4 / 7.5 cm).
5. **Chin/throat/chest** (`throat_fix.py`, after `compose.py`): under the jaw and on the chest both texture sets get a
   geometric belly/hide split and one brightness field shared across Meshy's UV islands and the neck seam (4 cm 3D
   grid × each texel's fine detail). The pale stair-step blocks are mostly gone; a few small steps remain low on the
   chest beside the forelegs.

Gates rerun on the final build: floor pass on all tiers (corpse 0.0), strides 0.875 / 1.4583 m on all six feet,
crest clearance worst gap −0.25 sinks (Attack), worst swallow 0.97 (Death), tips ≥ 12.7 cm apart, winding 0 on
16 GLBs, viewer 24/24 with no console errors. No Meshy credits (35 of 60 in all).

Follow-up (coordinator): the `short` set was nearly as tall as `full` (a radius × 1.6 height floor lifted it to
×0.7); now ×0.5 of the full heights, one more side per plate (rounder), without the outer shoulder row and the
plates under 9 cm (no neck spines), glow bands kept: 1,592 triangles at LOD0. Crest clearance, winding (0 on 14 crest
GLBs) and the viewer (24/24) rerun; [tiers before/after](review/tiers_before_after.png) refreshed.

Attack rework (user review: "goes onto his back legs, stands up a bit and swipes/bites down"): `REAR` keys in
`anim.py`, a hind-hip pivot for the body pitch, per-leg knee folding, and an ease-in segment for the slam. The hind
feet stay planted, and every foot that lands does so on its own rest foothold (no sliding). At the peak the middle
feet hang up to 9.7 cm short of their raised targets, in the air as intended. Gates: floor pass (a support foot is
always on the floor), crest clearance through the rear-up (worst gap −0.05 of a short-crest sink, tips of all three
sets ≥ 12.8 cm apart), winding 0 on 15 GLBs, viewer 27/27. [Strip](review/attack_strip.png), side and three-quarter.

## Doubtful or for the user

- **Size** as decided: the Bull is 1.7 m at the back and 4.1 m long.
- The glow strips read as solid emissive colour (the engine draws them unlit); their brightness in game, with and
  without bloom, is unchecked. The review renders approximate it (Eevee, half base + half emission).
- Small belly steps remain low on the chest; the blend preview in `review/closeups.png` shows the head and throat.
- Not checked in game (no install, no engine work in this task).

## Engine needs (not done: engine work is on hold)

- **Multi-node or skinned attachments.** One crest per tier is now five rigid attachments (10 draws on top of the
  body's 1). A rigid attachment GLB with pieces on several named joints, or a skinned attachment on the carrier's
  skeleton, would make it one model per crest size.
- **Shared images across attachment GLBs.** Every crest GLB carries its own small glass atlas (512² base, 256² ORM
  and mask): five copies per tier.
- **Per-descriptor node scale or hidden nodes** would allow one skinned crest with per-tier spine length instead.
- **Glow/bloom:** the crest glow is a constant `emissiveFactor` on the static attachment material, which the bloom
  view picks up where it runs; not verified in game.
- `EnergyImmune` rule and the shots glancing off the glass (design, `design/kreegan_world/ENGINE.md`).
- The Glassback Queen (10101, ×1.6, "crystal spines grown into a crown") can reuse this body with the `tall` crest and
  her own crown attachment on `Head`.

## Replay

Claim the project (`tools/creature_workspace.py claim --project level_generation/creatures/hes_glassback_claude
--identity hesper:glassback ...`), then with `TOK=<lease>`: `scripts/run.sh prep.py`, `python3 scripts/normalise.py
meshy/body_geometry_v3/model_urls_glb.glb work/body_norm.npy && python3 scripts/leg_axes.py work/body_norm.npy`,
`scripts/run.sh rig.py`, `export_uploads.py`, the Meshy retextures (`requests/retexture_v1.json`,
`head_retexture_v1.json`), `transfer_uv.py` (UVMap, then HeadUV), `raster.py` ×2, `bake_ao.py`, `fix_feet.py`,
`back_weights.py`, `reduce.py work/rig_v3.blend work/rig_v4.blend 0.42 0.7`, `rest_bend.py work/rig_v4.blend
work/rig_v5.blend 0.05`; `python3 scripts/glass_texture.py`, `python3 scripts/compose.py`, `python3 scripts/throat_fix.py`; then `scripts/build_runtime.sh` (clips, crest, gates, export, LODs, variants, head
merge, floor fix, crest attachments) and for review `python3 scripts/tier_textures.py`, `scripts/run.sh
viewer_export.py shots`, `python3 scripts/viewer_manifest.py`, `python3 scripts/review_sheets.py`,
`scripts/run.sh clip_sheet.py work/crest_v3.blend review/clips_clay.png 6 full` + `assemble_sheet.py`.

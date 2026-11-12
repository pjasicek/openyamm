# Werewolf texture quality pass (MM6 `mm6_wwf`), 2026-11-12

Wolfman / Werewolf / Greater Werewolf (descriptors Werewolf A/B/C, palettes 831/832/833). Part of the MM6–MM8 audit
fixes ([COMMON.md](../audit_mm678_20261111/fixes/COMMON.md), texpass stream), agent `wwf-revert-texpass`, lease
`mm6:wwf`.

## Rebuild reverted (user, 2026-11-12)

After comparing in the side-by-side viewer the user said: "I preferred the old werewolf I think, just maybe do the
retexture on the model again? and keep the model and anims as they were". The 2026-11-11 rebuild
([mm6_wwf_rebuild_claude](../mm6_wwf_rebuild_claude/README.md): MM9 BIGFOOT skeleton and clips, plus its fur-tone
follow-up) was taken out:

- Reinstalled `mm6_wwf_rebuild_claude/work/before_rebuild/mm6_wwf.glb` with `tools/install_model.py --world mm6`;
  sha256 `b6bd5fa7…` equals `audit_mm678_20261111/compare_viewer/before/worlds/mm6/models/mm6_wwf.glb` (the HEAD
  original), and the cooked runtime copy equals HEAD's `assets_dev` file (`d368d5ce…`).
- `assets_dev/worlds/mm6/models/actors.yml`: the Werewolf A/B/C entries restored from
  `work/before_rebuild/actors_mm6.yml` (byte-identical block: scale 145.1, Walk2/Run2/Sprint, `Spine02`,
  `[neck, Head]`, impact 0.331); the rebuild's three-line comment removed. Nothing else in the file was touched.
  (The file was replaced by temp file and rename, which broke its hard link with
  `output/studio_slice_root/worlds/mm6/models/actors.yml`; that copy still holds the rebuild bindings.)
- `game/outdoor/HeadlessOutdoorDiagnostics.cpp`: the rebuild did not touch it. The werewolf case
  (`mm6_werewolf_actor_model_tiers_share_the_native_height`) is a generic tier-height check with no working-tree diff.
- The rebuild's installed GLB and bindings are kept in `work/before_texpass/mm6_wwf_rebuild_installed.glb`,
  `actors_entries_rebuild.yml` and `actors_mm6_full.yml` in case they are wanted again.

## Texture quality pass on the original

Starting point: the reinstalled original, backed up as `work/before_texpass/mm6_wwf.glb` with its `actors.yml`
entries (`actors_entries.yml`). Only UVs, vertex splits and images changed. Mesh, rig, clips, materials, region ramps,
variants `wwf_a/b/c` and `actors.yml` are the original ones. Toolkit: `mm7_m218_texpass_claude/scripts/` (texpass-2,
with `detail_guard` and `head_uv_split`), config `texpass.json`.

**Cause.** One 2080×1024 set, body on the left half and the head set (head, jaw, teeth, mane; 22 % of the surface) on
the right at twice the body's density: 34.0 % atlas use, 1,012 islands, 17.2 % fragments, stretch p90 2.27.

**Route** (recipe [section 0](../claude_shared/TEXTURE_QUALITY_PASS.md#0-default-pipeline-since-2026-11-12-uv-study),
the 2026-11-12 defaults):
1. `dump.py`: LOD0 (6,489 triangles). The head is the old head set (`head_uv_split` 0.5), ×1.8, so body and head both
   about double their density. The hands are ×1.3.
2. `uv.py` (headless Blender). This copy adds one vertex group per joint, because PartUV's part tree is built from the
   vertex groups and the toolkit's mesh otherwise carries only HeadSet/Hands.
   - `uv_v1` (plain defaults): PartUV 728 charts, sparrow, 73.9 % atlas, but 14.8 % fragments. The mane tufts
     (closed 16–53-triangle pieces) were split into 5–22 islands each.
   - **`uv_v2`, the paid layout** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0`, the recipe's closed-piece
     setting): PartUV charts, seam pass, sparrow packing, no fallbacks; 426 charts, 76.0 % atlas, 6.9 % fragments,
     stretch p90 1.32. **Never re-run it.**
3. Meshy (backup account), meshy-7, 4K, our UVs:
   - `body_retexture_v2`: the original HD masters 01–04 from `mm6_wfigt1_claude/references_hd/`, 10 credits;
   - `head_retexture_v2`: the head turnaround with the charcoal mane (`references_head/meshy/`) on the head faces,
     10 credits.
   - The returned GLB measures the same layout as the upload.
4. `resample.py`, `bake_ao.py` (reach 0.035), then `compose.py` at the defaults (sigma 4, detail 0.9, tone curves per
   class: shorts, gem, rest). Rounds:
   - r1: the yellow eyes lost their sharp highlight and became a soft yellow smear;
   - r2: `keep_approved_near` keeps the approved eyes (two 2.5 cm spheres at the painted irises);
   - **r3, installed**: also keeps the pendant (5 cm, 134 triangles, no fur). The new paint had put a pale teal fringe
     on the pendant's back faces in every tier.
5. `gutter_fill.py work/uv_v2.npz` on colour, normal, metal/roughness and region mask (in place), then `apply.py`:
   LOD0 layout; LOD1 projected per chart; shadow LODs follow; LOD2/LOD3 keep their own UVs and maps, refilled from the
   new LOD0 at 512/256 px.

## Results (`texture_quality.py`, `Werewolf_A`)

| | Before (2080×1024) | After (2048²) |
|---|---|---|
| Atlas | 34.0 % | **76.0 %** |
| Equivalent px | 1,214 | 1,786 |
| Density p10 / p50 / p90 | 368 / 524 / 1,089 | 1,095 / 1,184 / 2,109 |
| Density per part (p50, texels/m) | body 337, head 673 | body 742, head 1,335 (spread 1.20 each) |
| Islands / fragments | 1,012 / 17.2 % | 433 / 6.9 % (head mane tufts 4.2 %, whole pieces under 8 triangles 2.4 %) |
| Stretch p90 | 2.27 | 1.32 |

The fragments stay above the 3 % target: they are mane cards and loose small pieces, a mesh issue (the recipe's
hair-card exception).

**Tone** (sRGB, approved -> pass, area-weighted): shorts (133.2, 92.3, 59.3) -> (132.9, 92.1, 59.3), luminance sd
29.3 -> 32.0; fur and the rest (51.4, 50.4, 48.5) -> (51.4, 50.4, 48.5), sd 35.7 -> 36.7; the gem and the eyes keep the
approved colour. Tier ramps are unchanged, so rust/navy/red shorts and the teal/red/blue gems are as approved. The
normal is Meshy's, tilt scaled 0.369 to the approved p90.

**LOD colour error** (mean / p99, installed -> pass; `lod_check.py`): LOD1 3.4 / 38.4 -> 4.9 / 53.8; LOD2 3.8 / 35.4 ->
8.0 / 40.5; LOD3 6.8 / 42.3 -> 9.2 / 43.5. The mean colour of the LOD2/LOD3 images is unchanged (LOD2 69.2/60.8/51.7 ->
69.5/61.1/51.8). The higher error is LOD0's new fine fur detail, which the far LODs cannot carry, not a tone shift.

**Look** (identical cameras, all three tiers): face, yellow eyes, nose, teeth and tongue, gold necklace, pendant,
ivory claws and the dark grey-black fur read as approved. The fur strands on the head, chest and limbs and the shorts'
weave are crisper. Small drift: the inner ears are a little greyer (the approved paint had a faint pink).

Sheets:
- [review/texpass_sheet_wwf.png](review/texpass_sheet_wwf.png): forehead close-ups, top, side and full body, every
  tier.
- [review/texpass_face_sheet_wwf.png](review/texpass_face_sheet_wwf.png): face front, 3/4 and side, and the chest,
  every tier.
- [review/cmp_pendant_r3.png](review/cmp_pendant_r3.png): the pendant.
- Earlier rounds are in `review/r1/` and `review/r2/`.

## Checks

- `glb_diff`: OK, only UVs, vertex splits (LOD0 7,570 -> 8,544, LOD1 3,782 -> 4,249) and images (2080×1024 -> 2048²).
- Winding: 0 inverted closed parts. Flat shading: 0.01.
- Motion audit (`audit_before/`, `audit_after/`): every clip identical except Attack `accel_p99` 161.4 -> 162.4
  (the seam vertex splits).
- Floor (`Werewolf*`): 3 bindings, 0 problems.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS (647 descriptors on 185 models). Whole `actors` suite
  (`work/actors_suite.log`): 191 passed, 2 failed, `mm6_werewolf_actor_model_tiers_share_the_native_height` PASS. The two
  failures are not this model: `every_map_loads_and_builds_its_actor_models` lists 42 MM9 maps with actors without
  models, and `out05_event_clearance_completes_from_monster_killed_hook` is an event/quest check that fails again on a
  re-run.
- Project viewer `review/viewer/` (`run_creature_review.py check`): 66 switches, 0 console errors.
- Compare viewer, rebuilt with `compare_viewer/build.py`
  (<http://127.0.0.1:8912/level_generation/creatures/audit_mm678_20261111/compare_viewer/#mm6_wwf>): the left side is
  the original (`b6bd5fa7…`), the right side the pass, with the same bindings on both sides; `check_viewer.mjs`:
  36 switches, 0 console errors.

Installed 2026-11-12 with `python3 tools/install_model.py level_generation/creatures/mm6_wwf_texpass_claude/export/mm6_wwf.glb --world mm6`.
To return to the untextured original: `python3 tools/install_model.py level_generation/creatures/mm6_wwf_texpass_claude/work/before_texpass/mm6_wwf.glb --world mm6`
(`actors.yml` unchanged by the pass).

Meshy: **20 credits** (body 10, head 10), backup account 455 -> 435.

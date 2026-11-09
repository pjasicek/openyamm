# MM6 Bloodsucker: head texture set and maw rework (installed 2026-10-14)

User (2026-10-14), after the 45 % reduction review: the attack "scare" maw disc was weirdly visible, and the head (the
mouth interior) looked weak; agreed: fix the maw and give the head its own texture set (one Meshy head retexture).
Base: the installed reduction (`../mm6_bld_reduce_claude/`, Cand_45) in a copy of the animated master
(`../mm6_bld_claude/work/anim_v1.blend`: rig and procedural clips). Body texture set unchanged.

## What was wrong with the maw

The old maw was a flat disc on a `Maw` bone (child of Head) that pointed straight ahead, 9 degrees off the tube's
opening, and rested at 0.55 scale with its rim 6-8 mm in front of the lip: a tilted plate always poked out of the
snout. At the attack peak (x4.84) it stayed a flat plate, and its art was a 0.1 x 0.1 corner of the 2K body texture.

## New maw (scripts/build_master.py)

The restored attack frames (`../mm6_bld/trimmed_2x/bldatt[a-f]0.png`) show the head thrust at the viewer in b-c: a
round oral disc facing the camera (thick green hide rim with ivory hooks, red ring, radial teeth converging on a dark
throat), not a separate cone. A first version here (a deep funnel growing into the throat) read as a megaphone and,
from the front, showed only its stretched outer band around the tube end; user: "was this cone intended?" (no).

- Oral disc: a shallow dish (2 cm radius, 5 mm deep at scale 1) on the tube's own axis, 1 mm in front of the most
  forward head vertex so it covers the snout end at full gape, with a thick rounded hide rim behind it; 360 tris.
- Maw keys remapped from the old opening amount: scale 0.01 (hidden in the mouth) in Fly and Fidget; grows to the old
  attack span (0.25 m radius) with the depth growing to about half of it, so the side view reads as a lip ring.
  Radial peaks: Attack 12.5, Death 4.17, Hit 2.25, Dead 0.81.
- As it opens, the disc also slides forward along the mouth axis by its dish depth plus 15 mm: the flared snout prongs
  sat in front of the recessed dish centre and showed through it (user, attack front view). Gate
  `scripts/check_maw_cover.py`: no head vertex inside the open disc's footprint in front of its face in any frame of
  Attack, Hit, Death or Dead (worst margin 2.5 mm).
- Art: `references_head/04_maw.png` (Codex, from the native attack frames) on a round island of 20 % of the head atlas;
  the rim samples its outer band.

## Head set

- Head faces: mostly weighted to Neck2, Head, Mouth or Maw (eyes included), 1,245 tris of 5,210. UVs from seams (lip
  between tube and throat cup, underside midline) and an angle-based unwrap: one sleeve, the throat cup, the spikes,
  the maw island (smart projection gave ~150 islands on the decimated head).
- References: `references_head/` (Codex head turnaround from the accepted HD masters + the maw; 1254 px returns).
- Meshy `head_texture` (`requests/head_texture.json`, `enable_original_uv`, 2k): 10 credits; UV parity exact
  (2,655 corners).
- `scripts/compose_head.py`: regions from the new colours (teal hide -> body, salmon throat/underside -> maw, maw island
  -> disc; ivory and eyes in none). Body region luminance matched to the installed tier-A body by the rank of the
  smoothed luminance (bands, not noise, take the dark tones), detail on top; the maw art keeps its contrast with one
  gain to the old disc median. Eyes: Meshy painted none; round orange eyes (pupil, iris, rim) where the installed model
  had them (`scripts/find_eyes.py`), outside every tier region. Maps padded before the 2K -> 1K downsize.
- Body base colour drops to 1K beside the 1K head set (texture guide; `merge_head_material.py` needs equal sizes).
  Tiers: body and head entries in `textures/bld_ramps.json` with identical ramps; the head merges into the body
  material (one draw).

## Runtime (scripts/build_runtime.sh)

export -> prepare -> LODs **5,210 / 2,601 / 895 / 261** -> shadow LODs tucked in (`shrink_shadow_lods.py`, which the
generic reduction route had skipped for the installed r45) -> region variants -> head merge -> collapsed-mesh check
(none: the maw is part of the body mesh) -> `export/mm6_bld.glb` (7.1 MB, installed r45 7.0 MB).

## Review

- Viewer `review/viewer/` (installed r45 vs head set, A/B/C, all clips): `check_viewer.mjs` 36 loads, no errors.
- `review/compare/maw_sheet.png` (rows A/B/C now/new; Attack front, three-quarter and side, Hit, Death, Fly),
  `review/compare/tiers_sheet.png` (earlier funnel version), `close_sheet.png` (head close-ups),
  `review/master/sheet.png` (maw test pattern in every clip, head UV layout).
- Viewer fix: `viewer_variants.py` resized the RGBA region mask as one image, which premultiplies by the alpha
  (region 4) channel and zeroed the other regions whenever mask and base sizes differ, so every earlier "installed"
  viewer model showed tier A colours for B/C. Fixed per channel here, in the template
  (`../mm6_wdm_reduce_claude/scripts/`) and in this session's reduction projects; the engine was never affected.

## Installed

User accepted (2026-10-14). Previous source (the r45 reduction without the head set) backed up to
`work/mm6_bld_source_pre_head.glb`; installed with `tools/install_model.py` (runtime back-face pass: 657 back copies,
5,567 runtime triangles). No bloodsucker-specific regression case exists; the `actor_model` cases were run after
install. Ledger row updated.

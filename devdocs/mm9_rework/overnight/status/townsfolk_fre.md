# Fre (MM9 row 256, FRE.abc / Fre.dtx) — status

- Project: `level_generation/creatures/mm9_fre_claude/`, lease `mm9:fre`, owner fre-20261104 (claimed 2026-11-04 06:12 UTC).
- Brief: `devdocs/mm9_rework/overnight/FINISH_BRIEF_20261104.md`, Job 4.
- Phase: investigation (mesh comparison, MM9 renders, DAT scripts).
- Route (decided 07:20): variant of the PeasantF4 body (`mm9_meshcmp.py`: PeasantF4 -> Fre all regions <= 3.6 cm, same 73-joint skeleton
  and binds; Fre adds a hair cap and one braid, no hood). F4's frozen asm copied into `work/f4/` (read only); F4's hood replaced by a
  hair cap (component hood4) and a braid. Clips: F1/F4's PeasantFemale set (NPC337.scr plays none of its own). Cap 20 credits.
- PeasantF4 job 8 fixes (sleeve tube winding, bodice eyelet holes, peplum spikes) applied from snapshots of that agent's scripts.
- Codex masters done 07:45 (body 4 on F4's masters, head 4 painted over renders of our head).
- Meshy 08:0x: body retexture 4K `fre_body_tex_4k` (10) and head retexture 4K `fre_head_tex_4k` (10); backup 2305 -> 2295 -> 2285.
- 07:49 both Meshy jobs SUCCEEDED (10 + 10 consumed). Builds r1-r5 in the review viewer: under-jaw shading (geometry, F4's carved chin;
  the paint there is skin), cap-edge skin teeth -> hair, hair toned to MM9's chestnut, feather paint on F1's puffed upper sleeves -> red cloth
  patch from the skirt, flat yellow back collar -> feather patch, hem lowered over the collar, rim/lining along the face opening dropped.
- Gates r5: arm/hand 0 frames > 1 cm (Cower forearm 2.4 cm = F4's bell on the bust), jitter 0, robe 0, sleeve poke 0, braid 0,
  flat 0.00/0.01, bones 0, detached = 2 legs (as F1/F4), texture body 69.6 % / head 60.9 % (frag 1.8 %, stretch p90 1.47).
  Cap hem vs body (F4's hood metric) 2.1-2.9 cm: investigating with a ray-based poke gate (body showing through the hair).
- r6-r20 (09:xx): cheek line traced (Meshy's own faint projection seam, made solid by sym_paint and a gutter pass of mine: both fixed;
  back to Meshy's faint level, not gone). Final r20 installed: sha256 02437871...5989 (= export). Bound `MM9 256 Fre` (actors.yml block
  mm9_fre_claude), row 256 in mm9_npc_actor_rows.tsv (fallback 352), tables regenerated (250 rows); binding regression PASS (250
  descriptors on 112 models, 0 failed); floor audit ok; viewer check 11 switches, 0 errors. Map placement is the orchestrator's.
- See-through (r6 geometry = r20): head 65/27 px, torso 1596/50, sleeve L 2004/40, collar 974/63, sleeve R 7/44, boots 0 (el 0/20; worst
  Death from the feet up the hollow dress, as F1/F4).
- Cap poke (r6): 0 mm in 8 clips; Talk 11.9 mm, Cower 7.2 mm, Conv1 2.3 mm (neck through the hair's lower edge in head turns). Open.
- Final gates r19/r20 (same geometry/weights): arm/hand 0 frames > 1 cm (Cower forearm 2.4 cm), jitter 0, robe 0, sleeve poke 0, braid
  0 except Hit 1.9 cm (2 frames), old hood out 0, cap hem metric 1.0-2.9 cm (fails), cap poke Talk 11.9 / Cower 7.2 / Conv1 2.3 mm (fails),
  flat 0.00/0.01, bones 0, detached 2 legs, winding 0, texture 69.6 % / 60.9 %. Open: cheek line, cap poke. README complete.
- Lease released (see below).
- 08:29 pass 2 (orchestrator pre-screen r20): cheek/neck lines, under-jaw wedge, chin V, forearm tube back views. Lease re-claimed.
- PASS 2 done (r36, 0 credits): cheek/neck lines healed (screen-space probe -> texel map, base + normal), under-jaw normals turned forward
  (UCHIN 1.5, positions untouched), chin/lip specks mostly cleaned (1-2 px dot left at the chin point), forearm tubes clean from behind in
  5 clips (part-colour + magenta back-face renders), F4's final bodice_fix (r41) taken. Installed r36 sha 990ccb7e (= export), binding PASS
  252/114, floor ok, viewer 0 errors. Gates r36 as r19 (arm/hand 0 frames > 1 cm, jitter 0, robe 0, sleeve poke 0, flat 0.00/0.01, bones 0,
  detached 2 legs; braid Hit 1.9 cm 2 frames; cap hem metric 1.0-2.9 cm and cap poke Talk 11.9 / Cower 7.2 mm still open). Lease released.
- 11:20 pass 3 (user review r36): face shading panels, hair cut into the face. Lease re-claimed.
- PASS 3 done (r43, 0 credits): smooth-falloff under-chin normals (no region boundary); hair cap drawn back (ear-lobe height at the sides,
  nape 0.595 m) on the same topology/UVs, braid root into the cap, old hood outside it dropped/pulled in; newly bare jaw/neck repainted as
  skin (expose_skin_fre.py) with chart-own gutters. Installed r43 sha ad6b6174 (= export), binding PASS 252/114, floor ok, viewer 0 errors.
  Gates: arm/hand, jitter, robe, poke, braid 0; cap poke Talk 10.3 / Cower 8.7 / Fidget 7.5 mm (open). Lease released.
- 11:55 pass 4 (orchestrator r43): real hair (transplant PeasantF2's hair), cap poke 0, jaw smudges. Lease re-claimed.
- 13:55 pass 4 in progress: PeasantF2's hair (cap + braid, its UVs and paint) transplanted as part 'hair2' (`build_hair_fre.py`), rim
  pulled onto the face outline and smoothed, recoloured to Fre's auburn with the circlet re-painted from the old cap (`hair_tex_fre.py`),
  old-bob AO and paint healed (`ao_lift_fre.py`, `seam_skin_fre.py`). Viewer r52/r53 under review; not installed yet.
- PASS 4 done (r62, 0 credits): PeasantF2's hair (cap + braid, its UVs and paint) transplanted as 'hair2'; rim pulled onto the face
  outline (max 25.8 mm, median 11.2 mm; skull rows under the cap moved <= 24.5 mm), recoloured auburn, circlet repainted, soft 8 mm
  hairline; temples/jaw sides healed from the cheek skin (one smooth 3D-weighted heal, AO to 1). Cap poke 0.0 mm in all 11 clips; other
  gates 0 as before. Installed r62 sha 6cf1b266 (= export), binding PASS 252/114, floor ok, viewer 11/0. Sheets
  level_generation/creatures/mm9_fre_claude/review/faces/r62_face.png, face_r43_vs_r62.png, review/mm9_vs_ours_r43_r62.png. Lease released.
- 19:43 pass 5 (orchestrator r62: temple/face-side shading patches). Lease re-claimed.
- PASS 5 done (r72, 0 credits): temple/face-side paint healed as one smooth 3D-weighted area (unlit smooth), hair moved out to her head
  instead of her face in (max 12.4 mm), rim normals onto the skin, flipped normals fixed, bob AO removed. Residue: pale angular area at
  the temple and dark shards below the ear in Talk only (lighting on the face-shell outline geometry); stopped iterating as asked.
  Cap poke 0 in all clips, other gates 0. Installed r72 sha aabcf1a4 (= export), floor ok, viewer 11/0. Binding regression blocked:
  game fails to load worlds/mm9/modifiers.yml:33 (evade_min_seconds, not Fre's change). Lease released.
- pass 6 (orchestrator r72: rebuild the side-of-head strip). Lease re-claimed.
- PASS 6 stopped (user: new head by a fresh agent). Nothing installed; r72 (aabcf1a4) stays. Lease released.

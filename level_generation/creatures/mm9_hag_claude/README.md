# MM9 Old Hag, Hjordisa (mm9_hag) — 3D actor on the approved Yrsa body, 2026-11-02

MM9 `MONSTERS.txt` row 245 "Old Hag" (`hag.abc`, skin `hag.dtx`, IsMonster 0, Scale 1). One DAT object: `OldHag` in Guberland
(script `NPC132.scr`, Hjordisa the Hag: `OnDamage` -> `die`, `OnUse` -> `DoRude 132`; it plays no other animation). Built as a
shared-mesh variant (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`): the approved Yrsa body, rig, weights and clips
(`../mm9_yrsa_claude/`, read only), with the Hag's two geometry differences and her own paint. Own GLB `mm9_hag.glb`.

## What differs from Yrsa in MM9 (measured)
`meshcmp.py yrsa:hag` (region surface distance) and per-bone vertex distances (`review/mm9/` renders: `yrsa_vs_hag.png`,
`heads_yrsa_vs_hag.png`, `arms_yrsa_vs_hag.png`, `skins_yrsa_hag.png`):
- **Skeleton and clips**: same 73 joints; binds identical except the braid chains (`xpony*`, up to 3.3 units) and Ponytail11/12 (0.2).
  The five shared clips (`walk`, `stand`, `fidget1`, `Wince3`, `Die3`) are byte-identical (every key, every node); `hag.abc` adds a static
  `hag1`. In bone-local space the Hag's braid vertices are within 1.6-3.5 cm of Yrsa's, so the posed braids are the same: Yrsa's braids kept.
- **Sleeves**: bell sleeves. The forearm pieces have 4 more vertices; the lower back of each cuff hangs out by up to 9.7 cm.
- **Head**: no forehead band of beads (the skin has none); 8 temple-hair vertices differ by 2-4 cm (kept as Yrsa's hair).
- **Torso, legs**: identical (p90 0.0 cm).
- **Skin**: ginger hair and ginger braids, an olive-ochre hood, a golden damask (swirl) bodice and overskirt, navy-black sleeves and lower
  skirt, the same dark woven yoke, collar of teeth, boots and hands; a different, paler face. A new body paint, not a recolour.

## Route (0 + 20 Meshy credits)
1. Baseline: `v2/work/yrsa_sleeves_v2.blend` (copy of Yrsa's approved master) rebuilt with Yrsa's own runtime script in this project ->
   byte-identical to the installed `mm9_yrsa.glb` (proves the copied route).
2. `scripts/hag_geo.py` -> `v2/work/hag_geo.blend`: the 8 bead parts deleted; both sleeves flared (shell, lining and cuff rim move together by
   position along the forearm axis, so the 3 mm lining gap holds; smoothstep from 9 cm along the forearm to the cuff, +1.2 cm all round
   plus up to 9 cm where the cuff faces MM9's hang direction, back and down): 9.7 cm left, 8.9 cm right (`v2/work/hag_geo.json`).
   Weights, UVs, hands, head unchanged.
3. Texture-pass UVs (the shared v2 scripts): `texpass_uv.py` (body, atlas 62 %) and `texpass_head_uv.py` (head square) ->
   `v2/work/texpass_head.blend`, uploads `v2/texturing/hag_*_texpass_upload.glb`. **Never re-run** (the paints belong to these layouts).
4. HD masters (Codex, one run, brief `references_hd/CODEX_BRIEF.md`): four body views on Yrsa's approved masters as the shape authority with
   the Hag's colours from MM9's renders and skin, and a four-view head turnaround on Yrsa's head masters (same face structure, ginger hair, no
   bead band). Alpha halos cleaned (`scripts/clean_alpha.py`, `*_clean.png`).
5. Meshy (backup account): body retexture 4K `hag_body_tex_4k` (10) and head retexture 4K `hag_head_tex_4k` (10); balances seen
   3225 / 3215 before the jobs.
6. Maps: `bake_ao_texpass.py`, `compose_texpass.py`, gentle grade (`grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5
   --contrast 1.06 --saturation 1.15`) -> `textures/hag_tp_*`; `compose_head_texpass.py yrsa hag_tp` (head square from the new paint,
   Yrsa's hand texels kept) then `scripts/hand_tone.py` (hands toned to the Hag's paler face by the ratio of the two faces' cheek colour
   on identical close-ups, x1.22 / 1.30 / 1.17, times 1.1 = x1.35 / 1.43 / 1.29) -> `v2/textures/hag_tp_head_*`.
7. Runtime: `PYGLTF_PYTHON=../claude_shared/gltf_venv/bin/python TOKEN=<lease> BLEND=v2/work/texpass_head.blend BODYTEX=hag_tp
   HEADTEX=hag_tp v2/scripts/build_runtime_v2.sh hag Hag v2/scripts/roles_yrsa_v2.json [--install]` (Yrsa's clips, hand rest
   `v2/scripts/hand_rest_hag.txt` = Yrsa's, floor fixes, LODs, winding). LOD0 8,477 triangles (Yrsa 8,676 minus the beads).

## Gates (final GLB, `v2/review/gates/`, `scripts/gates.sh`)

| Gate | Hag | Yrsa (approved) |
|---|---|---|
| `arm_hand_gate.py --outer-only --exact` (48 fps) | hands 0 frames > 1 cm in every clip (worst Death L 1.0, Fidget L 0.6); forearm cloth worst 6.0 cm Fidget L (as Yrsa), Walking/Running R 4.9 cm (Yrsa 1.3: the flared cuff's hanging point brushes the skirt on the back swing, cloth on cloth) | hands 0 frames > 1 cm |
| `jitter_gate.py` vs the raw MM9 clips | 0 fails | 0 fails |
| `sleeve_gate.py` (poke / see-through px) | poke 0; see-through within 0-11 px of Yrsa's per clip and view (Walking L above34 29 vs 18) | |
| `see_through_gate.py` (pdm2) hole max px | torso 265, head 188, sleeve L 89, sleeve R 16, collar 2, boots 0 | identical: 265 / 187 / 88 / 15 / 4 / 0 (`v2/review/gates_yrsa/`) |
| `detached_parts_audit.py --fps 48` | 0 detached | 0 |
| `flat_shading_check.py` | 0.00 / 0.00 | |
| `check_winding.py` | 0 inverted | 0 |
| `texture_quality.py` | body atlas 62.4 %, density p10/p50/p90 957/979/1000, spread 1.04, fragments 0.3 %, stretch p90 1.12; head set 44.5 % of the 2K (the head square plus Yrsa's hand squares), spread 1.11, fragments 0.6 %, stretch 1.27 | body 29.5 %, spread 2.08, fragments 9.7 % |
| `floor_audit.py --world mm9 --match 'MM9 245*'` | stand 0.0, walk -0.3..+0.2, living -1.9, dead 0.0: ok | the same |
| `mm9_actor_models_build_every_binding` (`--world mm9`) | PASS, 194 descriptors on 84 models, 0 failed | |
| Viewer `run_creature_review.py check` | 7 clips, 0 failed, 0 console errors (`review/viewer/`, revision r2-20261102) | |

The see-through holes are Yrsa's (approved) at the hood edge, the hair and the dress shell in the fall; the Hag adds none. Not lined in
this pass (it would change the approved body's look; see open points).

## Sheets (read)
`v2/review/r2/before_after_sheet.png` (MM9 Yrsa, MM9 Hag, our approved Yrsa, our Hag: five views each),
`v2/review/r1/mm9_vs_ours_r1.png` (MM9 vs ours, full and head), `v2/review/r1/face.png` + `face_detail.png` (front, 3/4, both sides, eyes,
mouth, both neck sides; bind and Fidget), `v2/review/ears_sheet.png` (both ears, under the jaw, party view), `v2/review/r1/cuffR.png`
(the bell cuff in bind, Walking, Fidget, Hit, Death, Standing), `v2/review/geo/sleeve_flare_v1.png` (cuff before/after the flare),
`v2/review/gates/sleeve_gate_*.png`, `see_through_*.png`, Codex masters `references_hd/selected_views_review.png`,
`v2/references_head/selected_views_review.png`.

## Binding
`assets_dev/worlds/mm9/models/actors.yml` block `mm9_hag_claude` (`scripts/bind_actors_hag.py`, under the flock via
`scripts/bind_under_lock.sh`): `MM9 245 Old Hag`, scale 100, Yrsa's animation block and clips (talk -> Fidget). Row 245 added to
`tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visual 307, as Yrsa), tables regenerated. Map placement (the Guberland
`OldHag` object) is the orchestrator's switch.

## Approved Yrsa unchanged (proof)
sha256 before and after this run: `assets_source/.../mm9_yrsa.glb` 5f601016...071f2 and `assets_dev/.../mm9_yrsa.glb` 188d2e2e...3fd7
identical (`work/approved_sha_before.txt`); every file of `../mm9_yrsa_claude/` hashed before and after: identical; the `MM9 254 Yrsa the
Troll` binding block identical. Nothing was written into the Yrsa project (its blend and scripts were copied here).

## Deviations and open points
- **Bell sleeves** are a deformation of Yrsa's sleeves (no new topology), so the hanging point is a smooth flare, not MM9's sharp triangle.
- **Hood lump beside the right jaw**: Yrsa's hood geometry (approved, asymmetric) hangs there; the Hag's paint makes it olive knit.
- **Mouth**: Yrsa's grin slit with a thin painted teeth line (MM9's Hag grins with teeth); no pink plate.
- **Hands**: Yrsa's MPFB hand skin toned to the Hag's face (x1.35 / 1.43 / 1.29); slightly darker than the face in close-ups.
- **Navy** reads nearly black under the viewer's light (MM9's is a dark blue).
- Material class map: `compose_texpass.py` classed most of the golden damask as metal (Meshy's metallic map); ORM blue and metallicFactor are
  0, so nothing renders as metal; the class map is a record only.

## What was not checked
In game (the maps do not place descriptor 245 yet); motion by eye at normal speed (strips and gates only); LOD1-3 by eye.

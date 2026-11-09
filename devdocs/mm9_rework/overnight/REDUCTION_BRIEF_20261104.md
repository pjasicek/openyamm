# MM9 triangle reduction of approved models: batch brief (2026-11-04, user request)

The user asked to run the triangle-reduction route over the MM9 models they have approved, about five at a time, and to keep
it tracked so sessions do not mix it up or miss a model. **The single record is the "MM9 reduction" section of
[REDUCTION_LEDGER.md](../../../level_generation/creatures/REDUCTION_LEDGER.md)**: one row per GLB, heaviest first, with
status, counts, project and rollback source. Every agent updates only its own rows, inside
`flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock` (re-read the file inside the lock, edit one row,
write with a temp file + rename; several agents share it); the orchestrator assigns rows and records the
user's review. A model that is not "approved" on the overview page (`status:'ok'`) is not reduced; models approved later are
appended to the queue.

## Order (user, 2026-11-04)
"The special/unique NPCs — I don't care much about them, they can be higher tris. The monsters though need to be tris reduced
since I will encounter a lot of them." The ledger's Prio column: 1 = monsters (heaviest first), 2 = townsfolk and animals,
3 = unique NPCs and one-off bosses (`deferred`, only on request). For monsters, which appear many at a time, a real cut matters
more than for a one-off; Igrid (unique) came out `kept` because her protected parts were 80 % of the mesh: measure the
protected share first and say early if a model cannot reach ~15 %.

### Prio-2 townsfolk (from 2026-11-04 evening)
The relaxed keep set below applies to prio-2 townsfolk too (they stand in numbers in the cities), with the face kept exact as
always. One agent per GLB family: bodies that share a mesh (dwarf women DF1/2/4, girls human + elf, HOF1/HOF2) are reduced once
and the variants re-derived from that cut, so all of them stay consistent. Monsters left after the light-body findings: the ten
bodies under 7.5k built with `reduce_body.py` are recorded `kept (not run)`.

### Prio-1 monsters: relaxed keep set (orchestrator, 2026-11-04, after Igrid and Ebora came out `kept`)
The full keep set below protected 65-80 % of those meshes. For prio-1 monsters only:
- **Still exact:** the face skin (eyes, lids, brows, nose, mouth, lips, teeth/tusks, ears, jaw, chin) and the neck seam.
- **May be cut:** hair, hood, beard and mane shells and their back copies (0.6-0.8, judged at party distance and in the front
  close-up: no holes, no hard steps); hands at 0.6-0.75 keeping every finger, the grip contact and the hand-graft junction;
  linings and rim strips may be dropped over the cut cloth and rebuilt from the reduced outer shell (offset copy, same weights;
  `meshy-cloth-lining` memory route) instead of kept; wing membranes, cloth chains and other helper-driven parts reduced in a
  separate pass that keeps every vertex the helper bones weight heavily.
- **Simple-shaped props and rigid pieces** (weapons, shields, plates, buckles): rebuild them low-poly from measurements and
  projection-bake their colour/ORM/mask/normal from the installed piece onto new UVs, rather than decimating them: the Giant's
  mallet went 3,506 -> 532 with no visible change and the model 15,670 -> 9,480 (`mm9_giant_reduce_claude/README.md`, pass 2).
- **Cloth that is flat at rest but curves in motion** (cloaks, dresses, wings): the MeshLab ladder judges the rest pose and fails
  the clips; use `mm9_banshee_reduce_claude/scripts/mpqem.py`, which scores each collapse over poses from every clip and only
  removes vertices (kept vertices keep position, UV, normal, weights). Banshee 14,994 -> 11,378 with every gate kept.
  The Highwayman's copy (`mm9_highwayman_reduce_claude/`, 13,094 -> 9,916, every gate equal or better) adds lining faces rebuilt
  from the cut outer cloth, a texture guard (a collapse is refused if the new face would show colours the source does not have
  there, in any tier) and whole-belt keeps: prefer it as the starting point for clothed humanoids.
- **UV triangles leaving the painted charts** (Mummy, 2026-11-04): a collapse can make a new face whose UV triangle reaches off
  its chart into gutter or another chart; the colour texture guard and a stretch guard both missed 204 such faces (a smeared
  chevron on a forearm). Keep every new face's UVs on the source charts (`mm9_mummy_reduce_claude/scripts/uv_escape.py`) and
  run that check on every candidate before reporting.
- **Thin painted details smear** (strap rims, greave bands) at the decimator's default texture weight; raising the texture
  weight from 1 to 3-8 halved the smeared faces at the same count on the Trellborg (`mm9_trellborg_reduce_claude/`). Try that
  before drift locks, which only move the damage.
- **Painted motifs** may soften a little: judge them at party distance and in the viewer's standard 3/4, not in a texel crop.
- The stop rule still applies (silhouette, SSIM, deviation over every clip) and every gate must still pass after the lining
  rebuild. The user reviews side by side before anything installs.

## Why and how far
User rules (memory "triangle budget by complexity"): reduce LOD0 **until visuals or rig start suffering**, even well below 15k
(15k is a ceiling, not a target); about 5k for simple rigid bodies, about 5-8k for clothed humanoids is typical. The ladder's
measured stop rule (silhouette IoU, textured SSIM, deviation over every clip; `MM6_CODEX_BATCH_GOAL.md`) picks the step, then the
gates below must still pass. Expected: 12-16k humanoids down to roughly 6-9k, animals and simple monsters a little or not at all.

## Route: the playbook's no-retexture branch, on the installed source
Read [RETOPOLOGY_PLAYBOOK.md](../../../level_generation/creatures/RETOPOLOGY_PLAYBOOK.md) "Default route" in full, including
"No part to rebuild: skip the retexture", the weld-only-identical-weights rule, the coincident-seam rule (m492), the MM8 batch
lessons and every later section that applies. Reference scripts: `level_generation/creatures/reduce_installed.sh` (MM6, adapt the
paths to `assets_source/worlds/mm9/models/` and the project name) with `mm6_wdm_reduce_claude/`, `mm8_m492_reduce_claude/`
(exact weights, seam keep), `mm6_lzd_reduce_claude/` (soles locked, fitted LODs, gates), `mm6_gst_reduce_claude/` (protect
only the face), `mm6_kni_reduce_claude/` (weld, prune materials).
- Project `level_generation/creatures/mm9_<name>_reduce_claude/` per GLB family; source = the installed
  `assets_source/worlds/mm9/models/<file>.glb`, copied first to `<project>/before/` (the rollback source).
- **Keep every helper script and temp file inside your own project** (`scripts/`, `work/`), never in the session scratchpad: the
  agents share it, and one agent's ledger helper overwrote another's (Igrid's row landed on the Giant's, 2026-11-04).
- `export_cand.py` from the MM6 reference lifts everything below z = 0 to the floor; MM9 rigs often have the pelvis at the origin,
  so use the source's lowest point as the floor (`mm9_wyrdold_reduce_claude/scripts/export_cand.py`).
- pymeshlab lives in `level_generation/creatures/claude_shared/meshlab_venv/bin/python -I` (the old `/tmp` venv is gone).
- **No Meshy, no retexture, no repaint**: UVs, textures, tiers (`KHR_materials_variants`, region masks, ramps, per-tier head
  images) and clips stay byte-identical; only geometry changes. Carry the variants to every LOD (`carry_variants.py`) and check
  every tier in the viewer.
- **Faces are untouchable**: the user spent many rounds on every face. Keep the face/head skin exactly (the faces of the head
  texture set: eyes, lids, brows, nose, mouth, lips, tusks, teeth, ears, jaw, chin, neck seam) — `REA_PROTECT_HEAD`/`REA_PROTECT_FACES`
  with ratio 1.0 for the face; hair/hood/beard may take a gentle ratio (0.7-0.8) only if the head sheet shows no change.
- **Keep exactly** what fixes and gates depend on: hands and fingers (grips, MPFB hands), hand-graft junctions, cuffs and
  undersleeves, linings and rim caps (see-through fixes), soles, ear pieces, held props and their sockets, braids and their chains,
  coincident split seams. Reduce cloth, armour, body and hair masses.
- **LOD protection can silently miss:** `tools/build_actor_lods.py` matches protected points to 1e-5 m, but Blender's import can
  move vertices by ~1.3e-5 m, so nothing is protected (Lesser Demon LOD3 floated 8 cm). Snap each protected point to the nearest
  imported vertex first (`mm9_lesserdemon_reduce_claude/scripts/build_lods.py`) and verify LOD height and floor contact by number.
- Build LOD1-3 the way the model was built (fitted/trimmed LODs where the project did that); check every LOD's height and that no
  LOD face stretches in any clip; prune unused materials.
- Memory: every Blender or heavy Python job under `systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0`, one
  Blender per agent, `--threads 4`.

## Gates (must be no worse than the installed model)
Run on the reduced candidate whatever the model's own project ran and record before/after: arm/hand, jitter, see-through
(every clip), sleeve poke, robe/legs, prop/held-item, ear/cap poke, detached parts, bone length, winding, flat shading, floor.
Then the viewer check and the binding regression after install. Look yourself: viewer side by side (installed vs reduced) of
full body front/3-4/back in Standing and two motion clips, plus the face sheet (front close-up, 3/4, true profile, low 3/4,
party) for every tier — the face must be pixel-for-pixel the same apart from lighting on neighbours.

## UV chart audit is a hard gate (2026-11-04, after a rollback of 12 installs)
`level_generation/creatures/claude_shared/reduction_uv_audit.py <reduced.glb> <before.glb> --json out.json` must report 0
LOD0 faces leaving the painted charts before a candidate is "ready for review"; `install_reduced.sh` refuses otherwise. Full-body
side-by-side sheets do NOT show these faults (they are 1-5 cm texture wedges); the orchestrator pre-screen also reads the
candidate's close-up texture sheets. 17 of the first 30 installs had escaping faces, 12 visibly; those 12 were rolled back
(ledger) and get fix passes with the chart guard (`mm9_imp_reduce_claude/scripts/mpqem.py`).

## Review and install
**User, 2026-11-04 (after the first 23): "if they look the same then it is fine with me."** From then on the orchestrator
installs a candidate after its own pre-screen shows no visible difference (side-by-side sheets every tier, face unchanged, gates
no worse beyond single-frame noise), then tells the user; anything with a visible change still goes to the user first.

- The agent stops at a candidate: export, side-by-side reduction viewer (installed vs reduced, every tier), gates, sheets.
  Status in the ledger: **ready for review**. No install yet.
- The orchestrator pre-screens and shows the user; on the user's OK the agent (or orchestrator) installs with
  `tools/install_model.py` (check_winding first), runs the binding regression, and sets the ledger row to **installed** with
  date, after count, LOD counts and the rollback source.
- Mark the creature's own project README with a line "LOD0 reduced post-install on <date> by `<reduce project>`; a rebuild from
  this project must re-run that reduction" so a later fix does not silently restore the old mesh.
- If no step saves at least ~15 % of LOD0, record **kept (no useful gain)** with the ladder numbers and stop.

## Rules carried over
[RUN2_COMMON.md](RUN2_COMMON.md) hard rules (git, leases, installs only via the tool, safe deletes, kill only your own PIDs, read
your own sheets, final report) and the review server rule (http://127.0.0.1:8912/, do not start or kill it; at most 2 viewer shot
scripts at once). Lease identity `mm9reduce:<name>`; also check the creature's own `mm9:<name>` lease is free before touching its
installed file. No `game/`/`engine/` edits, no engine builds.

## Final report (short)
Per file: before/after LOD0 and LOD1-3, the picked ladder step and why, gates before/after, sheets read (absolute paths), the
reduction viewer URL, what to look at, what you did not check.

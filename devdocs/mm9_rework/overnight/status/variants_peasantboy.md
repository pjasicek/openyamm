# Variants: MM9 human boy family (PeasantBoy1 / PeasantBoy2 / PeasantBoy1e) — status

- Project: `level_generation/creatures/mm9_peasantboy_claude/` (README is the record), lease `mm9:peasantboy`, owner variants-d.
- Rows: 69 Commoner Child (Peasantboy1.ABC, skin PEASANTBOY1; DAT CommonerChildHumanChildA, 5 objects), 70 Townsfolk Child
  (Peasantboy2.ABC, skin PEASANTBOY3; no placed objects), 73 Commoner Child elf (Peasantboy1e.ABC, skin PEASANTBOY2; DAT
  CommonerChildElfChildA, 5 objects).
- Mesh check (`meshcmp.py`): Boy1 vs Boy2 head max 4.0 cm (5 % > 1.5 cm), body 0.3 cm; Boy1 vs Boy1e head max 1.8 cm + the
  14-vertex ear piece Boy_1a; PEASANTCHILDBOY (clip library) = Boy1 body + Boy_1a.
- Phase: **second pass done** (orchestrator review of r8, 2026-11-02): reinstalled, gates rerun, sheets read; README "Second pass".
- Credits: **45 / 60** (Smart Topology 5, body 4K retexture 10, head 4K retextures a/b/e 3 x 10; backup 3290 -> 3050, shared).
- Installed: `assets_source/worlds/mm9/models/mm9_peasantboy.glb` (variants pboy_a / pboy_b / pboy_e) and
  `mm9_peasantboy_elfears.glb` (row 73's ears, attachment on `Bip01 ElfEars`).
- Binding: rows 69, 70, 73 in `mm9_npc_actor_rows.tsv` (fallback visuals 166 / 167 / 340), tables regenerated (9069 / 9070 / 9073),
  `actors.yml` block `mm9_peasantboy_claude`. Map placement left to the orchestrator (stand-ins 166 / 340 still placed).
- Skeleton: MM9's 30-joint child skeleton + a static `Bip01 L Hand` (MM9 has no left hand joint) + `Bip01 ElfEars`. Clips: the
  PEASANTCHILDBOY library (stand, walk, run, Fidget1, conv1, hattack1, wince, die1, cower; Dead from die1).
- Gates (final): arm/hand 0 frames > 1 cm (all 10 clips, both hands); jitter 0 fails; sleeve poke 0 mm; detached 0; floor ok
  (69/70/73); winding 0 (body, ears); flat 0.00; bones 0 stretching; body atlas 63.3 %, head 43.8 %; viewer 30 switches 0 errors;
  `mm9_actor_models_build_every_binding` PASS (201 on 88 models).
- See-through NOT fully passed: torso slit at the belt in bent poses 95 px (party view 35), trousers up under the hem 25 px;
  sleeves 7, collar 6, boots 1-2. Details in the README.
- Open: pattern differences (b's open vest, e's trim, check on b/e trousers) not reproduced; boy a reads slightly
  parted-lipped; descriptor heights from the legacy stand-ins (160/160/106 vs MM9's 1.36 m boy); no game run.

## Second pass (2026-11-02), 0 Meshy credits
1. Back of head: no split in the mesh or paint; the "slit" was two mirrored side views side by side in sheet_ears.png. Proof
   `review/sheet_back_of_head.png` (3/4 back, back, top, Cower, Death; all tiers).
2. Nose: lighter mid-face half mirrored onto the darker (paint), needle-triangle streak on b removed.
3. Mouths: closed calm mouth painted on every tier (no teeth/gap/second lip).
4. Hands: one clean skin colour per tier from that tier's cheek (a 211/134/111, b 234/152/125, e 231/144/121).
5. See-through: dark backstop tube inside the waist + knee rim linings. Torso 95 -> 21 px (party view 35 -> 4) after the tube;
   final numbers in README / `review/gates/see_through_p3/`.
6. b/e trousers plain brown; b's open vest with a cream shirt panel (per-tier region mask, no Meshy job).
7. Correct descriptor body for 9069/9070/9073 by MM9's rule: **Height 133, Radius 26** (now 160/160/106). Not written.
- Installed export sha256 ebcae1094819...; ears unchanged cf923380686a... Binding test PASS (202 on 89 models; a first run
  failed on row 74, another agent's half-installed girl model, then passed). Floor ok, jitter 0, arm/hand 0, sleeve poke 0,
  detached 0, winding 0, flat 0.00. Viewer p3, 30 switches, 0 errors.
- Sheets: `review/sheet_before_after_p2.png`, `review/sheet_back_of_head.png`, `review/sheet_viewer_p2.png`, `review/tiers_p2.png`.

## Third pass (2026-11-02), 0 credits
- Mouths: pout geometry relaxed (`mouth_relax.py`), wide relaxed closed smile painted. Sheet `review/sheet_faces_p3.png`.
- Elf ears: only MM9 73 attaches them (69/70 never did); the a/b ears in tiers_p2 were a preview-render artifact; re-rendered.
- Boy b's nose stripe: geometry shading, not paint; left (smoothing opened a notch at degenerate midline slivers).
- Installed f11d12d36d38...; binding PASS; arm/hand, jitter, detached, winding 0; viewer p4 0 errors. Lease released.

## Fourth pass (2026-11-02, user mouth note), 0 credits
- Mouth: Meshy's loose lip pieces (the bulge and specks) deleted, one rose closed mouth painted on the shell's own lip line.
- Nose: midline slivers welded at the bridge top, bridge smoothed: stripe and diamond gone in the viewer light.
- Eye rims desaturated toward cheek skin. Sheet `review/sheet_faces_p4.png` (viewer lighting, MM9 side by side, before/after).
- Gates all 0 / PASS (binding 214 on 92 models). Lease released.

## Fifth pass (2026-11-02), 0 credits
- Lips sculpted (upper +1 mm, lower +1.8 mm, mentolabial dip, philtrum, corners tucked; `lip_sculpt.py`), lip paint with a
  cupid's bow, fuller lower lip and centre highlight, inner colour fading to skin; glabella smudge cleaned on a/e (and b).
- Sheet `review/sheet_faces_p5.png` (viewer lighting, MM9 side by side, before/after, zoomed after-front row).

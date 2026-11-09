# Townsfolk PeasantM1 (mm9_peasantm1_claude)

State 2026-11-01 ~22:45: **installed and bound**, lease released at the end of the run. README:
`level_generation/creatures/mm9_peasantm1_claude/README.md`.

- Rows naming PEASANTM1.abc: 43 Commoner (PEASANTM1A, DAT `CommonerHumanMaleA`), 56 Prisoner (PEASANTM1B, no placement),
  296 RailTest (PEASANTM1A, test row). Skins C/D are PeasantM1d's (sibling).
- Model `assets_source/worlds/mm9/models/mm9_peasantm1.glb`, variants `pm1_a` / `pm1_b`; LOD0 7,354 triangles.
- Binding: `actors.yml` block `mm9_peasantm1_claude` (`MM9 43 Commoner`, `MM9 56 Prisoner`, `MM9 296 RailTest`); rows 43/56/296 in
  `mm9_npc_actor_rows.tsv` (legacy 358/375/358), tables regenerated (168 rows). Maps still spawn the stand-in 358: the
  transcoder switch is the orchestrator's (brief, "Lessons from wave 1").
- Route: Annud's (PeasantMale skeleton + library), five Codex HD masters + two head turnarounds (A, and B as a different
  man), Smart Topology, fit + MPFB hands, uv_atlas body (59.1 %) and head UVs, three 4K paints, region mask + ramps (jacket,
  sleeve, trousers), tier B head image, hand rest on Talk/Conv4/Conv5/Bow, mirrored to true handedness.
- Clips: stand1, walk3, run, fidget1, conv2 (Talk), hattack1 (impact 0.5), wince1, die1, Dead; script clips cower, conv4,
  conv5, bow, stand -> Standing.
- Gates: hands clear except Conv5 L 1.9 cm on 15/1065 frames; forearms <= 3.5 cm except Fidget 5.7/6.0 (sleeve behind the
  open jacket flap); jitter: hand motion equals MM9's, 4 real upper-arm flags from the hand rest (Conv5 +3.44, Bow +2.12,
  Talk/Conv4 R +1.2 deg/f) + 2 shoulder-skin artefacts (Walking, Death); detached 0; flat 0; winding 0; floor ok; bones 1/12
  (L thigh, MM9's own data slides more); viewer check 0 errors; `mm9_actor_models_build_every_binding` PASS.
- Regression suite (first run, before the final texture-only reinstall): passed 191, failed 2 — `out05` (known) and
  `every_map_loads_and_builds_its_actor_models`: "mm9 bootcamp.odm: model image was not found:
  worlds/mm7/models/textures/b6bdcc0ff12f1558a747250d06abf6e9.oytex" (an MM7 model texture deleted in the working tree by
  other work; not this body).
- Regression suite on the final install: **passed 192, failed 1** (only the known `out05`); the earlier bootcamp/MM7 texture
  failure did not recur.
- **Meshy credits spent: 35** (5 + 10 + 10 + 10, backup account; balance was 3655 after the last job).

## Face fix r16 (2026-11-01/02, user: "looks like he has 2 eyebrows? and like weird eye area?")
- Causes: Meshy's recessed eye plate (a lit goggle whose rim read as second brows), a flat tan painted band and slit
  eyes (B: red rims), and the pale body-set chest skin under the jaw meeting the head set's neck cut as a hard panel.
- Fixed with 0 Meshy credits and one Codex run (eye-area repaint of an unlit front render, projected back):
  `eye_relax.py` (biharmonic fill of the eye plate, positions only), `codex_face.sh` + `warp_eyes.py` + `lid_lift.py` +
  `project_face.py`, `fix_neck.py` (seam lines), `fix_chest.py`. Installed (r16); rollback of r7 in
  `level_generation/creatures/mm9_peasantm1_claude/work/rollback_r7/`.
- Sheets read: `review/sheet_facefix_blender.png` (both tiers: front, 3/4, party view 22 deg above, eye close-up;
  before/after), `review/sheet_facefix_viewer.png`, `review/neck_facefix.png`.
- Gates identical to r7; binding test PASS (181 descriptors, after a transient MM9 36 sibling race in the full suite);
  full suite otherwise only the known `out05`.
- Left: A's upper lids read slightly lighter from the viewer's raised camera; a small stretched triangle at B's outer
  eye corner; a rust wedge on B's neck side in close-ups.

## Neck fix r17 (2026-11-02, orchestrator review of r16)
- Seam, rust patch and "bib" were paint, not geometry (shared boundary normals identical, 0 flat). The neck shell continues
  below the head cut into the body set, painted collar-olive (rust on B through the jacket mask) and pale chest skin.
- `fix_seam.py`: those body texels continue the head set's neck colour (detail kept), out of the jacket/sleeve/trouser
  regions, into a 4th region with per-tier skin ramps; `fix_neck.py` r17 tone-matches the whole lower neck with a smooth ramp.
- Installed r17 (rollback r16 in `level_generation/creatures/mm9_peasantm1_claude/work/rollback_r16/`); 0 credits.
- Gates identical; binding test PASS (182 descriptors); viewer check 0 errors.
- Sheets read: `review/sheet_neckfix.png`, `review/sheet_neckfix_viewer.png`.
- Left: faint light chart lines in tight neck close-ups; pale vein-like paint detail on tier A's chest in the shirt V.

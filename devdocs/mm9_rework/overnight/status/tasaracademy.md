# tasaracademy — overnight status: DONE (2026-10-30)

- **Phase:** done (definition of done in AGENT_BRIEF.md met; see "Not checked"). No process of mine running, no lock held.
- Project: `level_generation/projects/mm9r_tasaracademy/` (README.md), props: `level_generation/props/mm9_tasaracademy_claude/` (README.md, built by a sub-agent).
- Review root: tasaracademy.blv, scene, Lua, minimap line map, 64-sample bake (`stale_bakes.py --check`: not listed).

## Summary
- Faces 6 918; rooms 29 (+ sector 0); portal faces 34 (15 UserPortals, 7 door leaves, 6 archway cuts, 6 rect portals:
  the pit's mouth, five pen gates); movers 45 (38 dat, 6 rotate, 1 sink); ladders 2; lights 116 (+5 bake-only, 4 DirLights
  in the bake); decorations 304; chests 4; actors 26 (incl. the crate's hidden Dagrell).
- Scenarios (final build, real clicks): scenario_doors_exits PASS, scenario_chests PASS, scenario_scripted PASS.
  Compiler unit tests 21/21 pass.
- Reach: audit finds no cut-off region holding an actor (unreachable = bunks and daises). Dagrell probes: comes out of the
  store room to SecretDoor0's doorway after a party out of sight; the shut door holds it (control).
- Brightness: calibrated to the DAT lightmaps (x1, AGENT_BRIEF): per-zone texel ratio ours/MM9 0.89-1.21, hue B/R
  0.92-0.98 vs MM9's neutral 0.98-1.00 (profile direct 0.9, bounce 1, ambient 1.725 at sector light 31, sky 0.05).
  Info: screen means capture 64.3 / unbaked 51.2 / baked 54.5 (x0.85); views off the capture by >10 %: the library
  column (a22 x0.42, a19 x0.51, a18 x0.64; its MM9 lightmap is dark, ours x1.16 of it), west corridor/dormitory x0.66-0.67,
  east octagon x0.67, and others in review/brightness_v03.txt. No real MM9 screenshots of this map exist.
- Props workaround: sector minimum light 31 (`map.ambient`), ambient_scale raised so the bake is unchanged.
- Unmatched scripted objects: TaSarGuardDuty.scr walks (no marker paths), TaSarTeacher's attack animation,
  BookLetter.scr on three AIRails (invisible helpers), AmbientSound (9). Everything else is a native event citing its .scr.
- Sheets (looked at): review/v03_pages_p01-p13.jpg (original | unbaked | baked, 76 views), review/v03_compare.jpg,
  review/lighting_v03_compare.jpg, review/features02/ (flame card from the side, pen gates, skylights, trap doors).
- Not checked: trap doors / bookcase mid-motion on the desktop; arrival by walking Lindisfarne's ExitTrigger1; perception
  hints in a capture at exactly Perception 10; the sparring fight itself; combat AI beyond the reach probes; no real MM9 shots.

## Incidents
- ~22:50-23:10 the desktop game closed at startup in the review root ("Actor model load failed: worlds/mm9/models/actors.yml:
  invalid node; first invalid key: attack_ranged", another session's edit). Worked round once with a private hard-linked
  copy without actors.yml (output/mm9_rework/tasar_root, since removed); it cleared by itself afterwards.

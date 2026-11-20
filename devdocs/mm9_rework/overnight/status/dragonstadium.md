# dragonstadium (overnight map agent)

- Phase: DONE (2026-10-31), orchestrator wall review addressed (rebake v03)
- Record: level_generation/projects/mm9r_dragonstadium/README.md; props: level_generation/props/mm9_dragonstadium_claude/README.md
- Faces 1 480, rooms 3 (4 sectors), portal faces 2, movers 0, lights 3 (BLV) + bake-only sun, decorations 5,
  chests 2, actors 1 (Dragon King, immobile boss; Winged Mutants spawned by script, row 9160)
- Scenarios: doors_exits PASS, chests PASS, scripted PASS (real clicks on pillars and chests; trigger by walking)
- Compiler unit tests: openyamm_indoor_source_tests 21/21 pass
- Walls vs MM9 DAT lightmaps, vertical faces only (ours/MM9): bowl 0.85 -> 0.99 (arena sector level 18), entrance
  tunnel 1.04 -> 1.04, side tunnel 0.99 -> 0.99; floors bowl 1.06, tunnels 0.96-0.99; hue matched (B/R 1.00-1.06).
  Off by > 10 %: bowl slopes 1.15; mixed sub-zones floor west/east 0.90/1.37 (patch edges vs boxes). MM9's own render
  of the bowl walls = texture 72.4 x 0.196 = luma 14; ours 15-16; capture 79-92 (old import, too bright).
  Capture (info only): 74.5; baked v03 23.8; darkest view 13.0
- Unmatched: Dragon.scr fly-in/Land/Taunt (he appears in place), any movement (immobile, user decision), target
  switching, wing push, breathing smoke, model-key sounds; pillar damage by weapons/fire (click instead) and their
  ExplodeDamage/debris
- Shared changes: tools/lighting/bake_indoor.py opt-in profile key `shadowless_faces` (doc in
  devdocs/INDOOR_BAKED_LIGHTING.md); decoration row 2452 mm9_skeletonlayingprop_x150 (under the lock); playbook row + lessons
- Sheets: review/v03_compare.jpg (26 views), review/lighting_compare_v03.jpg (original | v02 | v03), review/v02_compare.jpg,
  review/lighting_compare.jpg, review/dragon_sheet.jpg,
  review/pillars_sheet_a.jpg / _b.jpg (all looked at)
- Not checked: pillar break by a desktop click (save from scenario events instead), the fight in the desktop game, the
  unreachable ledges in game, sound
- Blockers: none

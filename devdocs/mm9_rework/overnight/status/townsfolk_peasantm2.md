# townsfolk_peasantm2 (claude-townsfolk-peasantm2)
Phase: sources. Lease token ffa64d64cd5c4326b4c818fb4370043b. Credits 0/60 (backup 3740 at start, floor 2740).
Project level_generation/creatures/mm9_peasantm2_claude. Background: none.
Rows on PeasantM2.abc: 44 Commoner Human1 MaleA B (PEASANTM2B), 50 Commoner Human2 MaleA A (PEASANTM2A).
PEASANTM2C/D skins belong to PeasantM2d.abc (rows 24 Town Elf MaleB A, 26 Shopkeeper Elf MaleC A): checking whether they fit.
Template: mm9_njam_claude (same PeasantMale 45-joint skeleton), nobleman tiers scripts.
21:09 Masters done (references_hd, 03_left = mirrored 04_right). ST pm2_smart_v1 submitted (credits 5/60, backup 3715 before). Codex head turnarounds A+B running (references_head/).
21:10 ST done (5 cr). scripts/clean_pm2.py (figure's left half mirrored; head kept, eyeball cups/lip strips/lacing dropped) -> face_fix.py (mouth pocket closed, lids smoothed) -> fit_pm2.py -> step_b.sh (rig_pm2, MPFB hand graft, helpers). Clay clips OK (review/quick_frames_grid.png).
Head turnarounds A (beard) + B (clean-shaven) accepted (references_head/grey_sheet.png). UV layout uv_pm2.py running (then FROZEN: never re-run).
Plan: body 4K retexture (10) + head-only 4K retextures A and B (10 each) = 35 total.
21:29 UVs FROZEN (work/uv_v1.blend; never re-run uv_pm2.py). Submitted pm2_retex_body, pm2_retex_head_a, pm2_retex_head_b (credits 35/60).
21:32 Retextures done and downloaded (35/60 spent).
22:00 Paint composed; fixes: sleeve shards (Meshy hand piece's forearm stub was Hand-weighted -> split Forearm/Hand; stub texels skin), bell cuff
weights fully on the arm, cuff lining + two-sided hem, forearm midline seam on the forehead (head_seam.py), tier B sleeve edge by armhole plane.
22:38 Installed first build (r3); rows 44/50 in mm9_npc_actor_rows.tsv, tables regenerated, actors.yml block bound (flock). Gates r3: jitter 0
fails (reference = MM9 untouched + same half keys), detached 0, flat 0.00-0.01, bones 0/12, winding 0. Hands: Fidget R 5.3 cm (head scratch into
hair), Conv1 L 6.0 cm (MM9 hand on belly; any push >3 cm failed jitter). Regression running. Then: Cower/Bow floor fix reinstall, floor audit.
Map placement switch is the orchestrator's (brief "Lessons from wave 1").
23:05 DONE. Final install sha 97615c0b451b (Cower/Bow grounded). Regression mm9_ PASS (170 descriptors on 70 models). Floor audit ok (44, 50).
Viewer r3-20261101, check 26 switches 0 errors. Credits 35/60 (backup 3605 after my last job). Lease released. Background: none. Chromes: none.
Open: Conv1 L hand on belly 6.0 cm (push >3 cm failed jitter), Fidget R 5.3 cm (forehead rub into hair). Map placement switch = orchestrator.
2026-11-02 ear-sweep fix (owner ear-sweep-fix): white net beside/below both ears was Meshy's paid head paint (both tiers).
`scripts/fix_net_pm2.py` (between head_seam.py and finish_tex.py): tier B net and leftover specks -> skin; tier A sideburn net -> skin,
jaw beard kept (no sideburn now). Rebuild (IN=uv_v3.blend), only the two head colour images changed (0.000 mm in every clip), installed
r4 sha fc3e623f4d1d, rollback work/installed_preear.glb. Viewer r4-20261102, check 26 switches 0 failed. Sheet review/sheet_ear_before_after.png.

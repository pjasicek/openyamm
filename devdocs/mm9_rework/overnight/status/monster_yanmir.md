# monster_yanmir (overnight-yanmir)
Phase: DONE after the follow-up pass: r5 installed and bound (staff, thumb, back hair, necklace disks; Death2 hands left). Lease released.
Credits: 20/30 (body Smart Topology 5, head-only Smart Topology 5, body 4K retexture 10). Backup balance before the last job 3995.
Row: 206 Yanmir L70 (`MM9 206 Yanmir`), one skin, no tiers. Model `assets_source/worlds/mm9/models/mm9_yanmir.glb`, binding block
`# >>> mm9_yanmir_claude` in assets_dev/worlds/mm9/models/actors.yml (scale 333.333, strides 1.46/1.77, melee 0.603, ranged 0.405 from Ystafftop).
Skeleton: YANMIR.abc (not the giant's); re-rested onto our A-pose mesh (rig_yan.py); Death/Death2 = MM9 Giant die1/die2 retargeted (giant_deaths.py).
Gates (r4): handedness ok; bones 0 stretching; body detached 0 (staff flagged as a held part); flat 0; winding 0; floor ok; regression PASS
150/60/0; viewer 23 clips 0 failed; arm-hand pass 22/23 (Death2 script clip L 3.5 cm 4 f, R forearm 6.0 cm last frame); staff vs body 0
(AttackMeleeSave 4.0 cm, Death 0.6); grip 0.26 cm, fingers wrap 120-150, thumb 15; jitter strict 7 flags (left arm, attacks/deaths), relative 1;
collapse not zero (Death2 hips 72/36 head 85, head 56-71 in StartDie/Fall/Wipe, finger up to 72); beard gate 6 cm (beard tip joined to chest skin).
Texture: body atlas 60.4 % spread 1.07; head 65 % spread 1.78.
Sheets: review/mm9_vs_ours.png, sheet_heads(.png,_b), sheet_hand_staff.png, sheet_closeups.png, sheet_strips_1-3.png, ingame_sheet.png.
README: level_generation/creatures/mm9_yanmir_claude/README.md. Rebuild: scripts/textures_all.sh, scripts/parts_chain.sh, REV=rN scripts/rebuild.sh --install.
Background: none.
Follow-up (in progress): make_staff.py v2 (thick speckled pole r 0.034-0.038, four-petal tulip cup + ring, Codex pole tile
references_acc/v2/pole_tile.png), fist_yan.py per-finger wrap on the thick pole + thumb over it, disks_silver.py (necklace disks dark
silver), hair_widen.py (back hair 1.30x wider at its foot) + hair_contrast.py (head-set paint, back), parts_chain.sh -> parts_r5.blend;
textures_all.sh rerun. Next: Death2 hand trial, REV=r5 rebuild --install, gates, regression, sheets.
Follow-up r5 done 18:1x: see README 'Follow-up r5'. 0 credits.
